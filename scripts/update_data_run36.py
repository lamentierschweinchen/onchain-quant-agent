#!/usr/bin/env python3
"""Run #36: refresh previous.json, known-addresses.json, methodology Evolution Log, and append the learnings entry."""
import json, copy
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"; RD="2026-11-09"
S="/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/174a0ac3-37e6-4a71-9596-a35c3cbb3939/scratchpad"
c=json.load(open(f"{REPO}/data/collected/{RD}.json")); R=json.load(open(f"{REPO}/reports/{RD}.json"))
pv=json.load(open(f"{REPO}/data/previous.json")); kn=json.load(open(f"{REPO}/data/known-addresses.json")); L=json.load(open(f"{REPO}/data/learnings.json"))
D=json.load(open(f"{S}/digest36.json")); B=json.load(open(f"{S}/baselines36.json"))
LM={}
for s,e in kn.items():
    if isinstance(e,dict):
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"): LM[a]=m.get("name")
eco=c["economics"]; st=c["stats"]; E=1e18
P=copy.deepcopy(pv); P.pop("_run35_note",None)
P["snapshot_date"]=RD
P["economics"]={"egld_price_usd":eco["price"],"market_cap_usd":eco["marketCap"],"total_supply":eco["totalSupply"],"circulating_supply":eco["circulatingSupply"],
  "staked_egld":eco["staked"],"staked_ratio":eco["staked"]/eco["circulatingSupply"],"staking_apr":eco["apr"],"base_apr":eco["baseApr"],"topup_apr":eco["topUpApr"],
  "token_market_cap_usd":eco["tokenMarketCap"],"btc_price_usd":c["btc_eth"]["bitcoin"]["usd"],"eth_price_usd":c["btc_eth"]["ethereum"]["usd"]}
P["activity"]={"total_accounts":st["accounts"],"total_transactions":st["transactions"],"epoch":st["epoch"],"blocks":st["blocks"],"shards":3}
P["top_accounts"]=[{"address":x["address"],"balance_egld":int(x["balance"])/E,"label":LM.get(x["address"],"Unknown")} for x in c["top_accounts"][:100]]
P["top_tokens_by_holders"]=[{"identifier":t["identifier"],"name":t.get("name"),"holders":t["accounts"],"price_usd":t.get("price"),"supply_raw":t.get("supply"),"decimals":t.get("decimals")} for t in c["tokens_holders"][:25]]
P["top_tokens_by_volume"]=[{"identifier":t["identifier"],"name":t.get("name"),"transactions":t.get("transactions"),"holders":t.get("accounts")} for t in c["tokens_txs"][:25]]
P["newly_issued_tokens"]=R["token_activity"]["newly_issued"]
P["staking_providers"]=[{"provider":p.get("identity") or p["provider"],"name":p.get("identity") or p["provider"],"address":p["provider"],"locked_egld":float(p.get("locked",0) or 0)/E,
  "num_delegators":p.get("numUsers"),"apr":p.get("apr"),"fee":p.get("serviceFee"),"num_nodes":p.get("numNodes")} for p in c["providers"]]
P["staking_concentration"]={"hhi":D["hhi"],"top_5_share_pct":D["top5"],"top_10_share_pct":D["top10"],"total_locked_egld":R["staking_intelligence"]["summary"]["total_delegated_egld"]}
P["exchange_balances"]={k:pv["exchange_balances"][k]+D["chg"][k] for k in pv["exchange_balances"]}
P["defi_tvl"]=D["TVL"]
P["lsd_supply"]={t:float(c["tvl_tokens"][t].get("supply") or 0) for t in ["SEGLD-3ad2d0","XEGLD-e413ed","SWTAO-356a25","USH-111e09"]}
P["stablecoin_supply"]={"USDC-c76f1f":7119153.0,"USDT-f8c08c":381086.0}
x=R["token_activity"]["xexchange"]
P["xexchange"]={"volume_24h_usd":D["vol24"],"total_pairs":x["total_pairs"],"mex_price_usd":x["mex_price_usd"],"mex_market_cap_usd":x["mex_market_cap_usd"],
  "mex_price_source":"xExchange /mex/economics","volume_status":"run #36 24h snapshot (7.05-day window)","pool_tvl_usd":D["tvl"],"turnover_ratio_pct":x["turnover_ratio_pct"],
  "volume_24h_egld":D["vol24"]/D["price"],"pool_tvl_egld":D["tvl"]/D["price"]}
