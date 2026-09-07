#!/usr/bin/env python3
"""Run #24 stage 4: anomalies, trend indicators, watch list -> /tmp/run24w/part3.json"""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-09-07"
O=json.load(open("/tmp/run24w/derived.json"))
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
beh=json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
M=O["macro"]; otc=O["otc"]; wave=otc["wave"]; ex=O["exch"]
cust=O["custody"]; bid=O["bid"]; br=O["breadth"]; sk=O["staking"]; tk=O["tokens"]
xx=O["xexchange"]; df=O["defi"]; z=O["z"]; ub=O["unbond"]; absb=O["absorbers"]; p2p=O["p2p"]
zsc=O["zero_stake_cohort"]; em=O["emerging_lsd"]; jex=O["jex"]
price=M["price"]; pc=M["price_chg"]; econ=D["economics"]
cvc=beh["aggregates"]["compound_vs_claim_at_function_level"]
HOT=O["hot_to_pipe"]; FEED=O["feeders_in"]
def f(x,d=0):
    try: return f"{x:,.{d}f}"
    except: return str(x)
def zz(k): return z[k].get("z")
def V(d_,k): return d_.get(k,0.0)
dser={d["identity"]:d for d in O["dereg_series"]}
R={}

R["anomalies"]=[
 {"metric":"otc_net_one_way_egld_7d","current_value":otc["net_one_way"],
  "previous_value":prev["otc_net_one_way_series"]["run23"],"method":"z_score","severity":"critical",
  "average_value":z["otc_net"]["mean"],"stddev":z["otc_net"]["stddev"],"z_score":zz("otc_net"),
  "change_pct":100*(otc["net_one_way"]-prev["otc_net_one_way_series"]["run23"])/prev["otc_net_one_way_series"]["run23"],
  "description":f"The OTC desks delivered {f(otc['net_one_way'])} EGLD one-way in seven days, z={zz('otc_net'):+.2f}sigma - the largest weekly distribution ever measured and 31% past the previous record, the re-netted run #17 peak of 409,680. Netted feed-to-drain across the whole of wave #3 (Aug 17 - Sep 7) the figure is {f(wave['net_one_way'])} EGLD, more than double the largest wave previously tracked. Destinations two hops out: Binance.com +{f(V(otc['net_by_venue'],'Binance.com'))}, Bybit +{f(V(otc['net_by_venue'],'Bybit'))}, Gate.io +{f(V(otc['net_by_venue'],'Gate.io'))}. All exchange deposit paths."},
 {"metric":"otc_desk_inventory_egld","current_value":otc["desk_bal"],
  "previous_value":otc["prev_desk"],"method":"rule_based","severity":"critical",
  "change_pct":100*otc["desk_delta"]/otc["prev_desk"],
  "description":f"Desk inventory {f(otc['prev_desk'])} -> {f(otc['desk_bal'])} EGLD ({100*otc['desk_delta']/otc['prev_desk']:+.0f}%), the largest single-week drain in tracking, and it resolves run #23's central question. The record 266,213 was staged supply, not a new level: the desks emptied it into order books and ended the week holding less than they have since run #21. The inventory series across the wave reads 60,565 -> 109,857 -> 266,213 -> {f(otc['desk_bal'])} - three weeks of staging and one of delivery."},
 {"metric":"egld_price_usd","current_value":price,"previous_value":M["prev_price"],
  "method":"z_score","severity":"high",
  "average_value":z["price"]["mean"],"stddev":z["price"]["stddev"],"z_score":zz("price"),
  "change_pct":pc,
  "description":f"EGLD ${price:.2f}, {pc:+.2f}%, z={zz('price'):+.2f}sigma - the largest weekly gain in the archive and the second consecutive EGLD-specific move under the run #16 rule, with BTC {M['btc_wow']:+.2f}% and ETH {M['eth_wow']:+.2f}% both effectively unchanged. What makes it an anomaly rather than a rally note is the coincidence: this is also the week the OTC pipeline delivered a record {f(otc['net_one_way'])} EGLD to order books. Price rose 17% THROUGH the largest supply delivery ever measured, and no tracked demand instrument shows the counterparty."},
 {"metric":"binance_hot_to_otc_feeders_egld","current_value":HOT["total_egld"],
  "previous_value":135003.0,"method":"rule_based","severity":"high",
  "change_pct":100*(HOT["total_egld"]-135003.0)/135003.0,
  "description":f"The Binance.com hot wallet sent {f(HOT['total_egld'])} EGLD to known OTC desk feeders and routers over the full seven days - five times the 50,000 flow threshold run #23 registered after its balance-based predecessor failed, and equal to {100*HOT['total_egld']/otc['net_one_way']:.0f}% of everything the desks delivered one-way. The main collector pass measured only {f(HOT.get('main_pass_egld',0))} because this wallet fills a 1,000-transaction budget in 4.4 days; the window was re-queried in per-calendar-day slices. Binance-labelled feeders delivered {f(FEED.get('Binance',0))} EGLD into the desks. In the same week Binance Staking custody REVERSED its two-week drawdown, +{f(cust['delta'])} to {f(cust['balance'])} on 900,000 out and 1,272,434 back. Funding the pipeline and refilling custody happened simultaneously, which is why only the flow trace answers this question."},
 {"metric":"staked_ratio","current_value":M["sr"],"previous_value":M["sr_prev"],
  "method":"z_score","severity":"high",
  "average_value":z["sr"]["mean"],"stddev":z["sr"]["stddev"],"z_score":zz("sr"),
  "change_pct":100*(M["sr"]-M["sr_prev"])/M["sr_prev"],
  "description":f"The staked ratio fell {100*(M['sr']-M['sr_prev']):+.3f}pp to {100*M['sr']:.2f}%, z={zz('sr'):+.2f}sigma and the lowest reading in the archive. Total staked {M['staked_chg']:+,.0f} EGLD against {f(econ['totalSupply']-prev['economics']['total_supply'])} of emission, delegation TVL {f(sk['delta_locked'])}, and {f(sk['undelegated_week'])} EGLD entering the unbonding queue. In a +17% price week the security budget shrank - participation is moving the opposite way from the price for the fifth consecutive week."},
 {"metric":"zero_stake_provider_cohort","current_value":zsc["contracts"],"previous_value":3,
  "method":"rule_based","severity":"high",
  "description":f"{zsc['contracts']} provider contracts hold zero stake with {f(zsc['attached_delegator_records'])} delegator records attached - {zsc['share_of_all_delegator_records_pct']:.1f}% of every delegator record on the network, against the three cases run #23 reported. Running the widened detector backwards over all {zsc['archive_snapshots']} stored snapshots shows only four emptied inside the archive; the rest predate tracking. Only ONE of the {zsc['contracts']} saw any inbound transaction this week (ledgerbyfigment), so most of those records are stale rather than stranded. The operational consequence is a reporting rule: quote the delegator base on the locked>0 basis, or a storage change made last run prints a fake -28,141 collapse."},
 {"metric":"unbonding_queue_undelegated_egld_7d","current_value":sk["undelegated_week"],
  "previous_value":151443.0,"method":"rule_based","severity":"medium",
  "change_pct":100*(sk["undelegated_week"]-151443.0)/151443.0,
  "description":f"{f(sk['undelegated_week'])} EGLD unDelegated by {sk['undelegate_callers']} distinct wallets across all {sk['providers_scanned']} provider contracts, against 151,443 by 300 last week. Part of the increase is coverage: run #23 recommended re-paging the contracts that filled the 6-page budget, and {len(O['scan_depth']['deep_scanned'])} of them were re-scanned at 30 pages this run. Measured pending unbonding {f(sk['pool_total'])} EGLD, {f(sk['claimable_now'])} of it already claimable. This is the first scan deep enough to call a comparable baseline."},
 {"metric":"reward_compound_pct","current_value":cvc["compound_pct_of_reward_decisions"],
  "previous_value":57.51,"method":"z_score","severity":"medium",
  "average_value":z["compound"]["mean"],"stddev":z["compound"]["stddev"],"z_score":zz("compound"),
  "change_pct":100*(cvc["compound_pct_of_reward_decisions"]-57.51)/57.51,
  "description":f"Compound rate {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} redelegate vs {cvc['claim_count']} claim), z={zz('compound'):+.2f}sigma - a sharp reversal after four consecutive declines and the highest of eleven readings. Run #23's pre-committed test used contiguous branches this time and resolves cleanly on the 'stabilised' side: the four-week decline was a level shift, not a drift toward monetising yield. Notably the reversal came in the week of the largest OTC delivery on record - the people already staking compounded harder while the supply arrived from elsewhere."},
 {"metric":"stablecoin_supply_combined","current_value":tk["stable"]["USDC-c76f1f"]["supply"]+tk["stable"]["USDT-f8c08c"]["supply"],
  "previous_value":tk["stable"]["USDC-c76f1f"]["prev"]+tk["stable"]["USDT-f8c08c"]["prev"],
  "method":"rule_based","severity":"medium",
  "change_pct":100*((tk["stable"]["USDC-c76f1f"]["supply"]+tk["stable"]["USDT-f8c08c"]["supply"])-(tk["stable"]["USDC-c76f1f"]["prev"]+tk["stable"]["USDT-f8c08c"]["prev"]))/(tk["stable"]["USDC-c76f1f"]["prev"]+tk["stable"]["USDT-f8c08c"]["prev"]),
  "description":f"THIRD CONSECUTIVE WEEK OF COMBINED CONTRACTION, which is the promotion condition run #23 registered. USDC {tk['stable']['USDC-c76f1f']['pct']:+.2f}% to {f(tk['stable']['USDC-c76f1f']['supply'])} and USDT {tk['stable']['USDT-f8c08c']['pct']:+.2f}% to {f(tk['stable']['USDT-f8c08c']['supply'])} - roughly $140K of wrapped dollars redeemed in a {pc:+.1f}% week, and about $220K over the three weeks. The on-chain dollar base is now reported as a de-risking instrument alongside USH rather than as plumbing noise."},
 {"metric":"ush_supply","current_value":tk["lsd"]["USH-111e09"]["supply"],
  "previous_value":tk["lsd"]["USH-111e09"]["prev"],"method":"rule_based","severity":"medium",
  "change_pct":tk["lsd"]["USH-111e09"]["pct"],
  "description":f"USH MINTED {tk['lsd']['USH-111e09']['pct']:+.2f}% ({f(tk['lsd']['USH-111e09']['supply']-tk['lsd']['USH-111e09']['prev'])} tokens) to {f(tk['lsd']['USH-111e09']['supply'])}, reversing two consecutive burns and taking the base above where the sequence began. The run #16 framing is restored: a large enough up-week brings CDP leverage back. Reading the two weeks of burning as 'a behaviour' was premature - it was debt repayment through a moderate rally, and this week borrowers levered into a big one. USH is the only tracked on-chain instrument that moved the way a rally predicts."},
 {"metric":"dex_volume_egld_24h","current_value":bid["dexvol_egld"],
  "previous_value":bid["prev_dexvol_egld"],"method":"rule_based","severity":"medium",
  "change_pct":100*(bid["dexvol_egld"]-bid["prev_dexvol_egld"])/bid["prev_dexvol_egld"],
  "description":f"EGLD-denominated DEX volume {f(bid['prev_dexvol_egld'])} -> {f(bid['dexvol_egld'])} per day ({100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}%), below the 60,000 branch run #23 pre-registered. That resolves the turnover question against the constructive reading: the USD ratio ({bid['prev_turnover']:.2f}% -> {bid['turnover']:.2f}%) has been tracking price, and the venue processed less EGLD in the biggest up-week of the year than it did the week before. The series is reported in EGLD from here."},
 {"metric":"withdrawal_breadth_ex_pipeline_egld","current_value":br["ex_egld"],
  "previous_value":400112.54,"method":"rule_based","severity":"medium",
  "change_pct":100*(br["ex_egld"]-400112.54)/400112.54,
  "description":f"{br['ex_n']} distinct non-pipeline addresses took {f(br['ex_egld'])} EGLD off exchanges (50 and 400,113 last week), clearing the pre-registered bar of 40 recipients and 300,000 EGLD, with no page-cap terminations. Read with the caveat the test could not pre-specify: two recipients account for {100*(br['top'][0]['egld']+br['top'][1]['egld'])/br['ex_egld']:.0f}% of the value, and the second of them is the wallet that also received 68,732 EGLD directly from the Binance hot wallet. The count broadened; the value did not disperse."},
 {"metric":"hatom_lending_inverse_response_ratio","current_value":df["inverse_ratio"],
  "previous_value":0.69,"method":"rule_based","severity":"low",
  "description":f"BILATERAL INVERSE RULE, fifth up-week confirmation: price {pc:+.2f}%, Hatom Lending EGLD-denominated TVL {df['hatom_lending_egld_pct']:+.2f}%, response ratio {df['inverse_ratio']:.2f}. The up-week series is 0.49 / 0.72 / 0.28 / 0.69 / {df['inverse_ratio']:.2f} - a stable band around 0.5 with one weak outlier. The rule is now as well-supported as anything in the model and the capacity-exhaustion watch stays closed."},
 {"metric":"otc_pipeline_throughput_egld_7d","current_value":otc["gross_out"],
  "previous_value":prev["otc_throughput_series"]["run23"],"method":"z_score","severity":"low",
  "average_value":z["otc"]["mean"],"stddev":z["otc"]["stddev"],"z_score":zz("otc"),
  "change_pct":100*(otc["gross_out"]-prev["otc_throughput_series"]["run23"])/prev["otc_throughput_series"]["run23"],
  "description":f"Gross desk throughput {f(otc['gross_out'])} EGLD out against {f(otc['gross_in'])} in, z={zz('otc'):+.2f}sigma - a record on the gross basis too, past run #17's 1,284,688, at {otc['circ_pct']:.0f}% circularity (inside the historical 63-80% band, so no straddle warning this week). Reported at low severity because gross is pipeline ACTIVITY: it counts every leg including the {f(otc['circular'])} EGLD that round-trips. The net figure carries the finding."},
 {"metric":"exchange_net_flow_egld","current_value":ex["net"],
  "previous_value":-101744.0,"method":"z_score","severity":"low",
  "average_value":z["exflow"]["mean"],"stddev":z["exflow"]["stddev"],"z_score":zz("exflow"),
  "description":f"Net exchange flow {ex['net']:+,.0f} EGLD, z={zz('exflow'):+.2f}sigma. Per the run #15 rule it decomposes before it is labelled: Binance {next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Binance'),0):+,.0f} is internal plumbing around a 900,000 custody transfer, UPbit {next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='UPbit'),0):+,.0f} is a venue that fed {f(otc['upbit_feed'])} to its own desk and took {f(V(otc['out_by_venue'],'UPbit'))} back, and Bybit {next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Bybit'),0):+,.0f} fell while the hub delivered +{f(V(otc['net_by_venue'],'Bybit'))} into it. At a pipeline gross of {f(otc['gross_out'])} the balance channel is noise."},
 {"metric":"total_delegators","current_value":sk["users"],"previous_value":sk["prev_users"],
  "method":"rule_based","severity":"low",
  "change_pct":100*sk["users_delta"]/sk["prev_users"],
  "description":f"Delegator count {sk['users_delta']:+,} to {f(sk['users'])} ({100*sk['users_delta']/sk['prev_users']:+.3f}%) on the locked>0 basis. Reported rule_based rather than by z-score because the baseline's standard deviation is tiny relative to the base. An eleventh consecutive flat week, this one through a +17% price move, the largest OTC delivery on record and a fee reversal at two providers - none of which moved the number."},
]

