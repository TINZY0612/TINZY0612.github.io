import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';
const root=path.dirname(fileURLToPath(import.meta.url));
const load=async n=>JSON.parse(await fs.readFile(path.join(root,'results',n),'utf8'));
const reg=await load('subscription_regression.json'),fund=await load('usyc_fund_and_services_analysis.json'),flow=await load('usdc_flow_analysis.json'),route=await load('cctp_route_and_cohort_analysis.json'),mix=await load('usdc_chain_composition.json'),forward=await load('usyc_forward_build_inputs.json'),ff=await load('2026-11-21_Q4_USYC_fee_forecast.json'),supply=await load('supply_projection_forecast.json');
const out=path.resolve(root,'../outputs/01a1fcd4-2a0f-7c92-a89f-a871c89c1db7');await fs.mkdir(out,{recursive:true});await fs.mkdir(path.join(root,'previews'),{recursive:true});
const wb=Workbook.create(),r=wb.worksheets.add('Regression'),o=wb.worksheets.add('Onchain analysis'),d=wb.worksheets.add('Daily factors');
const ink='#263238',navy='#253B59',blue='#2155A3',green='#197045',gray='#5F6B76';
const num='#,##0.000;(#,##0.000);"-"',pct='0.0%;(0.0%);"-"';
const val=(s,a,x)=>s.getRange(a).values=[[x]];
function fx(s,a,x){s.getRange(a).formulas=[[x]];s.getRange(a).format.font.color=x.includes("'Daily factors'")||x.includes("'Regression'")?green:ink;}
function head(s,a){s.getRange(a).format={fill:navy,font:{name:'Arial',size:10,color:'#FFFFFF',bold:true},horizontalAlignment:'center',verticalAlignment:'center',wrapText:true,rowHeight:33};}
function base(s,a,title){s.showGridLines=false;s.getRange(a).format={font:{name:'Arial',size:10,color:ink},verticalAlignment:'center',rowHeight:22};val(s,'C2',title);s.getRange('C2').format.font={name:'Arial',size:14,bold:true,color:navy};s.getRange('C3:L3').format.borders={bottom:{style:'thin',color:navy}};s.getRange('A:B').format.columnWidth=2;}
function date(x){return new Date(x+'T00:00:00Z');}
const qlabel=q=>'Q'+q.slice(-1)+':'+q.slice(2,4);
base(d,'C1:M650','Daily factor inputs');d.getRange('C:D').format.columnWidth=15;d.getRange('E:H').format.columnWidth=21;d.getRange('J:J').format.columnWidth=120;
d.getRange('C8:H8').values=[['UTC/provider date','Quarter','Stablecoins ($bn)','BTC close ($000)','USDC par ($bn)','USDC share (%)']];head(d,'C8:H8');
const data=reg.daily_inputs.map(x=>[date(x.date),qlabel(x.period),x.stablecoin_usd/1e9,x.btc_usd_close/1000,x.usdc_par_usd/1e9]);
d.getRange(`C9:G${8+data.length}`).values=data;d.getRange(`C9:C${8+data.length}`).setNumberFormat('dd-mmm-yy');d.getRange(`E9:H${8+data.length}`).setNumberFormat(num);d.getRange(`E9:G${8+data.length}`).format.font.color=blue;
for(let i=0;i<data.length;i++)fx(d,'H'+(9+i),`=G${9+i}/E${9+i}*100`);
val(d,'J5',reg.sources.stablecoin_total);val(d,'J6',reg.sources.usdc);val(d,'J7',reg.sources.btc);val(d,'J9','Stablecoin total sums totalCirculatingUSD peg categories. USDC is valued at $1 par.');val(d,'J10','BTC uses Coinbase daily UTC closing prices. Extra returned buckets are excluded.');d.freezePanes.freezeRows(8);

