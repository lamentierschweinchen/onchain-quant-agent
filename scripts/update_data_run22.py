#!/usr/bin/env python3
"""Run #22: refresh previous.json, known-addresses.json and append the learnings entry."""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D=json.load(open(f"{REPO}/data/collected/2026-08-24.json"))
R=json.load(open(f"{REPO}/reports/2026-08-24.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
learn=json.load(open(f"{REPO}/data/learnings.json"))
O=json.load(open("/tmp/run22w/derived.json"))

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
P2P_PROVIDER="erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqm8llllsyhrgzd"
WHALE_I_CP="erd1qkazru7aw5heycg7c79lwmcnnczgjj2td2dg8j574h586ahwkptq20zlgy"
UNBOND="erd1daqlaezxx22rzyxnqx5ddkykm5ajelt0hetjnstm7rxqg78xqusqazv9ms"

new_prev={
 "snapshot_date":"2026-08-24",
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
 # NET one-way, WEEKLY frame. NOTE (run #22, NARROWING run #21's blanket rule): weekly nets
 # are accurate UNLESS a wave straddles a week boundary. The July episode (Jul 6-27) re-netted
 # feed-to-drain is 829,863 vs 833,754 summed weekly - 0.47% apart. The August wave straddles
 # and overstates by 47.7%. Test the wave; do not assume the frame.
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
 "unbonding_in_flight":R["staking_intelligence"]["unbonding_in_flight"],
 "watch_addresses":[
  {"address":UNBOND,"label":"THE 229,865 EGLD UNBOND - COMPLETED AND UNWITHDRAWN. 80,279 reads userUnBondable with seconds_remaining = 0 (claimable now) and 149,585 had 5,279s left at snapshot; NEITHER has been withdrawn and the wallet sent no outbound tx in the Aug 17-24 window. None of run #21's three branches fired. RE-REGISTERED with a no-action branch: withdrawn to an exchange/OTC feeder = a 230K distribution event on a restarting pipeline; withdrawn and redelegated = rotation; still unwithdrawn after a second full week = inactive/lost-access holder, retire it as a live flow","balance_egld":b(UNBOND) or 2369.5,"weeks_tracked":2,"first_seen":"2026-08-17"},
  {"address":UPBIT_DESK,"label":f"UPbit OTC Desk (FEED RESTARTED AT SCALE: UPbit tranche 297,000 vs 14,000 last week; standing-programme branch fired at ~2x its threshold in week one. Desk at {b(UPBIT_DESK):,.0f})","balance_egld":b(UPBIT_DESK),"weeks_tracked":22,"first_seen":"2026-04-02"},
  {"address":DIST_DESK,"label":f"OTC Distribution Wallet (COMBINED DESK INVENTORY {(b(UPBIT_DESK) or 0)+(b(DIST_DESK) or 0):,.0f} EGLD, +49,292 - the HIGHEST recorded. Weekly gross 767,206, net one-way 252,109 at 67% circular, back inside the 63-80% band. More is loaded than delivered: the drain leg is still ahead)","balance_egld":b(DIST_DESK),"weeks_tracked":20,"first_seen":"2026-04-13"},
  {"address":CUSTODY,"label":f"Binance Staking custody (DRAWDOWN BRANCH FIRED, 2nd time since run #9: -300,000 in ONE traceable standard transfer into the Binance.com hot wallet on 2026-08-24, now {b(CUSTODY):,.0f}. NOT delegated - binance_staking provider took only +2,422. Pre-registered reading: drawdown to hot = distribution. NEW PRE-COMMIT: hot falling >150K next week with the OTC feed continuing = the custody drawdown funds the pipeline and the two watches are one)","balance_egld":b(CUSTODY),"weeks_tracked":16,"first_seen":"2026-05-11"},
  {"address":MEGA,"label":f"Mega Whale erd18mv2z6r2 (ZERO for a 2nd week and 3 of the last 4; balance {b(MEGA):,.0f}, unchanged to 4dp, no transactions. Read against DEX turnover tripling in the same week, the instrument itself is now suspect: one wallet is not a proxy for aggregate demand. Repair by discovering absorbers dynamically from desk outbound terminals, or retire it)","balance_egld":b(MEGA),"weeks_tracked":19,"first_seen":"2026-04-20"},
  {"address":CB_ROUTING,"label":f"Coinbase Routing Wallet (idle at {b(CB_ROUTING):,.1f} EGLD, no inbound. Second consecutive dormant week)","balance_egld":b(CB_ROUTING),"weeks_tracked":5,"first_seen":"2026-07-27"},
  {"address":WHALE_I,"label":f"Unknown Whale I - CLASSIFICATION CLOSED as OTC operator inventory. Its largest external counterparty erd1qkazru7aw5 turns out to trade almost exclusively with Whale I itself (37,188 out to it / 52,551 in from it over 30d, on a 46,629 balance, nonce 566) - a second wallet of the same operator, not an external buyer. Balance {b(WHALE_I):,.0f} (-34,622). Its +2,686 net hub take is excluded from demand. Graduating to background unless it doubles","balance_egld":b(WHALE_I),"weeks_tracked":4,"first_seen":"2026-08-03"},
  {"address":P2P_PROVIDER,"label":"p2p_org_ delegation contract - FIRST OPERATOR DEREGISTRATION IN TRACKING. unStakeNodes took stake 67,500 + topUp 2,083 to ZERO locked; 50 nodes still listed, APR 0, 1,244 delegators still attached. PRE-COMMITTED: >25% of those 1,244 leaving within two weeks = total yield loss DOES break participation inertia and the stake becomes a traceable forced-migration flow; <10% = inertia is near-absolute. Owner erd1jxuc98ud0pe7 - check for any relationship to the two 100%-fee operators","balance_egld":0.0,"weeks_tracked":1,"first_seen":"2026-08-24"},
  {"address":XOXNO_LSD,"label":f"XOXNO LSD contract (XEGLD -0.15%, third consecutive deceleration and now inside the noise band - the run #14 redemption episode is over. Graduating unless supply moves >1%)","balance_egld":b(XOXNO_LSD) or 0,"weeks_tracked":9,"first_seen":"2026-06-29"},
  {"address":SRC17,"label":f"OTC source erd17l22 (-8,452 to {b(SRC17):,.0f}; small distribution against a restarted feed it is not the source of)","balance_egld":b(SRC17),"weeks_tracked":16,"first_seen":"2026-05-11"},
  {"address":FUNDER,"label":"OTC source funder (Binance.com -> erd17l22 pass-through)","balance_egld":b(FUNDER) or 0,"weeks_tracked":14,"first_seen":"2026-05-25"},
  {"address":CUST_FUNDER,"label":"Binance de-staking withdrawal wallet erd1r3w62vq (quiet a 4th week; this week's -300,000 custody move went directly to the Binance.com hot wallet, not through this wallet)","balance_egld":b(CUST_FUNDER),"weeks_tracked":5,"first_seen":"2026-07-27"}]}
json.dump(new_prev,open(f"{REPO}/data/previous.json","w"),indent=2)
print("WROTE previous.json; top_accounts",len(top_accounts),"providers",len(staking_providers))

# ---- known-addresses.json ----
def add_addr(section,addr,name,category,subcategory,notes):
    kn.setdefault(section,{})
    if addr in kn[section]: return False
    kn[section][addr]={"name":name,"category":category,"subcategory":subcategory,"notes":notes,
                       "first_seen":"2026-08-24","discovered_run":22}
    return True
added=0
if add_addr("unlabeled_whales",WHALE_I_CP,"Unknown Whale I - second operator wallet (erd1qkazru7aw5)","whale","otc_operator_inventory",
   "Nonce 566, ~46,629 EGLD. Identified run #22 as Whale I's largest external counterparty and then resolved as the SAME operator: over 30 days it sent 37,188 EGLD to Whale I and received 52,551 from it, and essentially nothing else (its five other counterparties total ~12,800 out and ~1 in). Closes the run #20/#21 Whale I classification - both wallets are OTC operator inventory and their hub take must be excluded from the demand instruments."):
    added+=1
if add_addr("validators",P2P_PROVIDER,"p2p_org_ delegation contract (DEREGISTERED run #22)","validator","deregistered",
   "Called unStakeNodes in the 2026-08-17..2026-08-24 window, taking stake 67,500 EGLD and topUp 2,083 to ZERO locked. numNodes still reads 50, APR reads 0, and numUsers still reads 1,244 - the operator withdrew the nodes from under an intact delegator book. First operator deregistration in twenty-two runs. Owner erd1jxuc98ud0pe7lcf3c0d4x0xf25wrf63d2n80t7muyucl6ptym3hqk0252k. Detection signature: locked == 0 with numNodes > 0; the provider does NOT drop out of /providers."):
    added+=1
hub=D["otc_hub_trace"]
for addr,rec in hub["inbound"].items():
    if rec.get("kind")!="router" or rec["amount"]<15000: continue
    terms={k:v for k,v in rec["terminals"].items() if not k.startswith("UNRESOLVED")}
    src=max(terms,key=terms.get) if terms else "unknown"
    if label_map.get(addr): continue
    if add_addr("exchange_routers",addr,f"{src}->OTC Desk Feeder (run #22)","router","otc_feeder",
       f"Zero-balance pass-through carrying {rec['amount']:,.0f} EGLD from {src} into the UPbit OTC desk complex in the 2026-08-17..2026-08-24 window."):
        added+=1
for addr,rec in hub["outbound"].items():
    if rec.get("kind")!="router" or rec["amount"]<15000: continue
    terms={k:v for k,v in rec["terminals"].items() if not k.startswith("UNRESOLVED")}
    dst=max(terms,key=terms.get) if terms else "unknown"
    if label_map.get(addr): continue
    if add_addr("exchange_routers",addr,f"OTC Desk->{dst} Router (run #22)","router","otc_router",
       f"Zero-balance pass-through forwarding {rec['amount']:,.0f} EGLD from the OTC desks to {dst} in the 2026-08-17..2026-08-24 window."):
        added+=1
kn.setdefault("_metadata",{})["last_updated"]="2026-08-24"
json.dump(kn,open(f"{REPO}/data/known-addresses.json","w"),indent=2)
print("known-addresses.json: added",added)

# ---- learnings.json ----
def roll(arr,val,n=8):
    a=list(arr)+[val]
    return a[-n:] if len(a)>n else a
rbp=learn["runs"][-1]["running_baselines"]
_pct=R["pre_committed_tests"]
_res=[t for t in _pct if t.get("resolved_in_run")==22]
_res_n=len(_res); _open_n=sum(1 for t in _pct if t["status"]=="open")
_hit=100*sum(1 for t in _res if t.get("outcome")=="as_predicted")/_res_n if _res_n else 0.0
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
   "2026-08-10..2026-08-17 (run #21)":138265,
   "2026-08-03..2026-08-24 (WAVE #2 netted feed-to-drain, run #21 - the correct measure)":round(wave["net_one_way_egld"])},
 "otc_circularity_pct":{k:round(v,1) for k,v in otc["circularity_series_pct"].items()},
 "dex_turnover_ratio_pct":roll(rbp.get("dex_turnover_ratio_pct",[]),round(xxr["turnover_ratio_pct"],3)),
 "identifiable_bid_absorbed_egld_7d":roll(rbp.get("identifiable_bid_absorbed_egld_7d",[]),0.0),
 "binance_staking_custody_egld":roll(rbp.get("binance_staking_custody_egld") or [],exchange_balances["Binance Staking"]),
 "reward_compound_pct":roll(rbp.get("reward_compound_pct",[]),
   round(R["staking_intelligence"]["reward_behavior"]["compound_pct_at_function_level"],2)),
 "delegation_total_locked_egld":roll(rbp.get("delegation_total_locked_egld",[]),
   round(R["staking_intelligence"]["summary"]["total_delegated_egld"])),
 "usdt_supply":roll(rbp.get("usdt_supply",[]),round(O["tokens"]["stable"]["USDT-f8c08c"]["supply"])),
 "pre_committed_tests_resolved":roll(rbp.get("pre_committed_tests_resolved",[]),_res_n),
 "pre_committed_test_hit_rate_pct":roll(rbp.get("pre_committed_test_hit_rate_pct",[]),round(_hit,1)),
 "pre_committed_tests_open":roll(rbp.get("pre_committed_tests_open",[]),_open_n)}

