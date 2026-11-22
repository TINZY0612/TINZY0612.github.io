# Circle equity research proposal

**Current structure, revised 22 November 2026:** [Part I: public-data extraction and validation; Part II: an EPS forecasting model and evaluation](Report_Framework.md). This replaces the original report organization while preserving the stage folders and dated forecasts below. The main endpoint is a defensible EPS estimate and a comparison showing the incremental value of on-chain data. Valuation is an optional later extension.

Prepared 21 November 2026 for an undergraduate application to the Binance On Chain Research Analyst role.

## Research objective

Build a reproducible equity research report that tests how accurately public blockchain data and free financial data can estimate Circle's quarterly reserve income before earnings are released. Extend the model to total revenue, revenue less distribution costs, and equity valuation, with uncertainty increasing as the analysis moves further down the income statement.

The proposed central question is: **How much of Circle's financial performance can an outside analyst observe before an earnings release, and where does public visibility end?** This connects on-chain data engineering with financial statement analysis, forecasting, and valuation.

Stages 3 and 4 are complete for reserve-income testing and the requested other-revenue investigation. See the [Stage 3 findings](stage3/Stage_3_Findings.md) and [Stage 4 findings](stage4/Stage_4_Findings.md). Stage 4 establishes earlier ARC sale, guidance and mint announcements, conditional recognition scenarios, a verified USYC fee-mint example and USYC/CCTP fee histories. ARC's token contract and investor/escrow wallets remain unauthenticated. Current historical data are not archived historical vintages. A dated Q4 other-revenue forecast is recorded for future scoring; a full partner-cost model, audited product reconciliation, consensus comparison, valuation and final report remain subsequent work.

This proposal covers the research design and an initial source check. Following approval in chat, the first feasibility stage was completed on 21 November 2026. The [feasibility report](feasibility/Feasibility_Report.md) records the results and narrows the initial historical testing scope. The full financial model, backtest, investment conclusion, and final equity report remain subsequent work.

## Initial findings and implications

Circle's FY2025 Form 10-K is the starting financial reference. It describes reserve income and distribution arrangements, including payments to Coinbase. This means USDC growth must be assessed alongside how much of the resulting income Circle retains. [FY2025 Form 10-K](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000062/crcl-20251231.htm)

The latest quarterly reference identified in this source check is Q3 2026. Its revenue note reports $181.8 million of ARC token presale revenue. A supply-times-yield model therefore cannot explain all reported revenue. The model should separately forecast recurring reserve income, other operating revenue, and revenue with specific recognition conditions. [Q3 2026 Form 10-Q, Note 11](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm)

