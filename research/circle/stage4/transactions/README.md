# Reproduce the transaction extension

Read Findings.md for results and Protocol.md for the fixed comparison rules.

From the Trading Agent workspace, run the bundled Python with `-X utf8`:

1. `python -X utf8 Circle/stage4/transactions/analyze.py`
2. `node Circle/stage4/transactions/build_workbook.mjs`
3. `python -X utf8 Circle/stage4/transactions/verify.py`

The node_modules junction points to the bundled Artifact Tool runtime. No dependencies were installed. The saved workbook is under Circle/outputs/01a1fcd4-2a0f-7c92-a89f-a871c89c1db7. The financial ledger, original filings and downloaded CCTP series from earlier stages are required inputs. No private credentials or paid data are used.

`results/transaction_backtest.json` records every estimate, cutoff, calibration quarter, date-coverage result and error. `results/workbook_inspection.json` records formula checks and an input-change/recalculation/restore test. `results/verification.json` independently recomputes fee bridges, checks exported cached values and records source hashes. Workbook rendering covers all three worksheets. Native Excel application recalculation is not separately tested.

The optional `collect.py` downloads total stablecoin history and FRED CBBTCUSD daily prices for empirical factor correlations. These failed DNS resolution in this run, so no factor-correlation result is claimed. It also attempts to archive current redemption-policy evidence; that policy was read using the web tool when the host download failed. Existing current histories are not historical data vintages.

No source file, historical result, original workbook or dated Q4 forecast was overwritten by this extension.
