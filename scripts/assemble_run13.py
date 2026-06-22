#!/usr/bin/env python3
"""Assemble reports/2026-06-22.json (run #13) from collected data."""
import json, math
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D = json.load(open("/tmp/run13/collected.json"))
prev = json.load(open(f"{REPO}/data/previous.json"))
kn = json.load(open(f"{REPO}/data/known-addresses.json"))
learn = json.load(open(f"{REPO}/data/learnings.json"))
prevcol = json.load(open(f"{REPO}/data/collected/2026-06-15.json"))  # for supply WoW

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
 "Binance":"Net -6.3K (-0.1% of entity total). Binance.com hot wallet -6.3K; Binance Staking custody UNCHANGED at 3,512,650 EGLD for the 3rd CONSECUTIVE WEEK. The custody stall is now 3 weeks (after a 3-week accumulation phase runs #7+9+10) = 6 weeks of an undeployed 779K-EGLD position ($2.22M at current price). Hot-wallet outflow is mild operational drift; the headline Binance signal remains the entrenched, frozen custody position.",
 "Coinbase":"+6.0K (+3.5%) - 3rd CONSECUTIVE net inflow week (+43K -> +8.3K -> +6.0K). Primary wallet +3.9K, secondary +2.0K. Per run #11's 2-week confirmation rule (now exceeded at 3 weeks), the off-exchange-accumulation reversal is now STRUCTURAL, not a transient. Coinbase has been a net depositor through the entire bounce-and-fail sequence - consistent with distributing into any strength.",
 "Crypto.com":"+7.7K (+4.4%). Reversed last week's -7.3K. Material inflow, 2nd-largest entity gain this week.",
 "Bybit":"+10.9K (+2.2%) on the cold wallet - the single largest exchange inflow this week. Continues the deposit-side drift visible across recent runs.",
 "UPbit":"Cold wallet -5.2K (-0.4%) - mild outflow. Separately, UPbit OTC Desk +4.8K and OTC Distribution +2.3K (the OTC pipeline reloaded - see OTC section).",
 "MEXC":"+1.1K (+1.2%). Mild inflow, reversing recent outflow drift.",
 "KuCoin":"-3.9K (-12.4%) on the cold wallet - the largest pct outflow this week, but small in absolute EGLD (27K base).",
 "Bitget":"+0.4K (+0.4%). Flat.",
 "Gate.io":"+1.2K (+2.1%). Mild inflow continues.",
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
    "signal":f"Net exchange flow {net_total:+,.0f} EGLD ({100*net_total/total_prev if total_prev else 0:+.2f}%) - 3rd CONSECUTIVE week of net INFLOW. The off-exchange-accumulation thesis (run #10) is now decisively and structurally dead: Coinbase has posted 3 straight inflow weeks (+43K/+8.3K/+6.0K), and aggregate exchange balances rose through the entire failed-bounce sequence. Net inflow during a -4.7% price decline = sell-side deposits. This is the textbook bearish read, and it directly corroborates run #12's 'exit liquidity bounce' diagnosis: the +1.4% bounce last week drew sellers, not buyers, and price has now broken to a new local low at $2.85. Binance Staking custody remains frozen at 3.51M for the 3rd week - the parked-capital thesis stays dead.",
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

