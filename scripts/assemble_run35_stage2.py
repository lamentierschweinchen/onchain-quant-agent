#!/usr/bin/env python3
"""Run #35 stage 2: z-scores, narrative, trends, tests, meta_learning. Reads stage1.json, writes reports/2026-11-02.json."""
import json, statistics, copy
REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
S = "/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/c0752602-bed0-4149-acb9-643dfdca7616/scratchpad"
RD = "2026-11-02"
R = json.load(open(f"{S}/stage1.json")); D = json.load(open(f"{S}/digest35.json"))
c = json.load(open(f"{REPO}/data/collected/{RD}.json")); pv = json.load(open(f"{REPO}/data/previous.json"))
r0 = json.load(open(f"{REPO}/reports/2026-10-26.json")); L = json.load(open(f"{REPO}/data/learnings.json"))
rb = L["runs"][-1]["running_baselines"]
price, pc, rel = D["price"], D["pc"], D["rel"]
def z(key, cur):
    arr = rb[key][-8:]
    if len(arr) < 4: return None
    sd = statistics.pstdev(arr); m = statistics.mean(arr)
    return (cur - m) / sd if sd else None, m, sd
def sev(zv):
    a = abs(zv); return "critical" if a > 4 else "high" if a > 3 else "medium" if a > 2 else None

# ---- baselines (this run's values)
mexp = c["mex_economics"]["price"]
BASE = {"egld_price_usd": price, "dex_volume_24h_usd": D["vol24"], "dex_volume_24h_egld": D["vol24"] / price, "staked_egld": D["staked"],
        "mex_price_usd": mexp, "total_delegators": D["dl"], "staked_ratio": D["ratio"], "korea_premium_pct": round(D["prem"], 1),
        "exchange_net_flow_egld": D["net"], "binance_staking_custody_egld": D["chg"]["Binance Staking"] + pv["exchange_balances"]["Binance Staking"],
        "usdt_supply": 413975, "usdc_supply": 7176244}
json.dump(BASE, open(f"{S}/baselines35.json", "w"))

anoms = []
for key, label, fmt in (("egld_price_usd", "egld_price_usd", "price"), ("dex_volume_24h_usd", "dex_volume_24h_usd", "dex"),
                         ("staked_egld", "staked_egld", "staked"), ("total_delegators", "total_delegators", "deleg"),
                         ("mex_price_usd", "mex_price_usd", "mex")):
    cur = BASE[key]; out = z(key, cur)
    if not out: continue
    zv, m, sd = out; s = sev(zv)
    if s:
        anoms.append({"metric": label, "current_value": cur, "average_value": m, "stddev": sd, "z_score": zv, "method": "z_score", "severity": s,
                      "change_pct": (cur - rb[key][-1]) / rb[key][-1] * 100,
                      "description": f"{label} {cur:,.6g} vs 8-run mean {m:,.6g} (z = {zv:+.2f})."})
zdx = z("dex_volume_24h_usd", D["vol24"]); zp = z("egld_price_usd", price); zd = z("total_delegators", D["dl"])
anoms.append({"metric": "exchange_net_flow_egld", "current_value": D["net"], "previous_value": -32129, "method": "rule_based", "severity": "medium",
    "description": f"Tracked exchange wallets lost {abs(D['net']):,.0f} EGLD; KuCoin (-149,563) and MEXC (-54,886) are 99% of it. The Binance hot -> custody send (309,906, Oct 29) nets to zero inside the tracked set."})
anoms.append({"metric": "korea_premium_pct", "current_value": D["prem"], "previous_value": 20.55, "method": "rule_based", "severity": "medium",
    "description": f"Upbit $3.87 vs Binance $3.39: premium {D['prem']:.1f}% (from 20.6%), Upbit share of 24h volume {D['up_share']:.0f}% (from 90%). Bithumb trades at $4.06. Rule-based: no weekly baseline."})
anoms.append({"metric": "egld_minus_btc_pp", "current_value": rel, "previous_value": -8.54, "method": "rule_based", "severity": "low",
    "description": f"EGLD {pc:+.2f}% vs BTC {D['btc_wow']:+.2f}% (+{rel:.1f}pp) after -8.5pp last window; first window ahead of BTC with exchange outflow."})
