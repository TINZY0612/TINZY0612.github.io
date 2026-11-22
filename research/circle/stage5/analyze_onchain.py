"""Turn authenticated event logs into financial drivers and scoped activity metrics."""
import collections
import datetime as dt
from decimal import Decimal as D
import json
import gzip
from pathlib import Path
import statistics as st
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results';CIRCLE=ROOT.parent
def read(n):
    p=OUT/n
    return json.loads(p.read_text()) if p.exists() else json.loads(gzip.open(str(p)+'.gz','rb').read())
def save(n,x):(OUT/n).write_text(json.dumps(x,indent=2),encoding='utf8')
checks=[]
def ck(name,v):checks.append({'name':name,'passed':bool(v)})
def amount(log):return int(log['data'],16)
contracts=read('authenticated_contracts.json');bound=read('ethereum_boundaries.json')
flows=read('usdc_q3_2026_mint_burn_logs.json');control=read('usdc_flow_controls.json')
minters={v.lower() for v in contracts['minters'].values()}
def totals(logs):
    sums=collections.defaultdict(int);counts=collections.Counter()
    for x in logs:
        kind='mint' if x['topics'][0]==flows['mint_topic'] else 'burn'
        actor='0x'+x['topics'][1][-40:];group='cctp' if actor.lower() in minters else 'non_cctp'
        raw=amount(x);sums[kind]+=raw;sums[group+'_'+kind]+=raw;counts[group+'_'+kind]+=1
    return {'amounts_usd_million':{k:v/1e12 for k,v in sums.items()},'counts':dict(counts),'net_usd_million':(sums['mint']-sums['burn'])/1e12,
      'cctp_net_usd_million':(sums['cctp_mint']-sums['cctp_burn'])/1e12,'non_cctp_net_usd_million':(sums['non_cctp_mint']-sums['non_cctp_burn'])/1e12}
alltotals=totals(flows['logs'])
v2minter=contracts['minters']['v2_2026-10-01'].lower()
v2_burns=[x for x in flows['logs'] if x['topics'][0]==flows['burn_topic'] and ('0x'+x['topics'][1][-40:]).lower()==v2minter]
v2_mints=[x for x in flows['logs'] if x['topics'][0]==flows['mint_topic'] and ('0x'+x['topics'][1][-40:]).lower()==v2minter]
v2_control={'burn_amount_raw':sum(amount(x) for x in v2_burns),'mint_amount_raw':sum(amount(x) for x in v2_mints),'burn_events':len(v2_burns),'mint_events':len(v2_mints)}
del v2_burns,v2_mints
opening=int(control['raw_supplies']['2026-07-01'],16);closing=int(control['raw_supplies']['2026-10-01'],16)
rawnet=sum(amount(x)*(1 if x['topics'][0]==flows['mint_topic'] else -1) for x in flows['logs'])
ck('exact raw-unit supply reconciliation',opening+rawnet==closing)
ck('unique mint/burn log identities',len(flows['logs'])==len({(x['transactionHash'],x['logIndex']) for x in flows['logs']}))
month_end={
 '2026-07':json.loads((CIRCLE/'feasibility/raw/checkpoint_2026_07_31_block_lookup.json').read_text())['height'],
 '2026-08':json.loads((CIRCLE/'feasibility/raw/checkpoint_2026_08_31_block_lookup.json').read_text())['height'],
 '2026-09':bound['2026-10-01']}
def month(b):return next(m for m,h in month_end.items() if b<=h)
monthly=[]
for m,h in month_end.items():monthly.append({'month':m,**totals([x for x in flows['logs'] if month(int(x['blockNumber'],16))==m])})
save('usdc_flow_analysis.json',{'scope':'Ethereum native USDC Q3 2026, raw token units reconciled against totalSupply; USD at par',
 'contracts':contracts,'first_block':flows['first'],'last_block':flows['last'],'opening_supply_usd_million':opening/1e12,'closing_supply_usd_million':closing/1e12,
 'supply_difference_raw_units':str(opening+rawnet-closing),'quarter':alltotals,'monthly':monthly,
 'use':'Demand and migration decomposition. Non-CCTP is an unclassified residual, not an exact measure of fiat customer redemptions or fee-paying activity.',
 'forecast_link':'Global reserve estimates still use global daily USDC and yield. Do not add Ethereum net flow again to an already observed global supply series.'})
del flows['logs']

