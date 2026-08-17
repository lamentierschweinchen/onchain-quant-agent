#!/usr/bin/env python3
"""Run #21 stage 2: staking, tokens, DeFi, whale-I classification, z-scores.
Appends to /tmp/run21w/derived.json."""
import json, math
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D = json.load(open(f"{REPO}/data/collected/2026-08-17.json"))
prevcol = json.load(open(f"{REPO}/data/collected/2026-08-10.json"))
prev = json.load(open(f"{REPO}/data/previous.json"))
kn = json.load(open(f"{REPO}/data/known-addresses.json"))
learn = json.load(open(f"{REPO}/data/learnings.json"))
beh = json.load(open(f"{REPO}/data/collected/delegator_behavior_2026-08-17.json"))
F = json.load(open(f"{REPO}/data/collected/followup_2026-08-17.json"))
O = json.load(open("/tmp/run21w/derived.json"))

label_map, cat_map = {}, {}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"):
                label_map[a]=m.get("name","Unknown"); cat_map[a]=m.get("category","unknown")
def lab(a): return label_map.get(a,"Unknown")

econ=D["economics"]; price=econ["price"]; pp=prev["economics"]["egld_price_usd"]
staked=econ["staked"]

# ---------------- staking ----------------
provs=[p for p in D["providers"] if p.get("locked") and float(p["locked"])>0]
for p in provs: p["_lk"]=float(p["locked"])/1e18
provs.sort(key=lambda p:-p["_lk"])
total_locked=sum(p["_lk"] for p in provs)
shares=[p["_lk"]/total_locked for p in provs]
hhi=sum(s*s for s in shares); top5=sum(shares[:5])*100; top10=sum(shares[:10])*100
prevp={p["name"]:p["locked_egld"] for p in prev["staking_providers"]}
prevu={p["name"]:p["num_delegators"] for p in prev["staking_providers"]}
prevfee={p["name"]:p.get("fee") for p in prev["staking_providers"]}
prevapr={p["name"]:p.get("apr") for p in prev["staking_providers"]}
def aprp(p): return p.get("apr") or 0
def feep(p): return p.get("serviceFee") or 0
def nm_of(p): return p.get("identity") or p.get("provider")

top_providers=[]
for i,p in enumerate(provs[:20],1):
    nm=nm_of(p); pl_=prevp.get(nm)
    top_providers.append({"rank":i,"identity":nm,"name":nm,"provider_address":p["provider"],
        "locked_egld":p["_lk"],"previous_locked_egld":pl_,"share_pct":p["_lk"]/total_locked*100,
        "apr_pct":aprp(p),"fee_pct":feep(p)*100,"num_users":p.get("numUsers"),
        "num_nodes":p.get("numNodes"),
        "wow_change_egld":(p["_lk"]-pl_) if pl_ is not None else None})
apr_w=sum(p["_lk"]*aprp(p) for p in provs)/total_locked
buckets=[]
for lbl,mn,mx in [("5-6%",5,6),("6-7%",6,7),("7-8%",7,8),("8-9%",8,9),("9-10%",9,10),("10%+",10,100)]:
    sub=[p for p in provs if mn<=aprp(p)<mx]
    buckets.append({"label":lbl,"min_apr_pct":mn,"max_apr_pct":mx,"provider_count":len(sub),
                    "total_locked_egld":sum(p["_lk"] for p in sub)})
zero_apr=[p for p in provs if aprp(p)==0]
qual=[p for p in provs if p["_lk"]>5000]
top_apr=[{"identity":nm_of(p),"name":nm_of(p),"apr_pct":aprp(p),"fee_pct":feep(p)*100,
          "locked_egld":p["_lk"]} for p in sorted(qual,key=lambda p:-aprp(p))[:5]]
lowest_fee=[{"identity":nm_of(p),"name":nm_of(p),"apr_pct":aprp(p),"fee_pct":feep(p)*100,
             "locked_egld":p["_lk"]} for p in sorted(qual,key=lambda p:(feep(p),-aprp(p)))[:5]]
