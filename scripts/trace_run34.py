#!/usr/bin/env python3
"""Run #34 targeted traces (after collector/followup/rails). Writes D["run34_traces"].
(16) run #33 rec #5: seller chain erd1hl5y4a -> erd1079hvt0 -> erd1hhvfrw (+ one-shot hops) total EGLD to Binance.com since Oct 9.
(17) run #33 rec #4: Binance Staking custody erd1rf4hv70 outbound / delegation since Oct 22 (binance-custody-hold).
(15) run #32 rec #1/#2: one-hop trace of any withdraw leg > 1,000 EGLD out of the Binance de-staking wallet erd1r3w62vq and the ninjastaking unbond wallet erd1me5hmqt5qg (destination resolution).
(13) run #31 rec #4: ninjastaking 26,699 unbond wallet erd1me5hmqt5qg - status and any move.
(14) run #31 rec #5: USDC bridge redemption trace - USDC in/out of the xBridge Tokens Wrapper in the window, by wallet, and whether those wallets sold EGLD for USDC first.
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
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent";SNAP=f"{REPO}/data/collected/2026-10-26.json"
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
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"intel-agent/34-trace"}),timeout=40) as r: return json.loads(r.read().decode())
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
    while frm<8000:
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
calls,err=pall(MMK,"receiver",WIN)
fn=_C(); fn_senders={}
for t in calls:
    f_=t.get("function") or "transfer"; fn[f_]+=1; fn_senders.setdefault(f_,set()).add(t["sender"])
liq=[t for t in calls if "liquid" in (t.get("function") or "").lower()]
red=[t for t in calls if (t.get("function") or "") in ("redeem","withdraw","exitMarket","redeemUnderlying")]
T["hatom_egld_mm"]={"since_utc":"window start","calls":len(calls),"error":err,
    "by_function":{k:{"n":v,"distinct_senders":len(fn_senders[k])} for k,v in fn.most_common(15)},
    "liquidation_calls":len(liq),"redeem_calls":len(red),
    "redeem_senders_top":_C(t["sender"] for t in red).most_common(8)}
print("[hatom-mm]",T["hatom_egld_mm"]["by_function"])


# (9) run #30 rec #1: Binance 320,002 unbond - still pending? any move from the de-staking wallet?
DESTAKE="erd1r3w62vqmsux5e38p6vnueatmfcs8nr5lmg3s97x6rafqpgxfae0sxv9z0v"
BSTAKE="erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqc0llllsayxegu"
dl=get(f"/accounts/{DESTAKE}/delegation");time.sleep(0.3)
info=get(f"/accounts/{DESTAKE}");time.sleep(0.3)
o=txs(DESTAKE,WIN,50,sender=DESTAKE); i=txs(DESTAKE,WIN,50,receiver=DESTAKE)
T["binance_unbond"]={"wallet":DESTAKE,"balance_egld":int(info.get("balance","0"))/1e18 if isinstance(info,dict) and "balance" in info else None,
  "delegation":dl if isinstance(dl,list) else [dl],
  "out":[{"to":x["receiver"],"label":(LM.get(x["receiver"]) or [None])[0],"egld":eg(x),"fn":x.get("function"),"ts":x["timestamp"]} for x in o][:15],
  "in":[{"from":x["sender"],"label":(LM.get(x["sender"]) or [None])[0],"egld":eg(x),"fn":x.get("function"),"ts":x["timestamp"]} for x in i][:15]}
print("[binance-unbond]",T["binance_unbond"]["balance_egld"],json.dumps(T["binance_unbond"]["delegation"],default=str)[:600],len(o),len(i))
# (10) run #30 rec #3: cross-venue arbitrage wallets - in/out by venue in the window
ARB={"erd1d2anjjha":"erd1d2anjjhad4xlcrcu8jkk99yhrflsg5skavxqpkxwamxq80lmmglqzw605j",
     "erd13sytuz92":"erd13sytuz92vyz0h0l52xzw3xmuy3msulhxyzdu7h0feankdakxs9sq49uzdt",
     "erd1reh7sy2c":"erd1reh7sy2c4x53wdgtgq53lnesljgsyuwlel5tq684uemn83k0et4sn3d6lc"}
arb={}
for k,a in ARB.items():
    info=get(f"/accounts/{a}");time.sleep(0.3)
    o,eo=pall(a,"sender",WIN); i,ei=pall(a,"receiver",WIN)
    vo={};vi={}
    for x in o:
        if eg(x)>0: lab=(LM.get(x["receiver"]) or [x["receiver"][:12]])[0]; vo[lab]=vo.get(lab,0)+eg(x)
    for x in i:
        if eg(x)>0: lab=(LM.get(x["sender"]) or [x["sender"][:12]])[0]; vi[lab]=vi.get(lab,0)+eg(x)
    arb[k]={"address":a,"balance_egld":int(info.get("balance","0"))/1e18 if isinstance(info,dict) and "balance" in info else None,
            "nonce":info.get("nonce") if isinstance(info,dict) else None,"errors":[eo,ei],
            "out_by_counterparty":dict(sorted(vo.items(),key=lambda kv:-kv[1])),"in_by_counterparty":dict(sorted(vi.items(),key=lambda kv:-kv[1])),
            "out_egld":sum(vo.values()),"in_egld":sum(vi.values()),"n_out":sum(1 for x in o if eg(x)>0),"n_in":sum(1 for x in i if eg(x)>0)}
T["arb_wallets"]=arb
print("[arb]",{k:(round(v["in_egld"]),round(v["out_egld"]),v["n_in"],v["n_out"]) for k,v in arb.items()})
# (11) run #30 rec #4: Coinbase routing wallet + Whale B + Mega Whale legs in window
CBR={"cb_routing":"erd1lgdltequh7627rtlacmcp6p5vec7zmu2rxhu7pjwvcja8f4a9gqq9vcc70",
     "whale_b":"erd1at3jm3xvzxhdgt4f695l7l2f6r0tpkqjnemfpc0raam5e9xtjuqqs6fkul",
     "mega":"erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"}
cb={}
for k,a in CBR.items():
    info=get(f"/accounts/{a}");time.sleep(0.3)
    o=txs(a,WIN,50,sender=a); i=txs(a,WIN,50,receiver=a)
    cb[k]={"address":a,"balance_egld":int(info.get("balance","0"))/1e18 if isinstance(info,dict) and "balance" in info else None,
           "out":[{"to":x["receiver"],"label":(LM.get(x["receiver"]) or [None])[0],"egld":eg(x),"fn":x.get("function"),"ts":x["timestamp"]} for x in o if eg(x)>=1][:15],
           "in":[{"from":x["sender"],"label":(LM.get(x["sender"]) or [None])[0],"egld":eg(x),"fn":x.get("function"),"ts":x["timestamp"]} for x in i if eg(x)>=1][:15]}
T["coinbase_legs"]=cb
print("[cb-legs]",{k:(round(v["balance_egld"] or 0),len(v["in"]),len(v["out"]),round(sum(x["egld"] for x in v["in"])),round(sum(x["egld"] for x in v["out"]))) for k,v in cb.items()})
# (12) run #30 rec #2: distinct UPbit depositors since restart 2
UP="erd1fcxu3f0hlxyvnp7zvuqmf34zf5w782tst6vuqhm4dwq4ayjspdaqce0q49"
ui,eu=pall(UP,"receiver",1790263800); uo,eo2=pall(UP,"sender",1790263800)
uv=[x for x in ui if eg(x)>0]; uwo=[x for x in uo if eg(x)>0]
T["upbit_depositors"]={"since_utc":"2026-09-24 15:30","errors":[eu,eo2],"deposits":len(uv),"deposit_egld":sum(eg(x) for x in uv),
  "distinct_depositors":len({x["sender"] for x in uv}),"distinct_depositors_in_window":len({x["sender"] for x in uv if x["timestamp"]>=WIN}),
  "withdrawals":len(uwo),"withdrawal_egld":sum(eg(x) for x in uwo),
  "deposits_list":[{"from":x["sender"],"label":(LM.get(x["sender"]) or [None])[0],"egld":eg(x),"ts":x["timestamp"]} for x in uv][-20:]}
print("[upbit]",{k:v for k,v in T["upbit_depositors"].items() if k!="deposits_list"})

# (13) run #31 rec #4: ninjastaking unbond wallet
NINJ="erd1me5hmqt5qg9r9jgw9r936444va6f4qw4uf0y2sgk0hsfhmtwvhnscdu9us"
dl=get(f"/accounts/{NINJ}/delegation");time.sleep(0.3)
info=get(f"/accounts/{NINJ}");time.sleep(0.3)
o=txs(NINJ,WIN-86400*4,50,sender=NINJ); i=txs(NINJ,WIN-86400*4,50,receiver=NINJ)
T["ninjastaking_unbond"]={"wallet":NINJ,"balance_egld":int(info.get("balance","0"))/1e18 if isinstance(info,dict) and "balance" in info else None,
  "delegation":dl if isinstance(dl,list) else [dl],
  "out":[{"to":x["receiver"],"label":(LM.get(x["receiver"]) or [None])[0],"egld":eg(x),"fn":x.get("function"),"ts":x["timestamp"]} for x in o][:15],
  "in":[{"from":x["sender"],"label":(LM.get(x["sender"]) or [None])[0],"egld":eg(x),"fn":x.get("function"),"ts":x["timestamp"]} for x in i][:15]}
print("[ninja-unbond]",T["ninjastaking_unbond"]["balance_egld"],json.dumps(T["ninjastaking_unbond"]["delegation"],default=str)[:600])
# (14) run #31 rec #5: USDC through the xBridge Tokens Wrapper
WRAP="erd1qqqqqqqqqqqqqpgq305jfaqrdxpzjgf9y5gvzh60mergh866yfkqzqjv2h"
def tpaged(**q):
    out,frm=[],0
    while frm<1000:
        b=get("/transfers",size=50,**{"from":frm},token="USDC-c76f1f",after=WIN,**q);time.sleep(0.4)
        if not isinstance(b,list): return out,b.get("__error__")
        out+=b
        if len(b)<50: return out,None
        frm+=50
    return out,"cap"
def usdc_amt(t):
    tot=0
    for a in (t.get("action") or {}).get("arguments",{}).get("transfers",[]) or []:
        if a.get("token")=="USDC-c76f1f" or a.get("identifier")=="USDC-c76f1f": tot+=int(a.get("value","0"))/1e6
    return tot
uin,e_in=tpaged(receiver=WRAP); uout,e_out=tpaged(sender=WRAP)
def agg(rows,side):
    m={}
    for t in rows:
        w=t[side]; m.setdefault(w,{"usdc":0.0,"n":0}); m[w]["usdc"]+=usdc_amt(t); m[w]["n"]+=1
    return dict(sorted(m.items(),key=lambda kv:-kv[1]["usdc"]))
uin_by=agg(uin,"sender"); uout_by=agg(uout,"receiver")
dest={}
for t in uin:
    fa=((t.get("action") or {}).get("arguments") or {}).get("functionArgs") or []
    try: tk=bytes.fromhex(fa[0]).decode()
    except Exception: tk="?"
    dest[tk]=dest.get(tk,0)+usdc_amt(t)
# did the top unwrappers sell EGLD for USDC in the 7 days before? (swap calls with value>0 to a DEX pair)
sellers={}
for w,v in list(uin_by.items())[:6]:
    o=txs(w,WIN-86400*7,50,sender=w)
    sw=[x for x in o if eg(x)>0 and (x.get("function") or "").lower().startswith("swap")]
    ins=txs(w,WIN-86400*7,50,receiver=w)
    cex=[x for x in ins if (LM.get(x["sender"]) or [None,None])[1] in ("exchange",)]
    sellers[w]={"label":(LM.get(w) or [None])[0],"usdc_unwrapped":v["usdc"],"egld_swapped_7d":sum(eg(x) for x in sw),"swap_calls_7d":len(sw),
                "cex_inbound_7d_txs":len(cex)}
T["usdc_bridge"]={"wrapper":WRAP,"errors":[e_in,e_out],"unwrap_txs":len(uin),"unwrap_usdc":sum(v["usdc"] for v in uin_by.values()),
  "unwrap_by_destination_token":dest,"wrap_txs":len(uout),"wrap_usdc":sum(v["usdc"] for v in uout_by.values()),
  "top_unwrappers":dict(list(uin_by.items())[:8]),"top_wrappers":dict(list(uout_by.items())[:8]),"unwrapper_egld_sales":sellers}
print("[usdc-bridge]",{k:v for k,v in T["usdc_bridge"].items() if k in ("errors","unwrap_txs","unwrap_usdc","wrap_txs","wrap_usdc")})

# (15) run #32 rec #1/#2: one hop past the unbond wallets
hop={}
for k,w in (("binance_unbond",DESTAKE),("ninjastaking_unbond",NINJ)):
    legs=[x for x in T[k]["out"] if x["egld"]>=1000]
    rows=[]
    for x in legs:
        o2=txs(x["to"],x["ts"]-30,30,sender=x["to"])
        info2=get(f"/accounts/{x['to']}");time.sleep(0.3)
        rows.append({**x,"to_category":(LM.get(x["to"]) or [None,None])[1],
                     "to_balance_egld":int(info2.get("balance","0"))/1e18 if isinstance(info2,dict) and "balance" in info2 else None,
                     "onward":[{"to":y["receiver"],"label":(LM.get(y["receiver"]) or [None])[0],"category":(LM.get(y["receiver"]) or [None,None])[1],"egld":eg(y),"fn":y.get("function"),"ts":y["timestamp"]} for y in reversed(o2) if y["timestamp"]>=x["ts"] and eg(y)>0][:8]})
    hop[k]={"legs_ge_1000":len(legs),"rows":rows}
T["unbond_destinations"]=hop
print("[unbond-dest]",json.dumps({k:[(r["egld"],r["label"],[(o["label"],round(o["egld"])) for o in r["onward"]]) for r in v["rows"]] for k,v in hop.items()},default=str)[:1500])

# (16) run #33 rec #5: seller chain as one entity, EGLD routed to Binance.com since the Oct 9 reopening
SELLER={"erd1hl5y4a":"erd1hl5y4ahk2a52rf4znn69a62w8skjputp7h3wxfsyyq3kykj0j2uqt7vqmy",
        "erd1079hvt0":"erd1079hvt0a2tha0jr6gykh5ft7nuvgrlt07c6tkuzm8zkyyc66v72qgt9u6p",
        "erd1hhvfrw":"erd1hhvfrwvqj5jhxqwlac9vftwgnlkv0s9y7xy7xp98vehlq74qee6srkqgdh",
        "erd1rgm4td29":"erd1rgm4td296wxwxnepwets5wnwsea7jy5u4lw4xt2sa535khgsjcdqfag6j4",
        "erd1rcty49":"erd1rcty49rmvv6z80exv2l4pj2cgnnyqkjs639ss2cz0r5nkr8s4rnqfu5v0n"}
SADDR=set(SELLER.values())
sc={}
for k,a in SELLER.items():
    info=get(f"/accounts/{a}");time.sleep(0.3)
    o,eo=pall(a,"sender",BREOPEN)
    vo=[x for x in o if eg(x)>0]
    to_bin=sum(eg(x) for x in vo if x["receiver"]==BIN)
    to_chain=sum(eg(x) for x in vo if x["receiver"] in SADDR)
    hops={}
    for x in vo:
        r_=x["receiver"]
        if r_ in SADDR or r_==BIN: continue
        hops[r_]=hops.get(r_,0)+eg(x)
    sc[k]={"address":a,"balance_egld":int(info.get("balance","0"))/1e18 if isinstance(info,dict) and "balance" in info else None,
           "nonce":info.get("nonce") if isinstance(info,dict) else None,"error":eo,"out_txs":len(vo),"out_egld":sum(eg(x) for x in vo),
           "to_binance_egld":to_bin,"to_chain_egld":to_chain,
           "to_binance_in_window_egld":sum(eg(x) for x in vo if x["receiver"]==BIN and x["timestamp"]>=WIN),
           "other_destinations":dict(sorted(hops.items(),key=lambda kv:-kv[1])[:10])}
# fresh one-shot hops that received from erd1hhvfrw in the window and then paid Binance
newhops=[]
for r_,v in sc["erd1hhvfrw"]["other_destinations"].items():
    if v<1000: continue
    o2=txs(r_,BREOPEN,30,sender=r_); info2=get(f"/accounts/{r_}");time.sleep(0.3)
    newhops.append({"address":r_,"label":(LM.get(r_) or [None])[0],"received_egld":v,"nonce":info2.get("nonce") if isinstance(info2,dict) else None,
                    "to_binance_egld":sum(eg(x) for x in o2 if x["receiver"]==BIN),
                    "onward":[{"to":x["receiver"],"label":(LM.get(x["receiver"]) or [None])[0],"egld":eg(x),"ts":x["timestamp"]} for x in o2 if eg(x)>0][:6]})
T["seller_chain"]={"since_utc":"2026-10-09 08:04","wallets":sc,"other_hops_from_hhvfrw":newhops,
    "total_to_binance_egld":sum(v["to_binance_egld"] for v in sc.values())+sum(h["to_binance_egld"] for h in newhops if h["address"] not in SADDR)}
print("[seller-chain]",{k:(round(v["balance_egld"] or 0),round(v["to_binance_egld"]),round(v["to_binance_in_window_egld"])) for k,v in sc.items()},round(T["seller_chain"]["total_to_binance_egld"]))

# (17) run #33 rec #4: Binance Staking custody since the 320,000 return
CUSTW="erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"
CSINCE=1792660000   # 2026-10-22 ~09:06 UTC, just before the custody receipt
info=get(f"/accounts/{CUSTW}");time.sleep(0.3)
co,ce=pall(CUSTW,"sender",CSINCE); ci,ce2=pall(CUSTW,"receiver",CSINCE)
T["binance_custody"]={"address":CUSTW,"balance_egld":int(info.get("balance","0"))/1e18 if isinstance(info,dict) and "balance" in info else None,
   "errors":[ce,ce2],
   "out":[{"to":x["receiver"],"label":(LM.get(x["receiver"]) or [None])[0],"egld":eg(x),"fn":x.get("function"),"ts":x["timestamp"]} for x in co if eg(x)>0 or x.get("function")][:30],
   "in":[{"from":x["sender"],"label":(LM.get(x["sender"]) or [None])[0],"egld":eg(x),"fn":x.get("function"),"ts":x["timestamp"]} for x in ci if eg(x)>0][:30],
   "out_to_hot_egld":sum(eg(x) for x in co if x["receiver"]==BIN),"delegated_egld":sum(eg(x) for x in co if x.get("function") in ("delegate","stake")),
   "out_total_egld":sum(eg(x) for x in co)}
print("[custody]",T["binance_custody"]["balance_egld"],T["binance_custody"]["out_total_egld"],T["binance_custody"]["out_to_hot_egld"],T["binance_custody"]["delegated_egld"])

D2=json.load(open(SNAP));D2["run34_traces"]=T
json.dump(D2,open(SNAP,"w"))
print(json.dumps(T,indent=1,default=str)[:9000])
