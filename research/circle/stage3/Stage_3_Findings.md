# Circle reserve income historical test

Completed 21 November 2026. **The six-quarter results support the idea that USDC supply and interest rates can estimate Circle's reserve income closely. Estimating total revenue and retained revenue requires separate work on other revenue and distribution costs.**

The working reserve model's average absolute error is **0.34%**, versus **6.29%** from carrying forward the previous quarter's reserve income with a quarter-length adjustment. A model using the Circle Reserve Fund's yield has a **0.24%** average absolute error. These are retrospective simulations using today's historical supply and benchmark data, with financial and fund inputs filtered by their publication dates. They are not six forecasts recorded before the actual announcements.

## What the models do in plain language

First, use the previous quarter to estimate how much income Circle actually earned per dollar of average USDC. Next, update that earned yield for changes in an observable interest-rate benchmark. Finally, multiply the updated yield by each day's USDC supply and add the daily income estimates for the quarter.

The working model uses SOFR, an overnight Treasury repo benchmark. It retains the previous quarter's gap between Circle's implied earned yield and SOFR. This captures a persistent difference between the benchmark and Circle's overall reserve-income economics without assuming every reserve dollar earns the benchmark rate.

The fund challenger follows the same logic using the Circle Reserve Fund's net seven-day yield. The fund yields incorporate fund expenses, so the model does not deduct those expenses again. This is a fund-aware proxy, not an exact calculation of fund dividends, bank interest, or a complete reserve portfolio.

Both models use USDC supply as the balance proxy while the target is Circle's total reported reserve income. EURC and other differences in the reserve-income perimeter remain embedded in the lagged calibration. The model does not independently identify each source of interest income.

## Supply meets the accepted tolerance

The user accepted an absolute supply difference of **0.5% preferred**, with **1.0% as the outer limit**. These thresholds apply to supply data, not to earnings prediction errors.

All seven quarter-end comparisons from Stage 2 pass the preferred tolerance. Their differences range from -0.161% to +0.365%. The quarter-average comparisons, using the provider's dates as labeled, also pass: -0.499% to +0.351%. Q3 2025 is close to the preferred boundary. Q4's reported average supply is rounded to $0.1 billion, which limits the precision of that comparison.

