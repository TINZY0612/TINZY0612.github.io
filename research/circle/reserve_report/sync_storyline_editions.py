"""Refresh the web and text editions from the same user-formatted Word report.

This never generates a new Word design. Existing external link relationships
and body order are read from the current authoritative DOCX.
"""
import html
import json
from pathlib import Path
import re
import shutil
import zipfile
from lxml import etree as ET

ROOT = Path(__file__).resolve().parent
SITE = ROOT/'site/circle'
DOCX = ROOT/'Circle_Reserve_Income_Report.docx'
W='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
R='http://schemas.openxmlformats.org/officeDocument/2006/relationships'
NS={'w':W,'r':R,'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
with zipfile.ZipFile(DOCX) as z:
    document=ET.fromstring(z.read('word/document.xml'))
    relations=ET.fromstring(z.read('word/_rels/document.xml.rels'))
links={x.get('Id'):x.get('Target') for x in relations if x.get('TargetMode')=='External'}
image_links={x.get('Id'):x.get('Target') for x in relations if x.get('Type','').endswith('/image') and x.get('TargetMode')!='External'}


def raw_text(node):return ''.join(node.xpath('.//w:t/text()',namespaces=NS))


def inline_md(node):
    pieces=[]
    for child in node:
        local=ET.QName(child).localname
        if local=='r':
            value=raw_text(child)
            bold=child.find('w:rPr/w:b',NS)
            if bold is not None and bold.get('{'+W+'}val','1') not in ['0','false'] and value.strip():value='**'+value+'**'
            pieces.append(value)
        elif local=='hyperlink':
            value=raw_text(child);target=links.get(child.get('{'+R+'}id'))
            pieces.append('['+value+']('+target+')' if target else value)
        elif local not in ['pPr','bookmarkStart','bookmarkEnd','proofErr']:
            pieces.append(raw_text(child))
    return ''.join(pieces).replace('****','')


blocks=[]
for node in document.find('w:body',NS):
    local=ET.QName(node).localname
    if local=='p':
        for drawing in node.xpath('.//a:blip',namespaces=NS):
            target=image_links.get(drawing.get('{'+R+'}embed'))
            if not target or not target.startswith('media/') or '..' in target.split('/'):
                raise ValueError('Unexpected report image relationship')
            name=Path(target).name
            asset=SITE/'assets/report'/name
            asset.parent.mkdir(parents=True,exist_ok=True)
            with zipfile.ZipFile(DOCX) as z:
                asset.write_bytes(z.read('word/'+target))
            markdown_asset=ROOT/'assets/report'/name
            markdown_asset.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(asset,markdown_asset)
            blocks.append('![Signed prediction error for fund yield with prior yield ratio](assets/report/'+name+')')
        style=node.find('w:pPr/w:pStyle',NS);style=style.get('{'+W+'}val') if style is not None else ''
        value=inline_md(node)
        if not value.strip():continue
        if style=='Title':blocks.append('# '+raw_text(node))
        elif style.startswith('Heading') and style[-1:].isdigit():blocks.append('#'*(int(style[-1])+1)+' '+raw_text(node))
        elif style=='ListBullet':blocks.append('- '+value)
        else:blocks.append(value)
    elif local=='tbl':
        rows=[]
        for row in node.findall('w:tr',NS):
            cells=[]
            for cell in row.findall('w:tc',NS):
                cells.append(' '.join(inline_md(p) for p in cell.findall('w:p',NS)).replace('|','/'))
            rows.append(cells)
        blocks.append('\n'.join(['| '+' | '.join(rows[0])+' |','| '+' | '.join('---' for _ in rows[0])+' |']+['| '+' | '.join(row)+' |' for row in rows[1:]]))
markdown='\n\n'.join(blocks)+'\n'
(ROOT/'Circle_Reserve_Income_Report.md').write_text(markdown,encoding='utf8')
(SITE/'report.md').write_text(markdown,encoding='utf8')


def inline(value):
    value=html.escape(value)
    value=re.sub(r'\[([^]]+)\]\((https?://[^)]+)\)',r'<a href="\2">\1</a>',value)
    return re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',value)


rendered=[];toc=[];used={}
for block in blocks:
    if block.startswith('#'):
        match=re.match(r'^(#+) (.+)',block);level=len(match[1]);title=match[2]
        anchor=re.sub('[^a-z0-9]+','-',title.lower()).strip('-');used[anchor]=used.get(anchor,0)+1
        if used[anchor]>1:anchor+='-'+str(used[anchor])
        if title.endswith('Financial actuals and announcement sources'):rendered.append('<span id="financial-source-ledger"></span>')
        if title.endswith('Original fund report archive'):rendered.append('<span id="appendix-d-original-fund-report-archive"></span>')
        rendered.append(f'<h{level} id="{anchor}">{html.escape(title)}</h{level}>')
        if level==2:toc.append(f'<a href="#{anchor}">{html.escape(title)}</a>')
    elif block.startswith('!['):
        match=re.fullmatch(r'!\[([^]]+)\]\((assets/report/[^)]+)\)',block)
        if not match:raise ValueError('Unexpected report figure')
        rendered.append('<figure class="report-figure"><img src="'+html.escape(match[2],quote=True)+'" alt="'+html.escape(match[1],quote=True)+'" loading="lazy"></figure>')
    elif block.startswith('|'):
        rows=[[c.strip() for c in line.strip('|').split('|')] for line in block.splitlines()]
        rows=[r for r in rows if not all(re.fullmatch('[-: ]+',c) for c in r)]
        rendered.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+inline(c)+'</th>' for c in rows[0])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in row)+'</tr>' for row in rows[1:])+'</tbody></table></div>')
    elif block.startswith('- '):rendered.append('<ul><li>'+inline(block[2:])+'</li></ul>')
    else:rendered.append('<p>'+inline(block)+'</p>')
