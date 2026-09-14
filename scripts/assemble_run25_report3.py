#!/usr/bin/env python3
"""Run #25 stage 4: anomalies, trends, watch list, tests, meta_learning, merge -> reports/2026-09-14.json"""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-09-14"
O=json.load(open("/tmp/run25w/derived.json"))
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
beh=json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
status=json.load(open("/tmp/run25w/status.json"))
r24=json.load(open(f"{REPO}/reports/2026-09-07.json"))
p1=json.load(open("/tmp/run25w/part1.json")); p2=json.load(open("/tmp/run25w/part2.json"))
M=O["macro"]; otc=O["otc"]; wave=otc["wave"]; ex=O["exch"]
cust=O["custody"]; bid=O["bid"]; br=O["breadth"]; sk=O["staking"]; tk=O["tokens"]
xx=O["xexchange"]; df=O["defi"]; z=O["z"]; ub=O["unbond"]; absb=O["absorbers"]
zsc=O["zero_stake_cohort"]; em=O["emerging_lsd"]; MEXE=O["mex_event"]
HOT=O["hot_to_pipe"]; FEED=O["feeders_in"]; BOOK=O["orderbook"]; FB=O["feeder_backtrace"]
price=M["price"]; pc=M["price_chg"]; econ=D["economics"]
cvc=beh["aggregates"]["compound_vs_claim_at_function_level"]
OB=p1["whale_intelligence"]["demand_instruments"]["exchange_orderbook"]
def f(x,d=0):
    try: return f"{x:,.{d}f}"
    except: return str(x)
def zz(k): return z[k].get("z")
def V(d_,k): return d_.get(k,0.0)
def mv(ident,field,default=0):
    return next((m[field] for m in sk["moves"] if m["identity"]==ident), default)
def ent(n): return next((e2 for e2 in ex["entity"] if e2["entity"]==n),{"net_flow_egld":0,"pct":0,"wallets_count":0})
dser={d["identity"]:d for d in O["dereg_series"]}
usdc=tk["stable"]["USDC-c76f1f"]; usdt=tk["stable"]["USDT-f8c08c"]
comb=usdc["supply"]+usdt["supply"]; combp=usdc["prev"]+usdt["prev"]; comb_pct=100*(comb-combp)/combp
peak=max(BOOK["daily_prices"])
fb0=FB[0]["parent_attribution_egld"] if FB else {}
ht=df["h_tokens"]
R={}

