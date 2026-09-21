#!/usr/bin/env python3
"""Run #26 stage 2: assemble reports/2026-09-21.json from derived.json + snapshot.

The week's defining event is the 2026-09-19 VM-level exploit and the chain halt
that followed at 07:41 UTC. Every flow window below therefore ends at the halt
(Sep 14 00:00 -> Sep 19 07:41, 5.3 days), and every balance delta is reported
NET of incident-attributable EGLD (raw figures kept alongside).
"""
import json, copy
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD = "2026-09-21"
O = json.load(open("/tmp/run26w/derived.json"))
D = json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev = json.load(open("/tmp/run26w/previous_run25.json"))
status = json.load(open("/tmp/run26w/status.json"))
beh = json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
r25 = json.load(open(f"{REPO}/reports/2026-09-14.json"))
disc = json.load(open(f"{REPO}/data/collected/liquid_staking_discovery_{RD}.json"))


def f(x, d=0):
    try:
        return f"{x:,.{d}f}"
    except Exception:
        return str(x)


def V(d_, k, default=0.0):
    return (d_ or {}).get(k, default)


def iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def hm(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%b %d %H:%M")


M = O["macro"]; otc = O["otc"]; wave = otc["wave"]; ex = O["exch"]; cust = O["custody"]
bid = O["bid"]; br = O["breadth"]; sk = O["staking"]; tk = O["tokens"]; xx = O["xexchange"]
df = O["defi"]; z = O["z"]; ub = O["unbond"]; absb = O["absorbers"]; zsc = O["zero_stake_cohort"]
HOT = O["hot_to_pipe"]; FEED = O["feeders_in"]; BOOK = O["orderbook"]; FB = O["feeder_backtrace"]
INC = O["incident"]; MR = O["mex_recovery"]; WD = O["withdraw_decoded"] or {}; PZ = O["address_poisoning"] or {}
econ = D["economics"]; st = D["stats"]; pecon = prev["economics"]; pact = prev["activity"]
price = M["price"]; pc = M["price_chg"]
cvc = beh["aggregates"]["compound_vs_claim_at_function_level"]
ag = beh["aggregates"]; fates = ag["delegator_fates_by_tier"]
HALT = D["chain_halt_incident"]
HALT_TS = max(v["timestamp"] for v in HALT["last_blocks"].values())
HALT_TS0 = min(v["timestamp"] for v in HALT["last_blocks"].values())
WIN_START = D["_period"]["window_start_ts"]
WIN_DAYS = (HALT_TS - WIN_START) / 86400
ATT = HALT["attacker"]; ROUNDS = [r for r in ATT["rounds"] if r["fn"] == "deposit"]
FAN = HALT["fanout"]; FANBY = HALT["fanout_by_destination"]
INC_EX = INC["inc_by_entity"]; INC_EX_TOT = sum(INC_EX.values())
UNMOVED = FANBY.get("(unmoved in fresh wallet)", 0)
WHALE_I = FANBY.get("Unknown Whale I (active)", 0)
A6 = "erd1a6lte0wqwwdjtt0nvv62c6pacltznzgq93gjxu6el44cx6lqx3fsu48u4l"
A6_AMT = FANBY.get(A6, 0)
MINTED_HELD = INC["attacker_balance"] + INC["contract_balance"]
MINTED_TOTAL = MINTED_HELD + HALT["fanout_total_egld"]
FUND = sum(x["egld"] for x in ATT["funding"])
cg_e = HALT["cg_egld_hourly_7d"]["prices"]; cg_b = HALT["cg_btc_hourly_7d"]["prices"]
pre_halt_px = [p for p in cg_e if p[0] <= HALT_TS * 1000][-1][1]
post = [p for p in cg_e if p[0] > HALT_TS * 1000]
post_lo = min(post, key=lambda p: p[1]); post_last = post[-1][1]
btc_pre = [p for p in cg_b if p[0] <= HALT_TS * 1000][-1][1]; btc_last = cg_b[-1][1]
EGLD_VS_BTC = pc - M["btc_wow"]
RES_CALLS = [c for c in MR["owner_calls"] if c["fn"] == "resume"]
RESUME_TS = RES_CALLS[0]["ts"] if RES_CALLS else None
WL_TS = [c["ts"] for c in MR["owner_calls"] if c["fn"] == "addToPauseWhitelist"]
REC_C = "erd1qqqqqqqqqqqqqpgqwmq40hvu7j88gqc7935prc0r96mdhs3m78sszpu2uj"
# recovery contract flows (enrichment done in this run; see methodology run #26)
RECOVERY = {"contract": REC_C, "deployer": "erd1cc2yw3reulhshp3x73q2wye0pq8f4a3xz3pt7xj79phv9wm978ssu99pvt (Hatom deployer)",
            "deployed_utc": "2026-09-15 15:38", "rounds": 89, "window_utc": "2026-09-15 19:15-21:11",
            "hmex_redeemed": 13043099562331.55, "mex_redeemed": 270174026280.96,
            "mex_sold_mex_wegld": 222033688205.27, "wegld_received": 75792.02,
            "mex_sold_mex_ush": 40157156303.69, "ush_received": 49917.87,
            "mex_sold_mex_usdc": 7983181771.99, "usdc_received": 9652.42,
            "liquidate_borrow_calls": 53}
HT = df["h_tokens"]
zz = lambda k: z[k].get("z")

R = {}
# ---------------------------------------------------------------------------
R["metadata"] = {
    "report_date": RD, "period_start": "2026-09-14", "period_end": RD,
    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "egld_price_usd": price, "btc_price_usd": M["btc"], "eth_price_usd": M["eth"],
    "run_number": 26,
    "data_sources_ok": status["ok"] + [
        "followup pass: 377 withdraw calls decoded from smart-contract results, address-poisoning scan, dashboard series (0 errors)",
        "chain-halt evidence: last block per shard, attacker transaction history, 12-wallet fan-out, CoinGecko hourly EGLD and BTC",
        "delegator reward behaviour: 8 of 8 providers sampled, run AFTER the collector (run #25 rule)",
        "liquid-staking sweep seeded from last week's finds: all six known protocols returned"],
    "data_sources_failed": status["failed"],
    "data_sources_recovered": [
        f"THE CHAIN IS HALTED. No block on any shard since {iso(HALT_TS0)}-{iso(HALT_TS)[11:]}. The API serves the halted state, so every 7-day window in this report is really {WIN_DAYS:.1f} days (Sep 14 00:00 to the halt), and every balance delta is reported net of incident-attributable EGLD",
        "xExchange 24h volume and every protocol's 24h transfer count read 0: the 24 hours before the snapshot contain no blocks. These are not endpoint failures; they are not evaluable this week, and 7-day counts are used where they exist",
        "SWTAO-356a25: price null through the main pass and 4 isolated retries; recovered via the run #11 accumulator ratio against WTAO-4f5363 (marked estimated). Supply remains the primary signal",
        "SALSA and VestaX were missed by last week's sweep; this week's sweep seeds from previous finds and returned both"]}

# ---------------------------------------------------------------------------
R["executive_summary"] = [
    {"category": "network", "severity": "critical", "finding":
     f"THE MULTIVERSX CHAIN HAS BEEN HALTED SINCE {hm(HALT_TS0)}-{iso(HALT_TS)[11:16]} UTC AFTER A VM-LEVEL EXPLOIT MINTED EGLD THAT DID NOT EXIST. "
     f"One wallet (erd1kwvkch79...rvvjd2), funded on Sep 16 with {f(FUND,1)} EGLD from MEXC and Bybit withdrawals and one other wallet, deployed a contract at 06:34 UTC and ran {len(ROUNDS)} deposit-then-compound rounds with the deposit doubling each time (0.048, 0.095, 0.19 ... EGLD). "
     f"It ended holding {f(INC['attacker_balance']/1e6,1)}M EGLD, its contract {f(INC['contract_balance']/1e6,1)}M, about {MINTED_HELD/econ['totalSupply']:.1f}x the {f(econ['totalSupply']/1e6,1)}M total supply. "
     f"Between 07:24 and 07:27 it sent {f(HALT['fanout_total_egld']/1e6,2)}M EGLD to 12 fresh wallets; {f(INC_EX_TOT/1e6,2)}M reached Binance.com ({f(V(INC_EX,'Binance'))}), KuCoin ({f(V(INC_EX,'KuCoin'))}) and MEXC ({f(V(INC_EX,'MEXC'))}) within two hops. The last block landed about ten minutes later. "
     f"MultiversX calls it an attempted exploit of a VM-level atomicity issue that caused invalid state changes; progression is paused, a fix is being validated on a shadow fork, attacker accounts are frozen with exchanges, and a targeted recovery of only the incident-related changes is being evaluated. "
     f"EGLD went from ${pre_halt_px:.2f} at the halt to ${post_lo[1]:.2f} on Sep 20 and is back at ${post_last:.2f}; Upbit has put EGLD on a trading-caution list."},
    {"category": "whale", "severity": "high", "finding":
     f"ALL FLOW FIGURES THIS WEEK ARE NET OF THE EXPLOIT. The raw exchange balance change is {ex['net_raw']:+,.0f} EGLD, ten times the largest weekly move in tracking (489,174 in the Apr 13 report). {f(INC_EX_TOT)} of it is minted EGLD deposited at three exchanges in three minutes; net of that the complex moved {ex['net']:+,.0f}. "
     f"The whale tiers, wallet changes and large-transaction list are computed the same way: incident wallets excluded, incident deposits subtracted. Two more destinations carry minted EGLD: {f(A6_AMT)} to an unlabelled high-nonce wallet (erd1a6lte0...u48u4l, nonce 2,131, many small retail-sized deposits, so probably an exchange hot wallet), and {f(WHALE_I)} to the wallet this model has called Unknown Whale I since run #19. "
     f"An attacker routing stolen funds to it is strong evidence that Unknown Whale I is an exchange deposit wallet, not an OTC operator's inventory. {f(UNMOVED)} EGLD sits unmoved in three fresh wallets."},
    {"category": "whale", "severity": "high", "finding":
     f"THE OTC PIPELINE WAS ALREADY QUIET BEFORE THE HALT. In the {WIN_DAYS:.1f} days before block production stopped, the desks moved {f(otc['gross_out'])} EGLD gross and delivered {f(otc['net_one_way'])} one-way, against 401,353 last week: {otc['circ_pct']:.0f}% of the flow went back to the venue that supplied it. "
     f"UPbit fed only {f(otc['upbit_feed'])} (from 372,000) and took 80,000 back. Wave #4, netted as one window from Sep 7, delivered {f(wave['net_one_way'])}, and the two weekly frames sum to {f(wave['sum_weekly'])}, so there was no straddle. "
     f"Since the halt no desk can move anything. The pipeline is stopped by construction, and no pre-halt reading can say whether wave #4 was ending or pausing."},
    {"category": "defi", "severity": "high", "finding":
     f"HATOM'S MEX INCIDENT CLOSED BEFORE THE HALT, AND THE CHAIN SHOWS HOW. A contract deployed by Hatom's deployer on Sep 15 redeemed {f(RECOVERY['hmex_redeemed']/1e12,2)}T HMEX (the seized collateral) for {f(RECOVERY['mex_redeemed']/1e9,0)}B MEX and sold it in {RECOVERY['rounds']} rounds between 19:15 and 21:11 UTC: {f(RECOVERY['mex_sold_mex_wegld']/1e9,0)}B MEX into MEX/WEGLD for {f(RECOVERY['wegld_received'])} WEGLD, plus smaller sales into MEX/USH and MEX/USDC. "
     f"It did so while those pools were still paused to everyone else: the router owner put the three pairs on a pause whitelist at {hm(WL_TS[0])} and resumed trading at {hm(RESUME_TS)} UTC, one day after Hatom's stated Wednesday. "
     f"Hatom's EGLD money market went {f(df['egld_mm_prev_balance'])} -> {f(df['egld_mm_balance'])} EGLD, which covers the 73,600 EGLD the incident wallet borrowed. HMEX supply fell {abs(HT['HMEX-df6df7']['supply_pct']):.0f}%, and MEX prices at {xx['mex_price']:.2e} from the restored pool, about 1.5x its pre-incident level. No loss or bad debt has been disclosed and Hatom's incident report is still pending."},
    {"category": "staking", "severity": "medium", "finding":
     f"LAST WEEK'S STAKING SCARE DID NOT REPEAT. The compound rate went back to {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} redelegate vs {cvc['claim_count']} claim) from 49.44%, so the fall below 50% was a one-week reaction and the regime-switch claim is against. "
     f"The staked ratio held at {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp), inside the settled band of the run #27 test. For the first time the model measured what withdraw calls return: {f(WD.get('egld_returned_total',0))} EGLD across {WD.get('calls',0)} calls in the pre-halt window, against {f(sk['undelegated_week'])} EGLD of new unDelegations from {sk['undelegate_callers']} wallets. Exits are completing faster than new ones start. Delegation TVL rose {sk['delta_locked']:+,.0f}."},
    {"category": "anomaly", "severity": "medium", "finding":
     f"SOMEONE IS ADDRESS-POISONING THE OTC PIPELINE. Two wallets built to share the first and last characters of the desks (erd1z7wy...ppm63r mimics the OTC Distribution Wallet erd1z7fn...nm63r; erd1v6k4...ryxnk5 mimics the UPbit OTC Desk erd1v6x9...hcxnk5) sent {sum(v['dust_txs_30d'] for v in PZ.values())} dust transfers of 0.0001 EGLD to the pipeline's routers in 30 days, {max(v['distinct_targets_30d'] for v in PZ.values())} targets each. "
     "The aim is for a router operator to copy the lookalike from their history and send a chunk to it. Neither wallet has received anything above 0.01 EGLD, so no transfer has been misdirected yet."},
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
                 "avg_daily_transactions": int((st["transactions"] - pact["total_transactions"]) / WIN_DAYS)},
    "deltas": {"price_change_pct": pc,
               "market_cap_change_pct": 100 * (econ["marketCap"] - pecon["market_cap_usd"]) / pecon["market_cap_usd"],
               "staked_ratio_change_pp": 100 * (M["sr"] - M["sr_prev"]),
               "apr_change_pp": 100 * (econ["apr"] - pecon["staking_apr"]),
               "accounts_added": st["accounts"] - pact["total_accounts"],
               "transactions_added": st["transactions"] - pact["total_transactions"],
               "supply_added": econ["totalSupply"] - pecon["total_supply"],
               "staked_egld_added": M["staked_chg"], "epoch_advanced": st["epoch"] - pact["epoch"],
               "btc_correlation_note": f"BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%, EGLD {pc:+.2f}%: EGLD lagged BTC by {abs(EGLD_VS_BTC):.1f}pp in a week where its chain stopped. From the halt to the snapshot EGLD went ${pre_halt_px:.2f} -> ${post_last:.2f} ({100*(post_last-pre_halt_px)/pre_halt_px:+.1f}%) and BTC {100*(btc_last-btc_pre)/btc_pre:+.1f}%."},
    "analysis": (
        f"THE CHAIN STOPPED. The last block on shard 0 is timestamped {iso(HALT['last_blocks']['0']['timestamp'])}, shard 1 {iso(HALT['last_blocks']['1']['timestamp'])[11:]}, shard 2 {iso(HALT['last_blocks']['2']['timestamp'])[11:]} and the metachain {iso(HALT['last_blocks']['4294967295']['timestamp'])[11:]}. The snapshot was taken 55 hours later and no shard had advanced. "
        f"The epoch counter reads {st['epoch']} ({st['epoch']-pact['epoch']:+d} on the week) and the chain processed {f(st['transactions']-pact['total_transactions'])} transactions before it stopped, about {f(int((st['transactions']-pact['total_transactions'])/WIN_DAYS))} a day over the {WIN_DAYS:.1f} days it ran.\n\n"
        f"WHAT HAPPENED, FROM THE CHAIN. Wallet erd1kwvkch79...rvvjd2 received {f(FUND,1)} EGLD on Sep 16 (from MEXC and Bybit withdrawal wallets and one other address), then on Sep 19 deployed contract erd1qqqq...ke2kq9 at 06:34 UTC, created an NFT, and began a loop: deposit EGLD into the contract, call compound, move the resulting token to itself, repeat. "
        f"The deposits doubled every round, {len(ROUNDS)} deposit rounds in all. At the end the wallet held {f(INC['attacker_balance'])} EGLD and the contract {f(INC['contract_balance'])}. "
        f"Doubling a 0.05 EGLD stake thirty-odd times gives numbers of that size, which fits MultiversX's description of an atomicity flaw in the VM: the balance produced by a failed or partial step was kept. "
        f"The model reports the flows and leaves the mechanism to MultiversX's technical report.\n\n"
        f"From 07:24 to 07:27 UTC the wallet sent {f(HALT['fanout_total_egld'])} EGLD to 12 fresh addresses, each of which forwarded its whole receipt within minutes: Binance.com {f(V(INC_EX,'Binance'))}, KuCoin {f(V(INC_EX,'KuCoin'))}, MEXC {f(V(INC_EX,'MEXC'))}, the unlabelled wallet erd1a6lte0 {f(A6_AMT)}, and Unknown Whale I {f(WHALE_I)}. Three fresh wallets still hold {f(UNMOVED)}. "
        f"Block production stopped about ten minutes after the last forward. The total supply field on /economics still reads {f(econ['totalSupply'])}, so the protocol's own accounting has not absorbed the minted balances.\n\n"
        f"WHAT MULTIVERSX AND THE EXCHANGES SAID. MultiversX: an actor attempted to exploit a VM-level atomicity issue that caused invalid state changes; network progression is paused; a fix is being validated on a shadow fork and will be deployed in coordination with validators, exchanges and infrastructure partners; a targeted recovery that preserves finalized history and legitimate user state is being evaluated; attacker accounts are identified and frozen with exchanges. "
        "Upbit suspended EGLD deposits and withdrawals on Sep 19 and designated EGLD a trading-caution market on Sep 21 (review through Oct 19-23); Bithumb suspended transfers; Kraken set EGLD to cancel-only. Those points come from press reports of MultiversX's statement and the exchanges' notices, not from the chain.\n\n"
        f"PRICE. EGLD closed the snapshot at ${price:.2f} ({pc:+.2f}% on the week). The hourly series shows the path: ${pre_halt_px:.2f} at the halt, a low of ${post_lo[1]:.2f} on {datetime.fromtimestamp(post_lo[0]/1000,tz=timezone.utc).strftime('%b %d %H:%M')} UTC, then a full recovery to ${post_last:.2f} while BTC rose {100*(btc_last-btc_pre)/btc_pre:+.1f}% from the halt. "
        f"The market is pricing a successful recovery. It is doing so on exchanges whose EGLD deposits and withdrawals are closed, so no new supply can reach the order books and no one can withdraw to self-custody. That is a closed book, and today's price is a price inside it.\n\n"
        f"STAKING, BEFORE THE HALT. Staked EGLD {M['staked_chg']:+,.0f} to {f(econ['staked'])}, ratio {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp). APR {100*econ['apr']:.2f}%. The staked figures are the halted state and include no incident balances: the attacker never staked.")}

