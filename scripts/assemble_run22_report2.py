#!/usr/bin/env python3
"""Run #22 stage 3: staking, tokens, defi -> /tmp/run22w/part2.json"""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-08-24"
O=json.load(open("/tmp/run22w/derived.json"))
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
beh=json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
F=json.load(open(f"{REPO}/data/collected/followup_{RD}.json"))
lm={}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"): lm[a]=m.get("name","Unknown")
M=O["macro"]; sk=O["staking"]; tk=O["tokens"]; xx=O["xexchange"]; df=O["defi"]; bid=O["bid"]
econ=D["economics"]; price=M["price"]; pc=M["price_chg"]
def f(x,d=0):
    try: return f"{x:,.{d}f}"
    except: return str(x)
provs=sk["provs"]; tl=sk["total_locked"]
pkey={p["provider"]:p for p in prev["staking_providers"]}
def pk(p): return p.get("identity") or p["provider"]
ag=beh["aggregates"]; cvc=ag["compound_vs_claim_at_function_level"]
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

pool_rows=[]
for r in sk["pool"]:
    for pu in r["pending_unbonding"]:
        pool_rows.append({"wallet":r["wallet"],"amount_egld":pu["amount_egld"],
                          "contract":pu["contract"],"days_remaining":pu["days_remaining"],
                          "wallet_balance_egld":r["balance_egld"]})
pool_rows.sort(key=lambda x:-x["amount_egld"])

