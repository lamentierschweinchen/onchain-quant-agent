#!/usr/bin/env python3
"""Run #22 stage 4: anomalies, trends, watch list, meta_learning, pre_committed_tests"""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-08-24"
O=json.load(open("/tmp/run22w/derived.json"))
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
beh=json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
F=json.load(open(f"{REPO}/data/collected/followup_{RD}.json"))
r21=json.load(open(f"{REPO}/reports/2026-08-17.json"))
M=O["macro"]; otc=O["otc"]; wave=otc["wave"]; july=otc["july"]; ex=O["exch"]
cust=O["custody"]; bid=O["bid"]; br=O["breadth"]; sk=O["staking"]; tk=O["tokens"]
xx=O["xexchange"]; df=O["defi"]; z=O["z"]
price=M["price"]; pc=M["price_chg"]; econ=D["economics"]
cvc=beh["aggregates"]["compound_vs_claim_at_function_level"]
def f(x,d=0):
    try: return f"{x:,.{d}f}"
    except: return str(x)
R={}

def zz(k): return z[k].get("z")
R["anomalies"]=[
 {"metric":"egld_price_usd","current_value":price,"previous_value":M["prev_price"],
  "method":"z_score","severity":"high" if abs(zz('price'))>3 else "medium",
  "average_value":z["price"]["mean"],"stddev":z["price"]["stddev"],"z_score":zz("price"),
  "change_pct":pc,
  "description":f"EGLD ${price:.2f}, {pc:+.2f}% - the largest weekly move in twenty-two runs, z={zz('price'):+.2f}sigma against an 8-week baseline. The run #16 caveat about z UNDER-flagging after a trend applies in the same direction here: two up-weeks preceded this one and pulled the baseline mean up, so the true break is if anything larger than the z suggests. Cross-check with the rule-based read: BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%, EGLD between them. This is a beta move with no EGLD-specific component, which is the opposite of run #16."},
 {"metric":"dex_turnover_ratio_pct","current_value":bid["turnover"],"previous_value":bid["prev_turnover"],
  "method":"z_score","severity":"critical",
  "average_value":z["turnover"]["mean"],"stddev":z["turnover"]["stddev"],"z_score":zz("turnover"),
  "change_pct":100*(bid["turnover"]-bid["prev_turnover"])/bid["prev_turnover"],
  "description":f"DEX turnover {bid['turnover']:.2f}% of pool TVL per day against {bid['prev_turnover']:.2f}%, z={zz('turnover'):+.1f}sigma. CAVEAT ON THE Z: the baseline holds only four points (4.06 / 2.14 / 2.24 / 2.93) with a standard deviation of {z['turnover']['stddev']:.2f}, so the sigma figure is arithmetically correct but statistically thin - the finding rests on the raw magnitude, not the z. Volume tripled to ${f(bid['dexvol'])} while pool depth rose {100*(bid['pooltvl']-bid['prev_pooltvl'])/bid['prev_pooltvl']:.1f}%, which is the exact inverse of the run #18 absent-bid signature."},
 {"metric":"otc_pipeline_upbit_tranche_egld","current_value":otc["upbit_feed"],"previous_value":14000,
  "method":"rule_based","severity":"high",
  "change_pct":100*(otc["upbit_feed"]-14000)/14000,
  "description":f"UPbit fed {f(otc['upbit_feed'])} EGLD into the OTC desks after a one-week pause at 14,000. That is above the ~150,000 threshold run #21 pre-registered for calling the July-August pattern a standing programme rather than two discrete episodes, and it arrived in week one of the two-week window. Desk inventory rose +{f(otc['desk_delta'])} to {f(otc['desk_bal'])} - the highest combined desk balance recorded - so more is loaded than has been delivered."},
 {"metric":"binance_staking_custody_egld","current_value":cust["balance"],"previous_value":cust["previous"],
  "method":"z_score","severity":"medium",
  "average_value":z["custody"]["mean"],"stddev":z["custody"]["stddev"],"z_score":zz("custody"),
  "change_pct":100*cust["delta"]/cust["previous"],
  "description":f"Binance Staking custody {f(cust['delta'])} to {f(cust['balance'])}, z={zz('custody'):+.2f}sigma. The move is one standard transfer of 300,000 to the Binance.com hot wallet, visible on the custody address exactly as the run #15 rule predicts for custody<->hot legs. This is the pre-registered BEARISH branch of a watch standing since run #9, firing for the second time (run #15 was -158,853). The binance_staking delegation provider took only +2,422, so the EGLD did not go to staking."},
 {"metric":"provider_deregistration_p2p_org","current_value":0,"previous_value":sk["p2p_prev_locked"],
  "method":"rule_based","severity":"critical",
  "description":f"FIRST OPERATOR DEREGISTRATION IN TRACKING. p2p_org_ called unStakeNodes and went from 67,500 EGLD of node stake plus 2,083 topUp to ZERO locked, with 50 nodes still listed, 1,244 delegators still attached and APR now 0. Prior 'providers leaving' entries were books draining as delegators left; this is the operator pulling the nodes out from under the book. It is also the second leg of run #21's story - the wallet that unDelegated 149,585 EGLD did so from this exact contract."},
 {"metric":"delegation_total_locked_egld","current_value":sk["total_locked"],
  "previous_value":sk["prev_total_locked"],"method":"rule_based","severity":"medium",
  "change_pct":100*sk["delta_locked"]/sk["prev_total_locked"],
  "description":f"Delegation TVL {sk['delta_locked']:+,.0f} to {f(sk['total_locked'])}. Per the run #16 single-entity rule this must be decomposed before it is narrated: p2p_org_'s {f(abs(sk['p2p_prev_locked']))} is {100*abs(sk['p2p_prev_locked'])/abs(sk['delta_locked']):.0f}% of the decline and ex-that provider delegation moved {sk['delta_locked']+sk['p2p_prev_locked']:+,.0f} - flat, with the usual yield rotation underneath (pi-staking +18,964, stakenest +6,568, vaporrepublic +5,906 against Synexis -16,111 from one wallet)."},
 {"metric":"total_delegators","current_value":sk["users"],"previous_value":sk["prev_users"],
  "method":"rule_based","severity":"low",
  "change_pct":100*sk["users_delta"]/sk["prev_users"],
  "description":f"Delegator count {sk['users_delta']:+,} to {f(sk['users'])}, apparently breaking a nine-week flat series. IT IS NOT A BREAK, and the z-score is reported as rule_based deliberately: the baseline's standard deviation is about 25 on a base of 174,000, so a mechanical z of {zz('delegators'):+.0f}sigma is the degenerate-baseline artifact the run #9 guard exists to suppress. {sk['p2p_users']:,} of the {abs(sk['users_delta']):,} are p2p_org_'s users dropping out of the locked>0 working set when their provider's stake hit zero - nobody undelegated. Ex-p2p_org_ the base moved {sk['users_ex_p2p']:+,}. Participation inertia holds."},
 {"metric":"reward_compound_pct","current_value":cvc["compound_pct_of_reward_decisions"],
  "previous_value":59.07,"method":"z_score","severity":"medium",
  "average_value":z["compound"]["mean"],"stddev":z["compound"]["stddev"],"z_score":zz("compound"),
  "description":f"Compound rate {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} redelegate vs {cvc['claim_count']} claim), z={zz('compound'):+.2f}sigma and the lowest of nine readings. Third consecutive weekly decline. The run #11 framing reads a falling ratio during a decline as panic-claiming; during a +30.43% week the same sign means delegators monetising yield into strength. Corroborated at the tier level: institutional claims sold 3 of 4 by count, the first time any tier has led with selling."},
 {"metric":"hatom_lending_inverse_response_ratio","current_value":df["inverse_ratio"],
  "previous_value":0.72,"method":"rule_based","severity":"medium",
  "description":f"BILATERAL INVERSE RULE: ratio {df['inverse_ratio']:.2f}, below the 0.30 threshold the methodology registers as depositor-capacity exhaustion. Price {pc:+.2f}% (evaluable), Hatom Lending EGLD-denominated TVL {df['hatom_lending_egld_pct']:+.2f}% - correct inverse sign, so this is a genuine third up-week confirmation, but the weakest response the rule has produced on an up-week (0.49 / 0.72 / {df['inverse_ratio']:.2f}). The straightforward reading is that there is less deposit base left to withdraw than in June."},
 {"metric":"ush_supply","current_value":tk["lsd"]["USH-111e09"]["supply"],
  "previous_value":tk["lsd"]["USH-111e09"]["prev"],"method":"rule_based","severity":"medium",
  "change_pct":tk["lsd"]["USH-111e09"]["pct"],
  "description":f"USH supply {tk['lsd']['USH-111e09']['pct']:+.2f}% ({f(abs(tk['lsd']['USH-111e09']['supply']-tk['lsd']['USH-111e09']['prev']))} tokens burned) to {f(tk['lsd']['USH-111e09']['supply'])}. The run #11/#16 rule has burns as de-leveraging during declines and mints as leverage returning during rallies; a burn of this size INTO a +30% week is neither pattern. CDP borrowers repaid debt as collateral appreciated - de-risking into strength. Below the 5% exec-summary threshold but surfaced there anyway because the sign is anomalous for the price direction."},
 {"metric":"withdrawal_breadth_pipeline_share_pct","current_value":br["pipeline_share"],
  "previous_value":46.73,"method":"rule_based","severity":"medium",
  "description":f"{br['pipeline_share']:.1f}% of exchange outflow value above 1,000 EGLD went to OTC desks, feeders or routers, against 46.7% last week - the highest reading since run #17's 84%. Ex-pipeline the breadth was {br['ex_n']} recipients taking {f(br['ex_egld'])} EGLD, against 24 recipients and 111,683 last week. The withdrawal channel is hub-dominated again. CAVEAT: one Binance hot-wallet scan terminated on the page cap after 400 transactions covering 2.4 days, so the raw figure of {f(br['raw_egld'])} EGLD is a lower bound."},
 {"metric":"identifiable_bid_absorbed_egld_7d","current_value":0,"previous_value":0,
  "method":"rule_based","severity":"low",
  "description":f"The identifiable bid read ZERO for a second consecutive week and in three of the last four. The Mega Whale absorber recorded no transactions at all and its balance is unchanged to four decimals at {f(bid['mega_bal'],4)}; the Coinbase Routing pipe holds {f(bid['cbr_bal'],2)}. Reported at LOW severity rather than high because this week the other demand instrument moved hard in the opposite direction - turnover tripled - and the honest conclusion is that a single-wallet proxy has stopped being informative about aggregate demand."},
 {"metric":"exchange_net_flow_egld","current_value":ex["net"],"previous_value":3619.71,
  "method":"z_score","severity":"low",
  "average_value":z["exflow"]["mean"],"stddev":z["exflow"]["stddev"],"z_score":zz("exflow"),
  "description":f"Net exchange flow {ex['net']:+,.0f} EGLD, z={zz('exflow'):+.2f}sigma - statistically unremarkable and substantively uninformative. UPbit's {next((w['change_egld'] for w in ex['per_wallet'] if 'UPbit' in w['exchange']),0):+,.0f} is the OTC loading leg and Binance's move nets out within the entity; ex-UPbit the complex is flat. The run #14 rule applies in full: the flow signal this week is in the pipeline, not the balances."},
 {"metric":"otc_pipeline_throughput_egld_7d","current_value":otc["gross_out"],
  "previous_value":222532,"method":"z_score","severity":"low",
  "average_value":z["otc"]["mean"],"stddev":z["otc"]["stddev"],"z_score":zz("otc"),
  "description":f"Gross desk throughput {f(otc['gross_out'])} EGLD, 3.4x last week's 222,532 but only z={zz('otc'):+.2f}sigma because the baseline already contains the 1.28M run #17 peak. This is the run #16 under-flagging failure mode in reverse - a high-variance baseline swallowing a large move - and it is why the tranche size and the desk reload, not the gross figure, carry the finding."},
 {"metric":"usdt_supply","current_value":tk["stable"]["USDT-f8c08c"]["supply"],
  "previous_value":549884,"method":"rule_based","severity":"low",
  "change_pct":100*(tk["stable"]["USDT-f8c08c"]["supply"]-549884)/549884,
  "description":f"USDT supply {f(tk['stable']['USDT-f8c08c']['supply'])}, {100*(tk['stable']['USDT-f8c08c']['supply']-549884)/549884:+.2f}% - recovered. Run #21's -15.42% contraction resolves as a single desk redemption, on the benign branch of its pre-registered test. Top-25 holders account for 82% of supply and the largest is Hatom's USDT Money Market at 118,671, so the base is concentrated but the bridge is not draining."},
]

