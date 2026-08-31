#!/usr/bin/env python3
"""Run #23 stage 3: staking, tokens, defi -> /tmp/run23w/part2.json"""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-08-31"
O=json.load(open("/tmp/run23w/derived.json"))
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
beh=json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
M=O["macro"]; sk=O["staking"]; tk=O["tokens"]; xx=O["xexchange"]; df=O["defi"]
bid=O["bid"]; ub=O["unbond"]; p2p=O["p2p"]
econ=D["economics"]; price=M["price"]; pc=M["price_chg"]
def f(x,d=0):
    try: return f"{x:,.{d}f}"
    except: return str(x)
provs=sk["provs"]; tl=sk["total_locked"]
pkey={p["provider"]:p for p in prev["staking_providers"]}
def pk(p): return p.get("identity") or p["provider"]
ag=beh["aggregates"]; cvc=ag["compound_vs_claim_at_function_level"]
def mv(ident,field,default=0):
    return next((m[field] for m in sk["moves"] if m["identity"]==ident), default)
R={}

top_providers=[]
for i,p in enumerate(provs[:20],1):
    k=pk(p); pl=pkey.get(k,{}).get("locked_egld")
    top_providers.append({"rank":i,"identity":k,"name":k,"provider_address":p["provider"],
      "locked_egld":p["_lk"],"previous_locked_egld":pl,
      "share_pct":100*p["_lk"]/tl,"apr_pct":p.get("apr") or 0,
      "fee_pct":(p.get("serviceFee") or 0)*100,"num_users":p.get("numUsers") or 0,
      "num_nodes":p.get("numNodes") or 0,
      "wow_change_egld":(p["_lk"]-pl) if pl is not None else None})

pool_rows=sk["pool_rows"][:12]

# provider states (the run #22 dashboard suggestion's data, produced this run)
states=[]
for x in sk["dereg"]:
    states.append({"provider":x["key"],"state":"deregistered","locked_egld":0.0,
                   "num_users":x["users"],"num_nodes":x["nodes"],"apr_pct":0.0,
                   "fee_pct":(x["fee"] or 0)*100,
                   "weeks_in_state":11 if x["key"]=="ledgerbyfigment" else (13 if x["key"]=="stakedinc" else 1),
                   "note":("zero-locked since the 2026-06-15 snapshot (run #13 window); 170,808 EGLD and 3,961 delegators at the time - never reported"
                           if x["key"]=="ledgerbyfigment" else
                           "zero-locked with 10 nodes across the ENTIRE stored snapshot history (2026-06-01 onward)")})
states.append({"provider":"p2p_org_","state":"deregistered","locked_egld":0.0,
  "num_users":p2p["users_now"],"num_nodes":p2p["nodes"],"apr_pct":0.0,
  "fee_pct":12.0,"weeks_in_state":2,
  "note":f"EXIT COMPLETED this week - owner called removeNodes x{p2p['function_counts'].get('removeNodes',0)} plus unBondNodes, numNodes 50 -> 0. 1,244 delegators still attached; {p2p['function_counts'].get('unDelegate',0)} unDelegate calls all week against {p2p['function_counts'].get('reDelegateRewards',0)} reDelegateRewards on a contract paying nothing."})
for ident in ("egldstakingprovider","procryptostaking"):
    states.append({"provider":ident,"state":"zero_apr","locked_egld":mv(ident,"locked"),
      "num_users":mv(ident,"users"),"num_nodes":mv(ident,"nodes"),"apr_pct":0.0,"fee_pct":100.0,
      "weeks_in_state":3,
      "note":f"serviceFee 1.0 / APR 0 for a third week. Book {mv(ident,'delta'):+,.0f} this week; users {mv(ident,'users_delta'):+d}."})

