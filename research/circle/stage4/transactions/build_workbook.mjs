import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const root=path.dirname(fileURLToPath(import.meta.url));
const m=JSON.parse(await fs.readFile(path.join(root,'results/transaction_backtest.json'),'utf8'));
const ledger=JSON.parse(await fs.readFile(path.join(root,'../results/other_revenue_model.json'),'utf8')).ledger;
const feeData=JSON.parse(await fs.readFile(path.join(root,'../raw/llama_cctp_fee_history.json'),'utf8')).totalDataChart;
const out=path.resolve(root,'../../outputs/01a1fcd4-2a0f-7c92-a89f-a871c89c1db7');
await fs.mkdir(out,{recursive:true});await fs.mkdir(path.join(root,'previews'),{recursive:true});
const wb=Workbook.create();const back=wb.worksheets.add('Transaction backtest'),inputs=wb.worksheets.add('Quarter inputs'),daily=wb.worksheets.add('Daily CCTP');
const ink='#263238',navy='#253B59',blue='#2155A3',green='#197045',muted='#596675';
const number='#,##0.000;(#,##0.000);"-"',pct='0.00%;(0.00%);"-"';
function v(s,a,x){s.getRange(a).values=[[x]];}
function f(s,a,x){s.getRange(a).formulas=[[x]];s.getRange(a).format.font.color=x.includes("'Quarter inputs'")||x.includes("'Daily CCTP'")?green:ink;}
function h(s,a){s.getRange(a).format={fill:navy,font:{name:'Arial',size:10,color:'#FFFFFF',bold:true},horizontalAlignment:'center',verticalAlignment:'center'};}
function base(s,a){s.showGridLines=false;s.getRange(a).format={font:{name:'Arial',size:10,color:ink},verticalAlignment:'center',rowHeight:22};}
function title(s,t,r){v(s,'C2',t);s.getRange('C2').format.font={name:'Arial',size:14,bold:true,color:navy};s.getRange(r).format.borders={bottom:{style:'thin',color:navy}};}
function date(x){return new Date(x+'T00:00:00Z');}
function near(a,b){return typeof a==='number'&&Math.abs(a-b)<1e-8;}
const qa=[];function must(x,name){qa.push({name,passed:!!x});if(!x)throw Error(name);}

base(daily,'C1:G590');title(daily,'Observed CCTP fees','C3:F3');
daily.getRange('C:C').format.columnWidth=17;daily.getRange('D:D').format.columnWidth=23;daily.getRange('F:F').format.columnWidth=100;
v(daily,'C5','UTC date');v(daily,'D5','Fees (USD millions)');h(daily,'C5:D5');
v(daily,'F5',m.cctp_source_url);v(daily,'F6','Current reconstructed history; historical publication availability unverified.');
const series=feeData.filter(([t])=>new Date(t*1000).toISOString().slice(0,10)<='2026-11-21');
daily.getRange(`C6:D${5+series.length}`).values=series.map(([t,x])=>[new Date(t*1000),x/1e6]);
daily.getRange(`C6:C${5+series.length}`).setNumberFormat('dd-mmm-yy');daily.getRange(`D6:D${5+series.length}`).setNumberFormat('#,##0.000000');daily.getRange(`D6:D${5+series.length}`).format.font.color=blue;
daily.freezePanes.freezeRows(5);

