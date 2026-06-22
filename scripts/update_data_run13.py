#!/usr/bin/env python3
import json
from datetime import datetime, timezone
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D=json.load(open("/tmp/run13/collected.json"))
R=json.load(open(f"{REPO}/reports/2026-06-22.json"))
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
 "snapshot_date":"2026-06-22",
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
   {"address":"erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p","label":"Binance Staking custody (STALLED 3rd consecutive week at 3.51M; 6 weeks parked)","balance_egld":b("erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"),"weeks_tracked":7,"first_seen":"2026-05-11"},
   {"address":"erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5","label":"UPbit OTC Desk (RELOADED +4.8K; loading phase, distribution wave expected 1-3 weeks)","balance_egld":b("erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"),"weeks_tracked":13,"first_seen":"2026-04-02"},
   {"address":"erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r","label":"OTC Distribution Wallet (RELOADED +2.3K; loading phase)","balance_egld":b("erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"),"weeks_tracked":11,"first_seen":"2026-04-13"},
   {"address":"erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh","label":"OTC source erd17l22","balance_egld":b("erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh"),"weeks_tracked":7,"first_seen":"2026-05-11"},
   {"address":"erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp","label":"OTC source funder (Binance.com -> erd17l22 pass-through)","balance_egld":b("erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp") or 0,"weeks_tracked":5,"first_seen":"2026-05-25"},
   {"address":"erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw","label":"Unknown Mega Whale (dormant 3rd week at 998,971; near 1M threshold)","balance_egld":b("erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"),"weeks_tracked":10,"first_seen":"2026-04-20"},
   {"address":"erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets","label":"Binance.com hot (canonical); -6.3K WoW","balance_egld":b("erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets"),"weeks_tracked":2,"first_seen":"2026-06-15"},
   {"address":"erd16jruked88jgtsar78ej85hjp3qsd9jkjcw4swsn7k0teqh3wgcqqgyrupq","label":"Coinbase (3rd consecutive inflow week; +3.9K)","balance_egld":b("erd16jruked88jgtsar78ej85hjp3qsd9jkjcw4swsn7k0teqh3wgcqqgyrupq"),"weeks_tracked":4,"first_seen":"2026-06-01"}]}
json.dump(new_prev,open(f"{REPO}/data/previous.json","w"),indent=2)
print("WROTE previous.json; top_accounts",len(top_accounts),"providers",len(staking_providers))

# ---- learnings.json append ----
def roll(arr,val,n=8):
    a=arr+[val]
    return a[-n:] if len(a)>n else a
rbprev=learn["runs"][-1]["running_baselines"]
sr_cur=econ["staked"]/econ["circulatingSupply"]
otc_throughput_13 = 7028  # desk balance change (LOADING): UPbit OTC +4752 + OTC Dist +2276
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
 "date":"2026-06-22","run_number":13,
 "data_quality":{
   "endpoints_that_worked":R["meta_learning"]["endpoints_that_worked"],
   "endpoints_that_failed":R["meta_learning"]["endpoints_that_failed"],
   "api_quirks_discovered":R["meta_learning"]["api_quirks"],
   "data_gaps":R["meta_learning"]["data_gaps"]},
 "analysis_insights":{
   "what_worked":[
     "Exit-liquidity-bounce thesis from run #12 cleanly validated: predicted the bounce would fail; price broke to a new low within one week.",
     "Coinbase 2-week confirmation rule extended to 3 weeks - off-exchange-accumulation reversal confirmed structural.",
     "OTC load->distribute cycle prediction worked: the inter-cycle gap resolved to a reload exactly as forecast.",
     "Supply-based LSD reporting dissolved the phantom 'synchronized LSD contraction' narrative built on price-contaminated mcap data across runs #11-12.",
     "Degenerate-z-score guard correctly prevented over-flagging the -78 delegator move as a -2.68σ anomaly."],
   "what_needs_improvement":[
     "Collector needs a dataApi populated-or-retry guard: 4 LSD/stablecoin tokens went null at 1.0s spacing and only recovered on an isolated 2.5s re-fetch.",
     "Newly-issued token scan empty 2nd week - still no way to distinguish a quiet week from method failure.",
     "EMRS-6e4067 surfaced at $28M headline mcap with no holder/volume traction - need a low-float flag to avoid mis-ranking thin listings."],
   "surprising_findings":[
     "The delegator capitulation was a single shake-out: -4,003 last week, -78 this week. The base stabilized rather than entering an accelerating exit.",
     "On a supply basis the LSDs GREW or held flat (XEGLD +0.6%, SEGLD -0.5%) despite USD mcaps falling - the multi-run 'contraction' story was a price artifact.",
     "USH de-leveraging (2-week burn) ended; supply flat. CDP closure pressure paused.",
     "Reward compound rate fell for a 3rd straight week (61.9% -> 59.14% -> 55.31%), a slow bearish drift in delegator conviction.",
     "Bridged stablecoins contracted (USDC -0.5%, USDT -1.8%) - dollar liquidity bridging out during the decline."]},
 "methodology_changes":R["meta_learning"]["methodology_changes"],
 "new_addresses_discovered":[],
 "action_items_completed":[
   "DONE: Capitulation bounce thesis - FAILED. Bounce lasted one week; price broke to a new low $2.85. Exit-liquidity read validated.",
   "DONE: Binance Staking custody 3rd-week stall - CONFIRMED unchanged at 3.51M (6 weeks parked).",
   "DONE: Delegator capitulation follow-up - ONE-SHOT. -78 this week (vs -4,003); base stabilized at 174,406.",
   "DONE: OTC pipeline reload - CONFIRMED. +7K desk balance, 85K throughput; Binance->OTC Router 2 feeding 4,800 chunks.",
   "DONE: LSD/USH rate-limit fix verification - FAILED at 1.0s (went null again); escalated to isolated 2.5s re-fetch + supply-based reporting.",
   "DONE: Coinbase 3rd-week inflow check - CONFIRMED. 3 consecutive inflow weeks; reversal now structural.",
   "DONE: Yield-chase cohort follow-up - MIXED net redemption (~-22K); valuestaking/star/egldstaking bleed, pi-staking +21.9K isolated entry.",
   "DONE: XOXNO LSD 3rd-week contraction watch - NOT CONFIRMED. XEGLD supply grew +0.6%; LSD-contraction thesis dead.",
   "DONE: Mega Whale erd18mv2z6r2 - dormant 3rd week at 998,971, no downstream forwarding.",
   "DEFERRED: GTA/GSN/FRA newly-issued mcap-threshold check - newly-issued scan returned 0 this week; not re-queried individually."],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":R["meta_learning"]["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":R["meta_learning"]["dashboard_suggestions_followup"],
 "self_assessment":{
   "most_valuable_insight":R["meta_learning"]["most_valuable_insight"],
   "actions_completed_count":9,"actions_attempted_count":10,
   "what_would_2x_next_week":"Build the LSD circulating-supply timeline (supply, not mcap). This run proved the multi-run 'LSD contraction' narrative was a price artifact; a supply-based view would have prevented three runs of mis-narration and is immune to the dataApi null-price issue. Second: an OTC cycle phase indicator, since the load->distribute->gap->reload cycle is now empirically validated and forward-predictive."},
 "recommendations_for_next_run":R["meta_learning"]["recommendations_for_next_run"]}
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #13; total runs",len(learn["runs"]))
print("baselines price",new_baselines["egld_price_usd"])
print("baselines compound",new_baselines["reward_compound_pct"])
print("baselines binance_custody",new_baselines.get("binance_staking_custody_egld"))
