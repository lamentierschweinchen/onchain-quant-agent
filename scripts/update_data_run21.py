#!/usr/bin/env python3
"""Run #21: refresh previous.json, known-addresses.json and append the learnings entry."""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D=json.load(open(f"{REPO}/data/collected/2026-08-17.json"))
R=json.load(open(f"{REPO}/reports/2026-08-17.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
learn=json.load(open(f"{REPO}/data/learnings.json"))
O=json.load(open("/tmp/run21w/derived.json"))

label_map={}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"): label_map[a]=m.get("name","Unknown")
def lab(a): return label_map.get(a,"Unknown")
acc=D["accounts"]
def b(a):
    x=acc.get(a)
    return int(x["info"]["balance"])/1e18 if x and isinstance(x.get("info"),dict) and "balance" in x["info"] else None
econ=D["economics"]; st=D["stats"]; be=D["btc_eth"]; meco=D["mex_economics"]
otc=R["whale_intelligence"]["otc_pipeline"]; wave=otc["wave_window_netting"]
sk=O["staking"]; wv=O["otc"]

# ---- previous.json ----
top_accounts=[{"address":x["address"],"balance_egld":int(x["balance"])/1e18,"label":lab(x["address"])}
              for x in D["top_accounts"][:60]]
top_tokens_by_holders=[{"identifier":t["identifier"],"name":t.get("name"),"holders":t["accounts"],
    "price_usd":t.get("price"),"supply_raw":t.get("supply"),"decimals":t.get("decimals")}
    for t in D["tokens_holders"][:25]]
top_tokens_by_volume=[{"identifier":t["identifier"],"name":t.get("name"),
    "transactions":t.get("transactions"),"holders":t.get("accounts")} for t in D["tokens_txs"][:25]]
provs=[p for p in D["providers"] if p.get("locked") and float(p["locked"])>0]
for p in provs: p["_lk"]=float(p["locked"])/1e18
provs.sort(key=lambda p:-p["_lk"])
staking_providers=[{"provider":p.get("identity") or p["provider"],"name":p.get("identity") or p["provider"],
    "locked_egld":p["_lk"],"num_delegators":p.get("numUsers"),"apr":p.get("apr"),
    "fee":p.get("serviceFee"),"num_nodes":p.get("numNodes")} for p in provs]
binance_com_addrs=["erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets",
    "erd1ylwuswz9zuk4acuq4aa6d0x9ys293yhlpwg6vpuwntndyej4u44q896zlz",
    "erd1v4ms58e22zjcp08suzqgm9ajmumwxcy4hfkdc23gvynnegjdflmsj6gmaq"]
binance_com=sum((b(a) or 0) for a in binance_com_addrs)
cb=sum((b(a) or 0) for a in ["erd16jruked88jgtsar78ej85hjp3qsd9jkjcw4swsn7k0teqh3wgcqqgyrupq",
    "erd1m9qn6gvercs6ksvtn924w4y7z9ppglyfugpu34al26t9u4mvzvqqlq9dc3",
    "erd1eae23a530qymlpvfrudzsge5wgl003wl92saax74cew7j549eqqq3jklut"])
exchange_balances={
 "Binance Staking":b("erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"),
 "Binance.com":binance_com,
 "UPbit":b("erd1fcxu3f0hlxyvnp7zvuqmf34zf5w782tst6vuqhm4dwq4ayjspdaqce0q49"),
 "Bybit":b("erd1vj3efd5czwearu0gr3vjct8ef53lvtl7vs42vts2kh2qn3cucrnsj7ymqx"),
 "Crypto.com":(b("erd1hzccjg25yqaqnr732x2ka7pj5glx72pfqzf05jj9hxqn3lxkramq5zu8h4") or 0)+
              (b("erd1qr9av6ar4ymr05xj93jzdxyezdrp6r4hz6u0scz4dtzvv7kmlldse7zktc") or 0),
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
CB_ROUTING="erd1lgdltequh7627rtlacmcp6p5vec7zmu2rxhu7pjwvcja8f4a9gqq9vcc70"
SRC17="erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh"
FUNDER="erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp"
XOXNO_LSD="erd1qqqqqqqqqqqqqpgq6uzdzy54wnesfnlaycxwymrn9texlnmyah0ssrfvk6"
CUST_FUNDER="erd1r3w62vqmsux5e38p6vnueatmfcs8nr5lmg3s97x6rafqpgxfae0sxv9z0v"
WHALE_I="erd1vd76pwhl4dyeyd8gylv6mkkvy7g4dnfezjuyp4j4x3wwnauga57q53m3z0"
UNBOND=sk["unwind"]["address"]

new_prev={
 "snapshot_date":"2026-08-17",
 "economics":{"egld_price_usd":econ["price"],"market_cap_usd":econ["marketCap"],
   "total_supply":econ["totalSupply"],"circulating_supply":econ["circulatingSupply"],
   "staked_egld":econ["staked"],"staked_ratio":econ["staked"]/econ["circulatingSupply"],
   "staking_apr":econ["apr"],"base_apr":econ["baseApr"],"topup_apr":econ["topUpApr"],
   "token_market_cap_usd":econ["tokenMarketCap"],
   "btc_price_usd":be["bitcoin"]["usd"],"eth_price_usd":be["ethereum"]["usd"]},
 "activity":{"total_accounts":st["accounts"],"total_transactions":st["transactions"],
   "epoch":st["epoch"],"blocks":st["blocks"],"shards":st["shards"]},
 "top_accounts":top_accounts,
 "top_tokens_by_holders":top_tokens_by_holders,
 "top_tokens_by_volume":top_tokens_by_volume,
 "newly_issued_tokens":[{"identifier":t["identifier"],"name":t["name"],"ticker":t["ticker"],
   "timestamp":t["timestamp"],"accounts":t["accounts"],"transactions":t["transactions"]}
   for t in D.get("newly_issued",[])],
 "staking_providers":staking_providers,
 "staking_concentration":{"hhi":R["staking_intelligence"]["concentration"]["hhi"],
   "top_5_share_pct":R["staking_intelligence"]["concentration"]["top_5_share_pct"],
   "top_10_share_pct":R["staking_intelligence"]["concentration"]["top_10_share_pct"],
   "total_locked_egld":R["staking_intelligence"]["summary"]["total_delegated_egld"]},
 "exchange_balances":exchange_balances,
 "defi_tvl":defi_tvl,
 "xexchange":{"volume_24h_usd":R["token_activity"]["xexchange"]["total_volume_24h_usd"],
   "total_pairs":meco["marketPairs"],"mex_price_usd":meco["price"],
   "mex_market_cap_usd":meco["marketCap"],
   "pool_tvl_usd":R["token_activity"]["xexchange"]["pool_tvl_usd"],
   "turnover_ratio_pct":R["token_activity"]["xexchange"]["turnover_ratio_pct"],
   "mex_pair_depth":R["token_activity"]["xexchange"]["mex_pair_depth"]},
 "lsd_supply":{tid:D["tvl_tokens"].get(tid,{}).get("supply")
   for tid in ["SEGLD-3ad2d0","XEGLD-e413ed","SWTAO-356a25","USH-111e09"]},
 # GROSS paginated throughput, net of desk-to-desk only.
 "otc_throughput_series":{k:round(v) for k,v in otc["gross_series_egld_7d"].items()},
 # NET one-way: FIVE measured anchors after this run's run #16 / #18 backfill.
 # NOTE (run #21): these are WEEKLY-frame nets and are UPPER BOUNDS - circularity crosses
 # week boundaries. Prefer the wave-window figure when a wave straddles two windows.
 "otc_net_one_way_series":{k:round(v) for k,v in otc["net_one_way_series_egld_7d"].items()},
 "otc_circularity_measured_pct":{k:round(v,1) for k,v in otc["circularity_series_pct"].items()},
 "otc_wave_window_netting":{"window":wave["window"],"gross_outbound_egld":round(wave["gross_outbound_egld"]),
   "circular_share_pct":round(wave["circular_share_pct"],1),
   "net_one_way_egld":round(wave["net_one_way_egld"]),
   "sum_of_weekly_nets_egld":round(wave["sum_of_weekly_nets_egld"]),
   "weekly_frame_overstatement_pct":round(wave["weekly_frame_overstatement_pct"],1)},
 "demand_instruments":{"dex_turnover_ratio_pct":R["token_activity"]["xexchange"]["turnover_ratio_pct"],
   "identifiable_bid_absorbed_egld_7d":0,"weeks_bid_at_zero":1,
   "weeks_bid_at_zero_in_last_four":3,
   "withdrawal_breadth_ex_pipeline":R["whale_intelligence"]["demand_instruments"]["withdrawal_breadth"]},
 "unbonding_in_flight":{"wallet":UNBOND,"total_egld":sk["unwind"]["total"],
   "legs":sk["unwind"]["legs"],"corrected_direct_node_egld":sk["corrected_direct"],
   "raw_residual_egld":sk["raw_direct_residual"]},
 "watch_addresses":[
  {"address":UNBOND,"label":f"THE 229,865 EGLD UNBOND (new, top watch): unDelegated 149,585 from p2p_org_ (Aug 15) and 80,279 from erd1qqqq...pvhlllls6yl73z (Aug 14), both zero-value txs with the amount in the data field. Unbonding completes in ~7 and ~6 days, i.e. inside the next window. PRE-COMMITTED: destination a delegation contract = rotation/neutral; an exchange or OTC feeder = a 230K distribution event larger than this week's entire OTC one-way; staying in wallet = idiosyncratic","balance_egld":2253.5,"weeks_tracked":1,"first_seen":"2026-08-17"},
  {"address":UPBIT_DESK,"label":f"UPbit OTC Desk (WAVE #2 STOPPED FEEDING: UPbit tranche 14,000 vs 319,000 last week, -96%, and the desks returned 130,000 to UPbit. Desk at {b(UPBIT_DESK):,.0f})","balance_egld":b(UPBIT_DESK),"weeks_tracked":21,"first_seen":"2026-04-02"},
  {"address":DIST_DESK,"label":f"OTC Distribution Wallet (combined desk balance {(b(UPBIT_DESK) or 0)+(b(DIST_DESK) or 0):,.0f}, -3,229. Weekly gross 222,532, weekly net one-way 138,265 at only 38% circular - but the WAVE-window net (Aug 3-17) is 210,922 at 74% circular, so weekly nets are upper bounds)","balance_egld":b(DIST_DESK),"weeks_tracked":19,"first_seen":"2026-04-13"},
  {"address":CUSTODY,"label":f"Binance Staking custody (RE-PARKED: +118,440 from Binance.com hot in one traceable transfer on 2026-08-14, now {b(CUSTODY):,.0f}, -37,110 from the 3,512,650 peak. NOT delegated - the binance_staking provider moved only +18,577. Same shape as the runs #7-#10 accumulation phase that ended in a drawdown. Branches unchanged: delegation = constructive, drawdown to hot = distribution)","balance_egld":b(CUSTODY),"weeks_tracked":15,"first_seen":"2026-05-11"},
  {"address":MEGA,"label":f"Mega Whale erd18mv2z6r2 (BACK TO ZERO: no transactions at all, balance {b(MEGA):,.0f}. Run #20's reactivation was a maintenance transfer exactly as the sub-10K branch pre-registered. Dormancy revived as structural - absent in 3 of the last 4 weeks. Threshold for calling the bid back is unchanged at a 30-50K tranche)","balance_egld":b(MEGA),"weeks_tracked":18,"first_seen":"2026-04-20"},
  {"address":CB_ROUTING,"label":f"Coinbase Routing Wallet (idle again at {b(CB_ROUTING):,.1f} EGLD after last week's 5,764 refill and forward. The bid pipe exists but was not used this week)","balance_egld":b(CB_ROUTING),"weeks_tracked":4,"first_seen":"2026-07-27"},
  {"address":WHALE_I,"label":f"Unknown Whale I - RECLASSIFIED as OTC operator inventory (run #20's 60% test cleared). 30d trace with the raised page cap: 661/562 txs, 103/66 distinct counterparties, 68.9% of inbound value and 55.7% of outbound value with hub desks/routers/feeders, 62.5% combined. Its hub take is NOT demand. Balance {b(WHALE_I):,.0f}. NEXT: identify its largest external counterparty erd1qkazru7aw5 (27,216 in / 41,970 out over 30d)","balance_egld":b(WHALE_I),"weeks_tracked":3,"first_seen":"2026-08-03"},
  {"address":XOXNO_LSD,"label":f"XOXNO LSD contract (REDEMPTION TRACED AND BENIGN: XEGLD -0.80% and decelerating; the contract has zero outbound value txs so the trace ran through the 8 unDelegate/withdraw callers - 80-600 EGLD each, 531 EGLD into native delegation, ZERO to exchanges. Graduating unless supply moves >1%)","balance_egld":b(XOXNO_LSD) or 0,"weeks_tracked":8,"first_seen":"2026-06-29"},
  {"address":SRC17,"label":"OTC source erd17l22 (inventory parked, not pushing)","balance_egld":b(SRC17),"weeks_tracked":15,"first_seen":"2026-05-11"},
  {"address":FUNDER,"label":"OTC source funder (Binance.com -> erd17l22 pass-through)","balance_egld":b(FUNDER) or 0,"weeks_tracked":13,"first_seen":"2026-05-25"},
  {"address":CUST_FUNDER,"label":"Binance de-staking withdrawal wallet erd1r3w62vq (quiet a 3rd week; the Aug 14 custody reload came from Binance.com hot directly, not from this wallet)","balance_egld":b(CUST_FUNDER),"weeks_tracked":4,"first_seen":"2026-07-27"}]}
json.dump(new_prev,open(f"{REPO}/data/previous.json","w"),indent=2)
print("WROTE previous.json; top_accounts",len(top_accounts),"providers",len(staking_providers))

# ---- known-addresses.json ----
def add_addr(section,addr,name,category,subcategory,notes):
    kn.setdefault(section,{})
    if addr in kn[section]: return False
    kn[section][addr]={"name":name,"category":category,"subcategory":subcategory,"notes":notes,
                       "first_seen":"2026-08-17","discovered_run":21}
    return True
added=0
if add_addr("unlabeled_whales",UNBOND,"Delegation unwinder erd1daqlaezxx22rzy (229,865 EGLD)","whale","delegation_unwind",
   "Nonce 55, balance ~2,254 EGLD. unDelegated 149,585 from p2p_org_ on 2026-08-15 and 80,279 from erd1qqqq...pvhlllls6yl73z on 2026-08-14, both as zero-value txs with the amount in the data field; both confirmed unbonding via /accounts/{addr}/delegation. Historically received ~110 EGLD/day reward drips from erd1l23apusdq4j6jc and forwarded 12,100-15,000 EGLD chunks to erd1g4dlmma7zmt7ye (nonce 7, zero balance). This single wallet explains 97% of run #21's delegation TVL decline and the entire staked-minus-delegated residual flip."):
    added+=1
hub=D["otc_hub_trace"]
for addr,rec in hub["inbound"].items():
    if rec.get("kind")!="router" or rec["amount"]<15000: continue
    terms={k:v for k,v in rec["terminals"].items() if not k.startswith("UNRESOLVED")}
    src=max(terms,key=terms.get) if terms else "unknown"
    if label_map.get(addr): continue
    if add_addr("exchange_routers",addr,f"{src}->OTC Desk Feeder (run #21)","router","otc_feeder",
       f"Zero-balance pass-through carrying {rec['amount']:,.0f} EGLD from {src} into the UPbit OTC desk complex in the 2026-08-10..2026-08-17 window."):
        added+=1
for addr,rec in hub["outbound"].items():
    if rec.get("kind")!="router" or rec["amount"]<15000: continue
    terms={k:v for k,v in rec["terminals"].items() if not k.startswith("UNRESOLVED")}
    dst=max(terms,key=terms.get) if terms else "unknown"
    if label_map.get(addr): continue
    if add_addr("exchange_routers",addr,f"OTC Desk->{dst} Router (run #21)","router","otc_router",
       f"Zero-balance pass-through forwarding {rec['amount']:,.0f} EGLD from the OTC desks to {dst} in the 2026-08-10..2026-08-17 window."):
        added+=1
kn.setdefault("_metadata",{})["last_updated"]="2026-08-17"
json.dump(kn,open(f"{REPO}/data/known-addresses.json","w"),indent=2)
print("known-addresses.json: added",added)

# ---- learnings.json ----
def roll(arr,val,n=8):
    a=list(arr)+[val]
    return a[-n:] if len(a)>n else a
rbp=learn["runs"][-1]["running_baselines"]
sr=econ["staked"]/econ["circulatingSupply"]
xxr=R["token_activity"]["xexchange"]
new_baselines={
 "egld_price_usd":roll(rbp["egld_price_usd"],econ["price"]),
 "dex_volume_24h_usd":roll(rbp["dex_volume_24h_usd"],xxr["total_volume_24h_usd"]),
 "staked_egld":roll(rbp["staked_egld"],econ["staked"]),
 "mex_price_usd":roll(rbp["mex_price_usd"],meco["price"]),
 "total_delegators":roll(rbp["total_delegators"],R["staking_intelligence"]["churn"]["total_delegators_current"]),
 "staked_ratio":roll(rbp["staked_ratio"],sr),
 "exchange_net_flow_egld":roll(rbp["exchange_net_flow_egld"],R["whale_intelligence"]["exchange_flows"]["net_change_egld"]),
 "otc_pipeline_throughput_egld_7d":roll(rbp["otc_pipeline_throughput_egld_7d"],round(otc["gross_outbound_egld_7d"])),
 # WEEKLY-frame net one-way. Run #21 established these are UPPER BOUNDS (circularity
 # crosses week boundaries); the wave-netted figure lives in otc_wave_window_netting.
 "otc_net_one_way_egld_7d":roll(rbp.get("otc_net_one_way_egld_7d",[]),round(otc["net_one_way_egld_7d"])),
 "otc_net_one_way_measured_windows":{
   "2026-07-06..2026-07-13 (run #16, backfilled run #21)":round(otc["net_one_way_series_egld_7d"]["run16"]),
   "2026-07-13..2026-07-20 (run #17 peak, re-netted run #20)":round(otc["peak_window_renetted"]["net_one_way_egld"]),
   "2026-07-20..2026-07-27 (run #18, backfilled run #21)":round(otc["net_one_way_series_egld_7d"]["run18"]),
   "2026-07-27..2026-08-03 (run #19)":61435,
   "2026-08-03..2026-08-10 (run #20)":round(otc["net_one_way_series_egld_7d"]["run20"]),
   "2026-08-10..2026-08-17 (run #21)":round(otc["net_one_way_egld_7d"]),
   "2026-08-03..2026-08-17 (WAVE #2 netted feed-to-drain, run #21 - the correct measure)":round(wave["net_one_way_egld"])},
 "otc_circularity_pct":{k:round(v,1) for k,v in otc["circularity_series_pct"].items()},
 "dex_turnover_ratio_pct":roll(rbp.get("dex_turnover_ratio_pct",[]),round(xxr["turnover_ratio_pct"],3)),
 "identifiable_bid_absorbed_egld_7d":roll(rbp.get("identifiable_bid_absorbed_egld_7d",[]),0.0),
 "binance_staking_custody_egld":roll(rbp.get("binance_staking_custody_egld") or [],exchange_balances["Binance Staking"]),
 "reward_compound_pct":roll(rbp.get("reward_compound_pct",[]),
   round(R["staking_intelligence"]["reward_behavior"]["compound_pct_at_function_level"],2)),
 "delegation_total_locked_egld":roll(rbp.get("delegation_total_locked_egld",[]),
   round(R["staking_intelligence"]["summary"]["total_delegated_egld"])),
 "usdt_supply":roll(rbp.get("usdt_supply",[]),round(O["defi"]["usdt_supply"]))}

entry={
 "date":"2026-08-17","run_number":21,
 "data_quality":{
   "endpoints_that_worked":R["meta_learning"]["endpoints_that_worked"],
   "endpoints_that_failed":R["meta_learning"]["endpoints_that_failed"],
   "api_quirks_discovered":R["meta_learning"]["api_quirks"],
   "data_gaps":R["meta_learning"]["data_gaps"]},
 "analysis_insights":{
   "what_worked":[
     "PRE-COMMITTED TESTS RESOLVED CLEANLY EVEN WHEN THEY FAILED TO FIRE. Run #20 registered five tests with numeric thresholds. The OTC escalation test (net >300K on a tranche >350K) missed on both legs and the feed collapsed -96%; the bid test resolved on its sub-10K/zero branch; the XEGLD destination test landed on the constructive branch; the whale-I 60% counterparty test was cleared. None of these required a post-hoc reading, and the one that could not be resolved cleanly (the weekly net figure sitting between the escalation and collapse thresholds) is what exposed the netting-frame bug.",
     "RAISING THE PAGE CAP AND LOGGING CAP TERMINATIONS WORKED FIRST TIME. max_pages 40 completed the whale-I 30-day trace (661/562 txs) with an empty page-cap log, which turned a two-run 'profiled but not identified' item into a resolved reclassification.",
     "TRACING THROUGH THE CALLERS WHEN A CONTRACT HAS NO OUTBOUND VALUE TXS. The XOXNO LSD contract settles via SC results, so the destination question was answered by enumerating unDelegate/withdraw callers and following their onward flows instead - 8 wallets, 80-600 EGLD each, zero exchange destinations. The same technique is what resolved the delegation unwind.",
     "READING /accounts/{addr}/delegation. This endpoint is what turned a three-run mystery into an artifact: userUndelegatedList gives amount and seconds remaining per contract, which makes in-flight unbonding measurable and shows the staked-minus-delegated residual to be a direct-node PLUS unbonding figure.",
     "VERIFYING AN IMPLAUSIBLE FIELD ON THREE ENDPOINTS BEFORE NARRATING IT. serviceFee=1.0 with apr=0 on two providers looked like an indexer artifact; /providers, /providers?identity= and /providers/{address} all agreed, and the owners differ, so the finding could be stated without hedging."],
   "what_needs_improvement":[
     "THE WEEKLY NETTING FRAME WAS WRONG AND THE MODEL SHIPPED IT FOR THREE RUNS. Circularity crosses week boundaries, so every weekly net one-way figure is an upper bound; wave #2 netted feed-to-drain is 210,922 against 326,924 from summing its two weekly nets. This was discoverable the moment a return leg exceeded a feed in the same week, and the 38% circularity reading this week was the tell.",
     "THREE PUBLISHED CLAIMS WERE WITHDRAWN THIS RUN (the direct-node unwind, the competitive fee cut, MEX stale pricing). All three shared a mechanism: a quantity was reported before the cheapest available check was run. The MEX one is the least defensible - the pair's TVL was already in the collected snapshot for two runs.",
     "THE CORRECTED DIRECT-NODE FIGURE CANNOT BE BACKFILLED. /accounts/{addr}/delegation is point-in-time, so the runs #18-#20 residuals cannot be decomposed retroactively; the honest position is that they are unreliable rather than inverted. A prospective unbonding-pool series (10-20 queries/run) would have prevented the whole episode.",
     "WHY TWO UNRELATED PROVIDERS SET A 100% FEE IN THE SAME WEEK IS UNEXPLAINED. The owners differ and neither was traced further, which leaves a coincidence sitting inside a high-severity finding."],
   "surprising_findings":[
     "A 55% MEASUREMENT ERROR IN THE MODEL'S HEADLINE SERIES. Wave #2 is 210,922 EGLD of one-way movement netted feed-to-drain, not the 326,924 its weekly figures sum to, because UPbit fed 319,000 in one window and took 130,000 back in the next.",
     "THE 'DIRECT-NODE UNWIND' NEVER HAPPENED. One wallet's 229,865 EGLD unDelegate pair explains this week's entire +282,713 residual flip; corrected, direct-node stake GREW +52,848, and the prior three weeks' readings are equally consistent with earlier unbondings completing.",
     "TWO PROVIDERS SET THEIR SERVICE FEE TO 100%, ZEROING DELEGATOR APR - one of them the provider run #20 celebrated for cutting 24% -> 15% a week earlier. Different owners, 50 nodes each still running, both still bleeding stake.",
     "A ZERO-YIELD SIGNAL MOVED CAPITAL BUT NOT PEOPLE. egldstakingprovider lost 26% of its book at a 100% fee while its user count fell by 13 of ~1,124 - the cleanest demonstration of participation inertia the model has produced, because the incentive to leave was absolute.",
     "MEX/WEGLD IS THE #2 DEEPEST POOL ON xEXCHANGE ($291,459, 15.9% of all depth, 125 trades/24h). The 'stale pricing in illiquid pairs' explanation used in two prior runs was wrong, and MEX has now matched or beaten EGLD for four consecutive weeks with no mechanism identified.",
     "BRIDGED USDT FELL 15.42% IN ONE WEEK (100,287 tokens), four times the prior worst weekly contraction - the only instrument this week pointing against the price action.",
     "EGLD ROSE 3% WITH THE IDENTIFIABLE BID AT LITERALLY ZERO. The absorber and its feeder pipe recorded no transactions at all, and the price rose anyway once the OTC feed switched off - which is direct evidence that the marginal seller, not the marginal buyer, has been setting this price."]},
 "methodology_changes":R["meta_learning"]["methodology_changes"],
 "new_addresses_discovered":[
   "erd1daqlaezxx22rzy... - the delegation unwinder: nonce 55, ~2,254 EGLD, unDelegated 149,585 from p2p_org_ and 80,279 from erd1qqqq...pvhlllls6yl73z within 24 hours of each other, both unbonding. Explains 97% of the delegation TVL decline and the entire residual flip. Added to known-addresses under unlabeled_whales and to watch_addresses as the top item.",
   "Additional OTC desk feeder/router wallets labelled from this week's hub trace (>15K EGLD legs), terminating at UPbit, Binance.com, Bybit and Gate.io.",
   "STILL FLAGGED, not fixed: two invalid-checksum entries in known-addresses.json (Hatom UTK Money Market, OneDex Launchpad). Neither is queried by the collector."],
 "action_items_completed":[
   "DONE (run #20 rec #1): DOES WAVE #2 ESCALATE TO PEAK SCALE? No. The UPbit tranche fell -96% to 14,000 against a 350,000 threshold and the desks returned 130,000 to UPbit; the wave netted feed-to-drain is 210,922, about 51% of the re-netted run #17 peak. The attempt to answer this at the weekly level is what exposed the netting-frame error, which is the run's biggest result. UPbit's replenishment source was also found and it is circular: its 30-day inbound is led by the desks and their own feeders, so there is no external source to trace.",
   "DONE (rec #2): TRACE THE DIRECT-NODE UNWIND. Resolved as a measurement artifact rather than a flow. The protocol Staking SC is not queryable for transactions (HTTP 400 on every variant), but /accounts/{addr}/delegation showed one wallet holding 229,865 EGLD in unbonding across two providers, which accounts for the entire residual. Corrected direct-node stake grew +52,848. The three-run narrative is withdrawn.",
   "DONE (rec #3): TRACE THE XEGLD REDEMPTION DESTINATION. Constructive branch. The LSD contract has zero outbound value txs, so the trace ran through 8 unDelegate/withdraw callers: onward flows of 80-600 EGLD each, 531 EGLD into native delegation contracts, ZERO to any labelled exchange. Supply decelerated to -0.80%.",
   "DONE (rec #4): DID THE FEE CUT WORK? Emphatically not - and the question was mis-specified. egldstakingprovider went 15% -> 100% and procryptostaking 20% -> 100%, both zeroing delegator APR, both still bleeding. Run #20's 'first competitive fee cut' reading is withdrawn; a fee change is not evidence of competition.",
   "DONE (rec #5): DOES THE BID SCALE UP OR WAS IT MAINTENANCE? Maintenance. Zero absorption, zero transactions on both the absorber and the Coinbase Routing pipe - exactly the pre-registered branch that revives the dormancy finding as structural.",
   "DONE (rec #6): FINISH IDENTIFYING 'Unknown Whale I'. Page cap raised to 40, trace completed without truncation, and the 60% threshold is cleared (68.9% inbound / 55.7% outbound / 62.5% combined with hub infrastructure). Reclassified as OTC operator inventory; its hub take is no longer counted as demand.",
   "DONE (rec #7): BACKFILL THE NET ONE-WAY SERIES. Run #16 (1,100,791 gross = 309,197 one-way, 72% circular) and run #18 (312,870 = 114,877, 63%) both re-netted, giving five measured anchors and confirming roughly constant circularity. Also revealed that run #16's gross_in exceeded its gross_out, the signature of a straddling wave - which is why the July episode should now be re-netted feed-to-drain too.",
   "DONE (rec #8): CHECK MEX PAIR DEPTH DIRECTLY. Falsified the model's own explanation: MEX/WEGLD holds $291,459 (15.9% of all xExchange depth, #2 deepest pool) on 125 trades/24h. Not stale pricing."],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":R["meta_learning"]["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":R["meta_learning"]["dashboard_suggestions_followup"],
 "self_assessment":{
   "most_valuable_insight":R["meta_learning"]["most_valuable_insight"],
   "actions_completed_count":8,"actions_attempted_count":8,
   "what_would_2x_next_week":"Resolve the 229,865 EGLD unbond, which lands inside the next window and is larger than this week's entire OTC one-way figure - its destination (delegation contract, exchange, or the wallet itself) is the single most consequential unknown the model currently has, and the query is trivial. Second, re-net the July episode (runs #16-#18) feed-to-drain rather than weekly: run #16's gross_in exceeded its gross_out, which is the same straddling signature that produced a 55% overstatement in wave #2, so the five-anchor series may still be too high. Third, start recording the unbonding pool prospectively for wallets behind provider moves above ~20K EGLD - 10-20 queries a run, and it would have prevented three runs of a wrong direct-node narrative. Fourth, stop repeating explanations: three claims were withdrawn this run and the MEX one had been checkable from the stored snapshot for two weeks.",
   "pre_committed_test_for_next_run":"UNBOND: the 229,865 EGLD arriving at a delegation contract = provider rotation, neutral; at an exchange or OTC feeder = a distribution event larger than this week's entire OTC one-way and the dominant fact of the run; staying in the wallet = idiosyncratic. OTC FEED: a fresh UPbit tranche above ~150,000 within two weeks = the July-August pattern is a standing programme; nothing above ~50,000 for two consecutive weeks = between cycles. 100%-FEE PROVIDERS: books halving again with flat user counts = retail inertia is absolute; fee reversed = an operational move; nodes deregistered = the first genuine validator exit in tracking. USDT: another >5% contraction = the bridge is draining and the ~450K remaining becomes a first-order concern; flat or positive = the -15.4% was one desk. TURNOVER: a third rise above ~3.5% with the feed still off = the demand side is genuinely repairing; below 2.5% = the bounce tracked the supply pause. MEX: a fifth week >= EGLD = a genuine relative-value signal needing a mechanism."},
 "recommendations_for_next_run":R["meta_learning"]["recommendations_for_next_run"]}
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #21; total runs",len(learn["runs"]))
for k in ["egld_price_usd","otc_net_one_way_egld_7d","dex_turnover_ratio_pct","reward_compound_pct","usdt_supply"]:
    print("  baseline",k,new_baselines[k])
