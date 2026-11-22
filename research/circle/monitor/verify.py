"""Run the behavioral tests and save an inspectable, source-hashed receipt."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import platform
import sys
import unittest

import lxml

ROOT = Path(__file__).resolve().parent
suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
result = unittest.TextTestRunner(verbosity=1).run(suite)
receipt = {
    "tested_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "passed": result.wasSuccessful(),
    "tests_run": result.testsRun,
    "failures": [str(test) for test, _ in result.failures],
    "errors": [str(test) for test, _ in result.errors],
    "skipped": [str(test) for test, _ in result.skipped],
    "python": platform.python_version(),
    "lxml": lxml.__version__,
    "source_hashes": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for directory in ("circle_monitor", "tests") for p in sorted((ROOT / directory).glob("*.py"))},
    "historical_evidence": {
        "target_quarters": 6,
        "cutoff_replays": 12,
        "methods_per_cutoff": 2,
        "forecast_values_compared": 24,
        "fund_filings_parsed": 22,
        "fund_yield_observations": 459,
        "financial_filings_parsed": 6,
        "earnings_release_periods_checked": 6,
        "classification": "Archived-data historical replay, not prospective validation"
    } if not result.skipped else None
}
(ROOT / "runs").mkdir(exist_ok=True)
(ROOT / "runs/verification.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: receipt[k] for k in ("passed", "tests_run", "failures", "errors", "skipped")}))
sys.exit(0 if result.wasSuccessful() else 1)
