"""Independent checks of the report and dashboard publication data."""
import datetime as dt
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import statistics as st
from lxml import html

ROOT=Path(__file__).resolve().parent
CIRCLE=ROOT.parent
SITE=ROOT/'site/circle'
d=json.loads((SITE/'data/research.json').read_text())
original=json.loads((CIRCLE/'stage3/results/stage3_model.json').read_text())
daily=json.loads((CIRCLE/'stage3/results/daily_model_inputs.json').read_text())
checks=[]


def ck(name, condition):
    checks.append({'check':name,'passed':bool(condition)})


def close(a,b):return math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-7)


ck('seven quarters, twelve evaluations, eight methods',len(d['periods'])==7 and len(d['evaluations'])==12 and len(d['methods'])==8)
ck('638 unique displayed daily observations',len(d['daily'])==638 and len({x['date'] for x in d['daily']})==638)
for e in d['evaluations']:
    lag=next(p for p in d['periods'] if p['period']==e['lag_period'])
    cur=[r for r in daily if r['evaluation']==e['id'] and r['role']=='current']
    prev=[r for r in daily if r['evaluation']==e['id'] and r['role']=='lag']
    ck(e['id']+' complete current and lag daily coverage',len(cur)==e['days'] and len(prev)==lag['days'])
    ck(e['id']+' fund dates eligible',all(r['fund_filed']<=e['cutoff'] and r['fund_observation_date']<=r['date'] for r in cur+prev))
    y=lag['reserve_income']/lag['reported_average_supply']*365/lag['days']
    exposure=sum(r['supply_million'] for r in cur)
    old_exposure=sum(r['supply_million'] for r in prev)
    values={
        'carry_forward':lag['reserve_income']*len(cur)/lag['days'],
        'lagged_implied_yield':exposure*y/365,
        'sofr':sum(r['supply_million']*r['sofr']/360 for r in cur),
        'treasury_3m':sum(r['supply_million']*r['treasury_3m']/365 for r in cur)}
    for benchmark,field,scale in [('sofr','sofr',365/360),('fund','fund_net_yield',1)]:
        prior=sum(r['supply_million']*r[field]*scale for r in prev)/old_exposure
        values[benchmark+'_lagged_spread']=sum(r['supply_million']*(r[field]*scale+y-prior)/365 for r in cur)
        values[benchmark+'_proportional']=sum(r['supply_million']*r[field]*scale*y/prior/365 for r in cur)
    for method,value in values.items():
        ck(e['id']+' '+method+' independent arithmetic',close(value,e['estimates'][method]))
        ck(e['id']+' '+method+' signed error',close(value/e['actual_reserve_income']-1,e['errors'][method]))
    ck(e['id']+' target is scoring only',e['actual_reserve_income']==next(p['reserve_income'] for p in d['periods'] if p['period']==e['period']))
for phase in ['early','late']:
    rows=[e for e in d['evaluations'] if e['phase']==phase]
    for method in d['methods']:
        k=method['id'];errors=[abs(e['errors'][k]) for e in rows]
        ck(phase+' '+k+' mean and worst error',close(st.mean(errors),d['metrics'][phase][k]['mape']) and close(max(errors),d['metrics'][phase][k]['worst_abs_error']))
for source in d['source_hashes']:
    ck('immutable source '+source['path'],hashlib.sha256((CIRCLE/source['path']).read_bytes()).hexdigest()==source['sha256'])
live=json.loads((SITE/'data/live.json').read_text())
value=sum(r['supply_million']*(r['sofr']/360+live['annual_spread']/365) for r in live['rows'])
ck('current scenario arithmetic',close(value,live['reserve_income_million']))
ck('forward excluded from accuracy metrics',all(e['period']!='2026Q4' for e in d['evaluations']) and live['actual'] is None)
ck('forward has 92 calendar dates',len(live['rows'])==92 and len({r['date'] for r in live['rows']})==92)
ck('current-day supply excluded',live['observed_supply_through']<live['as_of_utc'][:10])
ck('observed plus projected days',live['observed_days']+live['projected_days']==92)
for file in ['index.html','report.html']:
    tree=html.fromstring((SITE/file).read_bytes());ids=tree.xpath('//*[@id]/@id')
    ck(file+' unique ids',len(ids)==len(set(ids)))
    bad=[]
    for path in tree.xpath('//@href|//@src'):
        if path.startswith(('http:','https:','mailto:','tel:','/','data:')):continue
        if path.startswith('#'):
            if path[1:] not in ids:bad.append(path)
        elif not (SITE/path.split('#')[0].split('?')[0]).exists():bad.append(path)
    ck(file+' local assets and anchors exist',not bad)
# Verify the smaller new feed agrees with the full feed in the same-day archive.
p=CIRCLE/'data_inventory';mp=p/json.loads((p/'latest_access_check.json').read_text())['manifest'];manifest=json.loads(mp.read_text())
entry=next(x for x in manifest['sources'] if x['name']=='usdc_supply')
full=json.loads(gzip.decompress((p/entry['raw_path']).read_bytes()))
full_map={int(x['date']):x['circulating']['peggedUSD'] for x in full['tokens']}
compact=json.loads((ROOT/'usdc_compact_api.json').read_text())
shared=[x for x in compact if int(x['date']) in full_map and '2026-07-01'<=dt.datetime.fromtimestamp(int(x['date']),dt.timezone.utc).date().isoformat()<='2026-11-21']
differences=[abs(x['totalCirculating']['peggedUSD']-full_map[int(x['date'])]) for x in shared]
ck('compact feed matches full feed over July to November shared dates',len(shared)==144 and max(differences,default=math.inf)<.01)
result={'passed':all(x['passed'] for x in checks),'checks_total':len(checks),'checks_passed':sum(x['passed'] for x in checks),'compact_full_shared_dates':len(shared),'compact_full_max_difference_usd':max(differences,default=None),'checks':checks}
(ROOT/'verification.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='checks'}));print('FAILED',json.dumps([x for x in checks if not x['passed']]))
assert result['passed']
