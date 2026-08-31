#!/usr/bin/env python3
"""Run #23 stage 1: compute every derived quantity -> /tmp/run23w/derived.json"""
import json, os, math
from datetime import datetime, timezone

REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
OUT="/tmp/run23w"; os.makedirs(OUT, exist_ok=True)
RD="2026-08-31"
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
learn=json.load(open(f"{REPO}/data/learnings.json"))
beh=json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))

label_map,cat_map={},{}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"):
                label_map[a]=m.get("name","Unknown"); cat_map[a]=m.get("category","unknown")
def lab(a): return label_map.get(a,"Unknown")
def cat(a): return cat_map.get(a,"unknown")

O={}
econ=D["economics"]; st=D["stats"]; pecon=prev["economics"]; pact=prev["activity"]
price=econ["price"]; staked=econ["staked"]; circ=econ["circulatingSupply"]
pp=pecon["egld_price_usd"]; be=D["btc_eth"]
O["macro"]={"price":price,"prev_price":pp,"price_chg":100*(price-pp)/pp,
    "btc":be["bitcoin"]["usd"],"eth":be["ethereum"]["usd"],
    "btc_wow":100*(be["bitcoin"]["usd"]-pecon["btc_price_usd"])/pecon["btc_price_usd"],
    "eth_wow":100*(be["ethereum"]["usd"]-pecon["eth_price_usd"])/pecon["eth_price_usd"],
    "staked":staked,"staked_prev":pecon["staked_egld"],"staked_chg":staked-pecon["staked_egld"],
    "sr":staked/circ,"sr_prev":pecon["staked_ratio"]}

acc=D["accounts"]
def bal_of(a):
    x=acc.get(a)
    if x and isinstance(x.get("info"),dict) and "balance" in x["info"]:
        try: return int(x["info"]["balance"])/1e18
        except: return None
    return None

UPBIT_DESK="erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
DIST_DESK="erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
DESK_SET={UPBIT_DESK,DIST_DESK}

vn=D["otc_hub_trace"]["venue_netting"]
desk_bal=(bal_of(UPBIT_DESK) or 0)+(bal_of(DIST_DESK) or 0)
prev_desk=55362.50898512902+54494.86347169873   # run #22 desk balances
upbit_feed=0.0
for a,rec in D["desk_inbound_paged"].items():
    for t in rec["txs"]:
        s=t.get("sender")
        if cat(s)=="exchange" and "UPbit" in lab(s) and "OTC" not in lab(s):
            upbit_feed+=int(t.get("value","0"))/1e18
# every exchange feeding the desks directly this week
feed_by_venue={}
for a,rec in D["desk_inbound_paged"].items():
    for t in rec["txs"]:
        s=t.get("sender"); v=int(t.get("value","0"))/1e18
        if v<=0 or s in DESK_SET: continue
        if cat(s)=="exchange":
            feed_by_venue[lab(s)]=feed_by_venue.get(lab(s),0)+v

wave=D["otc_hub_trace_wave3ext"]["venue_netting"]
prev_nets=prev["otc_net_one_way_series"]
sum_wave_weekly=prev_nets["run22"]+vn["net_one_way"]

O["otc"]={
 "gross_out":vn["gross_out"],"gross_in":vn["gross_in"],"circular":vn["circular"],
 "net_one_way":vn["net_one_way"],
 "circ_pct":100*vn["circular"]/vn["gross_out"] if vn["gross_out"] else 0,
 "desk_bal":desk_bal,"prev_desk":prev_desk,"desk_delta":desk_bal-prev_desk,
 "upbit_feed":upbit_feed,"prev_upbit_feed":297000.0,"feed_by_venue":feed_by_venue,
 "net_by_venue":vn["net_by_venue"],"out_by_venue":vn["outbound_by_venue"],
 "in_by_venue":vn["inbound_by_venue"],
 "unresolved_out":vn["unresolved_out"],"unresolved_in":vn["unresolved_in"],
 "wave":{"window":"2026-08-17..2026-08-31","gross_out":wave["gross_out"],
   "gross_in":wave["gross_in"],"circular":wave["circular"],
   "circ_pct":100*wave["circular"]/wave["gross_out"] if wave["gross_out"] else 0,
   "net_one_way":wave["net_one_way"],"sum_weekly":sum_wave_weekly,
   "overstate_egld":sum_wave_weekly-wave["net_one_way"],
   "overstate_pct":100*(sum_wave_weekly-wave["net_one_way"])/wave["net_one_way"] if wave["net_one_way"] else 0,
   "net_by_venue":wave["net_by_venue"],"out_by_venue":wave["outbound_by_venue"],
   "in_by_venue":wave["inbound_by_venue"]},
}