cur_deleg=sum(p.get("numUsers",0) for p in provs); prev_deleg=sum(prevu.values())
gain=sum(1 for p in provs if prevu.get(nm_of(p)) is not None and p.get("numUsers",0)>prevu[nm_of(p)])
lose=sum(1 for p in provs if prevu.get(nm_of(p)) is not None and p.get("numUsers",0)<prevu[nm_of(p)])
def lk_wow(nm):
    p=next((x for x in provs if nm_of(x)==nm),None)
    if not p or nm not in prevp: return None
    return p["_lk"]-prevp[nm]
def usr_wow(nm):
    p=next((x for x in provs if nm_of(x)==nm),None)
    if not p or nm not in prevu: return None
    return p.get("numUsers",0)-prevu[nm]

deleg_tvl_wow=total_locked-prev["staking_concentration"]["total_locked_egld"]
raw_direct_residual=(staked-prev["economics"]["staked_egld"])-deleg_tvl_wow

# fee events: providers whose serviceFee changed
fee_events=[]
for p in provs:
    nm=nm_of(p); pf=prevfee.get(nm); cf=feep(p)
    if pf is not None and abs(cf-pf)>1e-9:
        fee_events.append({"provider":nm,"fee_from_pct":pf*100,"fee_to_pct":cf*100,
            "apr_from_pct":prevapr.get(nm),"apr_to_pct":aprp(p),
            "locked_egld":p["_lk"],"locked_wow_egld":lk_wow(nm),"users":p.get("numUsers"),
            "users_wow":usr_wow(nm),"num_nodes":p.get("numNodes")})
fee_events.sort(key=lambda x:-(x["fee_to_pct"]-x["fee_from_pct"]))

# provider that left (locked -> 0)
cur_names={nm_of(p) for p in provs}
leavers=[n for n in prevp if n not in cur_names]
notable_leavers=[{"identity":n,"name":n,"previous_locked_egld":prevp[n]} for n in leavers
                 if prevp[n]>50000]

# the single unwinding delegator (from followup)
UNWIND_ADDR="erd1daqlaezxx22rzyxnqx5ddkykm5ajelt0hetjnstm7rxqg78xqusqazv9ms"
UNWIND_TOTAL=229864.6
UNWIND_LEGS=[{"provider":"p2p_org_","amount":149585.4,"days_to_unbond":7.1,"date":"2026-08-15"},
             {"provider":"erd1qqqq...pvhlllls6yl73z (unnamed, now zero-locked)",
              "amount":80279.2,"days_to_unbond":6.1,"date":"2026-08-14"}]
corrected_direct=raw_direct_residual-UNWIND_TOTAL

hi_apr=[p for p in provs if aprp(p)>=8.8 and nm_of(p) in prevp]
hi_apr_net=sum(p["_lk"]-prevp[nm_of(p)] for p in hi_apr)
zero_fee=[p for p in provs if feep(p)==0 and nm_of(p) in prevp]
zero_fee_net=sum(p["_lk"]-prevp[nm_of(p)] for p in zero_fee)
moves=sorted(((nm_of(p), p["_lk"]-prevp[nm_of(p)], usr_wow(nm_of(p)), aprp(p), feep(p)*100)
              for p in provs if nm_of(p) in prevp), key=lambda x:-abs(x[1]))

