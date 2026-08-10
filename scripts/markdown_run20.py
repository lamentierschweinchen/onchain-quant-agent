#!/usr/bin/env python3
import json
R=json.load(open("/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/reports/2026-08-10.json"))
m=R["metadata"]; nh=R["network_health"]; wi=R["whale_intelligence"]; si=R["staking_intelligence"]
ta=R["token_activity"]; da=R["defi_activity"]; an=R["anomalies"]; ti=R["trend_indicators"]; wl=R["watch_list"]
e=nh["economics"]; d=nh["deltas"]
_prevR=json.load(open("/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/reports/2026-08-03.json"))
pecon=dict(_prevR["network_health"]["economics"]); pecon["btc_price_usd"]=_prevR["metadata"]["btc_price_usd"]; pecon["eth_price_usd"]=_prevR["metadata"]["eth_price_usd"]
def egld(x): return f"{x:,.0f}" if x is not None else "n/a"
def usd(x):
    if x is None: return "n/a"
    if x>=1e6: return f"${x/1e6:.2f}M"
    if x>=1e3: return f"${x/1e3:.1f}K"
    return f"${x:.2f}"
L=[]
def w(s=""): L.append(s)

w("# MultiversX Weekly On-Chain Intelligence Report")
w()
w(f"**Report date**: {m['report_date']} (UTC)")
w(f"**Period**: 2026-08-03 -> 2026-08-10 (7 days)")
w(f"**EGLD price**: ${e['egld_price_usd']:.2f} ({d['price_change_pct']:+.2f}% WoW)")
w(f"**Run number**: {m['run_number']} . Schema v2")
w(); w("---"); w()
w("## TL;DR (Top Findings)"); w()
emoji={"high":"FILL","critical":"FILL","medium":"WATCH","low":"OK"}
for i,f in enumerate(R["executive_summary"],1):
    w(f"{i}. **{f['category'].title()}** [{f['severity'].upper()}]: {f['finding']}")
