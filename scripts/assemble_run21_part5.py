#!/usr/bin/env python3
"""Run #21 stage 5: watch list + meta_learning, then write reports/2026-08-17.json."""
import json
from datetime import datetime, timezone

REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
O=json.load(open("/tmp/run21w/derived.json"))
P3=json.load(open("/tmp/run21w/part3.json"))
P4=json.load(open("/tmp/run21w/part4.json"))
D=json.load(open(f"{REPO}/data/collected/2026-08-17.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
status=json.load(open("/tmp/run21w/status.json"))

M=O["macro"]; otc=O["otc"]; wave=otc["wave"]; bid=O["bid"]; ex=O["exch"]; cust=O["custody"]
sk=O["staking"]; rw=O["reward"]; xx=O["xexchange"]; df=O["defi"]; wi=O["whale_i"]; br=O["breadth"]
FEE=sk["fee_events"]; F1=FEE[0]; F2=FEE[1]; UNW=sk["unwind"]
price=M["price"]; pc=M["price_chg"]
def f(x,d=0): return f"{x:,.{d}f}"

watch_list=[
 {"item":f"THE 229,865 EGLD UNBOND LANDS NEXT WEEK: one wallet unDelegated {f(UNW['legs'][0]['amount'])} from p2p_org_ and {f(UNW['legs'][1]['amount'])} from a second provider, unbonding completes in {UNW['legs'][1]['days_to_unbond']:.1f} and {UNW['legs'][0]['days_to_unbond']:.1f} days",
  "reason":f"This is the largest single-wallet delegation unwind in tracking and it explains {UNW['share_of_delegation_decline_pct']:.0f}% of this week's delegation TVL decline and essentially all of the {sk['raw_direct_residual']:+,.0f} residual that used to be called a direct-node unwind. The wallet ({UNW['address'][:20]}...) holds {f(2253.5,0)} EGLD, nonce 55, and has historically received ~110 EGLD/day reward drips and forwarded 12,100-15,000 EGLD chunks to a single nonce-7 recipient. PRE-COMMITTED READING: the withdrawn EGLD arriving at a delegation contract = rotation between providers, neutral; arriving at an exchange or an OTC feeder = a 230K distribution event that would dwarf this week's entire OTC one-way figure and should be treated as the dominant fact next run; staying in the wallet = idiosyncratic and dismissable. Check /accounts/{{addr}}/delegation for completion and then the wallet's outbound within 72h.","weeks_on_list":1},
 {"item":f"WAVE #2 STOPPED FEEDING: UPbit tranche {f(otc['upbit_feed'])} vs 319,000, desks returned {f(otc['upbit_return'])} to UPbit; wave-window net one-way {f(wave['net_one_way'])} ({100*wave['net_one_way']/otc['peak']['net']:.0f}% of the re-netted run #17 peak)",
  "reason":f"Run #20's escalation thresholds (net >300K, tranche >350K) did not fire and the feed collapsed {100*(otc['upbit_feed']-otc['prev_upbit_feed'])/otc['prev_upbit_feed']:+.0f}%. The desks are now unloading inventory back to UPbit rather than distributing it onward. PRE-COMMITTED: a fresh UPbit tranche above ~150,000 within two weeks = wave #3 and the July-August pattern is a standing programme rather than two episodes; no tranche above ~50,000 for two consecutive weeks = the programme is between cycles and the historical reload lag (1-3 weeks) becomes the thing to watch. Report the WAVE-window net alongside the weekly one from now on - the weekly figure is an upper bound.","weeks_on_list":3},
 {"item":f"TWO PROVIDERS AT A 100% SERVICE FEE ({F1['provider']} 15%->100%, {F2['provider']} 20%->100%), delegator APR zero, both still running 50 nodes",
  "reason":f"Run #20's 'first competitive fee cut in twenty runs' is withdrawn - this is a wind-down or a squeeze by two unrelated operators (different owner wallets), verified on three endpoints. Combined they hold {f(F1['locked_egld']+F2['locked_egld'])} EGLD and {F1['users']+F2['users']:,} delegators earning nothing. PRE-COMMITTED: if their books halve again within 2-3 weeks while the user counts stay flat, retail inertia is confirmed as absolute and the delegation market's price mechanism only operates on large holders; if the fee is reversed, it was a temporary operational move and the run #20 reading was merely early rather than wrong; if the providers deregister their nodes, this is the first genuine validator exit in tracking and the delegators' {f(F1['locked_egld']+F2['locked_egld'])} EGLD becomes a forced-migration flow worth tracing.","weeks_on_list":1},
 {"item":f"IDENTIFIABLE BID BACK TO ZERO - absent in {bid['weeks_at_zero_in_last_four']} of the last 4 weeks",
  "reason":f"Run #20's pre-registered sub-10K branch fired: the absorber recorded zero transactions ({f(bid['mega_balance'])}, {bid['mega_change']:+.2f}) and the Coinbase Routing pipe stayed dry at {f(bid['cb_routing_balance'],1)} EGLD. Dormancy is revived as a structural finding. PRE-COMMITTED: a tranche of 30-50K would still be the threshold for calling the bid genuinely back; a second consecutive zero week alongside a resumed OTC feed would be the bearish configuration to fear, because this week's tolerable outcome depended entirely on the offer being absent too.","weeks_on_list":19},
 {"item":f"BINANCE RE-PARKED {f(cust['change'])} HOT -> CUSTODY, custody {f(cust['balance'])} ({cust['from_peak']:+,.0f} from peak), not delegated",
  "reason":f"First custody movement in three weeks, one traceable standard transfer on 2026-08-14. Neither registered branch fired - this is re-parking, the third case, mildly constructive because the coins left the wallet Binance sells from. The runs #7-#10 precedent is a warning: that accumulation phase also parked without delegating and ended in a -305,549 drawdown. PRE-COMMITTED, unchanged: a jump in the binance_staking provider or economics.staked matching the custody balance = delegation, the first genuinely constructive Binance signal in seven runs; a drawdown back to hot = distribution resuming; continued parking = no information, do not narrate it again until it moves.","weeks_on_list":15},
 {"item":f"BRIDGED USDT -{abs(df['usdt_supply_wow']):.2f}% ({f(df['usdt_supply_prev']-df['usdt_supply'])} tokens) - largest stablecoin contraction in tracking, 9th run without an inflow week",
  "reason":f"USDT {f(df['usdt_supply_prev'])} -> {f(df['usdt_supply'])}, USDC {df['usdc_supply_wow']:+.2f}%. On a ~$100K absolute basis this is not systemic, but it is the only instrument this week pointing against the price action, and a 15% single-week redemption on a bridged asset is usually one desk closing a position rather than diffuse retail. PRE-COMMITTED: another >5% USDT contraction = the bridge is being drained and the on-chain dollar base becomes a first-order concern at ~450K remaining; a flat or positive week = this was a single redemption and the nine-run bleed continues at its usual low rate.","weeks_on_list":8},
 {"item":f"DEX TURNOVER ROSE A SECOND WEEK: {xx['previous_turnover_ratio_pct']:.2f}% -> {xx['turnover_ratio_pct']:.2f}% of pool TVL/day on volume {xx['dex_vol_wow_pct']:+.0f}%",
  "reason":f"First two-week improvement in any demand instrument since they were built in run #19; series 4.06 / 2.14 / 2.24 / {xx['turnover_ratio_pct']:.2f}. Run #19's ~4% threshold for evidence of a returning bid is unmet. PRE-COMMITTED: a third rise taking turnover above ~3.5% while the OTC feed stays off = the demand side is genuinely repairing and the model should stop describing it as absent; a reversion below 2.5% = the two-week bounce tracked the supply pause rather than any new bid.","weeks_on_list":4},
 {"item":f"'UNKNOWN WHALE I' RECLASSIFIED as OTC operator inventory ({wi['combined_pipeline_pct']:.1f}% of two-way value with hub infrastructure, threshold was 60%)",
  "reason":f"The raised page cap completed the 30-day trace with no truncation: {wi['in_txs']}/{wi['out_txs']} transactions, {wi['in_counterparties']}/{wi['out_counterparties']} distinct counterparties, {wi['in_pipeline_pct']:.1f}% of inbound and {wi['out_pipeline_pct']:.1f}% of outbound value from/to desks, routers and feeders. It clears run #20's threshold on the combined and inbound bases and misses on outbound alone, so the classification carries that caveat. CONSEQUENCE APPLIED: its hub take is no longer counted as demand; netting it out moves this week's one-way from {f(otc['net_one_way'])} to {f(otc['net_one_way']-wi['hub_net_this_week'])}. NEXT: identify its largest EXTERNAL counterparty (erd1qkazru7aw5, 27,216 in / 41,970 out over 30 days) - if that is also pipeline infrastructure the classification becomes unambiguous.","weeks_on_list":3},
 {"item":f"MEX HAS MATCHED OR BEATEN EGLD FOR FOUR WEEKS and the stale-pricing explanation is falsified (MEX/WEGLD is the #{xx['mex_pair_depth']['depth_rank']} deepest pool at ${xx['mex_pair_depth']['tvl_usd']:,.0f}, {xx['mex_pair_depth']['trades_24h']} trades/24h)",
  "reason":f"MEX {xx['mex_price_change_wow_pct']:+.2f}% vs EGLD {pc:+.2f}% this week. Two runs asserted illiquidity without checking; measured, the pair holds {xx['mex_pair_depth']['share_of_pool_tvl_pct']:.1f}% of all xExchange depth. PRE-COMMITTED: a fifth week of MEX >= EGLD makes this a genuine relative-value signal worth explaining (buybacks, farm emissions changing, or rotation into the DEX token ahead of the native asset); a reversion means the four-week run was noise on thin volume after all. Either way the model must stop offering the illiquidity explanation.","weeks_on_list":1},
 {"item":f"XEGLD REDEMPTION TRACED AND BENIGN: {O['xegld_trace']['callers']} callers, {f(O['xegld_trace']['delegation_egld'])} EGLD into native delegation, ZERO to exchanges; supply {df['xegld_supply_wow']:+.2f}% (decelerating from -2.23%)",
  "reason":f"Run #20's highest-value open DeFi question is closed on the constructive branch. The LSD contract settles via SC results with zero outbound value transactions, so the method that worked was tracing the unDelegate/withdraw callers and their onward flows - 80-600 EGLD each, heterogeneous, no exchange destination. GRADUATING this item unless XEGLD supply moves more than 1% in either direction next run, in which case re-run the same caller trace.","weeks_on_list":2}]

# ---------------- meta learning ----------------
api_quirks=[
 "THE PROTOCOL STAKING SC IS NOT QUERYABLE FOR TRANSACTIONS. erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqplllst77y4l returns a valid /accounts response (balance 14,514,270, matching economics.staked) but HTTP 400 on /accounts/{addr}/transactions in every variant tried - with and without status, with and without a direction filter, and on the global /transactions?receiver= form. Direct-node stake flows therefore cannot be traced through the staking contract at all; /accounts/{addr}/delegation on individual wallets is the only route to the unbonding pool.",
 "/accounts/{addr}/delegation IS THE MISSING INSTRUMENT FOR THE STAKED-VS-DELEGATED RESIDUAL. It returns, per delegation contract, userActiveStake, userUnBondable and a userUndelegatedList with amounts and remaining seconds. This is what makes in-flight unbonding measurable and it is what shows the residual (economics.staked minus summed provider locked) to be a direct-node PLUS unbonding-pool figure rather than a direct-node figure.",
 "A PROVIDER CAN REPORT serviceFee = 1.0 AND apr = 0. Two providers did this week (egldstakingprovider, procryptostaking), consistently across /providers, /providers?identity= and /providers/{address}. It is not an indexer artifact and it puts them outside every APR bucket, so bucket coverage must be reported against total delegated rather than assumed complete: 5 providers now hold "+f"{sk['zero_apr_locked']:,.0f}"+" EGLD at 0% APR.",
 "A PROVIDER THAT GOES TO locked = 0 DISAPPEARS FROM THE locked>0 WORKING SET, so its entire balance registers as a validator departure rather than a delegation outflow. One provider did this week (122,947 -> 0). Decompose delegation TVL change as: sum of surviving-provider deltas PLUS the full locked of any provider that left, or the numbers will not reconcile (they do: -212,841 + 99,353 - 122,947 = -236,435).",
 "ZERO-VALUE TRANSACTIONS CARRY THE AMOUNT IN THE data FIELD - the run #19 rule, now load-bearing twice. unDelegate@1fad0a25583f89808905 decodes to 149,585.4 EGLD. Any delegation-layer flow analysis that reads only tx.value sees nothing.",
 "PAGINATED HISTORICAL WINDOWS REMAIN REPRODUCIBLE. The run #16 (Jul 6-13) window re-queried six weeks later returned gross 1,100,791 - matching run #18's independent backfill to the EGLD - and every router and feeder was still resolvable. Retrospective re-netting works at least six weeks out.",
 "PAGE-CAP LOGGING WORKED AND REPORTED NOTHING. The collector now records any paginated query that terminates on the page cap rather than the time boundary; with max_pages raised to 40 the whale-I 30-day trace completed cleanly (661/562 txs) and the log is empty, which is the intended outcome of run #20's recommendation.",
 "CLEAN PRICE-FEED RUN (7th consecutive): the dataApi re-fetch guard reported 0 retries across SEGLD, SWTAO, USH and XEGLD.",
 "The ESDT system-SC issue scan returned exactly one issuance: BTC-8549df, named 'Bitcoin', 3 holders / 23 transactions - a ticker impersonation, filtered by the run #15 quality bar."]

data_gaps=[
 "The wave-window netting method is established but only ONE wave has been netted that way (Aug 3-17). Runs #16-#18 were single-window measurements and their feed and drain legs may also straddle window boundaries - the run #16 window shows gross_in 1,305,005 against gross_out 1,100,791, which is exactly the signature of a feed whose drain sits outside the window. The five-anchor net series should be treated as upper bounds until the July episode is re-netted feed-to-drain.",
 "Why two unrelated providers set a 100% service fee in the same week is unexplained. Coordinated operator behaviour, a common service provider, or an unrelated coincidence are all consistent with what was measured; the owner wallets differ and neither was traced further.",
 "MEX outperforming EGLD for four consecutive weeks is now a measured fact with no mechanism attached. The illiquidity explanation is falsified; buybacks, emission changes and rotation are all untested.",
 "The corrected direct-node figure (+52,848 this week) has not been recomputed for runs #18-#20, because doing so requires the unbonding pool at each historical date and /accounts/{addr}/delegation is a point-in-time endpoint. The honest position is that the prior three weeks' direct-node readings are unreliable in magnitude and direction, not that they were the opposite sign.",
 "Two entries in known-addresses.json remain invalid-checksum and are flagged rather than guessed: Hatom UTK Money Market and OneDex Launchpad. Neither is queried by the collector, so no figure is affected."]

key_findings=[
 f"WAVE #2 DID NOT ESCALATE: UPbit's feed collapsed {100*(otc['upbit_feed']-otc['prev_upbit_feed'])/otc['prev_upbit_feed']:+.0f}% to {f(otc['upbit_feed'])} and the desks returned {f(otc['upbit_return'])} to UPbit. Run #20's pre-committed escalation thresholds (net >300K, tranche >350K) both missed.",
 f"WEEKLY NETTING OVERSTATES DISTRIBUTION BY {wave['overstatement_pct']:.0f}%: the wave netted as one window (Aug 3-17) is {f(wave['net_one_way'])} one-way against {f(wave['sum_of_weekly_nets'])} from summing weekly nets. Circularity crosses week boundaries. NEW RULE: net feed-to-drain, treat weekly net one-way as an upper bound.",
 f"THE DIRECT-NODE UNWIND IS WITHDRAWN: the staked-minus-delegated residual also contains delegation unbonding in flight. One wallet's {f(UNW['total'])} unDelegate pair explains this week's {sk['raw_direct_residual']:+,.0f} flip; corrected, direct-node stake GREW {sk['corrected_direct']:+,.0f}.",
 f"BOTH HIGH-FEE INCUMBENTS SET SERVICE FEE TO 100% (APR 0): {F1['provider']} 15%->100%, {F2['provider']} 20%->100%, different owners, 50 nodes each. Run #20's 'first competitive fee cut' reading is withdrawn.",
 f"THE IDENTIFIABLE BID RETURNED TO ZERO exactly as the pre-committed sub-10K branch specified - absorber and Coinbase Routing both recorded zero transactions. Dormancy revived as structural: absent in {bid['weeks_at_zero_in_last_four']} of 4 weeks.",
 f"EGLD OUTPERFORMED for the first time since run #16 ({pc:+.2f}% vs BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%) in the same week the OTC feed switched off - the marginal seller, not the marginal buyer, has been setting this price.",
 f"BRIDGED USDT -{abs(df['usdt_supply_wow']):.2f}% ({f(df['usdt_supply_prev']-df['usdt_supply'])} tokens), the largest stablecoin contraction in tracking; USDC {df['usdc_supply_wow']:+.2f}%. Ninth run with no inflow week.",
 f"BINANCE RE-PARKED {f(cust['change'])} EGLD hot -> staking custody in one traceable transfer; custody {f(cust['balance'])}, not delegated.",
 f"NET ONE-WAY SERIES BACKFILLED to five measured anchors: run #16 {f(otc['run16']['net'])} ({otc['run16']['circ_pct']:.0f}% circular), run #17 {f(otc['peak']['net'])}, run #18 {f(otc['run18']['net'])} ({otc['run18']['circ_pct']:.0f}%), run #19 61,435, run #20 {f(otc['prev_net'])}, run #21 {f(otc['net_one_way'])}.",
 f"MEX's OUTPERFORMANCE IS REAL: MEX/WEGLD is the #{xx['mex_pair_depth']['depth_rank']} deepest pool on xExchange (${xx['mex_pair_depth']['tvl_usd']:,.0f}, {xx['mex_pair_depth']['share_of_pool_tvl_pct']:.1f}% of all depth) with {xx['mex_pair_depth']['trades_24h']} trades/24h. Four weeks of MEX >= EGLD; the stale-pricing explanation is withdrawn.",
 f"XEGLD REDEMPTION TRACED: {O['xegld_trace']['callers']} callers, onward flows 80-600 EGLD each, {f(O['xegld_trace']['delegation_egld'])} EGLD into native delegation, ZERO to exchanges. Retail rotation, not an exit.",
 f"'UNKNOWN WHALE I' meets the 60% threshold ({wi['combined_pipeline_pct']:.1f}% two-way with hub infrastructure) and is reclassified as OTC operator inventory; one-way ex-whale-I is {f(otc['net_one_way']-wi['hub_net_this_week'])}.",
 f"DELEGATION TVL {sk['deleg_tvl_wow']:+,.0f} is {UNW['share_of_delegation_decline_pct']:.0f}% one wallet; ex-it, flat. One provider left the active set (122,947 -> 0), the first >50K departure in tracking. Delegators {sk['churn']['total_delegators_current']:,} ({sk['churn']['delegators_added']:+}), 9th flat week.",
 f"Turnover rose a 2nd week ({xx['previous_turnover_ratio_pct']:.2f}% -> {xx['turnover_ratio_pct']:.2f}%) and ex-pipeline withdrawal breadth hit its highest reading yet ({br['distinct_recipients_ex_pipeline']} addresses, {f(br['total_egld_ex_pipeline'])} EGLD, pipeline share down to {br['pipeline_share_pct']:.0f}% from 84%).",
 "ZERO qualifying new tokens for a 5th consecutive week; the single issuance was a 'Bitcoin' ticker impersonation with 3 holders."]

methodology_changes=[
 "NET THE OTC HUB OVER THE WAVE, NOT THE REPORTING WEEK (new, and it revises every net one-way figure). Circularity crosses week boundaries: UPbit's 319,000 feed landed in the Aug 3-10 window and 130,000 of the return leg landed in Aug 10-17, so weekly netting counts legs whose mirrors sit in the adjacent week. Summed weekly nets for wave #2 give 326,924; netting Aug 3-17 as one window gives 210,922, a 55% overstatement. Rule: report the wave-window net alongside the weekly figure, and treat weekly net one-way as an upper bound.",
 "THE STAKED-MINUS-DELEGATED RESIDUAL IS NOT A DIRECT-NODE MEASURE (new, and it withdraws a three-run narrative). It also contains delegation unbonding in flight, because unDelegate removes EGLD from provider locked immediately while it stays in the staking module for 7-10 epochs. Decompose it with /accounts/{addr}/delegation on the wallets behind large provider moves before attributing anything to node operators. The protocol Staking SC cannot be used as a cross-check - it returns HTTP 400 on all transaction queries.",
 "A FEE CHANGE IS NOT EVIDENCE OF COMPETITION (new, correcting run #20). Run #20 read egldstakingprovider's 24% -> 15% cut as the delegation market's first competitive repricing; one week later it went to 100% and so did procryptostaking. Rule: a single parameter move by an incumbent under pressure is ambiguous between competing, winding down and squeezing - wait for the direction to persist for two weeks, or for stake to actually return, before assigning intent.",
 "DECOMPOSE DELEGATION TVL AS SURVIVING-PROVIDER DELTAS PLUS FULL LOCKED OF ANY LEAVER (new). A provider whose locked goes to zero drops out of the locked>0 working set, so its balance silently becomes a validator-departure statistic rather than part of the TVL delta. This week: -212,841 + 99,353 - 122,947 = -236,435, and without the third term the figures do not reconcile.",
 "CHECK THE CHEAP THING BEFORE REPEATING AN EXPLANATION (new, correcting runs #19-#20). MEX's outperformance was attributed to 'stale pricing in illiquid pairs' twice without querying the pair. One field (totalValue on /mex/pairs, already in the collected snapshot) shows MEX/WEGLD is the #2 deepest pool on the venue. Rule: an explanation repeated in a second run must be verified in that run, not restated.",
 "RAISED max_pages TO 40 FOR HIGH-FREQUENCY ADDRESSES AND LOGGED PAGE-CAP TERMINATIONS (implemented, closes run #20's method fix). The whale-I 30-day trace completed without truncation and the page-cap log is empty."]

dashboard_suggestions=[
 {"title":"Wave-window OTC netting (feed-to-drain) alongside the weekly series",
  "motivation":f"This run's most consequential result is that weekly netting overstates one-way distribution by {wave['overstatement_pct']:.0f}% because circularity crosses week boundaries - wave #2 is {f(wave['net_one_way'])} netted feed-to-drain against {f(wave['sum_of_weekly_nets'])} summed weekly. The dashboard currently shows one number per week, which is exactly the framing this run proved to be an upper bound. A reader cannot see that the run #20 bar and the run #21 bar are two halves of one episode.",
  "suggested_visualization":"the weekly net series as light bars with wave episodes drawn as brackets spanning their weeks, each bracket labelled with its feed-to-drain net and the % overstatement of the summed weekly figures inside it; a chip per wave for feeding / draining / dormant.",
  "data_already_available":True,
  "data_source":"whale_intelligence.otc_pipeline now carries wave_window_netting (window, gross, circular, net_one_way, sum_of_weekly_nets, overstatement) plus the five-anchor net series and per-venue netting",
  "priority":"high"},
 {"title":"Delegation unbonding queue",
  "motivation":f"A single wallet's {f(UNW['total'])} unDelegate pair explained this week's entire staked-minus-delegated residual and {UNW['share_of_delegation_decline_pct']:.0f}% of the delegation TVL decline, and it withdrew a three-run 'direct-node unwind' narrative. The unbonding pool is a first-order quantity the dashboard cannot show at all, and it is forward-looking: {f(UNW['total'])} EGLD becomes liquid within 7 days, and where it goes is next week's most important flow.",
  "suggested_visualization":"a small queue table - amount, source provider, days remaining, and (once resolved) destination class - with a stacked bar of EGLD becoming liquid per upcoming week, so the reader sees the overhang before it lands.",
  "data_already_available":False,
  "data_source":"/accounts/{addr}/delegation userUndelegatedList per wallet behind large provider moves; would need an `unbonding_queue` array in staking_intelligence carrying amount, provider, seconds_remaining, wallet",
  "priority":"high"},
 {"title":"Pre-committed test scoreboard (third submission)",
  "motivation":f"Run #20 registered five tests with numeric thresholds. This run resolved four of them - the OTC escalation test failed to fire, the bid returned to zero on the sub-10K branch, the XEGLD destination landed on the constructive branch, and the whale-I 60% threshold was cleared - and separately WITHDREW two prior headlines (the fee cut, the direct-node unwind). A reader of this report sees ten assertive findings with no way to distinguish a prediction that fired from a correction of last week's claim, and both are present here in quantity.",
  "suggested_visualization":"a table of open and resolved tests - registered-in run, claim, numeric threshold, outcome chip (fired-as-predicted / fired-against / withdrawn / open) - with open tests pinned to the top and a small counter of headlines withdrawn per run next to it.",
  "data_already_available":False,
  "data_source":"still prose inside watch_list.reason and recommendations_for_next_run; needs a structured pre_committed_tests array with threshold, branches and resolution, plus a withdrawn_claims array",
  "priority":"high"}]

dashboard_followup=[
 {"title":"OTC net one-way series with measurement-provenance markers","status":"pending",
  "note":"Not built, and this run changes its specification: the series now has five measured anchors (run #16 and #18 backfilled) but ALSO a demonstrated frame problem, so provenance markers must distinguish weekly-netted from wave-netted, not just gross from net. Superseded in scope by this run's suggestion #1."},
 {"title":"Pre-committed test scoreboard","status":"pending",
  "note":"Re-submitted a third time, still high priority. Four tests resolved this run and two prior headlines were withdrawn, which is the strongest case yet: the scoreboard is what separates 'the model predicted this' from 'the model corrected itself', and this report contains both."},
 {"title":"Unexplained-flow tracker","status":"deprioritized",
  "note":"Deprioritised because the run #20 entries it was designed to hold have both been resolved this run - the direct-node unwind was an artifact and the XEGLD redemption is traced and benign. The constructive successor is the unbonding-queue view (this run's suggestion #2), which tracks a KNOWN forward flow rather than a residual nobody can explain."},
 {"title":"OTC hub flow map: gross vs net one-way, with venue-level netting","status":"pending",
  "note":"Not built. Still well-supported by the data (per-venue netting for five windows plus the wave window), and this week's UPbit reversal - net source in one week, net receiver in the next - is precisely the structure a chord or Sankey view would make legible where a table does not."},
 {"title":"Demand instrument panel: turnover ratio, identifiable bid, withdrawal breadth","status":"pending",
  "note":"Not built, and the case strengthened again: turnover has four points with two consecutive rises, the bid series now reads 0 / 0 / 5,748 / 0 (a spike, not a recovery), and ex-pipeline withdrawal breadth hit its highest reading with the pipeline share falling from 84% to "+f"{br['pipeline_share_pct']:.0f}%"+". Three series with genuine shape."},
 {"title":"Conclusion-revision log","status":"pending",
  "note":"REVIVED after being deprioritised in run #20. The premise then was that pre-registration had eliminated corrections; this run withdrew two headline claims from run #20 (the competitive fee cut) and from runs #18-#20 (the direct-node unwind), plus an explanation repeated twice (MEX stale pricing). A revision log is the honest counterpart to the test scoreboard and the two should ship together."},
 {"title":"EGLD relative-strength (beta) tracker","status":"deprioritized",
  "note":"Deprioritised a fourth time. EGLD did outperform this week, but a single +3% week against a flat tape with a visible supply-side cause does not need a tracker to interpret."}]

recommendations=[
 f"WHERE DOES THE 229,865 EGLD UNBOND GO? One wallet unDelegated {f(UNW['legs'][0]['amount'])} from p2p_org_ and {f(UNW['legs'][1]['amount'])} from a second provider; unbonding completes in {UNW['legs'][1]['days_to_unbond']:.1f} and {UNW['legs'][0]['days_to_unbond']:.1f} days, i.e. inside the next reporting window. PRE-COMMITTED: arriving at another delegation contract = provider rotation, neutral; arriving at an exchange or an OTC feeder = a distribution event larger than this entire week's OTC one-way figure and the dominant fact of the run; staying in the wallet = idiosyncratic. Method: /accounts/{{addr}}/delegation to confirm completion, then the wallet's outbound within 72h. This is the single highest-value query of next run.",
 f"RE-NET THE JULY EPISODE FEED-TO-DRAIN. This run proved weekly netting overstates one-way movement by {wave['overstatement_pct']:.0f}% and the run #16 window shows the signature of a straddling wave (gross_in 1,305,005 > gross_out 1,100,791). Re-net runs #16-#18 as ONE window (Jul 6-27) and compare against the sum of the three weekly nets. PRE-COMMITTED: if the combined figure is materially below the ~834K the three weekly nets sum to, the July peak must be restated a second time and the five-anchor series relabelled as upper bounds; if it is close, weekly netting is adequate outside the specific Aug 3-17 pattern and the new rule applies only to waves that straddle a boundary.",
 f"DO THE 100%-FEE PROVIDERS DEREGISTER? {F1['provider']} and {F2['provider']} hold {f(F1['locked_egld']+F2['locked_egld'])} EGLD and {F1['users']+F2['users']:,} delegators earning zero. PRE-COMMITTED 2-3 week test: books halving again with flat user counts = retail inertia is absolute and the delegation market's price mechanism only reaches large holders; fee reversed = an operational move and run #20's reading was early rather than wrong; nodes deregistered = the first genuine validator exit in tracking, and the delegators' stake becomes a forced-migration flow worth tracing. Also worth ~4 queries: check whether the two owner wallets share a counterparty, since two unrelated operators making the same move in the same week is unexplained.",
 f"DOES THE OTC FEED RESUME? The tranche fell {100*(otc['upbit_feed']-otc['prev_upbit_feed'])/otc['prev_upbit_feed']:+.0f}% to {f(otc['upbit_feed'])} and the desks are returning inventory to UPbit ({f(otc['upbit_return'])}). PRE-COMMITTED: a fresh tranche above ~150,000 within two weeks = the July-August pattern is a standing programme, not two episodes; nothing above ~50,000 for two consecutive weeks = between cycles, and the historical 1-3 week reload lag becomes the thing to watch. Report the wave-window net alongside the weekly figure either way.",
 f"IS THE USDT DRAIN ONE DESK OR THE BRIDGE? USDT supply fell {df['usdt_supply_wow']:+.2f}% ({f(df['usdt_supply_prev']-df['usdt_supply'])} tokens) to {f(df['usdt_supply'])}, the largest stablecoin contraction in tracking, and the model did not trace it. Query the USDT-f8c08c largest holders and the bridge contract's flows. PRE-COMMITTED: one holder accounting for most of the redemption = idiosyncratic, note and move on; broad = the on-chain dollar base is contracting at a rate that makes ~450K remaining a first-order concern for DEX depth.",
 f"WHY IS MEX LEADING EGLD? Four consecutive weeks, and the illiquidity explanation is now falsified (MEX/WEGLD is the #{xx['mex_pair_depth']['depth_rank']} deepest pool at ${xx['mex_pair_depth']['tvl_usd']:,.0f} on {xx['mex_pair_depth']['trades_24h']} trades/24h). Check the plausible mechanisms directly: MEX total supply WoW (buyback or burn), farm emission changes, and whether the MEX/WEGLD pool's TVL is growing in EGLD terms. A DEX token outperforming its chain's native asset through a distribution episode is either a genuine rotation signal or a mechanical artifact of emissions, and the model currently cannot say which.",
 f"CORRECT THE DEMAND-SIDE READING FOR THE RECLASSIFIED WHALE. 'Unknown Whale I' is now classified as OTC operator inventory ({wi['combined_pipeline_pct']:.1f}% two-way with hub infrastructure), so its hub take must not be counted as demand in any window. Apply this retroactively to the run #17 peak (+42,206) and run #20 (+2,858) figures when they are next cited, and identify its largest external counterparty (erd1qkazru7aw5) to close the classification.",
 f"BUILD THE UNBONDING-POOL SERIES. The residual correction this run rests on a single point-in-time /accounts/{{addr}}/delegation read. Start recording, each week, the unbonding total for the wallets behind every provider move above ~20K EGLD, so the staked-minus-delegated residual can be decomposed prospectively instead of being re-explained after it flips. Roughly 10-20 queries per run and it would have prevented three runs of a wrong narrative."]

most_valuable=f"""The most valuable result is a correction of the model's own measure, not a market observation. Wave #2 of the OTC distribution was reported last week as a tripling of net one-way movement to 188,658 on a 319,000 UPbit tranche. This week the feed collapsed to {f(otc['upbit_feed'])} and the desks sent {f(otc['upbit_return'])} back to UPbit - and that return leg exposed the flaw: circularity does not respect the reporting week. Netting the wave as one window (Aug 3-17) gives {f(wave['net_one_way'])} EGLD of genuinely one-way movement against the {f(wave['sum_of_weekly_nets'])} the two weekly figures sum to, a {wave['overstatement_pct']:.0f}% overstatement, so every weekly net one-way figure the model has published is an upper bound.

The same week produced a second, larger correction. The 'direct-node unwind' - carried for three runs, described last week as the largest unexplained structural flow tracked - does not exist. The residual it was measured from (economics.staked minus summed provider locked) also contains delegation unbonding in flight, because an unDelegate removes EGLD from a provider's locked figure immediately while the EGLD stays in the staking module for 7-10 epochs. One wallet explains {f(UNW['total'])} of this week's {sk['raw_direct_residual']:+,.0f} residual flip, via two zero-value transactions whose amounts sit in the data field. Corrected for in-flight unbonding, direct-node stake GREW {sk['corrected_direct']:+,.0f}.

Add the withdrawal of run #20's 'first competitive fee cut in twenty runs' - the same provider moved 15% to 100% a week later, alongside the other named incumbent - and the falsification of the twice-repeated 'MEX is stale-priced' explanation, and this is a run in which the model corrected itself four times. That is uncomfortable but it is the correct output: three of the four corrections came from measuring one level deeper on a claim the model had already published, which is exactly the failure mode the methodology has been warning about since run #19.

The market observation worth keeping is simple and now well-evidenced: EGLD rose {pc:+.2f}% against BTC {M['btc_wow']:+.2f}% and ETH {M['eth_wow']:+.2f}% in the same week the OTC feed switched off, while the one identifiable large bid recorded literally zero transactions. Removing the marginal seller was worth roughly 3pp with no new buyer at all - which says this market has been supply-driven rather than starved of demand, and it makes the resumption of the feed, not the arrival of a bid, the thing to watch."""

meta_learning={"run_number":21,
 "endpoints_that_worked":status["ok"],"endpoints_that_failed":status["failed"],
 "api_quirks":api_quirks,"data_gaps":data_gaps,"key_findings":key_findings,
 "action_items_from_previous":8,"action_items_completed":8,
 "methodology_changes":methodology_changes,"new_addresses_discovered":2,
 "most_valuable_insight":most_valuable,
 "top_recommendation":recommendations[0],
 "recommendations_for_next_run":recommendations,
 "dashboard_feature_suggestions":dashboard_suggestions,
 "dashboard_suggestions_followup":dashboard_followup}

# ---------------- final report ----------------
otc_pipeline={"gross_outbound_egld_7d":otc["gross_out"],"gross_inbound_egld_7d":otc["gross_in"],
 "circular_egld_7d":otc["circular"],"net_one_way_egld_7d":otc["net_one_way"],
 "circular_share_pct":otc["circ_pct"],
 "desk_balance_egld":otc["desk_balance"],"previous_desk_balance_egld":otc["desk_balance_prev"],
 "upbit_reload_egld":otc["upbit_feed"],
 "venue_netting":[{"venue":v,"desk_to_venue_egld":otc["outbound_by_venue"].get(v,0),
                   "venue_to_desk_egld":otc["inbound_by_venue"].get(v,0),
                   "net_egld":otc["net_by_venue"][v]} for v in sorted(otc["net_by_venue"])],
 "gross_series_egld_7d":otc["gross_series"],
 "net_one_way_series_egld_7d":otc["net_series"],
 "circularity_series_pct":otc["circ_series_pct"],
 "peak_window_renetted":{"window":"2026-07-13..2026-07-20 (run #17 peak)","gross_egld":otc["peak"]["gross"],
   "circular_egld":otc["peak"]["circ"],"net_one_way_egld":otc["peak"]["net"],
   "circular_share_pct":otc["peak"]["circ_pct"],"net_by_venue":otc["peak"]["net_by_venue"]},
 "backfilled_windows":[
   {"window":"2026-07-06..2026-07-13 (run #16)","gross_egld":otc["run16"]["gross"],
    "circular_egld":otc["run16"]["circ"],"net_one_way_egld":otc["run16"]["net"],
    "circular_share_pct":otc["run16"]["circ_pct"],"net_by_venue":otc["run16"]["net_by_venue"]},
   {"window":"2026-07-20..2026-07-27 (run #18)","gross_egld":otc["run18"]["gross"],
    "circular_egld":otc["run18"]["circ"],"net_one_way_egld":otc["run18"]["net"],
    "circular_share_pct":otc["run18"]["circ_pct"],"net_by_venue":otc["run18"]["net_by_venue"]}],
 "wave_window_netting":{"window":wave["window"],"gross_outbound_egld":wave["gross_out"],
   "gross_inbound_egld":wave["gross_in"],"circular_egld":wave["circular"],
   "circular_share_pct":wave["circ_pct"],"net_one_way_egld":wave["net_one_way"],
   "sum_of_weekly_nets_egld":wave["sum_of_weekly_nets"],
   "weekly_frame_overstatement_egld":wave["weekly_frame_overstatement"],
   "weekly_frame_overstatement_pct":wave["overstatement_pct"],
   "net_by_venue":wave["net_by_venue"],
   "note":"Wave #2 netted feed-to-drain across both of its weeks. Circularity crosses week boundaries (UPbit fed 319,000 in the first week and took 130,000 back in the second), so weekly net one-way figures are UPPER BOUNDS. Report both."},
 "series_note":f"GROSS series (runs #12-#21) is paginated and net of desk-to-desk transfers only. NET one-way now has FIVE measured anchors: run #16 {f(otc['run16']['net'])}, run #17 peak {f(otc['peak']['net'])}, run #18 {f(otc['run18']['net'])}, run #19 61,435, run #20 {f(otc['prev_net'])}, run #21 {f(otc['net_one_way'])}. Circularity measured at {otc['run16']['circ_pct']:.0f}% / {otc['peak']['circ_pct']:.0f}% / {otc['run18']['circ_pct']:.0f}% / 80% / {otc['circ_series_pct']['run20']:.0f}% / {otc['circ_pct']:.0f}%; the last is the outlier because this week contained a return leg whose feed sat in the prior window. Never compare a gross figure to a net one, and prefer the wave-window net to any weekly net."}

demand_instruments={"identifiable_bid_absorbed_egld_7d":bid["absorbed"],
 "mega_whale_balance_egld":bid["mega_balance"],"mega_whale_change_egld":bid["mega_change"],
 "coinbase_routing_balance_egld":bid["cb_routing_balance"],
 "coinbase_routing_inflow_egld":bid["cb_routing_inflow"],
 "coinbase_routing_funder":None,"coinbase_routing_funder_label":"no inflow this week",
 "weeks_at_zero":1,"weeks_at_zero_in_last_four":bid["weeks_at_zero_in_last_four"],
 "bid_to_distribution_ratio_pct":0.0,
 "dex_turnover_ratio_pct":xx["turnover_ratio_pct"],
 "previous_dex_turnover_ratio_pct":xx["previous_turnover_ratio_pct"],
 "withdrawal_breadth":O["breadth"],"withdrawal_breadth_top":O["breadth_top"]}

report={
 "metadata":{"report_date":"2026-08-17","period_start":"2026-08-10","period_end":"2026-08-17",
   "generated_at":datetime.now(timezone.utc).isoformat(),"egld_price_usd":price,
   "btc_price_usd":M["btc"],"eth_price_usd":M["eth"],"run_number":21,
   "data_sources_ok":status["ok"],"data_sources_failed":status["failed"]},
 "executive_summary":P4["executive_summary"],
 "network_health":P4["network_health"],
 "whale_intelligence":{"large_transactions":O["large_transactions"],"wallet_changes":O["wallet_changes"],
   "whale_tiers":O["whale_tiers"],"exchange_flows":P4["exchange_flows"],
   "dormant_activations":[],"otc_pipeline":otc_pipeline,
   "demand_instruments":demand_instruments,"analysis":P4["whale_analysis"]},
 "staking_intelligence":{"summary":{"total_staked_egld":M["staked"],
   "total_delegated_egld":sk["total_locked"],"staked_ratio":M["sr"],"num_providers":sk["n_providers"],
   "apr_min":0.0,"apr_max":max(p["apr_pct"] for p in sk["top_apr"]),"apr_weighted_avg":sk["apr_w"]},
   "top_providers":sk["top_providers"],
   "concentration":{"top_5_share_pct":sk["top5"],"top_10_share_pct":sk["top10"],"hhi":sk["hhi"],
     "hhi_previous":prev["staking_concentration"]["hhi"],"hhi_interpretation":"competitive"},
   "apr_distribution":{"buckets":sk["buckets"],
     "zero_apr_providers":sk["zero_apr_providers"],"zero_apr_locked_egld":sk["zero_apr_locked"]},
   "apr_outliers":{"top_apr":sk["top_apr"],"lowest_fee":sk["lowest_fee"]},
   "churn":sk["churn"],
   "fee_events":sk["fee_events"],
   "unbonding_in_flight":{"wallet":sk["unwind"]["address"],"total_egld":sk["unwind"]["total"],
     "legs":sk["unwind"]["legs"],
     "share_of_delegation_decline_pct":sk["unwind"]["share_of_delegation_decline_pct"],
     "raw_residual_egld":sk["raw_direct_residual"],
     "corrected_direct_node_egld":sk["corrected_direct"]},
   "analysis":P4["staking_analysis"]},
 "token_activity":{"top_by_holders":O["tokens"]["top_by_holders"],
   "top_by_volume":O["tokens"]["top_by_volume"],
   "top_by_market_cap":O["tokens"]["top_by_market_cap"],
   "newly_issued":O["tokens"]["newly_issued"],"xexchange":xx,"analysis":P4["token_analysis"]},
 "defi_activity":{"protocols":P4["protocols"],"protocol_breakdown":P4["protocol_breakdown"],
   "sc_deployments":[],"analysis":P4["defi_analysis"]},
 "anomalies":P3["anomalies"],
 "trend_indicators":P3["trend_indicators"],
 "watch_list":watch_list,
 "meta_learning":meta_learning}

json.dump(report,open(f"{REPO}/reports/2026-08-17.json","w"),indent=2)
print("WROTE reports/2026-08-17.json")
print("exec",len(report["executive_summary"]),"anomalies",len(report["anomalies"]),
      "watch",len(report["watch_list"]),"largetx",len(report["whale_intelligence"]["large_transactions"]),
      "providers",len(report["staking_intelligence"]["top_providers"]))
