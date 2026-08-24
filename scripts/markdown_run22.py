#!/usr/bin/env python3
import json
R=json.load(open("/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/reports/2026-08-24.json"))
m=R["metadata"]; nh=R["network_health"]; wi=R["whale_intelligence"]; si=R["staking_intelligence"]
ta=R["token_activity"]; da=R["defi_activity"]; an=R["anomalies"]; ti=R["trend_indicators"]; wl=R["watch_list"]
e=nh["economics"]; d=nh["deltas"]
_prevR=json.load(open("/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/reports/2026-08-17.json"))
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
w(f"**Period**: 2026-08-17 -> 2026-08-24 (7 days)")
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
w(f"| Price action | LARGEST MOVE IN 22 RUNS | {d['price_change_pct']:+.2f}% WoW to ${e['egld_price_usd']:.2f} with BTC {100*(m['btc_price_usd']-pecon['btc_price_usd'])/pecon['btc_price_usd']:+.2f}% and ETH {100*(m['eth_price_usd']-pecon['eth_price_usd'])/pecon['eth_price_usd']:+.2f}% - a BETA move, EGLD landed between the majors |")
w(f"| OTC feed | RESTARTED AT SCALE | UPbit tranche {otc['upbit_reload_egld']:,.0f} EGLD vs 14,000 last week; gross throughput {otc['gross_outbound_egld_7d']:,.0f} (3.4x); standing-programme branch fired |")
w(f"| Desk inventory | RECORD, STILL LOADED | Combined desks {otc['desk_balance_egld']:,.0f} EGLD ({otc['desk_balance_egld']-otc['previous_desk_balance_egld']:+,.0f}) - more loaded than delivered, the drain leg is ahead |")
w(f"| OTC destinations | ORDER BOOKS, NOT HOLDERS | Two-hop net: Bybit +{[v for v in otc['venue_netting'] if v['venue']=='Bybit'][0]['net_egld']:,.0f}, Binance.com +{[v for v in otc['venue_netting'] if v['venue']=='Binance.com'][0]['net_egld']:,.0f}, Gate.io +{[v for v in otc['venue_netting'] if v['venue']=='Gate.io'][0]['net_egld']:,.0f}; UPbit sole net source |")
w(f"| Netting method | RULE NARROWED | July episode re-netted feed-to-drain = {[b for b in otc['backfilled_windows']][0]['net_one_way_egld']:,.0f} vs 833,754 summed weekly (0.47% apart). Weekly framing is fine UNLESS a wave straddles a boundary - August's does ({wave['weekly_frame_overstatement_pct']:.0f}%) |")
w(f"| Binance custody | DRAWDOWN BRANCH FIRED (2nd time) | -300,000 in one traceable transfer into the hot wallet; custody now {[p for p in wi['wallet_changes'] if p['label']=='Binance Staking'][0]['balance_current_egld']:,.0f}, hot {[p for p in wi['wallet_changes'] if p['label']=='Binance.com'][0]['balance_current_egld']:,.0f}. Pre-registered as bearish since run #9 |")
w(f"| Validator set | FIRST OPERATOR EXIT | p2p_org_ called unStakeNodes: 67,500 stake + 2,083 topUp -> ZERO locked, 50 nodes still listed, 1,244 delegators stranded at 0% APR |")
w(f"| Unbonding queue | 229,865 CLAIMABLE, UNCLAIMED | The run #21 unbond completed and was NOT withdrawn - a fourth state none of the three pre-registered branches covered. Plus {ub['queue_this_week']['undelegated_egld']:,.0f} fresh across {ub['queue_this_week']['distinct_callers']} wallets |")
w(f"| Direct-node residual | NO SIGNAL EXTRACTABLE | Residual {ub['raw_residual_egld']:+,.0f} is fully absorbed by unbonding in flight; run #21's +52,848 corrected figure is WITHDRAWN as a partial subtraction |")
w(f"| Delegation fees | TWO PROVIDERS STILL AT 100% | {fe[0]['provider']} {fe[0]['locked_wow_egld']:+,.0f} and {fe[1]['provider']} {fe[1]['locked_wow_egld']:+,.0f} - books did not halve, fee not reversed, nodes not deregistered. Test open into week 2 |")
w(f"| Delegator base | INERT (artifact break) | {si['churn']['delegators_added']:+,} to {si['churn']['total_delegators_current']:,} - but 1,244 are p2p_org_'s users leaving the locked>0 set. Ex-that, -67. Inertia intact |")
w(f"| DEX turnover | TRIPLED - CONSTRUCTIVE BRANCH | {x0['previous_turnover_ratio_pct']:.2f}% -> {x0['turnover_ratio_pct']:.2f}% of pool TVL/day on volume {x0['dex_vol_wow_pct']:+.0f}% with depth also up |")
w(f"| Identifiable bid | ZERO (2nd wk, 3 of 4) | Absorber recorded zero transactions. Contradicts turnover - the single-wallet proxy has stopped being informative |")
w(f"| Exchange flows | UNINFORMATIVE | Net {wi['exchange_flows']['net_change_egld']:+,.0f} EGLD; UPbit's share is the OTC loading leg, Binance's nets out intra-entity. Ex-UPbit: flat |")
w(f"| Withdrawal breadth | HUB-DOMINATED AGAIN | {dem['withdrawal_breadth']['pipeline_share_pct']:.0f}% of exchange outflow went to desks/feeders/routers (was 47%); ex-pipeline {dem['withdrawal_breadth']['distinct_recipients_ex_pipeline']} recipients / {dem['withdrawal_breadth']['total_egld_ex_pipeline']:,.0f} EGLD |")
w(f"| Compound rate | LOWEST OF NINE (3rd fall) | {rbx['compound_pct_at_function_level']:.2f}% ({rbx['compound_vs_claim']['redelegate_count']} vs {rbx['compound_vs_claim']['claim_count']}); institutional tier sold 3 of 4 claims - first tier to lead with selling |")
w(f"| DeFi leverage | DE-RISKED INTO STRENGTH | USH burned {[t for t in ti['token_supply_events'] if t['identifier']=='USH-111e09'][0]['change_pct']:+.2f}% during a +30% week; Hatom Lending EGLD-TVL {[p for p in da['protocol_breakdown'] if p['protocol']=='Hatom Lending'][0]['tvl_wow_change_pct']:+.2f}%, inverse ratio 0.28 (below the 0.30 exhaustion threshold) |")
w(f"| Liquid staking | ZERO SUBSCRIPTION | SEGLD, XEGLD and SWTAO all inside the noise band on supply through a +30% week - nobody converted the rally into a yield position |")
w(f"| Stablecoins | USDT RECOVERED | +0.44% to {int([t for t in ti['token_supply_events'] if t['identifier']=='USDT-f8c08c'][0]['supply_current']):,} - run #21's -15.42% resolves as one desk redeeming, not a bridge drain |")
w(f"| MEX vs EGLD | 5TH WEEK, NO MECHANISM | MEX {x0['mex_price_change_wow_pct']:+.2f}% vs EGLD {d['price_change_pct']:+.2f}%; +9.8pp cumulative over 5 weeks. Supply {-0.151:+.3f}% and pool depth grew with the market - neither explains it |")
w(f"| Staking concentration | Healthy | HHI {si['concentration']['hhi']:.3f}; top-5 {si['concentration']['top_5_share_pct']:.1f}%; {si['apr_distribution'].get('zero_apr_providers',0)} providers at sub-5% APR |")
w(f"| New tokens | ZERO (6th wk) | Two issuances, both below the quality bar - 'Mybigbone' (1 holder) and a ticker-spoof named Bitcoin (3 holders) |")
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
w("### OTC Pipeline - the feed restarted, and the netting rule is narrowed"); w()
w(f"Gross desk throughput was **{otc['gross_outbound_egld_7d']:,.0f} EGLD** out / {otc['gross_inbound_egld_7d']:,.0f} in, with **{otc['circular_share_pct']:.0f}% round-trip churn** (back inside the historical 63-80% band after run #21's anomalous 38%) and **{otc['net_one_way_egld_7d']:,.0f} EGLD one-way**. UPbit fed **{otc['upbit_reload_egld']:,.0f} EGLD** into the desks against 14,000 in the whole of last week - above the ~150,000 threshold run #21 pre-registered, in week one of a two-week window. The desks did NOT drain doing it: combined inventory rose {otc['desk_balance_egld']-otc['previous_desk_balance_egld']:+,.0f} to **{otc['desk_balance_egld']:,.0f} EGLD**, the highest recorded, so more is loaded than has been delivered.")
w()
bfl=otc.get("backfilled_windows",[])
jw=bfl[0] if bfl else None
if jw:
    w(f"**Run #21's blanket upper-bound rule does not survive the July test.** Re-netting the July episode ({jw['window']}) feed-to-drain as ONE window gives **{jw['net_one_way_egld']:,.0f} EGLD** one-way against **833,754** from summing its three weekly nets - **0.47% apart**. Weekly framing was accurate there. The August wave still is not: extended to {wave['window']} it nets {wave['net_one_way_egld']:,.0f} against {wave['sum_of_weekly_nets_egld']:,.0f} summed weekly, a {wave['weekly_frame_overstatement_pct']:.1f}% overstatement, because UPbit feeds in one week and takes back in the next. The corrected rule: **the overstatement is a property of waves that STRADDLE a week boundary**, not of weekly netting as such. The diagnostic tell remains a weekly circularity reading far outside 63-80%.")
    w()
