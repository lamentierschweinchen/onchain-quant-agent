#!/usr/bin/env python3
"""Run #34 stage 2: assemble reports/2026-10-26.json from derived.json + snapshot.

~4.4-day window (Oct 22 07:28 -> Oct 26 16:03) plus the fixed overhang-absorbed rail window (Oct 19 14:40 -> Oct 26 14:40)
and a trailing 7-day rail pass.
"""
import json
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD = "2026-10-26"
O = json.load(open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/1c89fe3e-3241-42ca-b5b7-8b835c9990a6/scratchpad/run34w/derived.json"))
D = json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev = json.load(open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/1c89fe3e-3241-42ca-b5b7-8b835c9990a6/scratchpad/run34w/previous_run33.json"))
status = json.load(open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/1c89fe3e-3241-42ca-b5b7-8b835c9990a6/scratchpad/run34w/status.json"))
beh = json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
r26 = json.load(open(f"{REPO}/reports/2026-10-22.json"))   # previous report (name kept for the reused blocks)
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
    if lbl == "MEXC":   # run #34: KuCoin reopened withdrawals Oct 23; only MEXC still shows the Sep 24 replay
        v = {**v, "first_in": None, "first_out": None}
    # run #29: sub-1-EGLD receives are address-poisoning/test dust, not deposits; UPbit's only send is to its own OTC desk
    dep_ok = v["in_egld"] >= 10; wd_ok = v["out_txs"] > 0 and lbl != "UPbit"   # run #33: Bitget took 22 receives totalling ~1 EGLD (dust); floor raised from 1 to 10
    v["state"] = ("open" if dep_ok and wd_ok else "deposit_only" if dep_ok else "withdrawal_only" if wd_ok else "closed")
    VEN[lbl] = v
_NONVENUE_INTERNAL = {"Binance Staking", "Binance: de-staking withdrawal wallet"}
_NONVENUE = {"Coinbase (secondary)", "Coinbase Routing Wallet", "Coinbase Custody", "Coinbase Custody 2 (migration destination)", "Binance Staking", "Binance: de-staking withdrawal wallet"}
OPEN = [k for k, v in VEN.items() if v["state"] == "open" and k not in _NONVENUE]   # run #30: venues, not each entity wallet
DEPONLY = [k for k, v in VEN.items() if v["state"] == "deposit_only" and k not in _NONVENUE]
CLOSED_MAJOR = [k for k in ("UPbit", "Bybit", "Coinbase", "MEXC", "KuCoin", "Bitfinex") if VEN.get(k, {}).get("state") == "closed"]
# run #33: Binance de-staking -> Binance Staking custody (320,000) is an internal move; keep it out of rail totals
RAIL_EGLD_IN = sum(v["in_egld"] for k, v in VEN.items() if k not in _NONVENUE_INTERNAL); RAIL_EGLD_OUT = sum(v["out_egld"] for k, v in VEN.items() if k not in _NONVENUE_INTERNAL)

# ---- run #34 traces ----
TR = D["run34_traces"]
BINV = VEN["Binance.com"]
BD = TR["binance_daily"]["days"]
BIN_DEP = BINV["in_egld"]; BIN_WD_EXT = BINV["out_egld"]
BIN_EXT_NET = BIN_DEP - BIN_WD_EXT
def ent_net(n): return next((e2["net_flow_egld"] for e2 in ex["entity"] if e2["entity"] == n), 0.0)
# run #34: Binance's de-staking wallet sent 320,000 to Binance Staking custody at 09:18 UTC Oct 22, after run #33's
# 07:28 balance read, so it lands in THIS window's balance basis. It is internal (staking contract -> Binance custody).
INTERNAL_BIN = 320000.0
EX_NET_RAW = ex["net"]; EX_NET = EX_NET_RAW - INTERNAL_BIN
BIN_ENT_EX_INTERNAL = ent_net("Binance") - INTERNAL_BIN
CUST = TR["binance_custody"]; CUST_NOW = CUST["balance_egld"]
BIN_UNDEL = 320002.0
POOL = D.get("unbonding_pool") or []
NU = TR["ninjastaking_unbond"]
NINJA_WALLET = NU["wallet"]; NINJA_AMT = 26698.742540426985
NINJA_ACTIVE = sum(int(d_.get("userActiveStake") or 0) for d_ in NU["delegation"]) / 1e18
NINJA_REDELEG = 15000.0          # delegate to ninjastaking (erd1...q48llllszfjtl6) 2026-10-24 05:23 UTC, verified one-off query
NINJA_REDELEG_PCT = 100 * NINJA_REDELEG / NINJA_AMT
NINJA_DEX = 14484.0              # 18 composeTasks/xo swaps Oct 23 19:55 -> Oct 26 08:23 (sum of EGLD-valued legs): the ~11,700 not re-delegated plus EGLD borrowed on Hatom
NINJA_WD_TS = "2026-10-23 19:54 UTC"
EXS = TR["exit_route_scan"]; EXR = EXS["by_route"]
EXIT_TRACED = sum(r["withdrawn_egld"] for r in EXS["rows"] if r["route"] != "internal")
EXIT_CEX = sum(r["withdrawn_egld"] for r in EXS["rows"] if r["route"] == "cex")
TERM = TR["desk_terminal"]; TERM_BAL = int(TERM["info"]["balance"]) / 1e18
HMM = TR["hatom_egld_mm"]
ARB = TR["arb_wallets"]; CBL = TR["coinbase_legs"]; UPD = TR["upbit_depositors"]
ARB_SET = {v["address"] for v in ARB.values()}
ARB_RETAINED = sum(v["in_egld"] - v["out_egld"] for v in ARB.values())
EX_NET_EX_ARB = EX_NET - ARB_RETAINED
PACE_NOW = EX_NET_EX_ARB / LIVE_DAYS; PACE_PREV = 16237 / 2.71   # run #33: +16,237 over 2.71 days
# ---- fixed overhang-absorbed window: Oct 19 14:40:28 -> Oct 26 14:40:28 (rails, value-bearing) ----
OV_S = D["_period"]["rail_ov_start_ts"]; OV_E = D["_period"]["rail_ov_end_ts"]
_RV = [r for r in RAILS.values() if r["label"] not in _NONVENUE_INTERNAL]
OV_IN = sum(r["in"]["egld_ov"] for r in _RV); OV_OUT = sum(r["out"]["egld_ov"] for r in _RV)
OV_ARB_IN = sum(v for r in _RV for c, v in r["in"]["by_cp_ov"].items() if c in ARB_SET)
OV_ARB_OUT = sum(v for r in _RV for c, v in r["out"]["by_cp_ov"].items() if c in ARB_SET)
OV_NET = OV_IN - OV_OUT; OV_NET_EX_ARB = OV_NET - OV_ARB_IN + OV_ARB_OUT
OV_BY = {}
for r in _RV:
    OV_BY[r["label"]] = OV_BY.get(r["label"], 0.0) + r["in"]["egld_ov"] - r["out"]["egld_ov"]
def _px(ch, t): return min(ch["prices"], key=lambda p: abs(p[0] / 1000 - t))[1]
OV_EGLD = 100 * (_px(D["cg_egld_hourly_8d"], OV_E) - _px(D["cg_egld_hourly_8d"], OV_S)) / _px(D["cg_egld_hourly_8d"], OV_S)
OV_BTC = 100 * (_px(D["cg_btc_hourly_8d"], OV_E) - _px(D["cg_btc_hourly_8d"], OV_S)) / _px(D["cg_btc_hourly_8d"], OV_S)
OV_REL = OV_EGLD - OV_BTC
OV_OUTCOME = ("absorbed" if (OV_NET_EX_ARB < 10000 and OV_REL >= -1) else "still distributing" if (OV_NET_EX_ARB > 25000 and OV_REL < -3) else "no conclusion")
# ---- trailing 7-day rails (ends at this run's rail pass) ----
R7_START = D["_period"]["rail_7d_start_ts"]
R7_DAYS = (D["_period"]["rail_window_end_ts"] - R7_START) / 86400
R7_IN = sum(r["in"]["egld_7d"] for r in _RV); R7_OUT = sum(r["out"]["egld_7d"] for r in _RV)
R7_ARB_IN = sum(v for r in _RV for c, v in r["in"]["by_cp_7d"].items() if c in ARB_SET)
R7_ARB_OUT = sum(v for r in _RV for c, v in r["out"]["by_cp_7d"].items() if c in ARB_SET)
R7_NET = R7_IN - R7_OUT; R7_NET_EX_ARB = R7_NET - R7_ARB_IN + R7_ARB_OUT
R7_BY = {}
for r in _RV:
    R7_BY[r["label"]] = R7_BY.get(r["label"], 0.0) + r["in"]["egld_7d"] - r["out"]["egld_7d"]
P7_EGLD, P7_BTC, P7_REL = OV_EGLD, OV_BTC, OV_REL   # the trailing 7d starts 3 min after the fixed window; same price base
BAL7_EX_ARB = r26["whale_intelligence"]["exchange_flows"]["net_change_egld"] + EX_NET_EX_ARB   # run #33 window (+16,237) + this window, balance basis ex internal
# ---- seller chain (run #33 rec #5) ----
SC = TR["seller_chain"]; SCW = SC["wallets"]
SC_TOTAL = SC["total_to_binance_egld"]
SC_HOPS = sum(v["to_binance_egld"] for k, v in SCW.items() if k in ("erd1rgm4td29", "erd1rcty49"))
HL5_WIN_VXA = 33129.054474   # erd1hl5y4a -> erd1vxa2vk on 2026-10-26 12:15 UTC (large_transactions)
SC_WINDOW = sum(v["to_binance_in_window_egld"] for v in SCW.values())
SC_DRIP = next((h["to_binance_egld"] for h in SC["other_hops_from_hhvfrw"] if h["address"].startswith("erd137cw9q")), 0.0)
HL5_TO_VXA = SCW["erd1hl5y4a"]["other_destinations"].get("erd1vxa2vkdd945k0d6v8dscm8pwt56ueujdtzsyghh6zu4c4lf0kyjqaqkhd2", 0.0)
HL5_BAL = SCW["erd1hl5y4a"]["balance_egld"]
DRIP_WIN = TR["binance_funders"]["erd137cw9q"]["to_binance_egld"]
# ---- Binance withdrawals ----
BIG_WD = cust["hot_big_outbound"][0] if cust["hot_big_outbound"] else {"amount": 0.0, "receiver": "", "receiver_balance": 0.0}
WB = CBL["whale_b"]
UB_ = TR["usdc_bridge"]; USDC_NET_IN = UB_["wrap_usdc"] - UB_["unwrap_usdc"]
USDC_D = usdc["supply"] - usdc["prev"]
MEGA_IN = bid["mega_delta"]
UPBIT_DEP = VEN.get("UPbit", {}).get("in_egld", 0); UPBIT_DEP_N = VEN.get("UPbit", {}).get("in_senders", 0)
PREV_BOOK = prev["exchange_orderbook_latest"]
PREM_PREV = PREV_BOOK.get("korea_premium_pct", 12.2)
UPSH_PREV = PREV_BOOK.get("upbit_share_of_volume_pct", 47.0)
BIN_BID_PREV = PREV_BOOK["binance"]["depth_minus2_usd"]
BITHUMB = next((t for t in BOOK["top"] if t["market"] == "Bithumb"), {"volume_24h_usd": 0.0})
KUC = VEN.get("KuCoin", {})
STAKED_EX_BIN = M["staked_chg"] + BIN_UNDEL
WIN_TXT = f"{LIVE_DAYS:.1f}-day window (Oct 22 07:28 -> Oct 26 {hm(D['liveness']['0']['timestamp'])[-5:]} UTC)"
WINDOW_NOTE = (f"{WIN_TXT}. The pre-committed overhang-absorbed test uses its own fixed rail window, {iso(OV_S)} -> {iso(OV_E)}, and the trailing 7-day rail pass ends at {iso(D['_period']['rail_window_end_ts'])}. "
               f"Point-in-time flows below are {LIVE_DAYS:.1f}-day flows unless marked 7d.")
UPBIT_NOTE = "Upbit published on 2026-10-23 that it is extending EGLD's trading-caution designation for further review, to the third week of November (Nov 16-20); Bithumb's decision was not found."
wd_top0 = (WD.get("by_provider_top") or [[0, 0]])[0][1]
R = {}
R["metadata"] = {
    "report_date": RD, "period_start": "2026-10-22", "period_end": RD,
    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "egld_price_usd": price, "btc_price_usd": M["btc"], "eth_price_usd": M["eth"],
    "run_number": 34,
    "data_sources_ok": status["ok"] + [
        f"follow-up pass: {WD.get('calls', 0)} withdraw calls decoded, poisoning lookalikes re-scanned (0 errors)",
        "rail check (rails_run34.py): value-bearing EGLD per tracked exchange wallet from run #33's stored rail end (2026-10-22 13:48:49 UTC), the fixed overhang-absorbed window (Oct 19 14:40:28 -> Oct 26 14:40:28) with per-counterparty totals, and a trailing 7-day pass; page cap raised to 8,000 txs per side",
        "targeted traces (trace_run34.py): ninjastaking exiter withdraw and every leg after it, Binance Staking custody since the 320,000 receipt, the erd1hl5y4a -> erd1079hvt0 -> erd1hhvfrw seller chain since Oct 9, Binance.com daily rails, cross-venue wallets, Coinbase / Whale B / Mega Whale legs, UPbit depositors, USDC through the xBridge wrapper, Hatom EGLD market calls",
        "web check (Oct 26): Upbit extended EGLD's trading-caution review to Nov 16-20 (notice dated Oct 23)"],
    "data_sources_failed": status["failed"],
    "data_sources_recovered": [
        "LIVENESS GATE PASSED: every shard within a second of real time at collection",
        f"{D.get('_n_429', 0)} HTTP 429 responses in the main pass; 0 paged errors, 0 API errors; every pass ran under caffeinate with python -u and the whole chain finished in about 25 minutes",
        "Balances are read at 16:03 UTC Oct 26; Binance's 320,000 custody receipt (Oct 22 09:18) fell after run #33's read, so it is inside this window's balance basis and is reported separately as internal.",
        WINDOW_NOTE,
        f"delegator reward behaviour sampled {ag['providers_sampled']} of {ag.get('providers_requested', 8)} providers"]}

R["executive_summary"] = [
    {"category": "network", "severity": "high", "finding":
     f"EGLD FELL {abs(pc):.1f}% WHILE EXCHANGES LOST EGLD. ${M['prev_price']:.2f} -> ${price:.2f} over {LIVE_DAYS:.1f} days against BTC {M['btc_wow']:+.1f}% and ETH {M['eth_wow']:+.1f}% ({EGLD_VS_BTC:+.1f}pp vs BTC), the worst relative window since Oct 9. "
     f"Yet tracked exchange wallets lost {abs(EX_NET):,.0f} EGLD net of Binance's internal custody move (KuCoin {ent_net('KuCoin'):+,.0f}, Bybit {ent_net('Bybit'):+,.0f}, Binance.com {BIN_ENT_EX_INTERNAL:+,.0f}). The selling did not need fresh on-chain deposits: it came from EGLD already on the books."},
    {"category": "token", "severity": "high", "finding":
     f"UPBIT EXTENDED ITS CAUTION REVIEW AND THE KOREA PREMIUM WIDENED TO {PREM:.1f}%. Upbit's Oct 23 notice pushed the decision to Nov 16-20. Upbit traded ${up['converted_volume']['usd']/1e6:.1f}M of EGLD in 24h, {UP_SHARE:.0f}% of all venues (from {UPSH_PREV:.0f}%), at ${up['converted_last']['usd']:.2f} against ${bn['converted_last']['usd']:.2f} on Binance (premium from {PREM_PREV:.1f}%). "
     f"UPbit's wallet moved no EGLD, so this is a closed venue trading a stock that cannot leave: Korean EGLD is now priced as its own market."},
    {"category": "whale", "severity": "medium", "finding":
     f"OVERHANG-ABSORBED RESOLVES 'NO CONCLUSION'. On its fixed rail window (Oct 19 14:40 -> Oct 26 14:40) tracked exchanges netted {OV_NET_EX_ARB:+,.0f} EGLD ex cross-venue wallets, which passes the < +10,000 'absorbed' bar, but EGLD did {OV_REL:+.1f}pp against BTC, which fails its >= -1pp bar. "
     f"Neither branch holds. The flow side looks finished (net outflow, KuCoin reopened withdrawals Oct 23); the price side did not follow."},
    {"category": "staking", "severity": "medium", "finding":
     f"STAKED EGLD STEPPED DOWN {abs(M['staked_chg']):,.0f}, AS FORECAST. The ratio fell {100*(M['sr']-M['sr_prev']):+.2f}pp to {100*M['sr']:.2f}%. {f(BIN_UNDEL)} of it is Binance's unbond leaving the staking contract for its custody wallet on Oct 22 (custody unchanged at {f(CUST_NOW)}, no outbound since); the remaining {STAKED_EX_BIN:+,.0f} is ordinary exits. "
     f"binance-custody-hold reads 'held' so far (0 to the hot wallet, 0 re-delegated)."},
    {"category": "staking", "severity": "medium", "finding":
     f"THE NINJASTAKING EXITER ROTATED, IT DID NOT SELL. erd1me5hmqt5qg... withdrew {f(NINJA_AMT)} EGLD at {"Oct 23 19:54 UTC"} and delegated {f(NINJA_REDELEG)} ({NINJA_REDELEG_PCT:.0f}%) straight back into ninjastaking nine hours later; the other ~11,700, plus EGLD borrowed on Hatom, went through {f(NINJA_DEX)} EGLD of xExchange/XOXNO swaps into USDC/USDT supplied as Hatom collateral. "
     f"ninjastaking-exit-destination resolves 'rotation' (> 50% re-delegated): the claim it was a sale is contradicted. The rest is a short-EGLD loop, not an exchange sale."},
    {"category": "whale", "severity": "low", "finding":
     f"THE BINANCE SELLER CHAIN WENT QUIET. Traced as one entity, erd1hl5y4a... -> erd1079hvt0... -> erd1hhvfrw... and its two one-shot hops routed {f(SC_HOPS)}-{f(SC_TOTAL)} EGLD to Binance.com since the Oct 9 reopening (the upper bound counts the shared drip wallet erd137cw9q... in full), but {f(SC_WINDOW)} directly in this window. "
     f"Instead erd1hl5y4a... sent {f(HL5_WIN_VXA)} to Unknown Whale erd1vxa2vk... on Oct 26 (now {f(TR['binance_funders']['erd1vxa2vk']['balance_egld'])}); the drip wallet still carried {f(DRIP_WIN)} to Binance."},
    {"category": "token", "severity": "low", "finding":
     f"USDC FELL {abs(USDC_D):,.0f} ({usdc['pct']:+.2f}%) ON BRIDGE EXITS. {UB_['unwrap_txs']} unwraps sent {f(UB_['unwrap_usdc'])} USDC out through the xBridge wrapper against {f(UB_['wrap_usdc'])} in. USDT {usdt['pct']:+.2f}%. "
     f"Unbonding ran ~{f(sk['undelegated_week']/LIVE_DAYS*7)}/week ({sk['undelegate_callers']} callers), up from ~20,000 in run #33; compounding {cvc['compound_pct_of_reward_decisions']:.2f}%."},
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
               "btc_correlation_note": f"BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%, EGLD {pc:+.2f}% over {LIVE_DAYS:.1f} days: EGLD {EGLD_VS_BTC:+.1f}pp vs BTC, ending a two-window run ahead of BTC. On the fixed 7-day window (Oct 19 14:40 -> Oct 26 14:40) EGLD {OV_EGLD:+.1f}% vs BTC {OV_BTC:+.1f}% ({OV_REL:+.1f}pp)."},
    "liveness": {"ok": D["liveness_ok"], "latest_block_by_shard": {k: iso(v["timestamp"]) for k, v in D["liveness"].items()},
                 "restart_1_utc": iso(1790181300), "restart_1_stopped_utc": iso(1790182386), "restart_2_utc": iso(1790263800),
                 "live_days_in_window": LIVE_DAYS, "rollback_point_utc": "2026-09-19 06:37:45 UTC"},
    "analysis": (
        f"WINDOW. {WINDOW_NOTE} Every shard read within a second of real time. Epoch {st['epoch']} ({st['epoch']-pact['epoch']:+d}), "
        f"{f(st['transactions']-pact['total_transactions'])} transactions (~{f(int((st['transactions']-pact['total_transactions'])/LIVE_DAYS))}/day), {f(st['accounts']-pact['total_accounts'])} new accounts. Total supply {f(econ['totalSupply'])} ({econ['totalSupply']-pecon['total_supply']:+,}).\n\n"
        f"STAKING. Staked EGLD {M['staked_chg']:+,.0f} to {f(econ['staked'])}; ratio {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp). The step run #33 forecast arrived: Binance withdrew its {f(BIN_UNDEL)} EGLD unbond on Oct 22 09:15 (after that run's read) and parked it in custody, which /economics no longer counts as staked. "
        f"Ex-Binance the change is {STAKED_EX_BIN:+,.0f}: {O['withdraw_calls']} withdraw calls returned {f(WD.get('egld_returned_total', 0) - 322262.54)} EGLD outside Binance against new delegations (delegation TVL {sk['delta_locked']:+,.0f}). z = {zz('staked'):+.1f} on the staked series is that one known step, not a run. Network APR {100*econ['apr']:.2f}% (up as the denominator shrank).\n\n"
        f"PRICE. EGLD ${price:.2f}, {pc:+.2f}% against BTC {M['btc_wow']:+.2f}% and ETH {M['eth_wow']:+.2f}% ({EGLD_VS_BTC:+.1f}pp). Binance bids within 2% of mid ${f(BOOK['binance']['depth_minus2_usd'])} (from ${f(BIN_BID_PREV)}), all venues ${f(BOOK['all']['depth_minus2_usd'])}. "
        f"CEX spot volume over 7 days {f(BOOK['spot_volume_7d_egld']/1e6, 2)}M EGLD, flat on the prior week ({f(BOOK['spot_volume_prior_7d_egld']/1e6, 2)}M). Upbit traded {UP_SHARE:.0f}% of the last 24h's global volume at a {PREM:.1f}% premium: outside Korea EGLD is thinly traded and fell; inside Korea it trades heavily at ${up['converted_last']['usd']:.2f}. "
        f"Upbit published its caution extension on Oct 23, and the window's slide ran from there.")}


def tier(v):
    if v > 1_000_000: return "mega"
    if v >= 100_000: return "large"
    if v >= 10_000: return "mid"


def entity_interp(e):
    n = e["entity"]; v = VEN.get({"Binance": "Binance.com"}.get(n, n), {})
    st_ = v.get("state", "closed")
    if n == "Binance":
        return f"{e['net_flow_egld']:+,.0f} raw, of which +320,000 is Binance's own unbond moving from the staking contract into Binance Staking custody (Oct 22 09:18); customer flow at Binance.com {BIN_ENT_EX_INTERNAL:+,.0f} ({v.get('in_txs',0)} deposits / {v.get('out_txs',0)} withdrawals on the rails)."
    if e["net_flow_egld"] == 0:
        return f"0: no EGLD deposit or withdrawal this window across {e['wallets_count']} wallet(s); the rail is closed on chain."
    if n == "KuCoin":
        return f"{e['net_flow_egld']:+,.0f}: KuCoin's first customer withdrawals since the halt (from Oct 23 05:54 UTC; {v.get('out_txs',0)} withdrawals / {v.get('in_txs',0)} deposits). A backlog of EGLD held since the halt leaving the exchange."
    if st_ == "deposit_only":
        return f"{e['net_flow_egld']:+,.0f}: deposit-side only ({v['in_txs']} deposits from {v['in_senders']} senders, 0 withdrawals)."
    return f"{e['net_flow_egld']:+,.0f}: rail open both ways ({v.get('in_txs',0)} deposits / {v.get('out_txs',0)} withdrawals)."


INV_SERIES = {**prev["otc_desk_inventory_series"], "run34": round(otc["desk_bal"])}
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
        "net_change_egld": EX_NET, "net_change_pct": 100 * EX_NET / ex["total_prev"],
        "net_change_egld_raw": EX_NET_RAW, "internal_binance_staking_egld": INTERNAL_BIN,
        "direction": "inflow" if EX_NET >= 0 else "outflow",
        "rail_status": {"tracked_wallets": len(REOPEN), "egld_sends_since_restart": sum(v["out_txs"] for v in VEN.values()),
                        "egld_deposits_in_window": sum(v["in_txs"] for v in VEN.values()),
                        "egld_deposited_in_window": RAIL_EGLD_IN, "egld_withdrawn_in_window": RAIL_EGLD_OUT,
                        "venues_open": OPEN, "venues_deposit_only": DEPONLY, "venues_closed": [k for k, v in VEN.items() if v["state"] == "closed"],
                        "by_venue": venue_rows,
                        "note": f"Value-bearing EGLD transactions only (ESDT spam airdrops and exchange-internal sweeps excluded). Rail window from run #33's stored rail end (Oct 22 13:48:49 UTC) to {iso(D['_period']['rail_window_end_ts'])}. KuCoin sent its first customer withdrawals since the halt on Oct 23. UPbit, Bitfinex and Tokero moved no EGLD; MEXC one dust tx. {UPBIT_NOTE}",
                        "rail_7d": {"start_utc": iso(R7_START), "days": R7_DAYS, "deposits_egld": R7_IN, "withdrawals_egld": R7_OUT, "net_egld": R7_NET,
                                    "cross_venue_deposits_egld": R7_ARB_IN, "cross_venue_withdrawals_egld": R7_ARB_OUT, "net_ex_cross_venue_egld": R7_NET_EX_ARB,
                                    "by_venue_net_egld": {k: v for k, v in R7_BY.items() if v}, "egld_change_pct": P7_EGLD, "btc_change_pct": P7_BTC, "egld_minus_btc_pp": P7_REL,
                                    "balance_basis_net_ex_cross_venue_egld": BAL7_EX_ARB},
                        "rail_overhang_window": {"start_utc": iso(OV_S), "end_utc": iso(OV_E), "deposits_egld": OV_IN, "withdrawals_egld": OV_OUT, "net_egld": OV_NET,
                                                 "cross_venue_deposits_egld": OV_ARB_IN, "cross_venue_withdrawals_egld": OV_ARB_OUT, "net_ex_cross_venue_egld": OV_NET_EX_ARB,
                                                 "by_venue_net_egld": {k: v for k, v in OV_BY.items() if abs(v) >= 1}, "egld_change_pct": OV_EGLD, "btc_change_pct": OV_BTC,
                                                 "egld_minus_btc_pp": OV_REL, "outcome": OV_OUTCOME}},
        "signal": (f"NET OUTFLOW ON A FALLING PRICE. {len(OPEN)} tracked venues move EGLD both ways ({', '.join(OPEN)}). Balance change {EX_NET_RAW:+,.0f} EGLD raw over {LIVE_DAYS:.1f} days, {EX_NET:+,.0f} after Binance's internal 320,000 custody move: "
                   + ", ".join(f"{e2['entity']} {e2['net_flow_egld'] - (INTERNAL_BIN if e2['entity'] == 'Binance' else 0):+,.0f}" for e2 in ex["entity"] if e2["net_flow_egld"]) + ". "
                   f"First net outflow since the rails reopened (runs #28-#33 were all inflows). Cross-venue wallet erd1d2anjjha... moved {f(ARB['erd1d2anjjha']['in_egld'])} in / {f(ARB['erd1d2anjjha']['out_egld'])} out. "
                   f"FIXED 7-DAY WINDOW (overhang-absorbed): {OV_NET:+,.0f} raw, {OV_NET_EX_ARB:+,.0f} ex cross-venue, EGLD {OV_EGLD:+.1f}% vs BTC {OV_BTC:+.1f}% -> '{OV_OUTCOME}'. Exchange-flow and OTC series stay out of the weekly baselines (UPbit closed)."),
        "by_exchange": [{"exchange": w["exchange"], "change_egld": w["change_egld"], "pct": w["pct"]} for w in ex["per_wallet"]],
        "entity_netting": [{"entity": e2["entity"], "wallets_count": e2["wallets_count"],
                            "net_flow_egld": e2["net_flow_egld"], "interpretation": entity_interp(e2)} for e2 in ex["entity"]]},
    "dormant_activations": [],
    "exit_routes": {
        "route_this_run": f"no CEX exits among withdraws > 3,000 EGLD; ninjastaking exiter re-delegated {NINJA_REDELEG_PCT:.0f}% and swapped the rest into stablecoins on Hatom",
        "route_previous_run": "no delegator withdraw above 3,000 EGLD; Binance's 320,000 unbond went to Binance Staking custody (internal)",
        "scan_threshold_egld": 3000, "scan_calls": EXS["calls"], "scan_by_route": EXR,
        "scan_rows": [{"sender": r_["sender"], "sender_label": r_["sender_label"], "provider": r_["provider"], "withdrawn_egld": r_["withdrawn_egld"],
                       "route": r_["route"], "balance_now_egld": r_["balance_now"]} for r_ in EXS["rows"]],
        "traced_egld_ex_internal": EXIT_TRACED, "traced_to_cex_egld": EXIT_CEX,
        "binance_undelegation": {"wallet": "erd1r3w62vqmsux5e38p6vnueatmfcs8nr5lmg3s97x6rafqpgxfae0sxv9z0v", "egld": BIN_UNDEL,
                                 "called_utc": "2026-10-12 06:16 UTC", "unbonds_in_days": 0.0, "matures_utc": "2026-10-21 16:21 UTC",
                                 "status": f"RESOLVED run #33 (to custody). Custody erd1rf4hv70... {f(CUST_NOW)} EGLD at the trace; {len(CUST['out'])} outbound txs since Oct 22 09:06, {f(CUST['out_to_hot_egld'])} to the hot wallet, {f(CUST['delegated_egld'])} re-delegated."},
        "binance_hot_to_custody_egld": 0.0,
        "largest_new_undelegation": {"wallet": NINJA_WALLET, "provider": "ninjastaking", "egld": NINJA_AMT,
                                     "unbonds_in_days": 0.0, "wallet_balance_egld": NU["balance_egld"],
                                     "note": f"WITHDRAWN {NINJA_WD_TS}. {f(NINJA_REDELEG)} re-delegated to ninjastaking at 05:23 UTC Oct 24; the rest, plus EGLD borrowed on Hatom, swapped ({f(NINJA_DEX)} EGLD across 18 swaps) via xExchange compose / XOXNO into USDC/USDT supplied on Hatom. Active stake now {f(NINJA_ACTIVE)} (incl. 5,000 at pi-staking from Oct 18)."},
        "note": (f"Collector-side scan of every delegator withdraw call above 3,000 EGLD: {EXS['calls']} calls. Routes: " + ", ".join(f"{k} {v['n']} ({f(v['egld'])})" for k, v in EXR.items()) + ". "
                 f"{O['withdraw_calls']} withdraw calls (from {O['prev_withdraw_calls']}) returned {f(WD.get('egld_returned_total', 0))} EGLD, {f(wd_top0)} of it Binance's unbond. "
                 f"erd1qyt62v5ndd... withdrew from westake, Synexis and bober (24,702) and holds 25,698; erd155j9c36hp5 (the post-restart DEX+bridge exiter) withdrew 8,889 from Synexis and passed it to a new wallet in three sends.")},
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
        "method_note": f"Eighth read after restart; invalid balances {HR['invalid_total_egld']:.2f} EGLD, unchanged."},
    "otc_pipeline": {
        "gross_outbound_egld_7d": otc["gross_out"], "gross_inbound_egld_7d": otc["gross_in"],
        "circular_egld_7d": otc["circular"], "net_one_way_egld_7d": otc["net_one_way"],
        "circular_share_pct": otc["circ_pct"],
        "desk_balance_egld": otc["desk_bal"], "previous_desk_balance_egld": otc["prev_desk"],
        "upbit_reload_egld": otc["upbit_feed"],
        "venue_netting": [],
        "router_tail_delivery_egld": 0.0, "router_tail_routers": 0,
        "gross_series_egld_7d": {**r26o["gross_series_egld_7d"], "run34": otc["gross_out"]},
        "net_one_way_series_egld_7d": {**r26o["net_one_way_series_egld_7d"], "run34": otc["net_one_way"]},
        "desk_inventory_series_egld": INV_SERIES,
        "circularity_series_pct": {**r26o["circularity_series_pct"], "run34": 0.0},
        "peak_window_renetted": r26o["peak_window_renetted"],
        "backfilled_windows": r26o.get("backfilled_windows", []),
        "wave_window_netting": {**r26o["wave_window_netting"],
            "note": f"Wave #4 stays closed at 467,107 EGLD one-way (Sep 7 to the halt, frozen labels). The post-restart window (Sep 24 - Oct 26) nets {f(otc['wave']['net_one_way'])} EGLD one-way."},
        "feed_by_parent_venue": [],
        "feeder_backtrace": O["feeder_backtrace"],
        "address_poisoning": [{"address": a, "mimics": v["note"], "nonce": v["nonce"], "dust_txs_30d": v["dust_txs_30d"],
                               "distinct_targets_30d": v["distinct_targets_30d"],
                               "inbound_above_0_01_egld": len(v["inbound_above_0_01_egld"])} for a, v in PZ.items()],
        "desk_terminal_resolved": {"address": TERM["address"], "nonce": TERM["info"].get("nonce"), "balance_egld": TERM_BAL, "role": "holder (nonce 1, no value sent)"},
        "series_note": (f"QUIET, {LIVE_DAYS:.1f}-DAY WINDOW. Desk gross out {f(otc['gross_out'])} EGLD, all of it small payments; no UPbit reload (UPbit's wallet moved no EGLD). Desks {f(otc['desk_bal'])}. "
                        f"The Oct 6 terminal erd1y27r22... holds {f(TERM_BAL, 1)} EGLD.")},
    "demand_instruments": {
        "identifiable_bid_absorbed_egld_7d": 0.0, "mega_whale_otc_leg_egld": MEGA_IN,
        "mega_whale_balance_egld": bid["mega_bal"] or 0.0, "mega_whale_change_egld": bid["mega_delta"],
        "coinbase_routing_balance_egld": bid["cbr_bal"] or 0.0, "coinbase_routing_inflow_egld": 0.0,
        "coinbase_routing_funder": "erd1m9qn6gvercs6ksvtn924w4y7z9ppglyfugpu34al26t9u4mvzvqqlq9dc3", "coinbase_routing_funder_label": "Coinbase (secondary); idle toward the routing wallet. Whale B and the Mega Whale did not move",
        "weeks_at_zero": 14, "weeks_at_zero_in_last_four": 4, "bid_to_distribution_ratio_pct": 0.0,
        "dex_turnover_ratio_pct": bid["turnover"], "previous_dex_turnover_ratio_pct": bid["prev_turnover"],
        "dex_volume_egld_24h": bid["dexvol_egld"], "previous_dex_volume_egld_24h": bid["prev_dexvol_egld"],
        "pool_tvl_egld": bid["pooltvl_egld"], "previous_pool_tvl_egld": bid["prev_pooltvl_egld"],
        "wegld_usdc_volume_usd": bid["wegld_usdc_vol"], "wegld_usdc_share_of_volume_pct": bid["wegld_usdc_share"],
        "ex_wegld_usdc_volume_usd": bid["ex_wegld_usdc_vol"], "ex_wegld_usdc_volume_egld": bid["ex_wegld_usdc_vol_egld"],
        "dex_volume_status": "evaluable; compared with run #33",
        "absorber_scan": {"terminals_scanned": absb["scanned"],
                          "terminals_retaining_over_half": len(absb["retaining"]),
                          "total_received_from_desks_egld": absb["total_received"],
                          "total_retained_egld": absb["total_balance_held"],
                          "retained_share_pct": 0.0,
                          "verdict": f"Desk outbound {f(otc['gross_out'])} EGLD; the instrument stays retired. The Mega Whale did not move."},
        "withdrawal_breadth": {"distinct_recipients_raw": br["raw_n"], "total_egld_raw": br["raw_egld"],
                               "distinct_recipients_ex_pipeline": br["ex_n"], "total_egld_ex_pipeline": br["ex_egld"],
                               "pipeline_share_pct": br["pipeline_share"], "top_two_share_pct": br["top_two_share_pct"]},
        "withdrawal_breadth_top": br["top"],
        "exchange_orderbook": {
            "source": "CoinGecko exchange tickers with 2% depth and daily spot volume (third-party). PARTIAL RAILS: UPbit closed on chain (no EGLD flow; caution review extended to Nov 16-20); Binance.com, Coinbase, Bybit, Gate.io, Crypto.com, KuCoin open",
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
R["whale_intelligence"]["analysis"] = (
    f"RAILS. Value-bearing EGLD per tracked exchange wallet from run #33's rail end (Oct 22 13:48) to {hm(D['_period']['rail_window_end_ts'])}: "
    + "; ".join(f"{k}: {v['state'].replace('_', ' ')} ({v['in_txs']} in / {v['out_txs']} out)" for k, v in VEN.items() if v["state"] != "closed" and k not in _NONVENUE_INTERNAL)
    + f". No EGLD moved: {', '.join(k for k, v in VEN.items() if v['state'] == 'closed')}. Venue deposits {f(RAIL_EGLD_IN)}, withdrawals {f(RAIL_EGLD_OUT)} (net {RAIL_EGLD_IN-RAIL_EGLD_OUT:+,.0f}; the balance basis ex the internal Binance move is {EX_NET:+,.0f}).\n\n"
    f"KUCOIN REOPENED WITHDRAWALS. KuCoin's only sends since the restart had been the Sep 24 replays; from 05:54 UTC Oct 23 it paid out {KUC.get('out_txs',0)} withdrawals ({f(KUC.get('out_egld',0))} EGLD), led by 9,999 to erd1r35rd2zy... in three sends within ten minutes, against {f(KUC.get('in_egld',0))} of deposits. Customers took EGLD that had been stuck since the halt off the exchange.\n\n"
    f"OVERHANG-ABSORBED (fixed window {iso(OV_S)[5:16]} -> {iso(OV_E)[5:16]}). Deposits {f(OV_IN)}, withdrawals {f(OV_OUT)}, net {OV_NET:+,.0f}; cross-venue wallets {f(OV_ARB_IN)} in / {f(OV_ARB_OUT)} out, so {OV_NET_EX_ARB:+,.0f} ex cross-venue. By venue: " + ", ".join(f"{k} {v:+,.0f}" for k, v in sorted(OV_BY.items(), key=lambda kv: -abs(kv[1])) if abs(v) >= 500)
    + f". EGLD {OV_EGLD:+.1f}%, BTC {OV_BTC:+.1f}% ({OV_REL:+.1f}pp). Flow says absorbed, price says not: '{OV_OUTCOME}'.\n\n"
    f"BINANCE.COM. Per day since Oct 19 (deposits / withdrawals, EGLD): " + "; ".join(f"{d_[5:]}: {f(v_['dep_egld'])} / {f(v_['wd_egld'])}" for d_, v_ in BD.items() if d_ >= "2026-10-19")
    + f". In the rail window {f(BIN_DEP)} in and {f(BIN_WD_EXT)} out. The largest withdrawal, {f(BIG_WD['amount'])} EGLD at 08:15 UTC Oct 26 to erd1ygkh9r65... (a fresh wallet), is held there ({f(BIG_WD.get('receiver_balance') or 0)}). Oct 26 alone took {f(BD.get('2026-10-26',{}).get('wd_egld',0))} out.\n\n"
    f"THE SELLER CHAIN AS ONE ENTITY (run #33 rec #5). Since the Oct 9 reopening, erd1hl5y4a... (balance {f(HL5_BAL)}) funded erd1079hvt0... ({f(SCW['erd1079hvt0']['out_egld'])} passed on), which refilled erd1hhvfrw... ({f(SCW['erd1hhvfrw']['out_egld'])} sent on). The chain delivered {f(SC_HOPS)} EGLD to Binance.com through the two one-shot hops (12,223 and 25,000), plus up to {f(SC_DRIP)} through the drip wallet erd137cw9q..., which also takes EGLD from other sellers: {f(SC_HOPS)}-{f(SC_TOTAL)} in all. "
    f"In this window it sent {f(SC_WINDOW)} to Binance directly; erd1hl5y4a... moved {f(HL5_WIN_VXA)} to Unknown Whale erd1vxa2vk... instead on Oct 26 ({f(HL5_TO_VXA)} since Oct 9), and erd1079hvt0... received 5,795 from Bybit on Oct 23. The seller paused while the price fell.\n\n"
    f"CROSS-VENUE. erd1d2anjjha... took {f(ARB['erd1d2anjjha']['in_egld'])} and sent {f(ARB['erd1d2anjjha']['out_egld'])}; two further pass-through wallets (erd1470jqfmh..., ~7,000 Bybit -> Binance on Oct 24, and erd1wznqcfmq..., 3,987 Binance -> Bybit on Oct 26) moved EGLD between venues within minutes.\n\n"
    f"COINBASE, WHALE B, MEGA WHALE. Whale B ({f(WB['balance_egld'])}), the Mega Whale ({f(CBL['mega']['balance_egld'])}) and the routing wallet ({f(CBL['cb_routing']['balance_egld'],1)}) did not move. Coinbase entity {ent_net('Coinbase'):+,.0f}.\n\n"
    f"WHALES. Tiers on the common-address basis ({O['tiers_basis']} wallets): mega {O['tiers']['mega']['net_change_egld']:+,.0f} (all of it Binance's custody receipt), large {O['tiers']['large']['net_change_egld']:+,.0f} (KuCoin and Bybit outflows, an Unknown Whale +28,372, xExchange's WEGLD contract +26,719 as EGLD was wrapped), mid {O['tiers']['mid']['net_change_egld']:+,.0f}. "
    f"Unknown Whale I: {CEN['Unknown Whale I']['inbound_txs']} inbound. erd1a6lte0: {CEN['erd1a6lte0']['inbound_txs']} inbound.\n\n"
    f"DEMAND. Binance+Bybit bids within 2% of mid total ${f(bbn)}; Binance's own bid ${f(BOOK['binance']['depth_minus2_usd'])} from ${f(BIN_BID_PREV)}. Upbit's premium {PREM:.1f}% (from {PREM_PREV:.1f}%) on {UP_SHARE:.0f}% of global 24h volume (from {UPSH_PREV:.0f}%), plus Bithumb ${BITHUMB['volume_24h_usd']/1e6:.2f}M. {UPBIT_NOTE}")
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
                   "weeks_in_state": {"ledgerbyfigment": 17, "p2p_org_": 8, "truststakingsw": 19}.get(r["provider"], 5),
                   "note": f"emptied inside the archive (last locked > 0 snapshot {r['last_locked_in_archive']}); {r['inbound_txs_this_week']} inbound txs this week"
                           + (f"; delegators {d['prev_users']:,} -> {d['users']:,} ({d['users_delta']:+d})" if d.get("users") is not None and d.get("prev_users") is not None else "")})
