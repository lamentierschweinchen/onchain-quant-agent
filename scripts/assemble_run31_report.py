#!/usr/bin/env python3
"""Run #31 stage 2: assemble reports/2026-10-15.json from derived.json + snapshot.

~2.7-day window (Oct 9 21:00 -> Oct 12). Defining facts: Binance unDelegated 320,002 EGLD from binance_staking and moved
161,137 EGLD hot -> custody on Oct 12; Coinbase (Oct 10) and Bybit (Oct 12) reopened; Whale B -> Coinbase -> Mega Whale 120K.
"""
import json
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD = "2026-10-15"
O = json.load(open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/ac9fba45-13d5-4386-8dce-5e7be1f1def0/scratchpad/run31w/derived.json"))
D = json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev = json.load(open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/ac9fba45-13d5-4386-8dce-5e7be1f1def0/scratchpad/run31w/previous_run30.json"))
status = json.load(open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/ac9fba45-13d5-4386-8dce-5e7be1f1def0/scratchpad/run31w/status.json"))
beh = json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
r26 = json.load(open(f"{REPO}/reports/2026-10-12.json"))   # previous report (name kept for the reused blocks)
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

# ---- run #31 traces ----
TR = D["run31_traces"]
BINV = VEN["Binance.com"]
BD = TR["binance_daily"]["days"]
BIN_DEP = BINV["in_egld"]; BIN_WD_EXT = BINV["out_egld"]
BIN_EXT_NET = BIN_DEP - BIN_WD_EXT
BIN_EXT_PER_DAY = BIN_EXT_NET / LIVE_DAYS
BIN_ENTITY_NET = next((e2["net_flow_egld"] for e2 in ex["entity"] if e2["entity"] == "Binance"), 0.0)
BU = TR["binance_unbond"]
BIN_UNDEL = sum(int(u["amount"]) for d_ in BU["delegation"] for u in (d_.get("userUndelegatedList") or [])) / 1e18
BIN_UNDEL_SECS = max([u["seconds"] for d_ in BU["delegation"] for u in (d_.get("userUndelegatedList") or [])] or [0])
BIN_UNDEL_DAYS = BIN_UNDEL_SECS / 86400
BIN_MATURES = iso(D["liveness"]["0"]["timestamp"] + BIN_UNDEL_SECS)
POOL = D.get("unbonding_pool") or []
NINJA = next(r for r in sk["pool_rows"] if r["wallet"].startswith("erd1me5hmqt5qg") and r["amount_egld"] > 20000)
RETAIL_UNDEL = sk["undelegated_week"] - NINJA["amount_egld"]
BINP = next(m for m in sk["moves"] if m["identity"] == "binance_staking")
NINJAP = next(m for m in sk["moves"] if m["identity"] == "ninjastaking")
EXS = TR["exit_route_scan"]; EXR = EXS["by_route"]
EXIT_TRACED = sum(r["withdrawn_egld"] for r in EXS["rows"] if r["route"] != "internal")
EXIT_CEX = sum(r["withdrawn_egld"] for r in EXS["rows"] if r["route"] == "cex")
TERM = TR["desk_terminal"]; TERM_BAL = int(TERM["info"]["balance"]) / 1e18
HMM = TR["hatom_egld_mm"]
ARB = TR["arb_wallets"]; CBL = TR["coinbase_legs"]; UPD = TR["upbit_depositors"]
ARB_GATE_IN = ARB["erd1d2anjjha"]["out_by_counterparty"].get("Gate.io", 0.0)
GATE_NET = next((e2["net_flow_egld"] for e2 in ex["entity"] if e2["entity"] == "Gate.io"), 0.0)
EX_NET_EX_ARB = ex["net"] - ARB_GATE_IN
OVERLAP_NOTE = "Run #30's rail pass read exchange flows up to 15:05 UTC Oct 12, past its 14:48 window end; this run's rail window starts at 15:05:30 so nothing is counted twice (the 15,179 EGLD Gate.io -> Binance.com arbitrage deposit at 15:00 belongs to run #30). Balance-based exchange deltas still run from 14:48 and include that deposit."
MEGA_IN = bid["mega_delta"]
UPBIT_DEP = VEN.get("UPbit", {}).get("in_egld", 0); UPBIT_DEP_N = VEN.get("UPbit", {}).get("in_senders", 0)
USDC_BURN = usdc["prev"] - usdc["supply"]
PREV_BOOK = prev["exchange_orderbook_latest"]
PREM_PREV = PREV_BOOK.get("korea_premium_pct", 18.8)
UPSH_PREV = PREV_BOOK.get("upbit_share_of_volume_pct", 17.7)
WIN_TXT = f"{LIVE_DAYS:.1f}-day window (Oct 12 14:48 -> Oct 15 {hm(D['liveness']['0']['timestamp'])[-5:]} UTC)"
WINDOW_NOTE = f"{WIN_TXT}: the Thursday snapshot after Monday's, so every flow below is a {LIVE_DAYS:.1f}-day flow."
wd_top0 = (WD.get("by_provider_top") or [[0, 0]])[0][1]
R = {}
R["metadata"] = {
    "report_date": RD, "period_start": "2026-10-12", "period_end": RD,
    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "egld_price_usd": price, "btc_price_usd": M["btc"], "eth_price_usd": M["eth"],
    "run_number": 31,
    "data_sources_ok": status["ok"] + [
        f"follow-up pass: {WD.get('calls', 0)} withdraw calls decoded, poisoning lookalikes re-scanned (0 errors)",
        "rail check (rails_run31.py): value-bearing EGLD deposits/withdrawals per tracked exchange wallet, window start de-duplicated against run #30 (15:05:30 UTC Oct 12)",
        "targeted traces (trace_run31.py): exit-route scan over every withdraw > 3,000 EGLD, Binance.com daily rails since Oct 9, Binance de-staking wallet /delegation (unbond status), cross-venue wallets by counterparty, Coinbase routing / Whale B / Mega Whale legs, UPbit depositor census since restart 2, Hatom EGLD market calls",
        "web check: Upbit / Coinbase / Bybit EGLD network notices (no new notice found beyond the Oct 19-23 Upbit review)"],
    "data_sources_failed": status["failed"],
    "data_sources_recovered": [
        "LIVENESS GATE PASSED: every shard within seconds of real time at collection",
        f"{D.get('_n_429', 0)} HTTP 429 responses in the main pass; 0 paged errors, 0 API errors",
        OVERLAP_NOTE,
        WINDOW_NOTE,
        f"delegator reward behaviour sampled {ag['providers_sampled']} of {ag.get('providers_requested', 8)} providers"]}

R["executive_summary"] = [
    {"category": "network", "severity": "high", "finding":
     f"EGLD {pc:+.1f}% TO ${price:.2f}, THE LOWEST READING SINCE AUG 17 AND -23% FROM OCT 5's $4.60, WHILE BTC FELL {abs(M['btc_wow']):.1f}% AND ETH {abs(M['eth_wow']):.1f}%. EGLD trailed BTC by {abs(EGLD_VS_BTC):.1f}pp over {LIVE_DAYS:.1f} days, the fourth consecutive window it underperformed (z = {zz('price'):+.2f}). "
     f"Order books thinned with it: Binance bids within 2% of mid ${f(BOOK['binance']['depth_minus2_usd'])} (from $45,076). The Upbit premium narrowed to {PREM:.1f}% (from {PREM_PREV:.1f}%) and Upbit's share of global volume fell to {UP_SHARE:.0f}% (from {UPSH_PREV:.0f}%) ahead of its Oct 19-23 review."},
    {"category": "whale", "severity": "medium", "finding":
     f"EXCHANGES TOOK IN A NET {f(ex['net'])} EGLD ON A FALLING PRICE. Binance.com {BIN_ENTITY_NET:+,.0f}, Coinbase {next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Coinbase'),0):+,.0f}, Crypto.com {next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Crypto.com'),0):+,.0f}, Bybit {next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Bybit'),0):+,.0f}, Gate.io {GATE_NET:+,.0f}. "
     f"Two adjustments shrink it: about 15,000 of Binance's balance gain is a run #30 arbitrage deposit that landed after its window end, and {f(ARB_GATE_IN)} of Gate.io's inflow is one cross-venue wallet emptying into it. On de-duplicated rails Binance.com customers deposited {f(BIN_DEP)} and withdrew {f(BIN_WD_EXT)} ({BIN_EXT_PER_DAY:+,.0f}/day), down from +19,776/day: the Binance deposit lead has faded to flat."},
    {"category": "staking", "severity": "medium", "finding":
     f"BINANCE'S {f(BIN_UNDEL)} EGLD UNBOND IS STILL PENDING. /delegation on erd1r3w62vq... shows the full amount undelegated with {BIN_UNDEL_DAYS:.1f} days left (matures about {BIN_MATURES[:16]}); the wallet made no transactions this window and custody is unchanged at {f(cust['balance'])}. "
     f"binance_staking itself rose {BINP['delta']:+,.0f} to {f(BINP['locked'])}. binance-undelegation-destination is evaluable at run #32 or #33."},
    {"category": "staking", "severity": "medium", "finding":
     f"A SECOND LARGE SINGLE EXIT: {f(NINJA['amount_egld'])} EGLD FROM NINJASTAKING. Wallet erd1me5hmqt5qg... unDelegated it in one call (ninjastaking {NINJAP['delta']:+,.0f} to {f(NINJAP['locked'])}); it unbonds in {NINJA['days_remaining']:.0f} days and the wallet holds {f(NINJA['wallet_balance_egld'])} EGLD. "
     f"{sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD in {LIVE_DAYS:.1f} days; the other {sk['undelegate_callers']-1} account for {f(RETAIL_UNDEL)}, about {f(RETAIL_UNDEL/LIVE_DAYS*7)}/week at this pace (run #30: ~54,000). Delegators flat ({sk['users_delta']:+d}); staked ratio {100*M['sr']:.2f}%."},
    {"category": "token", "severity": "medium", "finding":
     f"USDC SUPPLY FELL {f(USDC_BURN)} ({usdc['pct']:+.2f}%) TO {f(usdc['supply'])}, above the 50,000 line exit-route-cex used for an active bridge route; USDC has now fallen in seven of the last eight readings, about 508,000 since the first stored value (7.71M). USDT {usdt['pct']:+.2f}%. "
     f"Read with the price: wrapped USDC was redeemed, most likely bridged out, while EGLD went to exchanges; the burn was not traced to transactions this run. xExchange 24h volume ${f(bid['dexvol'])} ({100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.0f}% in EGLD), {bid['wegld_usdc_share']:.0f}% WEGLD/USDC; pool TVL ${f(bid['pooltvl'])}."},
    {"category": "whale", "severity": "low", "finding":
     f"THE WHALE CHANNELS WENT QUIET. No Whale B -> Coinbase -> Mega Whale leg (Mega Whale {f(bid['mega_bal'])}, Whale B {f(CBL['whale_b']['balance_egld'])}, routing wallet {f(CBL['cb_routing']['balance_egld'], 1)}, no transactions). OTC desks sent nothing ({f(otc['desk_bal'])} held). "
     f"UPbit's hot wallet had no EGLD flow at all: {UPD['distinct_depositors']} distinct depositors since the restart, far under the 20 that would make korea-premium-arbitrage evaluable. otc-pipeline-resumption closes not evaluable."},
    {"category": "defi", "severity": "low", "finding":
     f"HATOM'S EGLD MARKET OUTFLOW SLOWED TO {EMM_D:+,.0f} EGLD ({100*EMM_D/df['egld_mm_prev_balance']:+.1f}%) TO {f(df['egld_mm_balance'])}; HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.1f}%. {HMM['redeem_calls']} redeem calls, {HMM['by_function'].get('mintAndEnterMarket',{}).get('n',0)} new supply-and-collateral calls and {HMM['liquidation_calls']} liquidations in the window. "
     f"VoxEGLD supply +{em['VOXEGLD-5872e5']['pct']:.0f}% to {f(em['VOXEGLD-5872e5']['supply'])}, a seventh week of growth."},
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
               "btc_correlation_note": f"BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%, EGLD {pc:+.2f}%: EGLD fell {abs(EGLD_VS_BTC):.1f}pp against BTC over {LIVE_DAYS:.1f} days; ETH fell almost as much, so part of this was a broad risk-off move, but EGLD still did worst."},
    "liveness": {"ok": D["liveness_ok"], "latest_block_by_shard": {k: iso(v["timestamp"]) for k, v in D["liveness"].items()},
                 "restart_1_utc": iso(1790181300), "restart_1_stopped_utc": iso(1790182386), "restart_2_utc": iso(1790263800),
                 "live_days_in_window": LIVE_DAYS, "rollback_point_utc": "2026-09-19 06:37:45 UTC"},
    "analysis": (
        f"WINDOW. {WINDOW_NOTE} Every shard read within seconds of real time. Epoch {st['epoch']} ({st['epoch']-pact['epoch']:+d}), "
        f"{f(st['transactions']-pact['total_transactions'])} transactions (~{f(int((st['transactions']-pact['total_transactions'])/LIVE_DAYS))}/day), {f(st['accounts']-pact['total_accounts'])} new accounts. Total supply {f(econ['totalSupply'])} ({econ['totalSupply']-pecon['total_supply']:+,}).\n\n"
        f"STAKING. Staked EGLD {M['staked_chg']:+,.0f} to {f(econ['staked'])}; ratio {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp), flat. Delegation TVL fell {f(abs(sk['delta_locked']))}, mostly one {f(NINJA['amount_egld'])} EGLD unDelegate from ninjastaking. "
        f"Binance's {f(BIN_UNDEL)} EGLD (Oct 12) is still in the unbonding queue and still counted as staked; the ratio should step down about {100*BIN_UNDEL/econ['circulatingSupply']:.1f}pp when it matures (~{BIN_MATURES[:10]}) unless Binance re-stakes it. Network APR {100*econ['apr']:.2f}%.\n\n"
        f"PRICE. EGLD ${price:.2f}, {pc:+.2f}%, against BTC {M['btc_wow']:+.2f}% and ETH {M['eth_wow']:+.2f}%: the fourth consecutive window in which EGLD trailed BTC (runs #28-#31), and -23% from the Oct 5 reading ($4.60). "
        f"Bids thinned: Binance within 2% ${f(BOOK['binance']['depth_minus2_usd'])} (from $45,076), all venues ${f(BOOK['all']['depth_minus2_usd'])}. Global CEX spot volume over 7 days {f(BOOK['spot_volume_7d_egld']/1e6, 2)}M EGLD, against {f(BOOK['spot_volume_prior_7d_egld']/1e6, 2)}M a week earlier: more volume on a lower price, which is selling, not a lack of interest.")}


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


INV_SERIES = {**prev["otc_desk_inventory_series"], "run31": round(otc["desk_bal"])}
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
                        "note": f"Value-bearing EGLD transactions only (ESDT spam airdrops and exchange-internal sweeps excluded). {WIN_TXT}; rail window starts 15:05:30 UTC Oct 12 to avoid double counting run #30's tail. UPbit, MEXC, KuCoin, Bitfinex and Tokero moved no EGLD. Crypto.com's two wallets exchanged 2,042 EGLD internally (hot -> staking sweep), which shows up as a withdrawal from one and a deposit to the other; the entity net is unaffected. Coinbase's routing wallet and the Binance de-staking wallet were idle. Web check: no exchange notice found beyond the Upbit caution review (Oct 19-23); Binance's native-network state is still inferred from chain data."},
        "signal": (f"NET INFLOW ON A FALLING PRICE. {len(OPEN)} tracked venues move EGLD both ways ({', '.join(OPEN)}). Net exchange balance change {ex['net']:+,.0f} EGLD over {LIVE_DAYS:.1f} days: " + ", ".join(f"{e2['entity']} {e2['net_flow_egld']:+,.0f}" for e2 in ex["entity"] if e2["net_flow_egld"]) + ". "
                   f"Netting: about 15,000 of Binance's balance gain is the 15:00 Oct 12 arbitrage deposit already reported in run #30; {f(ARB_GATE_IN)} of Gate.io's inflow is erd1d2anjjha... emptying its balance into Gate.io (it withdrew 27,107 from Binance.com and Bybit in run #30), so ex-arbitrage Gate.io is {GATE_NET-ARB_GATE_IN:+,.0f}. "
                   f"Ex-arbitrage total about {EX_NET_EX_ARB-15179:+,.0f}: still a net deposit, led by Coinbase and Crypto.com. Exchange-flow and OTC series are still not appended to the weekly baselines (UPbit closed, short window)."),
        "by_exchange": [{"exchange": w["exchange"], "change_egld": w["change_egld"], "pct": w["pct"]} for w in ex["per_wallet"]],
        "entity_netting": [{"entity": e2["entity"], "wallets_count": e2["wallets_count"],
                            "net_flow_egld": e2["net_flow_egld"], "interpretation": entity_interp(e2)} for e2 in ex["entity"]]},
    "dormant_activations": [],
    "exit_routes": {
        "route_this_run": "no CEX exits; one withdraw > 3,000 EGLD, moved to a linked personal wallet",
        "route_previous_run": "no CEX exits; re-delegate / held",
        "scan_threshold_egld": 3000, "scan_calls": EXS["calls"], "scan_by_route": EXR,
        "scan_rows": [{"sender": r_["sender"], "sender_label": r_["sender_label"], "provider": r_["provider"], "withdrawn_egld": r_["withdrawn_egld"],
                       "route": r_["route"], "balance_now_egld": r_["balance_now"]} for r_ in EXS["rows"]],
        "traced_egld_ex_internal": EXIT_TRACED, "traced_to_cex_egld": EXIT_CEX,
        "binance_undelegation": {"wallet": "erd1r3w62vqmsux5e38p6vnueatmfcs8nr5lmg3s97x6rafqpgxfae0sxv9z0v", "egld": BIN_UNDEL,
                                 "called_utc": "2026-10-12 06:16 UTC", "unbonds_in_days": BIN_UNDEL_DAYS, "matures_utc": BIN_MATURES,
                                 "status": "pending (userUndelegatedList), wallet idle in the window"},
        "binance_hot_to_custody_egld": 0.0,
        "largest_new_undelegation": {"wallet": NINJA["wallet"], "provider": "ninjastaking", "egld": NINJA["amount_egld"],
                                     "unbonds_in_days": NINJA["days_remaining"], "wallet_balance_egld": NINJA["wallet_balance_egld"]},
        "note": (f"Collector-side scan of every withdraw call above 3,000 EGLD in the window ({EXS['calls']} call): a pi-staking delegator withdrew {f(EXS['rows'][0]['withdrawn_egld'])} EGLD and sent 3,400 to erd1hmzqtpzl..., a personal wallet (nonce 2,552, xExchange and staking history) that holds 1,700 and passed 1,700 to another wallet. No exchange hop. "
                 f"{O['withdraw_calls']} withdraw calls returned {f(WD.get('egld_returned_total', 0))} EGLD in total. Two large items are pending: Binance's {f(BIN_UNDEL)} (matures ~{BIN_MATURES[:16]}) and erd1me5hmqt5qg...'s {f(NINJA['amount_egld'])} from ninjastaking ({NINJA['days_remaining']:.0f} days).")},
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
        "method_note": f"Fifth read after restart; invalid balances {HR['invalid_total_egld']:.2f} EGLD, unchanged."},
    "otc_pipeline": {
        "gross_outbound_egld_7d": otc["gross_out"], "gross_inbound_egld_7d": otc["gross_in"],
        "circular_egld_7d": otc["circular"], "net_one_way_egld_7d": otc["net_one_way"],
        "circular_share_pct": otc["circ_pct"],
        "desk_balance_egld": otc["desk_bal"], "previous_desk_balance_egld": otc["prev_desk"],
        "upbit_reload_egld": otc["upbit_feed"],
        "venue_netting": [],
        "router_tail_delivery_egld": 0.0, "router_tail_routers": 0,
        "gross_series_egld_7d": {**r26o["gross_series_egld_7d"], "run31": otc["gross_out"]},
        "net_one_way_series_egld_7d": {**r26o["net_one_way_series_egld_7d"], "run31": otc["net_one_way"]},
        "desk_inventory_series_egld": INV_SERIES,
        "circularity_series_pct": {**r26o["circularity_series_pct"], "run31": 0.0},
        "peak_window_renetted": r26o["peak_window_renetted"],
        "backfilled_windows": r26o.get("backfilled_windows", []),
        "wave_window_netting": {**r26o["wave_window_netting"],
            "note": f"Wave #4 stays closed at 467,107 EGLD one-way (Sep 7 to the halt, frozen labels). The post-restart window (Sep 24 - Oct 15) nets {f(otc['wave']['net_one_way'])} EGLD one-way."},
        "feed_by_parent_venue": [],
        "feeder_backtrace": O["feeder_backtrace"],
        "address_poisoning": [{"address": a, "mimics": v["note"], "nonce": v["nonce"], "dust_txs_30d": v["dust_txs_30d"],
                               "distinct_targets_30d": v["distinct_targets_30d"],
                               "inbound_above_0_01_egld": len(v["inbound_above_0_01_egld"])} for a, v in PZ.items()],
        "desk_terminal_resolved": {"address": TERM["address"], "nonce": TERM["info"].get("nonce"), "balance_egld": TERM_BAL, "role": "holder (nonce 1, no value sent)"},
        "series_note": (f"SILENT, {LIVE_DAYS:.1f}-DAY WINDOW. Gross out {f(otc['gross_out'])} EGLD: neither desk sent or received anything of value. No UPbit reload (UPbit's hot wallet had no EGLD flow at all). "
                        f"The Oct 6 terminal erd1y27r22... still holds {f(TERM_BAL, 1)} EGLD. Desks {f(otc['desk_bal'])} (unchanged). otc-pipeline-resumption closes not evaluable: UPbit never reopened withdrawals through run #31.")},
    "demand_instruments": {
        "identifiable_bid_absorbed_egld_7d": 0.0, "mega_whale_otc_leg_egld": MEGA_IN,
        "mega_whale_balance_egld": bid["mega_bal"] or 0.0, "mega_whale_change_egld": bid["mega_delta"],
        "coinbase_routing_balance_egld": bid["cbr_bal"] or 0.0, "coinbase_routing_inflow_egld": 0.0,
        "coinbase_routing_funder": "erd1m9qn6gvercs6ksvtn924w4y7z9ppglyfugpu34al26t9u4mvzvqqlq9dc3", "coinbase_routing_funder_label": "Coinbase (secondary); idle this window (run #30: fed by Unknown Whale B's 122,054 deposit)",
        "weeks_at_zero": 11, "weeks_at_zero_in_last_four": 4, "bid_to_distribution_ratio_pct": 0.0,
        "dex_turnover_ratio_pct": bid["turnover"], "previous_dex_turnover_ratio_pct": bid["prev_turnover"],
        "dex_volume_egld_24h": bid["dexvol_egld"], "previous_dex_volume_egld_24h": bid["prev_dexvol_egld"],
        "pool_tvl_egld": bid["pooltvl_egld"], "previous_pool_tvl_egld": bid["prev_pooltvl_egld"],
        "wegld_usdc_volume_usd": bid["wegld_usdc_vol"], "wegld_usdc_share_of_volume_pct": bid["wegld_usdc_share"],
        "ex_wegld_usdc_volume_usd": bid["ex_wegld_usdc_vol"], "ex_wegld_usdc_volume_egld": bid["ex_wegld_usdc_vol_egld"],
        "dex_volume_status": "evaluable; compared with run #30",
        "absorber_scan": {"terminals_scanned": absb["scanned"],
                          "terminals_retaining_over_half": len(absb["retaining"]),
                          "total_received_from_desks_egld": absb["total_received"],
                          "total_retained_egld": absb["total_balance_held"],
                          "retained_share_pct": 0.0,
                          "verdict": "No desk outbound this window; the instrument stays retired. The Mega Whale did not move."},
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
    f"RAILS. Value-bearing EGLD per tracked exchange wallet, {WIN_TXT} (rail window from 15:05:30 Oct 12): "
    + "; ".join(f"{k}: {v['state'].replace('_', ' ')} ({v['in_txs']} in / {v['out_txs']} out)" for k, v in VEN.items() if v["state"] != "closed")
    + f". No EGLD moved: {', '.join(k for k, v in VEN.items() if v['state'] == 'closed')}. No venue opened or closed this window.\n\n"
    f"BINANCE.COM. Per day since the Oct 9 reopening (deposits / withdrawals, EGLD, raw; Oct 12 includes the 161,137 internal custody send): " + "; ".join(f"{d_[5:]}: {f(v_['dep_egld'])} / {f(v_['wd_egld'])}" for d_, v_ in BD.items())
    + f". On the de-duplicated window rails, {f(BIN_DEP)} in and {f(BIN_WD_EXT)} out: {BIN_EXT_NET:+,.0f} ({BIN_EXT_PER_DAY:+,.0f}/day), from +19,776/day in run #30. Oct 13 and Oct 15 were net withdrawals. The balance-based entity figure ({BIN_ENTITY_NET:+,.0f}) is larger because it includes the 15,179 arbitrage deposit at 15:00 Oct 12, inside run #30's rail pass. "
    f"A drip seller is visible: erd1vadknqe8... sends 200-250 EGLD clips to erd137cw9q46... (run #29's 57,620 EGLD Binance depositor), which forwards them to Binance.com within minutes ({f(TR['binance_funders']['erd137cw9q']['to_binance_egld'])} EGLD in the window from that wallet). Custody and the de-staking wallet did not move.\n\n"
    f"CROSS-VENUE WALLETS, NETTED. erd1d2anjjha... sent its whole balance, {f(ARB_GATE_IN)} EGLD, to Gate.io (after withdrawing 27,107 from Binance.com and Bybit in run #30); erd13sytuz92... moved {f(ARB['erd13sytuz92']['in_egld'])} from Binance.com and Coinbase to Bybit; erd1reh7sy2c... (nonce 1) made one Gate.io -> Binance.com round of 15,179 at 15:00 Oct 12 and is now empty. "
    f"Over two windows erd1d2anjjha... moved about 29,500 EGLD from Binance/Bybit to Gate.io and kept none, which is consistent with arbitrage or treasury rebalancing for one Gate.io client, not a holder. All three are labelled in known-addresses as cross-venue wallets; Gate.io's {GATE_NET:+,.0f} becomes {GATE_NET-ARB_GATE_IN:+,.0f} without them.\n\n"
    f"COINBASE. The Whale B -> Coinbase -> Mega Whale channel was idle: Whale B {f(CBL['whale_b']['balance_egld'])}, Mega Whale {f(CBL['mega']['balance_egld'])}, routing wallet {f(CBL['cb_routing']['balance_egld'],1)}, no transactions from any of them. Coinbase's entity gain ({next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Coinbase'),0):+,.0f}) is customer deposits into the secondary wallet ({f(VEN.get('Coinbase (secondary)',{}).get('in_egld',0))} in from {VEN.get('Coinbase (secondary)',{}).get('in_senders',0)} senders).\n\n"
    f"WHALES. Tiers on the common-address basis ({O['tiers_basis']} wallets): mega {O['tiers']['mega']['net_change_egld']:+,.0f} (no mega whale moved), large {O['tiers']['large']['net_change_egld']:+,.0f} (Binance.com, Crypto.com, Bybit hot wallets plus the two growth funds' scheduled +4,246 each), mid {O['tiers']['mid']['net_change_egld']:+,.0f} (Coinbase secondary +12.5K; erd1r4aap2km... withdrew 8,265 from Gate.io). Exchange hot wallets explain most of the large-tier gain, so it is not whale accumulation.\n\n"
    f"UNKNOWN WHALE I: {CEN['Unknown Whale I']['inbound_txs']} inbound for another window. erd1a6lte0: {CEN['erd1a6lte0']['inbound_txs']} inbound from {CEN['erd1a6lte0']['distinct_senders']} senders, the same deposit-wallet pattern as run #30.\n\n"
    f"DEMAND. Binance+Bybit bids within 2% of mid total ${f(bbn)} (closed-book base ${f(bbn_prev)}). Upbit's premium {PREM:.1f}% (from {PREM_PREV:.1f}%) on {UP_SHARE:.0f}% of global volume (from {UPSH_PREV:.0f}%): Korean demand cooled before the Oct 19-23 decision.")
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
                   "fee_pct": mv(ident, "fee") or 0.0, "weeks_in_state": 8,
                   "note": f"EIGHTH WEEK AFTER THE FEE REVERSAL ({LIVE_DAYS:.1f}-day window): book {mv(ident,'delta'):+,.0f}, users {mv(ident,'users_delta'):+d}. Outflows stopped; the book is flat to slightly up."})
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
                          "note": "Zero transitions for an eighth week. Join on contract address, 100% match (188 of 188), no identity changes."},
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
            f"COMPOUND RATE {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} reDelegateRewards vs {cvc['claim_count']} claimRewards), from 59.38%. Series: 57.51 / 62.05 / 49.44 / 62.68 / 52.40 / 58.28 / 60.85 / 59.38 / {cvc['compound_pct_of_reward_decisions']:.2f}. Inside the 57-63% range for a fifth run, on a -7% price window.",
            f"Retail {fates['retail']['total_events']} claims, {fates['retail']['by_count'].get('sold',0)} to a labelled exchange; mid-tier {fates['mid_tier']['total_events']}, {fates['mid_tier']['by_count'].get('sold',0)} sold; institutional {fates.get('institutional',{}).get('total_events',0)}, {fates.get('institutional',{}).get('by_count',{}).get('sold',0)} sold (four claims, too few to read).",
            f"Sample: {ag['providers_sampled']} of {ag.get('providers_requested',8)} providers, 7-day delegator window (overlaps run #30's).",
            "PROVIDER OPERATORS DID NOT SELL FEES for a nineteenth consecutive run (destinations: DeFi deposits, held, rotated)."]},
    "analysis": (
        f"THE EXIT PACE PICKED UP AS PRICE FELL. {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD in {LIVE_DAYS:.1f} days across {sk['providers_scanned']} provider contracts. {f(NINJA['amount_egld'])} ({100*NINJA['amount_egld']/sk['undelegated_week']:.0f}%) is one call: erd1me5hmqt5qg... leaving ninjastaking (it also has 5,071 unbonding from another provider, due in ~2 days). "
        f"The other {sk['undelegate_callers']-1} wallets unDelegated {f(RETAIL_UNDEL)}, about {f(RETAIL_UNDEL/LIVE_DAYS*7)} a week at this pace, against ~54,000 in run #30 and 73-84K in pre-halt weeks. Short-window readings are recorded, not appended to the weekly series.\n\n"
        f"WITHDRAWALS STAYED SMALL. {O['withdraw_calls']} withdraw calls returned {f(WD.get('egld_returned_total',0))} EGLD, led by pi-staking ({f(wd_top0)}). The single call above 3,000 EGLD went to a personal wallet, not an exchange. Measured pending among the window's callers: {f(sk['pool_total'])} EGLD; add Binance's {f(BIN_UNDEL)} from Oct 12, maturing ~{BIN_MATURES[:10]}.\n\n"
        f"THE RATIO AND THE RESIDUAL. Delegation TVL fell {f(abs(sk['delta_locked']))} to {f(tl)} while /economics staked rose {M['staked_chg']:+,.0f}: undelegated EGLD stays in 'staked' until it unbonds. Ratio {100*M['sr']:.2f}%. HHI {sk['hhi']:.5f} (from {sk['prev_hhi']:.5f}). 74 of 100 APR-bearing providers sit in the 8-9% bucket; pokerstaking (9.86%, 0% fee) is the best headline deal again.\n\n"
        f"COMPOUNDING {cvc['compound_pct_of_reward_decisions']:.2f}%. DELEGATORS {sk['users_delta']:+,} to {f(sk['users'])}; {sk['gaining']} providers gained and {sk['losing']} lost. Synexis led inflows ({mv('Synexis','delta'):+,.0f}, {mv('Synexis','users_delta'):+d} delegators), ninjastaking led outflows. binance_staking {BINP['delta']:+,.0f} to {f(BINP['locked'])}. Zero deregistration transitions for an eighth week.")}
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
        "volume_status": "evaluable; compared with run #30 (24h snapshots)",
        "mex_pair_depth": {"pair": "MEX/WEGLD", "tvl_usd": xx["mex_pair_depth"]["tvl_usd"], "tvl_egld": xx["mex_pair_depth"]["tvl_egld"],
                           "previous_tvl_egld": xx["mex_pair_depth"]["previous_tvl_egld"], "tvl_egld_wow_pct": xx["mex_pair_depth"]["tvl_egld_wow_pct"],
                           "volume_24h_usd": xx["mex_pair_depth"]["volume_24h_usd"], "trades_24h": xx["mex_pair_depth"]["trades_24h"],
                           "share_of_pool_tvl_pct": xx["mex_pair_depth"]["share_of_pool_tvl_pct"], "depth_rank": xx["mex_pair_depth"]["depth_rank"]},
        "mex_pair_event": r26["token_activity"]["xexchange"]["mex_pair_event"]},
    "analysis": (
        f"DEX VOLUME EASED. 24h volume ${f(xx['vol'])} ({f(bid['dexvol_egld'])} EGLD) against ${f(xx['prev_vol'])} ({f(bid['prev_dexvol_egld'])} EGLD) at the last snapshot, {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.0f}% in EGLD. "
        f"WEGLD/USDC is {bid['wegld_usdc_share']:.0f}% of it: the venue is effectively one EGLD/dollar pool arbitraged against the exchanges; everything else traded ${f(bid['ex_wegld_usdc_vol'])}. Turnover {bid['turnover']:.2f}% of pool TVL (from {bid['prev_turnover']:.2f}%). Pool TVL {f(bid['pooltvl_egld'])} EGLD ({100*(bid['pooltvl_egld']-bid['prev_pooltvl_egld'])/bid['prev_pooltvl_egld']:+.1f}% in EGLD), ${f(bid['pooltvl'])} ({100*(bid['pooltvl']-bid['prev_pooltvl'])/bid['prev_pooltvl']:+.1f}%) in dollars, mostly the price.\n\n"
        f"MEX ${xx['mex_price']:.2e} ({xx['mex_wow']:+.1f}% over the window, against EGLD {pc:+.1f}%); MEX/WEGLD depth ${f(xx['mex_pair_depth']['tvl_usd'])} ({xx['mex_pair_depth']['tvl_egld_wow_pct']:+.1f}% in EGLD), rank {xx['mex_pair_depth']['depth_rank']}.\n\n"
        f"STABLECOINS. USDC {usdc['pct']:+.2f}% to {f(usdc['supply'])} ({f(USDC_BURN)} redeemed), above the 50,000 line; USDT {usdt['pct']:+.2f}% to {f(usdt['supply'])}, back to falling after one up reading. USDC has fallen in seven of eight stored readings. "
        f"NEWLY ISSUED: {len(newly)} issuances in the window ({', '.join(t['identifier'] for t in newly)}), each with 1-3 holders, below the traction bar.")}
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
         "notable_events": f"{f(es('VOXEGLD-5872e5'))} EGLD, supply {(em['VOXEGLD-5872e5']['pct'] or 0):+.1f}%, holders {em['VOXEGLD-5872e5']['holders']}: seventh week of growth.", "health_signal": hs(ep("VOXEGLD-5872e5"))},
        {"protocol": "VestaX Finance", "category": "liquid_staking", "addresses_tracked": 1, "tvl_usd": (es("VEGLD-2b9319") or 0) * price, "tvl_egld": es("VEGLD-2b9319") or 0.0,
         "tvl_wow_change_pct": ep("VEGLD-2b9319"), "transfers_24h": None,
         "notable_events": f"{f(es('VEGLD-2b9319'))} EGLD.", "health_signal": hs(ep("VEGLD-2b9319"))}],
    "sc_deployments": [],
    "analysis": (
        f"HATOM'S EGLD MARKET OUTFLOW SLOWED. The EGLD money market holds {f(df['egld_mm_balance'])} EGLD, from {f(df['egld_mm_prev_balance'])} ({EMM_D:+,.0f}, after -12,786 in run #30 and -30,848 in run #29); HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.2f}%. "
        f"Calls in the window: {HMM['redeem_calls']} redeems from {HMM['by_function'].get('redeem',{}).get('distinct_senders',0)} wallets, {HMM['by_function'].get('mintAndEnterMarket',{}).get('n',0)} supply-and-collateral calls from {HMM['by_function'].get('mintAndEnterMarket',{}).get('distinct_senders',0)}, {HMM['by_function'].get('borrow',{}).get('n',0)} borrows, {HMM['by_function'].get('repayBorrow',{}).get('n',0)} repayments, {HMM['liquidation_calls']} liquidations. New supply roughly matched redemptions, and a -7% price window produced no liquidation call on the EGLD market.\n\n"
        f"INVERSE-RATIO RULE EVALUABLE. Aggregate lending TVL ex-HMEX reads {hl:+.2f}% in EGLD on a {pc:+.2f}% price move (ratio {df['inverse_ratio_ex_hmex']:.2f}): dollar collateral (HUSDC {HT['HUSDC-d80042']['supply_pct']:+.2f}%, HUSDT {HT['HUSDT-6f0914']['supply_pct']:+.2f}%) is worth more EGLD at a lower price, so the EGLD-denominated rise is mechanical, not new deposits.\n\n"
        f"LIQUID STAKING. SEGLD {lsd['SEGLD-3ad2d0']['pct']:+.2f}%, XEGLD {lsd['XEGLD-e413ed']['pct']:+.2f}%, SWTAO {lsd['SWTAO-356a25']['pct']:+.2f}%, USH {lsd['USH-111e09']['pct']:+.2f}%: flat through the drawdown. VoxEGLD {(em['VOXEGLD-5872e5']['pct'] or 0):+.1f}% to {f(em['VOXEGLD-5872e5']['supply'])} (seventh week of growth, still small). XOXNO's EGLD liquid-staking contract balance fell 2,925 to 8,858 EGLD (buffer, not TVL).\n\n"
        f"ACTIVITY. XOXNO aggregator {f(cnt('XOXNO Aggregator'))} transfers in 24h, OneDex {f(cnt('OneDex Swap'))}, Hatom LSD {f(cnt('Hatom Liquid Staking'))}.")}

