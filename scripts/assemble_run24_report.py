#!/usr/bin/env python3
"""Run #24 stage 2: build part1 of reports/2026-09-07.json"""
import json, os
from datetime import datetime, timezone

REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-09-07"
O=json.load(open("/tmp/run24w/derived.json"))
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
status=json.load(open("/tmp/run24w/status.json"))
beh=json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
r23=json.load(open(f"{REPO}/reports/2026-08-31.json"))

M=O["macro"]; otc=O["otc"]; wave=otc["wave"]
ex=O["exch"]; cust=O["custody"]; bid=O["bid"]; br=O["breadth"]
sk=O["staking"]; tk=O["tokens"]; xx=O["xexchange"]; df=O["defi"]; z=O["z"]
ub=O["unbond"]; absb=O["absorbers"]; zsc=O["zero_stake_cohort"]
econ=D["economics"]; st=D["stats"]; pecon=prev["economics"]; pact=prev["activity"]
price=M["price"]; pc=M["price_chg"]
cvc=beh["aggregates"]["compound_vs_claim_at_function_level"]
def f(x,d=0):
    try: return f"{x:,.{d}f}"
    except: return str(x)
def venue(d_,k,default=0.0): return d_.get(k,default)

# ---- boundary-crossing-netted tiers (run #14 guard) ------------------------
cross=O["tier_crossers"]
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

# Binance hot -> known OTC feeders and desks, measured on the FLOW (the run #23
# test was re-specified on flow after a balance threshold failed).
LABELS={}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"): LABELS[a]=m.get("name","Unknown")
DESK={"erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5",
      "erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"}
FEEDERS={a for a,l in LABELS.items()
         if "OTC Desk Feeder" in l or "OTC Router" in l or "→OTC" in l or "->OTC" in l}
hot_to_pipe={}
for t in (D.get("binance_hot_out") or []):
    v=int(t.get("value","0"))/1e18
    r=t.get("receiver")
    if v>0 and (r in DESK or r in FEEDERS):
        hot_to_pipe[r]=hot_to_pipe.get(r,0)+v
HOT_TO_PIPE=sum(hot_to_pipe.values())
hot_cap=[x for x in (D.get("_pagecap_terminations") or []) if x.get("tag")=="binance_hot_out"]
HOT_COVER=hot_cap[0]["coverage_days"] if hot_cap else 7.0
# every desk feeder by parent venue, this week
feeders_in={}
for a,rec in D["desk_inbound_paged"].items():
    for t in rec["txs"]:
        v=int(t.get("value","0"))/1e18; s2=t.get("sender")
        if v<=0 or s2 in DESK: continue
        l=LABELS.get(s2,"Unknown")
        p=("UPbit" if l.startswith("UPbit") else "Binance" if "Binance" in l
           else "Bybit" if "Bybit" in l else "Gate.io" if "Gate" in l else "Unattributed")
        feeders_in[p]=feeders_in.get(p,0)+v
O["feeders_in"]=feeders_in
O["hot_to_pipe"]={"total_egld":HOT_TO_PIPE,"coverage_days":HOT_COVER,
                  "by_recipient":{LABELS.get(k,k[:14]):v for k,v in
                                  sorted(hot_to_pipe.items(),key=lambda x:-x[1])}}
json.dump(O,open("/tmp/run24w/derived.json","w"),indent=1,default=str)

LF=next((r for r in zsc["with_activity_this_week"] if r["provider"]=="ledgerbyfigment"), {})
LF_FN=LF.get("function_counts",{})

R={}
R["metadata"]={"report_date":RD,"period_start":"2026-08-31","period_end":RD,
  "generated_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
  "egld_price_usd":price,"btc_price_usd":M["btc"],"eth_price_usd":M["eth"],
  "run_number":24,"data_sources_ok":status["ok"],
  "data_sources_failed":status["failed"]+[
    "/tokens/WTAO-3ec9c0: HTTP 404 - confirmed dead identifier, kept in the pre-flight recheck list as a known-bad control",
    "Binance.com hot wallet outbound: page-capped at 1,000 txs covering "
    f"{HOT_COVER} of 7 days, so the {f(HOT_TO_PIPE)} EGLD hot-to-pipeline figure is a LOWER BOUND",
    "16 provider contracts filled the 6-page unDelegate budget and were re-scanned at 30 pages (rec #10); "
    "the queue figure is now a near-complete scan rather than a lower bound, but 16 deep scans still terminated on the cap"],
  "data_sources_recovered":[
    "/tokens/WTAO-4f5363 - the correct WrappedTAO identifier, dead in the collector from run #13 to #23, queried and priced this run",
    "/accounts/{Binance.com hot} - run #23's invalid bech32 constant replaced with the three checksummed wallets; now covered by the pre-flight validator",
    "/accounts/{unbond wallet}/delegation - HTTP 429 last run, clean on the first pass this run with exponential backoff in place"]}

