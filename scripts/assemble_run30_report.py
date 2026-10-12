#!/usr/bin/env python3
"""Run #30 stage 2: assemble reports/2026-10-12.json from derived.json + snapshot.

~2.7-day window (Oct 9 21:00 -> Oct 12). Defining facts: Binance unDelegated 320,002 EGLD from binance_staking and moved
161,137 EGLD hot -> custody on Oct 12; Coinbase (Oct 10) and Bybit (Oct 12) reopened; Whale B -> Coinbase -> Mega Whale 120K.
"""
import json
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD = "2026-10-12"
O = json.load(open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/b8b82f4e-fcb2-488c-b627-23fb854f5366/scratchpad/run30w/derived.json"))
D = json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev = json.load(open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/b8b82f4e-fcb2-488c-b627-23fb854f5366/scratchpad/run30w/previous_run29.json"))
status = json.load(open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/b8b82f4e-fcb2-488c-b627-23fb854f5366/scratchpad/run30w/status.json"))
beh = json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
r26 = json.load(open(f"{REPO}/reports/2026-10-09.json"))   # previous report (name kept for the reused blocks)
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

# ---- run #30 traces ----
TR = D["run30_traces"]
BINV = VEN["Binance.com"]
BD = TR["binance_daily"]["days"]
BIN_TO_CUSTODY = sum(x["egld"] for x in TR["binance_daily"]["top_withdrawals_window"] if x["to"] == "erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p")
BIN_DEP = BINV["in_egld"]; BIN_WD_EXT = BINV["out_egld"] - BIN_TO_CUSTODY
BIN_EXT_NET = BIN_DEP - BIN_WD_EXT
BIN_EXT_PER_DAY = BIN_EXT_NET / LIVE_DAYS
BIN_ENTITY_NET = next((e2["net_flow_egld"] for e2 in ex["entity"] if e2["entity"] == "Binance"), 0.0)
POOL = D.get("unbonding_pool") or []
BIN_UNDEL = sum(pu["amount_egld"] for r in POOL if r["wallet"].startswith("erd1r3w62vq") for pu in r["pending_unbonding"])
BIN_UNDEL_DAYS = max([pu["days_remaining"] for r in POOL if r["wallet"].startswith("erd1r3w62vq") for pu in r["pending_unbonding"]] or [0])
RETAIL_UNDEL = sk["undelegated_week"] - BIN_UNDEL
BINP = next(m for m in sk["moves"] if m["identity"] == "binance_staking")
EXS = TR["exit_route_scan"]; EXR = EXS["by_route"]
EXIT_TRACED = sum(r["withdrawn_egld"] for r in EXS["rows"] if r["route"] != "internal")
EXIT_CEX = sum(r["withdrawn_egld"] for r in EXS["rows"] if r["route"] == "cex")
TERM = TR["desk_terminal"]; TERM_BAL = int(TERM["info"]["balance"]) / 1e18
HMM = TR["hatom_egld_mm"]
CB_OPEN = min(REOPEN[a]["first_send_after_restart_ts"] for a in REOPEN if REOPEN[a]["label"] in ("Coinbase", "Coinbase (secondary)") and REOPEN[a]["first_send_after_restart_ts"])
BY_OPEN = next(REOPEN[a]["first_send_after_restart_ts"] for a in REOPEN if REOPEN[a]["label"] == "Bybit")
MEGA_IN = bid["mega_delta"]; WHALE_B_OUT = 122054.0; WHALE_B_BACK = 30296.0 + 7971.0 + 8167.0 + 8602.0
UPBIT_DEP = VEN.get("UPbit", {}).get("in_egld", 0); UPBIT_DEP_N = VEN.get("UPbit", {}).get("in_senders", 0)
USDC_BURN = usdc["prev"] - usdc["supply"]
PREV_BOOK = prev["exchange_orderbook_latest"]
PREM_PREV = PREV_BOOK.get("korea_premium_pct", 15.4)
UPSH_PREV = PREV_BOOK.get("upbit_share_of_volume_pct", 20.0)
WIN_TXT = f"{LIVE_DAYS:.1f}-day window (Oct 9 21:00 -> Oct 12 {hm(D['liveness']['0']['timestamp'])[-5:]} UTC)"
WINDOW_NOTE = f"{WIN_TXT}: back on the Monday cadence, but the previous snapshot was Friday's, so every flow below is a {LIVE_DAYS:.1f}-day flow."
BIN_RESULT = "as_predicted" if BIN_EXT_PER_DAY > 10000 else ("against" if BIN_EXT_PER_DAY < -5000 else "inconclusive")

wd_top0 = (WD.get("by_provider_top") or [[0, 0]])[0][1]
R = {}
R["metadata"] = {
    "report_date": RD, "period_start": "2026-10-09", "period_end": RD,
    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "egld_price_usd": price, "btc_price_usd": M["btc"], "eth_price_usd": M["eth"],
    "run_number": 30,
    "data_sources_ok": status["ok"] + [
        f"follow-up pass: {WD.get('calls', 0)} withdraw calls decoded, poisoning lookalikes re-scanned (0 errors)",
        "rail check (rails_run30.py): value-bearing EGLD deposits/withdrawals per tracked exchange wallet since restart 2, paginated",
        "targeted traces (trace_run30.py): collector-side exit-route scan over every withdraw > 3,000 EGLD, Binance.com per-day rails since Oct 9 08:04, funder-wallet re-deposit check, OTC desk terminal, Hatom EGLD market call history since Oct 5",
        "spot checks: Unknown Whale B and the cross-venue wallet erd1d2anjjha transaction histories"],
    "data_sources_failed": status["failed"],
    "data_sources_recovered": [
        "LIVENESS GATE PASSED: every shard within seconds of real time at collection",
        f"{D.get('_n_429', 0)} HTTP 429 responses in the main pass; 0 paged errors, 0 API errors",
        "The first collector launch stalled for ~5 hours with no output (buffered stdout, likely host sleep); it was killed and re-run unbuffered. Window end is the re-run time.",
        WINDOW_NOTE,
        f"delegator reward behaviour sampled {ag['providers_sampled']} of {ag.get('providers_requested', 8)} providers"]}

R["executive_summary"] = [
    {"category": "staking", "severity": "high", "finding":
     f"BINANCE UNDELEGATED {f(BIN_UNDEL)} EGLD FROM ITS OWN STAKING PROVIDER. At 06:16 UTC on Oct 12 Binance's de-staking wallet (erd1r3w62vq...) called unDelegate on the binance_staking contract, which fell {f(abs(BINP['delta']))} to {f(BINP['locked'])} EGLD (-80%). It unbonds in ~{BIN_UNDEL_DAYS:.0f} days (about Oct 21). "
     f"That one call is {100*BIN_UNDEL/sk['undelegated_week']:.0f}% of the window's {f(sk['undelegated_week'])} EGLD unDelegated; the other {sk['undelegate_callers']-1} wallets account for {f(RETAIL_UNDEL)}. In run #18/19 the same wallet forwarded unbonded EGLD to the Binance Staking custody wallet, not to the hot wallet."},
    {"category": "whale", "severity": "high", "finding":
     f"BINANCE MOVED {f(BIN_TO_CUSTODY)} EGLD FROM ITS HOT WALLET INTO STAKING CUSTODY THE SAME MORNING (10:22 UTC). Custody rose to {f(cust['balance'])} EGLD, its highest reading in the series, and the hot wallet fell {f(cust['hot_previous']-cust['hot_balance'])}. Net of that internal move, Binance.com took {f(BIN_DEP)} EGLD of deposits against {f(BIN_WD_EXT)} of customer withdrawals: {BIN_EXT_NET:+,.0f} EGLD, or {BIN_EXT_PER_DAY:+,.0f} per day. "
     "Deposits still lead withdrawals on every day of the window, so binance-deposit-persistence resolves as predicted (> +10,000 EGLD/day)."},
    {"category": "whale", "severity": "high", "finding":
     f"COINBASE AND BYBIT REOPENED. Coinbase's first post-halt EGLD flows came at {hm(CB_OPEN)} UTC; within six minutes Unknown Whale B sent {f(WHALE_B_OUT)} EGLD into Coinbase and Coinbase's routing wallet passed {f(MEGA_IN)} to the Mega Whale erd18mv2z6r2 (balance {f(bid['mega_bal'])}). "
     f"That is the April pattern: a Coinbase-intermediated transfer between two known whales, not open-market buying. Bybit sent its first withdrawal at {hm(BY_OPEN)} UTC. Open both ways this window: {', '.join(OPEN)}."},
    {"category": "network", "severity": "medium", "finding":
     f"EGLD {pc:+.1f}% TO ${price:.2f} WHILE BTC ({M['btc_wow']:+.1f}%) AND ETH ({M['eth_wow']:+.1f}%) ROSE. The Upbit premium widened again to {PREM:.1f}% (from {PREM_PREV:.1f}%) and Upbit's share of global volume rose to {UP_SHARE:.0f}% (from {UPSH_PREV:.0f}%); UPbit's hot wallet received {UPBIT_DEP_N} small deposits ({f(UPBIT_DEP)} EGLD) and made no withdrawals. "
     f"Cross-venue wallets are active again: erd1d2anjjha... withdrew from Binance.com and Bybit and deposited at Gate.io; erd13sytuz92... moved Gate.io to Bybit. 7-day CEX spot volume {f(BOOK['spot_volume_7d_egld']/1e6, 2)}M EGLD (from {f(BOOK['spot_volume_prior_7d_egld']/1e6, 2)}M)."},
    {"category": "staking", "severity": "medium", "finding":
     f"NO RETAIL EXIT TO A CEX IN THE WINDOW. The collector-side scan covered every withdraw call above 3,000 EGLD: {EXS['calls']} calls, {f(EXIT_TRACED)} EGLD outside exchange-operated wallets, none to a CEX ({EXR.get('re-delegate',{}).get('n',0)} re-delegated, {EXR.get('held',{}).get('n',0)} held; Crypto.com's own sweep wallet tagged internal). "
     f"All {O['withdraw_calls']} withdraw calls returned {f(WD.get('egld_returned_total', 0))} EGLD. exit-route-cex resolves inconclusive: there was almost no unbonded EGLD to route. The test that matters is where Binance's {f(BIN_UNDEL)} goes around Oct 21."},
    {"category": "defi", "severity": "low", "finding":
     f"HATOM'S EGLD MARKET FELL ANOTHER {abs(EMM_D):,.0f} EGLD ({100*EMM_D/df['egld_mm_prev_balance']:+.0f}%) TO {f(df['egld_mm_balance'])}; HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.1f}%. Since Oct 5 the market logged {HMM['redeem_calls']} redeem calls from {HMM['by_function'].get('redeem',{}).get('distinct_senders',0)} wallets (one wallet made {HMM['redeem_senders_top'][0][1]} of them) and zero liquidation calls: suppliers left, borrowers were not forced out. "
     f"xExchange 24h volume ${f(bid['dexvol'])} ({100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.0f}% in EGLD), {bid['wegld_usdc_share']:.0f}% WEGLD/USDC."},
    {"category": "whale", "severity": "low", "finding":
     f"THE OTC DESK'S OCT 6 TERMINAL IS A HOLDER, NOT A ROUTER. erd1y27r22... has nonce 1 and holds {f(TERM_BAL, 1)} EGLD, the desk's 5,745 plus small top-ups; it has sent nothing of value. Desks {f(otc['desk_bal'])} (from {f(otc['prev_desk'])}); gross out {f(otc['gross_out'])} EGLD in the window, all from the Distribution wallet in sub-700 EGLD clips. No UPbit reload."},
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
               "btc_correlation_note": f"BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%, EGLD {pc:+.2f}%: EGLD fell {abs(EGLD_VS_BTC):.1f}pp against BTC over {LIVE_DAYS:.1f} days while both majors were flat to up."},
    "liveness": {"ok": D["liveness_ok"], "latest_block_by_shard": {k: iso(v["timestamp"]) for k, v in D["liveness"].items()},
                 "restart_1_utc": iso(1790181300), "restart_1_stopped_utc": iso(1790182386), "restart_2_utc": iso(1790263800),
                 "live_days_in_window": LIVE_DAYS, "rollback_point_utc": "2026-09-19 06:37:45 UTC"},
    "analysis": (
        f"WINDOW. {WINDOW_NOTE} Every shard read within seconds of real time. Epoch {st['epoch']} ({st['epoch']-pact['epoch']:+d}), "
        f"{f(st['transactions']-pact['total_transactions'])} transactions (~{f(int((st['transactions']-pact['total_transactions'])/LIVE_DAYS))}/day), {f(st['accounts']-pact['total_accounts'])} new accounts. Total supply {f(econ['totalSupply'])} ({econ['totalSupply']-pecon['total_supply']:+,}).\n\n"
        f"STAKING. Staked EGLD {M['staked_chg']:+,.0f} to {f(econ['staked'])}; ratio {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp), flat on the low. That flat print hides the window's biggest event: Binance unDelegated {f(BIN_UNDEL)} EGLD on Oct 12, and delegation TVL fell {f(abs(sk['delta_locked']))}. "
        f"Undelegated EGLD still counts in /economics staked until it unbonds, so the ratio should step down by about {100*BIN_UNDEL/econ['circulatingSupply']:.1f}pp around Oct 21 unless Binance re-stakes it. Network APR {100*econ['apr']:.2f}%.\n\n"
        f"PRICE. EGLD ${price:.2f}, {pc:+.2f}%, against BTC {M['btc_wow']:+.2f}% and ETH {M['eth_wow']:+.2f}%: a third consecutive window in which EGLD trailed BTC (runs #28-#30; run #27 outperformed). "
        f"The order books are thin (Binance bids within 2% total ${f(BOOK['binance']['depth_minus2_usd'])}; all venues ${f(BOOK['all']['depth_minus2_usd'])}). Global CEX spot volume over 7 days {f(BOOK['spot_volume_7d_egld']/1e6, 2)}M EGLD, against {f(BOOK['spot_volume_prior_7d_egld']/1e6, 2)}M the week before.")}


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


INV_SERIES = {**prev["otc_desk_inventory_series"], "run30": round(otc["desk_bal"])}
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
                        "note": f"Value-bearing EGLD transactions only (ESDT spam airdrops and exchange-internal sweeps excluded). {WIN_TXT}. Coinbase first moved EGLD both ways at {hm(CB_OPEN)} UTC; Bybit sent its first withdrawal at {hm(BY_OPEN)} UTC; Binance.com includes one internal {f(BIN_TO_CUSTODY)} EGLD send to Binance Staking custody (Oct 12 10:22). UPbit received small deposits but sent nothing. MEXC, KuCoin, Bitfinex and Tokero moved no EGLD. Previous run (4-day window Oct 5 - Oct 9): states describe this window only (Crypto.com, Bitget and Tokero worked both ways in earlier windows; Bitget and Tokero receives this window were sub-1-EGLD dust, so they read as withdrawal-only, and Crypto.com had no customer flow). Binance.com sent its first EGLD withdrawal on Oct 9 at 08:04 UTC after deposits had been open since Sep 29; the UPbit exchange wallet's only value-bearing flow was a 14,000 EGLD send to its OTC desk (not a customer withdrawal). MEXC and KuCoin remain at their Sep 24 replay transactions. Public status: no Binance announcement of a native-network reopening was found in web search, so the Binance state is inferred from chain data."},
        "signal": (f"{len(OPEN)} TRACKED VENUES NOW MOVE EGLD BOTH WAYS ({', '.join(OPEN)}). Net exchange balance change {ex['net']:+,.0f} EGLD over {LIVE_DAYS:.1f} days: " + ", ".join(f"{e2['entity']} {e2['net_flow_egld']:+,.0f}" for e2 in ex["entity"] if e2["net_flow_egld"]) + ". "
                   f"Binance's +{f(BIN_ENTITY_NET)} includes its own hot-to-custody move ({f(BIN_TO_CUSTODY)}), which nets to zero inside the entity; customer flow at Binance.com was {BIN_EXT_NET:+,.0f}. Gate.io's {next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Gate.io'),0):+,.0f} is more than half two cross-venue wallets (about 30,000 EGLD) that re-deposited at Binance.com and Bybit. "
                   "Exchange-flow and OTC series are still not appended to the weekly baselines: UPbit is closed for withdrawals and the window is short."),
        "by_exchange": [{"exchange": w["exchange"], "change_egld": w["change_egld"], "pct": w["pct"]} for w in ex["per_wallet"]],
        "entity_netting": [{"entity": e2["entity"], "wallets_count": e2["wallets_count"],
                            "net_flow_egld": e2["net_flow_egld"], "interpretation": entity_interp(e2)} for e2 in ex["entity"]]},
    "dormant_activations": [],
    "exit_routes": {
        "route_this_run": "no CEX exits; re-delegate / held (scan of every withdraw > 3,000 EGLD)",
        "route_previous_run": "CEX deposit (Binance.com, meria unstaker)",
        "scan_threshold_egld": 3000, "scan_calls": EXS["calls"], "scan_by_route": EXR,
        "scan_rows": [{"sender": r_["sender"], "sender_label": r_["sender_label"], "provider": r_["provider"], "withdrawn_egld": r_["withdrawn_egld"],
                       "route": r_["route"], "balance_now_egld": r_["balance_now"]} for r_ in EXS["rows"]],
        "traced_egld_ex_internal": EXIT_TRACED, "traced_to_cex_egld": EXIT_CEX,
        "binance_undelegation": {"wallet": "erd1r3w62vqmsux5e38p6vnueatmfcs8nr5lmg3s97x6rafqpgxfae0sxv9z0v", "egld": BIN_UNDEL,
                                 "called_utc": "2026-10-12 06:16 UTC", "unbonds_in_days": BIN_UNDEL_DAYS,
                                 "claimed_rewards_egld": 6760.28, "rewards_route": "erd124tc2z7gzk... then Binance.com hot wallet, Oct 12 06:35"},
        "binance_hot_to_custody_egld": BIN_TO_CUSTODY,
        "whale_b_to_mega_whale": {"whale_b": "erd1at3jm3xvzxhdgt4f695l7l2f6r0tpkqjnemfpc0raam5e9xtjuqqs6fkul", "sent_to_coinbase_egld": WHALE_B_OUT,
                                  "received_back_from_coinbase_egld": WHALE_B_BACK, "mega_whale_received_egld": MEGA_IN, "utc": "2026-10-10 22:32-22:55 UTC"},
        "note": (f"Collector-side scan of every withdraw call above 3,000 EGLD in the window ({EXS['calls']} calls): Crypto.com's own staking-sweep wallet (3,027, internal), a valuestaking leg (4,892) still held in the wallet, and a core-block leg (3,833) re-delegated to pi-staking within two minutes. None reached an exchange. "
                 f"The large pending item is Binance's own {f(BIN_UNDEL)} EGLD unDelegate, which unbonds about Oct 21; its 6,760 EGLD of claimed rewards went to Binance.com through one hop the same morning.")},
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
        "method_note": f"Fourth read after restart; invalid balances {HR['invalid_total_egld']:.2f} EGLD, unchanged."},
    "otc_pipeline": {
        "gross_outbound_egld_7d": otc["gross_out"], "gross_inbound_egld_7d": otc["gross_in"],
        "circular_egld_7d": otc["circular"], "net_one_way_egld_7d": otc["net_one_way"],
        "circular_share_pct": otc["circ_pct"],
        "desk_balance_egld": otc["desk_bal"], "previous_desk_balance_egld": otc["prev_desk"],
        "upbit_reload_egld": otc["upbit_feed"],
        "venue_netting": [],
        "router_tail_delivery_egld": 0.0, "router_tail_routers": 0,
        "gross_series_egld_7d": {**r26o["gross_series_egld_7d"], "run30": otc["gross_out"]},
        "net_one_way_series_egld_7d": {**r26o["net_one_way_series_egld_7d"], "run30": otc["net_one_way"]},
        "desk_inventory_series_egld": INV_SERIES,
        "circularity_series_pct": {**r26o["circularity_series_pct"], "run30": 0.0},
        "peak_window_renetted": r26o["peak_window_renetted"],
        "backfilled_windows": r26o.get("backfilled_windows", []),
        "wave_window_netting": {**r26o["wave_window_netting"],
            "note": f"Wave #4 stays closed at 467,107 EGLD one-way (Sep 7 to the halt, frozen labels). The post-restart window (Sep 24 - Oct 12) nets {f(otc['wave']['net_one_way'])} EGLD one-way."},
        "feed_by_parent_venue": [],
        "feeder_backtrace": O["feeder_backtrace"],
        "address_poisoning": [{"address": a, "mimics": v["note"], "nonce": v["nonce"], "dust_txs_30d": v["dust_txs_30d"],
                               "distinct_targets_30d": v["distinct_targets_30d"],
                               "inbound_above_0_01_egld": len(v["inbound_above_0_01_egld"])} for a, v in PZ.items()],
        "desk_terminal_resolved": {"address": TERM["address"], "nonce": TERM["info"].get("nonce"), "balance_egld": TERM_BAL, "role": "holder (nonce 1, no value sent)"},
        "series_note": (f"QUIET, {LIVE_DAYS:.1f}-DAY WINDOW. Gross out {f(otc['gross_out'])} EGLD, all from the Distribution wallet: seven 137 EGLD clips to erd14fmv4hsu... on Oct 11 05:21-05:27 and 694 to erd14xjr6u0s..., both of which deposited the same amounts at Gate.io on Oct 11 23:00. No UPbit reload. "
                        f"Oct 6 terminal erd1y27r22... resolved: nonce 1, holds {f(TERM_BAL, 1)} EGLD (a holder, not a router). Desks {f(otc['desk_bal'])} (from {f(otc['prev_desk'])}). Under the 20,000 partial line of otc-pipeline-resumption.")},
    "demand_instruments": {
        "identifiable_bid_absorbed_egld_7d": 0.0, "mega_whale_otc_leg_egld": MEGA_IN,
        "mega_whale_balance_egld": bid["mega_bal"] or 0.0, "mega_whale_change_egld": bid["mega_delta"],
        "coinbase_routing_balance_egld": bid["cbr_bal"] or 0.0, "coinbase_routing_inflow_egld": 120141.0,
        "coinbase_routing_funder": "erd1m9qn6gvercs6ksvtn924w4y7z9ppglyfugpu34al26t9u4mvzvqqlq9dc3", "coinbase_routing_funder_label": "Coinbase (secondary), fed by Unknown Whale B's 122,054 deposit three minutes earlier",
        "weeks_at_zero": 10, "weeks_at_zero_in_last_four": 4, "bid_to_distribution_ratio_pct": 0.0,
        "dex_turnover_ratio_pct": bid["turnover"], "previous_dex_turnover_ratio_pct": bid["prev_turnover"],
        "dex_volume_egld_24h": bid["dexvol_egld"], "previous_dex_volume_egld_24h": bid["prev_dexvol_egld"],
        "pool_tvl_egld": bid["pooltvl_egld"], "previous_pool_tvl_egld": bid["prev_pooltvl_egld"],
        "wegld_usdc_volume_usd": bid["wegld_usdc_vol"], "wegld_usdc_share_of_volume_pct": bid["wegld_usdc_share"],
        "ex_wegld_usdc_volume_usd": bid["ex_wegld_usdc_vol"], "ex_wegld_usdc_volume_egld": bid["ex_wegld_usdc_vol_egld"],
        "dex_volume_status": "evaluable; compared with run #29",
        "absorber_scan": {"terminals_scanned": absb["scanned"],
                          "terminals_retaining_over_half": len(absb["retaining"]),
                          "total_received_from_desks_egld": absb["total_received"],
                          "total_retained_egld": absb["total_balance_held"],
                          "retained_share_pct": 0.0,
                          "verdict": "One small desk outbound terminal; the instrument stays retired. The Mega Whale's +120,172 is a Coinbase-intermediated whale-to-whale leg, recorded separately, not an absorbed bid."},
        "withdrawal_breadth": {"distinct_recipients_raw": br["raw_n"], "total_egld_raw": br["raw_egld"],
                               "distinct_recipients_ex_pipeline": br["ex_n"], "total_egld_ex_pipeline": br["ex_egld"],
                               "pipeline_share_pct": br["pipeline_share"], "top_two_share_pct": br["top_two_share_pct"]},
        "withdrawal_breadth_top": br["top"],
        "exchange_orderbook": {
            "source": "CoinGecko exchange tickers with 2% depth and daily spot volume (third-party). PARTIAL RAILS: UPbit withdrawals still closed on chain; Binance.com, Coinbase, Bybit, Gate.io open",
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
    + f". Closed, no EGLD moved: {', '.join(k for k, v in VEN.items() if v['state'] == 'closed')}. Coinbase reopened at {hm(CB_OPEN)} UTC and Bybit at {hm(BY_OPEN)} UTC.\n\n"
    f"BINANCE, THREE MOVES IN ONE MORNING. (1) 06:15-06:16 UTC Oct 12: the de-staking wallet erd1r3w62vq... claimed rewards and unDelegated {f(BIN_UNDEL)} EGLD from binance_staking (provider {f(BINP['prev_locked'])} -> {f(BINP['locked'])}). (2) 06:17-06:35: the 6,760 EGLD of claimed rewards went through erd124tc2z7gzk... into the Binance.com hot wallet. "
    f"(3) 10:22: the hot wallet sent {f(BIN_TO_CUSTODY)} EGLD to Binance Staking custody, now {f(cust['balance'])}. In run #18/19 this de-staking wallet forwarded unbonded EGLD to custody, so the likely end state around Oct 21 is a larger custody balance and a smaller provider, not a sale. That is an inference from one prior cycle; the test is registered (binance-undelegation-destination).\n\n"
    f"BINANCE.COM CUSTOMER FLOW. Per day since the Oct 9 08:04 reopening (deposits / withdrawals, EGLD): " + "; ".join(f"{d_[5:]}: {f(v_['dep_egld'])} / {f(v_['wd_egld'])}" for d_, v_ in BD.items())
    + f". Oct 12's withdrawals include the {f(BIN_TO_CUSTODY)} custody move; without it, {f(BD['2026-10-12']['wd_egld']-BIN_TO_CUSTODY)}. Over the window, {f(BIN_DEP)} in and {f(BIN_WD_EXT)} out to customers: {BIN_EXT_NET:+,.0f} ({BIN_EXT_PER_DAY:+,.0f}/day). The largest deposit was 15,179 EGLD from erd1reh7sy2c..., which had withdrawn 15,177 from Gate.io minutes earlier: an arbitrage leg, not a holder selling. "
    f"Last week's funders did not return: erd1hl5y4a... sent Binance only a 172 EGLD clip and holds {f(TR['binance_funders']['erd1hl5y4a']['balance_egld'])}; erd1vxa2vk... holds {f(TR['binance_funders']['erd1vxa2vk']['balance_egld'])} and sent nothing; the meria consolidator is empty. erd1hl5y4a... takes many 100-160 EGLD receives from distinct wallets, a hot-wallet pattern; it is probably an exchange or payment wallet, not a whale.\n\n"
    f"COINBASE REOPENED WITH A WHALE-TO-WHALE TRANSFER. Coinbase's first EGLD flows came at {hm(CB_OPEN)}. At 22:32 Unknown Whale B sent {f(WHALE_B_OUT)} EGLD to Coinbase (secondary); at 22:33 that wallet sent 110,002 to Coinbase's routing wallet, which forwarded 110,033 to the Mega Whale erd18mv2z6r2 at 22:35 and another 10,139 at 22:55. Whale B then received {f(WHALE_B_BACK)} back from Coinbase over two days. "
    "This is the April 14-18 pattern repeated (Whale B liquidated 512K to Coinbase and the Mega Whale received 799K through the same routing wallet): Coinbase intermediating a bilateral transfer. The Mega Whale's first gain in ten weeks is not open-market demand.\n\n"
    f"CROSS-VENUE WALLETS. With five venues open, arbitrage wallets are back: erd1d2anjjha... withdrew 14,315 from Binance.com and 12,792 from Bybit and deposited 8,992 at Gate.io; erd13sytuz92... moved 12,943 from Gate.io to Bybit; erd1reh7sy2c... moved 15,177 from Gate.io to Binance.com. Gate.io's {next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Gate.io'),0):+,.0f} is mostly this.\n\n"
    f"WHALES. Tiers on the common-address basis ({O['tiers_basis']} wallets): mega {O['tiers']['mega']['net_change_egld']:+,.0f} (custody +161K, Mega Whale +120K), large {O['tiers']['large']['net_change_egld']:+,.0f} (Binance.com hot -125K, Whale B -67K), mid {O['tiers']['mid']['net_change_egld']:+,.0f} (Gate.io, Coinbase secondary, Hatom EGLD market -12.8K).\n\n"
    f"UNKNOWN WHALE I: {CEN['Unknown Whale I']['inbound_txs']} inbound again. erd1a6lte0: {CEN['erd1a6lte0']['inbound_txs']} inbound from {CEN['erd1a6lte0']['distinct_senders']} distinct senders and one outbound, its first activity since the halt and the deposit-wallet pattern the exchange hypothesis predicts.\n\n"
    f"DEMAND. Binance+Bybit bids within 2% of mid total ${f(bbn)} (closed-book base ${f(bbn_prev)}). Upbit's premium is {PREM:.1f}% (from {PREM_PREV:.1f}%) on {UP_SHARE:.0f}% of global volume (from {UPSH_PREV:.0f}%).")
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
                   "weeks_in_state": {"ledgerbyfigment": 15, "p2p_org_": 6, "truststakingsw": 17}.get(r["provider"], 4),
                   "note": f"emptied inside the archive (last locked > 0 snapshot {r['last_locked_in_archive']}); {r['inbound_txs_this_week']} inbound txs this week"
                           + (f"; delegators {d['prev_users']:,} -> {d['users']:,} ({d['users_delta']:+d})" if d.get("users") is not None and d.get("prev_users") is not None else "")})
