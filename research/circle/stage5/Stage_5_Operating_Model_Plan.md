# Stage 5: turn the revenue evidence into earnings and valuation

Framework update, 22 November 2026: the [current report structure](../Report_Framework.md) has two main parts: first catalogue and validate accessible Circle-related data, then use it to estimate and evaluate EPS. This document remains the detailed operating-model work plan. The completed RLDC work feeds Part II; valuation is now an optional later extension.

Updated 21 November 2026. The user has chosen a simple operating-other-revenue case. The preceding regression and on-chain extensions are completed supporting work. The main next phase returns to the original equity-research sequence: revenue → retained revenue → operating earnings → EPS/cash flow → valuation.

## Agreed revenue assumptions

Reserve income continues to use the established global daily USDC supply and reserve-yield methodology. It is the empirical centerpiece. It is a completed-quarter nowcast when quarter-wide supply/yield observations are available; a genuinely future-quarter forecast still needs explicit future supply and rate assumptions.

Hold each non-ARC operating-other-revenue component flat at the latest reported quarter, Q3 2026. Do not carry forward the reported total-other line containing the large ARC item. Do not add a separate USYC growth forecast on top of a flat services total, because that would change the user's chosen case and could double-count the existing fee component.

| Operating revenue component ($m) | Q4 2026 working case | Each subsequent quarter |
| --- | --- | --- |
| Subscription/services | 19.587 | 19.587 |
| Transaction revenue | 5.335 | 5.335 |
| Remaining product-level other, excluding ARC (approximate) | 0.542 | 0.542 |
| Non-ARC operating other subtotal | 25.464 | 25.464 |
| Existing ARC presale recognition | 60.400 | 0 |
| Total operating other revenue (approximate) | 85.864 | 25.464 |

The small residual is $182.342m reported product-level Other less $181.8m disclosed ARC recognition; it is approximate because the ARC amount is rounded. These targets come from [Q3 2026 Form 10-Q, Note 11](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm). Flat subsequent quarters imply approximately $101.856m annual non-ARC operating other revenue. The distinct non-operating “other income (expense), net” line is not included in this revenue subtotal and belongs in the earnings bridge.

The $60.4m remaining balance is supported by the filing's approximate $242.2m presale proceeds less $181.8m recognized. Full Q4 recognition is the user's modeling assumption, not a confirmed issuer recognition schedule. Recognition contributes revenue; it is not automatically $60.4m net profit or new Q4 cash. Assume no new unannounced token sales, with future issuer announcements/filings as revision triggers. This does not imply that future sales are impossible.

The earlier guidance-implied Q4 operating-other range is approximately $27.529m–$47.529m. Thus the new $85.864m working case lies above that benchmark. Preserve both cases and explain that the departure principally reflects the assumed additional ARC recognition. The older dated guidance and ARC-scenario JSON files are not overwritten. New assumptions are in `results/2026-11-21_flat_other_ARC_working_case.json`.

## Arc activity evidence

We downloaded DefiLlama's public daily spot-DEX volume history for Arc, Ethereum, Solana and Base. Requests follow `https://api.llama.fi/overview/dexs/arc?excludeTotalDataChart=false&excludeTotalDataChartBreakdown=true&dataType=dailyVolume`, replacing the chain name for each peer. Sum the `totalDataChart` values dated 22 October–20 November 2026 inclusive, then divide by 30. All four series contain all 30 dates; the partial/current date 21 November is excluded. This is the arithmetic mean of daily tracked spot DEX trading volume, not an average of a dashboard's changing 24-hour readings.

| Chain | 30-day total spot DEX volume | Mean daily spot DEX volume | Arc as a proportion of peer |
| --- | --- | --- | --- |
| Arc | $582.932m | $19.431m | — |
| Ethereum | $56.343bn | $1.878bn | 1.03% |
| Solana | $49.474bn | $1.649bn | 1.18% |
| Base | $32.660bn | $1.089bn | 1.78% |

