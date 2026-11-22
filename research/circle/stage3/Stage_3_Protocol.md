# Circle historical reserve income test

Protocol fixed on 21 November 2026 before calculating the six-quarter results. The financial outcomes and Q3 pilot have already been viewed, so this is a retrospective evaluation, not a blind holdout.

## Scope and accepted tolerance

Evaluate Q2 2025 through Q3 2026. Use Q1 2025 as the initial lagged financial period. The user's accepted supply tolerance is an absolute difference of 0.5% preferred and 1.0% as the outer limit. This applies to supply comparisons, not earnings prediction errors. Preserve the earlier 0.10% investigation threshold as historical work, and report the new acceptance decision separately. A small comparison gap does not prove identical definitions or observation times.

Use the provider's as-labeled daily supply as the primary convention, with following-date buckets as an alignment sensitivity. Do not force a correction based on contemporaneous reported average supply. All seven observed quarter-end comparison gaps pass the preferred tolerance. Test quarter-average differences separately.

## Information cutoffs

Two cutoffs per quarter: seven calendar days after quarter-end (early estimate), and the day before the verified earnings release (late estimate). Financial inputs and fund filings must have been published by the relevant cutoff. A later filing may establish an evaluation target but cannot enter an earlier forecast. When a lagged quarter is unavailable, keep the affected model unavailable rather than use it retroactively. Current provider history is not a vintage archive. Call results publication-filtered historical simulations using current history, not strict point-in-time forecasts.

## Fixed model rules

1. Carry forward prior-quarter reserve income, adjusted for quarter length.
2. Daily supply times the prior-quarter implied effective annual yield: prior reserve income / prior reported average USDC * 365 / prior quarter days. This is an all-in reserve-income proxy, including effects outside USDC. It is not a disclosed contractual return. Prefer this to inserting an originally unavailable rounded Q1 yield.
3. Daily supply times SOFR, ACT/360, and daily supply times the three-month Treasury benchmark, ACT/365 approximation. Forward-fill only earlier rate dates.
4. Daily supply times SOFR with the previous quarter's effective yield spread held constant. Translate SOFR to ACT/365 equivalent before subtracting it from the implied yield. No fit to the quarter being forecast.
5. Fund-aware model if adequate original monthly disclosures can be recovered: use the latest eligible observation for each economic date, taking the first original monthly filing eligible by the cutoff. Carry forward an earlier eligible yield for uncovered dates, never fill backward from future economic dates. Use net seven-day yields as an income-rate proxy, not actual dividends. Calibrate the previous quarter's spread against a fully disclosed prior fund quarter where available. Explicitly label a fund-based proxy if complete cash/portfolio allocation is unavailable.

Do not tune model definitions or weights after viewing the error table. Report signed percentage errors, mean absolute percentage errors, monetary errors, worst quarter, availability counts, and common-sample comparisons. Six quarters do not establish robust predictive skill. Separate rate/supply diagnostics from model inputs. Report sensitivity to +/-0.5% and +/-1.0% supply, and yield changes.

Use model 4 (SOFR with a lagged effective spread) as the working reserve-income input to the RLDC bridge. The fund model is a challenger, not a model selected after comparing errors. This designation is made before executing the model results.

## RLDC and other revenue

For each cutoff, use the prior eligible quarter's other revenue and total distribution/transaction/other costs divided by reserve income. Predict total revenue and RLDC separately from reserve income. Report a +/-5 percentage-point effective cost-ratio sensitivity as an illustrative range, not a probability interval or a partner contract formula. ARC-related current-quarter reported revenue must not be added as an ex-ante input without dated evidence. Keep actuals available only for scoring and diagnostics.

## Future work explicitly requested by the user

Investigate whether Circle's growing non-reserve revenue can be independently verified on-chain. For each product, map revenue recognition to observable contracts, fees, settlements, or token events. Establish whether activity translates into Circle revenue, distinguish cash receipts from recognized revenue, and quantify what remains private. ARC, payments/transaction services, and tokenized-fund activity are candidate areas to investigate, not established fully observable revenue streams. This is a later research extension, not a prerequisite for the reserve-income test.

## Deliverables

A reproducible local pipeline, original-source archive and publication manifest, six-quarter results with explicit exclusions, a formula-driven workbook, and a plain-language findings note. Report remaining historical-vintage, portfolio, and private distribution limitations alongside the results.
