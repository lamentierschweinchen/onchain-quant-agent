#!/usr/bin/env python3
"""Run #27: render reports/2026-09-28.md from the report JSON."""
import json
REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD = "2026-09-28"
R = json.load(open(f"{REPO}/reports/{RD}.json"))
P = json.load(open(f"{REPO}/reports/2026-09-21.json"))
m = R["metadata"]; nh = R["network_health"]; wi = R["whale_intelligence"]; si = R["staking_intelligence"]
ta = R["token_activity"]; da = R["defi_activity"]; an = R["anomalies"]; ti = R["trend_indicators"]; wl = R["watch_list"]
e = nh["economics"]; d = nh["deltas"]; pe = P["network_health"]["economics"]; pm = P["metadata"]
otc = wi["otc_pipeline"]; dem = wi["demand_instruments"]; ob = dem["exchange_orderbook"]; x0 = ta["xexchange"]
hr = wi["halt_recovery"]; lv = nh["liveness"]; q = si["unbonding_in_flight"]["queue_this_week"]; rb = si["reward_behavior"]
wave = otc["wave_window_netting"]


def egld(x): return f"{x:,.0f}" if x is not None else "n/a"


def usd(x):
    if x is None: return "n/a"
    if x >= 1e6: return f"${x/1e6:.2f}M"
    if x >= 1e3: return f"${x/1e3:.1f}K"
    return f"${x:.2f}"


def pct(x, dd=2): return f"{x:+.{dd}f}%" if x is not None else "n/a"


L = []
w = L.append
w("# MultiversX Weekly On-Chain Intelligence Report"); w("")
w(f"**Report date**: {RD} (UTC)  ")
w(f"**Period**: 2026-09-21 -> 2026-09-28 ({lv['live_days_in_window']} live days: chain restarted Sep 23 16:35, halted again 16:53, live since Sep 24 15:30)  ")
w(f"**EGLD price**: ${e['egld_price_usd']:.2f} ({d['price_change_pct']:+.2f}% WoW; BTC ${m['btc_price_usd']:,})  ")
w(f"**Run number**: {m['run_number']} . Schema v2"); w(""); w("---"); w("")
w("## TL;DR"); w("")
for i, f_ in enumerate(R["executive_summary"], 1):
    w(f"{i}. **{f_['category'].title()}** [{f_['severity'].upper()}]: {f_['finding']}")
w(""); w("---"); w("")
w("## Risk Dashboard"); w("")
w("| Signal | Status | Reading |"); w("|---|---|---|")
w(f"| Chain liveness | 🟢 LIVE | All shards current at collection; rollback point {lv['rollback_point_utc']}; live since {lv['restart_2_utc']} |")
w(f"| Exploit state | 🟢 REMOVED | {hr['invalid_balances_egld_now']:.2f} EGLD across 14 incident addresses (was {hr['invalid_balances_egld_at_halt']/1e6:,.1f}M) |")
w(f"| Recovery method | 🟡 ROLLBACK | 64 min of finalized history rewritten; 1,597 non-exploit txs not replayed (467 EGLD) |")
w(f"| Exchange rails | 🔴 CLOSED | {wi['exchange_flows']['rail_status']['egld_sends_since_restart']} EGLD send across {wi['exchange_flows']['rail_status']['tracked_wallets']} tracked wallets since restart (a replay) |")
w(f"| Price | 🟡 CLOSED-BOOK RALLY | {d['price_change_pct']:+.2f}% vs BTC {100*(m['btc_price_usd']-pm['btc_price_usd'])/pm['btc_price_usd']:+.2f}%; Upbit premium {ob['korea_premium_pct']:.0f}% on {ob['upbit_share_of_volume_pct']:.0f}% of volume |")
w(f"| Staking exits | 🟡 ELEVATED | {egld(q['undelegated_egld'])} EGLD unDelegated in {lv['live_days_in_window']} live days (~{egld(q['undelegated_weekly_pace_egld'])}/wk pace) |")
w(f"| Staked ratio | 🟡 SETTLED LOWER | {100*e['staked_ratio']:.2f}% ({d['staked_ratio_change_pp']:+.2f}pp) |")
w(f"| OTC pipeline | 🟡 IDLE | Gross {egld(otc['gross_outbound_egld_7d'])} EGLD; desks {egld(otc['desk_balance_egld'])}; wave #4 closed at {egld(wave['net_one_way_egld'])} |")
hlp = next(p for p in da["protocol_breakdown"] if p["protocol"] == "Hatom Lending")
w(f"| Hatom lending | 🟢 NO LIQUIDATION WAVE | {hlp['notable_events'][:120]}... |")
w(f"| Compound rate | 🟡 DIPPED | {rb['compound_pct_at_function_level']:.2f}% ({rb['compound_vs_claim']['redelegate_count']} vs {rb['compound_vs_claim']['claim_count']}) |")
w(f"| Stablecoins | 🔴 BURNING | USDT/USDC contracting again |")
w(""); w("---"); w("")
w("## Network Health"); w("")
w("| Metric | Current | Previous | Delta |"); w("|---|---|---|---|")
w(f"| EGLD price | ${e['egld_price_usd']:.2f} | ${pe['egld_price_usd']:.2f} | **{d['price_change_pct']:+.2f}%** |")
w(f"| Market cap | {usd(e['market_cap_usd'])} | {usd(pe['market_cap_usd'])} | {d['market_cap_change_pct']:+.2f}% |")
w(f"| Total supply | {egld(e['total_supply'])} | {egld(pe['total_supply'])} | +{d['supply_added']:,} |")
w(f"| Staked EGLD | {egld(e['staked_egld'])} | {egld(pe['staked_egld'])} | {d['staked_egld_added']:+,} |")
w(f"| Staked ratio | {100*e['staked_ratio']:.2f}% | {100*pe['staked_ratio']:.2f}% | {d['staked_ratio_change_pp']:+.2f}pp |")
w(f"| Network APR | {100*e['staking_apr']:.2f}% | {100*pe['staking_apr']:.2f}% | {d['apr_change_pp']:+.3f}pp |")
w(f"| Epoch | {nh['activity']['epoch']} | | +{d['epoch_advanced']} |")
w(f"| Transactions added | {d['transactions_added']:,} | | ~{nh['activity']['avg_daily_transactions']:,}/live day |")
w(""); w("**Liveness at collection:** " + ", ".join(f"shard {k}: {v}" for k, v in lv["latest_block_by_shard"].items())); w("")
w(nh["analysis"]); w(""); w("---"); w("")
w("## Whale Intelligence"); w("")
w("### Halt recovery check"); w("")
w("| Address set | At halt (run #26) | Now |"); w("|---|---|---|")
w(f"| Attacker + contract + 12 fan-out wallets | {hr['invalid_balances_egld_at_halt']:,.0f} | {hr['invalid_balances_egld_now']:.2f} |")
for k, v in hr["legitimate_balances"].items():
    w(f"| {k} | {egld(v['pre_halt_egld'])} (reference) | {egld(v['now_egld'])} |")