w(); w("---"); w()
w("## Risk Dashboard"); w()
w("| Signal | Status | Reading |")
w("|---|---|---|")
otc=wi["otc_pipeline"]; dem=wi["demand_instruments"]; x0=ta["xexchange"]
w(f"| Price action | FLAT, UNDERPERFORMING | {d['price_change_pct']:+.2f}% WoW to ${e['egld_price_usd']:.2f} with BTC {100*(m['btc_price_usd']-pecon['btc_price_usd'])/pecon['btc_price_usd']:+.2f}% and ETH {100*(m['eth_price_usd']-pecon['eth_price_usd'])/pecon['eth_price_usd']:+.2f}% - ~2pp underperformance is the supply overhang, quantified |")
w(f"| OTC pipeline | WAVE #2 STAGING | Net one-way TRIPLED to {otc['net_one_way_egld_7d']:,.0f} EGLD (threshold was 150K); gross {otc['gross_outbound_egld_7d']:,.0f}, {otc['circular_share_pct']:.0f}% circular |")
w(f"| OTC feed | UPbit ESCALATED 4.8x | {otc['upbit_reload_egld']:,.0f} EGLD tranche vs 67,000 last week (threshold was 200K); desk balance {otc['desk_balance_egld']-otc['previous_desk_balance_egld']:+,.0f} to {otc['desk_balance_egld']:,.0f} - passing through, not accumulating |")
w(f"| Run #17 peak | RE-NETTED | {otc['peak_window_renetted']['gross_egld']:,.0f} gross = {otc['peak_window_renetted']['net_one_way_egld']:,.0f} one-way ({otc['peak_window_renetted']['circular_share_pct']:.0f}% circular); this week is {100*otc['net_one_way_egld_7d']/otc['peak_window_renetted']['net_one_way_egld']:.0f}% of peak |")
w(f"| Identifiable bid | REACTIVATED (small) | Absorber took {dem['identifiable_bid_absorbed_egld_7d']:,.0f} EGLD via the Coinbase Routing pipe after 2 zero weeks - but only {dem['bid_to_distribution_ratio_pct']:.0f}% of the week's net distribution |")
w(f"| Exchange flows | INFLOW, DO NOT READ AS BUYING | {wi['exchange_flows']['net_change_egld']:+,.0f} EGLD broad-based, but Binance.com and Bybit are the hub's two largest net RECEIVERS this week |")
w(f"| Delegation market | FIRST FEE CUT IN 20 RUNS | A high-fee incumbent cut 24% -> 15%, the exact event run #19 pre-registered; it has not stopped the bleeding yet |")
w(f"| Binance staking | PARKED (2nd wk) | Custody unchanged at 3,357,101, zero transactions; both registered branches still open |")
w(f"| DEX depth | HALVING STOPPED | {x0['previous_turnover_ratio_pct']:.2f}% -> {x0['turnover_ratio_pct']:.2f}% of pool TVL traded daily - first non-decline in 3 weeks, but far below the ~4% recovery threshold |")
w(f"| DEX activity | LOW, STABILISING | {usd(x0['total_volume_24h_usd'])} 24h volume on {x0['top_pair_dominance_pct']:.1f}% WEGLD/USDC concentration |")
w(f"| DeFi leverage | UNWIND COMPLETE | USH -0.32% after -2.93% and -2.60% - run #19's stabilisation branch; no capitulation tell, no new leverage |")
w(f"| DeFi deposits | ADDING (3rd wk) | Hatom Lending EGLD-TVL +1.30%, and this week WITHOUT a dip to buy. Inverse rule NOT evaluable at a -0.37% price move |")
w(f"| Liquid staking | XOXNO REDEEMING, NO DRIVER | XEGLD -2.23% on a flat price week - first decoupling in tracking; SEGLD flat to 3 decimals (-0.045%) |")
w(f"| Staking | ROTATION, WEEK 3 | Total staked {d['staked_egld_added']:+,} to {e['staked_egld']:,} while delegation GREW +23,527; ~25.6K left DIRECT-NODE stake (~215K over 3 weeks, unexplained) |")
w(f"| Yield arbitrage | STILL THE ONLY FORCE | star_staking +8,992 and pi-staking +3,713 (8th wk) at 0% fees; APR>=8.8% cohort +11,518 |")
w(f"| Delegator base | INERT (8th wk) | {si['churn']['delegators_added']:+} WoW at {si['churn']['total_delegators_current']:,}; structural since run #18 |")
w(f"| Staking concentration | Healthy | HHI {si['concentration']['hhi']:.3f}; top-5 {si['concentration']['top_5_share_pct']:.1f}% (essentially unchanged) |")
w(f"| Stablecoins | BLEEDING AGAIN, MILDLY | USDC -0.47%, USDT -1.02%, WEGLD -1.06% - dollars leaving and EGLD unwrapping; still no inflow week in 8 runs |")
w(f"| New tokens | ZERO (4th wk) | Not one qualifying issuance in the window - the most durable problem in this report |")
w(); w("---"); w()
w("## Network Health"); w(); w("### Economics"); w()
w("| Metric | Current | Previous | Delta |")
w("|---|---|---|---|")
w(f"| EGLD price | ${e['egld_price_usd']:.2f} | ${pecon['egld_price_usd']:.2f} | **{d['price_change_pct']:+.2f}%** |")
w(f"| Market cap | {usd(e['market_cap_usd'])} | {usd(pecon['market_cap_usd'])} | {d['market_cap_change_pct']:+.2f}% |")
w(f"| Circulating supply | {egld(e['circulating_supply'])} | {egld(pecon['circulating_supply'])} | +{d['supply_added']:,} |")
w(f"| Staked EGLD | {egld(e['staked_egld'])} | {egld(pecon['staked_egld'])} | {d['staked_egld_added']:+,} |")
w(f"| Staked ratio | {e['staked_ratio']*100:.2f}% | {pecon['staked_ratio']*100:.2f}% | {d['staked_ratio_change_pp']:+.2f}pp |")
w(f"| Network APR | {e['staking_apr']*100:.2f}% | {pecon['staking_apr']*100:.2f}% | {d['apr_change_pp']:+.3f}pp |")
w(f"| BTC | ${m['btc_price_usd']:,} | ${pecon.get('btc_price_usd',0):,.0f} | {100*(m['btc_price_usd']-pecon.get('btc_price_usd',m['btc_price_usd']))/pecon.get('btc_price_usd',m['btc_price_usd']):+.2f}% WoW |")
w(f"| ETH | ${m['eth_price_usd']:,.0f} | ${pecon.get('eth_price_usd',0):,.0f} | {100*(m['eth_price_usd']-pecon.get('eth_price_usd',m['eth_price_usd']))/pecon.get('eth_price_usd',m['eth_price_usd']):+.2f}% WoW |")
w()
w("### Activity"); w()
w(f"- **Total accounts**: {nh['activity']['total_accounts']:,} (+{d['accounts_added']:,} WoW)")
w(f"- **Total transactions**: {nh['activity']['total_transactions']:,} (+{nh['activity']['transactions_7d']:,} in 7d = {nh['activity']['avg_daily_transactions']:,}/day)")
w(f"- **Epoch**: {nh['activity']['epoch']:,} . **Blocks**: {nh['activity']['blocks']:,}")
w(); w("### Analysis"); w(); w(nh["analysis"]); w(); w("---"); w()