protocol_breakdown=[
 {"protocol":"xExchange","category":"dex","addresses_tracked":16,"tvl_usd":xexch_tvl_usd,"tvl_egld":xexch_tvl_egld,
  "tvl_wow_change_pct":100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld,"transfers_24h":None,"volume_24h_usd":totvol,
  "notable_events":f"DEX volume ${totvol/1000:.0f}K (+{100*(totvol-prev_dexvol)/prev_dexvol:.0f}% off last week's $55K floor, but still ~50% below the $122K of two weeks ago). WEGLD/USDC dominance {pairs[0]['share_pct']:.1f}% (down from 85.1%); ZoidPay/WEGLD share {pairs[1]['share_pct'] if len(pairs)>1 else 0:.1f}% (up from 8.1%). WEGLD supply WoW {wegld_chg_pct:+.2f}% (flat). The bounce in volume off the floor is shallow - liquidity remains depressed.","health_signal":"shrinking"},
 {"protocol":"Hatom Lending","category":"lending","addresses_tracked":13,"tvl_usd":hatom_lending,"tvl_egld":hl_egld,
  "tvl_wow_change_pct":100*(hl_egld-prev_hl_egld)/prev_hl_egld,"transfers_24h":tcount("Hatom EGLD MM"),
  "notable_events":f"TVL ${hatom_lending/1e6:.2f}M USD ({100*(hatom_lending-prev['defi_tvl']['Hatom Lending'])/prev['defi_tvl']['Hatom Lending']:+.1f}%), {hl_egld/1000:.0f}K EGLD ({100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}% EGLD). Bilateral inverse rule NOT EVALUABLE: price move -4.68% is just below the |Δprice|>=5% threshold. Note the EGLD-denominated +3.2% in the OPPOSITE direction to price IS consistent with the rule's historical sign (depositors hold/DCA during dips), but at a sub-threshold price move it does not formally count as an observation.","health_signal":"flat"},
 {"protocol":"Hatom Liquid Staking","category":"liquid_staking","addresses_tracked":2,"tvl_usd":hatom_lsd,"tvl_egld":hlsd_egld,
  "tvl_wow_change_pct":100*(hlsd_egld-prev_hlsd_egld)/prev_hlsd_egld,"transfers_24h":tcount("Hatom Liquid Staking"),
  "notable_events":f"SEGLD ${segld_mcap/1e6:.2f}M + SWTAO ${swtao_mcap/1e6:.2f}M = ${hatom_lsd/1e6:.2f}M USD ({100*(hatom_lsd-prev_hlsd)/prev_hlsd:+.1f}%). USD drop is mostly PRICE: SEGLD supply {segld_supply_wow:+.2f}% (mild redemption), SWTAO supply {swtao_supply_wow:+.2f}% (flat). SWTAO mcap fell on TAO price, not MultiversX redemptions. On a supply basis Hatom LSD is essentially FLAT - the 'contraction' is a price artifact.","health_signal":"flat"},
 {"protocol":"Hatom USH","category":"stablecoin","addresses_tracked":4,"tvl_usd":hatom_ush,"tvl_egld":ush_egld,
  "tvl_wow_change_pct":100*(hatom_ush-prev_hush)/prev_hush,"transfers_24h":None,
  "notable_events":f"USH mcap ${hatom_ush/1000:.0f}K ({100*(hatom_ush-prev_hush)/prev_hush:+.1f}% USD). USH supply {ush_supply_wow:+.2f}% WoW - the 2-week burn/de-leveraging trend has ENDED; USH is now flat. CDP de-risking pressure paused.","health_signal":"flat"},
 {"protocol":"XOXNO LSD","category":"liquid_staking","addresses_tracked":2,"tvl_usd":xoxno_lsd,"tvl_egld":xlsd_egld,
  "tvl_wow_change_pct":100*(xlsd_egld-prev_xl_egld)/prev_xl_egld,"transfers_24h":tcount("XOXNO LSD"),
  "notable_events":f"XEGLD ${xoxno_lsd/1e6:.2f}M ({100*(xoxno_lsd-prev['defi_tvl']['XOXNO LSD'])/prev['defi_tvl']['XOXNO LSD']:+.1f}% USD), XEGLD supply {xegld_supply_wow:+.2f}% WoW. The run #12 'XOXNO LSD 3rd-week contraction' watch is NOT CONFIRMED - on a supply basis XEGLD actually GREW {xegld_supply_wow:+.2f}%. The mild USD decline is purely EGLD price. The bearish-LSD-during-stress thesis is now dead on both LSDs.","health_signal":"flat"},
 {"protocol":"XOXNO Aggregator","category":"aggregator","addresses_tracked":1,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("XOXNO Aggregator"),
  "notable_events":f"Throughput {tcount('XOXNO Aggregator'):,} daily transfers (down from a ~21K baseline; on-chain routing activity cooled alongside the broader engagement slump).","health_signal":"flat"},
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
  "description":f"EGLD {100*(price-pp)/pp:+.2f}% WoW to ${price:.2f}, z={zp[2]:+.2f}σ (N={len(rb['egld_price_usd'])}). The capitulation bounce FAILED: after last week's +1.36% relief rally to $2.99, price broke back below the $2.95 floor to a NEW local low at $2.85. EGLD again DECOUPLED to the downside - on a 24h basis BTC was flat (-0.0%) and ETH +0.84%, while WoW BTC -2.49% and ETH +1.43% vs EGLD -4.68%. This validates run #12's 'exit liquidity bounce' thesis: the bounce was sell-side execution, and the downtrend has resumed. 6-week trajectory from the May peak now ~-39%."},
 {"metric":"mex_price_usd","current_value":meco["price"],"previous_value":prev_mexp,"method":"z_score",
  "average_value":zmex[0],"stddev":zmex[1],"z_score":zmex[2],"severity":"low",
  "description":f"MEX price {100*(meco['price']-prev_mexp)/prev_mexp:+.2f}% to ${meco['price']:.3e} (z={zmex[2]:+.2f}σ, N={len(rb['mex_price_usd'])}). MEX tracked EGLD down this week (last week it had decoupled upward). MEX mcap ${meco['marketCap']/1e6:.2f}M. DEX volume recovered modestly to ${totvol/1000:.0f}K but remains depressed."},
 {"metric":"total_delegators","current_value":cur_deleg,"previous_value":prev_deleg,"method":"z_score",
  "average_value":zd[0],"stddev":zd[1],"z_score":zd[2],"severity":"low",
  "description":f"Total delegators {cur_deleg:,} ({deleg_wow:+,} WoW = {100*deleg_wow/prev_deleg:+.2f}%). The raw z-score is z={zd[2]:+.2f}σ, but this is the run #9 DEGENERATE-Z-SCORE case: the baseline mean is dragged up by the pre-capitulation ~179K level, so the post-capitulation level reads as a large negative z even though the actual WoW move is only {deleg_wow:+,} (-0.04%, well within normal weekly noise). DOWNGRADED to LOW. The decisive finding: last week's -4,003 capitulation was a ONE-SHOT shake-out, NOT the start of sustained outflow. The delegator base has STABILIZED at the new lower level. This answers run #12's highest-information open question."},
 {"metric":"staked_egld","current_value":staked,"previous_value":pecon["staked_egld"],"method":"z_score",
  "average_value":zse[0],"stddev":zse[1],"z_score":zse[2],"severity":"low",
  "description":f"Total staked {staked:,} EGLD ({staked-pecon['staked_egld']:+,} WoW, {100*(staked-pecon['staked_egld'])/pecon['staked_egld']:+.2f}%). z={zse[2]:+.2f}σ. Near-flat after last week's -38K - the protocol-level unstaking has decelerated sharply, consistent with the delegator base stabilizing. Staked ratio {sr*100:.2f}% ({100*(sr-pecon['staked_ratio']):+.2f}pp)."},
 {"metric":"binance_staking_custody_stalled_3rd_week","current_value":3512650,"previous_value":3512650,"method":"rule_based",
  "severity":"high",
  "description":"Binance Staking custody UNCHANGED at 3,512,650 EGLD for the 3rd CONSECUTIVE WEEK. The 3-week accumulation phase (runs #7+9+10, cumulative +402K) is now followed by a 3-week stall = 6 weeks of an undeployed 779K-EGLD position ($2.22M at current price). No delegation to the protocol staked module; no drawdown to hot wallets. Entrenched structural position. Each additional frozen week raises the stakes of the eventual move (delegate = bullish supply lock; distribute = bearish overhang)."},
 {"metric":"dex_volume_24h_usd","current_value":totvol,"previous_value":prev_dexvol,"method":"z_score",
  "average_value":zv[0],"stddev":zv[1],"z_score":zv[2],"severity":"low",
  "description":f"DEX volume ${totvol/1000:.0f}K ({100*(totvol-prev_dexvol)/prev_dexvol:+.0f}% off last week's floor, z={zv[2]:+.2f}σ, N={len(rb['dex_volume_24h_usd'])}). A shallow bounce off the record-low $55K but still ~half the $122K of two weeks ago. Engagement remains depressed - the volume recovery is not enough to reverse the 'exit liquidity' read, especially with price making a new low."},
 {"metric":"otc_pipeline_reloaded","current_value":7028,"previous_value":-881,"method":"rule_based",
  "severity":"medium",
  "description":"OTC pipeline RELOADED on schedule (run #12 predicted reload within 1-2 weeks). UPbit OTC Desk +4,752 and OTC Distribution +2,276 (combined desk balance +7,028 after last week's inter-cycle gap of -0.9K). Combined 7d outbound throughput 85,328 EGLD (vs 44K last week). 'Binance->OTC Router 2' fed 4,800-EGLD chunks into OTC Distribution this week, confirming the loading mechanism. Per the empirically-validated load->distribute cycle (run #10/#11), a new retail distribution wave is expected in the next 1-3 weeks - a bearish retail-overhang setup."},
 {"metric":"coinbase_3rd_week_inflow_structural","current_value":5989,"previous_value":8320,"method":"rule_based",
  "severity":"medium",
  "description":"Coinbase entity +6.0K net inflow - 3rd CONSECUTIVE inflow week (+43K -> +8.3K -> +6.0K). Run #11's 2-week confirmation rule is now exceeded at 3 weeks: the off-exchange-accumulation reversal (run #10 thesis) is STRUCTURAL. Coinbase deposited through the entire failed-bounce sequence - consistent with distribution into any strength. Aggregate net exchange flow also posted a 3rd inflow week (+11.95K)."},
 {"metric":"stablecoin_supply_contraction","current_value":-1.75,"previous_value":None,"method":"rule_based",
  "severity":"low",
  "description":"Bridged stablecoin supply contracted: USDC -0.47% (burn) and USDT -1.75% (burn) WoW, both above the 0.1% stablecoin threshold. Stablecoin burn = redemptions/bridge-out, i.e. dollar liquidity leaving the MultiversX ecosystem during the price decline. A mild but directionally-bearish capital-flight signal that corroborates the on-exchange capital build."}]

