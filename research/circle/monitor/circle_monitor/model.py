from __future__ import annotations

import bisect
import datetime as dt
import statistics

from .domain import DataError, Quarter, ReviewRequired, digest, duration_quarter, iso, number, timestamp

MODEL_VERSION = "reserve-public-data-v1"
METHODS = ("fund_proportional", "sofr_lagged_spread")


def financial_quarters(records, as_of):
    """Select original disclosures. Derive Q4 from annual less nine months."""
    groups = {}
    for record in records:
        if timestamp(record["published_at"]) <= as_of:
            groups.setdefault((record["metric"], record["start"], record["end"]), []).append(record)
    measures = {}
    for key, rows in groups.items():
        rows.sort(key=lambda r: (timestamp(r["published_at"]), r.get("accession", "")))
        first = rows[0]
        if any(abs(r["value"] - first["value"]) > 1e-8 for r in rows):
            raise ReviewRequired("Conflicting original/comparative financial facts; retain prior forecasts and review the revision")
        measures[key] = first
    quarters = {}
    for (metric, start, end), record in measures.items():
        q = duration_quarter(start, end)
        if q:
            quarters.setdefault(q.key, {"period": q.key})[metric] = record
    years = {dt.date.fromisoformat(r["end"]).year for r in records}
    for year in years:
        q = Quarter(year, 4)
        destination = quarters.setdefault(q.key, {"period": q.key})
        for metric in ("reserve_income", "average_usdc"):
            if metric in destination:
                continue
            annual = measures.get((metric, f"{year}-01-01", f"{year}-12-31"))
            nine = measures.get((metric, f"{year}-01-01", f"{year}-09-30"))
            if annual is None or nine is None:
                continue
            value = annual["value"] - nine["value"]
            precision = annual.get("precision_million", 0) + nine.get("precision_million", 0)
            if metric == "average_usdc":
                annual_days = (q.end - dt.date(year, 1, 1)).days + 1
                nine_days = annual_days - q.days
                value = (annual["value"] * annual_days - nine["value"] * nine_days) / q.days
                precision = (annual.get("precision_million", 0) * annual_days + nine.get("precision_million", 0) * nine_days) / q.days
            destination[metric] = {"metric": metric, "start": str(q.start), "end": str(q.end),
                "value": number(value, minimum=0), "published_at": max(annual["published_at"], nine["published_at"]),
                "basis": "annual_less_nine_months" if metric == "reserve_income" else "day_weighted_annual_less_nine_months",
                "precision_million": precision, "source_hashes": sorted({annual["source_hash"], nine["source_hash"]}),
                "source_url": annual["source_url"], "components": [annual, nine]}
    return {k: v for k, v in quarters.items() if "reserve_income" in v}


def series_lookup(mapping):
    dates = sorted(mapping)

    def lookup(day):
        index = bisect.bisect_right(dates, day) - 1
        if index < 0:
            raise DataError("No eligible observation on or before " + day)
        return dates[index], mapping[dates[index]]
    return lookup