The provider is therefore accepted as the working supply source. No fixed correction is applied. Timing and definition differences are retained in the research record without delaying the earnings model. Original comparison sources are in the [Stage 2 findings](../stage2/Stage_2_Findings.md) and [Circle's reserve report archive](https://www.circle.com/transparency).

## Reserve income results

Amounts are USD millions. Error is estimate divided by reported income, less one. The estimates below use the cutoff immediately before earnings.

| Quarter | Reported income | SOFR model | SOFR error | Fund model | Fund error |
| --- | ---: | ---: | ---: | ---: | ---: |
| Q2 2025 | 634.27 | 633.10 | -0.19% | 631.59 | -0.42% |
| Q3 2025 | 711.24 | 709.90 | -0.19% | 710.06 | -0.17% |
| Q4 2025 | 733.40 | 730.78 | -0.36% | 731.91 | -0.20% |
| Q1 2026 | 652.51 | 646.66 | -0.90% | 648.68 | -0.59% |
| Q2 2026 | 667.73 | 665.31 | -0.36% | 667.55 | -0.03% |
| Q3 2026 | 657.62 | 657.83 | +0.03% | 657.74 | +0.02% |

Financial targets come from the original filing observations preserved in Stage 2, including Q4's annual-minus-nine-month derivation. [FY2025 filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000062/crcl-20251231.htm), [Q3 2026 filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm).

| Method | Average absolute error | Worst quarter's absolute error | Average dollar error |
| --- | ---: | ---: | ---: |
| Carry prior income, adjust quarter length | 6.29% | 11.06% | $42.11m |
| Supply times prior implied earned yield | 3.28% | 8.64% | $22.61m |
| Supply times SOFR, without calibration | 5.14% | 5.57% | $34.78m |
| Supply times three-month Treasury yield | 4.97% | 11.07% | $32.82m |
| SOFR with previous quarter's yield gap | **0.34%** | **0.90%** | **$2.27m** |
| Fund yield with previous quarter's yield gap | **0.24%** | **0.59%** | **$1.58m** |

All methods cover the same six quarters. Both calibrated models beat the carry-forward baseline in all six. The important result is that adjusting for rate changes and Circle's lagged earned-yield gap adds more value than multiplying supply by a market rate alone. The fund challenger's small advantage over SOFR is insufficient to establish a durable ranking from six observations.

The SOFR model was designated as the working RLDC input before this six-quarter calculation. The protocol was fixed after the financial outcomes and the feasibility pilot had already been viewed, so it is not a blind holdout. No current-quarter outcome was used to fit a spread or choose a model weight.

## Subsequent comparison of yield adjustment rules

Following the user's question on 21 November 2026, a proportional adjustment was tested against the original fixed percentage-point spread. This is a subsequent exploratory comparison on the same six quarters and current historical datasets, not a new holdout. Each method uses the same publication cutoffs, daily balances, rates and lagged financial inputs.

The original rule adds the previous quarter's yield gap to the current benchmark. The proportional rule multiplies the current benchmark by the previous quarter's Circle implied yield divided by the previous benchmark yield. Equivalently, it applies the benchmark's relative percentage change to Circle's previous implied yield. Both are assumptions about how a previously observed relationship persists; neither is a verified contract formula.

| Benchmark | Original additive mean absolute error | Proportional mean absolute error | Quarters improved by proportional rule |
| --- | ---: | ---: | ---: |
| Circle Reserve Fund | 0.237% | 0.156% | 5 of 6 |
| SOFR | 0.337% | 0.193% | 4 of 6 |

For the fund model, average absolute dollar error falls from $1.579m to $1.025m. Q2 2026 income becomes $667.681737m versus $667.554064m under the original rule and $667.733m reported. Q3 becomes $657.557286m versus $657.738983m originally and $657.624m reported. The proportional fund model also improves the early-cutoff mean absolute error, from 0.242% to 0.161%.

These small-sample results make the proportional rule a candidate for future validation. They do not establish that a fixed ratio will survive changes in reserve allocation, bank yields or rate regimes. The original workbook and results above retain their original additive definitions. [Comparison results](results/yield_adjustment_comparison.json) preserve both methods, all quarterly errors and 48 arithmetic checks.

## What was available before earnings

There are two estimates per quarter: seven calendar days after quarter-end, and the calendar day before the verified earnings release. Each lagged financial input has a recorded public-by date. This avoids using the originally unavailable Q1 2025 rounded yield: the model calculates an implied yield from the Q1 income and average-supply figures already public in the IPO prospectus.

The fund archive contains **22 original monthly reports**, December 2024 through September 2026, with **459 business-date observations of net seven-day yields**. Two November 2026 amendments were excluded. Their filing dates were after the last earnings cutoff in the sample. Filing dates were checked against SEC submissions metadata.

The clearest timing example is June 2026. Its fund report was filed on **8 July**, after the early **7 July** cutoff. The early model carries May's last eligible yield forward for the uncovered June dates. It estimates $667.35m. The late estimate can use June's filing and estimates $667.55m. Actual reserve income was $667.73m. The other five early fund estimates equal their late counterparts because the relevant quarter's original fund filings were already available by their early cutoffs. [June fund filing timestamp](https://www.sec.gov/Archives/edgar/data/844779/000119312526298262/0001193125-26-298262-index.htm).

Only fund observations on or before each economic date are used. Weekend gaps carry the latest earlier observation forward. A yield observed later in the month is never filled backward into earlier days. The SEC yield is an annualized rolling seven-calendar-day measure reported for each business date; multiplying it by a daily balance remains an approximation to realized interest. SOFR uses a 360-day convention, and the model converts it before comparing it with the 365-day implied earned yield. The Treasury calculation is explicitly an ACT/365 benchmark approximation. [SEC Form N-MFP, Items A.19 and B.8](https://www.sec.gov/about/forms/formn-mfp.pdf), [New York Fed rate conventions](https://www.newyorkfed.org/markets/reference-rates/additional-information-about-reference-rates).

The supplied history was downloaded on 21 November 2026. Publication filtering of financial statements and fund filings does not recover what DefiLlama's history looked like at each earlier cutoff. Historical supply revisions remain an important limitation. The simulation also uses the currently retrieved rate history rather than independently archived daily vintages. We should describe this result as promising retrospective evidence, not a demonstrated live trading edge or an independently observed analyst-consensus beat.

## Rate uncertainty matters more than small supply differences

For Q3 2026, holding the other assumptions fixed:

| Change | Estimated reserve income effect |
| --- | ---: |
| Supply 0.5% higher | +$3.29m |
| Supply 1.0% higher | +$6.58m |
| Annual yield 0.25 percentage points higher | +$46.33m |

These are sensitivities, not error forecasts. They explain why it is reasonable to proceed within the accepted supply tolerance and put more effort into earned yield and reserve composition. The 0.24% and 0.34% historical model errors are smaller than the preferred 0.5% supply tolerance, so those errors should not become a precision promise for future quarters.

Using following-date supply buckets for both current-quarter balances and lagged benchmark calibration changes SOFR-model income by between -$0.35m and +$1.43m across the sample. Average absolute error becomes 0.31%. Both alignments remain in the workbook; neither is proven exact end-of-day supply.

## The RLDC bridge is less predictable

RLDC means total revenue less distribution, transaction and other costs. It is before operating expenses. The first bridge uses the SOFR reserve estimate, carries forward the previous quarter's other revenue, and applies the previous quarter's total-cost-to-reserve-income ratio. That ratio is an empirical forecasting assumption, not a contractual payout rate.

| Quarter | Estimated RLDC | Reported RLDC | Error |
| --- | ---: | ---: | ---: |
| Q2 2025 | 259.26 | 251.14 | +3.24% |
| Q3 2025 | 278.24 | 292.15 | -4.76% |
| Q4 2025 | 299.39 | 308.78 | -3.04% |
| Q1 2026 | 276.62 | 287.35 | -3.73% |
| Q2 2026 | 292.18 | 288.85 | +1.15% |
| Q3 2026 | 285.06 | 453.25 | -37.11% |

Average absolute RLDC error is **8.84%** across all six quarters. For context, the first five quarters average 3.18%, but they are not a replacement evaluation sample. Q3 2026 remains included in the headline result.

In Q3 2026 the reserve estimate is only $0.21m above actual. However, the other-revenue estimate is $33.58m against $207.26m reported, a $173.68m miss. Reported other revenue includes $181.8m of ARC presale recognition. The smaller cost-estimate difference offsets part of the revenue miss, leaving an RLDC miss of $168.19m. The model therefore demonstrates its limit: reserve visibility does not guarantee visibility into other revenue. [Q3 2026 revenue recognition note](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm).

The workbook allows a five-percentage-point increase or decrease in the assumed cost ratio through one case selector. For Q3 2026 that moves RLDC by $32.89m in either direction. This range is illustrative and does not cover the actual other-revenue surprise. It is not a probability interval. An exact decomposition of partner costs or platform mix is still future work; labeled exchange wallets do not by themselves establish contractual custodial balances.

## Further development requested by the user

Stage 4 follow-up, 21 November 2026: the [other-revenue investigation](../stage4/Stage_4_Findings.md) found that Circle had already guided approximately $180m of annual ARC revenue on August 5 and announced mint completion on September 16. The original Stage 3 lagged-other-revenue miss should therefore not be read as proof that ARC was unknowable before earnings. Allocating that annual guidance to Q3 remains a conditional timing case. The original Stage 3 results and workbook are preserved.

Investigate whether Circle's other income sources can also be verified on-chain. For each product, establish its accounting revenue line and recognition conditions, identify the relevant contracts and fee recipient addresses, and test whether the observable activity can predict recognized revenue before its disclosure.

ARC-related token events, payments/transaction activity and tokenized-fund activity are candidate research areas, subject to verifying their actual economics. Do not equate token transfers or customer volumes with Circle revenue. A presale payment, token issuance and accounting recognition can occur at different times. Separate observed activity, inferred revenue and unobservable contractual assumptions in the eventual report.

## What the next stage should resolve

The research can now move to the distribution and product economics behind retained revenue. Priorities are partner/platform cost drivers, a dated event model for non-reserve revenue, and a more explicit separation of fund income and cash interest. Archive new data vintages to support a future genuinely prospective test. Validate historical analyst-consensus snapshots before making any claim about beating consensus, and keep equity valuation behind these operating assumptions.

The calculation passed 269 source, eligibility and arithmetic checks. An independent verification passed 55 checks, including a test that changing current-quarter financial targets does not change the predictions. The workbook separately recalculates from the daily inputs and is checked against the analytical results. These checks establish calculation consistency, not future forecast accuracy.

The workbook passed 47 calculation and input-change checks and all 184 independent export checks. Exported cells contain no Excel errors, and all four worksheets were visually reviewed. Native Excel recalculation was not separately tested. The authoring process's nonzero shutdown status after successful export is recorded in the [technical notes](README.md).
