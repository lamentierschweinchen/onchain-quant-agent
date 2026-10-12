#!/usr/bin/env python3
"""Run #30 targeted traces (after collector/followup/rails). Writes D["run30_traces"].
(5) run #29 rec #2: collector-side exit-route scan over EVERY withdraw call > 3,000 EGLD, next hop classified.
(6) run #29 rec #1: Binance.com per-day value-bearing deposits/withdrawals since Oct 9 08:04; funder wallets re-deposit check.
(7) run #29 rec #3: OTC desk terminal erd1y27r22 resolution.
(8) run #29 rec #5: Hatom EGLD money-market call history Oct 5 -> now (withdraw vs liquidation).
(1) Largest EGLD deposits into the Binance.com hot wallet in the window: who sent, and where did the sender's EGLD come from (provider withdraw? DEX?)
(2) The 11,000 EGLD Binance withdrawal: recipient and onward hop.
(3) The OTC desk's first post-halt outbound: timestamps, routers, terminals.
(4) Exit-route scan (run #28 rec #3): every provider withdraw call > 1,000 EGLD in the follow-up decode -> where did the sender's EGLD go next.
"""
import json,time,urllib.request,urllib.parse
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent";SNAP=f"{REPO}/data/collected/2026-10-12.json"
D=json.load(open(SNAP));API="https://api.multiversx.com";WIN=D["_period"]["window_start_ts"]
kn=json.load(open(f"{REPO}/data/known-addresses.json"));LM={}
for s,e in kn.items():
    if isinstance(e,dict):
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"): LM[a]=(m.get("name"),m.get("category"))
def get(p,**q):
    url=API+p+("?"+urllib.parse.urlencode(q) if q else "");d=1.5
    for a in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"intel-agent/30-trace"}),timeout=40) as r: return json.loads(r.read().decode())
        except Exception as e:
            if a==6: return {"__error__":str(e)}
            time.sleep(d);d=min(d*2,30)
def txs(a,after=0,n=100,**kw):
    r=get(f"/accounts/{a}/transactions",size=n,after=after,order="desc",status="success",**kw);time.sleep(0.45);return r if isinstance(r,list) else []
def eg(t): return int(t.get("value","0"))/1e18
BIN="erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets"
T={}
# (1) deposits
dep=[t for t in txs(BIN,WIN,100,receiver=BIN) if eg(t)>=500]
dep+= [t for t in txs(BIN,WIN+0,100,receiver=BIN,**{"from":100}) if eg(t)>=500] if len(dep)>=1 else []
by={}
for t in dep:
    by.setdefault(t["sender"],[]).append({"egld":eg(t),"ts":t["timestamp"],"hash":t["txHash"]})
rows=[]
for s,l in sorted(by.items(),key=lambda kv:-sum(x["egld"] for x in kv[1]))[:8]:
    info=get(f"/accounts/{s}");time.sleep(0.4)
    inb=txs(s,WIN-86400*14,40,receiver=s)
    src={}
    for t in inb:
        if eg(t)>=100: src.setdefault(t["sender"],[]).append({"egld":eg(t),"fn":t.get("function"),"ts":t["timestamp"]})
    rows.append({"sender":s,"label":LM.get(s),"total_egld":sum(x["egld"] for x in l),"n":len(l),"deposits":l[:6],
                 "balance_egld":int(info.get("balance","0"))/1e18 if isinstance(info,dict) else None,
                 "inbound_sources_14d":[{"from":k,"label":LM.get(k),"egld":sum(x["egld"] for x in v),"fns":sorted({x["fn"] or "transfer" for x in v})} for k,v in sorted(src.items(),key=lambda kv:-sum(x["egld"] for x in kv[1]))[:5]]})