R["anomalies"]=[
 {"metric":"mex_price_usd","current_value":xx["mex_price"],"previous_value":xx["prev_mex_price"],
  "method":"z_score","severity":"critical","average_value":z["mex"]["mean"],"stddev":z["mex"]["stddev"],"z_score":zz("mex"),
  "change_pct":xx["mex_wow"],
  "description":f"MEX {xx['mex_wow']:+.0f}% WoW on CoinGecko ({xx['prev_mex_price']:.2e} -> {xx['mex_price']:.2e}), z={zz('mex'):+.1f}sigma - the largest standardised move on any tracked series. It followed a `pause` on the MEX/WEGLD pool at 2026-09-13 16:43 UTC, sent by the xExchange router owner. The daily close jumped ~7.5x on about $1.6M of volume and has since given back 40%. /mex/economics reports MEX at $0 and /tokens at {MEXE['mex_price_tokens_api']:.2e}. No on-chain pool sets this price any more, so the z-score describes a quote, not a market the chain can see."},
 {"metric":"xexchange_mex_wegld_pair_state","current_value":0,"previous_value":MEXE["prev_pair_tvl_usd"],
  "method":"rule_based","severity":"critical","change_pct":-100.0,
  "description":f"The #2 deepest pool on xExchange (${f(MEXE['prev_pair_tvl_usd'])} last week) is paused and has been dropped from /mex/pairs. It holds {f(MEXE['pair_holds_mex']/1e9,1)}B MEX and {f(MEXE['pair_holds_wegld'])} WEGLD. 172 transactions have failed against it in the week, 116 of them removeLiquidity, so LPs are trying and failing to withdraw. This is the first venue-level state change in the archive, as opposed to a flow."},
 {"metric":"hatom_hmex_supply","current_value":MEXE["hmex_supply"],"previous_value":MEXE["hmex_prev_supply"],
  "method":"rule_based","severity":"high","change_pct":ht["HMEX-df6df7"]["supply_pct"],
  "description":f"HMEX supply {ht['HMEX-df6df7']['supply_pct']:+.0f}% ({f(MEXE['hmex_prev_supply']/1e12,2)}T -> {f(MEXE['hmex_supply']/1e12,2)}T): MEX was deposited into Hatom's MEX money market in size in the pause week. HMEX market cap went from ${f(ht['HMEX-df6df7']['prev_mcap'])} to ${f(ht['HMEX-df6df7']['mcap'])} and would have lifted Hatom Lending's EGLD TVL {df['hatom_lending_egld_pct']:+.0f}% if left in. The breakdown reports lending ex-HMEX ({df['hatom_lending_ex_hmex_egld_pct']:+.2f}%)."},
 {"metric":"reward_compound_pct","current_value":cvc["compound_pct_of_reward_decisions"],"previous_value":62.05,
  "method":"z_score","severity":"high","average_value":z["compound"]["mean"],"stddev":z["compound"]["stddev"],"z_score":zz("compound"),
  "change_pct":100*(cvc["compound_pct_of_reward_decisions"]-62.05)/62.05,
  "description":f"Compound rate {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} redelegate vs {cvc['claim_count']} claim), z={zz('compound'):+.2f}sigma - the first reading below 50% and a 12.6pp fall from last week's series high. None of the claims went to exchanges in the retail tier and one of 21 did in mid-tier, so this is yield being kept liquid, not sold, in a week that ran from about ${peak:.2f} to ${price:.2f}."},
 {"metric":"staked_ratio","current_value":M["sr"],"previous_value":M["sr_prev"],
  "method":"z_score","severity":"high","average_value":z["sr"]["mean"],"stddev":z["sr"]["stddev"],"z_score":zz("sr"),
  "change_pct":100*(M["sr"]-M["sr_prev"])/M["sr_prev"],
  "description":f"Staked ratio {100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.2f}pp), z={zz('sr'):+.2f}sigma, through the 46.80% branch in the first week of run #24's three-week test. Staked {M['staked_chg']:+,.0f} while delegation TVL rose {sk['delta_locked']:+,.0f}. The timing matches earlier unbonding queues maturing, and new unDelegations fell to {f(sk['undelegated_week'])}."},
 {"metric":"staked_egld","current_value":econ["staked"],"previous_value":prev["economics"]["staked_egld"],
  "method":"z_score","severity":"high","average_value":z["staked"]["mean"],"stddev":z["staked"]["stddev"],"z_score":zz("staked"),
  "change_pct":100*M["staked_chg"]/prev["economics"]["staked_egld"],
  "description":f"Staked EGLD {M['staked_chg']:+,.0f} to {f(econ['staked'])}, z={zz('staked'):+.2f}sigma, the largest weekly fall in the eight-run baseline. Residual against delegation {f(sk['residual'])}; no direct-node figure is extractable."},
 {"metric":"dex_volume_egld_24h","current_value":bid["dexvol_egld"],"previous_value":bid["prev_dexvol_egld"],
  "method":"rule_based","severity":"medium","change_pct":100*(bid["dexvol_egld"]-bid["prev_dexvol_egld"])/bid["prev_dexvol_egld"],
  "description":f"xExchange volume in EGLD {f(bid['prev_dexvol_egld'])} -> {f(bid['dexvol_egld'])}/day, {bid['wegld_usdc_share']:.1f}% on WEGLD/USDC, during a falling price. By the run #18 diagnostic that is an aggressive offer, not an absent bid. USD turnover {bid['turnover']:.2f}% (z={zz('turnover'):+.2f}); the like-for-like prior turnover ex the paused MEX pair was {bid['prev_turnover_ex_mex']:.2f}%."},
 {"metric":"egld_price_usd","current_value":price,"previous_value":M["prev_price"],
  "method":"rule_based","severity":"medium","change_pct":pc,
  "description":f"EGLD {pc:+.2f}% to ${price:.2f} with BTC {M['btc_wow']:+.2f}% and ETH {M['eth_wow']:+.2f}%, the third consecutive EGLD-specific week and the first down. The absolute z of {zz('price'):+.2f} is positive because the baseline mean (${z['price']['mean']:.2f}) is below the current price after four up-weeks, which is the run #16 under-flag case, so the move is scored rule-based. Intra-week the CoinGecko daily series peaked near ${peak:.2f}, so peak-to-snapshot was about {100*(price-peak)/peak:.0f}%."},
 {"metric":"otc_net_one_way_egld_7d","current_value":otc["net_one_way"],"previous_value":prev["otc_net_one_way_series"]["run24"],
  "method":"z_score","severity":"medium","average_value":z["otc_net"]["mean"],"stddev":z["otc_net"]["stddev"],"z_score":zz("otc_net"),
  "change_pct":100*(otc["net_one_way"]-prev["otc_net_one_way_series"]["run24"])/prev["otc_net_one_way_series"]["run24"],
  "description":f"Net one-way delivery {f(otc['net_one_way'])} EGLD, z={zz('otc_net'):+.2f}sigma, the second-largest week in tracking. On the new exchange-side scale that is {OB['net_one_way_share_of_spot_volume_pct']:.1f}% of CEX spot volume ({OB['previous_net_one_way_share_of_spot_volume_pct']:.1f}% last week). Aug 17 - Sep 14 netted as one window: {f(wave['net_one_way'])}."},
 {"metric":"otc_circularity_pct","current_value":otc["circ_pct"],"previous_value":65.7,
  "method":"rule_based","severity":"low",
  "description":f"Circularity {otc['circ_pct']:.0f}%, below the 63-80% band. Under the run #21/#22 rule that means a return leg landed whose feed sat in an earlier week. The four-week window confirms it with a {wave['overstate_pct']:.0f}% weekly-frame overstatement, small because the feed and drain largely overlap across four frames."},
 {"metric":"stablecoin_supply_combined","current_value":comb,"previous_value":combp,"method":"rule_based","severity":"low",
  "change_pct":comb_pct,
  "description":f"Combined USDC+USDT {comb_pct:+.2f}% - expansion, ending the three-week contraction and resolving run #24's promotion test against it. Inside the total USDT fell {abs(usdt['pct']):.2f}% (the largest move in its series) and USDC rose {usdc['pct']:+.2f}%."},
 {"metric":"total_delegators","current_value":sk["users"],"previous_value":sk["prev_users"],"method":"rule_based","severity":"low",
  "change_pct":100*sk["users_delta"]/sk["prev_users"],
  "description":f"Delegators {sk['users_delta']:+,} to {f(sk['users'])} on the locked>0 basis ({100*sk['users_delta']/sk['prev_users']:+.3f}%); {sk['gaining']} providers gained, {sk['losing']} lost. Inside the inertia base rate, though with the widest gain/loss imbalance in several weeks."},
]

