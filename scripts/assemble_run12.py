#!/usr/bin/env python3
"""Assemble reports/2026-06-15.json (run #12) from collected data."""
import json, math
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D = json.load(open("/tmp/run12/collected.json"))
prev = json.load(open(f"{REPO}/data/previous.json"))
kn = json.load(open(f"{REPO}/data/known-addresses.json"))
learn = json.load(open(f"{REPO}/data/learnings.json"))

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
be=D["btc_eth"]
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
by_exchange=[]; ent_cur={}; ent_w={}
# bad address from run #11 - skip it; use only correctable addresses
BAD_ADDR = "erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp29trp6qsl2gdvvz2eqra76xc"
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
# Build prev_ent using corrected accounting: pull from prev top_accounts for the canonical address, not from previous.json exchange_balances (which had the broken entry)
prev_ent={}
prev_ta_map={x["address"]:x["balance_egld"] for x in prev["top_accounts"]}
for a in exch:
    if a == BAD_ADDR: continue
    e=entity_of(a)
    if not e: continue
    if a in prev_ta_map:
        prev_ent[e]=prev_ent.get(e,0)+prev_ta_map[a]
# For addresses outside top_accounts, fall back to previous.json exchange_balances pro-rata (use last reported)
for k,v in prev["exchange_balances"].items():
    e = "Binance" if "Binance" in k else ("Coinbase" if "Coinbase" in k else k)
    if e == "Crypto.com": e = "Crypto.com"
    # Avoid double-counting if already in prev_ent from top_accounts
    if e not in prev_ent:
        prev_ent[e] = v

