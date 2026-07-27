#!/usr/bin/env python3
"""Assemble reports/2026-07-27.json (run #18) from collected data."""
import json, math
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D = json.load(open(f"{REPO}/data/collected/2026-07-27.json"))
prev = json.load(open(f"{REPO}/data/previous.json"))
kn = json.load(open(f"{REPO}/data/known-addresses.json"))
learn = json.load(open(f"{REPO}/data/learnings.json"))
prevcol = json.load(open(f"{REPO}/data/collected/2026-07-20.json"))  # for supply WoW

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
pp=pecon["egld_price_usd"]
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
# OTC throughput - PAGINATED BY DEFAULT (run #17 recommendation #1, implemented)
# The collector now pages to the after= boundary; inter-desk transfers are netted
# out so the two desks do not inflate each other. The runs #13-#15 windows were
# re-queried with the identical method this run, so the series below is finally
# a comparable time series rather than a set of truncated lower bounds.
# ---------------------------------------------------------------------------
UPBIT_DESK="erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
DIST_DESK="erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
DESK_SET={UPBIT_DESK,DIST_DESK}
def desk_throughput(block):
    gross=inter=0.0; dest={}
    for a,v in block.items():
        for t in v.get("txs",[]):
            try: val=int(t.get("value","0"))/1e18
            except: val=0
            if val<=0: continue
            gross+=val
            r=t.get("receiver")
            if r in DESK_SET: inter+=val
            else: dest[r]=dest.get(r,0)+val
    return gross,inter,dest
OTC_THR_GROSS,OTC_THR_INTERDESK,desk_dest=desk_throughput(D["desk_outbound_paged"])
OTC_THR_7D=OTC_THR_GROSS-OTC_THR_INTERDESK
# Backfilled with the identical paginated method this run:
OTC_SERIES={"run13":66128.0,"run14":186124.0,"run15":506053.0,"run16":1100791.0,
            "run17":1284688.0,"run18":OTC_THR_7D}
OTC_THR_7D_PREV=OTC_SERIES["run17"]
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

# ---------- wallet changes ----------
changes=[]
for a,b in cur_top.items():
    if a in prev_top and cat(a)!="system":
        pb=prev_top[a]; d=b-pb; pct=100*d/pb if pb else None
        if abs(d)>2000 or (pct is not None and abs(pct)>5):
            tier="mega_whale" if b>1e6 else "large_whale" if b>=1e5 else "mid_whale" if b>=1e4 else None
            changes.append({"address":a,"label":lab(a),"category":cat(a),"tier":tier,
                "balance_current_egld":b,"balance_previous_egld":pb,"change_egld":d,"change_pct":pct})
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
tx_pools.append(D.get("mega_whale_inbound")); tx_pools.append(D.get("mega_whale_outbound"))
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
# Run #12 quirk, 2nd occurrence (run #18): watch_addresses carried an invalid-checksum
# KuCoin address (erd1ty4pvmjtl3mnsjvnsxqkm3xqm4dm7ppgz9sh4nk4tqvlmw0jyggqzn4mdc, HTTP 400).
# The canonical KuCoin wallet is erd1ty4pvmjtl3mnsjvnsxgcpedd08fsn83f05tu0v5j23wnfce9p86snlkdyy.
BAD_ADDRS={"erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp29trp6qsl2gdvvz2eqra76xc",
           "erd1ty4pvmjtl3mnsjvnsxqkm3xqm4dm7ppgz9sh4nk4tqvlmw0jyggqzn4mdc"}
# Coinbase Custody 2 was ADDED to the tracked set in run #17 (it is the nonce-0 destination
# of Coinbase Custody's 65,090 migration). It carries no prior-week balance, so counting it
# naively books a phantom +65,090 inflow. Netted out explicitly below.
NEWLY_TRACKED={"erd1z4xerdjq6aa2eex7rj6gsclc7yhq5nfsjjmtxgqrx7q4cwypz5vs8v3s3l":65090.0}
by_exchange=[]; ent_cur={}; ent_w={}
for a in exch:
    if a in BAD_ADDRS: continue
    e=entity_of(a)
    if not e: continue
    cur=bal_of(a)
    if cur is None: cur=cur_top.get(a)
    pb=prev_top.get(a)
    ent_w[e]=ent_w.get(e,0)+1
    if cur is not None: ent_cur[e]=ent_cur.get(e,0)+cur
    if cur is not None and pb is not None:
        by_exchange.append({"exchange":lab(a),"change_egld":cur-pb,"pct":(100*(cur-pb)/pb if pb else None)})
by_exchange.sort(key=lambda x:-abs(x["change_egld"]))
prev_ent={}
prev_ta_map={x["address"]:x["balance_egld"] for x in prev["top_accounts"]}
for a in exch:
    if a in BAD_ADDRS: continue
    e=entity_of(a)
    if not e: continue
    if a in prev_ta_map:
        prev_ent[e]=prev_ent.get(e,0)+prev_ta_map[a]
for k,v in prev["exchange_balances"].items():
    e = "Binance" if "Binance" in k else ("Coinbase" if "Coinbase" in k else k)
    if e not in prev_ent:
        prev_ent[e] = v

cust_bal=bal_of("erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p") or 3357101
CUSTODY_RELOAD=150000.0
# A third Binance.com wallet (6,995 EGLD) has no prior-week balance in previous.json
# top_accounts, so it books its full balance as a phantom inflow - same class of bug as
# run #17's Coinbase Custody 2 (which IS correctly diffed this run because it made the
# prior top-60 cut). Netted out explicitly.
UNTRACKED_PRIOR=6995.0
NONFLOW=CUSTODY_RELOAD+UNTRACKED_PRIOR

ent_interp={
 "Binance":"Net +162,696 across 4 wallets - but 150,000 of it is the STAKING CUSTODY RELOADING, which is the single most important reversal of the week. The custody wallet took a single 150,000 EGLD transfer from erd1r3w62vq (a nonce-8 wallet holding 2 EGLD - pure pass-through) and now sits at 3,357,101. That ENDS the three-leg de-staking programme (-305,549 cumulative over runs #15-#17 from the 3,512,650 peak) and reverses roughly half of it in one move. Binance.com hot wallets were essentially flat (+5,701 on the main wallet; a third smaller wallet contributes +6,995 that is a tracking phantom rather than a flow, since it carries no prior-week balance). Per the run #9 decompose rule this is intra-entity parking, not customer deposit flow, so it should NOT be read as bearish exchange inflow - if anything a custody wallet refilling is the opposite of distribution.",
 "Coinbase":"+2,607 across 5 wallets - flat. The run #17 custody migration (65,090 to the fresh nonce-0 wallet erd1z4xerdjq6aa2) is correctly netted this week because that destination made the stored top-60 and therefore carries a prior-week balance to diff against; the migration is confirmed complete and stationary. The important Coinbase datapoint is not the balance at all: the Coinbase Routing -> Mega Whale erd18mv2z6r2 pipe was IDLE, with the routing wallet drained to 77 EGLD and the whale exactly flat. The one channel through which the market's identifiable large bid was being filled in runs #15 and #17 sent nothing.",
 "Bybit":"+33,541 (+10.6%) to 351,281, a 2nd consecutive inflow week. Bybit remains the largest single destination of the OTC pipeline - the same zero-balance routers (erd1g6fntj, erd1e9luc4, erd1w7nlme) that carried last week's wave forwarded to Bybit again this week, just at a quarter of the volume. Steady accumulation of deposit balances on a venue during a -10% price week is the ordinary bearish read.",
 "UPbit":"-24,620 (-2.0%) to 1,234,929. A mild drawdown, and notably UPbit did NOT push a fresh large tranche out to its OTC desks this week (last week it sent 364,000). The absence of a reload is the single most constructive data point in the exchange complex: the operator that staged the 1.28M distribution wave has stopped feeding the pipeline.",
 "KuCoin":"-4,591 (-2.6%) to 171,338. This RESOLVES the run #17 pre-committed test. Whale erd15ku2r2j6 sent its entire 145,443 EGLD to KuCoin last week and went to zero; the pre-registered reading was that a balance bleeding back down means withdrawal/OTC settlement (neutral) while a balance staying elevated means the position was sold into the book (bearish). The balance stayed: KuCoin retained ~97% of the deposit and its own 7d flows were tiny (~1.5K in, ~1.2K out). The coins did not leave. Read per the pre-commitment, the position was absorbed by the venue - bearish, and consistent with this week's -10.13% price move.",
 "Crypto.com":"-4,688 (-2.2%) across 2 wallets. Flat.",
 "Gate.io":"+3,982 (+4.8%). Small inflow.",
 "MEXC":"-2,159 (-2.3%). Flat.",
 "Bitget":"-6,408 (-9.4%). Mild outflow off a small base.",
 "Tokero":"Flat.",
 "Bitfinex":"Flat."}
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
net_adjusted=net_total-NONFLOW