w("## Whale Intelligence"); w()
w("### Whale Tier Stratification (top-60, apples-to-apples)"); w()
w("| Tier | Count | Total EGLD | Prev EGLD | Net Delta EGLD |")
w("|---|---|---|---|---|")
for k,nm in [("mega_whales","Mega (>1M)"),("large_whales","Large (100K-1M)"),("mid_whales","Mid (10K-100K)")]:
    t=wi["whale_tiers"][k]
    w(f"| {nm} | {t['count_current']} | {egld(t['total_balance_egld'])} | {egld(t['previous_total_balance_egld'])} | {t['net_change_egld']:+,.0f} |")
w()
w("### Exchange Flows (entity-netted)"); w()
w(f"**Total tracked exchange EGLD**: {egld(wi['exchange_flows']['total_exchange_egld_current'])} ({wi['exchange_flows']['net_change_egld']:+,.0f} WoW, {wi['exchange_flows']['net_change_pct']:+.2f}%) - **{wi['exchange_flows']['direction']}**")
w()
w(f"_{wi['exchange_flows']['signal']}_")
w()
w("| Entity | Wallets | Net flow EGLD | Read |")
w("|---|---|---|---|")
for x in wi["exchange_flows"]["entity_netting"]:
    w(f"| {x['entity']} | {x['wallets_count']} | {x['net_flow_egld']:+,.0f} | {x['interpretation']} |")
w()
w("### OTC Pipeline - gross vs net one-way (NEW this run)"); w()
w(f"Gross desk throughput was **{otc['gross_outbound_egld_7d']:,.0f} EGLD** out / {otc['gross_inbound_egld_7d']:,.0f} in. Resolving BOTH legs two hops out shows **{otc['circular_share_pct']:.0f}% is round-trip churn**, leaving **{otc['net_one_way_egld_7d']:,.0f} EGLD of genuine one-way movement** - a TRIPLING from last week's 61,435. UPbit fed a **{otc['upbit_reload_egld']:,.0f} EGLD** tranche (4.8x last week). Run #19's pre-committed thresholds for 'wave #2 is genuinely staging' were a tranche above 200,000 AND net one-way above 150,000. **Both cleared.**")
w()
w("| Venue | Desk -> venue | Venue -> desk | Net |")
w("|---|---|---|---|")
for v in sorted(otc["venue_netting"], key=lambda z:-abs(z["net_egld"])):
    w(f"| {v['venue']} | {v['desk_to_venue_egld']:,.0f} | {v['venue_to_desk_egld']:,.0f} | {v['net_egld']:+,.0f} |")
w()
pk=otc["peak_window_renetted"]
w(f"**Run #17 peak window re-netted** (closing run #19's top recommendation): {pk['gross_egld']:,.0f} gross was {pk['circular_share_pct']:.0f}% circular, leaving **{pk['net_one_way_egld']:,.0f} EGLD one-way**. Circularity is now measured at {pk['circular_share_pct']:.0f}% / 80% / {otc['circular_share_pct']:.0f}% across three windows - roughly constant, which means the gross series has the right SHAPE and the wrong UNITS (a ~3-5x overstatement of distribution), rather than being unusable.")
w()
w(f"_Gross series (runs #12-#20, paginated, NOT netted for circularity): " +
  " / ".join(f"{k[3:]}: {v:,.0f}" for k,v in otc["gross_series_egld_7d"].items()) + "._")
w()
w(f"_NET one-way series (measured anchors only): " +
  " / ".join(f"{k}: {v:,.0f}" for k,v in otc["net_one_way_series_egld_7d"].items()) + "._")
