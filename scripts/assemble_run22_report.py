#!/usr/bin/env python3
"""Run #22 stage 2: build reports/2026-08-24.json"""
import json, os
from datetime import datetime, timezone

REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-08-24"
O=json.load(open("/tmp/run22w/derived.json"))
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
status=json.load(open("/tmp/run22w/status.json"))
beh=json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
F=json.load(open(f"{REPO}/data/collected/followup_{RD}.json"))
r21=json.load(open(f"{REPO}/reports/2026-08-17.json"))

lm={}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"): lm[a]=m.get("name","Unknown")

M=O["macro"]; otc=O["otc"]; wave=otc["wave"]; july=otc["july"]
ex=O["exch"]; cust=O["custody"]; bid=O["bid"]; br=O["breadth"]
sk=O["staking"]; tk=O["tokens"]; xx=O["xexchange"]; df=O["defi"]; z=O["z"]
econ=D["economics"]; st=D["stats"]; pecon=prev["economics"]; pact=prev["activity"]
price=M["price"]; pc=M["price_chg"]
def f(x,d=0):
    try: return f"{x:,.{d}f}"
    except: return str(x)

R={}
R["metadata"]={"report_date":RD,"period_start":"2026-08-17","period_end":RD,
  "generated_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
  "egld_price_usd":price,"btc_price_usd":M["btc"],"eth_price_usd":M["eth"],
  "run_number":22,"data_sources_ok":status["ok"],"data_sources_failed":status["failed"]}

