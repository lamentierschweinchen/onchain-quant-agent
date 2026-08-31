#!/usr/bin/env python3
import json
R=json.load(open("/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/reports/2026-08-31.json"))
m=R["metadata"]; nh=R["network_health"]; wi=R["whale_intelligence"]; si=R["staking_intelligence"]
ta=R["token_activity"]; da=R["defi_activity"]; an=R["anomalies"]; ti=R["trend_indicators"]; wl=R["watch_list"]
e=nh["economics"]; d=nh["deltas"]
_prevR=json.load(open("/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/reports/2026-08-24.json"))
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
w(f"**Period**: 2026-08-24 -> 2026-08-31 (7 days)")
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
wave=otc["wave_window_netting"]; ub=si["unbonding_in_flight"]; fe=si.get("fee_events",[])
rbx=si["reward_behavior"]
w(f"| Price action | EGLD-SPECIFIC UPSIDE | {d['price_change_pct']:+.2f}% WoW to ${e['egld_price_usd']:.2f} with BTC {100*(m['btc_price_usd']-pecon['btc_price_usd'])/pecon['btc_price_usd']:+.2f}% and ETH {100*(m['eth_price_usd']-pecon['eth_price_usd'])/pecon['eth_price_usd']:+.2f}% - EGLD rose while BOTH majors fell. First decoupling to the upside since run #16 |")
w(f"| Desk inventory | RECORD, 2.4x PRIOR RECORD | Combined desks {otc['desk_balance_egld']:,.0f} EGLD ({otc['desk_balance_egld']-otc['previous_desk_balance_egld']:+,.0f}) AFTER delivering {otc['net_one_way_egld_7d']:,.0f} one-way. The pipeline accumulated faster than it distributed - a first |")
w(f"| OTC feed | ESCALATING, 3x THRESHOLD | UPbit tranche {otc['upbit_reload_egld']:,.0f} EGLD; series 14,000 / 297,000 / {otc['upbit_reload_egld']:,.0f}. Gross throughput {otc['gross_outbound_egld_7d']:,.0f} out / {otc['gross_inbound_egld_7d']:,.0f} in |")
w(f"| OTC destinations | FIVE VENUES NOW | Two-hop net: Binance.com +{[v for v in otc['venue_netting'] if v['venue']=='Binance.com'][0]['net_egld']:,.0f}, Bybit +{[v for v in otc['venue_netting'] if v['venue']=='Bybit'][0]['net_egld']:,.0f}, Gate.io +{[v for v in otc['venue_netting'] if v['venue']=='Gate.io'][0]['net_egld']:,.0f}, Bitget +{[v for v in otc['venue_netting'] if v['venue']=='Bitget'][0]['net_egld']:,.0f} (new); UPbit sole net source |")
w(f"| Binance | NOW A DESK FEEDER | Custody -196,758 (2nd week, -497K over two). Hot wallet forwarded {135003:,} EGLD into the desks via the run #19 and #20 feeders plus one direct transfer. Custody and pipeline watches are ONE instrument |")
w(f"| Netting frame | WAVE STRADDLES, AS PREDICTED | Wave #3 ({wave['window'].split(' (')[0]}) nets {wave['net_one_way_egld']:,.0f} vs {wave['sum_of_weekly_nets_egld']:,.0f} summed weekly ({wave['weekly_frame_overstatement_pct']:.0f}% overstatement). This week's {otc['circular_share_pct']:.0f}% circularity below the 63-80% band called it in advance |")
w(f"| Validator set | RUN #22's HEADLINE WITHDRAWN | THREE deregistrations, not one: ledgerbyfigment (run #13 window, 170,808 EGLD, 3,883 users), stakedinc (whole archive, 637 users), p2p_org_ (exit COMPLETED, nodes 50 -> 0) |")
w(f"| Participation inertia | MEASURED IN MONTHS | ledgerbyfigment -2.0% of delegators in 11 weeks at 0% APR; stakedinc -0.3% across the archive; p2p_org_ 2 unDelegate calls from 1,244 users. Books fall 20-52%, people 1-7% |")
w(f"| Delegator base | FLAT, CLEAN READING | {si['churn']['delegators_added']:+,} to {si['churn']['total_delegators_current']:,} with no deregistration artifact to net out - 11th consecutive flat week |")
w(f"| Identifiable bid | RETIRED | All {dem['absorber_scan']['terminals_scanned']} desk terminals scanned: every one a zero-balance router retaining {dem['absorber_scan']['retained_share_pct']:.1f}% of {dem['absorber_scan']['total_received_from_desks_egld']:,.0f} EGLD. No absorbers exist to discover |")
w(f"| DEX turnover | RATIO HELD, EGLD FELL | {x0['turnover_ratio_pct']:.2f}% (above the 5% regime branch) but EGLD volume {x0['dex_vol_egld_wow_pct']:+.1f}% to {x0['dex_volume_egld_24h']:,.0f} EGLD/day. Both sides scaled with price |")
w(f"| Withdrawal breadth | BEST READING YET | {dem['withdrawal_breadth']['distinct_recipients_ex_pipeline']} recipients / {dem['withdrawal_breadth']['total_egld_ex_pipeline']:,.0f} EGLD ex-pipeline (21 / 133,521 last week); pipeline share {dem['withdrawal_breadth']['pipeline_share_pct']:.0f}% vs 88%. First full 7d scan, no page-cap |")
w(f"| Exchange flows | UNINFORMATIVE | Net {wi['exchange_flows']['net_change_egld']:+,.0f} EGLD; UPbit is desk loading, Binance is internal plumbing. Ex those two: mild INFLOW led by Bybit and Bitget, both hub destinations |")
w(f"| Unbonding queue | FIRST FULL-SET SCAN | {ub['queue_this_week']['undelegated_egld']:,.0f} EGLD from {ub['queue_this_week']['distinct_callers']} wallets across all 107 contracts - 2.1x run #22's ten-provider partial. Residual again fully absorbed |")
w(f"| The 229,865 unbond | RETIRED | Unmoved for a 2nd full week - zero outbound txs, zero function calls. The no-action branch fires |")
w(f"| Compound rate | 4TH FALL, LOWEST OF TEN | {rbx['compound_pct_at_function_level']:.2f}% ({rbx['compound_vs_claim']['redelegate_count']} vs {rbx['compound_vs_claim']['claim_count']}). Test unresolvable - branches were non-contiguous |")
w(f"| DeFi leverage | DE-RISKED, 2ND WEEK | USH burned {[t for t in ti['token_supply_events'] if t['identifier']=='USH-111e09'][0]['change_pct']:+.2f}% into a rising price for a second week; Hatom Lending EGLD-TVL {[p for p in da['protocol_breakdown'] if p['protocol']=='Hatom Lending'][0]['tvl_wow_change_pct']:+.2f}%, inverse ratio 0.69 - the exhaustion watch is CLEARED |")
w(f"| Stablecoins | BOTH CONTRACTED | USDC {[t for t in ti['token_supply_events'] if t['identifier']=='USDC-c76f1f'][0]['change_pct']:+.2f}% and USDT {[t for t in ti['token_supply_events'] if t['identifier']=='USDT-f8c08c'][0]['change_pct']:+.2f}% - ~$77K of on-chain dollars left during a +6.4% price week |")
w(f"| Liquid staking | ZERO SUBSCRIPTION, 6 WKS | SEGLD, XEGLD and SWTAO all inside the noise band on supply through a cumulative ~+39% move |")
w(f"| MEX vs EGLD | STREAK BROKE, CLOSED | MEX {x0['mex_price_change_wow_pct']:+.2f}% vs EGLD {d['price_change_pct']:+.2f}% - first underperformance in six weeks. Mechanism test failed both branches; labelled unexplained flow and closed |")
w(f"| Staking concentration | Healthy | HHI {si['concentration']['hhi']:.3f}; top-5 {si['concentration']['top_5_share_pct']:.1f}%; {si['apr_distribution'].get('zero_apr_providers',0)} providers at sub-5% APR holding {si['apr_distribution'].get('zero_apr_locked_egld',0):,.0f} EGLD |")
w(f"| New tokens | ZERO (7th wk) | {len(ta['newly_issued'])} issuances, all with exactly 1 holder |")
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
w("### Whale Tier Stratification (common-address basis - only wallets present in BOTH snapshots)"); w()
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
w("### OTC Pipeline - a record delivery AND a record reload in the same week"); w()
w(f"Gross desk throughput was **{otc['gross_outbound_egld_7d']:,.0f} EGLD** out / {otc['gross_inbound_egld_7d']:,.0f} in, with **{otc['circular_share_pct']:.0f}% round-trip churn** and **{otc['net_one_way_egld_7d']:,.0f} EGLD one-way**. UPbit fed **{otc['upbit_reload_egld']:,.0f} EGLD** into the desks - the tranche series is now 14,000 / 297,000 / {otc['upbit_reload_egld']:,.0f}, three times run #21's escalation threshold. **The number that matters more is what did NOT go out**: desk inventory rose {otc['desk_balance_egld']-otc['previous_desk_balance_egld']:+,.0f} to **{otc['desk_balance_egld']:,.0f} EGLD**, 2.4x last week's record, after already delivering {otc['net_one_way_egld_7d']:,.0f} one-way. For comparison the entire run #17 peak wave delivered 409,680 from a starting inventory of 335,430. This pipeline is accumulating faster than it distributes, which has not happened before in tracking.")
w()
bfl=otc.get("backfilled_windows",[])
w(f"**The straddle was called in advance.** Run #22 narrowed run #21's blanket rule to: weekly netting overstates only when a wave straddles a week boundary, and the diagnostic tell is a circularity reading outside the 63-80% band. This week's circularity is {otc['circular_share_pct']:.0f}% - below the band - and the wave duly straddles: netted feed-to-drain over {wave['window']} it delivered **{wave['net_one_way_egld']:,.0f} EGLD** one-way against **{wave['sum_of_weekly_nets_egld']:,.0f}** from summing the two weekly nets, a **{wave['weekly_frame_overstatement_pct']:.0f}% overstatement**. Use the wave figure for distribution; the weekly numbers are upper bounds.")
w()
w("**This week (weekly frame), two-hop resolved:**"); w()
w("| Venue | Desk -> venue | Venue -> desk | Net |")
w("|---|---|---|---|")
for v in sorted(otc["venue_netting"], key=lambda z:-abs(z["net_egld"])):
    w(f"| {v['venue']} | {v['desk_to_venue_egld']:,.0f} | {v['venue_to_desk_egld']:,.0f} | {v['net_egld']:+,.0f} |")
