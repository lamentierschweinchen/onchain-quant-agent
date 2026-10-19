#!/usr/bin/env python3
"""Run #29 rail check (run #27 rec #1/#2): value-bearing EGLD deposits and
withdrawals per tracked exchange wallet since restart 2 and inside the window.
Counts from the collector include ESDT spam airdrops; this pass keeps only
transactions with value > 0 EGLD and records distinct counterparties, so
'reopened' means EGLD actually moved. Run AFTER the collector and follow-up.
Writes D["exchange_rails"] into data/collected/2026-10-19.json.
Run #32: also records a full 7-day window (from run #30's rail pass end, Oct 12 15:05:30) per wallet
(run #31 rec #2: test reopening-supply-overhang on 7 days, not a short window)."""
import json, time, urllib.request, urllib.parse
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-10-19"; SNAP=f"{REPO}/data/collected/{RD}.json"
D=json.load(open(SNAP)); API="https://api.multiversx.com"
RESTART2=1790263800
# run #32: run #31's rail pass ran after its 09:08 collector end and before its 09:47 commit; start at the commit
# so nothing is counted twice (may miss <40 min of flow; noted). 7-day pass starts after run #30's rail pass.
RAIL_START=1792057640   # 2026-10-15 09:47:20 UTC
RAIL7_START=1791817530  # 2026-10-12 15:05:30 UTC
WIN=max(D["_period"]["window_start_ts"],RAIL_START)
def get(path,params):
    url=API+path+"?"+urllib.parse.urlencode(params); d=1.5
    for a in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"intel-agent/32-rails"}),timeout=40) as r:
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
# Exchange-operated wallets whose flows are internal, not customer deposits/withdrawals.
# Crypto.com's daily 02:00 sweep to erd1uskf6 (which stakes with Figment) and the
# 0-value 02:00 bot erd1usslt0 ran before the halt too; counting them dated Crypto.com's
# reopening to Sep 29 when the first customer-like flows were Oct 2 (run #28 correction).
INTERNAL={"erd1uskf6lu8x23mrxfm7gde28jaq6m5wxxws2uw5gf5z6yk6srel7mspeukls",
          "erd1usslt0y60j295kxv6dyxrxjjkznjlptdau4wj5wjnshh02qcs3cq7zukls"}
rails={}
for a,v in D["exchange_reopen"].items():
    if not ((v.get("sends_since_restart") or 0)+(v.get("receives_since_restart") or 0)): continue
    rec={"label":v["label"]}
    for side,key,cp in (("sender","out","receiver"),("receiver","in","sender")):
        txs,err=paged(a,side)
        internal=[t for t in txs if int(t.get("value","0"))>0 and t[cp] in INTERNAL]
        val=[t for t in txs if int(t.get("value","0"))>0 and t[cp] not in INTERNAL]
        win=[t for t in val if t["timestamp"]>=WIN]
        w7=[t for t in val if t["timestamp"]>=RAIL7_START]
        rec[key]={"egld_txs_since_restart":len(val),"egld_since_restart":sum(int(t["value"]) for t in val)/1e18,
                  "egld_txs_in_window":len(win),"egld_in_window":sum(int(t["value"]) for t in win)/1e18,
                  "distinct_counterparties_in_window":len({t[cp] for t in win}),
                  "egld_txs_7d":len(w7),"egld_7d":sum(int(t["value"]) for t in w7)/1e18,"distinct_counterparties_7d":len({t[cp] for t in w7}),
                  "by_cp_7d":dict(sorted(((c,sum(int(t["value"]) for t in w7 if t[cp]==c)/1e18) for c in {t[cp] for t in w7}),key=lambda kv:-kv[1])[:15]),
                  "first_egld_ts":val[0]["timestamp"] if val else None,"error":err,
                  "internal_excluded_txs":len(internal),"internal_excluded_egld":sum(int(t["value"]) for t in internal)/1e18,
                  "top":sorted(({"cp":t[cp],"egld":int(t["value"])/1e18,"ts":t["timestamp"]} for t in win),key=lambda x:-x["egld"])[:5]}
    rails[a]=rec
    print(v["label"],{k:(rec[k]["egld_txs_in_window"],round(rec[k]["egld_in_window"]),rec[k]["distinct_counterparties_in_window"]) for k in ("out","in")})
D["exchange_rails"]=rails; D["_period"]["rail_window_start_ts"]=WIN; D["_period"]["rail_7d_start_ts"]=RAIL7_START
json.dump(D,open(SNAP,"w")); print("written")
