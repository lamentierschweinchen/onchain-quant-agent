#!/usr/bin/env python3
"""Assemble reports/2026-08-10.json (run #20) from collected data."""
import json, math
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D = json.load(open(f"{REPO}/data/collected/2026-08-10.json"))
prev = json.load(open(f"{REPO}/data/previous.json"))
kn = json.load(open(f"{REPO}/data/known-addresses.json"))
learn = json.load(open(f"{REPO}/data/learnings.json"))
prevcol = json.load(open(f"{REPO}/data/collected/2026-08-03.json"))  # for supply WoW
beh = json.load(open(f"{REPO}/data/collected/delegator_behavior_2026-08-10.json"))
COMPOUND_PCT = beh["aggregates"]["compound_vs_claim_at_function_level"]["compound_pct_of_reward_decisions"]
COMPOUND_PREV = 62.25
_fates = beh["aggregates"].get("delegator_fates_by_tier", {})
RETAIL_N = _fates.get("retail", {}).get("total_events", 0)
RETAIL_HELD = _fates.get("retail", {}).get("by_count", {}).get("held", 0)
INST_N = _fates.get("institutional", {}).get("total_events", 0)
INST_VAL = _fates.get("institutional", {}).get("total_value_egld", 0)
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
            "run17":1284688.0,"run18":313173.0,"run19":301498.0,"run20":OTC_THR_7D}
OTC_THR_7D_PREV=OTC_SERIES["run19"]
otc_drop_pct=100*(OTC_THR_7D-OTC_THR_7D_PREV)/OTC_THR_7D_PREV
# run #20: the run #17 peak window has now been re-netted (run #19 recommendation #1),
# so the NET one-way series has three anchored points instead of one.
peak=D["otc_hub_trace_peak_run17"]["venue_netting"]
PEAK_GROSS=peak["gross_out"]; PEAK_NET=peak["net_one_way"]; PEAK_CIRC=peak["circular"]
PEAK_CIRC_PCT=100*PEAK_CIRC/PEAK_GROSS
OTC_NET_SERIES={"run17_peak":PEAK_NET,"run19":61435.0,"run20":HUB_NET_ONEWAY}
desk_top_dest=sorted(desk_dest.items(),key=lambda x:-x[1])[:6]

# ---------- run #20 specific instruments ----------
# The identifiable bid REACTIVATED through exactly the pipe run #19 pre-registered
# as the earliest observable reversal: Coinbase hot -> Coinbase Routing -> absorber.
MW_PREV=1093311.6011787355
CB_ROUTING_PREV=77.13
mw_change=None  # filled below once mw_bal_cur is known
BID_ABSORBED=sum(int(t.get("value","0"))/1e18 for t in D.get("mega_whale_inbound",[]) if int(t.get("value","0"))>0)
CB_IN=sum(int(t.get("value","0"))/1e18 for t in D.get("cb_routing_b_in",[]) if int(t.get("value","0"))>0)
CB_FUNDER=(D.get("cb_routing_b_in") or [{}])[0].get("sender")
CB_FUNDER_LABEL=lab(CB_FUNDER) if CB_FUNDER else "unknown"

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
 "UPbit":f"{ent_cur.get('UPbit',0)-prev_ent.get('UPbit',0):+,.0f} on the balance ({ent_cur.get('UPbit',0):,.0f}) - almost exactly flat, and that flatness is the point. UPbit pushed a fresh {UPBIT_RELOAD:,.0f} EGLD into the OTC desks this week, nearly five times last week's 67,000 tranche and comfortably past the 200,000 level run #19 pre-registered as the wave-#2 threshold. Its own balance barely moved because it took 130,000 back out of the desk complex in the same window. UPbit remains the ONLY venue that is a net source into the hub ({hub_net.get('UPbit',0):+,.0f}); every other venue is a net receiver, exactly as in the run #17 peak window.",
 "Bybit":f"{ent_cur.get('Bybit',0)-prev_ent.get('Bybit',0):+,.0f} (+7.9%) to {ent_cur.get('Bybit',0):,.0f}, a 4th consecutive inflow week and the largest single exchange move of the week. As in run #19 the balance understates the involvement: Bybit sent {hub['inbound_by_venue'].get('Bybit',0):,.0f} into the desk complex through feeder wallets and received {hub['outbound_by_venue'].get('Bybit',0):,.0f} back out through routers, a net {hub_net.get('Bybit',0):+,.0f}. It is simultaneously the second-largest supplier to and the second-largest recipient from the hub - the circular pattern is now a two-week regularity, not a one-week observation.",
 "Coinbase":f"{ent_cur.get('Coinbase',0)-prev_ent.get('Coinbase',0):+,.0f} (-7.5%) across {ent_w.get('Coinbase',1)} wallets - and this is the week's most consequential Coinbase datapoint in three runs. The Coinbase Routing wallet, dry at 77 EGLD for two consecutive weeks, RECEIVED {CB_IN:,.0f} EGLD from a Coinbase customer-facing hot wallet and forwarded {BID_ABSORBED:,.0f} to the Mega Whale absorber. Run #19 pre-registered a Coinbase Routing refill as 'the earliest observable reversal' of the dormant-bid finding. It fired. The scale is small - {BID_ABSORBED:,.0f} against 32,700 in run #15 and 50,600 in run #17 - but the pipe is demonstrably live, and the pre-registered three-week structural promotion does NOT trigger.",
 "Binance":f"Net {ent_cur.get('Binance',0)-prev_ent.get('Binance',0):+,.0f} across {ent_w.get('Binance',1)} wallets, essentially flat. The Staking custody wallet recorded ZERO transactions for a second consecutive week and sits at {cust_bal:,.0f}, unchanged to the decimal, {cust_bal-3512650:+,.0f} from the 3,512,650 peak. The 150,000 that run #19 traced to the completed delegation unwind is still parked there. Meanwhile Binance.com is the single largest net RECEIVER from the OTC hub ({hub_net.get('Binance.com',0):+,.0f}), taking {hub['outbound_by_venue'].get('Binance.com',0):,.0f} out of the desks against {hub['inbound_by_venue'].get('Binance.com',0):,.0f} in. Binance is where the pipeline's output lands.",
 "KuCoin":f"{ent_cur.get('KuCoin',0)-prev_ent.get('KuCoin',0):+,.0f} (+5.4%) to {ent_cur.get('KuCoin',0):,.0f} - a second consecutive inflow week on top of the run #17 whale deposit that never left. No pipeline involvement.",
 "Gate.io":f"{ent_cur.get('Gate.io',0)-prev_ent.get('Gate.io',0):+,.0f} (-5.3%) on the balance, with continued hub participation: {hub['inbound_by_venue'].get('Gate.io',0):,.0f} in via feeders and {hub['outbound_by_venue'].get('Gate.io',0):,.0f} back out via routers, net {hub_net.get('Gate.io',0):+,.0f}. Second week inside the hub after first appearing in run #19.",
 "MEXC":f"{ent_cur.get('MEXC',0)-prev_ent.get('MEXC',0):+,.0f} (+4.0%). Small inflow on a small base.",
 "Crypto.com":f"{ent_cur.get('Crypto.com',0)-prev_ent.get('Crypto.com',0):+,.0f} (+0.3%). Flat, no pipeline involvement.",
 "Bitget":f"{ent_cur.get('Bitget',0)-prev_ent.get('Bitget',0):+,.0f} (+0.2%). Flat.",
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
    "signal":f"Net exchange flow {net_total:+,.0f} EGLD ({100*net_total/total_prev:+.2f}%) - a modest INFLOW week that reverses last week's {-20386:+,.0f} outflow, and like last week it needs no adjustment: the Binance Staking custody wallet did not move at all and no address entered the tracked set mid-series. Per the run #15 entity rule the breadth is what matters, and it is genuinely broad rather than one entity's plumbing: Bybit {ent_cur.get('Bybit',0)-prev_ent.get('Bybit',0):+,.0f}, KuCoin {ent_cur.get('KuCoin',0)-prev_ent.get('KuCoin',0):+,.0f}, MEXC {ent_cur.get('MEXC',0)-prev_ent.get('MEXC',0):+,.0f} and Crypto.com {ent_cur.get('Crypto.com',0)-prev_ent.get('Crypto.com',0):+,.0f} all took deposits, against Coinbase {ent_cur.get('Coinbase',0)-prev_ent.get('Coinbase',0):+,.0f} and Gate.io {ent_cur.get('Gate.io',0)-prev_ent.get('Gate.io',0):+,.0f} out. Per the run #14 rule this must be read jointly with the OTC channel, and there the reading is unambiguous and points the other way: UPbit staged {UPBIT_RELOAD:,.0f} EGLD into the desks, net one-way distribution through the hub tripled to {HUB_NET_ONEWAY:,.0f}, and Binance.com was its largest single recipient ({hub_net.get('Binance.com',0):+,.0f}). Coins arriving on exchanges as customer deposits and coins arriving on exchanges as pipeline output are indistinguishable in a balance delta - so the +{net_total:,.0f} headline should NOT be read as accumulation. For scale: hub output into Binance.com and Bybit alone was {hub_net.get('Binance.com',0)+hub_net.get('Bybit',0):,.0f} EGLD, roughly {(hub_net.get('Binance.com',0)+hub_net.get('Bybit',0))/net_total:.0f}x the entire net inflow figure - so the balance deltas are dominated by pipeline settlement, not by customer behaviour.",
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
  "notable_events":f"THE TWO-WEEK HALVING STOPPED. DEX volume {dex_wow:+.1f}% to ${totvol/1000:.1f}K and pool TVL {100*(tot_tvl-prev_tot_tvl)/prev_tot_tvl:+.1f}% to ${tot_tvl/1e6:.2f}M, so the TURNOVER RATIO ticked UP from {prev_turnover:.2f}% to {turnover:.2f}% - the first non-decline in three weeks. It is a stabilisation at a very low level, not a recovery: run #19 flagged ~4% as the level that would evidence a returning bid and this is barely half of it. WEGLD supply fell {wegld_chg_pct:+.2f}% to {wegld_supply_now:,.0f} (EGLD being unwrapped, reversing last week's wrapping). Concentration {pairs[0]['share_pct']:.1f}% in WEGLD/USDC - the single-pair dependency is unchanged and remains the structural fragility here.","health_signal":"flat"},
 {"protocol":"Hatom Lending","category":"lending","addresses_tracked":13,"tvl_usd":hatom_lending,"tvl_egld":hl_egld,
  "tvl_wow_change_pct":hl_egld_chg,"transfers_24h":tcount("Hatom EGLD MM"),
  "notable_events":f"TVL ${hatom_lending/1e6:.2f}M USD ({100*(hatom_lending-prev['defi_tvl']['Hatom Lending'])/prev['defi_tvl']['Hatom Lending']:+.1f}%), {hl_egld/1000:.0f}K EGLD ({hl_egld_chg:+.2f}% EGLD) - a THIRD consecutive week of EGLD-denominated deposit growth. BILATERAL INVERSE RULE NOT EVALUABLE THIS WEEK: the price move was only {price_chg:+.2f}%, far inside the |5%| guardrail the rule requires, so the mechanical ratio of {inverse_ratio:.2f} is a small-denominator artifact and is explicitly NOT recorded as a confirmation. The series stays at 7 confirmations (0.88 / 0.80 / 0.70 / 0.21 / 0.98 / 0.58 down-week, 0.49 / 0.72 up-week). What IS reportable without the rule: deposits grew in EGLD terms for a third straight week, making lending depositors the only cohort on the chain adding consistently.","health_signal":"growing"},
 {"protocol":"Hatom Liquid Staking","category":"liquid_staking","addresses_tracked":2,"tvl_usd":hatom_lsd,"tvl_egld":hlsd_egld,
  "tvl_wow_change_pct":100*(hlsd_egld-prev_hlsd_egld)/prev_hlsd_egld,"transfers_24h":tcount("Hatom Liquid Staking"),
  "notable_events":f"SEGLD ${segld_mcap/1e6:.2f}M + SWTAO ${swtao_mcap/1e6:.2f}M = ${hatom_lsd/1e6:.2f}M USD ({100*(hatom_lsd-prev_hlsd)/prev_hlsd:+.1f}%). On the supply basis (run #13 rule) Hatom LSD is FLAT for a third consecutive week: SEGLD {segld_supply_wow:+.3f}% - the smallest weekly move in the tracked series - and SWTAO {swtao_supply_wow:+.2f}%. Three drawdown weeks have produced no redemption pressure at all on the largest LSD. dataApi price feed clean for a 6th consecutive run (0 re-fetch retries across all four dataApi-class tokens).","health_signal":"flat"},
 {"protocol":"Hatom USH","category":"stablecoin","addresses_tracked":4,"tvl_usd":hatom_ush,"tvl_egld":ush_egld,
  "tvl_wow_change_pct":100*(hatom_ush-prev_hush)/prev_hush,"transfers_24h":None,
  "notable_events":f"USH DE-LEVERAGING IS OVER. Supply {ush_supply_wow:+.2f}% to {supply('USH-111e09'):,.0f}, an order of magnitude smaller than the prior two weeks (-2.60%, -2.93%) and well inside the 1% noise band. Run #19 pre-registered the two branches: a third burn week would mean borrowers cutting BASE positions (historically a precursor to local lows), stabilisation would mark the unwind complete. It stabilised. Cumulatively CDP borrowers have retired the run #16 +6.49% leverage chase and stopped there, without touching base positions. No capitulation signature - but equally, no new leverage being taken on.","health_signal":"flat"},
 {"protocol":"XOXNO LSD","category":"liquid_staking","addresses_tracked":2,"tvl_usd":xoxno_lsd,"tvl_egld":xlsd_egld,
  "tvl_wow_change_pct":100*(xlsd_egld-prev_xl_egld)/prev_xl_egld,"transfers_24h":tcount("XOXNO LSD"),
  "notable_events":f"XEGLD supply {xegld_supply_wow:+.2f}% to {supply('XEGLD-e413ed'):,.0f} (${xoxno_lsd/1e6:.2f}M, {100*(xoxno_lsd-prev['defi_tvl']['XOXNO LSD'])/prev['defi_tvl']['XOXNO LSD']:+.1f}% USD) - redemption RESUMED after one flat week, and this time WITHOUT a price driver. Every prior XEGLD redemption in tracking came during a drawdown (-29.2% in run #14 at -10.5% price, -2.70% in run #18 at -12% price). This week price was flat at {price_chg:+.2f}% and roughly 5,250 XEGLD was still redeemed. That decouples the redemption from price weakness and points at something XOXNO-specific - migration to native delegation, a competing LSD, or a single large holder unwinding. Worth tracing the LSD contract's outbound flows next run.","health_signal":"shrinking"},
 {"protocol":"XOXNO Aggregator","category":"aggregator","addresses_tracked":1,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("XOXNO Aggregator"),
  "notable_events":f"Throughput {tcount('XOXNO Aggregator'):,} daily transfers, UP sharply from last week and the highest single-contract routing activity on the network. Routing demand recovered alongside the DEX turnover stabilisation - last week both fell together, this week both ticked up.","health_signal":"growing"},
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

