# Circle quarterly actuals and supply findings

Completed 21 November 2026. This stage establishes the historical accounting targets and the limits of the initial supply dataset. It does not evaluate a forecasting model.

Subsequent user decision: accept absolute supply differences within 0.5% as the preferred tolerance and within 1.0% as the outer limit. All seven quarter-end comparisons below pass the preferred tolerance. The original 0.10% investigation flags remain part of this stage's historical record. [Stage 3](../stage3/Stage_3_Findings.md) applies the accepted tolerance and evaluates reserve income.

## Result

The quarterly financial dataset now covers Q1 2025 through Q3 2026. Q1 2025 is a reference period for lagged inputs, with six subsequent public-company releases available for the first forecast evaluation. Original filings support the revenue and cost bridge, and Refinitiv Workspace independently matches all seven quarterly total-revenue figures through two field queries.

The supply comparison is now more precisely defined. The September difference can be decomposed arithmetically, but its economic interpretation remains partly unresolved. The provider's daily timestamps do not establish an exact observation time. A fixed adjustment to the supply series would therefore be unjustified.

## Quarterly accounting targets

Amounts are USD millions. RLDC means revenue less total distribution, transaction, and other costs.

| Quarter | Reserve income | Total revenue and reserve income | RLDC |
| --- | ---: | ---: | ---: |
| Q1 2025 | 557.911 | 578.573 | 230.926 |
| Q2 2025 | 634.274 | 658.078 | 251.136 |
| Q3 2025 | 711.241 | 739.759 | 292.147 |
| Q4 2025 | 733.396 | 770.232 | 308.782 |
| Q1 2026 | 652.508 | 694.133 | 287.352 |
| Q2 2026 | 667.733 | 701.315 | 288.845 |
| Q3 2026 | 657.624 | 864.888 | 453.254 |