# ---------- trend indicators ----------
accelerating_outflows=[
 {"exchange":"Coinbase","trend":"inflow","cumulative_change_pct":None,"weeks_in_trend":3,
  "interpretation":"Coinbase 3-week net inflow (+43K -> +8.3K -> +6.0K). The off-exchange-accumulation reversal is now structural (exceeds run #11's 2-week confirmation rule). Coinbase has been a net depositor through the entire bounce-and-fail sequence."},
 {"exchange":"NET_EXCHANGE","trend":"inflow","cumulative_change_pct":None,"weeks_in_trend":3,
  "interpretation":f"Aggregate net exchange flow +12K inflow - 3rd consecutive inflow week. The bullish parked-capital thesis (run #10) is fully and durably invalidated. Net inflow during a -4.7% price decline = sell-side deposits = sustained distribution."},
 {"exchange":"UPbit OTC Desks","trend":"loading","cumulative_change_pct":None,"weeks_in_trend":1,
  "interpretation":"OTC desks RELOADED after last week's inter-cycle gap: UPbit OTC +4.8K, OTC Distribution +2.3K (combined +7K balance), throughput 85K (vs 44K last week). Loading phase active; new distribution wave expected in 1-3 weeks per the validated cycle."}]

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
   {"metric":"egld_price","direction":"down","weeks":1,"cumulative_change_pct":100*(price-pp)/pp,
    "interpretation":f"Capitulation bounce failed after 1 week. EGLD $2.99 -> $2.85 ({100*(price-pp)/pp:+.2f}%), a new local low below the $2.95 floor. The 5-down / 1-up / 1-down sequence confirms the up-week was a counter-trend bounce, not a reversal. 6-week drawdown from the May peak ~-39%."},
   {"metric":"net_exchange_inflow","direction":"up","weeks":3,"cumulative_change_pct":None,
    "interpretation":"3rd consecutive week of net exchange INFLOW (+25K/+42K/+12K). Coinbase 3-week inflow streak. Sustained sell-side deposit pressure; off-exchange-accumulation thesis durably dead."},
   {"metric":"binance_staking_custody_stalled","direction":"flat","weeks":3,"cumulative_change_pct":0,
    "interpretation":"3rd consecutive week of stall at 3,512,650 EGLD. 3-week accumulation + 3-week stall = 6 weeks, 779K parked. Entrenched structural position; the eventual delegate-vs-distribute move becomes more decisive each frozen week."},
   {"metric":"token_holder_count_decline","direction":"down","weeks":13,"cumulative_change_pct":None,
    "interpretation":"13th consecutive week of small holder declines across top-10 tokens (-17 to -83 this week). Established airdrop-decay baseline; the active >$1M-mcap token base is stable."}],
 "regime_shifts":[
   {"metric":"capitulation_bounce_failed","before_value":2.99,"after_value":price,
    "description":"The run #11/#12 capitulation-bounce thesis resolved: the $2.95-floor bounce to $2.99 lasted exactly one week before failing to a new low at $2.85. Combined with 3 weeks of net exchange inflow and the OTC reload, this confirms the 'exit liquidity bounce' as a bearish regime, not a reversal. The bounce was distribution, not accumulation."},
   {"metric":"delegator_capitulation_was_one_shot","before_value":-4003,"after_value":deleg_wow,
    "description":f"Last week's -4,003 delegator drop (largest in tracking by 9x) did NOT continue: this week {deleg_wow:+,} (-0.04%, normal noise). The capitulation was a single shake-out event, and the delegator base has stabilized at the new ~174.4K level. Staked-EGLD unstaking also decelerated from -38K to {staked-pecon['staked_egld']:+,}."}]}

# ---------- dormant activations ----------
dormant_activations=[]