w()
w(f"**Wave #3 ({wave['window'].split(' (')[0]}), feed-to-drain:**"); w()
w("| Venue | Desk -> venue (wave) | Venue -> desk (wave) | Net (wave) |")
w("|---|---|---|---|")
for v in sorted(wave["net_by_venue"], key=lambda k:-abs(wave["net_by_venue"][k])):
    w(f"| {v} | {wave.get('outbound_by_venue',{}).get(v,0):,.0f} | {wave.get('inbound_by_venue',{}).get(v,0):,.0f} | {wave['net_by_venue'][v]:+,.0f} |")
w()
if bfl:
    w("**Measured windows:**"); w()
    w("| Window | Gross | Circular | Net one-way |")
    w("|---|---|---|---|")
    for b in bfl:
        w(f"| {b['window']} | {b['gross_egld']:,.0f} | {b['circular_share_pct']:.0f}% | {b['net_one_way_egld']:,.0f} |")
    pk=otc["peak_window_renetted"]
    w(f"| {pk['window']} | {pk['gross_egld']:,.0f} | {pk['circular_share_pct']:.0f}% | {pk['net_one_way_egld']:,.0f} |")
    w(f"| {wave['window']} | {wave['gross_outbound_egld']:,.0f} | {wave['circular_share_pct']:.0f}% | {wave['net_one_way_egld']:,.0f} |")
    w()
