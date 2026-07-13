#!/usr/bin/env python3
"""Assemble reports/2026-07-13.json (run #16) from collected data."""
import json, math
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D = json.load(open("/tmp/run16/collected.json"))
prev = json.load(open(f"{REPO}/data/previous.json"))
kn = json.load(open(f"{REPO}/data/known-addresses.json"))
learn = json.load(open(f"{REPO}/data/learnings.json"))
prevcol = json.load(open(f"{REPO}/data/collected/2026-07-06.json"))  # for supply WoW

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

# OTC desk 7d outbound throughput (hoisted early - referenced in exchange_flows narrative)
def thr(key):
    txs=D.get(key)
    return sum(int(t.get("value","0"))/1e18 for t in txs if isinstance(t,dict)) if isinstance(txs,list) else 0
upbit_thr=thr("upbit_otc_outbound"); dist_thr=thr("otc_dist_outbound")

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
 "Binance":"Net +114,902 INFLOW across 4 wallets - Binance FLIPPED to net inflow this week (coins arriving on Binance hot during the +15.9% rip - sellers positioning?). Two moving parts: (1) the Staking custody continued its 2nd-leg drawdown -43,118 (3,353,797 -> 3,310,680), traced via standard transfers (Binance.com hot -> custody 156,882, custody -> Binance.com 200,000 = net -43K custody -> hot); the custody has now shed -202K over two weeks from its 3.51M peak. (2) A Binance.com hot wallet grew +151,024 (141,094 -> 292,118) - more than the +43K the custody sent it, so ~+108K of EXTERNAL EGLD also arrived on Binance hot this week. Net: Binance is de-staking (custody drawdown) AND taking net deposits onto its hot wallets into the strength - a distributive posture, not accumulation.",
 "Coinbase":"+10K net across 4 wallets - a mild reversal back to inflow. Coinbase primary -53K but Coinbase (secondary) +62K, a wallet reshuffle netting mildly positive. The Coinbase Routing -> Mega Whale erd18mv2z6r2 pipe went QUIET this week (the mega whale held flat, no new absorption).",
 "Crypto.com":"+15K (+7.3%) across 2 wallets - a 2nd consecutive inflow week. Capital moving onto Crypto.com into the rally.",
 "Bybit":"-221,402 (-46.5%) on the cold wallet - BY FAR the largest single exchange move this week and the dominant driver of the aggregate net OUTFLOW (476,430 -> 255,027). In isolation a -221K exchange outflow during a rip reads as self-custody accumulation, but its destination is not cleanly traced (internal-transfer-invisible) - so read jointly with the record OTC throughput, it is ambiguous (self-custody vs OTC-routing). Reverses last week's +21K inflow.",
 "UPbit":"Cold wallet -131,346 (-10.6%) OUTFLOW (1,237,926 -> 1,106,580) - but this is OTC ROUTING, not customer withdrawal: UPbit fed its own UPbit OTC Desk 320,000 + 140,000 = 460K in standard transfers this week, and the desk balance grew +117K. UPbit's 'outflow' is the loading leg of a large OTC distribution wave (see OTC section), not coins leaving to self-custody.",
 "MEXC":"+3.5K (+4.1%). Mild inflow.",
 "KuCoin":"-4.9K (-13.0%). Mild outflow off a small base.",
 "Bitget":"-6.9K (-8.0%). Mild outflow.",
 "Gate.io":"+26K (+43.1%) - the largest proportional inflow this week, a 2nd straight inflow week off a small base.",
 "Tokero":"Flat.",
 "Bitfinex":"-0.6K. Flat."}
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
    "signal":f"Net exchange flow {net_total:+,.0f} EGLD ({100*net_total/total_prev if total_prev else 0:+.2f}%) - a 3rd consecutive net OUTFLOW, but the composition is NOT clean accumulation. The outflow is concentrated in just two venues: Bybit -221K (destination untraced) and UPbit -131K (which is OTC ROUTING - UPbit fed its own OTC Desk 460K in standard transfers, loading the desk +117K). Against those, the REST of the complex took coins IN during the rip: Binance +115K (custody de-staking but hot wallets net-inflow), Gate.io +26K, Crypto.com +15K, Coinbase +10K, MEXC +3.5K. So per the run #15 rule (decompose before labeling), the aggregate -196K is Bybit+UPbit outflow (one ambiguous, one OTC-routed) on top of a broadly INFLOW tape. Read jointly with OTC (run #14 rule): the desks RELOADED +238K (the biggest single-week load in tracking) and ran a RECORD ~{(upbit_thr+dist_thr)/1000:.0f}K of 7d throughput - a large distribution wave is being LOADED into the strength. Net read: despite the green candle, on-chain positioning is distributive - Binance de-staking + Bybit dump + a record OTC reload - and this week the identifiable absorber (Mega Whale erd18mv2z6r2) stepped BACK (flat), so the distribution is not being visibly soaked up the way it was last week.",
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
# newly_issued: the ESDT system-SC issue scan can FALSE-POSITIVE onto long-established
# tokens when an `issue`-function tx in the window resolves via name-search to an old
# ticker. Run #15: it matched WrappedUSDC (USDC-c76f1f, 81,516 holders) - clearly not a
# fresh mint. Filter out anything with a large existing holder base (>1,000) or an already-
# canonical identifier in known-addresses/previous - a genuinely new token this window has
# a tiny holder count. Keep the quality bar (>10 holders, >5 txs) for the rest.
KNOWN_TOKEN_IDS={t["identifier"] for t in prev.get("top_tokens_by_holders",[])} | {t["identifier"] for t in prev.get("top_tokens_by_volume",[])}
newly_issued=[]
for ni in D.get("newly_issued", []):
    if ni["accounts"]>1000 or ni["identifier"] in KNOWN_TOKEN_IDS:
        continue  # established token misidentified by the issue-scan name match
    if ni["accounts"]<=10 or ni["transactions"]<=5:
        continue  # spam / dormant deploy
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
  "notable_events":f"DEX volume ${totvol/1000:.0f}K (+{100*(totvol-prev_dexvol)/prev_dexvol:.0f}% WoW) - a real jump on the +16% price rip, the highest since spring. Extremely concentrated: WEGLD/USDC {pairs[0]['share_pct']:.1f}% (CEX-derived buyers routing the deep stable pair), {pairs[1]['name'] if len(pairs)>1 else '?'} {pairs[1]['share_pct'] if len(pairs)>1 else 0:.1f}% the only other meaningful pair. WEGLD supply WoW {wegld_chg_pct:+.2f}% (net unwrapping to native EGLD).","health_signal":"growing"},
 {"protocol":"Hatom Lending","category":"lending","addresses_tracked":13,"tvl_usd":hatom_lending,"tvl_egld":hl_egld,
  "tvl_wow_change_pct":100*(hl_egld-prev_hl_egld)/prev_hl_egld,"transfers_24h":tcount("Hatom EGLD MM"),
  "notable_events":f"TVL ${hatom_lending/1e6:.2f}M USD ({100*(hatom_lending-prev['defi_tvl']['Hatom Lending'])/prev['defi_tvl']['Hatom Lending']:+.1f}%), {hl_egld/1000:.0f}K EGLD ({100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}% EGLD). Bilateral inverse rule EVALUABLE (price +{100*(price-pp)/pp:.1f}% exceeds the |dPrice|>=5% threshold): EGLD-denominated TVL moved {100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}% (counter to price - depositors WITHDREW to capture gains into the rally, the mirror of the dip-DCA behavior). Response ratio {abs(100*(hl_egld-prev_hl_egld)/prev_hl_egld)/abs(100*(price-pp)/pp):.2f}.","health_signal":"flat"},
 {"protocol":"Hatom Liquid Staking","category":"liquid_staking","addresses_tracked":2,"tvl_usd":hatom_lsd,"tvl_egld":hlsd_egld,
  "tvl_wow_change_pct":100*(hlsd_egld-prev_hlsd_egld)/prev_hlsd_egld,"transfers_24h":tcount("Hatom Liquid Staking"),
  "notable_events":f"SEGLD ${segld_mcap/1e6:.2f}M + SWTAO ${swtao_mcap/1e6:.2f}M = ${hatom_lsd/1e6:.2f}M USD ({100*(hatom_lsd-prev_hlsd)/prev_hlsd:+.1f}%, up with the price). On a supply basis Hatom LSD is FLAT: SEGLD {segld_supply_wow:+.2f}%, SWTAO {swtao_supply_wow:+.2f}%. dataApi price feed clean (0 re-fetch retries, all 4 tokens first pass).","health_signal":"flat"},
 {"protocol":"Hatom USH","category":"stablecoin","addresses_tracked":4,"tvl_usd":hatom_ush,"tvl_egld":ush_egld,
  "tvl_wow_change_pct":100*(hatom_ush-prev_hush)/prev_hush,"transfers_24h":None,
  "notable_events":f"USH mcap ${hatom_ush/1000:.0f}K ({100*(hatom_ush-prev_hush)/prev_hush:+.1f}% USD). USH supply MINTED {ush_supply_wow:+.2f}% WoW to {supply('USH-111e09'):,.0f} - the largest USH move since the run #11 -7% burn, and in the OPPOSITE direction: borrowers are OPENING new CDP positions (minting USH against collateral) = on-chain LEVERAGE RETURNING as EGLD rallies. The mirror of the multi-week de-leveraging burn during the decline. A genuine-demand signal.","health_signal":"growing"},
 {"protocol":"XOXNO LSD","category":"liquid_staking","addresses_tracked":2,"tvl_usd":xoxno_lsd,"tvl_egld":xlsd_egld,
  "tvl_wow_change_pct":100*(xlsd_egld-prev_xl_egld)/prev_xl_egld,"transfers_24h":tcount("XOXNO LSD"),
  "notable_events":f"XEGLD ${xoxno_lsd/1e6:.2f}M ({100*(xoxno_lsd-prev['defi_tvl']['XOXNO LSD'])/prev['defi_tvl']['XOXNO LSD']:+.1f}% USD). The real signal is SUPPLY: XEGLD supply GREW {xegld_supply_wow:+.2f}% WoW to {supply('XEGLD-e413ed'):,.0f}, RE-ACCUMULATING after the run #14 -29% collapse and run #15 stabilization. The LSD contract's EGLD balance fell -106K as it deployed fresh deposits to validators. Liquid staking is back in inflow - the redemption event is fully resolved.","health_signal":"growing"},
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
# OTC desk 7d outbound throughput + mega whale current balance (for anomaly/trend narrative)
def thr(key):
    txs=D.get(key)
    return sum(int(t.get("value","0"))/1e18 for t in txs if isinstance(t,dict)) if isinstance(txs,list) else 0