# ---------- watch list ----------
mw_bal=bal_of("erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw") or 998971
watch_list=[
 {"item":f"Capitulation bounce FAILED - EGLD {100*(price-pp)/pp:+.1f}% to a new low at ${price:.2f}","reason":"Last week's +1.36% bounce to $2.99 lasted one week before breaking back below the $2.95 floor. EGLD again decoupled to the downside (WoW BTC -2.5%, ETH +1.4%, EGLD -4.7%). Run #12's 'exit liquidity bounce' thesis validated. Watch whether $2.85 holds as a new floor or the downtrend extends; engagement metrics (still depressed) are the tell.","weeks_on_list":4},
 {"item":"Binance Staking custody STALLED 3rd consecutive week at 3.51M","reason":"6 weeks of an undeployed 779K-EGLD position ($2.22M). No delegation, no drawdown. The longer it sits frozen, the more decisive the eventual move. Highest-priority single-wallet watch.","weeks_on_list":7},
 {"item":"Delegator capitulation was a ONE-SHOT (-78 this week vs -4,003 last week)","reason":"The largest-ever single-week delegator drop did NOT begin a sustained outflow - the base stabilized at 174,406. Staked-EGLD unstaking also decelerated (-38K -> -9K). Resolves run #12's key open question: it was a shake-out, not a regime of accelerating exit. Watch for whether the stable level holds.","weeks_on_list":2},
 {"item":"Exchange net inflow 3rd consecutive week (+12K); off-exchange thesis structurally dead","reason":"Coinbase 3-week inflow streak (+43K/+8.3K/+6.0K); aggregate net inflow through the entire failed-bounce. Net deposits during a price decline = sustained distribution. The run #10 bullish parked-capital read is durably invalidated.","weeks_on_list":3},
 {"item":"OTC pipeline RELOADED (+7K desk balance, 85K throughput)","reason":"After last week's inter-cycle gap, UPbit OTC +4.8K and OTC Distribution +2.3K, with 'Binance->OTC Router 2' feeding 4,800-EGLD chunks. Per the validated load->distribute cycle, a retail distribution wave is expected in 1-3 weeks - a bearish retail-overhang setup.","weeks_on_list":4},
 {"item":"LSD 'contraction' thesis fully dead - supply-based reads show LSDs flat","reason":"In price-independent supply terms: SEGLD -0.5%, XEGLD +0.6% (GREW), SWTAO/USH flat. The run #12 'XOXNO LSD 3rd-week contraction' watch is NOT confirmed. Prior mcap-based 'contraction' reads were EGLD/TAO price artifacts. Recommend reporting LSDs in supply terms going forward.","weeks_on_list":3},
 {"item":"USH de-leveraging trend ENDED (supply flat)","reason":"After two weeks of USH burn (CDP de-risking), USH supply is now flat (-0.08%). Borrowers paused position closures. Watch whether de-leveraging resumes if price weakens further.","weeks_on_list":1},
 {"item":"Stablecoin supply contraction: USDC -0.5%, USDT -1.8% burn","reason":"Bridged-stablecoin redemptions during the decline = dollar liquidity leaving the ecosystem. Mild but directionally bearish; corroborates the on-exchange capital build. Watch for continuation.","weeks_on_list":1},
 {"item":f"Unknown Mega Whale erd18mv2z6r2 unchanged at {mw_bal:,.0f}","reason":"Zero inbound/outbound activity for a 3rd week, holding just below the 1M threshold. No downstream forwarding from the OTC-received position. Dormant but flagged for any movement.","weeks_on_list":3},
 {"item":"dataApi-sourced token mcaps returned null even at 1.0s spacing","reason":"SEGLD/SWTAO/USH/XEGLD all returned price=null at 1.05s spacing this run (H-tokens were fine). Isolated re-fetch at 2.5s recovered all. Run #12's '1.0s fixes it' rule is incomplete for priceSource=dataApi tokens - they need a populated-or-retry guard. Added to methodology.","weeks_on_list":1}]

# ---------- executive summary ----------
executive_summary=[
 {"finding":f"Capitulation bounce FAILED. EGLD {100*(price-pp)/pp:+.2f}% to ${price:.2f}, breaking back below the $2.95 floor to a new local low one week after the +1.36% relief rally. EGLD again decoupled to the downside (WoW BTC -2.5%, ETH +1.4%). This validates run #12's 'exit liquidity bounce' thesis - the bounce was sell-side execution, and the downtrend has resumed.","severity":"high","category":"network"},
 {"finding":f"Delegator capitulation was a ONE-SHOT. After last week's -4,003 (largest drop in tracking by 9x), the base moved just {deleg_wow:+,} (-0.04%) this week and STABILIZED at {cur_deleg:,}. Staked-EGLD unstaking decelerated from -38K to {staked-pecon['staked_egld']:+,}. The shake-out did not become a sustained outflow - run #12's key open question resolved.","severity":"medium","category":"staking"},
 {"finding":"Exchange net inflow 3rd consecutive week (+12K). Coinbase posted a 3rd straight inflow week (+43K/+8.3K/+6.0K), exceeding run #11's 2-week confirmation rule - the off-exchange-accumulation reversal is now STRUCTURAL. Net deposits during a price decline = sustained sell-side distribution.","severity":"high","category":"whale"},
 {"finding":"Binance Staking custody STALLED for a 3rd consecutive week at 3.51M EGLD. 3-week accumulation + 3-week stall = 6 weeks, 779K parked ($2.22M). Entrenched structural position; the eventual delegate-vs-distribute decision becomes more decisive each frozen week.","severity":"high","category":"whale"},
 {"finding":"OTC pipeline RELOADED on schedule (run #12 predicted 1-2 weeks). UPbit OTC +4.8K, OTC Distribution +2.3K (combined +7K balance), throughput 85K vs 44K last week, with 'Binance->OTC Router 2' feeding 4,800-EGLD chunks. A new retail distribution wave is expected within 1-3 weeks per the validated cycle.","severity":"medium","category":"whale"},
 {"finding":"LSD 'contraction' thesis fully dead. In price-independent supply terms, LSDs are flat-to-up: SEGLD -0.5%, XEGLD +0.6% (grew), SWTAO/USH flat. The run #12 'XOXNO LSD 3rd-week contraction' watch is NOT confirmed; prior mcap-based reads were EGLD/TAO price artifacts. Reporting LSDs in supply terms going forward.","severity":"low","category":"defi"},
 {"finding":"Stablecoin supply contracted: USDC -0.47%, USDT -1.75% burn - dollar liquidity bridging out during the decline. A mild but directionally-bearish capital-flight signal corroborating the on-exchange capital build.","severity":"low","category":"defi"},
 {"finding":"Data-quality: dataApi-sourced token mcaps (SEGLD/SWTAO/USH/XEGLD) returned null even at the run #12-mandated 1.0s spacing; an isolated 2.5s re-fetch recovered all. The '1.0s fixes it' rule is incomplete for priceSource=dataApi tokens - they need a populated-or-retry guard (now in methodology).","severity":"low","category":"network"}]

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
   "btc_correlation_note":f"EGLD {100*(price-pp)/pp:+.2f}% WoW vs BTC {btc_wow:+.2f}% / ETH {eth_wow:+.2f}% (WoW). EGLD again DECOUPLED to the downside - it fell while ETH rose and BTC fell only mildly. MultiversX-specific weakness resumed after last week's brief re-coupling during the bounce.",
   "transactions_added":st["transactions"]-pact["total_transactions"],"supply_added":econ["totalSupply"]-pecon["total_supply"],
   "staked_egld_added":staked-pecon["staked_egld"],"epoch_advanced":st["epoch"]-pact["epoch"]},
 "analysis":f"EGLD {100*(price-pp)/pp:+.2f}% WoW to ${price:.2f} - the capitulation bounce FAILED. After last week's +1.36% relief rally to $2.99, price broke back below the $2.95 floor to a new local low at $2.85. z={zp[2]:+.2f}σ. WoW comparisons show EGLD again decoupled to the downside: BTC {btc_wow:+.2f}%, ETH {eth_wow:+.2f}%, EGLD {100*(price-pp)/pp:+.2f}%. Market cap ${econ['marketCap']/1e6:.1f}M ({100*(econ['marketCap']-pecon['market_cap_usd'])/pecon['market_cap_usd']:+.1f}%). Staked ratio {sr*100:.2f}% ({100*(sr-pecon['staked_ratio']):+.2f}pp); protocol staked module near-flat at {staked/1e6:.3f}M ({staked-pecon['staked_egld']:+,}) - the heavy unstaking of last week decelerated. CRUCIALLY, the delegator base STABILIZED ({deleg_wow:+,}, -0.04%) after last week's -4,003 capitulation - that drop was a one-shot, not the start of a regime. Activity: {round((st['transactions']-pact['total_transactions'])/7)/1e6:.1f}M txs/day, account growth +{(st['accounts']-pact['total_accounts'])/1000:.1f}K. The read: the price downtrend has resumed on continued (3rd-week) exchange inflows and an OTC reload, but the retail-delegation capitulation appears to have been a single shake-out rather than an accelerating exit."}

