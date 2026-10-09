#!/usr/bin/env python3
"""Run #29 stage 2: assemble reports/2026-10-09.json from derived.json + snapshot.

Off-cadence 4-day window (Oct 5 -> Oct 9). Defining facts: EGLD -14% to $3.95 (BTC -4.4%); Binance.com
withdrawals reopened Oct 9 08:04 UTC and ~124K EGLD of deposits arrived, among them unstaked EGLD; the UPbit
OTC desk restarted (first post-halt send Oct 6, UPbit reload of 14,000 Oct 8); Upbit premium re-widened.
"""
import json
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD = "2026-10-09"
O = json.load(open("/tmp/run29w/derived.json"))
D = json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev = json.load(open("/tmp/run29w/previous_run28.json"))
status = json.load(open("/tmp/run29w/status.json"))
beh = json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
r26 = json.load(open(f"{REPO}/reports/2026-10-05.json"))   # previous report (name kept for the reused blocks)
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
LIVE_DAYS = 4.0
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
    dep_ok = v["in_egld"] >= 1 and lbl != "UPbit"; wd_ok = v["out_txs"] > 0 and lbl != "UPbit"
    v["state"] = ("open" if dep_ok and wd_ok else "deposit_only" if dep_ok else "withdrawal_only" if wd_ok else "closed")
    VEN[lbl] = v
OPEN = [k for k, v in VEN.items() if v["state"] == "open"]
DEPONLY = [k for k, v in VEN.items() if v["state"] == "deposit_only"]
CLOSED_MAJOR = [k for k in ("UPbit", "Bybit", "Coinbase", "MEXC", "KuCoin", "Bitfinex") if VEN.get(k, {}).get("state") == "closed"]
RAIL_EGLD_IN = sum(v["in_egld"] for v in VEN.values()); RAIL_EGLD_OUT = sum(v["out_egld"] for v in VEN.values())

# ---- run #29 traces ----
TR = D["run29_traces"]
BINV = VEN["Binance.com"]
BIN_DEP = TR["binance_depositors"]
BIN_TOP3 = sum(x["total_egld"] for x in BIN_DEP[:3])
BIN_DEP_ALL = BINV["in_egld"]
DEP_WHALE = next(x for x in BIN_DEP if x["sender"].startswith("erd137cw9"))
DEP_MERIA = next(x for x in BIN_DEP if x["sender"].startswith("erd14ds7pk"))
EXITS = TR["exit_routes"]
MERIA_WD = sum(e["withdrawn_egld"] for e in EXITS if e["provider"] == "meria")
DESKS = TR["desks"]
UPB_DESK = "erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
DIST_DESK = "erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
DESK_FIRST_SEND = min(x["ts"] for a_ in DESKS.values() for x in a_["out"] if x["egld"] > 1)
UPBIT_RELOAD = 14000.0
USDC_BURN = usdc["prev"] - usdc["supply"]
PREV_BOOK = prev["exchange_orderbook_latest"]
PREM_PREV = PREV_BOOK.get("korea_premium_pct", 11.7)
UPSH_PREV = PREV_BOOK.get("upbit_share_of_volume_pct", 20.0)
PREM_RESULT = "against" if PREM > 15 else ("as_predicted" if PREM < 5 else "inconclusive")
WINDOW_NOTE = "4-day window (Oct 5 -> Oct 9): every flow below is a 4-day flow, not a 7-day one."

wd_top0 = (WD.get("by_provider_top") or [[0, 0]])[0][1]
R = {}
R["metadata"] = {
    "report_date": RD, "period_start": "2026-10-05", "period_end": RD,
    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "egld_price_usd": price, "btc_price_usd": M["btc"], "eth_price_usd": M["eth"],
    "run_number": 29,
    "data_sources_ok": status["ok"] + [
        "follow-up pass: 303 withdraw calls decoded, poisoning lookalikes re-scanned (0 errors)",
        "rail check (rails_run29.py): value-bearing EGLD deposits/withdrawals per tracked exchange wallet since restart 2, paginated",
        "targeted traces (trace_run29.py): largest Binance.com depositors and their funding, the 11,000 EGLD Binance withdrawal, the OTC desks' in/out, exit routes of the six largest withdraw calls",
        "public sources: web search found no Binance announcement of a native-network reopening and no MultiversX technical incident report; Upbit caution review Oct 19-23"],
    "data_sources_failed": status["failed"],
    "data_sources_recovered": [
        "LIVENESS GATE PASSED: every shard within seconds of real time; chain live all four days of the window",
        f"{D.get('_n_429', 0)} HTTP 429 responses in the main pass; paged scans recovered, 1 API error logged ({len(D.get('_api_errors', []))})",
        "OFF-CADENCE RUN: previous snapshot Oct 5, this one Oct 9. " + WINDOW_NOTE,
        f"delegator reward behaviour sampled {ag['providers_sampled']} of {ag.get('providers_requested', 8)} providers"]}

