#!/usr/bin/env python3
"""Run #25 stage 2: metadata, executive summary, network health, whale intelligence -> /tmp/run25w/part1.json"""
import json
from datetime import datetime, timezone

REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-09-14"
O=json.load(open("/tmp/run25w/derived.json"))
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev=json.load(open("/tmp/run25w/previous_run24.json"))
kn=json.load(open("/tmp/run25w/known_run24.json"))
status=json.load(open("/tmp/run25w/status.json"))
beh=json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
r24=json.load(open(f"{REPO}/reports/2026-09-07.json"))

M=O["macro"]; otc=O["otc"]; wave=otc["wave"]
ex=O["exch"]; cust=O["custody"]; bid=O["bid"]; br=O["breadth"]
sk=O["staking"]; tk=O["tokens"]; xx=O["xexchange"]; df=O["defi"]; z=O["z"]
ub=O["unbond"]; absb=O["absorbers"]; zsc=O["zero_stake_cohort"]
HOT=O["hot_to_pipe"]; FEED=O["feeders_in"]; BOOK=O["orderbook"]; MEXE=O["mex_event"]
econ=D["economics"]; st=D["stats"]; pecon=prev["economics"]; pact=prev["activity"]
price=M["price"]; pc=M["price_chg"]
cvc=beh["aggregates"]["compound_vs_claim_at_function_level"]
def f(x,d=0):
    try: return f"{x:,.{d}f}"
    except: return str(x)
def V(d_,k,default=0.0): return d_.get(k,default)
def ent(n): return next((e2 for e2 in ex["entity"] if e2["entity"]==n),{"net_flow_egld":0,"pct":0,"wallets_count":0})

# ---- boundary-crossing-netted tiers (run #14 guard) ------------------------
cur_top={x["address"]:int(x["balance"])/1e18 for x in D["top_accounts"]}
prev_top={x["address"]:x["balance_egld"] for x in prev["top_accounts"]}
def tier(v):
    if v>1_000_000: return "mega"
    if v>=100_000: return "large"
    if v>=10_000: return "mid"
cm={}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"): cm[a]=m.get("category","unknown")
common=[a for a in cur_top if a in prev_top and not a.startswith("erd1qqqqqqqqqqqqq") and cm.get(a,"unknown")!="system"]
fixed={"mega":[0.0,0.0],"large":[0.0,0.0],"mid":[0.0,0.0]}
for a in common:
    t=tier(prev_top[a])
    if not t: continue
    fixed[t][0]+=prev_top[a]; fixed[t][1]+=cur_top[a]
tiers_fixed={t:{"previous":fixed[t][0],"current":fixed[t][1],
                "net_change_egld":fixed[t][1]-fixed[t][0],
                "net_change_pct":100*(fixed[t][1]-fixed[t][0])/fixed[t][0] if fixed[t][0] else 0}
             for t in fixed}
O["tiers_fixed"]=tiers_fixed
json.dump(O,open("/tmp/run25w/derived.json","w"),indent=1,default=str)

# ---- scale instruments ------------------------------------------------------
spot7=BOOK.get("spot_volume_7d_egld") or 0
spot7p=BOOK.get("spot_volume_prior_7d_egld") or 0
deliv_share=100*otc["net_one_way"]/spot7 if spot7 else None
prev_deliv_share=100*prev["otc_net_one_way_series"]["run24"]/spot7p if spot7p else None
bb_bid=BOOK["binance"]["depth_minus2_usd"]+BOOK["bybit"]["depth_minus2_usd"]
bb_net_usd=(V(otc["net_by_venue"],"Binance.com")+V(otc["net_by_venue"],"Bybit"))*price
FB=O["feeder_backtrace"]; FB0=FB[0] if FB else {}
fb0_par=FB0.get("parent_attribution_egld",{})
cg_prices=BOOK.get("daily_prices") or []
peak=max(cg_prices) if cg_prices else None
mex_cg=MEXE["mex_price_coingecko_now"]; mex_pre=MEXE["mex_price_coingecko_sep13"]
from datetime import datetime as _DT, timezone as _TZ
INC=MEXE.get("incident") or {}
WA=INC["wallets"]["A"]; WB=INC["wallets"]["B"]
PZ={p["pair"]:p for p in INC["pauses"]}
def HM(t): return _DT.fromtimestamp(t,tz=_TZ.utc).strftime("%H:%M")
BORROW_FIRST=HM(WA["borrows"][0]["ts"]); BORROW_LAST=HM(WA["borrows"][-1]["ts"])
MEX_CIRC=float(D["mex_economics"]["circulatingSupply"])
HATOM_URL=INC["statement"]["source"]