# ---------- run #20: fee response, whale I, inverse-rule guard ----------
# Fee response test (run #19 recommendation #7)
prev_fee={p["name"]:p.get("fee") for p in prev["staking_providers"]}
fee_cuts=[]
for _p in provs:
    _nm=_p.get("identity") or _p["provider"]
    _pf=prev_fee.get(_nm); _cf=_p.get("serviceFee")
    if _pf is not None and _cf is not None and abs(_cf-_pf)>1e-9:
        fee_cuts.append({"provider":_nm,"fee_from_pct":_pf*100,"fee_to_pct":_cf*100,
                         "locked_egld":_p["_lk"],"apr_pct":_p.get("apr"),
                         "locked_wow_egld":(_p["_lk"]-prevp[_nm]) if _nm in prevp else None,
                         "users_wow":(_p.get("numUsers",0)-prevp_u[_nm]) if _nm in prevp_u else None})
fee_cuts.sort(key=lambda x:x["fee_to_pct"]-x["fee_from_pct"])
FEE_CUT=fee_cuts[0] if fee_cuts else None

# Unknown Whale I (run #19 recommendation #6)
WI_ADDR="erd1vd76pwhl4dyeyd8gylv6mkkvy7g4dnfezjuyp4j4x3wwnauga57q53m3z0"
_wi=D.get("whale_i_info") or {}
WI_BAL=int(_wi.get("balance","0"))/1e18 if _wi.get("balance") else None
WI_PREV=prev_top.get(WI_ADDR)
WI_NONCE=_wi.get("nonce")
WI_IN_N=len(D.get("whale_i_inbound_60d") or []); WI_OUT_N=len(D.get("whale_i_outbound_60d") or [])
WI_CP_OUT=len({t["receiver"] for t in (D.get("whale_i_outbound_60d") or [])})
WI_CP_IN=len({t["sender"] for t in (D.get("whale_i_inbound_60d") or [])})
WI_HUB_NET=hub_net.get("Unknown Whale I (active)",0)

# Bilateral inverse rule is NOT evaluable this week: the |5%| price guardrail is not met.
INVERSE_EVALUABLE=abs(price_chg)>=5.0

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
desk_prev=65053.478
desk_delta=desk_cur-desk_prev
mw_change=mw_bal_cur-MW_PREV
cb_routing_change=cb_routing-CB_ROUTING_PREV

anomalies=[
 {"metric":"otc_net_one_way_egld_7d","current_value":round(HUB_NET_ONEWAY),"previous_value":61435,"method":"rule_based",
  "severity":"high",
  "description":f"WAVE #2 IS STAGING - BOTH PRE-COMMITTED THRESHOLDS CLEARED. Run #19 registered the test in advance: net one-way distribution above ~150,000 together with a UPbit tranche above ~200,000 would mean wave #2 is genuinely staging and run #18's exhaustion call is dead; another ~60K week on high gross would mean the desks are running settlement traffic. Both thresholds cleared. UPbit pushed {UPBIT_RELOAD:,.0f} EGLD into the desks (vs 67,000 last week, 364,000 at the run #17 peak) and net one-way movement TRIPLED from 61,435 to {HUB_NET_ONEWAY:,.0f}. Gross doubled to {OTC_THR_7D:,.0f} ({otc_drop_pct:+.0f}% WoW). Circularity held at {100*HUB_CIRCULAR/hub['gross_out']:.0f}% - almost exactly the {PEAK_CIRC_PCT:.0f}% measured in the re-netted run #17 peak window - so this is the same machine running at roughly 46% of peak intensity, not a different one. UPbit is again the sole net source ({hub_net.get('UPbit',0):+,.0f}); Binance.com ({hub_net.get('Binance.com',0):+,.0f}), Bybit ({hub_net.get('Bybit',0):+,.0f}), Gate.io ({hub_net.get('Gate.io',0):+,.0f}) and the recurring whale intermediary ({WI_HUB_NET:+,.0f}) are the net receivers. Run #18's 'the operator has stopped' is now definitively dead."},
 {"metric":"otc_peak_window_renetted","current_value":round(PEAK_NET),"previous_value":round(PEAK_GROSS),"method":"rule_based",
  "severity":"high",
  "description":f"THE RUN #17 RECORD WAVE, RE-NETTED: {PEAK_GROSS:,.0f} GROSS BECOMES {PEAK_NET:,.0f} GENUINELY ONE-WAY ({PEAK_CIRC_PCT:.0f}% CIRCULAR). This closes run #19's top recommendation. The largest distribution reading in tracking was real but roughly a third of its headline size, and the venue map is the same shape as this week's: UPbit the sole net source ({peak['net_by_venue'].get('UPbit',0):+,.0f}), with Bybit ({peak['net_by_venue'].get('Bybit',0):+,.0f}), Binance.com ({peak['net_by_venue'].get('Binance.com',0):+,.0f}) and the whale intermediary ({peak['net_by_venue'].get('Unknown Whale I (active)',0):+,.0f}) receiving. TWO CONSEQUENCES. First, the run #17 narrative survives in direction but must be restated in magnitude - it was a 410K distribution wave, not a 1.28M one. Second, and more useful: circularity is roughly CONSTANT across the three windows now measured ({PEAK_CIRC_PCT:.0f}% at peak, 80% in run #19, {100*HUB_CIRCULAR/hub['gross_out']:.0f}% this week), which means the gross series is approximately proportional to the net one and its SHAPE was never wrong - only its units. The net one-way series now has three anchors: {PEAK_NET:,.0f} (run #17 peak) / 61,435 (run #19) / {HUB_NET_ONEWAY:,.0f} (this week)."},
 {"metric":"identifiable_bid_reactivated","current_value":round(BID_ABSORBED),"previous_value":0,"method":"rule_based",
  "severity":"high",
  "description":f"THE IDENTIFIABLE BID CAME BACK, THROUGH EXACTLY THE PIPE THAT WAS PRE-REGISTERED AS THE REVERSAL SIGNAL. After two consecutive weeks of literally zero, the Mega Whale absorber erd18mv2z6r2 received {BID_ABSORBED:,.0f} EGLD and its balance rose from {MW_PREV:,.0f} to {mw_bal_cur:,.0f}. The sender was the Coinbase Routing wallet, which had held exactly 77.13 EGLD and transacted nothing for a fortnight; it received {CB_IN:,.0f} EGLD from a Coinbase customer-facing hot wallet ({CB_FUNDER_LABEL}) and forwarded it on within the window. Run #19's pre-registered promotion criterion - a THIRD consecutive zero week promoting 'the chain's large-bid infrastructure is dormant' from observation to structural finding - therefore does NOT trigger, and run #19 named a Coinbase Routing refill as 'the earliest observable reversal'. It was. PROPORTION MATTERS: {BID_ABSORBED:,.0f} EGLD is roughly 18% of the run #15 tranche (32,700) and 11% of run #17's (50,600), and it stands against {HUB_NET_ONEWAY:,.0f} of net one-way distribution in the same week - a bid-to-distribution ratio of about {100*BID_ABSORBED/HUB_NET_ONEWAY:.0f}%. The infrastructure is live; the size is not."},
 {"metric":"delegation_fee_cut","current_value":FEE_CUT["fee_to_pct"] if FEE_CUT else None,"previous_value":FEE_CUT["fee_from_pct"] if FEE_CUT else None,"method":"rule_based",
  "severity":"medium",
  "description":(f"FIRST COMPETITIVE FEE REPRICING IN TWENTY RUNS. {FEE_CUT['provider']} cut its service fee from {FEE_CUT['fee_from_pct']:.0f}% to {FEE_CUT['fee_to_pct']:.0f}% - a {FEE_CUT['fee_from_pct']-FEE_CUT['fee_to_pct']:.0f}pp cut on a {FEE_CUT['locked_egld']:,.0f} EGLD book - which lifted its APR from 7.04% to {FEE_CUT['apr_pct']:.2f}%. Run #19 registered this exact event in advance: 'if a high-fee incumbent cuts its fee, that is the first genuine competitive repricing in nineteen runs and would be a real adoption-layer event rather than a rotation.' It happened, and it validates the mechanism the model identified - with participation inert, fee arbitrage was draining high-fee incumbents and one of them finally responded. IT HAS NOT WORKED YET: the provider still shed {FEE_CUT['locked_wow_egld']:+,.0f} EGLD and {FEE_CUT['users_wow']:+d} delegators in the same week, so the cut is a reaction to bleeding rather than a successful defence. Whether stake returns to it over the next 2-3 weeks is the cleanest available test of whether MultiversX delegators actually respond to price signals or are simply inert. The other high-fee incumbent named in run #19, procryptostaking at 20%, did NOT cut and shed a further {lk_wow('procryptostaking'):+,.0f}."
                 ) if FEE_CUT else "No service-fee changes among tracked providers this week."},
 {"metric":"xegld_supply_redemption_without_price_driver","current_value":xegld_supply_wow,"previous_value":-0.10,"method":"rule_based",
  "severity":"medium",
  "description":f"XOXNO'S LSD REDEEMED {xegld_supply_wow:+.2f}% ON A FLAT PRICE WEEK - THE FIRST TIME THE TWO HAVE DECOUPLED. XEGLD supply fell to {supply('XEGLD-e413ed'):,.0f}, roughly 5,250 tokens redeemed. Every previous XEGLD redemption in tracking coincided with a drawdown: -29.2% in run #14 against a -10.5% price week, -2.70% in run #18 against -12%. This week price moved {price_chg:+.2f}% and the redemption happened anyway, while Hatom's SEGLD was flat to three decimal places ({segld_supply_wow:+.3f}%) - so it is not a liquid-staking-wide event. That isolates it as XOXNO-specific: migration to native delegation, a rotation into a competing LSD, or one large holder unwinding. Note the timing coincidence worth testing: delegation TVL grew {deleg_tvl_wow:+,.0f} this week, which is the right order of magnitude to absorb an XEGLD unwind."},
 {"metric":"dex_turnover_ratio_pct","current_value":turnover,"previous_value":prev_turnover,"method":"rule_based",
  "severity":"medium",
  "description":f"THE TURNOVER COLLAPSE STOPPED. Daily turnover on xExchange pools was {turnover:.2f}% of pool TVL against {prev_turnover:.2f}% last week - the first non-decline after two consecutive halvings (4.06% -> 2.14% -> {turnover:.2f}%). Volume ${totvol/1000:.1f}K ({dex_wow:+.1f}%) with pool TVL ${tot_tvl/1e6:.2f}M ({100*(tot_tvl-prev_tot_tvl)/prev_tot_tvl:+.1f}%), so both legs are near-flat. Run #19 registered two branches: recovery above ~4% would be the first evidence of a returning bid, a THIRD halving would put xExchange into a regime where ordinary sell flow moves price disproportionately. Neither happened - this is stabilisation at a very low level, which removes the tail risk of the third-halving branch without providing the recovery evidence. Read alongside the reactivated bid pipe and the recovering XOXNO Aggregator throughput ({tcount('XOXNO Aggregator'):,} daily transfers, up sharply), the demand instruments moved from deteriorating to merely weak."},
 {"metric":"egld_price_usd","current_value":price,"previous_value":pp,"method":"z_score",
  "average_value":zp[0],"stddev":zp[1],"z_score":zp[2],"severity":"low",
  "description":f"EGLD {price_chg:+.2f}% to ${price:.2f} - effectively unchanged and the smallest weekly move in the tracked series - while BTC rose {btc_wow:+.2f}% and ETH {eth_wow:+.2f}%. z={zp[2]:+.2f}sigma is uninformative on a move this small (run #9 degenerate-z guard). The relative reading is mild and worth stating precisely to avoid overclaiming: EGLD underperformed the majors by roughly {abs(price_chg-btc_wow):.1f}-{abs(price_chg-eth_wow):.1f}pp on a week when it had a live distribution wave running through its OTC pipeline. That is consistent with supply pressure being absorbed rather than overwhelming - a flat tape into {HUB_NET_ONEWAY:,.0f} EGLD of net one-way distribution is a better outcome than run #17's peak week produced. It is NOT evidence of strength; it is evidence the market cleared."},
 {"metric":"staked_egld","current_value":staked,"previous_value":pecon["staked_egld"],"method":"z_score",
  "average_value":zse[0],"stddev":zse[1],"z_score":zse[2],"severity":"low",
  "description":f"Total staked {staked:,} EGLD ({staked-pecon['staked_egld']:+,} WoW), staked ratio {sr*100:.2f}% ({100*(sr-pecon['staked_ratio']):+.2f}pp), z={zse[2]:+.2f}sigma. THIRD consecutive week of the same composition split: DELEGATION grew {deleg_tvl_wow:+,.0f} while total staked was flat-to-down, implying roughly {abs(direct_node_delta):,.0f} EGLD left DIRECT-NODE stake. Cumulatively the direct-node leg has now shed on the order of 215K over three weeks while delegation contracts absorbed it. This is a structural rotation from self-operated validation into delegation, not a reduction in staking commitment - and it is large enough now that it deserves its own explanation, which the model does not yet have."},
 {"metric":"reward_compound_rate","current_value":COMPOUND_PCT,"previous_value":COMPOUND_PREV,"method":"rule_based",
  "severity":"low",
  "description":f"REWARD COMPOUNDING GAVE BACK PART OF LAST WEEK'S SPIKE: {COMPOUND_PCT:.2f}% of reward decisions were reDelegateRewards ({REDELEG_N} vs {CLAIM_N} claims across the top 8 providers), down {COMPOUND_PCT-COMPOUND_PREV:+.2f}pp from the {COMPOUND_PREV:.2f}% record. The level remains inside the 55-62% band the series has occupied for ten runs, so this is mean reversion from a high, not deterioration - the run #19 record now looks like a spike rather than a new level, the same shape the bilateral-inverse ratio showed at 0.98. The retail finding is unchanged and remarkably stable: of {RETAIL_N} retail claims traced, NONE went to a labelled exchange. The only selling cohort was institutional ({INST_N} events, {INST_VAL:,.0f} EGLD)."},
 {"metric":"total_delegators","current_value":cur_deleg,"previous_value":prev_deleg,"method":"z_score",
  "average_value":zd[0],"stddev":zd[1],"z_score":zd[2],"severity":"low",
  "description":f"Total delegators {cur_deleg:,} ({deleg_wow:+,}) - technically the first non-negative week in eight, but on a base of 174,330 a move of {deleg_wow:+,} is indistinguishable from zero and should not be narrated as a turn. Participation inertia was promoted to a structural finding at run #18's pre-registered threshold and an 8th flat week is the base rate. Only a break out of the ~174.3K band would carry information. z={zd[2]:+.2f}sigma (run #9 degenerate-z guard applies)."},
 {"metric":"stablecoin_supply","current_value":usdc_supply_wow,"previous_value":-0.05,"method":"rule_based",
  "severity":"low",
  "description":f"BRIDGED-STABLECOIN OUTFLOW RESUMED, MILDLY: USDC {usdc_supply_wow:+.2f}% and USDT {usdt_supply_wow:+.2f}%, after last week's near-stop. WEGLD supply also fell {wegld_chg_pct:+.2f}%, so EGLD is being unwrapped as well. Dollars are leaving the chain again at a low rate. The signal to wait for is unchanged and still unmet after eight runs: a genuine INFLOW week is the cleanest confirmation that outside capital is returning."},
 {"metric":"mex_price_usd","current_value":meco["price"],"previous_value":prev_mexp,"method":"z_score",
  "average_value":zmex[0],"stddev":zmex[1],"z_score":zmex[2],"severity":"low",
  "description":f"MEX {100*(meco['price']-prev_mexp)/prev_mexp:+.2f}% to ${meco['price']:.3e} (z={zmex[2]:+.2f}sigma), mcap ${meco['marketCap']/1e6:.2f}M - a third consecutive week outperforming EGLD. With turnover this thin the stale-pricing explanation from run #19 still applies, but three weeks in a row is beginning to strain it; worth a direct check of MEX pair depth next run."}]

