#!/usr/bin/env python3
"""Assemble reports/2026-05-25.json (run #9) from collected data."""
import json, math
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D = json.load(open("/tmp/run9/collected.json"))
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
wallet_changes=changes[:15]

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
large_transactions=bigtx[:22]

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
prev_ent={}
for k,v in prev["exchange_balances"].items():
    if "Binance" in k: prev_ent["Binance"]=prev_ent.get("Binance",0)+v
    elif "Coinbase" in k: prev_ent["Coinbase"]=prev_ent.get("Coinbase",0)+v
    elif "Crypto.com" in k: prev_ent["Crypto.com"]=prev_ent.get("Crypto.com",0)+v
    else: prev_ent[k]=prev_ent.get(k,0)+v
ent_interp={
 "Binance":"Hot wallet erd1sdsl -316K moved into staking-custody wallet (+267K, now 3.38M); entity net -49K. Internal hot->staking shuffle, NOT a real off-exchange flow.",
 "Coinbase":"Hot wallet -21K, partially offset by secondary; net -12.9K. Reverses last week's +39K bearish inflow.",
 "Crypto.com":"Net -7.7K across two wallets.",
 "Bybit":"Hot wallet +5.6K. Continues to receive OTC routing flow (Bidirectional router, Bybit->UPbit OTC).",
 "MEXC":"Net +4.8K.","KuCoin":"Net +1.9K.","Bitget":"Net +1.0K.","Gate.io":"Net +0.5K (stabilized after run #8's +21K).",
 "Tokero":"Net -0.1K (flat).","Bitfinex":"Flat.","UPbit":"Hot wallet flat; OTC desk separately active in distribution."}
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
    "signal":"mild net outflow (-56K) reversing last week's +169K bearish inflow. Dominated by Binance hot->staking-custody shuffle (+267K into Binance Staking wallet); the +169K capitulation read was a single-week reaction, not multi-week.",
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
        "apr_pct":aprp(p),"fee_pct":feep(p),"num_users":p.get("numUsers"),"num_nodes":p.get("numNodes"),
        "wow_change_egld":(p["_lk"]-pl) if pl is not None else None})
apr_w=sum(p["_lk"]*aprp(p) for p in provs)/total_locked
buckets=[]
for lbl,mn,mx in [("5-6%",5,6),("6-7%",6,7),("7-8%",7,8),("8-9%",8,9),("9-10%",9,10),("10%+",10,100)]:
    sub=[p for p in provs if mn<=aprp(p)<mx]
    buckets.append({"label":lbl,"min_apr_pct":mn,"max_apr_pct":mx,"provider_count":len(sub),
        "total_locked_egld":sum(p["_lk"] for p in sub)})
qual=[p for p in provs if p["_lk"]>5000]
top_apr=[{"identity":p.get("identity") or p["provider"],"apr_pct":aprp(p),"fee_pct":feep(p),
    "locked_egld":p["_lk"],"name":p.get("identity") or p["provider"]} for p in sorted(qual,key=lambda p:-aprp(p))[:5]]