wegld_vol_pct=100*(bid["dexvol_egld"]-bid["prev_dexvol_egld"])/bid["prev_dexvol_egld"]
stab=tk["stable"]; usdc=stab["USDC-c76f1f"]; usdt=stab["USDT-f8c08c"]
comb=usdc["supply"]+usdt["supply"]; combp=usdc["prev"]+usdt["prev"]
comb_pct=100*(comb-combp)/combp
UPBIT_RES=next((e2["current"] for e2 in ex["entity"] if e2["entity"]=="UPbit"),0)

R={}
R["metadata"]={"report_date":RD,"period_start":"2026-09-07","period_end":RD,
  "generated_at":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
  "egld_price_usd":price,"btc_price_usd":M["btc"],"eth_price_usd":M["eth"],
  "run_number":25,
  # Run #23 rule: a source is only "failed" if the report ships without its data. None of this
  # run's four candidates qualifies, so they are recorded where their data actually came from.
  "data_sources_ok":status["ok"]+[
    "/tokens/WTAO-3ec9c0: HTTP 404 as expected - a known-bad identifier kept in the pre-flight recheck as a control; the live WrappedTAO (WTAO-4f5363) was priced"],
  "data_sources_failed":status["failed"],
  "data_sources_recovered":[
    "MEX price: /mex/economics returns $0 because the MEX/WEGLD pool is paused, not because the endpoint is down (no resume call as of the report). Priced from CoinGecko instead, with the MultiversX /tokens quote alongside; the onchain pool price returns when the pools resume",
    "MEX/WEGLD pool data: /mex/pairs drops paused pools (the pair route returns 404). Reserves (191B MEX, 141,281 WEGLD), the pause call and all 223 pool transactions were read directly from the pair contract",
    "SALSA and VestaX liquid staking: this week's discovery sweep did not list them, so their delegated stake (6,420 and 1,121 EGLD) was measured directly from each contract's delegation endpoint",
    "desk wave-window legs (OTC Distribution Wallet, both directions): HTTP 429 on the main pass while the reward-behaviour scan ran concurrently; re-paged by a follow-up pass and the four-week hub trace rebuilt from the recovered legs",
    "delegator reward behaviour: the concurrent first pass sampled only 4 of 8 providers under rate limiting; re-run alone, 8 of 8, zero 429s",
    "/accounts/{Binance.com hot}/transactions - queried in per-calendar-day slices in the main pass (run #24 rec #3), 772 outbound txs, zero day-slices capped"]}

