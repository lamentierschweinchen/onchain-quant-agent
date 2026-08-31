#!/usr/bin/env python3
"""Run #23: refresh previous.json, known-addresses.json and append the learnings entry."""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-08-31"
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
F=json.load(open(f"{REPO}/data/collected/followup_{RD}.json"))
R=json.load(open(f"{REPO}/reports/{RD}.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
learn=json.load(open(f"{REPO}/data/learnings.json"))
O=json.load(open("/tmp/run23w/derived.json"))

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
sk=O["staking"]; cust=O["custody"]; ub=O["unbond"]; p2p=O["p2p"]

# ---- previous.json ----
top_accounts=[{"address":x["address"],"balance_egld":int(x["balance"])/1e18,"label":lab(x["address"])}
              for x in D["top_accounts"][:100]]
top_tokens_by_holders=[{"identifier":t["identifier"],"name":t.get("name"),"holders":t["accounts"],
    "price_usd":t.get("price"),"supply_raw":t.get("supply"),"decimals":t.get("decimals")}
    for t in D["tokens_holders"][:25]]
top_tokens_by_volume=[{"identifier":t["identifier"],"name":t.get("name"),
    "transactions":t.get("transactions"),"holders":t.get("accounts")} for t in D["tokens_txs"][:25]]

# RUN #23 FIX: store the FULL /providers list, not the locked>0 subset. Two operator
# deregistrations went unreported for ten runs because a provider that goes to zero
# silently drops out of the stored comparison set and can never appear as a WoW event.
all_prov=[]
for p in D["providers"]:
    lk=float(p.get("locked",0) or 0)/1e18
    all_prov.append({"provider":p.get("identity") or p["provider"],
        "name":p.get("identity") or p["provider"],"address":p["provider"],
        "locked_egld":lk,"num_delegators":p.get("numUsers"),"apr":p.get("apr"),
        "fee":p.get("serviceFee"),"num_nodes":p.get("numNodes")})
all_prov.sort(key=lambda x:-x["locked_egld"])
staking_providers=all_prov

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
BINANCE_HOT="erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets"
MEGA="erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"
CB_ROUTING="erd1lgdltequh7627rtlacmcp6p5vec7zmu2rxhu7pjwvcja8f4a9gqq9vcc70"
SRC17="erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh"
XOXNO_LSD="erd1qqqqqqqqqqqqqpgq6uzdzy54wnesfnlaycxwymrn9texlnmyah0ssrfvk6"
P2P_PROVIDER="erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqm8llllsyhrgzd"
LEDGERBYFIGMENT="erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqppllllls9ftvxy"
STAKEDINC="erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqkhllllsx7vmg6"
UNBOND="erd1daqlaezxx22rzyxnqx5ddkykm5ajelt0hetjnstm7rxqg78xqusqazv9ms"

desks=(b(UPBIT_DESK) or 0)+(b(DIST_DESK) or 0)
new_prev={
 "snapshot_date":RD,
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
 # RUN #23: the FULL provider list (187 entries), including zero-locked ones. Storing only
 # locked>0 is why ledgerbyfigment's and stakedinc's deregistrations went unreported.
 "staking_providers":staking_providers,
 "staking_providers_note":"FULL /providers list including locked==0 entries (run #23 change). Prior snapshots stored only locked>0, which made a provider going to zero silently drop out of the WoW comparison instead of registering as an event.",
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
   "volume_24h_egld":R["token_activity"]["xexchange"]["dex_volume_egld_24h"],
   "pool_tvl_egld":R["token_activity"]["xexchange"]["pool_tvl_egld"],
   "mex_pair_depth":R["token_activity"]["xexchange"]["mex_pair_depth"]},
 "lsd_supply":{tid:D["tvl_tokens"].get(tid,{}).get("supply")
   for tid in ["SEGLD-3ad2d0","XEGLD-e413ed","SWTAO-356a25","USH-111e09"]},
 "stablecoin_supply":{"USDC-c76f1f":O["tokens"]["stable"]["USDC-c76f1f"]["supply"],
                      "USDT-f8c08c":O["tokens"]["stable"]["USDT-f8c08c"]["supply"]},
 "otc_throughput_series":{k:round(v) for k,v in otc["gross_series_egld_7d"].items()},
 "otc_net_one_way_series":{k:round(v) for k,v in otc["net_one_way_series_egld_7d"].items()},
 "otc_circularity_measured_pct":{k:round(v,1) for k,v in otc["circularity_series_pct"].items()},
 "otc_desk_inventory_series":{"run21":60565,"run22":109857,"run23":round(desks)},
 "otc_wave_window_netting":{"window":wave["window"],"gross_outbound_egld":round(wave["gross_outbound_egld"]),
   "circular_share_pct":round(wave["circular_share_pct"],1),
   "net_one_way_egld":round(wave["net_one_way_egld"]),
   "sum_of_weekly_nets_egld":round(wave["sum_of_weekly_nets_egld"]),
   "weekly_frame_overstatement_pct":round(wave["weekly_frame_overstatement_pct"],1)},
 "demand_instruments":{"dex_turnover_ratio_pct":R["token_activity"]["xexchange"]["turnover_ratio_pct"],
   "dex_volume_egld_24h":R["token_activity"]["xexchange"]["dex_volume_egld_24h"],
   "identifiable_bid_absorbed_egld_7d":0,"weeks_bid_at_zero":3,
   "weeks_bid_at_zero_in_last_four":4,
   "identifiable_bid_status":"RETIRED run #23 - all 14 desk outbound terminals scanned, none retains what it receives (1.7% of 505,597 EGLD stayed). No absorbers exist on the outbound side of the pipeline.",
   "withdrawal_breadth_ex_pipeline":R["whale_intelligence"]["demand_instruments"]["withdrawal_breadth"]},
 "unbonding_in_flight":R["staking_intelligence"]["unbonding_in_flight"],
 "deregistered_providers":[
   {"identity":"ledgerbyfigment","address":LEDGERBYFIGMENT,"num_users":3883,"num_nodes":7,
    "zero_locked_since":"2026-06-15 snapshot (run #13 window)","locked_at_deregistration_egld":170808,
    "users_at_deregistration":3961},
   {"identity":"stakedinc","address":STAKEDINC,"num_users":637,"num_nodes":10,
    "zero_locked_since":"before 2026-06-01 (whole stored archive)","locked_at_deregistration_egld":None,
    "users_at_deregistration":639},
   {"identity":"p2p_org_","address":P2P_PROVIDER,"num_users":1244,"num_nodes":0,
    "zero_locked_since":"2026-08-24 snapshot (run #22 window)","locked_at_deregistration_egld":69583,
    "users_at_deregistration":1244}],
 "watch_addresses":[
  {"address":UPBIT_DESK,"label":f"UPbit OTC Desk (RECORD INVENTORY. Combined desks {desks:,.0f} EGLD, +156,356, 2.4x the prior record - AFTER delivering 272,396 one-way. UPbit tranche series 14,000 / 297,000 / 460,000. PRE-COMMITTED: desks < 120,000 next week = the overhang was delivered and wave #3 is the largest distribution wave tracked; >= 220,000 with the feed continuing = staging still running and the delivery is ahead)","balance_egld":b(UPBIT_DESK),"weeks_tracked":23,"first_seen":"2026-04-02"},
  {"address":DIST_DESK,"label":f"OTC Distribution Wallet (at {b(DIST_DESK):,.0f}. Destinations two hops: Binance.com +117,884, Bybit +105,679, Gate.io +33,944, Bitget +4,610 - FIVE venues now. Circularity 62%, below the 63-80% band, which correctly predicted the wave straddle)","balance_egld":b(DIST_DESK),"weeks_tracked":21,"first_seen":"2026-04-13"},
  {"address":CUSTODY,"label":f"Binance Staking custody ({cust['delta']:+,.0f} to {b(CUSTODY):,.0f}, 2nd consecutive drawdown, -497K over two weeks. SENT 500,000 to the Binance.com hot wallet, which forwarded 135,003 into the OTC desks via the run #19 and #20 feeders plus one direct transfer and returned 303,242. The custody watch and the pipeline watch are ONE instrument. PRE-COMMITTED ON FLOW not balance: hot -> desks/feeders > 50,000 next week = standing programme; < 10,000 = one-off routing)","balance_egld":b(CUSTODY),"weeks_tracked":17,"first_seen":"2026-05-25"},
  {"address":BINANCE_HOT,"label":f"Binance.com hot wallet ({b(BINANCE_HOT):,.0f}, +159,709). THE NEW INSTRUMENT: it is now a desk feeder. NOTE FOR THE COLLECTOR - run #23's collector hardcoded an INVALID bech32 variant of this address, got HTTP 400 and silently reported zero outbound; the valid address is this one","balance_egld":b(BINANCE_HOT),"weeks_tracked":1,"first_seen":"2026-08-31"},
  {"address":LEDGERBYFIGMENT,"label":"ledgerbyfigment delegation contract - THE DEREGISTRATION THE MODEL MISSED FOR TEN RUNS. Went 170,808 EGLD -> 0 between the 2026-06-08 and 2026-06-15 snapshots (run #13 window), keeping 7 nodes and 3,961 delegators. Eleven weeks at 0% APR since; delegators 3,961 -> 3,883 (-2.0%). This is the longest-running participation-inertia experiment available - track its user count weekly","balance_egld":0.0,"weeks_tracked":1,"first_seen":"2026-08-31"},
  {"address":STAKEDINC,"label":"stakedinc delegation contract - zero-locked with 10 nodes and ~639 users across the ENTIRE stored archive (2026-06-01 onward). Users 639 -> 637. The limit case of participation inertia: a contract that has never paid anything in the model's memory and has lost 0.3% of its book of people","balance_egld":0.0,"weeks_tracked":1,"first_seen":"2026-08-31"},
  {"address":P2P_PROVIDER,"label":f"p2p_org_ delegation contract - EXIT COMPLETED. Owner called removeNodes x{p2p['function_counts'].get('removeNodes',0)} plus unBondNodes; numNodes 50 -> 0. 1,244 delegators still attached to a contract with zero stake, zero nodes and zero APR, and they produced {p2p['function_counts'].get('unDelegate',0)} unDelegate calls against {p2p['function_counts'].get('reDelegateRewards',0)} reDelegateRewards this week. PRE-COMMITTED (fourth-deregistration test): a FOURTH provider hitting locked==0 with users attached within four weeks = operator attrition is a trend","balance_egld":0.0,"weeks_tracked":2,"first_seen":"2026-08-24"},
  {"address":MEGA,"label":f"Mega Whale erd18mv2z6r2 - IDENTIFIABLE-BID INSTRUMENT RETIRED. Zero for a 3rd week and 4 of the last 5; balance {b(MEGA):,.0f} unchanged to 4dp, no transactions. The run #22 repair (discover absorbers dynamically from desk terminals) was attempted and returned a decisive negative: all 14 terminals are zero-balance routers retaining 1.7% of 505,597 EGLD. Kept on the list as a dormancy marker only","balance_egld":b(MEGA),"weeks_tracked":23,"first_seen":"2026-04-02"},
  {"address":CB_ROUTING,"label":f"Coinbase Routing Wallet (idle at {b(CB_ROUTING):,.1f} EGLD, third consecutive dormant week)","balance_egld":b(CB_ROUTING),"weeks_tracked":6,"first_seen":"2026-07-27"},
  {"address":UNBOND,"label":f"THE 229,865 EGLD UNBOND - RETIRED AS A LIVE FLOW. Unmoved for a second full week: balance {ub['balance']:,.2f} EGLD unchanged, {ub['pending_total']:,.0f} still unbonded-and-unclaimed inside the delegation contracts, zero outbound transactions and zero function calls. The no-action branch run #22 added to the test fires. Kept on the list at low priority in case it ever moves","balance_egld":ub["balance"],"weeks_tracked":3,"first_seen":"2026-08-17"},
  {"address":XOXNO_LSD,"label":f"XOXNO LSD contract (XEGLD -0.16%, fourth week inside the noise band - the run #14 redemption episode is closed. Graduating unless supply moves >1%)","balance_egld":b(XOXNO_LSD) or 0,"weeks_tracked":10,"first_seen":"2026-06-29"},
  {"address":SRC17,"label":f"OTC source erd17l22 (+6,002 to {b(SRC17):,.0f}; not the source of the current feed, which is UPbit and now Binance)","balance_egld":b(SRC17),"weeks_tracked":17,"first_seen":"2026-05-11"}]}
json.dump(new_prev,open(f"{REPO}/data/previous.json","w"),indent=2)
print("WROTE previous.json; top_accounts",len(top_accounts),"providers",len(staking_providers),"(FULL list incl. zero-locked)")

# ---- known-addresses.json ----
def add_addr(section,addr,name,category,subcategory,notes):
    kn.setdefault(section,{})
    if addr in kn[section]: return False
    kn[section][addr]={"name":name,"category":category,"subcategory":subcategory,"notes":notes,
                       "first_seen":RD,"discovered_run":23}
    return True
added=0
if add_addr("validators",LEDGERBYFIGMENT,"ledgerbyfigment delegation contract (DEREGISTERED, run #13 window)","validator","deregistered",
   "Went from 170,808 EGLD locked to ZERO between the 2026-06-08 and 2026-06-15 snapshots, keeping 7 nodes and 3,961 delegators. Never reported at the time; discovered run #23 by applying run #22's deregistration signature (locked==0 with nodes/users attached) backwards over the stored archive. Eleven weeks at 0% APR since, delegators 3,961 -> 3,883 (-2.0%) - the longest participation-inertia measurement available."):
    added+=1
if add_addr("validators",STAKEDINC,"stakedinc delegation contract (DEREGISTERED, pre-archive)","validator","deregistered",
   "Zero locked with 10 nodes and ~639 users across the entire stored snapshot archive (2026-06-01 onward), so its deregistration predates the model's memory. Users 639 -> 637 over thirteen weeks. Discovered run #23 alongside ledgerbyfigment."):
    added+=1
hub=D["otc_hub_trace"]
for addr,rec in hub["inbound"].items():
    if rec.get("kind")!="router" or rec["amount"]<15000: continue
    terms={k:v for k,v in rec["terminals"].items() if not k.startswith("UNRESOLVED")}
    src=max(terms,key=terms.get) if terms else "unknown"
    if label_map.get(addr): continue
    if add_addr("exchange_routers",addr,f"{src}->OTC Desk Feeder (run #23)","router","otc_feeder",
       f"Zero-balance pass-through carrying {rec['amount']:,.0f} EGLD from {src} into the OTC desk complex in the 2026-08-24..2026-08-31 window."):
        added+=1
for addr,rec in hub["outbound"].items():
    if rec.get("kind")!="router" or rec["amount"]<15000: continue
    terms={k:v for k,v in rec["terminals"].items() if not k.startswith("UNRESOLVED")}
    dst=max(terms,key=terms.get) if terms else "unknown"
    if label_map.get(addr): continue
    if add_addr("exchange_routers",addr,f"OTC Desk->{dst} Router (run #23)","router","otc_router",
       f"Zero-balance pass-through forwarding {rec['amount']:,.0f} EGLD from the OTC desks to {dst} in the 2026-08-24..2026-08-31 window. Confirmed non-absorbing by the run #23 terminal scan."):
        added+=1
kn.setdefault("_metadata",{})["last_updated"]=RD
json.dump(kn,open(f"{REPO}/data/known-addresses.json","w"),indent=2)
print("known-addresses.json: added",added)

# ---- learnings.json ----
def roll(arr,val,n=8):
    a=list(arr)+[val]
    return a[-n:] if len(a)>n else a
rbp=learn["runs"][-1]["running_baselines"]
_pct=R["pre_committed_tests"]
_res=[t for t in _pct if t.get("resolved_in_run")==23]
_res_n=len(_res); _open_n=sum(1 for t in _pct if t["status"]=="open")
_hit=100*sum(1 for t in _res if t.get("outcome")=="as_predicted")/_res_n if _res_n else 0.0
sr=econ["staked"]/econ["circulatingSupply"]
xxr=R["token_activity"]["xexchange"]
new_baselines={
 "egld_price_usd":roll(rbp["egld_price_usd"],econ["price"]),
 "dex_volume_24h_usd":roll(rbp["dex_volume_24h_usd"],xxr["total_volume_24h_usd"]),
 "dex_volume_24h_egld":roll(rbp.get("dex_volume_24h_egld",[]),round(xxr["dex_volume_egld_24h"])),
 "staked_egld":roll(rbp["staked_egld"],econ["staked"]),
 "mex_price_usd":roll(rbp["mex_price_usd"],meco["price"]),
 "total_delegators":roll(rbp["total_delegators"],R["staking_intelligence"]["churn"]["total_delegators_current"]),
 "staked_ratio":roll(rbp["staked_ratio"],sr),
 "exchange_net_flow_egld":roll(rbp["exchange_net_flow_egld"],R["whale_intelligence"]["exchange_flows"]["net_change_egld"]),
 "otc_pipeline_throughput_egld_7d":roll(rbp["otc_pipeline_throughput_egld_7d"],round(otc["gross_outbound_egld_7d"])),
 "otc_net_one_way_egld_7d":roll(rbp.get("otc_net_one_way_egld_7d",[]),round(otc["net_one_way_egld_7d"])),
 "otc_desk_inventory_egld":roll(rbp.get("otc_desk_inventory_egld",[]),round(desks)),
 "otc_net_one_way_measured_windows":{
   **(rbp.get("otc_net_one_way_measured_windows") or {}),
   "2026-08-24..2026-08-31 (run #23, weekly frame - UPPER BOUND, the wave straddles)":round(otc["net_one_way_egld_7d"]),
   "2026-08-17..2026-08-31 (WAVE #3 netted feed-to-drain, run #23 - the correct measure)":round(wave["net_one_way_egld"])},
 "otc_circularity_pct":{k:round(v,1) for k,v in otc["circularity_series_pct"].items()},
 "dex_turnover_ratio_pct":roll(rbp.get("dex_turnover_ratio_pct",[]),round(xxr["turnover_ratio_pct"],3)),
 "identifiable_bid_absorbed_egld_7d":roll(rbp.get("identifiable_bid_absorbed_egld_7d",[]),0.0),
 "binance_staking_custody_egld":roll(rbp.get("binance_staking_custody_egld") or [],exchange_balances["Binance Staking"]),
 "reward_compound_pct":roll(rbp.get("reward_compound_pct",[]),
   round(R["staking_intelligence"]["reward_behavior"]["compound_pct_at_function_level"],2)),
 "delegation_total_locked_egld":roll(rbp.get("delegation_total_locked_egld",[]),
   round(R["staking_intelligence"]["summary"]["total_delegated_egld"])),
 "usdt_supply":roll(rbp.get("usdt_supply",[]),round(O["tokens"]["stable"]["USDT-f8c08c"]["supply"])),
 "usdc_supply":roll(rbp.get("usdc_supply",[]),round(O["tokens"]["stable"]["USDC-c76f1f"]["supply"])),
 "unbonding_queue_undelegated_egld_7d":roll(rbp.get("unbonding_queue_undelegated_egld_7d",[]),round(sk["undelegated_week"])),
 "withdrawal_breadth_ex_pipeline_egld":roll(rbp.get("withdrawal_breadth_ex_pipeline_egld",[]),
   round(R["whale_intelligence"]["demand_instruments"]["withdrawal_breadth"]["total_egld_ex_pipeline"])),
 "pre_committed_tests_resolved":roll(rbp.get("pre_committed_tests_resolved",[]),_res_n),
 "pre_committed_test_hit_rate_pct":roll(rbp.get("pre_committed_test_hit_rate_pct",[]),round(_hit,1)),
 "pre_committed_tests_open":roll(rbp.get("pre_committed_tests_open",[]),_open_n)}

entry={
 "date":RD,"run_number":23,
 "data_quality":{
   "endpoints_that_worked":R["meta_learning"]["endpoints_that_worked"],
   "endpoints_that_failed":R["meta_learning"]["endpoints_that_failed"],
   "api_quirks_discovered":R["meta_learning"]["api_quirks"],
   "data_gaps":R["meta_learning"]["data_gaps"]},
 "analysis_insights":{
   "what_worked":[
     "RUNNING A NEWLY INVENTED DETECTOR BACKWARDS OVER THE ARCHIVE. Run #22 built the deregistration signature and published 'the first in tracking' the same week. Applying that signature to the stored snapshots took one loop and found two earlier cases, the larger of which - ledgerbyfigment, 170,808 EGLD and 3,961 delegators - had been invisible for ten runs. The archive is where a new detector's false-negative rate is measurable, and checking it is nearly free.",
     "SCANNING ALL 107 PROVIDER CONTRACTS INSTEAD OF THE MOVERS. Run #22's ten-provider partial found 70,498 EGLD of unDelegations; the full set found 151,443 from 300 wallets. The partial was not slightly incomplete, it was missing more than half, and there was no way to know that without doing the full scan once.",
     "MEASURING THE DEMAND INSTRUMENT'S REPAIR RATHER THAN ASSUMING IT. The proposal was to discover absorber wallets dynamically from the desks' outbound terminals. Scanning all 14 showed every one is a zero-balance router retaining 1.7% of what passes through, so the instrument cannot be repaired that way and is retired. A decisive negative is a better outcome than a plausible-looking replacement.",
     "REPORTING VENUE THROUGHPUT IN EGLD AS WELL AS USD. One extra division showed that the DEX turnover ratio held only because both numerator and denominator scaled with a +6.4% price - EGLD volume actually fell 4.3%. This closed run #22's stated confound in a single line.",
     "SPECIFYING THE CUSTODY QUESTION AS A FLOW TRACE. Seventeen runs of watching a balance produced ambiguity every time. Following the hot wallet's outbound above 10,000 EGLD and testing the receivers against the desk inbound list answered it in one pass: 135,003 EGLD into the desks through two feeders already in the address book.",
     "RAISING THE PAGE CAP FOR EXCHANGE HOT WALLETS. Run #22's recommendation eliminated page-cap terminations from the withdrawal-breadth scan entirely, so the raw figure is a genuine 7-day total for the first time rather than a caveated lower bound."],
   "what_needs_improvement":[
     "AN INVALID HARDCODED ADDRESS PRODUCED A CONFIDENT WRONG ANSWER. collect_run23.py carried a Binance hot wallet with a bad bech32 checksum. It returned HTTP 400, the pagination helper broke on the error dict and returned an empty list, and the collector printed '0 outbound recipients >=10K' - which, taken at face value, would have resolved a pre-committed test on evidence that did not exist. The pre-flight validator covers the JSON data files and not the collector source.",
     "THE PAGINATION HELPER TREATS AN ERROR AS AN EMPTY WINDOW. Three separate findings were nulled this run by `if not isinstance(batch, list) or not batch: break`. An HTTP 400 and a genuinely quiet week are indistinguishable to every downstream consumer. This is the same class of silent failure the methodology has now logged four times in different clothes.",
     "THE RUN EXCEEDED THE API's RATE LIMIT AND DID NOT KNOW IT. The all-provider scan pushed past roughly 800 requests and started drawing HTTP 429s on unrelated queries. A fixed 0.22s delay is not a rate-limit strategy; the followup pass with exponential backoff hit zero errors.",
     "THE PROVIDER SCAN STILL HITS ITS PAGE CAP ON THE BUSIEST CONTRACTS, so the 151,443 EGLD unbonding figure is a lower bound on exactly the providers where most unbonding happens - the same shape of error the full-set scan was meant to fix.",
     "TWO CONSECUTIVE RUNS HAVE LOST A TEST TO A SPECIFICATION DEFECT. Run #22's unbond test had no no-action branch; this run's compound-rate test had a gap between its branches. Both failures were in how the test was written, not in what happened. A test that cannot resolve costs a week."],
   "surprising_findings":[
     "THE DESKS DELIVERED A RECORD AND RELOADED TO A BIGGER RECORD IN THE SAME WEEK. 272,396 EGLD one-way out, and inventory still ended +156,356 at 266,213 - more than the entire run #17 peak wave delivered. The pipeline accumulated faster than it distributed, which has not happened before in tracking.",
     "RUN #22's HEADLINE WAS WRONG BY TWO CASES AND TEN RUNS. ledgerbyfigment deregistered in the run #13 window with 170,808 EGLD and 3,961 delegators and nobody noticed, because previous.json only ever stored providers with locked > 0.",
     "FOUR WALLETS CALLED reDelegateRewards ON p2p_org_ THIS WEEK - compounding rewards on a contract with zero stake, zero nodes and zero APR. Whatever participation inertia is, it is not merely passive.",
     "EGLD ROSE 6.39% WHILE BOTH MAJORS FELL, in the same week the largest staged supply position in tracking was assembled. The two facts are hard to hold together and the report does not pretend to reconcile them.",
     "THE ABSORBER SCAN FOUND NOTHING AT ALL. Not a weak signal - 14 of 14 terminals are zero-balance routers, and 1.7% of half a million EGLD stayed anywhere near the pipeline's exit. The demand side of this pipeline has no visible holders.",
     "BINANCE IS FEEDING THE DESKS. For twenty-three runs UPbit was the sole net source; this week Binance's hot wallet, funded by a 500,000 custody drawdown, pushed 135,003 EGLD in through feeders the model had already labelled in runs #19 and #20."]},
 "methodology_changes":R["meta_learning"]["methodology_changes"],
 "new_addresses_discovered":[
   "erd1qqqq...ppllllls9ftvxy (ledgerbyfigment delegation contract) - added under validators/deregistered. 170,808 EGLD -> 0 in the run #13 window with 7 nodes and 3,961 delegators; eleven weeks at 0% APR since, now 3,883 users. The single most valuable address added this run: it is the longest-running participation-inertia experiment available.",
   "erd1qqqq...qkhllllsx7vmg6 (stakedinc delegation contract) - added under validators/deregistered. Zero-locked with 10 nodes and ~639 users across the entire stored archive; its deregistration predates the model's memory.",
   "Binance.com hot wallet erd1sdsl...gdsv6sets recorded in previous.json watch_addresses with an explicit note that run #23's collector hardcoded an INVALID variant of it, so the next run does not repeat the bug.",
   "New OTC desk feeder/router wallets labelled from this week's hub trace (>15K EGLD legs), terminating at Binance.com, Bybit, Gate.io and - for the first time - Bitget. All confirmed non-absorbing by the terminal scan.",
   "STILL FLAGGED, not fixed: two invalid-checksum entries in known-addresses.json (Hatom UTK Money Market, OneDex Launchpad), open since run #18."],
 "action_items_completed":[
   "DONE (run #22 rec #1): MAINTAIN THE SCOREBOARD AND ERRATA. All 8 of run #22's open tests resolved - 7 as predicted, 1 inconclusive on a specification defect - and 7 new tests registered with contiguous branches before the data existed. Two claims withdrawn with asserted_in_runs so the errata overlay warns on run #22. Prediction record appended to running_baselines.",
   "DONE (rec #2): POST-DEPLOY RENDER CHECK. Added to the publish sequence: after the manifest and deploy, the live URL is loaded in a headless browser and the console is read for errors. This is the check both schema layers cannot perform, and it is what run #22 asked for.",
   "DONE (rec #3): RESOLVE THE UNBOND AND WAVE #3 TOGETHER. The unbond did not move for a second week - balance unchanged, zero outbound transactions, zero function calls - so the no-action branch fires and it is retired as a live flow. Wave #3 escalated to a 460,000 UPbit tranche, 3x its threshold. They are not the same flow.",
   "DONE (rec #4): TRACE P2P.ORG'S 1,244 STRANDED DELEGATORS. 2 unDelegate calls in the window (0.16%) against 4 reDelegateRewards and 6 claimRewards on a dead contract; the owner completed the exit with removeNodes x11 plus unBondNodes. The owner erd1jxuc98ud0pe7 has no visible relationship to the two 100%-fee operators. Far more importantly the question got two much longer natural experiments attached to it - ledgerbyfigment and stakedinc.",
   "DONE (rec #5): BUILD THE UNBONDING QUEUE ACROSS ALL PROVIDERS. All 107 contracts with locked>0 or nodes>0 paged for unDelegate: 300 distinct callers, 151,443 EGLD, 2.1x the ten-provider partial. Measured pending 132,392 across the 45 largest callers.",
   "DONE (rec #6): SEPARATE THE TURNOVER SIGNAL FROM THE RALLY. DEX volume and pool TVL now recorded in EGLD as well as USD, and WEGLD/USDC split out from the rest. The separation immediately mattered: turnover held above its regime threshold while EGLD volume fell 4.3%.",
   "DONE (rec #7): STOP EXPLAINING MEX AND START BOUNDING IT. Both mechanism branches measured and both failed - supply -0.070% against a 1% bar, MEX/WEGLD pool depth +0.83% in EGLD terms against a 10% bar. Labelled unexplained flow and closed; the streak also broke this week.",
   "DONE (rec #8): RETIRE OR REPAIR THE IDENTIFIABLE-BID INSTRUMENT. Repair attempted properly - all 14 desk outbound terminals scanned for retention - and returned a decisive negative (1.7% of 505,597 EGLD retained, every terminal a zero-balance router). Retired.",
   "DONE (rec #9): WATCH THE HATOM RESPONSE RATIO FOR A SECOND SUB-0.30 READING. It did not come: this up-week returned 0.69 against a 0.28 last week, so the capacity-exhaustion claim is withdrawn and the rule survives with four up-week confirmations.",
   "DONE (rec #10): ADD A PAGE-CAP BUDGET FOR THE BREADTH SCAN. Raised to 30 pages for exchange hot wallets. Zero page-cap terminations in the breadth scan this run - the raw figure is a full 7-day total for the first time.",
   "DONE (rec #11): CHECK WHETHER THE BINANCE 300,000 REACHES THE DESKS. It does. The hot wallet forwarded 135,003 EGLD into the desks through the run #19 and run #20 feeders plus one direct transfer. The custody watch and the pipeline watch are one instrument from here. (This is also the item that exposed the invalid hardcoded address, since the first attempt returned zero.)"],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":R["meta_learning"]["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":R["meta_learning"]["dashboard_suggestions_followup"],
 "self_assessment":{
   "most_valuable_insight":R["meta_learning"]["most_valuable_insight"],
   "actions_completed_count":11,"actions_attempted_count":11,
   "what_would_2x_next_week":"Fix the two silent-failure classes this run exposed, because they are cheap and they are the difference between a report and a plausible-looking report. (1) Extend scripts/validate_addresses.py to grep erd1 literals out of scripts/*.py - roughly twenty lines, and it would have caught the invalid Binance hot wallet that produced a confidently wrong '0 outbound recipients >=10K'. (2) Make the pagination helper distinguish an HTTP error from an empty window and add exponential backoff on 429 - three findings were nulled this run by a helper that cannot tell those apart. Everything else in the report is a judgement call; these two are defects.",
   "pre_committed_test_for_next_run":"DESK INVENTORY DRAIN: desks below ~120,000 = the record overhang was delivered and wave #3 is the largest distribution wave in tracking; at or above ~220,000 with the feed continuing = staging is still running and the delivery is ahead. BINANCE DESK FEED (specified on FLOW, not balance): hot -> desks/feeders above ~50,000 = a standing funding programme; below ~10,000 = one-off routing. FOURTH DEREGISTRATION: a fourth provider reaching locked==0 with users attached within four weeks = operator attrition is a trend."},
 "recommendations_for_next_run":R["meta_learning"]["recommendations_for_next_run"]}
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #23; total runs",len(learn["runs"]))
for k in ["egld_price_usd","otc_net_one_way_egld_7d","otc_desk_inventory_egld","dex_turnover_ratio_pct","dex_volume_24h_egld","reward_compound_pct","pre_committed_test_hit_rate_pct"]:
    print("  baseline",k,new_baselines[k])