# ---------------- trend indicators ----------------------------------------
R["trend_indicators"]={
 "accelerating_exchange_outflows":[
  {"exchange":"UPbit","trend":"down","cumulative_change_pct":-6.19,"weeks_in_trend":1,
   "interpretation":f"UPbit fell {next((w['change_egld'] for w in ex['per_wallet'] if 'UPbit' in w['exchange']),0):+,.0f} while sending {f(otc['upbit_feed'])} to its own OTC desk. Per the run #16 rule this is the LOADING leg of a distribution programme, not customer withdrawal, and it should not be read as accumulation."},
  {"exchange":"Gate.io","trend":"down","cumulative_change_pct":-33.89,"weeks_in_trend":1,
   "interpretation":"Largest proportional fall of the week, -30,887 (-33.9%). Gate.io is simultaneously a net RECEIVER from the OTC hub (+28,346 two-hop-resolved), so its balance fell despite hub inflow - a genuine withdrawal against an incoming supply stream."},
  {"exchange":"Bybit","trend":"up","cumulative_change_pct":11.67,"weeks_in_trend":2,
   "interpretation":"+49,454 for a second consecutive build. Bybit is the largest net receiver from the desks (+132,402), so the balance growth is hub output arriving rather than independent customer deposits - supply landing at the venue with the deepest order book."},
  {"exchange":"Coinbase","trend":"down","cumulative_change_pct":-19.94,"weeks_in_trend":1,
   "interpretation":"-29,346 across 3 wallets. Coinbase (secondary) sent 20,974 EGLD to Unknown Whale B in two chunks and that wallet still holds it, so per the run #17 migration rule this is a withdrawal to a holder, not distribution."}],
 "validator_movements":{
  "providers_joining":0,"providers_leaving":1,"net_provider_change":-1,
  "notable_joiners":[],
  "notable_leavers":[{"identity":"p2p_org_","name":"p2p_org_",
    "previous_locked_egld":sk["p2p_prev_locked"]}]},
 "token_supply_events":[
  {"identifier":"USH-111e09","name":"Hatom USH","event":"burn",
   "supply_previous":str(int(tk["lsd"]["USH-111e09"]["prev"])),
   "supply_current":str(int(tk["lsd"]["USH-111e09"]["supply"])),
   "change_pct":tk["lsd"]["USH-111e09"]["pct"],
   "description":f"{f(abs(tk['lsd']['USH-111e09']['supply']-tk['lsd']['USH-111e09']['prev']))} USH burned ({tk['lsd']['USH-111e09']['pct']:+.2f}%) during a +30.43% price week. CDP borrowers repaid as collateral appreciated. Largest burn since run #19 and the first of any size on an up-week."},
  {"identifier":"USDT-f8c08c","name":"WrappedUSDT","event":"mint",
   "supply_previous":"549884","supply_current":str(int(tk["stable"]["USDT-f8c08c"]["supply"])),
   "change_pct":100*(tk["stable"]["USDT-f8c08c"]["supply"]-549884)/549884,
   "description":"USDT recovered +0.44% after run #21's -15.42% contraction, resolving that episode as a single desk redemption rather than a bridge drain."},
  {"identifier":"MEX-455c57","name":"MEX","event":"burn",
   "supply_previous":str(int(tk["mex_prev_supply"])),
   "supply_current":str(int(tk["mex_supply"])),
   "change_pct":100*(tk["mex_supply"]-tk["mex_prev_supply"])/tk["mex_prev_supply"],
   "description":f"MEX circulating supply fell {100*(tk['mex_supply']-tk['mex_prev_supply'])/tk['mex_prev_supply']:+.3f}% ({f(tk['mex_prev_supply']-tk['mex_supply'])} tokens). Real, but three orders of magnitude too small to explain the ~9.8pp five-week outperformance against EGLD. Queried specifically to test the buyback/burn hypothesis; it is not the mechanism."}],
 "consecutive_streaks":[
  {"metric":"dex_turnover_ratio_pct","direction":"up","weeks":3,"cumulative_change_pct":405.9,
   "interpretation":f"2.14 -> 2.24 -> 2.93 -> {bid['turnover']:.2f}%. Three consecutive rises and the last one is a step change. This is the model's cleanest demand series because it is price-independent, and it is now the strongest evidence against the absent-bid diagnosis carried since run #18."},
  {"metric":"reward_compound_pct","direction":"down","weeks":3,
   "cumulative_change_pct":100*(cvc['compound_pct_of_reward_decisions']-62.25)/62.25,
   "interpretation":f"62.25 -> 59.54 -> 59.07 -> {cvc['compound_pct_of_reward_decisions']:.2f}%. Delegators have compounded less every week for three weeks, through both a flat tape and a +30% one. On this week's price action the reading is yield being monetised into strength rather than panic-claimed."},
  {"metric":"identifiable_bid_absorbed_egld_7d","direction":"flat","weeks":2,
   "cumulative_change_pct":0.0,
   "interpretation":"Zero for a second straight week and in three of the last four. Read alongside the turnover streak, the conclusion is about the instrument rather than about demand: one wallet is no longer a proxy for the bid."},
  {"metric":"egld_price_usd","direction":"up","weeks":2,"cumulative_change_pct":34.33,
   "interpretation":"2.68 -> 2.76 -> 3.60. Two weeks, and the second is 30%. Not yet a 3-week streak, but it establishes the level the OTC feed restarted into."},
  {"metric":"lsd_supply_all","direction":"flat","weeks":5,"cumulative_change_pct":0.0,
   "interpretation":"SEGLD, XEGLD and SWTAO have all sat inside the noise band on the supply basis for five weeks, including through a 30% rally. No holder converted the move into a yield-bearing position at any measurable scale."},
  {"metric":"provider_operator_fee_selling","direction":"flat","weeks":10,
   "cumulative_change_pct":0.0,
   "interpretation":"Ten consecutive runs with zero exchange destinations from any sampled provider-operator wallet. Established as a base rate; only a break is newsworthy."}],
 "regime_shifts":[
  {"metric":"dex_turnover_ratio_pct","before_value":2.93,"after_value":bid["turnover"],
   "description":f"Turnover stepped from a 2-4% band to {bid['turnover']:.2f}% on volume tripling with depth rising. Flagged as a CANDIDATE regime shift, not a confirmed one: the methodology requires the new level to hold for 2+ weeks before promotion from anomaly, and a rally-week volume spike is the obvious alternative explanation. Pre-committed threshold registered below."},
  {"metric":"provider_deregistration","before_value":0,"after_value":1,
   "description":"The first operator deregistration in twenty-two runs. Whether it is a regime shift or a single business decision depends entirely on whether a second follows; one event is not a trend and is not treated as one here."},
  {"metric":"otc_weekly_netting_validity","before_value":55.0,"after_value":july["overstate_pct"],
   "description":f"Run #21 concluded from one wave that every weekly net one-way figure is an upper bound, with a 55% overstatement. Re-netting the July episode as one window gives {abs(july['overstate_pct']):.2f}% - weekly framing was accurate there. The corrected generalisation is that the overstatement is a property of waves that straddle a week boundary; the August wave does, July's did not."}]}