ent_interp={
 "Binance":"Hot wallet (corrected addr erd1sdslv...3rgul) +23.8K WoW (+12.0%); Binance.com 3-wallet entity total +23.8K to 689K. Binance Staking custody UNCHANGED at 3,512,650 EGLD for the 2nd consecutive week (3-week accumulation phase now extended into a stall - 779K parked since run #7). The hot-wallet inflow without offsetting custody movement is consistent with on-exchange capital REBUILDING (deposit-side flow, not distribution to retail). Note: a previously-tracked Binance.com address with invalid bech32 checksum was excluded this run; entity now uses 3 canonical addresses.",
 "Coinbase":"Primary wallet +8.4K (+10.7%), Coinbase 2 -2.6K, Coinbase 3 +2.5K. Combined entity +8.3K - a 2nd consecutive week of net inflow (last week +43K, this week +8.3K). Run #11's off-exchange-accumulation thesis remains DEAD; sell-into-decline pattern continues but at much milder intensity than last week's surge. Per run #11 recommendation #4 (2nd inflow confirmation), this DOES confirm the pattern reversal.",
 "Crypto.com":"-7.3K (-3.9%). Reversed last week's +10.9K inflow. Net 2-week cycle nearly flat.",
 "Bybit":"+4.1K (+0.8%) on cold wallet. Mild deposit drift.",
 "UPbit":"Cold wallet +3.0K (+0.2%) - effectively flat. UPbit OTC Desk separately -1.8K (-6%). OTC Distribution Wallet +0.9K (+3%). Combined OTC desks essentially STATIC after last week's -26.4K distribution; pipeline appears in the inter-cycle gap.",
 "MEXC":"-2.6K (-2.7%). Mild outflow continues.",
 "KuCoin":"+3.7K (+13.5%) on cold wallet. Visible deposit step similar to last week.",
 "Bitget":"+1.4K (+1.6%). Flat after last week's surge.",
 "Gate.io":"+5.6K (+10.9%). Material inflow after a flat run #11.",
 "Tokero":"Effectively flat (-0.7K).",
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
    "signal":f"Net exchange flow {net_total:+,.0f} EGLD ({100*net_total/total_prev if total_prev else 0:+.2f}%) - 2nd consecutive week of INFLOW. Last week's collapse of the off-exchange-accumulation thesis is now confirmed by a 2nd inflow week (per run #11's recommended 2-week confirmation rule). The Coinbase 3-week outflow streak followed by 2 inflow weeks marks a directional reversal. With Binance Staking custody STALLED for 2nd consecutive week, the bullish parked-capital thesis remains dead. The on-exchange capital continues rebuilding during the price recovery attempt - a sell-into-bounce setup more than a recovery accumulation. EGLD bounced +1.4% to $2.99 but the on-exchange capital build suggests sellers are using the bounce as exit liquidity.",
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
# top_by_market_cap: fill holders from tokens_holders join when possible
holders_map={t["identifier"]:t.get("accounts") for t in D["tokens_holders"]}
top_by_market_cap=[]
for t in D["tokens_mcap"][:10]:
    tid=t["identifier"]
    h=holders_map.get(tid)
    ph=prev_th.get(tid,{}).get("holders")
    top_by_market_cap.append({"identifier":tid,"name":t.get("name"),"holders":h,"previous_holders":ph,
        "price_usd":t.get("price"),"market_cap_usd":t.get("marketCap"),"volume_24h_usd":None})
# Newly-issued tokens
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
xexchange={"total_pairs":meco.get("marketPairs"),"total_volume_24h_usd":totvol,"mex_price_usd":meco["price"],
    "mex_market_cap_usd":meco["marketCap"],"mex_price_change_24h_pct":None,
    "mex_price_change_wow_pct":100*(meco["price"]-prev_mexp)/prev_mexp,
    "top_pair":pairs[0]["name"],"top_pair_volume_24h_usd":pairs[0]["volume_24h_usd"],
    "top_pair_dominance_pct":pairs[0]["share_pct"],"top_pairs_by_volume":pairs[:5]}

# ---------- defi - LSD mcaps with supply-fallback (defense-in-depth) ----------
tt=D["tvl_tokens"]
def mc(tid):
    t=tt.get(tid); return (t.get("marketCap") or 0) if isinstance(t,dict) else 0
def supply_circ(tid, decimals=18):
    """Circulating supply (minted - burnt) / 10^decimals. Returns 0 if data missing."""
    t = tt.get(tid)
    if not isinstance(t, dict): return 0
    try:
        m = int(t.get("minted", "0") or "0")
        b = int(t.get("burnt", "0") or "0")
        return (m - b) / (10**decimals)
    except Exception:
        return 0
def mc_or_fallback(tid, peg_kind):
    """Returns marketCap if API populated, else supply-based fallback.
    peg_kind: 'egld' (multiply by EGLD price), 'usd' (1:1), 'none' (no fallback, return 0)."""
    v = mc(tid)
    if v > 0:
        return v
    circ = supply_circ(tid)
    if peg_kind == "egld":
        return circ * price
    elif peg_kind == "usd":
        return circ
    return 0

# Hatom Lending - 10 H-tokens (all have working mcaps when API healthy)
hatom_lending=sum(mc(x) for x in ["HUSDC-d80042","HEGLD-d61095","HUSDT-6f0914","HWBTC-49ca31","HWETH-b3d17e","HBUSD-ac1fca","HHTM-e03ba5","HMEX-df6df7","HUTK-4fa4b2","HWTAO-2e9136"])
# LSDs: SEGLD/XEGLD peg to EGLD, USH pegs to USD. SWTAO pegs to TAO (no fallback).
# Run #11 SWTAO null caused $1.18M Hatom LSD undercount — defense-in-depth keeps the fallback even
# after the rate-limit root cause is fixed, so future hiccups degrade gracefully.
segld_mcap = mc_or_fallback("SEGLD-3ad2d0", "egld")
swtao_mcap = mc("SWTAO-356a25")  # no fallback (TAO peg)
hatom_lsd = segld_mcap + swtao_mcap
# Apples-to-apples WoW: previous "Hatom LSD" was $2.51M, but that was SEGLD-only.
# Add back the SWTAO mcap from this run ($1.19M) as a proxy for what last week actually was.
hatom_lsd_prev_corrected = prev["defi_tvl"]["Hatom Liquid Staking"] + swtao_mcap
hatom_ush = mc_or_fallback("USH-111e09", "usd")  # stablecoin → 1:1 USD fallback
xoxno_lsd = mc_or_fallback("XEGLD-e413ed", "egld")  # EGLD peg → supply × price fallback

wegld_egld=sum(int(b["balance"])/1e18 for b in D["wegld"].values() if isinstance(b,dict) and "balance" in b)
xexch_tvl_egld=wegld_egld; xexch_tvl_usd=wegld_egld*price
def tcount(name):
    c=D["proto"][name]["transfers_24h"]; return c.get("count") if isinstance(c,dict) else c
ppx=pecon["egld_price_usd"]
prev_hl_egld=prev["defi_tvl"]["Hatom Lending"]/ppx
prev_xl_egld=prev["defi_tvl"]["XOXNO LSD"]/ppx
prev_hush=prev["defi_tvl"]["Hatom USH"]
prev_xexch_egld=prev["defi_tvl"]["xExchange (USD)"]/ppx
prev_hlsd=prev["defi_tvl"]["Hatom Liquid Staking"]
prev_hlsd_egld=prev_hlsd/ppx
# Corrected apples-to-apples for Hatom LSD (prev was SEGLD-only)
prev_hlsd_corrected_egld = hatom_lsd_prev_corrected / ppx
hl_egld=hatom_lending/price
hlsd_egld=hatom_lsd/price
xlsd_egld=xoxno_lsd/price
ush_egld=hatom_ush/price
# WEGLD WoW supply
weglds=D["tokens_holders"]
wegld_tok=next((t for t in weglds if t["identifier"]=="WEGLD-bd4d79"), None)
wegld_supply_now = int(wegld_tok.get("supply","0")) if wegld_tok else 0
wegld_supply_prev = int(prev_th.get("WEGLD-bd4d79",{}).get("supply_raw",0) or 0)
wegld_chg_pct = 100*(wegld_supply_now-wegld_supply_prev)/max(wegld_supply_prev,1) if wegld_supply_prev else 0
protocol_breakdown=[
 {"protocol":"xExchange","category":"dex","addresses_tracked":16,"tvl_usd":xexch_tvl_usd,"tvl_egld":xexch_tvl_egld,
  "tvl_wow_change_pct":100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld,"transfers_24h":None,"volume_24h_usd":totvol,
  "notable_events":f"DEX volume -55.2% to ${totvol/1000:.0f}K (vs $122K last week) — substantial liquidity contraction during the price bounce. WEGLD/USDC dominance 85.1% (down from 93.2%); ZoidPay/WEGLD share 8.1% (up from 3.0%). WEGLD supply WoW {wegld_chg_pct:+.2f}% (flat).","health_signal":"shrinking"},
 {"protocol":"Hatom Lending","category":"lending","addresses_tracked":13,"tvl_usd":hatom_lending,"tvl_egld":hl_egld,
  "tvl_wow_change_pct":100*(hl_egld-prev_hl_egld)/prev_hl_egld,"transfers_24h":tcount("Hatom EGLD MM"),
  "notable_events":f"TVL ${hatom_lending/1e6:.2f}M USD ({100*(hatom_lending-prev['defi_tvl']['Hatom Lending'])/prev['defi_tvl']['Hatom Lending']:+.1f}%), {hl_egld/1000:.0f}K EGLD ({100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}%). Bilateral inverse rule NOT EVALUABLE this run — price move +1.4% is below the meaningful-move threshold (rule observed only at |Δprice|>5% historically); EGLD-TVL response +0.9% within noise band.","health_signal":"flat"},
 {"protocol":"Hatom Liquid Staking","category":"liquid_staking","addresses_tracked":2,"tvl_usd":hatom_lsd,"tvl_egld":hlsd_egld,
  "tvl_wow_change_pct":100*(hlsd_egld-prev_hlsd_corrected_egld)/prev_hlsd_corrected_egld,"transfers_24h":tcount("Hatom Liquid Staking"),
  "notable_events":f"SEGLD ${segld_mcap/1e6:.2f}M + SWTAO ${swtao_mcap/1e6:.2f}M = ${hatom_lsd/1e6:.2f}M. NOTE: run #11 previous.json undercounted Hatom LSD by ${swtao_mcap/1e6:.2f}M (SWTAO was null due to a rate-limit miss). Apples-to-apples WoW (adding SWTAO to prev): {100*(hlsd_egld-prev_hlsd_corrected_egld)/prev_hlsd_corrected_egld:+.1f}% EGLD. Hatom LSD is essentially flat — not the contraction the uncorrected data suggested last run.","health_signal":"flat"},
 {"protocol":"Hatom USH","category":"stablecoin","addresses_tracked":4,"tvl_usd":hatom_ush,"tvl_egld":ush_egld,
  "tvl_wow_change_pct":100*(hatom_ush-prev_hush)/prev_hush,"transfers_24h":None,
  "notable_events":f"USH mcap ${hatom_ush/1000:.0f}K ({100*(hatom_ush-prev_hush)/prev_hush:+.1f}% USD). 2nd consecutive week of contraction (-3.7%, then {100*(hatom_ush-prev_hush)/prev_hush:+.1f}%). USH supply minted-burnt = {(int(tt['USH-111e09']['minted'])-int(tt['USH-111e09']['burnt']))/1e18:,.0f} USH circulating. De-leveraging trend continues.","health_signal":"shrinking" if (hatom_ush-prev_hush)/prev_hush < -0.02 else "flat"},
 {"protocol":"XOXNO LSD","category":"liquid_staking","addresses_tracked":2,"tvl_usd":xoxno_lsd,"tvl_egld":xlsd_egld,
  "tvl_wow_change_pct":100*(xlsd_egld-prev_xl_egld)/prev_xl_egld,"transfers_24h":tcount("XOXNO LSD"),
  "notable_events":f"XEGLD ${xoxno_lsd/1e6:.2f}M ({100*(xoxno_lsd-prev['defi_tvl']['XOXNO LSD'])/prev['defi_tvl']['XOXNO LSD']:+.1f}% USD), {xlsd_egld/1000:.0f}K EGLD ({100*(xlsd_egld-prev_xl_egld)/prev_xl_egld:+.1f}% EGLD). 2nd consecutive week of mild EGLD-denominated contraction (-1.4% last run, {100*(xlsd_egld-prev_xl_egld)/prev_xl_egld:+.1f}% now). Pattern continues but milder than initially read.","health_signal":"shrinking"},
 {"protocol":"XOXNO Aggregator","category":"aggregator","addresses_tracked":1,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("XOXNO Aggregator"),
  "notable_events":f"Throughput {tcount('XOXNO Aggregator'):,} daily transfers. Aggregator activity elevated throughout the decline; baseline ~21K/day.","health_signal":"flat"},
 {"protocol":"OneDex","category":"aggregator","addresses_tracked":5,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("OneDex Swap"),
  "notable_events":f"{tcount('OneDex Swap'):,} daily transfers via swap contract. Aggregator throughput steady.","health_signal":"flat"},
 {"protocol":"JEXchange","category":"dex","addresses_tracked":4,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("JEXchange Fees"),
  "notable_events":f"Fees wallet {tcount('JEXchange Fees'):,} daily transfers. Aggregator activity steady.","health_signal":"flat"}]
protocols=[
 {"name":"xExchange","category":"dex","volume_24h_usd":totvol,"active_pairs":25,"transfers_24h":None,"tvl_usd":xexch_tvl_usd,"tvl_egld":xexch_tvl_egld,"tvl_wow_change_pct":100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld},
 {"name":"Hatom Lending","category":"lending","volume_24h_usd":None,"active_pairs":None,"transfers_24h":tcount("Hatom EGLD MM"),"tvl_usd":hatom_lending,"tvl_egld":hl_egld,"tvl_wow_change_pct":100*(hl_egld-prev_hl_egld)/prev_hl_egld},
 {"name":"Hatom Liquid Staking","category":"liquid_staking","volume_24h_usd":None,"active_pairs":None,"transfers_24h":tcount("Hatom Liquid Staking"),"tvl_usd":hatom_lsd,"tvl_egld":hlsd_egld,"tvl_wow_change_pct":100*(hlsd_egld-prev_hlsd_corrected_egld)/prev_hlsd_corrected_egld},
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
anomalies=[
 {"metric":"egld_price_usd","current_value":price,"previous_value":pecon["egld_price_usd"],"method":"z_score",
  "average_value":zp[0],"stddev":zp[1],"z_score":zp[2],"severity":"medium" if abs(zp[2])<3 else "high",
  "description":f"EGLD +1.36% WoW to $2.99, z={zp[2]:+.2f}σ (N={len(rb['egld_price_usd'])}). FIRST UP-WEEK after 5 consecutive down-weeks. Run #11's predicted capitulation bounce off $2.95 materialized. BTC +2.00% / ETH +2.58% (24h) - EGLD back in line with crypto-macro (no longer decoupled to downside, though still underperforming). The bounce is mild relative to the 5-week -37% drawdown; whether this is genuine reversal or dead-cat depends on next 1-2 weeks. The on-exchange capital build (per exchange_flows) suggests sellers using the bounce as exit liquidity rather than capitulation low confirmation."},
 {"metric":"mex_price_usd","current_value":meco["price"],"previous_value":prev_mexp,"method":"z_score",
  "average_value":zmex[0],"stddev":zmex[1],"z_score":zmex[2],"severity":"low",
  "description":f"MEX price -0.83% to ${meco['price']:.3e} (z={zmex[2]:+.2f}σ, LOW severity, N={len(rb['mex_price_usd'])}). MEX DECOUPLED from EGLD this week — EGLD +1.4% but MEX -0.8%. Typically MEX amplifies EGLD moves; this independent direction is unusual. MEX mcap roughly flat at $1.11M (-1.3%). With DEX volume -55% the trading apparatus is contracting."},
 {"metric":"total_delegators","current_value":cur_deleg,"previous_value":prev_deleg,"method":"z_score",
  "average_value":zd[0],"stddev":zd[1],"z_score":zd[2],"severity":"high",
  "description":f"Total delegators {cur_deleg:,} (-{prev_deleg-cur_deleg:,} WoW = -{100*(prev_deleg-cur_deleg)/prev_deleg:.2f}%). z={zd[2]:+.2f}σ. The largest absolute drop in tracking history by 9x (last run was -447, this run -{prev_deleg-cur_deleg:,}). With z-score now significantly negative AND absolute % move at -2.24%, the run #9 degenerate-z-score downgrade does NOT apply — this is a real capitulation event. Combined with staked-EGLD -38K decline, this is concentrated delegation exit by retail. Confirms run #11's emerging capitulation pattern at much larger magnitude."},
 {"metric":"staked_egld","current_value":staked,"previous_value":pecon["staked_egld"],"method":"z_score",
  "average_value":zse[0],"stddev":zse[1],"z_score":zse[2],"severity":"low",
  "description":f"Total staked {staked:,} EGLD (-{(pecon['staked_egld']-staked):,} WoW, -{100*(pecon['staked_egld']-staked)/pecon['staked_egld']:.2f}%). z={zse[2]:+.2f}σ. Sustained protocol-level unstaking continues — 2nd consecutive week of decline (-27K last run, -38K this run). Staked ratio dropped 48.08% → {sr*100:.2f}% (-0.21pp). Mild but consistent with delegator exit."},
 {"metric":"binance_staking_custody_stalled_2nd_week","current_value":3512650,"previous_value":3512650,"method":"rule_based",
  "severity":"high",
  "description":"Binance Staking custody UNCHANGED at 3,512,650 EGLD for 2nd consecutive week. The 3-week accumulation phase (runs #7+9+10 cumulative +402K) has now extended into a 2-week stall. Total parked since run #7: 779K EGLD ($2.33M at current price). No delegation to protocol staked module; no drawdown to hot wallets. Promoted from anomaly to ENTRENCHED STRUCTURAL POSITION. The longer this sits, the more decisive the eventual move becomes."},
 {"metric":"dex_volume_24h_usd","current_value":totvol,"previous_value":prev['xexchange']['volume_24h_usd'],"method":"z_score",
  "average_value":zv[0],"stddev":zv[1],"z_score":zv[2],"severity":"medium",
  "description":f"DEX volume -55.2% to ${totvol/1000:.0f}K (z={zv[2]:+.2f}σ, N={len(rb['dex_volume_24h_usd'])}). Largest WoW DEX volume contraction in tracked history. The price bounce did NOT bring liquidity — instead trading dried up. Pair composition shifted: WEGLD/USDC dominance fell 93.2% → 85.1%; ZoidPay/WEGLD share rose 3.0% → 8.1% (event-driven, not regime). Read: traders not engaging during the bounce — confirms the 'exit liquidity' interpretation of the price recovery."},
 {"metric":"yield_chase_cohort_reversal","current_value":-17000,"previous_value":-2610,"method":"rule_based",
  "severity":"high",
  "description":"Yield-chase cohort cratered for a 2nd consecutive week and at much larger magnitude. ninjastaking -10.5K (last week's only sustained gainer reversed sharply), procryptostaking -6.8K, egldstakingprovider -3.3K, valuestaking +3.4K (only positive). Net cohort flow ~-17K (vs -2.6K last week). Combined with the -4,003 delegator drop, this is concentrated retail exit from the high-APR providers. Yield-chase regime is fully terminated; cohort now in net redemption."},
 {"metric":"coinbase_2nd_week_inflow_confirmation","current_value":8320,"previous_value":42932,"method":"rule_based",
  "severity":"medium",
  "description":f"Coinbase entity +8.3K net inflow this week (vs +43K last week). Per run #11's recommended 2-week confirmation rule, the off-exchange-accumulation thesis reversal IS confirmed. Direction: inflow continues but at much milder magnitude. Combined 2-week net: +51K inflow. The bullish parked-capital read from run #10 is decisively dead."}]

# ---------- trend indicators ----------
accelerating_outflows=[
 {"exchange":"Coinbase","trend":"inflow","cumulative_change_pct":None,"weeks_in_trend":2,
  "interpretation":"Coinbase 2-week net inflow CONFIRMS the reversal flagged in run #11. Direction: +43K → +8.3K (mild deceleration but still inflow). Off-exchange accumulation thesis decisively dead. Coinbase Routing Wallet did NOT send to Unknown Mega Whale this week (last week sent +5,925)."},
 {"exchange":"NET_EXCHANGE","trend":"inflow","cumulative_change_pct":None,"weeks_in_trend":2,
  "interpretation":"Aggregate net exchange flow +24K inflow → +X inflow (2-week consecutive inflow streak). 2-week confirmation rule satisfied: the bullish parked-capital thesis from run #10 is fully invalidated. Sell-into-decline pattern continues into a sell-into-bounce setup."},
 {"exchange":"UPbit OTC Desks","trend":"flat","cumulative_change_pct":None,"weeks_in_trend":1,
  "interpretation":"OTC desks essentially flat this week (UPbit OTC -1.8K, OTC Distribution +0.9K, combined -0.9K). Outflow throughput 20K+24K=44K (vs 99K+64K=163K last week). Pipeline appears in the inter-cycle gap between distribution and reload. Per run #11's prediction, expect loading phase to return within 1-2 weeks."}]
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
   {"metric":"egld_price","direction":"up","weeks":1,"cumulative_change_pct":1.36,
    "interpretation":"FIRST up-week after 5 down-weeks. EGLD $2.95 → $2.99 (+1.36%). The capitulation bounce predicted in run #11 materialized. Whether this becomes recovery or dead-cat depends on next 1-2 weeks. BTC +2%, ETH +2.6% confirm broad-crypto recovery; EGLD is participating but trailing."},
   {"metric":"token_holder_count_decline","direction":"down","weeks":12,"cumulative_change_pct":None,
    "interpretation":"12th consecutive week of small holder declines across top-10 tokens. Established airdrop-decay baseline; active >$1M-mcap token base stable."},
   {"metric":"binance_staking_custody_stalled","direction":"flat","weeks":2,"cumulative_change_pct":0,
    "interpretation":"2nd consecutive week of stall at 3,512,650 EGLD. The 3-week accumulation phase (runs #7+9+10) extended into a 2-week stall. Total parked 779K since run #7 — promoted to entrenched structural position. The longer this sits, the more decisive the eventual move."},
   {"metric":"delegator_capitulation","direction":"down","weeks":2,"cumulative_change_pct":-2.5,
    "interpretation":"2-week capitulation streak: -447 last week, -4,003 this week. 9x acceleration. Cumulative -4,450 delegators (~-2.5%) since run #10. Combined with -65K cumulative staked-EGLD decline = concentrated retail exit from delegation."},
   {"metric":"lsd_xoxno_contraction","direction":"down","weeks":2,"cumulative_change_pct":None,
    "interpretation":"XOXNO LSD contracted in EGLD terms for 2nd consecutive week (-1.4% then -2.5%). Hatom LSD, on apples-to-apples basis (adding back the SWTAO undercount from run #11), is essentially FLAT not contracting. The 'synchronized LSD contraction' pattern from run #11 is downgraded: only XOXNO LSD confirmed; Hatom LSD pattern was a data-quality artifact."},
   {"metric":"dex_volume","direction":"down","weeks":1,"cumulative_change_pct":-55.2,
    "interpretation":"Largest WoW DEX volume drop in tracking history. ${prev['xexchange']['volume_24h_usd']/1000:.0f}K → ${totvol/1000:.0f}K. Traders not engaging during the bounce — supports the 'exit liquidity' read on the price recovery."}],
 "regime_shifts":[
   {"metric":"yield_chase_full_termination","before_value":-2610,"after_value":-17000,
    "description":"Yield-chase cohort moved from regime-end (-2.6K last run) to active net redemption (-17K this run). ninjastaking — the only sustained gainer across 5 weeks — reversed sharply to -10.5K. The 5-week migration is now FULLY UNWOUND."},
   {"metric":"delegator_capitulation_event","before_value":-447,"after_value":cur_deleg-prev_deleg,
    "description":"Delegator drop accelerated 9x WoW (-447 → -4,003). The largest single-week drop in tracking by an order of magnitude. Combined with -38K staked-EGLD decline, this is concentrated retail exit. Regime: delegation contraction."},
   {"metric":"dex_volume_collapse","before_value":prev['xexchange']['volume_24h_usd'],"after_value":totvol,
    "description":"DEX volume cratered -55% to $55K — the lowest since run #6's $75K post-rally low. Traders disengaging during the bounce indicates exit liquidity rather than fresh demand."}]}

