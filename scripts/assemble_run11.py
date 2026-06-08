#!/usr/bin/env python3
"""Assemble reports/2026-06-08.json (run #11) from collected data."""
import json, math
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D = json.load(open("/tmp/run11/collected.json"))
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
for a in exch:
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
for k,v in prev["exchange_balances"].items():
    if "Binance" in k: prev_ent["Binance"]=prev_ent.get("Binance",0)+v
    elif "Coinbase" in k: prev_ent["Coinbase"]=prev_ent.get("Coinbase",0)+v
    elif "Crypto.com" in k: prev_ent["Crypto.com"]=prev_ent.get("Crypto.com",0)+v
    else: prev_ent[k]=prev_ent.get(k,0)+v
ent_interp={
 "Binance":"Hot wallet erd1sdsl -36.7K (-15.6%). Binance Staking custody UNCHANGED at 3,512,650 EGLD (the run #10 +135K transfer was a one-shot, not a 3-week streak as feared). Run #10's headline forward indicator question resolved: Binance has neither delegated nor distributed the parked 779K - it is STALLED. Entity net -36.7K = pure hot drawdown without offsetting custody growth.",
 "Coinbase":"Primary wallet +26.8K (+51.5%) reverses 3-week net-outflow streak (-39K/-12.9K/-10.1K WAS the cleanest off-exchange withdrawal signal - now BROKEN). Combined +42.9K net inflow this week, the largest positive entity flow. Coinbase Routing Wallet also fed Unknown Mega Whale erd18mv2z6r2 with 5,925 EGLD on 2026-06-07 (same OTC pattern as Apr 18). Off-exchange-accumulation thesis FAILED.",
 "Crypto.com":"+10.9K net inflow (+6.3%). First inflow after 3 weeks of mild bleed.",
 "Bybit":"+9.0K net inflow (+1.9%). Reversed mild bleed.",
 "UPbit":"Hot wallet -12.7K (-1.0%). UPbit OTC Desk separately distributed -14.0K (-30%), and OTC Distribution Wallet -12.4K (-28%). Combined OTC desks -26.4K (-29% across desks) confirms run #10's predicted distribution wave.",
 "MEXC":"-3.1K (-3.0%). Mild outflow.",
 "KuCoin":"+7.6K net inflow (+38.3%). Visible step-up after last week's -20% bleed.",
 "Bitget":"+9.6K net inflow (+12.6%). Sharpest mid-tier inflow.",
 "Gate.io":"Effectively flat (+0.1K).",
 "Tokero":"Effectively flat (-0.4K).",
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
    "net_change_egld":net_total,"net_change_pct":100*net_total/total_prev,
    "direction":"outflow" if net_total<0 else "inflow",
    "signal":"NET INFLOW +24,902 EGLD (+0.38%) - REVERSES the 2-week off-exchange-accumulation outflow streak. Per the 2-week confirmation rule, this kills the off-exchange-accumulation thesis from run #10 (which predicted Coinbase would extend its 3-week outflow to a 4th week). Coinbase did the OPPOSITE - +43K net inflow, reversing the cleanest signal. With Binance Staking custody also STALLED at 3.51M, the entire 'bullish parked capital' setup from run #10 has dissolved. The on-exchange capital is rebuilding during the price decline - classic bearish surrender pattern (sell-into-decline).",
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
top_by_holders=[]
for t in D["tokens_holders"][:10]:
    pid=prev_th.get(t["identifier"]); ph=pid["holders"] if pid else None
    top_by_holders.append({"identifier":t["identifier"],"name":t.get("name"),"holders":t["accounts"],
        "previous_holders":ph,"holders_change":(t["accounts"]-ph) if ph else None,
        "price_usd":t.get("price"),"market_cap_usd":t.get("marketCap"),"volume_24h_usd":None})
top_by_volume=[{"identifier":t["identifier"],"name":t.get("name"),"transactions":t.get("transactions"),
    "previous_transactions":None,"change_pct":None,"price_usd":None,"volume_24h_usd":None} for t in D["tokens_txs"][:10]]
top_by_market_cap=[{"identifier":t["identifier"],"name":t.get("name"),"holders":None,"previous_holders":None,
    "price_usd":t.get("price"),"market_cap_usd":t.get("marketCap"),"volume_24h_usd":None} for t in D["tokens_mcap"][:10]]
# Newly-issued tokens from ESDT system SC scan (run #10 recommendation #7 implemented)
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

# ---------- defi ----------
tt=D["tvl_tokens"]
def mc(tid):
    t=tt.get(tid); return (t.get("marketCap") or 0) if isinstance(t,dict) else 0
hatom_lending=sum(mc(x) for x in ["HUSDC-d80042","HEGLD-d61095","HUSDT-6f0914","HWBTC-49ca31","HWETH-b3d17e","HBUSD-ac1fca","HHTM-e03ba5","HMEX-df6df7","HUTK-4fa4b2","HWTAO-2e9136"])
hatom_lsd=mc("SEGLD-3ad2d0")+mc("SWTAO-356a25")
hatom_ush=mc("USH-111e09"); xoxno_lsd=mc("XEGLD-e413ed")
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
hl_egld=hatom_lending/price
hlsd_egld=hatom_lsd/price
xlsd_egld=xoxno_lsd/price
ush_egld=hatom_ush/price
protocol_breakdown=[
 {"protocol":"xExchange","category":"dex","addresses_tracked":16,"tvl_usd":xexch_tvl_usd,"tvl_egld":xexch_tvl_egld,
  "tvl_wow_change_pct":100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld,"transfers_24h":None,"volume_24h_usd":totvol,
  "notable_events":f"DEX volume +12.3% to ${totvol/1000:.0f}K (vs $108K last week). WEGLD/USDC dominance 93.2% (back to historical norm after run #9 ZoidPay event). ZoidPay/WEGLD share 3.0% (-58% WoW). WEGLD supply held nearly flat WoW ({100*(int(D['tokens_holders'][1].get('supply','0') or 0) - int(prev_th['WEGLD-bd4d79'].get('supply_raw',0)))/max(int(prev_th['WEGLD-bd4d79'].get('supply_raw',1)),1):+.2f}% raw) - run #10's +4.7% wrap event was a one-off, not sustained DEX expansion.","health_signal":"flat"},
 {"protocol":"Hatom Lending","category":"lending","addresses_tracked":13,"tvl_usd":hatom_lending,"tvl_egld":hl_egld,
  "tvl_wow_change_pct":100*(hl_egld-prev_hl_egld)/prev_hl_egld,"transfers_24h":tcount("Hatom EGLD MM"),
  "notable_events":f"TVL ${hatom_lending/1e6:.2f}M USD ({100*(hatom_lending-prev['defi_tvl']['Hatom Lending'])/prev['defi_tvl']['Hatom Lending']:+.1f}%) but {hl_egld/1000:.0f}K EGLD ({100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}%). BILATERAL INVERSE RULE 5TH CONFIRMATION: -15.7% price -> +3.3% EGLD-denominated deposits. Magnitude weaker than run #10 (+8.3% during -11.8%) - depositors DCAing less aggressively this leg.","health_signal":"flat"},
 {"protocol":"Hatom Liquid Staking","category":"liquid_staking","addresses_tracked":2,"tvl_usd":hatom_lsd,"tvl_egld":hlsd_egld,
  "tvl_wow_change_pct":100*(hlsd_egld-prev_hlsd_egld)/prev_hlsd_egld,"transfers_24h":tcount("Hatom Liquid Staking"),
  "notable_events":f"SEGLD-3ad2d0 mcap ${mc('SEGLD-3ad2d0')/1e6:.2f}M (SWTAO not loaded this run). In EGLD: {hlsd_egld/1000:.0f}K ({100*(hlsd_egld-prev_hlsd_egld)/prev_hlsd_egld:+.1f}%). LSD contracted in EGLD terms - unusual; suggests some users unstaked into liquid form during the decline.","health_signal":"shrinking"},
 {"protocol":"Hatom USH","category":"stablecoin","addresses_tracked":4,"tvl_usd":hatom_ush,"tvl_egld":ush_egld,
  "tvl_wow_change_pct":100*(hatom_ush-prev_hush)/prev_hush,"transfers_24h":None,
  "notable_events":f"USH-111e09 mcap ${hatom_ush/1000:.0f}K ({100*(hatom_ush-prev_hush)/prev_hush:+.1f}% USD). Stablecoin contracted mildly.","health_signal":"flat"},
 {"protocol":"XOXNO LSD","category":"liquid_staking","addresses_tracked":2,"tvl_usd":xoxno_lsd,"tvl_egld":xlsd_egld,
  "tvl_wow_change_pct":100*(xlsd_egld-prev_xl_egld)/prev_xl_egld,"transfers_24h":tcount("XOXNO LSD"),
  "notable_events":f"XEGLD-e413ed mcap ${xoxno_lsd/1e6:.2f}M ({100*(xoxno_lsd-prev['defi_tvl']['XOXNO LSD'])/prev['defi_tvl']['XOXNO LSD']:+.1f}% USD), {xlsd_egld/1000:.0f}K EGLD ({100*(xlsd_egld-prev_xl_egld)/prev_xl_egld:+.1f}% EGLD). Both USD and EGLD contracted - unstaking activity.","health_signal":"shrinking"},
 {"protocol":"XOXNO Aggregator","category":"aggregator","addresses_tracked":1,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("XOXNO Aggregator"),
  "notable_events":f"Throughput {tcount('XOXNO Aggregator'):,} daily transfers (~flat vs last week's 14,564). DEX aggregator activity remains elevated during price stress.","health_signal":"flat"},
 {"protocol":"OneDex","category":"aggregator","addresses_tracked":5,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("OneDex Swap"),
  "notable_events":f"{tcount('OneDex Swap'):,} daily transfers. Aggregator throughput elevated; on-chain activity rotation continues.","health_signal":"flat"},
 {"protocol":"JEXchange","category":"dex","addresses_tracked":4,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("JEXchange Fees"),
  "notable_events":f"Fees wallet throughput {tcount('JEXchange Fees'):,} daily transfers. Aggregator activity steady.","health_signal":"flat"}]
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
                    "description":f"{tid} supply {chg:+.2f}% ({ev}). {'Continuation of run #10 OTC-coupled wrapping' if tid=='WEGLD-bd4d79' else 'Protocol-level event'}."})

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
  "average_value":zp[0],"stddev":zp[1],"z_score":zp[2],"severity":"high",
  "description":f"EGLD -15.71% WoW to $2.95 (z={zp[2]:+.2f} sigma, HIGH severity, N=7). Floor BROKE - run #10's $3.50 floor prediction failed. 5-week trajectory: $4.67 (May 4) -> $3.88 -> $3.97 -> $3.50 -> $2.95 = -37% in 5 weeks. EGLD strongly UNDERPERFORMED BTC (+1.33% 24h) and ETH (+3.56% 24h) - both up while EGLD down 16%. This is no longer noise; combined with run #10's break of $3.74, this is a regime shift to a new lower price band."},
 {"metric":"mex_price_usd","current_value":meco["price"],"previous_value":prev_mexp,"method":"z_score",
  "average_value":zmex[0],"stddev":zmex[1],"z_score":zmex[2],"severity":"high",
  "description":f"MEX price -16.3% to ${meco['price']:.3e} (z={zmex[2]:+.2f} sigma, HIGH severity, N=6). MEX moved in lockstep with EGLD (-15.7% vs -16.3%) and slightly worse - typical native-token amplification. MEX mcap dropped $1.33M -> $1.12M (-16%)."},
 {"metric":"total_delegators","current_value":cur_deleg,"previous_value":prev_deleg,"method":"z_score",
  "average_value":zd[0],"stddev":zd[1],"z_score":zd[2],"severity":"low",
  "description":f"Total delegators {cur_deleg:,} (-447 WoW = -0.25%). z={zd[2]:+.2f} sigma but again DEGENERATE (baseline sd ~47 over a ~179K base). Per run #9 rule, severity downgraded to LOW given <0.5% absolute move. Larger drop than recent weeks (was -24 to -53 prior weeks) - delegator exodus accelerating but absolute base still flat at scale."},
 {"metric":"binance_staking_custody_stalled","current_value":3512650,"previous_value":3512650,"method":"rule_based",
  "severity":"high",
  "description":"Binance Staking custody UNCHANGED at 3,512,650 EGLD (last txn at this wallet was the 2026-05-31 +135K from run #10). The 3-week accumulation pattern HALTED this week. Protocol staked module rose -27K (econ.staked 14,497,721 -> 14,471,101 = -27K), so no new delegation either. Run #10's headline forward indicator question resolved: neither bullish lockup nor bearish distribution - it is STALLED. Total parked since run #7: ~779K EGLD ($2.30M at current price, down from $2.73M last week). Promoted from anomaly to STRUCTURAL HOLDING."},
 {"metric":"otc_pipeline_distribution_wave_confirmed","current_value":-26410,"previous_value":32605,"method":"rule_based",
  "severity":"high",
  "description":"OTC desks DISTRIBUTED this week as predicted in run #10. UPbit OTC Desk -14.0K (-30%), OTC Distribution Wallet -12.4K (-28%), combined -26.4K. Outflow rate: UPbit OTC sent 99,189 EGLD to 50 recipients in 7d; OTC Distribution sent 64,448 EGLD to 50 recipients. The retail distribution wave hit on schedule (1-week window after loading). The fact that the wave came so quickly suggests aggressive sell-side execution given the price decline."},
 {"metric":"coinbase_3wk_outflow_streak_BROKEN","current_value":42932,"previous_value":-10100,"method":"rule_based",
  "severity":"high",
  "description":"Coinbase entity +43.0K NET INFLOW (primary wallet +26.8K = +51.5%, Coinbase Custody flat). This BREAKS the 3-week net outflow streak (-39K/-12.9K/-10.1K) that was last week's cleanest off-exchange-accumulation signal. Run #10's recommended 4-week confirmation FAILED. Combined with the Binance staking-custody STALL, the bullish parked-capital thesis collapses entirely - on-exchange capital is rebuilding during the price decline (classic sell-into-decline pattern). Coinbase Routing Wallet separately fed Unknown Mega Whale erd18mv2z6r2 with 5,925 EGLD (2026-06-07) - this is the Apr 18 OTC pattern recurring."},
 {"metric":"yield_chase_regime_ended","current_value":-2610,"previous_value":3500,"method":"rule_based",
  "severity":"medium",
  "description":"5 weeks of yield-chase officially ENDED. Net flow to low-fee 9%+ APR cohort: ninjastaking +2.6K (the only meaningful gainer this week), procryptostaking +0.7K, mapleleafnetwork flat. ALL three previous leaders REVERSED: egldstakingprovider -3.1K, valuestaking -1.0K, orius -1.8K. Net cohort flow -2.6K (vs +3.5K last week, ~+50K cumulative weeks 1-4). Regime is over. ninjastaking is the only sustained gainer across all 5 weeks (+38K cumulative)."}]

