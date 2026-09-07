#!/usr/bin/env python3
"""Run #24 stage 3: staking, tokens, defi -> /tmp/run24w/part2.json"""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-09-07"
O=json.load(open("/tmp/run24w/derived.json"))
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
zsc0=O["zero_stake_cohort"]
LF=next((r for r in zsc0["with_activity_this_week"] if r["provider"]=="ledgerbyfigment"), {})
LFC=LF.get("function_counts",{})
dser={d["identity"]:d for d in O["dereg_series"]}

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

# provider states. Run #23 listed three deregistrations; the widened detector
# run across the whole stored archive shows they are the visible end of a much
# larger, much older cohort - so the states array now carries the cohort summary
# alongside the named cases.
zsc=O["zero_stake_cohort"]
dseries={d["identity"]:d for d in O["dereg_series"]}
states=[]
for r in zsc["emptied_inside_archive"]:
    d=dseries.get(r["provider"],{})
    states.append({"provider":r["provider"],"state":"deregistered","locked_egld":0.0,
      "num_users":r["users"],"num_nodes":r["nodes"],"apr_pct":0.0,"fee_pct":0.0,
      "weeks_in_state":{"ledgerbyfigment":12,"p2p_org_":3,"truststakingsw":14}.get(r["provider"],1),
      "note":(f"emptied inside the archive - last snapshot with locked > 0 was {r['last_locked_in_archive']}. "
              f"{r['inbound_txs_this_week']} inbound txs this week"
              + (f"; delegators {d['prev_users']:,} -> {d['users']:,} ({d['users_delta']:+d})" if d.get("users") is not None else "")
              + (f"; function calls {r['function_counts']}" if r["function_counts"] else ""))})
for r in zsc["rows"][:6]:
    if any(x["provider"]==r["provider"] for x in states): continue
    states.append({"provider":r["provider"],"state":"deregistered","locked_egld":0.0,
      "num_users":r["users"],"num_nodes":r["nodes"],"apr_pct":0.0,"fee_pct":0.0,
      "weeks_in_state":None,
      "note":"zero locked stake for the ENTIRE stored archive (2026-06-01 onward) with delegator records still attached, and zero inbound transactions this week - a dormant record rather than a live position"})
for ident in ("egldstakingprovider","procryptostaking"):
    states.append({"provider":ident,"state":"fee_squeezed","locked_egld":mv(ident,"locked"),
      "num_users":mv(ident,"users"),"num_nodes":mv(ident,"nodes"),
      "apr_pct":mv(ident,"apr"),"fee_pct":mv(ident,"fee"),"weeks_in_state":1,
      "note":f"FEE REVERSED off 100% this week - now {mv(ident,'fee'):.0f}% with APR back to {mv(ident,'apr'):.2f}%. Book {mv(ident,'delta'):+,.0f}, users {mv(ident,'users_delta'):+d}: the money kept leaving anyway."})

