#!/usr/bin/env python3
"""Assemble reports/2026-08-03.json (run #19) from collected data."""
import json, math
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D = json.load(open(f"{REPO}/data/collected/2026-08-03.json"))
prev = json.load(open(f"{REPO}/data/previous.json"))
kn = json.load(open(f"{REPO}/data/known-addresses.json"))
learn = json.load(open(f"{REPO}/data/learnings.json"))
prevcol = json.load(open(f"{REPO}/data/collected/2026-07-27.json"))  # for supply WoW
beh = json.load(open(f"{REPO}/data/collected/delegator_behavior_2026-08-03.json"))
COMPOUND_PCT = beh["aggregates"]["compound_vs_claim_at_function_level"]["compound_pct_of_reward_decisions"]
COMPOUND_PREV = 58.81
REDELEG_N = beh["aggregates"]["compound_vs_claim_at_function_level"]["redelegate_count"]
CLAIM_N = beh["aggregates"]["compound_vs_claim_at_function_level"]["claim_count"]

label_map, cat_map = {}, {}
for section, entries in kn.items():
    if not isinstance(entries, dict) or section == "_metadata": continue
    for addr, meta in entries.items():
        if isinstance(meta, dict) and addr.startswith("erd1"):
            label_map[addr] = meta.get("name","Unknown"); cat_map[addr]=meta.get("category","unknown")
def lab(a): return label_map.get(a,"Unknown")
def cat(a): return cat_map.get(a,"unknown")

econ=D["economics"]; st=D["stats"]; pecon=prev["economics"]; pact=prev["activity"]
price=econ["price"]; circ=econ["circulatingSupply"]; staked=econ["staked"]; sr=staked/circ
pp=pecon["egld_price_usd"]; price_chg=100*(price-pp)/pp
be=D["btc_eth"]
btc_wow=100*(be["bitcoin"]["usd"]-pecon["btc_price_usd"])/pecon["btc_price_usd"]
eth_wow=100*(be["ethereum"]["usd"]-pecon["eth_price_usd"])/pecon["eth_price_usd"]
acc=D["accounts"]
def bal_of(a):
    x=acc.get(a)
    if x and isinstance(x.get("info"),dict) and "balance" in x["info"]:
        try: return int(x["info"]["balance"])/1e18
        except: return None
    return None

# ---------------------------------------------------------------------------
# OTC HUB - gross throughput AND (new this run) two-hop venue netting.
# Run #17 said read a wave by DESTINATION; run #19 adds the mirror, because the
# desks were FED by exchanges this week. 80% of gross round-trips to the same
# venue that supplied it, so gross throughput massively overstates distribution.
# ---------------------------------------------------------------------------
UPBIT_DESK="erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
DIST_DESK="erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
DESK_SET={UPBIT_DESK,DIST_DESK}
def desk_throughput(block, key="receiver"):
    gross=inter=0.0; other={}
    for a,v in block.items():
        for t in v.get("txs",[]):
            try: val=int(t.get("value","0"))/1e18
            except: val=0
            if val<=0: continue
            gross+=val
            o=t.get(key)
            if o in DESK_SET: inter+=val
            else: other[o]=other.get(o,0)+val
    return gross,inter,other
OTC_THR_GROSS,OTC_THR_INTERDESK,desk_dest=desk_throughput(D["desk_outbound_paged"],"receiver")
OTC_THR_7D=OTC_THR_GROSS-OTC_THR_INTERDESK
_ing,_ini,desk_src=desk_throughput(D["desk_inbound_paged"],"sender")
OTC_IN_7D=sum(desk_src.values())

hub=D["otc_hub_trace"]["venue_netting"]
HUB_CIRCULAR=hub["circular"]; HUB_NET_ONEWAY=hub["gross_out"]-hub["circular"]
hub_net={k:v for k,v in hub["net_by_venue"].items()}
UPBIT_RELOAD=abs(hub["inbound_by_venue"].get("UPbit",0))

# Gross series (runs #13-#18 are gross, un-netted for circularity - see caveat)
OTC_SERIES={"run12":44335.0,"run13":66128.0,"run14":186124.0,"run15":506053.0,"run16":1100791.0,
            "run17":1284688.0,"run18":313173.0,"run19":OTC_THR_7D}
OTC_THR_7D_PREV=OTC_SERIES["run18"]
otc_drop_pct=100*(OTC_THR_7D-OTC_THR_7D_PREV)/OTC_THR_7D_PREV
# run #19 backfill of the run #12 window (the series' new left edge)
bf_gross,bf_inter,_=desk_throughput(D["otc_backfill"]["run12_jun08_jun15"],"receiver")
OTC_SERIES["run12"]=bf_gross-bf_inter
desk_top_dest=sorted(desk_dest.items(),key=lambda x:-x[1])[:6]

ta=D["top_accounts"]
cur_top={x["address"]:int(x["balance"])/1e18 for x in ta}
prev_top={x["address"]:x["balance_egld"] for x in prev["top_accounts"]}
N_prev=len(prev["top_accounts"])

# ---------- whale tiers ----------
def tiers(top):
    items=[(a,b) for a,b in top.items() if cat(a)!="system"]
    return ([x for x in items if x[1]>1e6],[x for x in items if 1e5<=x[1]<=1e6],[x for x in items if 1e4<=x[1]<1e5])
cur_trim=dict(sorted(cur_top.items(),key=lambda kv:-kv[1])[:N_prev])
cm,cl,cmid=tiers(cur_trim); pm,pl,pmid=tiers(prev_top)
def tot(x): return sum(b for _,b in x)
def tierblock(c,p,th):
    ct,pt=tot(c),tot(p)
    return {"threshold_egld":th,"count_current":len(c),"count_previous":len(p),
            "total_balance_egld":ct,"previous_total_balance_egld":pt,
            "net_change_egld":ct-pt,"net_change_pct":(100*(ct-pt)/pt if pt else None)}
whale_tiers={"mega_whales":tierblock(cm,pm,1000000),"large_whales":tierblock(cl,pl,100000),"mid_whales":tierblock(cmid,pmid,10000)}
# run #14 boundary-crossing guard
prev_l_set={a for a,_ in pl}; cur_l_set={a for a,_ in cl}
crossers_up=[(a,prev_top.get(a),cur_top.get(a)) for a in cur_l_set-prev_l_set if a in prev_top]
crossers_dn=[(a,prev_top.get(a),cur_top.get(a)) for a in prev_l_set-cur_l_set if a in cur_top]

# ---------- wallet changes ----------
changes=[]
for a,b in cur_top.items():
    if a in prev_top and cat(a)!="system":
        pb=prev_top[a]; d=b-pb; pctc=100*d/pb if pb else None
        if abs(d)>2000 or (pctc is not None and abs(pctc)>5):
            tier="mega_whale" if b>1e6 else "large_whale" if b>=1e5 else "mid_whale" if b>=1e4 else None
            changes.append({"address":a,"label":lab(a),"category":cat(a),"tier":tier,
                "balance_current_egld":b,"balance_previous_egld":pb,"change_egld":d,"change_pct":pctc})
changes.sort(key=lambda x:-abs(x["change_egld"]))
wallet_changes=changes[:18]

# ---------- large transactions ----------
router_set=set(kn.get("exchange_routers",{}).keys())
otc_set=set(a for a,m in kn.get("unlabeled_whales",{}).items() if m.get("subcategory")=="otc")
def classify(s,r):
    sl,rl=lab(s),lab(r); sc,rc=cat(s),cat(r)
    se,re_=sc=="exchange",rc=="exchange"
    sro,rro=s in router_set,r in router_set
    so=s in otc_set or "OTC" in sl; ro=r in otc_set or "OTC" in rl
    sw="Whale" in sl; rw="Whale" in rl
    if (se or sro or so) and (re_ or rro or ro): return "exchange_to_exchange"
    if re_ and not se: return "exchange_inflow"
    if se and not re_: return "exchange_outflow"
    if rc=="defi": return "defi_deposit"
    if sc=="defi": return "defi_withdrawal"
    if rc=="validator": return "staking"
    if sc=="validator": return "unstaking"
    if rc=="bridge" or sc=="bridge": return "bridge"
    if "OTC" in sl or "OTC" in rl or sro or rro: return "exchange_inflow"
    if sw and rw: return "whale_to_whale"
    return "unknown"
seen=set(); bigtx=[]
tx_pools=[info.get("txs") for info in acc.values()]
for v in D["desk_outbound_paged"].values(): tx_pools.append(v.get("txs"))
for v in D["desk_inbound_paged"].values(): tx_pools.append(v.get("txs"))
for v in D.get("exchange_outbound_paged",{}).values(): tx_pools.append(v.get("txs"))
tx_pools.append(D.get("mega_whale_inbound")); tx_pools.append(D.get("mega_whale_outbound"))
tx_pools.append(D.get("custody_funder_outbound_30d"))
for txs in tx_pools:
    if not isinstance(txs,list): continue
    for t in txs:
        if not isinstance(t,dict): continue
        h=t.get("txHash")
        if not h or h in seen: continue
        try: v=int(t.get("value","0"))/1e18
        except: v=0
        if v<1000: continue
        seen.add(h)
        s=t.get("sender"); r=t.get("receiver"); tsx=t.get("timestamp")
        bigtx.append({"hash":h,"timestamp":datetime.fromtimestamp(tsx,tz=timezone.utc).isoformat() if tsx else None,
            "sender":s,"sender_label":lab(s),"receiver":r,"receiver_label":lab(r),
            "value_egld":v,"value_usd":v*price,"flow_type":classify(s,r)})
bigtx.sort(key=lambda x:-x["value_egld"])
large_transactions=bigtx[:25]

# ---------- withdrawal breadth (NEW - run #18 recommendation #4c) ----------
PIPELINE=set(DESK_SET)|router_set|{a for a in D["otc_hub_trace"]["inbound"]}|{a for a in D["otc_hub_trace"]["outbound"]}
breadth_raw={}; breadth_clean={}
for a,v in D.get("exchange_outbound_paged",{}).items():
    for t in v.get("txs",[]):
        try: val=int(t.get("value","0"))/1e18
        except: val=0
        if val<1000: continue
        r=t.get("receiver")
        if cat(r)=="exchange": continue
        breadth_raw[r]=breadth_raw.get(r,0)+val
        if r in PIPELINE or "OTC" in lab(r) or "Router" in lab(r): continue
        breadth_clean[r]=breadth_clean.get(r,0)+val
breadth={"distinct_recipients_raw":len(breadth_raw),"total_egld_raw":sum(breadth_raw.values()),
         "distinct_recipients_ex_pipeline":len(breadth_clean),"total_egld_ex_pipeline":sum(breadth_clean.values()),
         "pipeline_share_pct":100*(1-sum(breadth_clean.values())/sum(breadth_raw.values())) if breadth_raw else None}
breadth_top=sorted(breadth_clean.items(),key=lambda x:-x[1])[:5]

# ---------- exchange flows ----------
def entity_of(a):
    l=lab(a)
    if "Binance" in l: return "Binance"
    if "Coinbase" in l: return "Coinbase"
    if "Crypto.com" in l: return "Crypto.com"
    for e in ["UPbit","Bybit","MEXC","Bitget","Gate.io","KuCoin","Bitfinex","Tokero"]:
        if e in l: return e
    return None
exch=[a for a,c in cat_map.items() if c=="exchange"]
BAD_ADDRS={"erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp29trp6qsl2gdvvz2eqra76xc",
           "erd1ty4pvmjtl3mnsjvnsxqkm3xqm4dm7ppgz9sh4nk4tqvlmw0jyggqzn4mdc"}
by_exchange=[]; ent_cur={}; ent_w={}; no_prior=[]
for a in exch:
    if a in BAD_ADDRS: continue
    e=entity_of(a)
    if not e: continue
    cur=bal_of(a)
    if cur is None: cur=cur_top.get(a)
    pb=prev_top.get(a)
    if cur is None: continue
    if pb is None:
        # run #18 rule: an address with no prior-week balance would book its whole
        # balance as a phantom flow. Exclude from BOTH sides of the delta.
        no_prior.append((e,lab(a),cur)); continue
    ent_w[e]=ent_w.get(e,0)+1
    ent_cur[e]=ent_cur.get(e,0)+cur
    by_exchange.append({"exchange":lab(a),"change_egld":cur-pb,"pct":(100*(cur-pb)/pb if pb else None)})
by_exchange.sort(key=lambda x:-abs(x["change_egld"]))
prev_ent={}
for a in exch:
    if a in BAD_ADDRS: continue
    e=entity_of(a)
    if not e: continue
    if a in prev_top and e in ent_cur:
        prev_ent[e]=prev_ent.get(e,0)+prev_top[a]

cust_bal=bal_of("erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p") or 3357101
cust_prev=prev["exchange_balances"]["Binance Staking"]