w(f"_Gross series (runs #12-#23, paginated, NOT netted for circularity): " +
  " / ".join(f"{k[3:]}: {v:,.0f}" for k,v in otc["gross_series_egld_7d"].items()) + "._")
w()
w(f"_NET one-way series (measured anchors): " +
  " / ".join(f"{k}: {v:,.0f}" for k,v in otc["net_one_way_series_egld_7d"].items()) + "._")
w()
w(f"_{otc['series_note']}_")
w()
w("### Demand Instruments"); w()
w("| Instrument | Reading | Prior |")
w("|---|---|---|")
w(f"| Identifiable bid absorbed (7d) | **{dem['identifiable_bid_absorbed_egld_7d']:,.0f} EGLD** - RETIRED | zero for a 3rd week and 4 of the last 5 |")
w(f"| Absorber scan (NEW, run #22 rec #8) | {dem['absorber_scan']['terminals_scanned']} desk terminals scanned, **{dem['absorber_scan']['terminals_retaining_over_half']} retain what they receive** | {dem['absorber_scan']['total_received_from_desks_egld']:,.0f} EGLD passed through, {dem['absorber_scan']['total_retained_egld']:,.0f} ({dem['absorber_scan']['retained_share_pct']:.1f}%) stayed |")
w(f"| Mega Whale erd18mv2z6r2 | {dem['mega_whale_balance_egld']:,.0f} EGLD ({dem['mega_whale_change_egld']:+.4f}) | zero transactions, balance unchanged to 4dp |")
w(f"| Coinbase Routing wallet | {dem['coinbase_routing_balance_egld']:,.1f} EGLD | idle, 3rd week |")
w(f"| DEX turnover ratio (USD) | **{dem['dex_turnover_ratio_pct']:.2f}%** of pool TVL/day | {dem['previous_dex_turnover_ratio_pct']:.2f}% - held above the 5% regime branch |")
w(f"| DEX volume IN EGLD (NEW, run #22 rec #6) | **{dem['dex_volume_egld_24h']:,.0f} EGLD/day** | {dem['previous_dex_volume_egld_24h']:,.0f} last week - FELL {100*(dem['dex_volume_egld_24h']-dem['previous_dex_volume_egld_24h'])/dem['previous_dex_volume_egld_24h']:+.1f}% |")
w(f"| Pool depth IN EGLD | {dem['pool_tvl_egld']:,.0f} EGLD | {dem['previous_pool_tvl_egld']:,.0f} - {100*(dem['pool_tvl_egld']-dem['previous_pool_tvl_egld'])/dem['previous_pool_tvl_egld']:+.1f}% |")
w(f"| WEGLD/USDC share of volume | {dem['wegld_usdc_share_of_volume_pct']:.1f}% | ex that pair the venue traded {usd(dem['ex_wegld_usdc_volume_usd'])} = {dem['ex_wegld_usdc_volume_egld']:,.0f} EGLD in 24h |")
b=dem["withdrawal_breadth"]
w(f"| Withdrawal breadth (>1K EGLD, ex-pipeline) | **{b['distinct_recipients_ex_pipeline']} addresses / {b['total_egld_ex_pipeline']:,.0f} EGLD** | 21 / 133,521 last week - best reading since the measure was built |")
w(f"| Withdrawal breadth (raw) | {b['distinct_recipients_raw']} addresses / {b['total_egld_raw']:,.0f} EGLD | {b['pipeline_share_pct']:.0f}% went to the OTC pipeline (was 88%). FULL 7-day scan, NO page-cap terminations - not a lower bound for the first time |")
w()
w("**The identifiable-bid instrument is retired rather than repaired.** Run #22 recommended discovering absorbers dynamically from the desks' outbound terminals instead of watching one wallet. All 14 were scanned and every one is a zero-balance, high-nonce pass-through router: of 505,597 EGLD received, 8,545 (1.7%) stayed. There are no absorbers on the outbound side of this pipeline to find. What is left is turnover - which held its USD ratio while EGLD throughput fell - and ex-pipeline withdrawal breadth, which had its best reading yet and is the one genuinely constructive instrument in the report.")
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

