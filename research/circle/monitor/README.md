# Circle reserve-income monitor

This is the reusable successor to the Q4-2026-only collector. It calculates forecasts without an AI service, discovers new public filings, preserves dated estimates, and scores completed-quarter forecasts when a reliable financial actual becomes available. It is built and tested locally. The dashboard and dated monitor export were published on 22 November 2026; its VM timer and automatic website publisher are not activated.

## What runs automatically

1. Read DefiLlama's USDC circulation history, New York Fed SOFR, Circle's SEC submissions, and the original Circle Reserve Fund N-MFP3 reports. Use Circle's official investor-relations page for release discovery, with its official pressroom as a separate fallback.
2. Keep both the current-quarter scenario and completed quarters awaiting earnings. Year changes and leap years are calculated from dates; no Q4-2026 stop date remains.
3. Use the most recent *published* calibration quarter ending before the forecast quarter. On January 7, the previous Q4's earnings may not be available, so Q3 can still be the valid calibration. The engine stops rather than use financial inputs more than two quarters behind.
4. At seven calendar days after quarter-end, save an initial forecast. If the first successful run is later, record the actual publication timestamp and number of days late; never backdate it.
5. Retain later input-driven updates as separate files. The initial forecast is never replaced. Re-running with unchanged relevant inputs does not create another forecast.
6. Detect earnings releases before generating forecasts. Treat the entire known release day as ineligible for a strictly pre-release forecast. If an image-based release cannot be parsed, show `released_awaiting_actual` until an interpretable filing arrives; do not guess its income.
7. Validate the initial forecast and latest eligible pre-release update separately. Publish dollar error, signed percentage error and separate performance summaries. Large errors remain in the statistics; they can trigger the configured alert flag.

The primary model remains **fund yield × prior company-to-fund yield ratio**. SOFR plus the prior yield gap is an independent benchmark. A missing or stale fund observation makes the primary model explicitly unavailable; the benchmark is not silently relabeled as the primary model. Current-quarter scenarios use flat supply/rates for future dates and are not mixed with completed-quarter accuracy statistics.

## Evidence and data rules

- Monetary calculations use USD millions; annual yields use decimal units. SOFR accrues on 360 days; fund yield and company implied yield use the research's 365-day convention.
- Exclude the current UTC supply bucket. Internal missing supply dates are errors, not zero balances or future projections.
- Carry the latest eligible business-date fund yield across weekends and unreleased observations. Never interpolate future yield observations or use a fund filing before publication.
- The default maximum lag of an observed fund yield is 45 calendar days. This does not apply to explicitly projected future dates. SOFR and supply have separate freshness checks.
- Parse reserve income from dimension-free Circle inline-XBRL contexts, checking the row label, units, scale and reporting interval. Operating-indicator tables require recognized duration/year headers and a stated monetary scale.
- Derive Q4 reserve income from annual less nine months when necessary. A Q4 average USDC derived from rounded annual/nine-month averages is marked as a day-weighted derivation, with its input precision preserved.
- API response bodies, retrieval receipts, financial facts, fund observations, forecasts and validations are retained. Files carrying forecasts/validations are immutable and content-addressed. A process lock prevents overlapping runs; writes replace the small exported view atomically.
- Historical seed data create no forecasts and no scores. `--fixture` runs are always `historical_replay` and never enter prospective accuracy metrics. An arbitrary `--as-of` cannot be used with live collection.
- A critical collection failure leaves the last good `monitor.json` in place and writes a failed `health.json`. A problem affecting only one target quarter preserves that quarter's previous estimate while allowing another fully supported quarter to update.
- TLS verification stays enabled. The initial live test found an expired certificate on `investor.circle.com`; the fallback is `https://www.circle.com/pressroom`, not an unverified connection or proxy.

## Run locally

Python 3.10+ is required; this workspace uses Python 3.12. Install `requirements.txt` in a virtual environment. Only `lxml` is an external dependency. No model API or paid market-data key is required.

From this directory:

```sh
python -m venv .venv
# Activate the environment using your shell's normal command.
python -m pip install -r requirements.txt
python verify.py

# Portable public-data seed exported from the audited research ledger.
python -m circle_monitor seed --bundle data/audited_seed.json --state state

# Copy config.example.json to config.json and set your identifying contact email.
python -m circle_monitor probe --state state --user-agent "CircleResearch/1.0 your-email@example.com"
python -m circle_monitor run --config config.json --state state --output export
```

To regenerate the seed in the complete research workspace:

