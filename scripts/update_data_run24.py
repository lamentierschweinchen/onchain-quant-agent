#!/usr/bin/env python3
"""Run #24: refresh previous.json, known-addresses.json and append the learnings entry."""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-09-07"
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
R=json.load(open(f"{REPO}/reports/{RD}.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
learn=json.load(open(f"{REPO}/data/learnings.json"))
O=json.load(open("/tmp/run24w/derived.json"))

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
zsc=O["zero_stake_cohort"]; em=O["emerging_lsd"]; jex=O["jex"]
HOT=O["hot_to_pipe"]; FEED=O["feeders_in"]; br=O["breadth"]
dser={d["identity"]:d for d in O["dereg_series"]}

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
 # BOTH bases: token supply AND delegated stake. JWLEGLD's 25,073 supply is a 1:1
 # deposit token against 1,799 EGLD actually delegated, and LEGLD appreciates, so
 # supply alone is not a TVL proxy for these protocols.
 "lsd_supply_emerging":{t:em[t]["supply"] for t in em},
 "lsd_staked_emerging":{(p_.get("known_label") or p_["address"]):p_.get("staked_egld")
                        for p_ in json.load(open(f"{REPO}/data/collected/liquid_staking_discovery_{RD}.json"))["liquid_staking_protocols"]
                        if (p_.get("staked_egld") or 0) >= 100},
 "stablecoin_supply":{"USDC-c76f1f":O["tokens"]["stable"]["USDC-c76f1f"]["supply"],
                      "USDT-f8c08c":O["tokens"]["stable"]["USDT-f8c08c"]["supply"]},
 "otc_throughput_series":{k:round(v) for k,v in otc["gross_series_egld_7d"].items()},
 "otc_net_one_way_series":{k:round(v) for k,v in otc["net_one_way_series_egld_7d"].items()},
 "otc_circularity_measured_pct":{k:round(v,1) for k,v in otc["circularity_series_pct"].items()},
 "otc_desk_inventory_series":{"run21":60565,"run22":109857,"run23":266213,"run24":round(desks)},
 "otc_wave_window_netting":{"window":wave["window"],"gross_outbound_egld":round(wave["gross_outbound_egld"]),
   "circular_share_pct":round(wave["circular_share_pct"],1),
   "net_one_way_egld":round(wave["net_one_way_egld"]),
   "sum_of_weekly_nets_egld":round(wave["sum_of_weekly_nets_egld"]),
   "weekly_frame_overstatement_pct":round(wave["weekly_frame_overstatement_pct"],1)},
 "demand_instruments":{"dex_turnover_ratio_pct":R["token_activity"]["xexchange"]["turnover_ratio_pct"],
   "dex_volume_egld_24h":R["token_activity"]["xexchange"]["dex_volume_egld_24h"],
   "identifiable_bid_absorbed_egld_7d":0,"weeks_bid_at_zero":4,
   "weeks_bid_at_zero_in_last_four":4,
   "identifiable_bid_status":f"RETIRED (run #23, reconfirmed run #24 on a corrected measure). The 14 desk outbound terminals took {O['absorbers']['total_received']:,.0f} EGLD and ended the week holding {O['absorbers']['total_balance_held']:,.0f} between them. Run #23's received-minus-forwarded retention figure compared a multi-week inflow against a one-week outflow and is not usable; balance is the correct test.",
   "withdrawal_breadth_ex_pipeline":R["whale_intelligence"]["demand_instruments"]["withdrawal_breadth"]},
 "unbonding_in_flight":R["staking_intelligence"]["unbonding_in_flight"],
  "deregistered_providers":[
   {"identity":"ledgerbyfigment","address":LEDGERBYFIGMENT,
    "num_users":dser.get("ledgerbyfigment",{}).get("users"),"num_nodes":7,
    "zero_locked_since":"2026-06-15 snapshot (run #13 window)","locked_at_deregistration_egld":170808,
    "users_at_deregistration":3961},
   {"identity":"stakedinc","address":STAKEDINC,
    "num_users":dser.get("stakedinc",{}).get("users"),"num_nodes":10,
    "zero_locked_since":"before 2026-06-01 (whole stored archive)","locked_at_deregistration_egld":None,
    "users_at_deregistration":639},
   {"identity":"p2p_org_","address":P2P_PROVIDER,
    "num_users":dser.get("p2p_org_",{}).get("users"),"num_nodes":0,
    "zero_locked_since":"2026-08-24 snapshot (run #22 window)","locked_at_deregistration_egld":69583,
    "users_at_deregistration":1244}],
 "zero_stake_cohort":{
   "contracts":zsc["contracts"],"attached_delegator_records":zsc["attached_delegator_records"],
   "emptied_inside_archive":[{"provider":r["provider"],"users":r["users"],
                              "last_locked_in_archive":r["last_locked_in_archive"]}
                             for r in zsc["emptied_inside_archive"]],
   "note":("Run #24: the widened signature matches 82 contracts holding 28,032 delegator records, "
           "but only four have an observed transition from locked > 0 inside the archive and only "
           "ledgerbyfigment has any activity. Deregistration means an observed transition, not a zero "
           "reading today. Quote the delegator base on the locked>0 basis.")},
 "watch_addresses":[
  {"address":UPBIT_DESK,"label":f"UPbit OTC Desk (DRAINED. Combined desks {desks:,.0f} EGLD against 266,213 last week (-64%) after delivering a record {otc['net_one_way_egld_7d']:,.0f} one-way. UPbit tranche series 297,000 / 460,000 / {otc['upbit_reload_egld']:,.0f} - the feed has plateaued. PRE-COMMITTED (wave4-restart): a tranche above ~200,000 next week = the programme is continuous and wave #4 has started; below ~50,000 with desks still under ~120,000 = wave #3 is complete and the pipeline goes quiet)","balance_egld":b(UPBIT_DESK),"weeks_tracked":24,"first_seen":"2026-04-02"},
  {"address":DIST_DESK,"label":f"OTC Distribution Wallet (at {b(DIST_DESK):,.0f}, down from 133,708. Destinations two hops: Binance.com +{[v for v in otc['venue_netting'] if v['venue']=='Binance.com'][0]['net_egld']:,.0f}, Bybit +{[v for v in otc['venue_netting'] if v['venue']=='Bybit'][0]['net_egld']:,.0f}, Gate.io +{[v for v in otc['venue_netting'] if v['venue']=='Gate.io'][0]['net_egld']:,.0f}. Circularity {otc['circular_share_pct']:.0f}%, inside the 63-80% band)","balance_egld":b(DIST_DESK),"weeks_tracked":22,"first_seen":"2026-04-13"},
  {"address":CUSTODY,"label":f"Binance Staking custody ({cust['delta']:+,.0f} to {b(CUSTODY):,.0f} - the two-week drawdown REVERSED. Sent 900,000 to the Binance.com hot wallet and took 1,272,434 back. The feed into the desks continued anyway, so the custody balance is not the funding source; the hot wallet's outbound flow is. Watch the flow, not this balance)","balance_egld":b(CUSTODY),"weeks_tracked":18,"first_seen":"2026-05-25"},
  {"address":BINANCE_HOT,"label":f"Binance.com hot wallet ({b(BINANCE_HOT):,.0f}). THE INSTRUMENT FOR THE BINANCE FEED: it sent {HOT['total_egld']:,.0f} EGLD to known OTC feeders and routers in {HOT['coverage_days']} covered days, clearing the 50,000 flow threshold. Its outbound is too busy for a 1,000-tx budget - query it in daily slices next run. PRE-COMMITTED: above ~50,000 for a third week = a permanent funding line","balance_egld":b(BINANCE_HOT),"weeks_tracked":2,"first_seen":"2026-08-31"},
  {"address":LEDGERBYFIGMENT,"label":f"ledgerbyfigment delegation contract - the only zero-stake contract of 82 with any activity. Delegators {dser.get('ledgerbyfigment',{}).get('prev_users',0):,} -> {dser.get('ledgerbyfigment',{}).get('users',0):,} ({dser.get('ledgerbyfigment',{}).get('users_delta',0):+d}) in its twelfth week at 0% APR, 85 lost of 3,961 (-2.1%). 17 unDelegate and 12 withdraw calls this week. The longest-running participation-inertia measurement available - track weekly","balance_egld":0.0,"weeks_tracked":2,"first_seen":"2026-08-31"},
  {"address":STAKEDINC,"label":f"stakedinc delegation contract - zero-locked with 10 nodes and {dser.get('stakedinc',{}).get('users',0):,} users across the ENTIRE stored archive, unchanged again this week and zero inbound transactions. The limit case: a contract that has never paid anything in the model's memory and loses nobody","balance_egld":0.0,"weeks_tracked":2,"first_seen":"2026-08-31"},
  {"address":P2P_PROVIDER,"label":f"p2p_org_ delegation contract - exit completed in run #23; {dser.get('p2p_org_',{}).get('users',0):,} delegators still attached, unchanged, producing {p2p['function_counts'].get('unDelegate',0)} unDelegate and {p2p['function_counts'].get('claimRewards',0)} claimRewards calls on a contract paying nothing. PRE-COMMITTED (fourth-deregistration, week 2 of 4): a provider transitioning from locked > 0 to zero with users attached = operator attrition is a trend","balance_egld":0.0,"weeks_tracked":3,"first_seen":"2026-08-24"},
  {"address":MEGA,"label":f"Mega Whale erd18mv2z6r2 - identifiable-bid instrument RETIRED. Zero for a fourth consecutive week; balance {b(MEGA):,.0f} unchanged to 4dp, no transactions. Kept as a dormancy marker only","balance_egld":b(MEGA),"weeks_tracked":24,"first_seen":"2026-04-02"},
  {"address":CB_ROUTING,"label":f"Coinbase Routing Wallet (idle at {b(CB_ROUTING):,.1f} EGLD, fourth consecutive dormant week)","balance_egld":b(CB_ROUTING),"weeks_tracked":7,"first_seen":"2026-07-27"},
  {"address":UNBOND,"label":f"THE 229,865 EGLD UNBOND - RETIRED, third week unmoved. Balance {ub['balance']:,.2f} EGLD unchanged, {ub['pending_total']:,.0f} still unbonded-and-unclaimed with the unbonding period long expired, zero outbound transactions. Kept at low priority in case it ever moves","balance_egld":ub["balance"],"weeks_tracked":4,"first_seen":"2026-08-17"},
  {"address":XOXNO_LSD,"label":f"XOXNO LSD contract (XEGLD {O['tokens']['lsd']['XEGLD-e413ed']['pct']:+.2f}%, fifth week without subscription. Graduating unless supply moves >1%)","balance_egld":b(XOXNO_LSD) or 0,"weeks_tracked":11,"first_seen":"2026-06-29"},
  {"address":"erd1tx933j8r57smz7s7c6y4p4nzx9np968gpt66escfym3908k3zcqqcde3y8","label":f"Unlabelled whale - took {br['top'][1]['egld']:,.0f} EGLD off exchanges outside the pipeline this week AND received 68,732 EGLD directly from the Binance.com hot wallet. The second-largest ex-pipeline recipient and the reason this week's breadth reading is concentration rather than dispersal. Resolve its onward flow next run","balance_egld":None,"weeks_tracked":1,"first_seen":RD},
  {"address":SRC17,"label":f"OTC source erd17l22 (at {b(SRC17):,.0f}; not the source of the current feed, which is UPbit plus Binance and Bybit feeders)","balance_egld":b(SRC17),"weeks_tracked":18,"first_seen":"2026-05-11"}]}
json.dump(new_prev,open(f"{REPO}/data/previous.json","w"),indent=2)
print("WROTE previous.json; top_accounts",len(top_accounts),"providers",len(staking_providers),"(FULL list incl. zero-locked)")

# ---- known-addresses.json ----
def add_addr(section,addr,name,category,subcategory,notes):
    kn.setdefault(section,{})
    if addr in kn[section]: return False
    kn[section][addr]={"name":name,"category":category,"subcategory":subcategory,"notes":notes,
                       "first_seen":RD,"discovered_run":24}
    return True
added=0
# rec #11: the live JEXchange aggregator, re-derived from the fees contract's callers
_jc=jex["candidates"][0]
if add_addr("defi_jexchange",_jc["address"],"JEXchange: live aggregator (re-derived run #24)","defi","dex_aggregator",
   f"Re-derived by tracing the JEXchange fees contract's inbound leg back to its callers, after the previously tracked aggregator returned 0 transfers for four consecutive runs while the fees contract reported thousands. {_jc['transfers_7d']:,} transfers in 7 days. Four further routers sit behind it at "
   + ", ".join(f"{c['transfers_7d']:,}" for c in jex["candidates"][1:5]) + " transfers."):
    added+=1
if add_addr("whales","erd1tx933j8r57smz7s7c6y4p4nzx9np968gpt66escfym3908k3zcqqcde3y8",
   "Unknown whale - ex-pipeline withdrawal recipient, Binance hot-funded (run #24)","whale","accumulator_candidate",
   f"Took {br['top'][1]['egld']:,.0f} EGLD off exchanges outside the OTC pipeline in the 2026-08-31..2026-09-07 window, the second-largest ex-pipeline recipient, and separately received 68,732 EGLD directly from the Binance.com hot wallet. Its size is why this week's withdrawal-breadth reading is concentration rather than dispersal."):
    added+=1
hub=D["otc_hub_trace"]
for addr,rec in hub["inbound"].items():
    if rec.get("kind")!="router" or rec["amount"]<15000: continue
    terms={k:v for k,v in rec["terminals"].items() if not k.startswith("UNRESOLVED")}
    src=max(terms,key=terms.get) if terms else "unknown"
    if label_map.get(addr): continue
    if add_addr("exchange_routers",addr,f"{src}->OTC Desk Feeder (run #24)","router","otc_feeder",
       f"Zero-balance pass-through carrying {rec['amount']:,.0f} EGLD from {src} into the OTC desk complex in the 2026-08-31..2026-09-07 window."):
        added+=1
for addr,rec in hub["outbound"].items():
    if rec.get("kind")!="router" or rec["amount"]<15000: continue
    terms={k:v for k,v in rec["terminals"].items() if not k.startswith("UNRESOLVED")}
    dst=max(terms,key=terms.get) if terms else "unknown"
    if label_map.get(addr): continue
    if add_addr("exchange_routers",addr,f"OTC Desk->{dst} Router (run #24)","router","otc_router",
       f"Zero-balance pass-through forwarding {rec['amount']:,.0f} EGLD from the OTC desks to {dst} in the 2026-08-31..2026-09-07 window, during the largest one-way delivery week in tracking."):
        added+=1
kn.setdefault("_metadata",{})["last_updated"]=RD
json.dump(kn,open(f"{REPO}/data/known-addresses.json","w"),indent=2)
print("known-addresses.json: added",added)

# ---- learnings.json ----
def roll(arr,val,n=8):
    a=list(arr)+[val]
    return a[-n:] if len(a)>n else a
# baselines must roll off the PREVIOUS run, not off a partial re-run of this one
rbp=[r for r in learn["runs"] if r.get("run_number")!=24][-1]["running_baselines"]
_pct=R["pre_committed_tests"]
_res=[t for t in _pct if t.get("resolved_in_run")==24]
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
   "2026-08-31..2026-09-07 (run #24, weekly frame - a RECORD, and inside the wave)":round(otc["net_one_way_egld_7d"]),
   "2026-08-17..2026-09-07 (WAVE #3 netted feed-to-drain, three frames - the correct measure)":round(wave["net_one_way_egld"])},
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
 "date":RD,"run_number":24,
 "data_quality":{
   "endpoints_that_worked":R["meta_learning"]["endpoints_that_worked"],
   "endpoints_that_failed":R["meta_learning"]["endpoints_that_failed"],
   "api_quirks_discovered":R["meta_learning"]["api_quirks"],
   "data_gaps":R["meta_learning"]["data_gaps"]},
 "analysis_insights":{
   "what_worked":[
     "PRE-COMMITTED BRANCHES THAT PARTITION THE OUTCOME SPACE. Six of the seven open tests resolved on the data, all six as predicted, after two consecutive runs lost a test to a specification defect. The compound-rate test - which failed twice on non-contiguous branches - resolved on its first attempt with a single cut at 57.0%.",
     "MEASURING A STOCK ALONGSIDE THE FLOW. Run #23's central finding was that desk inventory rose while delivery was positive; this run the same pair of numbers gave the answer, because the inventory series existed to compare against. The pipeline's stock is now published as desk_inventory_series_egld and drawn on the dashboard chart.",
     "RUNNING THE WIDENED DETECTOR BACKWARDS OVER THE ARCHIVE - again, and this time it corrected our own new finding rather than an old one. The 'three deregistrations' framing became 82 contracts and 28,032 records, of which only four have an observed transition. A detector without a recency qualifier describes archaeology.",
     "SPECIFYING THE BINANCE QUESTION ON FLOW. The third attempt at this question resolved on the first pass because the threshold was written on what the hot wallet SENDS rather than on what it HOLDS - and the result would have been read backwards on a balance basis, since custody rose while the feed ran.",
     "THE PRE-FLIGHT ADDRESS VALIDATOR, EXTENDED TO COLLECTOR SOURCE, CAUGHT THE EXACT BUG IT WAS BUILT FOR on its first run: run #23's invalid Binance hot-wallet literal, still present in the copied collector, flagged before any query was made.",
     "EXPONENTIAL BACKOFF IN THE MAIN COLLECTOR. The largest run so far - more requests than any previous week, including 16 deep re-scans - completed with zero HTTP 429 failures and zero paged errors."],
   "what_needs_improvement":[
     "A STORAGE CHANGE ALMOST BECAME A HEADLINE. Run #23 started storing the full /providers list; comparing this run's locked>0 delegator total against that stored sum produces a -28,141 collapse that is pure artifact. It was caught because the number was implausible, not because anything checked. Any WoW that spans a snapshot-schema change needs an explicit common-basis guard.",
     "THE ABSORBER RETENTION FIGURE WAS WRONG BY CONSTRUCTION FOR TWO RUNS. received = max(7d, wave) minus forwarded = 7d only. It happened to give the right conclusion in run #23 (no absorbers) and would have given the opposite this week (45% retention on terminals holding 0.9%).",
     "THE BINANCE HOT WALLET IS TOO BUSY FOR THE PAGE BUDGET. 1,000 transactions covered 4.4 of 7 days, so a figure that resolved a pre-committed test is a lower bound. It resolved comfortably, but the next one might not.",
     "THE MODEL HAS NO DEMAND-SIDE INSTRUMENT THAT WORKS. A record delivery was absorbed with a +17% price rise and every proxy read flat, zero or negative. That is the largest open gap in the report and it is not a data problem - it is that all four proxies are on-chain shadows of off-chain decisions.",
     "16 PROVIDER SCANS STILL TERMINATED ON A CAP even after the deep re-scan at 30 pages, so the unbonding queue remains a lower bound on the busiest contracts."],
   "surprising_findings":[
     "THE PRICE ROSE 17% THROUGH THE LARGEST SUPPLY DELIVERY EVER MEASURED. Every prior delivery wave in this archive coincided with a flat or falling EGLD. 536,459 EGLD hit order books and the token added a sixth of its value while BTC and ETH did nothing.",
     "THE DESKS EMPTIED COMPLETELY. 266,213 -> 96,114 in a week, and wave #3 totals 878,809 EGLD one-way feed-to-drain - more than double the previous largest wave in tracking.",
     "BINANCE REFILLED CUSTODY WHILE FEEDING THE DESKS. Custody +372,434 after two weeks of -497K, with 900,000 out and 1,272,434 back, and the hot wallet still pushed 97,390 into OTC feeders. The 'custody drawdown funds distribution' story from run #23 does not survive contact with a third week.",
     "82 PROVIDER CONTRACTS CARRY 28,032 DELEGATOR RECORDS AND NO STAKE - 14% of every delegator record on the network. Only one of the 82 saw a single transaction this week.",
     "THE TWO 100%-FEE PROVIDERS RESTORED THEIR FEES AND NOTHING CAME BACK. egldstakingprovider 100% -> 50%, procryptostaking 100% -> 35%, APR restored on both, and both still lost book and users in the same week.",
     "THE COMPOUND RATE REVERSED IN THE WEEK OF THE RECORD DELIVERY. Four consecutive declines ended at 62.05%, the highest of eleven readings, while half a million EGLD was being sold into order books from somewhere else entirely."]},
 "methodology_changes":R["meta_learning"]["methodology_changes"],
 "new_addresses_discovered":[
   f"{jex['candidates'][0]['address']} (JEXchange: live aggregator, re-derived run #24) - added under defi_jexchange. {jex['candidates'][0]['transfers_7d']:,} transfers in 7 days, found by tracing the fees contract's inbound callers after the tracked aggregator read 0 for four consecutive runs. Four secondary routers sit behind it.",
   "erd1tx933j8r57smz7s7c6y4p4nzx9np968gpt66escfym3908k3zcqqcde3y8 (unlabelled whale) - took 101,664 EGLD off exchanges outside the pipeline AND received 68,732 EGLD straight from the Binance.com hot wallet. Added under whales/accumulator_candidate; resolve its onward flow next run.",
   "New OTC desk feeder and router wallets labelled from this week's hub trace (>15K EGLD legs) - the feed side now carries Bybit- and Binance-parented feeders alongside UPbit, and about 344,000 EGLD arrived from routers whose parent venue is still unresolved.",
   "STILL FLAGGED, not fixed: two invalid-checksum entries in known-addresses.json (Hatom UTK Money Market, OneDex Launchpad), open since run #18 and now confirmed by a validator that also covers collector source."],
 "action_items_completed":R["meta_learning"]["action_items_completed_detail"],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":R["meta_learning"]["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":R["meta_learning"]["dashboard_suggestions_followup"],
 "self_assessment":{
   "most_valuable_insight":R["meta_learning"]["most_valuable_insight"],
   "actions_completed_count":13,"actions_attempted_count":13,
   "what_would_2x_next_week":("Build one exchange-side demand instrument. This week the model measured supply arriving at order books "
     "to the EGLD - a record 536,459 - and could not say a single thing about who bought it, because every demand proxy it owns "
     "(absorber wallets, Mega Whale balance, DEX turnover, withdrawal breadth) is an on-chain shadow of an off-chain decision and all four read empty. "
     "A third-party exchange netflow or order-book depth series for Bybit and Binance.com, the two venues the pipeline delivers into, would turn "
     "'the buyer is not visible' into a measurement. Everything else on the list is refinement; this is the gap."),
   "pre_committed_test_for_next_run":("WAVE #4 RESTART: a UPbit tranche above ~200,000 = the programme is continuous; below ~50,000 with desks under ~120,000 = wave #3 is complete. "
     "UNIDENTIFIED BID: price above ~$4.20 with no new delivery = real off-chain demand; below ~$3.90 = a squeeze into thin books. "
     "STAKED RATIO: below 46.80% within three weeks = a genuine downtrend in the security budget; above 47.60% = unbonding-cycle noise.")},
 "recommendations_for_next_run":R["meta_learning"]["recommendations_for_next_run"]}
learn["runs"]=[r for r in learn["runs"] if r.get("run_number")!=24]
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #24; total runs",len(learn["runs"]))
for k in ["egld_price_usd","otc_net_one_way_egld_7d","otc_desk_inventory_egld","dex_turnover_ratio_pct","dex_volume_24h_egld","reward_compound_pct","pre_committed_test_hit_rate_pct"]:
    print("  baseline",k,new_baselines[k])