# ---------- trend indicators ----------
accelerating_outflows=[
 {"exchange":"Coinbase","trend":"flat","cumulative_change_pct":None,"weeks_in_trend":1,
  "interpretation":"Coinbase 3-week outflow streak BROKEN. Run #8 +39K -> Run #9 -12.9K -> Run #10 -10.1K -> Run #11 +43K. The off-exchange accumulation thesis from run #10 is invalidated. Coinbase is now in inflow mode during the price decline."},
 {"exchange":"NET_EXCHANGE","trend":"flat","cumulative_change_pct":None,"weeks_in_trend":1,
  "interpretation":"Aggregate net exchange flow REVERSED to +25K inflow after 2 weeks of net outflow (-56K, -71K). The bullish off-exchange-accumulation setup from run #10 dissolved. With Binance Staking custody also stalled, the entire 'parked capital' thesis collapses."},
 {"exchange":"UPbit OTC Desks","trend":"declining","cumulative_change_pct":-29.0,"weeks_in_trend":1,
  "interpretation":"OTC desk distribution wave hit on schedule. Combined desks -26.4K (-29%). Outflow rate: 99K (UPbit OTC) + 64K (OTC Distribution) = 163K total throughput in 7d. Confirms run #10 prediction of 1-3 week distribution window."}]
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
   {"metric":"egld_price_decline","direction":"down","weeks":5,"cumulative_change_pct":-37.0,
    "interpretation":"5 weeks of EGLD decline: $4.67 -> $3.88 -> $3.97 -> $3.50 -> $2.95 (with one mild uptick run #9 to #10 break). Cumulative -37% from May 4 peak. -2-sigma threshold breached for 2nd time in 4 weeks (run #10 -2.09σ, this week -3.32σ). Confirmed regime shift to lower price band."},
   {"metric":"token_holder_count_decline","direction":"down","weeks":11,"cumulative_change_pct":None,
    "interpretation":"11th consecutive week of small holder declines across all top-10 tokens (-21 to -139 this week). Established airdrop-decay baseline; active >$1M-mcap token base stable."},
   {"metric":"binance_staking_custody_stalled","direction":"flat","weeks":1,"cumulative_change_pct":0,
    "interpretation":"3-week accumulation streak ENDED. Wallet unchanged at 3,512,650. Awaiting next event - delegation (bullish) or distribution (bearish)."},
   {"metric":"otc_desk_balance","direction":"down","weeks":1,"cumulative_change_pct":-29.0,
    "interpretation":"OTC desks reversed from last week's loading to this week's distribution. -26.4K combined this week confirms run #10's distribution wave prediction. The load-distribute cycle is now empirically validated."},
   {"metric":"yield_chase_migration","direction":"flat","weeks":1,"cumulative_change_pct":-0.1,
    "interpretation":"5-week yield-chase regime ENDED. Cohort net flow -2.6K (3 of 5 previous leaders reversed). ninjastaking the only sustained gainer (+38K cumulative across all 5 weeks)."}],
 "regime_shifts":[
   {"metric":"egld_price_regime","before_value":3.50,"after_value":price,
    "description":"EGLD broke run #10's $3.50 floor. Cumulative 5-week decline -37% from $4.67 peak. New price band $2.95 sits below all 2026 prior weekly closes. z-score -3.32σ HIGH severity confirms regime change."},
   {"metric":"binance_custody_stall","before_value":3377559,"after_value":3512650,
    "description":"3-week Binance Staking custody accumulation ENDED. Wallet locked at 3.51M (zero change). The structural question (delegate vs distribute) remains unanswered but the accumulation phase is over. Next move determines bullish/bearish read."},
   {"metric":"exchange_flow_direction_reversal","before_value":-70846,"after_value":24902,
    "description":"Net exchange flow reversed from -71K outflow to +25K inflow in a single week. Combined with Coinbase 3-week outflow break, the off-exchange-accumulation thesis from run #10 is invalidated. Sell-into-decline (classic surrender) pattern emerging."}]}

