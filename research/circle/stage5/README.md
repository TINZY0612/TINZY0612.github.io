# Circle on-chain extensions and services regression

Completed from public data on 21 November 2026. Start with [Stage_5_Findings.md](Stage_5_Findings.md). The stage label follows the latest research extension; the broader company analysis and valuation in the original proposal remain later work.

The subsequent [operating-model plan](Stage_5_Operating_Model_Plan.md) returns to that broader Stage 5. It records the latest user-selected flat non-ARC revenue case, separate conditional Q4 $60.4m ARC recognition, and a new 30-day Arc/peer DEX activity comparison. Run `collect_arc_activity.py` to reuse its public snapshots and `record_working_case.py` to check the dated case and activity calculations. New evidence files are in `arc_activity`; older forecasts and the existing regression workbook are preserved.

Stage 5A is now complete: [distribution-cost and RLDC findings](rldc/Findings.md) compare eight rules across six quarters and record a prospective Q4 RLDC case. The pooled three-quarter cost ratio is the provisional working method. The remaining work is operating expenses, EPS, expectations and valuation.

## Reproduce from saved inputs

From the Circle directory, run these sequentially using the bundled Python and Node runtimes (Python needs NumPy; Node uses the bundled `@oai/artifact-tool`). No packages were installed and no credentials are required.

```text
python -X utf8 stage5/regression.py
python -X utf8 stage5/analyze_onchain.py
python -X utf8 stage5/forecast_supply.py
python -X utf8 stage5/forecast_usyc_forward.py
node stage5/build_workbook.mjs
python -X utf8 stage5/verify.py
python -X utf8 stage5/build_findings.py
```

Local dependencies are the financial ledger in Stage 4, quarter definitions in Stage 2, saved NY Fed rates in feasibility, the total stablecoin series in Stage 4 transactions, and the current issuer USYC API snapshot in Stage 4. Missing-date and contract-event checks fail rather than silently impute values.

The main output workbook is saved in `../outputs/01a1fcd4-2a0f-7c92-a89f-a871c89c1db7/`. Preview PNGs are in `previews`. `results/verification.json` checks raw-source hashes, the independent OLS calculation, fee/NAV arithmetic, exact raw-unit flow reconciliation and exported formula caches. It also records hashes of the prior dated ARC and other-revenue forecasts. Native Excel application recalculation was not tested.

## Collect or intentionally refresh public data

`collect_markets.py` collects daily BTC candles, USDC history and official token source. `collect_chain.py` queries Ethereum read-only using public RPCs for USDC mint/burn, CCTP messages/fees, reporter events, historical supply and block times. `public_data.py` handles caching and source manifests. Run collectors sequentially because they share one manifest. Internal independent market downloads use a small thread pool.

Successful cached responses are reused. Failed/limited provider responses remain recorded. An intentional refresh should use a new dated snapshot/manifest and separate result path so historical inputs and forecasts are not silently revised. These current historical series are not archived point-in-time vintages. No private keys, signing or transactions are involved.

Public providers can rate-limit or change access. The successful full-quarter log/state collection used Tenderly's public Ethereum gateway; PublicNode supplied block data; dRPC was an additional fallback. `eth_getLogs` requests split adaptively on provider limits. Contract identity comes from official Circle registries/source, not RPC labels. Report timestamps are fetched from actual blocks.

`archive_large_snapshots.py` compressed 123 large responses/derived log files losslessly from approximately 1.55GB to 238MB. Readers handle `.json.gz` automatically. Original payload hashes remain in the source manifest and `results/archive_manifest.json`; verification hashes decompressed content. The originals were removed only after equality checks. Repeating compression is optional after a fresh collection.

## Model boundaries

- Seven quarters support the primary regression, regardless of its 638 daily factor inputs. R² is in-sample; leave-one-out is not a forward-time backtest.
- Ethereum supply is not global circulating USDC. CCTP activity is migration; non-CCTP residuals are not authenticated fee-paying fiat redemptions.
- CCTP source routes and destination fees are different populations. Direct Ethereum fees differ from the prior aggregator series by 3.53%; unresolved, both retained.
- USYC fees are a measurable component, not an audited reconciliation to all consolidated services revenue. Observation dates can differ from accrual dates.
- The Q4 USYC file is a dated prospective fee-component scenario with unknown actual, separate from the earlier total-other-revenue and ARC forecasts. Its script refuses changed-input overwrite.
- Chain mix includes provider bridge adjustments. Arc-chain USDC is not evidence of ARC token sales.

`Protocol.md` preserves the scope and primary regression specification written before fitting. `results/subscription_regression.json` stores the full daily/quarterly inputs, source financial URLs, results, diagnostic fits and checks. The findings report explains exact units, transformations, formulas and cutoffs.
