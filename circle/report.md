# Estimating Circle reserve income with public data

Detailed research report and reproducible historical test

Prepared 22 November 2026. Historical model and data vintage 21 November 2026. Scope is reserve income before distribution costs and operating expenses. Financial amounts are USD millions unless stated otherwise.

## Research conclusion

Public USDC balance data, combined with observable interest rates and the previous quarter's reported economics, can reproduce Circle's reserve income closely in this historical sample. Across six target quarters from Q2 2025 through Q3 2026, the original SOFR model has **0.337% mean absolute percentage error**, and the Circle Reserve Fund challenger has **0.237%**. Carrying forward prior reserve income with a day-count adjustment has **6.287%** error. The calibrated models outperform that baseline in every tested quarter.

The result is economically intuitive. A larger stock of reserve-backed USDC increases the balance on which Circle can earn interest; a change in the earned yield changes income on that balance. We estimate both exposures daily rather than infer income from quarter-end circulation alone. The previous quarter provides a lagged bridge between a public rate and Circle's broader realized reserve-income economics.

The evidence is promising but narrower than a claim that Circle's earnings are predictable within a fixed tolerance. There are seven quarters of financial observations and six target-quarter predictions because the first quarter supplies the initial calibration. The outcomes and a feasibility pilot had already been inspected before the protocol was fixed. Supply and rate histories were downloaded later, although financial and fund inputs are filtered by publication dates. These are retrospective simulations, not six timestamped forecasts made before earnings. Reserve income is also a gross income line; it is not net income or earnings per share.

The report focuses on what the data support: source extraction, balance checks, daily income calculations, alternative methods and comparison with actual financial disclosures. Other revenue, ARC token recognition, distribution costs, valuation and EPS are outside this report.

## Why reserve income is observable

USDC is a dollar-denominated stablecoin. Circle invests the reserves supporting its circulation, so reserve income depends primarily on the size of the reserve balance and the return earned on the reserve assets. The token's public circulation gives an outside analyst a frequent proxy for the earning balance. The interest itself, bank holdings, fund allocations and recognition adjustments are not all recorded in token transfers.