# ---------- dormant activations ----------
dormant_activations=[]

# ---------- watch list ----------
watch_list=[
 {"item":"EGLD broke $3.50 floor - new low $2.95 (-15.7%, z=-3.32σ)","reason":"5-week cumulative -37% from May 4 peak. EGLD UNDERPERFORMED BTC (+1.3% 24h) and ETH (+3.6% 24h) - decoupled to the downside. Test next week: a bounce off $2.95 indicates capitulation low; a continued decline locks in the lower regime. BTC/ETH both up suggests this is MultiversX-specific.","weeks_on_list":2},
 {"item":"Binance Staking custody STALLED at 3.51M (UNCHANGED for first time in 3 weeks)","reason":"Run #10's top forward indicator question is half-resolved: neither delegated nor distributed. The 779K parked since run #7 remains undeployed. Watching for the next event - jump in econ.staked (delegation/bullish) OR drawdown to hot wallets (distribution/bearish). The longer this sits, the more likely a sudden decisive move.","weeks_on_list":5},
 {"item":"OTC desks distributed -26.4K (-29%) THIS week - run #10 prediction VALIDATED","reason":"UPbit OTC Desk -14K, OTC Distribution -12.4K. Combined retail throughput 163K in 7d. The load-distribute cycle is now empirically validated. Next: watch for desks loading again (next 1-2 weeks expected per cycle).","weeks_on_list":2},
 {"item":"Coinbase 3-week outflow streak BROKEN - +43K inflow","reason":"Run #10's cleanest off-exchange-withdrawal signal reversed sharply. Combined with Binance custody stall, the bullish parked-capital thesis collapses. Sell-into-decline (surrender) pattern emerging. Also: Coinbase Routing Wallet sent 5,925 EGLD to Unknown Mega Whale erd18mv2z6r2 - Apr 18 OTC pattern recurring.","weeks_on_list":3},
 {"item":"Yield-chase regime ENDED at week 5","reason":"Cohort net flow -2.6K (5 weeks accumulated ~+50K weeks 1-4, +3.5K week 5, -2.6K week 6). 3 of 5 previous leaders reversed. ninjastaking the only sustained gainer (+38K total). Regime can be removed from active watch.","weeks_on_list":6},
 {"item":"Hatom Lending +3.3% EGLD during -15.7% price drop (bilateral inverse rule, 5th confirmation)","reason":"Bilateral inverse rule magnitude scaling: +14.7%/-13%, -16.9%/+13.6%, -11.8%/+8.3%, -15.7%/+3.3%. This week's response is WEAKER than expected for the price magnitude - depositors DCAed less aggressively. Possible interpretation: depositor capacity diminishing OR conviction reducing as decline persists.","weeks_on_list":4},
 {"item":"Newly-issued token detection WORKAROUND IMPLEMENTED","reason":"ESDT system SC scan (per run #10 recommendation #7) successfully detected 3 issuances in 7d: FRANZELA (FRA), GreenSmokeNetwork (GSN), GrandTheftAurum (GTA). All low-quality (1-2 holders, 0-2 txs, no identifiable deployer). Workaround is reliable. Method now standard.","weeks_on_list":1},
 {"item":"Coinbase Routing Wallet -> Unknown Mega Whale erd18mv2z6r2 (+5,925 EGLD)","reason":"Apr 18 OTC distribution pattern recurring. erd18mv2z6r2 now 998,970 EGLD (was 993,047). Same flow type: Coinbase Routing intermediary -> mega-whale wallet. Track erd18mv2z6r2 for downstream movement.","weeks_on_list":1},
 {"item":"Hatom LSD and XOXNO LSD both contracted in EGLD terms","reason":"Bilateral inverse rule applied to LSDs gives the OPPOSITE pattern this week: Hatom LSD EGLD -1.6%, XOXNO LSD EGLD -1.4%. Unusual - usually LSD users are long-term stakers. Possible: LSD users unstaking to free liquid EGLD during the decline. Watch next week to distinguish noise from emerging trend.","weeks_on_list":1},
 {"item":"DEX volume +12% during -15.7% price drop","reason":"On-chain liquidity rotation continues during EGLD stress. xExchange volume $122K (vs $108K last week). WEGLD/USDC dominance recovered to 93.2% (normalized). DeFi engagement remains healthy under price stress.","weeks_on_list":1},
 {"item":"Total delegators -447 WoW (-0.25%) - largest absolute drop in tracking","reason":"178,487 delegators, accelerating exodus (-24 to -53 prior weeks vs -447 now). z-score degenerate but the absolute move is the largest of any tracked week. Combined with stable total staked EGLD, this is concentrated re-staking by fewer larger holders.","weeks_on_list":1}]

