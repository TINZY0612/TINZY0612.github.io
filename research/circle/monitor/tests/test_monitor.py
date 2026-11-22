from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from circle_monitor.bootstrap import from_research
from circle_monitor.domain import DataError, Quarter, ReviewRequired, UTC, canonical, timestamp
from circle_monitor.engine import export, tick
from circle_monitor.model import financial_quarters, forecast, metrics
from circle_monitor.parsers import earnings_event, financial_report, fund_report, ir_release_links, sofr_feed, supply_feed
from circle_monitor.publish import publish
from circle_monitor.sources import COMPANY_URL, HttpClient, allowed, submission_rows
from circle_monitor.store import Store

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "reserve_report/repository/circle/data/research.json"
GIT = Path("C:/Users/Tin/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe")
GIT = str(GIT) if GIT.exists() else "git"


def dates(a, b):
    a, b = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
    return [a + dt.timedelta(days=i) for i in range((b - a).days + 1)]


def financial(period, income, average, published):
    q = Quarter.parse(period)
    return [{"metric": metric, "start": str(q.start), "end": str(q.end), "value": value, "published_at": published,
             "source_url": "https://www.sec.gov/fixture", "source_hash": "fixture-" + period,
             "basis": "reported_test_fixture", "accession": "fixture-" + period}
            for metric, value in (("reserve_income", income), ("average_usdc", average))]


def bundle():
    days = dates("2026-07-01", "2027-04-20")
    funds = []
    for day in days:
        if day.weekday() >= 5:
            continue
        last = dt.date(day.year + (day.month == 12), day.month % 12 + 1, 1) - dt.timedelta(days=1)
        published = last + dt.timedelta(days=7)
        funds.append({"date": str(day), "net_yield": .04, "report_date": str(last),
                      "published_at": str(published) + "T12:00:00Z", "accession": str(last), "source_url": "https://www.sec.gov/fund", "source_hash": "fund-fixture"})
    return {"supply": {str(d): 70000.0 for d in days}, "sofr": {str(d): .04 for d in days if d.weekday() < 5},
            "financials": financial("2026Q3", 630, 70000, "2026-11-04T12:00:00Z"), "funds": funds, "releases": [], "source_hashes": []}


class CalendarTests(unittest.TestCase):
    def test_year_rollover_and_leap_year(self):
        self.assertEqual(Quarter.parse("2026Q4").shift(1).key, "2027Q1")
        self.assertEqual(Quarter.parse("2027Q1").shift(-1).key, "2026Q4")
        self.assertEqual(Quarter.parse("2024Q1").days, 91)
        self.assertEqual(Quarter.parse("2025Q1").days, 90)
        with self.assertRaises(DataError):
            timestamp("2027-01-07T12:00:00")


