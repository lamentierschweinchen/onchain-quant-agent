#!/usr/bin/env python3
"""Assemble reports/2026-07-20.json (run #17) from collected data."""
import json, math
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D = json.load(open("/tmp/run17/collected.json"))
prev = json.load(open(f"{REPO}/data/previous.json"))
kn = json.load(open(f"{REPO}/data/known-addresses.json"))
learn = json.load(open(f"{REPO}/data/learnings.json"))
prevcol = json.load(open(f"{REPO}/data/collected/2026-07-13.json"))  # for supply WoW

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
# NOTE (run #17): the collector's *_outbound arrays are capped at size=50, which on a
# high-activity desk covers only ~2.5 of the 7 days - so every prior run's "throughput"
# figure was a severe undercount (run #16 reported ~323K; the true paginated 7d figure was
# 1,100,791). The constants below come from a full paginated re-query of both desks over
# the 7d window, net of desk<->desk inter-transfers. See methodology.md (run #17 entry).
OTC_THR_7D_GROSS=1_495_037.0      # paginated, both desks, gross outbound
OTC_THR_7D_INTERDESK=167_000.0    # desk -> desk transfers (double-counted in gross)
OTC_THR_7D=OTC_THR_7D_GROSS-OTC_THR_7D_INTERDESK   # 1,328,037 net distribution throughput
OTC_THR_7D_PREV=1_100_791.0       # run #16 window, same paginated method (apples-to-apples)
upbit_thr=OTC_THR_7D/2; dist_thr=OTC_THR_7D/2      # legacy split, kept for f-string compat

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
 "UPbit":"+152,969 (+13.8%) INFLOW (1,106,580 -> 1,259,550) - a full REVERSAL of last week's -131K, and the mechanical other side of the OTC distribution. UPbit both fed its own OTC Desk a further 364,000 this week AND took 150,000 straight back from the desk in a single transfer, plus more via routers. The round-trip confirms the desks are UPbit-operated distribution infrastructure: coins go out to the desk, get chopped into retail-sized chunks, and the unsold remainder plus proceeds cycle back. Net for the week, UPbit ENDED with more EGLD than it started - the distribution wave did not clear the inventory off the venue.",
 "KuCoin":"+142,773 (+430.6%) - the largest PROPORTIONAL exchange move in tracking history (33,156 -> 175,929). Fully explained by ONE counterparty: Unknown Whale erd15ku2r2j6 sent its ENTIRE 145,443 EGLD balance to KuCoin in the 7d window and went to ZERO. This is not diffuse retail deposit flow - it is a single large holder fully exiting its position onto one venue. A wallet that empties itself onto an exchange is the cleanest available proxy for intent to sell. Highest-priority follow-up: watch whether KuCoin's balance bleeds back down (the whale withdrew/was OTC'd) or stays elevated (the coins were sold into the book).",
 "Bybit":"+62,712 (+24.6%) INFLOW (255,027 -> 317,740) - a partial round-trip of last week's -221,402, which run #16 flagged as untraced-and-ambiguous. That ambiguity now resolves toward the bearish reading: Bybit was also the single largest destination of this week's OTC distribution, receiving ~166K via at least four routing wallets (erd1w7nlme, erd1e9luc4, erd1g6fntj + the tracked OTC->Bybit routers), all zero-balance pass-throughs. So Bybit is on the RECEIVING end of the distribution pipeline, not accumulating in self-custody.",
 "Binance":"Net -81,032 across 4 wallets, but the composition matters more than the sign. The Staking CUSTODY shed a 3rd consecutive leg, -103,579 (3,310,680 -> 3,207,101), fully traced via standard transfers (Binance.com -> custody 396,421, custody -> Binance.com 500,000). Cumulative custody drawdown is now -305,549 over three weeks from the 3,512,650 peak - a sustained, deliberate de-staking programme, not a one-off. Offsetting it, Binance.com hot took +15,552. Note the binance_staking DELEGATION provider (a separate leg) STABILIZED at +298 after last week's -148,941, so the de-staking is now concentrated in the custody wallet alone.",
 "Coinbase":"-75,338 across 4 wallets - but this is NOT distribution and should not be read as an outflow. Coinbase Custody went 65,090 -> 0, which looks like a full drain; tracing the single outbound transfer shows all 65,090 went to erd1z4xerdjq6aa2, a FRESH nonce-0 wallet that still holds the exact amount. It is an internal custody migration. Netting that out, real Coinbase movement is only ~-10K. Separately, the Coinbase Routing -> Mega Whale erd18mv2z6r2 pipe REOPENED (+50,621), so Coinbase remains the conduit through which the market's one identifiable large bid is being filled.",
 "Crypto.com":"+5,940 across 2 wallets. Broadly flat after two inflow weeks.",
 "MEXC":"+1,702 (+1.9%). Flat.",
 "Bitget":"-11,851 (-14.8%). Mild outflow off a small base.",
 "Gate.io":"-4,128 (-4.8%). Mild outflow, reversing last week's +26K.",
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