R["executive_summary"] = [
    {"category": "network", "severity": "high", "finding":
     f"EGLD FELL {abs(pc):.1f}% IN FOUR DAYS TO ${price:.2f}, AGAINST BTC {M['btc_wow']:+.1f}% AND ETH {M['eth_wow']:+.1f}%. The daily series ran $4.49 / $4.55 / $4.55 / $4.59 / $4.45 / then $4.11, $4.00, $3.95 from Oct 7. EGLD trailed BTC by {abs(EGLD_VS_BTC):.1f}pp. The slide began Oct 7, two days before the first Binance.com withdrawals. "
     f"The 8-week price z-score is {zz('price'):+.2f} against a baseline that mixes halt-period prices. CEX spot volume over 7 days was {f(BOOK['spot_volume_7d_egld']/1e6, 2)}M EGLD."},
    {"category": "whale", "severity": "high", "finding":
     f"BINANCE.COM WITHDRAWALS REOPENED ON THE NATIVE CHAIN ON OCT 9 AT {hm(BINV['first_out'])[-5:]} UTC, AND DEPOSITS SURGED. The hot wallet sent {BINV['out_txs']} withdrawals ({f(BINV['out_egld'])} EGLD) to 182 distinct recipients, none before that minute, and took {BINV['in_txs']} deposits worth {f(BIN_DEP_ALL)} EGLD from {BINV['in_senders']} senders. "
     f"Its balance rose {f(cust['hot_balance']-cust['hot_previous'])} EGLD ({100*(cust['hot_balance']-cust['hot_previous'])/cust['hot_previous']:+.0f}%). Three wallets account for {f(BIN_TOP3)} EGLD ({100*BIN_TOP3/BIN_DEP_ALL:.0f}%) of the deposits. Web search found no Binance announcement; the evidence is on chain only."},
    {"category": "staking", "severity": "high", "finding":
     f"UNSTAKED EGLD IS GOING BACK TO CEX DEPOSITS. Last week's exit ran DEX to USDC to Ethereum at a ~9% discount; this week two meria withdrawals ({f(MERIA_WD)} EGLD, Oct 6) were merged with roughly 8,000 EGLD more into one wallet that deposited {f(DEP_MERIA['total_egld'])} EGLD to Binance.com on Oct 9 at 12:18 UTC, four hours after the venue's withdrawals reopened. "
     "The measured exit route switches the moment a CEX deposit rail is open. The other large Binance depositor, 57,620 EGLD in twelve clips, was funded by the 'Unknown Whale' wallet (35,739) and a second unlabelled wallet."},
    {"category": "whale", "severity": "medium", "finding":
     f"THE OTC PIPELINE MOVED FOR THE FIRST TIME SINCE THE HALT, SMALL. The UPbit OTC desk sent {f(otc['gross_out'])} EGLD through routers on Oct 6 04:27-04:29 (first send since the halt), the UPbit exchange wallet reloaded it with {f(UPBIT_RELOAD)} EGLD on Oct 8 14:53, and the desk passed 7,000 on to the Distribution wallet four minutes later. Desk inventory {f(otc['desk_bal'])} (from {f(otc['prev_desk'])}). "
     "That is 5.7K gross against a 100K+ weekly programme before the halt: a restart signal, not a restart. Tracked as otc-pipeline-resumption (open)."},
    {"category": "network", "severity": "medium", "finding":
     f"THE KOREA PREMIUM RE-WIDENED WITH UPBIT STILL SHUT. Upbit ${up['converted_last']['usd']:.2f} vs Binance ${bn['converted_last']['usd']:.2f} is a {PREM:.1f}% premium, up from {PREM_PREV:.1f}%; Upbit's share of volume is {UP_SHARE:.0f}% (from {UPSH_PREV:.0f}%). The upbit-premium-decay test (< 5% = demand faded) resolves against; 15.4% is just over its 15% 'persists' line. Upbit's caution review runs Oct 19-23."},
    {"category": "staking", "severity": "medium", "finding":
     f"STAKED RATIO {100*M['sr']:.2f}% IS A NEW LOW ({100*(M['sr']-M['sr_prev']):+.2f}pp), staked EGLD {M['staked_chg']:+,.0f}. {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD in four days (~{f(sk['undelegated_week']/LIVE_DAYS*7)} per week), and {O['withdraw_calls']} withdraw calls returned {f(WD.get('egld_returned_total', 0))} EGLD, led by meria ({f(wd_top0)}). Compounding {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} vs {cvc['claim_count']}); delegators {sk['users_delta']:+,}."},
    {"category": "defi", "severity": "low", "finding":
     f"HATOM'S EGLD MARKET LOST {abs(EMM_D):,.0f} EGLD ({100*EMM_D/df['egld_mm_prev_balance']:+.0f}%) AND HEGLD SUPPLY FELL {abs(HT['HEGLD-d61095']['supply_pct']):.1f}%, while lending TVL in EGLD terms read {hl:+.1f}% because its dollar collateral is worth more EGLD at a lower price (mechanical, the inverse-ratio effect). xExchange 24h volume ${f(bid['dexvol'])} ({100*(bid['dexvol']-bid['prev_dexvol'])/bid['prev_dexvol']:+.0f}%); pool TVL ex-MEX {bid['pooltvl_ex_mex_wow_pct']:+.0f}% in dollars. Bridged dollars kept leaving: USDC {usdc['pct']:+.2f}%, USDT {usdt['pct']:+.2f}%."},
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
               "btc_correlation_note": f"BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%, EGLD {pc:+.2f}%: EGLD fell {abs(EGLD_VS_BTC):.1f}pp more than BTC over four days as Binance deposits and unstaked EGLD reached exchanges."},
    "liveness": {"ok": D["liveness_ok"], "latest_block_by_shard": {k: iso(v["timestamp"]) for k, v in D["liveness"].items()},
                 "restart_1_utc": iso(1790181300), "restart_1_stopped_utc": iso(1790182386), "restart_2_utc": iso(1790263800),
                 "live_days_in_window": LIVE_DAYS, "rollback_point_utc": "2026-09-19 06:37:45 UTC"},
    "analysis": (
        f"A FOUR-DAY WINDOW. This is an off-cadence run (previous snapshot Oct 5, this one Oct 9), so every flow is a 4-day flow. Every shard read within seconds of real time and the chain ran all four days. Epoch {st['epoch']} ({st['epoch']-pact['epoch']:+d}), "
        f"{f(st['transactions']-pact['total_transactions'])} transactions (~{f(int((st['transactions']-pact['total_transactions'])/LIVE_DAYS))}/day), {f(st['accounts']-pact['total_accounts'])} new accounts. Total supply {f(econ['totalSupply'])} ({econ['totalSupply']-pecon['total_supply']:+,}). "
        "No technical incident report from MultiversX was found in web search.\n\n"
        f"STAKING. Staked EGLD {M['staked_chg']:+,.0f} to {f(econ['staked'])}; ratio {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp), the lowest in the tracked series for a second consecutive print. Network APR {100*econ['apr']:.2f}%.\n\n"
        f"PRICE. EGLD ${price:.2f}, {pc:+.2f}% against BTC {M['btc_wow']:+.2f}% and ETH {M['eth_wow']:+.2f}%. The fall happened over Oct 7-9 (daily closes $4.45, $4.11, $4.00, $3.95) before and while deposits surged at Binance.com. "
        "Correlation in time is not attribution: 124,524 EGLD of deposits is about $0.5M at these prices, and the order books are thin (Binance bids within 2% total $" + f(BOOK['binance']['depth_minus2_usd']) + "), so it does not take much. "
        f"Global CEX spot volume over 7 days was {f(BOOK['spot_volume_7d_egld']/1e6, 2)}M EGLD, against {f(BOOK['spot_volume_prior_7d_egld']/1e6, 2)}M the week before.")}


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