# ---------------- executive summary ---------------------------------------
R["executive_summary"]=[
 {"category":"network","severity":"high","finding":
  f"EGLD ROSE {pc:+.2f}% TO ${price:.2f} - THE LARGEST WEEKLY MOVE IN TWENTY-TWO RUNS - AND IT WAS A MARKET MOVE, NOT AN EGLD MOVE. BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%; EGLD landed between them, so the relative-strength read is neutral and the run #16 EGLD-specific-decoupling pattern does NOT apply. Market cap ${f(econ['marketCap'])}. The z-score is +{z['price']['z']:.2f}sigma on an 8-point baseline, but the run #16 caveat runs the other way here: two consecutive up-weeks preceded this one, so the baseline is if anything understating the break."},
 {"category":"whale","severity":"critical","finding":
  f"THE OTC DISTRIBUTION PIPELINE RESTARTED INTO THE RALLY AT FULL SCALE. UPbit fed {f(otc['upbit_feed'])} EGLD into the desks against 14,000 last week (+{100*(otc['upbit_feed']-14000)/14000:,.0f}%), gross desk throughput was {f(otc['gross_out'])} (3.4x), and the desks reloaded +{f(otc['desk_delta'])} to {f(otc['desk_bal'])} combined - the largest desk inventory since tracking began. Weekly net one-way {f(otc['net_one_way'])} at {otc['circ_pct']:.0f}% circularity, back inside the 63-80% band. Destinations resolve two hops to Bybit (+{f(otc['net_by_venue'].get('Bybit',0))} net), Binance.com (+{f(otc['net_by_venue'].get('Binance.com',0))}) and Gate.io (+{f(otc['net_by_venue'].get('Gate.io',0))}) - supply arriving at order books, not dispersing to holders. This RESOLVES run #21's feed-resumption test on the standing-programme branch: the threshold was a tranche above ~150,000 within two weeks and it came in week one at nearly double that."},
 {"category":"whale","severity":"high","finding":
  f"BINANCE'S STAKING CUSTODY DREW DOWN -{f(abs(cust['delta']))} STRAIGHT INTO ITS HOT WALLET - THE BEARISH BRANCH OF A WATCH PRE-REGISTERED SINCE RUN #9, FIRING FOR THE SECOND TIME. One traceable standard transfer of 300,000 on the custody address (the run #15 rule: custody<->hot legs ARE visible even when hot<->external is not). Custody now {f(cust['balance'])}, hot {f(cust['hot_balance'])} (+{f((cust['hot_balance'] or 0)-(cust['hot_previous'] or 0))}). At entity level Binance nets +{f(next((e['net_flow_egld'] for e in ex['entity'] if e['entity']=='Binance'),0))}, so this is intra-entity plumbing in the flow arithmetic - but the DIRECTION is what the watch was registered on, and it points the same way as the OTC restart."},
 {"category":"staking","severity":"critical","finding":
  f"P2P.ORG DEREGISTERED ITS NODES - THE FIRST OPERATOR EXIT IN TRACKING. p2p_org_ called unStakeNodes and went from 67,500 stake + 2,083 topUp to ZERO locked, with 50 nodes still registered and 1,244 delegators still attached to a contract that now pays 0% APR. That single provider is {100*abs(sk['p2p_prev_locked'])/abs(sk['delta_locked']):.0f}% of this week's -{f(abs(sk['delta_locked']))} delegation TVL decline; ex-p2p_org_ delegation was {f(sk['delta_locked']+sk['p2p_prev_locked'],0)}, roughly flat. It also breaks the nine-week flat delegator series on paper ({f(sk['prev_users'])} -> {f(sk['users'])}, {sk['users_delta']:+,}) - but {sk['p2p_users']:,} of the {abs(sk['users_delta']):,} are p2p_org_'s own users dropping out of the locked>0 working set, so ex-p2p_org_ the base moved {sk['users_ex_p2p']:+,} and participation inertia is INTACT."},
 {"category":"staking","severity":"high","finding":
  f"THE 229,865 EGLD UNBOND DID NOT MOVE - AND NONE OF THE THREE PRE-REGISTERED BRANCHES FIRED. Run #21 registered destinations of delegation contract (rotation), exchange/OTC feeder (a 230K distribution event) or the wallet itself (idiosyncratic). The actual state is a fourth one the branches did not anticipate: the EGLD is still sitting INSIDE the delegation contracts, unbonded and unwithdrawn. 80,279 has seconds_remaining = 0 (fully claimable) and 149,585 had 5,279 seconds left at snapshot. The wallet holds {f(F['run21_unbond_wallet']['balance_egld'],0)} EGLD, took one 116 EGLD reward drip and sent nothing. The overhang is now fully liquid and unclaimed, and the destination question simply rolls forward."},
 {"category":"defi","severity":"high","finding":
  f"DEX TURNOVER TRIPLED TO {bid['turnover']:.2f}% OF POOL TVL PER DAY - THE DEMAND INSTRUMENT FIRED ON ITS CONSTRUCTIVE BRANCH FOR THE FIRST TIME. Volume ${f(bid['dexvol'])} (+{100*(bid['dexvol']-bid['prev_dexvol'])/bid['prev_dexvol']:.0f}%) on pool TVL ${f(bid['pooltvl'])} (+{100*(bid['pooltvl']-bid['prev_pooltvl'])/bid['prev_pooltvl']:.1f}%). Series 4.06 / 2.14 / 2.24 / 2.93 / {bid['turnover']:.2f} - a third consecutive rise, far above the ~3.5% threshold run #21 pre-registered. It also directly contradicts the other demand instrument: the identifiable bid read ZERO again (the Mega Whale absorber recorded no transactions for a fifth week in six). Turnover is the price-independent one and it is the one that moved; the absorber measures one wallet."},
 {"category":"trend","severity":"medium","finding":
  f"WEEKLY OTC NETTING IS NOT SYSTEMATICALLY BIASED - RUN #21'S UPPER-BOUND RULE IS TOO BROAD AND IS NARROWED. Re-netting the July episode (Jul 6-27) as ONE feed-to-drain window gives {f(july['net_one_way'])} against {f(july['sum_weekly'])} from summing its three weekly nets, a difference of {abs(july['overstate_pct']):.2f}%. Weekly framing was accurate there. The August wave still is not: extended to Aug 3-24 it nets {f(wave['net_one_way'])} against {f(wave['sum_weekly'])} summed weekly, {wave['overstate_pct']:.1f}% overstatement, because UPbit keeps feeding in one week and taking back in the next. The corrected rule is that the overstatement is a property of waves that STRADDLE a week boundary, not of weekly netting as such."},
 {"category":"defi","severity":"high","finding":
  f"EVERY HOLDING-SIDE INSTRUMENT DE-RISKED INTO THE RALLY, WHICH IS THE WEEK'S REAL SIGNAL. (1) The reward compound rate fell to {beh['aggregates']['compound_vs_claim_at_function_level']['compound_pct_of_reward_decisions']:.2f}% ({beh['aggregates']['compound_vs_claim_at_function_level']['redelegate_count']} redelegate vs {beh['aggregates']['compound_vs_claim_at_function_level']['claim_count']} claim), lowest of nine readings and a third consecutive decline, with the institutional tier selling 3 of 4 claims by count - the first tier ever to lead with selling. "
  f"(2) Hatom Lending's EGLD-denominated deposits fell {df['hatom_lending_egld_pct']:+.2f}% against price {pc:+.2f}% - a correct third up-week confirmation of the bilateral inverse rule, but at a response ratio of {df['inverse_ratio']:.2f}, below the 0.30 depositor-capacity-exhaustion threshold. "
  f"(3) USH burned {tk['lsd']['USH-111e09']['pct']:+.2f}% ({f(abs(tk['lsd']['USH-111e09']['supply']-tk['lsd']['USH-111e09']['prev']))} tokens) INTO the rally - CDP borrowers repaid as collateral appreciated, a sign combination neither the run #11 burn framing nor the run #16 mint framing covers. "
  f"(4) No LSD took a measurable subscription: SEGLD {tk['lsd']['SEGLD-3ad2d0']['pct']:+.3f}%, XEGLD {tk['lsd']['XEGLD-e413ed']['pct']:+.3f}%. Separately USDT recovered to {f(tk['stable']['USDT-f8c08c']['supply'])} ({100*(tk['stable']['USDT-f8c08c']['supply']-549884)/549884:+.2f}%), resolving run #21's -15.42% as one desk redeeming rather than the bridge draining."},
]

