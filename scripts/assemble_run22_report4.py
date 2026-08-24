#!/usr/bin/env python3
"""Run #22 stage 5: meta_learning + pre_committed_tests, then merge into reports/2026-08-24.json"""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-08-24"
O=json.load(open("/tmp/run22w/derived.json"))
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
status=json.load(open("/tmp/run22w/status.json"))
F=json.load(open(f"{REPO}/data/collected/followup_{RD}.json"))
beh=json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
r21=json.load(open(f"{REPO}/reports/2026-08-17.json"))
M=O["macro"]; otc=O["otc"]; wave=otc["wave"]; july=otc["july"]; ex=O["exch"]
cust=O["custody"]; bid=O["bid"]; br=O["breadth"]; sk=O["staking"]; tk=O["tokens"]
xx=O["xexchange"]; df=O["defi"]
price=M["price"]; pc=M["price_chg"]
cvc=beh["aggregates"]["compound_vs_claim_at_function_level"]
def f(x,d=0):
    try: return f"{x:,.{d}f}"
    except: return str(x)

# ---- resolve run #21's open tests, register run #22's --------------------
prior={t["id"]:t for t in r21["pre_committed_tests"]}
tests=[t for t in r21["pre_committed_tests"] if t["status"]=="resolved"]

def resolve(tid,outcome,measured,resolution):
    t=dict(prior[tid]); t.update({"status":"resolved","outcome":outcome,"resolved_in_run":22,
        "measured_value":measured,"resolution":resolution}); return t

tests.append(resolve("unbond-destination","inconclusive",
  f"unmoved: 80,279 fully unbonded (seconds_remaining = 0) and 149,585 with 5,279s left, both still inside the delegation contracts; wallet balance {f(F['run21_unbond_wallet']['balance_egld'],0)} EGLD, zero outbound transactions",
  "NONE of the three branches fired, because a fourth state existed that the test did not anticipate: the holder never withdrew. The EGLD is not in a delegation contract as active stake, not at an exchange, and not in the wallet - it is unbonded and unclaimed inside the contracts it was undelegated from. The test was specified on a destination and the answer is that there is not yet a destination. LESSON: a destination test needs a no-action branch with a time bound, or it cannot resolve when the counterparty simply does nothing. Re-registered below with that branch added."))

tests.append(resolve("otc-feed-resumption","as_predicted",
  f"UPbit tranche {f(otc['upbit_feed'])} EGLD in week one of the two-week window, against a ~150,000 threshold; gross throughput {f(otc['gross_out'])} (3.4x), desks reloaded +{f(otc['desk_delta'])} to {f(otc['desk_bal'])}",
  f"The standing-programme branch fired at nearly double its threshold and a week early. The July-August pattern is a programme with pauses, not two discrete episodes. Circularity returned to {otc['circ_pct']:.0f}%, inside the historical 63-80% band, which is itself confirmation of run #21's diagnostic that the anomalous 38% reading was a straddling return leg rather than a change in how the hub works."))

tests.append(resolve("usdt-drain","as_predicted",
  f"USDT supply {f(tk['stable']['USDT-f8c08c']['supply'])}, {100*(tk['stable']['USDT-f8c08c']['supply']-549884)/549884:+.2f}% - recovered rather than contracting further",
  "The flat-or-positive branch fired. Run #21's -15.42% was one desk redeeming, not the bridge draining. Holder inspection supports it: the top 25 addresses hold 82% of supply and the largest single holder is Hatom's USDT Money Market at 118,671, so the base is concentrated enough for one position to move it double digits. The ~450K first-order-concern scenario is withdrawn."))

tests.append(resolve("dex-turnover-recovery","as_predicted",
  f"turnover {bid['turnover']:.2f}% against a ~3.5% threshold; series 4.06 / 2.14 / 2.24 / 2.93 / {bid['turnover']:.2f}",
  f"The third-rise branch fired and then some - not a recovery to the old level but a step change past it, on volume +{100*(bid['dexvol']-bid['prev_dexvol'])/bid['prev_dexvol']:.0f}% with pool depth also up {100*(bid['pooltvl']-bid['prev_pooltvl'])/bid['prev_pooltvl']:.1f}%. CAVEAT the test did not anticipate: it fired in the same week as a +30% price move and a restarted OTC feed, so 'the demand side is genuinely repairing' is confounded with 'there was a rally'. The persistence test registered below is what separates them."))