INV_SERIES = {**prev["otc_desk_inventory_series"], "run29": round(otc["desk_bal"])}
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
                        "note": "Value-bearing EGLD transactions only (ESDT spam airdrops and exchange-internal sweeps excluded). 4-day window Oct 5 - Oct 9; states describe this window only (Crypto.com, Bitget and Tokero worked both ways in earlier windows; Bitget and Tokero receives this window were sub-1-EGLD dust, so they read as withdrawal-only, and Crypto.com had no customer flow). Binance.com sent its first EGLD withdrawal on Oct 9 at 08:04 UTC after deposits had been open since Sep 29; the UPbit exchange wallet's only value-bearing flow was a 14,000 EGLD send to its OTC desk (not a customer withdrawal). MEXC and KuCoin remain at their Sep 24 replay transactions. Public status: no Binance announcement of a native-network reopening was found in web search, so the Binance state is inferred from chain data."},
        "signal": (f"BINANCE.COM REOPENED BOTH WAYS. Net exchange balance change {ex['net']:+,.0f} EGLD: " + ", ".join(f"{e2['entity']} {e2['net_flow_egld']:+,.0f}" for e2 in ex["entity"] if e2["net_flow_egld"]) + ". "
                   f"Binance.com took {f(BIN_DEP_ALL)} EGLD of deposits and paid out {f(BINV['out_egld'])} after 08:04 UTC on Oct 9; UPbit's -14,000 is the OTC reload, not a customer flow. {', '.join(CLOSED_MAJOR)} moved no EGLD. "
                   "A reopening day prints an inflow; the readings are recorded but not appended to the exchange-flow baseline until Upbit and Bybit also move EGLD."),
        "by_exchange": [{"exchange": w["exchange"], "change_egld": w["change_egld"], "pct": w["pct"]} for w in ex["per_wallet"]],
        "entity_netting": [{"entity": e2["entity"], "wallets_count": e2["wallets_count"],
                            "net_flow_egld": e2["net_flow_egld"], "interpretation": entity_interp(e2)} for e2 in ex["entity"]]},
    "dormant_activations": [],
    "exit_routes": {
        "route_this_run": "CEX deposit (Binance.com, Crypto.com)",
        "route_previous_run": "DEX -> USDC -> xBridge -> Ethereum (~9% below CEX)",
        "meria_unstaker_withdrawn_egld": MERIA_WD,
        "meria_unstaker_withdrawn_utc": "2026-10-06 15:49-15:50 UTC",
        "consolidated_wallet": DEP_MERIA["sender"],
        "binance_deposit_egld": DEP_MERIA["total_egld"], "binance_deposit_utc": iso(DEP_MERIA["deposits"][0]["ts"]),
        "binance_depositor_2": {"wallet": DEP_WHALE["sender"], "total_egld": DEP_WHALE["total_egld"], "deposits": DEP_WHALE["n"],
                                "funders": ["Unknown Whale erd1hl5y4a... 35,739 EGLD", "unlabelled erd1hhvfrw... 22,987 EGLD"]},
        "binance_big_withdrawal": {"egld": 11000.0, "recipient": TR["binance_big_withdrawals"][0]["receiver"],
                                   "onward": "delegate to a staking provider contract within 2 minutes"},
        "note": "Exit-route scan over the six largest withdraw calls: two meria legs (20,120 and 7,850 EGLD) were merged into one wallet that deposited 35,949 EGLD to Binance.com at 12:18 UTC Oct 9; a Figment-linked 3,523 EGLD withdraw landed at Crypto.com, but that sender is Crypto.com's own staking-sweep wallet, so it is internal and not counted as an exit; Trust Staking re-delegated 2,892 EGLD; Valid Blocks and Ledger by Figment legs stayed in the wallet or moved on unlabelled. The one Binance withdrawal above 5,000 EGLD (11,000) went straight back into a delegation contract."},
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
        "method_note": "Third read after restart; invalid balances 2.55 EGLD, unchanged. No MultiversX technical incident report found in web search."},
    "otc_pipeline": {
        "gross_outbound_egld_7d": otc["gross_out"], "gross_inbound_egld_7d": otc["gross_in"],
        "circular_egld_7d": otc["circular"], "net_one_way_egld_7d": otc["net_one_way"],
        "circular_share_pct": otc["circ_pct"],
        "desk_balance_egld": otc["desk_bal"], "previous_desk_balance_egld": otc["prev_desk"],
        "upbit_reload_egld": otc["upbit_feed"],
        "venue_netting": [{"venue": "UPbit (reload to the UPbit OTC desk)", "desk_to_venue_egld": 0.0, "venue_to_desk_egld": UPBIT_RELOAD, "net_egld": -UPBIT_RELOAD}],
        "router_tail_delivery_egld": 0.0, "router_tail_routers": 0,
        "gross_series_egld_7d": {**r26o["gross_series_egld_7d"], "run29": otc["gross_out"]},
        "net_one_way_series_egld_7d": {**r26o["net_one_way_series_egld_7d"], "run29": otc["net_one_way"]},
        "desk_inventory_series_egld": INV_SERIES,
        "circularity_series_pct": {**r26o["circularity_series_pct"], "run29": 0.0},
        "peak_window_renetted": r26o["peak_window_renetted"],
        "backfilled_windows": r26o.get("backfilled_windows", []),
        "wave_window_netting": {**r26o["wave_window_netting"],
            "note": "Wave #4 stays closed at 467,107 EGLD one-way (Sep 7 to the halt, frozen labels). Its Gate.io router tail cleared in run #28. The post-restart window (Sep 24 - Oct 9) nets 5,924 EGLD one-way."},
        "feed_by_parent_venue": [],
        "feeder_backtrace": O["feeder_backtrace"],
        "address_poisoning": [{"address": a, "mimics": v["note"], "nonce": v["nonce"], "dust_txs_30d": v["dust_txs_30d"],
                               "distinct_targets_30d": v["distinct_targets_30d"],
                               "inbound_above_0_01_egld": len(v["inbound_above_0_01_egld"])} for a, v in PZ.items()],
        "series_note": (f"RESTART SIGNAL, 4-DAY WINDOW. The UPbit OTC desk sent {f(otc['gross_out'])} EGLD to routers on Oct 6 at 04:27-04:29 UTC (its first send since the halt; terminal erd1y27r22... unresolved), received {f(UPBIT_RELOAD)} EGLD from the UPbit exchange wallet on Oct 8 at 14:53 and passed 7,000 to the Distribution wallet at 14:57. "
                        f"Desk inventory {f(otc['desk_bal'])} (from {f(otc['prev_desk'])}). Gross 5.7K is under the 20,000 'partial' line of otc-pipeline-resumption in a 4-day window. Not appended to the throughput baselines (partial rails, short window).")},
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
    "RAILS. Value-bearing EGLD per tracked exchange wallet over Oct 5-9: "
    + "; ".join(f"{k}: {v['state'].replace('_', ' ')} ({v['in_txs']} in / {v['out_txs']} out)" for k, v in VEN.items() if v["state"] != "closed")
    + f". Closed, no EGLD moved: {', '.join(k for k, v in VEN.items() if v['state'] == 'closed')}. UPbit's only flow was a 14,000 EGLD send to its own OTC desk.\n\n"
    f"BINANCE.COM. Deposits had been open since Sep 29 (about 4,240 EGLD through Oct 5). On Oct 9 the first EGLD withdrawal left the hot wallet at {hm(BINV['first_out'])} UTC and {BINV['out_txs']} followed to 182 recipients ({f(BINV['out_egld'])} EGLD), so the native chain is open both ways there. "
    f"In the same window {BINV['in_txs']} deposits brought {f(BIN_DEP_ALL)} EGLD from {BINV['in_senders']} senders; the hot wallet rose {f(cust['hot_balance']-cust['hot_previous'])} to {f(cust['hot_balance'])}. Three wallets supplied {f(BIN_TOP3)} EGLD: "
    f"{DEP_WHALE['sender'][:12]}... (57,620 EGLD in {DEP_WHALE['n']} clips, funded by the unlabelled 'Unknown Whale' erd1hl5y4a... and erd1hhvfrw...), {DEP_MERIA['sender'][:12]}... ({f(DEP_MERIA['total_egld'])} EGLD, a meria unstaker's consolidated exit) and erd15qfhdy... (7,413). "
    "The mirror image is the one Binance withdrawal above 5,000 EGLD (11,000): it was delegated to a staking provider within two minutes. Nobody has withdrawn to sell; the large movers deposited and the large withdrawer staked. The Binance staking custody (3,493,535 EGLD) did not move.\n\n"
    f"EXIT ROUTE SCAN (run #28 rec #3). Of the six largest withdraw calls, meria's two legs ({f(MERIA_WD)} EGLD, Oct 6 15:49) became the Binance deposit above; Trust Staking re-delegated 2,892; the rest stayed on chain. Last week the same kind of EGLD went DEX to USDC to Ethereum at a ~9% discount. With a deposit rail open, the exit price is the CEX price. "
    f"No DEX-and-bridge exit of that size repeated this window; USDC supply fell {f(USDC_BURN)} ({usdc['pct']:+.2f}%).\n\n"
    f"THE UPBIT OTC DESK WOKE UP, SMALL. First post-halt send Oct 6 04:27-04:29 UTC: {f(otc['gross_out'])} EGLD to routers, ending at erd1y27r22... (unresolved). Oct 8 14:53: the UPbit exchange wallet sent 14,000 EGLD to the desk; 14:57: the desk sent 7,000 to the Distribution wallet. Desks {f(otc['desk_bal'])} (from {f(otc['prev_desk'])}). A reload of 14,000 compares with tranches above 100,000 in the pre-halt programme.\n\n"
    f"WHALES. Tiers on the common-address basis ({O['tiers_basis']} wallets): mega {O['tiers']['mega']['net_change_egld']:+,.0f} (the UPbit send), large {O['tiers']['large']['net_change_egld']:+,.0f} (Binance.com), mid {O['tiers']['mid']['net_change_egld']:+,.0f} (Hatom's EGLD market -30,692). "
    "Unknown Whale (erd1vxa2vk...) passed 7,120 and 3,024 EGLD to erd1hl5y4a... on Oct 7-8, and erd1hl5y4a... was a funder of the 57,620 EGLD Binance deposit: treat that pair as linked. Unlabelled erd1hhvfrw... fell 29,338 EGLD and funded both Binance depositors.\n\n"
    f"UNKNOWN WHALE I AND erd1a6lte0: {CEN['Unknown Whale I']['inbound_txs']} and {CEN['erd1a6lte0']['inbound_txs']} inbound transactions in four days. Still not evaluable.\n\n"
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
                   "fee_pct": mv(ident, "fee") or 0.0, "weeks_in_state": 6,
                   "note": f"SIXTH WEEK AFTER THE FEE REVERSAL: book {mv(ident,'delta'):+,.0f}, users {mv(ident,'users_delta'):+d}. Still losing capital with yield restored."})
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
                          "note": "Zero transitions for a sixth week. Join on contract address, 100% match, no identity changes."},
    "fee_events": [{"provider": i, "fee_from_pct": 100.0, "fee_to_pct": mv(i, "fee") or 0.0, "apr_from_pct": 0.0, "apr_to_pct": mv(i, "apr") or 0.0,
                    "locked_egld": mv(i, "locked"), "locked_wow_egld": mv(i, "delta"), "users": mv(i, "users"),
                    "users_wow": mv(i, "users_delta"), "num_nodes": mv(i, "nodes")} for i in ("egldstakingprovider", "procryptostaking")],
    "unbonding_in_flight": {
        "wallet": ub["wallet"], "total_egld": ub["pending_total"],
        "legs": [{"provider": p["contract"][:10] + "..." + p["contract"][-8:], "amount": p["amount_egld"],
                  "days_to_unbond": p["days_remaining"], "date": "2026-08-14" if p["amount_egld"] < 100000 else "2026-08-15"} for p in ub["pending"]],
        "share_of_delegation_decline_pct": 0.0, "raw_residual_egld": sk["residual"], "corrected_direct_node_egld": None,
        "status": f"RETIRED, EIGHTH WEEK UNMOVED. Balance {f(ub['balance'],2)} EGLD, {f(ub['pending_total'])} unbonded-and-unclaimed.",
        "queue_this_week": {
            "undelegated_egld": sk["undelegated_week"], "distinct_callers": sk["undelegate_callers"],
            "measured_pending_egld": sk["pool_total"], "largest_legs": sk["pool_rows"][:12],
            "withdraw_calls": O["withdraw_calls"], "previous_withdraw_calls": O["prev_withdraw_calls"],
            "withdraw_egld_returned": WD.get("egld_returned_total", 0.0),
            "withdraw_egld_by_provider_top": [{"provider": a, "egld": b} for a, b in wd_top[:8]],
            "undelegated_weekly_pace_egld": UNDEL_PACE, "live_days": LIVE_DAYS,
            "coverage_note": (f"Full-set scan of {sk['providers_scanned']} provider contracts over a 4-day window; the busiest provider scan hit its page cap (4.1 days of coverage). {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD; "
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
            f"COMPOUND RATE {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} reDelegateRewards vs {cvc['claim_count']} claimRewards), from 58.28%. Series: 59.07 / 57.03 / 57.51 / 62.05 / 49.44 / 62.68 / 52.40 / 58.28 / {cvc['compound_pct_of_reward_decisions']:.2f}. Inside the 57-63% range for a second week.",
            f"Retail {fates['retail']['total_events']} claims, {fates['retail']['by_count'].get('sold',0)} to a labelled exchange; mid-tier {fates['mid_tier']['total_events']}, {fates['mid_tier']['by_count'].get('sold',0)} sold; institutional {fates.get('institutional',{}).get('total_events',0)}, {fates.get('institutional',{}).get('by_count',{}).get('sold',0)} sold. Partial rails: a 'held' reading at a venue that accepts no deposits is not a choice to hold.",
            f"Sample: {ag['providers_sampled']} of {ag.get('providers_requested',8)} providers.",
            "PROVIDER OPERATORS DID NOT SELL FEES for a seventeenth consecutive run."]},
    "analysis": (
        f"A SLOWER QUEUE. {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD in four days across {sk['providers_scanned']} provider contracts, about {f(sk['undelegated_week']/LIVE_DAYS*7)} a week at this pace, under the 73-84K pre-halt weeks and last week's {f(83604)} withdrawn. The post-restart burst is not repeating; the staked ratio nonetheless fell to {100*M['sr']:.2f}% because earlier legs keep leaving /economics staked as they unbond.\n\n"
        f"THE WITHDRAWALS NOW HAVE A DESTINATION WE CAN SEE. {O['withdraw_calls']} withdraw calls returned {f(WD.get('egld_returned_total',0))} EGLD, {f(wd_top0)} of it from meria (20,120 and 7,850 EGLD legs on Oct 6, the largest). Those two legs ended as a 35,949 EGLD Binance.com deposit on Oct 9, four hours after that venue's withdrawals reopened. Trust Staking's 2,847 EGLD was re-delegated. Measured pending among the largest callers: {f(sk['pool_total'])} EGLD.\n\n"
        f"THE RATIO AND THE RESIDUAL. Staked EGLD {M['staked_chg']:+,.0f} while delegation TVL rose {sk['delta_locked']:+,.0f} to {f(tl)}, a residual of {sk['residual']:+,.0f}. Ratio {100*M['sr']:.2f}% is below run #25's 46.30% floor for a second print.\n\n"
        f"COMPOUNDING {cvc['compound_pct_of_reward_decisions']:.2f}%. DELEGATORS {sk['users_delta']:+,} to {f(sk['users'])}; {sk['gaining']} providers gained and {sk['losing']} lost. oxsyai led inflows ({mv('oxsyai','delta'):+,.0f}); inceptionnetwork ({mv('inceptionnetwork','delta'):+,.0f}) and rosettastake ({mv('rosettastake','delta'):+,.0f}) led outflows. Zero deregistration transitions for a sixth week.")}
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
        f"THE DEX WAS QUIETER AS CEX RAILS OPENED. 24h volume ${f(xx['vol'])} ({f(bid['dexvol_egld'])} EGLD) against ${f(xx['prev_vol'])} ({f(bid['prev_dexvol_egld'])} EGLD) last snapshot, {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.0f}% in EGLD terms (flat in EGLD, down in dollars with the price). "
        f"WEGLD/USDC is {bid['wegld_usdc_share']:.0f}% of it. Turnover {bid['turnover']:.2f}% of pool TVL (from {bid['prev_turnover']:.2f}%). Pool TVL {f(bid['pooltvl_egld'])} EGLD ({100*(bid['pooltvl_egld']-bid['prev_pooltvl_egld'])/bid['prev_pooltvl_egld']:+.1f}% in EGLD), ${f(bid['pooltvl'])} ({100*(bid['pooltvl']-bid['prev_pooltvl'])/bid['prev_pooltvl']:+.1f}%) in dollars. "
        "Last week's exit sold 26,678 EGLD into this venue; this window shows no single seller of that size.\n\n"
        f"MEX ${xx['mex_price']:.2e} from the pool ({xx['mex_wow']:+.1f}% over the window, against EGLD {pc:+.1f}%: MEX has held up better than EGLD); MEX/WEGLD depth ${f(xx['mex_pair_depth']['tvl_usd'])}, rank {xx['mex_pair_depth']['depth_rank']}.\n\n"
        f"STABLECOINS. USDC {usdc['pct']:+.2f}% to {f(usdc['supply'])} ({f(USDC_BURN)} burned) and USDT {usdt['pct']:+.2f}% to {f(usdt['supply'])}. Bridged dollars kept contracting at a slower pace than last week's USDC burn. "
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
        f"HATOM'S EGLD MARKET DRAINED. The EGLD money market holds {f(df['egld_mm_balance'])} EGLD, from {f(df['egld_mm_prev_balance'])} ({EMM_D:+,.0f}), and HEGLD supply is {HT['HEGLD-d61095']['supply_pct']:+.2f}%: depositors withdrew EGLD as the price fell. Aggregate lending TVL ex-HMEX reads {hl:+.2f}% in EGLD because the dollar-denominated assets (HUSDC {HT['HUSDC-d80042']['supply_pct']:+.2f}%, HUSDT {HT['HUSDT-6f0914']['supply_pct']:+.2f}%, HWBTC flat) are worth more EGLD. "
        f"The price moved more than 5% and the inverse ratio is {df['inverse_ratio_ex_hmex']:.2f} of the price change, so the inverse-ratio rule is evaluable and the book behaved mechanically.\n\n"
        f"LIQUID STAKING. SEGLD {lsd['SEGLD-3ad2d0']['pct']:+.2f}%, XEGLD {lsd['XEGLD-e413ed']['pct']:+.2f}%, SWTAO {lsd['SWTAO-356a25']['pct']:+.2f}%, USH {lsd['USH-111e09']['pct']:+.2f}%. VoxEGLD {(em['VOXEGLD-5872e5']['pct'] or 0):+.1f}%. Discovery sweep: eight protocols found, two of them 1-2 EGLD test deployments.\n\n"
        f"ACTIVITY. XOXNO aggregator {f(cnt('XOXNO Aggregator'))} transfers in 24h, OneDex {f(cnt('OneDex Swap'))}, Hatom LSD {f(cnt('Hatom Liquid Staking'))}.")}

