#!/usr/bin/env python3
import json
from datetime import datetime, timezone
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D=json.load(open("/tmp/run10/collected.json"))
R=json.load(open(f"{REPO}/reports/2026-06-01.json"))
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
binance_com=sum((b(a) or 0) for a in ["erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets","erd1ylwuswz9zuk4acuq4aa6d0x9ys293yhlpwg6vpuwntndyej4u44q896zlz","erd1v4ms58e22zjcp08suzqgm9ajmumwxcy4hfkdc23gvynnegjdflmsj6gmaq"])
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
 "snapshot_date":"2026-06-01",
 "economics":{"egld_price_usd":econ["price"],"market_cap_usd":econ["marketCap"],"total_supply":econ["totalSupply"],
   "circulating_supply":econ["circulatingSupply"],"staked_egld":econ["staked"],"staked_ratio":econ["staked"]/econ["circulatingSupply"],
   "staking_apr":econ["apr"],"base_apr":econ["baseApr"],"topup_apr":econ["topUpApr"],"token_market_cap_usd":econ["tokenMarketCap"],
   "btc_price_usd":be["bitcoin"]["usd"],"eth_price_usd":be["ethereum"]["usd"]},
 "activity":{"total_accounts":st["accounts"],"total_transactions":st["transactions"],"epoch":st["epoch"],"blocks":st["blocks"],"shards":st["shards"]},
 "top_accounts":top_accounts,
 "top_tokens_by_holders":top_tokens_by_holders,
 "top_tokens_by_volume":top_tokens_by_volume,
 "newly_issued_tokens":[],
 "staking_providers":staking_providers,
 "staking_concentration":{"hhi":R["staking_intelligence"]["concentration"]["hhi"],
   "top_5_share_pct":R["staking_intelligence"]["concentration"]["top_5_share_pct"],
   "top_10_share_pct":R["staking_intelligence"]["concentration"]["top_10_share_pct"],
   "total_locked_egld":R["staking_intelligence"]["summary"]["total_delegated_egld"]},
 "exchange_balances":exchange_balances,
 "defi_tvl":defi_tvl,
 "xexchange":{"volume_24h_usd":R["token_activity"]["xexchange"]["total_volume_24h_usd"],"total_pairs":meco["marketPairs"],
   "mex_price_usd":meco["price"],"mex_market_cap_usd":meco["marketCap"]},
 "watch_addresses":[
   {"address":"erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p","label":"Binance Staking custody (+135K this week, now 3.51M; +402K over 3 weeks; UNDEPLOYED)","balance_egld":b("erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"),"weeks_tracked":4,"first_seen":"2026-05-11"},
   {"address":"erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh","label":"OTC source (small distribution wave: +6K through funder)","balance_egld":b("erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh"),"weeks_tracked":4,"first_seen":"2026-05-11"},
   {"address":"erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp","label":"OTC source funder (100% Binance.com -> erd17l22 pass-through; 6,970 EGLD 7d)","balance_egld":0.0,"weeks_tracked":2,"first_seen":"2026-05-25"},
   {"address":"erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw","label":"Unknown Mega Whale (993K, flat)","balance_egld":b("erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"),"weeks_tracked":7,"first_seen":"2026-04-20"},
   {"address":"erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5","label":"UPbit OTC Desk (LOADING phase, +56% WoW)","balance_egld":b("erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"),"weeks_tracked":10,"first_seen":"2026-04-02"},
   {"address":"erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r","label":"OTC Distribution Wallet (LOADING phase, +54% WoW)","balance_egld":b("erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"),"weeks_tracked":8,"first_seen":"2026-04-13"},
   {"address":"erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets","label":"Binance.com hot (-170K this week -> staking custody +135K)","balance_egld":b("erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets"),"weeks_tracked":3,"first_seen":"2026-05-18"}]}
json.dump(new_prev,open(f"{REPO}/data/previous.json","w"),indent=2)
print("WROTE previous.json; top_accounts",len(top_accounts),"providers",len(staking_providers))

# ---- learnings.json append ----
def roll(arr,val,n=7):
    a=arr+[val]
    return a[-n:] if len(a)>n else a