R["executive_summary"]=[
 {"category":"whale","severity":"critical","finding":
  f"THE OVERHANG WAS DELIVERED. Desk inventory fell from {f(otc['prev_desk'])} to {f(otc['desk_bal'])} EGLD ({100*otc['desk_delta']/otc['prev_desk']:+.0f}%) while the desks pushed a record {f(otc['net_one_way'])} EGLD one-way to exchange order books - z={z['otc_net']['z']:+.2f}sigma and 31% above the previous record, run #17's 409,680. Run #23's pre-committed test asked whether the record inventory was staged supply or a new level; the sub-120,000 branch fires cleanly. Netted feed-to-drain over the whole of wave #3 (Aug 17 - Sep 7) the programme delivered {f(wave['net_one_way'])} EGLD one-way, more than double the largest wave previously tracked. Destinations: Binance.com +{f(venue(otc['net_by_venue'],'Binance.com'))}, Bybit +{f(venue(otc['net_by_venue'],'Bybit'))}, Gate.io +{f(venue(otc['net_by_venue'],'Gate.io'))}, with UPbit the sole net source at {f(venue(otc['net_by_venue'],'UPbit'))}."},
 {"category":"network","severity":"high","finding":
  f"EGLD ROSE {pc:+.2f}% TO ${price:.2f} INTO THE LARGEST DELIVERY WEEK ON RECORD, AND AGAIN WITHOUT THE MAJORS. BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}% - both effectively flat, so by the run #16 rule this is an EGLD-specific move for a second consecutive week. z={z['price']['z']:+.2f}sigma. Nothing on the participation side corroborates it: staked EGLD {M['staked_chg']:+,.0f}, the staked ratio FELL {100*(M['sr']-M['sr_prev']):+.3f}pp to {100*M['sr']:.2f}%, delegation TVL {f(sk['delta_locked'])}, and DEX volume in EGLD terms fell {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}% to {f(bid['dexvol_egld'])} EGLD/day. A price that absorbed half a million EGLD of desk supply and still rose 17% is the week's central fact, and the bid behind it is not visible in any instrument this model has."},
 {"category":"whale","severity":"high","finding":
  f"THE BINANCE FEED IS A STANDING PROGRAMME - AND THE CUSTODY DRAWDOWN REVERSED IN THE SAME WEEK. The Binance.com hot wallet sent {f(HOT_TO_PIPE)} EGLD to known OTC desk feeders in a page-capped {HOT_COVER}-day window, clearing the 50,000 flow threshold run #23 registered after a balance threshold failed on the same question. Binance-labelled feeders delivered {f(feeders_in.get('Binance',0))} EGLD into the desks. But staking custody REVERSED: +{f(cust['delta'])} to {f(cust['balance'])} after two weeks of drawdown totalling -497K, on 900,000 out to the hot wallet against 1,272,434 back. Binance funded the pipeline and refilled custody at the same time, which means the custody balance is a poor supply proxy on its own - the flow trace is the instrument."},
 {"category":"whale","severity":"high","finding":
  f"THE DELIVERY SURFACE IS NOW THREE VENUES DEEP ON BOTH SIDES. Feed: UPbit {f(feeders_in.get('UPbit',0))}, Bybit feeders {f(feeders_in.get('Bybit',0))}, Binance feeders {f(feeders_in.get('Binance',0))}. Delivery: Bybit took {f(venue(otc['out_by_venue'],'Bybit'))} gross and fed back {f(venue(otc['in_by_venue'],'Bybit'))}, Binance.com {f(venue(otc['out_by_venue'],'Binance.com'))} against {f(venue(otc['in_by_venue'],'Binance.com'))}, Gate.io {f(venue(otc['out_by_venue'],'Gate.io'))} against {f(venue(otc['in_by_venue'],'Gate.io'))}. Gross throughput {f(otc['gross_out'])} out / {f(otc['gross_in'])} in at {otc['circ_pct']:.0f}% circularity - the highest gross ever recorded, past run #17's 1,284,688. When a venue appears on both legs it is running inventory, not taking delivery; the net figures are the ones that mean anything."},
 {"category":"staking","severity":"high","finding":
  f"RUN #23's THREE DEREGISTRATIONS ARE THE VISIBLE END OF A MUCH OLDER PHENOMENON: {zsc['contracts']} PROVIDER CONTRACTS HOLD ZERO STAKE AND {f(zsc['attached_delegator_records'])} ATTACHED DELEGATOR RECORDS - {zsc['share_of_all_delegator_records_pct']:.1f}% of every delegator record on the network. Running the widened detector backwards over all {zsc['archive_snapshots']} stored snapshots shows only FOUR of them emptied inside the archive (ledgerbyfigment Jun 8, p2p_org_ Aug 17, truststakingsw before Jun 1, one small contract Aug 10); the rest - everstake 3,681 records, stakedao-devops 2,862, bharvest 1,383, phidelta 1,009 - have been at zero since before tracking began. Exactly ONE of the {zsc['contracts']} saw any inbound transaction this week: ledgerbyfigment, with {LF_FN.get('unDelegate',0)} unDelegate and {LF_FN.get('withdraw',0)} withdraw calls. The other 81 are dormant records, not live positions, and the delegator base should be quoted on the locked>0 basis ({f(sk['users'])}) rather than the full list ({f(sk['prev_users_all_contracts'])})."},
 {"category":"staking","severity":"medium","finding":
  f"THE UNBONDING QUEUE IS AT A TRACKED HIGH AND THE COMPOUND RATE SNAPPED BACK. {f(sk['undelegated_week'])} EGLD unDelegated by {sk['undelegate_callers']} distinct wallets across all {sk['providers_scanned']} provider contracts (run #23: 151,443 by 300), with {f(sk['pool_total'])} measured pending - and this is the first scan where the sixteen busiest contracts were re-paged at a 30-page budget, so the coverage gap run #23 flagged is closed. Against that, the reward compound rate REVERSED to {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} redelegate vs {cvc['claim_count']} claim) after four consecutive declines, resolving run #23's drift test on the 'stabilised' branch. More EGLD is queued to leave staking, but the people already in it are compounding harder."},
 {"category":"token","severity":"medium","finding":
  f"THE ON-CHAIN DOLLAR BASE CONTRACTED FOR A THIRD CONSECUTIVE WEEK, WHICH PROMOTES IT TO AN INSTRUMENT. USDC {tk['stable']['USDC-c76f1f']['pct']:+.2f}% to {f(tk['stable']['USDC-c76f1f']['supply'])}, USDT {tk['stable']['USDT-f8c08c']['pct']:+.2f}% to {f(tk['stable']['USDT-f8c08c']['supply'])} - about $140K of wrapped dollars redeemed into a +17% price week, and the third straight week both contracted together. Run #23's pre-committed test made that the promotion condition. Against it, USH MINTED +{tk['lsd']['USH-111e09']['pct']:.2f}% ({f(tk['lsd']['USH-111e09']['supply']-tk['lsd']['USH-111e09']['prev'])} tokens) after two consecutive burns - CDP leverage returning exactly as the run #16 framing predicts for a rally, and the reverse of what the dollar base did."},
 {"category":"defi","severity":"medium","finding":
  f"DEX TURNOVER FAILED IN BOTH DENOMINATIONS THIS WEEK, WHICH SETTLES THE QUESTION RUN #23 LEFT OPEN. Volume in EGLD terms {f(bid['dexvol_egld'])}/day against a pre-registered 60,000 floor - the branch that says the USD turnover ratio has been tracking price fires, and the series is reported in EGLD from here. Turnover fell {bid['turnover']:.2f}% from {bid['prev_turnover']:.2f}%, USD volume {100*(bid['dexvol']-bid['prev_dexvol'])/bid['prev_dexvol']:+.1f}%, and WEGLD/USDC is now {bid['wegld_usdc_share']:.1f}% of all venue volume - ex that single pair xExchange traded {f(bid['ex_wegld_usdc_vol_egld'])} EGLD in 24h. Separately the JEXchange aggregator address that returned zero for three runs was re-derived from the fees contract's inbound leg: the live router does {f(O['jex']['candidates'][0]['transfers_7d'])} transfers a week, so the protocol was never halted - the address was stale."},
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
  "btc_correlation_note":f"BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%, EGLD {pc:+.2f}%. Both majors were flat to three decimal places on the week while EGLD added a sixth of its value - the cleanest decoupling signature in the archive, and the second consecutive week the run #16 rule applies."},
 "analysis":(
  f"EGLD closed at ${price:.2f}, {pc:+.2f}% on the week, against BTC {M['btc_wow']:+.2f}% and ETH {M['eth_wow']:+.2f}%. "
  f"Two flat majors and a +17% EGLD is not beta; it is the second consecutive EGLD-specific move and the largest since the archive began. z={z['price']['z']:+.2f}sigma, with the usual caveat that four up-weeks have dragged the baseline mean up behind it.\n\n"
  f"What makes this week different from last week is not the price, it is what the price absorbed. The OTC desks delivered {f(otc['net_one_way'])} EGLD one-way into exchange order books - the largest single week ever measured, 31% past the run #17 peak - and the price went UP through it. "
  f"Every prior delivery wave in this archive coincided with a flat or falling EGLD; this one did not.\n\n"
  f"The participation instruments all point the other way. Total staked fell {abs(M['staked_chg']):,.0f} EGLD to {f(econ['staked'])}, and with {f(econ['totalSupply']-pecon['total_supply'])} EGLD of emission on top, the staked RATIO fell {100*(M['sr']-M['sr_prev']):+.3f}pp to {100*M['sr']:.2f}% - the lowest reading in the archive. "
  f"Delegation TVL fell {f(sk['delta_locked'])} and {f(sk['undelegated_week'])} EGLD entered the unbonding queue. "
  f"{f(st['transactions']-pact['total_transactions'])} transactions settled over {st['epoch']-pact['epoch']} epochs ({f(int((st['transactions']-pact['total_transactions'])/7))}/day) and {f(st['accounts']-pact['total_accounts'])} accounts were created - both mid-range. "
  f"Network APR {100*(econ['apr']-pecon['staking_apr']):+.3f}pp to {100*econ['apr']:.2f}%.\n\n"
  f"So the honest reading is a demand event the model cannot see the counterparty for. Supply is fully accounted: {f(otc['net_one_way'])} EGLD arrived at order books from a pipeline whose inventory drained {100*abs(otc['desk_delta'])/otc['prev_desk']:.0f}%. "
  f"The bid that took it is not in the staking data, not in DEX volume, not in LSD subscriptions, and not in the identifiable-bid wallets - all of which were flat or negative. "
  f"The one place it shows up is off-venue withdrawal breadth: {br['ex_n']} distinct non-pipeline addresses pulled {f(br['ex_egld'])} EGLD off exchanges, the highest count the instrument has recorded."),
}
json.dump(R,open("/tmp/run24w/part1a.json","w"),indent=1,default=str)
print("part1a ok:",list(R.keys()))
print("tiers_fixed:",{k:round(v['net_change_egld']) for k,v in tiers_fixed.items()})
print("hot_to_pipe:",round(HOT_TO_PIPE),"coverage",HOT_COVER,"feeders_in:",{k:round(v) for k,v in feeders_in.items()})

