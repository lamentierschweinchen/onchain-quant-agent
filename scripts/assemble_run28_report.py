#!/usr/bin/env python3
"""Run #28 stage 2: assemble reports/2026-10-05.json from derived.json + snapshot.

The week's defining facts: the first full live week since the Sep 19 halt. Exchange
rails reopened PARTIALLY and venue by venue (Tokero Sep 28-29, Crypto.com Oct 2 - corrected from Sep 29,
Binance.com deposit-side only from Sep 29, Bitget Oct 3-4, Gate.io Oct 4); UPbit,
Bybit, Coinbase, MEXC and KuCoin moved no EGLD. The first post-reopen pipeline
delivery was stranded pre-halt router inventory hitting Gate.io at its 23:00 sweep.
The largest post-restart unstaker exited through the DEX and the Ethereum bridge,
at a ~10% discount to CEX prices. Exchange/OTC readings are PARTIAL-RAIL readings
and stay out of the baselines.
"""
import json
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD = "2026-10-05"
O = json.load(open("/tmp/run28w/derived.json"))
D = json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev = json.load(open("/tmp/run28w/previous_run27.json"))
status = json.load(open("/tmp/run28w/status.json"))
beh = json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
r26 = json.load(open(f"{REPO}/reports/2026-09-28.json"))   # previous report (name kept for the reused blocks)
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
LIVE_DAYS = 7.0
EGLD_VS_BTC = pc - M["btc_wow"]
tick = D["cg_tickers"]["tickers"]
up = next(t for t in tick if t["market"]["name"] == "Upbit")
bn = next(t for t in tick if t["market"]["name"] == "Binance" and t["target"] == "USDT")
PREM = 100 * (up["converted_last"]["usd"] - bn["converted_last"]["usd"]) / bn["converted_last"]["usd"]
UP_SHARE = 100 * up["converted_volume"]["usd"] / BOOK["all"]["volume_24h_usd"]
PREM_PREV = prev["exchange_orderbook_closed_book_run27"]["korea_premium_pct"]
UPSH_PREV = prev["exchange_orderbook_closed_book_run27"]["upbit_share_of_volume_pct"]
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
    v["state"] = ("open" if v["in_txs"] and v["out_txs"] else "deposit_only" if v["in_txs"] else "withdrawal_only" if v["out_txs"] else "closed")
    VEN[lbl] = v
OPEN = [k for k, v in VEN.items() if v["state"] == "open"]
DEPONLY = [k for k, v in VEN.items() if v["state"] == "deposit_only"]
CLOSED_MAJOR = [k for k in ("UPbit", "Bybit", "Coinbase", "MEXC", "KuCoin", "Bitfinex") if VEN.get(k, {}).get("state") == "closed"]
RAIL_EGLD_IN = sum(v["in_egld"] for v in VEN.values()); RAIL_EGLD_OUT = sum(v["out_egld"] for v in VEN.values())

# ---- the stranded-router delivery at Gate.io's reopen ----
GATE = "erd1p4vy5n9mlkdys7xczegj398xtyvw2nawz00nnfh4yr7fpjh297cqtsu7lw"
GR = D["run28_traces"]["gate_routers"]
ROUTER_DELIV = sum(t["egld"] for r in GR.values() for t in r["out"] if t["to"] == GATE and t["ts"] >= D["_period"]["window_start_ts"])
ROUTER_PREHALT_IN = sum(t["egld"] for r in GR.values() for t in r["in"] if 1790200000 > t["ts"] >= 1790380000 - 86400 * 2 and t["egld"] > 1)
ROUTER_N = len(GR)
# ---- the DEX + bridge exit ----
U = D["run28_traces"]["undelegator"]
U_ADDR = "erd155j9c36hp5dkqp7u5gwjek00g2axermvqdzk3j7mpk9k8yunpy4s9fpq8c"
U_SOLD = sum(t["egld"] for t in U["out"] if t["fn"] in ("xo", "composeTasks"))
U_SOLD_SEP29 = sum(t["egld"] for t in U["out"] if t["fn"] in ("xo", "composeTasks") and t["ts"] < 1790800000)
U_SOLD_OCT4 = U_SOLD - U_SOLD_SEP29
U_BRIDGED_USDC = 111274.24   # 5 xBridge unwrapTokenCreateTransaction calls, USDC-c76f1f -> ETHUSDC, decoded from tx actions
U_BRIDGED_SEP29 = 37955.70; U_BRIDGED_OCT4 = U_BRIDGED_USDC - U_BRIDGED_SEP29
U_PX = U_BRIDGED_USDC / U_SOLD
U_PX_SEP29 = U_BRIDGED_SEP29 / U_SOLD_SEP29; U_PX_OCT4 = U_BRIDGED_OCT4 / U_SOLD_OCT4
U_DISC = 100 * (U_PX / price - 1)
U_ETH_DEST = "0x0acdff4c5927dd7845b1a0e104e820104723d653"
USDC_BURN = usdc["prev"] - usdc["supply"]
POST_EXIT = "against"

R = {}
R["metadata"] = {
    "report_date": RD, "period_start": "2026-09-28", "period_end": RD,
    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "egld_price_usd": price, "btc_price_usd": M["btc"], "eth_price_usd": M["eth"],
    "run_number": 28,
    "data_sources_ok": status["ok"] + [
        "follow-up pass: 2 provider scans lost to HTTP 429 re-paged in full (384 and 212 txs), 393 withdraw calls decoded, poisoning lookalikes re-scanned (0 errors)",
        "rail check (new script rails_run28.py): value-bearing EGLD deposits/withdrawals per tracked exchange wallet since restart 2, paginated",
        "targeted traces (trace_run28.py): largest post-restart unstaker, the five OTC Desk->Gate.io routers, four largest unlabelled movers",
        "xBridge decode: 5 unwrapTokenCreateTransaction calls (USDC -> Ethereum) from the unDelegator",
        "post-publication correction: exchange-internal Crypto.com flows excluded from rail counts (Crypto.com first customer-like flows Oct 2, not Sep 29)",
        "public sources: exchange status (Kraken reopened Oct 1; Upbit caution designation Sep 21, review Oct 19-23; Binance native network closed, BEP-20 only) and the absence of a MultiversX technical incident report as of Oct 3"],
    "data_sources_failed": status["failed"],
    "data_sources_recovered": [
        "LIVENESS GATE PASSED: every shard within 6 s of real time; the window is a full 7 live days for the first time since the Sep 19 halt",
        f"{D.get('_n_429', 40)} HTTP 429 responses in the main pass despite the new global 4 req/s budget; 2 paged provider scans and 4 single calls were affected, all recovered in the follow-up",
        f"delegator reward behaviour sampled {ag['providers_sampled']} of {ag.get('providers_requested', 8)} providers" + ("" if ag["providers_sampled"] == 8 else " after one retry; the two lost to HTTP 429 are excluded, not counted as empty")]}