R["trend_indicators"]={
 "accelerating_exchange_outflows":[
  {"exchange":"UPbit","trend":"up","cumulative_change_pct":12.1,"weeks_in_trend":1,
   "interpretation":f"UPbit's balance ROSE {next((w['change_egld'] for w in ex['per_wallet'] if 'UPbit' in w['exchange']),0):+,.0f} to {f(next((w['current'] for w in ex['per_wallet'] if 'UPbit' in w['exchange']),0))} while it fed {f(otc['upbit_feed'])} EGLD to its own desk - because {f(V(otc['out_by_venue'],'UPbit'))} came back from the desks in the same window. It is still the pipeline's sole net source at {f(V(otc['net_by_venue'],'UPbit'))}. Tranche series 14,000 / 297,000 / 460,000 / {f(otc['upbit_feed'])}: the feed has plateaued at roughly 460,000 a week for three weeks."},
  {"exchange":"Binance","trend":"up","cumulative_change_pct":12.5,"weeks_in_trend":1,
   "interpretation":f"Staking custody +{f(cust['delta'])} to {f(cust['balance'])}, REVERSING two weeks of drawdown (-497K), while the hot complex fell {f(cust['hot_entity_balance']-cust['hot_entity_previous'])} and the hot wallet sent {f(HOT['total_egld'])} into OTC feeders and routers. The two-week 'custody is being drawn down to fund distribution' trend is broken; the funding continued anyway, out of a custody balance that grew."},
  {"exchange":"Bybit","trend":"down","cumulative_change_pct":-23.7,"weeks_in_trend":1,
   "interpretation":f"{next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Bybit'),0):+,.0f}, the largest balance fall of the week, and it breaks a three-week build. Bybit is on both legs of the pipeline at scale - it received {f(V(otc['out_by_venue'],'Bybit'))} from the desks and fed {f(V(otc['in_by_venue'],'Bybit'))} back - so a falling balance against +{f(V(otc['net_by_venue'],'Bybit'))} of net delivery means customers took more off the venue than the desks put on it."},
  {"exchange":"Coinbase","trend":"down","cumulative_change_pct":-29.3,"weeks_in_trend":3,
   "interpretation":f"{next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Coinbase'),0):+,.0f} across {next((e2['wallets_count'] for e2 in ex['entity'] if e2['entity']=='Coinbase'),0)} wallets, a third consecutive fall, cumulatively about -29% over the three. Coinbase appears nowhere in the OTC pipeline in any tracked window, so this is ordinary customer withdrawal - the cleanest such series on the venue list."},
  {"exchange":"Gate.io","trend":"up","cumulative_change_pct":27.8,"weeks_in_trend":2,
   "interpretation":f"+{f(next((e2['net_flow_egld'] for e2 in ex['entity'] if e2['entity']=='Gate.io'),0))} ({next((e2['pct'] for e2 in ex['entity'] if e2['entity']=='Gate.io'),0):+.1f}%) with +{f(V(otc['net_by_venue'],'Gate.io'))} of hub delivery into it. The only venue where the balance and the pipeline moved the same way, so the desk delivery is still sitting on the venue rather than having been absorbed."}],
 "validator_movements":{
  "providers_joining":0,"providers_leaving":0,"net_provider_change":0,
  "notable_joiners":[],
  "notable_leavers":[]},
 "token_supply_events":[
  {"identifier":"USH-111e09","name":"Hatom USH","event":"mint",
   "supply_previous":str(int(tk["lsd"]["USH-111e09"]["prev"])),
   "supply_current":str(int(tk["lsd"]["USH-111e09"]["supply"])),
   "change_pct":tk["lsd"]["USH-111e09"]["pct"],
   "description":f"{f(tk['lsd']['USH-111e09']['supply']-tk['lsd']['USH-111e09']['prev'])} USH minted ({tk['lsd']['USH-111e09']['pct']:+.2f}%), reversing two consecutive burns. CDP leverage returning into a +17% week - the run #16 pattern, and the only on-chain instrument that responded to the price the way a rally predicts."},
  {"identifier":"USDC-c76f1f","name":"WrappedUSDC","event":"burn",
   "supply_previous":str(int(tk["stable"]["USDC-c76f1f"]["prev"])),
   "supply_current":str(int(tk["stable"]["USDC-c76f1f"]["supply"])),
   "change_pct":tk["stable"]["USDC-c76f1f"]["pct"],
   "description":f"{f(abs(tk['stable']['USDC-c76f1f']['supply']-tk['stable']['USDC-c76f1f']['prev']))} USDC redeemed ({tk['stable']['USDC-c76f1f']['pct']:+.2f}%), sixteen times the 0.1% stablecoin threshold and the third consecutive week of contraction."},
  {"identifier":"USDT-f8c08c","name":"WrappedUSDT","event":"burn",
   "supply_previous":str(int(tk["stable"]["USDT-f8c08c"]["prev"])),
   "supply_current":str(int(tk["stable"]["USDT-f8c08c"]["supply"])),
   "change_pct":tk["stable"]["USDT-f8c08c"]["pct"],
   "description":f"USDT {tk['stable']['USDT-f8c08c']['pct']:+.2f}% to {f(tk['stable']['USDT-f8c08c']['supply'])}, the largest weekly contraction in the tracked series and the third in a row alongside USDC."},
  {"identifier":"JWLEGLD-023462","name":"JewelSwap JewelEGLD","event":"supply_change",
   "supply_previous":None,"supply_current":str(int(em["JWLEGLD-023462"]["supply"])),
   "change_pct":None,
   "description":f"FIRST MEASUREMENT, and a correction to how it should be read: {f(em['JWLEGLD-023462']['supply'])} JWLEGLD across {em['JWLEGLD-023462']['holders']} holders looks like the largest protocol the discovery sweep has surfaced, but JWLEGLD is a 1:1 EGLD-pegged DEPOSIT token rather than a staking receipt. The stake delegated behind JewelSwap's liquid-staking contract is 1,799 EGLD, the smallest of the four. Supply is only a TVL proxy when the token IS the receipt."}],
 "consecutive_streaks":[
  {"metric":"lsd_supply_all","direction":"flat","weeks":7,
   "cumulative_change_pct":0.0,
   "interpretation":f"SEGLD {tk['lsd']['SEGLD-3ad2d0']['pct']:+.3f}%, XEGLD {tk['lsd']['XEGLD-e413ed']['pct']:+.3f}%, SWTAO {tk['lsd']['SWTAO-356a25']['pct']:+.2f}% - seven consecutive weeks inside the noise band, now through a cumulative +63% price move. The single exception is the smallest protocol on the list: Dinovox VoxEGLD grew delegated stake +7.9% to 1,895 EGLD and went from 78 to {em['VOXEGLD-5872e5']['holders']} holders."},
  {"metric":"total_delegators","direction":"flat","weeks":12,
   "cumulative_change_pct":-0.9,
   "interpretation":f"{sk['users_delta']:+,} this week to {f(sk['users'])}. Twelve weeks flat, through a +63% cumulative price move, a fee reversal at two providers and the largest distribution wave on record. This is a structural property of the delegation market, not a weekly observation, and it stays on the list only as a base rate."},
  {"metric":"provider_operator_fee_selling","direction":"flat","weeks":12,
   "cumulative_change_pct":0.0,
   "interpretation":"Twelve consecutive runs with zero exchange destinations from any sampled provider-operator wallet. Only a break would be newsworthy."},
  {"metric":"newly_issued_quality","direction":"flat","weeks":8,
   "cumulative_change_pct":0.0,
   "interpretation":f"Eight consecutive weeks with no token issuance clearing the >10-holder / >5-transaction bar. The best of this week's {len(tk['newly'])} has {tk['newly'][0]['accounts']} holders; the rest have one each. Primary issuance on this chain is effectively dormant."},
  {"metric":"stablecoin_supply_combined","direction":"down","weeks":3,
   "cumulative_change_pct":-3.5,
   "interpretation":"Three consecutive weeks of combined USDC+USDT contraction, every one into a rising price. Promoted this run from plumbing noise to a de-risking instrument reported alongside USH."},
  {"metric":"identifiable_bid_absorbed_egld_7d","direction":"flat","weeks":4,
   "cumulative_change_pct":0.0,
   "interpretation":f"Zero for a fourth straight week. The Mega Whale proxy's balance is unchanged to four decimals with zero transactions, and the desks' {absb['scanned']} outbound terminals ended the week holding {f(absb['total_balance_held'])} EGLD against {f(absb['total_received'])} received. The instrument stays retired."}],
 "regime_shifts":[
  {"metric":"otc_desk_inventory_egld","before_value":266213.0,"after_value":otc["desk_bal"],
   "description":f"The candidate regime shift flagged in run #23 is REJECTED, which is the correct outcome for a two-week promotion rule. Inventory did not hold its new level: {f(otc['prev_desk'])} -> {f(otc['desk_bal'])}. It was a staging event with a one-week delivery leg, exactly as the alternative hypothesis stated. The methodology's requirement that a new level hold two weeks before promotion earned its keep this week."},
  {"metric":"otc_wave_scale_egld","before_value":409680.0,"after_value":wave["net_one_way"],
   "description":f"Wave #3 delivered {f(wave['net_one_way'])} EGLD one-way feed-to-drain across Aug 17 - Sep 7, against 409,680 for the run #17 peak that had stood as the largest since tracking began. The scale of a single distribution episode has more than doubled. Whether that is a new operating scale or one exceptional programme needs another wave to answer, and the feed has to restart first."},
  {"metric":"binance_pipeline_participation","before_value":135003.0,
   "after_value":HOT["total_egld"],
   "description":f"Confirmed rather than newly flagged: Binance fed the desks for a second consecutive week ({f(HOT['total_egld'])} from the hot wallet into known feeders, {f(FEED.get('Binance',0))} arriving at the desks from Binance-labelled feeders). The custody watch and the pipeline watch stay merged. The new information is that custody REFILLED while the feed ran, so the funding source for the feed is not a custody drawdown - it is Binance's ordinary hot-wallet flow."}]}

