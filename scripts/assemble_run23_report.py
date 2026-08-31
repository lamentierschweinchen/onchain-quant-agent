#!/usr/bin/env python3
"""Run #23 stage 2: build part1 of reports/2026-08-31.json"""
import json, os
from datetime import datetime, timezone

REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-08-31"
O=json.load(open("/tmp/run23w/derived.json"))
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
F=json.load(open(f"{REPO}/data/collected/followup_{RD}.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
status=json.load(open("/tmp/run23w/status.json"))
beh=json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
r22=json.load(open(f"{REPO}/reports/2026-08-24.json"))

M=O["macro"]; otc=O["otc"]; wave=otc["wave"]
ex=O["exch"]; cust=O["custody"]; bid=O["bid"]; br=O["breadth"]
sk=O["staking"]; tk=O["tokens"]; xx=O["xexchange"]; df=O["defi"]; z=O["z"]
ub=O["unbond"]; absb=O["absorbers"]
econ=D["economics"]; st=D["stats"]; pecon=prev["economics"]; pact=prev["activity"]
price=M["price"]; pc=M["price_chg"]
cvc=beh["aggregates"]["compound_vs_claim_at_function_level"]
def f(x,d=0):
    try: return f"{x:,.{d}f}"
    except: return str(x)

# ---- boundary-crossing-netted tiers (run #14 guard) ------------------------
cross=O["tier_crossers"]
cross_by={c["address"]:c for c in cross}
cur_top={x["address"]:int(x["balance"])/1e18 for x in D["top_accounts"]}
prev_top={x["address"]:x["balance_egld"] for x in prev["top_accounts"]}
def tier(v):
    if v>1_000_000: return "mega"
    if v>=100_000: return "large"
    if v>=10_000: return "mid"
SYS="erd1qqqqqqqqqqqqq"
cm={}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"): cm[a]=m.get("category","unknown")
common=[a for a in cur_top if a in prev_top and not a.startswith(SYS) and cm.get(a,"unknown")!="system"]
fixed={"mega":[0.0,0.0],"large":[0.0,0.0],"mid":[0.0,0.0]}
for a in common:
    t=tier(prev_top[a])          # hold each wallet in its PRIOR tier
    if not t: continue
    fixed[t][0]+=prev_top[a]; fixed[t][1]+=cur_top[a]
tiers_fixed={t:{"previous":fixed[t][0],"current":fixed[t][1],
                "net_change_egld":fixed[t][1]-fixed[t][0],
                "net_change_pct":100*(fixed[t][1]-fixed[t][0])/fixed[t][0] if fixed[t][0] else 0}
             for t in fixed}
O["tiers_fixed"]=tiers_fixed
json.dump(O,open("/tmp/run23w/derived.json","w"),indent=1,default=str)

R={}
R["metadata"]={"report_date":RD,"period_start":"2026-08-24","period_end":RD,
  "generated_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
  "egld_price_usd":price,"btc_price_usd":M["btc"],"eth_price_usd":M["eth"],
  "run_number":23,"data_sources_ok":status["ok"]+[
    "followup pass: 3 valid Binance.com hot wallets (main collector's hardcoded address failed bech32)",
    "followup pass: unbond wallet info/delegation/outbound (429 recovery)",
    "followup pass: wave #3 extended window netting Aug 17-31",
    "historical provider snapshots re-read for the deregistration signature (runs #10-#22)"],
  "data_sources_failed":status["failed"]+[
    "collect_run23.py BINANCE_HOT constant: invalid bech32 -> HTTP 400 (repaired in followup)",
    "/accounts/{unbond}/delegation: HTTP 429 on the main pass (repaired in followup)",
    "wave-window desk pagination: zero txs on the main pass (repaired in followup)",
    "/tokens/WTAO-3ec9c0: HTTP 404 (accumulator fallback unavailable; not needed, SWTAO priced)"]}

hot_feeders=[r for r in cust["hot_big_outbound"] if r["hop2_to_desk"]>0 or r["reaches_desk_directly"]]

R["executive_summary"]=[
 {"category":"network","severity":"high","finding":
  f"EGLD ROSE {pc:+.2f}% TO ${price:.2f} WHILE BOTH MAJORS FELL - THE FIRST EGLD-SPECIFIC DECOUPLING TO THE UPSIDE SINCE RUN #16. BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%. Last week's +30.43% was a beta move that landed between the majors; this one is not, and the run #16 rule applies - when EGLD moves against a flat-or-falling tape the move has an EGLD-specific component. z={z['price']['z']:+.2f}sigma, with the standing caveat that three consecutive up-weeks have pulled the baseline up and the z understates the break. The chain-side instruments did not corroborate: staked EGLD moved {M['staked_chg']:+,.0f} (flat), the staked ratio FELL {100*(M['sr']-M['sr_prev']):+.3f}pp, and DEX volume in EGLD terms fell {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}%."},
 {"category":"whale","severity":"critical","finding":
  f"THE LARGEST STAGED SUPPLY OVERHANG IN TRACKING - THE DESKS DELIVERED {f(otc['net_one_way'])} EGLD ONE-WAY AND STILL ENDED THE WEEK WITH A RECORD {f(otc['desk_bal'])} LOADED. UPbit fed {f(otc['upbit_feed'])} EGLD ({100*(otc['upbit_feed']-otc['prev_upbit_feed'])/otc['prev_upbit_feed']:+.0f}% on last week's 297,000), gross throughput {f(otc['gross_out'])} out against {f(otc['gross_in'])} in, {otc['circ_pct']:.0f}% circular. Desk inventory rose +{f(otc['desk_delta'])} to {f(otc['desk_bal'])} - 2.4x the previous record set last week. Two-hop destinations: Binance.com +{f(otc['net_by_venue'].get('Binance.com',0))}, Bybit +{f(otc['net_by_venue'].get('Bybit',0))}, Gate.io +{f(otc['net_by_venue'].get('Gate.io',0))}, with UPbit the sole net source at {f(otc['net_by_venue'].get('UPbit',0))}. Run #22's wave-#3 escalation test fires at 3x its threshold."},
 {"category":"whale","severity":"critical","finding":
  f"BINANCE IS A DESK FEEDER - THE CUSTODY WATCH AND THE PIPELINE WATCH ARE ONE INSTRUMENT. Run #22 asked whether the 300,000 custody drawdown reaches the desks; it does. The staking custody sent {f(cust['custody_out_this_window'])} to the Binance.com hot wallet this week, and that wallet forwarded {f(cust['hot_to_desk_total'])} EGLD into the OTC desks - 73,421 through the feeder identified in run #19, 30,554 through the run #20 feeder, and 21,297 direct - while returning {f(cust['hot_to_custody_egld'])} to custody. Custody is now {f(cust['balance'])} ({f(cust['delta'])} WoW, a second consecutive drawdown; -497K over two weeks). The pre-registered branch tested the hot wallet's BALANCE, which ROSE {f((cust['hot_balance'] or 0)-(cust['hot_previous'] or 0))} because custody refilled it faster than it spent - a balance threshold cannot see a flow that is funded faster than it is spent, and the claim resolves on the flow trace instead."},
 {"category":"staking","severity":"critical","finding":
  f"RUN #22's 'FIRST OPERATOR DEREGISTRATION IN TRACKING' IS WITHDRAWN - THERE WERE TWO BEFORE IT, AND THE BIGGER ONE WAS MISSED BY TEN RUNS. Applying run #22's own detection signature (locked == 0 with numNodes > 0) to the stored snapshots shows ledgerbyfigment went from 170,808 EGLD to zero between the 2026-06-08 and 2026-06-15 snapshots - inside the run #13 window - carrying 7 nodes and 3,961 delegators, and stakedinc has been zero-locked with 10 nodes and ~639 users for the ENTIRE stored history. Neither was ever reported. p2p_org_ was the third, not the first, and it COMPLETED this week: its owner called removeNodes eleven times plus unBondNodes, taking numNodes 50 -> 0. The signature also needs widening - p2p_org_ no longer matches it, because a fully exited operator has no nodes left."},
 {"category":"staking","severity":"high","finding":
  f"PARTICIPATION INERTIA IS NOW MEASURED IN MONTHS, AND CAPITAL AND PEOPLE MOVE AT COMPLETELY DIFFERENT SPEEDS. ledgerbyfigment has paid 0% APR for ELEVEN WEEKS and lost 78 of 3,961 delegators (-2.0%); stakedinc has paid nothing for the whole stored history and lost 2 of 639; p2p_org_'s 1,244 stranded delegators produced exactly {O['p2p']['function_counts'].get('unDelegate',0)} unDelegate calls this week, against {O['p2p']['function_counts'].get('reDelegateRewards',0)} reDelegateRewards and {O['p2p']['function_counts'].get('claimRewards',0)} claimRewards on a contract that generates nothing. Against that, the two 100%-fee providers' BOOKS have halved - egldstakingprovider 94,349 -> {f(next(m['locked'] for m in sk['moves'] if m['identity']=='egldstakingprovider'))} in two weeks (-34.8%, -51.8% over three), procryptostaking 156,917 -> {f(next(m['locked'] for m in sk['moves'] if m['identity']=='procryptostaking'))} (-20.5%) - with users down only 6.1% and 1.3%. The delegation market has a price mechanism for large holders and none for retail."},
 {"category":"whale","severity":"high","finding":
  f"THE IDENTIFIABLE-BID REPAIR FAILED, AND THE FAILURE IS THE ANSWER. Run #22 recommended discovering absorber wallets dynamically from the desks' outbound terminals rather than watching one wallet. All {absb['scanned']} terminals were scanned: every one is a zero-balance pass-through router, and of {f(absb['total_received'])} EGLD received they retained {f(absb['total_retained'])} ({100*absb['total_retained']/absb['total_received']:.1f}%). There are no absorbers on the outbound side of this pipeline to discover - the desks deliver exclusively to venues through routers. The Mega Whale proxy read exactly zero for a third straight week (balance unchanged to four decimals, zero transactions). The instrument is retired: demand is carried by DEX turnover and ex-pipeline withdrawal breadth from here."},
 {"category":"defi","severity":"medium","finding":
  f"DEX TURNOVER HELD THE REGIME THRESHOLD ON THE USD RATIO AND FAILED IT IN EGLD TERMS - THE CONFOUND RUN #22 ASKED TO SEPARATE. Turnover {bid['turnover']:.2f}% against last week's {bid['prev_turnover']:.2f}%, comfortably above the ~5% branch, so the pre-committed test fires on the regime-change side. But volume in EGLD terms fell from {f(bid['prev_dexvol_egld'])} to {f(bid['dexvol_egld'])} EGLD/day ({100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}%) and pool depth in EGLD terms fell {100*(bid['pooltvl_egld']-bid['prev_pooltvl_egld'])/bid['prev_pooltvl_egld']:+.1f}% - the USD ratio held because both sides scaled with a +6.4% price, not because more EGLD changed hands. WEGLD/USDC is {bid['wegld_usdc_share']:.1f}% of all volume; ex that one pair the venue traded ${f(bid['ex_wegld_usdc_vol'])} in 24h, about {f(bid['ex_wegld_usdc_vol_egld'])} EGLD."},
 {"category":"staking","severity":"medium","finding":
  f"THE 229,865 EGLD UNBOND DID NOT MOVE FOR A SECOND FULL WEEK AND IS RETIRED AS A LIVE FLOW. Balance unchanged at {f(ub['balance'],2)} EGLD, {f(ub['pending_total'])} still sitting unbonded-and-unclaimed inside the delegation contracts, zero outbound transactions, zero function calls. That is the no-action branch run #22 added after the test failed to resolve for want of one - it fires, and the overhang stops being tracked as forward supply. Meanwhile the WEEKLY unbonding queue more than doubled: {f(sk['undelegated_week'])} EGLD unDelegated by {sk['undelegate_callers']} distinct wallets across all {sk['providers_scanned']} provider contracts (run #22 measured 70,498 across ten), with {f(sk['pool_total'])} measured pending. The staked-minus-delegated residual of {f(sk['residual'])} is again fully absorbed, so no direct-node figure is published."},
]

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
  "btc_correlation_note":f"BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%, EGLD {pc:+.2f}% - EGLD rose while BOTH majors fell. That is the run #16 decoupling signature and the opposite of last week, when EGLD's +30.43% landed between BTC +23.78% and ETH +30.67% and carried no EGLD-specific component."},
 "analysis":(
  f"EGLD closed at ${price:.2f}, {pc:+.2f}%, and did it against a falling tape - BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%. "
  f"By the run #16 rule that is an EGLD-specific move rather than beta, and it is the second week running that the price has behaved differently from the chain underneath it.\n\n"
  f"Nothing on-chain corroborates a demand story. Total staked moved {M['staked_chg']:+,.0f} EGLD to {f(econ['staked'])} - flat to three significant figures - and because supply grew {f(econ['totalSupply']-pecon['total_supply'])} EGLD of emission, the staked RATIO actually FELL {100*(M['sr']-M['sr_prev']):+.3f}pp to {100*M['sr']:.2f}%. "
  f"{f(st['transactions']-pact['total_transactions'])} transactions settled over {st['epoch']-pact['epoch']} epochs ({f(int((st['transactions']-pact['total_transactions'])/7))}/day) and {f(st['accounts']-pact['total_accounts'])} accounts were created, both unremarkable. "
  f"DEX volume rose {100*(bid['dexvol']-bid['prev_dexvol'])/bid['prev_dexvol']:+.1f}% in dollars and FELL {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}% in EGLD. Delegation TVL fell {f(sk['delta_locked'])}. The delegator base fell {sk['users_delta']:+,}. "
  f"Network APR {100*(econ['apr']-pecon['staking_apr']):+.3f}pp to {100*econ['apr']:.2f}%.\n\n"
  f"So the honest framing is a price that moved on its own while every participation instrument sat still - and it moved in the same week the OTC pipeline delivered {f(otc['net_one_way'])} EGLD one-way to exchange order books and reloaded to a record {f(otc['desk_bal'])}. "
  f"A rising price into that much staged supply is the week's central tension, and it is not resolved by anything the model can currently see on the bid side."),
}

