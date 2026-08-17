#!/usr/bin/env python3
import json
R=json.load(open("/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/reports/2026-08-17.json"))
m=R["metadata"]; nh=R["network_health"]; wi=R["whale_intelligence"]; si=R["staking_intelligence"]
ta=R["token_activity"]; da=R["defi_activity"]; an=R["anomalies"]; ti=R["trend_indicators"]; wl=R["watch_list"]
e=nh["economics"]; d=nh["deltas"]
_prevR=json.load(open("/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/reports/2026-08-10.json"))
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
w(f"**Period**: 2026-08-10 -> 2026-08-17 (7 days)")
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
w(f"| Price action | OUTPERFORMED | {d['price_change_pct']:+.2f}% WoW to ${e['egld_price_usd']:.2f} with BTC {100*(m['btc_price_usd']-pecon['btc_price_usd'])/pecon['btc_price_usd']:+.2f}% and ETH {100*(m['eth_price_usd']-pecon['eth_price_usd'])/pecon['eth_price_usd']:+.2f}% - first EGLD-specific up-week since run #16, in the week the OTC feed switched off |")
w(f"| OTC feed | SWITCHED OFF | UPbit tranche {otc['upbit_reload_egld']:,.0f} EGLD vs 319,000 last week (-96%); desks returned {otc['venue_netting'][[v['venue'] for v in otc['venue_netting']].index('UPbit')]['desk_to_venue_egld']:,.0f} to UPbit |")
w(f"| OTC wave #2 | DID NOT ESCALATE | Wave-window net one-way {wave['net_one_way_egld']:,.0f} EGLD (Aug 3-17), ~{100*wave['net_one_way_egld']/otc['peak_window_renetted']['net_one_way_egld']:.0f}% of the re-netted run #17 peak; both pre-committed thresholds missed |")
w(f"| Netting method | WEEKLY FRAME OVERSTATES {wave['weekly_frame_overstatement_pct']:.0f}% | Summed weekly nets {wave['sum_of_weekly_nets_egld']:,.0f} vs wave-netted {wave['net_one_way_egld']:,.0f} - circularity crosses week boundaries; weekly figures are UPPER BOUNDS |")
w(f"| Identifiable bid | BACK TO ZERO | Absorber and Coinbase Routing both recorded zero transactions; absent in {dem['weeks_at_zero_in_last_four']} of the last 4 weeks - dormancy revived as structural |")
w(f"| Direct-node unwind | WITHDRAWN (artifact) | The staked-minus-delegated residual also holds unbonding in flight; one wallet's {ub['total_egld']:,.0f} explains this week's {ub['raw_residual_egld']:+,.0f} flip. Corrected direct-node {ub['corrected_direct_node_egld']:+,.0f} |")
w(f"| Unbonding queue | {ub['total_egld']:,.0f} EGLD LANDS IN <8 DAYS | One wallet, two providers ({ub['legs'][0]['amount']:,.0f} + {ub['legs'][1]['amount']:,.0f}); destination is next run's highest-value question |")
if fe:
    w(f"| Delegation fees | TWO PROVIDERS AT 100% | {fe[0]['provider']} {fe[0]['fee_from_pct']:.0f}%->100% and {fe[1]['provider']} {fe[1]['fee_from_pct']:.0f}%->100%, delegator APR zero; run #20's 'first competitive fee cut' withdrawn |")