dxp = (D["vol24"] - 129917.01) / 129917.01 * 100
anoms.append({"metric": "dex_volume_24h_usd_wow", "current_value": D["vol24"], "previous_value": 129917.01, "method": "percent_threshold", "severity": "low",
    "change_pct": dxp, "description": f"DEX 24h volume ${D['vol24']:,.0f} ({dxp:+.1f}% WoW); 24h snapshots are noisy, z = {zdx[0]:+.2f} on the 8-run baseline."})
R["anomalies"] = anoms

# ---- narrative
chg = D["chg"]
R["network_health"]["analysis"] = (
 f"WINDOW. 7.0 days (Oct 26 14:23 -> Nov 2 16:03 UTC); all four shards read live within 3 seconds. Epoch {R['network_health']['activity']['epoch']}, "
 f"{R['network_health']['activity']['transactions_7d']:,} transactions, {R['network_health']['deltas']['accounts_added']:,} new accounts. This is the first full 7-day window since run #32.\n\n"
 f"PRICE. EGLD ${price:.2f}, {pc:+.2f}% against BTC {D['btc_wow']:+.2f}% and ETH {D['eth_wow']:+.2f}%: EGLD {rel:+.1f}pp ahead of BTC, a full reversal of last window's -8.5pp. It rose while tracked exchanges lost EGLD.\n\n"
 f"STAKING. Staked EGLD {D['staked']:,.0f} ({D['dstaked']:+,.0f}); ratio {D['ratio']*100:.2f}% (flat). Network APR {c['economics']['apr']*100:.2f}%. After last window's forecast Binance step, staking is back to its pre-Oct-22 plateau.")
ex = R["whale_intelligence"]["exchange_flows"]
R["whale_intelligence"]["analysis"] = (
 f"EXCHANGE BOOKS SHRANK. Tracked exchange wallets hold {D['tot_c']:,.0f} EGLD, {D['net']:+,.0f} ({D['net']/D['tot_p']*100:+.2f}%). Two venues explain it: KuCoin -149,563 (155,756 out, 6,193 in; its book fell from 205,330 to 55,768) and MEXC -54,886 (no deposits). Bybit -20,136. Crypto.com, Coinbase and Gate.io each gained 6-7K.\n\n"
 "BINANCE MOVED ITS OWN EGLD, NOT CUSTOMERS'. On Oct 29 the Binance.com hot wallet sent 309,906 EGLD to Binance Staking custody (now 4,284,611). Both wallets are tracked, so the move nets to zero. Customer flow at Binance.com was balanced: 72,137 deposited, 73,480 withdrawn ex custody. The 320,000 EGLD returned to custody on Oct 22 has not moved (0 outbound, 0 to the hot wallet, 0 re-delegated): binance-custody-hold resolves 'held'. Custody now holds 4.28M EGLD unstaked, the largest idle balance on the chain.\n\n"
 "TIERS. Mega whales +309,940 (the same internal move); large whales -25,820; mid whales -186,495 on a common-address basis, driven by exchange wallets (KuCoin, MEXC, Bybit) shrinking through tier lines.\n\n"
 "EXITS. Two provider withdrawals above 3,000 EGLD (orangestaking 10,994, ninjastaking 10,450): both re-delegated (the first into vaporrepublic). None went to an exchange. Mega Whale (1,219,231) and Whale B (181,822) did not move.")
R["staking_intelligence"]["analysis"] = (
 f"FLAT. {c['undelegate_callers_count']} wallets unDelegated {c['undelegated_this_week_total_egld']:,.0f} EGLD (unbonding pool {c['unbonding_pool_total_egld']:,.0f}), against {D['dstaked']:+,.0f} net change in staked EGLD. Delegators {D['dl']:,} ({D['dl']-D['dlp']:+,}, {(D['dl']-D['dlp'])/D['dlp']*100:+.2f}%); {R['staking_intelligence']['churn']['providers_gaining_delegators']} providers gained, {R['staking_intelligence']['churn']['providers_losing_delegators']} lost. "
 f"The delegator base has now slipped for nine straight weekly readings ({rb['total_delegators'][0]:,} -> {D['dl']:,} over the baseline). Concentration unchanged: HHI {D['hhi']:.5f}, top-5 {D['top5']:.2f}%. "
 "Biggest provider moves: ninjastaking -14,861 (its fee-1% book keeps leaving), vaporrepublic +10,683, equinoxecapital +7,292. Capital rotates between providers; the people do not leave.")
