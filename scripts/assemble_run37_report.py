#!/usr/bin/env python3
"""Run #37: lean assembler (from run #36). Uses the run #36 report as a blanked structural template, recomputes every
numeric section from data/collected/2026-11-16.json, drops the bespoke sections whose inputs this run did
not re-collect (otc_pipeline, halt_recovery, unbonding_in_flight, provider_states, fee_events) and writes
fresh narrative from the computed figures."""
import json, copy, statistics, sys
sys.path.insert(0, "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/scripts")
from report_template import blank_template, load_previous
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD = "2026-11-16"
E = 1e18
c = json.load(open(f"{REPO}/data/collected/{RD}.json"))
pv = load_previous(RD)   # snapshot taken before this report, safe to re-run
r0 = json.load(open(f"{REPO}/reports/2026-11-09.json"))
learn = json.load(open(f"{REPO}/data/learnings.json"))
learn["runs"] = [x for x in learn["runs"] if x["date"] < RD]   # runs before this report
kn = json.load(open(f"{REPO}/data/known-addresses.json"))
R = blank_template(r0)   # shape only; every value must be recomputed below
for k in ("otc_pipeline", "halt_recovery"):
    R["whale_intelligence"].pop(k, None)
for k in ("unbonding_in_flight", "provider_states", "fee_events", "identity_renames", "zero_stake_cohort"):
    R["staking_intelligence"].pop(k, None)

LM = {}
for s, e in kn.items():
    if isinstance(e, dict):
        for a, m in e.items():
            if isinstance(m, dict) and a.startswith("erd1"):
                LM[a] = (m.get("name"), m.get("category"))
def lab(a): return (LM.get(a) or [None])[0]
def iso(t): return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def pct(a, b): return None if not b else (a - b) / b * 100

# ---------------------------------------------------------------- economics
eco, peco = c["economics"], pv["economics"]
price, pprice = eco["price"], peco["egld_price_usd"]
btc, eth = c["btc_eth"]["bitcoin"]["usd"], c["btc_eth"]["ethereum"]["usd"]
btc_wow, eth_wow = pct(btc, peco["btc_price_usd"]), pct(eth, peco["eth_price_usd"])
pc = pct(price, pprice)
rel = pc - btc_wow
PREV_REL = next(a["current_value"] for a in r0["anomalies"] if a["metric"] == "egld_minus_btc_pp")
staked = eco["staked"]; ratio = staked / eco["circulatingSupply"]
live = c["liveness"]
hm = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
st = c["stats"]
acts = R["network_health"]["activity"]
tx_added = st["transactions"] - pv["activity"]["total_transactions"]
R["metadata"].update({"report_date": RD, "period_start": "2026-11-09", "period_end": RD,
    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "egld_price_usd": price, "btc_price_usd": btc, "eth_price_usd": eth, "run_number": 37})
nh = R["network_health"]
nh["economics"] = {"egld_price_usd": price, "market_cap_usd": eco["marketCap"], "total_supply": eco["totalSupply"],
    "circulating_supply": eco["circulatingSupply"], "staked_egld": staked, "staked_ratio": ratio,
    "staking_apr": eco["apr"], "base_apr": eco["baseApr"], "topup_apr": eco["topUpApr"],
    "token_market_cap_usd": eco["tokenMarketCap"]}
nh["activity"] = {"total_accounts": st["accounts"], "total_transactions": st["transactions"], "epoch": st["epoch"],
    "blocks": st["blocks"], "shards": 3, "transactions_7d": tx_added, "avg_daily_transactions": round(tx_added / c["_period"]["window_days"])}
nh["deltas"] = {"price_change_pct": pc, "market_cap_change_pct": pct(eco["marketCap"], peco["market_cap_usd"]),
    "staked_ratio_change_pp": (ratio - peco["staked_ratio"]) * 100, "apr_change_pp": (eco["apr"] - peco["staking_apr"]) * 100,
    "accounts_added": st["accounts"] - pv["activity"]["total_accounts"], "transactions_added": tx_added,
    "supply_added": eco["totalSupply"] - peco["total_supply"], "staked_egld_added": staked - peco["staked_egld"],
    "epoch_advanced": st["epoch"] - pv["activity"]["epoch"],
    "btc_correlation_note": f"BTC {btc_wow:+.2f}%, ETH {eth_wow:+.2f}%, EGLD {pc:+.2f}% over {c['_period']['window_days']:.2f} days: EGLD {rel:+.1f}pp vs BTC, after {PREV_REL:+.1f}pp in run #36."}