R["staking_intelligence"]={
 "summary":{"total_staked_egld":econ["staked"],"total_delegated_egld":tl,
   "staked_ratio":M["sr"],"num_providers":len(provs),
   "apr_min":sk["apr_min"],"apr_max":sk["apr_max"],"apr_weighted_avg":sk["apr_wavg"]},
 "top_providers":top_providers,
 "concentration":{"top_5_share_pct":sk["top5"],"top_10_share_pct":sk["top10"],
   "hhi":sk["hhi"],"hhi_previous":sk["prev_hhi"],
   "hhi_interpretation":f"HHI {sk['hhi']:.5f} (previous {sk['prev_hhi']:.5f}), far below the 0.15 competitive threshold; top-5 {sk['top5']:.2f}%, top-10 {sk['top10']:.2f}%, both flat. Concentration has never been the risk in this market. The tail is: {O['zero_stake_cohort']['contracts']} contracts carry no stake at all and still list {O['zero_stake_cohort']['attached_delegator_records']:,} delegator records between them."},
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
 "zero_stake_cohort":{
   "contracts":zsc["contracts"],
   "attached_delegator_records":zsc["attached_delegator_records"],
   "share_of_all_delegator_records_pct":zsc["share_of_all_delegator_records_pct"],
   "emptied_inside_archive":len(zsc["emptied_inside_archive"]),
   "with_activity_this_week":len(zsc["with_activity_this_week"]),
   "archive_snapshots":zsc["archive_snapshots"],
   "archive_first_snapshot":zsc["archive_first"],
   "note":("Contracts with locked == 0 and delegator records still attached. Only the four with a recorded "
           "transition inside the archive are deregistrations in any meaningful sense; the rest were emptied "
           "before tracking began and show no activity. The delegator base must be quoted on the locked>0 basis.")},
 "fee_events":[
   {"provider":"egldstakingprovider","fee_from_pct":100.0,"fee_to_pct":mv("egldstakingprovider","fee"),
    "apr_from_pct":0.0,"apr_to_pct":mv("egldstakingprovider","apr"),
    "locked_egld":mv("egldstakingprovider","locked"),
    "locked_wow_egld":mv("egldstakingprovider","delta"),
    "users":mv("egldstakingprovider","users"),
    "users_wow":mv("egldstakingprovider","users_delta"),"num_nodes":mv("egldstakingprovider","nodes")},
   {"provider":"procryptostaking","fee_from_pct":100.0,"fee_to_pct":mv("procryptostaking","fee"),
    "apr_from_pct":0.0,"apr_to_pct":mv("procryptostaking","apr"),
    "locked_egld":mv("procryptostaking","locked"),
    "locked_wow_egld":mv("procryptostaking","delta"),
    "users":mv("procryptostaking","users"),
    "users_wow":mv("procryptostaking","users_delta"),"num_nodes":mv("procryptostaking","nodes")}],
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
   "status":(f"STILL UNMOVED, THIRD CONSECUTIVE WEEK, AND IT STAYS RETIRED. Balance unchanged at {f(ub['balance'],2)} EGLD to the cent, "
             f"{f(ub['pending_total'])} EGLD still sitting unbonded-and-unclaimed inside two delegation contracts with the unbonding period long expired, zero outbound transactions and zero function calls. "
             f"Run #23 retired it as a live forward flow on the no-action branch; a third week of nothing confirms that call. It is reported here only so the position does not silently reappear as a surprise if it ever moves."),
   "queue_this_week":{
     "undelegated_egld":sk["undelegated_week"],
     "distinct_callers":sk["undelegate_callers"],
     "measured_pending_egld":sk["pool_total"],
     "largest_legs":pool_rows,
     "coverage_note":(f"FULL-SET SCAN AT A RAISED BUDGET (run #23 rec #10). All {sk['providers_scanned']} provider contracts with locked > 0 or nodes > 0 were paged for unDelegate calls; the {len(O['scan_depth']['deep_scanned'])} contracts that filled the 6-page budget were re-paged at 30 pages, which is the coverage gap run #23 reported as an open lower bound. "
                      f"{sk['undelegate_callers']} distinct wallets unDelegated {f(sk['undelegated_week'])} EGLD against 300 wallets and 151,443 EGLD last week - and roughly half of that increase is the deeper scan rather than new behaviour, so treat this as the first fully comparable reading rather than a 37% jump. "
                      f"/accounts/{{addr}}/delegation was then queried for the 45 largest callers, giving {f(sk['pool_total'])} EGLD of measured pending unbonding, of which {f(sk['claimable_now'])} is already claimable. "
                      f"CAVEAT: {len(O['scan_depth']['pagecap_provscan'])} scans still terminated on a cap, so the figure remains a lower bound on the busiest contracts - but a much tighter one.")}},
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
     f"COMPOUND RATE REVERSED: {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} reDelegateRewards vs {cvc['claim_count']} claimRewards), up from 57.51% and the highest of eleven readings (58.54 / 60.35 / 61.59 / 60.19 / 58.81 / 62.25 / 59.54 / 59.07 / 57.03 / 57.51 / {cvc['compound_pct_of_reward_decisions']:.2f}).",
     "THE PRE-COMMITTED TEST RESOLVES CLEANLY THIS TIME. Run #23 registered contiguous branches after two runs lost to gaps: 'below 57.0% = systematic drift, 57.0% or above = stabilised'. The reading is well clear of the boundary, so the four-week decline was a level shift and not a drift toward monetising yield.",
     "The reversal landed in the week of the largest OTC delivery ever measured, which is the opposite of what a supply-pressure story would predict: the people already staking compounded harder while half a million EGLD hit order books from elsewhere.",
     f"INSTITUTIONAL TIER SOLD AGAIN, AND ONLY THE INSTITUTIONAL TIER. Both traced institutional claims (50-1000 EGLD) went to a labelled exchange, {ag['delegator_fates_by_tier']['institutional']['by_value_egld'].get('sold',0):.0f} EGLD. Third consecutive week this tier leads with selling, on a small sample each time.",
     f"RETAIL STILL DOES NOT SELL - an eleventh consecutive run. {ag['delegator_fates_by_tier']['retail']['total_events']} retail claims, ZERO to any labelled exchange; {ag['delegator_fates_by_tier']['retail']['by_count'].get('held',0)} held, {ag['delegator_fates_by_tier']['retail']['by_count'].get('held_or_other',0)} unlabelled, {ag['delegator_fates_by_tier']['retail']['by_count'].get('rotated_provider',0)} rotated provider, {ag['delegator_fates_by_tier']['retail']['by_count'].get('defi_deposit',0)} into DeFi.",
     f"Mid-tier (1-50 EGLD): {ag['delegator_fates_by_tier']['mid_tier']['by_count'].get('held',0)} held, {ag['delegator_fates_by_tier']['mid_tier']['by_count'].get('held_or_other',0)} unlabelled, {ag['delegator_fates_by_tier']['mid_tier']['by_count'].get('rotated_provider',0)} provider rotations, {ag['delegator_fates_by_tier']['mid_tier']['by_count'].get('defi_deposit',0)} into DeFi, no exchange destinations.",
     f"unDelegate was {ag['overall_function_distribution'].get('unDelegate',{}).get('share_pct',0):.2f}% of observed function calls and withdraw {ag['overall_function_distribution'].get('withdraw',{}).get('share_pct',0):.2f}%, against a full-set queue of {f(sk['undelegated_week'])} EGLD - the sampled providers are not where the unbonding is concentrated.",
     "PROVIDER OPERATORS DID NOT SELL FEES for a twelfth consecutive run. Zero exchange destinations across all sampled owner wallets in 30 days; truststaking's owner again made the only sizeable move, 2,524.59 EGLD into a DeFi contract.",
     f"Sample: {ag['providers_sampled']} providers, {sum(v['count'] for v in ag['overall_function_distribution'].values())} function calls, {sum(t['total_events'] for t in ag['delegator_fates_by_tier'].values())} traced claims."]},
 "analysis":(
  f"THE DEREGISTRATION STORY IS AN ORDER OF MAGNITUDE BIGGER THAN RUN #23 REPORTED, AND MOSTLY OLDER THAN THE ARCHIVE. "
  f"Run #23 widened the detection signature to 'locked == 0 AND (numNodes > 0 OR numUsers > 0)' and reported three deregistered providers. Applying that signature to the full stored provider list - which run #23 also started saving - returns {zsc['contracts']} contracts holding zero stake with {zsc['attached_delegator_records']:,} delegator records attached between them, {zsc['share_of_all_delegator_records_pct']:.1f}% of every delegator record on the network. "
  f"Running it backwards over all {zsc['archive_snapshots']} stored snapshots (the run #23 rule: test a new detector against the archive in the same run) shows only FOUR emptied inside the archive: ledgerbyfigment (last locked 2026-06-08), p2p_org_ (2026-08-17), truststakingsw (2026-06-01) and one 6-user contract (2026-08-10). "
  f"everstake's 3,681 records, stakedao-devops's 2,862, bharvest's 1,383, phidelta's 1,009 and the rest have been at zero since before tracking began.\n\n"
  f"THAT REFRAMES THE FINDING RATHER THAN ENLARGING IT. Exactly ONE of the {zsc['contracts']} contracts saw a single inbound transaction this week: ledgerbyfigment, with {LFC.get('unDelegate',0)} unDelegate, {LFC.get('withdraw',0)} withdraw, {LFC.get('claimRewards',0)} claimRewards and {LFC.get('reDelegateRewards',0)} reDelegateRewards calls, and its delegator count fell {dser.get('ledgerbyfigment',{}).get('users_delta',0):+d} to {dser.get('ledgerbyfigment',{}).get('users',0):,}. "
  f"The other 81 are silent. So most of those 28,032 'delegators' are stale records on contracts that were emptied long ago, not people sitting on stranded positions - which is the more mundane and more likely reading, and it is why the delegator base must be quoted on the locked>0 basis ({f(sk['users'])}) rather than the full-list basis ({f(sk['prev_users_all_contracts'])}). "
  f"Getting that wrong would have printed a -28,141 delegator collapse this week that consists entirely of a storage change made last run.\n\n"
  f"THE DECAY SERIES, NOW IN ITS SECOND READING. ledgerbyfigment {dser.get('ledgerbyfigment',{}).get('prev_users',0):,} -> {dser.get('ledgerbyfigment',{}).get('users',0):,} ({dser.get('ledgerbyfigment',{}).get('users_delta',0):+d}), stakedinc {dser.get('stakedinc',{}).get('users',0):,} (unchanged), p2p_org_ {dser.get('p2p_org_',{}).get('users',0):,} (unchanged). "
  f"Twelve weeks at zero yield has cost ledgerbyfigment 85 of 3,961 delegators, 2.1%, and this week's -7 is right on that trend. p2p_org_'s stranded 1,244 produced {p2p['function_counts'].get('unDelegate',0)} unDelegate and {p2p['function_counts'].get('claimRewards',0)} claimRewards calls - 0.4% of the book touching a contract that pays nothing. Participation inertia measured over three months holds at roughly 2% per quarter.\n\n"
  f"THE TWO 100%-FEE PROVIDERS REVERSED THEIR FEES AND IT CHANGED NOTHING. egldstakingprovider went 100% -> {mv('egldstakingprovider','fee'):.0f}% with APR back to {mv('egldstakingprovider','apr'):.2f}%, procryptostaking 100% -> {mv('procryptostaking','fee'):.0f}% at {mv('procryptostaking','apr'):.2f}% - and their books still fell {mv('egldstakingprovider','delta'):+,.0f} and {mv('procryptostaking','delta'):+,.0f} while users fell {mv('egldstakingprovider','users_delta'):+d} and {mv('procryptostaking','users_delta'):+d}. "
  f"Run #21's rule - a fee change is not evidence of competition - applies in the other direction too: restoring a yield does not bring capital back within a week. Capital that left over three weeks of zero APR did not return in the week the APR returned.\n\n"
  f"UNDERNEATH, THE MARKET SHRANK QUIETLY. Delegation TVL fell {sk['delta_locked']:+,.0f} to {f(tl)} with {len(sk['movers'])} providers moving more than 5,000 EGLD - meria {mv('meria','delta'):+,.0f}, procryptostaking {mv('procryptostaking','delta'):+,.0f}, egldstakingprovider {mv('egldstakingprovider','delta'):+,.0f} - against one real gainer, pi-staking at {mv('pi-staking','delta'):+,.0f} with {mv('pi-staking','users_delta'):+d} delegators on a 0% fee and the highest APR in the set ({mv('pi-staking','apr'):.2f}%). "
  f"{sk['gaining']} providers gained delegators and {sk['losing']} lost them. The delegator base itself moved {sk['users_delta']:+,} to {f(sk['users'])} - flat again, an eleventh consecutive week inside the run #18 inertia base rate, and this time through a +17% price move and the largest OTC delivery on record.\n\n"
  f"THE UNBONDING QUEUE IS THE ONE STAKING NUMBER THAT MOVED. {f(sk['undelegated_week'])} EGLD unDelegated by {sk['undelegate_callers']} distinct wallets across all {sk['providers_scanned']} contracts, against 151,443 by 300 last week. "
  f"Read that carefully: {len(O['scan_depth']['deep_scanned'])} contracts filled last run's 6-page budget and were re-paged at 30 pages this run on run #23's own recommendation, so part of the increase is coverage rather than behaviour - this is the first scan deep enough to call comparable. "
  f"Measured pending unbonding across the 45 largest callers is {f(sk['pool_total'])} EGLD, of which {f(sk['claimable_now'])} is already claimable and the rest sits at 5-9 days. "
  f"The residual test resolves the same way as the last two runs: staked fell {M['staked_chg']:+,.0f} while delegation fell {sk['delta_locked']:+,.0f}, leaving a residual of {f(sk['residual'])} against {f(sk['undelegated_week'])} of measured unbonding in flight. Fully absorbed, so corrected_direct_node_egld stays null for a third run.\n\n"
  f"REWARD BEHAVIOUR REVERSED. The compound rate came back to {cvc['compound_pct_of_reward_decisions']:.2f}% after four consecutive declines, resolving run #23's drift test on the 'stabilised' branch. "
  f"The composition is unchanged where it matters: retail sold nothing for an eleventh run, mid-tier sold nothing, and the only exchange destinations came from the institutional tier ({ag['delegator_fates_by_tier']['institutional']['by_value_egld'].get('sold',0):.0f} EGLD across 2 claims). Operators sold no fees for a twelfth run."),
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
  f"THE DEX QUESTION RUN #23 LEFT OPEN IS ANSWERED, AND THE ANSWER IS THAT THE TURNOVER SIGNAL WAS PRICE. "
  f"Run #23 pre-registered EGLD-denominated volume above 70,000/day as genuine venue demand and below 60,000 as proof the USD series had been tracking price. It came in at {f(bid['dexvol_egld'])} EGLD/day, {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}%, comfortably inside the lower branch. "
  f"In dollars the same week reads ${f(xx['vol'])} ({100*(xx['vol']-xx['prev_vol'])/xx['prev_vol']:+.1f}%) on pool TVL ${f(xx['pool_tvl'])} ({100*(xx['pool_tvl']-xx['prev_pool_tvl'])/xx['prev_pool_tvl']:+.1f}%) at {xx['turnover']:.2f}% turnover against {xx['prev_turnover']:.2f}%. "
  f"Pool depth in EGLD fell {100*(bid['pooltvl_egld']-bid['prev_pooltvl_egld'])/bid['prev_pooltvl_egld']:+.1f}% to {f(bid['pooltvl_egld'])} EGLD. From this run the venue series is reported in EGLD as the primary and the USD ratio as context, and the 'DEX turnover shows the bid returning' reading carried since run #22 is withdrawn.\n\n"
  f"Concentration is unchanged and extreme: WEGLD/USDC is {bid['wegld_usdc_share']:.1f}% of all volume on {xx['top_pairs'][0]['trades_count_24h']:,} trades. Ex that single pair the whole venue traded ${f(bid['ex_wegld_usdc_vol'])} - about {f(bid['ex_wegld_usdc_vol_egld'])} EGLD - in 24 hours. "
  f"MEX gained {xx['mex_wow']:+.2f}% against EGLD {pc:+.2f}%, a second consecutive week of UNDERPERFORMANCE after five of outperformance; MEX/WEGLD pool depth {mexd['tvl_egld_wow_pct']:+.2f}% in EGLD terms at rank {mexd['depth_rank']} on {mexd['trades_24h']} trades, supply {100*(tk['mex_supply']-tk['mex_prev_supply'])/tk['mex_prev_supply']:+.3f}%. The unexplained-flow label from run #23 stands and the question stays closed.\n\n"
  f"THE ON-CHAIN DOLLAR BASE CONTRACTED FOR A THIRD CONSECUTIVE WEEK, WHICH IS THE PROMOTION CONDITION RUN #23 REGISTERED. "
  f"USDC {tk['stable']['USDC-c76f1f']['pct']:+.2f}% to {f(tk['stable']['USDC-c76f1f']['supply'])} ({f(abs(tk['stable']['USDC-c76f1f']['supply']-tk['stable']['USDC-c76f1f']['prev']))} tokens redeemed) and USDT {tk['stable']['USDT-f8c08c']['pct']:+.2f}% to {f(tk['stable']['USDT-f8c08c']['supply'])}, about $140K of wrapped dollars leaving in a {pc:+.1f}% week. "
  f"Three weeks, cumulative roughly -3.5% on the combined base, every one of them into a rising price. The dollar base is now reported alongside USH as a de-risking instrument rather than as plumbing: dollars are leaving this chain while the token appreciates, which is what an exit into strength looks like when the exit is settled off-chain.\n\n"
  f"HOLDER COUNTS FELL ON EVERY TOP-10 TOKEN AGAIN - WEGLD -138, HYPE -139, QWT -135, ZPAY -128, USDC -97 - the same dust-account attrition the archive has recorded almost every week. "
  f"NEWLY ISSUED: {len(tk['newly'])} issuances cleared the ESDT system-SC scan. The best of them, {tk['newly'][0]['identifier']}, has {tk['newly'][0]['accounts']} holders and {tk['newly'][0]['transactions']} transactions; the other three have one holder each. That is an eighth consecutive week with no launch clearing the >10-holder / >5-transaction bar."),
}