# ---------- exchange flows -------------------------------------------------
cur_top={x["address"]:int(x["balance"])/1e18 for x in D["top_accounts"]}
prev_top={x["address"]:x["balance_egld"] for x in prev["top_accounts"]}
def ent(a):
    l=lab(a)
    if "Binance" in l: return "Binance"
    if "Coinbase" in l: return "Coinbase"
    if "Crypto.com" in l: return "Crypto.com"
    for e2 in ["UPbit","Bybit","MEXC","Bitget","Gate.io","KuCoin","Bitfinex","Tokero"]:
        if e2 in l: return e2
    return None
BAD={"erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp29trp6qsl2gdvvz2eqra76xc",
     "erd1ty4pvmjtl3mnsjvnsxqkm3xqm4dm7ppgz9sh4nk4tqvlmw0jyggqzn4mdc"}
exch=[a for a,c in cat_map.items() if c=="exchange"]
per_wallet=[]; ec,ep,ew={},{},{}; noprior=[]
for a in exch:
    if a in BAD or a in DESK_SET: continue
    e2=ent(a)
    if not e2: continue
    cur=bal_of(a); cur=cur if cur is not None else cur_top.get(a)
    p=prev_top.get(a)
    if cur is None: continue
    if p is None: noprior.append({"entity":e2,"label":lab(a),"balance":cur}); continue
    per_wallet.append({"exchange":lab(a),"address":a,"entity":e2,"current":cur,"previous":p,
                       "change_egld":cur-p,"pct":100*(cur-p)/p if p else 0.0})
    ec[e2]=ec.get(e2,0)+cur; ep[e2]=ep.get(e2,0)+p; ew[e2]=ew.get(e2,0)+1
per_wallet.sort(key=lambda x:-abs(x["change_egld"]))
entity=[{"entity":k,"wallets_count":ew[k],"current":ec[k],"previous":ep[k],
         "net_flow_egld":ec[k]-ep[k],"pct":100*(ec[k]-ep[k])/ep[k] if ep[k] else 0.0}
        for k in ec]
entity.sort(key=lambda x:-abs(x["net_flow_egld"]))
O["exch"]={"per_wallet":per_wallet,"entity":entity,"noprior":noprior,
  "total_cur":sum(ec.values()),"total_prev":sum(ep.values()),
  "net":sum(ec.values())-sum(ep.values())}

# ---------- Binance custody + the 300,000 follow-through -------------------
BC="erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"
BH="erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets"
cust_out=[{"to":t["receiver"],"label":lab(t["receiver"]),"egld":int(t.get("value","0"))/1e18,
           "ts":t.get("timestamp")} for t in (D.get("binance_custody_out") or [])
          if int(t.get("value","0"))>0]
cust_in=[{"from":t["sender"],"label":lab(t["sender"]),"egld":int(t.get("value","0"))/1e18,
          "ts":t.get("timestamp")} for t in (D.get("binance_custody_in") or [])
         if int(t.get("value","0"))>0]
# does the Binance hot outflow reach the desks / their feeders?
desk_in_senders=set()
for a,rec in D["desk_inbound_paged"].items():
    for t in rec["txs"]:
        if int(t.get("value","0"))>0: desk_in_senders.add(t["sender"])
wave_in_senders=set()
for a,rec in D["desk_inbound_wave3ext"].items():
    for t in rec["txs"]:
        if int(t.get("value","0"))>0: wave_in_senders.add(t["sender"])
hot_big=[]
for r,amt in sorted((D.get("binance_hot_big_outbound") or {}).items(), key=lambda x:-x[1]):
    tr=(D.get("binance_hot_big_traces") or {}).get(r,{})
    hop2={}
    for t in (tr.get("out") or []):
        v=int(t.get("value","0"))/1e18
        if v>0: hop2[t["receiver"]]=hop2.get(t["receiver"],0)+v
    hot_big.append({"receiver":r,"label":lab(r),"amount":amt,
        "receiver_balance":int((tr.get("info") or {}).get("balance","0"))/1e18
            if isinstance(tr.get("info"),dict) and "balance" in tr["info"] else None,
        "reaches_desk_directly": r in desk_in_senders or r in wave_in_senders,
        "hop2_to_desk": sum(v for k,v in hop2.items() if k in DESK_SET),
        "hop2_top":[{"to":k,"label":lab(k),"egld":v} for k,v in sorted(hop2.items(),key=lambda x:-x[1])[:3]]})
