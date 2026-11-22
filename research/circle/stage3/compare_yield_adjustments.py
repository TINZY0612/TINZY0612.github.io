"""User-requested comparison of additive and proportional yield adjustments.

Exploratory extension after viewing the original six-quarter results. Original
Stage 3 rules and workbook are retained. Same data, cutoffs, day conventions and
lagged financial inputs; only the yield adjustment rule changes.
"""
import json
from pathlib import Path
import statistics as st

ROOT=Path(__file__).resolve().parent
model=json.loads((ROOT/'results/stage3_model.json').read_text())
daily=json.loads((ROOT/'results/daily_model_inputs.json').read_text())
rows=[];checks=[]
def check(name,ok):checks.append({'check':name,'passed':bool(ok)})
for e in model['evaluations']:
    ds=[r for r in daily if r['evaluation']==e['id'] and r['role']=='current']
    for benchmark in ['fund','sofr']:
        prior=e['lag_fund_weighted'] if benchmark=='fund' else e['lag_sofr_weighted_365']
        raw=e['raw_fund_estimate'] if benchmark=='fund' else e['estimates']['sofr']
        factor=e['lag_implied_yield']/prior
        proportional=raw*factor
        additive=e['estimates'][benchmark+'_lagged_spread']
        independent=sum(r['supply_million']*(r['fund_net_yield']/365 if benchmark=='fund' else r['sofr']/360)*factor for r in ds)
        current_yield=raw*365/e['supply_sum_million_days']
        check(e['id']+' '+benchmark+' independent daily sum',abs(proportional-independent)<1e-8)
        check(e['id']+' '+benchmark+' percentage-change identity',abs(current_yield*factor-e['lag_implied_yield']*(1+(current_yield/prior-1)))<1e-12)
        rows.append({'evaluation':e['id'],'period':e['period'],'phase':e['phase'],'cutoff':e['cutoff'],
          'benchmark':benchmark,'previous_circle_implied_yield':e['lag_implied_yield'],
          'previous_benchmark_weighted_yield':prior,'current_benchmark_weighted_yield':current_yield,
          'benchmark_relative_change':current_yield/prior-1,'proportional_factor':factor,
          'additive_adjusted_yield':current_yield+e['lag_implied_yield']-prior,
          'proportional_adjusted_yield':current_yield*factor,
          'additive_income_million':additive,'proportional_income_million':proportional,
          'difference_proportional_minus_additive_million':proportional-additive,
          'actual_income_million':e['actual_reserve_income'],
          'additive_error':additive/e['actual_reserve_income']-1,
          'proportional_error':proportional/e['actual_reserve_income']-1})
summary={}
for phase in ['early','late']:
    summary[phase]={}
    for benchmark in ['fund','sofr']:
        sample=[r for r in rows if r['phase']==phase and r['benchmark']==benchmark]
        summary[phase][benchmark]={}
        for method in ['additive','proportional']:
            summary[phase][benchmark][method]={'quarters':len(sample),
              'mape':st.mean(abs(r[method+'_error']) for r in sample),
              'mean_signed_error':st.mean(r[method+'_error'] for r in sample),
              'mae_million':st.mean(abs(r[method+'_income_million']-r['actual_income_million']) for r in sample),
              'worst_abs_error':max(abs(r[method+'_error']) for r in sample)}
        summary[phase][benchmark]['proportional_wins']=sum(abs(r['proportional_error'])<abs(r['additive_error']) for r in sample)
output={'scope':'Exploratory user-requested extension; retrospective current-history simulation, not blind validation',
  'original_method':'additive','challenger':'proportional','rows':rows,'summary':summary,
  'checks_passed':sum(r['passed'] for r in checks),'checks_total':len(checks),'checks':checks}
(ROOT/'results/yield_adjustment_comparison.json').write_text(json.dumps(output,indent=2),encoding='utf8')
print(json.dumps({'late_summary':summary['late'],'early_summary':summary['early'],
  'fund_rows':[r for r in rows if r['phase']=='late' and r['benchmark']=='fund'],
  'checks_passed':output['checks_passed'],'checks_total':len(checks)},indent=2))
assert all(r['passed'] for r in checks)
