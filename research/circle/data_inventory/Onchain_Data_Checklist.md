# Circle on-chain data checklist

Audit date: **22 November 2026**. This is the data inventory requested before drafting the equity research report. It covers the financially relevant observable data families identified so far, including sources that do not improve earnings forecasts. It is not a claim that every candidate has been downloaded or every Circle business can be reconstructed publicly.

## First: what the two CCTP amounts mean

The **$154,093.848015** is the sum of actual `feeCollected` amounts in USDC from CCTP V2 destination-side events on Ethereum during Q3 2026, using our direct contract extraction. **$148,838** is DefiLlama's Ethereum fee series summed over the same quarter. These are two measurements, not two forecasting methods. The difference is **$5,255.848015, or 3.53% of the aggregator value**. It remains unresolved. A fresh download on this audit date reproduces the aggregator amount; it does not resolve the discrepancy.

The direct fee audit covers **one chain and one quarter**. We have not run it across all seven financial quarters. It is separate from forecasting Circle's entire transaction-revenue line, which also includes other services and fees. There is no separately disclosed audited quarterly CCTP revenue series against which to calculate a Circle-reported CCTP prediction error.

### Exact backtest coverage

| Workstream | Methods / observations | Actual evaluation coverage | What the result establishes |
| --- | --- | --- | --- |
| USDC supply reconciliation | Aggregated daily supply vs company disclosures | Seven financial quarters, Q1 2025–Q3 2026 | Supply is a useful reserve-balance proxy; this is not seven independent EPS forecasts |
| Reserve income | SOFR plus lagged gap; fund yield plus lagged gap; carry baseline | Six target quarters, Q2 2025–Q3 2026; Q1 calibration | Main methods' MAPE approximately 0.34% and 0.24%; retrospective, current-vintage supply limitations remain |
| Transaction revenue | Prior flat; day-scaled flat; observed CCTP plus lagged residual; day-scaled residual | **Four common target quarters, Q4 2025–Q3 2026** | MAPE 42.44%, 42.03%, 41.85%, 41.50% respectively; component observability has not solved total-revenue forecasting |
| Direct CCTP fee measurement | RPC event sums vs aggregator | **Ethereum, Q3 2026 only** | Approximately 3.53% measurement discrepancy, not a prediction error |
| USYC / services | Observed performance fee plus lagged services residual vs flat | Five target quarters | Approximately 25.01% vs 25.16% MAPE; small improvement |
| Three proposed services factors | Stablecoin total, BTC price, USDC share | Seven quarterly observations; regression and leave-one-out diagnostics | R² 0.4627; adjusted R² −0.0746; leave-one-out MAPE about 38.1%. This is not seven forward forecasts |
| Distribution costs / RLDC | Eight alternatives | Six target quarters | Pooled three-quarter ratio cost MAPE approximately 0.94%; underlying RLDC MAPE approximately 2.98% |
| Full GAAP diluted EPS | Accounting bridge not completed | None yet | We cannot claim demonstrated EPS accuracy |

The transaction methods and their original inputs are preserved in [Stage 4 transactions](../stage4/transactions/Findings.md). The later regression and direct-chain work are in [Stage 5](../stage5/Stage_5_Findings.md), which supersedes the earlier statement that the services factors had not yet been tested. Original dated forecasts are unchanged.

### Seven-quarter CCTP coverage audit

These are **current-vintage aggregator observations**, rechecked on 22 November. An observed partial sum is not a complete-quarter estimate. A missing day is not assumed to have zero activity.

| Quarter | Aggregate dates present / expected | Observed global fees, USD | Comparable four-method transaction forecast? | Direct-chain fee validation? |
| --- | --- | ---: | --- | --- |
| Q1 2025 | 0 / 90 | Missing | No | No |
| Q2 2025 | 72 / 91 | 21,110, partial | No | No |
| Q3 2025 | 92 / 92 | 347,579 | Excluded from common sample: preceding Q2 incomplete | No |
| Q4 2025 | 92 / 92 | 551,443 | Yes | No |
| Q1 2026 | 90 / 90 | 318,316 | Yes | No |
| Q2 2026 | 91 / 91 | 307,709 | Yes | No |
| Q3 2026 | 92 / 92 | 475,940 | Yes | Ethereum only |