# ---------------- network health ------------------------------------------
R["network_health"]={
 "economics":{"egld_price_usd":price,"market_cap_usd":econ["marketCap"],
  "total_supply":econ["totalSupply"],"circulating_supply":econ["circulatingSupply"],
  "staked_egld":econ["staked"],"staked_ratio":M["sr"],"staking_apr":econ["apr"],
  "base_apr":econ["baseApr"],"topup_apr":econ["topUpApr"],
  "token_market_cap_usd":econ["tokenMarketCap"]},
 "activity":{"total_accounts":st["accounts"],"total_transactions":st["transactions"],
  "epoch":st["epoch"],"blocks":st["blocks"],"shards":st["shards"],
  "transactions_7d":st["transactions"]-pact["total_transactions"],
  "avg_daily_transactions":int((st["transactions"]-pact["total_transactions"])/7)},
 "deltas":{"price_change_pct":pc,
  "market_cap_change_pct":100*(econ["marketCap"]-pecon["market_cap_usd"])/pecon["market_cap_usd"],
  "staked_ratio_change_pp":100*(M["sr"]-M["sr_prev"]),
  "apr_change_pp":100*(econ["apr"]-pecon["staking_apr"]),
  "accounts_added":st["accounts"]-pact["total_accounts"],
  "transactions_added":st["transactions"]-pact["total_transactions"],
  "supply_added":econ["totalSupply"]-pecon["total_supply"],
  "staked_egld_added":M["staked_chg"],"epoch_advanced":st["epoch"]-pact["epoch"],
  "btc_correlation_note":f"BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%, EGLD {pc:+.2f}% - EGLD sat between the two majors, so this was a beta week with no EGLD-specific component. Contrast run #16, where EGLD ripped +15.93% against a flat tape and the decoupling was the finding."},
 "analysis":(
  f"EGLD closed the week at ${price:.2f}, {pc:+.2f}% - the largest single-week move across twenty-two runs, and one that arrived with the majors rather than ahead of them (BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%). "
  f"The chain's own metrics moved far less than the price did. Total staked rose {M['staked_chg']:+,.0f} to {f(econ['staked'])} and the staked ratio {100*(M['sr']-M['sr_prev']):+.3f}pp to {100*M['sr']:.2f}%, both inside their usual weekly range; "
  f"{f(st['transactions']-pact['total_transactions'])} transactions settled across {st['epoch']-pact['epoch']} epochs and {f(st['accounts']-pact['total_accounts'])} accounts were created, which is unremarkable against the prior fortnight. "
  f"Supply grew {f(econ['totalSupply']-pecon['total_supply'])} EGLD of emission. "
  f"The gap between a +30% price and flat on-chain participation is the week's structural fact: the move was priced on venues, and the chain-side instruments that DID respond were the ones measuring trading rather than holding - DEX volume +{100*(bid['dexvol']-bid['prev_dexvol'])/bid['prev_dexvol']:.0f}% and turnover {bid['prev_turnover']:.2f}% -> {bid['turnover']:.2f}%. "
  f"Network APR eased {100*(econ['apr']-pecon['staking_apr']):+.3f}pp to {100*econ['apr']:.2f}% as the staked base grew slightly faster than rewards."),
}