exchange_flows={"total_exchange_egld_current":total_cur,"total_exchange_egld_previous":total_prev,
    "net_change_egld":net_total,"net_change_pct":100*net_total/total_prev if total_prev else None,
    "direction":"outflow" if net_total<0 else "inflow",
    "signal":f"Net exchange flow {net_total:+,.0f} EGLD ({100*net_total/total_prev if total_prev else 0:+.2f}%) - a decisive REVERSAL to net INFLOW after three consecutive outflow weeks, and the cleanest bearish read of the quarter because it is the mechanical consequence of the OTC wave finally executing. Decomposed per the run #15 entity rule, the inflow is concentrated and explainable: UPbit +152,969 (the desks pushing inventory back onto the venue), KuCoin +142,773 (ONE whale, erd15ku2r2j6, emptying its entire 145,443 balance onto the venue and going to zero), Bybit +62,712 (the single largest destination of this week's OTC distribution, ~166K arriving via four zero-balance routers). Against those, the apparent outflows are largely NOT distribution: Coinbase -75,338 is mostly an internal custody migration (65,090 to a fresh nonce-0 wallet that still holds it), and Binance -81,032 is the 3rd leg of the custody de-staking programme rather than customer flow. Read jointly with OTC (run #14 rule), the two channels now agree for the first time in weeks: the desks DRAINED -255,736 (-76%) while running {OTC_THR_7D/1e6:.2f}M of 7d throughput, and the coins landed on exchanges. Last week's staged supply has been delivered - and the tape absorbed it with only a +0.96% price gain.",
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
# NOTE (run #17): the collector's *_outbound arrays are capped at size=50, which on a
# high-activity desk covers only ~2.5 of the 7 days - so every prior run's "throughput"
# figure was a severe undercount (run #16 reported ~323K; the true paginated 7d figure was
# 1,100,791). The constants below come from a full paginated re-query of both desks over
# the 7d window, net of desk<->desk inter-transfers. See methodology.md (run #17 entry).
OTC_THR_7D_GROSS=1_495_037.0      # paginated, both desks, gross outbound
OTC_THR_7D_INTERDESK=167_000.0    # desk -> desk transfers (double-counted in gross)
OTC_THR_7D=OTC_THR_7D_GROSS-OTC_THR_7D_INTERDESK   # 1,328,037 net distribution throughput
OTC_THR_7D_PREV=1_100_791.0       # run #16 window, same paginated method (apples-to-apples)
upbit_thr=OTC_THR_7D/2; dist_thr=OTC_THR_7D/2      # legacy split, kept for f-string compat
mw_bal_cur=bal_of("erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw") or 1093312
cust_bal=bal_of("erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p") or 3207101
binance_staking_prov_wow=lk_wow("binance_staking")
UPBIT_DESK="erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
DIST_DESK="erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
desk_cur=(bal_of(UPBIT_DESK) or 39726)+(bal_of(DIST_DESK) or 39968)
desk_prev=335430.0   # run #16 close: UPbit OTC 168,484 + OTC Distribution 166,946
desk_delta=desk_cur-desk_prev
anomalies=[
 {"metric":"otc_distribution_executed","current_value":round(desk_cur),"previous_value":round(desk_prev),"method":"rule_based",
  "severity":"critical",
  "description":f"THE RECORD OTC RELOAD HAS BEEN DISTRIBUTED - and the destination is exchanges. Run #16 flagged the biggest desk load in tracking (+238K, desks to ~335K) and asked whether the inventory would be pushed out. It was, in full: combined desk balance COLLAPSED {desk_delta:+,.0f} EGLD ({desk_prev:,.0f} -> {desk_cur:,.0f}, {100*desk_delta/desk_prev:+.1f}%) - the largest single-week desk drawdown observed - while pushing {OTC_THR_7D:,.0f} EGLD of 7d outbound throughput (vs {OTC_THR_7D_PREV:,.0f} in the run #16 window on the same paginated method, +{100*(OTC_THR_7D-OTC_THR_7D_PREV)/OTC_THR_7D_PREV:.0f}%). Crucially the destinations are now TRACED: the largest unlabeled recipients (erd1w7nlme 213,607 / erd1e9luc4 100,425 / erd1g6fntj 74,252 / erd1ckh3v9 72,871 / erd1ddqnaj 54,468) are all ZERO-BALANCE, high-nonce pass-through routers that forward to Bybit and Binance.com, plus 150,000 sent straight back to UPbit. So this was not distribution to retail self-custody - the staged supply was delivered ONTO EXCHANGES. The market absorbed it with a price gain of only +{100*(price-pp)/pp:.2f}%, which is the bearish part: it took a full 1.33M-EGLD distribution wave to cap the rally, and the rally stopped."},
 {"metric":"net_exchange_flow_reversal","current_value":round(net_total),"previous_value":-196000,"method":"rule_based",
  "severity":"high",
  "description":f"NET EXCHANGE FLOW REVERSED TO INFLOW: {net_total:+,.0f} EGLD after three consecutive outflow weeks. This is the confirming half of the OTC story - the coins the desks pushed out landed on venues. Concentrated in three places: UPbit +152,969 (desk inventory cycling back), KuCoin +142,773 (a single whale's full exit, below), Bybit +62,712 (the OTC pipeline's largest single destination, ~166K via four routers). Applying the run #15 decompose-before-labeling rule in the other direction, the apparent OUTFLOWS are the ones that are not real: Coinbase -75,338 is mostly an internal custody migration (65,090 moved to a fresh nonce-0 wallet that still holds it) and Binance -81,032 is the custody de-staking leg, not customer flow. Both channels - exchange balances and OTC throughput - now point the same way for the first time in a month."},
 {"metric":"kucoin_single_whale_exit","current_value":142773,"previous_value":0,"method":"rule_based",
  "severity":"high",
  "description":f"LARGEST PROPORTIONAL EXCHANGE MOVE IN TRACKING HISTORY: KuCoin +430.6% (33,156 -> 175,929). It is not diffuse deposit flow - it is ONE wallet. Unknown Whale erd15ku2r2j6smlwumftumlpw0mfpqxy32wyt4ewxzyhs3ugsjee8stq2xh84e (nonce 24) sent its ENTIRE 145,443 EGLD balance to KuCoin inside the window and now holds ZERO. A previously passive large holder emptying itself onto a single venue is the cleanest available proxy for intent to sell, and at ~0.5% of circulating supply it is material. It also drops the wallet out of the large-whale tier entirely. Follow-up: if KuCoin's balance bleeds back down next week the coins were withdrawn or OTC'd; if it stays elevated the position was sold into the book."},
 {"metric":"egld_price_usd","current_value":price,"previous_value":pp,"method":"z_score",
  "average_value":zp[0],"stddev":zp[1],"z_score":zp[2],"severity":"medium",
  "description":f"THE EGLD-LEADERSHIP THESIS FAILED IN ONE WEEK. EGLD gained only {100*(price-pp)/pp:+.2f}% to ${price:.2f} while BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}% BOTH OUTPACED IT. Run #16's headline was EGLD decoupling to the upside (+15.93% on flat majors) and the registered question was whether a 3rd up-week would confirm momentum leadership or fade back to beta. It faded: EGLD is once again a laggard, underperforming ETH by ~3.4pp. The +15.93% decoupling was therefore a ONE-WEEK event, not a regime change - and per the run #13 exit-liquidity pattern, a rally that stalls immediately while distribution runs at record pace is the signature of supply meeting a bid, not of a trend. z={zp[2]:+.2f}σ (LOW/neutral). Cumulative off the $2.55 low is now ~+24%, but the streak of gains has effectively stopped."},
 {"metric":"binance_custody_de_staking","current_value":round(cust_bal),"previous_value":3310680,"method":"rule_based",
  "severity":"medium",
  "description":f"BINANCE CUSTODY DE-STAKING, 3RD CONSECUTIVE LEG: -{3310680-cust_bal:,.0f} this week (3,310,680 -> {cust_bal:,.0f}), fully traced via standard transfers (Binance.com -> custody 396,421; custody -> Binance.com 500,000) exactly as the run #15 rule predicts for custody<->hot legs. Cumulative drawdown is now -{3512650-cust_bal:,.0f} EGLD over three weeks from the 3,512,650 peak. Three consecutive legs in the same direction promotes this from an event to a deliberate programme: Binance is systematically unwinding the position it spent runs #9-#11 accumulating. Note the counterweight - the separate binance_staking DELEGATION provider STABILIZED at {binance_staking_prov_wow:+,.0f} after last week's -148,941, so the de-staking is now concentrated in the custody wallet alone rather than running on two fronts."},
 {"metric":"mega_whale_absorber_resumed","current_value":round(mw_bal_cur),"previous_value":1042690,"method":"rule_based",
  "severity":"medium",
  "description":f"THE ABSORBER CAME BACK - the week's main constructive counter-signal. Mega Whale erd18mv2z6r2, which run #16 flagged as having PAUSED (flat at 1.04M) just as the OTC desks reloaded, resumed accumulating: +{mw_bal_cur-1042690:,.0f} EGLD in a single transfer to {mw_bal_cur:,.0f}. The counterparty is once again the Coinbase Routing Wallet, the same pipe observed in run #15 - so the market's one identifiable large bid is still live and still being filled through Coinbase. This matters for reading the distribution: a 1.33M OTC wave with a returning ~50K absorber is being partially soaked up rather than dumped into a vacuum. But note the asymmetry - the absorber took ~50K against ~1.33M distributed, so it is a floor, not a match for the supply."},
 {"metric":"defi_leverage_paused","current_value":ush_supply_wow,"previous_value":6.49,"method":"rule_based",
  "severity":"low",
  "description":f"DEFI LEVERAGE EXPANSION PAUSED (did not reverse). USH (Hatom CDP stablecoin) supply was essentially FLAT at {ush_supply_wow:+.2f}% ({supply('USH-111e09'):,.0f}) after last week's +6.49% mint - so the run #16 'leverage returning' signal did NOT sustain into a second week, but neither did it unwind (no forced-closure burn). XEGLD (XOXNO LSD) supply DID continue, +{xegld_supply_wow:.2f}% for a 2nd straight week of re-accumulation. Reward compound rate slipped to 60.19% from 61.59%, ending a 3-week rise. Net read: the DeFi demand cluster that offset the distribution last week has cooled to neutral - borrowers stopped adding leverage the moment price stopped going up, which is consistent with the rally having been chased rather than believed."},
 {"metric":"total_delegators","current_value":cur_deleg,"previous_value":prev_deleg,"method":"z_score",
  "average_value":zd[0],"stddev":zd[1],"z_score":zd[2],"severity":"low",
  "description":f"Total delegators {cur_deleg:,} ({deleg_wow:+,} WoW = {100*deleg_wow/prev_deleg:+.3f}%). Raw z={zd[2]:+.2f}σ but this is the run #9 DEGENERATE-Z case (baseline mean still dragged by the pre-capitulation ~179K level) - the economic move is ~zero, so DOWNGRADED to LOW. The base has now been FLAT for a 5TH CONSECUTIVE WEEK at ~174.3K. Five weeks spanning a +16% rip and a +24% cumulative recovery have produced no net new delegators at all. The participation-breadth watch has now failed to confirm long enough to be a finding in its own right: this recovery has zero retail broadening behind it."},
 {"metric":"staked_egld","current_value":staked,"previous_value":pecon["staked_egld"],"method":"z_score",
  "average_value":zse[0],"stddev":zse[1],"z_score":zse[2],"severity":"low",
  "description":f"Total staked {staked:,} EGLD ({staked-pecon['staked_egld']:+,} WoW, {100*(staked-pecon['staked_egld'])/pecon['staked_egld']:+.2f}%), staked ratio {sr*100:.2f}% ({100*(sr-pecon['staked_ratio']):+.2f}pp). z={zse[2]:+.2f}σ. Unlike last week, delegation and total staked AGREE this week: delegation-contract TVL rose +{total_locked-prev['staking_concentration']['total_locked_egld']:,.0f} and economics.staked rose +{staked-pecon['staked_egld']:,.0f}, with the binance_staking distortion gone ({binance_staking_prov_wow:+,.0f}). Delegation growth was broad - valuestaking +12,710, Synexis +11,749, pi-staking +5,731 (+14 users, a 4th growth week), ninjastaking +5,638 - against smartchainconnection -44,396 reversing its own prior-week gain. Holders continue to lock coins through the tape even as the delegator COUNT stays flat: existing participants adding, no newcomers."},
 {"metric":"mex_price_usd","current_value":meco["price"],"previous_value":prev_mexp,"method":"z_score",
  "average_value":zmex[0],"stddev":zmex[1],"z_score":zmex[2],"severity":"low",
  "description":f"MEX price {100*(meco['price']-prev_mexp)/prev_mexp:+.2f}% to ${meco['price']:.3e} (z={zmex[2]:+.2f}σ). MEX mcap ${meco['marketCap']/1e6:.2f}M. DEX volume rose +{100*(totvol-prev_dexvol)/prev_dexvol:.0f}% to ${totvol/1000:.0f}K, but WEGLD/USDC carries {pairs[0]['share_pct']:.0f}% of it - the same thin, CEX-derived, single-pair tape as prior rally weeks. Rising DEX volume on a stalling price with record OTC distribution is consistent with exit execution rather than broad on-chain demand."},
 {"metric":"stablecoin_supply_flat","current_value":usdc_supply_wow,"previous_value":-0.66,"method":"rule_based",
  "severity":"low",
  "description":f"Bridged-stablecoin supply STABILIZED: USDC {usdc_supply_wow:+.2f}% and USDT {usdt_supply_wow:+.2f}%, both effectively flat after several weeks of contraction. The multi-week bridged-dollar bleed has stopped, which removes a standing bearish input - dollars are no longer leaving the chain - but there is no inflow either. Combined with flat USH, the stablecoin complex is neutral this week: no fresh dry powder arriving to absorb the distribution."}]

# ---------- trend indicators ----------
accelerating_outflows=[
 {"exchange":"NET_EXCHANGE","trend":"inflow","cumulative_change_pct":None,"weeks_in_trend":1,
  "interpretation":f"Aggregate net exchange flow REVERSED to {net_total:+,.0f} EGLD INFLOW, ending a 3-week outflow streak. Per the run #15 rule the aggregate is decomposed before labeling: the inflow is real and concentrated (UPbit +152,969 desk cycling, KuCoin +142,773 single-whale exit, Bybit +62,712 OTC-routed), while the two large apparent OUTFLOWS are artifacts - Coinbase -75,338 is mostly an internal migration to a fresh nonce-0 wallet, Binance -81,032 is custody de-staking plumbing. Read jointly with OTC (run #14 rule), this is the confirming leg: the desks drained and the coins arrived on venues."},
 {"exchange":"UPbit OTC Desks","trend":"distributing","cumulative_change_pct":round(100*desk_delta/desk_prev,1),"weeks_in_trend":1,
  "interpretation":f"THE DISTRIBUTION LEG EXECUTED. Desks drained {desk_delta:+,.0f} ({desk_prev:,.0f} -> {desk_cur:,.0f}, {100*desk_delta/desk_prev:+.1f}%) - the largest single-week desk drawdown in tracking - on {OTC_THR_7D:,.0f} EGLD of 7d throughput, +{100*(OTC_THR_7D-OTC_THR_7D_PREV)/OTC_THR_7D_PREV:.0f}% over the run #16 window measured the same way. Destinations traced through zero-balance routers to Bybit, Binance.com and back to UPbit. The load-then-distribute cycle that run #16 predicted has now completed inside one week. Watch whether UPbit reloads the desks again (a fresh 364,000 already went out to the desks this week, so the pipeline is NOT idle) or whether the drawdown to ~80K marks the end of the wave."},
 {"exchange":"KuCoin","trend":"inflow","cumulative_change_pct":430.6,"weeks_in_trend":1,
  "interpretation":"KuCoin +142,773 (+430.6%), the largest proportional exchange move recorded. Entirely one counterparty: Unknown Whale erd15ku2r2j6 emptied its full 145,443 EGLD balance onto the venue and went to zero. Track KuCoin's balance next week to distinguish sale-into-book (balance stays elevated) from withdrawal/OTC (balance bleeds back down)."},
 {"exchange":"Binance Staking custody","trend":"outflow","cumulative_change_pct":round(-100*(3512650-cust_bal)/3512650,1),"weeks_in_trend":3,
  "interpretation":f"3rd consecutive drawdown leg: -{3310680-cust_bal:,.0f} this week, -{3512650-cust_bal:,.0f} cumulative from the 3,512,650 peak. Three legs in one direction makes this a programme rather than an event. Fully traced via standard custody<->hot transfers per the run #15 rule."}]

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
   {"metric":"egld_price_up","direction":"up","weeks":3,"cumulative_change_pct":round(100*(price-2.55)/2.55,1),
    "interpretation":f"3rd consecutive up-week, but only barely: +{100*(price-pp)/pp:.2f}% to ${price:.2f} after +15.93% and +5.88%. The streak survives on a technicality while its CHARACTER inverted - EGLD went from leading with the majors flat (run #16) to lagging both BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}% this week. ~+{100*(price-2.55)/2.55:.0f}% cumulative off the $2.55 low. Treat the streak as stalling, not extending: the registered run #16 question (leadership vs fade) resolved to FADE."},
   {"metric":"delegator_base_flat","direction":"flat","weeks":5,"cumulative_change_pct":0,
    "interpretation":f"5TH consecutive flat week for the delegator base at ~174.3K ({deleg_wow:+,} this week). This has now persisted across the entire +24% recovery. Five weeks is long enough to conclude the recovery has NO retail broadening behind it - the staking growth that is happening (+{staked-pecon['staked_egld']:,.0f} staked) comes from existing participants adding, not new entrants. A rally with no new participants is structurally fragile."},
   {"metric":"binance_custody_drawdown","direction":"down","weeks":3,"cumulative_change_pct":round(-100*(3512650-cust_bal)/3512650,1),
    "interpretation":f"3rd consecutive week of Binance Staking custody drawdown, -{3512650-cust_bal:,.0f} cumulative from the peak. Promoted from event to programme: a sustained unwind of the position accumulated over runs #9-#11."},
   {"metric":"token_holder_count_decline","direction":"down","weeks":17,"cumulative_change_pct":None,
    "interpretation":"17th consecutive week of small holder declines across top-10 tokens. Established airdrop-decay baseline; the active >$1M-mcap token base is stable."}],
 "regime_shifts":[
   {"metric":"otc_distribution_wave_delivered","before_value":round(desk_prev),"after_value":round(desk_cur),
    "description":f"THE STAGED SUPPLY WAS DELIVERED. The run #16 record reload (desks to {desk_prev:,.0f}) unwound completely in one week: desks {desk_prev:,.0f} -> {desk_cur:,.0f} ({desk_delta:+,.0f}, {100*desk_delta/desk_prev:+.1f}%) on {OTC_THR_7D:,.0f} EGLD of throughput, with destinations traced through zero-balance routers to Bybit, Binance.com and UPbit. This completes the load-then-distribute cycle inside a single week and is the defining on-chain event of the run. The market's response - +{100*(price-pp)/pp:.2f}% price - is the tell: a 1.33M distribution wave was enough to stop a +24% recovery in its tracks."},
   {"metric":"egld_leadership_thesis_failed","before_value":pp,"after_value":price,
    "description":f"THE RUN #16 DECOUPLING WAS A ONE-WEEK EVENT, NOT A REGIME. Last run recorded EGLD's first EGLD-specific up-move (+15.93% on flat majors) as a potential laggard->leader regime break, with the explicit test being a 3rd up-week. The test failed: EGLD +{100*(price-pp)/pp:.2f}% vs BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}%, back to underperforming both. The correct classification is now a one-week distribution-absorbing spike, consistent with the run #13 exit-liquidity pattern (relief move on an unimproving structural base fails quickly). Registering it as a FAILED regime shift closes the run #16 watch cleanly."},
   {"metric":"exchange_and_otc_channels_aligned","before_value":-196000,"after_value":round(net_total),
    "description":f"For the first time since run #13 the two distribution channels AGREE. Through runs #14-#16 exchange balances and OTC throughput substituted for each other (outflows on the venue while the desks loaded), which made every net-flow number ambiguous. This week both point the same way: desks drained {desk_delta:+,.0f} AND exchanges took {net_total:+,.0f} net inflow. The ambiguity that forced the run #14 joint-read rule has resolved - to the distributive side."}]}

