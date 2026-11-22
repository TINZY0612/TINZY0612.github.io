import { forwardIncome } from './model.mjs';

const $ = id => document.getElementById(id);
const fmt = (x, places = 3) => new Intl.NumberFormat('en-US', { minimumFractionDigits: places, maximumFractionDigits: places }).format(x);
const percent = (x, signed = false, places = 3) => `${signed && x >= 0 ? '+' : ''}${fmt(x * 100, places)}%`;
const quarter = value => `${value.slice(4)} ${value.slice(0, 4)}`;
const esc = value => String(value).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
let research, live;

const descriptions = {
  carry_forward: 'Baseline: previous reserve income multiplied by the ratio of quarter lengths. No current-quarter supply or rate update.',
  lagged_implied_yield: 'Current daily USDC supply multiplied by the prior quarter’s implied company yield. Supply changes, but the earned yield stays fixed.',
  sofr: 'Current daily USDC supply × available SOFR ÷ 360. No adjustment for Circle’s company-to-benchmark yield difference.',
  treasury_3m: 'Current daily USDC supply × the three-month Treasury quoted yield ÷ 365. A benchmark proxy rather than actual portfolio holdings.',
  sofr_lagged_spread: 'Primary specification: daily USDC supply and SOFR, adjusted by the previous quarter’s implied company yield gap. SOFR uses a 360-day accrual basis.',
  fund_lagged_spread: 'Fund challenger: daily USDC supply and the Circle Reserve Fund’s net seven-day yield, adjusted by the previous quarter’s company-to-fund gap.',
  sofr_proportional: 'Exploratory extension: preserve the previous company-yield-to-SOFR ratio. Tested later on the same six quarters; not an independent holdout.',
  fund_proportional: 'Exploratory extension: preserve the previous company-yield-to-fund-yield ratio. Tested later on the same six quarters; not an independent holdout.'
};

function lineChart(rows, method) {
  const W = Math.max(300, Math.round($('income-chart').clientWidth)), H = W<600?280:320, l = W<600?42:70, r = W<600?22:30, top = 25, bottom = 55;
  const values = rows.flatMap(e => [e.actual_reserve_income, e.estimates[method]]);
  const low = Math.floor((Math.min(...values) - 10) / 25) * 25, high = Math.ceil((Math.max(...values) + 10) / 25) * 25;
  const x = i => l + i * (W-l-r) / (rows.length-1), y = v => H-bottom-(v-low)/(high-low)*(H-top-bottom);
  let content = '';
  for (let i = 0; i <= 4; i++) {
    const v = low+(high-low)*i/4;
    content += `<line x1="${l}" x2="${W-r}" y1="${y(v)}" y2="${y(v)}" stroke="#2c3b4b"/><text x="${l-12}" y="${y(v)+4}" fill="#afbecd" text-anchor="end" font-size="14">${fmt(v, 0)}</text>`;
  }
  const points = field => rows.map((e, i) => `${x(i)},${y(field(e))}`).join(' ');
  content += `<polyline points="${points(e => e.actual_reserve_income)}" fill="none" stroke="#70b7ff" stroke-width="3"/><polyline points="${points(e => e.estimates[method])}" fill="none" stroke="#c9ff3b" stroke-width="2.5" stroke-dasharray="7 5"/>`;
  rows.forEach((e, i) => {
    const qlabel=W<600?`${e.period.slice(4)}<tspan x="${x(i)}" dy="17" font-size="12">${e.period.slice(0,4)}</tspan>`:quarter(e.period);
    content += `<circle cx="${x(i)}" cy="${y(e.actual_reserve_income)}" r="5" fill="#70b7ff"><title>${quarter(e.period)} actual $${fmt(e.actual_reserve_income)}m</title></circle><circle cx="${x(i)}" cy="${y(e.estimates[method])}" r="4" fill="#111b28" stroke="#c9ff3b" stroke-width="2"><title>${quarter(e.period)} estimate $${fmt(e.estimates[method])}m</title></circle><text x="${x(i)}" y="${H-(W<600?28:15)}" fill="#afbecd" text-anchor="middle" font-size="14">${qlabel}</text>`;
  });
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="chart-title chart-description"><title id="chart-title">Actual and estimated reserve income</title><desc id="chart-description">Six quarterly observations in USD millions. The accessible data table below provides exact values.</desc>${content}</svg>`;
}

function errorChart(rows, method) {
  const W=Math.max(300,Math.round($('error-chart').clientWidth)),H=210,l=W<600?32:70,r=20,zero=95,extent=65;
  const max = Math.max(.005, ...rows.map(e => Math.abs(e.errors[method]))) * 1.15;
  const x=i=>l+(i+.5)*(W-l-r)/rows.length;
  let content=`<line x1="${l}" x2="${W-r}" y1="${zero}" y2="${zero}" stroke="#8195a8"/><text x="${l-10}" y="${zero+5}" text-anchor="end" fill="#afbecd" font-size="14">0%</text>`;
  rows.forEach((e,i)=>{
    const v=e.errors[method],height=Math.max(1,Math.abs(v)/max*extent),y=v>=0?zero-height:zero;
    const bw=Math.min(48,(W-l-r)/rows.length*.35),fs=W<600?12:14;
    const shortQuarter=W<600?`${e.period.slice(4)} '${e.period.slice(2,4)}`:quarter(e.period);
    content+=`<rect x="${x(i)-bw/2}" y="${y}" width="${bw}" height="${height}" rx="3" fill="${v>=0?'#ffc181':'#c4a8ff'}"/><text x="${x(i)}" y="${v>=0?y-9:zero+height+19}" fill="#edf2f7" font-size="${fs}" text-anchor="middle">${percent(v,true,2)}</text><text x="${x(i)}" y="195" fill="#afbecd" font-size="${fs}" text-anchor="middle">${shortQuarter}</text>`;
  });
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Signed percentage error by quarter">${content}</svg>`;
}

