# Circle distribution costs and RLDC

Completed 21 November 2026. Start with [Findings.md](Findings.md). This is Stage 5A, extending the existing reserve nowcast into a distribution-cost and retained-revenue forecast.

## Reproduce saved analysis

From the Circle folder, using the bundled Python/Node runtimes:

```text
python -X utf8 stage5/rldc/analyze.py
python -X utf8 stage5/rldc/forecast.py
node stage5/rldc/build_workbook.mjs
python -X utf8 stage5/rldc/verify.py
python -X utf8 stage5/rldc/build_findings.py
```

Existing dependencies are NumPy-compatible analytical inputs, lxml and pypdf, plus bundled `@oai/artifact-tool`. No paid data, credentials or packages installed for this task. The authoring script resolves the existing Stage 5 runtime junction. Output is `../../outputs/01a1fcd4-2a0f-7c92-a89f-a871c89c1db7/Circle_RLDC_Projection.xlsx`.

`collect_sources.py` caches original public Coinbase earnings exhibits, the SEC submissions register, source slides and Circle–Coinbase agreements. Raw responses are never silently overwritten. Requests rejected for a bad URL remain in the manifest; corrected SEC accession index requests succeeded. The later versioned Q1 PDF is retained as context but original SEC data supply historical model inputs. Sources and successful-response hashes are verified independently.

The public contract descriptions explain the financial mechanism, but redacted definitions and unavailable eligible-balance histories limit exact contract reconstruction. Coinbase combined USDC income is a proxy; total Circle costs minus that proxy is an unclassified residual. Changed Circle comparative payment amounts stay in their own dated ledger and do not contaminate the headline aggregate-cost rules.

`Protocol.md` lists all eight methods and the source-driven residual definition before fitting. The experiment has only six target quarters and uses outcomes already viewed, plus current historical supply/rate vintages. The chronological split is a retrospective robustness diagnostic, not an unseen test. Earlier partner publication is explicitly distinguished from the pre-partner information set.

In the workbook, the primary Q4 method selector is 1 pooled-three-quarter ratio, 2 latest-quarter ratio, or 3 fixed-decay exponential ratio. One active cost-ratio driver feeds the same Q4 calculation. Future supply and SOFR inputs are on `Reserve build`; non-ARC other revenue and ARC recognition are on `RLDC`. Historical actuals are separate on `Inputs`. The historical method table compares distinct formulas on the same six quarters. Native Excel application recalculation was not tested.

`results/2026-11-21_Q4_RLDC_forecast.json` is a prospective scenario with actual null. Its writer refuses to overwrite changed inputs. The $60.4m ARC timing remains conditional, and flat non-ARC revenue is the user's assumption. These do not replace earlier dated guidance or ARC records. Opex, EPS and valuation remain the subsequent stages.
