#!/usr/bin/env python3
"""Run #27 stage 2: assemble reports/2026-09-28.json from derived.json + snapshot.

The week's defining facts: the chain restarted (Sep 23 16:35, halted again 16:53,
live since Sep 24 15:30) after a rollback to Sep 19 06:37:45; the exploit state is
gone; and in the ~3.7 live days not one tracked exchange wallet sent or received
EGLD apart from two re-executed Sep 19 transfers. Exchange rails are closed on
chain, so every exchange/OTC flow metric this week is a CLOSED-BOOK reading and
is kept out of the baselines.
"""
import json
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD = "2026-09-28"
O = json.load(open("/tmp/run27w/derived.json"))
D = json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev = json.load(open("/tmp/run27w/previous_run26.json"))
status = json.load(open("/tmp/run27w/status.json"))
beh = json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
r26 = json.load(open(f"{REPO}/reports/2026-09-21.json"))
disc = json.load(open(f"{REPO}/data/collected/liquid_staking_discovery_{RD}.json"))
P21 = json.load(open(f"{REPO}/data/collected/2026-09-21.json"))
XPOST = json.load(open("/tmp/run27w/exchange_post_restart_counts.json"))


def f(x, d=0):
    try:
        return f"{x:,.{d}f}"
    except Exception:
        return str(x)


def V(d_, k, default=0.0):
    return (d_ or {}).get(k, default)


def iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


M = O["macro"]; otc = O["otc"]; ex = O["exch"]; cust = O["custody"]
bid = O["bid"]; br = O["breadth"]; sk = O["staking"]; tk = O["tokens"]; xx = O["xexchange"]
df = O["defi"]; z = O["z"]; ub = O["unbond"]; absb = O["absorbers"]; zsc = O["zero_stake_cohort"]
BOOK = O["orderbook"]; WD = O["withdraw_decoded"] or {}; PZ = O["address_poisoning"] or {}
HR = O["halt_recovery"]; HRP = O["halt_recovery_prev"]; CEN = O["census"]; PR = O["poison_ring"]
econ = D["economics"]; st = D["stats"]; pecon = prev["economics"]; pact = prev["activity"]
price = M["price"]; pc = M["price_chg"]
cvc = beh["aggregates"]["compound_vs_claim_at_function_level"]
ag = beh["aggregates"]; fates = ag["delegator_fates_by_tier"]
ATTP = D.get("attacker_post_restart") or {}
zz = lambda k: z[k].get("z")
HT = df["h_tokens"]
lsd = tk["lsd"]; usdc = tk["stable"]["USDC-c76f1f"]; usdt = tk["stable"]["USDT-f8c08c"]

RESTART1, RESTART1_STOP, RESTART2 = 1790181300, 1790182386, 1790263800
WIN_START = D["_period"]["window_start_ts"]
SNAP_TS = max(v["timestamp"] for v in D["liveness"].values())
LIVE_DAYS = (SNAP_TS - RESTART2) / 86400 + (RESTART1_STOP - RESTART1) / 86400
EGLD_VS_BTC = pc - M["btc_wow"]
# Korea premium from the stored CoinGecko tickers
tick = D["cg_tickers"]["tickers"]
up = next(t for t in tick if t["market"]["name"] == "Upbit")
bn = next(t for t in tick if t["market"]["name"] == "Binance" and t["target"] == "USDT")
PREM = 100 * (up["converted_last"]["usd"] - bn["converted_last"]["usd"]) / bn["converted_last"]["usd"]
UP_SHARE = 100 * up["converted_volume"]["usd"] / BOOK["all"]["volume_24h_usd"]
# exchange rails: tracked wallets with any EGLD value tx since restart 2 (post-restart counts)
EX_SENDS = sum((x[2] or 0) for x in XPOST)
# Wave #4: the re-net this run differs from last week's only through labels (see methodology run #27)
W4_PREV = P21["otc_hub_trace_wave4"]["venue_netting"]
W4 = {"gross_out": W4_PREV["gross_out"], "gross_in": W4_PREV["gross_in"], "circular": W4_PREV["circular"],
      "net_one_way": W4_PREV["net_one_way"], "net_by_venue": W4_PREV["net_by_venue"],
      "out_by_venue": W4_PREV["outbound_by_venue"], "in_by_venue": W4_PREV["inbound_by_venue"]}
W4["circ_pct"] = 100 * W4["circular"] / W4["gross_out"]
W4_RELABEL_NET = otc["wave"]["net_one_way"]
SUM_W = prev["otc_net_one_way_series"]["run25"] + prev["otc_net_one_way_series"]["run26"]
hl = df["hatom_lending_ex_hmex_egld_pct"]
EMM_D = df["egld_mm_balance"] - df["egld_mm_prev_balance"]
legit = HR["legit"]

R = {}
# ---------------------------------------------------------------------------
R["metadata"] = {
    "report_date": RD, "period_start": "2026-09-21", "period_end": RD,
    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "egld_price_usd": price, "btc_price_usd": M["btc"], "eth_price_usd": M["eth"],
    "run_number": 27,
    "data_sources_ok": status["ok"] + [
        "follow-up pass: 8 provider scans lost to HTTP 429 re-paged in full, 212 withdraw calls decoded, poisoning lookalikes re-scanned (0 errors)",
        "post-restart exchange rail check: send/receive counts since 2026-09-24 15:30 for 20 tracked exchange wallets",
        "attacker wallet post-restart activity (109 txs)",
        "delegator reward behaviour: 8 of 8 providers sampled, run after the collector",
        "liquid-staking sweep seeded from last week's finds: all six known protocols returned"],
    "data_sources_failed": status["failed"],
    "data_sources_recovered": [
        f"LIVENESS GATE PASSED: every shard within 1 s of real time at collector start. But the 7-day window contains only {LIVE_DAYS:.1f} live days: the chain was halted until Sep 23 16:35, ran 18 minutes, halted again until Sep 24 15:30",
        "47 HTTP 429 responses in the main pass (provider scan, protocol counters, two JEX routers): all re-queried successfully in the follow-up and a targeted recovery pass",
        "SWTAO-356a25 and the other dataApi tokens priced on the first pass this week (no fallback needed)"]}

# ---------------------------------------------------------------------------
R["executive_summary"] = [
    {"category": "network", "severity": "high", "finding":
     f"THE CHAIN IS BACK, AND THE RECOVERY WAS A ROLLBACK. Block production resumed Sep 23 16:35 UTC, stopped again after 18 minutes, and has run continuously since Sep 24 15:30 (every shard within 1 second of real time at collection). "
     f"Every shard's history after Sep 19 06:37:45 was replaced, and the exploit state is gone: the attacker wallet, its contract and the 12 fan-out wallets hold {f(HR['invalid_total_egld'],2)} EGLD combined, down from {f((HRP['attacker'] or 0)+(HRP['contract'] or 0)+(HRP['fanout_total'] or 0))}. "
     f"The pre-committed test resolves on the 'broader rollback' branch, AGAINST the 'targeted recovery that preserves finalized history' framing: 64 minutes of finalized blocks were rewritten, and a Sep 24 reconstruction found 1,597 non-exploit transactions from that hour that were never re-executed (467 EGLD, mostly spam-bot transfers). "
     f"Desk and Binance-custody balances match the pre-exploit state to the EGLD; Hatom's EGLD market is +{f(EMM_D)} on ordinary post-restart activity."},
    {"category": "whale", "severity": "high", "finding":
     f"EXCHANGE RAILS ARE STILL CLOSED ON CHAIN. In {LIVE_DAYS:.1f} live days, {len(XPOST)} tracked exchange wallets sent {EX_SENDS} EGLD transaction (a re-executed Sep 19 KuCoin withdrawal of 2.9 EGLD) and received one (a re-executed 1.5 EGLD MEXC deposit). Apart from those and token-spam airdrops, nothing moved. "
     f"Every exchange balance is unchanged to the EGLD, so the net exchange flow of {ex['net']:+,.0f} is a closed book, not a flat week. The OTC desks moved {f(otc['gross_out'])} EGLD (from 314,290 in the 5.3 pre-halt days last week) and still hold {f(otc['desk_bal'])}. "
     "None of this week's exchange or pipeline readings goes into a baseline. Wave #4 ends at 467,107 EGLD one-way, netted Sep 7 to the halt."},
    {"category": "network", "severity": "high", "finding":
     f"EGLD +{pc:.2f}% WHILE BTC {M['btc_wow']:+.2f}%: {EGLD_VS_BTC:+.1f}pp of outperformance, priced inside a closed book. Upbit trades at ${up['converted_last']['usd']:.2f} against ${bn['converted_last']['usd']:.2f} on Binance, a {PREM:.0f}% premium, and carries {UP_SHARE:.0f}% of global EGLD volume. "
     "Korean buyers cannot deposit EGLD to arbitrage it away, and no holder can move EGLD onto any exchange. "
     "The week's price move therefore says little about supply and demand at open rails; the first reading after deposits reopen is the one that counts."},
    {"category": "staking", "severity": "medium", "finding":
     f"STAKING EXITS RAN HOT AFTER THE RESTART. {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD in {LIVE_DAYS:.1f} live days, a ~{f(sk['undelegated_week']/LIVE_DAYS*7)} weekly pace against 73-84K in the two prior weeks. Delegation TVL {sk['delta_locked']:+,.0f} and the staked ratio {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp). "
     f"The ratio is inside the 46.30-46.80% band, so the staked-ratio-floor test resolves 'settled lower', against 'exits continuing'. That call rests on a ratio frozen for five of seven days; the unDelegation pace is registered as a new test. "
     f"The compound rate fell to {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} vs {cvc['claim_count']}), the second sub-55% reading in three weeks. Claims were still not sold: exchanges accept no deposits."},
    {"category": "defi", "severity": "medium", "finding":
     f"DEFI RESTARTED WITHOUT A LIQUIDATION WAVE. Hatom's EGLD market rose {f(df['egld_mm_prev_balance'])} -> {f(df['egld_mm_balance'])} EGLD, with HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.2f}% and HUSDC {HT['HUSDC-d80042']['supply_pct']:+.2f}%: depositors added collateral. "
     f"xExchange volume was ${f(bid['dexvol'])} over 24h ({f(bid['dexvol_egld'])} EGLD), {bid['wegld_usdc_share']:.0f}% of it WEGLD/USDC. Bridged dollars kept draining: USDC {usdc['pct']:+.2f}% and USDT {usdt['pct']:+.2f}%. "
     f"LSD supplies were flat (SEGLD {lsd['SEGLD-3ad2d0']['pct']:+.2f}%, XEGLD {lsd['XEGLD-e413ed']['pct']:+.2f}%)."},
    {"category": "anomaly", "severity": "low", "finding":
     f"THE EXPLOIT WALLET IS STILL ACTIVE. On Sep 27 between 19:58 and 20:05 UTC it sent its remaining {f(ATTP.get('out_egld',0),1)} EGLD to {ATTP.get('distinct_receivers',0)} distinct wallets in 0.1066 EGLD pieces, some fresh (nonce 16) and some long-lived. "
     f"The amount is trivial. The pattern (fan-out to over a hundred addresses) is the kind that seeds later attribution noise. The address-poisoning operator sent {PR['operator_out_7d']} dust transactions this week; neither desk lookalike has received anything above dust."},
]