R["staking_intelligence"]={
 "summary":{"total_staked_egld":econ["staked"],"total_delegated_egld":tl,
   "staked_ratio":M["sr"],"num_providers":len(provs),
   "apr_min":sk["apr_min"],"apr_max":sk["apr_max"],"apr_weighted_avg":sk["apr_wavg"]},
 "top_providers":top_providers,
 "concentration":{"top_5_share_pct":sk["top5"],"top_10_share_pct":sk["top10"],
   "hhi":sk["hhi"],"hhi_previous":sk["prev_hhi"],
   "hhi_interpretation":f"HHI {sk['hhi']:.5f} (previous {sk['prev_hhi']:.5f}), far below the 0.15 competitive threshold; top-5 {sk['top5']:.2f}%, top-10 {sk['top10']:.2f}%. Both edged up as two distressed books shrank out of the denominator. The delegation market remains the least concentrated part of the network - and that is precisely why the distressed tail matters: concentration is not the risk here, operator attrition is."},
 "apr_distribution":{"buckets":sk["buckets"],
   "zero_apr_providers":sk["zero_apr_n"],"zero_apr_locked_egld":sk["zero_apr_locked"]},
 "apr_outliers":{
   "top_apr":[{"identity":pk(p),"name":pk(p),"apr_pct":p.get("apr") or 0,
     "fee_pct":(p.get("serviceFee") or 0)*100,"locked_egld":p["_lk"]}
     for p in sorted(provs,key=lambda x:-(x.get("apr") or 0))[:5]],
   "lowest_fee":[{"identity":pk(p),"name":pk(p),"apr_pct":p.get("apr") or 0,
     "fee_pct":(p.get("serviceFee") or 0)*100,"locked_egld":p["_lk"]}
     for p in sorted(provs,key=lambda x:((x.get("serviceFee") or 0),-(x.get("apr") or 0)))[:5]]},
 "churn":{"total_delegators_current":sk["users"],"total_delegators_previous":sk["prev_users"],
   "delegators_added":sk["users_delta"],
   "delegators_change_pct":100*sk["users_delta"]/sk["prev_users"],
   "providers_gaining_delegators":sk["gaining"],"providers_losing_delegators":sk["losing"]},
 "provider_states":states,
 "fee_events":[
   {"provider":"egldstakingprovider","fee_from_pct":100.0,"fee_to_pct":100,
    "apr_from_pct":0.0,"apr_to_pct":0,
    "locked_egld":mv("egldstakingprovider","locked"),
    "locked_wow_egld":mv("egldstakingprovider","delta"),
    "users":mv("egldstakingprovider","users"),
    "users_wow":mv("egldstakingprovider","users_delta"),"num_nodes":50},
   {"provider":"procryptostaking","fee_from_pct":100.0,"fee_to_pct":100,
    "apr_from_pct":0.0,"apr_to_pct":0,
    "locked_egld":mv("procryptostaking","locked"),
    "locked_wow_egld":mv("procryptostaking","delta"),
    "users":mv("procryptostaking","users"),
    "users_wow":mv("procryptostaking","users_delta"),"num_nodes":50}],
 "unbonding_in_flight":{
   "wallet":ub["wallet"],
   "total_egld":ub["pending_total"],
   "legs":[{"provider":(p["contract"][:10]+"..."+p["contract"][-8:]),
            "amount":p["amount_egld"],"days_to_unbond":p["days_remaining"],
            "date":"2026-08-14" if p["amount_egld"]<100000 else "2026-08-15"}
           for p in ub["pending"]],
   "share_of_delegation_decline_pct":0.0,
   "raw_residual_egld":sk["residual"],
   "corrected_direct_node_egld":None,
   "status":(f"UNMOVED FOR A SECOND FULL WEEK - RETIRED AS A LIVE FLOW. Balance unchanged at {f(ub['balance'],2)} EGLD, "
             f"{f(ub['pending_total'])} still unbonded-and-unclaimed inside the delegation contracts, zero outbound transactions and zero function calls in the window. "
             f"That is the no-action branch run #22 added to the test after it failed to resolve for want of one. The holder is inactive or has lost access; the overhang stops being tracked as forward supply."),
   "queue_this_week":{
     "undelegated_egld":sk["undelegated_week"],
     "distinct_callers":sk["undelegate_callers"],
     "measured_pending_egld":sk["pool_total"],
     "largest_legs":pool_rows,
     "coverage_note":(f"FIRST FULL-SET SCAN (run #22 rec #5): all {sk['providers_scanned']} provider contracts with locked > 0 or nodes > 0 were paged for unDelegate calls, not just the movers. "
                      f"{sk['undelegate_callers']} distinct wallets unDelegated {f(sk['undelegated_week'])} EGLD - 2.1x the 70,498 run #22 measured across ten providers, which tells you how much the partial scan was missing. "
                      f"/accounts/{{addr}}/delegation was then queried for the 45 largest callers, giving {f(sk['pool_total'])} EGLD of measured pending unbonding. "
                      f"CAVEAT: {len([p for p in (D.get('_pagecap_terminations') or []) if p.get('tag')=='provscan'])} provider scans terminated on the 6-page cap, so the {f(sk['undelegated_week'])} figure is a LOWER bound on the busiest contracts.")}},
 "reward_behavior":{
   "providers_sampled":ag["providers_sampled"],
   "delegator_window_days":ag["window_days"],
   "operator_window_days":ag["operator_window_days"],
   "function_distribution":ag["overall_function_distribution"],
   "compound_pct_at_function_level":cvc["compound_pct_of_reward_decisions"],
   "compound_vs_claim":{"redelegate_count":cvc["redelegate_count"],
                        "claim_count":cvc["claim_count"]},
   "delegator_fates_by_tier":ag["delegator_fates_by_tier"],
   "provider_operators":[{"provider":pr.get("identity") or pr.get("provider_address"),
     "owner_address":(pr.get("operator") or {}).get("owner_address") or pr.get("owner_address"),
     "owner_label":(pr.get("operator") or {}).get("owner_label","Unknown"),
     "owner_balance_egld":(pr.get("operator") or {}).get("owner_balance_egld"),
     "outbound_count":(pr.get("operator") or {}).get("outbound_count_30d",0),
     "fates_by_count":(pr.get("operator") or {}).get("fates_by_count",{}),
     "fates_by_value_egld":(pr.get("operator") or {}).get("fates_by_value_egld",{})}
     for pr in beh.get("per_provider",[])],
   "key_findings":[
     f"Compound rate {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} reDelegateRewards vs {cvc['claim_count']} claimRewards) - a FOURTH consecutive decline and the lowest of ten readings (58.54 / 60.35 / 61.59 / 60.19 / 58.81 / 62.25 / 59.54 / 59.07 / 57.03 / {cvc['compound_pct_of_reward_decisions']:.2f}).",
     "THE PRE-COMMITTED TEST LANDED BETWEEN ITS BRANCHES. Run #22 registered 'below 56% = systematic monetisation, above 59% = rally-week spike'. 57.51% is neither, so the test resolves INCONCLUSIVE - the second run in a row a test could not resolve on a specification defect rather than on the data. Branches must be contiguous.",
     "Interpreted on the trend rather than the threshold: four consecutive declines through a flat week, a +30% week and a +6% week is not price-following behaviour. It is a slow drift toward taking yield in cash.",
     f"INSTITUTIONAL TIER SOLD AGAIN: 3 of 6 institutional claims (50-1000 EGLD) went to a labelled exchange, {ag['delegator_fates_by_tier']['institutional']['by_value_egld'].get('sold',0):.0f} EGLD sold against {ag['delegator_fates_by_tier']['institutional']['by_value_egld'].get('held',0):.0f} held. Second consecutive week this tier has led with selling.",
     f"RETAIL STILL DOES NOT SELL - a tenth consecutive run. {ag['delegator_fates_by_tier']['retail']['total_events']} retail claims, ZERO to any labelled exchange; 41 held, 8 unlabelled, 4 rotated provider, 1 into DeFi.",
     "Mid-tier (1-50 EGLD): 18 held, 14 unlabelled, 2 provider rotations, no exchange destinations.",
     f"unDelegate was {ag['overall_function_distribution'].get('unDelegate',{}).get('share_pct',0):.2f}% of observed function calls and withdraw {ag['overall_function_distribution'].get('withdraw',{}).get('share_pct',0):.2f}% - both consistent with the doubled unbonding queue measured across the full provider set.",
     "PROVIDER OPERATORS DID NOT SELL FEES for an eleventh consecutive run. Zero exchange destinations across all sampled owner wallets in 30 days; truststaking's owner (XOXNO: Deployer Wallet) again made the only sizeable move, 2,484.56 EGLD into a DeFi contract.",
     f"Sample: 8 providers, {sum(v['count'] for v in ag['overall_function_distribution'].values())} function calls, {sum(t['total_events'] for t in ag['delegator_fates_by_tier'].values())} traced claims."]},
 "analysis":(
  f"THE HEADLINE IS A CORRECTION TO OUR OWN HEADLINE. Run #22 called p2p_org_ 'the first operator deregistration in tracking' and built a narrative on it. Applying run #22's own detection signature - locked == 0 with numNodes > 0 - to the stored snapshot archive shows that was wrong twice over. "
  f"ledgerbyfigment went from 170,808 EGLD to zero between the 2026-06-08 and 2026-06-15 snapshots, inside the run #13 window, keeping 7 nodes and 3,961 delegators; it has been sitting at zero locked and 0% APR ever since and was never reported. stakedinc has been in the same state, with 10 nodes and ~639 users, for the entire stored history. "
  f"p2p_org_ was the third. The reason both were missed is the one run #22 identified and only half-fixed: 'providers leaving' logic keyed on set membership, and previous.json only ever stored providers with locked > 0, so a provider that goes to zero simply drops out of the comparison rather than showing up as an event.\n\n"
  f"P2P.ORG's EXIT COMPLETED THIS WEEK. Its owner wallet called removeNodes {p2p['function_counts'].get('removeNodes',0)} times plus unBondNodes once, taking numNodes from 50 to 0. The contract now shows zero locked, zero nodes, zero APR - and {p2p['users_now']:,} delegators still attached. "
  f"Note that this breaks the detection signature itself: a fully exited operator has no nodes left, so 'locked == 0 AND numNodes > 0' no longer matches p2p_org_. The signature needs widening to 'locked == 0 AND (numNodes > 0 OR numUsers > 0)'.\n\n"
  f"AND THAT GIVES THE INERTIA EXPERIMENT ELEVEN WEEKS OF DATA INSTEAD OF ONE. Run #22 registered a test on whether p2p_org_'s 1,244 stranded delegators would move. This week they produced {p2p['function_counts'].get('unDelegate',0)} unDelegate calls - 0.16% of the book - against {p2p['function_counts'].get('reDelegateRewards',0)} reDelegateRewards and {p2p['function_counts'].get('claimRewards',0)} claimRewards on a contract that generates nothing at all. "
  f"But ledgerbyfigment is the real evidence: ELEVEN weeks at zero yield, and its delegator count has gone 3,961 -> 3,883, a loss of 78 people, 2.0%. stakedinc has lost 2 of 639 across the whole archive. "
  f"Set that against the two 100%-fee providers, whose BOOKS have collapsed - egldstakingprovider 94,349 -> {f(mv('egldstakingprovider','locked'))} in two weeks ({100*mv('egldstakingprovider','delta')/79639:.1f}% this week, -51.8% over three) and procryptostaking 156,917 -> {f(mv('procryptostaking','locked'))} ({100*mv('procryptostaking','delta')/141804:.1f}% this week, -20.5% over two) - while their user counts fell only {mv('egldstakingprovider','users_delta'):+d} and {mv('procryptostaking','users_delta'):+d}. "
  f"The conclusion is now solid enough to state plainly: in this delegation market capital responds to price signals and people do not. A total loss of yield moves roughly 2% of a user base per quarter and roughly half of its EGLD per month.\n\n"
  f"UNDERNEATH, THE MARKET WAS QUIET. Delegation TVL fell {sk['delta_locked']:+,.0f} to {f(tl)} with only {len(sk['movers'])} providers moving more than 5,000 EGLD, and two of those are the 100%-fee pair. "
  f"The largest genuine mover was the system aggregator contract at {mv('erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqlhllllsr0pd0j','delta',0):+,.0f}; below it vaporrepublic {mv('vaporrepublic','delta'):+,.0f}, ninjastaking {mv('ninjastaking','delta'):+,.0f}, valuestaking {mv('valuestaking','delta'):+,.0f} and oxsyai {mv('oxsyai','delta'):+,.0f}. "
  f"The delegator base moved {sk['users_delta']:+,} to {f(sk['users'])} - flat, and this week with no deregistration artifact to net out, which makes it the cleanest confirmation of the run #18 inertia base rate the model has had. {sk['gaining']} providers gained delegators and {sk['losing']} lost them.\n\n"
  f"THE UNBONDING QUEUE, SCANNED IN FULL FOR THE FIRST TIME. Run #22 measured 70,498 EGLD of unDelegations across the ten providers that had moved; this run paged all {sk['providers_scanned']} contracts and found {f(sk['undelegated_week'])} EGLD from {sk['undelegate_callers']} distinct wallets - 2.1x. "
  f"The partial scan was not slightly incomplete, it was missing more than half. Measured pending unbonding across the 45 largest callers is {f(sk['pool_total'])} EGLD, the largest single leg 40,888 from a wallet holding 10 EGLD. "
  f"That in turn settles the residual question the same way as last week: staked rose {M['staked_chg']:+,.0f} while delegation fell {sk['delta_locked']:+,.0f}, giving a residual of {f(sk['residual'])} against {f(sk['undelegated_week'])} of measured unbonding in flight. "
  f"The residual is fully absorbed with room to spare, so corrected_direct_node_egld is published as null for a second run - and the run #22 rule that produced that answer is now confirmed rather than merely asserted.\n\n"
  f"THE RUN #21 UNBOND IS RETIRED. {f(ub['pending_total'])} EGLD, fully unbonded, sat unmoved for a second consecutive week: wallet balance unchanged at {f(ub['balance'],2)}, zero outbound transactions, zero function calls. The no-action branch fires and the position stops being tracked as a live forward flow."),
}