O["staking"]={"total_locked":total_locked,"hhi":hhi,"top5":top5,"top10":top10,
  "top_providers":top_providers,"buckets":buckets,"top_apr":top_apr,"lowest_fee":lowest_fee,
  "apr_w":apr_w,"n_providers":len(provs),"zero_apr_providers":len(zero_apr),
  "zero_apr_locked":sum(p["_lk"] for p in zero_apr),
  "churn":{"total_delegators_current":cur_deleg,"total_delegators_previous":prev_deleg,
    "delegators_added":cur_deleg-prev_deleg,
    "delegators_change_pct":100*(cur_deleg-prev_deleg)/prev_deleg,
    "providers_gaining_delegators":gain,"providers_losing_delegators":lose},
  "deleg_tvl_wow":deleg_tvl_wow,"raw_direct_residual":raw_direct_residual,
  "corrected_direct":corrected_direct,"fee_events":fee_events,
  "leavers":leavers,"notable_leavers":notable_leavers,
  "unwind":{"address":UNWIND_ADDR,"total":UNWIND_TOTAL,"legs":UNWIND_LEGS,
            "share_of_delegation_decline_pct":100*UNWIND_TOTAL/abs(deleg_tvl_wow)},
  "hi_apr_net":hi_apr_net,"hi_apr_n":len(hi_apr),"zero_fee_net":zero_fee_net,
  "top_moves":[{"provider":m[0],"locked_wow":m[1],"users_wow":m[2],"apr":m[3],"fee":m[4]} for m in moves[:14]],
  "binance_staking_prov_wow":lk_wow("binance_staking"),
  "pi_staking_wow":lk_wow("pi-staking"),"pi_staking_users_wow":usr_wow("pi-staking"),
  "stakenest_wow":lk_wow("stakenest"),"cslabsio_wow":lk_wow("cslabsio"),
  "disruptive_wow":lk_wow("disruptivedigital"),"vapor_wow":lk_wow("vaporrepublic")}

# ---------------- reward behavior ----------------
agg=beh["aggregates"]; cvc=agg["compound_vs_claim_at_function_level"]
fates=agg.get("delegator_fates_by_tier",{})
O["reward"]={"compound_pct":cvc["compound_pct_of_reward_decisions"],"compound_prev":59.54,
  "redelegate":cvc["redelegate_count"],"claims":cvc["claim_count"],
  "retail_n":fates.get("retail",{}).get("total_events",0),
  "retail_sold":fates.get("retail",{}).get("by_count",{}).get("sold",0),
  "retail_held":fates.get("retail",{}).get("by_count",{}).get("held",0),
  "inst_n":fates.get("institutional",{}).get("total_events",0),
  "inst_val":fates.get("institutional",{}).get("total_value_egld",0),
  "inst_sold_val":fates.get("institutional",{}).get("by_value_egld",{}).get("sold",0)}

# ---------------- tokens ----------------
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
    ptx=prev_tv.get(t["identifier"]); pt=ptx.get("transactions") if ptx else None
    top_by_volume.append({"identifier":t["identifier"],"name":t.get("name"),
        "transactions":t.get("transactions"),"previous_transactions":pt,
        "change_pct":(100*(t.get("transactions",0)-pt)/pt) if pt else None,
        "price_usd":t.get("price"),"volume_24h_usd":None})
holders_map={t["identifier"]:t.get("accounts") for t in D["tokens_holders"]}
top_by_market_cap=[]
for t in D["tokens_mcap"][:10]:
    tid=t["identifier"]
    top_by_market_cap.append({"identifier":tid,"name":t.get("name"),"holders":holders_map.get(tid),
        "previous_holders":prev_th.get(tid,{}).get("holders"),"price_usd":t.get("price"),
        "market_cap_usd":t.get("marketCap"),"volume_24h_usd":None})
KNOWN={t["identifier"] for t in prev.get("top_tokens_by_holders",[])}|{t["identifier"] for t in prev.get("top_tokens_by_volume",[])}
newly=[]; rejected=[]
for ni in D.get("newly_issued",[]):
    if ni["accounts"]>1000 or ni["identifier"] in KNOWN:
        rejected.append({"identifier":ni["identifier"],"reason":"established token misidentified by issue-scan"}); continue
    if ni["accounts"]<=10 or ni["transactions"]<=5:
        rejected.append({"identifier":ni["identifier"],"name":ni.get("name"),
            "reason":f"below quality bar ({ni['accounts']} holders, {ni['transactions']} txs)"}); continue
    newly.append({"identifier":ni["identifier"],"name":ni["name"],"ticker":ni["ticker"],
        "holders":ni["accounts"],"transactions":ni["transactions"],"timestamp":ni["timestamp"],
        "deployer":ni["deployer"],"deployer_label":lab(ni["deployer"]),
        "issued_at":datetime.fromtimestamp(ni["timestamp"],tz=timezone.utc).isoformat()})