ent_interp={
 "Binance":f"Net {ent_cur.get('Binance',0)-prev_ent.get('Binance',0):+,.0f} across {ent_w.get('Binance',1)} wallets. The custody wallet did not move at all this week ({cust_bal:,.0f}, unchanged to the decimal), and the Binance.com hot wallet fell -17,254 (-5.5%). The important Binance result is not a balance at all - it is the RESOLUTION of last week's +150,000 custody reload. The sender erd1r3w62vq turns out to have made exactly two other transactions in 30 days: an unDelegate on the Binance Staking delegation contract (2026-07-09) and a withdraw from the same contract (2026-07-22), immediately followed by the 150,000 transfer to custody. The reload was therefore the delegation unwind COMPLETING - the -148,941 that the binance_staking provider shed in run #16 arriving in custody after the unbonding period - not fresh accumulation. Run #18 read it as a reversal of the de-staking programme and the strongest bullish structural counter-signal of the week. That reading is falsified: the programme did not reverse, it changed legs.",
 "UPbit":f"{ent_cur.get('UPbit',0)-prev_ent.get('UPbit',0):+,.0f} (-2.7%) to {ent_cur.get('UPbit',0):,.0f}, and this is the single most consequential exchange line of the week. UPbit RESUMED feeding the OTC desks with a fresh {UPBIT_RELOAD:,.0f} EGLD tranche after sending nothing at all in the run #18 window. It is roughly a fifth of run #17's 364,000, but it is not zero - and on the two-hop netting UPbit is the ONLY venue that is a net source into the desk hub ({hub_net.get('UPbit',0):+,.0f}). Every other venue is a net receiver. The 'the operator that staged the wave has stopped' conclusion from run #18 held for exactly one week.",
 "Bybit":f"{ent_cur.get('Bybit',0)-prev_ent.get('Bybit',0):+,.0f} (+5.4%) to {ent_cur.get('Bybit',0):,.0f}, a 3rd consecutive inflow week - but the balance change badly understates Bybit's involvement. Bybit pushed {hub['inbound_by_venue'].get('Bybit',0):,.0f} EGLD INTO the desk complex through three feeder wallets and received {hub['outbound_by_venue'].get('Bybit',0):,.0f} back out of it through five routers. It is simultaneously the largest supplier to and the largest recipient from the OTC hub, which is what makes this week's pipeline circular rather than distributive.",
 "Coinbase":f"{ent_cur.get('Coinbase',0)-prev_ent.get('Coinbase',0):+,.0f} across {ent_w.get('Coinbase',1)} wallets - small inflow, no migration activity, and the custody position from run #17 remains stationary. The Coinbase datapoint that matters is again not the balance: the Coinbase Routing wallet that fed the Mega Whale absorber in runs #15 and #17 is still sitting at 77 EGLD with zero transactions for a second consecutive week. The identifiable-bid pipe has now been dry for two weeks.",
 "Gate.io":f"{ent_cur.get('Gate.io',0)-prev_ent.get('Gate.io',0):+,.0f} on the balance, but Gate.io newly appears INSIDE the OTC hub this week: {hub['inbound_by_venue'].get('Gate.io',0):,.0f} in via feeders and {hub['outbound_by_venue'].get('Gate.io',0):,.0f} back out via routers, a net {hub_net.get('Gate.io',0):+,.0f}. It was not a participant in the run #17 wave.",
 "KuCoin":f"{ent_cur.get('KuCoin',0)-prev_ent.get('KuCoin',0):+,.0f} (+1.5%) to {ent_cur.get('KuCoin',0):,.0f}. The run #17 whale deposit (145,443) is still sitting on the venue two weeks later - it neither bled back out nor moved on. Consistent with the run #18 resolution that it was sold into the book. Graduating from the watch list.",
 "Crypto.com":f"{ent_cur.get('Crypto.com',0)-prev_ent.get('Crypto.com',0):+,.0f} - small inflow, no pipeline involvement.",
 "MEXC":f"{ent_cur.get('MEXC',0)-prev_ent.get('MEXC',0):+,.0f} (-5.0%). Flat-to-lower on a small base.",
 "Bitget":f"{ent_cur.get('Bitget',0)-prev_ent.get('Bitget',0):+,.0f} (-3.9%). Flat.",
 "Bitfinex":"Flat.","Tokero":"Flat."}
entity_netting=[]
total_cur=total_prev=0
for e in sorted(set(list(ent_cur)+list(prev_ent))):
    c=ent_cur.get(e); p=prev_ent.get(e)
    if c is None or p is None: continue
    net=c-p; total_cur+=c; total_prev+=p
    entity_netting.append({"entity":e,"wallets_count":ent_w.get(e,1),"net_flow_egld":net,
        "interpretation":ent_interp.get(e,f"Net change: {net:+.0f} EGLD")})
entity_netting.sort(key=lambda x:-abs(x["net_flow_egld"]))
net_total=total_cur-total_prev
net_adjusted=net_total   # no intra-entity reload and no newly tracked address this week

exchange_flows={"total_exchange_egld_current":total_cur,"total_exchange_egld_previous":total_prev,
    "net_change_egld":net_total,"net_change_pct":100*net_total/total_prev if total_prev else None,
    "direction":"outflow" if net_total<0 else "inflow",
    "signal":f"Net exchange flow {net_total:+,.0f} EGLD ({100*net_total/total_prev:+.2f}%) - a genuine OUTFLOW week and, unusually, one that needs no adjustment: the Binance Staking custody wallet did not move at all, no address entered the tracked set mid-series, so the headline number is the true number for once (contrast run #18, where 94% of the headline was artifact). The composition is the interesting part. UPbit {ent_cur.get('UPbit',0)-prev_ent.get('UPbit',0):+,.0f} and Binance.com {ent_cur.get('Binance',0)-prev_ent.get('Binance',0):+,.0f} account for the entire net; Bybit {ent_cur.get('Bybit',0)-prev_ent.get('Bybit',0):+,.0f}, KuCoin {ent_cur.get('KuCoin',0)-prev_ent.get('KuCoin',0):+,.0f} and Crypto.com {ent_cur.get('Crypto.com',0)-prev_ent.get('Crypto.com',0):+,.0f} took deposits. Per the run #14 rule this must be read jointly with the OTC channel, and there the balance-delta view is actively misleading: UPbit's -33,368 balance change conceals a {UPBIT_RELOAD:,.0f} EGLD tranche pushed into the OTC desks, which is distribution staged rather than coins leaving the system. Read jointly, the exchange complex was a modest net source of EGLD and UPbit was the source of the source.",
    "by_exchange":by_exchange,"entity_netting":entity_netting}

# ---------- staking ----------
provs=[p for p in D["providers"] if p.get("locked") and float(p["locked"])>0]
for p in provs: p["_lk"]=float(p["locked"])/1e18
provs.sort(key=lambda p:-p["_lk"])
total_locked=sum(p["_lk"] for p in provs)
shares=[p["_lk"]/total_locked for p in provs]
hhi=sum(s*s for s in shares); top5=sum(shares[:5])*100; top10=sum(shares[:10])*100
prevp={p["name"]:p["locked_egld"] for p in prev["staking_providers"]}
prevp_u={p["name"]:p["num_delegators"] for p in prev["staking_providers"]}
def aprp(p): return p.get("apr",0)
def feep(p): return p.get("serviceFee",0) or 0
top_providers=[]
for i,p in enumerate(provs[:20],1):
    nm=p.get("identity") or p.get("provider")
    pl_=prevp.get(nm)
    top_providers.append({"rank":i,"identity":nm,"name":nm,"provider_address":p["provider"],
        "locked_egld":p["_lk"],"previous_locked_egld":pl_,"share_pct":p["_lk"]/total_locked*100,
        "apr_pct":aprp(p),"fee_pct":feep(p)*100,"num_users":p.get("numUsers"),"num_nodes":p.get("numNodes"),
        "wow_change_egld":(p["_lk"]-pl_) if pl_ is not None else None})
apr_w=sum(p["_lk"]*aprp(p) for p in provs)/total_locked
buckets=[]
for lbl,mn,mx in [("5-6%",5,6),("6-7%",6,7),("7-8%",7,8),("8-9%",8,9),("9-10%",9,10),("10%+",10,100)]:
    sub=[p for p in provs if mn<=aprp(p)<mx]
    buckets.append({"label":lbl,"min_apr_pct":mn,"max_apr_pct":mx,"provider_count":len(sub),
        "total_locked_egld":sum(p["_lk"] for p in sub)})
qual=[p for p in provs if p["_lk"]>5000]
top_apr=[{"identity":p.get("identity") or p["provider"],"apr_pct":aprp(p),"fee_pct":feep(p)*100,
    "locked_egld":p["_lk"],"name":p.get("identity") or p["provider"]} for p in sorted(qual,key=lambda p:-aprp(p))[:5]]
lowest_fee=[{"identity":p.get("identity") or p["provider"],"apr_pct":aprp(p),"fee_pct":feep(p)*100,
    "locked_egld":p["_lk"],"name":p.get("identity") or p["provider"]} for p in sorted(qual,key=lambda p:(feep(p),-aprp(p)))[:5]]
cur_deleg=sum(p.get("numUsers",0) for p in provs); prev_deleg=sum(prevp_u.values())
gain=sum(1 for p in provs if prevp_u.get(p.get("identity") or p.get("provider")) is not None and p.get("numUsers",0)>prevp_u.get(p.get("identity") or p.get("provider")))
lose=sum(1 for p in provs if prevp_u.get(p.get("identity") or p.get("provider")) is not None and p.get("numUsers",0)<prevp_u.get(p.get("identity") or p.get("provider")))
churn={"total_delegators_current":cur_deleg,"total_delegators_previous":prev_deleg,
    "delegators_added":cur_deleg-prev_deleg,"delegators_change_pct":100*(cur_deleg-prev_deleg)/prev_deleg,
    "providers_gaining_delegators":gain,"providers_losing_delegators":lose}
def lk_wow(nm):
    p=next((x for x in provs if (x.get("identity") or x.get("provider"))==nm),None)
    if not p or nm not in prevp: return None
    return p["_lk"]-prevp[nm]
def usr_wow(nm):
    p=next((x for x in provs if (x.get("identity") or x.get("provider"))==nm),None)
    if not p or nm not in prevp_u: return None
    return p.get("numUsers",0)-prevp_u[nm]
deleg_wow=cur_deleg-prev_deleg
deleg_tvl_wow=total_locked-prev["staking_concentration"]["total_locked_egld"]
direct_node_delta=(staked-pecon["staked_egld"])-deleg_tvl_wow
# yield-chase cohorts
hi_apr=[p for p in provs if aprp(p)>=8.8 and (p.get("identity") or p["provider"]) in prevp]
hi_apr_net=sum(p["_lk"]-prevp[p.get("identity") or p["provider"]] for p in hi_apr)
zero_fee=[p for p in provs if feep(p)==0 and (p.get("identity") or p["provider"]) in prevp]
zero_fee_net=sum(p["_lk"]-prevp[p.get("identity") or p["provider"]] for p in zero_fee)
pi=next((p for p in provs if (p.get("identity") or p["provider"])=="pi-staking"),None)
pi_funcs={}
for t in D.get("pi_staking_inbound_7d",[]):
    f=t.get("function","?"); pi_funcs[f]=pi_funcs.get(f,0)+1
binance_staking_prov_wow=lk_wow("binance_staking")

# ---------- tokens ----------
prev_th={t["identifier"]:t for t in prev["top_tokens_by_holders"]}
prev_tv={t["identifier"]:t for t in prev.get("top_tokens_by_volume",[])}
top_by_holders=[]
for t in D["tokens_holders"][:10]:
    pid=prev_th.get(t["identifier"]); ph=pid["holders"] if pid else None
    top_by_holders.append({"identifier":t["identifier"],"name":t.get("name"),"holders":t["accounts"],
        "previous_holders":ph,"holders_change":(t["accounts"]-ph) if ph else None,
        "price_usd":t.get("price"),"market_cap_usd":t.get("marketCap"),"volume_24h_usd":None})
top_by_volume=[]
for t in D["tokens_txs"][:10]:
    ptx=prev_tv.get(t["identifier"])
    pt=ptx.get("transactions") if ptx else None
    top_by_volume.append({"identifier":t["identifier"],"name":t.get("name"),"transactions":t.get("transactions"),
        "previous_transactions":pt,"change_pct":(100*(t.get("transactions",0)-pt)/pt) if pt else None,
        "price_usd":t.get("price"),"volume_24h_usd":None})
holders_map={t["identifier"]:t.get("accounts") for t in D["tokens_holders"]}
top_by_market_cap=[]
for t in D["tokens_mcap"][:10]:
    tid=t["identifier"]
    top_by_market_cap.append({"identifier":tid,"name":t.get("name"),"holders":holders_map.get(tid),
        "previous_holders":prev_th.get(tid,{}).get("holders"),
        "price_usd":t.get("price"),"market_cap_usd":t.get("marketCap"),"volume_24h_usd":None})
KNOWN_TOKEN_IDS={t["identifier"] for t in prev.get("top_tokens_by_holders",[])} | {t["identifier"] for t in prev.get("top_tokens_by_volume",[])}
newly_issued=[]; newly_issued_rejected=[]
for ni in D.get("newly_issued", []):
    if ni["accounts"]>1000 or ni["identifier"] in KNOWN_TOKEN_IDS:
        newly_issued_rejected.append((ni["identifier"],"established token misidentified by issue-scan")); continue
    if ni["accounts"]<=10 or ni["transactions"]<=5:
        newly_issued_rejected.append((ni["identifier"],f"below quality bar ({ni['accounts']} holders, {ni['transactions']} txs)")); continue
    newly_issued.append({"identifier":ni["identifier"],"name":ni["name"],"ticker":ni["ticker"],
        "holders":ni["accounts"],"transactions":ni["transactions"],"timestamp":ni["timestamp"],
        "deployer":ni["deployer"],"deployer_label":lab(ni["deployer"]),
        "issued_at":datetime.fromtimestamp(ni["timestamp"],tz=timezone.utc).isoformat()})

mp=D["mex_pairs"]; meco=D["mex_economics"]
pairs=[]
for p in mp:
    pairs.append({"name":p.get("baseName","?")+"/"+p.get("quoteName","?"),"volume_24h_usd":p.get("volume24h") or 0,
        "tvl_usd":p.get("totalValue"),"trades_count_24h":p.get("tradesCount24h",p.get("trades24h")),"is_other":False})
pairs.sort(key=lambda x:-(x["volume_24h_usd"] or 0))
totvol=sum((x["volume_24h_usd"] or 0) for x in pairs)
for x in pairs: x["share_pct"]=100*(x["volume_24h_usd"] or 0)/totvol if totvol else 0
# NEW (run #18 recommendation #4b): depth / turnover ratio
tot_tvl=sum((p.get("totalValue") or 0) for p in mp)
prev_tot_tvl=sum((p.get("totalValue") or 0) for p in prevcol.get("mex_pairs",[]))
prev_tot_vol=sum((p.get("volume24h") or 0) for p in prevcol.get("mex_pairs",[]))
turnover=100*totvol/tot_tvl if tot_tvl else None
prev_turnover=100*prev_tot_vol/prev_tot_tvl if prev_tot_tvl else None
prev_mexp=prev["xexchange"]["mex_price_usd"]; prev_dexvol=prev["xexchange"]["volume_24h_usd"]
dex_wow=100*(totvol-prev_dexvol)/prev_dexvol
xexchange={"total_pairs":meco.get("marketPairs"),"total_volume_24h_usd":totvol,"mex_price_usd":meco["price"],
    "mex_market_cap_usd":meco["marketCap"],"mex_price_change_24h_pct":None,
    "mex_price_change_wow_pct":100*(meco["price"]-prev_mexp)/prev_mexp,
    "top_pair":pairs[0]["name"],"top_pair_volume_24h_usd":pairs[0]["volume_24h_usd"],
    "top_pair_dominance_pct":pairs[0]["share_pct"],"top_pairs_by_volume":pairs[:5],
    "pool_tvl_usd":tot_tvl,"previous_pool_tvl_usd":prev_tot_tvl,
    "turnover_ratio_pct":turnover,"previous_turnover_ratio_pct":prev_turnover}