R["staking_intelligence"]={
 "summary":{"total_staked_egld":econ["staked"],"total_delegated_egld":tl,
   "staked_ratio":M["sr"],"num_providers":len(provs),
   "apr_min":sk["apr_min"],"apr_max":sk["apr_max"],"apr_weighted_avg":sk["apr_wavg"]},
 "top_providers":top_providers,
 "concentration":{"top_5_share_pct":sk["top5"],"top_10_share_pct":sk["top10"],
   "hhi":sk["hhi"],"hhi_previous":sk["prev_hhi"],
   "hhi_interpretation":f"HHI {sk['hhi']:.5f} (previous {sk['prev_hhi']:.5f}) - far below the 0.15 competitive threshold. The delegation market remains the least concentrated part of the network; top-5 {sk['top5']:.2f}%, top-10 {sk['top10']:.2f}%, both up marginally as the p2p_org_ exit removed a mid-sized book from the denominator."},
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
 "fee_events":[
   {"provider":"egldstakingprovider","fee_from_pct":100.0,"fee_to_pct":100,
    "apr_from_pct":0.0,"apr_to_pct":0,
    "locked_egld":next(m["locked"] for m in sk["moves"] if m["identity"]=="egldstakingprovider"),
    "locked_wow_egld":next(m["delta"] for m in sk["moves"] if m["identity"]=="egldstakingprovider"),
    "users":next(m["users"] for m in sk["moves"] if m["identity"]=="egldstakingprovider"),
    "users_wow":next(m["users_delta"] for m in sk["moves"] if m["identity"]=="egldstakingprovider"),
    "num_nodes":50},
   {"provider":"procryptostaking","fee_from_pct":100.0,"fee_to_pct":100,
    "apr_from_pct":0.0,"apr_to_pct":0,
    "locked_egld":next(m["locked"] for m in sk["moves"] if m["identity"]=="procryptostaking"),
    "locked_wow_egld":next(m["delta"] for m in sk["moves"] if m["identity"]=="procryptostaking"),
    "users":next(m["users"] for m in sk["moves"] if m["identity"]=="procryptostaking"),
    "users_wow":next(m["users_delta"] for m in sk["moves"] if m["identity"]=="procryptostaking"),
    "num_nodes":50},
   {"provider":"westake","fee_from_pct":4.0,"fee_to_pct":5,
    "apr_from_pct":8.42,"apr_to_pct":8,
    "locked_egld":next((m["locked"] for m in sk["moves"] if m["identity"]=="westake"),0),
    "locked_wow_egld":next((m["delta"] for m in sk["moves"] if m["identity"]=="westake"),0),
    "users":next((m["users"] for m in sk["moves"] if m["identity"]=="westake"),0),
    "users_wow":next((m["users_delta"] for m in sk["moves"] if m["identity"]=="westake"),0),
    "num_nodes":next((m["nodes"] for m in sk["moves"] if m["identity"]=="westake"),0)}],
 "unbonding_in_flight":{
   "wallet":"erd1daqlaezxx22rzyxnqx5ddkykm5ajelt0hetjnstm7rxqg78xqusqazv9ms",
   "total_egld":229864.6,
   "legs":[{"provider":"p2p_org_ (erd1qqqq...m8llllsyhrgzd)","amount":149585.4,
            "days_to_unbond":0.06,"date":"2026-08-15"},
           {"provider":"erd1qqqq...pvhlllls6yl73z (zero-locked)","amount":80279.2,
            "days_to_unbond":0.0,"date":"2026-08-14"}],
   "share_of_delegation_decline_pct":0.0,
   "raw_residual_egld":sk["residual"],
   "corrected_direct_node_egld":None,
   "status":"UNBONDED AND UNWITHDRAWN - the EGLD is still inside the delegation contracts. 80,279 has seconds_remaining = 0 (fully claimable); 149,585 had 5,279 seconds left at snapshot. Neither leg has been withdrawn and the wallet sent no outbound transaction all week.",
   "queue_this_week":{
     "undelegated_egld":sk["undelegated_week"],
     "distinct_callers":sk["undelegate_callers"],
     "measured_pending_egld":sk["pool_total"],
     "largest_legs":pool_rows[:10],
     "coverage_note":F["unbonding_pool_coverage_note"]}},
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
     f"Compound rate {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} reDelegateRewards vs {cvc['claim_count']} claimRewards) - the LOWEST reading in the nine-point series (58.54 / 60.35 / 61.59 / 60.19 / 58.81 / 62.25 / 59.54 / 59.07 / {cvc['compound_pct_of_reward_decisions']:.2f}) and a third consecutive decline.",
     "A falling compound rate during a DECLINE reads as panic-claiming (run #11 framing). A falling compound rate during a +30.43% week is the opposite behaviour with the same sign: delegators monetising yield into strength.",
     "INSTITUTIONAL TIER SOLD FOR THE FIRST TIME: 3 of 4 institutional-tier claims (50-1000 EGLD) went to a labelled exchange, 258.80 EGLD sold against 257.64 held. Small sample, but the run #11 baseline had this tier at 50/50 and retail at zero selling.",
     "RETAIL STILL DOES NOT SELL: 53 retail claims, ZERO to any labelled exchange. 46 held, 3 into DeFi, 1 rotated provider. Nine runs, no retail selling observed.",
     "Mid-tier (1-50 EGLD): 17 held, 3 DeFi deposits, 2 provider rotations, 2 unlabelled. No exchange destinations.",
     "unDelegate calls were 2.76% of observed function calls and withdraw 3.41% - both elevated against the compound/claim pair, consistent with the week's unbonding activity.",
     "PROVIDER OPERATORS DID NOT SELL FEES, for a tenth consecutive run. Zero exchange destinations across all sampled owner wallets in 30 days.",
     "truststaking's owner is XOXNO: Deployer Wallet and it made the only meaningful operator move: 2,481 EGLD into a DeFi contract, 150 held.",
     "stakingagency's operator moved 445 EGLD to unlabelled destinations, thepalmtreenw 650, istariv 596 - all treasury-scale, none to venues.",
     "The two 100%-fee providers' owner wallets each hold 1.69 EGLD, have received NOTHING in 30 days and sent one small transfer each (511 and 698 EGLD) to two DIFFERENT unlabelled recipients - so the run #21 question of whether the two operators share a counterparty is answered NO on the available evidence.",
     "Sample: 8 providers requested, 7 with usable inbound windows, 615 function calls, 81 traced claims."]},
 "analysis":(
  f"THE FIRST OPERATOR EXIT IN TWENTY-TWO RUNS. p2p_org_ - a provider with 1,244 delegators and a name that belongs to a large institutional staking business - called unStakeNodes this week and went from 67,500 EGLD of node stake plus 2,083 of topUp to ZERO locked. Its 50 nodes are still registered in the API, its 1,244 users are still attached, and its APR now reads 0. "
  f"That is a qualitatively different event from the 'provider left the active set' entries of prior runs, which were books draining as delegators left; this is the operator withdrawing the nodes underneath the book. It is also the second leg of a story that began in run #21, when a single wallet unDelegated 149,585 EGLD from this exact contract.\n\n"
  f"MECHANICALLY IT DOMINATES EVERY DELEGATION AGGREGATE, AND MUST BE NETTED OUT OF ALL OF THEM. Delegation TVL fell {sk['delta_locked']:+,.0f} to {f(tl)}; p2p_org_'s {f(abs(sk['p2p_prev_locked']))} is {100*abs(sk['p2p_prev_locked'])/abs(sk['delta_locked']):.0f}% of that, and ex-p2p_org_ delegation moved {sk['delta_locked']+sk['p2p_prev_locked']:+,.0f} - flat. "
  f"The delegator count fell {sk['users_delta']:+,} to {f(sk['users'])}, which on its face BREAKS the nine-week flat series that run #18 promoted to a background assumption. It does not: {sk['p2p_users']:,} of those users are p2p_org_'s, and they left the count only because the working set is providers with locked > 0, not because anyone undelegated. Ex-p2p_org_ the base moved {sk['users_ex_p2p']:+,}. Participation inertia survives, and the honest statement is that the model cannot currently see whether those 1,244 people have noticed their provider has no stake.\n\n"
  f"UNDERNEATH, ROTATION TO YIELD CONTINUED. pi-staking took +{f(next(m['delta'] for m in sk['moves'] if m['identity']=='pi-staking'))} and +{next(m['users_delta'] for m in sk['moves'] if m['identity']=='pi-staking')} users at 9.31% APR and 0% fee - an eleventh consecutive week of growth for the clearest best-deal provider on the network. stakenest +{f(next(m['delta'] for m in sk['moves'] if m['identity']=='stakenest'))} (0% fee, 8.90%), vaporrepublic +{f(next(m['delta'] for m in sk['moves'] if m['identity']=='vaporrepublic'))} (2% fee, 8.98%), disruptivedigital +{f(next(m['delta'] for m in sk['moves'] if m['identity']=='disruptivedigital'))}. The zero-fee cohort took +{f(sum(m['delta'] for m in sk['moves'] if m['fee']==0))} net across 11 providers. Against that Synexis lost {f(next(m['delta'] for m in sk['moves'] if m['identity']=='Synexis'))} to a single wallet unDelegating 26,692 across three providers while GAINING 10 users, which is the classic one-large-holder-leaves shape.\n\n"
  f"THE 100%-FEE PROVIDERS DID NOT REVERSE, DID NOT DEREGISTER, AND DID NOT HALVE. procryptostaking {f(next(m['delta'] for m in sk['moves'] if m['identity']=='procryptostaking'))} ({100*next(m['delta'] for m in sk['moves'] if m['identity']=='procryptostaking')/156917:.1f}%) and egldstakingprovider {f(next(m['delta'] for m in sk['moves'] if m['identity']=='egldstakingprovider'))} ({100*next(m['delta'] for m in sk['moves'] if m['identity']=='egldstakingprovider')/94349:.1f}%), both still at serviceFee 1.0 with 0% APR and 50 nodes each, and users of {next(m['users'] for m in sk['moves'] if m['identity']=='procryptostaking'):,} ({next(m['users_delta'] for m in sk['moves'] if m['identity']=='procryptostaking'):+d}) and {next(m['users'] for m in sk['moves'] if m['identity']=='egldstakingprovider'):,} ({next(m['users_delta'] for m in sk['moves'] if m['identity']=='egldstakingprovider'):+d}). "
  f"None of the three pre-registered branches has fired at threshold, so the test stays OPEN into week two. What the week did add is that {f(sum(abs(m['delta']) for m in sk['moves'] if m['identity'] in ('procryptostaking','egldstakingprovider')))} EGLD left two providers paying literally nothing while 8,110 people stayed - the strongest inertia reading available, and the same shape as run #21's.\n\n"
  f"THE UNBONDING QUEUE IS NOW A SERIES, NOT A CARD. Run #21 recommended recording it weekly and this run does, using the correct join key (previous.json stores providers by IDENTITY, not address - the first attempt joined on address and produced 79 phantom movers and zero wallets). "
  f"Across the ten providers that moved more than 5,000 EGLD, {sk['undelegate_callers']} distinct wallets called unDelegate for {f(sk['undelegated_week'])} EGLD, of which the largest single leg is 26,692 from one wallet spread over Synexis, ninjastaking and pokerstaking. Measured pending unbonding across the wallets queried is {f(sk['pool_total'])} EGLD, settling over the next 2-8 days.\n\n"
  f"AND THE RESIDUAL STILL CARRIES NO DIRECT-NODE SIGNAL. Staked rose {M['staked_chg']:+,.0f} while delegation fell {sk['delta_locked']:+,.0f}, so the staked-minus-delegated residual is {sk['residual']:+,.0f}. Run #21's rule says decompose before attributing: p2p_org_'s {f(abs(sk['p2p_prev_locked']))} node unstake is now unbonding inside the staking module, and at least {f(sk['undelegated_week'])} of fresh delegator unDelegations sit there too - {f(abs(sk['p2p_prev_locked'])+sk['undelegated_week'])} against a {f(sk['residual'])} residual, measured across the largest movers ALONE. "
  f"The residual is fully absorbed by unbonding in flight with room to spare, so no direct-node number can be extracted from it this week and none is published. That also forces a correction to run #21, which subtracted ONE wallet's 229,865 and published 'direct-node stake GREW +52,848' - that subtraction was incomplete by construction, and the figure is withdrawn."),
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
   "mex_pair_depth":xx["mex_pair_depth"]},
 "analysis":(
  f"MEX MATCHED EGLD ALMOST EXACTLY AND THAT RESOLVES THE RELATIVE-STRENGTH TEST ON THE LETTER OF ITS THRESHOLD. MEX {xx['mex_wow']:+.2f}% against EGLD {pc:+.2f}% - a fifth consecutive week of MEX >= EGLD, by 0.08pp. "
  f"Over the five weeks the gap compounds to something real: EGLD went 3.16 -> {price:.2f} (+13.92%) while MEX went 2.7007e-7 -> {xx['mex_price']:.4e} (+23.73%), so MEX has outperformed by roughly 9.8pp. "
  f"The MECHANISM, which run #21 asked for, is still not identified. MEX circulating supply moved {100*(tk['mex_supply']-tk['mex_prev_supply'])/tk['mex_prev_supply']:+.3f}% ({f(tk['mex_prev_supply']-tk['mex_supply'])} tokens burned) - real but three orders of magnitude too small to price a 10pp outperformance. "
  f"Pool depth is not the answer either: MEX/WEGLD holds ${f(xx['mex_pair_depth']['tvl_usd'])} ({xx['mex_pair_depth']['share_of_pool_tvl_pct']:.1f}% of xExchange TVL, rank {xx['mex_pair_depth']['depth_rank']}) on {xx['mex_pair_depth']['trades_24h']} trades, up from $291,459 - it grew WITH the market, not ahead of it. So the test fires as predicted and the follow-up question is re-registered rather than answered.\n\n"
  f"THE DEX WOKE UP. Volume ${f(xx['vol'])} against ${f(xx['prev_vol'])} (+{100*(xx['vol']-xx['prev_vol'])/xx['prev_vol']:.0f}%) on pool TVL ${f(xx['pool_tvl'])} (+{100*(xx['pool_tvl']-xx['prev_pool_tvl'])/xx['prev_pool_tvl']:.1f}%), giving a turnover ratio of {xx['turnover']:.2f}% against {xx['prev_turnover']:.2f}%. "
  f"That is the single largest move in any demand instrument the model tracks, and it is the exact inverse of the run #18 diagnostic: there, price fell on collapsing volume with intact depth, which was read as an absent bid. Here price rose on volume tripling with depth also rising. Concentration stayed extreme - WEGLD/USDC is {xx['top_pairs'][0]['share_pct']:.1f}% of all volume on {xx['top_pairs'][0]['trades_count_24h']:,} trades - so the venue is deep in exactly one place, and a thin book everywhere else is still the structural condition.\n\n"
  f"STABLECOINS: USDT recovered to {f(tk['stable']['USDT-f8c08c']['supply'])} ({100*(tk['stable']['USDT-f8c08c']['supply']-549884)/549884:+.2f}%), which closes run #21's drain question on the benign branch - one desk redeemed, the bridge is not emptying. USDC {f(tk['stable']['USDC-c76f1f']['supply'])}. The on-chain dollar base is roughly $8.3M, which remains small enough that a single large redemption moves it double digits.\n\n"
  f"HOLDER COUNTS FELL ACROSS THE BOARD AGAIN - WEGLD -137, MEX -103, ZoidPay -107, UTK -102, holoride -99 - continuing a pattern that has now run for most of the tracking period and is best read as dust-account attrition rather than adoption loss, since transaction counts rose on every one of them. "
  f"NEWLY ISSUED: two issuances cleared the scan and neither clears the quality bar - 'Mybigbone' (1 holder, 0 transactions) and a token that names itself Bitcoin with ticker BTC (3 holders, 23 transactions). The latter is a ticker-spoof of the sort the >10-holder filter exists to catch, and it is worth noting that the filter is the only thing standing between it and the report's top-5 list."),
}