R["executive_summary"] = [
    {"category": "whale", "severity": "high", "finding":
     f"EXCHANGE RAILS REOPENED VENUE BY VENUE, AND THE BIG ONES ARE STILL SHUT. In the first full live week since the halt, EGLD moved both ways at {', '.join(OPEN)}; Binance.com's hot wallet took {VEN['Binance.com']['in_txs']} deposits ({f(VEN['Binance.com']['in_egld'])} EGLD) and sent nothing. "
     f"{', '.join(CLOSED_MAJOR)} moved no EGLD at all. Tracked exchange balances rose {ex['net']:+,.0f} EGLD, {f(VEN['Gate.io']['in_egld'])} of it at Gate.io. "
     "This is a partial-rail week: the readings are recorded but stay out of the baselines until Binance withdrawals and UPbit reopen."},
    {"category": "whale", "severity": "high", "finding":
     f"THE PIPELINE'S FIRST POST-HALT DELIVERY WAS STRANDED INVENTORY. Gate.io reopened deposits on Oct 4, and at its 23:00 UTC sweep {ROUTER_N} 'OTC Desk->Gate.io' routers delivered {f(ROUTER_DELIV)} EGLD in two minutes. "
     "The routers had been loaded by the UPbit OTC desk and the Distribution wallet on Sep 18-19, hours before the halt, and had sat on that EGLD for 16 days. "
     f"The desks themselves sent nothing all week and still hold {f(otc['desk_bal'])}. The programme has not restarted; its pre-halt tail has just cleared."},
    {"category": "staking", "severity": "high", "finding":
     f"THE LARGEST POST-RESTART EXIT WENT OUT THROUGH THE DEX AND THE BRIDGE. The wallet that unDelegated 8,888 EGLD from each of three providers on Sep 24 withdrew it as it matured and sold {f(U_SOLD)} EGLD through the XOXNO aggregator and xExchange (Sep 29 and Oct 4). "
     f"It bridged the proceeds to Ethereum as {f(U_BRIDGED_USDC)} USDC, an average ${U_PX:.2f} per EGLD, {abs(U_DISC):.0f}% below this week's ${price:.2f}. That one wallet accounts for {100*U_BRIDGED_USDC/USDC_BURN:.0f}% of the week's {f(USDC_BURN)} USDC supply burn. "
     "With CEX deposits closed, exits route through on-chain liquidity and pay for it."},
    {"category": "staking", "severity": "medium", "finding":
     f"THE EXIT WAVE DID NOT CONTINUE. Over a full 7-day window {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD, under the 90,000 bar. The pre-committed post-restart-exit-wave test resolves 'one-off burst' (against the wave claim), and last week's ~117K pace was the restart, not a trend. "
     f"Withdrawals did run hot: {O['withdraw_calls']} calls returned {f(WD.get('egld_returned_total', 0))} EGLD as the Sep 24-25 queue matured. Staked EGLD {M['staked_chg']:+,.0f} and the staked ratio {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp) slipped below the 46.30% floor of run #25's band, while delegation TVL rose {sk['delta_locked']:+,.0f}."},
    {"category": "network", "severity": "medium", "finding":
     f"THE KOREA PREMIUM COLLAPSED WHILE UPBIT STAYED SHUT. Upbit trades at ${up['converted_last']['usd']:.2f} against ${bn['converted_last']['usd']:.2f} on Binance, an {PREM:.1f}% premium, down from {PREM_PREV:.1f}%. Its share of global EGLD volume fell from {UPSH_PREV:.0f}% to {UP_SHARE:.0f}%. "
     f"No EGLD reached Upbit, so arbitrage did not close the gap; the premium shrank because Korean buyers paid less of it (tested as upbit-premium-decay). Upbit has EGLD on a caution designation and will decide on Oct 19-23 whether to keep trading it. "
     f"EGLD {pc:+.2f}% against BTC {M['btc_wow']:+.2f}% ({EGLD_VS_BTC:+.1f}pp), and the 7-day CEX spot volume fell to {f(BOOK['spot_volume_7d_egld']/1e6, 2)}M EGLD from {f(BOOK['spot_volume_prior_7d_egld']/1e6, 2)}M."},
    {"category": "defi", "severity": "low", "finding":
     f"DEFI QUIETLY TOOK THE EXCHANGE VOLUME. xExchange 24h volume ${f(bid['dexvol'])} ({f(bid['dexvol_egld'])} EGLD, {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.0f}% in EGLD), {bid['wegld_usdc_share']:.0f}% of it WEGLD/USDC, the pair an exit needs. Hatom lending was flat in EGLD ({hl:+.2f}%) with HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.2f}%; USH {lsd['USH-111e09']['pct']:+.2f}%. "
     f"Bridged dollars kept leaving: USDT {usdt['pct']:+.2f}% and USDC {usdc['pct']:+.2f}%."},
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
               "btc_correlation_note": f"BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%, EGLD {pc:+.2f}%: EGLD trailed BTC by {abs(EGLD_VS_BTC):.1f}pp and gave back part of last week's closed-book outperformance as the Upbit premium compressed from {PREM_PREV:.0f}% to {PREM:.0f}%."},
    "liveness": {"ok": D["liveness_ok"], "latest_block_by_shard": {k: iso(v["timestamp"]) for k, v in D["liveness"].items()},
                 "restart_1_utc": iso(1790181300), "restart_1_stopped_utc": iso(1790182386), "restart_2_utc": iso(1790263800),
                 "live_days_in_window": LIVE_DAYS, "rollback_point_utc": "2026-09-19 06:37:45 UTC"},
    "analysis": (
        f"A FULL LIVE WEEK. Every shard read within 6 seconds of real time at collection, and the chain ran all seven days of the window. Epoch {st['epoch']} ({st['epoch']-pact['epoch']:+d}), "
        f"{f(st['transactions']-pact['total_transactions'])} transactions (~{f(int((st['transactions']-pact['total_transactions'])/LIVE_DAYS))}/day), {f(st['accounts']-pact['total_accounts'])} new accounts. "
        f"Total supply {f(econ['totalSupply'])} ({econ['totalSupply']-pecon['total_supply']:+,}): normal epoch issuance resumed. MultiversX had still not published a technical incident report as of Oct 3, so the chain's own record (a rollback to Sep 19 06:37:45, reconstructed in run #27) is the only account of the recovery.\n\n"
        f"STAKING. Staked EGLD {M['staked_chg']:+,.0f} to {f(econ['staked'])}; ratio {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp), the lowest in the tracked series and just below run #25's 46.30-46.80% band. Network APR {100*econ['apr']:.2f}%.\n\n"
        f"PRICE. EGLD ${price:.2f}, {pc:+.2f}% on the week, against BTC {M['btc_wow']:+.2f}% and ETH {M['eth_wow']:+.2f}%. Last week EGLD beat BTC by 8.3pp inside a closed book. This week, with a few venues open and the Upbit premium halving, it trailed by {abs(EGLD_VS_BTC):.1f}pp. "
        f"Global CEX spot volume over 7 days was {f(BOOK['spot_volume_7d_egld']/1e6, 2)}M EGLD, down {100*(1-BOOK['spot_volume_7d_egld']/BOOK['spot_volume_prior_7d_egld']):.0f}% from the prior week, most of the drop from Upbit. The market is thinner, not busier, as rails reopen.")}


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


