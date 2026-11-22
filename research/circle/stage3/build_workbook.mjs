import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';

const root=path.dirname(fileURLToPath(import.meta.url));
const m=JSON.parse(await fs.readFile(path.join(root,'results/stage3_model.json'),'utf8'));
const daily=JSON.parse(await fs.readFile(path.join(root,'results/daily_model_inputs.json'),'utf8'));
const original=JSON.parse(await fs.readFile(path.join(root,'../stage2/results/stage2_data_model.json'),'utf8'));
const out=path.join(root,'../outputs/01a1fcd4-2a0f-7c92-a89f-a871c89c1db7');
await fs.mkdir(out,{recursive:true});await fs.mkdir(path.join(root,'previews'),{recursive:true});
const wb=Workbook.create();
const back=wb.worksheets.add('Backtest'),rl=wb.worksheets.add('RLDC'),inputs=wb.worksheets.add('Source inputs'),db=wb.worksheets.add('Daily build');
const navy='#283B58',ink='#1F2937',blue='#2355A4',green='#197045',gray='#657185';
const num='#,##0.0;(#,##0.0);"-"',pct='0.00%;(0.00%);"-"';
const checks=[];function must(x,s){checks.push({check:s,passed:!!x});if(!x)throw new Error(s);}
function value(s,c,v){s.getRange(c).values=[[v]];}
function formula(s,c,f){s.getRange(c).formulas=[[f]];s.getRange(c).format.font={name:'Arial',size:10,color:f.includes("'Source inputs'")||f.includes("'Backtest'")||f.includes("'Daily build'")?green:ink};}
function header(s,r){s.getRange(r).format={fill:navy,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',verticalAlignment:'center'};}
function band(s,r){s.getRange(r).format.fill='#EDF0F5';s.getRange(r).format.font={name:'Arial',size:10,bold:true,color:navy};}
function title(s,t,r){value(s,'C2',t);s.getRange('C2').format.font={name:'Arial',size:14,bold:true,color:navy};s.getRange(r).format.borders={bottom:{style:'thin',color:navy}};}
function base(s,r){s.showGridLines=false;s.getRange(r).format.font={name:'Arial',size:10,color:ink};s.getRange(r).format.verticalAlignment='center';s.getRange(r).format.rowHeight=23;s.getRange('A1:B150').format.columnWidth=2;}
function date(x){return new Date(x+'T00:00:00Z');}
function near(a,b,tol=1e-7){return typeof a==='number'&&Math.abs(a-b)<=tol;}
function number(s,c){return s.getRange(c).values[0][0];}
const letters=['D','E','F','G','H','I','J'];
const lates=m.evaluations.filter(e=>e.phase==='late');
const earlies=m.evaluations.filter(e=>e.phase==='early');
const obsRows=new Map();

base(inputs,'C1:M180');title(inputs,'Circle financial and model inputs','C3:M3');
inputs.getRange('C1:C180').format.columnWidth=42;inputs.getRange('D1:J24').format.columnWidth=16;
value(inputs,'C4','Preferred supply tolerance');value(inputs,'D4',m.supply_preferred_tolerance);
value(inputs,'F4','Outer tolerance');value(inputs,'G4',m.supply_outer_tolerance);
value(inputs,'I4','Cost case change');value(inputs,'J4',0.05);
value(inputs,'C5','Annual day basis');value(inputs,'D5',365);value(inputs,'F5','SOFR day basis');value(inputs,'G5',360);
value(inputs,'I5','Yield sensitivity');value(inputs,'J5',0.0025);
for(const c of ['D4','G4','J4','J5'])inputs.getRange(c).setNumberFormat(pct);
for(const c of ['D4','G4','J4','D5','G5','J5'])inputs.getRange(c).format.font={name:'Arial',size:10,color:blue};
inputs.getRange('D8:J8').values=[m.quarters.map(q=>'Q'+q.period.slice(5)+':'+q.period.slice(2,4))];value(inputs,'C8','Quarterly source data');header(inputs,'C8:J8');
const labels={9:'Quarter start',10:'Quarter end',11:'Calendar days',12:'Reserve income public by',13:'Reserve income (USD m)',14:'Average supply public by',15:'Reported average USDC (m)',16:'Other revenue public by',17:'Other revenue (USD m)',18:'Total costs public by',19:'Total costs (USD m)',20:'Actual total revenue (USD m)',21:'Actual RLDC (USD m)'};
for(const [r,t] of Object.entries(labels))value(inputs,'C'+r,t);
inputs.getRange('C26:H26').values=[['Metric','Period','ID','Value','Unit','Public by']];header(inputs,'C26:H26');value(inputs,'K26','Source locator');value(inputs,'M26','Public source URL');
inputs.getRange('K1:K180').format.columnWidth=90;inputs.getRange('M1:M180').format.columnWidth=140;
for(const [r,label,url]of [[4,'Daily supply','https://stablecoins.llama.fi/stablecoin/2'],[5,'SOFR','https://markets.newyorkfed.org/api/rates/secured/sofr/search.json'],[6,'Three-month Treasury benchmark','https://fred.stlouisfed.org/series/DGS3MO']]){value(inputs,'K'+r,label);value(inputs,'M'+r,url);}
const obs=original.source_observations;
inputs.getRange(`C27:H${26+obs.length}`).values=obs.map((o,i)=>{obsRows.set(o.id,27+i);return[o.metric.replaceAll('_',' '),o.period,o.id,o.unit==='date'?date(o.value):o.value,o.unit,o.published_by?date(o.published_by):'n.a.'];});
inputs.getRange(`K27:K${26+obs.length}`).values=obs.map(o=>[o.locator]);inputs.getRange(`M27:M${26+obs.length}`).values=obs.map(o=>[o.source_url]);
inputs.getRange(`F27:F${26+obs.length}`).setNumberFormat('#,##0.000;(#,##0.000);"-"');inputs.getRange(`F27:F${26+obs.length}`).format.font={name:'Arial',size:10,color:blue};inputs.getRange(`H27:H${26+obs.length}`).setNumberFormat('dd-mmm-yy');
for(const o of obs){if(o.unit==='date')inputs.getRange('F'+obsRows.get(o.id)).setNumberFormat('dd-mmm-yy');else if(o.unit==='decimal')inputs.getRange('F'+obsRows.get(o.id)).setNumberFormat(pct);}
function guarded(id){const r='F'+obsRows.get(id);return `IF(ISNUMBER(${r}),${r},NA())`;}
function metricFormula(q,k){const z=q.metrics[k],ids=z.input_ids;return '='+guarded(ids[0])+(ids.length===2?'-'+guarded(ids[1]):'');}
const financialRows={reserve_income:13,usdc_average:15,other_revenue:17,total_costs:19,total_revenue:20};
m.quarters.forEach((q,i)=>{
 const c=letters[i];value(inputs,c+'9',date(q.start));value(inputs,c+'10',date(q.end));formula(inputs,c+'11',`=${c}10-${c}9+1`);
 for(const [k,r] of Object.entries(financialRows))formula(inputs,c+r,metricFormula(q,k));
 for(const [k,r] of Object.entries({reserve_income:12,usdc_average:14,other_revenue:16,total_costs:18}))value(inputs,c+r,date(q.metrics[k].published_by));
 formula(inputs,c+'21',`=${c}20-${c}19`);
 for(const r of [9,10,12,14,16,18])inputs.getRange(c+r).setNumberFormat('dd-mmm-yy');
 for(const r of [13,15,17,19,20,21])inputs.getRange(c+r).setNumberFormat(num);
});
value(inputs,'C23','Source values retain original dates. Q4 flows equal annual less nine months.');inputs.getRange('C23').format.font={name:'Arial',size:10,italic:true,color:gray};
inputs.freezePanes.freezeRows(8);inputs.tabColor='#F4EBDD';

const dn=daily.length+8;const end=dn;
base(db,`C1:V${dn}`);title(db,'Daily supply and eligible yield inputs','C3:T3');
value(db,'C4','Balances in USD millions. Fund yields are rolling seven-day rates, not realized daily income.');
db.getRange('C1:C'+dn).format.columnWidth=21;db.getRange('D1:D'+dn).format.columnWidth=12;db.getRange('E1:G'+dn).format.columnWidth=16;db.getRange('H1:J'+dn).format.columnWidth=13;db.getRange('K1:M'+dn).format.columnWidth=16;db.getRange('N1:N'+dn).format.columnWidth=26;db.getRange('O1:S'+dn).format.columnWidth=17;db.getRange('T1:T'+dn).format.columnWidth=12;db.getRange('U1:U'+dn).format.columnWidth=3;db.getRange('V1:V'+dn).format.columnWidth=140;
db.getRange('C7:T7').values=[['Evaluation','Role','Economic date','Supply (m)','Next bucket (m)','SOFR','3m Treasury','Fund net yield','Fund yield date','Fund filed','Cutoff','Fund accession','SOFR income','Treasury income','Fund proxy income','Next SOFR income','Next fund income','Yield age days']];header(db,'C7:T7');db.getRange('C7:T7').format.wrapText=true;db.getRange('C7:T7').format.rowHeight=38;
db.getRange(`C8:N${daily.length+7}`).values=daily.map(r=>[r.evaluation,r.role,date(r.date),r.supply_million,r.next_supply_million,r.sofr,r.treasury_3m,r.fund_net_yield,date(r.fund_observation_date),date(r.fund_filed),date(r.cutoff),r.fund_accession]);
db.getRange(`V8:V${daily.length+7}`).values=daily.map(r=>[r.fund_url]);
db.getRange(`E8:E${daily.length+7}`).setNumberFormat('dd-mmm-yy');db.getRange(`K8:M${daily.length+7}`).setNumberFormat('dd-mmm-yy');db.getRange(`F8:G${daily.length+7}`).setNumberFormat(num);db.getRange(`H8:J${daily.length+7}`).setNumberFormat(pct);db.getRange(`O8:S${daily.length+7}`).setNumberFormat('#,##0.000;(#,##0.000);"-"');db.getRange(`F8:J${daily.length+7}`).format.font={name:'Arial',size:10,color:blue};
const dataEnd=daily.length+7;
db.getRange(`O8:T${dataEnd}`).formulas=daily.map((r,i)=>{const n=i+8;return[`=IF(AND(ISNUMBER(F${n}),ISNUMBER(H${n})),F${n}*H${n}/'Source inputs'!$G$5,NA())`,`=IF(AND(ISNUMBER(F${n}),ISNUMBER(I${n})),F${n}*I${n}/'Source inputs'!$D$5,NA())`,`=IF(AND(ISNUMBER(F${n}),ISNUMBER(J${n})),F${n}*J${n}/'Source inputs'!$D$5,NA())`,`=IF(AND(ISNUMBER(G${n}),ISNUMBER(H${n})),G${n}*H${n}/'Source inputs'!$G$5,NA())`,`=IF(AND(ISNUMBER(G${n}),ISNUMBER(J${n})),G${n}*J${n}/'Source inputs'!$D$5,NA())`,`=E${n}-K${n}`];});
db.getRange(`O8:S${dataEnd}`).format.font={name:'Arial',size:10,color:green};db.freezePanes.freezeRows(7);db.freezePanes.freezeColumns(5);
function sum(col,id,role){return `SUMIFS('Daily build'!$${col}$8:$${col}$${dataEnd},'Daily build'!$C$8:$C$${dataEnd},${id},'Daily build'!$D$8:$D$${dataEnd},"${role}")`;}

base(back,'C1:O100');title(back,'Circle reserve income backtest','C3:O3');back.tabColor=navy;
back.getRange('C1:C100').format.columnWidth=43;back.getRange('D1:I100').format.columnWidth=16;back.getRange('J1:J100').format.columnWidth=3;back.getRange('K1:K100').format.columnWidth=31;back.getRange('L1:O100').format.columnWidth=15;
value(back,'C5','Six historical quarters. Current supply history. Financial and fund inputs filtered by publication date.');back.getRange('C5').format.font={name:'Arial',size:10,italic:true,color:gray};
value(back,'C7','Reserve income (USD millions)');back.getRange('D7:I7').values=[lates.map(e=>e.period)];header(back,'C7:I7');
const outputLabels={8:'Late estimate cutoff',9:'Reported reserve income',11:'Carry prior income, adjust days',12:'Error versus reported',14:'Supply times lagged earned yield',15:'Error versus reported',17:'Supply times SOFR',18:'Error versus reported',20:'Supply times 3m Treasury',21:'Error versus reported',23:'SOFR with lagged yield spread',24:'Error versus reported',26:'Fund yield with lagged spread',27:'Error versus reported',30:'Fund estimate seven days after quarter',31:'Error versus reported',32:'Early estimate cutoff',34:'SOFR model, following-date buckets',35:'Error versus reported',37:'Provider average supply (USDC m)',38:'Reported average supply (USDC m)',39:'Average supply difference',41:'Supply tolerance result',44:'Working model uses SOFR with lagged spread.',45:'Fund model is a challenger. Neither uses current-quarter reported yield.'};
for(const [r,t] of Object.entries(outputLabels))value(back,'C'+r,t);
for(const r of [9,23,26,30,34,37])band(back,`C${r}:I${r}`);
value(back,'C48','Yield spread means the prior gap between Circle\'s earned yield and the benchmark.');
value(back,'C49','Following-date sensitivity recalculates both prior and current benchmark weights.');
value(back,'C50','Source inputs show actuals for scoring. Forecast formulas use only the prior quarter.');
value(back,'C53','Model calculation');band(back,'C53:I53');back.getRange('D54:I54').values=[lates.map(e=>e.period)];header(back,'C54:I54');
const calcLabels={61:'Evaluation ID',62:'Late cutoff',63:'Current calendar days',64:'Prior calendar days',65:'Prior reserve income',66:'Prior reported average supply',67:'Prior implied earned yield',68:'Current supply sum (m days)',69:'Prior supply sum (m days)',70:'Current SOFR income proxy',71:'Prior SOFR income proxy',72:'Prior weighted SOFR, 365 basis',73:'Lagged SOFR yield spread',74:'Current Treasury income proxy',75:'Current fund income proxy',76:'Prior fund income proxy',77:'Prior weighted fund yield',78:'Lagged fund yield spread',79:'SOFR model reserve income',80:'Fund model reserve income',81:'Following-date current supply sum',82:'Following-date prior supply sum',83:'Following-date current SOFR income',84:'Following-date prior SOFR income',85:'Following-date SOFR yield spread',86:'Following-date SOFR model income',90:'Early evaluation ID',91:'Early current fund income proxy',92:'Early prior fund income proxy',93:'Early prior supply sum',94:'Early lagged fund spread',95:'Early current supply sum',96:'Early fund model income'};
for(const [r,t] of Object.entries(calcLabels))value(back,'C'+r,t);
lates.forEach((e,i)=>{
 const c=letters[i],cur=letters[i+1],prev=letters[i];value(back,c+'61',e.id);value(back,c+'62',date(e.cutoff));
 for(const [r,sr,ic] of [[63,11,cur],[64,11,prev],[65,13,prev],[66,15,prev]])formula(back,c+r,`='Source inputs'!${ic}${sr}`);
 formula(back,c+'67',`=${c}65/${c}66*'Source inputs'!$D$5/${c}64`);
 for(const [r,col,role] of [[68,'F','current'],[69,'F','lag'],[70,'O','current'],[71,'O','lag'],[74,'P','current'],[75,'Q','current'],[76,'Q','lag'],[81,'G','current'],[82,'G','lag'],[83,'R','current'],[84,'R','lag']])formula(back,c+r,'='+sum(col,c+'61',role));
 formula(back,c+'72',`=${c}71*'Source inputs'!$D$5/${c}69`);formula(back,c+'73',`=${c}67-${c}72`);
 formula(back,c+'77',`=${c}76*'Source inputs'!$D$5/${c}69`);formula(back,c+'78',`=${c}67-${c}77`);
 formula(back,c+'79',`=${c}70+${c}68*${c}73/'Source inputs'!$D$5`);formula(back,c+'80',`=${c}75+${c}68*${c}78/'Source inputs'!$D$5`);
 formula(back,c+'85',`=${c}67-${c}84*'Source inputs'!$D$5/${c}82`);formula(back,c+'86',`=${c}83+${c}81*${c}85/'Source inputs'!$D$5`);
 value(back,c+'90',earlies[i].id);
 for(const [r,col,role] of [[91,'Q','current'],[92,'Q','lag'],[93,'F','lag'],[95,'F','current']])formula(back,c+r,'='+sum(col,c+'90',role));
 formula(back,c+'94',`=${c}67-${c}92*'Source inputs'!$D$5/${c}93`);formula(back,c+'96',`=${c}91+${c}95*${c}94/'Source inputs'!$D$5`);
 formula(back,c+'8',`=${c}62`);formula(back,c+'9',`='Source inputs'!${cur}13`);formula(back,c+'11',`=${c}65*${c}63/${c}64`);formula(back,c+'14',`=${c}68*${c}67/'Source inputs'!$D$5`);
 for(const [r,cr] of [[17,70],[20,74],[23,79],[26,80],[30,96],[34,86]])formula(back,c+r,`=${c}${cr}`);
 for(const [r,est] of [[12,11],[15,14],[18,17],[21,20],[24,23],[27,26],[31,30],[35,34]])formula(back,c+r,`=${c}${est}/${c}9-1`);
 value(back,c+'32',date(earlies[i].cutoff));formula(back,c+'37',`=${c}68/${c}63`);formula(back,c+'38',`='Source inputs'!${cur}15`);formula(back,c+'39',`=${c}37/${c}38-1`);
 formula(back,c+'41',`=IF(ABS(${c}39)<='Source inputs'!$D$4,"Preferred",IF(ABS(${c}39)<='Source inputs'!$G$4,"Outer only","Outside"))`);
});
back.getRange('D8:I96').setNumberFormat(num);
for(const r of [8,32,62])back.getRange(`D${r}:I${r}`).setNumberFormat('dd-mmm-yy');
for(const r of [12,15,18,21,24,27,31,35,39,67,72,73,77,78,85,94]){back.getRange(`D${r}:I${r}`).setNumberFormat(pct);back.getRange(`C${r}:I${r}`).format.font.italic=true;}
back.getRange('D39:I39').setNumberFormat('0.000%;(0.000%);"-"');
for(const r of [63,64])back.getRange(`D${r}:I${r}`).setNumberFormat('0');
back.getRange('D8:I41').format.font.color=ink;
back.getRange('K7:O7').values=[['Method','Mean abs. error','Worst abs. error','Mean abs. ($m)','Wins vs carry']];header(back,'K7:O7');back.getRange('K7:O7').format.wrapText=true;back.getRange('K7:O7').format.rowHeight=36;
const methods=[['Carry prior income','carry_forward',11,12],['Lagged earned yield','lagged_implied_yield',14,15],['SOFR','sofr',17,18],['3m Treasury','treasury_3m',20,21],['SOFR with lagged spread','sofr_lagged_spread',23,24],['Fund with lagged spread','fund_lagged_spread',26,27]];
methods.forEach(([label,key,er,rr],i)=>{const r=i+8;value(back,'K'+r,label);formula(back,'L'+r,'=SUM('+letters.slice(0,6).map(c=>`ABS(${c}${rr})`).join(',')+')/6');formula(back,'M'+r,'=MAX('+letters.slice(0,6).map(c=>`ABS(${c}${rr})`).join(',')+')');formula(back,'N'+r,'=SUM('+letters.slice(0,6).map(c=>`ABS(${c}${er}-${c}9)`).join(',')+')/6');formula(back,'O'+r,'=SUM('+letters.slice(0,6).map(c=>`IF(ABS(${c}${rr})<ABS(${c}12),1,0)`).join(',')+')');});
back.getRange('L8:M13').setNumberFormat(pct);back.getRange('N8:N13').setNumberFormat(num);back.getRange('O8:O13').setNumberFormat('0');
value(back,'K16','Mean absolute error ignores the sign.');value(back,'K17','Six observations per method.');value(back,'K18','A small supply gap does not prove exact definitions.');
back.getRange('D41:I41').conditionalFormats.add('containsText',{text:'Outside',format:{fill:'#FCE4E4',font:{bold:true,color:'#9C2626'}}});back.freezePanes.freezeRows(7);back.freezePanes.freezeColumns(3);

base(rl,'C1:L40');title(rl,'Circle revenue and retained revenue','C3:I3');rl.tabColor='#627B9C';rl.getRange('C1:C40').format.columnWidth=44;rl.getRange('D1:I40').format.columnWidth=16;
value(rl,'C4','Cost case selected');value(rl,'D4',1);rl.getRange('D4').format.font.color=blue;rl.getRange('D4').dataValidation={rule:{type:'whole',operator:'between',formula1:1,formula2:3}};formula(rl,'F4','=CHOOSE(D4,"Base","Higher costs","Lower costs")');rl.getRange('F4').format.font.color=green;rl.getRange('F4').format.horizontalAlignment='center';rl.getRange('F4').format.borders={preset:'outside',style:'dashed',color:'#A7B3C3'};
value(rl,'C5','1 Base. 2 Higher costs. 3 Lower costs. Set the case increment in Source inputs.');
rl.getRange('D7:I7').values=[lates.map(e=>e.period)];value(rl,'C7','USD millions unless stated');header(rl,'C7:I7');
const rlLabels={9:'Reserve income estimate',10:'Other revenue, prior quarter',11:'Total revenue estimate',13:'Active cost ratio',15:'Base cost ratio, prior quarter',16:'Higher cost ratio',17:'Lower cost ratio',19:'Estimated distribution and related costs',20:'Revenue less distribution costs',22:'Reported total revenue',23:'Total revenue error',25:'Reported RLDC',26:'RLDC error',28:'RLDC effect of 1pp higher cost ratio',29:'Income effect, preferred supply tolerance',30:'Income effect, outer supply tolerance',31:'Income effect, yield sensitivity'};
for(const [r,t]of Object.entries(rlLabels))value(rl,'C'+r,t);
lates.forEach((e,i)=>{const c=letters[i],prev=letters[i],cur=letters[i+1];formula(rl,c+'9',`='Backtest'!${c}23`);formula(rl,c+'10',`='Source inputs'!${prev}17`);formula(rl,c+'11',`=SUM(${c}9:${c}10)`);formula(rl,c+'15',`='Source inputs'!${prev}19/'Source inputs'!${prev}13`);formula(rl,c+'16',`=IF(ISNUMBER('Source inputs'!$J$4),${c}15+'Source inputs'!$J$4,NA())`);formula(rl,c+'17',`=IF(ISNUMBER('Source inputs'!$J$4),${c}15-'Source inputs'!$J$4,NA())`);formula(rl,c+'13',`=CHOOSE($D$4,${c}15,${c}16,${c}17)`);formula(rl,c+'19',`=${c}9*${c}13`);formula(rl,c+'20',`=${c}11-${c}19`);formula(rl,c+'22',`='Source inputs'!${cur}20`);formula(rl,c+'23',`=${c}11/${c}22-1`);formula(rl,c+'25',`='Source inputs'!${cur}21`);formula(rl,c+'26',`=${c}20/${c}25-1`);formula(rl,c+'28',`=-${c}9*1%`);formula(rl,c+'29',`=${c}9*'Source inputs'!$D$4`);formula(rl,c+'30',`=${c}9*'Source inputs'!$G$4`);formula(rl,c+'31',`='Backtest'!${c}68*'Source inputs'!$J$5/'Source inputs'!$D$5`);});
rl.getRange('D9:I31').setNumberFormat(num);for(const r of [13,15,16,17,23,26]){rl.getRange(`D${r}:I${r}`).setNumberFormat(pct);rl.getRange(`C${r}:I${r}`).format.font.italic=true;}
for(const r of [11,13,20,25])band(rl,`C${r}:I${r}`);
value(rl,'C34','RLDC is before operating expenses. The cost cases are illustrative, not probability intervals.');
value(rl,'C35','Other revenue uses the prior quarter. Q3 2026 ARC recognition is not added to the estimate.');
value(rl,'C36','Quarterly actuals do not change when the cost selector changes.');

wb.recalculate();
lates.forEach((e,i)=>{const c=letters[i];must(near(number(back,c+'23'),e.estimates.sofr_lagged_spread),e.id+' primary matches Python');must(near(number(back,c+'26'),e.estimates.fund_lagged_spread),e.id+' fund matches Python');must(near(number(back,c+'30'),earlies[i].estimates.fund_lagged_spread),e.id+' early fund matches Python');must(near(number(back,c+'34'),e.next_bucket_estimates_recalibrated_spreads.sofr_lagged_spread),e.id+' alignment matches Python');must(near(number(rl,c+'20'),e.rldc.rldc_estimate),e.id+' RLDC matches Python');});
methods.forEach(([,key],i)=>must(near(number(back,'L'+(i+8)),m.metrics.late[key].mape,1e-10),key+' MAPE matches Python'));
const baseRL=number(rl,'I20'),baseRI=number(back,'I23'),actual=number(rl,'I25');
value(rl,'D4',2);wb.recalculate();must(near(number(rl,'I20'),baseRL-baseRI*0.05),'higher cost case recalculates');must(number(rl,'I25')===actual,'actuals unchanged by case');value(rl,'D4',3);wb.recalculate();must(near(number(rl,'I20'),baseRL+baseRI*0.05),'lower cost case recalculates');value(rl,'D4',1);
value(inputs,'J4',null);wb.recalculate();must(near(number(rl,'I20'),baseRL),'blank unselected case increment does not block base');value(rl,'D4',2);wb.recalculate();must(typeof number(rl,'I20')!=='number','missing selected case increment exposed');value(inputs,'J4',0.05);value(rl,'D4',1);
const prevOther=m.quarters[5].metrics.other_revenue.input_ids[0],otherCell='F'+obsRows.get(prevOther),otherOriginal=number(inputs,otherCell);
value(inputs,otherCell,0);wb.recalculate();must(near(number(rl,'I11'),baseRI),'valid zero other revenue preserved');value(inputs,otherCell,otherOriginal);
const lagReserve=m.quarters[5].metrics.reserve_income.input_ids[0],lagCell='F'+obsRows.get(lagReserve),lagOriginal=number(inputs,lagCell);
value(inputs,lagCell,null);wb.recalculate();must(typeof number(back,'I23')!=='number','missing lag reserve income exposed');value(inputs,lagCell,lagOriginal);
const currentReserve=m.quarters[6].metrics.reserve_income.input_ids[0],curCell='F'+obsRows.get(currentReserve),curOriginal=number(inputs,curCell);
value(inputs,curCell,curOriginal+100);wb.recalculate();must(near(number(back,'I23'),baseRI),'current target shock leaves prediction unchanged');value(inputs,curCell,curOriginal);
const sourceDailyIndex=daily.findIndex(r=>r.evaluation==='2026Q3_late'&&r.role==='current')+8,sourceDailyCell='F'+sourceDailyIndex,sourceDailyValue=number(db,sourceDailyCell);
value(db,sourceDailyCell,null);wb.recalculate();must(typeof number(back,'I23')!=='number','missing daily balance exposed');value(db,sourceDailyCell,sourceDailyValue);
value(inputs,'D4',0.004);wb.recalculate();must(number(back,'E41')==='Outer only','supply tolerance boundary recalculates');value(inputs,'D4',0.005);
wb.recalculate();must(near(number(rl,'I20'),baseRL),'all temporary edits restored');
const scan=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:50},summary:'final formula error scan'});
await fs.writeFile(path.join(root,'results/workbook_formula_scan.txt'),scan.ndjson);
const inspect=await wb.inspect({kind:'table',range:'Backtest!C7:O41',include:'values,formulas',tableMaxRows:35,tableMaxCols:13,maxChars:10000});await fs.writeFile(path.join(root,'results/workbook_inspection.txt'),inspect.ndjson);
const views=[['Backtest','C2:O42','backtest'],['RLDC','C2:I36','rldc'],['Source inputs','C8:J23','financial_inputs'],['Source inputs','C26:H36','source_observations'],['Daily build','C2:T19','daily_build']];
for(const [sheet,range,name] of views){const blob=await wb.render({sheetName:sheet,range,scale:1.4,format:'png'});await fs.writeFile(path.join(root,'previews',name+'.png'),new Uint8Array(await blob.arrayBuffer()));}
const xlsx=await SpreadsheetFile.exportXlsx(wb);const target=path.join(out,'Circle_Reserve_Income_Backtest.xlsx');await xlsx.save(target);
await fs.writeFile(path.join(root,'results/workbook_validation.json'),JSON.stringify({checks_passed:checks.filter(x=>x.passed).length,checks_total:checks.length,checks,output:target},null,2));
console.log(JSON.stringify({output:target,checks:checks.length,daily_rows:daily.length,scan:scan.ndjson}));
process.exitCode=0;