R["executive_summary"]=[
 {"category":"defi","severity":"critical","finding":
  f"HATOM'S MEX MONEY MARKET HAD AN INCIDENT, AND XEXCHANGE PAUSED THREE MEX POOLS TO CONTAIN IT. On Sep 13, while MEX was rising on xExchange, one wallet (erd10fe5lv5v...fuqq) spent {f(WA['egld_spent_buying_mex'])} EGLD buying {f(WA['mex_bought']/1e9,0)}B MEX through xExchange, deposited {f(WA['mex_deposited']/1e9,0)}B MEX ({100*WA['mex_deposited']/MEX_CIRC:.1f}% of circulating supply) into Hatom's MEX market as collateral (HMEX supply {100*(MEXE['hmex_supply']-MEXE['hmex_prev_supply'])/MEXE['hmex_prev_supply']:+.0f}% on the week), and borrowed {f(WA['egld_borrowed'])} EGLD from Hatom's EGLD market in {len(WA['borrows'])} draws between {BORROW_FIRST} and {BORROW_LAST} UTC. The xExchange router owner paused MEX/WEGLD at 16:43, six minutes after the last draw, then MEX/USH at {HM(PZ['MEX/USH']['ts'])} and MEX/USDC at {HM(PZ['MEX/USDC']['ts'])}. Hatom's statement (Sep 14, 21:03 UTC) says user funds are safe, the incident is contained, and a recovery plan will unwind the incident-driven activity without user losses or bad debt; the MEX market and the three pairs should resume by Wednesday. Hatom has not stated a cause yet. MEX is still {xx['mex_wow']:+.0f}% on the week at {mex_cg:.2e} (CoinGecko), the paused MEX/WEGLD pool holds {f(MEXE['pair_holds_mex']/1e9,1)}B MEX and {f(MEXE['pair_holds_wegld'])} WEGLD, and 172 calls against it failed in the week."},
 {"category":"whale","severity":"high","finding":
  f"WAVE #4 IS UNDER WAY - THE DISTRIBUTION PROGRAMME IS CONTINUOUS. UPbit sent {f(otc['upbit_feed'])} EGLD into its desk, above the 200,000 branch run #24 pre-registered, and the desks delivered {f(otc['net_one_way'])} EGLD one-way on {f(otc['gross_out'])} gross (circularity {otc['circ_pct']:.0f}%). Destinations two hops out: Binance.com +{f(V(otc['net_by_venue'],'Binance.com'))}, Bybit +{f(V(otc['net_by_venue'],'Bybit'))}, Gate.io +{f(V(otc['net_by_venue'],'Gate.io'))}. The desk balance fell to {f(otc['desk_bal'])}, but it is a working float, not a stock being sold down: the UPbit wallet that refills it still holds {f(UPBIT_RES)} EGLD. Netted as one window from Aug 17 to Sep 14 the programme has delivered {f(wave['net_one_way'])} EGLD one-way; the four weekly figures sum to {f(wave['sum_weekly'])}, a {wave['overstate_pct']:.0f}% overstatement. The 55% weekly circularity sits below the 63-80% band, the run #21 sign that a return leg landed from an earlier week."},
 {"category":"network","severity":"high","finding":
  f"EGLD FELL {abs(pc):.2f}% TO ${price:.2f} WHILE THE MAJORS HELD - AND THE ORDER BOOK SHOWS WHY THE PIPELINE IS NOT THE WHOLE STORY. BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%: a third consecutive EGLD-specific week, this time to the downside, after a peak near ${peak:.2f} on the CoinGecko daily series. The first exchange-side measurement this model has taken puts the week in scale: CEX spot volume was {f(spot7/1e6,1)}M EGLD over seven days ({100*(spot7-spot7p)/spot7p:+.0f}% WoW), so the desks' one-way delivery was {deliv_share:.1f}% of it, against {prev_deliv_share:.1f}% in the record week. On depth, Binance and Bybit together show ${f(bb_bid)} of bids within 2% of mid, and the pipeline's net delivery into those two venues this week was ${f(bb_net_usd)}, about {bb_net_usd/bb_bid:.0f}x that visible bid. The desks' supply is worked into the book over days rather than hitting it at once, and it is a small fraction of what trades. Run #24's price-only bid test ended inconclusive at ${price:.2f}."},
 {"category":"staking","severity":"high","finding":
  f"THE STAKED RATIO BROKE 46.80% IN WEEK ONE OF A THREE-WEEK TEST: {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp), z={z['sr']['z']:+.2f}sigma. Staked EGLD fell {f(abs(M['staked_chg']))} while delegation TVL ROSE {f(sk['delta_locked'])}, a residual of {f(sk['residual'])}. The timing fits the previous two weeks' unbonding queues (151,443 and 208,125 EGLD) maturing, while fresh unDelegations fell to {f(sk['undelegated_week'])} EGLD from {sk['undelegate_callers']} wallets. The branch fires as registered and the security budget is at a new low. The forward read is weaker than the level: the inflow into the queue is a third of last week's. That attribution rests on timing; withdraw amounts are not measured, and withdraw calls rose only from 528 to 573."},
 {"category":"staking","severity":"high","finding":
  f"DELEGATORS TOOK MORE REWARDS IN CASH THAN THEY COMPOUNDED FOR THE FIRST TIME IN TWELVE READINGS. Compound rate {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} redelegate vs {cvc['claim_count']} claim), down from 62.05%, z={z['compound']['z']:+.2f}sigma. The claimants did not sell: 0 of 73 retail claims and 1 of 21 mid-tier claims went to a labelled exchange. In a week that ran from ${peak:.2f} to ${price:.2f}, delegators pulled yield into their wallets and held it there. That points to preparation or risk reduction. It does not show up as selling."},
 {"category":"whale","severity":"medium","finding":
  f"THE BINANCE FEED IS A PERMANENT LINE AND THE LARGEST UNATTRIBUTED FEEDER IS BYBIT AND GATE.IO. Queried one day at a time with no capped slices, the Binance.com hot wallet sent {f(HOT['total_egld'])} EGLD to known desk feeders and routers, the third consecutive week above 50,000. It also moved {f(cust['delta'])} into staking custody. Run #24 guessed that the 196,492 EGLD feeder with no parent venue would name a fifth feeding venue. Two hops back it does not: erd1ytpenkzj received {f(V(fb0_par,'Bybit'))} EGLD from Bybit and {f(V(fb0_par,'Gate.io'))} from Gate.io over the wave. The feed side is UPbit, Binance, Bybit and Gate.io, the same four venues the desks deliver back into."},
 {"category":"token","severity":"medium","finding":
  f"THE DOLLAR-BASE PROMOTION IS WITHDRAWN AFTER ONE WEEK. USDC {usdc['pct']:+.2f}% to {f(usdc['supply'])}, USDT {usdt['pct']:+.2f}% to {f(usdt['supply'])}; combined {comb_pct:+.2f}%, the first combined expansion in four weeks. Run #24's test said any expansion demotes the series to the DeFi section, and it does. USDT's -12.8% is the largest weekly move in the tracked series, but USDC more than offset it. Separately, two newly issued tokens cleared the >10-holder / >5-transaction bar (BRO-aa5132, 18 holders; ECAT-4ebd0f, 15), which ends an eight-week run in which none did."},
 {"category":"defi","severity":"medium","finding":
  f"THE VENUE RAN HOT ON ONE PAIR. xExchange volume in EGLD terms {f(bid['prev_dexvol_egld'])} -> {f(bid['dexvol_egld'])}/day ({wegld_vol_pct:+.0f}%), {bid['wegld_usdc_share']:.1f}% of it WEGLD/USDC; every other pair together traded ${f(bid['ex_wegld_usdc_vol'])}. Hatom's EGLD market lost depositors too (HEGLD supply {df['h_tokens']['HEGLD-d61095']['supply_pct']:+.2f}%). Pool TVL is down {abs(100*(bid['pooltvl']-bid['prev_pooltvl'])/bid['prev_pooltvl']):.0f}% in dollars on the raw series, but most of that is the frozen MEX/WEGLD pool dropping out of the API. On a like-for-like base it is {bid['pooltvl_ex_mex_wow_pct']:+.1f}% in USD and {bid['pooltvl_egld_ex_mex_wow_pct']:+.1f}% in EGLD. Aggregator routing surged on the pause day: XOXNO {f(df['proto'].get('XOXNO Aggregator'))} transfers/24h (from 20,471) and OneDex {f(df['proto'].get('OneDex Swap'))} (from 10,408). The re-derived JEXchange router did {f(O['jex_router_7d'].get('JEXchange Router'))} transfers in 7 days, so the address test resolves as predicted."},
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
  "btc_correlation_note":f"BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%, EGLD {pc:+.2f}%. Third consecutive EGLD-specific week under the run #16 rule, and the first of the three to the downside. The CoinGecko daily series shows the round trip inside the window: up to about ${peak:.2f}, then down to ${price:.2f}."},
 "analysis":(
  f"EGLD closed at ${price:.2f}, {pc:+.2f}% on the week, with BTC {M['btc_wow']:+.2f}% and ETH {M['eth_wow']:+.2f}%. The snapshot-to-snapshot figure hides a round trip. On CoinGecko's daily series EGLD pushed to about ${peak:.2f} early in the window, extending last week's move, and then gave back roughly a fifth of its value into Sunday. z={z['price']['z']:+.2f}sigma, which understates it: four up-weeks pulled the baseline mean to ${z['price']['mean']:.2f}, below the current price (the run #16 under-flag rule).\n\n"
  f"THE STAKED RATIO BROKE ITS FLOOR. Staked EGLD fell {f(abs(M['staked_chg']))} to {f(econ['staked'])}. With {f(econ['totalSupply']-pecon['total_supply'])} EGLD of emission on top, the ratio fell {100*(M['sr']-M['sr_prev']):+.2f}pp to {100*M['sr']:.2f}%, below the 46.80% line run #24 registered as the genuine-downtrend branch. It is the lowest reading in the archive by a wide margin, z={z['sr']['z']:+.2f}sigma.\n\n"
  f"The mechanism matters for what happens next. Delegation TVL ROSE {f(sk['delta_locked'])} in the same week, so the fall in staked EGLD is not in the delegation layer's active stake. The staked-minus-delegated residual moved {f(sk['residual'])}. The most likely explanation is timing: the two previous full-set scans found 151,443 and 208,125 EGLD entering the unbonding queue, and the unbonding period for much of that ends inside this window. The evidence for it is circumstantial. {sum(v['function_counts'].get('withdraw',0) for v in D['provider_inbound_all'].values())} withdraw calls hit provider contracts this week against 528 last week, and the scan does not decode withdraw amounts. What is measured is the inflow: new unDelegations fell to {f(sk['undelegated_week'])} EGLD from {sk['undelegate_callers']} wallets, a third of last week's. The security budget did shrink. The pipe feeding the next round has narrowed.\n\n"
  f"Activity: {f(st['transactions']-pact['total_transactions'])} transactions over {st['epoch']-pact['epoch']} epochs ({f(int((st['transactions']-pact['total_transactions'])/7))}/day) and {f(st['accounts']-pact['total_accounts'])} new accounts. Network APR {100*(econ['apr']-pecon['staking_apr']):+.3f}pp to {100*econ['apr']:.2f}%, which is what a smaller staked base does to a fixed reward.\n\n"
  f"FOR THE FIRST TIME THE MODEL CAN PUT THE PIPELINE IN MARKET SCALE. CoinGecko's aggregate spot volume for EGLD was {f(spot7/1e6,2)}M EGLD over the seven days, against {f(spot7p/1e6,2)}M in the record-delivery week. The desks' one-way delivery of {f(otc['net_one_way'])} is {deliv_share:.1f}% of it, and last week's record 536,459 was {prev_deliv_share:.1f}%. Run #24 ended on the claim that a record delivery was absorbed by a bid nobody could see. Part of that bid is simply the market's ordinary turnover, which is some fifty times the pipeline's weekly flow. This does not make the pipeline irrelevant. It is persistent, one-directional and aimed at two venues, and a steady 2% net offer can move a price the other 98% only churns. It does mean a week's delivery cannot be read against the week's price as if nothing else traded."),
}

