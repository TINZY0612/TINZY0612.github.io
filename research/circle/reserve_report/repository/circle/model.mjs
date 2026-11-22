export function forwardIncome(snapshot, supplyChangePercent = 0, quotedRateChangeBps = 0) {
  if (!snapshot || !Array.isArray(snapshot.rows) || !Number.isFinite(snapshot.annual_spread)) throw new Error('Invalid forward snapshot');
  const supplyFactor = 1 + Number(supplyChangePercent) / 100;
  const rateChange = Number(quotedRateChangeBps) / 10000;
  if (!Number.isFinite(supplyFactor) || supplyFactor < 0 || !Number.isFinite(rateChange)) throw new Error('Invalid scenario assumption');
  return snapshot.rows.reduce((total, row) => {
    if (!Number.isFinite(row.supply_million) || !Number.isFinite(row.sofr)) throw new Error('Missing daily model input');
    const future = row.supply_status === 'flat_future_assumption';
    const supply = row.supply_million * (future ? supplyFactor : 1);
    const rate = row.sofr + (future ? rateChange : 0);
    return total + supply * (rate / 360 + snapshot.annual_spread / 365);
  }, 0);
}

export function estimateFromDaily(current, previous, lagIncome, lagReportedAverage, lagDays, benchmark, rule = 'additive') {
  if (!current.length || !previous.length || !(lagReportedAverage > 0) || !(lagDays > 0)) throw new Error('Incomplete calibration');
  const field = benchmark === 'sofr' ? 'sofr' : 'fund_net_yield';
  const scale = benchmark === 'sofr' ? 365 / 360 : 1;
  const oldYield = lagIncome / lagReportedAverage * 365 / lagDays;
  const oldExposure = previous.reduce((a, r) => a + r.supply_million, 0);
  const benchmarkYield = previous.reduce((a, r) => a + r.supply_million * r[field] * scale, 0) / oldExposure;
  if (!(benchmarkYield > 0)) throw new Error('Zero calibration benchmark');
  return current.reduce((a, r) => {
    const adjusted = rule === 'proportional' ? r[field] * scale * oldYield / benchmarkYield : r[field] * scale + oldYield - benchmarkYield;
    return a + r.supply_million * adjusted / 365;
  }, 0);
}