function renderBacktest() {
  const method=$('method').value, phase=$('phase').value, metrics=research.metrics[phase][method];
  const rows=research.evaluations.filter(e=>e.phase===phase);
  $('method-description').textContent=descriptions[method];
  $('mape').textContent=percent(metrics.mape); $('mae').textContent=`$${fmt(metrics.mae_million)}m`; $('worst').textContent=percent(metrics.worst_abs_error);
  $('income-chart').innerHTML=lineChart(rows,method); $('error-chart').innerHTML=errorChart(rows,method);
  $('quarter-table').innerHTML=rows.map(e=>`<tr><td>${quarter(e.period)}</td><td>${e.cutoff}</td><td>${fmt(e.estimates[method])}</td><td>${fmt(e.actual_reserve_income)}</td><td>${fmt(e.estimates[method]-e.actual_reserve_income)}</td><td class="${e.errors[method]>=0?'positive':'negative'}">${percent(e.errors[method],true)}</td></tr>`).join('');
  $('method-table').innerHTML=research.methods.map(m=>{const s=research.metrics[phase][m.id];return `<tr class="${m.id===method?'chosen':''}"><td><button class="method-button" data-method="${m.id}" type="button">${esc(m.label)}</button></td><td class="${m.category==='exploratory'?'exploratory':''}">${esc(m.category)}</td><td>${percent(s.mape)}</td><td>${fmt(s.mae_million)}</td><td>${percent(s.worst_abs_error)}</td></tr>`;}).join('');
  renderWorked();
}

function step(number,title,text,math,full=false) {
  return `<article class="step ${full?'full':''}"><p class="step-label">STEP ${number}</p><h3>${title}</h3><p>${text}</p><p class="equation">${math}</p></article>`;
}