nh["liveness"] = {"ok": c["liveness_ok"], "latest_block_by_shard": {k: hm(v["timestamp"]) for k, v in live.items()},
    "restart_1_utc": "2026-09-23 16:35 UTC", "restart_1_stopped_utc": "2026-09-23 16:53 UTC", "restart_2_utc": "2026-09-24 15:30 UTC",
    "live_days_in_window": c["_period"]["live_days"], "rollback_point_utc": "2026-09-19 06:37:45 UTC"}

# ---------------------------------------------------------------- exchange balances / flows
VEN = [("Binance Staking custody", "Binance Staking"), ("Binance.com", "Binance.com"), ("UPbit hot", "UPbit"), ("Bybit", "Bybit"),
       ("Crypto.com", "Crypto.com"), ("MEXC", "MEXC"), ("Bitget", "Bitget"), ("Coinbase", "Coinbase"), ("Gate.io", "Gate.io"),
       ("KuCoin", "KuCoin"), ("Bitfinex", "Bitfinex"), ("Tokero", "Tokero")]
cur = {}
bal = {}
for a, v in c["accounts"].items():
    b = int(v["info"]["balance"]) / E
    bal[a] = b
    for k, n in VEN:
        if v["label"].startswith(k) and "round-trip whale" not in v["label"]:
            cur[n] = cur.get(n, 0) + b
            break
AH = c["run37_adhoc"]; NH = AH["new_hot"]; NEWHOT = NH["address"]
bal[NEWHOT] = NH["info"]["balance_egld"]; cur["Binance.com"] += bal[NEWHOT]   # Binance hot wallet 2, first seen this window
prevb = pv["exchange_balances"]
chg = {k: cur.get(k, 0) - prevb[k] for k in prevb}
tot_c, tot_p = sum(cur.get(k, 0) for k in prevb), sum(prevb.values())
net = tot_c - tot_p
INTERNAL = 0.0   # Binance.com hot -> Binance Staking custody sends inside the window (internal, not customer flow)
_seen_int = set()
for a, v in c["accounts"].items():
    for t in v["txs"]:
        if t["txHash"] in _seen_int or t["timestamp"] < c["_period"]["window_start_ts"]: continue
        ls0, lr0 = (LM.get(t["sender"]) or [""])[0] or "", (LM.get(t["receiver"]) or [""])[0] or ""
        if ls0.startswith("Binance") and lr0.startswith("Binance"):
            _seen_int.add(t["txHash"]); INTERNAL += int(t.get("value", "0")) / E
ef = R["whale_intelligence"]["exchange_flows"]
rails = c["exchange_rails"]
def rsum(label, key, side): return sum(v[side][key] for v in rails.values() if v["label"].startswith(label))
venues = []
for lbl in ("Binance.com", "Bybit", "Gate.io", "Coinbase", "Crypto.com", "KuCoin", "MEXC", "Bitget"):
    dep = rsum(lbl, "egld_7d", "in"); wd = rsum(lbl, "egld_7d", "out")
    dn = rsum(lbl, "egld_txs_7d", "in"); wn = rsum(lbl, "egld_txs_7d", "out")
    if lbl == "Binance.com":   # customer flow is on hot wallet 2; the tracked Binance wallets only moved EGLD between themselves
        dep, wd, dn, wn = NH["external_in_egld_window"], NH["out_egld_window"], NH["external_in_txs"], NH["out_n_window"]
    venues.append({"venue": lbl, "state": "open" if dep >= 10 and wd >= 10 else ("withdraw_only" if wd >= 10 else "closed"),
        "deposits_egld_txs_7d": dn, "deposits_egld_7d": dep, "withdrawals_egld_txs_7d": wn, "withdrawals_egld_7d": wd})
prev_rs = r0["whale_intelligence"]["exchange_flows"].get("rail_status", {})
LV = c["run37_traces"]["rail_liveness"]["rows"]
def last_seen(lbl):
    ts_ = [max(x for x in (v["last_out_ts"], v["last_in_ts"]) if x) for v in LV.values() if v["label"].startswith(lbl) and (v["last_out_ts"] or v["last_in_ts"])]
    return max(ts_) if ts_ else None
CLOSED = []
for lbl in sorted({v["label"] for v in rails.values()}):
    if lbl.startswith("Binance"): continue
    tot_ = sum(v["in"]["egld_in_window"] + v["out"]["egld_in_window"] for v in rails.values() if v["label"] == lbl)
    if tot_ < 10:
        ls_ = last_seen(lbl)
        CLOSED.append(f"{lbl} (last value-bearing transfer {hm(ls_)})" if ls_ else f"{lbl} (no value-bearing transfer in the last 50 transactions)")