O["custody"]={"balance":bal_of(BC),"previous":prev["exchange_balances"]["Binance Staking"],
  "delta":(bal_of(BC) or 0)-prev["exchange_balances"]["Binance Staking"],
  "out":cust_out,"in":cust_in,
  "hot_balance":bal_of(BH),"hot_previous":prev_top.get(BH),
  "hot_entity_balance":sum((bal_of(a) or 0) for a in
      ["erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets",
       "erd1ylwuswz9zuk4acuq4aa6d0x9ys293yhlpwg6vpuwntndyej4u44q896zlz",
       "erd1v4ms58e22zjcp08suzqgm9ajmumwxcy4hfkdc23gvynnegjdflmsj6gmaq"]),
  "hot_entity_previous":prev["exchange_balances"]["Binance.com"],
  "hot_big_outbound":hot_big,
  "hot_to_desk_total":sum(h["amount"] for h in hot_big if h["reaches_desk_directly"])
                     +sum(h["hop2_to_desk"] for h in hot_big)}

# ---------- demand instruments --------------------------------------------
MEGA="erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"
CBR="erd1lgdltequh7627rtlacmcp6p5vec7zmu2rxhu7pjwvcja8f4a9gqq9vcc70"
mega_bal=bal_of(MEGA); mega_prev=prev_top.get(MEGA) or 1099059.3223354353
mp=D["mex_pairs"]
dexvol=sum((p.get("volume24h") or 0) for p in mp)
pooltvl=sum((p.get("totalValue") or 0) for p in mp)
turn=100*dexvol/pooltvl if pooltvl else 0
# rec #6: EGLD-denominated volume + WEGLD/USDC split out
pairs_sorted=sorted(mp,key=lambda p:-(p.get("volume24h") or 0))
def pname(p): return f"{p.get('baseSymbol')}/{p.get('quoteSymbol')}"
wegld_usdc=next((p for p in mp if pname(p) in ("WEGLD/USDC","USDC/WEGLD")),None)
wu_vol=(wegld_usdc or {}).get("volume24h") or 0
O["bid"]={"mega_bal":mega_bal,"mega_prev":mega_prev,"mega_delta":(mega_bal or 0)-mega_prev,
  "mega_txs":len(D.get("mega_whale_inbound") or [])+len(D.get("mega_whale_outbound") or []),
  "cbr_bal":bal_of(CBR),"absorbed":max(0.0,(mega_bal or 0)-mega_prev),
  "turnover":turn,"prev_turnover":prev["xexchange"]["turnover_ratio_pct"],
  "dexvol":dexvol,"prev_dexvol":prev["xexchange"]["volume_24h_usd"],
  "pooltvl":pooltvl,"prev_pooltvl":prev["xexchange"]["pool_tvl_usd"],
  # rec #6 - price-independent framings
  "dexvol_egld":dexvol/price,"prev_dexvol_egld":prev["xexchange"]["volume_24h_usd"]/pp,
  "pooltvl_egld":pooltvl/price,"prev_pooltvl_egld":prev["xexchange"]["pool_tvl_usd"]/pp,
  "wegld_usdc_vol":wu_vol,"wegld_usdc_share":100*wu_vol/dexvol if dexvol else 0,
  "ex_wegld_usdc_vol":dexvol-wu_vol,
  "ex_wegld_usdc_vol_egld":(dexvol-wu_vol)/price}

# rec #8 - dynamic absorbers
absorbers=D.get("dynamic_absorbers") or []
O["absorbers"]={"scanned":len(absorbers),
  "retaining":[a for a in absorbers if a.get("is_absorber")],
  "total_received":sum(a["received_from_desks"] for a in absorbers),
  "total_retained":sum(a["retained_egld"] for a in absorbers),
  "rows":sorted(absorbers,key=lambda x:-x["received_from_desks"])[:12]}

# withdrawal breadth
hub=D["otc_hub_trace"]; PIPE=set(hub["inbound"])|set(hub["outbound"])
for w in ("wave3ext","wave2ext","julywave","run16","run18","peak_run17"):
    h=D.get(f"otc_hub_trace_{w}")
    if h: PIPE|=set(h["inbound"])|set(h["outbound"])
