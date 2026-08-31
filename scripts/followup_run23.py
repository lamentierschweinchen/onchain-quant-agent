#!/usr/bin/env python3
"""Run #23 follow-up: repair the queries the main collector lost.

Three failure modes hit this run and ALL of them were silent:
  1. BINANCE_HOT was hardcoded in the collector with an INVALID bech32 checksum
     (erd1sdsl...gdvvz2eqra76xc). HTTP 400 -> paged_txs breaks -> empty list ->
     "0 outbound recipients >=10K", which would have resolved a pre-committed
     test on fabricated evidence. scripts/validate_addresses.py does NOT cover
     addresses hardcoded in collector scripts, only the JSON data files.
  2. HTTP 429 during the heavy pass nulled the unbond wallet's info/delegation.
  3. The wave-window hub trace returned zero txs (transient), so the wave netting
     could not be computed at all.

This script re-runs those with 429-aware backoff and REFUSES to write an empty
result without recording it as an error.
"""
import json, time, urllib.request, urllib.parse, os
from datetime import datetime, timezone

API="https://api.multiversx.com"
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-08-31"
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))

label_map,cat_map={},{}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"):
                label_map[a]=m.get("name","Unknown"); cat_map[a]=m.get("category","unknown")

def ts(y,m,d): return int(datetime(y,m,d,tzinfo=timezone.utc).timestamp())
AFTER=ts(2026,8,24); END=ts(2026,8,31)
WAVE_START=ts(2026,8,17)
THIRTY=ts(2026,8,1)