base(inputs,'C1:R25');title(inputs,'Circle quarterly source inputs','C3:L3');inputs.getRange('C:C').format.columnWidth=14;inputs.getRange('D:E').format.columnWidth=15;inputs.getRange('F:F').format.columnWidth=11;inputs.getRange('G:G').format.columnWidth=16;inputs.getRange('H:I').format.columnWidth=19;inputs.getRange('J:K').format.columnWidth=15;inputs.getRange('L:L').format.columnWidth=21;inputs.getRange('N:N').format.columnWidth=110;
inputs.getRange('C7:L7').values=[['Quarter','Start','End','Days','Public by','Transaction ($m)','CCTP fees ($m)','Days observed','Complete','Services ($m)']];h(inputs,'C7:L7');inputs.getRange('H7:I7').format.wrapText=true;inputs.getRange('C7:L7').format.rowHeight=32;
const rows=new Map();
for(let i=0;i<m.quarters.length;i++){
 const q=m.quarters[i],r=8+i;rows.set(q.period,r);
 const s=ledger.find(x=>x.period===q.period&&x.classification==='current'&&x.published_by===q.published_by);
 inputs.getRange(`C${r}:H${r}`).values=[[q.period,date(q.start),date(q.end),q.days,q.published_by?date(q.published_by):'n.a.',q.transaction_actual??'n.a.']];
 f(inputs,'I'+r,`=IF(J${r}=0,"n.a.",SUMIFS('Daily CCTP'!$D$6:$D$${5+series.length},'Daily CCTP'!$C$6:$C$${5+series.length},">="&D${r},'Daily CCTP'!$C$6:$C$${5+series.length},"<="&E${r}))`);
 f(inputs,'J'+r,`=COUNTIFS('Daily CCTP'!$C$6:$C$${5+series.length},">="&D${r},'Daily CCTP'!$C$6:$C$${5+series.length},"<="&E${r})`);
 f(inputs,'K'+r,`=J${r}=F${r}`);v(inputs,'L'+r,s?s.metrics.subscription_services.value:'n.a.');v(inputs,'N'+r,q.source_url??'n.a.');
}
inputs.getRange('D8:E14').setNumberFormat('dd-mmm-yy');inputs.getRange('G8:G14').setNumberFormat('dd-mmm-yy');inputs.getRange('H8:I14').setNumberFormat(number);inputs.getRange('L8:L14').setNumberFormat(number);inputs.getRange('H8:H14').format.font.color=blue;inputs.getRange('L8:L14').format.font.color=blue;
inputs.getRange('D8:L14').format.horizontalAlignment='right';
v(inputs,'C17','Q1 2025 uses the August 2025 comparable split; not an eligible early Q2 forecast input.');
v(inputs,'C18','Q2 2025 CCTP has 19 missing dates; no zeros are imputed.');v(inputs,'C19','Q4 2025 financial categories are annual less original nine months.');
v(inputs,'C21','CCTP mapping to GAAP transaction revenue is assumed; the residual is not independently identified.');