for ident in ("egldstakingprovider", "procryptostaking"):
    states.append({"provider": ident, "state": "fee_squeezed", "locked_egld": mv(ident, "locked"),
                   "num_users": mv(ident, "users"), "num_nodes": mv(ident, "nodes"), "apr_pct": mv(ident, "apr") or 0.0,
                   "fee_pct": mv(ident, "fee") or 0.0, "weeks_in_state": 10,
                   "note": f"ELEVENTH WEEK AFTER THE FEE REVERSAL ({LIVE_DAYS:.1f}-day window): book {mv(ident,'delta'):+,.0f}, users {mv(ident,'users_delta'):+d}."})
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
                          "note": f"Zero transitions for an eleventh week. Join on contract address, {100*(sk['join_match_rate'] or 0):.0f}% match, no identity changes."},
    "fee_events": [{"provider": i, "fee_from_pct": 100.0, "fee_to_pct": mv(i, "fee") or 0.0, "apr_from_pct": 0.0, "apr_to_pct": mv(i, "apr") or 0.0,
                    "locked_egld": mv(i, "locked"), "locked_wow_egld": mv(i, "delta"), "users": mv(i, "users"),
                    "users_wow": mv(i, "users_delta"), "num_nodes": mv(i, "nodes")} for i in ("egldstakingprovider", "procryptostaking")],
    "unbonding_in_flight": {
        "wallet": ub["wallet"], "total_egld": ub["pending_total"],
        "legs": [{"provider": p["contract"][:10] + "..." + p["contract"][-8:], "amount": p["amount_egld"],
                  "days_to_unbond": p["days_remaining"], "date": "2026-08-14" if p["amount_egld"] < 100000 else "2026-08-15"} for p in ub["pending"]],
        "share_of_delegation_decline_pct": 0.0, "raw_residual_egld": sk["residual"], "corrected_direct_node_egld": None,
        "status": f"RETIRED, TWELFTH WEEK UNMOVED. Balance {f(ub['balance'],2)} EGLD, {f(ub['pending_total'])} unbonded-and-unclaimed.",
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
            f"COMPOUND RATE {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} reDelegateRewards vs {cvc['claim_count']} claimRewards), from 61.27%. Series: 49.44 / 62.68 / 52.40 / 58.28 / 60.85 / 59.38 / 59.40 / 60.93 / 61.27 / {cvc['compound_pct_of_reward_decisions']:.2f}. Inside the 57-63% range for an eighth run, on a week EGLD fell {abs(pc):.0f}%.",
            f"Retail {fates['retail']['total_events']} claims, {fates['retail']['by_count'].get('sold',0)} to a labelled exchange; mid-tier {fates['mid_tier']['total_events']}, {fates['mid_tier']['by_count'].get('sold',0)} sold; institutional {fates.get('institutional',{}).get('total_events',0)}, {fates.get('institutional',{}).get('by_count',{}).get('sold',0)} sold (too few to read).",
            f"Sample: {ag['providers_sampled']} of {ag.get('providers_requested',8)} providers, 7-day delegator window.",
            "PROVIDER OPERATORS DID NOT SELL FEES for a twenty-first consecutive run (destinations: DeFi deposits, rotated, held)."]},
    "analysis": (
        f"EXITS PICKED UP AGAIN. {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD in {LIVE_DAYS:.1f} days across {sk['providers_scanned']} provider contracts, about {f(sk['undelegated_week']/LIVE_DAYS*7)} a week, against ~20,000 in run #33 and ~86,000 in runs #31-#32. "
        f"Largest pending legs: " + ", ".join(f"{f(r_['amount_egld'])} ({r_['days_remaining']:.0f}d)" for r_ in sk['pool_rows'][:4]) + f"; measured pending among the window's callers {f(sk['pool_total'])} EGLD. Still no single exit above 10,000.\n\n"
        f"WITHDRAWALS. {O['withdraw_calls']} withdraw calls (from {O['prev_withdraw_calls']}) returned {f(WD.get('egld_returned_total',0))} EGLD: Binance {f(wd_top0)} (its unbond, Oct 22 09:15), ninjastaking {f(NINJA_AMT)} (re-delegated {NINJA_REDELEG_PCT:.0f}% to the same provider), Synexis, bober and westake. One wallet, erd1qyt62v5ndd..., withdrew 24,702 from westake, Synexis and bober on Oct 25 and is holding 25,698.\n\n"
        f"THE RATIO. /economics staked {M['staked_chg']:+,.0f} to {f(econ['staked'])}, ratio {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp): {f(BIN_UNDEL)} is Binance's custody move, {STAKED_EX_BIN:+,.0f} everything else. Delegation TVL {sk['delta_locked']:+,.0f} to {f(tl)} (vaporrepublic {mv('vaporrepublic','delta'):+,.0f}, ninjastaking {mv('ninjastaking','delta'):+,.0f}, pi-staking {mv('pi-staking','delta'):+,.0f}; alchemycapital {mv('alchemycapital','delta'):+,.0f}, egldsqueeze {mv('egldsqueeze','delta'):+,.0f}). HHI {sk['hhi']:.5f} (from {sk['prev_hhi']:.5f}). "
        f"72 of 99 APR-bearing providers sit in the 8-9% bucket; network APR rose to {100*econ['apr']:.2f}% as staked fell.\n\n"
        f"COMPOUNDING {cvc['compound_pct_of_reward_decisions']:.2f}%. DELEGATORS {sk['users_delta']:+,} to {f(sk['users'])}; {sk['gaining']} providers gained and {sk['losing']} lost. A {abs(pc):.0f}% price drop did not change reward behaviour: no tier sold more than a handful of claims.")}
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
        "volume_status": "evaluable; compared with run #33 (24h snapshots)",
        "mex_pair_depth": {"pair": "MEX/WEGLD", "tvl_usd": xx["mex_pair_depth"]["tvl_usd"], "tvl_egld": xx["mex_pair_depth"]["tvl_egld"],
                           "previous_tvl_egld": xx["mex_pair_depth"]["previous_tvl_egld"], "tvl_egld_wow_pct": xx["mex_pair_depth"]["tvl_egld_wow_pct"],
                           "volume_24h_usd": xx["mex_pair_depth"]["volume_24h_usd"], "trades_24h": xx["mex_pair_depth"]["trades_24h"],
                           "share_of_pool_tvl_pct": xx["mex_pair_depth"]["share_of_pool_tvl_pct"], "depth_rank": xx["mex_pair_depth"]["depth_rank"]},
        "mex_pair_event": r26["token_activity"]["xexchange"]["mex_pair_event"]},
    "analysis": (
        f"DEX VOLUME HELD. 24h volume ${f(xx['vol'])} ({f(bid['dexvol_egld'])} EGLD) against ${f(xx['prev_vol'])} ({f(bid['prev_dexvol_egld'])} EGLD), {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.0f}% in EGLD. WEGLD/USDC is {bid['wegld_usdc_share']:.0f}% of it; everything else traded ${f(bid['ex_wegld_usdc_vol'])}. "
        f"Turnover {bid['turnover']:.2f}% of pool TVL (from {bid['prev_turnover']:.2f}%). Pool TVL {f(bid['pooltvl_egld'])} EGLD ({100*(bid['pooltvl_egld']-bid['prev_pooltvl_egld'])/bid['prev_pooltvl_egld']:+.1f}% in EGLD), ${f(bid['pooltvl'])}: the EGLD-denominated rise is the price falling under the dollar half of each pool, not new liquidity.\n\n"
        f"MEX ${xx['mex_price']:.2e} ({xx['mex_wow']:+.1f}%, against EGLD {pc:+.1f}%); MEX/WEGLD depth ${f(xx['mex_pair_depth']['tvl_usd'])} ({xx['mex_pair_depth']['tvl_egld_wow_pct']:+.1f}% in EGLD), rank {xx['mex_pair_depth']['depth_rank']}.\n\n"
        f"STABLECOINS. USDC {usdc['pct']:+.2f}% ({USDC_D:+,.0f}) to {f(usdc['supply'])}, ending two bridge-led rises. Through the xBridge Tokens Wrapper {UB_['unwrap_txs']} unwraps sent {f(UB_['unwrap_usdc'])} USDC out ({f(UB_['unwrap_by_destination_token'].get('BSCUSDC-887875',0))} to BSC, {f(UB_['unwrap_by_destination_token'].get('ETHUSDC-220753',0))} to Ethereum) against {UB_['wrap_txs']} wraps bringing {f(UB_['wrap_usdc'])} in. "
        f"USDT {usdt['pct']:+.2f}% to {f(usdt['supply'])}, and Hatom's HUSDT supply rose {HT['HUSDT-6f0914']['supply_pct']:+.2f}%: some of the dollars stayed on chain as lending collateral (the ninjastaking exiter is one such loop).\n\n"
        f"NEWLY ISSUED: {len(newly)} issuances in the window.")}
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
         "notable_events": f"EGLD market {f(df['egld_mm_prev_balance'])} -> {f(df['egld_mm_balance'])} EGLD, HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.2f}%, HUSDC {HT['HUSDC-d80042']['supply_pct']:+.2f}%. Aggregate lending TVL in EGLD {hl:+.2f}% on a {pc:+.2f}% price window: the price mechanism (dollar collateral re-denominated), while the EGLD market itself shrank.",
         "health_signal": "draining" if EMM_D < -25000 else ("shrinking" if EMM_D < -5000 else ("growing" if EMM_D > 5000 else "flat"))},
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
         "notable_events": f"{f(es('VOXEGLD-5872e5'))} EGLD, supply {(em['VOXEGLD-5872e5']['pct'] or 0):+.1f}%, holders {em['VOXEGLD-5872e5']['holders']}.", "health_signal": hs(ep("VOXEGLD-5872e5"))},
        {"protocol": "VestaX Finance", "category": "liquid_staking", "addresses_tracked": 1, "tvl_usd": (es("VEGLD-2b9319") or 0) * price, "tvl_egld": es("VEGLD-2b9319") or 0.0,
         "tvl_wow_change_pct": ep("VEGLD-2b9319"), "transfers_24h": None,
         "notable_events": f"{f(es('VEGLD-2b9319'))} EGLD.", "health_signal": hs(ep("VEGLD-2b9319"))}],
    "sc_deployments": [],
    "analysis": (
        f"HATOM'S EGLD MARKET SHRANK; STABLECOIN MARKETS GREW. The EGLD money market holds {f(df['egld_mm_balance'])} EGLD, from {f(df['egld_mm_prev_balance'])} ({EMM_D:+,.0f}); HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.2f}%, HUSDT {HT['HUSDT-6f0914']['supply_pct']:+.2f}%, HUSDC {HT['HUSDC-d80042']['supply_pct']:+.2f}%, HWETH {HT['HWETH-b3d17e']['supply_pct']:+.2f}%. "
        f"Calls in the window: {HMM['by_function'].get('mintAndEnterMarket',{}).get('n',0)} supply-and-collateral calls from {HMM['by_function'].get('mintAndEnterMarket',{}).get('distinct_senders',0)} wallets, {HMM['by_function'].get('borrow',{}).get('n',0)} borrows from {HMM['by_function'].get('borrow',{}).get('distinct_senders',0)}, {HMM['by_function'].get('repayBorrow',{}).get('n',0)} repayments, {HMM['by_function'].get('redeem',{}).get('n',0)} redeems; no liquidations. "
        f"The pattern this window is borrow EGLD, swap to stablecoins, supply the stablecoins: a leveraged short on EGLD inside Hatom. The ninjastaking exiter ran it at least three times (Oct 24-26).\n\n"
        f"INVERSE-RATIO RULE. Aggregate lending TVL ex-HMEX reads {hl:+.2f}% in EGLD on a {pc:+.2f}% price move, a ratio of {abs(hl/pc) if pc else 0:.2f}: almost all of it is the price mechanism (dollar collateral re-denominated in a cheaper EGLD), not deposits.\n\n"
        f"LIQUID STAKING. SEGLD {lsd['SEGLD-3ad2d0']['pct']:+.2f}%, XEGLD {lsd['XEGLD-e413ed']['pct']:+.2f}%, SWTAO {lsd['SWTAO-356a25']['pct']:+.2f}%, USH {lsd['USH-111e09']['pct']:+.2f}%: flat. Emerging LSDs: VoxEGLD {(em['VOXEGLD-5872e5']['pct'] or 0):+.1f}%, LEGLD {(em['LEGLD-d74da9']['pct'] or 0):+.1f}%, JWLEGLD and VEGLD unchanged.\n\n"
        f"ACTIVITY. XOXNO aggregator {f(cnt('XOXNO Aggregator'))} transfers in 24h, OneDex {f(cnt('OneDex Swap'))}, Hatom LSD {f(cnt('Hatom Liquid Staking'))}. JEXchange router transfers over 7 days {f(jex7.get('JEXchange Router'))} on the main router.")}