# ---------------------------------------------------------------------------
R["anomalies"] = [
    {"metric": "egld_price_usd", "current_value": price, "previous_value": M["prev_price"], "method": "z_score", "severity": z["price"].get("severity", "medium"),
     "average_value": z["price"].get("mean"), "stddev": z["price"].get("stddev"), "z_score": zz("price"), "change_pct": pc,
     "description": f"{pc:+.2f}% in {LIVE_DAYS:.1f} days (BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%); z={zz('price'):+.2f}. Fourth window in a row that EGLD trailed BTC; -23% from Oct 5."},
    {"metric": "exchange_net_flow_egld", "current_value": ex["net"], "previous_value": None, "method": "rule_based", "severity": "medium",
     "change_pct": None,
     "description": f"Tracked exchange balances {ex['net']:+,.0f} EGLD on a falling price (about {EX_NET_EX_ARB-15179:+,.0f} after removing one cross-venue wallet and run #30's tail deposit). Not z-scored: partial rails and a short window keep it out of the weekly baseline."},
    {"metric": "usdc_supply", "current_value": usdc["supply"], "previous_value": usdc["prev"], "method": "rule_based", "severity": "medium",
     "change_pct": usdc["pct"],
     "description": f"{f(USDC_BURN)} USDC redeemed in {LIVE_DAYS:.1f} days, above the 50,000 bridge-route line; seventh decline in eight readings."},
    {"metric": "ninjastaking_locked_egld", "current_value": NINJAP["locked"], "previous_value": NINJAP["prev_locked"], "method": "rule_based", "severity": "low",
     "change_pct": 100 * NINJAP["delta"] / NINJAP["prev_locked"],
     "description": f"ninjastaking {NINJAP['delta']:+,.0f} ({100*NINJAP['delta']/NINJAP['prev_locked']:+.1f}%): one {f(NINJA['amount_egld'])} EGLD unDelegate by erd1me5hmqt5qg..., unbonds in {NINJA['days_remaining']:.0f} days."},
    {"metric": "korea_premium_pct", "current_value": PREM, "previous_value": PREM_PREV, "method": "rule_based", "severity": "low",
     "change_pct": 100 * (PREM - PREM_PREV) / PREM_PREV,
     "description": f"Upbit premium narrowed to {PREM:.1f}% from {PREM_PREV:.1f}%; Upbit {UP_SHARE:.0f}% of global volume (from {UPSH_PREV:.0f}%). UPbit rails closed; review Oct 19-23."},
    {"metric": "binance_bid_depth_2pct_usd", "current_value": BOOK["binance"]["depth_minus2_usd"], "previous_value": 45076.0, "method": "rule_based", "severity": "low",
     "change_pct": 100 * (BOOK["binance"]["depth_minus2_usd"] - 45076.0) / 45076.0,
     "description": f"Binance bids within 2% of mid ${f(BOOK['binance']['depth_minus2_usd'])} from $45,076; spot volume up, so the book thinned while selling rose."},
    {"metric": "dex_volume_24h_egld", "current_value": bid["dexvol_egld"], "previous_value": bid["prev_dexvol_egld"], "method": "z_score", "severity": z["dexvol"].get("severity", "low"),
     "average_value": z["dexvol"].get("mean"), "stddev": z["dexvol"].get("stddev"), "z_score": zz("dexvol"),
     "change_pct": 100 * (bid["dexvol_egld"] - bid["prev_dexvol_egld"]) / bid["prev_dexvol_egld"],
     "description": f"xExchange 24h volume {f(bid['dexvol_egld'])} EGLD ({100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.0f}%), {bid['wegld_usdc_share']:.0f}% WEGLD/USDC; z in dollars {zz('dexvol'):+.2f}. Normal."},
]