R["token_activity"]["analysis"] = (
 f"DEX VOLUME HALVED. 24h xExchange volume ${D['vol24']:,.0f} ({dxp:+.1f}% vs ${129917:,}); in EGLD {D['vol24']/price:,.0f}. Pair TVL ${D['tvl']:,.0f}. A single 24h snapshot is noisy (z = {zdx[0]:+.2f}). "
 f"MEX ${mexp:.3e}, market cap ${c['mex_economics']['marketCap']:,.0f}. WrappedUSDC supply 7,176,244 (-0.44%), USDT 413,975 (-2.71%): the stablecoin base contracted again. "
 f"Newly issued tokens this window: {len(R['token_activity']['newly_issued'])} with holders (all are single-holder deployments).")
R["defi_activity"]["analysis"] = (
 "Hatom's EGLD money market saw 166 calls: 86 mintAndEnterMarket (22 wallets), 30 borrow (17 wallets), 22 repayBorrow, 16 redeem (15 from one wallet) and 0 liquidations. Suppliers outnumber borrowers; no liquidation pressure at +3.7% price. "
 "XOXNO aggregator 10,322 transfers/24h, OneDex 3,840, Hatom Liquid Staking 535. USDC bridge: 22 unwraps (34,225 USDC, 91% to BSC) vs 19 wraps (2,292): net USDC leaving through the xBridge wrapper. Protocol TVL percentages are not restated this run (tracked-contract balances were not re-collected); only DEX and transfer counts are fresh.")

# ---- exec summary
R["executive_summary"] = [
 {"category": "network", "severity": "medium", "finding": f"EGLD ROSE {pc:.1f}% TO ${price:.2f} AGAINST BTC {D['btc_wow']:.1f}%. +{rel:.1f}pp relative, reversing last window's -8.5pp, while tracked exchanges lost 205,817 EGLD."},
 {"category": "whale", "severity": "medium", "finding": "EXCHANGE BOOKS SHRANK 3.0%, ALMOST ALL FROM TWO VENUES. KuCoin -149,563 (73% of its book; backlog release from the halt) and MEXC -54,886. Binance customer flow was balanced; its 309,906 hot -> custody send on Oct 29 is internal."},
 {"category": "whale", "severity": "high", "finding": "BINANCE STAKING CUSTODY IS 4.28M IDLE EGLD. The 320,000 returned Oct 22 has not moved and the hot wallet added another 309,906. binance-custody-hold resolves 'held'; the open risk is that this balance is large and unstaked."},
 {"category": "token", "severity": "medium", "finding": f"KOREA PREMIUM FELL TO {D['prem']:.1f}% FROM 20.6%. Upbit $3.87 vs Binance $3.39; Upbit's share of volume dropped to {D['up_share']:.0f}% (from 90%). Upbit's decision is still due Nov 16-20."},
 {"category": "staking", "severity": "low", "finding": f"STAKING FLAT: {D['dstaked']:+,.0f} EGLD, ratio 44.73%. Delegators 171,641 (-384), nine readings of decline. 58,797 EGLD unDelegated by 137 wallets; nothing to an exchange."},
 {"category": "defi", "severity": "low", "finding": f"DEX VOLUME ${D['vol24']:,.0f}/24h ({dxp:+.0f}%); stablecoin supply contracted again (USDC -0.44%, USDT -2.71%). Hatom EGLD market: no liquidations."},
 {"category": "trend", "severity": "medium", "finding": "outflow-bottom resolves 'bottoming': exchanges net -205,817 and EGLD +7.2pp vs BTC. One window; the price leg needs a repeat."},
]

