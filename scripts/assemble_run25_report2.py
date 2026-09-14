#!/usr/bin/env python3
"""Run #25 stage 3: staking, tokens, defi -> /tmp/run25w/part2.json"""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-09-14"
O=json.load(open("/tmp/run25w/derived.json"))
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
beh=json.load(open(f"{REPO}/data/collected/delegator_behavior_{RD}.json"))
r24=json.load(open(f"{REPO}/reports/2026-09-07.json"))
M=O["macro"]; sk=O["staking"]; tk=O["tokens"]; xx=O["xexchange"]; df=O["defi"]
bid=O["bid"]; ub=O["unbond"]; p2p=O["p2p"]; MEXE=O["mex_event"]
econ=D["economics"]; price=M["price"]; pc=M["price_chg"]
def f(x,d=0):
    try: return f"{x:,.{d}f}"
    except: return str(x)
provs=sk["provs"]; tl=sk["total_locked"]
pkey={p["provider"]:p for p in prev["staking_providers"]}
paddr={p["address"]:p for p in prev["staking_providers"]}
def pk(p): return p.get("identity") or p["provider"]
def prevrow(p): return pkey.get(pk(p)) or paddr.get(p["provider"]) or {}
ag=beh["aggregates"]; cvc=ag["compound_vs_claim_at_function_level"]
def mv(ident,field,default=0):
    return next((m[field] for m in sk["moves"] if m["identity"]==ident), default)
zsc=O["zero_stake_cohort"]
dser={d["identity"]:d for d in O["dereg_series"]}
LF=next((r for r in zsc["with_activity_this_week"] if r["provider"]=="ledgerbyfigment"), {})
LFC=LF.get("function_counts",{})
fates=ag["delegator_fates_by_tier"]
withdraw_calls=sum(v["function_counts"].get("withdraw",0) for v in D["provider_inbound_all"].values())
prev_withdraw_calls=None
try:
    P7=json.load(open(f"{REPO}/data/collected/2026-09-07.json"))
    prev_withdraw_calls=sum(v["function_counts"].get("withdraw",0) for v in P7["provider_inbound_all"].values())
except Exception: pass
R={}

top_providers=[]
for i,p in enumerate(provs[:20],1):
    k=pk(p); pl=prevrow(p).get("locked_egld")
    top_providers.append({"rank":i,"identity":k,"name":k,"provider_address":p["provider"],
      "locked_egld":p["_lk"],"previous_locked_egld":pl,
      "share_pct":100*p["_lk"]/tl,"apr_pct":p.get("apr") or 0,
      "fee_pct":(p.get("serviceFee") or 0)*100,"num_users":p.get("numUsers") or 0,
      "num_nodes":p.get("numNodes") or 0,
      "wow_change_egld":(p["_lk"]-pl) if pl is not None else None})

pool_rows=sk["pool_rows"][:12]
states=[]
for r in zsc["emptied_inside_archive"]:
    d=dser.get(r["provider"],{})
    states.append({"provider":r["provider"],"state":"deregistered","locked_egld":0.0,
      "num_users":r["users"],"num_nodes":r["nodes"],"apr_pct":0.0,"fee_pct":0.0,
      "weeks_in_state":{"ledgerbyfigment":13,"p2p_org_":4,"truststakingsw":15}.get(r["provider"],2),
      "note":(f"emptied inside the archive - last snapshot with locked > 0 was {r['last_locked_in_archive']}. "
              f"{r['inbound_txs_this_week']} inbound txs this week"
              + (f"; delegators {d['prev_users']:,} -> {d['users']:,} ({d['users_delta']:+d})" if d.get("users") is not None and d.get("prev_users") is not None else ""))})
for ident in ("egldstakingprovider","procryptostaking"):
    states.append({"provider":ident,"state":"fee_squeezed","locked_egld":mv(ident,"locked"),
      "num_users":mv(ident,"users"),"num_nodes":mv(ident,"nodes"),
      "apr_pct":mv(ident,"apr"),"fee_pct":mv(ident,"fee"),"weeks_in_state":2,
      "note":f"SECOND WEEK AFTER THE FEE REVERSAL: fee {mv(ident,'fee'):.0f}%, APR {mv(ident,'apr'):.2f}%, book {mv(ident,'delta'):+,.0f}, users {mv(ident,'users_delta'):+d}. Capital that left during the 100%-fee weeks has not come back."})
for r in O["identity_renames"]:
    states.append({"provider":r["new_identity"],"state":"active","locked_egld":r["locked"],
      "num_users":r["users"],"num_nodes":0,"apr_pct":0.0,"fee_pct":0.0,"weeks_in_state":1,
      "note":f"IDENTITY RENAMED from '{r['old_identity']}' (contract {r['address'][:18]}...). The identity-keyed join read it as a {r['prev_locked']:,.0f} EGLD leaver; on the contract address the book moved {r['delta']:+,.0f}."})

