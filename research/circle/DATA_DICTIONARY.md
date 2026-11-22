# Data dictionary and source map

All amounts in the model are USD millions unless explicitly labeled USD billions or raw token units. Annual yields are decimal fractions in JSON: `0.0392` means 3.92%.

| Input | Primary source | Unit | Model role | Archived location |
| --- | --- | --- | --- | --- |
| Daily global USDC circulation | DefiLlama USDC history API | Token dollars at par; converted to USD millions | Daily earning-balance proxy | `feasibility/raw/`, `stage5/raw/`, `data_inventory/access_checks/`, `downloaded_monitor_http/` |
| Quarterly reserve income | Circle original SEC filings | USD millions | Actual for scoring; previous quarters only for calibration | `stage2/raw/`, `stage2/results/stage2_data_model.json` |
| Reported average USDC | Circle financial and operating disclosures | USD millions | Denominator for previous company implied yield | Same financial ledger |
| Monthly fund disclosure | Original Circle Reserve Fund Form N-MFP3, series S000077205 | Net seven-day yield, annualized | Fund benchmark | `stage3/raw/`, `stage3/fund_filings.json` |
| SOFR | Federal Reserve Bank of New York | Annual rate; quoted percent in original feed, decimal in model | Alternative benchmark, actual/360 accrual | `stage3/raw/`, `reserve_report/sofr_live.json`, `downloaded_monitor_http/` |
| Three-month Treasury yield | DGS3MO | Annual percent, converted to decimal | Simple alternative benchmark | `stage3/raw/` |
| Original earnings dates | Circle SEC 8-K release exhibits and official pressroom | Calendar dates / available filing timestamps | Establish forecast cutoff and release barrier | `stage2/earnings_calendar.json`, `reserve_report/earnings_sources/` |
| Ethereum native USDC mints and burns | Public Ethereum RPC contract events | Integer token units, 6 decimals | Independent supply-accounting sample | `stage5/raw/`, `stage5/results/` |
| CCTP route and fee events | Authenticated Circle contract events, public RPC | Token amounts, fees and event metadata | Exploratory transaction-fee analysis | `stage5/raw/`, `stage5/results/` |
| Other revenue / RLDC inputs | Circle and partner filings; public protocol feeds | USD millions and protocol-specific units | Exploratory extensions, outside completed report scope | `stage4/`, `stage5/rldc/` |

## Reader-friendly exports

- `reserve_report/site/circle/data/research.json`: seven-quarter financial/supply ledger, twelve cutoff evaluations, eight methods, monthly fund-report metadata and dated observations.
- `reserve_report/site/circle/data/backtest.csv`: historical estimates and errors.
- `reserve_report/site/circle/data/daily_inputs.csv`: daily balance/yield inputs and fund-source accessions.
- `reserve_report/assets/fund_ratio_signed_errors.json`: exact six late-cutoff errors used in the report's signed-error chart.
- `stage3/results/daily_model_inputs.json`: detailed original daily calculations, including the prior-quarter calibration rows.
- `monitor/runs/live-export/monitor.json`: dated monitor view. Actuals for the unfinished target quarter are unavailable.
- `monitor/runs/live-export/forecasts/`: immutable dated calculation evidence, named by content hash.

## Date conventions

`observation date` is when a balance/rate refers to. `published_at` / filing date is when a disclosure could be used. `as_of_utc` is when the monitor saved its estimate. These are distinct.

The historical report uses calendar-date cutoffs and later-downloaded balance/rate histories; it does not establish a complete original-data vintage for every historical day. The reusable monitor retains retrieval bodies and saved forecasts for prospective evaluation. The current UTC supply bucket is excluded as potentially incomplete.

A fund's net seven-day yield is an annualized measure, not the return earned in a single day. The model divides by 365 when accruing its daily contribution. SOFR uses 360; the prior yield-gap comparison explicitly converts day-count conventions.

## Source links

- [DefiLlama USDC history](https://stablecoins.llama.fi/stablecoin/2)
- [Circle transparency and reserve reports](https://www.circle.com/transparency)
- [Circle SEC submissions](https://data.sec.gov/submissions/CIK0001876042.json)
- [New York Fed SOFR](https://www.newyorkfed.org/markets/reference-rates/sofr)
- [Circle native USDC contract registry](https://developers.circle.com/stablecoins/usdc-contract-addresses)

The report links the original financial filings and all 22 monthly fund reports used in its historical sample. Stage-specific source manifests preserve more precise document URLs and retrieval metadata. `FILE_MANIFEST.json` records the published bytes; a recorded hash verifies a file, not the economic correctness of its source.