# ---------------------------------------------------------------------------
R["anomalies"] = [
    {"metric": "egld_price_usd", "current_value": price, "previous_value": M["prev_price"], "method": "z_score", "severity": "high" if abs(pc) > 10 else z["price"].get("severity", "low"),
     "average_value": z["price"].get("mean"), "stddev": z["price"].get("stddev"), "z_score": zz("price"), "change_pct": pc,
     "description": f"{pc:+.2f}% in four days (BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%); z={zz('price'):+.2f} against an 8-run baseline that mixes halt-period prices, so the rule-based read (>10% move, {abs(EGLD_VS_BTC):.1f}pp worse than BTC) is the operative one."},
    {"metric": "binance_com_deposits_egld", "current_value": BIN_DEP_ALL, "previous_value": 4240.0, "method": "rule_based", "severity": "high",
     "change_pct": 100 * (BIN_DEP_ALL - 4240.0) / 4240.0,
     "description": f"{f(BIN_DEP_ALL)} EGLD of deposits from {BINV['in_senders']} senders in four days against about 4,240 through Oct 5; three wallets supplied {f(BIN_TOP3)}. Withdrawals started Oct 9 08:04 UTC ({f(BINV['out_egld'])} EGLD, {BINV['out_txs']} txs)."},
    {"metric": "meria_unstake_to_binance_egld", "current_value": DEP_MERIA["total_egld"], "previous_value": 0, "method": "rule_based", "severity": "medium",
     "description": f"Two meria withdrawals ({f(MERIA_WD)} EGLD, Oct 6) fed a {f(DEP_MERIA['total_egld'])} EGLD Binance.com deposit on Oct 9: the first traced unstaking exit to a CEX since the halt."},
    {"metric": "korea_premium_pct", "current_value": PREM, "previous_value": PREM_PREV, "method": "rule_based", "severity": "medium",
     "change_pct": 100 * (PREM - PREM_PREV) / PREM_PREV,
     "description": f"Upbit premium {PREM:.1f}% from {PREM_PREV:.1f}% with UPbit deposits still closed; Upbit share of global volume {UP_SHARE:.0f}% from {UPSH_PREV:.0f}%."},
    {"metric": "otc_desk_gross_outbound_egld", "current_value": otc["gross_out"], "previous_value": 0, "method": "rule_based", "severity": "low",
     "description": f"First post-halt desk send: {f(otc['gross_out'])} EGLD Oct 6, UPbit reload {f(UPBIT_RELOAD)} Oct 8. Far under the pre-halt programme."},
    {"metric": "hatom_egld_market_balance", "current_value": df["egld_mm_balance"], "previous_value": df["egld_mm_prev_balance"], "method": "rule_based", "severity": "medium",
     "change_pct": 100 * EMM_D / df["egld_mm_prev_balance"],
     "description": f"Hatom's EGLD money market {EMM_D:+,.0f} EGLD; HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.2f}%."},
    {"metric": "staked_ratio", "current_value": M["sr"], "previous_value": M["sr_prev"], "method": "z_score", "severity": z["sr"].get("severity", "low"),
     "average_value": z["sr"].get("mean"), "stddev": z["sr"].get("stddev"), "z_score": zz("sr"), "change_pct": 100 * (M["sr"] - M["sr_prev"]) / M["sr_prev"],
     "description": f"Staked ratio {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp), z={zz('sr'):+.2f}: a new low."},
    {"metric": "cex_spot_volume_7d_egld", "current_value": BOOK["spot_volume_7d_egld"], "previous_value": BOOK["spot_volume_prior_7d_egld"], "method": "rule_based", "severity": "low",
     "change_pct": 100 * (BOOK["spot_volume_7d_egld"] - BOOK["spot_volume_prior_7d_egld"]) / BOOK["spot_volume_prior_7d_egld"],
     "description": f"7-day CEX spot volume {f(BOOK['spot_volume_7d_egld']/1e6,2)}M EGLD, from {f(BOOK['spot_volume_prior_7d_egld']/1e6,2)}M."},
]