w(""); w("### Exchange flows (closed book)"); w("")
w(wi["exchange_flows"]["signal"]); w("")
w("| Entity | Wallets | Net flow (EGLD) |"); w("|---|---|---|")
for en in wi["exchange_flows"]["entity_netting"]:
    w(f"| {en['entity']} | {en['wallets_count']} | {en['net_flow_egld']:+,.0f} |")
w(""); w("### Whale tiers (common-address basis)"); w("")
w("| Tier | Count | Balance (EGLD) | Previous | Net change |"); w("|---|---|---|---|---|")
for t_, k in [("Mega (>1M)", "mega_whales"), ("Large (100K-1M)", "large_whales"), ("Mid (10K-100K)", "mid_whales")]:
    x = wi["whale_tiers"][k]
    w(f"| {t_} | {x['count_current']} | {egld(x['total_balance_egld'])} | {egld(x['previous_total_balance_egld'])} | {x['net_change_egld']:+,.0f} |")
w(""); w("### Wallet changes > 2,000 EGLD"); w("")
w("| Wallet | Category | Tier | Change |"); w("|---|---|---|---|")
for c in wi["wallet_changes"]:
    w(f"| {c['label']} | {c['category']} | {c.get('tier') or '-'} | {c['change_egld']:+,.0f} |")
w(""); w(f"Large transactions (>1,000 EGLD) in tracked-account scans: {len(wi['large_transactions'])}."); w("")
w("### OTC pipeline"); w("")
w(f"Gross out {egld(otc['gross_outbound_egld_7d'])} EGLD, net one-way {egld(otc['net_one_way_egld_7d'])}, desks {egld(otc['desk_balance_egld'])} (previous {egld(otc['previous_desk_balance_egld'])}). {otc['series_note']}"); w("")
w(f"**Wave #4 (final):** {wave['window']}: gross {egld(wave['gross_outbound_egld'])}, circular {wave['circular_share_pct']:.0f}%, **net one-way {egld(wave['net_one_way_egld'])}**. {wave['note']}"); w("")
w(wi["analysis"]); w(""); w("---"); w("")
w("## Staking Power Map"); w("")
c = si["concentration"]; ch = si["churn"]
w(f"Delegated {egld(si['summary']['total_delegated_egld'])} EGLD across {si['summary']['num_providers']} providers; HHI {c['hhi']:.4f}, top-5 {c['top_5_share_pct']:.2f}%, top-10 {c['top_10_share_pct']:.2f}%. Delegators {ch['total_delegators_current']:,} ({ch['delegators_added']:+,}); {ch['providers_gaining_delegators']} gaining, {ch['providers_losing_delegators']} losing."); w("")
w("| # | Provider | Locked (EGLD) | WoW | APR | Fee | Users |"); w("|---|---|---|---|---|---|---|")
for p in si["top_providers"][:10]:
    w(f"| {p['rank']} | {p['name']} | {egld(p['locked_egld'])} | {(p['wow_change_egld'] or 0):+,.0f} | {p['apr_pct']:.2f}% | {p['fee_pct']:.1f}% | {p['num_users']:,} |")