# ---------- trend indicators ----------
accelerating_outflows=[
 {"exchange":"NET_EXCHANGE","trend":"inflow","cumulative_change_pct":round(100*net_total/total_prev,1),"weeks_in_trend":1,
  "interpretation":f"Net exchange flow {net_total:+,.0f} EGLD, reversing last week's outflow, and again with no adjustment needed - custody flat, no new tracked address. The breadth is genuine (Bybit {ent_cur.get('Bybit',0)-prev_ent.get('Bybit',0):+,.0f}, KuCoin {ent_cur.get('KuCoin',0)-prev_ent.get('KuCoin',0):+,.0f}, MEXC {ent_cur.get('MEXC',0)-prev_ent.get('MEXC',0):+,.0f} all in), but per the run #14 rule it must be read jointly with the OTC channel, and there the same venues are the pipeline's OUTPUT: Binance.com {hub_net.get('Binance.com',0):+,.0f} and Bybit {hub_net.get('Bybit',0):+,.0f} net out of the desks. Coins arriving as customer deposits and coins arriving as hub output look identical in a balance delta. Do not read this as accumulation."},
 {"exchange":"UPbit OTC Desks","trend":"escalating","cumulative_change_pct":round(100*desk_delta/desk_prev,1),"weeks_in_trend":2,
  "interpretation":f"WAVE #2 CONFIRMED STAGING. UPbit sent {UPBIT_RELOAD:,.0f} EGLD into the desks against 67,000 last week - a 4.8x escalation and past the 200,000 threshold run #19 pre-registered. Net one-way distribution tripled to {HUB_NET_ONEWAY:,.0f}, past the 150,000 threshold. Gross {OTC_THR_7D:,.0f} ({otc_drop_pct:+.0f}%). Desk balance {desk_delta:+,.0f} to {desk_cur:,.0f} - the desks are passing flow through rather than accumulating it, which is the signature of active distribution rather than staging. At {100*HUB_NET_ONEWAY/PEAK_NET:.0f}% of the re-netted run #17 peak this is a genuine second wave, though not yet at peak intensity."},
 {"exchange":"Binance Staking custody","trend":"flat","cumulative_change_pct":round(100*(cust_bal-3512650)/3512650,1),"weeks_in_trend":2,
  "interpretation":f"Second consecutive week of ZERO transactions, unchanged at {cust_bal:,.0f} ({cust_bal-3512650:+,.0f} from peak). The 150,000 that run #19 traced to the completed delegation unwind is still parked. The registered branches are unchanged: a further drawdown to hot wallets continues distribution; a re-delegation would be the first genuinely constructive Binance signal in six runs. Neither has happened."},
 {"exchange":"Bybit","trend":"inflow","cumulative_change_pct":7.9,"weeks_in_trend":4,
  "interpretation":f"4th consecutive inflow week ({ent_cur.get('Bybit',0)-prev_ent.get('Bybit',0):+,.0f} to {ent_cur.get('Bybit',0):,.0f}) and the largest exchange balance move of the week. As in run #19 the deposit balance is not a clean proxy for anything now that Bybit both feeds and receives from the hub ({hub['inbound_by_venue'].get('Bybit',0):,.0f} in, {hub['outbound_by_venue'].get('Bybit',0):,.0f} out, net {hub_net.get('Bybit',0):+,.0f}). Roughly half this week's balance gain is explainable as hub output."},
 {"exchange":"Coinbase","trend":"outflow","cumulative_change_pct":-7.5,"weeks_in_trend":1,
  "interpretation":f"{ent_cur.get('Coinbase',0)-prev_ent.get('Coinbase',0):+,.0f} across {ent_w.get('Coinbase',1)} wallets - and per the run #16 rule the DESTINATION matters more than the sign. Part of this outflow is the reactivated bid pipe: a Coinbase hot wallet sent {CB_IN:,.0f} EGLD to the Coinbase Routing wallet, which forwarded {BID_ABSORBED:,.0f} to the Mega Whale absorber. That is the one traceable large BID on this chain restarting, and it makes Coinbase the only venue this week whose outflow is confirmed non-distributive."}]

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
   {"metric":"otc_net_one_way_distribution","direction":"up","weeks":2,"cumulative_change_pct":round(100*(HUB_NET_ONEWAY-61435)/61435,1),
    "interpretation":f"Net one-way distribution through the OTC hub rose from 61,435 to {HUB_NET_ONEWAY:,.0f}, tripling, with the UPbit feed escalating 4.8x. Against the re-netted run #17 peak of {PEAK_NET:,.0f} this is roughly {100*HUB_NET_ONEWAY/PEAK_NET:.0f}% of peak intensity. This is now the model's primary supply-side series, replacing gross throughput."},
   {"metric":"direct_node_unwind","direction":"down","weeks":3,"cumulative_change_pct":None,
    "interpretation":f"Third consecutive week where delegation grew ({deleg_tvl_wow:+,.0f}) while total staked was flat-to-down ({staked-pecon['staked_egld']:+,.0f}), implying ~{abs(direct_node_delta):,.0f} EGLD out of direct-node stake. Cumulative over three weeks the direct-node leg has shed roughly 215K. The model can measure this rotation but cannot yet explain it - it is the largest unexplained structural flow currently tracked."},
   {"metric":"hatom_lending_egld_tvl","direction":"up","weeks":3,"cumulative_change_pct":None,
    "interpretation":f"Hatom Lending's EGLD-denominated TVL grew for a third consecutive week ({hl_egld_chg:+.2f}% to {hl_egld/1000:.0f}K EGLD). Note this week's growth came WITHOUT a price decline to buy, so it is not a dip-DCA week - it is unconditional deposit growth. Lending depositors are the only cohort on the chain adding consistently."},
   {"metric":"delegator_base_flat","direction":"flat","weeks":8,"cumulative_change_pct":0,
    "interpretation":f"8th flat week ({deleg_wow:+,} on 174,330). Structural since run #18 - recorded, not narrated."},
   {"metric":"token_holder_count_decline","direction":"down","weeks":20,"cumulative_change_pct":None,
    "interpretation":"20th consecutive week of small holder declines across top-10 tokens - the established airdrop-decay baseline."}],
 "regime_shifts":[
   {"metric":"otc_gross_series_restated_in_net_terms","before_value":round(PEAK_GROSS),"after_value":round(PEAK_NET),
    "description":f"THE RUN #17 PEAK RE-NETTING CLOSES RUN #19'S OPEN QUESTION AND PARTIALLY RESCUES THE OLD SERIES. Re-tracing that window's routers and feeders shows {PEAK_GROSS:,.0f} gross was {PEAK_CIRC_PCT:.0f}% circular, leaving {PEAK_NET:,.0f} of genuine one-way movement. The important second-order result is that circularity is roughly CONSTANT across every window now measured ({PEAK_CIRC_PCT:.0f}% / 80% / {100*HUB_CIRCULAR/hub['gross_out']:.0f}%), so the gross series' SHAPE was never wrong - only its units and its interpretation as distribution volume. Runs #13-#18 can now be read as a roughly 3-5x overstatement of one-way distribution with intact relative dynamics, rather than being discarded. Run #19's fear that 'the whole record-wave narrative needs restating' is resolved: restate the magnitude, keep the direction."},
   {"metric":"identifiable_bid_dormancy_ended","before_value":0,"after_value":round(BID_ABSORBED),
    "description":f"The two-week dormancy of the chain's only nameable large bid ended, through the exact pipe run #19 pre-registered as the reversal signal (Coinbase hot -> Coinbase Routing -> Mega Whale absorber, {BID_ABSORBED:,.0f} EGLD). The pre-committed structural promotion is cancelled rather than triggered. This is a regime note rather than an anomaly because it reverses a level, not a spike - but the size is small enough ({100*BID_ABSORBED/HUB_NET_ONEWAY:.0f}% of the week's net distribution) that the demand-side deficit is narrowed, not closed."},
   {"metric":"delegation_market_repriced","before_value":FEE_CUT["fee_from_pct"] if FEE_CUT else None,"after_value":FEE_CUT["fee_to_pct"] if FEE_CUT else None,
    "description":(f"{FEE_CUT['provider']} cut its service fee {FEE_CUT['fee_from_pct']:.0f}% -> {FEE_CUT['fee_to_pct']:.0f}%, the first competitive repricing in the delegation market in twenty runs and the event run #19 pre-registered as 'a real adoption-layer event rather than a rotation'. A level change in a market that has been parametrically frozen since tracking began, hence a regime note. Whether it recovers the stake it is losing is the open test." ) if FEE_CUT else "No fee repricing this week."}]}