base(r,'C1:P74','Circle subscription and services regression');r.tabColor=navy;r.getRange('C:C').format.columnWidth=14;r.getRange('D:M').format.columnWidth=17;r.getRange('N:N').format.columnWidth=17;r.getRange('P:P').format.columnWidth=115;
val(r,'C5','R-squared');fx(r,'D5','=1-D24/D25');val(r,'F5','Adjusted R2');fx(r,'G5','=1-(1-D5)*(COUNT(D9:D15)-1)/(COUNT(D9:D15)-4)');val(r,'I5','LOO MAPE');fx(r,'J5','=AVERAGE(L9:L15)');
val(r,'C6','Quarters');fx(r,'D6','=COUNT(D9:D15)');val(r,'F6','Residual df');fx(r,'G6','=COUNT(D9:D15)-4');val(r,'I6','In-sample MAPE');fx(r,'J6','=SUMPRODUCT(ABS(J9),1)');
// Explicit absolute-error helper avoids array formulas.
r.getRange('C8:L8').values=[['Quarter','Services ($m)','Stablecoins ($bn)','BTC mean ($000)','USDC share (%)','OLS fitted ($m)','Residual ($m)','Signed error','LOO fitted ($m)','LOO abs error']];head(r,'C8:L8');val(r,'N8','Target public by');val(r,'P8','Financial source');
const qs=reg.quarterly_inputs;
for(let i=0;i<qs.length;i++){
 const x=qs[i],n=9+i;val(r,'C'+n,qlabel(x.period));val(r,'D'+n,x.services_actual_usd_million);r.getRange('D'+n).format.font.color=blue;
 for(const[col,src]of [['E','E'],['F','F'],['G','H']])fx(r,col+n,`=AVERAGEIFS('Daily factors'!$${src}$9:$${src}$${8+data.length},'Daily factors'!$D$9:$D$${8+data.length},C${n})`);
 fx(r,'H'+n,`=$E$44+$E$45*E${n}+$E$46*F${n}+$E$47*G${n}`);fx(r,'I'+n,`=D${n}-H${n}`);fx(r,'J'+n,`=H${n}/D${n}-1`);fx(r,'K'+n,`=D${n}-I${54+i}`);fx(r,'L'+n,`=ABS(K${n}/D${n}-1)`);val(r,'N'+n,date(x.target_public_by));val(r,'P'+n,x.target_source_url);
}
r.getRange('D9:L15').setNumberFormat(num);r.getRange('J9:J15').setNumberFormat(pct);r.getRange('L9:L15').setNumberFormat(pct);r.getRange('D9:L15').format.horizontalAlignment='right';r.getRange('N9:N15').setNumberFormat('dd-mmm-yy');r.getRange('D5').setNumberFormat('0.000');r.getRange('G5').setNumberFormat('0.000;(0.000)');r.getRange('J5:J6').setNumberFormat(pct);
val(r,'C18','Seven observations and three residual degrees of freedom. In-sample R2 is not forecast accuracy.');
val(r,'C19','Q1 2025 uses the first comparable split; the later comparative is a sensitivity in the report.');
r.getRange('D21:G21').values=[['Services mean','Stablecoin mean','BTC mean','Share mean']];head(r,'D21:G21');for(const col of ['D','E','F','G'])fx(r,col+'22',`=AVERAGE(${col}9:${col}15)`);r.getRange('D22:G22').setNumberFormat(num);
val(r,'C24','SSE');fx(r,'D24','=SUMPRODUCT(I9:I15,I9:I15)');val(r,'C25','TSS');fx(r,'D25','=SUMPRODUCT(D9:D15,D9:D15)-SUM(D9:D15)^2/COUNT(D9:D15)');val(r,'C26','LOO PRESS');fx(r,'D26','=SUMPRODUCT(I54:I60,I54:I60)');val(r,'F26','LOO predictive R2');fx(r,'G26','=1-D26/D25');r.getRange('D24:G26').setNumberFormat(num);
val(r,'D28','Centered cross-products');r.getRange('D29:H29').values=[['Factor','Stablecoins','BTC','Share','Services']];head(r,'D29:H29');
for(let i=0;i<3;i++){const rr=30+i,src='EFG'[i];val(r,'D'+rr,['Stablecoins','BTC','USDC share'][i]);for(let j=0;j<4;j++){const other='EFGD'[j];fx(r,'EFGH'[j]+rr,`=SUMPRODUCT(${src}9:${src}15,${other}9:${other}15)-SUM(${src}9:${src}15)*SUM(${other}9:${other}15)/COUNT(D9:D15)`);}}
val(r,'C35','Determinant');fx(r,'D35','=E30*(F31*G32-G31*F32)-F30*(E31*G32-G31*E32)+G30*(E31*F32-F31*E32)');
val(r,'D37','Inverse matrix');const inverse=[['(F31*G32-G31*F32)','(G30*F32-F30*G32)','(F30*G31-G30*F31)'],['(G31*E32-E31*G32)','(E30*G32-G30*E32)','(G30*E31-E30*G31)'],['(E31*F32-F31*E32)','(F30*E32-E30*F32)','(E30*F31-F30*E31)']];
inverse.forEach((row,i)=>row.forEach((x,j)=>fx(r,'EFG'[j]+(38+i),'='+x+'/$D$35')));
r.getRange('D43:F43').values=[['Coefficient','OLS beta','VIF']];head(r,'D43:F43');
for(const[n,label]of [[44,'Intercept'],[45,'Stablecoin $bn'],[46,'BTC $000'],[47,'Share, 1pp']])val(r,'D'+n,label);
for(let i=0;i<3;i++){const n=45+i,rr=38+i;fx(r,'E'+n,`=E${rr}*H30+F${rr}*H31+G${rr}*H32`);fx(r,'F'+n,`=${'EFG'[i]}${rr}*${'EFG'[i]}${30+i}`);}
fx(r,'E44','=D22-E45*E22-E46*F22-E47*G22');r.getRange('E44:F47').setNumberFormat('0.0000;(0.0000)');
r.getRange('J29:M29').values=[['Correlation','Stablecoins','BTC','Share']];head(r,'J29:M29');
for(let i=0;i<3;i++){val(r,'J'+(30+i),['Stablecoins','BTC','USDC share'][i]);for(let j=0;j<3;j++)fx(r,'KLM'[j]+(30+i),`=${'EFG'[j]}${30+i}/SQRT(${'EFG'[i]}${30+i}*${'EFG'[j]}${30+j})`);}r.getRange('K30:M32').setNumberFormat('0.000;(0.000)');
r.getRange('C53:I53').values=[['Quarter','Total centered','BTC centered','Share centered','Y centered','Leverage','LOO residual']];head(r,'C53:I53');
for(let i=0;i<7;i++){const h=54+i,n=9+i;fx(r,'C'+h,`=C${n}`);for(const[col,src]of [['D','E'],['E','F'],['F','G'],['G','D']])fx(r,col+h,`=${src}${n}-$${src}$22`);
 fx(r,'H'+h,`=1/COUNT($D$9:$D$15)+D${h}*($E$38*D${h}+$F$38*E${h}+$G$38*F${h})+E${h}*($E$39*D${h}+$F$39*E${h}+$G$39*F${h})+F${h}*($E$40*D${h}+$F$40*E${h}+$G$40*F${h})`);fx(r,'I'+h,`=I${n}/(1-H${h})`);fx(r,'K'+h,`=ABS(J${n})`);
}r.getRange('D54:K60').setNumberFormat(num);fx(r,'J6','=AVERAGE(K54:K60)');
val(r,'C63','OLS is solved from centered normal equations. LOO uses residual divided by (1 - leverage).');
val(r,'C64','LOO trains with later quarters too. It is a diagnostic, not a forward-time backtest.');
val(r,'C66','Growth model R2');val(r,'E66',reg.changes_ols.r_squared);val(r,'G66','Adjusted');val(r,'H66',reg.changes_ols.adjusted_r_squared);
val(r,'C67','Lagged model R2');val(r,'E67',reg.lagged_levels_ols.r_squared);val(r,'G67','Adjusted');val(r,'H67',reg.lagged_levels_ols.adjusted_r_squared);
val(r,'C68','These diagnostic fits are Python outputs; the primary OLS above recalculates in this workbook.');r.getRange('E66:H67').setNumberFormat('0.000;(0.000)');