T["binance_depositors"]=rows
# (2) the 11,000 withdrawal
big=[t for t in txs(BIN,WIN,100,sender=BIN) if eg(t)>=5000]
w=[]
for t in big:
    r=t["receiver"];o=txs(r,t["timestamp"]-60,20,sender=r)
    w.append({"receiver":r,"egld":eg(t),"ts":t["timestamp"],"label":LM.get(r),"onward":[{"to":x["receiver"],"label":LM.get(x["receiver"]),"egld":eg(x),"fn":x.get("function"),"ts":x["timestamp"]} for x in o if eg(x)>0][:5]})
T["binance_big_withdrawals"]=w
# (3) desk outbound
desk=["erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5","erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"]
dd={}
for a in desk:
    dd[a]={"out":[{"to":t["receiver"],"label":LM.get(t["receiver"]),"egld":eg(t),"ts":t["timestamp"]} for t in txs(a,WIN,100,sender=a) if eg(t)>0],
           "in":[{"from":t["sender"],"label":LM.get(t["sender"]),"egld":eg(t),"ts":t["timestamp"]} for t in txs(a,WIN,100,receiver=a) if eg(t)>0.01]}
T["desks"]=dd
# (4) exit-route scan over big withdraws
WDL=(D.get("withdraw_decoded") or {}).get("largest") or []
ex=[]
for w_ in WDL[:6]:
    s=w_["sender"];o=txs(s,w_["timestamp"]-30,30,sender=s)
    ex.append({"sender":s,"label":LM.get(s),"provider":w_.get("identity"),"withdrawn_egld":w_["egld_returned"],"ts":w_["timestamp"],
               "next":[{"to":x["receiver"],"label":LM.get(x["receiver"]),"egld":eg(x),"fn":x.get("function"),"ts":x["timestamp"]} for x in reversed(o) if eg(x)>0 or x.get("function")][:6]})
T["exit_routes"]=ex

# (5) exit-route scan, every withdraw > 3,000 EGLD, classified next hop
MM={LM_a for LM_a,v in LM.items()}
def klass(to,fn,sender):
    lab=LM.get(to)
    cat=lab[1] if lab else None
    if cat=="exchange" or cat=="exchange_router" or cat=="router": return "cex"
    if cat=="bridge": return "bridge"
    if fn in ("delegate","stake","reDelegateRewards") or (to.startswith("erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqq") ): return "re-delegate"
    if cat=="defi" or (fn and ("swap" in fn.lower() or fn in ("ESDTTransfer","MultiESDTNFTTransfer","wrapEgld"))): return "dex/defi"
    if cat=="validator": return "re-delegate"
    return "wallet"
ALLW=[x for x in ((D.get("withdraw_decoded") or {}).get("largest") or []) if (x.get("egld_returned") or 0)>3000]
# 'largest' only keeps 15; widen from the full leg list via the follow-up decode if present
full=[x for x in (D.get("withdraw_legs_decoded_all") or []) if (x.get("egld_returned") or 0)>3000]
if full: ALLW=full
scan=[]
for w_ in ALLW:
    s_=w_["sender"]
    o=txs(s_,w_["timestamp"]-30,30,sender=s_)
    ADMIN={"withdraw","claimRewards","unDelegate","reDelegateRewards","unStake","unBond"}
    nxt=[x for x in reversed(o) if x["timestamp"]>=w_["timestamp"] and (eg(x)>0 or (x.get("function") and x.get("function") not in ADMIN))][:6]   # run #30: a zero-value withdraw/claim is the exit call itself, not a re-delegation
    info=get(f"/accounts/{s_}");time.sleep(0.3)
    bal=int(info.get("balance","0"))/1e18 if isinstance(info,dict) and "balance" in info else None
    hops=[{"to":x["receiver"],"label":(LM.get(x["receiver"]) or [None])[0],"egld":eg(x),"fn":x.get("function"),"ts":x["timestamp"],"class":klass(x["receiver"],x.get("function"),s_)} for x in nxt]
    big=[h for h in hops if h["egld"]>=0.5*w_["egld_returned"] or h["class"]=="re-delegate"]
    route=("internal" if (LM.get(s_) or [None,None])[1] in ("exchange","exchange_ops") else big[0]["class"]) if big or (LM.get(s_) or [None,None])[1] in ("exchange","exchange_ops") else ("held" if bal is not None and bal>=0.8*w_["egld_returned"] else "split/unresolved")
    scan.append({"sender":s_,"sender_label":(LM.get(s_) or [None])[0],"sender_category":(LM.get(s_) or [None,None])[1],
                 "provider":w_.get("identity") or w_.get("provider"),"withdrawn_egld":w_["egld_returned"],"ts":w_["timestamp"],
                 "balance_now":bal,"route":route,"next":hops})