R["trend_indicators"] = {
    "accelerating_exchange_outflows": [],
    "validator_movements": {"providers_joining": 0, "providers_leaving": 0, "net_provider_change": 0, "notable_joiners": [],
                            "notable_leavers": [], "note": f"No joins or deregistrations for an eighth week. ninjastaking lost {f(abs(NINJAP['delta']))} to one delegator but stays registered."},
    "token_supply_events": [
        {"identifier": "USDC-c76f1f", "name": "WrappedUSDC", "event": "burn", "supply_previous": str(int(usdc["prev"])), "supply_current": str(int(usdc["supply"])),
         "change_pct": usdc["pct"], "description": f"{f(USDC_BURN)} USDC redeemed in {LIVE_DAYS:.1f} days, above the 50,000 bridge-route line."},
        {"identifier": "USDT-f8c08c", "name": "USDT", "event": "burn", "supply_previous": str(int(usdt["prev"])), "supply_current": str(int(usdt["supply"])),
         "change_pct": usdt["pct"], "description": f"{f(usdt['prev']-usdt['supply'])} USDT redeemed; run #30's increase did not continue."},
        {"identifier": "VOXEGLD-5872e5", "name": "VoxEGLD", "event": "mint", "supply_previous": str(int(em["VOXEGLD-5872e5"]["prev"])), "supply_current": str(int(em["VOXEGLD-5872e5"]["supply"])),
         "change_pct": em["VOXEGLD-5872e5"]["pct"], "description": "Dinovox liquid staking, seventh week of growth; small base."}],
    "consecutive_streaks": [
        {"metric": "egld_vs_btc", "direction": "down", "weeks": 4, "cumulative_change_pct": None,
         "interpretation": f"EGLD has trailed BTC in four consecutive windows (runs #28-#31; this one {EGLD_VS_BTC:+.1f}pp)."},
        {"metric": "egld_price_usd", "direction": "down", "weeks": 4, "cumulative_change_pct": 100 * (price - 4.60) / 4.60,
         "interpretation": f"$4.60 (Oct 5) -> $3.95 -> $3.81 -> ${price:.2f}: four falling readings, {100*(price-4.60)/4.60:+.1f}% in ten days, since exchange rails reopened."},
        {"metric": "usdc_supply", "direction": "down", "weeks": 3, "cumulative_change_pct": 100 * (usdc["supply"] - 7343990) / 7343990,
         "interpretation": "Three straight declines (7.34M -> 7.32M -> 7.28M -> 7.20M); seven of eight readings down."},
        {"metric": "total_delegators", "direction": "flat", "weeks": 19, "cumulative_change_pct": -1.2, "interpretation": f"{sk['users_delta']:+,} to {f(sk['users'])}. The base rate."},
        {"metric": "provider_operator_fee_selling", "direction": "flat", "weeks": 19, "cumulative_change_pct": 0.0, "interpretation": "Nineteen runs with zero exchange destinations from sampled operator wallets."}],
    "regime_shifts": [
        {"metric": "exchange_rail_state", "before_value": 0.0, "after_value": round(len(OPEN) / max(1, len([k for k in VEN if k not in _NONVENUE])), 2),
         "description": f"Unchanged: {len(OPEN)} of {len([k for k in VEN if k not in _NONVENUE])} tracked venues move EGLD both ways ({', '.join(OPEN)}). UPbit had no EGLD flow. Promote when UPbit opens both ways."},
        {"metric": "binance_staking_allocation", "before_value": 399100.0, "after_value": BINP["locked"],
         "description": f"CANDIDATE, unchanged: {f(BIN_UNDEL)} EGLD in Binance's unbonding queue, maturing ~{BIN_MATURES[:10]}. Resolve on where the withdraw goes."},
        {"metric": "rails_reopened_price_path", "before_value": 4.60, "after_value": price,
         "description": f"CANDIDATE: since the main venues reopened (Binance.com Oct 9, Coinbase Oct 10, Bybit Oct 12) EGLD fell {100*(price-4.60)/4.60:.0f}% and tracked exchanges took net deposits in every window (+19,442, +93,778, +9,029, and this one). The pent-up supply reading from the halt weeks fits; promote if the next full week also shows net inflow with EGLD trailing BTC."}]}

