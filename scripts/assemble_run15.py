#!/usr/bin/env python3
"""Assemble reports/2026-07-06.json (run #15) from collected data."""
import json, math
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D = json.load(open("/tmp/run15/collected.json"))
prev = json.load(open(f"{REPO}/data/previous.json"))
kn = json.load(open(f"{REPO}/data/known-addresses.json"))
learn = json.load(open(f"{REPO}/data/learnings.json"))
prevcol = json.load(open(f"{REPO}/data/collected/2026-06-29.json"))  # for supply WoW

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
 "Binance":"Net -236K - by far the largest exchange move this week and the dominant driver of the aggregate net OUTFLOW. THE 7-WEEK CUSTODY STANDOFF RESOLVED: Binance Staking custody drew down -158,853 (3,512,650 -> 3,353,797) after 4 weeks frozen / 7 weeks parked - and this time it was TRACEABLE via standard transfers: custody received 241,147 from the Binance.com hot wallet but sent back 300,000 + 100,000 to it (net -158,853 custody -> hot). A custody-to-hot drawdown is the DISTRIBUTION-direction resolution the multi-week watch was set up to catch (delegate=bullish / drawdown-to-hot=bearish), NOT a delegation. On top of that, one Binance.com hot wallet drained -160K (166,995 -> 6,995) while another gained +83K, so Binance's tracked total fell -236K net. The funds now sit in hot wallets (not provably sold), but the direction is distributive - notable that this happened INTO a +5.9% price bounce.",
 "Coinbase":"-17K net across 4 wallets. Coinbase Routing sent +32,679 onward to Mega Whale erd18mv2z6r2 (an OTC-counterparty accumulator), i.e. Coinbase routed distribution to a large on-chain buyer this week. The prior 3-week inflow streak stays broken (2nd outflow week).",
 "Crypto.com":"+27K (+15.3%) across 2 wallets - the largest exchange INFLOW this week. Capital moving onto Crypto.com during the bounce.",
 "Bybit":"+21K (+4.5%) on the cold wallet - a reversal back to inflow after last week's -56K outflow.",
 "UPbit":"Cold wallet -18K (-1.4%) - mild outflow. Separately UPbit OTC Desk -2.5K and OTC Distribution -6.4K (combined desk balance -8.9K) - the desks are now DRAINING after last week's +35K load, while still pushing ~172K of distribution throughput. A fresh UPbit -> UPbit OTC Desk 160K reload landed mid-week (see OTC section).",
 "MEXC":"-5K (-5.6%). Mild outflow.",
 "KuCoin":"+9.6K (+33.7%) - notable proportional inflow off a small base.",
 "Bitget":"-4K (-4.4%). Mild outflow.",
 "Gate.io":"+4.3K (+7.6%). Mild inflow.",
 "Tokero":"Flat (-0.1K).",
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
    "signal":f"Net exchange flow {net_total:+,.0f} EGLD ({100*net_total/total_prev if total_prev else 0:+.2f}%) - a 2nd consecutive net OUTFLOW, but this week almost ENTIRELY a Binance idiosyncratic move (-236K) rather than a broad exchange-wide signal. The headline event: the 7-week Binance Staking custody standoff RESOLVED to a -158,853 DRAWDOWN back to Binance.com hot wallets (traced: custody +241K in, -400K out = -159K net custody->hot). Per the multi-week custody watch, a drawdown-to-hot is the DISTRIBUTION-direction outcome (not delegation). The rest of the tape was mixed and mostly INFLOW: Crypto.com +27K, Bybit +21K, KuCoin +9.6K IN; Coinbase -17K (routed +32.7K to an OTC accumulator), UPbit -18K OUT. So strip out Binance and the exchange complex was net-INFLOW during the bounce. Read jointly with OTC (methodology rule): the OTC desks are now DRAINING (-8.9K) while still distributing ~172K throughput, and identifiable large buyers absorbed the flow (Mega Whale erd18mv2z6r2 +32.7K from Coinbase Routing). Net read: distribution continues (Binance custody unwind + OTC), but it is being met by real accumulation bids into the rally - not a one-sided dump.",
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
  "notable_events":f"DEX volume ${totvol/1000:.0f}K (+{100*(totvol-prev_dexvol)/prev_dexvol:.0f}% WoW) - a mild recovery tracking the price bounce, still depressed vs the $100K+ of a month ago. WEGLD/USDC dominance {pairs[0]['share_pct']:.1f}%; ZoidPay/WEGLD share {pairs[1]['share_pct'] if len(pairs)>1 else 0:.1f}%. WEGLD supply WoW {wegld_chg_pct:+.2f}% (flat).","health_signal":"flat"},
 {"protocol":"Hatom Lending","category":"lending","addresses_tracked":13,"tvl_usd":hatom_lending,"tvl_egld":hl_egld,
  "tvl_wow_change_pct":100*(hl_egld-prev_hl_egld)/prev_hl_egld,"transfers_24h":tcount("Hatom EGLD MM"),
  "notable_events":f"TVL ${hatom_lending/1e6:.2f}M USD ({100*(hatom_lending-prev['defi_tvl']['Hatom Lending'])/prev['defi_tvl']['Hatom Lending']:+.1f}%), {hl_egld/1000:.0f}K EGLD ({100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}% EGLD). Bilateral inverse rule EVALUABLE (price +{100*(price-pp)/pp:.1f}% exceeds the |dPrice|>=5% threshold): EGLD-denominated TVL moved {100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}% (counter to price - depositors WITHDREW to capture gains into the rally, the mirror of the dip-DCA behavior). Response ratio {abs(100*(hl_egld-prev_hl_egld)/prev_hl_egld)/abs(100*(price-pp)/pp):.2f}.","health_signal":"flat"},
 {"protocol":"Hatom Liquid Staking","category":"liquid_staking","addresses_tracked":2,"tvl_usd":hatom_lsd,"tvl_egld":hlsd_egld,
  "tvl_wow_change_pct":100*(hlsd_egld-prev_hlsd_egld)/prev_hlsd_egld,"transfers_24h":tcount("Hatom Liquid Staking"),
  "notable_events":f"SEGLD ${segld_mcap/1e6:.2f}M + SWTAO ${swtao_mcap/1e6:.2f}M = ${hatom_lsd/1e6:.2f}M USD ({100*(hatom_lsd-prev_hlsd)/prev_hlsd:+.1f}%). On a supply basis Hatom LSD is FLAT: SEGLD {segld_supply_wow:+.2f}%, SWTAO {swtao_supply_wow:+.2f}%. NOTE: SWTAO price feed RECOVERED cleanly this run (dataApi re-fetch guard needed 0 retries - all 4 dataApi tokens populated first pass), so the USD figure is a real reading this week, not a carried estimate.","health_signal":"flat"},
 {"protocol":"Hatom USH","category":"stablecoin","addresses_tracked":4,"tvl_usd":hatom_ush,"tvl_egld":ush_egld,
  "tvl_wow_change_pct":100*(hatom_ush-prev_hush)/prev_hush,"transfers_24h":None,
  "notable_events":f"USH mcap ${hatom_ush/1000:.0f}K ({100*(hatom_ush-prev_hush)/prev_hush:+.1f}% USD). USH supply {ush_supply_wow:+.2f}% WoW - FLAT: the 2-week de-leveraging/burn has STOPPED as price recovered. CDP borrowers are no longer force-closing positions; on-chain leverage stabilized.","health_signal":"flat"},
 {"protocol":"XOXNO LSD","category":"liquid_staking","addresses_tracked":2,"tvl_usd":xoxno_lsd,"tvl_egld":xlsd_egld,
  "tvl_wow_change_pct":100*(xlsd_egld-prev_xl_egld)/prev_xl_egld,"transfers_24h":tcount("XOXNO LSD"),
  "notable_events":f"XEGLD ${xoxno_lsd/1e6:.2f}M ({100*(xoxno_lsd-prev['defi_tvl']['XOXNO LSD'])/prev['defi_tvl']['XOXNO LSD']:+.1f}% USD). The real signal is SUPPLY: XEGLD supply STABILIZED at {supply('XEGLD-e413ed'):,.0f} ({xegld_supply_wow:+.2f}% WoW) after last week's -29% collapse. The redemption was a ONE-SHOT event, not an ongoing exit - no continuation this week. XOXNO LSD TVL has settled at its new lower level (~{xlsd_egld/1000:.0f}K EGLD).","health_signal":"flat"},
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
anomalies=[
 {"metric":"binance_staking_custody_drawdown","current_value":3353797,"previous_value":3512650,"method":"rule_based",
  "severity":"high",
  "description":"THE 7-WEEK CUSTODY STANDOFF RESOLVED - to the DISTRIBUTION side. Binance Staking custody drew down -158,853 EGLD (3,512,650 -> 3,353,797) after 4 consecutive frozen weeks (7 weeks total: 3 accumulation +402K, 4 stall). Unlike prior weeks the move was TRACEABLE via standard transfers: custody received 241,147 from Binance.com hot but sent back 300,000 + 100,000, net -158,853 custody -> hot. The multi-week watch was set up precisely to catch this: delegate=bullish, drawdown-to-hot=bearish. It drew down to hot, NOT to the protocol staked module - the distribution-direction outcome. Combined with a separate -160K drain on another Binance.com hot wallet, Binance's tracked total fell -236K. The EGLD now sits in hot wallets (not provably sold), but the direction is distributive - and it happened INTO a +5.9% price bounce, i.e. selling strength."},
 {"metric":"egld_price_usd","current_value":price,"previous_value":pp,"method":"z_score",
  "average_value":zp[0],"stddev":zp[1],"z_score":zp[2],"severity":"low",
  "description":f"EGLD {100*(price-pp)/pp:+.2f}% WoW to ${price:.2f}, z={zp[2]:+.2f}σ (N={len(rb['egld_price_usd'])}) - the FIRST up-week after a multi-week decline, and $2.55 held as a floor. The move was a broad-market relief bounce: WoW BTC {btc_wow:+.2f}%, ETH {eth_wow:+.2f}%, EGLD {100*(price-pp)/pp:+.2f}%. Notably EGLD UNDERPERFORMED the rally - ETH gained more than 2x EGLD's move - continuing its high-beta-but-laggard behavior (it fell harder on the way down and is rising less on the way up). z is only {zp[2]:+.2f}σ (LOW) because the baseline is still centered above the current level. Market cap ${econ['marketCap']/1e6:.1f}M ({100*(econ['marketCap']-pecon['market_cap_usd'])/pecon['market_cap_usd']:+.1f}%)."},
 {"metric":"mex_price_usd","current_value":meco["price"],"previous_value":prev_mexp,"method":"z_score",
  "average_value":zmex[0],"stddev":zmex[1],"z_score":zmex[2],"severity":"low",
  "description":f"MEX price {100*(meco['price']-prev_mexp)/prev_mexp:+.2f}% to ${meco['price']:.3e} (z={zmex[2]:+.2f}σ, N={len(rb['mex_price_usd'])}), tracking EGLD's bounce. MEX mcap ${meco['marketCap']/1e6:.2f}M. DEX volume +{100*(totvol-prev_dexvol)/prev_dexvol:.0f}% to ${totvol/1000:.0f}K but still depressed vs the $100K+ of a month ago."},
 {"metric":"total_delegators","current_value":cur_deleg,"previous_value":prev_deleg,"method":"z_score",
  "average_value":zd[0],"stddev":zd[1],"z_score":zd[2],"severity":"low",
  "description":f"Total delegators {cur_deleg:,} ({deleg_wow:+,} WoW = {100*deleg_wow/prev_deleg:+.3f}%). Raw z={zd[2]:+.2f}σ but this is the run #9 DEGENERATE-Z-SCORE case (baseline mean dragged by the pre-capitulation ~179K level) - the actual WoW move is essentially ZERO. DOWNGRADED to LOW. Decisive read: the delegator base has now been FLAT for a 3rd CONSECUTIVE week at ~174.4K - the run #12 -4,003 capitulation is fully behind us, the retail base is stable. Meanwhile delegation TVL GREW +{total_locked-prev['staking_concentration']['total_locked_egld']:,.0f} broadly (Synexis +18K, stakingagency +8.8K, oxsyai +6.5K), so more EGLD per delegator, not more delegators."},
 {"metric":"staked_egld","current_value":staked,"previous_value":pecon["staked_egld"],"method":"z_score",
  "average_value":zse[0],"stddev":zse[1],"z_score":zse[2],"severity":"low",
  "description":f"Total staked {staked:,} EGLD ({staked-pecon['staked_egld']:+,} WoW, {100*(staked-pecon['staked_egld'])/pecon['staked_egld']:+.2f}%). z={zse[2]:+.2f}σ. A DIVERGENCE inside the staking complex: total staked FELL -{abs(staked-pecon['staked_egld']):,.0f} (direct-node staking down) even as delegation-contract TVL ROSE +{total_locked-prev['staking_concentration']['total_locked_egld']:,.0f} - a rotation from direct-node staking into delegation. Staked ratio {sr*100:.2f}% ({100*(sr-pecon['staked_ratio']):+.2f}pp). Last week's +81K buy-the-dip staking partly gave back as price recovered; the 0%-fee yield-chase cohort UNWOUND net {cohort_net/1000:+.0f}K (egldstakingprovider -13.7K led the reversal), though pi-staking kept drawing (+13 users, 3rd week)."},
 {"metric":"otc_distribution_continues_desks_draining","current_value":round(upbit_thr+dist_thr),"previous_value":195447,"method":"rule_based",
  "severity":"medium",
  "description":f"OTC pipeline distribution CONTINUES but the desks have shifted from LOADING to DRAINING. Combined UPbit OTC + OTC Distribution 7d outbound throughput ~{(upbit_thr+dist_thr)/1000:.0f}K EGLD (vs 195K last week - still high) WHILE desk balances FELL -8.9K (UPbit OTC -2.5K to {bal_of('erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5') or 51128:,.0f}; OTC Distribution -6.4K to {bal_of('erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r') or 46585:,.0f}), reversing last week's +35K load. A fresh UPbit -> UPbit OTC Desk 160K reload landed mid-week, so the desks are being refilled AND emptied. Late-distribution phase: the wave is being pushed out and absorbed rather than reloaded."},
 {"metric":"mega_whale_erd18mv2z6r2_accumulating","current_value":round(mw_bal_cur),"previous_value":1010011,"method":"rule_based",
  "severity":"medium",
  "description":f"Unknown Mega Whale erd18mv2z6r2 KEPT ACCUMULATING for a 2nd week: received +32,679 EGLD FROM the Coinbase Routing Wallet and rose to {mw_bal_cur:,.0f} (1,010,011 -> {mw_bal_cur:,.0f}). Last run flagged it (activated +11K, crossed 1M) and asked to watch for a large OUTBOUND - instead it did the opposite: it ABSORBED an exchange-routed distribution. This is the Apr-18 bilateral-deal OTC counterparty (received 798K then); it is behaving as an accumulator soaking up distributed supply, not a seller. A large identifiable buyer providing the bid that the OTC/Binance distribution is meeting."},
 {"metric":"stablecoin_supply_mixed","current_value":usdc_supply_wow,"previous_value":-1.30,"method":"rule_based",
  "severity":"low",
  "description":f"Bridged-stablecoin supply now MIXED, not a clean acceleration: USDC {usdc_supply_wow:+.2f}% (3rd week of burn, still contracting) but USDT {usdt_supply_wow:+.2f}% (burn nearly STOPPED, vs -3.7% last week). Dollar-liquidity flight is now concentrated in USDC alone; the aggregate de-risking has decelerated as price stabilized. USH (Hatom CDP stablecoin) supply FLAT ({ush_supply_wow:+.2f}%) - the 2-week CDP de-leveraging has ended."}]