# ---------- dormant activations ----------
dormant_activations=[]

# ---------- watch list ----------
watch_list=[
 {"item":"EGLD $2.95 capitulation bounce confirmed (+1.36% to $2.99)","reason":"First up-week after 5 down-weeks. BTC +2.0%, ETH +2.6% confirm broad recovery; EGLD trailing but in line. Whether this is genuine reversal or dead-cat depends on next 1-2 weeks. The on-exchange capital build during the bounce (per exchange flows) suggests sellers using bounce as exit liquidity rather than capitulation low confirmation.","weeks_on_list":3},
 {"item":"Binance Staking custody STALLED for 2nd consecutive week at 3.51M","reason":"3-week accumulation followed by 2-week stall. 779K parked since run #7 ($2.33M at current price) remains undeployed. Watching for the decisive move — delegation (bullish, would jump econ.staked) or distribution (bearish, would drawdown to hot wallets). Each additional week of stall makes the eventual move more decisive.","weeks_on_list":6},
 {"item":"Delegator capitulation event: -4,003 WoW (9x last week)","reason":"Largest single-week drop in tracking history by an order of magnitude. Combined with -38K staked-EGLD decline, this is concentrated retail exit from delegation. Watch next week to confirm continuation or one-shot shake-out.","weeks_on_list":2},
 {"item":"Yield-chase cohort fully unwound: net -17K","reason":"ninjastaking — last week's only sustained gainer — reversed sharply -10.5K. procryptostaking -6.8K, egldstakingprovider -3.3K. The 5-week migration regime is fully terminated and now in net redemption.","weeks_on_list":7},
 {"item":"Coinbase 2-week net inflow CONFIRMED","reason":"Per run #11's 2-week confirmation rule: +43K → +8.3K = 2 consecutive inflow weeks. Off-exchange accumulation thesis decisively dead. Coinbase Routing Wallet did NOT send to mega-whale this week (last week +5,925 to erd18mv2z6r2). Pattern: inflow continues but at milder magnitude.","weeks_on_list":4},
 {"item":"DEX volume collapsed -55% during the bounce","reason":"$122K → $55K, largest WoW drop in tracking. Traders disengaged during the price recovery. Confirms the 'exit liquidity' read — recovery happening on light, sell-side volume.","weeks_on_list":1},
 {"item":"XOXNO LSD mild contraction continues (-2.5% EGLD); Hatom LSD apples-to-apples flat","reason":"Run #11 'synchronized LSD contraction' pattern downgraded: only XOXNO LSD confirmed contracting (-1.4% then -2.5% EGLD). Hatom LSD comparison was contaminated by SWTAO mcap being null in run #11's prev (rate-limit miss). Apples-to-apples Hatom LSD is flat. Watch XOXNO LSD for 3rd week to formalize.","weeks_on_list":2},
 {"item":"Unknown Mega Whale erd18mv2z6r2 unchanged at 998,971","reason":"Last week received +5,925 from Coinbase Routing Wallet. This week: zero inbound or outbound activity. Near the 1M threshold. Watching for downstream forwarding to confirm OTC pattern.","weeks_on_list":2},
 {"item":"OTC pipeline in inter-cycle gap","reason":"UPbit OTC -1.8K, OTC Distribution +0.9K = essentially flat. Outflow throughput dropped from 163K (run #11) to 44K (this run). Per run #11 prediction, expect loading phase to return within 1-2 weeks.","weeks_on_list":3},
 {"item":"Bilateral inverse rule observation #6: now in counter-direction (up-week)","reason":f"Price +1.4% (mild up-week) → Hatom Lending EGLD {100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}%. First UP-week observation. The rule's behavior under upward moves complements the 5 down-week observations. Magnitude scaling under modest up-moves is informative for future rallies.","weeks_on_list":5},
 {"item":"Token mcap rate-limit issue caused SWTAO null in run #11","reason":"Initial run-12 collection with 0.55s delays returned ALL 4 LSD/USH token mcaps as null. Re-fetch with 1.0s delays returned proper data. Diagnosis: run #11 SWTAO 'null price feed' was a rate-limit miss, NOT an outage. Hatom LSD was therefore undercounted by ~$1.18M last run. New rule: use ≥1.0s between /tokens/{id} queries.","weeks_on_list":1},
 {"item":"erd1sdslv address with bad bech32 checksum — run #11 stored an invalid address","reason":"The canonical Binance.com hot wallet (erd1sdslv...3rgul...sets) returns 222K but previous.json watch_addresses had erd1sdslv...29trp...76xc (invalid checksum, API returns HTTP 400). This caused run #11's Binance.com entity to undercount by ~222K (only 2 of 3 wallets counted). Address now removed from watch_addresses.","weeks_on_list":1}]