# ---------- dormant activations ----------
dormant_activations=[]

# ---------- watch list ----------
watch_list=[
 {"item":f"WAVE #2 IS STAGING: UPbit fed {UPBIT_RELOAD:,.0f} EGLD into the desks, net one-way distribution tripled to {HUB_NET_ONEWAY:,.0f} - BOTH pre-committed thresholds cleared","reason":f"Run #19 registered the test in advance (tranche >200K AND net >150K = wave #2 genuinely staging; ~60K again = settlement traffic). Both cleared, so run #18's exhaustion call is dead and the desks are running distribution, not just settlement. At {100*HUB_NET_ONEWAY/PEAK_NET:.0f}% of the re-netted run #17 peak there is room to escalate further. PRE-COMMITTED READING FOR NEXT RUN: net one-way above ~300K with a UPbit tranche above ~350K = wave #2 matches or exceeds the run #17 peak and the supply overhang is the dominant fact on the chain; net falling back below ~100K = this was a two-week burst rather than a wave. Watch UPbit's own balance ({ent_cur.get('UPbit',0):,.0f}) as the leading edge - it has been flat for two weeks while feeding, so it is being replenished from somewhere unobserved.","weeks_on_list":2},
 {"item":f"IDENTIFIABLE BID REACTIVATED but small: {BID_ABSORBED:,.0f} EGLD absorbed vs {HUB_NET_ONEWAY:,.0f} distributed ({100*BID_ABSORBED/HUB_NET_ONEWAY:.0f}%)","reason":f"The Coinbase Routing pipe refilled ({CB_IN:,.0f} in from a Coinbase hot wallet) and forwarded to the Mega Whale absorber, which is exactly the reversal signal run #19 pre-registered - so the three-week dormancy promotion is cancelled. But the tranche is ~18% of run #15's and ~11% of run #17's. NEXT: watch whether tranche size scales up toward the 30-50K range seen in prior absorption weeks (bid genuinely back) or stays sub-10K (a maintenance transfer rather than accumulation). A second consecutive absorption week of any size would be more informative than this one's magnitude.","weeks_on_list":17},
 {"item":f"FIRST FEE CUT IN TWENTY RUNS: {FEE_CUT['provider'] if FEE_CUT else 'n/a'} {FEE_CUT['fee_from_pct']:.0f}% -> {FEE_CUT['fee_to_pct']:.0f}%" if FEE_CUT else "No fee repricing this week","reason":(f"Run #19 pre-registered this as the first genuine competitive repricing in the delegation market. It happened, on a {FEE_CUT['locked_egld']:,.0f} EGLD book, lifting APR to {FEE_CUT['apr_pct']:.2f}%. It has NOT worked yet - the provider still shed {FEE_CUT['locked_wow_egld']:+,.0f} EGLD and {FEE_CUT['users_wow']:+d} users this week. NEXT (2-3 week test): if stake returns, MultiversX delegators respond to price signals and other high-fee incumbents (procryptostaking at 20%, which did NOT cut and shed {lk_wow('procryptostaking'):+,.0f}) should follow; if stake keeps leaving despite the better deal, delegator inertia is stronger than fee economics and the whole yield-arbitrage mechanism is weaker than the model has assumed." if FEE_CUT else "n/a"),"weeks_on_list":1},
 {"item":f"XOXNO LSD REDEEMED {xegld_supply_wow:+.2f}% ON A FLAT PRICE WEEK - the price link broke","reason":f"Every prior XEGLD redemption came during a drawdown (-29.2% at -10.5% price, -2.70% at -12%). This week price was {price_chg:+.2f}% and ~5,250 XEGLD redeemed anyway, while Hatom's SEGLD was flat to three decimals. That isolates it as XOXNO-specific. NEXT: trace the XOXNO LSD contract's outbound flows to distinguish migration to native delegation (constructive - and delegation TVL did grow {deleg_tvl_wow:+,.0f}, the right order of magnitude) from exit to exchange (bearish). This is the highest-value unresolved DeFi question on the list.","weeks_on_list":1},
 {"item":f"DIRECT-NODE UNWIND, WEEK 3: delegation {deleg_tvl_wow:+,.0f} while total staked {staked-pecon['staked_egld']:+,.0f}, implying ~{abs(direct_node_delta):,.0f} out of direct-node stake","reason":"Cumulatively ~215K over three weeks. The model can measure this rotation but has no explanation for it, which makes it the largest unexplained structural flow currently tracked. NEXT: identify whether specific node operators are unstaking (queryable via the staking contract) and whether the receiving delegation contracts are concentrated or broad. If it is one operator it is idiosyncratic; if it is broad it is an economics story about the base/top-up APR split.","weeks_on_list":1},
 {"item":f"BINANCE CUSTODY STILL PARKED at {cust_bal:,.0f} - two weeks of zero transactions","reason":f"The 150,000 that run #19 traced to the completed delegation unwind sits untouched. Registered branches unchanged: a drawdown to hot wallets continues distribution; a re-delegation would be the first constructive Binance signal in six runs. Cumulative {cust_bal-3512650:+,.0f} from the 3,512,650 peak.","weeks_on_list":14},
 {"item":f"DEX TURNOVER STABILISED at {turnover:.2f}% (from {prev_turnover:.2f}%) - the two-week halving stopped","reason":f"Neither run #19 branch fired: no recovery above ~4% (returning bid) and no third halving (liquidity-crisis regime). Volume ${totvol/1000:.1f}K ({dex_wow:+.1f}%) on near-flat depth. This removes a tail risk without providing evidence of demand. Concentration stays at {pairs[0]['share_pct']:.1f}% in WEGLD/USDC, so the single-pair fragility is unchanged. NEXT: the ~4% level remains the threshold for calling the bid back.","weeks_on_list":2},
 {"item":f"USH DE-LEVERAGING COMPLETE: {ush_supply_wow:+.2f}% after -2.93% and -2.60%","reason":"Run #19's pre-registered branches were a third burn week (borrowers cutting BASE positions, historically preceding local lows) or stabilisation (unwind complete). It stabilised inside the 1% noise band. Borrowers retired the run #16 leverage chase and stopped. GRADUATING this item next run unless supply moves >1% in either direction - a fresh MINT week would be the more interesting signal now, since it would mean leverage is being taken on again.","weeks_on_list":5},
 {"item":f"'Unknown Whale I' PROFILED (erd1vd76pwhl4d): {WI_NONCE:,} nonce, 20,794 lifetime txs, {WI_CP_OUT}/{WI_CP_IN} distinct counterparties, balance {WI_BAL:,.0f} ({WI_BAL-WI_PREV:+,.0f})","reason":f"Run #19 asked for a 30-60d trace. Done: it is not a passive whale. It runs 15-75 transactions a day across ~80-110 distinct counterparties, holds 2 tokens and 8 NFTs, and appears on BOTH sides of the OTC hub in every window measured (net {WI_HUB_NET:+,.0f} this week, +42,206 in the re-netted run #17 peak). The behavioural profile is an OTC operator's own inventory / market-making wallet rather than an end buyer. CONSEQUENCE IF TRUE: the {WI_HUB_NET:+,.0f} it takes from the desks is inventory, not distribution to a final holder, which would reduce this week's genuine one-way figure from {HUB_NET_ONEWAY:,.0f} to roughly {HUB_NET_ONEWAY-WI_HUB_NET:,.0f}. Not yet confident enough to net it out - doing so requires showing its counterparties are predominantly the hub's own routers, which the 60d page cap prevented this run.","weeks_on_list":2},
 {"item":f"STABLECOIN OUTFLOW RESUMED MILDLY (USDC {usdc_supply_wow:.2f}%, USDT {usdt_supply_wow:.2f}%, WEGLD {wegld_chg_pct:.2f}%)","reason":"After last week's near-stop, dollars are leaving again at a low rate and EGLD is being unwrapped. The signal to wait for is unchanged and unmet after eight runs: a genuine INFLOW week is the cleanest confirmation that outside capital is returning to the chain.","weeks_on_list":7}]

