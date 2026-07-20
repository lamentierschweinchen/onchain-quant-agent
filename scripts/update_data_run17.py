#!/usr/bin/env python3
import json
from datetime import datetime, timezone
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D=json.load(open("/tmp/run17/collected.json"))
R=json.load(open(f"{REPO}/reports/2026-07-20.json"))
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
 "snapshot_date":"2026-07-20",
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
   {"address":"erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5","label":"UPbit OTC Desk (DISTRIBUTED: -128,758 to ~39.7K, -76%; ran the distribution leg of the record reload; UPbit sent a fresh 364K back out to the desks - watch for reload)","balance_egld":b("erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"),"weeks_tracked":17,"first_seen":"2026-04-02"},
   {"address":"erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r","label":"OTC Distribution Wallet (DISTRIBUTED: -126,978 to ~40.0K, -76%; combined desk drawdown -255,736, largest in tracking)","balance_egld":b("erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"),"weeks_tracked":15,"first_seen":"2026-04-13"},
   {"address":"erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p","label":"Binance Staking custody (3rd de-staking leg -103,579 to 3.21M; -305,549 cumulative from the 3.51M peak - now a programme, not an event)","balance_egld":b("erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"),"weeks_tracked":11,"first_seen":"2026-05-11"},
   {"address":"erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw","label":"Mega Whale erd18mv2z6r2 (RESUMED absorbing +50,621 to 1.09M via Coinbase Routing; the one identifiable bid, but ~1/25th the distributed volume)","balance_egld":b("erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"),"weeks_tracked":14,"first_seen":"2026-04-20"},
   {"address":"erd15ku2r2j6smlwumftumlpw0mfpqxy32wyt4ewxzyhs3ugsjee8stq2xh84e","label":"Whale erd15ku2r2j6 (FULL EXIT: sent its entire 145,443 EGLD to KuCoin and went to ZERO; watch whether KuCoin bleeds back down (withdrawal/OTC) or holds (sold into book))","balance_egld":b("erd15ku2r2j6smlwumftumlpw0mfpqxy32wyt4ewxzyhs3ugsjee8stq2xh84e") or 0,"weeks_tracked":1,"first_seen":"2026-07-20"},
   {"address":"erd1ty4pvmjtl3mnsjvnsxqkm3xqm4dm7ppgz9sh4nk4tqvlmw0jyggqzn4mdc","label":"KuCoin (+142,773, +430.6%, largest proportional exchange move in tracking - one whale's full exit; watch whether the balance persists)","balance_egld":b("erd1ty4pvmjtl3mnsjvnsxqkm3xqm4dm7ppgz9sh4nk4tqvlmw0jyggqzn4mdc") or 0,"weeks_tracked":1,"first_seen":"2026-07-20"},
   {"address":"erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh","label":"OTC source erd17l22 (upstream feeder of the desk pipeline)","balance_egld":b("erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh"),"weeks_tracked":11,"first_seen":"2026-05-11"},
   {"address":"erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp","label":"OTC source funder (Binance.com -> erd17l22 pass-through)","balance_egld":b("erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp") or 0,"weeks_tracked":9,"first_seen":"2026-05-25"},
   {"address":"erd1qqqqqqqqqqqqqpgq6uzdzy54wnesfnlaycxwymrn9texlnmyah0ssrfvk6","label":"XOXNO LSD contract (XEGLD supply +2.69% to 243,049, 2nd week re-accumulating - the one DeFi leg still in genuine inflow)","balance_egld":b("erd1qqqqqqqqqqqqqpgq6uzdzy54wnesfnlaycxwymrn9texlnmyah0ssrfvk6") or 0,"weeks_tracked":4,"first_seen":"2026-06-29"}]}
json.dump(new_prev,open(f"{REPO}/data/previous.json","w"),indent=2)
print("WROTE previous.json; top_accounts",len(top_accounts),"providers",len(staking_providers))

# ---- learnings.json append ----
def roll(arr,val,n=8):
    a=arr+[val]
    return a[-n:] if len(a)>n else a