ef["rail_liveness"] = [{"venue": v["label"], "address": a, "last_deposit_utc": hm(v["last_in_ts"]) if v["last_in_ts"] else None,
    "last_withdrawal_utc": hm(v["last_out_ts"]) if v["last_out_ts"] else None, "silent_hours": v["silent_hours"], "silent_gt_48h": v["silent_gt_48h"]} for a, v in LV.items()]
ef.update({"total_exchange_egld_current": tot_c, "total_exchange_egld_previous": tot_p, "net_change_egld": net,
    "net_change_pct": pct(tot_c, tot_p), "net_change_egld_raw": net, "internal_binance_staking_egld": INTERNAL,
    "direction": "outflow" if net < 0 else "inflow"})
ef["rail_status"] = {"tracked_wallets": len(rails) + 1, "egld_deposited_in_window": sum(v["in"]["egld_in_window"] for k, v in rails.items() if not v["label"].startswith("Binance")) + NH["external_in_egld_window"],
    "egld_withdrawn_in_window": sum(v["out"]["egld_in_window"] for v in rails.values() if not v["label"].startswith("Binance")) + NH["out_egld_window"],
    "venues_open": [v["venue"] for v in venues if v["state"] == "open"],
    "venues_deposit_only": [v["venue"] for v in venues if v["deposits_egld_7d"] >= 10 and v["withdrawals_egld_7d"] < 10], "venues_closed": CLOSED,
    "by_venue": venues}
bye = []
for k in prevb:
    bye.append({"exchange": k, "change_egld": chg[k], "pct": pct(cur.get(k, 0), prevb[k])})
ef["by_exchange"] = bye
bin_cust = chg["Binance.com"] + chg["Binance Staking"]
VV = {v["venue"]: v for v in venues}
def dw(n): v = VV[n]; return f"{v['withdrawals_egld_7d']:,.0f} withdrawn vs {v['deposits_egld_7d']:,.0f} deposited (trailing 7d rails)"
ENT = {"Binance": bin_cust}
ef["internal_note"] = f"{INTERNAL:,.0f} EGLD moved between Binance's own wallets in the window (custody -> Binance.com 2,264,611; custody and Binance.com -> hot wallet 2 100,300). Netted at entity level."
for k in prevb:
    if not k.startswith("Binance"): ENT[k] = chg[k]
def _interp(k):
    if k in VV: return f"{ENT[k]:+,.0f} on balances; {dw(k)}."
    return f"{ENT[k]:+,.0f} on balances."
ef["entity_netting"] = [{"entity": k, "wallets_count": 5 if k == "Binance" else sum(1 for v in rails.values() if v["label"].startswith(k)) or 1, "net_flow_egld": v, "interpretation": _interp(k)}
                        for k, v in sorted(ENT.items(), key=lambda kv: -abs(kv[1])) if abs(v) >= 500 or k == "Binance"]
_mv = sorted(((k, v) for k, v in chg.items() if abs(v) >= 1000), key=lambda kv: kv[1])
ef["signal"] = (f"Tracked exchange wallets {'lost' if net < 0 else 'gained'} {abs(net):,.0f} EGLD ({pct(tot_c, tot_p):+.2f}%). " + ", ".join(f"{k} {v:+,.0f}" for k, v in _mv) + ".")

# ---------------------------------------------------------------- wallet changes / tiers
wc = []
prevw = {w["address"]: w for w in r0["whale_intelligence"]["wallet_changes"]}
topmap = {x["address"]: int(x["balance"]) / E for x in c["top_accounts"]}
for a, w in prevw.items():
    b = bal.get(a, topmap.get(a))
    if b is None:
        continue
    d = dict(w); d["balance_previous_egld"] = w["balance_current_egld"]; d["balance_current_egld"] = b
    d["change_egld"] = b - w["balance_current_egld"]; d["change_pct"] = pct(b, w["balance_current_egld"])
    wc.append(d)
YLW = AH["binance_ylw"]["address"]; RLQ = next(a for a in AH["unlabelled_movers"] if a.startswith("erd1rlqdj67qxp"))
oldtop = {x["address"]: float(x.get("balance_egld") or 0) for x in pv["top_accounts"]}
for a_, lab_, cat_, prev_ in ((YLW, "Binance.com (received 2,264,611 from Binance Staking custody)", "exchange", 1.2673575994379942),
                              (NEWHOT, "Binance.com hot wallet 2 (new)", "exchange", 0.0),
                              (RLQ, "Binance depositor whale (erd1rlqdj67qxp)", "other", oldtop.get(RLQ))):
    b_ = bal.get(a_, topmap.get(a_))
    if b_ is None or prev_ is None or a_ in prevw: continue
    wc.append({"address": a_, "label": lab_, "category": cat_, "balance_current_egld": b_, "balance_previous_egld": prev_,
               "change_egld": b_ - prev_, "change_pct": pct(b_, prev_)})
