"""Fixed-rule, publication-filtered transaction revenue backtest."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import statistics as st
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
stage4=ROOT.parent;circle=stage4.parent
ledger=json.loads((stage4/'results/other_revenue_model.json').read_text())['ledger']
financial=json.loads((circle/'stage2/results/stage2_data_model.json').read_text())['quarters']
raw=json.loads((stage4/'raw/llama_cctp_fee_history.json').read_text())
fees={dt.datetime.fromtimestamp(int(t),dt.timezone.utc).date():float(v)/1e6 for t,v in raw['totalDataChart']}
assert len(fees)==len(raw['totalDataChart'])
checks=[]
def ck(name,v):checks.append({'name':name,'passed':bool(v)})
def snap(period,cutoff):
    e=[x for x in ledger if x['period']==period and x['published_by']<=cutoff and 'transaction_revenue' in x['metrics'] and x['classification']=='current']
    return max(e,key=lambda x:x['published_by']) if e else None
def fee_period(a,b):
    days=[a+dt.timedelta(days=i) for i in range((b-a).days+1)]
    missing=[d.isoformat() for d in days if d not in fees]
    present=[fees[d] for d in days if d in fees]
    return {'sum_observed':sum(present) if present else None,'days_present':len(present),'days_expected':len(days),'missing_dates':missing,'complete':not missing}
quarters=[]
for q in financial:
    a=dt.date.fromisoformat(q['start']);b=dt.date.fromisoformat(q['end'])
    # Preserve the first comparable Q1 2025 split used by the 2025 Q3 growth
    # challenger; its later May 2026 comparative is a different classification.
    s=snap(q['period'],'2025-08-12' if q['period']=='2025Q1' else '2026-11-21')
    quarters.append({'period':q['period'],'start':q['start'],'end':q['end'],'days':q['days'],
      'earnings_release_date':q.get('earnings_release_date'),
      'transaction_actual':s['metrics']['transaction_revenue']['value'] if s else None,
      'published_by':s['published_by'] if s else None,'source_url':s['source_url'] if s else None,
      'cctp':fee_period(a,b)})
late=[];early=[]
for i,q in enumerate(quarters):
    if i<2:continue
    prev=quarters[i-1];prev2=quarters[i-2]
    cutoff=(dt.date.fromisoformat(q['earnings_release_date'])-dt.timedelta(days=1)).isoformat()
    p=snap(prev['period'],cutoff);p2=snap(prev2['period'],cutoff)
    assert p
    lag=p['metrics']['transaction_revenue']['value'];actual=q['transaction_actual']
    methods={'prior_quarter_flat':lag,'prior_quarter_day_scaled':lag*q['days']/prev['days']}
    if p2:methods['repeat_prior_growth']=lag**2/p2['metrics']['transaction_revenue']['value']
    residual=None;unavailable={}
    if prev['cctp']['complete'] and q['cctp']['complete']:
        residual=lag-prev['cctp']['sum_observed']
        methods['observed_cctp_plus_flat_residual']=q['cctp']['sum_observed']+residual
        methods['observed_cctp_plus_day_scaled_residual']=q['cctp']['sum_observed']+residual*q['days']/prev['days']
    else:
        unavailable['observed_cctp_methods']='CCTP coverage incomplete in current or prior quarter; no zero fill'
    ck(q['period']+' lag public before earnings',p['published_by']<=cutoff)
    late.append({'period':q['period'],'cutoff':cutoff,'actual':actual,'current_cctp':q['cctp']['sum_observed'],
      'prior_actual':lag,'prior_cctp':prev['cctp']['sum_observed'],'lagged_non_cctp_residual':residual,
      'current_days':q['days'],'prior_days':prev['days'],'lag_public_by':p['published_by'],
      'cctp_share_actual':q['cctp']['sum_observed']/actual,'methods':methods,'unavailable':unavailable,
      'signed_error':{k:v/actual-1 for k,v in methods.items()}})
    earlydate=dt.date.fromisoformat(q['start'])+dt.timedelta(days=29)
    available=[x for x in quarters[:i] if (s:=snap(x['period'],earlydate.isoformat())) is not None]
    e={'period':q['period'],'cutoff':earlydate.isoformat(),'actual':actual,'methods':{},'unavailable':{}}
    first30=fee_period(dt.date.fromisoformat(q['start']),earlydate)
    e['first30_cctp']=first30
    if available:
        base=available[-1];bs=snap(base['period'],earlydate.isoformat());base_value=bs['metrics']['transaction_revenue']['value']
        e.update(base_period=base['period'],base_actual=base_value,base_cctp=base['cctp']['sum_observed'],base_days=base['days'],base_public_by=bs['published_by'],current_days=q['days'])
        e['methods']['latest_public_flat']=base_value
        e['methods']['latest_public_day_scaled']=base_value*q['days']/base['days']
        if first30['complete'] and base['cctp']['complete']:
            projected_cctp=first30['sum_observed']*q['days']/30
            residual=(base_value-base['cctp']['sum_observed'])*q['days']/base['days']
            e.update(projected_cctp=projected_cctp,projected_residual=residual)
            e['methods']['first30_cctp_plus_latest_public_residual']=projected_cctp+residual
        else:e['unavailable']['cctp_model']='First30 or calibration-quarter CCTP coverage incomplete'
        ck(q['period']+' early base publicly available',bs['published_by']<=earlydate.isoformat())
    else:e['unavailable']['all']='No comparable transaction-category financial result public by early cutoff; IPO Q1 category differs'
    e['signed_error']={k:v/actual-1 for k,v in e['methods'].items()};early.append(e)

def scores(rows,names=None,common=False):
    names=names or sorted({k for x in rows for k in x['methods']})
    population=[x for x in rows if all(n in x['methods'] for n in names)] if common else rows
    out={}
    for name in names:
        r=[x for x in population if name in x['methods']]
        if not r:continue
        err=[abs(x['methods'][name]/x['actual']-1) for x in r]
        out[name]={'n':len(r),'periods':[x['period'] for x in r],'mape':st.mean(err),
          'mae_million':st.mean(abs(x['methods'][name]-x['actual']) for x in r),'worst_abs_error':max(err)}
    return out
main_names=['prior_quarter_flat','prior_quarter_day_scaled','observed_cctp_plus_flat_residual','observed_cctp_plus_day_scaled_residual']
early_names=['latest_public_flat','latest_public_day_scaled','first30_cctp_plus_latest_public_residual']
ck('five comparable late targets retained',len(late)==5)
ck('Q4 spike remains in all comparable late models',all('2025Q4' in x['periods'] for x in scores(late,main_names,True).values()))
ck('Q3 2025 hybrid unavailable instead of imputing missing CCTP','observed_cctp_plus_flat_residual' not in late[0]['methods'])
ck('early Q3 2026 does not use unpublished Q2 financials',next(x for x in early if x['period']=='2026Q3').get('base_period')=='2026Q1')
result={'as_of':'2026-11-21','unit':'USD million','scope':'Historical publication-filtered financial inputs and current reconstructed CCTP observations; not a blind forecast or verified historical data vintage',
 'cctp_source_url':'https://api.llama.fi/summary/fees/circle-cctp?dataType=dailyFees',
 'cctp_mapping_assumption':'Observed CCTP protocol fees map to same-period Circle transaction revenue; the rest is forecast as a lagged residual. Component GAAP reconciliation is not independently disclosed.',
 'quarters':quarters,'late':late,'early':early,'late_all_available_metrics':scores(late),
 'late_common_metrics':scores(late,main_names,True),'early_all_available_metrics':scores(early),
 'early_common_metrics':scores(early,early_names,True),'checks':checks}
(OUT/'transaction_backtest.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({'late_rows':[{'period':x['period'],'actual':x['actual'],'methods':x['methods'],'errors':x['signed_error']} for x in late],
 'late_common':result['late_common_metrics'],'early_common':result['early_common_metrics'],'checks':len(checks)},indent=2))
assert all(x['passed'] for x in checks)
