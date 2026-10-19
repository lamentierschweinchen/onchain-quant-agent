#!/usr/bin/env python3
"""Run #32 stage 2: assemble reports/2026-10-19.json from derived.json + snapshot.

~4.2-day window (Oct 15 09:08 -> Oct 19) plus a full 7-day rail window from Oct 12 15:05 for reopening-supply-overhang.
"""
import json
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD = "2026-10-19"
O = json.load(open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/804ae5e2-5073-4035-9536-3626fd353e79/scratchpad/run32w/derived.json"))
D = json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev = json.load(open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/804ae5e2-5073-4035-9536-3626fd353e79/scratchpad/run32w/previous_run31.json"))
status = json.load(open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/804ae5e2-5073-4035-9536-3626fd353e79/scratchpad/run32w/status.json"))
beh = json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
r26 = json.load(open(f"{REPO}/reports/2026-10-15.json"))   # previous report (name kept for the reused blocks)
disc = json.load(open(f"{REPO}/data/collected/liquid_staking_discovery_{RD}.json"))


def f(x, d=0):
    try:
        return f"{x:,.{d}f}"
    except Exception:
        return str(x)


def iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def hm(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%b %d %H:%M")


em = O["emerging_lsd"]
M = O["macro"]; otc = O["otc"]; ex = O["exch"]; cust = O["custody"]
bid = O["bid"]; br = O["breadth"]; sk = O["staking"]; tk = O["tokens"]; xx = O["xexchange"]
df = O["defi"]; z = O["z"]; ub = O["unbond"]; absb = O["absorbers"]; zsc = O["zero_stake_cohort"]
BOOK = O["orderbook"]; WD = O["withdraw_decoded"] or {}; PZ = O["address_poisoning"] or {}
HR = O["halt_recovery"]; CEN = O["census"]; PR = O["poison_ring"]
econ = D["economics"]; st = D["stats"]; pecon = prev["economics"]; pact = prev["activity"]
price = M["price"]; pc = M["price_chg"]
cvc = beh["aggregates"]["compound_vs_claim_at_function_level"]
ag = beh["aggregates"]; fates = ag["delegator_fates_by_tier"]
zz = lambda k: z[k].get("z")
HT = df["h_tokens"]
lsd = tk["lsd"]; usdc = tk["stable"]["USDC-c76f1f"]; usdt = tk["stable"]["USDT-f8c08c"]
LIVE_DAYS = D["_period"]["window_days"]
EGLD_VS_BTC = pc - M["btc_wow"]
tick = D["cg_tickers"]["tickers"]
up = next(t for t in tick if t["market"]["name"] == "Upbit")
bn = next(t for t in tick if t["market"]["name"] == "Binance" and t["target"] == "USDT")
PREM = 100 * (up["converted_last"]["usd"] - bn["converted_last"]["usd"]) / bn["converted_last"]["usd"]
UP_SHARE = 100 * up["converted_volume"]["usd"] / BOOK["all"]["volume_24h_usd"]
hl = df["hatom_lending_ex_hmex_egld_pct"]
EMM_D = df["egld_mm_balance"] - df["egld_mm_prev_balance"]

# ---- RAILS (run #27 rec #1): value-bearing EGLD per tracked exchange wallet ----
RAILS = D["exchange_rails"]; REOPEN = D["exchange_reopen"]


def vsum(lbl):
    rs = [r for r in RAILS.values() if r["label"] == lbl]
    return {"in_txs": sum(r["in"]["egld_txs_in_window"] for r in rs), "in_egld": sum(r["in"]["egld_in_window"] for r in rs),
            "in_senders": sum(r["in"]["distinct_counterparties_in_window"] for r in rs),
            "out_txs": sum(r["out"]["egld_txs_in_window"] for r in rs), "out_egld": sum(r["out"]["egld_in_window"] for r in rs),
            "first_in": min([r["in"]["first_egld_ts"] for r in rs if r["in"]["first_egld_ts"]] or [None], key=lambda x: x or 9e18),
            "first_out": min([r["out"]["first_egld_ts"] for r in rs if r["out"]["first_egld_ts"]] or [None], key=lambda x: x or 9e18)}


VEN = {}
for lbl in sorted({v["label"] for v in REOPEN.values()}):
    v = vsum(lbl) if any(r["label"] == lbl for r in RAILS.values()) else {"in_txs": 0, "in_egld": 0, "in_senders": 0, "out_txs": 0, "out_egld": 0, "first_in": None, "first_out": None}
    # MEXC/KuCoin's only txs since restart are the Sep 24 15:41 replays of Sep 19 transfers
    if lbl in ("MEXC", "KuCoin"):
        v = {**v, "first_in": None, "first_out": None}
    # run #29: sub-1-EGLD receives are address-poisoning/test dust, not deposits; UPbit's only send is to its own OTC desk
    dep_ok = v["in_egld"] >= 1; wd_ok = v["out_txs"] > 0 and lbl != "UPbit"
    v["state"] = ("open" if dep_ok and wd_ok else "deposit_only" if dep_ok else "withdrawal_only" if wd_ok else "closed")
    VEN[lbl] = v
_NONVENUE = {"Coinbase (secondary)", "Coinbase Routing Wallet", "Coinbase Custody", "Coinbase Custody 2 (migration destination)", "Binance Staking", "Binance: de-staking withdrawal wallet"}
OPEN = [k for k, v in VEN.items() if v["state"] == "open" and k not in _NONVENUE]   # run #30: venues, not each entity wallet
DEPONLY = [k for k, v in VEN.items() if v["state"] == "deposit_only" and k not in _NONVENUE]
CLOSED_MAJOR = [k for k in ("UPbit", "Bybit", "Coinbase", "MEXC", "KuCoin", "Bitfinex") if VEN.get(k, {}).get("state") == "closed"]
RAIL_EGLD_IN = sum(v["in_egld"] for v in VEN.values()); RAIL_EGLD_OUT = sum(v["out_egld"] for v in VEN.values())

# ---- run #32 traces ----
TR = D["run32_traces"]
BINV = VEN["Binance.com"]
BD = TR["binance_daily"]["days"]
BIN_DEP = BINV["in_egld"]; BIN_WD_EXT = BINV["out_egld"]
BIN_EXT_NET = BIN_DEP - BIN_WD_EXT
BIN_EXT_PER_DAY = BIN_EXT_NET / LIVE_DAYS
BIN_ENTITY_NET = next((e2["net_flow_egld"] for e2 in ex["entity"] if e2["entity"] == "Binance"), 0.0)
def ent_net(n): return next((e2["net_flow_egld"] for e2 in ex["entity"] if e2["entity"] == n), 0.0)
BU = TR["binance_unbond"]
BIN_UNDEL = sum(int(u["amount"]) for d_ in BU["delegation"] for u in (d_.get("userUndelegatedList") or [])) / 1e18
BIN_UNDEL_SECS = max([u["seconds"] for d_ in BU["delegation"] for u in (d_.get("userUndelegatedList") or [])] or [0])
BIN_UNDEL_DAYS = BIN_UNDEL_SECS / 86400
BIN_MATURES = iso(D["liveness"]["0"]["timestamp"] + BIN_UNDEL_SECS)
POOL = D.get("unbonding_pool") or []
NU = TR["ninjastaking_unbond"]
_nl = [(d_["contract"], u) for d_ in NU["delegation"] for u in (d_.get("userUndelegatedList") or [])]
NINJA = {"wallet": NU["wallet"], "amount_egld": sum(int(u["amount"]) for _, u in _nl) / 1e18,
         "days_remaining": max([u["seconds"] for _, u in _nl] or [0]) / 86400, "wallet_balance_egld": NU["balance_egld"],
         "active_stake_egld": sum(int(d_.get("userActiveStake") or 0) for d_ in NU["delegation"]) / 1e18}
NINJA_MATURES = iso(D["liveness"]["0"]["timestamp"] + max([u["seconds"] for _, u in _nl] or [0]))
NINJA_REDELEG = sum(x["egld"] for x in NU["out"] if x.get("fn") == "delegate")
NINJA_WD = sum(x["egld_returned"] for x in (WD.get("largest") or []) if x["sender"] == NU["wallet"])
BINP = next(m for m in sk["moves"] if m["identity"] == "binance_staking")
NINJAP = next(m for m in sk["moves"] if m["identity"] == "ninjastaking")
EXS = TR["exit_route_scan"]; EXR = EXS["by_route"]
EXIT_TRACED = sum(r["withdrawn_egld"] for r in EXS["rows"] if r["route"] != "internal")
EXIT_CEX = sum(r["withdrawn_egld"] for r in EXS["rows"] if r["route"] == "cex")
TERM = TR["desk_terminal"]; TERM_BAL = int(TERM["info"]["balance"]) / 1e18
HMM = TR["hatom_egld_mm"]
ARB = TR["arb_wallets"]; CBL = TR["coinbase_legs"]; UPD = TR["upbit_depositors"]
ARB_SET = {v["address"] for v in ARB.values()}
GATE_NET = ent_net("Gate.io")
# cross-venue wallets moved EGLD only between tracked venues this window (in == out), so the TOTAL is unaffected; entity figures are
ARB_D2_IN = ARB["erd1d2anjjha"]["in_egld"]; ARB_D2_OUT = ARB["erd1d2anjjha"]["out_egld"]
ARB_13_IN = ARB["erd13sytuz92"]["in_egld"]
ARB_RETAINED = sum(v["in_egld"] - v["out_egld"] for v in ARB.values())
EX_NET_EX_ARB = ex["net"] - ARB_RETAINED
PACE_NOW = EX_NET_EX_ARB / LIVE_DAYS; PACE_PREV = 7218 / 2.76   # run #31 ex cross-venue and ex run #30 tail: +7,218 over 2.76 days
ENT_EX_ARB = {"Binance": ent_net("Binance") + ARB["erd1d2anjjha"]["in_by_counterparty"].get("Binance.com", 0.0),
              "Bybit": ent_net("Bybit") + ARB["erd1d2anjjha"]["in_by_counterparty"].get("Bybit", 0.0) - ARB["erd13sytuz92"]["out_by_counterparty"].get("Bybit", 0.0),
              "Gate.io": GATE_NET - ARB["erd1d2anjjha"]["out_by_counterparty"].get("Gate.io", 0.0) + ARB["erd13sytuz92"]["in_by_counterparty"].get("Gate.io", 0.0)}
# ---- run #31 rec #2: the full 7-day rail window (Oct 12 15:05:30 -> now) ----
R7_START = D["_period"]["rail_7d_start_ts"]
R7_DAYS = (D["liveness"]["0"]["timestamp"] - R7_START) / 86400
R7_IN = sum(r["in"]["egld_7d"] for r in RAILS.values()); R7_OUT = sum(r["out"]["egld_7d"] for r in RAILS.values())
R7_ARB_IN = sum(v for r in RAILS.values() for c, v in r["in"]["by_cp_7d"].items() if c in ARB_SET)
R7_ARB_OUT = sum(v for r in RAILS.values() for c, v in r["out"]["by_cp_7d"].items() if c in ARB_SET)
R7_NET = R7_IN - R7_OUT; R7_NET_EX_ARB = R7_NET - R7_ARB_IN + R7_ARB_OUT
R7_BY = {}
for r in RAILS.values():
    R7_BY[r["label"]] = R7_BY.get(r["label"], 0.0) + r["in"]["egld_7d"] - r["out"]["egld_7d"]
P30 = json.load(open(f"{REPO}/reports/2026-10-12.json"))
P7_EGLD = 100 * (price - P30["metadata"]["egld_price_usd"]) / P30["metadata"]["egld_price_usd"]
P7_BTC = 100 * (M["btc"] - P30["metadata"]["btc_price_usd"]) / P30["metadata"]["btc_price_usd"]
P7_REL = P7_EGLD - P7_BTC
BAL7_EX_ARB = r26["whale_intelligence"]["exchange_flows"]["net_change_egld"] - 15179 - 20542 + EX_NET_EX_ARB   # run #31 ex-arb (+7,218) + this window
OVERHANG = ("persists" if (R7_NET_EX_ARB > 25000 and P7_REL < -3) else "cleared" if (R7_NET_EX_ARB < 0 and P7_REL > 0) else "no conclusion")
# ---- whale / depositor traces ----
HHV = "erd1hhvfrwvqj5jhxqwlac9vftwgnlkv0s9y7xy7xp98vehlq74qee6srkqgdh"
HHV_HOP = "erd1rgm4td296wxwxnepwets5wnwsea7jy5u4lw4xt2sa535khgsjcdqfag6j4"
HHV_DEP = next((x["egld"] for x in TR["binance_daily"]["top_deposits_window"] if x["from"] == HHV_HOP), 0.0)
WB = CBL["whale_b"]; WB_IN = sum(x["egld"] for x in WB["in"])
UB_ = TR["usdc_bridge"]; USDC_NET_IN = UB_["wrap_usdc"] - UB_["unwrap_usdc"]
USDC_D = usdc["supply"] - usdc["prev"]
OVERLAP_NOTE = "Run #31's rail pass ran after its 09:08 collector end and before its 09:47 commit; this run's rail window starts at the commit (09:47:20 UTC Oct 15) so nothing is counted twice. Up to 39 minutes of flow (09:08-09:47) may be missed on the rails; balance-based exchange deltas run from 09:08 and include it."
MEGA_IN = bid["mega_delta"]
UPBIT_DEP = VEN.get("UPbit", {}).get("in_egld", 0); UPBIT_DEP_N = VEN.get("UPbit", {}).get("in_senders", 0)
PREV_BOOK = prev["exchange_orderbook_latest"]
PREM_PREV = PREV_BOOK.get("korea_premium_pct", 13.6)
UPSH_PREV = PREV_BOOK.get("upbit_share_of_volume_pct", 10.7)
BIN_BID_PREV = PREV_BOOK["binance"]["depth_minus2_usd"]
WIN_TXT = f"{LIVE_DAYS:.1f}-day window (Oct 15 09:08 -> Oct 19 {hm(D['liveness']['0']['timestamp'])[-5:]} UTC)"
WINDOW_NOTE = f"{WIN_TXT}, plus a full 7-day rail window from Oct 12 15:05 for the pre-committed overhang test. Point-in-time flows below are {LIVE_DAYS:.1f}-day flows unless marked 7d."
wd_top0 = (WD.get("by_provider_top") or [[0, 0]])[0][1]
R = {}
R["metadata"] = {
    "report_date": RD, "period_start": "2026-10-15", "period_end": RD,
    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "egld_price_usd": price, "btc_price_usd": M["btc"], "eth_price_usd": M["eth"],
    "run_number": 32,
    "data_sources_ok": status["ok"] + [
        f"follow-up pass: {WD.get('calls', 0)} withdraw calls decoded, 2 rate-limited provider scans recovered, poisoning lookalikes re-scanned (0 errors)",
        "rail check (rails_run32.py): value-bearing EGLD per tracked exchange wallet, window start de-duplicated against run #31 (09:47:20 UTC Oct 15), plus a full 7-day pass from Oct 12 15:05:30 with per-counterparty totals",
        "targeted traces (trace_run32.py): exit-route scan, Binance.com daily rails since Oct 9, Binance de-staking wallet /delegation, ninjastaking exiter /delegation and outbound, USDC through the xBridge Tokens Wrapper by wallet and destination chain, cross-venue wallets, Coinbase / Whale B / Mega Whale legs, UPbit depositors, Hatom EGLD market calls",
        "web check: Upbit's EGLD caution review runs Oct 19-23; no outcome announced at collection"],
    "data_sources_failed": status["failed"],
    "data_sources_recovered": [
        "LIVENESS GATE PASSED: every shard within seconds of real time at collection",
        f"{D.get('_n_429', 0)} HTTP 429 responses in the main pass; 2 provider scans returned 429 and were re-read by the follow-up pass",
        OVERLAP_NOTE,
        WINDOW_NOTE,
        f"delegator reward behaviour sampled {ag['providers_sampled']} of {ag.get('providers_requested', 8)} providers"]}

R["executive_summary"] = [
    {"category": "whale", "severity": "high", "finding":
     f"THE REOPENING SUPPLY OVERHANG HELD OVER A FULL WEEK. On 7-day rails (Oct 12 15:05 -> Oct 19), tracked exchanges took a net {R7_NET:+,.0f} EGLD, {R7_NET_EX_ARB:+,.0f} after removing three cross-venue wallets, while EGLD fell {abs(P7_EGLD):.1f}% against BTC {P7_BTC:+.1f}% ({P7_REL:+.1f}pp). "
     f"Both legs of the pre-committed test cleared (> +25,000 and < -3pp): reopening-supply-overhang resolves as predicted. The margin is thin on the balance basis (about {BAL7_EX_ARB:+,.0f})."},
    {"category": "network", "severity": "medium", "finding":
     f"BUT IN THE LAST {LIVE_DAYS:.1f} DAYS THE SUPPLY STOPPED MOVING THE PRICE. EGLD {pc:+.1f}% to ${price:.2f} against BTC {M['btc_wow']:+.1f}%, the first window since run #27 that EGLD did not trail BTC. "
     f"Exchanges still took {ex['net']:+,.0f} EGLD net, about {PACE_NOW:,.0f}/day ex cross-venue wallets, no slower than run #31's ~{PACE_PREV:,.0f}/day: the supply kept arriving but was absorbed at a flat price. "
     f"Binance.com deposits slowed after Oct 16 (Oct 17-18: {f(BD.get('2026-10-17',{}).get('dep_egld',0))} and {f(BD.get('2026-10-18',{}).get('dep_egld',0))} in). The Upbit premium narrowed again to {PREM:.1f}% (from {PREM_PREV:.1f}%)."},
    {"category": "whale", "severity": "medium", "finding":
     f"A KNOWN BINANCE FUNDER SOLD THROUGH A FRESH HOP. erd1hhvfrw..., already labelled as funding a Binance deposit, sent {f(HHV_DEP)} EGLD on Oct 19 03:34 to a new wallet (nonce 1), which deposited it at Binance.com two minutes later. That is the window's largest single deposit and about two-thirds of Oct 19's deposits. "
     f"Cross-venue wallets moved {f(ARB_D2_IN + ARB_13_IN)} EGLD between Binance.com, Bybit and Gate.io and kept none; netted, Binance is {ENT_EX_ARB['Binance']:+,.0f}, Bybit {ENT_EX_ARB['Bybit']:+,.0f}, Gate.io {ENT_EX_ARB['Gate.io']:+,.0f}."},
    {"category": "staking", "severity": "medium", "finding":
     f"BOTH LARGE UNBONDS ARE STILL PENDING. Binance's {f(BIN_UNDEL)} EGLD matures about {BIN_MATURES[:16]} ({BIN_UNDEL_DAYS:.1f} days after collection) and the de-staking wallet is idle; binance-undelegation-destination moves to run #33. "
     f"The ninjastaking exiter's {f(NINJA['amount_egld'])} matures ~{NINJA_MATURES[:10]}, but the same wallet withdrew {f(NINJA_WD)} EGLD from two other providers on Oct 18 and re-delegated {f(NINJA_REDELEG)} of it to pi-staking within eight minutes, and the wallet is repaying Hatom USDC loans: an early sign of rotation and deleveraging, not a sale."},
    {"category": "staking", "severity": "low", "finding":
     f"EXITS HOLD AT ABOUT 86,000 A WEEK. {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD in {LIVE_DAYS:.1f} days (~{f(sk['undelegated_week']/LIVE_DAYS*7)}/week, the same pace as run #31) with no single exit above 25,000; {O['withdraw_calls']} withdraw calls returned {f(WD.get('egld_returned_total',0))}. "
     f"Delegators {sk['users_delta']:+d}; delegation TVL {sk['delta_locked']:+,.0f}; staked ratio {100*M['sr']:.2f}%. Compounding {cvc['compound_pct_of_reward_decisions']:.2f}%, in range."},
    {"category": "token", "severity": "low", "finding":
     f"USDC TURNED: SUPPLY {USDC_D:+,.0f} ({usdc['pct']:+.2f}%) TO {f(usdc['supply'])}, ending three straight declines. Through the xBridge wrapper {f(UB_['wrap_usdc'])} USDC came in and {f(UB_['unwrap_usdc'])} went out ({f(UB_['unwrap_by_destination_token'].get('BSCUSDC-887875',0))} to BSC, {f(UB_['unwrap_by_destination_token'].get('ETHUSDC-220753',0))} to Ethereum), and none of the top unwrappers swapped EGLD first. USDT {usdt['pct']:+.2f}%. "
     f"xExchange volume halved ({f(bid['dexvol_egld'])} EGLD/24h, {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.0f}%), {bid['wegld_usdc_share']:.0f}% WEGLD/USDC."},
    {"category": "whale", "severity": "low", "finding":
     f"WHALE B TOOK EGLD BACK OUT OF COINBASE. Coinbase sent {f(WB_IN)} EGLD to Unknown Whale B (now {f(WB['balance_egld'])}), the reverse of its run #30 sale; the Mega Whale did not move ({f(CBL['mega']['balance_egld'])}). mega-whale-coinbase-leg reached its run #32 deadline with neither branch met and closes inconclusive."},
]

R["network_health"] = {
    "economics": {"egld_price_usd": price, "market_cap_usd": econ["marketCap"],
                  "total_supply": econ["totalSupply"], "circulating_supply": econ["circulatingSupply"],
                  "staked_egld": econ["staked"], "staked_ratio": M["sr"], "staking_apr": econ["apr"],
                  "base_apr": econ["baseApr"], "topup_apr": econ["topUpApr"],
                  "token_market_cap_usd": econ["tokenMarketCap"]},
    "activity": {"total_accounts": st["accounts"], "total_transactions": st["transactions"],
                 "epoch": st["epoch"], "blocks": st["blocks"], "shards": st["shards"],
                 "transactions_7d": st["transactions"] - pact["total_transactions"],
                 "avg_daily_transactions": int((st["transactions"] - pact["total_transactions"]) / LIVE_DAYS)},
    "deltas": {"price_change_pct": pc,
               "market_cap_change_pct": 100 * (econ["marketCap"] - pecon["market_cap_usd"]) / pecon["market_cap_usd"],
               "staked_ratio_change_pp": 100 * (M["sr"] - M["sr_prev"]),
               "apr_change_pp": 100 * (econ["apr"] - pecon["staking_apr"]),
               "accounts_added": st["accounts"] - pact["total_accounts"],
               "transactions_added": st["transactions"] - pact["total_transactions"],
               "supply_added": econ["totalSupply"] - pecon["total_supply"],
               "staked_egld_added": M["staked_chg"], "epoch_advanced": st["epoch"] - pact["epoch"],
               "btc_correlation_note": f"BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%, EGLD {pc:+.2f}% over {LIVE_DAYS:.1f} days: EGLD {EGLD_VS_BTC:+.1f}pp vs BTC, the first non-negative window since run #27. Over the full 7 days EGLD {P7_EGLD:+.1f}% vs BTC {P7_BTC:+.1f}% ({P7_REL:+.1f}pp)."},
    "liveness": {"ok": D["liveness_ok"], "latest_block_by_shard": {k: iso(v["timestamp"]) for k, v in D["liveness"].items()},
                 "restart_1_utc": iso(1790181300), "restart_1_stopped_utc": iso(1790182386), "restart_2_utc": iso(1790263800),
                 "live_days_in_window": LIVE_DAYS, "rollback_point_utc": "2026-09-19 06:37:45 UTC"},
    "analysis": (
        f"WINDOW. {WINDOW_NOTE} Every shard read within seconds of real time. Epoch {st['epoch']} ({st['epoch']-pact['epoch']:+d}), "
        f"{f(st['transactions']-pact['total_transactions'])} transactions (~{f(int((st['transactions']-pact['total_transactions'])/LIVE_DAYS))}/day), {f(st['accounts']-pact['total_accounts'])} new accounts. Total supply {f(econ['totalSupply'])} ({econ['totalSupply']-pecon['total_supply']:+,}).\n\n"
        f"STAKING. Staked EGLD {M['staked_chg']:+,.0f} to {f(econ['staked'])}; ratio {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp). Delegation TVL fell {f(abs(sk['delta_locked']))}, spread across many small exits. "
        f"Binance's {f(BIN_UNDEL)} EGLD is still unbonding and still counted as staked; the ratio should step down about {100*BIN_UNDEL/econ['circulatingSupply']:.1f}pp around {BIN_MATURES[:10]} unless Binance re-stakes it. Network APR {100*econ['apr']:.2f}%.\n\n"
        f"PRICE. EGLD ${price:.2f}, {pc:+.2f}% against BTC {M['btc_wow']:+.2f}% and ETH {M['eth_wow']:+.2f}%: the slide since Oct 5 ($4.60) paused, and EGLD kept pace with BTC for the first time in five windows. Daily closes ran $3.56-$3.76 with no new low. "
        f"Binance bids within 2% of mid ${f(BOOK['binance']['depth_minus2_usd'])} (from ${f(BIN_BID_PREV)}), all venues ${f(BOOK['all']['depth_minus2_usd'])}. CEX spot volume over 7 days {f(BOOK['spot_volume_7d_egld']/1e6, 2)}M EGLD against {f(BOOK['spot_volume_prior_7d_egld']/1e6, 2)}M a week earlier: slightly less volume on a flat price, so selling eased without new buying showing up.")}


def tier(v):
    if v > 1_000_000: return "mega"
    if v >= 100_000: return "large"
    if v >= 10_000: return "mid"


def entity_interp(e):
    n = e["entity"]; v = VEN.get({"Binance": "Binance.com"}.get(n, n), {})
    st_ = v.get("state", "closed")
    if e["net_flow_egld"] == 0:
        return f"0: no EGLD deposit or withdrawal this week across {e['wallets_count']} wallet(s); the rail is closed on chain."
    if st_ == "deposit_only":
        return f"{e['net_flow_egld']:+,.0f}: deposit-side only ({v['in_txs']} deposits from {v['in_senders']} senders, 0 withdrawals). Users can send EGLD in; nothing comes out on the native chain."
    return f"{e['net_flow_egld']:+,.0f}: rail open both ways ({v.get('in_txs',0)} deposits / {v.get('out_txs',0)} withdrawals). A partial-rail reading, not a market-wide flow."


INV_SERIES = {**prev["otc_desk_inventory_series"], "run32": round(otc["desk_bal"])}
r26o = r26["whale_intelligence"]["otc_pipeline"]
venue_rows = [{"venue": k, "state": v["state"], "deposits_egld_txs_7d": v["in_txs"], "deposits_egld_7d": v["in_egld"],
               "distinct_depositors_7d": v["in_senders"], "withdrawals_egld_txs_7d": v["out_txs"], "withdrawals_egld_7d": v["out_egld"],
               "first_egld_deposit_utc": iso(v["first_in"]) if v["first_in"] else None,
               "first_egld_withdrawal_utc": iso(v["first_out"]) if v["first_out"] else None} for k, v in sorted(VEN.items(), key=lambda kv: -(kv[1]["in_egld"] + kv[1]["out_egld"]))]
R["whale_intelligence"] = {
    "large_transactions": O["large_txs"],
    "wallet_changes": O["wallet_changes"],
    "whale_tiers": {
        "mega_whales": dict(threshold_egld=1000000, **O["tiers"]["mega"]),
        "large_whales": dict(threshold_egld=100000, **O["tiers"]["large"]),
        "mid_whales": dict(threshold_egld=10000, **O["tiers"]["mid"])},
    "exchange_flows": {
        "total_exchange_egld_current": ex["total_cur"], "total_exchange_egld_previous": ex["total_prev"],
        "net_change_egld": ex["net"], "net_change_pct": 100 * ex["net"] / ex["total_prev"],
        "direction": "inflow" if ex["net"] >= 0 else "outflow",
        "rail_status": {"tracked_wallets": len(REOPEN), "egld_sends_since_restart": sum(v["out_txs"] for v in VEN.values()),
                        "egld_deposits_in_window": sum(v["in_txs"] for v in VEN.values()),
                        "egld_deposited_in_window": RAIL_EGLD_IN, "egld_withdrawn_in_window": RAIL_EGLD_OUT,
                        "venues_open": OPEN, "venues_deposit_only": DEPONLY, "venues_closed": [k for k, v in VEN.items() if v["state"] == "closed"],
                        "by_venue": venue_rows,
                        "note": f"Value-bearing EGLD transactions only (ESDT spam airdrops and exchange-internal sweeps excluded). {WIN_TXT}; rail window starts 09:47:20 UTC Oct 15 (run #31's commit) to avoid double counting. UPbit, MEXC, KuCoin, Bitfinex and Tokero moved no EGLD. Crypto.com's two wallets exchanged 2,603 EGLD internally (one hot -> staking sweep). Coinbase's routing wallet and the Binance de-staking wallet were idle. Web check: Upbit's caution review runs Oct 19-23, no outcome at collection.",
                        "rail_7d": {"start_utc": iso(R7_START), "days": R7_DAYS, "deposits_egld": R7_IN, "withdrawals_egld": R7_OUT, "net_egld": R7_NET,
                                    "cross_venue_deposits_egld": R7_ARB_IN, "cross_venue_withdrawals_egld": R7_ARB_OUT, "net_ex_cross_venue_egld": R7_NET_EX_ARB,
                                    "by_venue_net_egld": {k: v for k, v in R7_BY.items() if v}, "egld_change_pct": P7_EGLD, "btc_change_pct": P7_BTC, "egld_minus_btc_pp": P7_REL,
                                    "balance_basis_net_ex_cross_venue_egld": BAL7_EX_ARB}},
        "signal": (f"NET INFLOW CONTINUES. {len(OPEN)} tracked venues move EGLD both ways ({', '.join(OPEN)}). Net exchange balance change {ex['net']:+,.0f} EGLD over {LIVE_DAYS:.1f} days ({PACE_NOW:+,.0f}/day ex cross-venue, against ~{PACE_PREV:+,.0f}/day on the same basis in run #31): " + ", ".join(f"{e2['entity']} {e2['net_flow_egld']:+,.0f}" for e2 in ex["entity"] if e2["net_flow_egld"]) + ". "
                   f"Cross-venue wallets kept nothing this window (in = out), so the total is unaffected, but entity figures move: ex cross-venue, Binance {ENT_EX_ARB['Binance']:+,.0f}, Bybit {ENT_EX_ARB['Bybit']:+,.0f}, Gate.io {ENT_EX_ARB['Gate.io']:+,.0f}. "
                   f"FULL 7 DAYS (rails, Oct 12 15:05 -> Oct 19): {R7_NET:+,.0f} raw, {R7_NET_EX_ARB:+,.0f} ex cross-venue, on EGLD {P7_EGLD:+.1f}% vs BTC {P7_BTC:+.1f}%. Exchange-flow and OTC series stay out of the weekly baselines (UPbit closed)."),
        "by_exchange": [{"exchange": w["exchange"], "change_egld": w["change_egld"], "pct": w["pct"]} for w in ex["per_wallet"]],
        "entity_netting": [{"entity": e2["entity"], "wallets_count": e2["wallets_count"],
                            "net_flow_egld": e2["net_flow_egld"], "interpretation": entity_interp(e2)} for e2 in ex["entity"]]},
    "dormant_activations": [],
    "exit_routes": {
        "route_this_run": "no CEX exits; the one withdraw > 3,000 EGLD was re-delegated (ninjastaking exiter -> pi-staking)",
        "route_previous_run": "no CEX exits; one withdraw to a personal wallet",
        "scan_threshold_egld": 3000, "scan_calls": EXS["calls"], "scan_by_route": EXR,
        "scan_rows": [{"sender": r_["sender"], "sender_label": r_["sender_label"], "provider": r_["provider"], "withdrawn_egld": r_["withdrawn_egld"],
                       "route": r_["route"], "balance_now_egld": r_["balance_now"]} for r_ in EXS["rows"]],
        "traced_egld_ex_internal": EXIT_TRACED, "traced_to_cex_egld": EXIT_CEX,
        "binance_undelegation": {"wallet": "erd1r3w62vqmsux5e38p6vnueatmfcs8nr5lmg3s97x6rafqpgxfae0sxv9z0v", "egld": BIN_UNDEL,
                                 "called_utc": "2026-10-12 06:16 UTC", "unbonds_in_days": BIN_UNDEL_DAYS, "matures_utc": BIN_MATURES,
                                 "status": f"pending (userUndelegatedList, {BIN_UNDEL_DAYS:.1f} days left at collection), wallet idle in the window"},
        "binance_hot_to_custody_egld": 0.0,
        "largest_new_undelegation": {"wallet": NINJA["wallet"], "provider": "ninjastaking", "egld": NINJA["amount_egld"],
                                     "unbonds_in_days": NINJA["days_remaining"], "wallet_balance_egld": NINJA["wallet_balance_egld"],
                                     "note": f"carried from run #31; matures ~{NINJA_MATURES[:16]}. Same wallet withdrew {f(NINJA_WD)} from inceptionnetwork and pi-staking on Oct 18 and re-delegated {f(NINJA_REDELEG)} to pi-staking; active stake now {f(NINJA['active_stake_egld'])}."},
        "note": (f"Collector-side scan of every withdraw call above 3,000 EGLD in the window ({EXS['calls']} call): erd1me5hmqt5qg..., the run #31 ninjastaking exiter, withdrew {f(EXS['rows'][0]['withdrawn_egld'] if EXS['rows'] else 0)} from inceptionnetwork (and 2,000 from pi-staking) and re-delegated 5,000 to pi-staking eight minutes later; it also repaid a Hatom USDC borrow and sent 1,000 to a personal wallet. No exchange hop. "
                 f"{O['withdraw_calls']} withdraw calls (from {O['prev_withdraw_calls']}) returned {f(WD.get('egld_returned_total', 0))} EGLD. Two large items are pending: Binance's {f(BIN_UNDEL)} (matures ~{BIN_MATURES[:16]}) and erd1me5hmqt5qg...'s {f(NINJA['amount_egld'])} from ninjastaking (~{NINJA_MATURES[:10]}).")},
    "halt_recovery": {
        "invalid_balances_egld_now": HR["invalid_total_egld"],
        "invalid_balances_egld_at_halt": prev["halt_recovery_run27"]["invalid_balances_egld_at_halt"],
        "attacker_balance_egld": HR["attacker"].get("balance_egld"), "attacker_nonce": HR["attacker"].get("nonce"),
        "contract_balance_egld": HR["contract"].get("balance_egld"),
        "fanout_wallets_balance_egld": sum(v.get("balance_egld", 0) or 0 for v in HR["fanout"].values()),
        "legitimate_balances": {k: {"now_egld": v.get("balance_egld"),
                                    "pre_halt_egld": prev["pre_halt_reference_balances"].get(
                                        {"UPbit OTC Desk": "otc_desks", "OTC Distribution Wallet": "otc_desks",
                                         "Binance Staking custody": "binance_custody", "Hatom EGLD money market": "hatom_egld_mm"}[k])}
                                for k, v in HR["legit"].items()},
        "rollback_point_utc": "2026-09-19 06:37:45 UTC",
        "not_replayed_non_incident_txs": 1597, "not_replayed_value_egld": 467,
        "method_note": f"Sixth read after restart; invalid balances {HR['invalid_total_egld']:.2f} EGLD, unchanged."},
    "otc_pipeline": {
        "gross_outbound_egld_7d": otc["gross_out"], "gross_inbound_egld_7d": otc["gross_in"],
        "circular_egld_7d": otc["circular"], "net_one_way_egld_7d": otc["net_one_way"],
        "circular_share_pct": otc["circ_pct"],
        "desk_balance_egld": otc["desk_bal"], "previous_desk_balance_egld": otc["prev_desk"],
        "upbit_reload_egld": otc["upbit_feed"],
        "venue_netting": [],
        "router_tail_delivery_egld": 0.0, "router_tail_routers": 0,
        "gross_series_egld_7d": {**r26o["gross_series_egld_7d"], "run32": otc["gross_out"]},
        "net_one_way_series_egld_7d": {**r26o["net_one_way_series_egld_7d"], "run32": otc["net_one_way"]},
        "desk_inventory_series_egld": INV_SERIES,
        "circularity_series_pct": {**r26o["circularity_series_pct"], "run32": 0.0},
        "peak_window_renetted": r26o["peak_window_renetted"],
        "backfilled_windows": r26o.get("backfilled_windows", []),
        "wave_window_netting": {**r26o["wave_window_netting"],
            "note": f"Wave #4 stays closed at 467,107 EGLD one-way (Sep 7 to the halt, frozen labels). The post-restart window (Sep 24 - Oct 19) nets {f(otc['wave']['net_one_way'])} EGLD one-way."},
        "feed_by_parent_venue": [],
        "feeder_backtrace": O["feeder_backtrace"],
        "address_poisoning": [{"address": a, "mimics": v["note"], "nonce": v["nonce"], "dust_txs_30d": v["dust_txs_30d"],
                               "distinct_targets_30d": v["distinct_targets_30d"],
                               "inbound_above_0_01_egld": len(v["inbound_above_0_01_egld"])} for a, v in PZ.items()],
        "desk_terminal_resolved": {"address": TERM["address"], "nonce": TERM["info"].get("nonce"), "balance_egld": TERM_BAL, "role": "holder (nonce 1, no value sent)"},
        "series_note": (f"SILENT, {LIVE_DAYS:.1f}-DAY WINDOW. Gross out {f(otc['gross_out'])} EGLD: the UPbit desk sent two small payments (58 and 23 EGLD) to unlabelled wallets; nothing came in. No UPbit reload (UPbit's hot wallet had no EGLD flow). "
                        f"The Oct 6 terminal erd1y27r22... still holds {f(TERM_BAL, 1)} EGLD. Desks {f(otc['desk_bal'])}.")},
    "demand_instruments": {
        "identifiable_bid_absorbed_egld_7d": 0.0, "mega_whale_otc_leg_egld": MEGA_IN,
        "mega_whale_balance_egld": bid["mega_bal"] or 0.0, "mega_whale_change_egld": bid["mega_delta"],
        "coinbase_routing_balance_egld": bid["cbr_bal"] or 0.0, "coinbase_routing_inflow_egld": 0.0,
        "coinbase_routing_funder": "erd1m9qn6gvercs6ksvtn924w4y7z9ppglyfugpu34al26t9u4mvzvqqlq9dc3", "coinbase_routing_funder_label": "Coinbase (secondary); idle this window. Coinbase main instead sent 8,628 to Unknown Whale B (the reverse of run #30)",
        "weeks_at_zero": 12, "weeks_at_zero_in_last_four": 4, "bid_to_distribution_ratio_pct": 0.0,
        "dex_turnover_ratio_pct": bid["turnover"], "previous_dex_turnover_ratio_pct": bid["prev_turnover"],
        "dex_volume_egld_24h": bid["dexvol_egld"], "previous_dex_volume_egld_24h": bid["prev_dexvol_egld"],
        "pool_tvl_egld": bid["pooltvl_egld"], "previous_pool_tvl_egld": bid["prev_pooltvl_egld"],
        "wegld_usdc_volume_usd": bid["wegld_usdc_vol"], "wegld_usdc_share_of_volume_pct": bid["wegld_usdc_share"],
        "ex_wegld_usdc_volume_usd": bid["ex_wegld_usdc_vol"], "ex_wegld_usdc_volume_egld": bid["ex_wegld_usdc_vol_egld"],
        "dex_volume_status": "evaluable; compared with run #31",
        "absorber_scan": {"terminals_scanned": absb["scanned"],
                          "terminals_retaining_over_half": len(absb["retaining"]),
                          "total_received_from_desks_egld": absb["total_received"],
                          "total_retained_egld": absb["total_balance_held"],
                          "retained_share_pct": 0.0,
                          "verdict": f"Desk outbound {f(otc['gross_out'])} EGLD (two small payments); the instrument stays retired. The Mega Whale did not move."},
        "withdrawal_breadth": {"distinct_recipients_raw": br["raw_n"], "total_egld_raw": br["raw_egld"],
                               "distinct_recipients_ex_pipeline": br["ex_n"], "total_egld_ex_pipeline": br["ex_egld"],
                               "pipeline_share_pct": br["pipeline_share"], "top_two_share_pct": br["top_two_share_pct"]},
        "withdrawal_breadth_top": br["top"],
        "exchange_orderbook": {
            "source": "CoinGecko exchange tickers with 2% depth and daily spot volume (third-party). PARTIAL RAILS: UPbit closed on chain (no EGLD flow); Binance.com, Coinbase, Bybit, Gate.io, Crypto.com open",
            "binance": BOOK["binance"], "bybit": BOOK["bybit"], "upbit": BOOK["upbit"],
            "coinbase": BOOK["coinbase"], "gate": BOOK["gate"], "all_venues": BOOK["all"],
            "spot_volume_7d_egld": BOOK["spot_volume_7d_egld"] or 0.0,
            "spot_volume_prior_7d_egld": BOOK["spot_volume_prior_7d_egld"] or 0.0,
            "net_one_way_share_of_spot_volume_pct": 100 * otc["net_one_way"] / BOOK["spot_volume_7d_egld"] if BOOK["spot_volume_7d_egld"] else 0.0,
            "previous_net_one_way_share_of_spot_volume_pct": 0.0,
            "binance_bybit_net_delivery_usd_7d": 0.0,
            "binance_bybit_bid_depth_2pct_usd": BOOK["binance"]["depth_minus2_usd"] + BOOK["bybit"]["depth_minus2_usd"],
            "previous_binance_bybit_bid_depth_2pct_usd": prev["exchange_orderbook_closed_book_run27"]["binance"]["depth_minus2_usd"] + prev["exchange_orderbook_closed_book_run27"]["bybit"]["depth_minus2_usd"],
            "venue_depth_wow": {v: {"bid_now": BOOK[v]["depth_minus2_usd"], "bid_prev": prev["exchange_orderbook_closed_book_run27"][v]["depth_minus2_usd"],
                                    "ask_now": BOOK[v]["depth_plus2_usd"], "ask_prev": prev["exchange_orderbook_closed_book_run27"][v]["depth_plus2_usd"]}
                                for v in ("binance", "bybit", "upbit", "coinbase", "gate")},
            "korea_premium_pct": PREM, "previous_korea_premium_pct": PREM_PREV, "upbit_share_of_volume_pct": UP_SHARE,
            "previous_upbit_share_of_volume_pct": UPSH_PREV,
            "delivery_share_series": BOOK["delivery_share_series"], "top_tickers": BOOK["top"]}},
}
bbn = BOOK["binance"]["depth_minus2_usd"] + BOOK["bybit"]["depth_minus2_usd"]
bbn_prev = R["whale_intelligence"]["demand_instruments"]["exchange_orderbook"]["previous_binance_bybit_bid_depth_2pct_usd"]
wc = {w["address"]: w for w in O["wallet_changes"]}
R["whale_intelligence"]["analysis"] = (
    f"RAILS. Value-bearing EGLD per tracked exchange wallet, {WIN_TXT}: "
    + "; ".join(f"{k}: {v['state'].replace('_', ' ')} ({v['in_txs']} in / {v['out_txs']} out)" for k, v in VEN.items() if v["state"] != "closed")
    + f". No EGLD moved: {', '.join(k for k, v in VEN.items() if v['state'] == 'closed')}. No venue opened or closed.\n\n"
    f"THE FULL WEEK (run #31 rec #2). Rails from Oct 12 15:05:30 (after run #30's rail pass) to collection, {R7_DAYS:.1f} days: deposits {f(R7_IN)}, withdrawals {f(R7_OUT)}, net {R7_NET:+,.0f} EGLD. "
    f"Cross-venue wallets deposited {f(R7_ARB_IN)} and withdrew {f(R7_ARB_OUT)}; the {f(R7_ARB_IN-R7_ARB_OUT)} difference is erd1d2anjjha... emptying EGLD it had withdrawn before the window, so it comes out: {R7_NET_EX_ARB:+,.0f} ex cross-venue. By venue (raw, 7d): " + ", ".join(f"{k} {v:+,.0f}" for k, v in sorted(R7_BY.items(), key=lambda kv: -abs(kv[1])) if abs(v) >= 500)
    + f". Over the same days EGLD {P7_EGLD:+.1f}% and BTC {P7_BTC:+.1f}%. The balance-based equivalent (run #31 ex-arbitrage +7,218 plus this window) is {BAL7_EX_ARB:+,.0f}; the gap is mostly the rails' wider start and excluded internal sweeps.\n\n"
    f"BINANCE.COM. Per day since the Oct 9 reopening (deposits / withdrawals, EGLD, raw; Oct 12 includes the 161,137 internal custody send): " + "; ".join(f"{d_[5:]}: {f(v_['dep_egld'])} / {f(v_['wd_egld'])}" for d_, v_ in BD.items())
    + f". In this window {f(BIN_DEP)} in and {f(BIN_WD_EXT)} out ({BIN_EXT_PER_DAY:+,.0f}/day), but {f(ARB['erd1d2anjjha']['in_by_counterparty'].get('Binance.com',0))} of the withdrawals went to a cross-venue wallet and the largest deposit, {f(HHV_DEP)} on Oct 19, came from erd1hhvfrw... via a fresh nonce-1 hop (erd1rgm4td29...). "
    f"erd1hhvfrw... has fed Binance since run #29 (labelled); routing a single 12,223 EGLD lot through a new wallet two minutes before deposit looks like an attempt to keep the deposit from being linked, not a change of seller. Without it, Oct 17-19 deposits ran under 10,000 a day. The drip route erd137cw9q46... -> Binance.com carried {f(TR['binance_funders']['erd137cw9q']['to_binance_egld'])} EGLD (from 2,489 last window).\n\n"
    f"CROSS-VENUE WALLETS. erd1d2anjjha... withdrew {f(ARB['erd1d2anjjha']['in_by_counterparty'].get('Binance.com',0))} from Binance.com and {f(ARB['erd1d2anjjha']['in_by_counterparty'].get('Bybit',0))} from Bybit on Oct 16 03:27 and sent {f(ARB_D2_OUT)} to Gate.io at 23:00 the same day; erd13sytuz92... took {f(ARB_13_IN)} from Gate.io to Bybit at 05:42. Both ended at zero. Third window running for erd1d2anjjha... (about 56,000 EGLD moved toward Gate.io in total): one Gate.io client rebalancing across venues.\n\n"
    f"COINBASE AND WHALE B. Coinbase sent {f(WB_IN)} EGLD to Unknown Whale B on Oct 16 03:39 (Whale B now {f(WB['balance_egld'])}); in run #30 Whale B had deposited 122,054 at Coinbase. The Mega Whale ({f(CBL['mega']['balance_egld'])}) and the routing wallet ({f(CBL['cb_routing']['balance_egld'],1)}) did not move. Coinbase's entity outflow ({ent_net('Coinbase'):+,.0f}) is mostly this one withdrawal.\n\n"
    f"WHALES. Tiers on the common-address basis ({O['tiers_basis']} wallets): mega {O['tiers']['mega']['net_change_egld']:+,.0f} (no mega whale moved), large {O['tiers']['large']['net_change_egld']:+,.0f} (Binance.com +27,102, Whale B +8,628, the two growth funds +5,666 each, minus Bybit), mid {O['tiers']['mid']['net_change_egld']:+,.0f} (erd1hhvfrw... -12,637, Coinbase -12,053). No tier crossings.\n\n"
    f"UNKNOWN WHALE I: {CEN['Unknown Whale I']['inbound_txs']} inbound. erd1a6lte0: {CEN['erd1a6lte0']['inbound_txs']} inbound from {CEN['erd1a6lte0']['distinct_senders']} senders, down from 12.\n\n"
    f"DEMAND. Binance+Bybit bids within 2% of mid total ${f(bbn)} (closed-book base ${f(bbn_prev)}). Upbit's premium {PREM:.1f}% (from {PREM_PREV:.1f}%) on {UP_SHARE:.0f}% of global volume (from {UPSH_PREV:.0f}%), at the start of its Oct 19-23 review.")
# ---------------------------------------------------------------------------
provs = sk["provs"]; tl = sk["total_locked"]
paddr = {(p.get("address") or p["provider"]): p for p in prev["staking_providers"]}


def pk(p): return p.get("identity") or p["provider"]


def mv(ident, field, default=0):
    return next((m[field] for m in sk["moves"] if m["identity"] == ident), default)


top_providers = []
for i, p in enumerate(provs[:20], 1):
    pl = paddr.get(p["provider"], {}).get("locked_egld")
    top_providers.append({"rank": i, "identity": pk(p), "name": pk(p), "provider_address": p["provider"],
                          "locked_egld": p["_lk"], "previous_locked_egld": pl, "share_pct": 100 * p["_lk"] / tl,
                          "apr_pct": p.get("apr") or 0, "fee_pct": (p.get("serviceFee") or 0) * 100,
                          "num_users": p.get("numUsers") or 0, "num_nodes": p.get("numNodes") or 0,
                          "wow_change_egld": (p["_lk"] - pl) if pl is not None else None})
dser = {d["identity"]: d for d in O["dereg_series"]}
states = []
for r in zsc["emptied_inside_archive"]:
    d = dser.get(r["provider"], {})
    states.append({"provider": r["provider"], "state": "deregistered", "locked_egld": 0.0, "num_users": r["users"],
                   "num_nodes": r["nodes"], "apr_pct": 0.0, "fee_pct": 0.0,
                   "weeks_in_state": {"ledgerbyfigment": 16, "p2p_org_": 7, "truststakingsw": 18}.get(r["provider"], 5),
                   "note": f"emptied inside the archive (last locked > 0 snapshot {r['last_locked_in_archive']}); {r['inbound_txs_this_week']} inbound txs this week"
                           + (f"; delegators {d['prev_users']:,} -> {d['users']:,} ({d['users_delta']:+d})" if d.get("users") is not None and d.get("prev_users") is not None else "")})
for ident in ("egldstakingprovider", "procryptostaking"):
    states.append({"provider": ident, "state": "fee_squeezed", "locked_egld": mv(ident, "locked"),
                   "num_users": mv(ident, "users"), "num_nodes": mv(ident, "nodes"), "apr_pct": mv(ident, "apr") or 0.0,
                   "fee_pct": mv(ident, "fee") or 0.0, "weeks_in_state": 9,
                   "note": f"NINTH WEEK AFTER THE FEE REVERSAL ({LIVE_DAYS:.1f}-day window): book {mv(ident,'delta'):+,.0f}, users {mv(ident,'users_delta'):+d}. Flat."})
wd_top = WD.get("by_provider_top", [])
UNDEL_PACE = sk["undelegated_week"]
R["staking_intelligence"] = {
    "summary": {"total_staked_egld": econ["staked"], "total_delegated_egld": tl, "staked_ratio": M["sr"],
                "num_providers": len(provs), "apr_min": sk["apr_min"], "apr_max": sk["apr_max"], "apr_weighted_avg": sk["apr_wavg"]},
    "top_providers": top_providers,
    "concentration": {"top_5_share_pct": sk["top5"], "top_10_share_pct": sk["top10"], "hhi": sk["hhi"], "hhi_previous": sk["prev_hhi"],
                      "hhi_interpretation": f"HHI {sk['hhi']:.5f} (previous {sk['prev_hhi']:.5f}), far below the 0.15 competitive threshold; top-5 {sk['top5']:.2f}%, top-10 {sk['top10']:.2f}%."},
    "apr_distribution": {"buckets": sk["buckets"], "zero_apr_providers": sk["zero_apr_n"], "zero_apr_locked_egld": sk["zero_apr_locked"]},
    "apr_outliers": {
        "top_apr": [{"identity": pk(p), "name": pk(p), "apr_pct": p.get("apr") or 0, "fee_pct": (p.get("serviceFee") or 0) * 100, "locked_egld": p["_lk"]}
                    for p in sorted(provs, key=lambda x: -(x.get("apr") or 0))[:5]],
        "lowest_fee": [{"identity": pk(p), "name": pk(p), "apr_pct": p.get("apr") or 0, "fee_pct": (p.get("serviceFee") or 0) * 100, "locked_egld": p["_lk"]}
                       for p in sorted(provs, key=lambda x: ((x.get("serviceFee") or 0), -(x.get("apr") or 0)))[:5]]},
    "churn": {"total_delegators_current": sk["users"], "total_delegators_previous": sk["prev_users"],
              "delegators_added": sk["users_delta"], "delegators_change_pct": 100 * sk["users_delta"] / sk["prev_users"],
              "providers_gaining_delegators": sk["gaining"], "providers_losing_delegators": sk["losing"]},
    "provider_states": states,
    "identity_renames": O["identity_renames"],
    "zero_stake_cohort": {"contracts": zsc["contracts"], "attached_delegator_records": zsc["attached_delegator_records"],
                          "share_of_all_delegator_records_pct": zsc["share_of_all_delegator_records_pct"],
                          "emptied_inside_archive": len(zsc["emptied_inside_archive"]),
                          "with_activity_this_week": len(zsc["with_activity_this_week"]),
                          "archive_snapshots": zsc["archive_snapshots"], "archive_first_snapshot": zsc["archive_first"],
                          "transitions_this_week": len(O["dereg_transitions"]),
                          "note": f"Zero transitions for a ninth week. Join on contract address, {100*(sk['join_match_rate'] or 0):.0f}% match, no identity changes."},
    "fee_events": [{"provider": i, "fee_from_pct": 100.0, "fee_to_pct": mv(i, "fee") or 0.0, "apr_from_pct": 0.0, "apr_to_pct": mv(i, "apr") or 0.0,
                    "locked_egld": mv(i, "locked"), "locked_wow_egld": mv(i, "delta"), "users": mv(i, "users"),
                    "users_wow": mv(i, "users_delta"), "num_nodes": mv(i, "nodes")} for i in ("egldstakingprovider", "procryptostaking")],
    "unbonding_in_flight": {
        "wallet": ub["wallet"], "total_egld": ub["pending_total"],
        "legs": [{"provider": p["contract"][:10] + "..." + p["contract"][-8:], "amount": p["amount_egld"],
                  "days_to_unbond": p["days_remaining"], "date": "2026-08-14" if p["amount_egld"] < 100000 else "2026-08-15"} for p in ub["pending"]],
        "share_of_delegation_decline_pct": 0.0, "raw_residual_egld": sk["residual"], "corrected_direct_node_egld": None,
        "status": f"RETIRED, TENTH WEEK UNMOVED. Balance {f(ub['balance'],2)} EGLD, {f(ub['pending_total'])} unbonded-and-unclaimed.",
        "queue_this_week": {
            "undelegated_egld": sk["undelegated_week"], "distinct_callers": sk["undelegate_callers"],
            "measured_pending_egld": sk["pool_total"], "largest_legs": sk["pool_rows"][:12],
            "withdraw_calls": O["withdraw_calls"], "previous_withdraw_calls": O["prev_withdraw_calls"],
            "withdraw_egld_returned": WD.get("egld_returned_total", 0.0),
            "withdraw_egld_by_provider_top": [{"provider": a, "egld": b} for a, b in wd_top[:8]],
            "undelegated_weekly_pace_egld": UNDEL_PACE, "live_days": LIVE_DAYS,
            "coverage_note": (f"Full-set scan of {sk['providers_scanned']} provider contracts over the {LIVE_DAYS:.1f}-day window; no page caps hit. {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD; "
                              f"{O['withdraw_calls']} withdraw calls returned {f(WD.get('egld_returned_total',0))} EGLD.")}},
    "reward_behavior": {
        "providers_sampled": ag["providers_sampled"], "delegator_window_days": ag["window_days"], "operator_window_days": ag["operator_window_days"],
        "function_distribution": ag["overall_function_distribution"],
        "compound_pct_at_function_level": cvc["compound_pct_of_reward_decisions"],
        "compound_vs_claim": {"redelegate_count": cvc["redelegate_count"], "claim_count": cvc["claim_count"]},
        "delegator_fates_by_tier": fates,
        "provider_operators": [{"provider": pr.get("identity") or pr.get("provider_address"),
                                "owner_address": (pr.get("operator") or {}).get("owner_address") or pr.get("owner_address"),
                                "owner_label": (pr.get("operator") or {}).get("owner_label", "Unknown"),
                                "owner_balance_egld": (pr.get("operator") or {}).get("owner_balance_egld"),
                                "outbound_count": (pr.get("operator") or {}).get("outbound_count_30d", 0),
                                "fates_by_count": (pr.get("operator") or {}).get("fates_by_count", {}),
                                "fates_by_value_egld": (pr.get("operator") or {}).get("fates_by_value_egld", {})}
                               for pr in beh.get("per_provider", [])],
        "key_findings": [
            f"COMPOUND RATE {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} reDelegateRewards vs {cvc['claim_count']} claimRewards), from 59.40%. Series: 62.05 / 49.44 / 62.68 / 52.40 / 58.28 / 60.85 / 59.38 / 59.40 / {cvc['compound_pct_of_reward_decisions']:.2f}. Inside the 57-63% range for a sixth run.",
            f"Retail {fates['retail']['total_events']} claims, {fates['retail']['by_count'].get('sold',0)} to a labelled exchange; mid-tier {fates['mid_tier']['total_events']}, {fates['mid_tier']['by_count'].get('sold',0)} sold; institutional {fates.get('institutional',{}).get('total_events',0)}, {fates.get('institutional',{}).get('by_count',{}).get('sold',0)} sold (three claims, too few to read).",
            f"Sample: {ag['providers_sampled']} of {ag.get('providers_requested',8)} providers, 7-day delegator window (overlaps run #31's by about three days).",
            "PROVIDER OPERATORS DID NOT SELL FEES for a twentieth consecutive run (destinations: DeFi deposits, held, rotated)."]},
    "analysis": (
        f"EXITS STEADY, NO WHALE-SIZED CALL. {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD in {LIVE_DAYS:.1f} days across {sk['providers_scanned']} provider contracts with activity, about {f(sk['undelegated_week']/LIVE_DAYS*7)} a week: the same pace as run #31 (~86,000) and above run #30 (~54,000). "
        f"The largest are erd18qdhkls5e8... 10,450 and erd1qyt62v5ndd... 24,702 split across three providers (8,351 / 8,350 / 8,001); nothing like run #31's 26,699 or Binance's 320,002. Measured pending among the window's callers: {f(sk['pool_total'])} EGLD.\n\n"
        f"WITHDRAWALS ROSE BUT STAYED SMALL. {O['withdraw_calls']} withdraw calls (from {O['prev_withdraw_calls']}) returned {f(WD.get('egld_returned_total',0))} EGLD, led by pi-staking ({f(wd_top0)}). The one call above 3,000 EGLD was re-delegated. Still queued: Binance's {f(BIN_UNDEL)} (~{BIN_MATURES[:10]}) and the ninjastaking exiter's {f(NINJA['amount_egld'])} (~{NINJA_MATURES[:10]}).\n\n"
        f"THE RATIO AND THE RESIDUAL. Delegation TVL {sk['delta_locked']:+,.0f} to {f(tl)} while /economics staked moved {M['staked_chg']:+,.0f}: undelegated EGLD stays in 'staked' until it unbonds. Ratio {100*M['sr']:.2f}%. HHI {sk['hhi']:.5f} (from {sk['prev_hhi']:.5f}). 74 of 102 APR-bearing providers sit in the 8-9% bucket; pi-staking (9.70%, 0% fee) and pokerstaking (9.65%, 0% fee) are the best headline deals.\n\n"
        f"COMPOUNDING {cvc['compound_pct_of_reward_decisions']:.2f}%. DELEGATORS {sk['users_delta']:+,} to {f(sk['users'])}; {sk['gaining']} providers gained and {sk['losing']} lost. pi-staking led inflows ({mv('pi-staking','delta'):+,.0f}, {mv('pi-staking','users_delta'):+d} delegators, partly the ninjastaking exiter's 5,000), ninjastaking ({mv('ninjastaking','delta'):+,.0f}), bober, westake and Synexis led outflows. binance_staking {BINP['delta']:+,.0f} to {f(BINP['locked'])}. Zero deregistration transitions for a ninth week.")}
# ---------------------------------------------------------------------------
ph = {t["identifier"]: t for t in prev["top_tokens_by_holders"]}
pv = {t["identifier"]: t for t in prev["top_tokens_by_volume"]}


def th(t):
    i = t["identifier"]; prevh = ph.get(i, {}).get("holders")
    return {"identifier": i, "name": t.get("name"), "holders": t.get("accounts") or 0, "previous_holders": prevh,
            "holders_change": (t.get("accounts", 0) - prevh) if prevh is not None else None,
            "price_usd": t.get("price"), "market_cap_usd": t.get("marketCap"), "volume_24h_usd": None}


def tv(t):
    i = t["identifier"]; pt = pv.get(i, {}).get("transactions")
    return {"identifier": i, "name": t.get("name"), "transactions": t.get("transactions") or 0, "previous_transactions": pt,
            "change_pct": (100 * (t.get("transactions", 0) - pt) / pt) if pt else None, "price_usd": t.get("price"), "volume_24h_usd": None}


def tm(t):
    i = t["identifier"]
    return {"identifier": i, "name": t.get("name"), "holders": t.get("accounts"), "previous_holders": ph.get(i, {}).get("holders"),
            "price_usd": t.get("price"), "market_cap_usd": t.get("marketCap"), "volume_24h_usd": None}


newly = tk["newly"]
top_pair = xx["top_pairs"][0] if xx["top_pairs"] else {"name": "n/a", "volume_24h_usd": 0.0, "share_pct": 0.0}
R["token_activity"] = {
    "top_by_holders": [th(t) for t in D["tokens_holders"][:10]],
    "top_by_volume": [tv(t) for t in D["tokens_txs"][:10]],
    "top_by_market_cap": [tm(t) for t in D["tokens_mcap"][:10]],
    "newly_issued": [{"identifier": t["identifier"], "name": t["name"], "holders": t["accounts"], "transactions": t["transactions"],
                      "deployer": t["deployer"], "note": "below the >10 holder / >5 tx bar"} for t in newly],
    "xexchange": {
        "total_pairs": xx["pairs"], "total_volume_24h_usd": xx["vol"], "mex_price_usd": xx["mex_price"], "mex_market_cap_usd": xx["mex_mcap"],
        "mex_price_change_24h_pct": None, "mex_price_change_wow_pct": xx["mex_wow"], "mex_price_source": xx["mex_price_source"],
        "top_pair": top_pair["name"], "top_pair_volume_24h_usd": top_pair["volume_24h_usd"], "top_pair_dominance_pct": top_pair["share_pct"],
        "top_pairs_by_volume": xx["top_pairs"],
        "pool_tvl_usd": xx["pool_tvl"], "previous_pool_tvl_usd": xx["prev_pool_tvl"],
        "turnover_ratio_pct": bid["turnover"], "previous_turnover_ratio_pct": bid["prev_turnover"],
        "dex_vol_wow_pct": 100 * (xx["vol"] - xx["prev_vol"]) / xx["prev_vol"],
        "dex_volume_egld_24h": bid["dexvol_egld"], "previous_dex_volume_egld_24h": bid["prev_dexvol_egld"],
        "dex_vol_egld_wow_pct": 100 * (bid["dexvol_egld"] - bid["prev_dexvol_egld"]) / bid["prev_dexvol_egld"],
        "pool_tvl_egld": bid["pooltvl_egld"], "previous_pool_tvl_egld": bid["prev_pooltvl_egld"],
        "wegld_usdc_share_of_volume_pct": bid["wegld_usdc_share"], "ex_wegld_usdc_volume_usd": bid["ex_wegld_usdc_vol"],
        "volume_status": "evaluable; compared with run #31 (24h snapshots)",
        "mex_pair_depth": {"pair": "MEX/WEGLD", "tvl_usd": xx["mex_pair_depth"]["tvl_usd"], "tvl_egld": xx["mex_pair_depth"]["tvl_egld"],
                           "previous_tvl_egld": xx["mex_pair_depth"]["previous_tvl_egld"], "tvl_egld_wow_pct": xx["mex_pair_depth"]["tvl_egld_wow_pct"],
                           "volume_24h_usd": xx["mex_pair_depth"]["volume_24h_usd"], "trades_24h": xx["mex_pair_depth"]["trades_24h"],
                           "share_of_pool_tvl_pct": xx["mex_pair_depth"]["share_of_pool_tvl_pct"], "depth_rank": xx["mex_pair_depth"]["depth_rank"]},
        "mex_pair_event": r26["token_activity"]["xexchange"]["mex_pair_event"]},
    "analysis": (
        f"DEX VOLUME HALVED. 24h volume ${f(xx['vol'])} ({f(bid['dexvol_egld'])} EGLD) against ${f(xx['prev_vol'])} ({f(bid['prev_dexvol_egld'])} EGLD) at the last snapshot, {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.0f}% in EGLD. "
        f"WEGLD/USDC is {bid['wegld_usdc_share']:.0f}% of it: the venue is effectively one EGLD/dollar pool arbitraged against the exchanges; everything else traded ${f(bid['ex_wegld_usdc_vol'])}. Turnover {bid['turnover']:.2f}% of pool TVL (from {bid['prev_turnover']:.2f}%). Pool TVL {f(bid['pooltvl_egld'])} EGLD ({100*(bid['pooltvl_egld']-bid['prev_pooltvl_egld'])/bid['prev_pooltvl_egld']:+.1f}% in EGLD), ${f(bid['pooltvl'])} ({100*(bid['pooltvl']-bid['prev_pooltvl'])/bid['prev_pooltvl']:+.1f}%) in dollars, mostly the price.\n\n"
        f"MEX ${xx['mex_price']:.2e} ({xx['mex_wow']:+.1f}% over the window, against EGLD {pc:+.1f}%); MEX/WEGLD depth ${f(xx['mex_pair_depth']['tvl_usd'])} ({xx['mex_pair_depth']['tvl_egld_wow_pct']:+.1f}% in EGLD), rank {xx['mex_pair_depth']['depth_rank']}.\n\n"
        f"STABLECOINS. USDC {usdc['pct']:+.2f}% ({USDC_D:+,.0f}) to {f(usdc['supply'])}, the first rise after three declines. Traced through the xBridge Tokens Wrapper (run #31 rec #5): {UB_['wrap_txs']} wraps brought in {f(UB_['wrap_usdc'])} USDC and {UB_['unwrap_txs']} unwraps sent {f(UB_['unwrap_usdc'])} out, {f(UB_['unwrap_by_destination_token'].get('BSCUSDC-887875',0))} of it to BSC and {f(UB_['unwrap_by_destination_token'].get('ETHUSDC-220753',0))} to Ethereum; net {USDC_NET_IN:+,.0f}, within a few hundred of the supply change. "
        f"The largest unwrapper (erd1ltetacm7..., {f(list(UB_['top_unwrappers'].values())[0]['usdc'])} USDC in two calls) and the next five made no EGLD swap and received nothing from an exchange in the prior 7 days: dollars leaving, not EGLD sold for dollars. USDT {usdt['pct']:+.2f}% to {f(usdt['supply'])}. "
        f"NEWLY ISSUED: {len(newly)} issuances in the window ({', '.join(t['identifier'] for t in newly)}), each with 1-4 holders, below the traction bar.")}
# ---------------------------------------------------------------------------
em = O["emerging_lsd"]; proto = df["proto"]; jex7 = O["jex_router_7d"]
STAKE = {}
for p_ in disc["liquid_staking_protocols"]:
    for t_ in p_.get("receipt_tokens", []):
        STAKE[t_["identifier"]] = p_.get("staked_egld")
EMP = prev["lsd_staked_emerging"]
EM_PREV = {"LEGLD-d74da9": EMP.get("SALSA: Liquid Staking"), "VOXEGLD-5872e5": EMP.get("Dinovox: VoxEGLD Liquid Staking"),
           "VEGLD-2b9319": EMP.get("VestaX Finance: Liquid Staking"), "JWLEGLD-023462": EMP.get("JewelSwap: Liquid Staking")}


def es(t): return STAKE.get(t)


def ep(t):
    p0 = EM_PREV.get(t); c = es(t)
    return 100 * (c - p0) / p0 if (p0 and c is not None) else None


def hs(pct):
    if pct is None: return None
    if pct > 50: return "spiking"
    if pct > 5: return "growing"
    if pct < -15: return "draining"
    if pct < -2: return "shrinking"
    return "flat"


def cnt(n):
    v = proto.get(n)
    return v if isinstance(v, int) else None


xe_egld_pct = 100 * (df["xexch_egld"] - df["xexch_prev_usd"] / pecon["egld_price_usd"]) / (df["xexch_prev_usd"] / pecon["egld_price_usd"])
R["defi_activity"] = {
    "protocols": [
        {"name": "xExchange", "category": "dex", "volume_24h_usd": xx["vol"], "active_pairs": xx["pairs"], "transfers_24h": None,
         "tvl_usd": df["xexch_usd"], "tvl_egld": df["xexch_egld"], "tvl_wow_change_pct": xe_egld_pct},
        {"name": "Hatom Lending", "category": "lending", "volume_24h_usd": 0.0, "active_pairs": 0, "transfers_24h": cnt("Hatom EGLD MM"),
         "tvl_usd": df["hatom_lending_usd"], "tvl_egld": df["hatom_lending_egld"], "tvl_wow_change_pct": hl},
        {"name": "Hatom Liquid Staking", "category": "liquid_staking", "volume_24h_usd": 0.0, "active_pairs": 0, "transfers_24h": cnt("Hatom Liquid Staking"),
         "tvl_usd": df["hatom_lsd_usd"], "tvl_egld": df["hatom_lsd_usd"] / price, "tvl_wow_change_pct": lsd["SEGLD-3ad2d0"]["pct"]},
        {"name": "XOXNO LSD", "category": "liquid_staking", "volume_24h_usd": 0.0, "active_pairs": 0, "transfers_24h": cnt("XOXNO LSD"),
         "tvl_usd": df["xoxno_usd"], "tvl_egld": df["xoxno_usd"] / price, "tvl_wow_change_pct": lsd["XEGLD-e413ed"]["pct"]}],
    "protocol_breakdown": [
        {"protocol": "xExchange", "category": "dex", "addresses_tracked": 17, "tvl_usd": df["xexch_usd"], "tvl_egld": df["xexch_egld"],
         "tvl_wow_change_pct": xe_egld_pct, "transfers_24h": None, "volume_24h_usd": xx["vol"],
         "notable_events": f"Volume ${f(xx['vol'])}/24h, {bid['wegld_usdc_share']:.0f}% WEGLD/USDC. WEGLD contract balances {f(df['xexch_egld'])} EGLD ({xe_egld_pct:+.1f}%).",
         "health_signal": hs(xe_egld_pct)},
        {"protocol": "Hatom Lending", "category": "lending", "addresses_tracked": 13, "tvl_usd": df["hatom_lending_usd"], "tvl_egld": df["hatom_lending_egld"],
         "tvl_wow_change_pct": hl, "transfers_24h": cnt("Hatom EGLD MM"),
         "notable_events": f"EGLD market {f(df['egld_mm_prev_balance'])} -> {f(df['egld_mm_balance'])} EGLD, HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.2f}%, HUSDC {HT['HUSDC-d80042']['supply_pct']:+.2f}%. Aggregate lending TVL in EGLD {hl:+.2f}% on a {pc:+.2f}% price window: small real deposits, not the price mechanism.",
         "health_signal": "draining" if EMM_D < -25000 else ("growing" if EMM_D > 5000 else "flat")},
        {"protocol": "Hatom Liquid Staking", "category": "liquid_staking", "addresses_tracked": 2, "tvl_usd": df["hatom_lsd_usd"], "tvl_egld": df["hatom_lsd_usd"] / price,
         "tvl_wow_change_pct": lsd["SEGLD-3ad2d0"]["pct"], "transfers_24h": cnt("Hatom Liquid Staking"),
         "notable_events": f"SEGLD supply {lsd['SEGLD-3ad2d0']['pct']:+.2f}% to {f(lsd['SEGLD-3ad2d0']['supply'])}; SWTAO {lsd['SWTAO-356a25']['pct']:+.2f}%.",
         "health_signal": hs(lsd["SEGLD-3ad2d0"]["pct"])},
        {"protocol": "Hatom USH", "category": "stablecoin", "addresses_tracked": 4, "tvl_usd": df["ush_usd"], "tvl_egld": df["ush_usd"] / price,
         "tvl_wow_change_pct": lsd["USH-111e09"]["pct"], "transfers_24h": None,
         "notable_events": f"USH {lsd['USH-111e09']['pct']:+.2f}% to {f(lsd['USH-111e09']['supply'])}.", "health_signal": hs(lsd["USH-111e09"]["pct"])},
        {"protocol": "XOXNO LSD", "category": "liquid_staking", "addresses_tracked": 3, "tvl_usd": df["xoxno_usd"], "tvl_egld": df["xoxno_usd"] / price,
         "tvl_wow_change_pct": lsd["XEGLD-e413ed"]["pct"], "transfers_24h": cnt("XOXNO LSD"),
         "notable_events": f"XEGLD supply {lsd['XEGLD-e413ed']['pct']:+.2f}% to {f(lsd['XEGLD-e413ed']['supply'])}.",
         "health_signal": hs(lsd["XEGLD-e413ed"]["pct"])},
        {"protocol": "XOXNO Aggregator", "category": "aggregator", "addresses_tracked": 1, "tvl_usd": 0.0, "tvl_egld": 0.0, "tvl_wow_change_pct": None,
         "transfers_24h": cnt("XOXNO Aggregator"), "volume_24h_usd": 0.0, "notable_events": f"{f(cnt('XOXNO Aggregator'))} transfers in 24h.", "health_signal": "flat"},
        {"protocol": "OneDex", "category": "aggregator", "addresses_tracked": 5, "tvl_usd": 0.0, "tvl_egld": 0.0, "tvl_wow_change_pct": None,
         "transfers_24h": cnt("OneDex Swap"), "volume_24h_usd": 0.0, "notable_events": f"{f(cnt('OneDex Swap'))} transfers in 24h. OneDex Launchpad still fails bech32 validation.", "health_signal": "flat"},
        {"protocol": "JEXchange", "category": "dex", "addresses_tracked": 10, "tvl_usd": 0.0, "tvl_egld": 0.0, "tvl_wow_change_pct": None,
         "transfers_24h": cnt("JEXchange Router"), "volume_24h_usd": 0.0,
         "notable_events": f"7-day router transfers {f(jex7.get('JEXchange Router'))} on the main router (7 live days), " + ", ".join(f(jex7.get(f'JEXchange Router {i}')) for i in range(2, 6)) + " on routers 2-5.",
         "health_signal": "shrinking"},
        {"protocol": "JewelSwap", "category": "liquid_staking", "addresses_tracked": 1, "tvl_usd": (es("JWLEGLD-023462") or 0) * price, "tvl_egld": es("JWLEGLD-023462") or 0.0,
         "tvl_wow_change_pct": ep("JWLEGLD-023462"), "transfers_24h": None,
         "notable_events": f"{f(es('JWLEGLD-023462'))} EGLD delegated, {em['JWLEGLD-023462']['holders']} holders.", "health_signal": hs(ep("JWLEGLD-023462"))},
        {"protocol": "SALSA (Staking Agency)", "category": "liquid_staking", "addresses_tracked": 1, "tvl_usd": (es("LEGLD-d74da9") or 0) * price, "tvl_egld": es("LEGLD-d74da9") or 0.0,
         "tvl_wow_change_pct": ep("LEGLD-d74da9"), "transfers_24h": None,
         "notable_events": f"{f(es('LEGLD-d74da9'))} EGLD delegated; LEGLD supply {(em['LEGLD-d74da9']['pct'] or 0):+.2f}%.", "health_signal": hs(ep("LEGLD-d74da9"))},
        {"protocol": "Dinovox VoxEGLD", "category": "liquid_staking", "addresses_tracked": 1, "tvl_usd": (es("VOXEGLD-5872e5") or 0) * price, "tvl_egld": es("VOXEGLD-5872e5") or 0.0,
         "tvl_wow_change_pct": ep("VOXEGLD-5872e5"), "transfers_24h": None,
         "notable_events": f"{f(es('VOXEGLD-5872e5'))} EGLD, supply {(em['VOXEGLD-5872e5']['pct'] or 0):+.1f}%, holders {em['VOXEGLD-5872e5']['holders']}: growth slowed to under 1%.", "health_signal": hs(ep("VOXEGLD-5872e5"))},
        {"protocol": "VestaX Finance", "category": "liquid_staking", "addresses_tracked": 1, "tvl_usd": (es("VEGLD-2b9319") or 0) * price, "tvl_egld": es("VEGLD-2b9319") or 0.0,
         "tvl_wow_change_pct": ep("VEGLD-2b9319"), "transfers_24h": None,
         "notable_events": f"{f(es('VEGLD-2b9319'))} EGLD.", "health_signal": hs(ep("VEGLD-2b9319"))}],
    "sc_deployments": [],
    "analysis": (
        f"HATOM'S EGLD MARKET STOPPED SHRINKING. The EGLD money market holds {f(df['egld_mm_balance'])} EGLD, from {f(df['egld_mm_prev_balance'])} ({EMM_D:+,.0f}, after -12,786 in run #30 and -2,161 in run #31); HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.2f}%. "
        f"Calls in the window: {HMM['by_function'].get('repayBorrow',{}).get('n',0)} loan repayments from {HMM['by_function'].get('repayBorrow',{}).get('distinct_senders',0)} wallets, {HMM['by_function'].get('borrow',{}).get('n',0)} borrows from {HMM['by_function'].get('borrow',{}).get('distinct_senders',0)}, {HMM['by_function'].get('mintAndEnterMarket',{}).get('n',0)} supply-and-collateral calls, {HMM['redeem_calls']} redeems, {HMM['liquidation_calls']} liquidations. More repaying than borrowing, and redemptions dried up: borrowers are deleveraging into the flat price rather than being forced out. The ninjastaking exiter is one of them (a USDC loan repayment on Oct 18).\n\n"
        f"INVERSE-RATIO RULE. Aggregate lending TVL ex-HMEX reads {hl:+.2f}% in EGLD on a {pc:+.2f}% price move, so this window the EGLD-denominated rise is not the price mechanism (EGLD rose); it is HEGLD {HT['HEGLD-d61095']['supply_pct']:+.2f}%, HUSDT {HT['HUSDT-6f0914']['supply_pct']:+.2f}% and HUSDC {HT['HUSDC-d80042']['supply_pct']:+.2f}%: small real deposits.\n\n"
        f"LIQUID STAKING. SEGLD {lsd['SEGLD-3ad2d0']['pct']:+.2f}%, XEGLD {lsd['XEGLD-e413ed']['pct']:+.2f}%, SWTAO {lsd['SWTAO-356a25']['pct']:+.2f}%, USH {lsd['USH-111e09']['pct']:+.2f}%: flat. The emerging LSDs barely moved (VoxEGLD {(em['VOXEGLD-5872e5']['pct'] or 0):+.1f}%, LEGLD {(em['LEGLD-d74da9']['pct'] or 0):+.1f}%). Hatom's liquid-staking contract balance rose 3,872 EGLD (buffer, not TVL).\n\n"
        f"ACTIVITY. XOXNO aggregator {f(cnt('XOXNO Aggregator'))} transfers in 24h, OneDex {f(cnt('OneDex Swap'))}, Hatom LSD {f(cnt('Hatom Liquid Staking'))}. JEXchange router transfers over 7 days {f(jex7.get('JEXchange Router'))} on the main router.")}

# ---------------------------------------------------------------------------
R["anomalies"] = [
    {"metric": "exchange_net_flow_egld_7d_rails", "current_value": R7_NET_EX_ARB, "previous_value": None, "method": "rule_based", "severity": "medium",
     "change_pct": None,
     "description": f"Full-week rails: tracked exchanges {R7_NET:+,.0f} EGLD raw, {R7_NET_EX_ARB:+,.0f} ex cross-venue wallets, with EGLD {P7_REL:+.1f}pp vs BTC. Resolves reopening-supply-overhang as predicted. Not z-scored: UPbit is closed, so the series stays out of the weekly baseline."},
    {"metric": "egld_price_usd", "current_value": price, "previous_value": M["prev_price"], "method": "z_score", "severity": z["price"].get("severity", "low"),
     "average_value": z["price"].get("mean"), "stddev": z["price"].get("stddev"), "z_score": zz("price"), "change_pct": pc,
     "description": f"{pc:+.2f}% in {LIVE_DAYS:.1f} days (BTC {M['btc_wow']:+.2f}%); z={zz('price'):+.2f} against an 8-reading baseline that still holds the pre-halt $4+ prices. First window since run #27 that EGLD did not trail BTC."},
    {"metric": "dex_volume_24h_egld", "current_value": bid["dexvol_egld"], "previous_value": bid["prev_dexvol_egld"], "method": "z_score", "severity": z["dexvol"].get("severity", "low"),
     "average_value": z["dexvol"].get("mean"), "stddev": z["dexvol"].get("stddev"), "z_score": zz("dexvol"),
     "change_pct": 100 * (bid["dexvol_egld"] - bid["prev_dexvol_egld"]) / bid["prev_dexvol_egld"],
     "description": f"xExchange 24h volume {f(bid['dexvol_egld'])} EGLD ({100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.0f}%), {bid['wegld_usdc_share']:.0f}% WEGLD/USDC; turnover {bid['turnover']:.2f}% from {bid['prev_turnover']:.2f}%. z in dollars {zz('dexvol'):+.2f}: low, but a single 24h snapshot on a quiet Monday."},
    {"metric": "usdc_supply", "current_value": usdc["supply"], "previous_value": usdc["prev"], "method": "rule_based", "severity": "low",
     "change_pct": usdc["pct"],
     "description": f"USDC {USDC_D:+,.0f} after three declines; wrapper net {USDC_NET_IN:+,.0f} (in {f(UB_['wrap_usdc'])}, out {f(UB_['unwrap_usdc'])}, mostly to BSC)."},
    {"metric": "binance_single_deposit_via_fresh_hop", "current_value": HHV_DEP, "previous_value": None, "method": "rule_based", "severity": "low",
     "change_pct": None,
     "description": f"{f(HHV_DEP)} EGLD from labelled Binance funder erd1hhvfrw... through a new nonce-1 wallet, deposited two minutes after funding. Largest deposit of the window."},
    {"metric": "korea_premium_pct", "current_value": PREM, "previous_value": PREM_PREV, "method": "rule_based", "severity": "low",
     "change_pct": 100 * (PREM - PREM_PREV) / PREM_PREV,
     "description": f"Upbit premium {PREM:.1f}% from {PREM_PREV:.1f}%; Upbit {UP_SHARE:.0f}% of global volume (from {UPSH_PREV:.0f}%). UPbit rails closed; review Oct 19-23 under way."},
]

R["trend_indicators"] = {
    "accelerating_exchange_outflows": [],
    "validator_movements": {"providers_joining": 0, "providers_leaving": 0, "net_provider_change": 0, "notable_joiners": [],
                            "notable_leavers": [], "note": "No joins or deregistrations for a ninth week."},
    "token_supply_events": [
        {"identifier": "USDC-c76f1f", "name": "WrappedUSDC", "event": "mint", "supply_previous": str(int(usdc["prev"])), "supply_current": str(int(usdc["supply"])),
         "change_pct": usdc["pct"], "description": f"{USDC_D:+,.0f} USDC: bridge inflow {f(UB_['wrap_usdc'])} exceeded outflow {f(UB_['unwrap_usdc'])}. Ends three declines."},
        {"identifier": "USDT-f8c08c", "name": "USDT", "event": "mint", "supply_previous": str(int(usdt["prev"])), "supply_current": str(int(usdt["supply"])),
         "change_pct": usdt["pct"], "description": f"{f(usdt['supply']-usdt['prev'])} USDT added."}],
    "consecutive_streaks": [
        {"metric": "exchange_net_inflow_since_reopening", "direction": "up", "weeks": 5, "cumulative_change_pct": None,
         "interpretation": f"Tracked exchanges took net deposits in every window since the rails reopened (runs #28-#32; this one {ex['net']:+,.0f}). Ex cross-venue wallets the pace held at ~{PACE_NOW:,.0f}/day (run #31 ~{PACE_PREV:,.0f}/day); what changed is that EGLD stopped falling against BTC."},
        {"metric": "egld_vs_btc", "direction": "flat", "weeks": 1, "cumulative_change_pct": None,
         "interpretation": f"Four-window underperformance streak ended: EGLD {EGLD_VS_BTC:+.1f}pp vs BTC this window. Over the full week still {P7_REL:+.1f}pp."},
        {"metric": "total_delegators", "direction": "flat", "weeks": 20, "cumulative_change_pct": -1.2, "interpretation": f"{sk['users_delta']:+,} to {f(sk['users'])}. The base rate."},
        {"metric": "provider_operator_fee_selling", "direction": "flat", "weeks": 20, "cumulative_change_pct": 0.0, "interpretation": "Twenty runs with zero exchange destinations from sampled operator wallets."},
        {"metric": "undelegation_pace", "direction": "up", "weeks": 2, "cumulative_change_pct": None, "interpretation": f"~86,000/week for a second window (run #30 ~54,000), now without a single large exit."}],
    "regime_shifts": [
        {"metric": "exchange_rail_state", "before_value": 0.0, "after_value": round(len(OPEN) / max(1, len([k for k in VEN if k not in _NONVENUE])), 2),
         "description": f"Unchanged: {len(OPEN)} of {len([k for k in VEN if k not in _NONVENUE])} tracked venues move EGLD both ways ({', '.join(OPEN)}). UPbit had no EGLD flow. Promote when UPbit opens both ways."},
        {"metric": "binance_staking_allocation", "before_value": 399100.0, "after_value": BINP["locked"],
         "description": f"CANDIDATE, unchanged: {f(BIN_UNDEL)} EGLD in Binance's unbonding queue, maturing ~{BIN_MATURES[:16]}. Resolve on where the withdraw goes (run #33)."},
        {"metric": "rails_reopened_price_path", "before_value": 4.60, "after_value": price,
         "description": f"PROMOTED (reopening-supply-overhang, as predicted): over the first full week EGLD fell {abs(P7_EGLD):.1f}% ({P7_REL:+.1f}pp vs BTC) with {R7_NET_EX_ARB:+,.0f} EGLD net to exchanges ex cross-venue. In the last {LIVE_DAYS:.1f} days inflow continued at the same ex cross-venue pace but EGLD held level with BTC; overhang-absorbed tests whether the inflow itself ends next week."}]}

R["watch_list"] = [
    {"item": f"BINANCE UNBOND - {f(BIN_UNDEL)} EGLD matures ~{BIN_MATURES[:16]}", "weeks_on_list": 3,
     "reason": f"Still pending ({BIN_UNDEL_DAYS:.1f} days left at collection). Custody, re-delegation or hot wallet? PRE-COMMITTED (binance-undelegation-destination), now evaluable at run #33."},
    {"item": "UPBIT CAUTION REVIEW Oct 19-23", "weeks_on_list": 6,
     "reason": f"Decision due this week. Premium {PREM:.1f}% (from {PREM_PREV:.1f}%), {UP_SHARE:.0f}% of global volume; UPbit had no EGLD flow; {UPD['distinct_depositors']} distinct depositors since restart. A delisting retires korea-premium-arbitrage and delivery-price-relevance-2."},
    {"item": "EXCHANGE NET INFLOW - ABSORBED?", "weeks_on_list": 2,
     "reason": f"Overhang confirmed on the full week ({R7_NET_EX_ARB:+,.0f} ex cross-venue). This window inflow continued (~{PACE_NOW:,.0f}/day ex cross-venue) but EGLD held level with BTC. PRE-COMMITTED (overhang-absorbed), run #33."},
    {"item": f"NINJASTAKING EXITER - {f(NINJA['amount_egld'])} EGLD matures ~{NINJA_MATURES[:10]}", "weeks_on_list": 2,
     "reason": f"Same wallet re-delegated {f(NINJA_REDELEG)} of a {f(NINJA_WD)} withdraw on Oct 18 and is repaying Hatom USDC. PRE-COMMITTED (ninjastaking-exit-destination)."},
    {"item": "ERD1HHVFRW - BINANCE FUNDER USING FRESH HOPS", "weeks_on_list": 1,
     "reason": f"Sent {f(HHV_DEP)} to Binance.com via a nonce-1 wallet on Oct 19; balance now 35,150. Watch for more one-shot hops."},
    {"item": "WHALE B / COINBASE", "weeks_on_list": 3,
     "reason": f"Withdrew {f(WB_IN)} from Coinbase (balance {f(WB['balance_egld'])}); Mega Whale idle. mega-whale-coinbase-leg closed inconclusive."},
    {"item": "CROSS-VENUE WALLETS", "weeks_on_list": 3,
     "reason": f"erd1d2anjjha... (Binance/Bybit -> Gate.io, {f(ARB_D2_OUT)} this window) and erd13sytuz92... (Gate.io -> Bybit, {f(ARB_13_IN)}). Net them out of venue flows."},
    {"item": "DRIP SELLER INTO BINANCE", "weeks_on_list": 2,
     "reason": f"erd1vadknqe8... -> erd137cw9q46... -> Binance.com; {f(TR['binance_funders']['erd137cw9q']['to_binance_egld'])} this window."},
    {"item": "OTC PIPELINE", "weeks_on_list": 32,
     "reason": f"Silent: gross {f(otc['gross_out'])}, desks {f(otc['desk_bal'])}. Keep until Upbit's decision."},
    {"item": "EXPLOIT WALLET AND POISONING RING", "weeks_on_list": 7,
     "reason": f"Incident addresses hold {HR['invalid_total_egld']:.2f} EGLD; poisoning operator {PR['operator_out_7d']} dust txs in the window, zero hits above dust."},
]

# ---------------------------------------------------------------------------
prior = {t["id"]: t for t in r26["pre_committed_tests"]}
tests = [t for t in r26["pre_committed_tests"] if t["status"] == "resolved"]


def resolve(tid, outcome, measured, resolution):
    t = dict(prior[tid]); t.update({"status": "resolved", "outcome": outcome, "resolved_in_run": 32, "measured_value": measured, "resolution": resolution}); return t


tests.append(resolve("reopening-supply-overhang", "as_predicted" if OVERHANG == "persists" else ("contradicted" if OVERHANG == "cleared" else "inconclusive"),
    f"7-day rails Oct 12 15:05 -> Oct 19 ({R7_DAYS:.1f} days): net {R7_NET:+,.0f} EGLD raw, {R7_NET_EX_ARB:+,.0f} ex cross-venue wallets; EGLD {P7_EGLD:+.2f}% vs BTC {P7_BTC:+.2f}% ({P7_REL:+.1f}pp). Balance basis ex cross-venue about {BAL7_EX_ARB:+,.0f}.",
    f"Branch '{OVERHANG}': both conditions met on the rail measure the test was written for. Caveat stated up front: on the balance basis the inflow is about {BAL7_EX_ARB:+,.0f}, under the 25,000 line, so the margin is thin; and in the last {LIVE_DAYS:.1f} days of the week the price impact faded (EGLD {EGLD_VS_BTC:+.1f}pp vs BTC) although the inflow pace did not. The halt-weeks overhang reached exchanges during the first week after reopening; whether it is finished is a separate test (overhang-absorbed)."))
tests.append(resolve("mega-whale-coinbase-leg", "inconclusive",
    f"by run #32: Whale B {f(WB['balance_egld'])} ({WB_IN:+,.0f}, a Coinbase withdrawal, not a deposit); Mega Whale {f(CBL['mega']['balance_egld'])} (unchanged); routing wallet idle",
    "Neither branch: Whale B did not fall further and the Mega Whale received nothing. Whale B instead pulled 8,628 back from Coinbase. The run #30 leg stays a single observation; no bilateral pattern and no independent buying."))
for tid, note in [("delivery-price-relevance-2", f"run #32: desk gross {f(otc['gross_out'])} EGLD; no delivery. Not evaluable."),
                  ("korea-premium-arbitrage", f"run #32: premium {PREM:.1f}%; UPbit {UPD['distinct_depositors']} distinct depositors since restart, 0 in the window. Not evaluable; Upbit decides Oct 19-23."),
                  ("binance-undelegation-destination", f"run #32: still pending, {f(BIN_UNDEL)} EGLD with {BIN_UNDEL_DAYS:.1f} days left (matures ~{BIN_MATURES[:16]}). The 'not withdrawn by run #32' clause is not triggered: the unbond cannot be withdrawn before maturity, which falls after this run. Evaluate at run #33; no threshold changed."),
                  ("ninjastaking-exit-destination", f"run #32: {f(NINJA['amount_egld'])} still unbonding (~{NINJA_MATURES[:16]}). Side evidence, not the test: the wallet withdrew {f(NINJA_WD)} from two other providers and re-delegated {f(NINJA_REDELEG)} to pi-staking within eight minutes, and repaid a Hatom USDC borrow.")]:
    t = dict(prior[tid]); t.update({"status": "open", "measured_value": note, "resolution": None}); tests.append(t)


def new(tid, claim, threshold, branches, measured):
    return {"id": tid, "registered_in_run": 32, "claim": claim, "threshold": threshold, "branches": branches,
            "status": "open", "outcome": None, "resolved_in_run": None, "measured_value": measured, "resolution": None}


tests += [
    new("overhang-absorbed", "The halt-weeks supply overhang has been absorbed: the post-reopening inflow to exchanges is ending and EGLD stops underperforming BTC.",
        "Over the next 7-day rail window (run #33, start after this run's rail pass): tracked exchanges net < +10,000 EGLD ex cross-venue wallets AND EGLD - BTC >= -1pp = absorbed; net > +25,000 AND EGLD - BTC < -3pp = still being distributed; otherwise no conclusion",
        [{"condition": "net < +10K ex cross-venue and EGLD-BTC >= -1pp", "reading": "absorbed"},
         {"condition": "net > +25K and EGLD-BTC < -3pp", "reading": "still distributing"},
         {"condition": "otherwise", "reading": "no conclusion"}],
        f"run #32 last {LIVE_DAYS:.1f} days: exchanges {ex['net']:+,.0f} EGLD (cross-venue wallets kept nothing), EGLD - BTC {EGLD_VS_BTC:+.1f}pp."),
]
resolved = [t for t in tests if t.get("resolved_in_run") == 32]
as_pred = sum(1 for t in resolved if t["outcome"] == "as_predicted")
R["pre_committed_tests"] = tests

# ---------------------------------------------------------------------------
R["meta_learning"] = {
    "run_number": 32,
    "endpoints_that_worked": status["ok"],
    "endpoints_that_failed": [f"NONE with data missing. {D.get('_n_429', 0)} HTTP 429s in the main pass; 2 provider-scan pages rate-limited and recovered by the follow-up; 0 errors in rails and traces."],
    "api_quirks": [
        "/transfers?token=USDC-c76f1f&receiver=<xBridge Tokens Wrapper> returns each bridge-out as a transfer whose action.arguments.functionArgs[0] is the hex of the destination-chain token (BSCUSDC-887875, ETHUSDC-220753). Decoding it gives bridge outflow by chain without reading the Safe contracts; the Safe itself shows 0 USDC transfers because the wrapper converts first.",
        "The collector's [reopen] console line is a dict keyed by label, so several wallets sharing a label (three 'Binance.com' entries) collapse to the last one and printed 0/0 for Binance.com while the stored record held 194 sends / 252 receives. Read the stored exchange_reopen, never the console summary."],
    "data_gaps": [
        "The rail window starts at run #31's commit (09:47 UTC Oct 15), so up to 39 minutes after its collector end are not on the rails; the run #31 rail pass time was not stored.",
        "The 7-day delegator reward window overlaps run #31's by about three days.",
        "Kraken has no tracked address.",
        "Hatom UTK Money Market and OneDex Launchpad still fail bech32 validation."],
    "key_findings": [
        f"reopening-supply-overhang resolved as predicted: full-week rails {R7_NET_EX_ARB:+,.0f} EGLD ex cross-venue, EGLD {P7_REL:+.1f}pp vs BTC.",
        f"Last {LIVE_DAYS:.1f} days: EGLD {pc:+.2f}% vs BTC {M['btc_wow']:+.2f}%, first non-negative relative window since run #27; inflow continued at ~{PACE_NOW:,.0f}/day ex cross-venue.",
        f"Largest deposit {f(HHV_DEP)} EGLD from a labelled Binance funder via a fresh nonce-1 hop.",
        f"Binance's {f(BIN_UNDEL)} unbond still pending (~{BIN_MATURES[:16]}); ninjastaking exiter re-delegated {f(NINJA_REDELEG)} and is repaying Hatom USDC.",
        f"USDC {USDC_D:+,.0f}: bridge inflow beat outflow; unwraps went mostly to BSC with no EGLD sold first.",
        "mega-whale-coinbase-leg closed inconclusive; Whale B withdrew 8,628 from Coinbase."],
    "action_items_from_previous": len(r26["meta_learning"]["recommendations_for_next_run"]),
    "action_items_completed_detail": [
        f"FULL 7-DAY WINDOW - done on the rails: a 7-day pass from Oct 12 15:05:30 with per-counterparty totals; reopening-supply-overhang resolved ({OVERHANG}).",
        "RAIL DE-DUPLICATION - done: rail window starts at run #31's commit time; the 7-day pass starts after run #30's rail pass. The 7-day start time is stored in the snapshot.",
        f"USDC TRACE - done: USDC through the xBridge Tokens Wrapper by wallet and destination chain (in {f(UB_['wrap_usdc'])}, out {f(UB_['unwrap_usdc'])}); top unwrappers checked for EGLD swaps and CEX inflows (none). Run #31's 79,801 burn itself predates this window and was not re-traced.",
        "UPBIT DECISION - checked: review window Oct 19-23 has just opened, no outcome; korea-premium-arbitrage and delivery-price-relevance-2 stay open.",
        f"BINANCE UNBOND - not evaluable: run #32 lands {BIN_UNDEL_DAYS:.1f} days before maturity; /delegation confirms it pending, wallet idle. Moved to run #33.",
        f"NINJASTAKING UNBOND - not yet matured (~{NINJA_MATURES[:10]}); traced the wallet's other legs instead (withdraw {f(NINJA_WD)}, re-delegate {f(NINJA_REDELEG)}, Hatom USDC repayment)."],
    "methodology_changes": [
        "SEVEN-DAY RAIL PASS ALONGSIDE THE WINDOW: rails_run32.py records egld_7d / by_cp_7d per wallet from a fixed 7-day start, so a pre-committed weekly test can be resolved even when the schedule fires off-cadence.",
        "CROSS-VENUE NETTING ON RAILS: a cross-venue wallet's deposits minus withdrawals across tracked venues is removed from the net (it is pre-window inventory), entity figures are re-attributed, and the total is quoted raw and ex cross-venue.",
        "BRIDGE FLOW BY CHAIN: USDC in/out of the xBridge Tokens Wrapper decoded from functionArgs[0]; supply changes are now attributed to bridge flows, not inferred."],
    "new_addresses_discovered_detail": [
        "erd1rgm4td296wxwxnepwets5wnwsea7jy5u4lw4xt2sa535khgsjcdqfag6j4 - one-shot hop (nonce 1): received 12,223 EGLD from erd1hhvfrw... and deposited it at Binance.com two minutes later (Oct 19 03:34-03:36 UTC)",
        "erd1ltetacm786cz9atjjs9rgtlj56ce2n6k7ex0t9n6vfavg4krzl4qg7tl8j - largest USDC bridge-out of the window (21,442 USDC in two unwraps), no EGLD swaps, no CEX inflow in 7 days"],
    "action_items_completed": 4,
    "new_addresses_discovered": 2,
    "most_valuable_insight": (
        f"Measured over a full week, the post-reopening sell pressure is real: {R7_NET_EX_ARB:+,.0f} EGLD reached tracked exchanges ex cross-venue wallets while EGLD lost {abs(P7_REL):.1f}pp to BTC. But its price impact faded: in the last {LIVE_DAYS:.1f} days EGLD held level with BTC for the first time since the restart while exchange inflow continued at the same pace (~{PACE_NOW:,.0f}/day ex cross-venue) and Hatom borrowers repaid more than they borrowed. Supply is still arriving, but it is now being absorbed; next week's overhang-absorbed test checks whether the inflow itself stops."),
    "top_recommendation": f"RUN #33 FIRST: trace Binance's {f(BIN_UNDEL)} EGLD withdraw (matures {BIN_MATURES[:16]}) and the ninjastaking exiter's {f(NINJA['amount_egld'])} (~{NINJA_MATURES[:10]}) one hop, and resolve overhang-absorbed on a 7-day rail window.",
    "recommendations_for_next_run": [
        f"BINANCE UNBOND: after {BIN_MATURES[:16]}, trace the withdraw from erd1r3w62vq... one hop and resolve binance-undelegation-destination.",
        f"NINJASTAKING: after ~{NINJA_MATURES[:10]}, trace erd1me5hmqt5qg...'s {f(NINJA['amount_egld'])} withdraw and resolve ninjastaking-exit-destination (Hatom repayment counts as neither branch; note it).",
        "Resolve overhang-absorbed on a 7-day rail window starting after this run's rail pass (store the rail pass end time in _period this time).",
        "UPBIT: web-check the Oct 19-23 decision; if delisted, retire korea-premium-arbitrage and delivery-price-relevance-2; if kept and deposits reopen, run the >= 20-depositor premium test.",
        "Watch erd1hhvfrw... for further one-shot hops into Binance.com; label any new hop as it appears.",
        "Store rails_run33.py's own end timestamp in _period.rail_window_end_ts so the next window start is exact, not the commit time."],
    "dashboard_feature_suggestions": [
        {"title": "Seven-day rail netting with cross-venue removal",
         "motivation": f"This run resolved reopening-supply-overhang on a 7-day rail window ({R7_NET:+,.0f} raw, {R7_NET_EX_ARB:+,.0f} ex cross-venue) that is separate from the {LIVE_DAYS:.1f}-day point-in-time window. The dashboard shows only the window's balance-based net, so the number the test actually resolved on, and how much of it cross-venue wallets explained, cannot be seen.",
         "suggested_visualization": "waterfall per venue: 7d deposits, 7d withdrawals, cross-venue adjustment, net; with a toggle between window and 7d bases",
         "data_already_available": True, "data_source": "whale_intelligence.exchange_flows.rail_status.rail_7d (new field this run)", "priority": "high"},
        {"title": "Cross-venue wallet flow graph",
         "motivation": f"erd1d2anjjha... has moved about 56,000 EGLD from Binance.com/Bybit to Gate.io across three windows and erd13sytuz92... cycles Gate.io -> Bybit; this run they shifted {f(ARB_D2_IN + ARB_13_IN)} EGLD between venues and changed three entity nets by 4-14K each. In text it reads as noise; as a graph it shows one client's routing.",
         "suggested_visualization": "sankey of venue -> cross-venue wallet -> venue per window, with a run scrubber",
         "data_already_available": False, "data_source": "run32_traces.arb_wallets in data/collected (not yet in the report JSON; would need a whale_intelligence.cross_venue_wallets field)", "priority": "medium"}],
    "dashboard_suggestions_followup": [
        {"title": "Post-reopening price vs exchange net flow", "status": "pending",
         "note": "Not built. More useful now that the overhang test resolved; the 7-day waterfall above would supply its per-run ex cross-venue figure."},
        {"title": "Unbonding maturity calendar", "status": "pending",
         "note": "Not built. Both queued exits (Binance ~Oct 21, ninjastaking ~Oct 23) mature before run #33, so it would show its first resolved destinations next run."}],
    "withdrawn_claims": [],
}

rep = {k: R[k] for k in ["metadata", "executive_summary", "network_health", "whale_intelligence", "staking_intelligence", "token_activity",
                         "defi_activity", "anomalies", "trend_indicators", "watch_list", "meta_learning", "pre_committed_tests"]}
json.dump(rep, open(f"{REPO}/reports/{RD}.json", "w"), indent=1, default=str)
print("report written", len(json.dumps(rep, default=str)), "bytes")
print(f"tests resolved this run {len(resolved)}, as_predicted {as_pred}, open {sum(1 for t in tests if t['status']=='open')}")
print("PREM", round(PREM, 1), "UP_SHARE", round(UP_SHARE, 1), "OPEN", OPEN, "DEPONLY", DEPONLY)