R["watch_list"] = [
    {"item": f"BINANCE UNBOND - {f(BIN_UNDEL)} EGLD matures ~{BIN_MATURES[:10]}", "weeks_on_list": 2,
     "reason": f"Still pending on erd1r3w62vq... ({BIN_UNDEL_DAYS:.1f} days left at collection). Custody, re-delegation or hot wallet? PRE-COMMITTED (binance-undelegation-destination), evaluable run #32/#33."},
    {"item": "UPBIT CAUTION REVIEW Oct 19-23", "weeks_on_list": 5,
     "reason": f"Premium {PREM:.1f}% (from {PREM_PREV:.1f}%), {UP_SHARE:.0f}% of global volume; UPbit had no EGLD flow; {UPD['distinct_depositors']} distinct depositors since restart. A delisting would remove the venue that carried the OTC pipeline."},
    {"item": "EXCHANGE NET INFLOW ON A FALLING PRICE", "weeks_on_list": 1,
     "reason": f"{ex['net']:+,.0f} EGLD to tracked venues in {LIVE_DAYS:.1f} days while EGLD fell {abs(pc):.1f}%. Next full week decides whether this is a regime (pre-committed: reopening-supply-overhang)."},
    {"item": "NINJASTAKING EXIT - 26,699 EGLD", "weeks_on_list": 1,
     "reason": f"erd1me5hmqt5qg... unbonds in {NINJA['days_remaining']:.0f} days (plus 5,071 elsewhere in ~2). Trace the withdraw: exchange or re-stake."},
    {"item": "USDC REDEMPTIONS", "weeks_on_list": 1,
     "reason": f"{f(USDC_BURN)} redeemed this window, above the 50,000 bridge line; three straight declines."},
    {"item": "COINBASE / WHALE B / MEGA WHALE", "weeks_on_list": 2,
     "reason": f"Idle this window (Whale B {f(CBL['whale_b']['balance_egld'])}, Mega Whale {f(CBL['mega']['balance_egld'])}). PRE-COMMITTED (mega-whale-coinbase-leg) by run #32."},
    {"item": "CROSS-VENUE WALLETS", "weeks_on_list": 2,
     "reason": "erd1d2anjjha... (emptied into Gate.io), erd13sytuz92... (to Bybit), erd1reh7sy2c... (empty). Labelled; net them out of venue flows."},
    {"item": "DRIP SELLER INTO BINANCE", "weeks_on_list": 1,
     "reason": "erd1vadknqe8... -> erd137cw9q46... -> Binance.com in 200-250 EGLD clips; holds about 67,800 EGLD."},
    {"item": "OTC PIPELINE", "weeks_on_list": 31,
     "reason": f"Silent: gross {f(otc['gross_out'])}, desks {f(otc['desk_bal'])}. otc-pipeline-resumption closed not evaluable; keep on the list until Upbit's decision."},
    {"item": "EXPLOIT WALLET AND POISONING RING", "weeks_on_list": 6,
     "reason": f"Incident addresses hold {HR['invalid_total_egld']:.2f} EGLD; poisoning operator {PR['operator_out_7d']} dust txs in the window, zero hits above dust."},
]

