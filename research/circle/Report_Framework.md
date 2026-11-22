# Circle: from public data to an EPS estimate

Revised 22 November 2026 for the undergraduate on-chain research application. This is the current report structure. Existing stage folders remain the research record; their numerical results and dated forecasts are preserved. The report has two main parts. Valuation is an optional later extension, not a prerequisite for demonstrating the forecasting method.

Central question: **Which publicly accessible data can help an outside analyst estimate Circle's quarterly earnings before release, and how much does on-chain data improve that estimate?**

## Part I. Discover, extract and validate Circle-related data

Create a comprehensive inventory of financially relevant datasets available online. Include direct blockchain observations, third-party on-chain aggregates, primary financial disclosures, interest rates, product terms, corporate events and optional licensed expectations data. “Available online” does not mean “observable on-chain,” and a dashboard's existence does not establish free historical access. This is a bounded financial-data investigation, not an indefinite search for every online mention of Circle.

Each dataset must have:

- The economic question and accounting line it could inform.
- Source URL/contract identity, extraction method, raw response or document, and file hash.
- Definition, units, frequency, chain/product scope and historical coverage.
- Observation date, first established public-by date, retrieval date and revision/vintage status.
- Coverage and reconciliation checks, missing observations and unresolved attribution.
- Access status: collected and checked, partial, candidate not tested, or unavailable/private.
- Role: direct model input, forecast assumption support, business context, or rejected predictor.

Do not drop an unhelpful dataset from the research record merely because it fails to improve the model. Equally, do not force every collected series into the EPS equation. A usage indicator can support the business discussion without being a validated earnings driver.

### Working data inventory

The detailed 22 November source audit is now in [On-chain Data Checklist](data_inventory/Onchain_Data_Checklist.md): 69 numbered metrics/questions, live free-API access checks, explicit seven-quarter coverage limits and public-dashboard references. The [website dashboard plan](data_inventory/Website_Dashboard_Plan.md) uses the inspected ziyik0612.me GitHub Pages repository; no website deployment has been made.

Statuses below describe work completed by the framework revision. Candidate rows are research tasks, not claims that complete public histories exist.

| Dataset family | Financial connection | Existing evidence | Remaining work |
| --- | --- | --- | --- |
| Daily global USDC and chain composition | Reserve-balance proxy and demand mix | Collected provider history; reconciled reported supply; bridge-adjustment limits recorded | Maintain dated vintages and deployment/definition changes |
| Native USDC mint/burn and historical supply | Independent issuance audit and migration decomposition | Q3 Ethereum raw-unit stock-flow identity reconciled exactly | Extend direct validation selectively to additional material chains |
| Allowed-but-not-issued, denied and pending-burn balances | Explain raw supply versus financial circulation | Definitions investigated; aggregate reconciliation within accepted tolerance | Authenticate address/time histories where publicly recoverable |
| EURC supply and euro reserve benchmarks | Separate the smaller reserve-income perimeter | Identified as a gap inside the lagged calibration | Test separate history, rates and materiality before adding complexity |
| Circle Reserve Fund yields, assets, holdings and distributions | Reserve return and portfolio mix | Original monthly yield filings collected and publication-filtered | More explicit fund/cash/direct-Treasury decomposition and distribution reconciliation |
| SOFR and Treasury benchmarks | Yield transmission and future rate assumptions | Collected and backtested with day-count and publication controls | Maintain vintages and compare future-rate scenarios |
| Official reserve and mint/redemption reports | Validate supply and reserve composition | Used in supply/source checks | Build a dated structured allocation series where available |
| Coinbase disclosures and distribution agreements | Largest partner-cost economics and earlier information window | Original exhibits and agreements collected; proxy methods tested | Monitor definition/term changes and explain unclassified residuals |
| Circle/Binance/other eligible partner balances and incentives | Distribution costs and retained income | Public terms reviewed; partial platform KPIs | Complete eligible populations and exact rates may remain private; do not substitute exchange labels |
| CCTP messages, routes and actual collected fees | Observable transaction-fee component | Aggregate fee history plus direct Ethereum Q3 extraction | Broader direct-chain reconciliation and resolution of the fee-series difference |
| USYC price, share supply and performance-fee reports | Fund-management component of services revenue | 438 historical reports reconstructed; dated fee projection stored | Reconcile observation-time fees to company recognition and examine redemption fees |
| Stablecoin/USYC redemption volumes and realized fees | Transaction revenue | Pricing and limitations reviewed; gross burns not equated to paid redemptions | Establish chargeable activity, exemptions and fee recipients if possible |
| Circle-owned reward/validator wallets and asset prices | Blockchain rewards and valuation of noncash income | Identified; complete entitlement reconstruction not established | Authenticate ownership, rewards, prices and recognition policy |
| ARC sales, deferred consideration and performance milestones | Event-dependent revenue recognition | Announcement/filing timeline and remaining-balance scenario stored | Recognition timetable and investor addresses not established; revise only with new evidence |
| Arc activity, fees and validator economics | Adoption context and potential future income | DEX/bridge activity examined; chain USDC composition collected | Attribute fees actually earned by Circle, rather than all network/app fees |
| Market stablecoin totals, USDC share and BTC prices | Potential demand indicators | Daily factors collected and services regression tested | Retain the weak result; do not promote it to a validated earnings relationship |
| Financial statements, guidance and accounting policies | Actual revenue, costs, operating expenses and EPS targets | Seven-quarter revenue/cost ledger and primary filings collected | Complete expense, non-operating, tax and common-share earnings schedules |
| Share awards, diluted shares and corporate actions | EPS denominator and compensation | Present in filings; not yet a completed forecast schedule | Build period-specific share/SBC logic, including loss-period antidilution |
| Analyst expectations and market prices | External benchmark and economic significance | Access options identified; no validated historical consensus-beat result | Confirm licensed coverage, estimate timestamps and accounting comparability |

