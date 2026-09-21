#!/usr/bin/env python3
import json
R=json.load(open("/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/reports/2026-09-21.json"))
m=R["metadata"]; nh=R["network_health"]; wi=R["whale_intelligence"]; si=R["staking_intelligence"]
ta=R["token_activity"]; da=R["defi_activity"]; an=R["anomalies"]; ti=R["trend_indicators"]; wl=R["watch_list"]
e=nh["economics"]; d=nh["deltas"]
_prevR=json.load(open("/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/reports/2026-09-14.json"))
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
w(f"**Period**: 2026-09-14 -> 2026-09-21 (chain halted 2026-09-19 07:41 UTC: flow windows cover 5.3 days)")
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
ob=dem["exchange_orderbook"]; mexe=x0["mex_pair_event"]
hi=wi["chain_halt_incident"]
w(f"| CHAIN LIVENESS | HALTED | No block since {hi['halted_since_utc']}; MultiversX: VM-level atomicity exploit, fix on shadow fork, targeted recovery planned |")
w(f"| Exploit | ~{(hi['attacker_balance_egld']+hi['contract_balance_egld']+hi['fanout_total_egld'])/1e6:,.0f}M EGLD INVALID | Attacker {hi['attacker_balance_egld']/1e6:.1f}M + contract {hi['contract_balance_egld']/1e6:.1f}M; fan-out {hi['fanout_total_egld']/1e6:.2f}M; exchange deposits {sum(hi['exchange_deposits_egld'].values())/1e6:.2f}M |")
w(f"| Price action | ROUND TRIP | {d['price_change_pct']:+.2f}% WoW to ${e['egld_price_usd']:.2f}; ${hi['price_path']['at_halt_usd']:.2f} at halt, low ${hi['price_path']['post_halt_low_usd']:.2f}; BTC {100*(m['btc_price_usd']-pecon['btc_price_usd'])/pecon['btc_price_usd']:+.2f}% |")
w(f"| Exchange flow | NET OF INCIDENT | {wi['exchange_flows']['net_change_egld']:+,.0f} net; raw {wi['exchange_flows']['raw_net_change_egld_including_incident']:+,.0f} |")
w(f"| OTC pipeline | QUIET, THEN STOPPED | Net one-way {otc['net_one_way_egld_7d']:,.0f} ({otc['circular_share_pct']:.0f}% circular); UPbit feed {otc['upbit_reload_egld']:,.0f}; wave #4 {wave['net_one_way_egld']:,.0f} |")
w(f"| Hatom MEX incident | RECOVERED ON CHAIN | Pools resumed Sep 17; recovery sold 270B MEX via whitelisted paused pools; EGLD market back to {x0['mex_incident_recovery']['egld_money_market_balance']:,.0f} |")
w(f"| Compound rate | BACK TO BAND | {rbx['compound_pct_at_function_level']:.2f}% ({rbx['compound_vs_claim']['redelegate_count']} vs {rbx['compound_vs_claim']['claim_count']}) |")
w(f"| Staked ratio | SETTLED BAND | {100*e['staked_ratio']:.2f}% ({d['staked_ratio_change_pp']:+.2f}pp); withdraws returned {ub['queue_this_week']['withdraw_egld_returned']:,.0f} vs {ub['queue_this_week']['undelegated_egld']:,.0f} new unDelegations |")
w(f"| Address poisoning | NEW | Lookalikes of both desks dusting 33 routers each; no misdirected transfer |")
w(f"| DEX volume | NOT EVALUABLE | No blocks in the 24h before the snapshot |")
w(f"| Delegator base | FLAT, 14TH WEEK | {si['churn']['delegators_added']:+,} to {si['churn']['total_delegators_current']:,} |")
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
w("### Chain Halt and Exploit"); w()
w(wi["chain_halt_incident"]["method_note"]); w()
w("| Destination of minted EGLD | EGLD |"); w("|---|---|")
for k_,v_ in sorted(wi["chain_halt_incident"]["fanout_by_destination_egld"].items(), key=lambda x:-x[1]): w(f"| {k_} | {v_:,.0f} |")
w()
w("### OTC Pipeline - quiet week before the halt"); w()
w(f"Gross {otc['gross_outbound_egld_7d']:,.0f} out / {otc['gross_inbound_egld_7d']:,.0f} in, {otc['circular_share_pct']:.0f}% circular, **{otc['net_one_way_egld_7d']:,.0f} EGLD one-way**. UPbit fed **{otc['upbit_reload_egld']:,.0f}**; desk float {otc['previous_desk_balance_egld']:,.0f} -> **{otc['desk_balance_egld']:,.0f}** (a refilled float, not a stock). Wave #4 netted Sep 7 to the halt as one window: **{wave['net_one_way_egld']:,.0f} EGLD**.")
w()
w("**Feed by parent venue (7d):** " + ", ".join(f"{r['venue']} {r['egld_7d']:,.0f}" for r in otc['feed_by_parent_venue']))
w()
w("**This week (weekly frame), two-hop resolved:**"); w()
w("| Venue | Desk -> venue | Venue -> desk | Net |")
w("|---|---|---|---|")
for v in sorted(otc["venue_netting"], key=lambda z:-abs(z["net_egld"])):
    w(f"| {v['venue']} | {v['desk_to_venue_egld']:,.0f} | {v['venue_to_desk_egld']:,.0f} | {v['net_egld']:+,.0f} |")