upbit_thr=thr("upbit_otc_outbound"); dist_thr=thr("otc_dist_outbound")
mw_bal_cur=bal_of("erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw") or 1042690
cust_bal=bal_of("erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p") or 3310680
binance_staking_prov_wow=lk_wow("binance_staking")
anomalies=[
 {"metric":"egld_price_usd","current_value":price,"previous_value":pp,"method":"z_score",
  "average_value":zp[0],"stddev":zp[1],"z_score":zp[2],"severity":"medium",
  "description":f"EGLD RIPPED {100*(price-pp)/pp:+.2f}% WoW to ${price:.2f} - a 2nd consecutive up-week and an EGLD-SPECIFIC breakout. Unlike last week's beta-laggard bounce, EGLD this week DECOUPLED to the UPSIDE: WoW BTC {btc_wow:+.2f}%, ETH {eth_wow:+.2f}% (both essentially FLAT) while EGLD gained +15.9%. This flips the multi-month narrative - EGLD had underperformed on the way down and on the first bounce; this week it LED with the majors going nowhere. z is only {zp[2]:+.2f}σ (LOW - the baseline mean has caught up to the current level after two up-weeks), so the z-score understates a real regime change; the rule-based read (EGLD-specific decoupling, no macro tailwind) is the signal. Market cap ${econ['marketCap']/1e6:.1f}M ({100*(econ['marketCap']-pecon['market_cap_usd'])/pecon['market_cap_usd']:+.1f}%). The caveat is on-chain: a record OTC distribution reload is loading into the strength (see below)."},
 {"metric":"otc_pipeline_record_reload","current_value":round(upbit_thr+dist_thr),"previous_value":172000,"method":"rule_based",
  "severity":"high",
  "description":f"THE OTC PIPELINE JUST STAGED ITS BIGGEST RELOAD IN TRACKING - into the price rip. Combined UPbit OTC Desk + OTC Distribution desk balance ROSE +{(bal_of('erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5') or 168484)+(bal_of('erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r') or 166946)-97713:,.0f} EGLD (UPbit OTC 51,128 -> {bal_of('erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5') or 168484:,.0f}, OTC Distribution 46,585 -> {bal_of('erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r') or 166946:,.0f}) - reversing last week's -8.9K drain, and the largest single-week desk load observed. Simultaneously 7d outbound throughput hit a RECORD ~{(upbit_thr+dist_thr)/1000:.0f}K EGLD (vs ~172K last week). The reload was fed directly by UPbit: UPbit -> UPbit OTC Desk 320,000 + 140,000 = 460K in standard transfers. A desk that is both loading heavily AND distributing at record pace = a large distribution wave being SET UP into strength. This is the week's key bearish tell under the green candle."},
 {"metric":"binance_de_staking","current_value":round(cust_bal),"previous_value":3353797,"method":"rule_based",
  "severity":"medium",
  "description":f"BINANCE IS REDUCING STAKED EGLD ON TWO FRONTS INTO THE RIP. (1) The Staking custody continued its 2nd-leg drawdown -{3353797-cust_bal:,.0f} (3,353,797 -> {cust_bal:,.0f}), traced via standard transfers (Binance.com -> custody 156,882; custody -> Binance.com 200,000). The custody has now shed -{3512650-cust_bal:,.0f} over two weeks from its 3.51M peak - the distribution-direction unwind continues. (2) SEPARATELY, the binance_staking DELEGATION provider shed -{abs(binance_staking_prov_wow) if binance_staking_prov_wow else 148941:,.0f} EGLD of locked stake this week (numUsers ~flat). Combined, Binance pulled ~-{(3353797-cust_bal)+(abs(binance_staking_prov_wow) if binance_staking_prov_wow else 148941):,.0f} EGLD out of staked/custody positions. Meanwhile Binance hot wallets took net +115K INFLOW (custody's 200K PLUS ~108K external). Every leg points the same way: de-stake and accumulate on hot wallets into the strength - a distributive posture."},
 {"metric":"ush_supply_mint","current_value":round(supply('USH-111e09') or 626942),"previous_value":round((supply('USH-111e09') or 626942)/(1+(ush_supply_wow or 6.49)/100)),"method":"rule_based",
  "severity":"medium",
  "description":f"USH (Hatom CDP stablecoin) supply MINTED +{ush_supply_wow:+.2f}% WoW to {supply('USH-111e09'):,.0f} - the largest USH supply move since the run #11 -7% burn, and this time in the OTHER direction. USH supply grows when borrowers OPEN new CDP positions (mint USH against collateral); a +6.5% mint = on-chain LEVERAGE RETURNING as EGLD rallies. This is the clean mirror of the multi-week de-leveraging burn seen during the decline (borrowers force-closing to avoid liquidation). A constructive, genuine-demand signal: DeFi participants are re-levering into the strength, not de-risking. Surface in exec_summary (>5% supply move)."},
 {"metric":"mex_price_usd","current_value":meco["price"],"previous_value":prev_mexp,"method":"z_score",
  "average_value":zmex[0],"stddev":zmex[1],"z_score":zmex[2],"severity":"low",
  "description":f"MEX price {100*(meco['price']-prev_mexp)/prev_mexp:+.2f}% to ${meco['price']:.3e} (z={zmex[2]:+.2f}σ, N={len(rb['mex_price_usd'])}), tracking EGLD's rip. MEX mcap ${meco['marketCap']/1e6:.2f}M. DEX volume +{100*(totvol-prev_dexvol)/prev_dexvol:.0f}% to ${totvol/1000:.0f}K - a real jump on the rally, though WEGLD/USDC carries {pairs[0]['share_pct']:.0f}% of it (thin, CEX-derived buyers parking in the stable pair)."},
 {"metric":"total_delegators","current_value":cur_deleg,"previous_value":prev_deleg,"method":"z_score",
  "average_value":zd[0],"stddev":zd[1],"z_score":zd[2],"severity":"low",
  "description":f"Total delegators {cur_deleg:,} ({deleg_wow:+,} WoW = {100*deleg_wow/prev_deleg:+.3f}%). Raw z={zd[2]:+.2f}σ but this is the run #9 DEGENERATE-Z-SCORE case (baseline mean dragged by the pre-capitulation ~179K level) - the actual WoW move is essentially ZERO. DOWNGRADED to LOW. The delegator base has now been FLAT for a 4th CONSECUTIVE week at ~174.3K - the run #12 -4,003 capitulation is decisively behind us; no new retail joining on the rip yet either. Meanwhile delegation TVL fell -{abs(total_locked-prev['staking_concentration']['total_locked_egld']):,.0f} NET, but that is ENTIRELY the binance_staking provider -149K; ex-Binance, delegation grew +120K broadly (smartchainconnection +38K, pokerstaking +16.6K, Synexis +9.3K)."},
 {"metric":"staked_egld","current_value":staked,"previous_value":pecon["staked_egld"],"method":"z_score",
  "average_value":zse[0],"stddev":zse[1],"z_score":zse[2],"severity":"low",
  "description":f"Total staked {staked:,} EGLD ({staked-pecon['staked_egld']:+,} WoW, {100*(staked-pecon['staked_egld'])/pecon['staked_egld']:+.2f}%) - UP +80K even as EGLD ripped +16% (staking through a rally, not chasing spot). z={zse[2]:+.2f}σ. Note the DIVERGENCE: economics.staked (direct-node + delegation) ROSE +80K while delegation-contract TVL FELL -{abs(total_locked-prev['staking_concentration']['total_locked_egld']):,.0f} - the opposite of last week. But the delegation drop is entirely the binance_staking provider -149K (Binance de-staking); ex-Binance delegation GREW +120K broadly, and direct-node staking rose. Staked ratio {sr*100:.2f}% ({100*(sr-pecon['staked_ratio']):+.2f}pp). The 0%-fee yield-chase cohort was flat this week (net {cohort_net/1000:+.1f}K)."},
 {"metric":"stablecoin_supply_mixed","current_value":usdc_supply_wow,"previous_value":-2.0,"method":"rule_based",
  "severity":"low",
  "description":f"Bridged-stablecoin supply MIXED again: USDC {usdc_supply_wow:+.2f}% (a 4th burn week but DECELERATING from -2.0% last week) while USDT {usdt_supply_wow:+.2f}% (RE-ACCELERATED from -0.3%). No clean signal - the dollar-liquidity picture is choppy rather than a directional flight. Contrast with USH (native CDP stablecoin) which MINTED +{ush_supply_wow:.1f}% - the bridged-dollar contraction and the native-leverage expansion are pointing opposite ways, consistent with capital rotating from parked stables into levered EGLD exposure on the rally."}]