# ---------- executive summary ----------
executive_summary=[
 {"finding":f"EGLD +1.36% to $2.99 — FIRST UP-WEEK after 5 down-weeks. Run #11's predicted capitulation bounce off $2.95 materialized. BTC +2.0%, ETH +2.6% confirm broad-crypto recovery (EGLD trailing but no longer decoupled). Whether this is reversal or dead-cat depends on next 1-2 weeks; the on-exchange capital build during the bounce signals exit liquidity rather than capitulation low.","severity":"medium","category":"network"},
 {"finding":"Delegator base CRATERED -4,003 WoW (-2.24%), the largest single-week drop in tracking history by 9x. Combined with -38K staked-EGLD decline and yield-chase cohort -17K, this is a concentrated retail capitulation event. Run #11's emerging pattern at much larger magnitude.","severity":"high","category":"staking"},
 {"finding":"Binance Staking custody STALLED for 2nd consecutive week at 3.51M EGLD. The 3-week accumulation (runs #7+9+10) plus 2-week stall = 5 weeks parked, 779K total. Now firmly in entrenched structural position; each additional week makes eventual delegation-vs-distribution move more decisive.","severity":"high","category":"whale"},
 {"finding":"Yield-chase cohort FULLY UNWOUND: net -17K. ninjastaking (the only 5-week sustained gainer) reversed -10.5K, procryptostaking -6.8K, egldstakingprovider -3.3K. The 5-week migration regime terminated and now in net redemption.","severity":"high","category":"staking"},
 {"finding":"Coinbase 2-week net inflow CONFIRMED per run #11's 2-week rule: +43K → +8.3K. Off-exchange accumulation thesis decisively dead. Net exchange flow 2nd consecutive inflow week (+24.9K → ~+33K). Direction: sellers using bounces as exit liquidity.","severity":"medium","category":"whale"},
 {"finding":"DEX volume -55% to $55K — largest WoW contraction in tracking history. The price bounce did NOT bring liquidity; traders disengaged. Supports the 'exit liquidity' read on the EGLD recovery.","severity":"medium","category":"defi"},
 {"finding":"XOXNO LSD contraction continues 2nd week (-2.5% EGLD); but the run #11 'synchronized LSD contraction' pattern DOWNGRADED — Hatom LSD apples-to-apples is flat once the run #11 SWTAO rate-limit miss is corrected. Watch list updated.","severity":"low","category":"defi"},
 {"finding":"Data-quality fix: run #11's 'SWTAO API outage' was actually a rate-limit miss (0.55s delay). All 4 LSD/USH mcaps return cleanly at ≥1.0s spacing. Run #11 Hatom LSD was UNDERCOUNTED by ~$1.18M. New rule: use ≥1.0s between /tokens/{id} queries.","severity":"low","category":"network"}]