Part I's deliverable is a sourced data catalogue, reproducible extraction examples and a data-to-accounting map. Highlight USDC issuance, CCTP fee decoding and USYC fee-share conversion as direct extraction examples. Keep broader adoption charts and weak predictors in supporting analysis.

## Part II. Use the extracted data to estimate and evaluate EPS

Choose the primary output explicitly: quarterly GAAP diluted EPS attributable to common shareholders, subject to the issuer's actual presentation and share rules. Show basic-share treatment where loss-period antidilution requires it. Use adjusted EPS only as a separately defined and reconciled secondary measure. Do not divide RLDC or total operating income by shares and call that GAAP EPS.

### A. Assemble the accounting bridge

```text
Daily reserve balances × estimated earned yields
  + subscription/services revenue
  + transaction revenue
  + event-dependent revenue, including conditional ARC recognition
  = total revenue and reserve income

Total revenue and reserve income
  − distribution, transaction and other costs
  = RLDC

RLDC
  − compensation, administration, technology, marketing, D&A
  − or + other operating items
  = operating income

Operating income
  + or − non-operating items
  − income taxes
  − noncontrolling interests / other common-share numerator adjustments where applicable
  = net income attributable to common shareholders

Common-share net income ÷ applicable weighted-average diluted shares
  = diluted EPS
```

Every line must be tagged as directly observed, estimated from a validated relationship, or assumed. Model an income item once and in its correct category. For example, observed USYC performance fees cannot be added on top of a flat total-services forecast that already includes that component.

### B. Preserve the current working assumptions

Keep the established reserve models and provisional pooled-three-quarter distribution-cost ratio as starting methods, with the alternatives retained for comparison. Hold non-ARC operating other revenue flat at approximately $25.464m per quarter in the user-selected working case. The approximately $60.4m remaining existing ARC presale balance is assumed recognized in Q4 2026, followed by zero recognition from that exhausted balance and zero new unannounced sales. Recognition timing is not verified. Show the delayed-recognition case separately, preserve the issuer-guidance benchmark, and do not treat deferred-revenue release as new cash or automatically net profit.

Do not refresh or replace the 21 November dated forecasts merely because the framework changed. Later observations must create separately dated revisions. The current Q4 record remains a forward scenario with some days projected, not a completed-quarter observation.

### C. Test the incremental contribution of on-chain data

The paper must answer more than whether one fitted model looks accurate. On comparable targets and cutoffs, compare:

1. **Financial-data baseline:** a simple forecast from previously published financials and explicit expense/share assumptions, without current-period blockchain observations.
2. **Reserve model with on-chain supply:** replace the baseline reserve balance with current-period chain-derived supply and observable rate information. Keep the remaining assumptions comparable.
3. **Additional measured components:** add authenticated fee or fund observations where they improve coverage, showing whether they reduce forecast error rather than assuming that more data helps.

The comparison should isolate changes: use a financial-only reserve-balance proxy with the same rate benchmark when measuring the incremental value of on-chain supply. Separately show the benefit of updated rates. Do not attribute the combined improvement entirely to blockchain data.

Report intermediate reserve-income and cost errors as well as EPS errors. This distinguishes data-extraction success from errors in operating expenses, taxes or dilution. Use an error-contribution bridge so an EPS miss can be traced to the relevant line.

### D. Use clear information cutoffs and honest evaluation

Separate historical reconstruction, completed-quarter pre-earnings nowcasts, and earlier-quarter forecasts that project the remaining days. Inputs need to have been public at each chosen cutoff. Coinbase's current-quarter results can enter only after Coinbase reports. A future fund filing, revised wallet label or later comparative cannot enter an earlier prediction.

Retain the small-sample and current-vintage limitations of the existing tests. Do not rename the last two historical quarters an unseen holdout after their outcomes have already been examined. Freeze prospective forecasts and score them after release. A genuinely unused older/new period can be a holdout only if it was not used in development.

Evaluate EPS with absolute error in dollars per share, signed error and bias, and quarter-by-quarter results. Percentage errors can become unstable near zero or across profit/loss transitions, so do not rely on EPS MAPE alone. Explain IPO-related share changes, major SBC events and category reclassifications when comparing quarters. Compare with analyst consensus only if a dated, matching GAAP/adjusted series is verified.

### E. Present uncertainty and economic meaning

Show assumptions for unobserved data, changes in supply/yields/partner costs, unusual expenses and ARC timing. Distinguish scenario ranges from statistical confidence intervals. Explain why a small revenue or RLDC error can produce a much larger EPS error when the profit margin is small. A public-data model can be useful without observing every company expense on-chain.

## Writing structure and next work

The two substantive parts will be preceded by a short research question and findings summary, then followed by limitations and a technical appendix. Existing scripts, source registers and dated model files are the evidence base. A detailed equity valuation can be added later if it serves the final application sample; the immediate success criterion is an auditable EPS estimate and a defensible measurement of on-chain data's contribution.

Next, consolidate the Part I catalogue and mark coverage/access gaps. Then complete the missing operating-expense, non-operating, tax and share schedules for Part II. Work can proceed on those schedules while low-materiality or inaccessible data gaps remain openly documented. No new collection or EPS result is claimed by this framework revision.