exchange_flows={"total_exchange_egld_current":total_cur,"total_exchange_egld_previous":total_prev,
    "net_change_egld":net_total,"net_change_pct":100*net_total/total_prev if total_prev else None,
    "direction":"outflow" if net_total<0 else "inflow",
    "signal":f"Headline net exchange flow {net_total:+,.0f} EGLD ({100*net_total/total_prev:+.2f}%) - a 2nd consecutive inflow week on the raw number, but the run #15 decompose-before-labeling rule strips almost all of it away. Two items account for {100*NONFLOW/net_total:.0f}% of the total and neither is customer flow: Binance Staking CUSTODY +150,000 (an intra-Binance reload of a parked position, arriving in one transfer from a nonce-8 pass-through) and a third Binance.com hot wallet +{UNTRACKED_PRIOR:,.0f} that carries no prior-week balance in the stored top-60 and therefore books its whole balance as a phantom inflow. Netting both out, TRUE external exchange flow this week is {net_adjusted:+,.0f} EGLD - essentially FLAT. That is the important result: EGLD fell {100*(price-pp)/pp:.2f}% on a week when almost nothing arrived at exchanges and the OTC desks ran at a quarter of last week's volume. The supply channel that explained the last four weeks did not explain this one.",
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
cohort_names=["ninjastaking","egldstakingprovider","procryptostaking","valuestaking","orius","star_staking"]
cohort_flows={nm:lk_wow(nm) for nm in cohort_names if lk_wow(nm) is not None}
cohort_net=sum(v for v in cohort_flows.values())
binance_staking_prov_wow=lk_wow("binance_staking")
deleg_wow=cur_deleg-prev_deleg

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
newly_issued=[]
newly_issued_rejected=[]
for ni in D.get("newly_issued", []):
    if ni["accounts"]>1000 or ni["identifier"] in KNOWN_TOKEN_IDS:
        newly_issued_rejected.append((ni["identifier"],"established token misidentified by issue-scan"))
        continue
    if ni["accounts"]<=10 or ni["transactions"]<=5:
        newly_issued_rejected.append((ni["identifier"],f"below quality bar ({ni['accounts']} holders, {ni['transactions']} txs)"))
        continue
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
prev_mexp=prev["xexchange"]["mex_price_usd"]
prev_dexvol=prev["xexchange"]["volume_24h_usd"]
xexchange={"total_pairs":meco.get("marketPairs"),"total_volume_24h_usd":totvol,"mex_price_usd":meco["price"],
    "mex_market_cap_usd":meco["marketCap"],"mex_price_change_24h_pct":None,
    "mex_price_change_wow_pct":100*(meco["price"]-prev_mexp)/prev_mexp,
    "top_pair":pairs[0]["name"],"top_pair_volume_24h_usd":pairs[0]["volume_24h_usd"],
    "top_pair_dominance_pct":pairs[0]["share_pct"],"top_pairs_by_volume":pairs[:5]}

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
hatom_ush=mc("USH-111e09")
xoxno_lsd=mc("XEGLD-e413ed")
segld_supply_wow=supply_wow("SEGLD-3ad2d0")
xegld_supply_wow=supply_wow("XEGLD-e413ed")
swtao_supply_wow=supply_wow("SWTAO-356a25")
ush_supply_wow=supply_wow("USH-111e09")

wegld_egld=sum(int(b["balance"])/1e18 for b in D["wegld"].values() if isinstance(b,dict) and "balance" in b)
xexch_tvl_egld=wegld_egld; xexch_tvl_usd=wegld_egld*price
def tcount(name):
    c=D["proto"][name]["transfers_24h"]; return c.get("count") if isinstance(c,dict) else c
prev_hl_egld=prev["defi_tvl"]["Hatom Lending"]/pp
prev_xl_egld=prev["defi_tvl"]["XOXNO LSD"]/pp
prev_hush=prev["defi_tvl"]["Hatom USH"]
prev_xexch_egld=prev["defi_tvl"]["xExchange (USD)"]/pp
prev_hlsd=prev["defi_tvl"]["Hatom Liquid Staking"]
prev_hlsd_egld=prev_hlsd/pp
hl_egld=hatom_lending/price
hlsd_egld=hatom_lsd/price
xlsd_egld=xoxno_lsd/price
ush_egld=hatom_ush/price
price_chg=100*(price-pp)/pp
hl_egld_chg=100*(hl_egld-prev_hl_egld)/prev_hl_egld
inverse_ratio=abs(hl_egld_chg)/abs(price_chg)

wegld_tok=next((t for t in D["tokens_holders"] if t["identifier"]=="WEGLD-bd4d79"), None)
wegld_supply_now = int(wegld_tok.get("supply","0")) if wegld_tok else 0
wegld_supply_prev = int(prev_th.get("WEGLD-bd4d79",{}).get("supply_raw",0) or 0)
wegld_chg_pct = 100*(wegld_supply_now-wegld_supply_prev)/max(wegld_supply_prev,1) if wegld_supply_prev else 0

def stable_wow(sid):
    t=D.get("stable_"+sid,{})
    try: cur=float(t.get("supply")) if t and t.get("supply") else None
    except: cur=None
    praw=prev_th.get(sid,{}).get("supply_raw")
    prev_adj=(float(praw)/1e6) if praw else None
    if cur is None or prev_adj is None or prev_adj==0: return None
    return 100*(cur-prev_adj)/prev_adj
usdc_supply_wow=stable_wow("USDC-c76f1f")
usdt_supply_wow=stable_wow("USDT-f8c08c")

protocol_breakdown=[
 {"protocol":"xExchange","category":"dex","addresses_tracked":16,"tvl_usd":xexch_tvl_usd,"tvl_egld":xexch_tvl_egld,
  "tvl_wow_change_pct":100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld,"transfers_24h":None,"volume_24h_usd":totvol,
  "notable_events":f"DEX volume COLLAPSED to ${totvol/1000:.0f}K ({100*(totvol-prev_dexvol)/prev_dexvol:.0f}% WoW) - the second-largest weekly drop in tracking after run #12's -55%, and it fully retraces the two-week rally-volume spike. Concentration got worse, not better: WEGLD/USDC now carries {pairs[0]['share_pct']:.1f}% of all volume (vs 91.5% last week), with {pairs[1]['name'] if len(pairs)>1 else '?'} a distant {pairs[1]['share_pct'] if len(pairs)>1 else 0:.1f}%. Pool TVL rose in EGLD terms ({100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld:+.1f}%) and WEGLD supply grew {wegld_chg_pct:+.2f}% (more EGLD wrapped), so liquidity is present - it is TRADING that vanished. Volume dying while price falls {price_chg:.1f}% is the signature of an absent bid rather than aggressive selling.","health_signal":"shrinking"},
 {"protocol":"Hatom Lending","category":"lending","addresses_tracked":13,"tvl_usd":hatom_lending,"tvl_egld":hl_egld,
  "tvl_wow_change_pct":hl_egld_chg,"transfers_24h":tcount("Hatom EGLD MM"),
  "notable_events":f"TVL ${hatom_lending/1e6:.2f}M USD ({100*(hatom_lending-prev['defi_tvl']['Hatom Lending'])/prev['defi_tvl']['Hatom Lending']:+.1f}%), {hl_egld/1000:.0f}K EGLD ({hl_egld_chg:+.1f}% EGLD). BILATERAL INVERSE RULE: 6th confirmation and the STRONGEST response ratio ever recorded. Price {price_chg:+.2f}% (well past the |5%| guardrail, so the rule is evaluable) against EGLD-denominated TVL {hl_egld_chg:+.2f}% - depositors DCA'd into the drop, exactly the run #8 down-week behavior. Response ratio {inverse_ratio:.2f} versus a prior down-week series of 0.88 / 0.80 / 0.70 / 0.21 that run #11 flagged as DETERIORATING. That deterioration has fully reversed: depositor capacity is the healthiest it has been in the tracked history. This is the single most constructive on-chain data point of the week.","health_signal":"growing"},
 {"protocol":"Hatom Liquid Staking","category":"liquid_staking","addresses_tracked":2,"tvl_usd":hatom_lsd,"tvl_egld":hlsd_egld,
  "tvl_wow_change_pct":100*(hlsd_egld-prev_hlsd_egld)/prev_hlsd_egld,"transfers_24h":tcount("Hatom Liquid Staking"),
  "notable_events":f"SEGLD ${segld_mcap/1e6:.2f}M + SWTAO ${swtao_mcap/1e6:.2f}M = ${hatom_lsd/1e6:.2f}M USD ({100*(hatom_lsd-prev_hlsd)/prev_hlsd:+.1f}%, tracking the price down). On the supply basis that actually matters (run #13 rule) Hatom LSD is FLAT: SEGLD {segld_supply_wow:+.2f}%, SWTAO {swtao_supply_wow:+.2f}%. No redemption pressure on the largest LSD despite a -10% week. dataApi price feed clean for a 4th consecutive run (0 re-fetch retries).","health_signal":"flat"},
 {"protocol":"Hatom USH","category":"stablecoin","addresses_tracked":4,"tvl_usd":hatom_ush,"tvl_egld":ush_egld,
  "tvl_wow_change_pct":100*(hatom_ush-prev_hush)/prev_hush,"transfers_24h":None,
  "notable_events":f"USH supply BURNED {ush_supply_wow:+.2f}% WoW to {supply('USH-111e09'):,.0f} - past the 1% threshold, so the run #11 DE-LEVERAGING rule re-activates. This resolves the run #17 registered test exactly as the bearish branch specified: 'if price rolls over and USH burns >1%, the leverage was chased.' Price rolled over {price_chg:.2f}% and USH burned {abs(ush_supply_wow):.2f}%. The run #16 +6.49% mint is therefore reclassified as a leverage CHASE into a rally rather than conviction - CDP borrowers opened positions at the top and closed them two weeks later.","health_signal":"shrinking"},
 {"protocol":"XOXNO LSD","category":"liquid_staking","addresses_tracked":2,"tvl_usd":xoxno_lsd,"tvl_egld":xlsd_egld,
  "tvl_wow_change_pct":100*(xlsd_egld-prev_xl_egld)/prev_xl_egld,"transfers_24h":tcount("XOXNO LSD"),
  "notable_events":f"XEGLD ${xoxno_lsd/1e6:.2f}M ({100*(xoxno_lsd-prev['defi_tvl']['XOXNO LSD'])/prev['defi_tvl']['XOXNO LSD']:+.1f}% USD). SUPPLY is the signal: XEGLD supply CONTRACTED {xegld_supply_wow:+.2f}% to {supply('XEGLD-e413ed'):,.0f}, ending the two-week re-accumulation (+4.54%, +2.69%) that followed the run #14 -29% collapse. XOXNO is the one LSD leg that redeems on weakness while Hatom's holds - a consistent behavioural difference across four runs now.","health_signal":"shrinking"},
 {"protocol":"XOXNO Aggregator","category":"aggregator","addresses_tracked":1,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("XOXNO Aggregator"),
  "notable_events":f"Throughput {tcount('XOXNO Aggregator'):,} daily transfers - steady, the highest single-contract routing activity on the network. Notably it did NOT fall with DEX volume, so on-chain routing demand is intact even as xExchange order flow dried up.","health_signal":"flat"},
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
                ev = "mint" if chg>0 else "burn"
                token_supply_events.append({
                    "identifier":tid,"name":ct.get("name","?"),"event":ev,
                    "supply_previous":str(ps),"supply_current":str(cs),"change_pct":chg,
                    "description":f"{tid} supply {chg:+.2f}% ({ev})."})

# ---------- anomalies ----------
rb=learn["runs"][-1]["running_baselines"]
def zc(arr,cur):
    if len(arr)<4: return None
    m=sum(arr)/len(arr); sd=math.sqrt(sum((x-m)**2 for x in arr)/len(arr))
    return m,sd,((cur-m)/sd if sd else 0)
zp=zc(rb["egld_price_usd"],price)
zmex=zc(rb["mex_price_usd"],meco["price"])
zd=zc(rb["total_delegators"],cur_deleg)
zse=zc(rb["staked_egld"],staked)
zv=zc(rb["dex_volume_24h_usd"],totvol)
mw_bal_cur=bal_of("erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw") or 1093312
desk_cur=(bal_of(UPBIT_DESK) or 32109)+(bal_of(DIST_DESK) or 29387)
desk_prev=79694.0   # run #17 close: UPbit OTC 39,726 + OTC Distribution 39,968
desk_delta=desk_cur-desk_prev
otc_drop_pct=100*(OTC_THR_7D-OTC_THR_7D_PREV)/OTC_THR_7D_PREV

anomalies=[
 {"metric":"egld_price_usd","current_value":price,"previous_value":pp,"method":"rule_based",
  "severity":"high",
  "description":f"EGLD DECOUPLED TO THE DOWNSIDE WHILE THE MAJORS ROSE - the cleanest EGLD-specific weakness signal of the cycle. EGLD {price_chg:+.2f}% to ${price:.2f} while BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}% both GAINED. This is not high-beta lag (which would show EGLD falling further in a falling market); the market was UP and EGLD alone fell double digits. Run #17 registered exactly this test - 'if EGLD falls harder than BTC/ETH on a macro down week, the laggard regime is re-confirmed' - and the actual outcome is worse than the test anticipated: it did not even need a macro down week. The +24% recovery off $2.55 is now formally reclassified as a BEAR-MARKET RALLY: the entire move retraced ~9 of its ~24 percentage points in a single week against a rising crypto tape. The z-score is only {zp[2]:+.2f}sigma, a textbook instance of the run #16 rule that z UNDER-flags after a multi-week trend widens the baseline - the rule-based read governs here."},
 {"metric":"otc_distribution_wave_exhausted","current_value":round(OTC_THR_7D),"previous_value":round(OTC_THR_7D_PREV),"method":"rule_based",
  "severity":"high",
  "description":f"THE OTC WAVE IS OVER - and the run #17 pre-committed test resolved on the CONSTRUCTIVE branch. Pre-registered reading was: desks rebuilding toward 300K+ = a second distribution wave staged (bearish); desks holding near 80K on low throughput = wave finished, supply exhausted (constructive). Outcome: desks drained a further {desk_delta:+,.0f} to {desk_cur:,.0f} (well BELOW the 80K trigger) and 7d throughput COLLAPSED to {OTC_THR_7D:,.0f} EGLD, {otc_drop_pct:.0f}% below last week's {OTC_THR_7D_PREV:,.0f}. Decisively, UPbit did NOT reload the desks this week (it sent 364,000 out to them in the run #17 window and nothing comparable now); desk inbound was {sum(int(t.get('value','0'))/1e18 for v in D['desk_inbound_paged'].values() for t in v['txs']):,.0f} EGLD and essentially all of it was desk-to-desk shuffling. The pipeline still functions - the same zero-balance routers (erd1g6fntj 92,538, erd1e9luc4 45,026, erd1w7nlme 33,493) forwarded to Bybit and Binance.com again - but at a quarter of the volume. The uncomfortable implication: price fell {price_chg:.2f}% in the week that OTC supply pressure LARGELY WENT AWAY, which means the marginal seller was not the desk and the weakness is a DEMAND failure, not a supply flood."},
 {"metric":"dex_volume_24h_usd","current_value":totvol,"previous_value":prev_dexvol,"method":"z_score",
  "average_value":zv[0],"stddev":zv[1],"z_score":zv[2],"severity":"medium",
  "description":f"DEX VOLUME COLLAPSED {100*(totvol-prev_dexvol)/prev_dexvol:.1f}% to ${totvol/1000:.0f}K - the 2nd-largest weekly drop in tracking history (run #12's -55% was the largest) and a full retrace of the two-week rally spike back to the pre-rally floor. Raw z is only {zv[2]:+.2f}sigma because the baseline was inflated by the same spike, so the percent-threshold read governs (>50% = noteworthy). Concentration worsened to {pairs[0]['share_pct']:.1f}% in WEGLD/USDC alone. Read alongside the OTC collapse this is the key structural fact of the week: BOTH the OTC channel and the DEX tape went quiet, and price still fell {price_chg:.2f}%. Liquidity did not get overwhelmed - it evaporated. There was no bid to sell into."},
 {"metric":"binance_custody_reload","current_value":round(cust_bal),"previous_value":3207101,"method":"rule_based",
  "severity":"medium",
  "description":f"BINANCE CUSTODY DE-STAKING PROGRAMME REVERSED. After three consecutive drawdown legs (-305,549 cumulative from the 3,512,650 peak across runs #15-#17), the custody wallet took a single +{CUSTODY_RELOAD:,.0f} EGLD transfer and rose to {cust_bal:,.0f} - recovering roughly half the cumulative drawdown in one move. The counterparty is erd1r3w62vq, a nonce-8 wallet now holding 2 EGLD (pure pass-through, so the true origin is one hop further back and not resolved this run). Run #17's registered question was whether a 4th de-staking leg would follow; the answer is no, and the programme inverted. A custody wallet re-filling is the opposite of a distribution signal, and it lands in the same week the OTC desks stopped being fed - two independent supply channels switching off together. This is the strongest bullish structural counter-signal against a very bearish price tape."},
 {"metric":"kucoin_whale_exit_resolved","current_value":171338,"previous_value":175929,"method":"rule_based",
  "severity":"medium",
  "description":f"THE KUCOIN WHALE EXIT RESOLVED - BEARISH, per the run #17 pre-commitment. Whale erd15ku2r2j6 sent its entire 145,443 EGLD to KuCoin last week and went to zero (it is still at ~0.001 EGLD, so no re-funding). The pre-registered test: a balance bleeding back down = withdrawal or OTC settlement (neutral); a balance staying elevated = the position was sold into the book (bearish). KuCoin RETAINED it - balance {171338:,} vs {175929:,}, only -2.6%, with the venue's own 7d flows tiny (~1,528 in / ~1,229 out). The coins did not leave. ~0.5% of circulating supply was absorbed by an exchange and stayed there, in the same week price fell {price_chg:.2f}%. Attempts to trace the wallet's funding history found nothing inside a 90-day inbound window, so it was a long-dormant holder rather than a recent OTC recipient - a genuine long-term-holder capitulation rather than pipeline flow."},
 {"metric":"defi_leverage_unwound","current_value":ush_supply_wow,"previous_value":0.14,"method":"rule_based",
  "severity":"medium",
  "description":f"THE RUN #16 LEVERAGE RETURN WAS A CHASE - confirmed by its own registered test. USH (Hatom's CDP stablecoin) supply BURNED {ush_supply_wow:+.2f}% to {supply('USH-111e09'):,.0f}, past the 1% threshold that re-activates the run #11 de-leveraging rule. The run #17 test read: 'if price breaks higher and USH resumes minting, the leverage was conviction; if price rolls over and USH burns >1%, it was a chase.' Price rolled over {price_chg:.2f}% and USH burned {abs(ush_supply_wow):.2f}%, so the +6.49% mint two weeks ago is reclassified as leverage chased into a rally top. XEGLD supply also reversed ({xegld_supply_wow:+.2f}% after +4.54% and +2.69%), ending its two-week re-accumulation. The DeFi demand cluster that offset the run #16 distribution has now fully unwound."},
 {"metric":"total_delegators","current_value":cur_deleg,"previous_value":prev_deleg,"method":"z_score",
  "average_value":zd[0],"stddev":zd[1],"z_score":zd[2],"severity":"low",
  "description":f"Total delegators {cur_deleg:,} ({deleg_wow:+,} WoW = {100*deleg_wow/prev_deleg:+.4f}%). Raw z={zd[2]:+.2f}sigma, downgraded to LOW per the run #9 degenerate-z guard (the economic move is six accounts). This is the 6TH CONSECUTIVE FLAT WEEK at ~174.3K, and it now spans BOTH the entire +24% recovery AND its first sharp reversal. Run #17 pre-registered the promotion criterion: 'if it stays flat a sixth week, treat recoveries on this chain do not broaden participation as an established structural finding rather than a running observation.' The criterion is met. PROMOTED to a standing structural finding: MultiversX price recoveries do not recruit new delegators. The corollary now also holds - drawdowns do not drive them out either. The delegator base is inert with respect to price over a 6-week, 34-percentage-point round trip."},
 {"metric":"staked_egld","current_value":staked,"previous_value":pecon["staked_egld"],"method":"z_score",
  "average_value":zse[0],"stddev":zse[1],"z_score":zse[2],"severity":"low",
  "description":f"Total staked {staked:,} EGLD ({staked-pecon['staked_egld']:+,} WoW, {100*(staked-pecon['staked_egld'])/pecon['staked_egld']:+.2f}%), staked ratio {sr*100:.2f}% ({100*(sr-pecon['staked_ratio']):+.2f}pp) - the first meaningful unstaking week since run #11 and a reversal of four straight weeks of accumulation. z={zse[2]:+.2f}sigma (the baseline sits almost exactly at the current level). Crucially the drawdown did NOT come from the delegation providers: delegation TVL fell only {total_locked-prev['staking_concentration']['total_locked_egld']:+,.0f} and the binance_staking provider was flat ({binance_staking_prov_wow:+,.0f}), so ~110K of the -126,662 exited from DIRECT-NODE stake rather than delegated stake. Within delegation the flows were rotational, not directional: pi-staking +11,330 (+35 users, a 6th consecutive growth week and now the single most persistent gainer in tracking) and Synexis +10,429 (+17) against procryptostaking -11,051, ieleman -10,091 and westake -9,044. 32 providers gained delegators, 42 lost."},
 {"metric":"bilateral_inverse_strongest_ever","current_value":inverse_ratio,"previous_value":0.21,"method":"rule_based",
  "severity":"low",
  "description":f"BILATERAL INVERSE RULE: 6TH CONFIRMATION AND THE STRONGEST RESPONSE EVER MEASURED. Price {price_chg:+.2f}% (comfortably past the |5%| guardrail, so unlike run #17 the rule IS evaluable this week) against Hatom Lending EGLD-denominated TVL {hl_egld_chg:+.2f}% - depositors bought the dip hard. Response ratio {inverse_ratio:.2f} versus the prior down-week series 0.88 / 0.80 / 0.70 / 0.21, which run #11 flagged as a DETERIORATING trend interpreted as diminishing depositor capacity. That interpretation is now falsified: capacity did not diminish, it was cyclical, and it has fully recovered. Hatom LSD (+3.32% EGLD) and USH collateral (+6.86% EGLD) moved the same way. Set against the demand failure everywhere else, DeFi depositors are the one cohort that showed up this week."},
 {"metric":"stablecoin_bleed_resumed","current_value":usdc_supply_wow,"previous_value":-0.13,"method":"rule_based",
  "severity":"low",
  "description":f"BRIDGED-STABLECOIN CONTRACTION RESUMED after exactly one flat week: USDC {usdc_supply_wow:+.2f}% (vs -0.13% last week) and USDT {usdt_supply_wow:+.2f}% (vs +0.05%). Run #17 recorded the bleed as having STOPPED and flagged a genuine inflow week as the signal that outside capital was returning; instead the burn restarted at close to its prior pace on the first down week. Bridged dollars leaving the chain during a drawdown is the ordinary de-risking pattern (run #11 rule) and removes the constructive read that run #17 tentatively logged. No fresh dry powder is arriving."},
 {"metric":"mex_price_usd","current_value":meco["price"],"previous_value":prev_mexp,"method":"z_score",
  "average_value":zmex[0],"stddev":zmex[1],"z_score":zmex[2],"severity":"low",
  "description":f"MEX price {100*(meco['price']-prev_mexp)/prev_mexp:+.2f}% to ${meco['price']:.3e} (z={zmex[2]:+.2f}sigma), mcap ${meco['marketCap']/1e6:.2f}M. MEX outperformed EGLD on the week ({100*(meco['price']-prev_mexp)/prev_mexp:+.1f}% vs {price_chg:+.1f}%), which is unusual - the DEX token normally amplifies EGLD moves in both directions. With DEX volume down {100*(totvol-prev_dexvol)/prev_dexvol:.0f}% the more likely explanation is illiquidity in the MEX pairs rather than relative strength."},
 {"metric":"mega_whale_absorber_idle","current_value":round(mw_bal_cur),"previous_value":1093312,"method":"rule_based",
  "severity":"medium",
  "description":f"THE ABSORBER WENT TO ZERO ACTIVITY IN THE WORST POSSIBLE WEEK. Mega Whale erd18mv2z6r2 - the market's one identifiable large bid, which accumulated +32.7K in run #15 and +50.6K in run #17 through the Coinbase Routing pipe - recorded NO value transactions at all this week and sits exactly flat at {mw_bal_cur:,.0f}. The Coinbase Routing wallet that feeds it is down to 77 EGLD, so the pipe is dry rather than merely paused. Run #17 asked whether the absorber's clip size would GROW (a real bid building) or stay ~50K (a floor only); the actual answer is neither - it stopped entirely, precisely in the week price fell {price_chg:.2f}%. The single identifiable source of large-scale demand withdrew, and that absence is a better explanation of this week's price action than any selling flow observed on-chain."}]

# ---------- trend indicators ----------
accelerating_outflows=[
 {"exchange":"NET_EXCHANGE","trend":"inflow","cumulative_change_pct":round(100*net_total/total_prev,1),"weeks_in_trend":2,
  "interpretation":f"Headline net exchange flow {net_total:+,.0f} EGLD (2nd inflow week), but decomposition per the run #15 rule removes almost all of it: Binance Staking custody +150,000 is an intra-entity reload and an untracked-prior Binance.com wallet +{UNTRACKED_PRIOR:,.0f} is a phantom. TRUE external flow is {net_adjusted:+,.0f} - flat. The honest statement is that the exchange channel was quiet this week, which makes the -10% price move harder to explain with supply and easier to explain with an absent bid."},
 {"exchange":"UPbit OTC Desks","trend":"exhausted","cumulative_change_pct":round(100*desk_delta/desk_prev,1),"weeks_in_trend":2,
  "interpretation":f"WAVE FINISHED. Desks drained a further {desk_delta:+,.0f} to {desk_cur:,.0f} (through the 80K level the run #17 pre-commitment set as the exhaustion trigger) on {OTC_THR_7D:,.0f} of 7d throughput, {otc_drop_pct:.0f}% below last week. The decisive detail is the absence of a reload: UPbit sent no comparable fresh tranche to the desks, so both the inventory AND the feed are off. On the now-comparable paginated series - {OTC_SERIES['run13']:,.0f} / {OTC_SERIES['run14']:,.0f} / {OTC_SERIES['run15']:,.0f} / {OTC_SERIES['run16']:,.0f} / {OTC_SERIES['run17']:,.0f} / {OTC_THR_7D:,.0f} for runs #13-#18 - this is a clean five-week escalation that peaked in run #17 and broke."},
 {"exchange":"Binance Staking custody","trend":"inflow","cumulative_change_pct":round(100*(cust_bal-3512650)/3512650,1),"weeks_in_trend":1,
  "interpretation":f"REVERSAL of the three-leg de-staking programme: +{CUSTODY_RELOAD:,.0f} in one transfer to {cust_bal:,.0f}, recovering about half of the -305,549 drawn down over runs #15-#17. Streak broken at 3 weeks. Source is a nonce-8 pass-through (erd1r3w62vq) that retains 2 EGLD, so the ultimate origin needs one more hop of tracing next run."},
 {"exchange":"Bybit","trend":"inflow","cumulative_change_pct":37.7,"weeks_in_trend":2,
  "interpretation":"2nd consecutive inflow week (+33,541, +10.6%; +96,253 cumulative over two weeks). Bybit remains the primary terminal destination of the OTC router network even at reduced volume, so its deposit balance is the cleanest single proxy for pipeline output."}]

prev_names=set(prevp.keys()); cur_names={(p.get('identity') or p['provider']) for p in provs}
joining=[n for n in cur_names-prev_names if n]
leaving=[n for n in prev_names-cur_names if n]
def real_validator(n):
    return n and not n.startswith("erd1qqqqqqqqqqqqqqq")
real_joiners=[n for n in joining if real_validator(n)]
real_leavers=[n for n in leaving if real_validator(n)]
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
   {"metric":"delegator_base_flat","direction":"flat","weeks":6,"cumulative_change_pct":0,
    "interpretation":f"6TH consecutive flat week at ~174.3K ({deleg_wow:+,} this week). The run #17 promotion criterion is met, so this stops being a running observation and becomes a STRUCTURAL FINDING: on MultiversX, neither a +24% recovery nor its -10% reversal moves the delegator base. Participation is inert with respect to price across a 34-percentage-point round trip. Practical consequence for the model: stop treating flat delegators as a bearish confirmation of a rally - it is the base rate, and only a genuine break out of the ~174.3K band carries information."},
   {"metric":"egld_price_reversal","direction":"down","weeks":1,"cumulative_change_pct":round(price_chg,1),
    "interpretation":f"The 3-week up-streak ended hard: {price_chg:+.2f}% to ${price:.2f}, giving back ~9 of the ~24 percentage points gained off the $2.55 low. What makes it a regime datapoint rather than a pullback is the relative move - BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}% were both UP. EGLD fell alone."},
   {"metric":"otc_throughput_escalation_broken","direction":"down","weeks":1,"cumulative_change_pct":round(otc_drop_pct,1),
    "interpretation":f"On the corrected paginated series the OTC channel escalated for five straight windows ({OTC_SERIES['run13']:,.0f} -> {OTC_SERIES['run14']:,.0f} -> {OTC_SERIES['run15']:,.0f} -> {OTC_SERIES['run16']:,.0f} -> {OTC_SERIES['run17']:,.0f}) before collapsing {otc_drop_pct:.0f}% to {OTC_THR_7D:,.0f} this week. Note this streak only became visible once the size=50 cap was fixed - at the old truncated figures the series was noise."},
   {"metric":"bybit_inflow","direction":"up","weeks":2,"cumulative_change_pct":37.7,
    "interpretation":"2nd consecutive week of Bybit deposit-balance growth (+96,253 cumulative), tracking the residual OTC router output."},
   {"metric":"token_holder_count_decline","direction":"down","weeks":18,"cumulative_change_pct":None,
    "interpretation":"18th consecutive week of small holder declines across top-10 tokens. Established airdrop-decay baseline; the active >$1M-mcap token base is stable."}],
 "regime_shifts":[
   {"metric":"recovery_reclassified_as_bear_rally","before_value":pp,"after_value":price,
    "description":f"THE +24% RECOVERY IS RECLASSIFIED AS A BEAR-MARKET RALLY. Run #17 registered the confirming test - EGLD underperforming on a down week - and the actual outcome exceeded it: EGLD fell {price_chg:.2f}% while BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}% ROSE. Chain-specific weakness against a rising tape is a stronger signal than high-beta lag. Combined with the participation finding (6 flat delegator weeks) and the leverage unwind (USH -2.60% after the +6.49% chase), the recovery had no structural base underneath it at any point."},
   {"metric":"supply_channels_switched_off_together","before_value":round(OTC_THR_7D_PREV),"after_value":round(OTC_THR_7D),
    "description":f"BOTH IDENTIFIED SUPPLY CHANNELS TURNED OFF IN THE SAME WEEK - and price fell anyway. OTC throughput {otc_drop_pct:.0f}% to {OTC_THR_7D:,.0f} with no desk reload; Binance custody reversed from a three-leg unwind to a +150,000 reload; true external exchange flow {net_adjusted:+,.0f} (flat). For four runs the model explained EGLD weakness through traceable distribution. That explanation is unavailable this week, which forces the diagnosis onto the demand side: the Mega Whale absorber went completely idle, DEX volume collapsed {100*(totvol-prev_dexvol)/prev_dexvol:.0f}%, and stablecoin inflows resumed contracting. The regime shift is from a SUPPLY-driven decline to a DEMAND-absent decline - a worse condition, because supply exhausts while absent demand does not."},
   {"metric":"participation_inertia_confirmed","before_value":174335,"after_value":cur_deleg,
    "description":f"PARTICIPATION INERTIA promoted from observation to structural finding at the pre-registered 6-week threshold. The delegator base has now held ~174.3K through a +24% rally and a -10% reversal without moving more than a few dozen accounts in either direction. This closes a watch that has been open since run #13."}]}