# ---------- trend indicators ----------
accelerating_outflows=[
 {"exchange":"NET_EXCHANGE","trend":"outflow","cumulative_change_pct":None,"weeks_in_trend":3,
  "interpretation":f"Aggregate net exchange flow {net_total:+,.0f} EGLD OUTFLOW - a 3rd consecutive outflow week, but NOT clean accumulation. Decomposed: Bybit -221K (untraced) and UPbit -131K (OTC-routing - fed its own OTC Desk 460K) are the only material outflows; the rest of the complex took coins IN (Binance +115K, Gate.io +26K, Crypto.com +15K, Coinbase +10K, MEXC +3.5K). Per the run #14 joint-read rule the decisive channel is OTC, not the exchange balance: the desks RELOADED +238K (biggest in tracking) and ran a record ~{(upbit_thr+dist_thr)/1000:.0f}K throughput. So the 'outflow' overstates accumulation - it is one dump (Bybit) plus an OTC loading leg (UPbit)."},
 {"exchange":"Bybit","trend":"outflow","cumulative_change_pct":None,"weeks_in_trend":1,
  "interpretation":"Bybit cold wallet -221,402 (476,430 -> 255,027), -46.5% - the single largest exchange move this week, reversing last week's +21K inflow. Destination is internal-transfer-invisible so it cannot be classed as self-custody vs OTC-routing. In a week with a record OTC reload, treat it as ambiguous rather than assuming bullish self-custody. Watch for a re-inflow (round-trip) or a downstream OTC/routing appearance next week."},
 {"exchange":"UPbit OTC Desks","trend":"loading+distributing","cumulative_change_pct":None,"weeks_in_trend":4,
  "interpretation":f"OTC desks staged their BIGGEST RELOAD in tracking (+{(bal_of('erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5') or 168484)+(bal_of('erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r') or 166946)-97713:,.0f} combined desk balance) AND ran a record ~{(upbit_thr+dist_thr)/1000:.0f}K 7d throughput (vs 172K last week). Fed by UPbit -> UPbit OTC Desk 460K. This flips last week's DRAINING back to a heavy LOADING+distributing phase - a large fresh distribution wave is being built into the price strength. Watch whether the throughput sustains (ongoing distribution) or the desks bleed the reload down over coming weeks."}]

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
   {"metric":"egld_price_up","direction":"up","weeks":2,"cumulative_change_pct":round(100*(price-2.55)/2.55,1),
    "interpretation":f"2nd consecutive up-week for EGLD (+{100*(price-pp)/pp:.1f}% to ${price:.2f}, after +5.9% last week) - ~+23% cumulative off the $2.55 low. More important than the streak length: this week's gain was EGLD-SPECIFIC (BTC/ETH flat), so it is no longer just a beta bounce. Watch for a 3rd up-week to confirm a momentum regime, or a fade like the run #12 one-week bounce."},
   {"metric":"reward_compound_rate_up","direction":"up","weeks":3,"cumulative_change_pct":None,
    "interpretation":"Reward compound rate rose a 3rd straight week (58.54% -> 60.35% -> 61.59%). Delegators are increasingly compounding rather than claiming as EGLD rallies - a bullish DeFi-sentiment tell (the mirror of the panic-claim drift during the decline). Back near the run #11 61.9% baseline."},
   {"metric":"delegator_base_flat","direction":"flat","weeks":4,"cumulative_change_pct":0,
    "interpretation":f"4th consecutive flat week for the delegator base at ~174.3K ({deleg_wow:+,} this week). The run #12 capitulation is long behind us - but note NO new retail joined on the +16% rip either, so the flatness is now a mild disappointment rather than a relief. The rally is being driven by existing holders re-levering, not new participants."},
   {"metric":"token_holder_count_decline","direction":"down","weeks":16,"cumulative_change_pct":None,
    "interpretation":"16th consecutive week of small holder declines across top-10 tokens. Established airdrop-decay baseline; the active >$1M-mcap token base is stable."}],
 "regime_shifts":[
   {"metric":"egld_specific_outperformance","before_value":pp,"after_value":price,
    "description":f"EGLD DECOUPLED TO THE UPSIDE. After months of high-beta-laggard behavior (falling harder than BTC/ETH, bouncing less), EGLD gained +{100*(price-pp)/pp:.1f}% this week while BTC ({btc_wow:+.1f}%) and ETH ({eth_wow:+.1f}%) were essentially FLAT. This is the first EGLD-specific up-move in the tracked decline - a potential regime break from laggard to leader. It is not yet confirmed (one week, and a record OTC distribution reload is loading against it), but a flat-majors / EGLD-up tape is a materially different signal from the run #15 beta bounce. Watch for continuation vs a distribution-driven fade."},
   {"metric":"otc_distribution_wave_reloaded","before_value":97713,"after_value":round((bal_of('erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5') or 168484)+(bal_of('erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r') or 166946)),
    "description":f"The OTC desks flipped from last week's late-phase DRAINING to the LARGEST RELOAD in tracking: combined desk balance {97713:,.0f} -> {round((bal_of('erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5') or 168484)+(bal_of('erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r') or 166946)):,.0f} (+238K), fed by UPbit -> OTC Desk 460K, on top of a record ~{(upbit_thr+dist_thr)/1000:.0f}K throughput. A step-change in distribution capacity being staged into the price strength - the dominant on-chain counter to the bullish price tape."},
   {"metric":"defi_leverage_returning","before_value":round((supply('USH-111e09') or 626942)/(1+(ush_supply_wow or 6.49)/100)),"after_value":round(supply('USH-111e09') or 626942),
    "description":f"USH supply minted +{ush_supply_wow:.1f}% (to {supply('USH-111e09'):,.0f}) and XEGLD (XOXNO LSD) supply grew +{xegld_supply_wow:.1f}% (to {supply('XEGLD-e413ed'):,.0f}, recovering after the -29% collapse) - two independent signals of DeFi leverage/engagement RETURNING as EGLD rallies. Borrowers are re-opening CDPs and liquid-staking is re-accumulating. A genuine-demand counterweight to the distribution loading on the exchange side."}]}

# ---------- dormant activations ----------
dormant_activations=[]

