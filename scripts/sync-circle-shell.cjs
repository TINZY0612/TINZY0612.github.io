const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const home = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const header = home.match(/<header class="site-topbar">[\s\S]*?<\/header>/)?.[0]
  .replace('<a href="/circle/">', '<a href="/circle/" aria-current="page">');
const footer = home.match(/<footer class="site-footer">[\s\S]*?<\/footer>/)?.[0];
if (!header || !footer) throw new Error('Homepage header or footer is missing.');

for (const name of ['index.html', 'report.html']) {
  const file = path.join(root, 'circle', name);
  const original = fs.readFileSync(file, 'utf8');
  let html = original;
  const report = name === 'report.html';
  if (report && !html.includes('class="report-actions"')) {
    const actions = html.match(/<header>[\s\S]*?<nav>([\s\S]*?)<\/nav><\/header>/)?.[1];
    if (!actions) throw new Error('Report actions are missing.');
    html = html.replace(/<header>[\s\S]*?<\/header>/, `${header}\n<nav class="report-actions" aria-label="Report actions">${actions}</nav>`);
  } else {
    html = html.replace(/<header class="(?:site-header|site-topbar)">[\s\S]*?<\/header>/, header);
  }
  if (!html.includes('class="site-footer"')) {
    const metadata = html.match(/<footer>([\s\S]*?)<\/footer>/)?.[1];
    if (!metadata) throw new Error(`Research metadata is missing: ${name}`);
    html = html.replace(/<footer>[\s\S]*?<\/footer>/, `<div class="research-footer">${metadata}</div>\n${footer}`);
  } else {
    html = html.replace(/<footer class="site-footer">[\s\S]*?<\/footer>/, footer);
  }
  const bodyClass = report ? 'site-circle-report-page' : 'site-circle-page';
  html = html.replace(/<body[^>]*>/, `<body class="${bodyClass}" data-page-navigation="custom">`);
  html = html.replace(/<link[^>]*href="(?:\/assets\/site-footer\.css|site-theme\.css|\/assets\/site-topbar\.css)(?:\?[^"]*)?"[^>]*>/g, '');
  if (!report) html = html.replace(/href="dashboard\.css(?:\?[^"]*)?"/, 'href="dashboard.css?v=circle-shell-2"')
    .replace(/src="dashboard\.js(?:\?[^"]*)?"/, 'src="dashboard.js?v=reserve-monitor-v2"');
  for (const href of ['/assets/site-footer.css?v=circle-shell-2', 'site-theme.css?v=circle-shell-2', '/assets/site-topbar.css?v=circle-shell-2']) {
    if (!html.includes(`href="${href}"`)) html = html.replace('</head>', `<link rel="stylesheet" href="${href}"></head>`);
  }
  if (!html.includes('/favicon.svg')) html = html.replace('</head>', '<link rel="icon" type="image/svg+xml" href="/favicon.svg?v=3"></head>');
  if (html !== original) fs.writeFileSync(file, html, 'utf8');
}
console.log('Circle dashboard and report now share the homepage header and footer.');