P["binance_rail"]={"hot_wallet":"erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets","last_tx_utc":"2026-10-29 23:05:39","deposits_7d":0,"withdrawals_7d":0,"state":"dark"}
wa=[w for w in pv["watch_addresses"]]
for w in wa:
    w["weeks_tracked"]=w.get("weeks_tracked",0)+1
    if w["address"] in c["accounts"]: w["balance_egld"]=int(c["accounts"][w["address"]]["info"]["balance"])/E
wa.insert(0,{"address":"erd15ku2r2j6smlwumftumlpw0mfpqxy32wyt4ewxzyhs3ugsjee8stq2xh84e","label":"KuCoin round-trip whale - deposited 145,443 Jul 19, withdrew 168,359 Oct 30/Nov 3, holds; kucoin-whale-holds","balance_egld":168357.92,"weeks_tracked":1,"first_seen":RD})
wa.insert(1,{"address":"erd1drc22z7hz90sqmugmtwu6pe8kyncg67gv7xulcu4mq92ygyxpacq72xywa","label":"OTC operator vault - received 112,634 from Unknown Whale I Nov 5, returns daily clips","balance_egld":107151.37,"weeks_tracked":1,"first_seen":RD})
P["watch_addresses"]=wa
P["_run36_note"]="defi_tvl and lsd_supply restated in run #36 from token market caps; otc series not refreshed."
json.dump(P,open(f"{REPO}/data/previous.json","w"))

# known addresses
kn["unlabeled_whales"]["erd15ku2r2j6smlwumftumlpw0mfpqxy32wyt4ewxzyhs3ugsjee8stq2xh84e"]={"name":"KuCoin round-trip whale (erd15ku2r2j6)","category":"other","subcategory":"cex_withdrawal",
  "notes":"Deposited 145,443 EGLD to KuCoin 2026-07-19; withdrew 136,359 (Oct 30) and 32,000 (Nov 3); holds 168,358. Targeted by poisoning lookalike erd1tyfnsaztln.","first_seen":RD,"discovered_run":36}
kn["unlabeled_whales"]["erd1drc22z7hz90sqmugmtwu6pe8kyncg67gv7xulcu4mq92ygyxpacq72xywa"]={"name":"OTC operator vault (erd1drc22z7h)","category":"other","subcategory":"otc",
  "notes":"Received 112,634 EGLD from Unknown Whale I (OTC operator inventory) 2026-11-05; sends 1,500-3,200 EGLD clips back to Whale I twice daily.","first_seen":RD,"discovered_run":36}
json.dump(kn,open(f"{REPO}/data/known-addresses.json","w"),indent=2)

# methodology
row=("| 36 | 2026-11-09 | **BINANCE'S RAIL WENT DARK; THE KUCOIN BACKLOG WAS ONE WALLET.** 7.05-day window. EGLD -11.5% to $3.01 vs BTC -3.4% (-8.1pp). "
 "(1) Binance.com: 0 deposits, 0 withdrawals; hot wallet silent since its Oct 29 23:05 sweep of 309,906 to custody (3 EGLD left); 15 recent depositors also silent, so paused rail, not a new address. Spot trading continues. "
 "(2) Tracked exchanges -86,702 (KuCoin -40,396, Bybit -16,734, MEXC -15,014 withdraw-only, Gate.io -8,015) with price down: bottom-confirms INCONCLUSIVE. "
 "(3) KuCoin withdrawals traced one hop: erd15ku2r2j6 took 168,359 (deposited 145,443 in July) and holds; ex that, daily outflow fell under 400 EGLD. kucoin-backlog-decay INCONCLUSIVE (middle band; premise wrong). "
 "(4) Unknown Whale I moved 112,634 to an internal vault. (5) TVL restated from token market caps (two-week basis): Hatom Lending $5.86M, Hatom LSD $3.45M. "
 "Rules: read a zero-flow venue's hot-wallet last-tx time before calling it balanced; decompose venue outflow by withdrawer before calling it a backlog; filter zero-value poisoning dust. "
 "Tests: 2 resolved (both inconclusive), 2 registered (binance-rail-reopens, kucoin-whale-holds). 5/6 prior action items completed. |")