# ---- trends
ti = R["trend_indicators"]
ti["accelerating_exchange_outflows"] = [
 {"exchange": "KuCoin", "trend": "outflow", "cumulative_change_pct": (55768 - 220076) / 220076 * 100, "weeks_in_trend": 2,
  "interpretation": "Second week of outflow: -14,746 then -149,563. The backlog is large and not yet exhausted at 55,768 remaining."},
 {"exchange": "MEXC", "trend": "outflow", "cumulative_change_pct": chg["MEXC"] / 110883 * 100, "weeks_in_trend": 1,
  "interpretation": "First big outflow since the halt: -54,886 with zero deposits."}]
ti["validator_movements"] = {"providers_joining": 0, "providers_leaving": 0, "net_provider_change": 0, "notable_joiners": [], "notable_leavers": [], "note": "No joins or deregistrations for a twelfth week (106 providers)."}
ti["token_supply_events"] = [
 {"identifier": "USDC-c76f1f", "name": "WrappedUSDC", "event": "burn", "supply_previous": "7208177", "supply_current": "7176244", "change_pct": -0.443, "description": "-31,933 USDC; fifth contraction in six readings. Bridge unwraps 34,225 vs wraps 2,292."},
 {"identifier": "USDT-f8c08c", "name": "USDT", "event": "burn", "supply_previous": "425495", "supply_current": "413975", "change_pct": -2.707, "description": "-11,520 USDT, reversing last week's +17,745 mint."}]
dlarr = rb["total_delegators"] + [D["dl"]]
streak = 0
for i in range(len(dlarr) - 1, 0, -1):
    if dlarr[i] < dlarr[i - 1]: streak += 1
    else: break
ti["consecutive_streaks"] = [
 {"metric": "total_delegators", "direction": "down", "weeks": streak, "cumulative_change_pct": (D["dl"] - dlarr[-streak - 1]) / dlarr[-streak - 1] * 100,
  "interpretation": f"{D['dl']:,} ({D['dl']-D['dlp']:+,}); a slow bleed of roughly 100-400 per window against a steady plateau of capital."},
 {"metric": "korea_premium", "direction": "down", "weeks": 1, "cumulative_change_pct": None, "interpretation": "20.6% -> 14.2% after three widening readings."},
 {"metric": "egld_vs_btc", "direction": "up", "weeks": 1, "cumulative_change_pct": None, "interpretation": f"+{rel:.1f}pp after -8.5pp."},
 {"metric": "provider_operator_fee_selling", "direction": "flat", "weeks": 23, "cumulative_change_pct": 0.0, "interpretation": "See reward behavior section; no exchange destinations from sampled operator wallets."}]
ti["regime_shifts"] = [
 {"metric": "binance_staking_custody_egld", "before_value": 3974671.46, "after_value": 4284611.45, "description": "Custody balance stepped +309,940 from the Binance.com hot wallet (Oct 29). It now holds 4.28M EGLD unstaked; it is no longer a flat series."},
 {"metric": "kucoin_book_egld", "before_value": 205330.21, "after_value": 55768.0, "description": "KuCoin's EGLD book fell 73% in one window as the post-halt backlog left."}]

# ---- watch list
R["watch_list"] = [
 {"item": "UPBIT CAUTION REVIEW - decision Nov 16-20", "weeks_on_list": 9, "reason": f"Premium {D['prem']:.1f}% (from 20.6%), Upbit share {D['up_share']:.0f}%. UPbit's wallet moved no EGLD (1,055,326). PRE-COMMITTED (upbit-premium-on-decision). Record premium and volume share every run until Nov 20; Bithumb ($4.06) decision still not found."},
 {"item": "BINANCE STAKING CUSTODY 4.28M", "weeks_on_list": 3, "reason": "Received 320,000 (Oct 22) and 309,906 (Oct 29); 0 outbound, 0 re-delegated. 'held' resolved; watch for the first outbound or delegate call."},
 {"item": "KUCOIN BACKLOG", "weeks_on_list": 2, "reason": "55,768 left after -149,563. PRE-COMMITTED (kucoin-backlog-decay)."},
 {"item": "MEXC OUTFLOW", "weeks_on_list": 1, "reason": "-54,886 with no deposits; 55,997 left."},
 {"item": "EXCHANGE FLOW + PRICE BOTTOM", "weeks_on_list": 5, "reason": "outflow-bottom resolved 'bottoming' on one window. PRE-COMMITTED (bottom-confirms) for run #36."},
 {"item": "WALLETS FROM RUN #34", "weeks_on_list": 2, "reason": "erd1qyt62v5ndd (25,698 unstaked) and erd1ygkh9r65 (27,084 from Binance) both still hold; no sale visible."},
 {"item": "SELLER CHAIN erd1hl5y4a", "weeks_on_list": 4, "reason": "221,315 EGLD; sent small clips (about 200-300 EGLD each) to erd12h90ev through the end of the window; 0 to Binance directly."},
 {"item": "OTC PIPELINE", "weeks_on_list": 35, "reason": "Quiet: desk gross under 100. UPbit OTC desk 26,874. Keep until Upbit's decision."},
 {"item": "EXPLOIT WALLET AND POISONING RING", "weeks_on_list": 10, "reason": "Exploit wallet 2.5 EGLD; poisoning lookalikes zero balances."}]