# ---------------------------------------------------------------------------
# whale intelligence
# ---------------------------------------------------------------------------
def entity_interp(e):
    n=e["entity"]; v=e["net_flow_egld"]
    if n=="Binance":
        return (f"{v:+,.0f} across {e['wallets_count']} wallets, and almost all of it is one internal transfer: the Binance.com hot wallet sent {f(cust['delta'])} EGLD to staking custody (custody now {f(cust['balance'])}). "
                f"Externally, day-sliced with no capped slices, the hot wallet sent {f(HOT['total_egld'])} EGLD into known OTC desk feeders and routers - a third consecutive week above 50,000 - and Binance-parented feeders delivered {f(FEED.get('Binance',0))} into the desks. "
                f"The hot complex ended at {f(cust['hot_entity_balance'])} against {f(cust['hot_entity_previous'])}: it funded the pipeline and custody at once and still closed nearly flat.")
    if n=="UPbit":
        return (f"{v:+,.0f} ({e['pct']:+.1f}%) while sending {f(otc['upbit_feed'])} EGLD to its own desk (the 150,000 and 53,000 transfers lead the large-transaction list) and taking {f(V(otc['out_by_venue'],'UPbit'))} back. "
                f"Loading leg, not customer withdrawal (run #16 rule). Tranche series 297,000 / 460,000 / 462,000 / {f(otc['upbit_feed'])}.")
    if n=="Bybit":
        return (f"{v:+,.0f} ({e['pct']:+.1f}%), essentially flat against a hub net of +{f(V(otc['net_by_venue'],'Bybit'))} delivered into it. Bybit is on both legs: {f(V(otc['out_by_venue'],'Bybit'))} received from the desks, {f(V(otc['in_by_venue'],'Bybit'))} fed in, and the largest unattributed feeder traces back to it. A flat balance under net delivery means customers withdrew about what the desks deposited.")
    if n=="Gate.io":
        return f"{v:+,.0f} ({e['pct']:+.1f}%), a second week of growth, with +{f(V(otc['net_by_venue'],'Gate.io'))} of hub delivery into it. Gate.io is also the second parent of the largest unattributed feeder, so it runs inventory both ways."
    if n=="Bitget":
        return f"{v:+,.0f} ({e['pct']:+.1f}%). Not a hub destination this week; an ordinary withdrawal of a quarter of the tracked balance."
    if n=="Coinbase":
        return f"{v:+,.0f} ({e['pct']:+.1f}%), a fourth consecutive fall. Coinbase still appears in no pipeline window, so this is plain customer withdrawal. Unknown Whale B cycled 27,963 in and 14,591 out on its secondary wallet."
    return f"{v:+,.0f} across {e['wallets_count']} wallet(s), {e['pct']:+.2f}%."