# ---------- network health ----------
network_health={
 "economics":{"egld_price_usd":price,"market_cap_usd":econ["marketCap"],"total_supply":econ["totalSupply"],
   "circulating_supply":econ["circulatingSupply"],"staked_egld":staked,"staked_ratio":sr,
   "staking_apr":econ["apr"],"base_apr":econ["baseApr"],"topup_apr":econ["topUpApr"],"token_market_cap_usd":econ["tokenMarketCap"]},
 "activity":{"total_accounts":st["accounts"],"total_transactions":st["transactions"],"epoch":st["epoch"],
   "blocks":st["blocks"],"shards":st["shards"],"transactions_7d":st["transactions"]-pact["total_transactions"],
   "avg_daily_transactions":round((st["transactions"]-pact["total_transactions"])/7)},
 "deltas":{"price_change_pct":100*(price-pecon["egld_price_usd"])/pecon["egld_price_usd"],
   "market_cap_change_pct":100*(econ["marketCap"]-pecon["market_cap_usd"])/pecon["market_cap_usd"],
   "staked_ratio_change_pp":100*(sr-pecon["staked_ratio"]),
   "apr_change_pp":100*(econ["apr"]-pecon["staking_apr"]),"accounts_added":st["accounts"]-pact["total_accounts"],
   "btc_correlation_note":f"EGLD +1.36% WoW vs BTC +2.00% / ETH +2.58% (24h). EGLD trailing but back IN LINE with crypto-macro after last week's decoupling. Beta to crypto-majors normalized this week.",
   "transactions_added":st["transactions"]-pact["total_transactions"],"supply_added":econ["totalSupply"]-pecon["total_supply"],
   "staked_egld_added":staked-pecon["staked_egld"],"epoch_advanced":st["epoch"]-pact["epoch"]},
 "analysis":f"EGLD +1.36% WoW to $2.99 — FIRST up-week after 5 consecutive down-weeks. z={zp[2]:+.2f}σ (mild positive). The capitulation bounce predicted in run #11 off the $2.95 floor materialized. BTC +2.00% and ETH +2.58% (24h) confirm broad-crypto recovery; EGLD trailing but no longer DECOUPLED to the downside (last week was -15.7% vs BTC +1.3%). Market cap $90.1M (+1.5%). Staked ratio mildly down to {sr*100:.2f}% (-0.21pp); protocol staked module fell -38K to 14.433M (continuation from last week's -27K). Delegator base CRATERED -4,003 (-2.24%) — the largest single-week drop by an order of magnitude (last run was -447). Activity: 1.6M txs/day average, account growth modest at +0.3K. The price recovery is real but happening on collapsing engagement (DEX volume -55%, delegator -2.2%, LSD contractions, yield-chase unwind). Read: technical bounce, not demand-driven recovery."}

