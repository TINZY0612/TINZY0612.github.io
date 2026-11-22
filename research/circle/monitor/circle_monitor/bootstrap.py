"""Import audited financial inputs; importing never creates a forecast or score."""
from __future__ import annotations

import hashlib
import json

from .domain import DataError, Quarter, date_only_end


def from_research(path, ledger_path=None):
    raw = path.read_bytes()
    data = json.loads(raw)
    sha = hashlib.sha256(raw).hexdigest()
    result = {"financials": [], "funds": [], "releases": []}
    if ledger_path is None:
        ledger_path = next((p / "stage2/results/stage2_data_model.json" for p in path.resolve().parents if (p / "stage2/results/stage2_data_model.json").exists()), None)
    ledger = json.loads(ledger_path.read_bytes()) if ledger_path is not None else None
    for row in data["periods"]:
        q = Quarter.parse(row["period"])
        for original_metric, metric, value_key in (("reserve_income", "reserve_income", "reserve_income"), ("usdc_average", "average_usdc", "reported_average_supply")):
            source = next((r for r in row["financial_sources"] if r["metric"] == original_metric), None)
            if source is None:
                if ledger is None:
                    raise DataError("Derived seed input requires the audited Stage 2 ledger; no publication date is guessed")
                measure = next(r for r in ledger["quarters"] if r["period"] == q.key)["metrics"][original_metric]
                components = [r for r in ledger["source_observations"] if r["id"] in measure["input_ids"]]
                source = {"published_by": measure["published_by"], "source_url": components[0]["source_url"],
                          "locator": "Audited derivation: " + measure["basis"], "source_name": "audited-derived-" + q.key,
                          "components": components, "source_precision": .001}
            result["financials"].append({"metric": metric, "start": str(q.start), "end": str(q.end), "value": row[value_key],
                "published_at": date_only_end(source["published_by"]), "source_url": source["source_url"],
                "source_hash": sha, "locator": source["locator"], "basis": "audited_research_seed",
                "precision_million": source.get("source_precision", .001) / 2, "accession": source["source_name"],
                "components": source.get("components", [])})
    reports = {r["accession"]: r for r in data["fund_reports"]}
    for row in data["fund_observations"]:
        report = reports[row["accession"]]
        result["funds"].append({"date": row["date"], "net_yield": row["net_yield"], "report_date": row["report_date"],
            "published_at": report.get("accepted_datetime") or date_only_end(row["filed"]),
            "accession": row["accession"], "source_url": row["url"], "source_hash": sha})
    for row in data["earnings_calendar"]:
        result["releases"].append({"period": row["period"], "published_at": row["date"] + "T00:00:00Z",
                                   "source_url": row["url"], "kind": "audited_release_date"})
    return result
