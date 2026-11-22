"""Strict adapters for the public feeds and original financial disclosures."""
from __future__ import annotations

import datetime as dt
import re
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

from lxml import html

from .domain import DataError, ReviewRequired, Quarter, duration_quarter, number

SERIES = "S000077205"
CIRCLE_CIK = "1876042"


def supply_feed(payload):
    rows = payload.get("tokens", []) if isinstance(payload, dict) else payload
    if not isinstance(rows, list) or not rows:
        raise DataError("Empty or unrecognized USDC feed")
    result = {}
    for row in rows:
        day = dt.datetime.fromtimestamp(int(row["date"]), dt.timezone.utc).date().isoformat()
        if day in result:
            raise DataError("Duplicate USDC date")
        field = row.get("totalCirculating", row.get("circulating", {}))
        result[day] = number(field.get("peggedUSD"), minimum=1, maximum=1e13) / 1e6
    return result


def sofr_feed(payload):
    result = {}
    for row in payload.get("refRates", []):
        day = dt.date.fromisoformat(row["effectiveDate"]).isoformat()
        if row.get("type") != "SOFR" or day in result:
            raise DataError("Duplicate date or wrong rate type")
        result[day] = number(row["percentRate"], minimum=-10, maximum=25) / 100
    if not result:
        raise DataError("Empty SOFR feed")
    return result


def fund_report(raw: bytes, *, published_at, accession, source_url, source_hash):
    if b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ReviewRequired("Fund XML contains a document type or entity declaration")
    root = ET.fromstring(raw)
    text = lambda name: root.findtext(".//{*}" + name)
    if text("seriesId") != SERIES:
        raise ReviewRequired("Wrong reserve-fund series")
    report_date = dt.date.fromisoformat(text("reportDate"))
    observations = []
    seen = set()
    for item in root.findall(".//{*}sevenDayNetYield"):
        day = dt.date.fromisoformat(item.findtext("{*}sevenDayNetYieldDate"))
        if day in seen or (day.year, day.month) != (report_date.year, report_date.month):
            raise ReviewRequired("Fund yield dates duplicate or outside report month")
        seen.add(day)
        observations.append({"date": day.isoformat(), "net_yield": number(item.findtext("{*}sevenDayNetYieldValue"), minimum=-.10, maximum=.25),
                             "published_at": published_at, "report_date": report_date.isoformat(),
                             "accession": accession, "source_url": source_url, "source_hash": source_hash})
    if not 15 <= len(observations) <= 23:
        raise ReviewRequired("Unexpected number of business-day fund yields")
    return observations


def text(element):
    return " ".join(" ".join(element.itertext()).replace("\xa0", " ").split())


def local(tag):
    return str(tag).split("}")[-1].split(":")[-1].lower()


def money(fact):
    if fact.get("format", "").lower() not in ("", "ixt:num-dot-decimal", "ixt4:num-dot-decimal", "ixt:numdotdecimal"):
        raise ReviewRequired("Unrecognized inline-XBRL numeric transform")
    value = text(fact).replace(",", "").replace(" ", "")
    if not re.fullmatch(r"-?\d+(?:\.\d+)?", value):
        raise ReviewRequired("Unsupported inline-XBRL numeric value")
    try:
        scale = int(fact.get("scale", "0"))
        if not -12 <= scale <= 12:
            raise ReviewRequired("Inline-XBRL scale is outside the supported range")
        amount = Decimal(value) * Decimal(10) ** scale
    except (InvalidOperation, ValueError, OverflowError) as exc:
        raise ReviewRequired("Invalid inline-XBRL scale") from exc
    if fact.get("sign") == "-":
        amount = -amount
    return number(amount / Decimal(1_000_000), minimum=0, maximum=1e8)


