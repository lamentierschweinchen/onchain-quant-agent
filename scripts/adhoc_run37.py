#!/usr/bin/env python3
"""Run #37 ad-hoc traces (run AFTER every other pass; shares the API rate limit). Writes D["run37_adhoc"].
(A) erd1ts0g6r0hn2: wallet funded by Binance Staking custody (20,000) and Binance.com erd1ylwusw (80,300) in the window.
    Full in/out profile, per day, to decide whether it is Binance's new withdrawal hot wallet.
(B) erd1ylwusw (Binance.com, received 2,264,611 from custody): every value-bearing inbound/outbound in the window.
(C) Routers/wallets feeding Bybit and Coinbase this window: where their EGLD came from.
(D) Top-100 movers without a label: erd1rlqdj67qxp (-43,586), erd13yl06g75l2 (new, 16,025), erd1295n68497840 (new, 9,199).
(E) Lookalikes erd1tsddlqzd63 / erd1yl5ksy466z sending zero-value transfers to Binance wallets.
(F) Provider movers: largest delegate calls into lsr0pd0j and mandalastaking.
"""
import json, time, urllib.request, urllib.parse, datetime as dt
from collections import Counter
REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"; SNAP = f"{REPO}/data/collected/2026-11-16.json"
D = json.load(open(SNAP)); API = "https://api.multiversx.com"; WIN = D["_period"]["window_start_ts"]
kn = json.load(open(f"{REPO}/data/known-addresses.json")); LM = {}
for s, e in kn.items():
    if isinstance(e, dict):
        for a, m in e.items():
            if isinstance(m, dict) and a.startswith("erd1"): LM[a] = (m.get("name"), m.get("category"))
def lab(a): return (LM.get(a) or [None])[0]
def get(p, **q):
    url = API + p + ("?" + urllib.parse.urlencode(q) if q else ""); d = 1.5
    for a in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "intel-agent/37-adhoc"}), timeout=40) as r: return json.loads(r.read().decode())
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
NEWHOT = "erd1ts0g6r0hn2tme5t53epyp9lurm7893v52c30xp5zur05mm92r4hqx6jd26"
YLW = "erd1ylwuswz9zuk4acuq4aa6d0x9ys293yhlpwg6vpuwntndyej4u44q896zlz"
OLD = "erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets"
BINSET = {NEWHOT, YLW, OLD, "erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p", "erd1v4ms58e22zjcp08suzqgm9ajmumwxcy4hfkdc23gvynnegjdflmsj6gmaq"}

# (A) new hot wallet: everything since its first transaction
ft = first_tx(NEWHOT)
SINCE = max((ft or WIN) - 1, 1793000000)
o, e1 = pall(NEWHOT, "sender", SINCE); i, e2 = pall(NEWHOT, "receiver", SINCE)
days = {}
for t in o:
    if eg(t) < 0.01: continue
    r = days.setdefault(day(t), {"wd_n": 0, "wd_egld": 0.0, "wd_receivers": set(), "dep_n": 0, "dep_egld": 0.0, "dep_senders": set(), "fund_egld": 0.0})
    r["wd_n"] += 1; r["wd_egld"] += eg(t); r["wd_receivers"].add(t["receiver"])
for t in i:
    if eg(t) < 0.01: continue
    r = days.setdefault(day(t), {"wd_n": 0, "wd_egld": 0.0, "wd_receivers": set(), "dep_n": 0, "dep_egld": 0.0, "dep_senders": set(), "fund_egld": 0.0})
    if t["sender"] in BINSET: r["fund_egld"] += eg(t)
    else: r["dep_n"] += 1; r["dep_egld"] += eg(t); r["dep_senders"].add(t["sender"])
