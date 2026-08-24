#!/usr/bin/env python3
"""Run #22 stage 1: compute every derived quantity -> /tmp/run22w/derived.json"""
import json, os, math
from datetime import datetime, timezone

REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
OUT="/tmp/run22w"; os.makedirs(OUT, exist_ok=True)
D=json.load(open(f"{REPO}/data/collected/2026-08-24.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
learn=json.load(open(f"{REPO}/data/learnings.json"))
beh=json.load(open(f"{REPO}/data/collected/delegator_behavior_2026-08-24.json"))
F=json.load(open(f"{REPO}/data/collected/followup_2026-08-24.json"))

label_map,cat_map={},{}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"):
                label_map[a]=m.get("name","Unknown"); cat_map[a]=m.get("category","unknown")
def lab(a): return label_map.get(a,"Unknown")
def cat(a): return cat_map.get(a,"unknown")

O={}
econ=D["economics"]; st=D["stats"]; pecon=prev["economics"]; pact=prev["activity"]
price=econ["price"]; staked=econ["staked"]; circ=econ["circulatingSupply"]
pp=pecon["egld_price_usd"]; be=D["btc_eth"]
O["macro"]={"price":price,"prev_price":pp,"price_chg":100*(price-pp)/pp,
    "btc":be["bitcoin"]["usd"],"eth":be["ethereum"]["usd"],
    "btc_wow":100*(be["bitcoin"]["usd"]-pecon["btc_price_usd"])/pecon["btc_price_usd"],
    "eth_wow":100*(be["ethereum"]["usd"]-pecon["eth_price_usd"])/pecon["eth_price_usd"],
    "staked":staked,"staked_prev":pecon["staked_egld"],"staked_chg":staked-pecon["staked_egld"],
    "sr":staked/circ,"sr_prev":pecon["staked_ratio"]}

acc=D["accounts"]
def bal_of(a):
    x=acc.get(a)
    if x and isinstance(x.get("info"),dict) and "balance" in x["info"]:
        try: return int(x["info"]["balance"])/1e18
        except: return None
    return None

UPBIT_DESK="erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
DIST_DESK="erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
DESK_SET={UPBIT_DESK,DIST_DESK}

vn=D["otc_hub_trace"]["venue_netting"]
desk_bal=(bal_of(UPBIT_DESK) or 0)+(bal_of(DIST_DESK) or 0)
prev_desk=38391.918355489026+22173.94614754873
# UPbit -> desk feed this week
upbit_feed=0.0
for a,rec in D["desk_inbound_paged"].items():
    for t in rec["txs"]:
        if cat(t.get("sender"))=="exchange" and "UPbit" in lab(t.get("sender")) and "OTC" not in lab(t.get("sender")):
            upbit_feed+=int(t.get("value","0"))/1e18

wave=D["otc_hub_trace_wave2ext"]["venue_netting"]
july=D["otc_hub_trace_julywave"]["venue_netting"]
weekly_nets={"run19":61435,"run20":188658,"run21":138265,"run22":vn["net_one_way"]}
sum_wave_weekly=188658+138265+vn["net_one_way"]
sum_july_weekly=309197+409680+114877

O["otc"]={
 "gross_out":vn["gross_out"],"gross_in":vn["gross_in"],"circular":vn["circular"],
 "net_one_way":vn["net_one_way"],
 "circ_pct":100*vn["circular"]/vn["gross_out"] if vn["gross_out"] else 0,
 "desk_bal":desk_bal,"prev_desk":prev_desk,"desk_delta":desk_bal-prev_desk,
 "upbit_feed":upbit_feed,"prev_upbit_feed":14000.0,
 "net_by_venue":vn["net_by_venue"],"out_by_venue":vn["outbound_by_venue"],
 "in_by_venue":vn["inbound_by_venue"],
 "wave":{"window":"2026-08-03..2026-08-24","gross_out":wave["gross_out"],"gross_in":wave["gross_in"],
   "circular":wave["circular"],"circ_pct":100*wave["circular"]/wave["gross_out"],
   "net_one_way":wave["net_one_way"],"sum_weekly":sum_wave_weekly,
   "overstate_egld":sum_wave_weekly-wave["net_one_way"],
   "overstate_pct":100*(sum_wave_weekly-wave["net_one_way"])/wave["net_one_way"],
   "net_by_venue":wave["net_by_venue"],"out_by_venue":wave["outbound_by_venue"],
   "in_by_venue":wave["inbound_by_venue"]},
 "july":{"window":"2026-07-06..2026-07-27","gross_out":july["gross_out"],"gross_in":july["gross_in"],
   "circular":july["circular"],"circ_pct":100*july["circular"]/july["gross_out"],
   "net_one_way":july["net_one_way"],"sum_weekly":sum_july_weekly,
   "overstate_egld":sum_july_weekly-july["net_one_way"],
   "overstate_pct":100*(sum_july_weekly-july["net_one_way"])/july["net_one_way"],
   "net_by_venue":july["net_by_venue"]},
}

# ---------- exchange flows -------------------------------------------------
cur_top={x["address"]:int(x["balance"])/1e18 for x in D["top_accounts"]}
prev_top={x["address"]:x["balance_egld"] for x in prev["top_accounts"]}
def ent(a):
    l=lab(a)
    if "Binance" in l: return "Binance"
    if "Coinbase" in l: return "Coinbase"
    if "Crypto.com" in l: return "Crypto.com"
    for e2 in ["UPbit","Bybit","MEXC","Bitget","Gate.io","KuCoin","Bitfinex","Tokero"]:
        if e2 in l: return e2
    return None
BAD={"erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp29trp6qsl2gdvvz2eqra76xc",
     "erd1ty4pvmjtl3mnsjvnsxqkm3xqm4dm7ppgz9sh4nk4tqvlmw0jyggqzn4mdc"}
exch=[a for a,c in cat_map.items() if c=="exchange"]
per_wallet=[]; ec,ep,ew={},{},{}; noprior=[]
for a in exch:
    if a in BAD or a in DESK_SET: continue
    e2=ent(a)
    if not e2: continue
    cur=bal_of(a); cur=cur if cur is not None else cur_top.get(a)
    p=prev_top.get(a)
    if cur is None: continue
    if p is None: noprior.append({"entity":e2,"label":lab(a),"balance":cur}); continue
    per_wallet.append({"exchange":lab(a),"address":a,"entity":e2,"current":cur,"previous":p,
                       "change_egld":cur-p,"pct":100*(cur-p)/p if p else 0.0})
    ec[e2]=ec.get(e2,0)+cur; ep[e2]=ep.get(e2,0)+p; ew[e2]=ew.get(e2,0)+1
per_wallet.sort(key=lambda x:-abs(x["change_egld"]))
entity=[{"entity":k,"wallets_count":ew[k],"current":ec[k],"previous":ep[k],
         "net_flow_egld":ec[k]-ep[k],"pct":100*(ec[k]-ep[k])/ep[k] if ep[k] else 0.0}
        for k in ec]
entity.sort(key=lambda x:-abs(x["net_flow_egld"]))
O["exch"]={"per_wallet":per_wallet,"entity":entity,"noprior":noprior,
  "total_cur":sum(ec.values()),"total_prev":sum(ep.values()),
  "net":sum(ec.values())-sum(ep.values())}

# ---------- Binance custody ------------------------------------------------
BC="erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"
BH="erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets"
cust_out=[]
for t in (D.get("binance_custody_out") or []):
    v=int(t.get("value","0"))/1e18
    if v>0: cust_out.append({"to":t["receiver"],"label":lab(t["receiver"]),"egld":v,"ts":t.get("timestamp")})
cust_in=[]
for t in (D.get("binance_custody_in") or []):
    v=int(t.get("value","0"))/1e18
    if v>0: cust_in.append({"from":t["sender"],"label":lab(t["sender"]),"egld":v,"ts":t.get("timestamp")})
O["custody"]={"balance":bal_of(BC),"previous":3475540.385133772,
  "delta":(bal_of(BC) or 0)-3475540.385133772,"out":cust_out,"in":cust_in,
  "hot_balance":bal_of(BH),"hot_previous":prev_top.get(BH)}

# ---------- demand instruments --------------------------------------------
MEGA="erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"
CBR="erd1lgdltequh7627rtlacmcp6p5vec7zmu2rxhu7pjwvcja8f4a9gqq9vcc70"
mega_bal=bal_of(MEGA); mega_prev=1099059.3223354353
mp=D["mex_pairs"]
dexvol=sum((p.get("volume24h") or 0) for p in mp)
pooltvl=sum((p.get("totalValue") or 0) for p in mp)
turn=100*dexvol/pooltvl if pooltvl else 0
# withdrawal breadth
hub=D["otc_hub_trace"]; PIPE=set(hub["inbound"])|set(hub["outbound"])
for w in ("julywave","wave2ext","run16","run18","peak_run17"):
    h=D.get(f"otc_hub_trace_{w}")
    if h: PIPE|=set(h["inbound"])|set(h["outbound"])
ROUTERS=set(kn.get("exchange_routers",{}).keys())
raw={}; expipe={}
for a,rec in (D.get("exchange_outbound_paged") or {}).items():
    for t in rec["txs"]:
        v=int(t.get("value","0"))/1e18; r=t.get("receiver")
        if v<1000 or cat(r)=="exchange": continue
        raw[r]=raw.get(r,0)+v
        if r not in PIPE and r not in DESK_SET and r not in ROUTERS: expipe[r]=expipe.get(r,0)+v
O["bid"]={"mega_bal":mega_bal,"mega_prev":mega_prev,"mega_delta":(mega_bal or 0)-mega_prev,
  "mega_txs":len(D.get("mega_whale_inbound") or [])+len(D.get("mega_whale_outbound") or []),
  "cbr_bal":bal_of(CBR),"absorbed":max(0.0,(mega_bal or 0)-mega_prev),
  "turnover":turn,"prev_turnover":prev["xexchange"]["turnover_ratio_pct"],
  "dexvol":dexvol,"prev_dexvol":prev["xexchange"]["volume_24h_usd"],
  "pooltvl":pooltvl,"prev_pooltvl":prev["xexchange"]["pool_tvl_usd"]}
O["breadth"]={"raw_n":len(raw),"raw_egld":sum(raw.values()),
  "ex_n":len(expipe),"ex_egld":sum(expipe.values()),
  "pipeline_share":100*(1-sum(expipe.values())/sum(raw.values())) if raw else 0,
  "top":[{"address":a,"label":lab(a),"egld":v} for a,v in sorted(expipe.items(),key=lambda x:-x[1])[:5]]}

# ---------- staking --------------------------------------------------------
provs=[p for p in D["providers"] if float(p.get("locked",0) or 0)>0]
for p in provs: p["_lk"]=float(p["locked"])/1e18
provs.sort(key=lambda p:-p["_lk"])
tl=sum(p["_lk"] for p in provs)
pkey={p["provider"]:p for p in prev["staking_providers"]}
def pk(p): return p.get("identity") or p["provider"]
shares=[p["_lk"]/tl for p in provs]
hhi=sum(s*s for s in shares)
cur_users=sum(int(p.get("numUsers",0) or 0) for p in provs)
prev_users=sum(p["num_delegators"] for p in prev["staking_providers"])
# p2p_org_ left the locked>0 set carrying its users
p2p=next((p for p in D["providers"] if p.get("identity")=="p2p_org_"),None)
p2p_users=int(p2p.get("numUsers",0)) if p2p else 0
p2p_prev_locked=pkey.get("p2p_org_",{}).get("locked_egld",0.0)
gain=loss=0
moves=[]
for p in provs:
    k=pk(p)
    if k in pkey:
        d=p["_lk"]-pkey[k]["locked_egld"]; du=int(p.get("numUsers",0) or 0)-pkey[k]["num_delegators"]
        moves.append({"identity":k,"delta":d,"users_delta":du,"apr":p.get("apr"),
                      "fee":(p.get("serviceFee") or 0)*100,"locked":p["_lk"],
                      "users":p.get("numUsers"),"nodes":p.get("numNodes")})
        if du>0: gain+=1
        elif du<0: loss+=1
moves.sort(key=lambda m:-abs(m["delta"]))
buckets=[]
covered=0
for lb,lo,hi in [("5-6%",5,6),("6-7%",6,7),("7-8%",7,8),("8-9%",8,9),("9-10%",9,10),("10%+",10,999)]:
    sel=[p for p in provs if lo<=(p.get("apr") or 0)<hi]
    lk=sum(p["_lk"] for p in sel); covered+=lk
    buckets.append({"label":lb,"min_apr_pct":lo,"max_apr_pct":(hi if hi<999 else 99),
                    "provider_count":len(sel),"total_locked_egld":lk})
zeros=[p for p in provs if (p.get("apr") or 0)<5]
residual=(staked-pecon["staked_egld"])-(tl-prev["staking_concentration"]["total_locked_egld"])
pool=F["unbonding_pool"]
O["staking"]={"provs":provs,"total_locked":tl,
  "prev_total_locked":prev["staking_concentration"]["total_locked_egld"],
  "delta_locked":tl-prev["staking_concentration"]["total_locked_egld"],
  "hhi":hhi,"prev_hhi":prev["staking_concentration"]["hhi"],
  "top5":sum(shares[:5])*100,"top10":sum(shares[:10])*100,
  "users":cur_users,"prev_users":prev_users,"users_delta":cur_users-prev_users,
  "p2p_users":p2p_users,"p2p_prev_locked":p2p_prev_locked,
  "users_ex_p2p":cur_users+p2p_users-prev_users,
  "gaining":gain,"losing":loss,"moves":moves,"buckets":buckets,
  "coverage_pct":100*covered/tl,
  "zero_apr_n":len(zeros),"zero_apr_locked":sum(p["_lk"] for p in zeros),
  "residual":residual,
  "undelegated_week":F["undelegated_this_week_total_egld"],
  "undelegate_callers":F["undelegate_callers_count"],
  "pool_total":F["unbonding_pool_total_egld"],
  "pool":pool[:12],
  "run21_wallet":F["run21_unbond_wallet"],
  "movers":F["provider_movers"],
  "apr_min":min(p.get("apr") or 0 for p in provs if (p.get("apr") or 0)>0),
  "apr_max":max(p.get("apr") or 0 for p in provs),
  "apr_wavg":sum((p.get("apr") or 0)*p["_lk"] for p in provs)/tl}

# reward behaviour
ag=beh["aggregates"]
O["reward"]=ag

# ---------- tokens ---------------------------------------------------------
tt=D["tvl_tokens"]; prevls=prev["lsd_supply"]
def sup(t): 
    x=tt.get(t) or {}
    try: return float(x.get("supply") or 0)
    except: return 0.0
def mc(t):
    x=tt.get(t)
    return (x.get("marketCap") or 0) if isinstance(x,dict) else 0
lsd={}
for t in ["SEGLD-3ad2d0","XEGLD-e413ed","SWTAO-356a25","USH-111e09"]:
    c=sup(t); p=float(prevls.get(t) or 0)
    lsd[t]={"supply":c,"prev":p,"pct":100*(c-p)/p if p else 0,"mcap":mc(t),
            "price":(tt.get(t) or {}).get("price")}
stab={}
for sid in ["USDC-c76f1f","USDT-f8c08c"]:
    c=D.get("stable_"+sid) or {}
    stab[sid]={"supply":float(c.get("supply") or 0),"price":c.get("price"),
               "mcap":c.get("marketCap"),"accounts":c.get("accounts")}
O["tokens"]={"lsd":lsd,"stable":stab,
  "wegld_supply":float((D["wegld_token"] or {}).get("supply") or 0),
  "mex_supply":float((D["mex_token"] or {}).get("supply") or 0),
  "mex_prev_supply":float(F["mex_prev"]["supply"] or 0),
  "dataapi":D["dataapi_refetch_log"],"newly":D["newly_issued"]}

# xexchange
mexp=D["mex_economics"]["price"]; pmex=prev["xexchange"]["mex_price_usd"]
pairs=sorted(mp,key=lambda p:-(p.get("volume24h") or 0))
mexpair=next((p for p in (D.get("mex_pairs_wide") or mp)
              if p.get("baseSymbol")=="MEX" and p.get("quoteSymbol")=="WEGLD"),None)
O["xexchange"]={"pairs":D["mex_economics"]["marketPairs"],"vol":dexvol,
  "prev_vol":prev["xexchange"]["volume_24h_usd"],
  "mex_price":mexp,"prev_mex_price":pmex,"mex_wow":100*(mexp-pmex)/pmex,
  "mex_mcap":D["mex_economics"]["marketCap"],
  "top_pairs":[{"name":f"{p.get('baseName')}/{p.get('quoteName')}",
    "volume_24h_usd":p.get("volume24h") or 0,"tvl_usd":p.get("totalValue") or 0,
    "trades_count_24h":p.get("tradesCount24h") or p.get("trades24h") or 0,
    "is_other":False,"share_pct":100*(p.get("volume24h") or 0)/dexvol if dexvol else 0}
    for p in pairs[:5]],
  "pool_tvl":pooltvl,"prev_pool_tvl":prev["xexchange"]["pool_tvl_usd"],
  "turnover":turn,"prev_turnover":prev["xexchange"]["turnover_ratio_pct"],
  "mex_pair_depth":{"pair":"MEX/WEGLD","tvl_usd":(mexpair or {}).get("totalValue") or 0,
    "volume_24h_usd":(mexpair or {}).get("volume24h") or 0,
    "trades_24h":(mexpair or {}).get("tradesCount24h") or 0,
    "share_of_pool_tvl_pct":100*((mexpair or {}).get("totalValue") or 0)/pooltvl if pooltvl else 0,
    "depth_rank":sorted(mp,key=lambda p:-(p.get("totalValue") or 0)).index(mexpair)+1 if mexpair in mp else 2}}

# ---------- defi -----------------------------------------------------------
HL=["HUSDC-d80042","HEGLD-d61095","HUSDT-6f0914","HWBTC-49ca31","HWETH-b3d17e",
    "HBUSD-ac1fca","HHTM-e03ba5","HMEX-df6df7","HUTK-4fa4b2","HWTAO-2e9136"]
hl=sum(mc(t) for t in HL)
we=sum(int(x["balance"])/1e18 for x in D["wegld"].values() if isinstance(x,dict) and "balance" in x)
def egldtvl(usd): return usd/price
prev_hl_egld=prev["defi_tvl"]["Hatom Lending"]/pp
hl_egld=hl/price
O["defi"]={"hatom_lending_usd":hl,"hatom_lending_egld":hl_egld,
  "hatom_lending_prev_usd":prev["defi_tvl"]["Hatom Lending"],
  "hatom_lending_prev_egld":prev_hl_egld,
  "hatom_lending_egld_pct":100*(hl_egld-prev_hl_egld)/prev_hl_egld,
  "hatom_lsd_usd":mc("SEGLD-3ad2d0")+mc("SWTAO-356a25"),
  "hatom_lsd_prev_usd":prev["defi_tvl"]["Hatom Liquid Staking"],
  "ush_usd":mc("USH-111e09"),"ush_prev_usd":prev["defi_tvl"]["Hatom USH"],
  "xoxno_usd":mc("XEGLD-e413ed"),"xoxno_prev_usd":prev["defi_tvl"]["XOXNO LSD"],
  "xexch_usd":we*price,"xexch_egld":we,"xexch_prev_usd":prev["defi_tvl"]["xExchange (USD)"],
  "proto":{k:(v["transfers_24h"].get("count") if isinstance(v["transfers_24h"],dict) else v["transfers_24h"])
           for k,v in D["proto"].items()},
  "inverse_ratio":abs(100*(hl_egld-prev_hl_egld)/prev_hl_egld)/abs(O["macro"]["price_chg"]) if O["macro"]["price_chg"] else None,
  "evaluable":abs(O["macro"]["price_chg"])>=5.0}

# ---------- whale tiers (common-address basis) -----------------------------
SYS="erd1qqqqqqqqqqqqq"
common=[a for a in cur_top if a in prev_top and not a.startswith(SYS) and cat(a)!="system"]
def tier(v):
    if v>1_000_000: return "mega"
    if v>=100_000: return "large"
    if v>=10_000: return "mid"
def buck(pairs_):
    o={"mega":[0,0.0],"large":[0,0.0],"mid":[0,0.0]}
    for a,v in pairs_:
        t=tier(v)
        if t: o[t][0]+=1; o[t][1]+=v
    return o
cb=buck([(a,cur_top[a]) for a in common]); pb=buck([(a,prev_top[a]) for a in common])
O["tiers"]={t:{"count_current":cb[t][0],"count_previous":pb[t][0],
   "total_balance_egld":cb[t][1],"previous_total_balance_egld":pb[t][1],
   "net_change_egld":cb[t][1]-pb[t][1],
   "net_change_pct":100*(cb[t][1]-pb[t][1])/pb[t][1] if pb[t][1] else 0}
   for t in ("mega","large","mid")}
O["tiers_basis"]=len(common)
crossers=[]
for a in common:
    if tier(cur_top[a])!=tier(prev_top[a]):
        crossers.append({"address":a,"label":lab(a),"prev":prev_top[a],"cur":cur_top[a],
                         "from":tier(prev_top[a]),"to":tier(cur_top[a])})
O["tier_crossers"]=crossers

# wallet changes
wc=[]
for a,v in sorted(cur_top.items(),key=lambda kv:-kv[1])[:len(prev_top)]:
    if a in prev_top and cat(a)!="system":
        d=v-prev_top[a]
        if abs(d)>2000:
            wc.append({"address":a,"label":lab(a),"category":cat(a),
                       "tier":(tier(v)+"_whale") if tier(v) else None,
                       "balance_current_egld":v,"balance_previous_egld":prev_top[a],
                       "change_egld":d,"change_pct":100*d/prev_top[a] if prev_top[a] else 0})
wc.sort(key=lambda x:-abs(x["change_egld"]))
O["wallet_changes"]=wc[:20]

# large transactions
seen=set(); rows=[]
for a,rec in D["accounts"].items():
    for t in (rec.get("txs") if isinstance(rec.get("txs"),list) else []):
        v=int(t.get("value","0"))/1e18
        if v>=1000 and t.get("txHash") not in seen:
            seen.add(t["txHash"]); rows.append((v,t))
rows.sort(key=lambda x:-x[0])
def flow(t):
    s,r=t["sender"],t["receiver"]
    sc,rc=cat(s),cat(r)
    if sc=="exchange" and rc=="exchange": return "exchange_to_exchange"
    if rc=="exchange": return "exchange_inflow"
    if sc=="exchange": return "exchange_outflow"
    if rc=="defi": return "defi_deposit"
    if sc=="defi": return "defi_withdrawal"
    if rc=="validator" or (r or "").startswith("erd1qqqqqqqqqqqqqqqpqqq"): return "staking"
    if sc=="validator": return "unstaking"
    if sc!="unknown" or rc!="unknown": return "whale_to_whale"
    return "unknown"
O["large_txs"]=[{"hash":t["txHash"],
  "timestamp":datetime.fromtimestamp(t["timestamp"],tz=timezone.utc).isoformat().replace("+00:00","Z"),
  "sender":t["sender"],"sender_label":lab(t["sender"]),
  "receiver":t["receiver"],"receiver_label":lab(t["receiver"]),
  "value_egld":v,"value_usd":v*price,"flow_type":flow(t)} for v,t in rows[:25]]
O["large_txs_count"]=len(rows)

# ---------- z-scores -------------------------------------------------------
rb=learn["runs"][-1]["running_baselines"]
def z(metric,cur_v):
    arr=rb.get(metric) or []
    if len(arr)<4: return {"method":"percent_threshold","n":len(arr)}
    mean=sum(arr)/len(arr)
    sd=math.sqrt(sum((x-mean)**2 for x in arr)/len(arr))
    if sd==0: return {"method":"rule_based","n":len(arr),"note":"degenerate stddev"}
    zz=(cur_v-mean)/sd
    sev="low" if abs(zz)<2 else ("medium" if abs(zz)<3 else ("high" if abs(zz)<4 else "critical"))
    return {"method":"z_score","n":len(arr),"mean":mean,"stddev":sd,"z":zz,"severity":sev}
O["z"]={
 "price":z("egld_price_usd",price),
 "dexvol":z("dex_volume_24h_usd",dexvol),
 "staked":z("staked_egld",staked),
 "mex":z("mex_price_usd",mexp),
 "delegators":z("total_delegators",cur_users),
 "exflow":z("exchange_net_flow_egld",O["exch"]["net"]),
 "otc":z("otc_pipeline_throughput_egld_7d",vn["gross_out"]),
 "turnover":z("dex_turnover_ratio_pct",turn),
 "compound":z("reward_compound_pct",ag["compound_vs_claim_at_function_level"]["compound_pct_of_reward_decisions"]),
 "custody":z("binance_staking_custody_egld",O["custody"]["balance"]),
 "sr":z("staked_ratio",staked/circ),
}
O["baselines"]=rb
json.dump(O,open(f"{OUT}/derived.json","w"),indent=1,default=str)
print("derived written")
for k in ("macro","otc","staking","bid","breadth","defi"):
    print(k,"ok")
print("price_chg",round(O["macro"]["price_chg"],2),"net_one_way",O["otc"]["net_one_way"])
print("z:",json.dumps({k:(round(v.get("z",0),2) if "z" in v else v.get("method")) for k,v in O["z"].items()}))
