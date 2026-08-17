#!/usr/bin/env python3
"""Run #21: add the structured pre-committed test scoreboard and the withdrawn-claims
errata to reports/2026-08-17.json.

Forward-only by design (fable review, run #21): the tests registered in run #20 and
resolved in run #21 are hand-structured here from the two reports' own text; runs <=#19
are NOT backfilled from prose. Every future run appends its own registered tests and
resolves the prior run's, so the scoreboard compounds at zero marginal cost.
"""
import json

REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
p=f"{REPO}/reports/2026-08-17.json"
R=json.load(open(p))

tests=[
 # ---- registered in run #20, resolved this run -------------------------------
 {"id":"otc-wave2-escalation","registered_in_run":20,
  "claim":"Wave #2 of the OTC distribution escalates to the scale of the re-netted run #17 peak (409,680 EGLD one-way).",
  "threshold":"net one-way > ~300,000 AND UPbit tranche > ~350,000 = matches/exceeds the peak; net < ~100,000 = a two-week burst rather than a wave",
  "branches":[
    {"condition":"net > 300K and tranche > 350K","reading":"supply overhang is the dominant fact on the chain"},
    {"condition":"net < 100K","reading":"a two-week burst, not a wave"}],
  "status":"resolved","outcome":"inconclusive","resolved_in_run":21,
  "measured_value":"weekly net 138,265 on a 14,000 tranche (-96%); wave-netted 210,922",
  "resolution":"NEITHER branch fired, and the attempt to resolve it exposed a flaw in the measure. The escalation threshold missed by a wide margin - the UPbit tranche collapsed 96% to 14,000 and the desks returned 130,000 to UPbit - but the weekly net (138,265) landed between the two thresholds. Netting the wave feed-to-drain instead gives 210,922 against 326,924 from summing its two weekly nets, so the thresholds were specified on a quantity that is frame-dependent. Substantive answer: the wave did not escalate, it stopped."},
 {"id":"bid-scale-up","registered_in_run":20,
  "claim":"The identifiable bid (Mega Whale absorber via the Coinbase Routing pipe) is genuinely back rather than a one-off maintenance transfer.",
  "threshold":"a tranche of 30,000-50,000 EGLD = the bid is back; another sub-10,000 week or a return to zero = maintenance transfer and the dormancy finding is revived",
  "branches":[
    {"condition":"tranche 30-50K","reading":"the demand deficit is closing"},
    {"condition":"sub-10K or zero","reading":"maintenance transfer; revive bid dormancy as structural"}],
  "status":"resolved","outcome":"as_predicted","resolved_in_run":21,
  "measured_value":"0 EGLD - zero transactions on both the absorber and the Coinbase Routing wallet",
  "resolution":"The sub-10K/zero branch fired exactly as written. Run #20's 5,748 EGLD reactivation was a maintenance transfer; bid dormancy is revived as a structural finding, absent in 3 of the last 4 weeks."},
 {"id":"whale-i-classification","registered_in_run":20,
  "claim":"'Unknown Whale I' is OTC operator inventory rather than a genuine large buyer.",
  "threshold":"> 60% of counterparty value being hub feeders and routers = operator inventory, net it out of the one-way figure; broad and external = a genuine buyer belonging in the demand instruments",
  "branches":[
    {"condition":">60% hub counterparties","reading":"operator inventory - net it out of distribution, do not count as demand"},
    {"condition":"broad external counterparties","reading":"a genuine large buyer - the most consequential reclassification available"}],
  "status":"resolved","outcome":"as_predicted","resolved_in_run":21,
  "measured_value":"68.9% of inbound value, 55.7% of outbound, 62.5% combined (30d trace, 661/562 txs, no page-cap truncation)",
  "resolution":"Threshold cleared on the combined and inbound bases, marginally missed on outbound alone. Reclassified as OTC operator inventory with that caveat; its hub take is no longer counted as demand and one-way ex-whale-I is 135,407."},
 {"id":"xegld-redemption-destination","registered_in_run":20,
  "claim":"The XEGLD (XOXNO LSD) redemption that decoupled from price is migration rather than an exit.",
  "threshold":"destinations in native delegation contracts = migration, constructive; destinations at exchanges = exit, bearish; a single large recipient = idiosyncratic",
  "branches":[
    {"condition":"native delegation contracts","reading":"migration - constructive"},
    {"condition":"exchanges","reading":"exit - bearish"},
    {"condition":"one large recipient","reading":"idiosyncratic, dismissable"}],
  "status":"resolved","outcome":"as_predicted","resolved_in_run":21,
  "measured_value":"8 callers, onward flows 80-600 EGLD each, 531 EGLD into native delegation, 0 EGLD to any labelled exchange",
  "resolution":"The constructive branch fired, with an idiosyncratic flavour: retail-scale rotation, partly into native delegation, no exchange destination and no single large redeemer. Supply decelerated to -0.80%. The LSD contract itself has zero outbound value txs, so the trace ran through the unDelegate/withdraw callers."},
 {"id":"fee-cut-follow-through","registered_in_run":20,
  "claim":"MultiversX delegators respond to fee price signals: stake returns to egldstakingprovider after its 24% -> 15% cut.",
  "threshold":"stake returning within 2-3 weeks = delegators respond to price signals and other high-fee incumbents follow; stake continuing to leave = delegator inertia dominates fee economics",
  "branches":[
    {"condition":"stake returns","reading":"the yield-arbitrage mechanism works in both directions"},
    {"condition":"stake keeps leaving","reading":"inertia dominates; the mechanism is weaker than assumed"}],
  "status":"resolved","outcome":"withdrawn","resolved_in_run":21,
  "measured_value":"the provider set its fee to 100% (APR 0) and shed a further -33,182 EGLD / -13 users; procryptostaking did the same at 20% -> 100%",
  "resolution":"The test's premise was withdrawn rather than resolved. One week after the cut, the same provider moved 15% -> 100%, zeroing delegator APR, and the other named incumbent did too - different owners, 50 nodes each. A fee change is not evidence of competition, so run #20's 'first competitive repricing in twenty runs' is withdrawn. Incidental finding: a zero-yield signal moved 26% of one book but only 13 of ~1,124 users."},
 {"id":"direct-node-unwind-trace","registered_in_run":20,
  "claim":"Node operators are exiting direct staking - ~215K EGLD over three weeks, the largest unexplained structural flow tracked.",
  "threshold":"one operator unstaking = idiosyncratic; broad operator exit = an economics story about the base/top-up APR split",
  "branches":[
    {"condition":"one operator","reading":"idiosyncratic"},
    {"condition":"broad","reading":"a protocol-level finding about the APR split"}],
  "status":"resolved","outcome":"withdrawn","resolved_in_run":21,
  "measured_value":"residual flipped +282,713; one wallet held 229,865 EGLD in delegation unbonding; corrected direct-node change +52,848",
  "resolution":"Neither branch: the flow does not exist. The staked-minus-delegated residual also contains delegation unbonding in flight, and one wallet's unDelegate pair (149,585 + 80,279, both zero-value txs with the amount in the data field) explains the entire flip. Corrected, direct-node stake GREW. The three-run narrative is withdrawn."},
 {"id":"mex-stale-pricing","registered_in_run":20,
  "claim":"MEX outperforming EGLD is stale pricing in illiquid pairs (the explanation given in runs #19 and #20).",
  "threshold":"query the MEX pairs' actual TVL and trade counts - if the pricing is real, MEX outperforming its own chain's native token through a distribution wave is a finding, not noise",
  "status":"resolved","outcome":"against","resolved_in_run":21,
  "measured_value":"MEX/WEGLD holds $291,459 of pool TVL - 15.9% of all xExchange depth, the #2 deepest pool - on 125 trades in 24h",
  "resolution":"The model's own explanation is falsified. The pair is thin in volume but properly priced, and MEX has matched or beaten EGLD for four consecutive weeks. A real finding with no mechanism attached yet."},

 # ---- registered in run #21, open ------------------------------------------
 {"id":"unbond-destination","registered_in_run":21,
  "claim":"The 229,865 EGLD unbonding from a single wallet is provider rotation rather than distribution.",
  "threshold":"arrives at a delegation contract = rotation, neutral; at an exchange or OTC feeder = a distribution event larger than this week's entire OTC one-way figure; stays in the wallet = idiosyncratic",
  "branches":[
    {"condition":"delegation contract","reading":"provider rotation - neutral"},
    {"condition":"exchange or OTC feeder","reading":"a 230K distribution event and the dominant fact of the run"},
    {"condition":"stays in wallet","reading":"idiosyncratic"}],
  "status":"open","outcome":None,"resolved_in_run":None,
  "measured_value":"unbonding completes ~6 and ~7 days from 2026-08-17, i.e. inside the next window",
  "resolution":None},
 {"id":"otc-feed-resumption","registered_in_run":21,
  "claim":"The July-August OTC pattern is a standing programme rather than two discrete episodes.",
  "threshold":"a fresh UPbit tranche above ~150,000 within two weeks = standing programme; nothing above ~50,000 for two consecutive weeks = between cycles",
  "branches":[
    {"condition":"tranche > 150K within 2 weeks","reading":"a standing distribution programme"},
    {"condition":"nothing > 50K for 2 weeks","reading":"between cycles; watch the 1-3 week reload lag"}],
  "status":"open","outcome":None,"resolved_in_run":None,
  "measured_value":"this week's tranche 14,000 (-96%)","resolution":None},
 {"id":"hundred-pct-fee-providers","registered_in_run":21,
  "claim":"The two providers at a 100% service fee are winding down, and their delegators are inert rather than trapped.",
  "threshold":"books halving again with flat user counts = retail inertia is absolute; fee reversed = an operational move; nodes deregistered = the first genuine validator exit in tracking",
  "branches":[
    {"condition":"books halve, users flat","reading":"the delegation market's price mechanism only reaches large holders"},
    {"condition":"fee reversed","reading":"an operational move; run #20's reading was early rather than wrong"},
    {"condition":"nodes deregistered","reading":"first genuine validator exit; 251,266 EGLD becomes a forced-migration flow"}],
  "status":"open","outcome":None,"resolved_in_run":None,
  "measured_value":"combined 251,266 EGLD locked and 8,177 delegators earning zero","resolution":None},
 {"id":"usdt-drain","registered_in_run":21,
  "claim":"The 15.42% USDT contraction is one desk closing a position, not the bridge draining.",
  "threshold":"another > 5% contraction = the bridge is draining and ~450K remaining becomes a first-order concern; flat or positive = it was one redemption",
  "branches":[
    {"condition":"another >5% contraction","reading":"on-chain dollar base contracting materially"},
    {"condition":"flat or positive","reading":"a single desk redemption"}],
  "status":"open","outcome":None,"resolved_in_run":None,
  "measured_value":"USDT supply 650,171 -> 549,884 (-100,287 tokens)","resolution":None},
 {"id":"dex-turnover-recovery","registered_in_run":21,
  "claim":"The two-week turnover recovery is a returning bid rather than an artifact of the supply pause.",
  "threshold":"a third rise above ~3.5% with the OTC feed still off = the demand side is genuinely repairing; a reversion below 2.5% = the bounce tracked the supply pause",
  "branches":[
    {"condition":"third rise above 3.5%","reading":"stop describing demand as absent"},
    {"condition":"reversion below 2.5%","reading":"the bounce tracked the supply pause"}],
  "status":"open","outcome":None,"resolved_in_run":None,
  "measured_value":"turnover 2.24% -> 2.93% of pool TVL/day; series 4.06 / 2.14 / 2.24 / 2.93","resolution":None},
 {"id":"mex-relative-strength","registered_in_run":21,
  "claim":"MEX leading EGLD is a genuine relative-value signal, not noise on thin volume.",
  "threshold":"a fifth consecutive week of MEX >= EGLD = a real signal needing a mechanism (buybacks, emissions, rotation); a reversion = four weeks of noise",
  "branches":[
    {"condition":"5th week MEX >= EGLD","reading":"a real signal - identify the mechanism"},
    {"condition":"reversion","reading":"noise on thin volume"}],
  "status":"open","outcome":None,"resolved_in_run":None,
  "measured_value":"MEX +3.57% vs EGLD +2.99% this week; 4 consecutive weeks","resolution":None}]