R["staking_intelligence"]={
 "summary":{"total_staked_egld":econ["staked"],"total_delegated_egld":tl,
   "staked_ratio":M["sr"],"num_providers":len(provs),
   "apr_min":sk["apr_min"],"apr_max":sk["apr_max"],"apr_weighted_avg":sk["apr_wavg"]},
 "top_providers":top_providers,
 "concentration":{"top_5_share_pct":sk["top5"],"top_10_share_pct":sk["top10"],
   "hhi":sk["hhi"],"hhi_previous":sk["prev_hhi"],
   "hhi_interpretation":f"HHI {sk['hhi']:.5f} (previous {sk['prev_hhi']:.5f}), far below the 0.15 competitive threshold; top-5 {sk['top5']:.2f}%, top-10 {sk['top10']:.2f}%. Concentration is not where this week's staking story is."},
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
 "identity_renames":O["identity_renames"],
 "zero_stake_cohort":{
   "contracts":zsc["contracts"],
   "attached_delegator_records":zsc["attached_delegator_records"],
   "share_of_all_delegator_records_pct":zsc["share_of_all_delegator_records_pct"],
   "emptied_inside_archive":len(zsc["emptied_inside_archive"]),
   "with_activity_this_week":len(zsc["with_activity_this_week"]),
   "archive_snapshots":zsc["archive_snapshots"],
   "archive_first_snapshot":zsc["archive_first"],
   "transitions_this_week":len(O["dereg_transitions"]),
   "note":("Deregistration is now scored as an observed TRANSITION: locked > 0 in the prior stored snapshot and locked == 0 now "
           "(run #24 rec #4). Zero transitions this week. The 82-contract cohort is context, not news.")},
 "fee_events":[
   {"provider":i,"fee_from_pct":100.0,"fee_to_pct":mv(i,"fee"),"apr_from_pct":0.0,"apr_to_pct":mv(i,"apr"),
    "locked_egld":mv(i,"locked"),"locked_wow_egld":mv(i,"delta"),"users":mv(i,"users"),
    "users_wow":mv(i,"users_delta"),"num_nodes":mv(i,"nodes")}
   for i in ("egldstakingprovider","procryptostaking")],
 "unbonding_in_flight":{
   "wallet":ub["wallet"],"total_egld":ub["pending_total"],
   "legs":[{"provider":(p["contract"][:10]+"..."+p["contract"][-8:]),"amount":p["amount_egld"],
            "days_to_unbond":p["days_remaining"],"date":"2026-08-14" if p["amount_egld"]<100000 else "2026-08-15"}
           for p in ub["pending"]],
   "share_of_delegation_decline_pct":0.0,
   "raw_residual_egld":sk["residual"],
   "corrected_direct_node_egld":None,
   "status":(f"RETIRED, FOURTH WEEK UNMOVED. Balance {f(ub['balance'],2)} EGLD, {f(ub['pending_total'])} EGLD still unbonded-and-unclaimed, zero outbound transactions. Reported only so it cannot reappear as a surprise."),
   "queue_this_week":{
     "undelegated_egld":sk["undelegated_week"],"distinct_callers":sk["undelegate_callers"],
     "measured_pending_egld":sk["pool_total"],"largest_legs":pool_rows,
     "withdraw_calls":withdraw_calls,"previous_withdraw_calls":prev_withdraw_calls,
     "coverage_note":(f"Full-set scan of all {sk['providers_scanned']} provider contracts with locked > 0 or nodes > 0; {len(O['scan_depth']['deep_scanned'])} busy contracts re-paged at 30 pages. "
                      f"{sk['undelegate_callers']} wallets unDelegated {f(sk['undelegated_week'])} EGLD, down from 208,125 by 537 last week. {withdraw_calls} withdraw calls against {prev_withdraw_calls} last week (amounts not decoded). "
                      f"CAVEAT: {len(O['scan_depth']['pagecap_provscan'])} first-pass scans still ended on the page cap before the deep pass; the deep pass superseded them.")}},
 "reward_behavior":{
   "providers_sampled":ag["providers_sampled"],"delegator_window_days":ag["window_days"],
   "operator_window_days":ag["operator_window_days"],
   "function_distribution":ag["overall_function_distribution"],
   "compound_pct_at_function_level":cvc["compound_pct_of_reward_decisions"],
   "compound_vs_claim":{"redelegate_count":cvc["redelegate_count"],"claim_count":cvc["claim_count"]},
   "delegator_fates_by_tier":fates,
   "provider_operators":[{"provider":pr.get("identity") or pr.get("provider_address"),
     "owner_address":(pr.get("operator") or {}).get("owner_address") or pr.get("owner_address"),
     "owner_label":(pr.get("operator") or {}).get("owner_label","Unknown"),
     "owner_balance_egld":(pr.get("operator") or {}).get("owner_balance_egld"),
     "outbound_count":(pr.get("operator") or {}).get("outbound_count_30d",0),
     "fates_by_count":(pr.get("operator") or {}).get("fates_by_count",{}),
     "fates_by_value_egld":(pr.get("operator") or {}).get("fates_by_value_egld",{})}
     for pr in beh.get("per_provider",[])],
   "key_findings":[
     f"CLAIMS OUTNUMBERED COMPOUNDS FOR THE FIRST TIME IN TWELVE READINGS: {cvc['compound_pct_of_reward_decisions']:.2f}% ({cvc['redelegate_count']} reDelegateRewards vs {cvc['claim_count']} claimRewards). Series: 58.54 / 60.35 / 61.59 / 60.19 / 58.81 / 62.25 / 59.54 / 59.07 / 57.03 / 57.51 / 62.05 / {cvc['compound_pct_of_reward_decisions']:.2f}.",
     "The previous low was 57.03%. This is a 12.6pp one-week fall from the highest reading in the series to the lowest, in a week when EGLD went from about $5.17 to $4.14. The compound rate has never moved this far in one week.",
     f"THE CLAIMS WERE NOT SOLD. Retail {fates['retail']['total_events']} claims, zero to a labelled exchange ({fates['retail']['by_count'].get('held',0)} held, {fates['retail']['by_count'].get('rotated_provider',0)} rotated provider, {fates['retail']['by_count'].get('defi_deposit',0)} into DeFi) - a twelfth consecutive run.",
     f"Mid-tier {fates['mid_tier']['total_events']} claims, {fates['mid_tier']['by_count'].get('sold',0)} to an exchange; institutional {fates['institutional']['total_events']} claims, {fates['institutional']['by_count'].get('sold',0)} sold ({fates['institutional']['by_value_egld'].get('sold',0):.0f} EGLD).",
     f"withdraw was {ag['overall_function_distribution'].get('withdraw',{}).get('share_pct',0):.2f}% of sampled calls and unDelegate {ag['overall_function_distribution'].get('unDelegate',{}).get('share_pct',0):.2f}%, consistent with the full-set scan: new exits down sharply, completions roughly steady.",
     "PROVIDER OPERATORS DID NOT SELL FEES for a thirteenth consecutive run: zero exchange destinations across all sampled owner wallets in 30 days.",
     f"Sample: {ag['providers_sampled']} providers, {sum(v['count'] for v in ag['overall_function_distribution'].values())} function calls, {sum(t['total_events'] for t in fates.values())} traced claims. A first concurrent pass that sampled only 4 providers under rate limiting was discarded."]},
 "analysis":(
  f"THE SECURITY BUDGET SHRANK, BUT MOST OF THE MOVE WAS DECIDED WEEKS AGO. Staked EGLD {M['staked_chg']:+,.0f} to {f(econ['staked'])}, ratio {100*M['sr']:.2f}% - below the 46.80% branch of run #24's three-week test in its first week. "
  f"Delegation TVL went the other way, {sk['delta_locked']:+,.0f} to {f(tl)}. When active delegation grows while total staked falls by {f(abs(M['staked_chg']))}, the missing EGLD is leaving through the unbonding exit, not the active book. "
  f"The full-set scan is consistent with that reading but does not prove it: {withdraw_calls} withdraw calls on provider contracts against {prev_withdraw_calls} last week (a modest rise, amounts not decoded), and new unDelegations down to {f(sk['undelegated_week'])} EGLD from {sk['undelegate_callers']} wallets (last week 208,125 from 537). "
  f"The residual of {f(sk['residual'])} cannot be split cleanly into direct-node and unbonding components, so no corrected direct-node figure is published for a fourth run.\n\n"
  f"THE REWARD DECISION FLIPPED. Compound rate {cvc['compound_pct_of_reward_decisions']:.2f}%, the first reading below 50% in twelve, a week after the series high. Claims {cvc['claim_count']} against {cvc['redelegate_count']} redelegations across {ag['providers_sampled']} providers. "
  f"The claims went into wallets, not to exchanges: retail zero sold for a twelfth run, mid-tier one of {fates['mid_tier']['total_events']}. "
  f"The run #11 framing reads a falling compound rate during a decline as retail panic-claiming. The fate data does not support the panic part, because nothing was sold. It supports a narrower reading: stakers stopped adding to positions when the price turned, and kept the yield liquid.\n\n"
  f"THE DELEGATOR BASE {sk['users_delta']:+,} to {f(sk['users'])} on the locked>0 basis; {sk['gaining']} providers gained delegators and {sk['losing']} lost them. The breadth is worse than the net, but the count stays inside the inertia base rate for a thirteenth week.\n\n"
  f"PROVIDER MOVES: pi-staking {mv('pi-staking','delta'):+,.0f} ({mv('pi-staking','users_delta'):+d} delegators, 0% fee, {mv('pi-staking','apr'):.2f}% APR) is the largest gainer for a second week, then vaporrepublic {mv('vaporrepublic','delta'):+,.0f} and star_staking {mv('star_staking','delta'):+,.0f}; meria {mv('meria','delta'):+,.0f} is the largest loser. "
  f"The fee-reversed providers lost book for a second week after restoring APR: egldstakingprovider {mv('egldstakingprovider','delta'):+,.0f} ({mv('egldstakingprovider','users_delta'):+d} users), procryptostaking {mv('procryptostaking','delta'):+,.0f}. Run #24 asked for a second week before calling it; the asymmetry is now measured: capital that left under a 100% fee has not returned in two weeks of restored yield.\n\n"
  f"A JOIN TRAP, CAUGHT BEFORE PUBLICATION. The collector reported cslabsio as a 177,587 EGLD leaver. It is not: the contract renamed its identity to chainstatelabs and its book moved +{f(O['identity_renames'][0]['delta'])} EGLD. kevinlallement -> dinovox did the same at 8,804 EGLD. The run #22 rule joined on identity to fix an address/identity mismatch, and a rename breaks it the other way. Joins now fall back to the contract address, which is the only stable key.\n\n"
  f"DEREGISTRATION ON A TRANSITION BASIS: zero providers moved from locked > 0 to zero this week (week 2 of the four-week test). ledgerbyfigment {dser.get('ledgerbyfigment',{}).get('users_delta',0):+d} to {f(dser.get('ledgerbyfigment',{}).get('users',0))}, p2p_org_ {dser.get('p2p_org_',{}).get('users_delta',0):+d} to {f(dser.get('p2p_org_',{}).get('users',0))}, stakedinc unchanged. The unbond wallet is unmoved for a fourth week."),
}