INV_SERIES = {**prev["otc_desk_inventory_series"], "run28": round(otc["desk_bal"])}
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
                        "note": "Value-bearing EGLD transactions only (ESDT spam airdrops excluded), and exchange-internal flows excluded: Crypto.com's daily 02:00 sweep to its own staking wallet (erd1uskf6...) and a 0-value 02:00 bot ran before the halt too, and counting them first dated Crypto.com's reopening to Sep 29 (corrected: first customer-like flows Oct 2, 2 withdrawals and 1 large deposit, none since). MEXC's and KuCoin's only transactions since restart are the Sep 24 15:41 replays of Sep 19 transfers. Public status: Kraken reopened Oct 1 (no tracked address); Binance lists the native network closed and withdraws via BEP-20 only."},
        "signal": (f"PARTIAL RAILS. Net exchange flow {ex['net']:+,.0f} EGLD, all of it at the venues that reopened (balance change): " + ", ".join(f"{e2['entity']} {e2['net_flow_egld']:+,.0f}" for e2 in ex["entity"] if e2["net_flow_egld"]) + ". Binance is deposit-only; Crypto.com's customer-like flows were two withdrawals and one deposit, all on Oct 2 (its daily internal staking sweep is excluded from rail counts). " +
                   f"{', '.join(CLOSED_MAJOR)} moved no EGLD. The inflow sign is what a reopening looks like (deposits first, withdrawals later), so it is recorded but not appended to the exchange-flow baseline."),
        "by_exchange": [{"exchange": w["exchange"], "change_egld": w["change_egld"], "pct": w["pct"]} for w in ex["per_wallet"]],
        "entity_netting": [{"entity": e2["entity"], "wallets_count": e2["wallets_count"],
                            "net_flow_egld": e2["net_flow_egld"], "interpretation": entity_interp(e2)} for e2 in ex["entity"]]},
    "dormant_activations": [],
    "exit_routes": {
        "wallet": U_ADDR, "undelegated_sep24_egld": 3 * 8888, "sold_on_dex_egld": U_SOLD,
        "sold_sep29_egld": U_SOLD_SEP29, "sold_oct4_egld": U_SOLD_OCT4,
        "venues": ["XOXNO: Swap Aggregator", "xExchange: Compose Tasks contract"],
        "bridged_usdc": U_BRIDGED_USDC, "bridge": "xBridge: Tokens Wrapper (USDC-c76f1f -> ETHUSDC -> Ethereum)", "ethereum_destination": U_ETH_DEST,
        "effective_price_usd": U_PX, "effective_price_sep29_usd": U_PX_SEP29, "effective_price_oct4_usd": U_PX_OCT4,
        "discount_to_week_close_pct": U_DISC, "share_of_usdc_supply_burn_pct": 100 * U_BRIDGED_USDC / USDC_BURN,
        "remaining_balance_egld": int(U["info"]["balance"]) / 1e18,
        "note": "One wallet, measured end to end: unDelegate (Sep 24) -> withdraw as each leg matured (Pi Staking Sep 29, Star Staking and Vapor Republic Oct 4) -> swap to USDC on chain -> bridge to Ethereum. It keeps 8,889 EGLD delegated at a fourth provider."},
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
        "method_note": "Second weekly read after restart; unchanged. MultiversX had published no technical incident report as of Oct 3."},
    "otc_pipeline": {
        "gross_outbound_egld_7d": otc["gross_out"], "gross_inbound_egld_7d": otc["gross_in"],
        "circular_egld_7d": otc["circular"], "net_one_way_egld_7d": otc["net_one_way"],
        "circular_share_pct": otc["circ_pct"],
        "desk_balance_egld": otc["desk_bal"], "previous_desk_balance_egld": otc["prev_desk"],
        "upbit_reload_egld": otc["upbit_feed"],
        "venue_netting": [{"venue": "Gate.io (router tail, stranded since Sep 18-19)", "desk_to_venue_egld": ROUTER_DELIV, "venue_to_desk_egld": 0.0, "net_egld": ROUTER_DELIV}],
        "router_tail_delivery_egld": ROUTER_DELIV, "router_tail_routers": ROUTER_N,
        "gross_series_egld_7d": {**r26o["gross_series_egld_7d"], "run28": otc["gross_out"]},
        "net_one_way_series_egld_7d": {**r26o["net_one_way_series_egld_7d"], "run28": otc["net_one_way"]},
        "desk_inventory_series_egld": INV_SERIES,
        "circularity_series_pct": {**r26o["circularity_series_pct"], "run28": 0.0},
        "peak_window_renetted": r26o["peak_window_renetted"],
        "backfilled_windows": r26o.get("backfilled_windows", []),
        "wave_window_netting": {**r26o["wave_window_netting"],
            "note": (f"Wave #4 stays closed at 467,107 EGLD one-way (Sep 7 to the halt, frozen labels). Its tail cleared this week: {f(ROUTER_DELIV)} EGLD the desks had pushed into {ROUTER_N} Gate.io routers on Sep 18-19 reached Gate.io at its Oct 4 23:00 sweep. "
                     "That EGLD was already counted as delivered in wave #4 (desk -> Gate.io router resolves to Gate.io), so it is not added again.")},
        "feed_by_parent_venue": [],
        "feeder_backtrace": O["feeder_backtrace"],
        "address_poisoning": [{"address": a, "mimics": v["note"], "nonce": v["nonce"], "dust_txs_30d": v["dust_txs_30d"],
                               "distinct_targets_30d": v["distinct_targets_30d"],
                               "inbound_above_0_01_egld": len(v["inbound_above_0_01_egld"])} for a, v in PZ.items()],
        "series_note": (f"IDLE DESKS, PARTIAL RAILS. The desks sent and received nothing in seven live days and hold {f(otc['desk_bal'])}, the same as the two weeks before. "
                        f"The only pipeline EGLD that moved was the {f(ROUTER_DELIV)} router tail into Gate.io. The UPbit desk's feeder venue (UPbit) is still closed, so the desks have nothing to reload from. Kept out of the baselines.")},
    "demand_instruments": {
        "identifiable_bid_absorbed_egld_7d": 0.0,
        "mega_whale_balance_egld": bid["mega_bal"] or 0.0, "mega_whale_change_egld": bid["mega_delta"],
        "coinbase_routing_balance_egld": bid["cbr_bal"] or 0.0, "coinbase_routing_inflow_egld": 0,
        "coinbase_routing_funder": None, "coinbase_routing_funder_label": "n/a - no inbound this week",
        "weeks_at_zero": 8, "weeks_at_zero_in_last_four": 4, "bid_to_distribution_ratio_pct": 0.0,
        "dex_turnover_ratio_pct": bid["turnover"], "previous_dex_turnover_ratio_pct": bid["prev_turnover"],
        "dex_volume_egld_24h": bid["dexvol_egld"], "previous_dex_volume_egld_24h": bid["prev_dexvol_egld"],
        "pool_tvl_egld": bid["pooltvl_egld"], "previous_pool_tvl_egld": bid["prev_pooltvl_egld"],
        "wegld_usdc_volume_usd": bid["wegld_usdc_vol"], "wegld_usdc_share_of_volume_pct": bid["wegld_usdc_share"],
        "ex_wegld_usdc_volume_usd": bid["ex_wegld_usdc_vol"], "ex_wegld_usdc_volume_egld": bid["ex_wegld_usdc_vol_egld"],
        "dex_volume_status": "evaluable; compared with run #27",
        "absorber_scan": {"terminals_scanned": absb["scanned"],
                          "terminals_retaining_over_half": len(absb["retaining"]),
                          "total_received_from_desks_egld": absb["total_received"],
                          "total_retained_egld": absb["total_balance_held"],
                          "retained_share_pct": 0.0,
                          "verdict": "No desk outbound this week; nothing to scan."},
        "withdrawal_breadth": {"distinct_recipients_raw": br["raw_n"], "total_egld_raw": br["raw_egld"],
                               "distinct_recipients_ex_pipeline": br["ex_n"], "total_egld_ex_pipeline": br["ex_egld"],
                               "pipeline_share_pct": br["pipeline_share"], "top_two_share_pct": br["top_two_share_pct"]},
        "withdrawal_breadth_top": br["top"],
        "exchange_orderbook": {
            "source": "CoinGecko exchange tickers with 2% depth and daily spot volume (third-party). PARTIAL RAILS: Binance withdrawals and UPbit/Bybit/Coinbase transfers closed on chain",
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
    "RAILS, VENUE BY VENUE. The rail check this run counts only transactions that carry EGLD, per tracked exchange wallet since restart 2. "
    + "; ".join(f"{k}: {v['state'].replace('_', ' ')} ({v['in_txs']} in / {v['out_txs']} out" + (f", first deposit {hm(v['first_in'])}" if v['first_in'] else "") + ")" for k, v in VEN.items() if v["state"] != "closed")
    + f". Closed, with no EGLD moved: {', '.join(k for k, v in VEN.items() if v['state'] == 'closed')}. Kraken reopened on Oct 1 according to its status page, but this model tracks no Kraken address. "
    f"The order of reopening matters for reading flows. Deposits come back first, so a reopening week prints an inflow ({ex['net']:+,.0f} EGLD here) that says nothing about demand to sell.\n\n"
    f"THE GATE.IO SWEEP. Gate.io's first EGLD deposits after the halt came at Oct 4 23:00 UTC, and the first {ROUTER_N} were the pipeline's own routers: {f(ROUTER_DELIV)} EGLD within two minutes. "
    "Each router had received a tranche from the UPbit OTC desk or the Distribution wallet between Sep 18 14:21 and Sep 19 05:14, before the rollback point, so the rollback preserved them. Each sweeps to Gate.io at 23:00, and Gate's closed deposits had held them for 16 days. "
    "That is a delivery the desks scheduled before the halt, not a new one. The desks sent nothing all week.\n\n"
    f"THE DEX EXIT. {U_ADDR[:12]}... unDelegated 8,888 EGLD from each of Pi Staking, Star Staking and Vapor Republic on Sep 24, three hours after restart. As each leg matured it withdrew and sold: {f(U_SOLD_SEP29)} EGLD on Sep 29 and {f(U_SOLD_OCT4)} on Oct 4, in 1,000-2,000 EGLD clips through the XOXNO aggregator and xExchange. "
    f"The USDC went straight to the xBridge wrapper and out to one Ethereum address: {f(U_BRIDGED_USDC)} USDC, ${U_PX_SEP29:.2f}/EGLD on Sep 29 and ${U_PX_OCT4:.2f} on Oct 4, against ${price:.2f} on CEX at the close. "
    f"The ~{abs(U_DISC):.0f}% discount is the price of exiting while CEX deposits are closed, paid in pool slippage on a {f(bid['pooltvl_egld'])} EGLD pool base.\n\n"
    f"WHALES. Tiers on the common-address basis ({O['tiers_basis']} wallets): mega {O['tiers']['mega']['net_change_egld']:+,.0f}, large {O['tiers']['large']['net_change_egld']:+,.0f}, mid {O['tiers']['mid']['net_change_egld']:+,.0f}. "
    "The largest unlabelled move was a single 30,000 EGLD transfer between two unlabelled wallets on Sep 30 (erd1ygqnss... to erd1hhvfrw...); the receiver has since sent out only 603 EGLD. "
    "An unlabelled 'Unknown Whale' pair (erd1hl5y4a... and erd1vxa2vk...) passed 12,825 EGLD back and forth and erd1hl5y4a... took about 6,300 EGLD from four other wallets on Oct 5. No holder above 100,000 EGLD moved more than 9,893 EGLD, and those two were team funds receiving epoch distributions.\n\n"
    f"UNKNOWN WHALE I AND erd1a6lte0: {CEN['Unknown Whale I']['inbound_txs']} and {CEN['erd1a6lte0']['inbound_txs']} inbound transactions in seven live days. A hot wallet at a venue that has reopened would be busy; at a closed venue, or for an idle operator, this is what it looks like. Still not evaluable.\n\n"
    f"DEMAND. Binance+Bybit bids within 2% of mid total ${f(bbn)} (from ${f(bbn_prev)}). Upbit's premium is {PREM:.1f}% (from {PREM_PREV:.1f}%) on {UP_SHARE:.0f}% of global volume (from {UPSH_PREV:.0f}%).")
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
                   "fee_pct": mv(ident, "fee") or 0.0, "weeks_in_state": 5,
                   "note": f"FIFTH WEEK AFTER THE FEE REVERSAL: book {mv(ident,'delta'):+,.0f}, users {mv(ident,'users_delta'):+d}. Still losing capital with yield restored."})
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
                          "note": "Zero transitions for a fifth week. Join on contract address, 100% match, no identity changes."},
    "fee_events": [{"provider": i, "fee_from_pct": 100.0, "fee_to_pct": mv(i, "fee") or 0.0, "apr_from_pct": 0.0, "apr_to_pct": mv(i, "apr") or 0.0,
                    "locked_egld": mv(i, "locked"), "locked_wow_egld": mv(i, "delta"), "users": mv(i, "users"),
                    "users_wow": mv(i, "users_delta"), "num_nodes": mv(i, "nodes")} for i in ("egldstakingprovider", "procryptostaking")],
    "unbonding_in_flight": {
        "wallet": ub["wallet"], "total_egld": ub["pending_total"],
        "legs": [{"provider": p["contract"][:10] + "..." + p["contract"][-8:], "amount": p["amount_egld"],
                  "days_to_unbond": p["days_remaining"], "date": "2026-08-14" if p["amount_egld"] < 100000 else "2026-08-15"} for p in ub["pending"]],
        "share_of_delegation_decline_pct": 0.0, "raw_residual_egld": sk["residual"], "corrected_direct_node_egld": None,
        "status": f"RETIRED, SEVENTH WEEK UNMOVED. Balance {f(ub['balance'],2)} EGLD, {f(ub['pending_total'])} unbonded-and-unclaimed.",
        "queue_this_week": {
            "undelegated_egld": sk["undelegated_week"], "distinct_callers": sk["undelegate_callers"],
            "measured_pending_egld": sk["pool_total"], "largest_legs": sk["pool_rows"][:12],
            "withdraw_calls": O["withdraw_calls"], "previous_withdraw_calls": O["prev_withdraw_calls"],
            "withdraw_egld_returned": WD.get("egld_returned_total", 0.0),
            "withdraw_egld_by_provider_top": [{"provider": a, "egld": b} for a, b in wd_top[:8]],
            "undelegated_weekly_pace_egld": UNDEL_PACE, "live_days": LIVE_DAYS,
            "coverage_note": (f"Full-set scan of {sk['providers_scanned']} provider contracts; 2 scans lost to HTTP 429 were re-paged in the follow-up. {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD over a full 7 live days; "
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
            f"COMPOUND RATE {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} reDelegateRewards vs {cvc['claim_count']} claimRewards), from 52.40%. Series: 59.54 / 59.07 / 57.03 / 57.51 / 62.05 / 49.44 / 62.68 / 52.40 / {cvc['compound_pct_of_reward_decisions']:.2f}. Back inside the 57-63% range: last week's dip was the restart, as the two-week rule said to wait for.",
            f"Retail {fates['retail']['total_events']} claims, {fates['retail']['by_count'].get('sold',0)} to a labelled exchange; mid-tier {fates['mid_tier']['total_events']}, {fates['mid_tier']['by_count'].get('sold',0)} sold; institutional {fates.get('institutional',{}).get('total_events',0)}, {fates.get('institutional',{}).get('by_count',{}).get('sold',0)} sold. Partial rails: a 'held' reading at a venue that accepts no deposits is not a choice to hold.",
            f"Sample: {ag['providers_sampled']} of {ag.get('providers_requested',8)} providers on the second attempt (the first lost truststaking and meria to HTTP 429 and was discarded, per the run #25 rule).",
            "PROVIDER OPERATORS DID NOT SELL FEES for a sixteenth consecutive run."]},
    "analysis": (
        f"THE BURST ENDED. A full 7-day scan of {sk['providers_scanned']} provider contracts found that {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD, against 62,093 in last week's 3.7 live days and 73-84K in the two pre-halt weeks. Callers fell from 510 to {sk['undelegate_callers']}. "
        f"The pre-committed post-restart-exit-wave test resolves on its '< 90,000 = one-off burst' branch, so the restart produced a burst of exits and not a sustained wave.\n\n"
        f"THE QUEUE MATURED. {O['withdraw_calls']} withdraw calls (from {O['prev_withdraw_calls']}) returned {f(WD.get('egld_returned_total',0))} EGLD, led by pi-staking {f(wd_top[0][1]) if wd_top else 'n/a'}, vaporrepublic and star_staking, the three providers the largest post-restart exit drew on. "
        f"That exit is traced end to end in whale intelligence: {f(U_SOLD)} EGLD withdrawn, sold on chain and bridged to Ethereum as USDC at ~{abs(U_DISC):.0f}% below the CEX price. Measured pending among the largest callers: {f(sk['pool_total'])} EGLD, most of it 3-10 days from unbonding.\n\n"
        f"THE RATIO AND THE RESIDUAL. Staked EGLD {M['staked_chg']:+,.0f} while delegation TVL rose {sk['delta_locked']:+,.0f} to {f(tl)}, a staked-minus-delegated residual of {sk['residual']:+,.0f}. "
        f"Delegation books gained as unbonding legs left /economics staked first. The staked ratio {100*M['sr']:.2f}% sits just below run #25's 46.30-46.80% band; that test is already resolved, and this is the first print under its floor.\n\n"
        f"COMPOUNDING RECOVERED to {cvc['compound_pct_of_reward_decisions']:.2f}% from 52.40%, so last week's dip does not become a regime candidate. "
        f"DELEGATORS {sk['users_delta']:+,} to {f(sk['users'])}; {sk['gaining']} providers gained and {sk['losing']} lost. meria led inflows ({mv('meria','delta'):+,.0f}); core-block ({mv('core-block','delta'):+,.0f}) and valuestaking ({mv('valuestaking','delta'):+,.0f}) led outflows. Zero deregistration transitions for a fifth week.")}
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
        "volume_status": "evaluable; compared with run #27",
        "mex_pair_depth": {"pair": "MEX/WEGLD", "tvl_usd": xx["mex_pair_depth"]["tvl_usd"], "tvl_egld": xx["mex_pair_depth"]["tvl_egld"],
                           "previous_tvl_egld": xx["mex_pair_depth"]["previous_tvl_egld"], "tvl_egld_wow_pct": xx["mex_pair_depth"]["tvl_egld_wow_pct"],
                           "volume_24h_usd": xx["mex_pair_depth"]["volume_24h_usd"], "trades_24h": xx["mex_pair_depth"]["trades_24h"],
                           "share_of_pool_tvl_pct": xx["mex_pair_depth"]["share_of_pool_tvl_pct"], "depth_rank": xx["mex_pair_depth"]["depth_rank"]},
        "mex_pair_event": r26["token_activity"]["xexchange"]["mex_pair_event"]},
    "analysis": (
        f"THE DEX CARRIED THE EXITS. 24h volume ${f(xx['vol'])} ({f(bid['dexvol_egld'])} EGLD) against ${f(xx['prev_vol'])} ({f(bid['prev_dexvol_egld'])} EGLD) last week, {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.0f}% in EGLD terms. "
        f"WEGLD/USDC is {bid['wegld_usdc_share']:.0f}% of it; everything else traded {f(bid['ex_wegld_usdc_vol_egld'])} EGLD. Turnover {bid['turnover']:.2f}% of pool TVL (from {bid['prev_turnover']:.2f}%). "
        f"Pool TVL {f(bid['pooltvl_egld'])} EGLD ({100*(bid['pooltvl_egld']-bid['prev_pooltvl_egld'])/bid['prev_pooltvl_egld']:+.1f}% in EGLD). One wallet sold {f(U_SOLD)} EGLD into this venue in two sessions and received ~{abs(U_DISC):.0f}% less per EGLD than the CEX price. "
        "With most CEX rails closed, the DEX is where an EGLD holder who needs dollars goes, and its depth sets the exit cost.\n\n"
        f"MEX ${xx['mex_price']:.2e} from the pool ({xx['mex_wow']:+.1f}% WoW); MEX/WEGLD depth ${f(xx['mex_pair_depth']['tvl_usd'])}, rank {xx['mex_pair_depth']['depth_rank']}.\n\n"
        f"STABLECOINS. USDC {usdc['pct']:+.2f}% to {f(usdc['supply'])} ({f(usdc['prev']-usdc['supply'])} burned) and USDT {usdt['pct']:+.2f}% to {f(usdt['supply'])}. "
        f"This week the burn has a measured source: {f(U_BRIDGED_USDC)} of the USDC left through xBridge from the one exiting staker. Bridged dollars on MultiversX are the exit route, not new money arriving. "
        f"NEWLY ISSUED: {len(newly)} issuance{'s' if len(newly)!=1 else ''} in the window.")}
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
         "notable_events": f"EGLD market {f(df['egld_mm_prev_balance'])} -> {f(df['egld_mm_balance'])} EGLD, HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.2f}%, HUSDC {HT['HUSDC-d80042']['supply_pct']:+.2f}%. Aggregate lending TVL in EGLD {hl:+.2f}% on a {pc:+.2f}% price week (mechanical: dollar collateral shrinks in EGLD terms when EGLD rises). Second quiet week after restart.",
         "health_signal": "flat"},
        {"protocol": "Hatom Liquid Staking", "category": "liquid_staking", "addresses_tracked": 2, "tvl_usd": df["hatom_lsd_usd"], "tvl_egld": df["hatom_lsd_usd"] / price,
         "tvl_wow_change_pct": lsd["SEGLD-3ad2d0"]["pct"], "transfers_24h": cnt("Hatom Liquid Staking"),
         "notable_events": f"SEGLD supply {lsd['SEGLD-3ad2d0']['pct']:+.2f}% to {f(lsd['SEGLD-3ad2d0']['supply'])}; SWTAO {lsd['SWTAO-356a25']['pct']:+.2f}%.",
         "health_signal": hs(lsd["SEGLD-3ad2d0"]["pct"])},
        {"protocol": "Hatom USH", "category": "stablecoin", "addresses_tracked": 4, "tvl_usd": df["ush_usd"], "tvl_egld": df["ush_usd"] / price,
         "tvl_wow_change_pct": lsd["USH-111e09"]["pct"], "transfers_24h": None,
         "notable_events": f"USH {lsd['USH-111e09']['pct']:+.2f}% to {f(lsd['USH-111e09']['supply'])}.", "health_signal": hs(lsd["USH-111e09"]["pct"])},
        {"protocol": "XOXNO LSD", "category": "liquid_staking", "addresses_tracked": 3, "tvl_usd": df["xoxno_usd"], "tvl_egld": df["xoxno_usd"] / price,
         "tvl_wow_change_pct": lsd["XEGLD-e413ed"]["pct"], "transfers_24h": cnt("XOXNO LSD"),
         "notable_events": f"XEGLD supply {lsd['XEGLD-e413ed']['pct']:+.2f}% to {f(lsd['XEGLD-e413ed']['supply'])}, a third week of mild redemption.",
         "health_signal": hs(lsd["XEGLD-e413ed"]["pct"])},
        {"protocol": "XOXNO Aggregator", "category": "aggregator", "addresses_tracked": 1, "tvl_usd": 0.0, "tvl_egld": 0.0, "tvl_wow_change_pct": None,
         "transfers_24h": cnt("XOXNO Aggregator"), "volume_24h_usd": 0.0, "notable_events": f"{f(cnt('XOXNO Aggregator'))} transfers in 24h; the route the week's largest staking exit took (11 xo calls).", "health_signal": "flat"},
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
         "notable_events": f"{f(es('VOXEGLD-5872e5'))} EGLD, supply {(em['VOXEGLD-5872e5']['pct'] or 0):+.1f}%, holders {em['VOXEGLD-5872e5']['holders']}: fifth week of growth.", "health_signal": hs(ep("VOXEGLD-5872e5"))},
        {"protocol": "VestaX Finance", "category": "liquid_staking", "addresses_tracked": 1, "tvl_usd": (es("VEGLD-2b9319") or 0) * price, "tvl_egld": es("VEGLD-2b9319") or 0.0,
         "tvl_wow_change_pct": ep("VEGLD-2b9319"), "transfers_24h": None,
         "notable_events": f"{f(es('VEGLD-2b9319'))} EGLD.", "health_signal": hs(ep("VEGLD-2b9319"))}],
    "sc_deployments": [],
    "analysis": (
        f"LENDING FLAT, IN EGLD. Hatom lending TVL ex-HMEX {hl:+.2f}% in EGLD on a {pc:+.2f}% price week; the EGLD market {f(df['egld_mm_prev_balance'])} -> {f(df['egld_mm_balance'])} EGLD ({EMM_D:+,.0f}). "
        f"HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.2f}% (EGLD depositors added), HUSDC {HT['HUSDC-d80042']['supply_pct']:+.2f}%, HUSDT {HT['HUSDT-6f0914']['supply_pct']:+.2f}%: dollar suppliers withdrew, consistent with the bridge outflow. "
        f"The price move is under 5%, so the inverse-ratio rule is not evaluable.\n\n"
        f"LIQUID STAKING. SEGLD {lsd['SEGLD-3ad2d0']['pct']:+.2f}%, XEGLD {lsd['XEGLD-e413ed']['pct']:+.2f}%, SWTAO {lsd['SWTAO-356a25']['pct']:+.2f}%, USH {lsd['USH-111e09']['pct']:+.2f}% (USH minted against collateral; Hatom's stablecoin grew while bridged dollars shrank). VoxEGLD {(em['VOXEGLD-5872e5']['pct'] or 0):+.1f}%, the others flat. "
        "The discovery sweep returned the six known protocols plus two 1-2 EGLD test deployments.\n\n"
        f"ACTIVITY. XOXNO aggregator {f(cnt('XOXNO Aggregator'))} transfers in 24h, OneDex {f(cnt('OneDex Swap'))}, Hatom LSD {f(cnt('Hatom Liquid Staking'))}. The XOXNO aggregator was the main venue for the week's largest exit (11 swap calls, {f(U_SOLD)} EGLD with xExchange compose).")}