for d in wc:
    b_ = d["balance_current_egld"]
    t_ = "mega_whale" if b_ >= 1e6 else "large_whale" if b_ >= 1e5 else "mid_whale" if b_ >= 1e4 else None
    if t_: d["tier"] = t_
    else: d.pop("tier", None)
R["whale_intelligence"]["wallet_changes"] = wc

def tiers(lst):
    out = {}
    for name, lo, hi in (("mega_whales", 1e6, 1e12), ("large_whales", 1e5, 1e6), ("mid_whales", 1e4, 1e5)):
        out[name] = (lo, [x for x in lst if lo <= x[1] < hi])
    return out
cur_top = {x["address"]: int(x["balance"]) / E for x in c["top_accounts"] if not x["address"].startswith("erd1qqqqqqqq")}
old_top = {x["address"]: float(x.get("balance_egld") or x.get("balance") or 0) for x in pv["top_accounts"]}
old_top.setdefault("erd1ylwuswz9zuk4acuq4aa6d0x9ys293yhlpwg6vpuwntndyej4u44q896zlz", 1.2673575994379942)   # Binance.com wallet, below the top 100 last week; in c["accounts"] then
common = [a for a in cur_top if a in old_top]
WT = {}
for name, lo, hi in (("mega_whales", 1e6, 1e12), ("large_whales", 1e5, 1e6), ("mid_whales", 1e4, 1e5)):
    ca = [a for a in common if lo <= cur_top[a] < hi]
    cn = [a for a in cur_top if lo <= cur_top[a] < hi]
    pn = [a for a in old_top if lo <= old_top[a] < hi]
    tc = sum(cur_top[a] for a in ca); tp = sum(old_top[a] for a in ca)
    WT[name] = {"threshold_egld": lo, "count_current": len(cn), "count_previous": len(pn),
                "total_balance_egld": sum(cur_top[a] for a in cn), "previous_total_balance_egld": tp,
                "net_change_egld": tc - tp, "net_change_pct": pct(tc, tp)}
R["whale_intelligence"]["whale_tiers"] = WT

# large transactions: value >= 5,000 EGLD seen on tracked accounts in the window
seen, LT = set(), []
for a, v in c["accounts"].items():
    for t in v["txs"]:
        val = int(t.get("value", "0")) / E
        if val >= 5000 and t["txHash"] not in seen and t["timestamp"] >= c["_period"]["window_start_ts"]:
            seen.add(t["txHash"])
            s_, r_ = t["sender"], t["receiver"]
            ls_, lr_ = lab(s_), lab(r_)
            cs, cr = (LM.get(s_) or [None, None])[1], (LM.get(r_) or [None, None])[1]
            if cs == "exchange" and cr == "exchange": ft = "exchange_to_exchange"
            elif cr == "exchange": ft = "exchange_inflow"
            elif cs == "exchange": ft = "exchange_outflow"
            else: ft = "whale_to_whale"
            LT.append({"hash": t["txHash"], "timestamp": iso(t["timestamp"]), "sender": s_, "sender_label": ls_, "receiver": r_,
                       "receiver_label": lr_, "value_egld": val, "value_usd": val * price, "flow_type": ft})
LT.sort(key=lambda x: -x["value_egld"]); R["whale_intelligence"]["large_transactions"] = LT[:25]
R["whale_intelligence"]["dormant_activations"] = []
XR = c["run37_traces"]["exit_route_scan"]
R["whale_intelligence"]["exit_routes"] = {"threshold_egld": 3000, "calls": XR.get("calls"),
    "note": f"{XR.get('calls') or 0} withdraw calls above 3,000 EGLD: " + ", ".join(f"{v['n'] if isinstance(v, dict) and 'n' in v else v} {k}" for k, v in (XR.get("by_route") or {}).items()) + ".",
    "rows": XR["rows"]}