tests.append(resolve("mex-relative-strength","as_predicted",
  f"MEX {xx['mex_wow']:+.2f}% vs EGLD {pc:+.2f}% - a fifth consecutive week at or above, by 0.08pp; cumulative over the five weeks MEX +23.73% vs EGLD +13.92%",
  f"The threshold fired on the letter and the cumulative gap of ~9.8pp is material rather than noise. The reading the branch prescribed - identify the mechanism - was attempted and came back EMPTY. MEX supply moved {100*(tk['mex_supply']-tk['mex_prev_supply'])/tk['mex_prev_supply']:+.3f}%, three orders of magnitude too small to price the gap, and MEX/WEGLD pool depth grew roughly with the market (${f(xx['mex_pair_depth']['tvl_usd'])}, rank {xx['mex_pair_depth']['depth_rank']}) rather than ahead of it. So the statistical claim survives and the causal one does not exist yet; per the run #21 rule the model states that rather than reaching for a third explanation."))

# carried open
t=dict(prior["hundred-pct-fee-providers"])
t["measured_value"]=(f"week 1 of 2-3: procryptostaking {f(next(m['delta'] for m in sk['moves'] if m['identity']=='procryptostaking'))} (-9.6%, users -35), "
  f"egldstakingprovider {f(next(m['delta'] for m in sk['moves'] if m['identity']=='egldstakingprovider'))} (-15.6%, users -32); fee still 1.0, APR still 0, 50 nodes each. "
  f"Owner wallets hold 1.69 EGLD each, received nothing in 30d, and sent one small transfer each (511 and 698 EGLD) to two DIFFERENT unlabelled recipients - no shared counterparty on the available evidence.")
tests.append(t)

def new(tid,claim,threshold,branches,measured):
    return {"id":tid,"registered_in_run":22,"claim":claim,"threshold":threshold,
            "branches":branches,"status":"open","outcome":None,"resolved_in_run":None,
            "measured_value":measured,"resolution":None}

