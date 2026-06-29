#!/usr/bin/env python3
"""Assemble reports/2026-06-29.json (run #14) from collected data."""
import json, math
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D = json.load(open("/tmp/run14/collected.json"))
prev = json.load(open(f"{REPO}/data/previous.json"))
kn = json.load(open(f"{REPO}/data/known-addresses.json"))
learn = json.load(open(f"{REPO}/data/learnings.json"))
prevcol = json.load(open(f"{REPO}/data/collected/2026-06-22.json"))  # for supply WoW

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
btc_wow=100*(be["bitcoin"]["usd"]-pecon.get("btc_price_usd",be["bitcoin"]["usd"]))/pecon.get("btc_price_usd",be["bitcoin"]["usd"]) if pecon.get("btc_price_usd") else None
eth_wow=100*(be["ethereum"]["usd"]-pecon.get("eth_price_usd",be["ethereum"]["usd"]))/pecon.get("eth_price_usd",be["ethereum"]["usd"]) if pecon.get("eth_price_usd") else None
acc=D["accounts"]
def bal_of(a):
    x=acc.get(a)
    if x and isinstance(x.get("info"),dict) and "balance" in x["info"]:
        try: return int(x["info"]["balance"])/1e18
        except: return None
    return None

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
for a,info in acc.items():
    txs=info.get("txs")
    if not isinstance(txs,list): continue
    for t in txs:
        if not isinstance(t,dict): continue
        h=t.get("txHash")
        if not h or h in seen: continue
        try: v=int(t.get("value","0"))/1e18
        except: v=0
        if v<1000: continue
        seen.add(h)
        s=t.get("sender"); r=t.get("receiver"); ts=t.get("timestamp")
        bigtx.append({"hash":h,"timestamp":datetime.fromtimestamp(ts,tz=timezone.utc).isoformat() if ts else None,
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
BAD_ADDR = "erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp29trp6qsl2gdvvz2eqra76xc"
by_exchange=[]; ent_cur={}; ent_w={}
for a in exch:
    if a == BAD_ADDR: continue
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
    if a == BAD_ADDR: continue
    e=entity_of(a)
    if not e: continue
    if a in prev_ta_map:
        prev_ent[e]=prev_ent.get(e,0)+prev_ta_map[a]
for k,v in prev["exchange_balances"].items():
    e = "Binance" if "Binance" in k else ("Coinbase" if "Coinbase" in k else k)
    if e not in prev_ent:
        prev_ent[e] = v

ent_interp={
 "Binance":"Net -158K - the single largest exchange move this week and the dominant driver of the aggregate net OUTFLOW. Binance hot wallets fell from 683K to 525K (erd1sdsl 58K + erd1ylwus 167K + erd1v4ms 300K); Binance Staking custody UNCHANGED at 3,512,650 for the 4th CONSECUTIVE WEEK. The -158K is NOT visible in standard /transactions (large exchanges move via internal transfers / SC mechanisms), so the destination cannot be traced directly. Context is ambiguous during a -10.5% market-wide dump: a large hot-wallet drawdown can be withdrawals to self-custody (accumulation) OR routing to the OTC pipeline for distribution. Given the OTC desks loaded +35K and ran 195K of throughput this week, a meaningful share is likely OTC-bound; the rest is unattributed.",
 "Coinbase":"-1.6K - the 3-CONSECUTIVE-week inflow streak (+43K/+8.3K/+6.0K) BROKE this week to a mild net outflow. Primary +4.0K, secondary -5.8K. The 'structural distribution via Coinbase' read from run #13 is paused; one outflow week is not yet a reversal, but it ends the streak that the bearish-distribution thesis leaned on.",
 "Crypto.com":"+1.7K (+0.9%). Mild inflow.",
 "Bybit":"-56K (-11.0%) on the cold wallet - the 2nd-largest exchange move and a sharp reversal of last week's +10.9K inflow. Large outflow during the dump.",
 "UPbit":"Cold wallet -13K (-1.0%) - mild outflow. Separately, the UPbit OTC Desk +18K and OTC Distribution +17K (combined desk balance +35K) - the OTC pipeline is in a HEAVY loading phase even as it simultaneously ran 195K of distribution throughput (see OTC section).",
 "MEXC":"-3.6K (-3.8%). Mild outflow.",
 "KuCoin":"+1.1K (+4.1%). Small inflow, reversing last week's outflow.",
 "Bitget":"+3.5K (+4.0%). Mild inflow.",
 "Gate.io":"-1.6K (-2.8%). Mild outflow.",
 "Tokero":"Flat (+0.1K).",
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

exchange_flows={"total_exchange_egld_current":total_cur,"total_exchange_egld_previous":total_prev,
    "net_change_egld":net_total,"net_change_pct":100*net_total/total_prev if total_prev else None,
    "direction":"outflow" if net_total<0 else "inflow",
    "signal":f"Net exchange flow {net_total:+,.0f} EGLD ({100*net_total/total_prev if total_prev else 0:+.2f}%) - a sharp REVERSAL to net OUTFLOW after 3 consecutive inflow weeks. Binance hot -158K and Bybit -56K dominate; Coinbase's 3-week inflow streak also broke (-1.6K). This breaks the 'structural distribution via exchange inflows' read that ran through runs #11-13. IMPORTANT CAVEAT: this is a broad market-dump week (BTC -6.4%, ETH -9.5% WoW), and a large net exchange outflow during a sell-off is ambiguous - it can be capitulation withdrawals to self-custody (latent accumulation) rather than a bullish demand signal. The bearish counter-evidence is that the OTC pipeline simultaneously ran 195K of distribution throughput (up from 85K) and loaded another +35K into the desks, so a chunk of the exchange outflow is OTC-distribution plumbing, not clean off-exchange accumulation. Net read: the inflow streak ended, but the outflow is not cleanly bullish given the heavy OTC distribution running underneath it. Binance Staking custody remains frozen at 3.51M for the 4th week.",
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
    pl=prevp.get(nm)
    top_providers.append({"rank":i,"identity":nm,"name":nm,"provider_address":p["provider"],
        "locked_egld":p["_lk"],"previous_locked_egld":pl,"share_pct":p["_lk"]/total_locked*100,
        "apr_pct":aprp(p),"fee_pct":feep(p)*100,"num_users":p.get("numUsers"),"num_nodes":p.get("numNodes"),
        "wow_change_egld":(p["_lk"]-pl) if pl is not None else None})
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

# yield-chase cohort net flow
def lk_wow(nm):
    p=next((x for x in provs if (x.get("identity") or x.get("provider"))==nm),None)
    if not p or nm not in prevp: return None
    return p["_lk"]-prevp[nm]
cohort_names=["ninjastaking","egldstakingprovider","procryptostaking","valuestaking","orius","star_staking"]
cohort_flows={nm:lk_wow(nm) for nm in cohort_names if lk_wow(nm) is not None}
cohort_net=sum(v for v in cohort_flows.values())

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
    h=holders_map.get(tid)
    ph=prev_th.get(tid,{}).get("holders")
    top_by_market_cap.append({"identifier":tid,"name":t.get("name"),"holders":h,"previous_holders":ph,
        "price_usd":t.get("price"),"market_cap_usd":t.get("marketCap"),"volume_24h_usd":None})
newly_issued=[]
for ni in D.get("newly_issued", []):
    newly_issued.append({"identifier":ni["identifier"],"name":ni["name"],"ticker":ni["ticker"],
        "holders":ni["accounts"],"transactions":ni["transactions"],"timestamp":ni["timestamp"],
        "deployer":ni["deployer"],"deployer_label":lab(ni["deployer"]),
        "issued_at":datetime.fromtimestamp(ni["timestamp"],tz=timezone.utc).isoformat()})

# xExchange
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

# ---------- defi - LSD mcaps + supply-based WoW ----------
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
# SWTAO null-price fallback (run #13/#14 quirk): the dataApi feed returned null even after
# 4x isolated 2.5s re-fetch this run, and WTAO price is also null so the accumulator-ratio
# fallback is unavailable. Carry the prior-week SWTAO price applied to current supply. Supply
# is the PRIMARY signal (price-independent, never null) and is flat (+0.27% WoW), so this
# estimate only affects the secondary USD figure. Flagged in data_sources_failed + methodology.
swtao_price_est=None
if swtao_mcap==0:
    prev_sw=prevcol.get("tvl_tokens",{}).get("SWTAO-356a25",{})
    sw_cur_supply=supply("SWTAO-356a25")
    prev_sw_price=prev_sw.get("price") if isinstance(prev_sw,dict) else None
    if prev_sw_price and sw_cur_supply:
        swtao_price_est=prev_sw_price
        swtao_mcap=prev_sw_price*sw_cur_supply
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
ppx=pp
prev_hl_egld=prev["defi_tvl"]["Hatom Lending"]/ppx
prev_xl_egld=prev["defi_tvl"]["XOXNO LSD"]/ppx
prev_hush=prev["defi_tvl"]["Hatom USH"]
prev_xexch_egld=prev["defi_tvl"]["xExchange (USD)"]/ppx
prev_hlsd=prev["defi_tvl"]["Hatom Liquid Staking"]
prev_hlsd_egld=prev_hlsd/ppx
hl_egld=hatom_lending/price
hlsd_egld=hatom_lsd/price
xlsd_egld=xoxno_lsd/price
ush_egld=hatom_ush/price
weglds=D["tokens_holders"]
wegld_tok=next((t for t in weglds if t["identifier"]=="WEGLD-bd4d79"), None)
wegld_supply_now = int(wegld_tok.get("supply","0")) if wegld_tok else 0
wegld_supply_prev = int(prev_th.get("WEGLD-bd4d79",{}).get("supply_raw",0) or 0)
wegld_chg_pct = 100*(wegld_supply_now-wegld_supply_prev)/max(wegld_supply_prev,1) if wegld_supply_prev else 0

# stablecoin supply WoW (both 6 decimals). cur `supply` is decimals-adjusted; prev stored
# supply_raw (raw integer) -> divide by 1e6 to compare like-for-like.
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
  "notable_events":f"DEX volume ${totvol/1000:.0f}K (+{100*(totvol-prev_dexvol)/prev_dexvol:.0f}% WoW) - a recovery off the floor but still depressed vs the $100K+ of a month ago. WEGLD/USDC dominance {pairs[0]['share_pct']:.1f}% (the highest in recent runs); ZoidPay/WEGLD share {pairs[1]['share_pct'] if len(pairs)>1 else 0:.1f}%. WEGLD supply WoW {wegld_chg_pct:+.2f}% (flat). Volume rose on sell-side turnover during the dump.","health_signal":"flat"},
 {"protocol":"Hatom Lending","category":"lending","addresses_tracked":13,"tvl_usd":hatom_lending,"tvl_egld":hl_egld,
  "tvl_wow_change_pct":100*(hl_egld-prev_hl_egld)/prev_hl_egld,"transfers_24h":tcount("Hatom EGLD MM"),
  "notable_events":f"TVL ${hatom_lending/1e6:.2f}M USD ({100*(hatom_lending-prev['defi_tvl']['Hatom Lending'])/prev['defi_tvl']['Hatom Lending']:+.1f}%), {hl_egld/1000:.0f}K EGLD ({100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}% EGLD). Bilateral inverse rule NOW EVALUABLE (price -10.5% exceeds the |Δprice|>=5% threshold): EGLD-denominated TVL moved {100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}% (counter to price, depositors hold/DCA during dips). Response ratio {abs(100*(hl_egld-prev_hl_egld)/prev_hl_egld)/abs(100*(price-pp)/pp):.2f} - low, continuing the depositor-capacity-exhaustion series.","health_signal":"flat"},
 {"protocol":"Hatom Liquid Staking","category":"liquid_staking","addresses_tracked":2,"tvl_usd":hatom_lsd,"tvl_egld":hlsd_egld,
  "tvl_wow_change_pct":100*(hlsd_egld-prev_hlsd_egld)/prev_hlsd_egld,"transfers_24h":tcount("Hatom Liquid Staking"),
  "notable_events":f"SEGLD ${segld_mcap/1e6:.2f}M + SWTAO ${swtao_mcap/1e6:.2f}M (est.) = ${hatom_lsd/1e6:.2f}M USD ({100*(hatom_lsd-prev_hlsd)/prev_hlsd:+.1f}%). On a supply basis Hatom LSD is FLAT: SEGLD {segld_supply_wow:+.2f}% (mild redemption), SWTAO {swtao_supply_wow:+.2f}% (flat). SWTAO USD is a carried-prior-price estimate (dataApi feed null all run); supply is the reliable signal.","health_signal":"flat"},
 {"protocol":"Hatom USH","category":"stablecoin","addresses_tracked":4,"tvl_usd":hatom_ush,"tvl_egld":ush_egld,
  "tvl_wow_change_pct":100*(hatom_ush-prev_hush)/prev_hush,"transfers_24h":None,
  "notable_events":f"USH mcap ${hatom_ush/1000:.0f}K ({100*(hatom_ush-prev_hush)/prev_hush:+.1f}% USD). USH supply {ush_supply_wow:+.2f}% WoW - burn/de-leveraging RESUMED after last week's pause. Borrowers re-closing CDP positions during the dump to avoid liquidation = on-chain leverage unwinding.","health_signal":"shrinking"},
 {"protocol":"XOXNO LSD","category":"liquid_staking","addresses_tracked":2,"tvl_usd":xoxno_lsd,"tvl_egld":xlsd_egld,
  "tvl_wow_change_pct":100*(xlsd_egld-prev_xl_egld)/prev_xl_egld,"transfers_24h":tcount("XOXNO LSD"),
  "notable_events":f"XEGLD ${xoxno_lsd/1e6:.2f}M ({100*(xoxno_lsd-prev['defi_tvl']['XOXNO LSD'])/prev['defi_tvl']['XOXNO LSD']:+.1f}% USD), but the real signal is SUPPLY: XEGLD supply COLLAPSED {xegld_supply_wow:+.1f}% WoW (321,592 -> 227,765, ~94K redeemed). The largest single-protocol LSD supply move in tracking. XOXNO-specific (SEGLD flat), likely a few large redeemers. Trace next run: migration to native delegation/another LSD, or outright exit?","health_signal":"draining"},
 {"protocol":"XOXNO Aggregator","category":"aggregator","addresses_tracked":1,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("XOXNO Aggregator"),
  "notable_events":f"Throughput {tcount('XOXNO Aggregator'):,} daily transfers (~16-17K; on-chain routing activity steady).","health_signal":"flat"},
 {"protocol":"OneDex","category":"aggregator","addresses_tracked":5,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("OneDex Swap"),
  "notable_events":f"{tcount('OneDex Swap'):,} daily transfers via swap contract.","health_signal":"flat"},
 {"protocol":"JEXchange","category":"dex","addresses_tracked":4,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("JEXchange Fees"),
  "notable_events":f"Fees wallet {tcount('JEXchange Fees'):,} daily transfers.","health_signal":"flat"}]
protocols=[
 {"name":"xExchange","category":"dex","volume_24h_usd":totvol,"active_pairs":25,"transfers_24h":None,"tvl_usd":xexch_tvl_usd,"tvl_egld":xexch_tvl_egld,"tvl_wow_change_pct":100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld},
 {"name":"Hatom Lending","category":"lending","volume_24h_usd":None,"active_pairs":None,"transfers_24h":tcount("Hatom EGLD MM"),"tvl_usd":hatom_lending,"tvl_egld":hl_egld,"tvl_wow_change_pct":100*(hl_egld-prev_hl_egld)/prev_hl_egld},
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
zsr=zc(rb["staked_ratio"],sr)
zd=zc(rb["total_delegators"],cur_deleg)
zse=zc(rb["staked_egld"],staked)
zv=zc(rb["dex_volume_24h_usd"],totvol)
deleg_wow=cur_deleg-prev_deleg
anomalies=[
 {"metric":"egld_price_usd","current_value":price,"previous_value":pp,"method":"z_score",
  "average_value":zp[0],"stddev":zp[1],"z_score":zp[2],"severity":"medium",
  "description":f"EGLD {100*(price-pp)/pp:+.2f}% WoW to ${price:.2f}, z={zp[2]:+.2f}σ (N={len(rb['egld_price_usd'])}). The $2.85 floor did NOT hold - price broke to a new local low of ${price:.2f}, extending the downtrend. The raw -10.5% is the 2nd-largest weekly drop in tracking, but the z-score is only {zp[2]:+.2f}σ because the multi-week decline has widened the baseline stddev (the model has partially absorbed the downtrend) - hence MEDIUM, not high. UNLIKE recent weeks, this was a BROAD-MARKET dump, not EGLD-specific decoupling: WoW BTC {btc_wow:+.2f}%, ETH {eth_wow:+.2f}%, EGLD {100*(price-pp)/pp:+.2f}%. EGLD still underperformed (high-beta) but moved WITH the market (24h: BTC -0.24%, ETH +0.37% = market stabilizing at the lows). 7-week trajectory from the May peak now ~-45%."},
 {"metric":"mex_price_usd","current_value":meco["price"],"previous_value":prev_mexp,"method":"z_score",
  "average_value":zmex[0],"stddev":zmex[1],"z_score":zmex[2],"severity":"low",
  "description":f"MEX price {100*(meco['price']-prev_mexp)/prev_mexp:+.2f}% to ${meco['price']:.3e} (z={zmex[2]:+.2f}σ, N={len(rb['mex_price_usd'])}). MEX tracked EGLD down through the dump, underperforming it slightly. MEX mcap ${meco['marketCap']/1e6:.2f}M. DEX volume rose +{100*(totvol-prev_dexvol)/prev_dexvol:.0f}% to ${totvol/1000:.0f}K but remains depressed vs the $100K+ of a month ago."},
 {"metric":"total_delegators","current_value":cur_deleg,"previous_value":prev_deleg,"method":"z_score",
  "average_value":zd[0],"stddev":zd[1],"z_score":zd[2],"severity":"low",
  "description":f"Total delegators {cur_deleg:,} ({deleg_wow:+,} WoW = {100*deleg_wow/prev_deleg:+.3f}%). The raw z-score is z={zd[2]:+.2f}σ, but this is the run #9 DEGENERATE-Z-SCORE case: the baseline mean is dragged up by the pre-capitulation ~179K level, so the post-capitulation level reads as a large negative z even though the actual WoW move is essentially ZERO ({deleg_wow:+,}). DOWNGRADED to LOW. Decisive read: the delegator base has now been FLAT for a 2nd consecutive week at ~174.4K, CONFIRMING that run #12's -4,003 capitulation was a one-shot shake-out, not the start of sustained outflow. Resolves the carried highest-information question - the base has stabilized."},
 {"metric":"staked_egld","current_value":staked,"previous_value":pecon["staked_egld"],"method":"z_score",
  "average_value":zse[0],"stddev":zse[1],"z_score":zse[2],"severity":"low",
  "description":f"Total staked {staked:,} EGLD ({staked-pecon['staked_egld']:+,} WoW, {100*(staked-pecon['staked_egld'])/pecon['staked_egld']:+.2f}%). z={zse[2]:+.2f}σ. Staked ROSE +81K this week - a reversal of the prior multi-week unstaking drift, even as price dumped -10.5%. This is buy-the-dip staking: delegation TVL +32K and a sharp reignition of the 0%-fee yield-chase cohort (ninjastaking +11.6K, star_staking +7.7K, pi-staking +7.1K). Staked ratio {sr*100:.2f}% ({100*(sr-pecon['staked_ratio']):+.2f}pp). A mild bullish-conviction signal: some holders locked EGLD into yield during the sell-off rather than selling it."},
 {"metric":"xegld_supply_collapse","current_value":227765,"previous_value":321592,"method":"rule_based",
  "severity":"high",
  "description":f"XOXNO LSD (XEGLD) circulating supply COLLAPSED {xegld_supply_wow:+.1f}% WoW - from 321,592 to 227,765 XEGLD, a redemption of ~94K XEGLD (~$300K+) in a single week. This is the largest single-protocol LSD supply move in tracking history and the standout DeFi event this run. It is XOXNO-SPECIFIC, not a synchronized LSD event: SEGLD supply was only {segld_supply_wow:+.2f}% and SWTAO flat. On a supply basis (the run #13 methodology) this is unambiguous and large - a major unstake/redemption from XOXNO's liquid-staking product, likely one or a few large redeemers given the size and the single-week timing. Whether it reflects a migration (to native delegation / another LSD) or an outright exit needs tracing next run; either way it removes a meaningful chunk of XOXNO LSD TVL."},
 {"metric":"binance_staking_custody_stalled_4th_week","current_value":3512650,"previous_value":3512650,"method":"rule_based",
  "severity":"high",
  "description":"Binance Staking custody UNCHANGED at 3,512,650 EGLD for the 4th CONSECUTIVE WEEK. The 3-week accumulation phase (runs #7+9+10, +402K) is now followed by a 4-week stall = 7 weeks of an undeployed 779K-EGLD position ($1.99M at the current $2.55). No delegation to the protocol staked module; no drawdown to hot wallets. Entrenched structural position - notably, the +81K staked rise this week came from OTHER wallets (yield-chase delegation), NOT from this custody balance. Each additional frozen week raises the stakes of the eventual move."},
 {"metric":"otc_distribution_wave_active","current_value":195447,"previous_value":85328,"method":"rule_based",
  "severity":"high",
  "description":"OTC pipeline ran a MAJOR distribution wave this week: combined UPbit OTC + OTC Distribution 7d outbound throughput 195,447 EGLD (up from 85K last week, the highest in tracking) - the distribution wave predicted by run #13's reload arrived on schedule (week 1 of the 1-3 week window). SIMULTANEOUSLY the desk balances rose +35K (UPbit OTC +18K to 53,619; OTC Distribution +17K to 52,962), i.e. the desks are running heavy two-way flow - distributing 195K while reloading. OTC source erd17l22 +16K to 317K is actively feeding the chain. Combined with Binance's -158K hot-wallet drawdown, this is a large retail-distribution operation running underneath the price dump - the dominant bearish on-chain signal this week."},
 {"metric":"mega_whale_erd18mv2z6r2_activated","current_value":1010011,"previous_value":998971,"method":"rule_based",
  "severity":"medium",
  "description":"Unknown Mega Whale erd18mv2z6r2 ACTIVATED after 3 weeks dormant: received +11,040 EGLD from erd1lgdltequh76 and crossed back above the 1M threshold to 1,010,011 (998,971 -> 1,010,011). This is the OTC-counterparty wallet from the Apr-18 bilateral deal (it received 798K then). The inbound is modest and it has not forwarded the funds onward, but a previously-dormant mega-OTC counterparty turning active during a distribution wave is worth flagging."},
 {"metric":"stablecoin_supply_contraction_2nd_week","current_value":usdt_supply_wow,"previous_value":-1.75,"method":"rule_based",
  "severity":"low",
  "description":f"Bridged stablecoin supply contracted for a 2nd CONSECUTIVE week, ACCELERATING: USDC {usdc_supply_wow:+.2f}% and USDT {usdt_supply_wow:+.2f}% WoW (vs -0.47% / -1.75% last week), both well above the 0.1% stablecoin threshold. Stablecoin burn = redemptions / bridge-out = dollar liquidity leaving the MultiversX ecosystem, accelerating during the dump. Confirms the carried 'sustained dollar-liquidity flight' watch - a directionally-bearish capital-flight signal, now a 2-week trend. USH (Hatom CDP stablecoin) also resumed burning ({ush_supply_wow:+.2f}%), i.e. on-chain leverage being unwound too."}]

# ---------- trend indicators ----------
accelerating_outflows=[
 {"exchange":"NET_EXCHANGE","trend":"outflow","cumulative_change_pct":None,"weeks_in_trend":1,
  "interpretation":f"Aggregate net exchange flow {net_total:+,.0f} EGLD OUTFLOW - REVERSING the 3-week inflow streak (+25K/+42K/+12K). Binance hot -158K and Bybit -56K dominate. During a -10.5% market-wide dump, a net exchange outflow is ambiguous (capitulation withdrawals to self-custody vs OTC routing), but the simultaneous 195K OTC distribution throughput means much of it is distribution plumbing, not clean off-exchange accumulation."},
 {"exchange":"Binance hot","trend":"outflow","cumulative_change_pct":None,"weeks_in_trend":1,
  "interpretation":"Binance hot wallets -158K (683K -> 525K), the single largest exchange move this week. Not traceable via standard /transactions (internal transfers). Likely split between self-custody withdrawals and the OTC pipeline given the +35K desk load and 195K throughput."},
 {"exchange":"UPbit OTC Desks","trend":"distributing+loading","cumulative_change_pct":None,"weeks_in_trend":2,
  "interpretation":"OTC desks ran a MAJOR distribution wave (195K throughput, up from 85K - highest in tracking) WHILE simultaneously loading +35K into desk balances (UPbit OTC +18K, OTC Distribution +17K). The run #13-predicted distribution wave arrived in week 1 of the 1-3 week window; the heavy reload signals more distribution to follow."}]

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
   {"metric":"egld_price","direction":"down","weeks":2,"cumulative_change_pct":100*(price-2.99)/2.99,
    "interpretation":f"2nd consecutive down-week after the failed bounce: $2.99 -> $2.85 -> ${price:.2f}. The downtrend has resumed and the $2.85 'floor' did not hold. This week's leg was a broad-market beta move (BTC -6.4%, ETH -9.5% WoW), unlike the prior EGLD-specific decoupling. 7-week drawdown from the May peak ~-45%."},
   {"metric":"delegator_base_flat","direction":"flat","weeks":2,"cumulative_change_pct":0,
    "interpretation":f"2nd consecutive flat week for the delegator base at ~174.4K ({deleg_wow:+,} this week). CONFIRMS the run #12 -4,003 capitulation was a one-shot shake-out. The retail-delegation exit has stopped; the base has stabilized."},
   {"metric":"binance_staking_custody_stalled","direction":"flat","weeks":4,"cumulative_change_pct":0,
    "interpretation":"4th consecutive week of stall at 3,512,650 EGLD. 3-week accumulation + 4-week stall = 7 weeks, 779K parked. Entrenched structural position; the eventual delegate-vs-distribute move becomes more decisive each frozen week."},
   {"metric":"stablecoin_supply_burn","direction":"down","weeks":2,"cumulative_change_pct":None,
    "interpretation":f"2nd consecutive week of bridged-stablecoin burn, accelerating: USDC {usdc_supply_wow:+.2f}% / USDT {usdt_supply_wow:+.2f}% (vs -0.5%/-1.8% last week). Dollar liquidity bridging out of the ecosystem during the dump - sustained capital flight."},
   {"metric":"token_holder_count_decline","direction":"down","weeks":14,"cumulative_change_pct":None,
    "interpretation":"14th consecutive week of small holder declines across top-10 tokens. Established airdrop-decay baseline; the active >$1M-mcap token base is stable."}],
 "regime_shifts":[
   {"metric":"xoxno_lsd_supply_collapse","before_value":321592,"after_value":227765,
    "description":f"XOXNO LSD (XEGLD) supply collapsed {xegld_supply_wow:+.1f}% in one week (321,592 -> 227,765 XEGLD, ~94K redeemed). The largest single-protocol LSD supply move in tracking. XOXNO-specific (SEGLD flat), likely a few large redeemers. A step-change in XOXNO LSD TVL that needs tracing next run (migration vs exit)."},
   {"metric":"exchange_inflow_streak_broke","before_value":12194,"after_value":net_total,
    "description":f"The 3-week net-exchange-INFLOW regime broke to a {net_total:+,.0f} OUTFLOW. The 'structural distribution via exchange deposits' read (runs #11-13) is paused. But the outflow is not cleanly bullish: it coincides with a record 195K OTC distribution throughput, so distribution shifted channel (exchange deposits -> OTC pipeline) rather than stopping."},
   {"metric":"buy_the_dip_staking","before_value":-9166,"after_value":staked-pecon["staked_egld"],
    "description":f"Protocol staked reversed from multi-week unstaking to +81K this week despite the -10.5% dump - buy-the-dip staking. The 0%-fee yield-chase cohort reignited (ninjastaking +11.6K, star_staking +7.7K, pi-staking +7.1K/+24 users). A mild bullish-conviction counter-signal to the otherwise bearish tape."}]}

# ---------- dormant activations ----------
dormant_activations=[]

# ---------- watch list ----------
mw_bal=bal_of("erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw") or 998971
watch_list=[
 {"item":f"$2.85 floor BROKE - EGLD {100*(price-pp)/pp:+.1f}% to ${price:.2f} in a broad-market dump","reason":"The downtrend extended and the $2.85 'floor' did not hold. UNLIKE recent weeks this was a market-wide beta move (WoW BTC -6.4%, ETH -9.5%), not EGLD-specific decoupling - EGLD still underperformed (high beta) but moved with the market. 24h prices stabilized (BTC -0.2%, ETH +0.4%). Watch whether $2.55 holds or the market makes further lows; EGLD's beta to BTC/ETH is now the dominant driver.","weeks_on_list":5},
 {"item":"XOXNO LSD (XEGLD) supply COLLAPSED -29% in one week","reason":"XEGLD circulating supply fell 321,592 -> 227,765 (~94K redeemed, ~$300K+), the largest single-protocol LSD supply move in tracking. XOXNO-specific (SEGLD flat). Likely one/few large redeemers. TRACE NEXT RUN: is it a migration (to native delegation / another LSD) or an outright exit? Highest-priority new DeFi watch.","weeks_on_list":1},
 {"item":"Net exchange flow REVERSED to outflow (-222K); inflow streak broke","reason":"After 3 inflow weeks, Binance hot -158K and Bybit -56K drove a net outflow. Ambiguous in a dump (capitulation withdrawals vs OTC routing). The bearish counter: 195K of OTC distribution throughput ran simultaneously, so distribution shifted channel rather than stopping. Watch whether outflow continues (latent accumulation) or reverts.","weeks_on_list":1},
 {"item":"OTC distribution wave ACTIVE (195K throughput) + desks reloading (+35K)","reason":"The run #13-predicted distribution wave arrived in week 1: combined OTC throughput 195K (up from 85K, highest in tracking) WHILE desk balances rose +35K. Heavy two-way flow = ongoing retail distribution with more loaded. Bearish retail-overhang; watch for the throughput to land on exchanges.","weeks_on_list":5},
 {"item":"Binance Staking custody STALLED 4th consecutive week at 3.51M","reason":"7 weeks of an undeployed 779K-EGLD position ($1.99M). This week's +81K staked rise came from yield-chase wallets, NOT this custody. No delegation, no drawdown. The longer frozen, the more decisive the eventual move. Highest-priority single-wallet watch.","weeks_on_list":8},
 {"item":"Delegator base FLAT 2nd week (~174.4K) - capitulation confirmed one-shot","reason":f"2nd consecutive flat week ({deleg_wow:+} this week) confirms run #12's -4,003 drop was a one-shot shake-out, not sustained outflow. The retail-delegation exit has stopped. Resolved - graduating off the watch list next run unless it resumes.","weeks_on_list":2},
 {"item":"Buy-the-dip staking: protocol staked +81K, yield-chase REIGNITED","reason":"Staked rose +81K despite the -10.5% dump. The 0%-fee yield-chase cohort reignited hard: ninjastaking +11.6K, star_staking +7.7K, pi-staking +7.1K (+24 users, 14->38). pi-staking was last run's isolated-entry watch - it is NOT a one-off, it kept drawing. Mild bullish-conviction counter-signal. Watch whether the cohort sustains.","weeks_on_list":1},
 {"item":"Stablecoin burn ACCELERATING 2nd week: USDC -1.3%, USDT -3.7%","reason":"Bridged-stablecoin redemptions accelerated (vs -0.5%/-1.8% last week) = dollar liquidity bridging out, now a 2-week trend. USH (CDP stablecoin) also resumed burning (-3.2%) = on-chain leverage unwinding. Directionally bearish; watch for a 3rd week.","weeks_on_list":2},
 {"item":f"Mega Whale erd18mv2z6r2 ACTIVATED, crossed 1M to {mw_bal:,.0f}","reason":"After 3 weeks dormant, received +11,040 from erd1lgdltequh76 and crossed back above 1M. This is the Apr-18 bilateral-deal OTC counterparty (received 798K then). Has not forwarded onward. A dormant mega-OTC wallet turning active during a distribution wave - watch for any large outbound.","weeks_on_list":4},
 {"item":"SWTAO dataApi price null even after 4x 2.5s re-fetch","reason":"SWTAO-356a25 returned null price after the main pass AND 4 isolated 2.5s retries (SEGLD/XEGLD/USH recovered fine). WTAO price also null, so the accumulator-ratio fallback was unavailable; carried prior price for the USD estimate (supply, the primary signal, is flat). The dataApi feed can stay null for a specific token across a whole run - supply-based reporting is the robust mitigation.","weeks_on_list":1}]

# ---------- executive summary ----------
executive_summary=[
 {"finding":f"$2.85 floor BROKE in a broad-market dump. EGLD {100*(price-pp)/pp:+.2f}% to ${price:.2f}, extending the downtrend. UNLIKE recent weeks this was a market-wide beta move (WoW BTC {btc_wow:+.1f}%, ETH {eth_wow:+.1f}%), not EGLD-specific decoupling - EGLD still underperformed (high beta) but moved WITH the market; 24h prices stabilized at the lows (BTC -0.2%, ETH +0.4%). 7-week drawdown from the May peak ~-45%.","severity":"high","category":"network"},
 {"finding":f"XOXNO LSD (XEGLD) supply COLLAPSED {xegld_supply_wow:+.1f}% in one week (321,592 -> 227,765 XEGLD, ~94K redeemed, ~$300K+) - the largest single-protocol LSD supply move in tracking. XOXNO-SPECIFIC (SEGLD flat), likely a few large redeemers. A standout DeFi event needing tracing (migration vs exit) next run.","severity":"high","category":"defi"},
 {"finding":f"Net exchange flow REVERSED to {net_total:+,.0f} OUTFLOW after 3 inflow weeks (Binance hot -158K, Bybit -56K). Ambiguous in a dump (capitulation withdrawals vs OTC routing), but distribution did not stop - it shifted channel: the OTC pipeline ran a record 195K throughput simultaneously. The 'structural exchange-inflow distribution' streak broke, but on-chain distribution continues via OTC.","severity":"high","category":"whale"},
 {"finding":"OTC distribution wave ACTIVE on schedule (run #13 predicted week 1-3). Combined UPbit OTC + OTC Distribution 7d throughput 195K EGLD (up from 85K, highest in tracking) WHILE desk balances reloaded +35K. Heavy two-way OTC flow - ongoing retail distribution with more loaded. Dominant bearish on-chain signal this week.","severity":"high","category":"whale"},
 {"finding":f"Delegator capitulation CONFIRMED a one-shot. The base held flat for a 2nd consecutive week at {cur_deleg:,} ({deleg_wow:+}). Resolves run #12's key open question - the -4,003 drop was a single shake-out, not sustained outflow. Meanwhile protocol staked ROSE +81K (buy-the-dip) and the 0%-fee yield-chase cohort reignited (ninjastaking +11.6K, pi-staking +7.1K/+24 users) - a mild bullish-conviction counter-signal.","severity":"medium","category":"staking"},
 {"finding":"Binance Staking custody STALLED a 4th consecutive week at 3.51M EGLD (7 weeks parked, 779K, $1.99M). This week's +81K staked rise came from yield-chase wallets, NOT this custody. Entrenched structural position; the eventual delegate-vs-distribute decision becomes more decisive each frozen week.","severity":"high","category":"whale"},
 {"finding":f"Stablecoin burn ACCELERATED for a 2nd week: USDC {usdc_supply_wow:+.2f}%, USDT {usdt_supply_wow:+.2f}% (vs -0.5%/-1.8% last week) - dollar liquidity bridging out during the dump. USH (CDP stablecoin) also resumed burning ({ush_supply_wow:+.2f}%) = on-chain leverage unwinding. A 2-week capital-flight / de-leveraging trend.","severity":"low","category":"defi"},
 {"finding":"Mega Whale erd18mv2z6r2 ACTIVATED after 3 weeks dormant - received +11,040 and crossed back above 1M to 1,010,011. This is the Apr-18 bilateral-deal OTC counterparty (received 798K then). Has not forwarded onward; a dormant mega-OTC wallet turning active during a distribution wave is worth flagging.","severity":"medium","category":"whale"}]

# ---------- network health ----------
btc_wow=100*(be["bitcoin"]["usd"]-pecon.get("btc_price_usd",be["bitcoin"]["usd"]))/pecon.get("btc_price_usd",be["bitcoin"]["usd"]) if pecon.get("btc_price_usd") else None
eth_wow=100*(be["ethereum"]["usd"]-pecon.get("eth_price_usd",be["ethereum"]["usd"]))/pecon.get("eth_price_usd",be["ethereum"]["usd"]) if pecon.get("eth_price_usd") else None
network_health={
 "economics":{"egld_price_usd":price,"market_cap_usd":econ["marketCap"],"total_supply":econ["totalSupply"],
   "circulating_supply":econ["circulatingSupply"],"staked_egld":staked,"staked_ratio":sr,
   "staking_apr":econ["apr"],"base_apr":econ["baseApr"],"topup_apr":econ["topUpApr"],"token_market_cap_usd":econ["tokenMarketCap"]},
 "activity":{"total_accounts":st["accounts"],"total_transactions":st["transactions"],"epoch":st["epoch"],
   "blocks":st["blocks"],"shards":st["shards"],"transactions_7d":st["transactions"]-pact["total_transactions"],
   "avg_daily_transactions":round((st["transactions"]-pact["total_transactions"])/7)},
 "deltas":{"price_change_pct":100*(price-pp)/pp,
   "market_cap_change_pct":100*(econ["marketCap"]-pecon["market_cap_usd"])/pecon["market_cap_usd"],
   "staked_ratio_change_pp":100*(sr-pecon["staked_ratio"]),
   "apr_change_pp":100*(econ["apr"]-pecon["staking_apr"]),"accounts_added":st["accounts"]-pact["total_accounts"],
   "btc_correlation_note":f"EGLD {100*(price-pp)/pp:+.2f}% WoW vs BTC {btc_wow:+.2f}% / ETH {eth_wow:+.2f}% (WoW). UNLIKE recent weeks, EGLD moved WITH the market this time - this was a broad-crypto dump (BTC and ETH both down hard), with EGLD underperforming as a high-beta asset rather than decoupling on MultiversX-specific weakness. 24h prices stabilized at the lows (BTC -0.24%, ETH +0.37%).",
   "transactions_added":st["transactions"]-pact["total_transactions"],"supply_added":econ["totalSupply"]-pecon["total_supply"],
   "staked_egld_added":staked-pecon["staked_egld"],"epoch_advanced":st["epoch"]-pact["epoch"]},
 "analysis":f"EGLD {100*(price-pp)/pp:+.2f}% WoW to ${price:.2f} - the $2.85 floor broke and the downtrend extended. z={zp[2]:+.2f}σ (only moderate because the multi-week decline has widened the baseline; the raw -10.5% is the 2nd-largest weekly drop in tracking). The key context: this was a BROAD-MARKET dump (WoW BTC {btc_wow:+.2f}%, ETH {eth_wow:+.2f}%), so EGLD moved WITH the market as a high-beta asset rather than decoupling on MultiversX-specific weakness as in prior weeks; 24h prices stabilized at the lows. Market cap ${econ['marketCap']/1e6:.1f}M ({100*(econ['marketCap']-pecon['market_cap_usd'])/pecon['market_cap_usd']:+.1f}%). NOTABLY, on-chain conviction metrics IMPROVED against the price: protocol staked ROSE +{staked-pecon['staked_egld']:,} to {staked/1e6:.3f}M (buy-the-dip staking; staked ratio {sr*100:.2f}%, {100*(sr-pecon['staked_ratio']):+.2f}pp), the delegator base held FLAT for a 2nd week at {cur_deleg:,} (confirming last week's -4,003 was a one-shot), and the 0%-fee yield-chase cohort reignited. Activity: {round((st['transactions']-pact['total_transactions'])/7)/1e6:.1f}M txs/day, account growth +{(st['accounts']-pact['total_accounts'])/1000:.1f}K. The read: price fell on broad-market beta, but the domestic retail-delegation base stabilized and even added stake into the dip - a divergence between price (bearish, market-driven) and staking conviction (mildly bullish). The dominant bearish on-chain signal is the OTC pipeline running a record 195K distribution throughput, not the staking side."}

# ---------- whale analysis ----------
whale_analysis=("THIS WEEK'S DOMINANT MOVES:\n"
 f"1) OTC DISTRIBUTION WAVE RAN AT RECORD SCALE. Combined UPbit OTC + OTC Distribution 7d outbound throughput hit 195,447 EGLD (up from 85K last week - the highest in tracking). The distribution wave that run #13's reload predicted arrived in week 1 of the 1-3 week window. SIMULTANEOUSLY the desks reloaded: UPbit OTC +18K to 53,619 and OTC Distribution +17K to 52,962 (combined desk balance +35K). So the OTC fabric is running heavy TWO-WAY flow - distributing 195K while loading another 35K - and OTC source erd17l22 (+16K to 317K) is actively feeding it. This is a large, ongoing retail-distribution operation and the dominant bearish on-chain signal this week.\n\n"
 f"2) NET EXCHANGE FLOW REVERSED TO OUTFLOW ({net_total:+,.0f} EGLD), breaking the 3-week inflow streak. Binance hot wallets -158K (683K -> 525K) and Bybit -56K dominate; Coinbase's 3-week inflow streak also broke (-1.6K). The Binance move is not traceable via standard /transactions (internal transfers). CAVEAT: a large net outflow during a -10.5% market-wide dump is ambiguous - it can be capitulation withdrawals to self-custody (latent accumulation) OR routing to the OTC pipeline. Given the record OTC throughput running underneath, a meaningful share is distribution plumbing, so the outflow is NOT cleanly bullish. Net read: exchange-deposit distribution paused, but distribution shifted channel to OTC rather than stopping.\n\n"
 "3) BINANCE STAKING CUSTODY STALLED 4TH CONSECUTIVE WEEK at 3,512,650 EGLD. The 3-week accumulation phase (runs #7+9+10, +402K) is now followed by a 4-week stall - 7 weeks of a frozen, undeployed 779K-EGLD position ($1.99M at current price). Tellingly, this week's +81K protocol-staked rise came from OTHER (yield-chase) wallets, NOT this custody. Entrenched structural position; each frozen week increases the decisiveness of the eventual delegate-vs-distribute move.\n\n"
 f"4) WHALE TIERS (top-{N_prev} apples-to-apples): mega {whale_tiers['mega_whales']['net_change_egld']/1000:+.0f}K, large {whale_tiers['large_whales']['net_change_egld']/1000:+.0f}K, mid {whale_tiers['mid_whales']['net_change_egld']/1000:+.0f}K. The large mega-tier 'gain' and large-tier 'loss' are a RECLASSIFICATION ARTIFACT: Mega Whale erd18mv2z6r2 crossed the 1M threshold (998,971 -> 1,010,011), moving a ~1M wallet from the large tier into the mega tier. Net of that boundary crossing, the tiers are roughly flat - there is no organic mega-accumulation story this week.\n\n"
 f"5) MEGA WHALE erd18mv2z6r2 ACTIVATED after 3 weeks dormant - received +11,040 EGLD from erd1lgdltequh76 and crossed back above 1M to {mw_bal:,.0f}. This is the Apr-18 bilateral-deal OTC counterparty (it received 798K then). The inbound is modest and it has not forwarded the funds onward, but a previously-dormant mega-OTC counterparty turning active during a distribution wave is worth watching for any large outbound.")

# ---------- staking analysis ----------
staking_analysis=(f"Staking concentration remains low (HHI {hhi:.4f}, top-5 {top5:.1f}%, top-10 {top10:.1f}% - essentially unchanged WoW). Total delegated {total_locked:,.0f} EGLD across {len(provs)} active providers (+{total_locked-prev['staking_concentration']['total_locked_egld']:,.0f} WoW). Active delegator base {cur_deleg:,} ({deleg_wow:+}, {100*deleg_wow/prev_deleg:+.3f}%).\n\n"
 f"DELEGATOR CAPITULATION CONFIRMED A ONE-SHOT. The base held essentially FLAT for a 2nd consecutive week ({deleg_wow:+} this week, after last week's flat read) at {cur_deleg:,}, definitively confirming that run #12's -4,003 drop (largest in tracking by 9x) was a single shake-out, not the start of sustained outflow. The raw z-score reads {zd[2]:+.2f}σ but is the run #9 degenerate case (baseline mean dragged by the pre-capitulation ~179K level) - downgraded to LOW. Run #12's highest-information open question is now resolved: the retail-delegation exit has stopped.\n\n"
 f"BUY-THE-DIP STAKING: protocol staked ROSE +{staked-pecon['staked_egld']:,} EGLD and delegation TVL +{total_locked-prev['staking_concentration']['total_locked_egld']:,.0f} despite the -10.5% price dump - a reversal of the prior multi-week unstaking drift. The 0%-fee yield-chase cohort REIGNITED HARD (net ~{cohort_net/1000:+.0f}K): ninjastaking {cohort_flows.get('ninjastaking',0):+,.0f} (the single largest provider gain), star_staking {cohort_flows.get('star_staking',0):+,.0f}, valuestaking {cohort_flows.get('valuestaking',0):+,.0f}; partly offset by egldstakingprovider {cohort_flows.get('egldstakingprovider',0):+,.0f}, orius {cohort_flows.get('orius',0):+,.0f}. Separately, pi-staking (9.33% APR, 0% fee) drew +7,075 from +24 new delegators (14 -> 38 users) - last run's isolated-entry watch is NOT a one-off; it kept drawing fresh delegation. This is a mild bullish-conviction counter-signal against the bearish tape: some holders locked EGLD into yield during the sell-off.\n\n"
 f"APR distribution: {buckets[3]['provider_count']} providers in the 8-9% bucket holding {buckets[3]['total_locked_egld']/1e6:.1f}M EGLD (the dominant cluster); the 9-10% bucket holds {buckets[4]['provider_count']} providers / {buckets[4]['total_locked_egld']/1e3:.0f}K EGLD. Empty 10%+ bucket (consistent across all 2026 runs). APR-weighted average {apr_w:.2f}%.\n\n"
 f"DELEGATOR CHURN: {gain} providers gaining vs {lose} losing delegators ({deleg_wow:+} net) - balanced, healthy churn. No notable named-validator joiners/leavers >50K EGLD; system-contract aggregators (erd1qqqq...) excluded per the run #10 rule.")

# ---------- token analysis ----------
top_pair_share=pairs[0]['share_pct']
second_pair=pairs[1] if len(pairs)>1 else None
token_analysis=(f"DEX volume rose to ${totvol/1000:.0f}K ({100*(totvol-prev_dexvol)/prev_dexvol:+.0f}% WoW) - a modest recovery off the prior weeks' floor but still depressed vs the $100K+ of a month ago. WEGLD/USDC dominance {top_pair_share:.1f}% (the highest in recent runs); ZoidPay/WEGLD share {second_pair['share_pct'] if second_pair else 0:.1f}%. Volume rose on the dump (sell-side turnover), consistent with the broad-market beta move.\n\n"
 f"NEWLY-ISSUED TOKENS: the ESDT system-SC issue scan returned 0 issuances this week - a 3rd consecutive empty week. The method is validated (run #11+); empty results signal genuinely low launch activity in the bear tape.\n\n"
 f"Token holder counts declined for a 14th consecutive week (small declines across the top 10) - the established airdrop-decay baseline. WrappedEGLD and WrappedUSDC remain the most-held real tokens.\n\n"
 f"MEX price {100*(meco['price']-prev_mexp)/prev_mexp:+.2f}% to ${meco['price']:.3e}, tracking EGLD down through the dump. MEX mcap ${meco['marketCap']/1e6:.2f}M.\n\n"
 f"Top by market cap: EmoryaSportsX (EMRS) leads at ${D['tokens_mcap'][0].get('marketCap',0)/1e6:.1f}M. CORRECTION to last run's read: EMRS is NOT a thin low-float listing - it has {D.get('emrs_token',{}).get('accounts',0):,} holders and {D.get('emrs_token',{}).get('transactions',0):,} transactions, genuine traction that places it among the network's most-held tokens. It just doesn't lead the volume table. After EMRS: WrappedUSDC ${D['tokens_mcap'][1].get('marketCap',0)/1e6:.2f}M, xMoney UTK ${D['tokens_mcap'][2].get('marketCap',0)/1e6:.2f}M, ZoidPay ${D['tokens_mcap'][3].get('marketCap',0)/1e6:.2f}M (continuing its multi-week mcap slide), StakedEGLD ${D['tokens_mcap'][4].get('marketCap',0)/1e6:.2f}M.\n\n"
 f"Bridged stablecoin supply CONTRACTED for a 2nd consecutive week, ACCELERATING: USDC {usdc_supply_wow:+.2f}% and USDT {usdt_supply_wow:+.2f}% (vs -0.47%/-1.75% last week). Stablecoin redemptions during the dump = dollar liquidity bridging out of the ecosystem - a sustained capital-flight signal, now a 2-week trend.")

# ---------- defi analysis ----------
defi_analysis=(f"XOXNO LSD SUPPLY COLLAPSED {xegld_supply_wow:+.1f}% - THE DEFI EVENT OF THE WEEK. In price-independent supply terms, XEGLD circulating supply fell from 321,592 to 227,765 (~94K XEGLD redeemed, ~$300K+) - the largest single-protocol LSD supply move in tracking history. This validates the run #13 methodology (report LSDs in supply, not mcap): the move is unambiguous on a supply basis and would have been muddied by the parallel -10.5% price drop in mcap terms. It is XOXNO-SPECIFIC, NOT synchronized: SEGLD supply only {segld_supply_wow:+.2f}%, SWTAO {swtao_supply_wow:+.2f}% (flat). The size and single-week timing point to one or a few large redeemers exiting XOXNO's liquid-staking product. TRACE NEXT RUN: is this a migration (to native delegation - consistent with the +81K protocol-staked rise and yield-chase reignition this week - or to another LSD) or an outright exit? Either way XOXNO LSD TVL stepped down materially (now ${xoxno_lsd/1e6:.2f}M / {xlsd_egld/1000:.0f}K EGLD vs ${prev['defi_tvl']['XOXNO LSD']/1e6:.2f}M / {prev_xl_egld/1000:.0f}K last week).\n\n"
 f"OTHER LSDs FLAT in supply terms: SEGLD {segld_supply_wow:+.2f}% (mild redemption), SWTAO {swtao_supply_wow:+.2f}% (flat - supply intact even though its dataApi price feed was null this run). Hatom LSD ${hatom_lsd/1e6:.2f}M USD (SEGLD ${segld_mcap/1e6:.2f}M + SWTAO ${swtao_mcap/1e6:.2f}M est.), {100*(hatom_lsd-prev_hlsd)/prev_hlsd:+.1f}% USD - the USD decline is mostly EGLD/TAO price, not redemptions. NOTE: the SWTAO USD figure is an ESTIMATE (carried prior-week price; the dataApi feed stayed null across the whole run, see data-quality below); the supply read (flat) is the reliable signal.\n\n"
 f"HATOM USH stablecoin ${hatom_ush/1000:.0f}K, supply {ush_supply_wow:+.2f}% WoW - the burn/de-leveraging RESUMED after last week's pause. Borrowers re-closing CDP positions during the dump to release collateral and avoid liquidation = on-chain leverage unwinding. Watch for continuation if price weakens further.\n\n"
 f"HATOM LENDING ${hatom_lending/1e6:.2f}M USD ({100*(hatom_lending-prev['defi_tvl']['Hatom Lending'])/prev['defi_tvl']['Hatom Lending']:+.1f}% USD, {100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}% EGLD). The -10.5% price move now EXCEEDS the |Δprice|>=5% guardrail, so the bilateral inverse rule IS evaluable: the EGLD-denominated TVL moved {100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}% (counter to price), consistent with the rule's sign (depositors hold/DCA during dips). Response ratio |{100*(hl_egld-prev_hl_egld)/prev_hl_egld:.1f}%|/|{100*(price-pp)/pp:.1f}%| = {abs(100*(hl_egld-prev_hl_egld)/prev_hl_egld)/abs(100*(price-pp)/pp):.2f} - low, continuing the run #11 'magnitude deterioration / depositor-capacity exhaustion' series.\n\n"
 f"xExchange TVL ${xexch_tvl_usd/1e6:.2f}M / {xexch_tvl_egld/1000:.0f}K EGLD ({100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld:+.1f}% EGLD). DEX volume ${totvol/1000:.0f}K (+{100*(totvol-prev_dexvol)/prev_dexvol:.0f}%). Aggregator throughput: XOXNO {tcount('XOXNO Aggregator'):,}, OneDex {tcount('OneDex Swap'):,} daily transfers.\n\n"
 f"DATA-QUALITY: the dataApi re-fetch guard (added this run per the run #13 recommendation) worked for SEGLD/XEGLD/USH (populated on the first pass) but SWTAO-356a25 stayed null through the main pass AND 4 isolated 2.5s retries. WTAO price was also null, so the accumulator-ratio fallback was unavailable; the SWTAO USD mcap is a carried-prior-price estimate. Lesson reinforced: the dataApi feed can keep a specific token null for an entire run - SUPPLY-based metrics (never null) are the robust primary signal for the LSD/stablecoin set, with USD mcap strictly secondary.")

report={
 "metadata":{"report_date":"2026-06-29","period_start":"2026-06-22T00:00:00Z","period_end":"2026-06-29T00:00:00Z",
   "generated_at":datetime.now(timezone.utc).isoformat(),"egld_price_usd":price,
   "btc_price_usd":be["bitcoin"]["usd"],"eth_price_usd":be["ethereum"]["usd"],"run_number":14,
   "data_sources_ok":json.load(open("/tmp/run14/status.json"))["ok"],
   "data_sources_failed":["SWTAO-356a25 (priceSource=dataApi) returned price=null/marketCap=null on the main pass AND after 4 isolated 2.5s re-fetches; WTAO price also null so the accumulator-ratio fallback was unavailable - SWTAO USD mcap is a carried-prior-price estimate (supply, the primary signal, is intact and flat). SEGLD/XEGLD/USH populated fine via the new dataApi re-fetch guard."]},
 "executive_summary":executive_summary,
 "network_health":network_health,
 "whale_intelligence":{"large_transactions":large_transactions,"wallet_changes":wallet_changes,
   "whale_tiers":whale_tiers,"exchange_flows":exchange_flows,"dormant_activations":dormant_activations,"analysis":whale_analysis},
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
 "meta_learning":{"run_number":14,
   "endpoints_that_worked":json.load(open("/tmp/run14/status.json"))["ok"],
   "endpoints_that_failed":[],
   "api_quirks":[
     "dataApi re-fetch guard (added this run) WORKED for SEGLD/XEGLD/USH (populated first pass) but SWTAO-356a25 stayed null through the main pass AND 4 isolated 2.5s retries. WTAO price was also null, so the accumulator-ratio fallback (run #11) was unavailable. Conclusion: the dataApi feed can keep a SPECIFIC token null for an entire run, not just under sequential load - supply-based metrics (never null) are the robust primary signal; USD mcap for such a token must fall back to a carried-prior-price estimate and be flagged.",
     "Large exchange hot-wallet moves are invisible in /accounts/{addr}/transactions: Binance's -158K hot-wallet drawdown produced no value-bearing standard txs (internal transfers/SC mechanisms). Always compute exchange flow from balance deltas, never from tx scans.",
     "Whale-tier deltas can be dominated by a single wallet crossing a tier boundary: erd18mv2z6r2 crossing 1M (998,971->1,010,011) produced a +997K mega / -1.2M large swing that is a reclassification artifact, not real accumulation. Always check for boundary crossings before narrating tier-aggregate moves.",
     "Stablecoin supply units: /tokens/{id} `supply` is decimals-adjusted; previous.json stores supply_raw (raw integer). For USDC/USDT (6 decimals) divide supply_raw by 1e6 before comparison - else WoW reads -100%."],
   "data_gaps":[
     "SWTAO-356a25 USD mcap is a carried-prior-price estimate this run (dataApi feed null all run, WTAO price also null). Supply is intact; USD figure is approximate.",
     "Binance -158K hot-wallet outflow destination is untraceable via standard txs; split between self-custody and OTC is inferred, not proven.",
     "XEGLD -29% supply collapse: the redeemer(s) and destination are not yet traced - flagged for next run.",
     "Newly-issued token scan returned empty for a 3rd week - cannot distinguish a genuinely quiet launch week from method failure without external corroboration."],
   "key_findings":[
     "XOXNO LSD (XEGLD) supply COLLAPSED -29% in one week (321,592->227,765, ~94K redeemed) - largest single-protocol LSD supply move in tracking; XOXNO-specific (SEGLD flat).",
     "$2.85 floor BROKE: EGLD -10.5% to $2.55, but in a BROAD-MARKET dump (BTC -6.4%, ETH -9.5% WoW) - beta move, not EGLD-specific decoupling.",
     "Net exchange flow REVERSED to -222K outflow (Binance hot -158K, Bybit -56K), breaking the 3-week inflow streak; ambiguous in a dump.",
     "OTC distribution wave HIT at record scale: 195K combined throughput (vs 85K) WHILE desks reloaded +35K - dominant bearish on-chain signal.",
     "Delegator base FLAT 2nd week (~174.4K) - capitulation confirmed a one-shot; protocol staked ROSE +81K (buy-the-dip).",
     "Yield-chase REIGNITED: ninjastaking +11.6K, star_staking +7.7K, pi-staking +7.1K/+24 users (last run's isolated entry kept drawing).",
     "Binance Staking custody STALLED 4th week at 3.51M (7 weeks parked); +81K staked came from yield-chase, not custody.",
     "Stablecoin burn ACCELERATED 2nd week (USDC -1.3%, USDT -3.7%); USH burn RESUMED (-3.2%) = on-chain de-leveraging.",
     "Mega Whale erd18mv2z6r2 ACTIVATED after 3 weeks dormant, crossed 1M (Apr-18 bilateral-deal counterparty)."],
   "action_items_from_previous":9,
   "action_items_completed":8,
   "methodology_changes":[
     "SUPPLY-BASED LSD REPORTING VALIDATED UNDER STRESS: the XEGLD -29% supply collapse this run is unambiguous on a supply basis and would have been muddied by the parallel -10.5% price drop in mcap terms. The run #13 supply-first rule proved its worth in its first real stress test - it surfaced a major redemption that mcap framing would have blended into 'price'.",
     "dataApi RE-FETCH GUARD shipped in collect_run14.py (detect null dataApi-token price after main pass, re-fetch individually at >=2.5s, up to 4 retries). It recovered 3 of 4 tokens; SWTAO needs an additional carried-prior-price USD fallback when WTAO is also null (now in assembler).",
     "EXCHANGE-FLOW-DURING-DUMP AMBIGUITY: a large net exchange OUTFLOW during a broad sell-off is NOT automatically bullish - cross-check the OTC pipeline throughput. This run, 195K of OTC distribution ran underneath a -222K exchange outflow, so distribution shifted channel rather than stopping. New rule: net exchange flow must be read jointly with OTC throughput, never alone.",
     "WHALE-TIER BOUNDARY-CROSSING GUARD: before narrating tier-aggregate net changes, check whether a single wallet crossed a tier threshold (here erd18mv2z6r2 crossing 1M created a phantom +997K mega / -1.2M large swing). Net out boundary crossings first.",
     "BILATERAL INVERSE RULE re-engaged at -10.5% price (>5% guardrail): Hatom Lending EGLD-TVL counter-moved, response ratio ~0.3 - continuing the run #11 magnitude-deterioration series (0.88/0.80/0.70/0.21/~0.3)."],
   "new_addresses_discovered":1,
   "most_valuable_insight":"The XEGLD supply collapse (-29% in one week, ~94K XEGLD redeemed) is the standout finding and a vindication of the run #13 supply-first LSD methodology: on a supply basis it is a clear, large redemption from XOXNO's liquid-staking product, whereas an mcap-only view would have blended it into the -10.5% EGLD price drop and missed it. The week's larger story is a divergence: price fell on broad-market beta (BTC -6.4%, ETH -9.5%), but domestic on-chain conviction actually firmed - the delegator base stabilized for a 2nd week, protocol staked rose +81K, and the 0%-fee yield-chase cohort reignited (buy-the-dip staking). The dominant bearish signal is not the staking side but the OTC pipeline running a record 195K distribution throughput while reloading another 35K.",
   "top_recommendation":"Trace the XEGLD -29% supply collapse: identify the redeemer(s) via XOXNO LSD contract outbound and the destination of the freed EGLD (native delegation, another LSD, or exchange). The hypothesis - that it migrated to native delegation, consistent with the +81K protocol-staked rise and yield-chase reignition - is testable and would distinguish a bullish migration from a bearish exit. Pair with tracking the active OTC distribution wave (195K throughput) onto exchanges.",
   "recommendations_for_next_run":[
     "TRACE XEGLD -29% supply collapse: query the XOXNO LSD contract's outbound flows and the redeemer wallets; classify the freed EGLD destination (native delegation = bullish migration, exchange = bearish exit). Highest-priority follow-up.",
     "OTC distribution wave is ACTIVE (195K throughput, +35K reload): trace UPbit OTC / OTC Distribution outbound chunks to routing wallets and onward to exchanges; confirm whether the distribution lands as exchange inflows next week.",
     "Net exchange flow reversed to -222K outflow during the dump: watch whether it continues (latent self-custody accumulation) or reverts to inflow - and always read it jointly with OTC throughput.",
     "Binance hot -158K: untraceable this run. Watch whether the hot-wallet balance keeps falling (sustained withdrawal) or rebuilds, and whether the OTC desks absorb proportional volume.",
     "Binance Staking custody 5th-week stall watch: 7 weeks parked at 3.51M. The eventual move (delegate=bullish / drawdown=bearish) becomes more decisive each week.",
     "Yield-chase sustainability: ninjastaking +11.6K, star_staking +7.7K, pi-staking +7.1K/+24 users this week. Watch whether buy-the-dip staking sustains (bullish conviction) or unwinds next week.",
     "Stablecoin burn is a 2-week accelerating trend (USDC -1.3%, USDT -3.7%): a 3rd week confirms sustained dollar-liquidity flight; a reversal suggests the de-risking is done.",
     "Does $2.55 hold, or does the broad market make further lows? EGLD is now trading as high-beta to BTC/ETH; track the beta and whether on-chain conviction (staking) keeps diverging from price.",
     "Mega Whale erd18mv2z6r2 just activated (+11K, crossed 1M): watch for any large outbound from this Apr-18 OTC-deal counterparty."],
   "dashboard_feature_suggestions":[
     {"title":"LSD circulating-supply timeline (supply, not mcap)","motivation":"This run delivered the methodology's first real payoff: XEGLD supply collapsed -29% in one week - a major redemption that an mcap-only view would have blended into the -10.5% EGLD price drop and missed entirely. A supply timeline would have made this jump unmissable and is the single highest-value unbuilt widget. Re-listed at high priority for a 3rd run.","suggested_visualization":"dual-line chart of SEGLD and XEGLD circulating supply (in token units) across weekly snapshots, with EGLD price on a secondary axis; a WoW-delta bar overlay would make step-changes like XEGLD -29% pop.","data_already_available":True,"data_source":"data/collected/{date}.json tvl_tokens.{SEGLD,XEGLD}.supply + previous.json lsd_supply across snapshots","priority":"high"},
     {"title":"Exchange-flow vs OTC-throughput dual-axis chart","motivation":"This run's key analytical nuance: net exchange flow reversed to -222K OUTFLOW while OTC distribution ran a record 195K throughput - so distribution did not stop, it shifted channel. Reading either series alone misleads (the outflow looks bullish in isolation). A dual-axis view makes the channel-shift legible and prevents the single-metric misread.","suggested_visualization":"weekly grouped bars: net exchange flow (signed) on the left axis, combined OTC desk throughput on the right axis, with the EGLD price line overlaid; divergence weeks (outflow + high OTC) highlighted.","data_already_available":True,"data_source":"exchange_flows.net_change_egld + OTC desk outbound throughput, both already computed per run","priority":"high"},
     {"title":"OTC pipeline load/distribute cycle phase indicator","motivation":"The pipeline completed another textbook cycle turn this run: run #13 reload (GAP->LOADING) was followed this run by the predicted DISTRIBUTING wave (195K throughput) arriving in week 1 - while still loading. A phase badge would have flagged this transition and the live forward prediction explicitly.","suggested_visualization":"horizontal phase timeline (LOADING / DISTRIBUTING / GAP) across weekly snapshots, with desk-balance-delta and 7d-throughput series and a current-phase badge.","data_already_available":True,"data_source":"OTC desk balances + outbound throughput per run; needs a small per-run phase label in previous.json","priority":"medium"}],
   "dashboard_suggestions_followup":[
     {"from_run":13,"title":"LSD circulating-supply timeline (supply, not mcap)","status":"pending","note":"NOT yet built. This run proved its value decisively (XEGLD -29% supply collapse) - re-listed at high priority for a 3rd consecutive run. Should be the next widget built."},
     {"from_run":13,"title":"OTC pipeline load/distribute cycle phase indicator","status":"pending","note":"NOT yet built. Re-listed - the GAP->LOADING->DISTRIBUTING transition played out exactly as the indicator would track this run."},
     {"from_run":13,"title":"Forward-indicator scorecard (prediction resolution tracker)","status":"deprioritized","note":"Still useful but lower priority than the supply timeline and the exchange-flow-vs-OTC chart, both of which tie directly to THIS run's headline findings. Deferred; replaced in this run's top-3 by the dual-axis exchange/OTC chart."},
     {"from_run":12,"title":"Engagement-collapse composite indicator","status":"deprioritized","note":"The engagement question resolved benignly (delegators stabilized 2nd week, staked rose, yield-chase reignited), so a composite is less urgent than the supply and flow widgets. Deferred."},
     {"from_run":10,"title":"Multi-week Binance custody vs protocol-staked tracker","status":"pending","note":"Now 7 weeks of custody data (3 accumulation + 4 stall) against a protocol-staked line that rose +81K this run from OTHER wallets - the divergence (custody flat, staked up) is exactly what this chart would surface. Still motivated."},
     {"from_run":9,"title":"Multi-week net exchange-flow oscillation chart","status":"superseded","note":"Superseded by this run's exchange-flow-vs-OTC DUAL-AXIS suggestion, which adds the OTC dimension this run showed is essential to interpret exchange flow correctly."},
     {"from_run":8,"title":"OTC pipeline graph view (Sankey/force-directed)","status":"pending","note":"The pipeline ran 195K throughput with traceable Binance->OTC Router->OTC Distribution edges this run. A graph view would render the active distribution edges directly; still a strong idea, lower priority than the timeline/dual-axis charts."}]}}

json.dump(report,open(f"{REPO}/reports/2026-06-29.json","w"),indent=2)
print("WROTE reports/2026-06-29.json")
print("exec_summary:",len(executive_summary),"large_tx:",len(large_transactions),"wallet_changes:",len(wallet_changes),
      "providers:",len(provs),"anomalies:",len(anomalies),"watch:",len(watch_list))
print("net exchange flow:",round(net_total,1),"total_locked:",round(total_locked,1),"apr_w:",round(apr_w,3))
print("DEFI: Hatom Lending USD",round(hatom_lending),"LSD",round(hatom_lsd),"USH",round(hatom_ush),"XOXNO LSD",round(xoxno_lsd))
print("LSD supply WoW: SEGLD %.2f%% XEGLD %.2f%% SWTAO %.2f%% USH %.2f%%"%(segld_supply_wow,xegld_supply_wow,swtao_supply_wow,ush_supply_wow))
print("Token supply events:",len(token_supply_events))
print("Newly issued:",len(newly_issued))
print("DEX volume:",round(totvol,1),"WoW%:",round(100*(totvol-prev_dexvol)/prev_dexvol,1))
print("Delegators:",cur_deleg,"WoW:",deleg_wow,"  cohort_net:",round(cohort_net))
print("Staked:",staked,"WoW:",staked-pecon["staked_egld"])
print("EGLD price:",price,"WoW:",f"{100*(price-pp)/pp:+.2f}%","z=",round(zp[2],2))
print("BTC WoW:",round(btc_wow,2),"ETH WoW:",round(eth_wow,2))