rbprev=learn["runs"][-1]["running_baselines"]
sr_cur=econ["staked"]/econ["circulatingSupply"]
otc_throughput_10 = 6970 + 32605  # funder pass-through + OTC desk net inflow
new_baselines={
 "egld_price_usd":roll(rbprev["egld_price_usd"],econ["price"]),
 "dex_volume_24h_usd":roll(rbprev["dex_volume_24h_usd"],R["token_activity"]["xexchange"]["total_volume_24h_usd"]),
 "staked_egld":roll(rbprev["staked_egld"],econ["staked"]),
 "mex_price_usd":(rbprev["mex_price_usd"]+[meco["price"]])[-8:],
 "total_delegators":(rbprev["total_delegators"]+[R["staking_intelligence"]["churn"]["total_delegators_current"]])[-8:],
 "staked_ratio":(rbprev["staked_ratio"]+[sr_cur])[-7:],
 "exchange_net_flow_egld":rbprev.get("exchange_net_flow_egld",[])+[R["whale_intelligence"]["exchange_flows"]["net_change_egld"]],
 "otc_pipeline_throughput_egld_7d":rbprev.get("otc_pipeline_throughput_egld_7d",[])+[otc_throughput_10],
 "binance_staking_custody_egld":(rbprev.get("binance_staking_custody_egld") or [3110663, 3377559])+[exchange_balances["Binance Staking"]]}
