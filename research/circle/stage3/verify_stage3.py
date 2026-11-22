"""Independently recompute headline results and test target contamination."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import statistics

ROOT=Path(__file__).resolve().parent
model=json.loads((ROOT/'results/stage3_model.json').read_text())
daily=json.loads((ROOT/'results/daily_model_inputs.json').read_text())
tests=[]
def test(name,passed):tests.append({'check':name,'passed':bool(passed)})
quarters={q['period']:q for q in model['quarters']}
for e in model['evaluations']:
    cur=[r for r in daily if r['evaluation']==e['id'] and r['role']=='current']
    lag=[r for r in daily if r['evaluation']==e['id'] and r['role']=='lag']
    qm=quarters[e['lag_period']]['metrics']
    effective=qm['reserve_income']['value']/qm['usdc_average']['value']*365/e['lag_days']
    # Independent mean-product expression, rather than the saved spread or predictions.
    lag_weighted=sum(r['sofr']*r['supply_million'] for r in lag)/sum(r['supply_million'] for r in lag)
    independent=sum(r['supply_million']*(effective/365+(r['sofr']-lag_weighted)/360) for r in cur)
    test(e['id']+' independent primary income',abs(independent-e['estimates']['sofr_lagged_spread'])<1e-8)
    test(e['id']+' all fund observations eligible',all(r['fund_filed']<=e['cutoff'] and r['fund_observation_date']<=r['date'] for r in cur+lag))
    bridge=e['rldc'];test(e['id']+' independent RLDC',abs(independent*(1-qm['total_costs']['value']/qm['reserve_income']['value'])+qm['other_revenue']['value']-bridge['rldc_estimate'])<1e-8)
for method,metrics in model['metrics']['late'].items():
    vals=[abs(e['estimates'][method]/e['actual_reserve_income']-1) for e in model['evaluations'] if e['phase']=='late']
    test(method+' independent MAPE',abs(statistics.mean(vals)-metrics['mape'])<1e-12)

spec=importlib.util.spec_from_file_location('analysis',ROOT/'analyze_stage3.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
original_read=mod.read;captured={}
def changed_read(p):
    j=original_read(p)
    if p.name=='stage2_data_model.json':
        j=copy.deepcopy(j);m=j['quarters'][-1]['metrics']
        for k,change in [('reserve_income',100),('other_revenue',50),('total_revenue',150),('total_costs',20),('rldc',130)]:m[k]['value']+=change
    return j
mod.read=changed_read;mod.save=lambda name,obj:captured.update({name:obj})
# main also writes the CSV: direct only this extra file to a bounded QA directory.
qa=ROOT/'qa';qa.mkdir(exist_ok=True);mod.OUT=qa
with contextlib.redirect_stdout(io.StringIO()):mod.main()
modified=captured['stage3_model.json']
for orig,changed in zip(model['evaluations'],modified['evaluations']):
    test(orig['id']+' forecasts unchanged after target-only financial shock',orig['estimates']==changed['estimates'] and orig['rldc']['rldc_estimate']==changed['rldc']['rldc_estimate'])
test('target shock changes evaluation errors',model['evaluations'][-1]['errors']!=modified['evaluations'][-1]['errors'])
result={'passed':sum(r['passed'] for r in tests),'total':len(tests),'checks':tests}
(ROOT/'results/independent_validation.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'passed':result['passed'],'total':result['total']}))
assert all(r['passed'] for r in tests),[r for r in tests if not r['passed']]
