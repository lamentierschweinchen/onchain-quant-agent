#!/usr/bin/env python3
"""Run #33 stage 2: assemble reports/2026-10-22.json from derived.json + snapshot.

~2.7-day window (Oct 19 14:26 -> Oct 22 07:28) plus a trailing 7-day rail pass (interim reading for overhang-absorbed).
"""
import json
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD = "2026-10-22"
O = json.load(open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/3c0a602f-249e-4712-aa69-2471f95a7c73/scratchpad/run33w/derived.json"))
D = json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev = json.load(open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/3c0a602f-249e-4712-aa69-2471f95a7c73/scratchpad/run33w/previous_run32.json"))
status = json.load(open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/3c0a602f-249e-4712-aa69-2471f95a7c73/scratchpad/run33w/status.json"))
beh = json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
r26 = json.load(open(f"{REPO}/reports/2026-10-19.json"))   # previous report (name kept for the reused blocks)
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

# ---- run #33 traces ----
TR = D["run33_traces"]
BINV = VEN["Binance.com"]
BD = TR["binance_daily"]["days"]
BIN_DEP = BINV["in_egld"]; BIN_WD_EXT = BINV["out_egld"]
BIN_EXT_NET = BIN_DEP - BIN_WD_EXT
BIN_EXT_PER_DAY = BIN_EXT_NET / LIVE_DAYS
BIN_ENTITY_NET = next((e2["net_flow_egld"] for e2 in ex["entity"] if e2["entity"] == "Binance"), 0.0)
def ent_net(n): return next((e2["net_flow_egld"] for e2 in ex["entity"] if e2["entity"] == n), 0.0)
BU = TR["binance_unbond"]
# run #33: the unbond matured (Oct 21 16:21) and was withdrawn Oct 22 09:15; /delegation is now empty
BIN_UNDEL = 320002.0
BIN_MATURES = "2026-10-21 16:21 UTC"
UD = TR["unbond_destinations"]["binance_unbond"]["rows"]
BIN_WD_OUT = sum(x["egld"] for x in BU["out"] if x["egld"] > 0)
BIN_TO_CUST = sum(x["egld"] for x in UD if x.get("label") == "Binance Staking")
BIN_TO_CUST_PCT = 100 * BIN_TO_CUST / BIN_WD_OUT if BIN_WD_OUT else 0.0
BIN_WD_TS = next((x["ts"] for x in BU["out"] if x.get("fn") == "withdraw"), None)
BIN_SEND_TS = next((x["ts"] for x in BU["out"] if x["egld"] > 0), None)
CUST_NOW = next((x["to_balance_egld"] for x in UD if x.get("label") == "Binance Staking"), cust["balance"])
BIN_UNDEL_DAYS = 0.0
POOL = D.get("unbonding_pool") or []
NU = TR["ninjastaking_unbond"]
_nl = [(d_["contract"], u) for d_ in NU["delegation"] for u in (d_.get("userUndelegatedList") or [])]
NINJA = {"wallet": NU["wallet"], "amount_egld": sum(int(u["amount"]) for _, u in _nl) / 1e18,
         "days_remaining": max([u["seconds"] for _, u in _nl] or [0]) / 86400, "wallet_balance_egld": NU["balance_egld"],
         "active_stake_egld": sum(int(d_.get("userActiveStake") or 0) for d_ in NU["delegation"]) / 1e18}
NINJA_MATURES = iso(D["liveness"]["0"]["timestamp"] + max([u["seconds"] for _, u in _nl] or [0]))
NINJA_REDELEG = sum(x["egld"] for x in NU["out"] if x.get("fn") == "delegate")
NINJA_WD = 7071.0   # run #32: withdrew from inceptionnetwork and pi-staking on Oct 18 (stored in run #32)
NINJA_LEGS = TR["unbond_destinations"]["ninjastaking_unbond"]["rows"]
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
PACE_NOW = EX_NET_EX_ARB / LIVE_DAYS; PACE_PREV = 12843 / 4.22   # run #32: +12,843 over 4.22 days (cross-venue wallets kept nothing)
ENT_EX_ARB = {"Binance": ent_net("Binance") + ARB["erd1d2anjjha"]["in_by_counterparty"].get("Binance.com", 0.0),
              "Bybit": ent_net("Bybit") + ARB["erd1d2anjjha"]["in_by_counterparty"].get("Bybit", 0.0) - ARB["erd13sytuz92"]["out_by_counterparty"].get("Bybit", 0.0),
              "Gate.io": GATE_NET - ARB["erd1d2anjjha"]["out_by_counterparty"].get("Gate.io", 0.0) + ARB["erd13sytuz92"]["in_by_counterparty"].get("Gate.io", 0.0)}
# ---- run #33: trailing 7-day rail window (overlaps run #32 by ~4 days); interim reading only ----
R7_START = D["_period"]["rail_7d_start_ts"]
R7_DAYS = (D["liveness"]["0"]["timestamp"] - R7_START) / 86400
_RV = [r for r in RAILS.values() if r["label"] not in _NONVENUE_INTERNAL]
R7_IN = sum(r["in"]["egld_7d"] for r in _RV); R7_OUT = sum(r["out"]["egld_7d"] for r in _RV)
R7_ARB_IN = sum(v for r in RAILS.values() for c, v in r["in"]["by_cp_7d"].items() if c in ARB_SET)
R7_ARB_OUT = sum(v for r in RAILS.values() for c, v in r["out"]["by_cp_7d"].items() if c in ARB_SET)
R7_NET = R7_IN - R7_OUT; R7_NET_EX_ARB = R7_NET - R7_ARB_IN + R7_ARB_OUT
R7_BY = {}
for r in _RV:
    R7_BY[r["label"]] = R7_BY.get(r["label"], 0.0) + r["in"]["egld_7d"] - r["out"]["egld_7d"]
P30 = json.load(open(f"{REPO}/reports/2026-10-15.json"))   # run #33: trailing 7d starts ~Oct 15
P7_EGLD = 100 * (price - P30["metadata"]["egld_price_usd"]) / P30["metadata"]["egld_price_usd"]
P7_BTC = 100 * (M["btc"] - P30["metadata"]["btc_price_usd"]) / P30["metadata"]["btc_price_usd"]
P7_REL = P7_EGLD - P7_BTC
BAL7_EX_ARB = r26["whale_intelligence"]["exchange_flows"]["net_change_egld"] + EX_NET_EX_ARB   # run #32 (+12,843, cross-venue kept nothing) + this window: Oct 15 09:08 -> Oct 22 07:28, balance basis
ABSORBED_INTERIM = ("absorbed" if (R7_NET_EX_ARB < 10000 and P7_REL >= -1) else "still distributing" if (R7_NET_EX_ARB > 25000 and P7_REL < -3) else "no conclusion")
# ---- whale / depositor traces ----
HHV = "erd1hhvfrwvqj5jhxqwlac9vftwgnlkv0s9y7xy7xp98vehlq74qee6srkqgdh"
HHV_HOP = "erd1rcty49rmvv6z80exv2l4pj2cgnnyqkjs639ss2cz0r5nkr8s4rnqfu5v0n"   # run #33 hop (run #32 hop: erd1rgm4td29...)
HHV_DEP = next((x["egld"] for x in TR["binance_daily"]["top_deposits_window"] if x["from"] == HHV_HOP), 0.0)
WB = CBL["whale_b"]; WB_IN = sum(x["egld"] for x in WB["in"])
UB_ = TR["usdc_bridge"]; USDC_NET_IN = UB_["wrap_usdc"] - UB_["unwrap_usdc"]
USDC_D = usdc["supply"] - usdc["prev"]
OVERLAP_NOTE = f"Rail window starts exactly at run #32's stored rail end (2026-10-19 14:40:28 UTC) and ends at this run's rail pass ({iso(D['_period']['rail_window_end_ts'])}), stored in the snapshot. Balance-based deltas end at the collector's read ({iso(D['liveness']['0']['timestamp'])}); the Binance custody receipt (09:18 UTC) falls between the two."
MEGA_IN = bid["mega_delta"]
UPBIT_DEP = VEN.get("UPbit", {}).get("in_egld", 0); UPBIT_DEP_N = VEN.get("UPbit", {}).get("in_senders", 0)
PREV_BOOK = prev["exchange_orderbook_latest"]
PREM_PREV = PREV_BOOK.get("korea_premium_pct", 13.6)
UPSH_PREV = PREV_BOOK.get("upbit_share_of_volume_pct", 10.7)
BIN_BID_PREV = PREV_BOOK["binance"]["depth_minus2_usd"]
WIN_TXT = f"{LIVE_DAYS:.1f}-day window (Oct 19 14:26 -> Oct 22 {hm(D['liveness']['0']['timestamp'])[-5:]} UTC)"
WINDOW_NOTE = f"{WIN_TXT}, plus a trailing 7-day rail pass from {iso(R7_START)[:16]} (overlaps run #32 by about four days; an interim reading for overhang-absorbed, whose own window matures Oct 26). Point-in-time flows below are {LIVE_DAYS:.1f}-day flows unless marked 7d."
wd_top0 = (WD.get("by_provider_top") or [[0, 0]])[0][1]
R = {}
R["metadata"] = {
    "report_date": RD, "period_start": "2026-10-19", "period_end": RD,
    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "egld_price_usd": price, "btc_price_usd": M["btc"], "eth_price_usd": M["eth"],
    "run_number": 33,
    "data_sources_ok": status["ok"] + [
        f"follow-up pass: {WD.get('calls', 0)} withdraw calls decoded, poisoning lookalikes re-scanned (0 errors)",
        "rail check (rails_run33.py): value-bearing EGLD per tracked exchange wallet from run #32's stored rail end (2026-10-19 14:40:28 UTC), plus a trailing 7-day pass with per-counterparty totals; own end time stored in the snapshot",
        "targeted traces (trace_run33.py): Binance de-staking wallet withdraw and one-hop destination, ninjastaking exiter /delegation and legs, Binance.com daily rails since Oct 9, Binance depositor funding sources, USDC through the xBridge Tokens Wrapper, cross-venue wallets, Coinbase / Whale B / Mega Whale legs, UPbit depositors, OTC desk legs, Hatom EGLD market calls",
        "web check (Oct 22): Upbit's EGLD caution review (Oct 19-23) still had no published outcome"],
    "data_sources_failed": status["failed"],
    "data_sources_recovered": [
        "LIVENESS GATE PASSED: every shard within seconds of real time at collection",
        f"{D.get('_n_429', 0)} HTTP 429 responses in the main pass; 0 paged errors, 0 API errors",
        "The collector ran about five hours because the host Mac idle-slept between agent turns and suspended the background process; the follow-up passes were re-run under caffeinate and finished in minutes. Balances are as of the collector's first reads (07:28 UTC); rails and traces run to about 10:00 UTC.",
        OVERLAP_NOTE,
        WINDOW_NOTE,
        f"delegator reward behaviour sampled {ag['providers_sampled']} of {ag.get('providers_requested', 8)} providers"]}

R["executive_summary"] = [
    {"category": "staking", "severity": "high", "finding":
     f"BINANCE'S 320,002 EGLD UNBOND WENT TO ITS OWN CUSTODY. The de-staking wallet withdrew it at {hm(BIN_WD_TS)} UTC and sent {f(BIN_TO_CUST)} EGLD to Binance Staking custody (erd1rf4hv70...) three minutes later; custody now holds {f(CUST_NOW)}. "
     f"{BIN_TO_CUST_PCT:.0f}% to custody against a 70% bar: binance-undelegation-destination resolves as predicted (re-allocation, not supply). The EGLD is no longer delegated, so /economics staked should fall by about 320,000 (~{100*BIN_UNDEL/econ['circulatingSupply']:.1f}pp of the ratio) at the next read unless Binance re-stakes it."},
    {"category": "network", "severity": "medium", "finding":
     f"EGLD BEAT BTC FOR A SECOND WINDOW WHILE EXCHANGE INFLOW SPED UP. EGLD {pc:+.1f}% to ${price:.2f} against BTC {M['btc_wow']:+.1f}% ({EGLD_VS_BTC:+.1f}pp) over {LIVE_DAYS:.1f} days, while tracked exchanges took {ex['net']:+,.0f} EGLD net, about {PACE_NOW:,.0f}/day against ~{PACE_PREV:,.0f}/day in run #32. "
     f"On the trailing 7 days (rails, overlapping run #32) exchanges netted {R7_NET_EX_ARB:+,.0f} ex cross-venue wallets while EGLD gained {P7_REL:+.1f}pp on BTC. Supply is still arriving and is being bought: overhang-absorbed reads '{ABSORBED_INTERIM}' on this interim basis; its own window matures Oct 26."},
    {"category": "whale", "severity": "medium", "finding":
     f"THE BINANCE FUNDER USED A SECOND FRESH HOP, TWICE AS LARGE. erd1hhvfrw... sent a 6 EGLD test and then 24,994 EGLD to a new wallet (erd1rcty49..., nonce 2) on Oct 20 21:18-21:26, which deposited {f(HHV_DEP)} at Binance.com nine minutes later. "
     f"That is half of Binance.com's {f(BIN_DEP)} EGLD of deposits in the window and the reason Oct 20 took {f(BD.get('2026-10-20',{}).get('dep_egld',0))}. erd1hhvfrw... is a busy wallet (nonce 9,000, 12,643 EGLD left) fed in clips via erd1079hvt0... from Unknown Whale erd1hl5y4a... (220,695 EGLD)."},
    {"category": "token", "severity": "medium", "finding":
     f"KOREAN VENUES TOOK NEARLY HALF OF GLOBAL EGLD VOLUME. Upbit traded ${up['converted_volume']['usd']/1e6:.2f}M in 24h, {UP_SHARE:.0f}% of all venues (from {UPSH_PREV:.0f}%), and Bithumb another $1.0M, at a {PREM:.1f}% premium to Binance (from {PREM_PREV:.1f}%). "
     f"Upbit's caution decision is due Oct 19-23 and no outcome was published by Oct 22; UPbit's wallet still moved no EGLD. Volume this concentrated on a market that cannot deposit or withdraw is positioning ahead of the decision, not arbitrage."},
    {"category": "staking", "severity": "low", "finding":
     f"UNBONDING FELL BY THREE QUARTERS. {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD in {LIVE_DAYS:.1f} days (~{f(sk['undelegated_week']/LIVE_DAYS*7)}/week, from ~86,000/week in runs #31-#32), the largest under 3,000. "
     f"Delegation TVL {sk['delta_locked']:+,.0f} (procryptostaking +8,101); delegators {sk['users_delta']:+d}. Compounding {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} vs {cvc['claim_count']}). The ninjastaking exiter's {f(NINJA['amount_egld'])} matures {NINJA_MATURES[:16]}, after this run."},
    {"category": "token", "severity": "low", "finding":
     f"USDC +{f(USDC_D)} ({usdc['pct']:+.2f}%) TO {f(usdc['supply'])}, A SECOND RISE. {f(UB_['wrap_usdc'])} USDC came in through the xBridge wrapper ({UB_['wrap_txs']} wraps, almost all via one bridge contract) and {f(UB_['unwrap_usdc'])} went out ({f(UB_['unwrap_by_destination_token'].get('BSCUSDC-887875',0))} to BSC). "
     f"The largest unwrapper (25,000) made no EGLD swap first. USDT {usdt['pct']:+.2f}%. xExchange volume {f(bid['dexvol_egld'])} EGLD/24h ({100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.0f}%), {bid['wegld_usdc_share']:.0f}% WEGLD/USDC."},
    {"category": "defi", "severity": "low", "finding":
     f"A BINANCE WITHDRAWAL WENT STRAIGHT INTO HATOM. {f(cust['hot_big_outbound'][0]['amount'] if cust['hot_big_outbound'] else 0)} EGLD left Binance.com on Oct 20 09:00 to a fresh wallet that supplied it to Hatom's EGLD money market six minutes later; the market rose {EMM_D:+,.0f} to {f(df['egld_mm_balance'])}. "
     f"The OTC desk relayed 5,302 EGLD from the run #19 Binance-side feeder to the Gate.io router in 24 minutes on Oct 22 02:20-02:44, after an 81 EGLD run #32: small, and not an UPbit reload."},
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
               "btc_correlation_note": f"BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%, EGLD {pc:+.2f}% over {LIVE_DAYS:.1f} days: EGLD {EGLD_VS_BTC:+.1f}pp vs BTC, the second window in a row EGLD did not trail BTC. Over the trailing 7 days (from the run #31 report) EGLD {P7_EGLD:+.1f}% vs BTC {P7_BTC:+.1f}% ({P7_REL:+.1f}pp)."},
    "liveness": {"ok": D["liveness_ok"], "latest_block_by_shard": {k: iso(v["timestamp"]) for k, v in D["liveness"].items()},
                 "restart_1_utc": iso(1790181300), "restart_1_stopped_utc": iso(1790182386), "restart_2_utc": iso(1790263800),
                 "live_days_in_window": LIVE_DAYS, "rollback_point_utc": "2026-09-19 06:37:45 UTC"},
    "analysis": (
        f"WINDOW. {WINDOW_NOTE} Every shard read within seconds of real time. Epoch {st['epoch']} ({st['epoch']-pact['epoch']:+d}), "
        f"{f(st['transactions']-pact['total_transactions'])} transactions (~{f(int((st['transactions']-pact['total_transactions'])/LIVE_DAYS))}/day), {f(st['accounts']-pact['total_accounts'])} new accounts. Total supply {f(econ['totalSupply'])} ({econ['totalSupply']-pecon['total_supply']:+,}).\n\n"
        f"STAKING. Staked EGLD {M['staked_chg']:+,.0f} to {f(econ['staked'])}; ratio {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp). Delegation TVL {sk['delta_locked']:+,.0f}: inflows outran a much smaller exit flow. "
        f"Binance's {f(BIN_UNDEL)} EGLD unbond matured {BIN_MATURES} and was withdrawn at {hm(BIN_WD_TS)} UTC, about two hours AFTER this run's /economics read, so the staked figure above still includes it. Binance sent it to custody rather than re-delegating, so expect staked to fall about 320,000 (~{100*BIN_UNDEL/econ['circulatingSupply']:.1f}pp of the ratio) at the run #34 read unless it is re-staked. Network APR {100*econ['apr']:.2f}%.\n\n"
        f"PRICE. EGLD ${price:.2f}, {pc:+.2f}% against BTC {M['btc_wow']:+.2f}% and ETH {M['eth_wow']:+.2f}%: a second window ahead of BTC. Hourly prices ran $3.58-$3.79 in the window (high on Oct 20), after an Oct 18 low near $3.51. "
        f"Binance bids within 2% of mid ${f(BOOK['binance']['depth_minus2_usd'])} (from ${f(BIN_BID_PREV)}), all venues ${f(BOOK['all']['depth_minus2_usd'])}. CEX spot volume over 7 days {f(BOOK['spot_volume_7d_egld']/1e6, 2)}M EGLD against {f(BOOK['spot_volume_prior_7d_egld']/1e6, 2)}M a week earlier. Binance's bid deepened ({100*(BOOK['binance']['depth_minus2_usd']-BIN_BID_PREV)/BIN_BID_PREV:+.0f}%) and Upbit carried {UP_SHARE:.0f}% of the last 24h's volume: the move was led by Korean trading, not by Binance buyers.")}


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


INV_SERIES = {**prev["otc_desk_inventory_series"], "run33": round(otc["desk_bal"])}
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
                        "note": f"Value-bearing EGLD transactions only (ESDT spam airdrops and exchange-internal sweeps excluded). {WIN_TXT}; rail window starts at run #32's stored rail end (14:40:28 UTC Oct 19). UPbit, KuCoin and Bitfinex moved no EGLD; MEXC sent one dust tx; Tokero took one 200 EGLD deposit. Crypto.com's two wallets exchanged 2,038 EGLD internally. The Binance de-staking wallet's 320,000 to Binance Staking custody is internal and excluded from the window totals. Web check: Upbit's caution review (Oct 19-23) had no published outcome on Oct 22.",
                        "rail_7d": {"start_utc": iso(R7_START), "days": R7_DAYS, "deposits_egld": R7_IN, "withdrawals_egld": R7_OUT, "net_egld": R7_NET,
                                    "cross_venue_deposits_egld": R7_ARB_IN, "cross_venue_withdrawals_egld": R7_ARB_OUT, "net_ex_cross_venue_egld": R7_NET_EX_ARB,
                                    "by_venue_net_egld": {k: v for k, v in R7_BY.items() if v}, "egld_change_pct": P7_EGLD, "btc_change_pct": P7_BTC, "egld_minus_btc_pp": P7_REL,
                                    "balance_basis_net_ex_cross_venue_egld": BAL7_EX_ARB}},
        "signal": (f"NET INFLOW, FASTER, ON A RISING PRICE. {len(OPEN)} tracked venues move EGLD both ways ({', '.join(OPEN)}). Net exchange balance change {ex['net']:+,.0f} EGLD over {LIVE_DAYS:.1f} days ({PACE_NOW:+,.0f}/day, against ~{PACE_PREV:+,.0f}/day in run #32): " + ", ".join(f"{e2['entity']} {e2['net_flow_egld']:+,.0f}" for e2 in ex["entity"] if e2["net_flow_egld"]) + ". "
                   f"The three cross-venue wallets were idle, so no netting adjustment applies. Half of Binance.com's deposits ({f(HHV_DEP)}) is one lot from erd1hhvfrw... through a fresh hop. "
                   f"TRAILING 7 DAYS (rails from {iso(R7_START)[:16]}, overlaps run #32): {R7_NET:+,.0f} raw, {R7_NET_EX_ARB:+,.0f} ex cross-venue, on EGLD {P7_EGLD:+.1f}% vs BTC {P7_BTC:+.1f}%; balance basis Oct 15 -> Oct 22 {BAL7_EX_ARB:+,.0f}. Exchange-flow and OTC series stay out of the weekly baselines (UPbit closed)."),
        "by_exchange": [{"exchange": w["exchange"], "change_egld": w["change_egld"], "pct": w["pct"]} for w in ex["per_wallet"]],
        "entity_netting": [{"entity": e2["entity"], "wallets_count": e2["wallets_count"],
                            "net_flow_egld": e2["net_flow_egld"], "interpretation": entity_interp(e2)} for e2 in ex["entity"]]},
    "dormant_activations": [],
    "exit_routes": {
        "route_this_run": "no delegator withdraw above 3,000 EGLD; Binance's 320,000 unbond went to Binance Staking custody (internal)",
        "route_previous_run": "no CEX exits; the one withdraw > 3,000 EGLD was re-delegated (ninjastaking exiter -> pi-staking)",
        "scan_threshold_egld": 3000, "scan_calls": EXS["calls"], "scan_by_route": EXR,
        "scan_rows": [{"sender": r_["sender"], "sender_label": r_["sender_label"], "provider": r_["provider"], "withdrawn_egld": r_["withdrawn_egld"],
                       "route": r_["route"], "balance_now_egld": r_["balance_now"]} for r_ in EXS["rows"]],
        "traced_egld_ex_internal": EXIT_TRACED, "traced_to_cex_egld": EXIT_CEX,
        "binance_undelegation": {"wallet": "erd1r3w62vqmsux5e38p6vnueatmfcs8nr5lmg3s97x6rafqpgxfae0sxv9z0v", "egld": BIN_UNDEL,
                                 "called_utc": "2026-10-12 06:16 UTC", "unbonds_in_days": BIN_UNDEL_DAYS, "matures_utc": BIN_MATURES,
                                 "status": f"WITHDRAWN {hm(BIN_WD_TS)} UTC and sent {f(BIN_TO_CUST)} to Binance Staking custody (erd1rf4hv70...) at {hm(BIN_SEND_TS)} UTC; custody now {f(CUST_NOW)}. Not re-delegated at the trace. binance-undelegation-destination resolved: re-allocation."},
        "binance_hot_to_custody_egld": 0.0,
        "largest_new_undelegation": {"wallet": NINJA["wallet"], "provider": "ninjastaking", "egld": NINJA["amount_egld"],
                                     "unbonds_in_days": NINJA["days_remaining"], "wallet_balance_egld": NINJA["wallet_balance_egld"],
                                     "note": f"carried from run #31; matures {NINJA_MATURES[:16]} (about {NINJA['days_remaining']:.1f} days after the trace). Wallet balance {f(NINJA['wallet_balance_egld'], 1)} EGLD and active stake {f(NINJA['active_stake_egld'])} (the 5,000 re-delegated to pi-staking on Oct 18); no new legs in the window."},
        "note": (f"Collector-side scan of every delegator withdraw call above 3,000 EGLD in the window: {EXS['calls']} calls. {O['withdraw_calls']} withdraw calls (from {O['prev_withdraw_calls']}) returned {f(WD.get('egld_returned_total', 0))} EGLD, the largest {f(wd_top0)} from orius. "
                 f"Binance's {f(BIN_UNDEL)} unbond (matured {BIN_MATURES}) went to Binance Staking custody, not the hot wallet. One large item is pending: erd1me5hmqt5qg...'s {f(NINJA['amount_egld'])} from ninjastaking ({NINJA_MATURES[:16]}). One of that wallet's older legs (1,000 EGLD on Oct 18) reached Binance.com through a fresh wallet; a further 1,000 went to an xExchange swap.")},
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
        "method_note": f"Seventh read after restart; invalid balances {HR['invalid_total_egld']:.2f} EGLD, unchanged."},
    "otc_pipeline": {
        "gross_outbound_egld_7d": otc["gross_out"], "gross_inbound_egld_7d": otc["gross_in"],
        "circular_egld_7d": otc["circular"], "net_one_way_egld_7d": otc["net_one_way"],
        "circular_share_pct": otc["circ_pct"],
        "desk_balance_egld": otc["desk_bal"], "previous_desk_balance_egld": otc["prev_desk"],
        "upbit_reload_egld": otc["upbit_feed"],
        "venue_netting": [],
        "router_tail_delivery_egld": 0.0, "router_tail_routers": 0,
        "gross_series_egld_7d": {**r26o["gross_series_egld_7d"], "run33": otc["gross_out"]},
        "net_one_way_series_egld_7d": {**r26o["net_one_way_series_egld_7d"], "run33": otc["net_one_way"]},
        "desk_inventory_series_egld": INV_SERIES,
        "circularity_series_pct": {**r26o["circularity_series_pct"], "run33": 0.0},
        "peak_window_renetted": r26o["peak_window_renetted"],
        "backfilled_windows": r26o.get("backfilled_windows", []),
        "wave_window_netting": {**r26o["wave_window_netting"],
            "note": f"Wave #4 stays closed at 467,107 EGLD one-way (Sep 7 to the halt, frozen labels). The post-restart window (Sep 24 - Oct 22) nets {f(otc['wave']['net_one_way'])} EGLD one-way."},
        "feed_by_parent_venue": [],
        "feeder_backtrace": O["feeder_backtrace"],
        "address_poisoning": [{"address": a, "mimics": v["note"], "nonce": v["nonce"], "dust_txs_30d": v["dust_txs_30d"],
                               "distinct_targets_30d": v["distinct_targets_30d"],
                               "inbound_above_0_01_egld": len(v["inbound_above_0_01_egld"])} for a, v in PZ.items()],
        "desk_terminal_resolved": {"address": TERM["address"], "nonce": TERM["info"].get("nonce"), "balance_egld": TERM_BAL, "role": "holder (nonce 1, no value sent)"},
        "series_note": (f"ONE RELAY, {LIVE_DAYS:.1f}-DAY WINDOW. Gross out {f(otc['gross_out'])} EGLD: the OTC Distribution Wallet took 5,302 from the run #19 Binance.com -> desk feeder at 02:20 UTC Oct 22 and passed it to the run #22 Gate.io router at 02:44; the UPbit desk sent 38 EGLD to an unlabelled wallet. No UPbit reload (UPbit's hot wallet had no EGLD flow). "
                        f"The Oct 6 terminal erd1y27r22... still holds {f(TERM_BAL, 1)} EGLD. Desks {f(otc['desk_bal'])}.")},
    "demand_instruments": {
        "identifiable_bid_absorbed_egld_7d": 0.0, "mega_whale_otc_leg_egld": MEGA_IN,
        "mega_whale_balance_egld": bid["mega_bal"] or 0.0, "mega_whale_change_egld": bid["mega_delta"],
        "coinbase_routing_balance_egld": bid["cbr_bal"] or 0.0, "coinbase_routing_inflow_egld": 0.0,
        "coinbase_routing_funder": "erd1m9qn6gvercs6ksvtn924w4y7z9ppglyfugpu34al26t9u4mvzvqqlq9dc3", "coinbase_routing_funder_label": "Coinbase (secondary); idle toward the routing wallet. Whale B and the Mega Whale did not move",
        "weeks_at_zero": 13, "weeks_at_zero_in_last_four": 4, "bid_to_distribution_ratio_pct": 0.0,
        "dex_turnover_ratio_pct": bid["turnover"], "previous_dex_turnover_ratio_pct": bid["prev_turnover"],
        "dex_volume_egld_24h": bid["dexvol_egld"], "previous_dex_volume_egld_24h": bid["prev_dexvol_egld"],
        "pool_tvl_egld": bid["pooltvl_egld"], "previous_pool_tvl_egld": bid["prev_pooltvl_egld"],
        "wegld_usdc_volume_usd": bid["wegld_usdc_vol"], "wegld_usdc_share_of_volume_pct": bid["wegld_usdc_share"],
        "ex_wegld_usdc_volume_usd": bid["ex_wegld_usdc_vol"], "ex_wegld_usdc_volume_egld": bid["ex_wegld_usdc_vol_egld"],
        "dex_volume_status": "evaluable; compared with run #32",
        "absorber_scan": {"terminals_scanned": absb["scanned"],
                          "terminals_retaining_over_half": len(absb["retaining"]),
                          "total_received_from_desks_egld": absb["total_received"],
                          "total_retained_egld": absb["total_balance_held"],
                          "retained_share_pct": 0.0,
                          "verdict": f"Desk outbound {f(otc['gross_out'])} EGLD (one Binance -> Gate.io relay and one small payment); the instrument stays retired. The Mega Whale did not move."},
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
    f"RAILS. Value-bearing EGLD per tracked exchange wallet, {WIN_TXT} (rails to the {hm(D['_period']['rail_window_end_ts'])} pass): "
    + "; ".join(f"{k}: {v['state'].replace('_', ' ')} ({v['in_txs']} in / {v['out_txs']} out)" for k, v in VEN.items() if v["state"] != "closed" and k not in _NONVENUE_INTERNAL)
    + f". No EGLD moved: {', '.join(k for k, v in VEN.items() if v['state'] == 'closed')}. Venue deposits {f(RAIL_EGLD_IN)}, withdrawals {f(RAIL_EGLD_OUT)} (net {RAIL_EGLD_IN-RAIL_EGLD_OUT:+,.0f}; the balance basis, which stops at the 07:28 read, is {ex['net']:+,.0f}).\n\n"
    f"BINANCE'S UNBOND (run #32 rec #1). The de-staking wallet erd1r3w62vq... called withdraw on Binance's staking contract at {hm(BIN_WD_TS)} UTC and sent {f(BIN_TO_CUST)} EGLD to Binance Staking custody erd1rf4hv70... at {hm(BIN_SEND_TS)}; nothing went to the Binance.com hot wallet, and custody did not pass it on before the trace (balance {f(CUST_NOW)}). "
    f"In run #30 the same custody wallet had received 161,137 from the hot wallet; Binance is consolidating staked EGLD into custody, not selling it.\n\n"
    f"TRAILING 7 DAYS. Rails from {iso(R7_START)[:16]} ({R7_DAYS:.1f} days, overlapping run #32 by about four days; internal Binance staking moves excluded): deposits {f(R7_IN)}, withdrawals {f(R7_OUT)}, net {R7_NET:+,.0f}; cross-venue wallets (run #32's Oct 16 legs) {f(R7_ARB_IN)} in / {f(R7_ARB_OUT)} out, so {R7_NET_EX_ARB:+,.0f} ex cross-venue. By venue: " + ", ".join(f"{k} {v:+,.0f}" for k, v in sorted(R7_BY.items(), key=lambda kv: -abs(kv[1])) if abs(v) >= 500)
    + f". EGLD {P7_EGLD:+.1f}% and BTC {P7_BTC:+.1f}% over the same days. On the balance basis Oct 15 09:08 -> Oct 22 07:28 the net is {BAL7_EX_ARB:+,.0f}.\n\n"
    f"BINANCE.COM. Per day since the Oct 9 reopening (deposits / withdrawals, EGLD, raw; Oct 12 includes the 161,137 internal custody send): " + "; ".join(f"{d_[5:]}: {f(v_['dep_egld'])} / {f(v_['wd_egld'])}" for d_, v_ in BD.items())
    + f". In this window {f(BIN_DEP)} in and {f(BIN_WD_EXT)} out ({BIN_EXT_PER_DAY:+,.0f}/day). The largest deposit, {f(HHV_DEP)} at 21:35 UTC Oct 20, came from erd1hhvfrw... through erd1rcty49... (nonce 2): a 6 EGLD test at 21:18, 24,994 at 21:26, deposit nine minutes later. "
    f"Same seller as run #32's 12,223 lot (hop erd1rgm4td29...), twice the size, again via a wallet used once. erd1hhvfrw... itself is an operational wallet (nonce 9,000) refilled every 30-60 minutes in 200-700 EGLD clips by erd1079hvt0..., which is funded by Unknown Whale erd1hl5y4a... (220,695 EGLD). "
    f"Next largest: erd15k0p5m... 4,000 and erd13tpyjr... 2,500, each funded one hop earlier by an unlabelled wallet. The drip route erd137cw9q46... -> Binance.com carried {f(sum(x['egld'] for x in TR['binance_depositors'][2]['deposits']) if len(TR.get('binance_depositors', [])) > 2 else 0)} EGLD in five clips, funded by erd1hl5y4a..., the drip seller and Coinbase withdrawals. "
    f"Withdrawals: 10,004 to a fresh wallet that supplied Hatom's EGLD market six minutes later (Oct 20), and 6,624 to erd1rlqdj67... (held).\n\n"
    f"CROSS-VENUE WALLETS. erd1d2anjjha..., erd13sytuz92... and erd1reh7sy2c... moved nothing in the window; all three sit at zero.\n\n"
    f"COINBASE AND WHALE B. Whale B ({f(WB['balance_egld'])}), the Mega Whale ({f(CBL['mega']['balance_egld'])}) and the routing wallet ({f(CBL['cb_routing']['balance_egld'],1)}) did not move. Coinbase's entity net {ent_net('Coinbase'):+,.0f}: the secondary wallet paid out 4,864 in 27 withdrawals, several to erd1ukxuufpk..., which then deposited 3,254 at Binance.com in four clips (Coinbase -> Binance migration by a retail-sized seller).\n\n"
    f"WHALES. Tiers on the common-address basis ({O['tiers_basis']} wallets): mega {O['tiers']['mega']['net_change_egld']:+,.0f} (no mega whale moved), large {O['tiers']['large']['net_change_egld']:+,.0f} (Binance.com +20,003, Bybit +5,591, the two growth funds +4,264 each), mid {O['tiers']['mid']['net_change_egld']:+,.0f} (erd1hhvfrw... -25,011, Coinbase secondary -4,294, Gate.io -3,050, against erd1rlqdj67... +6,624 and Hatom's EGLD market +4,976). No tier crossings. "
    f"Unknown Whale I: {CEN['Unknown Whale I']['inbound_txs']} inbound. erd1a6lte0: {CEN['erd1a6lte0']['inbound_txs']} inbound.\n\n"
    f"DEMAND. Binance+Bybit bids within 2% of mid total ${f(bbn)} (closed-book base ${f(bbn_prev)}); Binance's own bid ${f(BOOK['binance']['depth_minus2_usd'])} from ${f(BIN_BID_PREV)}. Upbit's premium {PREM:.1f}% (from {PREM_PREV:.1f}%) on {UP_SHARE:.0f}% of global 24h volume (from {UPSH_PREV:.0f}%), plus Bithumb about $1.0M, mid-way through its Oct 19-23 review with no outcome published.")
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
                   "note": f"TENTH WEEK AFTER THE FEE REVERSAL ({LIVE_DAYS:.1f}-day window): book {mv(ident,'delta'):+,.0f}, users {mv(ident,'users_delta'):+d}."})
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
                          "note": f"Zero transitions for a tenth week. Join on contract address, {100*(sk['join_match_rate'] or 0):.0f}% match, no identity changes."},
    "fee_events": [{"provider": i, "fee_from_pct": 100.0, "fee_to_pct": mv(i, "fee") or 0.0, "apr_from_pct": 0.0, "apr_to_pct": mv(i, "apr") or 0.0,
                    "locked_egld": mv(i, "locked"), "locked_wow_egld": mv(i, "delta"), "users": mv(i, "users"),
                    "users_wow": mv(i, "users_delta"), "num_nodes": mv(i, "nodes")} for i in ("egldstakingprovider", "procryptostaking")],
    "unbonding_in_flight": {
        "wallet": ub["wallet"], "total_egld": ub["pending_total"],
        "legs": [{"provider": p["contract"][:10] + "..." + p["contract"][-8:], "amount": p["amount_egld"],
                  "days_to_unbond": p["days_remaining"], "date": "2026-08-14" if p["amount_egld"] < 100000 else "2026-08-15"} for p in ub["pending"]],
        "share_of_delegation_decline_pct": 0.0, "raw_residual_egld": sk["residual"], "corrected_direct_node_egld": None,
        "status": f"RETIRED, ELEVENTH WEEK UNMOVED. Balance {f(ub['balance'],2)} EGLD, {f(ub['pending_total'])} unbonded-and-unclaimed.",
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
            f"COMPOUND RATE {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} reDelegateRewards vs {cvc['claim_count']} claimRewards), from 60.93%. Series: 49.44 / 62.68 / 52.40 / 58.28 / 60.85 / 59.38 / 59.40 / 60.93 / {cvc['compound_pct_of_reward_decisions']:.2f}. Inside the 57-63% range for a seventh run.",
            f"Retail {fates['retail']['total_events']} claims, {fates['retail']['by_count'].get('sold',0)} to a labelled exchange; mid-tier {fates['mid_tier']['total_events']}, {fates['mid_tier']['by_count'].get('sold',0)} sold; institutional {fates.get('institutional',{}).get('total_events',0)}, {fates.get('institutional',{}).get('by_count',{}).get('sold',0)} sold (too few to read).",
            f"Sample: {ag['providers_sampled']} of {ag.get('providers_requested',8)} providers, 7-day delegator window (overlaps run #32's by about four days).",
            "PROVIDER OPERATORS DID NOT SELL FEES for a twentieth consecutive run (destinations: DeFi deposits, held, rotated)."]},
    "analysis": (
        f"EXITS DRIED UP. {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD in {LIVE_DAYS:.1f} days across {sk['providers_scanned']} provider contracts with activity, about {f(sk['undelegated_week']/LIVE_DAYS*7)} a week, against ~86,000 in runs #31 and #32 and ~54,000 in run #30. "
        f"The largest single exit was 1,000 EGLD (erd15mymvg3d...), then 934 and 729: retail-sized only. Measured pending among the window's callers: {f(sk['pool_total'])} EGLD. Read with the price: exits fell away in the window EGLD outperformed BTC.\n\n"
        f"WITHDRAWALS FELL. {O['withdraw_calls']} withdraw calls (from {O['prev_withdraw_calls']}) returned {f(WD.get('egld_returned_total',0))} EGLD, led by orius ({f(wd_top0)}); none above 3,000. Binance's {f(BIN_UNDEL)} unbond matured {BIN_MATURES} and went to custody (Whale Intelligence). Still queued: the ninjastaking exiter's {f(NINJA['amount_egld'])} ({NINJA_MATURES[:16]}).\n\n"
        f"THE RATIO AND THE RESIDUAL. Delegation TVL {sk['delta_locked']:+,.0f} to {f(tl)} while /economics staked moved {M['staked_chg']:+,.0f}. Ratio {100*M['sr']:.2f}%, read before Binance's withdraw; the ~320,000 leaves 'staked' at the next read. HHI {sk['hhi']:.5f} (from {sk['prev_hhi']:.5f}). 75 of 102 APR-bearing providers sit in the 8-9% bucket; stakenest and pokerstaking (9.60%, 0% fee) and pi-staking (9.59%, 0% fee) are the best headline deals.\n\n"
        f"COMPOUNDING {cvc['compound_pct_of_reward_decisions']:.2f}%. DELEGATORS {sk['users_delta']:+,} to {f(sk['users'])}; {sk['gaining']} providers gained and {sk['losing']} lost. procryptostaking led inflows ({mv('procryptostaking','delta'):+,.0f}, one of the two fee-reversal providers; +1 delegator, so one or two large deposits), then oxsyai ({mv('oxsyai','delta'):+,.0f}) and pi-staking ({mv('pi-staking','delta'):+,.0f}); outflows were small (MrEGLD {mv('MrEGLD','delta'):+,.0f}, stakingagency {mv('stakingagency','delta'):+,.0f}). binance_staking {BINP['delta']:+,.0f} to {f(BINP['locked'])}. Zero deregistration transitions for a tenth week.")}
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
        "volume_status": "evaluable; compared with run #32 (24h snapshots)",
        "mex_pair_depth": {"pair": "MEX/WEGLD", "tvl_usd": xx["mex_pair_depth"]["tvl_usd"], "tvl_egld": xx["mex_pair_depth"]["tvl_egld"],
                           "previous_tvl_egld": xx["mex_pair_depth"]["previous_tvl_egld"], "tvl_egld_wow_pct": xx["mex_pair_depth"]["tvl_egld_wow_pct"],
                           "volume_24h_usd": xx["mex_pair_depth"]["volume_24h_usd"], "trades_24h": xx["mex_pair_depth"]["trades_24h"],
                           "share_of_pool_tvl_pct": xx["mex_pair_depth"]["share_of_pool_tvl_pct"], "depth_rank": xx["mex_pair_depth"]["depth_rank"]},
        "mex_pair_event": r26["token_activity"]["xexchange"]["mex_pair_event"]},
    "analysis": (
        f"DEX VOLUME RECOVERED PART OF ITS DROP. 24h volume ${f(xx['vol'])} ({f(bid['dexvol_egld'])} EGLD) against ${f(xx['prev_vol'])} ({f(bid['prev_dexvol_egld'])} EGLD) at the last snapshot, {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.0f}% in EGLD. "
        f"WEGLD/USDC is {bid['wegld_usdc_share']:.0f}% of it: the venue is effectively one EGLD/dollar pool arbitraged against the exchanges; everything else traded ${f(bid['ex_wegld_usdc_vol'])}. Turnover {bid['turnover']:.2f}% of pool TVL (from {bid['prev_turnover']:.2f}%). Pool TVL {f(bid['pooltvl_egld'])} EGLD ({100*(bid['pooltvl_egld']-bid['prev_pooltvl_egld'])/bid['prev_pooltvl_egld']:+.1f}% in EGLD), ${f(bid['pooltvl'])} ({100*(bid['pooltvl']-bid['prev_pooltvl'])/bid['prev_pooltvl']:+.1f}%) in dollars.\n\n"
        f"MEX ${xx['mex_price']:.2e} ({xx['mex_wow']:+.1f}% over the window, against EGLD {pc:+.1f}%); MEX/WEGLD depth ${f(xx['mex_pair_depth']['tvl_usd'])} ({xx['mex_pair_depth']['tvl_egld_wow_pct']:+.1f}% in EGLD), rank {xx['mex_pair_depth']['depth_rank']}.\n\n"
        f"STABLECOINS. USDC {usdc['pct']:+.2f}% ({USDC_D:+,.0f}) to {f(usdc['supply'])}, a second rise after three declines. Traced through the xBridge Tokens Wrapper: {UB_['wrap_txs']} wraps brought in {f(UB_['wrap_usdc'])} USDC and {UB_['unwrap_txs']} unwraps sent {f(UB_['unwrap_usdc'])} out, {f(UB_['unwrap_by_destination_token'].get('BSCUSDC-887875',0))} of it to BSC and {f(UB_['unwrap_by_destination_token'].get('ETHUSDC-220753',0))} to Ethereum; net {USDC_NET_IN:+,.0f} against a {USDC_D:+,.0f} supply change. Almost all wraps ({f(list(UB_['top_wrappers'].values())[0]['usdc'])} in {list(UB_['top_wrappers'].values())[0]['n']}) came through one contract, the bridge's own entry path, so the inflow is many bridge users, not one wallet. "
        f"The largest unwrapper (erd1ml0p4c5k..., {f(list(UB_['top_unwrappers'].values())[0]['usdc'])} USDC in one call) made no EGLD swap and received nothing from an exchange in the prior 7 days. USDT {usdt['pct']:+.2f}% to {f(usdt['supply'])}. "
        f"NEWLY ISSUED: {len(newly)} issuances in the window ({', '.join(t['identifier'] for t in newly)}), below the traction bar.")}
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
         "notable_events": f"{f(es('VOXEGLD-5872e5'))} EGLD, supply {(em['VOXEGLD-5872e5']['pct'] or 0):+.1f}%, holders {em['VOXEGLD-5872e5']['holders']}.", "health_signal": hs(ep("VOXEGLD-5872e5"))},
        {"protocol": "VestaX Finance", "category": "liquid_staking", "addresses_tracked": 1, "tvl_usd": (es("VEGLD-2b9319") or 0) * price, "tvl_egld": es("VEGLD-2b9319") or 0.0,
         "tvl_wow_change_pct": ep("VEGLD-2b9319"), "transfers_24h": None,
         "notable_events": f"{f(es('VEGLD-2b9319'))} EGLD.", "health_signal": hs(ep("VEGLD-2b9319"))}],
    "sc_deployments": [],
    "analysis": (
        f"HATOM'S EGLD MARKET GREW, FED FROM BINANCE. The EGLD money market holds {f(df['egld_mm_balance'])} EGLD, from {f(df['egld_mm_prev_balance'])} ({EMM_D:+,.0f}); HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.2f}%. "
        f"Most of it is one deposit: 10,004 EGLD withdrawn from Binance.com on Oct 20 09:00 went through a fresh wallet and was supplied as collateral six minutes later, i.e. EGLD bought or held on Binance and posted as collateral. "
        f"Calls in the window: {HMM['by_function'].get('mintAndEnterMarket',{}).get('n',0)} supply-and-collateral calls from {HMM['by_function'].get('mintAndEnterMarket',{}).get('distinct_senders',0)} wallets, {HMM['by_function'].get('repayBorrow',{}).get('n',0)} repayments from {HMM['by_function'].get('repayBorrow',{}).get('distinct_senders',0)}, {HMM['by_function'].get('borrow',{}).get('n',0)} borrows from {HMM['by_function'].get('borrow',{}).get('distinct_senders',0)}, {HMM['redeem_calls']} redeems, {HMM['liquidation_calls']} liquidations. Collateral is being added on a rising price; no forced selling.\n\n"
        f"INVERSE-RATIO RULE. Aggregate lending TVL ex-HMEX reads {hl:+.2f}% in EGLD on a {pc:+.2f}% price move, so the EGLD-denominated rise is not the price mechanism (EGLD rose, which would lower it); it is HEGLD {HT['HEGLD-d61095']['supply_pct']:+.2f}%, HUSDC {HT['HUSDC-d80042']['supply_pct']:+.2f}% and HWETH {HT['HWETH-b3d17e']['supply_pct']:+.2f}% against HUSDT {HT['HUSDT-6f0914']['supply_pct']:+.2f}%: real deposits.\n\n"
        f"LIQUID STAKING. SEGLD {lsd['SEGLD-3ad2d0']['pct']:+.2f}%, XEGLD {lsd['XEGLD-e413ed']['pct']:+.2f}%, SWTAO {lsd['SWTAO-356a25']['pct']:+.2f}%, USH {lsd['USH-111e09']['pct']:+.2f}%: flat. Emerging LSDs: VoxEGLD {(em['VOXEGLD-5872e5']['pct'] or 0):+.1f}%, LEGLD {(em['LEGLD-d74da9']['pct'] or 0):+.1f}%, JWLEGLD and VEGLD unchanged.\n\n"
        f"ACTIVITY. XOXNO aggregator {f(cnt('XOXNO Aggregator'))} transfers in 24h, OneDex {f(cnt('OneDex Swap'))}, Hatom LSD {f(cnt('Hatom Liquid Staking'))}. JEXchange router transfers over 7 days {f(jex7.get('JEXchange Router'))} on the main router.")}