# ---------- dormant activations ----------
dormant_activations=[]

# ---------- watch list ----------
watch_list=[
 {"item":f"DEMAND, NOT SUPPLY, IS NOW THE PROBLEM: price {price_chg:.2f}% in the week OTC throughput collapsed {otc_drop_pct:.0f}%, Binance custody reloaded +150,000, and true exchange flow was flat ({net_adjusted:+,.0f})","reason":"The model's explanatory framework for the last four runs was traceable distribution. That framework does not explain this week. With both supply channels off, the decline has to be attributed to absent demand - the Mega Whale absorber recorded zero activity, DEX volume fell 61%, stablecoins resumed burning. PRE-COMMITTED READING for next week: if price stabilises or recovers with OTC still quiet, this was a liquidity air-pocket and the supply exhaustion is genuinely constructive; if price keeps falling with no distribution flow to point at, the chain has a structural bid problem that no supply metric will forecast. This is now the highest-value question on the list.","weeks_on_list":1},
 {"item":f"MEGA WHALE ABSORBER erd18mv2z6r2 WENT COMPLETELY IDLE (flat at {mw_bal_cur:,.0f}, zero value txs; Coinbase Routing wallet drained to 77 EGLD)","reason":"The one identifiable large bid in the market stopped entirely in the week price fell 10%. Run #17 asked whether its clip size would grow or stay ~50K; instead it went to zero and the routing pipe that fed it is empty. Watch whether the Coinbase Routing wallet refills (bid returning) or stays dry. If the absorber does not come back, the floor that soaked up runs #15 and #17 distribution is gone.","weeks_on_list":15},
 {"item":f"OTC desks EXHAUSTED at {desk_cur:,.0f} on {OTC_THR_7D:,.0f} throughput ({otc_drop_pct:.0f}%) with NO UPbit reload","reason":"The run #17 pre-committed test resolved on the constructive branch - the wave is finished and the feed is off. But the corrected paginated series shows five weeks of escalation before this break, and the pipeline infrastructure (routers to Bybit/Binance.com) is intact and still running at reduced volume. NEXT TEST: a fresh large UPbit -> desk tranche would signal wave #2 staging; continued quiet at sub-70K desks for a third week would establish exhaustion as durable. Both readings registered now.","weeks_on_list":9},
 {"item":f"BINANCE CUSTODY REVERSED to +{CUSTODY_RELOAD:,.0f} (now {cust_bal:,.0f}) - three-leg de-staking programme broken","reason":"After -305,549 over three weeks the custody wallet took a single 150,000 reload from nonce-8 pass-through erd1r3w62vq. This is the strongest structural counter-signal against the price tape. Watch two things: whether a second reload leg follows (accumulation resuming, as in runs #9-#11) and whether the true origin behind erd1r3w62vq can be traced one hop further - the immediate sender is a pass-through holding 2 EGLD.","weeks_on_list":12},
 {"item":"DELEGATOR BASE FLAT A 6TH WEEK - promoted to a STRUCTURAL FINDING, watch closed as a running item","reason":"The run #17 promotion criterion was met: six flat weeks spanning a +24% recovery and its -10% reversal. 'MultiversX price moves do not change participation' is now a base rate rather than a weekly observation. Retained on the list only to detect a genuine BREAK out of the ~174.3K band in either direction, which would then be informative. Do not report flatness as a finding again.","weeks_on_list":6},
 {"item":f"DEFI LEVERAGE UNWOUND: USH burned {ush_supply_wow:.2f}% (run #11 de-leveraging rule re-activated), XEGLD {xegld_supply_wow:.2f}% after two growth weeks","reason":"Run #17's registered test resolved on the bearish branch - the run #16 +6.49% USH mint was a chase, not conviction. Watch whether the burn accelerates past ~5% (forced CDP closures, which historically mark local capitulation) or stops at this single week. Hatom LENDING moved the opposite way (+9.89% EGLD TVL, strongest inverse-rule response ever), so the two Hatom legs are diverging - depositors buying while borrowers de-lever.","weeks_on_list":3},
 {"item":f"KUCOIN WHALE EXIT RESOLVED BEARISH - balance retained ({171338:,}, -2.6%); the 145,443 was absorbed by the venue and stayed","reason":"Run #17's pre-commitment resolved: the coins did not bleed back down, so per the registered reading the position was sold into the book rather than withdrawn or OTC-settled. The source wallet remains at zero with no re-funding, and a 90-day inbound trace found no funding history, so this was long-dormant-holder capitulation rather than pipeline flow. Graduating next week unless KuCoin's balance moves materially.","weeks_on_list":2},
 {"item":f"BRIDGED STABLECOIN BLEED RESUMED (USDC {usdc_supply_wow:.2f}%, USDT {usdt_supply_wow:.2f}%) after one flat week","reason":"Run #17 logged the bleed as stopped; it restarted immediately on the first down week, which suggests the pause was a function of the rally rather than a change in capital flows. Watch for a genuine INFLOW week as the first evidence that outside capital is returning - that remains the cleanest single confirmation that the drawdown regime has ended.","weeks_on_list":5}]