w(f"| Exchange flows | UNINFORMATIVE | Net {wi['exchange_flows']['net_change_egld']:+,.0f} EGLD, smallest in the series; Binance's move is intra-entity (hot -127,064 -> custody +118,440) |")
w(f"| Binance staking | RE-PARKED | Custody +118,440 to 3,475,540 in one traceable transfer, NOT delegated; -37,110 from the peak |")
w(f"| DEX depth | IMPROVING (2nd wk) | Turnover {x0['previous_turnover_ratio_pct']:.2f}% -> {x0['turnover_ratio_pct']:.2f}% of pool TVL/day on volume {x0['dex_vol_wow_pct']:+.0f}%; still below the ~4% bid threshold |")
w(f"| MEX vs EGLD | REAL, NOT STALE PRICING | MEX/WEGLD is the #{x0['mex_pair_depth']['depth_rank']} deepest pool (${x0['mex_pair_depth']['tvl_usd']:,.0f}, {x0['mex_pair_depth']['trades_24h']} trades/24h); 4th week of MEX >= EGLD |")
w(f"| Stablecoins | SHARPEST EXIT IN TRACKING | USDT -15.42% (100,287 tokens), USDC -0.57%; 9th run with no inflow week |")
w(f"| DeFi leverage | STILL FLAT | USH +0.05% for a 2nd week - borrowers did not chase a +3% price week |")
w(f"| Liquid staking | XOXNO REDEMPTION BENIGN | XEGLD -0.80% (decelerating); callers' flows traced - native delegation and unlabeled wallets, ZERO to exchanges |")
w(f"| Staking | ONE-WALLET DISTORTION | Delegation {si['summary']['total_delegated_egld']:,.0f} ({-236435:+,}), 97% one wallet; total staked {d['staked_egld_added']:+,} to {e['staked_egld']:,} |")
w(f"| Delegator base | INERT (9th wk) | {si['churn']['delegators_added']:+} WoW at {si['churn']['total_delegators_current']:,} - unmoved even by two providers going to zero yield |")
w(f"| Staking concentration | Healthy | HHI {si['concentration']['hhi']:.3f}; top-5 {si['concentration']['top_5_share_pct']:.1f}%; {si['apr_distribution'].get('zero_apr_providers',0)} providers now at 0% APR |")
w(f"| New tokens | ZERO (5th wk) | One issuance: 'Bitcoin' (BTC-8549df), 3 holders - a ticker impersonation, filtered by the quality bar |")
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
w("### OTC Pipeline - weekly netting vs wave-window netting"); w()
w(f"Gross desk throughput was **{otc['gross_outbound_egld_7d']:,.0f} EGLD** out / {otc['gross_inbound_egld_7d']:,.0f} in, with **{otc['circular_share_pct']:.0f}% round-trip churn** and {otc['net_one_way_egld_7d']:,.0f} EGLD one-way on the weekly frame. UPbit fed only **{otc['upbit_reload_egld']:,.0f} EGLD** (vs 319,000 last week) and the desks returned 130,000 to UPbit, so run #20's pre-committed escalation thresholds (net >300K on a tranche >350K) both **missed**.")
w()
w(f"**The weekly frame is the wrong unit for a multi-week wave.** Netting wave #2 feed-to-drain across {wave['window']} gives {wave['gross_outbound_egld']:,.0f} gross, {wave['circular_share_pct']:.0f}% circular and **{wave['net_one_way_egld']:,.0f} EGLD genuinely one-way** - {wave['weekly_frame_overstatement_egld']:,.0f} EGLD ({wave['weekly_frame_overstatement_pct']:.0f}%) less than the {wave['sum_of_weekly_nets_egld']:,.0f} the two weekly nets sum to, because UPbit's feed landed in one week and its return leg in the next. Every weekly net one-way figure is therefore an **upper bound**.")
w()
w("| Venue | Desk -> venue (wave) | Venue -> desk (wave) | Net (wave) |")
w("|---|---|---|---|")
for v in sorted(wave["net_by_venue"], key=lambda k:-abs(wave["net_by_venue"][k])):
    w(f"| {v} | {wave.get('outbound_by_venue',{}).get(v,0):,.0f} | {wave.get('inbound_by_venue',{}).get(v,0):,.0f} | {wave['net_by_venue'][v]:+,.0f} |")
w()
w("**This week only (weekly frame):**"); w()
w("| Venue | Desk -> venue | Venue -> desk | Net |")
w("|---|---|---|---|")
for v in sorted(otc["venue_netting"], key=lambda z:-abs(z["net_egld"])):
    w(f"| {v['venue']} | {v['desk_to_venue_egld']:,.0f} | {v['venue_to_desk_egld']:,.0f} | {v['net_egld']:+,.0f} |")
w()
bfl=otc.get("backfilled_windows",[])
if bfl:
    w("**Backfilled windows (closes run #20 recommendation #7):**"); w()
    w("| Window | Gross | Circular | Net one-way |")
    w("|---|---|---|---|")
    for b in bfl:
        w(f"| {b['window']} | {b['gross_egld']:,.0f} | {b['circular_share_pct']:.0f}% | {b['net_one_way_egld']:,.0f} |")
    pk=otc["peak_window_renetted"]
    w(f"| {pk['window']} | {pk['gross_egld']:,.0f} | {pk['circular_share_pct']:.0f}% | {pk['net_one_way_egld']:,.0f} |")
    w()