R["trend_indicators"] = {
    "accelerating_exchange_outflows": [],
    "validator_movements": {"providers_joining": 0, "providers_leaving": 0, "net_provider_change": 0, "notable_joiners": [], "notable_leavers": []},
    "token_supply_events": [
        {"identifier": "USDT-f8c08c", "name": "USDT", "event": "burn", "supply_previous": str(int(usdt["prev"])), "supply_current": str(int(usdt["supply"])),
         "change_pct": usdt["pct"], "description": f"{f(usdt['prev']-usdt['supply'])} USDT redeemed."},
        {"identifier": "USDC-c76f1f", "name": "WrappedUSDC", "event": "burn", "supply_previous": str(int(usdc["prev"])), "supply_current": str(int(usdc["supply"])),
         "change_pct": usdc["pct"], "description": f"{f(USDC_BURN)} USDC redeemed, a fraction of last week's burn."},
        {"identifier": "HEGLD-d61095", "name": "HEGLD", "event": "burn", "supply_previous": str(int(float(HT['HEGLD-d61095']['prev_supply']))), "supply_current": str(int(float(HT['HEGLD-d61095']['supply']))),
         "change_pct": HT["HEGLD-d61095"]["supply_pct"], "description": "EGLD withdrawn from Hatom's money market as the price fell."}],
    "consecutive_streaks": [
        {"metric": "staked_ratio", "direction": "down", "weeks": 4, "cumulative_change_pct": 100 * (M["sr"] - 0.4655083730551601) / 0.4655083730551601,
         "interpretation": f"46.55% / 46.59% / 46.48% / 46.27% / {100*M['sr']:.2f}%: a slow grind lower since the September step down."},
        {"metric": "usdt_supply", "direction": "down", "weeks": 5, "cumulative_change_pct": 100 * (usdt["supply"] - 463905) / 463905,
         "interpretation": f"463,905 to {f(usdt['supply'])}: bridged dollars keep leaving MultiversX, slowly."},
        {"metric": "total_delegators", "direction": "flat", "weeks": 17, "cumulative_change_pct": -1.1, "interpretation": f"{sk['users_delta']:+,} to {f(sk['users'])}. Still the base rate."},
        {"metric": "provider_operator_fee_selling", "direction": "flat", "weeks": 17, "cumulative_change_pct": 0.0, "interpretation": "Seventeen runs with zero exchange destinations from sampled operator wallets."}],
    "regime_shifts": [
        {"metric": "exit_route", "before_value": 0.0, "after_value": 1.0,
         "description": "CANDIDATE, supersedes last week's DEX-and-bridge candidate: with a CEX deposit rail open (Binance.com), a traced unstaking exit went to the exchange instead. Two observations, opposite routes, one variable (rail state). Promote only if the next window repeats."},
        {"metric": "exchange_rail_state", "before_value": 0.0, "after_value": round(len(OPEN) / max(1, len(VEN)), 2),
         "description": f"Binance.com now moves EGLD both ways ({len(OPEN)} of {len(VEN)} tracked venues open); UPbit, Bybit, Coinbase, MEXC, KuCoin remain closed. Still changing week to week, not promoted."}]}