tests += [
 new("unbond-withdrawal",
  "The 229,865 EGLD, now fully unbonded and claimable, is a live forward flow rather than an abandoned position.",
  "withdrawn and sent to an exchange or OTC feeder within the window = a 230K distribution event on top of a restarting pipeline; withdrawn and redelegated = rotation, neutral; STILL UNWITHDRAWN after this second full week = an inactive or lost-access holder, and the overhang is retired as a forward flow",
  [{"condition":"withdrawn to exchange/OTC feeder","reading":"230K distribution, dominant fact of the run"},
   {"condition":"withdrawn and redelegated","reading":"provider rotation - neutral"},
   {"condition":"still unwithdrawn after a second full week","reading":"inactive holder; stop tracking it as a live flow"}],
  "80,279 at seconds_remaining = 0, 149,585 at 5,279s; wallet sent zero outbound transactions in the Aug 17-24 window"),
 new("otc-wave3-escalation",
  "Wave #3 escalates toward the re-netted run #17 peak (409,680 one-way) rather than stopping at one reload.",
  "another UPbit tranche above ~150,000 next week = escalating, and the supply overhang is the dominant fact; nothing above ~50,000 = the 297,000 was a single reload and the desks work down their record inventory",
  [{"condition":"tranche > 150K again","reading":"wave #3 escalating to run #17 scale"},
   {"condition":"nothing > 50K","reading":"single reload; watch the desks drain the record 109,857"}],
  f"this week's tranche {f(otc['upbit_feed'])}; desk inventory {f(otc['desk_bal'])} (record); weekly net one-way {f(otc['net_one_way'])}"),
 new("custody-drawdown-follow-through",
  "The 300,000 Binance custody drawdown is the funding leg of distribution rather than internal rebalancing.",
  "the Binance.com hot wallet falling more than ~150,000 next week while the OTC feed continues = the two channels are one programme; hot flat or the custody re-parked = internal rebalancing and the bearish branch over-reads a plumbing move",
  [{"condition":"hot falls >150K with OTC feed continuing","reading":"custody drawdown funds distribution - one programme"},
   {"condition":"hot flat or custody re-parked","reading":"internal rebalancing; the pre-registered branch over-reads plumbing"}],
  f"custody {f(cust['balance'])} ({f(cust['delta'])}), hot {f(cust['hot_balance'])} (+{f((cust['hot_balance'] or 0)-(cust['hot_previous'] or 0))}); binance_staking provider took only +2,422"),
 new("p2p-org-delegator-migration",
  "The 1,244 delegators stranded on p2p_org_'s zero-stake contract will move, breaking participation inertia where a 100% fee did not.",
  "more than ~25% of the 1,244 users leaving the contract within two weeks = a total loss of yield DOES break inertia and the stake becomes a traceable forced-migration flow; fewer than ~10% = inertia survives even total yield loss, which is the strongest possible reading of it",
  [{"condition":">25% of users leave in 2 weeks","reading":"inertia breaks at total yield loss; trace the migration flow"},
   {"condition":"<10% leave","reading":"inertia is near-absolute; the delegation market has no working price mechanism for retail"}],
  "p2p_org_ locked 0, APR 0, 1,244 users still attached, 50 nodes still listed after unStakeNodes"),
 new("dex-turnover-persistence",
  "The turnover step change is a demand regime shift rather than a rally-week volume spike.",
  "holding above ~5% next week = a genuine regime change and the absent-bid diagnosis carried since run #18 is retired; falling back below 3.5% = a spike that tracked the price move and the 2-4% band is the real level",
  [{"condition":"turnover > 5%","reading":"regime change - retire the absent-bid diagnosis"},
   {"condition":"turnover < 3.5%","reading":"rally-week spike; the 2-4% band stands"}],
  f"turnover {bid['turnover']:.2f}% on volume ${f(bid['dexvol'])} (+{100*(bid['dexvol']-bid['prev_dexvol'])/bid['prev_dexvol']:.0f}%) and pool TVL ${f(bid['pooltvl'])} (+{100*(bid['pooltvl']-bid['prev_pooltvl'])/bid['prev_pooltvl']:.1f}%)"),
 new("mex-mechanism",
  "MEX's five-week outperformance of EGLD has a mechanical cause the model can measure.",
  "MEX/WEGLD pool TVL growing more than 10% WoW in EGLD terms OR MEX supply falling more than 1% = a mechanical explanation (liquidity migration or a real burn); NEITHER, for a second consecutive run of looking = the outperformance is unexplained flow and must be labelled as such rather than re-explained",
  [{"condition":"pool TVL +10% in EGLD terms or supply -1%","reading":"mechanical - name it and close the question"},
   {"condition":"neither, second run running","reading":"unexplained flow; stop generating explanations"}],
  f"supply {100*(tk['mex_supply']-tk['mex_prev_supply'])/tk['mex_prev_supply']:+.3f}%, pool TVL ${f(xx['mex_pair_depth']['tvl_usd'])} (grew with the market), 5-week cumulative gap ~9.8pp"),
 new("compound-rate-break",
  "The three-week decline in the reward compound rate is delegators tracking price strength rather than noise.",
  "below 56% next week = a systematic shift toward monetising yield and the compound rate is a price-following series; back above 59% = a single rally-week claim spike",
  [{"condition":"compound < 56%","reading":"systematic monetisation; the series follows price"},
   {"condition":"compound > 59%","reading":"rally-week spike, mean-reverting"}],
  f"{cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} redelegate vs {cvc['claim_count']} claim), lowest of nine; institutional tier sold 3 of 4 claims by count"),
]

resolved=[t for t in tests if t["status"]=="resolved" and t.get("resolved_in_run")==22]
as_pred=sum(1 for t in resolved if t["outcome"]=="as_predicted")
hit=100*as_pred/len(resolved)