# ---------------- tokens ---------------------------------------------------
ph={t["identifier"]:t for t in prev["top_tokens_by_holders"]}
pv={t["identifier"]:t for t in prev["top_tokens_by_volume"]}
def th(t):
    i=t["identifier"]; prevh=ph.get(i,{}).get("holders")
    return {"identifier":i,"name":t.get("name"),"holders":t.get("accounts") or 0,"previous_holders":prevh,
            "holders_change":(t.get("accounts",0)-prevh) if prevh is not None else None,
            "price_usd":t.get("price"),"market_cap_usd":t.get("marketCap"),"volume_24h_usd":None}
def tv(t):
    i=t["identifier"]; pt=pv.get(i,{}).get("transactions")
    return {"identifier":i,"name":t.get("name"),"transactions":t.get("transactions") or 0,"previous_transactions":pt,
            "change_pct":(100*(t.get("transactions",0)-pt)/pt) if pt else None,"price_usd":t.get("price"),"volume_24h_usd":None}
def tm(t):
    i=t["identifier"]
    return {"identifier":i,"name":t.get("name"),"holders":t.get("accounts"),"previous_holders":ph.get(i,{}).get("holders"),
            "price_usd":t.get("price"),"market_cap_usd":t.get("marketCap"),"volume_24h_usd":None}