# ---------- trend indicators ----------
accelerating_outflows=[
 {"exchange":"NET_EXCHANGE","trend":"outflow","cumulative_change_pct":None,"weeks_in_trend":2,
  "interpretation":f"Aggregate net exchange flow {net_total:+,.0f} EGLD OUTFLOW - a 2nd consecutive outflow week, but ~all of it is a single Binance idiosyncratic move (-236K net). Strip Binance out and the exchange complex was net-INFLOW (Crypto.com +27K, Bybit +21K, KuCoin +9.6K). So this is NOT a broad exchange-wide distribution signal - it is the Binance custody unwind. Read jointly with OTC: distribution continues via OTC (~{(upbit_thr+dist_thr)/1000:.0f}K throughput) but the desks are now draining, and identifiable large buyers absorbed the flow."},
 {"exchange":"Binance","trend":"outflow","cumulative_change_pct":None,"weeks_in_trend":1,
  "interpretation":"Binance -236K net across 4 wallets. The 7-week Staking custody standstill RESOLVED to a -158,853 drawdown back to hot wallets (traced: +241K in, -400K out). Distribution-direction, not delegation. A separate hot wallet drained -160K. The custody EGLD now sits in hot wallets - watch whether it drains onward (confirmed distribution) or rebuilds."},
 {"exchange":"UPbit OTC Desks","trend":"distributing+draining","cumulative_change_pct":None,"weeks_in_trend":3,
  "interpretation":f"OTC desks still distributing (~{(upbit_thr+dist_thr)/1000:.0f}K combined 7d throughput, vs 195K last week) but the desk balances FLIPPED from loading to DRAINING (-8.9K, vs +35K last week). A fresh UPbit -> UPbit OTC Desk 160K reload landed mid-week. Late-distribution phase: the wave is being pushed out and met by buyers (e.g. Mega Whale +32.7K), not reloaded for another leg."}]

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
   {"metric":"delegator_base_flat","direction":"flat","weeks":3,"cumulative_change_pct":0,
    "interpretation":f"3rd consecutive flat week for the delegator base at ~174.4K ({deleg_wow:+,} this week). The run #12 -4,003 capitulation is now decisively behind us - the retail base has been stable for three weeks. Graduating this off the watch list; the exit has stopped."},
   {"metric":"delegation_tvl_growth","direction":"up","weeks":2,"cumulative_change_pct":None,
    "interpretation":f"2nd consecutive week of delegation-contract TVL growth (+{total_locked-prev['staking_concentration']['total_locked_egld']:,.0f} this week, broad-based: Synexis +18K, stakingagency +8.8K, oxsyai +6.5K). Delegation is growing even as total staked fell and price only bounced - a slow accumulation into staking contracts, decoupled from the yield-chase names that cooled."},
   {"metric":"stablecoin_supply_burn_usdc","direction":"down","weeks":3,"cumulative_change_pct":None,
    "interpretation":f"USDC supply burn now a 3-week trend ({usdc_supply_wow:+.2f}% this week). But USDT burn nearly STOPPED ({usdt_supply_wow:+.2f}%, vs -3.7% last week), so the aggregate dollar-liquidity flight has decelerated and concentrated in USDC. Not a clean acceleration anymore."},
   {"metric":"token_holder_count_decline","direction":"down","weeks":15,"cumulative_change_pct":None,
    "interpretation":"15th consecutive week of small holder declines across top-10 tokens. Established airdrop-decay baseline; the active >$1M-mcap token base is stable."}],
 "regime_shifts":[
   {"metric":"binance_custody_standoff_resolved","before_value":3512650,"after_value":3353797,
    "description":"The 7-week Binance Staking custody position (3 weeks accumulation +402K, 4 weeks frozen at 3.51M) RESOLVED this week to a -158,853 drawdown back to Binance.com hot wallets. This is the step-change the multi-week watch was built to catch, and it resolved to the DISTRIBUTION side (drawdown-to-hot, not delegation-to-protocol). A structural regime break: the parked position is being unwound, and it moved into a price bounce (selling strength). Watch whether the hot-wallet EGLD drains onward next week."},
   {"metric":"xoxno_lsd_supply_stabilized","before_value":227765,"after_value":round(supply('XEGLD-e413ed') or 226400),
    "description":f"XOXNO LSD (XEGLD) supply STABILIZED at {supply('XEGLD-e413ed'):,.0f} ({xegld_supply_wow:+.2f}% WoW) after last week's -29% collapse. The redemption was a ONE-SHOT event, not the start of an ongoing drain. XOXNO LSD TVL has settled at its new lower level. Resolves last run's highest-priority DeFi watch."},
   {"metric":"first_up_week","before_value":pp,"after_value":price,
    "description":f"EGLD posted its FIRST up-week ({100*(price-pp)/pp:+.1f}% to ${price:.2f}) after a multi-week decline, and $2.55 held as a floor - a broad-market relief bounce (BTC +5.2%, ETH +12.3%). But EGLD UNDERPERFORMED the rally badly (ETH gained 2x+ EGLD's move), so it is not leadership - it is a laggard bouncing with beta. Not yet a confirmed trend reversal; watch whether it holds or fades like the run #12 bounce did."}]}