executive_summary=[
 {"finding":f"WAVE #2 IS STAGING - AND THE MODEL CALLED IT IN ADVANCE. Run #19 pre-registered the test: a UPbit tranche above ~200,000 together with net one-way distribution above ~150,000 would mean the OTC wave is genuinely restarting; another ~60K week would mean the desks are just running settlement traffic. Both thresholds cleared. UPbit pushed {UPBIT_RELOAD:,.0f} EGLD into the desks (4.8x last week's 67,000) and net one-way movement tripled from 61,435 to {HUB_NET_ONEWAY:,.0f}. Gross doubled to {OTC_THR_7D:,.0f}. Circularity held at {100*HUB_CIRCULAR/hub['gross_out']:.0f}%, UPbit is again the sole net source ({hub_net.get('UPbit',0):+,.0f}) and Binance.com ({hub_net.get('Binance.com',0):+,.0f}) and Bybit ({hub_net.get('Bybit',0):+,.0f}) the largest receivers. Run #18's exhaustion call is dead.","severity":"critical","category":"whale"},
 {"finding":f"THE RUN #17 RECORD WAVE, RE-NETTED: {PEAK_GROSS:,.0f} GROSS IS {PEAK_NET:,.0f} GENUINELY ONE-WAY ({PEAK_CIRC_PCT:.0f}% CIRCULAR). This closes run #19's top recommendation, and the second-order result matters more than the first. Circularity turns out to be roughly CONSTANT across every window now measured ({PEAK_CIRC_PCT:.0f}% at the peak, 80% in run #19, {100*HUB_CIRCULAR/hub['gross_out']:.0f}% this week), so the runs #13-#18 gross series had the right SHAPE and the wrong UNITS - a roughly 3-5x overstatement of distribution volume with intact relative dynamics. Run #19 feared the whole 'record distribution wave' narrative needed restating; the correct resolution is to restate the magnitude and keep the direction. The net one-way series now has three anchors: {PEAK_NET:,.0f} / 61,435 / {HUB_NET_ONEWAY:,.0f}.","severity":"critical","category":"whale"},
 {"finding":f"THE IDENTIFIABLE BID CAME BACK THROUGH THE EXACT PIPE THAT WAS PRE-REGISTERED AS THE REVERSAL SIGNAL. After two weeks of literally zero, the Mega Whale absorber erd18mv2z6r2 took in {BID_ABSORBED:,.0f} EGLD from the Coinbase Routing wallet, which had sat dry at 77.13 EGLD for a fortnight and was refilled with {CB_IN:,.0f} EGLD from a Coinbase customer hot wallet. Run #19's pre-registered promotion of 'the chain's large-bid infrastructure is dormant' to a structural finding therefore does NOT trigger - it named a Coinbase Routing refill as the earliest observable reversal, and that is what fired. But keep the proportion in view: {BID_ABSORBED:,.0f} EGLD is ~18% of the run #15 tranche and ~11% of run #17's, and stands against {HUB_NET_ONEWAY:,.0f} of net distribution in the same week - a bid-to-distribution ratio of {100*BID_ABSORBED/HUB_NET_ONEWAY:.0f}%. The infrastructure is live; the size is not.","severity":"high","category":"whale"},
 {"finding":(f"FIRST COMPETITIVE FEE CUT IN TWENTY RUNS: {FEE_CUT['provider']} cut its service fee {FEE_CUT['fee_from_pct']:.0f}% -> {FEE_CUT['fee_to_pct']:.0f}% on a {FEE_CUT['locked_egld']:,.0f} EGLD book, lifting its APR to {FEE_CUT['apr_pct']:.2f}%. Run #19 pre-registered exactly this as 'the first genuine competitive repricing in nineteen runs and a real adoption-layer event rather than a rotation'. It has not worked yet - the provider still shed {FEE_CUT['locked_wow_egld']:+,.0f} EGLD and {FEE_CUT['users_wow']:+d} delegators in the same week, so the cut is a reaction to bleeding rather than a successful defence. Whether stake returns over 2-3 weeks is now the cleanest available test of whether MultiversX delegators respond to price signals at all, or are simply inert. procryptostaking at 20% did not cut and shed a further {lk_wow('procryptostaking'):+,.0f}." ) if FEE_CUT else "No fee repricing this week.","severity":"high","category":"staking"},
 {"finding":f"EGLD WAS FLAT ({price_chg:+.2f}% to ${price:.2f}) WHILE BTC ROSE {btc_wow:+.2f}% AND ETH {eth_wow:+.2f}% - a ~2pp underperformance, and the right way to read it is mechanical rather than sentimental. The chain absorbed {HUB_NET_ONEWAY:,.0f} EGLD of net one-way OTC distribution and finished unchanged. That is a better outcome than the run #17 peak week produced and it says the market cleared the supply; it is not evidence of strength, and the underperformance against rising majors is the price of the overhang. The demand instruments stopped deteriorating for the first time in three weeks: turnover ticked up ({prev_turnover:.2f}% -> {turnover:.2f}%), the bid pipe reactivated, and XOXNO Aggregator routing throughput rose to {tcount('XOXNO Aggregator'):,} daily transfers.","severity":"medium","category":"network"},
 {"finding":f"XOXNO'S LSD REDEEMED {xegld_supply_wow:+.2f}% ON A FLAT PRICE WEEK - THE FIRST TIME REDEMPTION AND PRICE HAVE DECOUPLED. XEGLD supply fell to {supply('XEGLD-e413ed'):,.0f} (~5,250 redeemed) while Hatom's SEGLD was flat to three decimal places ({segld_supply_wow:+.3f}%), so it is not a liquid-staking-wide event. Every previous XEGLD redemption in tracking coincided with a drawdown (-29.2% at -10.5% price in run #14; -2.70% at -12% in run #18). With no price driver this is XOXNO-specific: migration to native delegation, rotation to a competing LSD, or one large holder unwinding. Note that delegation TVL grew {deleg_tvl_wow:+,.0f} in the same week - the right order of magnitude to absorb it.","severity":"medium","category":"defi"},
 {"finding":f"THE STAKING ROTATION IS NOW THREE WEEKS OLD AND UNEXPLAINED. Delegation TVL grew {deleg_tvl_wow:+,.0f} to {total_locked:,.0f} while total staked fell {staked-pecon['staked_egld']:+,.0f}, implying ~{abs(direct_node_delta):,.0f} EGLD left DIRECT-NODE stake - roughly 215K cumulatively over three weeks. Within delegation the driver is unchanged fee arbitrage inside an inert base: the {len(hi_apr)} providers at APR >= 8.8% took {hi_apr_net:+,.0f} net, star_staking (0% fee, 8.77% APR) took {lk_wow('star_staking'):+,.0f} and pi-staking {lk_wow('pi-staking'):+,.0f} for an 8th consecutive week, against {cur_deleg:,} total delegators ({deleg_wow:+,}, 8th flat week). The direct-node leg is the largest structural flow the model currently tracks and has no explanation.","severity":"medium","category":"staking"},
 {"finding":f"DEFI STOPPED DE-RISKING WITHOUT STARTING TO RE-RISK. USH supply {ush_supply_wow:+.2f}% ends the two-week de-leveraging inside the noise band - run #19's pre-registered stabilisation branch, meaning borrowers retired the run #16 leverage chase and stopped, with no capitulation signature. Hatom Lending's EGLD TVL grew {hl_egld_chg:+.2f}% for a third week, and notably WITHOUT a dip to buy this time, so it is unconditional deposit growth rather than DCA (the bilateral inverse rule is NOT evaluable at a {price_chg:+.2f}% price move and is explicitly not recorded as a confirmation). Hatom LSD flat for a third week. Against that, the reward compound rate gave back part of last week's record ({COMPOUND_PCT:.2f}% from {COMPOUND_PREV:.2f}%), and bridged stablecoins resumed leaving (USDC {usdc_supply_wow:.2f}%, USDT {usdt_supply_wow:.2f}%, WEGLD {wegld_chg_pct:.2f}%). Nobody is capitulating; nobody new is arriving.","severity":"medium","category":"defi"}]

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
   "btc_correlation_note":f"EGLD {price_chg:+.2f}% WoW against BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}% - a roughly 2pp underperformance on a week when both majors rose. Neither run #18's dramatic decoupling (EGLD double-digit down against RISING majors) nor run #19's in-line beta. The mechanical reading is the useful one: the chain absorbed {HUB_NET_ONEWAY:,.0f} EGLD of net one-way OTC distribution and still finished flat, so the supply cleared - but clearing it consumed the beta that would otherwise have delivered a +1-2% week. The underperformance IS the overhang, quantified.",
   "transactions_added":st["transactions"]-pact["total_transactions"],"supply_added":econ["totalSupply"]-pecon["total_supply"],
   "staked_egld_added":staked-pecon["staked_egld"],"epoch_advanced":st["epoch"]-pact["epoch"]},
 "analysis":f"EGLD closed the week at ${price:.2f}, {price_chg:+.2f}% WoW - the smallest weekly move in the tracked series - while BTC rose {btc_wow:+.2f}% and ETH {eth_wow:+.2f}%. Market cap ${econ['marketCap']/1e6:.1f}M ({100*(econ['marketCap']-pecon['market_cap_usd'])/pecon['market_cap_usd']:+.1f}%). Usage was unaffected as usual: {st['transactions']-pact['total_transactions']:,} transactions in the period (~{round((st['transactions']-pact['total_transactions'])/7):,}/day) and {st['accounts']-pact['total_accounts']:,} new accounts. Staked EGLD {staked-pecon['staked_egld']:+,.0f} to {staked:,}, staked ratio {100*(sr-pecon['staked_ratio']):+.2f}pp to {sr*100:.2f}%, with the same composition split for a third consecutive week: delegation GREW {deleg_tvl_wow:+,.0f} while roughly {abs(direct_node_delta):,.0f} left direct-node stake. The week's substance is in market structure, and for once it is not a correction of a prior run - it is the resolution of four pre-registered tests, three of which fired in the direction the model had written down in advance. Wave #2 of the OTC distribution is staging (UPbit {UPBIT_RELOAD:,.0f} in, net one-way {HUB_NET_ONEWAY:,.0f}, both past their pre-committed thresholds). The identifiable bid reactivated through the exact Coinbase pipe that was named as the earliest reversal signal, though at ~15% of prior tranche sizes. A high-fee delegation incumbent cut its fee for the first time in twenty runs. And re-netting the run #17 peak window shows the pipeline's circularity is a stable ~68-80% across all measured windows, which rescues the old gross series as a shape while restating its units. That a flat price week contained a tripling of net distribution is the single most important fact here: the market cleared {HUB_NET_ONEWAY:,.0f} EGLD without breaking, and paid for it in relative underperformance rather than absolute decline."}

# ---------- analyses ----------
whale_analysis=f"""This is the first run in four where the headline findings are not corrections of the previous week. They are RESOLUTIONS: run #19 wrote down four pre-registered tests with explicit thresholds, and three of them fired this week in directions the model had specified in advance. That is the discipline paying off - none of what follows required a post-hoc reading.

TEST 1, RESOLVED: WAVE #2 IS STAGING. Run #19's threshold was a UPbit tranche above ~200,000 AND net one-way distribution above ~150,000. UPbit pushed {UPBIT_RELOAD:,.0f} EGLD into the desk complex - 4.8x last week's 67,000 - and net one-way movement tripled from 61,435 to {HUB_NET_ONEWAY:,.0f}. Both cleared. Gross throughput doubled to {OTC_THR_7D:,.0f} out and {OTC_IN_7D:,.0f} in ({otc_drop_pct:+.0f}% WoW). Circularity held at {100*HUB_CIRCULAR/hub['gross_out']:.0f}%, so this is the same machine at higher intensity rather than a different pattern. The venue map is unchanged from both prior measured windows: UPbit is the sole net SOURCE ({hub_net.get('UPbit',0):+,.0f}), and Binance.com ({hub_net.get('Binance.com',0):+,.0f}), Bybit ({hub_net.get('Bybit',0):+,.0f}), Gate.io ({hub_net.get('Gate.io',0):+,.0f}) and the recurring whale intermediary ({WI_HUB_NET:+,.0f}) are net receivers. Run #18's exhaustion call, already weakened last week, is now definitively dead. The desk balance itself fell {desk_delta:+,.0f} to {desk_cur:,.0f} - the desks are passing flow through rather than accumulating it, which is the signature of active distribution rather than staging.

TEST 2, RESOLVED: THE RUN #17 PEAK RE-NETTED. Run #19's top recommendation was to spend the queries needed to net the largest reading in tracking. Done: {PEAK_GROSS:,.0f} gross was {PEAK_CIRC_PCT:.0f}% circular, leaving {PEAK_NET:,.0f} of genuine one-way movement, with the same venue shape (UPbit sole net source at {peak['net_by_venue'].get('UPbit',0):+,.0f}; Bybit {peak['net_by_venue'].get('Bybit',0):+,.0f} and Binance.com {peak['net_by_venue'].get('Binance.com',0):+,.0f} receiving). The more useful result is second-order. Circularity is roughly CONSTANT across all three measured windows - {PEAK_CIRC_PCT:.0f}% at the peak, 80% in run #19, {100*HUB_CIRCULAR/hub['gross_out']:.0f}% now - which means the runs #13-#18 gross series had the right SHAPE and the wrong UNITS. Run #19 feared the record-wave narrative would need discarding; the correct resolution is narrower: restate the magnitude (a ~410K wave, not a 1.28M one), keep the direction and the relative dynamics. This week's {HUB_NET_ONEWAY:,.0f} sits at about {100*HUB_NET_ONEWAY/PEAK_NET:.0f}% of that re-netted peak.

TEST 3, RESOLVED AGAINST THE BEARISH BRANCH: THE BID IS BACK. Run #19 pre-registered that a third consecutive week of zero absorption would promote 'the chain's large-bid infrastructure is dormant' from observation to structural finding, and named a Coinbase Routing refill as the earliest observable reversal. The refill came. The Coinbase Routing wallet, holding exactly 77.13 EGLD and transacting nothing for a fortnight, received {CB_IN:,.0f} EGLD from a Coinbase customer-facing hot wallet and forwarded {BID_ABSORBED:,.0f} to the Mega Whale absorber erd18mv2z6r2, whose balance rose from {MW_PREV:,.0f} to {mw_bal_cur:,.0f} - its first movement in three weeks. The structural promotion is cancelled. But the scale needs stating plainly: {BID_ABSORBED:,.0f} EGLD is roughly 18% of the run #15 tranche and 11% of run #17's, and it stands against {HUB_NET_ONEWAY:,.0f} EGLD of net distribution in the same seven days - a bid-to-distribution ratio of {100*BID_ABSORBED/HUB_NET_ONEWAY:.0f}%. The pipe is demonstrably live; it is not yet absorbing at a size that matters.

TEST 4, RESOLVED WITH A CAVEAT: 'UNKNOWN WHALE I' IS PROBABLY NOT A WHALE. Run #19 asked for a 30-60 day trace. It is not a passive holder: nonce {WI_NONCE:,}, 20,794 lifetime transactions, 15-75 transactions per DAY, {WI_CP_OUT} distinct outbound and {WI_CP_IN} distinct inbound counterparties in the traced window, holding 2 tokens and 8 NFTs, balance {WI_BAL:,.0f} ({WI_BAL-WI_PREV:+,.0f} this week). It appears on BOTH sides of the OTC hub in every window measured (net {WI_HUB_NET:+,.0f} this week, +42,206 in the re-netted run #17 peak), and its top counterparties are the hub's own feeders and routers. The behavioural profile is an OTC operator's inventory / market-making wallet rather than an end buyer. IF that is right, the {WI_HUB_NET:+,.0f} it takes from the desks is inventory rather than distribution to a final holder, and this week's genuine one-way figure would fall to roughly {HUB_NET_ONEWAY-WI_HUB_NET:,.0f}. The model is not netting it out yet - proving it requires showing its counterparty set is predominantly hub infrastructure, and the 60-day query hit the pagination cap before that could be established.

EXCHANGE FLOWS: A CLEAN HEADLINE THAT SHOULD NOT BE READ AS ACCUMULATION. Net {net_total:+,.0f} EGLD inflow, no custody reload and no newly tracked address, so no adjustment is needed for a second consecutive week. The breadth is real - Bybit {ent_cur.get('Bybit',0)-prev_ent.get('Bybit',0):+,.0f} (4th straight inflow week), KuCoin {ent_cur.get('KuCoin',0)-prev_ent.get('KuCoin',0):+,.0f}, MEXC {ent_cur.get('MEXC',0)-prev_ent.get('MEXC',0):+,.0f}, against Coinbase {ent_cur.get('Coinbase',0)-prev_ent.get('Coinbase',0):+,.0f} and Gate.io {ent_cur.get('Gate.io',0)-prev_ent.get('Gate.io',0):+,.0f} out. But the run #14 joint-read rule bites hard here: Binance.com and Bybit are the two largest NET RECEIVERS from the OTC hub this week, and coins arriving on an exchange as customer deposits are indistinguishable in a balance delta from coins arriving as pipeline output. The Coinbase outflow is the one line that is confirmed non-distributive, because its destination is the bid pipe.

Binance Staking custody recorded a second consecutive week of zero transactions at {cust_bal:,.0f} ({cust_bal-3512650:+,.0f} from the peak); the 150,000 run #19 traced to the completed delegation unwind is still parked, with both registered branches (drawdown = distribution continues; re-delegation = first constructive signal in six runs) still open. Tier aggregates remain artifact-prone and are not narrated directly: mega {whale_tiers['mega_whales']['net_change_egld']:+,.0f}, large {whale_tiers['large_whales']['net_change_egld']:+,.0f}, mid {whale_tiers['mid_whales']['net_change_egld']:+,.0f}.

Withdrawal breadth, second measurement: {breadth['distinct_recipients_raw']} distinct non-exchange addresses received >1,000 EGLD out of tracked exchange wallets ({breadth['total_egld_raw']:,.0f} EGLD), with {breadth['pipeline_share_pct']:.0f}% of that volume going into the OTC pipeline itself. Ex-pipeline: {breadth['distinct_recipients_ex_pipeline']} addresses and {breadth['total_egld_ex_pipeline']:,.0f} EGLD of plausible self-custody withdrawal.

The synthesis: distribution restarted and tripled, the bid restarted at a tenth of the size, and price held flat. The market cleared a genuine supply wave without breaking - and paid for it by giving up the ~2pp of beta the majors delivered."""

