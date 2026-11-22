# Circle Stage 4 research files

The later [transaction-revenue backtest and subscription factor assessment](transactions/Findings.md) tests the user's follow-up hypotheses. It includes a separate formula-linked workbook, early and late cutoffs and explicit missing-data limitations. It does not change the original results or dated Q4 forecast.

Start with [Stage 4 findings](Stage_4_Findings.md). The [protocol](Stage_4_Protocol.md) fixes the investigation's scope and evidence rules. The earlier [plan and revenue mix](Stage_4_Plan_and_Revenue_Mix.md) is retained as a planning record.

The deliverable includes six historical forecasts of other operating revenue, an ARC announcement and milestone timeline, conditional Q3 recognition scenarios, public chain-access tests, a verified USYC fee-mint example, reconstructed USYC/CCTP fee histories and a forward Q4 guidance-based range. All money in the model is USD millions unless a field explicitly says USD or raw token units. Nothing uses private keys or submits transactions.

## Reproduce the analysis from saved inputs

Use the bundled Python runtime, with `-X utf8` on Windows, from the Trading Agent workspace. Required packages are already available: lxml and pypdf. No paid data or credentials are needed. Stages 2 and 3 are local dependencies.

1. `python -X utf8 Circle/stage4/analyze_other_revenue.py`
2. `python -X utf8 Circle/stage4/analyze_product_fees.py`
3. `python -X utf8 Circle/stage4/build_stage4_findings.py`
4. `python -X utf8 Circle/stage4/verify_stage4.py`

`results/other_revenue_model.json` contains the dated category ledger, baseline forecasts, actuals for scoring, conditional ARC cases and RLDC bridge. `results/arc_evidence_timeline.json` distinguishes event dates from public disclosure dates. `results/arc_chain_check.json` records the bounded chain scan and unresolved token identity. `results/product_fee_analysis.json` contains the USYC receipt control, fee aggregates, data coverage and Q4 projection with an unknown actual. `results/stage4_verification.json` independently recomputes key results and verifies public-source SHA-256 hashes.

## Public-source collection

`collect_stage4.py`, `collect_product_history.py`, `collect_fee_validation.py` and `collect_final_event_sources.py` preserve downloaded responses in `raw` and metadata in `source_manifest.json`. Successful and failed attempts are cached. Re-running a collector deliberately reuses its snapshots rather than silently revising the history. Version a failed entry or snapshot intentionally before a new retrieval. Network access may require the application's public-network execution approval. Failed certificate and HTTP requests remain recorded; TLS verification was not disabled.

Run network collectors sequentially: they share the same manifest. They can fetch independent sources concurrently internally. Avoid launching one while a chain script is updating that manifest.

`check_arc_chain.py` queries Arc mainnet read-only, finds UTC September 14 block boundaries, saves zero-address Transfer logs and samples token metadata. The first exploratory metadata loop was stopped after the full log scan because repeated amount matches were expensive and could not authenticate an issuer. The script now caps exploration at 64 contracts and reuses metadata by address. `finish_chain_and_product_checks.py` reconstructs the saved scan, verifies a 500-block subset with another provider and makes current USYC/CCTP endpoint checks. Its `--retry-network-denied` option preserves socket-denied attempts before retrying them in an approved execution context. Saved results record the actual 82-contract metadata sample from the first run; this exceeds the new rerun cap.

The raw primary scan covers only one chain, one UTC day and ERC-20-style mint events. It is an access and identification feasibility test, not an authenticated ARC investor-distribution reconstruction. Do not infer an ARC address from the token name, amount or chain name.

## Interpretation

The original Q3 outcome was known before Stage 4. Earlier company disclosures support an approximately $180m ARC annual revenue expectation and Q3 milestone evidence; assigning the annual amount to Q3 remains a scenario. Current DefiLlama history and adapter code are reconstructed observations, not archived pre-earnings vintages. The USYC adapter's November 17 revision was after Q3 earnings. Protocol fees are not automatically the same as consolidated GAAP revenue.

The report retains the original Stage 3 partner-cost bridge. Its improvement from adding an ARC timing case is conditional; a full partner/platform distribution forecast remains later work. No Stage 3 workbook forecasts were overwritten.

The Q4 range is recorded as of November 21, 2026, before Q4 results. Preserve it for subsequent evaluation. Changes from new information should be stored as new dated forecasts, not replacements for this record.

The separate `results/2026-11-21_Q4_other_revenue_forecast.json` records that forecast with its source PDF hash. The findings builder refuses to overwrite it with changed inputs.

The later [on-chain extensions and services regression](../stage5/Stage_5_Findings.md) reconstruct Ethereum USDC flows, CCTP activity and USYC fee history, and test the three requested market factors. Its dated Q4 USYC fee-component projection is separate from the total-other-revenue forecast above. The direct Ethereum CCTP fee series has a disclosed 3.53% difference from the earlier aggregator series; earlier transaction backtest inputs are retained.
