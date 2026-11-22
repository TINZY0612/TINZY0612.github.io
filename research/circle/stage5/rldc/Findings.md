# Circle: distribution costs and RLDC projection

Completed 21 November 2026. Currency amounts are USD millions unless stated. RLDC means total revenue and reserve income less total distribution, transaction and other costs, before operating expenses and tax.

**A simple pooled historical cost ratio is the most useful working approach in this sample.** Its six-quarter cost MAPE is 0.94%, versus 1.17% for the latest-quarter ratio. An exponentially weighted ratio is close at 0.97%. Platform-share and partner-revenue models do not improve aggregate costs. These are modest historical improvements from only six targets, not a promise of sub-1% future accuracy.

With flat non-ARC other revenue, the selected rule's end-to-end non-ARC RLDC MAPE is 2.98%. Reported RLDC MAPE remains 8.71% without an ARC event assumption. A separate conditional Q3 ARC timing case gives 2.67%; it is not a validated unconditional earnings forecast.

## Sources and timing

Financial targets, original source observations and dates come from the existing Stage 2 ledger and primary Circle filings. The reserve estimates are the unchanged Stage 3 publication-filtered SOFR model. All six target quarters, Q2 2025–Q3 2026, remain in the comparison. We do not remove the difficult ARC quarter.

The partner approach uses original Coinbase SEC shareholder letters and earnings exhibits. Coinbase reports earlier than Circle, creating an additional information window. The early comparison is dated the day before Coinbase's release; partner-dependent rules are evaluated only at the day before Circle's release. Every financial calibration quarter was already public by the earlier cutoff. Historical supply/rate data were retrieved later and may have been revised, so the exercise is a reconstruction rather than a strict archived-vintage test.