base(back,'C1:O88');title(back,'Circle transaction revenue backtest','C3:O3');back.tabColor=navy;
back.getRange('C:C').format.columnWidth=44;back.getRange('D:H').format.columnWidth=15;back.getRange('I:J').format.columnWidth=3;back.getRange('K:K').format.columnWidth=35;back.getRange('L:O').format.columnWidth=14;
v(back,'C5','USD millions. Common late sample: Q4 2025 through Q3 2026.');
v(back,'C6','Completed-quarter CCTP observations plus a lagged residual; current histories, not archived vintages.');
v(back,'C8','Late estimate');back.getRange('D8:H8').values=[m.late.map(x=>'Q'+x.period.slice(-1)+':'+x.period.slice(2,4))];h(back,'C8:H8');
const labels={9:'Actual transaction revenue',10:'Observed CCTP fees',11:'CCTP / actual transaction revenue',13:'Prior-quarter flat estimate',14:'Signed error',15:'Absolute percentage error',17:'CCTP + flat residual estimate',18:'Signed error',19:'Absolute percentage error',21:'CCTP + day-scaled residual',22:'Signed error',23:'Absolute percentage error',25:'Day-scaled prior-quarter estimate',26:'Signed error',27:'Absolute percentage error',29:'Repeat previous growth estimate',30:'Signed error',31:'Absolute percentage error',33:'Prior-quarter transaction revenue',34:'Prior-quarter CCTP observed fees',35:'Prior-quarter residual',36:'Day-before-earnings cutoff',37:'Prior financial result public by',38:'Current quarter days',39:'Prior quarter days',41:'Flat absolute USD error',42:'CCTP + flat absolute USD error',43:'CCTP + scaled absolute USD error',44:'Scaled baseline absolute USD error'};
for(const[r,t]of Object.entries(labels))v(back,'C'+r,t);
for(let i=0;i<m.late.length;i++){
 const e=m.late[i],col='DEFGH'[i],r=rows.get(e.period),p=r-1;
 f(back,col+'9',`='Quarter inputs'!H${r}`);f(back,col+'10',`='Quarter inputs'!I${r}`);f(back,col+'11',`=${col}10/${col}9`);
 f(back,col+'33',`='Quarter inputs'!H${p}`);f(back,col+'34',`='Quarter inputs'!I${p}`);
 f(back,col+'35',`=IF('Quarter inputs'!K${p},${col}33-${col}34,"n.a.")`);
 f(back,col+'13',`=${col}33`);
 for(const[er,pr]of [[14,13],[18,17],[22,21],[26,25],[30,29]])f(back,col+er,`=IF(ISNUMBER(${col}${pr}),${col}${pr}/${col}9-1,"n.a.")`);
 for(const[ar,er]of [[15,14],[19,18],[23,22],[27,26],[31,30]])f(back,col+ar,`=IF(ISNUMBER(${col}${er}),ABS(${col}${er}),"n.a.")`);
 f(back,col+'17',`=IF(AND('Quarter inputs'!K${r},ISNUMBER(${col}35)),${col}10+${col}35,"n.a.")`);
 f(back,col+'21',`=IF(AND('Quarter inputs'!K${r},ISNUMBER(${col}35)),${col}10+${col}35*${col}38/${col}39,"n.a.")`);
 f(back,col+'25',`=${col}33*${col}38/${col}39`);
 f(back,col+'29',`=${col}33*${col}33/'Quarter inputs'!H${p-1}`);
 v(back,col+'36',date(e.cutoff));v(back,col+'37',date(e.lag_public_by));f(back,col+'38',`='Quarter inputs'!F${r}`);f(back,col+'39',`='Quarter inputs'!F${p}`);
 for(const[ar,pr]of [[41,13],[42,17],[43,21],[44,25]])f(back,col+ar,`=IF(ISNUMBER(${col}${pr}),ABS(${col}${pr}-${col}9),"n.a.")`);
}
back.getRange('D9:H44').setNumberFormat(number);back.getRange('D36:H37').setNumberFormat('dd-mmm-yy');back.getRange('D38:H39').setNumberFormat('0');
for(const r of [11,14,15,18,19,22,23,26,27,30,31]){back.getRange(`D${r}:H${r}`).setNumberFormat(pct);back.getRange(`C${r}:H${r}`).format.font.italic=true;}
back.getRange('K8:O8').values=[['Common four-quarter score','N','MAPE','MAE ($m)','Worst APE']];h(back,'K8:O8');back.getRange('K8:O8').format.wrapText=true;back.getRange('K8:O8').format.rowHeight=32;
const scoreMethods=[['Flat baseline',15,41,'prior_quarter_flat'],['Day-scaled baseline',27,44,'prior_quarter_day_scaled'],['CCTP + flat residual',19,42,'observed_cctp_plus_flat_residual'],['CCTP + scaled residual',23,43,'observed_cctp_plus_day_scaled_residual']];
scoreMethods.forEach(([name,ap,ab,key],i)=>{const r=9+i;v(back,'K'+r,name);f(back,'L'+r,`=COUNT(E${ap}:H${ap})`);f(back,'M'+r,`=AVERAGE(E${ap}:H${ap})`);f(back,'N'+r,`=AVERAGE(E${ab}:H${ab})`);f(back,'O'+r,`=MAX(E${ap}:H${ap})`);});
back.getRange('M9:M12').setNumberFormat(pct);back.getRange('O9:O12').setNumberFormat(pct);back.getRange('N9:N12').setNumberFormat(number);
v(back,'K15','Q3 2025 hybrid unavailable:');v(back,'K16','prior CCTP quarter is incomplete.');v(back,'K18','Q4 2025 spike stays in the sample.');v(back,'K20','USYC performance fees are services,');v(back,'K21','so they are excluded from this model.');