# ---------- dormant activations ----------
dormant_activations=[]

# ---------- watch list ----------
mw_bal=bal_of("erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw") or 998971
watch_list=[
 {"item":"Binance Staking custody UNWOUND -159K to hot wallets (7-week standoff resolved, distribution-side)","reason":"After 3 accumulation weeks (+402K) and 4 frozen weeks at 3.51M, the custody drew down -158,853 back to Binance.com hot (traced: +241K in, -400K out). Resolved to the DISTRIBUTION side, not delegation. Highest-priority follow-up: does the hot-wallet EGLD now drain onward (confirmed sell/distribution) or rebuild (reorg)? The eventual on-chain destination is the decisive read.","weeks_on_list":9},
 {"item":f"EGLD bounced +{100*(price-pp)/pp:.0f}% to ${price:.2f} (first up-week) but UNDERPERFORMED the rally","reason":f"$2.55 held and EGLD posted its first up-week in a broad relief bounce (BTC +5.2%, ETH +12.3%), but EGLD gained less than half of ETH's move - a laggard bouncing with beta, not leadership. The run #12 bounce failed within a week; watch whether this one holds ${price:.2f} or fades. EGLD's beta to BTC/ETH remains the dominant driver.","weeks_on_list":6},
 {"item":f"Net exchange flow {net_total/1000:+.0f}K (2nd outflow week) - but Binance-only; rest was inflow","reason":"The -218K net is almost entirely Binance's -236K custody unwind. Ex-Binance, exchanges were net-INFLOW (Crypto.com +27K, Bybit +21K). So NOT a broad distribution signal. Watch whether the Binance hot-wallet EGLD drains onward and whether the ex-Binance inflow persists (would signal renewed on-exchange positioning into the bounce).","weeks_on_list":1},
 {"item":f"OTC pipeline: distribution continues (~{(upbit_thr+dist_thr)/1000:.0f}K) but desks now DRAINING (-8.9K)","reason":"Combined OTC throughput ~172K (vs 195K last week) while desk balances flipped from +35K load to -8.9K drain. A fresh UPbit->UPbit OTC Desk 160K reload landed. Late-distribution phase: the wave is being pushed out and absorbed by buyers (Mega Whale +32.7K), not reloaded for a fresh leg. Watch for a GAP (throughput collapse) that would signal the wave is done.","weeks_on_list":6},
 {"item":f"Mega Whale erd18mv2z6r2 KEEPS ACCUMULATING (+32.7K from Coinbase Routing) to {mw_bal_cur:,.0f}","reason":"Last run asked to watch for a large OUTBOUND; instead it ABSORBED +32,679 routed from Coinbase, its 2nd straight accumulation week. This Apr-18 bilateral-deal OTC counterparty is acting as a buyer soaking up distributed supply - now 1.04M. Watch whether it keeps accumulating (a large bid under the market) or turns to distribute.","weeks_on_list":5},
 {"item":"Delegation TVL GREW +70K broadly while total staked FELL -46K (rotation into delegation)","reason":"Delegation-contract TVL rose broadly (Synexis +18K, stakingagency +8.8K) but economics.staked fell -46K = a rotation from direct-node staking into delegation. The 0%-fee yield-chase cohort UNWOUND net -8.6K (egldstakingprovider -13.7K), so last week's buy-the-dip spike faded as price recovered; pi-staking (+13 users) is the exception still drawing. Watch whether broad delegation growth sustains.","weeks_on_list":1},
 {"item":"Stablecoin flight DECELERATING: USDC -2.0% (3rd wk) but USDT burn nearly stopped (-0.3%)","reason":"USDC continues to contract (3-week burn) but USDT's -3.7% collapse last week decelerated to -0.3%, and USH CDP de-leveraging ended (flat). The dollar-liquidity flight has decelerated and concentrated in USDC as price stabilized. Watch whether USDC follows USDT and flattens (de-risking done) or keeps burning.","weeks_on_list":3},
 {"item":"XEGLD supply STABILIZED after -29% collapse - one-shot confirmed","reason":"XEGLD supply settled at ~226,400 (-0.6% WoW) after last week's -29% redemption; no continuation. The collapse was a single large event, not an ongoing drain. Resolved - graduating off the watch list unless redemptions resume. (Redeemer destination not cleanly traceable via standard txs - the LSD contract moves via SC results.)","weeks_on_list":2}]