title=raw_text(document.find('w:body/w:p',NS))
page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Circle Reserve Income Research | Zi Yik</title><meta name="description" content="From hypothesis to evidence: testing public-data methods for Circle reserve income and the next step toward EPS."><link rel="stylesheet" href="report.css"></head><body><header><a href="/">ZI YIK</a><nav><a href="./">Reserve dashboard</a><a href="Circle_Reserve_Income_Report.pdf">Download PDF</a><a href="Circle_Reserve_Income_Report.docx">Download Word report</a><button type="button" onclick="window.print()">Print or save PDF</button></nav></header><div class="report-layout"><aside aria-label="Report contents"><p>IN THIS REPORT</p>'''+''.join(toc)+'''</aside><main><p class="eyebrow">INDEPENDENT RESEARCH / RESERVE INCOME</p>'''+ '\n'.join(rendered)+'''</main></div><footer>Zi Yik · Research dated 22 November 2026 · Historical results retain the 21 November data vintage</footer></body></html>'''
page=page.replace('</head>','<link rel="stylesheet" href="/assets/site-typography.css"></head>')
page=page.replace('href="Circle_Reserve_Income_Report.pdf"','href="Circle_Reserve_Income_Report.pdf?v=20261122-chart"').replace('href="Circle_Reserve_Income_Report.docx"','href="Circle_Reserve_Income_Report.docx?v=20261122-chart"')
page=page.replace('<button type="button" onclick="window.print()">','<a href="https://github.com/TINZY0612/TINZY0612.github.io/tree/main/research/circle">Data and code</a><button type="button" onclick="window.print()">')
# Keep the reviewed website chrome when refreshing the report's body from Word.
previous_web=SITE/'report.html'
if previous_web.exists():
    previous=previous_web.read_text(encoding='utf8')
    shared_header=re.search(r'<header class="site-topbar">[\s\S]*?</header>',previous)
    shared_footer=re.search(r'<footer class="site-footer">[\s\S]*?</footer>',previous)
    if shared_header and shared_footer:
        actions=re.search(r'<header>[\s\S]*?<nav>([\s\S]*?)</nav></header>',page).group(1)
        page=re.sub(r'<header>[\s\S]*?</header>',lambda _:shared_header.group(0)+'<nav class="report-actions" aria-label="Report actions">'+actions+'</nav>',page,count=1)
        page=re.sub(r'<footer>([\s\S]*?)</footer>',lambda m:'<div class="research-footer">'+m.group(1)+'</div>'+shared_footer.group(0),page,count=1)
        page=page.replace('<body>','<body class="site-circle-report-page" data-page-navigation="custom">')
        for href in re.findall(r'<link[^>]*href="([^"]+)"',previous):
            if 'site-footer.css' in href or 'site-topbar.css' in href or 'site-theme.css' in href:
                page=page.replace('</head>','<link rel="stylesheet" href="'+href+'"></head>')
        page=page.replace('</head>','<link rel="icon" type="image/svg+xml" href="/favicon.svg?v=3"></head>')
(SITE/'report.html').write_text(page,encoding='utf8')
css=SITE/'report.css';text=css.read_text(encoding='utf8');text=text.replace('font-family:Aptos,Inter,','font-family:Inter,')
if 'h4{' not in text:text+='\nh4{font-size:16px;line-height:1.45;margin:23px 0 10px;color:#203b52}\n'
if '.report-figure{' not in text:text+='\n.report-figure{margin:24px 0;break-inside:avoid}.report-figure img{display:block;width:100%;height:auto}\n'
css.write_text(text,encoding='utf8')
initial=ROOT/'revisions/2026-11-22_initial_generated_report.docx'
if not initial.exists():shutil.copyfile(SITE/'Circle_Reserve_Income_Report.docx',initial)
shutil.copyfile(DOCX,SITE/DOCX.name)
if (ROOT/'Circle_Reserve_Income_Report.pdf').exists():shutil.copyfile(ROOT/'Circle_Reserve_Income_Report.pdf',SITE/'Circle_Reserve_Income_Report.pdf')
# Keep the unpublished integration checkout in sync, without committing or publishing.
for name in ['report.html','report.md','report.css','Circle_Reserve_Income_Report.docx','Circle_Reserve_Income_Report.pdf']:
    repo=ROOT/'repository/circle'/name
    if repo.parent.exists():shutil.copyfile(SITE/name,repo)
shutil.copytree(SITE/'assets/report',ROOT/'repository/circle/assets/report',dirs_exist_ok=True)
print(json.dumps({'title':title,'word_count_approx':len(markdown.split()),'main_chapters_and_appendices':len(toc),'tables':sum(1 for x in blocks if x.startswith('|')),'same_word_file':True,'production_published':False}))