function renderWorked() {
  const e=research.evaluations.find(e=>e.period===$('worked-quarter').value && e.phase===$('phase').value);
  const prev=research.periods.find(q=>q.period===e.lag_period), q=research.periods.find(q=>q.period===e.period);
  const sum=e.supply_sum_million_days, correction=sum*e.fund_spread/365;
  const source=q.financial_sources.find(x=>x.metric==='reserve_income')?.source_url || 'https://www.sec.gov/Archives/edgar/data/1876042/000187604226000062/crcl-20251231.htm';
  $('walkthrough').innerHTML=
    step(1,'Infer the previous company yield',`${quarter(prev.period)} reported reserve income divided by reported average USDC, annualized over ${prev.days} days. Both are lagged public financial inputs.`,`${fmt(prev.reserve_income,6)} ÷ ${fmt(prev.reported_average_supply,3)} × 365 ÷ ${prev.days}<br>= ${percent(e.lag_implied_yield,false,6)}`)+
    step(2,'Build the daily balance exposure',`Sum ${q.days} calendar-date USDC balances. Daily balances provide the weights, including weekends.`,`${fmt(sum,6)} million USDC days<br>÷ ${q.days} = $${fmt(sum/q.days,3)}m average USDC`)+
    step(3,'Read and weight the public fund yields',`Original monthly filings eligible by ${e.cutoff}; latest observation on or before each economic date. Longest target-quarter carry: ${e.fund_max_carry_days_current} days.`,`Previous weighted fund yield: ${percent(e.lag_fund_weighted,false,6)}<br>Current weighted fund yield: ${percent(e.current_weighted_fund,false,6)}`)+
    step(4,'Carry the previous yield gap',`Subtract the previous weighted fund yield from the previous implied company yield. A percentage-point gap is not a relative percentage reduction.`,`${percent(e.lag_implied_yield,false,6)} − ${percent(e.lag_fund_weighted,false,6)}<br>= ${fmt(e.fund_spread*100,6)} percentage points<br>= ${fmt(e.fund_spread*10000,4)} basis points`)+
    step(5,'Calculate the fund estimate',`Raw income is the sum of daily USDC × assigned annual fund yield ÷ 365. Add the lagged gap correction.`,`Raw fund estimate: $${fmt(e.raw_fund_estimate,6)}m<br>Gap correction: $${fmt(correction,6)}m<br>Fund estimate: $${fmt(e.estimates.fund_lagged_spread,6)}m`)+
    step(6,'Calculate the SOFR estimate',`Use SOFR ÷ 360 for daily accrual; convert the lagged weighted benchmark by 365/360 before calculating the yield gap.`,`Raw SOFR: $${fmt(e.estimates.sofr,6)}m<br>Annual gap: ${fmt(e.sofr_spread*100,6)} percentage points<br>SOFR estimate: $${fmt(e.estimates.sofr_lagged_spread,6)}m`)+
    step(7,'Score against the actual after publication',`Earnings release: ${e.earnings_release}. Prediction cutoff: ${e.cutoff}. The exact scoring actual is from the original financial filing. <a href="${esc(source)}">Open filing</a>.`,`Reported reserve income: $${fmt(e.actual_reserve_income,6)}m<br>Fund signed error: ${percent(e.errors.fund_lagged_spread,true,6)}<br>SOFR signed error: ${percent(e.errors.sofr_lagged_spread,true,6)}`,true);
  const report=research.fund_reports.find(f=>f.report_date===q.end);
  const observation=research.fund_observations.find(f=>f.date===q.end);
  const eligible=report && report.filed<=e.cutoff;
  $('fund-example').innerHTML=report?`<p><a href="${esc(report.url)}">Open ${esc(report.report_date.slice(0,7))} original fund filing</a>, filed ${report.filed}; ${report.yield_observations} business-date observations.${observation?` The ${q.end} net-yield observation is ${percent(observation.net_yield,false,2)} annually.`:''} ${eligible?'This report was eligible at the selected cutoff. The model uses every eligible daily observation, not this endpoint alone.':'This report was NOT public at the selected cutoff and is excluded from that estimate; the model carries the latest observation from an earlier eligible filing.'}</p>`:'';
}

function renderSupply() {
  $('supply-table').innerHTML=research.periods.map(p=>`<tr><td>${quarter(p.period)}</td><td>${fmt(p.provider_average_supply/1000)}</td><td>${fmt(p.reported_average_supply/1000)}</td><td>${percent(p.average_gap,true)}</td><td>${percent(p.end_gap,true)}</td></tr>`).join('');
}

