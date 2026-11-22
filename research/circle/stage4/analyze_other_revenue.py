"""Build a publication-dated product ledger and exploratory revenue forecasts.

The ARC recognition-in-Q3 case is conditional. An FY2026 guide is not a
quarter-specific guarantee. Current-quarter actuals enter scoring only.
"""
from __future__ import annotations
import datetime as dt
import hashlib
import json
from pathlib import Path
import re
import statistics as st
import lxml.html

ROOT=Path(__file__).resolve().parent;CIRCLE=ROOT.parent
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
model=json.loads((CIRCLE/'stage2/results/stage2_data_model.json').read_text())
reserve=json.loads((CIRCLE/'stage3/results/stage3_model.json').read_text())
observations=[];checks=[];ledger=[]
def check(name,ok,detail=None):checks.append({'check':name,'passed':bool(ok),'detail':detail})
def save(name,x):(OUT/name).write_text(json.dumps(x,indent=2,allow_nan=False),encoding='utf8')
SOURCES={
 'ipo_prospectus':('2025-06-05','https://www.sec.gov/Archives/edgar/data/1876042/000119312525135795/d737521d424b4.htm'),
 'q2_2025_html':('2025-08-12','https://www.sec.gov/Archives/edgar/data/1876042/000162828025039781/crcl-20250630.htm'),
 'q3_2025_html':('2025-11-12','https://www.sec.gov/Archives/edgar/data/1876042/000187604225000047/crcl-20250930.htm'),
 'fy2025_html':('2026-03-09','https://www.sec.gov/Archives/edgar/data/1876042/000187604226000062/crcl-20251231.htm'),
 'q1_2026_html':('2026-05-11','https://www.sec.gov/Archives/edgar/data/1876042/000187604226000150/crcl-20260331.htm'),
 'q2_2026_html':('2026-08-05','https://www.sec.gov/Archives/edgar/data/1876042/000187604226000248/crcl-20260630.htm'),
 'q3_2026_html':('2026-11-04','https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm')}
docs={k:lxml.html.fromstring((CIRCLE/'stage2/raw'/(k+'.html')).read_bytes()) for k in SOURCES}

def nums(cells):
    out=[]
    for x in cells[1:]:
        x=x.strip()
        if re.fullmatch(r'\(?[\d,]+(?:\.\d+)?\)?',x):out.append(float(x.replace(',','').replace('(','-').replace(')',''))/1000)
    return out

def revenue_rows(name):
    trs=docs[name].xpath('//tr');entries=[]
    for i,tr in enumerate(trs):
        cells=[' '.join(' '.join(c.itertext()).split()) for c in tr.xpath('./td')]
        entries.append({'row':i,'label':cells[0] if cells else '', 'cells':cells,'numbers':nums(cells) if cells else []})
    if name=='ipo_prospectus':
        # IPO current-quarter table has the original labels, not later classifications.
        start=next(i for i,e in enumerate(entries) if e['label']=='Integration services' and e['numbers'] and abs(e['numbers'][0]-16.331)<1e-9)
        return {'integration_services':entries[start],'transaction_services':entries[start+1],'other':entries[start+2]}
    start=next(i for i,e in enumerate(entries) if e['label']=='Subscription and services')
    return {'subscription_services':entries[start],'transaction_revenue':entries[start+1],'other':entries[start+2]}
tables={k:revenue_rows(k) for k in SOURCES}

def snapshot(period,name,col=0,subtract_col=None,classification='current',basis='reported'):
    vals={}
    for metric,row in tables[name].items():
        val=row['numbers'][col]-(row['numbers'][subtract_col] if subtract_col is not None else 0)
        o={'id':'P'+str(len(observations)+1).zfill(3),'period':period,'metric':metric,'value':val,'unit':'USD million',
          'published_by':SOURCES[name][0],'source_url':SOURCES[name][1],'source_file':'stage2/raw/'+name+'.html',
          'locator':f"HTML row {row['row']}, {row['label']}, numeric column {col+1}"+(f' less column {subtract_col+1}' if subtract_col is not None else ''),
          'basis':basis,'classification':classification}
        observations.append(o);vals[metric]=o
    entry={'period':period,'published_by':SOURCES[name][0],'classification':classification,'metrics':vals,'source_url':SOURCES[name][1]}
    ledger.append(entry);return entry

ipo=snapshot('2025Q1','ipo_prospectus',classification='IPO original')
q1_derived=snapshot('2025Q1','q2_2025_html',2,0,basis='six months less Q2; first comparable categories')
direct={
 '2025Q2':snapshot('2025Q2','q2_2025_html'),
 '2025Q3':snapshot('2025Q3','q3_2025_html'),
 '2026Q1':snapshot('2026Q1','q1_2026_html'),
 '2026Q2':snapshot('2026Q2','q2_2026_html'),
 '2026Q3':snapshot('2026Q3','q3_2026_html')}