# ---------------------------------------------------------------- demand instruments (orderbook / korea premium)
tk = c["cg_tickers"]["tickers"]; tv = sum(x["converted_volume"]["usd"] for x in tk)
def vol(m): return sum(x["converted_volume"]["usd"] for x in tk if x["market"]["identifier"] == m)
up_px = next(x["converted_last"]["usd"] for x in tk if x["market"]["identifier"] == "upbit")
bn_px = next(x["converted_last"]["usd"] for x in tk if x["market"]["identifier"] == "binance")
prem = (up_px / bn_px - 1) * 100; up_share = vol("upbit") / tv * 100
prev_prem = r0["whale_intelligence"]["demand_instruments"]["exchange_orderbook"]["korea_premium_pct"]
bn = [x for x in tk if x["market"]["identifier"] == "binance"]
bn_bid = sum(x.get("cost_to_move_down_usd") or 0 for x in bn)
di = R["whale_intelligence"]["demand_instruments"]
for k in list(di):
    if k not in ("exchange_orderbook", "dex_turnover_ratio_pct", "dex_volume_egld_24h"):
        di.pop(k)
di["exchange_orderbook"] = {"source": "CoinGecko exchange tickers (third-party), 2% depth and daily volume",
    "binance": {"pairs": len(bn), "volume_24h_usd": vol("binance"), "depth_minus2_usd": bn_bid},
    "upbit": {"volume_24h_usd": vol("upbit"), "price_usd": up_px}, "all_venues": {"pairs": len(tk), "volume_24h_usd": tv},
    "korea_premium_pct": prem, "upbit_share_of_volume_pct": up_share, "binance_price_usd": bn_px}
di["identifiable_bid_status"] = None   # written in stage 2 from the vault trace

# ---------------------------------------------------------------- staking
P = [x for x in c["providers"] if int(x["locked"]) > 0]
for x in P:
    x["lk"] = int(x["locked"]) / E
P.sort(key=lambda x: -x["lk"])
tot = sum(x["lk"] for x in P)
idm = {}
for i in c["identities"] if isinstance(c["identities"], list) else []:
    idm[i.get("identity")] = i
pprov = {x["address"]: x for x in pv["staking_providers"]}
def nm(x): return x.get("identity") or x["provider"]
shares = [x["lk"] / tot for x in P]
hhi = sum(s * s for s in shares)
tp = []
for i, x in enumerate(P[:20], 1):
    o = pprov.get(x["provider"])
    tp.append({"rank": i, "identity": nm(x), "name": nm(x), "provider_address": x["provider"], "locked_egld": x["lk"],
        "previous_locked_egld": o["locked_egld"] if o else None, "share_pct": x["lk"] / tot * 100, "apr_pct": x["apr"],
        "fee_pct": x["serviceFee"] * 100, "num_users": x["numUsers"], "num_nodes": x["numNodes"],
        "wow_change_egld": x["lk"] - o["locked_egld"] if o else None})
si = R["staking_intelligence"]
si["top_providers"] = tp
aprs = [x["apr"] for x in P if x["apr"] > 0]
si["summary"] = {"total_staked_egld": staked, "total_delegated_egld": tot, "staked_ratio": ratio, "num_providers": len(P),
    "apr_min": min(aprs), "apr_max": max(aprs), "apr_weighted_avg": sum(x["apr"] * x["lk"] for x in P) / tot}
top5, top10 = sum(shares[:5]) * 100, sum(shares[:10]) * 100
si["concentration"] = {"top_5_share_pct": top5, "top_10_share_pct": top10, "hhi": hhi, "hhi_previous": pv["staking_concentration"]["hhi"],
    "hhi_interpretation": f"HHI {hhi:.5f} (previous {pv['staking_concentration']['hhi']:.5f}), far below the 0.15 competitive threshold; top-5 {top5:.2f}%, top-10 {top10:.2f}%."}
bk = []
for lab_, lo, hi in (("5-6%", 5, 6), ("6-7%", 6, 7), ("7-8%", 7, 8), ("8-9%", 8, 9), ("9-10%", 9, 10), ("10%+", 10, 99)):
    m = [x for x in P if lo <= x["apr"] < hi]
    bk.append({"label": lab_, "min_apr_pct": lo, "max_apr_pct": hi, "provider_count": len(m), "total_locked_egld": sum(x["lk"] for x in m)})
z = [x for x in P if x["apr"] == 0]
si["apr_distribution"] = {"buckets": bk, "zero_apr_providers": len(z), "zero_apr_locked_egld": sum(x["lk"] for x in z)}
def orow(x): return {"identity": nm(x), "name": nm(x), "apr_pct": x["apr"], "fee_pct": x["serviceFee"] * 100, "locked_egld": x["lk"]}
big = [x for x in P if x["lk"] >= 20000 and x["apr"] > 0]
si["apr_outliers"] = {"top_apr": [orow(x) for x in sorted(big, key=lambda x: -x["apr"])[:5]],
    "lowest_fee": [orow(x) for x in sorted(big, key=lambda x: (x["serviceFee"], -x["apr"]))[:5]]}