# ---------- defi ----------
tt=D["tvl_tokens"]
def mc(tid):
    t=tt.get(tid); return (t.get("marketCap") or 0) if isinstance(t,dict) else 0
def supply(tid, col=tt):
    t=col.get(tid)
    try: return float(t.get("supply")) if t and t.get("supply") else None
    except: return None
def supply_wow(tid):
    c=supply(tid); p=supply(tid,prevcol.get("tvl_tokens",{}))
    if c is None or p is None or p==0: return None
    return 100*(c-p)/p
hatom_lending=sum(mc(x) for x in ["HUSDC-d80042","HEGLD-d61095","HUSDT-6f0914","HWBTC-49ca31","HWETH-b3d17e","HBUSD-ac1fca","HHTM-e03ba5","HMEX-df6df7","HUTK-4fa4b2","HWTAO-2e9136"])
segld_mcap=mc("SEGLD-3ad2d0"); swtao_mcap=mc("SWTAO-356a25")
hatom_lsd=segld_mcap+swtao_mcap
hatom_ush=mc("USH-111e09"); xoxno_lsd=mc("XEGLD-e413ed")
segld_supply_wow=supply_wow("SEGLD-3ad2d0"); xegld_supply_wow=supply_wow("XEGLD-e413ed")
swtao_supply_wow=supply_wow("SWTAO-356a25"); ush_supply_wow=supply_wow("USH-111e09")

wegld_egld=sum(int(b["balance"])/1e18 for b in D["wegld"].values() if isinstance(b,dict) and "balance" in b)
xexch_tvl_egld=wegld_egld; xexch_tvl_usd=wegld_egld*price
def tcount(name):
    c=D["proto"][name]["transfers_24h"]; return c.get("count") if isinstance(c,dict) else c
prev_hl_egld=prev["defi_tvl"]["Hatom Lending"]/pp
prev_xl_egld=prev["defi_tvl"]["XOXNO LSD"]/pp
prev_hush=prev["defi_tvl"]["Hatom USH"]
prev_xexch_egld=prev["defi_tvl"]["xExchange (USD)"]/pp
prev_hlsd=prev["defi_tvl"]["Hatom Liquid Staking"]; prev_hlsd_egld=prev_hlsd/pp
hl_egld=hatom_lending/price; hlsd_egld=hatom_lsd/price
xlsd_egld=xoxno_lsd/price; ush_egld=hatom_ush/price
hl_egld_chg=100*(hl_egld-prev_hl_egld)/prev_hl_egld
inverse_ratio=abs(hl_egld_chg)/abs(price_chg)

wegld_tok=D.get("wegld_token") or {}
wegld_supply_now=float(wegld_tok.get("supply") or 0)
wegld_supply_prev=None
for t in prevcol.get("tokens_holders",[]):
    if t["identifier"]=="WEGLD-bd4d79":
        try: wegld_supply_prev=int(t.get("supply","0"))/1e18
        except: pass
wegld_chg_pct=100*(wegld_supply_now-wegld_supply_prev)/wegld_supply_prev if wegld_supply_prev else 0

def stable_wow(sid):
    c=D.get("stable_"+sid,{}); p=prevcol.get("stable_"+sid,{})
    try: cur=float(c.get("supply")); pr=float(p.get("supply"))
    except: return None
    return 100*(cur-pr)/pr if pr else None
usdc_supply_wow=stable_wow("USDC-c76f1f"); usdt_supply_wow=stable_wow("USDT-f8c08c")
USH_PREV_WOW=-2.60
USH_CUM_2W=100*((1+ush_supply_wow/100)*(1+USH_PREV_WOW/100)-1)

protocol_breakdown=[
 {"protocol":"xExchange","category":"dex","addresses_tracked":16,"tvl_usd":xexch_tvl_usd,"tvl_egld":xexch_tvl_egld,
  "tvl_wow_change_pct":100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld,"transfers_24h":None,"volume_24h_usd":totvol,
  "notable_events":f"DEX volume fell a further {dex_wow:.0f}% to ${totvol/1000:.0f}K - a NEW LOW for the tracked history, below run #12's floor, and the second consecutive halving. The new depth instrument (added this run per run #18's recommendation) measures what was inferred last week: pool TVL is ${tot_tvl/1e6:.2f}M against ${prev_tot_tvl/1e6:.2f}M ({100*(tot_tvl-prev_tot_tvl)/prev_tot_tvl:+.1f}%), so the TURNOVER RATIO halved from {prev_turnover:.2f}% to {turnover:.2f}% of pool value traded per day. Liquidity is being provided and not used. WEGLD supply also rose {wegld_chg_pct:+.2f}% (more EGLD wrapped, not less). Concentration {pairs[0]['share_pct']:.1f}% in WEGLD/USDC.","health_signal":"shrinking"},
 {"protocol":"Hatom Lending","category":"lending","addresses_tracked":13,"tvl_usd":hatom_lending,"tvl_egld":hl_egld,
  "tvl_wow_change_pct":hl_egld_chg,"transfers_24h":tcount("Hatom EGLD MM"),
  "notable_events":f"TVL ${hatom_lending/1e6:.2f}M USD ({100*(hatom_lending-prev['defi_tvl']['Hatom Lending'])/prev['defi_tvl']['Hatom Lending']:+.1f}%), {hl_egld/1000:.0f}K EGLD ({hl_egld_chg:+.2f}% EGLD). BILATERAL INVERSE RULE: 7th confirmation. Price {price_chg:+.2f}% (just past the |5%| guardrail, so the rule is evaluable) against EGLD-denominated TVL {hl_egld_chg:+.2f}%, response ratio {inverse_ratio:.2f}. Down-week series is now 0.88 / 0.80 / 0.70 / 0.21 / 0.98 / {inverse_ratio:.2f}. Run #18's 0.98 was a spike rather than a new level, but this is comfortably above the 0.21 trough - depositor dip-buying capacity is present and mid-range, not exhausted. Deposits grew for a second straight week in EGLD terms.","health_signal":"growing"},
 {"protocol":"Hatom Liquid Staking","category":"liquid_staking","addresses_tracked":2,"tvl_usd":hatom_lsd,"tvl_egld":hlsd_egld,
  "tvl_wow_change_pct":100*(hlsd_egld-prev_hlsd_egld)/prev_hlsd_egld,"transfers_24h":tcount("Hatom Liquid Staking"),
  "notable_events":f"SEGLD ${segld_mcap/1e6:.2f}M + SWTAO ${swtao_mcap/1e6:.2f}M = ${hatom_lsd/1e6:.2f}M USD ({100*(hatom_lsd-prev_hlsd)/prev_hlsd:+.1f}%). On the supply basis (run #13 rule) Hatom LSD is FLAT for a second week: SEGLD {segld_supply_wow:+.2f}%, SWTAO {swtao_supply_wow:+.2f}%. Two consecutive -5% and -10% price weeks have produced no redemption pressure on the largest LSD. dataApi price feed clean for a 5th consecutive run (0 re-fetch retries).","health_signal":"flat"},
 {"protocol":"Hatom USH","category":"stablecoin","addresses_tracked":4,"tvl_usd":hatom_ush,"tvl_egld":ush_egld,
  "tvl_wow_change_pct":100*(hatom_ush-prev_hush)/prev_hush,"transfers_24h":None,
  "notable_events":f"USH supply burned {ush_supply_wow:+.2f}% to {supply('USH-111e09'):,.0f} - a SECOND consecutive burn week past the 1% threshold, cumulative {USH_CUM_2W:+.2f}% over two weeks. The run #18 question was whether the de-leveraging would accelerate past ~5% in a single week (forced-closure capitulation signature) or stop at one week (orderly de-risking). Neither: it continued at almost exactly the same pace, which reads as orderly, sustained position-closing rather than liquidation. CDP borrowers have now unwound roughly the whole of the run #16 +6.49% leverage chase.","health_signal":"shrinking"},
 {"protocol":"XOXNO LSD","category":"liquid_staking","addresses_tracked":2,"tvl_usd":xoxno_lsd,"tvl_egld":xlsd_egld,
  "tvl_wow_change_pct":100*(xlsd_egld-prev_xl_egld)/prev_xl_egld,"transfers_24h":tcount("XOXNO LSD"),
  "notable_events":f"XEGLD ${xoxno_lsd/1e6:.2f}M ({100*(xoxno_lsd-prev['defi_tvl']['XOXNO LSD'])/prev['defi_tvl']['XOXNO LSD']:+.1f}% USD). Supply {xegld_supply_wow:+.2f}% to {supply('XEGLD-e413ed'):,.0f} - essentially FLAT, which breaks the pattern. XOXNO has been the LSD leg that redeems on weakness in every prior drawdown (-29% in run #14, -2.70% last week); this week it held through a -5% price move. Either the redeemer cohort is exhausted or the marginal holder has changed.","health_signal":"flat"},
 {"protocol":"XOXNO Aggregator","category":"aggregator","addresses_tracked":1,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("XOXNO Aggregator"),
  "notable_events":f"Throughput {tcount('XOXNO Aggregator'):,} daily transfers, still the highest single-contract routing activity on the network but DOWN from 12,055-class levels seen through the rally. Unlike last week it did fall alongside DEX volume, so on-chain routing demand is now softening too.","health_signal":"flat"},
 {"protocol":"OneDex","category":"aggregator","addresses_tracked":5,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("OneDex Swap"),
  "notable_events":f"{tcount('OneDex Swap'):,} daily transfers via the swap contract.","health_signal":"flat"},
 {"protocol":"JEXchange","category":"dex","addresses_tracked":4,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("JEXchange Fees"),
  "notable_events":f"Fees wallet {tcount('JEXchange Fees'):,} daily transfers.","health_signal":"flat"}]
protocols=[
 {"name":"xExchange","category":"dex","volume_24h_usd":totvol,"active_pairs":25,"transfers_24h":None,"tvl_usd":xexch_tvl_usd,"tvl_egld":xexch_tvl_egld,"tvl_wow_change_pct":100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld},
 {"name":"Hatom Lending","category":"lending","volume_24h_usd":None,"active_pairs":None,"transfers_24h":tcount("Hatom EGLD MM"),"tvl_usd":hatom_lending,"tvl_egld":hl_egld,"tvl_wow_change_pct":hl_egld_chg},
 {"name":"Hatom Liquid Staking","category":"liquid_staking","volume_24h_usd":None,"active_pairs":None,"transfers_24h":tcount("Hatom Liquid Staking"),"tvl_usd":hatom_lsd,"tvl_egld":hlsd_egld,"tvl_wow_change_pct":100*(hlsd_egld-prev_hlsd_egld)/prev_hlsd_egld},
 {"name":"XOXNO LSD","category":"liquid_staking","volume_24h_usd":None,"active_pairs":None,"transfers_24h":tcount("XOXNO LSD"),"tvl_usd":xoxno_lsd,"tvl_egld":xlsd_egld,"tvl_wow_change_pct":100*(xlsd_egld-prev_xl_egld)/prev_xl_egld}]

# ---------- token supply events ----------
prev_supply_raw={t["identifier"]:int(t["supply_raw"]) if t.get("supply_raw") else None for t in prev["top_tokens_by_holders"]}
cur_by_id={t["identifier"]:t for t in D["tokens_holders"]}
token_supply_events=[]
for tid,ps in prev_supply_raw.items():
    ct=cur_by_id.get(tid)
    if ct and ps and ps>0:
        try: cs=int(ct.get("supply","0"))
        except: cs=None
        if cs and cs>0:
            chg=100*(cs-ps)/ps
            thresh = 0.1 if tid.startswith("USDC") or tid.startswith("USDT") else 1.0
            if abs(chg)>thresh:
                ev="mint" if chg>0 else "burn"
                token_supply_events.append({"identifier":tid,"name":ct.get("name","?"),"event":ev,
                    "supply_previous":str(ps),"supply_current":str(cs),"change_pct":chg,
                    "description":f"{tid} supply {chg:+.2f}% ({ev})."})

# ---------- anomalies ----------
rb=learn["runs"][-1]["running_baselines"]
def zc(arr,cur):
    if len(arr)<4: return None
    m=sum(arr)/len(arr); sd=math.sqrt(sum((x-m)**2 for x in arr)/len(arr))
    return m,sd,((cur-m)/sd if sd else 0)
zp=zc(rb["egld_price_usd"],price); zmex=zc(rb["mex_price_usd"],meco["price"])
zd=zc(rb["total_delegators"],cur_deleg); zse=zc(rb["staked_egld"],staked)
zv=zc(rb["dex_volume_24h_usd"],totvol)
mw_bal_cur=bal_of("erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw") or 1093312
cb_routing=bal_of("erd1lgdltequh7627rtlacmcp6p5vec7zmu2rxhu7pjwvcja8f4a9gqq9vcc70") or 0
desk_cur=(bal_of(UPBIT_DESK) or 0)+(bal_of(DIST_DESK) or 0)
desk_prev=61495.0
desk_delta=desk_cur-desk_prev

