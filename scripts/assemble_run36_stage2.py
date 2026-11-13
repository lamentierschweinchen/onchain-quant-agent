#!/usr/bin/env python3
"""Run #36 stage 2: z-scores, narrative, trends, tests, meta_learning. Reads stage1.json, writes reports/2026-11-09.json."""
import json, statistics, copy, sys
sys.path.insert(0, "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/scripts")
from report_template import load_previous
REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
S = "/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/174a0ac3-37e6-4a71-9596-a35c3cbb3939/scratchpad"
RD = "2026-11-09"
R = json.load(open(f"{S}/stage1.json")); D = json.load(open(f"{S}/digest36.json"))
c = json.load(open(f"{REPO}/data/collected/{RD}.json")); pv = load_previous(RD)
r0 = json.load(open(f"{REPO}/reports/2026-11-02.json")); L = json.load(open(f"{REPO}/data/learnings.json")); L["runs"] = [x for x in L["runs"] if x["date"] < RD]
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
        "usdt_supply": 381086, "usdc_supply": 7119153}
json.dump(BASE, open(f"{S}/baselines36.json", "w"))

NICE = {"egld_price_usd": "EGLD price (USD)", "dex_volume_24h_usd": "DEX 24h volume (USD)", "staked_egld": "Staked EGLD", "total_delegators": "Delegator count", "mex_price_usd": "MEX price (USD)"}
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
                      "description": f"{NICE.get(label,label)} {cur:,.6g} vs 8-run mean {m:,.6g} (z = {zv:+.2f})."})
zdx = z("dex_volume_24h_usd", D["vol24"]); zp = z("egld_price_usd", price); zd = z("total_delegators", D["dl"])
anoms.append({"metric": "binance_native_rail", "current_value": 0, "previous_value": 145617, "method": "rule_based", "severity": "high",
    "description": "Binance.com recorded 0 native EGLD deposits and 0 withdrawals in a 7-day window (run #35: 72,137 in / 73,480 out). The hot wallet erd1sdslvl last moved on Oct 29 23:05 UTC, when it swept 309,906 to custody and kept 3 EGLD. Spot trading continues. No announcement found."})
anoms.append({"metric": "exchange_net_flow_egld", "current_value": D["net"], "previous_value": -205817, "method": "rule_based", "severity": "medium",
    "description": f"Tracked exchange wallets lost {abs(D['net']):,.0f} EGLD with Binance shut: KuCoin -40,396, Bybit -16,734, MEXC -15,014, Gate.io -8,015. A third straight net outflow did not lift the price (EGLD {pc:+.1f}%)."})
anoms.append({"metric": "korea_premium_pct", "current_value": D["prem"], "previous_value": 14.2, "method": "rule_based", "severity": "medium",
    "description": f"Upbit $3.50 vs Binance $2.99: premium {D['prem']:.1f}% (from 14.2%); Upbit {D['up_share']:.0f}% of 24h volume (from 43%). Bithumb $3.73. Rule-based: no weekly baseline."})
anoms.append({"metric": "egld_minus_btc_pp", "current_value": rel, "previous_value": 7.2, "method": "rule_based", "severity": "medium",
    "description": f"EGLD {pc:+.2f}% vs BTC {D['btc_wow']:+.2f}% ({rel:+.1f}pp), giving back last window's +7.2pp. ETH {D['eth_wow']:+.1f}%."})
dxp = (D["vol24"] - 66892.02) / 66892.02 * 100
anoms.append({"metric": "dex_volume_24h_usd_wow", "current_value": D["vol24"], "previous_value": 66892.02, "method": "percent_threshold", "severity": "low",
    "change_pct": dxp, "description": f"DEX 24h volume ${D['vol24']:,.0f} ({dxp:+.1f}% WoW) after last week's low; WEGLD/USDC is 93% of it. z = {zdx[0]:+.2f} on the 8-run baseline. Degraded mode for the WoW read."})