R={"pre_committed_tests":tests}
R["meta_learning"]={
 "run_number":22,
 "endpoints_that_worked":status["ok"],
 "endpoints_that_failed":status["failed"],
 "api_quirks":[
  "previous.json stores staking providers keyed by IDENTITY (or the address when there is no identity), NOT by contract address. Joining the live /providers list on `provider` (the address) silently produces a near-total mismatch - the first pass this run reported 79 providers as having moved more than 20K EGLD and found zero unDelegate callers. The correct key is `identity or provider`.",
  "A provider that calls unStakeNodes does NOT disappear from /providers. It stays listed with numNodes unchanged (p2p_org_ still shows 50), stake and topUp and locked all zero, apr 0, and numUsers unchanged at 1,244. Any 'providers leaving' count built on set membership will miss it entirely; the detectable signature is locked going to zero with numNodes > 0.",
  "unStakeNodes appears as a normal function on the provider contract's INBOUND transaction list, alongside delegate / unDelegate / claimRewards. It is the operator-side counterpart to the delegator-side unDelegate and is the only visible marker of a deregistration.",
  "/accounts/{addr}/delegation reports a completed unbonding as userUnBondable > 0 with a userUndelegatedList entry at seconds = 0. The EGLD is claimable but has NOT left the contract, and it appears in neither the wallet balance nor the provider's locked figure - it sits in the staking module and therefore inside economics.staked.",
  "SWTAO-356a25 returned price and marketCap null from /tokens/SWTAO-356a25 through the main pass AND all four isolated 2.5s retries - but the /tokens?sort=marketCap LIST endpoint returned a live price ($305.80) and marketCap for the SAME token in the SAME run. The two endpoints disagree about whether a price exists. This supersedes the run #14 prior-price carry-forward as the first-choice fallback: cross-check the list endpoints before deriving an estimate, because a measured value beats a derived one.",
  "The delegator_behavior collector requests 8 providers but reports providers_sampled 7 in its aggregates when one has no usable inbound window; the metadata block still says 8. Read the aggregates figure, not the metadata one.",
  "/tokens/{id}/accounts returns balances in the token's own decimals as raw strings - USDT and USDC are 6-decimal, so divide by 1e6, not 1e18.",
  "The page-cap guard fired once, on a Binance hot wallet in the withdrawal-breadth scan: 400 transactions covering only 2.4 days of a 7-day window. Any breadth total including that address is a lower bound and must be labelled one.",
  "The two long-flagged invalid bech32 entries (Hatom UTK Money Market, OneDex Launchpad) still fail pre-flight validation, unchanged since run #18. They remain flagged rather than guessed."],
 "data_gaps":[
  "The unbonding-pool measurement covers the ten providers that moved more than 5,000 EGLD, not all 105. Gross weekly unDelegation across the whole set is therefore higher than the 70,498 reported, which is why the residual is described as fully absorbed rather than decomposed to a number.",
  "One Binance hot-wallet breadth scan hit the page cap at 2.4 days of coverage; raw withdrawal breadth is a lower bound.",
  
  "Whether p2p_org_'s 1,244 delegators have acted is not observable this week - their stake reads zero because the contract's stake is zero, not because they withdrew.",
  "MEX's outperformance has no measured mechanism after two runs of looking; the model states the gap rather than explaining it.",
  "Hatom UTK Money Market and OneDex Launchpad remain excluded from protocol address sets pending valid addresses."],
 "key_findings":[
  f"EGLD {pc:+.2f}% to ${price:.2f}, the largest weekly move in twenty-two runs, and a beta move rather than an EGLD-specific one (BTC {M['btc_wow']:+.2f}%, ETH {M['eth_wow']:+.2f}%).",
  f"The OTC distribution pipeline restarted into the rally: UPbit fed {f(otc['upbit_feed'])} EGLD against 14,000 last week, gross throughput {f(otc['gross_out'])}, net one-way {f(otc['net_one_way'])}, desks reloaded to a record {f(otc['desk_bal'])}.",
  f"Binance's staking custody drew down {f(cust['delta'])} into its hot wallet - the pre-registered bearish branch firing for the second time since run #9.",
  "p2p_org_ called unStakeNodes and went to zero locked with 1,244 delegators still attached - the first operator deregistration in tracking.",
  "The 229,865 EGLD unbond did not move; it is unbonded and unwithdrawn inside the delegation contracts, a state none of the three pre-registered branches covered.",
  f"DEX turnover tripled to {bid['turnover']:.2f}% on volume +{100*(bid['dexvol']-bid['prev_dexvol'])/bid['prev_dexvol']:.0f}% with depth also rising - the first constructive reading any demand instrument has produced.",
  f"The two demand instruments contradicted each other: turnover tripled while the identifiable bid read zero for a second week. The single-wallet proxy is no longer informative.",
  f"Weekly OTC netting is NOT systematically biased: the July episode re-netted feed-to-drain gives {f(july['net_one_way'])} against {f(july['sum_weekly'])} summed weekly, {abs(july['overstate_pct']):.2f}% apart. Run #21's blanket upper-bound rule is narrowed to waves that straddle a week boundary.",
  f"The extended August wave (Aug 3-24) DOES straddle: {f(wave['net_one_way'])} netted against {f(wave['sum_weekly'])} summed, {wave['overstate_pct']:.1f}% overstatement.",
  f"Reward compound rate fell to {cvc['compound_pct_of_reward_decisions']:.2f}%, lowest of nine and a third consecutive decline, with the institutional tier selling 3 of 4 claims - delegators monetised yield into strength.",
  f"The bilateral inverse rule took a third up-week confirmation at its weakest response ratio yet ({df['inverse_ratio']:.2f}), below the 0.30 depositor-capacity threshold.",
  f"USH burned {tk['lsd']['USH-111e09']['pct']:+.2f}% INTO a +30% rally - CDP borrowers repaying as collateral appreciated, a sign combination neither the run #11 nor run #16 framing covers.",
  "USDT recovered +0.44%, resolving run #21's contraction as one desk redeeming rather than the bridge draining.",
  f"The delegator count's apparent nine-week-streak break is an artifact: {sk['p2p_users']:,} of the {abs(sk['users_delta']):,} are p2p_org_'s users leaving the locked>0 working set. Ex-p2p_org_ the base moved {sk['users_ex_p2p']:+,}.",
  f"The staked-minus-delegated residual ({f(sk['residual'])}) is fully absorbed by unbonding in flight - p2p_org_'s {f(abs(sk['p2p_prev_locked']))} node unstake plus at least {f(sk['undelegated_week'])} of delegator unDelegations - so no direct-node figure is published, and run #21's +52,848 is withdrawn as an incomplete subtraction.",
  "Unknown Whale I's largest external counterparty turns out to be a second wallet of the same operator, closing the classification as OTC inventory.",
  f"{as_pred} of {len(resolved)} pre-committed tests resolved this run fired as predicted ({hit:.1f}%); one resolved inconclusive because the counterparty simply did nothing and the test had no no-action branch."],
 "action_items_from_previous":10,
 "action_items_completed":8,
 "methodology_changes":[
  "JOIN PROVIDERS ON IDENTITY, NOT ADDRESS. previous.json keys staking_providers by identity; the live API keys by contract address. Joining wrong is silent and catastrophic - it reported 79 phantom 20K+ movers and found zero unDelegate callers on the first pass this run.",
  "A DEREGISTERED PROVIDER STAYS IN /providers. Detect it as locked == 0 with numNodes > 0, and confirm with an unStakeNodes call on the contract's inbound list. Set-membership 'providers leaving' logic misses it.",
  "NET A DEREGISTERED PROVIDER OUT OF BOTH DELEGATION TVL AND THE DELEGATOR COUNT. Its users leave the locked>0 working set without undelegating, which manufactures a break in the delegator series. Report the count both ways.",
  "AN UNBONDING CAN COMPLETE AND STILL NOT MOVE. userUnBondable > 0 with seconds = 0 means claimable-but-unclaimed; the EGLD stays inside the staking module and inside economics.staked. A destination test needs an explicit no-action branch with a time bound or it cannot resolve.",
  "RECOVER NULL TOKEN PRICES FROM THE LIST ENDPOINTS BEFORE DERIVING THEM. /tokens/{id} and /tokens?sort=marketCap can disagree about whether a price exists; this run the list had SWTAO at $305.80 while the per-token endpoint nulled through four retries. Check the lists first, then fall back to the run #11 accumulator ratio, then to the run #14 prior-price carry-forward.",
  "NARROW RUN #21'S WEEKLY-NETTING RULE. Weekly netting is accurate unless a wave straddles a week boundary - the July episode re-netted to within 0.47% of the sum of its weekly nets while the August wave overstates by 47.7%. Test the wave, do not assume the frame.",
  "DO NOT PUBLISH A CORRECTED DIRECT-NODE FIGURE FROM A PARTIAL UNBONDING SUBTRACTION. Run #21 subtracted one wallet and published +52,848; the correct statement when the measured unbonding exceeds the residual is that the residual carries no direct-node signal.",
  "WHEN TWO INSTRUMENTS FOR THE SAME QUANTITY DISAGREE, SAY WHICH ONE IS BETTER MEASURED AND WHY. Turnover covers a whole venue and is price-independent; the identifiable bid is one wallet. Reporting them as a contradiction without adjudicating is a non-answer."],
 "new_addresses_discovered":3,
 "most_valuable_insight":(
  "The week's most valuable result is that a +30% rally arrived with distribution rather than accumulation, and every instrument that could distinguish them agreed. "
  "The OTC pipeline restarted at 297,000 into the move and the desks ended with record inventory still loaded. Binance's staking custody drew down 300,000 to its hot wallet, the branch pre-registered as bearish since run #9. "
  "Hatom depositors withdrew, CDP borrowers repaid, delegators claimed instead of compounding, and no LSD took a single measurable subscription. "
  "The one instrument pointing the other way - DEX turnover tripling - measures trading rather than holding, and trading is what you would expect on both readings. "
  "The structural point is that this chain's holders used a 30% move to reduce exposure, and the supply that funded it is visible, named and only partly delivered."),
 "top_recommendation":(
  "Resolve the unbond-withdrawal test and the wave-#3 escalation test in the same pass, because they may be the same flow. "
  "229,865 EGLD is claimable and unclaimed at the exact moment a distribution pipeline restarted with a record 109,857 of desk inventory still loaded. "
  "If the withdrawal lands and routes to an OTC feeder, that is a single event larger than this week's entire one-way figure and it converts two separate watches into one."),
 "recommendations_for_next_run":[
  "MAINTAIN THE SCOREBOARD AND ERRATA. Resolve the 8 open pre_committed_tests, register run #23's before seeing the data, and append the prediction record to running_baselines. This run resolved 5 of run #21's 6 and carried 1 forward; note that the one inconclusive resolution was caused by a missing no-action branch, which is now a standing design rule for destination tests.",
  "RESOLVE THE UNBOND AND WAVE #3 TOGETHER. 229,865 EGLD is claimable-and-unclaimed while the desks hold a record 109,857 loaded. Query /accounts/erd1daqlaezxx22rzyxnqx5ddkykm5ajelt0hetjnstm7rxqg78xqusqazv9ms/delegation for withdrawal, then its outbound within 72h, and check whether any receiver appears in the desk inbound list. If they are the same flow it is the largest single event the pipeline has carried.",
  "TRACE P2P.ORG'S 1,244 STRANDED DELEGATORS. The contract has zero stake and zero APR. Enumerate the callers on its contract (withdraw / unDelegate / delegate) over the next two weeks and count how many of the 1,244 act. This is the cleanest natural experiment on participation inertia the model will get: a 100% fee moved 26% of a book and 1% of its users; a dead contract is the limit case. Also check whether owner erd1jxuc98ud0pe7 relates to the two 100%-fee operators.",
  "BUILD THE UNBONDING QUEUE ACROSS ALL PROVIDERS, NOT JUST THE MOVERS. This run measured 70,498 across ten providers and could only say the residual was 'fully absorbed'. Querying unDelegate calls on all 105 contracts is roughly 105 paged queries - expensive but it turns the residual from an uninterpretable number into a decomposition, and it is the only forward-looking series the report has.",
  "SEPARATE THE TURNOVER SIGNAL FROM THE RALLY. Turnover tripled in the same week as a +30% price move and a restarted OTC feed, so the constructive reading is confounded. Record volume in EGLD terms as well as USD, and record the WEGLD/USDC pair's volume separately from the rest, so a repeat can be attributed to venue demand rather than to price.",
  "STOP EXPLAINING MEX AND START BOUNDING IT. Two runs have now looked for a mechanism and found none - supply moves are three orders of magnitude too small and pool depth grew with the market. Per the run #21 rule about repeated explanations, the next run should either measure MEX/WEGLD pool TVL in EGLD terms and farm emissions directly, or label the 9.8pp five-week gap as unexplained flow and stop.",
  "RETIRE OR REPAIR THE IDENTIFIABLE-BID INSTRUMENT. It has read zero in three of the last four weeks including one where DEX turnover tripled. Either widen it to a set of absorber wallets discovered dynamically from the desks' outbound terminals, or drop it and let turnover plus ex-pipeline withdrawal breadth carry the demand read. Reporting a broken proxy alongside a working one every week is narrative cost.",
  "WATCH THE HATOM RESPONSE RATIO FOR A SECOND SUB-0.30 READING. The bilateral inverse rule confirmed correctly but at 0.28, below the capacity-exhaustion threshold. Two consecutive sub-0.30 readings on |dPrice| >= 5% weeks means the deposit base the rule depends on has been drawn down and the rule should be retired rather than re-confirmed - which would be a cleaner outcome than letting it decay into a formality.",
  "ADD A PAGE-CAP BUDGET FOR THE BREADTH SCAN. One Binance hot wallet covered 2.4 days of a 7-day window at max_pages=8. Raise the cap for exchange hot wallets specifically, or accept and label the lower bound explicitly in the field name rather than in a caveat.",
  "CHECK WHETHER THE BINANCE 300,000 REACHES THE DESKS. The custody drawdown and the OTC restart happened in the same week and the model has not connected them. Trace the Binance.com hot wallet's outbound above 10,000 EGLD and test against the desk inbound list; a link would make the custody watch and the pipeline watch one instrument instead of two."],
 "dashboard_feature_suggestions":[
  {"title":"Unbonding queue table with a settlement calendar",
   "motivation":"Run #21's unbonding card was deliberately one number because there was one observation. This run there are 158 distinct unDelegate callers moving 70,498 EGLD with settlement dates spread over 2-8 days, plus a 229,865 position that has completed unbonding and simply not been claimed - a state the card cannot express at all. The card now understates the thing it exists to show, and the claimable-but-unclaimed distinction is the single most decision-relevant fact in it.",
   "suggested_visualization":"a table of the largest legs (amount, source provider, days remaining, wallet balance) beside a small stacked bar of EGLD becoming liquid per upcoming day, with a separate CLAIMABLE NOW band pinned at day zero for completed-but-unwithdrawn positions.",
   "data_already_available":True,
   "data_source":"staking_intelligence.unbonding_in_flight.queue_this_week (new this run: undelegated_egld, distinct_callers, measured_pending_egld, largest_legs with days_remaining) plus the existing legs array",
   "priority":"high"},
  {"title":"Demand instruments panel - and make it show the disagreement",
   "motivation":"Pending for three runs, and this week is the one that makes the case: DEX turnover tripled to 10.83% while the identifiable bid read exactly zero and ex-pipeline withdrawal breadth fell to 21 recipients with the pipeline share jumping to 88.3%. Three series, all with real shape, pointing in different directions in the same week - and the report has to spend a paragraph adjudicating between them because there is no view where a reader can see it. The adjudication (turnover measures a venue and is price-independent; the bid measures one wallet) is exactly what a shared-axis panel would make obvious.",
   "suggested_visualization":"three small multiples on a shared week axis - turnover %, identifiable bid EGLD, ex-pipeline breadth recipients - with the pipeline-share % as a shaded band behind the breadth series, and weeks where the instruments disagree in sign marked.",
   "data_already_available":True,
   "data_source":"whale_intelligence.demand_instruments (dex_turnover_ratio_pct, identifiable_bid_absorbed_egld_7d, withdrawal_breadth) across reports, plus the running_baselines arrays",
   "priority":"high"},
  {"title":"Provider lifecycle strip",
   "motivation":"p2p_org_ went from 1,244 delegators and 67,500 EGLD of node stake to zero locked via unStakeNodes, and the dashboard renders that as a single 'notable leaver' row with a previous-locked number. It cannot show that the nodes are still registered, the users are still attached, the APR is now zero, and the book did not drain - the operator left. Two 100%-fee providers are in a related state (paying nothing, keeping their books) and there is no view that connects them.",
   "suggested_visualization":"a compact strip of provider states - healthy / fee-squeezed / zero-APR / deregistered - with each affected provider as a chip carrying locked, users and weeks-in-state, so a reader sees the distressed end of the validator set as a group rather than as scattered rows.",
   "data_already_available":False,
   "data_source":"derivable from /providers (locked, numNodes, apr, serviceFee, numUsers) but needs a new staking_intelligence.provider_states array carrying the state label and weeks_in_state",
   "priority":"medium"}],
 "dashboard_suggestions_followup":[
  {"title":"Wave-window OTC netting (feed-to-drain) alongside the weekly series","status":"built",
   "note":"Built in run #21 and it earned itself immediately - the July re-net this run needed exactly that panel to show that weekly framing was ACCURATE for July while the August wave straddles. The bracket is now carrying two waves with opposite verdicts, which is more than the original proposal anticipated."},
  {"title":"Delegation unbonding queue","status":"pending",
   "note":"The CARD was built in run #21 with the graduation condition stated explicitly: it becomes a table when the collector records the pool weekly. That collector change shipped this run (158 callers, 70,498 EGLD, settlement dates), so the graduation condition is met and the table is this run's top suggestion."},
  {"title":"Pre-committed test scoreboard","status":"built",
   "note":"Built in run #21, load-bearing this run. It resolved five run #21 tests, carried one open into week two, and registered seven new ones. The inconclusive outcome earned its place again: the unbond test could not resolve because it had no no-action branch, and having to record that in structure rather than prose is what produced the design rule."},
  {"title":"Errata overlay on superseded reports","status":"built",
   "note":"Built in run #21 and used this run for two withdrawals - run #21's own +52,848 direct-node figure and its blanket weekly-netting rule. Notable that both withdrawals are of run #21 claims by run #22, so the overlay is now correcting the run that built it, which is the behaviour it was designed for."},
  {"title":"OTC hub flow map: gross vs net one-way, with venue-level netting","status":"pending",
   "note":"Still not built and the case is stronger again: this week UPbit is a -297,000 net source while Bybit (+132,402), Binance.com (+81,652) and Gate.io (+28,346) are receivers, and the same venues invert across the wave boundary. A chord or Sankey makes a source-to-sink structure legible where a signed table does not."},
  {"title":"Conclusion-revision log","status":"built",
   "note":"Shipped as the errata overlay in run #21; see above."},
  {"title":"EGLD relative-strength (beta) tracker","status":"deprioritized",
   "note":"Deprioritised a fifth time, and this week is the cleanest reason yet: EGLD +30.43% landed between BTC +23.78% and ETH +30.67%, which is a one-line observation in the network-health narrative. A tracker would have shown a flat line through the largest price move in the series."}],
 "withdrawn_claims":[
  {"claim":"Corrected for in-flight unbonding, direct-node stake GREW +52,848 this week.",
   "asserted_in_runs":[21],"withdrawn_in_run":22,
   "reason":"The correction subtracted ONE wallet's 229,865 EGLD from the staked-minus-delegated residual and published the remainder as a direct-node figure. That subtraction was incomplete by construction: delegator unDelegations happen across the whole provider set every week, and this run measured 70,498 EGLD of them across the ten largest-moving providers ALONE. Applying the same partial method to run #22 would give a 'direct-node' number that is fully consumed by unbonding several times over.",
   "replacement":"When measured unbonding in flight meets or exceeds the residual, the correct statement is that the residual carries no extractable direct-node signal - not a smaller direct-node number. Run #22 publishes corrected_direct_node_egld as null on that basis."},
  {"claim":"Every weekly net one-way OTC figure is an upper bound; netting must run over the wave rather than the reporting week.",
   "asserted_in_runs":[21],"withdrawn_in_run":22,
   "reason":f"The rule was generalised from a single wave. Re-netting the July episode (Jul 6-27) feed-to-drain as ONE window gives {f(july['net_one_way'])} EGLD against {f(july['sum_weekly'])} from summing its three weekly nets - {abs(july['overstate_pct']):.2f}% apart, i.e. weekly framing was accurate there. The 55% overstatement run #21 measured is specific to waves whose feed and drain legs sit in different reporting weeks, which the August wave does (UPbit feeding one week, receiving the next) and July's did not.",
   "replacement":f"Weekly netting is adequate unless a wave straddles a week boundary. Test the wave rather than assuming the frame: the extended August wave (Aug 3-24) still overstates by {wave['overstate_pct']:.1f}%, so the wave-window figure is reported alongside the weekly one whenever a straddle is detected - the diagnostic tell remains a weekly circularity reading far outside the 63-80% band."}]}

# ---- merge -----------------------------------------------------------------
rep={}
rep.update(json.load(open("/tmp/run22w/part1.json")))
rep.update(json.load(open("/tmp/run22w/part2.json")))
p3=json.load(open("/tmp/run22w/part3.json"))
rep["anomalies"]=p3["anomalies"]; rep["trend_indicators"]=p3["trend_indicators"]
rep["watch_list"]=p3["watch_list"]
rep["meta_learning"]=R["meta_learning"]
rep["pre_committed_tests"]=R["pre_committed_tests"]
order=["metadata","executive_summary","network_health","whale_intelligence",
       "staking_intelligence","token_activity","defi_activity","anomalies",
       "trend_indicators","watch_list","meta_learning","pre_committed_tests"]
rep={k:rep[k] for k in order}
json.dump(rep,open(f"{REPO}/reports/{RD}.json","w"),indent=1,default=str)
print("report written; keys:",list(rep.keys()))
print(f"tests: {len(tests)} total, {len(resolved)} resolved this run, {as_pred} as_predicted ({hit:.1f}%), {sum(1 for t in tests if t['status']=='open')} open")