R["trend_indicators"]={
 "accelerating_exchange_outflows":[
  {"exchange":"UPbit","trend":"down","cumulative_change_pct":ent("UPbit")["pct"],"weeks_in_trend":1,
   "interpretation":f"{ent('UPbit')['net_flow_egld']:+,.0f} while feeding {f(otc['upbit_feed'])} to its own desk. Tranche series 297,000 / 460,000 / 462,000 / {f(otc['upbit_feed'])}: four weeks above 290,000, sole net source of the four-week window at {f(V(wave['net_by_venue'],'UPbit'))}."},
  {"exchange":"Binance","trend":"up","cumulative_change_pct":17.3,"weeks_in_trend":2,
   "interpretation":f"Staking custody +{f(cust['delta'])} to {f(cust['balance'])}, a second week of refill (+372,434 then +{f(cust['delta'])}), all from the hot wallet. The hot wallet also sent {f(HOT['total_egld'])} to OTC feeders: the refill and the feed run together."},
  {"exchange":"Coinbase","trend":"down","cumulative_change_pct":-37.6,"weeks_in_trend":4,
   "interpretation":f"{ent('Coinbase')['net_flow_egld']:+,.0f} ({ent('Coinbase')['pct']:+.1f}%), a fourth consecutive fall. Outside every pipeline window; plain customer withdrawal."},
  {"exchange":"Gate.io","trend":"up","cumulative_change_pct":59.8,"weeks_in_trend":3,
   "interpretation":f"{ent('Gate.io')['net_flow_egld']:+,.0f} ({ent('Gate.io')['pct']:+.1f}%), a third week up, with +{f(V(otc['net_by_venue'],'Gate.io'))} of hub delivery. Gate.io is now a confirmed parent of the largest unattributed desk feeder ({f(V(fb0,'Gate.io'))} EGLD over the wave), so it runs inventory in both directions."},
  {"exchange":"Bitget","trend":"down","cumulative_change_pct":ent("Bitget")["pct"],"weeks_in_trend":1,
   "interpretation":f"{ent('Bitget')['net_flow_egld']:+,.0f} ({ent('Bitget')['pct']:+.1f}%), not a pipeline week for Bitget."}],
 "validator_movements":{"providers_joining":0,"providers_leaving":0,"net_provider_change":0,
  "notable_joiners":[],"notable_leavers":[]},
 "token_supply_events":[
  {"identifier":"HMEX-df6df7","name":"HMEX","event":"mint",
   "supply_previous":str(int(MEXE["hmex_prev_supply"])),"supply_current":str(int(MEXE["hmex_supply"])),
   "change_pct":ht["HMEX-df6df7"]["supply_pct"],
   "description":f"HMEX minted {ht['HMEX-df6df7']['supply_pct']:+.0f}%: MEX deposited into Hatom in the week the MEX/WEGLD pool was paused."},
  {"identifier":"USDT-f8c08c","name":"USDT","event":"burn",
   "supply_previous":str(int(usdt["prev"])),"supply_current":str(int(usdt["supply"])),"change_pct":usdt["pct"],
   "description":f"{f(usdt['prev']-usdt['supply'])} USDT redeemed ({usdt['pct']:+.2f}%), the largest weekly move in the tracked series."},
  {"identifier":"USDC-c76f1f","name":"WrappedUSDC","event":"mint",
   "supply_previous":str(int(usdc["prev"])),"supply_current":str(int(usdc["supply"])),"change_pct":usdc["pct"],
   "description":f"{f(usdc['supply']-usdc['prev'])} USDC minted ({usdc['pct']:+.2f}%), more than offsetting USDT; the combined dollar base expanded {comb_pct:+.2f}%."},
  {"identifier":"USH-111e09","name":"Hatom USH","event":"mint",
   "supply_previous":str(int(tk["lsd"]["USH-111e09"]["prev"])),"supply_current":str(int(tk["lsd"]["USH-111e09"]["supply"])),
   "change_pct":tk["lsd"]["USH-111e09"]["pct"],
   "description":f"USH {tk['lsd']['USH-111e09']['pct']:+.2f}%, a second consecutive mint, below the 5% threshold."},
  {"identifier":"HEGLD-d61095","name":"HEGLD","event":"burn",
   "supply_previous":None,"supply_current":None,"change_pct":ht["HEGLD-d61095"]["supply_pct"],
   "description":f"HEGLD supply {ht['HEGLD-d61095']['supply_pct']:+.2f}%: EGLD depositors withdrew from Hatom as EGLD fell. This is the behavioural leg the inverse rule should be read on; this week it moved with price, not against it."}],
 "consecutive_streaks":[
  {"metric":"otc_upbit_tranche_above_290k","direction":"up","weeks":4,"cumulative_change_pct":None,
   "interpretation":f"297,000 / 460,000 / 462,000 / {f(otc['upbit_feed'])}. Wave #4 confirmed; the programme is continuous."},
  {"metric":"binance_hot_to_otc_feeders_above_50k","direction":"up","weeks":3,"cumulative_change_pct":None,
   "interpretation":f"135,003 (run #23, feeders only) / 255,442 / {f(HOT['total_egld'])}. The run #24 watch named a third week above 50,000 as a permanent funding line, and this is that week."},
  {"metric":"otc_desk_inventory_egld","direction":"down","weeks":2,"cumulative_change_pct":-78.7,
   "interpretation":f"266,213 -> 96,114 -> {f(otc['desk_bal'])}. The desks are running on the current week's feed with almost nothing staged."},
  {"metric":"lsd_supply_segld","direction":"flat","weeks":8,"cumulative_change_pct":0.0,
   "interpretation":f"SEGLD {tk['lsd']['SEGLD-3ad2d0']['pct']:+.3f}%: eight flat weeks through a rally and its reversal."},
  {"metric":"total_delegators","direction":"flat","weeks":13,"cumulative_change_pct":-1.0,
   "interpretation":f"{sk['users_delta']:+,} to {f(sk['users'])}. Still the base rate."},
  {"metric":"provider_operator_fee_selling","direction":"flat","weeks":13,"cumulative_change_pct":0.0,
   "interpretation":"Thirteen consecutive runs with zero exchange destinations from sampled operator wallets."},
  {"metric":"identifiable_bid_absorbed_egld_7d","direction":"flat","weeks":5,"cumulative_change_pct":0.0,
   "interpretation":"Zero for a fifth week; retired instrument, kept as a dormancy marker."}],
 "regime_shifts":[
  {"metric":"xexchange_mex_venue","before_value":MEXE["prev_pair_tvl_usd"],"after_value":0.0,
   "description":"CANDIDATE, not promoted. The MEX/WEGLD pool is paused and MEX has no on-chain price. If the pair stays paused or delisted through run #26, MEX's price discovery has moved off-chain structurally. A resume would make it an incident. Registered as a pre-committed test."},
  {"metric":"reward_compound_pct","before_value":62.05,"after_value":cvc["compound_pct_of_reward_decisions"],
   "description":"CANDIDATE, not promoted. A one-week fall from the series high to the series low. It needs a second week under ~52% to count as a regime shift, per the two-week rule that correctly rejected the desk-inventory candidate in run #24."}]}