q1_later=snapshot('2025Q1','q1_2026_html',1,basis='later comparative classification')
# Q4 category flows must subtract a separate original nine-month statement.
for metric,row in tables['fy2025_html'].items():
    a=row['numbers'][0];b=tables['q3_2025_html'][metric]['numbers'][2]
    o={'id':'P'+str(len(observations)+1).zfill(3),'period':'2025Q4','metric':metric,'value':a-b,'unit':'USD million',
      'published_by':'2026-03-09','source_url':SOURCES['fy2025_html'][1],
      'secondary_source_url':SOURCES['q3_2025_html'][1],'source_file':'stage2/raw/fy2025_html.html',
      'locator':f"FY2025 Table 11.1 {row['label']} less original 9M2025 same category",'basis':'annual less nine months','classification':'current'}
    observations.append(o)
q4={'period':'2025Q4','published_by':'2026-03-09','classification':'current','metrics':{o['metric']:o for o in observations if o['period']=='2025Q4'},'source_url':SOURCES['fy2025_html'][1]}
ledger.append(q4);direct['2025Q4']=q4
quarters={q['period']:q for q in model['quarters']}
for e in ledger:
    total=sum(o['value'] for o in e['metrics'].values());expected=quarters[e['period']]['metrics']['other_revenue']['value']
    check(e['period']+' '+e['published_by']+' category sum',abs(total-expected)<1e-8,{'sum':total,'total_other':expected})
check('Q4 negative other category retained',q4['metrics']['other']['value']<0)
check('Q1 comparative classification difference retained',abs(q1_derived['metrics']['subscription_services']['value']-q1_later['metrics']['subscription_services']['value']-1.223)<1e-8)

def latest(period,cutoff,comparable=False):
    elig=[e for e in ledger if e['period']==period and e['published_by']<=cutoff and (not comparable or e['classification']=='current')]
    return max(elig,key=lambda e:e['published_by']) if elig else None

forecasts=[]
for i,q in enumerate(model['quarters'][1:],1):
    prev=model['quarters'][i-1];cutoff=(dt.date.fromisoformat(q['earnings_release_date'])-dt.timedelta(days=1)).isoformat()
    lag=latest(prev['period'],cutoff);assert lag
    lagtotal=sum(o['value'] for o in lag['metrics'].values());actual=q['metrics']['other_revenue']['value']
    methods={'flat_prior_total':lagtotal,'day_scaled_prior_total':lagtotal*q['days']/prev['days']}
    detail={};availability=[]
    if i>=2:
        prev2=model['quarters'][i-2];lag2=latest(prev2['period'],cutoff)
        if lag2:
            lag2total=sum(o['value'] for o in lag2['metrics'].values())
            methods['repeat_prior_total_growth']=lagtotal*lagtotal/lag2total
        comp1=latest(prev['period'],cutoff,True);comp2=latest(prev2['period'],cutoff,True)
        if comp1 and comp2:
            detail={}
            for k in ['subscription_services','transaction_revenue','other']:
                v1=comp1['metrics'][k]['value'];v2=comp2['metrics'][k]['value']
                detail[k]={'prior':v1,'prior2':v2,'forecast':v1*v1/v2 if v1>0 and v2>0 else None,
                           'availability':'available' if v1>0 and v2>0 else 'percentage-growth extrapolation not meaningful with nonpositive prior category',
                           'source_public_by':[comp1['published_by'],comp2['published_by']]}
            if all(v['forecast'] is not None for v in detail.values()):methods['repeat_prior_category_growth']=sum(v['forecast'] for v in detail.values())
    check(q['period']+' lagged source eligible',lag['published_by']<=cutoff)
    check(q['period']+' baseline equals Stage 3 prior other revenue',abs(lagtotal-prev['metrics']['other_revenue']['value'])<1e-8)
    forecasts.append({'period':q['period'],'cutoff':cutoff,'actual_other_revenue':actual,'actual_categories':{k:v['value'] for k,v in direct[q['period']]['metrics'].items()},
      'lag_snapshot_public_by':lag['published_by'],'lag_classification':lag['classification'],
      'methods':methods,'errors':{k:v/actual-1 for k,v in methods.items()},'category_growth_detail':detail})