# ---------------- tokens ---------------------------------------------------
ph={t["identifier"]:t for t in prev["top_tokens_by_holders"]}
pv={t["identifier"]:t for t in prev["top_tokens_by_volume"]}
def th(t):
    i=t["identifier"]; prevh=ph.get(i,{}).get("holders")
    return {"identifier":i,"name":t.get("name"),"holders":t.get("accounts") or 0,
            "previous_holders":prevh,
            "holders_change":(t.get("accounts",0)-prevh) if prevh is not None else None,
            "price_usd":t.get("price"),"market_cap_usd":t.get("marketCap"),
            "volume_24h_usd":None}
def tv(t):
    i=t["identifier"]; pt=pv.get(i,{}).get("transactions")
    return {"identifier":i,"name":t.get("name"),"transactions":t.get("transactions") or 0,
            "previous_transactions":pt,
            "change_pct":(100*(t.get("transactions",0)-pt)/pt) if pt else None,
            "price_usd":t.get("price"),"volume_24h_usd":None}
def tm(t):
    i=t["identifier"]
    return {"identifier":i,"name":t.get("name"),"holders":t.get("accounts"),
            "previous_holders":ph.get(i,{}).get("holders"),
            "price_usd":t.get("price"),"market_cap_usd":t.get("marketCap"),
            "volume_24h_usd":None}