base(o,'C1:P96','On-chain drivers and financial forecasts');o.getRange('C:C').format.columnWidth=42;o.getRange('D:K').format.columnWidth=17;o.getRange('L:L').format.columnWidth=3;o.getRange('N:N').format.columnWidth=115;
val(o,'C5','Ethereum USDC flow reconciliation, Q3 2026 (USD millions)');head(o,'C7:D7');val(o,'C7','Supply bridge');val(o,'D7','USD millions');
for(const[n,label,value]of [[8,'Opening contract supply',flow.opening_supply_usd_million],[9,'Minted',flow.quarter.amounts_usd_million.mint],[10,'Burned',flow.quarter.amounts_usd_million.burn],[12,'Closing supply from RPC',flow.closing_supply_usd_million]]){val(o,'C'+n,label);val(o,'D'+n,value);o.getRange('D'+n).format.font.color=blue;}
val(o,'C11','Calculated closing supply');fx(o,'D11','=SUM(D8:D9)-D10');val(o,'C13','Reconciliation difference');fx(o,'D13','=D11-D12');
val(o,'F7','Flow component');val(o,'G7','Net ($m)');head(o,'F7:G7');val(o,'F8','CCTP');val(o,'G8',flow.quarter.cctp_net_usd_million);val(o,'F9','Other actors');val(o,'G9',flow.quarter.non_cctp_net_usd_million);val(o,'F10','Total');fx(o,'G10','=SUM(G8:G9)');
val(o,'C15','Other actors are not automatically fiat customer flows. This is one chain, not global USDC.');val(o,'N8','https://ethereum-rpc.publicnode.com');val(o,'N9','https://developers.circle.com/stablecoins/usdc-contract-addresses');
o.getRange('D8:G13').setNumberFormat(num);
val(o,'C19','USYC fee observations plus lagged services residual');o.getRange('C21:K21').values=[['Quarter','Actual services','Prior services','Current USYC fee','Prior USYC fee','Estimate','Signed error','Abs error','Flat abs error']];head(o,'C21:K21');
for(let i=0;i<fund.services_nowcasts.length;i++){const e=fund.services_nowcasts[i],n=22+i,qindex=qs.findIndex(q=>q.period===e.period);val(o,'C'+n,qlabel(e.period));fx(o,'D'+n,`='Regression'!D${9+qindex}`);fx(o,'E'+n,`='Regression'!D${8+qindex}`);fx(o,'F'+n,`=D${85+qindex}`);fx(o,'G'+n,`=D${84+qindex}`);fx(o,'H'+n,`=F${n}+E${n}-G${n}`);fx(o,'I'+n,`=H${n}/D${n}-1`);fx(o,'J'+n,`=ABS(I${n})`);fx(o,'K'+n,`=ABS(E${n}/D${n}-1)`);}
o.getRange('D22:H26').setNumberFormat(num);o.getRange('I22:K28').setNumberFormat(pct);val(o,'H28','MAPE');fx(o,'J28','=AVERAGE(J22:J26)');fx(o,'K28','=AVERAGE(K22:K26)');
val(o,'C30','Direct fee observations are not an audited reconciliation to Circle product revenue.');
val(o,'C33','Forward Q4 USYC fee scenarios as of 21 November 2026');head(o,'C34:D34');val(o,'C34','Driver');val(o,'D34','Value');
const forwardRows=[[35,'Known Q4 fees ($m)','known_fee_usd_million'],[36,'Trailing 28-day fees ($m)','trailing_fee_usd_million'],[37,'Trailing gross income ($m)','trailing_gross_income_usd_million'],[38,'Mean reported NAV ($m)','trailing_mean_aum_usd_million'],[39,'Last reported NAV ($m)','last_aum_usd_million'],[40,'Performance fee fraction','fee_fraction'],[41,'Remaining calendar days','remaining_calendar_days'],[42,'Trailing calendar days','trailing_calendar_days'],[43,'Annual day basis','annual_day_basis']];
for(const[n,label,key]of forwardRows){val(o,'C'+n,label);val(o,'D'+n,forward[key]);o.getRange('D'+n).format.font.color=blue;}
val(o,'F35','Flat daily-fee forecast');fx(o,'H35','=D35+D36/D42*D41');val(o,'F37','Implied gross annual yield');fx(o,'H37','=D37/D38*D43/D42');val(o,'F39','Flat last-NAV forecast');fx(o,'H39','=D35+D39*H37*D40*D41/D43');o.getRange('D35:D39').setNumberFormat(num);o.getRange('D40').setNumberFormat(pct);o.getRange('H35:H39').setNumberFormat(num);o.getRange('H37').setNumberFormat(pct);val(o,'N35',ff.source_url);
val(o,'C45','These are USYC fee components, not total services revenue or net profit. Future actual is unknown.');
val(o,'C48','Ethereum CCTP and address activity, Q3 2026');head(o,'C49:D49');val(o,'C49','Metric');val(o,'D49','Value');
for(const[n,label,value]of [[50,'Source USDC events',route.source_events],[51,'Source USDC volume ($m)',route.source_volume_usd_million],[52,'Unique depositor addresses',route.source_unique_depositors],[53,'Top 10 depositor volume share',route.source_top10_depositor_volume_share],[54,'Direct destination fees ($m)',route.destination_fees_usd/1e6],[55,'Aggregator Ethereum fees ($m)',route.defillama_ethereum_fees_usd/1e6]]){val(o,'C'+n,label);val(o,'D'+n,value);}
val(o,'C56','Direct minus aggregator ($m)');fx(o,'D56','=D54-D55');o.getRange('D51').setNumberFormat(num);o.getRange('D53').setNumberFormat(pct);o.getRange('D54:D56').setNumberFormat(num);
val(o,'F50','July-Aug sender retention');val(o,'H50',route.monthly_depositor_retention[0].retention);val(o,'F52','Aug-Sep sender retention');val(o,'H52',route.monthly_depositor_retention[1].retention);o.getRange('H50:H52').setNumberFormat(pct);
val(o,'C58','Fee-series difference remains unresolved. Sender addresses are not all USDC users.');val(o,'N50','https://developers.circle.com/cctp/references/contract-interfaces');val(o,'N54','https://api.llama.fi/summary/fees/circle-cctp?dataType=dailyFees');
val(o,'C61','Selected-chain circulation at Q3 end');o.getRange('C62:F62').values=[['Chain','Provider amount ($m)','Share of global','Minted field ($m)']];head(o,'C62:F62');
mix.quarterly.at(-1).chains.forEach((x,i)=>{o.getRange(`C${63+i}:F${63+i}`).values=[[x.chain,x.provider_circulation_usd_million,x.share_global,x.native_minted_field_usd_million]];});o.getRange(`D63:F${62+mix.quarterly.at(-1).chains.length}`).setNumberFormat(num);o.getRange(`E63:E${62+mix.quarterly.at(-1).chains.length}`).setNumberFormat(pct);val(o,'C70','Provider circulation includes bridge adjustment. Minted fields are separate; do not sum them.');
val(o,'C73','First-30-day global reserve forecast');o.getRange('C74:E74').values=[['Rule','N','MAPE']];head(o,'C74:E74');val(o,'C75','Supply flat at day 30');val(o,'D75',supply.metrics.flat_last_supply.n);val(o,'E75',supply.metrics.flat_last_supply.mape);val(o,'C76','Continue first-30-day net-flow pace');val(o,'D76',supply.metrics.continue_first30_net_flow_pace.n);val(o,'E76',supply.metrics.continue_first30_net_flow_pace.mape);o.getRange('E75:E76').setNumberFormat(pct);
val(o,'C78','Global supply plus SOFR and an eligible lagged spread. Earlier quarter-end reserve results are unchanged.');
o.getRange('C84:H84').values=[['USYC report quarter','Performance fee ($m)','End report NAV ($m)','Price ($)','Shares (m)','Reports']];head(o,'C84:H84');fund.quarterly.forEach((x,i)=>{o.getRange(`C${85+i}:H${85+i}`).values=[[qlabel(x.period),x.performance_fees_usd_million,x.ending_report_aum_usd_million,x.ending_price_usd,x.ending_share_supply_million,x.reports]];});o.getRange('D85:G91').setNumberFormat(num);val(o,'N85','https://usyc.hashnote.com/api/price-reports');val(o,'N86','https://developers.circle.com/tokenized/usyc/smart-contracts');val(o,'C93','Fund history is not automatically Circle-attributable revenue for every pre-acquisition date.');
o.getRange('D22:K26').format.horizontalAlignment='right';r.getRange('H9:L15').format.font.color=ink;r.getRange('D9:D15').format.font.color=blue;r.getRange('E9:G15').format.font.color=green;
r.getRange('E30:H32').setNumberFormat(num);r.getRange('E38:G40').setNumberFormat('0.000000;(0.000000)');
o.getRange('D13').setNumberFormat('0.00;(0.00)');