Full date-presence tests do not establish complete chain coverage, correct asset scope or GAAP recognition. The previous early-quarter test used first-30-day observations and the financial statement actually public at the forecast date; it covered three common quarters, with roughly 61.92% MAPE versus 62.04% for the latest-public flat baseline.

## How to read the checklist

- **V — verified in stated scope:** extracted and checked against a meaningful identity or reconciliation. A check mark applies only to that scope.
- **E — extracted:** data downloaded, with incomplete economic or accounting validation. No check mark.
- **P — public reference:** page, SQL, contract documentation or methodology reviewed; extraction/history not established here.
- **A — access needed:** account, API key, credits or licensed access may be required; entitlement not assumed.
- **N — not established publicly:** exact commercial/ownership information is unavailable or unauthenticated. Do not substitute a convenient proxy and call it observed.

“Model input” below means an eligible input after its stated checks, not proof that it improves forecasts. Dollars, token units and shares must stay separate. Aggregate daily series generally refresh daily; contract events can be sampled after finality. Provider-date observations are not automatically end-of-day values.

## A. Supply and reserve-balance perimeter

Sources: [DefiLlama USDC API](https://stablecoins.llama.fi/stablecoin/2), [stablecoin registry](https://stablecoins.llama.fi/stablecoins?includePrices=true), [EURC API, registry ID 50](https://stablecoins.llama.fi/stablecoin/50), [Circle's native USDC contracts](https://developers.circle.com/stablecoins/usdc-contract-addresses), [EURC contracts](https://developers.circle.com/stablecoins/eurc-contract-addresses), [Dune USDC](https://dune.com/markets/stablecoins/usdc), [Dune Circle issuer page](https://dune.com/markets/stablecoins/circle).

| Check / ID | Data and actual extraction route | Research use | Status and next check |
| --- | --- | --- | --- |
| [x] S01 | Global daily USDC supply: `tokens[].circulating.peggedUSD` from stablecoin/2; quarter averages and endpoints | Largest reserve-income balance input | **V**, seven-quarter comparison to company disclosures; fresh sample has 2,995 dates, 2018-09-11–2026-11-22. Historical vintages may change |
| [ ] S02 | USDC chain balances and daily chain histories: same response's `chainBalances` | Explain chain mix and identify material validation targets | **E**; response includes native and bridged representations. Never sum every chain balance as new reserve-backed liabilities |
| [x] S03 | Ethereum native USDC historical `totalSupply` and mint/burn event identity | Direct validation of the on-chain accounting | **V**, Q3 2026 only; opening + mints − burns equals closing in integer token units |
| [ ] S04 | Native supply on Solana, Base, Arbitrum, Stellar and other material chains: official mint registry plus chain-specific RPC | Broader independent balance verification | **P**, no completed all-chain historical reconstruction; token-program and pre-mint rules differ |
| [ ] S05 | EURC daily supply: stablecoin registry search for EURC/EUROC, then stablecoin/50 | Separate euro reserve-income contribution | **E**, 1,607 dates, 2022-06-30–2026-11-22. Preserve EUR units; convert to USD with matched FX and use euro earned yields |
| [ ] S06 | EURC chain issuance/burns and holder balances | Verify EURC growth and native perimeter | **P**, official contracts found; event history not independently reconstructed |
| [ ] S07 | `unreleased` / pre-mint inventories and issuer-held unissued tokens | Reconcile gross token supply to circulation earning reserves | **E**, provider fields available; authenticate address and treatment histories before an explicit adjustment |
| [ ] S08 | Blocked/frozen balances, blacklisting events and recoveries | Explain circulation adjustments and exceptional risks | **P**, events can be extracted; frozen does not automatically mean excluded from reserve liabilities |
| [ ] S09 | Pending burns, cross-chain messages in transit and Gateway pre-mints | Explain timing gaps and prevent double counting | **P**, contract/announcement references; need historical snapshots and liability treatment |
| [ ] S10 | Third-party bridged USDC, canonical bridge escrow and wrapper backing | Deduplicate economic supply | **E/P**, chain metadata available; map wrapper-to-underlying and avoid adding locked native backing twice |
| [ ] S11 | Raw totalSupply → adjusted circulation → Circle reported circulation bridge | Turn blockchain balances into the financial perimeter | **V** for aggregate tolerance comparison; explicit address-level adjustment ledger is incomplete |
| [ ] S12 | Stablecoin prices, peg deviations and liquidity | Distinguish par reserve liabilities from market prices and stress | **P**, DefiLlama price API / DEX trades; USDC reserve-balance model uses par, not depeg market cap |

## B. Issuance, redemption and organic demand

Sources: direct native-token and CCTP events; [existing Ethereum extraction](../stage5/collect_chain.py); [Visa / Allium](https://visaonchainanalytics.com/); [Artemis stablecoins](https://www.artemis.ai/sectors/stablecoins/overview?tab=usage); [Coin Metrics community data](https://docs.coinmetrics.io/getting-started/coin-metrics-community-data).

| Check / ID | Data and extraction route | Research use | Status and next check |
| --- | --- | --- | --- |
| [x] F01 | Gross native mints and burns: event logs, exact decimals, UTC block boundaries | Show gross issuance activity behind net supply | **V**, Ethereum Q3 2026; 488,594 mint/burn events reconcile exactly |
| [x] F02 | CCTP versus other minter activity: historical authenticated minter roles | Separate interchain relocation from other issuance | **V**, Ethereum Q3 only; “other” is not synonymous with fiat mint/redemption |
| [x] F03 | Net non-CCTP supply change on Ethereum | Demand/context indicator | **V**, Q3 residual approximately −$2.174bn; not directly fee-paying redemptions |
| [ ] F04 | Chargeable fiat redemption volume, customer tier and realized fee | Transaction-revenue input if economic entitlement established | **N**, public burns do not identify off-chain customer/tier, exemptions or paid fees |
| [ ] F05 | Address balances, active addresses and transfer counts | Adoption breadth and retention context | **P/E**, Dune/Artemis/Coin Metrics; addresses are not customers and internal transfers inflate usage |
| [ ] F06 | Gross versus adjusted transfer value, by chain and use case | Separate settlement activity from bots, exchange and contract churn | **P**, Visa/Allium and Artemis methodologies reviewed; export/API histories not yet downloaded |
| [ ] F07 | Newly funded addresses, cohorts and holding-duration / balance persistence | Explain sticky reserve balances and forecast supply | **P**, raw transfers/balances support calculation; distinguish contract aggregators from users |
| [ ] F08 | Cross-chain canonical and third-party bridge net flows | Explain where supply migrates without new reserves | **P/E**, CCTP subset extracted; complete bridge deduplication not done |

## C. Distribution costs and platform economics

Sources: native balances and role mappings, provider labels, [Circle's USDC economics explanation](https://www.circle.com/blog/the-economics-of-usdc-and-why-our-partners-win), original financial disclosures, [existing RLDC tests](../stage5/rldc/Findings.md).

| Check / ID | Data and extraction route | Research use | Status and next check |
| --- | --- | --- | --- |
| [ ] D01 | Authenticated Coinbase-associated USDC balances / custody wallets | Potential distribution-cost mix proxy | **P/N**, labels do not reveal total eligible custody/off-chain balances or contract-defined reward base |
| [ ] D02 | Binance and other partner balances, eligible holdings and incentive terms | Retained reserve-yield sensitivity | **P/N**, public wallets are a subset; exact eligibility/terms can remain private |
| [ ] D03 | Circle-controlled wallets and balances | Distinguish platform holdings from third-party custody | **P/N**, authenticate ownership across dates; do not assume a label equals financial platform KPI |
| [ ] D04 | USDC deployed into DeFi lending, pools and collateral positions | Platform/adoption mix and concentration | **P**, Dune / protocol contracts; this does not itself identify a distribution payment |
| [ ] D05 | Exchange deposits/withdrawals and balances by labeled venue | Market structure and balance-stickiness context | **P/A**, Dune / Artemis / commercial labels; free export and completeness unverified |
| [ ] D06 | On-chain reward distributions to partners or holders | Potential direct cost observation | **N**, no complete authenticated payment ledger tied to Circle's expense recognition; many costs settle off chain |

The current best cost model uses a lagged financial ratio, not a complete on-chain reconstruction of partner expenses. Include that limitation prominently in the report.

## D. CCTP: the clearest transaction-fee extraction example

Sources: [Circle CCTP](https://www.circle.com/cross-chain-transfer-protocol), [contract registry](https://developers.circle.com/cctp/references/contract-addresses), [DefiLlama fee API](https://api.llama.fi/summary/fees/circle-cctp?dataType=dailyFees), [open-source fee adapter](https://github.com/DefiLlama/dimension-adapters/blob/master/fees/cctp/index.ts), [direct extraction results](../stage5/results/cctp_route_and_cohort_analysis.json).

| Check / ID | Data and extraction route | Research use | Status and next check |
| --- | --- | --- | --- |
| [x] C01 | Source `DepositForBurn` events, filtered by actual USDC `burnToken` | Count and value cross-chain demand | **V**, Ethereum Q3 2026; 155,899 source events, approximately $11.458bn outgoing |
| [x] C02 | Source chain → destination domain route volumes | Geography of chain usage and route concentration | **V**, Ethereum Q3; domain registry must be versioned, not inferred from token tickers |
| [x] C03 | Destination `MintAndWithdraw.feeCollected`, USDC only | Observed protocol fee component | **V** as decoded events in Ethereum Q3; $154,093.848015. Aggregator reconciliation incomplete |
| [ ] C04 | Global daily and chain-level collected fee totals from DefiLlama | Pragmatic daily monitoring / component nowcast | **E**, 581 observations returned; earliest 2025-04-20, missing older dates and chain coverage limits |
| [x] C05 | Unique depositor addresses and depositor concentration | Dependence on large integrators | **V**, Ethereum Q3; 22,219 depositor addresses, top 10 approximately 66.03% of outbound value; not 22,219 human customers |
| [x] C06 | Monthly returning depositor cohorts | Repeat protocol usage | **V**, Ethereum Q3; August/September approximately 19.73% / 17.43%; financial predictive value unproven |
| [x] C07 | Requested finality / fast-transfer flag | Fast usage mix and fee-demand context | **V**, request field decoded; about 61.75% request-fast share is not the actual fee-paying share |
| [ ] C08 | Actual fee-paying frequency and matched fee bps by route | Forecast fee intensity as well as volume | **E**, destination positive-fee events known; join source and destination by version-correct message identifier before computing route rates |
| [ ] C09 | Message completions, outstanding transfers, delays and failures | Operational quality / adoption risk | **P**, public Dune SQL examples found; nonce vs message-hash differences and failed/retried transfers need validation |
| [ ] C10 | EURC and future supported non-USDC CCTP assets / versions | Avoid USDC-only undercount and historical version errors | **P**, current docs include an expanded asset perimeter; do not impose today's support on past quarters |
| [ ] C11 | Contract upgrades, fees/fee controllers, caps and recipient changes | Structural breaks in monetization | **P/E**, verified source and current adapter available; build effective-date ledger |
| [ ] C12 | Transaction-by-transaction direct vs aggregator reconciliation on material chains | Establish trusted fee history before model claims | **Open**: one-quarter aggregate comparison done; matched reconciliation and other quarters/chains not done |

**Extraction mechanics.** Authenticate contract, implementation ABI and activation block. Find first block at/after quarter start and first at/after next quarter start; query the half-open UTC interval with bounded log requests. Deduplicate by chain, transaction hash and log index; reject removed logs; use integer token units until reporting. On Ethereum, the verified fee event has two indexed address fields and non-indexed `amount` and `feeCollected`. Decode according to the historical deployed ABI, filter the native USDC token, and sum `feeCollected / 10^6`. `maxFee` on a source message is a ceiling, not a collected fee. Source outgoing volume and destination incoming fees are different populations; dividing one by the other is not a valid fee rate.

Ethereum identities already used: native USDC `0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48`; CCTP V2 TokenMessenger `0x28b5a0e9c621a5badaa536219b3a228c8168cf5d`. Use the official registry for other chains and dates. Our implementation-specific source-event signature includes `minFinalityThreshold` and `hookData`; copying a generic ABI or an old Dune query without checking it can silently misdecode fields.

## E. USYC: observable fund economics, incomplete company-revenue mapping

Sources: [Circle USYC](https://www.circle.com/usyc), [contract documentation](https://developers.circle.com/tokenized/usyc/smart-contracts), [public reports API](https://usyc.hashnote.com/api/price-reports), [DefiLlama revenue series](https://api.llama.fi/summary/fees/circle-usyc?dataType=dailyRevenue), [Dune USYC](https://dune.com/markets/rwa/usyc), [RWA.xyz treasuries](https://app.rwa-xyz.com/treasuries).

| Check / ID | Data and extraction route | Research use | Status and next check |
| --- | --- | --- | --- |
| [x] U01 | Reporter NAV/share price, share supply and timestamps | Fund-size and yield reconstruction | **V**, 438 chain reports Jan 2025–Sep 2026 in existing extraction; authenticate fund-wide reporter scope rather than add every chain wrapper |
| [x] U02 | Fee shares × relevant NAV/share price | Estimate observable performance-fee economics | **V**, reconstructed amounts reconcile with 10% of reported gross income within rounding in tested reports; not proof of identical GAAP recognition |
| [x] U03 | Daily/quarterly fee aggregation by observation timestamp | Component estimate and lag test | **V**, Q3 2026 approximately $2.546m; total services revenue $19.587m, so this is only part of the category |
| [ ] U04 | Latest reports API, including `fee`, `price`, `totalSupply`, transaction hash | Low-cost refresh / raw-chain cross-reference | **E**, current request returns 45 reports, 2026-09-17–2026-11-20; do not treat it as full historical coverage |
| [ ] U05 | Mint/burn/redemption flows and subscription/redemption fees | Fund growth and transaction-fee component | **P**, distinguish shares from dollars, pricing timing, fee rates and customer exemptions |
| [ ] U06 | USYC holder concentration, lending collateral and chain exposure | Distribution / fund-risk context | **P**, Dune / RWA / protocol balances; holder count ≠ investor count and escrow can obscure beneficial holdings |
| [ ] U07 | Yield from NAV changes and underlying portfolio / benchmark spread | Fee-run-rate scenarios | **E/P**, use fee policy and aligned intervals; avoid counting NAV appreciation and fee shares twice |
| [ ] U08 | Fund fees → Circle contractual entitlement → services recognized | Complete accounting bridge | **Open**, observable fund fees alone do not identify every revenue-recognition adjustment or services contract |

USYC's current public API field `fee` must not be assumed to be dollars simply because it is numeric. Existing chain reconstruction handles fee shares and NAV explicitly. Reserve Fund yield supporting USDC and the USYC investment fund are different datasets and businesses.

## F. Arc chain and ARC token: separate activity from corporate entitlement

Sources: [Arc official site](https://www.arc.io/), [Arc docs](https://docs.arc.io/), [Dune's Arc coverage announcement](https://dune.com/blog/arc-circle-live-on-dune), [DefiLlama Arc](https://defillama.com/chain/arc), [existing activity comparison](../stage5/arc_activity/activity_results.json), Circle filings/announcements for token terms.

| Check / ID | Data and extraction route | Research use | Status and next check |
| --- | --- | --- | --- |
| [ ] A01 | Mainnet blocks, transactions, successful transactions and active addresses | Adoption dashboard | **P**, public chain/Dune access identified; certify chain ID and mainnet start before history comparisons |
| [ ] A02 | USDC native gas paid, proposer/validator receipts and any burn | Potential transaction/rewards economics | **P**, need native-gas chain semantics and historical fee-distribution rules; all chain gas is not Circle revenue |
| [ ] A03 | Circle-operated validator share and net economic entitlement | Possible Circle rewards component | **N**, ownership, reward rights and costs not comprehensively authenticated |
| [x] A04 | Arc spot DEX volume against other chains, same 30-day window | Adoption/context chart | **V** for prior dated provider comparison: Oct 22–Nov 20 mean daily Arc approximately $19.43m; Ethereum $1.878bn, Solana $1.649bn, Base $1.089bn. Does not prove token fundraising demand |
| [ ] A05 | Bridged flows, chain USDC stock and liquidity | Chain funding versus actual usage | **E**, prior 30-day bridge volume approximately $4.443bn; bridge flow differs from DEX volume and company revenue |
| [ ] A06 | Application/protocol fees on Arc | Ecosystem monetization context | **E, quarantined from Circle earnings**: API returned data but includes independent apps; not an Arc gas or Circle-revenue total |
| [ ] A07 | Authenticated official ARC genesis, issuer treasury, vesting/lock contracts and transfers | Potential delivery/supply-event monitor | **N/P**, no authenticated contract-and-investor address registry in this project. Do not use a matching ticker or presumed treasury |
| [ ] A08 | Known ARC sale consideration: attributable stablecoin receipts and delivery to authenticated buyers | Corroborate a disclosed sale | **N**, future receipts could be off-chain; transfers can be vesting, custody or grants. Transfer alone cannot reveal sale price, side terms or revenue recognition |
| [ ] A09 | Delivered ARC / vesting milestone × disclosed contract accounting | Event-dependent deferred-revenue scenario | **Off-chain-led**, require actual sale agreement, consideration and recognition conditions. Remaining approximately $60.4m recognized next quarter remains the user's working assumption, not a chain-confirmed outcome |

**New issue to resolve:** the fresh Arc DEX and application-fee API histories begin **2026-06-03**, earlier than the September mainnet launch date used in the prior research. These histories must be checked for testnet, adapter backfill or mislabeled perimeter before use as a mainnet time series. Do not chart all earlier dates as established mainnet business activity. The previous Oct–Nov comparison is preserved as a dated provider observation, with this new perimeter caveat attached.

## G. Other Circle infrastructure: promising additions, not validated revenue inputs

Sources: [Gateway](https://www.circle.com/gateway), [Gateway contracts](https://developers.circle.com/gateway/references/contract-addresses), [interfaces/events](https://developers.circle.com/gateway/references/contract-interfaces-and-events), [xReserve](https://www.circle.com/xreserve), [Paymaster](https://www.circle.com/paymaster), [Circle documentation index](https://developers.circle.com/llms.txt).

| Check / ID | Data and extraction route | Research use | Status and next check |
| --- | --- | --- | --- |
| [ ] I01 | Gateway deposits, balances, burns/mints and withdrawals | Unified-liquidity adoption and supply reconciliation | **P**, official contract and event pages inspected; need production/version/asset registry and cross-chain deduplication |
| [ ] I02 | Gateway realized fees, refunds and gas reimbursements | Candidate transaction-revenue component | **P/N**, fee quote is not settlement and gross gas reimbursement is not automatically net revenue |
| [ ] I03 | xReserve collateral balances, deposits, withdrawals and partner-issued USDC-backed supply | Adoption and collateral backing | **P**, official product describes USDC collateral plus partner-issued tokens; do not add partner supply to original USDC reserves |
| [ ] I04 | xReserve fee receipts and contract-specific entitlement | Candidate infrastructure monetization | **P/N**, validate actual pricing and recognized entitlement before linking volume to revenue |
| [ ] I05 | Paymaster-sponsored operations, USDC collected, native gas spent and markup | Potential measurable service-fee / cost bridge | **P**, public pricing/flow reviewed; exact contracts, exceptions and matched costs still need extraction. Gross USDC charge contains gas funding |
| [ ] I06 | StableFX / institutional FX on-chain settlement, pair, notional and counterparties where public | FX adoption and potential fee component | **P**, docs index identifies product; execution/settlement amounts need privacy and fee-term checks; notional ≠ earned spread |
| [ ] I07 | Wallets / smart-contract-platform deployments and attributed transactions | Infrastructure use proxy | **P/N**, many clients' accounts are not publicly attributable; no complete paying-subscriber or contract-price ledger |
| [ ] I08 | CPN payments with publicly attributable settlement addresses | Payments-adoption context | **N/P**, public-chain payment does not identify CPN membership, bank leg or Circle fee; network-wide complete fee data not established |
| [ ] I09 | cirBTC supply, mints/burns and reserve proof | Additional product perimeter / backing risk | **P**, current official docs identify 1:1 BTC backing and reserve proof. No extracted history or validated company fee model; BTC backing does not imply Treasury reserve interest |

## H. Market, liquidity and risk context

| Check / ID | Data and extraction route | Research use | Status and next check |
| --- | --- | --- | --- |
| [x] M01 | Total stablecoin USD value and USDC share: daily DefiLlama histories | Market position and proposed services factor | **V** for seven-quarter factor construction; total sums USD-converted peg categories. Market share depends on the selected provider universe |
| [x] M02 | BTC daily price joined to stablecoin factors | Proposed services predictor | **V** for extraction/regression; BTC price is market data, not an on-chain balance. Weak predictive result retained |
| [ ] M03 | USDC DEX liquidity, volumes, pool concentration, lending utilization and borrow rates | Peg, liquidity and adoption risks | **P**, contract / Dune / protocol APIs; not direct Circle transaction revenue |
| [ ] M04 | Tokenized Treasury competitor AUM / stablecoin competitors and chain shares | Competitive and rate-cycle context | **P**, Dune RWA, RWA.xyz, DefiLlama; harmonize token wrappers, fund-wide NAV and market universe |
| [ ] M05 | Authenticated Circle treasury / validator token balances, rewards and valuation prices | Possible rewards revenue / non-operating exposure | **N/P**, ownership and accounting perimeter not complete; do not infer corporate assets from a generic address label |

This inventory contains **69 numbered metrics/questions**. Closely related rows can share one extraction. Some are explicit public-data limitations, not obtainable data. Prioritize economic materiality and a clean audit over collecting every candidate at once.

## Provider check: what we actually established

| Provider | Useful coverage | Access verified here | Practical use / caveat |
| --- | --- | --- | --- |
| DefiLlama | USDC/EURC history, total stablecoins, CCTP/USYC fees, Arc adoption | **Live no-key downloads succeeded**; raw responses, SHA-256 and schemas archived | Best core dashboard feed. Inspect adapters and definitions. API `dailyRevenue` is a provider classification, not issuer GAAP revenue |
| Dune | Issuer/token stablecoin pages; USYC/RWA data; Arc raw data; community CCTP SQL | Public pages/SQL reviewed; a no-key query-results API request returned **401**. No Dune query was executed in this audit | Excellent SQL workbench and reproducible methods appendix; API/scheduling use depends on account and credits. Do not promise free unlimited history |
| Coin Metrics | Community asset supply/activity metrics | USDC metric catalog and three daily `SplyCur` observations downloaded without a key | Independent measurement candidate; `usdc` asset scope must be established before comparing it to all-chain Circle circulation |
| Visa / Allium | Adjusted vs gross stablecoin transfers and addresses | Public dashboard/methodology reviewed; programmatic historical download not tested | Useful adoption charts; adjusted-volume definitions matter; public website ≠ free Allium warehouse/API |
| Artemis | Supply, flows, exchanges, regions and use-case activity | Public dashboard and methodology reviewed; CSV control visible; export and API entitlement not tested | Good classification reference. Do not promise an automated feed or rehost data before verifying terms/entitlement |
| RWA.xyz | USYC and tokenized Treasury competitors, holders and flows | Public treasuries page reviewed; many fields show login restrictions; API not tested | Cross-check and competitor context; distinguish public preview from historical export entitlement |
| Direct RPC / chain explorer | Source-of-truth contract events, balances and implementation histories | Ethereum historical extraction succeeded in earlier stages | Best audit sample; free providers vary in archive/log limits. Explorer labels are not ownership proof |
| Circle docs / SEC / fund disclosures | Contract registries, pricing, reserve yields, agreements and recognition policies | Existing primary documents plus current product docs | Necessary off-chain complement. There is no sound EPS estimate using blockchain data alone |

### Specific Dune references and how to use them

- [USDC market page](https://dune.com/markets/stablecoins/usdc), [Circle issuer page](https://dune.com/markets/stablecoins/circle), [USYC page](https://dune.com/markets/rwa/usyc) and [RWA data description](https://dune.com/data/rwa): useful comparative dashboards and data schemas. Their curated token universe can differ from DefiLlama's, and normalized USDC variants need native/wrapped checks.
- [Arc coverage announcement](https://dune.com/blog/arc-circle-live-on-dune): establishes a candidate raw-data source; it does not establish that our own required full-history query has run.
- [Public Arc CCTP inflows SQL, query 9169111](https://dune.com/queries/9169111): raw-log route example reviewed, not executed. Check its historical contract ABI, `burnToken` filter, domain interpretation, mainnet dates and included chains before reuse. An “all chains” title is not proof of all-chain coverage.
- [Arc launch net inflows query 8749343](https://dune.com/queries/8749343): combines CCTP/Gateway activity; use as a decomposition reference, not an independent revenue series or additional supply.
- [CCTP outstanding-transfer query 9062979](https://dune.com/queries/9062979): decoded-table candidate. Review V1/V2 message identifiers, chain scope and raw-unit threshold before reuse; 1,000,000 raw USDC units is $1, not $1m.
- [Dune latest-results API](https://docs.dune.com/api-reference/executions/endpoint/get-query-result): result retrieval is separate from execution. Store execution timestamp, query revision, covered blocks and pagination; fetching cached results does not guarantee fresh calculations.

No Dune credentials were supplied or recovered. Query IDs are source references, not evidence that results have been independently verified.

## Minimum extraction contract for every series

Store the source URL, contract/asset/chain/version, exact query or adapter commit, raw response, retrieval timestamp and hash. Record the source's observation time, the first established public-by time, and whether old values can be revised. Keep raw units, token decimals, USD conversion, stock/flow classification, timezone and aggregation rule explicit.

For chain work, preserve block numbers/hashes, finality rule, address/role activation histories, transaction hashes and log indexes. Assert unique events, complete block ranges and sensible units; a successful HTTP response alone does not validate the economic series. For provider data, check expected dates, duplicated timestamps, schema changes, missing chain components and currency fields. Today's partial observation must be labeled or excluded from completed-day averages.

For accounting, map **activity → chargeable service → actual fee → Circle entitlement → recognition period → financial line**. Any missing link makes the series context or a scenario input rather than observed company revenue. Keep chain fees, protocol fees, application fees and company revenue distinct.

## Off-chain data still required for EPS

- USDC reserve allocation, fund seven-day yields, cash/deposit yield and euro rates/FX; these are not observable from USDC token transfers.
- Distribution agreements, partner economics and off-chain eligible balances.
- Services contract prices, one-time milestones, customer exemptions and subscription billing.
- ARC sale agreements, consideration, refunds/vesting/performance obligations and deferred-revenue recognition.
- Compensation/SBC, operating expenses, investment/other income, taxes, minority interests and common-share earnings adjustments.
- Basic/diluted weighted-average shares, award dilution and loss-period antidilution.

Blockchain data helps estimate important components; these other schedules are necessary before calling the output diluted EPS.

## Recommended order after this checklist

1. Resolve the **$5,256 CCTP discrepancy** using matched events and the archived adapter version; then extend Ethereum across feasible earlier fee-bearing quarters. Explicitly retain unavailable periods. Expand to a second material chain only after one history reconciles.
2. Add **EURC's separate reserve contribution**, and authenticate raw-supply adjustments. The existing calibrated reserve model already works well; quantify whether the extra detail changes accuracy materially.
3. Implement one bounded new monetization audit, preferably **Paymaster or Gateway**, if deployed production contracts and fee rights can be authenticated. Do not launch nine infrastructure data projects simultaneously.
4. Build the website dashboard using the verified free feeds and visible audit coverage, then complete the EPS bridge. Preserve dated forecast snapshots for future genuine out-of-sample evaluation.

Reproducible new access checks are in [probe_public_sources.py](probe_public_sources.py); current pointer [latest_access_check.json](latest_access_check.json); coverage calculation [summarize_access_checks.py](summarize_access_checks.py); [website integration plan](Website_Dashboard_Plan.md). These new downloads do **not** replace the prior seven-quarter ledger or the dated 21 November forecasts.