# ---------------------------------------------------------------------------
cur_top = {x["address"]: int(x["balance"]) / 1e18 for x in D["top_accounts"]}
prev_top = {x["address"]: x["balance_egld"] for x in prev["top_accounts"]}
INC_IN = INC["inc_in"]; INC_ADDRS = set(INC["inc_addrs"])
cur_adj = {a: v - INC_IN.get(a, 0.0) for a, v in cur_top.items() if a not in INC_ADDRS}


def tier(v):
    if v > 1_000_000: return "mega"
    if v >= 100_000: return "large"
    if v >= 10_000: return "mid"


common = [a for a in cur_adj if a in prev_top and not a.startswith("erd1qqqqqqqqqqqqq")]
fixed = {"mega": [0.0, 0.0], "large": [0.0, 0.0], "mid": [0.0, 0.0]}
for a in common:
    t = tier(prev_top[a])
    if t:
        fixed[t][0] += prev_top[a]; fixed[t][1] += cur_adj[a]
tiers_fixed = {t: {"previous": v[0], "current": v[1], "net_change_egld": v[1] - v[0]} for t, v in fixed.items()}


def ent(n):
    return next((e2 for e2 in ex["entity"] if e2["entity"] == n), {"net_flow_egld": 0, "pct": 0, "wallets_count": 0})


def entity_interp(e):
    n = e["entity"]; v = e["net_flow_egld"]; inc = V(INC_EX, n)
    base = f"{v:+,.0f} net of the exploit"
    if inc:
        base += f" (raw {v+inc:+,.0f}; {f(inc)} EGLD of minted deposits in three minutes on Sep 19, frozen per MultiversX)"
    if n == "Binance":
        return base + f". Staking custody unchanged at {f(cust['balance'])}. Day-sliced, the hot wallet sent {f(HOT['total_egld'])} EGLD into known desk feeders and routers before the halt, down from 218,264 last week and under the 50,000 line for the first time in four weeks (a 5.3-day window)."
    if n == "UPbit":
        return base + f". Fed only {f(otc['upbit_feed'])} to its desk (from 372,000) and took 80,000 back."
    if n == "KuCoin":
        return base + ". The largest single recipient of minted EGLD after Binance: two fresh wallets delivered 921,564 and 899,812 at 07:25."
    if n == "MEXC":
        return base + ". MEXC also funded the attacker's wallet with 2.74 EGLD on Sep 16, which gives MEXC the attacker's withdrawal record."
    if n == "Coinbase":
        return base + ". Two identical withdrawals (100,000 + 14,208) went to two different wallets, one of them Unknown Whale B."
    if n == "Gate.io":
        return base + f". Gate.io was the largest venue on both legs of the desks this week ({f(V(otc['out_by_venue'],'Gate.io'))} received, {f(V(otc['in_by_venue'],'Gate.io'))} fed)."
    return base + "."