lowest_fee=[{"identity":p.get("identity") or p["provider"],"apr_pct":aprp(p),"fee_pct":feep(p),
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
protocol_breakdown=[
 {"protocol":"xExchange","category":"dex","addresses_tracked":16,"tvl_usd":xexch_tvl_usd,"tvl_egld":xexch_tvl_egld,
  "tvl_wow_change_pct":100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld,"transfers_24h":None,"volume_24h_usd":totvol,
  "notable_events":"WEGLD/USDC dominance collapsed 91.6%->56.2% as ZoidPay/WEGLD volume surged to 40.8% ($33.4K). DEX volume +9.4% to $81.9K. TVL -4.7% in EGLD terms.","health_signal":"shrinking"},
 {"protocol":"Hatom Lending","category":"lending","addresses_tracked":13,"tvl_usd":hatom_lending,"tvl_egld":hatom_lending/price,
  "tvl_wow_change_pct":100*(hatom_lending/price-prev_hl_egld)/prev_hl_egld,"transfers_24h":tcount("Hatom EGLD MM"),
  "notable_events":"TVL +1.3% USD / -1.0% EGLD during the +2.3% price recovery. Consistent with bilateral inverse rule: depositors trim during rallies.","health_signal":"flat"},
 {"protocol":"Hatom Liquid Staking","category":"liquid_staking","addresses_tracked":2,"tvl_usd":hatom_lsd,"tvl_egld":hatom_lsd/price,
  "tvl_wow_change_pct":100*((hatom_lsd/price)-(4.55e6/ppx))/(4.55e6/ppx),"transfers_24h":tcount("Hatom Liquid Staking"),
  "notable_events":"SEGLD-3ad2d0 mcap $3.49M + SWTAO-356a25 $1.16M = $4.65M. Flat in EGLD (~1.17M) this week, pausing the 2-week accumulation streak during the price recovery (inverse rule).","health_signal":"flat"},
 {"protocol":"Hatom USH","category":"stablecoin","addresses_tracked":4,"tvl_usd":hatom_ush,"tvl_egld":hatom_ush/price,
  "tvl_wow_change_pct":100*(hatom_ush-prev_hush)/prev_hush,"transfers_24h":None,
  "notable_events":"USH-111e09 mcap $690K. Stablecoin scale unchanged (flat).","health_signal":"flat"},
 {"protocol":"XOXNO LSD","category":"liquid_staking","addresses_tracked":2,"tvl_usd":xoxno_lsd,"tvl_egld":xoxno_lsd/price,
  "tvl_wow_change_pct":100*((xoxno_lsd/price)-prev_xl_egld)/prev_xl_egld,"transfers_24h":tcount("XOXNO LSD"),
  "notable_events":"XEGLD-e413ed mcap $1.42M (+2% USD, flat -0.3% EGLD).","health_signal":"flat"},
 {"protocol":"XOXNO Aggregator","category":"aggregator","addresses_tracked":1,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("XOXNO Aggregator"),
  "notable_events":"Throughput +20.2% WoW to 11,933 daily transfers, recovering part of run #8's -40.8% retracement.","health_signal":"growing"},
 {"protocol":"OneDex","category":"aggregator","addresses_tracked":5,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("OneDex Swap"),
  "notable_events":"6,916 daily transfers, flat WoW (-1%).","health_signal":"flat"},
 {"protocol":"JEXchange","category":"dex","addresses_tracked":4,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("JEXchange Fees"),
  "notable_events":"Fees wallet throughput +23.6% to 2,607 daily transfers.","health_signal":"growing"}]
protocols=[
 {"name":"xExchange","category":"dex","volume_24h_usd":totvol,"active_pairs":25,"transfers_24h":None,"tvl_usd":xexch_tvl_usd,"tvl_egld":xexch_tvl_egld,"tvl_wow_change_pct":None},
 {"name":"Hatom Lending","category":"lending","volume_24h_usd":None,"active_pairs":None,"transfers_24h":None,"tvl_usd":hatom_lending,"tvl_egld":hatom_lending/price,"tvl_wow_change_pct":None},
 {"name":"Hatom Liquid Staking","category":"liquid_staking","volume_24h_usd":None,"active_pairs":None,"transfers_24h":None,"tvl_usd":hatom_lsd,"tvl_egld":hatom_lsd/price,"tvl_wow_change_pct":None},
 {"name":"XOXNO LSD","category":"liquid_staking","volume_24h_usd":None,"active_pairs":None,"transfers_24h":None,"tvl_usd":xoxno_lsd,"tvl_egld":xoxno_lsd/price,"tvl_wow_change_pct":None}]

# ---------- anomalies ----------
rb=learn["runs"][-1]["running_baselines"]
def zc(arr,cur):
    if len(arr)<4: return None
    m=sum(arr)/len(arr); sd=math.sqrt(sum((x-m)**2 for x in arr)/len(arr))
    return m,sd,((cur-m)/sd if sd else 0)
zd=zc(rb["total_delegators"],cur_deleg)
zsr=zc(rb["staked_ratio"],sr)
zmex=zc(rb["mex_price_usd"],meco["price"])
anomalies=[
 {"metric":"total_delegators","current_value":cur_deleg,"previous_value":prev_deleg,"method":"z_score",
  "average_value":zd[0],"stddev":zd[1],"z_score":zd[2],"severity":"medium",
  "description":f"Total delegators {cur_deleg} (-53 WoW). z={zd[2]:.2f} sigma but this is a DEGENERATE z-score: the baseline has near-zero variance (sd={zd[1]:.0f} delegators over 4 weeks), so a -0.03% move registers as >4 sigma. Economically the signal is minor. The real read: delegator base flat-to-declining for 5 consecutive readings (179038->179060->179050->179011->178958) while staked EGLD holds at 14.47M = continued whale consolidation, retail not joining."},
 {"metric":"staked_ratio","current_value":sr,"previous_value":pecon["staked_ratio"],"method":"z_score",
  "average_value":zsr[0],"stddev":zsr[1],"z_score":zsr[2],"severity":"low",
  "description":f"Staked ratio 48.22% (z={zsr[2]:.2f} sigma). Receded from run #8's -1.81 sigma as the ratio stabilized (-0.07pp WoW). The run #8 watch for a z<-2 breach did NOT trigger. 50% milestone remains ~1.8pp away."},
 {"metric":"zoidpay_price_and_dex_share","current_value":0.008642909732690761,"previous_value":0.005432310832366669,"method":"rule_based",
  "severity":"medium",
  "description":"ZoidPay (ZPAY) +59.1% price ($0.00543->$0.00864, mcap $3.34M->$5.32M) and its ZPAY/WEGLD pair surged to 40.8% of all xExchange volume ($33.4K), collapsing WEGLD/USDC dominance from 91.6% to 56.2%. First time in tracking history a non-WEGLD/USDC pair captured >40% of DEX volume. Echoes run #4's ZPAY +33% move - recurring accumulation pattern, possible catalyst pending."},
 {"metric":"binance_hot_to_staking_consolidation","current_value":266896.5,"previous_value":0,"method":"rule_based",
  "severity":"medium",
  "description":"Binance.com hot wallet erd1sdsl -316K; +267K landed in Binance Staking custody wallet (now 3.38M). The protocol staked module rose only +2,078, so this 267K is PARKED in the staking wallet, not yet delegated. Combined with run #7's 377K, Binance is accumulating EGLD in its staking-designated wallet. Watch whether it gets delegated (bullish stake) or moves to hot wallets (sell)."}]

# ---------- trend indicators ----------
prev_names=set(prevp.keys()); cur_names={(p.get('identity') or p['provider']) for p in provs}
joining=[n for n in cur_names-prev_names if n]
leaving=[n for n in prev_names-cur_names if n]
trend_indicators={
 "accelerating_exchange_outflows":[],
 "validator_movements":{"providers_joining":len(joining),"providers_leaving":len(leaving),
   "net_provider_change":len(provs)-len(prev["staking_providers"]),
   "notable_joiners":[],"notable_leavers":[]},
 "token_supply_events":[],
 "consecutive_streaks":[
   {"metric":"token_holder_count_decline","direction":"down","weeks":9,"cumulative_change_pct":None,
    "interpretation":"9th consecutive week of small holder declines across all top-10 tokens (-21 to -95 this week). Established airdrop-decay baseline; active >$1M-mcap token base stable."},
   {"metric":"yield_chase_migration","direction":"up","weeks":4,"cumulative_change_pct":None,
    "interpretation":"Week 4 of the 0%-fee 9%+ APR migration. Leadership rotated this week: procryptostaking +17.1K and valuestaking +16.2K led (both 0%/low-fee high-APR), while last week's leader egldstakingprovider gave back -4.5K. Pattern persists structurally but rotates within the low-fee cohort."}],
 "regime_shifts":[
   {"metric":"yield_chase_validator_migration","before_value":None,"after_value":0,
    "description":"Yield-chase regime shift holds into week 4. Cumulative ~+50K to low-fee high-APR providers over 4 weeks (procryptostaking, valuestaking, ninjastaking, orius). Confirms permanent reallocation; ~1pp APR spread is sufficient to pull delegated capital."},
   {"metric":"dex_pair_concentration","before_value":91.6,"after_value":pairs[0]["share_pct"],
    "description":"WEGLD/USDC single-pair dominance dropped from 91.6% (run #8) to 56.2% as ZoidPay/WEGLD captured 40.8%. Watch next week: if ZPAY volume reverts, this is event-driven; if sustained, the DEX has a genuine second active market for the first time in tracking history."}]}

# ---------- watch list ----------
watch_list=[
 {"item":"Binance Staking custody wallet now 3.38M (+267K this week)","reason":"Run #7's 377K parked capital GREW by another 267K (hot wallet erd1sdsl -316K -> staking wallet). Protocol staked module did NOT rise, so it is parked/pre-positioned, not delegated. Watch: delegation (bullish lockup) vs move to hot wallets (sell pressure).","weeks_on_list":3},
 {"item":"ZoidPay (ZPAY) +59% price, 40.8% of DEX volume","reason":"First non-WEGLD/USDC pair to capture >40% of xExchange volume. Mcap $3.34M->$5.32M. Echoes run #4's +33% move. Watch for catalyst / whether the volume sustains or reverts.","weeks_on_list":1},
 {"item":"Yield-chase regime shift - week 4, leadership rotating","reason":"procryptostaking +17.1K, valuestaking +16.2K led this week; egldstakingprovider gave back. Pattern persists into week 4 (permanent reallocation) but rotates within the 0%-fee cohort.","weeks_on_list":4},
 {"item":"Exchange flows reversed to net -56K outflow","reason":"Last week's +169K bearish inflow did NOT continue - reversed to mild outflow (single-week reaction confirmed). Dominated by Binance internal shuffle. Watch for re-acceleration of inflows (bearish) or sustained outflows (bullish accumulation off-exchange).","weeks_on_list":2},
 {"item":"OTC pipeline in active distribution phase (~145K throughput)","reason":"UPbit OTC Desk + OTC Distribution net distributing ~54K to retail recipients while receiving ~47K from Binance->OTC routers. Both desks -8.5K/-9.3K WoW (drawing down). Source wallet erd17l22 went dormant after its run #8 distribution wave.","weeks_on_list":5},
 {"item":"Unknown Mega Whale erd18mv2 (993K) - small bidirectional Coinbase activity","reason":"Flat balance (+0.9K) but resumed small two-way flow with Coinbase routing wallet (recv 6.1K, sent 5.2K). 6 weeks since the Apr 18 Coinbase OTC receipt. Still 4th-largest non-system account.","weeks_on_list":6},
 {"item":"erd17l22 OTC source - funding partially traced","reason":"Dormant this week (only +2K inbound from erd12tq6ax5k - a candidate funding wallet). Last week's distribution wave (-26K) appears to be a completed cycle. Add erd12tq6ax5k to monitoring as the upstream funder.","weeks_on_list":3},
 {"item":"Total delegators flat for 5 readings (whale consolidation)","reason":"178,958 (-53). Delegator base essentially flat for 5 weeks while staked EGLD holds at 14.47M. Classic whale-consolidation signature: fewer/larger holders, no retail inflow. The z=-4.5 sigma is a low-variance artifact, not a real anomaly.","weeks_on_list":1},
 {"item":"Token holder decline streak (now 9 weeks)","reason":"Confirmed structural airdrop decay. Watch for any week the streak breaks (would indicate real user growth).","weeks_on_list":5},
 {"item":"Newly-issued token detection still blocked","reason":"4th run carrying. /tokens?sort=timestamp returns HTTP 400. ESDT system-contract issuance scan workaround still TODO.","weeks_on_list":2}]

# ---------- executive summary ----------
executive_summary=[
 {"finding":"Binance moved 266K EGLD from its hot wallet (erd1sdsl -316K) into its staking-custody wallet (now 3.38M). The protocol staked module rose only +2K, so the capital is PARKED, not yet delegated - run #7's 377K parked stash has grown, not deployed.","severity":"high","category":"whale"},
 {"finding":"Exchange flows REVERSED to net -56K outflow (vs +169K inflow last week). The bearish capitulation read was a single-week reaction, not multi-week. Most of the move is Binance's internal hot->staking shuffle; other exchanges near-flat.","severity":"medium","category":"whale"},
 {"finding":"ZoidPay (ZPAY) +59% price and its ZPAY/WEGLD pair captured 40.8% of xExchange volume - first time a non-WEGLD/USDC pair broke 40%, collapsing WEGLD/USDC dominance from 91.6% to 56.2%.","severity":"medium","category":"token"},
 {"finding":"Yield-chase regime shift persists into week 4 with rotating leadership: procryptostaking +17.1K and valuestaking +16.2K led (0%-fee 9% APR); egldstakingprovider gave back -4.5K. ~1pp APR spread continues to pull delegated capital structurally.","severity":"medium","category":"staking"},
 {"finding":"EGLD +2.3% to $3.97 - partial recovery from last week's -16.9% drop. z-score normal (-0.27 sigma). BTC flat (+0.6%), ETH flat (0%) - EGLD modestly outperformed on the week.","severity":"low","category":"network"},
 {"finding":"Total delegators flat for a 5th reading (178,958, -53) while staked EGLD holds at 14.47M - continued whale consolidation, retail not joining. The headline z=-4.5 sigma is a low-variance artifact, not a true anomaly.","severity":"medium","category":"staking"},
 {"finding":"OTC pipeline in active distribution phase: ~145K throughput, UPbit OTC Desk + OTC Distribution paid out ~54K to retail while drawing down (-8.5K/-9.3K). Source wallet erd17l22 went dormant after its run #8 wave; funding partially traced to erd12tq6ax5k.","severity":"medium","category":"whale"}]

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
   "btc_correlation_note":f"EGLD +2.32% WoW vs BTC +0.58% / ETH -0.01% (24h)",
   "transactions_added":st["transactions"]-pact["total_transactions"],"supply_added":econ["totalSupply"]-pecon["total_supply"],
   "staked_egld_added":staked-pecon["staked_egld"],"epoch_advanced":st["epoch"]-pact["epoch"]},
 "analysis":f"EGLD recovered +2.3% to $3.97, clawing back roughly an eighth of last week's -16.9% drop. Z-score back to -0.27 sigma (normal). BTC +0.58% and ETH flat (24h) - EGLD modestly outperformed on the week but the two-week round-trip ($4.67 -> $3.88 -> $3.97) leaves it still well below the early-May peak. Market cap $119.1M (+2.5%). Staked ratio slipped marginally to 48.22% (-0.07pp); the run #8 watch for a z<-2 sigma breach did not trigger - the ratio stabilized. Network activity 1,183,917 txs in 7d (~169K/day), down ~7% from last week's pace. Token market cap dropped further to $42.2M (from $48.0M) as alt valuations compressed. Accounts +1,691 to 9.20M, epoch 2124 (+7)."}