R["watch_list"]=[
 {"item":"XEXCHANGE MEX/WEGLD POOL PAUSED - LPs locked, MEX priced off-chain","weeks_on_list":1,
  "reason":f"Paused 2026-09-13 16:43 UTC by erd1ss6u80ruas2p... (the router owner), tx b0decfa361de... The pool holds {f(MEXE['pair_holds_mex']/1e9,1)}B MEX and {f(MEXE['pair_holds_wegld'])} WEGLD. 172 failed transactions in the week, 116 of them removeLiquidity. MEX {xx['mex_wow']:+.0f}% WoW on CoinGecko; HMEX supply {ht['HMEX-df6df7']['supply_pct']:+.0f}%. PRE-COMMITTED (mex-pair-resume): pair resumed within two weeks with MEX back under ~8.2e-07 (2x pre-pause) = an incident and a liquidity-freeze squeeze; resumed with MEX above that = repricing that stuck; still paused or delisted by run #27 = MEX price discovery has left the chain."},
 {"item":f"OTC PIPELINE - wave #4 running, desks near empty at {f(otc['desk_bal'])}","weeks_on_list":25,
  "reason":f"UPbit tranche {f(otc['upbit_feed'])}; net one-way {f(otc['net_one_way'])} ({OB['net_one_way_share_of_spot_volume_pct']:.1f}% of CEX spot volume); gross {f(otc['gross_out'])}; destinations Binance.com +{f(V(otc['net_by_venue'],'Binance.com'))}, Bybit +{f(V(otc['net_by_venue'],'Bybit'))}, Gate.io +{f(V(otc['net_by_venue'],'Gate.io'))}. Aug 17 - Sep 14 as one window: {f(wave['net_one_way'])}. PRE-COMMITTED (delivery-price-relevance): see the scoreboard."},
 {"item":"EXCHANGE ORDER BOOK - the first demand-side reading, now a baseline","weeks_on_list":1,
  "reason":f"Binance ±2% depth ${f(OB['binance']['depth_plus2_usd'])} ask / ${f(OB['binance']['depth_minus2_usd'])} bid; Bybit ${f(OB['bybit']['depth_plus2_usd'])} / ${f(OB['bybit']['depth_minus2_usd'])}; all venues ${f(OB['all_venues']['depth_plus2_usd'])} / ${f(OB['all_venues']['depth_minus2_usd'])} on ${f(OB['all_venues']['volume_24h_usd'])} 24h volume. 7d spot volume {f(OB['spot_volume_7d_egld']/1e6,2)}M EGLD. One snapshot, so no trend claim yet. Next week the model can say whether bids thinned under continued delivery."},
 {"item":"STAKED RATIO BELOW 46.80% - the security budget","weeks_on_list":3,
  "reason":f"{100*M['sr']:.2f}%, staked {M['staked_chg']:+,.0f}, delegation {sk['delta_locked']:+,.0f}, new unDelegations {f(sk['undelegated_week'])} (from 208,125). PRE-COMMITTED (staked-ratio-floor): below 46.30% by run #27 = exits are continuing beyond the matured queue; 46.30-46.80% = settled at a lower level; back above 46.80% = the drop was one matured queue."},
 {"item":"COMPOUND RATE BELOW 50%","weeks_on_list":6,
  "reason":f"{cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} vs {cvc['claim_count']}), from 62.05%. Claims held, not sold. PRE-COMMITTED (compound-regime): under 52% next week = stakers have switched to taking yield in cash; 55% or above = a one-week reaction to the price reversal; 52-55% = carry."},
 {"item":"BINANCE HOT WALLET - permanent OTC funding line","weeks_on_list":19,
  "reason":f"{f(HOT['total_egld'])} EGLD to desk feeders and routers, day-sliced and uncapped, the third week above 50,000. Custody +{f(cust['delta'])} to {f(cust['balance'])}. Kept for the scale of the flow, not as an open question."},
 {"item":"DELEGATION FEE ASYMMETRY - capital does not come back","weeks_on_list":3,
  "reason":f"egldstakingprovider {mv('egldstakingprovider','delta'):+,.0f} ({mv('egldstakingprovider','users_delta'):+d} users) and procryptostaking {mv('procryptostaking','delta'):+,.0f} in the second week after restoring fees. Measured over two weeks; graduating to methodology unless stake returns."},
 {"item":"PROVIDER TRANSITIONS - fourth-deregistration test, week 2 of 4","weeks_on_list":4,
  "reason":f"Zero locked>0 -> 0 transitions this week. ledgerbyfigment {dser.get('ledgerbyfigment',{}).get('users_delta',0):+d} to {f(dser.get('ledgerbyfigment',{}).get('users',0))}, p2p_org_ {dser.get('p2p_org_',{}).get('users_delta',0):+d}. Two identity renames (cslabsio -> chainstatelabs, kevinlallement -> dinovox) were caught before they posed as exits."},
 {"item":"EMERGING LSDs - the sweep lost two known protocols","weeks_on_list":3,
  "reason":f"JewelSwap stake +28% to 2,307 EGLD, VoxEGLD +6.5% to 2,018 with 128 holders. SALSA and VestaX still stake but were not surfaced by this week's sweep; the sweep will seed from the prior week's finds from run #26."},
 {"item":"WITHDRAWAL BREADTH - dispersal confirmed","weeks_on_list":7,
  "reason":f"{br['ex_n']} recipients / {f(br['ex_egld'])} EGLD ex-pipeline, top two {br['top_two_share_pct']:.0f}%. Run #24's concentration test resolved on the genuine-dispersal branch; the instrument stands as written."},
]

# ---------------- pre-committed tests --------------------------------------
prior={t["id"]:t for t in r24["pre_committed_tests"]}
tests=[t for t in r24["pre_committed_tests"] if t["status"]=="resolved"]
def resolve(tid,outcome,measured,resolution):
    t=dict(prior[tid]); t.update({"status":"resolved","outcome":outcome,"resolved_in_run":25,
        "measured_value":measured,"resolution":resolution}); return t