w(f"_Gross series (runs #12-#21, paginated, NOT netted for circularity): " +
  " / ".join(f"{k[3:]}: {v:,.0f}" for k,v in otc["gross_series_egld_7d"].items()) + "._")
w()
w(f"_NET one-way series (five measured anchors): " +
  " / ".join(f"{k}: {v:,.0f}" for k,v in otc["net_one_way_series_egld_7d"].items()) + "._")
w()
w(f"_{otc['series_note']}_")
w()
w("### Demand Instruments"); w()
w("| Instrument | Reading | Prior |")
w("|---|---|---|")
w(f"| Identifiable bid absorbed (7d) | **{dem['identifiable_bid_absorbed_egld_7d']:,.0f} EGLD** | 5,748 last week - BACK TO ZERO, the pre-committed maintenance-transfer branch |")
w(f"| Weeks at zero (last 4) | {dem['weeks_at_zero_in_last_four']} of 4 | dormancy revived as a structural finding |")
w(f"| Mega Whale erd18mv2z6r2 | {dem['mega_whale_balance_egld']:,.0f} EGLD ({dem['mega_whale_change_egld']:+.2f}) | zero transactions this week |")
w(f"| Coinbase Routing wallet | {dem['coinbase_routing_balance_egld']:,.1f} EGLD, received {dem['coinbase_routing_inflow_egld']:,.0f} | refilled 5,764 last week, idle this week |")
w(f"| DEX turnover ratio | {dem['dex_turnover_ratio_pct']:.2f}% of pool TVL/day | {dem['previous_dex_turnover_ratio_pct']:.2f}% |")
b=dem["withdrawal_breadth"]
w(f"| Withdrawal breadth (>1K EGLD, ex-pipeline) | {b['distinct_recipients_ex_pipeline']} addresses / {b['total_egld_ex_pipeline']:,.0f} EGLD | 2nd measurement |")
w(f"| Withdrawal breadth (raw) | {b['distinct_recipients_raw']} addresses / {b['total_egld_raw']:,.0f} EGLD | {b['pipeline_share_pct']:.0f}% went to the OTC pipeline (was 47% last week, 84% in run #19) |")
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
    w("### Unbonding In Flight (the residual correction)"); w()
    w(f"One wallet (`{u['wallet'][:20]}...`) is unwinding **{egld(u['total_egld'])} EGLD** across two providers - {u['share_of_delegation_decline_pct']:.0f}% of this week's delegation TVL decline and essentially all of the {u['raw_residual_egld']:+,.0f} staked-minus-delegated residual. Corrected for in-flight unbonding, direct-node stake **grew {u['corrected_direct_node_egld']:+,.0f}**, which withdraws the three-run 'direct-node unwind' narrative.")
    w()
    w("| Provider | Amount EGLD | unDelegate date | Days to unbond |")
    w("|---|---|---|---|")
    for l in u["legs"]:
        w(f"| {l['provider']} | {egld(l['amount'])} | {l['date']} | {l['days_to_unbond']:.1f} |")
    w()

# Reward behavior section
if "reward_behavior" in si:
    rb=si["reward_behavior"]
    w("### Reward Behavior"); w()
    w(f"- **Compound rate** (function-level): {rb.get('compound_pct_at_function_level','n/a')}% (vs 59.54% last run: -0.47pp, flat and inside the 55-62% band the series has held for eleven runs)")
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
    w("One issuance detected - `BTC-8549df`, named \"Bitcoin\", 3 holders / 23 transactions - filtered by the run #15 quality bar (>10 holders, >5 txs). It is a ticker impersonation rather than a launch. Qualifying new-token formation is now zero for a FIFTH consecutive week.")
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
w(f"**Validator movements:** {vm['providers_joining']} joining, {vm['providers_leaving']} leaving, net {vm['net_provider_change']}. 106 active providers. The leaver went from 122,947 EGLD locked to zero (7 users) - the first >50K departure in tracking, and the second leg of the same wallet's 229,865 EGLD unwind.")
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

open("/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/reports/2026-08-17.md","w").write("\n".join(L)+"\n")
print("WROTE reports/2026-08-17.md  lines:",len(L))
