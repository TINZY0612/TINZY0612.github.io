# Circle Stage 4 plan and revenue mix

Status update, 21 November 2026: the requested other-revenue and ARC investigation is completed in [Stage 4 findings](Stage_4_Findings.md). This file preserves the earlier plan and revenue-share calculation. The full partner/platform distribution model remains later work.

Prepared 21 November 2026. Stage 4 will forecast non-reserve revenue and improve the distribution-cost bridge so the reserve-income model can feed total revenue and revenue less distribution costs (RLDC). This file records the scope and completes the requested revenue-share calculation. Product forecasts and on-chain verification are not yet completed.

## Reserve income share of total revenue

Amounts are USD millions. Total revenue means the financial statement line “Total revenue and reserve income.” Share equals reserve income divided by that total. Non-operating “Other income (expense), net” is outside this denominator.

| Quarter | Earnings release | Reserve income | Other revenue | Total revenue | Reserve share |
| --- | --- | ---: | ---: | ---: | ---: |
| 2025Q1 | IPO reference | 557.911 | 20.662 | 578.573 | 96.43% |
| 2025Q2 | 12 Aug 2025 | 634.274 | 23.804 | 658.078 | 96.38% |
| 2025Q3 | 12 Nov 2025 | 711.241 | 28.518 | 739.759 | 96.14% |
| 2025Q4 | 25 Feb 2026 | 733.396 | 36.836 | 770.232 | 95.22% |
| 2026Q1 | 11 May 2026 | 652.508 | 41.625 | 694.133 | 94.00% |
| 2026Q2 | 05 Aug 2026 | 667.733 | 33.582 | 701.315 | 95.21% |
| 2026Q3 | 04 Nov 2026 | 657.624 | 207.264 | 864.888 | 76.04% |

This covers every verified public-company quarterly earnings release in our current sample, plus Q1 2025 as a pre-IPO reference disclosed in the IPO prospectus. Q4 2025 flows are annual less nine months. Figures are preserved at published statement precision rather than rounded earnings-release headlines. FY2025's full-year reserve share was **96.00%**; it is a separate annual aggregation, not an additional quarter.

The source observations and original filing links are in [the saved calculation](revenue_mix.json) and [Stage 2](../stage2/Stage_2_Findings.md). Sources include the [IPO prospectus](https://www.sec.gov/Archives/edgar/data/1876042/000119312525135795/d737521d424b4.htm), [FY2025 filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000062/crcl-20251231.htm), and [Q3 2026 filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm).

Reserve share stayed between 94.00% and 96.43% through Q2 2026, then fell to 76.04%. Q3 2026 includes $181.8m of ARC presale revenue recognition. Removing only that recognition from the revenue denominator gives a reserve share of **96.27%**. This is a revenue-mix diagnostic; it is not adjusted profit and makes no corresponding cost adjustment. The fall in the headline reserve share therefore does not by itself establish a lasting change in recurring revenue mix. [Revenue note, Table 11.1 and ARC discussion](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm).

## Work sequence

### 1 Reconstruct non-reserve revenue by product

Extract standalone quarterly subscription and services, transaction revenue, and other revenue. Within those categories, identify recurring service delivery, integration milestones, USYC fees and ARC recognition wherever the disclosures permit. Preserve cash receipts, deferred revenue and recognized revenue separately. Do not use an undifferentiated growth rate for all other revenue. Clarify differences between revenue and non-operating income before extending the model to EPS.

### 2 Establish what can be observed before earnings

For each revenue stream, find free activity data and the relevant on-chain contracts, fee recipients or official disclosures. Classify the evidence as directly observable, inferable with assumptions, or dependent on private contracts. Verify historical addresses, fee schedules, dates and economic rights before connecting transaction activity to Circle revenue.

| Candidate stream | Information to investigate | Main accounting question |
| --- | --- | --- |
| Subscription, maintenance and licensing | Agreements, customer/product disclosures and renewals | Revenue recognized over service delivery versus transaction activity |
| Integration services | Announcements, completed integrations and disclosed milestones | When the performance obligation is accepted and revenue becomes recognizable |
| USYC-related fees | On-chain balances, fund performance and applicable fee/entitlement terms | Which fee rights actually belong to Circle and when variable consideration is recognized |
| Transaction and CCTP-related services | Fee-bearing activity, effective fee schedules and recipient addresses | Paid activity and Circle's recognized fees, rather than total transfer volume |
| ARC presale recognition | Prior disclosures, purchase agreements, receipts and performance obligations | Whether the recognition event could have been anticipated before earnings |

These are research questions, not findings that every stream is fully observable. In particular, do not assume USYC fees are simply assets multiplied by a fixed management-fee rate, or that all CCTP volume generates the same fee. The latest filing describes performance-fee entitlement and several transaction-revenue sources. [Q3 2026 Note 11](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm).

### 3 Build and evaluate the other-revenue forecast

Create product-level forecasts using dated inputs. Compare them with the Stage 3 carry-forward baseline across the same six releases. Include Q3 2026 in the headline error calculation. Test whether earlier disclosures could have anticipated the ARC recognition; the baseline's miss does not prove the event was inherently unforecastable. Report ranges where the fee economics or recognition dates remain private. Keep proxy usage measures separate from verified revenue.

### 4 Improve distribution costs and retained revenue

Separate Coinbase, other partner incentives and transaction/other costs where disclosure permits. Map contractual payment bases, issuer retention and platform/ecosystem allocations before using wallet balances. Use disclosed platform metrics and scenarios when contractual balances or labels cannot be established. The annual filing describes a daily net-reserve-income payment base with issuer retention, platform allocations and an ecosystem split. [FY2025 distribution arrangements](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000062/crcl-20251231.htm).

Combine reserve income and the new other-revenue forecast, then subtract distribution and related costs to estimate RLDC. Compare the result with the existing lagged-cost-ratio baseline. Keep RLDC distinct from net profit. Operating expenses, taxes, EPS and equity valuation follow once the operating revenue/cost assumptions are established.

## Outputs and completion criteria

A quarterly product-revenue ledger reconciled to total other revenue; a source and on-chain observability map; a dated product-level forecast with baseline errors and explicit ranges; and an improved RLDC bridge. A model may retain scenario-based assumptions for private terms, but must identify them. Check that a new product driver improves an interpretable forecast rather than merely explaining already published results.

The additive-versus-proportional yield comparison remains in [Stage 3](../stage3/Stage_3_Findings.md). Both rules should remain available for further validation; the subsequent comparison is not a new blind holdout. No valuation or analyst-consensus outperformance claim is made at this stage.