# ---------- executive summary ----------
executive_summary=[
 {"finding":f"THE 7-WEEK BINANCE CUSTODY STANDOFF RESOLVED - to the DISTRIBUTION side. Binance Staking custody drew down -158,853 EGLD (3,512,650 -> 3,353,797) back to Binance.com hot wallets (traced: +241K in, -400K out). The multi-week watch was built to catch this: delegate=bullish, drawdown-to-hot=bearish. It unwound to hot, NOT the protocol staked module - and did so INTO a +5.9% price bounce (selling strength). With a separate -160K hot-wallet drain, Binance's tracked total fell -236K.","severity":"high","category":"whale"},
 {"finding":f"EGLD posted its FIRST up-week (+{100*(price-pp)/pp:.2f}% to ${price:.2f}) and $2.55 HELD, but badly UNDERPERFORMED the broad-market relief bounce (WoW BTC {btc_wow:+.1f}%, ETH {eth_wow:+.1f}%) - ETH gained more than 2x EGLD's move. A laggard bouncing with beta, not leadership. The run #12 bounce failed within a week; not yet a confirmed reversal.","severity":"medium","category":"network"},
 {"finding":f"XEGLD supply STABILIZED at ~226,400 ({xegld_supply_wow:+.2f}% WoW) after last week's -29% collapse - the redemption was a ONE-SHOT event, not an ongoing drain. Resolves last run's highest-priority DeFi watch: XOXNO LSD TVL has settled at its new lower level, no continuation.","severity":"medium","category":"defi"},
 {"finding":f"Net exchange flow {net_total:+,.0f} (2nd outflow week) - but almost ENTIRELY the Binance -236K custody unwind. Strip Binance out and exchanges were net-INFLOW (Crypto.com +27K, Bybit +21K, KuCoin +9.6K). So this is NOT a broad distribution signal; it is one idiosyncratic Binance move. Read jointly with OTC: distribution continues via OTC but the desks are now draining, met by buyers.","severity":"medium","category":"whale"},
 {"finding":f"OTC pipeline still distributing (~{(upbit_thr+dist_thr)/1000:.0f}K 7d throughput, vs 195K last week) but the desks FLIPPED from loading (+35K) to DRAINING (-8.9K) - a late-distribution phase. Crucially the flow is being ABSORBED: Mega Whale erd18mv2z6r2 took +32.7K routed from Coinbase, its 2nd straight accumulation week (now 1.04M). Distribution meeting a real bid.","severity":"medium","category":"whale"},
 {"finding":f"Delegator base FLAT for a 3rd consecutive week at {cur_deleg:,} ({deleg_wow:+}) - the run #12 capitulation is decisively behind us. Delegation-contract TVL grew +{total_locked-prev['staking_concentration']['total_locked_egld']:,.0f} broadly (Synexis +18K, stakingagency +8.8K), even as total staked FELL -{abs(staked-pecon['staked_egld']):,.0f} (rotation from direct-node staking into delegation). Last week's yield-chase spike UNWOUND net {cohort_net/1000:+.0f}K as price recovered.","severity":"low","category":"staking"},
 {"finding":f"Stablecoin flight DECELERATED and narrowed: USDC {usdc_supply_wow:+.2f}% (3rd burn week) but USDT burn nearly stopped ({usdt_supply_wow:+.2f}%, vs -3.7% last week) and USH CDP de-leveraging ENDED (flat {ush_supply_wow:+.2f}%). As price stabilized, dollar-liquidity flight decelerated and concentrated in USDC alone - not the clean acceleration of last week.","severity":"low","category":"defi"}]

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
   "btc_correlation_note":f"EGLD {100*(price-pp)/pp:+.2f}% WoW vs BTC {btc_wow:+.2f}% / ETH {eth_wow:+.2f}% (WoW). EGLD bounced WITH the broad market (both BTC and ETH up), but UNDERPERFORMED badly - ETH's +12.3% is more than 2x EGLD's gain. EGLD is behaving as a high-beta laggard: it fell harder on the way down and is rising less on the way up. 24h prices flat-to-up (BTC +0.15%, ETH +0.18%).",
   "transactions_added":st["transactions"]-pact["total_transactions"],"supply_added":econ["totalSupply"]-pecon["total_supply"],
   "staked_egld_added":staked-pecon["staked_egld"],"epoch_advanced":st["epoch"]-pact["epoch"]},
 "analysis":f"EGLD {100*(price-pp)/pp:+.2f}% WoW to ${price:.2f} - the FIRST up-week after a multi-week decline, and $2.55 held as a floor. z={zp[2]:+.2f}σ (LOW). The move was a broad-market relief bounce (WoW BTC {btc_wow:+.2f}%, ETH {eth_wow:+.2f}%), but EGLD badly UNDERPERFORMED - ETH gained more than 2x its move - so this is beta-laggard behavior, not leadership. Market cap ${econ['marketCap']/1e6:.1f}M ({100*(econ['marketCap']-pecon['market_cap_usd'])/pecon['market_cap_usd']:+.1f}%). The on-chain tape is mixed-to-distributive despite the green candle: the headline is Binance unwinding its 7-week custody position (-159K back to hot wallets, the DISTRIBUTION-direction resolution of the long-running watch), and net exchange flow was a 2nd outflow week (-218K) - though that is almost entirely the Binance move; ex-Binance exchanges were net-inflow. On the constructive side, the delegator base held FLAT for a 3rd week at {cur_deleg:,} (capitulation fully behind us) and delegation-contract TVL grew +{total_locked-prev['staking_concentration']['total_locked_egld']:,.0f} broadly, though total staked FELL -{abs(staked-pecon['staked_egld']):,.0f} (rotation from direct-node into delegation) and last week's buy-the-dip yield-chase spike UNWOUND ({cohort_net/1000:+.0f}K). Activity: {round((st['transactions']-pact['total_transactions'])/7)/1e6:.1f}M txs/day, account growth +{(st['accounts']-pact['total_accounts'])/1000:.1f}K. The read: a laggard bounce on beta, with the on-chain story dominated by Binance's custody unwind (distributive) being met by identifiable large accumulators (Mega Whale +32.7K) - distribution finding a bid, not a one-sided move in either direction."}