T["exit_route_scan"]={"threshold_egld":3000,"calls":len(scan),"rows":scan,
    "by_route":{r:{"n":sum(1 for x in scan if x["route"]==r),"egld":sum(x["withdrawn_egld"] for x in scan if x["route"]==r)} for r in sorted({x["route"] for x in scan})}}
print("[exit-scan]",T["exit_route_scan"]["by_route"])

# (6) Binance.com daily rails since Oct 9 08:04 UTC
BREOPEN=1791532800+8*3600+4*60   # 2026-10-09 08:04 UTC
def pall(a,side,after):
    out,frm=[],0
    while frm<3000:
        b=get(f"/accounts/{a}/transactions",size=50,**{"from":frm},after=after,order="asc",status="success",**{side:a})
        time.sleep(0.4)
        if not isinstance(b,list): return out,b.get("__error__")
        out+=b
        if len(b)<50: return out,None
        frm+=50
    return out,"cap"
import datetime as _dt
days={}
bdep,e1=pall(BIN,"receiver",BREOPEN); bwd,e2=pall(BIN,"sender",BREOPEN)
for t in bdep:
    if eg(t)<1: continue
    d=_dt.datetime.utcfromtimestamp(t["timestamp"]).strftime("%Y-%m-%d"); r=days.setdefault(d,{"dep_n":0,"dep_egld":0.0,"wd_n":0,"wd_egld":0.0,"dep_senders":set(),"wd_receivers":set()})
    r["dep_n"]+=1;r["dep_egld"]+=eg(t);r["dep_senders"].add(t["sender"])
for t in bwd:
    if eg(t)<1: continue
    d=_dt.datetime.utcfromtimestamp(t["timestamp"]).strftime("%Y-%m-%d"); r=days.setdefault(d,{"dep_n":0,"dep_egld":0.0,"wd_n":0,"wd_egld":0.0,"dep_senders":set(),"wd_receivers":set()})
    r["wd_n"]+=1;r["wd_egld"]+=eg(t);r["wd_receivers"].add(t["receiver"])
T["binance_daily"]={"since_utc":"2026-10-09 08:04","errors":[e1,e2],
    "days":{d:{**{k:v for k,v in r.items() if not isinstance(v,set)},"distinct_depositors":len(r["dep_senders"]),"distinct_withdrawers":len(r["wd_receivers"])} for d,r in sorted(days.items())},
    "top_deposits_window":sorted(({"from":t["sender"],"label":(LM.get(t["sender"]) or [None])[0],"egld":eg(t),"ts":t["timestamp"]} for t in bdep if t["timestamp"]>=WIN),key=lambda x:-x["egld"])[:10],
    "top_withdrawals_window":sorted(({"to":t["receiver"],"label":(LM.get(t["receiver"]) or [None])[0],"egld":eg(t),"ts":t["timestamp"]} for t in bwd if t["timestamp"]>=WIN),key=lambda x:-x["egld"])[:10]}
print("[binance-daily]",{d:(round(v["dep_egld"]),round(v["wd_egld"])) for d,v in T["binance_daily"]["days"].items()})
FUND={"erd1hl5y4a":"erd1hl5y4ahk2a52rf4znn69a62w8skjputp7h3wxfsyyq3kykj0j2uqt7vqmy",
      "erd1hhvfrw":"erd1hhvfrwvqj5jhxqwlac9vftwgnlkv0s9y7xy7xp98vehlq74qee6srkqgdh",
      "erd1vxa2vk":"erd1vxa2vkdd945k0d6v8dscm8pwt56ueujdtzsyghh6zu4c4lf0kyjqaqkhd2",
      "erd137cw9q":"erd137cw9q46yzsx9wftk85m8x2n40yj6uzfcccqunut689thhr67nwsvnujun",
      "erd14ds7pk":"erd14ds7pkqm0aj70tjyd8yswunqgn0rfjztt82rzy983rrpyu34ygwqdjjml3"}
