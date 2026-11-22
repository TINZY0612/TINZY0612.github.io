"""Bounded historical-state tests; preserve the initial probe results."""
import concurrent.futures
import json
from collect_sources import ROOT, RAW, USDC, rpc, now


def provider_probe(name, url):
    out = []
    cases = [
        ("chainid", "eth_chainId", []),
        ("latest_supply", "eth_call", [{"to": USDC, "data": "0x18160ddd"}, "latest"]),
        ("q3_block", "eth_getBlockByNumber", [hex(26093737), False]),
        ("q3_next_block", "eth_getBlockByNumber", [hex(26093738), False]),
        ("q3_supply", "eth_call", [{"to": USDC, "data": "0x18160ddd"}, hex(26093737)]),
        ("2024_supply", "eth_call", [{"to": USDC, "data": "0x18160ddd"}, hex(21000000)]),
    ]
    for label, method, params in cases:
        record = rpc(url, f"archive_{name}_{label}", method, params)
        out.append(record)
        print(json.dumps({k:record.get(k) for k in ["name", "status", "http_status", "application_error", "error"]}), flush=True)
        if label == "chainid" and record["status"] != "received":
            break
    return out


if __name__ == "__main__":
    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(provider_probe, name, url) for name, url in [
            ("publicnode", "https://ethereum-rpc.publicnode.com"),
            ("drpc", "https://eth.drpc.org"),
            ("tenderly", "https://mainnet.gateway.tenderly.co"),
        ]]
        for f in concurrent.futures.as_completed(futures):
            records.extend(f.result())
    (ROOT / "rpc_supplement_manifest.json").write_text(json.dumps({"finished_at_utc": now(), "sources": records}, indent=2), encoding="utf-8")