INV_SERIES = {**prev["otc_desk_inventory_series"], "run26": round(otc["desk_bal"])}
r25o = r25["whale_intelligence"]["otc_pipeline"]
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
        "direction": "outflow" if ex["net"] < 0 else "inflow",
        "raw_net_change_egld_including_incident": ex["net_raw"],
        "incident_deposits_egld": INC_EX,
        "signal": (f"Net exchange flow {ex['net']:+,.0f} EGLD NET OF THE EXPLOIT. The raw figure is {ex['net_raw']:+,.0f}: {f(INC_EX_TOT)} of minted EGLD reached Binance.com, KuCoin and MEXC between 07:25 and 07:27 UTC on Sep 19, and MultiversX says the attacker accounts are frozen with exchanges. "
                   f"Ex-incident no entity moved more than 25,000 EGLD in either direction: Coinbase {ent('Coinbase')['net_flow_egld']:+,.0f}, UPbit {ent('UPbit')['net_flow_egld']:+,.0f}, Gate.io {ent('Gate.io')['net_flow_egld']:+,.0f}, KuCoin {ent('KuCoin')['net_flow_egld']:+,.0f}, Bybit {ent('Bybit')['net_flow_egld']:+,.0f}, Binance {ent('Binance')['net_flow_egld']:+,.0f}. The balance channel was flat in the {WIN_DAYS:.1f} days before the halt."),
        "by_exchange": [{"exchange": w["exchange"], "change_egld": w["change_egld"], "pct": w["pct"]} for w in ex["per_wallet"]],
        "entity_netting": [{"entity": e2["entity"], "wallets_count": e2["wallets_count"],
                            "net_flow_egld": e2["net_flow_egld"], "interpretation": entity_interp(e2)} for e2 in ex["entity"]]},
    "dormant_activations": [],
    "chain_halt_incident": {
        "halted_since_utc": iso(HALT_TS0), "last_block_by_shard": {k: iso(v["timestamp"]) for k, v in HALT["last_blocks"].items()},
        "attacker_wallet": ATT["address"], "attacker_contract": HALT["contract"]["address"],
        "attacker_funding_egld": FUND, "attacker_funding_sources": ATT["funding"],
        "deposit_compound_rounds": len(ROUNDS),
        "attacker_balance_egld": INC["attacker_balance"], "contract_balance_egld": INC["contract_balance"],
        "fanout_total_egld": HALT["fanout_total_egld"], "fanout_wallets": len(FAN),
        "fanout_by_destination_egld": FANBY, "exchange_deposits_egld": INC_EX,
        "unmoved_in_fresh_wallets_egld": UNMOVED,
        "total_supply_reported_egld": econ["totalSupply"],
        "public_statement": HALT["public_statement"],
        "price_path": {"at_halt_usd": pre_halt_px, "post_halt_low_usd": post_lo[1],
                       "post_halt_low_utc": datetime.fromtimestamp(post_lo[0] / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M"),
                       "at_snapshot_usd": post_last, "btc_change_since_halt_pct": 100 * (btc_last - btc_pre) / btc_pre},
        "method_note": ("Every balance delta in this report subtracts incident-attributable EGLD: the attacker wallet, its contract and the 12 fan-out wallets are excluded from the top-account set, and the amounts they forwarded are subtracted from the receiving wallets. "
                        "Flow windows end at the halt, so the 'week' is 5.3 days.")},
    "otc_pipeline": {
        "gross_outbound_egld_7d": otc["gross_out"], "gross_inbound_egld_7d": otc["gross_in"],
        "circular_egld_7d": otc["circular"], "net_one_way_egld_7d": otc["net_one_way"],
        "circular_share_pct": otc["circ_pct"],
        "desk_balance_egld": otc["desk_bal"], "previous_desk_balance_egld": otc["prev_desk"],
        "upbit_reload_egld": otc["upbit_feed"],
        "venue_netting": [{"venue": v, "desk_to_venue_egld": otc["out_by_venue"].get(v, 0),
                           "venue_to_desk_egld": otc["in_by_venue"].get(v, 0), "net_egld": otc["net_by_venue"][v]}
                          for v in sorted(otc["net_by_venue"], key=lambda k: -abs(otc["net_by_venue"][k]))],
        "gross_series_egld_7d": {**r25o["gross_series_egld_7d"], "run26": otc["gross_out"]},
        "net_one_way_series_egld_7d": {**r25o["net_one_way_series_egld_7d"], "run26": otc["net_one_way"]},
        "desk_inventory_series_egld": INV_SERIES,
        "circularity_series_pct": {**r25o["circularity_series_pct"], "run26": round(otc["circ_pct"], 1)},
        "peak_window_renetted": r25o["peak_window_renetted"],
        "backfilled_windows": r25o.get("backfilled_windows", []) + [
            {"window": "2026-08-17..2026-09-14 (WAVES #3+#4 as one window, run #25)",
             "gross_egld": r25o["wave_window_netting"]["gross_outbound_egld"],
             "circular_egld": r25o["wave_window_netting"]["circular_egld"],
             "net_one_way_egld": r25o["wave_window_netting"]["net_one_way_egld"],
             "circular_share_pct": r25o["wave_window_netting"]["circular_share_pct"],
             "net_by_venue": r25o["wave_window_netting"]["net_by_venue"]}],
        "wave_window_netting": {
            "window": wave["window"] + " (wave #4 feed-to-drain, two weekly frames; the second ends at the Sep 19 halt)",
            "gross_outbound_egld": wave["gross_out"], "gross_inbound_egld": wave["gross_in"],
            "circular_egld": wave["circular"], "circular_share_pct": wave["circ_pct"],
            "net_one_way_egld": wave["net_one_way"], "sum_of_weekly_nets_egld": wave["sum_weekly"],
            "weekly_frame_overstatement_egld": wave["overstate_egld"],
            "weekly_frame_overstatement_pct": wave["overstate_pct"],
            "net_by_venue": wave["net_by_venue"], "outbound_by_venue": wave["out_by_venue"], "inbound_by_venue": wave["in_by_venue"],
            "note": (f"Wave #4 netted as one window from Sep 7 to the halt delivered {f(wave['net_one_way'])} EGLD one-way; the two weekly frames sum to {f(wave['sum_weekly'])}. The frames agree to within {abs(wave['overstate_pct']):.1f}%, so this wave did not straddle the week boundary. "
                     f"UPbit is the only net source ({f(V(wave['net_by_venue'],'UPbit'))}); Binance.com ({f(V(wave['net_by_venue'],'Binance.com'))}) and Bybit ({f(V(wave['net_by_venue'],'Bybit'))}) took most of it.")},
        "feed_by_parent_venue": [{"venue": k, "egld_7d": v} for k, v in sorted(FEED.items(), key=lambda x: -x[1])],
        "feeder_backtrace": FB,
        "address_poisoning": [{"address": a, "mimics": v["note"], "nonce": v["nonce"], "dust_txs_30d": v["dust_txs_30d"],
                               "distinct_targets_30d": v["distinct_targets_30d"],
                               "inbound_above_0_01_egld": len(v["inbound_above_0_01_egld"])} for a, v in PZ.items()],
        "series_note": (f"The quietest pipeline week since run #19, measured over the {WIN_DAYS:.1f} days the chain ran: {f(otc['gross_out'])} gross, {f(otc['net_one_way'])} one-way, {otc['circ_pct']:.0f}% circular. "
                        f"End-of-week desk balance {' -> '.join(f'{k}: {v:,.0f}' for k, v in list(INV_SERIES.items())[-4:])}. The halt stops every desk, so the next reading after restart will say whether wave #4 had finished or only paused.")},
    "demand_instruments": {
        "identifiable_bid_absorbed_egld_7d": 0.0,
        "mega_whale_balance_egld": bid["mega_bal"] or 0.0, "mega_whale_change_egld": bid["mega_delta"],
        "coinbase_routing_balance_egld": bid["cbr_bal"] or 0.0, "coinbase_routing_inflow_egld": 0,
        "coinbase_routing_funder": None, "coinbase_routing_funder_label": "n/a - no inbound this week",
        "weeks_at_zero": 6, "weeks_at_zero_in_last_four": 4, "bid_to_distribution_ratio_pct": 0.0,
        "dex_turnover_ratio_pct": 0.0, "previous_dex_turnover_ratio_pct": bid["prev_turnover"],
        "dex_volume_egld_24h": 0.0, "previous_dex_volume_egld_24h": bid["prev_dexvol_egld"],
        "pool_tvl_egld": bid["pooltvl_egld"], "previous_pool_tvl_egld": bid["prev_pooltvl_egld"],
        "wegld_usdc_volume_usd": 0.0, "wegld_usdc_share_of_volume_pct": 0.0,
        "ex_wegld_usdc_volume_usd": 0.0, "ex_wegld_usdc_volume_egld": 0.0,
        "dex_volume_status": "NOT EVALUABLE - the 24 hours before the snapshot contain no blocks (chain halted Sep 19 07:41 UTC)",
        "absorber_scan": {"terminals_scanned": absb["scanned"],
                          "terminals_retaining_over_half": len(absb["retaining"]),
                          "total_received_from_desks_egld": absb["total_received"],
                          "total_retained_egld": absb["total_balance_held"],
                          "retained_share_pct": 100 * absb["total_balance_held"] / absb["total_received"] if absb["total_received"] else 0,
                          "verdict": f"Fourth week, same answer: {absb['scanned']} desk terminals took {f(absb['total_received'])} EGLD over the wave and hold {f(absb['total_balance_held'])} between them."},
        "withdrawal_breadth": {"distinct_recipients_raw": br["raw_n"], "total_egld_raw": br["raw_egld"],
                               "distinct_recipients_ex_pipeline": br["ex_n"], "total_egld_ex_pipeline": br["ex_egld"],
                               "pipeline_share_pct": br["pipeline_share"], "top_two_share_pct": br["top_two_share_pct"]},
        "withdrawal_breadth_top": br["top"],
        "exchange_orderbook": {
            "source": "CoinGecko exchange tickers with 2% depth, and daily spot volume (third-party). Read AFTER the halt: deposits and withdrawals are closed at most venues",
            "binance": BOOK["binance"], "bybit": BOOK["bybit"], "upbit": BOOK["upbit"],
            "coinbase": BOOK["coinbase"], "gate": BOOK["gate"], "all_venues": BOOK["all"],
            "spot_volume_7d_egld": BOOK["spot_volume_7d_egld"] or 0.0,
            "spot_volume_prior_7d_egld": BOOK["spot_volume_prior_7d_egld"] or 0.0,
            "net_one_way_share_of_spot_volume_pct": 100 * otc["net_one_way"] / BOOK["spot_volume_7d_egld"] if BOOK["spot_volume_7d_egld"] else 0.0,
            "previous_net_one_way_share_of_spot_volume_pct": prev["exchange_orderbook"]["net_one_way_share_of_spot_volume_pct"],
            "binance_bybit_net_delivery_usd_7d": (V(otc["net_by_venue"], "Binance.com") + V(otc["net_by_venue"], "Bybit")) * price,
            "binance_bybit_bid_depth_2pct_usd": BOOK["binance"]["depth_minus2_usd"] + BOOK["bybit"]["depth_minus2_usd"],
            "previous_binance_bybit_bid_depth_2pct_usd": prev["exchange_orderbook"]["binance_bybit_bid_depth_2pct_usd"],
            "venue_depth_wow": {v: {"bid_now": BOOK[v]["depth_minus2_usd"], "bid_prev": prev["exchange_orderbook"][v]["depth_minus2_usd"],
                                    "ask_now": BOOK[v]["depth_plus2_usd"], "ask_prev": prev["exchange_orderbook"][v]["depth_plus2_usd"]}
                                for v in ("binance", "bybit", "upbit", "coinbase", "gate")},
            "delivery_share_series": BOOK["delivery_share_series"], "top_tickers": BOOK["top"]}},
}
bbn = BOOK["binance"]["depth_minus2_usd"] + BOOK["bybit"]["depth_minus2_usd"]; bbp = prev["exchange_orderbook"]["binance_bybit_bid_depth_2pct_usd"]
R["whale_intelligence"]["analysis"] = (
    f"THE EXPLOIT IS IN EVERY RAW BALANCE. The top-account list now starts with the attacker's wallet ({f(INC['attacker_balance'])} EGLD) and contract ({f(INC['contract_balance'])}), followed by three fresh wallets holding {f(UNMOVED)} between them. "
    f"Binance.com's hot wallet reads {f(cust['hot_balance'] + V(INC_IN,'erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets'))} raw, KuCoin {f(cur_top.get('erd1ty4pvmjtl3mnsjvnsxgcpedd08fsn83f05tu0v5j23wnfce9p86snlkdyy',0))}, MEXC {f(cur_top.get('erd1ezp86jwmcp4fmmu2mfqz0438py392z5wp6kzuqsjldgd68nwt89qshfs0y',0))}. "
    "Every figure in this section subtracts what the fan-out delivered to each wallet and excludes the attacker's own addresses. If MultiversX's targeted recovery reverses those balances, the net figures here are the ones that will survive.\n\n"
    f"THE FAN-OUT RE-LABELS A PIPELINE WALLET. {f(WHALE_I)} EGLD of minted funds went through a fresh wallet into Unknown Whale I, the address this model has treated since run #19 as an OTC operator's inventory, both a feeder and a destination of the desks. "
    f"An attacker cashing out sends to exchange deposit addresses. Unknown Whale I is most likely an exchange hot wallet, which would make the 'operator' flows in every hub trace since run #19 exchange flows into a venue the model has not named. "
    f"The same reasoning applies to erd1a6lte0...u48u4l ({f(A6_AMT)} minted EGLD, nonce 2,131, a stream of small inbound transfers). Both are flagged for labelling; neither changes a past total, only what the venue column is called.\n\n"
    f"PIPELINE. In the {WIN_DAYS:.1f} days before the halt the desks moved {f(otc['gross_out'])} gross and delivered {f(otc['net_one_way'])} one-way ({otc['circ_pct']:.0f}% circular). Net by venue: Gate.io {V(otc['net_by_venue'],'Gate.io'):+,.0f}, Bybit {V(otc['net_by_venue'],'Bybit'):+,.0f}, UPbit {V(otc['net_by_venue'],'UPbit'):+,.0f}, Binance.com {V(otc['net_by_venue'],'Binance.com'):+,.0f}. "
    f"UPbit fed {f(otc['upbit_feed'])} and received 80,000 back, so for once UPbit was a net receiver. The desk balance ended at {f(otc['desk_bal'])}. Wave #4 netted Sep 7 to the halt: {f(wave['net_one_way'])} EGLD, with no straddle overstatement.\n\n"
    f"FEED SIDE. Bybit-parented feeders put {f(V(FEED,'Bybit'))} into the desks, UPbit {f(V(FEED,'UPbit'))}, Binance-parented {f(V(FEED,'Binance'))}, unattributed {f(V(FEED,'Unattributed'))}. The Binance hot wallet sent {f(HOT['total_egld'])} to known feeders and routers, day-sliced and uncapped: down from 218,264 last week and below the 50,000 line for the first time in four weeks (over 5.3 days, not 7).\n\n"
    f"ADDRESS POISONING. Two lookalike wallets have been spraying 0.0001 EGLD at the pipeline's routers ({max(v['distinct_targets_30d'] for v in PZ.values())} targets each in 30 days) so that a lookalike of a desk appears in each router's history. They also show up as 'unresolved' terminals in the hub trace at dust amounts, which is why the unattributed totals carry a few thousandths of an EGLD per router. No transfer above 0.01 EGLD has reached either lookalike.\n\n"
    f"TIERS, NET OF THE INCIDENT. On the common-address basis ({O['tiers_basis']} wallets): mega {O['tiers']['mega']['net_change_egld']:+,.0f}, large {O['tiers']['large']['net_change_egld']:+,.0f}, mid {O['tiers']['mid']['net_change_egld']:+,.0f}. Holding each wallet in its prior tier: mega {tiers_fixed['mega']['net_change_egld']:+,.0f}, large {tiers_fixed['large']['net_change_egld']:+,.0f}, mid {tiers_fixed['mid']['net_change_egld']:+,.0f}. "
    f"The large-tier fall is mostly two contract moves that are the MEX recovery and not holder behaviour: the xExchange WEGLD contract lost 66,943 EGLD (the recovery's WEGLD unwrapped to EGLD) and Hatom's EGLD money market gained 83,876 (the borrowed EGLD returned).\n\n"
    f"DEMAND. DEX volume is not evaluable: the 24 hours before the snapshot contain no blocks. The order book was read after the halt, with deposits closed: Binance+Bybit bids within 2% of mid ${f(bbn)} against ${f(bbp)} last week ({100*(bbn-bbp)/bbp:+.0f}%), and CEX spot volume over seven days {f(BOOK['spot_volume_7d_egld']/1e6,2)}M EGLD (from {f(BOOK['spot_volume_prior_7d_egld']/1e6,2)}M). "
    f"Withdrawal breadth ex-pipeline: {br['ex_n']} recipients took {f(br['ex_egld'])} EGLD, and two identical Coinbase withdrawals of 114,208 each make up {br['top_two_share_pct']:.0f}% of it.")

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
                   "weeks_in_state": {"ledgerbyfigment": 14, "p2p_org_": 5, "truststakingsw": 16}.get(r["provider"], 3),
                   "note": f"emptied inside the archive (last locked > 0 snapshot {r['last_locked_in_archive']}); {r['inbound_txs_this_week']} inbound txs this week"
                           + (f"; delegators {d['prev_users']:,} -> {d['users']:,} ({d['users_delta']:+d})" if d.get("users") is not None and d.get("prev_users") is not None else "")})