ROUTERS=set(kn.get("exchange_routers",{}).keys())
raw={}; expipe={}
for a,rec in (D.get("exchange_outbound_paged") or {}).items():
    for t in rec["txs"]:
        v=int(t.get("value","0"))/1e18; r=t.get("receiver")
        if v<1000 or cat(r)=="exchange": continue
        raw[r]=raw.get(r,0)+v
        if r not in PIPE and r not in DESK_SET and r not in ROUTERS:
            expipe[r]=expipe.get(r,0)+v
pagecaps=[p for p in (D.get("_pagecap_terminations") or []) if p.get("tag")=="breadth"]
O["breadth"]={"raw_n":len(raw),"raw_egld":sum(raw.values()),
  "ex_n":len(expipe),"ex_egld":sum(expipe.values()),
  "pipeline_share":100*(1-sum(expipe.values())/sum(raw.values())) if raw else 0,
  "pagecap_hits":pagecaps,
  "top":[{"address":a,"label":lab(a),"egld":v} for a,v in sorted(expipe.items(),key=lambda x:-x[1])[:6]]}

# ---------- staking --------------------------------------------------------
provs=[p for p in D["providers"] if float(p.get("locked",0) or 0)>0]
for p in provs: p["_lk"]=float(p["locked"])/1e18
provs.sort(key=lambda p:-p["_lk"])
tl=sum(p["_lk"] for p in provs)
pkey={p["provider"]:p for p in prev["staking_providers"]}
def pk(p): return p.get("identity") or p["provider"]
shares=[p["_lk"]/tl for p in provs]
hhi=sum(s*s for s in shares)
cur_users=sum(int(p.get("numUsers",0) or 0) for p in provs)
prev_users=sum(p["num_delegators"] for p in prev["staking_providers"])
gain=loss=0; moves=[]
for p in provs:
    k=pk(p)
    if k in pkey:
        d=p["_lk"]-pkey[k]["locked_egld"]
        du=int(p.get("numUsers",0) or 0)-(pkey[k]["num_delegators"] or 0)
        moves.append({"identity":k,"delta":d,"users_delta":du,"apr":p.get("apr"),
                      "fee":(p.get("serviceFee") or 0)*100,"locked":p["_lk"],
                      "users":p.get("numUsers"),"nodes":p.get("numNodes"),
                      "prev_locked":pkey[k]["locked_egld"]})
        if du>0: gain+=1
        elif du<0: loss+=1
moves.sort(key=lambda m:-abs(m["delta"]))
buckets=[]; covered=0
for lb,lo,hi in [("5-6%",5,6),("6-7%",6,7),("7-8%",7,8),("8-9%",8,9),("9-10%",9,10),("10%+",10,999)]:
    sel=[p for p in provs if lo<=(p.get("apr") or 0)<hi]
    lk=sum(p["_lk"] for p in sel); covered+=lk
    buckets.append({"label":lb,"min_apr_pct":lo,"max_apr_pct":(hi if hi<999 else 99),
                    "provider_count":len(sel),"total_locked_egld":lk})
zeros=[p for p in provs if (p.get("apr") or 0)<5]
residual=(staked-pecon["staked_egld"])-(tl-prev["staking_concentration"]["total_locked_egld"])

# deregistered set (locked==0 with nodes>0)
dereg=D.get("deregistered_providers") or []
dereg_users_now=sum(int(x["users"] or 0) for x in dereg)
# providers that were in the prior locked>0 set and are now zero-locked
new_dereg=[x for x in dereg if (x.get("prev_locked") or 0)>0]
p2p=next((x for x in dereg if x["key"]=="p2p_org_"), None)

pool=D.get("unbonding_pool") or []
pool_rows=[]
for r in pool:
    for pu in r["pending_unbonding"]:
        pool_rows.append({"wallet":r["wallet"],"amount_egld":pu["amount_egld"],
                          "contract":pu["contract"],"days_remaining":pu["days_remaining"],
                          "wallet_balance_egld":r["balance_egld"]})
pool_rows.sort(key=lambda x:-x["amount_egld"])
claimable_now=sum(x["amount_egld"] for x in pool_rows if (x["days_remaining"] or 0)<=0.01)

