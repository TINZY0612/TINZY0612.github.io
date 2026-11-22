import json,re
from pathlib import Path
from lxml import html
ROOT=Path(__file__).resolve().parent;CIRCLE=ROOT.parents[1]
(ROOT/'extracted').mkdir(exist_ok=True)
model=json.loads((CIRCLE/'stage2/results/stage2_data_model.json').read_text())
print('MODEL KEYS',list(model))
for q in model['quarters']:
    print(q['period'],{k:{'value':v['value'],'public':v.get('published_by')} for k,v in q['metrics'].items() if k in ['reserve_income','other_revenue','total_costs','platform_weight','platform_end','usdc_average','rldc']})
for name in ['ipo_prospectus','q2_2025_html','q3_2025_html','fy2025_html','q1_2026_html','q2_2026_html','q3_2026_html']:
    p=CIRCLE/'stage2/raw'/(name+'.html');tree=html.fromstring(p.read_bytes())
    for x in tree.xpath('//script|//style'):x.drop_tree()
    text=' '.join(tree.text_content().split());(ROOT/'extracted'/(name+'.txt')).write_text(text,encoding='utf8')
    hits=[]
    for pat in ['of distribution costs in connection with our agreements with Coinbase','of distribution costs related to Coinbase','issuer retention','USDC on platform, daily weighted']:
        for m in list(re.finditer(re.escape(pat),text,re.I))[-3:]:hits.append(text[max(0,m.start()-220):m.end()+200])
    print('\n'+name+'\n'+'\n'.join(hits))