# whale analysis
whale_analysis=("THE WEEK'S DOMINANT MOVE: Binance hot wallet erd1sdsl fell -316K (722K->406K) and 266,896 EGLD landed in the Binance Staking custody wallet (3.11M->3.38M) in a single tx on May 24. The protocol staked module rose only +2K, so this capital is PARKED in Binance's staking-designated wallet, NOT delegated. Together with run #7's 377K unstaking parked here, Binance has accumulated a large EGLD position in its staking wallet that has not been deployed on-chain - an open option worth watching for either delegation (lockup) or movement to hot wallets (sell).\n\n"
 f"WHALE TIERS (top-{N_prev} apples-to-apples): mega +267K (Binance Staking crossed deeper above 1M; UPbit flat), large -176K (driven by the Binance hot-wallet drawdown), mid -25K. The mega gain and large loss are two sides of the same Binance internal shuffle.\n\n"
 "EXCHANGE FLOWS reversed to net -56K outflow (vs +169K inflow last week). Entity netting: Binance -49K (internal hot->staking shuffle), Coinbase -12.9K (reverses last week's +39K), Crypto.com -7.7K; small inflows to Bybit (+5.6K), MEXC (+4.8K), KuCoin (+1.9K). Last week's bearish capitulation read was a single-week reaction, NOT multi-week.\n\n"
 "OTC PIPELINE in active distribution phase: ~145K throughput across 68 router/desk txs. UPbit OTC Desk + OTC Distribution Wallet distributed ~54K to retail recipients while receiving ~47K from Binance->OTC routers (5.6K/4.2K chunks); both desks drew down (-8.5K/-9.3K). Source wallet erd17l22 went DORMANT after its run #8 distribution wave (only +2K inbound from erd12tq6ax5k, a candidate upstream funder). Unknown Mega Whale erd18mv2 (993K, flat) resumed small bidirectional flow with Coinbase routing (recv 6.1K, sent 5.2K).")