# ---------------- defi -----------------------------------------------------
def hs(pct,fl=2.0):
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
   "notable_events":f"THE TURNOVER RECOVERY BECAME A REGIME CHANGE: {xx['prev_turnover']:.2f}% -> {xx['turnover']:.2f}% of pool TVL traded daily, on volume ${f(xx['vol'])} (+{100*(xx['vol']-xx['prev_vol'])/xx['prev_vol']:.0f}%) and depth ${f(xx['pool_tvl'])} (+{100*(xx['pool_tvl']-xx['prev_pool_tvl'])/xx['prev_pool_tvl']:.1f}%). Series 4.06 / 2.14 / 2.24 / 2.93 / {xx['turnover']:.2f}. WEGLD contract balance {f(df['xexch_egld'])} EGLD, roughly flat in EGLD terms - the USD gain of {xe_pct:+.1f}% is price. WEGLD supply {f(tk['wegld_supply'])}. Concentration {xx['top_pairs'][0]['share_pct']:.1f}% WEGLD/USDC.",
   "health_signal":"spiking"},
  {"protocol":"Hatom Lending","category":"lending","addresses_tracked":13,
   "tvl_usd":df["hatom_lending_usd"],"tvl_egld":df["hatom_lending_egld"],
   "tvl_wow_change_pct":df["hatom_lending_egld_pct"],
   "transfers_24h":proto.get("Hatom EGLD MM"),
   "notable_events":f"BILATERAL INVERSE RULE: THIRD UP-WEEK CONFIRMATION, WEAKEST RESPONSE YET. Price {pc:+.2f}% (evaluable - past the |5%| guardrail), EGLD-denominated TVL {df['hatom_lending_egld_pct']:+.2f}%, correct inverse sign, response ratio {df['inverse_ratio']:.2f}. Up-week series 0.49 / 0.72 / {df['inverse_ratio']:.2f}; full series now 9 confirmations. The ratio has fallen below the 0.30 depositor-capacity threshold the methodology registers, which is emitted as a rule-based anomaly. USD TVL ${f(df['hatom_lending_usd'])} (+{100*(df['hatom_lending_usd']-df['hatom_lending_prev_usd'])/df['hatom_lending_prev_usd']:.1f}%) is entirely the price move.",
   "health_signal":"shrinking"},
  {"protocol":"Hatom Liquid Staking","category":"liquid_staking","addresses_tracked":2,
   "tvl_usd":df["hatom_lsd_usd"],"tvl_egld":df["hatom_lsd_usd"]/price,
   "tvl_wow_change_pct":lsd_pct,"transfers_24h":proto.get("Hatom Liquid Staking"),
   "notable_events":f"SUPPLY BASIS (run #13 rule): SEGLD {lsd_pct:+.3f}% to {f(tk['lsd']['SEGLD-3ad2d0']['supply'])} - a fifth consecutive flat week, and the first with a POSITIVE sign in four. SWTAO {tk['lsd']['SWTAO-356a25']['pct']:+.2f}% to {f(tk['lsd']['SWTAO-356a25']['supply'])}. SWTAO price returned NULL from /tokens/SWTAO-356a25 through the main pass and all four 2.5s isolated retries (run #14 pattern) - but the /tokens?sort=marketCap LIST endpoint returned a live $305.80 for the same token in the same run, so no estimate was needed. That is a NEW and better fallback than run #14's prior-price carry-forward: cross-check the list endpoints before deriving anything. A +30% price week produced no subscription into the largest LSD, which is the same inertia the delegation base shows.",
   "health_signal":"flat"},
  {"protocol":"Hatom USH","category":"stablecoin","addresses_tracked":4,
   "tvl_usd":df["ush_usd"],"tvl_egld":df["ush_usd"]/price,
   "tvl_wow_change_pct":tk["lsd"]["USH-111e09"]["pct"],"transfers_24h":None,
   "notable_events":f"USH BURNED {tk['lsd']['USH-111e09']['pct']:+.2f}% ({f(abs(tk['lsd']['USH-111e09']['supply']-tk['lsd']['USH-111e09']['prev']))} tokens) to {f(tk['lsd']['USH-111e09']['supply'])} INTO a +30% rally - the largest burn since run #19 and the first of any size during an up-week. The run #11/#16 framing has burns as de-leveraging during declines and mints as leverage returning during rallies; this is neither. CDP borrowers repaid as their collateral appreciated, which is de-risking into strength rather than out of weakness. Two consecutive noise-band weeks ended.",
   "health_signal":"shrinking"},
  {"protocol":"XOXNO LSD","category":"liquid_staking","addresses_tracked":3,
   "tvl_usd":df["xoxno_usd"],"tvl_egld":df["xoxno_usd"]/price,
   "tvl_wow_change_pct":tk["lsd"]["XEGLD-e413ed"]["pct"],"transfers_24h":proto.get("XOXNO LSD"),
   "notable_events":f"XEGLD supply {tk['lsd']['XEGLD-e413ed']['pct']:+.3f}% to {f(tk['lsd']['XEGLD-e413ed']['supply'])} - a third consecutive deceleration from the run #14 -29.2% collapse, and now inside the noise band. The redemption episode is over. {proto.get('XOXNO LSD')} transfers in 24h.",
   "health_signal":"flat"},
  {"protocol":"XOXNO Aggregator","category":"aggregator","addresses_tracked":1,
   "tvl_usd":0.0,"tvl_egld":0.0,"tvl_wow_change_pct":None,
   "transfers_24h":proto.get("XOXNO Aggregator"),"volume_24h_usd":0.0,
   "notable_events":f"{f(proto.get('XOXNO Aggregator') or 0)} transfers in 24h, the highest reading recorded for this contract and consistent with the DEX turnover spike. Non-custodial routing, so TVL is not the metric.",
   "health_signal":"spiking"},
  {"protocol":"OneDex","category":"aggregator","addresses_tracked":5,
   "tvl_usd":0.0,"tvl_egld":0.0,"tvl_wow_change_pct":None,
   "transfers_24h":proto.get("OneDex Swap"),"volume_24h_usd":0.0,
   "notable_events":f"{f(proto.get('OneDex Swap') or 0)} transfers in 24h. Aggregator - throughput is the metric. One of its tracked addresses (OneDex Launchpad) still fails bech32 validation and is excluded rather than guessed, a gap open since run #18.",
   "health_signal":"growing"},
  {"protocol":"JEXchange","category":"dex","addresses_tracked":4,
   "tvl_usd":0.0,"tvl_egld":0.0,"tvl_wow_change_pct":None,
   "transfers_24h":proto.get("JEXchange Fees"),"volume_24h_usd":0.0,
   "notable_events":f"Fees contract {f(proto.get('JEXchange Fees') or 0)} transfers in 24h; the aggregator contract returned 0 for a second run, which is a data gap rather than a confirmed halt.",
   "health_signal":"flat"}],
 "sc_deployments":[],
 "analysis":(
  f"DeFi split cleanly this week between the venues, which boomed, and the credit stack, which de-risked.\n\n"
  f"xExchange had its single best week in the tracked series on every activity measure: volume ${f(xx['vol'])} (+{100*(xx['vol']-xx['prev_vol'])/xx['prev_vol']:.0f}%), pool TVL ${f(xx['pool_tvl'])} (+{100*(xx['pool_tvl']-xx['prev_pool_tvl'])/xx['prev_pool_tvl']:.1f}%), turnover {xx['turnover']:.2f}% against a prior series high of 4.06%. The XOXNO aggregator processed {f(proto.get('XOXNO Aggregator') or 0)} transfers in 24 hours and OneDex {f(proto.get('OneDex Swap') or 0)}, both at or near their highest recorded. Whatever else is true about the week, people traded.\n\n"
  f"The credit stack did the opposite. Hatom Lending's EGLD-denominated deposits fell {df['hatom_lending_egld_pct']:+.2f}% - the bilateral inverse rule firing correctly for a third up-week, with depositors withdrawing to bank a +30% move - and USH burned {tk['lsd']['USH-111e09']['pct']:+.2f}%, meaning CDP borrowers retired debt rather than levering into the rally. Those are the same cohort behaving consistently: reduce exposure while the price is good. "
  f"The response ratio of {df['inverse_ratio']:.2f} is the weakest confirmation the rule has produced on an up-week (0.49, then 0.72, now {df['inverse_ratio']:.2f}), and it sits below the 0.30 threshold the methodology defined as depositor-capacity exhaustion. The straightforward reading is that there are fewer deposits left to withdraw than there were in June.\n\n"
  f"The liquid-staking stack did nothing at all. SEGLD {lsd_pct:+.3f}%, XEGLD {tk['lsd']['XEGLD-e413ed']['pct']:+.3f}%, SWTAO {tk['lsd']['SWTAO-356a25']['pct']:+.2f}% - all inside the noise band on the supply basis, through a 30% price move. This matters more than it looks: an LSD is the instrument you would expect to see subscriptions into if holders were converting a rally into yield-bearing positions, and there were none. It is the same inertia the flat delegator base shows, measured a different way.\n\n"
  f"TVL METHOD NOTE: LSD and stablecoin figures are reported on the supply basis per the run #13 rule, with USD as context only - during a +30% price week the mcap-based view would have shown every EGLD-denominated protocol 'growing' 30% while nothing moved. SWTAO's per-token price nulled through all retries again (run #14 pattern), but the /tokens?sort=marketCap list endpoint carried a live price for it - so the value is measured, not estimated, and the run #14 carry-forward fallback was not needed."),
}
json.dump(R,open("/tmp/run22w/part2.json","w"),indent=1,default=str)
print("part2 ok:",list(R.keys()))