# ---------- whale analysis ----------
whale_analysis=("THIS WEEK'S DOMINANT MOVES:\n"
 f"1) CAPITULATION BOUNCE FAILED. EGLD fell {100*(price-pp)/pp:+.2f}% to a new local low of ${price:.2f}, breaking back below the $2.95 floor just one week after the +1.36% relief rally to $2.99. This is the textbook resolution of run #12's 'exit liquidity bounce' thesis: the bounce drew sellers, not buyers. Corroborating evidence is decisive this week - a 3rd consecutive week of net exchange inflow and an OTC pipeline reload.\n\n"
 "2) BINANCE STAKING CUSTODY STALLED 3RD CONSECUTIVE WEEK at 3,512,650 EGLD. The 3-week accumulation phase (runs #7+9+10, cumulative +402K) is now followed by a 3-week stall - 6 weeks of a frozen, undeployed 779K-EGLD position ($2.22M at current price). No delegation to the protocol staked module, no drawdown to hot wallets. Entrenched structural position; each frozen week increases the decisiveness of the eventual move.\n\n"
 "3) EXCHANGE NET INFLOW 3RD CONSECUTIVE WEEK. Coinbase posted a 3rd straight inflow week (+43K -> +8.3K -> +6.0K), exceeding run #11's 2-week confirmation rule and making the off-exchange-accumulation reversal STRUCTURAL. Aggregate net exchange flow {net_total:+,.0f} EGLD ({100*net_total/total_prev if total_prev else 0:+.2f}%). Bybit +10.9K and Crypto.com +7.7K led the inflows. Net deposits during a -4.7% price decline = sustained sell-side distribution.\n\n"
 f"WHALE TIERS (top-{N_prev} apples-to-apples): mega {whale_tiers['mega_whales']['net_change_egld']/1000:+.1f}K, large {whale_tiers['large_whales']['net_change_egld']/1000:+.1f}K, mid {whale_tiers['mid_whales']['net_change_egld']/1000:+.1f}K. Mid- and large-tier accumulation (+36K/+29K) against a small mega-tier decline (-5K) reflects exchange-wallet deposit inflows landing in the large/mid tiers, not organic distribution to smaller holders.\n\n"
 "4) OTC PIPELINE RELOADED. After last week's inter-cycle gap (combined -0.9K), UPbit OTC Desk +4.8K and OTC Distribution +2.3K (combined desk balance +7.0K), with 7d outbound throughput rising to 85K (from 44K). 'Binance->OTC Router 2' fed 4,800-EGLD chunks into OTC Distribution, confirming the loading mechanism. Per the empirically validated load->distribute cycle (runs #10/#11), a new retail distribution wave is expected within 1-3 weeks - a bearish retail-overhang setup.\n\n"
 f"5) MEGA WHALE erd18mv2z6r2 DORMANT 3RD WEEK at {mw_bal:,.0f} EGLD - zero inbound/outbound, holding just below the 1M threshold. No downstream forwarding from its OTC-received position.")

