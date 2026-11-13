#!/usr/bin/env python3
"""Run #36: lean assembler (from run #35). Starts from the run #35 report as a structural template, recomputes every
numeric section from data/collected/2026-11-02.json, drops the bespoke sections whose inputs this run did
not re-collect (otc_pipeline, halt_recovery, unbonding_in_flight, provider_states, fee_events) and writes
fresh narrative from the computed figures."""
import json, copy, statistics, sys
sys.path.insert(0, "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/scripts")
from report_template import blank_template, load_previous
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD = "2026-11-09"
E = 1e18
c = json.load(open(f"{REPO}/data/collected/{RD}.json"))
pv = load_previous(RD)   # snapshot taken before this report, safe to re-run
r0 = json.load(open(f"{REPO}/reports/2026-11-02.json"))
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
staked = eco["staked"]; ratio = staked / eco["circulatingSupply"]
live = c["liveness"]
hm = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
st = c["stats"]
acts = R["network_health"]["activity"]
tx_added = st["transactions"] - pv["activity"]["total_transactions"]
R["metadata"].update({"report_date": RD, "period_start": "2026-11-02", "period_end": RD,
    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "egld_price_usd": price, "btc_price_usd": btc, "eth_price_usd": eth, "run_number": 36})
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
    "btc_correlation_note": f"BTC {btc_wow:+.2f}%, ETH {eth_wow:+.2f}%, EGLD {pc:+.2f}% over 7.05 days: EGLD {rel:+.1f}pp vs BTC, after +7.2pp in run #35."}
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
        if v["label"].startswith(k):
            cur[n] = cur.get(n, 0) + b
            break
prevb = pv["exchange_balances"]
chg = {k: cur.get(k, 0) - prevb[k] for k in prevb}
tot_c, tot_p = sum(cur.get(k, 0) for k in prevb), sum(prevb.values())
net = tot_c - tot_p
INTERNAL = 0.0   # run #36: no move between two tracked exchange wallets in the window (checked)
ef = R["whale_intelligence"]["exchange_flows"]
rails = c["exchange_rails"]
def rsum(label, key, side): return sum(v[side][key] for v in rails.values() if v["label"].startswith(label))
venues = []
for lbl in ("Binance.com", "Bybit", "Gate.io", "Coinbase", "Crypto.com", "KuCoin", "MEXC", "Bitget"):
    dep = rsum(lbl, "egld_7d", "in"); wd = rsum(lbl, "egld_7d", "out")
    dn = rsum(lbl, "egld_txs_7d", "in"); wn = rsum(lbl, "egld_txs_7d", "out")
    if lbl == "Binance.com":   # remove the internal send to custody from withdrawals
        wd -= INTERNAL
    venues.append({"venue": lbl, "state": "open" if dep >= 10 and wd >= 10 else ("withdraw_only" if wd >= 10 else "closed"),
        "deposits_egld_txs_7d": dn, "deposits_egld_7d": dep, "withdrawals_egld_txs_7d": wn, "withdrawals_egld_7d": wd})
prev_rs = ef.get("rail_status", {})
ef.update({"total_exchange_egld_current": tot_c, "total_exchange_egld_previous": tot_p, "net_change_egld": net,
    "net_change_pct": pct(tot_c, tot_p), "net_change_egld_raw": net, "internal_binance_staking_egld": INTERNAL,
    "direction": "outflow" if net < 0 else "inflow"})
ef["rail_status"] = {"tracked_wallets": len(rails), "egld_deposited_in_window": sum(v["in"]["egld_in_window"] for k, v in rails.items() if not v["label"].startswith("Binance Staking")) - 0,
    "egld_withdrawn_in_window": sum(v["out"]["egld_in_window"] for v in rails.values()) - INTERNAL,
    "venues_open": [v["venue"] for v in venues if v["state"] == "open"],
    "venues_deposit_only": [], "venues_closed": ["Binance.com (native rail dark since Oct 29 23:05 UTC)", "UPbit", "Bitfinex", "Tokero", "Coinbase Custody", "Coinbase Routing Wallet"],
    "by_venue": venues}
bye = []
for k in prevb:
    bye.append({"exchange": k, "change_egld": chg[k], "pct": pct(cur.get(k, 0), prevb[k])})
