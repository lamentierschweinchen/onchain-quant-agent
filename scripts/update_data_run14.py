#!/usr/bin/env python3
import json
from datetime import datetime, timezone
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D=json.load(open("/tmp/run14/collected.json"))
R=json.load(open(f"{REPO}/reports/2026-06-29.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
learn=json.load(open(f"{REPO}/data/learnings.json"))

label_map,cat_map={},{}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"):
                label_map[a]=m.get("name","Unknown"); cat_map[a]=m.get("category","unknown")
def lab(a): return label_map.get(a,"Unknown")
acc=D["accounts"]
def b(a):
    x=acc.get(a)
    return int(x["info"]["balance"])/1e18 if x and isinstance(x.get("info"),dict) and "balance" in x["info"] else None
econ=D["economics"]; st=D["stats"]; be=D["btc_eth"]; meco=D["mex_economics"]

# ---- new previous.json ----
ta=D["top_accounts"]
top_accounts=[{"address":x["address"],"balance_egld":int(x["balance"])/1e18,"label":lab(x["address"])} for x in ta[:60]]
th=D["tokens_holders"][:25]
top_tokens_by_holders=[{"identifier":t["identifier"],"name":t.get("name"),"holders":t["accounts"],
    "price_usd":t.get("price"),"supply_raw":t.get("supply"),"decimals":t.get("decimals")} for t in th]
tv=D["tokens_txs"][:25]
top_tokens_by_volume=[{"identifier":t["identifier"],"name":t.get("name"),"transactions":t.get("transactions"),"holders":t.get("accounts")} for t in tv]
provs=[p for p in D["providers"] if p.get("locked") and float(p["locked"])>0]
for p in provs: p["_lk"]=float(p["locked"])/1e18
provs.sort(key=lambda p:-p["_lk"])
staking_providers=[{"provider":p.get("identity") or p["provider"],"name":p.get("identity") or p["provider"],
    "locked_egld":p["_lk"],"num_delegators":p.get("numUsers"),"apr":p.get("apr"),
    "fee":p.get("serviceFee"),"num_nodes":p.get("numNodes")} for p in provs]
binance_com_addrs = [
    "erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets",
    "erd1ylwuswz9zuk4acuq4aa6d0x9ys293yhlpwg6vpuwntndyej4u44q896zlz",
    "erd1v4ms58e22zjcp08suzqgm9ajmumwxcy4hfkdc23gvynnegjdflmsj6gmaq"
]
binance_com=sum((b(a) or 0) for a in binance_com_addrs)
cb=sum((b(a) or 0) for a in ["erd16jruked88jgtsar78ej85hjp3qsd9jkjcw4swsn7k0teqh3wgcqqgyrupq","erd1m9qn6gvercs6ksvtn924w4y7z9ppglyfugpu34al26t9u4mvzvqqlq9dc3","erd1eae23a530qymlpvfrudzsge5wgl003wl92saax74cew7j549eqqq3jklut"])
exchange_balances={
 "Binance Staking":b("erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"),
 "Binance.com":binance_com,
 "UPbit":b("erd1fcxu3f0hlxyvnp7zvuqmf34zf5w782tst6vuqhm4dwq4ayjspdaqce0q49"),
 "Bybit":b("erd1vj3efd5czwearu0gr3vjct8ef53lvtl7vs42vts2kh2qn3cucrnsj7ymqx"),
 "Crypto.com":(b("erd1hzccjg25yqaqnr732x2ka7pj5glx72pfqzf05jj9hxqn3lxkramq5zu8h4") or 0)+(b("erd1qr9av6ar4ymr05xj93jzdxyezdrp6r4hz6u0scz4dtzvv7kmlldse7zktc") or 0),
 "MEXC":b("erd1ezp86jwmcp4fmmu2mfqz0438py392z5wp6kzuqsjldgd68nwt89qshfs0y"),
 "Bitget":b("erd1w547kw69kpd60vlpr9pe0pn9nnqeljrcaz73znenjpgt0h3qlqqqm3szxj"),
 "Coinbase":cb,
 "Gate.io":b("erd1p4vy5n9mlkdys7xczegj398xtyvw2nawz00nnfh4yr7fpjh297cqtsu7lw"),
 "KuCoin":b("erd1ty4pvmjtl3mnsjvnsxgcpedd08fsn83f05tu0v5j23wnfce9p86snlkdyy"),
 "Bitfinex":b("erd1a56dkgcpwwx6grmcvw9w5vpf9zeq53w3w7n6dmxcpxjry3l7uh2s3h9dtr"),
 "Tokero":b("erd1ra67nmtcuagw2y73sca7fzgh66yemtslvshfz77z9tep9qx5swvsv23lhf")}
pb=R["defi_activity"]["protocol_breakdown"]
def find(n): return next(p for p in pb if p["protocol"]==n)
defi_tvl={"Hatom Lending":find("Hatom Lending")["tvl_usd"],
 "Hatom Liquid Staking":find("Hatom Liquid Staking")["tvl_usd"],
 "Hatom USH":find("Hatom USH")["tvl_usd"],
 "XOXNO LSD":find("XOXNO LSD")["tvl_usd"],
 "xExchange (USD)":find("xExchange")["tvl_usd"]}
new_prev={
 "snapshot_date":"2026-06-29",
 "economics":{"egld_price_usd":econ["price"],"market_cap_usd":econ["marketCap"],"total_supply":econ["totalSupply"],
   "circulating_supply":econ["circulatingSupply"],"staked_egld":econ["staked"],"staked_ratio":econ["staked"]/econ["circulatingSupply"],
   "staking_apr":econ["apr"],"base_apr":econ["baseApr"],"topup_apr":econ["topUpApr"],"token_market_cap_usd":econ["tokenMarketCap"],
   "btc_price_usd":be["bitcoin"]["usd"],"eth_price_usd":be["ethereum"]["usd"]},
 "activity":{"total_accounts":st["accounts"],"total_transactions":st["transactions"],"epoch":st["epoch"],"blocks":st["blocks"],"shards":st["shards"]},
 "top_accounts":top_accounts,
 "top_tokens_by_holders":top_tokens_by_holders,
 "top_tokens_by_volume":top_tokens_by_volume,
 "newly_issued_tokens":[{"identifier":t["identifier"],"name":t["name"],"ticker":t["ticker"],"timestamp":t["timestamp"],"accounts":t["accounts"],"transactions":t["transactions"]} for t in D.get("newly_issued",[])],
 "staking_providers":staking_providers,
 "staking_concentration":{"hhi":R["staking_intelligence"]["concentration"]["hhi"],
   "top_5_share_pct":R["staking_intelligence"]["concentration"]["top_5_share_pct"],
   "top_10_share_pct":R["staking_intelligence"]["concentration"]["top_10_share_pct"],
   "total_locked_egld":R["staking_intelligence"]["summary"]["total_delegated_egld"]},
 "exchange_balances":exchange_balances,
 "defi_tvl":defi_tvl,
 "xexchange":{"volume_24h_usd":R["token_activity"]["xexchange"]["total_volume_24h_usd"],"total_pairs":meco["marketPairs"],
   "mex_price_usd":meco["price"],"mex_market_cap_usd":meco["marketCap"]},
 # store LSD/stablecoin supply for next run's supply-based WoW (methodology change this run)
 "lsd_supply":{tid:D["tvl_tokens"].get(tid,{}).get("supply") for tid in ["SEGLD-3ad2d0","XEGLD-e413ed","SWTAO-356a25","USH-111e09"]},
 "watch_addresses":[
   {"address":"erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p","label":"Binance Staking custody (STALLED 4th consecutive week at 3.51M; 7 weeks parked)","balance_egld":b("erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"),"weeks_tracked":8,"first_seen":"2026-05-11"},
   {"address":"erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5","label":"UPbit OTC Desk (DISTRIBUTING+LOADING: +18K balance, 114K outbound 7d)","balance_egld":b("erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"),"weeks_tracked":14,"first_seen":"2026-04-02"},
   {"address":"erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r","label":"OTC Distribution Wallet (DISTRIBUTING+LOADING: +17K balance, 81K outbound 7d)","balance_egld":b("erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"),"weeks_tracked":12,"first_seen":"2026-04-13"},
   {"address":"erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh","label":"OTC source erd17l22 (+16K to 317K; actively feeding pipeline)","balance_egld":b("erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh"),"weeks_tracked":8,"first_seen":"2026-05-11"},
   {"address":"erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp","label":"OTC source funder (Binance.com -> erd17l22 pass-through)","balance_egld":b("erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp") or 0,"weeks_tracked":6,"first_seen":"2026-05-25"},
   {"address":"erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw","label":"Unknown Mega Whale (ACTIVATED +11K, crossed 1M to 1,010,011; Apr-18 OTC-deal counterparty)","balance_egld":b("erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"),"weeks_tracked":11,"first_seen":"2026-04-20"},
   {"address":"erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets","label":"Binance.com hot (canonical); Binance entity -158K hot-wallet drawdown this week","balance_egld":b("erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets"),"weeks_tracked":3,"first_seen":"2026-06-15"},
   {"address":"erd16jruked88jgtsar78ej85hjp3qsd9jkjcw4swsn7k0teqh3wgcqqgyrupq","label":"Coinbase (3-week inflow streak BROKE to -1.6K this week)","balance_egld":b("erd16jruked88jgtsar78ej85hjp3qsd9jkjcw4swsn7k0teqh3wgcqqgyrupq"),"weeks_tracked":5,"first_seen":"2026-06-01"},
   {"address":"erd1qqqqqqqqqqqqqpgq6uzdzy54wnesfnlaycxwymrn9texlnmyah0ssrfvk6","label":"XOXNO LSD contract (XEGLD supply -29% this week; trace redemptions next run)","balance_egld":b("erd1qqqqqqqqqqqqqpgq6uzdzy54wnesfnlaycxwymrn9texlnmyah0ssrfvk6") or 0,"weeks_tracked":1,"first_seen":"2026-06-29"}]}
json.dump(new_prev,open(f"{REPO}/data/previous.json","w"),indent=2)
print("WROTE previous.json; top_accounts",len(top_accounts),"providers",len(staking_providers))

# ---- learnings.json append ----
def roll(arr,val,n=8):
    a=arr+[val]
    return a[-n:] if len(a)>n else a
rbprev=learn["runs"][-1]["running_baselines"]
sr_cur=econ["staked"]/econ["circulatingSupply"]
# desk-balance delta convention (series tracks net loading/unloading, not throughput):
# UPbit OTC +18,040 + OTC Distribution +17,361 = +35,401 (HEAVY LOADING while distributing 195K)
otc_throughput_13 = 35401
new_baselines={
 "egld_price_usd":roll(rbprev["egld_price_usd"],econ["price"]),
 "dex_volume_24h_usd":roll(rbprev["dex_volume_24h_usd"],R["token_activity"]["xexchange"]["total_volume_24h_usd"]),
 "staked_egld":roll(rbprev["staked_egld"],econ["staked"]),
 "mex_price_usd":roll(rbprev["mex_price_usd"],meco["price"]),
 "total_delegators":roll(rbprev["total_delegators"],R["staking_intelligence"]["churn"]["total_delegators_current"]),
 "staked_ratio":roll(rbprev["staked_ratio"],sr_cur),
 "exchange_net_flow_egld":(rbprev.get("exchange_net_flow_egld",[])+[R["whale_intelligence"]["exchange_flows"]["net_change_egld"]])[-8:],
 "otc_pipeline_throughput_egld_7d":(rbprev.get("otc_pipeline_throughput_egld_7d",[])+[otc_throughput_13])[-8:],
 "binance_staking_custody_egld":((rbprev.get("binance_staking_custody_egld") or [])+[exchange_balances["Binance Staking"]])[-8:],
 "reward_compound_pct":(rbprev.get("reward_compound_pct",[61.9,59.14])+[round(R["staking_intelligence"].get("reward_behavior",{}).get("compound_pct_at_function_level",55.31),2)])[-8:]}
entry={
 "date":"2026-06-29","run_number":14,
 "data_quality":{
   "endpoints_that_worked":R["meta_learning"]["endpoints_that_worked"],
   "endpoints_that_failed":R["meta_learning"]["endpoints_that_failed"],
   "api_quirks_discovered":R["meta_learning"]["api_quirks"],
   "data_gaps":R["meta_learning"]["data_gaps"]},
 "analysis_insights":{
   "what_worked":[
     "Supply-based LSD reporting (run #13 methodology) paid off in its first stress test: it surfaced the XEGLD -29% supply collapse cleanly, which an mcap-only view would have blended into the -10.5% EGLD price drop and missed.",
     "dataApi re-fetch guard (added this run) recovered 3 of 4 LSD tokens (SEGLD/XEGLD/USH) on the first pass; only SWTAO stayed null (feed-specific outage), handled via carried-price fallback.",
     "Degenerate-z-score guard correctly kept the +1 delegator move from being flagged; confirmed the capitulation was a one-shot as predicted.",
     "Whale-tier boundary-crossing check caught the erd18mv2z6r2 1M crossing that would otherwise have produced a phantom +997K mega-accumulation narrative.",
     "Reading exchange flow JOINTLY with OTC throughput prevented a single-metric misread: the -222K exchange outflow looked bullish alone but coincided with a record 195K OTC distribution."],
   "what_needs_improvement":[
     "SWTAO dataApi feed can stay null for an ENTIRE run (not just under load); WTAO was also null so the accumulator-ratio fallback failed. Need a more robust TAO-price source or a multi-source SWTAO price.",
     "Binance -158K hot-wallet outflow is untraceable via standard txs; need an internal-transfer / SC-result data source to attribute large exchange moves.",
     "XEGLD -29% redemption: could not trace the redeemer(s)/destination within this run's budget - needs a dedicated XOXNO LSD contract outflow query next run.",
     "Newly-issued token scan empty a 3rd week - still no way to distinguish a quiet week from method failure."],
   "surprising_findings":[
     "XOXNO LSD (XEGLD) supply COLLAPSED -29% in one week (~94K redeemed) - the largest single-protocol LSD supply move in tracking; XOXNO-specific (SEGLD flat).",
     "On-chain conviction DIVERGED from price: despite the -10.5% dump, protocol staked ROSE +81K (buy-the-dip), the delegator base held flat 2nd week, and the yield-chase cohort reignited hard (ninjastaking +11.6K).",
     "Net exchange flow REVERSED to -222K outflow after 3 inflow weeks, but distribution didn't stop - it shifted to the OTC channel (record 195K throughput).",
     "Reward compound rate ROSE to 58.54% (from 55.31%), reversing the 3-week slide - consistent with the buy-the-dip staking conviction.",
     "EMRS-6e4067 is NOT a thin low-float listing (last run's assumption was wrong): it has 10,331 holders and 151,107 txs - genuine traction.",
     "The price drop was a BROAD-MARKET beta move (BTC -6.4%, ETH -9.5% WoW), unlike recent weeks' EGLD-specific decoupling."]},
 "methodology_changes":R["meta_learning"]["methodology_changes"],
 "new_addresses_discovered":["erd1lgdltequh76... (sender of +11,040 EGLD to Mega Whale erd18mv2z6r2 - source of its reactivation; unlabeled, flag for tracing)"],
 "action_items_completed":[
   "DONE: $2.85 floor check - BROKE. EGLD -10.5% to $2.55 in a broad-market dump; downtrend extended (but beta-driven, not EGLD-specific).",
   "DONE: Binance Staking custody 4th-week stall - CONFIRMED unchanged at 3.51M (7 weeks parked).",
   "DONE: Delegator base stability follow-up - CONFIRMED. Flat 2nd week (+1) at 174,407; capitulation was a one-shot.",
   "DONE: Exchange inflow 4th-week check - REVERSED to -222K outflow; the 3-week inflow streak broke (but distribution shifted to OTC).",
   "DONE: dataApi re-fetch guard - IMPLEMENTED in collect_run14.py and verified end-to-end; recovered 3 of 4 tokens (SWTAO feed-out, handled).",
   "DONE: pi-staking isolated-entry follow-up - NOT a one-off; pi-staking +7.1K / +24 users (14->38). Yield-chase reignited broadly.",
   "DONE: Stablecoin contraction follow-up - CONFIRMED 2nd week, accelerating (USDC -1.3%, USDT -3.7%); sustained dollar-liquidity flight.",
   "DONE: EMRS-6e4067 traction check - it IS a genuine large-cap (10,331 holders, 151,107 txs), correcting last run's thin-float assumption.",
   "DEFERRED/NEW: OTC distribution wave watch - the wave ARRIVED (195K throughput) AND desks reloaded +35K; rolled into next run's trace-the-throughput-onto-exchanges item."],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":R["meta_learning"]["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":R["meta_learning"]["dashboard_suggestions_followup"],
 "self_assessment":{
   "most_valuable_insight":R["meta_learning"]["most_valuable_insight"],
   "actions_completed_count":8,"actions_attempted_count":9,
   "what_would_2x_next_week":"Trace the XEGLD -29% supply collapse to its redeemer(s) and destination - this is the week's biggest open question and would distinguish a bullish migration to native delegation (consistent with the +81K staked rise) from a bearish exit. Second: build the LSD circulating-supply timeline (supply, not mcap), which would have made the XEGLD collapse unmissable and is now re-listed at high priority for a 3rd run; plus the exchange-flow-vs-OTC dual-axis chart, since this run showed reading exchange flow alone misleads."},
 "recommendations_for_next_run":R["meta_learning"]["recommendations_for_next_run"]}
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #14; total runs",len(learn["runs"]))
print("baselines price",new_baselines["egld_price_usd"])
print("baselines compound",new_baselines["reward_compound_pct"])
print("baselines binance_custody",new_baselines.get("binance_staking_custody_egld"))