# ---- tests
T = R["pre_committed_tests"]
def find(i): return next(t for t in T if t["id"] == i)
t = find("outflow-bottom"); t.update({"status": "resolved", "outcome": "as_predicted", "resolved_in_run": 35,
  "measured_value": f"net {D['net']:+,.0f} EGLD; EGLD {pc:+.2f}% vs BTC {D['btc_wow']:+.2f}% = {rel:+.1f}pp",
  "resolution": "Bottoming branch fired: exchanges net <= 0 and EGLD ahead of BTC. Caveats: 99% of the outflow is KuCoin and MEXC (one-off backlogs, not a trend), and the Binance internal move was inside the tracked set so it nets out. One window."})
t = find("binance-custody-hold"); t.update({"status": "resolved", "outcome": "as_predicted", "resolved_in_run": 35,
  "measured_value": "custody 4,284,611; 0 outbound txs, 0 to the hot wallet, 0 re-delegated since Oct 22",
  "resolution": "'Held' branch fired. The custody also received 309,906 from the hot wallet on Oct 29, which is outside the test but raises the idle balance."})
find("delivery-price-relevance-2").update({"measured_value": "run #35: desk gross under 100 EGLD, no UPbit delivery. Not evaluable."})
find("upbit-premium-on-decision").update({"measured_value": f"run #35: premium {D['prem']:.1f}%, Upbit {D['up_share']:.0f}% of volume, UPbit wallet idle; decision due Nov 16-20."})
T.append({"id": "kucoin-backlog-decay", "registered_in_run": 35, "claim": "KuCoin's outflow is a backlog release that decays.",
  "threshold": "KuCoin wallet net flow over run #36's window (balance basis): net outflow < 20,000 = decayed; > 50,000 = continuing; otherwise no conclusion",
  "branches": [{"condition": "outflow < 20K", "reading": "backlog exhausted"}, {"condition": "outflow > 50K", "reading": "open rail with ongoing sellers"}, {"condition": "otherwise", "reading": "no conclusion"}],
  "status": "open", "outcome": None, "resolved_in_run": None, "measured_value": "run #35: -149,563 (book 55,768)", "resolution": None})
T.append({"id": "bottom-confirms", "registered_in_run": 35, "claim": "The bottoming read holds in the next window.",
  "threshold": "Over run #36's window: tracked exchanges net <= +10,000 ex internal moves AND EGLD - BTC >= -2pp = confirms; net > +10,000 AND EGLD - BTC < -2pp = failed; otherwise no conclusion",
  "branches": [{"condition": "net <= +10K and EGLD-BTC >= -2pp", "reading": "confirms"}, {"condition": "net > +10K and EGLD-BTC < -2pp", "reading": "failed"}, {"condition": "otherwise", "reading": "no conclusion"}],
  "status": "open", "outcome": None, "resolved_in_run": None, "measured_value": "run #35: net -205,817, +7.2pp", "resolution": None})

