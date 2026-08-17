#!/usr/bin/env python3
"""Run #21 stage 1: compute every derived quantity and dump it to
/tmp/run21w/derived.json so the narrative assembler stays readable."""
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

label_map, cat_map = {}, {}
for section, entries in kn.items():
    if not isinstance(entries, dict) or section == "_metadata": continue
    for addr, meta in entries.items():
        if isinstance(meta, dict) and addr.startswith("erd1"):
            label_map[addr] = meta.get("name", "Unknown")
            cat_map[addr] = meta.get("category", "unknown")
def lab(a): return label_map.get(a, "Unknown")
def cat(a): return cat_map.get(a, "unknown")

O = {}   # derived output

# ---------------- macro ----------------
econ = D["economics"]; st = D["stats"]; pecon = prev["economics"]; pact = prev["activity"]
price = econ["price"]; staked = econ["staked"]; circ = econ["circulatingSupply"]
sr = staked / circ; pp = pecon["egld_price_usd"]
be = D["btc_eth"]
O["macro"] = {
    "price": price, "prev_price": pp, "price_chg": 100*(price-pp)/pp,
    "btc": be["bitcoin"]["usd"], "eth": be["ethereum"]["usd"],
    "btc_wow": 100*(be["bitcoin"]["usd"]-pecon["btc_price_usd"])/pecon["btc_price_usd"],
    "eth_wow": 100*(be["ethereum"]["usd"]-pecon["eth_price_usd"])/pecon["eth_price_usd"],
    "staked": staked, "staked_prev": pecon["staked_egld"], "staked_chg": staked-pecon["staked_egld"],
    "sr": sr, "sr_prev": pecon["staked_ratio"],
}

acc = D["accounts"]
def bal_of(a):
    x = acc.get(a)
    if x and isinstance(x.get("info"), dict) and "balance" in x["info"]:
        try: return int(x["info"]["balance"])/1e18
        except: return None
    return None

# ---------------- OTC hub: this week, backfills, wave-window netting ----------------
UPBIT_DESK = "erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
DIST_DESK  = "erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
DESK_SET = {UPBIT_DESK, DIST_DESK}

def desk_gross(block, key):
    gross = inter = 0.0; other = {}
    for a, v in block.items():
        for t in v.get("txs", []):
            try: val = int(t.get("value","0"))/1e18
            except: val = 0
            if val <= 0: continue
            gross += val
            o = t.get(key)
            if o in DESK_SET: inter += val
            else: other[o] = other.get(o,0)+val
    return gross, inter, other

G_OUT, G_INTER, desk_dest = desk_gross(D["desk_outbound_paged"], "receiver")
OTC_GROSS_OUT = G_OUT - G_INTER
_gi, _ii, desk_src = desk_gross(D["desk_inbound_paged"], "sender")
OTC_GROSS_IN = sum(desk_src.values())

hub = D["otc_hub_trace"]["venue_netting"]
HUB_CIRC = hub["circular"]; HUB_NET = hub["gross_out"] - hub["circular"]
hub_net = dict(hub["net_by_venue"])
UPBIT_FEED = abs(hub["inbound_by_venue"].get("UPbit", 0))
UPBIT_RETURN = hub["outbound_by_venue"].get("UPbit", 0)

peak = D["otc_hub_trace_peak_run17"]["venue_netting"]
r16 = D["otc_hub_trace_run16"]["venue_netting"]
r18 = D["otc_hub_trace_run18"]["venue_netting"]

# wave-window (two-week) netting: Aug 3 -> Aug 17
pr_hub = prevcol["otc_hub_trace"]["venue_netting"]
w_out, w_in = {}, {}
for src in (hub, pr_hub):
    for v, x in src["outbound_by_venue"].items(): w_out[v] = w_out.get(v,0)+x
    for v, x in src["inbound_by_venue"].items():  w_in[v]  = w_in.get(v,0)+x
w_venues = sorted(set(w_out)|set(w_in))
W_GROSS_OUT = hub["gross_out"] + pr_hub["gross_out"]
W_GROSS_IN  = hub["gross_in"]  + pr_hub["gross_in"]
W_CIRC = sum(min(w_out.get(v,0), w_in.get(v,0)) for v in w_venues)
W_NET = W_GROSS_OUT - W_CIRC
W_SUM_WEEKLY = pr_hub["net_one_way"] + HUB_NET