for ident in ("egldstakingprovider", "procryptostaking"):
    states.append({"provider": ident, "state": "fee_squeezed", "locked_egld": mv(ident, "locked"),
                   "num_users": mv(ident, "users"), "num_nodes": mv(ident, "nodes"), "apr_pct": mv(ident, "apr") or 0.0,
                   "fee_pct": mv(ident, "fee") or 0.0, "weeks_in_state": 7,
                   "note": f"SEVENTH WEEK AFTER THE FEE REVERSAL ({LIVE_DAYS:.1f}-day window): book {mv(ident,'delta'):+,.0f}, users {mv(ident,'users_delta'):+d}. Still losing capital with yield restored."})
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
                          "note": "Zero transitions for a seventh week. Join on contract address, 100% match (188 of 188), no identity changes. binance_staking fell 80% but keeps 50 nodes and 79,328 EGLD, so it is not a deregistration."},
    "fee_events": [{"provider": i, "fee_from_pct": 100.0, "fee_to_pct": mv(i, "fee") or 0.0, "apr_from_pct": 0.0, "apr_to_pct": mv(i, "apr") or 0.0,
                    "locked_egld": mv(i, "locked"), "locked_wow_egld": mv(i, "delta"), "users": mv(i, "users"),
                    "users_wow": mv(i, "users_delta"), "num_nodes": mv(i, "nodes")} for i in ("egldstakingprovider", "procryptostaking")],
    "unbonding_in_flight": {
        "wallet": ub["wallet"], "total_egld": ub["pending_total"],
        "legs": [{"provider": p["contract"][:10] + "..." + p["contract"][-8:], "amount": p["amount_egld"],
                  "days_to_unbond": p["days_remaining"], "date": "2026-08-14" if p["amount_egld"] < 100000 else "2026-08-15"} for p in ub["pending"]],
        "share_of_delegation_decline_pct": 0.0, "raw_residual_egld": sk["residual"], "corrected_direct_node_egld": None,
        "status": f"RETIRED, NINTH WEEK UNMOVED. Balance {f(ub['balance'],2)} EGLD, {f(ub['pending_total'])} unbonded-and-unclaimed.",
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
            f"COMPOUND RATE {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} reDelegateRewards vs {cvc['claim_count']} claimRewards), from 60.85%. Series: 57.03 / 57.51 / 62.05 / 49.44 / 62.68 / 52.40 / 58.28 / 60.85 / {cvc['compound_pct_of_reward_decisions']:.2f}. Inside the 57-63% range for a fourth run.",
            f"Retail {fates['retail']['total_events']} claims, {fates['retail']['by_count'].get('sold',0)} to a labelled exchange; mid-tier {fates['mid_tier']['total_events']}, {fates['mid_tier']['by_count'].get('sold',0)} sold; institutional {fates.get('institutional',{}).get('total_events',0)}, {fates.get('institutional',{}).get('by_count',{}).get('sold',0)} sold (two claims, too few to read).",
            f"Sample: {ag['providers_sampled']} of {ag.get('providers_requested',8)} providers, 7-day delegator window (overlaps run #29's).",
            "PROVIDER OPERATORS DID NOT SELL FEES for an eighteenth consecutive run (destinations: DeFi deposits, held, rotated)."]},
    "analysis": (
        f"ONE CALLER DOMINATES THE QUEUE. {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD in {LIVE_DAYS:.1f} days across {sk['providers_scanned']} provider contracts. {f(BIN_UNDEL)} of it ({100*BIN_UNDEL/sk['undelegated_week']:.0f}%) is one call by Binance's de-staking wallet on binance_staking. "
        f"The other {sk['undelegate_callers']-1} wallets unDelegated {f(RETAIL_UNDEL)} EGLD, about {f(RETAIL_UNDEL/LIVE_DAYS*7)} a week at this pace: well under the 73-84K pre-halt weeks. Outside Binance, the post-halt exit wave has faded.\n\n"
        f"WITHDRAWALS WERE SMALL. {O['withdraw_calls']} withdraw calls (from {O['prev_withdraw_calls']} in the 4-day run #29 window) returned {f(WD.get('egld_returned_total',0))} EGLD, led by valuestaking ({f(wd_top0)}). Every call above 3,000 EGLD was traced: none went to an exchange. Measured pending among the largest callers: {f(sk['pool_total'])} EGLD, {100*BIN_UNDEL/sk['pool_total']:.0f}% of it Binance's.\n\n"
        f"THE RATIO AND THE RESIDUAL. Delegation TVL fell {f(abs(sk['delta_locked']))} to {f(tl)} while /economics staked rose {M['staked_chg']:+,.0f}: a residual of {sk['residual']:+,.0f}, almost exactly Binance's undelegated amount, which stays in 'staked' until it unbonds. Ratio {100*M['sr']:.2f}%. "
        f"Concentration eased as binance_staking fell from {f(BINP['prev_locked'])} to {f(BINP['locked'])}: HHI {sk['hhi']:.5f} (from {sk['prev_hhi']:.5f}).\n\n"
        f"COMPOUNDING {cvc['compound_pct_of_reward_decisions']:.2f}%. DELEGATORS {sk['users_delta']:+,} to {f(sk['users'])}; {sk['gaining']} providers gained and {sk['losing']} lost. Outside Binance, pi-staking led inflows ({mv('pi-staking','delta'):+,.0f}, partly the core-block leg re-delegated) and Synexis led outflows ({mv('Synexis','delta'):+,.0f}) while gaining {mv('Synexis','users_delta'):+d} delegators. Zero deregistration transitions for a seventh week.")}
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
        "volume_status": "evaluable; compared with run #29 (24h snapshots)",
        "mex_pair_depth": {"pair": "MEX/WEGLD", "tvl_usd": xx["mex_pair_depth"]["tvl_usd"], "tvl_egld": xx["mex_pair_depth"]["tvl_egld"],
                           "previous_tvl_egld": xx["mex_pair_depth"]["previous_tvl_egld"], "tvl_egld_wow_pct": xx["mex_pair_depth"]["tvl_egld_wow_pct"],
                           "volume_24h_usd": xx["mex_pair_depth"]["volume_24h_usd"], "trades_24h": xx["mex_pair_depth"]["trades_24h"],
                           "share_of_pool_tvl_pct": xx["mex_pair_depth"]["share_of_pool_tvl_pct"], "depth_rank": xx["mex_pair_depth"]["depth_rank"]},
        "mex_pair_event": r26["token_activity"]["xexchange"]["mex_pair_event"]},
    "analysis": (
        f"DEX VOLUME DOUBLED IN EGLD TERMS. 24h volume ${f(xx['vol'])} ({f(bid['dexvol_egld'])} EGLD) against ${f(xx['prev_vol'])} ({f(bid['prev_dexvol_egld'])} EGLD) at the last snapshot, {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.0f}% in EGLD. "
        f"WEGLD/USDC is {bid['wegld_usdc_share']:.0f}% of it, so this is the main EGLD/dollar pool trading more as CEX rails reopened (arbitrage against the venues) rather than broader token activity. Turnover {bid['turnover']:.2f}% of pool TVL (from {bid['prev_turnover']:.2f}%). Pool TVL {f(bid['pooltvl_egld'])} EGLD ({100*(bid['pooltvl_egld']-bid['prev_pooltvl_egld'])/bid['prev_pooltvl_egld']:+.1f}% in EGLD), ${f(bid['pooltvl'])} ({100*(bid['pooltvl']-bid['prev_pooltvl'])/bid['prev_pooltvl']:+.1f}%) in dollars. A single 24h snapshot; read the direction, not the size.\n\n"
        f"MEX ${xx['mex_price']:.2e} from the pool ({xx['mex_wow']:+.1f}% over the window, against EGLD {pc:+.1f}%); MEX/WEGLD depth ${f(xx['mex_pair_depth']['tvl_usd'])}, rank {xx['mex_pair_depth']['depth_rank'] or 'outside the top 25 by volume'}.\n\n"
        f"STABLECOINS SPLIT. USDC {usdc['pct']:+.2f}% to {f(usdc['supply'])} ({f(USDC_BURN)} redeemed) while USDT rose {usdt['pct']:+.2f}% to {f(usdt['supply'])}, its first increase after seven declining readings in the stored series. "
        f"NEWLY ISSUED: {len(newly)} issuance{'s' if len(newly)!=1 else ''} in the window, below the traction bar.")}
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
         "notable_events": f"EGLD market {f(df['egld_mm_prev_balance'])} -> {f(df['egld_mm_balance'])} EGLD, HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.2f}%, HUSDC {HT['HUSDC-d80042']['supply_pct']:+.2f}%. Aggregate lending TVL in EGLD {hl:+.2f}% on a {pc:+.2f}% price week (mechanical: dollar collateral is worth more EGLD when EGLD falls).",
         "health_signal": "draining" if EMM_D < -25000 else "flat"},
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
         "notable_events": f"{f(es('VOXEGLD-5872e5'))} EGLD, supply {(em['VOXEGLD-5872e5']['pct'] or 0):+.1f}%, holders {em['VOXEGLD-5872e5']['holders']}: sixth week of growth.", "health_signal": hs(ep("VOXEGLD-5872e5"))},
        {"protocol": "VestaX Finance", "category": "liquid_staking", "addresses_tracked": 1, "tvl_usd": (es("VEGLD-2b9319") or 0) * price, "tvl_egld": es("VEGLD-2b9319") or 0.0,
         "tvl_wow_change_pct": ep("VEGLD-2b9319"), "transfers_24h": None,
         "notable_events": f"{f(es('VEGLD-2b9319'))} EGLD.", "health_signal": hs(ep("VEGLD-2b9319"))}],
    "sc_deployments": [],
    "analysis": (
        f"HATOM'S EGLD MARKET KEPT DRAINING, WITHOUT LIQUIDATIONS. The EGLD money market holds {f(df['egld_mm_balance'])} EGLD, from {f(df['egld_mm_prev_balance'])} ({EMM_D:+,.0f}), and HEGLD supply is {HT['HEGLD-d61095']['supply_pct']:+.2f}% (run #29: -30,848 EGLD). "
        f"The call history since Oct 5 answers run #29's question: {HMM['redeem_calls']} redeem calls from {HMM['by_function'].get('redeem',{}).get('distinct_senders',0)} wallets ({HMM['redeem_senders_top'][0][1]} of them from erd1wzlleutr...), {HMM['by_function'].get('borrow',{}).get('n',0)} borrows, {HMM['by_function'].get('repayBorrow',{}).get('n',0)} repayments and {HMM['liquidation_calls']} liquidations. Suppliers withdrew; borrowers kept borrowing. "
        f"Aggregate lending TVL ex-HMEX reads {hl:+.2f}% in EGLD because the dollar assets (HUSDC {HT['HUSDC-d80042']['supply_pct']:+.2f}%, HUSDT {HT['HUSDT-6f0914']['supply_pct']:+.2f}%) are worth more EGLD at a lower price. The price moved under 5%, so the inverse-ratio rule is not evaluable this window.\n\n"
        f"LIQUID STAKING. SEGLD {lsd['SEGLD-3ad2d0']['pct']:+.2f}%, XEGLD {lsd['XEGLD-e413ed']['pct']:+.2f}%, SWTAO {lsd['SWTAO-356a25']['pct']:+.2f}%, USH {lsd['USH-111e09']['pct']:+.2f}%. VoxEGLD {(em['VOXEGLD-5872e5']['pct'] or 0):+.1f}% (sixth week of growth, still under 2,500 EGLD). Discovery sweep: eight protocols found, two of them 1-2 EGLD test deployments.\n\n"
        f"ACTIVITY. XOXNO aggregator {f(cnt('XOXNO Aggregator'))} transfers in 24h, OneDex {f(cnt('OneDex Swap'))}, Hatom LSD {f(cnt('Hatom Liquid Staking'))}.")}