# ---------------------------------------------------------------------------
R["anomalies"] = [
    {"metric": "upbit_share_of_global_volume_pct", "current_value": UP_SHARE, "previous_value": UPSH_PREV, "method": "rule_based", "severity": "medium",
     "change_pct": 100 * (UP_SHARE - UPSH_PREV) / UPSH_PREV,
     "description": f"Upbit {UP_SHARE:.0f}% of global 24h EGLD volume (${up['converted_volume']['usd']/1e6:.2f}M), from {UPSH_PREV:.0f}%; Bithumb another ~$1.0M; premium {PREM:.1f}% (from {PREM_PREV:.1f}%). UPbit's wallet moved no EGLD, so this is trading inside a closed venue during its Oct 19-23 caution review: positioning on the decision. Rule-based: no weekly baseline for this share."},
    {"metric": "binance_unbond_to_custody_egld", "current_value": BIN_TO_CUST, "previous_value": None, "method": "rule_based", "severity": "medium",
     "change_pct": None,
     "description": f"Binance's matured unbond withdrawn and sent whole to Binance Staking custody ({BIN_TO_CUST_PCT:.0f}%); resolves binance-undelegation-destination as predicted. Staked EGLD should step down ~320,000 at the next /economics read."},
    {"metric": "egld_price_usd", "current_value": price, "previous_value": M["prev_price"], "method": "z_score", "severity": z["price"].get("severity", "low"),
     "average_value": z["price"].get("mean"), "stddev": z["price"].get("stddev"), "z_score": zz("price"), "change_pct": pc,
     "description": f"{pc:+.2f}% in {LIVE_DAYS:.1f} days (BTC {M['btc_wow']:+.2f}%); z={zz('price'):+.2f} against a baseline that still holds the pre-halt $4+ prices. Second window in a row ahead of BTC."},
    {"metric": "undelegation_pace_egld_per_week", "current_value": sk["undelegated_week"] / LIVE_DAYS * 7, "previous_value": 86074.0, "method": "percent_threshold", "severity": "low",
     "change_pct": 100 * (sk["undelegated_week"] / LIVE_DAYS * 7 - 86074.0) / 86074.0,
     "description": f"~{f(sk['undelegated_week']/LIVE_DAYS*7)}/week from ~86,074 (degraded mode: short-window readings are not in the weekly baseline). Largest single exit 1,000 EGLD."},
    {"metric": "binance_single_deposit_via_fresh_hop", "current_value": HHV_DEP, "previous_value": 12223.0, "method": "rule_based", "severity": "low",
     "change_pct": 100 * (HHV_DEP - 12223.0) / 12223.0,
     "description": f"{f(HHV_DEP)} EGLD from labelled Binance funder erd1hhvfrw... through a new wallet (nonce 2, test send first), deposited nine minutes after funding. Second such hop in two runs (run #32: 12,223). Half of Binance.com's deposits in the window."},
    {"metric": "dex_volume_24h_egld", "current_value": bid["dexvol_egld"], "previous_value": bid["prev_dexvol_egld"], "method": "z_score", "severity": z["dexvol"].get("severity", "low"),
     "average_value": z["dexvol"].get("mean"), "stddev": z["dexvol"].get("stddev"), "z_score": zz("dexvol"),
     "change_pct": 100 * (bid["dexvol_egld"] - bid["prev_dexvol_egld"]) / bid["prev_dexvol_egld"],
     "description": f"xExchange 24h volume {f(bid['dexvol_egld'])} EGLD ({100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.0f}%), {bid['wegld_usdc_share']:.0f}% WEGLD/USDC; turnover {bid['turnover']:.2f}% from {bid['prev_turnover']:.2f}%. z in dollars {zz('dexvol'):+.2f}: inside the band."},
    {"metric": "usdc_supply", "current_value": usdc["supply"], "previous_value": usdc["prev"], "method": "rule_based", "severity": "low",
     "change_pct": usdc["pct"],
     "description": f"USDC {USDC_D:+,.0f}, a second rise; wrapper net {USDC_NET_IN:+,.0f} (in {f(UB_['wrap_usdc'])}, out {f(UB_['unwrap_usdc'])}, mostly to BSC)."},
]