Q4 2025 flow amounts are derived from FY2025 minus nine months. The workbook shows those subtractions as formulas. It does not subtract stock balances or reported percentages. Q4's average circulation and return rate come from the earnings release's operating-indicator table. Its average circulation is rounded to $0.1 billion, a lower precision than the million-level figures used in other quarters. [FY2025 filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000062/crcl-20251231.htm), [Q3 2025 filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604225000047/crcl-20250930.htm), [Q4 release](https://www.circle.com/pressroom/circle-reports-fourth-quarter-and-full-fiscal-year-2025-financial-results).

All 18 comparisons of the six principal financial lines in original 2025 quarters against their 2026 comparative disclosures agree within the fixed source-rounding tolerance. This supports consistency for those tested lines. It is not a claim that every disclosure or non-GAAP definition was unchanged. [Q1 2026 filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000150/crcl-20260331.htm), [Q2 2026 filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000248/crcl-20260630.htm), [Q3 2026 filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm).

The jump in Q3 2026 total revenue and RLDC includes ARC-related recognition, so the current dataset deliberately keeps reserve income and other revenue separate. A forecast of the reserve business should not automatically inherit that quarter's total RLDC margin.

## Disclosure dates and input eligibility

Original Item 2.02 filings confirm these six press-release dates:

| Reported quarter | Earnings-release date |
| --- | --- |
| Q2 2025 | 12 August 2025 |
| Q3 2025 | 12 November 2025 |
| Q4 2025 | 25 February 2026 |
| Q1 2026 | 11 May 2026 |
| Q2 2026 | 5 August 2026 |
| Q3 2026 | 4 November 2026 |

The original releases are documented in [August 2025](https://www.sec.gov/Archives/edgar/data/1876042/000162828025039749/crcl-20250812.htm), [November 2025](https://www.sec.gov/Archives/edgar/data/1876042/000187604225000045/crcl-20251112.htm), [February 2026](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000032/crcl-20260225.htm), [May 2026](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000148/crcl-20260511.htm), [August 2026](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000246/crcl-20260805.htm), and [November 2026](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000309/crcl-20261104.htm). Each filing explicitly identifies its reporting period. Intraday first-publication times have not been established, so the first evaluation should use a cutoff on the preceding calendar day rather than assume a release-hour ordering.

The exact annual statement used for Q4 derivations was filed on 9 March 2026, after the 25 February earnings release. The workbook distinguishes the financial source's public-by date from the earnings-release date. Later data can establish the scoring target without becoming an input to an earlier forecast.

Two Q1 2025 operating metrics, reserve return and weighted-average platform share, were recovered from later comparative disclosures. Their original earlier publication has not been established. These particular observations are therefore ineligible for a Q2 2025 forecast input. Original Q1 revenue and supply figures are available in the IPO prospectus, but a yield inferred from them would be a separately labeled proxy. [IPO prospectus](https://www.sec.gov/Archives/edgar/data/1876042/000119312525135795/d737521d424b4.htm).

## What the supply gap now tells us

The following comparison uses Circle's exact attested quarter-end circulation and the provider's following-date bucket. It is a consistent comparison convention, not proof that both observations share an instant.

| Quarter | Provider minus attested circulation, USDC millions | Difference |
| --- | ---: | ---: |
| Q1 2025 | 165.983 | 0.277% |
| Q2 2025 | (98.969) | (0.161%) |
| Q3 2025 | (97.287) | (0.132%) |
| Q4 2025 | 54.724 | 0.073% |
| Q1 2026 | 87.268 | 0.113% |
| Q2 2026 | 211.030 | 0.288% |
| Q3 2026 | 269.452 | 0.365% |

Six of seven differences exceed the predeclared 0.10% investigation threshold. The smaller Q4 difference is not classified as reconciled. Original reserve reports were downloaded, their relevant pages rendered and inspected, and all seven attested stock figures agree with the financial filings at their published rounding. [Circle's original report archive](https://www.circle.com/transparency).

Inspection of the provider's current code shows that a daily record can be created from an hourly record while replacing its timestamp with the start of the day. In some cases a daily record can subsequently be replaced by a more complete hourly record. The API history inspected does not preserve the observation block needed to establish exact EOD state. This qualifies the initial feasibility report's next-midnight alignment assumption. It does not change its successful historical RPC access test. The archived current code is evidence of the provider's data construction, not proof that an identical implementation produced every historical point. [Daily reconciliation code](https://github.com/DefiLlama/peggedassets-server/blob/master/src/peggedAssets/storePeggedAssets/reconcileDailyFromHourly.ts), [storage code](https://github.com/DefiLlama/peggedassets-server/blob/master/src/peggedAssets/storePeggedAssets/storeNewPeggedBalances.ts).

The September difference can be decomposed exactly as follows. Amounts are USDC millions.

| Component of the provider-minus-official gap | Amount |
| --- | ---: |
| API minted fields less Circle's raw approved supply | (745.581) |
| Effect of API unreleased versus Circle's allowed-not-issued totals | 875.914 |
| Circle's access-denied exclusion | 131.246 |
| Circle's pending-burn exclusion | 0.047 |
| API chain aggregation residual after minted less unreleased | 7.825 |
| Global versus chain-sum rounding | Less than 0.001 |
| Total difference | **269.452** |

This is an accounting identity between differently defined snapshots. It does not establish that the category differences are errors, that the residual is entirely a bridge error, or that these are valid corrections to apply to the daily series. In particular, the API's minted and unreleased category totals are not proven equivalent to Circle's approved-chain supply and allowed-but-not-issued categories. Missing chain fields are shown as unavailable rather than confirmed zero balances.

The aggregation code also contains bridge attribution and cached-snapshot fallbacks. These mechanisms provide concrete issues to test, but they cannot uniquely assign the September gap to timing, chain coverage, custody classification, or stale values without additional historical evidence. [Aggregation code](https://github.com/DefiLlama/peggedassets-server/blob/master/src/peggedAssets/storePeggedAssets/getAndStorePeggedAssets.ts), [USDC configuration](https://github.com/DefiLlama/peggedassets-server/blob/master/src/adapters/peggedAssets/usd-coin/config.ts).

## Refinitiv access and validation

The direct Workspace Desktop API connection described in Gold Trade works. The existing authorized helper recovers the key into memory. The key was not copied into Circle's research files. The identity query resolves Circle as CRCL.N.

An initial revenue query supplied a quarterly frequency but omitted the fiscal-quarter anchor. It returned repeated annual figures and was excluded from the quarterly checks. Adding `Period=FQ0` produced proper quarterly observations. Both `TR.TotalRevenue` and `TR.F.TotRevenue` match the seven filing-derived quarterly totals, yielding 14 successful comparisons. Provider documentation describes why the period anchor and frequency must be specified together. [LSEG quarterly-request guidance](https://community.developers.lseg.com/discussion/93931/get-data-does-not-return-quarterly-data-for-some-fields/p1).

Raw Workspace responses remain in the local licensed-data folder. The workbook's source values come from public filings and reports. Historical consensus snapshots, stock-return data, and their as-of semantics have not yet been validated for this project.

## Deliverables and next calculation

The Excel workbook contains three worksheets: the quarterly earnings bridge, the supply comparison and gap decomposition, and their source observations. Q4 derivations and all calculated subtotals remain formulas. It has been recalculated and visually reviewed, including tests of a changed source amount, a valid zero, a missing required input, and the investigation threshold.

All 81 source and arithmetic checks passed. Forty-nine workbook results also match the authoritative dataset, including their exported cached values. The exported workbook contains no error cells. All 28 downloaded public-source files included in this stage's integrity check match their saved SHA-256 hashes. These checks do not classify the unresolved economic supply differences as reconciled.

The next stage can now build the reserve-income model against six dated releases. Keep the supplier's date buckets as an estimated balance series with alignment sensitivity. Use exact historical Ethereum states for independent checkpoints. Add reserve portfolio and yield information subject to its publication date, then evaluate an RLDC range using disclosed and lagged distribution economics.

The remaining requirements before a strict historical forecasting claim are publication eligibility for each model input, treatment of revised provider history, enough original fund disclosures across the sample, and explicit assumptions for bank yields and private distribution terms. The supply work has narrowed those uncertainties without forcing an artificial exact match.