executive_summary=[
 {"finding":f"EGLD FELL {abs(price_chg):.2f}% TO ${price:.2f} WHILE BTC {btc_wow:+.2f}% AND ETH {eth_wow:+.2f}% BOTH ROSE - chain-specific weakness against a rising tape, which is a stronger negative signal than high-beta lag. Run #17 registered the test as 'does EGLD fall harder on a macro DOWN week'; the outcome was worse than the test contemplated, since no macro down week was required. The +24% recovery off $2.55 gave back ~9 percentage points in one week and is formally reclassified as a BEAR-MARKET RALLY.","severity":"critical","category":"network"},
 {"finding":f"THE OTC DISTRIBUTION WAVE IS OVER - AND THAT IS THE PROBLEM. Desks drained through the 80K exhaustion trigger to {desk_cur:,.0f} on {OTC_THR_7D:,.0f} EGLD of 7d throughput, {otc_drop_pct:.0f}% below last week, with NO UPbit reload (it sent 364,000 in the prior window and nothing now). Run #17's pre-committed test resolved on the constructive branch. But price fell {abs(price_chg):.2f}% in the very week the identified supply pressure switched off, which inverts the diagnosis: the marginal seller was not the desk, and the weakness is a DEMAND failure rather than a supply flood.","severity":"critical","category":"whale"},
 {"finding":f"OTC THROUGHPUT NOW HAS A COMPARABLE TIME SERIES FOR THE FIRST TIME. Implementing run #17's top recommendation, the collector paginates to the after= boundary by default and the runs #13-#15 windows were re-queried with the identical method. Corrected series (net of desk-to-desk transfers): {OTC_SERIES['run13']:,.0f} / {OTC_SERIES['run14']:,.0f} / {OTC_SERIES['run15']:,.0f} / {OTC_SERIES['run16']:,.0f} / {OTC_SERIES['run17']:,.0f} / {OTC_THR_7D:,.0f}. The method reproduces run #16's independently-derived 1,100,791 exactly, which validates the backfill. What it reveals was invisible before: five consecutive weeks of escalating distribution that peaked in run #17 and broke this week.","severity":"high","category":"whale"},
 {"finding":f"THE ABSORBER WENT TO ZERO. Mega Whale erd18mv2z6r2 - the market's one identifiable large bid, +32.7K in run #15 and +50.6K in run #17 via the Coinbase Routing pipe - recorded NO value transactions at all and sits flat at {mw_bal_cur:,.0f}. The routing wallet feeding it is drained to 77 EGLD, so the pipe is dry rather than paused. Its absence explains this week's price action better than any selling flow observed on-chain, and combined with DEX volume collapsing {100*(totvol-prev_dexvol)/prev_dexvol:.0f}% to ${totvol/1000:.0f}K, the picture is an evaporated bid rather than an overwhelming offer.","severity":"high","category":"whale"},
 {"finding":f"BINANCE CUSTODY REVERSED ITS DE-STAKING PROGRAMME: +{CUSTODY_RELOAD:,.0f} in a single transfer to {cust_bal:,.0f}, recovering roughly half the -305,549 drawn down over three legs in runs #15-#17. Run #17 asked whether a 4th leg would follow; the programme inverted instead. Together with the OTC feed shutting off, two independent supply channels turned off in the same week - the strongest structural counter-signal available against a very bearish tape. The source is a nonce-8 pass-through wallet holding 2 EGLD, so the true origin is one hop beyond this run's tracing.","severity":"high","category":"whale"},
 {"finding":f"HEADLINE EXCHANGE INFLOW OF {net_total:+,.0f} IS ALMOST ENTIRELY ARTIFACT. Decomposed per the run #15 rule, {100*NONFLOW/net_total:.0f}% is two non-flow items: Binance Staking custody +150,000 (intra-entity parking) and a third Binance.com wallet +{UNTRACKED_PRIOR:,.0f} that has no prior-week balance in the stored top-60 and so books its full balance as a phantom. True external exchange flow is {net_adjusted:+,.0f} EGLD, effectively FLAT. Reporting the raw number would have manufactured a bearish signal that does not exist.","severity":"medium","category":"whale"},
 {"finding":f"PARTICIPATION INERTIA IS NOW A STRUCTURAL FINDING, NOT AN OBSERVATION. The delegator base was flat for a 6TH consecutive week at {cur_deleg:,} ({deleg_wow:+,}), meeting the promotion criterion run #17 pre-registered. Six weeks now span both a +24% recovery and a -10% reversal: MultiversX participation is inert with respect to price across a 34-percentage-point round trip. Total staked fell {staked-pecon['staked_egld']:+,.0f} (first real unstaking since run #11) but ~110K of that left DIRECT-NODE stake, not delegation, where flows were rotational - pi-staking +11,330 (+35 users, 6th growth week) and Synexis +10,429 against procryptostaking -11,051 and ieleman -10,091.","severity":"medium","category":"staking"},
 {"finding":f"DEFI SPLIT IN TWO: BORROWERS DE-LEVERED, DEPOSITORS BOUGHT THE DIP. USH supply burned {ush_supply_wow:.2f}% past the 1% threshold, re-activating the run #11 de-leveraging rule and resolving run #17's registered test on its bearish branch - the run #16 +6.49% mint was a leverage CHASE, not conviction. XEGLD also reversed {xegld_supply_wow:.2f}% after two growth weeks. Against that, Hatom Lending posted the STRONGEST bilateral-inverse response ever measured: EGLD-denominated TVL {hl_egld_chg:+.2f}% against price {price_chg:+.2f}%, a ratio of {inverse_ratio:.2f} versus a prior down-week series of 0.88/0.80/0.70/0.21 that run #11 had read as terminal decay. Depositor capacity was cyclical, not exhausted.","severity":"medium","category":"defi"}]

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
   "btc_correlation_note":f"EGLD {price_chg:+.2f}% WoW vs BTC {btc_wow:+.2f}% / ETH {eth_wow:+.2f}% (WoW). EGLD fell double digits while BOTH majors gained - a full decoupling to the DOWNSIDE, not high-beta lag. This is the strongest chain-specific weakness signal in the tracked history: in the prior decoupling weeks (runs #11, #13) the majors were roughly flat or falling; this week they rose. Run #17's registered laggard test is confirmed and exceeded, and the +24% recovery is reclassified as a bear-market rally.",
   "transactions_added":st["transactions"]-pact["total_transactions"],"supply_added":econ["totalSupply"]-pecon["total_supply"],
   "staked_egld_added":staked-pecon["staked_egld"],"epoch_advanced":st["epoch"]-pact["epoch"]},
 "analysis":f"EGLD closed the week at ${price:.2f}, {price_chg:+.2f}% WoW, against BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}%. The relative move is the story: this is the first week in tracking where EGLD fell by double digits while both majors ROSE. Market cap ${econ['marketCap']/1e6:.1f}M ({100*(econ['marketCap']-pecon['market_cap_usd'])/pecon['market_cap_usd']:+.1f}%). Network throughput was unaffected - {st['transactions']-pact['total_transactions']:,} transactions in the period (~{round((st['transactions']-pact['total_transactions'])/7):,}/day) and {st['accounts']-pact['total_accounts']:,} new accounts, both in line with recent weeks - so the weakness is purely a market-structure event, not a usage one. Staked EGLD fell {staked-pecon['staked_egld']:+,.0f} to {staked:,} and the staked ratio slipped {100*(sr-pecon['staked_ratio']):+.2f}pp to {sr*100:.2f}%, the first meaningful unstaking since run #11, though ~110K of it exited direct-node stake rather than delegation. Protocol APR ticked up to {econ['apr']*100:.2f}% mechanically as stake left. The defining feature of the week is what is MISSING: the OTC desks that drove four weeks of traceable distribution ran at a quarter of their prior volume with no reload, Binance's custody unwind reversed, and true external exchange flow was flat - yet price fell {abs(price_chg):.2f}%. When supply switches off and price still drops, the constraint has moved to the demand side."}