R["trend_indicators"] = {
    "accelerating_exchange_outflows": [],
    "validator_movements": {"providers_joining": 0, "providers_leaving": 0, "net_provider_change": 0, "notable_joiners": [],
                            "notable_leavers": [], "note": "No joins or deregistrations for a tenth week."},
    "token_supply_events": [
        {"identifier": "USDC-c76f1f", "name": "WrappedUSDC", "event": "mint", "supply_previous": str(int(usdc["prev"])), "supply_current": str(int(usdc["supply"])),
         "change_pct": usdc["pct"], "description": f"{USDC_D:+,.0f} USDC: bridge inflow {f(UB_['wrap_usdc'])} exceeded outflow {f(UB_['unwrap_usdc'])}. Second rise in a row."},
        {"identifier": "USDT-f8c08c", "name": "USDT", "event": "mint", "supply_previous": str(int(usdt["prev"])), "supply_current": str(int(usdt["supply"])),
         "change_pct": usdt["pct"], "description": f"{f(usdt['supply']-usdt['prev'])} USDT added."}],
    "consecutive_streaks": [
        {"metric": "exchange_net_inflow_since_reopening", "direction": "up", "weeks": 6, "cumulative_change_pct": None,
         "interpretation": f"Tracked exchanges took net deposits in every window since the rails reopened (runs #28-#33; this one {ex['net']:+,.0f}, ~{PACE_NOW:,.0f}/day against ~{PACE_PREV:,.0f}/day in run #32). Half of it is one seller's hop deposit."},
        {"metric": "egld_vs_btc", "direction": "up", "weeks": 2, "cumulative_change_pct": None,
         "interpretation": f"Second window ahead of BTC: {EGLD_VS_BTC:+.1f}pp (run #32 +0.4pp); trailing 7 days {P7_REL:+.1f}pp."},
        {"metric": "usdc_supply", "direction": "up", "weeks": 2, "cumulative_change_pct": None, "interpretation": f"Two rises (+28,384, {USDC_D:+,.0f}) after three declines, both bridge-led."},
        {"metric": "total_delegators", "direction": "flat", "weeks": 21, "cumulative_change_pct": -1.2, "interpretation": f"{sk['users_delta']:+,} to {f(sk['users'])}. The base rate."},
        {"metric": "provider_operator_fee_selling", "direction": "flat", "weeks": 21, "cumulative_change_pct": 0.0, "interpretation": "Twenty-one runs with zero exchange destinations from sampled operator wallets."}],
    "regime_shifts": [
        {"metric": "exchange_rail_state", "before_value": 0.0, "after_value": round(len(OPEN) / max(1, len([k for k in VEN if k not in _NONVENUE])), 2),
         "description": f"{len(OPEN)} of {len([k for k in VEN if k not in _NONVENUE])} tracked venues move EGLD both ways ({', '.join(OPEN)}). Bitget is withdrawal-only (its 22 receives total about 1 EGLD of dust). UPbit had no EGLD flow. Promote when UPbit opens both ways."},
        {"metric": "binance_staking_allocation", "before_value": 399100.0, "after_value": BINP["locked"],
         "description": f"PROMOTED (binance-undelegation-destination, as predicted): the {f(BIN_UNDEL)} EGLD left delegation for Binance Staking custody (now {f(CUST_NOW)}), not the hot wallet. Binance's delegated book stays near {f(BINP['locked'])}."},
        {"metric": "rails_reopened_price_path", "before_value": 4.60, "after_value": price,
         "description": f"reopening-supply-overhang resolved in run #32. Since then EGLD has led BTC for two windows ({EGLD_VS_BTC:+.1f}pp this one) while exchange inflow continued; overhang-absorbed resolves on its own 7-day window (Oct 19 14:40 -> Oct 26)."}]}