# ---------------------------------------------------------------------------
UNDEL_WK = sk["undelegated_week"] / LIVE_DAYS * 7
R["anomalies"] = [
    {"metric": "korea_premium_pct", "current_value": PREM, "previous_value": PREM_PREV, "method": "rule_based", "severity": "high",
     "change_pct": 100 * (PREM - PREM_PREV) / PREM_PREV,
     "description": f"Upbit EGLD at ${up['converted_last']['usd']:.2f} vs Binance ${bn['converted_last']['usd']:.2f}: a {PREM:.1f}% premium (from {PREM_PREV:.1f}%) on {UP_SHARE:.0f}% of global 24h volume (from {UPSH_PREV:.0f}%). Upbit extended its caution review to Nov 16-20 on Oct 23 and UPbit's wallet moved no EGLD: a closed venue pricing its own stock. Rule-based: no weekly baseline."},
    {"metric": "egld_minus_btc_pp", "current_value": EGLD_VS_BTC, "previous_value": 2.3, "method": "rule_based", "severity": "medium",
     "change_pct": None,
     "description": f"EGLD {pc:+.2f}% vs BTC {M['btc_wow']:+.2f}% over {LIVE_DAYS:.1f} days ({EGLD_VS_BTC:+.1f}pp), after two windows ahead of BTC. Price z = {zz('price'):+.2f} on the level series (inside 2 sigma because the baseline still holds the pre-halt $4+ prices)."},
    {"metric": "staked_egld", "current_value": econ["staked"], "previous_value": M["staked_prev"], "method": "z_score", "severity": z["staked"].get("severity", "low"),
     "average_value": z["staked"].get("mean"), "stddev": z["staked"].get("stddev"), "z_score": zz("staked"), "change_pct": 100 * M["staked_chg"] / M["staked_prev"],
     "description": f"{M['staked_chg']:+,.0f} (z={zz('staked'):+.1f}), forecast in run #33: {f(BIN_UNDEL)} is Binance's unbond leaving the staking contract for custody; {STAKED_EX_BIN:+,.0f} is everything else. A known one-off step on a low-variance series, not a run on staking."},
    {"metric": "exchange_net_flow_egld", "current_value": EX_NET, "previous_value": 16237.0, "method": "rule_based", "severity": "medium",
     "change_pct": None,
     "description": f"{EX_NET:+,.0f} EGLD ex Binance's internal 320,000 custody move ({EX_NET_RAW:+,.0f} raw): the first net outflow since the rails reopened, led by KuCoin's first withdrawals since the halt ({ent_net('KuCoin'):+,.0f}) and Bybit ({ent_net('Bybit'):+,.0f}). Rule-based: partial-rail readings stay out of the weekly baseline."},
    {"metric": "undelegation_pace_egld_per_week", "current_value": UNDEL_WK, "previous_value": 20000.0, "method": "percent_threshold", "severity": "low",
     "change_pct": 100 * (UNDEL_WK - 20000.0) / 20000.0,
     "description": f"~{f(UNDEL_WK)}/week from ~20,000 in run #33 (degraded mode: short-window readings are not in the weekly baseline). {sk['undelegate_callers']} callers, largest pending leg {f(sk['pool_rows'][0]['amount_egld']) if sk['pool_rows'] else 0}."},
    {"metric": "usdc_supply", "current_value": usdc["supply"], "previous_value": usdc["prev"], "method": "rule_based", "severity": "low",
     "change_pct": usdc["pct"],
     "description": f"USDC {USDC_D:+,.0f}: wrapper out {f(UB_['unwrap_usdc'])}, in {f(UB_['wrap_usdc'])}. Reverses two bridge-led rises."},
    {"metric": "dex_volume_24h_egld", "current_value": bid["dexvol_egld"], "previous_value": bid["prev_dexvol_egld"], "method": "z_score", "severity": z["dexvol"].get("severity", "low"),
     "average_value": z["dexvol"].get("mean"), "stddev": z["dexvol"].get("stddev"), "z_score": zz("dexvol"),
     "change_pct": 100 * (bid["dexvol_egld"] - bid["prev_dexvol_egld"]) / bid["prev_dexvol_egld"],
     "description": f"xExchange 24h volume {f(bid['dexvol_egld'])} EGLD, {bid['wegld_usdc_share']:.0f}% WEGLD/USDC; z in dollars {zz('dexvol'):+.2f}: inside the band."},
]

