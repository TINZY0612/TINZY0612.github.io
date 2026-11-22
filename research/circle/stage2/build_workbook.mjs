import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root=path.dirname(fileURLToPath(import.meta.url));
const model=JSON.parse(await fs.readFile(path.join(root,'results/stage2_data_model.json'),'utf8'));
const out=path.join(root,'../outputs/01a1fcd4-2a0f-7c92-a89f-a871c89c1db7');
const previewDir=path.join(root,'previews');
await fs.mkdir(out,{recursive:true}); await fs.mkdir(previewDir,{recursive:true});
const wb=Workbook.create();
const actual=wb.worksheets.add('Quarterly actuals');
const supply=wb.worksheets.add('Supply reconciliation');
const inputs=wb.worksheets.add('Source inputs');
const navy='#283B58', ink='#1F2937', blue='#2355A4', green='#197045', tan='#F4EBDD', muted='#657185';
const num='#,##0.000;(#,##0.000);"-"';
const gapnum='#,##0.00;(#,##0.00);0.00';
const headings={reserve_income:'Reserve income',other_revenue:'Other revenue',total_revenue:'Total revenue and reserve income',
 distribution_transaction_costs:'Distribution and transaction costs',other_costs:'Other costs',total_costs:'Total distribution, transaction and other costs',
 usdc_end:'USDC in circulation, end of period',usdc_average:'USDC in circulation, average of period',reserve_return:'Reserve return rate',platform_weight:'USDC on platform, weighted average'};