def entity_interp(e):
    n=e["entity"]; v=e["net_flow_egld"]
    if n=="Binance":
        return (f"{v:+,.0f} across {e['wallets_count']} wallets, and NOT a customer-flow signal. Internally: staking custody -> hot {f(cust['custody_out_this_window'])}, hot -> custody {f(cust['hot_to_custody_egld'])}. "
                f"Externally the informative number is that the hot wallet pushed {f(cust['hot_to_desk_total'])} EGLD into the OTC desks through two previously identified feeders and one direct transfer - the first time Binance has been observed feeding the pipeline, and the answer to a question open since run #22.")
    if n=="UPbit":
        return (f"{v:+,.0f} ({e['pct']:+.1f}%) is the OTC LOADING LEG, not customer withdrawal (run #16 rule). UPbit sent {f(otc['upbit_feed'])} EGLD to its own desk in traceable standard transfers - more than its balance fell, because inventory returned from the desks in the same window. It is the sole net SOURCE of the entire pipeline at {f(otc['net_by_venue'].get('UPbit',0))}.")
    if n=="Bybit":
        return (f"{v:+,.0f}. Bybit is the second-largest net RECEIVER from the hub (+{f(otc['net_by_venue'].get('Bybit',0))} two-hop-resolved) but its balance rose only {f(v)}, so most of what arrived has already been absorbed or moved on. Note Bybit also FED the desks {f(otc['in_by_venue'].get('Bybit',0))} - it is on both sides, which is what the circularity measure exists to catch.")
    if n=="Coinbase":
        return (f"{v:+,.0f} ({e['pct']:+.1f}%), the largest proportional fall of the week. Coinbase Custody 2 sent 40,000 and Coinbase (secondary) 18,108 to Unknown Whale B, which now holds {f(next((w['balance_current_egld'] for w in O['wallet_changes'] if 'Whale B' in w['label']),0))} - per the run #17 migration rule the receiver holds it, so this is withdrawal to a holder, not distribution.")
    if n=="Gate.io":
        return (f"{v:+,.0f} ({e['pct']:+.1f}%) against a hub inflow of +{f(otc['net_by_venue'].get('Gate.io',0))} - Gate.io absorbed desk output and still shed balance, so customers withdrew more than the pipeline delivered.")
    if n=="Bitget":
        return f"{v:+,.0f} ({e['pct']:+.1f}%), the largest proportional BUILD. Bitget appears as a hub destination for the first time (+{f(otc['net_by_venue'].get('Bitget',0))} two-hop-resolved) - a fifth venue on the delivery side."
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
     f"Net exchange flow {ex['net']:+,.0f} EGLD ({100*ex['net']/ex['total_prev']:+.2f}%), and per the run #15 decomposition rule it must be read entity by entity because two entities exceed the net. "
     f"UPbit alone is {next((w['change_egld'] for w in ex['per_wallet'] if 'UPbit' in w['exchange']),0):+,.0f} and that is the desk-loading leg - it sent {f(otc['upbit_feed'])} EGLD to its own OTC desk in standard transfers. "
     f"Binance's {next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Binance'),0):+,.0f} nets a {f(cust['custody_out_this_window'])} custody-to-hot transfer against a {f(cust['hot_to_custody_egld'])} return. "
     f"Ex those two the complex was {ex['net']-next((w['change_egld'] for w in ex['per_wallet'] if 'UPbit' in w['exchange']),0)-next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Binance'),0):+,.0f} - a mild INFLOW into a rising price, led by Bybit and Bitget, both of which are hub destinations. "
     f"Per the run #14 joint-read rule the balance deltas are the weaker channel this week: the pipeline moved {f(otc['gross_out'])} gross and {f(otc['net_one_way'])} one-way, an order of magnitude more than the net balance change. "
     f"{len(ex['noprior'])} addresses without a prior-week balance were excluded from the delta per the run #18 rule."),
   "by_exchange":[{"exchange":w["exchange"],"change_egld":w["change_egld"],"pct":w["pct"]}
                  for w in ex["per_wallet"]],
   "entity_netting":[{"entity":e2["entity"],"wallets_count":e2["wallets_count"],
                      "net_flow_egld":e2["net_flow_egld"],"interpretation":entity_interp(e2)}
                     for e2 in ex["entity"]]},
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
   "gross_series_egld_7d":{**r22["whale_intelligence"]["otc_pipeline"]["gross_series_egld_7d"],
                           "run23":otc["gross_out"]},
   "net_one_way_series_egld_7d":{**r22["whale_intelligence"]["otc_pipeline"]["net_one_way_series_egld_7d"],
                                 "run23":otc["net_one_way"]},
   "circularity_series_pct":{**r22["whale_intelligence"]["otc_pipeline"]["circularity_series_pct"],
                             "run23":round(otc["circ_pct"],1)},
   "peak_window_renetted":r22["whale_intelligence"]["otc_pipeline"]["peak_window_renetted"],
   "backfilled_windows":r22["whale_intelligence"]["otc_pipeline"].get("backfilled_windows",[]),
   "wave_window_netting":{
     "window":wave["window"]+" (WAVE #3 feed-to-drain)",
     "gross_outbound_egld":wave["gross_out"],"gross_inbound_egld":wave["gross_in"],
     "circular_egld":wave["circular"],"circular_share_pct":wave["circ_pct"],
     "net_one_way_egld":wave["net_one_way"],"sum_of_weekly_nets_egld":wave["sum_weekly"],
     "weekly_frame_overstatement_egld":wave["overstate_egld"],
     "weekly_frame_overstatement_pct":wave["overstate_pct"],
     "net_by_venue":wave["net_by_venue"],
     "outbound_by_venue":wave["out_by_venue"],"inbound_by_venue":wave["in_by_venue"],
     "note":(f"Wave #3 spans Aug 17-31 - the feed restarted on Aug 17-24 (297,000) and escalated on Aug 24-31 ({f(otc['upbit_feed'])}). "
             f"Netted feed-to-drain over the whole wave it delivered {f(wave['net_one_way'])} EGLD one-way against {f(wave['sum_weekly'])} from summing the two weekly nets - a {wave['overstate_pct']:.1f}% overstatement. "
             f"Run #22's narrowed rule predicted exactly this: the wave STRADDLES the week boundary (UPbit feeds in one week, inventory returns in the next), and the diagnostic tell fired in advance - this week's circularity of {otc['circ_pct']:.0f}% sits just below the 63-80% band. "
             f"The wave-window figure is the one to use for distribution; the weekly numbers are upper bounds here.")},
   "series_note":(
     f"gross_series is pipeline ACTIVITY, net_one_way is the distribution measure; this week they differ {otc['gross_out']/otc['net_one_way']:.1f}x. "
     f"The number that matters most is neither: desk inventory ENDED at {f(otc['desk_bal'])} after delivering {f(otc['net_one_way'])} one-way, which means the pipeline is more loaded now than at any point since tracking began and the drain leg of wave #3 is still ahead. "
     f"Bitget appears as a hub destination for the first time, taking the delivery-side venue count to five.")},
 "demand_instruments":{
   "identifiable_bid_absorbed_egld_7d":bid["absorbed"],
   "mega_whale_balance_egld":bid["mega_bal"],"mega_whale_change_egld":bid["mega_delta"],
   "coinbase_routing_balance_egld":bid["cbr_bal"],"coinbase_routing_inflow_egld":0,
   "coinbase_routing_funder":None,"coinbase_routing_funder_label":"n/a - no inbound this week",
   "weeks_at_zero":3,"weeks_at_zero_in_last_four":4,
   "bid_to_distribution_ratio_pct":0.0,
   "dex_turnover_ratio_pct":bid["turnover"],
   "previous_dex_turnover_ratio_pct":bid["prev_turnover"],
   "dex_volume_egld_24h":bid["dexvol_egld"],
   "previous_dex_volume_egld_24h":bid["prev_dexvol_egld"],
   "pool_tvl_egld":bid["pooltvl_egld"],"previous_pool_tvl_egld":bid["prev_pooltvl_egld"],
   "wegld_usdc_volume_usd":bid["wegld_usdc_vol"],
   "wegld_usdc_share_of_volume_pct":bid["wegld_usdc_share"],
   "ex_wegld_usdc_volume_usd":bid["ex_wegld_usdc_vol"],
   "ex_wegld_usdc_volume_egld":bid["ex_wegld_usdc_vol_egld"],
   "absorber_scan":{"terminals_scanned":absb["scanned"],
     "terminals_retaining_over_half":len(absb["retaining"]),
     "total_received_from_desks_egld":absb["total_received"],
     "total_retained_egld":absb["total_retained"],
     "retained_share_pct":100*absb["total_retained"]/absb["total_received"] if absb["total_received"] else 0,
     "verdict":"No absorbers exist on the outbound side of this pipeline. All 14 terminals are zero-balance pass-through routers. The single-wallet identifiable-bid instrument is RETIRED rather than repaired."},
   "withdrawal_breadth":{"distinct_recipients_raw":br["raw_n"],"total_egld_raw":br["raw_egld"],
     "distinct_recipients_ex_pipeline":br["ex_n"],"total_egld_ex_pipeline":br["ex_egld"],
     "pipeline_share_pct":br["pipeline_share"]},
   "withdrawal_breadth_top":br["top"]},
 "analysis":(
  f"THE PIPELINE. UPbit fed {f(otc['upbit_feed'])} EGLD into the OTC desks this week against 297,000 last week and 14,000 the week before - three data points that make the July-August pattern a single escalating programme rather than episodic. "
  f"The desks moved {f(otc['gross_out'])} out and took {f(otc['gross_in'])} in; {otc['circ_pct']:.0f}% round-trips to the venue that supplied it, leaving {f(otc['net_one_way'])} of genuine one-way movement. "
  f"Two-hop resolution puts the destinations at Binance.com +{f(otc['net_by_venue'].get('Binance.com',0))}, Bybit +{f(otc['net_by_venue'].get('Bybit',0))}, Gate.io +{f(otc['net_by_venue'].get('Gate.io',0))} and, for the first time, Bitget +{f(otc['net_by_venue'].get('Bitget',0))}. "
  f"Every one of those is an exchange deposit address, so this is the run #17 signature: supply arriving at order books rather than dispersing to holders.\n\n"
  f"THE PART THAT MATTERS MORE IS WHAT DID NOT GO OUT. Desk inventory rose +{f(otc['desk_delta'])} to {f(otc['desk_bal'])} - 2.4x the record set last week - AFTER delivering {f(otc['net_one_way'])} one-way. "
  f"For comparison, the entire run #17 peak wave delivered 409,680 one-way from a starting inventory of 335,430. The desks now hold {f(otc['desk_bal'])} with a feed still running. This is the largest staged, undelivered supply position the model has recorded.\n\n"
  f"BINANCE JOINED THE FEED SIDE. Run #22 flagged that the custody drawdown and the OTC restart happened in the same week without a demonstrated link. There is one. The staking custody sent {f(cust['custody_out_this_window'])} to the Binance.com hot wallet; the hot wallet forwarded {f(cust['hot_to_desk_total'])} EGLD to the desks - {f(hot_feeders[0]['amount']) if hot_feeders else 'n/a'} through the feeder identified in run #19, {f(hot_feeders[1]['amount']) if len(hot_feeders)>1 else 'n/a'} through the run #20 feeder, and 21,297 straight to a desk - and returned {f(cust['hot_to_custody_egld'])} to custody. "
  f"Custody has now fallen {f(cust['delta'])} this week on top of last week's -300,000. Note what this does to the pre-registered branch: it was written on the hot wallet's BALANCE falling more than 150,000, and the balance instead ROSE {f((cust['hot_balance'] or 0)-(cust['hot_previous'] or 0))} because custody refilled it faster than it distributed. A balance test cannot see a flow whose funding outruns its spending; the flow trace can, and it says the two channels are one programme.\n\n"
  f"EXCHANGE BALANCES. Headline {ex['net']:+,.0f} EGLD. UPbit's {next((w['change_egld'] for w in ex['per_wallet'] if 'UPbit' in w['exchange']),0):+,.0f} is desk loading and Binance's {next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Binance'),0):+,.0f} is internal plumbing; ex those two the complex took a mild INFLOW of {ex['net']-next((w['change_egld'] for w in ex['per_wallet'] if 'UPbit' in w['exchange']),0)-next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Binance'),0):+,.0f} into a rising price, led by Bybit +{f(next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Bybit'),0))} and Bitget +{f(next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Bitget'),0))} - both hub destinations, so even that is pipeline output rather than independent customer behaviour. Coinbase's {next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Coinbase'),0):+,.0f} resolves to a migration: 58,108 across two transfers to Unknown Whale B, which still holds it.\n\n"
  f"TIERS - READ THE NETTED VERSION. Raw, the {O['tiers_basis']}-address common basis shows mega {O['tiers']['mega']['net_change_egld']:+,.0f} ({O['tiers']['mega']['net_change_pct']:+.1f}%) and large {O['tiers']['large']['net_change_egld']:+,.0f} ({O['tiers']['large']['net_change_pct']:+.1f}%), which is almost entirely a reclassification artifact: FOUR wallets crossed a threshold this week - UPbit fell out of the mega tier at 950,444, and both OTC desks plus Unknown Whale B crossed up into the large tier. "
  f"Holding every wallet in its PRIOR tier (the run #14 boundary guard) gives mega {tiers_fixed['mega']['net_change_egld']:+,.0f}, large {tiers_fixed['large']['net_change_egld']:+,.0f}, mid {tiers_fixed['mid']['net_change_egld']:+,.0f}. "
  f"Decomposed: the mega figure is Binance custody (-196,758) plus UPbit's desk load (-164,918) and NOTHING else - two wallets, both pipeline mechanics. The large tier is the Binance.com hot wallet (+158,397) plus Bybit (+24,308), i.e. the receiving end of the same two flows. "
  f"The mid tier's {tiers_fixed['mid']['net_change_egld']:+,.0f} is three quarters the two OTC desks filling up (+156,356) plus Unknown Whale B (+36,505); ex those three it moved +10,844. "
  f"So on a netted basis NO tier accumulated independently this week - every figure above 10,000 EGLD belongs to the distribution pipeline or to a wallet migration.\n\n"
  f"DEMAND. The identifiable-bid instrument has been repaired-or-retired and the answer is retired. Scanning all {absb['scanned']} desk outbound terminals for wallets that KEEP what they receive found none: {f(absb['total_received'])} EGLD passed through them and {f(absb['total_retained'])} ({100*absb['total_retained']/absb['total_received']:.1f}%) stayed. Every terminal is a zero-balance router with a high nonce. "
  f"The Mega Whale proxy read zero for a third consecutive week and in four of the last five. What is left is turnover - which held its ratio but fell in EGLD terms - and ex-pipeline withdrawal breadth, which improved markedly: {br['ex_n']} distinct recipients took {f(br['ex_egld'])} EGLD off exchanges outside the pipeline, against 21 recipients and 133,521 last week, with the pipeline share falling from 88.3% to {br['pipeline_share']:.1f}%. "
  f"That is the one genuinely constructive reading available: more distinct wallets took more EGLD off venues than in any week since the instrument was built. The page-cap budget raised for hot wallets this run (run #22 rec #10) means the raw figure of {f(br['raw_egld'])} EGLD is a full 7-day scan with NO page-cap terminations - the first week that is true."),
}
json.dump(R,open("/tmp/run23w/part1.json","w"),indent=1,default=str)
print("part1 ok:",list(R.keys()))
print("tiers_fixed:",{k:round(v['net_change_egld']) for k,v in tiers_fixed.items()})
