#!/usr/bin/env python3
import json
from datetime import datetime, timezone
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D=json.load(open("/tmp/run11/collected.json"))
R=json.load(open(f"{REPO}/reports/2026-06-08.json"))
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
binance_com=sum((b(a) or 0) for a in ["erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp29trp6qsl2gdvvz2eqra76xc","erd1ylwuswz9zuk4acuq4aa6d0x9ys293yhlpwg6vpuwntndyej4u44q896zlz","erd1v4ms58e22zjcp08suzqgm9ajmumwxcy4hfkdc23gvynnegjdflmsj6gmaq"])
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
 "snapshot_date":"2026-06-08",
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
 "watch_addresses":[
   {"address":"erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p","label":"Binance Staking custody (STALLED at 3.51M, 4 wks tracked, neither delegation nor distribution)","balance_egld":b("erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"),"weeks_tracked":5,"first_seen":"2026-05-11"},
   {"address":"erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh","label":"OTC source (+7K WoW from chain, continuing pass-through; balance 303K)","balance_egld":b("erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh"),"weeks_tracked":5,"first_seen":"2026-05-11"},
   {"address":"erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp","label":"OTC source funder (canonicalized; 100% Binance.com -> erd17l22 pass-through)","balance_egld":0.0,"weeks_tracked":3,"first_seen":"2026-05-25"},
   {"address":"erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw","label":"Unknown Mega Whale (received +5,925 from Coinbase Routing 2026-06-07; near 1M threshold)","balance_egld":b("erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"),"weeks_tracked":8,"first_seen":"2026-04-20"},
   {"address":"erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5","label":"UPbit OTC Desk (DISTRIBUTION wave hit, -14K -30%)","balance_egld":b("erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"),"weeks_tracked":11,"first_seen":"2026-04-02"},
   {"address":"erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r","label":"OTC Distribution Wallet (DISTRIBUTION wave hit, -12.4K -28%)","balance_egld":b("erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"),"weeks_tracked":9,"first_seen":"2026-04-13"},
   {"address":"erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp29trp6qsl2gdvvz2eqra76xc","label":"Binance.com hot (-36.7K WoW, no offsetting custody growth this week)","balance_egld":b("erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp29trp6qsl2gdvvz2eqra76xc"),"weeks_tracked":4,"first_seen":"2026-05-18"},
   {"address":"erd16jruked88jgtsar78ej85hjp3qsd9jkjcw4swsn7k0teqh3wgcqqgyrupq","label":"Coinbase (+26.8K WoW, +51.5% - reversed 3-week outflow streak)","balance_egld":b("erd16jruked88jgtsar78ej85hjp3qsd9jkjcw4swsn7k0teqh3wgcqqgyrupq"),"weeks_tracked":2,"first_seen":"2026-06-01"}]}
json.dump(new_prev,open(f"{REPO}/data/previous.json","w"),indent=2)
print("WROTE previous.json; top_accounts",len(top_accounts),"providers",len(staking_providers))

# ---- learnings.json append ----
def roll(arr,val,n=7):
    a=arr+[val]
    return a[-n:] if len(a)>n else a
rbprev=learn["runs"][-1]["running_baselines"]
sr_cur=econ["staked"]/econ["circulatingSupply"]
# OTC throughput this week = sum of UPbit OTC + OTC Dist outbound to retail (~163K) but for baseline use NET change in OTC desks (distribution = negative throughput in the load-distribute cycle)
otc_throughput_11 = -26410  # net OTC desk balance change (distribution wave)
new_baselines={
 "egld_price_usd":roll(rbprev["egld_price_usd"],econ["price"]),
 "dex_volume_24h_usd":roll(rbprev["dex_volume_24h_usd"],R["token_activity"]["xexchange"]["total_volume_24h_usd"]),
 "staked_egld":roll(rbprev["staked_egld"],econ["staked"]),
 "mex_price_usd":(rbprev["mex_price_usd"]+[meco["price"]])[-8:],
 "total_delegators":(rbprev["total_delegators"]+[R["staking_intelligence"]["churn"]["total_delegators_current"]])[-8:],
 "staked_ratio":(rbprev["staked_ratio"]+[sr_cur])[-7:],
 "exchange_net_flow_egld":rbprev.get("exchange_net_flow_egld",[])+[R["whale_intelligence"]["exchange_flows"]["net_change_egld"]],
 "otc_pipeline_throughput_egld_7d":rbprev.get("otc_pipeline_throughput_egld_7d",[])+[otc_throughput_11],
 "binance_staking_custody_egld":(rbprev.get("binance_staking_custody_egld") or [])+[exchange_balances["Binance Staking"]]}