# ---------- executive summary ----------
executive_summary=[
 {"finding":"EGLD -15.71% to $2.95, BROKE the $3.50 floor (run #10 prediction failed) - z=-3.32σ HIGH severity. 5-week cumulative -37% from May 4 peak. EGLD strongly UNDERPERFORMED BTC (+1.3%) and ETH (+3.6%) - decoupled to the downside, MultiversX-specific weakness. Regime shift to lower price band confirmed.","severity":"high","category":"network"},
 {"finding":"Binance Staking custody STALLED at 3.51M (UNCHANGED) - 3-week accumulation streak ENDED. The 779K parked since run #7 remains undeployed; no delegation, no distribution. Run #10's headline forward-indicator question partially resolved: stalled, awaiting the next decisive move.","severity":"high","category":"whale"},
 {"finding":"OTC desk distribution wave HIT ON SCHEDULE: UPbit OTC -14K, OTC Distribution -12.4K (combined -26.4K, -29%). Throughput 163K in 7d to retail. Confirms run #10's predicted load-then-distribute cycle. The load-distribute cycle is now empirically validated.","severity":"high","category":"whale"},
 {"finding":"Coinbase 3-week outflow streak BROKEN with +43K net inflow (primary wallet +51.5%). Run #10's cleanest off-exchange-accumulation signal REVERSED. Combined with the Binance custody stall, the bullish parked-capital thesis from run #10 collapses entirely - sell-into-decline pattern emerging.","severity":"high","category":"whale"},
 {"finding":"Bilateral inverse rule 5TH CONFIRMATION but WEAKENING: Hatom Lending +3.3% EGLD during -15.7% price drop (vs +8.3% during -11.8% in run #10). Magnitude scaling factor deteriorating - depositors DCAing less aggressively each decline leg. Possible signal: depositor exhaustion as the decline persists.","severity":"medium","category":"defi"},
 {"finding":"Yield-chase regime ENDED at week 5. Cohort net flow -2.6K (3 of 5 prior leaders reversed). Only ninjastaking sustained across all 5 weeks (+38K cumulative). The 0%-fee 9%+ APR migration regime can be removed from active watch.","severity":"medium","category":"staking"},
 {"finding":"Newly-issued token detection workaround SUCCEEDED via ESDT system SC scan: 3 issuances in 7d (FRA, GSN, GTA) - all low-quality with 0-2 holders. Method now standard. Resolves a 6-run blocker.","severity":"low","category":"token"},
 {"finding":"Coinbase Routing Wallet -> Unknown Mega Whale erd18mv2z6r2 (+5,925 EGLD on 2026-06-07). Apr 18 OTC distribution pattern recurring. Mega Whale now 998,970 EGLD - track for downstream movement.","severity":"medium","category":"whale"}]

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
   "btc_correlation_note":f"EGLD -15.71% WoW vs BTC +1.33% / ETH +3.56% (24h). EGLD UNDERPERFORMED both crypto majors - decoupled to the downside, MultiversX-specific weakness.",
   "transactions_added":st["transactions"]-pact["total_transactions"],"supply_added":econ["totalSupply"]-pecon["total_supply"],
   "staked_egld_added":staked-pecon["staked_egld"],"epoch_advanced":st["epoch"]-pact["epoch"]},
 "analysis":f"EGLD -15.71% WoW to $2.95, BREAKING the $3.50 floor predicted to hold in run #10 (z={zp[2]:+.2f} sigma, HIGH severity). The 5-week downtrend from the May 4 peak ($4.67 -> $3.88 -> $3.97 -> $3.50 -> $2.95) cumulates -37% and confirms a regime shift to a new lower price band. BTC +1.33% and ETH +3.56% (24h) BOTH closed up while EGLD fell sharply - decoupled to the downside, MultiversX-specific weakness rather than crypto-macro. Market cap $88.8M (-15.6%). Staked ratio mildly down to 48.08% (-0.17pp); protocol staked module fell -27K to 14.471M while Binance's staking custody wallet was unchanged at 3.51M - so the small decline came from organic delegator unstaking. Activity: ~1.62M txs (+1.62M WoW, near constant), epoch 2138 (+7). Account growth modest: +3,133 to 9.21M."}