ext_in = [t for t in i if eg(t) >= 0.01 and t["sender"] not in BINSET]
recv = Counter(); [recv.update({t["receiver"]: eg(t)}) for t in o if eg(t) >= 0.01]
send = Counter(); [send.update({t["sender"]: eg(t)}) for t in ext_in]
fns = Counter((t.get("function") or "transfer") for t in o)
A["new_hot"] = {"address": NEWHOT, "info": info(NEWHOT), "first_tx_ts": ft, "errors": [e1, e2], "out_txs": len(o), "in_txs": len(i),
    "out_functions": dict(fns.most_common(6)),
    "out_egld_total": sum(eg(t) for t in o), "out_egld_window": sum(eg(t) for t in o if t["timestamp"] >= WIN),
    "out_n_window": sum(1 for t in o if t["timestamp"] >= WIN and eg(t) >= 0.01),
    "distinct_receivers": len(recv), "funding_from_binance_egld": sum(eg(t) for t in i if t["sender"] in BINSET),
    "funding_legs": [{"from": t["sender"], "label": lab(t["sender"]), "egld": eg(t), "ts": t["timestamp"]} for t in i if t["sender"] in BINSET and eg(t) > 0],
    "external_in_txs": len(ext_in), "external_in_egld": sum(eg(t) for t in ext_in), "external_in_egld_window": sum(eg(t) for t in ext_in if t["timestamp"] >= WIN),
    "external_in_distinct_senders": len(send),
    "top_external_senders": [{"from": k, "label": lab(k), "egld": v} for k, v in send.most_common(12)],
    "top_receivers": [{"to": k, "label": lab(k), "cat": (LM.get(k) or [None, None])[1], "egld": v} for k, v in recv.most_common(15)],
    "to_labelled_exchange_egld": sum(v for k, v in recv.items() if (LM.get(k) or [None, None])[1] in ("exchange", "exchange_router", "router", "exchange_ops")),
    "median_withdrawal_egld": sorted(eg(t) for t in o if eg(t) >= 0.01)[len([1 for t in o if eg(t) >= 0.01]) // 2] if o else None,
    "days": {d: {**{k: v for k, v in r.items() if not isinstance(v, set)}, "distinct_withdrawers": len(r["wd_receivers"]), "distinct_depositors": len(r["dep_senders"])} for d, r in sorted(days.items())}}
print("[new-hot]", json.dumps({k: v for k, v in A["new_hot"].items() if k not in ("days", "top_receivers", "top_external_senders")}, default=str)[:1500])
print("[new-hot days]", {d: (r["wd_n"], round(r["wd_egld"]), r["dep_n"], round(r["dep_egld"]), round(r["fund_egld"])) for d, r in A["new_hot"]["days"].items()})
print("[new-hot top recv]", [(x["to"][:14], x["label"], round(x["egld"])) for x in A["new_hot"]["top_receivers"]])
print("[new-hot ext senders]", [(x["from"][:14], x["label"], round(x["egld"])) for x in A["new_hot"]["top_external_senders"]])

# (B) erd1ylwusw in the window
o2, e3 = pall(YLW, "sender", WIN); i2, e4 = pall(YLW, "receiver", WIN)
A["binance_ylw"] = {"address": YLW, "info": info(YLW), "errors": [e3, e4],
    "out": [{"to": t["receiver"], "label": lab(t["receiver"]), "egld": eg(t), "ts": t["timestamp"], "fn": t.get("function")} for t in o2],
    "in": [{"from": t["sender"], "label": lab(t["sender"]), "egld": eg(t), "ts": t["timestamp"]} for t in i2],
    "external_in_egld": sum(eg(t) for t in i2 if t["sender"] not in BINSET), "external_in_n": sum(1 for t in i2 if t["sender"] not in BINSET and eg(t) >= 0.01)}
print("[ylw]", A["binance_ylw"]["info"], len(o2), len(i2), A["binance_ylw"]["external_in_egld"])
# does the old hot wallet's deposit side show anything at all?
oi, e5 = pall(OLD, "receiver", WIN)
A["old_hot_inbound_window"] = {"n": len(oi), "value_n": sum(1 for t in oi if eg(t) >= 0.01), "egld": sum(eg(t) for t in oi), "error": e5}
print("[old-hot]", A["old_hot_inbound_window"])

# (C) feeders of Bybit and Coinbase
FEED = {"bybit_router": "erd1ljlcx0wf", "bybit_dep2": "erd12h90evzx90", "coinbase_seller": "erd1tx933j8r", "gate_dep": "erd1n6vyn7p30y", "kucoin_dep": "erd18g8sa9jd3k", "gate_withdrawer": "erd1nr0t8uaq50", "mexc_withdrawer": "erd1mh7spsdcwx"}
full = {}
for a, v in D["exchange_rails"].items():
    for side in ("in", "out"):
        for cp in v[side]["by_cp_7d"]:
            for k, pre in FEED.items():
                if cp.startswith(pre): full[k] = cp
fd = {}
for k, a in full.items():
    oo, _ = pall(a, "sender", WIN, cap=400); ii, _ = pall(a, "receiver", WIN, cap=400)
    src = Counter(); [src.update({t["sender"]: eg(t)}) for t in ii if eg(t) >= 1]
    dst = Counter(); [dst.update({t["receiver"]: eg(t)}) for t in oo if eg(t) >= 1]
    fd[k] = {"address": a, "label": lab(a), "info": info(a), "in_egld": sum(src.values()), "out_egld": sum(dst.values()),
             "sources": [{"from": x, "label": lab(x) or ("NEW BINANCE HOT" if x == NEWHOT else None), "egld": y} for x, y in src.most_common(6)],
             "dests": [{"to": x, "label": lab(x) or ("NEW BINANCE HOT" if x == NEWHOT else None), "egld": y} for x, y in dst.most_common(6)],
             "fns_out": dict(Counter((t.get("function") or "transfer") for t in oo).most_common(5))}
    print("[feed]", k, a[:14], round(fd[k]["in_egld"]), round(fd[k]["out_egld"]), [(s["from"][:12], s["label"], round(s["egld"])) for s in fd[k]["sources"][:4]], [(s["to"][:12], s["label"], round(s["egld"])) for s in fd[k]["dests"][:4]])
A["venue_feeders"] = fd

# (D) unlabelled top-100 movers
top = {x["address"]: int(x["balance"]) / 1e18 for x in D["top_accounts"]}
MV = [a for a in top if a.startswith(("erd1rlqdj67qxp", "erd13yl06g75l2", "erd1295n68497840", "erd1yxvscrnwul"))]
mv = {}
for a in MV:
    oo, _ = pall(a, "sender", WIN, cap=300); ii, _ = pall(a, "receiver", WIN, cap=300)
    mv[a] = {"balance_egld": top[a], "info": info(a), "first_tx_ts": first_tx(a),
             "out": [{"to": t["receiver"], "label": lab(t["receiver"]) or ("NEW BINANCE HOT" if t["receiver"] == NEWHOT else None), "egld": eg(t), "fn": t.get("function"), "ts": t["timestamp"]} for t in oo if eg(t) >= 100 or t.get("function") in ("delegate", "unDelegate", "withdraw")][:25],
             "in": [{"from": t["sender"], "label": lab(t["sender"]) or ("NEW BINANCE HOT" if t["sender"] == NEWHOT else None), "egld": eg(t), "fn": t.get("function"), "ts": t["timestamp"]} for t in ii if eg(t) >= 100][:25]}
    print("[mover]", a[:16], round(top[a]), "OUT", [(x["to"][:12], x["label"], round(x["egld"]), x["fn"]) for x in mv[a]["out"][:8]], "IN", [(x["from"][:12], x["label"], round(x["egld"])) for x in mv[a]["in"][:8]])
A["unlabelled_movers"] = mv

# (E) lookalikes
lk = {}
for pre, target in (("erd1tsddlqzd63", NEWHOT), ("erd1yl5ksy466z", YLW)):
    full_a = None
    for t in D["binance_custody_in"] + D["binance_hot_in"]:
        if t["sender"].startswith(pre): full_a = t["sender"]
    if not full_a: continue
    oo, _ = pall(full_a, "sender", WIN - 30 * 86400, cap=300)
    lk[full_a] = {"mimics": target, "info": info(full_a), "first_tx_ts": first_tx(full_a), "out_txs_30d": len(oo), "zero_value_out": sum(1 for t in oo if eg(t) == 0),
                  "distinct_targets": len({t["receiver"] for t in oo}), "prefix_match": full_a[:6] == target[:6], "suffix_match": full_a[-4:] == target[-4:]}
    print("[lookalike]", full_a, lk[full_a])
A["binance_lookalikes"] = lk

# (F) provider movers: delegate calls >= 1,000 EGLD in the window
pm = {}
for m in D["provider_movers"][:3]:
    ii, _ = pall(m["address"], "receiver", WIN, cap=1500)
    big = sorted(({"from": t["sender"], "label": lab(t["sender"]), "egld": eg(t), "fn": t.get("function"), "ts": t["timestamp"]} for t in ii if eg(t) >= 1000), key=lambda x: -x["egld"])[:8]
    pm[m["identity"] or m["address"]] = {"delta_egld": m["delta_egld"], "users": m["users"], "prev_users": m["prev_users"], "big_inbound": big}
    print("[prov]", m["identity"], round(m["delta_egld"]), [(x["from"][:14], x["label"], round(x["egld"]), x["fn"]) for x in big])
A["provider_mover_inbound"] = pm

D2 = json.load(open(SNAP)); D2["run37_adhoc"] = A
json.dump(D2, open(SNAP, "w"))
print("written")
