from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
import time
import ssl
import urllib.error
import urllib.parse
import urllib.request

from .domain import DataError, ReviewRequired, canonical, date_only_end, iso, timestamp, UTC
from . import parsers
from .store import atomic_write

ALLOWED_HOSTS = {"stablecoins.llama.fi", "markets.newyorkfed.org", "data.sec.gov", "www.sec.gov", "efts.sec.gov", "investor.circle.com", "www.circle.com"}
IR_URL = "https://investor.circle.com/overview/default.aspx"
PRESSROOM_URL = "https://www.circle.com/pressroom"
COMPANY_URL = "https://data.sec.gov/submissions/CIK0001876042.json"
FUND_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK0000844779.json"
SUPPLY_URL = "https://stablecoins.llama.fi/stablecoincharts/all?stablecoin=2"


def allowed(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise DataError("Unapproved public-data URL: " + url)


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, url):
        allowed(url)
        return super().redirect_request(request, fp, code, msg, headers, url)


class HttpClient:
    def __init__(self, cache, user_agent, *, opener=None, interval=1.05):
        if "@" not in user_agent or len(user_agent) < 15:
            raise DataError("Set an identifying SEC User-Agent including a contact email")
        self.cache = Path(cache)
        self.user_agent = user_agent
        self.opener = opener or urllib.request.build_opener(SafeRedirect())
        self.interval = interval
        self.last_request = 0.0
        self.receipts = []

    def get(self, url, *, ttl=3600, max_bytes=16 * 1024 * 1024):
        allowed(url)
        now = dt.datetime.now(UTC)
        index = self.cache / "urls" / (hashlib.sha256(url.encode()).hexdigest() + ".json")
        old = json.loads(index.read_bytes()) if index.exists() else None
        if old and (now - timestamp(old["checked_at"])).total_seconds() < ttl:
            raw = (self.cache / "bodies" / old["sha256"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != old["sha256"]:
                raise DataError("Cached public-data body failed its hash check")
            self.receipts.append(old)
            return raw, old
        headers = {"User-Agent": self.user_agent, "Accept": "application/json,text/html,application/xml;q=.9,*/*;q=.5"}
        if old and old.get("etag"):
            headers["If-None-Match"] = old["etag"]
        for attempt in range(3):
            delay = self.interval - (time.monotonic() - self.last_request)
            if delay > 0:
                time.sleep(delay)
            self.last_request = time.monotonic()
            try:
                with self.opener.open(urllib.request.Request(url, headers=headers), timeout=35) as response:
                    raw = response.read(max_bytes + 1)
                    if len(raw) > max_bytes:
                        raise DataError("Public-data response exceeded its size limit")
                    if not raw:
                        raise DataError("Empty public-data response")
                    sha = hashlib.sha256(raw).hexdigest()
                    retrieved = iso(dt.datetime.now(UTC))
                    receipt = {"url": url, "sha256": sha, "bytes": len(raw), "checked_at": retrieved,
                               "first_seen_at": old["first_seen_at"] if old and sha == old["sha256"] else retrieved,
                               "etag": response.headers.get("ETag"), "content_type": response.headers.get("Content-Type")}
                body_path = self.cache / "bodies" / sha
                if not body_path.exists():
                    atomic_write(body_path, raw)
                # Every content version retains its own URL and retrieval receipt.
                version = self.cache / "receipts" / (hashlib.sha256((url + sha).encode()).hexdigest() + ".json")
                if not version.exists():
                    atomic_write(version, canonical(receipt))
                atomic_write(index, canonical(receipt))
                self.receipts.append(receipt)
                return raw, receipt
            except urllib.error.HTTPError as exc:
                if exc.code == 304 and old:
                    raw = (self.cache / "bodies" / old["sha256"]).read_bytes()
                    if hashlib.sha256(raw).hexdigest() != old["sha256"]:
                        raise DataError("Cached body failed hash validation")
                    receipt = {**old, "checked_at": iso(dt.datetime.now(UTC))}
                    atomic_write(index, canonical(receipt))
                    self.receipts.append(receipt)
                    return raw, receipt
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                    raise DataError(f"Public-data HTTP {exc.code}: {url}") from exc
                time.sleep(min(30, max(2 ** attempt, int(exc.headers.get("Retry-After", "0")) if exc.headers.get("Retry-After", "0").isdigit() else 0)))
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                if isinstance(getattr(exc, "reason", None), ssl.SSLCertVerificationError):
                    raise DataError("TLS certificate verification failed: " + url) from exc
                if attempt == 2:
                    raise DataError(f"Public-data request failed: {url}: {type(exc).__name__}") from exc
                time.sleep(2 ** attempt)
        raise DataError("Request failed")

    def json(self, url, **kwargs):
        raw, receipt = self.get(url, **kwargs)
        try:
            return json.loads(raw), receipt
        except (ValueError, UnicodeError) as exc:
            raise DataError("Public-data response is not JSON: " + url) from exc


def submission_rows(payload):
    recent = payload.get("filings", {}).get("recent", payload)
    count = len(recent.get("accessionNumber", []))
    for key in ("filingDate", "form", "primaryDocument", "acceptanceDateTime"):
        if len(recent.get(key, [])) != count:
            raise DataError("SEC submission arrays have different lengths")
    return [{key: values[i] for key, values in recent.items() if isinstance(values, list) and len(values) == count} for i in range(count)]


def filing_url(row, cik):
    accession = row["accessionNumber"]
    if not __import__("re").fullmatch(r"\d{10}-\d{2}-\d{6}", accession):
        raise DataError("Invalid SEC accession")
    document = row["primaryDocument"]
    if not document or "/" in document or "\\" in document or ".." in document:
        raise DataError("Invalid primary-document path")
    return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{document}"


def release_discovery(client):
    try:
        raw, receipt = client.get(IR_URL)
        links = parsers.ir_release_links(raw, IR_URL)
        if not links:
            raise ReviewRequired("IR earnings links changed")
        return [{**r, "published_at": receipt["first_seen_at"], "kind": "official_ir_observed", "source_hash": receipt["sha256"]} for r in links], []
    except DataError as exc:
        raw, receipt = client.get(PRESSROOM_URL)
        links = parsers.pressroom_release_links(raw)
        if not links:
            raise ReviewRequired("Neither official release index provides recognized earnings links") from exc
        return [{**r, "published_at": receipt["first_seen_at"], "kind": "official_pressroom_observed", "source_hash": receipt["sha256"]} for r in links], [str(exc) + "; using Circle's official pressroom with certificate verification enabled"]


def reviewed_amendment(row, receipt, registry):
    review = registry.get(row["accessionNumber"])
    return review is not None and review.get("sha256") == receipt["sha256"]


def collect(client: HttpClient, *, lookback_days=500, amendment_registry=None):
    """Acquire sources before forecasting. A critical discovery failure stops the run."""
    now = dt.datetime.now(UTC)
    if amendment_registry is None:
        registry_path = Path(__file__).resolve().parents[1] / "data/reviewed_amendments.json"
        amendment_registry = json.loads(registry_path.read_bytes()) if registry_path.exists() else {}
    lower = now.date() - dt.timedelta(days=lookback_days)
    supply, _ = client.json(SUPPLY_URL, ttl=21600)
    rates_url = "https://markets.newyorkfed.org/api/rates/secured/sofr/search.json?" + urllib.parse.urlencode({"startDate": str(lower), "endDate": str(now.date())})
    rates, _ = client.json(rates_url, ttl=21600)
    submissions, _ = client.json(COMPANY_URL)
    result = {"supply": parsers.supply_feed(supply), "sofr": parsers.sofr_feed(rates), "financials": [], "funds": [], "releases": [], "issues": []}
    result["releases"], result["notices"] = release_discovery(client)
    for row in sorted(submission_rows(submissions), key=lambda r: r["acceptanceDateTime"]):
        if row["filingDate"] >= str(lower) and row["form"] in ("10-Q/A", "10-K/A", "8-K/A"):
            amendment_url = filing_url(row, parsers.CIRCLE_CIK)
            _, receipt = client.get(amendment_url, ttl=315360000)
            if reviewed_amendment(row, receipt, amendment_registry):
                result["notices"].append("Reviewed amendment " + row["accessionNumber"] + ": " + amendment_registry[row["accessionNumber"]]["reason"])
            else:
                result["issues"].append({"source_url": amendment_url, "message": "Unreviewed amended filing detected; original values retained pending review"})
        if row["filingDate"] < str(lower) or row["form"] not in ("10-Q", "10-K", "8-K"):
            continue
        if row["form"] == "8-K" and "2.02" not in row.get("items", ""):
            continue
        url = filing_url(row, parsers.CIRCLE_CIK)
        raw, receipt = client.get(url, ttl=315360000)
        metadata = {"published_at": iso(timestamp(row["acceptanceDateTime"])), "accession": row["accessionNumber"], "source_url": url}
        try:
            if row["form"] == "8-K":
                event = parsers.earnings_event(raw, **metadata)
                if event:
                    result["releases"].append(event)
            else:
                result["financials"].extend(parsers.financial_report(raw, **metadata, source_hash=receipt["sha256"]))
        except (DataError, ValueError) as exc:
            result["issues"].append({"source_url": url, "message": str(exc)})
            # A known earnings 8-K with an unknown period must not allow forecasting.
            if row["form"] == "8-K":
                raise ReviewRequired("Could not identify a new earnings reporting period") from exc
    fund_submissions, _ = client.json(FUND_SUBMISSIONS_URL, ttl=21600)
    accepted = {r["accessionNumber"]: r["acceptanceDateTime"] for r in submission_rows(fund_submissions)}
    candidates = []
    for offset in range(0, 300, 100):
        query = urllib.parse.urlencode({"q": '"Circle Reserve Fund"', "dateRange": "custom", "startdt": str(lower), "enddt": str(now.date()),
                                       "forms": "N-MFP3", "ciks": "0000844779", "from": offset, "size": 100})
        payload, _ = client.json("https://efts.sec.gov/LATEST/search-index?" + query, ttl=21600)
        hits = payload.get("hits", {}).get("hits", [])
        candidates.extend(hits)
        total = payload.get("hits", {}).get("total", {}).get("value", len(hits))
        if offset + len(hits) >= total:
            break
    else:
        raise ReviewRequired("Reserve-fund discovery exceeded the bounded search window")
    if not candidates:
        raise DataError("No reserve-fund filings discovered")
    seen = set()
    for hit in candidates:
        row = hit["_source"]
        accession = row["adsh"]
        if row.get("form") != "N-MFP3" or accession in seen:
            continue
        seen.add(accession)
        url = filing_url({"accessionNumber": accession, "primaryDocument": "primary_doc.xml"}, "844779")
        raw, receipt = client.get(url, ttl=315360000)
        published = accepted.get(accession)
        # An observed live filing is certainly public by first retrieval. Otherwise
        # use end-of-filing-day, never invent an earlier intraday publication time.
        published = iso(timestamp(published)) if published else min(date_only_end(row["file_date"]), receipt["first_seen_at"])
        try:
            result["funds"].extend(parsers.fund_report(raw, published_at=published, accession=accession, source_url=url, source_hash=receipt["sha256"]))
        except ReviewRequired as exc:
            result["issues"].append({"source_url": url, "message": str(exc)})
    result["source_hashes"] = sorted({r["sha256"] for r in client.receipts})
    return result