# staking analysis
staking_analysis=(f"Staking stays competitive (HHI {hhi:.4f}, top-5 {top5:.1f}%). Total delegated {total_locked:,.0f} EGLD across {len(provs)} active providers (flat WoW). \n\n"
 "YIELD-CHASE WEEK 4 with rotating leadership. Top gainers: procryptostaking +17.1K (0% fee, 9.19% APR, 7,174 users), valuestaking +16.2K, bober +8.5K (0.07% fee), orius +4.3K. Last week's leaders cooled - egldstakingprovider -4.5K, ninjastaking +1.2K (after +19.4K last week). The capital keeps rotating among the 0%-fee 9%+ APR cohort; cumulative absorption ~+50K over 4 weeks confirms structural reallocation. Losers remain mid-tier 7-8% APR 0.1%+ fee providers (meria -1.3K, orangestaking -1.3K, aurentum -1.7K, thepalmtreenw -1.2K). \n\n"
 f"APR distribution: 64% of stake in the 8-9% bucket (74 providers, {buckets[3]['total_locked_egld']/1e6:.1f}M), 13% in 6-7% (5 providers incl. Figment/Binance), 6 providers in 9-10% holding {buckets[4]['total_locked_egld']/1e3:.0f}K. \n\n"
 f"DELEGATOR CHURN: {cur_deleg:,} (-53 WoW), {gain} providers gaining vs {lose} losing - broad mid-tier exodus continues. Delegator base flat for 5 readings while staked EGLD holds = concentrated re-staking by fewer/larger holders. \n\n"
 "VALIDATOR MOVEMENTS: quiet week, net provider count flat (107). No confident named large joiners or leavers (after run #8's MrsEGLD 158K joiner). Note: anonymous delegation-contract providers are hard to match WoW by name, so small apparent churn is treated conservatively.")