# ---------------------------------------------------------------------------
R["anomalies"] = [
    {"metric": "exchange_rail_reopening", "current_value": len(OPEN), "previous_value": 0, "method": "rule_based", "severity": "high",
     "description": f"Rails open both ways at {len(OPEN)} tracked venues ({', '.join(OPEN)}), deposit-only at {', '.join(DEPONLY)}, closed at {', '.join(CLOSED_MAJOR)}. {f(RAIL_EGLD_IN)} EGLD deposited and {f(RAIL_EGLD_OUT)} withdrawn on the open rails in the week."},
    {"metric": "otc_router_tail_to_gate", "current_value": ROUTER_DELIV, "previous_value": 0, "method": "rule_based", "severity": "medium",
     "description": f"{ROUTER_N} OTC Desk->Gate.io routers delivered {f(ROUTER_DELIV)} EGLD at Gate.io's Oct 4 23:00 sweep, all of it loaded Sep 18-19 and stranded by the halt. Desks themselves idle."},
    {"metric": "dex_exit_discount_pct", "current_value": U_DISC, "previous_value": None, "method": "rule_based", "severity": "medium",
     "description": f"{f(U_SOLD)} EGLD sold on chain for {f(U_BRIDGED_USDC)} USDC (${U_PX:.2f}/EGLD) and bridged to Ethereum, {abs(U_DISC):.0f}% below the ${price:.2f} close. The cost of exiting through on-chain liquidity while CEX deposits are closed."},
    {"metric": "korea_premium_pct", "current_value": PREM, "previous_value": PREM_PREV, "method": "rule_based", "severity": "medium",
     "change_pct": 100 * (PREM - PREM_PREV) / PREM_PREV,
     "description": f"Upbit premium {PREM:.1f}% from {PREM_PREV:.1f}% with UPbit deposits still closed; Upbit share of global volume {UP_SHARE:.0f}% from {UPSH_PREV:.0f}%. The gap narrowed without arbitrage."},
    {"metric": "cex_spot_volume_7d_egld", "current_value": BOOK["spot_volume_7d_egld"], "previous_value": BOOK["spot_volume_prior_7d_egld"], "method": "rule_based", "severity": "medium",
     "change_pct": 100 * (BOOK["spot_volume_7d_egld"] - BOOK["spot_volume_prior_7d_egld"]) / BOOK["spot_volume_prior_7d_egld"],
     "description": f"7-day CEX spot volume {f(BOOK['spot_volume_7d_egld']/1e6,2)}M EGLD, from {f(BOOK['spot_volume_prior_7d_egld']/1e6,2)}M; most of the drop is Upbit's closed-book rally fading."},
    {"metric": "egld_price_usd", "current_value": price, "previous_value": M["prev_price"], "method": "z_score", "severity": z["price"].get("severity", "low"),
     "average_value": z["price"].get("mean"), "stddev": z["price"].get("stddev"), "z_score": zz("price"), "change_pct": pc,
     "description": f"z={zz('price'):+.2f} against the 8-week baseline; EGLD trailed BTC by {abs(EGLD_VS_BTC):.1f}pp."},
    {"metric": "staked_ratio", "current_value": M["sr"], "previous_value": M["sr_prev"], "method": "z_score", "severity": z["sr"].get("severity", "low"),
     "average_value": z["sr"].get("mean"), "stddev": z["sr"].get("stddev"), "z_score": zz("sr"), "change_pct": 100 * (M["sr"] - M["sr_prev"]) / M["sr_prev"],
     "description": f"Staked ratio {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp), z={zz('sr'):+.2f}: the lowest reading in the series and the first below the 46.30% floor."},
    {"metric": "usdt_supply", "current_value": usdt["supply"], "previous_value": usdt["prev"], "method": "rule_based", "severity": "low", "change_pct": usdt["pct"],
     "description": f"USDT {usdt['pct']:+.2f}% and USDC {usdc['pct']:+.2f}%; {f(U_BRIDGED_USDC)} USDC of the burn is one staker's exit via xBridge."},
    {"metric": "unbonding_queue_undelegated_egld_7d", "current_value": sk["undelegated_week"], "previous_value": 84169, "method": "z_score" if z.get("unbond") else "rule_based", "severity": "low",
     "change_pct": 100 * (sk["undelegated_week"] - 84169) / 84169,
     "description": f"{f(sk['undelegated_week'])} EGLD unDelegated by {sk['undelegate_callers']} wallets over 7 live days: back under the pre-halt 73-84K range; the restart burst is over."},
]

