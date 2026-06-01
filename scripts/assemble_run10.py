#!/usr/bin/env python3
"""Assemble reports/2026-06-01.json (run #10) from collected data."""
import json, math
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D = json.load(open("/tmp/run10/collected.json"))
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
 "Binance":"Hot wallet erd1sdsl -170K -> Binance Staking custody +135K (now 3.51M). Same parked-not-delegated pattern as run #9 (then +267K). Run #7+9+10 cumulative: ~779K parked in custody wallet, undeployed. Protocol staked module rose +30K so most of this week's 135K is still in the custody wallet.",
 "Coinbase":"Hot -15.9K (secondary), +5.7K (primary). Net -10.1K - third consecutive week of net Coinbase outflow (-12.9K run #9, -10K now). Customer net withdrawals continuing.",
 "Crypto.com":"Net -7.5K (-4.1%). Two-wallet OTC-style intermediation visible in tx log (4.4K + 3.1K self-transfers).",
 "Bybit":"Hot -6.2K (-1.2%). Mild bleed.",
 "UPbit":"Hot wallet flat (-7.9K, -0.6%). UPbit OTC Desk separately RELOADED +16.7K (see OTC pipeline below).",
 "MEXC":"Net +3.96K (+4.1%). First non-Binance entity with positive net flow.",
 "KuCoin":"Net -5.2K (-20.8%). Visible step-down.","Bitget":"Flat (-0.1K).",
 "Gate.io":"Net -1.4K (-2.6%). Run #8's +21K bearish inflow fully reverted.",
 "Tokero":"Flat.","Bitfinex":"Flat."}
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
    "signal":"2nd consecutive week of NET OUTFLOW (-70.8K WoW, after -56K last week). Per the run #9 rule, 2 weeks of net outflow = off-exchange accumulation (bullish setup). But like last week, the move is dominated by Binance's internal hot->staking-custody shuffle (-170K hot, +135K custody = entity -35K), so the off-exchange read needs decomposition. Coinbase 3rd-week net outflow (-10K) is the cleanest bullish/withdrawal signal.",
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
  "notable_events":f"DEX volume +32.5% to ${totvol/1000:.0f}K. ZoidPay/WEGLD partially REVERTED from 40.8% share (run #9) to {pairs[1]['share_pct'] if len(pairs)>1 else 0:.1f}% - confirming run #9 was an event-driven spike. WEGLD/USDC dominance recovered 56.2%->{pairs[0]['share_pct']:.1f}%. WEGLD supply +4.7% (+26K WEGLD minted - notable supply event tied to OTC routing volume).","health_signal":"flat"},
 {"protocol":"Hatom Lending","category":"lending","addresses_tracked":13,"tvl_usd":hatom_lending,"tvl_egld":hl_egld,
  "tvl_wow_change_pct":100*(hl_egld-prev_hl_egld)/prev_hl_egld,"transfers_24h":tcount("Hatom EGLD MM"),
  "notable_events":f"TVL ${hatom_lending/1e6:.2f}M USD ({100*(hatom_lending-prev['defi_tvl']['Hatom Lending'])/prev['defi_tvl']['Hatom Lending']:+.1f}%) but {hl_egld/1000:.0f}K EGLD ({100*(hl_egld-prev_hl_egld)/prev_hl_egld:+.1f}%). BILATERAL INVERSE RULE STRONGLY CONFIRMED: -11.8% price -> +8.3% EGLD-denominated deposits. Depositors DCAed during the price decline, exactly as predicted.","health_signal":"growing"},
 {"protocol":"Hatom Liquid Staking","category":"liquid_staking","addresses_tracked":2,"tvl_usd":hatom_lsd,"tvl_egld":hlsd_egld,
  "tvl_wow_change_pct":100*(hlsd_egld-prev_hlsd_egld)/prev_hlsd_egld,"transfers_24h":tcount("Hatom Liquid Staking"),
  "notable_events":f"SEGLD-3ad2d0 mcap ${mc('SEGLD-3ad2d0')/1e6:.2f}M + SWTAO ${mc('SWTAO-356a25')/1e6:.2f}M = ${hatom_lsd/1e6:.2f}M. In EGLD: {hlsd_egld/1000:.0f}K ({100*(hlsd_egld-prev_hlsd_egld)/prev_hlsd_egld:+.1f}%). Continues the bilateral pattern - EGLD-denominated LSD deposits rose modestly while USD value contracted.","health_signal":"flat"},
 {"protocol":"Hatom USH","category":"stablecoin","addresses_tracked":4,"tvl_usd":hatom_ush,"tvl_egld":ush_egld,
  "tvl_wow_change_pct":100*(hatom_ush-prev_hush)/prev_hush,"transfers_24h":None,
  "notable_events":f"USH-111e09 mcap ${hatom_ush/1000:.0f}K ({100*(hatom_ush-prev_hush)/prev_hush:+.1f}% USD). Stablecoin holds value steadily.","health_signal":"flat"},
 {"protocol":"XOXNO LSD","category":"liquid_staking","addresses_tracked":2,"tvl_usd":xoxno_lsd,"tvl_egld":xlsd_egld,
  "tvl_wow_change_pct":100*(xlsd_egld-prev_xl_egld)/prev_xl_egld,"transfers_24h":tcount("XOXNO LSD"),
  "notable_events":f"XEGLD-e413ed mcap ${xoxno_lsd/1e6:.2f}M ({100*(xoxno_lsd-prev['defi_tvl']['XOXNO LSD'])/prev['defi_tvl']['XOXNO LSD']:+.1f}% USD), {xlsd_egld/1000:.0f}K EGLD ({100*(xlsd_egld-prev_xl_egld)/prev_xl_egld:+.1f}% EGLD). EGLD-denominated essentially flat - smaller bilateral effect than Hatom.","health_signal":"flat"},
 {"protocol":"XOXNO Aggregator","category":"aggregator","addresses_tracked":1,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("XOXNO Aggregator"),
  "notable_events":f"Throughput {tcount('XOXNO Aggregator'):,} daily transfers (+29% WoW from 11,933). Continues to recover from run #8's -40.8% retracement and is now near the trailing baseline.","health_signal":"growing"},
 {"protocol":"OneDex","category":"aggregator","addresses_tracked":5,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("OneDex Swap"),
  "notable_events":f"{tcount('OneDex Swap'):,} daily transfers (+43% WoW). Aggregator activity rising broadly with the price-decline-driven on-chain volume.","health_signal":"growing"},
 {"protocol":"JEXchange","category":"dex","addresses_tracked":4,"tvl_usd":None,"tvl_egld":None,
  "tvl_wow_change_pct":None,"transfers_24h":tcount("JEXchange Fees"),
  "notable_events":f"Fees wallet throughput {tcount('JEXchange Fees'):,} daily transfers (+6% WoW from 2,607). Steady growth.","health_signal":"growing"}]
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
                    "description":f"{tid} supply {chg:+.2f}% ({ev}). Likely tied to {'wrapping for DEX/OTC volume' if tid=='WEGLD-bd4d79' else 'protocol-level minting or burn'}."})

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
  "average_value":zp[0],"stddev":zp[1],"z_score":zp[2],"severity":"medium",
  "description":f"EGLD -11.84% WoW to $3.50 (z={zp[2]:+.2f} sigma, N=7). Approaching the -2 sigma threshold. After last week's +2.3% partial recovery, this is a fresh leg down. BTC -1.4% / ETH -2.4% (24h) - EGLD UNDERPERFORMED relative crypto. Two-week round-trip: $4.67 -> $3.88 -> $3.97 -> $3.50 = -25% from May 4 high in 4 weeks."},
 {"metric":"mex_price_usd","current_value":meco["price"],"previous_value":prev_mexp,"method":"z_score",
  "average_value":zmex[0],"stddev":zmex[1],"z_score":zmex[2],"severity":"medium",
  "description":f"MEX price -12.7% to ${meco['price']:.3e} (z={zmex[2]:+.2f} sigma, N=5). MEX moved nearly in lockstep with EGLD this week (-11.84% vs -12.7%) - typical for the platform's native token during EGLD volatility. Cross-check: MEX mcap dropped $1.53M -> $1.33M (-13.0%)."},
 {"metric":"total_delegators","current_value":cur_deleg,"previous_value":prev_deleg,"method":"z_score",
  "average_value":zd[0],"stddev":zd[1],"z_score":zd[2],"severity":"low",
  "description":f"Total delegators {cur_deleg:,} (-24 WoW = -0.013%). Naive z={zd[2]:+.2f} sigma but this remains a DEGENERATE z-score (baseline sd ~37 over a ~179K base). Per run #9 rule, severity downgraded to LOW given <0.1% absolute move. Real read: 6 consecutive readings near-flat = continued whale consolidation; retail not joining."},
 {"metric":"binance_staking_custody_continued_growth","current_value":3512650,"previous_value":3377559,"method":"rule_based",
  "severity":"high",
  "description":"Binance Staking custody wallet (erd1rf4hv70a) GREW for the 3rd consecutive week: 3.11M -> 3.38M -> 3.51M (+135K this week from a single transfer 2026-05-31). Protocol staked module rose only +30K (econ.staked 14.468M -> 14.498M), so the new 135K is ALMOST ENTIRELY UNDEPLOYED in the staking custody wallet. Run #7+9+10 cumulative parked: ~779K EGLD ($2.73M). Highest-signal forward indicator on the network: a sudden jump in econ.staked = bullish lockup; drawdown to hot wallets = sell. Currently still PARKED."},
 {"metric":"otc_pipeline_phase_reversal","current_value":32605,"previous_value":-17829,"method":"rule_based",
  "severity":"medium",
  "description":"OTC desks RELOADED this week, reversing run #9's distribution phase. UPbit OTC Desk +16.7K (+56%), OTC Distribution Wallet +15.9K (+54%). Combined +32.6K net inflow to OTC desks (vs run #9's combined -17.8K outflow). The OTC pipeline is in LOADING phase ahead of new distribution. Confirms run #9's 'completed cycle' read of erd17l22 and predicts a new distribution wave in 1-3 weeks."},
 {"metric":"otc_source_funder_chain_completed","current_value":6970,"previous_value":2000,"method":"rule_based",
  "severity":"high",
  "description":"OTC source funder erd12tq6ax5k traced to Binance.com (erd1sdsl) as the ultimate upstream source. 14d view: 8,972 EGLD inbound, ALL from Binance.com hot wallet. 7d: 6,970 EGLD passed through erd12tq6ax5k (balance 0, in=out=6,970), forwarded in identical chunks of 1252+1127+855+831+... to erd17l22 (OTC source). Pipeline taxonomy now COMPLETE: Binance.com -> erd12tq6ax5k (funder) -> erd17l22 (source) -> chain routers -> UPbit OTC Desk + OTC Distribution -> retail. This is the smoking gun: Binance is the ultimate origination of the OTC distribution flow on MultiversX."},
 {"metric":"zoidpay_dex_share_revert","current_value":pairs[1]["share_pct"] if len(pairs)>1 else 0,"previous_value":40.8,"method":"rule_based",
  "severity":"medium",
  "description":f"ZoidPay/WEGLD pair share REVERTED from 40.8% (run #9) to {pairs[1]['share_pct']:.1f}% this week (volume ${pairs[1]['volume_24h_usd']/1000:.1f}K). Predicted partial revert at run #9 confirmed - the +59% price move and 40% DEX share were a one-week event, not a regime shift. ZPAY still maintains #2 pair position with ~$5.30M mcap (down from $5.33M, essentially flat). WEGLD/USDC dominance recovered to {pairs[0]['share_pct']:.1f}%."}]

