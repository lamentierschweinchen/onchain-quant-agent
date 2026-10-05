#!/usr/bin/env python3
"""Run #28 rail check (run #27 rec #1/#2): value-bearing EGLD deposits and
withdrawals per tracked exchange wallet since restart 2 and inside the window.
Counts from the collector include ESDT spam airdrops; this pass keeps only
transactions with value > 0 EGLD and records distinct counterparties, so
'reopened' means EGLD actually moved. Run AFTER the collector and follow-up.
Writes D["exchange_rails"] into data/collected/2026-10-05.json."""
import json, time, urllib.request, urllib.parse
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-10-05"; SNAP=f"{REPO}/data/collected/{RD}.json"
D=json.load(open(SNAP)); API="https://api.multiversx.com"
RESTART2=1790263800; WIN=D["_period"]["window_start_ts"]
def get(path,params):
    url=API+path+"?"+urllib.parse.urlencode(params); d=1.5
    for a in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"intel-agent/28-rails"}),timeout=40) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if a==6: return {"__error__":str(e)}
            time.sleep(d); d=min(d*2,30)
def paged(addr,side):
    out,frm=[],0
    while frm<2000:
        b=get(f"/accounts/{addr}/transactions",{"size":50,"from":frm,"after":RESTART2,"order":"asc","status":"success",side:addr})
        time.sleep(0.4)
        if not isinstance(b,list): return out,b.get("__error__")
        out+=b
        if len(b)<50: return out,None
        frm+=50
    return out,"cap"
rails={}
for a,v in D["exchange_reopen"].items():
    if not ((v.get("sends_since_restart") or 0)+(v.get("receives_since_restart") or 0)): continue
    rec={"label":v["label"]}
    for side,key,cp in (("sender","out","receiver"),("receiver","in","sender")):
        txs,err=paged(a,side)
        val=[t for t in txs if int(t.get("value","0"))>0]
        win=[t for t in val if t["timestamp"]>=WIN]
        rec[key]={"egld_txs_since_restart":len(val),"egld_since_restart":sum(int(t["value"]) for t in val)/1e18,
                  "egld_txs_in_window":len(win),"egld_in_window":sum(int(t["value"]) for t in win)/1e18,
                  "distinct_counterparties_in_window":len({t[cp] for t in win}),
                  "first_egld_ts":val[0]["timestamp"] if val else None,"error":err,
                  "top":sorted(({"cp":t[cp],"egld":int(t["value"])/1e18,"ts":t["timestamp"]} for t in win),key=lambda x:-x["egld"])[:5]}
    rails[a]=rec
    print(v["label"],{k:(rec[k]["egld_txs_in_window"],round(rec[k]["egld_in_window"]),rec[k]["distinct_counterparties_in_window"]) for k in ("out","in")})
D["exchange_rails"]=rails
json.dump(D,open(SNAP,"w")); print("written")