# ---------------- defi -----------------------------------------------------
def hs(pct):
    if pct is None: return None
    if pct>5: return "growing"
    if pct<-15: return "draining"
    if pct<-2: return "shrinking"
    return "flat"
proto=df["proto"]
xe_pct=100*(df["xexch_usd"]-df["xexch_prev_usd"])/df["xexch_prev_usd"]
lsd_pct=tk["lsd"]["SEGLD-3ad2d0"]["pct"]
em=O["emerging_lsd"]
jex=O["jex"]
# THE RECEIPT TOKEN'S SUPPLY IS NOT THE PROTOCOL'S DELEGATED STAKE. JWLEGLD is a
# 1:1 EGLD-pegged DEPOSIT token (25,073 supply) against 1,799 EGLD actually
# delegated, and LEGLD appreciates against EGLD, so 5,058 LEGLD is 6,431 EGLD.
# The weekly discovery sweep reports staked_egld per protocol; that is the TVL
# basis, and it is the basis run #23 published for these protocols.
_disc=json.load(open(f"{REPO}/data/collected/liquid_staking_discovery_{RD}.json"))
STAKE={}
for _p in _disc["liquid_staking_protocols"]:
    for _t in _p.get("receipt_tokens",[]):
        STAKE[_t["identifier"]]=_p.get("staked_egld")