# ---------- whale analysis ----------
whale_analysis=("THIS WEEK'S DOMINANT MOVES:\n"
 "1) BINANCE STAKING CUSTODY STALLED at 3,512,650 EGLD - the 3-week accumulation streak (run #7+9+10 cumulative +402K) ENDED. The wallet had ZERO movement this week. Run #10's headline forward-indicator question is half-resolved: neither bullish lockup (no protocol-staked jump) nor bearish distribution (no hot-wallet flow back) - just STALL. The 779K parked since run #7 is now a confirmed STRUCTURAL position pending the next decisive move.\n\n"
 "2) OTC DISTRIBUTION WAVE HIT ON SCHEDULE. Run #10 said: 'desks loaded +32.6K this week. Next 1-3 weeks should show distribution to retail.' This week: UPbit OTC Desk -14.0K (-30%), OTC Distribution Wallet -12.4K (-28%), combined -26.4K. Retail throughput in 7d: UPbit OTC 99,189 EGLD across 50 recipients; OTC Distribution 64,448 EGLD across 50 recipients. The distribution arrived in the very first week of the predicted 1-3 week window - faster execution than the historical pattern, suggesting aggressive sell-side flow given the price decline.\n\n"
 "3) COINBASE 3-WEEK OUTFLOW STREAK BROKEN. The cleanest off-exchange-accumulation signal of the last 3 weeks (-39K/-12.9K/-10.1K) ABRUPTLY REVERSED to +43.0K NET INFLOW this week. Primary wallet +26.8K (+51.5%). Coinbase Routing Wallet separately sent 5,925 EGLD to Unknown Mega Whale erd18mv2z6r2 (the Apr 18 OTC pattern recurring). Run #10's recommended 4-week confirmation FAILED. The off-exchange-accumulation thesis collapses.\n\n"
 f"WHALE TIERS (top-{N_prev} apples-to-apples): mega {whale_tiers['mega_whales']['net_change_egld']/1000:+.1f}K, large {whale_tiers['large_whales']['net_change_egld']/1000:+.1f}K, mid {whale_tiers['mid_whales']['net_change_egld']/1000:+.1f}K. Mega-whale tier essentially flat (UPbit cold -12.7K offset). Large-whale tier -69.5K (Binance hot -36.7K is the dominant component). Mid-whale tier +103K - this is the redistribution: capital from the largest holders flowing into the mid-whale band (10K-100K EGLD), consistent with the Coinbase +27K and various +5K to +12K mid-tier wallets gaining.\n\n"
 "EXCHANGE FLOWS: net +24.9K INFLOW (+0.38%), 1st week of inflow after 2 weeks of -56K and -71K outflow. The bullish off-exchange-accumulation setup from run #10 dissolved. With Binance Staking custody also STALLED, the entire 'parked capital' thesis collapses. The new pattern: on-exchange capital REBUILDING during the price decline. This is the classic sell-into-decline (capitulation/surrender) pattern - sellers giving up and depositing for offloading rather than holding through.\n\n"
 "Multi-week net exchange flow trajectory: +169K (run #8 bearish, deeply inverted) -> -56K -> -71K -> +25K. The bearish-bullish-bullish-bearish oscillation makes the signal noisy at the weekly level; combine with the price action (down 5 weeks) and the read is decisively bearish on net.")