newly=tk["newly"]
def qual(t): return (t["accounts"] or 0)>10 and (t["transactions"] or 0)>5
hchg=sorted([th(t) for t in D["tokens_holders"][:10] if th(t)["holders_change"] is not None],key=lambda r:r["holders_change"])
R["token_activity"]={
 "top_by_holders":[th(t) for t in D["tokens_holders"][:10]],
 "top_by_volume":[tv(t) for t in D["tokens_txs"][:10]],
 "top_by_market_cap":[tm(t) for t in D["tokens_mcap"][:10]],
 "newly_issued":[{"identifier":t["identifier"],"name":t["name"],"holders":t["accounts"],
                  "transactions":t["transactions"],"deployer":t["deployer"],
                  "note":"clears the >10 holder / >5 tx quality bar" if qual(t) else "below the >10 holder / >5 tx quality bar"} for t in newly],
 "xexchange":{"total_pairs":xx["pairs"],"total_volume_24h_usd":xx["vol"],
   "mex_price_usd":xx["mex_price"],"mex_market_cap_usd":xx["mex_mcap"],
   "mex_price_change_24h_pct":None,"mex_price_change_wow_pct":xx["mex_wow"],
   "mex_price_source":xx.get("mex_price_source"),
   "top_pair":xx["top_pairs"][0]["name"],
   "top_pair_volume_24h_usd":xx["top_pairs"][0]["volume_24h_usd"],
   "top_pair_dominance_pct":xx["top_pairs"][0]["share_pct"],
   "top_pairs_by_volume":xx["top_pairs"],
   "pool_tvl_usd":xx["pool_tvl"],"previous_pool_tvl_usd":xx["prev_pool_tvl"],
   "previous_pool_tvl_ex_mex_pair_usd":bid["prev_pooltvl_ex_mex_usd"],
   "pool_tvl_ex_mex_pair_wow_pct":bid["pooltvl_ex_mex_wow_pct"],
   "turnover_ratio_pct":xx["turnover"],"previous_turnover_ratio_pct":xx["prev_turnover"],
   "previous_turnover_ratio_ex_mex_pair_pct":bid["prev_turnover_ex_mex"],
   "dex_vol_wow_pct":100*(xx["vol"]-xx["prev_vol"])/xx["prev_vol"],
   "dex_volume_egld_24h":bid["dexvol_egld"],"previous_dex_volume_egld_24h":bid["prev_dexvol_egld"],
   "dex_vol_egld_wow_pct":100*(bid["dexvol_egld"]-bid["prev_dexvol_egld"])/bid["prev_dexvol_egld"],
   "pool_tvl_egld":bid["pooltvl_egld"],"previous_pool_tvl_egld":bid["prev_pooltvl_egld"],
   "wegld_usdc_share_of_volume_pct":bid["wegld_usdc_share"],
   "ex_wegld_usdc_volume_usd":bid["ex_wegld_usdc_vol"],
   "mex_pair_depth":{"pair":"MEX/WEGLD","tvl_usd":0.0,"tvl_egld":0.0,
     "previous_tvl_egld":prev["xexchange"]["mex_pair_depth"]["tvl_egld"],"tvl_egld_wow_pct":None,
     "volume_24h_usd":0.0,"trades_24h":0,"share_of_pool_tvl_pct":0.0,"depth_rank":None,
     "status":"PAUSED 2026-09-13 16:43 UTC - no longer returned by /mex/pairs"},
   "mex_pair_event":MEXE},
 "analysis":(
  f"THE MEX/WEGLD POOL IS FROZEN. At 2026-09-13 16:43 UTC the wallet that owns the xExchange router (erd1ss6u80ruas2p...) called `pause` on the MEX/WEGLD pair contract. The last successful swap was three minutes earlier. "
  f"Since then 172 transactions against the pair have failed, 116 of them removeLiquidity calls from LPs trying to get out. The contract still holds {f(MEXE['pair_holds_mex']/1e9,1)}B MEX and {f(MEXE['pair_holds_wegld'])} WEGLD (about ${f(MEXE['pair_holds_wegld']*price)} of EGLD). "
  f"Last week this was the #2 deepest pool on the venue at ${f(MEXE['prev_pair_tvl_usd'])}. The API now omits it: /mex/pairs does not list it, /mex/pairs/MEX-455c57/WEGLD-bd4d79 returns 404, and /mex/economics reports MEX at $0.\n\n"
  f"THE PRICE WENT UP, NOT DOWN. CoinGecko's MEX close was {MEXE['mex_price_coingecko_sep13']:.2e} on Sep 13 and 3.05e-06 on Sep 14, about 7.5x, on some $1.6M of volume against a two-week norm around $10K a day. It has since fallen back to {MEXE['mex_price_coingecko_now']:.2e}, still {xx['mex_wow']:+.0f}% on the week. The MultiversX /tokens endpoint carries {MEXE['mex_price_tokens_api']:.2e}. "
  f"Three sources give three different prices and none of them comes from the on-chain pool, which is frozen. Hatom's HMEX supply rose from {f(MEXE['hmex_prev_supply']/1e12,2)}T to {f(MEXE['hmex_supply']/1e12,2)}T, so MEX was deposited into the Hatom money market in size in the same week. "
  f"What is NOT on-chain is the reason for the pause. The model records the call, its sender and its effects and does not guess the motive. MEX supply moved {100*(tk['mex_supply']-tk['mex_prev_supply'])/tk['mex_prev_supply']:+.3f}%, so the week included no mint or burn.\n\n"
  f"THE REST OF THE VENUE TRADED ONE PAIR. EGLD-denominated volume {f(bid['prev_dexvol_egld'])} -> {f(bid['dexvol_egld'])}/day ({100*(bid['dexvol_egld']-bid['prev_dexvol_egld'])/bid['prev_dexvol_egld']:+.0f}%), with WEGLD/USDC {bid['wegld_usdc_share']:.1f}% of it on {xx['top_pairs'][0]['trades_count_24h']:,} trades. Every other pair together did ${f(bid['ex_wegld_usdc_vol'])}. "
  f"Price fell while volume doubled, which by the run #18 diagnostic is an aggressive offer rather than an absent bid. Raw pool TVL fell {abs(100*(xx['pool_tvl']-xx['prev_pool_tvl'])/xx['prev_pool_tvl']):.0f}% in USD, but the MEX/WEGLD pool leaving the API accounts for most of that. Like-for-like it is {bid['pooltvl_ex_mex_wow_pct']:+.1f}% in USD and {bid['pooltvl_egld_ex_mex_wow_pct']:+.1f}% in EGLD, and the turnover ratio on that base went from {bid['prev_turnover_ex_mex']:.2f}% to {xx['turnover']:.2f}%.\n\n"
  f"STABLECOINS: USDC {tk['stable']['USDC-c76f1f']['pct']:+.2f}% to {f(tk['stable']['USDC-c76f1f']['supply'])}, USDT {tk['stable']['USDT-f8c08c']['pct']:+.2f}% to {f(tk['stable']['USDT-f8c08c']['supply'])}. Combined expansion ends the three-week contraction and demotes the dollar base to DeFi plumbing, as run #24's test specified. USDT's -12.8% ({f(tk['stable']['USDT-f8c08c']['prev']-tk['stable']['USDT-f8c08c']['supply'])} tokens) is the largest weekly move in its tracked series. It was offset by USDC minting {f(tk['stable']['USDC-c76f1f']['supply']-tk['stable']['USDC-c76f1f']['prev'])}.\n\n"
  f"HOLDERS: the top-10 list shows the usual dust attrition; the largest declines this week were " + ", ".join(f"{r['identifier'].split('-')[0]} {r['holders_change']:+,}" for r in hchg[:4]) + ".\n\n"
  f"NEWLY ISSUED: {len(newly)} issuances cleared the ESDT system-SC scan, and {sum(1 for t in newly if qual(t))} of them clear the quality bar: " + ", ".join(f"{t['identifier']} ({t['accounts']} holders, {t['transactions']} txs)" for t in newly if qual(t)) + ". That ends an eight-week run in which none did. Both are small, and neither has an identifiable deployer in known-addresses."),
}