# ---------------------------------------------------------------------------
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
               "btc_correlation_note": f"BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%, EGLD {pc:+.2f}%: EGLD outperformed BTC by {EGLD_VS_BTC:.1f}pp with deposits closed at every tracked venue and a {PREM:.0f}% Upbit premium."},
    "liveness": {"ok": D["liveness_ok"], "latest_block_by_shard": {k: iso(v["timestamp"]) for k, v in D["liveness"].items()},
                 "restart_1_utc": iso(RESTART1), "restart_1_stopped_utc": iso(RESTART1_STOP), "restart_2_utc": iso(RESTART2),
                 "live_days_in_window": round(LIVE_DAYS, 2),
                 "rollback_point_utc": "2026-09-19 06:37:45 UTC"},
    "analysis": (
        f"THE CHAIN IS LIVE AGAIN, ON A REWRITTEN HISTORY. The collector's new liveness gate read every shard within a second of real time. The epoch counter is {st['epoch']} ({st['epoch']-pact['epoch']:+d} on the week) and {f(st['transactions']-pact['total_transactions'])} transactions were added, about {f(int((st['transactions']-pact['total_transactions'])/LIVE_DAYS))} per live day. That is in line with the pre-halt rate. "
        f"The window, though, is {LIVE_DAYS:.1f} live days, not seven: the first restart at 16:35 on Sep 23 ran for 18 minutes and stopped on every shard, and the network has been continuously live only since 15:30 on Sep 24.\n\n"
        "WHAT THE RECOVERY DID. MultiversX said it would preserve finalized history and target only incident-related changes. The chain shows a rollback: every shard's blocks after 06:37:45 on Sep 19 were replaced, and the same heights now carry Sep 23-24 timestamps. "
        "Legitimate transactions from the rolled-back hour were re-executed after restart 2 (15:40-15:58 on Sep 24). A reconstruction on Sep 24 found 1,597 non-exploit transactions from that hour that were not replayed. They moved 467 EGLD, mostly from two spam bots, and three of the four value-bearing ones went to the wallet that funded the attacker on Sep 16. "
        f"The exploit's balances are gone ({f(HR['invalid_total_egld'],2)} EGLD across the 14 incident addresses), and the minted total supply never entered /economics: total supply reads {f(econ['totalSupply'])} ({econ['totalSupply']-pecon['total_supply']:+,} on the week).\n\n"
        f"ISSUANCE. Staked EGLD {M['staked_chg']:+,.0f} to {f(econ['staked'])}, ratio {100*M['sr']:.2f}%. Total supply rose only {f(econ['totalSupply']-pecon['total_supply'])} EGLD over the week because epochs did not advance while the chain was down. The downtime was not paid out as normal epochs, so stakers forwent roughly 27K EGLD of rewards.\n\n"
        f"PRICE. EGLD ${price:.2f}, {pc:+.2f}% on the week, while BTC fell {abs(M['btc_wow']):.2f}% and ETH {abs(M['eth_wow']):.2f}%. The hourly path went from $3.64 on Sep 20 to $4.70 on Sep 27 and eased to ${price:.2f}. "
        f"Upbit is {UP_SHARE:.0f}% of global volume and trades {PREM:.0f}% above Binance, and no EGLD can reach Korean exchanges to close the gap. This is the price of a closed market, and the report reads it that way.")}

# ---------------------------------------------------------------------------
def tier(v):
    if v > 1_000_000: return "mega"
    if v >= 100_000: return "large"
    if v >= 10_000: return "mid"


def ent(n):
    return next((e2 for e2 in ex["entity"] if e2["entity"] == n), {"net_flow_egld": 0, "pct": 0, "wallets_count": 0})


def entity_interp(e):
    return (f"{e['net_flow_egld']:+,.0f}: unchanged to the EGLD across {e['wallets_count']} wallet(s). No EGLD deposit or withdrawal since the restart; the rail is closed on chain, "
            "so this is a closed-book reading, not evidence of balance.")