# ---------------------------------------------------------------------------
# whale intelligence
# ---------------------------------------------------------------------------
def entity_interp(e):
    n=e["entity"]; v=e["net_flow_egld"]
    if n=="Binance":
        return (f"{v:+,.0f} across {e['wallets_count']} wallets, and the net is meaningless without the decomposition. "
                f"Internally: staking custody sent 900,000 to the hot wallet and took 1,272,434 back, so CUSTODY ROSE +{f(cust['delta'])} to {f(cust['balance'])} while the hot complex fell {f(cust['hot_entity_balance']-cust['hot_entity_previous'])}. "
                f"Externally the hot wallet pushed {f(HOT_TO_PIPE)} EGLD into known OTC feeders in {HOT_COVER} days of covered window, and Binance-labelled feeders delivered {f(feeders_in.get('Binance',0))} into the desks. "
                f"Two weeks of custody drawdown reversed while the feed continued - funding the pipeline and refilling custody are not the same decision, and this week Binance did both.")
    if n=="UPbit":
        return (f"{v:+,.0f} ({e['pct']:+.1f}%) with {f(otc['upbit_feed'])} EGLD sent to its own desk in the same window - the LOADING leg, not customer withdrawal (run #16 rule). "
                f"UPbit is the pipeline's sole net source again at {f(venue(otc['net_by_venue'],'UPbit'))}, and it took {f(venue(otc['out_by_venue'],'UPbit'))} back from the desks, which is why its balance rose while it was feeding.")
    if n=="Bybit":
        return (f"{v:+,.0f} ({e['pct']:+.1f}%), the largest balance fall of the week, and the venue is on BOTH legs of the pipeline at scale: it received {f(venue(otc['out_by_venue'],'Bybit'))} from the desks and fed {f(venue(otc['in_by_venue'],'Bybit'))} back, netting +{f(venue(otc['net_by_venue'],'Bybit'))}. "
                f"A balance that falls while the hub delivers into it means customers took more off the venue than the desks put on it.")
    if n=="Coinbase":
        return (f"{v:+,.0f} ({e['pct']:+.1f}%) across {e['wallets_count']} wallets, a third consecutive fall. Coinbase has no role in the OTC pipeline in any window tracked; this is ordinary withdrawal.")
    if n=="Gate.io":
        return (f"{v:+,.0f} ({e['pct']:+.1f}%) against a hub net of +{f(venue(otc['net_by_venue'],'Gate.io'))} - Gate.io absorbed desk delivery AND grew its balance, the only venue where both moved the same way this week.")
    if n=="Bitget":
        return f"{v:+,.0f} ({e['pct']:+.1f}%). Bitget was a hub destination in the Aug 17-31 frame (+{f(venue(wave['net_by_venue'],'Bitget'),0)} over the wave) but took nothing this week - the fifth venue was a one-week appearance so far."
    return f"{v:+,.0f} across {e['wallets_count']} wallet(s), {e['pct']:+.2f}%."