R["anomalies"] = anoms


# ---- narrative
chg = D["chg"]; T36 = c["run36_traces"]; si = R["staking_intelligence"]; ch = si["churn"]
act = R["network_health"]["activity"]; dl_ = R["network_health"]["deltas"]
R["network_health"]["analysis"] = (
 f"WINDOW. 7.05 days (Nov 2 16:03 -> Nov 9 17:19 UTC); all four shards live. Epoch {act['epoch']}, {act['transactions_7d']:,} transactions "
 f"({act['avg_daily_transactions']:,}/day), {dl_['accounts_added']:,} new accounts. Supply +{dl_['supply_added']:,.0f} EGLD (the weekly emission; the two growth funds took +11,426 each).\n\n"
 f"PRICE. EGLD ${price:.2f}, {pc:+.2f}% against BTC {D['btc_wow']:+.2f}% and ETH {D['eth_wow']:+.2f}%: {rel:+.1f}pp vs BTC, giving back last window's +7.2pp. "
 f"Market cap ${c['economics']['marketCap']/1e6:,.1f}M. Lowest weekly reading since Aug 17 ($2.76); the June-August range was $2.55-3.16.\n\n"
 f"STAKING. Staked EGLD {D['staked']:,.0f} ({D['dstaked']:+,.0f}); ratio {D['ratio']*100:.2f}%. Network APR {c['economics']['apr']*100:.2f}%. Flat.")
R["whale_intelligence"]["analysis"] = (
 "BINANCE'S NATIVE RAIL WENT DARK. No Binance wallet moved EGLD in the window: 0 deposits, 0 withdrawals (run #35: 72,137 in, 73,480 out). "
 "The hot wallet erd1sdslvl last transacted on Oct 29 23:05 UTC, when it swept 309,906 EGLD to Binance Staking custody and kept 3 EGLD. Its daily rail was live every day from Oct 9 to Oct 29. "
 "Fifteen of its last depositors have sent nothing anywhere since Oct 30, so this is a paused rail, not a new deposit address. Binance still trades EGLD spot ($2.99, about $420K/24h). No Binance announcement was found. "
 "Binance custody (4,284,611) did not move: no outbound, no delegate.\n\n"
 f"OTHER BOOKS KEPT SHRINKING. Tracked exchange wallets {D['tot_c']:,.0f} EGLD, {D['net']:+,.0f} ({D['net']/D['tot_p']*100:+.2f}%): KuCoin -40,396, Bybit -16,734, MEXC -15,014 (withdraw-only for a second week), Gate.io -8,015, Coinbase -3,501. No venue gained.\n\n"
 "THE KUCOIN BACKLOG WAS ONE WALLET. erd15ku2r2j6 deposited 145,443 EGLD into KuCoin on Jul 19, withdrew 136,359 on Oct 30 and 32,000 on Nov 3, and now holds 168,358. It has not sold or delegated. "
 "That one wallet is 85% of the 197,857 EGLD KuCoin paid out since Oct 26 (receivers of withdrawals >= 100 EGLD). Without it, KuCoin's withdrawals ran 2,700-5,000 EGLD a day on Nov 1-6 and fell under 400 on Nov 7-9. "
 "A lookalike address (erd1tyfnsaztln, mimicking KuCoin's erd1ty4pvm) has been sending it zero-value transfers: an address-poisoning attempt on a 168K wallet.\n\n"
 "OTC INVENTORY MOVED, INTERNALLY. Unknown Whale I (OTC operator inventory) sent 112,634 to erd1drc22z7h on Nov 5. That wallet sends clips of 1,500-3,200 EGLD back to Whale I twice a day: a vault, not a buyer. It also receives poisoning dust from a lookalike (erd1vdpfqqjaah).\n\n"
 f"TIERS. Mega whales flat; large whales {D['WT']['large_whales'][2]:+,.0f} (the KuCoin withdrawer); mid whales {D['WT']['mid_whales'][2]:+,.0f} on a common-address basis (Whale I's vault transfer plus KuCoin, MEXC and Gate.io wallets shrinking).\n\n"
 "EXITS. Five provider withdrawals above 3,000 EGLD: two held, one re-delegated, one to DeFi, one to a wallet. None went to an exchange. Mega Whale (1,219,231) and Whale B (181,822) did not move.")