withdrawn=[
 {"claim":"The direct-node unwind: ~215,000 EGLD left direct-node staking over three weeks, 'the largest unexplained structural flow tracked'.",
  "asserted_in_runs":[18,19,20],"withdrawn_in_run":21,
  "reason":"The residual it was measured from (economics.staked minus summed provider locked) also contains delegation unbonding in flight. One wallet's 229,865 EGLD unDelegate pair explains run #21's entire +282,713 residual flip; corrected, direct-node stake grew +52,848. The prior three weeks' readings are equally consistent with earlier unbondings completing.",
  "replacement":"Decompose the residual with /accounts/{addr}/delegation before attributing it to node operators. The protocol Staking SC returns HTTP 400 on all transaction queries."},
 {"claim":"The first competitive fee repricing in twenty runs: egldstakingprovider cut its service fee 24% -> 15%.",
  "asserted_in_runs":[20],"withdrawn_in_run":21,
  "reason":"One week later the same provider set its fee to 100% (delegator APR 0), and procryptostaking - the incumbent named as the one that had NOT cut - did the same. Different owner wallets, 50 nodes each still running, both still bleeding stake. A wind-down or a squeeze, not competition.",
  "replacement":"A single parameter move by an incumbent under pressure is ambiguous. Wait two weeks, or for stake to actually return, before assigning intent."},
 {"claim":"MEX's outperformance versus EGLD is stale pricing in illiquid pairs.",
  "asserted_in_runs":[19,20],"withdrawn_in_run":21,
  "reason":"Never checked before being repeated. Measured, MEX/WEGLD holds $291,459 of pool TVL - 15.9% of all xExchange depth and the #2 deepest pool on the venue - on 125 trades in 24h. Thin in volume but properly priced.",
  "replacement":"Four consecutive weeks of MEX >= EGLD is real price action with no mechanism identified yet."}]

R["pre_committed_tests"]=tests
R["meta_learning"]["withdrawn_claims"]=withdrawn
json.dump(R,open(p,"w"),indent=2)
res=[t for t in tests if t["status"]=="resolved"]
print(f"injected {len(tests)} tests ({len(res)} resolved, {len(tests)-len(res)} open) + {len(withdrawn)} withdrawn claims")
for t in res: print("  ",t["outcome"],"-",t["id"])
