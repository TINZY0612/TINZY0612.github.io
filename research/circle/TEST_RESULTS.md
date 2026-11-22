# Test results

All nine offline suites below passed from this public research copy on 22 November 2026. No credentials, paid data connection, live source download, GitHub push or scheduler activation is involved in these tests. The Git publication tests use temporary local bare repositories.

| Suite | Passed | What it establishes |
| --- | ---: | --- |
| Report data | 261 / 261 | Independent reserve-income arithmetic, historical errors, cutoff eligibility, source hashes, dates and web links. |
| Historical JavaScript model | 54 / 54 | Browser model arithmetic and future-only scenario behavior. |
| Reusable monitor Python | 37 / 37, no skips | Original filing parsers, 24 historical estimate replays, quarter rollover, immutable forecasts, release barriers, scoring, source failures and local Git publication. |
| Monitor JavaScript | 13 / 13 | Export validation, both methods, future-only yield sensitivities, missing data, corrupted values and year rollover. |
| Independent Stage 3 checks | 55 / 55 | Recalculated historical methods and target-outcome contamination controls. |
| Exploratory other revenue | 1,031 / 1,031 | Archived public-source integrity and arithmetic; 366 unique public files hashed. |
| Exploratory transaction revenue | 76 / 76 | Fee bridges, forecast arithmetic and exported workbook cache/formula checks. |
| On-chain extensions | 43 / 43 | Extraction controls and independent calculations; 307 source responses and 123 archives hashed, with no hash failures. |
| RLDC extension | 98 / 98 | Cost bridge, forecast arithmetic, source timing and workbook controls; 17 received sources checked. |

The separate [report publication check](verification/report_publication.json) verifies that the online report includes every nonempty body paragraph from the latest Word file, the exact embedded signed-error image, the other nine tables, and matching Word/PDF download bytes. The PDF has 14 pages and was visually inspected locally before publication.

## Reproduce

Install the dependencies and make Node.js and Git available as described in the [README](README.md), then run from this folder:

```sh
python verify_snapshot.py --extended
```

The first run verifies `FILE_MANIFEST.json` before running the suites. Test scripts update their output receipts, so use `--skip-manifest` only when repeating tests in a clone whose generated receipts have already changed. The committed raw input bytes remain independently inspectable.

See [verification/public_run.json](verification/public_run.json) for per-suite exit status, duration and captured output. The monitor's detailed receipt is [monitor/runs/verification.json](monitor/runs/verification.json).

## What a pass does not establish

These are software, source-integrity and calculation controls. They do not establish that future reserve-income errors will remain below 0.5% or 1%, that exploratory other-revenue/RLDC methods are accurate, or that the project forecasts EPS. The current monitor has no completed prospective earnings validation yet. Historical ratio-model selection used the same six-quarter sample; the report describes that limitation.

Workbook checks inspect formulas and cached results. They do not claim that native Microsoft Excel recalculation was tested. Original workbook-building scripts may require the author's artifact-authoring environment; those private dependencies are not redistributed and are unnecessary for the offline checks above.
