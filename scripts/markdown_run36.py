#!/usr/bin/env python3
"""Run #36: render reports/2026-11-09.md from the report JSON."""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"; RD="2026-11-09"
R=json.load(open(f"{REPO}/reports/{RD}.json")); m=R["metadata"]; nh=R["network_health"]; wi=R["whale_intelligence"]; si=R["staking_intelligence"]
ta=R["token_activity"]; da=R["defi_activity"]; ef=wi["exchange_flows"]; D=nh["deltas"]
L=[]; A=L.append
A(f"# MultiversX On-Chain Intelligence Report - {RD}\n")
A(f"**Period**: 2026-11-02 14:03 -> 2026-11-09 17:20 UTC (7.1 days) | **EGLD**: ${m['egld_price_usd']:.2f} ({D['price_change_pct']:+.2f}%) | **BTC**: ${m['btc_price_usd']:,.0f} | **Run**: #36\n")
A("## TL;DR\n")
for i,e in enumerate(R["executive_summary"],1): A(f"{i}. [{e['severity'].upper()}] {e['finding']}")
eo=ef["by_exchange"]
A("\n## Risk Dashboard\n\n| Signal | State | Note |\n|---|---|---|")
A(f"| Binance native rail | 🔴 | 0 deposits / 0 withdrawals since Oct 29 23:05 UTC |")
A(f"| Price vs BTC | 🔴 | {D['price_change_pct']:+.1f}% vs BTC; {R['anomalies'][[a['metric'] for a in R['anomalies']].index('egld_minus_btc_pp')]['current_value']:+.1f}pp |")
A(f"| Exchange books | 🟡 | {ef['net_change_egld']:+,.0f} EGLD; KuCoin's outflow is one holder |")
A(f"| Korea premium | 🟡 | {ta and wi['demand_instruments']['exchange_orderbook']['korea_premium_pct']:.1f}% (from 14.2%), Upbit decision Nov 16-20 |")
A(f"| Staking | 🟢 | {D['staked_egld_added']:+,.0f} EGLD, delegators -30 |")
A(f"| DeFi | 🟢 | No Hatom liquidations; LSD supply flat |")
A("\n## Network Health\n"); A(nh["analysis"].replace("\n\n","\n\n"))
A("\n## Whale Intelligence\n\n### Tiers\n\n| Tier | Count | Balance (EGLD) | Net change | % |\n|---|---|---|---|---|")
for k,v in wi["whale_tiers"].items(): A(f"| {k} | {v['count_current']} | {v['total_balance_egld']:,.0f} | {v['net_change_egld']:+,.0f} | {(v['net_change_pct'] or 0):+.2f}% |")
A("\n### Exchange balance change by venue\n\n| Venue | Change (EGLD) |\n|---|---|")
for x in eo: A(f"| {x['exchange']} | {x['change_egld']:+,.0f} |")
A("\n### Rails (value-bearing EGLD, trailing 7d)\n\n| Venue | State | Deposits | Withdrawals |\n|---|---|---|---|")
for v in ef["rail_status"]["by_venue"]: A(f"| {v['venue']} | {v['state']} | {v['deposits_egld_7d']:,.0f} ({v['deposits_egld_txs_7d']}) | {v['withdrawals_egld_7d']:,.0f} ({v['withdrawals_egld_txs_7d']}) |")
A("\n### Entity netting\n")
for e in ef["entity_netting"]: A(f"- **{e['entity']}** ({e['net_flow_egld']:+,.0f}): {e['interpretation']}")
A("\n### Large transactions (>= 5,000 EGLD)\n\n| Time | From | To | EGLD | Type |\n|---|---|---|---|---|")
for t in wi["large_transactions"][:10]: A(f"| {t['timestamp']} | {t['sender_label'] or t['sender'][:14]} | {t['receiver_label'] or t['receiver'][:14]} | {t['value_egld']:,.0f} | {t['flow_type']} |")
A("\n"+wi["analysis"])
A("\n## Staking Power Map\n"); A(si["analysis"])
rb=si.get("reward_behavior") or {}
if rb.get("compound_pct_at_function_level") is not None: A(f"\nREWARDS. Compound rate {rb['compound_pct_at_function_level']:.2f}% of reward decisions (from 57.26%, 8 providers sampled).")
A("\n| # | Provider | Locked | Share | APR | Fee | Delegators | WoW |\n|---|---|---|---|---|---|---|---|")
for p in si["top_providers"][:10]: A(f"| {p['rank']} | {p['name'][:20]} | {p['locked_egld']:,.0f} | {p['share_pct']:.2f}% | {p['apr_pct']:.2f}% | {p['fee_pct']:.0f}% | {p['num_users']:,} | {(p['wow_change_egld'] or 0):+,.0f} |")
A("\n| APR bucket | Providers | Locked |\n|---|---|---|")
for b in si["apr_distribution"]["buckets"]: A(f"| {b['label']} | {b['provider_count']} | {b['total_locked_egld']:,.0f} |")
c=si["concentration"]; A(f"\nConcentration: HHI {c['hhi']:.5f}, top-5 {c['top_5_share_pct']:.2f}%, top-10 {c['top_10_share_pct']:.2f}%.")
A("\n## Token & DeFi Activity\n"); A(ta["analysis"])
A("\n| Top by holders | Holders | Change |\n|---|---|---|")
for t in ta["top_by_holders"]: A(f"| {t['identifier']} | {t['holders']:,} | {(t['holders_change'] or 0):+,} |")
A("\n"+da["analysis"])
A("\n| Protocol | TVL (USD) | Change | Signal |\n|---|---|---|---|")
for p in da["protocol_breakdown"]:
    if p.get("tvl_usd"): A(f"| {p['protocol']} | ${p['tvl_usd']:,.0f} | {('%+.1f%%' % p['tvl_wow_change_pct']) if p.get('tvl_wow_change_pct') is not None else 'n/a'} | {p.get('health_signal') or '-'} |")
A("\nTVL change for Hatom and XOXNO is on a two-week basis (vs Oct 26); xExchange vs last week.")
A("\n## Anomalies & Trend Indicators\n")
for a in R["anomalies"]: A(f"- [{a['severity']}] **{a['metric']}**: {a['description']}")
for t in R["trend_indicators"]["accelerating_exchange_outflows"]: A(f"- Trend: **{t['exchange']}** {t['interpretation']}")
for t in R["trend_indicators"]["regime_shifts"]: A(f"- Regime: **{t['metric']}** {t['description']}")
A("\n## Pre-committed tests\n")
for t in R["pre_committed_tests"]:
    if t.get("resolved_in_run")==36: A(f"- **{t['id']}** -> {t['outcome']}: {t['resolution']}")
for t in R["pre_committed_tests"]:
    if t.get("registered_in_run")==36: A(f"- NEW **{t['id']}**: {t['claim']} Threshold: {t['threshold']}")
A("\n## Watch List\n")
for w in R["watch_list"]: A(f"- **{w['item']}** ({w['weeks_on_list']}w): {w['reason']}")
A("\n## Methodology log\n")
for x in R["meta_learning"]["methodology_changes"]: A(f"- {x}")
for x in R["meta_learning"]["data_gaps"]: A(f"- Gap: {x}")
A(f"\n---\n*Generated by the onchain-quant-agent, run #36. Dashboard: https://dashboard-omega-lyart-99.vercel.app*")
open(f"{REPO}/reports/{RD}.md","w").write("\n".join(L)+"\n"); print("wrote md", len(L))
