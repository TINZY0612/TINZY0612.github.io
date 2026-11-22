# Circle on-chain research priorities and ARC working assumptions

Recorded 21 November 2026 following the user's instruction to keep the paper focused on demonstrating on-chain research skills applied to equity analysis.

## ARC sales and the working recognition case

The reviewed official ARC token page and contract registry do not establish an issuer-authenticated ARC token contract, issuance chain, treasury wallet, investor/escrow mapping or a comprehensive public sales tracker. This is an identification limitation, not proof that no relevant ledger or transaction data exists. Future confirmed identity could enable transfer tracking; it would still not make every transfer a sale or accounting revenue. [Official token page](https://www.arc.io/arc-token-whitepaper), [official registry](https://docs.arc.io/arc/references/contract-addresses).

Use issuer announcements, 8-Ks, quarterly filings and earnings guidance for new sales until a sale-to-chain reconciliation is available. Do not infer no actual sales from no observed authenticated address. The forecast assumption is zero additional unannounced sales.

The user-directed case recognizes all approximately $60.4m remaining presale deferred revenue in Q4 2026, leaving zero from that existing balance thereafter. This is explicitly a timing assumption. The financial filing does not promise full recognition next quarter. Assuming no incremental distribution cost, the release adds $60.4m to revenue and RLDC before other costs/taxes; it is not a claim of $60.4m after-tax profit or new cash receipts. Future staking and other ARC activities remain distinct from token sales. [Q3 filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm).

Preserve the earlier Q4 guidance-derived benchmark, which assumed no additional ARC recognition. The new case is held in `results/2026-11-21_Q4_ARC_user_scenario.json`. Keeping other assumptions unchanged adds $60.4m to that benchmark's Q4 other-revenue midpoint, from $37.529m to $97.929m. It therefore sits above the published annual-guidance benchmark; it is not implied by management guidance. The old forecast and original workbooks are unchanged. [November call, page 9](https://s206.q4cdn.com/265218871/files/doc_earnings/2026/q3/transcript/Q326-Earnings-Transcript.pdf#page=9).

## The paper already uses on-chain evidence

The reserve model uses chain-derived USDC supply, with direct historical Ethereum contract-supply checks. CCTP fee observations and an issuer-report-to-Ethereum USYC fee-mint verification add direct transaction-level evidence. Interest-rate data, reserve-fund yields, contractual economics and financial actuals are off-chain complements. Explain the hybrid pipeline honestly rather than describing the entire financial model as directly observable on-chain.

## Additional analyses ranked for this paper

| Priority | Analysis not yet completed | On-chain inputs | Equity-research use | Important limitation |
| --- | --- | --- | --- | --- |
| 1 | Gross USDC issuance and retirement flow decomposition | Official native-token mint/burn events; CCTP messages; identified issuer/system transactions | Explain supply changes and test whether flows help forecast the future reserve base | Exclude cross-chain burn/mint pairs and internal rebalancing; non-CCTP burns are not automatically fiat redemptions or chargeable customers |
| 2 | Daily USYC fund scale, flows and fee reconciliation | Authenticated token supply, oracle price, fund reports and performance-fee mints | Build an observable subscription/services component from fund activity | Prevent wrapper/native double-counting; API coverage and accounting recognition still need reconciliation |
| 3 | CCTP route and fee composition | Message identities, source/destination domains, transferred amounts and actual fees | Explain how adoption translates into monetization and whether paid-route mix changes | Extends the existing aggregate fee work; deduplicate source/destination events and preserve coverage limits |
| 4 | USDC native-chain distribution and growth concentration | Native USDC supply by chain and cross-chain movements | Assess which ecosystems drive growth and whether apparent expansion is new supply or migration | A chain's growth alone is not global USDC growth; raw chain sums can double-count bridged representations |
| 5 | Holder activity, concentration and retention | Transfers, balance snapshots and documented address/entity tags | Assess whether demand is broadening or concentrated, and support durability/risk analysis | Addresses are not users; exclude internal movements where possible; exchange custody hides beneficial owners |
| Optional | USDC liquidity and peg stress | DEX pool balances, trades, depth and slippage under defined trade sizes | Support redemption/liquidity risk scenarios | Risk indicator rather than a direct quarterly revenue formula; pool coverage and price benchmark matter |

Native USDC contracts can be authenticated against [Circle's registry](https://developers.circle.com/stablecoins/usdc-contract-addresses). CCTP message/contract interfaces support transfer attribution and fee extraction: [official interfaces](https://developers.circle.com/cctp/references/contract-interfaces). USYC's official overview identifies token-price/oracle transparency: [USYC documentation](https://developers.circle.com/tokenized/usyc/overview). The [Visa on-chain analytics dashboard](https://visaonchainanalytics.com/) offers a reference for supply, transaction and address metrics; reviewed dashboard availability does not establish bulk historical API access.

Labeled exchange and DeFi balances can add context, but they cannot establish Circle's contractual on-platform balances or partner payout rates. Do not claim an exact Coinbase/Binance distribution-cost reconstruction from public wallet labels alone.

## Recommended scope

Keep the existing reserve-income forecast as the central result. Add the gross-flow decomposition on one flagship chain and a deeper USYC fee/AUM build, then use CCTP route composition as a shorter monetization case. Native-chain mix can reuse the supply work. Holder and liquidity analyses are optional if they answer a concrete investment-risk question.

For each module show the business question, authenticated contracts, event extraction, unit/time alignment, cleaning and deduplication, financial bridge, and out-of-period or publication-filtered evaluation. Preserve the difference between observed activity, forecast assumptions and unavailable private terms. Do not append unrelated metrics solely to increase the count of on-chain charts.