dl, dlp = sum(x["numUsers"] for x in P), sum(x["num_delegators"] for x in pv["staking_providers"] if x["locked_egld"] > 0)
gain = lose = 0
for x in P:
    o = pprov.get(x["provider"])
    if o:
        if x["numUsers"] > o["num_delegators"]: gain += 1
        elif x["numUsers"] < o["num_delegators"]: lose += 1
si["churn"] = {"total_delegators_current": dl, "total_delegators_previous": dlp, "delegators_added": dl - dlp,
    "delegators_change_pct": pct(dl, dlp), "providers_gaining_delegators": gain, "providers_losing_delegators": lose}
si["unbonding_pool"] = {"undelegated_this_window_egld": c["undelegated_this_week_total_egld"], "callers": c["undelegate_callers_count"],
    "pool_total_egld": c["unbonding_pool_total_egld"]}

# ---------------------------------------------------------------- tokens / xexchange
def tk_row(t, prevlist):
    o = next((p for p in prevlist if p["identifier"] == t["identifier"]), None)
    return o
th = []
for t in c["tokens_holders"][:10]:
    o = tk_row(t, pv["top_tokens_by_holders"])
    th.append({"identifier": t["identifier"], "name": t["name"], "holders": t["accounts"], "previous_holders": o["holders"] if o else None,
        "holders_change": t["accounts"] - o["holders"] if o else None, "price_usd": t.get("price"), "market_cap_usd": t.get("marketCap"), "volume_24h_usd": None})
tvv = []
for t in c["tokens_txs"][:10]:
    o = tk_row(t, pv["top_tokens_by_volume"])
    tvv.append({"identifier": t["identifier"], "name": t["name"], "transactions": t["transactions"],
        "previous_transactions": o["transactions"] if o else None, "change_pct": pct(t["transactions"], o["transactions"]) if o else None,
        "price_usd": t.get("price"), "volume_24h_usd": None})
tm = []
for t in c["tokens_mcap"][:10]:
    tm.append({"identifier": t["identifier"], "name": t["name"], "holders": t["accounts"], "previous_holders": None,
        "price_usd": t.get("price"), "market_cap_usd": t.get("marketCap"), "volume_24h_usd": None})
ta = R["token_activity"]
ta["top_by_holders"], ta["top_by_volume"], ta["top_by_market_cap"] = th, tvv, tm
ni = [t for t in c["newly_issued"] if t["timestamp"] >= c["_period"]["window_start_ts"]]
ni.sort(key=lambda t: -(t["accounts"] or 0))
ta["newly_issued"] = [{"identifier": t["identifier"], "name": t["name"], "ticker": t["ticker"], "holders": t["accounts"],
    "transactions": t["transactions"], "issued_at": iso(t["timestamp"]), "deployer": t["deployer"]} for t in ni[:5]]
me = c["mex_economics"]; pairs = sorted(c["mex_pairs"], key=lambda x: -(x.get("volume24h") or 0))
vol24 = sum(x.get("volume24h") or 0 for x in c["mex_pairs"]); tvl = sum(x.get("totalValue") or 0 for x in c["mex_pairs"])
px = c["mex_pairs"][0].get("quotePrice") or price
xx = ta["xexchange"]
tp_ = pairs[0]
xx.update({"mex_price_source": "xExchange /mex/economics", "total_pairs": me["marketPairs"], "total_volume_24h_usd": vol24, "mex_price_usd": me["price"], "mex_market_cap_usd": me["marketCap"],
    "mex_price_change_wow_pct": pct(me["price"], pv["xexchange"]["mex_price_usd"]), "top_pair": f"{tp_['baseName']}/{tp_['quoteName']}",
    "top_pair_volume_24h_usd": tp_.get("volume24h"), "top_pair_dominance_pct": (tp_.get("volume24h") or 0) / vol24 * 100 if vol24 else None,
    "top_pairs_by_volume": [{"name": f"{x['baseName']}/{x['quoteName']}", "volume_24h_usd": x.get("volume24h"), "tvl_usd": x.get("totalValue"),
        "trades_count_24h": x.get("tradesCount24h"), "is_other": False, "share_pct": (x.get("volume24h") or 0) / vol24 * 100 if vol24 else None} for x in pairs[:5]],
    "pool_tvl_usd": tvl, "previous_pool_tvl_usd": pv["xexchange"]["pool_tvl_usd"], "turnover_ratio_pct": vol24 / tvl * 100 if tvl else None,
    "previous_turnover_ratio_pct": pv["xexchange"]["turnover_ratio_pct"], "dex_vol_wow_pct": pct(vol24, pv["xexchange"]["volume_24h_usd"]),
    "dex_volume_egld_24h": vol24 / price, "previous_dex_volume_egld_24h": pv["xexchange"]["volume_24h_egld"],
    "dex_vol_egld_wow_pct": pct(vol24 / price, pv["xexchange"]["volume_24h_egld"]), "pool_tvl_egld": tvl / price, "previous_pool_tvl_egld": pv["xexchange"]["pool_tvl_egld"]})
