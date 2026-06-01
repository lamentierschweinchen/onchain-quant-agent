#!/usr/bin/env python3
import json
from datetime import datetime, timezone
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D=json.load(open("/tmp/run9/collected.json"))
R=json.load(open(f"{REPO}/reports/2026-05-25.json"))
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
binance_com=sum(b(a) for a in ["erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets","erd1ylwuswz9zuk4acuq4aa6d0x9ys293yhlpwg6vpuwntndyej4u44q896zlz","erd1v4ms58e22zjcp08suzqgm9ajmumwxcy4hfkdc23gvynnegjdflmsj6gmaq"])
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
 "snapshot_date":"2026-05-25",
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
   {"address":"erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p","label":"Binance Staking custody (+267K this week, now 3.38M - parked not delegated)","balance_egld":b("erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"),"weeks_tracked":3,"first_seen":"2026-05-11"},
   {"address":"erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh","label":"Unknown Whale (OTC source, dormant this week; funder erd12tq6ax5k identified)","balance_egld":b("erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh"),"weeks_tracked":3,"first_seen":"2026-05-11"},
   {"address":"erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp","label":"Candidate upstream funder of OTC source erd17l22 (2K top-up this week)","balance_egld":None,"weeks_tracked":1,"first_seen":"2026-05-25"},
   {"address":"erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw","label":"Unknown Mega Whale (993K, small bidirectional Coinbase flow resumed)","balance_egld":b("erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"),"weeks_tracked":6,"first_seen":"2026-04-20"},
   {"address":"erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5","label":"UPbit OTC Desk (distribution phase, drawing down)","balance_egld":b("erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"),"weeks_tracked":9,"first_seen":"2026-04-02"},
   {"address":"erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r","label":"OTC Distribution Wallet (distribution phase, drawing down)","balance_egld":b("erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"),"weeks_tracked":7,"first_seen":"2026-04-13"},
   {"address":"erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets","label":"Binance.com hot (-316K to staking custody this week)","balance_egld":b("erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets"),"weeks_tracked":2,"first_seen":"2026-05-18"}]}
json.dump(new_prev,open(f"{REPO}/data/previous.json","w"),indent=2)
print("WROTE previous.json; top_accounts",len(top_accounts),"providers",len(staking_providers))

# ---- learnings.json append ----
def roll(arr,val,n=7):
    a=arr+[val]
    return a[-n:] if len(a)>n else a
rbprev=learn["runs"][-1]["running_baselines"]
sr_cur=econ["staked"]/econ["circulatingSupply"]
new_baselines={
 "egld_price_usd":roll(rbprev["egld_price_usd"],econ["price"]),
 "dex_volume_24h_usd":roll(rbprev["dex_volume_24h_usd"],R["token_activity"]["xexchange"]["total_volume_24h_usd"]),
 "staked_egld":roll(rbprev["staked_egld"],econ["staked"]),
 "mex_price_usd":rbprev["mex_price_usd"]+[meco["price"]],
 "total_delegators":rbprev["total_delegators"]+[R["staking_intelligence"]["churn"]["total_delegators_current"]],
 "staked_ratio":(rbprev["staked_ratio"]+[sr_cur])[-6:],
 "exchange_net_flow_egld":rbprev.get("exchange_net_flow_egld",[])+[R["whale_intelligence"]["exchange_flows"]["net_change_egld"]],
 "otc_pipeline_throughput_egld_7d":rbprev.get("otc_pipeline_throughput_egld_7d",[])+[144933]}
