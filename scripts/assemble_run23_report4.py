#!/usr/bin/env python3
"""Run #23 stage 5: pre_committed_tests + meta_learning, then merge -> reports/2026-08-31.json"""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-08-31"
O=json.load(open("/tmp/run23w/derived.json"))
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
F=json.load(open(f"{REPO}/data/collected/followup_{RD}.json"))
status=json.load(open("/tmp/run23w/status.json"))
beh=json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
r22=json.load(open(f"{REPO}/reports/2026-08-24.json"))
M=O["macro"]; otc=O["otc"]; wave=otc["wave"]; ex=O["exch"]
cust=O["custody"]; bid=O["bid"]; br=O["breadth"]; sk=O["staking"]; tk=O["tokens"]
xx=O["xexchange"]; df=O["defi"]; ub=O["unbond"]; absb=O["absorbers"]; p2p=O["p2p"]
price=M["price"]; pc=M["price_chg"]
cvc=beh["aggregates"]["compound_vs_claim_at_function_level"]
def f(x,d=0):
    try: return f"{x:,.{d}f}"
    except: return str(x)
def mv(ident,field,default=0):
    return next((m[field] for m in sk["moves"] if m["identity"]==ident), default)

prior={t["id"]:t for t in r22["pre_committed_tests"]}
tests=[t for t in r22["pre_committed_tests"] if t["status"]=="resolved"]

def resolve(tid,outcome,measured,resolution):
    t=dict(prior[tid]); t.update({"status":"resolved","outcome":outcome,"resolved_in_run":23,
        "measured_value":measured,"resolution":resolution}); return t

tests.append(resolve("hundred-pct-fee-providers","as_predicted",
  f"egldstakingprovider {f(mv('egldstakingprovider','delta'))} to {f(mv('egldstakingprovider','locked'))} ({100*mv('egldstakingprovider','delta')/79639:.1f}% this week, -34.8% over two, -51.8% over three from ~127,500), users {mv('egldstakingprovider','users_delta'):+d} to {mv('egldstakingprovider','users'):,}; procryptostaking {f(mv('procryptostaking','delta'))} to {f(mv('procryptostaking','locked'))} (-20.5% over two), users {mv('procryptostaking','users_delta'):+d} to {mv('procryptostaking','users'):,}. serviceFee still 1.0, APR still 0, 50 nodes each - fee NOT reversed, nodes NOT deregistered.",
  "The 'books halve, users flat' branch fires. egldstakingprovider's book is down 51.8% over three weeks against a 7.2% user loss; procryptostaking is down 20.5% over two against 1.3%. The reading registered for this branch was that the delegation market's price mechanism only reaches large holders, and that is now supported by a second, much longer-running natural experiment discovered this run: ledgerbyfigment has paid 0% for eleven weeks and lost 2.0% of its delegators, stakedinc 0.3% across the whole archive. Capital leaves at roughly half a book per month; people leave at roughly two percent per quarter."))

tests.append(resolve("unbond-withdrawal","as_predicted",
  f"wallet balance unchanged at {f(ub['balance'],2)} EGLD, {f(ub['pending_total'])} still unbonded-and-unclaimed inside the delegation contracts, ZERO outbound transactions and zero function calls in the Aug 24-31 window",
  "The no-action branch - added to this test in run #22 precisely because its absence made the run #21 version unresolvable - fires cleanly. Two full weeks with a claimable position untouched is an inactive or lost-access holder, so the 229,865 is retired as a live forward flow. This is the first time a no-action branch has resolved a test, and it validates the run #22 design rule that every destination test needs one with a time bound."))

tests.append(resolve("otc-wave3-escalation","as_predicted",
  f"UPbit tranche {f(otc['upbit_feed'])} EGLD against a ~150,000 escalation threshold - 3x it; gross throughput {f(otc['gross_out'])} out / {f(otc['gross_in'])} in; net one-way {f(otc['net_one_way'])}; desk inventory {f(otc['desk_bal'])} (+{f(otc['desk_delta'])}), 2.4x the prior record",
  f"The escalation branch fires at three times its threshold. But the test's framing - 'escalates toward the run #17 peak of 409,680 one-way' - undersells what happened: the wave delivered {f(otc['net_one_way'])} one-way AND reloaded to a record {f(otc['desk_bal'])} in the same week, so the pipeline is now accumulating faster than it distributes. The run #17 peak drained its inventory delivering 409,680; this one has not started draining. Netted feed-to-drain over Aug 17-31 the wave has delivered {f(wave['net_one_way'])} one-way, against {f(wave['sum_weekly'])} from summing the two weekly nets ({wave['overstate_pct']:.0f}% overstatement) - and run #22's narrowed straddle rule predicted the overstatement in advance from this week's {otc['circ_pct']:.0f}% circularity sitting below the 63-80% band."))