mexd=xx["mex_pair_depth"]
R["token_activity"]={
 "top_by_holders":[th(t) for t in D["tokens_holders"][:10]],
 "top_by_volume":[tv(t) for t in D["tokens_txs"][:10]],
 "top_by_market_cap":[tm(t) for t in D["tokens_mcap"][:10]],
 "newly_issued":[{"identifier":t["identifier"],"name":t["name"],"holders":t["accounts"],
                  "transactions":t["transactions"],"deployer":t["deployer"],
                  "note":"below the >10 holder / >5 tx quality bar"} for t in tk["newly"]],
 "xexchange":{"total_pairs":xx["pairs"],"total_volume_24h_usd":xx["vol"],
   "mex_price_usd":xx["mex_price"],"mex_market_cap_usd":xx["mex_mcap"],
   "mex_price_change_24h_pct":None,"mex_price_change_wow_pct":xx["mex_wow"],
   "top_pair":xx["top_pairs"][0]["name"],
   "top_pair_volume_24h_usd":xx["top_pairs"][0]["volume_24h_usd"],
   "top_pair_dominance_pct":xx["top_pairs"][0]["share_pct"],
   "top_pairs_by_volume":xx["top_pairs"],
   "pool_tvl_usd":xx["pool_tvl"],"previous_pool_tvl_usd":xx["prev_pool_tvl"],
   "turnover_ratio_pct":xx["turnover"],"previous_turnover_ratio_pct":xx["prev_turnover"],
   "dex_vol_wow_pct":100*(xx["vol"]-xx["prev_vol"])/xx["prev_vol"],
   "dex_volume_egld_24h":bid["dexvol_egld"],
   "previous_dex_volume_egld_24h":bid["prev_dexvol_egld"],
   "dex_vol_egld_wow_pct":100*(bid["dexvol_egld"]-bid["prev_dexvol_egld"])/bid["prev_dexvol_egld"],
   "pool_tvl_egld":bid["pooltvl_egld"],"previous_pool_tvl_egld":bid["prev_pooltvl_egld"],
   "wegld_usdc_share_of_volume_pct":bid["wegld_usdc_share"],
   "ex_wegld_usdc_volume_usd":bid["ex_wegld_usdc_vol"],
   "mex_pair_depth":mexd},
 "analysis":(
  f"THE MEX STREAK BROKE, AND THE MECHANISM HUNT IS CLOSED WITHOUT AN ANSWER. MEX {xx['mex_wow']:+.2f}% against EGLD {pc:+.2f}% - the first week in six that MEX has UNDERPERFORMED, by 0.42pp. "
  f"Run #22's pre-committed mechanism test asked for MEX/WEGLD pool TVL growing more than 10% WoW in EGLD terms or supply falling more than 1%. Neither: pool TVL in EGLD terms moved {mexd['tvl_egld_wow_pct']:+.2f}% (${f(mexd['tvl_usd'])}, {f(mexd['tvl_egld'])} EGLD, rank {mexd['depth_rank']} by depth, {mexd['trades_24h']} trades) and supply moved {100*(tk['mex_supply']-tk['mex_prev_supply'])/tk['mex_prev_supply']:+.3f}%. "
  f"That is the 'neither, second run running' branch, so per the run #21 rule about repeated explanations the model stops generating them: the five-week ~9.8pp gap is UNEXPLAINED FLOW and is labelled as such. The streak ending in the same week is a reasonable coda - whatever it was, it is not obviously still running.\n\n"
  f"THE DEX SPLIT INTO ITS TWO COMPONENTS AND THEY DISAGREE - which is exactly what run #22 asked for. In dollars, volume ${f(xx['vol'])} ({100*(xx['vol']-xx['prev_vol'])/xx['prev_vol']:+.1f}%) on pool TVL ${f(xx['pool_tvl'])} ({100*(xx['pool_tvl']-xx['prev_pool_tvl'])/xx['prev_pool_tvl']:+.1f}%), turnover {xx['turnover']:.2f}% against {xx['prev_turnover']:.2f}% - the regime holds. "
  f"In EGLD, volume fell from {f(bid['prev_dexvol_egld'])} to {f(bid['dexvol_egld'])} EGLD/day ({100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}%) and pool depth from {f(bid['prev_pooltvl_egld'])} to {f(bid['pooltvl_egld'])} EGLD ({100*(bid['pooltvl_egld']-bid['prev_pooltvl_egld'])/bid['prev_pooltvl_egld']:+.1f}%). "
  f"Both sides of the ratio scaled with the price, which is why the ratio held. The venue did not process more EGLD this week than last; it processed slightly less. Concentration is unchanged and extreme: WEGLD/USDC is {bid['wegld_usdc_share']:.1f}% of all volume on {xx['top_pairs'][0]['trades_count_24h']:,} trades, and the entire rest of xExchange traded ${f(bid['ex_wegld_usdc_vol'])} - about {f(bid['ex_wegld_usdc_vol_egld'])} EGLD - in 24 hours.\n\n"
  f"STABLECOINS DRAINED, BOTH OF THEM. USDT {f(tk['stable']['USDT-f8c08c']['supply'])} ({tk['stable']['USDT-f8c08c']['pct']:+.2f}%) and USDC {f(tk['stable']['USDC-c76f1f']['supply'])} ({tk['stable']['USDC-c76f1f']['pct']:+.2f}%). "
  f"USDC falling {f(abs(tk['stable']['USDC-c76f1f']['supply']-tk['stable']['USDC-c76f1f']['prev']))} tokens is well past the 0.1% stablecoin threshold and is the larger of the two in absolute terms; the on-chain dollar base fell roughly $75K in a week when the price rose 6.4%. Dollars left the chain into strength - the same direction as every other holding-side instrument this week.\n\n"
  f"HOLDER COUNTS FELL ON EVERY TOP-10 TOKEN AGAIN - WEGLD -106, HYPE -94, QWT -93, ZPAY -85 - the continuing dust-account attrition, unremarkable on its own but now unbroken for most of the tracked period. "
  f"NEWLY ISSUED: {len(tk['newly'])} issuances cleared the ESDT system-SC scan and all {len(tk['newly'])} have exactly 1 holder ({', '.join(t['identifier'] for t in tk['newly'])}). That is a seventh consecutive week with no launch clearing the >10-holder / >5-tx bar."),
}