class ModelTests(unittest.TestCase):
    def test_future_financial_actual_cannot_change_forecast(self):
        data = bundle()
        baseline = forecast("2026Q4", "2027-01-07T23:00:00Z", data)
        data["financials"] += financial("2026Q4", 99999, 1, "2027-02-10T12:00:00Z")
        after = forecast("2026Q4", "2027-01-07T23:00:00Z", data)
        self.assertEqual(baseline["estimates_million"], after["estimates_million"])
        self.assertAlmostEqual(after["estimates_million"]["fund_proportional"], 630)

    def test_latest_published_calibration_can_be_two_quarters_old(self):
        data = bundle()
        data["financials"] += financial("2026Q4", 645, 70000, "2027-02-10T12:00:00Z")
        early = forecast("2027Q1", "2027-01-07T23:00:00Z", data)
        late = forecast("2027Q1", "2027-02-11T23:00:00Z", data)
        self.assertEqual(early["calibration"]["period"], "2026Q3")
        self.assertEqual(late["calibration"]["period"], "2026Q4")

    def test_future_fund_publication_is_excluded(self):
        data = bundle()
        before = forecast("2026Q4", "2027-01-07T11:00:00Z", data)
        for row in data["funds"]:
            if row["report_date"] == "2026-12-31":
                row["net_yield"] = .20
        after = forecast("2026Q4", "2027-01-07T11:00:00Z", data)
        self.assertEqual(before["estimates_million"], after["estimates_million"])
        visible = forecast("2026Q4", "2027-01-07T13:00:00Z", data)
        self.assertNotEqual(before["estimates_million"], visible["estimates_million"])

    def test_today_supply_excluded_and_only_future_days_projected(self):
        data = bundle()
        data["supply"]["2027-01-07"] = 999999
        result = forecast("2027Q1", "2027-01-07T23:00:00Z", data)
        self.assertEqual(result["observed_days"], 6)
        self.assertEqual(result["projected_days"], 84)
        self.assertTrue(all(r["supply_million"] == 70000 for r in result["rows"]))

    def test_internal_supply_gaps_fail_and_stale_rate_fails(self):
        data = bundle()
        del data["supply"]["2026-11-16"]
        with self.assertRaisesRegex(DataError, "Missing daily"):
            forecast("2026Q4", "2027-01-07T23:00:00Z", data)
        data = bundle()
        data["sofr"] = {d: v for d, v in data["sofr"].items() if d < "2026-12-20"}
        with self.assertRaisesRegex(DataError, "SOFR"):
            forecast("2026Q4", "2027-01-07T23:00:00Z", data)

    def test_missing_fund_does_not_silently_switch_primary(self):
        data = bundle()
        data["funds"] = []
        result = forecast("2026Q4", "2027-01-07T23:00:00Z", data)
        self.assertFalse(result["primary_available"])
        self.assertEqual(result["primary_method"], "fund_proportional")
        self.assertNotIn("fund_proportional", result["estimates_million"])
        self.assertIn("sofr_lagged_spread", result["estimates_million"])

    def test_nonfinite_values_and_zero_fund_denominator(self):
        data = bundle()
        data["supply"]["2026-12-01"] = float("nan")
        with self.assertRaises(DataError):
            forecast("2026Q4", "2027-01-07T23:00:00Z", data)
        data = bundle()
        for row in data["funds"]:
            row["net_yield"] = 0
        result = forecast("2026Q4", "2027-01-07T23:00:00Z", data)
        self.assertIn("denominator", result["fund_unavailable_reason"])

    def test_annual_less_nine_months_is_not_annual_reported_as_q4(self):
        records = []
        for metric, annual, nine in (("reserve_income", 2600, 1900), ("average_usdc", 65000, 61000)):
            for end, value in (("2026-12-31", annual), ("2026-09-30", nine)):
                records.append({"metric": metric, "start": "2026-01-01", "end": end, "value": value,
                                "published_at": "2027-02-10T12:00:00Z", "source_url": "filing", "source_hash": end, "precision_million": .5})
        actual = financial_quarters(records, timestamp("2027-02-11T12:00:00Z"))["2026Q4"]
        self.assertEqual(actual["reserve_income"]["value"], 700)
        self.assertAlmostEqual(actual["average_usdc"]["value"], (65000 * 365 - 61000 * 273) / 92)
        self.assertIn("day_weighted", actual["average_usdc"]["basis"])

    def test_changed_comparative_actual_requires_review(self):
        data = bundle()
        data['financials'] += financial('2026Q3', 640, 70000, '2027-01-01T12:00:00Z')
        with self.assertRaises(ReviewRequired):
            forecast('2026Q4', '2027-01-07T23:00:00Z', data)


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Path(self.temp.name) / "state")

    def run_tick(self, data, when, **kwargs):
        with self.store.lock():
            return tick(self.store, data, timestamp(when), **kwargs)

    def test_quarter_rollover_and_immutable_initial(self):
        data = bundle()
        waiting = self.run_tick(data, "2027-01-03T23:00:00Z")
        self.assertEqual(next(r for r in waiting["targets"] if r["period"] == "2026Q4")["status"], "awaiting_initial_cutoff")
        result = self.run_tick(data, "2027-01-07T23:00:00Z")
        self.assertEqual({r["period"] for r in result["targets"]}, {"2026Q4", "2027Q1"})
        initial = next(r for r in self.store.rows("forecasts") if r["period"] == "2026Q4" and r["kind"] == "initial")
        path = self.store.root / "forecasts" / (__import__("circle_monitor.domain", fromlist=["digest"]).digest(initial) + ".json")
        original_bytes = path.read_bytes()
        for day in data["supply"]:
            if "2026-10-01" <= day <= "2026-12-31":
                data["supply"][day] *= 1.01
        self.run_tick(data, "2027-01-08T23:00:00Z")
        self.assertEqual(path.read_bytes(), original_bytes)
        self.assertEqual(sum(r["kind"] == "initial" for r in self.store.rows("forecasts")), 1)
        self.assertTrue(any(r["kind"] == "update" for r in self.store.rows("forecasts")))

    def test_repeated_run_does_not_duplicate_forecast_or_score(self):
        data = bundle()
        self.run_tick(data, "2027-01-07T23:00:00Z")
        count = len(self.store.rows("forecasts"))
        self.run_tick(data, "2027-01-07T23:30:00Z")
        self.assertEqual(count, len(self.store.rows("forecasts")))
        data["financials"] += financial("2026Q4", 645, 70000, "2027-02-10T12:00:00Z")
        self.run_tick(data, "2027-02-11T23:00:00Z")
        self.assertEqual(len(self.store.rows("validations")), 4)
        self.run_tick(data, "2027-02-11T23:30:00Z")
        self.assertEqual(len(self.store.rows("validations")), 4)

    def test_scoring_retains_large_errors_and_separates_selections(self):
        data = bundle()
        self.run_tick(data, "2027-01-07T23:00:00Z")
        data["financials"] += financial("2026Q4", 645, 70000, "2027-02-10T12:00:00Z")
        view = self.run_tick(data, "2027-02-11T23:00:00Z")
        row = next(r for r in view["validations"] if r["selection"] == "initial" and r["method"] == "fund_proportional")
        self.assertAlmostEqual(row["difference_million"], -15)
        self.assertAlmostEqual(row["signed_error"], 630 / 645 - 1)
        self.assertTrue(row["alert"])
        self.assertEqual(view["prospective_metrics"]["initial"]["fund_proportional"]["n"], 1)

    def test_image_release_blocks_new_forecasts_until_actual_arrives(self):
        data = bundle()
        self.run_tick(data, "2027-01-07T23:00:00Z")
        data["releases"] = [{"period": "2026Q4", "published_at": "2027-02-10T12:00:00Z", "source_url": "release"}]
        view = self.run_tick(data, "2027-02-11T23:00:00Z")
        self.assertIn("2026Q4", view["released_awaiting_actual"])
        self.assertFalse(any(r["period"] == "2026Q4" for r in view["targets"]))
        self.assertEqual(view["validations"], [])

    def test_release_day_forecast_cannot_win_last_pre_release_score(self):
        data = bundle()
        self.run_tick(data, "2027-01-07T23:00:00Z")
        self.run_tick(data, "2027-02-10T01:00:00Z")
        data["financials"] += financial("2026Q4", 645, 70000, "2027-02-10T12:00:00Z")
        view = self.run_tick(data, "2027-02-11T23:00:00Z")
        self.assertTrue(all(r["forecast_at"][:10] < "2027-02-10" for r in view["validations"]))

    def test_historical_replay_never_enters_prospective_metrics(self):
        data = bundle()
        self.run_tick(data, "2027-01-07T23:00:00Z", provenance="historical_replay")
        data["financials"] += financial("2026Q4", 645, 70000, "2027-02-10T12:00:00Z")
        view = self.run_tick(data, "2027-02-11T23:00:00Z", provenance="historical_replay")
        self.assertEqual(len(view["validations"]), 4)
        self.assertEqual(view["prospective_metrics"]["initial"]["fund_proportional"]["n"], 0)

    def test_bad_data_keeps_last_good_forecast_and_exports_dated_values(self):
        data = bundle()
        self.run_tick(data, "2027-01-07T23:00:00Z")
        original = copy.deepcopy(self.store.rows("forecasts"))
        del data["supply"]["2026-11-16"]
        view = self.run_tick(data, "2027-01-08T23:00:00Z")
        self.assertEqual(view["status"], "needs_attention")
        self.assertTrue(next(r for r in view["targets"] if r["period"] == "2026Q4")["last_good_forecast"])
        self.assertEqual([r for r in self.store.rows("forecasts") if r["period"] == "2026Q4"], [r for r in original if r["period"] == "2026Q4"])
        out = Path(self.temp.name) / "export"
        export(self.store, view, out)
        self.assertTrue((out / "monitor.json").exists())
        self.assertFalse((out / "research.json").exists())

    def test_lock_prevents_concurrent_runs_and_releases_after_exit(self):
        with self.store.lock():
            with self.assertRaises(DataError):
                with Store(self.store.root).lock():
                    pass
        with Store(self.store.root).lock():
            pass


