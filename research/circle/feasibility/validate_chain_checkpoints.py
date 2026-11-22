"""Four EOD Ethereum checkpoints and original reserve examination sources."""
import concurrent.futures
import datetime as dt
import json
import lxml.html
from collect_sources import ROOT, RAW, USDC, request, rpc, now


def checkpoint(date):
    end = dt.datetime.fromisoformat(date).replace(tzinfo=dt.timezone.utc) + dt.timedelta(days=1, seconds=-1)
    stamp = int(end.timestamp())
    label = date.replace("-", "_")
    records = []
    r = request(f"checkpoint_{label}_block_lookup", f"https://coins.llama.fi/block/ethereum/{stamp}")
    records.append(r)
    if r["status"] != "received":
        return records
    block = json.loads((ROOT / r["file"]).read_text())["height"]
    for provider, url in [("tenderly", "https://mainnet.gateway.tenderly.co"), ("drpc", "https://eth.drpc.org")]:
        calls = [("supply", "eth_call", [{"to": USDC, "data": "0x18160ddd"}, hex(block)])]
        if provider == "tenderly":
            calls += [("block", "eth_getBlockByNumber", [hex(block), False]),
                      ("next_block", "eth_getBlockByNumber", [hex(block + 1), False])]
        for suffix, method, params in calls:
            r = rpc(url, f"checkpoint_{label}_{provider}_{suffix}", method, params)
            records.append(r)
            print(json.dumps({"name": r["name"], "status": r["status"]}), flush=True)
    return records


if __name__ == "__main__":
    doc = lxml.html.fromstring((RAW / "circle_transparency.html").read_bytes())
    links = [("attestation_2026_" + month, e.get("href")) for e in doc.xpath('//a[@href]')
             for month in ["June", "July", "August", "September"]
             if "/USDCAttestationReports/2026/" in e.get("href", "") and month in e.get("href", "")]
    links += [("defillama_usdc_supply_adapter", "https://raw.githubusercontent.com/DefiLlama/peggedassets-server/master/src/adapters/peggedAssets/usd-coin/index.ts"),
              ("defillama_find_closest", "https://raw.githubusercontent.com/DefiLlama/dimension-adapters/master/helpers/utils/findClosest.ts")]
    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        jobs = [pool.submit(request, name, url) for name, url in links]
        for f in concurrent.futures.as_completed(jobs):
            r = f.result()
            records.append(r)
            print(json.dumps({"name":r["name"], "status":r["status"], "error":r.get("error")}), flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        jobs = [pool.submit(checkpoint, date) for date in ["2026-06-30", "2026-07-31", "2026-08-31", "2026-09-30"]]
        for f in concurrent.futures.as_completed(jobs):
            records.extend(f.result())
    (ROOT / "checkpoint_manifest.json").write_text(json.dumps({"finished_at_utc":now(), "sources":records}, indent=2), encoding="utf-8")