fr={}
for k,a in FUND.items():
    info=get(f"/accounts/{a}");time.sleep(0.3)
    o=txs(a,WIN,50,sender=a); i=txs(a,WIN,50,receiver=a)
    fr[k]={"address":a,"balance_egld":int(info.get("balance","0"))/1e18 if isinstance(info,dict) and "balance" in info else None,
           "out":[{"to":x["receiver"],"label":(LM.get(x["receiver"]) or [None])[0],"egld":eg(x),"fn":x.get("function"),"ts":x["timestamp"]} for x in o if eg(x)>=1][:10],
           "in":[{"from":x["sender"],"label":(LM.get(x["sender"]) or [None])[0],"egld":eg(x),"fn":x.get("function"),"ts":x["timestamp"]} for x in i if eg(x)>=1][:10]}
    fr[k]["to_binance_egld"]=sum(x["egld"] for x in fr[k]["out"] if x["to"] in (BIN,FUND["erd137cw9q"]))
T["binance_funders"]=fr
print("[funders]",{k:(round(v["balance_egld"] or 0),round(v["to_binance_egld"]),len(v["out"])) for k,v in fr.items()})

# (7) OTC desk terminal erd1y27r22
TERM="erd1y27r22e4svp6g985ednf0nnd383pq2tmhkkzf3g58wems07kgc5stex2ne"
info=get(f"/accounts/{TERM}");time.sleep(0.3)
o=txs(TERM,1790263800,50,sender=TERM); i=txs(TERM,1790263800,50,receiver=TERM)
T["desk_terminal"]={"address":TERM,"info":{k:info.get(k) for k in ("balance","nonce","username","timestamp","isGuarded")} if isinstance(info,dict) else info,
    "out":[{"to":x["receiver"],"label":(LM.get(x["receiver"]) or [None])[0],"egld":eg(x),"fn":x.get("function"),"ts":x["timestamp"]} for x in o][:15],
    "in":[{"from":x["sender"],"label":(LM.get(x["sender"]) or [None])[0],"egld":eg(x),"fn":x.get("function"),"ts":x["timestamp"]} for x in i][:15]}
print("[terminal]",T["desk_terminal"]["info"],len(o),len(i))

# (8) Hatom EGLD money market call history since Oct 5
MMK="erd1qqqqqqqqqqqqqpgq35qkf34a8svu4r2zmfzuztmeltqclapv78ss5jleq3"
from collections import Counter as _C
calls,err=pall(MMK,"receiver",1791158400)
fn=_C(); fn_senders={}
for t in calls:
    f_=t.get("function") or "transfer"; fn[f_]+=1; fn_senders.setdefault(f_,set()).add(t["sender"])
liq=[t for t in calls if "liquid" in (t.get("function") or "").lower()]
red=[t for t in calls if (t.get("function") or "") in ("redeem","withdraw","exitMarket","redeemUnderlying")]
T["hatom_egld_mm"]={"since_utc":"2026-10-05","calls":len(calls),"error":err,
    "by_function":{k:{"n":v,"distinct_senders":len(fn_senders[k])} for k,v in fn.most_common(15)},
    "liquidation_calls":len(liq),"redeem_calls":len(red),
    "redeem_senders_top":_C(t["sender"] for t in red).most_common(8)}
print("[hatom-mm]",T["hatom_egld_mm"]["by_function"])

D2=json.load(open(SNAP));D2["run30_traces"]=T
json.dump(D2,open(SNAP,"w"))
print(json.dumps(T,indent=1,default=str)[:9000])