R["trend_indicators"] = {
    "accelerating_exchange_outflows": [
        {"exchange": "KuCoin", "trend": "outflow", "cumulative_change_pct": next((w["pct"] for w in ex["per_wallet"] if w["exchange"] == "KuCoin"), None), "weeks_in_trend": 1,
         "interpretation": f"First customer withdrawals since the halt (from Oct 23): {ent_net('KuCoin'):+,.0f} EGLD. A one-off backlog release until it repeats."}],
    "validator_movements": {"providers_joining": 0, "providers_leaving": 0, "net_provider_change": 0, "notable_joiners": [],
                            "notable_leavers": [], "note": "No joins or deregistrations for an eleventh week."},
    "token_supply_events": [
        {"identifier": "USDC-c76f1f", "name": "WrappedUSDC", "event": "burn", "supply_previous": str(int(usdc["prev"])), "supply_current": str(int(usdc["supply"])),
         "change_pct": usdc["pct"], "description": f"{USDC_D:+,.0f} USDC: bridge outflow {f(UB_['unwrap_usdc'])} exceeded inflow {f(UB_['wrap_usdc'])}."},
        {"identifier": "USDT-f8c08c", "name": "USDT", "event": "mint", "supply_previous": str(int(usdt["prev"])), "supply_current": str(int(usdt["supply"])),
         "change_pct": usdt["pct"], "description": f"{f(usdt['supply']-usdt['prev'])} USDT added; Hatom HUSDT supply {HT['HUSDT-6f0914']['supply_pct']:+.2f}%."}],
    "consecutive_streaks": [
        {"metric": "exchange_net_inflow_since_reopening", "direction": "down", "weeks": 1, "cumulative_change_pct": None,
         "interpretation": f"Broken: six windows of net deposits (runs #28-#33) ended with {EX_NET:+,.0f} ex internal moves."},
        {"metric": "egld_vs_btc", "direction": "down", "weeks": 1, "cumulative_change_pct": None,
         "interpretation": f"Two windows ahead of BTC ended: {EGLD_VS_BTC:+.1f}pp this window."},
        {"metric": "korea_premium", "direction": "up", "weeks": 3, "cumulative_change_pct": None,
         "interpretation": f"10.6% -> 12.2% -> {PREM:.1f}% across runs #32-#34 with Upbit's share 8% -> 47% -> {UP_SHARE:.0f}%: widening while Upbit stays closed."},
        {"metric": "total_delegators", "direction": "flat", "weeks": 22, "cumulative_change_pct": -1.3, "interpretation": f"{sk['users_delta']:+,} to {f(sk['users'])}. The base rate."},
        {"metric": "provider_operator_fee_selling", "direction": "flat", "weeks": 22, "cumulative_change_pct": 0.0, "interpretation": "Twenty-two runs with zero exchange destinations from sampled operator wallets."}],
    "regime_shifts": [
        {"metric": "exchange_rail_state", "before_value": 0.0, "after_value": round(len(OPEN) / max(1, len([k for k in VEN if k not in _NONVENUE])), 2),
         "description": f"{len(OPEN)} of {len([k for k in VEN if k not in _NONVENUE])} tracked venues move EGLD both ways ({', '.join(OPEN)}); KuCoin joined on Oct 23. UPbit had no EGLD flow; its review runs to Nov 16-20."},
        {"metric": "staked_ratio", "before_value": M["sr_prev"], "after_value": M["sr"],
         "description": f"STEP CONFIRMED: {100*M['sr_prev']:.2f}% -> {100*M['sr']:.2f}%, Binance's 320,000 moved from staked to custody. A level change by one holder's choice; it holds until Binance re-delegates (binance-custody-hold)."},
        {"metric": "korea_venue_share", "before_value": UPSH_PREV, "after_value": UP_SHARE,
         "description": f"CANDIDATE: Upbit {UPSH_PREV:.0f}% -> {UP_SHARE:.0f}% of global EGLD volume. Promote if it stays above 50% at run #35."}]}