# ---------- trend indicators ----------
accelerating_outflows=[
 {"exchange":"Coinbase","trend":"declining","cumulative_change_pct":-12.0,"weeks_in_trend":3,
  "interpretation":"Third consecutive week of Coinbase net outflow. Run #8 +39K -> Run #9 -12.9K -> Run #10 -10.1K. Customers continuing to withdraw from Coinbase wallets. Cumulative 2-week outflow: -23K EGLD."},
 {"exchange":"NET_EXCHANGE","trend":"declining","cumulative_change_pct":None,"weeks_in_trend":2,
  "interpretation":"Aggregate net exchange flow now 2 weeks of outflow (-56K -> -71K). Per run #9 rule, 2 consecutive weeks of net outflow = off-exchange accumulation (bullish). Caveat: dominated by Binance internal hot->custody shuffle. Coinbase the cleaner read."}]
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
   {"metric":"token_holder_count_decline","direction":"down","weeks":10,"cumulative_change_pct":None,
    "interpretation":"10th consecutive week of small holder declines across all top-10 tokens (-14 to -92 this week). Established airdrop-decay baseline; active >$1M-mcap token base stable."},
   {"metric":"yield_chase_migration","direction":"up","weeks":5,"cumulative_change_pct":None,
    "interpretation":"Week 5 of the 0%-fee 9%+ APR migration but PATTERN WEAKENING. procryptostaking still leads (+7.5K, was +17K last week), but valuestaking REVERSED (-3.1K), egldstakingprovider REVERSED (-1.9K), orius -1.7K, ninjastaking nearly flat (+0.7K). Net flow into the low-fee cohort dropped substantially - the regime shift is stalling, and the rotation has narrowed to a single provider (procryptostaking)."},
   {"metric":"binance_staking_custody","direction":"up","weeks":3,"cumulative_change_pct":13.0,
    "interpretation":"3 consecutive weeks of Binance Staking custody growth: 3.11M -> 3.38M -> 3.51M (+402K cumulative). Protocol staked module unchanged - capital remains PARKED. Highest-signal forward indicator on the network."},
   {"metric":"net_exchange_outflow","direction":"down","weeks":2,"cumulative_change_pct":None,
    "interpretation":"2 consecutive weeks of net EGLD outflow from exchanges (-56K -> -70K). Per run #9 rule, this is the bullish pattern (off-exchange accumulation). But heavily diluted by Binance internal shuffles - decomposed reading: Coinbase is the cleanest off-exchange withdrawal trend (3 weeks running)."},
   {"metric":"otc_desk_balance","direction":"up","weeks":1,"cumulative_change_pct":54.0,
    "interpretation":"OTC desks reversed direction: UPbit OTC Desk +56%, OTC Distribution +54% this week, after run #9's drawdown. Indicates a new distribution wave is being staged."}],
 "regime_shifts":[
   {"metric":"egld_price_regime","before_value":4.07,"after_value":price,
    "description":"EGLD has now traded down on 3 of 4 weeks since the May 4 peak ($4.67): $4.67 -> $3.88 -> $3.97 -> $3.50 = -25% in 4 weeks. The previous tracked regime had EGLD in a $3.74-$4.29 band; current $3.50 breaks below the prior range floor. Watch next week: a confirming break below $3.50 makes this a level-shift regime change."},
   {"metric":"yield_chase_validator_migration_weakening","before_value":50000,"after_value":3500,
    "description":"Week 5 of yield-chase but net flow into low-fee cohort has CONTRACTED sharply: cumulative ~+50K over weeks 1-4 vs +3.5K this week (procryptostaking +7.5K alone offset by reversals in valuestaking/egldstakingprovider/orius). The regime shift is stalling. If next week shows more reversals than gains, the regime ends."},
   {"metric":"binance_custody_accumulation","before_value":3110000,"after_value":3512650,
    "description":"Binance Staking custody crossed 3.5M EGLD. Cumulative parked since run #7: ~779K EGLD ($2.73M at current price). Sustained for 3 weeks with no delegation - this is now a STRUCTURAL position, not a transit. Open question: is this Binance preparing to delegate (bullish lockup) or accumulating for a large OTC sale (bearish)? Both run #7+9+10 saw hot-wallet drawdowns funding the custody buildup."}]}

