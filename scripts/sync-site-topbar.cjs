const fs = require('node:fs');
const path = require('node:path');

const root = path.resolve(__dirname, '..');

function pagesIn(directory) {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = path.join(directory, entry.name);
    if (entry.isDirectory() && entry.name !== '.git') return pagesIn(fullPath);
    return entry.isFile() && entry.name === 'index.html' ? [fullPath] : [];
  });
}

function headerFor(page) {
  const active = page === 'resume' ? 'resume' : page === 'news' || page.startsWith('news/') ? 'news' : '';
  const current = (name) => active === name ? ' aria-current="page"' : '';
  return `  <header class="site-topbar">
    <a class="site-topbar__brand" href="/">ZI<span>YIK</span></a>
    <nav class="site-topbar__nav" aria-label="Primary navigation">
      <a href="/resume/"${current('resume')}>Resume</a>
      <a href="/news/"${current('news')}>AI Projects</a>
    </nav>
    <div class="site-topbar__social" aria-label="Social links">
      <a href="https://www.linkedin.com/in/tin-zi-yik/" target="_blank" rel="noopener noreferrer" aria-label="LinkedIn">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.476-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 1 1 0-4.123 2.062 2.062 0 0 1 0 4.123zM7.119 20.452H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
      </a>
      <a href="https://github.com/TINZY0612/" target="_blank" rel="noopener noreferrer" aria-label="GitHub">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .5C5.65.5.5 5.65.5 12c0 5.09 3.29 9.4 7.86 10.93.58.11.79-.25.79-.56v-2.17c-3.2.7-3.87-1.37-3.87-1.37-.53-1.34-1.28-1.7-1.28-1.7-1.04-.71.08-.7.08-.7 1.15.08 1.76 1.18 1.76 1.18 1.02 1.75 2.68 1.25 3.33.96.1-.74.4-1.25.73-1.54-2.55-.29-5.23-1.28-5.23-5.7 0-1.26.45-2.29 1.18-3.1-.12-.29-.51-1.47.11-3.07 0 0 .96-.31 3.15 1.18A10.9 10.9 0 0 1 12 8.35c.97 0 1.94.13 2.85.38 2.18-1.49 3.14-1.18 3.14-1.18.62 1.6.23 2.78.11 3.07.74.81 1.18 1.84 1.18 3.1 0 4.43-2.69 5.4-5.25 5.69.41.36.78 1.08.78 2.18v3.23c0 .31.21.67.8.56A11.5 11.5 0 0 0 23.5 12C23.5 5.65 18.35.5 12 .5Z"/></svg>
      </a>
      <a href="https://x.com/ZiYik0612" target="_blank" rel="noopener noreferrer" aria-label="X / Twitter">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231Zm-1.161 17.52h1.833L7.083 4.126H5.117Z"/></svg>
      </a>
    </div>
  </header>`;
}

for (const file of pagesIn(root)) {
  const page = path.relative(root, path.dirname(file)).replaceAll('\\', '/');
  const pageName = page === '' ? 'home' : page.startsWith('news/') ? 'report' : page;
  const eol = fs.readFileSync(file).includes(Buffer.from('\r\n')) ? '\r\n' : '\n';
  let html = fs.readFileSync(file, 'utf8');
  const header = headerFor(page).replaceAll('\n', eol);
  const sharedHeader = /<header class="site-topbar">[\s\S]*?<\/header>/;
  const oldHeader = /<header class="topbar">[\s\S]*?<\/header>/;
  const oldNav = /<nav class="nav" aria-label="Primary navigation">[\s\S]*?<\/nav>/;

  if (sharedHeader.test(html)) html = html.replace(sharedHeader, header.trimStart());
  else if (oldHeader.test(html)) html = html.replace(oldHeader, header.trimStart());
  else if (oldNav.test(html)) html = html.replace(oldNav, header.trimStart());
  else if (!html.includes('class="site-topbar"')) {
    const skip = /(<a class="skip-link" href="#main-content">Skip to content<\/a>)/;
    if (!skip.test(html)) throw new Error(`Missing skip link: ${file}`);
    html = html.replace(skip, `$1${eol}${header}`);
  }

  if (!html.includes('class="site-topbar"')) throw new Error(`Missing site header: ${file}`);
  const body = /<body(?: class="([^"]*)")?>/;
  if (!body.test(html)) throw new Error(`Missing body tag: ${file}`);
  html = html.replace(body, (_, classes = '') => `<body class="${[...new Set([...classes.split(' ').filter(Boolean), `site-${pageName}-page`])].join(' ')}">`);
  if (!html.includes('/assets/site-topbar.css')) html = html.replace('</head>', `  <link rel="stylesheet" href="/assets/site-topbar.css">${eol}</head>`);

  fs.writeFileSync(file, html, 'utf8');
}

console.log('Synchronized site navigation across all HTML pages.');
