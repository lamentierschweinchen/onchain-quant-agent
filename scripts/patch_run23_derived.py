#!/usr/bin/env python3
"""Run #23: fold followup_2026-08-31.json into derived.json.

The main collector lost four things to an invalid hardcoded address (HTTP 400)
and transient HTTP 429s. The followup re-queried them with backoff; this patch
replaces the empty/zero values rather than letting them stand.
"""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-08-31"
O=json.load(open("/tmp/run23w/derived.json"))
F=json.load(open(f"{REPO}/data/collected/followup_{RD}.json"))
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
lm={};cm={}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"):
                lm[a]=m.get("name","Unknown"); cm[a]=m.get("category","unknown")
def lab(a): return lm.get(a,"Unknown")

UPBIT_DESK="erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
DIST_DESK="erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"

# ---- desk balances (authoritative, re-read after the drain) ---------------
db=F.get("desk_balances") or {}
desk_bal=sum((v.get("balance_egld") or 0) for v in db.values())
if desk_bal>0:
    O["otc"]["desk_bal"]=desk_bal
    O["otc"]["desk_delta"]=desk_bal-O["otc"]["prev_desk"]

# ---- wave #3 extended netting --------------------------------------------
w=F.get("wave3ext")
if w and w.get("venue_netting"):
    vnw=w["venue_netting"]
    sum_weekly=prev["otc_net_one_way_series"]["run22"]+O["otc"]["net_one_way"]
    O["otc"]["wave"]={"window":"2026-08-17..2026-08-31","gross_out":vnw["gross_out"],
      "gross_in":vnw["gross_in"],"circular":vnw["circular"],
      "circ_pct":100*vnw["circular"]/vnw["gross_out"] if vnw["gross_out"] else 0,
      "net_one_way":vnw["net_one_way"],"sum_weekly":sum_weekly,
      "overstate_egld":sum_weekly-vnw["net_one_way"],
      "overstate_pct":100*(sum_weekly-vnw["net_one_way"])/vnw["net_one_way"] if vnw["net_one_way"] else 0,
      "net_by_venue":vnw["net_by_venue"],"out_by_venue":vnw["outbound_by_venue"],
      "in_by_venue":vnw["inbound_by_venue"],
      "straddle_detected":True}

# ---- Binance hot / custody ------------------------------------------------
hot=F.get("binance_hot") or {}
hot_main="erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets"
if hot:
    O["custody"]["hot_balance"]=hot.get(hot_main,{}).get("balance_egld")
    O["custody"]["hot_entity_balance"]=sum((v.get("balance_egld") or 0) for v in hot.values())
if F.get("custody_balance_egld") is not None:
    O["custody"]["balance"]=F["custody_balance_egld"]
    O["custody"]["delta"]=F["custody_balance_egld"]-O["custody"]["previous"]
traces=F.get("binance_hot_big_traces") or {}
rows=[]
for r,t in sorted(traces.items(), key=lambda x:-x[1]["amount"]):
    rows.append({"receiver":r,"label":t["label"],"amount":t["amount"],
                 "receiver_balance":t["balance_egld"],"nonce":t.get("nonce"),
                 "reaches_desk_directly":t["reaches_desk_directly"],
                 "hop2_to_desk":t["hop2_to_desk"],"hop2_top":t["hop2_top"]})
O["custody"]["hot_big_outbound"]=rows
O["custody"]["hot_to_desk_total"]=sum(
    (r["amount"] if r["reaches_desk_directly"] and r["hop2_to_desk"]==0 else r["hop2_to_desk"])
    for r in rows)
O["custody"]["hot_to_custody_egld"]=sum(r["amount"] for r in rows
                                        if "Binance Staking" in (r["label"] or ""))