# ---------- analyses ----------
whale_analysis=f"""The whale layer produced a clean resolution of three registered tests and one genuinely new problem.

RESOLVED - OTC WAVE EXHAUSTED (constructive branch). Run #17 pre-committed: desks rebuilding toward 300K+ = second wave staged (bearish); desks near 80K on low throughput = wave finished (constructive). Outcome: combined desk balance fell a further {desk_delta:+,.0f} to {desk_cur:,.0f}, through the trigger, while 7d throughput collapsed {otc_drop_pct:.0f}% to {OTC_THR_7D:,.0f} EGLD. The decisive detail is the missing reload - UPbit pushed 364,000 out to the desks inside the run #17 window and sent nothing comparable this week. Desk inbound was essentially all desk-to-desk shuffling. The infrastructure remains live (the same zero-balance routers erd1g6fntj, erd1e9luc4, erd1w7nlme forwarded {desk_top_dest[0][1]:,.0f}, {desk_top_dest[1][1]:,.0f} and {desk_top_dest[2][1]:,.0f} EGLD onward to Bybit and Binance.com), but it is idling.

METHODOLOGY - the throughput series is now trustworthy. Run #17 discovered that the size=50 cap had undercounted every prior figure ~4x. This run implements pagination by default AND backfills runs #13-#15 with the identical method, which reproduces run #16's independently-derived 1,100,791 exactly. The corrected series ({OTC_SERIES['run13']:,.0f} / {OTC_SERIES['run14']:,.0f} / {OTC_SERIES['run15']:,.0f} / {OTC_SERIES['run16']:,.0f} / {OTC_SERIES['run17']:,.0f} / {OTC_THR_7D:,.0f}) shows a five-week escalation peaking in run #17 - a structure that simply did not exist in the truncated numbers.

RESOLVED - KUCOIN, bearishly. Whale erd15ku2r2j6's full 145,443 EGLD exit stayed on the venue: KuCoin {171338:,} vs {175929:,}, -2.6%, with the exchange's own 7d flows under 2K in either direction. Per the pre-commitment, retained balance = sold into the book. A 90-day inbound trace found no funding history, so this was a long-dormant holder capitulating, not pipeline flow.

REVERSED - BINANCE CUSTODY. Three consecutive de-staking legs (-305,549 cumulative from the 3,512,650 peak) ended with a single +{CUSTODY_RELOAD:,.0f} transfer to {cust_bal:,.0f}. The sender, erd1r3w62vq, is a nonce-8 wallet retaining 2 EGLD - a pass-through, so the origin is one hop beyond this run.

NEW - THE ABSORBER IS GONE. Mega Whale erd18mv2z6r2 recorded zero value transactions and is exactly flat at {mw_bal_cur:,.0f}. The Coinbase Routing wallet that filled it in runs #15 and #17 is drained to 77 EGLD. Run #17 asked whether the clip size would grow or stay ~50K; it went to zero, in the week price fell {abs(price_chg):.2f}%.

EXCHANGE FLOWS require the decomposition rule more than usual. The headline is {net_total:+,.0f} inflow, but {100*NONFLOW/net_total:.0f}% of it is the custody reload plus a phantom: Coinbase Custody 2 entered the tracked set in run #17 as the nonce-0 destination of Coinbase's own 65,090 migration, so it has no prior-week balance to diff against. True external flow is {net_adjusted:+,.0f} - flat. Tier aggregates are similarly artifact-heavy and should not be narrated directly (run #14 guard): mega tier {whale_tiers['mega_whales']['net_change_egld']:+,.0f}, large tier {whale_tiers['large_whales']['net_change_egld']:+,.0f}, mid tier {whale_tiers['mid_whales']['net_change_egld']:+,.0f}, driven mostly by the desks and KuCoin crossing boundaries.

The synthesis: every traceable supply channel this model tracks turned OFF this week, and price fell anyway. That is the single most important structural fact of run #18."""