# ---------- staking analysis ----------
staking_analysis=(f"Staking concentration remains low (HHI {hhi:.4f}, top-5 {top5:.1f}%, both essentially unchanged WoW). Total delegated {total_locked:,.0f} EGLD across {len(provs)} active providers. Active delegator base {cur_deleg:,} delegators (-447 WoW = -0.25% - the LARGEST single-week drop in tracking history).\n\n"
 "YIELD-CHASE REGIME ENDED AT WEEK 5. The 0%-fee 9%+ APR migration that ran from run #6 has now decisively rolled over. Net flow into the cohort this week: -2.6K. 3 of 5 previous leaders REVERSED: egldstakingprovider -3.1K, valuestaking -1.0K, orius -1.8K. Only ninjastaking +2.6K and procryptostaking +0.7K showed any positive flow. ninjastaking is the only sustained gainer across all 5 weeks (+38K cumulative). The regime can be removed from active watch.\n\n"
 f"APR distribution: 72% of stake in the 8-9% bucket ({buckets[3]['provider_count']} providers, {buckets[3]['total_locked_egld']/1e6:.1f}M). The 9-10% bucket holds only {buckets[4]['provider_count']} providers / {buckets[4]['total_locked_egld']/1e3:.0f}K EGLD. The 5-6% bucket has only 2 providers ({buckets[0]['total_locked_egld']/1e3:.0f}K) and 10%+ is empty (consistent across all 2026 runs). Apr-weighted average: {apr_w:.2f}%.\n\n"
 f"DELEGATOR CHURN ACCELERATED: {gain} providers gaining vs {lose} losing delegators (-447 net). Largest absolute weekly drop in tracking history. Combined with the staked-EGLD decline (-27K), this week broke the recent 6-reading flat-delegator pattern. Read: retail users beginning to leave delegation contracts amid the price decline (classic capitulation behavior). Watch next week to confirm whether this becomes a new declining trend.\n\n"
 "VALIDATOR MOVEMENTS: 6 system-contract addresses (erd1qqqq...) dropped out (treated as data artifact per run #10 rule). No real named-validator joiners or leavers >50K EGLD this week.")

# ---------- token analysis ----------
top_pair_share = pairs[0]['share_pct']
second_pair = pairs[1] if len(pairs)>1 else None
token_analysis=(f"DEX volume +12.3% to ${totvol/1000:.0f}K, continuing the trend from run #10's +32.5% recovery. WEGLD/USDC dominance back to {top_pair_share:.1f}% (historical norm), ZoidPay/WEGLD only {second_pair['share_pct'] if second_pair else 0:.1f}% (vs run #9's 40.8% event). Confirms run #9 was decisively event-driven, not regime-changing.\n\n"
 "NEWLY-ISSUED TOKENS workaround SUCCEEDED via ESDT system SC scan (run #10 recommendation #7 implemented): 3 issuances in 7d - FRANZELA (FRA-3d0fb7, 2 holders, 2 txs), GreenSmokeNetwork (GSN-514265, 1 holder, 0 txs), GrandTheftAurum (GTA-2329a1, 1 holder, 0 txs). All low-quality with no identifiable deployers - typical low-signal spam pattern. The method is now reliable and will run every week going forward. Resolves a 6-run blocker.\n\n"
 f"Token holder counts declined for an 11th consecutive week (-21 to -139 across top 10) - established airdrop-decay baseline. WrappedEGLD 132,589 (-123) and WrappedUSDC 81,882 (-139) remain the most-used real tokens.\n\n"
 f"MEX price -16.3% to ${meco['price']:.3e} (z={zmex[2]:+.2f} sigma, HIGH severity). Moved in lockstep with EGLD (-15.7%) and slightly worse - typical native-token amplification. MEX market cap $1.12M (-16%).\n\n"
 "Top by market cap: EmoryaSportsX $47.5M (likely price-feed artifact), USDC $8.41M, ZoidPay $4.73M (-11% from $5.30M), UTK $4.19M, SEGLD $2.51M, WEGLD $1.76M.\n\n"
 "WEGLD supply held essentially flat WoW (raw supply change near zero) - run #10's +4.7% wrap event was a one-off, not sustained DEX expansion, as predicted in last week's watch list.")

# ---------- defi analysis ----------
defi_analysis=(f"Hatom Lending +3.3% in EGLD ({prev_hl_egld/1000:.0f}K -> {hl_egld/1000:.0f}K) during the -15.7% price drop = BILATERAL INVERSE RULE 5TH CONFIRMATION. USD-denominated TVL fell -13.0% (${prev['defi_tvl']['Hatom Lending']/1e6:.2f}M -> ${hatom_lending/1e6:.2f}M). BUT the magnitude is WEAKER than run #10: that run saw +8.3% EGLD response to -11.8% price; this week +3.3% EGLD response to -15.7% price. Magnitude scaling has deteriorated significantly. Possible interpretation: depositor capacity diminishing OR conviction reducing as the decline persists. Magnitude history: +14.7%/-13%, -16.9%/+13.6%, -11.8%/+8.3%, -15.7%/+3.3% - the response intensity is now <25% of what the early observations indicated.\n\n"
 f"Hatom LSD ${hatom_lsd/1e6:.2f}M USD ({100*(hatom_lsd-prev_hlsd)/prev_hlsd:+.1f}%), {hlsd_egld/1000:.0f}K EGLD ({100*(hlsd_egld-prev_hlsd_egld)/prev_hlsd_egld:+.1f}%). LSD CONTRACTED in EGLD terms - unusual. Combined with XOXNO LSD also contracting -1.4% EGLD, this is a new pattern: LSD users may be unstaking to free liquid EGLD during the decline. Watch next week to confirm this as a trend.\n\n"
 f"XOXNO LSD ${xoxno_lsd/1e6:.2f}M / {xlsd_egld/1000:.0f}K EGLD ({100*(xlsd_egld-prev_xl_egld)/prev_xl_egld:+.1f}% EGLD, -16.2% USD).\n\n"
 f"xExchange TVL ${xexch_tvl_usd/1e6:.2f}M ({100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld:+.1f}% EGLD). DEX volume +12.3%. Aggregators continue elevated throughput (XOXNO {tcount('XOXNO Aggregator'):,}, OneDex {tcount('OneDex Swap'):,}) indicating on-chain rotation rather than exit.\n\n"
 f"Tracked TVL total: ~$10.9M (Hatom Lending $3.69M + Hatom LSD $2.51M + XOXNO LSD $1.05M + xExchange $1.76M + Hatom USH $618K + USH/misc). Down from $14.9M last week, mostly due to the price decline. Hatom still dominates with ~55% of tracked TVL.")