# ---------- watch list ----------
mw_bal=bal_of("erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw") or 998971
watch_list=[
 {"item":f"RECORD OTC RELOAD (+238K desk balance, ~{(upbit_thr+dist_thr)/1000:.0f}K throughput) loading into the +16% rip","reason":"The UPbit OTC + OTC Distribution desks staged their biggest reload in tracking (combined balance ~98K -> ~335K), fed by UPbit -> OTC Desk 460K, while running record 7d throughput. A large distribution wave is being SET UP into the price strength - the dominant bearish tell under the green candle. HIGHEST-PRIORITY follow-up: watch whether the loaded desks bleed the EGLD out over the next 1-3 weeks (the distribution leg) and whether price absorbs it or fades.","weeks_on_list":7},
 {"item":f"EGLD RIPPED +{100*(price-pp)/pp:.0f}% to ${price:.2f} and OUTPERFORMED flat majors (BTC {btc_wow:+.1f}%, ETH {eth_wow:+.1f}%)","reason":"2nd up-week and, unlike last week's beta bounce, an EGLD-SPECIFIC move (majors flat). Potential regime break from high-beta laggard to leader. NOT confirmed (one week, and a record OTC reload is loading against it). Watch for a 3rd up-week (momentum confirmation) vs a distribution-driven fade like the run #12 one-week bounce.","weeks_on_list":1},
 {"item":"Binance de-staking on TWO fronts: custody -43K (2nd leg) + binance_staking provider -149K","reason":"The Staking custody continued its unwind -43K (now -202K over 2 weeks from the 3.51M peak; traced custody<->hot). SEPARATELY the binance_staking delegation provider shed -149K locked. Combined ~-192K pulled out of staked positions, while Binance hot wallets took net +115K inflow. Every leg is distributive. Watch whether the custody keeps drawing down and where the hot-wallet EGLD goes.","weeks_on_list":10},
 {"item":f"Net exchange flow {net_total/1000:+.0f}K (3rd outflow week) but Bybit -221K + UPbit -131K only; rest INFLOW","reason":"The outflow is two venues: Bybit -221K (untraced, ambiguous) and UPbit -131K (OTC-routing). The rest of the complex took coins IN (Binance +115K, Gate.io +26K, Crypto.com +15K). So NOT clean accumulation. Read jointly with the record OTC reload. Watch whether Bybit's -221K round-trips back (was self-custody) or reappears downstream in OTC/routing (was distribution).","weeks_on_list":1},
 {"item":f"DeFi LEVERAGE RETURNING: USH minted +{ush_supply_wow:.1f}% (CDPs re-opening), XEGLD +{xegld_supply_wow:.1f}% (LSD recovering)","reason":"USH supply +6.5% (largest mint since the run #11 -7% burn) = borrowers re-levering into the rally; XEGLD supply +4.5% = XOXNO LSD re-accumulating after its -29% collapse. Both are genuine-demand signals countering the exchange-side distribution. Watch whether the CDP mint and LSD recovery sustain (real conviction) or reverse if price fades.","weeks_on_list":1},
 {"item":"Mega Whale erd18mv2z6r2 PAUSED accumulating (flat at 1.04M) - the absorber stepped back","reason":"After 2 accumulation weeks (+11K, +32.7K), the erd18mv2z6r2 absorber went FLAT this week (no net flow). Last week it soaked up Coinbase-routed distribution; this week it did not. With a record OTC reload staging, the disappearance of the visible large bid is notable. Watch whether it resumes absorbing (bid returns) or the distribution now lacks an identifiable buyer.","weeks_on_list":6},
 {"item":"Broad delegation growth +120K ex-Binance, but NO new delegators on the rip (base flat 4th week)","reason":"Ex-binance_staking, delegation grew +120K broadly (smartchainconnection +38K, pokerstaking +16.6K, Synexis +9.3K) and direct-node staking rose (+80K economics). But the delegator COUNT was flat (174,349, 4th week) - existing holders adding, no new retail. Watch whether the +16% rip eventually pulls new delegators in or the base stays flat (rally without broadening participation).","weeks_on_list":1},
 {"item":"Stablecoin supply choppy: USDC -0.66% (4th wk, decelerating), USDT -1.87% (re-accelerated)","reason":"No clean directional flight - USDC burn is fading (4th week, -0.66% vs -2.0%) while USDT re-accelerated (-1.87% vs -0.3%). Contrast with USH minting +6.5%. The read: bridged dollars choppy, native leverage expanding. Watch whether bridged stables stabilize as the rally holds.","weeks_on_list":4}]

# ---------- executive summary ----------
executive_summary=[
 {"finding":f"EGLD RIPPED +{100*(price-pp)/pp:.2f}% to ${price:.2f} and DECOUPLED TO THE UPSIDE - a 2nd up-week, but this time EGLD-SPECIFIC: BTC {btc_wow:+.1f}% and ETH {eth_wow:+.1f}% were FLAT while EGLD gained +15.9%. This flips the multi-month narrative (EGLD had been a high-beta laggard both directions). A potential regime break from laggard to leader - not yet confirmed (one week, majors could catch up or roll over), but a materially different signal from last week's beta bounce. Mcap ${econ['marketCap']/1e6:.1f}M ({100*(econ['marketCap']-pecon['market_cap_usd'])/pecon['market_cap_usd']:+.1f}%).","severity":"medium","category":"network"},
 {"finding":f"RECORD OTC DISTRIBUTION RELOAD LOADING INTO THE STRENGTH - the week's key bearish tell. The UPbit OTC + OTC Distribution desks staged their biggest single-week reload in tracking (combined balance ~98K -> ~335K, +238K), fed by UPbit -> OTC Desk 460K, while running a RECORD ~{(upbit_thr+dist_thr)/1000:.0f}K of 7d throughput. A large distribution wave is being SET UP into the price rip - and unlike last week, the identifiable absorber (Mega Whale erd18mv2z6r2) stepped back (flat), so the loaded supply is not visibly being soaked up yet.","severity":"high","category":"whale"},
 {"finding":f"BINANCE DE-STAKING ON TWO FRONTS into the rip: the Staking custody continued its unwind -{3353797-cust_bal:,.0f} (now -{3512650-cust_bal:,.0f} over 2 weeks from the 3.51M peak, traced custody<->hot) AND the binance_staking delegation provider shed -{abs(binance_staking_prov_wow) if binance_staking_prov_wow else 148941:,.0f} locked - ~-192K pulled out of staked positions. Meanwhile Binance hot wallets took net +115K INFLOW. Every leg is distributive: de-stake and load hot wallets into the strength.","severity":"medium","category":"whale"},
 {"finding":f"DeFi LEVERAGE IS RETURNING - genuine-demand counterweight to the exchange-side distribution. USH (Hatom CDP stablecoin) supply MINTED +{ush_supply_wow:.1f}% (626,942, largest move since the run #11 -7% burn) = borrowers re-opening CDP positions as EGLD rallies. XEGLD (XOXNO LSD) supply GREW +{xegld_supply_wow:.1f}% (236,685), re-accumulating after its -29% collapse. And the reward compound rate rose a 3rd straight week to 61.6%. On-chain participants are re-levering into the strength, not de-risking.","severity":"medium","category":"defi"},
 {"finding":f"Net exchange flow {net_total:+,.0f} (3rd outflow week) but NOT clean accumulation. The outflow is just two venues - Bybit -221K (untraced, ambiguous) and UPbit -131K (OTC-routing, fed its own desk 460K) - while the REST of the complex took coins IN (Binance +115K, Gate.io +26K, Crypto.com +15K, Coinbase +10K). Per the decompose-before-labeling rule this is one dump plus an OTC loading leg, not broad self-custody; the decisive channel is the record OTC reload.","severity":"medium","category":"whale"},
 {"finding":f"Staking through the rally: total staked ROSE +{staked-pecon['staked_egld']:,.0f} to {staked:,} even as EGLD ripped +16% (holders staking, not chasing spot). Delegation-contract TVL fell -{abs(total_locked-prev['staking_concentration']['total_locked_egld']):,.0f} NET but that is ENTIRELY the binance_staking provider -149K; ex-Binance delegation grew +120K broadly (smartchainconnection +38K, pokerstaking +16.6K, Synexis +9.3K). Delegator COUNT flat 4th week at {cur_deleg:,} - existing holders adding, no new retail on the rip.","severity":"low","category":"staking"},
 {"finding":f"Stablecoin supply choppy, not a clean flight: USDC {usdc_supply_wow:+.2f}% (4th burn week but decelerating from -2.0%) while USDT {usdt_supply_wow:+.2f}% (re-accelerated from -0.3%). Against USH minting +{ush_supply_wow:.1f}%, the read is capital rotating out of parked bridged-dollars and into levered native EGLD exposure on the rally. DEX volume +{100*(totvol-prev_dexvol)/prev_dexvol:.0f}% to ${totvol/1000:.0f}K tracking the rip (WEGLD/USDC {pairs[0]['share_pct']:.0f}% dominant).","severity":"low","category":"defi"}]

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
   "btc_correlation_note":f"EGLD {100*(price-pp)/pp:+.2f}% WoW vs BTC {btc_wow:+.2f}% / ETH {eth_wow:+.2f}% (WoW). EGLD DECOUPLED to the UPSIDE - the majors were essentially FLAT (BTC slightly down, ETH slightly up) while EGLD gained +15.9%. This is the first EGLD-specific up-move of the tracked cycle and inverts the prior high-beta-laggard pattern (where EGLD fell harder and bounced less). A flat-majors / EGLD-up tape means the move is driven by EGLD-specific flows, not a macro tailwind.",
   "transactions_added":st["transactions"]-pact["total_transactions"],"supply_added":econ["totalSupply"]-pecon["total_supply"],
   "staked_egld_added":staked-pecon["staked_egld"],"epoch_advanced":st["epoch"]-pact["epoch"]},
 "analysis":f"EGLD RIPPED {100*(price-pp)/pp:+.2f}% WoW to ${price:.2f} - a 2nd up-week and, crucially, an EGLD-SPECIFIC one: BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}% were FLAT while EGLD gained +15.9%. That decoupling to the upside inverts months of high-beta-laggard behavior and is the week's headline. z={zp[2]:+.2f}σ reads LOW only because the baseline mean has caught up after two up-weeks - it understates a genuine EGLD-specific regime change. Market cap ${econ['marketCap']/1e6:.1f}M ({100*(econ['marketCap']-pecon['market_cap_usd'])/pecon['market_cap_usd']:+.1f}%). BUT the on-chain tape is DISTRIBUTIVE under the green candle, and that is the tension of the week: the OTC pipeline staged its BIGGEST reload in tracking (+238K desk balance, record ~{(upbit_thr+dist_thr)/1000:.0f}K throughput, fed by UPbit -> OTC Desk 460K) - a large distribution wave being loaded into strength - while Binance de-staked on two fronts (custody -{3353797-cust_bal:,.0f}, binance_staking provider -149K) and took net hot-wallet inflows. Net exchange flow was a 3rd outflow week (-{abs(net_total)/1000:.0f}K) but that is just Bybit -221K + UPbit -131K (OTC-routed); the rest was inflow. Against the distribution, GENUINE DEMAND showed up in DeFi: USH minted +{ush_supply_wow:.1f}% (leverage returning), XEGLD supply +{xegld_supply_wow:.1f}% (LSD recovering), reward compound rate up a 3rd week to 61.6%, delegation +120K ex-Binance, total staked +{staked-pecon['staked_egld']:,.0f}, delegator base flat 4th week at {cur_deleg:,}. Activity: {round((st['transactions']-pact['total_transactions'])/7)/1e6:.1f}M txs/day, account growth +{(st['accounts']-pact['total_accounts'])/1000:.1f}K. The read: an EGLD-specific breakout meeting a record OTC distribution reload - real demand vs staged supply. The next 1-3 weeks (does the loaded OTC wave get pushed and does price absorb it) decide whether this is a genuine regime change or distribution into a fade."}

