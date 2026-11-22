import concurrent.futures
import datetime as dt
import json
from public_data import fetch,ROOT
qs=json.loads((ROOT.parent/'stage2/results/stage2_data_model.json').read_text())['quarters']
jobs=[('usdc_current_history','https://stablecoins.llama.fi/stablecoin/2'),
 ('usdc_contract_source','https://raw.githubusercontent.com/circlefin/stablecoin-evm/master/contracts/v1/FiatTokenV1.sol')]
for q in qs:
    end=(dt.date.fromisoformat(q['end'])+dt.timedelta(days=1)).isoformat()
    jobs.append(('btc_'+q['period'],f"https://api.exchange.coinbase.com/products/BTC-USD/candles?granularity=86400&start={q['start']}T00:00:00Z&end={end}T00:00:00Z"))
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    futures=[pool.submit(fetch,*j) for j in jobs]
    for f in futures:
        try:f.result()
        except Exception as e:print('PUBLIC SOURCE FAILED:',e,flush=True)