tests.append(resolve("wave4-restart","as_predicted",
  f"UPbit tranche {f(otc['upbit_feed'])} EGLD (bar: >200,000); net one-way {f(otc['net_one_way'])}; desks {f(otc['prev_desk'])} -> {f(otc['desk_bal'])}",
  f"The continuous-programme branch fires. The feed did not stop after wave #3's record delivery: a fourth consecutive tranche above 290,000 arrived and the desks delivered {f(otc['net_one_way'])} one-way on top of it. Waves #3 and #4 are best read as one programme, which netted as a single Aug 17 - Sep 14 window has delivered {f(wave['net_one_way'])} EGLD. The registered reading, that the supply overhang is structural, stands. The new exchange-side scale adds a qualification: that overhang is about 2% of weekly CEX spot volume."))

tests.append(resolve("unidentified-bid-persistence","inconclusive",
  f"EGLD ${price:.2f} at the snapshot, inside the $3.90-$4.20 band; the 'no new delivery' condition also failed ({f(otc['net_one_way'])} delivered); intra-week CoinGecko daily high about ${peak:.2f}",
  f"The middle branch fires and the test cannot resolve, for two reasons. The price landed in the undefined band, and the premise failed: the test assumed a quiet pipeline and got another 400,000 EGLD delivery. The question is replaced rather than carried. The exchange-side instrument that run #24 said the model lacked now exists, and it shows the 'invisible bid' was mostly the ordinary market. Last week's record delivery was {OB['previous_net_one_way_share_of_spot_volume_pct']:.1f}% of CEX spot volume. A new test on whether delivery moves price relative to BTC is registered below."))

tests.append(resolve("staked-ratio-downtrend","as_predicted",
  f"staked ratio {100*M['sr']:.2f}% in week 1 of 3 (bar: <46.80%); staked {M['staked_chg']:+,.0f}, delegation TVL {sk['delta_locked']:+,.0f}, residual {f(sk['residual'])}, new unDelegations {f(sk['undelegated_week'])} (from 208,125)",
  "The genuine-downtrend branch fires in its first week, and the security budget is at an archive low. Per the run #24 rule, here is the part of the registered reading the data contradicts. 'A rising price is not arresting it' has no test this week because the price fell. And the mechanism looks like matured exits from earlier weeks rather than a fresh wave: delegation TVL rose and new unDelegations fell by two-thirds. The level finding stands. Whether the downtrend continues is a separate question, registered below with a lower bar."))

tests.append(resolve("breadth-concentration","as_predicted",
  f"ex-pipeline {f(br['ex_egld'])} EGLD across {br['ex_n']} recipients, top two {br['top_two_share_pct']:.1f}% of value (bar: <50%)",
  "The genuine-dispersal branch fires on both terms: value above 300,000 and the top two under half of it. The instrument stands as written and no concentration-adjusted replacement is needed. The largest recipient is again the Binance hot-funded unlabelled whale, and at 17% of value it does not dominate."))

tests.append(resolve("dollar-base-fourth-contraction","against",
  f"combined USDC+USDT {comb_pct:+.2f}% (USDC {usdc['pct']:+.2f}%, USDT {usdt['pct']:+.2f}%)",
  "The expansion branch fires, against the claim. Three weeks of contraction was a redemption cycle, not a leading de-risking signal, and the dollar base returns to the DeFi section. Run #24 promoted it after three observations, and the promotion is withdrawn after one more, the same pattern run #24 itself withdrew on USH. Within the week the two stablecoins diverged sharply (USDT -12.8%, USDC +2.7%), so a combined series hides more than it shows."))

tests.append(resolve("jexchange-address-live","as_predicted",
  f"re-derived router {f(O['jex_router_7d'].get('JEXchange Router'))} transfers in 7 days (bar: >1,000); routers 2-5 at {', '.join(f(O['jex_router_7d'].get(f'JEXchange Router {i}')) for i in range(2,6))}; old aggregator 0",
  "Address correct: the four-run data gap was a stale identifier, not a halted protocol. The router set is now in the collector and known-addresses."))

t=dict(prior["fourth-deregistration"])
t.update({"status":"open","measured_value":f"week 2 of 4 on the TRANSITION basis (locked > 0 in the prior stored snapshot, 0 now): zero transitions. Two identity renames (cslabsio -> chainstatelabs, 177,587 EGLD; kevinlallement -> dinovox) would have scored as leavers on an identity-keyed join and were excluded.","resolution":None})
tests.append(t)

def new(tid,claim,threshold,branches,measured):
    return {"id":tid,"registered_in_run":25,"claim":claim,"threshold":threshold,"branches":branches,
            "status":"open","outcome":None,"resolved_in_run":None,"measured_value":measured,"resolution":None}
