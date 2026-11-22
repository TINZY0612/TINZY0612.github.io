from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import sys

from .bootstrap import from_research
from .domain import UTC, canonical, iso, timestamp
from .engine import export, tick
from .publish import publish
from .sources import COMPANY_URL, HttpClient, IR_URL, PRESSROOM_URL, SUPPLY_URL, collect
from . import parsers
from .sources import submission_rows
from .store import Store, atomic_write


def main(argv=None):
    parser = argparse.ArgumentParser(description="Circle reserve-income monitor; no AI or paid data service required")
    commands = parser.add_subparsers(dest="command", required=True)
    seed = commands.add_parser("seed", help="Import the audited historical financial/fund inputs, without generating forecasts")
    seed.add_argument("--research", type=Path)
    seed.add_argument("--bundle", type=Path, help="Portable audited seed bundle exported from the research workspace")
    seed.add_argument("--ledger", type=Path, help="Audited Stage 2 ledger for derived historical inputs")
    seed.add_argument("--state", type=Path, required=True)
    run = commands.add_parser("run", help="Collect sources, forecast, validate and export JSON")
    run.add_argument("--state", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--config", type=Path)
    run.add_argument("--fixture", type=Path, help="Offline replay, always excluded from prospective performance")
    run.add_argument("--as-of", help="Replay timestamp; allowed only with --fixture")
    probe = commands.add_parser("probe", help="Read-only live connectivity and schema checks")
    probe.add_argument("--state", type=Path, required=True)
    probe.add_argument("--user-agent", required=True)
    pub = commands.add_parser("publish", help="Data-only Git publisher; dry run unless --execute is given")
    pub.add_argument("--output", type=Path, required=True)
    pub.add_argument("--checkout", type=Path, required=True)
    pub.add_argument("--execute", action="store_true")
    pub.add_argument("--git", default="git")
    args = parser.parse_args(argv)
    try:
        if args.command == "seed":
            store = Store(args.state)
            with store.lock():
                if bool(args.research) == bool(args.bundle):
                    parser.error("seed requires exactly one of --research or --bundle")
                bundle = json.loads(args.bundle.read_bytes()) if args.bundle else from_research(args.research, args.ledger)
                for collection, rows in bundle.items():
                    for row in rows:
                        store.put(collection, row)
            result = {"seeded": {k: len(v) for k, v in bundle.items()}, "forecasts_created": 0, "validations_created": 0}
        elif args.command == "publish":
            result = publish(args.output, args.checkout, execute=args.execute, git=args.git)
        elif args.command == "probe":
            client = HttpClient(args.state / "http", args.user_agent)
            today = dt.datetime.now(UTC).date()
            urls = [SUPPLY_URL, COMPANY_URL, IR_URL,
                    "https://markets.newyorkfed.org/api/rates/secured/sofr/search.json?startDate=" + str(today - dt.timedelta(days=14)) + "&endDate=" + str(today),
                    'https://efts.sec.gov/LATEST/search-index?q=%22Circle+Reserve+Fund%22&dateRange=custom&startdt=' + str(today - dt.timedelta(days=120)) + '&enddt=' + str(today) + '&forms=N-MFP3&ciks=0000844779&from=0&size=10']
            checks = []
            for url in urls:
                try:
                    raw, receipt = client.get(url, ttl=0)
                    if url == SUPPLY_URL:
                        count = len(parsers.supply_feed(json.loads(raw)))
                    elif url == COMPANY_URL:
                        count = len(submission_rows(json.loads(raw)))
                    elif url == IR_URL:
                        count = len(parsers.ir_release_links(raw, IR_URL))
                    elif 'newyorkfed' in url:
                        count = len(parsers.sofr_feed(json.loads(raw)))
                    else:
                        count = len(json.loads(raw).get('hits', {}).get('hits', []))
                    if not count:
                        raise ValueError('Live source returned no recognized observations')
                    checks.append({"url": url, "ok": True, "bytes": len(raw), "observations": count, "sha256": receipt["sha256"]})
                except Exception as exc:
                    checks.append({"url": url, "ok": False, "error": str(exc)})
            ir_ok = next(r['ok'] for r in checks if r['url'] == IR_URL)
            if not ir_ok:
                try:
                    raw, receipt = client.get(PRESSROOM_URL, ttl=0)
                    links = parsers.pressroom_release_links(raw)
                    if not links:
                        raise ValueError('No dated official earnings-release links')
                    checks.append({'url': PRESSROOM_URL, 'ok': True, 'observations': len(links), 'sha256': receipt['sha256']})
                except Exception as exc:
                    checks.append({'url': PRESSROOM_URL, 'ok': False, 'error': str(exc)})
            release_ok = ir_ok or any(r['url'] == PRESSROOM_URL and r['ok'] for r in checks)
            result = {"as_of_utc": iso(dt.datetime.now(UTC)), "checks": checks,
                      "all_endpoints_passed": all(r["ok"] for r in checks),
                      "required_capabilities_passed": release_ok and all(r['ok'] for r in checks if r['url'] not in (IR_URL, PRESSROOM_URL))}
            atomic_write(args.state / "probe.json", canonical(result))
            print(json.dumps(result))
            return 0 if result["required_capabilities_passed"] else 1
        else:
            if args.as_of and not args.fixture:
                parser.error("--as-of is allowed only in offline replay mode")
            config = json.loads(args.config.read_bytes()) if args.config else {}
            store = Store(args.state)
            with store.lock():
                if args.fixture:
                    bundle = json.loads(args.fixture.read_bytes())
                    now = timestamp(args.as_of) if args.as_of else dt.datetime.now(UTC)
                else:
                    client = HttpClient(args.state / "http", config.get("user_agent", ""))
                    bundle = collect(client, lookback_days=config.get("lookback_days", 500))
                    now = dt.datetime.now(UTC)
                view = tick(store, bundle, now, initial_days=config.get("initial_days", 7),
                            provenance="historical_replay" if args.fixture else "prospective",
                            alert_threshold=config.get("error_alert_threshold", .01), max_fund_lag_days=config.get("max_fund_lag_days", 45))
                export(store, view, args.output)
                health = {"last_attempt_at": iso(dt.datetime.now(UTC)), "status": view["status"], "issues": view["issues"]}
                atomic_write(args.output / "health.json", canonical(health))
            result = {"status": view["status"], "as_of_utc": view["as_of_utc"], "targets": [{"period": r["period"], "status": r["status"]} for r in view["targets"]], "validations": len(view["validations"])}
        print(json.dumps(result))
        return 0
    except Exception as exc:
        if args.command == "run":
            atomic_write(args.output / "health.json", canonical({"last_attempt_at": iso(dt.datetime.now(UTC)), "status": "failed", "error": type(exc).__name__, "message": str(exc)}))
        print(json.dumps({"status": "failed", "error": type(exc).__name__, "message": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