R["watch_list"] = [
    {"item": "BINANCE.COM - first days of two-way flow", "weeks_on_list": 1,
     "reason": f"{f(BIN_DEP_ALL)} EGLD deposited, {f(BINV['out_egld'])} withdrawn since 08:04 UTC Oct 9; hot wallet {f(cust['hot_balance'])}. Does the deposit pressure continue while the price sits at ${price:.2f}? PRE-COMMITTED (binance-deposit-persistence)."},
    {"item": "UPBIT CAUTION REVIEW Oct 19-23 and the KOREA PREMIUM", "weeks_on_list": 3,
     "reason": f"Premium {PREM:.1f}% (from {PREM_PREV:.1f}%), {UP_SHARE:.0f}% of global volume, deposits and withdrawals closed. upbit-premium-decay resolved against; korea-premium-arbitrage still open."},
    {"item": "OTC PIPELINE - first sends since the halt", "weeks_on_list": 29,
     "reason": f"Desk gross {f(otc['gross_out'])} Oct 6, UPbit reload {f(UPBIT_RELOAD)} Oct 8, desks {f(otc['desk_bal'])}. PRE-COMMITTED (otc-pipeline-resumption)."},
    {"item": "UNSTAKED EGLD ROUTING", "weeks_on_list": 2,
     "reason": f"meria legs to Binance.com ({f(DEP_MERIA['total_egld'])}); {f(sk['pool_total'])} EGLD measured pending among the largest callers. PRE-COMMITTED (exit-route-cex)."},
    {"item": "UNKNOWN WHALE erd1hl5y4a... / erd1vxa2vk... / erd1hhvfrw...", "weeks_on_list": 1,
     "reason": "Linked unlabelled wallets that funded 57,620 EGLD of Binance deposits (35,739 + 22,987 from two of them). Watch for more deposits and whether any hold remains."},
    {"item": "STAKED RATIO NEW LOW", "weeks_on_list": 2,
     "reason": f"{100*M['sr']:.2f}%, staked {M['staked_chg']:+,.0f} in four days."},
    {"item": "HATOM EGLD MARKET", "weeks_on_list": 1,
     "reason": f"{EMM_D:+,.0f} EGLD in four days at a lower price; check whether borrowers or suppliers drove it."},
    {"item": "UNKNOWN WHALE I AND erd1a6lte0 - probable exchange hot wallets", "weeks_on_list": 4,
     "reason": "Zero inbound in four days again; if Binance.com is their venue they should have woken up."},
    {"item": "INCIDENT REPORTS - MultiversX technical report and Hatom MEX report", "weeks_on_list": 4,
     "reason": "No MultiversX technical incident report found in web search; none found from Hatom."},
    {"item": "EXPLOIT WALLET AND POISONING RING", "weeks_on_list": 4,
     "reason": f"Incident addresses hold {HR['invalid_total_egld']:.2f} EGLD; poisoning operator {PR['operator_out_7d']}+ dust txs (page cap)."},
]