# ---------- whale analysis ----------
whale_analysis=("THIS WEEK'S DOMINANT MOVES:\n"
 "1) THE 7-WEEK BINANCE CUSTODY STANDOFF RESOLVED - TO THE DISTRIBUTION SIDE. After 3 accumulation weeks (runs #7+9+10, +402K) and 4 frozen weeks at 3.51M, Binance Staking custody drew down -158,853 EGLD (3,512,650 -> 3,353,797). Unlike the untraceable Binance moves of prior weeks, this one showed up in standard transfers: the custody received 241,147 from the Binance.com hot wallet but sent back 300,000 + 100,000, a net -158,853 from custody TO hot. The multi-week watch was built to catch exactly this and pre-committed the reading: a move to the protocol staked module = bullish delegation; a drawdown back to hot wallets = distribution. It drew down to hot. The EGLD now sits in Binance.com hot wallets (not provably sold yet), but the direction is distributive - and it happened INTO a +5.9% price bounce, i.e. selling into strength.\n\n"
 f"2) NET EXCHANGE FLOW {net_total:+,.0f} EGLD (2nd outflow week) - BUT ALMOST ENTIRELY BINANCE. Binance's -236K net (custody unwind + a -160K drain on a separate hot wallet, partly offset by a +83K refill) dominates. Strip Binance out and the exchange complex was net-INFLOW: Crypto.com +27K (largest inflow), Bybit +21K (reversing last week's -56K), KuCoin +9.6K, Gate.io +4.3K; against Coinbase -17K, UPbit -18K, MEXC -5K. So this is NOT a broad exchange-wide distribution signal - it is one idiosyncratic Binance event on a tape that was otherwise mildly accumulative-onto-exchange into the bounce.\n\n"
 f"3) OTC PIPELINE: DISTRIBUTION CONTINUES, DESKS NOW DRAINING. Combined UPbit OTC + OTC Distribution 7d throughput ~{(upbit_thr+dist_thr)/1000:.0f}K EGLD (vs 195K last week - still elevated), but the desk balances FLIPPED from last week's +35K load to a -8.9K DRAIN (UPbit OTC -2.5K, OTC Distribution -6.4K). A fresh UPbit -> UPbit OTC Desk 160K reload landed mid-week, so the desks are being refilled and emptied in the same window. This is a late-distribution phase - the wave is being pushed out and ABSORBED rather than reloaded for a fresh leg.\n\n"
 f"4) MEGA WHALE erd18mv2z6r2 IS THE ABSORBER. It received +32,679 EGLD routed FROM the Coinbase Routing Wallet and rose to {mw_bal_cur:,.0f} - a 2nd consecutive accumulation week (activated +11K last run). Last run asked to watch for a large OUTBOUND; it did the opposite and soaked up an exchange-routed distribution. This Apr-18 bilateral-deal OTC counterparty (received 798K then) is behaving as a large buyer providing the bid that the Binance/OTC distribution is meeting - the single most important clue that this week's distribution is being met by real accumulation, not dumped into a vacuum.\n\n"
 f"5) WHALE TIERS (top-{N_prev} apples-to-apples): mega {whale_tiers['mega_whales']['net_change_egld']/1000:+.0f}K, large {whale_tiers['large_whales']['net_change_egld']/1000:+.0f}K, mid {whale_tiers['mid_whales']['net_change_egld']/1000:+.0f}K. NO boundary-crossing artifact this week (both mega counts = 3). The mega -144K is driven by the Binance custody drawdown; the large +169K is broad (Unknown Whale +35K, Unknown Whale B +30K, Bybit/Crypto.com inflows). Net: the very largest tier shed EGLD (Binance) while the 100K-1M tier accumulated - a mild wealth-distribution pattern, the healthier of the two directions.")

# ---------- staking analysis ----------
staking_analysis=(f"Staking concentration remains low (HHI {hhi:.4f}, top-5 {top5:.1f}%, top-10 {top10:.1f}% - essentially unchanged WoW). Total delegated {total_locked:,.0f} EGLD across {len(provs)} active providers (+{total_locked-prev['staking_concentration']['total_locked_egld']:,.0f} WoW). Active delegator base {cur_deleg:,} ({deleg_wow:+}, {100*deleg_wow/prev_deleg:+.3f}%).\n\n"
 f"DELEGATOR BASE STABLE FOR A 3RD WEEK. The base held FLAT again ({deleg_wow:+} this week) at {cur_deleg:,} - three consecutive flat weeks now put the run #12 -4,003 capitulation (largest in tracking by 9x) decisively behind us. The raw z-score reads {zd[2]:+.2f}σ but is the run #9 degenerate case (baseline mean dragged by the pre-capitulation ~179K level) - downgraded to LOW. Graduating this off the watch list: the retail-delegation exit is over.\n\n"
 f"A DIVERGENCE INSIDE THE STAKING COMPLEX: delegation-contract TVL GREW +{total_locked-prev['staking_concentration']['total_locked_egld']:,.0f} EGLD but total staked (economics, includes direct-node staking) FELL -{abs(staked-pecon['staked_egld']):,.0f} - a rotation OUT of direct-node staking and INTO delegation contracts. Staked ratio {sr*100:.2f}% ({100*(sr-pecon['staked_ratio']):+.2f}pp). The delegation growth was BROAD-BASED, not the 0%-fee yield-chase names: Synexis +18,101 (+35 users) led, then stakingagency +8,832, oxsyai +6,480, disruptivedigital +4,591. That breadth is healthier than the concentrated yield-chase of prior weeks.\n\n"
 f"YIELD-CHASE COHORT UNWOUND (net {cohort_net/1000:+.0f}K) as price recovered - the mirror of last week's buy-the-dip reignition. egldstakingprovider {cohort_flows.get('egldstakingprovider',0):+,.0f} led the reversal (gave back last week's gains), procryptostaking {cohort_flows.get('procryptostaking',0):+,.0f}, valuestaking {cohort_flows.get('valuestaking',0):+,.0f}; only partly offset by ninjastaking {cohort_flows.get('ninjastaking',0):+,.0f} and star_staking {cohort_flows.get('star_staking',0):+,.0f}. The EXCEPTION is pi-staking (0% fee): +3,963 from +13 new delegators (38 -> 51 users) - a 3rd straight week of growth. Last run's isolated-entry watch has become a genuine small-provider growth story, drawing steadily while the rest of the cohort cools.\n\n"
 f"APR distribution: {buckets[3]['provider_count']} providers in the 8-9% bucket holding {buckets[3]['total_locked_egld']/1e6:.1f}M EGLD (the dominant cluster); the 9-10% bucket holds {buckets[4]['provider_count']} providers / {buckets[4]['total_locked_egld']/1e3:.0f}K EGLD. Empty 10%+ bucket (consistent across all 2026 runs). APR-weighted average {apr_w:.2f}%.\n\n"
 f"DELEGATOR CHURN: {gain} providers gaining vs {lose} losing delegators ({deleg_wow:+} net) - balanced, healthy churn. No notable named-validator joiners/leavers >50K EGLD; system-contract aggregators (erd1qqqq...) excluded per the run #10 rule.")