R["watch_list"] = [
    {"item": "UPBIT CAUTION REVIEW - extended to Nov 16-20", "weeks_on_list": 8,
     "reason": f"Upbit's Oct 23 notice extended the review. Premium {PREM:.1f}% (from {PREM_PREV:.1f}%), Upbit {UP_SHARE:.0f}% of global volume. UPbit's wallet moved no EGLD. PRE-COMMITTED (upbit-premium-on-decision)."},
    {"item": "EXCHANGE FLOWS TURNED OUT", "weeks_on_list": 4,
     "reason": f"{EX_NET:+,.0f} ex internal moves; overhang-absorbed resolved 'no conclusion' (flow passed, price failed). PRE-COMMITTED (outflow-bottom) for run #35."},
    {"item": "BINANCE STAKING CUSTODY", "weeks_on_list": 2,
     "reason": f"{f(CUST_NOW)} EGLD; no outbound since the 320,000 receipt. PRE-COMMITTED (binance-custody-hold) by run #35: interim 'held'."},
    {"item": "HATOM SHORT-EGLD LOOPS", "weeks_on_list": 1,
     "reason": "The ninjastaking exiter borrowed EGLD on Hatom, swapped it into USDC/USDT and supplied those, repeatedly (Oct 24-26); the EGLD market shrank while HUSDT grew. Count wallets running the loop next run."},
    {"item": "KUCOIN REOPENED", "weeks_on_list": 1,
     "reason": f"First customer withdrawals since the halt from Oct 23 ({f(KUC.get('out_egld',0))} out, {f(KUC.get('in_egld',0))} in). Watch whether the outflow is a one-off backlog."},
    {"item": "SELLER CHAIN erd1hl5y4a -> erd1hhvfrw -> BINANCE", "weeks_on_list": 3,
     "reason": f"{f(SC_HOPS)}-{f(SC_TOTAL)} to Binance since Oct 9; {f(SC_WINDOW)} directly this window. erd1hl5y4a... ({f(HL5_BAL)}) sent {f(HL5_WIN_VXA)} to Unknown Whale erd1vxa2vk... on Oct 26 instead. Watch for the next one-shot hop."},
    {"item": "WESTAKE / SYNEXIS / BOBER EXITER erd1qyt62v5ndd", "weeks_on_list": 1,
     "reason": "Withdrew 24,702 from three providers on Oct 25 and holds 25,698 unstaked. Next hop decides whether it is supply."},
    {"item": "CROSS-VENUE WALLETS", "weeks_on_list": 5,
     "reason": f"erd1d2anjjha... {f(ARB['erd1d2anjjha']['in_egld'])} in / {f(ARB['erd1d2anjjha']['out_egld'])} out; new pass-throughs erd1470jqfmh... (Bybit -> Binance) and erd1wznqcfmq... (Binance -> Bybit). Keep netting them out."},
    {"item": "OTC PIPELINE", "weeks_on_list": 34,
     "reason": f"Quiet: gross {f(otc['gross_out'])}, desks {f(otc['desk_bal'])}. Keep until Upbit's decision."},
    {"item": "EXPLOIT WALLET AND POISONING RING", "weeks_on_list": 9,
     "reason": f"Incident addresses hold {HR['invalid_total_egld']:.2f} EGLD; poisoning operator {PR['operator_out_7d']} dust txs in the window, zero hits above dust."},
]