# ---------------------------------------------------------------------------
prior = {t["id"]: t for t in r26["pre_committed_tests"]}
tests = [t for t in r26["pre_committed_tests"] if t["status"] == "resolved"]


def resolve(tid, outcome, measured, resolution):
    t = dict(prior[tid]); t.update({"status": "resolved", "outcome": outcome, "resolved_in_run": 29, "measured_value": measured, "resolution": resolution}); return t


tests.append(resolve("upbit-premium-decay", PREM_RESULT,
    f"premium {PREM:.2f}% (Upbit ${up['converted_last']['usd']:.2f} vs Binance ${bn['converted_last']['usd']:.2f}), UPbit EGLD deposits closed (hot wallet: one 0.0001 EGLD dust receive, one 14,000 send to its own OTC desk)",
    f"Above the 15% line: the premium re-widened from {PREM_PREV:.1f}% rather than decaying to < 5%, so the claim that it is fading Korean demand fails. It is the exchange price move: Binance fell {abs(pc):.0f}% while Upbit (KRW) held, which widens the gap without any EGLD reaching Korea. korea-premium-arbitrage stays open."))
for tid, note in [("unknown-whale-i-is-exchange", f"run #29: {CEN['Unknown Whale I']['inbound_txs']} inbound txs in 4 days, 0 outbound, even with Binance.com reopened. Not evaluable; deadline unchanged."),
                  ("delivery-price-relevance-2", f"run #29: desk gross {f(otc['gross_out'])} EGLD in the window, nowhere near the 300,000 net one-way bar. Not evaluable."),
                  ("korea-premium-arbitrage", f"run #29: premium {PREM:.1f}%; UPbit hot wallet received no customer EGLD deposits (needs >= 20 distinct senders). Open until UPbit deposits reopen.")]:
    t = dict(prior[tid]); t.update({"status": "open", "measured_value": note, "resolution": None}); tests.append(t)
t = dict(prior["otc-pipeline-resumption"]); t.update({"status": "open", "measured_value": f"run #29 (4-day window): desk gross {f(otc['gross_out'])} EGLD, UPbit reload {f(UPBIT_RELOAD)}, desks {f(otc['desk_bal'])}. Under the 20,000 partial line; a 4-day window is not a weekly one.", "resolution": None}); tests.append(t)


def new(tid, claim, threshold, branches, measured):
    return {"id": tid, "registered_in_run": 29, "claim": claim, "threshold": threshold, "branches": branches,
            "status": "open", "outcome": None, "resolved_in_run": None, "measured_value": measured, "resolution": None}


tests += [
    new("binance-deposit-persistence", "The Binance.com deposit surge is the unstaked-EGLD overhang reaching a CEX and continues, not a one-day reopening artifact.",
        "At run #30, Binance.com hot-wallet value-bearing deposits minus withdrawals per day of window: > +10,000 EGLD/day = overhang still arriving; -5,000 to +10,000 = no conclusion; < -5,000 EGLD/day = withdrawals dominate, the surge was the reopening",
        [{"condition": "> +10,000 EGLD/day net", "reading": "overhang still arriving"},
         {"condition": "-5,000 to +10,000", "reading": "no conclusion"},
         {"condition": "< -5,000 EGLD/day", "reading": "reopening artifact"}],
        f"run #29: deposits {f(BIN_DEP_ALL)} and withdrawals {f(BINV['out_egld'])} (the withdrawals started Oct 9 08:04, hours before collection); hot wallet {cust['hot_balance']-cust['hot_previous']:+,.0f}"),
    new("exit-route-cex", "With a CEX deposit rail open, unstaking exits go to the exchange, not through the DEX and bridge.",
        "At run #30, among withdraw calls > 3,000 EGLD in the window whose proceeds can be traced: > 50% of EGLD to a CEX deposit = CEX route dominant; < 25% = the DEX/bridge route persists despite the open rail; USDC burn in the window > 50,000 = bridge route active",
        [{"condition": "> 50% traced to CEX deposits", "reading": "CEX route dominant"},
         {"condition": "< 25% to CEX", "reading": "DEX/bridge persists"},
         {"condition": "25-50%", "reading": "mixed"}],
        f"run #29: of the six largest withdraw calls, {f(MERIA_WD)} EGLD (meria) went to Binance.com; Trust Staking re-delegated; no repeat of the 26,678 EGLD DEX sale"),
]
resolved = [t for t in tests if t.get("resolved_in_run") == 29]
as_pred = sum(1 for t in resolved if t["outcome"] == "as_predicted")
R["pre_committed_tests"] = tests