INV_SERIES = {**prev["otc_desk_inventory_series"], "run27": round(otc["desk_bal"])}
r26o = r26["whale_intelligence"]["otc_pipeline"]
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
        "rail_status": {"tracked_wallets": len(XPOST), "egld_sends_since_restart": EX_SENDS,
                        "note": "the only EGLD movements are re-executions of Sep 19 transfers (KuCoin 2.9 out, MEXC 1.5 in); other inbound since restart is token-spam ESDT airdrops"},
        "signal": (f"CLOSED BOOK. Net exchange flow {ex['net']:+,.0f} EGLD because no tracked exchange wallet has moved EGLD since the restart: {EX_SENDS} send across {len(XPOST)} wallets, a re-executed Sep 19 transfer. "
                   "Balances equal the stored pre-exploit values to the EGLD, which also confirms the rollback reversed the minted deposits at Binance.com, KuCoin and MEXC. This reading is excluded from the exchange-flow baseline."),
        "by_exchange": [{"exchange": w["exchange"], "change_egld": w["change_egld"], "pct": w["pct"]} for w in ex["per_wallet"]],
        "entity_netting": [{"entity": e2["entity"], "wallets_count": e2["wallets_count"],
                            "net_flow_egld": e2["net_flow_egld"], "interpretation": entity_interp(e2)} for e2 in ex["entity"]]},
    "dormant_activations": [],
    "halt_recovery": {
        "invalid_balances_egld_now": HR["invalid_total_egld"],
        "invalid_balances_egld_at_halt": (HRP["attacker"] or 0) + (HRP["contract"] or 0) + (HRP["fanout_total"] or 0),
        "attacker_balance_egld": HR["attacker"].get("balance_egld"), "attacker_nonce": HR["attacker"].get("nonce"),
        "contract_balance_egld": HR["contract"].get("balance_egld"),
        "fanout_wallets_balance_egld": sum(v.get("balance_egld", 0) or 0 for v in HR["fanout"].values()),
        "legitimate_balances": {k: {"now_egld": v.get("balance_egld"),
                                    "pre_halt_egld": prev["pre_halt_reference_balances"].get(
                                        {"UPbit OTC Desk": "otc_desks", "OTC Distribution Wallet": "otc_desks",
                                         "Binance Staking custody": "binance_custody", "Hatom EGLD money market": "hatom_egld_mm"}[k])}
                                for k, v in legit.items()},
        "attacker_post_restart": ATTP,
        "rollback_point_utc": "2026-09-19 06:37:45 UTC",
        "not_replayed_non_incident_txs": 1597, "not_replayed_value_egld": 467,
        "method_note": "Balances read at the first weekly snapshot after restart. The OTC-desk reference is the two desks combined (46,637)."},
    "otc_pipeline": {
        "gross_outbound_egld_7d": otc["gross_out"], "gross_inbound_egld_7d": otc["gross_in"],
        "circular_egld_7d": otc["circular"], "net_one_way_egld_7d": otc["net_one_way"],
        "circular_share_pct": otc["circ_pct"],
        "desk_balance_egld": otc["desk_bal"], "previous_desk_balance_egld": otc["prev_desk"],
        "upbit_reload_egld": otc["upbit_feed"],
        "venue_netting": [{"venue": v, "desk_to_venue_egld": otc["out_by_venue"].get(v, 0),
                           "venue_to_desk_egld": otc["in_by_venue"].get(v, 0), "net_egld": otc["net_by_venue"][v]}
                          for v in sorted(otc["net_by_venue"], key=lambda k: -abs(otc["net_by_venue"][k]))],
        "gross_series_egld_7d": {**r26o["gross_series_egld_7d"], "run27": otc["gross_out"]},
        "net_one_way_series_egld_7d": {**r26o["net_one_way_series_egld_7d"], "run27": otc["net_one_way"]},
        "desk_inventory_series_egld": INV_SERIES,
        "circularity_series_pct": {**r26o["circularity_series_pct"], "run27": 0.0},
        "peak_window_renetted": r26o["peak_window_renetted"],
        "backfilled_windows": r26o.get("backfilled_windows", []),
        "wave_window_netting": {
            "window": "2026-09-07..2026-09-19 halt (wave #4, final: no desk activity after the restart)",
            "gross_outbound_egld": W4["gross_out"], "gross_inbound_egld": W4["gross_in"],
            "circular_egld": W4["circular"], "circular_share_pct": W4["circ_pct"],
            "net_one_way_egld": W4["net_one_way"], "sum_of_weekly_nets_egld": SUM_W,
            "weekly_frame_overstatement_egld": SUM_W - W4["net_one_way"],
            "weekly_frame_overstatement_pct": 100 * (SUM_W - W4["net_one_way"]) / W4["net_one_way"],
            "net_by_venue": W4["net_by_venue"], "outbound_by_venue": W4["out_by_venue"], "inbound_by_venue": W4["in_by_venue"],
            "note": (f"Wave #4 is closed at {f(W4['net_one_way'])} EGLD one-way (Sep 7 to the halt, run #26 labels). Re-netting the identical transactions with this week's label set gives {f(W4_RELABEL_NET)}: "
                     "router labels that contain 'Unknown Whale I' are now resolved as venues of their own, which removes 152K of circularity. The transactions are the same; only the attribution differs, so the frozen-label figure stands (run #24 rule).")},
        "feed_by_parent_venue": [],
        "feeder_backtrace": O["feeder_backtrace"],
        "address_poisoning": [{"address": a, "mimics": v["note"], "nonce": v["nonce"], "dust_txs_30d": v["dust_txs_30d"],
                               "distinct_targets_30d": v["distinct_targets_30d"],
                               "inbound_above_0_01_egld": len(v["inbound_above_0_01_egld"])} for a, v in PZ.items()],
        "series_note": (f"CLOSED BOOK. The desks moved {f(otc['gross_out'])} EGLD in the week and their balance is unchanged at {f(otc['desk_bal'])}. "
                        "Nothing can leave for a venue while exchange deposits are closed, so this week's point shows the rails, not the pipeline's intent. It is kept out of the baselines.")},
    "demand_instruments": {
        "identifiable_bid_absorbed_egld_7d": 0.0,
        "mega_whale_balance_egld": bid["mega_bal"] or 0.0, "mega_whale_change_egld": bid["mega_delta"],
        "coinbase_routing_balance_egld": bid["cbr_bal"] or 0.0, "coinbase_routing_inflow_egld": 0,
        "coinbase_routing_funder": None, "coinbase_routing_funder_label": "n/a - no inbound this week",
        "weeks_at_zero": 7, "weeks_at_zero_in_last_four": 4, "bid_to_distribution_ratio_pct": 0.0,
        "dex_turnover_ratio_pct": bid["turnover"], "previous_dex_turnover_ratio_pct": bid["prev_turnover"],
        "dex_volume_egld_24h": bid["dexvol_egld"], "previous_dex_volume_egld_24h": bid["prev_dexvol_egld"],
        "pool_tvl_egld": bid["pooltvl_egld"], "previous_pool_tvl_egld": bid["prev_pooltvl_egld"],
        "wegld_usdc_volume_usd": bid["wegld_usdc_vol"], "wegld_usdc_share_of_volume_pct": bid["wegld_usdc_share"],
        "ex_wegld_usdc_volume_usd": bid["ex_wegld_usdc_vol"], "ex_wegld_usdc_volume_egld": bid["ex_wegld_usdc_vol_egld"],
        "dex_volume_status": "evaluable (chain live > 24h at the snapshot); the previous value is run #25's, the last evaluable reading",
        "absorber_scan": {"terminals_scanned": absb["scanned"],
                          "terminals_retaining_over_half": len(absb["retaining"]),
                          "total_received_from_desks_egld": absb["total_received"],
                          "total_retained_egld": absb["total_balance_held"],
                          "retained_share_pct": 100 * absb["total_balance_held"] / absb["total_received"] if absb["total_received"] else 0,
                          "verdict": f"Fifth week, same answer: {absb['scanned']} desk terminals hold {f(absb['total_balance_held'])} of what passed through them."},
        "withdrawal_breadth": {"distinct_recipients_raw": br["raw_n"], "total_egld_raw": br["raw_egld"],
                               "distinct_recipients_ex_pipeline": br["ex_n"], "total_egld_ex_pipeline": br["ex_egld"],
                               "pipeline_share_pct": br["pipeline_share"], "top_two_share_pct": br["top_two_share_pct"]},
        "withdrawal_breadth_top": br["top"],
        "exchange_orderbook": {
            "source": "CoinGecko exchange tickers with 2% depth and daily spot volume (third-party). CLOSED BOOK: read with EGLD deposits and withdrawals closed at every tracked venue",
            "binance": BOOK["binance"], "bybit": BOOK["bybit"], "upbit": BOOK["upbit"],
            "coinbase": BOOK["coinbase"], "gate": BOOK["gate"], "all_venues": BOOK["all"],
            "spot_volume_7d_egld": BOOK["spot_volume_7d_egld"] or 0.0,
            "spot_volume_prior_7d_egld": BOOK["spot_volume_prior_7d_egld"] or 0.0,
            "net_one_way_share_of_spot_volume_pct": 100 * otc["net_one_way"] / BOOK["spot_volume_7d_egld"] if BOOK["spot_volume_7d_egld"] else 0.0,
            "previous_net_one_way_share_of_spot_volume_pct": prev["exchange_orderbook"]["net_one_way_share_of_spot_volume_pct"],
            "binance_bybit_net_delivery_usd_7d": 0.0,
            "binance_bybit_bid_depth_2pct_usd": BOOK["binance"]["depth_minus2_usd"] + BOOK["bybit"]["depth_minus2_usd"],
            "previous_binance_bybit_bid_depth_2pct_usd": prev["exchange_orderbook"]["binance_bybit_bid_depth_2pct_usd"],
            "venue_depth_wow": {v: {"bid_now": BOOK[v]["depth_minus2_usd"], "bid_prev": prev["exchange_orderbook"][v]["depth_minus2_usd"],
                                    "ask_now": BOOK[v]["depth_plus2_usd"], "ask_prev": prev["exchange_orderbook"][v]["depth_plus2_usd"]}
                                for v in ("binance", "bybit", "upbit", "coinbase", "gate")},
            "korea_premium_pct": PREM, "upbit_share_of_volume_pct": UP_SHARE,
            "delivery_share_series": BOOK["delivery_share_series"], "top_tickers": BOOK["top"]}},
}
bbn = BOOK["binance"]["depth_minus2_usd"] + BOOK["bybit"]["depth_minus2_usd"]
R["whale_intelligence"]["analysis"] = (
    f"THE ROLLBACK UNDID THE EXPLOIT'S BALANCE SHEET. Last week's top-account list began with a 41.3M EGLD attacker wallet and a 25.6M contract. Both now hold dust ({f(HR['attacker']['balance_egld'],2)} and {f(HR['contract']['balance_egld'],3)} EGLD), all 12 fan-out wallets are empty at nonce 0, and Binance.com, KuCoin and MEXC balances equal the net-of-incident figures this model stored. "
    "Storing net balances last week is what keeps this week's flow from showing the reversal as a -4.9M phantom outflow.\n\n"
    f"NOTHING MOVED ON THE EXCHANGE SIDE. {len(XPOST)} tracked exchange wallets, {EX_SENDS} send since restart 2 plus one receipt, both re-executed Sep 19 transfers (KuCoin 2.9 EGLD out, MEXC 1.5 EGLD in). Every tracked balance is unchanged to the EGLD. "
    "In an open week a flat aggregate is the sum of offsetting flows; here there are no flows. This is the most important caveat on the whole report: until deposits reopen, every exchange-side number describes the suspension.\n\n"
    f"PIPELINE. The desks moved {f(otc['gross_out'])} EGLD all week and hold {f(otc['desk_bal'])}, exactly last week's figure. Wave #4 closes at {f(W4['net_one_way'])} EGLD one-way, Sep 7 to the halt ({W4['circ_pct']:.0f}% circular). Its two weekly frames sum to {f(SUM_W)}, so the straddle is small. "
    f"LABEL DRIFT: re-netting the same wave with this week's label set gives {f(W4_RELABEL_NET)}, because the resolver treats any label containing 'Whale' as a venue and run #24-#25 router labels now contain 'Unknown Whale I'. The run #24 rule applies (freeze the label set, never mix stages), and the frozen figure stands.\n\n"
    f"UNKNOWN WHALE I. The census for the pre-registered test found {CEN['Unknown Whale I']['inbound_txs']} inbound transactions from {CEN['Unknown Whale I']['distinct_senders']} senders, both token-spam, and no outbound. erd1a6lte0 shows {CEN['erd1a6lte0']['inbound_txs']}. "
    "An exchange hot wallet with closed rails would look exactly like this, and so would an idle operator, so the test is not evaluable this week. It stays open.\n\n"
    f"TIERS. On the common-address basis ({O['tiers_basis']} wallets): mega {O['tiers']['mega']['net_change_egld']:+,.0f}, large {O['tiers']['large']['net_change_egld']:+,.0f}, mid {O['tiers']['mid']['net_change_egld']:+,.0f}. The only wallet changes above 2,000 EGLD are contracts (Hatom's EGLD market +13,419, an xExchange WEGLD shard -2,997) and two team funds (+5,012 each, epoch distributions). "
    f"No holder above 10,000 EGLD moved.\n\n"
    f"DEMAND, READ WITH CARE. xExchange turnover {bid['turnover']:.2f}% of pool TVL ({f(bid['dexvol_egld'])} EGLD/24h). Binance+Bybit bids within 2% of mid total ${f(bbn)}, and the 7-day CEX spot volume is {f(BOOK['spot_volume_7d_egld']/1e6,2)}M EGLD. Upbit is {UP_SHARE:.0f}% of that at a {PREM:.0f}% premium. "
    "All of it is a closed-book reading, so none of it is appended to the baselines.")

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
                   "fee_pct": mv(ident, "fee") or 0.0, "weeks_in_state": 4,
                   "note": f"FOURTH WEEK AFTER THE FEE REVERSAL: book {mv(ident,'delta'):+,.0f}, users {mv(ident,'users_delta'):+d}. Still losing capital with yield restored."})