O["otc"] = {
    "gross_out": OTC_GROSS_OUT, "gross_in": OTC_GROSS_IN,
    "circular": HUB_CIRC, "net_one_way": HUB_NET,
    "circ_pct": 100*HUB_CIRC/hub["gross_out"],
    "upbit_feed": UPBIT_FEED, "upbit_return": UPBIT_RETURN,
    "net_by_venue": hub_net,
    "outbound_by_venue": hub["outbound_by_venue"], "inbound_by_venue": hub["inbound_by_venue"],
    "prev_net": pr_hub["net_one_way"], "prev_gross": pr_hub["gross_out"],
    "prev_upbit_feed": abs(pr_hub["inbound_by_venue"].get("UPbit",0)),
    "peak": {"gross": peak["gross_out"], "circ": peak["circular"], "net": peak["net_one_way"],
             "circ_pct": 100*peak["circular"]/peak["gross_out"], "net_by_venue": peak["net_by_venue"]},
    "run16": {"gross": r16["gross_out"], "circ": r16["circular"], "net": r16["net_one_way"],
              "circ_pct": 100*r16["circular"]/r16["gross_out"], "net_by_venue": r16["net_by_venue"]},
    "run18": {"gross": r18["gross_out"], "circ": r18["circular"], "net": r18["net_one_way"],
              "circ_pct": 100*r18["circular"]/r18["gross_out"], "net_by_venue": r18["net_by_venue"]},
    "wave": {"window": "2026-08-03..2026-08-17", "gross_out": W_GROSS_OUT, "gross_in": W_GROSS_IN,
             "circular": W_CIRC, "circ_pct": 100*W_CIRC/W_GROSS_OUT, "net_one_way": W_NET,
             "sum_of_weekly_nets": W_SUM_WEEKLY, "weekly_frame_overstatement": W_SUM_WEEKLY-W_NET,
             "overstatement_pct": 100*(W_SUM_WEEKLY-W_NET)/W_NET,
             "net_by_venue": {v: w_out.get(v,0)-w_in.get(v,0) for v in w_venues},
             "outbound_by_venue": w_out, "inbound_by_venue": w_in},
    "desk_balance": (bal_of(UPBIT_DESK) or 0) + (bal_of(DIST_DESK) or 0),
    "desk_balance_prev": 63794.746,
}
O["otc"]["desk_delta"] = O["otc"]["desk_balance"] - O["otc"]["desk_balance_prev"]

# gross + net series
O["otc"]["gross_series"] = {"run12":44335.0,"run13":66128.0,"run14":186124.0,"run15":506053.0,
    "run16":1100791.0,"run17":1284688.0,"run18":313173.0,"run19":301498.0,"run20":604086.0,
    "run21":OTC_GROSS_OUT}
O["otc"]["net_series"] = {"run16":r16["net_one_way"],"run17_peak":peak["net_one_way"],
    "run18":r18["net_one_way"],"run19":61435.0,"run20":pr_hub["net_one_way"],"run21":HUB_NET}
O["otc"]["circ_series_pct"] = {"run16":100*r16["circular"]/r16["gross_out"],
    "run17_peak":100*peak["circular"]/peak["gross_out"],
    "run18":100*r18["circular"]/r18["gross_out"],"run19":80.0,
    "run20":100*pr_hub["circular"]/pr_hub["gross_out"],"run21":100*HUB_CIRC/hub["gross_out"]}

# ---------------- demand instruments ----------------
MEGA = "erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"
CB_ROUTING_B = "erd1lgdltequh7627rtlacmcp6p5vec7zmu2rxhu7pjwvcja8f4a9gqq9vcc70"
MW_PREV = 1099059.2951787356
BID = sum(int(t.get("value","0"))/1e18 for t in D.get("mega_whale_inbound",[]) if int(t.get("value","0"))>0)
CB_IN = sum(int(t.get("value","0"))/1e18 for t in D.get("cb_routing_b_in",[]) if int(t.get("value","0"))>0)
mw_bal = bal_of(MEGA) or MW_PREV
cb_bal = bal_of(CB_ROUTING_B) or 0
O["bid"] = {"absorbed": BID, "mega_balance": mw_bal, "mega_change": mw_bal-MW_PREV,
            "mega_txs": len(D.get("mega_whale_inbound",[]))+len(D.get("mega_whale_outbound",[])),
            "cb_routing_balance": cb_bal, "cb_routing_inflow": CB_IN,
            "weeks_at_zero_in_last_four": 3}