# ---------------------------------------------------------------------------
prior = {t["id"]: t for t in r26["pre_committed_tests"]}
tests = [t for t in r26["pre_committed_tests"] if t["status"] == "resolved"]


def resolve(tid, outcome, measured, resolution):
    t = dict(prior[tid]); t.update({"status": "resolved", "outcome": outcome, "resolved_in_run": 31, "measured_value": measured, "resolution": resolution}); return t


tests.append(resolve("otc-pipeline-resumption", "inconclusive",
    f"runs #28-#31: desk gross 0 / 5,745 / 1,604 / {f(otc['gross_out'])} EGLD (all < 20,000); UPbit withdrawals never reopened (its hot wallet had no EGLD flow this window, 1 send since restart, to its own OTC desk)",
    "Not evaluable by the test's own branch: UPbit was still closed at run #31. Every window stayed under the 20,000 partial line, but the programme's feed (UPbit -> desk) cannot run while UPbit's rail is shut, so 'programme ended' cannot be separated from 'programme blocked'. Re-register only if UPbit reopens."))
for tid, note in [("delivery-price-relevance-2", f"run #31: desk gross {f(otc['gross_out'])} EGLD; no delivery. Not evaluable."),
                  ("korea-premium-arbitrage", f"run #31: premium {PREM:.1f}%; UPbit {UPD['distinct_depositors']} distinct depositors since restart, 0 in the window. Not evaluable."),
                  ("binance-undelegation-destination", f"run #31: still pending, {f(BIN_UNDEL)} EGLD in the unbonding list with {BIN_UNDEL_DAYS:.1f} days left (matures ~{BIN_MATURES[:16]}); wallet idle; custody unchanged {f(cust['balance'])}."),
                  ("mega-whale-coinbase-leg", f"run #31: no leg. Whale B {f(CBL['whale_b']['balance_egld'])} and Mega Whale {f(CBL['mega']['balance_egld'])} unchanged; routing wallet idle.")]:
    t = dict(prior[tid]); t.update({"status": "open", "measured_value": note, "resolution": None}); tests.append(t)