for ident in ("egldstakingprovider", "procryptostaking"):
    states.append({"provider": ident, "state": "fee_squeezed", "locked_egld": mv(ident, "locked"),
                   "num_users": mv(ident, "users"), "num_nodes": mv(ident, "nodes"), "apr_pct": mv(ident, "apr") or 0.0,
                   "fee_pct": mv(ident, "fee") or 0.0, "weeks_in_state": 3,
                   "note": f"THIRD WEEK AFTER THE FEE REVERSAL: book {mv(ident,'delta'):+,.0f}, users {mv(ident,'users_delta'):+d}. Capital has not come back in three weeks of restored yield."})
wd_top = WD.get("by_provider_top", [])
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
                          "note": "Deregistration is scored as an observed TRANSITION (locked > 0 in the prior stored snapshot, 0 now). Zero transitions for a third week. The provider join now keys on the contract address in the collector itself (run #25 rec #7): 100% match, zero identity changes."},
    "fee_events": [{"provider": i, "fee_from_pct": 100.0, "fee_to_pct": mv(i, "fee") or 0.0, "apr_from_pct": 0.0, "apr_to_pct": mv(i, "apr") or 0.0,
                    "locked_egld": mv(i, "locked"), "locked_wow_egld": mv(i, "delta"), "users": mv(i, "users"),
                    "users_wow": mv(i, "users_delta"), "num_nodes": mv(i, "nodes")} for i in ("egldstakingprovider", "procryptostaking")],
    "unbonding_in_flight": {
        "wallet": ub["wallet"], "total_egld": ub["pending_total"],
        "legs": [{"provider": p["contract"][:10] + "..." + p["contract"][-8:], "amount": p["amount_egld"],
                  "days_to_unbond": p["days_remaining"], "date": "2026-08-14" if p["amount_egld"] < 100000 else "2026-08-15"} for p in ub["pending"]],
        "share_of_delegation_decline_pct": 0.0, "raw_residual_egld": sk["residual"], "corrected_direct_node_egld": None,
        "status": f"RETIRED, FIFTH WEEK UNMOVED. Balance {f(ub['balance'],2)} EGLD, {f(ub['pending_total'])} unbonded-and-unclaimed.",
        "queue_this_week": {
            "undelegated_egld": sk["undelegated_week"], "distinct_callers": sk["undelegate_callers"],
            "measured_pending_egld": sk["pool_total"], "largest_legs": sk["pool_rows"][:12],
            "withdraw_calls": O["withdraw_calls"], "previous_withdraw_calls": O["prev_withdraw_calls"],
            "withdraw_egld_returned": WD.get("egld_returned_total", 0.0),
            "withdraw_egld_by_provider_top": [{"provider": a, "egld": b} for a, b in wd_top[:8]],
            "coverage_note": (f"Full-set scan of {sk['providers_scanned']} provider contracts over the {WIN_DAYS:.1f} days the chain ran. {sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD; "
                              f"{O['withdraw_calls']} withdraw calls returned {f(WD.get('egld_returned_total',0))} EGLD, decoded from each call's smart-contract results for the first time (run #25 rec #5). "
                              f"{len(O['scan_depth']['pagecap_provscan'])} first-pass scan ended on the page cap and was re-paged in the deep pass.")}},
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
            f"THE COMPOUND RATE CAME BACK: {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} reDelegateRewards vs {cvc['claim_count']} claimRewards), from 49.44%. Series: 60.19 / 58.81 / 62.25 / 59.54 / 59.07 / 57.03 / 57.51 / 62.05 / 49.44 / {cvc['compound_pct_of_reward_decisions']:.2f}. Last week's reading was the outlier.",
            f"Retail {fates['retail']['total_events']} claims, {fates['retail']['by_count'].get('sold',0)} to a labelled exchange - a thirteenth consecutive run. Mid-tier {fates['mid_tier']['total_events']} claims, {fates['mid_tier']['by_count'].get('sold',0)} sold; institutional {fates['institutional']['total_events']}, {fates['institutional']['by_count'].get('sold',0)} sold.",
            f"CAVEAT: the scanner reads a trailing 7-day window ending at run time, and the chain stopped 55 hours before that, so the sample is the {WIN_DAYS:.1f} pre-halt days.",
            f"Sample: {ag['providers_sampled']} of {ag.get('providers_requested',8)} providers, {ag.get('api_errors',0)} retried API errors, run after the collector with the new 429 guard (run #25 rec #4).",
            "PROVIDER OPERATORS DID NOT SELL FEES for a fourteenth consecutive run."]},
    "analysis": (
        f"A QUIET STAKING WEEK THAT ENDED EARLY. Over the {WIN_DAYS:.1f} days before the halt, staked EGLD rose {M['staked_chg']:+,.0f} to {f(econ['staked'])} and the ratio held at {100*M['sr']:.2f}%, inside run #25's settled band (46.30-46.80%). Delegation TVL rose {sk['delta_locked']:+,.0f} to {f(tl)}. "
        f"The staked-minus-delegated residual moved {sk['residual']:+,.0f}.\n\n"
        f"WITHDRAW AMOUNTS, MEASURED FOR THE FIRST TIME. {O['withdraw_calls']} withdraw calls returned {f(WD.get('egld_returned_total',0))} EGLD to their callers (largest: " + ", ".join(f"{a} {f(b)}" for a, b in wd_top[:4]) + "). "
        f"New unDelegations were {f(sk['undelegated_week'])} EGLD from {sk['undelegate_callers']} wallets. More EGLD finished unbonding than started, so the unbonding queue shrank while active delegation grew. "
        f"Last week's attribution of the staked drop to matured queues rested on timing; it now has a measured counterpart, though last week's withdraw amounts ({O['prev_withdraw_calls']} calls) were not decoded and cannot be recovered cheaply.\n\n"
        f"THE REWARD DECISION FLIPPED BACK. {cvc['compound_pct_of_reward_decisions']:.2f}% compound, from 49.44%, so the compound-regime test resolves against the regime-switch reading. Claims were held, not sold, as they have been for thirteen runs.\n\n"
        f"PROVIDERS. meria {mv('meria','delta'):+,.0f} is the largest loser for a second week and also the largest withdraw recipient ({f(wd_top[0][1]) if wd_top else 'n/a'} EGLD returned); valuestaking {mv('valuestaking','delta'):+,.0f}, vaporrepublic {mv('vaporrepublic','delta'):+,.0f}, Synexis {mv('Synexis','delta'):+,.0f} gained. "
        f"The two fee-reversed providers lost book for a third week (egldstakingprovider {mv('egldstakingprovider','delta'):+,.0f}, procryptostaking {mv('procryptostaking','delta'):+,.0f}). Delegators {sk['users_delta']:+,} to {f(sk['users'])}; {sk['gaining']} providers gained, {sk['losing']} lost.\n\n"
        f"DEREGISTRATION: zero transitions (week 3 of 4). ledgerbyfigment {dser.get('ledgerbyfigment',{}).get('users_delta',0):+d}, p2p_org_ {dser.get('p2p_org_',{}).get('users_delta',0):+d}, stakedinc unchanged. The provider join now uses the contract address in the collector: 100% match and no identity changes.\n\n"
        "THE HALT AND STAKING. The halted state has no incident balance inside the staking module or any delegation contract. Epoch rewards stop with the chain, so the next reading will cover however long the network is down plus whatever the recovery does to the epoch schedule.")}

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
mexe_r25 = r25["token_activity"]["xexchange"]["mex_pair_event"]
usdc = tk["stable"]["USDC-c76f1f"]; usdt = tk["stable"]["USDT-f8c08c"]
lsd = tk["lsd"]
MEX_PRE = 3.97703098880543e-07
R["token_activity"] = {
    "top_by_holders": [th(t) for t in D["tokens_holders"][:10]],
    "top_by_volume": [tv(t) for t in D["tokens_txs"][:10]],
    "top_by_market_cap": [tm(t) for t in D["tokens_mcap"][:10]],
    "newly_issued": [{"identifier": t["identifier"], "name": t["name"], "holders": t["accounts"], "transactions": t["transactions"],
                      "deployer": t["deployer"], "note": "test issuance (TSTA..TSTJ series from one deployer); below the >10 holder / >5 tx bar"} for t in newly],
    "xexchange": {
        "total_pairs": xx["pairs"], "total_volume_24h_usd": 0.0, "mex_price_usd": xx["mex_price"], "mex_market_cap_usd": xx["mex_mcap"],
        "mex_price_change_24h_pct": None, "mex_price_change_wow_pct": xx["mex_wow"], "mex_price_source": xx["mex_price_source"],
        "top_pair": "n/a (no trades in the 24h before the snapshot - chain halted)", "top_pair_volume_24h_usd": 0.0, "top_pair_dominance_pct": 0.0,
        "top_pairs_by_volume": [],
        "pool_tvl_usd": xx["pool_tvl"], "previous_pool_tvl_usd": xx["prev_pool_tvl"],
        "pool_tvl_ex_mex_pair_usd": bid["pooltvl_ex_mex_usd"], "pool_tvl_ex_mex_pair_wow_pct": bid["pooltvl_ex_mex_wow_pct"],
        "turnover_ratio_pct": 0.0, "previous_turnover_ratio_pct": xx["prev_turnover"],
        "dex_vol_wow_pct": -100.0, "dex_volume_egld_24h": 0.0, "previous_dex_volume_egld_24h": bid["prev_dexvol_egld"], "dex_vol_egld_wow_pct": -100.0,
        "pool_tvl_egld": bid["pooltvl_egld"], "previous_pool_tvl_egld": bid["prev_pooltvl_egld"],
        "wegld_usdc_share_of_volume_pct": 0.0, "ex_wegld_usdc_volume_usd": 0.0,
        "volume_status": "NOT EVALUABLE - no blocks in the 24h before the snapshot",
        "mex_pair_depth": {"pair": "MEX/WEGLD", "tvl_usd": xx["mex_pair_depth"]["tvl_usd"], "tvl_egld": xx["mex_pair_depth"]["tvl_egld"],
                           "previous_tvl_egld": 0.0, "tvl_egld_wow_pct": None, "volume_24h_usd": 0.0, "trades_24h": 0,
                           "share_of_pool_tvl_pct": xx["mex_pair_depth"]["share_of_pool_tvl_pct"], "depth_rank": xx["mex_pair_depth"]["depth_rank"],
                           "status": f"RESUMED {iso(RESUME_TS)}; reserves {f(float(MR['pairs']['MEX/WEGLD']['holds'].get('WEGLD-bd4d79',0)))} WEGLD + {f(float(MR['pairs']['MEX/WEGLD']['holds'].get('MEX-455c57',0))/1e9,0)}B MEX"},
        "mex_pair_event": mexe_r25,
        "mex_incident_recovery": {"owner_calls": MR["owner_calls"], "recovery_contract": RECOVERY,
                                  "pairs_now": MR["pairs"], "mex_market_txs_7d": MR["mex_mm_txs_7d"], "mex_market_functions": MR["mex_mm_functions"],
                                  "hmex_supply": MR["hmex_supply"], "hmex_prev_supply": MR["hmex_prev_supply"],
                                  "egld_money_market_balance": df["egld_mm_balance"], "egld_money_market_prev_balance": df["egld_mm_prev_balance"],
                                  "incident_wallets_now": {k: {"balance_egld": v["balance_egld"], "txs_out": v["txs_out"], "out_functions": v["out_functions"]} for k, v in MR["wallets"].items()},
                                  "hatom_incident_report": "not published as of the snapshot"}},
    "analysis": (
        f"THE MEX INCIDENT UNWOUND ON CHAIN IN TWO HOURS. On Sep 15 at 15:38 UTC Hatom's deployer (erd1cc2yw3...99pvt) deployed a recovery contract (erd1qqqq...m78sszpu2uj) and configured it (setAllowedBorrower, setSaleRoute and campaign settings, all from the deployer). At {hm(WL_TS[0])} the xExchange router owner put MEX/WEGLD, MEX/USH and MEX/USDC on each pool's pause whitelist. "
        f"From 19:15 to 21:11 a keeper wallet (erd12uv6mj...7dlsmrt5jd) called runRound 89 times. Each round took seized HMEX collateral, redeemed it for MEX and sold the MEX into MEX/WEGLD, then unwrapped the WEGLD to EGLD. "
        f"In total the contract redeemed {f(RECOVERY['hmex_redeemed']/1e12,2)}T HMEX for {f(RECOVERY['mex_redeemed']/1e9,0)}B MEX and sold {f(RECOVERY['mex_sold_mex_wegld']/1e9,0)}B of it for {f(RECOVERY['wegld_received'])} WEGLD. On Sep 16 a second campaign sold {f(RECOVERY['mex_sold_mex_ush']/1e9,0)}B MEX into MEX/USH and {f(RECOVERY['mex_sold_mex_usdc']/1e9,0)}B into MEX/USDC and made {RECOVERY['liquidate_borrow_calls']} liquidateBorrow calls paid in USDT. "
        f"The router owner removed the whitelists and called resume at {hm(RESUME_TS)} UTC Sep 17, a day after Hatom's stated Wednesday. Hatom's EGLD money market is back to {f(df['egld_mm_balance'])} EGLD from {f(df['egld_mm_prev_balance'])}, close to its pre-incident 118,306.\n\n"
        f"WHO BORE THE SALE. The recovery sold into pools other LPs could not leave: {mexe_r25['failed_txs_7d']} withdrawal and swap calls had failed against MEX/WEGLD by Sep 14, and more failed until the resume. "
        f"The MEX sold back into the pool roughly matches what the incident wallet bought out of it on Sep 13 (220B MEX for 85,200 EGLD), so the pool's reserves ended close to their pre-incident composition, and LPs kept the difference plus fees. "
        f"Whether any LP lost value against a no-incident path depends on prices Hatom's report should state. What the chain shows is that the recovery depended on the DEX admin granting one contract exclusive access to paused pools. That privilege is worth knowing about, whatever the outcome this time.\n\n"
        f"MEX NOW. The pool prices MEX at {xx['mex_price']:.2e}, {100*(xx['mex_price']-MEX_PRE)/MEX_PRE:+.0f}% against its pre-incident {MEX_PRE:.2e} and {xx['mex_wow']:+.0f}% against last week's CoinGecko print. MEX/WEGLD holds {f(float(MR['pairs']['MEX/WEGLD']['holds'].get('WEGLD-bd4d79',0)))} WEGLD and {f(float(MR['pairs']['MEX/WEGLD']['holds'].get('MEX-455c57',0))/1e9,0)}B MEX, and after the resume 14 of its 22 calls were LPs removing liquidity. HMEX supply {HT['HMEX-df6df7']['supply_pct']:+.0f}% to {f(MR['hmex_supply']/1e12,2)}T. The incident wallet still holds 2.65 EGLD and has sent nothing since.\n\n"
        f"VENUE ACTIVITY IS NOT EVALUABLE. /mex/pairs returns zero 24h volume on every pair because no block has been produced in the last 24 hours. Pool TVL ${f(xx['pool_tvl'])} includes MEX/WEGLD again; like-for-like without it, {bid['pooltvl_egld_ex_mex_wow_pct']:+.1f}% in EGLD.\n\n"
        f"STABLECOINS: USDC {usdc['pct']:+.2f}% to {f(usdc['supply'])}, USDT {usdt['pct']:+.2f}% to {f(usdt['supply'])}; both contracted before the halt. NEWLY ISSUED: {len(newly)} issuances, all a TSTA-TSTJ test series from one deployer with two holders each; none clears the bar.")}

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