R["staking_intelligence"]["analysis"] = (
 f"FLAT. {c['undelegate_callers_count']} wallets unDelegated {c['undelegated_this_week_total_egld']:,.0f} EGLD; 257 withdraw calls returned 72,314. Staked {D['dstaked']:+,.0f}. "
 f"Delegators {D['dl']:,} ({D['dl']-D['dlp']:+,}): {ch['providers_gaining_delegators']} providers gained, {ch['providers_losing_delegators']} lost. The decline continued but nearly stopped (-30, after -384). "
 f"HHI {D['hhi']:.5f}, top-5 {D['top5']:.2f}%. Biggest movers across all providers: pi-staking +28,139, ninjastaking +8,866, equinoxecapital -7,878, valuestaking -4,645. A -11.5% price week did not produce an unstaking wave.")
R["token_activity"]["analysis"] = (
 f"DEX VOLUME RECOVERED. 24h xExchange volume ${D['vol24']:,.0f} ({dxp:+.1f}% vs $66,892); WEGLD/USDC 93% of it. Pair TVL ${D['tvl']:,.0f}. "
 f"MEX ${mexp:.3e} ({R['token_activity']['xexchange']['mex_price_change_wow_pct']:+.1f}%). "
 "Stablecoins kept contracting: WrappedUSDC 7,119,153 (-0.80%), USDT 381,086 (-7.94%). "
 "One new token this window (DIRHEM, one holder).")
R["defi_activity"]["analysis"] = (
 "TVL RESTATED (run #35 rec #4), two-week basis vs Oct 26: Hatom Lending $5.86M (-0.6% USD, +8.3% in EGLD terms because most collateral is stablecoins), Hatom Liquid Staking $3.45M (-9.1% USD, -1.0% EGLD), XOXNO LSD $0.70M (-8.6% USD, -0.4% EGLD), USH $0.62M (flat). "
 "Liquid-staking token supplies barely moved (Hatom 682,653 vs 680,134; XOXNO 205,113 vs 206,866): the USD drop is price, not exits. "
 "Hatom's EGLD money market: 48 repayments, 47 supply-and-collateralize calls, 32 borrows (13 wallets), 12 redemptions and 0 liquidations at -11.5%. "
 "USDC bridge: 33 unwraps (99,720 USDC, 81% to BSC) vs 48 wraps (40,629): net USDC still leaving through the xBridge wrapper.")