# ---------------------------------------------------------------------------
prior = {t["id"]: t for t in r26["pre_committed_tests"]}
tests = [t for t in r26["pre_committed_tests"] if t["status"] == "resolved"]


def resolve(tid, outcome, measured, resolution):
    t = dict(prior[tid]); t.update({"status": "resolved", "outcome": outcome, "resolved_in_run": 34, "measured_value": measured, "resolution": resolution}); return t


tests.append(resolve("overhang-absorbed", "inconclusive",
    f"run #34 fixed window {iso(OV_S)} -> {iso(OV_E)}: rails net {OV_NET:+,.0f} EGLD raw, {OV_NET_EX_ARB:+,.0f} ex cross-venue wallets (deposits {f(OV_IN)}, withdrawals {f(OV_OUT)}); EGLD {OV_EGLD:+.1f}% vs BTC {OV_BTC:+.1f}% = {OV_REL:+.1f}pp.",
    f"Branch 'otherwise / no conclusion': the flow leg passed (net {OV_NET_EX_ARB:+,.0f} < +10,000) but the price leg failed ({OV_REL:+.1f}pp < -1pp); 'still distributing' also fails (net not > +25,000). "
    f"The halt-weeks inflow did end, but EGLD fell anyway: the selling came from EGLD already on exchanges (and from Korea-closed liquidity elsewhere), not from new deposits. Follow-up registered: outflow-bottom."))