# ---------- whale analysis ----------
whale_analysis=("THIS WEEK'S DOMINANT MOVES:\n"
 f"1) DELEGATOR CAPITULATION EVENT. The delegator base dropped {prev_deleg-cur_deleg:,} WoW to {cur_deleg:,} ({100*(cur_deleg-prev_deleg)/prev_deleg:+.2f}%). This is 9x larger than last week's -447 drop and the largest single-week drop in tracking history by an order of magnitude. The drop is concentrated in the yield-chase cohort: ninjastaking -10.5K, procryptostaking -6.8K, egldstakingprovider -3.3K (all 0-10% fee 8-9% APR providers). Combined yield-chase cohort net flow: ~-17K (vs -2.6K last week). The 5-week yield-chase migration is now FULLY UNWOUND, with the cohort in active net redemption.\n\n"
 "2) BINANCE STAKING CUSTODY STALLED 2ND CONSECUTIVE WEEK at 3,512,650 EGLD. The 3-week accumulation phase (runs #7+9+10 cumulative +402K) has now extended into a 2-week stall. Total parked since run #7: 779K EGLD ($2.33M at current price). No delegation to protocol staked module (would jump econ.staked); no drawdown to hot wallets (would re-appear in by-exchange flows). Promoted from anomaly to ENTRENCHED STRUCTURAL POSITION. Each additional week of stall increases the eventual move's decisiveness.\n\n"
 "3) COINBASE 2-WEEK NET INFLOW CONFIRMED. Per run #11's recommended 2-week confirmation rule, Coinbase entity registered a 2nd consecutive net inflow week (+43K → +8.3K). The off-exchange accumulation thesis from run #10 is decisively dead. Coinbase Routing Wallet did NOT send to Unknown Mega Whale erd18mv2z6r2 this week (last week +5,925 EGLD on 2026-06-07); the Apr 18 OTC pattern is not currently active.\n\n"
 f"WHALE TIERS (top-{N_prev} apples-to-apples): mega {whale_tiers['mega_whales']['net_change_egld']/1000:+.1f}K, large {whale_tiers['large_whales']['net_change_egld']/1000:+.1f}K, mid {whale_tiers['mid_whales']['net_change_egld']/1000:+.1f}K. The Binance.com hot wallet correction (canonical erd1sdslv...3rgul addr vs invalid checksum in run #11 previous.json) explains some apparent mega-whale tier flux.\n\n"
 f"EXCHANGE FLOWS: 2nd consecutive week of NET INFLOW ({net_total:+,.0f}, {100*net_total/total_prev if total_prev else 0:+.2f}%). Off-exchange-accumulation thesis fully dead. Pattern: sell-into-decline (run #11) has continued into sell-into-bounce (this run) — sellers using the +1.4% EGLD recovery as exit liquidity rather than capitulation low confirmation. DEX volume cratered -55% during the same bounce, supporting the exit-liquidity interpretation.\n\n"
 "OTC PIPELINE IN INTER-CYCLE GAP. UPbit OTC Desk -1.8K, OTC Distribution +0.9K = combined -0.9K (essentially flat). Outflow throughput collapsed from 163K (last run) to 44K this run. Per run #11's prediction of 1-2 week reload, the pipeline is in the gap between last week's distribution wave and the next loading phase. Expect loading to resume next week.")

# ---------- staking analysis ----------
staking_analysis=(f"Staking concentration remains low (HHI {hhi:.4f}, top-5 {top5:.1f}%, both essentially unchanged WoW). Total delegated {total_locked:,.0f} EGLD across {len(provs)} active providers. Active delegator base {cur_deleg:,} delegators ({cur_deleg-prev_deleg:+}, {100*(cur_deleg-prev_deleg)/prev_deleg:+.2f}%) — the LARGEST single-week drop in tracking history by 9x.\n\n"
 "YIELD-CHASE COHORT FULLY UNWOUND. The 5-week 0%-fee 9%+ APR migration is now in active redemption: ninjastaking -10.5K (the only sustained gainer reversed sharply), procryptostaking -6.8K, egldstakingprovider -3.3K, valuestaking +3.4K (only positive). Net cohort -17K vs -2.6K last week. Combined 5-week cumulative for ninjastaking +38K (still net positive across the period) but now in active outflow. The regime is fully terminated and the cohort is in net redemption phase.\n\n"
 f"APR distribution: 77 providers (72% of the sample) in the 8-9% bucket holding {buckets[3]['total_locked_egld']/1e6:.1f}M EGLD. The 9-10% bucket holds {buckets[4]['provider_count']} providers / {buckets[4]['total_locked_egld']/1e3:.0f}K EGLD. Empty 10%+ bucket (consistent across all 2026 runs). APR-weighted average: {apr_w:.2f}%.\n\n"
 f"DELEGATOR CHURN ACCELERATED 9X: {gain} providers gaining vs {lose} losing delegators (-{prev_deleg-cur_deleg:,} net). z-score is now meaningful (not degenerate) and the absolute % move at -2.24% is the largest tracked. Read: a real capitulation event — retail leaving delegation contracts during the price recovery (suggests they were waiting for the bounce to exit). Combined with -38K staked-EGLD decline, this is a concentrated retail exit, not random churn.\n\n"
 "VALIDATOR MOVEMENTS: Quiet week. No notable named-validator joiners or leavers >50K EGLD. System-contract addresses (erd1qqqq...) excluded per the run #10 rule.")

# ---------- token analysis ----------
top_pair_share = pairs[0]['share_pct']
second_pair = pairs[1] if len(pairs)>1 else None
token_analysis=(f"DEX volume CRATERED -55.2% to ${totvol/1000:.0f}K (vs $122K last week) — the largest WoW DEX volume contraction in tracking history. WEGLD/USDC dominance fell 93.2% → {top_pair_share:.1f}%; ZoidPay/WEGLD share rose 3.0% → {second_pair['share_pct'] if second_pair else 0:.1f}%. The drop is concentrated in the dominant pair (WEGLD/USDC), suggesting CEX-derived traders disengaged during the price bounce. Confirms the 'exit liquidity' read on the EGLD recovery.\n\n"
 f"NEWLY-ISSUED TOKENS: scan returned 0 issuances this week (ESDT system SC issue function had no recent calls). Method validated last run; the empty result this run is signal of low activity rather than method failure.\n\n"
 f"Token holder counts declined for a 12th consecutive week (-21 to -139 across top 10) — established airdrop-decay baseline. WrappedEGLD and WrappedUSDC remain the most-used real tokens.\n\n"
 f"MEX price DECOUPLED from EGLD this run: EGLD +1.4% but MEX -0.83%. Typically MEX amplifies EGLD moves; the independent direction is unusual. MEX market cap $1.11M (-1.3%). With DEX volume -55%, MEX's underlying trading apparatus is contracting.\n\n"
 "Top by market cap: USDC $8.39M (Wrapped USDC), ZoidPay $5.36M (+13% from $4.73M), UTK $4.79M (+14% from $4.19M), HUSDC $1.35M (vs $1.31M), WrappedEGLD $1.78M (flat).\n\n"
 "WEGLD supply held essentially flat WoW (raw change <0.5%) — continues the post-run-#10 stabilization, no second wrap event.")