O["tokens"]={"top_by_holders":top_by_holders,"top_by_volume":top_by_volume,
             "top_by_market_cap":top_by_market_cap,"newly_issued":newly,"rejected":rejected}

# xexchange + MEX depth
mp=D["mex_pairs"]; meco=D["mex_economics"]
pairs=[]
for p in mp:
    pairs.append({"name":(p.get("baseName") or "?")+"/"+(p.get("quoteName") or "?"),
        "volume_24h_usd":p.get("volume24h") or 0,"tvl_usd":p.get("totalValue"),
        "trades_count_24h":p.get("tradesCount24h", p.get("trades24h")),"is_other":False})
pairs.sort(key=lambda x:-(x["volume_24h_usd"] or 0))
totvol=sum((x["volume_24h_usd"] or 0) for x in pairs)
for x in pairs: x["share_pct"]=100*(x["volume_24h_usd"] or 0)/totvol if totvol else 0
tot_tvl=sum((p.get("totalValue") or 0) for p in mp)
prev_tot_tvl=sum((p.get("totalValue") or 0) for p in prevcol.get("mex_pairs",[]))
prev_tot_vol=sum((p.get("volume24h") or 0) for p in prevcol.get("mex_pairs",[]))
turnover=100*totvol/tot_tvl if tot_tvl else None
prev_turnover=100*prev_tot_vol/prev_tot_tvl if prev_tot_tvl else None
prev_mexp=prev["xexchange"]["mex_price_usd"]; prev_dexvol=prev["xexchange"]["volume_24h_usd"]
mexpair=next((p for p in mp if (p.get("baseSymbol")=="MEX" or p.get("baseName")=="MEX")
              and (p.get("quoteSymbol")=="WEGLD" or p.get("quoteName")=="WrappedEGLD")), None)
O["xexchange"]={"total_pairs":meco.get("marketPairs"),"total_volume_24h_usd":totvol,
    "mex_price_usd":meco["price"],"mex_market_cap_usd":meco["marketCap"],
    "mex_price_change_24h_pct":None,
    "mex_price_change_wow_pct":100*(meco["price"]-prev_mexp)/prev_mexp,
    "top_pair":pairs[0]["name"],"top_pair_volume_24h_usd":pairs[0]["volume_24h_usd"],
    "top_pair_dominance_pct":pairs[0]["share_pct"],"top_pairs_by_volume":pairs[:5],
    "pool_tvl_usd":tot_tvl,"previous_pool_tvl_usd":prev_tot_tvl,
    "turnover_ratio_pct":turnover,"previous_turnover_ratio_pct":prev_turnover,
    "dex_vol_wow_pct":100*(totvol-prev_dexvol)/prev_dexvol,
    "mex_pair_depth":{"pair":"MEX/WEGLD","tvl_usd":(mexpair or {}).get("totalValue"),
        "volume_24h_usd":(mexpair or {}).get("volume24h"),
        "trades_24h":(mexpair or {}).get("tradesCount24h",(mexpair or {}).get("trades24h")),
        "share_of_pool_tvl_pct":100*((mexpair or {}).get("totalValue") or 0)/tot_tvl if tot_tvl else None,
        "depth_rank":sorted(mp,key=lambda p:-(p.get("totalValue") or 0)).index(mexpair)+1 if mexpair else None}}

# ---------------- DeFi ----------------
tt=D["tvl_tokens"]
def mc(tid):
    t=tt.get(tid); return (t.get("marketCap") or 0) if isinstance(t,dict) else 0
def sup(tid,col=tt):
    t=col.get(tid)
    try: return float(t.get("supply")) if t and t.get("supply") else None
    except: return None
def sup_wow(tid):
    c=sup(tid); p=float(prev["lsd_supply"].get(tid) or 0) or None
    if c is None or not p: return None
    return 100*(c-p)/p
