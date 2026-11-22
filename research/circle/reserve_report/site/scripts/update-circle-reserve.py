"""Refresh only the forward reserve scenario. Historical backtests stay fixed.

Standard-library-only collector for GitHub Actions or manual local execution.
No API keys. A failed source/coverage check leaves the last good cache untouched.
"""
import bisect
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "circle/data"


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "ZiYik-Circle-Research/1.0", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=40) as response:
        raw = response.read(4 * 1024 * 1024 + 1)
        if len(raw) > 4 * 1024 * 1024:
            raise ValueError("Feed exceeded 4 MiB size limit")
    return json.loads(raw), {"url": url, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def build(today=None):
    now = dt.datetime.now(dt.timezone.utc)
    today = today or now.date()
    research = json.loads((DATA / "research.json").read_text(encoding="utf-8"))
    last = research["periods"][-1]
    # This release has a fixed Q4 2026 calibration. Stop instead of silently
    # forecasting later quarters without loading newly reported financials.
    if not dt.date(2026, 10, 1) <= today <= dt.date(2027, 2, 28):
        raise ValueError("Q4 2026 model window has ended; update the financial calibration before continuing")
    usdc_url = "https://stablecoins.llama.fi/stablecoincharts/all?stablecoin=2"
    sofr_url = "https://markets.newyorkfed.org/api/rates/secured/sofr/search.json?startDate=2026-07-01&endDate=" + today.isoformat()
    supply_raw, supply_source = fetch(usdc_url)
    rate_raw, rate_source = fetch(sofr_url)
    supply = {}
    for row in supply_raw:
        date = dt.datetime.fromtimestamp(int(row["date"]), dt.timezone.utc).date()
        if date in supply:
            raise ValueError("Duplicate supply date")
        value = float(row["totalCirculating"]["peggedUSD"]) / 1e6
        if not 0 < value < 1e7:
            raise ValueError("USDC supply units or range changed")
        supply[date] = value
    rates = {}
    for row in rate_raw["refRates"]:
        date = dt.date.fromisoformat(row["effectiveDate"])
        rate = float(row["percentRate"]) / 100
        if date >= today or not 0 <= rate < 0.25 or row.get("type") != "SOFR":
            raise ValueError("Unexpected rate date, type or units")
        if date in rates:
            raise ValueError("Duplicate SOFR date")
        rates[date] = rate
    rate_dates = sorted(rates)
    if not rate_dates:
        raise ValueError("Empty SOFR feed")
    if (today - rate_dates[-1]).days > 7:
        raise ValueError("SOFR is more than seven calendar days old")

    def rate_on(date):
        index = bisect.bisect_right(rate_dates, date)-1
        if index < 0:
            raise ValueError("Missing calibration rate")
        return rates[rate_dates[index]]

    def dates(start, end):
        return [start + dt.timedelta(days=i) for i in range((end-start).days+1)]

    lag_dates = dates(dt.date(2026, 7, 1), dt.date(2026, 9, 30))
    if any(d not in supply for d in lag_dates):
        raise ValueError("Incomplete lag-quarter supply")
    lag_weighted = sum(supply[d]*rate_on(d)*365/360 for d in lag_dates) / sum(supply[d] for d in lag_dates)
    lag_implied = last["reserve_income"] / last["reported_average_supply"] * 365 / last["days"]
    spread = lag_implied - lag_weighted
    quarter_start, quarter_end = dt.date(2026, 10, 1), dt.date(2026, 12, 31)
    # Provider labels do not prove EOD. Exclude today's partial bucket.
    last_observed = min(max(d for d in supply if d < today), quarter_end)
    known_dates = dates(quarter_start, last_observed)
    if not known_dates or any(d not in supply for d in known_dates):
        raise ValueError("Missing Q4 supply date; no zero filling")
    if today <= quarter_end and (today-last_observed).days > 3:
        raise ValueError("Supply feed is stale")
    all_dates = dates(quarter_start, quarter_end)
    final_supply, final_rate = supply[last_observed], rate_on(last_observed)
    rows = [{"date": d.isoformat(), "supply_million": supply[d] if d <= last_observed else final_supply,
             "sofr": rate_on(d) if d <= last_observed else final_rate,
             "supply_status": "provider_observed" if d <= last_observed else "flat_future_assumption"} for d in all_dates]
    income = sum(r["supply_million"] * (r["sofr"]/360 + spread/365) for r in rows)
    result = {"as_of_utc": now.isoformat(), "model_version": "reserve-sofr-additive-v1", "period": "2026Q4", "actual": None,
        "status": "Forward scenario using current-vintage supply and a lagged financial calibration",
        "observed_supply_through": last_observed.isoformat(), "latest_sofr_effective_date": rate_dates[-1].isoformat(),
        "observed_days": len(known_dates), "projected_days": len(all_dates)-len(known_dates),
        "last_supply_million": final_supply, "last_sofr": final_rate, "lag_implied_yield": lag_implied,
        "lag_weighted_sofr_365": lag_weighted, "annual_spread": spread,
        "lag_reserve_income_million": last["reserve_income"], "lag_reported_average_supply_million": last["reported_average_supply"], "lag_days": last["days"],
        "calibration_rows": [{"date": d.isoformat(), "supply_million": supply[d], "sofr": rate_on(d)} for d in lag_dates],
        "reserve_income_million": income, "average_supply_million": sum(r["supply_million"] for r in rows)/len(rows),
        "sources": [supply_source, rate_source], "rows": rows,
        "limitations": ["Provider dates are not proven exact EOD states", "Future supply and SOFR held flat", "Financial calibration must be maintained after new earnings", "Reserve income is not net profit or EPS", "Historical backtests are not refreshed by this job"]}
    assert last["period"] == "2026Q3" and len(rows) == 92
    return result


if __name__ == "__main__":
    result = build()
    text = json.dumps(result, separators=(",", ":"), allow_nan=False)
    DATA.mkdir(parents=True, exist_ok=True)
    # Atomic last-good cache replacement after all validation succeeds.
    temp = DATA / "live.tmp"
    temp.write_text(text, encoding="utf-8")
    os.replace(temp, DATA / "live.json")
    archive = DATA / "forecasts"
    archive.mkdir(exist_ok=True)
    day = result["as_of_utc"][:10]
    snapshot = archive / (day + ".json")
    if not snapshot.exists():
        snapshot.write_text(text, encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("as_of_utc", "observed_supply_through", "observed_days", "projected_days", "reserve_income_million")}))
