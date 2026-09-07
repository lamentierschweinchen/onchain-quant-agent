#!/usr/bin/env python3
"""Run #24 stage 5: pre_committed_tests + meta_learning, then merge -> reports/2026-09-07.json"""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-09-07"
O=json.load(open("/tmp/run24w/derived.json"))
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
status=json.load(open("/tmp/run24w/status.json"))
beh=json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
r23=json.load(open(f"{REPO}/reports/2026-08-31.json"))
M=O["macro"]; otc=O["otc"]; wave=otc["wave"]; ex=O["exch"]
cust=O["custody"]; bid=O["bid"]; br=O["breadth"]; sk=O["staking"]; tk=O["tokens"]
xx=O["xexchange"]; df=O["defi"]; ub=O["unbond"]; absb=O["absorbers"]; p2p=O["p2p"]
zsc=O["zero_stake_cohort"]; em=O["emerging_lsd"]; jex=O["jex"]
HOT=O["hot_to_pipe"]; FEED=O["feeders_in"]
price=M["price"]; pc=M["price_chg"]
cvc=beh["aggregates"]["compound_vs_claim_at_function_level"]
def f(x,d=0):
    try: return f"{x:,.{d}f}"
    except: return str(x)
def mv(ident,field,default=0):
    return next((m[field] for m in sk["moves"] if m["identity"]==ident), default)
def V(d_,k): return d_.get(k,0.0)
dser={d["identity"]:d for d in O["dereg_series"]}

prior={t["id"]:t for t in r23["pre_committed_tests"]}
tests=[t for t in r23["pre_committed_tests"] if t["status"]=="resolved"]

def resolve(tid,outcome,measured,resolution):
    t=dict(prior[tid]); t.update({"status":"resolved","outcome":outcome,"resolved_in_run":24,
        "measured_value":measured,"resolution":resolution}); return t

tests.append(resolve("desk-inventory-drain","as_predicted",
  f"desk inventory {f(otc['prev_desk'])} -> {f(otc['desk_bal'])} ({100*otc['desk_delta']/otc['prev_desk']:+.0f}%), well below the 120,000 branch, after delivering a record {f(otc['net_one_way'])} EGLD one-way; wave #3 netted feed-to-drain {f(wave['net_one_way'])}",
  f"The sub-120,000 branch fires cleanly and its registered reading follows: wave #3 is the largest distribution wave in tracking by a factor of more than two ({f(wave['net_one_way'])} EGLD one-way against 409,680 for the run #17 peak). The record inventory was staged supply, not a new operating level - which also REJECTS the candidate regime shift run #23 flagged on the same number, and vindicates the two-week promotion rule that stopped it being published as one. The weekly delivery figure of {f(otc['net_one_way'])} is itself a record, 31% past run #17."))

tests.append(resolve("binance-desk-feed-standing","as_predicted",
  f"Binance.com hot -> known OTC feeders and routers {f(HOT['total_egld'])} EGLD inside a page-capped {HOT['coverage_days']}-day window (a LOWER bound); Binance-labelled feeders delivered {f(FEED.get('Binance',0))} into the desks; custody REVERSED +{f(cust['delta'])} to {f(cust['balance'])} on 900,000 out / 1,272,434 back",
  f"The >50,000 branch fires, so Binance's participation is a standing programme rather than one-off routing - and the flow-based specification is what made that answerable. Run #22 wrote this test on the hot wallet's BALANCE and it failed; run #23 re-specified it on the flow after the failure; this run it resolves on the first attempt. One correction to the registered reading: the branch said a standing programme means 'the custody drawdown is scheduled supply', but custody GREW +{f(cust['delta'])} this week while the feed continued. The feed is real and the custody link is not - the funding comes out of ordinary hot-wallet flow, not out of the custody balance. The two watches stay joined, on the flow rather than on the balance."))

tests.append(resolve("dex-demand-in-egld","as_predicted",
  f"EGLD-denominated volume {f(bid['prev_dexvol_egld'])} -> {f(bid['dexvol_egld'])} per day ({100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}%), below the 60,000 branch; USD turnover {bid['prev_turnover']:.2f}% -> {bid['turnover']:.2f}%; EGLD pool depth {100*(bid['pooltvl_egld']-bid['prev_pooltvl_egld'])/bid['prev_pooltvl_egld']:+.1f}%",
  f"The 'USD turnover tracks price' branch fires. In the largest up-week in the archive the venue processed LESS EGLD than the week before, which settles the question run #22 raised and run #23 pre-registered: the turnover ratio held for two months because both of its terms scale with the EGLD price, not because more EGLD changed hands. The constructive 'the bid is returning' reading carried since run #22 is withdrawn, and xExchange throughput is reported in EGLD as the primary series from here."))