wd_top = WD.get("by_provider_top", [])
UNDEL_PACE = sk["undelegated_week"] / LIVE_DAYS * 7
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
                          "note": "Zero transitions for a fourth week; the fourth-deregistration test resolves 'idiosyncratic'. Join on contract address, 100% match, no identity changes."},
    "fee_events": [{"provider": i, "fee_from_pct": 100.0, "fee_to_pct": mv(i, "fee") or 0.0, "apr_from_pct": 0.0, "apr_to_pct": mv(i, "apr") or 0.0,
                    "locked_egld": mv(i, "locked"), "locked_wow_egld": mv(i, "delta"), "users": mv(i, "users"),
                    "users_wow": mv(i, "users_delta"), "num_nodes": mv(i, "nodes")} for i in ("egldstakingprovider", "procryptostaking")],
    "unbonding_in_flight": {
        "wallet": ub["wallet"], "total_egld": ub["pending_total"],
        "legs": [{"provider": p["contract"][:10] + "..." + p["contract"][-8:], "amount": p["amount_egld"],
                  "days_to_unbond": p["days_remaining"], "date": "2026-08-14" if p["amount_egld"] < 100000 else "2026-08-15"} for p in ub["pending"]],
        "share_of_delegation_decline_pct": 0.0, "raw_residual_egld": sk["residual"], "corrected_direct_node_egld": None,
        "status": f"RETIRED, SIXTH WEEK UNMOVED. Balance {f(ub['balance'],2)} EGLD, {f(ub['pending_total'])} unbonded-and-unclaimed.",
        "queue_this_week": {
            "undelegated_egld": sk["undelegated_week"], "distinct_callers": sk["undelegate_callers"],
            "measured_pending_egld": sk["pool_total"], "largest_legs": sk["pool_rows"][:12],
            "withdraw_calls": O["withdraw_calls"], "previous_withdraw_calls": O["prev_withdraw_calls"],
            "withdraw_egld_returned": WD.get("egld_returned_total", 0.0),
            "withdraw_egld_by_provider_top": [{"provider": a, "egld": b} for a, b in wd_top[:8]],
            "undelegated_weekly_pace_egld": UNDEL_PACE, "live_days": LIVE_DAYS,
            "coverage_note": (f"Full-set scan of {sk['providers_scanned']} provider contracts; 8 scans lost to HTTP 429 were re-paged in the follow-up. {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD in {LIVE_DAYS:.1f} live days "
                              f"(weekly pace ~{f(UNDEL_PACE)}); {O['withdraw_calls']} withdraw calls returned {f(WD.get('egld_returned_total',0))} EGLD.")}},
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
            f"COMPOUND RATE {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} reDelegateRewards vs {cvc['claim_count']} claimRewards), from 62.68%. Series: 62.25 / 59.54 / 59.07 / 57.03 / 57.51 / 62.05 / 49.44 / 62.68 / {cvc['compound_pct_of_reward_decisions']:.2f}. Second sub-55% reading in three weeks, both right after a shock (the MEX incident week and the restart).",
            f"Retail {fates['retail']['total_events']} claims, {fates['retail']['by_count'].get('sold',0)} to a labelled exchange; mid-tier {fates['mid_tier']['total_events']}, {fates['mid_tier']['by_count'].get('sold',0)} sold; institutional {fates.get('institutional',{}).get('total_events',0)}, {fates.get('institutional',{}).get('by_count',{}).get('sold',0)} sold. With deposits closed a sale to an exchange is not possible this week, so the 'held' reading carries no information.",
            f"CAVEAT: the 7-day scan window holds {LIVE_DAYS:.1f} live days, most of them right after the restart.",
            f"Sample: {ag['providers_sampled']} of {ag.get('providers_requested',8)} providers, {ag.get('api_errors',0)} retried API errors.",
            "PROVIDER OPERATORS DID NOT SELL FEES for a fifteenth consecutive run (and could not deposit this week)."]},
    "analysis": (
        f"EXITS ACCELERATED ON RESTART. In {LIVE_DAYS:.1f} live days {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD, a weekly pace of about {f(UNDEL_PACE)} against 73,351 and 84,169 in the two weeks before the halt. "
        f"The largest queue legs are one wallet (erd155j9c36h...) with 8,888 EGLD from each of three providers, and orangestaking ({mv('orangestaking','delta'):+,.0f}), star_staking ({mv('star_staking','delta'):+,.0f}) and vaporrepublic ({mv('vaporrepublic','delta'):+,.0f}) are the largest losers. "
        f"Withdraw calls returned {f(WD.get('egld_returned_total',0))} EGLD (meria {f(wd_top[0][1]) if wd_top else 'n/a'}). None of that EGLD can reach an exchange yet, which means the unbonding queue is building a supply that arrives when rails reopen: {f(sk['pool_total'])} EGLD measured pending among the largest callers.\n\n"
        f"THE RATIO. Staked ratio {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp), inside run #25's 46.30-46.80% band, so staked-ratio-floor resolves 'settled lower'. Delegation TVL {sk['delta_locked']:+,.0f} to {f(tl)}; the staked-minus-delegated residual {sk['residual']:+,.0f} carries no direct-node signal while unbonding is this active.\n\n"
        f"COMPOUNDING DIPPED AGAIN. {cvc['compound_pct_of_reward_decisions']:.2f}% compound, the second sub-55% reading in three weeks, and both followed shocks. The run #26 test rejected a regime switch; this reading is a candidate, not a finding, until it holds a second week.\n\n"
        f"DELEGATORS {sk['users_delta']:+,} to {f(sk['users'])}: flat, as for fourteen weeks. {sk['gaining']} providers gained, {sk['losing']} lost. "
        f"DEREGISTRATION: zero transitions for a fourth week; the three known cases are idiosyncratic (ledgerbyfigment {dser.get('ledgerbyfigment',{}).get('users_delta',0):+d}, p2p_org_ {dser.get('p2p_org_',{}).get('users_delta',0):+d}, stakedinc unchanged).")}

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
        "volume_status": "evaluable; the comparison is against run #25 (run #26's 24h window had no blocks)",
        "mex_pair_depth": {"pair": "MEX/WEGLD", "tvl_usd": xx["mex_pair_depth"]["tvl_usd"], "tvl_egld": xx["mex_pair_depth"]["tvl_egld"],
                           "previous_tvl_egld": xx["mex_pair_depth"]["previous_tvl_egld"], "tvl_egld_wow_pct": xx["mex_pair_depth"]["tvl_egld_wow_pct"],
                           "volume_24h_usd": xx["mex_pair_depth"]["volume_24h_usd"], "trades_24h": xx["mex_pair_depth"]["trades_24h"],
                           "share_of_pool_tvl_pct": xx["mex_pair_depth"]["share_of_pool_tvl_pct"], "depth_rank": xx["mex_pair_depth"]["depth_rank"]},
        "mex_pair_event": r26["token_activity"]["xexchange"]["mex_pair_event"]},
    "analysis": (
        f"xEXCHANGE CAME BACK THIN. 24h volume ${f(xx['vol'])} ({f(bid['dexvol_egld'])} EGLD) against ${f(xx['prev_vol'])} ({f(bid['prev_dexvol_egld'])} EGLD) in run #25, the last week with an evaluable 24h window. "
        f"WEGLD/USDC is {bid['wegld_usdc_share']:.0f}% of it and everything else together traded {f(bid['ex_wegld_usdc_vol_egld'])} EGLD. Turnover {bid['turnover']:.2f}% of pool TVL. "
        f"Depth held: pool TVL {f(bid['pooltvl_egld'])} EGLD ({100*(bid['pooltvl_egld']-bid['prev_pooltvl_egld'])/bid['prev_pooltvl_egld']:+.1f}% in EGLD terms). "
        "The DEX is the one EGLD venue that is open, since on-chain swaps need no exchange deposit, and it is barely being used as one: the arbitrage between on-chain and Korean prices cannot run while EGLD cannot reach Upbit.\n\n"
        f"MEX prices at {xx['mex_price']:.2e} from the pool ({xx['mex_wow']:+.1f}% WoW); MEX/WEGLD holds ${f(xx['mex_pair_depth']['tvl_usd'])}, rank {xx['mex_pair_depth']['depth_rank']} by depth.\n\n"
        f"STABLECOINS KEPT BURNING: USDC {usdc['pct']:+.2f}% to {f(usdc['supply'])} and USDT {usdt['pct']:+.2f}% to {f(usdt['supply'])}. The bridge worked through the halt window's aftermath, and dollars left rather than arrived. "
        f"NEWLY ISSUED: {len(newly)} issuance{'s' if len(newly)!=1 else ''}, none clears the quality bar.")}

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
         "notable_events": f"Volume ${f(xx['vol'])}/24h after restart, {bid['wegld_usdc_share']:.0f}% WEGLD/USDC. WEGLD contract balances {f(df['xexch_egld'])} EGLD ({xe_egld_pct:+.1f}%).",
         "health_signal": hs(xe_egld_pct)},
        {"protocol": "Hatom Lending", "category": "lending", "addresses_tracked": 13, "tvl_usd": df["hatom_lending_usd"], "tvl_egld": df["hatom_lending_egld"],
         "tvl_wow_change_pct": hl, "transfers_24h": cnt("Hatom EGLD MM"),
         "notable_events": f"EGLD market {f(df['egld_mm_prev_balance'])} -> {f(df['egld_mm_balance'])} EGLD, HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.2f}%, HUSDC {HT['HUSDC-d80042']['supply_pct']:+.2f}%. Aggregate lending TVL in EGLD {hl:+.2f}% on a {pc:+.2f}% price week (mechanical: dollar collateral shrinks in EGLD terms when EGLD rises). No liquidation wave on restart.",
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
         "notable_events": f"XEGLD supply {lsd['XEGLD-e413ed']['pct']:+.2f}% to {f(lsd['XEGLD-e413ed']['supply'])}, a second week of mild redemption.",
         "health_signal": hs(lsd["XEGLD-e413ed"]["pct"])},
        {"protocol": "XOXNO Aggregator", "category": "aggregator", "addresses_tracked": 1, "tvl_usd": 0.0, "tvl_egld": 0.0, "tvl_wow_change_pct": None,
         "transfers_24h": cnt("XOXNO Aggregator"), "volume_24h_usd": 0.0, "notable_events": f"{f(cnt('XOXNO Aggregator'))} transfers in 24h, back to normal range.", "health_signal": "flat"},
        {"protocol": "OneDex", "category": "aggregator", "addresses_tracked": 5, "tvl_usd": 0.0, "tvl_egld": 0.0, "tvl_wow_change_pct": None,
         "transfers_24h": cnt("OneDex Swap"), "volume_24h_usd": 0.0, "notable_events": f"{f(cnt('OneDex Swap'))} transfers in 24h. OneDex Launchpad still fails bech32 validation.", "health_signal": "flat"},
        {"protocol": "JEXchange", "category": "dex", "addresses_tracked": 10, "tvl_usd": 0.0, "tvl_egld": 0.0, "tvl_wow_change_pct": None,
         "transfers_24h": cnt("JEXchange Router"), "volume_24h_usd": 0.0,
         "notable_events": f"7-day router transfers {f(jex7.get('JEXchange Router'))} on the main router ({LIVE_DAYS:.1f} live days), " + ", ".join(f(jex7.get(f'JEXchange Router {i}')) for i in range(2, 6)) + " on routers 2-5.",
         "health_signal": "shrinking"},
        {"protocol": "JewelSwap", "category": "liquid_staking", "addresses_tracked": 1, "tvl_usd": (es("JWLEGLD-023462") or 0) * price, "tvl_egld": es("JWLEGLD-023462") or 0.0,
         "tvl_wow_change_pct": ep("JWLEGLD-023462"), "transfers_24h": None,
         "notable_events": f"{f(es('JWLEGLD-023462'))} EGLD delegated, {em['JWLEGLD-023462']['holders']} holders.", "health_signal": hs(ep("JWLEGLD-023462"))},
        {"protocol": "SALSA (Staking Agency)", "category": "liquid_staking", "addresses_tracked": 1, "tvl_usd": (es("LEGLD-d74da9") or 0) * price, "tvl_egld": es("LEGLD-d74da9") or 0.0,
         "tvl_wow_change_pct": ep("LEGLD-d74da9"), "transfers_24h": None,
         "notable_events": f"{f(es('LEGLD-d74da9'))} EGLD delegated; LEGLD supply {(em['LEGLD-d74da9']['pct'] or 0):+.2f}%.", "health_signal": hs(ep("LEGLD-d74da9"))},
        {"protocol": "Dinovox VoxEGLD", "category": "liquid_staking", "addresses_tracked": 1, "tvl_usd": (es("VOXEGLD-5872e5") or 0) * price, "tvl_egld": es("VOXEGLD-5872e5") or 0.0,
         "tvl_wow_change_pct": ep("VOXEGLD-5872e5"), "transfers_24h": None,
         "notable_events": f"{f(es('VOXEGLD-5872e5'))} EGLD, supply {(em['VOXEGLD-5872e5']['pct'] or 0):+.1f}%, holders {em['VOXEGLD-5872e5']['holders']}: still growing through the halt.", "health_signal": hs(ep("VOXEGLD-5872e5"))},
        {"protocol": "VestaX Finance", "category": "liquid_staking", "addresses_tracked": 1, "tvl_usd": (es("VEGLD-2b9319") or 0) * price, "tvl_egld": es("VEGLD-2b9319") or 0.0,
         "tvl_wow_change_pct": ep("VEGLD-2b9319"), "transfers_24h": None,
         "notable_events": f"{f(es('VEGLD-2b9319'))} EGLD.", "health_signal": hs(ep("VEGLD-2b9319"))}],
    "sc_deployments": [],
    "analysis": (
        f"THE RESTART DID NOT BREAK THE LENDING MARKETS. Last week's worry was that collateral would reprice at a price that moved while no one could act. EGLD had risen through the halt, so the reprice favoured borrowers, and the EGLD market ADDED {f(EMM_D)} EGLD ({f(df['egld_mm_prev_balance'])} -> {f(df['egld_mm_balance'])}). "
        f"HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.2f}% is the behavioural read: EGLD depositors added. HUSDC {HT['HUSDC-d80042']['supply_pct']:+.2f}%, HUSDT {HT['HUSDT-6f0914']['supply_pct']:+.2f}%. "
        f"Aggregate lending TVL in EGLD moved {hl:+.2f}%, which is mechanical on a {pc:+.2f}% week (dollar collateral is worth less EGLD), so the run #25 rule reads the HEGLD leg: the inverse rule's sign (depositors adding on an up week) is AGAINST it this week, with the halt as a confounder.\n\n"
        f"LIQUID STAKING FLAT. SEGLD {lsd['SEGLD-3ad2d0']['pct']:+.2f}%, XEGLD {lsd['XEGLD-e413ed']['pct']:+.2f}%, SWTAO {lsd['SWTAO-356a25']['pct']:+.2f}%, USH {lsd['USH-111e09']['pct']:+.2f}%. Among the emerging LSDs, VoxEGLD grew {(em['VOXEGLD-5872e5']['pct'] or 0):+.1f}% and the others were unchanged. The sweep returned all six known protocols.\n\n"
        f"ACTIVITY. XOXNO aggregator {f(cnt('XOXNO Aggregator'))} transfers in 24h, OneDex {f(cnt('OneDex Swap'))}, Hatom LSD {f(cnt('Hatom Liquid Staking'))}: normal ranges, which means on-chain DeFi users came back at once, while exchange users could not.")}