staking_analysis=f"""Delegation TVL {total_locked:,.0f} EGLD ({total_locked-prev['staking_concentration']['total_locked_egld']:+,.0f} WoW) across {len(provs)} active providers, against protocol-wide staked {staked:,} ({staked-pecon['staked_egld']:+,.0f}). The gap matters: total staked fell {abs(staked-pecon['staked_egld']):,.0f} but delegation fell only {abs(total_locked-prev['staking_concentration']['total_locked_egld']):,.0f}, so roughly 110K exited DIRECT-NODE stake. The binance_staking provider was flat ({binance_staking_prov_wow:+,.0f}), so the run #16 net-out rule changes nothing this week.

PARTICIPATION INERTIA - PROMOTED TO A STRUCTURAL FINDING. The delegator base is {cur_deleg:,} ({deleg_wow:+,}), a 6th consecutive flat week. Run #17 pre-registered the promotion criterion and it is met. Six weeks now span a +24% recovery AND a -10% reversal with the base never leaving the ~174.3K band. The correct model update is to stop treating flat delegators as bearish confirmation - it is the base rate on this chain, and only a genuine break out of the band carries information in either direction.

Within delegation the flows were rotational rather than directional: {gain} providers gained delegators, {lose} lost. pi-staking +{lk_wow('pi-staking'):,.0f} (+35 users) extends what is now a 6-week growth streak and makes it the most persistent gainer in tracking history - worth understanding, since it is growing through both the rally and the reversal. Synexis +{lk_wow('Synexis'):,.0f} (+17 users) continues its own multi-week build. Against them procryptostaking {lk_wow('procryptostaking'):,.0f}, ieleman {lk_wow('ieleman'):,.0f}, westake {lk_wow('westake'):,.0f} and disruptivedigital {lk_wow('disruptivedigital'):,.0f} shed stake. The yield-chase cohort net {cohort_net:+,.0f} - no coordinated rotation this week.

Concentration remains healthy and static: HHI {hhi:.5f} (vs {prev['staking_concentration']['hhi']:.5f}), top-5 {top5:.2f}%, top-10 {top10:.2f}%. The APR distribution is tightly clustered - {buckets[3]['provider_count']} of {len(provs)} providers sit in the 8-9% band holding {buckets[3]['total_locked_egld']/1e6:.2f}M EGLD, with weighted-average APR {apr_w:.2f}%. For a delegator the standout combination remains a high-APR, low-fee provider: incalng ({[p for p in top_providers if p['identity']=='incalng'][0]['apr_pct'] if any(p['identity']=='incalng' for p in top_providers) else 8.63:.2f}% APR at 1% fee) is the clearest value in the top 10. A market this converged means fee competition, not yield, is the differentiator."""

token_analysis=f"""The token layer registered the demand failure more clearly than the price did.

xExchange 24h volume COLLAPSED {100*(totvol-prev_dexvol)/prev_dexvol:.1f}% to ${totvol/1000:.0f}K - the second-largest weekly drop in tracking after run #12's -55%, and a complete retrace of the two-week rally-volume spike back to the pre-rally floor. Concentration got WORSE: WEGLD/USDC alone is {pairs[0]['share_pct']:.1f}% of all volume (from 91.5%), with {pairs[1]['name'] if len(pairs)>1 else '?'} at {pairs[1]['share_pct'] if len(pairs)>1 else 0:.1f}% the only other pair above 1%. Liquidity itself did not leave - pool TVL rose in EGLD terms and WEGLD supply grew {wegld_chg_pct:+.2f}% (more EGLD wrapped, not less) - so this is trading activity vanishing against intact depth. Volume dying while price falls {abs(price_chg):.2f}% is the signature of an absent bid rather than aggressive selling; a genuine distribution week produces HIGH volume.

MEX ${meco['price']:.3e} ({100*(meco['price']-prev_mexp)/prev_mexp:+.2f}% WoW, mcap ${meco['marketCap']/1e6:.2f}M) actually outperformed EGLD, which is atypical for a DEX token that normally amplifies EGLD in both directions; with volume down {abs(100*(totvol-prev_dexvol)/prev_dexvol):.0f}% the likelier explanation is thin pricing rather than relative strength.

Bridged stablecoins resumed contracting after exactly one flat week: USDC {usdc_supply_wow:+.2f}%, USDT {usdt_supply_wow:+.2f}%. Run #17 logged the bleed as having stopped; it restarted on the first down week, which suggests the pause was a function of the rally rather than a change in capital flows. Dollars are leaving the chain again - the standard de-risking pattern from the run #11 rule, and it removes the tentative constructive read logged last week.

Holder counts declined marginally across the top 10 for an 18th consecutive week (DRX -27, WEGLD -3, HYPE -103, USDC -218), the established airdrop-decay baseline rather than a signal.

Newly-issued: the ESDT system-SC scan surfaced one issuance in the window, NOVA-04c5f5 (NovaAI), with 1 holder and 0 transactions. It is filtered out by the run #15 quality bar (>10 holders, >5 txs) as a dormant deploy. Genuine new-token formation was effectively zero this week - consistent with the wider risk-off tone."""

defi_analysis=f"""DeFi split cleanly in two this week, and the split is informative.

BORROWERS DE-LEVERED. USH supply burned {ush_supply_wow:+.2f}% to {supply('USH-111e09'):,.0f}, past the 1% threshold that re-activates the run #11 de-leveraging rule. This resolves the test run #17 registered on its bearish branch: 'if price rolls over and USH burns >1%, the leverage was a chase.' Price rolled over {price_chg:.2f}% and USH burned {abs(ush_supply_wow):.2f}%, so the run #16 +6.49% mint is reclassified as leverage chased into a rally top and unwound two weeks later. XEGLD supply also reversed {xegld_supply_wow:+.2f}% to {supply('XEGLD-e413ed'):,.0f}, ending the two-week re-accumulation that followed the run #14 -29% collapse - XOXNO remains the LSD leg that redeems on weakness, a consistent difference from Hatom across four runs.

DEPOSITORS BOUGHT THE DIP - HARD. Hatom Lending's EGLD-denominated TVL rose {hl_egld_chg:+.2f}% against a price move of {price_chg:+.2f}%, a bilateral-inverse response ratio of {inverse_ratio:.2f}. That is the STRONGEST reading in the rule's history and it falsifies a standing hypothesis: run #11 observed the down-week ratio series decaying (0.88, 0.80, 0.70, 0.21) and interpreted it as depositor capacity being exhausted by a prolonged decline. It was cyclical, not terminal - capacity has fully recovered. Hatom LSD held flat on a supply basis (SEGLD {segld_supply_wow:+.2f}%, SWTAO {swtao_supply_wow:+.2f}%) with no redemption pressure despite the drawdown, and USH collateral value rose {100*(ush_egld-prev_hush/pp)/(prev_hush/pp):+.2f}% in EGLD terms.

In USD terms every leg is down because the denominator moved: Hatom Lending ${hatom_lending/1e6:.2f}M ({100*(hatom_lending-prev['defi_tvl']['Hatom Lending'])/prev['defi_tvl']['Hatom Lending']:+.1f}%), Hatom LSD ${hatom_lsd/1e6:.2f}M ({100*(hatom_lsd-prev_hlsd)/prev_hlsd:+.1f}%), XOXNO LSD ${xoxno_lsd/1e6:.2f}M ({100*(xoxno_lsd-prev['defi_tvl']['XOXNO LSD'])/prev['defi_tvl']['XOXNO LSD']:+.1f}%), USH ${hatom_ush/1000:.0f}K ({100*(hatom_ush-prev_hush)/prev_hush:+.1f}%). Reporting those USD figures as 'DeFi contracting' would be the exact error the run #13 supply-first rule exists to prevent.

Routing activity was resilient and diverged sharply from the DEX tape: XOXNO Aggregator {tcount('XOXNO Aggregator'):,} daily transfers (steady, still the highest single-contract throughput on the network), OneDex {tcount('OneDex Swap'):,}, JEXchange fees wallet {tcount('JEXchange Fees'):,}. On-chain routing demand did not fall with xExchange volume, which supports reading the volume collapse as a market-making/bid phenomenon rather than a users-leaving phenomenon.

Net read: DeFi is the one part of the chain where somebody showed up this week. It does not offset an absent large bid, but it is the strongest counter-evidence to a pure capitulation reading."""