const qa=[];function must(x,name){qa.push({name,passed:!!x});if(!x)throw Error(name);}
function near(a,b,t=1e-7){return typeof a==='number'&&Math.abs(a-b)<t;}
wb.recalculate();
for(const[cell,value]of [['D5',reg.primary_levels_ols.r_squared],['G5',reg.primary_levels_ols.adjusted_r_squared],['J5',reg.primary_levels_ols.loo_mape],['G26',reg.primary_levels_ols.loo_predictive_r_squared]])must(near(r.getRange(cell).values[0][0],value),cell+' independently matches numpy OLS');
for(let i=0;i<4;i++)must(near(r.getRange('E'+(44+i)).values[0][0],reg.primary_levels_ols.coefficients[i].coefficient,1e-6),'coefficient '+i);
for(let i=0;i<7;i++){must(near(r.getRange('H'+(9+i)).values[0][0],reg.primary_levels_ols.fitted[i]),'fitted '+i);must(near(r.getRange('K'+(9+i)).values[0][0],reg.primary_levels_ols.loo_predictions[i],1e-5),'LOO '+i);}
must(near(o.getRange('D13').values[0][0],0,1e-6),'flow stock reconciliation');must(near(o.getRange('H35').values[0][0],ff.flat_trailing_daily_fee_q4_estimate_usd_million),'USYC forward pace');must(near(o.getRange('H39').values[0][0],ff.flat_last_aum_and_trailing_yield_q4_estimate_usd_million),'USYC forward NAV');must(near(o.getRange('J28').values[0][0],fund.nowcast_metrics.fee_plus_residual_mape),'services MAPE');
const saved=r.getRange('D15').values[0][0],beta=r.getRange('E45').values[0][0];val(r,'D15',saved+1);wb.recalculate();must(Math.abs(r.getRange('E45').values[0][0]-beta)>1e-8,'OLS refits after target input change');must(r.getRange('D14').values[0][0]===qs[5].services_actual_usd_million,'other target actual unchanged');val(r,'D15',saved);wb.recalculate();must(near(r.getRange('D5').values[0][0],reg.primary_levels_ols.r_squared),'primary R2 restored');
const errors=await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!',options:{useRegex:true,maxResults:50},maxChars:2000});
await fs.writeFile(path.join(root,'results/workbook_qa.json'),JSON.stringify({checks:qa,error_scan:errors.ndjson,primary_inspection:(await wb.inspect({kind:'table',range:'Regression!C5:J6',include:'values,formulas',maxChars:2500})).ndjson},null,2));
const exportPath=path.join(out,'Circle_Onchain_Extensions_and_Regression.xlsx');await(await SpreadsheetFile.exportXlsx(wb)).save(exportPath);
for(const[sheet,range,file]of [['Regression','C2:L19','regression'],['Regression','C28:M47','ols_build'],['Onchain analysis','C2:K30','onchain'],['Onchain analysis','C33:K58','forward'],['Onchain analysis','C61:K93','drivers'],['Daily factors','C2:H18','daily']]){const img=await wb.render({sheetName:sheet,range,scale:1.4,format:'png'});await fs.writeFile(path.join(root,'previews/'+file+'.png'),new Uint8Array(await img.arrayBuffer()));}
console.log(JSON.stringify({exportPath,checks:qa.length}));