# token analysis
token_analysis=("DEX volume +9.4% to $81.9K - still within normal range (z=-0.58) but the COMPOSITION shifted dramatically. ZoidPay/WEGLD surged to $33.4K (40.8% of all volume), collapsing WEGLD/USDC dominance from 91.6% to 56.2%. This is the first time in tracking history a non-WEGLD/USDC pair captured >40% of xExchange volume. It pairs with ZPAY's +59% price move ($0.00543->$0.00864, mcap $3.34M->$5.32M) - reminiscent of run #4's +33% ZPAY surge. Possible accumulation ahead of a catalyst; flagged as a rule-based anomaly and watch-list item.\n\n"
 "Token holder counts declined for a 9th consecutive week (-21 to -95 across the top 10) - the established airdrop-decay baseline. WrappedUSDC 82,113 (-85) remains the most-used real token. \n\n"
 "MEX price +1.9% WoW to 3.78e-07; z-score now ACTIVE (N=4, z=-0.83, normal). Top by market cap: EmoryaSportsX $36.4M (likely price-feed artifact, down from $38.5M), ZoidPay newly $5.3M (up on the rally), UTK $4.2M, SEGLD $3.49M. \n\n"
 "Newly-issued tokens: none detected. /tokens?sort=timestamp still returns HTTP 400 (4th run); token_supply_events left empty because previous.json stored decimals-adjusted supply while the API now returns raw integer supply (not directly comparable) - a methodology fix is needed before supply-event detection is reliable.")