R["watch_list"] = [
    {"item": "UPBIT CAUTION REVIEW Oct 19-23", "weeks_on_list": 7,
     "reason": f"No outcome published by Oct 22. Upbit traded {UP_SHARE:.0f}% of global 24h volume (from {UPSH_PREV:.0f}%) at a {PREM:.1f}% premium; UPbit's wallet moved no EGLD. A delisting retires korea-premium-arbitrage and delivery-price-relevance-2; a lifted caution with deposits reopened starts the >= 20-depositor premium test."},
    {"item": "EXCHANGE NET INFLOW - ABSORBED?", "weeks_on_list": 3,
     "reason": f"Inflow sped up to ~{PACE_NOW:,.0f}/day while EGLD led BTC by {EGLD_VS_BTC:+.1f}pp. Interim trailing-7d reading '{ABSORBED_INTERIM}' ({R7_NET_EX_ARB:+,.0f}, {P7_REL:+.1f}pp). PRE-COMMITTED (overhang-absorbed): its window Oct 19 14:40 -> Oct 26 resolves at run #34."},
    {"item": f"NINJASTAKING EXITER - {f(NINJA['amount_egld'])} EGLD matures {NINJA_MATURES[:16]}", "weeks_on_list": 3,
     "reason": f"Not yet withdrawable at the trace. Of its earlier legs, 5,000 was re-delegated (pi-staking) and 1,000 reached Binance.com through a fresh wallet. PRE-COMMITTED (ninjastaking-exit-destination): evaluate within 3 days of the withdraw, run #34."},
    {"item": "ERD1HHVFRW - BINANCE FUNDER USING FRESH HOPS", "weeks_on_list": 2,
     "reason": f"Second one-shot hop in two runs: {f(HHV_DEP)} via erd1rcty49... (Oct 20) after 12,223 via erd1rgm4td29... (Oct 19). Refilled in clips from erd1079hvt0... / Unknown Whale erd1hl5y4a... (220,695 EGLD), so the supply behind it is large."},
    {"item": "BINANCE STAKING CUSTODY", "weeks_on_list": 1,
     "reason": f"Now {f(CUST_NOW)} EGLD after the 320,000 return. Watch for re-delegation (staked back up) or a hot-wallet send (would reopen the supply question)."},
    {"item": "BINANCE -> HATOM COLLATERAL", "weeks_on_list": 1,
     "reason": f"10,004 EGLD withdrawn from Binance.com and supplied to Hatom's EGLD market within six minutes (Oct 20). Track whether more exchange withdrawals land as collateral."},
    {"item": "WHALE B / COINBASE", "weeks_on_list": 4,
     "reason": f"Idle (balance {f(WB['balance_egld'])}); Mega Whale idle ({f(CBL['mega']['balance_egld'])}). Drop next run if still idle."},
    {"item": "CROSS-VENUE WALLETS", "weeks_on_list": 4,
     "reason": "erd1d2anjjha..., erd13sytuz92... and erd1reh7sy2c... idle this window. Keep netting them out when they move."},
    {"item": "DRIP SELLER INTO BINANCE", "weeks_on_list": 3,
     "reason": f"erd1vadknqe8... / erd1hl5y4a... -> erd137cw9q46... -> Binance.com; {f(TR['binance_funders']['erd137cw9q']['to_binance_egld'])} this window in five clips."},
    {"item": "OTC PIPELINE", "weeks_on_list": 33,
     "reason": f"One Binance-feeder -> Gate.io relay (5,302); gross {f(otc['gross_out'])}, desks {f(otc['desk_bal'])}. Keep until Upbit's decision."},
    {"item": "EXPLOIT WALLET AND POISONING RING", "weeks_on_list": 8,
     "reason": f"Incident addresses hold {HR['invalid_total_egld']:.2f} EGLD; poisoning operator {PR['operator_out_7d']} dust txs in the window (page cap hit), zero hits above dust."},
]

