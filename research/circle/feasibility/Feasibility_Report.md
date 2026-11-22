# Circle earnings research feasibility test

Completed 21 November 2026. Financial pilot period: Q3 2026. Scope: source access, accounting reconciliation, four Ethereum checkpoints, and three simple reserve-income estimates.

## Decision

Subsequent finding on 21 November 2026: stage two confirms that the provider's daily timestamps can represent intraday data assigned to a calendar bucket. The following-date alignment used in this pilot remains an explicit approximation, not verified EOD supply. See the [stage two findings](../stage2/Stage_2_Findings.md) for the expanded comparison and revised treatment.

**Proceed with the reserve-income and RLDC research using free data.** The test establishes that the main inputs can be obtained and combined. It does not establish out-of-sample forecasting accuracy.

Use Ethereum as the initial chain for direct validation. Keep aggregate USDC history as the broad supply input while resolving its differences from Circle's definitions. Treat RLDC as an estimated range until distribution economics are sufficiently supported. Keep valuation behind these empirical steps.

The main unresolved issues are a 0.36% aggregate circulation difference, differing timestamps and definitions in chain snapshots, incomplete visibility into bank yields and distribution arrangements, and a short history of public quarterly releases.

## Results against the feasibility questions

| Question | Result | Implication |
| --- | --- | --- |
| Can we retrieve daily USDC history for free? | Yes. 2,994 consecutive daily records, 11 September 2018 through 21 November 2026; no missing Q3 dates | A supply-driven model is practical. This is today's historical dataset, not a vintage archive |
| Can we retrieve rates without paying or supplying an API key? | Yes. 969 SOFR observations and 971 three-month Treasury observations, beginning 3 January 2023 | Free benchmarks are available; neither is automatically Circle's realized yield |
| Can we extract an auditable quarterly earnings bridge? | Yes. Issuer HTML tables, a filing PDF, and SEC companyfacts are accessible | Standard financial facts can be automated; company-specific metrics need document extraction |
| Is free historical Ethereum state accessible? | Yes. Tenderly and dRPC agree exactly in raw token units at all four tested month ends and at block 21,000,000 in 2024 | We can begin direct historical contract validation without buying an archive-node subscription |
| Do chain snapshots already reconcile exactly to DefiLlama? | No. Raw minted supply differences range from about -0.382% to +0.345% at the four checkpoints | Snapshot timing and adapter definitions require investigation before an exact-match claim |
| Is historical fund yield data available? | Yes. A September fund regulatory XML yields 21 business-day observations of trailing seven-day net and gross yields | A more relevant free source exists than Treasury rates alone, with a monthly publication lag |
| Can we forecast RLDC precisely from wallets alone? | Not established | Use disclosed arrangements, lagged effective costs, and sensitivities; do not promise exact EPS |

The 165 chain series in the aggregate response include bridged representations and other coverage. They are not a count of Circle's native supported chains. The aggregate endpoint and its chart endpoint are two views of the same provider, not independent validation.