R["trend_indicators"] = {
    "accelerating_exchange_outflows": [],
    "validator_movements": {"providers_joining": 0, "providers_leaving": 0, "net_provider_change": 0, "notable_joiners": [], "notable_leavers": []},
    "token_supply_events": [
        {"identifier": "USDT-f8c08c", "name": "USDT", "event": "burn", "supply_previous": str(int(usdt["prev"])), "supply_current": str(int(usdt["supply"])),
         "change_pct": usdt["pct"], "description": f"{f(usdt['prev']-usdt['supply'])} USDT redeemed; an eighth contraction in nine weeks."},
        {"identifier": "USDC-c76f1f", "name": "WrappedUSDC", "event": "burn", "supply_previous": str(int(usdc["prev"])), "supply_current": str(int(usdc["supply"])),
         "change_pct": usdc["pct"], "description": f"{f(USDC_BURN)} USDC redeemed, {f(U_BRIDGED_USDC)} of it by the exiting staker via xBridge."},
        {"identifier": "USH-111e09", "name": "USH", "event": "mint", "supply_previous": str(int(lsd["USH-111e09"]["prev"])), "supply_current": str(int(lsd["USH-111e09"]["supply"])),
         "change_pct": lsd["USH-111e09"]["pct"], "description": "Hatom's native stablecoin minted against collateral while bridged dollars left."},
        {"identifier": "HEGLD-d61095", "name": "HEGLD", "event": "mint", "supply_previous": str(int(float(HT['HEGLD-d61095']['prev_supply']))), "supply_current": str(int(float(HT['HEGLD-d61095']['supply']))),
         "change_pct": HT["HEGLD-d61095"]["supply_pct"], "description": "EGLD supplied to Hatom, second week."}],
    "consecutive_streaks": [
        {"metric": "usdt_supply", "direction": "down", "weeks": 4, "cumulative_change_pct": 100 * (usdt["supply"] - 463905) / 463905,
         "interpretation": f"463,905 / 452,585 / 433,045 / {f(usdt['supply'])}: bridged dollars keep leaving MultiversX."},
        {"metric": "staked_ratio", "direction": "down", "weeks": 3, "cumulative_change_pct": 100 * (M["sr"] - 0.4655083730551601) / 0.4655083730551601,
         "interpretation": f"46.55% / 46.59% / 46.48% / {100*M['sr']:.2f}%: a slow grind lower since the September step down."},
        {"metric": "total_delegators", "direction": "flat", "weeks": 16, "cumulative_change_pct": -1.1, "interpretation": f"{sk['users_delta']:+,} to {f(sk['users'])}. Still the base rate."},
        {"metric": "provider_operator_fee_selling", "direction": "flat", "weeks": 16, "cumulative_change_pct": 0.0, "interpretation": "Sixteen runs with zero exchange destinations from sampled operator wallets."},
        {"metric": "otc_desk_inventory_egld", "direction": "flat", "weeks": 3, "cumulative_change_pct": 0.0, "interpretation": f"46,637 for three weekly reads: the desks have not moved since the halt."}],
    "regime_shifts": [
        {"metric": "exchange_rail_state", "before_value": 0.0, "after_value": round(len(OPEN) / max(1, len(VEN)), 2),
         "description": f"PARTIAL REOPENING. {len(OPEN)} of {len(VEN)} tracked venues move EGLD both ways, Binance.com takes deposits only, and the venues that carried most of the pipeline's deliveries and most global volume (UPbit, Bybit, Binance withdrawals) remain closed. Not promoted: the state is still changing week to week."},
        {"metric": "exit_route", "before_value": 0.0, "after_value": 1.0,
         "description": "CANDIDATE: with CEX deposits closed, a measured staking exit routed DEX -> USDC -> xBridge -> Ethereum. One wallet is an observation, not a regime; promote only if the USDC burn keeps tracking unbonding withdrawals once rails are open."}]}

