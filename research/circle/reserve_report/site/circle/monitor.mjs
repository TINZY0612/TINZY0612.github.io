// Pure presentation calculations for the versioned monitor feed.
export const monitorMethodLabel = {
  fund_proportional: 'Fund yield with prior yield ratio',
  sofr_lagged_spread: 'SOFR with prior yield gap'
};

function finite(value) {
  if (!Number.isFinite(value)) throw new Error('Missing or non-finite monitor input');
  return value;
}

export function monitorIncome(snapshot, method = 'fund_proportional', supplyChangePercent = 0, yieldChangeBps = 0) {
  if (!snapshot || !Array.isArray(snapshot.rows) || !monitorMethodLabel[method]) throw new Error('Invalid monitor snapshot');
  const factor = 1 + finite(Number(supplyChangePercent)) / 100;
  const change = finite(Number(yieldChangeBps)) / 10000;
  if (factor < 0) throw new Error('Negative scenario supply');
  if (method === 'fund_proportional' && !snapshot.primary_available) return null;
  const coefficient = finite(method === 'fund_proportional' ? snapshot.fund_yield_ratio : snapshot.sofr_annual_gap);
  return snapshot.rows.reduce((total, row) => {
    const future = row.supply_status === 'flat_future_assumption';
    if (!future && row.supply_status !== 'provider_observed') throw new Error('Unknown supply status');
    const balance = finite(row.supply_million) * (future ? factor : 1);
    const rate = finite(method === 'fund_proportional' ? row.fund_net_yield : row.sofr) + (future ? change : 0);
    return total + balance * (method === 'fund_proportional' ? rate * coefficient / 365 : rate / 360 + coefficient / 365);
  }, 0);
}

export function validateMonitor(view) {
  if (view?.schema_version !== 1 || !Array.isArray(view.targets) || !Array.isArray(view.validations)) throw new Error('Unexpected monitor schema');
  if (!Number.isFinite(Date.parse(view.as_of_utc))) throw new Error('Missing monitor timestamp');
  for (const target of view.targets) {
    const snapshot = target.forecast || target.last_good_forecast;
    if (!snapshot) continue;
    if (!/^\d{4}Q[1-4]$/.test(snapshot.period) || snapshot.period !== target.period) throw new Error('Invalid monitor period');
    const year = Number(snapshot.period.slice(0, 4)), q = Number(snapshot.period.slice(5));
    const start = Date.UTC(year, q * 3 - 3, 1), next = Date.UTC(year, q * 3, 1);
    const days = (next - start) / 86400000;
    finite(snapshot.estimates_million?.sofr_lagged_spread);
    if (snapshot.primary_available) finite(snapshot.estimates_million?.fund_proportional);
    if (snapshot.rows?.length !== days || snapshot.observed_days + snapshot.projected_days !== days) throw new Error('Incomplete monitor quarter');
    snapshot.rows.forEach((row, i) => {
      if (row.date !== new Date(start + i * 86400000).toISOString().slice(0, 10)) throw new Error('Duplicate or missing monitor date');
    });
    for (const [method, estimate] of Object.entries(snapshot.estimates_million || {})) {
      const calculated = monitorIncome(snapshot, method);
      if (calculated === null || Math.abs(calculated - finite(estimate)) > 1e-6) throw new Error('Monitor arithmetic check failed');
    }
  }
  for (const row of view.validations) {
    finite(row.estimate_million); finite(row.difference_million);
    if (row.actual_million <= 0 || !Number.isFinite(row.actual_million)) throw new Error('Invalid scored actual');
    if (Math.abs(row.estimate_million / row.actual_million - 1 - finite(row.signed_error)) > 1e-10) throw new Error('Validation arithmetic check failed');
    if (Math.abs(row.estimate_million - row.actual_million - row.difference_million) > 1e-6) throw new Error('Validation dollar difference check failed');
  }
  return view;
}

export function currentMonitorTarget(view) {
  const date = new Date(view.as_of_utc);
  const period = `${date.getUTCFullYear()}Q${Math.floor(date.getUTCMonth() / 3) + 1}`;
  return view.targets.find(target => target.period === period) || null;
}
