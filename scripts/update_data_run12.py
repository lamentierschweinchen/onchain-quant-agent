#!/usr/bin/env python3
import json
from datetime import datetime, timezone
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D=json.load(open("/tmp/run12/collected.json"))
R=json.load(open(f"{REPO}/reports/2026-06-15.json"))
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
# Binance: corrected addr (erd1sdslv...3rgul...sets) replaces bad one (erd1sdslv...29trp...76xc)
binance_com_addrs = [
    "erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets",  # canonical
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
 "snapshot_date":"2026-06-15",
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
   {"address":"erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p","label":"Binance Staking custody (STALLED 2nd consecutive week at 3.51M, 5 weeks tracked total)","balance_egld":b("erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"),"weeks_tracked":6,"first_seen":"2026-05-11"},
   {"address":"erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh","label":"OTC source -3.6K WoW; balance 299K","balance_egld":b("erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh"),"weeks_tracked":6,"first_seen":"2026-05-11"},
   {"address":"erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp","label":"OTC source funder (Binance.com -> erd17l22 pass-through)","balance_egld":b("erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp") or 0,"weeks_tracked":4,"first_seen":"2026-05-25"},
   {"address":"erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw","label":"Unknown Mega Whale (unchanged at 998,971 EGLD; near 1M threshold)","balance_egld":b("erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"),"weeks_tracked":9,"first_seen":"2026-04-20"},
   {"address":"erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5","label":"UPbit OTC Desk (inter-cycle gap, balance 30.8K)","balance_egld":b("erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"),"weeks_tracked":12,"first_seen":"2026-04-02"},
   {"address":"erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r","label":"OTC Distribution Wallet (inter-cycle gap, balance 33.3K)","balance_egld":b("erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"),"weeks_tracked":10,"first_seen":"2026-04-13"},
   {"address":"erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets","label":"Binance.com hot (canonical, replaces run #11 invalid checksum); +24K WoW","balance_egld":b("erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets"),"weeks_tracked":1,"first_seen":"2026-06-15"},
   {"address":"erd16jruked88jgtsar78ej85hjp3qsd9jkjcw4swsn7k0teqh3wgcqqgyrupq","label":"Coinbase (2nd consecutive inflow week; +8.4K to 87K)","balance_egld":b("erd16jruked88jgtsar78ej85hjp3qsd9jkjcw4swsn7k0teqh3wgcqqgyrupq"),"weeks_tracked":3,"first_seen":"2026-06-01"}]}
json.dump(new_prev,open(f"{REPO}/data/previous.json","w"),indent=2)
print("WROTE previous.json; top_accounts",len(top_accounts),"providers",len(staking_providers))

# ---- learnings.json append ----
def roll(arr,val,n=8):
    a=arr+[val]
    return a[-n:] if len(a)>n else a
rbprev=learn["runs"][-1]["running_baselines"]
sr_cur=econ["staked"]/econ["circulatingSupply"]
otc_throughput_12 = -881  # near-flat (-1.8K + 0.9K = -0.9K)
new_baselines={
 "egld_price_usd":roll(rbprev["egld_price_usd"],econ["price"]),
 "dex_volume_24h_usd":roll(rbprev["dex_volume_24h_usd"],R["token_activity"]["xexchange"]["total_volume_24h_usd"]),
 "staked_egld":roll(rbprev["staked_egld"],econ["staked"]),
 "mex_price_usd":roll(rbprev["mex_price_usd"],meco["price"]),
 "total_delegators":roll(rbprev["total_delegators"],R["staking_intelligence"]["churn"]["total_delegators_current"]),
 "staked_ratio":roll(rbprev["staked_ratio"],sr_cur),
 "exchange_net_flow_egld":rbprev.get("exchange_net_flow_egld",[])+[R["whale_intelligence"]["exchange_flows"]["net_change_egld"]],
 "otc_pipeline_throughput_egld_7d":rbprev.get("otc_pipeline_throughput_egld_7d",[])+[otc_throughput_12],
 "binance_staking_custody_egld":(rbprev.get("binance_staking_custody_egld") or [])+[exchange_balances["Binance Staking"]]}