This distinction defines the research design. Blockchain data provide the balance exposure. Public rate and fund disclosures provide yield proxies. Financial statements establish the accounting target and the lagged calibration. The model combines these sources rather than claiming that an equity income statement exists entirely on chain. Circle describes its reserve arrangements and publishes assurance reports through its [transparency archive](https://www.circle.com/transparency).

For illustration, an additional $1bn of average reserves earning 4% annually for a 90-day quarter contributes about $9.863m before other adjustments. A quarter-end balance does not establish that the same amount was outstanding for all 90 days. That is why daily balance exposure matters.

Our target is Circle's **reported total reserve income**. USDC supply is the balance proxy, while the target's perimeter includes smaller differences such as EURC-related reserve economics. The lagged gap can absorb some persistent differences, but it does not independently measure the euro business, bank interest or each reserve asset. Calling the result an exact USDC Treasury-interest calculation would overstate what has been identified.

## Establishing the financial actuals

We first create a seven-quarter accounting ledger from original SEC filings and earnings materials. Extract the reserve-income line separately from total revenue and reserve income. Reported figures in USD thousands are divided by 1,000 to produce USD millions. Each observation retains its original source, period, unit, publication date, row locator and ledger ID. A rounded press-release headline about total revenue is not substituted for the reserve-income line.

| Period | Days | Reserve income USD m | Average USDC USD bn |
| --- | --- | --- | --- |
| Q1 2025 | 90 | 557.911 | 54.136 |
| Q2 2025 | 91 | 634.274 | 61.039 |
| Q3 2025 | 92 | 711.241 | 67.842 |
| Q4 2025 | 92 | 733.396 | 76.200 |
| Q1 2026 | 90 | 652.508 | 75.200 |
| Q2 2026 | 91 | 667.733 | 76.524 |
| Q3 2026 | 92 | 657.624 | 73.264 |

Q1 2025 is the initial reference period, not a scored prediction. Q4 2025 reserve income is a flow derived as full-year reserve income of **$2,636.822m less nine-month reserve income of $1,903.426m = $733.396m**. We do not subtract balance-sheet stocks, yields or average balances in this way. Q4 average USDC is separately taken from the operating-indicator disclosure at $76.2bn, which is rounded more coarsely than the million-level data for the other periods.

The original earnings Form 8-K establishes the announcement date. Its release exhibit supplies the contemporaneous communication; the supporting Form 10-Q or Form 10-K supplies the precisely extracted reserve-income row used to score this research. The downloaded release exhibits contain image-based financial tables that are not safely parsed as ordinary HTML rows. Consequently, this edition does not claim a fresh automated exact-value match to every release image. It preserves the original release links and the independently extracted filing actuals. The exact filing ledger is the scoring authority; the release establishes when the announcement occurred. Q4's annual filing was published after the earnings announcement and is used for outcome verification, not as a pre-announcement predictor.

| Period | Announcement | Original release | Supporting filing actual USD m |
| --- | --- | --- | --- |
| Q2 2025 | 2025-08-12 | [Release exhibit](https://www.sec.gov/Archives/edgar/data/1876042/000162828025039749/q22025epr.htm) | 634.274 |
| Q3 2025 | 2025-11-12 | [Release exhibit](https://www.sec.gov/Archives/edgar/data/1876042/000187604225000045/nolivelinksversion_q3202.htm) | 711.241 |
| Q4 2025 | 2026-02-25 | [Release exhibit](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000032/final_circlereportsfourt.htm) | 733.396 |
| Q1 2026 | 2026-05-11 | [Release exhibit](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000148/final_05x11q1epr30.htm) | 652.508 |
| Q2 2026 | 2026-08-05 | [Release exhibit](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000246/augustepr-circle_q22026f.htm) | 667.733 |
| Q3 2026 | 2026-11-04 | [Release exhibit](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000309/finalq3epr-110326.htm) | 657.624 |

## Getting the USDC data

The working daily source is the free [DefiLlama USDC history endpoint](https://stablecoins.llama.fi/stablecoin/2). The JSON asset ID is 2. For the historical model, read each record in `tokens`, convert its Unix `date` to a UTC calendar date and extract `circulating.peggedUSD`. Divide by one million to align balances with financial amounts in USD millions. Keep the raw response and its hash; later changes to a provider's history must not silently alter a published backtest.

USDC is modeled at its dollar par value. A secondary-market depeg can change market value without changing the reserve liability dollar for dollar. We therefore use token circulation, not a market capitalization that fluctuates with a traded price. We do not sum all token balances across chains: third-party bridged representations can be backed by already counted native USDC locked elsewhere.

The dashboard's new refresh collector uses the smaller [USDC-filtered chart endpoint](https://stablecoins.llama.fi/stablecoincharts/all?stablecoin=2). Its values are checked against the full endpoint over shared dates during release verification. This avoids downloading the approximately 23.7 MB full chain-history response for every visitor. The historical backtest keeps its original source vintage and extraction definition.

### Checking supply against company disclosures

We compare both quarter-average circulation and quarter-end stock against Circle's disclosed figures. Average supply tests the balance relevant to income; a single end-date match cannot establish a correct quarter-average. The accepted working thresholds are 0.5% absolute difference as preferred and 1.0% as an outer limit. These are tolerances for supply data, not a forecast error guarantee.

| Period | Provider average USD bn | Reported average USD bn | Average difference | End stock difference |
| --- | --- | --- | --- | --- |
| Q1 2025 | 54.051 | 54.136 | -0.156% | +0.277% |
| Q2 2025 | 60.912 | 61.039 | -0.208% | -0.161% |
| Q3 2025 | 67.504 | 67.842 | -0.499% | -0.132% |
| Q4 2025 | 75.896 | 76.200 | -0.398% | +0.073% |
| Q1 2026 | 75.287 | 75.200 | +0.116% | +0.113% |
| Q2 2026 | 76.733 | 76.524 | +0.273% | +0.288% |
| Q3 2026 | 73.521 | 73.264 | +0.351% | +0.365% |

The end-stock comparison consistently uses the provider's following-date bucket against the attested quarter-end circulation. This is a comparison convention, not proof that both sources measure the same instant. Inspection of DefiLlama's daily storage logic showed that a record may inherit an hourly observation while its label is replaced with the start of a day. The historical API does not consistently supply an observation block sufficient to certify exact UTC end-of-day state. The mean-balance comparisons above instead use the provider's dates as labeled, which is also the main forecasting convention.

All seven end-stock comparisons fall inside the preferred 0.5% range, approximately −0.161% to +0.365%. Average differences range from −0.499% to +0.351%, also inside the preferred range. Q3 2025 is close to the boundary and Q4's official average is rounded. This is sufficient to use the series as a balance proxy under the accepted tolerance, but not to claim an exact reconciliation. No fixed correction is applied to force the data to match.

### Direct contract validation

The project also reconstructed Ethereum native USDC issuance and destruction directly for Q3 2026. Its opening supply plus all mints less all burns equals closing supply exactly in integer token units. The extraction processed 488,594 mint and burn events and authenticated CCTP minter roles to distinguish chain relocation from other issuance activity. This is an independent chain-accounting check; it covers one chain and quarter, not all global USDC balances over the seven-quarter sample.

This direct work demonstrates the underlying on-chain method. The broad daily income model uses DefiLlama because rebuilding complete historical state for every supported chain would add substantial archive infrastructure and reconciliation work. A third-party aggregator can be a practical production source while authenticated direct-chain samples test important parts of its perimeter.

## Getting and interpreting the interest rates

### SOFR

The [Federal Reserve Bank of New York](https://www.newyorkfed.org/markets/reference-rates/sofr) publishes SOFR, a measure of overnight borrowing costs collateralized by Treasury securities. The historical collector reads `effectiveDate` and `percentRate`; a quoted 3.90 means a decimal annual rate of 0.039, not 3.90. SOFR is an overnight benchmark, not a promise that every Circle reserve dollar earns that exact return.

For calendar dates without a new eligible rate, use the most recent effective-date observation. Publication timing is separate from economic date: an effective day's SOFR normally becomes public on the following business day. Historical cutoffs and the forward collector must not use a future publication. The backtest uses retrieved historical rates rather than fully archived original daily vintages, so later revisions remain a limitation.

SOFR accrual is calculated on an actual over 360 basis. Daily uncalibrated income is daily supply multiplied by annual SOFR divided by 360. To subtract it from an implied yield annualized over 365, first multiply SOFR by 365/360. Mixing a 360-day raw benchmark with a 365-day implied yield without this conversion creates an avoidable systematic difference.

### The Circle Reserve Fund net seven day yield

The fund model uses the **Circle Reserve Fund's net seven-day yield**, not the yield of the USYC tokenized fund. The fund is managed within BlackRock's money market fund reporting framework. A seven-day yield is an annualized measure based on a recent seven-day income window. It is not a seven-day percentage gain to be divided by seven, not a Treasury's yield to maturity, and not an exact statement of the dividends Circle earned that day.

The archive contains 22 original monthly Form N-MFP3 reports, December 2024 through September 2026. Those reports contain 459 dated business-day observations. We authenticate series ID **S000077205** and extract `sevenDayNetYieldDate` and `sevenDayNetYieldValue` within each `sevenDayNetYield` record. The SEC hosts the fund's disclosure; it does not calculate a special USDC yield for Circle. The rate reflects fund expenses, so we do not deduct those fund expenses a second time.

For a concrete source check, the [June 2026 original report](https://www.sec.gov/Archives/edgar/data/844779/000119312526298262/primary_doc.xml), filed 8 July, contains a 30 June net-yield observation of **0.036**, or **3.60% annually**. Its same-date gross yield is 0.0369, or 3.69%. The [September original report](https://www.sec.gov/Archives/edgar/data/844779/000119312526416631/primary_doc.xml), filed 7 October, contains a 30 September net yield of **0.0384**, or **3.84%**, and gross yield of 3.93%. These individual endpoint observations are examples; neither is used as the entire quarter's yield.

The XML's relevant structure is `sevenDayNetYield`, containing `sevenDayNetYieldDate` and `sevenDayNetYieldValue`. The stored decimal must be converted to percentage points only for display. Monthly report dates, business observation dates and SEC filing dates are three different fields. Preserve all three.

### Mapping business observations to daily balances

Filter the fund reports to those filed by the chosen prediction cutoff before constructing a date-to-yield map. Exclude later amendments, even when they refer to an earlier economic month. For each model calendar date, select the last eligible business observation on or before that date. Weekends and holidays inherit the previous observation; they do not become missing USDC balance days. No future observation is interpolated backward.

Then multiply each day's USDC balance by that day's assigned annual fund yield divided by 365. Sum those daily contributions over the full quarter. The supply-weighted fund yield equals the sum of supply times assigned yield divided by the sum of supply. A simple mean of business-date yields would weight a low-balance day as heavily as a high-balance day and would ignore the different number of calendar days carried through weekends.

For the normal late cutoffs in this sample, the target quarter's last-month original fund report was already public. Availability must still be checked quarter by quarter. At the seven-days-after-quarter-end Q3 2026 cutoff of 7 October, the September report is eligible because it was filed that day. This is a date-level cutoff, not proof that the data existed at a chosen intraday morning time. Specify an intraday cutoff and compare SEC acceptance timestamps before claiming an intraday strategy.

If a required month is not yet public, do not insert its future yields. The historical implementation carries the last eligible observation and records its age. A prospective alternative is to bridge missing fund yields with contemporaneously available SOFR plus a lagged observed fund-to-SOFR relationship. That fallback has not been independently validated here and should be labeled as an additional assumption rather than silently combined with the fund backtest.

## Defining the six original methods

All methods use the same six target quarters and target actuals. For a benchmark rate, the supply-weighted annual yield uses daily supply as weights. For the previous company yield, we use previously reported reserve income divided by previously reported average USDC, annualized by 365 over the previous quarter's day count. The denominator is the company's reported average, not the provider's historical average. This choice retains an independent financial calibration and means supply-definition differences can affect the inferred gap.

### Prior income with a day adjustment

Multiply the previous quarter's reserve income by target-quarter days divided by previous-quarter days. This naive baseline knows the prior financial result and calendar, but does not update for the target quarter's supply or interest-rate changes. It is useful precisely because it is easy to implement and makes the incremental value of a richer model visible.

### Current supply with the prior earned yield

Multiply the target quarter's sum of daily USDC balances by the previous implied annual company yield and divide by 365. This updates balance exposure but assumes that earned yield does not change. It is a useful test of whether supply alone is sufficient when rates move.

### Current supply with uncalibrated SOFR

Sum daily balances times daily SOFR divided by 360. This updates both balances and a benchmark rate but assumes that all reserves earn the benchmark without a persistent company-to-benchmark difference. Its systematic overestimation in this sample shows why an observable rate is not automatically Circle's realized return.

### Current supply with the three month Treasury yield

Use the daily three-month Treasury constant-maturity series, carry the last business observation over non-reporting dates, and sum daily balance times annual quoted yield divided by 365. This is a quoted market-yield proxy, not a reconstruction of actual securities purchased, fund holdings, maturity ladders or cash reinvestment. It is included as a plausible simple alternative rather than an exact portfolio-income method.

### SOFR with the previous yield gap

Calculate the previous implied company yield. Subtract the previous supply-weighted SOFR after its 365/360 conversion. Carry that fixed annual percentage-point gap into the target quarter. The estimate is uncalibrated target-quarter SOFR income plus target-quarter balance exposure multiplied by the lagged gap and divided by 365.

The gap is an empirical bridge. Reserve allocation, fund expenses, deposit rates, small non-USDC income and balance-definition differences can all contribute. We cannot identify its exact economic components from this regression-free calibration alone. A stable gap is an assumption to test, not a disclosed contractual spread.

### Fund yield with the previous yield gap

Use the same architecture with the fund's net seven-day yield. Subtract the previous supply-weighted fund yield from the previous implied company yield, then add that gap to the target quarter's daily fund yields. The fund benchmark already incorporates its expenses, but it does not equal the return on all cash and other reserve assets. The lagged correction therefore remains necessary.

The formula can be explained without fitting a statistical model: first establish how the public benchmark related to Circle's realized yield last quarter; then update for this quarter's publicly observable benchmark and reserve balance. No target-quarter reserve-income outcome enters either calibrated prediction.

## Worked example for Q2 2026

Additional digits in the worked examples preserve arithmetic reproducibility; they do not establish that the source data or future forecasts are accurate to those digits. The target quarter has 91 calendar days. The previous quarter is Q1 2026. Its reported reserve income is **$652.508m**, average USDC is **$75,200.000m**, and its length is 90 days. These are lagged inputs; the target quarter's actual income is used only at the final scoring step. The information cutoff is **2026-08-04**, before the **2026-08-05** earnings release.

### Step one Calculate the previous earned yield

Divide the previous quarter's reserve income by its reported average USDC, then annualize over its actual day count. The calculation is 652.508000 / 75,200.000000 × 365 / 90 = **3.518992612%**. This is an implied annual yield proxy, not Circle's rounded return KPI and not the fund's own yield.

### Step two Assemble the target balance exposure

Read every calendar-date USDC observation for the target quarter and sum the balances. The total is **6,982,711.353501 million USDC days**. Dividing by 91 gives the provider's average balance of **$76,733.091797m**. Multiplying a changing daily yield by the quarter-end balance would not reproduce this exposure.

### Step three Read and align the fund yields

Use only original monthly Form N-MFP3 reports filed by 2026-08-04. For each calendar day, use the most recent business-date net seven-day yield whose observation date is not later than that day. Carry the prior observation through non-reporting dates; do not interpolate using a future yield. The longest carry in this target quarter is **3 calendar days**.

The previous quarter's USDC-weighted fund yield is **3.600284141%**. The target quarter's weighted fund yield is **3.570727382%**. Each is the sum of daily supply times the applicable annual yield, divided by that quarter's sum of daily supply. Thus the yield is weighted by capital exposure, not by the number of SEC observations.

### Step four Calibrate the gap and estimate fund income

Subtract the previous weighted fund yield from the previous implied Circle yield: 3.518992612% − 3.600284141% = **-0.081291529 percentage points**, or **-8.129153 basis points**. A negative number means the prior implied company yield was below this fund benchmark. It is not evidence of a contractual charge at that rate.

Before calibration, summing daily supply times daily fund yield divided by 365 gives **$683.105715995m**. The fixed lagged gap contributes 6,982,711.353501 × (-0.000812915287) / 365 = **$-15.551651512m**. Add the two to obtain **$667.554064482m**. The combined adjusted annual yield is **3.489435854%**.

### Step five Run the independent SOFR benchmark

SOFR is quoted on an actual over 360 convention. Sum daily supply times the applicable SOFR divided by 360. That produces **$702.007145449m** before calibration. Convert the lagged benchmark to the model's annual 365 basis before comparing it with Circle's implied yield: the lagged weighted SOFR equivalent is **3.710788835%**. Subtracting it from the implied Circle yield gives **-0.191796223 percentage points**.

The gap correction is 6,982,711.353501 × (-0.001917962228) / 365 = **$-36.691990748m**. The SOFR estimate is therefore **$665.315154701m**. This construction is equivalent to summing daily supply times the sum of SOFR multiplied by 365/360 and the lagged gap, all divided by 365.

### Step six Compare with the subsequently reported actual

Circle's original financial filing reports **$667.733000m** of reserve income for this quarter. The fund estimate differs by **$-0.178936m**, or **-0.026797%**. The SOFR estimate differs by **$-2.417845m**, or **-0.362098%**. Error equals estimated income divided by actual income minus one. Preserve the prediction before attaching the target; do not use this error to recalibrate the same quarter.


## Worked example for Q3 2026

The target quarter has 92 calendar days. The previous quarter is Q2 2026. Its reported reserve income is **$667.733m**, average USDC is **$76,524.000m**, and its length is 91 days. These are lagged inputs; the target quarter's actual income is used only at the final scoring step. The information cutoff is **2026-11-03**, before the **2026-11-04** earnings release.

### Step one Calculate the previous earned yield

Divide the previous quarter's reserve income by its reported average USDC, then annualize over its actual day count. The calculation is 667.733000 / 76,524.000000 × 365 / 91 = **3.499908166%**. This is an implied annual yield proxy, not Circle's rounded return KPI and not the fund's own yield.

### Step two Assemble the target balance exposure

Read every calendar-date USDC observation for the target quarter and sum the balances. The total is **6,763,917.231610 million USDC days**. Dividing by 92 gives the provider's average balance of **$73,520.839474m**. Multiplying a changing daily yield by the quarter-end balance would not reproduce this exposure.

### Step three Read and align the fund yields

Use only original monthly Form N-MFP3 reports filed by 2026-11-03. For each calendar day, use the most recent business-date net seven-day yield whose observation date is not later than that day. Carry the prior observation through non-reporting dates; do not interpolate using a future yield. The longest carry in this target quarter is **3 calendar days**.

The previous quarter's USDC-weighted fund yield is **3.570727382%**. The target quarter's weighted fund yield is **3.620163781%**. Each is the sum of daily supply times the applicable annual yield, divided by that quarter's sum of daily supply. Thus the yield is weighted by capital exposure, not by the number of SEC observations.

### Step four Calibrate the gap and estimate fund income

Subtract the previous weighted fund yield from the previous implied Circle yield: 3.499908166% − 3.570727382% = **-0.070819216 percentage points**, or **-7.081922 basis points**. A negative number means the prior implied company yield was below this fund benchmark. It is not evidence of a contractual charge at that rate.

Before calibration, summing daily supply times daily fund yield divided by 365 gives **$670.862689890m**. The fixed lagged gap contributes 6,763,917.231610 × (-0.000708192160) / 365 = **$-13.123707280m**. Add the two to obtain **$657.738982610m**. The combined adjusted annual yield is **3.549344565%**.

### Step five Run the independent SOFR benchmark

SOFR is quoted on an actual over 360 convention. Sum daily supply times the applicable SOFR divided by 360. That produces **$689.264364852m** before calibration. Convert the lagged benchmark to the model's annual 365 basis before comparing it with Circle's implied yield: the lagged weighted SOFR equivalent is **3.669528857%**. Subtracting it from the implied Circle yield gives **-0.169620690 percentage points**.

The gap correction is 6,763,917.231610 × (-0.001696206902) / 365 = **$-31.432885179m**. The SOFR estimate is therefore **$657.831479673m**. This construction is equivalent to summing daily supply times the sum of SOFR multiplied by 365/360 and the lagged gap, all divided by 365.

### Step six Compare with the subsequently reported actual

Circle's original financial filing reports **$657.624000m** of reserve income for this quarter. The fund estimate differs by **$0.114983m**, or **+0.017485%**. The SOFR estimate differs by **$0.207480m**, or **+0.031550%**. Error equals estimated income divided by actual income minus one. Preserve the prediction before attaching the target; do not use this error to recalibrate the same quarter.


## Results across all six target quarters

| Period | Actual USD m | SOFR gap USD m | Error | Fund gap USD m | Error |
| --- | --- | --- | --- | --- | --- |
| Q2 2025 | 634.274 | 633.095 | -0.186% | 631.591 | -0.423% |
| Q3 2025 | 711.241 | 709.903 | -0.188% | 710.060 | -0.166% |
| Q4 2025 | 733.396 | 730.779 | -0.357% | 731.909 | -0.203% |
| Q1 2026 | 652.508 | 646.662 | -0.896% | 648.677 | -0.587% |
| Q2 2026 | 667.733 | 665.315 | -0.362% | 667.554 | -0.027% |
| Q3 2026 | 657.624 | 657.831 | +0.032% | 657.739 | +0.017% |

The Q1 2026 miss is the largest for both original calibrated models: approximately −0.896% for SOFR and −0.587% for the fund method. Keeping that quarter in the sample is important. It demonstrates that the lagged relationship can change and that a small historical mean does not imply every future estimate will lie within 0.5%. No quarter is removed because it weakens the preferred model.

| Method | MAPE | MAE USD m | Worst absolute error |
| --- | --- | --- | --- |
| Prior income with day adjustment | 6.287% | 42.114 | 11.062% |
| Supply with prior earned yield | 3.281% | 22.614 | 8.636% |
| Supply with uncalibrated SOFR | 5.140% | 34.785 | 5.573% |
| Supply with three month Treasury yield | 4.970% | 32.819 | 11.072% |
| SOFR with prior yield gap | 0.337% | 2.268 | 0.896% |
| Fund yield with prior yield gap | 0.237% | 1.579 | 0.587% |

Mean absolute percentage error, or MAPE, is the average of the absolute value of estimated income divided by actual income minus one. MAE is the average absolute dollar difference in USD millions. The worst-quarter column reports the largest absolute percentage error. These metrics answer different questions: typical proportional accuracy, typical dollar exposure and the largest observed miss. They do not establish a probability distribution or a confidence interval from six observations.

Both original calibrated methods beat the carry-forward baseline in six of six quarters. Updating supply without updating yield improves the mean error from 6.287% to 3.281%, but still leaves meaningful rate-cycle exposure. Uncalibrated SOFR averages 5.140% error and overestimates all six actuals. Adding the lagged gap brings SOFR to 0.337%; the fund version reaches 0.237%. The fund advantage is about $0.688m in average absolute error, a small difference relative to the uncertainty of six observations and the supply-data tolerances.

The primary SOFR method was designated as the working model before this six-quarter calculation, although after the outcomes and feasibility pilot had been inspected. Keep it as the principal reproducible specification and the fund model as a challenger. Reporting only the best number after looking at several methods would overstate the evidence.

## Percentage point gaps versus proportional yield adjustments

The original rule assumes an additive yield gap persists. If the prior company yield is 3.50% and the prior fund yield is 3.57%, the gap is −0.07 percentage points, or −7 basis points. Subtracting 0.07 percentage points from a new 3.62% benchmark gives a 3.55% company-yield estimate. This is different from subtracting 7% of the yield.

A proportional alternative instead assumes the prior ratio of company yield to benchmark yield persists. In that illustration, multiply the new benchmark by 3.50/3.57. Additive and proportional rules can be close when the benchmark moves little, but diverge across interest-rate regimes. Neither is inherently the true reserve-income mechanism.

In a subsequent exploratory comparison, both ratios were tested on the same six quarters. Fund proportional MAPE is **0.156%**, compared with **0.237%** for its additive version; SOFR proportional MAPE is **0.193%**, compared with **0.337%**. Fund proportional improves five of six quarters and SOFR proportional four of six. Fund proportional MAE is approximately **$1.025m**, with worst-quarter absolute error **0.412%**.

This is an exploratory extension, not another independent validation sample. The report and dashboard show it as such and retain the original specifications. A future prospective test should freeze the chosen model before new earnings are known, rather than replace the primary model whenever another rule wins on the same small sample.

## Publication dates and information cutoffs

| Period | Early cutoff | Late cutoff | Earnings date |
| --- | --- | --- | --- |
| Q2 2025 | 2025-07-07 | 2025-08-11 | 2025-08-12 |
| Q3 2025 | 2025-10-07 | 2025-11-11 | 2025-11-12 |
| Q4 2025 | 2026-01-07 | 2026-02-24 | 2026-02-25 |
| Q1 2026 | 2026-04-07 | 2026-05-10 | 2026-05-11 |
| Q2 2026 | 2026-07-07 | 2026-08-04 | 2026-08-05 |
| Q3 2026 | 2026-10-07 | 2026-11-03 | 2026-11-04 |

The early estimate is taken seven calendar days after quarter-end. The late estimate uses the calendar day before the verified earnings release. At each cutoff, the immediately previous quarter's relevant financial inputs must already be public. At the first evaluation, we calculate an implied Q1 2025 yield from income and supply already public in the IPO prospectus rather than use a rounded Q1 yield first established in a later comparative disclosure.

The original fund early-cutoff MAPE is approximately **0.242%**, compared with **0.237%** late. SOFR is approximately **0.337%** in both phases. These results do not show that waiting until the day before earnings necessarily adds substantial information once a quarter has ended and the relevant sources are available. They also do not establish a tradable advantage over analyst consensus, which was not evaluated.

Financial source eligibility and historical data vintage are separate controls. A model can correctly exclude a late financial filing but still use a historical USDC series revised months later. The historical supply and rates here were downloaded on 21 November 2026. Fund originals are selected by filing date and two later amendments are excluded. The protocol was not a blind preregistration. Those limits must accompany the accuracy figures wherever they are reused.

## Sensitivities and sources of uncertainty

For Q3 2026, a 0.5% increase in modeled supply raises the primary SOFR estimate by about **$3.289m**; 1.0% raises it by **$6.578m**. Increasing the modeled annual earned yield by 0.25 percentage points over the full quarter adds approximately **$46.328m**. The latter is a 365-basis earned-yield sensitivity, not a 25-basis-point move in the quoted 360-basis SOFR. These are mechanical sensitivities, not predicted error bands.

Using following-date supply buckets in both target exposure and lagged benchmark calibration changes the primary estimate by approximately −$0.35m to +$1.43m across the six quarters; its mean absolute percentage error becomes about 0.31%. Both timing conventions remain imperfect proxies. A lower in-sample error does not prove that one bucket is the true end-of-day state.

The important remaining risks are reserve-mix changes, differences between bank and fund yields, euro reserve economics, changes in the yield-gap relationship, income-recognition timing, current-day partial observations, source outages and historical revisions. Some of these risks may be persistent and calibrated away for a while, then change abruptly. An explicit fund/cash/direct-securities decomposition and separate EURC model would be useful later, but the report does not pretend they have already been solved.

## A dated forward scenario

The preserved **21 November 2026** Q4 scenario estimates reserve income of **$674.311946m**. It uses observed supply through **20 November**, covering 51 calendar days, and projects the remaining 41 days. Last observed USDC is approximately **$68.811bn**, with future supply held flat and the assumed future SOFR held at **3.90%**. The lagged implied yield is **3.561165%**, the lagged 365-equivalent weighted SOFR is **3.719464%**, and the carried annual gap is **−0.158300 percentage points**.

The projected full-quarter average supply is approximately **$70.462bn**. Raw SOFR income is **$702.426366m**; the lagged gap reduces that amount by approximately **$28.114420m**, giving the reserve-income scenario. The quarter is unfinished and actual reserve income is unavailable in this snapshot. It is excluded from all six-quarter accuracy statistics.

The dashboard also maintains a separately dated cache from current public feeds. Its initial 22 November refresh is approximately **$674.660m**, with supply observed through 21 November, 52 observed days and 40 projected days. The cache can change as data arrive; the report's historical results and original 21 November scenario do not. Differences between versions can reflect revised inputs as well as another day's observations, so compare their source dates and model inputs before attributing a change to business performance.

The scenario controls change only assumed future supply and future quoted SOFR. They do not retroactively change observed days, the prior financial outcome or the historical backtest. Their outputs are conditional scenarios, not confidence intervals and not forecasts of profit or EPS.

## How to reproduce and maintain the research

Download the source USDC series and rate histories, preserving exact URLs, retrieval timestamps and hashes. Extract original financial observations into a unit-normalized ledger. Authenticate the fund series and extract original monthly observations with both economic and publication dates. Select a cutoff, enforce source eligibility, and construct complete calendar-day balance/rate pairs. Compute the lagged yield and benchmark relationship, calculate the target-quarter prediction, save it, and only then attach the actual for scoring.

The companion dashboard provides the quarterly comparison, all eight method variants, early and late cutoffs, a calculation walkthrough, source links and downloadable daily inputs. The daily CSV repeats calibration rows where they belong to different evaluations and cutoffs; it is an audit table, not a series to sum indiscriminately. The compact daily display contains 638 unique dates from Q1 2025 through Q3 2026.

The source calculations passed 269 recorded source, eligibility and arithmetic checks; an independent Stage 3 verifier passed 55 checks, and the later yield-rule comparison passed 48 arithmetic checks. These checks support implementation consistency. They do not establish future forecast accuracy. This report's publishing checks additionally tie displayed tables and dashboard values to the frozen research files and verify that new cache updates do not overwrite the backtest.

For prospective evidence, freeze model code, calibration, raw inputs and a timestamped estimate before the next earnings release. After the actual is public, append an evaluation without replacing the saved forecast. Track both original and revised financial targets, record why a source or model changed, and compare a fixed baseline over the same evaluation periods. Several genuinely prospective quarters would provide more convincing evidence than further optimization on this six-quarter sample.

## Financial source ledger

Locators refer to the archived HTML extraction used by this project; live website layout can change. The quarter's reserve-income input is separate from rounded press-release total revenue.

| Period | Ledger reference | Locator or derivation | Source |
| --- | --- | --- | --- |
| Q1 2025 | O013 | Row 186 col 1 | [Original filing](https://www.sec.gov/Archives/edgar/data/1876042/000119312525135795/d737521d424b4.htm) |
| Q2 2025 | O023 | Row 120 col 1 | [Original filing](https://www.sec.gov/Archives/edgar/data/1876042/000162828025039781/crcl-20250630.htm) |
| Q3 2025 | O033 | Row 120 col 1 | [Original filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604225000047/crcl-20250930.htm) |
| Q4 2025 | FY less 9M | 2,636.822 minus 1,903.426 | [FY filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000062/crcl-20251231.htm) |
| Q1 2026 | O047 | Row 127 col 1 | [Original filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000150/crcl-20260331.htm) |
| Q2 2026 | O057 | Row 128 col 1 | [Original filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000248/crcl-20260630.htm) |
| Q3 2026 | O067 | Row 126 col 1 | [Original filing](https://www.sec.gov/Archives/edgar/data/1876042/000187604226000311/crcl-20260930.htm) |

## Fund report archive

Each linked report is an original monthly filing used in the fund-yield extraction. Use its filing date to establish availability, not the month-end report date.

| Month | Filed | Business observations | SEC source |
| --- | --- | --- | --- |
| 2024-12 | 2025-01-07 | 21 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000114554925000837/primary_doc.xml) |
| 2025-01 | 2025-02-06 | 21 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000114554925006067/primary_doc.xml) |
| 2025-02 | 2025-03-06 | 19 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000114554925016532/primary_doc.xml) |
| 2025-03 | 2025-04-07 | 21 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000114554925024211/primary_doc.xml) |
| 2025-04 | 2025-05-07 | 21 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000114554925029363/primary_doc.xml) |
| 2025-05 | 2025-06-06 | 21 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000114554925038812/primary_doc.xml) |
| 2025-06 | 2025-07-07 | 20 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000114554925045932/primary_doc.xml) |
| 2025-07 | 2025-08-06 | 22 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000114554925050582/primary_doc.xml) |
| 2025-08 | 2025-09-08 | 21 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000114554925057954/primary_doc.xml) |
| 2025-09 | 2025-10-07 | 21 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000119312525233100/primary_doc.xml) |
| 2025-10 | 2025-11-07 | 23 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000119312525271132/primary_doc.xml) |
| 2025-11 | 2025-12-05 | 19 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000119312525309323/primary_doc.xml) |
| 2025-12 | 2026-01-07 | 22 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000119312526006231/primary_doc.xml) |
| 2026-01 | 2026-02-06 | 20 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000119312526040594/primary_doc.xml) |
| 2026-02 | 2026-03-05 | 19 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000119312526093396/primary_doc.xml) |
| 2026-03 | 2026-04-07 | 22 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000119312526144819/primary_doc.xml) |
| 2026-04 | 2026-05-06 | 21 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000119312526208592/primary_doc.xml) |
| 2026-05 | 2026-06-05 | 20 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000119312526258597/primary_doc.xml) |
| 2026-06 | 2026-07-08 | 21 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000119312526298262/primary_doc.xml) |
| 2026-07 | 2026-08-06 | 22 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000119312526337709/primary_doc.xml) |
| 2026-08 | 2026-09-08 | 21 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000119312526384920/primary_doc.xml) |
| 2026-09 | 2026-10-07 | 21 | [Original report](https://www.sec.gov/Archives/edgar/data/844779/000119312526416631/primary_doc.xml) |

## Full original method estimates

All entries below are USD millions. These are late-cutoff estimates; errors and early-cutoff results are available in the downloadable backtest CSV. The six original methods share the same target quarters. The two proportional variants are separately labeled exploratory in the dashboard.

| Period | Carry | Prior yield | Raw SOFR | Treasury | SOFR gap | Fund gap |
| --- | --- | --- | --- | --- | --- | --- |
| Q2 2025 | 564.11 | 634.72 | 665.27 | 663.02 | 633.09 | 631.59 |
| Q3 2025 | 641.24 | 709.16 | 746.11 | 723.69 | 709.90 | 710.06 |
| Q4 2025 | 711.24 | 795.68 | 773.97 | 738.12 | 730.78 | 731.91 |
| Q1 2026 | 717.45 | 708.86 | 688.87 | 684.98 | 646.66 | 648.68 |
| Q2 2026 | 659.76 | 673.21 | 702.01 | 713.44 | 665.32 | 667.55 |
| Q3 2026 | 675.07 | 648.58 | 689.26 | 730.44 | 657.83 | 657.74 |

## Data and methodology references

- [Circle transparency and reserve assurance reports](https://www.circle.com/transparency)
- [DefiLlama USDC history API](https://stablecoins.llama.fi/stablecoin/2)
- [DefiLlama filtered USDC chart API](https://stablecoins.llama.fi/stablecoincharts/all?stablecoin=2)
- [DefiLlama daily reconciliation code](https://github.com/DefiLlama/peggedassets-server/blob/master/src/peggedAssets/storePeggedAssets/reconcileDailyFromHourly.ts)
- [New York Fed SOFR reference information](https://www.newyorkfed.org/markets/reference-rates/sofr)
- [FRED three month Treasury series DGS3MO](https://fred.stlouisfed.org/series/DGS3MO)
- [Circle native USDC contract registry](https://developers.circle.com/stablecoins/usdc-contract-addresses)

The research archive retains original observations and source hashes. The report explains a method and its measured historical limits; it does not extend the findings to total earnings or equity value.