for k in ("mex_pair_depth", "wegld_usdc_share_of_volume_pct", "ex_wegld_usdc_volume_usd", "mex_pair_event"):   # run 36: Sep MEX incident block retired
    xx.pop(k, None)

# ---------------------------------------------------------------- defi
pb = R["defi_activity"]["protocol_breakdown"]
wegld_bal = int(c["wegld"]["balance"]) / E if isinstance(c["wegld"], dict) and "balance" in c["wegld"] else None
tvlt = c["tvl_tokens"]
def supply(tok):
    t = tvlt.get(tok) or {}
    return (int(t.get("minted", 0)) - int(t.get("burnt", 0)))
for p_ in pb:
    p_["notable_events"] = None
    p_["tvl_wow_change_pct"] = None
    p_["health_signal"] = None
    p_["transfers_24h"] = p_.get("transfers_24h")
for p_ in pb:
    key = {"xExchange": None, "Hatom Lending": None}.get(p_["protocol"])
tr24 = {k: v["transfers_24h"] for k, v in c["proto"].items()}
for p_ in pb:
    n = p_["protocol"]
    if n.startswith("XOXNO"): p_["transfers_24h"] = tr24.get("XOXNO Aggregator")
    elif n.startswith("OneDex"): p_["transfers_24h"] = tr24.get("OneDex Swap")
    elif n.startswith("JEX"): p_["transfers_24h"] = tr24.get("JEXchange Router 2")
    elif n.startswith("Hatom Liquid"): p_["transfers_24h"] = tr24.get("Hatom Liquid Staking")
    elif n == "Hatom Lending": p_["transfers_24h"] = tr24.get("Hatom EGLD MM")
def sig0(x): return "growing" if x > 3 else "shrinking" if x < -3 else "flat"
xe = next(p for p in pb if p["protocol"] == "xExchange")
xe.update({"volume_24h_usd": vol24, "tvl_usd": tvl, "tvl_egld": tvl / price, "tvl_wow_change_pct": pct(tvl, pv["xexchange"]["pool_tvl_usd"]),
           "health_signal": "flat", "health_signal": sig0(pct(tvl, pv["xexchange"]["pool_tvl_usd"])), "notable_events": f"24h volume ${vol24:,.0f} (previous ${pv['xexchange']['volume_24h_usd']:,.0f}); pair TVL ${tvl:,.0f}."})
for p_ in R["defi_activity"]["protocols"]:
    p_.pop("tvl_wow_change_pct", None)
# protocol TVL from token market caps, one-week basis vs the run #36 snapshot (Nov 9)
P26 = pprice
def mcap(t): return (tvlt.get(t) or {}).get("marketCap") or 0
HL = ["HUSDC-d80042","HEGLD-d61095","HUSDT-6f0914","HWBTC-49ca31","HWETH-b3d17e","HBUSD-ac1fca","HHTM-e03ba5","HMEX-df6df7","HUTK-4fa4b2","HWTAO-2e9136"]
we = sum(int(x["balance"])/E for x in c["wegld"].values() if isinstance(x, dict) and "balance" in x)
TVL = {"Hatom Lending": sum(mcap(t) for t in HL), "Hatom Liquid Staking": mcap("SEGLD-3ad2d0") + mcap("SWTAO-356a25"),
       "Hatom USH": mcap("USH-111e09"), "XOXNO LSD": mcap("XEGLD-e413ed"), "xExchange (USD)": we * price}
def sig(x):
    return "growing" if x > 3 else "shrinking" if x < -3 else "flat"
for p_ in pb:
    k = p_["protocol"]
    if k in TVL and k != "xExchange (USD)":
        u = TVL[k]; pu = pv["defi_tvl"][k]; ue = u / price; pe = pu / P26
        p_.update({"tvl_usd": u, "tvl_egld": ue, "tvl_wow_change_pct": (u / pu - 1) * 100, "tvl_wow_change_egld": ue - pe,
                   "health_signal": sig((u / pu - 1) * 100),
                   "notable_events": f"${u:,.0f} vs ${pu:,.0f} on Nov 9 (USD {(u/pu-1)*100:+.1f}%, EGLD-terms {(ue/pe-1)*100:+.1f}%)."})