# ---------------------------------------------------------------------------
R["anomalies"] = [
    {"metric": "binance_staking_provider_locked_egld", "current_value": BINP["locked"], "previous_value": BINP["prev_locked"], "method": "rule_based", "severity": "high",
     "change_pct": 100 * BINP["delta"] / BINP["prev_locked"],
     "description": f"binance_staking {f(BINP['prev_locked'])} -> {f(BINP['locked'])} EGLD ({100*BINP['delta']/BINP['prev_locked']:+.0f}%): one unDelegate of {f(BIN_UNDEL)} EGLD by Binance's de-staking wallet, Oct 12 06:16 UTC. Unbonds ~Oct 21. One call is 94% of the window's unDelegated EGLD."},
    {"metric": "binance_staking_custody_egld", "current_value": cust["balance"], "previous_value": cust["previous"], "method": "z_score", "severity": "medium",
     "average_value": z["custody"].get("mean"), "stddev": z["custody"].get("stddev"), "z_score": zz("custody"), "change_pct": 100 * cust["delta"] / cust["previous"],
     "description": f"Custody +{f(cust['delta'])} to {f(cust['balance'])} from one Binance.com hot-wallet send (Oct 12 10:22). Intra-entity; the z-score ({zz('custody'):+.2f}) understates it because the baseline includes the pre-halt de-staking legs."},
    {"metric": "egld_price_usd", "current_value": price, "previous_value": M["prev_price"], "method": "z_score", "severity": z["price"].get("severity", "low"),
     "average_value": z["price"].get("mean"), "stddev": z["price"].get("stddev"), "z_score": zz("price"), "change_pct": pc,
     "description": f"{pc:+.2f}% in {LIVE_DAYS:.1f} days while BTC {M['btc_wow']:+.2f}% and ETH {M['eth_wow']:+.2f}%; z={zz('price'):+.2f}. Small, but the third window in a row that EGLD trailed BTC."},
    {"metric": "mega_whale_balance_egld", "current_value": bid["mega_bal"], "previous_value": bid["mega_prev"], "method": "rule_based", "severity": "medium",
     "change_pct": 100 * bid["mega_delta"] / bid["mega_prev"],
     "description": f"+{f(bid['mega_delta'])} via Coinbase's routing wallet minutes after Unknown Whale B deposited {f(WHALE_B_OUT)} at Coinbase (Oct 10 22:32-22:55). A Coinbase-intermediated whale-to-whale leg (April pattern), the Mega Whale's first gain in ten weeks."},
    {"metric": "korea_premium_pct", "current_value": PREM, "previous_value": PREM_PREV, "method": "rule_based", "severity": "medium",
     "change_pct": 100 * (PREM - PREM_PREV) / PREM_PREV,
     "description": f"Upbit premium {PREM:.1f}% from {PREM_PREV:.1f}% with UPbit withdrawals closed; Upbit {UP_SHARE:.0f}% of global volume (from {UPSH_PREV:.0f}%)."},
    {"metric": "dex_volume_24h_egld", "current_value": bid["dexvol_egld"], "previous_value": bid["prev_dexvol_egld"], "method": "z_score", "severity": z["dexvol"].get("severity", "low"),
     "average_value": z["dexvol"].get("mean"), "stddev": z["dexvol"].get("stddev"), "z_score": zz("dexvol"),
     "change_pct": 100 * (bid["dexvol_egld"] - bid["prev_dexvol_egld"]) / bid["prev_dexvol_egld"],
     "description": f"xExchange 24h volume {f(bid['dexvol_egld'])} EGLD ({100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.0f}%), {bid['wegld_usdc_share']:.0f}% WEGLD/USDC; z in dollars {zz('dexvol'):+.2f}."},
    {"metric": "hatom_egld_market_balance", "current_value": df["egld_mm_balance"], "previous_value": df["egld_mm_prev_balance"], "method": "rule_based", "severity": "low",
     "change_pct": 100 * EMM_D / df["egld_mm_prev_balance"],
     "description": f"Hatom's EGLD money market {EMM_D:+,.0f} EGLD (second window of outflows); {HMM['redeem_calls']} redeem calls and 0 liquidations since Oct 5."},
    {"metric": "cex_spot_volume_7d_egld", "current_value": BOOK["spot_volume_7d_egld"], "previous_value": BOOK["spot_volume_prior_7d_egld"], "method": "rule_based", "severity": "low",
     "change_pct": 100 * (BOOK["spot_volume_7d_egld"] - BOOK["spot_volume_prior_7d_egld"]) / BOOK["spot_volume_prior_7d_egld"],
     "description": f"7-day CEX spot volume {f(BOOK['spot_volume_7d_egld']/1e6,2)}M EGLD, from {f(BOOK['spot_volume_prior_7d_egld']/1e6,2)}M."},
]

