import datetime as dt
import hashlib
import io
import json
from pathlib import Path
import ssl
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from circle_monitor.domain import DataError, UTC, iso
from circle_monitor.sources import COMPANY_URL, HttpClient, IR_URL, PRESSROOM_URL, release_discovery, reviewed_amendment
from circle_monitor.__main__ import main


class Response(io.BytesIO):
    def __init__(self, raw):
        super().__init__(raw)
        self.headers = {"ETag": '"v1"', "Content-Type": "application/json"}


class Opener:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    def open(self, request, timeout):
        self.calls += 1
        value = next(self.responses)
        if isinstance(value, Exception):
            raise value
        return Response(value)


class SourceTests(unittest.TestCase):
    def test_amendment_review_is_pinned_to_exact_document_content(self):
        registry = {'accession': {'sha256': 'original-hash', 'reason': 'Reviewed fund-only supplement'}}
        self.assertTrue(reviewed_amendment({'accessionNumber':'accession'}, {'sha256':'original-hash'}, registry))
        self.assertFalse(reviewed_amendment({'accessionNumber':'accession'}, {'sha256':'changed-hash'}, registry))
        self.assertFalse(reviewed_amendment({'accessionNumber':'different'}, {'sha256':'original-hash'}, registry))
    def test_http_cache_preserves_hash_and_first_seen_time(self):
        with tempfile.TemporaryDirectory() as directory:
            opener = Opener([b'{"ok":true}'])
            client = HttpClient(directory, "Circle monitor test@example.com", opener=opener, interval=0)
            raw, first = client.get(COMPANY_URL)
            _, again = client.get(COMPANY_URL)
            self.assertEqual(opener.calls, 1)
            self.assertEqual(first["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(first["first_seen_at"], again["first_seen_at"])
            (Path(directory) / "bodies" / first["sha256"]).write_bytes(b"corrupt")
            with self.assertRaisesRegex(DataError, "hash"):
                client.get(COMPANY_URL)

    def test_not_modified_uses_checked_cached_body(self):
        with tempfile.TemporaryDirectory() as directory:
            not_modified = urllib.error.HTTPError(COMPANY_URL, 304, "Not Modified", {}, None)
            opener = Opener([b'{}', not_modified])
            client = HttpClient(directory, "Circle monitor test@example.com", opener=opener, interval=0)
            _, first = client.get(COMPANY_URL, ttl=0)
            raw, second = client.get(COMPANY_URL, ttl=0)
            self.assertEqual(raw, b'{}')
            self.assertEqual(first["first_seen_at"], second["first_seen_at"])

    def test_certificate_failure_is_not_retried_or_disabled(self):
        with tempfile.TemporaryDirectory() as directory:
            opener = Opener([urllib.error.URLError(ssl.SSLCertVerificationError("expired"))])
            client = HttpClient(directory, "Circle monitor test@example.com", opener=opener, interval=0)
            with self.assertRaisesRegex(DataError, "certificate"):
                client.get(IR_URL)
            self.assertEqual(opener.calls, 1)

    def test_official_pressroom_fallback_retains_reported_release_day(self):
        raw = b'<a href="/pressroom/circle-reports-third-quarter-2026-results">November 4, 2026 Circle Reports Third Quarter 2026 Results</a>'
        class Client:
            def get(self, url):
                if url == IR_URL:
                    raise DataError("TLS certificate verification failed")
                self_url = PRESSROOM_URL
                assert url == self_url
                return raw, {"first_seen_at": "2026-11-22T12:00:00Z", "sha256": "fixture"}
        events, notices = release_discovery(Client())
        self.assertEqual(events[0]["release_day"], "2026-11-04")
        self.assertEqual(events[0]["period"], "2026Q3")
        self.assertTrue(notices)

    def test_cli_failure_keeps_last_good_export(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "out"
            output.mkdir()
            (output / "monitor.json").write_bytes(b'{"last_good":true}')
            with patch("circle_monitor.__main__.collect", side_effect=DataError("source outage")):
                config = root / "config.json"
                config.write_text('{"user_agent":"Circle monitor test@example.com"}')
                with patch("sys.stderr", new=io.StringIO()):
                    code = main(["run", "--state", str(root / "state"), "--output", str(output), "--config", str(config)])
            self.assertEqual(code, 1)
            self.assertEqual((output / "monitor.json").read_bytes(), b'{"last_good":true}')
            self.assertEqual(json.loads((output / "health.json").read_bytes())["status"], "failed")

    def test_forged_replay_time_cannot_be_used_with_live_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch("sys.stderr", new=io.StringIO()):
                with self.assertRaises(SystemExit):
                    main(["run", "--state", directory, "--output", directory, "--as-of", "2025-01-01T00:00:00Z"])


if __name__ == "__main__":
    unittest.main()
