"""Publication-filtered historical simulations using current supply/rate history.

No current-quarter financial outcome enters a prediction. Original fund filings
are selected before constructing daily proxies. Public source values are in
USD millions, decimal annual rates, and calendar days unless otherwise stated.
"""
from __future__ import annotations
import bisect
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path
import statistics as st
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent; CIRCLE=ROOT.parent
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
checks=[]
def check(name,ok,detail=None):
    checks.append({'check':name,'passed':bool(ok),'detail':detail})
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(name,x):(OUT/name).write_text(json.dumps(x,indent=2,allow_nan=False),encoding='utf8')
def date(x):return dt.date.fromisoformat(x[:10])
def days(a,b):return [a+dt.timedelta(days=i) for i in range((b-a).days+1)]
def previous(mapping,d):
    k=sorted(mapping);i=bisect.bisect_right(k,d)-1
    if i<0:raise ValueError('No prior observation for '+str(d))
    return k[i],mapping[k[i]]

def extract_funds():
    filings=read(ROOT/'fund_filings.json')
    submissions=read(ROOT/'raw/fund_submissions.json')['filings']['recent']
    reg={a:{k:v[i] for k,v in submissions.items()} for i,a in enumerate(submissions['accessionNumber'])}
    originals={};excluded=[];all_rows=[];report_rows=[]
    for f in sorted(filings,key=lambda f:(f['filed'],f['accession'])):
        f=dict(f);f['form']=f['search_source']['form']
        control=reg.get(f['accession'])
        check(f['accession']+' independent filing date',control is not None and control['filingDate']==f['filed'])
        if control:f['accepted_datetime']=control['acceptanceDateTime']
        if f['form']!='N-MFP3' or f['report_date'] in originals:
            excluded.append({k:f[k] for k in ['accession','report_date','filed','form']});continue
        t=ET.parse(ROOT/f['file']);text=lambda tag:t.findtext('.//{*}'+tag)
        check(f['accession']+' series identity',text('seriesId')=='S000077205')
        net=t.findall('.//{*}sevenDayNetYield')
        gross={e.findtext('{*}sevenDayGrossYieldDate'):float(e.findtext('{*}sevenDayGrossYieldValue')) for e in t.findall('.//{*}sevenDayGrossYield')}
        r=[]
        for e in net:
            d=e.findtext('{*}sevenDayNetYieldDate');y=float(e.findtext('{*}sevenDayNetYieldValue'))
            r.append({'date':d,'net_yield':y,'gross_yield':gross.get(d),'filed':f['filed'],
                      'report_date':f['report_date'],'accession':f['accession'],'url':f['url']})
        check(f['report_date']+' fund observations nonempty and plausible',len(r)>=18 and all(0<=x['net_yield']<0.10 and x['date'][:7]==f['report_date'][:7] for x in r))
        check(f['report_date']+' fund dates unique',len({x['date'] for x in r})==len(r))
        originals[f['report_date']]=f
        all_rows.extend(r)
        report_rows.append({'report_date':f['report_date'],'filed':f['filed'],'accepted_datetime':f.get('accepted_datetime'),
          'accession':f['accession'],'net_assets_million':float(text('netAssetOfSeries'))/1e6,
          'yield_observations':len(r),'net_yield_min':min(x['net_yield'] for x in r),
          'net_yield_max':max(x['net_yield'] for x in r),'url':f['url'],'file':f['file']})
    check('22 consecutive original fund months',sorted(originals)==[f'{y}-{m:02d}-{(dt.date(y+(m==12),m%12+1,1)-dt.timedelta(days=1)).day:02d}' for y,m in [(2024,12)]+[(2025,m) for m in range(1,13)]+[(2026,m) for m in range(1,10)]])
    return sorted(all_rows,key=lambda r:r['date']),sorted(report_rows,key=lambda r:r['report_date']),excluded