O["staking"]={"provs":provs,"total_locked":tl,
  "prev_total_locked":prev["staking_concentration"]["total_locked_egld"],
  "delta_locked":tl-prev["staking_concentration"]["total_locked_egld"],
  "hhi":hhi,"prev_hhi":prev["staking_concentration"]["hhi"],
  "top5":sum(shares[:5])*100,"top10":sum(shares[:10])*100,
  "users":cur_users,"prev_users":prev_users,"users_delta":cur_users-prev_users,
  "gaining":gain,"losing":loss,"moves":moves,"buckets":buckets,
  "coverage_pct":100*covered/tl,
  "zero_apr_n":len(zeros),"zero_apr_locked":sum(p["_lk"] for p in zeros),
  "residual":residual,
  "dereg":dereg,"new_dereg":new_dereg,"dereg_users_now":dereg_users_now,"p2p":p2p,
  "undelegated_week":D.get("undelegated_this_week_total_egld") or 0,
  "undelegate_callers":D.get("undelegate_callers_count") or 0,
  "pool_total":D.get("unbonding_pool_total_egld") or 0,
  "pool":pool[:14],"pool_rows":pool_rows,"claimable_now":claimable_now,
  "providers_scanned":D.get("provider_scan_count"),
  "join_match_rate":D.get("_provider_join_match_rate"),
  "movers":D.get("provider_movers") or [],
  "apr_min":min([p.get("apr") or 0 for p in provs if (p.get("apr") or 0)>0] or [0]),
  "apr_max":max([p.get("apr") or 0 for p in provs] or [0]),
  "apr_wavg":sum((p.get("apr") or 0)*p["_lk"] for p in provs)/tl if tl else 0}

# p2p caller experiment (rec #4)
pc_=D.get("p2p_callers") or {}
O["p2p"]={"function_counts":pc_.get("function_counts",{}),
  "distinct_callers":pc_.get("distinct_callers",0),
  "tx_count":pc_.get("tx_count",0),
  "users_now":(D.get("p2p_provider") or {}).get("numUsers"),
  "users_prev":pkey.get("p2p_org_",{}).get("num_delegators"),
  "owner":D.get("p2p_owner"),
  "locked":float((D.get("p2p_provider") or {}).get("locked",0) or 0)/1e18,
  "nodes":(D.get("p2p_provider") or {}).get("numNodes")}

# unbond wallet resolution (rec #3)
ubw=D.get("unbond_wallet_delegation")
ub_pending=[]; ub_active=0.0
if isinstance(ubw,list):
    for row in ubw:
        ub_active+=int(row.get("userActiveStake","0") or 0)/1e18
        for u in (row.get("userUndelegatedList") or []):
            ub_pending.append({"contract":row.get("contract"),
                               "amount_egld":int(u["amount"])/1e18,
                               "seconds_remaining":u.get("seconds"),
                               "days_remaining":round((u.get("seconds") or 0)/86400,2)})
ub_out=[{"to":t["receiver"],"label":lab(t["receiver"]),"egld":int(t.get("value","0"))/1e18,
         "ts":t.get("timestamp")} for t in (D.get("unbond_wallet_out_7d") or [])
        if int(t.get("value","0"))>0]
ub_fns={}
for t in (D.get("unbond_wallet_all_out") or []):
    if isinstance(t,dict):
        fn=t.get("function") or "(transfer)"
        ub_fns[fn]=ub_fns.get(fn,0)+1
O["unbond"]={"wallet":"erd1daqlaezxx22rzyxnqx5ddkykm5ajelt0hetjnstm7rxqg78xqusqazv9ms",
  "balance":int((D.get("unbond_wallet_info") or {}).get("balance","0"))/1e18
      if isinstance(D.get("unbond_wallet_info"),dict) and "balance" in D["unbond_wallet_info"] else None,
  "prev_balance":2369.526068877824,
  "pending":ub_pending,"pending_total":sum(x["amount_egld"] for x in ub_pending),
  "active_stake":ub_active,"outbound":ub_out,
  "outbound_total":sum(x["egld"] for x in ub_out),
  "functions":ub_fns,
  "targets":D.get("unbond_wallet_targets") or {},
  "target_traces":{k:{"label":lab(k),"amount":v["amount"],
      "balance":int((v.get("info") or {}).get("balance","0"))/1e18
          if isinstance(v.get("info"),dict) and "balance" in v["info"] else None,
      "onward":[{"to":t["receiver"],"label":lab(t["receiver"]),
                 "egld":int(t.get("value","0"))/1e18}
                for t in (v.get("out") or []) if int(t.get("value","0"))>0][:5]}
    for k,v in (D.get("unbond_target_traces") or {}).items()}}