# ---------------- whale intelligence --------------------------------------
def entity_interp(e):
    n=e["entity"]; v=e["net_flow_egld"]
    if n=="Binance":
        return f"INTRA-ENTITY, NOT FLOW: hot +{f((cust['hot_balance'] or 0)-(cust['hot_previous'] or 0))} against custody {f(cust['delta'])} - one traceable 300,000 transfer from the staking custody into the hot wallet. The entity net of {v:+,.0f} is the residue, and the run #18 rule says to read it as plumbing. The direction (custody -> hot) is the pre-registered bearish branch of the standing watch."
    if n=="UPbit":
        return f"{v:+,.0f} is the OTC LOADING LEG, not customer withdrawal (run #16 rule). UPbit sent {f(otc['upbit_feed'])} EGLD to its own OTC desk in standard, traceable transfers this week; the balance decline is smaller than the feed because inventory returned from the desks in the same window."
    if n=="Bybit":
        return f"{v:+,.0f}. Bybit is the largest NET RECEIVER from the OTC hub this week (+{f(otc['net_by_venue'].get('Bybit',0))} two-hop-resolved), so the balance build is desk output arriving at the venue rather than independent customer deposits."
    if n=="Gate.io":
        return f"{v:+,.0f} ({e['pct']:+.1f}%), the largest proportional move of the week. Gate.io is simultaneously a net receiver from the hub (+{f(otc['net_by_venue'].get('Gate.io',0))}), so the balance fall is a withdrawal against a hub inflow rather than a clean exit."
    if n=="Coinbase":
        return f"{v:+,.0f} across {e['wallets_count']} wallets. Coinbase (secondary) sent 20,974 EGLD to Unknown Whale B in two chunks; the receiver holds it, so this is a withdrawal to a holder rather than a venue transfer."
    return f"{v:+,.0f} across {e['wallets_count']} wallet(s), {e['pct']:+.2f}%."