xe_egld_pct = 100 * (df["xexch_egld"] - df["xexch_prev_usd"] / pecon["egld_price_usd"]) / (df["xexch_prev_usd"] / pecon["egld_price_usd"])
hl_ex = df["hatom_lending_ex_hmex_egld_pct"]
HALTNOTE = "24h count reads 0: no blocks in the 24h before the snapshot (chain halted)."
R["defi_activity"] = {
    "protocols": [
        {"name": "xExchange", "category": "dex", "volume_24h_usd": 0.0, "active_pairs": xx["pairs"], "transfers_24h": None,
         "tvl_usd": df["xexch_usd"], "tvl_egld": df["xexch_egld"], "tvl_wow_change_pct": xe_egld_pct},
        {"name": "Hatom Lending", "category": "lending", "volume_24h_usd": 0.0, "active_pairs": 0, "transfers_24h": None,
         "tvl_usd": df["hatom_lending_usd"], "tvl_egld": df["hatom_lending_egld"], "tvl_wow_change_pct": hl_ex},
        {"name": "Hatom Liquid Staking", "category": "liquid_staking", "volume_24h_usd": 0.0, "active_pairs": 0, "transfers_24h": None,
         "tvl_usd": df["hatom_lsd_usd"], "tvl_egld": df["hatom_lsd_usd"] / price, "tvl_wow_change_pct": lsd["SEGLD-3ad2d0"]["pct"]},
        {"name": "XOXNO LSD", "category": "liquid_staking", "volume_24h_usd": 0.0, "active_pairs": 0, "transfers_24h": None,
         "tvl_usd": df["xoxno_usd"], "tvl_egld": df["xoxno_usd"] / price, "tvl_wow_change_pct": lsd["XEGLD-e413ed"]["pct"]}],
    "protocol_breakdown": [
        {"protocol": "xExchange", "category": "dex", "addresses_tracked": 17, "tvl_usd": df["xexch_usd"], "tvl_egld": df["xexch_egld"],
         "tvl_wow_change_pct": xe_egld_pct, "transfers_24h": None, "volume_24h_usd": 0.0,
         "notable_events": f"MEX pools RESUMED {iso(RESUME_TS)} after Hatom's recovery contract sold 270B MEX through whitelisted access to the paused pools. WEGLD contract balances {f(df['xexch_egld'])} EGLD ({xe_egld_pct:+.1f}%): the recovery unwrapped its WEGLD proceeds. Volume not evaluable (halt).",
         "health_signal": "shrinking"},
        {"protocol": "Hatom Lending", "category": "lending", "addresses_tracked": 13, "tvl_usd": df["hatom_lending_usd"], "tvl_egld": df["hatom_lending_egld"],
         "tvl_wow_change_pct": hl_ex, "transfers_24h": None,
         "notable_events": f"Ex-HMEX on both sides, EGLD TVL {hl_ex:+.2f}% on a {pc:+.2f}% price week: below the 5% guardrail, the inverse rule is NOT tested. HEGLD supply {HT['HEGLD-d61095']['supply_pct']:+.2f}% as the EGLD market refilled ({f(df['egld_mm_prev_balance'])} -> {f(df['egld_mm_balance'])} EGLD). HMEX {HT['HMEX-df6df7']['supply_pct']:+.0f}% as the seized collateral was redeemed; HHTM {HT['HHTM-e03ba5']['supply_pct']:+.0f}%.",
         "health_signal": "growing"},
        {"protocol": "Hatom Liquid Staking", "category": "liquid_staking", "addresses_tracked": 2, "tvl_usd": df["hatom_lsd_usd"], "tvl_egld": df["hatom_lsd_usd"] / price,
         "tvl_wow_change_pct": lsd["SEGLD-3ad2d0"]["pct"], "transfers_24h": None,
         "notable_events": f"SEGLD supply {lsd['SEGLD-3ad2d0']['pct']:+.2f}% to {f(lsd['SEGLD-3ad2d0']['supply'])}, a redemption after weeks of near-flat readings. SWTAO {lsd['SWTAO-356a25']['pct']:+.2f}% (price from the WTAO accumulator fallback; supply basis).",
         "health_signal": hs(lsd["SEGLD-3ad2d0"]["pct"])},
        {"protocol": "Hatom USH", "category": "stablecoin", "addresses_tracked": 4, "tvl_usd": df["ush_usd"], "tvl_egld": df["ush_usd"] / price,
         "tvl_wow_change_pct": lsd["USH-111e09"]["pct"], "transfers_24h": None,
         "notable_events": f"USH {lsd['USH-111e09']['pct']:+.2f}% to {f(lsd['USH-111e09']['supply'])}. The recovery took 49,918 USH out of MEX/USH and passed it on to the keeper.",
         "health_signal": "flat"},
        {"protocol": "XOXNO LSD", "category": "liquid_staking", "addresses_tracked": 3, "tvl_usd": df["xoxno_usd"], "tvl_egld": df["xoxno_usd"] / price,
         "tvl_wow_change_pct": lsd["XEGLD-e413ed"]["pct"], "transfers_24h": None,
         "notable_events": f"XEGLD supply {lsd['XEGLD-e413ed']['pct']:+.2f}% to {f(lsd['XEGLD-e413ed']['supply'])}, a redemption.",
         "health_signal": hs(lsd["XEGLD-e413ed"]["pct"])},
        {"protocol": "XOXNO Aggregator", "category": "aggregator", "addresses_tracked": 1, "tvl_usd": 0.0, "tvl_egld": 0.0, "tvl_wow_change_pct": None,
         "transfers_24h": None, "volume_24h_usd": 0.0, "notable_events": HALTNOTE, "health_signal": None},
        {"protocol": "OneDex", "category": "aggregator", "addresses_tracked": 5, "tvl_usd": 0.0, "tvl_egld": 0.0, "tvl_wow_change_pct": None,
         "transfers_24h": None, "volume_24h_usd": 0.0, "notable_events": HALTNOTE + " OneDex Launchpad still fails bech32 validation.", "health_signal": None},
        {"protocol": "JEXchange", "category": "dex", "addresses_tracked": 10, "tvl_usd": 0.0, "tvl_egld": 0.0, "tvl_wow_change_pct": None,
         "transfers_24h": None, "volume_24h_usd": 0.0,
         "notable_events": f"7-day router transfers (the window includes 55 halted hours): {f(jex7.get('JEXchange Router'))} on the main router (9,968 last week), " + ", ".join(f(jex7.get(f'JEXchange Router {i}')) for i in range(2, 6)) + " on routers 2-5.",
         "health_signal": "shrinking"},
        {"protocol": "JewelSwap", "category": "liquid_staking", "addresses_tracked": 1, "tvl_usd": (es("JWLEGLD-023462") or 0) * price, "tvl_egld": es("JWLEGLD-023462") or 0.0,
         "tvl_wow_change_pct": ep("JWLEGLD-023462"), "transfers_24h": None,
         "notable_events": f"{f(es('JWLEGLD-023462'))} EGLD delegated ({(ep('JWLEGLD-023462') or 0):+.2f}%), {em['JWLEGLD-023462']['holders']} holders.", "health_signal": hs(ep("JWLEGLD-023462"))},
        {"protocol": "SALSA (Staking Agency)", "category": "liquid_staking", "addresses_tracked": 1, "tvl_usd": (es("LEGLD-d74da9") or 0) * price, "tvl_egld": es("LEGLD-d74da9") or 0.0,
         "tvl_wow_change_pct": ep("LEGLD-d74da9"), "transfers_24h": None,
         "notable_events": f"Returned by the seeded sweep. {f(es('LEGLD-d74da9'))} EGLD delegated ({(ep('LEGLD-d74da9') or 0):+.2f}%); LEGLD supply {em['LEGLD-d74da9']['pct']:+.2f}%.", "health_signal": hs(ep("LEGLD-d74da9"))},
        {"protocol": "Dinovox VoxEGLD", "category": "liquid_staking", "addresses_tracked": 1, "tvl_usd": (es("VOXEGLD-5872e5") or 0) * price, "tvl_egld": es("VOXEGLD-5872e5") or 0.0,
         "tvl_wow_change_pct": ep("VOXEGLD-5872e5"), "transfers_24h": None,
         "notable_events": f"{f(es('VOXEGLD-5872e5'))} EGLD ({(ep('VOXEGLD-5872e5') or 0):+.1f}%), holders {em['VOXEGLD-5872e5']['holders']}: a third week of growth.", "health_signal": hs(ep("VOXEGLD-5872e5"))},
        {"protocol": "VestaX Finance", "category": "liquid_staking", "addresses_tracked": 1, "tvl_usd": (es("VEGLD-2b9319") or 0) * price, "tvl_egld": es("VEGLD-2b9319") or 0.0,
         "tvl_wow_change_pct": ep("VEGLD-2b9319"), "transfers_24h": None,
         "notable_events": f"Returned by the seeded sweep. {f(es('VEGLD-2b9319'))} EGLD.", "health_signal": hs(ep("VEGLD-2b9319"))}],
    "sc_deployments": [],
    "analysis": (
        f"DEFI STOPPED WITH THE CHAIN. Every protocol's 24-hour transfer count reads zero because the 24 hours before the snapshot contain no blocks; those counts are not evaluable and are left empty in the breakdown. What the halted state does show is the week up to Sep 19.\n\n"
        f"HATOM CLOSED ITS MEX INCIDENT. The EGLD money market recovered {f(df['egld_mm_balance']-df['egld_mm_prev_balance'])} EGLD to {f(df['egld_mm_balance'])} through the recovery contract's MEX sales, HEGLD supply rose {HT['HEGLD-d61095']['supply_pct']:+.2f}%, and HMEX supply fell {abs(HT['HMEX-df6df7']['supply_pct']):.0f}%. "
        f"Lending TVL ex-HMEX (on both sides; last week's HMEX was priced off a CoinGecko quote) moved {hl_ex:+.2f}% in EGLD. With EGLD {pc:+.2f}% on the week the inverse rule is not tested (the price moved less than 5%).\n\n"
        f"LIQUID STAKING SHOWED REDEMPTIONS BEFORE THE HALT. SEGLD supply {lsd['SEGLD-3ad2d0']['pct']:+.2f}% and XEGLD {lsd['XEGLD-e413ed']['pct']:+.2f}% after weeks of flat readings, and SALSA's LEGLD {em['LEGLD-d74da9']['pct']:+.2f}%. Supply is price-independent, so these are holders leaving, and they left before the exploit. "
        f"The seeded discovery sweep returned all six known protocols (SALSA and VestaX were missed last week) and two sub-100 EGLD test deploys.\n\n"
        f"WHAT THE HALT MEANS FOR DEFI. Liquidations, oracles and redemptions have been frozen for 55 hours while EGLD traded between ${post_lo[1]:.2f} and ${post_last:.2f} on exchanges. When blocks resume, lending markets will reprice collateral at a price that moved while no one could act. That restart is a risk to watch in itself.")}