ERRORS=[]
def get(path,params=None,retries=5):
    url=API+path
    if params: url+="?"+urllib.parse.urlencode(params)
    delay=1.0
    for a in range(retries+1):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"intel-agent/23f"})
            with urllib.request.urlopen(req,timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if "429" in str(e):
                time.sleep(delay); delay=min(delay*2,12.0); continue
            if a==retries:
                ERRORS.append({"url":url,"error":str(e)}); return {"__error__":str(e),"__url__":url}
            time.sleep(1.0)
    ERRORS.append({"url":url,"error":"429 exhausted"})
    return {"__error__":"429 exhausted","__url__":url}

def paged(addr,after,before=None,direction="sender",max_pages=60,tag=""):
    out,frm=[],0
    errored=False
    for _ in range(max_pages):
        p={"size":50,"from":frm,"after":after,"order":"desc","status":"success",direction:addr}
        if before: p["before"]=before
        b=get(f"/accounts/{addr}/transactions",p)
        time.sleep(0.35)
        if isinstance(b,dict):
            errored=True; break
        if not b: break
        out.extend(b)
        if len(b)<50: break
        frm+=50
    if errored:
        ERRORS.append({"address":addr,"direction":direction,"tag":tag,"error":"query failed mid-page"})
    return out

OUT={"_window":"2026-08-24..2026-08-31"}

# ---- (1) BINANCE hot wallets - CORRECT addresses --------------------------
BINANCE_HOT_VALID=[
 "erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets",
 "erd1ylwuswz9zuk4acuq4aa6d0x9ys293yhlpwg6vpuwntndyej4u44q896zlz",
 "erd1v4ms58e22zjcp08suzqgm9ajmumwxcy4hfkdc23gvynnegjdflmsj6gmaq",
]
BINANCE_CUSTODY="erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"
UPBIT_OTC="erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
OTC_DIST="erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
DESKS={UPBIT_OTC:"UPbit OTC Desk", OTC_DIST:"OTC Distribution Wallet"}

hot={}
for a in BINANCE_HOT_VALID:
    info=get(f"/accounts/{a}"); time.sleep(0.3)
    o=paged(a,AFTER,direction="sender",max_pages=30,tag="binance_hot_out")
    i=paged(a,AFTER,direction="receiver",max_pages=30,tag="binance_hot_in")
    hot[a]={"label":label_map.get(a,"Binance.com hot"),
            "balance_egld":int(info.get("balance","0"))/1e18 if isinstance(info,dict) and "balance" in info else None,
            "out":o,"in":i}
    print(f"[hot] {a[:16]} bal={hot[a]['balance_egld']} out={len(o)} in={len(i)}")
OUT["binance_hot"]=hot

# desk inbound senders (7d + wave) for the "does the 300,000 reach the desks" test
desk_in_senders=set()
for a,rec in D["desk_inbound_paged"].items():
    for t in rec["txs"]:
        if int(t.get("value","0"))>0: desk_in_senders.add(t["sender"])

big={}
for a,h in hot.items():
    for t in h["out"]:
        v=int(t.get("value","0"))/1e18
        if v>=5000: big[t["receiver"]]=big.get(t["receiver"],0)+v
OUT["binance_hot_big_outbound"]={k:v for k,v in sorted(big.items(),key=lambda x:-x[1])}
traces={}
for r,amt in list(sorted(big.items(),key=lambda x:-x[1]))[:6]:
    info=get(f"/accounts/{r}"); time.sleep(0.3)
    o=paged(r,AFTER,direction="sender",max_pages=6,tag="hot_hop2")
    hop2={}
    for t in o:
        v=int(t.get("value","0"))/1e18
        if v>0: hop2[t["receiver"]]=hop2.get(t["receiver"],0)+v
    traces[r]={"amount":amt,"label":label_map.get(r,"Unknown"),
               "balance_egld":int(info.get("balance","0"))/1e18 if isinstance(info,dict) and "balance" in info else None,
               "nonce":info.get("nonce") if isinstance(info,dict) else None,
               "reaches_desk_directly": r in desk_in_senders,
               "hop2_to_desk": sum(v for k,v in hop2.items() if k in DESKS),
               "hop2_top":[{"to":k,"label":label_map.get(k,"Unknown"),"egld":v}
                           for k,v in sorted(hop2.items(),key=lambda x:-x[1])[:4]]}
    print(f"[hot->] {amt:,.0f} to {r[:16]} {traces[r]['label']} desk_direct={traces[r]['reaches_desk_directly']} hop2_desk={traces[r]['hop2_to_desk']:,.0f}")
OUT["binance_hot_big_traces"]=traces

# custody re-query (worked, but re-read balance cleanly)
ci=get(f"/accounts/{BINANCE_CUSTODY}"); time.sleep(0.3)
OUT["custody_balance_egld"]=int(ci.get("balance","0"))/1e18 if isinstance(ci,dict) and "balance" in ci else None
print("[custody] balance",OUT["custody_balance_egld"])

# ---- (2) THE 229,865 UNBOND ----------------------------------------------
UNBOND="erd1daqlaezxx22rzyxnqx5ddkykm5ajelt0hetjnstm7rxqg78xqusqazv9ms"
ui=get(f"/accounts/{UNBOND}"); time.sleep(0.4)
ud=get(f"/accounts/{UNBOND}/delegation"); time.sleep(0.4)
uo=paged(UNBOND,AFTER,direction="sender",max_pages=20,tag="unbond_out")
uin=paged(UNBOND,AFTER,direction="receiver",max_pages=20,tag="unbond_in")
uall=get(f"/accounts/{UNBOND}/transactions",{"size":50,"after":AFTER,"order":"desc","sender":UNBOND})
time.sleep(0.3)
OUT["unbond"]={"info":ui,"delegation":ud,"out_7d":uo,"in_7d":uin,"all_out":uall,
               "balance_egld":int(ui.get("balance","0"))/1e18 if isinstance(ui,dict) and "balance" in ui else None}
pend=[]; active=0.0
if isinstance(ud,list):
    for row in ud:
        active+=int(row.get("userActiveStake","0") or 0)/1e18
        for u in (row.get("userUndelegatedList") or []):
            pend.append({"contract":row.get("contract"),"amount_egld":int(u["amount"])/1e18,
                         "seconds":u.get("seconds")})
OUT["unbond"]["pending"]=pend
OUT["unbond"]["pending_total"]=sum(p["amount_egld"] for p in pend)
OUT["unbond"]["active_stake"]=active
print(f"[unbond] bal={OUT['unbond']['balance_egld']} pending={OUT['unbond']['pending_total']:,.0f} "
      f"active={active:,.0f} out7d={len(uo)} allout={len(uall) if isinstance(uall,list) else uall}")
for t in (uall if isinstance(uall,list) else [])[:12]:
    print("   fn",t.get("function"),int(t.get("value","0"))/1e18,"->",t.get("receiver","")[:16])

# ---- (3) MEGA WHALE / absorber re-query ----------------------------------
MEGA="erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"
mi=get(f"/accounts/{MEGA}"); time.sleep(0.3)
OUT["mega_whale"]={"balance_egld":int(mi.get("balance","0"))/1e18 if isinstance(mi,dict) and "balance" in mi else None,
  "in":paged(MEGA,AFTER,direction="receiver",max_pages=6,tag="mega_in"),
  "out":paged(MEGA,AFTER,direction="sender",max_pages=6,tag="mega_out")}
print("[mega] bal",OUT["mega_whale"]["balance_egld"],"in",len(OUT["mega_whale"]["in"]),"out",len(OUT["mega_whale"]["out"]))

# ---- (4) WAVE-WINDOW HUB TRACE (Aug 17 -> Aug 31) ------------------------
def venue_of(addr):
    l=label_map.get(addr)
    if l and cat_map.get(addr)=="exchange":
        for v in ["Binance.com","Binance","UPbit","Bybit","Gate.io","KuCoin",
                  "Coinbase","Crypto.com","MEXC","Bitget","Bitfinex","Tokero"]:
            if v.split(".")[0] in l: return v
        return l
    if l and "Whale" in l: return l
    return None

_cache={}
def resolve_hop(addr,direction,after,before=None):
    key=(addr,direction)
    if key in _cache: return _cache[key]
    v=venue_of(addr)
    if v:
        res=({v:None},"direct",None); _cache[key]=res; return res
    side="sender" if direction=="out" else "receiver"
    p={"size":30,"after":after,"order":"desc","status":"success",side:addr}
    if before: p["before"]=before
    txs=get(f"/accounts/{addr}/transactions",p); time.sleep(0.3)
    info=get(f"/accounts/{addr}"); time.sleep(0.25)
    bal=int(info.get("balance","0"))/1e18 if isinstance(info,dict) and "balance" in info else None
    agg={}
    for t in (txs if isinstance(txs,list) else []):
        val=int(t.get("value","0"))/1e18
        if val<=0: continue
        other=t["receiver"] if direction=="out" else t["sender"]
        if other in DESKS: continue
        vv=venue_of(other) or ("UNRESOLVED:"+other)
        agg[vv]=agg.get(vv,0)+val
    res=(agg,"router",bal); _cache[key]=res; return res

def attribute(block):
    per,unres={},0.0
    for addr,rec in block.items():
        amt,terms=rec["amount"],rec["terminals"]
        if rec["kind"]=="direct":
            v=venue_of(addr); per[v]=per.get(v,0)+amt; continue
        named={k:v for k,v in terms.items() if v and not k.startswith("UNRESOLVED")}
        tot=sum(named.values())
        if tot<=0: unres+=amt; continue
        for v,val in named.items(): per[v]=per.get(v,0)+amt*(val/tot)
    return per,unres

def hub_trace(ob,ib,after,before=None,min_amt=1000):
    out_dest,in_src={},{}
    for a,v in ob.items():
        for t in v["txs"]:
            val=int(t.get("value","0"))/1e18
            if val<=0 or t["receiver"] in DESKS: continue
            out_dest[t["receiver"]]=out_dest.get(t["receiver"],0)+val
    for a,v in ib.items():
        for t in v["txs"]:
            val=int(t.get("value","0"))/1e18
            if val<=0 or t["sender"] in DESKS: continue
            in_src[t["sender"]]=in_src.get(t["sender"],0)+val
    tr={"outbound":{},"inbound":{}}
    for addr,amt in sorted(out_dest.items(),key=lambda x:-x[1]):
        if amt<min_amt:
            tr["outbound"][addr]={"amount":amt,"kind":"small","terminals":{},"balance":None,
                                  "label":label_map.get(addr,"Unknown")}; continue
        agg,kind,bal=resolve_hop(addr,"out",after,before)
        tr["outbound"][addr]={"amount":amt,"kind":kind,"terminals":agg,"balance":bal,
                              "label":label_map.get(addr,"Unknown")}
    for addr,amt in sorted(in_src.items(),key=lambda x:-x[1]):
        if amt<min_amt:
            tr["inbound"][addr]={"amount":amt,"kind":"small","terminals":{},"balance":None,
                                 "label":label_map.get(addr,"Unknown")}; continue
        agg,kind,bal=resolve_hop(addr,"in",after,before)
        tr["inbound"][addr]={"amount":amt,"kind":kind,"terminals":agg,"balance":bal,
                             "label":label_map.get(addr,"Unknown")}
    ov,ou=attribute(tr["outbound"]); iv,iu=attribute(tr["inbound"])
    venues=sorted(set(list(ov)+list(iv)))
    net={v:ov.get(v,0)-iv.get(v,0) for v in venues}
    go,gi=sum(out_dest.values()),sum(in_src.values())
    circ=sum(min(ov.get(v,0),iv.get(v,0)) for v in venues)
    tr["venue_netting"]={"outbound_by_venue":ov,"inbound_by_venue":iv,"net_by_venue":net,
        "unresolved_out":ou,"unresolved_in":iu,"gross_out":go,"gross_in":gi,
        "circular":circ,"net_one_way":go-circ}
    return tr

print("\n=== WAVE #3 EXTENDED HUB TRACE (Aug 17 -> Aug 31) ===")
wob,wib={},{}
for d_addr,d_label in DESKS.items():
    o=paged(d_addr,WAVE_START,before=END,direction="sender",max_pages=120,tag="wave3ext")
    i=paged(d_addr,WAVE_START,before=END,direction="receiver",max_pages=120,tag="wave3ext")
    wob[d_addr]={"label":d_label,"txs":o}; wib[d_addr]={"label":d_label,"txs":i}
    print(f"[wave3ext] {d_label}: out={len(o)} in={len(i)}")
if sum(len(v["txs"]) for v in wob.values())==0:
    ERRORS.append({"tag":"wave3ext","error":"still zero after retry - NOT written"})
    OUT["wave3ext"]=None
else:
    OUT["wave3ext"]=hub_trace(wob,wib,WAVE_START,before=END)
    vn=OUT["wave3ext"]["venue_netting"]
    print(f"[wave3ext] gross_out={vn['gross_out']:,.0f} gross_in={vn['gross_in']:,.0f} "
          f"circ={vn['circular']:,.0f} net_one_way={vn['net_one_way']:,.0f}")
    print("  net_by_venue:",{k:round(v) for k,v in vn["net_by_venue"].items()})

# ---- (5) previous-week desk balances sanity ------------------------------
for d_addr,d_label in DESKS.items():
    info=get(f"/accounts/{d_addr}"); time.sleep(0.3)
    OUT.setdefault("desk_balances",{})[d_addr]={"label":d_label,
        "balance_egld":int(info.get("balance","0"))/1e18 if isinstance(info,dict) and "balance" in info else None}
print("[desks]",{v["label"]:round(v["balance_egld"] or 0) for v in OUT["desk_balances"].values()})

OUT["_errors"]=ERRORS
json.dump(OUT,open(f"{REPO}/data/collected/followup_{RD}.json","w"),indent=1)
print(f"\nsaved data/collected/followup_{RD}.json; errors={len(ERRORS)}")
for e in ERRORS: print("  ERR", e)