v(back,'C47','First 30 calendar days');h(back,'C47:H47');
back.getRange('D47:H47').formulas=[['=D8','=E8','=F8','=G8','=H8']];
const earlyLabels={48:'Actual transaction revenue',49:'Latest public flat estimate',50:'Flat signed error',51:'Flat absolute percentage error',53:'First-30-day CCTP estimate',54:'CCTP model signed error',55:'CCTP model absolute percentage error',57:'Latest public day-scaled estimate',58:'Scaled signed error',59:'Scaled absolute percentage error',61:'Latest public calibration quarter',62:'First-30-day cutoff',63:'Calibration financials public by',64:'Calibration transaction revenue',65:'Calibration CCTP fees',66:'Projected quarter CCTP fees',67:'Projected non-CCTP residual',68:'Calibration quarter days',69:'Current quarter days'};
for(const[r,t]of Object.entries(earlyLabels))v(back,'C'+r,t);
for(let i=0;i<m.early.length;i++){
 const e=m.early[i],col='DEFGH'[i],r=rows.get(e.period);f(back,col+'48',`='Quarter inputs'!H${r}`);v(back,col+'62',date(e.cutoff));v(back,col+'69',e.current_days??m.quarters.find(x=>x.period===e.period).days);
 if(e.base_period){const br=rows.get(e.base_period);v(back,col+'61',e.base_period);v(back,col+'63',date(e.base_public_by));f(back,col+'64',`='Quarter inputs'!H${br}`);f(back,col+'65',`='Quarter inputs'!I${br}`);f(back,col+'68',`='Quarter inputs'!F${br}`);f(back,col+'49',`=${col}64`);f(back,col+'57',`=${col}64*${col}69/${col}68`);
  if(e.projected_cctp!==undefined){f(back,col+'66',`=SUMIFS('Daily CCTP'!$D$6:$D$${5+series.length},'Daily CCTP'!$C$6:$C$${5+series.length},">="&'Quarter inputs'!D${r},'Daily CCTP'!$C$6:$C$${5+series.length},"<="&${col}62)*${col}69/30`);f(back,col+'67',`=(${col}64-${col}65)*${col}69/${col}68`);f(back,col+'53',`=SUM(${col}66:${col}67)`);}else{v(back,col+'53','n.a.');v(back,col+'66','n.a.');v(back,col+'67','n.a.');}
 }else{for(const rr of [49,53,57,61,63,64,65,66,67,68])v(back,col+rr,'n.a.');}
 for(const[er,pr]of [[50,49],[54,53],[58,57]])f(back,col+er,`=IF(ISNUMBER(${col}${pr}),${col}${pr}/${col}48-1,"n.a.")`);
 for(const[ap,er]of [[51,50],[55,54],[59,58]])f(back,col+ap,`=IF(ISNUMBER(${col}${er}),ABS(${col}${er}),"n.a.")`);
}
back.getRange('D48:H69').setNumberFormat(number);back.getRange('D62:H63').setNumberFormat('dd-mmm-yy');back.getRange('D68:H69').setNumberFormat('0');
for(const r of [50,51,54,55,58,59])back.getRange(`D${r}:H${r}`).setNumberFormat(pct);
back.getRange('K48:M48').values=[['Common three-quarter score','N','MAPE']];h(back,'K48:M48');
[['Latest public flat',51],['Latest public day-scaled',59],['First 30 days + residual',55]].forEach(([n,a],i)=>{const r=49+i;v(back,'K'+r,n);f(back,'L'+r,`=COUNT(F${a}:H${a})`);f(back,'M'+r,`=AVERAGE(F${a}:H${a})`);});back.getRange('M49:M51').setNumberFormat(pct);
v(back,'K54','Early estimates use only financials');v(back,'K55','published by the stated cutoff.');v(back,'K57','The most recent quarter is often');v(back,'K58','still unpublished after 30 days.');
v(back,'C73','Subscription factor assessment');h(back,'C73:H73');
v(back,'C75','Total stablecoin supply');v(back,'D75','Use growth, not only level.');v(back,'C76','Bitcoin price');v(back,'D76','Test returns and volatility.');v(back,'C77','USDC market share');v(back,'D77','Use change in percentage points.');
v(back,'C79','Factor correlations were not computed: fresh historical downloads failed DNS resolution.');
v(back,'C80','Three candidate factors are not presumed independent; market share shares a denominator.');
v(back,'C81','Seven financial quarters are insufficient to validate a three-factor predictive regression.');
v(back,'C83','Services model: integration completions + maintenance + USYC performance fees + licensing.');
back.getRange('D9:H31').format.font.color=ink;
back.getRange('D48:H59').format.font.color=ink;
back.getRange('D9:H44').format.horizontalAlignment='right';
back.getRange('D48:H69').format.horizontalAlignment='right';