# ---- meta learning
ml = R["meta_learning"]
ml.update({"run_number": 35, "endpoints_that_failed": ["1 HTTP 429 on one Coinbase Custody 2 receiver count (non-critical)."],
 "api_quirks": ["A move between two tracked wallets (Binance hot -> custody) shows as +309,940 and -311,249 in the per-wallet table; net it at the entity level before reading customer flow. Venue label matching must avoid double counting the two 'Binance.com' wallets.",
                "/economics `staked` equals the staking module balance; custody receipts do not move it, so custody inflows never show up as a staking change."],
 "data_gaps": ["Protocol-level TVL WoW percentages were not restated this run (tracked contract balances not re-collected).", "Bithumb decision not found.", "OTC pipeline sections not refreshed (desk gross under 100 EGLD)."],
 "key_findings": [e["finding"] for e in R["executive_summary"][:5]],
 "action_items_from_previous": 6, "action_items_completed": 4,
 "action_items_completed_detail": ["binance-custody-hold resolved (held).", "outflow-bottom resolved (bottoming).", "Hatom loop scan: counted borrow/redeem activity (30 borrows by 17 wallets, 0 liquidations); the swap-then-supply join was not built.", "erd1qyt62v5ndd (25,698) and erd1ygkh9r65 (27,084) re-read: both still hold."],
 "methodology_changes": ["Lean assembler (assemble_run35_report.py + stage2) replaces the 8-script chain; bespoke sections not re-collected are dropped rather than carried stale.", "Internal moves between two tracked wallets are netted at entity level (Binance)."],
 "new_addresses_discovered_detail": [], "new_addresses_discovered": 0,
 "most_valuable_insight": "Exchange outflow and price moved in opposite directions again, but the outflow was two venues' halt backlogs (KuCoin, MEXC), not a market-wide exit; Binance's own 309,906 hot -> custody move would have read as a 311K outflow without entity netting.",
 "top_recommendation": "RUN #36 FIRST: resolve kucoin-backlog-decay and bottom-confirms; record the Upbit premium; check Binance custody for its first outbound.",
 "recommendations_for_next_run": [
  "Resolve kucoin-backlog-decay and bottom-confirms on run #36's window (balance basis, internal moves netted).",
  "Binance custody erd1rf4hv70: any outbound or delegate call? 4.28M is idle.",
  "Record the Upbit premium and volume share every run until Nov 20; search Bithumb's decision.",
  "Re-collect protocol TVL balances so per-protocol WoW is restated; build the Hatom borrow -> swap -> supply join.",
  "Per-day KuCoin and MEXC withdrawal counts to see whether the outflows decay or stay open.",
  "Trace where the 154K KuCoin withdrawals went (CEX, DEX, or staking)."],
 "dashboard_feature_suggestions": [
  {"title": "Entity-netted exchange flow bridge", "motivation": "Binance's 309,906 hot -> custody send reads as -311K at Binance.com and +310K at custody in the per-wallet table; only the entity table shows it nets out.", "suggested_visualization": "waterfall: per-wallet changes -> internal moves -> customer net, by entity", "data_already_available": True, "data_source": "whale_intelligence.exchange_flows.by_exchange + entity_netting", "priority": "medium"},
  {"title": "Exchange book depletion timeline", "motivation": "KuCoin's book went 205K -> 56K and MEXC's 111K -> 56K in a week; a single-week table cannot show a venue approaching empty.", "suggested_visualization": "small multiples of per-venue EGLD balance over runs with a remaining-weeks-at-current-pace marker", "data_already_available": True, "data_source": "previous.json exchange_balances history in data/collected snapshots", "priority": "medium"}],
 "dashboard_suggestions_followup": [
  {"title": "Staked-EGLD change waterfall", "status": "pending", "reason": "Not built; this run's staking change was small (+19,607) so the need is lower."},
  {"title": "Hatom leverage-loop tracker", "status": "pending", "reason": "Needs the swap-then-supply join, still not collected."},
  {"title": "Fixed test-window overlay on the price chart", "status": "deprioritized", "reason": "outflow-bottom resolved on balances plus spot price; low value."}],
 "self_assessment": {}})
R["meta_learning"]["endpoints_that_worked"] = ml.get("endpoints_that_worked", [])[:40]

json.dump(R, open(f"{REPO}/reports/{RD}.json", "w"), indent=1, default=str)
print("wrote reports/2026-11-02.json")