w(""); w("**APR distribution**"); w("")
w("| Bucket | Providers | Locked (EGLD) |"); w("|---|---|---|")
for b in si["apr_distribution"]["buckets"]:
    w(f"| {b['label']} | {b['provider_count']} | {egld(b['total_locked_egld'])} |")
w(""); w(f"**Unbonding this week:** {egld(q['undelegated_egld'])} EGLD unDelegated by {q['distinct_callers']} wallets; {q['withdraw_calls']} withdraw calls returned {egld(q['withdraw_egld_returned'])} EGLD. **Compound rate:** {rb['compound_pct_at_function_level']:.2f}%."); w("")
w(si["analysis"]); w(""); w("---"); w("")
w("## Token & DeFi Activity"); w("")
w("**Top 10 by holders**"); w("")
w("| Token | Holders | WoW |"); w("|---|---|---|")
for t in ta["top_by_holders"]:
    w(f"| {t['identifier']} | {t['holders']:,} | {t['holders_change']:+,} |" if t["holders_change"] is not None else f"| {t['identifier']} | {t['holders']:,} | n/a |")
w(""); w("**Top 10 by transactions**"); w("")
w("| Token | Transactions | WoW |"); w("|---|---|---|")
for t in ta["top_by_volume"]:
    w(f"| {t['identifier']} | {t['transactions']:,} | {pct(t['change_pct'])} |")
w(""); w(f"**Newly issued (top 5):** {len(ta['newly_issued'])} issuance(s), none above the quality bar."); w("")
w(f"**xExchange:** {x0['total_pairs']} pairs, 24h volume {usd(x0['total_volume_24h_usd'])} ({egld(x0['dex_volume_egld_24h'])} EGLD), turnover {x0['turnover_ratio_pct']:.2f}%, top pair {x0['top_pair']} ({x0['top_pair_dominance_pct']:.0f}%), MEX ${x0['mex_price_usd']:.2e}."); w("")
w(ta["analysis"]); w("")
w("**DeFi protocol breakdown**"); w("")
w("| Protocol | Category | TVL (USD) | TVL (EGLD) | WoW | 24h transfers | Signal |"); w("|---|---|---|---|---|---|---|")
for p in da["protocol_breakdown"]:
    w(f"| {p['protocol']} | {p['category']} | {usd(p['tvl_usd'])} | {egld(p['tvl_egld'])} | {pct(p['tvl_wow_change_pct'])} | {egld(p['transfers_24h']) if p['transfers_24h'] is not None else '-'} | {p['health_signal'] or '-'} |")
w(""); w(da["analysis"]); w(""); w("---"); w("")
w("## Anomalies & Trend Indicators"); w("")
w("| Metric | Method | Severity | Description |"); w("|---|---|---|---|")
for a in an:
    w(f"| {a['metric']} | {a['method']} | {a['severity']} | {a['description']} |")
w(""); w("**Regime shifts**"); w("")
for r_ in ti["regime_shifts"]:
    w(f"- **{r_['metric']}**: {r_['description']}")
w(""); w("**Token supply events**"); w("")
for s_ in ti["token_supply_events"]:
    w(f"- {s_['name']} {s_['event']} {s_['change_pct']:+.2f}%: {s_['description']}")
w(""); w("**Streaks**"); w("")
for s_ in ti["consecutive_streaks"]:
    w(f"- {s_['metric']} {s_['direction']} {s_['weeks']} weeks: {s_['interpretation']}")
w(""); w("### Pre-committed tests"); w("")
for t in R["pre_committed_tests"]:
    if t.get("resolved_in_run") == 27:
        w(f"- **{t['id']}** RESOLVED **{t['outcome']}**: {t['measured_value']}. {t['resolution']}")
for t in R["pre_committed_tests"]:
    if t["status"] == "open":
        w(f"- **{t['id']}** OPEN (run #{t['registered_in_run']}): {t['threshold']} Current: {t['measured_value']}")
w(""); w("---"); w("")
w("## Watch List"); w("")
for x in wl:
    w(f"- **{x['item']}** (week {x['weeks_on_list']}): {x['reason']}")
w(""); w("---"); w("")
ml = R["meta_learning"]
w("## Methodology Log"); w("")
w(f"- Data sources: {len(m['data_sources_ok'])} ok, {len(m['data_sources_failed'])} missing, {len(m['data_sources_recovered'])} notes/recovered.")
for x in m["data_sources_recovered"]: w(f"  - {x}")
w("- Methodology changes:")
for x in ml["methodology_changes"]: w(f"  - {x}")
w("- Withdrawn claims:")
for x in ml["withdrawn_claims"]: w(f"  - {x['claim']} (runs {x['asserted_in_runs']}): {x['reason']}")
w(f"- Most valuable insight: {ml['most_valuable_insight']}")
w("- Recommendations for next run:")
for x in ml["recommendations_for_next_run"]: w(f"  - {x}")
w(""); w("*Generated by the onchain-quant-agent, run #27. Dashboard: https://dashboard-omega-lyart-99.vercel.app*")
open(f"{REPO}/reports/{RD}.md", "w").write("\n".join(L) + "\n")
print("markdown written", len(L), "lines")