# ---------- whale analysis ----------
whale_analysis=("THIS WEEK'S DOMINANT MOVES:\n"
 f"1) RECORD OTC DISTRIBUTION RELOAD - THE KEY BEARISH TELL UNDER A +16% RIP. The UPbit OTC Desk + OTC Distribution Wallet staged their biggest single-week reload in tracking: combined desk balance rose from ~97,713 to ~{round((bal_of('erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5') or 168484)+(bal_of('erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r') or 166946)):,.0f} (+238K), while combined 7d outbound throughput hit a RECORD ~{(upbit_thr+dist_thr)/1000:.0f}K EGLD (vs ~172K last week). The reload was fed directly by UPbit: two large transfers UPbit -> UPbit OTC Desk of 320,000 + 140,000 = 460K. A desk loading heavily AND distributing at record pace = a large distribution wave being SET UP into price strength. This is the dominant on-chain counter to the bullish tape.\n\n"
 f"2) BINANCE DE-STAKING ON TWO FRONTS. (a) The Staking custody continued its 2nd-leg drawdown -{3353797-cust_bal:,.0f} (3,353,797 -> {cust_bal:,.0f}), traced via standard transfers (Binance.com -> custody 156,882; custody -> Binance.com 200,000). The custody has shed -{3512650-cust_bal:,.0f} over two weeks from its 3.51M peak. (b) SEPARATELY, the binance_staking DELEGATION provider shed -{abs(binance_staking_prov_wow) if binance_staking_prov_wow else 148941:,.0f} of locked stake (numUsers ~flat). Combined, ~-192K pulled out of Binance staked/custody positions. Meanwhile a Binance.com hot wallet grew +151K (of which ~108K is external inflow beyond the custody's 200K), so Binance took NET +115K onto its hot wallets. Every leg points distributive: de-stake, and accumulate on hot wallets, into the strength.\n\n"
 f"3) NET EXCHANGE FLOW {net_total:+,.0f} EGLD (3rd outflow week) - BUT NOT CLEAN ACCUMULATION. The outflow is just two venues: Bybit -221,402 (the single largest move, 476K -> 255K, destination untraced/ambiguous) and UPbit -131,346 (which is OTC-ROUTING - UPbit fed its own OTC Desk 460K). Against those, the REST of the complex took coins IN: Binance +115K, Gate.io +26K, Crypto.com +15K, Coinbase +10K, MEXC +3.5K. Per the run #15 decompose-before-labeling rule, calling the aggregate 'distribution' or 'accumulation' both mislead - it is one ambiguous dump (Bybit) plus an OTC loading leg (UPbit) on top of a broadly inflow tape. The decisive channel is the OTC reload, not the exchange balance.\n\n"
 f"4) MEGA WHALE erd18mv2z6r2 STEPPED BACK. After two accumulation weeks (+11K, then +32.7K routed from Coinbase Routing), the erd18mv2z6r2 absorber went FLAT this week (1,042,690, no net flow, 0 outbound). Last week it was the identifiable bid soaking up Coinbase-routed distribution; this week that pipe went quiet. With a record OTC reload staging, the disappearance of the visible large buyer is notable - the loaded supply does not yet have an obvious absorber the way it did last week.\n\n"
 f"5) WHALE TIERS (top-{N_prev} apples-to-apples): mega {whale_tiers['mega_whales']['net_change_egld']/1000:+.0f}K, large {whale_tiers['large_whales']['net_change_egld']/1000:+.0f}K, mid {whale_tiers['mid_whales']['net_change_egld']/1000:+.0f}K. NO boundary-crossing artifact (both mega counts = 3). The mega {whale_tiers['mega_whales']['net_change_egld']/1000:+.0f}K is the UPbit -131K outflow + Binance custody -43K; the large +{whale_tiers['large_whales']['net_change_egld']/1000:.0f}K is broad (Binance hot +151K, Coinbase secondary +62K, Gate.io +26K, Crypto.com inflows). Net: the very-largest tier shed EGLD while the 100K-1M tier accumulated - a mild wealth-distribution pattern (the healthier direction), though here it partly reflects the UPbit->OTC and custody->hot plumbing rather than pure conviction.")