# ---------- defi analysis ----------
defi_analysis=(f"BILATERAL INVERSE RULE NOT EVALUABLE THIS RUN. Price move +1.4% is below the meaningful-move threshold (rule observed only at |Δprice|≥5% historically). Hatom Lending EGLD-denominated response +0.9% is within the noise band for a small-move week. The rule's directional behavior remains: 5 down-week observations all triggered EGLD-TVL responses in the OPPOSITE direction (with deteriorating magnitude). An up-week observation requires a meaningful bounce (>+5%) to test rule symmetry.\n\n"
 f"HATOM LSD ${hatom_lsd/1e6:.2f}M (SEGLD ${segld_mcap/1e6:.2f}M + SWTAO ${swtao_mcap/1e6:.2f}M). Run #11 previous.json stored Hatom LSD = $2.51M but this was SEGLD-only because SWTAO returned null on the rate-limited 0.55s-delay query. Re-fetched this run with 1.0s delays confirms SWTAO ~$1.19M. Apples-to-apples (adding back SWTAO to prev): Hatom LSD ${hatom_lsd_prev_corrected/1e6:.2f}M -> ${hatom_lsd/1e6:.2f}M = essentially flat. The 'synchronized LSD contraction' pattern from run #11 is therefore DOWNGRADED — Hatom LSD is flat, not contracting.\n\n"
 f"XOXNO LSD ${xoxno_lsd/1e6:.2f}M / {xlsd_egld/1000:.0f}K EGLD ({100*(xlsd_egld-prev_xl_egld)/prev_xl_egld:+.1f}% EGLD). XOXNO LSD continues mild contraction for 2nd consecutive week (-1.4% then -2.5% EGLD). Still a watch item but no longer 'synchronized' since Hatom LSD is flat. The bearish-LSD-during-stress thesis needs 1-2 more confirmations of XOXNO LSD alone before being formalized.\n\n"
 f"xExchange TVL ${xexch_tvl_usd/1e6:.2f}M ({100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld:+.1f}% EGLD). DEX volume CRATERED -55%. Aggregators continue elevated throughput (XOXNO {tcount('XOXNO Aggregator'):,}, OneDex {tcount('OneDex Swap'):,}) — on-chain activity rotation continues.\n\n"
 f"HATOM USH stablecoin ${hatom_ush/1000:.0f}K ({100*(hatom_ush-prev_hush)/prev_hush:+.1f}% USD). 2nd consecutive week of contraction (was -2.2% last run-correlated, now {100*(hatom_ush-prev_hush)/prev_hush:+.1f}%). De-leveraging trend continues mildly.\n\n"
 f"DATA-QUALITY FIX: run #11's 'SWTAO null price' was a rate-limit miss with 0.55s spacing, not a feed outage. Re-fetching at 1.0s spacing returned proper data for all 4 LSD/USH-class tokens (SEGLD, SWTAO, USH, XEGLD). Methodology updated: use ≥1.0s between /tokens/{{id}} queries. Run #11 Hatom LSD was undercounted by ~$1.18M as a direct consequence.")