# ---------------------------------------------------------------------------
R["meta_learning"] = {
    "run_number": 29,
    "endpoints_that_worked": status["ok"],
    "endpoints_that_failed": [f"NONE with data missing. {D.get('_n_429', 0)} HTTP 429s; 1 API error logged; the busiest provider scan hit its page cap at 4.1 days of coverage (full window)."],
    "api_quirks": [
        "OFF-CADENCE WINDOWS: when the previous snapshot is less than 7 days old the collector window is snapshot-to-now; per-week figures (undelegation pace, DEX volume) must be labelled 4-day or scaled, never compared raw with 7-day history.",
        "A SENDER THAT LOOKS LIKE AN UNSTAKER MAY BE AN EXCHANGE'S OWN SWEEP WALLET: the 3,523 EGLD Figment withdraw that landed at Crypto.com came from Crypto.com's internal staking-sweep wallet (erd1uskf6...), already labelled; check known-addresses before calling a withdraw-to-exchange an exit.",
        "pgrep -f in a wait loop matches its own shell: use a done-file instead."],
    "data_gaps": [
        "No Binance announcement found for the native-network reopening; state inferred from chain data.",
        "Kraken has no tracked address.",
        "The desk's Oct 6 outbound terminates at erd1y27r22... (unresolved).",
        "MultiversX has published no technical incident report (web search).",
        "Hatom UTK Money Market and OneDex Launchpad still fail bech32 validation."],
    "key_findings": [
        f"EGLD {pc:+.2f}% to ${price:.2f} in four days (BTC {M['btc_wow']:+.2f}%).",
        f"Binance.com reopened withdrawals Oct 9 08:04 UTC; {f(BIN_DEP_ALL)} EGLD deposited, {f(BINV['out_egld'])} withdrawn.",
        f"Two meria withdrawals ({f(MERIA_WD)} EGLD) fed a {f(DEP_MERIA['total_egld'])} EGLD Binance.com deposit: exits switch to CEX when a rail is open.",
        f"UPbit OTC desk's first post-halt send ({f(otc['gross_out'])}) and a {f(UPBIT_RELOAD)} reload.",
        f"Upbit premium {PREM:.1f}% from {PREM_PREV:.1f}%: upbit-premium-decay resolved against.",
        f"Staked ratio {100*M['sr']:.2f}% (new low); Hatom EGLD market {EMM_D:+,.0f}."],
    "action_items_from_previous": len(r26["meta_learning"]["recommendations_for_next_run"]),
    "action_items_completed_detail": [
        "RAILS FIRST - done: the rail check script; Binance.com is open both ways; UPbit still closed, so korea-premium-arbitrage and delivery-price-relevance-2 stay open.",
        "RESOLVE upbit-premium-decay - done: resolved against (premium 15.4% with UPbit closed).",
        "EXIT-ROUTE SCAN - done for the six largest withdraw calls (targeted trace script); it found the meria-to-Binance route. Not yet a collector-side scan of every withdraw > 1,000.",
        "ADD KRAKEN / CHECK BINANCE BEP-20 - not done: no Kraken address located; web search found no Binance notice.",
        "SLOW THE PROVIDER SCAN - not done: global 4 req/s budget retained; 429s recovered by backoff.",
        "OTC: watch for the first post-halt send - done: Oct 6 04:27 UTC, 5,745 EGLD."],
    "methodology_changes": [
        "OFF-CADENCE RUNS: label every flow with the window length; do not append 4-day flows to weekly baselines (exchange and OTC flows were not appended).",
        "EXIT TRACES CHECK THE KNOWN-ADDRESS LABEL OF THE SENDER before calling a withdraw-to-exchange transfer an exit (Crypto.com's own sweep wallet).",
        "Resolve routing questions from the funding chain two hops back: the largest Binance depositors were funded by wallets already on the watch list."],
    "new_addresses_discovered_detail": [
        f"{DEP_WHALE['sender']} - Binance.com depositor, 57,620 EGLD in twelve clips Oct 9; funded by erd1hl5y4a... and erd1hhvfrw...",
        f"{DEP_MERIA['sender']} - consolidated meria unstaker, 35,949 EGLD to Binance.com Oct 9",
        "erd16pe79ay2m6g7ap9vpshvvqaqc3ayplwuqw0rkwj2gqvv0egn0wjsyzvjwd - received the 11,000 EGLD Binance withdrawal and delegated it within 2 minutes"],
    "action_items_completed": 4,
    "new_addresses_discovered": 3,
    "most_valuable_insight": (
        f"The exit route follows the rail. Last week an unstaker paid ~9% to leave through the DEX and the Ethereum bridge because CEX deposits were closed; this week, with Binance.com open, two meria withdrawals ({f(MERIA_WD)} EGLD) fed a {f(DEP_MERIA['total_egld'])} EGLD Binance deposit four hours after withdrawals reopened. "
        f"{f(BIN_DEP_ALL)} EGLD of deposits and a {abs(pc):.0f}% price fall arrived together."),
    "top_recommendation": "RUN #30 FIRST: Binance.com per-day net deposits (binance-deposit-persistence), then the exit-route scan over every withdraw > 3,000 EGLD (exit-route-cex).",
    "recommendations_for_next_run": [
        "BINANCE FIRST: value-bearing deposits and withdrawals per day for Binance.com since Oct 9 08:04; resolve binance-deposit-persistence; check whether the unlabelled funder wallets (erd1hl5y4a, erd1hhvfrw, erd1vxa2vk) deposit again.",
        "EXIT-ROUTE SCAN, collector side: every withdraw call > 3,000 EGLD, next hop classified CEX / DEX / bridge / re-delegate / held; resolve exit-route-cex. Check the sender against known-addresses first (Crypto.com sweep wallet).",
        "Resolve the OTC desk terminal erd1y27r22... and watch for the next UPbit reload (otc-pipeline-resumption).",
        "Upbit decision window is Oct 19-23: keep premium and Upbit volume share series; korea-premium-arbitrage deadline moves to the first run with UPbit deposits open.",
        "Hatom EGLD market: classify who withdrew the 30,848 EGLD (suppliers vs liquidations) from the market's call history.",
        "Return to the Monday cadence and state the window length in every flow."],
    "dashboard_feature_suggestions": [
        {"title": "Funding-chain graph for CEX deposits",
         "motivation": f"The week's two largest Binance depositors ({f(DEP_WHALE['total_egld'])} and {f(DEP_MERIA['total_egld'])} EGLD) each had a one- or two-hop funding chain back to a named provider withdraw or a watch-list wallet. A bar chart of deposits hides that the sellers are linked.",
         "suggested_visualization": "force-directed graph: provider withdraw -> consolidating wallet -> exchange deposit, edge width = EGLD, node colour = labelled / unlabelled / exchange",
         "data_already_available": False, "data_source": "whale_intelligence.exit_routes plus a collector-side two-hop funding trace for the top 10 exchange depositors", "priority": "high"},
        {"title": "Price vs venue-flow overlay (hourly)",
         "motivation": f"EGLD fell {abs(pc):.0f}% on Oct 7-9 while Binance.com first took deposits at scale and then reopened withdrawals at 08:04 UTC Oct 9. Daily points cannot show whether the price moved before or after the flows.",
         "suggested_visualization": "dual-axis hourly chart: EGLD price line over stacked bars of deposits and withdrawals at open venues, with rail-reopening markers",
         "data_already_available": False, "data_source": "new hourly query of exchange_rails transactions plus CoinGecko hourly price", "priority": "medium"}],
    "dashboard_suggestions_followup": [
        {"title": "Exit-route Sankey for unbonded EGLD", "status": "pending",
         "note": "Not built; this run's meria-to-Binance route (CEX instead of DEX/bridge) is a second observation that the Sankey needs per-route weekly totals."},
        {"title": "Rail reopening timeline per venue", "status": "pending",
         "note": "Not built; Binance.com's Oct 9 08:04 first withdrawal (deposits open since Sep 29) is exactly the deposit-first, withdrawal-later ordering it would show. Data already in rail_status.by_venue."}],
    "withdrawn_claims": [],
}

rep = {k: R[k] for k in ["metadata", "executive_summary", "network_health", "whale_intelligence", "staking_intelligence", "token_activity",
                         "defi_activity", "anomalies", "trend_indicators", "watch_list", "meta_learning", "pre_committed_tests"]}
json.dump(rep, open(f"{REPO}/reports/{RD}.json", "w"), indent=1, default=str)
print("report written", len(json.dumps(rep, default=str)), "bytes")
print(f"tests resolved this run {len(resolved)}, as_predicted {as_pred}, open {sum(1 for t in tests if t['status']=='open')}")
print("PREM", round(PREM, 1), "UP_SHARE", round(UP_SHARE, 1), "OPEN", OPEN, "DEPONLY", DEPONLY)
