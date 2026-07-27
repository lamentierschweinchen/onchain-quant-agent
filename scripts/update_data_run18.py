#!/usr/bin/env python3
"""Run #18: refresh previous.json and append the learnings entry."""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D=json.load(open(f"{REPO}/data/collected/2026-07-27.json"))
R=json.load(open(f"{REPO}/reports/2026-07-27.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
learn=json.load(open(f"{REPO}/data/learnings.json"))

label_map={}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"):
                label_map[a]=m.get("name","Unknown")
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
binance_com_addrs=[
    "erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets",
    "erd1ylwuswz9zuk4acuq4aa6d0x9ys293yhlpwg6vpuwntndyej4u44q896zlz",
    "erd1v4ms58e22zjcp08suzqgm9ajmumwxcy4hfkdc23gvynnegjdflmsj6gmaq"]
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

UPBIT_DESK="erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
DIST_DESK="erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
CUSTODY="erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"
MEGA="erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"
KUCOIN="erd1ty4pvmjtl3mnsjvnsxgcpedd08fsn83f05tu0v5j23wnfce9p86snlkdyy"
CB_ROUTER="erd1eae23a530qymlpvfrudzsge5wgl003wl92saax74cew7j549eqqq3jklut"
SRC17="erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh"
FUNDER="erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp"
XOXNO_LSD="erd1qqqqqqqqqqqqqpgq6uzdzy54wnesfnlaycxwymrn9texlnmyah0ssrfvk6"
CUST_FUNDER="erd1r3w62vqmsux5e38p6vnueatmfcs8nr5lmg3s97x6rafqpgxfae0sxv9z0v"

new_prev={
 "snapshot_date":"2026-07-27",
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
 "lsd_supply":{tid:D["tvl_tokens"].get(tid,{}).get("supply") for tid in ["SEGLD-3ad2d0","XEGLD-e413ed","SWTAO-356a25","USH-111e09"]},
 # run #18: the paginated, inter-desk-netted 7d throughput series. Runs #13-#15 were backfilled
 # with the identical method this run; the method reproduces run #16's independent 1,100,791
 # exactly. Runs <= #12 are NOT backfillable and are excluded - do not extend this array backwards.
 "otc_throughput_series":{"run13":66128,"run14":186124,"run15":506053,"run16":1100791,
                          "run17":1284688,"run18":313173},
 "watch_addresses":[
   {"address":UPBIT_DESK,"label":"UPbit OTC Desk (EXHAUSTED: drained to 32,109; no UPbit reload for the first time in the cycle - watch for a fresh large tranche = wave #2 staging)","balance_egld":b(UPBIT_DESK),"weeks_tracked":18,"first_seen":"2026-04-02"},
   {"address":DIST_DESK,"label":"OTC Distribution Wallet (EXHAUSTED: drained to 29,387; combined desk balance 61,495, through the 80K exhaustion trigger; 7d throughput 313,173, -76%)","balance_egld":b(DIST_DESK),"weeks_tracked":16,"first_seen":"2026-04-13"},
   {"address":CUSTODY,"label":"Binance Staking custody (RELOADED +150,000 to 3,357,101 - the three-leg de-staking programme (-305,549) broke; watch for a 2nd reload leg = accumulation resuming)","balance_egld":b(CUSTODY),"weeks_tracked":12,"first_seen":"2026-05-11"},
   {"address":CUST_FUNDER,"label":"Binance custody reload funder erd1r3w62vq (nonce 8, holds 2 EGLD - pure pass-through; sent the 150,000 to custody. TRACE ITS 14d INBOUND to find the true origin)","balance_egld":None,"weeks_tracked":1,"first_seen":"2026-07-27"},
   {"address":MEGA,"label":"Mega Whale erd18mv2z6r2 (IDLE: zero value txs, flat at 1,093,312; the one identifiable large bid stopped entirely in the week price fell 10%)","balance_egld":b(MEGA),"weeks_tracked":15,"first_seen":"2026-04-20"},
   {"address":CB_ROUTER,"label":"Coinbase Routing Wallet (DRAINED to 77 EGLD - the pipe that filled the Mega Whale absorber in runs #15 and #17 is dry; a refill = the bid returning)","balance_egld":b(CB_ROUTER),"weeks_tracked":1,"first_seen":"2026-07-27"},
   {"address":KUCOIN,"label":"KuCoin canonical (RESOLVED BEARISH: retained the whale's 145,443 deposit, -2.6% only, so it was sold into the book. NOTE: run #17's watch entry used an INVALID-checksum address - this is the correct one)","balance_egld":b(KUCOIN),"weeks_tracked":2,"first_seen":"2026-07-20"},
   {"address":SRC17,"label":"OTC source erd17l22 (upstream feeder of the desk pipeline; 322,681, -3,519 - still loaded but not pushing)","balance_egld":b(SRC17),"weeks_tracked":12,"first_seen":"2026-05-11"},
   {"address":FUNDER,"label":"OTC source funder (Binance.com -> erd17l22 pass-through)","balance_egld":b(FUNDER) or 0,"weeks_tracked":10,"first_seen":"2026-05-25"},
   {"address":XOXNO_LSD,"label":"XOXNO LSD contract (XEGLD supply REVERSED -2.70% to 236,486, ending two growth weeks; XOXNO remains the LSD leg that redeems on weakness)","balance_egld":b(XOXNO_LSD) or 0,"weeks_tracked":5,"first_seen":"2026-06-29"}]}
json.dump(new_prev,open(f"{REPO}/data/previous.json","w"),indent=2)
print("WROTE previous.json; top_accounts",len(top_accounts),"providers",len(staking_providers))

# ---- learnings.json append ----
def roll(arr,val,n=8):
    a=list(arr)+[val]
    return a[-n:] if len(a)>n else a
rbprev=learn["runs"][-1]["running_baselines"]
sr_cur=econ["staked"]/econ["circulatingSupply"]
# run #18: REPLACE the otc throughput baseline outright. The stored array mixed desk-balance
# deltas (runs <=#16) with one true paginated figure (run #17), so z-scores against it were
# meaningless. It is now the backfilled, method-consistent series for runs #13-#18 only.
otc_series=[66128,186124,506053,1100791,1284688,313173]
new_baselines={
 "egld_price_usd":roll(rbprev["egld_price_usd"],econ["price"]),
 "dex_volume_24h_usd":roll(rbprev["dex_volume_24h_usd"],R["token_activity"]["xexchange"]["total_volume_24h_usd"]),
 "staked_egld":roll(rbprev["staked_egld"],econ["staked"]),
 "mex_price_usd":roll(rbprev["mex_price_usd"],meco["price"]),
 "total_delegators":roll(rbprev["total_delegators"],R["staking_intelligence"]["churn"]["total_delegators_current"]),
 "staked_ratio":roll(rbprev["staked_ratio"],sr_cur),
 "exchange_net_flow_egld":roll(rbprev.get("exchange_net_flow_egld",[]),R["whale_intelligence"]["exchange_flows"]["net_change_egld"]),
 "otc_pipeline_throughput_egld_7d":otc_series,
 "binance_staking_custody_egld":roll(rbprev.get("binance_staking_custody_egld") or [],exchange_balances["Binance Staking"]),
 "reward_compound_pct":roll(rbprev.get("reward_compound_pct",[]),round(R["staking_intelligence"].get("reward_behavior",{}).get("compound_pct_at_function_level",58.81),2))}

entry={
 "date":"2026-07-27","run_number":18,
 "data_quality":{
   "endpoints_that_worked":R["meta_learning"]["endpoints_that_worked"],
   "endpoints_that_failed":R["meta_learning"]["endpoints_that_failed"],
   "api_quirks_discovered":R["meta_learning"]["api_quirks"],
   "data_gaps":R["meta_learning"]["data_gaps"]},
 "analysis_insights":{
   "what_worked":[
     "Implementing the paginated throughput fix AND backfilling runs #13-#15 in the same run paid off immediately: the corrected series (66,128 / 186,124 / 506,053 / 1,100,791 / 1,284,688 / 313,173) shows a five-week escalation and a break, a structure completely invisible in the old truncated figures. The backfill validates itself by reproducing run #16's independently derived 1,100,791 exactly.",
     "Pre-committed readings did their job for the third run in a row. Three separate tests registered in run #17 (OTC reload vs exhaustion, KuCoin persistence, USH leverage chase) all resolved cleanly against their pre-registered branches, with no room to retrofit the interpretation to the outcome. Two resolved constructive and one bearish, which is itself evidence the pre-commitment is not just confirming a house view.",
     "The run #15 decompose-before-labeling rule prevented a manufactured signal. The headline +166,978 exchange inflow reads bearish; 94% of it is the Binance custody reload plus a phantom from a wallet with no prior-week balance. True external flow is +9,983 - flat. Without the decomposition this run would have reported a second bearish inflow week that did not happen.",
     "Building the bech32 pre-flight validator (open since run #12) found four broken addresses immediately, including three nobody knew about. Cheap, one-off, and it converts a silent failure mode into a loud one.",
     "Supply-first LSD/stablecoin reporting again separated signal from denominator noise: every DeFi leg is down in USD purely because price fell 10%, while the supply view shows Hatom LSD flat, XEGLD redeeming and USH de-levering - three different behaviours that a USD table would have flattened into one."],
   "what_needs_improvement":[
     "The model is instrumented almost entirely on the supply side (desks, custody, exchange balances, routers) and this week every one of those switched off while price fell 10%. There was no comparable demand-side instrumentation to substitute, so the strongest demand observations (absorber idle, DEX volume -61% on rising TVL, stablecoin burn resuming) had to be assembled ad hoc from three different sections.",
     "Phantom flows from newly-tracked or partially-tracked addresses have now caused errors two runs running (Coinbase Custody 2 in run #17, a third Binance.com wallet this run). The entity-netting code should assert that every address contributing to a current-week entity total also has a prior-week balance, and exclude it loudly otherwise.",
     "The otc_pipeline_throughput baseline was silently mixing desk-balance deltas with throughput figures, so any z-score computed against it was meaningless. It was replaced this run, but the general lesson is that a baseline array whose UNITS change mid-series is worse than no baseline - the schema should record what each baseline measures.",
     "The Binance custody reload's origin is one hop beyond this run's tracing (a nonce-8 pass-through). High-value flows arriving from pass-through wallets should trigger an automatic one-more-hop query rather than being left for next run."],
   "surprising_findings":[
     "EGLD fell 10.13% while BTC ROSE 1.71% and ETH ROSE 5.35%. Prior decoupling weeks (runs #11, #13) happened against flat or falling majors; falling double digits against a rising tape is a materially stronger chain-specific weakness signal and is the first of its kind in tracking.",
     "Every traceable supply channel switched off in the same week - OTC throughput -76% with no desk reload, Binance custody reversing to a +150,000 reload, true exchange flow flat - and price fell anyway. The supply framework that explained runs #14-#17 simply does not apply, which forces the diagnosis onto the demand side.",
     "The Mega Whale absorber recorded ZERO value transactions and the Coinbase Routing wallet that fed it is down to 77 EGLD. The question run #17 asked was whether its clip size would grow or stay ~50K; it went to nothing, in precisely the week it was most needed.",
     "DEX volume collapsed 61% while pool TVL and WEGLD supply ROSE. Depth stayed and trading left - the opposite composition from a distribution week, which produces high volume. This is the clearest single measurement of an absent bid the pipeline has produced.",
     "The bilateral inverse rule produced its strongest reading ever (ratio 0.98), falsifying run #11's hypothesis that depositor dip-buying capacity was being permanently exhausted by the prolonged decline. It was cyclical. Depositors were the one cohort that showed up this week.",
     "Hatom's two legs moved in opposite directions: lending deposits surged in EGLD terms (+9.89%) while USH CDP borrowers de-levered (-2.60% supply). Same protocol, same week, opposite risk appetite between depositors and borrowers.",
     "The delegator base moved by SIX accounts across a week in which price fell 10%. Six flat weeks now span a +24% rally and its reversal - participation on this chain is genuinely inert with respect to price, in both directions."]},
 "methodology_changes":R["meta_learning"]["methodology_changes"],
 "new_addresses_discovered":[
   "erd1r3w62vqmsux5e38p6vnueatmfcs8nr5lmg3s97x6rafqpgxfae0sxv9z0v - nonce-8 pass-through wallet holding 2 EGLD that sent the +150,000 Binance Staking custody reload. Not yet labelled in known-addresses (its own funder is unresolved); added to watch_addresses for a one-hop inbound trace next run.",
   "CORRECTION, not a discovery: run #17's KuCoin watch entry (erd1ty4pvmjtl3mnsjvnsxqkm3xqm4dm7ppgz9sh4nk4tqvlmw0jyggqzn4mdc) is an invalid-checksum address returning HTTP 400. The canonical KuCoin wallet already in known-addresses is erd1ty4pvmjtl3mnsjvnsxgcpedd08fsn83f05tu0v5j23wnfce9p86snlkdyy; previous.json now carries the correct one.",
   "CORRECTION: known-addresses.json system_contracts held an invalid Delegation Manager address (erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqyllllslmq4y); replaced with the canonical erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqylllslmq6y6 (verified HTTP 200).",
   "FLAGGED, not fixed: two further invalid-checksum entries remain in known-addresses.json - defi_hatom 'Hatom: UTK Money Market' (erd1qqqqqqqqqqqqqpgqta0tv8d5pjzmwzshrtw62n4nww9kxtl278sssypgmrs) and defi_onedex 'OneDex: Launchpad' (erd1qqqqqqqqqqqqqpgqxjj6tyrnrdegga4j66s20wql5e9ksq0hmvlscg8r3m), both HTTP 400. Neither is queried directly by the current collector so no figure is affected, but they must be re-derived from the protocol's deployer rather than guessed."],
 "action_items_completed":[
   "DONE: REBUILD THE OTC THROUGHPUT SERIES WITH PAGINATION. collect_run18.py now pages to the after= boundary by default for both desks in both directions and nets out desk-to-desk transfers. The runs #13-#15 windows were re-queried with the identical method (66,128 / 186,124 / 506,053), and re-measuring the run #16 window reproduces 1,100,791 exactly, which validates the backfill. The learnings baseline array was replaced outright because it had been mixing desk-balance deltas with throughput.",
   "DONE: DO THE DESKS RELOAD? No - resolved on the CONSTRUCTIVE branch of the pre-commitment. Desks fell to 61,495 (through the 80K trigger), throughput collapsed 76% to 313,173, and critically UPbit sent no fresh tranche after last week's 364,000. Desk inbound was essentially all desk-to-desk shuffling.",
   "DONE: KUCOIN RESOLUTION. Resolved BEARISH per the pre-commitment - KuCoin retained the deposit (175,929 -> 171,338, -2.6%) with tiny native flows, so the whale's 145,443 was sold into the book rather than withdrawn or OTC-settled. The wallet's inbound history was also traced: a 90-day window shows no funding, so it was a long-dormant holder capitulating, not an OTC recipient.",
   "DONE: IS EGLD A LAGGARD ON THE DOWNSIDE TOO? Confirmed and exceeded. The test assumed a macro down week would be needed; instead EGLD fell 10.13% while BTC +1.71% and ETH +5.35% both ROSE. The +24% recovery is formally reclassified as a bear-market rally.",
   "DONE: BINANCE CUSTODY 4TH LEG? No - the programme REVERSED. A single +150,000 transfer took custody to 3,357,101, recovering about half the -305,549 three-leg drawdown. The binance_staking delegation provider stayed flat (-228), so neither leg is shedding.",
   "DONE: DOES DEFI LEVERAGE RESUME OR UNWIND? Unwound, on the bearish branch of the registered test. Price rolled over 10.13% and USH burned 2.60%, past the 1% threshold that re-activates the run #11 de-leveraging rule, confirming the run #16 +6.49% mint as a chase. XEGLD also reversed 2.70%.",
   "DONE: PARTICIPATION BREADTH, WEEK 6. The base was flat a sixth week (174,341, +6), meeting the promotion criterion run #17 pre-registered. Participation inertia is now recorded as a structural finding rather than a weekly observation, and the watch item is retained only to catch a genuine break out of the ~174.3K band.",
   "DONE: MEGA WHALE ABSORPTION SCALE. Answered, in the least expected way: the clip size neither grew nor held at ~50K - the absorber recorded zero value transactions and the Coinbase Routing pipe feeding it drained to 77 EGLD. The related sub-question (is the Coinbase Routing pipe fed from the OTC desks?) could not be tested because no flow occurred; carried forward.",
   "BONUS, closing a run #12 recommendation open for six runs: built scripts/validate_addresses.py, a bech32 pre-flight check over every address in known-addresses.json and previous.json. It found four invalid entries on the first run, including the KuCoin watch address that would otherwise have silently returned nothing for this week's resolution test."],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":R["meta_learning"]["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":R["meta_learning"]["dashboard_suggestions_followup"],
 "self_assessment":{
   "most_valuable_insight":R["meta_learning"]["most_valuable_insight"],
   "actions_completed_count":8,"actions_attempted_count":8,
   "what_would_2x_next_week":"Instrument the demand side. This run's central finding is that every supply channel the model tracks went quiet while price fell 10%, and the framework had nothing of equal rigour to put in its place - the demand evidence (absorber idle, DEX volume collapsing on rising TVL, stablecoin burn resuming) had to be assembled by hand from three sections. Three concrete additions would double the report's explanatory power: (1) a standing 'identifiable bid' metric combining the Coinbase Routing wallet balance and the Mega Whale delta; (2) a per-pair TVL/volume depth ratio from mex/pairs so 'depth held, trading left' becomes measured rather than inferred; (3) a withdrawal-breadth count of distinct addresses receiving >1,000 EGLD from exchanges, as a retail-accumulation proxy. Second priority: resolve the Binance custody reload origin one hop back, since whether it is internal re-parking or external accumulation changes the read on the strongest bullish structural signal available.",
   "pre_committed_test_for_next_run":"If price stabilises or recovers while OTC throughput stays quiet, this week was a liquidity air-pocket and the supply exhaustion is genuinely constructive. If price keeps falling with no traceable distribution to point at, the chain has a structural bid problem and the supply-side model must be demoted from primary explanation to supporting evidence."},
 "recommendations_for_next_run":R["meta_learning"]["recommendations_for_next_run"]}
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #18; total runs",len(learn["runs"]))
print("baselines price",new_baselines["egld_price_usd"])
print("baselines compound",new_baselines["reward_compound_pct"])
print("baselines otc",new_baselines["otc_pipeline_throughput_egld_7d"])
print("baselines custody",new_baselines["binance_staking_custody_egld"])