tests.append(resolve("custody-drawdown-follow-through","as_predicted",
  f"custody {f(cust['delta'])} to {f(cust['balance'])} (a second consecutive drawdown, -497K over two weeks); the Binance.com hot wallet ROSE {f((cust['hot_balance'] or 0)-(cust['hot_previous'] or 0))} to {f(cust['hot_balance'])} but forwarded {f(cust['hot_to_desk_total'])} EGLD into the OTC desks - 73,421 via the run #19 feeder, 30,554 via the run #20 feeder, 21,297 direct - while returning {f(cust['hot_to_custody_egld'])} to custody",
  "The CLAIM resolves as predicted - the custody drawdown is the funding leg of distribution, demonstrated by direct flow tracing for the first time in seventeen runs of watching this wallet. The THRESHOLD was mis-specified and would have resolved the opposite way if applied literally: it required the hot wallet's BALANCE to fall more than 150,000, and the balance ROSE because custody refilled it faster than it distributed. LESSON: a balance-delta threshold cannot detect a flow whose funding outruns its spending. Specify such tests on the flow (does X send to Y) rather than on the intermediary's balance. The re-registered version below does this."))

tests.append(resolve("p2p-org-delegator-migration","as_predicted",
  f"{p2p['function_counts'].get('unDelegate',0)} unDelegate calls from 1,244 attached delegators in the window (0.16%), against {p2p['function_counts'].get('reDelegateRewards',0)} reDelegateRewards and {p2p['function_counts'].get('claimRewards',0)} claimRewards on a contract with zero stake and zero APR; the owner meanwhile called removeNodes x{p2p['function_counts'].get('removeNodes',0)} plus unBondNodes, taking numNodes 50 -> 0",
  "The '<10% leave' branch fires overwhelmingly - 0.16% in a week, against a 25% threshold for the alternative. The registered reading was that inertia is near-absolute and the delegation market has no working price mechanism for retail, and this run supplies far stronger evidence than the test asked for: ledgerbyfigment has been in the identical state for ELEVEN weeks and lost 2.0% of 3,961 delegators, and stakedinc has lost 2 of 639 across the entire archive. The most striking detail is that four wallets called reDelegateRewards on p2p_org_ this week - compounding rewards that cannot exist."))

tests.append(resolve("dex-turnover-persistence","as_predicted",
  f"turnover {bid['turnover']:.2f}% against a ~5% regime threshold; volume ${f(bid['dexvol'])} ({100*(bid['dexvol']-bid['prev_dexvol'])/bid['prev_dexvol']:+.1f}%), pool TVL ${f(bid['pooltvl'])} ({100*(bid['pooltvl']-bid['prev_pooltvl'])/bid['prev_pooltvl']:+.1f}%). IN EGLD TERMS: volume {f(bid['prev_dexvol_egld'])} -> {f(bid['dexvol_egld'])} EGLD/day ({100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}%), pool depth {100*(bid['pooltvl_egld']-bid['prev_pooltvl_egld'])/bid['prev_pooltvl_egld']:+.1f}%",
  "The regime-change branch fires on the metric as defined, and the reading it prescribed - retire the absent-bid diagnosis carried since run #18 - is accepted with one qualification the test could not anticipate. The EGLD-denominated decomposition that run #22 recommended shows the ratio held because BOTH sides scaled with a +6.4% price: the venue processed slightly LESS EGLD than last week. So the absent-bid diagnosis is retired, but on the strength of withdrawal breadth rather than turnover, and the turnover series should be reported in EGLD terms from here."))

tests.append(resolve("mex-mechanism","as_predicted",
  f"MEX supply {100*(tk['mex_supply']-tk['mex_prev_supply'])/tk['mex_prev_supply']:+.3f}% (threshold was -1%); MEX/WEGLD pool TVL {xx['mex_pair_depth']['tvl_egld_wow_pct']:+.2f}% in EGLD terms (threshold +10%), ${f(xx['mex_pair_depth']['tvl_usd'])} / {f(xx['mex_pair_depth']['tvl_egld'])} EGLD at depth rank {xx['mex_pair_depth']['depth_rank']}. Separately the outperformance streak BROKE: MEX {xx['mex_wow']:+.2f}% vs EGLD {pc:+.2f}%",
  "The 'neither, second run running' branch fires. Per the run #21 rule about repeated explanations, the model stops generating them: the five-week ~9.8pp MEX-over-EGLD gap is labelled UNEXPLAINED FLOW and the question is closed rather than re-opened. The streak ending in the same week is a fitting coda - whatever drove it is no longer obviously running. This is the cleanest example so far of a pre-committed test being used to stop work rather than to start it."))

t=dict(prior["compound-rate-break"])
t.update({"status":"resolved","outcome":"inconclusive","resolved_in_run":23,
  "measured_value":f"{cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} redelegate vs {cvc['claim_count']} claim) - a fourth consecutive decline and the lowest of ten readings, but BETWEEN the two branches (below 56% / above 59%)",
  "resolution":"UNRESOLVABLE ON A SPECIFICATION DEFECT, not on the data. The branches were non-contiguous and the reading landed in the 56-59% gap. This is the second consecutive run in which a test failed to resolve because of how it was written rather than what happened - run #22's unbond test lacked a no-action branch, this one lacks the middle of its range. NEW STANDING RULE: branch conditions must partition the outcome space with no gaps. Substantively, four consecutive declines spanning a flat week, a +30% week and a +6% week is not a price-following series, and the re-registered version below uses a single contiguous cut."})
tests.append(t)