Circle publishes reserve composition and mint/redemption disclosures, while BlackRock publishes information about the Circle Reserve Fund. These are off-chain financial disclosures that can complement the blockchain record; the reserve portfolio itself is not fully observable on-chain. [Circle transparency](https://www.circle.com/transparency), [BlackRock Circle Reserve Fund](https://www.blackrock.com/cash/en-us/products/329365/circle-reserve-fund)

The proposed contribution is an independently validated model with an explicit information cutoff for every forecast. Simply plotting USDC supply against interest rates would be a useful starting chart, but would leave the main accounting and forecasting questions unanswered.

## What we need to estimate

| Model component | Required information | Proposed treatment |
| --- | --- | --- |
| Reserve balances | Daily native USDC supply by chain; EURC where material; differences between token supply, company circulation metrics, and financial reserves | Reconcile daily supply to official disclosures before treating it as an earning-asset proxy |
| Portfolio allocation | Reserve-fund assets, direct Treasury holdings, repo exposure, and bank cash | Use the most recent information available at each forecast date; show uncertainty where allocations are unavailable |
| Realized yield | Fund distributions or yield history, Treasury and repo benchmarks, bank yields, management fees, and rate transmission lags | Estimate a blended reserve return; avoid treating a quoted market yield as realized accounting income |
| Other revenue | Subscription and integration services, transaction fees, fund-management fees, and ARC-related recognition | Separate recurring and event-dependent components; identify the observable driver and remaining assumption for each |
| Distribution costs | Coinbase arrangements and platform mix; Binance and other partner arrangements; effective dates and incentives | Reconstruct disclosed economics; use lagged effective rates and scenarios where contractual inputs are private |
| Operating earnings | Compensation, stock-based compensation, infrastructure costs, taxes, and unusual items | Forecast from filings and guidance, with a clear bridge from retained revenue to GAAP earnings |
| Equity value | Sustainable growth, retained margins, reinvestment, corporate cash/debt, and diluted shares | Build scenarios and valuation sensitivities after validating the operating model |

Circle's Q3 filing distinguishes its circulation metric from raw token supply, including treatment of tokens allowed but not issued, access-denied tokens, and pending burns. It also describes differences between reserve assets and its circulation-based presentation. These distinctions make reconciliation a core part of the project. [Q3 2026 Form 10-Q, key operating indicators and reserve composition](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm)

## Free data sources and existing references

| Source | Use in this project | Access and limitation identified so far |
| --- | --- | --- |
| [Circle FY2025 annual report](https://s206.q4cdn.com/265218871/files/doc_financials/2025/ar/CRCL_AR_2026_WO13_WKV_PR-1.pdf) and [SEC filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000062/crcl-20251231.htm) | Audited statements, business model, accounting policies, historical disclosures | Annual-report PDF downloaded locally. Direct SEC HTML downloads returned HTTP 403; the filing was readable through web retrieval |
| [Circle Q3 2026 filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm) and earlier quarterly filings | Quarterly targets, updated product economics, distribution costs, and guidance | Public documents. Extract standalone quarters carefully from year-to-date data and preserve original publication dates |
| [SEC data APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | Standard financial facts and filing timestamps | Free public JSON interfaces. Company-specific metrics may still require inline XBRL or document extraction; full extraction has not been tested |
| [Circle transparency](https://www.circle.com/transparency) | Official reserve checks, asset allocation, and examination reports | Public page with weekly disclosures and monthly assurance reports. Historical publication timing needs to be recorded |
| [Circle contract directory](https://developers.circle.com/stablecoins/usdc-contract-addresses) | Establish the correct native token universe | Public documentation. Historical deployments, migrations, and discontinued chains need their own dated registry |
| [DefiLlama free API documentation](https://api-docs.defillama.com/llms-free.txt) | Daily aggregate supply and chain distribution | Live request to `https://stablecoins.llama.fi/stablecoin/2` succeeded without a key and returned USDC, 2,994 history records, and chain-balance fields. Units, coverage, and historical revisions still need validation |
| [DefiLlama Circle USDC dashboard](https://defillama.com/protocol/circle-usdc) and [source code](https://github.com/DefiLlama/dimension-adapters/blob/master/fees/circle.ts) | Existing revenue estimate and methodological benchmark | Public dashboard and inspectable adapter. Its definition of revenue is reserve yield collected by Circle; do not treat it as retained profit or an independent reported earnings figure |
| [BlackRock Circle Reserve Fund](https://www.blackrock.com/cash/en-us/products/329365/circle-reserve-fund) | Reserve-fund holdings, yield information, and distributions | Public product information. The availability of a complete daily historical export remains to be established |
| [FRED three-month Treasury yield](https://fred.stlouisfed.org/series/DGS3MO) | Free rate proxy for a simple baseline | Public series page is readable; the CSV request timed out in the initial check. It is a market benchmark, not Circle's realized portfolio yield; examine SOFR and shorter maturities during implementation |
| [Artemis stablecoin overview](https://www.artemis.ai/sectors/stablecoins/overview?tab=usage) | Adoption and usage comparisons | Public dashboard inspected. Historical bulk downloads and API access on a free tier are not established and are not assumed in the core plan |
| [Circle Reserve Visualizer](https://circle-reserves-visualizer.vercel.app/) | Reference for displaying reserve composition over time | Third-party dashboard links examination reports. Trace figures to Circle's originals before relying on them; not a financial ground truth |
| [BIS Bulletin 125](https://www.bis.org/publications/bulletin-125-stablecoin-remuneration-centralised-exchanges) and [online annex](https://www.bis.org/publ/bisbull125_annex.pdf) | Independent discussion of exchange remuneration and reserve-income sharing | Public research. Useful for understanding the economics; the governing filings remain the source for company-specific accounting |

These references reduce the need to build every dataset from scratch. We should still demonstrate some original on-chain extraction and reconciliation so the application shows more than dashboard aggregation. Dune is a possible SQL and presentation layer, but no specific Circle earnings dashboard has been validated in this initial check.

The core research will target a zero-dollar data budget. Python, pandas, requests, and PDF/XBRL extraction tools are proposed for the pipeline. Paid APIs and archive-node subscriptions are excluded from the initial plan. Historical RPC calls can be rate limited or require archive access; the first implementation stage will determine how much direct extraction is feasible for free.

## Proposed model

Start with an interpretable daily model rather than machine learning:

`Quarterly USDC reserve income estimate = sum over days [estimated reserve balance × estimated annualized blended yield × applicable day fraction]`

Estimate blended yield using separate reserve-fund, direct-Treasury, repo, and cash components where the data supports them. Document each rate's convention, fee treatment, and income-recognition timing. Use a simple supply-times-benchmark model as a baseline, then measure whether portfolio detail improves it.

The remaining bridge is:

`Total revenue and reserve income = USDC reserve income + EURC reserve income + other revenue`

`Revenue less distribution costs = total revenue and reserve income − total distribution, transaction, and other costs`

`Operating income = revenue less distribution costs − operating expenses`

Then bridge to net income and diluted EPS using non-operating items, taxes, and the appropriate share count. Maintain Circle's reported definitions and reconcile every non-GAAP measure to its GAAP counterpart.

Do not deduct partner payments from gross reserve income and then deduct them again in the retained-revenue bridge. Likewise, avoid subtracting fund fees twice when using a yield that is already net of expenses.

For distribution costs, first test a lagged effective-cost ratio. Add a platform-mix model only if it improves forecasts with information available at the time. Labeled exchange wallets are an incomplete proxy for a contractual platform balance, and customer ownership cannot be inferred reliably from every omnibus address.

## On-chain research contribution

User scope update, 21 November 2026: accept absolute supply differences within 0.5% as the preferred tolerance and within 1.0% as the outer limit. These are supply-data acceptance criteria, not earnings-forecast accuracy targets. Preserve measured differences and definition/timing qualifications without delaying the reserve-income model for an exact match.

Further development: assess whether Circle's non-reserve revenue streams can also be verified on-chain. Map each product's contracts, fees, settlements and token events to the relevant revenue-recognition policy. Separate observable usage and cash receipts from recognized revenue and quantify private or unobservable components. This extension follows the initial reserve-income and RLDC work.

Create a dated registry of native USDC contracts, then independently reconstruct daily supply and issuance/redemption activity for chains with workable free historical access. Compare those results with the aggregate dataset and official disclosures. Include all relevant chains through the aggregate source and disclose the proportion directly validated.

The registry must distinguish native USDC from bridged or wrapped claims. Counting a bridge's locked USDC and its wrapped representation as two independent reserve-backed balances would overstate earning assets. Cross-chain burn/mint transfers must also be separated from fiat-driven issuance and redemption when analyzing flows.

Use chain concentration, exchange and DeFi balances, holder concentration, and sustained net issuance to investigate the durability of demand. Transfer volume and address counts are adoption indicators to test, rather than assumed direct drivers of reserve revenue. Filter internal transfers and explain label uncertainty before presenting payment-use claims.

For the Binance application, include a focused distribution analysis: how exchange-held USDC and incentives could change Circle's retained economics. Use public disclosures and defensible wallet labels; quantify uncertainty around unobserved arrangements.

## Backtest design

Target 2023 through Q3 2026, subject to comparable quarterly targets and recoverable data. Use older annual data for context when standalone quarters cannot be established. Segment changes in accounting, products, and distribution agreements instead of fitting one stable relationship across every regime.

Run three distinct exercises:

1. **Historical reconstruction:** use the best available history to explain reported income. This checks accounting and data quality, but does not establish forecasting performance.
2. **Quarter-end nowcast:** estimate the completed quarter before earnings, using only information available at that dated cutoff.
3. **Earlier forecast:** issue estimates 30 days before quarter end, forecasting the remaining supply and rate path. Keep this uncertainty separate from the quarter-end exercise.

For each exercise, compare a prior-quarter carry-forward baseline, daily supply with a lagged yield assumption, daily supply with observable rate benchmarks, and the more detailed reserve/distribution model. Show reserve income, total revenue, and retained revenue separately so a good reserve estimate cannot conceal a poor revenue forecast.

Use an expanding training window and a final untouched holdout of at least two quarters if coverage permits. Report the sample count, dollar error, percentage error, mean absolute error, bias, and quarter-by-quarter results. Evaluate interval coverage if the sample supports it. Diagnose errors as supply, yield, allocation, distribution, other-revenue, or accounting effects.

Record the observation period, publication timestamp, retrieval timestamp, and revision status for each input. A later attestation, a retrospectively updated wallet label, or realized quarter yield cannot be inserted into an earlier forecast. If historical publication timing cannot be established, label that test as a reconstruction or a backtest using assumed publication lags. Do not call it a strict historical forecast.

Better accounting forecasts do not automatically imply stock-market alpha. A market-reaction study would be separate and would need dependable historical share-price and expectations data. Do not claim to beat analyst consensus unless a dated, comparable consensus series is available.

## Full company coverage and valuation

The final report should explain Circle's products, management and governance, distribution strategy, competitive position, and demand for USDC relative to other stablecoins. Review regulatory filings and official rulemaking for reserve requirements, permissible activities, reward arrangements, and jurisdictional exposure as of the report date.

Assess rate sensitivity, partner bargaining power, reserve liquidity, redemption stress, competition, customer concentration, cybersecurity, and dilution. Give ARC and other newer products their own economic and accounting assumptions rather than assigning them value from an untested narrative.

Build a three-year operating forecast and a DCF with a justified terminal period, then cross-check valuation using suitable listed financial infrastructure and payments businesses. Explain comparability limits. Show bull, base, and bear scenarios across USDC balances, yields, distribution costs, and operating margins. Reserve assets backing customer tokens must not be added to equity value as freely available corporate cash; reconcile both assets and associated liabilities.

An illustrative sensitivity table should show how changes in average supply and reserve yield affect gross reserve income, retained revenue, and ultimately valuation. Present a target price or investment stance only after completing the evidence and valuation work.

## Deliverables and sequence

| Stage | Work | Reviewable output |
| --- | --- | --- |
| 1 | Completed: test free financial/on-chain access and establish feasibility | Feasibility report, source snapshots and Ethereum checkpoints |
| 2 | Completed: extract quarterly accounting targets and compare supply definitions | Seven-quarter actuals, release dates, Workspace checks and supply comparisons |
| 3 | Completed: evaluate reserve-income models and an initial RLDC bridge | Six-quarter publication-filtered simulations, baseline errors and yield-adjustment comparisons |
| 4 | Completed: forecast other revenue, assess on-chain observability and retain a conditional distribution-cost bridge | Product-revenue ledger, dated forecasts, uncertainty ranges and RLDC scenarios |
| 5 | Complete company analysis, forward financial scenarios, expectations comparison and valuation | Financial model and sourced draft equity research report |
| 6 | Prepare the application sample | A two-page research brief, an approximately 10–15-page main report, and a technical appendix with reproducible code and charts |

The technical appendix should explain one complete chain-data-to-financial-statement calculation that you can reproduce and defend in an interview. A concise methodology and honest treatment of failures will be more useful than a large dashboard without an auditable earnings bridge.

The first decision after approval is whether the free data supports a credible historical nowcast. If it supports reserve income but not detailed distribution costs, keep the validated reserve model as the empirical centerpiece and present retained earnings as scenarios. Report that boundary openly.

## Files prepared for proposal review

- `sources/filings/Circle_FY2025_Annual_Report.pdf`: downloaded annual report.
- `sources/filings/download_manifest.json`: source URLs, download outcomes, and checksum for the downloaded report.
- `sources/feasibility_checks.json`: limited endpoint-access checks; failed checks are not evidence that a provider has no usable data.

All subsequent code, data, models, and report drafts should remain in this Circle folder. The proposal has been approved in chat and the first feasibility test is complete. Continue with the scope recorded in the feasibility report.

Stage two was completed on 21 November 2026. The [quarterly actuals and supply findings](stage2/Stage_2_Findings.md) document seven quarters, six original release dates, the Workspace revenue checks, and the remaining limits on supply reconciliation. Stage three records the subsequent forecast evaluation.

Stage three's forecast evaluation is now complete. Stage four's [plan and revenue mix](stage4/Stage_4_Plan_and_Revenue_Mix.md) records the next scope and the requested reserve-income share for every verified earnings release, plus the pre-IPO Q1 reference. The stage numbers above reflect the work sequence agreed during the research rather than the initial proposal's broader grouping.

The subsequent [on-chain extensions and services regression](stage5/Stage_5_Findings.md), completed on 21 November 2026, add a full-quarter Ethereum USDC flow reconciliation, CCTP route/fee/address analysis, reconstructed USYC fee history, a dated Q4 USYC fee scenario, early-quarter supply projections and the requested three-factor regression. This folder uses the Stage 5 label for that research extension; the broader company analysis and valuation in the original sequence remain later work. The regression and total-services nowcast do not yet support reliable forecasts. Earlier dated ARC/other-revenue forecasts and the Stage 3 reserve models are preserved.

The latest [Stage 5 operating-model plan](stage5/Stage_5_Operating_Model_Plan.md) records the user's flat non-ARC operating-other-revenue assumption (approximately $25.464m per quarter), conditional $60.4m Q4 ARC recognition, and zero unannounced new ARC sales. It also compares 30 complete days of Arc spot DEX volume with peers, while explicitly rejecting low spot volume as proof that institutional token sales cannot occur. The next main modeling step is distribution economics and RLDC, followed by expenses/EPS, expectations and valuation.

Stage 5A's [RLDC investigation](stage5/rldc/Findings.md) is complete. Eight rules were compared on six historical quarters. A pooled prior-three-quarter cost/reserve-income ratio gives 0.94% cost MAPE and 2.98% end-to-end non-ARC RLDC MAPE. A new dated Q4 scenario and independently recalculating workbook preserve the user's revenue assumptions and prior forecasts. Expenses and EPS are the next modeling work; valuation remains later.
