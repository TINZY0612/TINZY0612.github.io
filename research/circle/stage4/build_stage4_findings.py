"""Build the local evidence timeline and readable Stage 4 deliverable."""
import json
import hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'
def read(n):return json.loads((OUT/n).read_text())
model=read('other_revenue_model.json');chain=read('arc_chain_check.json');fees=read('product_fee_analysis.json')
forecast_path=OUT/'2026-11-21_Q4_other_revenue_forecast.json'
forecast_record={'recorded_as_of':'2026-11-21','time_zone':'Asia/Kuala_Lumpur','forecast':fees['q4_guidance_based_forecast'],
 'source_pdf_sha256':hashlib.sha256((ROOT/'raw/q3_2026_transcript.pdf').read_bytes()).hexdigest(),
 'revision_policy':'Keep this dated record. Later information requires a separately dated forecast; actual results enter scoring only.'}
if forecast_path.exists():
    assert json.loads(forecast_path.read_text())==forecast_record,'Dated forecast would change; write a new vintage instead.'
else:forecast_path.write_text(json.dumps(forecast_record,indent=2),encoding='utf8')
mix=json.loads((ROOT/'revenue_mix.json').read_text())
urls={
 'may':'https://www.sec.gov/Archives/edgar/data/1876042/000187604226000148/crcl-20260511.htm',
 'july':'https://www.sec.gov/Archives/edgar/data/1876042/000187604226000205/crcl-20260629.htm',
 'q1release':'https://www.circle.com/pressroom/circle-reports-first-quarter-2026-results',
 'q2':'https://www.sec.gov/Archives/edgar/data/1876042/000187604226000248/crcl-20260630.htm',
 'q3':'https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm',
 'q2call':'https://s206.q4cdn.com/265218871/files/doc_earnings/2026/q2/transcript/Q226-Earnings-Transcript.pdf',
 'q3call':'https://s206.q4cdn.com/265218871/files/doc_earnings/2026/q3/transcript/Q326-Earnings-Transcript.pdf',
 'schedule':'https://www.arc.io/blog/arc-mainnet-goes-live-on-september-16-2026',
 'launch':'https://www.circle.com/pressroom/circle-launches-arc-mainnet-an-economic-operating-system-for-the-internet',
 'whitepaper':'https://www.arc.io/arc-token-whitepaper',
 'registry':'https://docs.arc.network/arc/references/contract-addresses',
 'usycapi':'https://developers.circle.com/tokenized/usyc/web2-apis',
 'usyccontracts':'https://developers.circle.com/tokenized/usyc/smart-contracts',
 'usyccode':'https://github.com/DefiLlama/dimension-adapters/blob/master/fees/hashnote-usyc/index.ts',
 'cctpcode':'https://github.com/DefiLlama/dimension-adapters/blob/master/fees/cctp/index.ts',
}
timeline=[
 {'event_date':'2026-05-08','public_by':'2026-05-11','evidence':'signed presale agreements disclosed in 8-K','amount_usd_million':222,'tokens_million':740,'price_usd':.30,'source':urls['may'],'q3_pre_earnings_eligible':True},
 {'event_date':'2026-06-30','public_by':'2026-07-02','evidence':'June 29-30 second closing: 67.5m additional ARC at $0.30, $20.25m, disclosed in original July 2 8-K','additional_amount_usd_million':20.25,'source':urls['july'],'q3_pre_earnings_eligible':True},
 {'event_date':'2026-06-30','public_by':'2026-08-05','evidence':'quarterly agreement totals: 807.5m ARC at $0.30; rounded consideration $242.2m, Q2 cash received $222m; initially deferred','amount_usd_million':242.2,'source':urls['q2'],'q3_pre_earnings_eligible':True},
 {'event_date':'2026-08-05','public_by':'2026-08-05','evidence':'FY2026 ~75% milestone/revenue expectation and $180m included in guidance; no exact Q3 recognition commitment','source':urls['q2call'],'locator':'page 9','q3_pre_earnings_eligible':True},
 {'event_date':'2026-08-05','public_by':'2026-08-05','evidence':'September 16 mainnet launch scheduled','source':urls['schedule'],'q3_pre_earnings_eligible':True},
 {'event_date':'2026-09-16','public_by':'2026-09-16','evidence':'Circle announces mainnet launch AND completed 10bn ARC genesis mint that week; distinguishes mint from a commitment to public token launch; supports a milestone scenario without an exact GAAP progress fraction','source':urls['launch'],'q3_pre_earnings_eligible':True},
 {'event_date':'2026-09-14','public_by':'2026-11-04','evidence':'Exact September 14 mint date and subsequent investor distribution/escrow established in Q3 filing; mint completion was already announced September 16','source':urls['q3'],'q3_pre_earnings_eligible':False},
 {'event_date':'2026-09-30','public_by':'2026-11-04','evidence':'Q3 ARC revenue $181.8m and remaining ARC deferred balance about $60.4m; scoring only for historical test','source':urls['q3'],'q3_pre_earnings_eligible':False},
 {'event_date':'2026-11-04','public_by':'2026-11-04','evidence':'FY other revenue guide $310m-$330m maintained; ordinary products $130m-$150m, Q4 expected to improve; usable for forward Q4 projection','source':urls['q3call'],'locator':'page 9','q3_pre_earnings_eligible':False},
]
(OUT/'arc_evidence_timeline.json').write_text(json.dumps({'as_of':'2026-11-21','historical_cutoff':'2026-11-03','events':timeline},indent=2),encoding='utf8')
(OUT/'explorer_observations.json').write_text(json.dumps({'observed_date':'2026-11-21','method':'read-only browser UI','url':'https://explorer.arc.io/tokens?q=ARC','scope':'First 20 filtered token listings only; Next button available','result':'Ambiguous third-party token names; no issuer-authenticated ARC mapping established on the reviewed page','not_claimed':'No claim that all listings or all chains were searched','official_registry':urls['registry'],'official_token_page':urls['whitepaper']},indent=2),encoding='utf8')