# ---------------------------------------------------------------------------
prior = {t["id"]: t for t in r26["pre_committed_tests"]}
tests = [t for t in r26["pre_committed_tests"] if t["status"] == "resolved"]


def resolve(tid, outcome, measured, resolution):
    t = dict(prior[tid]); t.update({"status": "resolved", "outcome": outcome, "resolved_in_run": 33, "measured_value": measured, "resolution": resolution}); return t


BIN_HOT_PCT = 0.0
tests.append(resolve("binance-undelegation-destination",
    "as_predicted" if BIN_TO_CUST_PCT > 70 else ("contradicted" if BIN_HOT_PCT > 30 else "inconclusive"),
    f"run #33: withdraw {hm(BIN_WD_TS)} UTC by erd1r3w62vq...; {f(BIN_TO_CUST)} of {f(BIN_WD_OUT)} EGLD ({BIN_TO_CUST_PCT:.0f}%) sent to Binance Staking custody erd1rf4hv70... at {hm(BIN_SEND_TS)}; 0 to the Binance.com hot wallet; custody balance {f(CUST_NOW)} at the trace.",
    "Branch 're-allocation': > 70% reached Binance Staking custody. The unbond was a move from delegation into custody, not supply for sale. It is not (yet) re-delegated, so the staked ratio will show a ~1pp step down at the next read; that step is a custody choice, not an exit to market. Follow-up test registered: binance-custody-hold."))