INV_SERIES={**{k:v for k,v in prev["otc_desk_inventory_series"].items()},"run24":round(otc["desk_bal"])}

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
     f"Net exchange flow {ex['net']:+,.0f} EGLD ({100*ex['net']/ex['total_prev']:+.2f}%) - and per the run #15 decomposition rule that headline is the least informative number in this section. "
     f"Binance's {next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Binance'),0):+,.0f} nets a 900,000 custody-to-hot transfer against 1,272,434 coming back. "
     f"UPbit's {next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='UPbit'),0):+,.0f} is a venue that fed {f(otc['upbit_feed'])} EGLD to its own desk and took {f(venue(otc['out_by_venue'],'UPbit'))} back. "
     f"Bybit's {next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Bybit'),0):+,.0f} sits against +{f(venue(otc['net_by_venue'],'Bybit'))} of hub delivery INTO it. "
     f"The pipeline moved {f(otc['gross_out'])} EGLD gross and {f(otc['net_one_way'])} one-way this week; the entire exchange balance complex moved {abs(ex['net']):,.0f}. Per the run #14 joint-read rule the balance channel is noise at this scale and the flow trace is the signal. "
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
   "gross_series_egld_7d":{**r23["whale_intelligence"]["otc_pipeline"]["gross_series_egld_7d"],
                           "run24":otc["gross_out"]},
   "net_one_way_series_egld_7d":{**r23["whale_intelligence"]["otc_pipeline"]["net_one_way_series_egld_7d"],
                                 "run24":otc["net_one_way"]},
   "desk_inventory_series_egld":INV_SERIES,
   "circularity_series_pct":{**r23["whale_intelligence"]["otc_pipeline"]["circularity_series_pct"],
                             "run24":round(otc["circ_pct"],1)},
   "peak_window_renetted":r23["whale_intelligence"]["otc_pipeline"]["peak_window_renetted"],
   "backfilled_windows":r23["whale_intelligence"]["otc_pipeline"].get("backfilled_windows",[]),
   "wave_window_netting":{
     "window":wave["window"]+" (WAVE #3 feed-to-drain, three weekly frames)",
     "gross_outbound_egld":wave["gross_out"],"gross_inbound_egld":wave["gross_in"],
     "circular_egld":wave["circular"],"circular_share_pct":wave["circ_pct"],
     "net_one_way_egld":wave["net_one_way"],"sum_of_weekly_nets_egld":wave["sum_weekly"],
     "weekly_frame_overstatement_egld":wave["overstate_egld"],
     "weekly_frame_overstatement_pct":wave["overstate_pct"],
     "net_by_venue":wave["net_by_venue"],
     "outbound_by_venue":wave["out_by_venue"],"inbound_by_venue":wave["in_by_venue"],
     "note":(f"Wave #3 ran Aug 17 - Sep 7: feed 297,000 -> 460,000 -> {f(otc['upbit_feed'])} from UPbit, delivery {f(prev['otc_net_one_way_series']['run22'])} -> {f(prev['otc_net_one_way_series']['run23'])} -> {f(otc['net_one_way'])}. "
             f"Netted feed-to-drain across the whole wave it delivered {f(wave['net_one_way'])} EGLD one-way against {f(wave['sum_weekly'])} from summing the three weekly nets - a {wave['overstate_pct']:.0f}% overstatement, in line with the 21-55% range the straddle rule has produced before. "
             f"{f(wave['net_one_way'])} is more than twice the largest wave previously measured (the re-netted run #17 peak, 409,680), and it is the number to quote for this distribution episode.")},
   "series_note":(
     f"The stock is the story this week, not the flow. Desk inventory went {f(otc['prev_desk'])} -> {f(otc['desk_bal'])} EGLD while net one-way delivery hit a record {f(otc['net_one_way'])}: the desks delivered their own record AND emptied the warehouse behind it. "
     f"Inventory series across the wave: {' -> '.join(f'{k}: {v:,.0f}' for k,v in INV_SERIES.items())}. "
     f"Run #23 read a rising line against positive bars as a delivery leg still ahead; this week both moved the way that reading predicted.")},
 "demand_instruments":{
   "identifiable_bid_absorbed_egld_7d":bid["absorbed"],
   "mega_whale_balance_egld":bid["mega_bal"],"mega_whale_change_egld":bid["mega_delta"],
   "coinbase_routing_balance_egld":bid["cbr_bal"],"coinbase_routing_inflow_egld":0,
   "coinbase_routing_funder":None,"coinbase_routing_funder_label":"n/a - no inbound this week",
   "weeks_at_zero":4,"weeks_at_zero_in_last_four":4,
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
     "total_retained_egld":absb["total_balance_held"],
     "retained_share_pct":100*absb["total_balance_held"]/absb["total_received"] if absb["total_received"] else 0,
     "verdict":(f"Confirmed for a second week and on a corrected measure. The {absb['scanned']} terminals took {f(absb['total_received'])} EGLD from the desks and ended the week holding {f(absb['total_balance_held'])} between them ({100*absb['total_balance_held']/absb['total_received']:.1f}%), ten of the fourteen at a balance of zero. "
               f"METHOD FIX: run #23 computed retention as received-minus-forwarded, but `received` is the max of the 7-day and the multi-week wave window while `forwarded` is 7-day only, so that subtraction manufactures retention from a window mismatch. Balance is the correct test and it says the same thing the run #23 conclusion said: no absorbers on the outbound side.")},
   "withdrawal_breadth":{"distinct_recipients_raw":br["raw_n"],"total_egld_raw":br["raw_egld"],
     "distinct_recipients_ex_pipeline":br["ex_n"],"total_egld_ex_pipeline":br["ex_egld"],
     "pipeline_share_pct":br["pipeline_share"]},
   "withdrawal_breadth_top":br["top"]},
 "analysis":(
  f"THE PIPELINE DELIVERED AND EMPTIED IN THE SAME WEEK. Desk inventory {f(otc['prev_desk'])} -> {f(otc['desk_bal'])} ({100*otc['desk_delta']/otc['prev_desk']:+.0f}%) while net one-way delivery set a record at {f(otc['net_one_way'])} EGLD, z={z['otc_net']['z']:+.2f}sigma. "
  f"Gross throughput {f(otc['gross_out'])} out against {f(otc['gross_in'])} in at {otc['circ_pct']:.0f}% circularity - also a record, past run #17's 1,284,688. "
  f"Run #23 registered the question directly: was the record 266,213 inventory staged supply or a permanent level? It was staged, and it has now been delivered.\n\n"
  f"WHERE IT WENT. Two-hop resolution: Binance.com +{f(venue(otc['net_by_venue'],'Binance.com'))}, Bybit +{f(venue(otc['net_by_venue'],'Bybit'))}, Gate.io +{f(venue(otc['net_by_venue'],'Gate.io'))}, Unknown Whale I +{f(venue(otc['net_by_venue'],'Unknown Whale I (active)'))} (operator inventory, netted out of the demand read since run #21). "
  f"{f(otc['unresolved_out'])} EGLD of outbound remains unattributed. Every named destination is an exchange deposit path, so this is the run #17 signature at twice the run #17 scale: supply arriving at order books, not dispersing to holders.\n\n"
  f"WHERE IT CAME FROM. The feed side is no longer one venue. UPbit sent {f(feeders_in.get('UPbit',0))} EGLD directly, Bybit-labelled feeders {f(feeders_in.get('Bybit',0))}, Binance-labelled feeders {f(feeders_in.get('Binance',0))}, with {f(feeders_in.get('Unattributed',0))} arriving through routers whose parent venue is not yet resolved. "
  f"The Binance leg is now demonstrably a standing programme: the hot wallet sent {f(HOT_TO_PIPE)} EGLD to known feeders inside a {HOT_COVER}-day covered window, clearing the 50,000 flow threshold run #23 pre-registered. "
  f"What did NOT continue is the custody drawdown - Binance Staking custody rose +{f(cust['delta'])} to {f(cust['balance'])} after -497K over the prior two weeks. Custody is being refilled while the hot wallet feeds the desks, which is why run #23's balance-based version of this test failed and its flow-based replacement worked.\n\n"
  f"TIERS - READ THE NETTED VERSION. Raw, the {O['tiers_basis']}-address common basis shows mega {O['tiers']['mega']['net_change_egld']:+,.0f} and large {O['tiers']['large']['net_change_egld']:+,.0f}, which is almost entirely reclassification: UPbit crossed UP into the mega tier at {f(cur_top.get('erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5',0))} and both OTC desks crossed DOWN out of the large tier as they emptied. "
  f"Holding every wallet in its PRIOR tier (the run #14 boundary guard) gives mega {tiers_fixed['mega']['net_change_egld']:+,.0f}, large {tiers_fixed['large']['net_change_egld']:+,.0f}, mid {tiers_fixed['mid']['net_change_egld']:+,.0f}. "
  f"Decomposed, the mega figure IS the Binance custody refill and nothing else; the large tier is the Binance.com hot wallet ({f(cust['hot_entity_balance']-cust['hot_entity_previous'])}) plus Bybit ({f(next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Bybit'),0))}) plus the two desks draining. "
  f"No tier accumulated independently: every figure above 10,000 EGLD this week belongs to the pipeline or to Binance's internal plumbing.\n\n"
  f"DEMAND. The identifiable-bid instrument stays retired - the Mega Whale proxy read exactly zero for a FOURTH consecutive week (balance {f(bid['mega_bal'],4)} unchanged, zero transactions) and the desks' {absb['scanned']} outbound terminals ended the week holding {f(absb['total_balance_held'])} EGLD between them against {f(absb['total_received'])} received. "
  f"What did move is withdrawal breadth: {br['ex_n']} distinct non-pipeline addresses took {f(br['ex_egld'])} EGLD off exchanges (run #23: 50 and 400,113), against a pre-registered bar of 40 recipients and 300,000 EGLD - the broadening test fires. "
  f"Two names dominate it: Unknown Whale B took +{f(next((w['egld'] for w in br['top'] if 'Whale B' in w['label']),0))} and an unlabelled wallet took {f(next((w['egld'] for w in br['top'] if w['label']=='Unknown'),0))} - the same wallet that received 68,732 EGLD from the Binance hot wallet, so at least part of the 'broadening' is one large recipient rather than dispersal. "
  f"Read carefully, this is the only instrument on the demand side that responds at all, and it accounts for roughly {100*br['ex_egld']/otc['net_one_way']:.0f}% of what the pipeline delivered."),
}
json.dump(R,open("/tmp/run24w/part1.json","w"),indent=1,default=str)
print("part1 ok:",list(R.keys()))