R["executive_summary"] = [
 {"category": "whale", "severity": "high", "finding": "BINANCE'S NATIVE EGLD RAIL WENT DARK FOR THE WHOLE WINDOW. 0 deposits and 0 withdrawals; the hot wallet has not moved since it swept 309,906 EGLD to custody on Oct 29 and kept 3 EGLD. Spot trading continues. No announcement found."},
 {"category": "network", "severity": "medium", "finding": f"EGLD FELL {abs(pc):.1f}% TO ${price:.2f} AGAINST BTC {D['btc_wow']:.1f}% ({rel:+.1f}pp). It gave back all of last window's +7.2pp."},
 {"category": "whale", "severity": "medium", "finding": f"EXCHANGE BOOKS LOST ANOTHER {abs(D['net']):,.0f} EGLD AND PRICE STILL FELL. KuCoin -40,396, Bybit -16,734, MEXC -15,014 (withdraw-only), Gate.io -8,015. Outflow is not bullish while the largest venue's rail is shut."},
 {"category": "whale", "severity": "medium", "finding": "THE KUCOIN 'BACKLOG' WAS ONE WALLET. erd15ku2r2j6 deposited 145,443 in July and withdrew 168,359 after the halt (Oct 30 and Nov 3). It holds all of it and is being targeted by an address-poisoning lookalike."},
 {"category": "token", "severity": "medium", "finding": f"KOREA PREMIUM WIDENED TO {D['prem']:.1f}% (FROM 14.2%). Upbit $3.50 vs Binance $2.99, but Upbit's share of volume fell to {D['up_share']:.0f}%. Upbit's decision is due Nov 16-20."},
 {"category": "staking", "severity": "low", "finding": f"STAKING HELD THROUGH THE DROP: {D['dstaked']:+,.0f} EGLD, delegators -30. 56,486 EGLD unDelegated by 152 wallets; no withdrawal above 3,000 EGLD went to an exchange."},
 {"category": "defi", "severity": "low", "finding": "PROTOCOL TVL RESTATED: Hatom Lending $5.86M (-0.6% over two weeks), Hatom LSD $3.45M (-9.1%, all price). LSD supply flat. No Hatom liquidations. Stablecoins contracted again (USDT -7.9%)."},
]

ti = R["trend_indicators"]
ti["accelerating_exchange_outflows"] = [
 {"exchange": "KuCoin", "trend": "outflow", "cumulative_change_pct": (15372 - 220076) / 220076 * 100, "weeks_in_trend": 3,
  "interpretation": "Third week: -14,746, -149,563, -40,396. 168K of it is one self-custody withdrawer; the rest fell under 400 EGLD a day by Nov 7-9. 15,372 left."},
 {"exchange": "MEXC", "trend": "outflow", "cumulative_change_pct": (40983 - 110883) / 110883 * 100, "weeks_in_trend": 2,
  "interpretation": "Second week withdraw-only: -54,886, then -15,014 with zero deposits."},
 {"exchange": "Bybit", "trend": "outflow", "cumulative_change_pct": (339061 - 375931) / 375931 * 100, "weeks_in_trend": 2,
  "interpretation": "-20,136 then -16,734; deposits still arriving (13,445) but withdrawals double them."}]
ti["validator_movements"] = {"providers_joining": 0, "providers_leaving": 0, "net_provider_change": 0, "notable_joiners": [], "notable_leavers": [], "note": "No joins or deregistrations for a thirteenth week."}
ti["token_supply_events"] = [
 {"identifier": "USDC-c76f1f", "name": "WrappedUSDC", "event": "burn", "supply_previous": "7176244", "supply_current": "7119153", "change_pct": -0.796, "description": "-57,091 USDC; sixth contraction in seven readings. Bridge unwraps 99,720 vs wraps 40,629."},
 {"identifier": "USDT-f8c08c", "name": "USDT", "event": "burn", "supply_previous": "413975", "supply_current": "381086", "change_pct": -7.945, "description": "-32,889 USDT, second straight contraction."}]
dlarr = rb["total_delegators"] + [D["dl"]]
streak = 0
for i in range(len(dlarr) - 1, 0, -1):
    if dlarr[i] < dlarr[i - 1]: streak += 1
    else: break
usdc = rb["usdc_supply"] + [7119153]
ti["consecutive_streaks"] = [
 {"metric": "total_delegators", "direction": "down", "weeks": streak, "cumulative_change_pct": (D["dl"] - dlarr[-streak - 1]) / dlarr[-streak - 1] * 100,
  "interpretation": f"{D['dl']:,} ({D['dl']-D['dlp']:+,}); the bleed slowed to almost nothing this window."},
 {"metric": "tracked_exchange_net_flow", "direction": "down", "weeks": 2, "cumulative_change_pct": None, "interpretation": "-205,817 then -86,702; KuCoin and MEXC both windows."},
 {"metric": "usdt_supply", "direction": "down", "weeks": 2, "cumulative_change_pct": (381086 - 425495) / 425495 * 100, "interpretation": "425,495 -> 381,086."},
 {"metric": "provider_operator_fee_selling", "direction": "flat", "weeks": 24, "cumulative_change_pct": 0.0, "interpretation": "See reward behavior section."}]