# reward behaviour
ag=beh["aggregates"]
O["reward"]=ag

# ---------- tokens ---------------------------------------------------------
tt=D["tvl_tokens"]; prevls=prev["lsd_supply"]
def sup(t):
    x=tt.get(t) or {}
    try: return float(x.get("supply") or 0)
    except: return 0.0
def mc(t):
    x=tt.get(t)
    return (x.get("marketCap") or 0) if isinstance(x,dict) else 0
lsd={}
for t in ["SEGLD-3ad2d0","XEGLD-e413ed","SWTAO-356a25","USH-111e09"]:
    c=sup(t); p=float(prevls.get(t) or 0)
    lsd[t]={"supply":c,"prev":p,"pct":100*(c-p)/p if p else 0,"mcap":mc(t),
            "price":(tt.get(t) or {}).get("price"),
            "price_source":(tt.get(t) or {}).get("_price_source")}
stab={}
prev_stable={"USDC-c76f1f":None,"USDT-f8c08c":None}
try:
    _p22=json.load(open(f"{REPO}/data/collected/2026-08-24.json"))
    for sid in prev_stable:
        prev_stable[sid]=float((_p22.get("stable_"+sid) or {}).get("supply") or 0)
except Exception:
    pass
for sid in ["USDC-c76f1f","USDT-f8c08c"]:
    c=D.get("stable_"+sid) or {}
    cs=float(c.get("supply") or 0)
    ps=prev_stable.get(sid) or 0
    stab[sid]={"supply":cs,"prev":ps,"pct":100*(cs-ps)/ps if ps else 0,
               "price":c.get("price"),"mcap":c.get("marketCap"),"accounts":c.get("accounts")}
mex_prev_supply=0.0
try:
    mex_prev_supply=float((_p22.get("mex_token") or {}).get("supply") or 0)
except Exception:
    pass
O["tokens"]={"lsd":lsd,"stable":stab,
  "wegld_supply":float((D["wegld_token"] or {}).get("supply") or 0),
  "mex_supply":float((D["mex_token"] or {}).get("supply") or 0),
  "mex_prev_supply":mex_prev_supply,
  "dataapi":D["dataapi_refetch_log"],"newly":D["newly_issued"]}

# xexchange
mexp=D["mex_economics"]["price"]; pmex=prev["xexchange"]["mex_price_usd"]
mexpair=next((p for p in (D.get("mex_pairs_wide") or mp)
              if p.get("baseSymbol")=="MEX" and p.get("quoteSymbol")=="WEGLD"),None)
prev_mexdepth=prev["xexchange"].get("mex_pair_depth",{})
mex_depth_usd=(mexpair or {}).get("totalValue") or 0
mex_depth_egld=mex_depth_usd/price
prev_mex_depth_egld=(prev_mexdepth.get("tvl_usd") or 0)/pp
O["xexchange"]={"pairs":D["mex_economics"]["marketPairs"],"vol":dexvol,
  "prev_vol":prev["xexchange"]["volume_24h_usd"],
  "mex_price":mexp,"prev_mex_price":pmex,"mex_wow":100*(mexp-pmex)/pmex,
  "mex_mcap":D["mex_economics"]["marketCap"],
  "top_pairs":[{"name":f"{p.get('baseName')}/{p.get('quoteName')}",
    "volume_24h_usd":p.get("volume24h") or 0,"tvl_usd":p.get("totalValue") or 0,
    "trades_count_24h":p.get("tradesCount24h") or p.get("trades24h") or 0,
    "is_other":False,"share_pct":100*(p.get("volume24h") or 0)/dexvol if dexvol else 0}
    for p in pairs_sorted[:5]],
  "pool_tvl":pooltvl,"prev_pool_tvl":prev["xexchange"]["pool_tvl_usd"],
  "turnover":turn,"prev_turnover":prev["xexchange"]["turnover_ratio_pct"],
  "mex_pair_depth":{"pair":"MEX/WEGLD","tvl_usd":mex_depth_usd,
    "tvl_egld":mex_depth_egld,"previous_tvl_egld":prev_mex_depth_egld,
    "tvl_egld_wow_pct":100*(mex_depth_egld-prev_mex_depth_egld)/prev_mex_depth_egld
        if prev_mex_depth_egld else None,
    "volume_24h_usd":(mexpair or {}).get("volume24h") or 0,
    "trades_24h":(mexpair or {}).get("tradesCount24h") or 0,
    "share_of_pool_tvl_pct":100*mex_depth_usd/pooltvl if pooltvl else 0,
    "depth_rank":sorted(mp,key=lambda p:-(p.get("totalValue") or 0)).index(mexpair)+1
        if mexpair in mp else None}}