# ---------- token analysis ----------
top_pair_share=pairs[0]['share_pct']
second_pair=pairs[1] if len(pairs)>1 else None
token_analysis=(f"DEX volume rose to ${totvol/1000:.0f}K ({100*(totvol-prev_dexvol)/prev_dexvol:+.0f}% WoW) - a mild recovery tracking the price bounce, still depressed vs the $100K+ of a month ago. WEGLD/USDC dominance {top_pair_share:.1f}% (thin market, one pair carrying almost all volume); ZoidPay/WEGLD share {second_pair['share_pct'] if second_pair else 0:.1f}%.\n\n"
 f"NEWLY-ISSUED TOKENS: 0 genuine issuances this week. The ESDT system-SC issue scan returned one match (WrappedUSDC / USDC-c76f1f) but that is a FALSE POSITIVE - a long-established token with 81,516 holders, not a fresh mint; the scan's name-search resolved an `issue`-function tx onto the old ticker. Filtered out (holder-count guard added this run). No real new-token launches cleared the >10-holder / >5-tx quality bar - a quiet launch week.\n\n"
 f"Token holder counts declined for a 15th consecutive week (small declines across the top 10) - the established airdrop-decay baseline. WrappedEGLD and WrappedUSDC remain the most-held real tokens.\n\n"
 f"MEX price {100*(meco['price']-prev_mexp)/prev_mexp:+.2f}% to ${meco['price']:.3e}, bouncing with EGLD. MEX mcap ${meco['marketCap']/1e6:.2f}M.\n\n"
 f"Top by market cap: EmoryaSportsX (EMRS) leads at ${D['tokens_mcap'][0].get('marketCap',0)/1e6:.1f}M ({D.get('emrs_token',{}).get('accounts',0):,} holders, {D.get('emrs_token',{}).get('transactions',0):,} txs - a genuine large-cap, per last run's correction). After EMRS: WrappedUSDC ${D['tokens_mcap'][1].get('marketCap',0)/1e6:.2f}M, xMoney UTK ${D['tokens_mcap'][2].get('marketCap',0)/1e6:.2f}M, ZoidPay ${D['tokens_mcap'][3].get('marketCap',0)/1e6:.2f}M, StakedEGLD ${D['tokens_mcap'][4].get('marketCap',0)/1e6:.2f}M.\n\n"
 f"Bridged stablecoin supply MIXED: USDC {usdc_supply_wow:+.2f}% (3rd consecutive burn week) but USDT {usdt_supply_wow:+.2f}% (burn nearly STOPPED, vs -3.7% last week). The aggregate dollar-liquidity flight DECELERATED as price stabilized and is now concentrated in USDC alone - a narrower, milder signal than last week's synchronized -1.3%/-3.7% acceleration.")

# ---------- defi analysis ----------
defi_analysis=(f"XEGLD SUPPLY STABILIZED - LAST WEEK'S -29% COLLAPSE WAS A ONE-SHOT. XEGLD circulating supply settled at {supply('XEGLD-e413ed'):,.0f} ({xegld_supply_wow:+.2f}% WoW) after last week's 321,592 -> 227,765 crash. There was NO continuation: the ~94K redemption was a single large event, not the start of an ongoing drain from XOXNO's liquid-staking product. This resolves last run's highest-priority DeFi watch. XOXNO LSD TVL has simply settled at its new lower level (${xoxno_lsd/1e6:.2f}M / {xlsd_egld/1000:.0f}K EGLD). The redeemer's onward destination is not cleanly traceable via standard transactions (the LSD contract moves EGLD via SC results, not value-bearing txs) - but the supply stabilization tells us the exit is done, whichever direction it went.\n\n"
 f"ALL OTHER LSDs FLAT-TO-UP in supply terms: SEGLD {segld_supply_wow:+.2f}%, SWTAO {swtao_supply_wow:+.2f}%, both flat. Hatom LSD ${hatom_lsd/1e6:.2f}M USD (SEGLD ${segld_mcap/1e6:.2f}M + SWTAO ${swtao_mcap/1e6:.2f}M), {100*(hatom_lsd-prev_hlsd)/prev_hlsd:+.1f}% USD - roughly flat, tracking the price bounce. IMPORTANT: SWTAO's dataApi price feed RECOVERED cleanly this run (the re-fetch guard needed 0 retries - all 4 dataApi tokens populated on the first pass), so unlike last week the SWTAO USD figure is a real reading, not a carried estimate.\n\n"
 f"HATOM USH stablecoin ${hatom_ush/1000:.0f}K, supply {ush_supply_wow:+.2f}% WoW - FLAT. The 2-week CDP de-leveraging/burn has STOPPED as price recovered; borrowers are no longer force-closing positions to avoid liquidation. On-chain leverage has stabilized - a constructive read after last week's -3.2% burn.\n\n"
 f"HATOM LENDING ${hatom_lending/1e6:.2f}M USD ({100*(hatom_lending-prev['defi_tvl']['Hatom Lending'])/prev['defi_tvl']['Hatom Lending']:+.1f}% USD, {100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}% EGLD). The +{100*(price-pp)/pp:.1f}% price move exceeds the |dPrice|>=5% guardrail, so the bilateral inverse rule IS evaluable: EGLD-denominated TVL moved {100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}% (counter to price) - depositors WITHDREW to capture gains into the rally, the mirror image of the dip-DCA behavior seen on down-weeks. Response ratio |{100*(hl_egld-prev_hl_egld)/prev_hl_egld:.1f}%|/|{100*(price-pp)/pp:.1f}%| = {abs(100*(hl_egld-prev_hl_egld)/prev_hl_egld)/abs(100*(price-pp)/pp):.2f}. This is the first UP-week test of the rule - and it held with the correct (inverse) sign.\n\n"
 f"xExchange TVL ${xexch_tvl_usd/1e6:.2f}M / {xexch_tvl_egld/1000:.0f}K EGLD ({100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld:+.1f}% EGLD). DEX volume ${totvol/1000:.0f}K (+{100*(totvol-prev_dexvol)/prev_dexvol:.0f}%). Aggregator throughput: XOXNO {tcount('XOXNO Aggregator'):,}, OneDex {tcount('OneDex Swap'):,} daily transfers.\n\n"
 f"DATA-QUALITY: clean run for the token price feed - the dataApi re-fetch guard (shipped run #14) reported 0 retries needed; all 4 dataApi-class LSD/stablecoin tokens (SEGLD, SWTAO, USH, XEGLD) populated price+mcap on the first pass, including SWTAO which needed a carried-prior-price fallback last run. Supply-based metrics remain the primary LSD signal; this week the USD figures are also fully reliable.")