| Quarter | Coinbase public by | Circle cutoff | Combined Coinbase USDC income ($m) | Original source |
| --- | --- | --- | --- | --- |
| 2025Q1 | 2025-05-08 | Pre-IPO reference | 297.5 | [SEC exhibit](https://www.sec.gov/Archives/edgar/data/1679788/000167978825000088/q125shareholderletter.htm) |
| 2025Q2 | 2025-07-31 | 2025-08-11 | 332.5 | [SEC exhibit](https://www.sec.gov/Archives/edgar/data/1679788/000167978825000153/q225shareholderletter.htm) |
| 2025Q3 | 2025-10-30 | 2025-11-11 | 354.7 | [SEC exhibit](https://www.sec.gov/Archives/edgar/data/1679788/000167978825000207/q325shareholderletter.htm) |
| 2025Q4 | 2026-02-12 | 2026-02-24 | 364.1 | [SEC exhibit](https://www.sec.gov/Archives/edgar/data/1679788/000167978826000011/q425shareholderletter.htm) |
| 2026Q1 | 2026-05-07 | 2026-05-10 | 324.0 | [SEC exhibit](https://www.sec.gov/Archives/edgar/data/1679788/000167978826000053/q126earningsdeck-finalse.htm) |
| 2026Q2 | 2026-07-30 | 2026-08-04 | 320.0 | [SEC exhibit](https://www.sec.gov/Archives/edgar/data/1679788/000167978826000087/q226earningsdeck_sec.htm) |
| 2026Q3 | 2026-10-29 | 2026-11-03 | 328.0 | [SEC exhibit](https://www.sec.gov/Archives/edgar/data/1679788/000167978826000121/q326earningsdeck_vsec.htm) |

For 2025, extract the current-quarter Stablecoin revenue row from each original letter, not a later comparative. For 2026, use the presentation's explicitly combined stablecoin income and corporate-balance USDC income total. Corporate income is already inside the combined total and must not be added again. Original SEC exhibits avoid relying on the later versioned Q1 PDF. The original Q1/Q2/Q3 2026 USDC slides are pages 38/40/36; source images are saved, with Q2/Q3 visually checked. Product balances are rounded, except where the original narrative provides greater precision.

## What the contracts support

The [Circle–Coinbase collaboration agreement](https://www.sec.gov/Archives/edgar/data/1876042/000119312525070481/d737521dex101.htm), particularly sections 4.1–4.5, describes the payment base, issuer retention, product allocations and ecosystem sharing. The [ecosystem agreement](https://www.sec.gov/Archives/edgar/data/1876042/000119312525070481/d737521dex102.htm) adds approved participants. Some economic and address-attribution definitions are redacted. A simple claim that Coinbase always receives exactly half of gross reserve income is insufficient.

Let B be the payment base after issuer retention and deductions, c Coinbase's eligible product share, s Circle's eligible product share, A approved participant payments and T other direct costs. A simplified decomposition is:

```text
Coinbase payment ≈ B × c + 0.5 × [B × (1 − c − s) − A]
Total costs      ≈ 0.5 × B × (1 + c − s) + 0.5 × A + T
```

This is an explanatory approximation, not a full daily implementation of all contractual definitions. A change in Coinbase share does not identify simultaneous changes in Circle share, issuer retention or third-party terms. Eligible product balances include custody and managed/noncustodial services; labeled exchange addresses do not establish the complete contractual population. Therefore we tested a simplified share-change sensitivity rather than claim a precise wallet-level payout reconstruction.

Circle's original annual Coinbase cost amount is rounded to $1.4bn. Later filings also change earlier comparatives: original Q1 2025 is $298.8m versus $303.2m in the later comparative; original H1 $630.6m versus later $635.5m; original nine months $989.1m versus later $996.8m. The separate dated ledger retains these observations and approximate derivations. We do not turn them into a falsely exact same-vintage Q4 payment. Consequently, partner models forecast an **unclassified cost residual**, not an asserted exact non-Coinbase cost amount.

## Eight methods tested

Write Rhat for the estimated current reserve income, R and C for prior-quarter actual reserve income and costs, and P for Coinbase's combined USDC income. All historical quantities in these rules must already be public at the cutoff.

1. **Flat dollars:** Chat = C.
2. **Latest ratio:** Chat = Rhat × C/R.
3. **Pooled ratio:** Chat = Rhat × sum(prior costs)/sum(prior reserve income), using the latest available three quarters, or fewer at the beginning of the sample. This is a reserve-income-weighted ratio, not the arithmetic mean of percentages.
4. **Exponential ratio:** average all available prior C/R ratios with fixed 0.5 decay per quarter, then multiply by Rhat. Decay was specified before calculation, not tuned to these errors.
5. **Platform-share change:** Chat = Rhat × [C/R + 0.5 × (current Coinbase share − prior Coinbase share)]. This assumes unchanged unobserved Circle mix and residual contract economics. Current Coinbase share is available only after its results.
6. **Partner plus scaled residual:** Chat = current P + (C − prior P) × Rhat/R.
7. **Partner scales total costs:** Chat = C × current P/prior P.
8. **Partner plus flat residual:** Chat = current P + (C − prior P).

Rules 1–4 do not need current Coinbase results. Rules 5–8 are late partner-dependent nowcasts. The non-ARC other-revenue forecast is the latest prior-quarter figure held flat. None of these historical lag quarters contains recognized ARC revenue, so no repeated ARC balance enters those forecasts. Current recognized ARC amounts are used only in separate scoring normalization, never as a prediction input.

| Method | Cost MAPE | Cost MAE ($m) | Worst cost error | Non-ARC RLDC MAPE |
| --- | --- | --- | --- | --- |
| Previous-quarter total costs held flat | 6.95% | 29.166 | 14.57% | 10.68% |
| Latest cost / reserve-income ratio | 1.17% | 4.919 | 3.06% | 3.49% |
| Up-to-three-quarter pooled cost / reserve ratio | 0.94% | 3.870 | 3.06% | 2.98% |
| Cost / reserve ratios, fixed 0.5 exponential decay | 0.97% | 4.021 | 3.06% | 3.08% |
| Latest ratio plus half the change in Coinbase product share | 1.65% | 6.886 | 3.18% | 3.08% |
| Current Coinbase gross USDC income plus reserve-scaled lag residual | 1.90% | 7.934 | 4.31% | 3.20% |
| Prior total costs scaled by current/prior Coinbase gross USDC income | 2.37% | 9.929 | 4.52% | 3.80% |
| Current Coinbase gross USDC income plus flat lag dollar residual | 3.19% | 13.383 | 5.97% | 4.76% |

MAPE is the mean of absolute estimate/actual − 1. The selected rule's average dollar cost error is $3.870m. Its worst quarter is a 3.06% cost underestimate in Q2 2025. The others are not hidden by the average.

## Selected rule: exact historical example

Before Q3 2026 Circle results, Q4 2025 through Q2 2026 were public:

```text
Cost numerator   = 461.450 + 406.781 + 412.470 = 1,280.701
Reserve denominator = 733.396 + 652.508 + 667.733 = 2,053.637
Pooled cost ratio = 1,280.701 / 2,053.637 = 62.362579%
On-chain supply / SOFR reserve estimate = 657.831480
Cost estimate = 657.831480 × 0.62362579 = 410.240677
Reported costs = 411.634
Cost error = -0.3385%
```

This retains on-chain supply as the main observed earnings driver. The payout ratio is an empirical calibration that summarizes distribution economics, not an independently observed contract rate.

| Quarter | Cost estimate ($m) | Actual costs ($m) | Cost error | Non-ARC RLDC estimate ($m) | Non-ARC actual ($m) | Non-ARC RLDC error |
| --- | --- | --- | --- | --- | --- | --- |
| 2025Q2 | 394.496 | 406.942 | -3.06% | 259.261 | 251.136 | +3.24% |
| 2025Q3 | 449.331 | 447.612 | +0.38% | 284.377 | 292.147 | -2.66% |
| 2025Q4 | 461.559 | 461.450 | +0.02% | 297.738 | 308.782 | -3.58% |
| 2026Q1 | 409.354 | 406.781 | +0.63% | 274.144 | 287.352 | -4.60% |
| 2026Q2 | 417.449 | 412.470 | +1.21% | 289.492 | 288.845 | +0.22% |
| 2026Q3 | 410.241 | 411.634 | -0.34% | 281.173 | 271.454 | +3.58% |

For Q3 2026 specifically, costs are close but the flat other-revenue assumption is still too high after removing ARC: $33.582m forecast versus about $25.464m actual non-ARC other revenue. The resulting underlying RLDC error is +3.58%. Thus 0.94% cost error does not imply 0.94% RLDC error. Subtracting costs leaves a smaller denominator and other revenue introduces an additional error.

## Why added detail did not improve the forecast

Coinbase's disclosure is economically useful and is genuinely available earlier. However, its combined income is not exactly the same accounting line as Circle's distribution expense. There are issuer deductions, partner arrangements, timing and rounding differences. Other distribution and transaction costs can change independently. The unclassified gap between Circle total costs and Coinbase income rose from about $50.147m in Q1 2025 to $74.442m in Q2. Carrying forward that gap or scaling it mechanically misses the step change.

The exact Binance incentive rate and complete eligible balances are not established by public wallet labels. Circle's prospectus describes balance- and SOFR-linked payments and approved-participant treatment, which explains the economic direction but does not provide all inputs needed for a clean historical reconstruction. We did not invent rates or infer proprietary eligible balances from a small address list.

Smoothing a fairly stable observed aggregate ratio avoids some quarter-specific noise. That is why the pooled rule helps here. It may fail if rates, partner mix, agreements or incentives change materially. The latest-quarter ratio and exponential rule remain useful cross-checks.

## Small-sample robustness and selection limits

| Method | First four quarters cost MAPE | Last two quarters cost MAPE |
| --- | --- | --- |
| Latest cost / reserve-income ratio | 1.29% | 0.92% |
| Up-to-three-quarter pooled cost / reserve ratio | 1.02% | 0.77% |
| Cost / reserve ratios, fixed 0.5 exponential decay | 1.04% | 0.84% |
| Current Coinbase gross USDC income plus reserve-scaled lag residual | 1.90% | 1.88% |

The later two quarters are merely a retrospective chronological split; their outcomes were already known when this project began. The three-quarter window, 0.5 exponential decay and full method list were recorded before this calculation. Still, choosing the best method from eight on six targets creates selection risk. The improvement from 1.17% to 0.94% is only about 0.23 percentage points. Prefer the pooled rule provisionally for its simple economics and similarly good recent performance, not as a statistically proven winner. There is no new R² or significance claim.

## Reported RLDC and ARC timing

For the pooled rule, reported RLDC MAPE is **8.71%**, compared with the old latest-ratio baseline's **8.84%**. Q3 2026 remains a large miss because $181.8m recognized ARC revenue was not in the flat other-revenue forecast.

The pre-release annual ARC guidance was approximately $180m. Allocating that annual amount to Q3 gives a conditional historical scenario; use $180m, not the subsequently reported $181.8m. In that case pooled-rule RLDC MAPE is **2.67%**. This improvement depends on recognizing the right quarter and cannot be attributed solely to the cost model. Without an ARC timing assumption, the **non-ARC** RLDC MAPE is **2.98%**, versus 3.49% for the latest ratio. The cost-only diagnostic, which deliberately uses actual total revenue to isolate costs, has 1.42% RLDC MAPE and is not a forecast.

## Prospective Q4 2026 case as of 21 November

The new dated forecast has an unknown actual. USDC observations run through 20 November, giving **51 observed days and 41 projected days** of Q4. Remaining daily global USDC is held at **$68.811091bn** and SOFR at the latest published **3.90%**. Effective-date SOFR is eligible only after its following-business-day publication, represented by the next effective date in the continuous NY Fed series. The last known effective date is 19 November. A current snapshot is not a historical intraday vintage.

The reserve formula follows the prior Stage 3 convention:

```text
Lag implied yield = Q3 reserve income / Q3 reported average USDC × 365 / 92
Lag spread = lag implied yield − Q3 supply-weighted SOFR on a 365-day basis
Reserve forecast = sum(daily observed/projected USDC × available/projected SOFR / 360)
                 + sum(daily observed/projected USDC) × lag spread / 365
```

Raw SOFR income is $702.426m. The lag-spread adjustment is $-28.114m, giving **$674.312m reserve income**. This forward-quarter scenario has more uncertainty than the completed-quarter reserve backtest.

The Q4 cost ratio uses Q1–Q3 2026 actuals:

```text
Ratio = (406.781 + 412.470 + 411.634) / (652.508 + 667.733 + 657.624)
      = 1,230.885 / 1,977.865 = 62.233014%
```

| Q4 working case | $m |
| --- | --- |
| Reserve income | 674.312 |
| Flat non-ARC other revenue | 25.464 |
| Underlying total revenue | 699.776 |
| Distribution, transaction and other costs | (419.645) |
| Underlying RLDC | **280.131** |
| Conditional ARC recognition | 60.400 |
| RLDC including ARC | **340.531** |

Using the latest ratio instead gives $338.096m; the exponential ratio gives $339.347m. These are alternative model outputs, not confidence limits. Q4 Coinbase results have not been released, so the late partner models cannot yet use observed Q4 partner income.

The $60.4m ARC recognition is the user's assumption and has no verified Q4 timetable. The model assigns no incremental distribution cost to that recognition, so it adds $60.4m to RLDC before operating costs and tax. It does not create another $60.4m cash receipt or automatically equal net profit. Flat non-ARC other revenue is about $25.464m per quarter. No separate USYC uplift is added. Unannounced new ARC sales are zero in this case, with later evidence requiring a separate forecast version.

At this reserve estimate, a one-percentage-point increase in the cost ratio reduces RLDC by **$6.743m**. An extra $10m reserve income increases RLDC by only **$3.777m** at a fixed 62.23% payout ratio. Delaying ARC recognition reduces the reported-case RLDC by **$60.4m**. These illustrate why reserve accuracy alone does not settle the equity earnings outlook.

The resulting other revenue of approximately $85.864m remains above the earlier issuer-guidance-implied Q4 range. The guidance benchmark and previous dated scenarios are preserved, rather than silently reconciled to this user-directed case.

## Reproduction and verification

See `README.md`. `source_manifest.json` records requests, timestamps, source hashes and failed attempts. `results/circle_coinbase_cost_ledger.json` retains dated payment disclosures and changed comparatives. `results/method_comparison.json` preserves all eight rules, six quarters, signed errors and both chronological subsets. The Q4 JSON is immutable to changed inputs; its actual remains null.

The workbook independently recalculates all eight cost methods, error summaries, daily Q4 reserve build and selected RLDC. Changing the cost-method selector, future supply and ARC assumption was tested, and source actuals remained unchanged. Source hashes, historical publication gates, target-actual mutation controls and exported formula caches are independently checked in `results/verification.json`. Native Excel application recalculation was not tested.