entry={
 "date":"2026-06-15","run_number":12,
 "data_quality":{
   "endpoints_that_worked":R["meta_learning"]["endpoints_that_worked"],
   "endpoints_that_failed":R["meta_learning"]["endpoints_that_failed"],
   "api_quirks_discovered":R["meta_learning"]["api_quirks"],
   "data_gaps":R["meta_learning"]["data_gaps"]},
 "analysis_insights":{
   "what_worked":[
     "Capitulation bounce prediction validated: predicted +1.4% to $2.99 off $2.95 floor.",
     "Coinbase 2-week confirmation rule worked: off-exchange thesis killed in 2 weeks.",
     "Rate-limit diagnostic on /tokens/{id} resolved last run's SWTAO 'null' anomaly cleanly.",
     "Engagement-collapse composite as a new bearish read: 5 simultaneous bearish indicators during a price up-week is highly informative.",
     "Reward behavior compound rate moving as a slow-signal indicator (61.9% -> 59.14% = mild bearish drift)."],
   "what_needs_improvement":[
     "Bilateral inverse rule threshold should be explicitly encoded (5% minimum |Δprice| from this run's analysis).",
     "Address validation on storage to known-addresses.json — bech32 checksum check would have caught run #11's invalid address.",
     "Newly-issued token scan returned empty - no way to distinguish 'no activity' from 'method failure' without independent verification."],
   "surprising_findings":[
     "Run #11's 'synchronized LSD contraction' was partially a data artifact (SWTAO rate-limit miss caused $1.18M Hatom LSD undercount). Hatom LSD apples-to-apples is actually FLAT, not contracting. Only XOXNO LSD contracting confirmed.",
     "DEX volume -55% during the price bounce - largest WoW drop in tracking. Liquidity collapsed during what should have been a relief rally.",
     "Delegator drop 9x larger than last run (-447 -> -4,003). Combined with -38K staked-EGLD decline = retail capitulation during the bounce.",
     "Run #11's Binance.com 'hot wallet drawdown -36.7K' was partially an artifact of the bad-checksum address returning 0 (HTTP 400). The canonical address actually grew +24K this run, suggesting normal exchange operation continued through the period.",
     "Reward compound rate fell 61.9% -> 59.14% (mild) AND institutional claims went 100% sold (small sample of 2). Marginal bearish drift in delegator decision quality."]},
 "methodology_changes":R["meta_learning"]["methodology_changes"],
 "new_addresses_discovered":[
   {"address":"erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets",
    "label":"Binance.com hot wallet (canonical address; replaces run #11's invalid-checksum form)"}],
 "action_items_completed":[
   "DONE: Capitulation bounce check - $2.95 -> $2.99 (+1.4%) FIRST UP-WEEK after 5 down-weeks. Bounce real but on collapsing engagement.",
   "DONE: Binance Staking custody 4th-week check - STALLED 2nd consecutive week at 3.51M (5-week parked position).",
   "DONE: OTC desk reload check - desks in INTER-CYCLE GAP (combined -0.9K). Pipeline awaiting reload (run #11 predicted 1-2 weeks).",
   "DONE: Coinbase 2-week inflow confirmation - +43K then +8.3K = 2-week inflow confirmed per run #11's rule.",
   "DONE: LSD contraction follow-up - run #11 pattern downgraded (data artifact); only XOXNO LSD contracting confirmed.",
   "DONE: Hatom Lending magnitude check - not evaluable (price move +1.4% below 5% threshold for meaningful rule observation).",
   "DONE: Mega Whale erd18mv2z6r2 watch - balance UNCHANGED at 998,971. No downstream forwarding.",
   "NOT APPLICABLE: Newly-issued FRA/GSN/GTA adoption check - 0 issuances this run (system SC scan returned empty).",
   "NOT DONE: OTC funder re-trace and known-addresses canonicalization (4th run carrying)."],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":R["meta_learning"]["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":R["meta_learning"]["dashboard_suggestions_followup"],
 "self_assessment":{
   "most_valuable_insight":R["meta_learning"]["most_valuable_insight"],
   "actions_completed_count":7,"actions_attempted_count":9,
   "what_would_2x_next_week":"Build the engagement-composite indicator widget. The 'exit liquidity bounce' diagnostic relies on 4-5 metrics moving simultaneously - it's hard to spot at a glance without visualizing them together. A single composite score (or radar chart) would automatically surface this pattern in future bounces. Second-best: validate the LSD circulating-supply timeline visualization, which would be robust to the rate-limit data artifacts that bit us this run."},
 "recommendations_for_next_run":R["meta_learning"]["recommendations_for_next_run"]}
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #12; total runs",len(learn["runs"]))
print("baselines price",new_baselines["egld_price_usd"])
print("baselines delegators",new_baselines["total_delegators"])
print("baselines binance_custody",new_baselines.get("binance_staking_custody_egld"))