tests.append(resolve("withdrawal-breadth-broadening","as_predicted",
  f"{br['ex_n']} distinct ex-pipeline recipients took {f(br['ex_egld'])} EGLD off exchanges (bar: >40 and >300,000), pipeline share {br['pipeline_share']:.1f}%, zero page-cap terminations",
  f"The broadening branch fires on both terms. The registered reading - 'the strongest bid evidence the model has' - is accepted with a qualification the test could not pre-specify: two recipients account for {100*(br['top'][0]['egld']+br['top'][1]['egld'])/br['ex_egld']:.0f}% of the value, and one of them is the wallet that received 68,732 EGLD directly from the Binance hot wallet, which makes it pipeline-adjacent plumbing rather than independent accumulation. The COUNT broadened genuinely; the VALUE did not disperse. A concentration-adjusted version is registered below."))

tests.append(resolve("compound-rate-drift","as_predicted",
  f"{cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} redelegate vs {cvc['claim_count']} claim), against a 57.0% cut - the highest of eleven readings and a reversal of four consecutive declines",
  f"The 'stabilised' branch fires and the contiguous-branch rule introduced in run #23 does its job: this is the first of three consecutive attempts at this question to resolve on the data rather than on a specification defect. The four-week decline was a level shift, not a drift toward monetising yield, and the compound rate does NOT become a standing bearish indicator. The timing sharpens it: the reversal happened in the week the OTC pipeline delivered a record {f(otc['net_one_way'])} EGLD, so the people already staking compounded harder while the supply arrived from somewhere else entirely."))

tests.append(resolve("stablecoin-base-contraction","as_predicted",
  f"USDC {tk['stable']['USDC-c76f1f']['pct']:+.2f}% ({f(abs(tk['stable']['USDC-c76f1f']['supply']-tk['stable']['USDC-c76f1f']['prev']))} tokens) and USDT {tk['stable']['USDT-f8c08c']['pct']:+.2f}% - a third consecutive combined contraction, about $140K this week and $220K over the three",
  f"The promotion branch fires. Three consecutive weeks of combined contraction, every one into a rising price, is not redemption timing; the on-chain dollar base is now reported as a de-risking instrument alongside USH. The contrast within the same week makes the point: USH MINTED {tk['lsd']['USH-111e09']['pct']:+.2f}% while the dollar base shrank - leverage up, cash base down, which is a specific and coherent picture rather than two unrelated plumbing moves."))

t=dict(prior["fourth-deregistration"])
t.update({"status":"open","measured_value":
  f"NO new transition this week (week 1 of 4): zero providers moved from locked > 0 to zero. But the denominator changed - the widened signature applied to the full stored list finds {zsc['contracts']} contracts at zero locked stake with {f(zsc['attached_delegator_records'])} delegator records attached, of which only four emptied inside the {zsc['archive_snapshots']}-snapshot archive.",
  "resolution":None})
tests.append(t)

def new(tid,claim,threshold,branches,measured):
    return {"id":tid,"registered_in_run":24,"claim":claim,"threshold":threshold,
            "branches":branches,"status":"open","outcome":None,"resolved_in_run":None,
            "measured_value":measured,"resolution":None}