# ---------------- exchange flows ----------------
ta = D["top_accounts"]
cur_top = {x["address"]: int(x["balance"])/1e18 for x in ta}
prev_top = {x["address"]: x["balance_egld"] for x in prev["top_accounts"]}
N_prev = len(prev["top_accounts"])
def entity_of(a):
    l = lab(a)
    if "Binance" in l: return "Binance"
    if "Coinbase" in l: return "Coinbase"
    if "Crypto.com" in l: return "Crypto.com"
    for e in ["UPbit","Bybit","MEXC","Bitget","Gate.io","KuCoin","Bitfinex","Tokero"]:
        if e in l: return e
    return None
BAD = {"erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp29trp6qsl2gdvvz2eqra76xc",
       "erd1ty4pvmjtl3mnsjvnsxqkm3xqm4dm7ppgz9sh4nk4tqvlmw0jyggqzn4mdc"}
by_exchange = []; ent_cur = {}; ent_prev = {}; ent_w = {}; no_prior = []
exch = [a for a,c in cat_map.items() if c=="exchange"]
for a in exch:
    if a in BAD: continue
    e = entity_of(a)
    if not e: continue
    cur = bal_of(a)
    if cur is None: cur = cur_top.get(a)
    pb = prev_top.get(a)
    if cur is None: continue
    if pb is None:
        no_prior.append({"entity":e,"label":lab(a),"balance":cur}); continue
    ent_w[e] = ent_w.get(e,0)+1
    ent_cur[e] = ent_cur.get(e,0)+cur
    ent_prev[e] = ent_prev.get(e,0)+pb
    by_exchange.append({"exchange":lab(a),"change_egld":cur-pb,"pct":(100*(cur-pb)/pb if pb else None)})
by_exchange.sort(key=lambda x:-abs(x["change_egld"]))
net_total = sum(ent_cur[e]-ent_prev[e] for e in ent_cur)
O["exch"] = {"by_exchange":by_exchange, "ent_cur":ent_cur, "ent_prev":ent_prev, "ent_w":ent_w,
             "no_prior":no_prior, "net_total":net_total,
             "total_cur":sum(ent_cur.values()), "total_prev":sum(ent_prev.values())}

# Binance custody
CUSTODY = "erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"
cust_bal = bal_of(CUSTODY) or 0
cust_in = [{"value":int(t.get("value","0"))/1e18,"from":lab(t["sender"]),"from_addr":t["sender"],
            "fn":t.get("function"),"ts":t.get("timestamp")} for t in D.get("binance_custody_in",[])]
cust_out = [{"value":int(t.get("value","0"))/1e18,"to":lab(t["receiver"]),"fn":t.get("function"),
             "ts":t.get("timestamp")} for t in D.get("binance_custody_out",[])]
O["custody"] = {"balance":cust_bal,"prev":prev["exchange_balances"]["Binance Staking"],
                "change":cust_bal-prev["exchange_balances"]["Binance Staking"],
                "from_peak":cust_bal-3512650.2283337726,"inbound":cust_in,"outbound":cust_out}

# ---------------- whale tiers ----------------
def tiers(top):
    items = [(a,b) for a,b in top.items() if cat(a)!="system"]
    return ([x for x in items if x[1]>1e6], [x for x in items if 1e5<=x[1]<=1e6],
            [x for x in items if 1e4<=x[1]<1e5])
cur_trim = dict(sorted(cur_top.items(), key=lambda kv:-kv[1])[:N_prev])
cm_, cl_, cmid_ = tiers(cur_trim); pm_, pl_, pmid_ = tiers(prev_top)
def tot(x): return sum(b for _,b in x)
def tierblock(c,p,th):
    ct, pt = tot(c), tot(p)
    return {"threshold_egld":th,"count_current":len(c),"count_previous":len(p),
            "total_balance_egld":ct,"previous_total_balance_egld":pt,
            "net_change_egld":ct-pt,"net_change_pct":(100*(ct-pt)/pt if pt else None)}
O["whale_tiers"] = {"mega_whales":tierblock(cm_,pm_,1000000),
                    "large_whales":tierblock(cl_,pl_,100000),
                    "mid_whales":tierblock(cmid_,pmid_,10000)}

# wallet changes
changes = []
for a,b in cur_top.items():
    if a in prev_top and cat(a)!="system":
        pb = prev_top[a]; d = b-pb; pctc = 100*d/pb if pb else None
        if abs(d)>2000 or (pctc is not None and abs(pctc)>5):
            tier = "mega_whale" if b>1e6 else "large_whale" if b>=1e5 else "mid_whale" if b>=1e4 else None
            changes.append({"address":a,"label":lab(a),"category":cat(a),"tier":tier,
                "balance_current_egld":b,"balance_previous_egld":pb,"change_egld":d,"change_pct":pctc})