class ParserTests(unittest.TestCase):
    def test_feed_units_duplicates_and_wrong_type(self):
        self.assertEqual(supply_feed([{"date": 1735689600, "totalCirculating": {"peggedUSD": 70e9}}])["2025-01-01"], 70000)
        row = {"date": 1735689600, "totalCirculating": {"peggedUSD": 70e9}}
        with self.assertRaises(DataError):
            supply_feed([row, row])
        with self.assertRaises(DataError):
            sofr_feed({"refRates": [{"effectiveDate": "2027-01-05", "type": "EFFR", "percentRate": 4}]})

    def test_unknown_financial_units_or_ambiguous_facts_require_review(self):
        raw = (ROOT / "stage2/raw/q3_2026_html.html").read_bytes()
        metadata = {"published_at": "2026-11-04T12:00:00Z", "accession": "test", "source_url": "filing", "source_hash": "sha"}
        with self.assertRaises(ReviewRequired):
            financial_report(raw.replace(b'unitRef="usd"', b'unitRef="shares"'), **metadata)
        with self.assertRaises(ReviewRequired):
            financial_report(b'<html><body><img src="results.png">Reserve income</body></html>', **metadata)

    def test_official_ir_release_pdf_period(self):
        links = ir_release_links(b'<a href="https://s206.q4cdn.com/a/files/doc_earnings/2027/q1/earnings-result/result.pdf">Earnings release</a>', "https://investor.circle.com/")
        self.assertEqual(links[0]["period"], "2027Q1")

    def test_block_untrusted_hosts_and_misaligned_submission_arrays(self):
        for url in ["http://www.sec.gov/x", "https://www.sec.gov.evil.example/x", "https://user:secret@www.sec.gov/x"]:
            with self.assertRaises(DataError):
                allowed(url)
        with self.assertRaises(DataError):
            submission_rows({"accessionNumber": ["x"], "form": []})


