"""Reproduce the feasibility calculations from saved public-source responses.

Requires bundled lxml and pypdf. Outputs JSON data, not a fitted backtest.
Rates are decimalized exactly once; balances remain USD/token units.
"""
from __future__ import annotations
import bisect
import csv
import datetime as dt
import io
import json
from pathlib import Path
import re
import statistics
import xml.etree.ElementTree as ET
import lxml.html
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)
UTC = dt.timezone.utc


def load(name):
    return json.loads((RAW / name).read_text(encoding="utf-8"))


def day(timestamp):
    return dt.datetime.fromtimestamp(int(timestamp), UTC).date()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def document_rows():
    doc = lxml.html.fromstring((RAW / "circle_q3_2026_html.html").read_bytes())
    rows = []
    for tr in doc.xpath("//tr"):
        cells = [" ".join(" ".join(c.itertext()).split()) for c in tr.xpath("./td")]
        if cells:
            nums = [float(x.replace(",", "")) for x in cells[1:] if re.fullmatch(r"\d[\d,]*(?:\.\d+)?", x)]
            rows.append({"label": cells[0], "numbers": nums, "cells": cells})
    return rows


def main():
    checks = []
    def check(name, passed, detail=""):
        checks.append({"check":name, "passed":bool(passed), "detail":detail})

    rows = document_rows()
    def first_row(label, scale=1):
        row = next(r for r in rows if r["label"] == label and len(r["numbers"]) >= 4)
        return [x * scale for x in row["numbers"][:4]]

    labels = {
        "reserve_income": "Reserve income",
        "other_revenue": "Other revenue",
        "total_revenue": "Total revenue and reserve income",
        "distribution_and_transaction_costs": "Distribution and transaction costs",
        "other_costs": "Other costs",
        "total_distribution_transaction_other_costs": "Total distribution, transaction and other costs",
    }
    actuals = {k:first_row(v, 1000) for k,v in labels.items()}
    actuals["rldc"] = [a-b for a,b in zip(actuals["total_revenue"],actuals["total_distribution_transaction_other_costs"])]
    for i, period in enumerate(["Q3_2026", "Q3_2025", "9M_2026", "9M_2025"]):
        check(f"{period} revenue components", actuals["reserve_income"][i]+actuals["other_revenue"][i] == actuals["total_revenue"][i])
        check(f"{period} cost components", actuals["distribution_and_transaction_costs"][i]+actuals["other_costs"][i] == actuals["total_distribution_transaction_other_costs"][i])
    end_reported = first_row("USDC in circulation, end of period (1)", 1e6)[0]
    average_reported = first_row("USDC in circulation, average of period (1)", 1e6)[0]
    reported_rounded_rldc = first_row("Revenue less distribution costs (2)",1e6)[0]
    check("RLDC matches separately reported rounded KPI",abs(actuals["rldc"][0]-reported_rounded_rldc) <= 0.5e6)
    facts = load("sec_companyfacts.json")
    revenue_facts = facts["facts"]["us-gaap"]["Revenues"]["units"]["USD"]
    quarterly_revenue_periods = sorted({(f["start"],f["end"]) for f in revenue_facts if "start" in f
        and 75 <= (dt.date.fromisoformat(f["end"])-dt.date.fromisoformat(f["start"])).days <= 100})
    sec_revenue = [f for f in facts["facts"]["us-gaap"]["Revenues"]["units"]["USD"]
                   if f.get("start")=="2026-07-01" and f.get("end")=="2026-09-30"]
    check("SEC companyfacts matches issuer HTML revenue",bool(sec_revenue) and all(f["val"]==actuals["total_revenue"][0] for f in sec_revenue))
    q3 = {k:v[0] for k,v in actuals.items()}
    q3.update(average_usdc_reported=average_reported, end_usdc_reported=end_reported,
              rldc_margin=q3["rldc"]/q3["total_revenue"],
              filing_date=sec_revenue[0]["filed"],
              source_url="https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm")

    supply = load("defillama_usdc.json")
    check("USDC asset identity",str(supply["id"])=="2" and supply["symbol"]=="USDC")
    global_rows = supply["tokens"]
    global_by_date = {day(v["date"]):v for v in global_rows}
    check("No duplicate daily global timestamps",len(global_by_date)==len(global_rows))
    times = sorted(int(v["date"]) for v in global_rows)
    gaps = [(a,b) for a,b in zip(times,times[1:]) if b-a!=86400]
    start,end = dt.date(2026,7,1),dt.date(2026,9,30)
    days = [start+dt.timedelta(days=i) for i in range((end-start).days+1)]
    check("92 Q3 dates available without supply interpolation",all(d in global_by_date and d+dt.timedelta(days=1) in global_by_date for d in days))
    circulation = lambda row: row.get("circulating",{}).get("peggedUSD",0)
    chain_by_date = {chain:{day(v["date"]):v for v in obj["tokens"]} for chain,obj in supply["chainBalances"].items()}
    as_labeled = statistics.mean(circulation(global_by_date[d]) for d in days)
    next_midnight = statistics.mean(circulation(global_by_date[d+dt.timedelta(days=1)]) for d in days)

    # Calendar-day forward fill only, never backward fill from a future rate.
    sofr = {dt.date.fromisoformat(v["effectiveDate"]):v["percentRate"]/100
            for v in load("nyfed_sofr_2023_2026.json")["refRates"]}
    treasury = {dt.date.fromisoformat(v["observation_date"]):float(v["DGS3MO"])/100
                for v in csv.DictReader(io.StringIO((RAW/"fred_dgs3mo.txt").read_text()))
                if v["DGS3MO"] not in ["", "."]}
    def asof(mapping,d):
        keys=sorted(mapping)
        i=bisect.bisect_right(keys,d)-1
        if i<0:
            raise ValueError(f"No prior rate for {d}")
        return mapping[keys[i]], keys[i]
    daily=[]
    for d in days:
        s,sd = asof(sofr,d)
        t,td = asof(treasury,d)
        daily.append({"economic_date":d.isoformat(),"supply_snapshot_utc":str(d+dt.timedelta(days=1))+"T00:00:00Z",
                      "supply_snapshot_tokens":circulation(global_by_date[d+dt.timedelta(days=1)]),
                      "sofr_decimal":s,"sofr_effective_date":str(sd),"treasury_3m_decimal":t,"treasury_effective_date":str(td)})
    # Feasibility baselines only: no fitting to Q3 actuals.
    baselines=[]
    for name,key,basis in [("SOFR ACT/360","sofr_decimal",360),("3-month Treasury ACT/365 proxy","treasury_3m_decimal",365)]:
        estimate=sum(r["supply_snapshot_tokens"]*r[key]/basis for r in daily)
        baselines.append({"name":name,"estimate_usd":estimate,"error_usd":estimate-q3["reserve_income"],"error_percent":100*(estimate/q3["reserve_income"]-1),
                          "qualification":"unadjusted supply proxy and benchmark yield; reconstruction, not archived forecast"})
    q2reader=PdfReader(RAW/"circle_q2_2026_pdf.pdf")
    q2pages=[page.extract_text() or "" for page in q2reader.pages]
    q2kpi=next(t for t in q2pages if "Key operating indicators:" in t)
    q2rate_match=re.search(r"Reserve return rate\s+([\d.]+)\s*%",q2kpi)
    q2rate=float(q2rate_match.group(1))/100
    estimate=sum(r["supply_snapshot_tokens"]*q2rate/365 for r in daily)
    baselines.append({"name":"Q2 reported rounded reserve return ACT/365 proxy","annual_rate":q2rate,"estimate_usd":estimate,
                      "error_usd":estimate-q3["reserve_income"],"error_percent":100*(estimate/q3["reserve_income"]-1),
                      "qualification":"lagged rounded return applied to unadjusted USDC supply; does not resolve the reserve denominator or establish forecast accuracy"})

    # Exact reserve report bridge; numeric strings independently inspected on page 2.
    septext=" ".join((PdfReader(RAW/"attestation_2026_September.pdf").pages[1].extract_text() or "").split())
    attestation={"date":"2026-09-30","raw_approved_chain_supply":75866964179,
                 "tokens_allowed_but_not_issued":1856810081,"access_denied_tokens":131245845,
                 "gateway_pending_burns":46939,"circulation":73878861314,"reserve_assets_fair_value":73956687701,
                 "report_signature_date":"2026-10-26","publication_timestamp":"not established",
                 "source_file":"raw/attestation_2026_September.pdf","source_pdf_page":2}
    for k,v in attestation.items():
        if isinstance(v,int) and k!="source_pdf_page":
            check("September PDF contains "+k,f"{v:,}" in septext)
    att_calculated=attestation["raw_approved_chain_supply"]-attestation["tokens_allowed_but_not_issued"]-attestation["access_denied_tokens"]-attestation["gateway_pending_burns"]
    check("Exact attestation supply bridge",att_calculated==attestation["circulation"])
    check("Attestation circulation matches 10-Q rounding",abs(attestation["circulation"]-end_reported)<=0.5e6)

    # The fund's monthly regulatory XML supplies historical daily observations of
    # trailing seven-day yields. It is not a daily realized dividend series.
    fund_xml=ET.parse(RAW/"usdxx_nmfp_september_xml.txt").getroot()
    ns={"n":"http://www.sec.gov/edgar/nmfp3"}
    xt=lambda tag: fund_xml.findtext(".//n:"+tag,namespaces=ns)
    gross={e.findtext("n:sevenDayGrossYieldDate",namespaces=ns):float(e.findtext("n:sevenDayGrossYieldValue",namespaces=ns))
           for e in fund_xml.findall(".//n:sevenDayGrossYield",ns)}
    net={e.findtext("n:sevenDayNetYieldDate",namespaces=ns):float(e.findtext("n:sevenDayNetYieldValue",namespaces=ns))
         for e in fund_xml.findall(".//n:sevenDayNetYield",ns)}
    check("N-MFP identifies Circle Reserve Fund",xt("seriesId")=="S000077205" and xt("reportDate")=="2026-09-30")
    check("Fund net and gross yield date sets match",set(net)==set(gross) and len(net)>0)
    check("Net fund yields do not exceed gross",all(net[d]<=gross[d] for d in net))
    disclosed_fund_balance=first_row("Circle Reserve Fund",1e6)[0]
    fund_nav=float(xt("netAssetOfSeries"))
    check("Fund regulatory NAV matches 10-Q rounded fund balance",abs(fund_nav-disclosed_fund_balance)<0.5e6)
    fund={"series_id":xt("seriesId"),"report_date":xt("reportDate"),"fund_name":xt("nameOfSeries"),
          "net_assets_usd":fund_nav,"net_yield_observations":len(net),"net_yield_min":min(net.values()),"net_yield_max":max(net.values()),
          "filing_date":"2026-10-07","accepted_datetime_edgar":"2026-10-07 14:13:37",
          "filing_index_url":"https://www.sec.gov/Archives/edgar/data/844779/000119312526416631/0001193125-26-416631-index.htm",
          "qualification":"daily observations of trailing seven-business-day annualized yield, filed monthly; not same-day public observations or realized daily income",
          "daily_yields":[{"date":d,"gross_yield_decimal":gross[d],"net_yield_decimal":net[d]} for d in sorted(net)]}

    checkpoints=[]
    for date in ["2026-06-30","2026-07-31","2026-08-31","2026-09-30"]:
        label=date.replace("-","_")
        target=dt.datetime.fromisoformat(date).replace(tzinfo=UTC)+dt.timedelta(days=1,seconds=-1)
        block=load(f"checkpoint_{label}_tenderly_block.json")["result"]
        following=load(f"checkpoint_{label}_tenderly_next_block.json")["result"]
        btime=int(block["timestamp"],16)
        ntime=int(following["timestamp"],16)
        check(date+" block brackets UTC end of day",btime<=target.timestamp()<ntime)
        a=int(load(f"checkpoint_{label}_tenderly_supply.json")["result"],16)
        b=int(load(f"checkpoint_{label}_drpc_supply.json")["result"],16)
        check(date+" independent provider raw units agree",a==b)
        snap_date=dt.date.fromisoformat(date)+dt.timedelta(days=1)
        llama=chain_by_date["Ethereum"][snap_date]
        minted=llama["minted"]["peggedUSD"]
        c=circulation(llama)
        checkpoints.append({"economic_date":date,"block":int(block["number"],16),"block_hash":block["hash"],
                            "block_utc":dt.datetime.fromtimestamp(btime,UTC).isoformat(),
                            "next_block_utc":dt.datetime.fromtimestamp(ntime,UTC).isoformat(),
                            "raw_supply_integer":str(a),"decimals":6,"rpc_total_supply_tokens":a/1e6,
                            "providers_agree":a==b,"defillama_snapshot_date":str(snap_date),
                            "defillama_minted":minted,"defillama_chain_circulating":c,
                            "difference_rpc_minus_minted_tokens":a/1e6-minted,
                            "difference_rpc_minus_minted_bps":(a/1e6/minted-1)*10000,
                            "difference_rpc_minus_circulating_tokens":a/1e6-c})
    old_a=load("archive_tenderly_2024_supply.json")["result"]
    old_b=load("archive_drpc_2024_supply.json")["result"]
    check("2024 historical state providers agree",int(old_a,16)==int(old_b,16))

    endpoint=circulation(global_by_date[dt.date(2026,10,1)])
    chain_sum=sum(circulation(values.get(dt.date(2026,10,1),{})) for values in chain_by_date.values())
    reconciliation={"global_history_records":len(global_rows),"first_date":str(day(times[0])),"last_date":str(day(times[-1])),
                    "global_non_daily_intervals":len(gaps),"q3_days":len(days),"chain_series_count":len(chain_by_date),
                    "q3_average_as_labeled":as_labeled,"q3_average_next_midnight_alignment":next_midnight,
                    "q3_average_reported":average_reported,"average_gap_percent":100*(next_midnight/average_reported-1),
                    "q3_eod_defillama_global":endpoint,"q3_eod_attestation_circulation":attestation["circulation"],
                    "q3_eod_gap_usd":endpoint-attestation["circulation"],"q3_eod_gap_percent":100*(endpoint/attestation["circulation"]-1),
                    "chain_circulating_sum":chain_sum,"chain_sum_minus_global":chain_sum-endpoint,
                    "chain_sum_note":"Chain circulation may include reallocated bridged representations; inspect the aggregator before adding chains.",
                    "sofr_observation_count":len(sofr),"sofr_first_date":str(min(sofr)),"sofr_last_date":str(max(sofr)),
                    "treasury_observation_count":len(treasury),"treasury_first_date":str(min(treasury)),"treasury_last_date":str(max(treasury)),
                    "q3_calendar_sofr_average":statistics.mean(r["sofr_decimal"] for r in daily),
                    "q3_calendar_treasury_average":statistics.mean(r["treasury_3m_decimal"] for r in daily)}
    sensitivities=[{"distribution_transaction_other_cost_ratio_to_reserve_income":ratio,
                    "rldc_holding_actual_q3_revenue_constant":q3["total_revenue"]-q3["reserve_income"]*ratio,
                    "qualification":"illustrative sensitivity; not a forecast or contractual payout formula"}
                   for ratio in [0.50,0.55,0.60,0.65,0.70]]
    summary={"scope":"feasibility pilot; not out-of-sample backtest", "q3_2026_actuals_usd":q3,
             "supply_and_rate_coverage":reconciliation,"reserve_income_baselines":baselines,
             "attestation_reconciliation":attestation,"ethereum_checkpoints":checkpoints,
             "fund_regulatory_data":{k:v for k,v in fund.items() if k!="daily_yields"},
             "sec_direct_quarterly_revenue_periods":quarterly_revenue_periods,
             "rldc_cost_sensitivity":sensitivities,
             "rldc_impact_of_one_percentage_point_cost_ratio_to_reserve_income":q3["reserve_income"]*0.01,
             "checks_passed":sum(c["passed"] for c in checks),"checks_total":len(checks)}
    save("q3_reported_actuals.json",{"column_periods":["Q3_2026","Q3_2025","9M_2026","9M_2025"],"usd_values":actuals,"q3":q3})
    save("q3_daily_inputs.json",daily)
    save("ethereum_checkpoints.json",checkpoints)
    save("usdxx_september_regulatory_data.json",fund)
    save("quality_checks.json",checks)
    save("feasibility_summary.json",summary)
    print(json.dumps(summary,indent=2))
    failed=[c for c in checks if not c["passed"]]
    if failed:
        raise AssertionError(json.dumps(failed,indent=2))


if __name__ == "__main__":
    main()