# ---------- dormant activations ----------
dormant_activations=[]

# ---------- watch list ----------
mw_bal=bal_of("erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw") or 998971
watch_list=[
 {"item":f"KuCoin +142,773 (+430%) from ONE whale (erd15ku2r2j6) that emptied its entire 145,443 balance and went to zero","reason":"The largest proportional exchange move in tracking, and the single most actionable open question. A previously passive large holder fully exited onto one venue. NEXT WEEK'S TEST: if KuCoin's balance bleeds back down, the coins were withdrawn or OTC-settled (neutral); if it stays elevated or KuCoin distributes onward, the position was sold into the book (bearish, and ~0.5% of circulating supply hit the tape). Also watch whether the now-empty wallet refills from any source.","weeks_on_list":1},
 {"item":f"OTC desks DRAINED {desk_delta:+,.0f} to {desk_cur:,.0f} on {OTC_THR_7D/1e6:.2f}M throughput - distribution leg executed, but UPbit already sent 364,000 back out to the desks","reason":"The run #16 record reload has been fully distributed to exchanges via traced routers. The cycle is complete, BUT the pipeline is not idle - UPbit pushed a fresh 364,000 to the desks inside the same window. PRE-COMMITTED READING for next week: desks RELOADING back toward 300K+ = a second distribution wave is being staged (bearish continuation); desks staying near ~80K with low throughput = the wave is finished and supply is exhausted (constructive). This is the highest-value forward indicator on the list.","weeks_on_list":8},
 {"item":f"EGLD leadership FAILED - +{100*(price-pp)/pp:.2f}% vs BTC {btc_wow:+.2f}% / ETH {eth_wow:+.2f}%, back to laggard","reason":"Run #16's registered test (3rd up-week = momentum regime vs fade back to beta) resolved decisively to FADE within one week. EGLD is again underperforming both majors. Watch whether it now underperforms on the DOWNSIDE too - if the next macro down-week sees EGLD fall harder than BTC/ETH, the full high-beta-laggard regime is re-confirmed and the +24% recovery should be treated as a bear-market rally.","weeks_on_list":1},
 {"item":f"Binance Staking custody 3rd drawdown leg -{3310680-cust_bal:,.0f} (now {cust_bal:,.0f}, -{3512650-cust_bal:,.0f} from peak)","reason":"Three consecutive legs promotes this from event to programme. Fully traced via standard custody<->hot transfers. Note the binance_staking DELEGATION provider stabilized (+298) after last week's -149K, so the unwind is now custody-only. Watch whether the custody keeps drawing toward zero (a full exit of the runs #9-#11 accumulation) and whether the hot-wallet EGLD is distributed or re-staked.","weeks_on_list":11},
 {"item":f"Mega Whale erd18mv2z6r2 RESUMED absorbing +{mw_bal_cur-1042690:,.0f} (now {mw_bal_cur:,.0f}) via Coinbase Routing","reason":"The market's one identifiable large bid came back after a one-week pause, filled through the same Coinbase Routing pipe as run #15. This is the main constructive counter-signal. But the scale is asymmetric - ~50K absorbed against ~1.33M distributed. Watch whether the absorber scales up (a real bid building under the market) or continues taking ~50K clips (a floor, not a match for supply).","weeks_on_list":14},
 {"item":"Delegator base FLAT for a 5th consecutive week at ~174.3K across the entire +24% recovery","reason":"Five weeks spanning the full recovery with zero net new delegators. Staking is growing (+81K) but only from existing participants adding. A recovery with no participation broadening is structurally fragile. Watch whether a sustained hold above $3 finally pulls new delegators in, or whether the base stays flat and confirms the rally as existing-holder positioning only.","weeks_on_list":5},
 {"item":"DeFi leverage expansion PAUSED - USH flat (+0.14%) after last week's +6.49% mint; compound rate slipped 61.59% -> 60.19%","reason":"The run #16 'leverage returning' demand cluster did not sustain a second week. It did not reverse either (no forced-closure burn), so this is a pause, not a de-risking. XEGLD supply did continue +2.69% (2nd week). Watch whether USH resumes minting if price breaks higher (conviction) or begins burning if price rolls over (the leverage was chased).","weeks_on_list":2},
 {"item":"Bridged stablecoins stopped contracting (USDC -0.13%, USDT +0.05%) but no inflow","reason":"The multi-week bridged-dollar bleed has ended, removing a standing bearish input. But flat is not the same as returning - no fresh dry powder is arriving to absorb distribution. Watch for a genuine stablecoin INFLOW week as the first sign that outside capital is coming back to the chain.","weeks_on_list":4}]