# ---------- staking analysis ----------
staking_analysis=(f"Staking concentration remains low (HHI {hhi:.4f}, top-5 {top5:.1f}%, top-10 {top10:.1f}% - essentially unchanged WoW). Total delegated {total_locked:,.0f} EGLD across {len(provs)} active providers. Active delegator base {cur_deleg:,} ({deleg_wow:+}, {100*deleg_wow/prev_deleg:+.2f}%).\n\n"
 f"DELEGATOR CAPITULATION WAS A ONE-SHOT. Last week's -4,003 drop (largest in tracking by 9x) did NOT continue - this week the base moved only {deleg_wow:+,} (normal weekly noise) and stabilized at {cur_deleg:,}. The raw z-score reads {zd[2]:+.2f}σ, but this is the run #9 degenerate-z-score case (the baseline mean is dragged by the pre-capitulation ~179K level), so it is downgraded to LOW. The decisive read: the shake-out was a single event, not an accelerating exit regime. Protocol staked-EGLD unstaking also decelerated sharply (-38K last week -> {staked-pecon['staked_egld']:+,} this week).\n\n"
 f"YIELD-CHASE COHORT MIXED, NET REDEMPTION CONTINUES. The 0%-fee 9%-APR migration cohort is still bleeding on net (~{cohort_net/1000:+.0f}K): valuestaking {cohort_flows.get('valuestaking',0):+,.0f}, star_staking {cohort_flows.get('star_staking',0):+,.0f}, egldstakingprovider {cohort_flows.get('egldstakingprovider',0):+,.0f}; partly offset by orius {cohort_flows.get('orius',0):+,.0f}. Separately, pi-staking (9.33% APR, 0% fee) drew +21.9K from +10 new delegators - an isolated large entry into a tiny 14-user provider, the only fresh yield-chase signal this week.\n\n"
 f"APR distribution: {buckets[3]['provider_count']} providers in the 8-9% bucket holding {buckets[3]['total_locked_egld']/1e6:.1f}M EGLD (the dominant cluster); the 9-10% bucket holds {buckets[4]['provider_count']} providers / {buckets[4]['total_locked_egld']/1e3:.0f}K EGLD. Empty 10%+ bucket (consistent across all 2026 runs). APR-weighted average {apr_w:.2f}%.\n\n"
 f"DELEGATOR CHURN: {gain} providers gaining vs {lose} losing delegators ({deleg_wow:+} net) - balanced, healthy churn, a sharp normalization from last week's capitulation. No notable named-validator joiners/leavers >50K EGLD; system-contract aggregators (erd1qqqq...) excluded per the run #10 rule.")

# ---------- token analysis ----------
top_pair_share=pairs[0]['share_pct']
second_pair=pairs[1] if len(pairs)>1 else None
token_analysis=(f"DEX volume recovered modestly to ${totvol/1000:.0f}K ({100*(totvol-prev_dexvol)/prev_dexvol:+.0f}% off last week's record-low $55K) but remains ~half the $122K of two weeks ago. WEGLD/USDC dominance {top_pair_share:.1f}% (down from 85.1%); ZoidPay/WEGLD share {second_pair['share_pct'] if second_pair else 0:.1f}% (up from 8.1%). The shallow volume bounce, against a NEW PRICE LOW, does not reverse the 'exit liquidity' read - engagement is still depressed.\n\n"
 f"NEWLY-ISSUED TOKENS: the ESDT system-SC issue scan returned 0 issuances this week - a 2nd consecutive empty week. The method is validated (run #11/#12); empty results signal genuinely low launch activity in the bear tape.\n\n"
 f"Token holder counts declined for a 13th consecutive week (-17 to -83 across the top 10) - the established airdrop-decay baseline. WrappedEGLD (132K) and WrappedUSDC (82K) remain the most-held real tokens.\n\n"
 f"MEX price {100*(meco['price']-prev_mexp)/prev_mexp:+.2f}% to ${meco['price']:.3e}, re-coupling to EGLD's downside after last week's brief decoupling. MEX mcap ${meco['marketCap']/1e6:.2f}M.\n\n"
 f"Top by market cap: EmoryaSportsX (EMRS) leads at ${D['tokens_mcap'][0].get('marketCap',0)/1e6:.1f}M, then WrappedUSDC $8.35M, ZoidPay $4.65M (down from ~$5.36M), xMoney UTK $4.18M, StakedEGLD $2.40M. EMRS's large headline mcap reflects a high circulating valuation; it does not appear in the holder or volume leaders, so treat it as a low-float listing rather than broad adoption.\n\n"
 f"Bridged stablecoin supply CONTRACTED this week: USDC -0.47% and USDT -1.75% (burn). Stablecoin redemptions during a price decline = dollar liquidity bridging out of the ecosystem - a mild de-risking / capital-flight signal consistent with the on-exchange capital build.")

# ---------- defi analysis ----------
defi_analysis=(f"LSD 'CONTRACTION' THESIS FULLY DEAD - report LSDs in SUPPLY terms. The mcap-based reads that suggested LSD contraction in prior runs were dominated by EGLD/TAO PRICE moves. In price-independent supply terms this week: SEGLD {segld_supply_wow:+.2f}% (mild redemption), XEGLD {xegld_supply_wow:+.2f}% (actually GREW), SWTAO {swtao_supply_wow:+.2f}% (flat), USH {ush_supply_wow:+.2f}% (flat). The run #12 'XOXNO LSD 3rd-week contraction' watch is therefore NOT confirmed - XEGLD supply grew. Both LSDs are flat-to-up on a real-token basis; the bearish-LSD-during-stress thesis is dead.\n\n"
 f"HATOM LSD ${hatom_lsd/1e6:.2f}M USD (SEGLD ${segld_mcap/1e6:.2f}M + SWTAO ${swtao_mcap/1e6:.2f}M), {100*(hatom_lsd-prev_hlsd)/prev_hlsd:+.1f}% USD. The decline is almost entirely price: SEGLD supply only {segld_supply_wow:+.2f}%, and the SWTAO mcap drop tracks TAO's price, not MultiversX redemptions. Underlying staked EGLD is essentially unchanged.\n\n"
 f"HATOM USH stablecoin ${hatom_ush/1000:.0f}K, supply {ush_supply_wow:+.2f}% WoW - the 2-week burn/de-leveraging trend has ENDED. Borrowers paused CDP position closures; USH is flat. Watch for resumption if price weakens further.\n\n"
 f"HATOM LENDING ${hatom_lending/1e6:.2f}M USD ({100*(hatom_lending-prev['defi_tvl']['Hatom Lending'])/prev['defi_tvl']['Hatom Lending']:+.1f}% USD, {100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}% EGLD). The bilateral inverse rule is NOT formally evaluable - the -4.68% price move is just below the |Δprice|>=5% guardrail from run #12. The EGLD-denominated +3.2% IS in the rule's expected counter-direction (depositors hold during dips), but it does not count as a formal observation at a sub-threshold move.\n\n"
 f"xExchange TVL ${xexch_tvl_usd/1e6:.2f}M / {xexch_tvl_egld/1000:.0f}K EGLD ({100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld:+.1f}% EGLD). DEX volume recovered modestly to ${totvol/1000:.0f}K but remains depressed. Aggregator throughput cooled (XOXNO {tcount('XOXNO Aggregator'):,}, OneDex {tcount('OneDex Swap'):,}) alongside the broader engagement slump.\n\n"
 f"DATA-QUALITY: the four dataApi-priced tokens (SEGLD/SWTAO/USH/XEGLD) returned price=null even at the run #12-mandated 1.0s spacing, while H-tokens (a different price source) populated fine. An isolated 2.5s re-fetch recovered all four. Conclusion: the '1.0s spacing fixes it' rule is incomplete for priceSource=dataApi tokens; the collector needs a populated-or-retry guard, and TVL should prefer supply-based metrics (price-independent) for the LSD/stablecoin set.")