# ---------------------------------------------------------------------------
R["anomalies"] = [
    {"metric": "exchange_egld_sends_since_restart", "current_value": EX_SENDS, "previous_value": None, "method": "rule_based", "severity": "high",
     "description": f"{len(XPOST)} tracked exchange wallets sent {EX_SENDS} EGLD transaction in {LIVE_DAYS:.1f} live days and received one, both re-executions of Sep 19 transfers; no new EGLD deposits or withdrawals. On-chain exchange rails are closed; every exchange and OTC flow this week is a closed-book reading."},
    {"metric": "egld_vs_btc_wow_pp", "current_value": EGLD_VS_BTC, "previous_value": None, "method": "rule_based", "severity": "medium",
     "description": f"EGLD {pc:+.2f}% vs BTC {M['btc_wow']:+.2f}%: {EGLD_VS_BTC:+.1f}pp relative strength with a {PREM:.0f}% Upbit premium and Upbit {UP_SHARE:.0f}% of global volume. Price discovery is happening in a market that cannot receive supply."},
    {"metric": "egld_price_usd", "current_value": price, "previous_value": M["prev_price"], "method": "z_score", "severity": z["price"].get("severity", "low"),
     "average_value": z["price"].get("mean"), "stddev": z["price"].get("stddev"), "z_score": zz("price"), "change_pct": pc,
     "description": f"z={zz('price'):+.2f} against the 8-week baseline; the absolute z understates an EGLD-specific move in a week BTC fell (run #16 rule)."},
    {"metric": "unbonding_queue_undelegated_egld_7d", "current_value": sk["undelegated_week"], "previous_value": 84169, "method": "rule_based", "severity": "medium",
     "change_pct": 100 * (sk["undelegated_week"] - 84169) / 84169,
     "description": f"{f(sk['undelegated_week'])} EGLD unDelegated by {sk['undelegate_callers']} wallets in {LIVE_DAYS:.1f} live days, a ~{f(UNDEL_PACE)}/week pace against 84,169 the week before. Not appended to the weekly baseline (short window)."},
    {"metric": "reward_compound_pct", "current_value": cvc["compound_pct_of_reward_decisions"], "previous_value": 62.68, "method": "z_score", "severity": z["compound"].get("severity", "low"),
     "average_value": z["compound"].get("mean"), "stddev": z["compound"].get("stddev"), "z_score": zz("compound"),
     "change_pct": 100 * (cvc["compound_pct_of_reward_decisions"] - 62.68) / 62.68,
     "description": f"Compound {cvc['compound_pct_of_reward_decisions']:.2f}% from 62.68% (z={zz('compound'):+.2f}); second sub-55% reading in three weeks, both after a shock."},
    {"metric": "staked_ratio", "current_value": M["sr"], "previous_value": M["sr_prev"], "method": "z_score", "severity": z["sr"].get("severity", "low"),
     "average_value": z["sr"].get("mean"), "stddev": z["sr"].get("stddev"), "z_score": zz("sr"), "change_pct": 100 * (M["sr"] - M["sr_prev"]) / M["sr_prev"],
     "description": f"Staked ratio {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp), z={zz('sr'):+.2f}: the level is two standard deviations below the 8-week mean after the September step down, and inside the settled band."},
    {"metric": "usdt_supply", "current_value": usdt["supply"], "previous_value": usdt["prev"], "method": "rule_based", "severity": "low", "change_pct": usdt["pct"],
     "description": f"USDT {usdt['pct']:+.2f}% and USDC {usdc['pct']:+.2f}%: bridged dollar supply kept contracting through the restart."},
    {"metric": "hatom_egld_market_balance", "current_value": df["egld_mm_balance"], "previous_value": df["egld_mm_prev_balance"], "method": "rule_based", "severity": "low",
     "change_pct": 100 * EMM_D / df["egld_mm_prev_balance"],
     "description": f"Hatom's EGLD market +{f(EMM_D)} EGLD after the restart, with HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.2f}%: collateral added, no liquidation wave."},
    {"metric": "exploit_wallet_post_restart_fanout", "current_value": ATTP.get("distinct_receivers", 0), "previous_value": 12, "method": "rule_based", "severity": "low",
     "description": f"The Sep 19 exploit wallet sent {f(ATTP.get('out_egld',0),2)} EGLD in 0.1066 EGLD pieces to {ATTP.get('distinct_receivers',0)} wallets on Sep 27 (19:58-20:05 UTC)."},
]