R_TVL = TVL
di["dex_volume_egld_24h"] = vol24 / price
di["dex_turnover_ratio_pct"] = vol24 / tvl * 100 if tvl else None
xx["volume_status"] = f"run #37 24h snapshot ({c['_period']['window_days']:.2f}-day window); compared with run #36"
xx.pop("mex_price_change_24h_pct", None)
NOTREC = {"JewelSwap", "SALSA (Staking Agency)", "Dinovox VoxEGLD", "VestaX Finance"}
def _em(path):
    try: d_ = json.load(open(path))["liquid_staking_protocols"]
    except Exception: return {}
    out = {}
    for x in d_:
        nm_ = (x.get("known_label") or x.get("label") or x.get("name") or "")
        for key, pat in (("JewelSwap", "JewelSwap"), ("SALSA (Staking Agency)", "SALSA"), ("Dinovox VoxEGLD", "Dinovox"), ("VestaX Finance", "VestaX")):
            if pat in nm_: out[key] = float(x.get("staked_egld") or x.get("egld_staked") or 0)
    return out
EMERG = _em(f"{REPO}/data/collected/liquid_staking_discovery_{RD}.json"); OLD_EM = _em(f"{REPO}/data/collected/liquid_staking_discovery_2026-10-26.json")
for p_ in pb:
    n = p_["protocol"]
    if n == "XOXNO LSD": p_["transfers_24h"] = None
    if n in ("XOXNO Aggregator", "OneDex", "JEXchange"):
        p_.update({"tvl_usd": None, "tvl_egld": None, "tvl_wow_change_pct": None, "volume_24h_usd": None, "health_signal": None,
                   "notable_events": f"Activity only: {p_.get('transfers_24h') or 0:,} transfers in 24h. TVL not measured for routers/aggregators."})
    if n in NOTREC:
        e_ = EMERG.get(n)
        if e_:
            o_ = OLD_EM.get(n)
            ch_ = (e_ / o_ - 1) * 100 if o_ else None
            p_.update({"tvl_usd": e_ * price, "tvl_egld": e_, "tvl_wow_change_pct": None, "health_signal": (sig0(ch_) if ch_ is not None else None),
                       "notable_events": f"{e_:,.0f} EGLD staked through the protocol contract (discovery pass re-run this window" + (f"; {o_:,.0f} on Oct 26, {ch_:+.1f}% over three weeks)." if o_ else ").")})
        else:
            p_.update({"tvl_usd": None, "tvl_egld": None, "tvl_wow_change_pct": None, "health_signal": None,
                       "notable_events": "Discovery pass found no staked EGLD for this contract on Nov 16; figure withheld."})
LEG = {"xExchange": ("dex", vol24, me["marketPairs"], None, tvl), "Hatom Lending": ("lending", 0.0, 0, tr24.get("Hatom EGLD MM"), TVL["Hatom Lending"]),
       "Hatom Liquid Staking": ("liquid_staking", 0.0, 0, tr24.get("Hatom Liquid Staking"), TVL["Hatom Liquid Staking"]),
       "XOXNO LSD": ("liquid_staking", 0.0, 0, None, TVL["XOXNO LSD"])}
R["defi_activity"]["protocols"] = [{"name": k, "category": v[0], "volume_24h_usd": v[1], "active_pairs": v[2], "transfers_24h": v[3],
    "tvl_usd": v[4], "tvl_egld": v[4] / price} for k, v in LEG.items()]

json.dump(R, open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/dddf9200-b0cf-4286-98dd-088a97a7e141/scratchpad/stage1.json", "w"), default=str)
D = dict(INTERNAL=INTERNAL, PREV_REL=PREV_REL, prev_prem=prev_prem, EMERG=EMERG, price=price,  pprice=pprice, pc=pc, btc_wow=btc_wow, eth_wow=eth_wow, rel=rel, net=net, tot_c=tot_c, tot_p=tot_p, chg=chg, ratio=ratio,
         staked=staked, dstaked=staked - peco["staked_egld"], prem=prem, up_share=up_share, vol24=vol24, tvl=tvl, dl=dl, dlp=dlp, hhi=hhi,
         top5=top5, top10=top10, bn_bid=bn_bid, TVL=R_TVL, WT={k: (v["count_current"], v["total_balance_egld"], v["net_change_egld"], v["net_change_pct"]) for k, v in WT.items()})
json.dump(D, open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/dddf9200-b0cf-4286-98dd-088a97a7e141/scratchpad/digest37.json", "w"), default=str)
print(json.dumps(D, indent=1, default=str))
