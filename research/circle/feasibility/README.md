# Reproducing the Circle feasibility test

`Feasibility_Report.md` contains the decision and findings. This is a source-access and accounting pilot, not an out-of-sample backtest.

## Files

- `raw/`: original downloaded responses, including failures where response bodies were available.
- `source_manifest.json`: initial source and RPC checks.
- `rpc_supplement_manifest.json`: historical-state tests on three providers.
- `checkpoint_manifest.json`: original reserve PDFs, adapter code, and four month-end RPC checks.
- `q2_manifest.json`: source metadata for the prior-quarter filing.
- `fund_sources_manifest.json`: regulatory XML and holdings-export access results.
- `results/feasibility_summary.json`: calculated findings.
- `results/q3_daily_inputs.json`: 92 daily observations used in the pilot.
- `results/q3_reported_actuals.json`: extracted statement values and reconciled RLDC.
- `results/ethereum_checkpoints.json`: source blocks, hashes, raw token integers, provider agreement, and aggregator differences.
- `results/usdxx_september_regulatory_data.json`: extracted fund identification, filing date, NAV, and rolling-yield observations.
- `results/quality_checks.json`: the 34 analytical checks.
- `extracted/` and `previews/`: PDF extraction and visual inspection support files.

## Run the analysis offline

Use Python 3.11+ with `lxml` and `pypdf`. Both were available in the Codex bundled Python runtime for this run. From the Circle folder:

```text
python feasibility/analyze_feasibility.py
```

This reads saved responses and regenerates the result JSON files. It does not request new data.

## Refresh network checks

The collectors use standard-library HTTP requests with certificate verification. No API keys, wallet keys, signing, or transaction submission are used.

```text
python feasibility/collect_sources.py
python feasibility/check_historical_rpc.py
python feasibility/validate_chain_checkpoints.py
```

Refreshing replaces the named raw snapshots and corresponding manifests with today's responses. Copy the folder first if preserving this run. Rerun the offline analysis only after confirming all required sources succeeded. The initial collector does not download the supplemental Q2 PDF or fund regulatory XML; their exact URLs and checksums are in `q2_manifest.json` and `fund_sources_manifest.json`.

Economic dates are distinct from retrieval dates. In particular, the rolling fund yield observations were published in a later monthly regulatory filing. The present files are sufficient to reproduce this feasibility analysis, but they are not historical vintages of every data provider.