# ---------- defi -----------------------------------------------------------
HL=["HUSDC-d80042","HEGLD-d61095","HUSDT-6f0914","HWBTC-49ca31","HWETH-b3d17e",
    "HBUSD-ac1fca","HHTM-e03ba5","HMEX-df6df7","HUTK-4fa4b2","HWTAO-2e9136"]
hl=sum(mc(t) for t in HL)
we=sum(int(x["balance"])/1e18 for x in D["wegld"].values() if isinstance(x,dict) and "balance" in x)
prev_hl_egld=prev["defi_tvl"]["Hatom Lending"]/pp
hl_egld=hl/price
O["defi"]={"hatom_lending_usd":hl,"hatom_lending_egld":hl_egld,
  "hatom_lending_prev_usd":prev["defi_tvl"]["Hatom Lending"],
  "hatom_lending_prev_egld":prev_hl_egld,
  "hatom_lending_egld_pct":100*(hl_egld-prev_hl_egld)/prev_hl_egld,
  "hatom_lsd_usd":mc("SEGLD-3ad2d0")+mc("SWTAO-356a25"),
  "hatom_lsd_prev_usd":prev["defi_tvl"]["Hatom Liquid Staking"],
  "ush_usd":mc("USH-111e09"),"ush_prev_usd":prev["defi_tvl"]["Hatom USH"],
  "xoxno_usd":mc("XEGLD-e413ed"),"xoxno_prev_usd":prev["defi_tvl"]["XOXNO LSD"],
  "xexch_usd":we*price,"xexch_egld":we,"xexch_prev_usd":prev["defi_tvl"]["xExchange (USD)"],
  "proto":{k:(v["transfers_24h"].get("count") if isinstance(v["transfers_24h"],dict) else v["transfers_24h"])
           for k,v in D["proto"].items()},
  "inverse_ratio":abs(100*(hl_egld-prev_hl_egld)/prev_hl_egld)/abs(O["macro"]["price_chg"])
      if O["macro"]["price_chg"] else None,
  "evaluable":abs(O["macro"]["price_chg"])>=5.0}

# ---------- whale tiers (common-address basis) -----------------------------
SYS="erd1qqqqqqqqqqqqq"
common=[a for a in cur_top if a in prev_top and not a.startswith(SYS) and cat(a)!="system"]
def tier(v):
    if v>1_000_000: return "mega"
    if v>=100_000: return "large"
    if v>=10_000: return "mid"
def buck(pairs_):
    o={"mega":[0,0.0],"large":[0,0.0],"mid":[0,0.0]}
    for a,v in pairs_:
        t=tier(v)
        if t: o[t][0]+=1; o[t][1]+=v
    return o
cb=buck([(a,cur_top[a]) for a in common]); pb=buck([(a,prev_top[a]) for a in common])
O["tiers"]={t:{"count_current":cb[t][0],"count_previous":pb[t][0],
   "total_balance_egld":cb[t][1],"previous_total_balance_egld":pb[t][1],
   "net_change_egld":cb[t][1]-pb[t][1],
   "net_change_pct":100*(cb[t][1]-pb[t][1])/pb[t][1] if pb[t][1] else 0}
   for t in ("mega","large","mid")}
O["tiers_basis"]=len(common)
crossers=[]
for a in common:
    if tier(cur_top[a])!=tier(prev_top[a]):
        crossers.append({"address":a,"label":lab(a),"prev":prev_top[a],"cur":cur_top[a],
                         "from":tier(prev_top[a]),"to":tier(cur_top[a])})
O["tier_crossers"]=crossers

wc=[]
for a,v in sorted(cur_top.items(),key=lambda kv:-kv[1])[:len(prev_top)]:
    if a in prev_top and cat(a)!="system":
        d=v-prev_top[a]
        if abs(d)>2000:
            wc.append({"address":a,"label":lab(a),"category":cat(a),
                       "tier":(tier(v)+"_whale") if tier(v) else None,
                       "balance_current_egld":v,"balance_previous_egld":prev_top[a],
                       "change_egld":d,"change_pct":100*d/prev_top[a] if prev_top[a] else 0})