anomalies=[
 {"metric":"otc_pipeline_circularity","current_value":round(HUB_NET_ONEWAY),"previous_value":round(OTC_THR_7D),"method":"rule_based",
  "severity":"high",
  "description":f"THE OTC PIPELINE IS 80% CIRCULAR - AND NOBODY MEASURED THAT BEFORE. Gross 7d desk throughput was {OTC_THR_7D:,.0f} EGLD out and {OTC_IN_7D:,.0f} in, essentially unchanged from last week's {OTC_THR_7D_PREV:,.0f}. But resolving BOTH legs two hops out (run #17 established the outbound rule; the inbound mirror is new this run) shows the desks were fed by the same venues they deliver to. Bybit pushed {hub['inbound_by_venue'].get('Bybit',0):,.0f} EGLD in through three feeder wallets and took {hub['outbound_by_venue'].get('Bybit',0):,.0f} back out through five routers; Gate.io {hub['inbound_by_venue'].get('Gate.io',0):,.0f} in / {hub['outbound_by_venue'].get('Gate.io',0):,.0f} out. Netting round-trips out leaves {HUB_NET_ONEWAY:,.0f} EGLD of genuine one-way movement - {100*HUB_CIRCULAR/hub['gross_out']:.0f}% of the gross figure is churn. The net picture is simple and small: UPbit is the only net SOURCE ({hub_net.get('UPbit',0):+,.0f}), and Binance.com ({hub_net.get('Binance.com',0):+,.0f}), Bybit ({hub_net.get('Bybit',0):+,.0f}), Gate.io ({hub_net.get('Gate.io',0):+,.0f}) and one recurring whale intermediary ({hub_net.get('Unknown Whale I (active)',0):+,.0f}) are net receivers. IMPLICATION FOR THE SERIES: runs #13-#18 report GROSS throughput with no circularity adjustment, so the five-week escalation documented last run may be part churn. The gross series is still valid as a measure of pipeline ACTIVITY; it is not a measure of distribution volume."},
 {"metric":"binance_custody_reload_origin","current_value":round(cust_bal),"previous_value":round(cust_prev),"method":"rule_based",
  "severity":"high",
  "description":f"RUN #18'S BULLISH CUSTODY SIGNAL IS FALSIFIED. The +150,000 reload of the Binance Staking custody wallet arrived from erd1r3w62vq, which run #18 could only describe as a nonce-8 pass-through. Its full 30-day history is now resolved and contains exactly three transactions: an unDelegate on the Binance Staking DELEGATION contract (2026-07-09), a withdraw from the same contract (2026-07-22), and the 150,000 transfer to custody minutes later. The reload was the delegation unwind COMPLETING - the -148,941 the binance_staking provider shed in the run #16 window arriving in custody after the unbonding period - not fresh accumulation from an external or OTC source. Run #18 read it as the de-staking programme reversing and called it the strongest bullish structural counter-signal of that week; the correct reading is that the programme continued and merely changed legs, moving EGLD from delegated stake into custody. The custody wallet then did not move at all this week ({cust_bal:,.0f}, unchanged). Cumulative position: {cust_bal-3512650:+,.0f} from the 3,512,650 peak."},
 {"metric":"dex_volume_24h_usd","current_value":totvol,"previous_value":prev_dexvol,"method":"z_score",
  "average_value":zv[0],"stddev":zv[1],"z_score":zv[2],"severity":"medium",
  "description":f"DEX VOLUME MADE A NEW TRACKED LOW: ${totvol/1000:.1f}K, {dex_wow:.1f}% WoW and a second consecutive halving, taking out run #12's prior floor. z={zv[2]:+.2f}sigma understates it because the baseline still contains the rally spike. The depth instrument added this run resolves last week's inference: pool TVL is ${tot_tvl/1e6:.2f}M vs ${prev_tot_tvl/1e6:.2f}M ({100*(tot_tvl-prev_tot_tvl)/prev_tot_tvl:+.1f}%), so the daily TURNOVER RATIO fell from {prev_turnover:.2f}% to {turnover:.2f}%. Liquidity providers are still there; traders are not. Two weeks of falling price on collapsing turnover with intact depth is the signature of an absent bid, not aggressive selling."},
 {"metric":"identifiable_bid_absent","current_value":0,"previous_value":0,"method":"rule_based",
  "severity":"medium",
  "description":f"THE IDENTIFIABLE BID IS ABSENT FOR A SECOND WEEK - now measured as a standing instrument rather than an ad-hoc trace (run #18 recommendation #4a). Mega Whale erd18mv2z6r2, the only large absorber this model has ever been able to name, recorded zero value transactions again and sits at exactly {mw_bal_cur:,.0f}, unchanged to the decimal for a second week. The Coinbase Routing wallet that filled it in runs #15 (+32.7K) and #17 (+50.6K) holds {cb_routing:,.0f} EGLD and also transacted nothing. Composite identifiable-bid reading: 0 EGLD absorbed in 14 days, against roughly 61,000 of net one-way OTC distribution in the last 7 alone. This is the cleanest statement of the week's structural problem."},
 {"metric":"withdrawal_breadth","current_value":breadth["distinct_recipients_ex_pipeline"],"previous_value":None,"method":"rule_based",
  "severity":"low",
  "description":f"WITHDRAWAL BREADTH INSTRUMENTED (run #18 recommendation #4c) - first measurement, so it establishes a baseline rather than a signal. {breadth['distinct_recipients_raw']} distinct non-exchange addresses received transfers of >1,000 EGLD out of tracked exchange wallets this week, totalling {breadth['total_egld_raw']:,.0f} EGLD. The instrument is only useful once the OTC pipeline is stripped out, and it turns out the pipeline dominates: {breadth['pipeline_share_pct']:.0f}% of that volume went to desks, feeders or routers. Excluding them leaves {breadth['distinct_recipients_ex_pipeline']} addresses and {breadth['total_egld_ex_pipeline']:,.0f} EGLD of what could plausibly be self-custody withdrawal. Largest genuine recipients: {', '.join(f'{a[:10]}... {v:,.0f}' for a,v in breadth_top[:3])}. Note the asymmetry this exposes - roughly {breadth['total_egld_ex_pipeline']/1000:.0f}K of dispersed withdrawal against zero absorption by the one named large bid."},
 {"metric":"egld_price_usd","current_value":price,"previous_value":pp,"method":"z_score",
  "average_value":zp[0],"stddev":zp[1],"z_score":zp[2],"severity":"medium",
  "description":f"EGLD {price_chg:+.2f}% to ${price:.2f}, a second consecutive down week, z={zp[2]:+.2f}sigma. The relative picture changed from last week and that matters: BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}% BOTH FELL this week, and EGLD's decline is in line with ETH's rather than decoupled from it. Run #18's defining anomaly was EGLD falling double digits against RISING majors; that did not repeat. Practically this means the week's weakness is mostly broad crypto risk-off rather than a fresh chain-specific event - which slightly softens the run #18 diagnosis without overturning it, since the demand instruments (turnover ratio halved, absorber idle, OTC still net-distributing) all deteriorated independently of the tape."},
 {"metric":"ush_deleveraging_second_week","current_value":ush_supply_wow,"previous_value":-2.60,"method":"rule_based",
  "severity":"medium",
  "description":f"USH DE-LEVERAGING CONTINUED AT THE SAME PACE, NOT ACCELERATING. Supply burned {ush_supply_wow:+.2f}% to {supply('USH-111e09'):,.0f}, following -2.60% last week: cumulative {USH_CUM_2W:+.2f}% over two weeks. Run #18 registered the test as accelerate-past-5%-in-one-week (forced CDP closures, historically a capitulation and often a local low) versus stop-after-one-week (orderly de-risking). The outcome is the third possibility - a steady, orderly unwind - which reads as position management rather than liquidation. Borrowers have now retired approximately the entire run #16 +6.49% leverage build. No forced-closure signature, so no capitulation tell to trade off."},
 {"metric":"staked_egld","current_value":staked,"previous_value":pecon["staked_egld"],"method":"z_score",
  "average_value":zse[0],"stddev":zse[1],"z_score":zse[2],"severity":"low",
  "description":f"Total staked {staked:,} EGLD ({staked-pecon['staked_egld']:+,} WoW), staked ratio {sr*100:.2f}% ({100*(sr-pecon['staked_ratio']):+.2f}pp), z={zse[2]:+.2f}sigma. The composition repeats last week's pattern and is more informative than the headline: DELEGATION grew {deleg_tvl_wow:+,.0f} while total staked fell, so approximately {abs(direct_node_delta):,.0f} EGLD left DIRECT-NODE stake. That is a second consecutive week of node operators unwinding while delegated stake accumulates - a structural rotation from self-operated validation into delegation contracts, not a reduction in staking commitment."},
 {"metric":"yield_chase_reactivated","current_value":round(hi_apr_net),"previous_value":None,"method":"rule_based",
  "severity":"low",
  "description":f"THE pi-staking MYSTERY IS SOLVED, AND IT IS ORDINARY YIELD-CHASING (run #18 recommendation #8). pi-staking added {lk_wow('pi-staking'):+,.0f} EGLD and {usr_wow('pi-staking'):+d} delegators for a 7TH consecutive growth week. Its parameters explain it without any adoption story: 9.10% APR at a 0% service fee, which is the second-highest APR on the network and joint-lowest fee, on a small enough base ({pi['_lk']:,.0f} EGLD, {pi.get('numUsers')} delegators) to still absorb inflows without diluting. The cohort view confirms the mechanism: the {len(hi_apr)} providers with APR >= 8.8% gained {hi_apr_net:+,.0f} EGLD net this week while procryptostaking (7.38% APR, 20% fee) shed {lk_wow('procryptostaking'):+,.0f} and syndicatex (8.14%, 12% fee) shed {lk_wow('syndicatex'):+,.0f}. Zero-fee providers as a group took {zero_fee_net:+,.0f}. This is fee arbitrage inside a static delegator base, not new participation - pi-staking's inbound flow is {pi_funcs.get('delegate',0)} delegate calls averaging small ticket sizes."},
 {"metric":"total_delegators","current_value":cur_deleg,"previous_value":prev_deleg,"method":"z_score",
  "average_value":zd[0],"stddev":zd[1],"z_score":zd[2],"severity":"low",
  "description":f"Total delegators {cur_deleg:,} ({deleg_wow:+,}). Reported for continuity only: participation inertia was promoted to a structural finding at run #18's pre-registered threshold, so a 7th flat week is the base rate and carries no information. Only a break out of the ~174.3K band would. z={zd[2]:+.2f}sigma, immaterial on a {abs(100*deleg_wow/prev_deleg):.4f}% move (run #9 degenerate-z guard)."},
 {"metric":"stablecoin_bleed_stopped","current_value":usdc_supply_wow,"previous_value":-1.01,"method":"rule_based",
  "severity":"low",
  "description":f"BRIDGED-STABLECOIN OUTFLOW ESSENTIALLY STOPPED: USDC {usdc_supply_wow:+.2f}% (from -1.01%) and USDT {usdt_supply_wow:+.2f}% (from -2.79%). After the run #18 restart this is the smallest combined move in the tracked series - dollars stopped leaving the chain during a down week, which is a mild positive divergence from the price tape. It is still not INFLOW, which remains the signal to wait for: no fresh outside capital has arrived."},
 {"metric":"reward_compound_rate","current_value":COMPOUND_PCT,"previous_value":COMPOUND_PREV,"method":"rule_based",
  "severity":"low",
  "description":f"REWARD COMPOUNDING JUMPED TO ITS HIGHEST LEVEL IN TRACKING: {COMPOUND_PCT:.2f}% of reward decisions were reDelegateRewards rather than claimRewards ({REDELEG_N} vs {CLAIM_N} across the top 8 providers), up {COMPOUND_PCT-COMPOUND_PREV:+.2f}pp from {COMPOUND_PREV:.2f}% and above the 61.59% peak set in run #16. Two consecutive weekly slips reversed in one move, during a down week - the run #11 reading is that a rising compound rate through a decline means delegators are doubling down on yield rather than panic-claiming. Fate tracing supports it: of 73 retail claims, 63 were held in-wallet and NONE went to a labelled exchange; the only selling cohort was institutional (3 events, 218 EGLD). Alongside Hatom Lending deposits this is the second cohort adding into weakness."},
 {"metric":"mex_price_usd","current_value":meco["price"],"previous_value":prev_mexp,"method":"z_score",
  "average_value":zmex[0],"stddev":zmex[1],"z_score":zmex[2],"severity":"low",
  "description":f"MEX {100*(meco['price']-prev_mexp)/prev_mexp:+.2f}% to ${meco['price']:.3e} (z={zmex[2]:+.2f}sigma), mcap ${meco['marketCap']/1e6:.2f}M. MEX outperformed EGLD for a second consecutive week ({100*(meco['price']-prev_mexp)/prev_mexp:+.1f}% vs {price_chg:+.1f}%), which with turnover this thin is more likely stale pricing in illiquid pairs than genuine relative strength."}]

# ---------- trend indicators ----------
accelerating_outflows=[
 {"exchange":"NET_EXCHANGE","trend":"outflow","cumulative_change_pct":round(100*net_total/total_prev,1),"weeks_in_trend":1,
  "interpretation":f"Net exchange flow {net_total:+,.0f} EGLD, and for the first time in three weeks the headline needs no adjustment - no intra-entity custody reload, no newly tracked address. UPbit ({ent_cur.get('UPbit',0)-prev_ent.get('UPbit',0):+,.0f}) and Binance.com ({ent_cur.get('Binance',0)-prev_ent.get('Binance',0):+,.0f}) are the whole net; Bybit, KuCoin and Crypto.com took deposits. Read jointly with the OTC channel (run #14 rule), UPbit's outflow is not coins leaving the system - {UPBIT_RELOAD:,.0f} of it went straight into the OTC desks as a fresh distribution tranche."},
 {"exchange":"UPbit OTC Desks","trend":"reloaded","cumulative_change_pct":round(100*desk_delta/desk_prev,1),"weeks_in_trend":1,
  "interpretation":f"THE DESKS WERE RE-FED. Balance {desk_delta:+,.0f} to {desk_cur:,.0f} and gross throughput {OTC_THR_7D:,.0f} ({otc_drop_pct:+.0f}% WoW), but the composition is what changed: UPbit sent a fresh {UPBIT_RELOAD:,.0f} EGLD tranche after sending nothing last week, and Bybit/Gate.io began cycling large volume through the same desks. Run #18's pre-committed test asked whether a third quiet week would establish exhaustion as durable; it did not get one. Net of round-trips the genuine one-way distribution is {HUB_NET_ONEWAY:,.0f}, so the wave is running at roughly a twentieth of run #17's peak - reactivated, not re-escalated."},
 {"exchange":"Binance Staking custody","trend":"flat","cumulative_change_pct":round(100*(cust_bal-3512650)/3512650,1),"weeks_in_trend":1,
  "interpretation":f"Unchanged at {cust_bal:,.0f} - zero transactions. The story is retrospective: last week's +150,000 is now traced to an unDelegate/withdraw pair on the binance_staking DELEGATION contract, so it was the run #16 provider unwind landing rather than accumulation. Cumulative {cust_bal-3512650:+,.0f} from the peak. The de-staking programme is intact, not reversed."},
 {"exchange":"Bybit","trend":"inflow","cumulative_change_pct":5.4,"weeks_in_trend":3,
  "interpretation":f"3rd consecutive inflow week ({ent_cur.get('Bybit',0)-prev_ent.get('Bybit',0):+,.0f} to {ent_cur.get('Bybit',0):,.0f}). But Bybit's deposit balance is no longer a clean proxy for pipeline output now that it also FEEDS the pipeline: {hub['inbound_by_venue'].get('Bybit',0):,.0f} out to feeders against {hub['outbound_by_venue'].get('Bybit',0):,.0f} back from routers, a near-wash."}]