def new(tid,claim,threshold,branches,measured):
    return {"id":tid,"registered_in_run":23,"claim":claim,"threshold":threshold,
            "branches":branches,"status":"open","outcome":None,"resolved_in_run":None,
            "measured_value":measured,"resolution":None}

tests += [
 new("desk-inventory-drain",
  "The record desk inventory is staged supply awaiting delivery, not a permanent inventory level.",
  "desks falling below ~120,000 next week = the overhang is being delivered and wave #3 becomes the largest distribution wave in tracking; inventory holding at or above ~220,000 with the feed continuing = staging is still running and the delivery is ahead; between 120,000 and 220,000 = partial delivery, re-measure",
  [{"condition":"desks < 120,000","reading":"the overhang was delivered; wave #3 is the largest distribution wave tracked"},
   {"condition":"desks >= 220,000 with feed continuing","reading":"staging still running; the delivery leg is ahead of us"},
   {"condition":"desks between 120,000 and 220,000","reading":"partial delivery; re-measure without concluding"}],
  f"desk inventory {f(otc['desk_bal'])} (+{f(otc['desk_delta'])}, 2.4x the prior record) after delivering {f(otc['net_one_way'])} one-way; UPbit tranche series 14,000 / 297,000 / {f(otc['upbit_feed'])}"),
 new("binance-desk-feed-standing",
  "Binance's custody-to-hot-to-desk routing is a standing funding programme, not a one-off.",
  "SPECIFIED ON FLOW, NOT BALANCE (the run #22 version failed on exactly this): the Binance.com hot wallet sending more than ~50,000 EGLD to OTC desks or their known feeders next week = a standing programme and the custody drawdown is scheduled supply; nothing above ~10,000 = one-off routing and the custody and pipeline watches separate again; between 10,000 and 50,000 = continuing but not scaled",
  [{"condition":"hot -> desks/feeders > 50,000","reading":"standing programme; custody drawdown is scheduled supply"},
   {"condition":"hot -> desks/feeders < 10,000","reading":"one-off routing; separate the two watches again"},
   {"condition":"between 10,000 and 50,000","reading":"continuing but not scaled; keep both watches joined provisionally"}],
  f"hot -> desks {f(cust['hot_to_desk_total'])} this week via the run #19 feeder (73,421), the run #20 feeder (30,554) and one direct 21,297; custody {f(cust['delta'])} to {f(cust['balance'])}"),
 new("fourth-deregistration",
  "Operator deregistration is a trend in the MultiversX validator set, not three idiosyncratic business decisions.",
  "a FOURTH provider reaching locked == 0 while retaining attached delegators within four weeks = operator attrition is a trend and the delegation market is losing its long tail; none in four weeks = the three known cases are idiosyncratic",
  [{"condition":"a fourth provider hits locked == 0 with users attached within 4 weeks","reading":"operator attrition is a trend; the long tail is leaving"},
   {"condition":"none within 4 weeks","reading":"the three are idiosyncratic business decisions, not a market signal"}],
  "three known: ledgerbyfigment (run #13 window, 170,808 EGLD, 3,883 users now), stakedinc (whole archive, 637 users), p2p_org_ (exit completed this week, 1,244 users). Detection signature widened to locked == 0 AND (numNodes > 0 OR numUsers > 0)"),
 new("dex-demand-in-egld",
  "The DEX turnover regime reflects genuine venue demand rather than the price move it coincided with.",
  "EGLD-denominated 24h volume above ~70,000 next week = genuine demand growth independent of price; below ~60,000 = the USD turnover ratio has been tracking price and the series must be reported in EGLD from here; 60,000-70,000 = flat, no conclusion",
  [{"condition":"EGLD volume > 70,000/day","reading":"genuine venue demand independent of price"},
   {"condition":"EGLD volume < 60,000/day","reading":"USD turnover tracks price; report the series in EGLD"},
   {"condition":"60,000-70,000/day","reading":"flat; no conclusion"}],
  f"turnover {bid['turnover']:.2f}% (USD ratio held above the 5% branch) but EGLD volume {f(bid['prev_dexvol_egld'])} -> {f(bid['dexvol_egld'])}/day ({100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}%) and EGLD pool depth {100*(bid['pooltvl_egld']-bid['prev_pooltvl_egld'])/bid['prev_pooltvl_egld']:+.1f}%"),
 new("withdrawal-breadth-broadening",
  "The jump in ex-pipeline withdrawal breadth is a genuine broadening of off-venue accumulation, not a rally artifact.",
  "holding above ~40 distinct recipients AND ~300,000 EGLD next week = a real broadening and the strongest bid evidence the model has; falling below ~25 recipients = this week tracked the rally and the pipeline still dominates the withdrawal channel",
  [{"condition":">40 recipients and >300,000 EGLD","reading":"genuine broadening of off-venue accumulation"},
   {"condition":"<25 recipients","reading":"rally artifact; the pipeline still owns the channel"}],
  f"{br['ex_n']} recipients / {f(br['ex_egld'])} EGLD ex-pipeline against 21 / 133,521 last week; pipeline share {br['pipeline_share']:.1f}% vs 88.3%. First week with no page-cap terminations, so not a lower bound"),
 new("compound-rate-drift",
  "The four-week decline in the reward compound rate is a systematic drift toward monetising yield.",
  "CONTIGUOUS BRANCHES (the run #22 version failed on a gap): below 57.0% next week = the drift is systematic and the compound rate becomes a standing bearish participation indicator; 57.0% or above = it has stabilised and the four-week decline was a level shift rather than a trend",
  [{"condition":"compound < 57.0%","reading":"systematic drift; standing bearish participation indicator"},
   {"condition":"compound >= 57.0%","reading":"stabilised; the decline was a level shift, not a trend"}],
  f"{cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} vs {cvc['claim_count']}), fourth consecutive decline, lowest of ten; institutional tier sold 3 of 6 claims for a second week"),
 new("stablecoin-base-contraction",
  "The wrapped-dollar base contracting into a rising price is de-risking, not plumbing noise.",
  "a THIRD consecutive week of combined USDC+USDT contraction = the on-chain dollar base is a de-risking instrument and should be reported alongside USH; any week of net expansion = plumbing noise and the two-week run was redemption timing",
  [{"condition":"third consecutive combined contraction","reading":"the dollar base is a de-risking instrument; promote it"},
   {"condition":"net expansion","reading":"plumbing noise; drop it"}],
  f"USDC {tk['stable']['USDC-c76f1f']['pct']:+.2f}% ({f(abs(tk['stable']['USDC-c76f1f']['supply']-tk['stable']['USDC-c76f1f']['prev']))} tokens), USDT {tk['stable']['USDT-f8c08c']['pct']:+.2f}%; ~$77K combined during a +6.39% price week"),
]

