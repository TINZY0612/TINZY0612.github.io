"""Independent arithmetic, source-integrity and exported-workbook controls."""
import datetime as dt
import gzip
import hashlib
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results';CIRCLE=ROOT.parent
checks=[]
def ck(name,condition):
    checks.append({'name':name,'passed':bool(condition)})
def read(p):
    p=Path(p)
    if p.exists():return json.loads(p.read_text(encoding='utf-8'))
    return json.loads(gzip.open(str(p)+'.gz','rt',encoding='utf-8').read())
def digest(p):
    p=Path(p);opener=gzip.open if p.suffix=='.gz' else open
    h=hashlib.sha256()
    with opener(p,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()
reg=read(OUT/'subscription_regression.json');qs=reg['quarterly_inputs'];daily=reg['daily_inputs'];fit=reg['primary_levels_ols']
ck('638 distinct dates and seven quarterly targets',len(daily)==638 and len({r['date'] for r in daily})==638 and len(qs)==7)
for q in qs:
    rows=[r for r in daily if r['period']==q['period']]
    ck(q['period']+' daily averages independently reproduce factors',len(rows)==q['days'] and np.allclose(
        [np.mean([r['stablecoin_usd'] for r in rows])/1e9,np.mean([r['btc_usd_close'] for r in rows])/1000,np.mean([r['usdc_par_usd']/r['stablecoin_usd'] for r in rows])*100],
        [q['stablecoin_mean_usd_billion'],q['btc_mean_usd_thousand'],q['usdc_mean_share_pct']],rtol=1e-12))
y=np.array([q['services_actual_usd_million'] for q in qs]);x=np.array([[q[k] for k in ['stablecoin_mean_usd_billion','btc_mean_usd_thousand','usdc_mean_share_pct']] for q in qs])
z=(x-x.mean(0))/x.std(0);a=np.column_stack([np.ones(len(y)),z]);beta=np.linalg.solve(a.T@a,a.T@y);pred=a@beta
r2=1-sum((y-pred)**2)/sum((y-y.mean())**2)
loo=[]
for i in range(len(y)):
    mask=np.arange(len(y))!=i;b=np.linalg.solve(a[mask].T@a[mask],a[mask].T@y[mask]);loo.append(a[i]@b)
ck('scaled independent normal equations match SVD fit and R2',np.allclose(pred,fit['fitted'],rtol=1e-10) and abs(r2-fit['r_squared'])<1e-12)
ck('full leave-one-quarter-out refits match predictions',np.allclose(loo,fit['loo_predictions'],rtol=1e-9) and abs(np.mean(abs((np.array(loo)-y)/y))-fit['loo_mape'])<1e-10)
ck('adjusted R2 has correct three residual degrees of freedom',abs((1-(1-r2)*6/3)-fit['adjusted_r_squared'])<1e-12)
for filename,expected in reg['source_hashes'].items():ck('regression input SHA256 '+filename,digest(CIRCLE/filename)==expected)

# Stream-hash raw payloads, including decompressed archives, rather than trusting
# checks performed by the analysis itself. Error responses are retained too.
manifest=read(ROOT/'source_manifest.json');received=[e for e in manifest if e.get('status')=='received' and e.get('sha256')]
bad=[]
for e in received:
    p=ROOT/e['file']
    if not p.exists():p=Path(str(p)+'.gz')
    if not p.exists() or digest(p)!=e['sha256']:bad.append(e['name'])
ck('every received source manifest hash matches payload',not bad)
arc=read(OUT/'archive_manifest.json');bad_archive=[e['file'] for e in arc['files'] if digest(ROOT/e['file'])!=e['uncompressed_sha256']]
ck('every lossless archive matches its original SHA256',not bad_archive)

fund=read(OUT/'usyc_fund_and_services_analysis.json');reports=fund['reports']
ck('438 ordered consecutive USYC report rounds',len(reports)==438 and all(b['round_id']==a['round_id']+1 for a,b in zip(reports,reports[1:])))
ck('USYC share price units independently reproduce NAV and fee',all(abs(r['fee_shares']*r['price_usd']-r['performance_fee_usd'])<1e-6 and abs(r['share_supply']*r['price_usd']-r['aum_proxy_usd'])<1e-3 and abs(r['performance_fee_usd']-.1*r['gross_income_usd'])<.01 for r in reports))
for q in fund['quarterly']:
    rows=[r for r in reports if r['observed_at_utc'][:4]+ 'Q'+str((int(r['observed_at_utc'][5:7])-1)//3+1)==q['period']]
    ck(q['period']+' observation-time fee rollup',abs(sum(r['performance_fee_usd'] for r in rows)/1e6-q['performance_fees_usd_million'])<1e-10)
ff=read(OUT/'2026-11-21_Q4_USYC_fee_forecast.json');driver=read(OUT/'usyc_forward_build_inputs.json')
ck('prospective USYC forecast has unknown actual and unchanged source',ff['actual'] is None and digest(CIRCLE/'stage4/raw/usyc_historical_prices.json')==ff['source_sha256'])
pace=driver['known_fee_usd_million']+driver['trailing_fee_usd_million']/28*41
nav=driver['known_fee_usd_million']+driver['last_aum_usd_million']*(driver['trailing_gross_income_usd_million']/driver['trailing_mean_aum_usd_million']*365/28)*.1*41/365
ck('independent Q4 USYC scenario arithmetic',abs(pace-ff['flat_trailing_daily_fee_q4_estimate_usd_million'])<1e-12 and abs(nav-ff['flat_last_aum_and_trailing_yield_q4_estimate_usd_million'])<1e-12)

flow=read(OUT/'usdc_flow_analysis.json');control=read(OUT/'usdc_flow_controls.json');logs=read(OUT/'usdc_q3_2026_mint_burn_logs.json')
mint=sum(int(l['data'],16) for l in logs['logs'] if l['topics'][0]==logs['mint_topic']);burn=sum(int(l['data'],16) for l in logs['logs'] if l['topics'][0]==logs['burn_topic'])
ck('independent integer stock-flow reconciliation',int(control['raw_supplies']['2026-07-01'],16)+mint-burn==int(control['raw_supplies']['2026-10-01'],16) and abs(mint/1e12-flow['quarter']['amounts_usd_million']['mint'])<1e-8)
del logs
analysis=read(OUT/'onchain_analysis_checks.json');ck('bounded chain analysis controls all passed',analysis['checks_passed']==analysis['checks_total'] and all(c['passed'] for c in analysis['checks']))
sup=read(OUT/'supply_projection_forecast.json');ck('all early forecast calibrations public before cutoffs',all(r['base_public_by']<=r['cutoff'] for r in sup['rows']))
ck('reserve aggregate errors independently recompute',all(abs(np.mean([abs(r['methods'][m]/r['actual_reserve_income']-1) for r in sup['rows']])-v['mape'])<1e-12 for m,v in sup['metrics'].items()))

book=CIRCLE/'outputs/01a1fcd4-2a0f-7c92-a89f-a871c89c1db7/Circle_Onchain_Extensions_and_Regression.xlsx';ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(book) as zf:
    sheets=[n for n in zf.namelist() if n.startswith('xl/worksheets/sheet') and n.endswith('.xml')]
    trees=[ET.fromstring(zf.read(n)) for n in sorted(sheets)]
    errors=[c.attrib['r'] for t in trees for c in t.findall('.//s:c',ns) if c.attrib.get('t')=='e']
    ck('three exported worksheets and no cached formula error cells',len(trees)==3 and not errors)
    def cells(t):return {c.attrib['r']:c for c in t.findall('.//s:c',ns)}
    rc,oc=cells(trees[0]),cells(trees[1])
    def value(c):return float(c.find('s:v',ns).text)
    ck('exported workbook cached R2, adjusted R2 and LOO match',abs(value(rc['D5'])-fit['r_squared'])<1e-10 and abs(value(rc['G5'])-fit['adjusted_r_squared'])<1e-10 and abs(value(rc['J5'])-fit['loo_mape'])<1e-10)
    ck('exported workbook contains live OLS and forecast formulas',all(rc[k].find('s:f',ns) is not None for k in ['D5','G5','E44','E45','K9']) and all(oc[k].find('s:f',ns) is not None for k in ['D11','H35','H39']))
    ck('exported workbook has latest reserve forecast results',abs(value(oc['E75'])-sup['metrics']['flat_last_supply']['mape'])<1e-12)
qa=read(OUT/'workbook_qa.json');ck('workbook independent formula and input-change controls passed',all(c['passed'] for c in qa['checks']) and 'matched 0 entries' in qa['error_scan'])
result={'checks_passed':sum(x['passed'] for x in checks),'checks_total':len(checks),'checks':checks,'source_responses_hashed':len(received),'archives_hashed':len(arc['files']),'hash_failures':bad+bad_archive,'workbook_sha256':digest(book),'prior_dated_forecast_sha256':{n:digest(CIRCLE/'stage4/results'/n) for n in ['2026-11-21_Q4_other_revenue_forecast.json','2026-11-21_Q4_ARC_user_scenario.json']},'limitations':['Native Excel application recalculation not tested; formula evaluation, export caches and changed-input recalculation tested with ArtifactTool.']}
(OUT/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:result[k] for k in ['checks_passed','checks_total','source_responses_hashed','archives_hashed','hash_failures']},indent=2));assert all(x['passed'] for x in checks)