# ---------------- defi -----------------------------------------------------
def hs(pct):
    if pct is None: return None
    if pct>50: return "spiking"
    if pct>5: return "growing"
    if pct<-15: return "draining"
    if pct<-2: return "shrinking"
    return "flat"
proto=df["proto"]
xe_pct=100*(df["xexch_usd"]-df["xexch_prev_usd"])/df["xexch_prev_usd"]
xe_egld_pct=100*(df["xexch_egld"]-df["xexch_prev_usd"]/prev["economics"]["egld_price_usd"])/(df["xexch_prev_usd"]/prev["economics"]["egld_price_usd"])
lsd=tk["lsd"]; lsd_pct=lsd["SEGLD-3ad2d0"]["pct"]
em=O["emerging_lsd"]
_disc=json.load(open(f"{REPO}/data/collected/liquid_staking_discovery_{RD}.json"))
STAKE={}
for _p in _disc["liquid_staking_protocols"]:
    for _t in _p.get("receipt_tokens",[]):
        STAKE[_t["identifier"]]=_p.get("staked_egld")
# SALSA and VestaX were not surfaced by this week's sweep; measured directly (followup check)
STAKE.setdefault("LEGLD-d74da9",6419.960661549192)
STAKE.setdefault("VEGLD-2b9319",1121.362402476542)
EM_PREV={"LEGLD-d74da9":prev["lsd_staked_emerging"]["SALSA: Liquid Staking"],
         "VOXEGLD-5872e5":prev["lsd_staked_emerging"]["Dinovox: VoxEGLD Liquid Staking"],
         "VEGLD-2b9319":prev["lsd_staked_emerging"]["VestaX Finance: Liquid Staking"],
         "JWLEGLD-023462":prev["lsd_staked_emerging"]["JewelSwap: Liquid Staking"]}