w()
w(f"_{otc['series_note']}_")
w()
w("### Demand Instruments"); w()
w("| Instrument | Reading | Prior |")
w("|---|---|---|")
w(f"| Identifiable bid absorbed (7d) | **{dem['identifiable_bid_absorbed_egld_7d']:,.0f} EGLD** | 0 for the prior 2 weeks - REACTIVATED |")
w(f"| Bid vs distribution | {dem['bid_to_distribution_ratio_pct']:.0f}% of net one-way OTC distribution | ~18% of the run #15 tranche, ~11% of run #17's |")
w(f"| Mega Whale erd18mv2z6r2 | {dem['mega_whale_balance_egld']:,.0f} EGLD ({dem['mega_whale_change_egld']:+,.0f}) | unchanged to the decimal for 2 weeks before this |")
w(f"| Coinbase Routing wallet | {dem['coinbase_routing_balance_egld']:,.0f} EGLD, received {dem['coinbase_routing_inflow_egld']:,.0f} | dry at 77.13 for 2 weeks; funder = {dem['coinbase_routing_funder_label']} |")
w(f"| DEX turnover ratio | {dem['dex_turnover_ratio_pct']:.2f}% of pool TVL/day | {dem['previous_dex_turnover_ratio_pct']:.2f}% |")
b=dem["withdrawal_breadth"]
w(f"| Withdrawal breadth (>1K EGLD, ex-pipeline) | {b['distinct_recipients_ex_pipeline']} addresses / {b['total_egld_ex_pipeline']:,.0f} EGLD | 2nd measurement |")
w(f"| Withdrawal breadth (raw) | {b['distinct_recipients_raw']} addresses / {b['total_egld_raw']:,.0f} EGLD | {b['pipeline_share_pct']:.0f}% went to the OTC pipeline (was 84%) |")
w()
w("### Top Large Transactions (>1,000 EGLD)"); w()
w("| Value EGLD | Flow | From -> To | Time |")
w("|---|---|---|---|")
for t in wi["large_transactions"][:15]:
    w(f"| {t['value_egld']:,.0f} | {t['flow_type']} | {t['sender_label'][:24]} -> {t['receiver_label'][:24]} | {t['timestamp'][5:16] if t['timestamp'] else ''} |")
w()
w("### Analysis"); w(); w(wi["analysis"]); w(); w("---"); w()

w("## Staking Power Map"); w()
s=si["summary"]
w(f"- **Total delegated**: {egld(s['total_delegated_egld'])} EGLD across {s['num_providers']} active providers")
w(f"- **Concentration**: top-5 {si['concentration']['top_5_share_pct']:.1f}%, top-10 {si['concentration']['top_10_share_pct']:.1f}%, HHI {si['concentration']['hhi']:.4f} ({si['concentration']['hhi_interpretation']})")
w(f"- **APR**: weighted avg {s['apr_weighted_avg']:.2f}%, range {s['apr_min']:.1f}%-{s['apr_max']:.2f}%")
w(f"- **Delegators**: {si['churn']['total_delegators_current']:,} ({si['churn']['delegators_added']:+}), {si['churn']['providers_gaining_delegators']} gaining / {si['churn']['providers_losing_delegators']} losing")
w()
w("### Top Providers (WoW)"); w()
w("| # | Provider | Locked EGLD | APR | Fee | WoW Delta |")
w("|---|---|---|---|---|---|")
for p in si["top_providers"][:12]:
    wow=f"{p['wow_change_egld']:+,.0f}" if p['wow_change_egld'] is not None else "n/a"
    w(f"| {p['rank']} | {p['identity']} | {egld(p['locked_egld'])} | {p['apr_pct']:.2f}% | {p['fee_pct']:.1f}% | {wow} |")
w()
w("### APR Distribution"); w()
w("| Bucket | Providers | Locked EGLD |")
w("|---|---|---|")
for b in si["apr_distribution"]["buckets"]:
    w(f"| {b['label']} | {b['provider_count']} | {egld(b['total_locked_egld'])} |")
w()
w("### APR Outliers"); w()
w("**Top APR (qualified, >5K locked):**"); w()
for p in si["apr_outliers"]["top_apr"]:
    w(f"- {p['identity']}: {p['apr_pct']:.2f}% APR @ {p['fee_pct']:.1f}% fee - {egld(p['locked_egld'])} EGLD")