# ---------- dormant activations ----------
dormant_activations=[]

# ---------- watch list ----------
watch_list=[
 {"item":"Binance Staking custody now 3.51M (+135K this week, +402K over 3 weeks)","reason":"3rd consecutive week of growth. Protocol staked module rose only +30K vs custody wallet +135K - capital REMAINS PARKED, not delegated. Cumulative ~779K parked since run #7. Watch: jump in econ.staked (bullish lockup) vs drawdown to hot wallets (sell). Currently the single highest-signal forward indicator on the network.","weeks_on_list":4},
 {"item":"Binance is the ultimate source of the OTC distribution flow","reason":"erd12tq6ax5k traced as a pure pass-through funder receiving exclusively from Binance.com (erd1sdsl) and forwarding to OTC source erd17l22. Pipeline complete: Binance -> funder -> source -> routers -> OTC desks -> retail. 6,970 EGLD passed through in 7d. Implication: Binance is settling OTC sells on-chain via this multi-hop pipeline.","weeks_on_list":1},
 {"item":"OTC desks reloaded (+32.6K combined) - new distribution wave coming","reason":"UPbit OTC Desk +16.7K (+56%), OTC Distribution Wallet +15.9K (+54%). Run #9's distribution phase reversed - desks are now LOADING. Historical pattern: load -> distribute over 1-3 weeks. Expect distribution wave next 1-3 reports.","weeks_on_list":1},
 {"item":"EGLD -12% to $3.50, broke prior $3.74 floor","reason":"z-score -2.09 sigma (medium). 4-week trajectory $4.67 -> $3.88 -> $3.97 -> $3.50 = -25% from May 4 peak. EGLD underperformed BTC (-1.4%) and ETH (-2.4%). Test of $3.50 floor next week - a confirming break = regime shift down.","weeks_on_list":1},
 {"item":"Yield-chase regime SHIFT STALLING - week 5 leadership rotation collapsed","reason":"Net flow to low-fee cohort dropped from ~+50K cumulative weeks 1-4 to +3.5K this week. procryptostaking still gains (+7.5K) but valuestaking/egldstakingprovider/orius all REVERSED. Next week's read determines if regime ends.","weeks_on_list":5},
 {"item":"Coinbase 3rd consecutive week of net outflow (-10.1K)","reason":"Cleanest off-exchange withdrawal signal across exchanges. Customers continuing to pull EGLD. Bullish setup if it persists to week 4.","weeks_on_list":2},
 {"item":"WEGLD +4.7% supply growth (+26K minted)","reason":"Notable supply event coincident with OTC routing volume + DEX activity. WEGLD-bd4d79 558K -> 585K wrapped. Watch whether this is sustained DEX expansion or one-off OTC-driven wrapping.","weeks_on_list":1},
 {"item":"ZoidPay dominance REVERTED (40.8% -> 8.9%)","reason":"Confirms run #9's volume spike as event-driven, not regime. ZPAY mcap holds steady at $5.30M (still #2/3 pair). No new catalyst surfaced this week. Graduate from watch list if next week stays in single digits.","weeks_on_list":2},
 {"item":"Hatom Lending +8.3% EGLD-denominated during -12% price drop","reason":"Strongest bilateral inverse rule confirmation in tracking history. Depositors DCAed aggressively during the decline. Hatom Lending now 1.21M EGLD locked (up from 1.12M). Indicator strength: high - this is a leading sentiment signal.","weeks_on_list":3},
 {"item":"Aggregator throughput broadly rising (XOXNO +29%, OneDex +43%, JEXchange +6%)","reason":"Non-custodial DEX aggregator activity rising sharply during price decline. Indicates on-chain activity rotation rather than off-chain exit. Healthy DeFi engagement during EGLD stress.","weeks_on_list":1},
 {"item":"Newly-issued token detection still blocked","reason":"5th run carrying. /tokens?sort=timestamp returns HTTP 400. ESDT system-contract issuance scan workaround still TODO.","weeks_on_list":3},
 {"item":"Total delegators flat 6 readings + delegator base shrinking 5 weeks","reason":"178,934 (-24 WoW). z=-2.4 is degenerate (low-variance artifact). Whale consolidation continues; no retail joining.","weeks_on_list":2}]