def forecast(period, as_of, inputs, *, kind="scenario", provenance="prospective", max_fund_lag_days=45):
    q = Quarter.parse(period)
    as_of = timestamp(as_of)
    eligible = financial_quarters(inputs["financials"], as_of)
    candidates = [r for r in eligible.values() if Quarter.parse(r["period"]).end < q.start and "average_usdc" in r]
    if not candidates:
        raise DataError("No published calibration quarter with reserve income and average USDC")
    calibration = max(candidates, key=lambda r: r["period"])
    lag = Quarter.parse(calibration["period"])
    if q.shift(-2) > lag:
        raise DataError("Financial calibration is more than two quarters behind")
    supply = {day: number(value, minimum=.000001, maximum=1e7) for day, value in inputs["supply"].items() if day < str(as_of.date())}
    if not supply or max(supply) < str(q.start):
        raise DataError("No completed supply day for this quarter yet")
    latest_observed = min(max(supply), str(q.end))
    if q.end >= as_of.date() and (as_of.date() - dt.date.fromisoformat(max(supply))).days > 3:
        raise DataError("USDC feed is stale")
    needed = [str(d) for d in lag.dates()] + [str(d) for d in q.dates() if str(d) <= latest_observed]
    if any(day not in supply for day in needed):
        raise DataError("Missing daily USDC balance; internal gaps are not projections")
    rates = {day: number(value, minimum=-.1, maximum=.25) for day, value in inputs["sofr"].items() if day < str(as_of.date())}
    if not rates or (as_of.date() - dt.date.fromisoformat(max(rates))).days > 7:
        raise DataError("SOFR feed is empty or stale")
    rate_on = series_lookup(rates)
    funds, original_months = {}, {}
    for row in sorted(inputs["funds"], key=lambda r: (timestamp(r["published_at"]), r["accession"])):
        if timestamp(row["published_at"]) > as_of:
            continue
        month = row["report_date"]
        chosen = original_months.setdefault(month, row["accession"])
        if row["accession"] == chosen:
            if row["date"] in funds:
                if abs(funds[row["date"]]["net_yield"] - row["net_yield"]) > 1e-12:
                    raise ReviewRequired("Conflicting eligible fund observations")
            else:
                funds[row["date"]] = row
    fund_on = series_lookup(funds)
    lag_rows, current_rows = [], []
    fund_error = None
    for day in lag.dates() + q.dates():
        key = str(day)
        projected = day > dt.date.fromisoformat(latest_observed) and day >= q.start
        balance = supply[latest_observed] if projected else supply[key]
        effective, rate = rate_on(min(key, latest_observed))
        item = {"date": key, "supply_million": balance, "supply_status": "flat_future_assumption" if projected else "provider_observed",
                "sofr": rate, "sofr_effective_date": effective}
        try:
            fund_date, fund = fund_on(min(key, str(as_of.date() - dt.timedelta(days=1))))
            if not projected and (day - dt.date.fromisoformat(fund_date)).days > max_fund_lag_days:
                raise DataError("Fund observation is stale")
            item.update(fund_net_yield=number(fund["net_yield"], minimum=-.1, maximum=.25), fund_observation_date=fund_date,
                        fund_published_at=fund["published_at"], fund_accession=fund["accession"])
        except DataError as exc:
            fund_error = str(exc)
        (lag_rows if day <= lag.end else current_rows).append(item)
    # A two-quarter-old calibration does not include the intervening quarter.
    if len(lag_rows) != lag.days or len(current_rows) != q.days:
        raise DataError("Quarter row construction mismatch")
    previous_exposure = sum(r["supply_million"] for r in lag_rows)
    previous_yield = number(calibration["reserve_income"]["value"], minimum=.000001) / number(calibration["average_usdc"]["value"], minimum=.000001) * 365 / lag.days
    previous_sofr = sum(r["supply_million"] * r["sofr"] * 365 / 360 for r in lag_rows) / previous_exposure
    gap = previous_yield - previous_sofr
    estimates = {"sofr_lagged_spread": sum(r["supply_million"] * (r["sofr"] / 360 + gap / 365) for r in current_rows)}
    ratio = None
    if fund_error is None:
        previous_fund = sum(r["supply_million"] * r["fund_net_yield"] for r in lag_rows) / previous_exposure
        if previous_fund <= 0:
            fund_error = "Fund-ratio calibration denominator is not positive"
        else:
            ratio = previous_yield / previous_fund
            estimates["fund_proportional"] = sum(r["supply_million"] * r["fund_net_yield"] / 365 for r in current_rows) * ratio
    source_hashes = sorted(set(inputs.get("source_hashes", [])))
    payload = {"schema_version": 1, "model_version": MODEL_VERSION, "period": q.key, "start": str(q.start), "end": str(q.end),
        "as_of_utc": iso(as_of), "kind": kind, "provenance": provenance, "estimates_million": estimates,
        "primary_method": "fund_proportional", "primary_available": fund_error is None,
        "fund_unavailable_reason": fund_error, "calibration": calibration, "lag_implied_yield": previous_yield,
        "fund_yield_ratio": ratio, "sofr_annual_gap": gap, "observed_supply_through": latest_observed,
        "observed_days": sum(r["supply_status"] == "provider_observed" for r in current_rows),
        "projected_days": sum(r["supply_status"] != "provider_observed" for r in current_rows),
        "rows": current_rows, "calibration_rows": lag_rows, "source_hashes": source_hashes,
        "inputs_fingerprint": digest({"calibration": calibration, "rows": current_rows, "lag_rows": lag_rows}),
        "warnings": ["Provider date labels are not proven exact end-of-day states"] + (["Average USDC was derived from rounded annual and nine-month disclosures"] if calibration["average_usdc"]["basis"].startswith("day_weighted") else [])}
    payload["id"] = digest(payload)
    return payload


def metrics(validations, selection, method):
    rows = [r for r in validations if r["selection"] == selection and r["method"] == method and r["provenance"] == "prospective"]
    if not rows:
        return {"n": 0, "mape": None, "mae_million": None, "worst_abs_error": None}
    return {"n": len(rows), "mape": statistics.mean(abs(r["signed_error"]) for r in rows),
            "mae_million": statistics.mean(abs(r["difference_million"]) for r in rows),
            "worst_abs_error": max(abs(r["signed_error"]) for r in rows)}