# ---------------- defi -----------------------------------------------------
def hs(pct):
    if pct>5: return "growing"
    if pct<-15: return "draining"
    if pct<-2: return "shrinking"
    return "flat"
proto=df["proto"]
xe_pct=100*(df["xexch_usd"]-df["xexch_prev_usd"])/df["xexch_prev_usd"]
lsd_pct=tk["lsd"]["SEGLD-3ad2d0"]["pct"]
R["defi_activity"]={
 "protocols":[
  {"name":"xExchange","category":"dex","volume_24h_usd":xx["vol"],
   "active_pairs":xx["pairs"],"transfers_24h":None,"tvl_usd":df["xexch_usd"],
   "tvl_egld":df["xexch_egld"],"tvl_wow_change_pct":xe_pct},
  {"name":"Hatom Lending","category":"lending","volume_24h_usd":0.0,"active_pairs":0,
   "transfers_24h":proto.get("Hatom EGLD MM"),"tvl_usd":df["hatom_lending_usd"],
   "tvl_egld":df["hatom_lending_egld"],"tvl_wow_change_pct":df["hatom_lending_egld_pct"]},
  {"name":"Hatom Liquid Staking","category":"liquid_staking","volume_24h_usd":0.0,"active_pairs":0,
   "transfers_24h":proto.get("Hatom Liquid Staking"),"tvl_usd":df["hatom_lsd_usd"],
   "tvl_egld":df["hatom_lsd_usd"]/price,"tvl_wow_change_pct":lsd_pct},
  {"name":"XOXNO LSD","category":"liquid_staking","volume_24h_usd":0.0,"active_pairs":0,
   "transfers_24h":proto.get("XOXNO LSD"),"tvl_usd":df["xoxno_usd"],
   "tvl_egld":df["xoxno_usd"]/price,"tvl_wow_change_pct":tk["lsd"]["XEGLD-e413ed"]["pct"]}],
 "protocol_breakdown":[
  {"protocol":"xExchange","category":"dex","addresses_tracked":16,
   "tvl_usd":df["xexch_usd"],"tvl_egld":df["xexch_egld"],"tvl_wow_change_pct":xe_pct,
   "transfers_24h":None,"volume_24h_usd":xx["vol"],
   "notable_events":f"THE TURNOVER REGIME HELD IN USD AND FAILED IN EGLD. Turnover {xx['prev_turnover']:.2f}% -> {xx['turnover']:.2f}%, above the ~5% branch, but volume in EGLD terms fell {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}% to {f(bid['dexvol_egld'])} EGLD/day and pool depth {100*(bid['pooltvl_egld']-bid['prev_pooltvl_egld'])/bid['prev_pooltvl_egld']:+.1f}% to {f(bid['pooltvl_egld'])} EGLD. Both sides scaled with price. WEGLD contract balance {f(df['xexch_egld'])} EGLD (roughly flat); WEGLD supply {f(tk['wegld_supply'])}. Concentration {bid['wegld_usdc_share']:.1f}% WEGLD/USDC.",
   "health_signal":"flat"},
  {"protocol":"Hatom Lending","category":"lending","addresses_tracked":13,
   "tvl_usd":df["hatom_lending_usd"],"tvl_egld":df["hatom_lending_egld"],
   "tvl_wow_change_pct":df["hatom_lending_egld_pct"],
   "transfers_24h":proto.get("Hatom EGLD MM"),
   "notable_events":f"BILATERAL INVERSE RULE: FOURTH UP-WEEK CONFIRMATION, AND THE CAPACITY-EXHAUSTION WATCH IS CLEARED. Price {pc:+.2f}% (evaluable, past the |5%| guardrail), EGLD-denominated TVL {df['hatom_lending_egld_pct']:+.2f}% - correct inverse sign at a response ratio of {df['inverse_ratio']:.2f}. Run #22 asked whether a SECOND consecutive sub-0.30 reading would appear, which would have meant the deposit base was exhausted and the rule should be retired. It did not: 0.49 / 0.72 / 0.28 / {df['inverse_ratio']:.2f}. The 0.28 was a single weak reading against a +30% move, not depletion. USD TVL ${f(df['hatom_lending_usd'])} (+{100*(df['hatom_lending_usd']-df['hatom_lending_prev_usd'])/df['hatom_lending_prev_usd']:.1f}%) is price.",
   "health_signal":"shrinking"},
  {"protocol":"Hatom Liquid Staking","category":"liquid_staking","addresses_tracked":2,
   "tvl_usd":df["hatom_lsd_usd"],"tvl_egld":df["hatom_lsd_usd"]/price,
   "tvl_wow_change_pct":lsd_pct,"transfers_24h":proto.get("Hatom Liquid Staking"),
   "notable_events":f"SUPPLY BASIS (run #13 rule): SEGLD {lsd_pct:+.3f}% to {f(tk['lsd']['SEGLD-3ad2d0']['supply'])}, a sixth consecutive week inside the noise band. SWTAO {tk['lsd']['SWTAO-356a25']['pct']:+.2f}% to {f(tk['lsd']['SWTAO-356a25']['supply'])} - the largest SWTAO supply move since run #14 and a genuine redemption, though on a 3,198-token base it is ~54 tokens. All four dataApi tokens priced on the FIRST pass this run with zero retries, the first clean pass since the guard was added in run #13.",
   "health_signal":"flat"},
  {"protocol":"Hatom USH","category":"stablecoin","addresses_tracked":4,
   "tvl_usd":df["ush_usd"],"tvl_egld":df["ush_usd"]/price,
   "tvl_wow_change_pct":tk["lsd"]["USH-111e09"]["pct"],"transfers_24h":None,
   "notable_events":f"USH BURNED {tk['lsd']['USH-111e09']['pct']:+.2f}% ({f(abs(tk['lsd']['USH-111e09']['supply']-tk['lsd']['USH-111e09']['prev']))} tokens) to {f(tk['lsd']['USH-111e09']['supply'])} - a SECOND consecutive burn into a rising price. Run #22 noted that a burn during a rally fits neither the run #11 (burn = de-leveraging in a decline) nor run #16 (mint = leverage returning in a rally) framing; two in a row makes it a pattern rather than an oddity. CDP borrowers are repaying debt as their collateral appreciates. Cumulative -2.4% over two weeks.",
   "health_signal":"shrinking"},
  {"protocol":"XOXNO LSD","category":"liquid_staking","addresses_tracked":3,
   "tvl_usd":df["xoxno_usd"],"tvl_egld":df["xoxno_usd"]/price,
   "tvl_wow_change_pct":tk["lsd"]["XEGLD-e413ed"]["pct"],"transfers_24h":proto.get("XOXNO LSD"),
   "notable_events":f"XEGLD supply {tk['lsd']['XEGLD-e413ed']['pct']:+.3f}% to {f(tk['lsd']['XEGLD-e413ed']['supply'])} - a fourth week inside the noise band. The run #14 -29.2% redemption episode is closed. {proto.get('XOXNO LSD')} transfers in 24h.",
   "health_signal":"flat"},
  {"protocol":"XOXNO Aggregator","category":"aggregator","addresses_tracked":1,
   "tvl_usd":0.0,"tvl_egld":0.0,"tvl_wow_change_pct":None,
   "transfers_24h":proto.get("XOXNO Aggregator"),"volume_24h_usd":0.0,
   "notable_events":f"{f(proto.get('XOXNO Aggregator') or 0)} transfers in 24h - a new high for this contract and the clearest single activity reading on the network. Non-custodial routing, so TVL is not the metric.",
   "health_signal":"spiking"},
  {"protocol":"OneDex","category":"aggregator","addresses_tracked":5,
   "tvl_usd":0.0,"tvl_egld":0.0,"tvl_wow_change_pct":None,
   "transfers_24h":proto.get("OneDex Swap"),"volume_24h_usd":0.0,
   "notable_events":f"{f(proto.get('OneDex Swap') or 0)} transfers in 24h, also at the top of its range. One tracked address (OneDex Launchpad) still fails bech32 validation and stays excluded rather than guessed - a gap open since run #18.",
   "health_signal":"growing"},
  {"protocol":"JEXchange","category":"dex","addresses_tracked":4,
   "tvl_usd":0.0,"tvl_egld":0.0,"tvl_wow_change_pct":None,
   "transfers_24h":proto.get("JEXchange Fees"),"volume_24h_usd":0.0,
   "notable_events":f"Fees contract {f(proto.get('JEXchange Fees') or 0)} transfers in 24h; the aggregator contract returned 0 for a third consecutive run, which is now more likely a wrong address than a halt and should be re-derived.",
   "health_signal":"flat"}],
 "sc_deployments":[],
 "analysis":(
  f"DeFi did the same thing it did last week, one notch quieter, and the consistency is the finding.\n\n"
  f"Activity was strong where it is measured in transfers: the XOXNO aggregator processed {f(proto.get('XOXNO Aggregator') or 0)} in 24 hours and OneDex {f(proto.get('OneDex Swap') or 0)}, both at the top of their ranges. But xExchange's own throughput in EGLD terms FELL {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}%, so the venue-level demand read depends entirely on which denominator you pick - and the honest one for a chain-native question is EGLD.\n\n"
  f"The credit stack de-risked for a second consecutive week. Hatom Lending's EGLD-denominated deposits fell {df['hatom_lending_egld_pct']:+.2f}% against a {pc:+.2f}% price, the fourth up-week confirmation of the bilateral inverse rule and - importantly - at a response ratio of {df['inverse_ratio']:.2f}, well clear of the 0.30 exhaustion threshold. "
  f"Run #22 registered that two consecutive sub-0.30 readings would retire the rule; the second did not come, so the rule survives and last week's 0.28 is reclassified as one weak response to an unusually large price move rather than evidence of a depleted deposit base.\n\n"
  f"USH burned {tk['lsd']['USH-111e09']['pct']:+.2f}% for a second week running, {f(abs(tk['lsd']['USH-111e09']['supply']-tk['lsd']['USH-111e09']['prev']))} tokens, cumulative -2.4% across the two. A single burn into a rally was an anomaly; two is a behaviour, and the reading is that CDP borrowers are using appreciation to retire debt rather than to lever further. "
  f"That is the mirror image of run #16, where a +16% week produced a +6.49% USH MINT. The same instrument, the same direction of price, opposite response - which says the cohort changed, not the mechanism.\n\n"
  f"Liquid staking again did nothing: SEGLD {lsd_pct:+.3f}%, XEGLD {tk['lsd']['XEGLD-e413ed']['pct']:+.3f}%, SWTAO {tk['lsd']['SWTAO-356a25']['pct']:+.2f}%. Six consecutive weeks with no LSD subscription of any size, through a cumulative +39% price move. "
  f"Combined with a flat delegator base and a staked ratio that FELL, the picture is consistent: nobody converted this rally into a yield-bearing on-chain position.\n\n"
  f"TVL METHOD NOTE: LSD and stablecoin figures are on the supply basis per the run #13 rule, USD as context only. All four dataApi-priced tokens returned a live price on the first pass with zero retries - the first fully clean pass since the guard was added, so no fallback was needed at any level of the run #22 ordering."),
}
json.dump(R,open("/tmp/run23w/part2.json","w"),indent=1,default=str)
print("part2 ok:",list(R.keys()))