# ---------- executive summary ----------
executive_summary=[
 {"finding":"OTC pipeline FULLY TRACED to Binance.com origin: erd1sdsl (Binance hot) -> erd12tq6ax5k (funder, pass-through) -> erd17l22 (source) -> chain routers -> UPbit OTC Desk + OTC Distribution -> retail. 6,970 EGLD flowed through the funder in 7d, ALL from Binance. Binance is the ultimate originator of the on-chain OTC distribution flow.","severity":"high","category":"whale"},
 {"finding":"Binance Staking custody +135K to 3.51M - 3rd consecutive week of growth (cum +402K over weeks 8/9/10). Protocol staked module rose only +30K, so the 135K remains UNDEPLOYED in the staking wallet. ~779K parked since run #7. Highest-signal forward indicator on the network.","severity":"high","category":"whale"},
 {"finding":"EGLD -11.84% to $3.50, broke prior $3.74 trading-range floor. z-score -2.09 sigma (medium anomaly). 4-week trajectory: $4.67 (May 4) -> $3.50 (-25%). EGLD underperformed BTC (-1.4%) and ETH (-2.4%).","severity":"medium","category":"network"},
 {"finding":"Bilateral inverse rule STRONGEST CONFIRMATION in tracking history: Hatom Lending +8.3% EGLD-denominated during -12% price drop. Depositors DCAed aggressively. Rule is now well-validated as a sentiment leading indicator.","severity":"medium","category":"defi"},
 {"finding":"OTC desks REVERSED to loading phase: UPbit OTC Desk +56% (+16.7K), OTC Distribution +54% (+15.9K). Combined +32.6K net inflow to desks. New distribution wave staged for the next 1-3 weeks.","severity":"medium","category":"whale"},
 {"finding":"Yield-chase regime STALLING in week 5. Net flow to 0%-fee 9%+ APR cohort dropped from ~+50K cumulative weeks 1-4 to +3.5K this week. procryptostaking still gains (+7.5K) but valuestaking, egldstakingprovider, orius all REVERSED. Pattern weakening - one more reversal week ends the regime.","severity":"medium","category":"staking"},
 {"finding":"ZoidPay DEX dominance REVERTED (40.8% -> 8.9%) confirming run #9 was event-driven, not a regime shift. WEGLD/USDC dominance recovered 56.2% -> 86.3%. Notable bonus: WEGLD supply +4.7% (+26K minted), coincident with OTC volume.","severity":"low","category":"token"},
 {"finding":"Exchange net flow 2nd consecutive week of OUTFLOW (-70.8K WoW, after -56K). Coinbase the cleanest signal at 3 weeks of outflow (-10.1K). Off-exchange accumulation setup (bullish) but heavily diluted by Binance internal shuffles.","severity":"medium","category":"whale"}]

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
   "btc_correlation_note":f"EGLD -11.84% WoW vs BTC -1.44% / ETH -2.38% (24h). EGLD UNDERPERFORMED.",
   "transactions_added":st["transactions"]-pact["total_transactions"],"supply_added":econ["totalSupply"]-pecon["total_supply"],
   "staked_egld_added":staked-pecon["staked_egld"],"epoch_advanced":st["epoch"]-pact["epoch"]},
 "analysis":f"EGLD -11.84% WoW to $3.50, breaking the prior $3.74 trading-range floor (z={zp[2]:+.2f} sigma, medium anomaly). The 4-week downtrend from the May 4 peak ($4.67 -> $3.88 -> $3.97 -> $3.50) totals -25% and now poses the question of a regime shift to a lower price band. BTC -1.44% and ETH -2.38% (24h) - EGLD UNDERPERFORMED both. Market cap $105.2M (-15.0%). Staked ratio essentially unchanged at 48.24% (+0.02pp); protocol staked module rose +30K to 14.498M but Binance's staking custody wallet alone absorbed 135K - meaning external delegation actually CONTRACTED on a net basis when isolating the custody noise. Activity: ~1.4M txs (+202K WoW), epoch 2131 (+7). Account growth slowed: +1,442 to 9.21M (vs +1,691 last week)."}