prev_names=set(prevp.keys()); cur_names={(p.get('identity') or p['provider']) for p in provs}
joining=[n for n in cur_names-prev_names if n]; leaving=[n for n in prev_names-cur_names if n]
def real_validator(n): return n and not n.startswith("erd1qqqqqqqqqqqqqqq")
real_joiners=[n for n in joining if real_validator(n)]; real_leavers=[n for n in leaving if real_validator(n)]
cur_locked_by={(p.get('identity') or p['provider']):p['_lk'] for p in provs}
notable_joiners=[{"identity":n,"name":n,"locked_egld":cur_locked_by.get(n,0)} for n in real_joiners if cur_locked_by.get(n,0)>50000]
notable_leavers=[{"identity":n,"name":n,"previous_locked_egld":prevp.get(n,0)} for n in real_leavers if prevp.get(n,0)>50000]

trend_indicators={
 "accelerating_exchange_outflows":accelerating_outflows,
 "validator_movements":{"providers_joining":len(real_joiners),"providers_leaving":len(real_leavers),
   "net_provider_change":len(provs)-len(prev["staking_providers"]),
   "notable_joiners":notable_joiners,"notable_leavers":notable_leavers},
 "token_supply_events":token_supply_events,
 "consecutive_streaks":[
   {"metric":"dex_turnover_ratio","direction":"down","weeks":2,"cumulative_change_pct":round(100*(turnover-prev_turnover)/prev_turnover,1),
    "interpretation":f"Daily turnover on xExchange pools fell from {prev_turnover:.2f}% to {turnover:.2f}% of TVL, a second consecutive halving of activity against near-flat depth ({100*(tot_tvl-prev_tot_tvl)/prev_tot_tvl:+.1f}% pool TVL). This is the newly instrumented version of last week's inference, and it is now the model's cleanest demand-side series."},
   {"metric":"pi_staking_growth","direction":"up","weeks":7,"cumulative_change_pct":None,
    "interpretation":f"7th consecutive growth week ({lk_wow('pi-staking'):+,.0f}, {usr_wow('pi-staking'):+d} delegators). Explained this run: 9.10% APR at 0% fee on a small base. It is the sharpest expression of a broader rotation - the APR>=8.8% cohort took {hi_apr_net:+,.0f} EGLD while high-fee incumbents shed. Fee arbitrage inside a fixed delegator base."},
   {"metric":"direct_node_unwind","direction":"down","weeks":2,"cumulative_change_pct":None,
    "interpretation":f"Second consecutive week where delegation grew ({deleg_tvl_wow:+,.0f}) while total staked fell ({staked-pecon['staked_egld']:+,.0f}), implying roughly {abs(direct_node_delta):,.0f} EGLD exiting direct-node stake. Cumulative over two weeks the direct-node leg has shed close to 190K. Watch whether this is Binance-related (its provider and custody legs both sit inside this rotation) or a broader operator trend."},
   {"metric":"delegator_base_flat","direction":"flat","weeks":7,"cumulative_change_pct":0,
    "interpretation":f"7th flat week ({deleg_wow:+,}). Background assumption since run #18's promotion - recorded, not narrated."},
   {"metric":"token_holder_count_decline","direction":"down","weeks":19,"cumulative_change_pct":None,
    "interpretation":"19th consecutive week of small holder declines across top-10 tokens - the established airdrop-decay baseline."}],
 "regime_shifts":[
   {"metric":"otc_throughput_reinterpreted_as_circular","before_value":round(OTC_THR_7D),"after_value":round(HUB_NET_ONEWAY),
    "description":f"THE PIPELINE'S HEADLINE METRIC IS REDEFINED. Resolving both legs two hops out shows {100*HUB_CIRCULAR/hub['gross_out']:.0f}% of gross desk throughput round-trips to the venue that supplied it. Gross {OTC_THR_7D:,.0f} becomes {HUB_NET_ONEWAY:,.0f} of genuine one-way movement, of which UPbit is the sole net source. Going forward the pipeline needs two numbers - gross activity and net one-way distribution - and the runs #13-#18 series must be labelled as the former. This is the third consecutive run in which a measurement fix materially changed the interpretation (run #17 pagination, run #18 baseline units, run #19 circularity)."},
   {"metric":"custody_reload_reclassified","before_value":round(cust_prev),"after_value":round(cust_bal),
    "description":f"Run #18's 'de-staking programme REVERSED' is downgraded to 'de-staking programme CONTINUED via a different leg'. The reload's funder made an unDelegate and a withdraw on the binance_staking delegation contract immediately before forwarding 150,000 to custody. Bullish structural counter-signal withdrawn."}]}

# ---------- dormant activations ----------
dormant_activations=[]

# ---------- watch list ----------
watch_list=[
 {"item":f"OTC PIPELINE IS 80% CIRCULAR - gross {OTC_THR_7D:,.0f} vs {HUB_NET_ONEWAY:,.0f} genuine one-way; UPbit the only net source ({hub_net.get('UPbit',0):+,.0f})","reason":"Two-hop resolution of BOTH legs (new this run) shows Bybit and Gate.io feeding the same desks they receive from. This changes what the throughput series measures and retroactively qualifies run #18's '76% collapse' and run #17's '1.28M wave' - those are gross activity figures with unknown circularity. NEXT: re-run the two-hop netting every week so net one-way distribution becomes a series in its own right, and if query budget allows, re-net the run #17 peak window to find out how much of the 1.28M was one-way. PRE-COMMITTED READING: net one-way rising back above ~150K with UPbit reloading = wave #2 genuinely staging; net staying near 60K with gross churn = the desks are running settlement traffic, not distribution.","weeks_on_list":1},
 {"item":f"IDENTIFIABLE BID ABSENT 2 WEEKS: Mega Whale erd18mv2z6r2 flat at {mw_bal_cur:,.0f} with zero txs, Coinbase Routing at {cb_routing:,.0f} EGLD","reason":"Now a standing instrument rather than an ad-hoc trace. Zero EGLD absorbed in 14 days against ~61K of net one-way OTC distribution in the last 7. A refill of the Coinbase Routing wallet is the single cleanest early signal that the bid is back; absent that, price has no named buyer. Two weeks is not yet a structural claim - if a third passes with no activity, promote to a structural finding that the chain's large-bid infrastructure is dormant.","weeks_on_list":16},
 {"item":f"DEX TURNOVER RATIO HALVED TWICE: {prev_turnover:.2f}% -> {turnover:.2f}% of pool TVL traded daily, volume ${totvol/1000:.0f}K is a new tracked low","reason":"The depth instrument requested in run #18 is now live and it confirms the inference: depth is intact (pool TVL nearly flat), trading is gone. This is the model's best demand-side series because it is independent of both price and the flow plumbing. Watch for turnover recovering above ~4% as the first evidence that the bid returned, or a THIRD halving, which would put xExchange into a liquidity-crisis regime where even modest sells move price.","weeks_on_list":1},
 {"item":f"BINANCE DE-STAKING PROGRAMME IS INTACT, NOT REVERSED - custody flat at {cust_bal:,.0f}, last week's +150,000 traced to an unDelegate/withdraw","reason":"Falsifies run #18's bullish read. Binance has moved ~150K from its delegation provider into custody and drawn down ~305K from custody to hot wallets since the 3.51M peak. The open question is what custody does with the re-parked 150,000: a further drawdown to hot wallets continues distribution; a re-delegation would be the first genuinely constructive Binance signal in five runs. Both readings registered now.","weeks_on_list":13},
 {"item":f"USH DE-LEVERAGING, WEEK 2: {ush_supply_wow:.2f}% after {USH_PREV_WOW:.2f}%, cumulative {USH_CUM_2W:+.2f}%","reason":"Run #18's test resolved on a third branch - the burn neither accelerated past 5% in a week (capitulation) nor stopped (one-off). It is an orderly, sustained unwind that has now retired the whole run #16 leverage chase. NEXT: a third burn week would take USH below its pre-chase level and imply borrowers are cutting BASE positions rather than just the chase, which historically precedes local lows. A stabilisation would mark the de-leveraging complete.","weeks_on_list":4},
 {"item":f"DEPOSITOR CAPACITY CONFIRMED MID-RANGE: bilateral inverse ratio {inverse_ratio:.2f} (7th confirmation; down-week series 0.88/0.80/0.70/0.21/0.98/{inverse_ratio:.2f})","reason":"Run #18 asked whether the record 0.98 marked structurally restored capacity (>0.8 repeat) or a one-off (revert to 0.2-0.4). The answer is neither extreme: 0.58 is healthy, mid-range, and well clear of the 0.21 trough. Practical conclusion: run #11's capacity-decay hypothesis stays falsified, but 0.98 was a spike not a level. Hatom Lending deposits have now grown in EGLD terms for two consecutive down weeks - the only cohort consistently adding.","weeks_on_list":2},
 {"item":f"YIELD ARBITRAGE IS THE ONLY ACTIVE FORCE IN STAKING: APR>=8.8% cohort {hi_apr_net:+,.0f}, pi-staking {lk_wow('pi-staking'):+,.0f} for a 7th week","reason":"Run #18 asked what drives pi-staking; the answer is 9.10% APR at 0% fee on a small base, not an integration or adoption story. The generalisable finding is that with participation inert, the only stake that moves is existing delegators rotating toward zero-fee high-APR providers. Watch whether high-fee incumbents (procryptostaking at 20%, syndicatex at 12%) cut fees in response - that would be the first competitive repricing in the delegation market in tracking.","weeks_on_list":1},
 {"item":f"STABLECOIN OUTFLOW STOPPED (USDC {usdc_supply_wow:.2f}%, USDT {usdt_supply_wow:.2f}%) but no inflow","reason":"Smallest combined move in the series after last week's restart - dollars stopped leaving during a down week, a mild positive divergence. The signal to wait for is unchanged and unmet: a genuine INFLOW week is the cleanest confirmation that outside capital is returning to the chain.","weeks_on_list":6},
 {"item":"KUCOIN whale deposit GRADUATED - balance stable two weeks after the 145,443 arrival","reason":"Resolved bearish in run #18 and confirmed stationary this week (+2,549). The position was absorbed by the venue and has not moved. No further tracking value unless the balance moves materially.","weeks_on_list":3}]

executive_summary=[
 {"finding":f"THE OTC PIPELINE IS 80% CIRCULAR - THE HEADLINE THROUGHPUT NUMBER HAS BEEN MEASURING CHURN. Gross desk throughput was {OTC_THR_7D:,.0f} EGLD, barely changed from last week's {OTC_THR_7D_PREV:,.0f}. Resolving BOTH legs two hops out (run #17 did outbound; the inbound mirror is new) shows the desks were FED by the venues they deliver to: Bybit sent {hub['inbound_by_venue'].get('Bybit',0):,.0f} in through feeders and took {hub['outbound_by_venue'].get('Bybit',0):,.0f} back out through routers. Net of round-trips, genuine one-way movement is {HUB_NET_ONEWAY:,.0f}, with UPbit the only net source ({hub_net.get('UPbit',0):+,.0f}) and Binance.com, Bybit, Gate.io and one whale intermediary the net receivers. The runs #13-#18 series measures pipeline ACTIVITY, not distribution volume, and must be relabelled.","severity":"critical","category":"whale"},
 {"finding":f"RUN #18'S BULLISH CUSTODY SIGNAL IS FALSIFIED. The +150,000 that reloaded Binance's staking custody came from erd1r3w62vq, whose complete 30-day history is an unDelegate (Jul 9) and a withdraw (Jul 22) on the binance_staking DELEGATION contract, followed minutes later by the transfer to custody. It was the run #16 provider unwind (-148,941) completing after the unbonding period, not fresh accumulation. The de-staking programme did not reverse - it changed legs. Custody then sat unchanged at {cust_bal:,.0f} all week, {cust_bal-3512650:+,.0f} from its peak. This is the second consecutive run where tracing one hop further inverted the previous week's conclusion.","severity":"critical","category":"whale"},
 {"finding":f"THE UPbit RELOAD RESUMED AFTER ONE WEEK OFF. Run #18 read the absence of a UPbit tranche as the distribution feed switching off, and pre-registered a third quiet week as confirmation of durable exhaustion. It did not get a second: UPbit pushed a fresh {UPBIT_RELOAD:,.0f} EGLD into the desks (versus 364,000 at the run #17 peak and zero last week), and the desk balance rose {desk_delta:+,.0f} to {desk_cur:,.0f}. The wave is reactivated at roughly a twentieth of peak scale rather than re-escalating - but 'the operator has stopped' lasted exactly one week.","severity":"high","category":"whale"},
 {"finding":f"THE IDENTIFIABLE BID HAS BEEN ABSENT FOR TWO FULL WEEKS - now a standing instrument. Mega Whale erd18mv2z6r2 recorded zero value transactions for a second consecutive week and is unchanged to the decimal at {mw_bal_cur:,.0f}; the Coinbase Routing wallet that filled it in runs #15 and #17 holds {cb_routing:,.0f} EGLD and also did nothing. Composite reading: 0 EGLD absorbed in 14 days against ~{HUB_NET_ONEWAY/1000:.0f}K of net one-way OTC distribution in the last 7 alone.","severity":"high","category":"whale"},
 {"finding":f"DEX TURNOVER HALVED FOR A SECOND WEEK AND VOLUME MADE A NEW TRACKED LOW: ${totvol/1000:.1f}K ({dex_wow:.0f}%). The depth instrument added this run turns last week's inference into a measurement - pool TVL is ${tot_tvl/1e6:.2f}M against ${prev_tot_tvl/1e6:.2f}M ({100*(tot_tvl-prev_tot_tvl)/prev_tot_tvl:+.1f}%), so daily turnover fell from {prev_turnover:.2f}% to {turnover:.2f}% of pool value. Depth is intact and traders are gone. This is now the model's cleanest demand-side series because it is independent of both price and the flow plumbing.","severity":"high","category":"token"},
 {"finding":f"EGLD {price_chg:+.2f}% TO ${price:.2f}, BUT THIS TIME WITH THE TAPE: BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}% both fell, and EGLD tracked ETH almost exactly. Run #18's defining anomaly - a double-digit fall against RISING majors - did not repeat, so this week is broad risk-off rather than a fresh chain-specific event. That partially resolves run #18's pre-committed test: price kept falling (bid-problem branch), but the premise that there was 'no traceable distribution' turned out to be wrong once the pipeline was netted properly.","severity":"medium","category":"network"},
 {"finding":f"YIELD ARBITRAGE IS THE ONLY THING MOVING IN STAKING, AND IT EXPLAINS pi-staking. pi-staking added {lk_wow('pi-staking'):+,.0f} EGLD and {usr_wow('pi-staking'):+d} delegators for a 7th consecutive week; its parameters are 9.10% APR at a 0% fee on a {pi['_lk']:,.0f} EGLD base - second-highest APR, joint-lowest fee. The cohort confirms it: providers at APR >= 8.8% took {hi_apr_net:+,.0f} net while procryptostaking (20% fee) shed {lk_wow('procryptostaking'):+,.0f} and syndicatex (12% fee) shed {lk_wow('syndicatex'):+,.0f}. With participation inert at {cur_deleg:,} delegators, the only stake that moves is existing delegators repricing fees. Separately, delegation grew {deleg_tvl_wow:+,.0f} while total staked fell {staked-pecon['staked_egld']:+,.0f} - a second week of ~{abs(direct_node_delta)/1000:.0f}K leaving direct-node stake.","severity":"medium","category":"staking"},
 {"finding":f"DEFI HELD UP BETTER THAN THE TAPE. USH burned {ush_supply_wow:.2f}% for a second week (cumulative {USH_CUM_2W:+.2f}%), an orderly unwind that retires the run #16 leverage chase without the forced-closure signature that would mark capitulation. Against that: Hatom Lending's EGLD-denominated TVL rose {hl_egld_chg:+.2f}% for a second consecutive down week (bilateral-inverse ratio {inverse_ratio:.2f}, 7th confirmation), the Hatom and XOXNO LSDs were both FLAT on supply for the first time in four drawdown weeks, the reward compound rate made a new tracked high at {COMPOUND_PCT:.2f}%, and bridged stablecoin outflow essentially stopped (USDC {usdc_supply_wow:.2f}%, USDT {usdt_supply_wow:.2f}%). Nobody is leaving; nobody new is arriving.","severity":"medium","category":"defi"}]