R["watch_list"] = [
    {"item": "UPBIT CAUTION REVIEW Oct 19-23 and the KOREA PREMIUM", "weeks_on_list": 2,
     "reason": f"Upbit premium {PREM:.1f}% (from {PREM_PREV:.1f}%), {UP_SHARE:.0f}% of global volume, deposits and withdrawals closed. Upbit decides on continued support between Oct 19 and 23; delisting would remove the venue that has carried the pipeline. PRE-COMMITTED (korea-premium-arbitrage, upbit-premium-decay)."},
    {"item": "EXCHANGE RAILS - partial reopening", "weeks_on_list": 2,
     "reason": f"Open: {', '.join(OPEN)}. Deposit-only: {', '.join(DEPONLY)}. Closed: {', '.join(CLOSED_MAJOR)}. Binance withdrawals reopening on the native chain is the next step to watch."},
    {"item": "OTC PIPELINE - idle desks, router tail cleared", "weeks_on_list": 28,
     "reason": f"Desks {f(otc['desk_bal'])} for a third week, no sends; the {f(ROUTER_DELIV)} EGLD Gate.io router tail landed Oct 4. PRE-COMMITTED (otc-pipeline-resumption)."},
    {"item": "DEX + BRIDGE EXITS", "weeks_on_list": 1,
     "reason": f"{U_ADDR[:12]}... sold {f(U_SOLD)} EGLD on chain and bridged {f(U_BRIDGED_USDC)} USDC to {U_ETH_DEST[:10]}... at ~{abs(U_DISC):.0f}% below CEX. Watch for more matured unbonding following the same route ({f(sk['pool_total'])} EGLD measured pending)."},
    {"item": "UNKNOWN WHALE I AND erd1a6lte0 - probable exchange hot wallets", "weeks_on_list": 3,
     "reason": "Zero inbound in seven live days. If they are hot wallets, they belong to a venue that has not reopened."},
    {"item": "STAKED RATIO BELOW 46.30%", "weeks_on_list": 1,
     "reason": f"{100*M['sr']:.2f}%, the lowest in the series, with delegation TVL up: the gap is unbonding legs in flight."},
    {"item": "INCIDENT REPORTS - MultiversX technical report and Hatom MEX report", "weeks_on_list": 3,
     "reason": "Searched: no MultiversX technical incident report published as of Oct 3; none found from Hatom. Reconcile with the chain reconstruction once out."},
    {"item": "EXPLOIT WALLET AND POISONING RING", "weeks_on_list": 3,
     "reason": f"Incident addresses hold {HR['invalid_total_egld']:.2f} EGLD; poisoning operator {PR['operator_out_7d']}+ dust txs (page cap); lookalikes 0 inbound above dust."},
]

