# Circle transaction revenue backtest and subscription factors

Research date 21 November 2026. The requested historical transaction-revenue test is complete. Observing CCTP improves only a small component; total transaction revenue remains difficult to forecast. The three subscription factors are plausible candidates but are not validated predictors or assumed independent.

## Subscription and services factors

Total stablecoin supply measures industry scale, Bitcoin returns can proxy market appetite, and USDC market-share changes measure Circle's competitive position. Each has a plausible economic connection to demand for infrastructure. None mechanically determines integration completion, customer acceptance, contract price or maintenance revenue.

Use stablecoin supply growth, BTC returns and changes in USDC market share in percentage points as initial candidates. For forward forecasts, test lagged information available at the forecast date rather than future full-quarter observations. BTC volatility may matter separately, but adding more candidates to seven financial quarters would increase overfitting risk.

The three proposed series are not presumed weakly correlated. Crypto prices and stablecoin balances may share a market cycle. On any given date, with consistent definitions, total stablecoin supply multiplied by USDC share equals USDC supply. The share has a denominator in common with the market-total variable. This does not guarantee a particular pairwise correlation, but makes independence an empirical question. Even low pairwise correlation would not establish predictive value for services revenue.

Levels can rise together because of trends. Compare quarterly growth/changes as well as levels, and score actual forecasts against a simple baseline. Seven quarterly observations provide too little evidence for a defensible three-factor regression, lag optimization or robust holdout. Do not manufacture monthly revenue labels by interpolating quarterly accounts.

The preferred operating build is integration completions times expected recognized contract fees, plus maintenance from existing contracts, USYC performance fees and licensing. Market factors can help estimate future pipeline demand; they should not directly dictate all services revenue. Circle's August call describes upfront and recurring integration economics. USYC performance fees are included in subscription/services, not transaction revenue. [August call, page 15](https://s206.q4cdn.com/265218871/files/doc_earnings/2026/q2/transcript/Q226-Earnings-Transcript.pdf#page=15), [Q3 revenue note](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm).

Fresh DefiLlama market-total and FRED BTC history downloads failed because the host could not resolve their domains. Windows curl had the same failure; the alternative Node session was unavailable. No empirical correlation matrix or fitted coefficients are claimed. The collector and failed-request register preserve this limitation. The transaction test below uses previously downloaded, verified public data and is unaffected.

## What can actually be measured

CCTP's existing public adapter sums collected fees, and complete daily histories are available from Q3 2025. This supports an observable fee component. Circle does not separately disclose an audited quarterly CCTP revenue number, so the mapping of protocol fees into same-period GAAP transaction revenue remains an assumption. [Public adapter](https://github.com/DefiLlama/dimension-adapters/blob/master/fees/cctp/index.ts).