w("**This week (weekly frame), two-hop resolved:**"); w()
w("| Venue | Desk -> venue | Venue -> desk | Net |")
w("|---|---|---|---|")
for v in sorted(otc["venue_netting"], key=lambda z:-abs(z["net_egld"])):
    w(f"| {v['venue']} | {v['desk_to_venue_egld']:,.0f} | {v['venue_to_desk_egld']:,.0f} | {v['net_egld']:+,.0f} |")
w()
w(f"**Wave #2 extended ({wave['window']}), feed-to-drain:**"); w()
w("| Venue | Desk -> venue (wave) | Venue -> desk (wave) | Net (wave) |")
w("|---|---|---|---|")
for v in sorted(wave["net_by_venue"], key=lambda k:-abs(wave["net_by_venue"][k])):
    w(f"| {v} | {wave.get('outbound_by_venue',{}).get(v,0):,.0f} | {wave.get('inbound_by_venue',{}).get(v,0):,.0f} | {wave['net_by_venue'][v]:+,.0f} |")
w()
if jw:
    w("**Measured windows:**"); w()
    w("| Window | Gross | Circular | Net one-way |")
    w("|---|---|---|---|")
    for b in bfl:
        w(f"| {b['window']} | {b['gross_egld']:,.0f} | {b['circular_share_pct']:.0f}% | {b['net_one_way_egld']:,.0f} |")
    pk=otc["peak_window_renetted"]
    w(f"| {pk['window']} | {pk['gross_egld']:,.0f} | {pk['circular_share_pct']:.0f}% | {pk['net_one_way_egld']:,.0f} |")
    w(f"| {wave['window']} | {wave['gross_outbound_egld']:,.0f} | {wave['circular_share_pct']:.0f}% | {wave['net_one_way_egld']:,.0f} |")
    w()