# ---------------------------------------------------------------------------
comb = usdc["supply"] + usdt["supply"]; combp = usdc["prev"] + usdt["prev"]
R["anomalies"] = [
    {"metric": "chain_block_production", "current_value": 0, "previous_value": 1, "method": "rule_based", "severity": "critical", "change_pct": -100.0,
     "description": f"No block on any shard since {iso(HALT_TS0)} (metachain {iso(HALT_TS)[11:]}), 55 hours before the snapshot. MultiversX paused network progression after an attempted exploit of a VM-level atomicity issue produced invalid state changes. The first halt in 26 runs of tracking."},
    {"metric": "egld_minted_by_exploit", "current_value": MINTED_TOTAL, "previous_value": 0, "method": "rule_based", "severity": "critical",
     "description": f"One wallet and its contract hold {f(MINTED_HELD)} EGLD and forwarded {f(HALT['fanout_total_egld'])} more, about {MINTED_TOTAL/econ['totalSupply']:.1f}x the {f(econ['totalSupply'])} total supply, produced by {len(ROUNDS)} doubling deposit/compound rounds from {f(FUND,1)} EGLD of exchange-withdrawn funding. /economics total supply is unchanged, so the protocol's own accounting has not absorbed it; MultiversX plans a targeted recovery of the incident-related state."},
    {"metric": "exchange_net_flow_raw_egld", "current_value": ex["net_raw"], "previous_value": prev.get("exchange_net_flow_egld", 117970), "method": "rule_based", "severity": "critical",
     "description": f"Raw exchange balance change {ex['net_raw']:+,.0f}, of which {f(INC_EX_TOT)} is minted EGLD deposited at Binance.com, KuCoin and MEXC in three minutes. Net of the incident: {ex['net']:+,.0f} (z={zz('exflow'):+.2f})."},
    {"metric": "otc_net_one_way_egld_7d", "current_value": otc["net_one_way"], "previous_value": prev["otc_net_one_way_series"]["run25"], "method": "z_score", "severity": "medium",
     "average_value": z["otc_net"].get("mean"), "stddev": z["otc_net"].get("stddev"), "z_score": zz("otc_net"),
     "change_pct": 100 * (otc["net_one_way"] - prev["otc_net_one_way_series"]["run25"]) / prev["otc_net_one_way_series"]["run25"],
     "description": f"Net one-way delivery {f(otc['net_one_way'])} over the {WIN_DAYS:.1f} days before the halt, from 401,353 (z={zz('otc_net'):+.2f}); circularity {otc['circ_pct']:.0f}%, the highest since run #19. UPbit's feed fell to 71,000."},
    {"metric": "mex_price_usd", "current_value": xx["mex_price"], "previous_value": xx["prev_mex_price"], "method": "rule_based", "severity": "medium", "change_pct": xx["mex_wow"],
     "description": f"MEX {xx['mex_wow']:+.0f}% against last week's CoinGecko print, now priced by the restored MEX/WEGLD pool at {xx['mex_price']:.2e}, about {xx['mex_price']/MEX_PRE:.1f}x pre-incident. The recovery sold 270B MEX, most of it into MEX/WEGLD."},
    {"metric": "hatom_hmex_supply", "current_value": MR["hmex_supply"], "previous_value": MR["hmex_prev_supply"], "method": "rule_based", "severity": "medium", "change_pct": HT["HMEX-df6df7"]["supply_pct"],
     "description": f"HMEX supply {HT['HMEX-df6df7']['supply_pct']:+.0f}%: Hatom's recovery contract redeemed {f(RECOVERY['hmex_redeemed']/1e12,2)}T HMEX of seized collateral for MEX and sold it."},
    {"metric": "reward_compound_pct", "current_value": cvc["compound_pct_of_reward_decisions"], "previous_value": 49.44, "method": "z_score", "severity": "low",
     "average_value": z["compound"].get("mean"), "stddev": z["compound"].get("stddev"), "z_score": zz("compound"),
     "change_pct": 100 * (cvc["compound_pct_of_reward_decisions"] - 49.44) / 49.44,
     "description": f"Compound rate {cvc['compound_pct_of_reward_decisions']:.2f}% from 49.44%, z={zz('compound'):+.2f}: back inside its normal band. Last week's reading was the anomaly."},
    {"metric": "staked_ratio", "current_value": M["sr"], "previous_value": M["sr_prev"], "method": "z_score", "severity": "medium",
     "average_value": z["sr"].get("mean"), "stddev": z["sr"].get("stddev"), "z_score": zz("sr"), "change_pct": 100 * (M["sr"] - M["sr_prev"]) / M["sr_prev"],
     "description": f"Staked ratio {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp). The z of {zz('sr'):+.2f} reflects last week's drop pulling the level below the eight-week mean; the week itself was flat."},
    {"metric": "lsd_supply_xegld", "current_value": lsd["XEGLD-e413ed"]["supply"], "previous_value": lsd["XEGLD-e413ed"]["prev"], "method": "rule_based", "severity": "low", "change_pct": lsd["XEGLD-e413ed"]["pct"],
     "description": f"XEGLD supply {lsd['XEGLD-e413ed']['pct']:+.2f}% and SEGLD {lsd['SEGLD-3ad2d0']['pct']:+.2f}%: synchronized LSD redemption before the halt."},
    {"metric": "address_poisoning_dust_txs_30d", "current_value": sum(v["dust_txs_30d"] for v in PZ.values()), "previous_value": 0, "method": "rule_based", "severity": "low",
     "description": "Two lookalike wallets mimicking the OTC desks' first and last characters sent 0.0001 EGLD dust to 33 pipeline routers each. None has received a misdirected transfer."},
]

R["trend_indicators"] = {
    "accelerating_exchange_outflows": [
        {"exchange": "Coinbase", "trend": "up", "cumulative_change_pct": ent("Coinbase")["pct"], "weeks_in_trend": 1,
         "interpretation": f"{ent('Coinbase')['net_flow_egld']:+,.0f} ({ent('Coinbase')['pct']:+.1f}%), ending a four-week fall, while two identical 114,208 withdrawals went out."},
        {"exchange": "Gate.io", "trend": "down", "cumulative_change_pct": ent("Gate.io")["pct"], "weeks_in_trend": 1,
         "interpretation": f"{ent('Gate.io')['net_flow_egld']:+,.0f} ({ent('Gate.io')['pct']:+.1f}%) after three weeks up; Gate.io was the largest venue on both legs of the desks."},
        {"exchange": "UPbit", "trend": "up", "cumulative_change_pct": ent("UPbit")["pct"], "weeks_in_trend": 1,
         "interpretation": f"{ent('UPbit')['net_flow_egld']:+,.0f}: UPbit's desk feed fell to 71,000 and 80,000 came back."}],
    "validator_movements": {"providers_joining": 0, "providers_leaving": 0, "net_provider_change": 0, "notable_joiners": [], "notable_leavers": []},
    "token_supply_events": [
        {"identifier": "HMEX-df6df7", "name": "HMEX", "event": "burn", "supply_previous": str(int(MR["hmex_prev_supply"])), "supply_current": str(int(MR["hmex_supply"])),
         "change_pct": HT["HMEX-df6df7"]["supply_pct"], "description": "Hatom's recovery contract redeemed the incident collateral."},
        {"identifier": "XEGLD-e413ed", "name": "XEGLD", "event": "burn", "supply_previous": str(int(lsd["XEGLD-e413ed"]["prev"])), "supply_current": str(int(lsd["XEGLD-e413ed"]["supply"])),
         "change_pct": lsd["XEGLD-e413ed"]["pct"], "description": "XOXNO LSD redemption before the halt."},
        {"identifier": "USDT-f8c08c", "name": "USDT", "event": "burn", "supply_previous": str(int(usdt["prev"])), "supply_current": str(int(usdt["supply"])),
         "change_pct": usdt["pct"], "description": f"{f(usdt['prev']-usdt['supply'])} USDT redeemed before the halt."},
        {"identifier": "USDC-c76f1f", "name": "WrappedUSDC", "event": "burn", "supply_previous": str(int(usdc["prev"])), "supply_current": str(int(usdc["supply"])),
         "change_pct": usdc["pct"], "description": f"{f(usdc['prev']-usdc['supply'])} USDC redeemed; combined dollar base {100*(comb-combp)/combp:+.2f}%."},
        {"identifier": "EGLD", "name": "EGLD (account balances)", "event": "mint", "supply_previous": str(int(econ["totalSupply"])), "supply_current": str(int(econ["totalSupply"] + MINTED_TOTAL)),
         "change_pct": 100 * MINTED_TOTAL / econ["totalSupply"],
         "description": "Invalid EGLD created by the Sep 19 VM exploit and visible in account balances; /economics total supply unchanged. Expected to be addressed by MultiversX's targeted recovery."}],
    "consecutive_streaks": [
        {"metric": "otc_net_one_way_egld_7d", "direction": "down", "weeks": 2, "cumulative_change_pct": 100 * (otc["net_one_way"] - 536459) / 536459,
         "interpretation": f"536,459 / 401,353 / {f(otc['net_one_way'])}: the delivery peak is three weeks back, and the halt now freezes the series."},
        {"metric": "total_delegators", "direction": "flat", "weeks": 14, "cumulative_change_pct": -1.0, "interpretation": f"{sk['users_delta']:+,} to {f(sk['users'])}. Still the base rate."},
        {"metric": "provider_operator_fee_selling", "direction": "flat", "weeks": 14, "cumulative_change_pct": 0.0, "interpretation": "Fourteen runs with zero exchange destinations from sampled operator wallets."},
        {"metric": "identifiable_bid_absorbed_egld_7d", "direction": "flat", "weeks": 6, "cumulative_change_pct": 0.0, "interpretation": "Zero for a sixth week; retired instrument."}],
    "regime_shifts": [
        {"metric": "chain_liveness", "before_value": 1.0, "after_value": 0.0,
         "description": "NOT YET A REGIME SHIFT - AN OUTAGE. A halted chain is a state, not a level. It becomes a regime question only through what the recovery does: whether it reverts the invalid state cleanly, how long the network stays down, and whether exchanges restore transfers and lift warnings."},
        {"metric": "reward_compound_pct", "before_value": 49.44, "after_value": cvc["compound_pct_of_reward_decisions"],
         "description": "Candidate REJECTED. Run #25's sub-50% reading did not hold a second week; the two-week promotion rule worked again."}]}