entry={
 "date":"2026-08-24","run_number":22,
 "data_quality":{
   "endpoints_that_worked":R["meta_learning"]["endpoints_that_worked"],
   "endpoints_that_failed":R["meta_learning"]["endpoints_that_failed"],
   "api_quirks_discovered":R["meta_learning"]["api_quirks"],
   "data_gaps":R["meta_learning"]["data_gaps"]},
 "analysis_insights":{
   "what_worked":[
     "READING /accounts/{addr}/delegation FOR STATE, NOT JUST FOR AMOUNTS. The run #21 unbond resolved not by finding a destination but by finding a STATE the test had not imagined - userUnBondable > 0 with seconds_remaining = 0, i.e. claimable and unclaimed. That is invisible to a balance scan, invisible to a transaction scan, and invisible to the provider's locked figure. One endpoint answered a question three other instruments could not even pose.",
     "PRE-COMMITTED THRESHOLDS HELD UP UNDER A 30% PRICE MOVE. Four of five resolved as predicted, including two - the OTC feed resumption and the DEX turnover recovery - that would have been trivially easy to narrate either way after the fact. The one inconclusive resolution was informative rather than embarrassing: it identified a design flaw (destination tests need a no-action branch with a time bound) that generalises to every future watch of this shape.",
     "RE-MEASURING A METHODOLOGICAL CLAIM INSTEAD OF INHERITING IT. Run #21 established the wave-netting rule from ONE wave and generalised it. Re-netting the July episode as one window took a single collector change and showed weekly framing was accurate there (0.47% apart), which narrows the rule rather than repeating it. The model has now corrected its own correction, which is the behaviour the errata mechanism exists to support.",
     "CHECKING THE LIST ENDPOINT BEFORE DERIVING AN ESTIMATE. SWTAO's per-token price nulled through four 2.5s retries, exactly the run #14 pattern that previously forced a carry-forward estimate. The /tokens?sort=marketCap list had a live price for the same token in the same run. A measured value beat a derived one for the cost of one lookup.",
     "NETTING A SINGLE ENTITY OUT OF EVERY AGGREGATE IT TOUCHES. p2p_org_'s deregistration is 87% of the delegation TVL decline and 95% of the apparent delegator-count break. Applying the run #15/#16 decomposition rules mechanically turned two alarming headline numbers into one real event plus two artifacts.",
     "COMPUTING WHALE TIERS ON A COMMON-ADDRESS BASIS. The previous snapshot stores 60 accounts and this one holds 100; the naive comparison showed a phantom +264K mid-tier gain. Restricting to the 48 addresses present in both removed it."],
   "what_needs_improvement":[
     "THE PROVIDER JOIN KEY WAS WRONG AND IT FAILED SILENTLY. previous.json keys staking_providers by IDENTITY; the live API keys by contract address. The collector joined on address, reported 79 providers as having moved more than 20K EGLD, found zero unDelegate callers, and produced an empty unbonding pool without erroring. It was only caught because 79 movers was implausible on its face. Every cross-snapshot join in this pipeline should assert a minimum match rate.",
     "THE UNBONDING POOL COVERS TEN PROVIDERS, NOT 105. The measurement is good enough to say the residual is fully absorbed, and not good enough to decompose it. That is the difference between retiring a bad instrument and building a good one, and the run stopped at the first.",
     "THE TURNOVER FINDING IS CONFOUNDED AND THE TEST THAT REGISTERED IT DID NOT ANTICIPATE THAT. Turnover tripled in the same week as a +30% price move and a restarted OTC feed. 'Demand is repairing' and 'there was a rally' both predict it. The persistence test registered for run #23 separates them, but the original threshold should have been specified conditional on price.",
     "THE CUSTODY DRAWDOWN AND THE OTC RESTART HAPPENED IN THE SAME WEEK AND WERE NOT CONNECTED. 300,000 EGLD moved from Binance's staking custody to its hot wallet while 297,000 was fed into the desks from UPbit. The model reported both and tested neither against the other. Four queries would settle it.",
     "MEX HAS NOW BEEN 'EXPLAINED' ONCE, FALSIFIED ONCE, AND LEFT UNEXPLAINED TWICE. Two mechanisms were checked this run (supply, pool depth) and both came back negative. That is progress over run #19-#20's repeated hand-waving, but a five-week, 9.8pp relative move with no mechanism is a standing hole in the model's coverage."],
   "surprising_findings":[
     "A 30% RALLY ARRIVED WITH DISTRIBUTION, AND EVERY HOLDING-SIDE INSTRUMENT AGREED. The OTC feed restarted at 297,000, Binance's custody drew down 300,000 to hot, Hatom depositors withdrew, CDP borrowers burned 3.4% of USH, delegators compounded at the lowest rate in nine readings, and not one LSD took a measurable subscription. The only instrument pointing the other way measures trading rather than holding.",
     "THE 229,865 EGLD SIMPLY DID NOT MOVE. It completed unbonding and was not claimed. After a run that treated its destination as the single highest-value question, the answer was that its owner did nothing at all.",
     "P2P.ORG DEREGISTERED ITS NODES AND LEFT 1,244 DELEGATORS ATTACHED TO A ZERO-STAKE, ZERO-APR CONTRACT. The first operator exit in tracking, and it does not show up as a provider leaving the API - it shows up as locked = 0 with 50 nodes still listed.",
     "THE DESKS RELOADED WHILE DISTRIBUTING. Combined desk inventory rose 49,292 to a record 109,857 EGLD in the same week they pushed 252,109 net one-way to Bybit, Binance.com and Gate.io. Whatever the programme is, its supply was not exhausted by this week's delivery.",
     "RUN #21'S NETTING CORRECTION WAS ITSELF TOO STRONG. Weekly framing was accurate for the entire July episode (0.47% apart over three weeks). The 55% overstatement was a property of one wave's straddle, not of the method.",
     "THE TWO DEMAND INSTRUMENTS INVERTED AGAINST EACH OTHER. DEX turnover tripled to 10.83% while the identifiable bid read exactly zero, on a wallet whose balance did not change to four decimal places.",
     "THE TWO 100%-FEE OPERATORS SHARE NOTHING. Both owner wallets hold 1.69 EGLD, received nothing in 30 days, and sent one small transfer each - to two different unlabelled recipients. The coincidence run #21 flagged has no visible connection behind it."]},
 "methodology_changes":R["meta_learning"]["methodology_changes"],
 "new_addresses_discovered":[
   "erd1qkazru7aw5... - Unknown Whale I's SECOND OPERATOR WALLET, not an external buyer. Nonce 566, ~46,629 EGLD. Over 30 days it sent 37,188 EGLD to Whale I and received 52,551 from it and essentially transacted with nobody else. Added to known-addresses under unlabeled_whales; closes the run #20/#21 Whale I classification as OTC operator inventory.",
   "erd1qqqq...m8llllsyhrgzd (p2p_org_ delegation contract) - added under validators with subcategory 'deregistered'. Called unStakeNodes this week; locked 0, numNodes 50, numUsers 1,244, APR 0. Owner erd1jxuc98ud0pe7lcf3c0d4x0xf25wrf63d2n80t7muyucl6ptym3hqk0252k, not yet related to any other tracked entity.",
   "Additional OTC desk feeder/router wallets labelled from this week's hub trace (>15K EGLD legs), terminating at Bybit, Binance.com and Gate.io. The restarted feed brought several new zero-balance pass-throughs into the set.",
   "STILL FLAGGED, not fixed: two invalid-checksum entries in known-addresses.json (Hatom UTK Money Market, OneDex Launchpad), open since run #18. Neither is queried by the collector; a wrong replacement remains worse than a known gap."],
 "action_items_completed":[
   "DONE (run #21 rec #1): MAINTAIN THE SCOREBOARD AND ERRATA. Five of run #21's six open tests resolved (4 as predicted, 1 inconclusive), one carried open into week two, and seven new tests registered with thresholds and branches before next week's data exists. Two claims withdrawn with asserted_in_runs so the errata overlay warns on run #21. Prediction record appended to running_baselines.",
   "DONE (rec #2): WHERE DOES THE 229,865 EGLD UNBOND GO? Nowhere. Both legs completed or nearly completed unbonding and NEITHER was withdrawn; the wallet sent no outbound transaction all week. None of the three pre-registered branches covered that state, which is the finding: destination tests need an explicit no-action branch with a time bound. Re-registered accordingly.",
   "DONE (rec #3): RE-NET THE JULY EPISODE FEED-TO-DRAIN. Jul 6-27 as ONE window gives 829,863 EGLD one-way against 833,754 from summing its three weekly nets - 0.47% apart. Weekly framing was ADEQUATE for July, so run #21's blanket upper-bound rule is narrowed to waves that straddle a week boundary. The extended August wave (Aug 3-24) still overstates by 47.7%.",
   "DONE (rec #4): DO THE 100%-FEE PROVIDERS DEREGISTER? Not yet, and no branch fired at threshold - books fell 9.6% and 15.6% rather than halving, users moved -35 and -32, fee unchanged at 1.0, 50 nodes each still listed. Test stays open into week two. The owner-counterparty question IS answered: two distinct wallets, both holding 1.69 EGLD, both with zero 30-day inbound, each sending one small transfer to a DIFFERENT unlabelled recipient. No shared counterparty on the available evidence.",
   "DONE (rec #5): DOES THE OTC FEED RESUME? Yes, at nearly double its threshold and a week early - a 297,000 UPbit tranche against a ~150,000 bar, gross throughput 767,206, desks reloaded to a record 109,857. Standing-programme branch fired. Wave-window net reported alongside the weekly figure as instructed.",
   "DONE (rec #6): IS THE USDT DRAIN ONE DESK OR THE BRIDGE? One desk. Supply recovered +0.44% to 552,292 on the benign branch. Holder scan supports it: top 25 hold 82% of supply, largest is Hatom's USDT Money Market at 118,671, so a single position moves the aggregate double digits.",
   "DONE (rec #7): WHY IS MEX LEADING EGLD? Two mechanisms checked and both eliminated. MEX circulating supply moved -0.151% (6.03B tokens), three orders of magnitude too small to price a 9.8pp five-week gap; MEX/WEGLD pool depth rose to $359,078 but roughly in line with the market rather than ahead of it. The statistical claim survives, the causal one does not exist. Registered as a bounded test rather than explained a third time.",
   "DONE (rec #8): CORRECT THE DEMAND READING FOR THE RECLASSIFIED WHALE, and close the classification. Whale I's hub take (+2,686 this week) is excluded from the demand instruments, and its largest external counterparty turns out to be a second wallet of the same operator - which closes the identification rather than extending it.",
   "PARTIAL (rec #9/#10): BUILD THE UNBONDING-POOL SERIES. Built and recorded weekly for the first time: 158 distinct unDelegate callers moving 70,498 EGLD across the ten providers that moved more than 5,000, with per-leg settlement dates. NOT built across all 105 providers, so the residual can be shown to be fully absorbed but not decomposed. The first attempt failed silently on a wrong join key and is documented as an API quirk."],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":R["meta_learning"]["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":R["meta_learning"]["dashboard_suggestions_followup"],
 "self_assessment":{
   "most_valuable_insight":R["meta_learning"]["most_valuable_insight"],
   "actions_completed_count":8,"actions_attempted_count":10,
   "what_would_2x_next_week":"Resolve the unbond-withdrawal and OTC wave-#3 tests in the SAME pass, because they may be one flow: 229,865 EGLD is claimable and unclaimed at the exact moment a distribution pipeline restarted with a record 109,857 of desk inventory still loaded, and nobody has checked whether the wallet's eventual receiver appears in the desk inbound list. Second, connect the Binance custody drawdown to the pipeline - 300,000 left custody for the hot wallet in the same week 297,000 entered the desks, and four queries on the hot wallet's outbound above 10,000 EGLD would either merge two watches into one instrument or rule it out. Third, extend the unbonding pool to all 105 providers so the staked-minus-delegated residual becomes a decomposition rather than a statement that it cannot be read. Fourth, separate the turnover signal from the rally by recording volume in EGLD terms and the WEGLD/USDC pair separately, because the current reading is confounded with a +30% price week. Fifth, add a match-rate assertion to every cross-snapshot join: the provider join failed silently this run and produced 79 phantom movers before anyone noticed.",
   "pre_committed_test_for_next_run":"UNBOND WITHDRAWAL: withdrawn to an exchange/OTC feeder = a 230K distribution event on a restarting pipeline; withdrawn and redelegated = rotation; still unwithdrawn after a second full week = inactive/lost-access holder, retire it as a live flow. OTC WAVE #3: another tranche above ~150,000 = escalating toward the re-netted run #17 peak; nothing above ~50,000 = a single reload. CUSTODY: Binance.com hot falling >150,000 with the feed continuing = the custody drawdown funds the pipeline; hot flat or custody re-parked = internal rebalancing. P2P.ORG MIGRATION: >25% of the 1,244 stranded delegators leaving within two weeks = total yield loss breaks inertia; <10% = inertia is near-absolute. TURNOVER: above ~5% = a genuine regime change and the absent-bid diagnosis is retired; below 3.5% = a rally-week spike. MEX: pool TVL +10% WoW in EGLD terms or supply -1% = a mechanism; neither for a second run = label it unexplained flow and stop. COMPOUND: below 56% = systematic monetisation; above 59% = a rally-week spike. 100%-FEE PROVIDERS: carried open into week two of three."},
 "recommendations_for_next_run":R["meta_learning"]["recommendations_for_next_run"]}
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #22; total runs",len(learn["runs"]))
for k in ["egld_price_usd","otc_net_one_way_egld_7d","dex_turnover_ratio_pct","reward_compound_pct","usdt_supply"]:
    print("  baseline",k,new_baselines[k])