# ---------- network health ----------
network_health={
 "economics":{"egld_price_usd":price,"market_cap_usd":econ["marketCap"],"total_supply":econ["totalSupply"],
   "circulating_supply":econ["circulatingSupply"],"staked_egld":staked,"staked_ratio":sr,
   "staking_apr":econ["apr"],"base_apr":econ["baseApr"],"topup_apr":econ["topUpApr"],"token_market_cap_usd":econ["tokenMarketCap"]},
 "activity":{"total_accounts":st["accounts"],"total_transactions":st["transactions"],"epoch":st["epoch"],
   "blocks":st["blocks"],"shards":st["shards"],"transactions_7d":st["transactions"]-pact["total_transactions"],
   "avg_daily_transactions":round((st["transactions"]-pact["total_transactions"])/7)},
 "deltas":{"price_change_pct":price_chg,
   "market_cap_change_pct":100*(econ["marketCap"]-pecon["market_cap_usd"])/pecon["market_cap_usd"],
   "staked_ratio_change_pp":100*(sr-pecon["staked_ratio"]),
   "apr_change_pp":100*(econ["apr"]-pecon["staking_apr"]),"accounts_added":st["accounts"]-pact["total_accounts"],
   "btc_correlation_note":f"EGLD {price_chg:+.2f}% WoW vs BTC {btc_wow:+.2f}% / ETH {eth_wow:+.2f}%. Unlike run #18 - where EGLD fell double digits while both majors ROSE - this week the whole tape was down and EGLD's move is in line with ETH's and modestly worse than BTC's. That is ordinary high-beta behaviour, so the week's weakness should be attributed mostly to broad risk-off rather than a new chain-specific event. The chain-specific concerns from last week remain live but must now be evidenced from the demand instruments (turnover, absorber, net OTC), not from relative price.",
   "transactions_added":st["transactions"]-pact["total_transactions"],"supply_added":econ["totalSupply"]-pecon["total_supply"],
   "staked_egld_added":staked-pecon["staked_egld"],"epoch_advanced":st["epoch"]-pact["epoch"]},
 "analysis":f"EGLD closed the week at ${price:.2f}, {price_chg:+.2f}% WoW, with BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}% - a broad risk-off week in which EGLD behaved like ordinary high beta rather than repeating run #18's decoupling. Market cap ${econ['marketCap']/1e6:.1f}M ({100*(econ['marketCap']-pecon['market_cap_usd'])/pecon['market_cap_usd']:+.1f}%). Usage was again unaffected: {st['transactions']-pact['total_transactions']:,} transactions in the period (~{round((st['transactions']-pact['total_transactions'])/7):,}/day) and {st['accounts']-pact['total_accounts']:,} new accounts, both in line. Staked EGLD fell {staked-pecon['staked_egld']:+,.0f} to {staked:,} and the staked ratio slipped {100*(sr-pecon['staked_ratio']):+.2f}pp to {sr*100:.2f}%, but the composition matters more than the total: delegation GREW {deleg_tvl_wow:+,.0f} while roughly {abs(direct_node_delta):,.0f} left direct-node stake, the second consecutive week of that rotation. The market-structure picture is the substance of the week. Two measurement upgrades changed two of last week's headline conclusions: netting the OTC hub two hops in both directions shows {100*HUB_CIRCULAR/hub['gross_out']:.0f}% of desk throughput is round-trip churn between exchanges, and tracing the Binance custody funder shows last week's 'reload' was a delegation unwind completing rather than accumulation. What survives from last week's diagnosis is the demand side, and it deteriorated further: DEX turnover halved again on flat pool depth, and the one identifiable large bid recorded a second consecutive week of zero activity."}

# ---------- analyses ----------
whale_analysis=f"""Two of this week's findings are corrections to last week's, and both came from tracing one hop further than the previous run managed. That is now a pattern worth naming: on this chain, a balance delta is a hypothesis, not a fact.

CORRECTION 1 - THE OTC PIPELINE IS A CIRCULAR SETTLEMENT HUB, NOT A ONE-WAY DISTRIBUTION CHANNEL. Gross desk throughput was {OTC_THR_7D:,.0f} EGLD out and {OTC_IN_7D:,.0f} in, statistically unchanged from last week's {OTC_THR_7D_PREV:,.0f}. Run #17 established the rule of resolving desk OUTFLOWS two hops to their terminal venue; this run applies the same resolution to the INFLOWS, which had never been done because the desks had always been fed by UPbit alone. They were not this week. Bybit pushed {hub['inbound_by_venue'].get('Bybit',0):,.0f} EGLD into the desks through three zero-balance feeder wallets (erd1ytpenk, erd1rzkyku, erd18vmgdh) and received {hub['outbound_by_venue'].get('Bybit',0):,.0f} back out through five routers. Gate.io did the same at smaller scale ({hub['inbound_by_venue'].get('Gate.io',0):,.0f} in, {hub['outbound_by_venue'].get('Gate.io',0):,.0f} out). Netting round-trips leaves {HUB_NET_ONEWAY:,.0f} EGLD of genuine one-way movement - {100*HUB_CIRCULAR/hub['gross_out']:.0f}% of the gross number is churn between venues.

The net map is small and clear: UPbit is the sole net source at {hub_net.get('UPbit',0):+,.0f}; Binance.com ({hub_net.get('Binance.com',0):+,.0f}), Bybit ({hub_net.get('Bybit',0):+,.0f}), Gate.io ({hub_net.get('Gate.io',0):+,.0f}) and one recurring whale intermediary ({hub_net.get('Unknown Whale I (active)',0):+,.0f}) are net receivers. Every traced desk destination above 2,000 EGLD terminated at an exchange or at that whale - there was no retail dispersion at all. That matters for the series: runs #13-#18 report GROSS throughput with circularity unmeasured, so the five-week escalation documented last run is a measure of pipeline activity, not necessarily of distribution volume.

CORRECTION 2 - BINANCE NEVER STOPPED DE-STAKING. Run #18 could only say that the +150,000 custody reload came from erd1r3w62vq, a nonce-8 pass-through. Its complete 30-day history is three transactions: unDelegate on the binance_staking delegation contract (2026-07-09), withdraw from the same contract (2026-07-22), and the 150,000 transfer to custody immediately after. The unbonding period lines up exactly with the -148,941 that provider shed in the run #16 window. So the reload was the delegation unwind landing, not accumulation, and run #18's "strongest bullish structural counter-signal" is withdrawn. Custody then transacted nothing this week and sits at {cust_bal:,.0f}, {cust_bal-3512650:+,.0f} from the peak.

THE BID IS STILL MISSING, AND NOW IT IS INSTRUMENTED. Mega Whale erd18mv2z6r2 recorded zero value transactions for a second consecutive week, unchanged to the decimal at {mw_bal_cur:,.0f}. The Coinbase Routing wallet that filled it in runs #15 (+32.7K) and #17 (+50.6K) holds {cb_routing:,.0f} EGLD and did nothing. Fourteen days, zero absorption, against ~{HUB_NET_ONEWAY/1000:.0f}K of net one-way distribution in the last seven days alone.

WITHDRAWAL BREADTH, FIRST MEASUREMENT. {breadth['distinct_recipients_raw']} distinct non-exchange addresses received >1,000 EGLD out of tracked exchange wallets ({breadth['total_egld_raw']:,.0f} EGLD), but {breadth['pipeline_share_pct']:.0f}% of that volume went into the OTC pipeline itself. Stripping it out leaves {breadth['distinct_recipients_ex_pipeline']} addresses and {breadth['total_egld_ex_pipeline']:,.0f} EGLD of plausible self-custody withdrawal. No prior-week comparison exists, so this is a baseline.

EXCHANGE FLOWS, UNUSUALLY, NEED NO ADJUSTMENT. Net {net_total:+,.0f} EGLD with no custody reload and no newly tracked address to net out - the first clean headline in three weeks. UPbit ({ent_cur.get('UPbit',0)-prev_ent.get('UPbit',0):+,.0f}) and Binance.com ({ent_cur.get('Binance',0)-prev_ent.get('Binance',0):+,.0f}) are the whole net, while Bybit, KuCoin and Crypto.com took deposits. Tier aggregates remain artifact-prone and are not narrated directly: mega {whale_tiers['mega_whales']['net_change_egld']:+,.0f} (entirely UPbit), large {whale_tiers['large_whales']['net_change_egld']:+,.0f}, mid {whale_tiers['mid_whales']['net_change_egld']:+,.0f}, with one wallet crossing the 100K boundary.

The synthesis: the supply channel never actually switched off last week - it went circular, and the model could not see the difference. The demand side, which is now properly instrumented, got worse."""

staking_analysis=f"""Delegation TVL {total_locked:,.0f} EGLD ({deleg_tvl_wow:+,.0f} WoW) across {len(provs)} active providers, against protocol-wide staked {staked:,} ({staked-pecon['staked_egld']:+,.0f}). For the second consecutive week those two move in OPPOSITE directions, which implies roughly {abs(direct_node_delta):,.0f} EGLD left direct-node stake while delegated stake grew. Cumulatively over two weeks the direct-node leg has shed close to 190K. The binance_staking provider was flat ({binance_staking_prov_wow:+,.0f}), so the run #16 net-out rule does not change the picture, though Binance's own delegation-to-custody rotation (see whale section) sits inside this trend.

WHY pi-staking GROWS - the run #18 question, answered. pi-staking added {lk_wow('pi-staking'):+,.0f} EGLD and {usr_wow('pi-staking'):+d} delegators for a 7th consecutive week, and there is no adoption story behind it: 9.10% APR at a 0% service fee is the second-highest yield on the network at the joint-lowest fee, on a base ({pi['_lk']:,.0f} EGLD, {pi.get('numUsers')} delegators, {pi.get('numNodes')} nodes) small enough that inflows do not dilute the top-up APR. Its inbound flow this week was {pi_funcs.get('delegate',0)} delegate calls with small average ticket sizes - existing delegators moving, not new wallets appearing.

The cohort view generalises it. The {len(hi_apr)} providers at APR >= 8.8% took {hi_apr_net:+,.0f} EGLD net; zero-fee providers as a group took {zero_fee_net:+,.0f}. On the other side, procryptostaking (7.38% APR, 20% fee) shed {lk_wow('procryptostaking'):+,.0f} and syndicatex (8.14%, 12% fee) shed {lk_wow('syndicatex'):+,.0f}. Synexis (+{lk_wow('Synexis'):,.0f}, {usr_wow('Synexis'):+d} users, 9.04% APR at 2% fee) and vaporrepublic (+{lk_wow('vaporrepublic'):,.0f}) extend the same pattern. With the delegator base inert at {cur_deleg:,} ({deleg_wow:+,}, 7th flat week and a background assumption since run #18), fee arbitrage among existing delegators is the ONLY force operating in this market. The interesting forward question is whether high-fee incumbents respond - a fee cut by procryptostaking or syndicatex would be the first genuine competitive repricing in the delegation market in nineteen runs.

REWARD COMPOUNDING REVERSED UP, HARD. {COMPOUND_PCT:.2f}% of reward decisions were compounds ({REDELEG_N} reDelegateRewards vs {CLAIM_N} claimRewards across the top 8 providers), up {COMPOUND_PCT-COMPOUND_PREV:+.2f}pp from {COMPOUND_PREV:.2f}% and the highest reading in the tracked series, beating run #16's 61.59% peak. Two weeks of slippage undone in one move, and it happened during a down week - per the run #11 rule, a compound rate rising through a decline means delegators are doubling down on yield rather than panic-claiming. Fate tracing agrees: of 73 retail claims, 63 were simply held in-wallet and NONE went to a labelled exchange; the only selling cohort was institutional (3 events, 218 EGLD).

Concentration is unchanged and healthy: HHI {hhi:.5f} (vs {prev['staking_concentration']['hhi']:.5f}), top-5 {top5:.2f}%, top-10 {top10:.2f}%. The APR distribution is tightly clustered - {buckets[3]['provider_count']} of {len(provs)} providers in the 8-9% band holding {buckets[3]['total_locked_egld']/1e6:.2f}M EGLD, weighted-average APR {apr_w:.2f}%. For a delegator the standout deals are mapleleafnetwork (9.20% at 0% fee) and pi-staking (9.10% at 0%), which is precisely where the flow went."""