INV_SERIES={**prev["otc_desk_inventory_series"],"run25":round(otc["desk_bal"])}
fbv={}
for p_,v_ in FEED.items(): fbv[p_]=v_
feed_by_parent=[{"venue":k,"egld_7d":v} for k,v in sorted(fbv.items(),key=lambda x:-x[1])]

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
     f"Net exchange flow {ex['net']:+,.0f} EGLD ({100*ex['net']/ex['total_prev']:+.2f}%), and per the run #15 rule it decomposes to one transfer: Binance {ent('Binance')['net_flow_egld']:+,.0f}, of which {f(cust['delta'])} is the hot wallet moving EGLD into its own staking custody. "
     f"Ex-Binance the complex moved {ex['net']-ent('Binance')['net_flow_egld']:+,.0f}: UPbit {ent('UPbit')['net_flow_egld']:+,.0f} (desk loading), Gate.io {ent('Gate.io')['net_flow_egld']:+,.0f}, Bitget {ent('Bitget')['net_flow_egld']:+,.0f}, Coinbase {ent('Coinbase')['net_flow_egld']:+,.0f}. "
     f"Against a pipeline gross of {f(otc['gross_out'])} the balance channel is noise again. {len(ex['noprior'])} addresses without a prior-week balance were excluded per the run #18 rule."),
   "by_exchange":[{"exchange":w["exchange"],"change_egld":w["change_egld"],"pct":w["pct"]} for w in ex["per_wallet"]],
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
                     "venue_to_desk_egld":otc["in_by_venue"].get(v,0),"net_egld":otc["net_by_venue"][v]}
                    for v in sorted(otc["net_by_venue"],key=lambda k:-abs(otc["net_by_venue"][k]))],
   "gross_series_egld_7d":{**r24["whale_intelligence"]["otc_pipeline"]["gross_series_egld_7d"],"run25":otc["gross_out"]},
   "net_one_way_series_egld_7d":{**r24["whale_intelligence"]["otc_pipeline"]["net_one_way_series_egld_7d"],"run25":otc["net_one_way"]},
   "desk_inventory_series_egld":INV_SERIES,
   "circularity_series_pct":{**r24["whale_intelligence"]["otc_pipeline"]["circularity_series_pct"],"run25":round(otc["circ_pct"],1)},
   "peak_window_renetted":r24["whale_intelligence"]["otc_pipeline"]["peak_window_renetted"],
   "backfilled_windows":r24["whale_intelligence"]["otc_pipeline"].get("backfilled_windows",[])+[
     {"window":"2026-08-17..2026-09-07 (WAVE #3 netted feed-to-drain, run #24)",
      "gross_egld":r24["whale_intelligence"]["otc_pipeline"]["wave_window_netting"]["gross_outbound_egld"],
      "circular_egld":r24["whale_intelligence"]["otc_pipeline"]["wave_window_netting"]["circular_egld"],
      "net_one_way_egld":r24["whale_intelligence"]["otc_pipeline"]["wave_window_netting"]["net_one_way_egld"],
      "circular_share_pct":r24["whale_intelligence"]["otc_pipeline"]["wave_window_netting"]["circular_share_pct"],
      "net_by_venue":r24["whale_intelligence"]["otc_pipeline"]["wave_window_netting"]["net_by_venue"]}],
   "wave_window_netting":{
     "window":wave["window"]+" (waves #3 and #4 as ONE feed-to-drain window, four weekly frames)",
     "gross_outbound_egld":wave["gross_out"],"gross_inbound_egld":wave["gross_in"],
     "circular_egld":wave["circular"],"circular_share_pct":wave["circ_pct"],
     "net_one_way_egld":wave["net_one_way"],"sum_of_weekly_nets_egld":wave["sum_weekly"],
     "weekly_frame_overstatement_egld":wave["overstate_egld"],
     "weekly_frame_overstatement_pct":wave["overstate_pct"],
     "net_by_venue":wave["net_by_venue"],
     "outbound_by_venue":wave["out_by_venue"],"inbound_by_venue":wave["in_by_venue"],
     "note":(f"Netted as one window from Aug 17 to Sep 14, the programme delivered {f(wave['net_one_way'])} EGLD one-way. The four weekly nets sum to {f(wave['sum_weekly'])}, a {wave['overstate_pct']:.0f}% overstatement, smaller than wave #3's 21% on its own. "
             f"The four-week figure is {f(wave['net_one_way']-r24['whale_intelligence']['otc_pipeline']['wave_window_netting']['net_one_way_egld'])} above run #24's three-week measure of 878,809, which is more than this week's weekly net. Legs from earlier weeks resolved against this week's returns. "
             f"UPbit is the sole net source across the window at {f(V(wave['net_by_venue'],'UPbit'))}. The OTC Distribution Wallet legs of this trace were rebuilt after a rate-limit failure on the main pass (followup_run25.py).")},
   "feed_by_parent_venue":feed_by_parent,
   "feeder_backtrace":FB,
   "series_note":(
     f"Delivery held near record scale for a second week while the desk float fell. End-of-week desk balance {' -> '.join(f'{k}: {v:,.0f}' for k,v in INV_SERIES.items())}, while net one-way delivery was {f(otc['net_one_way'])}, the second-largest week on record. "
     f"The desk balance ({f(otc['desk_bal'])}) is a float that UPbit's {f(UPBIT_RES)} EGLD wallet refills, so a low reading does not mean supply is running out. The inventory line shows what sat on the desks at each week's end, not what is left to sell.")},
 "demand_instruments":{
   "identifiable_bid_absorbed_egld_7d":bid["absorbed"],
   "mega_whale_balance_egld":bid["mega_bal"],"mega_whale_change_egld":bid["mega_delta"],
   "coinbase_routing_balance_egld":bid["cbr_bal"],"coinbase_routing_inflow_egld":0,
   "coinbase_routing_funder":None,"coinbase_routing_funder_label":"n/a - no inbound this week",
   "weeks_at_zero":5,"weeks_at_zero_in_last_four":4,
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
     "verdict":(f"Third week, same answer, measured on end-of-week balance. The {absb['scanned']} terminals took {f(absb['total_received'])} EGLD from the desks across the four-week window and ended holding {f(absb['total_balance_held'])} EGLD between them. "
               "There are no absorbers on the outbound side of the pipeline.")},
   "withdrawal_breadth":{"distinct_recipients_raw":br["raw_n"],"total_egld_raw":br["raw_egld"],
     "distinct_recipients_ex_pipeline":br["ex_n"],"total_egld_ex_pipeline":br["ex_egld"],
     "pipeline_share_pct":br["pipeline_share"],"top_two_share_pct":br["top_two_share_pct"]},
   "withdrawal_breadth_top":br["top"],
   "exchange_orderbook":{
     "source":"CoinGecko exchange tickers with 2% depth, and daily spot volume (third-party, first reading run #25)",
     "binance":BOOK["binance"],"bybit":BOOK["bybit"],"upbit":BOOK["upbit"],
     "coinbase":BOOK["coinbase"],"gate":BOOK["gate"],"all_venues":BOOK["all"],
     "spot_volume_7d_egld":spot7,"spot_volume_prior_7d_egld":spot7p,
     "net_one_way_share_of_spot_volume_pct":deliv_share,
     "previous_net_one_way_share_of_spot_volume_pct":prev_deliv_share,
     "binance_bybit_net_delivery_usd_7d":bb_net_usd,
     "binance_bybit_bid_depth_2pct_usd":bb_bid,
     "delivery_share_series":BOOK["delivery_share_series"],
     "top_tickers":BOOK["top"]}},
 "analysis":(
  f"WAVE #4 CONFIRMED, AND THE RESERVOIR BEHIND THE DESKS IS STILL FULL. UPbit fed {f(otc['upbit_feed'])} EGLD, the fourth straight tranche above 290,000, and the desks delivered {f(otc['net_one_way'])} one-way on {f(otc['gross_out'])} gross. "
  f"The desk balance moved {f(otc['prev_desk'])} -> {f(otc['desk_bal'])}. That is a pass-through float, not an inventory: the UPbit wallet feeding it still holds {f(UPBIT_RES)} EGLD, roughly eighteen times the desk balance. z={z['otc_net']['z']:+.2f}sigma on the net series, the second-largest week in tracking behind last week's record.\n\n"
  f"WHERE IT WENT. Binance.com +{f(V(otc['net_by_venue'],'Binance.com'))} ({f(V(otc['out_by_venue'],'Binance.com'))} out, {f(V(otc['in_by_venue'],'Binance.com'))} back), Bybit +{f(V(otc['net_by_venue'],'Bybit'))}, Gate.io +{f(V(otc['net_by_venue'],'Gate.io'))}, plus the Unknown Whale I operator and its router. UPbit took {f(V(otc['out_by_venue'],'UPbit'))} back from the desks. {f(otc['unresolved_out'])} EGLD of outbound is unattributed after two hops. "
  f"Circularity was {otc['circ_pct']:.0f}%, below the 63-80% band. That is the run #21 straddle signature, and the four-week window netting confirms it: {f(wave['net_one_way'])} one-way over Aug 17 - Sep 14 against {f(wave['sum_weekly'])} from the weekly frames.\n\n"
  f"WHO FEEDS IT. By parent venue this week: UPbit {f(FEED.get('UPbit',0))}, Binance-parented feeders {f(FEED.get('Binance',0))}, Bybit-parented {f(FEED.get('Bybit',0))}, unattributed {f(FEED.get('Unattributed',0))}. "
  f"Run #24's open question about the 196,492 EGLD feeder is answered by the back-trace. erd1ytpenkzj (nonce {FB0.get('nonce')}, balance {f(FB0.get('balance') or 0,2)}) received {f(V(fb0_par,'Bybit'))} EGLD from Bybit and {f(V(fb0_par,'Gate.io'))} from Gate.io over the wave. It is a Bybit/Gate.io pass-through, not a fifth venue. "
  f"Of the eight largest unlabelled feeders, seven resolve to Binance, Bybit or Gate.io within two hops, and the eighth to the Unknown Whale I operator. The feed side and the delivery side are the same four exchanges.\n\n"
  f"BINANCE. Day-sliced over the full seven days (772 outbound transactions, no capped slice), the hot wallet sent {f(HOT['total_egld'])} EGLD to known OTC desk feeders and routers. That is the third consecutive week above the 50,000 line run #24's watch item named, so Binance is a standing funding line for the pipeline. "
  f"The same wallet sent {f(cust['delta'])} to staking custody, which has now risen two weeks running to {f(cust['balance'])}. Custody refills and the desk feed run side by side, so the custody balance should no longer be read as a supply signal.\n\n"
  f"TIERS. On the common-address basis mega {O['tiers']['mega']['net_change_egld']:+,.0f}, large {O['tiers']['large']['net_change_egld']:+,.0f}, mid {O['tiers']['mid']['net_change_egld']:+,.0f}. Holding each wallet in its prior tier (run #14 guard): mega {tiers_fixed['mega']['net_change_egld']:+,.0f}, large {tiers_fixed['large']['net_change_egld']:+,.0f}, mid {tiers_fixed['mid']['net_change_egld']:+,.0f}. "
  f"The mega figure is the Binance custody refill. The raw mid-tier loss is reclassification: an unlabelled wallet (erd1ygqnssmn...) grew 39,294 -> 106,732 and left the tier. Once that is netted out every tier is slightly positive. Inside the large tier two contract moves offset each other: the xExchange WEGLD contract +100,133 EGLD and the Hatom EGLD money market -89,886 EGLD. {f(WA['egld_borrowed']+WB['egld_borrowed'])} EGLD of that Hatom outflow is the two MEX-collateral wallets' borrowing during the incident.\n\n"
  f"DEMAND - THE FIRST EXCHANGE-SIDE READING. Run #24's top recommendation was an instrument on the far side of the order book, and a crude one now exists. Across every venue CoinGecko tracks, EGLD has ${f(BOOK['all']['depth_minus2_usd'])} of bids and ${f(BOOK['all']['depth_plus2_usd'])} of asks within 2% of mid, on ${f(BOOK['all']['volume_24h_usd'])} of 24h volume. "
  f"Binance ({BOOK['binance']['pairs']} pairs) shows ${f(BOOK['binance']['depth_minus2_usd'])} of bids and ${f(BOOK['binance']['depth_plus2_usd'])} of asks, Bybit ${f(BOOK['bybit']['depth_minus2_usd'])} and ${f(BOOK['bybit']['depth_plus2_usd'])}. "
  f"Seven-day spot volume was {f(spot7/1e6,2)}M EGLD, so this week's one-way delivery was {deliv_share:.1f}% of it. That is the scale the model has been missing. The pipeline is a persistent, directional ~2% of turnover, not a flood, and a 17% up-week through a record delivery is less paradoxical at that scale than run #24 made it sound. "
  f"Bids sit deeper than asks on both of the pipeline's destination venues. That is one snapshot and cannot yet be called a trend; it is the baseline for next week's reading.\n\n"
  f"The on-chain demand instruments: withdrawal breadth {br['ex_n']} ex-pipeline recipients took {f(br['ex_egld'])} EGLD, with the top two at {br['top_two_share_pct']:.0f}% of value, under the 50% line, so run #24's concentration test resolves on the genuine-dispersal branch. DEX volume in EGLD more than doubled, but 98% of it is WEGLD/USDC in a falling week, which is selling volume. The identifiable-bid proxies stayed at zero for a fifth week."),
}
json.dump(R,open("/tmp/run25w/part1.json","w"),indent=1,default=str)
print("part1 ok:",list(R.keys()))
print("tiers_fixed:",{k:round(v['net_change_egld']) for k,v in tiers_fixed.items()})
print("deliv_share",deliv_share,prev_deliv_share,"bb",bb_bid,bb_net_usd,"peak",peak)