w()
w("**Lowest fee (qualified, >5K locked):**"); w()
for p in si["apr_outliers"]["lowest_fee"]:
    w(f"- {p['identity']}: {p['fee_pct']:.1f}% fee @ {p['apr_pct']:.2f}% APR - {egld(p['locked_egld'])} EGLD")
w()

# Reward behavior section
if "reward_behavior" in si:
    rb=si["reward_behavior"]
    w("### Reward Behavior"); w()
    w(f"- **Compound rate** (function-level): {rb.get('compound_pct_at_function_level','n/a')}% (vs 58.81% last run: **+3.44pp and a NEW TRACKED HIGH**, above run #16's 61.59% peak - delegators compounding INTO the drawdown)")
    w()
    w("**Delegator fates by tier:**"); w()
    for tier, data in rb.get("delegator_fates_by_tier", {}).items():
        fates=data.get("fates",{})
        total_ev=data.get("events_count",0)
        total_val=data.get("total_value_egld",0)
        w(f"- **{tier}**: {total_ev} events / {total_val:.1f} EGLD")
        for fate,v in fates.items():
            w(f"    - {fate}: {v.get('count',0)} events, {v.get('value_egld',0):.2f} EGLD")
    w()
    w("**Provider operator behavior (30d outbound):**"); w()
    for op in rb.get("provider_operators",[]):
        nm=op.get("provider"); bal=op.get("operator_balance_egld",0); n=op.get("outbound_count_30d",0)
        w(f"- {nm}: balance {bal:.2f} EGLD, {n} outbound txs")
        for dest,d2 in op.get("destinations_by_category",{}).items():
            w(f"    - {dest}: {d2.get('value_egld',0):.1f} EGLD")
    w()

w("### Analysis"); w(); w(si["analysis"]); w(); w("---"); w()

w("## Token & DeFi Activity"); w(); w("### Top Tokens by Holders"); w()
w("| Token | Holders | WoW Delta | Price | Market Cap |")
w("|---|---|---|---|---|")
def pricestr(p):
    if not p: return "n/a"
    if p>1e-4: return usd(p)
    return f"${p:.2e}"
for t in ta["top_by_holders"][:10]:
    hc=f"{t['holders_change']:+}" if t['holders_change'] is not None else "n/a"
    w(f"| {t['name']} ({t['identifier']}) | {t['holders']:,} | {hc} | {pricestr(t['price_usd'])} | {usd(t['market_cap_usd'])} |")
w()
w("### Top Tokens by Transactions"); w()
w("| Token | Transactions |")
w("|---|---|")
for t in ta["top_by_volume"][:10]:
    w(f"| {t['name']} ({t['identifier']}) | {t['transactions']:,} |")
w()
w("### Top Tokens by Market Cap"); w()
w("| Token | Price | Market Cap |")
w("|---|---|---|")
for t in ta["top_by_market_cap"][:10]:
    w(f"| {t['name']} ({t['identifier']}) | {pricestr(t['price_usd'])} | {usd(t['market_cap_usd'])} |")
w()
if ta["newly_issued"]:
    w("### Newly-Issued Tokens (last 7 days)"); w()
    w("| Token | Holders | Txs | Deployer | Issued |")
    w("|---|---|---|---|---|")
    for t in ta["newly_issued"]:
        w(f"| {t['name']} ({t['identifier']}) | {t['holders']} | {t['transactions']} | {t.get('deployer','')[:16]}... | {t['issued_at'][5:16]} |")
    w()
else:
    w("### Newly-Issued Tokens (last 7 days)"); w()
    w("One issuance detected (JLBM-d9fa48, JallowBM) but filtered by the run #15 quality bar at 6 holders / 5 transactions. New-token formation remains effectively zero for a third consecutive week.")
    w()
w("### xExchange (DEX)"); w()
x=ta["xexchange"]
w(f"- **24h volume**: {usd(x['total_volume_24h_usd'])} across {x['total_pairs']} pairs")
w(f"- **MEX price**: {x['mex_price_usd']:.3e} ({x['mex_price_change_wow_pct']:+.1f}% WoW), mcap {usd(x['mex_market_cap_usd'])}")
w(f"- **Top pair**: {x['top_pair']} - {usd(x['top_pair_volume_24h_usd'])} ({x['top_pair_dominance_pct']:.1f}% dominance)")
if len(x['top_pairs_by_volume']) > 1:
    w(f"- **#2 pair**: {x['top_pairs_by_volume'][1]['name']} - {usd(x['top_pairs_by_volume'][1]['volume_24h_usd'])} ({x['top_pairs_by_volume'][1]['share_pct']:.1f}%)")