report={
 "metadata":{"report_date":"2026-06-22","period_start":"2026-06-15T00:00:00Z","period_end":"2026-06-22T00:00:00Z",
   "generated_at":datetime.now(timezone.utc).isoformat(),"egld_price_usd":price,
   "btc_price_usd":be["bitcoin"]["usd"],"eth_price_usd":be["ethereum"]["usd"],"run_number":13,
   "data_sources_ok":json.load(open("/tmp/run13/status.json"))["ok"],
   "data_sources_failed":["dataApi-priced token mcaps (SEGLD/SWTAO/USH/XEGLD) returned null on first pass even at 1.0s spacing; recovered via isolated 2.5s re-fetch (see methodology)"]},
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
 "meta_learning":{"run_number":13,
   "endpoints_that_worked":json.load(open("/tmp/run13/status.json"))["ok"],
   "endpoints_that_failed":[],
   "api_quirks":[
     "dataApi-sourced token prices (priceSource.type=='dataApi': SEGLD/SWTAO/USH/XEGLD) returned price=null marketCap=null on the sequential collection pass EVEN at 1.05s spacing, while H-tokens (different price source) populated fine. An isolated re-fetch at 2.5s spacing recovered all four. Run #12's '1.0s spacing fixes it' rule is INCOMPLETE for dataApi tokens - they need a populated-or-retry guard. Robust fix: prefer supply-based (minted-burnt) metrics for LSD/stablecoin TVL since supply fields never null.",
     "Capitulation bounce failed within one week: +1.36% (run #12) then -4.68% (this run) to a new low $2.85 below the $2.95 floor. The 'exit liquidity bounce' signature (price up on collapsing engagement) correctly predicted the failure.",
     "Delegator base z-score is in the run #9 degenerate regime: after last week's -4,003 level shift, the baseline mean keeps producing a large negative z (-2.68σ) for a tiny -78 WoW move. Always cross-check the absolute % move (-0.04% = noise) before assigning severity."],
   "data_gaps":[
     "dataApi token price feed intermittently null under sequential load; mitigated by isolated re-fetch and supply-based fallback.",
     "Newly-issued token scan returned empty for a 2nd week - cannot distinguish a genuinely quiet launch week from method failure without external corroboration.",
     "Provider previous list keyed by name only; anonymous providers still not WoW-matchable."],
   "key_findings":[
     "Capitulation bounce FAILED - EGLD -4.68% to a new low $2.85, validating run #12's 'exit liquidity bounce' thesis.",
     "Delegator capitulation was a ONE-SHOT: -78 this week (vs -4,003), base stabilized at 174,406.",
     "Exchange net inflow 3rd consecutive week (+12K); Coinbase 3-week inflow makes off-exchange reversal structural.",
     "Binance Staking custody STALLED 3rd consecutive week at 3.51M (6 weeks parked, 779K).",
     "OTC pipeline RELOADED (+7K desk balance, 85K throughput) - distribution wave expected in 1-3 weeks.",
     "LSD 'contraction' thesis dead: supply-based reads show SEGLD -0.5%, XEGLD +0.6% (grew), USH flat.",
     "Stablecoin supply contracted (USDC -0.5%, USDT -1.8% burn) - dollar liquidity bridging out.",
     "dataApi token mcaps null even at 1.0s spacing; need populated-or-retry guard + supply-based TVL."],
   "action_items_from_previous":10,
   "action_items_completed":9,
   "methodology_changes":[
     "REPORT LSDs IN SUPPLY TERMS (minted-burnt), not mcap, as the primary signal. Mcap-based LSD reads are dominated by EGLD/TAO price and produce spurious 'contraction' signals. Supply is price-independent and the field never returns null. This run: SEGLD -0.5%, XEGLD +0.6%, both flat-to-up despite USD mcaps falling. The run #11/#12 'synchronized LSD contraction' narrative was largely a price artifact.",
     "dataApi TOKEN RE-FETCH GUARD: priceSource=dataApi tokens (SEGLD/SWTAO/USH/XEGLD) can return null even at 1.0s spacing. Collector should detect null price after the main pass and re-fetch those specific tokens individually at >=2.5s spacing. Do NOT treat a single null pass as an outage - it recovers on isolated retry.",
     "DEGENERATE-Z-SCORE GUARD for total_delegators reaffirmed: after a one-time level shift (last week's -4,003), the baseline mean lags and produces a large |z| for a noise-level WoW move. Cross-check absolute % change and downgrade severity when |%|<0.1%.",
     "EXIT-LIQUIDITY-BOUNCE thesis validated as a forward indicator: a price up-week on collapsing engagement (run #12) correctly predicted a one-week failure to new lows. Promote to a reusable bearish pattern: relief rallies on contracting engagement are distribution, not reversal."],
   "new_addresses_discovered":0,
   "most_valuable_insight":"The capitulation bounce failed exactly as run #12's 'exit liquidity bounce' thesis predicted - EGLD broke to a new low ($2.85) within one week of the +1.36% relief rally, while exchange inflows continued for a 3rd week and the OTC pipeline reloaded. This is a clean validation that relief rallies on contracting engagement are distribution, not reversal. The secondary insight is methodological: reporting LSDs in supply terms (price-independent) dissolves the 'synchronized LSD contraction' narrative that prior runs built on price-contaminated mcap data - both LSDs are actually flat-to-growing on a real-token basis.",
   "top_recommendation":"Track the OTC distribution wave: per the validated load->distribute cycle and this week's reload (+7K desk balance, 85K throughput), expect retail distribution (UPbit OTC / OTC Distribution outflows in 1-8K chunks to routing wallets) within 1-3 weeks. If it lands alongside a 4th exchange-inflow week and the Binance custody finally moves, that confluence would be a decisive directional signal.",
   "recommendations_for_next_run":[
     "OTC distribution wave watch: the pipeline reloaded this week (+7K balance). Per cycle, expect a retail distribution wave (desk outflows) in 1-3 weeks. Confirm by tracing UPbit OTC / OTC Distribution outbound 1-8K chunks to routing wallets and onward to exchanges.",
     "Binance Staking custody 4th-week stall: 6 weeks parked. Watch for the decisive move - a jump in econ.staked (delegation, bullish) or a drawdown to hot wallets (distribution, bearish).",
     "Does $2.85 hold as a new floor, or does the downtrend extend? After the failed bounce, watch whether EGLD stabilizes or makes further lows; engagement metrics (DEX volume, delegators) are the tell for whether demand returns.",
     "Delegator base stability follow-up: it stabilized at 174,406 after the one-shot capitulation. Confirm the level holds (a 2nd flat week) vs a resumption of outflow.",
     "Exchange inflow 4th-week check: 3 consecutive inflow weeks logged. A 4th would deepen the structural-distribution read; a reversal to outflow would suggest the selling is exhausting.",
     "Implement the dataApi re-fetch guard in the collector and verify supply-based LSD reporting end-to-end next run (the run #12 1.0s rule was insufficient).",
     "pi-staking +21.9K / +10 users isolated entry: watch whether this tiny high-APR provider keeps drawing fresh delegation (a possible new yield-chase seed) or whether it was a one-off.",
     "Stablecoin contraction follow-up: USDC -0.5% / USDT -1.8% this week. A 2nd week of stablecoin burn would confirm sustained dollar-liquidity flight from the ecosystem.",
     "EMRS-6e4067 ($28M headline mcap, low float): verify whether this is a genuine large-cap or a thin listing; check holder/volume traction next run."],
   "dashboard_feature_suggestions":[
     {"title":"LSD circulating-supply timeline (supply, not mcap)","motivation":"This run's most important methodological finding: mcap-based LSD reads are price-contaminated and produced a phantom 'synchronized LSD contraction' across runs #11-12. On a supply basis (SEGLD -0.5%, XEGLD +0.6%) the LSDs are flat-to-growing. A supply-based timeline would have prevented three runs of mis-narration and is robust to the dataApi null-price issue that bit this run.","suggested_visualization":"dual-line chart of SEGLD and XEGLD circulating supply (minted-burnt, in token units) across weekly snapshots, with EGLD price on a secondary axis to visually separate supply moves from price moves.","data_already_available":True,"data_source":"derived from data/collected/{date}.json tvl_tokens.{SEGLD,XEGLD}.supply across snapshots","priority":"high"},
     {"title":"OTC pipeline load/distribute cycle phase indicator","motivation":"The OTC pipeline has now completed multiple observable load->distribute->gap->reload cycles (run #10 load, #11 distribute, #12 gap, #13 reload). This run's reload (+7K desk balance, 85K throughput) predicts a distribution wave in 1-3 weeks. A phase indicator would make the cycle position - and the forward prediction - explicit each week.","suggested_visualization":"horizontal phase timeline (LOADING / DISTRIBUTING / GAP) across weekly snapshots, with desk balance delta and 7d throughput as the underlying series; current-phase badge.","data_already_available":True,"data_source":"OTC desk balances + outbound throughput already collected per run; would need a small per-run phase label stored in previous.json","priority":"medium"},
     {"title":"Forward-indicator scorecard (prediction resolution tracker)","motivation":"This run RESOLVED run #12's headline prediction (capitulation bounce -> exit liquidity, now validated by the failure to new lows) and run #11's Coinbase 2-week rule (now 3 weeks, structural). A scorecard that tracks each report's open predictions and auto-marks them validated/invalidated/pending would make the analytical track record legible and surface which theses are paying off.","suggested_visualization":"table/kanban of open predictions with status chips (pending / validated / invalidated) and the run that opened and resolved each.","data_already_available":True,"data_source":"recommendations_for_next_run + action_items_completed across learnings.json runs","priority":"medium"}],
   "dashboard_suggestions_followup":[
     {"from_run":12,"title":"Engagement-collapse composite indicator","status":"pending","note":"Still valuable: this run shows a mixed engagement picture (DEX volume recovered +15%, delegators stabilized, exchange inflows continued) - a composite would quantify whether engagement is net-recovering or still contracting, which is exactly the open question for whether $2.85 holds."},
     {"from_run":12,"title":"LSD circulating-supply timeline","status":"re-prioritized-high","note":"PROMOTED to high priority and re-listed: this run's central methodological lesson is that supply-based LSD reporting dissolves the phantom contraction narrative. This is now the single most useful unbuilt widget."},
     {"from_run":12,"title":"Bilateral inverse rule up/down asymmetry scatter","status":"pending","note":"Not testable this run (price -4.68% just below the 5% guardrail). Still pending a qualifying observation; the scatter remains a good idea once enough qualifying weeks accrue."},
     {"from_run":11,"title":"Forward-indicator scorecard widget","status":"re-listed","note":"Re-listed (see this run's suggestions). The capitulation-bounce prediction just resolved VALIDATED and Coinbase 2-week->3-week resolved STRUCTURAL - the scorecard would have auto-surfaced both."},
     {"from_run":11,"title":"OTC cycle phase indicator","status":"re-listed","note":"Re-listed as a concrete suggestion this run. The pipeline just transitioned GAP->LOADING, a textbook phase change the indicator would capture."},
     {"from_run":10,"title":"Multi-week Binance custody vs protocol-staked tracker","status":"pending","note":"Now 6 weeks of data (3 accumulation + 3 stall). The flat-line stall against a flat protocol-staked line is increasingly the story; chart strongly motivated."},
     {"from_run":9,"title":"Multi-week net exchange-flow oscillation chart","status":"pending","note":"Trajectory now +169K/-56K/-71K/+25K/+42K/+12K = 3-week inflow streak. The streak is the signal; a multi-week chart would make it obvious."},
     {"from_run":8,"title":"OTC pipeline graph view (Sankey/force-directed)","status":"pending","note":"Pipeline reloaded this week with traceable Binance->Router->OTC Distribution edges (4,800-chunk flows). A graph view would render the active loading edges directly."}]}}

json.dump(report,open(f"{REPO}/reports/2026-06-22.json","w"),indent=2)
print("WROTE reports/2026-06-22.json")
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