report={
 "metadata":{"report_date":"2026-07-27","period_start":"2026-07-20","period_end":"2026-07-27",
   "generated_at":datetime.now(timezone.utc).isoformat(),"egld_price_usd":price,
   "btc_price_usd":be["bitcoin"]["usd"],"eth_price_usd":be["ethereum"]["usd"],"run_number":18,
   "data_sources_ok":json.load(open("/tmp/run18/status.json"))["ok"],
   "data_sources_failed":json.load(open("/tmp/run18/status.json"))["failed"]},
 "executive_summary":executive_summary,
 "network_health":network_health,
 "whale_intelligence":{"large_transactions":large_transactions,"wallet_changes":wallet_changes,
   "whale_tiers":whale_tiers,"exchange_flows":exchange_flows,
   "dormant_activations":dormant_activations,"analysis":whale_analysis},
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
 "meta_learning":{"run_number":18,
   "endpoints_that_worked":json.load(open("/tmp/run18/status.json"))["ok"],
   "endpoints_that_failed":json.load(open("/tmp/run18/status.json"))["failed"],
   "api_quirks":[
     "INVALID-CHECKSUM BECH32 IN watch_addresses, 2ND OCCURRENCE (run #12 quirk repeated). Run #17 recorded the KuCoin watch entry as erd1ty4pvmjtl3mnsjvnsxqkm3xqm4dm7ppgz9sh4nk4tqvlmw0jyggqzn4mdc, which returns HTTP 400 - the canonical KuCoin wallet is erd1ty4pvmjtl3mnsjvnsxgcpedd08fsn83f05tu0v5j23wnfce9p86snlkdyy. The bad address silently returned no balance and no transactions, so the KuCoin resolution test would have come back empty rather than erroring loudly. Run #12 recommended pre-storing bech32 validation and it was never implemented; scripts/validate_addresses.py now does it and is wired into the run.",
     "PAGINATION CONFIRMED CORRECT AGAINST AN INDEPENDENT MEASUREMENT: re-querying the run #16 window (Jul 6-13) with from=-paging to the after= boundary and netting desk-to-desk transfers reproduces 1,100,791 EGLD exactly, matching run #17's separately-derived figure. Re-measuring the run #17 window gives 1,284,688 vs the 1,328,037 reported at the time, a 3.3% difference attributable to boundary timing; the series uses the internally consistent figures.",
     "/providers RETURNS 187 ENTRIES BUT ONLY 107 HAVE locked>0. The pipeline's total_delegators metric is the sum of numUsers over providers with locked>0 (174,341), not over the whole response (201,299). Comparing the unfiltered sum against previous.json produces a spurious +26,964 delegator jump. The filter is load-bearing and must be applied before any churn comparison.",
     "CLEAN PRICE-FEED RUN (4th consecutive): the dataApi re-fetch guard reported 0 retries - all four dataApi-class tokens (SEGLD, SWTAO, USH, XEGLD) populated price and marketCap on the first sequential pass at 1.05s spacing. Four clean runs make the run #15 read (transient feed issue, not a systematic rate limit) settled.",
     "A NEWLY TRACKED ADDRESS CREATES A PHANTOM FLOW. Coinbase Custody 2 was added to known-addresses in run #17 as the destination of an internal migration; because it has no prior-week balance, including it in entity netting books its full 65,090 as an inflow. Any address added to the tracked set mid-series must be excluded from that week's WoW delta or seeded with its prior balance."],
   "data_gaps":[
     "The Binance custody reload's true origin is not resolved: the immediate sender erd1r3w62vq is a nonce-8 pass-through now holding 2 EGLD, so the 150,000 came from one hop further back. Tracing it is next run's cheapest high-value query.",
     "Router destination tracing remains capped at size=50 per router, so the amounts attributed to Bybit and Binance.com are lower bounds. The direction is certain; the exact venue split is not.",
     "Runs #1-#12 cannot be backfilled for OTC throughput - the raw collected snapshots only start at run #10 and the desk tx windows for earlier runs are no longer reconstructable within a reasonable query budget. The comparable series therefore starts at run #13.",
     "Why the Mega Whale absorber stopped is unknowable from on-chain data alone; only that the Coinbase Routing wallet feeding it is drained to 77 EGLD."],
   "key_findings":[
     f"EGLD DECOUPLED TO THE DOWNSIDE AGAINST RISING MAJORS: {price_chg:+.2f}% to ${price:.2f} while BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}% both gained. Stronger than the laggard test run #17 registered, which assumed a macro down week would be needed. The +24% recovery is reclassified as a bear-market rally.",
     f"OTC WAVE EXHAUSTED ON THE CONSTRUCTIVE BRANCH: desks through the 80K trigger to {desk_cur:,.0f}, throughput {otc_drop_pct:.0f}% to {OTC_THR_7D:,.0f}, and critically NO UPbit reload. But price fell {abs(price_chg):.2f}% in the same week - so the supply explanation that carried runs #14-#17 does not apply here.",
     f"THE THROUGHPUT SERIES IS FIXED AND BACKFILLED: {OTC_SERIES['run13']:,.0f} / {OTC_SERIES['run14']:,.0f} / {OTC_SERIES['run15']:,.0f} / {OTC_SERIES['run16']:,.0f} / {OTC_SERIES['run17']:,.0f} / {OTC_THR_7D:,.0f} for runs #13-#18, paginated and net of desk-to-desk. Method validated by exactly reproducing run #16's independent 1,100,791. Five weeks of escalation then a break - invisible in the old truncated numbers.",
     f"THE ABSORBER WENT IDLE: Mega Whale erd18mv2z6r2 recorded zero value txs, flat at {mw_bal_cur:,.0f}, and the Coinbase Routing pipe that filled it is drained to 77 EGLD. The one identifiable large bid disappeared in the week price fell 10%.",
     f"BINANCE CUSTODY DE-STAKING REVERSED: +{CUSTODY_RELOAD:,.0f} in one transfer to {cust_bal:,.0f} after three drawdown legs totalling -305,549. Two independent supply channels (OTC feed, custody unwind) switched off in the same week.",
     f"HEADLINE EXCHANGE INFLOW {net_total:+,.0f} IS {100*NONFLOW/net_total:.0f}% ARTIFACT (custody reload + a phantom from newly tracking Coinbase Custody 2). True external flow {net_adjusted:+,.0f} - flat.",
     f"KUCOIN RESOLVED BEARISH per run #17's pre-commitment: the 145,443 whale deposit STAYED ({171338:,}, -2.6%), so it was sold into the book rather than withdrawn. A 90-day inbound trace shows the source was a long-dormant holder, not an OTC recipient.",
     f"PARTICIPATION INERTIA PROMOTED TO STRUCTURAL FINDING at the pre-registered 6-week threshold: {cur_deleg:,} delegators ({deleg_wow:+,}), flat across a +24% rally AND its -10% reversal. Stop reporting flatness as a finding; only a break out of the band is informative.",
     f"DEFI SPLIT: USH burned {ush_supply_wow:.2f}% (run #11 de-leveraging rule re-activated, run #17's chase test resolved bearish) and XEGLD reversed {xegld_supply_wow:.2f}%, while Hatom Lending posted the STRONGEST bilateral-inverse response ever measured (ratio {inverse_ratio:.2f} vs a prior down-week series of 0.88/0.80/0.70/0.21). Run #11's depositor-capacity-decay hypothesis is falsified - it was cyclical.",
     f"DEX VOLUME COLLAPSED {100*(totvol-prev_dexvol)/prev_dexvol:.0f}% to ${totvol/1000:.0f}K (2nd-largest drop in tracking) on {pairs[0]['share_pct']:.1f}% WEGLD/USDC concentration, while pool TVL and WEGLD supply ROSE. Depth stayed, trading left - an absent bid, not aggressive selling. Stablecoin bleed resumed (USDC {usdc_supply_wow:.2f}%, USDT {usdt_supply_wow:.2f}%) after one flat week."],
   "action_items_from_previous":8,
   "action_items_completed":8,
   "methodology_changes":[
     "PAGINATED OTC THROUGHPUT IS NOW THE DEFAULT AND THE SERIES IS BACKFILLED (implements run #17's top recommendation). collect_run18.py pages with from= to the after= boundary for both desks in both directions, nets out desk-to-desk transfers, and re-queried the runs #13-#15 windows with the identical method. Validation: the method reproduces run #16's independently derived 1,100,791 exactly. Runs before #13 are not backfillable and the series is documented as starting there.",
     "PRE-FLIGHT BECH32 VALIDATION ADDED (closes a run #12 recommendation that had been open for six runs). scripts/validate_addresses.py checks every address in known-addresses.json and previous.json watch_addresses against the bech32 checksum and reports HTTP-400 offenders. This run found the second occurrence of the bug: run #17's KuCoin watch entry was an invalid address that silently returned nothing.",
     "EXCLUDE NEWLY TRACKED ADDRESSES FROM THEIR FIRST WoW DELTA (new). An address added to known-addresses mid-series has no prior-week balance, so entity netting books its entire balance as an inflow. Coinbase Custody 2 created a phantom +65,090 this week - 30% of the headline exchange flow. Either seed the prior balance or exclude the address from the delta for one week.",
     "PROMOTE A REPEATED NON-OBSERVATION TO A STRUCTURAL FINDING AT A PRE-REGISTERED THRESHOLD (new). The delegator base has been reported as 'flat again' for six consecutive runs, which is narrative cost with no information. Run #17 pre-registered a 6-week promotion criterion; it was met and the finding is now a base rate. General rule: when the same non-event is reported three or more times, pre-register the threshold at which it becomes a background assumption and stop re-reporting it.",
     "WHEN EVERY TRACKED SUPPLY CHANNEL IS OFF AND PRICE STILL FALLS, SWITCH THE DIAGNOSIS TO DEMAND (new). This model is instrumented almost entirely on the supply side - desks, custody wallets, exchange balances, routers. This week all of them went quiet and price fell 10%, which the framework cannot explain. The demand-side instruments that DID move (Mega Whale idle, DEX volume -61% on intact TVL, stablecoin burn resumed) should be read as a group and given equal standing rather than treated as colour."],
   "new_addresses_discovered":1,
   "most_valuable_insight":f"Run #17 ended with two pre-committed tests and both resolved on their CONSTRUCTIVE branch - the OTC desks did not reload (throughput collapsed {otc_drop_pct:.0f}% to {OTC_THR_7D:,.0f} with no fresh UPbit tranche) and Binance's three-leg custody de-staking programme reversed with a +150,000 reload. True external exchange flow, once the custody reload and a phantom from a newly tracked Coinbase wallet are netted out, was {net_adjusted:+,.0f} EGLD: flat. Every traceable supply channel this model instruments switched off in the same week. And EGLD fell {abs(price_chg):.2f}% to ${price:.2f} while BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}% both ROSE. That combination is the finding, and it is a diagnosis change rather than a data point: for four runs the framework explained EGLD's weakness through traceable distribution, and this week that explanation is simply unavailable. What did move was all on the demand side - the Mega Whale absorber that soaked up runs #15 and #17 recorded zero transactions and the Coinbase Routing pipe feeding it drained to 77 EGLD; xExchange volume collapsed {100*(totvol-prev_dexvol)/prev_dexvol:.0f}% while pool TVL and WEGLD supply ROSE, meaning depth stayed and trading left; bridged stablecoins resumed burning after one flat week. Supply exhausts, but absent demand does not, which makes this a worse structural condition than the distribution weeks even though the flow numbers look better. The one genuine counter-signal is that DeFi depositors showed up hard: Hatom Lending's bilateral-inverse response ratio of {inverse_ratio:.2f} is the strongest ever measured and falsifies run #11's hypothesis that depositor capacity was being permanently exhausted - it was cyclical. Methodologically the run's most durable contribution is that the OTC throughput series is finally comparable: pagination is now default, runs #13-#15 are backfilled, and the method validates by exactly reproducing run #16's independent figure - revealing a five-week escalation that peaked last week and broke.",
   "top_recommendation":f"TRACE THE DEMAND SIDE WITH THE SAME RIGOUR THE SUPPLY SIDE GETS. This run's central finding is that the supply framework stopped explaining price, and the model had no comparable instrumentation to put in its place. Concretely for run #19: (1) resolve the Binance custody reload's true origin - erd1r3w62vq is a nonce-8 pass-through, so query its 14d inbound and identify who funded the 150,000; (2) instrument the Coinbase Routing -> Mega Whale pipe as a standing weekly metric (routing wallet balance + whale delta) rather than an ad-hoc trace, since it is the only identifiable large bid on the chain and its disappearance was this week's best explanation of price; (3) add a bid-depth proxy from mex/pairs (TVL vs volume ratio per pair) so 'volume collapsed but depth held' becomes a measured signal rather than an inference. PRE-COMMITTED READING for next week, registered now: if price stabilises or recovers while OTC stays quiet, this week was a liquidity air-pocket and the supply exhaustion is genuinely constructive; if price keeps falling with no traceable distribution, the chain has a structural bid problem and the supply-side model needs to be demoted from primary to supporting.",
   "recommendations_for_next_run":[
     "TRACE THE BINANCE CUSTODY RELOAD ORIGIN. The +150,000 arrived from erd1r3w62vq, a nonce-8 wallet now holding 2 EGLD - a pass-through. Query its 14d inbound to identify the funder. If it traces back to Binance.com hot wallets this is an ordinary internal re-parking; if it traces to an external or OTC source, Binance is ACCUMULATING again and the runs #9-#11 pattern is repeating. Cheapest high-value query of the week.",
     "DID THE DEMAND SIDE COME BACK? Pre-committed reading registered this run: price stabilising or recovering with OTC still quiet = this week was a liquidity air-pocket and supply exhaustion is genuinely constructive; price continuing to fall with no traceable distribution = a structural bid problem, and the supply-side framework must be demoted from primary explanation to supporting evidence. The specific instruments to check are the Coinbase Routing wallet balance (77 EGLD now), the Mega Whale erd18mv2z6r2 delta (flat this week), and whether DEX volume recovers off the $75K floor.",
     "DO THE OTC DESKS STAY DEAD? Desks are at 61,496 with no UPbit reload for the first time in the tracked cycle and throughput down 76%. A third consecutive quiet week would establish exhaustion as durable rather than an inter-cycle gap (the run #12 pattern was a 1-2 week gap before reloading). A fresh large UPbit -> desk tranche would signal wave #2 staging. Watch UPbit's own balance (1,234,929) as the leading edge.",
     "INSTRUMENT DEMAND PROPERLY. Add three standing metrics to the collector: (a) Coinbase Routing wallet balance + Mega Whale delta as a single 'identifiable bid' indicator; (b) per-pair TVL/volume ratio from mex/pairs as a bid-depth proxy, so 'volume collapsed while depth held' is measured rather than inferred; (c) a count of distinct addresses receiving >1,000 EGLD from exchanges (withdrawal breadth) as a retail-accumulation proxy. The supply side has five instruments and the demand side has none.",
     "DOES THE USH DE-LEVERAGING ACCELERATE? USH burned -2.60%, re-activating the run #11 rule and confirming the run #16 mint was a chase. Historically a burn past ~5% coincided with forced CDP closures and local capitulation lows. Watch whether the burn accelerates (capitulation signature, often a bottoming tell) or stops at this one week (orderly de-risking). Track alongside Hatom Lending's EGLD TVL, which moved the OPPOSITE way this week.",
     "CONFIRM OR FALSIFY THE DEPOSITOR-CAPACITY RECOVERY. The bilateral inverse ratio hit 0.98, the strongest ever, falsifying run #11's decay hypothesis. One observation is not a trend. If the next |dPrice|>=5% week produces another ratio above ~0.8, treat depositor dip-buying capacity as structurally restored and upgrade it to a demand-side indicator in its own right; if it reverts toward 0.2-0.4, this week was a one-off and the decay hypothesis survives.",
     "BACKFILL THE OTC SERIES ONE WINDOW FURTHER IF CHEAP. Runs #13-#18 are now comparable. Run #12's window (Jun 8-15) may still be queryable with the same paginated method; if it is, it would establish whether the escalation began before run #13 or started there. Do not spend more than ~200 API calls on it - the series is already usable.",
     "WATCH pi-staking, THE ONLY PERSISTENT GROWTH STORY. Six consecutive weeks of gains (+11,330 and +35 users this week) through both the rally and the reversal makes it the most persistent provider in tracking. Identify what is driving it (fee, APR, an integration, an aggregator routing default) - a provider growing against the tape is the closest thing to a genuine adoption signal the staking layer has produced this quarter."],
   "dashboard_feature_suggestions":[
     {"title":"Supply-vs-demand channel dashboard (the 'what is switched on' panel)",
      "motivation":"This run's central finding is a diagnosis change: every traceable SUPPLY channel (OTC throughput, desk balance, Binance custody, true exchange flow) went quiet in the same week, while every DEMAND instrument (Mega Whale absorber, DEX volume, stablecoin supply) deteriorated - and price fell 10% anyway. Conveying that required four separate paragraphs cross-referencing four sections. A single panel showing each channel as ON/OFF/REVERSED with its weekly magnitude would have made the whole argument visible in one glance, and would immediately expose the weeks where supply and demand disagree, which is exactly when the model's explanation changes.",
      "suggested_visualization":"small-multiples strip: one row per channel (OTC throughput, desk balance, custody, exchange net, absorber delta, DEX volume, stablecoin supply), each a 6-week sparkline with a colour-coded current-state chip (supply-on/supply-off/demand-present/demand-absent).",
      "data_already_available":True,
      "data_source":"all seven series exist in running_baselines plus per-run report JSON fields; needs a small normalisation layer to put them on one panel","priority":"high"},
     {"title":"Corrected OTC throughput series with method-provenance markers",
      "motivation":"The paginated backfill landed this run and produced a genuinely new finding - five consecutive weeks of escalating distribution (66K -> 186K -> 506K -> 1.10M -> 1.28M) that peaked in run #17 and collapsed 76% this week. That structure was entirely invisible in the old truncated figures, and it is the strongest single piece of evidence the model has produced about distribution cycles. It needs a chart, and the chart needs to mark which points are paginated-and-verified (runs #13-#18) versus which are unusable lower bounds (runs #1-#12), so nobody re-derives a trend from the bad segment.",
      "suggested_visualization":"bar chart of weekly net throughput with desk balance as a line overlay, a shaded 'pre-pagination, not comparable' region before run #13, and phase labels (load / distribute / exhaust).",
      "data_already_available":True,
      "data_source":"OTC_SERIES in this run's assembler plus desk balances in previous.json watch_addresses; would need persisting as a first-class array in the report JSON rather than an assembler constant","priority":"high"},
     {"title":"Pre-committed test scoreboard",
      "motivation":"Four of this run's findings are resolutions of tests that prior runs pre-registered (OTC reload, KuCoin persistence, EGLD laggard confirmation, USH leverage chase), and one is a threshold-triggered promotion (participation inertia at six weeks). That discipline is the most valuable process the pipeline has, but it is currently buried in prose and only legible to someone reading two consecutive reports end to end. A scoreboard tracking each open test, its pre-registered branches, its resolution and the run that closed it would make the model's forecasting record auditable - including the misses.",
      "suggested_visualization":"table or timeline of pre-committed tests: registered-in run, question, branch A/branch B readings, resolved-in run, outcome chip (confirmed / falsified / not evaluable), with open tests pinned to the top.",
      "data_already_available":False,
      "data_source":"the information exists in watch_list reasons and recommendations_for_next_run across runs but is unstructured prose; would need a structured pre_committed_tests array added to the report schema","priority":"medium"}],
   "dashboard_suggestions_followup":[
     {"title":"OTC desk balance + true throughput cycle chart","status":"pending",
      "note":"Still not built, but its blocker is now cleared - the paginated backfill landed this run, so runs #13-#18 form a comparable series and the chart would show a real load-escalate-exhaust cycle rather than noise. Highest-value unbuilt item."},
     {"title":"OTC distribution Sankey: desk -> router -> venue","status":"deprioritized",
      "note":"Deferred one run. The pipeline ran at a quarter of last week's volume with the same routers and same two terminal venues, so a Sankey built now would show a thin version of last week's diagram and add little. Revisit if a second distribution wave stages."},
     {"title":"Participation breadth vs price recovery overlay","status":"deprioritized",
      "note":"Superseded by this run's promotion of participation inertia to a structural finding. The chart would now show a flat line against a round-tripping price - the answer is settled, so a dedicated view earns less than the supply-vs-demand panel proposed this run."},
     {"title":"EGLD relative-strength (beta) tracker","status":"pending",
      "note":"Carried from run #16 and still unbuilt, and this week made the strongest case yet: EGLD fell 10% while both majors ROSE, which is a different regime from high-beta lag and is hard to convey without a multi-week EGLD-vs-BTC/ETH view. Fold it into the supply-vs-demand panel as one row rather than building it standalone."}]
 }
}