for tid, note in [("delivery-price-relevance-2", f"run #33: desk gross {f(otc['gross_out'])} EGLD (one 5,302 relay to Gate.io); no UPbit delivery. Not evaluable."),
                  ("korea-premium-arbitrage", f"run #33: premium {PREM:.1f}%; UPbit took {UPBIT_DEP_N} dust receive in the window and no EGLD deposits; Upbit's caution decision (Oct 19-23) unpublished on Oct 22. Not evaluable; retire if Upbit delists."),
                  ("ninjastaking-exit-destination", f"run #33: {f(NINJA['amount_egld'])} still unbonding, matures {NINJA_MATURES[:16]} (after this run). Earlier legs of the same wallet: 5,000 re-delegated, 1,000 to Binance.com via a fresh wallet, 1,000 to an xExchange swap. Evaluate at run #34 (within 3 days of the withdraw)."),
                  ("overhang-absorbed", f"run #33 INTERIM (not the test window): trailing 7-day rails {R7_NET_EX_ARB:+,.0f} EGLD ex cross-venue, EGLD - BTC {P7_REL:+.1f}pp -> '{ABSORBED_INTERIM}'; the {LIVE_DAYS:.1f}-day window alone {ex['net']:+,.0f} with EGLD {EGLD_VS_BTC:+.1f}pp vs BTC. The registered window (Oct 19 14:40 -> Oct 26) is {LIVE_DAYS:.1f} days old; resolve at run #34, thresholds unchanged.")]:
    t = dict(prior[tid]); t.update({"status": "open", "measured_value": note, "resolution": None}); tests.append(t)