w()
w(f"**Wave #4 window (Sep 7 - halt), feed-to-drain:**"); w()
w("| Venue | Desk -> venue (wave) | Venue -> desk (wave) | Net (wave) |")
w("|---|---|---|---|")
for v in sorted(wave["net_by_venue"], key=lambda k:-abs(wave["net_by_venue"][k])):
    w(f"| {v} | {wave.get('outbound_by_venue',{}).get(v,0):,.0f} | {wave.get('inbound_by_venue',{}).get(v,0):,.0f} | {wave['net_by_venue'][v]:+,.0f} |")
w()
bfl=otc.get("backfilled_windows",[])
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
w("| Instrument | Reading |")
w("|---|---|")
w(f"| CEX 7d spot volume | {ob['spot_volume_7d_egld']:,.0f} EGLD (prior {ob['spot_volume_prior_7d_egld']:,.0f}) |")
w(f"| Delivery share of spot | {ob['net_one_way_share_of_spot_volume_pct']:.2f}% (last week {ob['previous_net_one_way_share_of_spot_volume_pct']:.2f}%) |")
for vn in ("binance","bybit","upbit","coinbase","gate","all_venues"):
    w(f"| ±2% depth {vn} | ask ${ob[vn]['depth_plus2_usd']:,.0f} / bid ${ob[vn]['depth_minus2_usd']:,.0f} on ${ob[vn]['volume_24h_usd']:,.0f} 24h |")
w(f"| DEX volume in EGLD | {dem['dex_volume_egld_24h']:,.0f}/day (prev {dem['previous_dex_volume_egld_24h']:,.0f}) |")
b=dem["withdrawal_breadth"]
w(f"| Withdrawal breadth ex-pipeline | {b['distinct_recipients_ex_pipeline']} / {b['total_egld_ex_pipeline']:,.0f} EGLD, top two {b['top_two_share_pct']:.0f}% |")
w(f"| Absorber scan | {dem['absorber_scan']['terminals_scanned']} terminals, {dem['absorber_scan']['total_retained_egld']:,.0f} EGLD held |")
w(f"| Identifiable bid | {dem['identifiable_bid_absorbed_egld_7d']:,.0f} (retired) |")
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
    w(f"_{u['status']}_")
    w()
    w("| Contract | Amount EGLD | unDelegate date | Days remaining |")
    w("|---|---|---|---|")
    for l in u["legs"]:
        w(f"| {l['provider']} | {egld(l['amount'])} | {l['date']} | {l['days_to_unbond']:.2f} |")
    w()
    if q:
        w(f"**Queue this week**: {q['distinct_callers']} wallets unDelegated **{q['undelegated_egld']:,.0f} EGLD**; {q['withdraw_calls']} withdraw calls (prev {q['previous_withdraw_calls']}). _{q['coverage_note']}_")
        w()
        w("| Wallet | Pending EGLD | Days remaining | Wallet balance |")
        w("|---|---|---|---|")
        for r in q["largest_legs"][:8]:
            w(f"| `{r['wallet'][:16]}...` | {r['amount_egld']:,.0f} | {r['days_remaining']:.2f} | {r['wallet_balance_egld']:,.2f} |")
        w()
    w(f"**Residual note**: staked-minus-delegated moved {u['raw_residual_egld']:+,.0f}; no direct-node figure is published.")
    w()

