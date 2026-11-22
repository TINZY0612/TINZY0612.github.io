# TINZY0612.github.io

Website: https://ziyik0612.me

Screen typography is shared through `assets/site-typography.css`, using self-hosted Inter 4.1 with system fallbacks for other scripts. The font license is retained in `assets/fonts/Inter-LICENSE.txt`. Code and equation text retain monospace styling; print styles remain separate.

After adding or regenerating HTML pages, run `node scripts/sync-site-typography.cjs` to include the shared stylesheet. It is safe to run again.

Circle uses the homepage's actual header and footer markup, shared stylesheets and palette. Run `node scripts/sync-circle-shell.cjs` after changing the homepage header/footer or regenerating the Circle web report. Research downloads and source links stay within the page, below the global navigation.