R["trend_indicators"] = {
    "accelerating_exchange_outflows": [],
    "validator_movements": {"providers_joining": 0, "providers_leaving": 0, "net_provider_change": 0, "notable_joiners": [],
                            "notable_leavers": [], "note": f"No joins or deregistrations. binance_staking shrank {f(abs(BINP['delta']))} but stays registered with 50 nodes."},
    "token_supply_events": [
        {"identifier": "USDC-c76f1f", "name": "WrappedUSDC", "event": "burn", "supply_previous": str(int(usdc["prev"])), "supply_current": str(int(usdc["supply"])),
         "change_pct": usdc["pct"], "description": f"{f(USDC_BURN)} USDC redeemed in {LIVE_DAYS:.1f} days, under the 50,000 bridge-route line."},
        {"identifier": "USDT-f8c08c", "name": "USDT", "event": "mint", "supply_previous": str(int(usdt["prev"])), "supply_current": str(int(usdt["supply"])),
         "change_pct": usdt["pct"], "description": f"+{f(usdt['supply']-usdt['prev'])} USDT, the first increase after seven declining readings."},
        {"identifier": "HEGLD-d61095", "name": "HEGLD", "event": "burn", "supply_previous": str(int(float(HT['HEGLD-d61095']['prev_supply']))), "supply_current": str(int(float(HT['HEGLD-d61095']['supply']))),
         "change_pct": HT["HEGLD-d61095"]["supply_pct"], "description": "Suppliers redeemed EGLD from Hatom's money market; no liquidations."}],
    "consecutive_streaks": [
        {"metric": "egld_vs_btc", "direction": "down", "weeks": 3, "cumulative_change_pct": None,
         "interpretation": f"EGLD has trailed BTC in three consecutive windows (run #28 to #30; this one {EGLD_VS_BTC:+.1f}pp)."},
        {"metric": "staked_ratio", "direction": "flat", "weeks": 1, "cumulative_change_pct": 100 * (M["sr"] - M["sr_prev"]) / M["sr_prev"],
         "interpretation": f"The four-run decline paused at {100*M['sr']:.2f}%, but only because Binance's {f(BIN_UNDEL)} is still counted as staked until it unbonds."},
        {"metric": "total_delegators", "direction": "flat", "weeks": 18, "cumulative_change_pct": -1.2, "interpretation": f"{sk['users_delta']:+,} to {f(sk['users'])}. The base rate."},
        {"metric": "provider_operator_fee_selling", "direction": "flat", "weeks": 18, "cumulative_change_pct": 0.0, "interpretation": "Eighteen runs with zero exchange destinations from sampled operator wallets."},
        {"metric": "mega_whale_balance", "direction": "flat", "weeks": 10, "cumulative_change_pct": 100 * bid["mega_delta"] / bid["mega_prev"], "interpretation": "Streak broken: +120,172 via Coinbase after nine flat weeks."}],
    "regime_shifts": [
        {"metric": "exchange_rail_state", "before_value": 0.0, "after_value": round(len(OPEN) / max(1, len([k for k in VEN if k not in _NONVENUE])), 2),
         "description": f"Coinbase (Oct 10) and Bybit (Oct 12) joined Binance.com, Gate.io and Crypto.com: {len(OPEN)} of {len([k for k in VEN if k not in _NONVENUE])} tracked venues move EGLD both ways. UPbit remains closed for withdrawals. Promote when UPbit opens both ways."},
        {"metric": "binance_staking_allocation", "before_value": BINP["prev_locked"], "after_value": BINP["locked"],
         "description": f"CANDIDATE: Binance is moving stake out of its delegation provider ({f(BIN_UNDEL)} unDelegated) while topping up its custody wallet (+{f(BIN_TO_CUSTODY)}). If the unbonded EGLD lands in custody around Oct 21, this is a re-allocation, not supply."},
        {"metric": "exit_route", "before_value": 1.0, "after_value": 0.0,
         "description": "Not promoted. Last week's CEX-route candidate had no exits to test this window (every large withdraw re-staked or held)."}]}