tests+=[
 new("mex-pair-resume",
  "The MEX/WEGLD pause is a structural move of MEX price discovery off-chain rather than a temporary incident.",
  "by run #27 (two weeks): pair still paused or delisted = structural; pair resumed with MEX under ~8.2e-07 (2x the pre-pause 4.08e-07) = an incident that caused a liquidity-freeze squeeze; pair resumed with MEX at or above 8.2e-07 = an incident whose repricing stuck",
  [{"condition":"still paused or delisted at run #27","reading":"structural: MEX price discovery has left the chain"},
   {"condition":"resumed and MEX < 8.2e-07","reading":"incident; the spike was a squeeze on frozen liquidity"},
   {"condition":"resumed and MEX >= 8.2e-07","reading":"incident; the repricing held after liquidity returned"}],
  f"paused 2026-09-13 16:43 UTC; MEX {xx['mex_price']:.2e} on CoinGecko ({xx['mex_wow']:+.0f}% WoW); HMEX supply {ht['HMEX-df6df7']['supply_pct']:+.0f}%"),
 new("delivery-price-relevance",
  "The OTC pipeline's delivery is large enough to move EGLD's price relative to the market, despite being ~2% of CEX spot volume.",
  "next week, with net one-way delivery above 300,000 EGLD: EGLD underperforming BTC by more than 5pp = delivery is price-relevant; EGLD within 5pp of BTC or outperforming = delivery is absorbed by ordinary turnover and is not a price signal on its own; delivery under 300,000 = not evaluable, re-register",
  [{"condition":"delivery > 300,000 and EGLD - BTC < -5pp","reading":"price-relevant supply"},
   {"condition":"delivery > 300,000 and EGLD - BTC >= -5pp","reading":"absorbed by turnover; not a standalone price signal"},
   {"condition":"delivery <= 300,000","reading":"not evaluable; re-register"}],
  f"this week: delivery {f(otc['net_one_way'])} ({OB['net_one_way_share_of_spot_volume_pct']:.1f}% of spot), EGLD - BTC = {pc-M['btc_wow']:+.2f}pp; last week delivery 536,459 (2.1%), EGLD - BTC = +16.61pp"),
 new("compound-regime",
  "The compound rate's fall below 50% is a switch to taking yield in cash, not a one-week reaction to the price reversal.",
  "next week's function-level compound rate below 52% = a regime switch; 55% or above = a one-week reaction; 52-55% = carry without concluding",
  [{"condition":"compound < 52%","reading":"regime switch to cash yield"},
   {"condition":"compound >= 55%","reading":"one-week reaction"},
   {"condition":"52% <= compound < 55%","reading":"carry"}],
  f"{cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} vs {cvc['claim_count']}), from 62.05%"),
 new("staked-ratio-floor",
  "Exits from staking continue beyond the queue that matured this week.",
  "staked ratio below 46.30% by run #27 = exits continuing; 46.30-46.80% = settled at a lower level; above 46.80% = this week's drop was one matured queue",
  [{"condition":"ratio < 46.30%","reading":"exits continuing"},
   {"condition":"46.30% <= ratio <= 46.80%","reading":"settled lower"},
   {"condition":"ratio > 46.80%","reading":"one matured queue"}],
  f"{100*M['sr']:.2f}%; new unDelegations {f(sk['undelegated_week'])} EGLD from {sk['undelegate_callers']} wallets"),
]
resolved=[t for t in tests if t.get("resolved_in_run")==25]
as_pred=sum(1 for t in resolved if t["outcome"]=="as_predicted")
hit=100*as_pred/len(resolved) if resolved else 0

