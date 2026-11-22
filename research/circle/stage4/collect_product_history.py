"""Download bounded free product history and its open-source definitions."""
from collect_stage4 import run
run([
 ('usyc_product_page','https://www.circle.com/usyc'),
 ('llama_usyc_dashboard','https://defillama.com/protocol/circle-usyc'),
 ('llama_cctp_dashboard','https://defillama.com/protocol/circle-cctp'),
 ('llama_usyc_adapter','https://raw.githubusercontent.com/DefiLlama/dimension-adapters/master/fees/hashnote-usyc/index.ts'),
 ('llama_cctp_adapter','https://raw.githubusercontent.com/DefiLlama/dimension-adapters/master/fees/cctp/index.ts'),
 ('llama_usyc_fee_history','https://api.llama.fi/summary/fees/circle-usyc?dataType=dailyFees'),
 ('llama_cctp_fee_history','https://api.llama.fi/summary/fees/circle-cctp?dataType=dailyFees'),
 ('usyc_history_limit_test','https://usyc.hashnote.com/api/price-reports?limit=2000'),
 ('usyc_history_offset_test','https://usyc.hashnote.com/api/price-reports?offset=45'),
])