R["watch_list"] = [
    {"item": "BINANCE UNDELEGATION - 320,002 EGLD unbonds ~Oct 21", "weeks_on_list": 1,
     "reason": f"Called Oct 12 06:16 UTC by erd1r3w62vq... Does it go to custody (re-allocation), back into delegation, or to the hot wallet? PRE-COMMITTED (binance-undelegation-destination)."},
    {"item": "UPBIT CAUTION REVIEW Oct 19-23 and the KOREA PREMIUM", "weeks_on_list": 4,
     "reason": f"Premium {PREM:.1f}% (from {PREM_PREV:.1f}%), {UP_SHARE:.0f}% of global volume; UPbit received {UPBIT_DEP_N} deposits and made no withdrawals. korea-premium-arbitrage not evaluable until >= 20 distinct depositors."},
    {"item": "COINBASE - reopened Oct 10 with a whale-to-whale leg", "weeks_on_list": 1,
     "reason": f"Whale B -> Coinbase -> Mega Whale {f(MEGA_IN)} EGLD. Watch for further routing-wallet transfers and whether Whale B ({f(wc.get('erd1at3jm3xvzxhdgt4f695l7l2f6r0tpkqjnemfpc0raam5e9xtjuqqs6fkul', {}).get('balance_current_egld', 173195))} EGLD) keeps feeding it."},
    {"item": "BINANCE.COM CUSTOMER FLOW", "weeks_on_list": 2,
     "reason": f"Net {BIN_EXT_PER_DAY:+,.0f} EGLD/day of customer deposits over the window; hot wallet {f(cust['hot_balance'])}. binance-deposit-persistence resolved as predicted; keep the daily series."},
    {"item": "OTC PIPELINE", "weeks_on_list": 30,
     "reason": f"Desk gross {f(otc['gross_out'])}, no UPbit reload, desks {f(otc['desk_bal'])}. PRE-COMMITTED (otc-pipeline-resumption)."},
    {"item": "CROSS-VENUE ARBITRAGE WALLETS", "weeks_on_list": 1,
     "reason": "erd1d2anjjha..., erd13sytuz92..., erd1reh7sy2c... cycling Binance.com / Bybit / Gate.io. Their volume will inflate venue flows; net them out before reading exchange flow."},
    {"item": "erd1a6lte0 - probable exchange hot wallet woke up", "weeks_on_list": 5,
     "reason": f"{CEN['erd1a6lte0']['inbound_txs']} inbound from {CEN['erd1a6lte0']['distinct_senders']} senders in the window after weeks idle."},
    {"item": "HATOM EGLD MARKET", "weeks_on_list": 2,
     "reason": f"{EMM_D:+,.0f} EGLD again; supplier redemptions, no liquidations."},
    {"item": "EXPLOIT WALLET AND POISONING RING", "weeks_on_list": 5,
     "reason": f"Incident addresses hold {HR['invalid_total_egld']:.2f} EGLD; poisoning operator {PR['operator_out_7d']} dust txs in the window, zero hits above dust."},
]