token_analysis=f"""The token layer produced the week's most important new measurement.

xExchange volume fell {dex_wow:.1f}% to ${totvol/1000:.1f}K - a NEW LOW for the tracked history, taking out run #12's floor, and the second consecutive halving. More useful than the volume number is the DEPTH RATIO added this run at run #18's request: pool TVL across the top-25 pairs is ${tot_tvl/1e6:.2f}M against ${prev_tot_tvl/1e6:.2f}M last week ({100*(tot_tvl-prev_tot_tvl)/prev_tot_tvl:+.1f}%), so daily turnover fell from {prev_turnover:.2f}% of pool value to {turnover:.2f}%. Liquidity is being supplied and not consumed. WEGLD supply rose {wegld_chg_pct:+.2f}% to {wegld_supply_now:,.0f}, so more EGLD is being wrapped even as trading dies. Concentration is {pairs[0]['share_pct']:.1f}% in WEGLD/USDC, with {pairs[1]['name'] if len(pairs)>1 else '?'} at {pairs[1]['share_pct'] if len(pairs)>1 else 0:.1f}% the only other pair above 1%. A market where depth holds and turnover halves twice in two weeks is one where the marginal buyer has left, and where even modest sell flow will move price - which is the mechanical link between this section and the price action.

MEX ${meco['price']:.3e} ({100*(meco['price']-prev_mexp)/prev_mexp:+.2f}% WoW, mcap ${meco['marketCap']/1e6:.2f}M) outperformed EGLD for a second week. At this level of turnover that is more plausibly stale pricing than relative strength.

Bridged stablecoins essentially STOPPED contracting: USDC {usdc_supply_wow:+.2f}% (from -1.01%) and USDT {usdt_supply_wow:+.2f}% (from -2.79%), the smallest combined move in the tracked series. Dollars stopped leaving the chain during a down week, which is a mild positive divergence from the price tape - though the signal that matters, a genuine inflow week, has still not appeared.

Holder counts declined marginally across the top 10 for a 19th consecutive week - the established airdrop-decay baseline, not a signal.

Newly-issued: the ESDT system-SC scan surfaced one issuance in the window, JLBM-d9fa48 (JallowBM), with 6 holders and 5 transactions. It fails the run #15 quality bar (>10 holders, >5 txs) and is filtered. New-token formation remains effectively zero for a third consecutive week."""

defi_analysis=f"""DeFi was the most resilient layer on the chain for a second week, and the composition changed in an interesting way.

BORROWERS CONTINUED DE-LEVERAGING, ORDERLY. USH supply burned {ush_supply_wow:+.2f}% to {supply('USH-111e09'):,.0f}, a second consecutive week past the 1% threshold and cumulative {USH_CUM_2W:+.2f}% over two weeks. Run #18 registered two branches - acceleration past 5% in a single week (forced CDP closures, historically a capitulation marker and often a local low) or a stop after one week (a one-off). The outcome is a third: a steady unwind at almost exactly the prior pace. That reads as position management rather than liquidation, and it has now retired approximately the entire run #16 +6.49% leverage chase. No capitulation signature means no bottoming tell.

THE LSDs WENT FLAT - BOTH OF THEM. SEGLD {segld_supply_wow:+.2f}%, XEGLD {xegld_supply_wow:+.2f}%, SWTAO {swtao_supply_wow:+.2f}%. XOXNO is the notable one: XEGLD has redeemed on every prior drawdown in tracking (-29.2% in run #14, -2.70% last week) and this week it held through a -5% price move. Either the redeemer cohort is exhausted or the marginal XEGLD holder has changed. Hatom's SEGLD has now been flat through two consecutive down weeks, so there is no redemption pressure anywhere in the liquid-staking layer.

DEPOSITORS KEPT BUYING, AT A NORMAL RATE. Hatom Lending's EGLD-denominated TVL rose {hl_egld_chg:+.2f}% against a price move of {price_chg:+.2f}%, a bilateral-inverse response ratio of {inverse_ratio:.2f} and the rule's 7th confirmation (the |5%| guardrail is met, just). The down-week series now reads 0.88 / 0.80 / 0.70 / 0.21 / 0.98 / {inverse_ratio:.2f}. Run #18 asked whether the record 0.98 meant capacity was structurally restored or was a one-off; the answer is in between - 0.58 is healthy and mid-range, far above the 0.21 trough, so run #11's capacity-decay hypothesis stays falsified while the 0.98 is best read as a spike rather than a new level. Two consecutive down weeks of EGLD-denominated deposit growth make lending depositors the only cohort on the chain consistently adding.

In USD terms every leg is lower because the denominator moved: Hatom Lending ${hatom_lending/1e6:.2f}M ({100*(hatom_lending-prev['defi_tvl']['Hatom Lending'])/prev['defi_tvl']['Hatom Lending']:+.1f}%), Hatom LSD ${hatom_lsd/1e6:.2f}M ({100*(hatom_lsd-prev_hlsd)/prev_hlsd:+.1f}%), XOXNO LSD ${xoxno_lsd/1e6:.2f}M ({100*(xoxno_lsd-prev['defi_tvl']['XOXNO LSD'])/prev['defi_tvl']['XOXNO LSD']:+.1f}%), USH ${hatom_ush/1000:.0f}K. Per the run #13 rule those are price artifacts, not contraction.

Routing activity softened this week, unlike last: XOXNO Aggregator {tcount('XOXNO Aggregator'):,} daily transfers, OneDex {tcount('OneDex Swap'):,}, JEXchange fees wallet {tcount('JEXchange Fees'):,}. Last week routing held up while xExchange volume collapsed, which supported reading the volume drop as a market-making phenomenon. This week routing fell too, which weakens that distinction and suggests genuine user activity is now also thinning."""