entry={
 "date":"2026-06-01","run_number":10,
 "data_quality":{
   "endpoints_that_worked":json.load(open("/tmp/run10/status.json"))["ok"],
   "endpoints_that_failed":["/tokens?sort=timestamp (HTTP 400 - 5th run carrying)","Brief HTTP 429 on H-token batch (recovered with longer delay)"],
   "api_quirks_discovered":[
     "/tokens/{id} batch hit HTTP 429 with 0.12s delays - increased to 0.6s fixed. Recommend keeping H-token batch delay >=0.5s, especially when followed by other API calls.",
     "OTC pipeline address typo in collect script caught a HTTP 400 (typo on Binance.com hot wallet and funder addresses). Lesson: always verify ad-hoc addresses against known-addresses.json before adding to query batch.",
     "Token supply_raw diff WORKS as predicted (run #9 fix landed) - flagged WEGLD +4.7% as the first reliable supply event detection. USDC/USDT diff still spurious because prev had signed values from the earlier bug.",
     "Validator joiners/leavers lists contain protocol system contracts (erd1qqqq...llllll...) that come/go as direct-node staking aggregators move above/below threshold - filter these out for the real validator movement count."],
   "data_gaps":[
     "Newly-issued token detection still BLOCKED (5 runs in a row). /tokens?sort=timestamp HTTP 400.",
     "AshSwap stableswap pool TVL still missing (admin contracts return zero EGLD).",
     "Validator joiner/leaver matching by name only; anonymous (no-identity) providers are not WoW-matchable. Need to store provider addresses in previous.json."]},
 "analysis_insights":{
   "what_worked":[
     "Tracing the OTC source funder (erd12tq6ax5k) confirmed 100% Binance.com origin - completing the OTC pipeline taxonomy that began run #6. The 14d inbound query against the funder address was the decisive evidence.",
     "Bilateral inverse rule prediction was strongly validated: -12% price -> +8.3% Hatom Lending EGLD. The rule has now produced 3 distinct event confirmations (run #7, #8, #10).",
     "Coinbase 3-week net outflow streak isolation provided a cleaner read on off-exchange accumulation than the noisy Binance-shuffle-dominated entity netting.",
     "Yield-chase regime tracking worked exactly as scoped: confirmed week 5 stalling via cohort-level WoW comparison vs the cumulative weeks 1-4 baseline."],
   "what_needs_improvement":[
     "Newly-issued token detection (6th run TODO).",
     "Validator joiner/leaver matching is unreliable; need address-based diffing.",
     "The Binance.com 'entity' is so dominant that headline exchange-flow numbers need automatic decomposition - this should be a structural report field, not just narrative."],
   "surprising_findings":[
     "OTC pipeline traced to Binance.com as the ULTIMATE origin via a pure pass-through funder. The 'organic OTC desk' framing is largely a fiction - Binance is settling customer sells through a multi-hop on-chain pipeline.",
     "Binance Staking custody crossed 3.5M EGLD with no delegation - 3 consecutive weeks of accumulation now constitutes a STRUCTURAL position, not transit.",
     "ZoidPay 40.8% DEX share fully reverted to 8.9% in a single week - confirming run #9 as event-driven with rare cleanliness.",
     "Bilateral inverse rule magnitude is now linear with price moves: +14.7% -> -13% EGLD; -16.9% -> +13.6% EGLD; -11.8% -> +8.3% EGLD."]},
 "methodology_changes":[
   "OTC PIPELINE TRACING METHOD: query funder address 14d inbound; if 100% concentration from one exchange + balance ~0 + outbound mirrors inbound = pure pass-through. Verified on erd12tq6ax5k.",
   "NEW RULE (validated): bilateral inverse rule scales linearly with price magnitude (3 data points).",
   "NEW RULE: validator joiner/leaver filtering - exclude erd1qqqq* system staking contracts.",
   "TOKEN SUPPLY EVENT DETECTION ACTIVE: prev.json supply_raw diff confirmed working. WEGLD +4.7% flagged as first real event. Thresholds 0.1% for stablecoins, 1.0% otherwise."],
 "new_addresses_discovered":[
   {"address":"erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp",
    "reason":"100% Binance.com inbound -> 100% erd17l22 outbound pass-through. 6,970 EGLD throughput 7d. This is the missing link between Binance.com and the OTC source layer.",
    "suggested_label":"Binance -> OTC Source Funder (verified 100% pass-through)","priority":"high"}],
 "action_items_completed":[
   "DONE: Tracked Binance Staking custody - now 3.51M, +135K parked again, protocol staked +30K only. 3-week structural accumulation confirmed.",
   "DONE: ZoidPay (ZPAY) follow-up - REVERTED from 40.8% to 8.9% in one week. Confirmed event-driven; not a regime shift.",
   "DONE: Yield-chase week 5 verified - PATTERN WEAKENING, net flow dropped from ~+50K cum to +3.5K, only procryptostaking sustained.",
   "DONE: erd12tq6ax5k traced - 100% Binance.com inbound, 100% erd17l22 outbound. Pipeline taxonomy COMPLETE.",
   "DONE: Token supply event detection - WEGLD +4.7% (+26K) flagged as first event after run #9 supply_raw fix.",
   "DONE: Exchange-flow direction verified - 2nd week of net outflow (-71K after -56K), per the run #9 rule = bullish off-exchange accumulation setup.",
   "PARTIAL: OTC trace on top-100 whales with >5% changes - erd12tq6ax5k traced; no new top-100 whale candidates surfaced this week.",
   "NOT DONE: Newly-issued token detection (5th run carrying).",
   "NOT DONE: AshSwap address set expansion."],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":R["meta_learning"]["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":[
   {"from_run":9,"title":"Multi-week net exchange-flow oscillation chart","status":"pending",
    "note":"Reaffirmed - this week is -71K (2nd outflow). A 3-bar diverging chart (+169K / -56K / -71K) makes the reversal story obvious. Still high priority."},
   {"from_run":9,"title":"DEX pair-composition stacked-area over time","status":"pending",
    "note":"This week's revert (40.8% -> 8.9%) is the perfect test case. Stacked-area would distinguish event-driven from regime-shift composition changes."},
   {"from_run":9,"title":"Binance staking-custody vs protocol-staked-module tracker","status":"pending",
    "note":"Re-proposed with even stronger motivation (3rd week of growth). Highest priority dashboard build. Re-listed in this run's suggestions."},
   {"from_run":8,"title":"OTC pipeline graph view (Sankey/force-directed)","status":"pending",
    "note":"Pipeline now FULLY MAPPED to Binance origin - the graph would be especially valuable now (5-hop chain). Still unbuilt."},
   {"from_run":8,"title":"Bilateral inverse rule chart (price vs Hatom Lending TVL in EGLD)","status":"pending",
    "note":"4th data point added this run. Have 3 validated rally/decline events now. Listed under this run's suggestions for build."},
   {"from_run":8,"title":"Yield-chase migration cumulative chart","status":"pending",
    "note":"Week 5 stalling visible - cumulative chart would clearly show the stall at +50K. Useful before regime ends."}],
 "self_assessment":{
   "most_valuable_insight":R["meta_learning"]["most_valuable_insight"],
   "actions_completed_count":7,"actions_attempted_count":9,
   "what_would_2x_next_week":"Build the Binance staking-custody vs protocol-staked tracker chart - 3 consecutive weeks of accumulation cry out for a multi-week visualization. Second: the OTC pipeline Sankey is now newly-relevant since the chain is fully traced (Binance origin). These two would transform single-week reports into a multi-week pattern dashboard for the two highest-signal flows on the network."},
 "recommendations_for_next_run":R["meta_learning"]["recommendations_for_next_run"]}
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #10; total runs",len(learn["runs"]))
print("baselines price",new_baselines["egld_price_usd"])
print("exchange_balances Binance Staking",round(exchange_balances["Binance Staking"],1))
