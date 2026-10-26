#!/usr/bin/env python3
"""Run #29 rail check (run #27 rec #1/#2): value-bearing EGLD deposits and
withdrawals per tracked exchange wallet since restart 2 and inside the window.
Counts from the collector include ESDT spam airdrops; this pass keeps only
transactions with value > 0 EGLD and records distinct counterparties, so
'reopened' means EGLD actually moved. Run AFTER the collector and follow-up.
Writes D["exchange_rails"] into data/collected/2026-10-22.json.
Run #34: window starts at run #33 stored rail end (Oct 22 13:48:49); fixed overhang-absorbed window Oct 19 14:40:28 -> Oct 26 14:40:28 stored as *_ov. Run #33 note: window starts at run #32's stored rail end (Oct 19 14:40:28). The 7-day pass is a TRAILING
7 days ending now (overlaps run #32 by ~4.8 days); the non-overlapping 7-day window run #32 rec #3 asked
for matures Oct 26 and is resolved next run. Stores its own end time in _period.rail_window_end_ts (run #32 rec #6)."""
import json, time, urllib.request, urllib.parse
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-10-26"; SNAP=f"{REPO}/data/collected/{RD}.json"
D=json.load(open(SNAP)); API="https://api.multiversx.com"
RESTART2=1790263800
# run #33: run #32 stored its rail end (1792420828 = 2026-10-19 14:40:28 UTC); start exactly there.
RAIL_START=1792676929   # run #33 stored rail end 2026-10-22 13:48:49 UTC
OV_START,OV_END=1792420828,1793025628   # overhang-absorbed fixed window: 2026-10-19 14:40:28 -> 2026-10-26 14:40:28 UTC
RAIL7_START=int(time.time())-7*86400  # trailing 7 days
WIN=max(D["_period"]["window_start_ts"],RAIL_START)
def get(path,params):
    url=API+path+"?"+urllib.parse.urlencode(params); d=1.5
    for a in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"intel-agent/34-rails"}),timeout=40) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if a==6: return {"__error__":str(e)}
            time.sleep(d); d=min(d*2,30)
def paged(addr,side):
    out,frm=[],0
    while frm<8000:
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
        wov=[t for t in val if OV_START<=t["timestamp"]<OV_END]
        rec[key]={"egld_txs_since_restart":len(val),"egld_since_restart":sum(int(t["value"]) for t in val)/1e18,
                  "egld_txs_in_window":len(win),"egld_in_window":sum(int(t["value"]) for t in win)/1e18,
                  "distinct_counterparties_in_window":len({t[cp] for t in win}),
                  "egld_txs_7d":len(w7),"egld_7d":sum(int(t["value"]) for t in w7)/1e18,"distinct_counterparties_7d":len({t[cp] for t in w7}),
                  "by_cp_7d":dict(sorted(((c,sum(int(t["value"]) for t in w7 if t[cp]==c)/1e18) for c in {t[cp] for t in w7}),key=lambda kv:-kv[1])[:15]),
                  "egld_txs_ov":len(wov),"egld_ov":sum(int(t["value"]) for t in wov)/1e18,
                  "by_cp_ov":dict(sorted(((c,sum(int(t["value"]) for t in wov if t[cp]==c)/1e18) for c in {t[cp] for t in wov}),key=lambda kv:-kv[1])[:25]),
                  "first_egld_ts":val[0]["timestamp"] if val else None,"error":err,
                  "internal_excluded_txs":len(internal),"internal_excluded_egld":sum(int(t["value"]) for t in internal)/1e18,
                  "top":sorted(({"cp":t[cp],"egld":int(t["value"])/1e18,"ts":t["timestamp"]} for t in win),key=lambda x:-x["egld"])[:5]}
    rails[a]=rec
    print(v["label"],{k:(rec[k]["egld_txs_in_window"],round(rec[k]["egld_in_window"]),rec[k]["distinct_counterparties_in_window"]) for k in ("out","in")})
D["exchange_rails"]=rails; D["_period"]["rail_window_start_ts"]=WIN; D["_period"]["rail_7d_start_ts"]=RAIL7_START; D["_period"]["rail_window_end_ts"]=int(time.time())
D["_period"]["rail_7d_basis"]="trailing 7d ending at rail_window_end_ts"; D["_period"]["rail_ov_start_ts"]=OV_START; D["_period"]["rail_ov_end_ts"]=OV_END
json.dump(D,open(SNAP,"w")); print("written")