entry={
 "date":"2026-05-25","run_number":9,
 "data_quality":{
   "endpoints_that_worked":json.load(open("/tmp/run9/status.json"))["ok"],
   "endpoints_that_failed":["/tokens?sort=timestamp (HTTP 400)"],
   "api_quirks_discovered":[
     "total_delegators z-score is DEGENERATE: baseline sd ~18 over a ~179K base means a -53 (-0.03%) move shows z=-4.5 sigma. Near-constant metrics produce spurious z-scores - always cross-check absolute % change before assigning severity.",
     "mex/economics volume24h returned a NONZERO value ($121K) this run (historically $0). Still prefer mex/pairs sum ($81.9K) for consistency, but the eco field may be becoming usable.",
     "Token supply comparison broken across runs: previous.json historically stored decimals-adjusted supply while /tokens returns raw integer supply. Fixed this run by storing supply_raw in previous.json for like-for-like diffs from run #10.",
     "Intra-entity wallet shuffles can dominate the headline exchange-flow figure (Binance hot->staking-custody +267K). Decompose entity netting into per-wallet moves before interpreting direction."],
   "data_gaps":[
     "erd17l22 +58K (run #7) original funding source still not fully resolved - this week only a 2K top-up from erd12tq6ax5k observed (the big inflow predates the 14d window).",
     "Newly-issued token detection still degraded (5 runs). /tokens?sort=timestamp HTTP 400; ESDT system-SC issuance scan still TODO.",
     "AshSwap stableswap pool TVL still missing (admin contracts return zero EGLD); address set needs pool contracts."]},
 "analysis_insights":{
   "what_worked":[
     "Decomposing the Binance entity flow surfaced the real story: hot wallet -316K -> staking custody +267K, a parked-capital accumulation, not an exchange inflow/outflow. Per-wallet decomposition beat the entity-net headline.",
     "Catching the degenerate total_delegators z-score (z=-4.5 from sd=18) and downgrading it - avoided a false 'critical' anomaly. Methodology self-correction.",
     "ZoidPay anomaly caught via DEX pair-composition shift (WEGLD/USDC 91.6%->56.2%) cross-referenced with the +59% price move - two independent signals confirming one event.",
     "Exchange-flow reversal (+169K -> -56K) validated the run #8 two-week confirmation rule: single-week capitulation reads should not be extrapolated."],
   "what_needs_improvement":[
     "Newly-issued token detection still TODO (5th run).",
     "Validator joiner/leaver matching is unreliable for anonymous (no-identity) delegation contracts - matched by name only. Need contract-address-based matching (store provider addresses in previous.json).",
     "AshSwap address set expansion still pending."],
   "surprising_findings":[
     "Binance moved 267K from hot wallet into staking-custody wallet (now 3.38M) but did NOT delegate it - the protocol staked module barely moved. A large undeployed position is accumulating.",
     "ZoidPay/WEGLD captured 40.8% of DEX volume - first time ANY non-WEGLD/USDC pair broke 40% in tracking history. WEGLD/USDC dominance fell from 91.6% to 56.2%.",
     "Last week's bearish +169K exchange inflow fully reversed to -56K - a clean single-week reaction, not the start of capitulation.",
     "Yield-chase leadership rotated within the 0%-fee cohort: procryptostaking +17K and valuestaking +16K took over from ninjastaking/egldstakingprovider."]},
 "methodology_changes":[
   "NEW RULE: degenerate z-scores - downgrade severity when baseline stddev is tiny relative to the metric and the absolute % move is <0.1% (total_delegators case).",
   "CONFIRMED: decompose entity netting into per-wallet moves; intra-entity shuffles (Binance hot->staking) masquerade as exchange flow.",
   "CONFIRMED (mild): bilateral inverse rule scales with price-move magnitude (+2.3% price -> Hatom Lending -1% EGLD).",
   "VALIDATED: run #8 exchange-flow two-week confirmation rule - the +169K inflow was a single-week reaction (reverted -56K)."],
 "new_addresses_discovered":[
   {"address":"erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp",
    "reason":"Sent ~2K EGLD in two chunks to OTC source wallet erd17l22 this week. Candidate upstream funder of the OTC source layer. erd17l22 was otherwise dormant.",
    "suggested_label":"OTC Source Funder (erd17l22 upstream)","priority":"medium"}],
 "action_items_completed":[
   "DONE: Applied OTC-source detection template to top-100 whales - erd17l22 now dormant (winding down after run #8 wave); traced inbound funder erd12tq6ax5k.",
   "DONE: erd17l22 inbound investigation - 14d inbound is just +2K from erd12tq6ax5k; the original +58K predates the window.",
   "DONE: staked_ratio z-watch - did NOT breach -2 sigma (receded to -1.38). Ratio stabilized at 48.22%.",
   "DONE: Binance Staking parked capital tracked - it GREW +267K (now 3.38M), capital added not deployed. Major finding.",
   "DONE: yield-chase week 4 verified - persists with rotating leadership (procryptostaking +17K, valuestaking +16K).",
   "DONE: exchange net-inflow trend - REVERSED to -56K (single-week reaction confirmed, not multi-week capitulation).",
   "DONE: MEX z-score activated (N=4, z=-0.83, normal).",
   "DONE: applied OTC trace to Unknown Mega Whale erd18mv2 - resumed small bidirectional Coinbase flow, balance flat.",
   "PARTIAL: MrsEGLD dossier - still present ~158K, quiet week, no new info.",
   "NOT DONE: newly-issued token detection (5th run carrying).",
   "NOT DONE: AshSwap address set expansion."],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":[
   {"title":"Multi-week net exchange-flow oscillation chart",
    "motivation":"Run #8 was +169K net inflow (bearish), run #9 reversed to -56K outflow. The single-week dashboard can't show that the +169K did NOT persist. A weekly net-flow bar chart (green outflow / red inflow) would make the single-week-reaction vs multi-week-capitulation distinction visible at a glance.",
    "suggested_visualization":"diverging bar chart, one bar per week, net exchange EGLD flow, colored by sign; overlay EGLD price line.",
    "data_already_available":True,
    "data_source":"learnings.json running_baselines.exchange_net_flow_egld + report whale_intelligence.exchange_flows.net_change_egld",
    "priority":"high"},
   {"title":"DEX pair-composition stacked-area over time",
    "motivation":"This run WEGLD/USDC dominance collapsed 91.6%->56.2% as ZoidPay/WEGLD took 40.8%. The current dashboard shows one week's pair list; a stacked-area of pair-share over weeks would surface emerging second markets (the ZPAY event) and revert/persist dynamics.",
    "suggested_visualization":"100% stacked area chart of top-5 pair volume share per week.",
    "data_already_available":True,
    "data_source":"report token_activity.xexchange.top_pairs_by_volume across reports",
    "priority":"medium"},
   {"title":"Binance staking-custody vs protocol-staked-module tracker",
    "motivation":"The week's top finding: Binance's staking-custody wallet grew to 3.38M (+267K) while the protocol staked module barely moved - capital parked, not delegated. A two-line chart (custody wallet balance vs staked module) would make 'parked vs delegated' obvious and flag the moment Binance deploys or distributes.",
    "suggested_visualization":"dual-line time series: Binance Staking wallet balance vs economics.staked, weekly.",
    "data_already_available":True,
    "data_source":"previous.json exchange_balances['Binance Staking'] + economics.staked_egld across reports",
    "priority":"high"}],
 "dashboard_suggestions_followup":[
   {"from_run":8,"title":"OTC pipeline graph view (Sankey/force-directed)","status":"pending",
    "note":"Still unbuilt; data available. Even more relevant now - pipeline in distribution phase (~145K throughput) and source layer (erd17l22 + funder erd12tq6ax5k) extended."},
   {"from_run":8,"title":"Bilateral inverse rule chart (price vs Hatom Lending TVL in EGLD)","status":"pending",
    "note":"3rd data point added this run (+2.3% price -> -1% EGLD lending). Now have rally/decline/mild-recovery points - good time to build."},
   {"from_run":8,"title":"Yield-chase migration cumulative chart","status":"pending",
    "note":"Week 4 confirmed with rotating leadership; cumulative chart would now show the rotation within the 0%-fee cohort. Still unbuilt."}],
 "self_assessment":{
   "most_valuable_insight":R["meta_learning"]["most_valuable_insight"],
   "actions_completed_count":8,"actions_attempted_count":11,
   "what_would_2x_next_week":"Build the Binance staking-custody vs staked-module tracker and wire exchange_net_flow_egld into a multi-week chart. The two highest-signal forward indicators (Binance's 3.38M undeployed position; whether exchange flows re-accelerate) are exactly the things the current single-week dashboard cannot show."},
 "recommendations_for_next_run":R["meta_learning"]["recommendations_for_next_run"]}
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #9; total runs",len(learn["runs"]))
print("baselines price",new_baselines["egld_price_usd"])
print("exchange_balances Binance Staking",round(exchange_balances["Binance Staking"],1))