def es(t): return STAKE.get(t)
def ep(t):
    p0=EM_PREV.get(t); c=es(t)
    return 100*(c-p0)/p0 if (p0 and c is not None) else None
r24pb={p["protocol"]:p for p in r24["defi_activity"]["protocol_breakdown"]}
def prev_tr(n): return r24pb.get(n,{}).get("transfers_24h")
jex7=O["jex_router_7d"]
hl_ex_pct=df["hatom_lending_ex_hmex_egld_pct"]
ht=df["h_tokens"]

R["defi_activity"]={
 "protocols":[
  {"name":"xExchange","category":"dex","volume_24h_usd":xx["vol"],"active_pairs":xx["pairs"],"transfers_24h":None,
   "tvl_usd":df["xexch_usd"],"tvl_egld":df["xexch_egld"],"tvl_wow_change_pct":xe_egld_pct},
  {"name":"Hatom Lending","category":"lending","volume_24h_usd":0.0,"active_pairs":0,
   "transfers_24h":proto.get("Hatom EGLD MM"),"tvl_usd":df["hatom_lending_usd"],
   "tvl_egld":df["hatom_lending_egld"],"tvl_wow_change_pct":hl_ex_pct},
  {"name":"Hatom Liquid Staking","category":"liquid_staking","volume_24h_usd":0.0,"active_pairs":0,
   "transfers_24h":proto.get("Hatom Liquid Staking"),"tvl_usd":df["hatom_lsd_usd"],
   "tvl_egld":df["hatom_lsd_usd"]/price,"tvl_wow_change_pct":lsd_pct},
  {"name":"XOXNO LSD","category":"liquid_staking","volume_24h_usd":0.0,"active_pairs":0,
   "transfers_24h":proto.get("XOXNO LSD"),"tvl_usd":df["xoxno_usd"],
   "tvl_egld":df["xoxno_usd"]/price,"tvl_wow_change_pct":lsd["XEGLD-e413ed"]["pct"]}],
 "protocol_breakdown":[
  {"protocol":"xExchange","category":"dex","addresses_tracked":16,
   "tvl_usd":df["xexch_usd"],"tvl_egld":df["xexch_egld"],"tvl_wow_change_pct":xe_egld_pct,
   "transfers_24h":None,"volume_24h_usd":xx["vol"],
   "notable_events":f"MEX/WEGLD PAUSED 2026-09-13 16:43 UTC by the router owner, with 191B MEX and 141,281 WEGLD still inside and 172 failed transactions since. Volume {f(bid['prev_dexvol_egld'])} -> {f(bid['dexvol_egld'])} EGLD/day, {bid['wegld_usdc_share']:.1f}% WEGLD/USDC. Like-for-like pool TVL ex the paused pair {bid['pooltvl_egld_ex_mex_wow_pct']:+.1f}% in EGLD. WEGLD contract balances {f(df['xexch_egld'])} EGLD ({xe_egld_pct:+.1f}%).",
   "health_signal":"spiking"},
  {"protocol":"Hatom Lending","category":"lending","addresses_tracked":13,
   "tvl_usd":df["hatom_lending_usd"],"tvl_egld":df["hatom_lending_egld"],"tvl_wow_change_pct":hl_ex_pct,
   "transfers_24h":proto.get("Hatom EGLD MM"),
   "notable_events":f"HEADLINE +{df['hatom_lending_egld_pct']:.0f}% IN EGLD IS A MEX PRICE PRINT. HMEX market cap ${f(ht['HMEX-df6df7']['prev_mcap'])} -> ${f(ht['HMEX-df6df7']['mcap'])} (supply {ht['HMEX-df6df7']['supply_pct']:+.0f}%, priced off a MEX quote that no pool sets). Ex-HMEX, EGLD-denominated TVL {hl_ex_pct:+.2f}% on a {pc:+.2f}% price: inverse rule sign correct on a down-week, response ratio {df['inverse_ratio_ex_hmex']:.2f}. The rule's sign came from USD collateral repricing (HUSDC supply {ht['HUSDC-d80042']['supply_pct']:+.1f}%, HWBTC {ht['HWBTC-49ca31']['supply_pct']:+.1f}%) while EGLD depositors WITHDREW: HEGLD supply {ht['HEGLD-d61095']['supply_pct']:+.2f}% and the EGLD money market contract -89,886 EGLD. HHTM supply {ht['HHTM-e03ba5']['supply_pct']:+.1f}%.",
   "health_signal":"growing"},
  {"protocol":"Hatom Liquid Staking","category":"liquid_staking","addresses_tracked":2,
   "tvl_usd":df["hatom_lsd_usd"],"tvl_egld":df["hatom_lsd_usd"]/price,"tvl_wow_change_pct":lsd_pct,
   "transfers_24h":proto.get("Hatom Liquid Staking"),
   "notable_events":f"SEGLD supply {lsd_pct:+.3f}% to {f(lsd['SEGLD-3ad2d0']['supply'])}, an eighth consecutive flat week, now through a round trip from about $5.17 to $4.14. SWTAO {lsd['SWTAO-356a25']['pct']:+.2f}%. All four dataApi-priced tokens priced on the first pass for a third run.",
   "health_signal":"flat"},
  {"protocol":"Hatom USH","category":"stablecoin","addresses_tracked":4,
   "tvl_usd":df["ush_usd"],"tvl_egld":df["ush_usd"]/price,"tvl_wow_change_pct":lsd["USH-111e09"]["pct"],"transfers_24h":None,
   "notable_events":f"USH minted {lsd['USH-111e09']['pct']:+.2f}% ({f(lsd['USH-111e09']['supply']-lsd['USH-111e09']['prev'])}) to {f(lsd['USH-111e09']['supply'])}, a second consecutive mint but under the 5% threshold. CDP borrowing kept growing slowly into a falling week.",
   "health_signal":"flat"},
  {"protocol":"XOXNO LSD","category":"liquid_staking","addresses_tracked":3,
   "tvl_usd":df["xoxno_usd"],"tvl_egld":df["xoxno_usd"]/price,"tvl_wow_change_pct":lsd["XEGLD-e413ed"]["pct"],
   "transfers_24h":proto.get("XOXNO LSD"),
   "notable_events":f"XEGLD supply {lsd['XEGLD-e413ed']['pct']:+.3f}% to {f(lsd['XEGLD-e413ed']['supply'])}, a sixth week without subscription.",
   "health_signal":"flat"},
  {"protocol":"XOXNO Aggregator","category":"aggregator","addresses_tracked":1,
   "tvl_usd":0.0,"tvl_egld":0.0,"tvl_wow_change_pct":None,"transfers_24h":proto.get("XOXNO Aggregator"),"volume_24h_usd":0.0,
   "notable_events":f"{f(proto.get('XOXNO Aggregator') or 0)} transfers in 24h against {f(prev_tr('XOXNO Aggregator') or 0)} last week ({100*((proto.get('XOXNO Aggregator') or 0)-(prev_tr('XOXNO Aggregator') or 1))/(prev_tr('XOXNO Aggregator') or 1):+.0f}%). The 24h window covers the MEX/WEGLD pause, and routing around a frozen pool is the obvious candidate for the surge.",
   "health_signal":"spiking"},
  {"protocol":"OneDex","category":"aggregator","addresses_tracked":5,
   "tvl_usd":0.0,"tvl_egld":0.0,"tvl_wow_change_pct":None,"transfers_24h":proto.get("OneDex Swap"),"volume_24h_usd":0.0,
   "notable_events":f"{f(proto.get('OneDex Swap') or 0)} transfers in 24h against {f(prev_tr('OneDex') or 0)} ({100*((proto.get('OneDex Swap') or 0)-(prev_tr('OneDex') or 1))/(prev_tr('OneDex') or 1):+.0f}%), the same pause-day surge. OneDex Launchpad still fails bech32 validation (open since run #18).",
   "health_signal":"spiking"},
  {"protocol":"JEXchange","category":"dex","addresses_tracked":10,
   "tvl_usd":0.0,"tvl_egld":0.0,"tvl_wow_change_pct":None,"transfers_24h":proto.get("JEXchange Fees"),"volume_24h_usd":0.0,
   "notable_events":f"ADDRESS TEST RESOLVED AS PREDICTED. The re-derived router did {f(jex7.get('JEXchange Router'))} transfers in 7 days (bar: 1,000), with the four contracts behind it at {', '.join(f(jex7.get(f'JEXchange Router {i}')) for i in range(2,6))}. All five are in the collector's protocol set and known-addresses. Fees contract {f(proto.get('JEXchange Fees') or 0)} transfers in 24h against {f(prev_tr('JEXchange') or 0)}.",
   "health_signal":"growing"},
  {"protocol":"JewelSwap","category":"liquid_staking","addresses_tracked":1,
   "tvl_usd":(es("JWLEGLD-023462") or 0)*price,"tvl_egld":es("JWLEGLD-023462"),
   "tvl_wow_change_pct":ep("JWLEGLD-023462"),"transfers_24h":None,
   "notable_events":f"Delegated stake {f(EM_PREV['JWLEGLD-023462'])} -> {f(es('JWLEGLD-023462'))} EGLD ({ep('JWLEGLD-023462'):+.1f}%), the largest percentage gain of any LSD. JWLEGLD deposit-token supply is flat at {f(em['JWLEGLD-023462']['supply'])} with {em['JWLEGLD-023462']['holders']} holders, so the new stake came from existing deposits being staked, not new money.",
   "health_signal":hs(ep("JWLEGLD-023462"))},
  {"protocol":"SALSA (Staking Agency)","category":"liquid_staking","addresses_tracked":1,
   "tvl_usd":(es("LEGLD-d74da9") or 0)*price,"tvl_egld":es("LEGLD-d74da9"),"tvl_wow_change_pct":ep("LEGLD-d74da9"),"transfers_24h":None,
   "notable_events":f"{f(es('LEGLD-d74da9'))} EGLD delegated ({ep('LEGLD-d74da9'):+.2f}%), {f(em['LEGLD-d74da9']['supply'])} LEGLD, {em['LEGLD-d74da9']['holders']} holders. This week's discovery sweep did NOT surface SALSA, so the stake was measured directly from the contract's /delegation. The sweep is not stable week to week and now needs last week's protocols as seeds.",
   "health_signal":hs(ep("LEGLD-d74da9"))},
  {"protocol":"Dinovox VoxEGLD","category":"liquid_staking","addresses_tracked":1,
   "tvl_usd":(es("VOXEGLD-5872e5") or 0)*price,"tvl_egld":es("VOXEGLD-5872e5"),"tvl_wow_change_pct":ep("VOXEGLD-5872e5"),"transfers_24h":None,
   "notable_events":f"Second week of growth: {f(EM_PREV['VOXEGLD-5872e5'])} -> {f(es('VOXEGLD-5872e5'))} EGLD ({ep('VOXEGLD-5872e5'):+.1f}%), supply {f(em['VOXEGLD-5872e5']['supply'])}, holders 113 -> {em['VOXEGLD-5872e5']['holders']}. Dinovox also appears this week as the new identity of the provider contract formerly named kevinlallement.",
   "health_signal":hs(ep("VOXEGLD-5872e5"))},
  {"protocol":"VestaX Finance","category":"liquid_staking","addresses_tracked":1,
   "tvl_usd":(es("VEGLD-2b9319") or 0)*price,"tvl_egld":es("VEGLD-2b9319"),"tvl_wow_change_pct":ep("VEGLD-2b9319"),"transfers_24h":None,
   "notable_events":f"{f(es('VEGLD-2b9319'))} EGLD, unchanged. Also missed by this week's sweep and measured directly.",
   "health_signal":"flat"}],
 "sc_deployments":[],
 "analysis":(
  f"THE WEEK'S DEFI STORY IS A FROZEN POOL AND WHAT ROUTED AROUND IT. The MEX/WEGLD pair has been paused since Saturday afternoon, and the aggregators lit up over the 24 hours that include the pause: XOXNO {f(proto.get('XOXNO Aggregator'))} transfers against {f(prev_tr('XOXNO Aggregator'))}, OneDex {f(proto.get('OneDex Swap'))} against {f(prev_tr('OneDex'))}, the JEXchange fees contract {f(proto.get('JEXchange Fees'))} against {f(prev_tr('JEXchange'))}. "
  f"Hatom's MEX market took the deposits: HMEX supply {ht['HMEX-df6df7']['supply_pct']:+.0f}%. That HMEX line is also a trap for the TVL figure. HMEX market cap went from ${f(ht['HMEX-df6df7']['prev_mcap'])} to ${f(ht['HMEX-df6df7']['mcap'])}, priced off a MEX quote no on-chain pool sets, which lifts Hatom Lending's headline EGLD TVL {df['hatom_lending_egld_pct']:+.0f}%. Excluding HMEX the move is {hl_ex_pct:+.2f}%, and that is the figure in the breakdown.\n\n"
  f"THE INVERSE RULE'S SIGN WAS RIGHT, FOR A MECHANICAL REASON. On a {pc:+.2f}% week, ex-HMEX lending TVL in EGLD rose {hl_ex_pct:+.2f}% - correct sign, response ratio {df['inverse_ratio_ex_hmex']:.2f}. "
  f"The per-market supplies show where the sign comes from. EGLD depositors withdrew: HEGLD supply {ht['HEGLD-d61095']['supply_pct']:+.2f}%, and the EGLD money market contract lost 89,886 EGLD. The markets that grew are dollar and BTC collateral (HUSDC {ht['HUSDC-d80042']['supply_pct']:+.1f}%, HUSDT {ht['HUSDT-6f0914']['supply_pct']:+.1f}%, HWETH {ht['HWETH-b3d17e']['supply_pct']:+.1f}%), and those rise in EGLD terms whenever EGLD falls. "
  f"Part of the rule's two-sided record is therefore just the divisor. The EGLD-native leg, HEGLD supply, is the behavioural test, and this week it moved WITH the price: depositors left as EGLD fell. The rule is kept, with its behavioural reading limited to the HEGLD leg from now on.\n\n"
  f"Liquid staking stayed still where it is large and grew where it is small. SEGLD {lsd_pct:+.3f}% (eighth flat week), XEGLD {lsd['XEGLD-e413ed']['pct']:+.3f}%, while JewelSwap's delegated stake rose {ep('JWLEGLD-023462'):+.0f}% and VoxEGLD {ep('VOXEGLD-5872e5'):+.1f}% with holders at {em['VOXEGLD-5872e5']['holders']}. Together those two added about 630 EGLD, which changes no aggregate. USH minted {lsd['USH-111e09']['pct']:+.2f}%.\n\n"
  f"SWEEP CAVEAT: the liquid-staking discovery sweep returned four protocols instead of six. SALSA (6,420 EGLD) and VestaX (1,121) still stake and were measured directly, but their receipt tokens did not appear in this week's candidate list. A discovery method that can lose a known protocol cannot be run from scratch each week; it has to carry last week's finds forward as seeds."),
}
json.dump(R,open("/tmp/run25w/part2.json","w"),indent=1,default=str)
print("part2 ok:",list(R.keys()))