changes.sort(key=lambda x:-abs(x["change_egld"]))
O["wallet_changes"] = changes[:18]

# ---------------- large transactions ----------------
router_set = set(kn.get("exchange_routers",{}).keys())
otc_set = set(a for a,m in kn.get("unlabeled_whales",{}).items() if m.get("subcategory")=="otc")
def classify(s,r):
    sl,rl = lab(s),lab(r); sc,rc = cat(s),cat(r)
    se,re_ = sc=="exchange", rc=="exchange"
    sro,rro = s in router_set, r in router_set
    so = s in otc_set or "OTC" in sl; ro = r in otc_set or "OTC" in rl
    sw = "Whale" in sl; rw = "Whale" in rl
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
pools = [info.get("txs") for info in acc.values()]
for v in D["desk_outbound_paged"].values(): pools.append(v.get("txs"))
for v in D["desk_inbound_paged"].values(): pools.append(v.get("txs"))
for v in D.get("exchange_outbound_paged",{}).values(): pools.append(v.get("txs"))
pools += [D.get("binance_custody_in"), D.get("binance_custody_out"),
          D.get("mega_whale_inbound"), D.get("mega_whale_outbound"),
          D.get("whale_i_inbound_30d"), D.get("whale_i_outbound_30d")]
W_START_TS = int(datetime(2026,8,10,tzinfo=timezone.utc).timestamp())
for txs in pools:
    if not isinstance(txs,list): continue
    for t in txs:
        if not isinstance(t,dict): continue
        h = t.get("txHash")
        if not h or h in seen: continue
        if (t.get("timestamp") or 0) < W_START_TS: continue
        try: v = int(t.get("value","0"))/1e18
        except: v = 0
        if v < 1000: continue
        seen.add(h)
        s = t.get("sender"); r = t.get("receiver"); tsx = t.get("timestamp")
        bigtx.append({"hash":h,
            "timestamp":datetime.fromtimestamp(tsx,tz=timezone.utc).isoformat() if tsx else None,
            "sender":s,"sender_label":lab(s),"receiver":r,"receiver_label":lab(r),
            "value_egld":v,"value_usd":v*price,"flow_type":classify(s,r)})
bigtx.sort(key=lambda x:-x["value_egld"])
O["large_transactions"] = bigtx[:25]

# ---------------- withdrawal breadth ----------------
PIPELINE = set(DESK_SET)|router_set|set(D["otc_hub_trace"]["inbound"])|set(D["otc_hub_trace"]["outbound"])
b_raw, b_clean = {}, {}
for a,v in D.get("exchange_outbound_paged",{}).items():
    for t in v.get("txs",[]):
        try: val = int(t.get("value","0"))/1e18
        except: val = 0
        if val < 1000: continue
        r = t.get("receiver")
        if cat(r)=="exchange": continue
        b_raw[r] = b_raw.get(r,0)+val
        if r in PIPELINE or "OTC" in lab(r) or "Router" in lab(r) or "Feeder" in lab(r): continue
        b_clean[r] = b_clean.get(r,0)+val
O["breadth"] = {"distinct_recipients_raw":len(b_raw),"total_egld_raw":sum(b_raw.values()),
    "distinct_recipients_ex_pipeline":len(b_clean),"total_egld_ex_pipeline":sum(b_clean.values()),
    "pipeline_share_pct":(100*(1-sum(b_clean.values())/sum(b_raw.values())) if b_raw else None)}
O["breadth_top"] = sorted(({"address":a,"label":lab(a),"egld":v} for a,v in b_clean.items()),
                          key=lambda x:-x["egld"])[:5]

json.dump(O, open("/tmp/run21w/derived.json","w"), indent=1)
print("STAGE 1 OK")
print("otc:", {k:round(v,1) if isinstance(v,(int,float)) else "..." for k,v in O["otc"].items() if isinstance(v,(int,float))})
print("wave:", {k:round(v,1) for k,v in O["otc"]["wave"].items() if isinstance(v,(int,float))})
print("bid:", O["bid"])
print("net exch flow:", round(net_total,1), "no_prior:", [x["label"] for x in no_prior])
print("custody:", {k:v for k,v in O["custody"].items() if not isinstance(v,list)})
print("breadth:", O["breadth"])
print("large tx:", len(O["large_transactions"]), "top:", [(round(t["value_egld"]), t["sender_label"][:18], t["receiver_label"][:18]) for t in O["large_transactions"][:6]])
