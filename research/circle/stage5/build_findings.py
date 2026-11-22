"""Build the research note from saved computed results, without refitting models."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def get(n):return json.loads((ROOT/'results'/n).read_text(encoding='utf-8'))
reg=get('subscription_regression.json');fund=get('usyc_fund_and_services_analysis.json');flow=get('usdc_flow_analysis.json');route=get('cctp_route_and_cohort_analysis.json');supply=get('supply_projection_forecast.json');mix=get('usdc_chain_composition.json');ff=get('2026-11-21_Q4_USYC_fee_forecast.json');drv=get('usyc_forward_build_inputs.json')
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])
factors=table(['Quarter','Services revenue ($m)','Mean stablecoin value ($bn)','Mean BTC close ($)','Mean USDC share'],[[q['period'],f"{q['services_actual_usd_million']:.3f}",f"{q['stablecoin_mean_usd_billion']:.3f}",f"{q['btc_mean_usd_thousand']*1000:,.2f}",f"{q['usdc_mean_share_pct']:.3f}%"] for q in reg['quarterly_inputs']])
sources=table(['Quarter','Target public by','Financial source'],[[q['period'],q['target_public_by'],f"[Source]({q['target_source_url']})"] for q in reg['quarterly_inputs']])
fits=table(['Quarter','Actual ($m)','OLS fitted ($m)','Leave-one-out fitted ($m)','LOO absolute error'],[[q['period'],f"{q['services_actual_usd_million']:.3f}",f'{a:.3f}',f'{b:.3f}',f"{abs(b/q['services_actual_usd_million']-1):.1%}"] for q,a,b in zip(reg['quarterly_inputs'],reg['primary_levels_ols']['fitted'],reg['primary_levels_ols']['loo_predictions'])])
fundtable=table(['Quarter','Observed performance fee ($m)','Last report NAV proxy ($m)','Reports'],[[q['period'],f"{q['performance_fees_usd_million']:.3f}",f"{q['ending_report_aum_usd_million']:,.3f}",q['reports']] for q in fund['quarterly']])
nowcasts=table(['Quarter','Services actual ($m)','Fee + lagged residual ($m)','Signed error'],[[q['period'],f"{q['actual_services']:.3f}",f"{q['fee_plus_flat_residual_estimate']:.3f}",f"{q['fee_plus_flat_residual_error']:+.1%}"] for q in fund['services_nowcasts']])
early=table(['Quarter','Information cutoff','Calibration quarter','Actual reserve income ($m)','Flat supply estimate ($m)','Continue net pace ($m)'],[[q['period'],q['cutoff'],q['base_period'],f"{q['actual_reserve_income']:.3f}",f"{q['methods']['flat_last_supply']:.3f}",f"{q['methods']['continue_first30_net_flow_pace']:.3f}"] for q in supply['rows']])
chains=table(['Chain','Provider circulation ($m)','Share of provider global total'],[[q['chain'],f"{q['provider_circulation_usd_million']:,.3f}",f"{q['share_global']:.2%}"] for q in mix['quarterly'][-1]['chains']])
note=f"""# Circle: additional on-chain evidence and subscription/services regression

Research date: 21 November 2026. All amounts are USD unless specified. This extension keeps the earlier reserve models, transaction backtest and dated ARC assumptions intact.

The three-factor regression has an in-sample R² of **46.27%**, adjusted R² of **−7.46%**, and leave-one-quarter-out mean absolute percentage error of **38.10%**. It is not yet suitable as the main services forecast. The most useful additional earnings input is the USYC performance-fee series reconstructed directly from fund-report events. Ethereum mint/burn and CCTP data also provide auditable evidence about supply movements, migration and usage, with carefully bounded interpretations.

## 1. Exactly what went into the regression

The dependent variable is quarterly **subscription and services revenue**, excluding transaction revenue and ARC token sales. The sample is Q1 2025–Q3 2026: seven quarterly targets. Daily market data provide 638 dates, but the effective regression sample is still seven quarters. We did not repeat quarterly revenue across daily rows to manufacture a larger sample.

The proposed factors are measured as follows:

