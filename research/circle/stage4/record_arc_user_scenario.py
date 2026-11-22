"""Record the user's ARC recognition case without replacing the earlier forecast."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
prior=ROOT/'results/2026-11-21_Q4_other_revenue_forecast.json'
before=hashlib.sha256(prior.read_bytes()).hexdigest()
benchmark=json.loads(prior.read_text())['forecast']
case={
 'recorded_as_of':'2026-11-21',
 'model_role':'User-directed working scenario, separate from the issuer-guidance benchmark',
 'period':'2026Q4',
 'new_arc_token_sales_assumed':0,
 'opening_existing_presale_deferred_revenue_usd_million':60.4,
 'existing_presale_revenue_recognized_usd_million':60.4,
 'closing_existing_presale_deferred_revenue_usd_million':0,
 'future_existing_presale_revenue_after_this_quarter_usd_million':0,
 'future_unannounced_token_sales_revenue_assumed_usd_million':0,
 'new_cash_from_release_of_existing_deferred_revenue_usd_million':0,
 'incremental_distribution_cost_assumed_usd_million':0,
 'incremental_rldc_before_other_costs_and_taxes_usd_million':60.4,
 'net_income_effect_usd_million':None,
 'recognition_timing_verified':False,
 'presale_remaining_balance_source':'https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm',
 'margin_and_guidance_source':'https://s206.q4cdn.com/265218871/files/doc_earnings/2026/q3/transcript/Q326-Earnings-Transcript.pdf',
 'benchmark_q4_total_other_revenue_midpoint_usd_million':benchmark['implied_q4_total_other_midpoint'],
 'mechanical_q4_total_other_revenue_midpoint_if_other_assumptions_unchanged_usd_million':benchmark['implied_q4_total_other_midpoint']+60.4,
 'interpretation':[
  'Q4 means the financial quarter reported at the next quarterly earnings release, not the calendar quarter containing that release.',
  'Full recognition in Q4 is the user-requested modeling assumption, not a disclosed recognition schedule or an independently validated prediction.',
  'The prior annual-guidance case includes no additional ARC recognition; this case adds $60.4m above that benchmark if other assumptions are unchanged.',
  'Recognized revenue and RLDC contribution are not necessarily after-tax profit.',
  'Zero future unannounced sales does not mean zero future staking, validator, services or incentive activity.',
  'New issuer announcements, filings and authenticated contract/wallet evidence can revise subsequent forecasts; preserve dated versions.',
  'Do not equate a token transfer with a sale, a cash receipt or recognized revenue.'
 ]
}
p=ROOT/'results/2026-11-21_Q4_ARC_user_scenario.json'
if p.exists():assert json.loads(p.read_text())==case,'Create a new dated version rather than overwrite a different forecast.'
else:p.write_text(json.dumps(case,indent=2),encoding='utf8')
assert case['opening_existing_presale_deferred_revenue_usd_million']-case['existing_presale_revenue_recognized_usd_million']==case['closing_existing_presale_deferred_revenue_usd_million']
assert hashlib.sha256(prior.read_bytes()).hexdigest()==before
assert case['net_income_effect_usd_million'] is None
print(json.dumps({'scenario_saved':str(p),'earlier_forecast_unchanged':True,'recognized_arc_revenue':60.4,'net_profit_not_assumed':True}))