R["watch_list"] = [
    {"item": "CHAIN HALT AND RECOVERY - network paused since Sep 19 07:41 UTC", "weeks_on_list": 1,
     "reason": f"VM-level atomicity exploit minted ~{f(MINTED_TOTAL/1e6,0)}M EGLD of invalid balances; {f(INC_EX_TOT/1e6,2)}M deposited at Binance.com, KuCoin, MEXC; {f(UNMOVED)} unmoved in three fresh wallets. MultiversX: fix on a shadow fork, targeted recovery of incident-related state, attacker accounts frozen with exchanges. PRE-COMMITTED (halt-recovery): see the test ledger."},
    {"item": "EXCHANGE TRANSFER RESTRICTIONS - Upbit trading-caution designation", "weeks_on_list": 1,
     "reason": "Upbit, Bithumb, Kraken and others restricted EGLD transfers; Upbit's caution review runs to Oct 19-23 with delisting possible. Deposits closed means OTC delivery cannot reach order books."},
    {"item": "UNKNOWN WHALE I AND erd1a6lte0 - probable exchange hot wallets", "weeks_on_list": 1,
     "reason": f"The attacker routed {f(WHALE_I)} and {f(A6_AMT)} minted EGLD into them. Identify the venues; relabel the hub-trace history if confirmed."},
    {"item": "OTC PIPELINE - quiet week, then stopped", "weeks_on_list": 26,
     "reason": f"Net one-way {f(otc['net_one_way'])} ({otc['circ_pct']:.0f}% circular) before the halt; UPbit feed 71,000; wave #4 netted {f(wave['net_one_way'])}. First post-restart reading decides whether wave #4 ended."},
    {"item": "ADDRESS POISONING OF PIPELINE ROUTERS", "weeks_on_list": 1,
     "reason": "Lookalikes of both desks dusting 33 routers each. Watch for any inbound above dust to erd1z7wy...ppm63r or erd1v6k4...ryxnk5."},
    {"item": "HATOM MEX RECOVERY - incident report pending", "weeks_on_list": 2,
     "reason": f"Recovery executed on chain Sep 15-16 via whitelisted access to paused pools; pools resumed {iso(RESUME_TS)}; EGLD market back to {f(df['egld_mm_balance'])}. Read the report for LP impact and bad debt."},
    {"item": "STAKED RATIO - floor test resolves at run #27", "weeks_on_list": 4,
     "reason": f"{100*M['sr']:.2f}%, inside the settled band. Withdraw calls returned {f(WD.get('egld_returned_total',0))} EGLD vs {f(sk['undelegated_week'])} new unDelegations."},
    {"item": "LSD REDEMPTIONS", "weeks_on_list": 1,
     "reason": f"SEGLD {lsd['SEGLD-3ad2d0']['pct']:+.2f}%, XEGLD {lsd['XEGLD-e413ed']['pct']:+.2f}%, LEGLD {em['LEGLD-d74da9']['pct']:+.2f}% before the halt."},
    {"item": "PROVIDER TRANSITIONS - fourth-deregistration test, week 3 of 4", "weeks_on_list": 5,
     "reason": "Zero transitions; join on contract address in the collector, 100% match."},
]

# ---------------------------------------------------------------------------
prior = {t["id"]: t for t in r25["pre_committed_tests"]}
tests = [t for t in r25["pre_committed_tests"] if t["status"] == "resolved"]


def resolve(tid, outcome, measured, resolution):
    t = dict(prior[tid]); t.update({"status": "resolved", "outcome": outcome, "resolved_in_run": 26, "measured_value": measured, "resolution": resolution}); return t


tests.append(resolve("mex-incident-recovery", "as_predicted",
    f"MEX/WEGLD, MEX/USH, MEX/USDC resumed {iso(RESUME_TS)} (router owner removeFromPauseWhitelist x3 then resume); Hatom EGLD money market {f(df['egld_mm_prev_balance'])} -> {f(df['egld_mm_balance'])} EGLD; HMEX {HT['HMEX-df6df7']['supply_pct']:+.0f}%; no loss or bad debt disclosed; incident report not yet published",
    "The 'all resumed, no loss disclosed' branch fires: recovery as stated. The data contradicts part of the stated terms, and it should be recorded (run #24 rule). The resume came on Thursday Sep 17, a day after the stated Wednesday. The branch did not fire on that alone because the test was scored at run #26. "
    "The unwind also relied on something the statement did not mention: the DEX admin whitelisted a Hatom-deployed recovery contract so it could sell 270B MEX of seized collateral into pools that other LPs could not trade or exit. "
    "'No losses to users' is Hatom's claim, and without its report there is no chain evidence against it. Any LP impact depends on counterfactual prices."))
tests.append(resolve("delivery-price-relevance", "inconclusive",
    f"net one-way {f(otc['net_one_way'])} EGLD (bar: >300,000); EGLD - BTC = {EGLD_VS_BTC:+.2f}pp",
    f"The 'not evaluable' branch fires: delivery fell to {f(otc['net_one_way'])}, far below the 300,000 bar, so the test cannot say whether delivery moves price. EGLD still lagged BTC by {abs(EGLD_VS_BTC):.1f}pp in a week with almost no delivery. That is weak evidence against the pipeline being the main source of EGLD's relative weakness, though the halt confounds it. Re-registered for the first full week after the chain restarts."))
tests.append(resolve("compound-regime", "against",
    f"compound {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} vs {cvc['claim_count']}), 8 of 8 providers, pre-halt window",
    "The '>= 55%' branch fires, against the claim: the fall below 50% was a one-week reaction to the price reversal, not a switch to taking yield in cash. The regime-shift candidate is rejected under the two-week rule."))
t = dict(prior["fourth-deregistration"]); t.update({"status": "open", "measured_value": "week 3 of 4 on the TRANSITION basis: zero transitions (join now on contract address in the collector, 100% match).", "resolution": None}); tests.append(t)
t = dict(prior["staked-ratio-floor"]); t.update({"status": "open", "measured_value": f"week 1 of 2: {100*M['sr']:.2f}% (settled band); withdraw calls returned {f(WD.get('egld_returned_total',0))} EGLD vs {f(sk['undelegated_week'])} new unDelegations. The halt freezes the ratio until blocks resume.", "resolution": None}); tests.append(t)


def new(tid, claim, threshold, branches, measured):
    return {"id": tid, "registered_in_run": 26, "claim": claim, "threshold": threshold, "branches": branches,
            "status": "open", "outcome": None, "resolved_in_run": None, "measured_value": measured, "resolution": None}


tests += [
    new("halt-recovery-clean", "MultiversX's targeted recovery removes the exploit's invalid balances without reverting legitimate pre-halt history.",
        "at the first snapshot after block production resumes: attacker wallet + contract + 12 fan-out wallets hold < 1,000 EGLD combined AND the pre-halt OTC desk, Binance custody and Hatom EGLD-market balances match this snapshot within 1% = clean targeted recovery; invalid balances gone but legitimate balances changed by > 1% = broader rollback; invalid balances still present = recovery incomplete; chain still halted at run #27 = extended outage",
        [{"condition": "invalid balances < 1,000 EGLD and legitimate balances within 1%", "reading": "clean targeted recovery"},
         {"condition": "invalid balances gone, legitimate balances moved > 1%", "reading": "broader rollback than stated"},
         {"condition": "invalid balances still present after restart", "reading": "recovery incomplete"},
         {"condition": "no block produced by run #27", "reading": "extended outage"}],
        f"halted since {iso(HALT_TS0)}; attacker + contract {f(MINTED_HELD)} EGLD; fan-out {f(HALT['fanout_total_egld'])}; desks {f(otc['desk_bal'])}, custody {f(cust['balance'])}, Hatom EGLD market {f(df['egld_mm_balance'])}"),
    new("unknown-whale-i-is-exchange", "Unknown Whale I (erd1vd76pwhl...q53m3z0) is an exchange hot wallet, not an OTC operator's inventory.",
        "by run #28: its inbound shows > 500 distinct senders in a 7-day window OR an exchange publicly identifies it = exchange hot wallet (relabel and re-attribute the hub history); < 50 distinct senders = operator inventory stands; 50-500 = no conclusion, re-measure",
        [{"condition": "> 500 distinct senders in 7 days, or public identification", "reading": "exchange hot wallet"},
         {"condition": "< 50 distinct senders in 7 days", "reading": "operator inventory"},
         {"condition": "50-500 distinct senders", "reading": "no conclusion"}],
        f"received {f(WHALE_I)} minted EGLD via a one-hop fresh wallet at 07:27 UTC Sep 19; the two-hop back-trace of its inbound hit the 300-transaction page cap in 14 days"),
    new("delivery-price-relevance-2", "Once transfers reopen, OTC delivery is large enough to move EGLD relative to BTC.",
        "in the first full week after exchange EGLD transfers reopen, with net one-way delivery > 300,000: EGLD - BTC < -5pp = price-relevant; >= -5pp = absorbed; delivery <= 300,000 = not evaluable",
        [{"condition": "delivery > 300,000 and EGLD - BTC < -5pp", "reading": "price-relevant supply"},
         {"condition": "delivery > 300,000 and EGLD - BTC >= -5pp", "reading": "absorbed by turnover"},
         {"condition": "delivery <= 300,000", "reading": "not evaluable"}],
        f"re-registered: run #26 delivery {f(otc['net_one_way'])} (not evaluable)"),
]
resolved = [t for t in tests if t.get("resolved_in_run") == 26]
as_pred = sum(1 for t in resolved if t["outcome"] == "as_predicted")
R["pre_committed_tests"] = tests