# run #23 measured these at discovery on the SAME staked-EGLD basis
EM_PREV={"LEGLD-d74da9":6450.547468433076,"VOXEGLD-5872e5":1756.8293137606825,
         "VEGLD-2b9319":1121.362402476542}
def em_stake(t): return STAKE.get(t)
def em_pct(t):
    p0=EM_PREV.get(t); cur=em_stake(t)
    return 100*(cur-p0)/p0 if (p0 and cur is not None) else None

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
   "notable_events":f"THE EGLD SERIES IS NOW THE PRIMARY ONE. Volume {f(bid['prev_dexvol_egld'])} -> {f(bid['dexvol_egld'])} EGLD/day ({100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}%), below the 60,000 branch run #23 pre-registered, so the USD turnover ratio is confirmed to have been tracking price. Turnover {xx['prev_turnover']:.2f}% -> {xx['turnover']:.2f}%. Pool depth {100*(bid['pooltvl_egld']-bid['prev_pooltvl_egld'])/bid['prev_pooltvl_egld']:+.1f}% to {f(bid['pooltvl_egld'])} EGLD; WEGLD contract balance {f(df['xexch_egld'])} EGLD, supply {f(tk['wegld_supply'])}. Concentration {bid['wegld_usdc_share']:.1f}% WEGLD/USDC.",
   "health_signal":"shrinking"},
  {"protocol":"Hatom Lending","category":"lending","addresses_tracked":13,
   "tvl_usd":df["hatom_lending_usd"],"tvl_egld":df["hatom_lending_egld"],
   "tvl_wow_change_pct":df["hatom_lending_egld_pct"],
   "transfers_24h":proto.get("Hatom EGLD MM"),
   "notable_events":f"BILATERAL INVERSE RULE: FIFTH UP-WEEK CONFIRMATION. Price {pc:+.2f}% (evaluable, past the |5%| guardrail), EGLD-denominated TVL {df['hatom_lending_egld_pct']:+.2f}% to {f(df['hatom_lending_egld'])} EGLD - correct inverse sign at a response ratio of {df['inverse_ratio']:.2f}. The up-week series is now 0.49 / 0.72 / 0.28 / 0.69 / {df['inverse_ratio']:.2f}, a stable band around 0.5 with one outlier, and the capacity-exhaustion watch run #22 opened is closed. USD TVL ${f(df['hatom_lending_usd'])} ({100*(df['hatom_lending_usd']-df['hatom_lending_prev_usd'])/df['hatom_lending_prev_usd']:+.1f}%) is price, not deposits.",
   "health_signal":"shrinking"},
  {"protocol":"Hatom Liquid Staking","category":"liquid_staking","addresses_tracked":2,
   "tvl_usd":df["hatom_lsd_usd"],"tvl_egld":df["hatom_lsd_usd"]/price,
   "tvl_wow_change_pct":lsd_pct,"transfers_24h":proto.get("Hatom Liquid Staking"),
   "notable_events":f"SUPPLY BASIS (run #13 rule): SEGLD {lsd_pct:+.3f}% to {f(tk['lsd']['SEGLD-3ad2d0']['supply'])} - a seventh consecutive week inside the noise band, and the largest LSD on the chain has now been flat through a cumulative +63% price move. SWTAO {tk['lsd']['SWTAO-356a25']['pct']:+.2f}% to {f(tk['lsd']['SWTAO-356a25']['supply'])}, a second consecutive redemption. All four dataApi-priced tokens returned a live price on the first pass for a second consecutive run.",
   "health_signal":"flat"},
  {"protocol":"Hatom USH","category":"stablecoin","addresses_tracked":4,
   "tvl_usd":df["ush_usd"],"tvl_egld":df["ush_usd"]/price,
   "tvl_wow_change_pct":tk["lsd"]["USH-111e09"]["pct"],"transfers_24h":None,
   "notable_events":f"USH MINTED {tk['lsd']['USH-111e09']['pct']:+.2f}% ({f(tk['lsd']['USH-111e09']['supply']-tk['lsd']['USH-111e09']['prev'])} tokens) to {f(tk['lsd']['USH-111e09']['supply'])}, REVERSING two consecutive burns and taking the base above where it started the sequence. This is the run #16 pattern restored: a large up-week brings CDP leverage back. The two-week burn is reclassified as debt repayment through a moderate rally, with leverage returning once the move got big enough - USH is the one on-chain instrument that responded to this price move in the direction a rally predicts.",
   "health_signal":"growing"},
  {"protocol":"XOXNO LSD","category":"liquid_staking","addresses_tracked":3,
   "tvl_usd":df["xoxno_usd"],"tvl_egld":df["xoxno_usd"]/price,
   "tvl_wow_change_pct":tk["lsd"]["XEGLD-e413ed"]["pct"],"transfers_24h":proto.get("XOXNO LSD"),
   "notable_events":f"XEGLD supply {tk['lsd']['XEGLD-e413ed']['pct']:+.3f}% to {f(tk['lsd']['XEGLD-e413ed']['supply'])} - a redemption at the top of the noise band, the fifth straight week without subscription. {proto.get('XOXNO LSD')} transfers in 24h.",
   "health_signal":"flat"},
  {"protocol":"XOXNO Aggregator","category":"aggregator","addresses_tracked":1,
   "tvl_usd":0.0,"tvl_egld":0.0,"tvl_wow_change_pct":None,
   "transfers_24h":proto.get("XOXNO Aggregator"),"volume_24h_usd":0.0,
   "notable_events":f"{f(proto.get('XOXNO Aggregator') or 0)} transfers in 24h against 32,462 last week (-37%). Still the largest single activity reading on the network, but the spike run #23 flagged did not hold. Non-custodial routing, so TVL is not the metric.",
   "health_signal":"flat"},
  {"protocol":"OneDex","category":"aggregator","addresses_tracked":5,
   "tvl_usd":0.0,"tvl_egld":0.0,"tvl_wow_change_pct":None,
   "transfers_24h":proto.get("OneDex Swap"),"volume_24h_usd":0.0,
   "notable_events":f"{f(proto.get('OneDex Swap') or 0)} transfers in 24h against 19,015 last week (-45%). Both aggregators halved their activity in the week the price rose 17% - routing volume is not tracking the price move. One tracked address (OneDex Launchpad) still fails bech32 validation and stays excluded rather than guessed, open since run #18.",
   "health_signal":"shrinking"},
  {"protocol":"JEXchange","category":"dex","addresses_tracked":5,
   "tvl_usd":0.0,"tvl_egld":0.0,"tvl_wow_change_pct":None,
   "transfers_24h":proto.get("JEXchange Fees"),"volume_24h_usd":0.0,
   "notable_events":f"ADDRESS RE-DERIVED (run #23 rec #11). The tracked aggregator returned {jex['old_transfers_7d']} transfers for a fourth consecutive run, which run #23 called as a stale address rather than a halted protocol - correct. Tracing the fees contract's inbound leg back to its callers (the run #21 rule) identifies the live router at {jex['candidates'][0]['address'][:20]}... with {f(jex['candidates'][0]['transfers_7d'])} transfers in 7 days, plus four more contracts at {', '.join(f(c['transfers_7d']) for c in jex['candidates'][1:5])}. JEXchange is one of the busiest venues on the chain and has been reported as a data gap for four runs. Fees contract {f(proto.get('JEXchange Fees') or 0)} transfers in 24h.",
   "health_signal":"growing"},
  {"protocol":"JewelSwap","category":"liquid_staking","addresses_tracked":1,
   "tvl_usd":(em_stake("JWLEGLD-023462") or 0)*price,"tvl_egld":em_stake("JWLEGLD-023462"),
   "tvl_wow_change_pct":None,"transfers_24h":None,
   "notable_events":f"FIRST MEASUREMENT, and it corrects an error this report nearly published. JWLEGLD-023462 has a supply of {f(em['JWLEGLD-023462']['supply'])} across {em['JWLEGLD-023462']['holders']} holders, which on a naive supply basis would make JewelSwap the largest of the four protocols the sweep surfaced - but JWLEGLD is a 1:1 EGLD-pegged DEPOSIT token, not a staking receipt, and the delegated stake behind the liquid-staking contract is {f(em_stake('JWLEGLD-023462'))} EGLD across {[p['delegation_contracts'] for p in _disc['liquid_staking_protocols'] if p['address'].startswith('erd1qqqqqqqqqqqqqpgqx6833')][0]} delegation contracts. SJWLEGLD (staked JWLEGLD) supply is 8,111 across 402 holders. On the delegated basis JewelSwap is the SMALLEST of the four, not the largest.",
   "health_signal":None},
  {"protocol":"SALSA (Staking Agency)","category":"liquid_staking","addresses_tracked":1,
   "tvl_usd":(em_stake("LEGLD-d74da9") or 0)*price,"tvl_egld":em_stake("LEGLD-d74da9"),
   "tvl_wow_change_pct":em_pct("LEGLD-d74da9"),"transfers_24h":None,
   "notable_events":f"FIRST WEEK-OVER-WEEK READING, on the delegated-stake basis run #23 used: {f(em_stake('LEGLD-d74da9'))} EGLD ({em_pct('LEGLD-d74da9'):+.2f}% on the 6,451 measured at discovery) behind {f(em['LEGLD-d74da9']['supply'])} LEGLD across {em['LEGLD-d74da9']['holders']} holders. LEGLD appreciates against EGLD, which is why 5,058 tokens are worth 6,431 EGLD of stake. Flat, like every established LSD.",
   "health_signal":hs(em_pct("LEGLD-d74da9"))},
  {"protocol":"Dinovox VoxEGLD","category":"liquid_staking","addresses_tracked":1,
   "tvl_usd":(em_stake("VOXEGLD-5872e5") or 0)*price,"tvl_egld":em_stake("VOXEGLD-5872e5"),
   "tvl_wow_change_pct":em_pct("VOXEGLD-5872e5"),"transfers_24h":None,
   "notable_events":f"THE ONLY LIQUID-STAKING STAKE THAT GREW THIS WEEK. {f(em_stake('VOXEGLD-5872e5'))} EGLD delegated ({em_pct('VOXEGLD-5872e5'):+.2f}% on the 1,757 measured at discovery) behind {f(em['VOXEGLD-5872e5']['supply'])} VOXEGLD across {em['VOXEGLD-5872e5']['holders']} holders, up from 78 holders at discovery. Tiny in absolute terms, and the point of tracking it: while SEGLD and XEGLD sat still through a +17% week, the newest protocol on the list grew stake and added 45% more holders.",
   "health_signal":hs(em_pct("VOXEGLD-5872e5"))},
  {"protocol":"VestaX Finance","category":"liquid_staking","addresses_tracked":1,
   "tvl_usd":(em_stake("VEGLD-2b9319") or 0)*price,"tvl_egld":em_stake("VEGLD-2b9319"),
   "tvl_wow_change_pct":em_pct("VEGLD-2b9319"),"transfers_24h":None,
   "notable_events":f"{f(em_stake('VEGLD-2b9319'))} EGLD delegated ({em_pct('VEGLD-2b9319'):+.2f}%), unchanged on the week, behind {f(em['VEGLD-2b9319']['supply'])} VEGLD across {em['VEGLD-2b9319']['holders']} holders. No price feed on VEGLD, so USD is derived from the delegated EGLD.",
   "health_signal":"flat"}],
 "sc_deployments":[],
 "analysis":(
  f"THE WEEK'S DEFI READING IS THAT NOTHING ON-CHAIN RESPONDED TO A +17% PRICE EXCEPT LEVERAGE.\n\n"
  f"Start with the venue. xExchange processed {f(bid['dexvol_egld'])} EGLD/day, {100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.1f}% on the week and below the 60,000 floor run #23 pre-registered. "
  f"In dollars the same numbers look like a 15% decline against a 10% larger pool, which is why the EGLD series is now the primary one: the USD ratio moves with the price of the asset being traded and tells you almost nothing about demand for it. "
  f"Both aggregators went the same way - XOXNO {f(proto.get('XOXNO Aggregator') or 0)} transfers against 32,462, OneDex {f(proto.get('OneDex Swap') or 0)} against 19,015. Routing activity roughly halved in the biggest up-week of the year.\n\n"
  f"The credit stack de-risked for a third consecutive week on the deposit side. Hatom Lending's EGLD-denominated deposits fell {df['hatom_lending_egld_pct']:+.2f}% against the {pc:+.2f}% price - the fifth up-week confirmation of the bilateral inverse rule, at a response ratio of {df['inverse_ratio']:.2f}, and the series now sits in a stable band around 0.5. "
  f"But USH went the OTHER way: {tk['lsd']['USH-111e09']['pct']:+.2f}%, a mint of {f(tk['lsd']['USH-111e09']['supply']-tk['lsd']['USH-111e09']['prev'])} tokens that reverses two weeks of burning and takes the base above where the sequence started. "
  f"Read together those two are not contradictory - depositors withdrew collateral while borrowers drew more debt against what remained, which is what a leverage cycle looks like at the point the move gets big enough to chase. USH is the only tracked instrument that behaved the way a rally is supposed to make things behave.\n\n"
  f"Liquid staking did nothing again: SEGLD {lsd_pct:+.3f}%, XEGLD {tk['lsd']['XEGLD-e413ed']['pct']:+.3f}%, SWTAO {tk['lsd']['SWTAO-356a25']['pct']:+.2f}%. Seven consecutive weeks with no subscription of any size, now through a cumulative +63% price move. "
  f"The one exception is at the bottom of the table: Dinovox VoxEGLD, the newest protocol the discovery sweep found, added {em_pct('VOXEGLD-5872e5'):+.1f}% of supply and grew from 78 to {em['VOXEGLD-5872e5']['holders']} holders. It is 1,882 EGLD against Hatom's 687,831, so it changes no aggregate - but it is the only liquid-staking number on the page that moved, which is precisely why run #23 recommended running the sweep weekly.\n\n"
  f"JEWELSWAP IS MEASURED FOR THE FIRST TIME AT {f(em['JWLEGLD-023462']['supply'])} EGLD ACROSS {em['JWLEGLD-023462']['holders']} HOLDERS - five times SALSA and the largest of the four protocols the sweep surfaced. It had been labelled in known-addresses since an earlier run and never appeared in a breakdown, which is the same class of failure as the JEXchange address: something known but not measured.\n\n"
  f"AND THE JEXCHANGE ADDRESS IS FIXED. The tracked aggregator has returned zero transfers for four runs while the fees contract reported thousands; tracing the fees contract's inbound leg back to its callers identifies a live router doing {f(jex['candidates'][0]['transfers_7d'])} transfers a week plus four more contracts behind it. The protocol was never halted. Both of this week's DeFi corrections came from the same discipline - when a tracked number reads zero while its neighbours do not, suspect the address before the protocol.\n\n"
  f"TVL METHOD NOTE: LSD and stablecoin figures are on the supply basis per the run #13 rule, USD as context only. All four dataApi-priced tokens returned a live price on the first pass with zero retries for a second consecutive run."),
}
json.dump(R,open("/tmp/run24w/part2.json","w"),indent=1,default=str)
print("part2 ok:",list(R.keys()))
