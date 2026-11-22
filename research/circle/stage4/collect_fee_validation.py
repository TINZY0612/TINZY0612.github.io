"""Read-only performance-fee data and one Ethereum receipt control."""
import json
from collect_stage4 import run, ROOT
p=json.loads((ROOT/'raw/usyc_historical_prices.json').read_text())['data'][0]
run([
 ('llama_usyc_revenue_history','https://api.llama.fi/summary/fees/circle-usyc?dataType=dailyRevenue'),
 ('usyc_fee_receipt','https://ethereum-rpc.publicnode.com',{'jsonrpc':'2.0','id':1,'method':'eth_getTransactionReceipt','params':[p['txhash']]}),
 ('llama_usyc_adapter_commit','https://api.github.com/repos/DefiLlama/dimension-adapters/commits?path=fees/hashnote-usyc/index.ts&per_page=1'),
 ('llama_cctp_adapter_commit','https://api.github.com/repos/DefiLlama/dimension-adapters/commits?path=fees/cctp/index.ts&per_page=1'),
])