# ---------------- watch list ----------------------------------------------
R["watch_list"]=[
 {"item":"THE 229,865 EGLD IS NOW FULLY UNBONDED AND UNWITHDRAWN - erd1daqlaezxx22rzy",
  "weeks_on_list":2,
  "reason":f"None of run #21's three branches fired because a fourth state existed: the EGLD never left the delegation contracts. 80,279 reads seconds_remaining = 0 (claimable now) and 149,585 had 5,279 seconds left at snapshot; the wallet holds {f(F['run21_unbond_wallet']['balance_egld'],0)} EGLD and sent nothing all week. RE-REGISTERED with the missing branch added: withdrawn and sent to an exchange or OTC feeder = a 230K distribution event on top of a restarting pipeline; withdrawn and redelegated = rotation; still unwithdrawn after a second full week = an inactive or lost-access holder and the overhang stops being a live forward flow."},
 {"item":"OTC WAVE #3 - UPbit fed 297,000 after a one-week pause; desks at a record 109,857",
  "weeks_on_list":22,
  "reason":f"The standing-programme branch fired at nearly double its threshold in week one. Desk inventory ROSE +{f(otc['desk_delta'])} to {f(otc['desk_bal'])}, the highest recorded, so more is loaded than delivered - the drain leg is still ahead. Destinations resolve two hops to Bybit +{f(otc['net_by_venue'].get('Bybit',0))}, Binance.com +{f(otc['net_by_venue'].get('Binance.com',0))}, Gate.io +{f(otc['net_by_venue'].get('Gate.io',0))}. PRE-COMMITTED: another tranche above ~150,000 next week = wave #3 is escalating toward run #17 scale and the supply overhang is the dominant fact; nothing above ~50,000 = the 297,000 was a single reload."},
 {"item":"BINANCE STAKING CUSTODY - drawdown branch fired for the second time (-300,000 to hot)",
  "weeks_on_list":16,
  "reason":f"Custody {f(cust['balance'])} after one traceable 300,000 transfer into the Binance.com hot wallet, which now holds {f(cust['hot_balance'])}. The pre-registered reading since run #9 is that a drawdown to hot is distribution; it fired at run #15 (-158,853) and again now. PRE-COMMITTED: the hot wallet falling more than ~150,000 next week while the OTC feed continues = the 300,000 is being distributed and the two channels are one programme; hot flat or the custody re-parked = internal rebalancing and the branch over-reads a plumbing move."},
 {"item":"P2P.ORG DEREGISTERED - 1,244 delegators attached to a zero-stake contract",
  "weeks_on_list":1,
  "reason":"unStakeNodes took p2p_org_ from 67,500 stake + 2,083 topUp to zero locked; 50 nodes still listed, APR 0, 1,244 users still registered. First operator exit in tracking. What happens to those 1,244 delegators is the test: if their stake migrates to other providers over the next fortnight that is a forced-migration flow worth tracing and a live demonstration that inertia breaks under a total-loss-of-yield signal; if they sit there earning nothing, inertia is stronger than the 100%-fee providers already suggested. Also worth ~4 queries: whether the owner wallet erd1jxuc98ud0pe7 has any relationship to the two 100%-fee operators."},
 {"item":"THE 100%-FEE PROVIDERS - week 1 of a 2-3 week test, no branch fired",
  "weeks_on_list":2,
  "reason":f"procryptostaking {f(next(m['delta'] for m in sk['moves'] if m['identity']=='procryptostaking'))} (-9.6%) and egldstakingprovider {f(next(m['delta'] for m in sk['moves'] if m['identity']=='egldstakingprovider'))} (-15.6%), both still at serviceFee 1.0, APR 0, 50 nodes each, users -35 and -32. Books did not halve, the fee was not reversed, nodes were not deregistered. New this run: the two owner wallets each hold 1.69 EGLD, received NOTHING in 30 days, and sent one small transfer each to two DIFFERENT unlabelled recipients - so on the available evidence they do not share a counterparty. Test stays open."},
 {"item":"DEX TURNOVER REGIME - 2.93% to 10.83% in one week",
  "weeks_on_list":4,
  "reason":f"Third consecutive rise and a step change, far past the ~3.5% threshold run #21 registered. Volume ${f(bid['dexvol'])} (+{100*(bid['dexvol']-bid['prev_dexvol'])/bid['prev_dexvol']:.0f}%) with depth also up {100*(bid['pooltvl']-bid['prev_pooltvl'])/bid['prev_pooltvl']:.1f}%. PRE-COMMITTED: holding above ~5% next week = a genuine regime change in DEX demand and the absent-bid diagnosis carried since run #18 is retired; falling back below 3.5% = a rally-week volume spike and the 2-4% band is the real level."},
 {"item":"MEX RELATIVE STRENGTH - 5 weeks, +9.8pp cumulative, mechanism still unidentified",
  "weeks_on_list":5,
  "reason":f"MEX {xx['mex_wow']:+.2f}% vs EGLD {pc:+.2f}%, a fifth consecutive week at or above, and over the five weeks MEX is +23.73% against EGLD's +13.92%. The threshold fired, but the mechanism hunt came back empty: supply moved {100*(tk['mex_supply']-tk['mex_prev_supply'])/tk['mex_prev_supply']:+.3f}% (far too small) and MEX/WEGLD pool depth grew with the market rather than ahead of it (${f(xx['mex_pair_depth']['tvl_usd'])}, {xx['mex_pair_depth']['share_of_pool_tvl_pct']:.1f}% of TVL). PRE-COMMITTED: pool TVL in EGLD terms growing >10% WoW or supply falling >1% = a mechanical explanation; neither, for a second run of looking = the outperformance is unexplained flow and should be labelled as such rather than re-explained."},
 {"item":"COMPOUND RATE - third consecutive decline, lowest of nine readings",
  "weeks_on_list":3,
  "reason":f"{cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} vs {cvc['claim_count']}). Institutional-tier claims sold 3 of 4 by count, the first tier ever to lead with selling; retail sold nothing for a ninth run. PRE-COMMITTED: below 56% next week = delegators are systematically monetising yield and the compound rate is tracking price strength rather than conviction; back above 59% = a single rally-week claim spike."},
 {"item":"UNBONDING QUEUE - now a weekly series",
  "weeks_on_list":2,
  "reason":f"Recorded properly this run after fixing the join key (previous.json stores providers by IDENTITY, not address; joining on address produced 79 phantom movers and zero wallets on the first pass). {sk['undelegate_callers']} distinct wallets unDelegated {f(sk['undelegated_week'])} EGLD across the ten providers that moved more than 5,000; measured pending unbonding {f(sk['pool_total'])} EGLD settling over 2-8 days, largest single leg 26,692 spread across three providers. Together with p2p_org_'s {f(abs(sk['p2p_prev_locked']))} node unstake this fully absorbs the {f(sk['residual'])} staked-minus-delegated residual, so no direct-node figure is published."},
 {"item":"UNKNOWN WHALE I - classification closed as operator inventory",
  "weeks_on_list":6,
  "reason":f"Balance 163,053 -> 128,431 (-34,622). Its largest external counterparty erd1qkazru7aw5 turns out to trade almost exclusively with Whale I itself (37,188 out to it, 52,551 in from it over 30 days, on a 46,629 balance and nonce 566) - a second wallet of the same operator, not an external buyer. That closes run #21's classification: Whale I's hub take is operator inventory and is excluded from the demand instruments. Its +2,686 net hub take this week is netted out of the one-way figure accordingly. Graduating to background unless it doubles in size."},
 {"item":"HATOM DEPOSITOR CAPACITY - inverse response ratio below 0.30",
  "weeks_on_list":1,
  "reason":f"Ratio {df['inverse_ratio']:.2f} on a correct-signed third up-week confirmation, below the 0.30 threshold the methodology defines as depositor-capacity exhaustion. Up-week series 0.49 / 0.72 / {df['inverse_ratio']:.2f}. Watch whether the next |5%| week produces a smaller response again; two consecutive sub-0.30 readings would mean the rule has run out of the deposit base it depends on and should be retired rather than re-confirmed."},
]
json.dump(R,open("/tmp/run22w/part3.json","w"),indent=1,default=str)
print("part3 ok:",list(R.keys()),len(R["anomalies"]),"anomalies",len(R["watch_list"]),"watch")