# ---------------------------------------------------------------------------
R["meta_learning"] = {
    "run_number": 26,
    "endpoints_that_worked": status["ok"],
    "endpoints_that_failed": [
        "NONE with data missing. The halt makes 24h aggregates (xExchange volume, protocol transfers/24h) read zero; that is the state of the chain, not a failed endpoint, and those metrics are marked not evaluable. SWTAO price null all run (supply used)."],
    "api_quirks": [
        "A HALTED CHAIN STILL SERVES A NORMAL-LOOKING API. /economics, /accounts, /providers and /stats all answer; nothing says the chain has stopped. The tells are /stats blocks not advancing between calls and /blocks?shard=N returning a latest timestamp hours old. Check the latest block timestamp at the start of every run.",
        "THE API SERVES INVALID STATE AS BALANCES. After the exploit, /accounts?sort=balance lists a wallet with 41.3M EGLD and a contract with 25.6M, more than the 30.8M /economics total supply, with no flag. Any aggregate built on account balances (exchange flows, whale tiers, top-account deltas) must be checked against total supply before it is narrated.",
        "24H WINDOWS GO TO ZERO DURING A HALT. /mex/pairs volume24h and /accounts/{addr}/transfers/count?after=now-24h read 0 on every pair and contract.",
        "A PAUSED xEXCHANGE PAIR CAN STILL TRADE FOR WHITELISTED CALLERS. addToPauseWhitelist on each pair let Hatom's recovery contract swap while every other caller failed. The whitelist calls are on the router owner's transaction list; the swaps appear only in the pair's /transfers (SC results), not its /transactions.",
        "WITHDRAW AMOUNTS: /transactions/{hash}?withScResults=true carries the EGLD returned to the caller in `results` (receiver == caller). 377 calls decoded in about 90 seconds."],
    "data_gaps": [
        "Flow windows end at the halt: the reporting 'week' is 5.3 days, so weekly series have one short observation.",
        "The exploit's mechanism is described only as a VM-level atomicity issue; the technical report is pending.",
        "Hatom's MEX incident report is not published; LP impact of the whitelisted recovery sales is not measurable without its counterfactual prices.",
        "Order-book depth and CEX volume were read after the halt, with deposits and withdrawals closed at most venues; they are not comparable to last week's baseline.",
        "Unknown Whale I and erd1a6lte0 are unlabelled; if they are exchanges, historical hub traces carry an unnamed venue.",
        "Hatom UTK Money Market and OneDex Launchpad still fail bech32 validation (open since run #18)."],
    "key_findings": [
        f"The chain halted at {iso(HALT_TS0)} after a VM-level exploit minted ~{f(MINTED_TOTAL/1e6,0)}M EGLD of invalid balances through {len(ROUNDS)} doubling deposit/compound rounds; {f(INC_EX_TOT/1e6,2)}M reached three exchanges in three minutes.",
        f"Net of the incident, exchange flow was {ex['net']:+,.0f}, against a raw {ex['net_raw']:+,.0f}.",
        f"The attacker routed {f(WHALE_I)} minted EGLD into Unknown Whale I, so that wallet is probably an exchange hot wallet, not an OTC operator.",
        f"Before the halt the OTC pipeline delivered only {f(otc['net_one_way'])} one-way ({otc['circ_pct']:.0f}% circular); wave #4 netted {f(wave['net_one_way'])}.",
        f"Hatom's MEX recovery sold 270B MEX of seized collateral through whitelisted access to paused pools and refilled its EGLD market to {f(df['egld_mm_balance'])}.",
        f"Compound rate back to {cvc['compound_pct_of_reward_decisions']:.2f}%; withdraw calls returned {f(WD.get('egld_returned_total',0))} EGLD, measured for the first time.",
        "Two lookalike wallets are address-poisoning the pipeline's routers; no misdirected transfer yet."],
    "action_items_from_previous": len(r25["meta_learning"]["recommendations_for_next_run"]),
    "action_items_completed_detail": [
        f"RESOLVE mex-incident-recovery - done: resume calls read from the router owner ({iso(RESUME_TS)}), the recovery contract traced end to end, EGLD market and HMEX measured; resolved as predicted with the contradicting details recorded.",
        "BUILD THE ORDER-BOOK SERIES - done mechanically (week-on-week bid and ask depth for Binance, Bybit, UPbit, Coinbase and Gate) but the second reading was taken after the halt with transfers closed, so it is not a clean WoW comparison.",
        "SEED THE LIQUID-STAKING SWEEP - done: the discovery sweep re-fetches every previously found receipt token and verifies every seed owner; all six protocols returned.",
        f"ADD A 429 GUARD TO THE REWARD-BEHAVIOUR SCRIPT - done: exponential backoff, errors recorded and surfaced in the output (failed providers and an API error count); run after the collector, 8 of 8 providers.",
        f"DECODE WITHDRAW AMOUNTS - done: the follow-up pass decodes all {WD.get('calls',0)} withdraw calls from SC results, {f(WD.get('egld_returned_total',0))} EGLD returned.",
        "RESOLVE THE COMPOUND-REGIME AND DELIVERY-PRICE-RELEVANCE TESTS - done: compound against, delivery not evaluable (re-registered).",
        "JOIN PROVIDERS ON ADDRESS IN THE COLLECTOR - done: the collector keys both snapshots on the contract address and logs identity changes; 100% match, zero renames.",
        "(unplanned) ADDED A TOTAL-SUPPLY AND LIVENESS CHECK TO THE AUDIT GATE: any account above total supply, or a new top account above 5% of it, is an error unless the report documents the incident; verified to fire on this snapshot with the incident section removed."],
    "methodology_changes": [
        "CHECK CHAIN LIVENESS FIRST. Read the latest block timestamp per shard before collecting; a halted chain serves plausible data and every window silently shortens.",
        "CHECK ACCOUNT-BALANCE AGGREGATES AGAINST TOTAL SUPPLY. A single account above total supply is invalid state; net incident balances out of every balance-derived metric and report raw alongside.",
        "AN ATTACKER'S CASH-OUT PATH LABELS EXCHANGE WALLETS. Fresh one-hop wallets forwarding minted funds point at deposit infrastructure; use that to label unnamed high-flow wallets.",
        "READ A PAUSED POOL'S /transfers, NOT ITS /transactions. Whitelisted trades during a pause appear only as SC-result transfers.",
        "DECODE WITHDRAW AMOUNTS EVERY RUN from SC results; report returned EGLD beside new unDelegations."],
    "new_addresses_discovered_detail": [
        {"address": ATT["address"], "label": "MultiversX VM exploit wallet (2026-09-19)", "evidence": f"{len(ROUNDS)} doubling deposit/compound rounds; holds {f(INC['attacker_balance'])} EGLD; fanned out {f(HALT['fanout_total_egld'])}"},
        {"address": HALT["contract"]["address"], "label": "MultiversX VM exploit contract (2026-09-19)", "evidence": f"deployed 06:34 UTC Sep 19 by the exploit wallet; holds {f(INC['contract_balance'])} EGLD"},
        {"address": REC_C, "label": "Hatom: MEX incident recovery contract", "evidence": "deployed by the Hatom deployer Sep 15; redeemed 13.04T HMEX and sold 270B MEX via whitelisted paused pools"},
        {"address": "erd12uv6mj42mv090ucffuuc4pwexrgqfuycegl2rg9j2ah9u20s7dlsmrt5jd", "label": "Hatom: MEX recovery keeper", "evidence": "called runRound 90 times and runCampaignRound 68 times on the recovery contract"},
        {"address": A6, "label": "Probable exchange hot wallet (received 1.63M minted EGLD)", "evidence": "nonce 2,131, many small inbound transfers, destination of two fan-out wallets"}],
    "action_items_completed": 7,
    "new_addresses_discovered": 5,
    "most_valuable_insight": (
        "Checking the numbers against the chain's own limits. The exploit showed up first as an exchange inflow of +4.9M EGLD, which the pipeline would have published as the largest accumulation-onto-exchange event in its history. "
        "It was caught because a single account held more EGLD than the total supply, and then because /stats blocks had not moved between calls. Neither check existed yesterday. Without them, every balance-derived figure in this report would have been wrong, with no sign of it."),
    "top_recommendation": ("AFTER THE RESTART, MEASURE WHAT THE RECOVERY CHANGED. Resolve halt-recovery-clean: attacker, contract and fan-out balances; the pre-halt desk, custody and Hatom balances against this snapshot; the first block's timestamp; exchange transfer status. Then re-run every flow metric on a window that starts at the restart."),
    "recommendations_for_next_run": [
        "CHECK LIVENESS AT COLLECTOR START: latest block per shard; if halted, set the flow-window end to the halt and say so in metadata.",
        "RESOLVE halt-recovery-clean against this snapshot (attacker/contract/fan-out balances; desks, Binance custody, Hatom EGLD market within 1%).",
        "LABEL UNKNOWN WHALE I AND erd1a6lte0: count distinct inbound senders over 7 days with deep paging (the back-trace scan hit its 300-transaction cap in 14 days).",
        "ADD A LIVENESS GATE TO THE COLLECTOR ITSELF (the audit now has one): stop and flag if the latest block on any shard is more than an hour old.",
        "READ HATOM'S INCIDENT REPORT and MultiversX's technical report when published; reconcile against the chain reconstruction.",
        "RE-READ THE ORDER BOOK once exchange transfers reopen; that reading, not this one, is the baseline's second point.",
        "WATCH THE POISONING LOOKALIKES for any inbound above dust."],
    "dashboard_feature_suggestions": [
        {"title": "Chain liveness and incident banner",
         "motivation": "The chain halted at 07:41 UTC Sep 19, and every panel on the dashboard renders this week's halted-state numbers as a normal week. A reader opening the page sees a +2.4% EGLD week and a quiet pipeline, with no sign that the network has been down for 55 hours or that the raw exchange inflow was +4.9M EGLD of minted funds.",
         "suggested_visualization": "a top-of-page status strip: last block per shard with an elapsed-time counter, the raw vs net-of-incident exchange flow side by side, and a link to the incident panel",
         "data_already_available": True, "data_source": "whale_intelligence.chain_halt_incident (new field this run)", "priority": "high"},
        {"title": "Exploit fan-out graph",
         "motivation": "The minted EGLD went attacker -> 12 fresh wallets -> Binance/KuCoin/MEXC/erd1a6lte0/Unknown Whale I in three minutes. That routing is what re-labels Unknown Whale I as a probable exchange, and a table cannot show it.",
         "suggested_visualization": "a left-to-right sankey: attacker wallet and contract on the left, the 12 hop-1 wallets in the middle, destinations on the right, with the unmoved wallets as a terminal node",
         "data_already_available": True, "data_source": "whale_intelligence.chain_halt_incident.fanout_by_destination_egld plus the persisted chain_halt_incident.fanout in the collected snapshot", "priority": "medium"}],
    "dashboard_suggestions_followup": [
        {"title": "Contract-state event timeline - the MEX/WEGLD pause against price and deposits", "status": "built",
         "note": "Built in run #25. This run adds the whitelist and resume calls (token_activity.xexchange.mex_incident_recovery.owner_calls), which the panel could append as markers."},
        {"title": "Pipeline in market scale - delivery as a share of CEX turnover and depth", "status": "built",
         "note": "Built in run #25; this week's order-book point was read after the halt and should be drawn hollow or skipped."},
        {"title": "Feed-side attribution - who fills the desks, not just who they deliver to", "status": "pending",
         "note": "Still queued. If Unknown Whale I is confirmed as an exchange, the venue column needs relabelling first."},
        {"title": "Demand-instrument scorecard", "status": "deprioritized",
         "note": "DEX volume is not evaluable this week and the order book was read in a closed market; the scorecard would show two broken tiles. Revisit after the restart."}],
    "withdrawn_claims": [
        {"claim": "The compound rate's fall below 50% was a switch to taking yield in cash (candidate regime shift).",
         "asserted_in_runs": [25], "withdrawn_in_run": 26,
         "reason": f"The rate returned to {cvc['compound_pct_of_reward_decisions']:.2f}% the next week, the one-week-reaction branch of the registered test.",
         "replacement": "A one-week reaction to the price reversal; the compound series stays in its 57-63% band."},
        {"claim": "Unknown Whale I is an OTC operator's inventory wallet (a pipeline participant on both legs).",
         "asserted_in_runs": [19, 20, 21, 22, 23, 24, 25], "withdrawn_in_run": 26,
         "reason": f"The Sep 19 exploit wallet routed {f(WHALE_I)} minted EGLD into it through a fresh one-hop wallet, the same pattern it used for Binance.com, KuCoin and MEXC deposits.",
         "replacement": "Probably an exchange hot wallet; confirmation registered as the unknown-whale-i-is-exchange test. Past hub totals are unchanged; only the venue label would change."}],
}

rep = {}
rep.update(R)
order = ["metadata", "executive_summary", "network_health", "whale_intelligence", "staking_intelligence", "token_activity",
         "defi_activity", "anomalies", "trend_indicators", "watch_list", "meta_learning", "pre_committed_tests"]
rep = {k: rep[k] for k in order}
json.dump(rep, open(f"{REPO}/reports/{RD}.json", "w"), indent=1, default=str)
print("report written", len(json.dumps(rep, default=str)), "bytes")
print(f"tests resolved this run {len(resolved)}, as_predicted {as_pred}, open {sum(1 for t in tests if t['status']=='open')}")