w()
w("### Token Analysis"); w(); w(ta["analysis"]); w()
w("### DeFi Per-Protocol Breakdown"); w()
w("| Protocol | Category | TVL USD | TVL EGLD | WoW% (EGLD) | 24h transfers | Signal |")
w("|---|---|---|---|---|---|---|")
for p in da["protocol_breakdown"]:
    tu=usd(p["tvl_usd"]) if p["tvl_usd"] else "-"
    te=egld(p["tvl_egld"]) if p["tvl_egld"] else "-"
    wow=f"{p['tvl_wow_change_pct']:+.1f}%" if p["tvl_wow_change_pct"] is not None else "-"
    tr=f"{p['transfers_24h']:,}" if p["transfers_24h"] else "-"
    w(f"| {p['protocol']} | {p['category']} | {tu} | {te} | {wow} | {tr} | {p['health_signal']} |")
w()
w("### DeFi Analysis"); w(); w(da["analysis"]); w(); w("---"); w()

w("## Anomalies & Trend Indicators"); w(); w("### Anomalies"); w()
for a in an:
    w(f"- **{a['metric']}** [{a['method']}, {a['severity']}]: {a['description']}")
    w()
w("### Trend Indicators"); w()
w("**Consecutive streaks:**"); w()
for s2 in ti["consecutive_streaks"]:
    w(f"- _{s2['metric']}_ ({s2['direction']}, {s2['weeks']} wks): {s2['interpretation']}")
    w()
w("**Regime shifts:**"); w()
for r in ti["regime_shifts"]:
    w(f"- _{r['metric']}_: {r['description']}")
    w()
w("**Accelerating exchange outflows:**"); w()
for ao in ti["accelerating_exchange_outflows"]:
    cum=f"{ao['cumulative_change_pct']:+.1f}%" if ao.get('cumulative_change_pct') is not None else "n/a"
    w(f"- _{ao['exchange']}_ ({ao['trend']}, {ao['weeks_in_trend']} wks, cum {cum}): {ao['interpretation']}")
    w()
if ti["token_supply_events"]:
    w("**Token supply events:**"); w()
    for tse in ti["token_supply_events"]:
        w(f"- _{tse['identifier']} ({tse['name']})_ - {tse['event']} {tse['change_pct']:+.2f}%: {tse['description']}")
        w()
vm=ti["validator_movements"]
w(f"**Validator movements:** {vm['providers_joining']} joining, {vm['providers_leaving']} leaving (named, filtered), net {vm['net_provider_change']}. Provider count unchanged at 107 active - system-contract aggregators excluded as data artifact.")
w(); w("---"); w()
w("## Watch List"); w()
for i,it in enumerate(wl,1):
    w(f"{i}. **{it['item']}** _(week {it['weeks_on_list']})_ - {it['reason']}")
    w()
w("---"); w()
w("## Methodology Notes"); w()
ml=R["meta_learning"]
new_addr_count = ml.get('new_addresses_discovered',0)
if isinstance(new_addr_count, list): new_addr_count = len(new_addr_count)
w(f"- **Run #{ml['run_number']}** . {ml['action_items_completed']}/{ml['action_items_from_previous']} prior action items completed . {new_addr_count} new addresses discovered")
w(f"- **Data sources**: {len(ml['endpoints_that_worked'])} endpoints OK; failed: {', '.join(ml['endpoints_that_failed'])}")
w(f"- **Most valuable insight**: {ml['most_valuable_insight']}")
w()
w("**Methodology changes this run:**"); w()
for c in ml["methodology_changes"]:
    w(f"- {c}")
w()
w("**Dashboard feature suggestions (this run):**"); w()
for sg in ml.get("dashboard_feature_suggestions",[]):
    w(f"- _{sg['title']}_ (priority {sg['priority']}): {sg['motivation']}")
    w()
w("_Generated by the autonomous weekly intel agent. All EGLD amounts human-readable (raw / 10^18). All times UTC._")

open("/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/reports/2026-08-10.md","w").write("\n".join(L)+"\n")
print("WROTE reports/2026-08-10.md  lines:",len(L))