ti["regime_shifts"] = [
 {"metric": "binance_native_rail_egld_7d", "before_value": 145617.0, "after_value": 0.0, "description": "Binance.com went from ~145K EGLD gross weekly on-chain flow to zero after the Oct 29 sweep. If it persists, the largest exit and entry venue is off-chain-only for EGLD."},
 {"metric": "kucoin_book_egld", "before_value": 220076.0, "after_value": 15372.0, "description": "KuCoin's book is down 93% in three windows; most of it is one wallet's round trip."}]

R["watch_list"] = [
 {"item": "BINANCE NATIVE RAIL DARK", "weeks_on_list": 1, "reason": "0 deposits/withdrawals since Oct 29 23:05 UTC; hot wallet 3 EGLD. PRE-COMMITTED (binance-rail-reopens). Watch for the first value-bearing deposit or a new Binance deposit address."},
 {"item": "UPBIT CAUTION REVIEW - decision Nov 16-20", "weeks_on_list": 10, "reason": f"Premium {D['prem']:.1f}% (from 14.2%), Upbit share {D['up_share']:.0f}%. UPbit wallet idle (1,055,326). PRE-COMMITTED (upbit-premium-on-decision). Bithumb ($3.73) decision still not found."},
 {"item": "KUCOIN WITHDRAWER erd15ku2r2j6 (168,358)", "weeks_on_list": 1, "reason": "Withdrew 168,359 from KuCoin after depositing 145,443 in July; holds. Address-poisoning lookalike erd1tyfnsaztln is targeting it. PRE-COMMITTED (kucoin-whale-holds)."},
 {"item": "BINANCE STAKING CUSTODY 4.28M", "weeks_on_list": 4, "reason": "No outbound, no delegate since Oct 22."},
 {"item": "MEXC WITHDRAW-ONLY", "weeks_on_list": 2, "reason": "Zero deposits for two windows; 40,983 left."},
 {"item": "OTC OPERATOR VAULT erd1drc22z7h", "weeks_on_list": 1, "reason": "Received 112,634 from Unknown Whale I on Nov 5; returns clips daily. Holds 107,151."},
 {"item": "SELLER CHAIN erd1hl5y4a", "weeks_on_list": 5, "reason": "217,782 (-3,533). With Binance's rail dark, its usual route is closed."},
 {"item": "OTC PIPELINE", "weeks_on_list": 36, "reason": "Quiet: desk gross 139 EGLD. Keep until Upbit's decision."},
 {"item": "EXPLOIT WALLET AND POISONING RING", "weeks_on_list": 11, "reason": "Exploit wallet dust only; poisoning now targets the KuCoin withdrawer and the OTC vault."}]

T = R["pre_committed_tests"]
def find(i): return next(t for t in T if t["id"] == i)
find("kucoin-backlog-decay").update({"status": "resolved", "outcome": "inconclusive", "resolved_in_run": 36,
  "measured_value": "KuCoin balance -40,396 (55,768 -> 15,372); one 32,000 withdrawal to erd15ku2r2j6, ex that -8,396",
  "resolution": "Middle branch (20K-50K): no conclusion on the registered rule. The trace explains why: the 'backlog' was one wallet's 168K round trip, not many sellers; ex that wallet the daily outflow fell under 400 EGLD. The premise of the test was wrong, not just the size."})
find("bottom-confirms").update({"status": "resolved", "outcome": "inconclusive", "resolved_in_run": 36,
  "measured_value": f"net {D['net']:+,.0f} EGLD; EGLD {pc:+.2f}% vs BTC {D['btc_wow']:+.2f}% = {rel:+.1f}pp",
  "resolution": "Neither branch: exchanges kept losing EGLD (bottom side) but EGLD lagged BTC by 8.1pp (failed side). Exchange outflow did not predict price this window, with Binance's rail shut."})