O["custody"]["custody_out_total"]=sum(x["egld"] for x in O["custody"]["out"])
O["custody"]["custody_in_total"]=sum(x["egld"] for x in O["custody"]["in"])
# the 300,000 leg dated 2026-08-24 sits on BOTH windows' boundary; run #22 already booked it
O["custody"]["boundary_double_count_egld"]=300000.0
O["custody"]["custody_out_this_window"]=O["custody"]["custody_out_total"]-300000.0

# ---- the 229,865 unbond ---------------------------------------------------
u=F.get("unbond") or {}
O["unbond"]["balance"]=u.get("balance_egld")
O["unbond"]["pending"]=[{"contract":p["contract"],"amount_egld":p["amount_egld"],
                         "seconds_remaining":p["seconds"],
                         "days_remaining":round((p["seconds"] or 0)/86400,2)}
                        for p in (u.get("pending") or [])]
O["unbond"]["pending_total"]=u.get("pending_total") or 0
O["unbond"]["active_stake"]=u.get("active_stake") or 0
O["unbond"]["outbound"]=[{"to":t["receiver"],"label":lab(t["receiver"]),
                          "egld":int(t.get("value","0"))/1e18,"ts":t.get("timestamp")}
                         for t in (u.get("out_7d") or []) if int(t.get("value","0"))>0]
O["unbond"]["outbound_total"]=sum(x["egld"] for x in O["unbond"]["outbound"])
fns={}
for t in (u.get("all_out") or []):
    if isinstance(t,dict):
        f=t.get("function") or "(transfer)"; fns[f]=fns.get(f,0)+1
O["unbond"]["functions"]=fns
O["unbond"]["moved"]=bool(O["unbond"]["outbound_total"]>0)

# ---- mega whale -----------------------------------------------------------
mw=F.get("mega_whale") or {}
if mw.get("balance_egld") is not None:
    O["bid"]["mega_bal"]=mw["balance_egld"]
    O["bid"]["mega_delta"]=mw["balance_egld"]-O["bid"]["mega_prev"]
    O["bid"]["absorbed"]=max(0.0,O["bid"]["mega_delta"])
    O["bid"]["mega_txs"]=len(mw.get("in") or [])+len(mw.get("out") or [])

O["_followup_repairs"]=[
 "BINANCE_HOT was hardcoded in collect_run23.py with an INVALID bech32 checksum -> HTTP 400 -> paged_txs returned [] -> '0 outbound recipients >=10K'. Re-queried with the three valid Binance.com wallets.",
 "HTTP 429 during the heavy all-provider pass nulled /accounts/{unbond}/info, /delegation and the outbound scan. Re-queried with exponential backoff.",
 "The wave-window (Aug 17-31) desk pagination returned zero txs on the first pass (transient). Re-run clean: 214/238 and 178/286 txs.",
 "Mega Whale absorber in/out scans returned [] for the same reason; re-queried and confirmed genuinely zero.",
]
json.dump(O,open("/tmp/run23w/derived.json","w"),indent=1,default=str)
print("patched.")
print("desk_bal",round(O["otc"]["desk_bal"]),"delta",round(O["otc"]["desk_delta"]))
print("wave:",{k:(round(v) if isinstance(v,(int,float)) else v) for k,v in O["otc"]["wave"].items() if k in ("gross_out","circular","circ_pct","net_one_way","sum_weekly","overstate_egld","overstate_pct")})
print("custody bal",round(O["custody"]["balance"]),"delta",round(O["custody"]["delta"]),
      "hot",round(O["custody"]["hot_balance"] or 0),"hot_entity",round(O["custody"]["hot_entity_balance"] or 0))
print("hot->desk total",round(O["custody"]["hot_to_desk_total"]),"hot->custody",round(O["custody"]["hot_to_custody_egld"]))
print("unbond bal",O["unbond"]["balance"],"pending",round(O["unbond"]["pending_total"]),"moved",O["unbond"]["moved"],"fns",O["unbond"]["functions"])
print("mega",O["bid"]["mega_bal"],"delta",O["bid"]["mega_delta"],"txs",O["bid"]["mega_txs"])