R["watch_list"]=[
 {"item":f"OTC PIPELINE - wave #3 delivered {f(wave['net_one_way'])} EGLD and the desks are empty; the question is whether it restarts",
  "weeks_on_list":24,
  "reason":f"Desk inventory {f(otc['prev_desk'])} -> {f(otc['desk_bal'])} while delivering a record {f(otc['net_one_way'])} one-way this week. UPbit's feed has run at 297,000 / 460,000 / {f(otc['upbit_feed'])} for three weeks; the desks now hold less than a fifth of what they held last Sunday. Destinations: Binance.com +{f(V(otc['net_by_venue'],'Binance.com'))}, Bybit +{f(V(otc['net_by_venue'],'Bybit'))}, Gate.io +{f(V(otc['net_by_venue'],'Gate.io'))}. PRE-COMMITTED: a UPbit tranche above ~200,000 next week = wave #4 has started and the programme is continuous rather than episodic; a tranche under ~50,000 with desks still under ~120,000 = wave #3 is complete and the pipeline goes quiet as it did after run #17."},
 {"item":"THE UNIDENTIFIED BID - a record delivery was absorbed by something the model cannot see",
  "weeks_on_list":1,
  "reason":f"{f(otc['net_one_way'])} EGLD hit order books and the price rose {pc:+.1f}%. Every demand instrument the model has says no: DEX volume {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}% in EGLD terms, LSD supply flat for a seventh week, staked ratio at an archive low, the Mega Whale proxy at zero for a fourth week, the desks' own terminals holding {f(absb['total_balance_held'])} EGLD. The only positive reading is off-venue withdrawal breadth ({br['ex_n']} recipients, {f(br['ex_egld'])} EGLD), and {100*(br['top'][0]['egld']+br['top'][1]['egld'])/br['ex_egld']:.0f}% of that is two wallets. PRE-COMMITTED: if next week's price holds above ~$4.20 while the pipeline stays quiet, the bid is real and off-chain and the model needs an exchange-side instrument it does not have; if price retraces below ~$3.90 on no new delivery, this week was a squeeze into thin books and the delivery was the whole story."},
 {"item":"BINANCE HOT WALLET -> OTC FEEDERS is a standing programme, but custody is no longer the funding source",
  "weeks_on_list":18,
  "reason":f"The hot wallet sent {f(HOT['total_egld'])} EGLD to known feeders and routers over the full week (the truncated main pass saw {f(HOT.get('main_pass_egld',0))}), clearing run #23's 50,000 flow threshold five times over; Binance-labelled feeders delivered {f(FEED.get('Binance',0))} into the desks. Custody meanwhile ROSE +{f(cust['delta'])} to {f(cust['balance'])} after two weeks of drawdown. PRE-COMMITTED: hot-to-feeder flow above ~50,000 for a third consecutive week = a permanent funding line and Binance should be modelled as a standing pipeline participant; below ~10,000 = the two-week run was the wave and the custody and pipeline watches separate again."},
 {"item":"THE ZERO-STAKE PROVIDER COHORT - 82 contracts, 28,032 delegator records, almost all dormant",
  "weeks_on_list":3,
  "reason":f"{zsc['contracts']} contracts at zero locked stake with {f(zsc['attached_delegator_records'])} delegator records ({zsc['share_of_all_delegator_records_pct']:.1f}% of all records); only four emptied inside the archive and only ledgerbyfigment ({dser.get('ledgerbyfigment',{}).get('users_delta',0):+d} delegators this week, {f(zsc['with_activity_this_week'][0]['inbound_txs_this_week'])} inbound txs) shows any activity. The run #23 framing of 'three deregistrations' is superseded: three are recent exits, the other 79 are archaeology. PRE-COMMITTED (unchanged, week 2 of 4): a provider transitioning from locked > 0 to zero with users attached within four weeks = operator attrition is a live trend; none by run #27 = the recent cases are idiosyncratic."},
 {"item":"STAKED RATIO AT AN ARCHIVE LOW while the price makes an archive high",
  "weeks_on_list":2,
  "reason":f"{100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.3f}pp), staked {M['staked_chg']:+,.0f}, delegation {f(sk['delta_locked'])}, unbonding queue {f(sk['undelegated_week'])} EGLD from {sk['undelegate_callers']} wallets. Five consecutive weeks where participation moved opposite to price. PRE-COMMITTED: the ratio falling below 46.8% within three weeks = the security budget is in a genuine downtrend that a rising price is not arresting, and it becomes a first-order network-health finding; a recovery above 47.6% = this was unbonding-cycle noise around a flat base."},
 {"item":"THE ON-CHAIN DOLLAR BASE vs HATOM USH - cash out, leverage in",
  "weeks_on_list":2,
  "reason":f"Third consecutive combined contraction: USDC {tk['stable']['USDC-c76f1f']['pct']:+.2f}%, USDT {tk['stable']['USDT-f8c08c']['pct']:+.2f}%, about $220K over three weeks, all of it into rising prices. Against it USH minted {tk['lsd']['USH-111e09']['pct']:+.2f}% - leverage up, cash base down. PRE-COMMITTED: a fourth consecutive contraction = the dollar base is a leading de-risking signal and belongs in the executive summary each week; any week of combined expansion = the three-week run was redemption timing and it returns to the DeFi section."},
 {"item":"DEX TURNOVER IN EGLD TERMS - the constructive reading is withdrawn",
  "weeks_on_list":6,
  "reason":f"{f(bid['dexvol_egld'])} EGLD/day ({100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}%), below the 60,000 branch, so the USD turnover ratio is confirmed to have been tracking price and the 'bid returning' reading carried since run #22 is withdrawn. Pool depth {f(bid['pooltvl_egld'])} EGLD ({100*(bid['pooltvl_egld']-bid['prev_pooltvl_egld'])/bid['prev_pooltvl_egld']:+.1f}%), WEGLD/USDC {bid['wegld_usdc_share']:.1f}% of all volume. Kept on the list as the primary venue-demand series in its EGLD form."},
 {"item":"WITHDRAWAL BREADTH - the count broadened, the value concentrated",
  "weeks_on_list":6,
  "reason":f"{br['ex_n']} recipients took {f(br['ex_egld'])} EGLD off exchanges outside the pipeline (50 / 400,113 last week), clearing the pre-registered 40-recipient and 300,000 EGLD bar with zero page-cap terminations. But Unknown Whale B took {f(br['top'][0]['egld'])} and an unlabelled wallet {f(br['top'][1]['egld'])} - the latter also received 68,732 EGLD straight from the Binance hot wallet, so it is plumbing rather than accumulation. PRE-COMMITTED: ex-pipeline value holding above ~300,000 with the top two recipients under half of it = genuine dispersal; the top two above 60% again = the instrument is measuring a small number of large wallets and needs a concentration-adjusted version."},
 {"item":"JEXCHANGE ADDRESS RE-DERIVED - four runs of a false data gap",
  "weeks_on_list":1,
  "reason":f"The tracked aggregator returned {jex['old_transfers_7d']} transfers for a fourth run; tracing the fees contract's inbound callers identifies a live router at {jex['candidates'][0]['address'][:24]}... doing {f(jex['candidates'][0]['transfers_7d'])} transfers in 7 days, plus four more contracts behind it. Added to known-addresses this run. Watch that the new address keeps reporting - and treat any tracked contract that reads zero while its neighbours do not as an address problem first."},
 {"item":"COMPOUND RATE - reversed, test resolved, watch continues at lower priority",
  "weeks_on_list":5,
  "reason":f"{cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} vs {cvc['claim_count']}), up from 57.51% and the highest of eleven readings; run #23's contiguous branches resolved it cleanly on the 'stabilised' side. Institutional claims sold again ({beh['aggregates']['delegator_fates_by_tier']['institutional']['by_value_egld'].get('sold',0):.0f} EGLD, 2 of 2), retail sold nothing for an eleventh run. Kept at low priority: the series is now known to mean-revert, so only a sustained move below ~55% would be informative."},
]
json.dump(R,open("/tmp/run24w/part3.json","w"),indent=1,default=str)
print("part3 ok:",len(R["anomalies"]),"anomalies",len(R["watch_list"]),"watch items")