w(f"_Gross series (runs #12-#22, paginated, NOT netted for circularity): " +
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
w(f"| Identifiable bid absorbed (7d) | **{dem['identifiable_bid_absorbed_egld_7d']:,.0f} EGLD** | zero for a 2nd week and 3 of the last 4 |")
w(f"| Mega Whale erd18mv2z6r2 | {dem['mega_whale_balance_egld']:,.0f} EGLD ({dem['mega_whale_change_egld']:+.4f}) | zero transactions this week |")
w(f"| Coinbase Routing wallet | {dem['coinbase_routing_balance_egld']:,.1f} EGLD | idle |")
w(f"| DEX turnover ratio | **{dem['dex_turnover_ratio_pct']:.2f}%** of pool TVL/day | {dem['previous_dex_turnover_ratio_pct']:.2f}% - a 3rd consecutive rise and a step change |")
b=dem["withdrawal_breadth"]
w(f"| Withdrawal breadth (>1K EGLD, ex-pipeline) | {b['distinct_recipients_ex_pipeline']} addresses / {b['total_egld_ex_pipeline']:,.0f} EGLD | 24 / 111,683 last week |")
w(f"| Withdrawal breadth (raw, LOWER BOUND) | {b['distinct_recipients_raw']} addresses / {b['total_egld_raw']:,.0f} EGLD | {b['pipeline_share_pct']:.0f}% went to the OTC pipeline (was 47%; run #17 was 84%). One Binance scan hit the page cap at 2.4 days of coverage |")
w()
w("**The two instruments disagree this week.** Turnover tripled while the identifiable bid read exactly zero. Turnover measures a whole venue and is price-independent; the bid measures one wallet. On this evidence demand returned to the DEX order book and did not return to the wallet the model has been watching for it, and the single-wallet proxy should be repaired or retired.")
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
    w(f"**The run #21 unbond completed and was not withdrawn.** Wallet `{u['wallet'][:20]}...` holds {egld(u['total_egld'])} EGLD across two delegation contracts in a state none of the three pre-registered branches covered: 80,279 reads `seconds_remaining = 0` (claimable now) and 149,585 had 5,279 seconds left at snapshot, and NEITHER has been withdrawn. The wallet sent no outbound transaction all week. The overhang is fully liquid and unclaimed.")
    w()
    w("| Contract | Amount EGLD | unDelegate date | Days remaining |")
    w("|---|---|---|---|")
    for l in u["legs"]:
        w(f"| {l['provider']} | {egld(l['amount'])} | {l['date']} | {l['days_to_unbond']:.2f} |")
    w()
    if q:
        w(f"**Fresh this week**: {q['distinct_callers']} distinct wallets unDelegated **{q['undelegated_egld']:,.0f} EGLD** across the ten providers that moved more than 5,000. Measured pending unbonding {q['measured_pending_egld']:,.0f} EGLD, settling over 2-8 days. _{q['coverage_note']}_")
        w()
        w("| Wallet | Pending EGLD | Days remaining | Wallet balance |")
        w("|---|---|---|---|")
        for r in q["largest_legs"][:8]:
            w(f"| `{r['wallet'][:16]}...` | {r['amount_egld']:,.0f} | {r['days_remaining']:.2f} | {r['wallet_balance_egld']:,.2f} |")
        w()
    w(f"**Residual note**: staked-minus-delegated came to {u['raw_residual_egld']:+,.0f}. p2p_org_'s 69,583 node unstake plus at least {q.get('undelegated_egld',0):,.0f} of delegator unDelegations already exceed it, so **no direct-node figure is published** and run #21's +52,848 is withdrawn as an incomplete subtraction.")
    w()

# Reward behavior section
if "reward_behavior" in si:
    rb=si["reward_behavior"]
    w("### Reward Behavior"); w()
    w(f"- **Compound rate** (function-level): **{rb['compound_pct_at_function_level']:.2f}%** ({rb['compound_vs_claim']['redelegate_count']} reDelegateRewards vs {rb['compound_vs_claim']['claim_count']} claimRewards) - the LOWEST of nine readings and a third consecutive decline. Series: 58.54 / 60.35 / 61.59 / 60.19 / 58.81 / 62.25 / 59.54 / 59.07 / {rb['compound_pct_at_function_level']:.2f}.")
    w(f"- During a +{d['price_change_pct']:.0f}% week this is yield being monetised into strength, not the panic-claiming the run #11 framing describes for declines.")
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
    w("_Zero exchange destinations across every sampled operator wallet, for a tenth consecutive run._")
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
    w("Two issuances cleared the scan and neither clears the quality bar (>10 holders, >5 transactions): `1245-255f1b` named \"Mybigbone\" (1 holder, 0 transactions) and `BTC-8549df` named \"Bitcoin\" with ticker BTC (3 holders, 23 transactions). The second is a ticker impersonation of exactly the kind the filter exists to catch. Qualifying new-token formation is now zero for a SIXTH consecutive week.")
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
w(f"**Validator movements:** {vm['providers_joining']} joining, {vm['providers_leaving']} leaving, net {vm['net_provider_change']}. {si['summary']['num_providers']} active providers. The leaver is **p2p_org_**, and it left in a way no prior departure has: it called `unStakeNodes`, taking 67,500 EGLD of node stake plus 2,083 of topUp to ZERO, while its 50 nodes stay listed, its 1,244 delegators stay attached and its APR reads 0. Prior departures were books draining as delegators left; this is the operator withdrawing the nodes from under the book - the first operator deregistration in twenty-two runs.")
w(); w("---"); w()
w("## Pre-Committed Test Scoreboard"); w()
pct=R.get("pre_committed_tests",[])
_res=[t for t in pct if t.get("resolved_in_run")==22]
_open=[t for t in pct if t["status"]=="open"]
_ap=sum(1 for t in _res if t.get("outcome")=="as_predicted")
w(f"**Resolved this run**: {len(_res)} ({_ap} as predicted, {100*_ap/len(_res) if _res else 0:.0f}%). **Open into run #23**: {len(_open)}.")
w()
w("| Test | Registered | Outcome | Measured |")
w("|---|---|---|---|")
for t in _res:
    w(f"| {t['id']} | run #{t['registered_in_run']} | **{t['outcome']}** | {t['measured_value']} |")
w()
for t in _res:
    w(f"- **{t['id']}** ({t['outcome']}): {t['resolution']}")
    w()
w("**Open tests registered for run #23:**"); w()
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

open("/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/reports/2026-08-24.md","w").write("\n".join(L)+"\n")
print("WROTE reports/2026-08-24.md  lines:",len(L))