# ---------------------------------------------------------------------------
prior = {t["id"]: t for t in r26["pre_committed_tests"]}
tests = [t for t in r26["pre_committed_tests"] if t["status"] == "resolved"]


def resolve(tid, outcome, measured, resolution):
    t = dict(prior[tid]); t.update({"status": "resolved", "outcome": outcome, "resolved_in_run": 28, "measured_value": measured, "resolution": resolution}); return t


tests.append(resolve("post-restart-exit-wave", POST_EXIT,
    f"{f(sk['undelegated_week'])} EGLD unDelegated by {sk['undelegate_callers']} wallets over the full 7-day live window Sep 28 - Oct 5 (bar < 90,000)",
    "The '< 90,000 = one-off burst' branch fires, against the claim that the restart triggered an exit wave. Last week's ~117K/week pace was a burst concentrated in the first hours after restart (one wallet alone queued 26,664). "
    "What the burst did next is measured: its largest leg was withdrawn, sold on chain and bridged out, so the burst was real exit supply even though it did not persist."))
t = dict(prior["unknown-whale-i-is-exchange"]); t.update({"status": "open", "measured_value": f"run #28: {CEN['Unknown Whale I']['inbound_txs']} inbound txs in 7 live days, 0 outbound. Not evaluable while its probable venue is closed; deadline stays at the second full week after deposits reopen at the major venues.", "resolution": None}); tests.append(t)
t = dict(prior["delivery-price-relevance-2"]); t.update({"status": "open", "measured_value": f"run #28: partial rails; desk delivery 0 (router tail {f(ROUTER_DELIV)} to Gate.io, already counted in wave #4). Not evaluable.", "resolution": None}); tests.append(t)
t = dict(prior["korea-premium-arbitrage"]); t.update({"status": "open", "measured_value": f"run #28: premium {PREM:.1f}% (Upbit ${up['converted_last']['usd']:.2f} vs Binance ${bn['converted_last']['usd']:.2f}); UPbit hot wallet 0 EGLD deposits. Deadline run #29.", "resolution": None}); tests.append(t)


def new(tid, claim, threshold, branches, measured):
    return {"id": tid, "registered_in_run": 28, "claim": claim, "threshold": threshold, "branches": branches,
            "status": "open", "outcome": None, "resolved_in_run": None, "measured_value": measured, "resolution": None}


tests += [
    new("otc-pipeline-resumption", "The OTC programme resumes once its feeder and delivery venues reopen, rather than having ended with the halt.",
        "desk gross outbound in any single weekly window through run #31: > 100,000 EGLD = resumed; 20,000-100,000 = partial, no conclusion; < 20,000 in every week through run #31 with UPbit deposits open for at least two of those weeks = programme ended; UPbit still closed at run #31 = not evaluable",
        [{"condition": "> 100,000 EGLD gross desk outbound in a week by run #31", "reading": "resumed"},
         {"condition": "20,000-100,000", "reading": "partial, no conclusion"},
         {"condition": "< 20,000 every week, UPbit open >= 2 weeks", "reading": "programme ended"},
         {"condition": "UPbit closed through run #31", "reading": "not evaluable"}],
        f"run #28: desk gross outbound {f(otc['gross_out'])}; router tail {f(ROUTER_DELIV)} to Gate.io; desks {f(otc['desk_bal'])}"),
    new("upbit-premium-decay", "The Upbit premium is fading Korean demand, not blocked arbitrage: it keeps closing while UPbit deposits stay shut.",
        "Upbit-Binance premium at run #29 with UPbit EGLD deposits still closed: < 5% = demand faded (premium closed without arbitrage); 5-15% = no conclusion; > 15% = premium re-widened, demand persists; UPbit deposits reopened before run #29 = not evaluable (korea-premium-arbitrage takes over)",
        [{"condition": "deposits closed and premium < 5%", "reading": "demand faded"},
         {"condition": "deposits closed and premium 5-15%", "reading": "no conclusion"},
         {"condition": "deposits closed and premium > 15%", "reading": "demand persists"},
         {"condition": "UPbit deposits reopened before run #29", "reading": "not evaluable"}],
        f"run #28: {PREM:.1f}% (from {PREM_PREV:.1f}%), UPbit deposits closed"),
]
resolved = [t for t in tests if t.get("resolved_in_run") == 28]
as_pred = sum(1 for t in resolved if t["outcome"] == "as_predicted")
R["pre_committed_tests"] = tests