| Factor | Free source and raw field | Transformation |
| --- | --- | --- |
| Total stablecoin market | [DefiLlama stablecoin history](https://stablecoins.llama.fi/stablecoincharts/all), sum of each date's `totalCirculatingUSD` peg categories | Average daily USD values across each quarter, then divide by 1 billion |
| BTC price | [Coinbase public candle API](https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles), `BTC-USD`, `granularity=86400`, close at array index 4 | Average UTC daily closing prices across the quarter; regression uses $000 |
| USDC share | [DefiLlama USDC history](https://stablecoins.llama.fi/stablecoin/2), `tokens[].circulating.peggedUSD` | For each date, USDC units valued at $1 divided by the same day's total stablecoin USD value; average the daily ratios; regression uses percentage points |

Example BTC request: `https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400&start=2025-01-01T00:00:00Z&end=2025-04-01T00:00:00Z`.

Each quarter fits within Coinbase's 300-candle maximum. Responses can include extra buckets, so the code filters to the requested quarter, deduplicates timestamps, checks OHLC ranges and requires complete date coverage. No missing factors were filled or interpolated. Stablecoin observations use provider dates; these are daily snapshots rather than a precisely synchronized continuous-time market measure. USDC at par divided by all tracked stablecoin USD value is our definition, not Circle's narrower fiat-backed stablecoin market-share measure.

{factors}

Financial targets come from the Stage 4 filing ledger. Q1 2025 uses the first comparable category split, $18.711m, derived from the six-month amount less Q2 and publicly available in August 2025. A later comparative reports $17.488m. We preserve the first split and show the later value as a sensitivity, rather than select whichever gives a higher R².

{sources}

## 2. Regression equation, fit and interpretation

Ordinary least squares includes an intercept and all three requested factors. Python uses NumPy's SVD least-squares solver; the workbook independently solves centered normal equations with live formulas.

```text
Estimated quarterly services revenue ($m)
 = 14.13747
 + 0.114249 × mean total stablecoin value ($bn)
 + 0.012274 × mean BTC close ($000)
 − 0.929780 × mean USDC share (percentage points)
```

A USDC share of 24.56% enters as 24.56, not 0.2456. The negative share coefficient is a conditional association in a very small sample, not evidence that greater USDC adoption causes lower services revenue.

| Statistic | Result | Meaning |
| --- | --- | --- |
| Observations / parameters | 7 / 4 | Intercept plus three factors leaves only three residual degrees of freedom |
| In-sample R² | 46.27% | The fitted equation explains this fraction of variation around the sample mean; it is not forecast accuracy |
| Adjusted R² | −7.46% | The fit is weak after penalizing the number of estimated parameters |
| In-sample MAPE | 11.92% | Uses the same observations that determined the coefficients |
| Leave-one-quarter-out MAPE | 38.10% | Remove one quarter, refit on six, then predict the omitted quarter |
| Leave-one-out predictive R² | −2.175 | Omitted-quarter squared errors exceed the full-sample-mean reference's squared deviations |

{fits}

Leave-one-out is a diagnostic, not a forward-time backtest: its training set can include quarters later than the omitted one. There are too few quarters to establish a stable three-factor forecasting model. No statistically reliable significance or causal claim is made.

The factors are not independent. Stablecoin value versus BTC correlation is −0.520; stablecoin value versus USDC share is −0.273; BTC versus USDC share is +0.624. Variance inflation factors are 1.38, 2.09 and 1.65 respectively. These do not indicate extreme multicollinearity in this sample, but low VIF alone does not make a useful forecast. Private contract timing, category comparability and the short history remain important uncertainties.

The predetermined quarterly growth/change diagnostic has six observations, R² 56.38% and adjusted R² −9.04%. A lagged-factor diagnostic has six observations, R² 61.11% and adjusted R² 2.77%. Substituting the later Q1 revenue comparative gives levels R² 50.59%. None provides persuasive validation. These are disclosed diagnostics, not specifications selected as a new base forecast.

**Forecast treatment:** keep the three-factor regression as an exploratory appendix. Forecast identifiable fee components directly; retain a separate, explicitly uncertain assumption for undisclosed service contracts. Do not mechanically increase all services revenue whenever BTC or stablecoin capitalization rises.

## 3. Ethereum USDC: reconstruct issuance and distinguish migration

The official Ethereum USDC contract is `0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48`, authenticated against [Circle's contract registry](https://developers.circle.com/stablecoins/usdc-contract-addresses). We read its `Mint` and `Burn` events using public Ethereum JSON-RPC `eth_getLogs`, and opening/closing `totalSupply()` using historical `eth_call`.

Event layouts were checked against [Circle's Solidity source](https://github.com/circlefin/stablecoin-evm/blob/master/contracts/v1/FiatTokenV1.sol): `Mint(address,address,uint256)` and `Burn(address,uint256)`. USDC has six decimal units. The minter/burner is taken from the indexed actor field, not inferred from a wallet label.

Q3 UTC boundaries were first located with DefiLlama's block lookup, then checked against actual block timestamps immediately before/after midnight. Included blocks are **25,433,939–26,093,737**. Opening supply is at block 25,433,938. Logs are deduplicated by transaction hash and log index. Ranges split adaptively when free providers reject or cap results. Tenderly's public gateway supplied the historical log/state calls; PublicNode supplied block data, with dRPC as a fallback. Request payloads and response hashes are saved. Endpoints are providers, not the source of contract identity.

| Q3 2026 Ethereum supply bridge | USDC / $m at par |
| --- | --- |
| Opening contract supply | {flow['opening_supply_usd_million']:,.6f} |
| Minted | {flow['quarter']['amounts_usd_million']['mint']:,.6f} |
| Burned | ({flow['quarter']['amounts_usd_million']['burn']:,.6f}) |
| Closing contract supply | {flow['closing_supply_usd_million']:,.6f} |
| Net change | {flow['quarter']['net_usd_million']:+,.6f} |
| Of which, net CCTP mint/burn | {flow['quarter']['cctp_net_usd_million']:+,.6f} |
| Of which, remaining actors | {flow['quarter']['non_cctp_net_usd_million']:+,.6f} |

The **488,594 mint/burn events reconcile exactly in integer token units**: opening supply + all mints − all burns = closing supply, difference zero. Classification uses CCTP V1/V2 token minters returned by `localMinter()` on the officially registered TokenMessenger contracts at both quarter endpoints; those addresses were unchanged at the two controls.

This matters economically: Ethereum supply fell about $1.597bn, but the CCTP component added about $0.577bn net. Other actors accounted for a $2.174bn decline. Looking only at Ethereum's net decline could confuse cross-chain migration with broader issuance activity. The residual is still not a verified measure of fiat customer redemptions, and it cannot be multiplied by a redemption fee as if every burn were chargeable. This contract supply also includes issuer/system holdings and differs from global circulating USDC.

The reserve model continues to use **global** daily circulating USDC × yield. Do not add Ethereum net flows again to an already observed global supply series. The direct event reconstruction is an audit and demand-composition extension to that model.

## 4. CCTP routes, concentration and actual protocol fees

We authenticate [Circle's CCTP contract addresses](https://developers.circle.com/cctp/references/contract-addresses), then decode V2 source `DepositForBurn` and destination `MintAndWithdraw` events separately. The emitting Ethereum V2 TokenMessenger is `0x28b5a0e9c621a5badaa536219b3a228c8168cf5d`.

The `DepositForBurn` ABI is derived from the downloaded [official V2 source](https://github.com/circlefin/evm-cctp-contracts/blob/master/src/v2/TokenMessengerV2.sol), because a generic documentation event table did not match its field/index layout. Its signature is `DepositForBurn(address,uint256,address,bytes32,uint32,bytes32,bytes32,uint256,uint32,bytes)`. We filter burnToken to official USDC, decode six-decimal amounts, destination domains and depositor addresses, and count each source event once. Token-level V2 burns match the source events in both amount and count. Destination-token mints separately match delivered amounts plus fees.

Q3 Ethereum V2 source activity: **155,899 USDC events**, **$11.458bn** volume, **22,219 depositor addresses**. The ten largest depositor addresses account for **66.03%** of volume. July-to-August returning-address rate is **19.73%**; August-to-September is **17.43%**. These are CCTP sender-address cohorts, not all USDC holders or unique people. Routers and exchange operations can account for many users behind one address. Requested fast-finality share, 61.75%, is not the same as observed fee-paying share.

For fees, `MintAndWithdraw(address,uint256,address,uint256)` exposes `feeCollected`. Filter its mintToken to USDC and sum the last data word / 1e6 across destination events. There are 150,383 filtered USDC delivery events, of which 70,727 have a positive fee. Direct Q3 Ethereum fees are **${route['destination_fees_usd']:,.2f}**, compared with **${route['defillama_ethereum_fees_usd']:,.2f}** in the earlier [DefiLlama CCTP fee aggregate](https://api.llama.fi/summary/fees/circle-cctp?dataType=dailyFees). The **$5,255.85 / 3.53% difference remains unresolved**. Both series are retained; this does not silently revise the earlier transaction backtest.

Source-route volume and Ethereum destination fees refer to different transaction populations. Dividing those two totals would not give a valid fee rate. To estimate total CCTP protocol fees, collect destination fee events across supported destination chains and sum once per delivery. Mapping protocol fees into consolidated transaction revenue also needs accounting timing and treatment. This stage demonstrates one chain end-to-end; it does not claim an all-chain GAAP revenue total.

## 5. USYC: a directly observable component of services revenue

[Circle's public API documentation](https://developers.circle.com/tokenized/usyc/web2-apis) provides the historical endpoint `https://usyc.hashnote.com/api/price-reports`. The saved snapshot contains a recent window, so it alone cannot establish the complete seven-quarter history. We extended it by scanning the reporter's historical on-chain `Transmitted` events.

Official Ethereum USYC is `0x136471a34f6ef19fe571effc1ca711fdb8e49f2b`; the reporter is `0x9fde717a21c5b272b8956d3aa0c3551e1ffd23d7`. Authentication combines [Circle's USYC registry](https://developers.circle.com/tokenized/usyc/smart-contracts), the issuer API transaction hash and the previously saved receipt control. The scan filters this reporter and USYC token, covers both pre/post July 2026 event versions, and reconstructs **438 consecutive report rounds** from January 2025 through September 2026.

The event signatures are `Transmitted(address,uint256,uint256,uint256,uint256,uint256,uint256,uint256)` and a later version with one extra uint256. After indexed token/round fields, six data words give principal, interest, share supply, economic updatedAt, price and fee shares; the newer seventh word gives embeddedIncome. Calculations are:

```text
fee in dollars = (raw fee shares / 1e6) × (raw price / 1e18)
NAV proxy      = (reported raw share supply / 1e6) × price
gross income  = (raw interest + raw embeddedIncome, if present) / 1e6
```

In all 438 reports, dollar fees match 10% of reported gross income within $0.01 rounding. Actual block timestamps determine when information became observable and which quarter receives the observation. The economic timestamp is also retained. Observation-quarter sums can differ from accounting accrual-quarter sums.

{fundtable}

These are fund-reporter observations, not audited product-level GAAP revenue. Do not add BSC/wrapped representations to the reporter's share supply. Last-report NAV is neither daily average NAV nor a fully reconciled global NAV. Q1 2025 includes pre-acquisition history and is not assumed fully Circle-attributable; services nowcast scoring starts Q3 2025 using Q2 as its prior-period baseline.

The simple earnings bridge tested is:

```text
current services estimate
 = observed current-quarter USYC performance fees
 + (previous publicly reported services − observed prior-quarter USYC fees)
```

It keeps the unobserved service-contract component flat. Prior financial targets must be public by the day before the current earnings release; current-quarter financial actuals are used only to score the estimate. On-chain history is reconstructed now, not from archived pre-earnings API vintages.

{nowcasts}

Five-quarter MAPE is **25.01%**, versus **25.16%** simply carrying forward total services. That is only a 0.15 percentage-point improvement. We can measure the fee component, but its movement does not explain the larger fluctuations in the remaining contract revenue. For Q3 2026 the observed fund fee is $2.546m against services of $19.587m, about 13.0% on this conditional bridge.

## 6. A dated, genuine Q4 2026 USYC fee projection

This is a prospective forecast recorded on 21 November 2026 with actual left unknown. The latest saved issuer report is 20 November. Known Q4 report fees total **$1.208828m** across 35 reports. There are 41 calendar days from 21 November through 31 December.

Case A holds the trailing 28-calendar-day fee pace constant:

```text
Q4 fee = 1.208827909 + (0.641469974 / 28) × 41
       = $2.148123m
```

Case B holds the latest reported NAV constant and uses the trailing implied gross yield:

```text
Trailing gross income             = $6.414699736m
Mean NAV across 19 trailing reports = $2,168.396874m
Implied annual gross yield         = 6.414699736 / 2,168.396874 × 365 / 28
                                   = 3.856314%
Latest reported NAV                = $2,016.349463m
Q4 fee = 1.208827909 + 2,016.349463 × 3.856314% × 10% × 41 / 365
       = $2.082260m
```

The mean is across report observations rather than a calendar-day-weighted NAV, so Case B's yield is an approximation. These are **two explicit scenarios of about $2.08m and $2.15m**, not a statistical confidence interval. They forecast only the USYC performance-fee component, not total services or profit. Future fund flows, rates, fee terms and recognition timing can change. The dated JSON refuses to overwrite itself if inputs change; future revisions must be stored separately.

## 7. Global supply forecasting earlier in the quarter

To test whether observed net issuance momentum adds predictive value, two fixed rules use only the first 30 calendar days of global USDC data: (A) hold supply at day 30; (B) continue the mean daily net change from the preceding quarter-end to day 30. Future SOFR is held at the latest rate available at the cutoff. NY Fed SOFR publication is on the following business day; the next effective-date observation in the continuous series is used as that publication-day control. An effective-date rate not yet published is excluded. This is a day-level cutoff rather than an archived intraday trading simulation.

For each target quarter, the spread is calibrated only to the latest financial quarter whose reserve-income figure was public by that early cutoff; often that is two quarters back. The calculation is:

```text
Reserve estimate = sum(projected USDC × available/projected SOFR / 360)
                 + lagged annual spread × sum(projected USDC-days) / 365
```

{early}

Across five quarters, flat-supply MAPE is **{supply['metrics']['flat_last_supply']['mape']:.2%}**; continuing the net-flow pace gives **{supply['metrics']['continue_first30_net_flow_pace']['mape']:.2%}**. Simple momentum extrapolation did not improve this sample. These forecasts have much less information than a completed-quarter reserve nowcast and should not be compared as equivalent tasks. Historical supply and rate snapshots are current vintages; provider revisions remain possible. Earlier Stage 3 results and dated forecasts are preserved.

## 8. Chain mix as business context

The same USDC history includes `chainBalances`. We extract selected-chain quarter-end `circulating` fields and divide by the global provider total. Its `minted` fields are kept separately in the workbook. This is a provider bridge-adjusted circulation measure, not a pure native-token holder census.

{chains}

These values use the provider's 30 September daily snapshot; they are not the exact quarter-end RPC state used in the stock-flow reconciliation. Differences can therefore reflect both timing and circulation definitions. Arc-chain USDC circulation is activity context; it does **not** identify ARC token investor sales, ARC revenue or gas fees retained by Circle.

## 9. What to use in the equity report

Use the reserve-income model as the main earnings estimate. Add the raw-unit Ethereum supply reconciliation as the clearest demonstration that you can authenticate contracts, query events, decode units, avoid double counting and explain migration. Include USYC's fee-share × price reconstruction and its prospective component forecast as a second financial bridge. CCTP routes, concentration and sender cohorts support a business-quality discussion; the direct-versus-aggregator fee difference belongs in the methodology limitations.

Keep the market-factor regression as a documented test that currently fails to justify a strong forecast claim. Its weak predictive diagnostic is a research result. Identifying what the public chain cannot reveal is part of sound on-chain analysis.

No new authenticated ARC investor-distribution contract was established in this extension. The separate user scenario remains: no new sales without evidence, conditional Q4 recognition of the remaining $60.4m deferred amount, then zero further recognition from that existing balance. Recognition is revenue, not automatically profit, and timing remains conditional on the contract's accounting milestones. The earlier guidance-based scenario remains a separate dated record.

## 10. Audit and reproduction files

`README.md` gives the execution sequence. `source_manifest.json` preserves public request URLs, payloads, retrieval timestamps and response SHA-256 hashes. Large JSON responses are losslessly gzipped, with uncompressed hashes retained in `results/archive_manifest.json`. No paid API or Refinitiv key was required. `results/verification.json` records independent arithmetic and source-integrity checks; `results/workbook_qa.json` records formula and changed-input controls. Workbook preview images are in `previews`.

The workbook has a live primary regression, 638 dated factor rows, the USDC supply bridge, USYC fee history, the services nowcast and the two Q4 fee formulas. Formula evaluation and exported cached values were checked with ArtifactTool; native Excel application recalculation was not tested. Exploratory lagged/growth regression outputs are Python results displayed in the workbook, not live alternative fits.
"""
(ROOT/'Stage_5_Findings.md').write_text(note,encoding='utf-8')
print('Wrote Stage_5_Findings.md')