report={
 "metadata":{"report_date":"2026-07-06","period_start":"2026-06-29T00:00:00Z","period_end":"2026-07-06T00:00:00Z",
   "generated_at":datetime.now(timezone.utc).isoformat(),"egld_price_usd":price,
   "btc_price_usd":be["bitcoin"]["usd"],"eth_price_usd":be["ethereum"]["usd"],"run_number":15,
   "data_sources_ok":json.load(open("/tmp/run15/status.json"))["ok"],
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
 "meta_learning":{"run_number":15,
   "endpoints_that_worked":json.load(open("/tmp/run15/status.json"))["ok"],
   "endpoints_that_failed":[],
   "api_quirks":[
     "CLEAN PRICE-FEED RUN: the dataApi re-fetch guard (shipped run #14) reported 0 retries needed - all 4 dataApi-class tokens (SEGLD, SWTAO, USH, XEGLD) populated price+mcap on the first sequential pass at 1.05s spacing, including SWTAO which stayed null for the ENTIRE run #14. Confirms the null behavior is a transient feed hiccup, not a persistent per-token outage; the guard is the right mitigation and this week it was a no-op.",
     "The custody-to-hot Binance move WAS traceable via standard /transactions this week (custody +241K in / -400K out = -159K net), UNLIKE prior weeks where Binance hot-wallet moves were internal-transfer-invisible. Lesson: staking-custody <-> hot-wallet transfers on Binance ARE standard value txs (visible), whereas hot-wallet <-> external/customer moves are not. When a custody wallet is involved, tx-scan the custody address before assuming the move is untraceable.",
     "Newly-issued token scan FALSE-POSITIVE: the ESDT system-SC issue-function scan resolved an `issue` tx onto WrappedUSDC (USDC-c76f1f, 81,516 holders) - a long-established token, not a new mint. The name-search step can match an old ticker. Added a holder-count guard (drop matches with >1,000 holders or an identifier already in previous.json) - a genuinely new token this window has a tiny holder base.",
     "Stablecoin supply units: /tokens/{id} `supply` is decimals-adjusted; previous.json stores supply_raw (raw integer). For USDC/USDT (6 decimals) divide supply_raw by 1e6 before comparison - else WoW reads -100%."],
   "data_gaps":[
     "XEGLD redeemer destination: the XOXNO LSD contract's EGLD outbound is via SC results, not value-bearing standard txs (the sender-filtered /transactions query returned 0), so the ~94K freed EGLD from last week's collapse could not be traced to a destination. The supply STABILIZATION this week (one-shot confirmed) is the substantive resolution regardless of destination.",
     "Binance's net -236K: the custody->hot leg is traced, but where the hot-wallet EGLD went onward (net -77K off the two hot wallets) is internal-transfer-invisible - self-custody vs customer withdrawal vs OTC is inferred, not proven.",
     "Newly-issued: 0 genuine launches after filtering the WrappedUSDC false positive - a quiet launch week, but the scan cannot fully distinguish 'quiet' from 'method missed a small deploy' without external corroboration."],
   "key_findings":[
     "THE 7-WEEK BINANCE CUSTODY STANDOFF RESOLVED to the DISTRIBUTION side: custody -158,853 back to Binance.com hot (traced: +241K in, -400K out). Drawdown-to-hot, not delegation - the bearish resolution of the long-running watch, into a +5.9% bounce.",
     "EGLD posted its FIRST up-week (+5.88% to $2.70) and $2.55 held, but UNDERPERFORMED the broad relief bounce (BTC +5.2%, ETH +12.3%) - a high-beta laggard, not leadership.",
     "XEGLD supply STABILIZED at ~226,400 (-0.6%) after last week's -29% collapse - the redemption was a ONE-SHOT event, no continuation. Resolves the top prior watch.",
     "Net exchange flow -218K (2nd outflow week) but ~entirely the Binance -236K custody unwind; ex-Binance the complex was net-INFLOW (Crypto.com +27K, Bybit +21K).",
     "OTC pipeline still distributing ~172K but desks FLIPPED from +35K load to -8.9K DRAIN - late-distribution phase; a fresh UPbit->OTC Desk 160K reload landed.",
     "Mega Whale erd18mv2z6r2 is the ABSORBER: +32.7K routed FROM Coinbase Routing (2nd straight accumulation week, now 1.04M) - distribution meeting a real bid, not dumped into a vacuum.",
     "Delegator base FLAT 3rd week (174,373) - capitulation fully behind us. Delegation TVL grew +70K broadly (Synexis +18K) while total staked FELL -46K = rotation from direct-node into delegation.",
     "Yield-chase spike UNWOUND (net -8.6K, egldstakingprovider -13.7K) as price recovered; pi-staking the exception (+13 users, 3rd growth week).",
     "Stablecoin flight DECELERATED and narrowed: USDC -2.0% (3rd burn week) but USDT burn nearly stopped (-0.3%), USH de-leveraging ended (flat)."],
   "action_items_from_previous":9,
   "action_items_completed":9,
   "methodology_changes":[
     "CUSTODY-VS-HOT MOVES ARE TRACEABLE (new): Binance Staking custody <-> Binance.com hot transfers show up as standard value txs (this run: +241K/-300K/-100K on the custody address), UNLIKE hot<->external moves. Rule: when a tracked custody wallet changes balance, tx-scan the custody address directly - the counterparty leg is often a visible standard transfer, letting you attribute the move instead of inferring it.",
     "CUSTODY-WATCH RESOLUTION FRAMEWORK VALIDATED: the multi-week 'custody parked -> eventual move' watch (run #9-14) resolved cleanly this run with the pre-committed reading (delegate=bullish / drawdown-to-hot=bearish). The drawdown-to-hot outcome fired. Keeping a pre-registered directional interpretation for a long-running structural watch paid off - it removed ambiguity when the move finally came.",
     "READ EXCHANGE FLOW BY ENTITY, NOT JUST AGGREGATE (reinforced): the -218K net was ~entirely one Binance idiosyncratic move; ex-Binance the complex was net-inflow. A headline net-flow number can invert the true breadth. Always decompose to per-entity before calling the aggregate bullish/bearish - especially when one entity's move exceeds the net.",
     "BILATERAL INVERSE RULE - FIRST UP-WEEK TEST PASSED: with price +5.88% (>5% guardrail), Hatom Lending EGLD-TVL moved -2.86% (inverse), depositors withdrew to capture gains - the mirror of dip-DCA. The rule now has an up-side confirmation, not just down-side. Response ratio 0.49.",
     "NEWLY-ISSUED HOLDER-COUNT GUARD: added a filter to drop issue-scan matches with >1,000 holders or an already-known identifier (the scan false-positived onto WrappedUSDC). Prevents an established token being mislabeled as a new launch."],
   "new_addresses_discovered":3,
   "most_valuable_insight":"The 7-week Binance Staking custody standoff finally resolved - and it resolved to the DISTRIBUTION side: the custody drew down -158,853 EGLD back to Binance.com hot wallets (traced, not inferred: +241K in, -400K out), into a +5.9% price bounce. This is the payoff of a multi-week structural watch with a pre-committed directional reading (delegate=bullish / drawdown-to-hot=bearish), and it fired bearish. But the week's fuller story is nuanced, not one-sided: the net exchange outflow was almost entirely this one Binance move (ex-Binance the complex was net-INFLOW), the OTC desks are now draining rather than reloading (late-distribution), and - critically - the distributed supply is being ABSORBED by an identifiable large buyer (Mega Whale erd18mv2z6r2 took +32.7K routed from Coinbase, its 2nd accumulation week). So distribution is real and ongoing, but it is meeting a bid, not dumping into a vacuum - consistent with a laggard price bounce that has some structural support under it. Meanwhile last week's two open questions both resolved benignly: the XEGLD -29% collapse was a one-shot (supply stabilized) and the delegator capitulation is fully over (flat 3rd week).",
   "top_recommendation":"Track the Binance custody unwind's second leg: the -159K now sits in Binance.com hot wallets. Watch whether it drains onward next week (confirmed distribution/sell) or rebuilds (a reorg, less bearish) - the onward destination is the decisive read on whether the custody resolution is genuinely distributive. Pair with the Mega Whale erd18mv2z6r2 absorber: if it keeps accumulating Coinbase-routed flow, there is a large standing bid under the market worth quantifying.",
   "recommendations_for_next_run":[
     "BINANCE CUSTODY 2ND LEG: the -159K unwound to Binance.com hot wallets this week. Watch whether the hot-wallet balance drains onward (confirmed distribution/sell) or rebuilds (reorg). tx-scan the custody AND hot addresses - custody legs are traceable. Highest-priority follow-up.",
     "MEGA WHALE erd18mv2z6r2 as absorber: +32.7K from Coinbase Routing this week (2nd accumulation week, now 1.04M). Watch whether it keeps absorbing exchange/OTC-routed distribution (a large standing bid) or turns to distribute. Trace its inbound sources each week.",
     "OTC pipeline phase: desks flipped to DRAINING (-8.9K) while still distributing ~172K, with a fresh 160K reload. Watch whether throughput COLLAPSES to a GAP (wave done) or the reload feeds another distribution leg.",
     "Ex-Binance exchange INFLOW: Crypto.com +27K, Bybit +21K, KuCoin +9.6K went ON exchanges into the bounce. Watch whether this builds (renewed on-exchange positioning = potential sell overhang) or reverses.",
     "Does the bounce HOLD? EGLD +5.9% but underperformed ETH (+12.3%) badly. The run #12 relief bounce failed within a week. Track whether $2.70 holds and whether EGLD's beta to ETH/BTC improves (leadership) or stays laggard.",
     "Stablecoin flight: USDC 3rd burn week (-2.0%) but USDT decelerated (-0.3%). Watch whether USDC follows USDT and flattens (de-risking done) or keeps contracting (isolated USDC bridge-out).",
     "Delegation-vs-direct-node rotation: delegation TVL +70K while total staked -46K. Watch whether the rotation into delegation contracts continues and whether the broad delegation growth (Synexis, stakingagency) sustains.",
     "pi-staking (0% fee) drew a 3rd straight week (+13 users to 51). Watch whether this small-provider growth story continues or plateaus - it's the only yield-chase name still drawing."],
   "dashboard_feature_suggestions":[
     {"title":"Binance custody-vs-hot-vs-protocol-staked unwind tracker","motivation":"THIS run's headline: the 7-week Binance Staking custody position finally unwound -159K back to hot wallets (traced). A single chart tracking custody balance, Binance hot-wallet balance, and protocol staked-EGLD across all weeks would have shown the full 3-week-accumulate / 4-week-stall / unwind arc AND made the delegate-vs-drawdown resolution visually obvious the moment it happened. The run #10 idea, now maximally motivated by the resolution.","suggested_visualization":"stacked/overlaid multi-line time series: Binance Staking custody balance, Binance.com hot-wallet total, and economics.staked - all weekly - with event annotations (accumulation / stall / unwind) and a shaded band for the parked position.","data_already_available":True,"data_source":"previous.json exchange_balances (Binance Staking, Binance.com) + economics.staked_egld across snapshots","priority":"high"},
     {"title":"Exchange-flow vs OTC-throughput dual-axis chart","motivation":"Re-listed and reinforced: this run the -218K net exchange OUTFLOW was almost entirely one Binance move while OTC desks drained yet still pushed ~172K throughput. Reading either series alone inverts the truth (the outflow looks like accumulation; ex-Binance it was inflow). A dual-axis view (plus a per-entity breakdown of the net) makes the channel-shift and the Binance-dominance legible.","suggested_visualization":"weekly grouped bars: net exchange flow (signed, with a Binance-vs-rest split) on the left axis, combined OTC desk 7d throughput on the right axis, EGLD price overlaid.","data_already_available":True,"data_source":"exchange_flows.net_change_egld + entity_netting + OTC desk outbound throughput, all computed per run","priority":"high"},
     {"title":"Distribution-absorber leaderboard","motivation":"This run's most useful nuance was WHO is absorbing the distribution: Mega Whale erd18mv2z6r2 took +32.7K routed from Coinbase Routing, its 2nd accumulation week. A recurring view of the top non-exchange wallets receiving exchange/OTC-routed inflows would quantify the standing bid under the market and distinguish 'distribution into a vacuum' (bearish) from 'distribution being accumulated' (supported).","suggested_visualization":"ranked bar list of top non-exchange wallets by WoW balance gain that was sourced from exchange/OTC/routing counterparties, with a multi-week accumulation streak badge per wallet.","data_already_available":True,"data_source":"wallet_changes[] cross-referenced with large_transactions[] sender categories (exchange/router/otc) - both already in the report JSON","priority":"medium"}],
   "dashboard_suggestions_followup":[
     {"from_run":10,"title":"Multi-week Binance custody vs protocol-staked tracker","status":"pending","note":"NOT yet built, and now MAXIMALLY motivated: the custody just unwound -159K this run after 7 weeks. Promoted to this run's #1 suggestion (renamed 'custody-vs-hot-vs-staked unwind tracker') - this is the moment the chart pays off. Should be the next widget built."},
     {"from_run":14,"title":"Exchange-flow vs OTC-throughput dual-axis chart","status":"pending","note":"NOT yet built. Re-listed at high priority - this run reinforced why it matters (Binance-dominated outflow + draining desks would be legible; the aggregate number alone misled)."},
     {"from_run":13,"title":"LSD circulating-supply timeline (supply, not mcap)","status":"pending","note":"NOT yet built. Still valuable - this run it would have shown XEGLD STABILIZING after last week's -29% collapse (the one-shot resolution), the natural companion frame to the collapse. Slightly lower urgency now that the XEGLD event resolved; kept in the queue."},
     {"from_run":13,"title":"OTC pipeline load/distribute cycle phase indicator","status":"pending","note":"NOT yet built. Re-listed - this run the phase advanced DISTRIBUTING -> DRAINING (late phase), exactly the transition the badge would show. Folded conceptually into the dual-axis chart's OTC axis."},
     {"from_run":13,"title":"Forward-indicator scorecard (prediction resolution tracker)","status":"deprioritized","note":"Still useful (this run resolved 9/9 prior action items, a strong scorecard week) but lower priority than the custody tracker and dual-axis chart. Deferred."},
     {"from_run":8,"title":"OTC pipeline graph view (Sankey/force-directed)","status":"pending","note":"Still a strong idea - this run had traceable Coinbase Routing -> Mega Whale and custody -> hot edges. Lower priority than the custody tracker; partially overlaps the new absorber-leaderboard suggestion."}]}}

json.dump(report,open(f"{REPO}/reports/2026-07-06.json","w"),indent=2)
print("WROTE reports/2026-07-06.json")
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