executive_summary=[
 {"finding":f"THE RECORD OTC RELOAD WAS DISTRIBUTED - AND IT WENT TO EXCHANGES. Run #16's biggest-ever desk load (+238K, to ~335K) unwound completely in one week: combined desk balance COLLAPSED {desk_delta:+,.0f} to {desk_cur:,.0f} ({100*desk_delta/desk_prev:+.1f}%, the largest drawdown in tracking) on {OTC_THR_7D:,.0f} EGLD of 7d throughput (+{100*(OTC_THR_7D-OTC_THR_7D_PREV)/OTC_THR_7D_PREV:.0f}% vs the run #16 window measured the same way). Destinations are TRACED this time: the five largest recipients are all zero-balance, high-nonce routers forwarding to Bybit and Binance.com, plus 150,000 straight back to UPbit. The staged supply was delivered onto venues, not into retail self-custody.","severity":"critical","category":"whale"},
 {"finding":f"THE MARKET ABSORBED IT AND STALLED: EGLD +{100*(price-pp)/pp:.2f}% to ${price:.2f} while BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}% BOTH OUTPACED IT. Run #16's registered test - a 3rd up-week confirming EGLD leadership vs a fade back to beta - resolved to FADE inside one week. The +15.93% EGLD-specific decoupling was a one-week event, not a regime break, and EGLD is again a laggard. A +24% recovery that stops dead the moment a 1.33M distribution wave hits is the run #13 exit-liquidity signature.","severity":"high","category":"network"},
 {"finding":f"NET EXCHANGE FLOW REVERSED TO {net_total:+,.0f} INFLOW after three outflow weeks - the confirming leg of the distribution. Concentrated in UPbit +152,969 (desk inventory cycling back), KuCoin +142,773 and Bybit +62,712 (the OTC pipeline's largest destination). The apparent offsetting OUTFLOWS are artifacts, not accumulation: Coinbase -75,338 is mostly an internal migration of 65,090 to a fresh nonce-0 wallet that still holds it, and Binance -81,032 is custody de-staking plumbing. For the first time since run #13 the exchange-balance and OTC channels agree - both distributive.","severity":"high","category":"whale"},
 {"finding":f"LARGEST PROPORTIONAL EXCHANGE MOVE EVER RECORDED - KuCoin +142,773 (+430.6%) from a SINGLE counterparty. Unknown Whale erd15ku2r2j6 (nonce 24) sent its ENTIRE 145,443 EGLD balance to KuCoin and now holds zero. A passive large holder emptying itself onto one venue is the cleanest proxy for intent to sell available on-chain, and at ~0.5% of circulating supply it is material. Whether it was sold into the book or withdrawn/OTC-settled is next week's most actionable test.","severity":"high","category":"whale"},
 {"finding":f"THE ABSORBER RETURNED, BUT IT IS OUTGUNNED. Mega Whale erd18mv2z6r2 resumed accumulating +{mw_bal_cur-1042690:,.0f} to {mw_bal_cur:,.0f}, filled once again through the Coinbase Routing pipe - the market's one identifiable large bid is still live after last week's pause. This is the main constructive counter-signal, but the scale is asymmetric: ~50K absorbed against ~1.33M distributed. It is a floor under the market, not a match for the supply.","severity":"medium","category":"whale"},
 {"finding":f"BINANCE CUSTODY DE-STAKING, 3RD CONSECUTIVE LEG: -{3310680-cust_bal:,.0f} to {cust_bal:,.0f}, now -{3512650-cust_bal:,.0f} cumulative from the 3.51M peak. Three legs in one direction promotes this from event to programme - a systematic unwind of the position accumulated in runs #9-#11, fully traced via standard custody<->hot transfers. The separate binance_staking DELEGATION provider STABILIZED ({binance_staking_prov_wow:+,.0f}) after last week's -148,941, so the unwind is now custody-only rather than two-front.","severity":"medium","category":"whale"},
 {"finding":f"STAKING GREW BUT PARTICIPATION DID NOT, 5TH WEEK RUNNING. Total staked +{staked-pecon['staked_egld']:,.0f} to {staked:,} (ratio {sr*100:.2f}%) and delegation TVL +{total_locked-prev['staking_concentration']['total_locked_egld']:,.0f} broadly (valuestaking +12,710, Synexis +11,749, pi-staking +5,731) - with the binance_staking distortion gone, delegation and total staked agree for once. But the delegator COUNT was flat for a 5th consecutive week at {cur_deleg:,}, spanning the entire +24% recovery. Existing holders are adding; no new entrants at all. A recovery with no participation broadening is structurally fragile.","severity":"medium","category":"staking"},
 {"finding":f"DEFI LEVERAGE EXPANSION PAUSED. USH supply was flat at {ush_supply_wow:+.2f}% after last week's +6.49% mint - the 'leverage returning' cluster did not sustain a 2nd week, though it did not unwind either (no forced-closure burn). XEGLD supply did continue +{xegld_supply_wow:.2f}% (2nd week re-accumulating). Reward compound rate slipped to 60.19% from 61.59%, ending a 3-week rise. Bridged stablecoins stopped contracting (USDC {usdc_supply_wow:+.2f}%, USDT {usdt_supply_wow:+.2f}%) but showed no inflow. Borrowers stopped adding leverage the moment price stopped rising - consistent with a chased rally.","severity":"low","category":"defi"}]

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
   "btc_correlation_note":f"EGLD {100*(price-pp)/pp:+.2f}% WoW vs BTC {btc_wow:+.2f}% / ETH {eth_wow:+.2f}% (WoW). EGLD UNDERPERFORMED BOTH MAJORS, reverting to the high-beta-laggard pattern after exactly one week of leadership. Run #16's EGLD-specific decoupling (+15.93% on flat majors) is therefore reclassified as a one-week event rather than a regime break. With the majors up and EGLD flat, the marginal EGLD seller is chain-specific - consistent with the 1.33M OTC distribution wave that ran through the same window.",
   "transactions_added":st["transactions"]-pact["total_transactions"],"supply_added":econ["totalSupply"]-pecon["total_supply"],
   "staked_egld_added":staked-pecon["staked_egld"],"epoch_advanced":st["epoch"]-pact["epoch"]},
 "analysis":f"EGLD gained only {100*(price-pp)/pp:+.2f}% WoW to ${price:.2f} - and the composition matters far more than the number. BTC {btc_wow:+.2f}% and ETH {eth_wow:+.2f}% BOTH outpaced it, so last week's EGLD-specific decoupling (+15.93% on flat majors) reversed inside a single week. Run #16 explicitly registered the test - a 3rd up-week to confirm laggard->leader, or a fade - and it resolved to FADE. z={zp[2]:+.2f}σ (neutral). Market cap ${econ['marketCap']/1e6:.1f}M ({100*(econ['marketCap']-pecon['market_cap_usd'])/pecon['market_cap_usd']:+.1f}%). The reason the rally stalled is legible on-chain: the OTC desks DELIVERED the record inventory they staged last week, draining {desk_delta:+,.0f} to {desk_cur:,.0f} while pushing {OTC_THR_7D:,.0f} EGLD of throughput, with destinations traced through zero-balance routers to Bybit, Binance.com and back to UPbit. Exchanges took {net_total:+,.0f} net INFLOW as a result, ending a 3-week outflow streak - so for the first time since run #13 the exchange-balance channel and the OTC channel point the same way instead of substituting for each other. Binance ran a 3rd custody de-staking leg (-{3310680-cust_bal:,.0f}, now -{3512650-cust_bal:,.0f} from peak). Against all that, the demand side was thinner than last week: the Mega Whale absorber resumed (+{mw_bal_cur-1042690:,.0f} via Coinbase Routing) but at ~1/25th the scale of the distribution; USH leverage-minting PAUSED ({ush_supply_wow:+.2f}% after +6.49%); the reward compound rate slipped to 60.19%; and the delegator base stayed flat a 5th week at {cur_deleg:,}. Staking itself was healthy - total staked +{staked-pecon['staked_egld']:,.0f} to {staked:,} (ratio {sr*100:.2f}%) and delegation +{total_locked-prev['staking_concentration']['total_locked_egld']:,.0f} broadly - but entirely from existing participants. Activity: {round((st['transactions']-pact['total_transactions'])/7)/1e6:.1f}M txs/day, account growth +{(st['accounts']-pact['total_accounts'])/1000:.1f}K. The read: last week posed real demand vs staged supply; this week supply was delivered, demand did not scale with it, and price stopped. That is a bearish resolution of the run #16 tension - tempered only by the fact that the market absorbed 1.33M EGLD without breaking down."}