ef["by_exchange"] = bye
bin_cust = chg["Binance.com"] + chg["Binance Staking"]
VV = {v["venue"]: v for v in venues}
def dw(n): v = VV[n]; return f"{v['withdrawals_egld_7d']:,.0f} withdrawn vs {v['deposits_egld_7d']:,.0f} deposited (trailing 7d rails)"
ef["entity_netting"] = [
    {"entity": "Binance", "wallets_count": 4, "net_flow_egld": bin_cust,
     "interpretation": "0 EGLD: no native EGLD deposit or withdrawal at any Binance wallet in the window. The hot wallet erd1sdslvl has not transacted since it swept 309,906 EGLD to custody on Oct 29 23:05 UTC and holds 3 EGLD; 15 of its last depositors also sent nothing anywhere after Oct 30, so this reads as a paused rail, not a new deposit address. Spot trading continues ($2.99)."},
    {"entity": "KuCoin", "wallets_count": 1, "net_flow_egld": chg["KuCoin"],
     "interpretation": f"{chg['KuCoin']:+,.0f} on balances; {dw('KuCoin')}. 32,000 of it was one Nov 3 withdrawal to erd15ku2r2j6, the same wallet that took 136,359 on Oct 30 and deposited 145,443 in July. It now holds 168,358 and has not sold. Ex that wallet, KuCoin's daily withdrawals ran 2,700-5,000 EGLD on Nov 1-6 and fell under 400 on Nov 7-9."},
    {"entity": "MEXC", "wallets_count": 1, "net_flow_egld": chg["MEXC"],
     "interpretation": f"{chg['MEXC']:+,.0f}: {VV['MEXC']['withdrawals_egld_txs_7d']} withdrawals, zero deposits for a second week (withdraw-only). 40,983 left."},
    {"entity": "Bybit", "wallets_count": 1, "net_flow_egld": chg["Bybit"], "interpretation": f"{chg['Bybit']:+,.0f} on balances; {dw('Bybit')}."},
    {"entity": "Gate.io", "wallets_count": 1, "net_flow_egld": chg["Gate.io"], "interpretation": f"{chg['Gate.io']:+,.0f} on balances; {dw('Gate.io')}."},
]
ef["signal"] = f"Tracked exchange wallets lost {abs(net):,.0f} EGLD ({pct(tot_c, tot_p):+.2f}%) with Binance's native rail dark all week. KuCoin -40,396 (32,000 is one self-custody withdrawal), Bybit -16,734, MEXC -15,014, Gate.io -8,015."

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
R["whale_intelligence"]["wallet_changes"] = wc

def tiers(lst):
    out = {}
    for name, lo, hi in (("mega_whales", 1e6, 1e12), ("large_whales", 1e5, 1e6), ("mid_whales", 1e4, 1e5)):
        out[name] = (lo, [x for x in lst if lo <= x[1] < hi])
    return out
cur_top = {x["address"]: int(x["balance"]) / E for x in c["top_accounts"] if not x["address"].startswith("erd1qqqqqqqq")}
old_top = {x["address"]: float(x.get("balance_egld") or x.get("balance") or 0) for x in pv["top_accounts"]}
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
R["whale_intelligence"]["exit_routes"] = {"threshold_egld": 3000, "calls": c.get("run36_traces", {}).get("exit_route_scan", {}).get("calls"),
    "note": "Five withdraw calls above 3,000 EGLD: two held, one re-delegated (15,000), one to DeFi (5,000), one to a wallet (6,500). None reached an exchange directly.",
    "rows": c["run36_traces"]["exit_route_scan"]["rows"]}

# ---------------------------------------------------------------- demand instruments (orderbook / korea premium)
tk = c["cg_tickers"]["tickers"]; tv = sum(x["converted_volume"]["usd"] for x in tk)
def vol(m): return sum(x["converted_volume"]["usd"] for x in tk if x["market"]["identifier"] == m)
up_px = next(x["converted_last"]["usd"] for x in tk if x["market"]["identifier"] == "upbit")
bn_px = next(x["converted_last"]["usd"] for x in tk if x["market"]["identifier"] == "binance")
prem = (up_px / bn_px - 1) * 100; up_share = vol("upbit") / tv * 100
prev_prem = 20.552147239263817
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
di["identifiable_bid_status"] = "RETIRED (run #23); Mega Whale 1,219,231 and Whale B 181,822 unchanged. OTC operator inventory (Unknown Whale I) moved 112,634 to erd1drc22z7h on Nov 5, which cycles it back in daily clips: an internal vault, not a sale."

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
    p_["notable_events"] = (p_.get("notable_events") or "")[:0] + "TVL restated at this run's prices; see analysis."
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
xe = next(p for p in pb if p["protocol"] == "xExchange")
xe.update({"volume_24h_usd": vol24, "tvl_usd": tvl, "tvl_egld": tvl / price, "tvl_wow_change_pct": pct(tvl, pv["xexchange"]["pool_tvl_usd"]),
           "health_signal": "flat", "notable_events": f"24h volume ${vol24:,.0f} (previous $66,892); pair TVL ${tvl:,.0f}."})
