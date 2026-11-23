#!/usr/bin/env python3
"""Run #38 ad-hoc traces (run AFTER every other pass; shares the API rate limit). Writes D["run38_adhoc"].
(A) Binance hot wallet 2 erd1ts0g6r0h: per-day customer flow in the window (resolves binance-backlog-fades).
(B) erd1ylwusw (2.18M exchange wallet) and Binance Staking custody: every value-bearing leg in the window (binance-reserve-stays).
(C) One hop past hot wallet 2: where its 15 largest receivers sent EGLD next (cross-venue relocation share).
(D) erd1rlqdj67qxp: funding since its first transaction (Oct 29) and any further clip to Binance (run #37 rec #5).
(E) Binance's delegation footprint: custody /delegation and the binance-identity providers' stake vs last week (run #37 rec #6).
(F) Provider movers: delegate calls >= 1,000 EGLD into the three largest movers.
"""
import json, time, urllib.request, urllib.parse, datetime as dt
from collections import Counter
REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"; SNAP = f"{REPO}/data/collected/2026-11-23.json"
D = json.load(open(SNAP)); API = "https://api.multiversx.com"; WIN = D["_period"]["window_start_ts"]
kn = json.load(open(f"{REPO}/data/known-addresses.json")); LM = {}
for s, e in kn.items():
    if isinstance(e, dict):
        for a, m in e.items():
            if isinstance(m, dict) and a.startswith("erd1"): LM[a] = (m.get("name"), m.get("category"))
def lab(a): return (LM.get(a) or [None])[0]
def cat(a): return (LM.get(a) or [None, None])[1]
def get(p, **q):
    url = API + p + ("?" + urllib.parse.urlencode(q) if q else ""); d = 1.5
    for a in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "intel-agent/38-adhoc"}), timeout=40) as r: return json.loads(r.read().decode())
        except Exception as e:
            if a == 6: return {"__error__": str(e)}
            time.sleep(d); d = min(d * 2, 30)
def pall(a, side, after, cap=6000):
    out, frm = [], 0
    while frm < cap:
        b = get(f"/accounts/{a}/transactions", size=50, **{"from": frm}, after=after, order="asc", status="success", **{side: a})
        time.sleep(0.4)
        if not isinstance(b, list): return out, b.get("__error__")
        out += b
        if len(b) < 50: return out, None
        frm += 50
    return out, "cap"
def eg(t): return int(t.get("value", "0")) / 1e18
def day(t): return dt.datetime.fromtimestamp(t["timestamp"], dt.timezone.utc).strftime("%Y-%m-%d")
def info(a):
    i = get(f"/accounts/{a}"); time.sleep(0.3)
    return {"balance_egld": int(i.get("balance", "0")) / 1e18, "nonce": i.get("nonce"), "shard": i.get("shard")} if isinstance(i, dict) and "balance" in i else {"error": str(i)[:120]}
def first_tx(a):
    b = get(f"/accounts/{a}/transactions", size=1, order="asc"); time.sleep(0.3)
    return b[0]["timestamp"] if isinstance(b, list) and b else None
A = {}
HOT2 = "erd1ts0g6r0hn2tme5t53epyp9lurm7893v52c30xp5zur05mm92r4hqx6jd26"
YLW = "erd1ylwuswz9zuk4acuq4aa6d0x9ys293yhlpwg6vpuwntndyej4u44q896zlz"
OLD = "erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets"
CUST = "erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"
BINSET = {HOT2, YLW, OLD, CUST, "erd1v4ms58e22zjcp08suzqgm9ajmumwxcy4hfkdc23gvynnegjdflmsj6gmaq"}

# (A) hot wallet 2 in the window
o, e1 = pall(HOT2, "sender", WIN, cap=8000); i, e2 = pall(HOT2, "receiver", WIN, cap=8000)
days = {}
def drow(d): return days.setdefault(d, {"wd_n": 0, "wd_egld": 0.0, "wd_receivers": set(), "dep_n": 0, "dep_egld": 0.0, "dep_senders": set(), "fund_egld": 0.0, "to_binance_egld": 0.0})
for t in o:
    if eg(t) < 0.01: continue
    r = drow(day(t))
    if t["receiver"] in BINSET: r["to_binance_egld"] += eg(t); continue
    r["wd_n"] += 1; r["wd_egld"] += eg(t); r["wd_receivers"].add(t["receiver"])
for t in i:
    if eg(t) < 0.01: continue
    r = drow(day(t))
    if t["sender"] in BINSET: r["fund_egld"] += eg(t)
    else: r["dep_n"] += 1; r["dep_egld"] += eg(t); r["dep_senders"].add(t["sender"])
