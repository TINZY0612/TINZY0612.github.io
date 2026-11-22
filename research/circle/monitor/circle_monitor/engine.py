from __future__ import annotations

import datetime as dt

from .domain import DataError, Quarter, canonical, digest, iso, timestamp
from .model import METHODS, MODEL_VERSION, financial_quarters, forecast, metrics
from .store import atomic_write


def release_barriers(financials, events, now):
    """Treat the whole known earnings-release day as ineligible for forecasts."""
    result = {}
    for row in events:
        if timestamp(row["published_at"]) <= now:
            day = row.get("release_day", row["published_at"][:10])
            result[row["period"]] = min(result.get(row["period"], day), day)
    for key, row in financial_quarters(financials, now).items():
        day = row["reserve_income"]["published_at"][:10]
        result[key] = min(result.get(key, day), day)
    return result


def score(store, now, financials, events, alert_threshold):
    actuals = financial_quarters(financials, now)
    barriers = release_barriers(financials, events, now)
    forecasts = store.rows("forecasts")
    existing = {(r["period"], r["selection"], r["method"]): r for r in store.rows("validations")}
    issues = []
    for period, financial in actuals.items():
        actual = financial["reserve_income"]["value"]
        if actual <= 0:
            issues.append({"period": period, "message": "Actual reserve income is not positive; percentage scoring requires review"})
            continue
        eligible = sorted((f for f in forecasts if f["period"] == period and f["as_of_utc"][:10] < barriers[period]
                           and f["projected_days"] == 0 and f["kind"] in ("initial", "update")), key=lambda f: (f["as_of_utc"], f["id"]))
        for selection in ("initial", "latest_pre_release"):
            candidates = [f for f in eligible if f["kind"] == "initial"] if selection == "initial" else eligible
            for method in METHODS:
                candidates_for_method = [f for f in candidates if method in f["estimates_million"]]
                if not candidates_for_method:
                    continue
                chosen = candidates_for_method[0] if selection == "initial" else candidates_for_method[-1]
                key = (period, selection, method)
                if key in existing:
                    if abs(existing[key]["actual_million"] - actual) > 1e-8:
                        issues.append({"period": period, "message": "Actual changed after validation; original score retained for review"})
                    continue
                estimate = chosen["estimates_million"][method]
                error = estimate / actual - 1
                record = {"period": period, "selection": selection, "method": method, "forecast_id": chosen["id"],
                    "forecast_at": chosen["as_of_utc"], "release_day_barrier": barriers[period], "validated_at": iso(now),
                    "forecast_file": "forecasts/" + digest(chosen) + ".json",
                    "estimate_million": estimate, "actual_million": actual, "difference_million": estimate - actual,
                    "signed_error": error, "absolute_error": abs(error), "provenance": chosen["provenance"],
                    "actual_source": financial["reserve_income"], "alert": abs(error) > alert_threshold}
                store.put("validations", record)
                existing[key] = record
    return issues


def tick(store, inputs, now, *, initial_days=7, provenance="prospective", alert_threshold=.01, max_fund_lag_days=45):
    """One idempotent run; the caller holds Store.lock across collection and tick."""
    now = timestamp(now)
    if not 1 <= initial_days <= 30:
        raise DataError("Initial forecast offset must be between 1 and 30 days")
    for collection in ("financials", "funds", "releases"):
        for row in inputs.get(collection, []):
            store.put(collection, row)
    merged = {**inputs, **{k: store.rows(k) for k in ("financials", "funds", "releases")}}
    barriers = release_barriers(merged["financials"], merged["releases"], now)
    current = Quarter.containing(now.date())
    existing = store.rows("forecasts")
    targets = {current.key, current.shift(-1).key} | {r["period"] for r in existing if r["period"] not in barriers}
    output, issues = [], list(inputs.get("issues", []))
    for period in sorted(targets):
        q = Quarter.parse(period)
        rows = sorted([f for f in existing if f["period"] == period], key=lambda f: (f["as_of_utc"], f["id"]))
        if period in barriers:
            continue
        scheduled = q.end + dt.timedelta(days=initial_days)
        if q.end < now.date() < scheduled:
            output.append({"period": period, "status": "awaiting_initial_cutoff", "scheduled_for": str(scheduled)})
            continue
        kind = "scenario" if q.end >= now.date() else "update" if any(f["kind"] == "initial" for f in rows) else "initial"
        try:
            result = forecast(period, now, merged, kind=kind, provenance=provenance, max_fund_lag_days=max_fund_lag_days)
            if kind == "initial":
                result["scheduled_for"] = str(scheduled)
                result["published_days_after_scheduled"] = (now.date() - scheduled).days
                # Include the initial publication policy in its immutable identity.
                result["id"] = digest({k: v for k, v in result.items() if k != "id"})
            unchanged = rows and rows[-1]["inputs_fingerprint"] == result["inputs_fingerprint"] and not (kind == "initial" and rows[-1]["kind"] != "initial")
            if unchanged:
                result = rows[-1]
            else:
                store.put("forecasts", result)
                existing.append(result)
            output.append({"period": period, "status": "current_quarter" if kind == "scenario" else "awaiting_earnings",
                           "forecast": result})
        except DataError as exc:
            issue = {"period": period, "message": str(exc)}
            issues.append(issue)
            output.append({"period": period, "status": "data_unavailable", "last_good_forecast": rows[-1] if rows else None})
    issues += score(store, now, merged["financials"], merged["releases"], alert_threshold)
    validations = store.rows("validations")
    metrics_by_selection = {selection: {method: metrics(validations, selection, method) for method in METHODS}
                            for selection in ("initial", "latest_pre_release")}
    for issue in issues:
        store.put("issues", {**issue, "observed_at": iso(now)})
    result = {"schema_version": 1, "model_version": MODEL_VERSION, "as_of_utc": iso(now), "provenance": provenance,
              "status": "needs_attention" if issues else "ok", "targets": output,
              "released_awaiting_actual": sorted(set(barriers) - set(financial_quarters(merged["financials"], now))),
              "validations": validations, "prospective_metrics": metrics_by_selection,
              "issues": issues, "historical_backtests_unchanged": True,
              "source_notices": inputs.get("notices", []),
              "frozen_forecasts": [{"period": f["period"], "as_of_utc": f["as_of_utc"], "estimates_million": f["estimates_million"],
                                     "provenance": f["provenance"], "evidence_file": "forecasts/" + digest(f) + ".json"}
                                    for f in sorted(store.rows("forecasts"), key=lambda r: r["as_of_utc"]) if f["kind"] == "initial"],
              "initial_forecast_days_after_quarter_end": initial_days,
              "error_alert_threshold": alert_threshold}
    store.put("runs", {"as_of_utc": iso(now), "status": result["status"], "target_periods": sorted(targets), "issues": issues})
    return result


def export(store, view, output_directory):
    """Generated data only; never touches website HTML, live.json or research.json."""
    from pathlib import Path
    output = Path(output_directory)
    for collection in ("forecasts", "validations"):
        for row in store.rows(collection):
            destination = output / collection / (digest(row) + ".json")
            if destination.exists() and destination.read_bytes() != canonical(row):
                raise DataError("Published immutable evidence differs from local evidence")
            if not destination.exists():
                atomic_write(destination, canonical(row))
    atomic_write(output / "monitor.json", canonical(view))