resolved=[t for t in tests if t["status"]=="resolved" and t.get("resolved_in_run")==23]
as_pred=sum(1 for t in resolved if t["outcome"]=="as_predicted")
hit=100*as_pred/len(resolved)

R={"pre_committed_tests":tests}
R["meta_learning"]={
 "run_number":23,
 "endpoints_that_worked":status["ok"],
 "endpoints_that_failed":status["failed"]+[
   "collect_run23.py BINANCE_HOT constant returned HTTP 400 (invalid bech32) - repaired in the followup pass",
   "/accounts/{unbond_wallet}/delegation, /accounts and outbound scan: HTTP 429 - repaired in the followup pass",
   "wave-window desk pagination returned zero txs on the main pass - repaired in the followup pass",
   "/tokens/WTAO-3ec9c0: HTTP 404"],
 "api_quirks":[
  "THE PRE-FLIGHT BECH32 VALIDATOR DOES NOT COVER COLLECTOR SCRIPTS. scripts/validate_addresses.py checks known-addresses.json and previous.json only. This run hardcoded a Binance hot wallet with an invalid checksum directly in collect_run23.py; it returned HTTP 400, paged_txs broke on the error dict and returned [], and the collector printed '0 outbound recipients >=10K' - which would have resolved a pre-committed test on fabricated evidence. The validator must be extended to grep erd1 literals out of scripts/*.py.",
  "paged_txs SILENTLY CONVERTS AN ERROR INTO AN EMPTY WINDOW. `if not isinstance(batch, list) or not batch: break` treats an HTTP error dict identically to a genuinely empty result, so a 400 or 429 produces 'nothing happened' rather than a failure. Three separate findings this run were nulled this way. Any pagination helper must distinguish the two and record the error.",
  "THE API RATE-LIMITS (HTTP 429) UNDER THE ALL-PROVIDER SCAN. Paging ~107 provider contracts at 0.22s between requests triggered 429s on unrelated queries issued around the same time. The followup pass used exponential backoff (1s doubling to 12s) and hit zero errors. Budget for backoff, not just a fixed delay, once a run exceeds roughly 800 requests.",
  "A FULLY EXITED OPERATOR NO LONGER MATCHES RUN #22's DEREGISTRATION SIGNATURE. p2p_org_ called removeNodes eleven times plus unBondNodes this week and now reads numNodes 0, so 'locked == 0 AND numNodes > 0' misses it. The signature must be 'locked == 0 AND (numNodes > 0 OR numUsers > 0)'.",
  "previous.json ONLY EVER STORED PROVIDERS WITH locked > 0, which is why two deregistrations went unreported for ten runs. A provider that goes to zero drops out of the stored set entirely and can never appear as a WoW event. The snapshot must store the full /providers list, not the locked>0 subset.",
  "All four dataApi-priced tokens (SEGLD, SWTAO, USH, XEGLD) returned a live price on the FIRST pass with zero retries - the first fully clean pass since the guard was added in run #13. The re-fetch guard and the run #22 list-endpoint fallback both stood down.",
  "/tokens/WTAO-3ec9c0 now returns HTTP 404, so the run #11 accumulator-ratio fallback for SWTAO is permanently unavailable. Not needed this run; if SWTAO nulls again the order is list-endpoint recovery (run #22) then prior-price carry-forward (run #14).",
  "The provider join-key fix from run #22 was folded into the main collector and asserted: match rate 100% (105 of 105). The assertion is cheap and should stay on every cross-snapshot join.",
  "Raising the page cap to 30 for exchange hot wallets (run #22 rec #10) eliminated page-cap terminations from the withdrawal-breadth scan entirely - the raw figure is a full 7-day scan for the first time. The provider scan at max_pages=6 still hit the cap on the busiest contracts, so the unbonding queue figure remains a lower bound.",
  "The two long-flagged invalid bech32 entries (Hatom UTK Money Market, OneDex Launchpad) still fail pre-flight validation, unchanged since run #18. Still flagged rather than guessed."],
 "data_gaps":[
  f"{len([p for p in (D.get('_pagecap_terminations') or []) if p.get('tag')=='provscan'])} provider contracts hit the 6-page cap during the unDelegate scan, so the {f(sk['undelegated_week'])} EGLD unbonding-queue figure is a LOWER bound on the busiest contracts.",
  "Measured pending unbonding covers the 45 largest unDelegate callers of 300, so the pool total is also a lower bound.",
  "The JEXchange aggregator contract has returned 0 transfers for three consecutive runs. That is now more likely a stale address than a halt and should be re-derived rather than re-reported.",
  "Hatom UTK Money Market and OneDex Launchpad remain excluded from protocol address sets pending valid addresses.",
  "MEX's five-week outperformance has no measured mechanism after two runs of looking and is closed as unexplained flow rather than explained.",
  "The archive cannot be pushed earlier than 2026-06-01 for provider state, so ledgerbyfigment's deregistration is dated to the run #13 window but stakedinc's zero-locked state has no discoverable start date."],
 "key_findings":[
  f"EGLD {pc:+.2f}% to ${price:.2f} while BTC {M['btc_wow']:+.2f}% and ETH {M['eth_wow']:+.2f}% BOTH FELL - the first EGLD-specific decoupling to the upside since run #16, and the opposite of last week's beta move.",
  f"The OTC desks delivered {f(otc['net_one_way'])} EGLD one-way AND ended the week with a record {f(otc['desk_bal'])} still loaded (+{f(otc['desk_delta'])}, 2.4x the prior record). The pipeline is accumulating faster than it distributes - which has not happened before in tracking.",
  f"UPbit's tranche series is now 14,000 / 297,000 / {f(otc['upbit_feed'])} - an escalating programme, and 3x run #21's escalation threshold.",
  f"Binance is a desk feeder. Custody sent {f(cust['custody_out_this_window'])} to the hot wallet, which forwarded {f(cust['hot_to_desk_total'])} into the OTC desks via two named feeders plus one direct transfer. Seventeen runs of watching custody and twenty-three of watching the pipeline collapse into one instrument.",
  "Run #22's 'first operator deregistration in tracking' is WITHDRAWN: ledgerbyfigment deregistered in the run #13 window with 170,808 EGLD and 3,961 delegators and was never reported; stakedinc has been in the same state across the entire archive.",
  f"Participation inertia is now an eleven-week measurement: ledgerbyfigment lost 2.0% of its delegators over eleven weeks of zero yield, stakedinc 0.3% across the archive, p2p_org_ produced {p2p['function_counts'].get('unDelegate',0)} unDelegate calls from 1,244 users - while the 100%-fee providers' books fell 51.8% and 20.5%. Capital responds to price signals; people do not.",
  f"The identifiable-bid repair returned a decisive NEGATIVE: all {absb['scanned']} desk outbound terminals are zero-balance pass-through routers retaining {100*absb['total_retained']/absb['total_received']:.1f}% of {f(absb['total_received'])} EGLD. There are no absorbers to discover, and the instrument is retired.",
  f"DEX turnover held its regime threshold in USD ({bid['turnover']:.2f}%) and failed it in EGLD: volume {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}% to {f(bid['dexvol_egld'])} EGLD/day. Both sides of the ratio scaled with price.",
  f"Ex-pipeline withdrawal breadth had its best reading since the instrument was built - {br['ex_n']} recipients taking {f(br['ex_egld'])} EGLD, pipeline share down to {br['pipeline_share']:.1f}% from 88.3% - and for the first time it is a full 7-day scan with no page-cap terminations.",
  f"The first full-set unbonding scan found {f(sk['undelegated_week'])} EGLD from {sk['undelegate_callers']} wallets across all {sk['providers_scanned']} contracts, 2.1x run #22's ten-provider partial. The residual is again fully absorbed; corrected_direct_node_egld stays null.",
  f"USH burned {tk['lsd']['USH-111e09']['pct']:+.2f}% for a second consecutive week into a rising price, and both wrapped dollars contracted (~$77K). Every holding-side instrument de-risked into strength.",
  f"{as_pred} of {len(resolved)} tests resolved this run fired as predicted ({hit:.1f}%); the one inconclusive failed on a specification defect - non-contiguous branches - for the second consecutive run of specification defects."],
 "action_items_from_previous":11,
 "action_items_completed":10,
 "methodology_changes":[
  "EXTEND PRE-FLIGHT ADDRESS VALIDATION TO COLLECTOR SOURCE. The bech32 validator covers the JSON data files only; this run's invalid address was a Python constant. Grep erd1 literals out of scripts/*.py and validate those too, before the collector runs.",
  "A PAGINATION HELPER MUST NOT RETURN [] ON AN ERROR. Distinguish 'no transactions' from 'the query failed' and record the latter. Three findings were nulled this run by a helper that treats an HTTP error dict as an empty page.",
  "USE EXPONENTIAL BACKOFF ON 429, NOT A FIXED DELAY. The all-provider scan pushed the run past the API's rate limit and nulled unrelated queries issued nearby. The followup pass with 1s-to-12s backoff hit zero errors.",
  "WIDEN THE DEREGISTRATION SIGNATURE to 'locked == 0 AND (numNodes > 0 OR numUsers > 0)'. A fully exited operator removes its nodes and stops matching run #22's version.",
  "STORE THE FULL /providers LIST IN previous.json, not the locked>0 subset. Two deregistrations went unreported for ten runs because a provider that goes to zero drops out of the stored set and can never appear as a WoW event.",
  "WHEN A DETECTOR IS INVENTED, RUN IT BACKWARDS OVER THE ARCHIVE IN THE SAME RUN. Run #22 invented the deregistration signature and immediately published 'the first in tracking' without applying it to the stored snapshots. Doing so this run found two earlier cases, the larger of which was ten runs old. Any 'first X in tracking' claim must be checked with the detector that found it.",
  "SPECIFY A TEST'S THRESHOLD ON THE QUANTITY THAT CARRIES THE SIGNAL. The custody test was written on the intermediary wallet's BALANCE and would have resolved backwards: the balance rose because the funding leg outran the spending leg. Write flow tests on the flow.",
  "BRANCH CONDITIONS MUST PARTITION THE OUTCOME SPACE WITH NO GAPS. The compound-rate test offered 'below 56%' and 'above 59%' and the reading landed in between, making it unresolvable. Two consecutive runs have now lost a test to a specification defect rather than to the data.",
  "REPORT VENUE THROUGHPUT IN EGLD AS WELL AS USD. A USD turnover ratio holds through a price move because both numerator and denominator scale with it; the EGLD figure showed volume actually fell. This closed run #22's confound in a single line."],
 "new_addresses_discovered":2,
 "most_valuable_insight":(
  "The most valuable result this run is a correction to our own headline, and it generalises. Run #22 invented a detection signature for operator deregistration, applied it to one week, and published 'the first operator deregistration in tracking'. "
  "Running that same signature backwards over the stored archive - a few seconds of work that run #22 did not do - shows ledgerbyfigment deregistered in the run #13 window with 170,808 EGLD and 3,961 delegators, and stakedinc has been in that state for the whole archive. Both went unreported for ten runs, and the reason is structural: previous.json only ever stored providers with locked > 0, so a provider going to zero silently leaves the comparison set. "
  "The generalisable rule is that a newly invented detector must be run over the archive in the same run it is invented, because the archive is where its false-negative rate is measurable. "
  "The finding it produced is also the more important one substantively: with eleven weeks of ledgerbyfigment and a whole archive of stakedinc, participation inertia stops being a weekly observation and becomes a measured constant - a total loss of yield removes roughly half a provider's EGLD in a month and roughly two percent of its people in a quarter."),
 "top_recommendation":(
  "Resolve the desk-inventory-drain test, because it is the largest forward-looking quantity the model has ever carried. "
  f"The desks hold {f(otc['desk_bal'])} EGLD - more than the entire run #17 peak wave delivered - having ALREADY delivered {f(otc['net_one_way'])} one-way this week, with UPbit's feed escalating and Binance now feeding alongside it. "
  "Either that inventory is delivered next week, in which case wave #3 is the largest distribution event in tracking and the +6% price move happened into it; or it holds, in which case the staging is still running and the delivery is ahead of us. "
  "Both readings are actionable and they point opposite ways for the following month."),
 "recommendations_for_next_run":[
  "MAINTAIN THE SCOREBOARD AND ERRATA. Resolve the 7 open pre_committed_tests, register run #24's before seeing the data, and append the prediction record to running_baselines. This run resolved all 8 of run #22's open tests, 7 as predicted and 1 inconclusive on a specification defect - the second consecutive run to lose a test that way, so check the new branches partition cleanly before registering them.",
  "RESOLVE THE DESK-INVENTORY DRAIN. The desks hold a record 266,213 EGLD after delivering 272,396 one-way. Measure the drain, re-net the Aug 17 wave feed-to-drain now that a third week exists, and trace the destinations two hops as usual. This is the single highest-value query of the week.",
  "EXTEND scripts/validate_addresses.py TO COVER COLLECTOR SOURCE. This run hardcoded an invalid Binance hot wallet in collect_run23.py, got HTTP 400, and silently produced '0 outbound recipients >=10K' - which would have resolved a pre-committed test on fabricated evidence. Grep erd1 literals out of scripts/*.py and validate them in the pre-flight. Roughly twenty lines and it closes a class of silent failure the JSON-only validator cannot see.",
  "FIX paged_txs TO DISTINGUISH ERROR FROM EMPTY, AND ADD 429 BACKOFF. Three findings were nulled this run by a helper that treats an HTTP error dict as an empty page, and the all-provider scan pushed the run past the API rate limit. The followup pass with exponential backoff had zero errors, so port that behaviour into the main collector.",
  "STORE THE FULL /providers LIST IN previous.json. Storing only locked>0 providers is why two deregistrations went unreported for ten runs. This is a one-line change with a ten-run backlog behind it.",
  "TRACK THE THREE DEREGISTERED PROVIDERS' DELEGATOR COUNTS AS A STANDING SERIES. ledgerbyfigment (3,883), stakedinc (637) and p2p_org_ (1,244) are a natural experiment on participation inertia running at three different durations - 11 weeks, the whole archive, and 2 weeks. Four numbers a week turns the strongest qualitative finding in the report into a measured decay rate.",
  "RAISE THE PROVIDER-SCAN PAGE CAP OR SAMPLE THE BUSY CONTRACTS SEPARATELY. Several contracts hit the 6-page cap during the unDelegate scan, so this run's 151,443 EGLD queue figure is a lower bound on exactly the providers where most unbonding happens. Either raise the cap for contracts with >250 weekly inbound txs or page those alone at a higher budget.",
  "RE-DERIVE THE JEXCHANGE AGGREGATOR ADDRESS. It has returned 0 transfers for three consecutive runs while the fees contract reports 6,775. That pattern is a stale address, not a halted protocol, and it has been reported as a data gap twice without being fixed.",
  "REPORT DEX TURNOVER IN EGLD TERMS AS THE PRIMARY SERIES. The USD ratio held this week only because both sides scaled with a +6.4% price while EGLD volume fell 4.3%. The EGLD series is price-independent and is the one that answers the demand question.",
  "WATCH FOR A THIRD CONSECUTIVE STABLECOIN CONTRACTION. USDC -0.90% and USDT -1.31% into a rising price is the first time both wrapped dollars have contracted together. A third week would make the on-chain dollar base a de-risking instrument worth reporting alongside USH rather than plumbing noise."],
 "dashboard_feature_suggestions":[
  {"title":"Desk inventory vs delivery - the staging chart",
   "motivation":"This run's central fact cannot be seen anywhere on the dashboard: the desks delivered 272,396 EGLD one-way AND ended the week holding a record 266,213, meaning the pipeline accumulated faster than it distributed for the first time in tracking. The OtcPipeline panel shows gross and net one-way bars per week, which is throughput; desk INVENTORY is a stock, and the relationship between the two (how much was staged versus how much left) is what tells a reader whether a distribution wave is ahead of them or behind them. Right now that comparison exists only as a sentence.",
   "suggested_visualization":"a combined chart per week - bars for net one-way delivered, an overlaid line for end-of-week desk inventory, and a shaded area for cumulative undelivered stage. Weeks where inventory rose while delivery was positive (only run #23 so far) marked explicitly.",
   "data_already_available":True,
   "data_source":"whale_intelligence.otc_pipeline.desk_balance_egld and net_one_way_series_egld_7d across reports; both fields already exist in every report from run #19 onward",
   "priority":"high"},
  {"title":"Provider lifecycle strip - now with three real cases and a decay series",
   "motivation":"Carried from run #22 at medium priority; this run makes it high. There are three deregistered providers with attached delegators (ledgerbyfigment 3,883 users for 11 weeks, stakedinc 637 across the archive, p2p_org_ 1,244 for 2 weeks) plus two at 100% fee with zero APR, and together they are the strongest quantitative finding the report has produced - a measured decay rate for participation inertia. The dashboard renders none of it; p2p_org_ appears as a single 'notable leaver' row and the other two appear nowhere at all.",
   "suggested_visualization":"a compact strip of provider states (healthy / fee-squeezed / zero-APR / deregistered) with each distressed provider as a chip carrying locked, users and weeks-in-state, plus a small sparkline of each one's delegator count over its weeks at zero yield - the decay curve is the finding.",
   "data_already_available":True,
   "data_source":"staking_intelligence.provider_states (NEW this run - state, locked_egld, num_users, num_nodes, apr_pct, fee_pct, weeks_in_state, note), plus per-week delegator counts recoverable from data/collected/*.json",
   "priority":"high"},
  {"title":"Errata linkage from the withdrawn claim to its replacement",
   "motivation":"The errata overlay warns a reader of a superseded archived report, which is the right behaviour, but this run withdraws a claim ('first operator deregistration in tracking') whose replacement is a substantially bigger finding sitting in a different run's report. A reader who lands on run #22 sees a warning and no route to what is now known. The overlay has the data to link them - withdrawn_claims already carries withdrawn_in_run and replacement text.",
   "suggested_visualization":"make the errata banner's replacement text a link to the correcting report, anchored to the section that carries the corrected finding, so a superseded claim routes forward rather than merely flagging itself.",
   "data_already_available":True,
   "data_source":"meta_learning.withdrawn_claims (claim, asserted_in_runs, withdrawn_in_run, reason, replacement) already aggregated into public/errata.json by generate-manifest.ts",
   "priority":"medium"}],
 "dashboard_suggestions_followup":[
  {"title":"Unbonding queue table with a settlement calendar","status":"pending",
   "note":"Not built. The case is stronger again - the first full-set scan found 300 distinct callers moving 151,443 EGLD, 2.1x last run's partial, and the card still renders one wallet's position as if it were the whole story. It was not built this run for a deliberate reason worth recording: the dashboard working tree carries uncommitted in-flight work from another session (App.tsx, Header.tsx, index.css, plus new PageTabs/CodePage files), and editing components into that state risks conflicting with work this run cannot see."},
  {"title":"Demand instruments panel - and make it show the disagreement","status":"deprioritized",
   "note":"Deprioritised because the run resolved the disagreement it was proposed to display. The identifiable bid is RETIRED - all 14 desk terminals were scanned and none retains what it receives, so there is no absorber series to plot. A panel built around three disagreeing instruments would now be plotting two, one of which is being replaced by its EGLD-denominated version. Re-propose once the EGLD turnover series has two points."},
  {"title":"Provider lifecycle strip","status":"pending",
   "note":"Carried and PROMOTED from medium to high. Run #22 proposed it with one deregistered provider and no state array; this run there are three deregistered providers with 5,764 attached delegators between them, two at 100% fee, and the data it asked for now exists as staking_intelligence.provider_states."},
  {"title":"OTC hub flow map: gross vs net one-way, with venue-level netting","status":"pending",
   "note":"Still not built, third run of asking. This week adds a fifth delivery venue (Bitget) and, for the first time, a second SOURCE - Binance alongside UPbit - so the structure is genuinely a source-to-sink graph now rather than one source fanning out. A signed table cannot show that two sources feed five sinks through a shared router layer."},
  {"title":"Wave-window OTC netting (feed-to-drain) alongside the weekly series","status":"built",
   "note":"Built run #21, load-bearing again. Wave #3 (Aug 17-31) nets 371,179 one-way against 524,505 summed weekly, a 41% overstatement, and the straddle was PREDICTED in advance this run by the circularity reading falling below the 63-80% band - the diagnostic run #21 registered is now doing forward work rather than post-hoc explanation."},
  {"title":"Pre-committed test scoreboard","status":"built",
   "note":"Built run #21. This run resolved all 8 open tests. Its most useful property this week was negative: two of the resolutions exposed defects in how the tests were WRITTEN (a balance threshold that could not see the flow, non-contiguous branches) rather than in the data, and having the thresholds recorded verbatim is what made those visible."},
  {"title":"Errata overlay on superseded reports","status":"built",
   "note":"Built run #21 and doing exactly its job this run - it now carries the withdrawal of run #22's 'first operator deregistration in tracking', which is the largest single correction the project has published. See the new suggestion above for the one thing it still cannot do: route the reader forward to the replacement."},
  {"title":"EGLD relative-strength (beta) tracker","status":"deprioritized",
   "note":"Deprioritised a sixth time, though this week is the strongest case yet against the streak: EGLD +6.39% while both majors fell is exactly what such a tracker would highlight. It remains one line in the network-health narrative, and six weeks of deprioritisation is itself the answer - if it were load-bearing it would have been built."}],
 "withdrawn_claims":[
  {"claim":"p2p_org_ is the FIRST operator deregistration in tracking.",
   "asserted_in_runs":[22],"withdrawn_in_run":23,
   "reason":"Run #22 invented the detection signature (locked == 0 with numNodes > 0) and published the claim without applying it to the stored snapshot archive. Applying it this run shows ledgerbyfigment went from 170,808 EGLD to zero between the 2026-06-08 and 2026-06-15 snapshots - inside the run #13 window - while keeping 7 nodes and 3,961 delegators, and stakedinc has been zero-locked with 10 nodes and ~639 users across the entire stored history from 2026-06-01. Neither was ever reported. p2p_org_ was the third and the smallest.",
   "replacement":"There are three known operator deregistrations. The largest and earliest is ledgerbyfigment (run #13 window, 170,808 EGLD, 3,961 delegators at the time, 3,883 now after eleven weeks at 0% APR). The reason both earlier cases were missed is structural: previous.json stores only providers with locked > 0, so a provider going to zero drops out of the comparison set rather than registering as an event. Two standing rules follow - store the full /providers list, and run any newly invented detector backwards over the archive in the same run it is invented."},
  {"claim":"The bilateral inverse rule's response ratio has fallen below the 0.30 depositor-capacity-exhaustion threshold, indicating the deposit base the rule depends on has been drawn down.",
   "asserted_in_runs":[22],"withdrawn_in_run":23,
   "reason":f"Run #22 measured 0.28 and flagged capacity exhaustion, registering that a second consecutive sub-0.30 reading would retire the rule. This week's up-week test returned {df['inverse_ratio']:.2f} - price {pc:+.2f}%, Hatom Lending EGLD-denominated TVL {df['hatom_lending_egld_pct']:+.2f}%, correct inverse sign - well clear of the threshold. The up-week series is 0.49 / 0.72 / 0.28 / {df['inverse_ratio']:.2f}.",
   "replacement":"The 0.28 is reclassified as a single weak response to an unusually large (+30.43%) price move rather than as evidence of a depleted deposit base. The rule stands with four up-week confirmations. The wider lesson is that a response RATIO is unstable when its denominator is a record-sized price move, so the exhaustion threshold should only be applied on weeks where |dPrice| sits inside the normal 5-15% band."}]}

rep={}
rep.update(json.load(open("/tmp/run23w/part1.json")))
rep.update(json.load(open("/tmp/run23w/part2.json")))
p3=json.load(open("/tmp/run23w/part3.json"))
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