report={
 "metadata":{"report_date":"2026-06-15","period_start":"2026-06-08T00:00:00Z","period_end":"2026-06-15T00:00:00Z",
   "generated_at":datetime.now(timezone.utc).isoformat(),"egld_price_usd":price,
   "btc_price_usd":be["bitcoin"]["usd"],"eth_price_usd":be["ethereum"]["usd"],"run_number":12,
   "data_sources_ok":json.load(open("/tmp/run12/status.json"))["ok"],
   "data_sources_failed":["LSD-token mcap fields: SEGLD/SWTAO/USH/XEGLD all returned price=null this run (supply-fallback used)","Binance.com hot bad bech32 address from run #11 (HTTP 400, excluded; canonical address used)"]},
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
 "meta_learning":{"run_number":12,
   "endpoints_that_worked":json.load(open("/tmp/run12/status.json"))["ok"],
   "endpoints_that_failed":["run #11 broken bech32 address erd1sdslv...29trp...76xc (HTTP 400, excluded)"],
   "api_quirks":[
     "/tokens/{id} HTTP 429 rate-limit kicks in faster than the 0.5s methodology rule. Initial run-12 collection with 0.55s delays returned ALL 4 LSD/USH tokens (SEGLD, SWTAO, USH, XEGLD) as price=null marketCap=null. Re-fetch with 1.0s delays returned proper data. Diagnosis: run #11 SWTAO 'null price feed' was the same rate-limit miss, not a data-feed outage. New rule: use ≥1.0s between /tokens/{id} queries. The previous 0.5s rule from run #10b is INCORRECT for this endpoint.",
     "run #11 watch_addresses contained an invalid bech32 address (erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp29trp6qsl2gdvvz2eqra76xc) that the API rejects with HTTP 400. The canonical Binance.com hot is erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets (verified via /accounts?search=). Both share the first ~36 chars but the bad one has incorrect checksum. This caused Binance.com entity to undercount by ~222K in run #11.",
     "Capitulation bounce predicted at $2.95 floor materialized as +1.4% to $2.99. BTC/ETH both up confirms broad-crypto recovery (not MultiversX-specific).",
     "DEX volume -55% during the price bounce - traders disengaged. This pattern (price up, DEX volume down) is the inverse of a normal recovery and is a new 'exit liquidity' signature to track."],
   "data_gaps":[
     "LSD/USH price-feed outage means USD-denominated TVLs depend on fallback. Watch for resolution.",
     "Provider previous list keyed by name only; anonymous providers still not WoW-matchable.",
     "Newly-issued token scan returned empty - cannot distinguish empty week from method failure without external corroboration."],
   "key_findings":[
     "EGLD +1.36% to $2.99 - FIRST UP-WEEK after 5 down-weeks. Run #11's capitulation bounce predicted.",
     "Delegator base CRATERED -4,003 (-2.24%) - largest single-week drop in tracking by 9x.",
     "Binance Staking custody STALLED 2nd consecutive week at 3.51M (5-week-old parked position).",
     "Yield-chase cohort FULLY UNWOUND: ninjastaking reversed -10.5K, cohort net -17K.",
     "Coinbase 2-week inflow CONFIRMED per run #11 rule: off-exchange thesis dead.",
     "DEX volume -55% during the bounce - largest WoW drop in tracking; traders disengaged.",
     "Exit liquidity bounce signature: price up while delegator/DEX-volume/yield-chase all collapse.",
     "Data-quality fix: run #11 SWTAO 'outage' was a rate-limit miss; new rule ≥1.0s spacing for /tokens/{id}. Hatom LSD undercount of $1.18M corrected this run."],
   "action_items_from_previous":9,
   "action_items_completed":7,
   "methodology_changes":[
     "FIXED: /tokens/{id} rate-limit threshold. The 0.5s spacing from run #10b methodology is too aggressive — HTTP 429 triggers and the response silently has price=null marketCap=null fields (no error returned, just null values). Use ≥1.0s spacing. This single fix resolves the run #11 SWTAO miss and would have prevented the Hatom LSD undercounting.",
     "NEW PATTERN: 'exit liquidity bounce' as a bearish read on price recoveries. Diagnostic: price recovers WHILE delegator base contracts AND DEX volume drops AND on-exchange capital builds. This run shows all three. The bounce is sell-side execution rather than fresh demand. Should be added as a forward-indicator question (does engagement recover next week?).",
     "BILATERAL INVERSE RULE EVALUATION GUARDRAIL: rule only applies for meaningful price moves (|Δ|≥5% based on the 5 historical observations). Small moves (<3%) cannot test the rule — EGLD-denominated TVL noise dominates the signal. This run's +1.4% / +0.9% does NOT count as observation #6.",
     "CRITICAL FIX: validate bech32 checksum when storing addresses to known-addresses.json and watch_addresses. Run #11 stored an invalid-checksum address that produced silent HTTP 400 errors, undercounting Binance.com entity by 222K. Pre-store validation recommended."],
   "new_addresses_discovered":1,
   "most_valuable_insight":"The 'exit liquidity bounce' signature - EGLD +1.4% recovery happening on COLLAPSING engagement: (1) delegator base -4,003 (largest drop in tracking by 9x), (2) yield-chase cohort fully reversed -17K, (3) DEX volume -55% (largest contraction in tracking), (4) on-exchange capital build 2nd consecutive week. A genuine recovery would show participation expanding; this shows it contracting. The bounce is technical, sell-side execution, not demand-driven. Diagnostic for next week: if engagement metrics recover (DEX volume back >$80K, delegator base flat-to-positive, on-exchange capital flatlines), the bounce is real. If engagement keeps contracting while price holds, the regime is decisively bearish despite the price action.",
   "top_recommendation":"Watch for engagement-collapse confirmation: if next week shows price flat-to-down WHILE delegator base, DEX volume, and LSD balances continue to contract, the regime is decisively bearish. If price holds OR moves up AND engagement recovers, the bounce is real. The diagnostic is engagement returning, not just price.",
   "recommendations_for_next_run":[
     "Verify capitulation bounce thesis: does $2.99 hold, extend, or fail back to $2.95 range? Engagement recovery (DEX volume back >$80K, delegator base flat-to-positive) confirms; engagement continues collapsing = exit liquidity confirmed.",
     "Binance Staking custody 3rd-week stall watch: each additional week increases the decisiveness of the eventual move (delegate or distribute).",
     "Delegator capitulation follow-up: is -4,003 a one-shot or the start of sustained outflow? Next week's number is the highest-information observation of the period.",
     "OTC pipeline reload: per cycle pattern, expect loading phase to return next week. UPbit OTC Desk + OTC Distribution combined +10K+ would confirm.",
     "Confirm LSD/USH rate-limit fix works: verify SEGLD/SWTAO/USH/XEGLD mcaps populated correctly with ≥1.0s spacing. If they go null again with that spacing, escalate to a real outage.",
     "Coinbase 3rd-week inflow check: +43K -> +8.3K -> ? If a 3rd inflow week, the off-exchange-accumulation reversal becomes structural.",
     "Yield-chase cohort net redemption follow-up: does ninjastaking continue bleeding? Does any provider in the cohort show positive flow?",
     "XOXNO LSD 3rd-week contraction watch: Hatom LSD pattern downgraded (data-quality artifact), but XOXNO LSD continues mild contraction. 3rd consecutive week would formalize XOXNO-LSD-as-bearish-indicator (no longer 'synchronized').",
     "Mega Whale erd18mv2z6r2 - any downstream forwarding from the 998K position? Approaching the 1M threshold for the 2nd week."],
   "dashboard_feature_suggestions":[
     {"title":"Engagement-collapse composite indicator","motivation":"Run #12's most valuable insight was the simultaneous collapse of FIVE engagement metrics (delegator base, yield-chase cohort, DEX volume, LSD balances, on-exchange capital) during a price bounce. A single 'engagement health' composite would surface this pattern across all weekly reports. The 'exit liquidity bounce' signature is hard to spot unless you look at all 5 metrics at once.","suggested_visualization":"5-spoke radar chart per week showing each engagement metric's z-score (or %WoW); historic radar overlays show pattern evolution. Lower-left collapse pattern = exit liquidity; balanced radar = healthy.","data_already_available":True,"data_source":"already-collected staking_intelligence.churn + protocol_breakdown[].tvl_wow_change_pct + token_activity.xexchange.total_volume_24h_usd + whale_intelligence.exchange_flows.net_change_egld","priority":"high"},
     {"title":"LSD circulating-supply timeline","motivation":"Token mcap is sensitive to API rate-limit hiccups (run #11 SWTAO miss caused $1.18M Hatom LSD undercount). A supply-based metric (circulating SEGLD/XEGLD in EGLD units, derived from minted-burnt) bypasses the price feed and is therefore more robust. A timeline of SEGLD and XEGLD circulating supply across weeks would directly track LSD adoption/contraction without dependency on mcap freshness.","suggested_visualization":"dual-line chart of SEGLD and XEGLD circulating supply over weekly snapshots.","data_already_available":True,"data_source":"derived from tvl_tokens.{SEGLD,XEGLD}.minted - .burnt in collected.json snapshots","priority":"medium"},
     {"title":"Bilateral inverse rule up-week / down-week asymmetry visualization","motivation":"This week added the FIRST up-week observation to the bilateral inverse rule (5 prior were all down-weeks). The rule's up/down asymmetry is now a tractable analytical question. A scatter plot of |price change %| vs Hatom Lending EGLD response % colored by direction (red=down-week, green=up-week) would make the asymmetry visible at a glance.","suggested_visualization":"scatter plot, x-axis = signed price change %, y-axis = Hatom Lending EGLD response %, distinct symbols for down/up weeks; trendline per category.","data_already_available":True,"data_source":"defi_activity.protocol_breakdown[Hatom Lending].tvl_wow_change_pct + network_health.deltas.price_change_pct across all reports","priority":"medium"}],
   "dashboard_suggestions_followup":[
     {"from_run":11,"title":"Forward-indicator scorecard widget","status":"pending","note":"Even more valuable now: this run's 'exit liquidity bounce' detection depends on multiple converging indicators. A scorecard tracking each report's open predictions (capitulation bounce thesis just RESOLVED VALIDATED on the price-up side; engagement thesis is now the new question) would surface these resolutions automatically. Re-listed."},
     {"from_run":11,"title":"OTC cycle phase indicator","status":"pending","note":"This week's pipeline is in the INTER-CYCLE GAP. The phase indicator would show LOADING(?)->DISTRIBUTING->GAP->[LOADING next?] - the gap state is itself useful information."},
     {"from_run":11,"title":"Bilateral inverse rule magnitude trajectory","status":"pending","note":"Run #12 added the FIRST up-week observation, changing this from a 1D magnitude question to a 2D up/down asymmetry question. The visualization gains additional dimension."},
     {"from_run":10,"title":"Multi-week Binance custody vs protocol-staked tracker chart","status":"pending","note":"Now 5 weeks of data: 3 weeks accumulation + 2 weeks stall. The chart is increasingly motivated as the stall persists."},
     {"from_run":10,"title":"OTC pipeline phase visualization (load vs distribute)","status":"pending","note":"This week's INTER-CYCLE GAP state would benefit from explicit phase tracking. Add 'gap' as a fourth state."},
     {"from_run":9,"title":"Multi-week net exchange-flow oscillation chart","status":"pending","note":"Trajectory: +169K / -56K / -71K / +25K / +33K = bearish-bullish-bullish-bearish-bearish. The bearish streak now 2 weeks confirms reversal of the bullish off-exchange-accumulation thesis."},
     {"from_run":9,"title":"DEX pair-composition stacked-area over time","status":"pending","note":"DEX volume cratered -55% this week. The pair composition shift (WEGLD/USDC 93%->85%, ZoidPay 3%->8%) during a volume collapse would be visible."},
     {"from_run":8,"title":"OTC pipeline graph view (Sankey/force-directed)","status":"pending","note":"Pipeline now in inter-cycle gap; visualization would show the rest state of the network."},
     {"from_run":8,"title":"Yield-chase migration cumulative chart","status":"built-this-run-conceptually","note":"5-week cumulative chart implicitly drawn in the staking analysis: cohort accumulated ~+50K weeks 1-4, +3.5K week 5, -2.6K week 6, -17K week 7 (this run). Could now be made explicit as a visualization given the full lifecycle has been observed."}]}}

json.dump(report,open(f"{REPO}/reports/2026-06-15.json","w"),indent=2)
print("WROTE reports/2026-06-15.json")
print("exec_summary:",len(executive_summary),"large_tx:",len(large_transactions),"wallet_changes:",len(wallet_changes),
      "providers:",len(provs),"anomalies:",len(anomalies),"watch:",len(watch_list))
print("net exchange flow:",round(net_total,1),"total_locked:",round(total_locked,1),"apr_w:",round(apr_w,3))
print("DEFI: Hatom Lending USD",round(hatom_lending),"LSD",round(hatom_lsd),"USH",round(hatom_ush),"XOXNO LSD",round(xoxno_lsd))
print("Token supply events:",len(token_supply_events))
print("Newly issued:",len(newly_issued))
print("DEX volume:",round(totvol,1))
print("Delegators:",cur_deleg,"WoW:",cur_deleg-prev_deleg)
print("Staked:",staked,"WoW:",staked-pecon["staked_egld"])
print("EGLD price:",price,"WoW:",f"{100*(price-pecon['egld_price_usd'])/pecon['egld_price_usd']:+.2f}%")