hatom_lending=sum(mc(x) for x in ["HUSDC-d80042","HEGLD-d61095","HUSDT-6f0914","HWBTC-49ca31",
    "HWETH-b3d17e","HBUSD-ac1fca","HHTM-e03ba5","HMEX-df6df7","HUTK-4fa4b2","HWTAO-2e9136"])
segld_mcap=mc("SEGLD-3ad2d0"); swtao_mcap=mc("SWTAO-356a25")
hatom_lsd=segld_mcap+swtao_mcap; hatom_ush=mc("USH-111e09"); xoxno_lsd=mc("XEGLD-e413ed")
wegld_egld=sum(int(b["balance"])/1e18 for b in D["wegld"].values() if isinstance(b,dict) and "balance" in b)
def tcount(name):
    c=D["proto"][name]["transfers_24h"]; return c.get("count") if isinstance(c,dict) else c
prev_hl_egld=prev["defi_tvl"]["Hatom Lending"]/pp
prev_xl_egld=prev["defi_tvl"]["XOXNO LSD"]/pp
prev_hlsd=prev["defi_tvl"]["Hatom Liquid Staking"]; prev_hlsd_egld=prev_hlsd/pp
prev_xexch_egld=prev["defi_tvl"]["xExchange (USD)"]/pp
hl_egld=hatom_lending/price; hlsd_egld=hatom_lsd/price
xlsd_egld=xoxno_lsd/price; ush_egld=hatom_ush/price
price_chg=O["macro"]["price_chg"]
hl_egld_chg=100*(hl_egld-prev_hl_egld)/prev_hl_egld
def stable_wow(sid):
    c=D.get("stable_"+sid,{}); p=prevcol.get("stable_"+sid,{})
    try: cur=float(c.get("supply")); pr=float(p.get("supply"))
    except: return None
    return 100*(cur-pr)/pr if pr else None
wegld_now=float((D.get("wegld_token") or {}).get("supply") or 0)
wegld_prev=None
for t in prevcol.get("tokens_holders",[]):
    if t["identifier"]=="WEGLD-bd4d79":
        try: wegld_prev=int(t.get("supply","0"))/1e18
        except: pass
O["defi"]={"hatom_lending_usd":hatom_lending,"hatom_lending_egld":hl_egld,
  "hatom_lending_egld_wow_pct":hl_egld_chg,"prev_hl_usd":prev["defi_tvl"]["Hatom Lending"],
  "hatom_lsd_usd":hatom_lsd,"hatom_lsd_egld":hlsd_egld,"segld_mcap":segld_mcap,"swtao_mcap":swtao_mcap,
  "hatom_lsd_egld_wow_pct":100*(hlsd_egld-prev_hlsd_egld)/prev_hlsd_egld,"prev_hlsd_usd":prev_hlsd,
  "ush_usd":hatom_ush,"ush_egld":ush_egld,"prev_ush_usd":prev["defi_tvl"]["Hatom USH"],
  "xoxno_lsd_usd":xoxno_lsd,"xoxno_lsd_egld":xlsd_egld,
  "xoxno_lsd_egld_wow_pct":100*(xlsd_egld-prev_xl_egld)/prev_xl_egld,
  "prev_xoxno_usd":prev["defi_tvl"]["XOXNO LSD"],
  "xexch_tvl_egld":wegld_egld,"xexch_tvl_usd":wegld_egld*price,
  "xexch_egld_wow_pct":100*(wegld_egld-prev_xexch_egld)/prev_xexch_egld,
  "segld_supply":sup("SEGLD-3ad2d0"),"segld_supply_wow":sup_wow("SEGLD-3ad2d0"),
  "xegld_supply":sup("XEGLD-e413ed"),"xegld_supply_wow":sup_wow("XEGLD-e413ed"),
  "swtao_supply":sup("SWTAO-356a25"),"swtao_supply_wow":sup_wow("SWTAO-356a25"),
  "ush_supply":sup("USH-111e09"),"ush_supply_wow":sup_wow("USH-111e09"),
  "usdc_supply_wow":stable_wow("USDC-c76f1f"),"usdt_supply_wow":stable_wow("USDT-f8c08c"),
  "usdc_supply":float((D.get("stable_USDC-c76f1f") or {}).get("supply") or 0),
  "usdt_supply":float((D.get("stable_USDT-f8c08c") or {}).get("supply") or 0),
  "usdt_supply_prev":float((prevcol.get("stable_USDT-f8c08c") or {}).get("supply") or 0),
  "wegld_supply":wegld_now,"wegld_supply_wow":(100*(wegld_now-wegld_prev)/wegld_prev if wegld_prev else None),
  "inverse_ratio_mechanical":abs(hl_egld_chg)/abs(price_chg) if price_chg else None,
  "inverse_evaluable":abs(price_chg)>=5.0,
  "transfers":{k:tcount(k) for k in D["proto"]}}