```sh
python -m circle_monitor seed --research ../reserve_report/repository/circle/data/research.json --ledger ../stage2/results/stage2_data_model.json --state state
```

The audited ledger is necessary for derived historical inputs, especially Q4 2025 income: its exact annual-minus-nine-month derivation was available later than the rounded earnings release. The importer refuses to invent a publication date if this evidence is absent.

Offline integration/replay:

```sh
python -m circle_monitor run --state replay-state --output replay-export --fixture input-bundle.json --as-of 2026-11-03T23:59:59Z
```

An input bundle has `supply` and `sofr` date/value mappings, plus `financials`, `funds` and `releases` arrays. See the parsers and `tests/test_monitor.py` for examples. Synthetic lifecycle tests exercise future quarter transitions; they are not real future financial results.

## Outputs

- `export/monitor.json`: current targets, unchanged historical backtest flag, validation records, prospective metrics, issues and source notices.
- `export/forecasts/<sha256>.json`: immutable forecast inputs, model version, publication time, assumptions and both estimates.
- `export/validations/<sha256>.json`: immutable scored comparisons and the precise forecast file used.
- `export/health.json`: latest attempt status, separate from the timestamp of the last good forecast.
- `state/http/`: original HTTP bodies, first-observation receipts and URL cache indexes. Cached bodies are hash-checked; requests are rate-limited and retry only appropriate temporary errors.

## Website publication and VM scheduling

The data publisher defaults to a dry run:

```sh
python -m circle_monitor publish --output export --checkout /path/to/website
# Explicit publication, only after repository authentication has been configured:
python -m circle_monitor publish --output export --checkout /path/to/website --execute
```

It only stages `circle/data/monitor/`. It refuses website-code changes, symlinks, conflicting immutable evidence, unrelated dirty files, divergent Git history and unpublished non-monitor commits. It uses normal fast-forward pushes, never force-pushes. Its integration test pushes only to a temporary local bare Git repository. Website HTML, `research.json`, old backtests and the current production `live.json` are not modified by this engine.

The new export has its own schema. The local website checkout now reads `data/monitor/monitor.json`, validates its arithmetic, shows the fund-ratio forecast and SOFR comparison, and displays frozen forecasts and earnings comparisons. It automatically rolls the heading forward to the current quarter. Before the new feed is deployed, a cold load retains the explicitly labeled older SOFR-only `live.json`. A failed reload retains the previously loaded valid versioned forecast. These UI changes and the tested dated export were published on 22 November 2026. The website explicitly states that scheduled source updates are not enabled.

`deploy/` contains **inactive** user-systemd templates for an hourly check at minute 17 UTC, with a small random delay and missed-run catch-up. They do not start an AI agent. On the VM, create a separate `~/circle-monitor` environment, import the audited seed, configure the public contact and repository-scoped Git authentication, run a live collection and data-publishing test, then install the reviewed units. The inactive service template includes a data-only publisher after a successful run. Activate it only after automatic publication is authorized, the reviewed dashboard changes are deployed and the Git checkout is configured. Remove its `ExecStartPost` line for a collection-only installation. Keep it separate from the Daily TG News service.

A normal successful job needs no human or AI. Changed filing layouts, conflicting actuals or prolonged source failures can require review. `data/reviewed_amendments.json` records an inspected fund-statement supplement by exact document hash; its exemption does not apply if the document changes. Unknown amendments still flag review. Alert flags are generated data; this version does not send Telegram/email messages or change the model automatically.

## Test evidence

Run `python verify.py` for a durable receipt in `runs/verification.json`. The suite covers the two models at 12 historical cutoff dates, 22 original monthly fund reports, six financial filings, six earnings-period detections, the original SOFR scenario, quarter rollover, publication-time exclusion, missing sources, immutable forecasts, error scoring, locking, HTTP caching and a local Git publication round-trip.

Archived-data tests require the original `Circle/stage2`, `stage3` and report dataset alongside this folder. They report skips when that archive is absent. Their historical reconstruction results are not prospective accuracy claims.

The browser integration tests exercise real-source Q4 data, future-only yield sliders and reset, a clearly labeled synthetic quarter-rollover/earnings replay, corrupt-data rejection, a missing-fund state, legacy-feed compatibility and a phone-width layout. The synthetic fixture is restored to the actual live-data test export before completion. Run `node verify_monitor.mjs` after a live test for the pure JavaScript calculation/schema checks. The original report and historical-model checks remain separate.