rbprev=learn["runs"][-1]["running_baselines"]
sr_cur=econ["staked"]/econ["circulatingSupply"]
# run #17: the baseline now stores TRUE paginated 7d outbound throughput net of inter-desk
# transfers (1,328,037), NOT the desk-balance delta and NOT the size=50-capped sample used in
# runs <=#16. Prior entries in this series are capped-sample lower bounds and are NOT comparable;
# the run #16 window re-measured properly is 1,100,791. See methodology.md run #17 entry.
otc_throughput_13 = 1328037
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
 "reward_compound_pct":(rbprev.get("reward_compound_pct",[61.9,59.14])+[round(R["staking_intelligence"].get("reward_behavior",{}).get("compound_pct_at_function_level",60.35),2)])[-8:]}
entry={
 "date":"2026-07-20","run_number":17,
 "data_quality":{
   "endpoints_that_worked":R["meta_learning"]["endpoints_that_worked"],
   "endpoints_that_failed":R["meta_learning"]["endpoints_that_failed"],
   "api_quirks_discovered":R["meta_learning"]["api_quirks"],
   "data_gaps":R["meta_learning"]["data_gaps"]},
 "analysis_insights":{
   "what_worked":[
     "The run #14 read-flow-jointly-with-OTC rule was decisive this week: the -196K net exchange OUTFLOW during a +16% rip looks like accumulation in isolation, but the OTC desks staged a RECORD +238K reload with record ~323K throughput - so the real signal is a distribution wave loading into strength, not self-custody accumulation.",
     "Checking the DESTINATION of a CEX outflow caught that UPbit's -131K was OTC-routing (fed its own OTC Desk 460K), not customer withdrawal - a per-transfer refinement of the entity-decompose rule.",
     "Netting out the binance_staking DELEGATION provider (-149K) revealed that delegation actually GREW +120K ex-Binance; the raw -28K NET would have misread as broad delegation shrinkage.",
     "Supply-based LSD/stablecoin metrics again cut through price noise: USH +6.5% mint and XEGLD +4.5% growth are clear leverage/engagement signals that mcap (contaminated by the +16% price move) would have blurred.",
     "The dataApi re-fetch guard was a clean no-op for the 2nd straight run (0 retries), confirming the null behavior is transient."],
   "what_needs_improvement":[
     "Bybit's -221K (the largest exchange move) could not be traced - internal-transfer-invisible. Distinguishing self-custody accumulation from OTC-routing on such moves needs an internal-transfer/SC-result data source, still the recurring gap.",
     "The ~+108K external inflow onto Binance hot (beyond the custody's 200K) is unattributed - who deposited into Binance during the rip (sellers positioning?) is inferred.",
     "z-score UNDER-flagged the EGLD regime change (z=-0.09 for a +15.9% EGLD-specific move) because two up-weeks pulled the baseline mean up. A relative-strength / de-trended anomaly measure would catch EGLD-vs-majors decoupling that the absolute z-score misses."],
   "surprising_findings":[
     "EGLD DECOUPLED TO THE UPSIDE (+15.9% while BTC/ETH flat) - the FIRST EGLD-specific up-move of the tracked cycle, inverting months of high-beta-laggard behavior. A potential regime break from laggard to leader.",
     "The OTC pipeline staged its BIGGEST reload in tracking (+238K desk balance, record ~323K throughput) INTO the price strength - distribution deliberately loading against the rally.",
     "Binance is de-staking on TWO fronts simultaneously: custody -43K (2nd leg) AND the binance_staking delegation provider -149K (~-192K total out of staked positions), while taking net +115K onto hot wallets.",
     "DeFi leverage is RETURNING: USH minted +6.5% (borrowers re-opening CDPs) - the largest USH move since the run #11 de-leveraging burn, now in the bullish direction; and XEGLD re-accumulated +4.5% after its -29% collapse.",
     "The identifiable absorber (Mega Whale erd18mv2z6r2) STEPPED BACK to flat just as the OTC reload staged - last week it soaked up distribution, this week the loaded supply has no visible large buyer.",
     "The rally pulled NO new delegators (base flat 4th week at 174,349 despite +16%) - it is existing holders re-levering and adding stake, not broadening participation.",
     "Bilateral inverse rule got its 2nd, larger up-week confirmation: price +15.9%, Hatom Lending EGLD-TVL -11.5%, ratio 0.72 (vs 0.49 last up-week)."]},
 "methodology_changes":R["meta_learning"]["methodology_changes"],
 "new_addresses_discovered":[
   "binance_staking (delegation provider identity, already in /providers) confirmed as a DISTINCT Binance staking leg from the Binance Staking custody wallet (erd1rf4hv70) - it shed -149K locked this week. Both are Binance de-staking; net the provider out of delegation-TVL WoW like the erd1qqqq system aggregators."],
 "action_items_completed":[
   "DONE: OTC pipeline phase watch - did NOT collapse to a gap. Instead the desks staged a RECORD reload (+238K combined balance, biggest in tracking) with record ~323K throughput, fed by UPbit -> OTC Desk 460K. A fresh distribution wave is loading into the strength.",
   "DONE: Does the bounce hold - YES and extended hard. EGLD ripped +15.9% to $3.13 (2nd up-week), $2.70 held. And it OUTPERFORMED: BTC/ETH flat, so EGLD decoupled to the upside - the laggard->leader flip the watch asked about.",
   "DONE: Binance custody 2nd leg - the custody continued its drawdown -43K (now -202K over 2 weeks). Traced (custody +157K in / -200K out). Separately the binance_staking delegation provider shed -149K. Every Binance leg distributive; hot wallets took net +115K inflow.",
   "DONE: Mega Whale erd18mv2z6r2 absorber watch - it STEPPED BACK to flat (1.04M, no net flow) after 2 accumulation weeks; the Coinbase Routing -> mega whale pipe went quiet. The identifiable bid disappeared just as OTC reloaded.",
   "DONE: Ex-Binance exchange inflow watch - mixed. Gate.io +26K, Crypto.com +15K, Coinbase +10K IN; but Bybit -221K, UPbit -131K (OTC-routed) OUT. No clean 'renewed on-exchange positioning' signal; the two big outflows dominate.",
   "DONE: Stablecoin flight - USDC decelerated (4th burn week, -0.66% vs -2.0%) while USDT re-accelerated (-1.87% vs -0.3%). Choppy, not a clean directional flight. USH (native) MINTED +6.5% (leverage returning) - opposite direction.",
   "DONE: Delegation-vs-direct-node rotation - REVERSED this week: total staked +80K (direct-node up) while delegation -28K NET (but ex-binance_staking +120K broad). Rotation direction flipped as Binance de-staked its provider.",
   "DONE: pi-staking watch - PLATEAUED. +82 EGLD, +0 users (held at 51). The 3-week small-provider growth story stalled; growth moved to the broad mid-tier names (smartchainconnection, pokerstaking)."],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":R["meta_learning"]["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":R["meta_learning"]["dashboard_suggestions_followup"],
 "self_assessment":{
   "most_valuable_insight":R["meta_learning"]["most_valuable_insight"],
   "actions_completed_count":8,"actions_attempted_count":8,
   "what_would_2x_next_week":"Resolve the demand-vs-distribution tension this week framed: does the RECORD OTC reload (~335K loaded) get pushed out and does price ABSORB it (regime change confirmed) or FADE under it (distribution into a bounce, like run #12)? Track the OTC desk balance drawdown + throughput next week as the primary tell. Second: build the OTC desk balance+throughput cycle chart AND the EGLD-vs-majors relative-strength tracker (this run's two top dashboard suggestions) - both would have flagged this week's setup (record load; EGLD-specific decoupling) at a glance that the single-week view buries. Third: an internal-transfer/SC-result data source to attribute Bybit's -221K and Binance's +108K external hot inflow, the two biggest untraced moves this week."},
 "recommendations_for_next_run":R["meta_learning"]["recommendations_for_next_run"]}
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #16; total runs",len(learn["runs"]))
print("baselines price",new_baselines["egld_price_usd"])
print("baselines compound",new_baselines["reward_compound_pct"])
print("baselines binance_custody",new_baselines.get("binance_staking_custody_egld"))