# Reward behavior section
if "reward_behavior" in si:
    rb=si["reward_behavior"]
    w("### Reward Behavior"); w()
    for kf in rb["key_findings"]:
        w(f"- {kf}")
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
    w("_Zero exchange destinations across every sampled operator wallet, a thirteenth consecutive run._")
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
    for t in _ni: w(f"- `{t['identifier']}` {t['name']}: {t['holders']} holders, {t['transactions']} txs - {t['note']}")
    w()
w("### xExchange (DEX)"); w()
x=ta["xexchange"]
w(f"- **24h volume**: {usd(x['total_volume_24h_usd'])} across {x['total_pairs']} pairs ({x['dex_vol_wow_pct']:+.1f}% in USD)")
w(f"- **24h volume IN EGLD**: {x['dex_volume_egld_24h']:,.0f} EGLD vs {x['previous_dex_volume_egld_24h']:,.0f} last week - **{x['dex_vol_egld_wow_pct']:+.1f}%**")
w(f"- **Turnover**: {x['turnover_ratio_pct']:.2f}% of pool TVL/day vs {x['previous_turnover_ratio_pct']:.2f}%; pool TVL {usd(x['pool_tvl_usd'])} ({x['pool_tvl_egld']:,.0f} EGLD vs {x['previous_pool_tvl_egld']:,.0f})")
w(f"- **MEX price**: {x['mex_price_usd']:.3e} ({x['mex_price_change_wow_pct']:+.1f}% WoW, CoinGecko - the MEX/WEGLD pool is paused), mcap {usd(x['mex_market_cap_usd'])}")
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
        w(f"- _{tse['identifier']} ({tse['name']})_ - {tse['event']} "
      + (f"{tse['change_pct']:+.2f}%" if tse.get('change_pct') is not None else "(first measurement)")
      + f": {tse['description']}")
        w()
vm=ti["validator_movements"]
w(f"**Validator movements:** {vm['providers_joining']} joining, {vm['providers_leaving']} leaving; zero locked>0 -> 0 transitions; two identity renames (cslabsio -> chainstatelabs, kevinlallement -> dinovox) excluded from exit counts.")
w(); w("---"); w()
w("## Pre-Committed Test Scoreboard"); w()
pct=R.get("pre_committed_tests",[])
_res=[t for t in pct if t.get("resolved_in_run")==25]
_open=[t for t in pct if t["status"]=="open"]
_ap=sum(1 for t in _res if t.get("outcome")=="as_predicted")
w(f"**Resolved this run**: {len(_res)} ({_ap} as predicted, {100*_ap/len(_res) if _res else 0:.0f}%). **Open into run #26**: {len(_open)}.")
w()
w("| Test | Registered | Outcome | Measured |")
w("|---|---|---|---|")
for t in _res:
    w(f"| {t['id']} | run #{t['registered_in_run']} | **{t['outcome']}** | {t['measured_value']} |")
w()
for t in _res:
    w(f"- **{t['id']}** ({t['outcome']}): {t['resolution']}")
    w()
w("**Open tests carried into run #26:**"); w()
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

open("/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/reports/2026-09-21.md","w").write("\n".join(L)+"\n")
print("WROTE reports/2026-09-21.md  lines:",len(L))