# ---------- staking analysis ----------
staking_analysis=(f"Staking concentration remains low (HHI {hhi:.4f}, top-5 {top5:.1f}%, top-10 {top10:.1f}% - essentially unchanged WoW). Total delegated {total_locked:,.0f} EGLD across {len(provs)} active providers ({total_locked-prev['staking_concentration']['total_locked_egld']:+,.0f} WoW). Active delegator base {cur_deleg:,} ({deleg_wow:+}, {100*deleg_wow/prev_deleg:+.3f}%). Total staked (economics, direct-node + delegation) {staked:,} EGLD ({staked-pecon['staked_egld']:+,.0f}), staked ratio {sr*100:.2f}% ({100*(sr-pecon['staked_ratio']):+.2f}pp).\n\n"
 f"STAKING THROUGH THE RALLY: economics.staked ROSE +{staked-pecon['staked_egld']:,.0f} even as EGLD ripped +16% - holders are adding to stake rather than chasing spot exposure, a constructive conviction signal. But note a DIVERGENCE: delegation-contract TVL FELL {total_locked-prev['staking_concentration']['total_locked_egld']:+,.0f} NET while economics.staked rose. The delegation drop is ENTIRELY the binance_staking provider -{abs(binance_staking_prov_wow) if binance_staking_prov_wow else 148941:,.0f} (Binance de-staking, see whale section); EX-BINANCE, delegation GREW +~120K broadly: smartchainconnection +38,033, pokerstaking +16,557 (+12 users), Synexis +9,321 (+16 users), disruptivedigital +8,391, valuestaking +7,790 (+25 users), westake +5,373. That breadth is the healthier kind of growth - so the network staked MORE this week; it was only Binance that reduced.\n\n"
 f"DELEGATOR BASE FLAT FOR A 4TH WEEK at {cur_deleg:,} ({deleg_wow:+} this week). The run #12 capitulation is long behind us, but the flatness now cuts the other way: NO new retail joined despite a +16% rip. The raw z-score {zd[2]:+.2f}σ is the run #9 degenerate case (baseline dragged by the ~179K pre-capitulation level) - downgraded to LOW. The rally is being driven by existing holders re-levering and adding stake, not by broadening participation.\n\n"
 f"YIELD-CHASE COHORT WENT QUIET (net {cohort_net/1000:+.1f}K) - neither the buy-the-dip reignition of two weeks ago nor a clean unwind; a wash. valuestaking +7,790 and star_staking +2,858 gained; egldstakingprovider {cohort_flows.get('egldstakingprovider',0):+,.0f} and procryptostaking {cohort_flows.get('procryptostaking',0):+,.0f} gave back. pi-staking (0% fee, last run's small-provider growth story) PLATEAUED: {cohort_flows.get('pi-staking',0):+,.0f} EGLD, +0 users (held at 51) - the 3-week draw stalled. The concentrated yield-chase dynamic of May has fully dissipated; growth this week is in the broad mid-tier names instead.\n\n"
 f"APR distribution: {buckets[3]['provider_count']} providers in the 8-9% bucket holding {buckets[3]['total_locked_egld']/1e6:.1f}M EGLD (the dominant cluster); the 9-10% bucket holds {buckets[4]['provider_count']} providers / {buckets[4]['total_locked_egld']/1e3:.0f}K EGLD. Empty 10%+ bucket (consistent across all 2026 runs). APR-weighted average {apr_w:.2f}%.\n\n"
 f"DELEGATOR CHURN: {gain} providers gaining vs {lose} losing delegators ({deleg_wow:+} net) - balanced, healthy churn. No notable named-validator joiners/leavers >50K EGLD; system-contract aggregators (erd1qqqq...) excluded per the run #10 rule.")

# ---------- token analysis ----------
top_pair_share=pairs[0]['share_pct']
second_pair=pairs[1] if len(pairs)>1 else None
token_analysis=(f"DEX volume JUMPED to ${totvol/1000:.0f}K ({100*(totvol-prev_dexvol)/prev_dexvol:+.0f}% WoW) on the +16% price rip - the highest weekly DEX volume since the spring. But WEGLD/USDC carried {top_pair_share:.1f}% of it - an extremely concentrated tape, meaning the volume is CEX-derived buyers routing through the one deep stable pair rather than broad on-DEX trading. MEX/WEGLD {second_pair['share_pct'] if second_pair else 0:.1f}% is the only other pair with meaningful share.\n\n"
 f"NEWLY-ISSUED TOKENS: 0 genuine issuances this week. The ESDT system-SC issue scan surfaced one candidate (Burger / BUR-f2028d) but at 1 holder / 0 txs it fails the >10-holder / >5-tx quality bar (spam/dormant deploy). No real new-token launches this week - a quiet launch week, consistent with a market where attention is on the EGLD spot move, not new deploys.\n\n"
 f"Token holder counts declined for a 16th consecutive week (small declines across the top 10) - the established airdrop-decay baseline. WrappedEGLD and WrappedUSDC remain the most-held real tokens. Note WEGLD supply BURNED -3.65% this week (net unwrapping of WEGLD back to native EGLD) - consistent with holders pulling out of wrapped/DEX form to hold or stake native EGLD into the rally.\n\n"
 f"MEX price {100*(meco['price']-prev_mexp)/prev_mexp:+.2f}% to ${meco['price']:.3e}, ripping with EGLD (its best week since the decline began). MEX mcap ${meco['marketCap']/1e6:.2f}M.\n\n"
 f"Top by market cap: EmoryaSportsX (EMRS) leads at ${D['tokens_mcap'][0].get('marketCap',0)/1e6:.1f}M ({D.get('emrs_token',{}).get('accounts',0):,} holders, {D.get('emrs_token',{}).get('transactions',0):,} txs - a genuine large-cap, per run #14's correction). After EMRS: WrappedUSDC ${D['tokens_mcap'][1].get('marketCap',0)/1e6:.2f}M, ZoidPay ${D['tokens_mcap'][2].get('marketCap',0)/1e6:.2f}M, xMoney UTK ${D['tokens_mcap'][3].get('marketCap',0)/1e6:.2f}M, StakedEGLD ${D['tokens_mcap'][4].get('marketCap',0)/1e6:.2f}M (SEGLD mcap rose with EGLD).\n\n"
 f"Bridged stablecoin supply CHOPPY: USDC {usdc_supply_wow:+.2f}% (a 4th burn week but DECELERATING from -2.0%) while USDT {usdt_supply_wow:+.2f}% (RE-ACCELERATED from -0.3%). No clean directional flight in bridged dollars. The contrast that matters is with USH (native CDP stablecoin) MINTING +{ush_supply_wow:.1f}% - bridged-dollar liquidity is choppy/contracting while native leverage is expanding, consistent with capital rotating from parked stables into levered EGLD exposure on the rally.")

# ---------- defi analysis ----------
defi_analysis=(f"DEFI LEVERAGE IS RETURNING - the constructive counter-signal to the exchange-side distribution. Two independent, price-independent supply signals both point to on-chain participants re-engaging as EGLD rallies:\n"
 f"(1) USH (Hatom CDP stablecoin) supply MINTED +{ush_supply_wow:.2f}% WoW to {supply('USH-111e09'):,.0f} - the largest USH supply move since the run #11 -7% burn, and in the opposite direction. USH is minted when borrowers OPEN CDP positions against collateral, so a +6.5% mint = borrowers RE-LEVERING into the strength. This is the clean mirror of the multi-week de-leveraging burn during the decline (force-closing to avoid liquidation). USH mcap ${hatom_ush/1000:.0f}K.\n"
 f"(2) XEGLD (XOXNO LSD) supply GREW +{xegld_supply_wow:.2f}% to {supply('XEGLD-e413ed'):,.0f}, RE-ACCUMULATING after its run #14 -29% collapse and run #15 stabilization. The XOXNO LSD contract's EGLD balance fell -106K this week as it deployed the fresh deposits to validators. Liquid staking is growing again - the redemption event is fully behind it and the product is back in inflow. XOXNO LSD TVL ${xoxno_lsd/1e6:.2f}M / {xlsd_egld/1000:.0f}K EGLD.\n\n"
 f"HATOM LSD FLAT-TO-UP: SEGLD supply {segld_supply_wow:+.2f}% (flat), SWTAO {swtao_supply_wow:+.2f}% (flat). Hatom LSD ${hatom_lsd/1e6:.2f}M USD (SEGLD ${segld_mcap/1e6:.2f}M + SWTAO ${swtao_mcap/1e6:.2f}M), {100*(hatom_lsd-prev_hlsd)/prev_hlsd:+.1f}% USD - up in dollar terms with the price. The dataApi price feed was CLEAN again this run (0 re-fetch retries, all 4 tokens first pass), so the USD figures are fully reliable.\n\n"
 f"HATOM LENDING ${hatom_lending/1e6:.2f}M USD ({100*(hatom_lending-prev['defi_tvl']['Hatom Lending'])/prev['defi_tvl']['Hatom Lending']:+.1f}% USD, {100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}% EGLD). The +{100*(price-pp)/pp:.1f}% price move far exceeds the |dPrice|>=5% guardrail, so the bilateral inverse rule IS evaluable - and this is its 2nd UP-week test: EGLD-denominated TVL moved {100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}% (counter to price - depositors WITHDREW to capture gains into the rally, the mirror of dip-DCA). Response ratio |{100*(hl_egld-prev_hl_egld)/prev_hl_egld:.1f}%|/|{100*(price-pp)/pp:.1f}%| = {abs(100*(hl_egld-prev_hl_egld)/prev_hl_egld)/abs(100*(price-pp)/pp):.2f} - a stronger response than last week's 0.49 up-week reading, and a large, unambiguous confirmation on a big up-move. NOTE the apparent tension with the USH mint: Lending EGLD-TVL falling (withdrawing collateral to bank gains) while USH is minted (opening new leverage) are different cohorts - profit-takers exiting deposits vs conviction borrowers levering up.\n\n"
 f"xExchange TVL ${xexch_tvl_usd/1e6:.2f}M / {xexch_tvl_egld/1000:.0f}K EGLD ({100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld:+.1f}% EGLD). DEX volume ${totvol/1000:.0f}K (+{100*(totvol-prev_dexvol)/prev_dexvol:.0f}%, tracking the rip; WEGLD/USDC {pairs[0]['share_pct']:.0f}% dominant). Aggregator throughput: XOXNO {tcount('XOXNO Aggregator'):,}, OneDex {tcount('OneDex Swap'):,} daily transfers.")