# defi analysis
defi_analysis=(f"Hatom still dominates: Lending $4.44M + LSD $4.65M + USH $691K = $9.78M (~68% of tracked TVL). \n\n"
 "BILATERAL INVERSE RULE - mild confirmation in the other direction: during this week's +2.3% price recovery, Hatom Lending TVL rose +1.3% USD but FELL -1.0% in EGLD terms, and Hatom LSD held flat in EGLD (~1.17M), pausing its 2-week accumulation streak. Consistent with the rule that depositors trim during rallies. The effect is small because the price move was small (+2.3% vs the +/-15% swings of runs #7-#8). \n\n"
 "xExchange TVL -4.7% in EGLD ($2.21M). XOXNO LSD flat in EGLD ($1.42M). \n\n"
 "Aggregator throughput recovering: XOXNO Aggregator +20.2% to 11,933 daily transfers (partial rebound from run #8's -40.8% retracement), JEXchange +23.6% to 2,607, OneDex flat at 6,916. \n\n"
 "AshSwap pools still return zero EGLD across tracked admin contracts (TVL sits in stableswap pools not yet in the address set - expansion still TODO).")

report={
 "metadata":{"report_date":"2026-05-25","period_start":"2026-05-18T00:00:00Z","period_end":"2026-05-25T00:00:00Z",
   "generated_at":datetime.now(timezone.utc).isoformat(),"egld_price_usd":price,
   "btc_price_usd":be["bitcoin"]["usd"],"eth_price_usd":be["ethereum"]["usd"],"run_number":9,
   "data_sources_ok":json.load(open("/tmp/run9/status.json"))["ok"],
   "data_sources_failed":["/tokens?sort=timestamp (HTTP 400 - silently unsupported; client-side filter on /tokens?sort=transactions sample yielded 0 issuances in 7d window)"]},
 "executive_summary":executive_summary,
 "network_health":network_health,
 "whale_intelligence":{"large_transactions":large_transactions,"wallet_changes":wallet_changes,
   "whale_tiers":whale_tiers,"exchange_flows":exchange_flows,"dormant_activations":[],"analysis":whale_analysis},
 "staking_intelligence":{"summary":{"total_staked_egld":staked,"total_delegated_egld":total_locked,
   "staked_ratio":sr,"num_providers":len(provs),"apr_min":min(aprp(p) for p in provs),
   "apr_max":max(aprp(p) for p in provs),"apr_weighted_avg":apr_w},
   "top_providers":top_providers,"concentration":{"top_5_share_pct":top5,"top_10_share_pct":top10,
   "hhi":hhi,"hhi_previous":prev["staking_concentration"]["hhi"],"hhi_interpretation":"competitive"},
   "apr_distribution":{"buckets":buckets},"apr_outliers":{"top_apr":top_apr,"lowest_fee":lowest_fee},
   "churn":churn,"analysis":staking_analysis},
 "token_activity":{"top_by_holders":top_by_holders,"top_by_volume":top_by_volume,
   "top_by_market_cap":top_by_market_cap,"newly_issued":[],"xexchange":xexchange,"analysis":token_analysis},
 "defi_activity":{"protocols":protocols,"protocol_breakdown":protocol_breakdown,"sc_deployments":[],"analysis":defi_analysis},
 "anomalies":anomalies,
 "trend_indicators":trend_indicators,
 "watch_list":watch_list,
 "meta_learning":{"run_number":9,
   "endpoints_that_worked":json.load(open("/tmp/run9/status.json"))["ok"],
   "endpoints_that_failed":["/tokens?sort=timestamp (HTTP 400)"],
   "api_quirks":[
     "Whale-tier deltas confirmed stable with top-50-vs-top-50 trimming (prev stored 60 accounts; trimmed current to 60).",
     "total_delegators z-score is degenerate: baseline sd ~18 delegators means any small move shows >4 sigma. Do NOT treat near-constant metrics' z-scores at face value - cross-check absolute % change before assigning severity.",
     "mex/economics volume24h returned a nonzero value ($121K) this run (was $0 historically); still prefer mex/pairs sum ($81.9K) for DEX volume consistency.",
     "Token supply comparison broken: previous.json stored decimals-adjusted supply, /tokens returns raw integer supply string - not comparable. token_supply_events needs a decimals-aware diff."],
   "key_findings":[
     "Binance moved 266K hot->staking-custody wallet (now 3.38M); parked, not delegated.",
     "Exchange flows reversed +169K inflow -> -56K outflow (single-week reaction, not capitulation).",
     "ZoidPay +59%, captured 40.8% of DEX volume - WEGLD/USDC dominance 91.6%->56.2%.",
     "Yield-chase week 4, leadership rotated (procryptostaking +17K, valuestaking +16K).",
     "EGLD +2.3% to $3.97, partial recovery; z-score normal -0.27 sigma.",
     "Total delegators flat 5 readings (whale consolidation); z=-4.5 is low-variance artifact.",
     "OTC pipeline in distribution phase (~145K throughput); erd17l22 source dormant, funder erd12tq6ax5k identified.",
     "MEX z-score activated (N=4, z=-0.83 normal).",
     "Hatom Lending -1% EGLD during +2.3% rally - mild bilateral-inverse confirmation."],
   "action_items_from_previous":11,"action_items_completed":8,
   "methodology_changes":[
     "NEW RULE: degenerate z-scores. When a baseline's stddev is tiny relative to the metric (e.g. total_delegators sd~18 on a ~179K base), the z-score inflates spuriously. Cross-check absolute % change; downgrade severity when the economic move is <0.1%.",
     "CONFIRMED: intra-entity wallet shuffles (Binance hot->staking custody) can dominate the headline exchange-flow number. Always decompose entity netting into per-wallet moves before calling a flow bullish/bearish.",
     "CONFIRMED (mild): bilateral inverse rule holds for small moves too - +2.3% price -> Hatom Lending -1% EGLD. Magnitude scales with price move.",
     "EXCHANGE-FLOW REVERSAL: run #8's +169K bearish inflow was a single-week reaction (reverted to -56K). Two-week confirmation rule worked - do not extrapolate single-week capitulation."],
   "new_addresses_discovered":1,
   "most_valuable_insight":"Binance's staking-custody wallet has quietly grown to 3.38M EGLD - run #7's 377K unstaking parked here, and this week another 267K arrived from the hot wallet, yet the protocol staked module barely moved. Binance is accumulating a large undeployed EGLD position in its staking-designated wallet. Whether it gets delegated (multi-week lockup, bullish) or routed to hot wallets (distribution, bearish) is now the single highest-signal thing to watch on the network.",
   "top_recommendation":"Track the Binance Staking custody wallet (erd1rf4hv70) weekly against the protocol staked module. A jump in the staked module matching a drawdown here = delegation (bullish). A drawdown here matching hot-wallet inflows = pending distribution (bearish). This wallet is now the clearest single forward indicator.",
   "recommendations_for_next_run":[
     "Watch Binance Staking custody (3.38M): delegated (staked module jumps) vs moved to hot wallets (sell). Highest-signal indicator.",
     "Track ZoidPay (ZPAY): does the +59% / 40% DEX-share hold or revert? If sustained 2 weeks, a genuine second active DEX market. Look for a catalyst (listing, announcement).",
     "Verify yield-chase week 5: still rotating within the 0%-fee cohort? procryptostaking + valuestaking now lead.",
     "Monitor erd12tq6ax5k as the candidate upstream funder of OTC source erd17l22; query its inbound/outbound.",
     "Newly-issued token detection (5th run carrying): implement decimals-aware /tokens supply diff AND try /transactions to ESDT system SC (erd1qqqq...llls8a5w6u) with function=issue filter.",
     "Fix token_supply_events: store raw integer supply in previous.json so next run can diff like-for-like.",
     "Expand AshSwap address set in known-addresses.json defi_ashswap with stableswap pool contracts (admin contracts return zero EGLD).",
     "Confirm exchange-flow direction: 2nd week of net outflow = off-exchange accumulation (bullish); reversal to inflow = renewed sell pressure.",
     "Apply OTC trace to any new top-100 whale with >5% WoW balance change (template from erd17l22)."]}}

json.dump(report,open(f"{REPO}/reports/2026-05-25.json","w"),indent=2)
print("WROTE reports/2026-05-25.json")
print("exec_summary:",len(executive_summary),"large_tx:",len(large_transactions),"wallet_changes:",len(wallet_changes),
      "providers:",len(provs),"anomalies:",len(anomalies),"watch:",len(watch_list))
print("net exchange flow:",round(net_total,1),"total_locked:",round(total_locked,1),"apr_w:",round(apr_w,3))
print("DEFI: Hatom Lending USD",round(hatom_lending),"LSD",round(hatom_lsd),"USH",round(hatom_ush),"XOXNO LSD",round(xoxno_lsd))