route=read('ethereum_cctp_q3_routes.json');route_rows=[]
# ABI layout is derived from downloaded Circle source, not a mismatched generic documentation table.
fields=route['fields'];indexed=[x.split()[-1] for x in fields if ' indexed ' in ' '+x+' ']
unindexed=[x.split()[-1] for x in fields if ' indexed ' not in ' '+x+' ']
for log in route['logs']:
    topics=log['topics'][1:];data=bytes.fromhex(log['data'][2:]);words=[int.from_bytes(data[i:i+32],'big') for i in range(0,len(data),32)]
    args={k:int(v,16) for k,v in zip(indexed,topics)};args.update({k:v for k,v in zip(unindexed,words)})
    if args.get('burnToken')!=int(contracts['usdc'],16):continue
    route_rows.append({'tx':log['transactionHash'],'log_index':int(log['logIndex'],16),'block':int(log['blockNumber'],16),
      'month':month(int(log['blockNumber'],16)),'depositor':'0x'+format(args['depositor'],'040x'),
      'destination_domain':args['destinationDomain'],'amount_usdc':args['amount']/1e6,
      'amount_raw':str(args['amount']),
      'requested_min_finality':args['minFinalityThreshold'],'max_fee_usdc':args['maxFee']/1e6})
dest=[]
for d in sorted({r['destination_domain'] for r in route_rows}):
    r=[x for x in route_rows if x['destination_domain']==d]
    dest.append({'destination_domain':d,'events':len(r),'volume_usd_million':sum(x['amount_usdc'] for x in r)/1e6,
     'requested_fast_events':sum(x['requested_min_finality']<2000 for x in r),'unique_depositors':len({x['depositor'] for x in r})})
users={m:{x['depositor'] for x in route_rows if x['month']==m} for m in month_end}
cohorts=[]
for m1,m2 in zip(list(month_end),list(month_end)[1:]):
    cohorts.append({'start_month':m1,'next_month':m2,'starting_addresses':len(users[m1]),'returning_addresses':len(users[m1]&users[m2]),'retention':len(users[m1]&users[m2])/len(users[m1]) if users[m1] else None})
byuser=collections.defaultdict(float)
for x in route_rows:byuser[x['depositor']]+=x['amount_usdc']
top10=sum(sorted(byuser.values(),reverse=True)[:10]);volume=sum(byuser.values())
fee_logs=read('ethereum_cctp_q3_fee_logs.json')['logs'];fee_rows=[];fee_word_lengths=set()
for log in fee_logs:
    if int(log['topics'][2],16)!=int(contracts['usdc'],16):continue
    words=[int(log['data'][i:i+64],16) for i in range(2,len(log['data']),64)]
    fee_word_lengths.add(len(words))
    fee_rows.append({'tx':log['transactionHash'],'amount_raw':str(words[0]),'fee_raw':str(words[1]),'month':month(int(log['blockNumber'],16))})
incoming_fee_usd=sum(int(x['fee_raw']) for x in fee_rows)/1e6
ck('all CCTP fee events have two data words',fee_word_lengths=={2})
ck('CCTP V2 source messages reconcile to USDC burn amount',v2_control['burn_amount_raw']==sum(int(x['amount_raw']) for x in route_rows))
ck('CCTP V2 source message count equals USDC burn count',v2_control['burn_events']==len(route_rows))
ck('CCTP V2 mint amount reconciles to delivered amount plus fee',v2_control['mint_amount_raw']==sum(int(x['amount_raw'])+int(x['fee_raw']) for x in fee_rows))
ck('CCTP V2 mint count reconciles to delivery and positive-fee mints',v2_control['mint_events']==len(fee_rows)+sum(int(x['fee_raw'])>0 for x in fee_rows))
llama=json.loads((CIRCLE/'stage4/raw/llama_cctp_fee_history.json').read_text())
llama_eth=0
llama_monthly=collections.defaultdict(float)
for t,data in llama['totalDataChartBreakdown']:
    d=dt.datetime.fromtimestamp(t,dt.timezone.utc).date()
    if dt.date(2026,7,1)<=d<=dt.date(2026,9,30):
        value=sum(data.get('Ethereum',{}).values());llama_eth+=value;llama_monthly[d.isoformat()[:7]]+=value