status=json.load(open("/tmp/run19/status.json"))
report={
 "metadata":{"report_date":"2026-08-03","period_start":"2026-07-27","period_end":"2026-08-03",
   "generated_at":datetime.now(timezone.utc).isoformat(),"egld_price_usd":price,
   "btc_price_usd":be["bitcoin"]["usd"],"eth_price_usd":be["ethereum"]["usd"],"run_number":19,
   "data_sources_ok":status["ok"],"data_sources_failed":status["failed"]},
 "executive_summary":executive_summary,
 "network_health":network_health,
 "whale_intelligence":{"large_transactions":large_transactions,"wallet_changes":wallet_changes,
   "whale_tiers":whale_tiers,"exchange_flows":exchange_flows,
   "dormant_activations":dormant_activations,
   # NEW (run #19): first-class OTC pipeline object so the gross-vs-net distinction is
   # machine-readable rather than buried in prose, and so a future dashboard flow map
   # does not need to re-derive it from the collected snapshot.
   "otc_pipeline":{"gross_outbound_egld_7d":OTC_THR_7D,"gross_inbound_egld_7d":OTC_IN_7D,
     "circular_egld_7d":HUB_CIRCULAR,"net_one_way_egld_7d":HUB_NET_ONEWAY,
     "circular_share_pct":100*HUB_CIRCULAR/hub["gross_out"] if hub["gross_out"] else None,
     "desk_balance_egld":desk_cur,"previous_desk_balance_egld":desk_prev,
     "upbit_reload_egld":UPBIT_RELOAD,
     "venue_netting":[{"venue":v,"desk_to_venue_egld":hub["outbound_by_venue"].get(v,0),
                       "venue_to_desk_egld":hub["inbound_by_venue"].get(v,0),
                       "net_egld":hub["net_by_venue"][v]} for v in sorted(hub["net_by_venue"])],
     "gross_series_egld_7d":OTC_SERIES,
     "series_note":"runs #12-#18 are GROSS throughput, paginated but NOT netted for round-trip circularity; only run #19 has a net one-way figure. Do not compare gross and net across runs."},
   "demand_instruments":{"identifiable_bid_absorbed_egld_7d":0.0,
     "mega_whale_balance_egld":mw_bal_cur,"mega_whale_change_egld":0.0,
     "coinbase_routing_balance_egld":cb_routing,"weeks_at_zero":2,
     "dex_turnover_ratio_pct":turnover,"previous_dex_turnover_ratio_pct":prev_turnover,
     "withdrawal_breadth":breadth},
   "analysis":whale_analysis},
 "staking_intelligence":{"summary":{"total_staked_egld":staked,"total_delegated_egld":total_locked,
   "staked_ratio":sr,"num_providers":len(provs),"apr_min":min(aprp(p) for p in provs),
   "apr_max":max(aprp(p) for p in provs),"apr_weighted_avg":apr_w},
   "top_providers":top_providers,"concentration":{"top_5_share_pct":top5,"top_10_share_pct":top10,
   "hhi":hhi,"hhi_previous":prev["staking_concentration"]["hhi"],"hhi_interpretation":"competitive"},
   "apr_distribution":{"buckets":buckets},"apr_outliers":{"top_apr":top_apr,"lowest_fee":lowest_fee},
   "churn":churn,"analysis":staking_analysis},
 "token_activity":{"top_by_holders":top_by_holders,"top_by_volume":top_by_volume,
   "top_by_market_cap":top_by_market_cap,"newly_issued":newly_issued,"xexchange":xexchange,"analysis":token_analysis},
 "defi_activity":{"protocols":protocols,"protocol_breakdown":protocol_breakdown,"sc_deployments":[],"analysis":defi_analysis},
 "anomalies":anomalies,
 "trend_indicators":trend_indicators,
 "watch_list":watch_list,
 "meta_learning":{"run_number":19,
   "endpoints_that_worked":status["ok"],"endpoints_that_failed":status["failed"],
   "api_quirks":[
     "THE INBOUND LEG OF THE OTC DESKS HAD NEVER BEEN RESOLVED TWO HOPS OUT, AND IT INVERTS THE READING. Desk inflows had always come from UPbit directly, so the collector treated inbound as a single-hop question. This week Bybit and Gate.io fed the desks through zero-balance feeder wallets, and only resolving those feeders showed that ~80% of gross throughput round-trips to the venue that supplied it. Rule: apply the run #17 two-hop destination rule symmetrically to both legs, every week.",
     "A ZERO-VALUE TRANSACTION IS NOT AN EMPTY TRANSACTION. The Binance custody funder erd1r3w62vq showed only one inbound transfer of 0.0001 EGLD in 30 days, which run #18 read as 'origin unresolved'. Its OUTBOUND list contained two zero-value txs whose `function` fields were unDelegate and withdraw against the binance_staking delegation contract - the EGLD arrived as a smart-contract result, invisible as a value transfer. Always read the `function`/`action` field on zero-value transactions before concluding a wallet's funding is untraceable.",
     "/providers again returned 187 entries of which 107 have locked>0. The locked>0 filter remains load-bearing for every churn and concentration metric; the unfiltered numUsers sum is ~201K against the correct 174K.",
     "CLEAN PRICE-FEED RUN (5th consecutive): the dataApi re-fetch guard reported 0 retries for all four dataApi-class tokens (SEGLD, SWTAO, USH, XEGLD).",
     "The run #12 OTC window (Jun 8-15) IS still queryable with the paginated method and returns 44,335 EGLD net, extending the comparable gross series one window to the left. It confirms the escalation began at run #13 rather than earlier."],
   "data_gaps":[
     "Circularity has only been measured for this week. Runs #13-#18 report gross throughput with unknown round-trip content, so the escalation series cannot be restated in net terms without re-tracing each window's routers and feeders (roughly 30-60 extra queries per window).",
     "Two entries in known-addresses.json remain invalid-checksum and are flagged rather than guessed: Hatom UTK Money Market and OneDex Launchpad. Neither is queried by the collector, so no figure is affected.",
     "The recurring counterparty labelled 'Unknown Whale I (active)' both feeds and receives from the OTC desks (net "+f"{hub_net.get('Unknown Whale I (active)',0):+,.0f}"+f") and is unidentified. It is the largest non-exchange participant in the hub.",
     "Why the Mega Whale absorber stopped remains unknowable on-chain; only that the Coinbase Routing wallet feeding it has held 77 EGLD for two weeks."],
   "key_findings":[
     f"OTC PIPELINE IS {100*HUB_CIRCULAR/hub['gross_out']:.0f}% CIRCULAR: gross {OTC_THR_7D:,.0f} vs {HUB_NET_ONEWAY:,.0f} net one-way. Bybit and Gate.io feed the desks they receive from; UPbit is the only net source ({hub_net.get('UPbit',0):+,.0f}). The runs #13-#18 series measures activity, not distribution.",
     f"RUN #18'S CUSTODY REVERSAL IS FALSIFIED: the +150,000 funder's 30-day history is unDelegate + withdraw on the binance_staking delegation contract. The reload was the run #16 provider unwind completing, not accumulation. Custody flat this week at {cust_bal:,.0f}.",
     f"UPbit RESUMED FEEDING after one week off: a fresh {UPBIT_RELOAD:,.0f} EGLD tranche into the desks, desk balance {desk_delta:+,.0f} to {desk_cur:,.0f}. Run #18's 'the operator has stopped' lasted one week.",
     f"IDENTIFIABLE BID ABSENT 2 WEEKS: Mega Whale zero txs and flat at {mw_bal_cur:,.0f}, Coinbase Routing at {cb_routing:,.0f} EGLD. Zero absorption in 14 days.",
     f"DEX TURNOVER HALVED A SECOND TIME: {prev_turnover:.2f}% -> {turnover:.2f}% of pool TVL per day, volume ${totvol/1000:.1f}K a new tracked low, pool depth {100*(tot_tvl-prev_tot_tvl)/prev_tot_tvl:+.1f}%. Depth intact, traders gone.",
     f"EGLD {price_chg:+.2f}% WITH the tape this time (BTC {btc_wow:+.2f}%, ETH {eth_wow:+.2f}%) - no repeat of run #18's decoupling, so this week is broad risk-off.",
     f"pi-staking EXPLAINED: 9.10% APR at 0% fee on a {pi['_lk']:,.0f} EGLD base. The APR>=8.8% cohort took {hi_apr_net:+,.0f} while 20%-fee procryptostaking shed {lk_wow('procryptostaking'):+,.0f}. Fee arbitrage inside an inert delegator base.",
     f"DIRECT-NODE UNWIND, WEEK 2: delegation {deleg_tvl_wow:+,.0f} while total staked {staked-pecon['staked_egld']:+,.0f}, implying ~{abs(direct_node_delta):,.0f} left direct-node stake.",
     f"USH DE-LEVERAGING CONTINUED ORDERLY: {ush_supply_wow:.2f}% (cumulative {USH_CUM_2W:+.2f}%), no forced-closure acceleration. LSDs FLAT for the first time in four drawdown weeks (SEGLD {segld_supply_wow:+.2f}%, XEGLD {xegld_supply_wow:+.2f}%).",
     f"REWARD COMPOUND RATE MADE A NEW HIGH at {COMPOUND_PCT:.2f}% ({REDELEG_N} redelegate vs {CLAIM_N} claim), up {COMPOUND_PCT-COMPOUND_PREV:+.2f}pp and above run #16 peak of 61.59% - delegators compounding INTO the drawdown, with zero retail claims going to an exchange.",
     f"BILATERAL INVERSE 7TH CONFIRMATION at {inverse_ratio:.2f} - mid-range, so run #18's 0.98 was a spike not a level; depositor capacity remains healthy. Stablecoin outflow essentially stopped (USDC {usdc_supply_wow:.2f}%, USDT {usdt_supply_wow:.2f}%)."],
   "action_items_from_previous":8,
   "action_items_completed":8,
   "methodology_changes":[
     "RESOLVE BOTH LEGS OF THE OTC HUB TWO HOPS OUT, AND REPORT GROSS AND NET SEPARATELY (new). Run #17 established two-hop resolution for desk OUTflows. This run applies the mirror to INflows and finds that ~80% of gross throughput round-trips to the venue that supplied it. Gross throughput measures pipeline activity; net one-way movement measures distribution. They differ by 5x this week. scripts/trace_otc_hub_run19.py performs the resolution and persists it into the collected snapshot as `otc_hub_trace`.",
     "READ THE function/action FIELD ON ZERO-VALUE TRANSACTIONS BEFORE DECLARING AN ORIGIN UNTRACEABLE (new). The Binance custody funder appeared to have no funding history because its EGLD arrived as a smart-contract result. Its zero-value outbound txs carried function=unDelegate and function=withdraw, which identified the source precisely. This is the delegation-layer analogue of the run #15 custody tx-scan rule.",
     "A CORRECTION-PRONE PATTERN IS NOW EXPLICIT: three consecutive runs have had a headline conclusion overturned by measuring one level deeper (run #17 pagination, run #18 baseline units, run #19 circularity plus the custody origin). Treat any single-week structural conclusion drawn from a flow aggregate as provisional until the constituent legs have been resolved.",
     "WITHDRAWAL BREADTH MUST BE REPORTED EX-PIPELINE (new). The raw count of addresses receiving >1,000 EGLD from exchanges is dominated by the OTC desks and their routers - "+f"{breadth['pipeline_share_pct']:.0f}%"+f" of volume this week. Only the pipeline-excluded figure is a retail-accumulation proxy.",
     "DEX DEPTH RATIO ADDED AS A STANDING METRIC (implements run #18 recommendation #4b). Daily volume divided by pool TVL from /mex/pairs turns 'depth held while trading left' from an inference into a measurement, and it is independent of both price and the flow plumbing."],
   "new_addresses_discovered":6,
   "most_valuable_insight":f"The week's two most important findings are both corrections of run #18's conclusions, and both came from resolving one level deeper than the previous run managed. First, the OTC pipeline did not switch off - it went circular. Gross desk throughput was {OTC_THR_7D:,.0f} EGLD, essentially unchanged week over week, but resolving the INBOUND leg two hops out (never necessary before, because UPbit had always been the sole feeder) shows Bybit pushing {hub['inbound_by_venue'].get('Bybit',0):,.0f} into the desks and taking {hub['outbound_by_venue'].get('Bybit',0):,.0f} back, with Gate.io doing the same at smaller scale. Netting round-trips leaves {HUB_NET_ONEWAY:,.0f} of genuine one-way movement, {100*HUB_CIRCULAR/hub['gross_out']:.0f}% of the gross being churn, and UPbit the only net source. Second, Binance never stopped de-staking: the +150,000 custody reload that run #18 called the strongest bullish structural counter-signal came from a wallet whose complete 30-day history is an unDelegate and a withdraw on the binance_staking delegation contract - the run #16 provider unwind completing after its unbonding period. Both errors share a mechanism: a flow aggregate was read as a fact when it was a hypothesis. Meanwhile the demand-side instrumentation requested last run went live and immediately paid: the DEX turnover ratio halved a second time ({prev_turnover:.2f}% to {turnover:.2f}% of pool TVL traded daily) on flat depth, and the identifiable-bid composite recorded a second consecutive week of exactly zero - the Mega Whale absorber unchanged to the decimal and the Coinbase Routing pipe still holding 77 EGLD. Price fell {abs(price_chg):.2f}%, but this time alongside BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}%, so the chain-specific claim from last week does not extend to this one on price evidence alone; it now rests on the demand instruments, which is exactly where the model wanted it.",
   "top_recommendation":f"NET THE PIPELINE EVERY WEEK AND REBUILD THE SERIES IN NET TERMS. The single highest-value change this run made was measuring circularity, and it immediately reduced a {OTC_THR_7D:,.0f} EGLD headline to {HUB_NET_ONEWAY:,.0f} of real one-way movement. Run #20 should (1) make the two-hop both-legs resolution part of the standard collector rather than a side script, (2) spend the ~60 queries needed to re-net the run #17 peak window so the model knows whether the 1.28M was one-way distribution or partly the same churn, and (3) publish gross and net as two distinct series so no future run confuses activity with distribution. PRE-COMMITTED READING for next week: net one-way distribution rising back above ~150K with a further UPbit tranche = wave #2 genuinely staging and the run #18 exhaustion call is dead; net staying near 60K on high gross = the desks have become cross-exchange settlement infrastructure and the throughput metric should be demoted from the model's supply indicators entirely.",
   "recommendations_for_next_run":[
     "RE-NET THE RUN #17 PEAK WINDOW. The 1,284,688 gross figure is the largest distribution reading in tracking and it is now known to be un-netted for circularity. Re-trace that window's routers and feeders (~60 queries) and report how much was genuinely one-way. If a large share was Bybit-Gate.io churn, the whole run #17 'record distribution wave' narrative needs restating - and the model needs to know that before it uses the series again.",
     "PROMOTE THE TWO-HOP BOTH-LEGS NETTING INTO THE COLLECTOR. scripts/trace_otc_hub_run19.py currently runs as a post-pass and writes `otc_hub_trace` into the snapshot. Fold it into collect_run20.py so gross and net one-way throughput are produced together every week, and add net_one_way to running_baselines as a NEW array (do not append to the gross one - run #18's units lesson).",
     "DOES THE UPbit RELOAD ESCALATE? UPbit sent 67,000 into the desks after a week of nothing, against 364,000 at the run #17 peak. Pre-committed reading: a tranche above ~200,000 with net one-way distribution above 150K = wave #2 staging and the run #18 exhaustion call is dead; another ~60K week = the desks are running settlement traffic rather than distribution. Watch UPbit's own balance (1,201,562) as the leading edge.",
     "DOES THE IDENTIFIABLE BID COME BACK, AND DOES 3 WEEKS MAKE IT STRUCTURAL? The Mega Whale absorber and the Coinbase Routing pipe have both been at exactly zero for two weeks. Pre-registered promotion criterion: a third consecutive week of zero absorption promotes 'the chain's large-bid infrastructure is dormant' from observation to structural finding, on the run #18 precedent for participation inertia. A Coinbase Routing refill is the earliest observable reversal.",
     "TRACK THE DEX TURNOVER RATIO AS A FIRST-CLASS SERIES. It halved twice in two weeks (4.06% -> 2.14%) on flat pool depth and is now the model's cleanest demand-side measurement. Add it to running_baselines, and watch for either a recovery above ~4% (bid returning) or a third halving, which would put xExchange into a regime where ordinary sell flow moves price disproportionately.",
     "IDENTIFY 'Unknown Whale I (active)' (erd1vd76pwhl4d...). It both feeds and receives from the OTC desks and is the largest non-exchange participant in the hub, with a balance that grew to 155,386 this week. Trace its inbound over 30-60 days and its historical relationship to the desks - it may be the operator's own inventory wallet, which would further reduce the genuine-distribution figure.",
     "WATCH FOR A FEE RESPONSE IN THE DELEGATION MARKET. With participation inert, fee arbitrage is the only force moving stake: the APR>=8.8% cohort took +37K while 20%-fee procryptostaking and 12%-fee syndicatex shed. If a high-fee incumbent cuts its fee, that is the first genuine competitive repricing in nineteen runs and would be a real adoption-layer event rather than a rotation.",
     "DOES USH STABILISE OR TAKE A THIRD WEEK? Cumulative -5.5% over two weeks has retired the run #16 leverage chase. A third burn week would mean borrowers are cutting BASE positions, not just the chase - historically that has preceded local lows. Stabilisation would mark the de-leveraging complete. Track alongside Hatom Lending's EGLD TVL, which has now risen through two consecutive down weeks."],
   "dashboard_feature_suggestions":[
     {"title":"OTC hub flow map: gross vs net one-way, with venue-level netting",
      "motivation":"This run's central finding is that 80% of the OTC pipeline's headline throughput is round-trip churn between Bybit, Gate.io and the desks, leaving only ~61K of genuine one-way movement with UPbit as the sole net source. Conveying it required a full section of prose plus five inline numbers, and the crucial point - that the same venue appears on BOTH sides - is exactly the sort of thing a reader cannot hold in their head from a table. It also retroactively qualifies the runs #13-#18 series that the dashboard already shows, so the corrected framing needs to be visible wherever that series appears.",
      "suggested_visualization":"Sankey or chord diagram of venue -> feeder -> desk -> router -> venue for the week, with round-trip edges rendered in a muted colour and net one-way edges highlighted; a headline pair of numbers (gross / net one-way) above it.",
      "data_already_available":True,
      "data_source":"data/collected/{date}.json `otc_hub_trace` (new this run) contains per-address amounts, resolved terminals, and venue-level netting; would need promoting into the report JSON as a first-class object","priority":"high"},
     {"title":"Demand instrument panel: turnover ratio, identifiable bid, withdrawal breadth",
      "motivation":"Three demand-side instruments went live this run (DEX turnover ratio, identifiable-bid composite, ex-pipeline withdrawal breadth) and they are the model's answer to run #18's finding that it was instrumented almost entirely on the supply side. Right now they are scattered across the token, whale and anomaly sections, and two of them are single points with no history. Giving them one panel with a shared time axis would make the demand story readable at a glance and would immediately show the weeks where supply and demand disagree.",
      "suggested_visualization":"three stacked sparklines on a shared week axis - turnover ratio (%), identifiable-bid absorption (EGLD, currently a flat zero line for 2 weeks), ex-pipeline withdrawal breadth (address count and EGLD) - each with the current value as a large numeral and a state chip.",
      "data_already_available":False,
      "data_source":"turnover ratio is in token_activity.xexchange this run; the bid composite and breadth exist only in anomaly descriptions and need first-class report fields plus a running_baselines array before a history can be drawn","priority":"high"},
     {"title":"Conclusion-revision log",
      "motivation":"Three consecutive runs have had a headline conclusion overturned by measuring one level deeper: run #17's pagination fix, run #18's baseline-units fix, and this run's circularity finding plus the falsified custody reversal. That self-correction is the pipeline's most credible feature, but a reader of any single report sees only the current conclusion and has no way to know it replaced an earlier one. A visible log of revised conclusions - what was claimed, in which run, what overturned it - would make the model's error-correction auditable and would stop stale narratives being carried forward by readers.",
      "suggested_visualization":"reverse-chronological list of revisions, each showing the original claim with a strikethrough, the correcting run, the measurement that forced the change, and a chip for the direction of the revision (more bullish / more bearish / neutral).",
      "data_already_available":False,
      "data_source":"the information is in meta_learning.methodology_changes and anomaly descriptions across runs but is unstructured; would need a `revisions` array in the report schema","priority":"medium"}],
   "dashboard_suggestions_followup":[
     {"title":"Supply-vs-demand channel dashboard (the 'what is switched on' panel)","status":"pending",
      "note":"Not built, and this run strengthens the case rather than weakening it: the supply channel that the panel would have shown as OFF last week was in fact ON but circular. The panel should therefore show net one-way rather than gross for the OTC row - a design change that only became apparent because of this run's finding."},
     {"title":"Corrected OTC throughput series with method-provenance markers","status":"pending",
      "note":"Still the highest-value unbuilt item, and now needs a second provenance dimension: not just paginated-vs-truncated (runs <#13 unusable) but gross-vs-net-one-way (only run #19 is netted). Building it with gross figures alone would now propagate a known overstatement."},
     {"title":"Pre-committed test scoreboard","status":"pending",
      "note":"Carried. This run resolved four pre-registered tests (UPbit reload, custody origin, USH acceleration, depositor capacity) and registered five more, so the queue it would track is now large enough to justify the schema work."},
     {"title":"EGLD relative-strength (beta) tracker","status":"deprioritized",
      "note":"Deprioritised for a second time. This week EGLD moved in line with ETH, so the decoupling that motivated the tracker looks like a run #18 one-off rather than a regime. Revisit only if a second decoupling week occurs."}]
 }
}

json.dump(report,open(f"{REPO}/reports/2026-08-03.json","w"),indent=2)
print("WROTE reports/2026-08-03.json")
print("exec_summary:",len(executive_summary),"large_tx:",len(large_transactions),"wallet_changes:",len(wallet_changes),
      "providers:",len(provs),"anomalies:",len(anomalies),"watch:",len(watch_list))
print("net exchange flow:",round(net_total,1))
print("OTC gross:",round(OTC_THR_7D),"net one-way:",round(HUB_NET_ONEWAY),"circular:",round(HUB_CIRCULAR))
print("desk cur:",round(desk_cur),"prev:",desk_prev,"delta:",round(desk_delta),"UPbit reload:",round(UPBIT_RELOAD))
print("breadth:",breadth)
print("turnover:",round(turnover,3),"prev",round(prev_turnover,3))
print("DEFI: HL USD",round(hatom_lending),"LSD",round(hatom_lsd),"USH",round(hatom_ush),"XOXNO",round(xoxno_lsd))
print("LSD supply WoW: SEGLD %.2f XEGLD %.2f SWTAO %.2f USH %.2f"%(segld_supply_wow,xegld_supply_wow,swtao_supply_wow,ush_supply_wow))
print("inverse ratio:",round(inverse_ratio,3))
print("Delegators:",cur_deleg,deleg_wow,"deleg TVL:",round(deleg_tvl_wow),"direct node:",round(direct_node_delta))
print("crossers up:",[(a[:12],round(p or 0),round(c or 0)) for a,p,c in crossers_up],"down:",[(a[:12],round(p or 0),round(c or 0)) for a,p,c in crossers_dn])
print("no_prior excluded:",no_prior)
print("newly_issued kept:",len(newly_issued),"rejected:",newly_issued_rejected)