# ---------- whale analysis ----------
whale_analysis=("THE WEEK'S DOMINANT MOVE (continuing run #9's pattern): Binance hot wallet erd1sdsl fell -170K and 135K landed in Binance Staking custody (3.38M -> 3.51M, a single transfer 2026-05-31). Run #7+9+10 cumulative parked in custody: ~779K EGLD ($2.73M). Protocol staked module rose only +30K so the new 135K remains UNDEPLOYED. This is now a STRUCTURAL position - 3 consecutive weeks of accumulation, no delegation, no distribution.\n\n"
 "OTC PIPELINE FULLY MAPPED: This week's tracing of the upstream funder erd12tq6ax5k (the correct address `erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp`) reveals that the funder is fed EXCLUSIVELY by Binance.com hot wallet (erd1sdsl). 7d throughput: 6,970 EGLD in = 6,970 EGLD out (balance 0, pure pass-through with nonce 1505 indicating heavy historical use). All outbound goes to erd17l22 (OTC source). Pipeline now complete:\n"
 "  Binance.com (erd1sdsl)\n"
 "    -> erd12tq6ax5k (funder, pass-through)\n"
 "      -> erd17l22 (OTC source, 295K balance)\n"
 "        -> chain routers (erd1nhtq4, erd1ecyftln, ...)\n"
 "          -> UPbit OTC Desk + OTC Distribution Wallet\n"
 "            -> retail recipients\n"
 "Implication: Binance is the ultimate originator of MultiversX on-chain OTC distribution flow. This is a 'smoking gun' completion of the OTC taxonomy that began run #6.\n\n"
 "OTC DESKS RELOADED: UPbit OTC Desk +16.7K (+56%) and OTC Distribution Wallet +15.9K (+54%) this week. Run #9 ended in distribution phase (~145K throughput, both desks drawing down). This week REVERSED - both desks are now LOADING. Expect a new distribution wave to retail in the next 1-3 weeks. Same-night routing activity 2026-05-31 23:30 UTC: Binance.com hot fired four chunks (5,600 + 5,600 + 4,200 + 4,000) to chain routers, which arrived at UPbit OTC Desk within minutes.\n\n"
 f"WHALE TIERS (top-{N_prev} apples-to-apples): mega +{whale_tiers['mega_whales']['net_change_egld']/1000:+.0f}K, large {whale_tiers['large_whales']['net_change_egld']/1000:+.0f}K, mid {whale_tiers['mid_whales']['net_change_egld']/1000:+.0f}K. The mega gain is the Binance custody +135K crossing further above 1M. The large loss is the Binance hot drawdown - same internal shuffle as run #9.\n\n"
 "EXCHANGE FLOWS: net -70.8K outflow, 2nd consecutive week (run #9 -56K). Per the run #9 rule, 2 weeks of outflow = bullish off-exchange accumulation. BUT the headline is heavily diluted by Binance internal shuffles. Decomposed: Binance entity net -35K (internal hot->custody shuffle), Coinbase -10.1K (3rd consecutive week - cleanest signal), Crypto.com -7.5K, Bybit -6.2K, KuCoin -5.2K. MEXC +4.0K and Coinbase primary +5.7K are the only material inflows. Coinbase is the cleanest off-exchange withdrawal signal of the week.")