# XEGLD redemption trace (rec #3)
xd=F.get("xegld_dest_class",{})
callers=F.get("xegld_caller_detail",[])
exch_dest=sum(v for k,v in xd.items() if k=="exchange")
O["xegld_trace"]={"callers":len(callers),"dest_class":xd,"exchange_egld":exch_dest,
  "delegation_egld":xd.get("delegation",0),"other_egld":xd.get("other",0),
  "fn_counts":{k:len(F.get(f"xegld_{k}") or []) for k in ["unDelegate","unDelegatePending","withdraw","withdrawPending"]}}

# ---------------- Unknown Whale I classification (rec #6) ----------------
WI="erd1vd76pwhl4dyeyd8gylv6mkkvy7g4dnfezjuyp4j4x3wwnauga57q53m3z0"
wi=D["whale_i_info"]
router_set=set(kn.get("exchange_routers",{}).keys())
UPBIT_DESK="erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
DIST_DESK="erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
PIPE=set(D["otc_hub_trace"]["inbound"])|set(D["otc_hub_trace"]["outbound"])|{UPBIT_DESK,DIST_DESK}
for w in ("run16","run18","peak_run17"):
    h=D.get(f"otc_hub_trace_{w}")
    if h: PIPE|=set(h["inbound"])|set(h["outbound"])
def wi_cls(a):
    if a in (UPBIT_DESK,DIST_DESK): return "desk"
    if a in router_set: return "router"
    if a in PIPE: return "pipeline"
    if cat_map.get(a)=="exchange": return "exchange"
    return "external"
def agg_val(txs,key):
    o={}
    for t in txs:
        try: v=int(t.get("value","0"))/1e18
        except: v=0
        if v<=0: continue
        o[t[key]]=o.get(t[key],0)+v
    return o
wi_in=agg_val(D["whale_i_inbound_30d"],"sender"); wi_out=agg_val(D["whale_i_outbound_30d"],"receiver")
def split(m):
    tot=sum(m.values()); byc={}
    for a,v in m.items(): byc[wi_cls(a)]=byc.get(wi_cls(a),0)+v
    return tot,byc
in_tot,in_by=split(wi_in); out_tot,out_by=split(wi_out)
def pipe_share(byc,tot):
    return 100*sum(v for k,v in byc.items() if k in ("desk","router","pipeline"))/tot if tot else 0
O["whale_i"]={"balance":int(wi.get("balance","0"))/1e18,"prev_balance":prev_top_bal if (prev_top_bal:=next((x["balance_egld"] for x in prev["top_accounts"] if x["address"]==WI),None)) else None,
  "nonce":wi.get("nonce"),"in_txs":len(D["whale_i_inbound_30d"]),"out_txs":len(D["whale_i_outbound_30d"]),
  "in_counterparties":len(wi_in),"out_counterparties":len(wi_out),
  "in_total":in_tot,"out_total":out_tot,"in_by_class":in_by,"out_by_class":out_by,
  "in_pipeline_pct":pipe_share(in_by,in_tot),"out_pipeline_pct":pipe_share(out_by,out_tot),
  "combined_pipeline_pct":100*(sum(v for k,v in in_by.items() if k in ("desk","router","pipeline"))
      +sum(v for k,v in out_by.items() if k in ("desk","router","pipeline")))/(in_tot+out_tot),
  "hub_net_this_week":O["otc"]["net_by_venue"].get("Unknown Whale I (active)",0),
  "page_cap_hit":len(D.get("_pagecap_terminations",[]))>0}