m=open(f"{REPO}/data/methodology.md").read().rstrip("\n")+"\n"+row+"\n"
open(f"{REPO}/data/methodology.md","w").write(m)

# learnings
prev=L["runs"][-1]; rb=copy.deepcopy(prev["running_baselines"])
def app(k,v):
    if isinstance(rb.get(k),list): rb[k].append(v)
for k in ("egld_price_usd","dex_volume_24h_usd","staked_egld","mex_price_usd","total_delegators","staked_ratio","exchange_net_flow_egld","usdt_supply","usdc_supply","korea_premium_pct"):
    app(k,B[k])
app("dex_volume_24h_egld",round(B["dex_volume_24h_egld"])); app("binance_staking_custody_egld",4284611.453933773)
app("dex_turnover_ratio_pct",round(R["token_activity"]["xexchange"]["turnover_ratio_pct"],3))
app("reward_compound_pct",round(R["staking_intelligence"]["reward_behavior"]["compound_pct_at_function_level"],2))
app("delegation_total_locked_egld",round(R["staking_intelligence"]["summary"]["total_delegated_egld"]))
app("unbonding_queue_undelegated_egld_7d",round(c["undelegated_this_week_total_egld"]))
app("withdraw_egld_returned_7d",72314)
app("pre_committed_tests_resolved",2); app("pre_committed_test_hit_rate_pct",0.0)
app("pre_committed_tests_open",sum(1 for t in R["pre_committed_tests"] if t["status"]=="open"))
rb["binance_native_rail_egld_7d"]=[0.0]
ml=R["meta_learning"]
entry={"date":RD,"run_number":36,
 "data_quality":{"endpoints_that_worked":ml.get("endpoints_that_worked",[]),"endpoints_that_failed":ml["endpoints_that_failed"],"api_quirks_discovered":ml["api_quirks"]},
 "analysis_insights":{"what_worked":["Trace pass per-venue daily rails and one-hop KuCoin withdrawal destinations","Checking the Binance hot wallet's last transaction instead of trusting a zero balance change","Restating TVL from token market caps"],
   "what_needs_improvement":ml["data_gaps"],
   "surprising_findings":["Binance's native EGLD rail has been dark since Oct 29 23:05 UTC.","KuCoin's three-week 'backlog' outflow was mostly one wallet's 168K round trip.","Address-poisoning lookalikes now target fresh large holders (KuCoin withdrawer, OTC vault).","An 86,702 EGLD exchange outflow coincided with EGLD -8.1pp vs BTC."]},
 "methodology_changes":ml["methodology_changes"],
 "new_addresses_discovered":ml["new_addresses_discovered_detail"],
 "action_items_completed":ml["action_items_completed_detail"],
 "running_baselines":rb,
 "dashboard_feature_suggestions":ml["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":ml["dashboard_suggestions_followup"],
 "self_assessment":{"most_valuable_insight":ml["most_valuable_insight"],"recommendations_completed":"5 of 6","next_week_2x_better":ml["self_assessment"]["what_would_make_it_2x_better"]},
 "recommendations_for_next_run":ml["recommendations_for_next_run"]}
L["runs"].append(entry)
json.dump(L,open(f"{REPO}/data/learnings.json","w"),indent=1)
print("updated previous/known/methodology/learnings; runs:",len(L["runs"]))
