# Circle quarterly actuals and supply reconciliation protocol

Stage started 21 November 2026. Function: historical financial analysis for an equity research report. Reader: the author and an analyst reviewing the application sample. No forecasting-performance claim is made at this stage.

## Sources and coverage

Use original Circle filings as the accounting authority. Target Q1 2025 through Q3 2026, with Q1 2025 serving as a lagged reference and Q2 2025 onward as candidate public-company evaluation periods. Derive Q4 2025 from FY2025 minus nine months only for additive income-statement amounts. Record the source document, publication date, units, and whether each value is reported or derived. Never derive a quarter-end stock by subtraction, or a quarter's average yield by subtracting annual and year-to-date percentages.

Review original reserve examination reports and the saved DefiLlama adapter logic to explain raw supply, unreleased balances, circulation, bridge attribution, and access-denied tokens. Preserve the feasibility snapshot and code. Use Refinitiv Workspace through the access method verified in Gold Trade only as a supplementary cross-check at this stage. Credentials remain in memory and licensed raw results remain local.

## Authoritative data model

Keep source observations separate from calculations. Each observation needs a metric, economic period, unit, source, filing date, source locator, and reported/derived status. Missing values remain missing. Multiple reports of the same metric are comparison evidence, not extra amounts to sum. Preserve original values and record reclassifications before combining versions.

The deliverables are a machine-readable dataset, one local Excel workbook, and a short findings note. The workbook presents quarterly actuals and the supply comparison with traceable source inputs. USD millions are the default financial display unit. Token quantities remain token quantities, with explicit scaling for display. Rates are decimal values with percentage formats. Dates are Gregorian calendar dates, with UTC used for chain snapshots.

## Checks fixed before extraction

1. Financial revenue and cost components must add to reported totals within USD 0.002 million when source figures are in thousands. RLDC equals total revenue less total distribution, transaction, and other costs. Rounded KPI checks allow half the published unit, plus an allowance for the components' displayed rounding.
2. Q4 flow derivations must reconcile to annual totals and all other quarters within source rounding. Stocks and average rates may not use flow subtraction. Day-weighted averages can be derived only from compatible definitions and day counts, and must be labeled derived.
3. Every quarter must have unique period keys and explicit source coverage for reserve income, other revenue, total revenue, and distribution costs. A missing metric is unavailable, never zero.
4. Preserve separate dates for a financial period, its original disclosure, later comparative disclosure, and data retrieval. A comparative published later cannot establish earlier public availability.
5. Supply components in an examination report must reconcile to circulation within one token when reported to whole tokens. A rounded filing circulation check allows half its displayed USD million.
6. Exact RPC provider comparisons require identical chain, contract, block, decimals, and underlying integer values. An aggregator timestamp without a source block cannot establish exact block-level agreement.
7. Display all provider-versus-official supply differences. Flag absolute gaps over 0.10% for investigation; this is a research materiality threshold, not an accuracy certification. Smaller gaps remain differences until explained.
8. Test every workbook calculation against the authoritative dataset, including first and last quarters and the derived Q4 column. Check missing versus zero behavior, formula errors, and representative input changes. Render all worksheets and inspect their populated layouts before delivery.

## Completion boundary

Stage completed on 21 November 2026. The quarterly dataset, workbook, original release calendar, and bounded supply-gap analysis are saved. All 81 data checks and 49 workbook-value comparisons passed. See `Stage_2_Findings.md` for conclusions and remaining input-eligibility constraints.

Complete this stage when the quarterly bridge is traceable, derivations and missing inputs are explicit, and the supply gap has either a supported explanation or a bounded list of unresolved components. The following stage will build and evaluate the reserve-income and RLDC forecast models.