R["trend_indicators"] = {
    "accelerating_exchange_outflows": [],
    "validator_movements": {"providers_joining": 0, "providers_leaving": 0, "net_provider_change": 0, "notable_joiners": [], "notable_leavers": []},
    "token_supply_events": [
        {"identifier": "USDT-f8c08c", "name": "USDT", "event": "burn", "supply_previous": str(int(usdt["prev"])), "supply_current": str(int(usdt["supply"])),
         "change_pct": usdt["pct"], "description": f"{f(usdt['prev']-usdt['supply'])} USDT redeemed; a seventh contraction in eight weeks."},
        {"identifier": "USDC-c76f1f", "name": "WrappedUSDC", "event": "burn", "supply_previous": str(int(usdc["prev"])), "supply_current": str(int(usdc["supply"])),
         "change_pct": usdc["pct"], "description": f"{f(usdc['prev']-usdc['supply'])} USDC redeemed."},
        {"identifier": "HEGLD-d61095", "name": "HEGLD", "event": "mint", "supply_previous": str(int(float(HT['HEGLD-d61095']['prev_supply']))), "supply_current": str(int(float(HT['HEGLD-d61095']['supply']))),
         "change_pct": HT["HEGLD-d61095"]["supply_pct"], "description": "EGLD deposited into Hatom after the restart."},
        {"identifier": "VOXEGLD-5872e5", "name": "VoxEGLD", "event": "mint", "supply_previous": str(em["VOXEGLD-5872e5"]["prev"]), "supply_current": str(em["VOXEGLD-5872e5"]["supply"]),
         "change_pct": em["VOXEGLD-5872e5"]["pct"] or 0.0, "description": "Emerging LSD, fourth week of growth."}],
    "consecutive_streaks": [
        {"metric": "usdt_supply", "direction": "down", "weeks": 3, "cumulative_change_pct": 100 * (usdt["supply"] - 463905) / 463905,
         "interpretation": f"463,905 / 452,585 / {f(usdt['supply'])}: bridged dollars keep leaving MultiversX."},
        {"metric": "total_delegators", "direction": "flat", "weeks": 15, "cumulative_change_pct": -1.0, "interpretation": f"{sk['users_delta']:+,} to {f(sk['users'])}. Still the base rate, even through a halt and a rollback."},
        {"metric": "provider_operator_fee_selling", "direction": "flat", "weeks": 15, "cumulative_change_pct": 0.0, "interpretation": "Fifteen runs with zero exchange destinations from sampled operator wallets."},
        {"metric": "identifiable_bid_absorbed_egld_7d", "direction": "flat", "weeks": 7, "cumulative_change_pct": 0.0, "interpretation": "Zero for a seventh week; retired instrument."}],
    "regime_shifts": [
        {"metric": "chain_liveness", "before_value": 0.0, "after_value": 1.0,
         "description": "RESTORED. Live since Sep 24 15:30 after a rollback to Sep 19 06:37:45. The regime question has moved to the exchange rails: the chain is open, the venues are not."},
        {"metric": "exchange_rail_state", "before_value": 1.0, "after_value": 0.0,
         "description": "CANDIDATE, not promoted: zero exchange EGLD deposits or withdrawals in the first 3.7 live days. A closed rail is a state, like the halt; it becomes a regime question only if it persists and venues delist."},
        {"metric": "reward_compound_pct", "before_value": 62.68, "after_value": cvc["compound_pct_of_reward_decisions"],
         "description": "Candidate only; the two-week rule applies (last sub-55% reading reverted the next week)."}]}

