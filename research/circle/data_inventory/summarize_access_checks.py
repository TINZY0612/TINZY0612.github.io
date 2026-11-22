"""Summarize downloaded samples without altering previous model vintages."""
import datetime as dt
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
manifest_path = ROOT / json.loads((ROOT / "latest_access_check.json").read_text())["manifest"]
manifest = json.loads(manifest_path.read_text())
entries = {x["name"]: x for x in manifest["sources"]}


def get(name):
    return json.loads(gzip.decompress((ROOT / entries[name]["raw_path"]).read_bytes()))


def day(stamp):
    return dt.datetime.fromtimestamp(int(stamp), dt.timezone.utc).date().isoformat()


def coverage(rows, stamp=lambda r: r[0]):
    dates = [day(stamp(r)) for r in rows]
    return {"rows": len(rows), "unique_dates": len(set(dates)),
            "first": min(dates) if dates else None, "last": max(dates) if dates else None,
            "duplicate_dates": len(dates) - len(set(dates))}


out = {"access_manifest": str(manifest_path.relative_to(ROOT)),
       "note": "Current-vintage access/coverage audit, not a new forecast or an extension of prior direct-chain validation."}
out["usdc"] = coverage(get("usdc_supply")["tokens"], lambda r: r["date"])
out["eurc"] = coverage(get("eurc_supply_50")["tokens"], lambda r: r["date"])
out["stablecoin_total"] = coverage(get("stablecoin_total"), lambda r: r["date"])
out["stablecoin_total"]["definition_warning"] = "Sum totalCirculatingUSD across peg categories for all-stablecoin USD value; never sum raw yen/euro/dollar units. Preserve the previous regression's original denominator separately."
cctp = get("cctp_fees")
out["cctp"] = coverage(cctp["totalDataChart"])
by_day = {day(t): v for t, v in cctp["totalDataChart"]}
eth = {}
for stamp, chains in cctp.get("totalDataChartBreakdown", []):
    if "Ethereum" in chains:
        values = chains["Ethereum"]
        eth[day(stamp)] = sum(values.values()) if isinstance(values, dict) else values
quarters = []
for year, quarter in [(2025, 1), (2025, 2), (2025, 3), (2025, 4), (2026, 1), (2026, 2), (2026, 3)]:
    start = dt.date(year, quarter * 3 - 2, 1)
    end = dt.date(year + (quarter == 4), 1 if quarter == 4 else quarter * 3 + 1, 1)
    expected = [(start + dt.timedelta(days=i)).isoformat() for i in range((end-start).days)]
    missing = [d for d in expected if d not in by_day]
    quarters.append({"quarter": f"{year}Q{quarter}", "expected_days": len(expected), "present_days": len(expected)-len(missing), "missing_dates": missing,
                     "observed_global_fee_usd": sum(by_day[d] for d in expected if d in by_day) if any(d in by_day for d in expected) else None,
                     "observed_ethereum_fee_usd": sum(eth[d] for d in expected if d in eth) if any(d in eth for d in expected) else None,
                     "ethereum_present_days": sum(d in eth for d in expected),
                     "complete_daily_aggregate": not missing,
                     "direct_rpc_validation": "Ethereum only; existing Stage 5 audit" if (year,quarter)==(2026,3) else "Not completed"})
out["cctp"]["quarter_coverage"] = quarters
q3 = quarters[-1]
direct = 154093.848015
out["cctp"]["q3_2026_measurement_comparison"] = {"existing_direct_ethereum_usdc_fee_usd": direct,
    "new_vintage_aggregator_ethereum_fee_usd": q3["observed_ethereum_fee_usd"],
    "difference_usd": direct-q3["observed_ethereum_fee_usd"],
    "difference_percent_of_aggregator": (direct/q3["observed_ethereum_fee_usd"]-1)*100,
    "status": "Unresolved: new aggregator sums are not a matched-transaction reconciliation."}
for key in ["usyc_fees", "arc_dex", "arc_fees"]:
    out[key] = coverage(get(key)["totalDataChart"])
out["arc_fees"]["warning"] = "Application/protocol fee overview for a chain; not authenticated Arc network gas fees or Circle GAAP revenue. Quarantined from earnings inputs."
reports = get("usyc_reports")["data"]
out["usyc_reports"] = coverage(reports, lambda r: r["timestamp"])
out["usyc_reports"]["warning"] = "Only the 45 reports returned by this request; full earlier chain reconstruction remains in Stage 5."
out["coinmetrics"] = {"daily_sample": get("coinmetrics_usdc_daily")["data"],
    "community_metric_names": [x["metric"] for x in get("coinmetrics_usdc_catalog")["data"][0]["metrics"] if any(f.get("community") for f in x["frequencies"])],
    "warning": "Asset id usdc is not assumed to be all-chain Circle circulation; authenticate asset methodology before reconciliation."}
out["dune"] = {"query_id": 9169111, "without_api_key_http_status": entries["dune_public_result_without_key"]["status"],
    "query_executed_in_this_audit": False, "warning": "A public SQL page does not establish free API download or successful execution."}
path = manifest_path.parent / "summary.json"
path.write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps({"summary": str(path), "cctp_coverage": [{k:v for k,v in x.items() if k not in ("missing_dates",)} for x in quarters], "comparison": out["cctp"]["q3_2026_measurement_comparison"], "histories": {k:{a:b for a,b in out[k].items() if a in ("rows","first","last")} for k in ("usdc","eurc","arc_dex","arc_fees","usyc_reports")}}, indent=2))