MONTH = {name.lower(): i for i, name in enumerate(("", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"))}
DURATION = re.compile(r"(three months|six months|nine months|twelve months|year|years) ended\s+([A-Za-z]+)\s+(\d{1,2})", re.I)


def table_measures(tree, label_pattern):
    """Interpret ordered year/duration headers; never assume column 1 is a quarter."""
    results = []
    for table in tree.xpath("//table"):
        rows = table.xpath("./tr|./tbody/tr|./thead/tr")
        for index, row in enumerate(rows):
            cells = row.xpath("./td|./th")
            if not cells or not re.match(label_pattern, text(cells[0]), re.I):
                continue
            values = []
            for cell in cells[1:]:
                value = text(cell).replace(",", "").strip()
                if re.fullmatch(r"\d+(?:\.\d+)?", value):
                    values.append(number(value, minimum=0, maximum=1e9))
            headers = [text(r) for r in rows[:index]]
            duration_headers = next((list(DURATION.finditer(h)) for h in headers if DURATION.search(h)), [])
            years = next(([int(text(c)) for c in r.xpath("./td|./th") if re.fullmatch(r"20\d\d", text(c))]
                          for r in rows[:index] if sum(bool(re.fullmatch(r"20\d\d", text(c))) for c in r.xpath("./td|./th")) == len(values) and values), [])
            if not values or not duration_headers or len(years) != len(values) or len(years) % len(duration_headers):
                continue
            unit_header = " ".join(headers).lower()
            if "in millions" in unit_header:
                scale = 1
            elif "in thousands" in unit_header:
                scale = .001
            else:
                continue
            columns_per_group = len(years) // len(duration_headers)
            for i, (year, value) in enumerate(zip(years, values)):
                duration, month, day = duration_headers[i // columns_per_group].groups()
                if month.lower() not in MONTH:
                    continue
                end = dt.date(year, MONTH[month.lower()], int(day))
                months = {"three months": 3, "six months": 6, "nine months": 9, "twelve months": 12, "year": 12, "years": 12}[duration.lower()]
                if end.month < months or end.day != Quarter.containing(end).end.day:
                    continue
                start = dt.date(year, end.month - months + 1, 1)
                results.append({"start": str(start), "end": str(end), "value": value * scale,
                                "basis": "reported_table", "precision_million": .5 * scale,
                                "locator": "Operating-indicator table: " + text(cells[0])})
    return unique_measures(results)


def unique_measures(rows):
    grouped = {}
    for row in rows:
        key = (row["start"], row["end"])
        if key in grouped and abs(grouped[key]["value"] - row["value"]) > 1e-8:
            raise ReviewRequired(f"Conflicting financial values for {key}")
        grouped[key] = row
    return list(grouped.values())


def financial_report(raw: bytes, *, published_at, accession, source_url, source_hash):
    tree = html.fromstring(raw)
    contexts, usd_units = {}, set()
    for element in tree.iter():
        if local(element.tag) == "context":
            identifiers = [text(e).lstrip("0") for e in element.iter() if local(e.tag) == "identifier"]
            dimensions = any(local(e.tag) in ("explicitmember", "typedmember") for e in element.iter())
            dates = {local(e.tag): text(e) for e in element.iter() if local(e.tag) in ("startdate", "enddate")}
            if identifiers == [CIRCLE_CIK] and not dimensions and len(dates) == 2:
                contexts[element.get("id")] = dates
        if local(element.tag) == "unit" and any(text(e).lower().endswith(":usd") for e in element.iter() if local(e.tag) == "measure"):
            usd_units.add(element.get("id"))
    income = []
    for fact in tree.iter():
        if local(fact.tag) != "nonfraction" or fact.get("contextref") not in contexts or fact.get("unitref") not in usd_units:
            continue
        row = next((a for a in fact.iterancestors() if local(a.tag) == "tr"), None)
        if row is None or not re.match(r"reserve income\b", text(row), re.I):
            continue
        concept = fact.get("name", "").split(":")[-1].lower()
        if concept not in ("interestanddividendincomeoperating", "reserveincome"):
            raise ReviewRequired("Reserve-income taxonomy changed")
        ctx = contexts[fact.get("contextref")]
        income.append({"start": ctx["startdate"], "end": ctx["enddate"], "value": money(fact),
                       "basis": "reported_inline_xbrl", "locator": fact.get("id"), "precision_million": .0005})
    averages = table_measures(tree, r"USDC\s+in\s+circulation,?\s+average\s+of\s+period\b")
    if not income:
        raise ReviewRequired("No unambiguous tagged Reserve income facts; image-only releases need review or the subsequent filing")
    records = []
    for metric, rows in (("reserve_income", unique_measures(income)), ("average_usdc", averages)):
        for row in rows:
            records.append({**row, "metric": metric, "published_at": published_at, "accession": accession,
                            "source_url": source_url, "source_hash": source_hash})
    return records


def earnings_event(raw: bytes, *, published_at, accession, source_url):
    tree = html.fromstring(raw)
    body = text(tree)
    if not re.search(r"Item\s*2\.02", body, re.I):
        return None
    matches = re.findall(r"(?:quarter|year)\s+ended\s+([A-Za-z]+)\s+(\d{1,2}),?\s+(20\d\d)", body, re.I)
    quarters = set()
    for month, day, year in matches:
        if month.lower() not in MONTH:
            continue
        end = dt.date(int(year), MONTH[month.lower()], int(day))
        quarter = Quarter.containing(end)
        if end == quarter.end:
            quarters.add(quarter.key)
    if len(quarters) != 1:
        raise ReviewRequired("Earnings release reporting period is ambiguous")
    return {"period": quarters.pop(), "published_at": published_at, "source_url": source_url,
            "accession": accession, "kind": "earnings_8k"}


def ir_release_links(raw: bytes, base_url: str):
    """The official IR overview links its latest quarterly earnings PDF."""
    tree = html.fromstring(raw)
    result = []
    for anchor in tree.xpath("//a[@href]"):
        href = urljoin(base_url, anchor.get("href"))
        match = re.search(r"/doc_earnings/(20\d\d)/q([1-4])/earnings-result/", href, re.I)
        if match:
            result.append({"period": f"{match[1]}Q{match[2]}", "source_url": href})
    return list({(x["period"], x["source_url"]): x for x in result}.values())


def pressroom_release_links(raw: bytes, base_url="https://www.circle.com/pressroom"):
    tree = html.fromstring(raw)
    result = []
    for anchor in tree.xpath("//a[@href]"):
        href = urljoin(base_url, anchor.get("href"))
        match = re.search(r"/pressroom/circle-reports-(first|second|third|fourth)-quarter(?:-and-full-year)?-(20\d\d)(?:-financial)?-results/?$", href)
        if not match:
            continue
        published = re.search(r"([A-Za-z]+)\s+(\d{1,2}),?\s+(20\d\d)", text(anchor))
        if not published or published[1].lower() not in MONTH:
            continue
        day = dt.date(int(published[3]), MONTH[published[1].lower()], int(published[2]))
        result.append({"period": match[2] + "Q" + str(("first", "second", "third", "fourth").index(match[1]) + 1),
                       "source_url": href, "release_day": str(day)})
    return list({(x["period"], x["source_url"]): x for x in result}.values())