R["watch_list"] = [
    {"item": "EXCHANGE RAILS - zero EGLD deposits/withdrawals since restart", "weeks_on_list": 1,
     "reason": f"{EX_SENDS} send across {len(XPOST)} tracked wallets in {LIVE_DAYS:.1f} live days (a replay). The first post-reopen week resolves delivery-price-relevance-2 and the Korea-premium test."},
    {"item": "KOREA PREMIUM", "weeks_on_list": 1,
     "reason": f"Upbit {PREM:.0f}% above Binance, {UP_SHARE:.0f}% of global volume, deposits closed. PRE-COMMITTED (korea-premium-arbitrage)."},
    {"item": "STAKING EXIT PACE AFTER RESTART", "weeks_on_list": 1,
     "reason": f"{f(sk['undelegated_week'])} EGLD unDelegated in {LIVE_DAYS:.1f} live days (~{f(UNDEL_PACE)}/week). The unbonded EGLD matures into closed rails. PRE-COMMITTED (post-restart-exit-wave)."},
    {"item": "UNKNOWN WHALE I AND erd1a6lte0 - probable exchange hot wallets", "weeks_on_list": 2,
     "reason": "Census not evaluable while rails are closed (2 and 1 spam inbound). Test deadline extended by the rail closure."},
    {"item": "OTC PIPELINE - idle behind closed rails", "weeks_on_list": 27,
     "reason": f"Gross {f(otc['gross_out'])} EGLD all week; desks {f(otc['desk_bal'])}. Wave #4 closed at 467,107 one-way."},
    {"item": "EXPLOIT WALLET AND POISONING RING", "weeks_on_list": 2,
     "reason": f"Exploit wallet sprayed its last {f(ATTP.get('out_egld',0),1)} EGLD to {ATTP.get('distinct_receivers',0)} wallets on Sep 27; poisoning operator {PR['operator_out_7d']} dust txs; lookalikes 0 hits."},
    {"item": "INCIDENT REPORTS - MultiversX technical report and Hatom MEX report", "weeks_on_list": 2,
     "reason": "Neither was read this run; reconcile against the chain reconstruction when published."},
    {"item": "COMPOUND RATE", "weeks_on_list": 1,
     "reason": f"{cvc['compound_pct_of_reward_decisions']:.2f}%, second sub-55% reading in three weeks."},
]

# ---------------------------------------------------------------------------
prior = {t["id"]: t for t in r26["pre_committed_tests"]}
tests = [t for t in r26["pre_committed_tests"] if t["status"] == "resolved"]


def resolve(tid, outcome, measured, resolution):
    t = dict(prior[tid]); t.update({"status": "resolved", "outcome": outcome, "resolved_in_run": 27, "measured_value": measured, "resolution": resolution}); return t


tests.append(resolve("halt-recovery-clean", "against",
    f"invalid balances {f(HR['invalid_total_egld'],2)} EGLD across attacker, contract and 12 fan-out wallets (bar < 1,000); desks {f(legit['UPbit OTC Desk']['balance_egld']+legit['OTC Distribution Wallet']['balance_egld'])} vs 46,637 (0.0%); Binance custody {f(legit['Binance Staking custody']['balance_egld'])} vs 3,493,535 (0.0%); Hatom EGLD market {f(legit['Hatom EGLD money market']['balance_egld'])} vs 112,295 ({100*(legit['Hatom EGLD money market']['balance_egld']-112294.58)/112294.58:+.1f}%)",
    "The 'broader rollback than stated' branch fires, against the claim of a targeted recovery that preserves finalized history. The invalid balances are gone, but they were removed by rolling every shard back to Sep 19 06:37:45, and 1,597 non-exploit transactions from the rolled-back hour were never re-executed. "
    "The data contradicts one part of the branch as written (run #24 rule): the only legitimate balance that moved by more than 1%, Hatom's EGLD market, moved through ordinary post-restart deposits, not through the rollback. The desks and Binance custody match to the EGLD. "
    "The branch fires on the recovery method, which the test's threshold was a proxy for; the threshold alone would have read it for the wrong reason."))
tests.append(resolve("staked-ratio-floor", "against",
    f"staked ratio {100*M['sr']:.2f}% at run #27 (band 46.30-46.80%)",
    f"The 'settled lower' branch fires, against 'exits continuing'. Caveat recorded: the ratio was frozen for five of the seven days, and unDelegations ran at a ~{f(UNDEL_PACE)}/week pace in the live days. The pace is registered separately (post-restart-exit-wave) rather than stretched into this test."))
tests.append(resolve("fourth-deregistration", "against",
    "week 4 of 4 on the TRANSITION basis: zero transitions; join on contract address, 100% match",
    "The 'none within 4 weeks' branch fires: the three known deregistrations are idiosyncratic business decisions, not a trend in the validator set."))
t = dict(prior["unknown-whale-i-is-exchange"]); t.update({"status": "open", "measured_value": f"run #27: {CEN['Unknown Whale I']['inbound_txs']} inbound txs from {CEN['Unknown Whale I']['distinct_senders']} senders in 7 days, both token-spam; 0 outbound. NOT EVALUABLE: exchange rails closed. Deadline moves to the second full week after deposits reopen.", "resolution": None}); tests.append(t)
t = dict(prior["delivery-price-relevance-2"]); t.update({"status": "open", "measured_value": f"run #27: rails still closed; delivery {f(otc['net_one_way'])} (not evaluable)", "resolution": None}); tests.append(t)


def new(tid, claim, threshold, branches, measured):
    return {"id": tid, "registered_in_run": 27, "claim": claim, "threshold": threshold, "branches": branches,
            "status": "open", "outcome": None, "resolved_in_run": None, "measured_value": measured, "resolution": None}


tests += [
    new("korea-premium-arbitrage", "The Upbit premium is blocked arbitrage, not Korean demand: it closes once EGLD deposits reopen.",
        f"first run in which UPbit's hot wallet receives EGLD deposits from >= 20 distinct senders in the window: Upbit-Binance premium < 5% = blocked arbitrage; 5-15% = no conclusion, re-measure next run; > 15% = premium is demand, not blocked arbitrage; deposits still closed at run #29 = not evaluable, retire",
        [{"condition": "deposits open and premium < 5%", "reading": "blocked arbitrage"},
         {"condition": "deposits open and premium 5-15%", "reading": "no conclusion, re-measure"},
         {"condition": "deposits open and premium > 15%", "reading": "Korean demand, not arbitrage"},
         {"condition": "deposits still closed at run #29", "reading": "not evaluable, retire"}],
        f"premium {PREM:.1f}% (Upbit ${up['converted_last']['usd']:.2f} vs Binance ${bn['converted_last']['usd']:.2f}); UPbit hot wallet 0 EGLD deposits since restart"),
    new("post-restart-exit-wave", "The restart triggered an exit wave from delegation, not a one-off burst.",
        "unDelegated EGLD in run #28's full 7-day live window: > 150,000 = exit wave continuing; 90,000-150,000 = elevated, no conclusion; < 90,000 = back to the pre-halt 73-84K range, a one-off burst",
        [{"condition": "> 150,000 EGLD unDelegated", "reading": "exit wave"},
         {"condition": "90,000-150,000", "reading": "elevated, no conclusion"},
         {"condition": "< 90,000", "reading": "one-off burst"}],
        f"run #27: {f(sk['undelegated_week'])} EGLD in {LIVE_DAYS:.1f} live days (~{f(UNDEL_PACE)}/week pace), {sk['undelegate_callers']} wallets"),
]
resolved = [t for t in tests if t.get("resolved_in_run") == 27]
as_pred = sum(1 for t in resolved if t["outcome"] == "as_predicted")
R["pre_committed_tests"] = tests