Stablecoin redemptions depend on customer tiers, waivers and credits. Gross burns are not automatically customer fiat redemptions, and net supply changes cannot identify gross redemptions. Current official pricing changed effective on or after October 19, 2026: Standard redemptions are free, Express has a headline 5bp fee, and credits can reduce it. This later policy is not applied to the older quarters. Current public pricing cannot establish historical account-specific realized fees. [Official redemption policy](https://help.circle.com/support/en/usdc-eurc-redemption-structure?id=kb_article_view&sysparm_article=KB0010644&sysparm_language=en).

USYC redemption activity may be measurable, but the applicable fee exemptions and fee-recipient mapping still need validation. The fee mints verified in the earlier stage are USYC performance fees, so adding them to the transaction model would misclassify revenue. Blockchain rewards require authenticated Circle wallets, reward entitlement and valuations. The Q3 filing describes some blockchain rewards that previously lacked quoted prices and liquidity. A complete public-wallet and valuation reconstruction was not established here. [Q3 filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm).

## Fixed-rule late model

The main test estimates a completed quarter before earnings. It is a nowcast, not a quarter-ahead forecast:

**Estimated transaction revenue = observed current-quarter CCTP fees + (previous-quarter transaction revenue minus previous-quarter CCTP fees).**

The bracketed residual includes the other businesses; it is not a measurement of redemption or blockchain rewards separately. Inputs use financial disclosure dates before the day-before-earnings cutoff. Current reconstructed daily history is not an archived historical data vintage. The outcomes were already known when this protocol was fixed. Coefficients are not optimized to outcomes.

USD millions; signed error is estimate divided by actual, minus one.

| Quarter | Actual transaction revenue | CCTP + flat residual estimate | Signed error |
| --- | ---: | ---: | ---: |
| Q4 2025 | 12.220 | 4.868 | -60.16% |
| Q1 2026 | 6.730 | 11.987 | +78.11% |
| Q2 2026 | 5.330 | 6.719 | +26.07% |
| Q3 2026 | 5.335 | 5.498 | +3.06% |

Common four-quarter mean absolute percentage errors:

| Method | MAPE | Mean absolute USD error |
| --- | ---: | ---: |
| Prior-quarter flat baseline | 42.44% | 3.613m |
| Prior-quarter day-scaled baseline | 42.03% | 3.577m |
| CCTP + flat residual | 41.85% | 3.540m |
| CCTP + day-scaled residual | 41.50% | 3.509m |

Adding measured CCTP reduces flat-model MAPE by only 0.59 percentage points. Day scaling does not change the conclusion. The Q4 2025 spike and the subsequent reversal remain in the sample. Q4 categories are annual less original nine-month figures, preserving the source-vintage construction and its comparability limit. Q3 2025 has a valid flat forecast but not a comparable CCTP bridge: the prior Q2 CCTP history has 19 missing dates. It is not quietly filled with zeros or included only for the baseline headline.

In Q3 2026 specifically: prior transaction revenue 5.330 less prior CCTP 0.307709 gives a residual of 5.022291. Add current CCTP 0.475940 to get 5.498231. Actual is 5.335. The flat baseline 5.330 was closer in this quarter; observing a small component need not improve the total when the rest changes in the opposite direction.

## Coverage and early-quarter result

| Quarter | CCTP fees, USD millions | CCTP / transaction actual |
| --- | ---: | ---: |
| Q3 2025 | 0.348 | 7.45% |
| Q4 2025 | 0.551 | 4.51% |
| Q1 2026 | 0.318 | 4.73% |
| Q2 2026 | 0.308 | 5.77% |
| Q3 2026 | 0.476 | 8.92% |

The observable CCTP component is only about 4.5%-8.9% of transaction revenue. Forecast uncertainty remains concentrated in the rest. This is different from the earlier 11.9% ratio, which combined USYC performance fees and CCTP against ordinary total other revenue.

The early test uses only the first 30 calendar days of CCTP observations, extrapolates their daily pace to quarter length, and carries the most recent publicly disclosed financial residual at a daily rate. It does not use the immediately preceding quarter when those financials were still unpublished. On the common Q1-Q3 2026 sample, early-model MAPE is 61.92%, compared with 62.04% for the latest-public flat baseline and 62.64% for its day-scaled version. A Q3 2026 early estimate uses Q1 financials because Q2 was not released until August 5. This is why simply using Q2 would introduce hindsight.

## Interpretation and next model

The requested reserve-income accuracy has not been reproduced for transaction revenue. We can track part of it, but must not claim the entire $5.335m line is observable on-chain. Prioritize redemption-fee customer economics and authenticated blockchain rewards before adding more generic market predictors. Evaluate whether each newly observed component actually reduces the error on the same sample.

For subscription/services, preserve USYC performance fees as an observable component and forecast the private integration/maintenance residual separately. Your three factors are useful hypotheses for this residual and the contract pipeline, not established coefficients. A prospective data archive and more financial periods are needed to validate them.

The companion workbook contains formulas, source dates, the late and early tests, missing-coverage flags and the complete downloaded daily CCTP history. Original Stage 2/3 files and the dated Q4 other-revenue forecast remain unchanged.
