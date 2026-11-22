# Zi Yik portfolio and research

Website: https://ziyik0612.me

## Circle reserve income research

Can public USDC balances and interest-rate disclosures estimate Circle's reserve income before earnings? This project combines on-chain balance data, fund filings and traditional financial analysis to test that hypothesis.

- **[Project README, source data, code and test results](https://github.com/TINZY0612/circle-reserve-income-research)**
- [Interactive dashboard](https://ziyik0612.me/circle/) and [online report](https://ziyik0612.me/circle/report.html)
- [Latest PDF](circle/Circle_Reserve_Income_Report.pdf) and [editable Word report](circle/Circle_Reserve_Income_Report.docx)
- [Data dictionary](https://github.com/TINZY0612/circle-reserve-income-research/blob/main/DATA_DICTIONARY.md) and [reproduction guide](https://github.com/TINZY0612/circle-reserve-income-research/blob/main/TEST_RESULTS.md)

The fund-yield model with a prior yield ratio recorded **0.156% mean absolute percentage error across six historical quarters**. These are retrospective tests, not six forecasts recorded before earnings, and the selected method was compared on the same sample. Future accuracy remains to be validated. The completed report covers reserve income; other revenue, distribution costs and EPS remain separate extensions.

The research archive contains public source downloads and extraction/results files, including large compressed Ethereum event logs. Credentials, licensed Refinitiv exports and installed dependencies are excluded. Start with the project README rather than downloading the whole archive for a first review.

## Website maintenance

Screen typography is shared through `assets/site-typography.css`, using self-hosted Inter 4.1 with system fallbacks for other scripts. The font license is retained in `assets/fonts/Inter-LICENSE.txt`. Code and equation text retain monospace styling; print styles remain separate.

After adding or regenerating HTML pages, run `node scripts/sync-site-typography.cjs` to include the shared stylesheet. It is safe to run again.

Circle uses the homepage's actual header and footer markup, shared stylesheets and palette. Run `node scripts/sync-circle-shell.cjs` after changing the homepage header/footer or regenerating the Circle web report. Research downloads and source links stay within the page, below the global navigation.