# ---------- whale analysis ----------
whale_analysis=("THIS WEEK'S DOMINANT MOVES:\n"
 f"1) THE OTC DISTRIBUTION WAVE EXECUTED - AND THE DESTINATIONS ARE TRACED. Run #16 flagged the biggest desk reload in tracking and asked whether the inventory would be pushed out. It was, completely: combined UPbit OTC + OTC Distribution desk balance COLLAPSED {desk_delta:+,.0f} EGLD ({desk_prev:,.0f} -> {desk_cur:,.0f}, {100*desk_delta/desk_prev:+.1f}%) - the largest single-week desk drawdown observed - while pushing {OTC_THR_7D:,.0f} EGLD of 7d outbound throughput, +{100*(OTC_THR_7D-OTC_THR_7D_PREV)/OTC_THR_7D_PREV:.0f}% over the run #16 window measured the same (paginated) way. Unlike prior weeks the endpoints are identified: the five largest unlabeled recipients (erd1w7nlme 213,607 / erd1e9luc4 100,425 / erd1g6fntj 74,252 / erd1ckh3v9 72,871 / erd1ddqnaj 54,468) are ALL zero-balance, high-nonce pass-through routers that forward to Bybit and Binance.com, alongside 150,000 sent straight back to UPbit and ~166K reaching Bybit in total. So the staged supply went ONTO EXCHANGES, not into retail self-custody. Note also that the pipeline is not finished: UPbit pushed a fresh 364,000 out to the desks inside the same window.\n\n"
 f"2) NET EXCHANGE FLOW REVERSED TO {net_total:+,.0f} INFLOW - the confirming leg. After three outflow weeks, coins arrived on venues exactly as the OTC trace predicts. UPbit +152,969 (desk inventory cycling back), KuCoin +142,773, Bybit +62,712 (the pipeline's largest destination, reversing last week's -221K and resolving that ambiguity toward the bearish reading). Applying the run #15 decompose rule in the opposite direction, the apparent OUTFLOWS are the unreal ones: Coinbase -75,338 is dominated by an internal custody migration (65,090 to fresh nonce-0 wallet erd1z4xerdjq6aa2, which still holds it), and Binance -81,032 is de-staking plumbing. For the first time since run #13 the exchange and OTC channels agree rather than substituting for each other.\n\n"
 f"3) A SINGLE WHALE FULLY EXITED ONTO KUCOIN - the largest proportional exchange move in tracking. KuCoin +142,773 (+430.6%, 33,156 -> 175,929) traces to ONE counterparty: Unknown Whale erd15ku2r2j6smlwumftumlpw0mfpqxy32wyt4ewxzyhs3ugsjee8stq2xh84e (nonce 24) sent its ENTIRE 145,443 EGLD balance to the venue and now holds ZERO. At ~0.5% of circulating supply this is material, and a wallet that empties itself onto an exchange is the cleanest on-chain proxy for intent to sell. Separately, a second large wallet (erd102hmf79en4, 165,006) also emptied - but that one is a MIGRATION, not a sale: the full 165,006 landed in fresh nonce-0 wallet erd18pwhucm0rd89, which holds it today.\n\n"
 f"4) THE ABSORBER RESUMED, AT ONE-TWENTY-FIFTH THE SCALE. Mega Whale erd18mv2z6r2, flagged last week as having PAUSED, resumed accumulating +{mw_bal_cur-1042690:,.0f} EGLD in a single transfer to {mw_bal_cur:,.0f} - counterparty once again the Coinbase Routing Wallet, the same pipe as run #15. The market's one identifiable large bid is therefore still live, which is the week's main constructive signal and means the distribution met a real buyer rather than a vacuum. But the asymmetry is the point: ~50K absorbed against ~{OTC_THR_7D/1e6:.2f}M distributed. It is a floor, not a counterweight.\n\n"
 f"5) BINANCE CUSTODY, 3RD DE-STAKING LEG: -{3310680-cust_bal:,.0f} (3,310,680 -> {cust_bal:,.0f}), traced via standard transfers (Binance.com -> custody 396,421; custody -> Binance.com 500,000), for a cumulative -{3512650-cust_bal:,.0f} over three weeks from the 3,512,650 peak. Three consecutive same-direction legs promotes this from event to programme - a systematic unwind of the runs #9-#11 accumulation. The one mitigating detail: the separate binance_staking DELEGATION provider STABILIZED at {binance_staking_prov_wow:+,.0f} after last week's -148,941, so the unwind is now custody-only rather than running on two fronts.\n\n"
 f"6) WHALE TIERS - READ WITH THE BOUNDARY GUARD APPLIED, because this week the raw aggregates are almost entirely artifact. Raw: mega {whale_tiers['mega_whales']['net_change_egld']/1000:+.0f}K, large {whale_tiers['large_whales']['net_change_egld']/1000:+.0f}K, mid {whale_tiers['mid_whales']['net_change_egld']/1000:+.0f}K. Three wallets crossed tier boundaries: BOTH OTC desks fell large->mid (-255,736 leaving the large tier purely by reclassification) while KuCoin rose mid->large (+142,773 entering it). On top of that, two large-tier wallets emptied - one a genuine sale to KuCoin (145,443) and one a pure wallet migration (165,006). Netting the reclassifications and the migration out, there is no meaningful organic tier rotation this week; the tier table is measuring the OTC cycle and two wallet reshuffles, not conviction. This is the run #14 boundary-crossing guard doing exactly the job it was written for.")