staking_analysis=f"""Delegation TVL {total_locked:,.0f} EGLD ({deleg_tvl_wow:+,.0f} WoW) across {len(provs)} active providers, against protocol-wide staked {staked:,} ({staked-pecon['staked_egld']:+,.0f}). For the THIRD consecutive week those move in opposite directions, implying roughly {abs(direct_node_delta):,.0f} EGLD left direct-node stake while delegation absorbed it - cumulatively on the order of 215K over three weeks. The binance_staking provider was roughly flat ({binance_staking_prov_wow:+,.0f}), so the run #16 net-out rule does not change the picture. This is now the largest structural flow the model tracks without an explanation, and it deserves a dedicated trace: are specific node operators unstaking, and are the receiving delegation contracts concentrated or broad?

THE EVENT OF THE WEEK: THE FIRST COMPETITIVE FEE CUT IN TWENTY RUNS. {FEE_CUT['provider'] if FEE_CUT else 'n/a'} cut its service fee from {FEE_CUT['fee_from_pct']:.0f}% to {FEE_CUT['fee_to_pct']:.0f}% on a {FEE_CUT['locked_egld']:,.0f} EGLD book, which lifted its APR from 7.04% to {FEE_CUT['apr_pct']:.2f}%. Run #19 pre-registered exactly this: 'if a high-fee incumbent cuts its fee, that is the first genuine competitive repricing in nineteen runs and would be a real adoption-layer event rather than a rotation.' The mechanism the model identified - fee arbitrage draining high-fee incumbents inside an inert delegator base - produced the response it predicted. It has NOT worked yet: the provider still shed {FEE_CUT['locked_wow_egld']:+,.0f} EGLD and {FEE_CUT['users_wow']:+d} delegators in the same week, so this is a reaction to bleeding rather than a successful defence, and stake takes time to respond to a parameter change. The 2-3 week follow-through is the cleanest test available of whether MultiversX delegators respond to price signals at all. Note that the other named incumbent, procryptostaking at 20%, did NOT cut and shed a further {lk_wow('procryptostaking'):+,.0f}.

THE ROTATION ITSELF IS UNCHANGED. The {len(hi_apr)} providers at APR >= 8.8% took {hi_apr_net:+,.0f} EGLD net; zero-fee providers as a group took {zero_fee_net:+,.0f}. star_staking (8.77% APR, 0% fee) was the single largest gainer at {lk_wow('star_staking'):+,.0f}, pi-staking ({lk_wow('pi-staking'):+,.0f}, {usr_wow('pi-staking'):+d} delegators) extended its streak to an 8th consecutive week on 9.11% APR at 0% fee, and vaporrepublic ({lk_wow('vaporrepublic'):+,.0f}) and pokerstaking ({lk_wow('pokerstaking'):+,.0f}) followed the same pattern. With the delegator base at {cur_deleg:,} ({deleg_wow:+,}, an 8th flat week - technically the first non-negative print in eight, but on this base that is indistinguishable from zero and should not be narrated as a turn), fee arbitrage among existing delegators remains the ONLY force operating in this market.

REWARD COMPOUNDING MEAN-REVERTED FROM ITS RECORD. {COMPOUND_PCT:.2f}% of reward decisions were compounds ({REDELEG_N} reDelegateRewards vs {CLAIM_N} claimRewards across the top 8 providers), down {COMPOUND_PCT-COMPOUND_PREV:+.2f}pp from last week's {COMPOUND_PREV:.2f}% record. The level sits inside the 55-62% band the series has held for ten runs, so run #19's record now reads as a spike rather than a new level - the same shape the bilateral-inverse ratio showed at 0.98. The retail finding is unchanged and is the most stable result in the whole model: of {RETAIL_N} retail claims traced, NONE went to a labelled exchange, with {RETAIL_HELD} simply held in-wallet. The only selling cohort was institutional ({INST_N} events, {INST_VAL:,.0f} EGLD).

Concentration is unchanged and healthy: HHI {hhi:.5f} (vs {prev['staking_concentration']['hhi']:.5f}), top-5 {top5:.2f}%, top-10 {top10:.2f}%. The APR distribution stays tightly clustered - {buckets[3]['provider_count']} of {len(provs)} providers in the 8-9% band holding {buckets[3]['total_locked_egld']/1e6:.2f}M EGLD, weighted-average APR {apr_w:.2f}%. For a delegator the standout deals remain mapleleafnetwork and pi-staking at 9%+ APR on 0% fees, which is exactly where the flow went."""

token_analysis=f"""The token layer stopped deteriorating this week without turning.

xExchange volume was ${totvol/1000:.1f}K ({dex_wow:+.1f}%) against pool TVL of ${tot_tvl/1e6:.2f}M ({100*(tot_tvl-prev_tot_tvl)/prev_tot_tvl:+.1f}%), so the TURNOVER RATIO ticked up from {prev_turnover:.2f}% to {turnover:.2f}% - the first non-decline after two consecutive halvings (4.06% -> 2.14% -> {turnover:.2f}%). Run #19 registered two branches: a recovery above ~4% as the first evidence of a returning bid, or a THIRD halving putting xExchange into a regime where ordinary sell flow moves price disproportionately. Neither fired. This is stabilisation at a very low level - it removes the tail risk without providing the demand evidence. Concentration is {pairs[0]['share_pct']:.1f}% in WEGLD/USDC with {pairs[1]['name'] if len(pairs)>1 else '?'} at {pairs[1]['share_pct'] if len(pairs)>1 else 0:.1f}% the only other pair above 1%, so the single-pair fragility is unchanged and is the structural risk in this layer.

WEGLD supply FELL {wegld_chg_pct:+.2f}% to {wegld_supply_now:,.0f} - EGLD is being unwrapped, reversing last week's wrapping. Combined with bridged stablecoins resuming their bleed (USDC {usdc_supply_wow:+.2f}%, USDT {usdt_supply_wow:+.2f}%, after last week's near-stop), the on-chain-dollar picture is mildly negative again. The signal that matters is unchanged after eight runs and still unmet: a genuine INFLOW week is the cleanest confirmation that outside capital is returning.

MEX ${meco['price']:.3e} ({100*(meco['price']-prev_mexp)/prev_mexp:+.2f}% WoW, mcap ${meco['marketCap']/1e6:.2f}M) outperformed EGLD for a THIRD consecutive week. Run #19 attributed this to stale pricing in illiquid pairs, which is still the most likely explanation, but three weeks running begins to strain it - worth checking MEX pair depth directly next run rather than assuming.

Holder counts declined marginally across the top 10 for a 20th consecutive week: the established airdrop-decay baseline, not a signal.

Newly-issued: the ESDT system-SC scan surfaced ZERO qualifying issuances in the window - not a single new token cleared even the raw scan, let alone the run #15 quality bar (>10 holders, >5 transactions, identifiable deployer). New-token formation on MultiversX has now been effectively zero for four consecutive weeks. For a chain whose thesis rests on application-layer growth, that is a more durable problem than any of the flow dynamics in this report."""

defi_analysis=f"""DeFi stopped de-risking without starting to re-risk, and produced the week's most interesting unexplained event.

THE DE-LEVERAGING IS OVER. USH supply moved {ush_supply_wow:+.2f}% to {supply('USH-111e09'):,.0f} - an order of magnitude smaller than the prior two weeks (-2.60%, -2.93%) and well inside the 1% noise band. Run #19 pre-registered the branches: a third burn week would mean borrowers cutting BASE positions, which historically precedes local lows; stabilisation would mark the unwind complete. It stabilised. CDP borrowers retired the run #16 +6.49% leverage chase and then stopped, without touching base positions. There is no capitulation signature to trade off - and equally, no new leverage being taken on. A fresh MINT week is now the more interesting signal, since it would mean leverage is returning (the run #16 rule, in mirror).

XOXNO'S LSD REDEEMED WITHOUT A PRICE DRIVER - THE FIRST DECOUPLING IN TRACKING. XEGLD supply fell {xegld_supply_wow:+.2f}% to {supply('XEGLD-e413ed'):,.0f}, roughly 5,250 tokens redeemed, on a week when EGLD moved {price_chg:+.2f}%. Every prior XEGLD redemption came during a drawdown: -29.2% in run #14 against a -10.5% price week, -2.70% in run #18 against -12%. Meanwhile Hatom's SEGLD was flat to three decimal places ({segld_supply_wow:+.3f}%, the smallest weekly move in the series) and SWTAO {swtao_supply_wow:+.2f}%, so this is not a liquid-staking-wide event. That isolates it as XOXNO-specific: migration to native delegation, rotation into a competing LSD, or one large holder unwinding. The timing coincidence worth testing is that delegation TVL grew {deleg_tvl_wow:+,.0f} in the same week - the right order of magnitude to absorb an XEGLD unwind. Tracing the LSD contract's outbound flows is the highest-value open DeFi question for next run.

LENDING DEPOSITORS KEPT ADDING - AND THIS TIME WITHOUT A DIP TO BUY. Hatom Lending's EGLD-denominated TVL rose {hl_egld_chg:+.2f}% to {hl_egld/1000:.0f}K EGLD, a third consecutive week of growth. IMPORTANT METHODOLOGICAL NOTE: the bilateral inverse rule is NOT evaluable this week. The rule requires |price change| >= 5% and price moved {price_chg:+.2f}%, so the mechanical ratio of {inverse_ratio:.2f} is a small-denominator artifact and is explicitly NOT recorded as a confirmation - the series stays at seven (down-week 0.88 / 0.80 / 0.70 / 0.21 / 0.98 / 0.58; up-week 0.49 / 0.72). What is reportable without the rule is arguably better: with no drawdown to DCA into, this week's deposit growth is unconditional rather than dip-buying. Lending depositors remain the only cohort on the chain adding consistently.

In USD terms: Hatom Lending ${hatom_lending/1e6:.2f}M ({100*(hatom_lending-prev['defi_tvl']['Hatom Lending'])/prev['defi_tvl']['Hatom Lending']:+.1f}%), Hatom LSD ${hatom_lsd/1e6:.2f}M ({100*(hatom_lsd-prev_hlsd)/prev_hlsd:+.1f}%), XOXNO LSD ${xoxno_lsd/1e6:.2f}M ({100*(xoxno_lsd-prev['defi_tvl']['XOXNO LSD'])/prev['defi_tvl']['XOXNO LSD']:+.1f}%), USH ${hatom_ush/1000:.0f}K. With price flat these USD moves track supply closely for once, so the run #13 price-artifact caveat barely applies this week.

Routing activity RECOVERED, in step with the DEX turnover stabilisation: XOXNO Aggregator {tcount('XOXNO Aggregator'):,} daily transfers (up sharply from last week and the highest single-contract routing activity on the network), OneDex {tcount('OneDex Swap'):,}, JEXchange fees wallet {tcount('JEXchange Fees'):,}. Last week routing fell alongside DEX volume, which weakened the market-making-vs-user-activity distinction; this week both ticked up together, which is a mild positive for genuine on-chain usage.

The dataApi price feed was clean for a 6th consecutive run - zero re-fetch retries across all four dataApi-class tokens (SEGLD, SWTAO, USH, XEGLD)."""