Access evidence and response checksums are recorded in the manifest files. [DefiLlama free endpoint documentation](https://api-docs.defillama.com/llms-free.txt), [SOFR methodology and data](https://www.newyorkfed.org/markets/reference-rates/sofr), [Treasury series definition](https://fred.stlouisfed.org/series/DGS3MO).

## Reported quarter and accounting bridge

The extracted Q3 statement reconciles as follows. Amounts are USD millions.

| Component | Q3 2026 |
| --- | ---: |
| Reserve income | 657.624 |
| Other revenue | 207.264 |
| Total revenue and reserve income | 864.888 |
| Distribution and transaction costs | (409.169) |
| Other costs within the distribution and cost bridge | (2.465) |
| Revenue less distribution costs | **453.254** |

The calculated RLDC agrees with the separately reported rounded $453 million KPI. Total revenue also matches SEC's standard `Revenues` fact for the quarter. The company-specific reserve-income and RLDC measures are not directly supplied as custom concepts in the companyfacts response inspected here. [Circle Q3 2026 filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm), [SEC companyfacts response](https://data.sec.gov/api/xbrl/companyfacts/CIK0001876042.json).

Other revenue includes $181.8 million of ARC presale revenue. Consequently, extrapolating this quarter's 52.4% RLDC margin as a recurring USDC margin would be inappropriate. Any adjusted margin must also consider associated costs, rather than merely subtracting revenue. [Circle Q3 revenue recognition note](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm).

## Supply reconciliation

The September examination report supports an exact bridge within Circle's own definitions:

| September 30 component | USDC tokens |
| --- | ---: |
| Total supply on approved chains | 75,866,964,179 |
| Less tokens allowed but not issued | (1,856,810,081) |
| Less access-denied tokens | (131,245,845) |
| Less Gateway pending burns | (46,939) |
| Attested circulation | **73,878,861,314** |

The result rounds to the 10-Q's $73.879 billion circulation KPI. The report separately shows reserve assets of $73,956,687,701. This verifies that raw supply, circulation, and reserve asset value are different quantities. [Original September reserve examination report, page 2](https://6778953.fs1.hubspotusercontent-na1.net/hubfs/6778953/USDCAttestationReports/2026/2026%20USDC_Examination%20Report%20September%2026.pdf).

DefiLlama's 1 October 00:00 UTC snapshot contains 74,148,312,961 circulating USDC, which is **269,451,647 tokens, or 0.3647%, above** the attested circulation. The component bridge above does not by itself explain that provider difference. Do not subtract the same exclusions from DefiLlama again without first establishing which adjustments its aggregator already makes.

For the quarter, the mean using next-midnight snapshots is $73.528 billion versus Circle's reported $73.264 billion, a 0.3605% difference. Using the dates exactly as labeled produces $73.521 billion, so a one-day alignment choice does not remove the issue. The sum of chain circulation values at the selected endpoint is only five tokens below the provider's global value, consistent with rounding; that arithmetic agreement does not establish agreement with Circle.

Next-midnight alignment is an explicit working convention: a 1 October midnight snapshot represents the end of 30 September. The provider response does not expose a source block for every historical snapshot. The reserve report states its cutoff to minute precision. Both limitations matter when pursuing exact reconciliation.

## Ethereum validation

The tested contract is Circle's official Ethereum USDC address, `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`. Read-only `eth_call` requests retrieve `totalSupply()`, using six decimals. Block headers and their successors verify that each chosen block brackets the selected UTC end of day. [Official contract directory](https://developers.circle.com/stablecoins/usdc-contract-addresses), [Ethereum JSON-RPC documentation](https://ethereum.org/developers/docs/apis/json-rpc/).

| UTC date | Block | RPC total supply, billions | DefiLlama minted, billions | Difference in basis points |
| --- | ---: | ---: | ---: | ---: |
| 30 June 2026 | 25,433,938 | 50.892445 | 50.717326 | +34.529 |
| 31 July 2026 | 25,656,292 | 49.437395 | 49.435365 | +0.411 |
| 31 August 2026 | 25,878,704 | 50.516269 | 50.709820 | -38.168 |
| 30 September 2026 | 26,093,737 | 49.295701 | 49.295160 | +0.110 |

Tenderly and dRPC returned identical underlying integers for every row. They also agreed on supply at the older 2024 block. This demonstrates access and consistency across two providers; their underlying infrastructure may overlap, so it is not proof of independent node implementations.

Compare raw `totalSupply()` with the adapter's `minted` field. DefiLlama's Ethereum `circulating` field is a different measure: at the September endpoint it is $45.652 billion. The adapter contains unreleased-balance and bridge logic, so comparing that number directly with raw contract supply would conflate definitions. The remaining minted-field differences are unresolved, including possible snapshot timing differences. [USDC supply adapter](https://github.com/DefiLlama/peggedassets-server/blob/master/src/adapters/peggedAssets/usd-coin/index.ts).

PublicNode returned current supply and historical headers but rejected the tested historical supply calls with HTTP 403. Two other initial URLs failed TLS certificate verification. Verification was not disabled. These are endpoint-specific outcomes, not evidence that free historical Ethereum access is generally unavailable. Sustained daily extraction over years and historical mint/burn log reconstruction have not yet been tested.

## Fund yields and the first reserve-income estimates

A useful additional source is the Circle Reserve Fund's monthly Form N-MFP. Its September XML identifies series S000077205 and reports net assets of $62,467,425,771.89, agreeing with the rounded fund balance in Circle's 10-Q. It contains 21 business-day observations of seven-day net yields between 3.60% and 3.84%, alongside gross yields. The filing was accepted on 7 October 2026, before Circle's 4 November filing. [Fund filing timestamp](https://www.sec.gov/Archives/edgar/data/844779/000119312526416631/0001193125-26-416631-index.htm), [machine-readable fund XML](https://www.sec.gov/Archives/edgar/data/844779/000119312526416631/primary_doc.xml).

These are observations of a rolling yield published in a monthly filing. They are not realized daily dividends or observations proven publicly available on each economic date. They can inform a later pre-earnings estimate once filed; they cannot be inserted into a forecast dated before the filing. Complete historical XML coverage and earlier form versions still need checking.

The following initial estimates use all 92 Q3 daily supply observations. Rate gaps over non-business days carry forward the latest prior observation. No estimate is fitted to Q3 reported income. Amounts are USD millions.

| Simple model | Estimate | Difference from reported reserve income |
| --- | ---: | ---: |
| Daily supply × SOFR, ACT/360 | 689.332 | +4.82% |
| Daily supply × three-month Treasury yield, ACT/365 approximation | 730.503 | +11.08% |
| Daily supply × Q2's rounded 3.5% reserve return, ACT/365 approximation | 648.659 | -1.36% |
| Reported reserve income | **657.624** | — |

The lagged return comes from Q2's reported KPI, rather than Q3's realized return. [Q2 filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000248/crcl-20260630.htm).

The closeness of the lagged model in this single quarter could be coincidental. The estimates also use USDC circulation as an unadjusted reserve proxy while reported reserve income includes other components. The different rate conventions are stated assumptions, not exact portfolio accounting. This is a feasibility reconstruction using data retrieved today, not a point-in-time backtest.

The next model should distinguish reserve-fund income, direct Treasury income, and bank cash, and model the lag between market rates and earned income. The September fund data has not yet been used to tune the pilot estimate.

## RLDC and historical testing limits

Holding other inputs constant, a one-percentage-point change in total distribution, transaction, and other costs as a proportion of this quarter's reserve income changes RLDC by approximately **$6.576 million**. This is a sensitivity definition, not a contractual payout rate. The public filings support reported cost targets, but the test has not established complete contemporaneous platform balances or all private partner terms.

The current SEC companyfacts response exposes eight distinct standalone quarterly total-revenue periods: Q2 and Q3 2024, Q1–Q3 2025, and Q1–Q3 2026. Additional quarters may be derived from annual and year-to-date facts; reserve-income components require further filing extraction. The earlier proposal's 2023 start should remain historical context unless comparable quarterly targets are recovered.

Use Q2 2025 through Q3 2026 as the initial candidate window for six public-company quarterly releases, subject to confirming first publication and target extraction. Earlier periods can enlarge an accounting reconstruction, but information first disclosed during the IPO cannot be treated as public in earlier years. A small sample calls for simple models and transparent quarter-by-quarter errors.

There is also a specific issue with reusing DefiLlama's revenue estimate as a backtest: its inspected helper selects the nearest attestation by absolute date difference, rather than enforcing that the attestation was already published. Its implementation also uses a FRED API key, although our benchmark CSV retrieval did not require one. Reimplement the necessary logic with dated input eligibility instead of treating the dashboard as independent earnings ground truth. [Revenue helper](https://github.com/DefiLlama/dimension-adapters/blob/master/helpers/attestations-stablecoins.ts), [nearest-date utility](https://github.com/DefiLlama/dimension-adapters/blob/master/helpers/utils/findClosest.ts).

## Scope now locked for the next stage

1. Extract comparable reserve income, other revenue, and RLDC actuals for the six candidate public-company quarters. Preserve original filing dates and reconcile standalone quarters.
2. Use aggregate supply for the initial income model, with Ethereum as the direct chain-validation case. Resolve supply definitions and timestamp differences before expanding direct validation to other chains.
3. Build both an early estimate shortly after quarter end and a later estimate immediately before earnings. Only the latter may use fund monthly filings released in the intervening period.
4. Compare simple lagged-yield and benchmark models with a portfolio-aware model. Set assumptions before evaluating the holdout; do not optimize around this pilot quarter.
5. Add RLDC using lagged effective costs and explicit partner/platform scenarios. Separate ARC-related and other revenue recognition from reserve income.

The feasibility decision is a go for this scope. There is no need for a paid API or a multi-chain reconstruction before beginning it. Bank-yield visibility, historical data vintages, and exact distribution terms remain constraints on the precision of the eventual conclusions.

The saved analysis passes 34 identity, arithmetic, period, block-bracketing, and cross-source checks. Those checks verify the stated calculations; they do not mark the unresolved supply gaps as reconciled or establish forecast validity. Source responses, retrieval times, checksums, code, daily pilot inputs, and calculation outputs are saved alongside this report.
