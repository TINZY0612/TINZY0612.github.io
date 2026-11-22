# Circle stage two

`Stage_2_Findings.md` explains the results. The authoritative calculation dataset is `results/stage2_data_model.json`. The workbook is saved under `Circle/outputs/01a1fcd4-2a0f-7c92-a89f-a871c89c1db7/`.

## Reproduce from saved public data

Run `build_actuals.py` with Python including `lxml` and `pypdf`. This also checks the saved local Workspace revenue responses. Run `build_workbook.mjs` with Node and `@oai/artifact-tool` to regenerate the workbook, calculation checks, and previews. This run used Codex's bundled dependencies and a local junction to the bundled Node packages.

The authoritative dataset separates source observations, quarterly derivations, comparative checks, provider cross-checks, and supply decomposition. Dates are calendar dates, with UTC used for blockchain snapshots. Financial inputs use USD millions, supply uses token millions, and rates are decimals. Original units and precision remain in the JSON observations. Q4 2025 average supply is rounded to USD 0.1 billion. Later comparative KPIs retain their later publication dates.

## Source refresh

`collect_stage2.py` downloads the original financial filings, filing-date metadata, and adapter configuration. `collect_reconciliation_sources.py` downloads the additional reserve reports and Q4 release. `collect_earnings_calendar.py` verifies six original earnings announcements. The image-source manifest records the two operating and financial tables embedded in the Q4 release. `adapter_manifest.json` records the extra aggregation files inspected. Refreshes replace named snapshots, so preserve a copy before refreshing.

The stage reads the saved feasibility USDC dataset and two reserve reports without altering them. Raw licensed Workspace responses are kept in `licensed/`. The local `workspace_crosscheck.py` reuses the previously authorized desktop helper and keeps credentials in memory. A logged-in Workspace desktop session is required for a refresh. No new credential entry is required while that setup remains available.

The initial Workspace query that returned repeated annual values is retained as an unsuccessful frequency specification, not used as quarterly evidence. Only the two explicitly anchored fiscal-quarter queries feed the comparison checks.

## Verification

`results/validation_checks.json` records source and arithmetic checks. `results/workbook_validation.json` records 49 independent workbook-value comparisons and input-change tests. The formula scan, rendered workbook previews, and rendered source report pages are saved for review. Native Microsoft Excel recalculation was not separately tested. The exported formulas were calculated using Artifact Tool.

The gap decomposition is algebraic. It is not a set of proved corrections to the supply series. Daily provider buckets are not exact historical EOD states, and current retrieved history is not a vintage archive. These limits remain part of the next model stage.