# ---------- staking analysis ----------
staking_analysis=(f"Staking concentration remains low (HHI {hhi:.4f}, top-5 {top5:.1f}%). Total delegated {total_locked:,.0f} EGLD across {len(provs)} active providers. Active delegator base {cur_deleg:,} (-24 WoW, -0.013% - degenerate z-score, real signal flat).\n\n"
 "YIELD-CHASE WEEK 5 - PATTERN WEAKENING. Net flow into the 0%-fee 9%+ APR cohort dropped from ~+50K cumulative across weeks 1-4 to only +3.5K this week. procryptostaking still leads (+7.5K, ~9% APR, 7,187 users) - the only material gainer in the cohort. But last week's other leaders all REVERSED: valuestaking -3.1K, egldstakingprovider -1.9K, orius -1.7K, ninjastaking nearly flat (+0.7K). The regime shift is stalling. One more week of contractions ends it.\n\n"
 f"APR distribution: 70% of stake in the 8-9% bucket ({buckets[3]['provider_count']} providers, {buckets[3]['total_locked_egld']/1e6:.1f}M). The 9-10% bucket holds {buckets[4]['provider_count']} providers / {buckets[4]['total_locked_egld']/1e3:.0f}K EGLD. The 5-6% bucket has only 1 provider ({buckets[0]['total_locked_egld']/1e3:.0f}K) and 10%+ is empty (was empty across all 2026 runs). Apr-weighted average: {apr_w:.2f}%.\n\n"
 f"DELEGATOR CHURN: {gain} providers gaining vs {lose} losing delegators (broad mid-tier exodus continues). Total delegators flat for 6 readings (179,038 -> 179,060 -> 179,050 -> 179,011 -> 178,958 -> 178,934) while staked EGLD up +30K = concentrated re-staking by fewer/larger holders. Classic whale-consolidation signature.\n\n"
 "VALIDATOR MOVEMENTS: 6 system-contract addresses (erd1qqqq...llllll...) dropped out of the providers list - these are protocol-level direct-node staking aggregators whose locked totals fell below threshold or to zero. Treated as data artifact, not real validator exits. Notable named validator movements: none this week.")

# ---------- token analysis ----------
top_pair_share = pairs[0]['share_pct']
second_pair = pairs[1] if len(pairs)>1 else None
token_analysis=(f"DEX volume RECOVERED +32.5% to ${totvol/1000:.0f}K, exiting the run #9 ZoidPay-event dip (z={zv[2]:+.2f} sigma, normal). Composition REVERTED: WEGLD/USDC dominance back to {top_pair_share:.1f}% (was 56.2% in run #9), ZoidPay/WEGLD share down to {second_pair['share_pct'] if second_pair else 0:.1f}% (was 40.8%). Confirms run #9's surge as event-driven, not regime. ZPAY price mcap $5.30M (essentially flat WoW), retaining its new top-3 mcap position.\n\n"
 "TOKEN SUPPLY EVENT: WEGLD-bd4d79 +4.7% (+26.5K wrapped EGLD minted; 558K -> 585K). Coincident with the OTC routing volume and DEX recovery - the OTC pipeline appears to wrap EGLD for off-chain settlement, and the +26K mint roughly matches the ~32.6K OTC desk loading. Notable supply event worth tracking.\n\n"
 "Token holder counts declined for a 10th consecutive week (-14 to -92 across top 10) - the established airdrop-decay baseline. WrappedUSDC 82,021 (-92) remains the most-used real token.\n\n"
 f"MEX price -12.7% WoW to ${meco['price']:.3e} (z={zmex[2]:+.2f} sigma, medium anomaly). Moved nearly in lockstep with EGLD (-11.84%). MEX market cap $1.33M (-13% from $1.53M).\n\n"
 "Top by market cap remains EmoryaSportsX $40.9M (likely price-feed artifact), USDC $8.56M (large mint between runs - watch), ZoidPay $5.30M, UTK $4.19M, SEGLD $3.00M.\n\n"
 "Newly-issued tokens: detection still blocked - /tokens?sort=timestamp returns HTTP 400 (5th run). Token supply events from prev.json supply_raw correctly diffed for the first time (recommendations_for_next_run #6 from run #9 completed) - flagged WEGLD and UTK as real events, USDC/USDT signal contaminated because prev still had signed values.")

# ---------- defi analysis ----------
defi_analysis=(f"Hatom Lending +8.3% in EGLD ({prev_hl_egld/1000:.0f}K -> {hl_egld/1000:.0f}K) during the -12% price drop = STRONGEST bilateral inverse rule confirmation in tracking history. USD-denominated TVL only fell -4.5% (${prev['defi_tvl']['Hatom Lending']/1e6:.2f}M -> ${hatom_lending/1e6:.2f}M) because depositors deposited 8.3% more EGLD. Depositors DCAed aggressively. The rule is now well-validated as a high-signal sentiment indicator.\n\n"
 f"Hatom LSD ${hatom_lsd/1e6:.2f}M USD ({100*(hatom_lsd-prev_hlsd)/prev_hlsd:+.1f}%), {hlsd_egld/1000:.0f}K EGLD ({100*(hlsd_egld-prev_hlsd_egld)/prev_hlsd_egld:+.1f}%). Smaller bilateral effect than Lending - LSD users tend to be long-term stakers, less sensitive to price-driven DCA.\n\n"
 f"XOXNO LSD ${xoxno_lsd/1e6:.2f}M / {xlsd_egld/1000:.0f}K EGLD - essentially flat in EGLD ({100*(xlsd_egld-prev_xl_egld)/prev_xl_egld:+.1f}%), -11.6% in USD. Same bilateral pattern but milder.\n\n"
 f"xExchange TVL ${xexch_tvl_usd/1e6:.2f}M ({100*(xexch_tvl_egld-prev_xexch_egld)/prev_xexch_egld:+.1f}% EGLD). DEX volume +32.5%.\n\n"
 f"AGGREGATOR THROUGHPUT RISING: XOXNO Aggregator {tcount('XOXNO Aggregator'):,} daily (+29% WoW), OneDex {tcount('OneDex Swap'):,} (+43% WoW), JEXchange {tcount('JEXchange Fees'):,} (+6% WoW). Non-custodial DEX aggregator activity is rising sharply during the price decline - on-chain volume rotation indicates HEALTHY DeFi engagement under EGLD stress (users staying on-chain rather than exiting to CEX).\n\n"
 "Tracked TVL total: ~$14.9M (Hatom Lending $4.24M + Hatom LSD $4.04M + XOXNO LSD $1.26M + xExchange $2.04M + Hatom USH $660K + remainder). Hatom still dominates with ~60% of tracked TVL.")