if si.get("fee_events"):
    w("### Service-Fee Events"); w()
    w("| Provider | Fee | APR | Locked EGLD | WoW EGLD | Users | WoW users |")
    w("|---|---|---|---|---|---|---|")
    for fev in si["fee_events"]:
        w(f"| {fev['provider']} | {fev['fee_from_pct']:.0f}% -> {fev['fee_to_pct']:.0f}% | {fev['apr_from_pct']:.2f}% -> {fev['apr_to_pct']:.2f}% | {egld(fev['locked_egld'])} | {fev['locked_wow_egld']:+,.0f} | {fev['users']:,} | {fev['users_wow']:+d} |")
    w()
if si.get("unbonding_in_flight"):
    u=si["unbonding_in_flight"]
    q=u.get("queue_this_week",{})
    w("### Unbonding Queue"); w()
    w(f"**The run #21 unbond is RETIRED.** Wallet `{u['wallet'][:20]}...` still holds {egld(u['total_egld'])} EGLD unbonded and unclaimed inside two delegation contracts, unmoved for a second full week: balance unchanged, zero outbound transactions, zero function calls. The no-action branch run #22 added to the test fires, and the position stops being tracked as forward supply.")
    w()
    w("| Contract | Amount EGLD | unDelegate date | Days remaining |")
    w("|---|---|---|---|")
    for l in u["legs"]:
        w(f"| {l['provider']} | {egld(l['amount'])} | {l['date']} | {l['days_to_unbond']:.2f} |")
    w()
    if q:
        w(f"**First FULL-SET scan (run #22 rec #5)**: {q['distinct_callers']} distinct wallets unDelegated **{q['undelegated_egld']:,.0f} EGLD** across ALL 107 provider contracts, not just the movers - 2.1x run #22's 70,498 ten-provider figure. Measured pending unbonding {q['measured_pending_egld']:,.0f} EGLD. _{q['coverage_note']}_")
        w()
        w("| Wallet | Pending EGLD | Days remaining | Wallet balance |")
        w("|---|---|---|---|")
        for r in q["largest_legs"][:8]:
            w(f"| `{r['wallet'][:16]}...` | {r['amount_egld']:,.0f} | {r['days_remaining']:.2f} | {r['wallet_balance_egld']:,.2f} |")
        w()
    w(f"**Residual note**: staked-minus-delegated came to {u['raw_residual_egld']:+,.0f} against {q.get('undelegated_egld',0):,.0f} EGLD of measured unbonding in flight. The residual is fully absorbed with room to spare, so **no direct-node figure is published** for a second consecutive run - and the run #22 rule that produced that answer is now confirmed on independent data rather than merely asserted.")
    w()