def new(tid, claim, threshold, branches, measured):
    return {"id": tid, "registered_in_run": 31, "claim": claim, "threshold": threshold, "branches": branches,
            "status": "open", "outcome": None, "resolved_in_run": None, "measured_value": measured, "resolution": None}


tests += [
    new("reopening-supply-overhang", "The post-reopening decline is pent-up supply from the halt weeks reaching exchanges, not a market-wide move.",
        "Over the next full 7-day window (run #32): tracked exchanges net inflow > +25,000 EGLD (ex cross-venue wallets) AND EGLD - BTC < -3pp = overhang persists; net outflow AND EGLD - BTC > 0 = overhang cleared; otherwise no conclusion",
        [{"condition": "net inflow > 25K and EGLD-BTC < -3pp", "reading": "overhang persists"},
         {"condition": "net outflow and EGLD-BTC > 0", "reading": "overhang cleared"},
         {"condition": "otherwise", "reading": "no conclusion"}],
        f"run #31: exchanges {ex['net']:+,.0f} EGLD ({EX_NET_EX_ARB-15179:+,.0f} ex-arbitrage) over {LIVE_DAYS:.1f} days; EGLD - BTC {EGLD_VS_BTC:+.1f}pp."),
    new("ninjastaking-exit-destination", "The 26,699 EGLD ninjastaking unDelegate (erd1me5hmqt5qg...) is a sale, not a provider rotation.",
        "Within 3 days of the withdraw (unbonds ~Oct 23): > 50% reaching a labelled exchange (one hop allowed) = sale; > 50% re-delegated = rotation; otherwise no conclusion",
        [{"condition": "> 50% to exchange", "reading": "sale"},
         {"condition": "> 50% re-delegated", "reading": "rotation"},
         {"condition": "otherwise", "reading": "no conclusion"}],
        f"run #31: unDelegated {f(NINJA['amount_egld'])}, {NINJA['days_remaining']:.1f} days to unbond; wallet holds {f(NINJA['wallet_balance_egld'])}."),
]
resolved = [t for t in tests if t.get("resolved_in_run") == 31]
as_pred = sum(1 for t in resolved if t["outcome"] == "as_predicted")
R["pre_committed_tests"] = tests