def main():
    model=read(CIRCLE/'stage2/results/stage2_data_model.json')
    quarters=model['quarters'];calendar={r['period']:date(r['date']) for r in read(CIRCLE/'stage2/earnings_calendar.json')}
    supply_raw=read(CIRCLE/'feasibility/raw/defillama_usdc.json')
    supply={dt.datetime.fromtimestamp(int(r['date']),dt.timezone.utc).date():r['circulating']['peggedUSD']/1e6 for r in supply_raw['tokens']}
    sofr={date(r['effectiveDate']):r['percentRate']/100 for r in read(CIRCLE/'feasibility/raw/nyfed_sofr_2023_2026.json')['refRates']}
    treasury={date(r['observation_date']):float(r['DGS3MO'])/100 for r in csv.DictReader((CIRCLE/'feasibility/raw/fred_dgs3mo.txt').read_text().splitlines()) if r['DGS3MO'] not in ['','.']}
    fund_rows,fund_reports,excluded=extract_funds()
    save('original_fund_reports.json',fund_reports);save('fund_yield_observations.json',fund_rows);save('excluded_amendments.json',excluded)
    evaluations=[];daily_records=[];diagnostics=[];eligibility=[]
    for i,q in enumerate(quarters):
        a,b=date(q['start']),date(q['end']);ds=days(a,b);m=q['metrics']
        current_supply=[supply[d] for d in ds]
        implied=m['reserve_income']['value']/m['usdc_average']['value']*365/q['days']
        check(q['period']+' daily supply coverage',len(current_supply)==q['days'] and all(v>0 for v in current_supply))
        diagnostics.append({'period':q['period'],'provider_average':st.mean(current_supply),'reported_average':m['usdc_average']['value'],
          'average_gap':st.mean(current_supply)/m['usdc_average']['value']-1,
          'next_average_gap':st.mean(supply[d+dt.timedelta(days=1)] for d in ds)/m['usdc_average']['value']-1,
          'actual_implied_yield':implied,'reported_rounded_yield':m['reserve_return']['value'],
          'actual_effective_cost_ratio':m['total_costs']['value']/m['reserve_income']['value']})
        if i==0:continue
        lag=quarters[i-1];lm=lag['metrics'];ldays=days(date(lag['start']),date(lag['end']))
        cutoffs={'early':b+dt.timedelta(days=7),'late':calendar[q['period']]-dt.timedelta(days=1)}
        for phase,cutoff in cutoffs.items():
            eid=q['period']+'_'+phase
            needed=['reserve_income','usdc_average','other_revenue','total_costs']
            eligible=all(date(lm[k]['published_by'])<=cutoff for k in needed)
            check(eid+' lag financial inputs eligible',eligible)
            for k in needed:eligibility.append({'evaluation':eid,'input':lag['period']+' '+k,'published_by':lm[k]['published_by'],'cutoff':str(cutoff),'eligible':date(lm[k]['published_by'])<=cutoff})
            f_map={date(r['date']):r for r in fund_rows if date(r['filed'])<=cutoff}
            groups={}
            for role,dates in [('current',ds),('lag',ldays)]:
                group=[]
                for d in dates:
                    fd,f=previous(f_map,d);sd,s=previous(sofr,d);td,t=previous(treasury,d)
                    r={'evaluation':eid,'period':q['period'],'phase':phase,'role':role,'date':str(d),
                       'supply_million':supply[d],'next_supply_million':supply[d+dt.timedelta(days=1)],
                       'sofr':s,'sofr_effective_date':str(sd),'treasury_3m':t,'treasury_effective_date':str(td),
                       'fund_net_yield':f['net_yield'],'fund_observation_date':str(fd),'fund_filed':f['filed'],
                       'fund_accession':f['accession'],'fund_url':f['url'],'cutoff':str(cutoff),
                       'fund_carry_days':(d-fd).days}
                    group.append(r)
                check(eid+' '+role+' no future yield observation',all(r['fund_observation_date']<=r['date'] and r['sofr_effective_date']<=r['date'] and r['treasury_effective_date']<=r['date'] for r in group))
                check(eid+' '+role+' no future fund publication',all(r['fund_filed']<=str(cutoff) for r in group))
                check(eid+' '+role+' SOFR published by cutoff',all(sorted(sofr)[bisect.bisect_right(sorted(sofr),date(r['sofr_effective_date']))]<=cutoff for r in group))
                check(eid+' '+role+' source dates unique',len({r['date'] for r in group})==len(dates))
                groups[role]=group;daily_records.extend(group)
            cur,prev=groups['current'],groups['lag']
            cur_sum=sum(r['supply_million'] for r in cur);prev_sum=sum(r['supply_million'] for r in prev)
            lag_yield=lm['reserve_income']['value']/lm['usdc_average']['value']*365/lag['days']
            prev_sofr_weighted=sum(r['supply_million']*r['sofr']*365/360 for r in prev)/prev_sum
            prev_fund_weighted=sum(r['supply_million']*r['fund_net_yield'] for r in prev)/prev_sum
            sofr_spread=lag_yield-prev_sofr_weighted;fund_spread=lag_yield-prev_fund_weighted
            raw_sofr=sum(r['supply_million']*r['sofr']/360 for r in cur)
            raw_fund=sum(r['supply_million']*r['fund_net_yield']/365 for r in cur)
            estimates={
              'carry_forward':lm['reserve_income']['value']*q['days']/lag['days'],
              'lagged_implied_yield':cur_sum*lag_yield/365,
              'sofr':raw_sofr,
              'treasury_3m':sum(r['supply_million']*r['treasury_3m']/365 for r in cur),
              'sofr_lagged_spread':raw_sofr+cur_sum*sofr_spread/365,
              'fund_lagged_spread':raw_fund+cur_sum*fund_spread/365,
            }
            next_estimates={
              'carry_forward':estimates['carry_forward'],
              'lagged_implied_yield':sum(r['next_supply_million']*lag_yield/365 for r in cur),
              'sofr':sum(r['next_supply_million']*r['sofr']/360 for r in cur),
              'treasury_3m':sum(r['next_supply_million']*r['treasury_3m']/365 for r in cur),
              'sofr_lagged_spread':sum(r['next_supply_million']*(r['sofr']*365/360+sofr_spread)/365 for r in cur),
              'fund_lagged_spread':sum(r['next_supply_million']*(r['fund_net_yield']+fund_spread)/365 for r in cur),
            }
            next_prev_sum=sum(r['next_supply_million'] for r in prev)
            next_sofr_spread=lag_yield-sum(r['next_supply_million']*r['sofr']*365/360 for r in prev)/next_prev_sum
            next_fund_spread=lag_yield-sum(r['next_supply_million']*r['fund_net_yield'] for r in prev)/next_prev_sum
            next_recalibrated={**next_estimates,
              'sofr_lagged_spread':sum(r['next_supply_million']*(r['sofr']*365/360+next_sofr_spread)/365 for r in cur),
              'fund_lagged_spread':sum(r['next_supply_million']*(r['fund_net_yield']+next_fund_spread)/365 for r in cur)}
            ri_actual=m['reserve_income']['value'];reserve_est=estimates['sofr_lagged_spread']
            cost_ratio=lm['total_costs']['value']/lm['reserve_income']['value']
            other_est=lm['other_revenue']['value'] # straight quarter carry, explicitly separate from day-adjusted reserve baseline
            costs_est=reserve_est*cost_ratio;revenue_est=reserve_est+other_est;rldc_est=revenue_est-costs_est
            row={'id':eid,'period':q['period'],'phase':phase,'cutoff':str(cutoff),'earnings_release':str(calendar[q['period']]),
              'days':q['days'],'lag_period':lag['period'],'lag_days':lag['days'],'lag_inputs_eligible':eligible,
              'supply_sum_million_days':cur_sum,'lag_supply_sum_million_days':prev_sum,
              'lag_implied_yield':lag_yield,'lag_sofr_weighted_365':prev_sofr_weighted,'lag_fund_weighted':prev_fund_weighted,
              'sofr_spread':sofr_spread,'fund_spread':fund_spread,'raw_fund_estimate':raw_fund,
              'estimates':estimates,'next_bucket_estimates_fixed_spreads':next_estimates,
              'next_bucket_estimates_recalibrated_spreads':next_recalibrated,
              'actual_reserve_income':ri_actual,'errors':{k:v/ri_actual-1 for k,v in estimates.items()},
              'fund_max_carry_days_current':max(r['fund_carry_days'] for r in cur),
              'fund_final_month_available':any(r['report_date']==str(b) and date(r['filed'])<=cutoff for r in fund_reports),
              'rldc':{'reserve_estimate':reserve_est,'other_revenue_estimate':other_est,'cost_ratio':cost_ratio,
                'costs_estimate':costs_est,'total_revenue_estimate':revenue_est,'rldc_estimate':rldc_est,
                'actual_other_revenue':m['other_revenue']['value'],'actual_total_revenue':m['total_revenue']['value'],
                'actual_costs':m['total_costs']['value'],'actual_rldc':m['rldc']['value'],
                'rldc_error':rldc_est/m['rldc']['value']-1,'total_revenue_error':revenue_est/m['total_revenue']['value']-1,
                'cost_ratio_sensitivity_pp':0.05,'illustrative_low':rldc_est-reserve_est*0.05,'illustrative_high':rldc_est+reserve_est*0.05},
              'supply_sensitivity':{str(delta):reserve_est*(1+delta) for delta in [-0.01,-0.005,0.005,0.01]},
              'yield_25bp_income_effect':cur_sum*0.0025/365}
            check(eid+' income bridge identity',abs(row['rldc']['total_revenue_estimate']-row['rldc']['costs_estimate']-row['rldc']['rldc_estimate'])<1e-9)
            check(eid+' spread arithmetic independent daily sum',abs(sum(r['supply_million']*(r['sofr']*365/360+sofr_spread)/365 for r in cur)-reserve_est)<1e-8)
            check(eid+' cost sensitivity correctly ordered',row['rldc']['illustrative_low']<rldc_est<row['rldc']['illustrative_high'])
            evaluations.append(row)
    metrics={}
    for phase in ['early','late']:
        ev=[r for r in evaluations if r['phase']==phase];metrics[phase]={}
        for method in ev[0]['estimates']:
            errs=[r['errors'][method] for r in ev]
            metrics[phase][method]={'n':len(errs),'mape':st.mean(abs(e) for e in errs),'mean_signed_error':st.mean(errs),
              'mae_million':st.mean(abs(r['estimates'][method]-r['actual_reserve_income']) for r in ev),
              'worst_abs_error':max(abs(e) for e in errs),'wins_vs_carry':sum(abs(r['errors'][method])<abs(r['errors']['carry_forward']) for r in ev)}
    supply_checks=[]
    for r in model['supply_checkpoints']:
        gap=r['following_bucket_gap_pct'];supply_checks.append({'period':r['period'],'quarter_end_gap':gap,
          'preferred_pass':abs(gap)<=0.005,'outer_pass':abs(gap)<=0.01,
          'average_gap':next(x['average_gap'] for x in diagnostics if x['period']==r['period'])})
    check('all 7 quarter-end comparisons pass user preferred supply tolerance',all(r['preferred_pass'] for r in supply_checks))
    check('all 7 quarter-average comparisons pass user preferred supply tolerance',all(abs(r['average_gap'])<=0.005 for r in supply_checks))
    check('six quarters and two cutoffs',len(evaluations)==12 and len({r['period'] for r in evaluations})==6)
    check('post-cutoff amendments never selected',not any(r['fund_accession'] in {a['accession'] for a in excluded} for r in daily_records))
    # Check boundary: June 2026 original fund filing was on July 8, beyond July 7 early cutoff.
    q2early=next(r for r in evaluations if r['id']=='2026Q2_early')
    check('July 8 fund filing excluded on July 7 early cutoff',not q2early['fund_final_month_available'])
    inventory=[]
    paths=[CIRCLE/'stage2/results/stage2_data_model.json',CIRCLE/'stage2/earnings_calendar.json',
      CIRCLE/'feasibility/raw/defillama_usdc.json',CIRCLE/'feasibility/raw/nyfed_sofr_2023_2026.json',CIRCLE/'feasibility/raw/fred_dgs3mo.txt',ROOT/'Stage_3_Protocol.md']
    paths += [ROOT/r['file'] for r in fund_reports]
    for p in paths:inventory.append({'file':str(p.relative_to(CIRCLE)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size})
    manifests={r['file']:r for r in read(ROOT/'source_manifest.json') if r.get('status')=='received'}
    for r in fund_reports:check(r['report_date']+' fund source hash',hashlib.sha256((ROOT/r['file']).read_bytes()).hexdigest()==manifests[r['file']]['sha256'])
    output={'as_of_date':'2026-11-21','status':'publication-filtered historical simulation using current data, not strict point-in-time',
      'primary_method':'sofr_lagged_spread','supply_preferred_tolerance':0.005,'supply_outer_tolerance':0.01,
      'quarters':quarters,'fund_reports':fund_reports,'excluded_amendments':excluded,'fund_observation_count':len(fund_rows),
      'evaluations':evaluations,'metrics':metrics,'supply_checks':supply_checks,'diagnostics_scoring_only':diagnostics,
      'checks_passed':sum(r['passed'] for r in checks),'checks_total':len(checks)}
    save('stage3_model.json',output);save('daily_model_inputs.json',daily_records);save('input_eligibility.json',eligibility);save('source_integrity.json',inventory);save('validation_checks.json',checks)
    with (OUT/'reserve_errors.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.writer(f);w.writerow(['period','phase','cutoff','method','estimate_usd_million','actual_usd_million','signed_error_pct'])
        for r in evaluations:
            for k,v in r['estimates'].items():w.writerow([r['period'],r['phase'],r['cutoff'],k,v,r['actual_reserve_income'],100*r['errors'][k]])
    print(json.dumps({'checks_passed':output['checks_passed'],'checks_total':len(checks),'fund_months':len(fund_reports),'fund_observations':len(fund_rows),'late_metrics':metrics['late'],
      'early_vs_late_fund':[(r['id'],round(r['estimates']['fund_lagged_spread'],3),r['fund_final_month_available']) for r in evaluations]},indent=2))
    if not all(r['passed'] for r in checks):raise SystemExit('FAILED CHECKS: '+str([r for r in checks if not r['passed']]))

if __name__=='__main__':main()