tests += [
 new("wave4-restart",
  "The OTC distribution programme is continuous - wave #3's delivery is followed by another feed rather than by a quiet period.",
  "UPbit tranche into the desks above ~200,000 next week = the programme is continuous and wave #4 has started; tranche below ~50,000 with desk inventory still under ~120,000 = wave #3 is complete and the pipeline goes quiet as it did for two weeks after run #17; 50,000-200,000 = a reduced feed, re-measure without concluding",
  [{"condition":"UPbit tranche > 200,000","reading":"continuous programme; wave #4 under way and supply overhang is structural"},
   {"condition":"tranche < 50,000 and desks < 120,000","reading":"wave #3 complete; the pipeline goes quiet"},
   {"condition":"tranche 50,000-200,000","reading":"reduced feed; re-measure"}],
  f"tranche series 14,000 / 297,000 / 460,000 / {f(otc['upbit_feed'])}; desks {f(otc['desk_bal'])} after delivering {f(otc['net_one_way'])} one-way"),
 new("unidentified-bid-persistence",
  "The bid that absorbed a record {0} EGLD delivery is real off-chain demand rather than a squeeze into thin order books.".format(f(otc['net_one_way'])),
  f"price holding above ~$4.20 next week with no new delivery = the bid is real and off-exchange, and the model needs an instrument it does not currently have; price below ~$3.90 = this week was a squeeze into thin books and the delivery was the whole story; $3.90-$4.20 = inconclusive, carry",
  [{"condition":"price > $4.20","reading":"real off-chain demand; build an exchange-side instrument"},
   {"condition":"price < $3.90","reading":"squeeze into thin books; the delivery was the story"},
   {"condition":"$3.90-$4.20","reading":"inconclusive; carry the test"}],
  f"EGLD ${price:.2f} ({pc:+.2f}%) absorbing {f(otc['net_one_way'])} EGLD of delivery, with every tracked demand instrument flat or negative except ex-pipeline withdrawal breadth"),
 new("staked-ratio-downtrend",
  "The falling staked ratio is a genuine downtrend in the security budget rather than unbonding-cycle noise.",
  "staked ratio below 46.80% within three weeks = a real downtrend that a rising price is not arresting, and it becomes a first-order network-health finding; back above 47.60% = unbonding-cycle noise around a flat base; 46.80-47.60% = still inside the band, carry",
  [{"condition":"staked ratio < 46.80%","reading":"genuine downtrend in the security budget"},
   {"condition":"staked ratio > 47.60%","reading":"unbonding-cycle noise; drop it"},
   {"condition":"46.80-47.60%","reading":"inside the band; carry"}],
  f"{100*M['sr']:.2f}% ({100*(M['sr']-M['sr_prev']):+.3f}pp), an archive low; staked {M['staked_chg']:+,.0f}, delegation {f(sk['delta_locked'])}, unbonding queue {f(sk['undelegated_week'])} EGLD from {sk['undelegate_callers']} wallets"),
 new("breadth-concentration",
  "Ex-pipeline withdrawal breadth measures genuine dispersal rather than a handful of large wallets.",
  "ex-pipeline value above ~300,000 EGLD with the top two recipients taking less than 50% of it = genuine dispersal and the instrument stands as written; top two above 60% again = the instrument is tracking a few large wallets and a concentration-adjusted version replaces it; 50-60% = carry unchanged",
  [{"condition":"top two < 50% of ex-pipeline value","reading":"genuine dispersal; instrument stands"},
   {"condition":"top two > 60%","reading":"the instrument tracks a few wallets; replace it with a concentration-adjusted version"},
   {"condition":"top two 50-60%","reading":"carry unchanged"}],
  f"{br['ex_n']} recipients / {f(br['ex_egld'])} EGLD, top two = {100*(br['top'][0]['egld']+br['top'][1]['egld'])/br['ex_egld']:.0f}% of value, one of them funded directly by the Binance hot wallet"),
 new("dollar-base-fourth-contraction",
  "The wrapped-dollar base is a leading de-risking signal that belongs in the executive summary each week.",
  "a FOURTH consecutive combined USDC+USDT contraction = a leading de-risking signal, promote it to the executive summary permanently; any week of combined expansion = the three-week run was a redemption cycle and it returns to the DeFi section",
  [{"condition":"fourth consecutive combined contraction","reading":"leading de-risking signal; permanent executive-summary line"},
   {"condition":"combined expansion","reading":"redemption cycle; demote to the DeFi section"}],
  f"three consecutive contractions: USDC {tk['stable']['USDC-c76f1f']['pct']:+.2f}%, USDT {tk['stable']['USDT-f8c08c']['pct']:+.2f}%, ~$220K cumulative, all into rising prices"),
 new("jexchange-address-live",
  "The re-derived JEXchange aggregator is the live contract and the four-run data gap was an address problem, not a halted protocol.",
  f"the re-derived router at {jex['candidates'][0]['address'][:16]}... reporting more than ~1,000 transfers next week = the address is correct and JEXchange is restored to the breakdown as an active venue; zero or near-zero = the fees-contract caller trace found a transient contract and the derivation must be redone from a different anchor",
  [{"condition":"re-derived router > 1,000 transfers/week","reading":"address correct; JEXchange restored as an active venue"},
   {"condition":"near zero","reading":"transient contract; re-derive from a different anchor"}],
  f"old aggregator {jex['old_transfers_7d']} transfers for a fourth run; re-derived router {f(jex['candidates'][0]['transfers_7d'])} transfers in 7 days, four further contracts behind it at {', '.join(f(c['transfers_7d']) for c in jex['candidates'][1:5])}"),
]