R["pre_committed_tests"]=tests
R["meta_learning"]={
 "run_number":25,
 "endpoints_that_worked":status["ok"],
 "endpoints_that_failed":[
   "/mex/economics price = 0 and the MEX/WEGLD pair absent from /mex/pairs (HTTP 404 on the pair route) - a real state change, the pool was paused, not an API outage",
   "/tokens/WTAO-3ec9c0: HTTP 404 - known-bad control",
   "liquid-staking discovery sweep missed two known protocols (SALSA, VestaX); measured directly"],
 "api_quirks":[
   "A PAUSED xEXCHANGE PAIR DISAPPEARS FROM /mex/pairs AND ZEROES /mex/economics PRICE. The contract still exists, holds its reserves and accepts (failing) calls. The API layer does not say it is paused; it just stops returning it. Read state from the pair contract's own transactions (function=pause) rather than inferring it from absence.",
   "PROVIDER IDENTITIES CAN BE RENAMED. cslabsio -> chainstatelabs and kevinlallement -> dinovox this week. The run #22 identity-keyed join, which fixed an address/identity mismatch, reads a rename as a full-book leaver: 177,587 EGLD of phantom exit. The contract address is the stable key, and joins now fall back to it.",
   "CONCURRENT SCRIPTS SHARE ONE RATE LIMIT. Running delegator_behavior.py alongside the collector produced HTTP 429 on the OTC Distribution Wallet's wave-window scan (inbound returned 0, outbound cut at 400) and cut the reward sample to 4 of 8 providers without any error in the output file. paged_txs recorded the collector's failures as errors, so they were recoverable, but delegator_behavior.py has no equivalent guard. Run API-heavy scripts sequentially.",
   "THE LIQUID-STAKING SWEEP IS NOT MONOTONE. Its candidate tokens come from search and ranked-list pages, and LEGLD and VEGLD fell out of that set this week while their contracts still stake. A discovery pass must seed from last week's finds.",
   "COINGECKO /coins/{id}/tickers?depth=true RETURNS cost_to_move_up_usd / cost_to_move_down_usd PER VENUE (±2% depth). /market_chart?interval=daily total_volumes gives rolling 24h volume per day. Together they are the first exchange-side instrument in the pipeline: 7d spot volume and venue depth."],
 "data_gaps":[
   "The reason for the MEX/WEGLD pause is not on-chain. The model records the call, sender, reserves and failed calls.",
   "Withdraw amounts on provider contracts are not decoded (withdraw carries no amount argument), so the matured-queue attribution of the staked drop rests on timing and call counts.",
   f"{f(otc['unresolved_out'])} EGLD of desk outbound remains unattributed after two hops.",
   "Order-book depth is one snapshot with no prior; trend claims wait a week.",
   "Hatom UTK Money Market and OneDex Launchpad still fail bech32 validation (open since run #18)."],
 "key_findings":[
   f"The xExchange router owner paused the MEX/WEGLD pool on 2026-09-13 16:43 UTC. MEX rose ~7.5x on CoinGecko the next day, HMEX supply {ht['HMEX-df6df7']['supply_pct']:+.0f}%, and 172 transactions against the frozen pair failed.",
   f"Wave #4 confirmed: UPbit tranche {f(otc['upbit_feed'])}, net one-way {f(otc['net_one_way'])}, desks down to {f(otc['desk_bal'])}; {f(wave['net_one_way'])} EGLD one-way over Aug 17 - Sep 14.",
   f"The first exchange-side reading puts delivery at {OB['net_one_way_share_of_spot_volume_pct']:.1f}% of CEX spot volume; last week's 'invisible bid' was mostly ordinary turnover.",
   f"Staked ratio {100*M['sr']:.2f}%, below 46.80% in week one of the test, while new unDelegations fell by two-thirds.",
   f"Compound rate {cvc['compound_pct_of_reward_decisions']:.2f}%, first reading below 50%; claims were held, not sold.",
   f"The largest unattributed desk feeder is Bybit ({f(V(fb0,'Bybit'))}) and Gate.io ({f(V(fb0,'Gate.io'))}), not a fifth venue.",
   f"The dollar-base promotion is withdrawn: combined stablecoins {comb_pct:+.2f}%."],
 "action_items_from_previous":len(r24["meta_learning"]["recommendations_for_next_run"]),
 "action_items_completed_detail":[
   f"RESOLVE WAVE #4 - resolved as predicted: UPbit tranche {f(otc['upbit_feed'])}, the programme is continuous.",
   f"BUILD OR SOURCE AN EXCHANGE-SIDE DEMAND INSTRUMENT - done, crude and third-party: CoinGecko per-venue ±2% depth and 7d spot volume, published in the demand-instruments section as the exchange order book. It reframed last week's headline in its first run.",
   f"QUERY THE BINANCE HOT WALLET BY DAY - done in the main pass: 7 day-slices x 3 wallets, 772 outbound txs, zero capped; hot-to-pipeline {f(HOT['total_egld'])}.",
   "ADD A RECENCY QUALIFIER TO THE DEREGISTRATION DETECTOR - done: transitions from locked > 0 in the prior stored snapshot, zero this week. Building it surfaced the identity-rename trap.",
   f"ATTRIBUTE THE UNATTRIBUTED FEEDERS - done: two-hop back-trace of the 8 largest unlabelled feeders; the 196,492/214,978 EGLD feeder resolves to Bybit and Gate.io.",
   "RE-QUERY THE JEXCHANGE ROUTER AND PROMOTE IT - done: five routers in the collector, 9,968 transfers/7d on the main one, test resolved as predicted.",
   "MEASURE WHETHER THE DESK-EMPTY STATE COINCIDES WITH A RETRACEMENT - done: desks near empty and EGLD -7.6% after a ~$5.17 intra-week peak, but delivery did not stop, so the pairing is not clean; replaced by the delivery-price-relevance test.",
   "KEEP THE EMERGING-LSD SWEEP WITH HOLDERS - done, and it exposed that the sweep drops known protocols; holders recorded (VoxEGLD 128, LEGLD 378, VEGLD 435, JWLEGLD 552).",
   f"CHECK THE FEE-REVERSED PROVIDERS - done: second week of losses ({mv('egldstakingprovider','delta'):+,.0f} and {mv('procryptostaking','delta'):+,.0f}); the asymmetry is measured."],
 "methodology_changes":[
   "JOIN PROVIDERS ON THE CONTRACT ADDRESS. Identities are mutable; a rename posed as a 177,587 EGLD exit.",
   "READ VENUE STATE FROM THE CONTRACT, NOT FROM API ABSENCE. A paused pair vanishes from /mex/pairs; the pause call is on the pair's own transaction list.",
   "PUT PIPELINE FLOWS IN MARKET SCALE. Report net one-way delivery as a share of 7d CEX spot volume alongside venue ±2% depth.",
   "EXCLUDE AN UNPRICED H-TOKEN FROM LENDING TVL WHEN ITS UNDERLYING HAS NO ON-CHAIN PRICE. HMEX alone added +44pp to Hatom Lending in EGLD terms.",
   "READ THE BILATERAL INVERSE RULE ON THE HEGLD LEG. Dollar- and BTC-denominated collateral rises in EGLD terms whenever EGLD falls; only EGLD-market supply tests depositor behaviour.",
   "RUN API-HEAVY SCRIPTS SEQUENTIALLY; SEED DISCOVERY SWEEPS FROM LAST WEEK."],
 "new_addresses_discovered_detail":[
   {"address":"erd1qqqqqqqqqqqqqpgqa0fsfshnff4n76jhcye6k7uvd7qacsq42jpsp6shh2","label":"xExchange: MEX/WEGLD pair (PAUSED 2026-09-13)",
    "evidence":"pause call from the router owner at 16:43 UTC; 191B MEX + 141,281 WEGLD reserves; 172 failed txs"},
   {"address":"erd1ss6u80ruas2phpmr82r42xnkd6rxy40g9jl69frppl4qez9w2jpsqj8x97","label":"xExchange: router owner / admin wallet",
    "evidence":"owner of the router contract that owns the pair; sent the pause"},
   {"address":"erd1ytpenkzjucgq7mxu4l6u8v72vfxxlux2237925glajhs4dj3u8asue9arn","label":"Bybit/Gate.io->OTC Desk Feeder (resolved run #25)",
    "evidence":f"two-hop back-trace: {f(V(fb0,'Bybit'))} EGLD from Bybit and {f(V(fb0,'Gate.io'))} from Gate.io over Aug 17 - Sep 14"}],
 "action_items_completed":9,
 "new_addresses_discovered":3,
 "most_valuable_insight":(
   f"Putting the pipeline in market scale. For five weeks the report has measured supply to the EGLD and treated the week's price as its counterpart. "
   f"The first exchange-side reading shows the desks' record 536,459 EGLD delivery was {OB['previous_net_one_way_share_of_spot_volume_pct']:.1f}% of that week's CEX spot volume, and this week's {f(otc['net_one_way'])} was {OB['net_one_way_share_of_spot_volume_pct']:.1f}%. "
   "The 'invisible bid' of run #24 was mostly ordinary turnover. The pipeline still matters, because it is persistent, one-directional and aimed at two venues, but its weekly total cannot be read against the weekly price as if nothing else traded. The MEX pause is the bigger event; this is the bigger correction to the model."),
 "top_recommendation":(
   "RE-READ THE MEX/WEGLD PAIR STATE FIRST NEXT RUN. The pause is registered as a two-week test. Query the pair's transactions for resume/unpause/setState calls and removeLiquidity successes, track HMEX supply and the MEX price on both CoinGecko and /tokens, and check whether any other xExchange pair received a pause in the same window."),
 "recommendations_for_next_run":[
   "RESOLVE THE MEX PAIR STATE. Query erd1qqqqqqqqqqqqqpgqa0fs...jpsp6shh2 for resume/setState calls and successful removeLiquidity; scan the router owner erd1ss6u80ruas2p... for pause calls on OTHER pairs this window; track HMEX supply and MEX on CoinGecko vs /tokens.",
   "BUILD THE ORDER-BOOK SERIES. Store this week's per-venue ±2% depth and 7d spot volume in previous.json and report the WoW change for Binance and Bybit, the two delivery venues.",
   "SEED THE LIQUID-STAKING SWEEP FROM LAST WEEK'S PROTOCOLS so a known LSD cannot drop out of the table.",
   "ADD A 429 GUARD TO delegator_behavior.py (error-vs-empty distinction plus exponential backoff) and run it after the collector, never alongside.",
   "DECODE WITHDRAW AMOUNTS for the staked-ratio attribution: the SC results of withdraw calls carry the EGLD returned, via /transactions/{hash} or /transfers. That turns the matured-queue timing argument into a measurement.",
   "RESOLVE THE COMPOUND-REGIME AND DELIVERY-PRICE-RELEVANCE TESTS - both are one-week tests with partitioned branches.",
   "JOIN PROVIDERS ON ADDRESS IN THE COLLECTOR ITSELF, not just in the assembler, and log identity renames as an event list."],
 "dashboard_feature_suggestions":[
  {"title":"Contract-state event timeline - the MEX/WEGLD pause against price and deposits",
   "motivation":"This run's headline is a venue-level state change: a pool paused at a known timestamp, followed within a day by a 7.5x MEX move, an 8x HMEX mint and 172 failed calls. The dashboard has no way to show an event with a timestamp next to the series it moved, so the causal ordering (pause at 16:43, last swap at 16:39, price spike the next day) is only in prose.",
   "suggested_visualization":"a time-axis strip with an annotated vertical marker for the pause tx, the MEX daily price line on one axis and HMEX supply on another, plus a small panel of the pair's reserves and failed-call count",
   "data_already_available":True,
   "data_source":"token_activity.xexchange.mex_pair_event (new field this run) plus a CoinGecko MEX market_chart stored in the collected snapshot",
   "priority":"high"},
  {"title":"Pipeline in market scale - delivery as a share of CEX turnover and depth",
   "motivation":"The first exchange-side reading changed how the OTC pipeline should be read: a record weekly delivery is ~2% of spot volume, and weekly net delivery into Binance+Bybit is about 10x their ±2% bid depth. The current OTC chart shows delivery in absolute EGLD only, which invites reading each bar against the week's price.",
   "suggested_visualization":"a second y-axis or a small-multiple under the OTC bars plotting net one-way as % of 7d spot volume, plus a per-venue depth tile row (Binance, Bybit, Gate) with bid vs ask ±2% bars",
   "data_already_available":True,
   "data_source":"whale_intelligence.demand_instruments.exchange_orderbook (new field this run); history starts run #25",
   "priority":"medium"}],
 "dashboard_suggestions_followup":[
  {"title":"Feed-side attribution - who fills the desks, not just who they deliver to","status":"pending",
   "note":"Data is now published (otc_pipeline.feed_by_parent_venue and otc_pipeline.feeder_backtrace), so the blocker named in run #24 is gone. Not built this run; the finding that the feed side is the same four venues as the delivery side makes the paired-bar version the right one."},
  {"title":"Demand-instrument scorecard - show the model's blind spot as a row of empties","status":"pending",
   "note":"Still worth building, but its framing changes: one tile (exchange order book) now has a live reading, so the strip is no longer a row of empties. It should wait a week so the order-book tile has a WoW direction."},
  {"title":"Provider lifecycle strip","status":"deprioritized",
   "note":"Zero transitions for two weeks and the cohort is mostly archaeology. Identity renames are the more useful lifecycle event now; revisit if the fourth-deregistration test fires."},
  {"title":"Errata linkage from the withdrawn claim to its replacement","status":"pending",
   "note":"Two claims are withdrawn this run (the dollar-base promotion and the fifth-venue guess), which strengthens the case slightly. Still queued behind the feed-side panel."}],
 "withdrawn_claims":[
  {"claim":"The on-chain wrapped-dollar base is a de-risking instrument, promoted after three consecutive contractions.",
   "asserted_in_runs":[24],"withdrawn_in_run":25,
   "reason":f"Combined USDC+USDT expanded {comb_pct:+.2f}% the following week, the branch run #24 itself registered as a demotion.",
   "replacement":"The three-week contraction was a redemption cycle. USDC and USDT are reported separately in the DeFi section, since they diverged by 15pp this week."},
  {"claim":"The 196,492 EGLD desk feeder with no parent venue probably represents a fifth feeding venue.",
   "asserted_in_runs":[24],"withdrawn_in_run":25,
   "reason":f"Two hops back it received {f(V(fb0,'Bybit'))} EGLD from Bybit and {f(V(fb0,'Gate.io'))} from Gate.io over the wave.",
   "replacement":"The feed side is UPbit, Binance, Bybit and Gate.io - the same four venues the desks deliver into."},
  {"claim":"A record OTC delivery absorbed into a +17% price rise means demand the model cannot see.",
   "asserted_in_runs":[24],"withdrawn_in_run":25,
   "reason":f"The first exchange-side measurement puts that delivery at {OB['previous_net_one_way_share_of_spot_volume_pct']:.1f}% of the week's CEX spot volume.",
   "replacement":"Most of the absorbing bid was ordinary market turnover. The open question is whether a persistent ~2% net offer moves price relative to BTC, registered as delivery-price-relevance."}],
}

rep={}
rep.update(p1); rep.update(p2)
rep["anomalies"]=R["anomalies"]; rep["trend_indicators"]=R["trend_indicators"]; rep["watch_list"]=R["watch_list"]
rep["meta_learning"]=R["meta_learning"]; rep["pre_committed_tests"]=R["pre_committed_tests"]
order=["metadata","executive_summary","network_health","whale_intelligence","staking_intelligence",
       "token_activity","defi_activity","anomalies","trend_indicators","watch_list","meta_learning","pre_committed_tests"]
rep={k:rep[k] for k in order}
json.dump(rep,open(f"{REPO}/reports/{RD}.json","w"),indent=1,default=str)
print("report written; keys:",list(rep.keys()))
print(f"tests: {len(tests)} total, {len(resolved)} resolved this run, {as_pred} as_predicted ({hit:.1f}%), {sum(1 for t in tests if t['status']=='open')} open")