# Reward behavior section
if "reward_behavior" in si:
    rb=si["reward_behavior"]
    w("### Reward Behavior"); w()
    w(f"- **Compound rate** (function-level): **{rb['compound_pct_at_function_level']:.2f}%** ({rb['compound_vs_claim']['redelegate_count']} reDelegateRewards vs {rb['compound_vs_claim']['claim_count']} claimRewards) - the LOWEST of ten readings and a FOURTH consecutive decline. Series: 58.54 / 60.35 / 61.59 / 60.19 / 58.81 / 62.25 / 59.54 / 59.07 / 57.03 / {rb['compound_pct_at_function_level']:.2f}.")
    w(f"- **The pre-committed test could not resolve**: run #22's branches were 'below 56%' and 'above 59%' and this landed in the gap. Second consecutive run to lose a test to a specification defect rather than to the data. Branches must partition the outcome space.")
    w(f"- Read on the trend instead: four declines spanning a flat week, a +30% week and a +{d['price_change_pct']:.0f}% week is not a price-following series - it is a slow drift toward taking yield in cash.")
    w()
    w("**Delegator fates by tier:**"); w()
    for tier, data in rb.get("delegator_fates_by_tier", {}).items():
        w(f"- **{tier}**: {data.get('total_events',0)} events / {data.get('total_value_egld',0):.2f} EGLD")
        for fate,c in data.get("by_count",{}).items():
            v=data.get("by_value_egld",{}).get(fate,0)
            w(f"    - {fate}: {c} events, {v:.2f} EGLD")
    w()
    w("**Provider operator behaviour (30d outbound):**"); w()
    for op in rb.get("provider_operators",[]):
        nm=op.get("provider"); bal=op.get("owner_balance_egld") or 0; n=op.get("outbound_count",0)
        w(f"- {str(nm)[:34]}: owner `{str(op.get('owner_address'))[:14]}...` ({op.get('owner_label')}), balance {bal:.2f} EGLD, {n} outbound txs")
        for dest,v in (op.get("fates_by_value_egld") or {}).items():
            w(f"    - {dest}: {v:,.1f} EGLD")
    w()
    w("_Zero exchange destinations across every sampled operator wallet, for an eleventh consecutive run._")
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
if False:
    pass