names=sorted({k for e in forecasts for k in e['methods']});metrics={}
for name in names:
    sample=[e for e in forecasts if name in e['methods']]
    metrics[name]={'n':len(sample),'mape':st.mean(abs(e['errors'][name]) for e in sample),'mae_million':st.mean(abs(e['methods'][name]-e['actual_other_revenue']) for e in sample),'worst_abs_error':max(abs(e['errors'][name]) for e in sample)}
common=[e for e in forecasts if 'repeat_prior_total_growth' in e['methods']]
common_metrics={name:{'n':len(common),'mape':st.mean(abs(e['errors'][name]) for e in common)} for name in ['flat_prior_total','day_scaled_prior_total','repeat_prior_total_growth']}

# ARC annual guidance was publicly discussed on the August 5 call (page 9).
# The Q3 allocation below remains a timing assumption, not a company Q3 guide.
q3=next(e for e in forecasts if e['period']=='2026Q3')
non_arc_actual=q3['actual_other_revenue']-181.8
ordinary={k:v for k,v in q3['methods'].items()}
ordinary['remaining_fy_guidance_even_split']=(140-(quarters['2026Q1']['metrics']['other_revenue']['value']+quarters['2026Q2']['metrics']['other_revenue']['value']))/2
scenario_rows=[]
for arc_label,arc in [('defer_recognition_beyond_Q3',0),('FY_guidance_recognized_in_Q3',180),('75pct_disclosed_consideration_in_Q3',242.2*0.75),('all_consideration_in_Q3',242.2)]:
    for method,other in ordinary.items():
        total=other+arc
        scenario_rows.append({'arc_case':arc_label,'ordinary_method':method,'ordinary_estimate':other,'arc_estimate':arc,'total_other_revenue_estimate':total,
          'actual_other_revenue':q3['actual_other_revenue'],'error':total/q3['actual_other_revenue']-1,
          'conditional_on_Q3_recognition':arc>0,'annual_guide_public_by':'2026-08-05','cutoff':'2026-11-03'})
fractions=[{'recognition_fraction':f,'arc_revenue':242.2*f,'definition':'illustrative sensitivity, not an independently observed progress measure'} for f in [0,0.25,0.5,0.75,1]]
reserve_q3=next(e for e in reserve['evaluations'] if e['id']=='2026Q3_late')
retained=[]
for name,arc in [('no_ARC',0),('FY_guidance_in_Q3',180),('75pct_in_Q3',181.65)]:
    rldc=reserve_q3['rldc']['rldc_estimate']+arc
    retained.append({'case':name,'estimated_rldc':rldc,'actual_rldc':453.254,'error':rldc/453.254-1,
      'assumption':'ARC case has no incremental distribution costs; otherwise original lagged-cost bridge retained'})
check('75% scenario arithmetic',abs(242.2*0.75-181.65)<1e-8)
check('annual guidance does not use actual recognition amount',all(e['arc_estimate']!=181.8 for e in scenario_rows))
check('Q2 original classification is used before its release',next(e for e in forecasts if e['period']=='2025Q2')['lag_classification']=='IPO original')
check('Q3 2025 comparable Q1 split is original 2025 vintage',next(e for e in forecasts if e['period']=='2025Q3')['category_growth_detail']['subscription_services']['prior2']==q1_derived['metrics']['subscription_services']['value'])

result={'as_of':'2026-11-21','scope':'Other operating revenue; ARC scenarios conditional on recognition timing; not blind or live forecasts',
 'ledger':ledger,'source_observations':observations,'forecasts':forecasts,'baseline_metrics':metrics,'common_five_quarter_metrics':common_metrics,
 'arc_q3_scenarios':scenario_rows,'arc_fraction_sensitivity':fractions,
 'non_arc_q3_actual_scoring_only':non_arc_actual,'non_arc_ordinary_forecasts':ordinary,
 'q3_rldc_scenarios':retained,
 'arc_deferred_bridge':{'consideration_rounded':242.2,'recognized_q3':181.8,'remaining_arc_rounded':60.4,'total_company_deferred_revenue':61.794,'other_deferred_approximate':1.394},
 'checks_passed':sum(c['passed'] for c in checks),'checks_total':len(checks),'checks':checks}
save('other_revenue_model.json',result)
print(json.dumps({'checks_passed':result['checks_passed'],'checks_total':len(checks),'baselines':metrics,'common_sample':common_metrics,
 'q3_scenarios':[s for s in scenario_rows if s['arc_case']=='FY_guidance_recognized_in_Q3'],'rldc':retained,
 'quarterly_categories':[{ 'period':p,'values':{k:v['value'] for k,v in e['metrics'].items()}} for p,e in direct.items()]},indent=2))
assert all(c['passed'] for c in checks),[c for c in checks if not c['passed']]