# ---------------- z-scores ----------------
rb=learn["runs"][-1]["running_baselines"]
def zc(arr,cur):
    if len(arr)<4: return None
    m=sum(arr)/len(arr); sd=math.sqrt(sum((x-m)**2 for x in arr)/len(arr))
    return [m,sd,((cur-m)/sd if sd else 0)]
O["z"]={"price":zc(rb["egld_price_usd"],price),
        "mex":zc(rb["mex_price_usd"],meco["price"]),
        "deleg":zc(rb["total_delegators"],cur_deleg),
        "staked":zc(rb["staked_egld"],staked),
        "dexvol":zc(rb["dex_volume_24h_usd"],totvol)}

# token supply events
prev_supply_raw={t["identifier"]:(int(t["supply_raw"]) if t.get("supply_raw") else None) for t in prev["top_tokens_by_holders"]}
cur_by_id={t["identifier"]:t for t in D["tokens_holders"]}
tse=[]
for tid,ps in prev_supply_raw.items():
    ct=cur_by_id.get(tid)
    if ct and ps and ps>0:
        try: cs=int(ct.get("supply","0"))
        except: cs=None
        if cs and cs>0:
            chg=100*(cs-ps)/ps
            thresh=0.1 if tid.startswith(("USDC","USDT")) else 1.0
            if abs(chg)>thresh:
                tse.append({"identifier":tid,"name":ct.get("name","?"),
                    "event":"mint" if chg>0 else "burn","supply_previous":str(ps),
                    "supply_current":str(cs),"change_pct":chg,
                    "description":f"{tid} supply {chg:+.2f}% ({'mint' if chg>0 else 'burn'})."})
O["token_supply_events"]=tse

json.dump(O,open("/tmp/run21w/derived.json","w"),indent=1)
print("STAGE 2 OK")
print("delegation",round(total_locked),"wow",round(deleg_tvl_wow),"raw residual",round(raw_direct_residual),
      "corrected",round(corrected_direct))
print("providers",len(provs),"zero-apr",len(zero_apr),"leavers",leavers)
print("fee_events",json.dumps(fee_events,indent=1))
print("churn",O["staking"]["churn"])
print("whale_i",{k:(round(v,1) if isinstance(v,float) else v) for k,v in O["whale_i"].items() if not isinstance(v,dict)})
print("  in_by",{k:round(v) for k,v in in_by.items()},"out_by",{k:round(v) for k,v in out_by.items()})
print("  pipeline pct in %.1f out %.1f combined %.1f"%(O["whale_i"]["in_pipeline_pct"],O["whale_i"]["out_pipeline_pct"],O["whale_i"]["combined_pipeline_pct"]))
print("dex",round(totvol),"turnover",round(turnover,3),"prev",round(prev_turnover,3),"mexpair",O["xexchange"]["mex_pair_depth"])
print("defi lending EGLD wow %.2f%% inverse mech %.2f evaluable %s"%(hl_egld_chg,O["defi"]["inverse_ratio_mechanical"],O["defi"]["inverse_evaluable"]))
print("supplies: SEGLD %.3f XEGLD %.3f SWTAO %.3f USH %.3f USDC %.3f USDT %.3f WEGLD %.3f"%(
  O["defi"]["segld_supply_wow"],O["defi"]["xegld_supply_wow"],O["defi"]["swtao_supply_wow"],
  O["defi"]["ush_supply_wow"],O["defi"]["usdc_supply_wow"],O["defi"]["usdt_supply_wow"],O["defi"]["wegld_supply_wow"]))
print("xegld_trace",O["xegld_trace"])
print("tse",[(t["identifier"],round(t["change_pct"],2)) for t in tse])
print("z",{k:[round(x,3) for x in v] if v else None for k,v in O["z"].items()})
print("reward",O["reward"])
print("newly",O["tokens"]["newly_issued"],"rejected",O["tokens"]["rejected"])
