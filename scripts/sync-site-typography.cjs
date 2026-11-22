const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');

function pagesIn(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap(entry => {
    if (entry.name === '.git') return [];
    const file = path.join(directory, entry.name);
    return entry.isDirectory() ? pagesIn(file) : entry.name.endsWith('.html') ? [file] : [];
  });
}

let updated = 0;
for (const file of pagesIn(root)) {
  const original = fs.readFileSync(file, 'utf8');
  const eol = original.includes('\r\n') ? '\r\n' : '\n';
  let html = original;
  // These older pages pointed a font source at a CSS response, not a font file.
  html = html.replace(/^[ \t]*@font-face\s*\{[^}]*src:url\('https:\/\/fonts\.googleapis\.com\/css2\?family=Noto\+Sans\+SC[^}]*\}\r?\n/gm, '');
  if (!html.includes('/assets/site-typography.css')) {
    html = html.replace('</head>', `  <link rel="stylesheet" href="/assets/site-typography.css">${eol}</head>`);
  }
  if (html !== original) {
    fs.writeFileSync(file, html, 'utf8');
    updated++;
  }
}
console.log(`Shared typography: ${updated} pages updated.`);