find("delivery-price-relevance-2").update({"measured_value": "run #36: desk gross 139 EGLD. Not evaluable."})
find("upbit-premium-on-decision").update({"measured_value": f"run #36: premium {D['prem']:.1f}%, Upbit {D['up_share']:.0f}% of volume; decision due Nov 16-20."})
T.append({"id": "binance-rail-reopens", "registered_in_run": 36, "claim": "Binance's dark native EGLD rail is a temporary pause, not a withdrawal of support.",
  "threshold": "Over run #37's window: any Binance-labelled wallet (or a newly identified Binance deposit address) receives >= 5,000 EGLD in value-bearing customer deposits = reopened; 0 = still dark; otherwise no conclusion",
  "branches": [{"condition": "deposits >= 5,000", "reading": "reopened"}, {"condition": "deposits == 0", "reading": "still dark"}, {"condition": "otherwise", "reading": "no conclusion"}],
  "status": "open", "outcome": None, "resolved_in_run": None, "measured_value": "run #36: 0 deposits, 0 withdrawals", "resolution": None})
T.append({"id": "kucoin-whale-holds", "registered_in_run": 36, "claim": "erd15ku2r2j6 withdrew to hold, not to sell elsewhere.",
  "threshold": "At run #37: balance >= 150,000 and no transfer >= 10,000 to any exchange-labelled wallet = holder; >= 50,000 sent to exchanges = seller; otherwise no conclusion",
  "branches": [{"condition": "balance >= 150K, no CEX send >= 10K", "reading": "holder"}, {"condition": ">= 50K to exchanges", "reading": "seller"}, {"condition": "otherwise", "reading": "no conclusion"}],
  "status": "open", "outcome": None, "resolved_in_run": None, "measured_value": "run #36: 168,358 held", "resolution": None})