Sources: [Arc API](https://api.llama.fi/overview/dexs/arc?excludeTotalDataChart=false&excludeTotalDataChartBreakdown=true&dataType=dailyVolume), [Ethereum API](https://api.llama.fi/overview/dexs/ethereum?excludeTotalDataChart=false&excludeTotalDataChartBreakdown=true&dataType=dailyVolume), [Solana API](https://api.llama.fi/overview/dexs/solana?excludeTotalDataChart=false&excludeTotalDataChartBreakdown=true&dataType=dailyVolume), [Base API](https://api.llama.fi/overview/dexs/base?excludeTotalDataChart=false&excludeTotalDataChartBreakdown=true&dataType=dailyVolume).

This supports the wording **“Arc's tracked spot-DEX activity remains small relative to established chains.”** It does not support “all Arc volume is very low” or prove that future institutional token sales will be zero. The [Arc bridge dashboard](https://defillama.com/bridges/chain/arc), labeled 20 November, reports $4.443bn over 30 days, about $148.1m/day; that is a different, larger activity measure and is retained as contextual counter-evidence. Payments, spot swaps, perpetual trading, bridging and token fundraising have different meanings and must not be pooled as one volume measure. App fees and blockchain fees also do not automatically accrue to Circle shareholders.

Raw API responses, retrieval times, SHA-256 hashes and all 120 dated observations are in `arc_activity/`. `arc_activity/verification.json` checks coverage, averages and source integrity. Initial sandbox socket-denied attempts are preserved in its manifest; the subsequent permitted public-network retrieval succeeded. Four downloaded source payloads passed hash checks. These are current provider snapshots, not archived historical vintages or an independent all-protocol volume audit.

## Stage 5A: distribution economics and RLDC

Completed: [eight-method cost comparison and dated Q4 RLDC forecast](rldc/Findings.md). The pooled ratio's six-quarter cost MAPE is 0.94%, and end-to-end non-ARC RLDC MAPE is 2.98%. The working Q4 scenario gives approximately $280.1m underlying RLDC and $340.5m including conditional ARC recognition. These are not net income or validated precision bounds. Historical targets were already known before this reconstruction; earlier dated scenarios remain intact.

The next substantive task is to estimate how much reserve income Circle retains after distribution costs. Extract historical Coinbase/other-partner distribution costs, platform balances/mix, and contract changes from primary filings and agreements. Reconcile them to the reported total distribution, transaction and other costs. Distinguish contractual terms from empirical ratios; a labeled exchange wallet is not automatically the full contractual balance used to calculate payments.

Reproduce the issuer's definition: RLDC = total revenue and reserve income minus total distribution, transaction and other costs. Compare (1) the existing lagged cost-to-reserve-income ratio baseline and (2) a partner/platform driver model if enough public evidence exists. Calibrate only with information public at each target cutoff and score quarter-by-quarter errors. If partner detail cannot be observed, retain a transparent baseline and sensitivity range rather than fill the gap with unsupported precision.

Output: a sourced cost ledger, formula-based revenue-to-RLDC bridge, historical errors, and Q4 scenarios. Show underlying RLDC excluding ARC recognition alongside reported-case RLDC.

## Stage 5B: operating expenses, earnings and cash flow

Forecast compensation, technology/infrastructure, marketing and administrative costs from disclosed history, guidance and identifiable changes. Separate recurring cash expenses, stock-based compensation and one-off items. Bridge RLDC through operating income, non-operating income/expense, tax, noncontrolling interests where applicable, and diluted shares to GAAP net income and EPS. Reconcile adjusted measures separately; do not call adjusted earnings GAAP earnings.

Present both the reported scenario containing $60.4m ARC recognition and underlying earnings excluding it. In the cash-flow reconciliation, releasing previously collected deferred revenue does not create another $60.4m cash receipt. Track the deferred balance down to zero under the selected timing case.

Output: Q4 forecast and a forward operating model, with explicit underlying/reporting differences and operating sensitivities.

## Stage 5C: expectations, scenarios and valuation

Compare the selected forecast with management guidance and available analyst estimates. Use the connected LSEG/Workspace tools or established access method if suitable; no need to print or move the user's key. Check estimate timestamps. Claim to have beaten consensus only if a credible archived pre-release consensus snapshot exists.

Extend to a three-year model with bull/base/bear assumptions for USDC supply, reserve yield, distribution economics and expenses. Keep flat non-ARC other revenue and zero new unannounced ARC sales in the base case unless the user revises them. Show the effect of delayed ARC recognition separately from the recurring growth cases. Cross-check valuation with a justified cash-flow method and suitable comparables, explicitly addressing dilution and the limited comparability of peers. Customer reserve assets and their matching liabilities are not freely distributable corporate cash and cannot be added to shareholder value as excess cash.

Output: a supported valuation range, expectation gap and investment thesis suitable for the research report. Following the completed Stage 5A comparison, the next priority is Stage 5B; a strong reserve-income estimate alone does not establish a strong EPS or valuation estimate.

## Stage 6: write the application sample

Once the model is coherent, prepare the concise research report and technical appendix. Feature the validated reserve nowcast, Ethereum stock-flow reconciliation and source-to-financial-line methodology. Include the failed/weak services-factor model as a bounded robustness test rather than as a main forecast. Preserve errors and limitations so the analysis can be defended in an interview.