save('cctp_route_and_cohort_analysis.json',{'scope':'Q3 2026 Ethereum CCTP V2 source-route and destination fee events; distinct populations',
 'signature':route['signature'],'fields':route['fields'],'source_events':len(route_rows),'source_volume_usd_million':volume/1e6,'destinations':dest,
 'source_unique_depositors':len(byuser),'source_top10_depositor_volume_share':top10/volume if volume else None,'monthly_depositor_retention':cohorts,
 'requested_fast_event_share':sum(x['requested_min_finality']<2000 for x in route_rows)/len(route_rows) if route_rows else None,
 'destination_fee_events':len(fee_rows),'destination_paid_fee_events':sum(int(x['fee_raw'])>0 for x in fee_rows),'destination_fees_usd':incoming_fee_usd,
 'defillama_ethereum_fees_usd':llama_eth,'rpc_minus_aggregator_fees_usd':incoming_fee_usd-llama_eth,
 'monthly_fee_comparison':[{'month':m,'rpc_usdc_fees_usd':sum(int(x['fee_raw']) for x in fee_rows if x['month']==m)/1e6,'aggregator_ethereum_fees_usd':llama_monthly[m]} for m in month_end],
 'token_event_cross_checks':{k:str(v) for k,v in v2_control.items()},
 'fee_reconciliation_status':'Unresolved direct-RPC versus aggregator difference; preserve both series and do not replace the earlier transaction backtest inputs.',
 'limitations':['Depositors are addresses, not people or all USDC holders','Requested fast finality is not a verified actual fee-paying outcome','Do not divide Ethereum incoming fees by outgoing-route volume as a fee rate','Top-depositor concentration can reflect aggregators and exchange operations','Protocol fee versus GAAP timing remains a separate reconciliation']})

fund=read('usyc_2025_2026_reporter_logs.json');times=read('usyc_report_block_times.json');reports=[]
for log in fund['logs']:
    words=[int(log['data'][i:i+64],16) for i in range(2,len(log['data']),64)]
    ck('USYC event layout',len(words) in [6,7]);principal,interest,supply,updated,price,fee=words[:6];embedded=words[6] if len(words)==7 else 0
    fee_usd=D(fee)*D(price)/D(10**24);gross=D(interest+embedded)/D(10**6);aum=D(supply)*D(price)/D(10**24)
    ck('USYC fee equals 10% gross income within rounding',abs(fee_usd-gross/D(10))<D('.01'))
    observed=times[str(int(log['blockNumber'],16))]
    reports.append({'round_id':int(log['topics'][2],16),'block':int(log['blockNumber'],16),'tx':log['transactionHash'],
      'observed_at_utc':dt.datetime.fromtimestamp(observed,dt.timezone.utc).isoformat(),'economic_at_utc':dt.datetime.fromtimestamp(updated,dt.timezone.utc).isoformat(),
      'observed_date':dt.datetime.fromtimestamp(observed,dt.timezone.utc).date().isoformat(),
      'price_usd':price/1e18,'share_supply':supply/1e6,'aum_proxy_usd':float(aum),'fee_shares':fee/1e6,'performance_fee_usd':float(fee_usd),'gross_income_usd':float(gross)})
reports.sort(key=lambda r:r['block']);ck('USYC unique round ids',len(reports)==len({x['round_id'] for x in reports}))
ck('USYC report rounds consecutive',max(x['round_id'] for x in reports)-min(x['round_id'] for x in reports)+1==len(reports))
ledger=json.loads((CIRCLE/'stage4/results/other_revenue_model.json').read_text())['ledger']
qs=json.loads((CIRCLE/'stage2/results/stage2_data_model.json').read_text())['quarters'];fund_quarters=[]
for q in qs:
    r=[x for x in reports if q['start']<=x['observed_date']<=q['end']]
    fund_quarters.append({'period':q['period'],'days':q['days'],'reports':len(r),'first_observed_date':r[0]['observed_date'] if r else None,'last_observed_date':r[-1]['observed_date'] if r else None,
      'performance_fees_usd_million':sum(x['performance_fee_usd'] for x in r)/1e6,
      'gross_income_usd_million':sum(x['gross_income_usd'] for x in r)/1e6,
      'ending_report_aum_usd_million':r[-1]['aum_proxy_usd']/1e6 if r else None,'ending_price_usd':r[-1]['price_usd'] if r else None,
      'ending_share_supply_million':r[-1]['share_supply']/1e6 if r else None})
def snapshot(p,cut):
    e=[x for x in ledger if x['period']==p and x['published_by']<=cut and x['classification']=='current']
    return max(e,key=lambda x:x['published_by']) if e else None
