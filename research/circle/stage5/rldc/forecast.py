"""Prospective Q4 RLDC scenario using only observations available 21 Nov 2026."""
import bisect,datetime as dt,hashlib,json,statistics as st
from pathlib import Path
ROOT=Path(__file__).resolve().parent;CIRCLE=ROOT.parents[1];OUT=ROOT/'results'
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
core=read(CIRCLE/'stage2/results/stage2_data_model.json');prior=core['quarters'][-1];m=prior['metrics']
history=read(CIRCLE/'stage5/raw/usdc_current_history.json')['tokens'];S={dt.datetime.fromtimestamp(int(x['date']),dt.timezone.utc).date():x['circulating']['peggedUSD']/1e6 for x in history}
rates=read(CIRCLE/'feasibility/raw/nyfed_sofr_2023_2026.json')['refRates'];rd={dt.date.fromisoformat(r['effectiveDate']):r['percentRate']/100 for r in rates};dates=sorted(rd)
pub={d:dates[i+1] for i,d in enumerate(dates[:-1])}
asof=dt.date(2026,11,21);cut=min(max(d for d in S if d<asof),asof-dt.timedelta(days=1))
def days(a,b):return [a+dt.timedelta(days=i) for i in range((b-a).days+1)]
def known_rate(d):
    eligible=[e for e in dates[:-1] if e<=d and pub[e]<=asof]
    assert eligible
    return rd[eligible[-1]]
lagdays=days(dt.date.fromisoformat(prior['start']),dt.date.fromisoformat(prior['end']))
lagyield=m['reserve_income']['value']/m['usdc_average']['value']*365/prior['days']
lagbenchmark=sum(S[d]*known_rate(d)*365/360 for d in lagdays)/sum(S[d] for d in lagdays);spread=lagyield-lagbenchmark
observed=days(dt.date(2026,10,1),cut);future=days(cut+dt.timedelta(days=1),dt.date(2026,12,31))
assert len(observed)+len(future)==92 and all(d in S for d in observed)
lastS=S[cut];lastRate=known_rate(asof);quarter_supply_days=sum(S[d] for d in observed)+lastS*len(future)
raw=sum(S[d]*known_rate(d)/360 for d in observed)+lastS*lastRate*len(future)/360
reserve=raw+spread*quarter_supply_days/365
qs=core['quarters'];window=qs[-3:];pool=sum(q['metrics']['total_costs']['value'] for q in window)/sum(q['metrics']['reserve_income']['value'] for q in window)
latest=m['total_costs']['value']/m['reserve_income']['value'];weights=[.5**j for j in reversed(range(len(qs)))];ewma=sum(w*q['metrics']['total_costs']['value']/q['metrics']['reserve_income']['value'] for w,q in zip(weights,qs))/sum(weights)
case=read(CIRCLE/'stage5/results/2026-11-21_flat_other_ARC_working_case.json');nonarc=case['quarterly_non_arc_operating_other_revenue_approx'];arc=case['q4_existing_arc_recognition_assumption']
result={'as_of':'2026-11-21','period':'2026Q4','actual':None,'units':'USD million unless specified','observed_supply_through':cut.isoformat(),'observed_calendar_days':len(observed),'projected_calendar_days':len(future),'last_observed_usdc_million':lastS,'projected_average_usdc_million':quarter_supply_days/92,'last_available_sofr':lastRate,
 'lag_period':'2026Q3','lag_reserve_income':m['reserve_income']['value'],'lag_reported_average_usdc_million':m['usdc_average']['value'],'lag_days':prior['days'],'lag_implied_yield':lagyield,'lag_supply_weighted_sofr_365':lagbenchmark,'annual_spread':spread,
 'known_supply_days_million':sum(S[d] for d in observed),'projected_supply_days_million':lastS*len(future),'raw_sofr_income':raw,'reserve_income_forecast':reserve,
 'non_arc_other_revenue_assumption_approx':nonarc,'arc_recognition_assumption':arc,'selected_method':'pool3_ratio','cost_calibration_periods':[q['period'] for q in window],
 'cost_calibration_rows':[{'period':q['period'],'reserve':q['metrics']['reserve_income']['value'],'cost':q['metrics']['total_costs']['value']} for q in qs],
 'cost_ratios':{'pool3_ratio':pool,'lag_ratio':latest,'ewma_ratio':ewma},
 'estimates':{n:{'cost_ratio':r,'total_costs':reserve*r,'underlying_rldc':reserve+nonarc-reserve*r,'rldc_including_arc':reserve+nonarc+arc-reserve*r} for n,r in [('pool3_ratio',pool),('lag_ratio',latest),('ewma_ratio',ewma)]},
 'simple_sensitivities':{'cost_ratio_plus_1pp_rldc_change':-reserve*.01,'reserve_income_plus_10m_rldc_change_at_fixed_ratio':10*(1-pool),'arc_delayed_recognition_rldc_change':-arc},
 'assumptions':['Remaining daily global USDC stays at the last complete observed date','Remaining SOFR stays at the latest published value; following-business-day publication control','Lagged reserve spread uses the Stage3 reported-average-supply implied-yield convention','Non-ARC operating other revenue stays flat at Q3 level','Existing ARC 60.4m is recognized in Q4 only as user-directed scenario','No separate incremental distribution cost assigned to ARC recognition; costs scale with reserve income','No current Q4 Coinbase earnings available; partner models cannot be populated as observed forecasts'],
 'limitations':['Prospective scenario, not a completed-quarter nowcast','Current provider histories are not archived point-in-time vintages','Supply uses provider daily buckets, not independently proven EOD alignment','Q4 ARC recognition timetable is unverified','Not EPS, net income or new cash receipts','Comparative formula cases are alternative methods, not confidence bounds'],
 'source_hashes':{str(p.relative_to(CIRCLE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [CIRCLE/'stage5/raw/usdc_current_history.json',CIRCLE/'feasibility/raw/nyfed_sofr_2023_2026.json',CIRCLE/'stage2/results/stage2_data_model.json',CIRCLE/'stage5/results/2026-11-21_flat_other_ARC_working_case.json']}}
p=OUT/'2026-11-21_Q4_RLDC_forecast.json'
daily=[]
for role,ds in [('Calibration',lagdays),('Forecast',observed+future)]:
    for d in ds:daily.append({'date':d.isoformat(),'role':role,'observed_supply_million':S[d] if role=='Calibration' or d<=cut else None,'available_sofr':known_rate(d) if role=='Calibration' or d<=cut else None})
(OUT/'q4_daily_build_inputs.json').write_text(json.dumps({'as_of':asof.isoformat(),'observed_through':cut.isoformat(),'rows':daily,'sources':['https://stablecoins.llama.fi/stablecoin/2','https://markets.newyorkfed.org/api/rates/secured/sofr/search.json?startDate=2023-01-01&endDate=2026-11-20']},indent=2),encoding='utf8')
if p.exists():assert read(p)==result,'Keep the dated forecast; new information requires a separate version.'
else:p.write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({k:result[k] for k in ['observed_supply_through','observed_calendar_days','projected_calendar_days','last_observed_usdc_million','last_available_sofr','reserve_income_forecast','cost_ratios','estimates','simple_sensitivities']},indent=2))
