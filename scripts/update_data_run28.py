#!/usr/bin/env python3
"""Run #28: refresh previous.json, known-addresses.json and append the learnings entry."""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-10-05"
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
R=json.load(open(f"{REPO}/reports/{RD}.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
learn=json.load(open(f"{REPO}/data/learnings.json"))
O=json.load(open("/tmp/run28w/derived.json"))
INC_IN={}; INC_ADDRS=set(O["incident"]["inc_addrs"])  # post-rollback: no netting, incident addresses excluded (dust)

label_map={}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"): label_map[a]=m.get("name","Unknown")
def lab(a): return label_map.get(a,"Unknown")
acc=D["accounts"]
def b(a):
    x=acc.get(a)
    # run #26: balances stored NET of the Sep 19 exploit deposits, so a recovery that
    # reverses them does not show up next week as a phantom outflow
    return int(x["info"]["balance"])/1e18-INC_IN.get(a,0.0) if x and isinstance(x.get("info"),dict) and "balance" in x["info"] else None
econ=D["economics"]; st=D["stats"]; be=D["btc_eth"]; meco=D["mex_economics"]
otc=R["whale_intelligence"]["otc_pipeline"]; wave=otc["wave_window_netting"]
sk=O["staking"]; cust=O["custody"]; ub=O["unbond"]; p2p=O["p2p"]
zsc=O["zero_stake_cohort"]; em=O["emerging_lsd"]; jex=O["jex"]
HOT=O["hot_to_pipe"]; FEED=O["feeders_in"]; br=O["breadth"]
dser={d["identity"]:d for d in O["dereg_series"]}

# ---- previous.json ----
top_accounts=[{"address":x["address"],"balance_egld":int(x["balance"])/1e18-INC_IN.get(x["address"],0.0),"label":lab(x["address"])}
              for x in D["top_accounts"][:100] if x["address"] not in INC_ADDRS]
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
   "total_pairs":meco["marketPairs"],"mex_price_usd":R["token_activity"]["xexchange"]["mex_price_usd"],
   "mex_market_cap_usd":R["token_activity"]["xexchange"]["mex_market_cap_usd"],
   "mex_price_source":"xExchange /mex/economics",
   "volume_status":"run #28 24h volume evaluable (full live week)",
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
 "lsd_protocol_seeds":{(p_.get("known_label") or p_["address"]):p_["address"]
                       for p_ in json.load(open(f"{REPO}/data/collected/liquid_staking_discovery_{RD}.json"))["liquid_staking_protocols"]
                       if (p_.get("staked_egld") or 0) >= 100},
 # run #28: partial rails - keep the last open-book reading as the comparison base; store the
 # latest partial-rail book under a stable key the next run reads (exchange_orderbook_latest)
 "exchange_orderbook":prev["exchange_orderbook"],
 "exchange_orderbook_closed_book_run27":prev["exchange_orderbook_closed_book_run27"],
 "exchange_orderbook_latest":{"run":28,"rails":"partial",**{k:R["whale_intelligence"]["demand_instruments"]["exchange_orderbook"][k] for k in ("binance","bybit","upbit","coinbase","gate","all_venues","korea_premium_pct","upbit_share_of_volume_pct","spot_volume_7d_egld")}},
 "mex_pair_event":R["token_activity"]["xexchange"]["mex_pair_event"],
 "mex_incident_recovery":prev.get("mex_incident_recovery"),
 "chain_halt_incident":prev.get("chain_halt_incident"),
 "incident_addresses":sorted(INC_ADDRS),
 "incident_balances_at_halt":prev.get("incident_balances_at_halt"),
 "pre_halt_reference_balances":prev.get("pre_halt_reference_balances"),
 "halt_recovery_run27":prev["halt_recovery_run27"],
 "halt_recovery_run28":{k:R["whale_intelligence"]["halt_recovery"][k] for k in ("invalid_balances_egld_now","invalid_balances_egld_at_halt")},
 "exchange_rail_status_run27":prev.get("exchange_rail_status_run27"),
 "exchange_rail_status_latest":{"run":28,**{k:R["whale_intelligence"]["exchange_flows"]["rail_status"][k] for k in ("venues_open","venues_deposit_only","venues_closed","by_venue")},"restart_2_ts":1790263800},
 "exit_routes_run28":R["whale_intelligence"]["exit_routes"],
 "stablecoin_supply":{"USDC-c76f1f":O["tokens"]["stable"]["USDC-c76f1f"]["supply"],
                      "USDT-f8c08c":O["tokens"]["stable"]["USDT-f8c08c"]["supply"]},
 "otc_throughput_series":{k:round(v) for k,v in otc["gross_series_egld_7d"].items()},
 "otc_net_one_way_series":{k:round(v) for k,v in otc["net_one_way_series_egld_7d"].items()},
 "otc_circularity_measured_pct":{k:round(v,1) for k,v in otc["circularity_series_pct"].items()},
 "otc_desk_inventory_series":{**prev["otc_desk_inventory_series"],"run28":round(desks)},
 "otc_wave_window_netting":{"window":wave["window"],"gross_outbound_egld":round(wave["gross_outbound_egld"]),
   "circular_share_pct":round(wave["circular_share_pct"],1),
   "net_one_way_egld":round(wave["net_one_way_egld"]),
   "sum_of_weekly_nets_egld":round(wave["sum_of_weekly_nets_egld"]),
   "weekly_frame_overstatement_pct":round(wave["weekly_frame_overstatement_pct"],1)},
 "demand_instruments":{"dex_turnover_ratio_pct":R["token_activity"]["xexchange"]["turnover_ratio_pct"],
   "dex_volume_egld_24h":R["token_activity"]["xexchange"]["dex_volume_egld_24h"],
   "identifiable_bid_absorbed_egld_7d":0,"weeks_bid_at_zero":8,
   "weeks_bid_at_zero_in_last_four":4,
   "identifiable_bid_status":f"RETIRED (run #23; zero for an eighth week run #28). The 14 desk outbound terminals took {O['absorbers']['total_received']:,.0f} EGLD and ended the week holding {O['absorbers']['total_balance_held']:,.0f} between them. Run #23's received-minus-forwarded retention figure compared a multi-week inflow against a one-week outflow and is not usable; balance is the correct test.",
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
  {"address":"erd155j9c36hp5dkqp7u5gwjek00g2axermvqdzk3j7mpk9k8yunpy4s9fpq8c","label":"Post-restart exiter: sold 26,678 EGLD on chain, bridged 111,274 USDC to Ethereum; 8,889 EGLD still delegated","balance_egld":b("erd155j9c36hp5dkqp7u5gwjek00g2axermvqdzk3j7mpk9k8yunpy4s9fpq8c"),"weeks_tracked":2,"first_seen":"2026-09-28"},
  {"address":"erd1fcxu3f0hlxyvnp7zvuqmf34zf5w782tst6vuqhm4dwq4ayjspdaqce0q49","label":"UPbit hot wallet - closed; Upbit caution review Oct 19-23. PRE-COMMITTED (korea-premium-arbitrage, upbit-premium-decay)","balance_egld":b("erd1fcxu3f0hlxyvnp7zvuqmf34zf5w782tst6vuqhm4dwq4ayjspdaqce0q49"),"weeks_tracked":2,"first_seen":"2026-09-28"},
  {"address":BINANCE_HOT,"label":"Binance.com hot wallet - deposit-only since Sep 29 (0 EGLD sends)","balance_egld":b(BINANCE_HOT),"weeks_tracked":6,"first_seen":"2026-08-31"},
  {"address":"erd1p4vy5n9mlkdys7xczegj398xtyvw2nawz00nnfh4yr7fpjh297cqtsu7lw","label":"Gate.io - reopened Oct 4; took the 12,184 EGLD OTC router tail at its 23:00 sweep","balance_egld":b("erd1p4vy5n9mlkdys7xczegj398xtyvw2nawz00nnfh4yr7fpjh297cqtsu7lw"),"weeks_tracked":1,"first_seen":RD},
  {"address":UPBIT_DESK,"label":"UPbit OTC Desk - idle three weeks. PRE-COMMITTED (otc-pipeline-resumption, delivery-price-relevance-2)","balance_egld":b(UPBIT_DESK),"weeks_tracked":28,"first_seen":"2026-04-02"},
  {"address":DIST_DESK,"label":"OTC Distribution Wallet - idle","balance_egld":b(DIST_DESK),"weeks_tracked":26,"first_seen":"2026-04-13"},
  {"address":"erd1vd76pwhl4dyeyd8gylv6mkkvy7g4dnfezjuyp4j4x3wwnauga57q53m3z0","label":"Unknown Whale I - probable exchange hot wallet, 0 inbound. PRE-COMMITTED (unknown-whale-i-is-exchange)","balance_egld":b("erd1vd76pwhl4dyeyd8gylv6mkkvy7g4dnfezjuyp4j4x3wwnauga57q53m3z0"),"weeks_tracked":10,"first_seen":"2026-08-03"},
  {"address":"erd1a6lte0wqwwdjtt0nvv62c6pacltznzgq93gjxu6el44cx6lqx3fsu48u4l","label":"Probable exchange hot wallet (erd1a6lte0) - idle","balance_egld":b("erd1a6lte0wqwwdjtt0nvv62c6pacltznzgq93gjxu6el44cx6lqx3fsu48u4l"),"weeks_tracked":3,"first_seen":"2026-09-21"},
  {"address":"erd1ygqnssmnq2p37l9wyv00jwq6echwa9dhssr50399gjj6c7qwa8vqap0prn","label":"Unlabelled: sent 30,000 EGLD to erd1hhvfrw on Sep 30","balance_egld":None,"weeks_tracked":1,"first_seen":RD},
  {"address":"erd1kwvkch79edm9qtg3tlaylgm9yff04lr9vaszazuavxtqrffz6scqrvvjd2","label":"MultiversX VM exploit wallet (Sep 19) - dust","balance_egld":b("erd1kwvkch79edm9qtg3tlaylgm9yff04lr9vaszazuavxtqrffz6scqrvvjd2"),"weeks_tracked":3,"first_seen":"2026-09-21"},
  {"address":"erd1z7wyqlr64qhr5k3wu9qa4d6c6wszxx8s5n9qc7067ds9f9pv3stqppm63r","label":"ADDRESS-POISONING lookalike of the OTC Distribution Wallet - 0 inbound above dust","balance_egld":None,"weeks_tracked":3,"first_seen":"2026-09-21"},
  {"address":"erd1v6k4dxe72tg0d43pvxrhq0zhlg0z5p0r4jeww2wtazv8kjn0cugsryxnk5","label":"ADDRESS-POISONING lookalike of the UPbit OTC Desk - 0 inbound above dust","balance_egld":None,"weeks_tracked":3,"first_seen":"2026-09-21"},
  {"address":CUSTODY,"label":f"Binance Staking custody ({b(CUSTODY):,.0f}, unchanged)","balance_egld":b(CUSTODY),"weeks_tracked":22,"first_seen":"2026-05-25"},
  {"address":MEGA,"label":"Mega Whale erd18mv2z6r2 - retired bid instrument, zero for an eighth week","balance_egld":b(MEGA),"weeks_tracked":28,"first_seen":"2026-04-02"},
  {"address":UNBOND,"label":"229,865 EGLD unbond - retired, seventh week unmoved","balance_egld":ub["balance"],"weeks_tracked":8,"first_seen":"2026-08-17"}]}
json.dump(new_prev,open(f"{REPO}/data/previous.json","w"),indent=2)
print("WROTE previous.json; top_accounts",len(top_accounts),"providers",len(staking_providers),"(FULL list incl. zero-locked)")

# ---- known-addresses.json ----
def add_addr(section,addr,name,category,subcategory,notes):
    kn.setdefault(section,{})
    if addr in kn[section]: return False
    kn[section][addr]={"name":name,"category":category,"subcategory":subcategory,"notes":notes,
                       "first_seen":RD,"discovered_run":28}
    return True
added=0
for sec in kn.values():
    if isinstance(sec,dict):
        for ra in ["erd1kyc7l2pgc9","erd1ktcvmyd6u6","erd10f38t4mcv6","erd1509av9juu0","erd1rjkvjatu8j"]:
            for a_,e_ in sec.items():
                if a_.startswith(ra) and isinstance(e_,dict) and "Run #28" not in e_.get("notes",""):
                    e_["notes"]=(e_.get("notes","")+" Run #28: held a Sep 18-19 desk tranche through the halt; swept it to Gate.io at the Oct 4 23:00 reopening.").strip()
kn.setdefault("_metadata",{})["last_updated"]=RD
json.dump(kn,open(f"{REPO}/data/known-addresses.json","w"),indent=2)
print("known-addresses.json: added",added)

# ---- learnings.json ----
def roll(arr,val,n=8):
    a=list(arr)+[val]
    return a[-n:] if len(a)>n else a
rbp=[r for r in learn["runs"] if r.get("run_number")!=28][-1]["running_baselines"]
_pct=R["pre_committed_tests"]
_res=[t for t in _pct if t.get("resolved_in_run")==28]
_res_n=len(_res); _open_n=sum(1 for t in _pct if t["status"]=="open")
_hit=100*sum(1 for t in _res if t.get("outcome")=="as_predicted")/_res_n if _res_n else 0.0
sr=econ["staked"]/econ["circulatingSupply"]
xxr=R["token_activity"]["xexchange"]; ob=R["whale_intelligence"]["demand_instruments"]["exchange_orderbook"]
q=R["staking_intelligence"]["unbonding_in_flight"]["queue_this_week"]
new_baselines={
 "egld_price_usd":roll(rbp["egld_price_usd"],econ["price"]),
 "dex_volume_24h_usd":roll(rbp["dex_volume_24h_usd"],xxr["total_volume_24h_usd"]),
 "dex_volume_24h_egld":roll(rbp.get("dex_volume_24h_egld",[]),round(xxr["dex_volume_egld_24h"])),
 "staked_egld":roll(rbp["staked_egld"],econ["staked"]),
 "mex_price_usd":roll(rbp["mex_price_usd"],xxr["mex_price_usd"]),
 "total_delegators":roll(rbp["total_delegators"],R["staking_intelligence"]["churn"]["total_delegators_current"]),
 "staked_ratio":roll(rbp["staked_ratio"],sr),
 # PARTIAL RAILS (UPbit/Bybit/Coinbase closed, Binance deposit-only): exchange flow and OTC series NOT appended
 "exchange_net_flow_egld":rbp["exchange_net_flow_egld"],
 "otc_pipeline_throughput_egld_7d":rbp["otc_pipeline_throughput_egld_7d"],
 "otc_net_one_way_egld_7d":rbp.get("otc_net_one_way_egld_7d",[]),
 "otc_desk_inventory_egld":roll(rbp.get("otc_desk_inventory_egld",[]),round(desks)),
 "otc_net_one_way_measured_windows":rbp.get("otc_net_one_way_measured_windows") or {},
 "otc_circularity_pct":rbp.get("otc_circularity_pct",{}),
 "dex_turnover_ratio_pct":roll(rbp.get("dex_turnover_ratio_pct",[]),round(xxr["turnover_ratio_pct"],3)),
 "identifiable_bid_absorbed_egld_7d":roll(rbp.get("identifiable_bid_absorbed_egld_7d",[]),0.0),
 "binance_staking_custody_egld":roll(rbp.get("binance_staking_custody_egld") or [],exchange_balances["Binance Staking"]),
 "reward_compound_pct":roll(rbp.get("reward_compound_pct",[]),round(R["staking_intelligence"]["reward_behavior"]["compound_pct_at_function_level"],2)),
 "delegation_total_locked_egld":roll(rbp.get("delegation_total_locked_egld",[]),round(R["staking_intelligence"]["summary"]["total_delegated_egld"])),
 "usdt_supply":roll(rbp.get("usdt_supply",[]),round(O["tokens"]["stable"]["USDT-f8c08c"]["supply"])),
 "usdc_supply":roll(rbp.get("usdc_supply",[]),round(O["tokens"]["stable"]["USDC-c76f1f"]["supply"])),
 # full 7-day live window again: appended
 "unbonding_queue_undelegated_egld_7d":roll(rbp.get("unbonding_queue_undelegated_egld_7d",[]),round(q["undelegated_egld"])),
 "unbonding_short_window_readings":rbp.get("unbonding_short_window_readings") or {},
 "withdraw_egld_returned_7d":roll(rbp.get("withdraw_egld_returned_7d",[]),round(q["withdraw_egld_returned"])),
 "withdrawal_breadth_ex_pipeline_egld":rbp.get("withdrawal_breadth_ex_pipeline_egld",[]),
 "cex_spot_volume_7d_egld":rbp.get("cex_spot_volume_7d_egld",[]),
 "otc_delivery_share_of_spot_pct":rbp.get("otc_delivery_share_of_spot_pct",[]),
 "binance_bybit_bid_depth_2pct_usd":rbp.get("binance_bybit_bid_depth_2pct_usd",[]),
 "closed_book_readings_run26":rbp.get("closed_book_readings_run26"),
 "closed_book_readings_run27":rbp.get("closed_book_readings_run27"),
 "partial_rail_readings_run28":{"cex_spot_volume_7d_egld":round(ob["spot_volume_7d_egld"]),"binance_bybit_bid_depth_2pct_usd":round(ob["binance_bybit_bid_depth_2pct_usd"]),
   "korea_premium_pct":round(ob["korea_premium_pct"],1),"upbit_share_of_volume_pct":round(ob["upbit_share_of_volume_pct"],1),
   "exchange_net_flow_egld":round(R["whale_intelligence"]["exchange_flows"]["net_change_egld"]),
   "otc_gross_egld":round(otc["gross_outbound_egld_7d"]),"otc_router_tail_to_gate_egld":round(otc["router_tail_delivery_egld"]),
   "venues_open":R["whale_intelligence"]["exchange_flows"]["rail_status"]["venues_open"]},
 "dex_exit_discount_pct":[round(R["whale_intelligence"]["exit_routes"]["discount_to_week_close_pct"],1)],
 "korea_premium_pct":[32.4,round(ob["korea_premium_pct"],1)],
 "hmex_supply":rbp.get("hmex_supply",[]),
 "pre_committed_tests_resolved":roll(rbp.get("pre_committed_tests_resolved",[]),_res_n),
 "pre_committed_test_hit_rate_pct":roll(rbp.get("pre_committed_test_hit_rate_pct",[]),round(_hit,1)),
 "pre_committed_tests_open":roll(rbp.get("pre_committed_tests_open",[]),_open_n)}
ml=R["meta_learning"]
entry={
 "date":RD,"run_number":28,
 "data_quality":{"endpoints_that_worked":ml["endpoints_that_worked"],"endpoints_that_failed":ml["endpoints_that_failed"],
   "api_quirks_discovered":ml["api_quirks"],"data_gaps":ml["data_gaps"]},
 "analysis_insights":{
   "what_worked":[
     "VALUE-BEARING RAIL COUNTS: raw counts said Binance.com 33 receives and Gate.io 17 (airdrop noise included); EGLD-only counts gave a clean per-venue state (open / deposit-only / closed) with first-deposit timestamps.",
     "FOLLOWING THE WATCH-LIST WALLET: last week's 'largest post-restart unDelegator' entry led straight to the week's best finding (withdraw -> DEX -> USDC -> bridge, a measured ~9% exit discount).",
     "READING ROUTER HISTORY BEFORE CALLING A DELIVERY: the Gate.io deposits looked like the pipeline restarting; the routers' inbound showed Sep 18-19 tranches, so it was a stranded tail already counted in wave #4.",
     "RE-RUNNING THE REWARD SAMPLER on a 6/8 result instead of publishing it (run #25 rule): 8/8 on retry, 58.28%."],
   "what_needs_improvement":[
     "A shared 4 req/s budget still drew ~40 HTTP 429s; the provider scan needs a slower dedicated budget.",
     "No Kraken address is tracked, so a venue that publicly reopened is invisible on chain.",
     "The exit trace covers one wallet; it should be a collector-side scan of every large withdraw.",
     "Run-specific scripts are still copied and patched weekly; the rail and trace scripts added this run should be folded into the collector."],
   "surprising_findings":[
     "The Upbit premium fell from 32% to 12% with Upbit deposits still closed: no arbitrage closed it.",
     "The pipeline's first EGLD to reach a reopened venue was inventory stranded 16 days earlier, delivered in the venue's first deposit hour.",
     "A staker paid ~9% to exit through the DEX and bridge rather than wait for a CEX.",
     "Binance.com reopened deposits on the native chain while publicly withdrawing via BEP-20 only."]},
 "methodology_changes":ml["methodology_changes"],
 "new_addresses_discovered":ml["new_addresses_discovered_detail"],
 "action_items_completed":ml["action_items_completed_detail"],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":ml["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":ml["dashboard_suggestions_followup"],
 "self_assessment":{
   "most_valuable_insight":ml["most_valuable_insight"],
   "actions_completed_count":5,"actions_attempted_count":6,
   "what_would_2x_next_week":"UPbit or Binance withdrawals reopening: a per-venue first-week trace, the premium against it, desk behaviour, and whether unbonding exits switch from the DEX+bridge route back to CEX deposits.",
   "pre_committed_test_for_next_run":"UPBIT-PREMIUM-DECAY (run #29: < 5% with UPbit closed = demand faded). KOREA-PREMIUM-ARBITRAGE deadline run #29. OTC-PIPELINE-RESUMPTION through run #31."},
 "recommendations_for_next_run":ml["recommendations_for_next_run"]}
learn["runs"]=[r for r in learn["runs"] if r.get("run_number")!=28]
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #28; total runs",len(learn["runs"]))