tests=[]
for i,q in enumerate(qs):
    if i<2:continue
    cut=(dt.date.fromisoformat(q['earnings_release_date'])-dt.timedelta(days=1)).isoformat();prev=qs[i-1];s=snapshot(prev['period'],cut)
    target=snapshot(q['period'],'2026-11-21')['metrics']['subscription_services']['value'];lag=s['metrics']['subscription_services']['value']
    current_fee=fund_quarters[i]['performance_fees_usd_million'];prior_fee=fund_quarters[i-1]['performance_fees_usd_million']
    pred=current_fee+(lag-prior_fee)
    ck(q['period']+' prior services available before earnings',s['published_by']<=cut)
    tests.append({'period':q['period'],'cutoff':cut,'actual_services':target,'current_usyc_fees':current_fee,'prior_usyc_fees':prior_fee,'prior_services':lag,
      'flat_estimate':lag,'flat_error':lag/target-1,'fee_plus_flat_residual_estimate':pred,'fee_plus_flat_residual_error':pred/target-1})
def metrics(rows):return {'n':len(rows),'flat_mape':st.mean(abs(x['flat_error']) for x in rows),'fee_plus_residual_mape':st.mean(abs(x['fee_plus_flat_residual_error']) for x in rows)}
save('usyc_fund_and_services_analysis.json',{'scope':'Authenticated Ethereum reporter fund-share NAV and fee observations; not a sum of all chain token supplies',
 'reports':reports,'quarterly':fund_quarters,'services_nowcasts':tests,'nowcast_metrics':metrics(tests),
 'formula':'Performance fee USD = raw fee shares / 1e6 * raw price / 1e18. NAV proxy = reported share supply / 1e6 * price. Gross income includes embeddedIncome where present.',
 'timing':'Quarter allocation and pre-earnings availability use actual block observation time, not merely the economic timestamp inside the report.',
 'forecast_link':'For a future period, project average fund assets times expected gross annual yield times fee rate and days/365; for a completed quarter, sum observed fee mints. Forecast private service residual separately.',
 'limits':['Reporter history is not an independently audited product GAAP revenue reconciliation','Report-date NAV proxies are not daily-average global NAV','Do not add wrapped/BSC share representations to reporter share supply','Quarterly observation-time fees can differ from economic accrual-date accounting','Measured fee component plus lagged residual is a fixed-rule exploratory nowcast']})

# Chain composition uses the provider's bridge-adjusted circulation measure, not a claim of native-only mint supply.
usdc=json.loads((ROOT/'raw/usdc_current_history.json').read_text());chains=usdc['chainBalances'];selected=[n for n in ['Ethereum','Solana','Base','Arbitrum','Polygon','Avalanche','Arc'] if n in chains]
mix=[]
for q in qs:
    stamp=int(dt.datetime.fromisoformat(q['end']).replace(tzinfo=dt.timezone.utc).timestamp())
    global_row=next(x for x in usdc['tokens'] if int(x['date'])==stamp);total=global_row['circulating']['peggedUSD'];entries=[]
    for name in selected:
        r=next((x for x in chains[name]['tokens'] if int(x['date'])==stamp),None)
        if r:entries.append({'chain':name,'provider_circulation_usd_million':r['circulating'].get('peggedUSD',0)/1e6,'share_global':r['circulating'].get('peggedUSD',0)/total,
          'native_minted_field_usd_million':r.get('minted',{}).get('peggedUSD',0)/1e6 if isinstance(r.get('minted'),dict) else None})
    mix.append({'period':q['period'],'global_circulation_usd_million':total/1e6,'chains':entries})
save('usdc_chain_composition.json',{'quarterly':mix,'scope':'Selected-chain provider circulation and separate minted fields, with official native-contract mapping in earlier stage',
 'limits':'Provider circulation includes bridge adjustment; it is not a clean native-only holder balance. Do not sum minted/bridged fields or assume all 165 series are Circle native issuance.'})
save('onchain_analysis_checks.json',{'checks_passed':sum(x['passed'] for x in checks),'checks_total':len(checks),'checks':checks})
print(json.dumps({'flow':alltotals,'supply_reconciliation_raw_units':str(opening+rawnet-closing),'routes':len(route_rows),'unique_source_depositors':len(byuser),'fee_usd':incoming_fee_usd,'fund_reports':len(reports),'fund_nowcast_metrics':metrics(tests)},indent=2))
assert all(x['passed'] for x in checks),[x for x in checks if not x['passed']]