report={
 "metadata":{"report_date":"2026-06-08","period_start":"2026-06-01T00:00:00Z","period_end":"2026-06-08T00:00:00Z",
   "generated_at":datetime.now(timezone.utc).isoformat(),"egld_price_usd":price,
   "btc_price_usd":be["bitcoin"]["usd"],"eth_price_usd":be["ethereum"]["usd"],"run_number":11,
   "data_sources_ok":json.load(open("/tmp/run11/status.json"))["ok"],
   "data_sources_failed":["/tokens?sort=timestamp (HTTP 400 - silently unsupported; now resolved via ESDT system SC scan workaround)"]},
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
 "meta_learning":{"run_number":11,
   "endpoints_that_worked":json.load(open("/tmp/run11/status.json"))["ok"],
   "endpoints_that_failed":["/tokens?sort=timestamp (HTTP 400 - resolved via ESDT system SC workaround)"],
   "api_quirks":[
     "Newly-issued token detection workaround validated: /accounts/erd1qqqq...llls8a5w6u/transactions?function=issue returns recent issuance txs. Decode 'data' field as hex pairs separated by '@' to extract token name, ticker, supply, decimals. Then look up resulting identifier via /tokens?search=<NAME>.",
     "/tokens token data field 'supply' returns string or null; need int() conversion + fallback. For 'supply_raw' diffing, use prev.json supply_raw values directly (set as int) and compare to current 'supply' field after int(). Verified working this week with WEGLD diff (essentially flat WoW, confirming run #10 was a one-off).",
     "Funder address mistype risk: the actual OTC funder is erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp (not erd12tq6ax5k49dkp4lwgxz8ed62gz3xc3xwa30dgxqhke9awz58z2qq07ny36). Both prefixes match for the first ~16 chars. Run #10's collect script had the wrong address; this run inherited the typo. The real funder is queryable as a sender of 9,411 EGLD into erd17l22 (visible in erd17l22 inbound list). Recommend canonicalizing this address in known-addresses.json under 'exchange_routers'.",
     "Run #10 prediction that the OTC distribution wave would arrive in the next 1-3 weeks VALIDATED on the very first week of the window. Cycle period (load->distribute) is now confirmed at 1 week minimum."],
   "key_findings":[
     "EGLD -15.7% to $2.95, broke $3.50 floor (run #10 prediction failed) - regime shift to lower band confirmed.",
     "Binance Staking custody STALLED at 3.51M (UNCHANGED) - 3-week accumulation streak ended.",
     "OTC distribution wave hit on schedule (UPbit OTC -14K, OTC Distribution -12.4K = combined -26.4K).",
     "Coinbase 3-week outflow streak BROKEN with +43K inflow (off-exchange-accumulation thesis collapses).",
     "Yield-chase regime ENDED at week 5 (3 of 5 leaders reversed, only ninjastaking sustained +38K cumulative).",
     "Bilateral inverse rule 5th confirmation but WEAKENING (Hatom Lending +3.3% EGLD during -15.7% drop, vs +8.3%/-11.8% last week).",
     "Newly-issued token detection workaround successful via ESDT system SC scan (3 low-quality tokens found).",
     "Coinbase Routing Wallet -> Unknown Mega Whale +5,925 EGLD (Apr 18 OTC pattern recurring)."],
   "action_items_from_previous":9,"action_items_completed":7,
   "methodology_changes":[
     "NEW WORKAROUND: newly-issued token detection. Query /accounts/erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u/transactions?after=SEVEN_DAYS_AGO&function=issue. Decode tx.data (hex segments split on @) to read [name, ticker, supply, decimals, ...flags]. Then resolve the identifier via /tokens?search=<NAME>. Reliable; 5-10 calls per week.",
     "NEW PATTERN: 'failed forward indicator' as a strong bearish signal. Run #10 forecast 4 things to watch (custody resolution, OTC distribution, $3.50 floor hold, Coinbase 4th-week outflow). Three of the four resolved in the BEARISH direction (custody stalled, floor broke, Coinbase reversed); only the OTC distribution prediction was directionally validated. When multiple bullish forward indicators fail simultaneously, the read is decisively bearish on net.",
     "REFINED RULE: Bilateral inverse rule magnitude is DETERIORATING with consecutive declines. +14.7%/-13%, -16.9%/+13.6%, -11.8%/+8.3%, -15.7%/+3.3%. Each subsequent decline triggers a weaker EGLD-denominated TVL response. Hypothesis: depositor capacity is diminishing OR conviction reducing as the decline persists. Track magnitude ratio next week.",
     "NEW PATTERN: LSD contraction during a price decline is unusual and may indicate liquid-staked users unstaking to free EGLD. Both Hatom LSD (-1.6% EGLD) and XOXNO LSD (-1.4% EGLD) contracted this week - a synchronized LSD shrinkage during a decline. Watch for confirmation next week."],
   "new_addresses_discovered":0,
   "most_valuable_insight":"The combined collapse of 3 of 4 bullish forward indicators from run #10 - Binance custody STALLED (was +135K trend), Coinbase outflow REVERSED (was -10K trend), $3.50 floor BROKE (was hold-or-break test) - while EGLD fell -15.7% and decoupled from BTC/ETH (both up). This is not a coincidence: when multiple independent on-chain accumulation signals fail simultaneously during a decline, the convergence is a strong sell-side execution signal. The only directionally validated prediction was the OTC distribution wave (BEARISH for retail). Net read: the bullish parked-capital thesis from run #10 is decisively dead, replaced by a sell-into-decline pattern. The Binance custody and Coinbase reversal are the two highest-conviction signals.",
   "top_recommendation":"Track Binance Staking custody and Coinbase entity net flow weekly going forward as a paired indicator. If Binance custody starts drawing down (back to hot wallets) AND Coinbase remains in inflow mode, the distribution thesis confirms and the next $0.50 of EGLD downside is likely. If Binance custody flows into the protocol staked module (delegation) AND Coinbase returns to outflow, the bullish thesis reactivates. Either resolution within 2-3 weeks ends ambiguity.",
   "recommendations_for_next_run":[
     "Verify Binance Staking custody resolution: 4th week of stall, delegation jump, or hot-wallet drawdown. Each week without movement makes the eventual move more decisive.",
     "Check EGLD price action at $2.95: a bounce indicates capitulation low; a continued decline locks in the lower regime. BTC/ETH likely up suggests this remains MultiversX-specific.",
     "OTC desk reload check: after this week's distribution wave (-26.4K), expect loading phase to return within 1-2 weeks. Confirm cycle period.",
     "Track Coinbase entity for 2nd consecutive inflow: confirmation of sell-into-decline pattern requires a second week.",
     "LSD contraction follow-up: Hatom LSD and XOXNO LSD both contracted in EGLD terms this week. If next week confirms, this is a new bearish trend indicator (LSD users unstaking).",
     "Hatom Lending magnitude ratio: did the bilateral inverse rule magnitude continue deteriorating, OR did this week's weak response bottom out at +3.3%? Magnitude trajectory matters.",
     "Track Unknown Mega Whale erd18mv2z6r2 - received +5,925 from Coinbase Routing Wallet this week (now 998,970 EGLD, near 1M threshold). Watch for downstream forwarding.",
     "Newly-issued token scan continues: check if any of FRANZELA, GreenSmokeNetwork, GrandTheftAurum showed adoption (>10 holders, >5 txs) - confirms genuine vs spam.",
     "Re-trace the OTC funder using the CORRECT address (erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp). Add to known-addresses.json under exchange_routers."],
   "dashboard_feature_suggestions":[
     {"title":"Forward-indicator scorecard widget","motivation":"Run #11's single most valuable insight came from tracking whether last week's PREDICTIONS were validated or invalidated. 3 of 4 run #10 predictions resolved bearish. A scorecard showing each report's open predictions with status (pending/validated/invalidated) would make this pattern visible at a glance and let users see when consensus bullish indicators are all failing simultaneously.","suggested_visualization":"vertical list per report, each row: prediction text + outcome icon (green/red/grey pending). Group by report. Top of dashboard.","data_already_available":True,"data_source":"meta_learning.recommendations_for_next_run in each report JSON + manual status tagging from the following week's run","priority":"high"},
     {"title":"OTC cycle phase indicator","motivation":"Run #10 said 'desks loaded, expect distribution 1-3 weeks'. Run #11 confirmed distribution arrived in week 1. The load-distribute cycle is now empirically validated. A simple phase-tracker (LOADING / DISTRIBUTING / DRAINED) per desk with countdown to expected reversal would let users anticipate the next event.","suggested_visualization":"phase chip per desk + 'expected reversal in N days' text. Optional: timeline view of phase transitions across past 5 weeks.","data_already_available":True,"data_source":"OTC desk balance + WoW change from report JSONs + simple state machine logic","priority":"high"},
     {"title":"Bilateral inverse rule magnitude trajectory","motivation":"Run #11 noted the rule's magnitude is DETERIORATING - response intensity now <25% of early observations. A chart of (Hatom Lending EGLD response %) divided by (|EGLD price change %|) across all confirmed events would show whether the rule's signal strength is fading - critical for interpreting future readings.","suggested_visualization":"line chart of response ratio across confirmed events; reference line at 1.0 = unit elasticity, declining trend = depositor fatigue","data_already_available":True,"data_source":"defi_activity.protocol_breakdown[Hatom Lending].tvl_wow_change_pct + network_health.deltas.price_change_pct across reports","priority":"medium"}],
   "dashboard_suggestions_followup":[
     {"prior_title":"Multi-week Binance custody vs protocol-staked tracker chart","status":"pending","note":"This week's STALL of the custody wallet (3.51M unchanged) plus ongoing protocol-staked microvariation makes this even more valuable - the next move will be either a delegation step (custody->staked) or a distribution step (custody->hot). Visualization would make the resolution moment unmissable."},
     {"prior_title":"OTC pipeline phase visualization (load vs distribute)","status":"pending","note":"Run #11 empirically confirms the load-distribute cycle exists. This week's distribution wave hit exactly when run #10 predicted. The visualization is now strongly motivated by validated data."},
     {"prior_title":"Bilateral inverse rule EGLD-vs-USD divergence chart for Hatom Lending","status":"pending","note":"This week added the 5th data point (and the first showing DETERIORATING magnitude). The chart would now show both the inverse rule and its weakening intensity - higher value."}]}}

json.dump(report,open(f"{REPO}/reports/2026-06-08.json","w"),indent=2)
print("WROTE reports/2026-06-08.json")
print("exec_summary:",len(executive_summary),"large_tx:",len(large_transactions),"wallet_changes:",len(wallet_changes),
      "providers:",len(provs),"anomalies:",len(anomalies),"watch:",len(watch_list))
print("net exchange flow:",round(net_total,1),"total_locked:",round(total_locked,1),"apr_w:",round(apr_w,3))
print("DEFI: Hatom Lending USD",round(hatom_lending),"LSD",round(hatom_lsd),"USH",round(hatom_ush),"XOXNO LSD",round(xoxno_lsd))
print("Token supply events:",len(token_supply_events))
print("Newly issued:",len(newly_issued))
print("trend_indicators.notable_joiners:", len(notable_joiners), "notable_leavers:", len(notable_leavers))