# ---------------------------------------------------------------------------
R["meta_learning"] = {
    "run_number": 31,
    "endpoints_that_worked": status["ok"],
    "endpoints_that_failed": [f"NONE with data missing. {D.get('_n_429', 0)} HTTP 429s; 0 paged errors; 0 API errors."],
    "api_quirks": [
        "RAIL WINDOWS OVERLAP WHEN THE RAIL PASS RUNS AFTER THE COLLECTOR: run #30's rails counted every transaction with ts >= window start and no upper bound, so flows between the collector's end (14:48) and the rail pass (~15:05) were read in run #30 and would have been read again here (a 15,179 EGLD deposit). The rail pass now records rail_window_start_ts and the next run starts after the previous rail pass, not after the previous collector.",
        "/accounts/{addr}/delegation returns userUndelegatedList with 'seconds' remaining per pending unbond; that is the cleanest way to confirm an unbond is still pending and when it matures, with no transaction scan."],
    "data_gaps": [
        "The 7-day delegator reward window overlaps run #30's.",
        "Kraken has no tracked address.",
        "The USDC burn was not traced to a bridge transaction; the reading is supply-only.",
        "Hatom UTK Money Market and OneDex Launchpad still fail bech32 validation."],
    "key_findings": [
        f"EGLD {pc:+.2f}% to ${price:.2f} vs BTC {M['btc_wow']:+.2f}%: fourth window trailing BTC, -23% since Oct 5.",
        f"Exchanges net {ex['net']:+,.0f} EGLD (about {EX_NET_EX_ARB-15179:+,.0f} ex-arbitrage and run #30 tail).",
        f"Binance.com customer flow {BIN_EXT_PER_DAY:+,.0f}/day, from +19,776: the deposit lead faded.",
        f"Binance's {f(BIN_UNDEL)} unbond still pending, matures ~{BIN_MATURES[:10]}.",
        f"ninjastaking {NINJAP['delta']:+,.0f} from one unDelegate; USDC {f(USDC_BURN)} redeemed.",
        "otc-pipeline-resumption closed not evaluable."],
    "action_items_from_previous": len(r26["meta_learning"]["recommendations_for_next_run"]),
    "action_items_completed_detail": [
        f"BINANCE UNBOND - done: run #31 lands before Oct 21, so confirmed pending via /delegation ({f(BIN_UNDEL)} EGLD, {BIN_UNDEL_DAYS:.1f} days left); wallet idle, custody unchanged.",
        f"UPBIT depositors - done: {UPD['distinct_depositors']} distinct depositors since restart 2, 0 in the window; korea-premium-arbitrage still not evaluable.",
        "CROSS-VENUE WALLETS - done: all three traced by counterparty in the window, netted out of Gate.io's flow and labelled in known-addresses (erd13sytuz92 and erd1reh7sy2c added).",
        "COINBASE ROUTING - done: Whale B, Mega Whale and routing wallet checked; no leg.",
        "WEB CHECK - done: no Coinbase/Bybit notice found; Upbit's Oct 19-23 review is the only open exchange item.",
        "FULL 7-DAY WINDOW - not done: the schedule fired on Thursday Oct 15, 2.8 days after run #30; flows stay out of the weekly baselines again."],
    "methodology_changes": [
        "RAIL WINDOW DE-DUPLICATION: the rail pass starts after the previous run's rail pass (stored as _period.rail_window_start_ts), not after the previous collector's window end.",
        "PENDING-UNBOND CHECK VIA /delegation: confirm an exchange's unbond and its maturity from userUndelegatedList before any trace.",
        "CROSS-VENUE WALLETS NETTED: exchange net flow is quoted both raw and ex cross-venue wallets."],
    "new_addresses_discovered_detail": [
        "erd13sytuz92vyz0h0l52xzw3xmuy3msulhxyzdu7h0feankdakxs9sq49uzdt - cross-venue wallet: Binance.com + Coinbase -> Bybit (5,565 this window; Gate.io -> Bybit in run #30)",
        "erd1reh7sy2c4x53wdgtgq53lnesljgsyuwlel5tq684uemn83k0et4sn3d6lc - one-shot cross-venue wallet (nonce 1): Gate.io -> Binance.com 15,179, now empty",
        "erd1vadknqe8tasfwz62sn5gre0ws8x08rnuy2lp6cw0np5aktl7sndsh9wtw7 - drip seller: 200-250 EGLD clips to Binance.com via erd137cw9q46..."],
    "action_items_completed": 5,
    "new_addresses_discovered": 3,
    "most_valuable_insight": (
        f"Since Binance.com, Coinbase and Bybit reopened (Oct 9-12), EGLD fell 23% and trailed BTC in every window, while tracked exchanges took net deposits ({ex['net']:+,.0f} EGLD this window) and Upbit's premium shrank. The halt left holders unable to sell for two weeks; the reopening is showing as supply arriving at the venues, not demand."),
    "top_recommendation": f"RUN #32 FIRST: trace Binance's {f(BIN_UNDEL)} EGLD withdraw (matures ~{BIN_MATURES[:10]}) one hop, and run a full 7-day window to test reopening-supply-overhang.",
    "recommendations_for_next_run": [
        f"BINANCE UNBOND: after ~{BIN_MATURES[:10]}, trace the withdraw from erd1r3w62vq... one hop (custody / re-delegate / hot wallet) and resolve binance-undelegation-destination.",
        "Run a full 7-day window and resolve reopening-supply-overhang (exchange net flow ex cross-venue wallets vs EGLD-BTC).",
        "UPBIT DECISION (Oct 19-23): web-check the outcome; if delisted, retire korea-premium-arbitrage and delivery-price-relevance-2.",
        "Trace erd1me5hmqt5qg...'s 26,699 EGLD ninjastaking unbond (~Oct 23) and resolve ninjastaking-exit-destination.",
        "Trace the USDC burn: find the bridge transactions behind the 79,801 redeemed and the wallets that sold EGLD for it, if any.",
        "Keep the rail window de-duplicated (start after the previous rail pass)."],
    "dashboard_feature_suggestions": [
        {"title": "Post-reopening price vs exchange net flow",
         "motivation": f"This run's main reading needs three windows side by side: EGLD fell from $4.60 (Oct 5) to ${price:.2f} while tracked exchanges took net deposits in every window (+19,442, +93,778, +9,029, and this one) since the rails reopened. The dashboard shows one window at a time, so the pattern behind reopening-supply-overhang is invisible.",
         "suggested_visualization": "dual-axis multi-run chart: EGLD and BTC indexed price lines over per-window exchange net flow bars (raw and ex cross-venue wallets), with rail reopening markers",
         "data_already_available": True, "data_source": "report JSON metadata.egld_price_usd / btc_price_usd + whale_intelligence.exchange_flows.net_change_egld across the archived reports; ex-arbitrage figure from meta_learning text (needs a field)", "priority": "high"},
        {"title": "Unbonding maturity calendar",
         "motivation": f"Two large exits are now queued with known maturity dates (Binance {f(BIN_UNDEL)} ~{BIN_MATURES[:10]}, ninjastaking 26,699 ~Oct 23) and the report can only describe them in text.",
         "suggested_visualization": "calendar / timeline of pending unbonds by maturity date, bar height = EGLD, colour = holder type (exchange, whale, retail), with resolved destinations filled in after maturity",
         "data_already_available": True, "data_source": "staking_intelligence.unbonding_in_flight.queue_this_week.largest_legs (days_to_unbond) + whale_intelligence.exit_routes.binance_undelegation", "priority": "medium"}],
    "dashboard_suggestions_followup": [
        {"title": "Intra-entity netting view for exchange flows", "status": "pending",
         "note": "Not built. Still relevant: this run adds cross-venue wallet netting (Gate.io +2,370 raw vs -18,172 ex-arbitrage), the same kind of correction."},
        {"title": "Staking-to-custody flow for exchange stake", "status": "pending",
         "note": "Not built. Becomes testable around Oct 21 when Binance's unbond matures; the unbonding calendar suggestion would cover its first half."}],
    "withdrawn_claims": [],
}

rep = {k: R[k] for k in ["metadata", "executive_summary", "network_health", "whale_intelligence", "staking_intelligence", "token_activity",
                         "defi_activity", "anomalies", "trend_indicators", "watch_list", "meta_learning", "pre_committed_tests"]}
json.dump(rep, open(f"{REPO}/reports/{RD}.json", "w"), indent=1, default=str)
print("report written", len(json.dumps(rep, default=str)), "bytes")
print(f"tests resolved this run {len(resolved)}, as_predicted {as_pred}, open {sum(1 for t in tests if t['status']=='open')}")
print("PREM", round(PREM, 1), "UP_SHARE", round(UP_SHARE, 1), "OPEN", OPEN, "DEPONLY", DEPONLY)