def new(tid, claim, threshold, branches, measured):
    return {"id": tid, "registered_in_run": 33, "claim": claim, "threshold": threshold, "branches": branches,
            "status": "open", "outcome": None, "resolved_in_run": None, "measured_value": measured, "resolution": None}


tests += [
    new("binance-custody-hold", "The 320,000 EGLD Binance returned to its staking custody stays off the market.",
        "By run #35, measured on Binance Staking custody erd1rf4hv70...: > 70% of the 320,000 re-delegated = re-stake; < 50,000 sent to the Binance.com hot wallet and the rest held = held; > 100,000 sent to the hot wallet = supply; otherwise no conclusion",
        [{"condition": "> 70% re-delegated", "reading": "re-stake"},
         {"condition": "< 50K to hot wallet, rest held", "reading": "held"},
         {"condition": "> 100K to hot wallet", "reading": "supply"},
         {"condition": "otherwise", "reading": "no conclusion"}],
        f"run #33: custody {f(CUST_NOW)} EGLD; no outbound at the trace."),
]
resolved = [t for t in tests if t.get("resolved_in_run") == 33]
as_pred = sum(1 for t in resolved if t["outcome"] == "as_predicted")
R["pre_committed_tests"] = tests

# ---------------------------------------------------------------------------
R["meta_learning"] = {
    "run_number": 33,
    "endpoints_that_worked": status["ok"],
    "endpoints_that_failed": [f"NONE with data missing. {D.get('_n_429', 0)} HTTP 429s in the main pass; 0 paged errors; 0 errors in follow-up, rails and traces."],
    "api_quirks": [
        "HOST, NOT API: the collector took about five hours with ~6 s of CPU because the Mac idle-slept between agent turns and suspended the background process (sample showed time.sleep and blocked SSL reads; the API answered in < 1 s). Re-running the follow-up chain under `caffeinate -ims` finished it in minutes. Wrap every background pass in caffeinate and run Python with -u so progress is visible.",
        "Rail state used 'deposits total >= 1 EGLD' to call a venue open; Bitget's 22 receives this window totalled about 1 EGLD of dust and flipped it to 'open'. Floor raised to 10 EGLD.",
        "/accounts/{addr}/delegation returns [] once an unbond is withdrawn, so the run #32 maturity arithmetic (userUndelegatedList seconds) yields 0; the destination has to come from the wallet's outbound legs."],
    "data_gaps": [
        "Balances are as of the collector's first reads (Oct 22 07:28 UTC); Binance's 320,000 custody send (09:18) is on the rails and traces but not in the balance-based exchange or staked figures.",
        "The trailing 7-day rail pass overlaps run #32 by about four days, so it is an interim reading; overhang-absorbed waits for its own window.",
        "Kraken has no tracked address.",
        "Hatom UTK Money Market and OneDex Launchpad still fail bech32 validation.",
        "The poisoning operator's outbound scan hit its 500-tx page cap (2.7 days covered of the window)."],
    "key_findings": [
        f"binance-undelegation-destination resolved as predicted: {f(BIN_TO_CUST)} EGLD ({BIN_TO_CUST_PCT:.0f}%) to Binance Staking custody.",
        f"EGLD {EGLD_VS_BTC:+.1f}pp vs BTC for a second window while exchange inflow rose to ~{PACE_NOW:,.0f}/day.",
        f"erd1hhvfrw... deposited {f(HHV_DEP)} at Binance.com through a second one-shot hop, half the window's Binance deposits.",
        f"Upbit {UP_SHARE:.0f}% of global volume at a {PREM:.1f}% premium during its caution review.",
        f"Unbonding fell to ~{f(sk['undelegated_week']/LIVE_DAYS*7)}/week from ~86,000.",
        f"USDC {USDC_D:+,.0f}, a second bridge-led rise."],
    "action_items_from_previous": len(r26["meta_learning"]["recommendations_for_next_run"]),
    "action_items_completed_detail": [
        f"BINANCE UNBOND - done: withdraw traced one hop; {f(BIN_TO_CUST)} to Binance Staking custody; binance-undelegation-destination resolved (re-allocation).",
        f"NINJASTAKING - deferred: the unbond matures {NINJA_MATURES[:16]}, after this run; the wallet's other legs re-checked (1,000 reached Binance.com via a fresh wallet).",
        "OVERHANG-ABSORBED - deferred: its 7-day window (from 14:40 Oct 19) is 2.7 days old; interim trailing-7d reading recorded, resolution at run #34.",
        "UPBIT - checked (English and Korean searches, Oct 22): no published outcome; both dependent tests stay open.",
        "ERD1HHVFRW HOPS - done: second hop erd1rcty49... found (25,000, Oct 20) and its funding chain traced back to Unknown Whale erd1hl5y4a... via erd1079hvt0....",
        "RAIL END TIMESTAMP - done: the rail pass now stores its own end time in the snapshot; this run's window started exactly at run #32's stored end."],
    "methodology_changes": [
        "CAFFEINATE BACKGROUND PASSES: every long collector/follow-up runs as `caffeinate -ims ... python3 -u`, so host idle sleep cannot stretch a 15-minute pass into hours.",
        "RAIL DEPOSIT FLOOR 10 EGLD: a venue counts as deposit-open only on >= 10 EGLD of value-bearing receives in the window (dust no longer flips state).",
        "INTERNAL STAKING MOVES OFF THE RAILS: Binance de-staking -> Binance Staking custody is excluded from rail totals and the 7-day net (it would add +320,000 and -320,000 to two non-venue wallets)."],
    "new_addresses_discovered_detail": [
        "erd1rcty49rmvv6z80exv2l4pj2cgnnyqkjs639ss2cz0r5nkr8s4rnqfu5v0n - one-shot hop (nonce 2): 6 EGLD test then 24,994 from erd1hhvfrw..., deposited 25,000 at Binance.com nine minutes later (Oct 20 21:35 UTC)",
        "erd1079hvt0a2tha0jr6gykh5ft7nuvgrlt07c6tkuzm8zkyyc66v72qgt9u6p - refill wallet: sends erd1hhvfrw... 200-700 EGLD every 30-60 minutes; funded by Unknown Whale erd1hl5y4a...",
        "erd1ukxuufpkva67hu8ae097euz9teegzv564sc9pf00u3puwer92h6qf07yl4 - Coinbase -> Binance migrator: withdrew ~29,000 from Coinbase wallets in 14 days, deposited 3,254 at Binance.com in four clips this window",
        "erd14gdre9z87n68q4k82v2ye9xsp5pn2xsty33ezq3azjtd8k4fj5ks0lxm9l - Binance.com withdrawal (10,004) supplied to Hatom's EGLD money market within six minutes (Oct 20)"],
    "action_items_completed": 4,
    "new_addresses_discovered": 4,
    "most_valuable_insight": (
        f"Binance's 320,002 EGLD unbond, the largest single exit since the restart, never touched the market: it went whole into Binance's staking custody, as pre-committed in run #30. "
        f"At the same time the market absorbed a faster exchange inflow (~{PACE_NOW:,.0f}/day, half of it one seller's 25,000 hop deposit) while EGLD beat BTC by {EGLD_VS_BTC:+.1f}pp, and the bid came from Korea: Upbit traded {UP_SHARE:.0f}% of global volume at a {PREM:.1f}% premium on a venue that cannot deposit or withdraw EGLD. "
        f"Supply is identifiable and still arriving; demand is concentrated in a market whose fate Upbit decides this week."),
    "top_recommendation": f"RUN #34 FIRST: resolve overhang-absorbed on its Oct 19 14:40 -> Oct 26 window and ninjastaking-exit-destination (withdraw after {NINJA_MATURES[:16]}); record Upbit's decision and re-read the premium and Upbit volume share the same day.",
    "recommendations_for_next_run": [
        "Resolve overhang-absorbed on rails from 2026-10-19 14:40:28 UTC to 2026-10-26 14:40 (fixed end, not trailing); cross-venue wallets out.",
        f"NINJASTAKING: trace erd1me5hmqt5qg...'s {f(NINJA['amount_egld'])} withdraw (matures {NINJA_MATURES[:16]}) one hop and resolve ninjastaking-exit-destination.",
        "UPBIT: record the caution decision (web check); if delisted, retire korea-premium-arbitrage and delivery-price-relevance-2 and measure the premium/volume unwind; if lifted with deposits reopened, start the >= 20-depositor test.",
        "Check /economics staked for the ~320,000 step-down and track Binance Staking custody erd1rf4hv70... outbound for binance-custody-hold.",
        "Trace erd1hl5y4a... -> erd1079hvt0... -> erd1hhvfrw... as one seller: total EGLD routed to Binance since Oct 9, including both one-shot hops.",
        "Run every background pass under caffeinate with python -u (this run lost ~5 hours to host idle sleep)."],
    "dashboard_feature_suggestions": [
        {"title": "Venue volume share and premium timeline",
         "motivation": f"This run Upbit's share of global EGLD volume jumped from {UPSH_PREV:.0f}% to {UP_SHARE:.0f}% at a {PREM:.1f}% premium during its caution review. The dashboard shows only the current orderbook snapshot, so a regime change in where EGLD trades is invisible unless the reader opens two reports side by side.",
         "suggested_visualization": "stacked area of 24h volume share by venue (Binance, Upbit, Bithumb, Bybit, other) per run, with the Korea premium as a line on a second axis and annotations for caution/decision dates",
         "data_already_available": True, "data_source": "whale_intelligence.demand_instruments.exchange_orderbook (upbit_share_of_volume_pct, korea_premium_pct, top_tickers) across report JSONs", "priority": "high"},
        {"title": "Seller funding-chain graph",
         "motivation": f"The largest Binance deposits of runs #32 and #33 ({f(HHV_DEP)} and 12,223) came from one seller through one-shot hops, refilled by erd1079hvt0... from Unknown Whale erd1hl5y4a.... In prose it is four addresses and two hops; as a graph it is one source feeding an exchange.",
         "suggested_visualization": "directed flow graph (source -> refill wallet -> operational wallet -> one-shot hop -> exchange) with edge widths in EGLD and a run selector",
         "data_already_available": False, "data_source": "run33_traces.binance_depositors and binance_funders in data/collected (would need a whale_intelligence.deposit_chains field)", "priority": "medium"},
        {"title": "Pre-committed test ledger with outcomes",
         "motivation": "binance-undelegation-destination resolved this run after three runs open; the dashboard has no view of registered tests, their branches, interim readings and outcomes, which is the report's main accountability mechanism.",
         "suggested_visualization": "table/timeline of tests: registered run, deadline, interim readings per run, resolved branch, with a hit-rate summary",
         "data_already_available": True, "data_source": "pre_committed_tests (top-level report field)", "priority": "medium"}],
    "dashboard_suggestions_followup": [
        {"title": "Seven-day rail netting with cross-venue removal", "status": "pending",
         "note": "Not built. Still useful: overhang-absorbed resolves on a fixed 7-day rail window next run."},
        {"title": "Cross-venue wallet flow graph", "status": "deprioritized",
         "note": "All three cross-venue wallets were idle this run; folded into the broader seller funding-chain graph suggestion."},
        {"title": "Unbonding maturity calendar", "status": "pending",
         "note": "Not built. Its first resolved destination (Binance -> custody) landed this run."}],
    "withdrawn_claims": [],
}

rep = {k: R[k] for k in ["metadata", "executive_summary", "network_health", "whale_intelligence", "staking_intelligence", "token_activity",
                         "defi_activity", "anomalies", "trend_indicators", "watch_list", "meta_learning", "pre_committed_tests"]}
json.dump(rep, open(f"{REPO}/reports/{RD}.json", "w"), indent=1, default=str)
print("report written", len(json.dumps(rep, default=str)), "bytes")
print(f"tests resolved this run {len(resolved)}, as_predicted {as_pred}, open {sum(1 for t in tests if t['status']=='open')}")
print("PREM", round(PREM, 1), "UP_SHARE", round(UP_SHARE, 1), "OPEN", OPEN, "DEPONLY", DEPONLY)