# ---------------------------------------------------------------------------
prior = {t["id"]: t for t in r26["pre_committed_tests"]}
tests = [t for t in r26["pre_committed_tests"] if t["status"] == "resolved"]


def resolve(tid, outcome, measured, resolution):
    t = dict(prior[tid]); t.update({"status": "resolved", "outcome": outcome, "resolved_in_run": 30, "measured_value": measured, "resolution": resolution}); return t


tests.append(resolve("binance-deposit-persistence", BIN_RESULT,
    f"window {LIVE_DAYS:.1f} days: deposits {f(BIN_DEP)}, customer withdrawals {f(BIN_WD_EXT)} (excluding the {f(BIN_TO_CUSTODY)} internal hot -> custody send), net {BIN_EXT_NET:+,.0f} = {BIN_EXT_PER_DAY:+,.0f} EGLD/day; per day " + ", ".join(f"{d_[5:]} {v_['dep_egld']-v_['wd_egld']:+,.0f}" for d_, v_ in BD.items()) + " (raw, Oct 12 includes the custody send)",
    "Deposits exceeded customer withdrawals on every full day since the reopening, by more than the +10,000/day line over the window. The raw hot-wallet figure (Oct 12: -145K) is the internal custody top-up, which the test's 'customer flow' reading must exclude. Caveat: the largest single deposit (15,179) was an arbitrage leg from Gate.io, so part of the inflow is cross-venue churn rather than holders selling."))