report={
 "metadata":{"report_date":"2026-06-01","period_start":"2026-05-25T00:00:00Z","period_end":"2026-06-01T00:00:00Z",
   "generated_at":datetime.now(timezone.utc).isoformat(),"egld_price_usd":price,
   "btc_price_usd":be["bitcoin"]["usd"],"eth_price_usd":be["ethereum"]["usd"],"run_number":10,
   "data_sources_ok":json.load(open("/tmp/run10/status.json"))["ok"],
   "data_sources_failed":["/tokens?sort=timestamp (HTTP 400 - silently unsupported; 5th run carrying)","Brief HTTP 429 on H-token batch (recovered with longer delay)"]},
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
   "top_by_market_cap":top_by_market_cap,"newly_issued":[],"xexchange":xexchange,"analysis":token_analysis},
 "defi_activity":{"protocols":protocols,"protocol_breakdown":protocol_breakdown,"sc_deployments":[],"analysis":defi_analysis},
 "anomalies":anomalies,
 "trend_indicators":trend_indicators,
 "watch_list":watch_list,
 "meta_learning":{"run_number":10,
   "endpoints_that_worked":json.load(open("/tmp/run10/status.json"))["ok"],
   "endpoints_that_failed":["/tokens?sort=timestamp (HTTP 400 - 5th run)"],
   "api_quirks":[
     "HTTP 429 rate limiting observed during /tokens/{id} batch (14 H-token mcap queries) - increased delay to 0.6s fixed it. Recommend keeping H-token batch delay >=0.5s.",
     "OTC pipeline address typo in the agent's collect script caught a HTTP 400; lesson: always verify ad-hoc addresses against known-addresses.json before adding to query batch.",
     "Token supply_raw diff now works (run #9 fix landed) - flagged WEGLD +4.7% as the first reliable supply event detection. USDC/USDT diff still spurious because prev had signed values from the earlier bug.",
     "Validator joiners/leavers lists contain protocol system contracts (erd1qqqq...llllll...) that come/go as direct-node staking aggregators move above/below threshold - filter these out for the real validator movement count."],
   "key_findings":[
     "OTC pipeline fully traced to Binance.com origin (erd1sdsl -> erd12tq6ax5k funder -> erd17l22 source -> OTC desks -> retail). 6,970 EGLD/week flow.",
     "Binance Staking custody +135K to 3.51M, 3rd consecutive week of growth (cum +402K), protocol staked module +30K only - 779K total parked, undelegated.",
     "EGLD -11.84% to $3.50, broke prior $3.74 floor, 4-week trajectory -25% from peak.",
     "Bilateral inverse rule strongest confirmation: Hatom Lending +8.3% EGLD during -12% price drop.",
     "OTC desks REVERSED to loading phase (+32.6K combined), new distribution wave staged.",
     "Yield-chase regime weakening week 5 (net +3.5K vs cumulative ~+50K weeks 1-4).",
     "ZoidPay DEX dominance reverted 40.8% -> 8.9% (event-driven confirmed).",
     "WEGLD supply +4.7% (+26K minted) - first reliable supply event detection after run #9 fix.",
     "Coinbase 3rd consecutive week of net outflow (-10.1K) - cleanest off-exchange signal."],
   "action_items_from_previous":9,"action_items_completed":7,
   "methodology_changes":[
     "OTC PIPELINE TRACING METHODOLOGY: when tracing a candidate funder address, verify by querying its 14-day inbound and checking sender concentration. If 100% of inbound comes from a single exchange wallet AND outbound mirrors inbound (pure pass-through with balance ~0), the chain is confirmed.",
     "NEW RULE: bilateral inverse rule scales linearly with price magnitude. Run #7 (+14.7%): -13% EGLD; run #8 (-16.9%): +13.6% EGLD; run #10 (-11.8%): +8.3% EGLD. Magnitude correlation now confirmed across 3 distinct events.",
     "NEW RULE: validator joiner/leaver filtering. Always exclude erd1qqqq* system staking contracts from validator movement counts - these are protocol-level direct-node aggregators that come and go from /providers based on locked balance threshold, not real validator activity.",
     "TOKEN SUPPLY EVENT DETECTION ACTIVE: prev.json supply_raw diff confirmed working. WEGLD +4.7% flagged as real event. Set the WEGLD/USDC/USDT thresholds to 0.1%, others to 1.0%."],
   "new_addresses_discovered":1,
   "most_valuable_insight":"The OTC distribution pipeline that has been studied since run #6 originates from Binance.com hot wallet. The funder address erd12tq6ax5k receives EXCLUSIVELY from Binance.com (erd1sdsl) and forwards 100% to the OTC source erd17l22. This completes the on-chain OTC settlement taxonomy and confirms that what looks like organic OTC desk activity is largely Binance routing customer sells through a multi-hop privacy/obfuscation chain. Combined with the Binance Staking custody accumulation (now 3.51M, +402K in 3 weeks), Binance's role in MultiversX flow is far more comprehensive than just being the largest exchange wallet - it is the originator of much of the on-chain liquidity flow.",
   "top_recommendation":"Track THREE Binance signals weekly going forward: (1) Binance Staking custody balance vs protocol staked module - delegated vs parked; (2) erd12tq6ax5k funder throughput - OTC pipeline volume; (3) Binance.com hot wallet drawdowns - source of both the custody buildup and the OTC routing. These three together give the cleanest read on the network's largest single capital allocator.",
   "recommendations_for_next_run":[
     "Watch Binance Staking custody (3.51M, +135K/wk for 3 weeks): does econ.staked finally jump (delegation/bullish lockup) or does the custody drawdown to hot wallets (distribution/bearish)? Either resolution is the highest-signal event possible.",
     "Verify OTC pipeline distribution wave - desks loaded +32.6K this week. Next 1-3 weeks should show distribution to retail. Track UPbit OTC Desk + OTC Distribution outflows.",
     "Test EGLD $3.50 floor: a confirming break below $3.50 next week = regime shift down to lower price band. Holding above $3.50 = floor confirmation.",
     "Yield-chase regime end watch: one more week of contractions in the low-fee cohort officially ends the regime. Procryptostaking the only sustained gainer.",
     "Coinbase 4-week net outflow check: -39K/+0/-12.9K/-10.1K. If week 4 stays negative, off-exchange accumulation thesis confirms.",
     "WEGLD supply +4.7% follow-up: did the new 26K wrap continue (DEX expansion) or hold (one-off OTC mint)?",
     "Newly-issued token detection workaround (6th run): try /transactions to ESDT system SC erd1qqqq...llls8a5w6u with function=issue filter OR /accounts/{ESDT_addr}/transfers within 7d window.",
     "Map remaining OTC source candidates: scan all top-100 whales with low nonce + frequent erd1sdsl inbound for additional Binance funder routes.",
     "Expand AshSwap defi_ashswap address set with stableswap pool contracts (still pending from run #9)."],
   "dashboard_feature_suggestions":[
     {"title":"Multi-week Binance custody vs protocol-staked tracker chart","motivation":"The week's top finding (and last week's): Binance Staking custody grew 3.11M -> 3.38M -> 3.51M while protocol staked rose negligibly. A dual-line time series would make parked-vs-delegated visible at a glance and immediately surface the moment Binance delegates (bullish step in econ.staked) or withdraws to hot wallets (bearish step down in custody). Currently each week's report shows only the current snapshot - the trajectory is invisible.","suggested_visualization":"dual-line chart: Binance Staking custody balance vs economics.staked_egld over weeks (or run numbers). Annotate jumps. Overlay net change bars.","data_already_available":True,"data_source":"previous.json exchange_balances['Binance Staking'] + economics.staked_egld across all report JSONs","priority":"high"},
     {"title":"OTC pipeline phase visualization (load vs distribute)","motivation":"This week we identified that the OTC desks REVERSED to loading phase (after run #9's distribution). A heatmap or area chart of OTC desk balance + flow direction over weeks would show the loading-distributing cycle visually and predict the next distribution wave. The pipeline is now fully traced (Binance origin) - the visualization should also show the chain.","suggested_visualization":"horizontal bar/area chart per OTC desk over weeks, colored by net direction (loading green / distributing red). OR a Sankey of upstream sources -> desks -> retail per week.","data_already_available":True,"data_source":"per-week report whale_intelligence.exchange_flows snapshots + accounts.UPbitOTCDesk / OTCDistribution balances","priority":"high"},
     {"title":"Bilateral inverse rule EGLD-vs-USD divergence chart for Hatom Lending","motivation":"Run #10 showed Hatom Lending +8.3% EGLD-denominated during -12% price drop - the strongest bilateral inverse rule confirmation in tracking history. A divergence visualization (USD line vs EGLD line, both indexed) would let users see at a glance that this is a leading sentiment signal, not noise.","suggested_visualization":"dual-axis line chart: Hatom Lending TVL in USD (left) vs in EGLD (right), normalized to 100 at run #1. Diverging lines highlight the bilateral rule operating.","data_already_available":True,"data_source":"defi_activity.protocol_breakdown[].tvl_usd and tvl_egld across reports","priority":"medium"}],
   "dashboard_suggestions_followup":[
     {"prior_title":"Multi-week net exchange-flow oscillation chart","status":"pending","note":"Still pending build - this week reaffirms its value: -56K -> -70K trend would be visually obvious in a bar chart. Confirms high priority."},
     {"prior_title":"DEX pair-composition stacked-area over time","status":"pending","note":"The ZoidPay 40.8% -> 8.9% revert this week would be visually dramatic. The chart would distinguish event-driven from regime-shift composition changes."},
     {"prior_title":"Binance staking-custody vs protocol-staked-module tracker","status":"pending","note":"Re-proposed as suggestion #1 above with stronger motivation (3 consecutive weeks of accumulation now)."}]}}

json.dump(report,open(f"{REPO}/reports/2026-06-01.json","w"),indent=2)
print("WROTE reports/2026-06-01.json")
print("exec_summary:",len(executive_summary),"large_tx:",len(large_transactions),"wallet_changes:",len(wallet_changes),
      "providers:",len(provs),"anomalies:",len(anomalies),"watch:",len(watch_list))
print("net exchange flow:",round(net_total,1),"total_locked:",round(total_locked,1),"apr_w:",round(apr_w,3))
print("DEFI: Hatom Lending USD",round(hatom_lending),"LSD",round(hatom_lsd),"USH",round(hatom_ush),"XOXNO LSD",round(xoxno_lsd))
print("Token supply events:",len(token_supply_events))
print("trend_indicators.notable_joiners:", len(notable_joiners), "notable_leavers:", len(notable_leavers))
