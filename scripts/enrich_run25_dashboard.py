#!/usr/bin/env python3
"""Run #25 dashboard enrichment: persist the time series the two new panels need.

(1) MEX/WEGLD pause timeline - CoinGecko MEX hourly price + volume (14d), and the
    pair contract's own call history (every tx since Sep 7, success and fail) so
    the pause, the last swap and the failed-withdrawal wall are plotted from
    chain data rather than described.
(2) Pipeline in market scale - CoinGecko EGLD daily spot volume (90d) so the
    delivery-as-share-of-spot series can be backfilled for every run whose
    7-day window sits inside the range.
Written into data/collected/2026-09-14.json under dash_* keys.
"""
import json, time, urllib.request, urllib.parse
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
SNAP=f"{REPO}/data/collected/2026-09-14.json"
PAIR="erd1qqqqqqqqqqqqqpgqa0fsfshnff4n76jhcye6k7uvd7qacsq42jpsp6shh2"
def g(url, retries=5):
    d=1.5
    for a in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"intel-agent/25-dash"}),timeout=40) as r:
                return json.loads(r.read())
        except Exception as e:
            if a==retries-1: return {"__error__":str(e)}
            time.sleep(d); d*=2
D=json.load(open(SNAP))
D["dash_cg_mex_hourly"]=g("https://api.coingecko.com/api/v3/coins/maiar-dex/market_chart?vs_currency=usd&days=14")
time.sleep(2)
D["dash_cg_egld_90d"]=g("https://api.coingecko.com/api/v3/coins/elrond-erd-2/market_chart?vs_currency=usd&days=90&interval=daily")
time.sleep(1)
txs=[]; frm=0
while True:
    q=urllib.parse.urlencode({"size":50,"from":frm,"after":1788739200,"order":"desc"})
    b=g(f"https://api.multiversx.com/accounts/{PAIR}/transactions?{q}")
    if not isinstance(b,list): print("pair page error",b); break
    txs+= [{"ts":t["timestamp"],"fn":t.get("function"),"status":t.get("status"),"sender":t.get("sender")} for t in b]
    if len(b)<50: break
    frm+=50; time.sleep(0.3)
D["dash_mex_pair_txs"]=txs
json.dump(D,open(SNAP,"w"))
from collections import Counter
print("mex hourly pts",len((D["dash_cg_mex_hourly"] or {}).get("prices",[])),"egld 90d pts",len((D["dash_cg_egld_90d"] or {}).get("total_volumes",[])))
print("pair txs",len(txs),Counter((t["fn"],t["status"]) for t in txs).most_common(8))