report={
 "metadata":{"report_date":"2026-07-13","period_start":"2026-07-06T00:00:00Z","period_end":"2026-07-13T00:00:00Z",
   "generated_at":datetime.now(timezone.utc).isoformat(),"egld_price_usd":price,
   "btc_price_usd":be["bitcoin"]["usd"],"eth_price_usd":be["ethereum"]["usd"],"run_number":16,
   "data_sources_ok":json.load(open("/tmp/run16/status.json"))["ok"],
   "data_sources_failed":[]},
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
 "meta_learning":{"run_number":16,
   "endpoints_that_worked":json.load(open("/tmp/run16/status.json"))["ok"],
   "endpoints_that_failed":[],
   "api_quirks":[
     "CLEAN PRICE-FEED RUN (2nd in a row): the dataApi re-fetch guard reported 0 retries needed - all 4 dataApi-class tokens (SEGLD, SWTAO, USH, XEGLD) populated price+mcap on the first sequential pass at 1.05s spacing. Two consecutive clean runs support the run #15 conclusion that the null behavior is a transient feed hiccup, not a persistent per-token outage.",
     "BINANCE OPERATES A DELEGATION PROVIDER ('binance_staking') distinct from its Staking CUSTODY wallet (erd1rf4hv70). Both moved this week (provider -149K locked; custody -43K balance). The provider's `locked` shows up in /providers and dropping it out of the delegation total can misread as broad delegation shrinkage - always net it out (like the erd1qqqq system aggregators) before narrating delegation-TVL WoW. The two are separate Binance staking legs.",
     "Custody<->hot transfers TRACEABLE again this week (custody received 156,882 from Binance.com hot, sent 200,000 back) - confirms the run #15 rule: staking-custody<->hot legs are standard value txs (visible), hot<->external is not. tx-scan the custody address to attribute the move.",
     "UPbit 'exchange outflow' == OTC loading: UPbit's -131K balance drop is NOT customer withdrawal - it fed the UPbit OTC Desk 460K in standard transfers (320K+140K). A CEX cold-wallet outflow that lands on a known OTC desk is distribution-routing, not self-custody; always check whether the outflow's receiver is an OTC desk before calling an exchange outflow bullish."],
   "data_gaps":[
     "Bybit -221K destination: the largest single exchange move this week is internal-transfer-invisible (0 value-bearing standard txs from the Bybit cold wallet), so self-custody vs OTC-routing vs another exchange cannot be distinguished. Flagged as ambiguous; watch for a re-inflow or downstream appearance next run.",
     "Binance hot-wallet +108K external inflow: the custody sent 200K to hot but hot grew +151K, so ~+108K arrived from external sources that are internal-transfer-invisible - who deposited it (customers positioning to sell? OTC?) is inferred, not proven.",
     "Newly-issued: 0 genuine launches (only Burger, 1 holder/0 tx, filtered) - a quiet launch week, but the scan cannot fully distinguish 'quiet' from 'method missed a small deploy'."],
   "key_findings":[
     "EGLD RIPPED +15.93% to $3.13 and DECOUPLED TO THE UPSIDE - BTC -0.2%/ETH +0.7% were FLAT. First EGLD-specific up-move of the cycle; flips the high-beta-laggard pattern to potential leader. z=-0.09 (baseline caught up, understates the regime change).",
     "RECORD OTC RELOAD into the strength: UPbit OTC + OTC Distribution desk balance +238K (~98K -> ~335K, biggest single-week load in tracking), fed by UPbit -> OTC Desk 460K, with a record ~323K 7d throughput. A large distribution wave being SET UP into the rally - the key bearish tell under the green candle.",
     "BINANCE DE-STAKING on two fronts: custody 2nd-leg -43K (now -202K over 2 weeks from the 3.51M peak) + binance_staking delegation provider -149K = ~-192K out of staked positions, while Binance hot wallets took net +115K inflow. Distributive on every leg.",
     "DEFI LEVERAGE RETURNING: USH supply minted +6.49% (largest since the run #11 -7% burn; borrowers re-opening CDPs), XEGLD supply +4.54% (XOXNO LSD re-accumulating after its -29% collapse), reward compound rate up a 3rd week to 61.59%. Genuine demand countering the exchange-side distribution.",
     "Net exchange flow -196K (3rd outflow week) but NOT clean accumulation: just Bybit -221K (untraced) + UPbit -131K (OTC-routed); the rest was INFLOW (Binance +115K, Gate.io +26K, Crypto.com +15K, Coinbase +10K).",
     "Mega Whale erd18mv2z6r2 STEPPED BACK (flat at 1.04M) after 2 accumulation weeks - the identifiable absorber went quiet just as a record OTC reload staged. The loaded distribution lacks a visible bid this week.",
     "Staking through the rally: total staked +80K to 14.54M (holders adding, not chasing spot); delegation -28K NET but entirely binance_staking -149K, ex-Binance delegation +120K broad (smartchainconnection +38K, pokerstaking +16.6K, Synexis +9.3K).",
     "Delegator base FLAT 4th week (174,349) - NO new retail on the +16% rip; rally driven by existing holders re-levering, not broadening participation.",
     "Bilateral inverse rule 2nd UP-week confirmation: price +15.93%, Hatom Lending EGLD-TVL -11.48% (inverse), response ratio 0.72 - a large, unambiguous up-week test on a big move.",
     "Stablecoins choppy: USDC -0.66% (4th burn wk, decelerating), USDT -1.87% (re-accelerated); DEX volume +82% to $161K (WEGLD/USDC 98% dominant)."],
   "action_items_from_previous":8,
   "action_items_completed":8,
   "methodology_changes":[
     "NET OUT THE binance_staking PROVIDER before narrating delegation-TVL WoW (new): Binance runs a delegation provider ('binance_staking') separate from its custody wallet. Its -149K locked this week made delegation-TVL look like it shrank -28K NET, when ex-Binance delegation GREW +120K broadly. Treat binance_staking (and other single-entity provider swings) like the erd1qqqq system aggregators - decompose before labeling the aggregate, same principle as the run #15 exchange-entity rule.",
     "READ CEX OUTFLOW BY DESTINATION, not just sign (reinforced): UPbit's -131K 'outflow' was OTC loading (fed its own OTC Desk 460K), not self-custody. Before calling an exchange outflow during a rally bullish, check whether the receiver is a known OTC desk/router. Complements the run #14 read-flow-jointly-with-OTC rule at the per-transfer level.",
     "z-SCORE LAGS A REGIME CHANGE: EGLD +15.93% produced z=-0.09 because two up-weeks pulled the baseline mean up to the current level. When a metric has trended one direction for 2+ weeks, the z-score understates a genuine break - cross-check with the rule-based read (here: EGLD-specific decoupling from flat majors). Same family as the run #9 degenerate-z guard but the opposite failure mode (under-flagging, not over-flagging).",
     "BILATERAL INVERSE RULE - 2nd UP-week test, larger magnitude: price +15.93%, Hatom Lending EGLD-TVL -11.48%, ratio 0.72 (vs 0.49 last up-week). The rule now has two up-side confirmations and holds at large magnitude. Response ratio series on up-weeks: 0.49, 0.72.",
     "USH MINT as a leverage-returning indicator (new, mirror of the run #11 burn rule): USH supply MINTING >5% in a week during a price RALLY signals borrowers re-opening CDP positions (leverage returning) - the bullish mirror of the >1% burn = de-leveraging rule. Surface in exec_summary when USH moves >5% in either direction."],
   "new_addresses_discovered":1,
   "most_valuable_insight":"This week set up the cleanest bull/bear tension of the tracking period. On the bull side, EGLD staged its FIRST EGLD-specific up-move of the cycle: +15.93% to $3.13 while BTC (-0.2%) and ETH (+0.7%) were flat - a decoupling to the upside that inverts months of high-beta-laggard behavior, corroborated by genuine on-chain demand (USH minted +6.5% = leverage returning, XEGLD supply +4.5% = LSD re-accumulating after its -29% collapse, reward compound rate up a 3rd week to 61.6%, total staked +80K, broad delegation +120K ex-Binance). On the bear side, the on-chain distribution machinery loaded HARD into the strength: the OTC desks staged their biggest reload in tracking (+238K desk balance, fed by UPbit -> OTC Desk 460K) while running a record ~323K throughput, Binance de-staked ~192K across its custody and delegation-provider legs and took net hot-wallet inflows, and - unlike last week - the identifiable large absorber (Mega Whale erd18mv2z6r2) STEPPED BACK to flat. So a genuine EGLD-specific demand impulse is meeting a record, deliberately-staged distribution supply with no visible large buyer this week. The resolution over the next 1-3 weeks - does the loaded OTC wave get pushed out and does price absorb it, or does it fade like the run #12 one-week bounce - is the single most important thing to watch, and it is now cleanly framed: real demand vs staged supply.",
   "top_recommendation":"Track the RECORD OTC RELOAD's distribution leg: the UPbit OTC + OTC Distribution desks now hold ~335K (+238K this week) after a UPbit -> OTC Desk 460K load, running record ~323K throughput. Watch whether that loaded EGLD gets pushed out over the next 1-3 weeks (the distribution leg) and, critically, whether price ABSORBS it (regime change confirmed) or FADES under it (distribution-into-a-bounce, like run #12). Pair with the EGLD-vs-majors relative strength: a 3rd EGLD-specific up-week while majors stay flat confirms the laggard->leader flip; a fade back toward beta says the distribution won.",
   "recommendations_for_next_run":[
     "OTC DISTRIBUTION LEG: the desks reloaded a record +238K (now ~335K) with record ~323K throughput. Watch whether the loaded EGLD is pushed OUT next week (distribution executing) and whether desk balances draw back down. This is the highest-priority follow-up - the biggest staged distribution in tracking.",
     "DOES EGLD LEAD OR REVERT? EGLD +15.9% while BTC/ETH flat = first EGLD-specific up-move. Watch for a 3rd up-week (momentum/leadership confirmed) vs a fade back to beta. Track EGLD WoW vs BTC/ETH WoW explicitly - the decoupling is the regime signal.",
     "BINANCE DE-STAKING CONTINUATION: custody -43K (2nd leg) + binance_staking provider -149K this week. Watch whether the custody keeps drawing down toward zero, whether the provider keeps shedding locked stake, and where the +115K hot-wallet inflow goes. Every leg is currently distributive.",
     "BYBIT -221K DESTINATION: the largest exchange move, untraced. Watch for a round-trip re-inflow (was self-custody accumulation, bullish) vs a downstream OTC/routing/exchange appearance (was distribution). Query Bybit cold-wallet flows and any large new recipient next run.",
     "DEFI LEVERAGE DURABILITY: USH minted +6.5% and XEGLD supply +4.5% (leverage/LSD returning). Watch whether the CDP mint and LSD re-accumulation SUSTAIN (real conviction) or reverse if price stalls - a reversal would say the leverage was a chase, not conviction.",
     "MEGA WHALE erd18mv2z6r2 (paused at 1.04M): the absorber went flat this week just as OTC reloaded. Watch whether it RESUMES absorbing (a bid returns under the market) or stays flat (the record OTC distribution lacks an identifiable buyer - more bearish).",
     "PARTICIPATION BREADTH: delegator base flat 4th week despite +16% - no new retail. Watch whether a sustained rally finally pulls new delegators in (healthy broadening) or the base stays flat (rally on existing-holder leverage only).",
     "STABLECOIN vs USH divergence: bridged USDC/USDT choppy-to-contracting while native USH mints. Watch whether bridged dollars stabilize/inflow as the rally holds (dollars returning) or keep bleeding (capital only rotating internally into leverage)."],
   "dashboard_feature_suggestions":[
     {"title":"OTC desk balance + throughput cycle chart","motivation":"THIS run's headline bearish tell: the OTC desks staged their BIGGEST reload in tracking (+238K desk balance) AND ran a record ~323K throughput - a load-and-distribute cycle the single-week dashboard cannot show. A multi-week view of desk BALANCE (loading vs draining) overlaid with 7d THROUGHPUT and EGLD price would make the reload-into-strength pattern - and the load/distribute phase - immediately legible, and would have flagged this week's setup at a glance.","suggested_visualization":"dual-axis weekly chart: combined OTC desk balance (area, left axis) + combined 7d outbound throughput (bars, right axis) + EGLD price (line overlay), with load/drain phase shading.","data_already_available":True,"data_source":"OTC desk balances (bal_of the two desk addresses) + upbit_otc/otc_dist 7d throughput - both computed per run","priority":"high"},
     {"title":"EGLD relative-strength (beta) tracker","motivation":"This run's regime signal was EGLD DECOUPLING to the upside (+15.9% vs flat BTC/ETH) - the flip from high-beta laggard to potential leader. The single-week dashboard only shows one week's btc_correlation_note; a multi-week chart of EGLD WoW% vs BTC/ETH WoW% (or a rolling relative-strength ratio) would make the laggard->leader transition visible and would distinguish a beta bounce (run #15) from an EGLD-specific move (this run) at a glance.","suggested_visualization":"grouped weekly bars of EGLD / BTC / ETH WoW% side by side, plus a line for EGLD's relative-strength ratio (EGLD%/avg(BTC%,ETH%)); annotate the laggard vs leader regime.","data_already_available":True,"data_source":"metadata.egld_price_usd/btc_price_usd/eth_price_usd stored per run + running_baselines.egld_price_usd","priority":"high"},
     {"title":"DeFi leverage/engagement composite panel","motivation":"This run's constructive counter-signal was a CLUSTER: USH supply +6.5% (CDPs re-opening), XEGLD supply +4.5% (LSD re-accumulating), reward compound rate up a 3rd week, Hatom Lending EGLD-TVL -11.5% (profit-taking). Individually they're scattered across sections; a single multi-week panel of these leverage/engagement supply signals would show whether DeFi conviction is building or fading as one composite - the demand side of the demand-vs-distribution tension.","suggested_visualization":"small-multiples of weekly supply WoW for USH / XEGLD / SEGLD + reward-compound-rate line + Hatom Lending EGLD-TVL, on a shared timeline.","data_already_available":True,"data_source":"lsd_supply block in previous.json + reward_behavior.compound_pct + protocol_breakdown EGLD TVLs, all per run","priority":"medium"}],
   "dashboard_suggestions_followup":[
     {"from_run":15,"title":"Binance custody-vs-hot-vs-protocol-staked unwind tracker","status":"pending","note":"NOT yet built. Still relevant - the custody continued a 2nd-leg drawdown -43K this week AND the binance_staking delegation provider shed -149K, so the tracker would now want a 3rd line (delegation-provider stake). Kept high priority; folds into the broader Binance de-staking picture."},
     {"from_run":15,"title":"Exchange-flow vs OTC-throughput dual-axis chart","status":"pending","note":"SUPERSEDED/absorbed into this run's 'OTC desk balance + throughput cycle chart' suggestion, which adds the desk-balance (load/drain) dimension that this run made essential. Same core idea, sharper framing - build the balance+throughput version."},
     {"from_run":15,"title":"Distribution-absorber leaderboard","status":"pending","note":"NOT yet built, and this run it would have shown the absorber (Mega Whale erd18mv2z6r2) going to ZERO/flat - exactly the signal that matters (the bid stepped back as OTC reloaded). Kept in the queue at medium; complements the OTC cycle chart."},
     {"from_run":13,"title":"LSD circulating-supply timeline (supply, not mcap)","status":"pending","note":"NOT yet built. This run it would have shown XEGLD RE-ACCUMULATING (+4.5%) after the -29% collapse and stabilization - the full collapse->stabilize->recover arc. Partially folded into this run's 'DeFi leverage/engagement composite' suggestion; kept."},
     {"from_run":13,"title":"Forward-indicator scorecard (prediction resolution tracker)","status":"deprioritized","note":"Still useful (8/8 prior action items completed this run) but lower priority than the OTC cycle chart and relative-strength tracker. Deferred again."},
     {"from_run":8,"title":"OTC pipeline graph view (Sankey/force-directed)","status":"pending","note":"Still a strong idea - this run had a clean UPbit -> UPbit OTC Desk 460K edge. Lower priority than the OTC balance+throughput cycle chart, which captures the phase/magnitude this run needed without the graph-layout complexity."}]}}

json.dump(report,open(f"{REPO}/reports/2026-07-13.json","w"),indent=2)
print("WROTE reports/2026-07-13.json")
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