entry={
 "date":"2026-06-08","run_number":11,
 "data_quality":{
   "endpoints_that_worked":json.load(open("/tmp/run11/status.json"))["ok"],
   "endpoints_that_failed":["/tokens?sort=timestamp (HTTP 400 - resolved via ESDT system SC workaround)"],
   "api_quirks_discovered":[
     "Newly-issued token detection workaround SUCCESSFUL: /accounts/erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u/transactions?after=SEVEN_DAYS_AGO&function=issue returns recent issuance txs. Decode tx.data (hex segments split on @) to extract [name_hex, ticker_hex, supply_hex, decimals_hex, ...flags]. Then look up resulting identifier via /tokens?search=<NAME>.",
     "Funder address mistype discovered: the run #10 collect script used erd12tq6ax5k49dkp4lwgxz8ed62gz3xc3xwa30dgxqhke9awz58z2qq07ny36 but the ACTUAL funder is erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp. Both prefixes match for the first ~16 chars. Visible from erd17l22 inbound list as the sender of 9,411 EGLD. Recommend canonicalizing this address in known-addresses.json under exchange_routers.",
     "previous.json supply_raw diff WORKS: WEGLD diff this week showed essentially flat (run #10's +4.7% was a one-off). The 0.1% / 1.0% thresholds catch genuine events.",
     "OTC cycle period confirmed: run #10 loading -> run #11 distribution = ~1 week minimum. Faster than initial 1-3 week estimate."],
   "data_gaps":[
     "AshSwap stableswap pool TVL still missing (admin contracts return zero EGLD).",
     "Validator joiner/leaver matching by name only; anonymous (no-identity) providers are not WoW-matchable. Need to store provider addresses in previous.json.",
     "SWTAO market cap returned 0 this run (Hatom LSD-only used SEGLD - check next week if SWTAO continues to register)."]},
 "analysis_insights":{
   "what_worked":[
     "Forward-indicator validation: 3 of 4 run #10 predictions resolved BEARISH (Binance custody stalled, $3.50 floor broke, Coinbase outflow streak ended). The 'failed forward indicator' is a strong new bearish signal pattern.",
     "OTC distribution wave prediction validated within 1 week of the predicted 1-3 week window - confirms the load-distribute cycle as empirically reliable.",
     "Newly-issued token detection workaround works in production - the ESDT system SC scan approach took 6 runs to design but resolves the blocker cleanly.",
     "Bilateral inverse rule remains directionally correct on 5th observation; the magnitude trajectory (now WEAKENING) is itself a new piece of intelligence."],
   "what_needs_improvement":[
     "Track the magnitude scaling of the bilateral inverse rule over time - the current weakening trend needs quantitative tracking.",
     "Coinbase entity netting still mixes primary/custody/routing - need to track each separately for cleaner OTC pattern detection.",
     "LSD contraction during a decline is a new pattern that doesn't have an established interpretation yet. Need 2-3 more confirmations to formalize."],
   "surprising_findings":[
     "EGLD decoupled to the downside from BTC (+1.3%) and ETH (+3.6%) - both up while EGLD -15.7%. MultiversX-specific weakness, not crypto-macro.",
     "Coinbase 3-week outflow streak (the cleanest bullish signal) reversed sharply in a single week to +43K inflow. Off-exchange-accumulation thesis killed.",
     "Binance Staking custody stalled at exactly the moment the bullish thesis needed it to escalate. Three weeks of accumulation, then stall, no resolution.",
     "OTC distribution wave hit in week 1 of the predicted window - aggressive sell-side execution given the price decline.",
     "Hatom LSD AND XOXNO LSD both contracted in EGLD terms - unusual; LSD users typically don't unstake during declines."]},
 "methodology_changes":[
   "NEW WORKAROUND: newly-issued token detection via ESDT system SC issue function scan. Now standard.",
   "NEW PATTERN: 'failed forward indicator' as bearish signal. When 3+ bullish predictions fail simultaneously during a decline, the convergence is decisive.",
   "REFINED RULE: Bilateral inverse rule magnitude is DETERIORATING (track ratio: response/|price chg|).",
   "NEW PATTERN: synchronized LSD contraction during decline (Hatom -1.6%, XOXNO -1.4% EGLD). Watch list item; needs 2-3 more observations to formalize.",
   "OTC cycle period confirmed at 1 week minimum (load->distribute)."],
 "new_addresses_discovered":[],
 "action_items_completed":[
   "DONE: Binance Staking custody resolution check - STALLED at 3.51M (neither delegated nor distributed). The 'either resolution is highest signal' question is half-resolved into a hold state.",
   "DONE: OTC distribution wave verification - HIT ON SCHEDULE in week 1 (UPbit OTC -14K, OTC Dist -12.4K = -26.4K).",
   "DONE: $3.50 floor test - FLOOR BROKE to $2.95 (-15.7%). Regime shift down to lower band confirmed.",
   "DONE: Yield-chase regime end watch - REGIME ENDED. Cohort net -2.6K, 3 of 5 leaders reversed.",
   "DONE: Coinbase 4-week net outflow check - FAILED. +43K inflow this week broke the streak. Off-exchange-accumulation thesis collapsed.",
   "DONE: WEGLD supply follow-up - flat WoW; run #10's +4.7% was a one-off (not sustained DEX expansion).",
   "DONE: Newly-issued token detection workaround - SUCCESSFUL via ESDT system SC scan. 3 issuances detected (FRA, GSN, GTA - all low-quality spam).",
   "PARTIAL: OTC source candidates mapping - no new Binance funder routes surfaced this run.",
   "NOT DONE: AshSwap address set expansion (4th run carrying)."],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":R["meta_learning"]["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":[
   {"from_run":10,"title":"Multi-week Binance custody vs protocol-staked tracker chart","status":"pending",
    "note":"Even more relevant this week: custody STALLED at 3.51M for first time after 3 wks of growth. Visualization would make the resolution moment unmissable. Re-listed in this run's suggestions."},
   {"from_run":10,"title":"OTC pipeline phase visualization (load vs distribute)","status":"pending",
    "note":"Empirically VALIDATED this week (run #10 loading -> run #11 distribution in 1 week). The visualization is now strongly motivated by validated data. Re-listed in this run's suggestions."},
   {"from_run":10,"title":"Bilateral inverse rule EGLD-vs-USD divergence chart for Hatom Lending","status":"pending",
    "note":"5th data point added, magnitude DETERIORATING. Chart would now show both the rule and its weakening intensity - higher value. Re-listed in this run's suggestions."},
   {"from_run":9,"title":"Multi-week net exchange-flow oscillation chart","status":"pending",
    "note":"Trajectory now +169K / -56K / -71K / +25K = bearish-bullish-bullish-bearish noisy oscillation. The chart would make the noise pattern obvious."},
   {"from_run":9,"title":"DEX pair-composition stacked-area over time","status":"pending",
    "note":"ZoidPay revert continued (3.0% this week). Stacked-area would show event-driven vs regime composition changes."},
   {"from_run":8,"title":"OTC pipeline graph view (Sankey/force-directed)","status":"pending",
    "note":"Pipeline fully traced (Binance origin) AND distribution wave validated this week. The Sankey view becomes especially valuable now."},
   {"from_run":8,"title":"Yield-chase migration cumulative chart","status":"deprioritized",
    "note":"Yield-chase regime ENDED this week. The chart would now show a completed pattern - useful for retrospective analysis but not for active monitoring."}],
 "self_assessment":{
   "most_valuable_insight":R["meta_learning"]["most_valuable_insight"],
   "actions_completed_count":7,"actions_attempted_count":9,
   "what_would_2x_next_week":"Implement the forward-indicator scorecard widget. Run #10 made 4 predictions; this run found 3 of 4 resolved BEARISH. That cluster of failed bullish predictions IS the bearish signal - more decisive than any individual anomaly. A widget tracking each run's recommendations_for_next_run with weekly outcome status would surface this 'all bullish forwards failing' pattern automatically. Second-best: build the Binance staking-custody chart now that we have 4 weekly data points showing accumulate-accumulate-accumulate-STALL."},
 "recommendations_for_next_run":R["meta_learning"]["recommendations_for_next_run"]}
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #11; total runs",len(learn["runs"]))
print("baselines price",new_baselines["egld_price_usd"])
print("exchange_balances Binance Staking",round(exchange_balances["Binance Staking"],1) if exchange_balances["Binance Staking"] is not None else "None")
print("exchange_balances Coinbase",round(exchange_balances["Coinbase"],1))