def table(headers,rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+'\n'.join('| '+' | '.join(str(v) for v in row)+' |' for row in rows)
mix_table=table(['Quarter','Reserve income, $m','Other operating revenue, $m','Reserve share'],[[x['period'],f"{x['reserve_income_usd_million']:.3f}",f"{x['other_revenue_usd_million']:.3f}",f"{100*x['reserve_income_share']:.2f}%"] for x in mix['quarterly_rows']])
category_table=table(['Quarter','Subscription/services','Transaction','Other category','Total other revenue'],[[p,*[f"{v:.3f}" for v in vals]] for p,vals in [
 ('2025Q1*',[18.711,1.626,.325,20.662]),('2025Q2',[17.784,5.825,.195,23.804]),('2025Q3',[23.594,4.664,.260,28.518]),('2025Q4†',[24.694,12.220,-.078,36.836]),('2026Q1',[34.861,6.730,.034,41.625]),('2026Q2',[28.156,5.330,.096,33.582]),('2026Q3',[19.587,5.335,182.342,207.264])]])
scenario_table=table(['Q3 case','Ordinary estimate','ARC estimate','Total other estimate','Actual','Error'],[
 ['Flat ordinary, no ARC','33.582','0.000','33.582','207.264','-83.80%'],
 ['Flat ordinary + annual ARC guide allocated to Q3','33.582','180.000','213.582','207.264','+3.05%'],
 ['Same ordinary + 75% of rounded consideration','33.582','181.650','215.232','207.264','+3.84%'],
 ['Repeat prior aggregate growth + $180m ARC','27.093','180.000','207.093','207.264','-0.08%'],
 ['Repeat category growth + $180m ARC','27.233','180.000','207.233','207.264','-0.02%']])
fees_table=table(['Quarter','USYC performance fees, $m','CCTP fees, $m','Sum / ordinary other revenue'],[[x['period'],f"{x['usyc_performance_fees_usd']/1e6:.3f}",f"{x['cctp_protocol_fees_usd']/1e6:.3f}",f"{100*x['tracked_fees_share_ordinary_other']:.2f}%"] for x in fees['quarterly_fee_observations']])
text=f"""# Circle Stage 4: other revenue, ARC milestones and on-chain fee evidence

Research date: 21 November 2026. All money is USD millions unless stated otherwise. The core finding is that ARC was partly predictable from earlier company disclosures: the August 5 earnings call already included about $180m of ARC revenue in annual guidance. Exact quarterly recognition still needed a timing assumption. The ordinary business lines remain substantially less predictable than reserve income.

This is a retrospective investigation with outcomes already known. Publication dates constrain financial inputs, but current chain/API histories are not archived historical vintages. The new Q4 projection below is a forward, guidance-based range as of the research date. No claim of beating analyst consensus is made.

## 1. What we are forecasting

“Other revenue” here means the operating revenue reported alongside reserve income. It does not mean non-operating “Other income (expense), net.” Within operating other revenue, Circle reports subscription/services, transactions and a smaller Other category. ARC recognition sits in that last category. A current-quarter token transfer is not automatically a current-quarter sale or accounting revenue.

{category_table}

*Q1 2025 comparable categories are derived from the original August 2025 six-month disclosure less Q2, so this split was not available before August 12. The IPO original instead reported integration services 16.331, transaction services 0.108 and other 4.223. A May 2026 comparative later reallocates another 1.223 from subscription to transactions. Each version is preserved in the ledger and old forecasts use eligible versions. †Q4 is the annual statement less original nine-month figures; the negative 0.078 Other adjustment is retained. These categories mix upfront, ongoing and usage-related fees; “ordinary” below means excluding identified ARC, not all contractually recurring revenue. [Original financial source ledger](results/other_revenue_model.json).

## 2. ARC: a disclosed sale followed by recognition milestones

On May 11, Circle disclosed agreements for 740m ARC at $0.30, or $222m. A **July 2 8-K** announced a June 29-30 second closing of another 67.5m ARC for $20.25m, so the expanded sale was public even before the Q2 results. By its August 5 Q2 report, agreements covered 807.5m tokens and approximately $242.2m consideration; $222m had been received in Q2 and the balance was receivable. Cash initially entered deferred revenue. Rounded token counts need not multiply to the last disclosed decimal of proceeds. [May 8-K]({urls['may']}), [July second-closing 8-K]({urls['july']}), [Q2 filing]({urls['q2']}).

The decisive earlier evidence is **page 9 of the August 5 call**: management expected about 75% of milestones/revenue in FY2026 and included $180m in its revised other-revenue guidance. It also guided $130m-$150m from other products and described a softer integration pipeline. This was public before the November 3 historical cutoff. It was annual guidance, not an explicit $180m Q3 commitment. The same call said the recognition would flow through to earnings. [Q2 transcript, page 9]({urls['q2call']}#page=9).

The September 16 mainnet launch was scheduled August 5 and publicly confirmed on launch day. **That September 16 announcement also disclosed that the 10bn ARC genesis mint had been completed that week.** Both events were therefore usable before Q3 earnings. They strengthened a Q3 recognition scenario without establishing exact accounting progress or investor delivery. The announcement distinguishes technical minting from a commitment to public token launch and points to a possible PoS transition in 2027. [Launch schedule]({urls['schedule']}), [launch and mint confirmation]({urls['launch']}).

The subsequent filing supplies the precise September 14 mint date, investor delivery/escrow and 181.8 of Q3 recognition. The obligation also includes functionality development toward Proof of Stake. The remaining ARC deferred balance is about 60.4; total company deferred revenue is 61.794. These are different balances. The precise date, delivery details and recognized amount are earnings-day outcome evidence; mint completion itself was already public. [Q3 filing, Notes 2 and 11]({urls['q3']}).

The practical model is: **recognized ARC revenue this quarter = cumulative sale consideration × cumulative recognized progress, less revenue recognized previously**, subject to the actual accounting policy and any new agreements/refunds. Use management's announced amount when available. If quarterly progress is unobserved, retain milestone scenarios. Do not substitute the current token market price for the $0.30 historical contract price.

{scenario_table}

The $180m and 75% cases assume the relevant annual milestone recognition occurs in Q3. The 75% × 242.2 = 181.65 ARC estimate is only 0.15 below the eventual 181.8, but neither rounded guidance nor a launch date establishes precise quarterly recognition. A 0-to-242.2 range would have bounded the existing presale before recognition; it is a timing sensitivity, not a probability interval or a cap on future new sales.

The apparently excellent category-growth total is **error cancellation**: ordinary revenue is estimated 1.769 too high and ARC 1.8 too low. Ordinary revenue alone is still 6.95% too high. It should not be presented as a validated 0.02%-accuracy model.

ARC presales are finite, milestone-dependent revenue from a particular contract pool. Circle treats token activity as operating revenue, and future sales can occur; that does not make this presale a fixed quarterly annuity. Keep it outside the ordinary run rate.

## 3. Did we establish ARC transfer tracking?

**Public chain access works; the issuer-token link remains unverified.** The read-only Arc RPC check authenticated chain ID 5042 and made successful calls to the official USDC contract. A bounded scan of UTC September 14 covered blocks {chain['first_block']:,}–{chain['last_block']:,}, {chain['block_count']:,} blocks, and returned {chain['zero_address_transfer_events']:,} zero-address Transfer events. It found raw 10bn-equivalent amounts across {chain['distinct_candidate_addresses']} distinct candidate addresses. Such amounts and symbols do not authenticate Circle ARC. The 500-block control matched 48 logs at a second provider. [Saved chain checks](results/arc_chain_check.json).

No official ARC contract/investor/escrow address mapping was established from the reviewed registry, official token page or first 20 explorer search results. This is not an exhaustive search of every chain or token listing; in particular, the ARC asset's issuance chain itself is not authenticated here. The current token page says ARC has not launched; the September announcement explicitly distinguishes technical minting from public token launch. Neither source provides the authenticated address mapping needed here. Arc's gas token is USDC. [Contract registry]({urls['registry']}), [current token page]({urls['whitepaper']}), [mint/public-launch distinction]({urls['launch']}).

Once an official identity is published, a tracker can record mints, company-to-investor/escrow transfers, recipient labels, block times and unique transaction/log identifiers, then reconcile delivery to the relevant agreements. Deduplicate escrow moves and internal transfers; a locked token delivery can matter even without a liquid market. Staking, sales and incentive transfers require different treatment. A genesis allocation or native/nonstandard token may not emit ERC-20 Transfer logs, so this one-day scan cannot establish absence.

The November call distinguishes prospective staking rewards, discretionary token sales and ecosystem incentives. It says incentives can produce other revenue **with an equal other distribution cost**. Tracking them could improve reported revenue estimates without increasing retained revenue by the same amount. Staking needs the transition, token holdings, reward rate and valuation inputs; a token transfer alone does not supply these. These disclosures are usable prospectively, not as earlier Q3 inputs. [Q3 transcript, page 8]({urls['q3call']}#page=8).

## 4. The smaller product lines: real fee data, partial financial coverage

**USYC offers the strongest verified on-chain fee example in this stage.** Circle documents free current and historical price endpoints. The historical endpoint returned only 45 reports, September 17–November 20; tested limit/offset parameters returned the same payload. DefiLlama's public adapter reconstructs longer history from oracle/reporter logs and handles a July 2026 event-signature change. Its latest USYC adapter commit is November 17, after Q3 earnings, so present-day reconstructed history does not prove that this dashboard implementation was available before that earnings release. [Circle API documentation]({urls['usycapi']}), [USYC adapter]({urls['usyccode']}).

A November 20 issuer report records **18,580.964598 USYC fee shares** at **$1.144377646131036353**, or **$21,263.64053**. We retrieved the matching successful Ethereum receipt and verified a zero-address mint of exactly those fee shares from Circle's officially listed USYC contract. Gross yield is 141,012.38 interest + 71,624.0253 embedded income = 212,636.4053; the fee is 10%. The same arithmetic holds across the 45 returned reports. Omitting embedded income would produce a wrong effective fee rate. [Official USYC contract mapping]({urls['usyccontracts']}), [sample transaction](https://etherscan.io/tx/{fees['usyc_fee_mint_control']['tx_hash']}), [saved unit and receipt checks](results/product_fee_analysis.json).

**CCTP:** current free quote API testing returned 1 basis point for Ethereum-to-Avalanche Fast Transfer and zero for Standard. This is one route today, not a universal historical price. The open adapter sums actual feeCollected amounts on supported contracts. Track actual fees, not all bridge volume times one fixed fee, and do not double-count source burns and destination mints. Fee switches, waivers and forwarding designs can change. [Official fee rules](https://developers.circle.com/cctp/concepts/fees), [CCTP adapter]({urls['cctpcode']}).

{fees_table}

These are observed protocol fee metrics from current histories, not audited reconciliations to Circle's revenue note. USYC uses **dailyRevenue** (performance fees), not **dailyFees** (gross fund yield). CCTP uses collected protocol fees. Their Q3 sum is about 3.021m, only 11.87% of ordinary other revenue of 25.464m. The balance cannot be filled by assuming all subscription/integration terms are on-chain. Each later quarter has 90/91/92 daily observations as appropriate; Q2 2025 CCTP starts April 20 and has only 72 days, with earlier days left missing. Fees may need accounting timing, scope, consolidation and incentive-cost adjustments.

Existing references are [DefiLlama USYC](https://defillama.com/protocol/circle-usyc) and [DefiLlama CCTP](https://defillama.com/protocol/circle-cctp). Their website display and search snippets can disagree about fees versus revenue; the downloaded API type and adapter definitions control this analysis. One Arc-only USYC supply call returned zero at the sampled block despite Ethereum/global product activity. A single-chain supply is therefore not a global AUM estimate. CPN, wallets and integration activity can reveal adoption, but no complete public transaction-to-recognized-revenue mapping was established here.

## 5. Accuracy result and retained-revenue impact

Flat prior-quarter other revenue has **28.59% MAPE** across six historical forecasts. Even after removing the identified ARC outcome for scoring, ordinary other revenue has **19.94% MAPE**. Day scaling does not fix this. On the common five-quarter sample, flat/day-scaled/repeated-aggregate-growth MAPEs are 31.67%/32.11%/30.48%. Category growth is available for only three quarters and is unstable when prior categories are zero/negative or classifications change. We do not tune weights to this small sample.

The plain $180m ARC timing case changes the original Q3 RLDC estimate from 285.060 to 465.060, versus 453.254 actual: error improves from -37.11% to +2.60%. Reserve and partner-cost estimates are otherwise unchanged. This is a conditional event adjustment, not a rebuilt partner distribution model. ARC's disclosed presale margin makes its omission economically important; future incentive distributions need matching cost entries.

The accepted ±0.5% to ±1% reserve-income tolerance is not demonstrated for other revenue. A strong reserve model and a good ARC event call can coexist with sizable errors in ordinary business revenue.

## 6. A forward Q4 2026 range recorded now

The November call maintained total FY other-revenue guidance at 310–330. Reported nine-month other revenue is 282.471, so the mechanically implied **Q4 total other revenue range is 27.529–47.529**, midpoint **37.529**. This is conditional on guidance being achieved, not an on-chain point estimate. The call also expects Q4 ordinary revenue to rise as integrations increase. [Q3 transcript, page 9]({urls['q3call']}#page=9).

The separate ordinary-product guide of 130–150 less nine-month ordinary revenue of 100.671 implies 29.329–49.329. Adding actual ARC recognition to that annual ordinary guide exceeds the total annual guide by 1.8 at both endpoints. Preserve this small inconsistency rather than silently adjust the company's rounded ranges. The total guide is the primary forward range here. Base case: no incremental presale recognition beyond the amount already in the annual guide. Remaining approximately 60.4 ARC deferred revenue is a milestone contingency, not automatic Q4 income. No future actual is stored. [Forward projection inputs](results/product_fee_analysis.json).

## 7. Reserve revenue shares retained for the equity report

{mix_table}

The Q3 2026 reserve share is 76.04% as reported, and 96.27% after removing the identified 181.8 ARC recognition from the denominator. That diagnostic does not exclude other ordinary revenues. Sources, dates and the FY2025 control remain in [the revenue mix register](revenue_mix.json).

## 8. Research decision and remaining work

Use three separate model blocks: the existing reserve-income model; an ordinary-product model with USYC/CCTP observed fee components and an explicitly uncertain integration/services residual; and an ARC contract/milestone schedule with timing scenarios. Archive announcements, guidance and data vintages from now on. A subsequent genuinely prospective earnings test should score this Q4 range without retrospectively changing it.

For ARC, require an issuer-authenticated chain/token mapping and investor or escrow attribution before interpreting transfers. For ordinary products, reconcile on-chain fees to reported categories and related costs before replacing the residual forecast. The detailed partner/platform distribution bridge remains unfinished; this stage keeps the prior bridge and tests ARC's effect. The final equity report, consensus comparison and valuation remain later deliverables.

Local analytical checks: 27/27 financial model, 22/22 chain-log controls and 25/25 product checks. An independent verification and SHA-256 manifest check are recorded in `results/stage4_verification.json`. Passing checks establishes calculation consistency and the stated sample controls, not future forecasting accuracy. Read [README](README.md) for reproduction and scope.
"""
(ROOT/'Stage_4_Findings.md').write_text(text,encoding='utf8')
print('Wrote Stage_4_Findings.md and evidence registers.')