wd = [t for t in o if eg(t) >= 0.01 and t["receiver"] not in BINSET]
ext_in = [t for t in i if eg(t) >= 0.01 and t["sender"] not in BINSET]
recv = Counter(); [recv.update({t["receiver"]: eg(t)}) for t in wd]
send = Counter(); [send.update({t["sender"]: eg(t)}) for t in ext_in]
A["hot2"] = {"address": HOT2, "info": info(HOT2), "errors": [e1, e2], "out_txs": len(o), "in_txs": len(i),
    "withdrawals_n": len(wd), "withdrawals_egld": sum(eg(t) for t in wd), "distinct_receivers": len(recv),
    "deposits_n": len(ext_in), "deposits_egld": sum(eg(t) for t in ext_in), "distinct_depositors": len(send),
    "funding_from_binance_egld": sum(eg(t) for t in i if t["sender"] in BINSET),
    "funding_legs": [{"from": t["sender"], "label": lab(t["sender"]), "egld": eg(t), "ts": t["timestamp"]} for t in i if t["sender"] in BINSET and eg(t) > 0],
    "sent_to_binance_egld": sum(eg(t) for t in o if t["receiver"] in BINSET),
    "sent_to_binance_legs": [{"to": t["receiver"], "label": lab(t["receiver"]), "egld": eg(t), "ts": t["timestamp"]} for t in o if t["receiver"] in BINSET and eg(t) > 0],
    "top_depositors": [{"from": k, "label": lab(k), "egld": v} for k, v in send.most_common(12)],
    "top_receivers": [{"to": k, "label": lab(k), "cat": cat(k), "egld": v} for k, v in recv.most_common(15)],
    "median_withdrawal_egld": sorted(eg(t) for t in wd)[len(wd) // 2] if wd else None,
    "days": {d: {**{k: v for k, v in r.items() if not isinstance(v, set)}, "distinct_withdrawers": len(r["wd_receivers"]), "distinct_depositors": len(r["dep_senders"])} for d, r in sorted(days.items())}}
print("[hot2]", json.dumps({k: v for k, v in A["hot2"].items() if k not in ("days", "top_receivers", "top_depositors", "funding_legs", "sent_to_binance_legs")}, default=str))
print("[hot2 days]", {d: (r["wd_n"], round(r["wd_egld"]), r["dep_n"], round(r["dep_egld"]), round(r["fund_egld"])) for d, r in A["hot2"]["days"].items()})
print("[hot2 funding]", [(x["label"], round(x["egld"])) for x in A["hot2"]["funding_legs"]])

# (B) erd1ylwusw + custody + old hot wallet
for key, ad in (("ylw", YLW), ("custody", CUST), ("old_hot", OLD)):
    oo, ea = pall(ad, "sender", WIN); ii, eb = pall(ad, "receiver", WIN)
    A[key] = {"address": ad, "info": info(ad), "errors": [ea, eb],
        "out": [{"to": t["receiver"], "label": lab(t["receiver"]), "egld": eg(t), "ts": t["timestamp"], "fn": t.get("function")} for t in oo if eg(t) > 0 or t.get("function")][:40],
        "in": [{"from": t["sender"], "label": lab(t["sender"]), "egld": eg(t), "ts": t["timestamp"], "fn": t.get("function")} for t in ii if eg(t) > 0][:40],
        "out_egld": sum(eg(t) for t in oo), "out_to_binance_egld": sum(eg(t) for t in oo if t["receiver"] in BINSET),
        "out_outside_binance_egld": sum(eg(t) for t in oo if t["receiver"] not in BINSET),
        "delegated_egld": sum(eg(t) for t in oo if (t.get("function") or "") in ("delegate", "stake")),
        "in_egld": sum(eg(t) for t in ii), "in_external_egld": sum(eg(t) for t in ii if t["sender"] not in BINSET and eg(t) >= 0.01),
        "in_external_n": sum(1 for t in ii if t["sender"] not in BINSET and eg(t) >= 0.01)}
    print(f"[{key}]", A[key]["info"], "out", round(A[key]["out_egld"]), "to-bin", round(A[key]["out_to_binance_egld"]), "outside", round(A[key]["out_outside_binance_egld"]), "deleg", round(A[key]["delegated_egld"]), "in", round(A[key]["in_egld"]), "ext-in", round(A[key]["in_external_egld"]))

# (C) one hop past hot wallet 2's top receivers
hop = {}
for r_ in A["hot2"]["top_receivers"]:
    a = r_["to"]
    oo, _ = pall(a, "sender", WIN, cap=400)
    dst = Counter(); [dst.update({t["receiver"]: eg(t)}) for t in oo if eg(t) >= 1]
    by = Counter()
    for k, v in dst.items():
        c_ = cat(k); l_ = lab(k) or ""
        cls = ("exchange:" + l_.split(" ")[0]) if c_ == "exchange" else ("staking" if k.startswith("erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq") or c_ == "staking" else ("defi" if k.startswith("erd1qqqqqqqqqqqqqpgq") else "wallet"))
        by[cls] += v
    hop[a] = {"received_from_hot2": r_["egld"], "label": r_["label"], "info": info(a), "out_egld": sum(dst.values()),
              "by_class": dict(by), "dests": [{"to": x, "label": lab(x), "egld": y} for x, y in dst.most_common(5)]}
    print("[hop]", a[:14], round(r_["egld"]), r_["label"], {k: round(v) for k, v in by.items()})
A["hot2_onehop"] = hop

# (D) erd1rlqdj67qxp
RLQ = next((x["address"] for x in D["top_accounts"] if x["address"].startswith("erd1rlqdj67qxp")), None) or \
      next(a for a in LM if a.startswith("erd1rlqdj67qxp"))
ft = first_tx(RLQ)
oo, _ = pall(RLQ, "sender", (ft or WIN) - 1, cap=600); ii, _ = pall(RLQ, "receiver", (ft or WIN) - 1, cap=600)
A["rlq"] = {"address": RLQ, "info": info(RLQ), "first_tx_ts": ft,
    "in_all": [{"from": t["sender"], "label": lab(t["sender"]), "egld": eg(t), "fn": t.get("function"), "ts": t["timestamp"]} for t in ii if eg(t) >= 1][:30],
    "out_all": [{"to": t["receiver"], "label": lab(t["receiver"]), "egld": eg(t), "fn": t.get("function"), "ts": t["timestamp"]} for t in oo if eg(t) >= 1 or t.get("function")][:30],
    "out_window": [{"to": t["receiver"], "label": lab(t["receiver"]), "egld": eg(t), "fn": t.get("function"), "ts": t["timestamp"]} for t in oo if t["timestamp"] >= WIN and (eg(t) >= 1 or t.get("function"))]}
# funder one hop back
fund = Counter(); [fund.update({x["from"]: x["egld"]}) for x in A["rlq"]["in_all"]]
A["rlq"]["funders"] = []
for f_, v in fund.most_common(3):
    fi, _ = pall(f_, "receiver", (ft or WIN) - 30 * 86400, cap=200)
    src = Counter(); [src.update({t["sender"]: eg(t)}) for t in fi if eg(t) >= 100]
    A["rlq"]["funders"].append({"address": f_, "label": lab(f_), "egld_to_rlq": v, "info": info(f_), "first_tx_ts": first_tx(f_),
                                "sources": [{"from": k, "label": lab(k), "egld": y} for k, y in src.most_common(5)]})
print("[rlq]", A["rlq"]["info"], A["rlq"]["first_tx_ts"], "IN", [(x["from"][:12], x["label"], round(x["egld"])) for x in A["rlq"]["in_all"][:8]],
      "OUTwin", [(x["to"][:12], x["label"], round(x["egld"]), x["fn"]) for x in A["rlq"]["out_window"][:8]])
print("[rlq funders]", [(f["address"][:14], f["label"], round(f["egld_to_rlq"]), [(s["from"][:12], s["label"], round(s["egld"])) for s in f["sources"][:3]]) for f in A["rlq"]["funders"]])

# (E) Binance delegation footprint
cd = get(f"/accounts/{CUST}/delegation"); time.sleep(0.3)
yd = get(f"/accounts/{YLW}/delegation"); time.sleep(0.3)
prov_prev = {x["address"]: x for x in json.load(open(f"{REPO}/data/previous.json"))["staking_providers"]}
bp = []
for x in D["providers"]:
    idn = (x.get("identity") or "").lower()
    if "binance" in idn:
        o_ = prov_prev.get(x["provider"])
        bp.append({"provider": x["provider"], "identity": x.get("identity"), "locked_egld": int(x["locked"]) / 1e18,
                   "previous_locked_egld": o_["locked_egld"] if o_ else None, "num_users": x.get("numUsers"),
                   "previous_users": o_["num_delegators"] if o_ else None})
A["binance_delegation"] = {"custody_delegation": cd, "ylw_delegation": yd, "binance_identity_providers": bp}
print("[bin-deleg]", json.dumps(cd, default=str)[:600], json.dumps(yd, default=str)[:200], bp)

# (F) provider movers
pm = {}
for m in sorted(D.get("provider_movers") or [], key=lambda m: -abs(m["delta_egld"]))[:3]:
    ii, _ = pall(m["address"], "receiver", WIN, cap=1500)
    big = sorted(({"from": t["sender"], "label": lab(t["sender"]), "egld": eg(t), "fn": t.get("function"), "ts": t["timestamp"]} for t in ii if eg(t) >= 1000), key=lambda x: -x["egld"])[:8]
    pm[m.get("identity") or m["address"]] = {"address": m["address"], "delta_egld": m["delta_egld"], "users": m.get("users"), "prev_users": m.get("prev_users"), "big_inbound": big}
    print("[prov]", m.get("identity"), round(m["delta_egld"]), [(x["from"][:14], x["label"], round(x["egld"]), x["fn"]) for x in big])
A["provider_mover_inbound"] = pm

D2 = json.load(open(SNAP)); D2["run38_adhoc"] = A
json.dump(D2, open(SNAP, "w"))
print("written")