# ---------------------------------------------------------------------------
R["meta_learning"] = {
    "run_number": 28,
    "endpoints_that_worked": status["ok"],
    "endpoints_that_failed": [
        f"NONE with data missing. {D.get('_n_429', 40)} HTTP 429s in the main pass despite the new global budget (2 paged provider scans, 4 single calls), all recovered by the follow-up; the reward sampler lost 2 of 8 providers to 429 on the first attempt and was re-run to 8 of 8."],
    "api_quirks": [
        "ACCOUNT TRANSACTION COUNTS INCLUDE ESDT SPAM AIRDROPS: Binance.com's hot wallet showed 33 receives since restart, Gate.io 17; only value-bearing EGLD transactions separate a reopened rail from airdrop noise.",
        "A 4 req/s GLOBAL BUDGET STILL DRAWS 429s ON THE PROVIDER SCAN: the API's limit is burstier than a flat rate; the paged provider scan needs ~0.5 s spacing or its own slower budget.",
        "xBridge exits are visible on MultiversX as unwrapTokenCreateTransaction calls to the Tokens Wrapper (erd1qqqqqqqqqqqqqpgq305jfaqrdxpzjgf9y5gvzh60mergh866yfkqzqjv2h); the action arguments carry the token, amount and Ethereum destination."],
    "data_gaps": [
        "Kraken reopened EGLD on Oct 1 but no Kraken address is tracked.",
        "MultiversX has published no technical incident report (as of Oct 3); Hatom's MEX report was not found.",
        "Unknown Whale I census not evaluable (probable venue closed).",
        "Hatom UTK Money Market and OneDex Launchpad still fail bech32 validation (open since run #18)."],
    "key_findings": [
        f"Rails reopened at {', '.join(OPEN)} (both ways) and Binance.com (deposits only); {', '.join(CLOSED_MAJOR)} stayed closed.",
        f"The first post-halt pipeline delivery was {f(ROUTER_DELIV)} EGLD of router inventory stranded since Sep 18-19, swept into Gate.io at its reopening; the desks stayed idle.",
        f"The largest post-restart unstaker sold {f(U_SOLD)} EGLD on chain and bridged {f(U_BRIDGED_USDC)} USDC to Ethereum at ~{abs(U_DISC):.0f}% below CEX.",
        f"post-restart-exit-wave resolved 'one-off burst': {f(sk['undelegated_week'])} EGLD unDelegated over a full week.",
        f"Upbit premium {PREM:.1f}% from {PREM_PREV:.1f}% with UPbit still closed; Upbit review Oct 19-23.",
        f"Staked ratio {100*M['sr']:.2f}%, first print below 46.30%; compound rate back to {cvc['compound_pct_of_reward_decisions']:.2f}%."],
    "action_items_from_previous": len(r26["meta_learning"]["recommendations_for_next_run"]),
    "action_items_completed_detail": [
        "COUNT EXCHANGE SENDS/RECEIVES SINCE RESTART FIRST - done, and tightened: the collector counts both legs since restart and in the window, and a new rail script keeps only value-bearing EGLD transactions (spam airdrops had inflated the raw counts). Exchange metrics kept out of baselines (partial rails).",
        "IF RAILS REOPENED: resolve korea-premium-arbitrage / delivery-price-relevance-2, re-run the UWI census - partially: UPbit and the delivery venues are still closed so both tests stay open; the UWI census was re-run (0 inbound).",
        "RESOLVE post-restart-exit-wave and TRACE MATURED UNBONDING - done: resolved 'one-off burst'; the largest leg traced through withdraw -> DEX -> USDC -> xBridge -> Ethereum.",
        "FIX THE VENUE RESOLVER - done: venues resolve on category == exchange plus an explicit VENUE_MAP; label text no longer creates venues.",
        "READ THE INCIDENT REPORTS - attempted: searched; MultiversX had published no technical incident report as of Oct 3 and no Hatom MEX report was found. Exchange status pages (Kraken, Upbit, Binance) read instead.",
        "GLOBAL RATE-LIMIT BUDGET - done but insufficient: a shared 4 req/s budget cut 429s from 47 to ~40; all recovered."],
    "methodology_changes": [
        "RAIL STATE IS VALUE-BEARING ONLY. Count EGLD-carrying transactions per exchange wallet (scripts/rails_run28.py); raw transaction counts include ESDT spam airdrops.",
        "A REOPENING WEEK PRINTS AN INFLOW. Deposits reopen before withdrawals, so partial-rail exchange flows are recorded but not appended to baselines until the major venues are open both ways.",
        "TRACE EXITS PAST THE DEX. When CEX rails are closed, follow matured unbonding through swap aggregators and xBridge unwrap calls; the bridge action arguments give the USDC amount and destination, and USDC/EGLD gives the realised exit price.",
        "venue_of() resolves on category plus an explicit map (VENUE_MAP), never on label text."],
    "new_addresses_discovered_detail": [
        "erd1qqqqqqqqqqqqqpgq305jfaqrdxpzjgf9y5gvzh60mergh866yfkqzqjv2h - xBridge: Tokens Wrapper (API asset label); added to known-addresses as bridge.",
        f"{U_ADDR} - post-restart exiter: 26,664 EGLD unDelegated, sold on chain, bridged to {U_ETH_DEST}."],
    "action_items_completed": 5,
    "new_addresses_discovered": 2,
    "most_valuable_insight": (
        f"Following one exit all the way out. The largest post-restart unstaker could not deposit at an exchange, so it withdrew, swapped on chain and bridged USDC to Ethereum, realising ${U_PX:.2f} per EGLD against ${price:.2f} on CEX. "
        f"That puts a measured price (~{abs(U_DISC):.0f}%) on closed rails, explains most of the week's USDC burn, and shows where the {f(sk['pool_total'])} EGLD still unbonding is likely to go while UPbit and Binance withdrawals stay shut."),
    "top_recommendation": "TRACK THE UPBIT DECISION (Oct 19-23) AND THE FIRST WEEK BINANCE/UPBIT MOVE EGLD BOTH WAYS: per-venue value-bearing counts, desk activity, the premium, and whether unbonding exits switch from the DEX+bridge route back to CEX deposits.",
    "recommendations_for_next_run": [
        "RAILS FIRST (value-bearing counts via rails_run28.py): if UPbit or Binance withdrawals reopened, resolve korea-premium-arbitrage and start delivery-price-relevance-2.",
        "Resolve upbit-premium-decay at run #29 (premium with UPbit still closed: < 5% = demand faded).",
        "EXIT-ROUTE SCAN: for every withdraw call > 1,000 EGLD, follow the EGLD to CEX deposit / DEX swap / xBridge unwrap; sum the bridge-out USDC against the USDC burn.",
        "Add a Kraken deposit address to known-addresses (Kraken reopened Oct 1) and check the Binance BEP-20 route via the Binance.com hot wallet's ESDT/bridge activity.",
        "Slow the provider scan to its own 0.5 s budget (40 HTTP 429s at a shared 4 req/s).",
        "OTC: watch the desks for the first post-halt send; otc-pipeline-resumption runs to run #31."],
    "dashboard_feature_suggestions": [
        {"title": "Exit-route Sankey for unbonded EGLD",
         "motivation": f"This run traced {f(U_SOLD)} EGLD from three provider withdrawals through the XOXNO aggregator and xExchange into USDC and out via xBridge to Ethereum, at ~{abs(U_DISC):.0f}% below CEX. The dashboard shows the unbonding queue and the USDC burn as two unrelated numbers; the link between them is the finding.",
         "suggested_visualization": "sankey from provider withdraw -> {CEX deposit, DEX swap, held, re-delegated} -> {USDC bridge-out, CEX}, weekly, with the realised exit price per route as a label",
         "data_already_available": False, "data_source": "whale_intelligence.exit_routes (one wallet this run); a collector-side exit-route scan over all withdraw calls > 1,000 EGLD would generalise it", "priority": "high"},
        {"title": "Rail reopening timeline per venue",
         "motivation": f"Rails reopened one venue at a time ({', '.join(f'{k} {hm(v['first_in'] or v['first_out'])}' for k, v in VEN.items() if v['state'] != 'closed' and (v['first_in'] or v['first_out']))}), and the pipeline's router tail hit Gate.io in its first deposit hour. A single net-flow number hides that order.",
         "suggested_visualization": "swimlane timeline (one lane per venue) from the halt to now, shaded closed / deposit-only / open, with first-deposit and first-withdrawal markers and dots for the largest deposits",
         "data_already_available": True, "data_source": "whale_intelligence.exchange_flows.rail_status.by_venue (first_egld_deposit_utc, first_egld_withdrawal_utc, state)", "priority": "high"}],
    "dashboard_suggestions_followup": [
        {"title": "Exchange rail status board", "status": "pending",
         "note": "Not built. Now carried by rail_status.by_venue with a per-venue state; superseded in scope by this run's rail reopening timeline suggestion, which adds the time axis."},
        {"title": "Korea premium tracker", "status": "pending",
         "note": "Not built. More useful this week: the premium halved with UPbit still closed, and Upbit's Oct 19-23 review makes the series decision-relevant."}],
    "withdrawn_claims": [
        {"claim": "Crypto.com reopened EGLD rails on Sep 29 (first published version of this run #28 report).",
         "asserted_in_runs": [28], "withdrawn_in_run": 28,
         "reason": "The Sep 29 and later 02:00 UTC transfers were Crypto.com's internal daily sweep to its own staking wallet (erd1uskf6..., which delegates to Figment) and a 0-value bot, a routine that also ran before the halt.",
         "replacement": "First customer-like Crypto.com flows on chain were Oct 2: withdrawals of 1,444 and 240 EGLD and one 5,617 EGLD deposit; none since. Both legs have worked at least once, but no public reopening notice was found, so the venue is 'functioning, unconfirmed'."}],
}

rep = {k: R[k] for k in ["metadata", "executive_summary", "network_health", "whale_intelligence", "staking_intelligence", "token_activity",
                         "defi_activity", "anomalies", "trend_indicators", "watch_list", "meta_learning", "pre_committed_tests"]}
json.dump(rep, open(f"{REPO}/reports/{RD}.json", "w"), indent=1, default=str)
print("report written", len(json.dumps(rep, default=str)), "bytes")
print(f"tests resolved this run {len(resolved)}, as_predicted {as_pred}, open {sum(1 for t in tests if t['status']=='open')}")
print("PREM", round(PREM, 1), "UP_SHARE", round(UP_SHARE, 1), "OPEN", OPEN, "DEPONLY", DEPONLY, "ROUTER", round(ROUTER_DELIV), "U_SOLD", U_SOLD, "U_PX", round(U_PX, 3), "disc", round(U_DISC, 1))