wb.recalculate();
for(const [i,e]of m.late.entries()){const col='DEFGH'[i];for(const[key,r]of [['prior_quarter_flat',13],['observed_cctp_plus_flat_residual',17],['observed_cctp_plus_day_scaled_residual',21],['prior_quarter_day_scaled',25],['repeat_prior_growth',29]]){const actual=back.getRange(col+r).values[0][0];must(key in e.methods?near(actual,e.methods[key]):actual==='n.a.',e.period+' '+key);}}
for(const [i,e]of m.early.entries()){const col='DEFGH'[i];for(const[key,r]of [['latest_public_flat',49],['latest_public_day_scaled',57],['first30_cctp_plus_latest_public_residual',53]]){const actual=back.getRange(col+r).values[0][0];must(key in e.methods?near(actual,e.methods[key]):actual==='n.a.',e.period+' early '+key);}}
scoreMethods.forEach(([, , ,key],i)=>must(near(back.getRange('M'+(9+i)).values[0][0],m.late_common_metrics[key].mape),key+' MAPE'));
// Change an observed fee and verify the model responds without changing GAAP actuals.
const saved=daily.getRange('D'+(6+series.findIndex(([t])=>new Date(t*1000).toISOString().slice(0,10)==='2026-08-03'))).values[0][0];
const cell='D'+(6+series.findIndex(([t])=>new Date(t*1000).toISOString().slice(0,10)==='2026-08-03'));
const original=back.getRange('H17').values[0][0],actual=back.getRange('H9').values[0][0];
v(daily,cell,saved+0.1);wb.recalculate();must(near(back.getRange('H17').values[0][0],original+0.1),'fee input recalculates hybrid');must(back.getRange('H9').values[0][0]===actual,'actual revenue unchanged by model fee edit');v(daily,cell,saved);wb.recalculate();must(near(back.getRange('H17').values[0][0],original),'fee restored');
await fs.writeFile(path.join(root,'results/workbook_inspection.json'),JSON.stringify({tables:(await wb.inspect({kind:'table',range:"'Transaction backtest'!K8:O12",include:'values,formulas',maxChars:3000})).ndjson,errors:(await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:50},maxChars:2000})).ndjson,checks:qa},null,2));
const exportPath=path.join(out,'Circle_Transaction_Revenue_Backtest.xlsx');await(await SpreadsheetFile.exportXlsx(wb)).save(exportPath);
for(const[sheet,range,name]of [['Transaction backtest','C2:O23','backtest'],['Transaction backtest','C47:M69','early'],['Quarter inputs','C2:L21','inputs'],['Daily CCTP','C2:F16','daily']]){const img=await wb.render({sheetName:sheet,range,scale:1.5,format:'png'});await fs.writeFile(path.join(root,'previews/'+name+'.png'),new Uint8Array(await img.arrayBuffer()));}
console.log(JSON.stringify({exportPath,checksPassed:qa.length}));