ml = R["meta_learning"]
ml.update({"run_number": 36, "endpoints_that_failed": ["Ad-hoc tracing hit HTTP 429 while three background passes ran; retried after they finished. Collector: 0 API errors."],
 "api_quirks": ["A venue whose rail is dark shows +0.000 balance change and zero txs; check the hot wallet's last-transaction timestamp before reading 'no flow' as balanced flow.",
                "Lookalike addresses send zero-value transfers to fresh large holders (erd1tyfnsaztln -> erd15ku2r2j6; erd1vdpfqqjaah -> erd1drc22z7h); filter zero-value txs before counting counterparties."],
 "data_gaps": ["No Binance announcement found for the paused EGLD rail.", "Bithumb and Upbit decisions not found.", "OTC pipeline sections not refreshed (desk gross 139 EGLD)."],
 "key_findings": [e["finding"] for e in R["executive_summary"][:5]],
 "action_items_from_previous": 6, "action_items_completed": 5,
 "action_items_completed_detail": ["kucoin-backlog-decay and bottom-confirms resolved (both inconclusive).",
   "Binance custody erd1rf4hv70: 0 outbound, 0 delegate since Oct 22.",
   "Upbit premium and volume share recorded (17.1%, 19%); Bithumb/Upbit decision searched, not found.",
   "Protocol TVL restated from token market caps (two-week basis); Hatom borrow->swap->supply join still not built.",
   "Per-day KuCoin and MEXC withdrawal counts collected; KuCoin withdrawals traced (168K to one holder)."],
 "methodology_changes": ["Trace pass adds per-venue daily rails and a one-hop destination class for every KuCoin withdrawal >= 100 EGLD.",
   "Rail liveness: report each tracked hot wallet's last-transaction time, so a dark venue is not read as balanced flow."],
 "new_addresses_discovered_detail": ["erd15ku2r2j6smlwumftumlpw0mfpqxy32wyt4ewxzyhs3ugsjee8stq2xh84e: KuCoin round-trip whale (168,358)",
   "erd1drc22z7hz90sqmugmtwu6pe8kyncg67gv7xulcu4mq92ygyxpacq72xywa: OTC operator vault (from Unknown Whale I)",
   "erd1tyfnsaztln...: address-poisoning lookalike of KuCoin", "erd1vdpfqqjaah...: address-poisoning lookalike of Unknown Whale I"],
 "new_addresses_discovered": 4,
 "most_valuable_insight": "A zero balance change at Binance was not balanced flow: the rail was dark. And the KuCoin 'backlog' that read as many sellers leaving was one wallet taking 168K into self-custody. Both would have been misread from the per-wallet table alone.",
 "top_recommendation": "RUN #37 FIRST: resolve binance-rail-reopens and kucoin-whale-holds; record the Upbit premium at the Nov 16-20 decision.",
 "recommendations_for_next_run": [
  "Resolve binance-rail-reopens and kucoin-whale-holds on run #37's window.",
  "Upbit decision (Nov 16-20): resolve upbit-premium-on-decision if announced; record premium and volume share either way.",
  "Add a rail-liveness check to the collector: last-transaction timestamp per tracked hot wallet, flag any venue silent > 48h.",
  "If Binance reopens, look for a new deposit address (first depositors after the gap) before netting flows.",
  "Build the Hatom borrow -> swap -> supply join (carried twice).",
  "Track erd1drc22z7h vault returns to Whale I: does the 112,634 drain back in clips?"],
 "dashboard_feature_suggestions": [
  {"title": "Venue rail liveness strip", "motivation": "Binance.com's 0-deposit, 0-withdrawal week reads as 'balanced' in the flow table; only the hot wallet's last-transaction time (Oct 29 23:05) shows the rail is dark.", "suggested_visualization": "per-venue horizontal timeline of daily value-bearing deposit/withdrawal counts, with gaps shaded and a 'silent for N days' badge", "data_already_available": True, "data_source": "run36_traces.binance_daily + venue_daily in data/collected; exchange_reopen sends/receives_in_window", "priority": "high"},
  {"title": "Single-wallet CEX round-trip ledger", "motivation": "KuCoin's 3-week outflow was one wallet (erd15ku2r2j6) depositing 145,443 in July and withdrawing 168,359 after the halt; the venue-level series cannot show that one holder drives the line.", "suggested_visualization": "venue outflow stacked by top withdrawers, with a drilldown to each wallet's deposit/withdraw timeline", "data_already_available": False, "data_source": "new: per-receiver aggregation of venue withdrawals (run36_traces.kucoin_destinations shows the shape)", "priority": "medium"}],
 "dashboard_suggestions_followup": [
  {"title": "Entity-netted exchange flow bridge", "status": "pending", "reason": "No internal move this window; still needed when the next one happens."},
  {"title": "Exchange book depletion timeline", "status": "pending", "reason": "More relevant now: KuCoin -93% over three windows, MEXC withdraw-only."},
  {"title": "Staked-EGLD change waterfall", "status": "deprioritized", "reason": "Staking flat for three windows (+15,648 this run)."},
  {"title": "Hatom leverage-loop tracker", "status": "pending", "reason": "Join still not built."}],
 "self_assessment": {"most_valuable_insight": "Binance's zero is a dark rail, not balance.", "recommendations_completed": "5 of 6", "what_would_make_it_2x_better": "Automated rail liveness and per-withdrawer venue decomposition in the collector, so these reads don't depend on ad-hoc tracing."}})
R["meta_learning"]["endpoints_that_worked"] = ml.get("endpoints_that_worked", [])[:40]

json.dump(R, open(f"{REPO}/reports/{RD}.json", "w"), indent=1, default=str)
print("wrote reports/2026-11-09.json")