function renderForward() {
  if (!live) return;
  const supply=Number($('supply-change').value),rate=Number($('rate-change').value);
  $('supply-output').textContent=`${supply>0?'+':''}${supply}%`; $('rate-output').textContent=`${rate>0?'+':''}${rate} bp`;
  const income=forwardIncome(live,supply,rate);
  $('forward-income').textContent=`$${fmt(income,3)}m`;
  $('observed-split').textContent=`${live.observed_days} observed supply days through ${live.observed_supply_through} · ${live.projected_days} projected days`;
  $('forward-base').textContent=`Published base: $${fmt(live.reserve_income_million,3)}m. Latest USDC: $${fmt(live.last_supply_million/1000,3)}bn. Latest available SOFR: ${percent(live.last_sofr,false,2)}.`;
  const age=(Date.now()-new Date(live.as_of_utc).getTime())/3600000;
  $('live-status').classList.toggle('stale',age>36);
  $('live-status').textContent=`Snapshot ${new Date(live.as_of_utc).toISOString().replace('T',' ').slice(0,19)} UTC. Latest SOFR effective date ${live.latest_sofr_effective_date}.${age>36?' This cache is over 36 hours old; inspect the update workflow.':''}`;
}

async function loadLive() {
  $('reload-cache').disabled=true;
  try {
    const response=await fetch(`data/live.json?t=${Date.now()}`,{cache:'no-store'});
    if(!response.ok) throw new Error(`HTTP ${response.status}`);
    const candidate=await response.json();
    if(candidate.period!=='2026Q4' || candidate.actual!==null || candidate.rows?.length!==92) throw new Error('Unexpected model period or schema');
    const calculated=forwardIncome(candidate);
    if(Math.abs(calculated-candidate.reserve_income_million)>.000001) throw new Error('Snapshot arithmetic check failed');
    live=candidate; renderForward();
  } catch(error) {
    $('live-status').classList.add('stale');
    $('live-status').textContent=`Could not reload the published snapshot (${error.message}). ${live?'The last loaded valid snapshot is retained.':'The historical research remains available; no missing data are treated as zero.'}`;
  } finally {$('reload-cache').disabled=false;}
}

async function start() {
  try {
    const response=await fetch('data/research.json');
    if(!response.ok) throw new Error(`HTTP ${response.status}`);
    research=await response.json();
    if(research.evaluations?.length!==12 || research.periods?.length!==7) throw new Error('Historical dataset coverage changed');
    $('method').innerHTML=research.methods.map(m=>`<option value="${m.id}">${esc(m.label)}${m.category==='exploratory'?' · exploratory':''}</option>`).join('');
    $('method').value='sofr_lagged_spread';
    $('worked-quarter').innerHTML=research.evaluations.filter(e=>e.phase==='late').map(e=>`<option value="${e.period}">${quarter(e.period)}</option>`).join(''); $('worked-quarter').value='2026Q3';
    $('method').addEventListener('change',renderBacktest); $('phase').addEventListener('change',renderBacktest); $('worked-quarter').addEventListener('change',renderWorked);
    let resizeTimer; window.addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(renderBacktest,150);});
    $('method-table').addEventListener('click',event=>{const button=event.target.closest('[data-method]');if(button){$('method').value=button.dataset.method;renderBacktest();}});
    $('supply-change').addEventListener('input',renderForward);$('rate-change').addEventListener('input',renderForward);
    $('reset-scenario').addEventListener('click',()=>{$('supply-change').value=0;$('rate-change').value=0;renderForward();});
    $('reload-cache').addEventListener('click',loadLive);
    renderBacktest();renderSupply();
    $('load-status').textContent='Archived research loaded · 6 target quarters · 6 original methods + 2 exploratory variants · financial and fund inputs filtered by cutoff date';
  } catch(error) {
    $('load-status').textContent=`The research data could not load (${error.message}). Read the report or download the CSV instead.`; $('load-status').classList.add('error');
  }
  await loadLive();
}
start();