# ---------------------------------------------------------------------------
R["meta_learning"] = {
    "run_number": 27,
    "endpoints_that_worked": status["ok"],
    "endpoints_that_failed": [
        "NONE with data missing. 47 HTTP 429s in the main pass (provider scan, protocol counters, JEX routers) were all recovered by the follow-up and a targeted re-query."],
    "api_quirks": [
        "AFTER A ROLLBACK THE API INDEX STILL SERVES ORPHANED TRANSACTIONS as success in account histories (the Sep 19 exploit deposits), while balances reflect the rolled-back state. Any tx-scan window that covers a rollback must be checked against block hashes or balances.",
        "HUB-TRACE VENUE RESOLUTION DEPENDS ON LABEL TEXT: venue_of() treats any label containing 'Whale' as a venue, so router labels written in runs #24-#25 ('OTC Desk->Unknown Whale I (active) Router') became pseudo-venues and cut wave #4's measured circularity by 152K on unchanged transactions.",
        "A closed exchange rail reads as a perfect zero: every tracked exchange balance equal to the EGLD. Distinguish 'no flow' from 'flat' with a send/receive count since the event."],
    "data_gaps": [
        "Only 3.7 live days in the 7-day window; weekly series get a short, closed-book observation.",
        "MultiversX's technical report and Hatom's MEX incident report were not read this run.",
        "Unknown Whale I census not evaluable while exchange rails are closed.",
        "Hatom UTK Money Market and OneDex Launchpad still fail bech32 validation (open since run #18)."],
    "key_findings": [
        f"The chain restarted on a rollback to Sep 19 06:37:45; exploit balances are {f(HR['invalid_total_egld'],2)} EGLD; halt-recovery-clean resolves 'broader rollback' (against).",
        f"No tracked exchange wallet has moved EGLD since the restart ({EX_SENDS} replayed send across {len(XPOST)} wallets); all exchange and OTC flow readings are closed-book.",
        f"EGLD +{pc:.2f}% vs BTC {M['btc_wow']:+.2f}% with a {PREM:.0f}% Upbit premium on {UP_SHARE:.0f}% of global volume.",
        f"UnDelegations ran at ~{f(UNDEL_PACE)}/week after the restart, while the staked ratio sat at {100*M['sr']:.2f}% (staked-ratio-floor: settled lower).",
        f"Hatom's EGLD market added {f(EMM_D)} EGLD with no liquidation wave; stablecoins kept burning (USDT {usdt['pct']:+.2f}%).",
        "Wave #4 closes at 467,107 EGLD one-way; a re-net with drifted labels would have shown 618,762."],
    "action_items_from_previous": len(r26["meta_learning"]["recommendations_for_next_run"]),
    "action_items_completed_detail": [
        "CHECK LIVENESS AT COLLECTOR START - done: the collector reads the latest block per shard before anything else and records the lags (all < 2 s).",
        "RESOLVE halt-recovery-clean - done: attacker, contract and all 12 fan-out balances read; desks, custody and Hatom compared; resolved against (broader rollback).",
        "LABEL UNKNOWN WHALE I AND erd1a6lte0 - attempted: deep-paged 7-day inbound census built into the collector; not evaluable while exchange rails are closed (2 and 1 spam inbound).",
        "ADD A LIVENESS GATE TO THE COLLECTOR - done: liveness_ok flag, printed warning when any shard lags > 1 h.",
        "READ THE INCIDENT REPORTS - not done this run (deferred).",
        "RE-READ THE ORDER BOOK once transfers reopen - deferred: transfers have not reopened; this run's reading is flagged closed-book and kept out of the baseline.",
        "WATCH THE POISONING LOOKALIKES - done: 0 inbound above dust on either lookalike; operator sent 181 dust txs this week.",
        "(unplanned) EXCHANGE RAIL CHECK: send/receive counts since restart for 20 tracked exchange wallets, which is what separated 'closed' from 'flat'."],
    "methodology_changes": [
        "SEPARATE 'NO FLOW' FROM 'FLAT'. After any network event, count exchange sends/receives since the event before narrating a flat exchange aggregate; a closed rail gives a perfect zero.",
        "CLOSED-BOOK READINGS STAY OUT OF BASELINES. Exchange flow, OTC throughput, order book and CEX volume read with rails closed are recorded but not appended.",
        "FREEZE THE LABEL SET FOR RE-NETTING A CLOSED WAVE; the resolver's venue test is label-text-based and drifts as router labels are added.",
        "REGISTER PACE-BASED TESTS ON A FULL LIVE WINDOW, not on a short window extrapolated."],
    "new_addresses_discovered_detail": [],
    "action_items_completed": 5,
    "new_addresses_discovered": 0,
    "most_valuable_insight": (
        "Telling a closed market from a quiet one. Every exchange balance matched last week to the EGLD, which a flow table presents as a perfectly flat week. "
        f"Counting sends since the restart ({EX_SENDS}, a replay) showed that nothing could move. That reframes everything downstream: the {EGLD_VS_BTC:+.1f}pp outperformance and the {PREM:.0f}% Upbit premium are prices set by buyers who cannot receive supply, and the {f(sk['undelegated_week'])} EGLD of fresh unDelegations is supply waiting for the rails to open."),
    "top_recommendation": "WHEN EXCHANGE RAILS REOPEN, MEASURE THE FIRST WEEK HARD: per-venue deposit/withdrawal counts and values from the first reopened block, the Upbit premium hourly, desk activity, and where the post-restart unbonded EGLD goes. That week resolves three open tests at once.",
    "recommendations_for_next_run": [
        "COUNT EXCHANGE SENDS/RECEIVES SINCE RESTART FIRST; if rails are still closed, keep every exchange-side metric out of the baselines again.",
        "If rails reopened: resolve korea-premium-arbitrage and delivery-price-relevance-2, and re-run the Unknown Whale I census.",
        "RESOLVE post-restart-exit-wave on a full 7-day live window; trace where matured unbonding EGLD goes (exchange once open vs held).",
        "FIX venue_of(): resolve venues on category == exchange plus an explicit venue map, not on 'Whale' in the label text; re-net waves only with a frozen label set.",
        "READ MultiversX's technical post-mortem and Hatom's MEX report; reconcile with the chain reconstruction.",
        "Add a GLOBAL rate-limit budget to the collector (47 HTTP 429s this run, all in the provider scan and protocol counters)."],
    "dashboard_feature_suggestions": [
        {"title": "Exchange rail status board",
         "motivation": f"This run's key finding is that no tracked exchange wallet moved EGLD in {LIVE_DAYS:.1f} live days after the restart. On the dashboard that renders as a flat exchange-flow chart and a zero, which reads as a calm week rather than a suspended market.",
         "suggested_visualization": "a per-venue row of status chips (open / closed / partial) with last on-chain EGLD deposit and withdrawal timestamps and a days-since counter, placed above the exchange-flow panel",
         "data_already_available": True, "data_source": "whale_intelligence.exchange_flows.rail_status plus a per-wallet since-restart count (collector field exchange_reopen)", "priority": "high"},
        {"title": "Korea premium tracker",
         "motivation": f"EGLD outperformed BTC by {EGLD_VS_BTC:.1f}pp while Upbit, {UP_SHARE:.0f}% of global volume, traded {PREM:.0f}% above Binance with deposits closed. The single-week price number cannot show that the move lives in one closed venue.",
         "suggested_visualization": "hourly line of Upbit vs global EGLD price with the premium as a shaded band, and rail-closed periods shaded on the time axis",
         "data_already_available": False, "data_source": "Upbit public candles API (hourly KRW-EGLD) + CoinGecko hourly; persisted in data/collected/special/2026-09-24-chain-restart.json for Sep 19-24", "priority": "medium"}],
    "dashboard_suggestions_followup": [
        {"title": "Chain liveness and incident banner", "status": "pending",
         "note": "Not built. The report now carries network_health.liveness and whale_intelligence.halt_recovery; the banner can read those. Still the highest-value missing panel after a halt."},
        {"title": "Exploit fan-out graph", "status": "deprioritized",
         "note": "The rollback erased the fan-out from canonical state; the graph would now be a historical record only."},
        {"title": "Feed-side attribution - who fills the desks, not just who they deliver to", "status": "pending",
         "note": "Blocked on the venue_of() label fix (this run found label drift in the resolver) and on the rails reopening."},
        {"title": "Demand-instrument scorecard", "status": "deprioritized",
         "note": "Closed-book week again: the order book and exchange tiles would show readings that are excluded from baselines."}],
    "withdrawn_claims": [
        {"claim": "MultiversX's recovery would be a targeted recovery that preserves finalized history (the framing the run #26 report relayed and tested).",
         "asserted_in_runs": [26], "withdrawn_in_run": 27,
         "reason": "The chain was rolled back to Sep 19 06:37:45 on every shard, rewriting 64 minutes of finalized blocks; 1,597 non-exploit transactions from that hour were not re-executed.",
         "replacement": "A rollback-and-replay recovery. Exploit balances are gone, and pre-exploit balances of the desks and Binance custody are intact to the EGLD."}],
}

rep = {}
rep.update(R)
order = ["metadata", "executive_summary", "network_health", "whale_intelligence", "staking_intelligence", "token_activity",
         "defi_activity", "anomalies", "trend_indicators", "watch_list", "meta_learning", "pre_committed_tests"]
rep = {k: rep[k] for k in order}
json.dump(rep, open(f"{REPO}/reports/{RD}.json", "w"), indent=1, default=str)
print("report written", len(json.dumps(rep, default=str)), "bytes")
print(f"tests resolved this run {len(resolved)}, as_predicted {as_pred}, open {sum(1 for t in tests if t['status']=='open')}")
print("PREM", round(PREM, 1), "UP_SHARE", round(UP_SHARE, 1), "LIVE_DAYS", round(LIVE_DAYS, 2), "EX_SENDS", EX_SENDS)