for p_ in R["defi_activity"]["protocols"]:
    p_.pop("tvl_wow_change_pct", None)
# run #36 rec #4: restate protocol TVL from token market caps (2-week basis vs run #34 Oct 26 values)
P26 = json.load(open(f"{REPO}/reports/2026-10-26.json"))["metadata"]["egld_price_usd"]
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
                   "notable_events": f"Restated: ${u:,.0f} vs ${pu:,.0f} on Oct 26 (two-week basis, USD {(u/pu-1)*100:+.1f}%, EGLD-terms {(ue/pe-1)*100:+.1f}%)."})
R_TVL = TVL
di["dex_volume_egld_24h"] = vol24 / price
di["dex_turnover_ratio_pct"] = vol24 / tvl * 100 if tvl else None
xx["volume_status"] = "run #36 24h snapshot (7.05-day window); compared with run #35"
xx.pop("mex_price_change_24h_pct", None)
NOTREC = {"JewelSwap", "SALSA (Staking Agency)", "Dinovox VoxEGLD", "VestaX Finance"}
for p_ in pb:
    n = p_["protocol"]
    if n == "XOXNO LSD": p_["transfers_24h"] = None
    if n in ("XOXNO Aggregator", "OneDex", "JEXchange"):
        p_.update({"tvl_usd": None, "tvl_egld": None, "tvl_wow_change_pct": None, "volume_24h_usd": None, "health_signal": None,
                   "notable_events": f"Activity only: {p_.get('transfers_24h') or 0:,} transfers in 24h. TVL not measured for routers/aggregators."})
    if n in NOTREC:
        p_.update({"tvl_usd": None, "tvl_egld": None, "tvl_wow_change_pct": None, "health_signal": None,
                   "notable_events": "Not re-collected this run (staked-EGLD discovery pass last ran in run #34); figure withheld rather than shown stale."})
LEG = {"xExchange": ("dex", vol24, me["marketPairs"], None, tvl), "Hatom Lending": ("lending", 0.0, 0, tr24.get("Hatom EGLD MM"), TVL["Hatom Lending"]),
       "Hatom Liquid Staking": ("liquid_staking", 0.0, 0, tr24.get("Hatom Liquid Staking"), TVL["Hatom Liquid Staking"]),
       "XOXNO LSD": ("liquid_staking", 0.0, 0, None, TVL["XOXNO LSD"])}
R["defi_activity"]["protocols"] = [{"name": k, "category": v[0], "volume_24h_usd": v[1], "active_pairs": v[2], "transfers_24h": v[3],
    "tvl_usd": v[4], "tvl_egld": v[4] / price} for k, v in LEG.items()]

json.dump(R, open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/174a0ac3-37e6-4a71-9596-a35c3cbb3939/scratchpad/stage1.json", "w"), default=str)
D = dict(price=price, pprice=pprice, pc=pc, btc_wow=btc_wow, eth_wow=eth_wow, rel=rel, net=net, tot_c=tot_c, tot_p=tot_p, chg=chg, ratio=ratio,
         staked=staked, dstaked=staked - peco["staked_egld"], prem=prem, up_share=up_share, vol24=vol24, tvl=tvl, dl=dl, dlp=dlp, hhi=hhi,
         top5=top5, top10=top10, bn_bid=bn_bid, TVL=R_TVL, WT={k: (v["count_current"], v["total_balance_egld"], v["net_change_egld"], v["net_change_pct"]) for k, v in WT.items()})
json.dump(D, open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/174a0ac3-37e6-4a71-9596-a35c3cbb3939/scratchpad/digest36.json", "w"), default=str)
print(json.dumps(D, indent=1, default=str))
