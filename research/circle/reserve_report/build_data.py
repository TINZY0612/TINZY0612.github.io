"""Publish a compact reserve-only view of the immutable Stage 2/3 research."""
import csv
import datetime as dt
import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CIRCLE = ROOT.parent
SITE = ROOT / "site" / "circle"
DATA = SITE / "data"
DATA.mkdir(parents=True, exist_ok=True)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False), encoding="utf-8")


m = read(CIRCLE / "stage3/results/stage3_model.json")
s = read(CIRCLE / "stage2/results/stage2_data_model.json")
comparison = read(CIRCLE / "stage3/results/yield_adjustment_comparison.json")
daily = read(CIRCLE / "stage3/results/daily_model_inputs.json")
calendar = read(CIRCLE / "stage2/earnings_calendar.json")
methods = [
    ("carry_forward", "Prior income with day adjustment", "baseline"),
    ("lagged_implied_yield", "Supply with prior earned yield", "baseline"),
    ("sofr", "Supply with uncalibrated SOFR", "benchmark"),
    ("treasury_3m", "Supply with three month Treasury yield", "benchmark"),
    ("sofr_lagged_spread", "SOFR with prior yield gap", "primary"),
    ("fund_lagged_spread", "Fund yield with prior yield gap", "challenger"),
    ("sofr_proportional", "SOFR with prior yield ratio", "exploratory"),
    ("fund_proportional", "Fund yield with prior yield ratio", "exploratory"),
]
evals = []
for original in m["evaluations"]:
    e = {k: v for k, v in original.items() if k not in ("rldc", "next_bucket_estimates_fixed_spreads", "next_bucket_estimates_recalibrated_spreads")}
    e["estimates"] = dict(e["estimates"])
    for c in comparison["rows"]:
        if c["evaluation"] == e["id"]:
            e["estimates"][c["benchmark"] + "_proportional"] = c["proportional_income_million"]
    e["errors"] = {k: v / e["actual_reserve_income"] - 1 for k, v in e["estimates"].items()}
    for role in ("current", "lag"):
        rows = [r for r in daily if r["evaluation"] == e["id"] and r["role"] == role]
        total = sum(r["supply_million"] for r in rows)
        e[role + "_weighted_fund"] = sum(r["supply_million"] * r["fund_net_yield"] for r in rows) / total
        e[role + "_weighted_sofr_365"] = sum(r["supply_million"] * r["sofr"] * 365 / 360 for r in rows) / total
    evals.append(e)

metrics = {}
for phase in ("early", "late"):
    rows = [e for e in evals if e["phase"] == phase]
    metrics[phase] = {}
    for method, _, _ in methods:
        err = [e["errors"][method] for e in rows]
        metrics[phase][method] = {"n": len(rows), "mape": statistics.mean(abs(x) for x in err),
            "mae_million": statistics.mean(abs(e["estimates"][method]-e["actual_reserve_income"]) for e in rows),
            "worst_abs_error": max(abs(x) for x in err)}

periods = []
for q, checkpoint in zip(m["quarters"], s["supply_checkpoints"]):
    observations = [o for o in s["source_observations"] if o["period"] == q["period"] and o["metric"] in ("reserve_income", "usdc_average")]
    periods.append({"period": q["period"], "start": q["start"], "end": q["end"], "days": q["days"],
        "reserve_income": q["metrics"]["reserve_income"]["value"], "reported_average_supply": q["metrics"]["usdc_average"]["value"],
        "reported_end_supply": q["metrics"]["usdc_end"]["value"], "reported_implied_yield": q["metrics"]["reserve_income"]["value"] / q["metrics"]["usdc_average"]["value"] * 365 / q["days"],
        "provider_average_supply": checkpoint["provider_average_as_labeled"] / 1e6,
        "provider_end_comparison_supply": checkpoint["provider_following_date_bucket"] / 1e6,
        "attested_end_supply": checkpoint["official_circulation"] / 1e6,
        "average_gap": checkpoint["average_gap_pct"], "end_gap": checkpoint["following_bucket_gap_pct"],
        "financial_sources": observations, "checkpoint_source_pdf": checkpoint["source_pdf"]})

f = read(CIRCLE / "stage5/rldc/results/2026-11-21_Q4_RLDC_forecast.json")
forward_keys = ["as_of", "period", "actual", "observed_supply_through", "observed_calendar_days", "projected_calendar_days", "last_observed_usdc_million", "projected_average_usdc_million", "last_available_sofr", "lag_period", "lag_reserve_income", "lag_reported_average_usdc_million", "lag_days", "lag_implied_yield", "lag_supply_weighted_sofr_365", "annual_spread", "known_supply_days_million", "projected_supply_days_million", "raw_sofr_income", "reserve_income_forecast"]
forward = {k: f[k] for k in forward_keys}
forward["classification"] = "Dated 21 November scenario; not scored, not a current-quarter actual"
canonical = {}
for row in daily:
    if row["phase"] == "late":
        canonical[row["date"]] = {k: row[k] for k in ("date", "supply_million", "sofr", "fund_net_yield", "fund_observation_date", "fund_filed", "fund_accession")}
sources = [CIRCLE / x for x in ("stage2/results/stage2_data_model.json", "stage3/results/stage3_model.json", "stage3/results/daily_model_inputs.json", "stage3/results/yield_adjustment_comparison.json", "stage5/rldc/results/2026-11-21_Q4_RLDC_forecast.json")]
research = {"meta": {"title": "Estimating Circle reserve income with public data", "report_date": "2026-11-22", "historical_data_vintage": "2026-11-21", "units": "USD million and decimal annual yields unless labeled otherwise", "scope": "Reserve income only", "status": m["status"]},
    "methods": [{"id": a, "label": b, "category": c} for a, b, c in methods], "periods": periods, "evaluations": evals, "metrics": metrics,
    "daily": sorted(canonical.values(), key=lambda r: r["date"]), "fund_reports": m["fund_reports"], "fund_observations": read(CIRCLE / "stage3/results/fund_yield_observations.json"),
    "earnings_calendar": [{k: x[k] for k in ("period", "date", "url")} for x in calendar], "frozen_forward": forward,
    "source_hashes": [{"path": str(p.relative_to(CIRCLE)), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources]}
write(DATA / "research.json", research)
with (DATA / "backtest.csv").open("w", newline="", encoding="utf-8") as file:
    w = csv.writer(file); w.writerow(["period", "phase", "cutoff", "method", "classification", "estimate_usd_million", "actual_usd_million", "signed_error_pct"])
    for e in evals:
        for method, _, category in methods:
            w.writerow([e["period"], e["phase"], e["cutoff"], method, category, e["estimates"][method], e["actual_reserve_income"], e["errors"][method]*100])
with (DATA / "daily_inputs.csv").open("w", newline="", encoding="utf-8") as file:
    keys = list(daily[0]); w = csv.DictWriter(file, fieldnames=keys); w.writeheader(); w.writerows(daily)
print(json.dumps({"evaluations": len(evals), "methods": len(methods), "unique_daily_rows": len(canonical), "research_bytes": (DATA / "research.json").stat().st_size}))