tests.append(resolve("ninjastaking-exit-destination", "against",
    f"run #34: withdraw {NINJA_WD_TS} ({f(NINJA_AMT)} EGLD); {f(NINJA_REDELEG)} ({NINJA_REDELEG_PCT:.0f}%) delegated back to ninjastaking at 2026-10-24 05:23 UTC; 0 to a labelled exchange; the rest swapped via xExchange/XOXNO into USDC/USDT supplied on Hatom (with EGLD borrowed against it).",
    "Branch 'rotation' (> 50% re-delegated): the claim that the unDelegate was a sale is contradicted. The wallet re-delegated to the same provider, so the 'exit' was a partial de-risking into stablecoins, executed on-chain through Hatom rather than on an exchange."))
tests.append(resolve("korea-premium-arbitrage", "inconclusive",
    f"run #34: UPbit received {UPBIT_DEP_N} EGLD deposits in the window (0 since run #27 above dust in the window); premium {PREM:.1f}%. Upbit extended its caution review to Nov 16-20.",
    "Branch 'deposits still closed at run #29 = not evaluable, retire': UPbit deposits never reopened. Retired and replaced by upbit-premium-on-decision, which is tied to Upbit's announced decision date."))
for tid, note in [("delivery-price-relevance-2", f"run #34: desk gross {f(otc['gross_out'])} EGLD; no UPbit delivery. Not evaluable; Upbit's review now ends Nov 16-20."),
                  ("binance-custody-hold", f"run #34 INTERIM: custody {f(CUST_NOW)} EGLD; {len(CUST['out'])} outbound txs since the receipt, {f(CUST['out_to_hot_egld'])} to the hot wallet, {f(CUST['delegated_egld'])} re-delegated -> reads 'held' so far. Resolves by run #35.")]:
    t = dict(prior[tid]); t.update({"status": "open", "measured_value": note, "resolution": None}); tests.append(t)


def new(tid, claim, threshold, branches, measured):
    return {"id": tid, "registered_in_run": 34, "claim": claim, "threshold": threshold, "branches": branches,
            "status": "open", "outcome": None, "resolved_in_run": None, "measured_value": measured, "resolution": None}


tests += [
    new("upbit-premium-on-decision", "The Upbit premium is a closed-venue premium: it collapses once Upbit decides (delisting or reopened deposits).",
        "At the first run after Upbit's announced decision (Nov 16-20): if Upbit delists EGLD or reopens deposits, Upbit-Binance premium < 5% = closed-venue premium; > 10% = Korean demand premium; 5-10% = no conclusion; caution extended again with deposits closed = re-date the test once",
        [{"condition": "decision taken and premium < 5%", "reading": "closed-venue premium"},
         {"condition": "decision taken and premium > 10%", "reading": "Korean demand"},
         {"condition": "decision taken and premium 5-10%", "reading": "no conclusion"},
         {"condition": "caution extended again, deposits closed", "reading": "re-date once"}],
        f"run #34: premium {PREM:.1f}%, Upbit {UP_SHARE:.0f}% of global volume, UPbit wallet idle."),
    new("outflow-bottom", "With exchange inflow over, EGLD stops underperforming BTC.",
        "Over run #35's window (balance basis ex internal moves, cross-venue wallets out): tracked exchanges net <= 0 AND EGLD - BTC >= 0pp = bottoming; net > +10,000 AND EGLD - BTC < -2pp = renewed distribution; otherwise no conclusion",
        [{"condition": "net <= 0 and EGLD-BTC >= 0pp", "reading": "bottoming"},
         {"condition": "net > +10K and EGLD-BTC < -2pp", "reading": "renewed distribution"},
         {"condition": "otherwise", "reading": "no conclusion"}],
        f"run #34: net {EX_NET:+,.0f} ex internal, EGLD {EGLD_VS_BTC:+.1f}pp vs BTC."),
]
resolved = [t for t in tests if t.get("resolved_in_run") == 34]
as_pred = sum(1 for t in resolved if t["outcome"] == "as_predicted")
R["pre_committed_tests"] = tests

