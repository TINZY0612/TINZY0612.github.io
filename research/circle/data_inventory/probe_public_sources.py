"""Bounded, credential-free access checks. Retains responses and never fills gaps.

Run from any directory with Python 3. This is an access/schema audit, not a
replacement for the historical models or a production dashboard collector.
"""
import concurrent.futures
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
START = dt.datetime.now(dt.timezone.utc)
RUN = ROOT / "access_checks" / START.strftime("%Y%m%dT%H%M%SZ")
RUN.mkdir(parents=True, exist_ok=True)
SOURCES = {
    "stablecoin_registry": "https://stablecoins.llama.fi/stablecoins?includePrices=true",
    "usdc_supply": "https://stablecoins.llama.fi/stablecoin/2",
    "stablecoin_total": "https://stablecoins.llama.fi/stablecoincharts/all",
    "cctp_fees": "https://api.llama.fi/summary/fees/circle-cctp?dataType=dailyFees",
    "usyc_fees": "https://api.llama.fi/summary/fees/circle-usyc?dataType=dailyRevenue",
    "arc_dex": "https://api.llama.fi/overview/dexs/arc?excludeTotalDataChart=false&excludeTotalDataChartBreakdown=true&dataType=dailyVolume",
    "arc_fees": "https://api.llama.fi/overview/fees/arc?excludeTotalDataChart=false&excludeTotalDataChartBreakdown=true&dataType=dailyFees",
    "usyc_reports": "https://usyc.hashnote.com/api/price-reports",
    "coinmetrics_usdc_catalog": "https://community-api.coinmetrics.io/v4/catalog-v2/asset-metrics?assets=usdc",
    "coinmetrics_usdc_daily": "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?assets=usdc&metrics=SplyCur&frequency=1d&start_time=2026-07-01&end_time=2026-07-03&page_size=10",
    "cctp_adapter": "https://raw.githubusercontent.com/DefiLlama/dimension-adapters/master/fees/cctp/index.ts",
    "dune_public_result_without_key": "https://api.dune.com/api/v1/query/9169111/results?limit=1",
}


def shape(data):
    out = {"type": type(data).__name__}
    if isinstance(data, dict):
        out["keys"] = list(data)[:25]
        for key in ("tokens", "totalDataChart", "data", "reports", "priceReports"):
            rows = data.get(key)
            if isinstance(rows, list):
                out[key + "_count"] = len(rows)
                if rows:
                    out[key + "_first"] = rows[0]
                    out[key + "_last"] = rows[-1]
        if "chainBalances" in data:
            out["chains"] = list(data["chainBalances"])
    elif isinstance(data, list):
        out["count"] = len(data)
        if data:
            out["first"] = data[0]
            out["last"] = data[-1]
    # Do not duplicate large nested records into manifest.
    for key, value in list(out.items()):
        if len(json.dumps(value)) > 1800:
            out[key] = {"preview": str(value)[:1000], "truncated": True}
    return out


def fetch(item):
    name, url = item
    entry = {"name": name, "url": url,
             "retrieved_at_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CircleResearch/1.0 public-source-access-audit", "Accept": "application/json,text/plain,*/*"})
        with urllib.request.urlopen(req, timeout=35) as res:
            raw = res.read(24 * 1024 * 1024 + 1)
            if len(raw) > 24 * 1024 * 1024:
                raise ValueError("Response exceeded 24 MiB audit limit")
            entry.update(status=res.status, final_url=res.url,
                         content_type=res.headers.get("Content-Type"),
                         source_date=res.headers.get("Date"),
                         browser_cors=res.headers.get("Access-Control-Allow-Origin"))
        path = RUN / (name + ".response.gz")
        path.write_bytes(gzip.compress(raw, mtime=0))
        entry.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(),
                     raw_path=str(path.relative_to(ROOT)))
        try:
            obj = json.loads(raw)
            entry["shape"] = shape(obj)
        except (ValueError, UnicodeDecodeError):
            obj = None
        return entry, obj
    except urllib.error.HTTPError as exc:
        raw = exc.read(4000)
        path = RUN / (name + ".error.txt")
        path.write_bytes(raw)
        entry.update(status=exc.code, error=str(exc),
                     response_excerpt=raw.decode(errors="replace")[:500],
                     raw_path=str(path.relative_to(ROOT)),
                     sha256=hashlib.sha256(raw).hexdigest())
    except Exception as exc:
        entry.update(status="failed", error=str(exc))
    return entry, None


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(fetch, SOURCES.items()))
    registry = next((obj for entry, obj in results if entry["name"] == "stablecoin_registry"), None)
    eurc = []
    if isinstance(registry, dict):
        eurc = [x for x in registry.get("peggedAssets", []) if x.get("symbol", "").upper() in ("EURC", "EUROC")]
    for asset in eurc:
        results.append(fetch(("eurc_supply_" + str(asset["id"]), "https://stablecoins.llama.fi/stablecoin/" + str(asset["id"]))))
    manifest = {"started_at_utc": START.isoformat(), "purpose": "Access and schema check only; current-vintage responses, not original historical vintages", "eurc_registry_matches": [{k: x.get(k) for k in ("id", "name", "symbol", "pegType", "priceSource")} for x in eurc], "sources": [x[0] for x in results]}
    (RUN / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (ROOT / "latest_access_check.json").write_text(json.dumps({"manifest": str((RUN / "manifest.json").relative_to(ROOT))}, indent=2), encoding="utf-8")
    print(json.dumps({"manifest": str(RUN / "manifest.json"), "results": [{"name": x[0]["name"], "status": x[0]["status"], "bytes": x[0].get("bytes"), "error": x[0].get("error")} for x in results]}, indent=2))