R["whale_intelligence"]={
 "large_transactions":O["large_txs"],
 "wallet_changes":O["wallet_changes"],
 "whale_tiers":{
   "mega_whales":dict(threshold_egld=1000000,**O["tiers"]["mega"]),
   "large_whales":dict(threshold_egld=100000,**O["tiers"]["large"]),
   "mid_whales":dict(threshold_egld=10000,**O["tiers"]["mid"])},
 "exchange_flows":{
   "total_exchange_egld_current":ex["total_cur"],
   "total_exchange_egld_previous":ex["total_prev"],
   "net_change_egld":ex["net"],
   "net_change_pct":100*ex["net"]/ex["total_prev"],
   "direction":"outflow" if ex["net"]<0 else "inflow",
   "signal":(
     f"Net exchange flow {ex['net']:+,.0f} EGLD ({100*ex['net']/ex['total_prev']:+.2f}%) - an apparent outflow that decomposes almost entirely into pipeline mechanics. "
     f"UPbit alone is {next((w['change_egld'] for w in ex['per_wallet'] if 'UPbit' in w['exchange']),0):+,.0f} and that is the OTC loading leg: it sent {f(otc['upbit_feed'])} EGLD to its own desk in traceable transfers. "
     f"Ex-UPbit the exchange complex was {ex['net']-next((w['change_egld'] for w in ex['per_wallet'] if 'UPbit' in w['exchange']),0):+,.0f} - flat. "
     f"Binance's {next((e['net_flow_egld'] for e in ex['entity'] if e['entity']=='Binance'),0):+,.0f} hides a 300,000 custody-to-hot transfer that nets out within the entity. "
     f"Bybit's {next((e['net_flow_egld'] for e in ex['entity'] if e['entity']=='Bybit'),0):+,.0f} is desk output arriving, not customer deposits. "
     f"Per the run #14 joint-read rule, the informative channel this week was NOT the balance deltas but the OTC pipeline, which ran {f(otc['gross_out'])} gross and {f(otc['net_one_way'])} net one-way into a +30% price. "
     f"{len(ex['noprior'])} addresses without a prior-week balance were excluded from the delta per the run #18 rule."),
   "by_exchange":[{"exchange":w["exchange"],"change_egld":w["change_egld"],"pct":w["pct"]}
                  for w in ex["per_wallet"]],
   "entity_netting":[{"entity":e["entity"],"wallets_count":e["wallets_count"],
                      "net_flow_egld":e["net_flow_egld"],"interpretation":entity_interp(e)}
                     for e in ex["entity"]]},
 "dormant_activations":[],
 "otc_pipeline":{
   "gross_outbound_egld_7d":otc["gross_out"],"gross_inbound_egld_7d":otc["gross_in"],
   "circular_egld_7d":otc["circular"],"net_one_way_egld_7d":otc["net_one_way"],
   "circular_share_pct":otc["circ_pct"],
   "desk_balance_egld":otc["desk_bal"],"previous_desk_balance_egld":otc["prev_desk"],
   "upbit_reload_egld":otc["upbit_feed"],
   "venue_netting":[{"venue":v,"desk_to_venue_egld":otc["out_by_venue"].get(v,0),
                     "venue_to_desk_egld":otc["in_by_venue"].get(v,0),
                     "net_egld":otc["net_by_venue"][v]}
                    for v in sorted(otc["net_by_venue"],key=lambda k:-abs(otc["net_by_venue"][k]))],
   "gross_series_egld_7d":{**r21["whale_intelligence"]["otc_pipeline"]["gross_series_egld_7d"],
                           "run22":otc["gross_out"]},
   "net_one_way_series_egld_7d":{**r21["whale_intelligence"]["otc_pipeline"]["net_one_way_series_egld_7d"],
                                 "run22":otc["net_one_way"]},
   "circularity_series_pct":{**r21["whale_intelligence"]["otc_pipeline"]["circularity_series_pct"],
                             "run22":round(otc["circ_pct"],1)},
   "peak_window_renetted":r21["whale_intelligence"]["otc_pipeline"]["peak_window_renetted"],
   "backfilled_windows":[
     {"window":july["window"]+" (JULY EPISODE re-netted as ONE window, run #22)",
      "gross_egld":july["gross_out"],"circular_egld":july["circular"],
      "net_one_way_egld":july["net_one_way"],"circular_share_pct":july["circ_pct"],
      "net_by_venue":july["net_by_venue"]}],
   "wave_window_netting":{
     "window":wave["window"]+" (WAVE #2 extended feed-to-drain)",
     "gross_outbound_egld":wave["gross_out"],"gross_inbound_egld":wave["gross_in"],
     "circular_egld":wave["circular"],"circular_share_pct":wave["circ_pct"],
     "net_one_way_egld":wave["net_one_way"],"sum_of_weekly_nets_egld":wave["sum_weekly"],
     "weekly_frame_overstatement_egld":wave["overstate_egld"],
     "weekly_frame_overstatement_pct":wave["overstate_pct"],
     "net_by_venue":wave["net_by_venue"],
     "outbound_by_venue":wave["out_by_venue"],"inbound_by_venue":wave["in_by_venue"],
     "note":(f"Wave #2 now spans three weeks (Aug 3-24) because the feed restarted after a one-week pause. "
             f"Netted feed-to-drain it delivered {f(wave['net_one_way'])} EGLD of genuine one-way movement against {f(wave['sum_weekly'])} from summing the three weekly nets - a {wave['overstate_pct']:.1f}% overstatement, driven as before by UPbit feeding in one week and receiving in the next. "
             f"CRITICALLY, the July episode does NOT show this: re-netted as one window (Jul 6-27) it gives {f(july['net_one_way'])} against {f(july['sum_weekly'])} summed weekly, {abs(july['overstate_pct']):.2f}% apart. "
             f"So run #21's blanket 'every weekly net is an upper bound' is narrowed: the overstatement is a property of waves that straddle a week boundary, and July's did not.")},
   "series_note":(
     f"gross_series is pipeline ACTIVITY and must not be read as distribution volume; net_one_way is the distribution measure. "
     f"This week gross {f(otc['gross_out'])} and net {f(otc['net_one_way'])} differ 3.0x. "
     f"Circularity {otc['circ_pct']:.0f}% is back inside the historical 63-80% band after run #21's anomalous 38%, which was itself the diagnostic tell that a return leg had landed whose feed sat in the prior window.")},
 "demand_instruments":{
   "identifiable_bid_absorbed_egld_7d":bid["absorbed"],
   "mega_whale_balance_egld":bid["mega_bal"],"mega_whale_change_egld":bid["mega_delta"],
   "coinbase_routing_balance_egld":bid["cbr_bal"],"coinbase_routing_inflow_egld":0,
   "coinbase_routing_funder":None,"coinbase_routing_funder_label":"n/a - no inbound this week",
   "weeks_at_zero":2,"weeks_at_zero_in_last_four":3,
   "bid_to_distribution_ratio_pct":0.0,
   "dex_turnover_ratio_pct":bid["turnover"],
   "previous_dex_turnover_ratio_pct":bid["prev_turnover"],
   "withdrawal_breadth":{"distinct_recipients_raw":br["raw_n"],"total_egld_raw":br["raw_egld"],
     "distinct_recipients_ex_pipeline":br["ex_n"],"total_egld_ex_pipeline":br["ex_egld"],
     "pipeline_share_pct":br["pipeline_share"]},
   "withdrawal_breadth_top":br["top"]},
 "analysis":(
  f"The week's whale story is a distribution pipeline restarting into a rally, with the exchange-balance arithmetic almost entirely uninformative about it.\n\n"
  f"THE OTC HUB. UPbit sent {f(otc['upbit_feed'])} EGLD to its OTC desk in three tranches (100,000 / 70,000 / 31,000 plus smaller), against 14,000 in the whole of last week. "
  f"Gross desk throughput was {f(otc['gross_out'])} out and {f(otc['gross_in'])} in; {otc['circ_pct']:.0f}% of it round-trips to the venue that supplied it, leaving {f(otc['net_one_way'])} of genuine one-way movement. "
  f"Two-hop resolution of the outbound leg puts the destinations at Bybit +{f(otc['net_by_venue'].get('Bybit',0))} net, Binance.com +{f(otc['net_by_venue'].get('Binance.com',0))}, Gate.io +{f(otc['net_by_venue'].get('Gate.io',0))}, with UPbit the sole net source at {f(otc['net_by_venue'].get('UPbit',0))}. "
  f"That terminal pattern is the run #17 distinction: this is supply arriving at order books, not supply dispersing to holders. And unlike run #17, the desks did not drain doing it - inventory ROSE +{f(otc['desk_delta'])} to {f(otc['desk_bal'])}, the highest combined desk balance recorded, so there is more loaded than was delivered.\n\n"
  f"EXCHANGE BALANCES. The headline is {ex['net']:+,.0f} EGLD, which reads as an outflow and is not one. UPbit's {next((w['change_egld'] for w in ex['per_wallet'] if 'UPbit' in w['exchange']),0):+,.0f} is the desk-loading leg; ex-UPbit the complex is within a couple of thousand EGLD of flat. "
  f"Binance's entity net of {next((e['net_flow_egld'] for e in ex['entity'] if e['entity']=='Binance'),0):+,.0f} contains a 300,000 custody-to-hot transfer that cancels inside the entity. Bybit's +{f(next((e['net_flow_egld'] for e in ex['entity'] if e['entity']=='Bybit'),0))} is hub output landing. "
  f"Applying the run #15 decomposition rule, no entity's move this week carries an independent customer-flow signal.\n\n"
  f"THE CUSTODY WATCH RESOLVED BEARISH, AGAIN. Binance Staking custody fell {f(cust['delta'])} to {f(cust['balance'])} in one standard transfer to the Binance.com hot wallet. The watch has carried a pre-registered reading since run #9: a move into the protocol staked module is constructive delegation, a drawdown back to hot is distribution. This is the second time the drawdown branch has fired (run #15 was the first, at -158,853). The binance_staking delegation PROVIDER moved only +2,422, so the EGLD did not go to staking.\n\n"
  f"TIERS. On the {O['tiers_basis']}-address common basis, mega whales fell {O['tiers']['mega']['net_change_egld']:+,.0f} ({O['tiers']['mega']['net_change_pct']:+.2f}%) and large whales rose {O['tiers']['large']['net_change_egld']:+,.0f} ({O['tiers']['large']['net_change_pct']:+.2f}%). Both figures are one transfer: the Binance custody (mega) sending 300,000 to the Binance hot wallet (large), plus UPbit's {f(abs(next((w['change_egld'] for w in ex['per_wallet'] if 'UPbit' in w['exchange']),0)))} desk load. Netting those out, the tier structure did not move, and the mid tier's {O['tiers']['mid']['net_change_egld']:+,.0f} ({O['tiers']['mid']['net_change_pct']:+.2f}%) is the only reading with any independent content - marginal accumulation. Note the tiers are computed on addresses present in BOTH snapshots, per the run #18 rule; the raw top-100 comparison would have shown a phantom +264K mid-tier gain purely because last week's snapshot stored 60 accounts and this week's holds 100.\n\n"
  f"DEMAND. Two instruments, and they disagree. Withdrawal breadth ex-pipeline was {br['ex_n']} recipients taking {f(br['ex_egld'])} EGLD, with the pipeline share of exchange outflows at {br['pipeline_share']:.1f}% - up from 46.7% and the highest since run #17, i.e. the withdrawal channel is dominated by the hub again. The identifiable bid read ZERO for a second straight week and in three of the last four: the Mega Whale absorber recorded no transactions at all and holds {f(bid['mega_bal'])} unchanged to four decimals. "
  f"Against that, DEX turnover tripled to {bid['turnover']:.2f}%. The honest reading is that the absorber is one wallet and has stopped being a useful proxy for aggregate demand, while turnover measures the whole venue and is price-independent. On this week's evidence, demand returned to the DEX order book and did not return to the one wallet the model has been watching for it.\n\n"
  f"CAVEAT: one Binance hot-wallet breadth scan terminated on the page cap at 400 transactions covering only 2.4 days, so the raw withdrawal-breadth figure of {f(br['raw_egld'])} EGLD is a LOWER bound."),
}

json.dump(R,open("/tmp/run22w/part1.json","w"),indent=1,default=str)
print("part1 ok:",list(R.keys()))