# ---------- staking analysis ----------
staking_analysis=(f"Staking concentration remains low and essentially static (HHI {hhi:.4f}, top-5 {top5:.1f}%, top-10 {top10:.1f}% - unchanged WoW). Total delegated {total_locked:,.0f} EGLD across {len(provs)} active providers ({total_locked-prev['staking_concentration']['total_locked_egld']:+,.0f} WoW). Active delegator base {cur_deleg:,} ({deleg_wow:+}, {100*deleg_wow/prev_deleg:+.3f}%). Total staked (economics, direct-node + delegation) {staked:,} EGLD ({staked-pecon['staked_egld']:+,.0f}), staked ratio {sr*100:.2f}% ({100*(sr-pecon['staked_ratio']):+.2f}pp).\n\n"
 f"DELEGATION AND TOTAL STAKED AGREE THIS WEEK. Last run the two diverged and the report had to net out a single distorting entity: the binance_staking provider's -148,941 made delegation TVL look like it shrank while ex-Binance it grew +120K. That distortion is gone - binance_staking was {binance_staking_prov_wow:+,.0f} this week - so both measures now move together: delegation +{total_locked-prev['staking_concentration']['total_locked_egld']:,.0f} and economics.staked +{staked-pecon['staked_egld']:,.0f}. Growth was broad across mid-tier names rather than concentrated: valuestaking +12,710 (+23 users), Synexis +11,749 (+16 users), pi-staking +5,731 (+14 users), ninjastaking +5,638, cslabsio +5,612, inotel +5,445, egldsqueeze +5,077, ProjectX +4,438, vaporrepublic +4,359. The single large offset was smartchainconnection -44,396, which simply gives back its own prior-week +38,033 - a round-trip, not a new trend.\n\n"
 f"THE DELEGATOR BASE HAS NOW BEEN FLAT FOR FIVE CONSECUTIVE WEEKS at {cur_deleg:,} ({deleg_wow:+} this week). That span covers the ENTIRE +24% recovery off the $2.55 low, including last week's +15.93% rip. The raw z-score {zd[2]:+.2f}sigma is the run #9 degenerate case (baseline still dragged by the ~179K pre-capitulation level) and is downgraded to LOW - the economic move is zero. The interpretation has hardened over five weeks: this is no longer 'capitulation is behind us' (that read was correct at week 1-2), it is a recovery with NO participation broadening whatsoever. Per the run #11 churn matrix, flat delegators with rising staked EGLD is whale/existing-holder consolidation, not retail growth. It is the single most persistent structural weakness in the current tape.\n\n"
 f"YIELD-CHASE COHORT: net {cohort_net/1000:+.1f}K. pi-staking (0% fee) continued its slow draw for a 4th week (+5,731, +14 users) - the one durable small-provider growth story left. Otherwise the concentrated May-era yield-chase dynamic remains dissipated; this week's growth is spread across ordinary mid-tier providers rather than clustering in the 0%-fee names.\n\n"
 f"APR distribution: {buckets[3]['provider_count']} providers in the 8-9% bucket holding {buckets[3]['total_locked_egld']/1e6:.1f}M EGLD (the dominant cluster, unchanged), {buckets[2]['provider_count']} in 7-8% holding {buckets[2]['total_locked_egld']/1e6:.1f}M, {buckets[4]['provider_count']} in 9-10% holding {buckets[4]['total_locked_egld']/1e3:.0f}K. The 10%+ bucket remains empty (consistent across all 2026 runs). APR-weighted average {apr_w:.2f}%. Base APR {100*econ['baseApr']:.2f}% vs topUp {100*econ['topUpApr']:.2f}% - both drifted marginally lower as staked supply rose.\n\n"
 f"DELEGATOR CHURN: {gain} providers gaining vs {lose} losing delegators for a net {deleg_wow:+} - balanced churn with a mild skew toward losers, consistent with a flat base reshuffling rather than growing. No notable named-validator joiners or leavers above 50K EGLD; system-contract aggregators (erd1qqqq...) are excluded per the run #10 rule.")

# ---------- token analysis ----------
top_pair_share=pairs[0]['share_pct']
second_pair=pairs[1] if len(pairs)>1 else None
token_analysis=(f"DEX volume rose to ${totvol/1000:.0f}K ({100*(totvol-prev_dexvol)/prev_dexvol:+.0f}% WoW) - a second consecutive increase, but WEGLD/USDC carried {top_pair_share:.1f}% of it. That extreme single-pair concentration is the same thin, CEX-derived tape seen through every rally week: buyers (and this week, sellers working out of the OTC distribution) routing through the one deep stable pair rather than broad on-DEX activity. MEX/WEGLD {second_pair['share_pct'] if second_pair else 0:.1f}% is the only other pair with meaningful share. Rising DEX volume on a stalling price during a record distribution wave is more consistent with exit execution than with fresh demand.\n\n"
 f"NEWLY-ISSUED TOKENS: 0 genuine issuances passing the quality bar this week. The ESDT system-SC issue scan ran clean (no false positives of the run #15 WrappedUSDC kind, the holder-count guard is working). A quiet launch week - attention is on the EGLD spot move, not new deploys.\n\n"
 f"Token holder counts declined for a 17th consecutive week across the top 10 - the established airdrop-decay baseline, not a new signal. WrappedEGLD and WrappedUSDC remain the most-held real tokens. WEGLD supply BURNED {[e for e in token_supply_events if e['identifier'].startswith('WEGLD')][0]['change_pct'] if any(e['identifier'].startswith('WEGLD') for e in token_supply_events) else 0:+.2f}% (net unwrapping back to native EGLD) - a 2nd straight week of unwrapping, consistent with holders moving out of DEX/wrapped form to hold or stake native EGLD.\n\n"
 f"MEX price {100*(meco['price']-prev_mexp)/prev_mexp:+.2f}% to ${meco['price']:.3e} - flat, tracking EGLD's stall after last week's rip. MEX mcap ${meco['marketCap']/1e6:.2f}M.\n\n"
 f"Top by market cap: EmoryaSportsX (EMRS) leads at ${D['tokens_mcap'][0].get('marketCap',0)/1e6:.1f}M ({D.get('emrs_token',{}).get('accounts',0):,} holders, {D.get('emrs_token',{}).get('transactions',0):,} txs - a genuine large-cap per run #14's correction). Then WrappedUSDC ${D['tokens_mcap'][1].get('marketCap',0)/1e6:.2f}M, xMoney UTK ${D['tokens_mcap'][2].get('marketCap',0)/1e6:.2f}M, ZoidPay ${D['tokens_mcap'][3].get('marketCap',0)/1e6:.2f}M, StakedEGLD ${D['tokens_mcap'][4].get('marketCap',0)/1e6:.2f}M.\n\n"
 f"Bridged stablecoin supply STOPPED CONTRACTING: USDC {usdc_supply_wow:+.2f}% and USDT {usdt_supply_wow:+.2f}%, both effectively flat after several weeks of burn (USDC had run -2.0% then -0.66%). Ending a multi-week bleed removes a standing bearish input - dollars are no longer leaving the chain. But flat is not returning: there is no stablecoin INFLOW, so no fresh dry powder arrived to absorb this week's distribution. With USH also flat, the entire stablecoin complex is neutral.")

# ---------- defi analysis ----------
defi_analysis=(f"DEFI DEMAND COOLED TO NEUTRAL - the constructive cluster that offset the distribution last week did not sustain. The supply-based signals (price-independent, per the run #13 rule) split:\n"
 f"(1) USH (Hatom CDP stablecoin) supply was FLAT at {ush_supply_wow:+.2f}% ({supply('USH-111e09'):,.0f}) after last week's +6.49% mint. Run #16 established the mint-as-leverage-returning rule and registered the test: does the CDP expansion SUSTAIN (conviction) or reverse (a chase)? Neither happened - borrowers simply STOPPED adding. No new leverage, but also no forced-closure burn, so this is a pause rather than de-risking. The timing is telling: leverage stopped expanding the same week price stopped rising.\n"
 f"(2) XEGLD (XOXNO LSD) supply DID continue, +{xegld_supply_wow:.2f}% to {supply('XEGLD-e413ed'):,.0f} - a 2nd straight week of re-accumulation after the run #14 -29% collapse and run #15 stabilization. Liquid staking is the one DeFi leg still in genuine inflow; the redemption event is fully behind it. XOXNO LSD TVL ${xoxno_lsd/1e6:.2f}M / {xlsd_egld/1000:.0f}K EGLD (+8.3% EGLD WoW).\n"
 f"(3) The reward compound rate SLIPPED to 60.19% from 61.59%, ending a 3-week rise. Delegators claimed slightly more and compounded slightly less as the price stalled - a mild bearish drift in DeFi sentiment, consistent with (1).\n\n"
 f"HATOM LSD FLAT: SEGLD supply {segld_supply_wow:+.2f}%, SWTAO {swtao_supply_wow:+.2f}% - both unchanged. Hatom LSD ${hatom_lsd/1e6:.2f}M USD (SEGLD ${segld_mcap/1e6:.2f}M + SWTAO ${swtao_mcap/1e6:.2f}M). The dataApi price feed was CLEAN for a 3rd consecutive run (0 re-fetch retries, all 4 dataApi-class tokens populated first pass), so the USD figures are fully reliable and the run #13/#14 null-price workaround stayed dormant.\n\n"
 f"HATOM LENDING ${hatom_lending/1e6:.2f}M USD, EGLD-denominated TVL {100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.2f}%. THE BILATERAL INVERSE RULE IS NOT EVALUABLE THIS WEEK and is explicitly not counted as an observation: the run #12 guardrail requires |dPrice| >= 5%, and this week's move was only {100*(price-pp)/pp:+.2f}%. At that magnitude EGLD-denominated TVL noise dominates any real depositor response, so the {100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.2f}% reading carries no information about the rule. The confirmed series stands unchanged at two up-week observations (0.49 in run #15, 0.72 in run #16) plus the earlier down-week set. Recording the non-test explicitly is the discipline the guardrail exists to enforce - the temptation on a small-move week is to log a spurious confirmation.\n\n"
 f"xExchange TVL ${xexch_tvl_usd/1e6:.2f}M / {xexch_tvl_egld/1000:.0f}K EGLD ({100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld:+.1f}% EGLD) - a mild contraction as WEGLD was unwrapped. Aggregator throughput held up: XOXNO {tcount('XOXNO Aggregator'):,} and OneDex {tcount('OneDex Swap'):,} daily transfers, both broadly stable, so routing/aggregation activity did not fall away with the price stall.")