tests.append(resolve("exit-route-cex", "inconclusive",
    f"{EXS['calls']} withdraw calls > 3,000 EGLD: internal {f(EXR.get('internal',{}).get('egld',0))} (Crypto.com sweep), re-delegated {f(EXR.get('re-delegate',{}).get('egld',0))}, held {f(EXR.get('held',{}).get('egld',0))}, to CEX 0, to DEX/bridge 0; USDC burn {f(USDC_BURN)} (< 50,000)",
    "Neither branch is met in substance: 0% went to a CEX, but nothing went through the DEX or bridge either. The population of large exits was near zero this window, so the claim was not tested. Binance's 320,002 EGLD unDelegate is an exchange's own stake, not a delegator exit, and is tested separately."))
tests.append(resolve("unknown-whale-i-is-exchange", "against",
    f"run #30: {CEN['Unknown Whale I']['inbound_txs']} inbound txs and 0 distinct senders in the window, with Binance.com, Coinbase, Bybit and Gate.io all moving EGLD both ways",
    "Past its run #28 deadline, which was extended only because exchange rails were closed. With four major venues open it received nothing: < 50 distinct senders, so the operator-inventory reading stands and the hub history is not re-attributed."))
for tid, note in [("delivery-price-relevance-2", f"run #30: desk gross {f(otc['gross_out'])} EGLD, nowhere near the 300,000 net one-way bar; UPbit withdrawals still closed. Not evaluable."),
                  ("korea-premium-arbitrage", f"run #30: premium {PREM:.1f}%; UPbit received {UPBIT_DEP_N} deposits ({f(UPBIT_DEP)} EGLD), under the 20 distinct-sender bar. Not evaluable."),
                  ("otc-pipeline-resumption", f"run #30 ({LIVE_DAYS:.1f}-day window): desk gross {f(otc['gross_out'])} EGLD, no UPbit reload, desks {f(otc['desk_bal'])}. Under the 20,000 partial line.")]:
    t = dict(prior[tid]); t.update({"status": "open", "measured_value": note, "resolution": None}); tests.append(t)


def new(tid, claim, threshold, branches, measured):
    return {"id": tid, "registered_in_run": 30, "claim": claim, "threshold": threshold, "branches": branches,
            "status": "open", "outcome": None, "resolved_in_run": None, "measured_value": measured, "resolution": None}


tests += [
    new("binance-undelegation-destination", "Binance's 320,002 EGLD unDelegate (Oct 12) is a re-allocation into its staking custody, not supply for sale.",
        "At the first run after the unbond matures (~Oct 21; run #31 or #32): of the EGLD withdrawn by erd1r3w62vq..., > 70% reaching Binance Staking custody or re-delegated = re-allocation; > 30% reaching the Binance.com hot wallet and custody not up by at least that much = supply; otherwise no conclusion. Not withdrawn by run #32 = not evaluable",
        [{"condition": "> 70% to custody or re-delegated", "reading": "re-allocation"},
         {"condition": "> 30% to hot wallet, custody not up", "reading": "supply"},
         {"condition": "otherwise", "reading": "no conclusion"}],
        f"run #30: unDelegated {f(BIN_UNDEL)} at 06:16 UTC Oct 12; same morning the hot wallet sent {f(BIN_TO_CUSTODY)} to custody ({f(cust['balance'])})."),
    new("mega-whale-coinbase-leg", "The Mega Whale's +120,172 EGLD is a Coinbase-intermediated transfer from Unknown Whale B, not a new buyer.",
        "By run #32: Whale B's balance falls by >= 50,000 more while the Mega Whale rises by a similar amount through the Coinbase routing wallet = bilateral OTC pattern confirmed; the Mega Whale receives >= 50,000 via Coinbase with no matching Whale B deposit = independent buying; neither = no conclusion",
        [{"condition": "matched Whale B -> Coinbase -> Mega Whale legs", "reading": "bilateral OTC"},
         {"condition": "Mega Whale inflow without a Whale B leg", "reading": "independent buying"},
         {"condition": "neither", "reading": "no conclusion"}],
        f"run #30: Whale B sent {f(WHALE_B_OUT)} at 22:32 Oct 10, received {f(WHALE_B_BACK)} back over two days; Mega Whale +{f(MEGA_IN)} at 22:35-22:55."),
]
resolved = [t for t in tests if t.get("resolved_in_run") == 30]
as_pred = sum(1 for t in resolved if t["outcome"] == "as_predicted")
R["pre_committed_tests"] = tests