resolved=[t for t in tests if t["status"]=="resolved" and t.get("resolved_in_run")==24]
as_pred=sum(1 for t in resolved if t["outcome"]=="as_predicted")
hit=100*as_pred/len(resolved) if resolved else 0

R={"pre_committed_tests":tests}
R["meta_learning"]={
 "run_number":24,
 "endpoints_that_worked":status["ok"],
 "endpoints_that_failed":[
   "/tokens/WTAO-3ec9c0: HTTP 404 - kept in the recheck list as a known-bad control, not a live dependency",
   f"Binance.com hot wallet outbound: page-capped at 1,000 txs covering {HOT['coverage_days']} of 7 days, so the {f(HOT['total_egld'])} hot-to-feeder figure is a lower bound",
   f"{len(O['scan_depth']['pagecap_provscan'])} provider unDelegate scans terminated on a page cap even after the deep re-scan"],
 "api_quirks":[
   "A STORAGE CHANGE CAN MANUFACTURE A HEADLINE. Run #23 started storing the FULL /providers list (including locked == 0 entries) in previous.json - the right fix for a real bug. This run, summing num_delegators across the stored list and comparing it to the current locked>0 total produced a -28,141 delegator collapse that is entirely an artifact of the basis change. Any WoW comparison that spans a snapshot-schema change must be recomputed on a common basis, and the assembler now filters previous.json to locked > 0 explicitly.",
   f"THE WIDENED DEREGISTRATION SIGNATURE MATCHES {zsc['contracts']} CONTRACTS, NOT THREE. 'locked == 0 AND (numNodes > 0 OR numUsers > 0)' returns {zsc['contracts']} provider contracts carrying {f(zsc['attached_delegator_records'])} delegator records. Running it backwards over all {zsc['archive_snapshots']} snapshots shows only four emptied inside the archive and only one has any activity at all, so the signature needs a recency qualifier before it can be called deregistration: a transition from locked > 0 observed in the archive, not just a zero reading today.",
   "AN ABSORBER-RETENTION FIGURE COMPUTED ACROSS TWO DIFFERENT WINDOWS IS MEANINGLESS. The run #23 absorber scan set received = max(7-day, wave-window) and forwarded = 7-day only, so received-minus-forwarded manufactured 789,331 EGLD of apparent retention this week on terminals whose balances total 15,534. Retention is now reported on the balance basis. Any derived quantity that subtracts one window's flow from another's is wrong by construction.",
   "PAGINATION BACKOFF WORKED: zero HTTP 429 failures across a run with more requests than any previous one, after exponential backoff was folded into the main collector (run #23 rec #7). paged_txs now records errors separately from empty windows and recorded none.",
   f"THE PRE-FLIGHT ADDRESS VALIDATOR NOW COVERS COLLECTOR SOURCE (run #23 rec #6) and caught the exact bug it was built for on its first run: the invalid Binance hot-wallet literal that run #23 shipped was still present in the copied collector and was flagged before any query was made. Restricting the scan to full 62-character literals in the current run's scripts keeps it to two long-standing known-bad entries.",
   f"A CONTRACT THAT READS ZERO WHILE ITS NEIGHBOURS DO NOT IS AN ADDRESS PROBLEM. The JEXchange aggregator returned 0 transfers for four consecutive runs while its own fees contract reported thousands. Tracing the fees contract's inbound callers found a live router doing {f(jex['candidates'][0]['transfers_7d'])} transfers a week plus four more behind it. Same failure mode as WTAO-3ec9c0, and the same fix: suspect the identifier before the protocol."],
 "data_gaps":[
   "The Binance.com hot wallet is too busy for a 1,000-tx budget - 4.4 days of coverage. Raise its cap or query it by day.",
   f"{f(otc['unresolved_out'])} EGLD of desk outbound and {f(otc['unresolved_in'])} of inbound remain unattributed to a venue after two hops.",
   f"{f(FEED.get('Unattributed',0))} EGLD arrived at the desks from routers whose parent venue is not resolved - the largest single unattributed feeder moved 196,492 EGLD.",
   "Hatom UTK Money Market and OneDex Launchpad still fail bech32 validation, open since run #18, still flagged rather than guessed."],
 "key_findings":[
   f"The desks delivered a record {f(otc['net_one_way'])} EGLD one-way and drained inventory from {f(otc['prev_desk'])} to {f(otc['desk_bal'])}; wave #3 totals {f(wave['net_one_way'])} feed-to-drain, more than double the previous largest wave.",
   f"EGLD rose {pc:+.2f}% through that delivery while BTC and ETH were flat - and no tracked demand instrument identifies the buyer.",
   f"Binance's feed into the desks is a standing programme ({f(HOT['total_egld'])} hot-to-feeder in {HOT['coverage_days']} covered days) but its custody balance ROSE {f(cust['delta'])}, breaking the custody-funds-distribution story.",
   f"{zsc['contracts']} provider contracts hold zero stake with {f(zsc['attached_delegator_records'])} delegator records attached; only four emptied inside the archive and only one shows any activity.",
   f"Third consecutive contraction in the wrapped-dollar base while USH minted {tk['lsd']['USH-111e09']['pct']:+.2f}% - cash out, leverage in.",
   "JewelSwap's 25,073 JWLEGLD is a 1:1 deposit token, not a staking receipt: its delegated stake is 1,799 EGLD, the smallest of the four discovered protocols rather than the largest.",
   f"The JEXchange aggregator address was stale for four runs; the live router does {f(jex['candidates'][0]['transfers_7d'])} transfers a week."],
 "action_items_from_previous":len(r23["meta_learning"]["recommendations_for_next_run"]),
 "action_items_completed_detail":[
   "MAINTAIN THE SCOREBOARD - all six resolvable open tests resolved as predicted, the seventh (fourth-deregistration) is a four-week test in week 1, and six new tests are registered with contiguous, partitioning branches.",
   "RECONCILE THE DASHBOARD WORKING TREE WITH HEAD - verified: HEAD's App.tsx now imports pages/HomePage and pages/CodePage, the working tree is clean, and the panels that were live only by accident of local state are committed.",
   "RE-TEST EVERY STANDING FAILURE - a pre-flight recheck queried all four of run #23's recorded failures: three had recovered (WTAO-4f5363, the Binance hot wallet, the unbond delegation call) and are reported under data_sources_recovered; only the known-bad WTAO-3ec9c0 control still fails.",
   "RUN THE LIQUID-STAKING SWEEP EVERY WEEK AND MEASURE WHAT IT FINDS - the sweep ran, found two new protocols at 1-2 EGLD (below the 100 EGLD floor, not added), and caught an error before publication: JewelSwap measured on token supply looked like the largest of the four discovered protocols at 25,073, but JWLEGLD is a 1:1 deposit token and the delegated stake is 1,799 EGLD, the smallest. All four are now in the breakdown on the delegated-stake basis.",
   "RESOLVE THE DESK-INVENTORY DRAIN - resolved as predicted, and it is the report's headline: 266,213 -> 96,114 while delivering a record 536,459.",
   "EXTEND validate_addresses.py TO COVER COLLECTOR SOURCE - done, and it caught run #23's invalid Binance literal in the copied collector before the first query.",
   "FIX paged_txs TO DISTINGUISH ERROR FROM EMPTY, AND ADD 429 BACKOFF - done; zero paged errors and zero 429 failures on the largest run so far.",
   "STORE THE FULL /providers LIST IN previous.json - already implemented in run #23; this run added the guard that stops the basis change from manufacturing a delegator collapse.",
   "TRACK THE THREE DEREGISTERED PROVIDERS' DELEGATOR COUNTS AS A STANDING SERIES - done: ledgerbyfigment -7 to 3,876, stakedinc unchanged at 637, p2p_org_ unchanged at 1,244.",
   f"RAISE THE PROVIDER-SCAN PAGE CAP FOR BUSY CONTRACTS - done: {len(O['scan_depth']['deep_scanned'])} contracts that filled the 6-page budget were re-paged at 30 pages.",
   f"RE-DERIVE THE JEXCHANGE AGGREGATOR ADDRESS - done via the fees contract's inbound callers; the live router does {f(jex['candidates'][0]['transfers_7d'])} transfers a week.",
   "REPORT DEX TURNOVER IN EGLD TERMS AS THE PRIMARY SERIES - done, and the pre-committed test resolved against the USD ratio.",
   "WATCH FOR A THIRD CONSECUTIVE STABLECOIN CONTRACTION - it came; the dollar base is promoted to a de-risking instrument."],
 "methodology_changes":[
   "COMPARE ACROSS A SNAPSHOT-SCHEMA CHANGE ON A COMMON BASIS. When the shape of previous.json changes, every WoW derived from it must be recomputed on the old basis or the change itself becomes the finding.",
   "A DERIVED QUANTITY MUST NOT SUBTRACT ONE WINDOW'S FLOW FROM ANOTHER'S. The absorber retention figure did exactly that; retention is now measured on end-of-week balance.",
   "A RECEIPT TOKEN'S SUPPLY IS A TVL PROXY ONLY WHEN THE TOKEN IS THE RECEIPT. JWLEGLD is a 1:1 EGLD-pegged deposit token with 25,073 supply against 1,799 EGLD delegated; LEGLD appreciates, so 5,058 tokens are 6,431 EGLD of stake. Compare supply against delegated stake before publishing either.",
   "A ZERO READING ON A TRACKED CONTRACT IS AN ADDRESS PROBLEM UNTIL PROVEN OTHERWISE, and the fix is to trace the neighbours that still report - here, the fees contract's inbound callers.",
   "A DETECTION SIGNATURE NEEDS A RECENCY QUALIFIER. 'locked == 0 with users attached' describes 82 contracts, most of them long dead. Deregistration means an observed TRANSITION in the archive, not a zero reading today.",
   "REJECTING A CANDIDATE REGIME SHIFT IS A RESULT. Run #23's two-week promotion rule stopped a one-week staging spike being published as a new level; this run it drained. Keep the rule."],
 "new_addresses_discovered_detail":[
   {"address":jex["candidates"][0]["address"],"label":"JEXchange: live aggregator (re-derived run #24)",
    "evidence":f"{f(jex['candidates'][0]['transfers_7d'])} transfers in 7 days and the largest caller on the JEXchange fees contract's inbound leg, while the previously tracked aggregator returned 0 for four runs"},
   {"address":"erd1tx933j8r57smz7s7c6y4p4nzx9np968gpt66escfym3908k3zcqqcde3y8",
    "label":"Unknown - large ex-pipeline withdrawal recipient, Binance hot-funded",
    "evidence":f"took {f(br['top'][1]['egld'])} EGLD off exchanges outside the pipeline this week and separately received 68,732 EGLD directly from the Binance.com hot wallet"}],
 "action_items_completed":13,
 "new_addresses_discovered":2,
 "most_valuable_insight":(
   f"The record inventory drained exactly as the pre-committed test's first branch described, and that is the least interesting part. The finding is what happened to the price while it drained: {f(otc['net_one_way'])} EGLD - the largest one-way delivery ever measured on this chain - hit exchange order books and EGLD rose {pc:+.2f}% through it, with BTC and ETH flat. "
   f"Every demand instrument the model owns reads negative or zero: DEX throughput in EGLD terms {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}%, LSD supply flat for a seventh week, the staked ratio at an archive low, the identifiable-bid proxies at zero for a fourth week. "
   f"That is a real gap in the model, not a real absence of buyers, and naming it is more useful than filling it with a story."),
 "top_recommendation":(
   "BUILD AN EXCHANGE-SIDE DEMAND INSTRUMENT. The model can measure supply arriving at order books to the EGLD and cannot measure anything that happens after it arrives. "
   "Every demand proxy built so far - absorber wallets, Mega Whale balance, DEX turnover, withdrawal breadth - is an on-chain shadow of an off-chain decision, and this week all of them read empty against a price that rose 17%. "
   "Candidates: exchange-reported order-book depth or volume for the venues the pipeline delivers to, or a Bybit/Binance netflow series from a third-party API. Without one, weeks like this end in 'the buyer is not visible', which is honest and not useful."),
 "recommendations_for_next_run":[
   "RESOLVE WAVE #4 OR CALL THE PROGRAMME COMPLETE. The desks are empty for the first time since run #21 and the UPbit tranche has run at ~460,000 for three weeks. The registered branches are a tranche above 200,000 (continuous programme) or below 50,000 with desks still under 120,000 (wave #3 complete). This is the single highest-value query of the week and it is one number.",
   "BUILD OR SOURCE ONE EXCHANGE-SIDE DEMAND INSTRUMENT, even a crude one. A record delivery was absorbed with a 17% price rise and the report cannot say by whom. Start with a third-party exchange netflow or order-book depth series for Bybit and Binance.com, the two venues the pipeline delivers into; anything that turns 'the bid is not visible' into a measurement.",
   "RAISE THE BINANCE HOT-WALLET PAGE BUDGET OR QUERY IT BY DAY. Its outbound filled a 1,000-tx budget in 4.4 days, so this run's hot-to-feeder figure is a lower bound on a number that resolved a pre-committed test. Query it in daily slices and sum.",
   "ADD A RECENCY QUALIFIER TO THE DEREGISTRATION DETECTOR. 'locked == 0 with users attached' matches 82 contracts, 78 of which predate the archive. The signature should require an observed transition from locked > 0 in a stored snapshot, and the fourth-deregistration test should be scored on that definition.",
   "ATTRIBUTE THE UNATTRIBUTED FEEDERS. About 344,000 EGLD reached the desks from routers whose parent venue is unresolved, including one moving 196,492 alone. Two hops back from that wallet would probably name a fifth feeding venue, and the feed side is now the more interesting half of the pipeline.",
   "RE-QUERY THE JEXCHANGE ROUTER AND PROMOTE IT INTO THE COLLECTOR'S PROTOCOL SET. The re-derived address is registered as a pre-committed test; if it reports again next week, replace the stale contract in known-addresses and add the four secondary routers to the DeFi breakdown.",
   "MEASURE WHETHER THE DESK-EMPTY STATE COINCIDES WITH A PRICE RETRACEMENT. The unidentified-bid test is registered on price alone ($4.20 / $3.90). Pair it with the pipeline state so the answer separates 'no supply, price holds' from 'no supply, price falls anyway' - the second would say this week's rise was mechanical.",
   "KEEP THE EMERGING-LSD SWEEP AND ADD HOLDER COUNTS TO THE SERIES. VoxEGLD grew supply 7.7% and holders from 78 to 113 while every established LSD sat still. Holders is the leading indicator on a base this small, and it is one field.",
   "CHECK WHETHER THE TWO FEE-REVERSED PROVIDERS RECOVER ANY STAKE. egldstakingprovider went 100% -> 50% and procryptostaking 100% -> 35%, both with APR restored, and both still lost book and users this week. A second week of losses would make 'capital does not come back' a measured asymmetry rather than one observation."],
 "dashboard_feature_suggestions":[
  {"title":"Staging vs delivery - the desk inventory line over the delivery bars",
   "motivation":"BUILT THIS RUN, and this is the week that proves the case: run #23 reported a record 266,213 inventory against 272,396 delivered, and this run the inventory fell to 96,114 while delivery hit a record 536,459. Those two facts are the same story and the panel previously showed the second one only, with inventory as a single stat tile. A reader looking at the bars alone would have seen 'another big delivery week' rather than 'the warehouse emptied'.",
   "suggested_visualization":"dashed inventory line with per-run dots drawn over the existing gross/net bars in the OTC pipeline chart, sharing the y-scale, with the legend switching to 'Delivered per week vs what stayed staged' when the series is present",
   "data_already_available":True,
   "data_source":"whale_intelligence.otc_pipeline.desk_inventory_series_egld (new field this run, backfilled from previous.json's otc_desk_inventory_series for runs #21-#23)",
   "priority":"high"},
  {"title":"Feed-side attribution - who fills the desks, not just who they deliver to",
   "motivation":"The pipeline's delivery side has been mapped for six runs; this week the FEED side became the more interesting half and there is nowhere to show it. UPbit sent 462,000, Bybit-labelled feeders 304,700, Binance-labelled feeders 200,046, and 343,872 arrived from routers whose parent venue is unresolved - including one wallet moving 196,492 on its own. The venue_netting table nets both legs into one signed number per venue, which hides that a venue can be a large feeder and a large destination at once.",
   "suggested_visualization":"a two-column sankey or paired horizontal bars - sources on the left, desks in the middle, destinations on the right - with the unattributed feeder share drawn explicitly as its own band so the size of the gap is visible rather than implied",
   "data_already_available":False,
   "data_source":"needs a new report field: whale_intelligence.otc_pipeline.feed_by_parent_venue, derivable from data already collected in desk_inbound_paged (computed this run as feeders_in but not yet published)",
   "priority":"high"},
  {"title":"Demand-instrument scorecard - show the model's blind spot as a row of empties",
   "motivation":"This run's most valuable insight is a negative: a record delivery was absorbed and no instrument identifies the buyer. That conclusion is currently spread across four sections (DEX volume in the token panel, LSD supply in DeFi, absorber scan and withdrawal breadth in whale intelligence, staked ratio in network health). A reader has to assemble it. A single row of instruments with their readings would make 'everything the model can see says no demand, and the price rose 17%' visible at a glance - and would make it obvious in a future week when one of them finally lights up.",
   "suggested_visualization":"a compact scorecard strip - one tile per demand instrument (DEX EGLD volume, LSD supply, staked ratio, identifiable bid, ex-pipeline breadth) showing this week's reading, its direction, and how many consecutive weeks it has read flat or negative",
   "data_already_available":True,
   "data_source":"whale_intelligence.demand_instruments plus token_activity.xexchange.dex_volume_egld_24h, defi_activity.protocol_breakdown LSD rows, network_health.economics.staked_ratio",
   "priority":"medium"}],
 "dashboard_suggestions_followup":[
  {"title":"Desk inventory vs delivery - the staging chart","status":"built",
   "note":"Built this run in dashboard/src/components/OtcPipeline.tsx: the inventory series is published as otc_pipeline.desk_inventory_series_egld and drawn as a dashed line with per-run dots over the existing bars, sharing the y-scale. Run #23 deferred it because the dashboard working tree carried uncommitted work from another session; that work is now committed to HEAD, so the blocker is gone."},
  {"title":"Provider lifecycle strip - now with three real cases and a decay series","status":"pending",
   "note":"Not built, and its framing needs revision before it is. This run shows 82 zero-stake contracts rather than three, of which only one has any activity - a strip of 82 chips would be noise. The right version is the four archive-observed transitions plus the two fee-reversed providers, driven off staking_intelligence.provider_states, which now carries exactly those rows."},
  {"title":"Errata linkage from the withdrawn claim to its replacement","status":"pending",
   "note":"Not built. No new withdrawn claim this run, so the case neither strengthened nor weakened; it stays queued behind the two panels above."},
  {"title":"OTC hub flow map: gross vs net one-way, with venue-level netting","status":"pending",
   "note":"Superseded in scope rather than dropped: this run's feed-side attribution suggestion is the same graph seen from the other end, and the two should be built as one panel. Fourth run of asking, and the case is now strongest on the feed side, where three source venues and 344,000 EGLD of unattributed routing are invisible in the signed table."}],
 "withdrawn_claims":[
  {"claim":"Two consecutive USH burns into a rising price make CDP debt repayment a behaviour rather than an oddity.",
   "asserted_in_runs":[22,23],"withdrawn_in_run":24,
   "reason":f"USH MINTED {tk['lsd']['USH-111e09']['pct']:+.2f}% this week ({f(tk['lsd']['USH-111e09']['supply']-tk['lsd']['USH-111e09']['prev'])} tokens), reversing both burns and taking the supply above where the sequence started. A pattern called at two observations lasted one more week.",
   "replacement":"The run #16 framing stands unmodified: CDP leverage returns on large up-weeks. The two burns were repayment through a moderate rally (+6.4% and flat weeks); a +17.0% week brought borrowing back immediately. The general lesson is the one run #21 already wrote down - two observations are not a behaviour, and naming one costs a withdrawal later."},
  {"claim":"Desk inventory has stepped to a new level - a candidate regime shift in the pipeline's operating scale.",
   "asserted_in_runs":[23],"withdrawn_in_run":24,
   "reason":f"Inventory fell {f(otc['prev_desk'])} -> {f(otc['desk_bal'])} within one week, so the level did not hold. Run #23 flagged it as a CANDIDATE and explicitly declined to promote it under the two-week rule, which is why this is a candidate being rejected rather than a published claim being withdrawn.",
   "replacement":"The 266,213 was a one-week staging peak inside wave #3, and the wave's true scale is the feed-to-drain figure of "+f(wave['net_one_way'])+" EGLD. The two-week promotion rule earned its keep and stays."}]}

rep={}
rep.update(json.load(open("/tmp/run24w/part1.json")))
rep.update(json.load(open("/tmp/run24w/part2.json")))
p3=json.load(open("/tmp/run24w/part3.json"))
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