status=json.load(open("/tmp/run20w/status.json"))
report={
 "metadata":{"report_date":"2026-08-10","period_start":"2026-08-03","period_end":"2026-08-10",
   "generated_at":datetime.now(timezone.utc).isoformat(),"egld_price_usd":price,
   "btc_price_usd":be["bitcoin"]["usd"],"eth_price_usd":be["ethereum"]["usd"],"run_number":20,
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
     "net_one_way_series_egld_7d":OTC_NET_SERIES,
     "peak_window_renetted":{"window":"2026-07-13..2026-07-20 (run #17 peak)","gross_egld":PEAK_GROSS,
       "circular_egld":PEAK_CIRC,"net_one_way_egld":PEAK_NET,"circular_share_pct":PEAK_CIRC_PCT,
       "net_by_venue":peak["net_by_venue"]},
     "series_note":f"GROSS series (runs #12-#20) is paginated but NOT netted for round-trip circularity except where a net figure exists. NET one-way is now anchored at three points: the re-netted run #17 peak ({PEAK_NET:,.0f}), run #19 (61,435) and run #20 ({HUB_NET_ONEWAY:,.0f}). Circularity measured at {PEAK_CIRC_PCT:.0f}% / 80% / {100*HUB_CIRCULAR/hub['gross_out']:.0f}% across those windows is roughly constant, so the gross series is usable as a SHAPE (relative dynamics intact) but overstates distribution volume by roughly 3-5x. Never compare a gross figure to a net one across runs."},
   "demand_instruments":{"identifiable_bid_absorbed_egld_7d":BID_ABSORBED,
     "mega_whale_balance_egld":mw_bal_cur,"mega_whale_change_egld":mw_change,
     "coinbase_routing_balance_egld":cb_routing,"coinbase_routing_inflow_egld":CB_IN,
     "coinbase_routing_funder":CB_FUNDER,"coinbase_routing_funder_label":CB_FUNDER_LABEL,
     "weeks_at_zero":0,
     "bid_to_distribution_ratio_pct":100*BID_ABSORBED/HUB_NET_ONEWAY if HUB_NET_ONEWAY else None,
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
 "meta_learning":{"run_number":20,
   "endpoints_that_worked":status["ok"],"endpoints_that_failed":status["failed"],
   "api_quirks":[
     "PAGINATED WINDOWS ARE REPRODUCIBLE WEEKS LATER. The run #17 peak window (Jul 13-20) re-queried on Aug 10 returned the same 1,284,688 gross figure reported at the time, and its routers and feeders were all still resolvable at a 60-day remove. This makes retrospective re-netting of any historical window a standing capability rather than a one-off, provided the window is inside the API's transaction retention.",
     "CIRCULARITY IS APPROXIMATELY CONSTANT ACROSS WINDOWS. Measured at 68% (run #17 peak), 80% (run #19) and 69% (run #20). This was not knowable from one measurement and it materially changes how the historical gross series should be treated - as a valid shape with wrong units rather than as unusable.",
     "/providers returned 187 entries of which 107 have locked>0, unchanged. The locked>0 filter remains load-bearing for every churn and concentration metric.",
     "CLEAN PRICE-FEED RUN (6th consecutive): the dataApi re-fetch guard reported 0 retries for all four dataApi-class tokens (SEGLD, SWTAO, USH, XEGLD).",
     "The ESDT system-SC issue scan returned ZERO issuances in the window - not a truncation or a filter artifact, the raw scan itself was empty. Fourth consecutive week of effectively zero new-token formation.",
     "The whale_i 60-day bidirectional trace hit the collector's 12-page cap (600 txs each way) rather than the time boundary, so the traced window is ~25 days, not 60. Any address running >20 txs/day needs max_pages raised or the window narrowed deliberately."],
   "data_gaps":[
     "The net one-way series has three anchors (run #17 peak, run #19, run #20) but runs #13-#16 and #18 are still gross-only. Given that circularity is now measured as roughly constant, interpolating them is defensible but has not been done - the honest statement is that the shape is trusted and the levels for those weeks are not.",
     "'Unknown Whale I' is profiled but not identified. The behavioural evidence (nonce 10,169, 20,794 lifetime txs, 15-75 txs/day, ~80-110 counterparties, both sides of the hub every week) points at an OTC operator inventory wallet, but the counterparty set was not fully enumerated because the 60d trace hit the page cap. Until it is, its net take from the desks is counted as distribution, which may overstate the genuine one-way figure by roughly 12,800 EGLD this week.",
     "The direct-node unwind (~215K over three weeks) is measured only as a residual - total staked minus delegation TVL. No trace of which node operators are unstaking or where the EGLD lands has been attempted. This is the largest unexplained flow currently tracked.",
     "The XEGLD redemption has no destination trace. Whether ~5,250 XEGLD went to native delegation, a competing LSD, or an exchange is the difference between a constructive and a bearish reading, and the model cannot currently say which.",
     "Two entries in known-addresses.json remain invalid-checksum and are flagged rather than guessed: Hatom UTK Money Market and OneDex Launchpad. Neither is queried by the collector, so no figure is affected."],
   "key_findings":[
     f"WAVE #2 IS STAGING - BOTH PRE-COMMITTED THRESHOLDS CLEARED. UPbit fed {UPBIT_RELOAD:,.0f} EGLD into the desks (vs 67,000 last week, threshold 200,000) and net one-way distribution tripled to {HUB_NET_ONEWAY:,.0f} (threshold 150,000). Gross {OTC_THR_7D:,.0f} ({otc_drop_pct:+.0f}%). Run #18's exhaustion call is dead.",
     f"RUN #17 PEAK RE-NETTED (closes run #19's top recommendation): {PEAK_GROSS:,.0f} gross = {PEAK_NET:,.0f} net one-way, {PEAK_CIRC_PCT:.0f}% circular. Circularity is roughly CONSTANT across all three measured windows, so the gross series has the right shape and the wrong units - restate magnitudes, keep directions.",
     f"THE IDENTIFIABLE BID REACTIVATED through exactly the pre-registered pipe: Coinbase hot -> Coinbase Routing ({CB_IN:,.0f} in) -> Mega Whale absorber ({BID_ABSORBED:,.0f}). The three-week dormancy promotion is CANCELLED. But at {100*BID_ABSORBED/HUB_NET_ONEWAY:.0f}% of the week's net distribution, the pipe is live and the size is not.",
     (f"FIRST COMPETITIVE FEE CUT IN TWENTY RUNS: {FEE_CUT['provider']} {FEE_CUT['fee_from_pct']:.0f}% -> {FEE_CUT['fee_to_pct']:.0f}% on a {FEE_CUT['locked_egld']:,.0f} EGLD book, APR to {FEE_CUT['apr_pct']:.2f}%. Pre-registered by run #19. It has not worked yet ({FEE_CUT['locked_wow_egld']:+,.0f} EGLD, {FEE_CUT['users_wow']:+d} users the same week)." ) if FEE_CUT else "No fee repricing this week.",
     f"EGLD FLAT at {price_chg:+.2f}% while BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}% - ~2pp underperformance. The chain absorbed {HUB_NET_ONEWAY:,.0f} of net distribution and finished unchanged: the supply cleared, and the underperformance IS the overhang quantified.",
     f"XEGLD REDEEMED {xegld_supply_wow:+.2f}% ON A FLAT PRICE WEEK - the first time XOXNO redemption has decoupled from a drawdown. SEGLD flat to three decimals ({segld_supply_wow:+.3f}%), so not LSD-wide. Destination untraced.",
     f"DIRECT-NODE UNWIND, WEEK 3: delegation {deleg_tvl_wow:+,.0f} while total staked {staked-pecon['staked_egld']:+,.0f}, implying ~{abs(direct_node_delta):,.0f} out of direct-node stake (~215K cumulative). Largest unexplained structural flow tracked.",
     f"USH DE-LEVERAGING COMPLETE: {ush_supply_wow:+.2f}% after -2.93% and -2.60%, inside the noise band. Run #19's stabilisation branch. Borrowers retired the run #16 leverage chase and stopped.",
     f"DEX TURNOVER STABILISED at {turnover:.2f}% (from {prev_turnover:.2f}%), first non-decline in three weeks - neither run #19 branch (recovery >4%, or a third halving) fired. Routing throughput recovered ({tcount('XOXNO Aggregator'):,} daily transfers).",
     f"REWARD COMPOUNDING MEAN-REVERTED to {COMPOUND_PCT:.2f}% from the {COMPOUND_PREV:.2f}% record, inside the ten-run 55-62% band. Of {RETAIL_N} retail claims traced, NONE went to a labelled exchange - the most stable result in the model.",
     f"ZERO new tokens issued for a fourth consecutive week. For a chain whose thesis rests on application-layer growth, this is more durable than any flow dynamic in this report.",
     f"'Unknown Whale I' PROFILED as an OTC operator inventory wallet, not a whale: nonce {WI_NONCE:,}, 20,794 lifetime txs, 15-75/day, {WI_CP_OUT}/{WI_CP_IN} counterparties, both sides of the hub every week. If confirmed, netting it out would cut this week's genuine one-way figure to ~{HUB_NET_ONEWAY-WI_HUB_NET:,.0f}."],
   "action_items_from_previous":8,
   "action_items_completed":8,
   "methodology_changes":[
     "HISTORICAL WINDOWS CAN BE RE-NETTED RETROSPECTIVELY (new). The run #17 peak window re-queried three weeks later returned identical gross figures with all routers and feeders still resolvable. Retrospective re-netting is therefore a standing capability, not a one-off - any window inside API retention can be restated in net one-way terms for ~60 queries.",
     "TREAT THE GROSS OTC SERIES AS A VALID SHAPE WITH WRONG UNITS, NOT AS UNUSABLE (new, and it softens run #19's conclusion). Circularity measured at 68% / 80% / 69% across three windows is roughly constant, so relative dynamics in the runs #13-#18 gross series are intact and only the levels overstate distribution, by roughly 3-5x. Run #19's fear that the record-wave narrative needed discarding was an overcorrection.",
     "THE BILATERAL INVERSE RULE MUST BE SUPPRESSED, NOT COMPUTED, WHEN |price change| < 5% (enforced this run). A 1.30% TVL move against a -0.37% price move produces a mechanical ratio of 3.50 that is pure small-denominator artifact. Prior runs computed and reported the ratio whenever both legs existed; from this run the report states explicitly that the rule is not evaluable and the confirmation count does not advance.",
     "PRE-COMMITTED TESTS ARE NOW THE MODEL'S PRIMARY OUTPUT DISCIPLINE. Four registered tests resolved this run (UPbit escalation, bid dormancy promotion, USH third week, fee response) and three fired in the pre-specified direction. Three consecutive runs before this one had a headline overturned by measuring deeper; this run had none, because the questions were specified before the data arrived rather than after.",
     "RAISE max_pages FOR HIGH-FREQUENCY ADDRESSES (new). The whale_i 60-day trace hit the 12-page cap at 600 txs and covered ~25 days instead of 60. Any address above ~20 txs/day needs the cap raised or the window narrowed deliberately, and the collector should log when a paginated query terminates on the page cap rather than the time boundary."],
   "new_addresses_discovered":3,
   "most_valuable_insight":f"For the first time in four runs the headline findings are resolutions rather than corrections, and that is the result worth recording. Run #19 wrote down four pre-registered tests with explicit numeric thresholds; three fired in the specified direction and the fourth resolved on its stated third branch. Wave #2 of the OTC distribution is staging: UPbit pushed {UPBIT_RELOAD:,.0f} EGLD into the desks against a 200,000 threshold, and net one-way distribution tripled from 61,435 to {HUB_NET_ONEWAY:,.0f} against a 150,000 threshold. The identifiable bid reactivated through exactly the pipe named as the earliest reversal signal - a Coinbase hot wallet refilled the Coinbase Routing wallet with {CB_IN:,.0f} EGLD, which forwarded {BID_ABSORBED:,.0f} to the Mega Whale absorber, cancelling the pre-registered promotion of bid-dormancy to a structural finding. A high-fee delegation incumbent cut its service fee for the first time in twenty runs, which was the exact event run #19 predicted the fee-arbitrage mechanism would eventually force. And re-netting the run #17 peak ({PEAK_GROSS:,.0f} gross = {PEAK_NET:,.0f} one-way, {PEAK_CIRC_PCT:.0f}% circular) closed the top recommendation and produced a better answer than expected: circularity is roughly constant across every window measured, so the old gross series has the right shape and the wrong units rather than being unusable. The synthesis of the week is a single sentence: distribution restarted and tripled, the bid restarted at roughly a tenth of that size, and price finished flat - the market cleared a genuine supply wave without breaking, and paid for it by giving up the ~2pp of beta that BTC and ETH delivered.",
   "top_recommendation":f"TRACE THE TWO UNEXPLAINED STRUCTURAL FLOWS. The model is now well-instrumented on the OTC pipeline and the demand side, and both behaved predictably this week. What it cannot explain are two flows of comparable size to the ones it narrates in detail: (1) the direct-node unwind, ~{abs(direct_node_delta):,.0f} EGLD this week and ~215K over three weeks, measured only as a residual between total staked and delegation TVL - identify whether specific operators are unstaking and whether the receiving delegation contracts are concentrated or broad; (2) the XEGLD redemption of ~5,250 tokens on a FLAT price week, the first time XOXNO redemption has decoupled from a drawdown - trace the LSD contract's outbound flows to distinguish migration to native delegation (constructive, and delegation grew by the right order of magnitude) from exit to exchange (bearish). Both are cheap to trace and both are currently narrated as 'unexplained', which is the weakest sentence a quantitative report can contain. PRE-COMMITTED READING for next week's OTC test: net one-way above ~300K with a UPbit tranche above ~350K = wave #2 matches or exceeds the re-netted run #17 peak and supply overhang becomes the dominant fact on the chain; net back below ~100K = this was a two-week burst, not a wave.",
   "recommendations_for_next_run":[
     f"DOES WAVE #2 ESCALATE TO PEAK SCALE? This week's net one-way was {HUB_NET_ONEWAY:,.0f}, about {100*HUB_NET_ONEWAY/PEAK_NET:.0f}% of the re-netted run #17 peak of {PEAK_NET:,.0f}, on a UPbit tranche of {UPBIT_RELOAD:,.0f}. PRE-COMMITTED: net above ~300K with a tranche above ~350K = wave #2 matches or exceeds the peak and the supply overhang is the dominant fact on the chain; net back below ~100K = this was a two-week burst rather than a wave. Watch UPbit's own balance ({ent_cur.get('UPbit',0):,.0f}) as the leading edge - it has stayed flat for two weeks while feeding the desks, so it is being replenished from a source the model has not observed. Finding that source is worth ~20 queries.",
     f"TRACE THE DIRECT-NODE UNWIND. Three consecutive weeks of delegation growing while total staked falls implies ~215K cumulative out of direct-node stake, and it is measured only as a residual. Identify which node operators are unstaking (queryable via the staking contract) and whether the receiving delegation contracts are concentrated or broad. One operator = idiosyncratic; broad = an economics story about the base/top-up APR split, which would be a genuine protocol-level finding.",
     f"TRACE THE XEGLD REDEMPTION DESTINATION. ~5,250 XEGLD redeemed on a {price_chg:+.2f}% price week - the first XOXNO redemption in tracking without a drawdown driver, while SEGLD was flat to three decimals. Query the XOXNO LSD contract's outbound flows. PRE-COMMITTED: destinations landing in native delegation contracts = migration, constructive, and it would also help explain the direct-node/delegation split; destinations landing at exchanges = exit, bearish; a single large recipient = idiosyncratic and dismissable.",
     f"DID THE FEE CUT WORK? {FEE_CUT['provider'] if FEE_CUT else 'The repricing provider'} cut {FEE_CUT['fee_from_pct']:.0f}% -> {FEE_CUT['fee_to_pct']:.0f}% and still shed {FEE_CUT['locked_wow_egld']:+,.0f} EGLD and {FEE_CUT['users_wow']:+d} delegators in the same week. PRE-COMMITTED 2-3 week test: stake returning = MultiversX delegators respond to price signals, and other high-fee incumbents (procryptostaking at 20%) should follow within a month; stake continuing to leave despite the better deal = delegator inertia dominates fee economics, which would materially weaken the yield-arbitrage mechanism this model has leaned on for four runs.",
     f"DOES THE BID SCALE UP OR WAS IT MAINTENANCE? The absorber took {BID_ABSORBED:,.0f} EGLD, roughly 18% of the run #15 tranche and 11% of run #17's, or {100*BID_ABSORBED/HUB_NET_ONEWAY:.0f}% of the week's net distribution. PRE-COMMITTED: a tranche in the 30-50K range = the bid is genuinely back and the demand deficit is closing; another sub-10K week or a return to zero = this was a maintenance transfer and the dormancy finding should be revived. A second consecutive absorption week of ANY size is more informative than this one's magnitude.",
     f"FINISH IDENTIFYING 'Unknown Whale I'. Raise the collector's page cap (it terminated on pages, not time, at 600 txs covering ~25 days of a requested 60) and enumerate its full counterparty set. The test is specific: if >60% of its counterparties by value are the hub's own feeders and routers, classify it as OTC operator inventory and NET IT OUT of the one-way distribution figure, which would cut this week's {HUB_NET_ONEWAY:,.0f} to roughly {HUB_NET_ONEWAY-WI_HUB_NET:,.0f}. If its counterparties are broad and external, it is a genuine large buyer and belongs in the demand instruments instead - which would be the single most consequential reclassification available to the model.",
     f"BACKFILL THE NET ONE-WAY SERIES FOR RUNS #13-#16 AND #18. Retrospective re-netting is now proven to work three weeks out, and circularity is roughly constant across the three measured windows, so the remaining five windows can be anchored properly for ~60 queries each. Prioritise run #16 (1,100,791 gross, the second-largest reading) and run #18 (313,173, the 'collapse' week whose interpretation drove two runs of narrative). Do not interpolate them from the constant-circularity assumption without measuring at least one more.",
     f"CHECK MEX PAIR DEPTH DIRECTLY. MEX has outperformed EGLD for three consecutive weeks ({100*(meco['price']-prev_mexp)/prev_mexp:+.2f}% vs {price_chg:+.2f}% this week). Run #19 attributed it to stale pricing in illiquid pairs and this run repeated that attribution, but three weeks strains the explanation. Query the MEX pairs' actual TVL and trade counts rather than assuming - if the pricing is real, MEX outperforming its own chain's native token through a distribution wave is a finding, not noise."],
   "dashboard_feature_suggestions":[
     {"title":"OTC net one-way series with measurement-provenance markers",
      "motivation":f"This run produced the second and third anchored points of the net one-way series (re-netted run #17 peak at {PEAK_NET:,.0f}, run #20 at {HUB_NET_ONEWAY:,.0f}, alongside run #19's 61,435) and simultaneously established that the surrounding gross series is a valid shape with 3-5x wrong units. The dashboard currently shows one throughput number per week with no indication of which measurement regime produced it - truncated (runs <#13), paginated-gross (#13-#18, #20), or paginated-and-netted (#17-peak, #19, #20). A reader cannot tell that the 1.28M bar and this week's 604K bar are not the same kind of number, and that the honest comparison is 410K vs 189K.",
      "suggested_visualization":"a single time series with two overlaid lines - gross (muted) and net one-way (emphasised) - where net is drawn solid at measured weeks and dashed/hollow at inferred ones, with a small provenance chip per bar (truncated / gross / netted) and a legend that states the ~3-5x relationship explicitly.",
      "data_already_available":True,
      "data_source":"whale_intelligence.otc_pipeline now carries gross_series_egld_7d, net_one_way_series_egld_7d and peak_window_renetted as first-class fields in this report","priority":"high"},
     {"title":"Pre-committed test scoreboard",
      "motivation":f"This is the run that makes the case. Four tests were registered in run #19 with explicit numeric thresholds, and three fired in the pre-specified direction - the UPbit escalation past 200,000, the bid-dormancy promotion cancelled by the exact pipe named as the reversal signal, and the fee cut that the yield-arbitrage mechanism was predicted to force. A reader of this single report sees eight assertive findings with no way to know that most of them were falsifiable predictions made a week earlier rather than post-hoc narration. The scoreboard is the difference between a newsletter and a model.",
      "suggested_visualization":"a table of open and resolved tests - registered-in run, the claim, the numeric threshold, the outcome, and a chip for resolved-as-predicted / resolved-against / unresolved - with open tests pinned to the top so the next run's questions are visible before its answers.",
      "data_already_available":False,
      "data_source":"the tests exist as prose inside watch_list.reason and recommendations_for_next_run across runs; making this real needs a structured `pre_committed_tests` array in the schema with threshold, branch and resolution fields","priority":"high"},
     {"title":"Unexplained-flow tracker",
      "motivation":f"Two flows this week are of comparable size to the ones the report narrates in detail and are labelled 'unexplained': the direct-node unwind (~{abs(direct_node_delta):,.0f} this week, ~215K over three weeks, measured only as a residual between total staked and delegation TVL) and the XEGLD redemption of ~5,250 tokens on a flat price week. Both have been carried as prose caveats rather than tracked quantities, which means their age and cumulative size are invisible. A reader should be able to see at a glance what the model is measuring but cannot explain, and for how long.",
      "suggested_visualization":"a compact card list - flow name, cumulative size, weeks unexplained, the specific query that would resolve it - sorted by cumulative size, so the largest blind spot is always the first thing shown.",
      "data_already_available":False,
      "data_source":"currently only in meta_learning.data_gaps as free text; would need an `unexplained_flows` array carrying magnitude, first_observed_run and resolution_query","priority":"medium"}],
   "dashboard_suggestions_followup":[
     {"title":"OTC hub flow map: gross vs net one-way, with venue-level netting","status":"pending",
      "note":"Not built, and the data case is now stronger: this report carries venue_netting, peak_window_renetted and a net series as first-class fields, so a Sankey or chord view needs no derivation from the collected snapshot. Two windows now show the same venue shape (UPbit sole source, Binance/Bybit receiving), which is exactly the recurring structure a diagram would make instantly legible."},
     {"title":"Demand instrument panel: turnover ratio, identifiable bid, withdrawal breadth","status":"pending",
      "note":"Not built, but the blocker named last run is now half-cleared - the bid composite and withdrawal breadth are first-class fields in whale_intelligence.demand_instruments this run, and the bid series has its first non-zero point (0, 0, "+f"{BID_ABSORBED:,.0f}"+"). Turnover has three points and just recorded its first non-decline. The panel would now show a genuine inflection rather than three flat lines."},
     {"title":"Corrected OTC throughput series with method-provenance markers","status":"pending",
      "note":"Superseded and re-scoped by this run's suggestion #1. The blocker was that building it with gross figures alone would propagate a known overstatement; measuring constant circularity across three windows resolves that - gross can now be shown alongside net with an explicit stated relationship rather than being withheld."},
     {"title":"Pre-committed test scoreboard","status":"pending",
      "note":"Re-submitted as this run's suggestion #2 and promoted to high priority. Four tests resolved this run with three firing as predicted, which is the strongest single argument for the feature that has occurred in twenty runs."},
     {"title":"Conclusion-revision log","status":"deprioritized",
      "note":"Deprioritised, and this run is why. The premise was three consecutive runs with overturned headlines; this run had zero corrections because the questions were pre-registered instead of derived after the fact. The pre-committed test scoreboard is the constructive version of the same idea and subsumes it - a revision log records failures after they happen, a test scoreboard prevents them."},
     {"title":"EGLD relative-strength (beta) tracker","status":"deprioritized",
      "note":"Deprioritised a third time. EGLD underperformed by ~2pp this week, which is ordinary and fully explained by the measured distribution wave, so there is still no decoupling regime to track."}]
 }
}

json.dump(report,open(f"{REPO}/reports/2026-08-10.json","w"),indent=2)
print("WROTE reports/2026-08-10.json")
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
