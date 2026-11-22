# Circle reserve income test files

Start with [the findings](Stage_3_Findings.md). The [protocol](Stage_3_Protocol.md) records the rules, accepted supply tolerances, cutoffs, and the later extension to on-chain verification of other revenue.

The Excel output is `../outputs/01a1fcd4-2a0f-7c92-a89f-a871c89c1db7/Circle_Reserve_Income_Backtest.xlsx`. It contains reserve-income estimates and errors, an RLDC bridge with one cost-case selector, financial source observations, and a daily input/calculation table. Monetary values are USD millions. Financial results remain actuals when cases change. The fund model is a proxy, not an exact dividend or reserve-portfolio accounting model.

## Reproduce

Use the bundled Python and Node runtimes. No credentials or paid data are required for this stage. Existing feasibility and Stage 2 source snapshots are dependencies.

1. `python collect_stage3.py index` retrieves the SEC fund search and submissions metadata.
2. `python collect_stage3.py funds` retrieves the individual fund XML filings and checks series identity.
3. `python analyze_stage3.py` builds the 12 dated simulations, daily input tables, eligibility records, source hashes and 269 checks.
4. `python verify_stage3.py` independently recomputes the primary results and tests target-only financial shocks.
5. `node build_workbook.mjs` builds and recalculates the Excel workbook using the bundled `@oai/artifact-tool` dependency. The local `node_modules` junction points to the bundled runtime and is not a project dependency installation.
6. `python verify_export.py` independently reads exported XLSX XML to verify cached results and detect Excel errors.
7. `python compare_yield_adjustments.py` reproduces the subsequent user-requested additive-versus-proportional comparison. Results are in `results/yield_adjustment_comparison.json`; the original workbook retains its additive model.

Network collectors save public responses with retrieval timestamps and SHA-256 checksums. Re-running them reuses already successful snapshots. Remove or version a snapshot deliberately before requesting a new one. This preserves the research history by default.

`results/stage3_model.json` holds the analytical results. `daily_model_inputs.json` records each selected fund observation and its filing date. `original_fund_reports.json` provides the monthly source register. `excluded_amendments.json` records two amendments filed after the sample's last earnings cutoff. `source_integrity.json` hashes the files consumed by the model.

## Interpretation

These are publication-filtered historical simulations using current supply and benchmark history. They are not strict point-in-time or live forecasts. Actual quarterly targets were already known when the protocol was fixed. All six quarters remain in the evaluation, including the Q3 2026 other-revenue surprise. Six quarters and a slowly changing yield spread do not establish performance in a different rate or distribution regime.

The workbook was checked with Artifact Tool recalculation, representative input changes, exported cached values and visual inspection. Native Microsoft Excel recalculation has not been separately tested. It contains no licensed Workspace responses or credentials. The previous Workspace verification remains in Stage 2.

The bundled authoring process returned exit status 1 after saving the workbook and reporting all 47 internal checks passed, without an accompanying JavaScript error. The saved ZIP/XML was then independently read and passed all 184 export checks with no Excel error cells. The nonzero process shutdown remains an unresolved runtime issue; successful file validation is recorded separately from that exit status. The `qa` folder contains counterfactual target-shock output from validation and is not an additional set of research results.