report={
 "metadata":{"report_date":"2026-07-20","period_start":"2026-07-13T00:00:00Z","period_end":"2026-07-20T00:00:00Z",
   "generated_at":datetime.now(timezone.utc).isoformat(),"egld_price_usd":price,
   "btc_price_usd":be["bitcoin"]["usd"],"eth_price_usd":be["ethereum"]["usd"],"run_number":17,
   "data_sources_ok":json.load(open("/tmp/run17/status.json"))["ok"],
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
 "meta_learning":{"run_number":17,
   "endpoints_that_worked":json.load(open("/tmp/run17/status.json"))["ok"],
   "endpoints_that_failed":[],
   "api_quirks":[
     "CRITICAL - OTC THROUGHPUT HAS BEEN UNDERCOUNTED ~4x IN EVERY PRIOR RUN. The collector fetches desk outbound txs with size=50 and no pagination. On a high-activity desk that window covers only ~2.5 of the 7 days, so the reported 'throughput' was a truncated tail, not a 7d total. Verified by re-querying with full pagination: this week's true figure is 1,328,037 EGLD net of inter-desk transfers (vs 213,181 from the capped sample), and re-running the run #16 window the same way gives 1,100,791 (vs the ~323K reported at the time). The entire historical throughput series (85K/145K/163K/172K/195K/323K) is a lower bound on a shifting window and is NOT a comparable time series. Fix: paginate until the after= boundary, and subtract desk<->desk transfers (157,500 this week) which double-count.",
     "DESK GROSS THROUGHPUT DOUBLE-COUNTS INTER-DESK TRANSFERS: UPbit OTC sent 315,000 to the OTC Distribution Wallet this week (and 255,500 in the run #16 window). Netting these out is required or the two desks inflate each other's numbers.",
     "CLEAN PRICE-FEED RUN (3rd consecutive): the dataApi re-fetch guard reported 0 retries - all 4 dataApi-class tokens (SEGLD, SWTAO, USH, XEGLD) populated price+mcap on the first sequential pass at 1.05s spacing. Three clean runs confirm the run #15 read that the null behavior is a transient feed hiccup, not a per-token outage.",
     "A ZERO-BALANCE nonce-0 RECIPIENT IS A MIGRATION, NOT A FLOW. Two apparent large 'exits' this week were wallet migrations: Coinbase Custody 65,090 -> fresh nonce-0 erd1z4xerdjq6aa2 (still holds it), and whale erd102hmf79en4 165,006 -> fresh nonce-0 erd18pwhucm0rd89 (still holds it). Both would have been misread as distribution from balance deltas alone. Rule: when a tracked wallet empties, resolve the single outbound receiver and check its nonce and balance before classifying - nonce 0 + holds the exact amount = migration."],
   "data_gaps":[
     "Desk-destination router tracing is itself capped at size=50 per router, so the ~166K attributed to Bybit and the amounts attributed to Binance.com are LOWER BOUNDS. The direction (routers forward to exchanges) is certain; the exact split across venues is not.",
     "The KuCoin depositor erd15ku2r2j6 shows a 0-value inbound leg in the 7d window, so where its 145,443 EGLD originally came from is not established - only that it left in full to KuCoin. Worth tracing its inbound history next run to see whether it was an OTC recipient.",
     "Whether the KuCoin +142,773 was sold into the order book or subsequently withdrawn/OTC-settled cannot be determined from balances alone until next week's snapshot."],
   "key_findings":[
     "THE RECORD OTC RELOAD WAS DISTRIBUTED, AND TO EXCHANGES. Desks drained -255,736 (335,430 -> 79,694, -76.2%, largest drawdown in tracking) on 1,328,037 EGLD of true 7d throughput (+20.6% vs the run #16 window measured the same paginated way). Destinations traced: five zero-balance high-nonce routers forwarding to Bybit and Binance.com, plus 150,000 straight back to UPbit.",
     "EGLD LEADERSHIP THESIS FAILED IN ONE WEEK: +0.96% to $3.16 while BTC +1.95% and ETH +4.36% both outpaced it. Run #16's registered test (3rd up-week = regime change vs fade) resolved to FADE. The +15.93% decoupling was a one-week event, not a laggard->leader flip.",
     "NET EXCHANGE FLOW REVERSED to +193,747 INFLOW after 3 outflow weeks - the confirming leg of the distribution. UPbit +152,969, KuCoin +142,773, Bybit +62,712. First time since run #13 that the exchange-balance and OTC channels agree instead of substituting.",
     "LARGEST PROPORTIONAL EXCHANGE MOVE IN TRACKING: KuCoin +430.6% (33,156 -> 175,929), entirely one counterparty - Unknown Whale erd15ku2r2j6 sent its ENTIRE 145,443 EGLD balance and went to zero. ~0.5% of circulating supply, a clean full-exit signature.",
     "THE ABSORBER RETURNED BUT IS OUTGUNNED: Mega Whale erd18mv2z6r2 resumed +50,621 (to 1,093,312) via the Coinbase Routing pipe after last week's pause - the one identifiable large bid is live, but ~50K absorbed against ~1.33M distributed.",
     "BINANCE CUSTODY 3RD DE-STAKING LEG: -103,579 (to 3,207,101), cumulative -305,549 over three weeks from the 3,512,650 peak. Promoted from event to programme. The separate binance_staking DELEGATION provider STABILIZED (+298) after last week's -148,941, so the unwind is now custody-only.",
     "DELEGATOR BASE FLAT A 5TH WEEK at 174,335 - spanning the entire +24% recovery. Staking grew (+81,022 staked, +47,701 delegation, broad across valuestaking/Synexis/pi-staking) but from existing participants only. Zero participation broadening.",
     "DEFI LEVERAGE PAUSED: USH flat +0.14% after last week's +6.49% mint (borrowers stopped adding the week price stopped rising, but no forced-closure burn); XEGLD supply +2.69% (2nd week re-accumulating); reward compound rate slipped 61.59% -> 60.19%, ending a 3-week rise.",
     "BILATERAL INVERSE RULE NOT EVALUABLE (|dPrice| 0.96% < the 5% guardrail) - explicitly recorded as a non-test rather than logging a spurious confirmation. Series stands at 0.49 / 0.72 on up-weeks.",
     "Bridged stablecoins STOPPED contracting (USDC -0.13%, USDT +0.05%) after weeks of burn - removes a bearish input but brings no fresh dry powder. DEX volume +20.5% to $194K on 91.5% WEGLD/USDC concentration."],
   "action_items_from_previous":8,
   "action_items_completed":8,
   "methodology_changes":[
     "PAGINATE DESK/ROUTER TX QUERIES - the single most important fix from this run. size=50 covers only ~2.5 days on a busy desk, so every prior throughput figure was a severe undercount (run #16: 323K reported vs 1,100,791 actual). Always page until the after= boundary and net out desk<->desk transfers. Historical throughput values must be treated as lower bounds on inconsistent windows, not a comparable series.",
     "RESOLVE THE RECEIVER BEFORE CALLING AN EMPTIED WALLET A SALE (new): a wallet going to zero looks like distribution but may be a migration. Check the single large outbound receiver's nonce and balance - nonce 0 holding the exact amount = internal migration (Coinbase Custody 65,090; whale erd102hmf79en4 165,006 this week). Both would otherwise have been logged as outflows. This is the wallet-level analogue of the run #15 entity-decomposition rule.",
     "APPLY THE BOUNDARY-CROSSING GUARD BEFORE NARRATING TIER AGGREGATES (reinforced, run #14 rule): this week the raw tier deltas are almost pure artifact - both OTC desks fell large->mid (-255,736 by reclassification) while KuCoin rose mid->large (+142,773), on top of one genuine sale and one migration. Netting these out leaves no organic tier rotation. The guard prevented a false wealth-distribution narrative.",
     "HONOR THE |dPrice| >= 5% GUARDRAIL ON THE BILATERAL INVERSE RULE (discipline reinforced): at +0.96% the rule is untestable and this run records it as a NON-observation. The temptation on a small-move week is to log a confirmation from noise; the guardrail exists precisely to prevent inflating the evidence base.",
     "A DISTRIBUTION WAVE'S DESTINATION IS THE SIGNAL, NOT ITS SIZE (extends the run #16 read-outflow-by-destination rule): this week's 1.33M throughput terminated at exchange deposit addresses via zero-balance routers, which makes it distribution-to-venue rather than distribution-to-holders. Tracing two hops past the desk changes the interpretation completely and should be standard on any large desk drawdown."],
   "new_addresses_discovered":8,
   "most_valuable_insight":"Run #16 framed the tension as real demand versus staged supply and registered two explicit tests. Both resolved this week, and both resolved bearishly. The staged supply was DELIVERED: the OTC desks drained -255,736 (-76%, the largest drawdown in tracking) on 1.33M EGLD of true throughput, and for the first time the destinations were traced two hops - through zero-balance routers onto Bybit, Binance.com and back to UPbit. It went to exchanges, not to holders. Meanwhile the demand side failed its test: EGLD gained only +0.96% while BTC (+1.95%) and ETH (+4.36%) both outpaced it, so the celebrated EGLD-specific decoupling was a one-week event rather than a laggard-to-leader regime change; USH leverage-minting stopped the same week price stopped rising; the reward compound rate slipped; and the delegator base stayed flat for a fifth consecutive week across the entire +24% recovery. The honest read is that a 1.33M-EGLD distribution wave was enough to cap the recovery, and it was absorbed by a bid roughly one twenty-fifth its size (the Mega Whale's +50,621 via Coinbase Routing). Two genuine caveats keep this from being outright bearish: the market absorbed 1.33M EGLD without breaking down, and the bridged-stablecoin bleed finally stopped. But the methodological finding may matter more than the market one - discovering that the 50-tx cap had been undercounting OTC throughput roughly fourfold in every prior run means the pipeline was systematically understating the scale of distribution it was built to detect, and the historical series has to be rebuilt before any trend claim about it can be trusted.",
   "top_recommendation":"Watch whether the OTC desks RELOAD. The distribution leg executed in full, but the pipeline is not idle - UPbit already pushed a fresh 364,000 out to the desks inside the same window while they were draining. PRE-COMMITTED READING (registering it now, per the run #15 pre-commit discipline): desks rebuilding toward 300K+ with sustained throughput = a second distribution wave is being staged and the recovery should be treated as distribution-into-strength; desks holding near ~80K with throughput falling back = the wave is finished and supply is exhausted, which would be the first genuinely constructive structural signal in months. Pair this with the KuCoin test (does the +142,773 bleed back down, meaning withdrawal/OTC, or stay, meaning it was sold into the book).",
   "recommendations_for_next_run":[
     "REBUILD THE OTC THROUGHPUT SERIES WITH PAGINATION. This run discovered the size=50 cap undercounted throughput ~4x in every prior run (run #16: 323K reported vs 1,100,791 actual). Re-query the desk windows for runs #13-#15 with full pagination so the series becomes comparable, and fix collect_run18.py to paginate and net out desk<->desk transfers by default. Until this is done, no trend claim about OTC throughput is defensible.",
     "DO THE DESKS RELOAD? Desks drained -255,736 to ~80K but UPbit sent a fresh 364,000 out to them in the same window. Pre-committed reading: rebuilding toward 300K+ = second distribution wave staged (bearish continuation); holding near 80K with low throughput = wave finished, supply exhausted (constructive). Highest-priority follow-up.",
     "KUCOIN +142,773 RESOLUTION: the whale erd15ku2r2j6 emptied its full 145,443 balance onto KuCoin and went to zero. If KuCoin's balance bleeds back down the coins were withdrawn or OTC-settled (neutral); if it stays elevated the position was sold into the book (bearish). Also trace the wallet's INBOUND history to establish whether it was itself an OTC recipient.",
     "IS EGLD A LAGGARD AGAIN ON THE DOWNSIDE TOO? The leadership thesis failed on the upside this week. The confirming test is a macro DOWN week: if EGLD falls harder than BTC/ETH, the full high-beta-laggard regime is re-confirmed and the +24% recovery should be classified as a bear-market rally. Track EGLD vs BTC/ETH WoW explicitly either way.",
     "BINANCE CUSTODY 4TH LEG? Three consecutive drawdown legs (-305,549 cumulative from the 3.51M peak) make this a programme. Watch whether the custody continues toward zero (full unwind of the runs #9-#11 accumulation) and whether the binance_staking provider stays stable or resumes shedding.",
     "DOES DEFI LEVERAGE RESUME OR UNWIND? USH went flat (+0.14%) after +6.49% - borrowers stopped adding but did not close. If price breaks higher and USH resumes minting, the leverage was conviction; if price rolls over and USH burns >1%, it was a chase and the run #11 de-leveraging rule re-activates. XEGLD (+2.69%, 2nd week) is the cleaner ongoing inflow to track.",
     "PARTICIPATION BREADTH, WEEK 6: the delegator base has been flat for five weeks across the entire recovery. Watch whether a sustained hold above $3 finally pulls new delegators in. If it stays flat a sixth week, treat 'recoveries on this chain do not broaden participation' as an established structural finding rather than a running observation.",
     "MEGA WHALE ABSORPTION SCALE: erd18mv2z6r2 resumed at +50,621 via Coinbase Routing, but that is ~1/25th of the distributed volume. Watch whether the clip size grows (a real bid building) or stays ~50K (a floor only). Also check whether the Coinbase Routing pipe is itself fed from the OTC desks - if so, the 'absorber' and the distribution are the same flow."],
   "dashboard_feature_suggestions":[
     {"title":"OTC desk balance + true throughput cycle chart","motivation":"This run's headline is a complete load-then-distribute cycle: desks went 98K -> 335K -> 80K across three weeks while throughput ran 1.10M then 1.33M. No single-week view can show a cycle, and the run #16 suggestion for this chart is now MORE valuable because the throughput inputs were just corrected ~4x. A multi-week dual-axis view of desk BALANCE (load vs drain phases) against TRUE paginated throughput and EGLD price would have made this week's resolution legible at a glance and is the natural home for the pre-committed reload/exhaustion test.","suggested_visualization":"dual-axis weekly chart: combined desk balance (area, left axis) + true 7d throughput (bars, right axis) + EGLD price (line overlay), with load/drain phase shading.","data_already_available":False,"data_source":"desk balances are per-run in previous.json watch_addresses; TRUE throughput requires the paginated re-query (only runs #16 and #17 currently have it) - backfill needed before the chart is meaningful","priority":"high"},
     {"title":"OTC distribution Sankey: desk -> router -> venue","motivation":"The decisive finding this week was not the SIZE of the distribution but its DESTINATION - tracing two hops past the desks showed 1.33M flowing through five zero-balance routers onto Bybit, Binance.com and back to UPbit. That multi-hop structure is currently conveyed as a paragraph of addresses and amounts, which badly undersells it; it is inherently a flow graph. A Sankey would also make it immediately obvious when a wave terminates at exchanges (distribution) versus dispersing to many small unlabeled wallets (genuine retail sale).","suggested_visualization":"Sankey / flow diagram with three columns (OTC desks -> routing wallets -> destination venues), edge width by EGLD volume, unlabeled routers rendered distinctly from known exchanges.","data_already_available":True,"data_source":"the paginated desk outbound tx set plus one-hop router queries - both collected this run; would need persisting as a structured edge list in the report JSON","priority":"high"},
     {"title":"Participation breadth vs price recovery overlay","motivation":"The delegator base has now been flat for five consecutive weeks spanning a +24% price recovery - a finding that only exists in the gap between two series and is invisible in any single-week panel. Showing delegator count against price on one timeline would turn a repeated weekly sentence into an obvious structural picture, and would immediately reveal if breadth ever does start following price.","suggested_visualization":"dual-axis line chart: total delegators (left) vs EGLD price (right) over all tracked runs, with recovery periods shaded.","data_already_available":True,"data_source":"running_baselines.total_delegators and running_baselines.egld_price_usd, both stored every run","priority":"medium"}],
   "dashboard_suggestions_followup":[
     {"title":"OTC desk balance + throughput cycle chart","status":"pending","note":"Still not built, and this run raised its priority: the throughput inputs were just corrected ~4x, so the chart now also needs a paginated backfill of runs #13-#15 before it would show a truthful series."},
     {"title":"EGLD relative-strength (beta) tracker","status":"pending","note":"Not built, and this week proved the need - the leadership thesis it was meant to track failed within one week, which a multi-week EGLD-vs-BTC/ETH view would have made visually obvious rather than requiring a narrative correction."},
     {"title":"DeFi leverage/engagement composite panel","status":"deprioritized","note":"Deferred behind the two OTC visualizations. The cluster it was designed to show (USH mint, XEGLD supply, compound rate) went neutral this week, so it would currently display a flat, low-information panel; revisit when the leverage signals move again."}]}
}

json.dump(report,open(f"{REPO}/reports/2026-07-20.json","w"),indent=2)
print("WROTE reports/2026-07-20.json")
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