function base(sheet,range){
 sheet.showGridLines=false;
 sheet.getRange(range).format.font={name:'Arial',size:10,color:ink};
 sheet.getRange(range).format.verticalAlignment='center';
 sheet.getRange(range).format.rowHeight=23;
 sheet.getRange('A1:B50').format.columnWidth=2;
}
function title(sheet,text,last='J'){
 sheet.getRange('C2').values=[[text]];
 sheet.getRange('C2').format.font={name:'Arial',size:14,bold:true,color:navy};
 sheet.getRange(`C3:${last}3`).format.borders={bottom:{style:'thin',color:navy}};
}
function header(sheet,range){sheet.getRange(range).format={fill:navy,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',verticalAlignment:'center'};}
function section(sheet,range){sheet.getRange(range).format.fill='#EDF0F5';sheet.getRange(range).format.font={name:'Arial',size:10,bold:true,color:navy};}
function val(sheet,cell,value){sheet.getRange(cell).values=[[value]];}
function formula(sheet,cell,text){sheet.getRange(cell).formulas=[[text]];}
function near(a,b,eps=1e-7){return typeof a==='number'&&Math.abs(a-b)<=eps;}
function must(test,message){if(!test)throw new Error(message);}
const observationRows=new Map();
const inputStart=10;
base(inputs,'C1:K330'); title(inputs,'Circle source observations','K');
inputs.getRange('C1:K330').format.wrapText=false;
inputs.getRange('C1:C330').format.columnWidth=10;
inputs.getRange('D1:D330').format.columnWidth=14;
inputs.getRange('E1:E330').format.columnWidth=48;
inputs.getRange('F1:F330').format.columnWidth=18;
inputs.getRange('G1:G330').format.columnWidth=18;
inputs.getRange('H1:H330').format.columnWidth=16;
inputs.getRange('I1:I330').format.columnWidth=90;
inputs.getRange('J1:J330').format.columnWidth=3;
inputs.getRange('K1:K330').format.columnWidth=150;
val(inputs,'C4','Supply investigation threshold');val(inputs,'F4',model.supply_materiality_threshold);
inputs.getRange('F4').setNumberFormat('0.00%');inputs.getRange('F4').format.font={name:'Arial',size:10,color:blue};
val(inputs,'C6','Original observations and stated units. Missing source dates remain unavailable.');
inputs.getRange('C6').format.font={name:'Arial',size:10,italic:true,color:muted};
inputs.getRange('C9:I9').values=[['ID','Period','Metric','Value','Unit','Public by','Source locator']];
header(inputs,'C9:I9');val(inputs,'K9','Source URL');
const rows=model.source_observations.map((o,i)=>{
 observationRows.set(o.id,inputStart+i);
 return [o.id,o.period,headings[o.metric]||o.metric.replaceAll('_',' '),o.unit==='date'?new Date(o.value+'T00:00:00Z'):o.value,o.unit,
  o.published_by?new Date(o.published_by+'T00:00:00Z'):'n.a.',o.locator];
});
inputs.getRange(`C${inputStart}:I${inputStart+rows.length-1}`).values=rows;
inputs.getRange(`K${inputStart}:K${inputStart+rows.length-1}`).values=model.source_observations.map(o=>[o.source_url]);
inputs.getRange(`F${inputStart}:F${inputStart+rows.length-1}`).setNumberFormat(num);
inputs.getRange(`F${inputStart}:F${inputStart+rows.length-1}`).format.font={name:'Arial',size:10,color:blue};
inputs.getRange(`H${inputStart}:H${inputStart+rows.length-1}`).setNumberFormat('dd-mmm-yy');
model.source_observations.forEach(o=>{
 const cell=inputs.getRange(`F${observationRows.get(o.id)}`);
 if(o.unit==='date')cell.setNumberFormat('dd-mmm-yy');
 else if(o.unit==='decimal')cell.setNumberFormat('0.0%');
 else if(o.source_precision>=1)cell.setNumberFormat('#,##0;(#,##0);"-"');
 else if(o.source_precision===0.000001)cell.setNumberFormat('#,##0.000000;(#,##0.000000);"-"');
});
const chainStart=inputStart+rows.length+5;
val(inputs,`E${chainStart-2}`,'API chain fields at 1 October 2026 date bucket, USDC millions');
inputs.getRange(`E${chainStart}:I${chainStart}`).values=[['Chain','Minted field','Unreleased field','Circulation field','Absent fields are not proven zero balances']];
header(inputs,`E${chainStart}:I${chainStart}`);
inputs.getRange(`E${chainStart+1}:I${chainStart+model.chain_field_inventory.length}`).values=model.chain_field_inventory.map(r=>[
 r.chain,r.minted_field_present?r.api_minted/1e6:'n.a.',r.unreleased_field_present?r.api_unreleased/1e6:'n.a.',r.api_circulating/1e6,
 !r.minted_field_present&&!r.unreleased_field_present?'Minted and unreleased absent':!r.minted_field_present?'Minted absent':!r.unreleased_field_present?'Unreleased absent':'Fields present']);
inputs.getRange(`F${chainStart+1}:H${chainStart+model.chain_field_inventory.length}`).setNumberFormat(num);
inputs.getRange(`F${chainStart+1}:H${chainStart+model.chain_field_inventory.length}`).format.horizontalAlignment='right';
inputs.getRange(`F${chainStart+1}:H${chainStart+model.chain_field_inventory.length}`).format.font={name:'Arial',size:10,color:blue};
val(inputs,`K${chainStart+1}`,'https://stablecoins.llama.fi/stablecoin/2');
inputs.freezePanes.freezeRows(9); inputs.freezePanes.freezeColumns(5);
inputs.tabColor=tan;

function ref(id){return `'Source inputs'!F${observationRows.get(id)}`;}
function safeRef(id){const r=ref(id);return `IF(ISNUMBER(${r}),${r},NA())`;}
function metricExpr(metric,negative=false){
 const ids=metric.input_ids;
 const expr=metric.operation==='subtract'?`IF(AND(ISNUMBER(${ref(ids[0])}),ISNUMBER(${ref(ids[1])})),${ref(ids[0])}-${ref(ids[1])},NA())`:safeRef(ids[0]);
 return '='+ (negative?`-(${expr})`:expr);
}
base(actual,'C1:J43'); title(actual,'Circle quarterly actuals');
actual.getRange('C1:C43').format.columnWidth=48;
actual.getRange('D1:J43').format.columnWidth=15;
val(actual,'C4','USD millions. USDC rows use token millions. Rates use percentages.');
actual.getRange('C4').format.font={name:'Arial',size:10,italic:true,color:muted};
actual.getRange('C6:J6').values=[['Metric',...model.quarters.map(q=>`Q${q.period.at(-1)}:${q.period.slice(2,4)}`)]];
header(actual,'C6:J6');
const rowMap={reserve_income:8,other_revenue:9,total_revenue:10,distribution_transaction_costs:12,other_costs:13,total_costs:14,
 rldc:16,rldc_margin:17,reserve_income_share:19,cost_ratio_to_reserve_income:20,usdc_end:22,usdc_average:23,reserve_return:24,platform_weight:25};
const labels={...headings,rldc:'Revenue less distribution costs',rldc_margin:'RLDC margin',reserve_income_share:'Reserve income / total revenue',cost_ratio_to_reserve_income:'Total costs / reserve income'};
for(const [key,row]of Object.entries(rowMap))val(actual,`C${row}`,labels[key]);
actual.getRange('D8:J25').setNumberFormat(num);
actual.getRange('D22:J23').setNumberFormat('#,##0;(#,##0);"-"');
for(const row of [10,14,16])section(actual,`C${row}:J${row}`);
for(const row of [17,19,20,24,25]){
 actual.getRange(`C${row}:J${row}`).format.font={name:'Arial',size:10,italic:true,color:ink};
 actual.getRange(`D${row}:J${row}`).setNumberFormat('0.0%');
}
model.quarters.forEach((q,i)=>{
 const col=String.fromCharCode(68+i);
 for(const key of ['reserve_income','other_revenue','distribution_transaction_costs','other_costs','usdc_end','usdc_average','reserve_return','platform_weight'])formula(actual,`${col}${rowMap[key]}`,metricExpr(q.metrics[key],['distribution_transaction_costs','other_costs'].includes(key)));
 formula(actual,`${col}10`,`=SUM(${col}8:${col}9)`);
 formula(actual,`${col}14`,`=SUM(${col}12:${col}13)`);
 formula(actual,`${col}16`,`=SUM(${col}10,${col}14)`);
 formula(actual,`${col}17`,`=IF(${col}10=0,"n.a.",${col}16/${col}10)`);
 formula(actual,`${col}19`,`=IF(${col}10=0,"n.a.",${col}8/${col}10)`);
 formula(actual,`${col}20`,`=IF(${col}8=0,"n.a.",-${col}14/${col}8)`);
 val(actual,`${col}28`,new Date(q.metrics.total_revenue.published_by+'T00:00:00Z'));
 if(q.earnings_release_input_id)formula(actual,`${col}29`,'='+ref(q.earnings_release_input_id));
 else val(actual,`${col}29`,'n.a.');
 formula(actual,`${col}31`,`=${col}10-(${metricExpr(q.metrics.total_revenue).slice(1)})`);
 formula(actual,`${col}32`,`=-${col}14-(${metricExpr(q.metrics.total_costs).slice(1)})`);
});
val(actual,'C28','Exact flow source public by');actual.getRange('D28:J28').setNumberFormat('dd-mmm-yy');
val(actual,'C29','Verified earnings-release date');actual.getRange('D29:J29').setNumberFormat('dd-mmm-yy');
val(actual,'C30','Arithmetic differences, USD millions');
val(actual,'C31','Revenue components less reported total');val(actual,'C32','Cost components less reported total');
val(actual,'C33','Four 2025 quarters less annual revenue');
formula(actual,'G33',`=SUM(D10:G10)-${ref(model.annual_controls['2025FY'].total_revenue.id)}`);
actual.getRange('D31:J33').setNumberFormat(gapnum);
actual.getRange('D31:J33').conditionalFormats.addCustom('ABS(D31)>0.002',{fill:'#FDE9E7',font:{bold:true,color:'#A32121'}});
val(actual,'C36','Q4 2025 flows: FY2025 less nine months. Stocks and percentages are not subtracted.');
val(actual,'C37','Q4 average circulation is reported to USD 0.1 billion, displayed here in millions.');
val(actual,'C38','Q1 2025 reserve return and platform weight are later comparatives, published in May 2026.');
val(actual,'C39','Q3 2026 other revenue includes ARC presale recognition. RLDC is not net income.');
actual.getRange('C36:J39').format.font={name:'Arial',size:10,color:muted};
actual.tabColor=navy;

base(supply,'C1:J49');title(supply,'USDC supply reconciliation');
supply.getRange('C1:C49').format.columnWidth=14;
supply.getRange('D1:F49').format.columnWidth=21;
supply.getRange('G1:G49').format.columnWidth=17;
supply.getRange('H1:H49').format.columnWidth=16;
supply.getRange('I1:I49').format.columnWidth=21;
supply.getRange('J1:J49').format.columnWidth=43;
val(supply,'C4','USDC millions. Provider timestamps identify daily buckets, not verified EOD balances.');
supply.getRange('C4').format.font={name:'Arial',size:10,italic:true,color:muted};
supply.getRange('C6:J6').values=[['Period','Attested circulation','Same-date bucket','Following-date bucket','Following gap','Gap %','Materiality','Timing']];header(supply,'C6:J6');
supply.getRange('C6:J6').format.wrapText=true;supply.getRange('C6:J6').format.rowHeight=38;
model.supply_checkpoints.forEach((s,i)=>{
 const row=7+i;
 val(supply,`C${row}`,`Q${s.period.at(-1)}:${s.period.slice(2,4)}`);
 for(const [col,key]of [['D','attested_circulation'],['E','provider_same_date_bucket'],['F','provider_following_date_bucket']])formula(supply,`${col}${row}`,'='+safeRef(s.input_ids[key]));
 formula(supply,`G${row}`,`=F${row}-D${row}`);formula(supply,`H${row}`,`=IF(D${row}=0,"n.a.",G${row}/D${row})`);
 formula(supply,`I${row}`,`=IF(ABS(H${row})>'Source inputs'!$F$4,"Investigate","Below threshold")`);
 val(supply,`J${row}`,'Observation time unverified');
});
supply.getRange('D7:G13').setNumberFormat(num);supply.getRange('H7:H13').setNumberFormat('0.00%');
supply.getRange('I7:I13').format.horizontalAlignment='center';
supply.getRange('G7:I13').conditionalFormats.addCustom("ABS($H7)>'Source inputs'!$F$4",{fill:'#FDE9E7',font:{color:'#A32121',bold:true}});
val(supply,'C16','September gap decomposition, USDC millions');
supply.getRange('C16').format.font={name:'Arial',size:11,bold:true,color:navy};
const crStart=chainStart+1,crEnd=chainStart+model.chain_field_inventory.length;
const d=model.supply_decomposition;
// Source and calculation rows have one owner; output differences below reuse them.
const bridgeRows=[
 [18,'API minted fields',`=SUM('Source inputs'!F${crStart}:F${crEnd})`],
 [19,'API unreleased fields',`=SUM('Source inputs'!G${crStart}:G${crEnd})`],
 [20,'API chain circulation',`=SUM('Source inputs'!H${crStart}:H${crEnd})`],
 [21,'API global circulation','=F13'],
 [22,'Circle raw approved supply','='+safeRef(d.official_input_ids.official_raw_supply)],
 [23,'Circle allowed not issued','='+safeRef(d.official_input_ids.official_allowed_not_issued)],
 [24,'Circle access denied','='+safeRef(d.official_input_ids.official_access_denied)],
 [25,'Circle pending burns','='+safeRef(d.official_input_ids.official_pending_burns)],
 [26,'Circle circulation','=D13'],
 [29,'Minted classification gap','=G18-G22'],
 [30,'Unreleased classification effect','=G23-G19'],
 [31,'Access-denied exclusion','=G24'],
 [32,'Pending-burn exclusion','=G25'],
 [33,'Chain aggregation residual','=G20-(G18-G19)'],
 [34,'Global versus chain rounding','=G21-G20'],
 [36,'Total difference','=SUM(G29:G34)'],
 [37,'Direct provider minus official','=G21-G26'],
 [39,'Decomposition difference','=G36-G37'],
];
for(const [row,label,expr]of bridgeRows){val(supply,`D${row}`,label);formula(supply,`G${row}`,expr);}
supply.getRange('D18:F39').format.font={name:'Arial',size:10,color:ink};
supply.getRange('G18:G39').setNumberFormat(num);
section(supply,'D36:G37');supply.getRange('G39').setNumberFormat('0.000000');
supply.getRange('G39').conditionalFormats.addCustom('ABS(G39)>0.000001',{fill:'#FDE9E7',font:{bold:true,color:'#A32121'}});
val(supply,'D42','This is an algebraic decomposition of different definitions and observation times.');
val(supply,'D43','The component differences are not proven causal corrections.');
val(supply,'D44','API category totals sum available fields. Absent fields are not confirmed zero balances.');
supply.getRange('D42:J44').format.font={name:'Arial',size:10,color:muted};
supply.tabColor='#526783';

wb.recalculate();
const validation=[];
for(const [i,q]of model.quarters.entries()){
 const col=String.fromCharCode(68+i);
 for(const key of ['reserve_income','other_revenue','total_revenue','total_costs','rldc','rldc_margin','usdc_average']){
  const actualValue=actual.getRange(`${col}${rowMap[key]}`).values[0][0];
  const expected=q.metrics[key].value*(key==='total_costs'?-1:1);
  must(near(actualValue,expected,1e-6),`${q.period} ${key}: ${actualValue} vs ${expected}`);
  validation.push({period:q.period,metric:key,matched:true});
 }
}
must(near(supply.getRange('G36').values[0][0],269.451647,1e-6),'Supply gap decomposition incorrect');
must(Math.abs(supply.getRange('G39').values[0][0])<=0.000001,'Supply decomposition check failed');
// Exercise a source change, a valid zero and a missing prerequisite, then restore.
const first=model.quarters[0].metrics.reserve_income.input_ids[0];
const sourceCell=inputs.getRange(`F${observationRows.get(first)}`);
const original=sourceCell.values[0][0];
sourceCell.values=[[original+1]];wb.recalculate();
must(near(actual.getRange('D16').values[0][0],model.quarters[0].metrics.rldc.value+1),'RLDC did not update with reserve income');
must(near(actual.getRange('D31').values[0][0],1),'Revenue check did not expose changed source');
sourceCell.values=[[0]];wb.recalculate();
must(actual.getRange('D8').values[0][0]===0,'Valid zero source was lost');
must(actual.getRange('D20').values[0][0]==='n.a.','Zero denominator was not handled explicitly');
sourceCell.values=[[null]];wb.recalculate();
const missingInspect=await wb.inspect({kind:'table',range:'Quarterly actuals!D8:D16',include:'values,formulas',tableMaxRows:9,tableMaxCols:1,maxChars:3000});
must(missingInspect.ndjson.includes('#N/A'),'Missing required source did not surface as unavailable');
sourceCell.values=[[original]];
inputs.getRange('F4').values=[[0.005]];wb.recalculate();
must(supply.getRange('I7:I13').values.every(r=>r[0]==='Below threshold'),'Materiality flags did not update');
inputs.getRange('F4').values=[[model.supply_materiality_threshold]];
wb.recalculate();
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:80},summary:'Final formula error scan',maxChars:5000});
await fs.writeFile(path.join(root,'results/workbook_formula_scan.txt'),errors.ndjson);
const inspected=await wb.inspect({kind:'table',range:'Quarterly actuals!C6:J33',include:'values,formulas',tableMaxRows:28,tableMaxCols:8,maxChars:22000});
await fs.writeFile(path.join(root,'results/workbook_actuals_inspection.txt'),inspected.ndjson);
const file=await SpreadsheetFile.exportXlsx(wb);
const workbookPath=path.join(out,'Circle_Quarterly_Actuals.xlsx');await file.save(workbookPath);
for(const [sheetName,range,name]of [
 ['Quarterly actuals','C1:J40','quarterly_actuals'],
 ['Supply reconciliation','C1:J44','supply_reconciliation'],
 ['Source inputs','C1:I24','source_inputs'],
 ['Source inputs',`E${chainStart-2}:I${chainStart+12}`,'chain_fields'],
]){
 const rendered=await wb.render({sheetName,range,scale:1.4,format:'png'});
 await fs.writeFile(path.join(previewDir,name+'.png'),new Uint8Array(await rendered.arrayBuffer()));
}
await fs.writeFile(path.join(root,'results/workbook_validation.json'),JSON.stringify({
 workbook:workbookPath,checked_values:validation.length,source_change_test:true,zero_source_test:true,missing_source_test:true,materiality_threshold_test:true,
 supply_decomposition_difference:supply.getRange('G39').values[0][0],validation},null,2));
console.log(JSON.stringify({workbook:workbookPath,checked_values:validation.length,formulaScan:errors.ndjson},null,2));