wc.sort(key=lambda x:-abs(x["change_egld"]))
O["wallet_changes"]=wc[:20]

seen=set(); rows=[]
for a,rec in D["accounts"].items():
    for t in (rec.get("txs") if isinstance(rec.get("txs"),list) else []):
        v=int(t.get("value","0"))/1e18
        if v>=1000 and t.get("txHash") not in seen:
            seen.add(t["txHash"]); rows.append((v,t))
rows.sort(key=lambda x:-x[0])
def flow(t):
    s,r=t["sender"],t["receiver"]
    sc,rc=cat(s),cat(r)
    if sc=="exchange" and rc=="exchange": return "exchange_to_exchange"
    if rc=="exchange": return "exchange_inflow"
    if sc=="exchange": return "exchange_outflow"
    if rc=="defi": return "defi_deposit"
    if sc=="defi": return "defi_withdrawal"
    if rc=="validator" or (r or "").startswith("erd1qqqqqqqqqqqqqqqpqqq"): return "staking"
    if sc=="validator": return "unstaking"
    if sc!="unknown" or rc!="unknown": return "whale_to_whale"
    return "unknown"
O["large_txs"]=[{"hash":t["txHash"],
  "timestamp":datetime.fromtimestamp(t["timestamp"],tz=timezone.utc).isoformat().replace("+00:00","Z"),
  "sender":t["sender"],"sender_label":lab(t["sender"]),
  "receiver":t["receiver"],"receiver_label":lab(t["receiver"]),
  "value_egld":v,"value_usd":v*price,"flow_type":flow(t)} for v,t in rows[:25]]
O["large_txs_count"]=len(rows)

# ---------- z-scores -------------------------------------------------------
rb=learn["runs"][-1]["running_baselines"]
def z(metric,cur_v):
    arr=rb.get(metric) or []
    if len(arr)<4: return {"method":"percent_threshold","n":len(arr)}
    mean=sum(arr)/len(arr)
    sd=math.sqrt(sum((x-mean)**2 for x in arr)/len(arr))
    if sd==0: return {"method":"rule_based","n":len(arr),"note":"degenerate stddev"}
    zz=(cur_v-mean)/sd
    sev="low" if abs(zz)<2 else ("medium" if abs(zz)<3 else ("high" if abs(zz)<4 else "critical"))
    return {"method":"z_score","n":len(arr),"mean":mean,"stddev":sd,"z":zz,"severity":sev}
O["z"]={
 "price":z("egld_price_usd",price),
 "dexvol":z("dex_volume_24h_usd",dexvol),
 "staked":z("staked_egld",staked),
 "mex":z("mex_price_usd",mexp),
 "delegators":z("total_delegators",cur_users),
 "exflow":z("exchange_net_flow_egld",O["exch"]["net"]),
 "otc":z("otc_pipeline_throughput_egld_7d",vn["gross_out"]),
 "otc_net":z("otc_net_one_way_egld_7d",vn["net_one_way"]),
 "turnover":z("dex_turnover_ratio_pct",turn),
 "compound":z("reward_compound_pct",ag["compound_vs_claim_at_function_level"]["compound_pct_of_reward_decisions"]),
 "custody":z("binance_staking_custody_egld",O["custody"]["balance"]),
 "sr":z("staked_ratio",staked/circ),
}
O["baselines"]=rb
json.dump(O,open(f"{OUT}/derived.json","w"),indent=1,default=str)
print("derived written")
print("price_chg",round(O["macro"]["price_chg"],2),
      "| gross",round(O["otc"]["gross_out"]),
      "| net_one_way",round(O["otc"]["net_one_way"]),
      "| circ%",round(O["otc"]["circ_pct"],1),
      "| desk",round(O["otc"]["desk_bal"]),"delta",round(O["otc"]["desk_delta"]))
print("upbit_feed",round(upbit_feed),"feed_by_venue",{k:round(v) for k,v in feed_by_venue.items()})
print("exch net",round(O["exch"]["net"]),"| custody",round(O["custody"]["delta"]))
print("turnover",round(turn,2),"prev",round(O["bid"]["prev_turnover"],2))
print("delegation",round(O["staking"]["delta_locked"]),"users",O["staking"]["users_delta"],
      "| undelegated",round(O["staking"]["undelegated_week"]),
      "callers",O["staking"]["undelegate_callers"])
print("z:",json.dumps({k:(round(v.get("z",0),2) if "z" in v else v.get("method")) for k,v in O["z"].items()}))