# ---------------------------------------------------------------------------
R["meta_learning"] = {
    "run_number": 30,
    "endpoints_that_worked": status["ok"],
    "endpoints_that_failed": [f"NONE with data missing. {D.get('_n_429', 0)} HTTP 429s; 0 paged errors; 0 API errors. The first collector launch stalled ~5h with no output and was re-run."],
    "api_quirks": [
        "A LONG-RUNNING COLLECTOR WITH BUFFERED STDOUT IS INDISTINGUISHABLE FROM A HUNG ONE: run it with python3 -u, or the log stays empty until exit. The first launch this run sat ~5 hours at 3 seconds of CPU (host sleep is the likely cause) and had to be killed.",
        "A ZERO-VALUE withdraw OR claimRewards CALL TO A STAKING CONTRACT IS THE EXIT CALL ITSELF, not a re-delegation: the first version of the exit-route scan classified the withdraw hop as 're-delegate'. Filter those functions out of next-hop lists.",
        "AN EXCHANGE'S OWN HOT -> CUSTODY MOVE CAN DOMINATE A DAY'S 'WITHDRAWALS': Binance.com's Oct 12 raw withdrawals (187,532) were 86% one internal send. Net intra-entity transfers before reading customer flow."],
    "data_gaps": [
        "No public note found for Coinbase's or Bybit's native-network reopening; states inferred from chain data (no web search this run).",
        "The 7-day delegator reward window overlaps run #29's.",
        "Kraken has no tracked address.",
        "Hatom UTK Money Market and OneDex Launchpad still fail bech32 validation."],
    "key_findings": [
        f"Binance unDelegated {f(BIN_UNDEL)} EGLD from binance_staking on Oct 12 (unbonds ~Oct 21) and moved {f(BIN_TO_CUSTODY)} hot -> custody the same morning.",
        f"Binance.com customer flow {BIN_EXT_PER_DAY:+,.0f} EGLD/day: binance-deposit-persistence as predicted.",
        f"Coinbase reopened Oct 10 with Whale B -> Coinbase -> Mega Whale ({f(MEGA_IN)}); Bybit reopened Oct 12.",
        "No large delegator exit reached a CEX; exit-route-cex inconclusive.",
        f"EGLD {pc:+.2f}% vs BTC {M['btc_wow']:+.2f}%; Upbit premium {PREM:.1f}%.",
        f"Hatom EGLD market {EMM_D:+,.0f}: supplier redemptions, zero liquidations."],
    "action_items_from_previous": len(r26["meta_learning"]["recommendations_for_next_run"]),
    "action_items_completed_detail": [
        "BINANCE FIRST - done: per-day value-bearing deposits/withdrawals since Oct 9 08:04 (targeted trace pass); binance-deposit-persistence resolved; the three funder wallets checked (none re-deposited at scale).",
        "EXIT-ROUTE SCAN, collector side - done: every withdraw > 3,000 EGLD scanned and classified, sender checked against known-addresses (Crypto.com sweep tagged internal); exit-route-cex resolved inconclusive.",
        "OTC desk terminal erd1y27r22... - done: nonce 1, holds 5,836 EGLD, a holder. No UPbit reload in the window.",
        "Upbit premium and volume share series - done (18.8%, Upbit 18% of volume).",
        "Hatom EGLD market - done: 46 redeem calls, 0 liquidations since Oct 5; suppliers, not liquidations.",
        "Monday cadence - done (window labelled ~2.7 days everywhere, short-window flows kept out of weekly baselines)."],
    "methodology_changes": [
        "EXIT-ROUTE SCAN IS NOW COLLECTOR-SIDE (trace_run30.py section 5): every withdraw > 3,000 EGLD, next hop classified cex / bridge / re-delegate / dex-defi / held / internal, zero-value admin calls excluded.",
        "INTRA-ENTITY NETTING FOR RAIL READINGS: venue withdrawals are read net of the venue's own sends to its custody/staking wallets before any deposit-persistence or customer-flow claim.",
        "Run long collectors unbuffered (python3 -u) and watch the log, not the process."],
    "new_addresses_discovered_detail": [
        "erd124tc2z7gzk0sg6uu4lequvwnevhd8jx0casskhwzf447zcl3at9sd6m3jz - received Binance's 6,760 EGLD of claimed binance_staking rewards and deposited them to Binance.com within 20 minutes (Binance rewards pass-through)",
        "erd1d2anjjhad4xlcrcu8jkk99yhrflsg5skavxqpkxwamxq80lmmglqzw605j - cross-venue wallet: withdrew 14,315 from Binance.com and 12,792 from Bybit, deposited 8,992 at Gate.io",
        "erd1y27r22e4svp6g985ednf0nnd383pq2tmhkkzf3g58wems07kgc5stex2ne - OTC desk terminal (Oct 6), nonce 1, holds 5,836 EGLD"],
    "action_items_completed": 6,
    "new_addresses_discovered": 3,
    "most_valuable_insight": (
        f"The window's two largest flows were Binance moving its own EGLD: {f(BIN_UNDEL)} unDelegated from its provider and {f(BIN_TO_CUSTODY)} sent hot -> custody, hours apart. Read raw, they look like a 320K unstaking exit and a 125K hot-wallet drain; netted, Binance.com customers deposited {BIN_EXT_PER_DAY:+,.0f} EGLD/day and the question becomes where the unbonded stake lands on Oct 21."),
    "top_recommendation": "RUN #31 FIRST: watch erd1r3w62vq... for the withdraw of the 320,002 EGLD (matures ~Oct 21) and trace it one hop (binance-undelegation-destination).",
    "recommendations_for_next_run": [
        "BINANCE UNBOND: if run #31 lands after Oct 21, trace the 320,002 EGLD withdraw from erd1r3w62vq... one hop (custody / re-delegate / hot wallet); otherwise confirm it is still pending.",
        "UPBIT Oct 19-23 decision: count distinct UPbit depositors; korea-premium-arbitrage becomes evaluable at >= 20.",
        "Net cross-venue arbitrage wallets (erd1d2anjjha, erd13sytuz92, erd1reh7sy2c) out of venue flows before reading exchange net flow; label them in known-addresses if they persist.",
        "Coinbase routing wallet: watch for further Whale B -> Coinbase -> Mega Whale legs (mega-whale-coinbase-leg).",
        "Run a full 7-day window (Oct 12 -> Oct 19) so flows return to the weekly baselines.",
        "Add a web check for Coinbase/Bybit/Upbit EGLD network notices (none was run this time)."],
    "dashboard_feature_suggestions": [
        {"title": "Intra-entity netting view for exchange flows",
         "motivation": f"Binance.com's raw Oct 12 withdrawals were {f(BD['2026-10-12']['wd_egld'])} EGLD, {100*BIN_TO_CUSTODY/BD['2026-10-12']['wd_egld']:.0f}% of it one send to Binance's own custody wallet. The current exchange-flow bars show the raw hot-wallet drop (-125K) and invite a wrong reading.",
         "suggested_visualization": "stacked daily bars per venue split into customer deposits, customer withdrawals and internal transfers (hatched), with entity net as a line",
         "data_already_available": True, "data_source": "whale_intelligence.exchange_flows.rail_status plus run30_traces.binance_daily (needs an internal-transfer field per day)", "priority": "high"},
        {"title": "Staking-to-custody flow for exchange stake",
         "motivation": f"Binance unDelegated {f(BIN_UNDEL)} from binance_staking while custody rose {f(BIN_TO_CUSTODY)}; the dashboard has no view that links provider stake, unbonding queue and custody balance for one entity over time.",
         "suggested_visualization": "multi-week stacked area per exchange entity: delegated stake, unbonding (with maturity markers), custody, hot wallet",
         "data_already_available": False, "data_source": "providers history from data/collected archive + unbonding_pool + exchange_balances series", "priority": "medium"}],
    "dashboard_suggestions_followup": [
        {"title": "Funding-chain graph for CEX deposits", "status": "pending",
         "note": "Not built. This window's largest deposits were arbitrage legs (Gate.io -> Binance.com) rather than linked holders, so priority drops to medium; still useful once arbitrage wallets are labelled."},
        {"title": "Price vs venue-flow overlay (hourly)", "status": "pending",
         "note": "Not built. Coinbase (Oct 10 22:26) and Bybit (Oct 12 10:18) reopenings are exactly the markers it would show; data needs an hourly rail query."}],
    "withdrawn_claims": [],
}

rep = {k: R[k] for k in ["metadata", "executive_summary", "network_health", "whale_intelligence", "staking_intelligence", "token_activity",
                         "defi_activity", "anomalies", "trend_indicators", "watch_list", "meta_learning", "pre_committed_tests"]}
json.dump(rep, open(f"{REPO}/reports/{RD}.json", "w"), indent=1, default=str)
print("report written", len(json.dumps(rep, default=str)), "bytes")
print(f"tests resolved this run {len(resolved)}, as_predicted {as_pred}, open {sum(1 for t in tests if t['status']=='open')}")
print("PREM", round(PREM, 1), "UP_SHARE", round(UP_SHARE, 1), "OPEN", OPEN, "DEPONLY", DEPONLY)