@unittest.skipUnless(RESEARCH.exists(), "Original research archive not present")
class ArchivedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.research = json.loads(RESEARCH.read_bytes())
        cls.seed = from_research(RESEARCH)
        cls.inputs = {**cls.seed, "supply": supply_feed(json.loads((ROOT / "feasibility/raw/defillama_usdc.json").read_bytes())),
                      "sofr": sofr_feed(json.loads((ROOT / "feasibility/raw/nyfed_sofr_2023_2026.json").read_bytes())), "source_hashes": []}

    def test_all_twelve_historical_cutoffs_reproduce_both_methods(self):
        errors = []
        for evaluation in self.research["evaluations"]:
            with self.subTest(evaluation=evaluation["id"]):
                result = forecast(evaluation["period"], evaluation["cutoff"] + "T23:59:59.999999Z", self.inputs, provenance="historical_replay")
                for method in ("fund_proportional", "sofr_lagged_spread"):
                    expected = evaluation["estimates"][method]
                    self.assertAlmostEqual(result["estimates_million"][method], expected, places=7)
                    if evaluation["phase"] == "late" and method == "fund_proportional":
                        errors.append(abs(result["estimates_million"][method] / evaluation["actual_reserve_income"] - 1))
        self.assertAlmostEqual(sum(errors) / len(errors), self.research["metrics"]["late"]["fund_proportional"]["mape"], places=12)

    def test_parse_all_twenty_two_original_monthly_fund_reports(self):
        count = 0
        for report in self.research["fund_reports"]:
            raw = (ROOT / "stage3" / report["file"].replace("\\", "/")).read_bytes()
            rows = fund_report(raw, published_at=report["accepted_datetime"], accession=report["accession"], source_url=report["url"], source_hash=hashlib.sha256(raw).hexdigest())
            self.assertEqual(len(rows), report["yield_observations"])
            self.assertAlmostEqual(min(r["net_yield"] for r in rows), report["net_yield_min"])
            count += len(rows)
        self.assertEqual(count, len(self.research["fund_observations"]))

    def test_parse_six_financial_filings_against_audited_actuals(self):
        expected = {"2025Q2": 634.274, "2025Q3": 711.241, "2026Q1": 652.508, "2026Q2": 667.733, "2026Q3": 657.624}
        combined = []
        for name, period in [("q2_2025_html.html", "2025Q2"), ("q3_2025_html.html", "2025Q3"), ("fy2025_html.html", None), ("q1_2026_html.html", "2026Q1"), ("q2_2026_html.html", "2026Q2"), ("q3_2026_html.html", "2026Q3")]:
            raw = (ROOT / "stage2/raw" / name).read_bytes()
            rows = financial_report(raw, published_at="2026-11-22T00:00:00Z", accession=name, source_url=name, source_hash=hashlib.sha256(raw).hexdigest())
            combined += rows
            if period:
                parsed = financial_quarters(rows, timestamp("2026-11-22T00:00:00Z"))
                self.assertAlmostEqual(parsed[period]["reserve_income"]["value"], expected[period])
        parsed = financial_quarters(combined, timestamp("2026-11-22T00:00:00Z"))
        self.assertAlmostEqual(parsed["2025Q4"]["reserve_income"]["value"], 733.396)
        self.assertEqual(parsed["2026Q3"]["average_usdc"]["value"], 73264)

    def test_detect_all_six_archived_earnings_release_periods(self):
        calendar = json.loads((ROOT / "stage2/earnings_calendar.json").read_bytes())
        for entry in calendar:
            raw = (ROOT / "stage2" / entry["download"]["file"].replace("\\", "/")).read_bytes()
            row = earnings_event(raw, published_at=entry["acceptance_datetime"], accession=entry["accession"], source_url=entry["url"])
            self.assertEqual(row["period"], entry["period"])

    def test_original_live_sofr_monitor_reproduced(self):
        live = json.loads((RESEARCH.parent / "live.json").read_bytes())
        data = copy.deepcopy(self.inputs)
        for row in live["calibration_rows"] + live["rows"]:
            if row["date"] < "2026-11-22":
                data["supply"][row["date"]] = row["supply_million"]
                data["sofr"][row["date"]] = row["sofr"]
        result = forecast("2026Q4", "2026-11-22T10:00:00Z", data, provenance="historical_replay")
        self.assertAlmostEqual(result["estimates_million"]["sofr_lagged_spread"], live["reserve_income_million"], places=7)

    def test_importing_historical_actuals_creates_no_forecasts_or_scores(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            for key, rows in self.seed.items():
                for row in rows:
                    store.put(key, row)
            self.assertEqual(store.rows("forecasts"), [])
            self.assertEqual(store.rows("validations"), [])


class PublisherTests(unittest.TestCase):
    def test_dry_run_and_reject_code_in_generated_output(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "export"
            source.mkdir()
            (source / "monitor.json").write_text('{}')
            self.assertTrue(publish(source, Path(directory) / "repo")["dry_run"])
            (source / "index.html").write_text('unexpected')
            with self.assertRaises(DataError):
                publish(source, Path(directory) / "repo")

    def test_local_git_publication_only_touches_generated_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            remote, checkout, source = root / "remote.git", root / "site", root / "export"
            def git(*args):
                return subprocess.check_output([GIT, *map(str, args)], stderr=subprocess.STDOUT).decode().strip()
            git('init', '--bare', remote)
            git('init', '-b', 'main', checkout)
            (checkout / 'index.html').write_text('unchanged website')
            git('-C', checkout, 'add', 'index.html')
            git('-C', checkout, '-c', 'user.name=Test', '-c', 'user.email=test@example.com', 'commit', '-m', 'initial')
            git('-C', checkout, 'remote', 'add', 'origin', remote)
            git('-C', checkout, 'push', '-u', 'origin', 'main')
            source.mkdir()
            (source / 'monitor.json').write_bytes(b'{"tested":true}')
            result = publish(source, checkout, execute=True, git=GIT)
            self.assertTrue(result['published'])
            self.assertEqual((checkout/'index.html').read_text(), 'unchanged website')
            self.assertEqual(git('--git-dir', remote, 'show', 'main:circle/data/monitor/monitor.json'), '{"tested":true}')
            again = publish(source, checkout, execute=True, git=GIT)
            self.assertFalse(again['changed'])
            (checkout/'index.html').write_text('unrelated change')
            with self.assertRaises(DataError):
                publish(source, checkout, execute=True, git=GIT)
            (checkout/'index.html').write_text('unpublished code commit')
            git('-C', checkout, 'add', 'index.html')
            git('-C', checkout, '-c', 'user.name=Test', '-c', 'user.email=test@example.com', 'commit', '-m', 'Do not publish this code')
            remote_before = git('--git-dir', remote, 'rev-parse', 'main')
            with self.assertRaisesRegex(DataError, 'Unpublished website-code'):
                publish(source, checkout, execute=True, git=GIT)
            self.assertEqual(git('--git-dir', remote, 'rev-parse', 'main'), remote_before)


if __name__ == '__main__':
    unittest.main()
