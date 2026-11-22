"""Audit earnings dates and Reserve income rows in original release exhibits."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.request
import urllib.parse
from lxml import html

ROOT = Path(__file__).resolve().parent
CIRCLE = ROOT.parent
RAW = ROOT / "earnings_sources"
RAW.mkdir(exist_ok=True)
calendar = json.loads((CIRCLE / "stage2/earnings_calendar.json").read_text())
model = json.loads((CIRCLE / "stage3/results/stage3_model.json").read_text())
actuals = {q["period"]: q["metrics"]["reserve_income"]["value"] for q in model["quarters"]}


def audit(entry):
    original = CIRCLE / "stage2" / entry["download"]["file"]
    tree = html.fromstring(original.read_bytes())
    candidates = tree.xpath('//a[contains(@href,"ex99") or contains(@href,"ex-99") or contains(@href,"exhibit99")]/@href')
    candidates += tree.xpath('//a[normalize-space(.)="99.1"]/@href')
    candidates += tree.xpath('//a[contains(translate(normalize-space(.),"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"),"press release")]/@href')
    candidates = list(dict.fromkeys(candidates))
    result = {"period": entry["period"], "release_date": entry["date"], "earnings_8k": entry["url"],
              "filing_actual_usd_million": actuals[entry["period"]], "candidate_exhibits": candidates, "release_rows": []}
    for i, href in enumerate(candidates[:3]):
        url = urllib.parse.urljoin(entry["url"], href)
        try:
            path = RAW / (entry["period"] + "_" + str(i) + ".html")
            if path.exists():
                raw = path.read_bytes()
            else:
                request = urllib.request.Request(url, headers={"User-Agent": "CircleResearch/1.0", "Accept": "text/html"})
                with urllib.request.urlopen(request, timeout=35) as response:
                    raw = response.read()
                path.write_bytes(raw)
            page = html.fromstring(raw)
            image_urls = [urllib.parse.urljoin(url, image) for image in page.xpath('//img/@src')]
            rows = page.xpath('//tr[contains(translate(normalize-space(.),"ABCDEFGHIJKLMNOPQRSTUVWXYZ","abcdefghijklmnopqrstuvwxyz"),"reserve income")]')
            found = []
            for row in rows:
                cells = [" ".join(x.itertext()).replace("\xa0", " ").strip() for x in row.xpath('./td|./th')]
                text = " ".join(" ".join(row.itertext()).split())
                if len(text) < 1800:
                    found.append({"text": text, "cells": cells})
            result["release_rows"].append({"url": url, "file": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(raw).hexdigest(), "rows": found, "image_urls": image_urls, "image_financial_values_independently_parsed": False})
        except Exception as exc:
            result.setdefault("errors", []).append({"url": url, "error": str(exc)})
    return result


if __name__ == "__main__":
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(audit, calendar))
    (ROOT / "earnings_release_audit.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    for r in rows:
        print(r["period"], "exhibits", len(r["release_rows"]), "rows", [x["text"][:350] for e in r["release_rows"] for x in e["rows"]][:3], "errors", r.get("errors"))
