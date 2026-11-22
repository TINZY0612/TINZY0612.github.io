"""Read-only, key-free source and Ethereum historical-state feasibility checks.

Run with Python 3.11+; only the standard library is required. Responses are cached
with timestamps and SHA-256 hashes. No wallet, signing, or transaction methods.
"""
from __future__ import annotations

import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
RAW.mkdir(parents=True, exist_ok=True)
UA = "CircleAcademicResearch/0.1 (public financial and blockchain data feasibility)"
USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def request(name, url, payload=None, timeout=22):
    started = time.monotonic()
    record = {"name": name, "url": url, "retrieved_at_utc": now(),
              "method": "POST" if payload is not None else "GET"}
    if payload is not None:
        record["request_json"] = payload
    try:
        data = json.dumps(payload).encode() if payload is not None else None
        headers = {"User-Agent": UA, "Accept": "*/*"}
        if data:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(url, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read()
            ctype = response.headers.get("Content-Type", "")
            record.update(http_status=response.status, content_type=ctype,
                          final_url=response.url, bytes=len(body))
        ext = "json" if "json" in ctype else "html" if "html" in ctype else "pdf" if body.startswith(b"%PDF") else "txt"
        dest = RAW / f"{name}.{ext}"
        dest.write_bytes(body)
        record.update(file=str(dest.relative_to(ROOT)), sha256=hashlib.sha256(body).hexdigest(), status="received")
        try:
            decoded = json.loads(body)
            if isinstance(decoded, dict) and "error" in decoded:
                record.update(status="application_error", application_error=decoded["error"])
        except (ValueError, UnicodeDecodeError):
            pass
    except urllib.error.HTTPError as exc:
        body = exc.read()
        dest = RAW / f"{name}_http_error.txt"
        dest.write_bytes(body)
        record.update(status="failed", http_status=exc.code, error=str(exc),
                      error_body_file=str(dest.relative_to(ROOT)),
                      error_body_sha256=hashlib.sha256(body).hexdigest())
    except Exception as exc:
        record.update(status="failed", error=str(exc))
    record["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return record


def rpc(url, name, method, params):
    return request(name, url, {"jsonrpc": "2.0", "id": 1, "method": method, "params": params})


def rpc_probe(provider, url):
    results = []
    for label, method, params in [
        ("chainid", "eth_chainId", []),
        ("latest_block", "eth_getBlockByNumber", ["latest", False]),
        ("historic_block", "eth_getBlockByNumber", [hex(21000000), False]),
        ("historic_supply", "eth_call", [{"to": USDC, "data": "0x18160ddd"}, hex(21000000)]),
        ("decimals", "eth_call", [{"to": USDC, "data": "0x313ce567"}, "latest"]),
    ]:
        result = rpc(url, f"rpc_{provider}_{label}", method, params)
        results.append(result)
        if label == "chainid" and result["status"] != "received":
            break
    return results


def main():
    sources = [
        ("defillama_usdc", "https://stablecoins.llama.fi/stablecoin/2"),
        ("defillama_usdc_chart", "https://stablecoins.llama.fi/stablecoincharts/all?stablecoin=2"),
        ("nyfed_sofr_q3", "https://markets.newyorkfed.org/api/rates/secured/sofr/search.json?startDate=2026-07-01&endDate=2026-09-30"),
        ("nyfed_sofr_2023_2026", "https://markets.newyorkfed.org/api/rates/secured/sofr/search.json?startDate=2023-01-01&endDate=2026-11-20"),
        ("fred_dgs3mo", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS3MO&cosd=2023-01-01&coed=2026-11-20"),
        ("treasury_2026", "https://home.treasury.gov/resource-center-data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value=2026"),
        ("circle_q3_2026_html", "https://d18rn0p25nwr6d.cloudfront.net/CIK-0001876042/e607a289-7db3-44a8-bdf6-c6624a132a27.html"),
        ("circle_q3_2026_pdf", "https://d18rn0p25nwr6d.cloudfront.net/CIK-0001876042/b3ce97a8-6be6-4a55-bf46-b670adcb57f1.pdf"),
        ("circle_transparency", "https://www.circle.com/transparency"),
        ("circle_contracts", "https://developers.circle.com/stablecoins/usdc-contract-addresses"),
        ("blackrock_usdxx", "https://www.blackrock.com/cash/en-us/products/329365/circle-reserve-fund"),
        ("sec_companyfacts", "https://data.sec.gov/api/xbrl/companyfacts/CIK0001876042.json"),
        ("defillama_circle_adapter", "https://raw.githubusercontent.com/DefiLlama/dimension-adapters/master/fees/circle.ts"),
        ("defillama_stablecoin_helper", "https://raw.githubusercontent.com/DefiLlama/dimension-adapters/master/helpers/attestations-stablecoins.ts"),
        ("eth_q3_end_block", "https://coins.llama.fi/block/ethereum/1790812799"),
    ]
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        jobs = {pool.submit(request, name, url): name for name, url in sources}
        for future in concurrent.futures.as_completed(jobs):
            result = future.result()
            results.append(result)
            print(json.dumps({k: result.get(k) for k in ["name", "status", "http_status", "bytes", "error"]}), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        jobs = [pool.submit(rpc_probe, name, url) for name, url in [
            ("publicnode", "https://ethereum-rpc.publicnode.com"),
            ("llamarpc", "https://eth.llamarpc.com"),
            ("1rpc", "https://1rpc.io/eth"),
        ]]
        for future in concurrent.futures.as_completed(jobs):
            batch = future.result()
            results.extend(batch)
            for result in batch:
                print(json.dumps({k: result.get(k) for k in ["name", "status", "http_status", "application_error", "error"]}), flush=True)
    manifest = {"run_finished_at_utc": now(), "purpose": "feasibility only; not a historical forecast", "sources": sorted(results, key=lambda x: x["name"])}
    (ROOT / "source_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Saved source_manifest.json", flush=True)


if __name__ == "__main__":
    main()