# ---------------------------------------------------------------------------
R["meta_learning"] = {
    "run_number": 34,
    "endpoints_that_worked": status["ok"],
    "endpoints_that_failed": [f"NONE with data missing. {D.get('_n_429', 0)} HTTP 429s in the main pass; 0 paged errors; 0 errors in follow-up, rails and traces."],
    "api_quirks": [
        "A balance-basis window that starts between a transfer's send and the previous run's read inherits the transfer: Binance's 320,000 custody receipt (Oct 22 09:18) post-dated run #33's 07:28 read, so it shows as +320,000 at 'Binance' this run. Net named internal moves out of the exchange total before reading customer flow.",
        "The rails pagination capped at 2,000 txs per side since restart 2; Binance.com reached ~1,100 value-bearing sends plus spam, so the cap was raised to 8,000 before it truncated silently (ascending order would have dropped the newest txs).",
        "/accounts/{addr}/delegation shows only active stake once an unbond is withdrawn; the ninjastaking exiter's re-delegation was visible there as a second contract (15,000) before the trace confirmed the delegate call."],
    "data_gaps": [
        "Bithumb's EGLD caution decision was not found (Upbit's was).",
        "Kraken has no tracked address.",
        "Hatom UTK Money Market and OneDex Launchpad still fail bech32 validation.",
        "The Hatom loop is identified for one wallet; a protocol-wide count of borrow -> swap -> supply loops is not yet collected."],
    "key_findings": [
        f"EGLD {pc:+.1f}% ({EGLD_VS_BTC:+.1f}pp vs BTC) while exchanges lost {abs(EX_NET):,.0f} EGLD net of internal moves.",
        f"Upbit extended its review to Nov 16-20; premium {PREM:.1f}% on {UP_SHARE:.0f}% of global volume.",
        f"overhang-absorbed resolved inconclusive (flow passed, price failed); ninjastaking-exit-destination resolved against (rotation, {NINJA_REDELEG_PCT:.0f}% re-delegated).",
        f"Staked {M['staked_chg']:+,.0f}: the forecast Binance step plus {STAKED_EX_BIN:+,.0f}.",
        f"Seller chain: {f(SC_HOPS)}-{f(SC_TOTAL)} to Binance since Oct 9, {f(SC_WINDOW)} this window.",
        "KuCoin reopened withdrawals Oct 23."],
    "action_items_from_previous": len(r26["meta_learning"]["recommendations_for_next_run"]),
    "action_items_completed_detail": [
        f"OVERHANG-ABSORBED - done: fixed rail window Oct 19 14:40 -> Oct 26 14:40 measured ({OV_NET_EX_ARB:+,.0f} ex cross-venue, {OV_REL:+.1f}pp); resolved inconclusive.",
        f"NINJASTAKING - done: withdraw traced leg by leg; {NINJA_REDELEG_PCT:.0f}% re-delegated; resolved against (rotation).",
        "UPBIT - done: Oct 23 notice found (caution extended to Nov 16-20); korea-premium-arbitrage retired, upbit-premium-on-decision registered.",
        f"STAKED STEP + CUSTODY - done: staked {M['staked_chg']:+,.0f} with 320,000 attributed; custody traced since the receipt (no outbound).",
        f"SELLER CHAIN - done: erd1hl5y4a/erd1079hvt0/erd1hhvfrw and both hops traced since Oct 9: {f(SC_HOPS)}-{f(SC_TOTAL)} EGLD to Binance.com (upper bound counts the shared drip wallet in full).",
        "CAFFEINATE - done: collector and chained follow-ups ran under caffeinate with python -u; whole collection ~25 minutes."],
    "methodology_changes": [
        "FIXED-WINDOW RAILS: rails_run34.py stores per-wallet counts and per-counterparty totals for a fixed [start, end) window (rail_ov_*) next to the rail window and the trailing 7 days, so a pre-committed window resolves exactly regardless of run cadence.",
        "PRICE ON THE SAME WINDOW: the test's EGLD-vs-BTC leg is read from the CoinGecko hourly series at the window's own endpoints, not from report-to-report prices.",
        "INTERNAL MOVES THAT STRADDLE A READ: a named internal transfer that landed between the previous read and the previous rail pass is netted out of this run's balance-basis exchange total and reported separately (raw and ex-internal both published)."],
    "new_addresses_discovered_detail": [
        "erd1qyt62v5ndd... - withdrew 24,702 EGLD from westake, Synexis and bober on 2026-10-25; holds 25,698 unstaked",
        "erd1ygkh9r65xm8nvczg0jcc3y3ncc3tq88zym7vpve7fpdmv2u0qgusfwf98h - fresh wallet, 27,066 EGLD Binance.com withdrawal 2026-10-26 08:15 UTC, held",
        "erd1r35rd2zy8dgkzan66ma2ahpx3rlluynlzvsq4f7td4nyu0ru245qftkzvg - first large KuCoin withdrawal after the halt (9,999 in three sends, 2026-10-23 05:54-06:04)",
        "erd1470jqfmh... / erd1wznqcfmq... - cross-venue pass-through wallets (Bybit -> Binance, Binance -> Bybit, within minutes)"],
    "action_items_completed": 6,
    "new_addresses_discovered": 4,
    "most_valuable_insight": (
        f"The two halves of the overhang question came apart. On chain the halt-weeks supply is gone: exchanges lost {abs(EX_NET):,.0f} EGLD net, KuCoin's stuck customers withdrew, the seller chain that fed Binance went quiet and the one large exiter re-staked. "
        f"Yet EGLD fell {abs(pc):.0f}% and trailed BTC by {abs(EGLD_VS_BTC):.1f}pp. The market that now sets the marginal EGLD price is one that cannot settle on chain: Upbit carries {UP_SHARE:.0f}% of global volume at a {PREM:.1f}% premium and has postponed its decision to Nov 16-20. "
        f"Outside Korea the book is thin and its sellers are holders already on exchanges, invisible to deposit tracking."),
    "top_recommendation": "RUN #35 FIRST: resolve binance-custody-hold and outflow-bottom; count Hatom borrow -> swap -> supply loops protocol-wide; re-read the Upbit premium and share.",
    "recommendations_for_next_run": [
        "Resolve binance-custody-hold on custody erd1rf4hv70... (re-delegated / to hot wallet / held).",
        "Resolve outflow-bottom on run #35's window: balance basis ex internal moves and cross-venue wallets, EGLD-BTC from the hourly series at the window endpoints.",
        "Hatom loops: scan EGLD money-market borrowers in the window for a swap into USDC/USDT followed by a stablecoin supply within an hour; report count, wallets and EGLD borrowed.",
        "Trace erd1qyt62v5ndd... (25,698 unstaked) and erd1ygkh9r65... (27,066 from Binance) one hop.",
        "KuCoin: is the outflow a backlog release (decaying) or an open rail (two-way)? Per-day counts since Oct 23.",
        "Record the Upbit premium and volume share every run until Nov 20; search for Bithumb's decision."],
    "dashboard_feature_suggestions": [
        {"title": "Staked-EGLD change waterfall",
         "motivation": f"Staked fell {abs(M['staked_chg']):,.0f} this run (z {zz('staked'):+.1f}), of which 320,000 is one holder's custody choice. The dashboard shows the delta as one number, so a forecast one-off step reads like a run on staking.",
         "suggested_visualization": "waterfall per run: previous staked -> named large withdraws (Binance, ninjastaking, ...) -> other withdraws -> new delegations -> current staked, with the custody move highlighted",
         "data_already_available": True, "data_source": "staking_intelligence.unbonding_in_flight.queue_this_week (withdraw_egld_by_provider_top, withdraw_egld_returned) plus network_health.deltas.staked_egld_added",
         "priority": "high"},
        {"title": "Hatom leverage-loop tracker",
         "motivation": "The ninjastaking exiter's 'exit' was a borrow EGLD -> swap -> supply stablecoins loop repeated over three days; the EGLD market shrank while HUSDT grew. On-chain shorting is invisible in the current DeFi table.",
         "suggested_visualization": "per-run bars of EGLD borrowed into loops vs stablecoin supplied, with a wallet drilldown listing each loop's legs on a timeline",
         "data_already_available": False, "data_source": "new collector pass over Hatom EGLD money-market borrow calls joined with the borrower's swap and supply calls within an hour",
         "priority": "medium"},
        {"title": "Fixed test-window overlay on the price chart",
         "motivation": "overhang-absorbed failed on price alone; the reader cannot see the test window, its flow total and EGLD vs BTC over exactly that window in one place.",
         "suggested_visualization": "shaded window on the EGLD/BTC relative-price line with the rail net flow annotated, one band per pre-committed window (rail_overhang_window)",
         "data_already_available": True, "data_source": "whale_intelligence.exchange_flows.rail_status.rail_overhang_window plus cg hourly series in data/collected",
         "priority": "low"}],
    "dashboard_suggestions_followup": [
        {"title": "Venue volume share and premium timeline", "status": "pending",
         "note": f"Not built; priority up: Upbit's share went to {UP_SHARE:.0f}% and the premium to {PREM:.1f}% this run."},
        {"title": "Seller funding-chain graph", "status": "pending",
         "note": "Not built; the data now exists as run34_traces.seller_chain (per-wallet totals and hops since Oct 9)."},
        {"title": "Pre-committed test ledger with outcomes", "status": "built",
         "note": "Already present as the Scoreboard panel (useScoreboard aggregates pre_committed_tests across reports); run #33's suggestion was redundant."}],
    "withdrawn_claims": [],
}

rep = {k: R[k] for k in ["metadata", "executive_summary", "network_health", "whale_intelligence", "staking_intelligence", "token_activity",
                         "defi_activity", "anomalies", "trend_indicators", "watch_list", "meta_learning", "pre_committed_tests"]}
json.dump(rep, open(f"{REPO}/reports/{RD}.json", "w"), indent=1, default=str)
print("report written", len(json.dumps(rep, default=str)), "bytes")
print(f"tests resolved this run {len(resolved)}, as_predicted {as_pred}, open {sum(1 for t in tests if t['status']=='open')}")
print("PREM", round(PREM, 1), "UP_SHARE", round(UP_SHARE, 1), "OPEN", OPEN, "DEPONLY", DEPONLY, "EX_NET", round(EX_NET), "OV", round(OV_NET_EX_ARB), round(OV_REL, 2), OV_OUTCOME)