else:
    w("### Newly-Issued Tokens (last 7 days)"); w()
    _ni=ta["newly_issued"]
    w(f"{len(_ni)} issuances cleared the ESDT system-SC scan and **all {len(_ni)} have exactly 1 holder** (" + ", ".join(f"`{t['identifier']}`" for t in _ni) + f"). None clears the quality bar (>10 holders, >5 transactions). Qualifying new-token formation is now zero for a **SEVENTH consecutive week** - primary issuance on this chain is effectively dormant.")
    w()
w("### xExchange (DEX)"); w()
x=ta["xexchange"]
w(f"- **24h volume**: {usd(x['total_volume_24h_usd'])} across {x['total_pairs']} pairs ({x['dex_vol_wow_pct']:+.1f}% in USD)")
w(f"- **24h volume IN EGLD** (run #22 rec #6): {x['dex_volume_egld_24h']:,.0f} EGLD vs {x['previous_dex_volume_egld_24h']:,.0f} last week - **{x['dex_vol_egld_wow_pct']:+.1f}%**. The USD ratio held only because both sides scaled with a {d['price_change_pct']:+.1f}% price")
w(f"- **Turnover**: {x['turnover_ratio_pct']:.2f}% of pool TVL/day vs {x['previous_turnover_ratio_pct']:.2f}%; pool TVL {usd(x['pool_tvl_usd'])} ({x['pool_tvl_egld']:,.0f} EGLD vs {x['previous_pool_tvl_egld']:,.0f})")
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
w(f"**Validator movements:** {vm['providers_joining']} joining, {vm['providers_leaving']} leaving this week, {si['summary']['num_providers']} active providers. The entries below are **BACKFILLED**, not new: applying run #22's deregistration signature (`locked == 0` with nodes or users attached) backwards over the stored snapshot archive found two operator exits that were never reported. **ledgerbyfigment** went from 170,808 EGLD to zero between the 2026-06-08 and 2026-06-15 snapshots - inside the run #13 window - keeping 7 nodes and 3,961 delegators, and has paid 0% APR for eleven weeks since. **stakedinc** has been zero-locked with 10 nodes and ~639 users across the entire stored history. Run #22's claim that p2p_org_ was the first operator deregistration in tracking is therefore **withdrawn**; it was the third and the smallest, and it COMPLETED this week when its owner called `removeNodes` eleven times plus `unBondNodes`, taking numNodes 50 -> 0.")
w(); w("---"); w()
w("## Pre-Committed Test Scoreboard"); w()
pct=R.get("pre_committed_tests",[])
_res=[t for t in pct if t.get("resolved_in_run")==23]
_open=[t for t in pct if t["status"]=="open"]
_ap=sum(1 for t in _res if t.get("outcome")=="as_predicted")
w(f"**Resolved this run**: {len(_res)} ({_ap} as predicted, {100*_ap/len(_res) if _res else 0:.0f}%). **Open into run #24**: {len(_open)}.")
w()
w("| Test | Registered | Outcome | Measured |")
w("|---|---|---|---|")
for t in _res:
    w(f"| {t['id']} | run #{t['registered_in_run']} | **{t['outcome']}** | {t['measured_value']} |")
w()
for t in _res:
    w(f"- **{t['id']}** ({t['outcome']}): {t['resolution']}")
    w()
w("**Open tests registered for run #24:**"); w()
w("| Test | Claim | Threshold |")
w("|---|---|---|")
for t in _open:
    w(f"| {t['id']} | {t['claim']} | {t['threshold']} |")
w()
w("**Claims withdrawn this run:**"); w()
for c in R["meta_learning"].get("withdrawn_claims",[]):
    w(f"- _\"{c['claim']}\"_ (asserted in run(s) {', '.join('#'+str(x) for x in c['asserted_in_runs'])}) - {c['reason']} **Replacement**: {c['replacement']}")
    w()
w("---"); w()
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

open("/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/reports/2026-08-31.md","w").write("\n".join(L)+"\n")
print("WROTE reports/2026-08-31.md  lines:",len(L))