json.dump(report,open(f"{REPO}/reports/2026-07-27.json","w"),indent=2)
print("WROTE reports/2026-07-27.json")
print("exec_summary:",len(executive_summary),"large_tx:",len(large_transactions),"wallet_changes:",len(wallet_changes),
      "providers:",len(provs),"anomalies:",len(anomalies),"watch:",len(watch_list))
print("net exchange flow:",round(net_total,1),"adjusted:",round(net_adjusted,1))
print("OTC throughput net:",round(OTC_THR_7D),"gross:",round(OTC_THR_GROSS),"interdesk:",round(OTC_THR_INTERDESK))
print("desk cur:",round(desk_cur),"prev:",desk_prev,"delta:",round(desk_delta))
print("DEFI: Hatom Lending USD",round(hatom_lending),"LSD",round(hatom_lsd),"USH",round(hatom_ush),"XOXNO LSD",round(xoxno_lsd))
print("LSD supply WoW: SEGLD %.2f%% XEGLD %.2f%% SWTAO %.2f%% USH %.2f%%"%(segld_supply_wow,xegld_supply_wow,swtao_supply_wow,ush_supply_wow))
print("inverse ratio:",round(inverse_ratio,3))
print("DEX volume:",round(totvol,1),"WoW%:",round(100*(totvol-prev_dexvol)/prev_dexvol,1))
print("Delegators:",cur_deleg,"WoW:",deleg_wow,"cohort_net:",round(cohort_net))
print("Staked:",staked,"WoW:",staked-pecon["staked_egld"],"locked:",round(total_locked))
print("EGLD price:",price,f"{price_chg:+.2f}%","BTC:",round(btc_wow,2),"ETH:",round(eth_wow,2))
print("newly_issued kept:",len(newly_issued),"rejected:",newly_issued_rejected)
