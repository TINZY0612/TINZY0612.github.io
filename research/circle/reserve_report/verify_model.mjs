import assert from 'node:assert/strict';
import fs from 'node:fs';
import {forwardIncome,estimateFromDaily} from './site/circle/model.mjs';
const data=JSON.parse(fs.readFileSync(new URL('./site/circle/data/research.json',import.meta.url)));
const daily=JSON.parse(fs.readFileSync(new URL('../stage3/results/daily_model_inputs.json',import.meta.url)));
let checks=0;
for(const e of data.evaluations){
  const q=data.periods.find(q=>q.period===e.lag_period);
  const current=daily.filter(r=>r.evaluation===e.id&&r.role==='current');
  const previous=daily.filter(r=>r.evaluation===e.id&&r.role==='lag');
  for(const benchmark of ['sofr','fund'])for(const rule of ['additive','proportional']){
    const predicted=estimateFromDaily(current,previous,q.reserve_income,q.reported_average_supply,q.days,benchmark,rule);
    const key=benchmark+(rule==='additive'?'_lagged_spread':'_proportional');
    assert.ok(Math.abs(predicted-e.estimates[key])<1e-7,`${e.id} ${key}`);checks++;
  }
}
const sample={annual_spread:0,rows:[{supply_million:1000,sofr:.036,supply_status:'provider_observed'},{supply_million:100,sofr:.036,supply_status:'flat_future_assumption'}]};
assert.ok(Math.abs(forwardIncome(sample)-.11)<1e-12);checks++;
assert.ok(Math.abs(forwardIncome(sample,100)-.12)<1e-12);checks++;
assert.ok(Math.abs(forwardIncome(sample,0,100)-(.11+100*.01/360))<1e-12);checks++;
assert.equal(sample.rows[0].supply_million,1000);checks++;
assert.throws(()=>forwardIncome(sample,NaN));checks++;
const live=JSON.parse(fs.readFileSync(new URL('./site/circle/data/live.json',import.meta.url)));
assert.ok(Math.abs(forwardIncome(live)-live.reserve_income_million)<1e-7);checks++;
const result={passed:true,checks_passed:checks};fs.writeFileSync(new URL('./javascript_verification.json',import.meta.url),JSON.stringify(result,null,2));console.log(JSON.stringify(result));
