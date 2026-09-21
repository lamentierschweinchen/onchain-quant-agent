#!/usr/bin/env python3
"""Run #26: refresh previous.json, known-addresses.json and append the learnings entry."""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-09-21"
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
R=json.load(open(f"{REPO}/reports/{RD}.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
learn=json.load(open(f"{REPO}/data/learnings.json"))
O=json.load(open("/tmp/run26w/derived.json"))
INC_IN=O["incident"]["inc_in"]; INC_ADDRS=set(O["incident"]["inc_addrs"])

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
 "xexchange":{"volume_24h_usd":prev["xexchange"]["volume_24h_usd"],
   "total_pairs":meco["marketPairs"],"mex_price_usd":R["token_activity"]["xexchange"]["mex_price_usd"],
   "mex_market_cap_usd":R["token_activity"]["xexchange"]["mex_market_cap_usd"],
   "mex_price_source":"xExchange /mex/economics (pool restored 2026-09-17)",
   "volume_status":"run #26 24h volume NOT EVALUABLE (chain halted); volume/turnover fields carry run #25's last evaluable values",
   "pool_tvl_usd":R["token_activity"]["xexchange"]["pool_tvl_usd"],
   "turnover_ratio_pct":prev["xexchange"]["turnover_ratio_pct"],
   "volume_24h_egld":prev["xexchange"]["volume_24h_egld"],
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
 "exchange_orderbook":R["whale_intelligence"]["demand_instruments"]["exchange_orderbook"],
 "mex_pair_event":R["token_activity"]["xexchange"]["mex_pair_event"],
 "mex_incident_recovery":{k:v for k,v in R["token_activity"]["xexchange"]["mex_incident_recovery"].items() if k!="pairs_now"},
 "chain_halt_incident":{k:v for k,v in R["whale_intelligence"]["chain_halt_incident"].items()},
 "incident_addresses":sorted(INC_ADDRS),
 "incident_balances_at_halt":{"attacker":O["incident"]["attacker_balance"],"contract":O["incident"]["contract_balance"],
   "fanout_hop1":{x["hop1"]:x["hop1_balance"] for x in D["chain_halt_incident"]["fanout"]},
   "exchange_deposits_by_address":INC_IN},
 "pre_halt_reference_balances":{"otc_desks":O["otc"]["desk_bal"],"binance_custody":O["custody"]["balance"],"hatom_egld_mm":O["defi"]["egld_mm_balance"]},
 "stablecoin_supply":{"USDC-c76f1f":O["tokens"]["stable"]["USDC-c76f1f"]["supply"],
                      "USDT-f8c08c":O["tokens"]["stable"]["USDT-f8c08c"]["supply"]},
 "otc_throughput_series":{k:round(v) for k,v in otc["gross_series_egld_7d"].items()},
 "otc_net_one_way_series":{k:round(v) for k,v in otc["net_one_way_series_egld_7d"].items()},
 "otc_circularity_measured_pct":{k:round(v,1) for k,v in otc["circularity_series_pct"].items()},
 "otc_desk_inventory_series":{**prev["otc_desk_inventory_series"],"run26":round(desks)},
 "otc_wave_window_netting":{"window":wave["window"],"gross_outbound_egld":round(wave["gross_outbound_egld"]),
   "circular_share_pct":round(wave["circular_share_pct"],1),
   "net_one_way_egld":round(wave["net_one_way_egld"]),
   "sum_of_weekly_nets_egld":round(wave["sum_of_weekly_nets_egld"]),
   "weekly_frame_overstatement_pct":round(wave["weekly_frame_overstatement_pct"],1)},
 "demand_instruments":{"dex_turnover_ratio_pct":R["token_activity"]["xexchange"]["turnover_ratio_pct"],
   "dex_volume_egld_24h":R["token_activity"]["xexchange"]["dex_volume_egld_24h"],
   "identifiable_bid_absorbed_egld_7d":0,"weeks_bid_at_zero":6,
   "weeks_bid_at_zero_in_last_four":4,
   "identifiable_bid_status":f"RETIRED (run #23; zero for a sixth week run #26). The 14 desk outbound terminals took {O['absorbers']['total_received']:,.0f} EGLD and ended the week holding {O['absorbers']['total_balance_held']:,.0f} between them. Run #23's received-minus-forwarded retention figure compared a multi-week inflow against a one-week outflow and is not usable; balance is the correct test.",
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
  {"address":"erd1kwvkch79edm9qtg3tlaylgm9yff04lr9vaszazuavxtqrffz6scqrvvjd2","label":f"MultiversX VM exploit wallet (Sep 19) - held {O['incident']['attacker_balance']:,.0f} invalid EGLD at the halt. PRE-COMMITTED (halt-recovery-clean): < 1,000 EGLD across attacker, contract and fan-out after restart = clean targeted recovery","balance_egld":O["incident"]["attacker_balance"],"weeks_tracked":1,"first_seen":RD},
  {"address":"erd1qqqqqqqqqqqqqpgqsqffm2ezs77zsu6cvc6nxd4v8qegne4v6scqke2kq9","label":f"MultiversX VM exploit contract - held {O['incident']['contract_balance']:,.0f} invalid EGLD at the halt","balance_egld":O["incident"]["contract_balance"],"weeks_tracked":1,"first_seen":RD},
  {"address":"erd1vd76pwhl4dyeyd8gylv6mkkvy7g4dnfezjuyp4j4x3wwnauga57q53m3z0","label":"Unknown Whale I - received 775,154 minted EGLD via a fresh hop; probable exchange hot wallet. PRE-COMMITTED (unknown-whale-i-is-exchange): >500 distinct senders in 7d = exchange","balance_egld":b("erd1vd76pwhl4dyeyd8gylv6mkkvy7g4dnfezjuyp4j4x3wwnauga57q53m3z0"),"weeks_tracked":8,"first_seen":"2026-08-03"},
  {"address":"erd1a6lte0wqwwdjtt0nvv62c6pacltznzgq93gjxu6el44cx6lqx3fsu48u4l","label":"Probable exchange hot wallet - received 1,634,870 minted EGLD from two fan-out wallets; nonce 2,131","balance_egld":b("erd1a6lte0wqwwdjtt0nvv62c6pacltznzgq93gjxu6el44cx6lqx3fsu48u4l"),"weeks_tracked":1,"first_seen":RD},
  {"address":UPBIT_DESK,"label":f"UPbit OTC Desk (pre-halt: UPbit fed {otc['upbit_reload_egld']:,.0f}, net one-way {otc['net_one_way_egld_7d']:,.0f}; wave #4 netted {wave['net_one_way_egld']:,.0f}). PRE-COMMITTED (delivery-price-relevance-2) for the first full week after transfers reopen","balance_egld":b(UPBIT_DESK),"weeks_tracked":26,"first_seen":"2026-04-02"},
  {"address":DIST_DESK,"label":f"OTC Distribution Wallet (circularity {otc['circular_share_pct']:.0f}% pre-halt)","balance_egld":b(DIST_DESK),"weeks_tracked":24,"first_seen":"2026-04-13"},
  {"address":"erd1z7wyqlr64qhr5k3wu9qa4d6c6wszxx8s5n9qc7067ds9f9pv3stqppm63r","label":"ADDRESS-POISONING lookalike of the OTC Distribution Wallet - dusting pipeline routers; watch for inbound above dust","balance_egld":None,"weeks_tracked":1,"first_seen":RD},
  {"address":"erd1v6k4dxe72tg0d43pvxrhq0zhlg0z5p0r4jeww2wtazv8kjn0cugsryxnk5","label":"ADDRESS-POISONING lookalike of the UPbit OTC Desk - dusting pipeline routers; watch for inbound above dust","balance_egld":None,"weeks_tracked":1,"first_seen":RD},
  {"address":"erd1qqqqqqqqqqqqqpgqwmq40hvu7j88gqc7935prc0r96mdhs3m78sszpu2uj","label":"Hatom MEX incident recovery contract (redeemed 13.04T HMEX, sold 270B MEX via whitelisted paused pools)","balance_egld":0.0,"weeks_tracked":1,"first_seen":RD},
  {"address":CUSTODY,"label":f"Binance Staking custody ({b(CUSTODY):,.0f}, unchanged pre-halt)","balance_egld":b(CUSTODY),"weeks_tracked":20,"first_seen":"2026-05-25"},
  {"address":BINANCE_HOT,"label":f"Binance.com hot wallet (net of 2,288,296 minted deposits). Sent {HOT['total_egld']:,.0f} to OTC feeders pre-halt, below 50,000 for the first time in four weeks","balance_egld":b(BINANCE_HOT),"weeks_tracked":4,"first_seen":"2026-08-31"},
  {"address":LEDGERBYFIGMENT,"label":f"ledgerbyfigment - zero-stake, delegators {dser.get('ledgerbyfigment',{}).get('users',0):,}","balance_egld":0.0,"weeks_tracked":4,"first_seen":"2026-08-31"},
  {"address":P2P_PROVIDER,"label":"p2p_org_ - exited. PRE-COMMITTED (fourth-deregistration, week 4 of 4 next run, TRANSITION basis)","balance_egld":0.0,"weeks_tracked":5,"first_seen":"2026-08-24"},
  {"address":MEGA,"label":"Mega Whale erd18mv2z6r2 - retired bid instrument, zero for a sixth week","balance_egld":b(MEGA),"weeks_tracked":26,"first_seen":"2026-04-02"},
  {"address":UNBOND,"label":"229,865 EGLD unbond - retired, fifth week unmoved","balance_egld":ub["balance"],"weeks_tracked":6,"first_seen":"2026-08-17"}]}
json.dump(new_prev,open(f"{REPO}/data/previous.json","w"),indent=2)
print("WROTE previous.json; top_accounts",len(top_accounts),"providers",len(staking_providers),"(FULL list incl. zero-locked)")

# ---- known-addresses.json ----
def add_addr(section,addr,name,category,subcategory,notes):
    kn.setdefault(section,{})
    if addr in kn[section]: return False
    kn[section][addr]={"name":name,"category":category,"subcategory":subcategory,"notes":notes,
                       "first_seen":RD,"discovered_run":26}
    return True
added=0
H=D["chain_halt_incident"]
if add_addr("incident","erd1kwvkch79edm9qtg3tlaylgm9yff04lr9vaszazuavxtqrffz6scqrvvjd2","MultiversX VM exploit wallet (2026-09-19)","incident","exploiter",
   "Funded Sep 16 by MEXC/Bybit withdrawals; Sep 19 06:34-07:37 UTC ran doubling deposit/compound rounds producing invalid EGLD balances; fanned out 9.81M EGLD to 12 wallets 07:24-07:27; chain halted ~07:41."): added+=1
if add_addr("incident","erd1qqqqqqqqqqqqqpgqsqffm2ezs77zsu6cvc6nxd4v8qegne4v6scqke2kq9","MultiversX VM exploit contract (2026-09-19)","incident","exploit_contract",
   "Deployed by the exploit wallet 06:34 UTC Sep 19; target of the deposit/compound loop; 25.56M EGLD at the halt."): added+=1
for x in H["fanout"]:
    if add_addr("incident",x["hop1"],"Exploit fan-out wallet (2026-09-19)","incident","exploit_hop",
       f"Received {x['egld']:,.0f} minted EGLD from the exploit wallet; forwarded to {', '.join((fw['label'] or fw['to'][:14]) for fw in x['forwarded']) or 'nowhere (unmoved)'}."): added+=1
for ad,nm,nt in [("erd1qqqqqqqqqqqqqpgqwmq40hvu7j88gqc7935prc0r96mdhs3m78sszpu2uj","Hatom: MEX incident recovery contract","Deployed Sep 15 by the Hatom deployer; redeemed seized HMEX and sold 270B MEX into MEX/WEGLD, MEX/USH, MEX/USDC while they were paused (pause whitelist)."),
                 ("erd12uv6mj42mv090ucffuuc4pwexrgqfuycegl2rg9j2ah9u20s7dlsmrt5jd","Hatom: MEX recovery keeper","Called runRound/runCampaignRound on the recovery contract Sep 15-17.")]:
    if add_addr("defi_hatom",ad,nm,"defi","hatom_ops",nt): added+=1
for ad,nt in [("erd1z7wyqlr64qhr5k3wu9qa4d6c6wszxx8s5n9qc7067ds9f9pv3stqppm63r","mimics OTC Distribution Wallet erd1z7fnqf...nm63r"),
              ("erd1v6k4dxe72tg0d43pvxrhq0zhlg0z5p0r4jeww2wtazv8kjn0cugsryxnk5","mimics UPbit OTC Desk erd1v6x9egd...hcxnk5")]:
    if add_addr("incident",ad,"Address-poisoning lookalike (OTC desk)","incident","address_poisoning",f"Sends 0.0001 EGLD dust to OTC pipeline routers; {nt}. No misdirected inbound as of run #26."): added+=1
if add_addr("exchanges_probable","erd1a6lte0wqwwdjtt0nvv62c6pacltznzgq93gjxu6el44cx6lqx3fsu48u4l","Probable exchange hot wallet (unnamed venue)","unknown","probable_exchange",
   "Nonce 2,131, streams of small inbound transfers; received 1,634,870 minted EGLD from two exploit fan-out wallets on Sep 19. Category left 'unknown' until the venue is identified."): added+=1
for sec in kn.values():
    if isinstance(sec,dict) and "erd1vd76pwhl4dyeyd8gylv6mkkvy7g4dnfezjuyp4j4x3wwnauga57q53m3z0" in sec:
        e_=sec["erd1vd76pwhl4dyeyd8gylv6mkkvy7g4dnfezjuyp4j4x3wwnauga57q53m3z0"]
        e_["notes"]=(e_.get("notes","")+" Run #26: received 775,154 minted EGLD from a Sep 19 exploit fan-out wallet - probable exchange hot wallet, not an OTC operator (test unknown-whale-i-is-exchange).").strip()
hub=D["otc_hub_trace"]
for addr,rec in hub["inbound"].items():
    if rec.get("kind")!="router" or rec["amount"]<15000: continue
    terms={k:v for k,v in rec["terminals"].items() if not k.startswith("UNRESOLVED")}
    src=max(terms,key=terms.get) if terms else "unknown"
    if label_map.get(addr): continue
    if add_addr("exchange_routers",addr,f"{src}->OTC Desk Feeder (run #26)","router","otc_feeder",
       f"Zero-balance pass-through carrying {rec['amount']:,.0f} EGLD from {src} into the OTC desk complex in the 2026-09-14..2026-09-19 (pre-halt) window."):
        added+=1
for addr,rec in hub["outbound"].items():
    if rec.get("kind")!="router" or rec["amount"]<15000: continue
    terms={k:v for k,v in rec["terminals"].items() if not k.startswith("UNRESOLVED")}
    dst=max(terms,key=terms.get) if terms else "unknown"
    if label_map.get(addr): continue
    if add_addr("exchange_routers",addr,f"OTC Desk->{dst} Router (run #26)","router","otc_router",
       f"Zero-balance pass-through forwarding {rec['amount']:,.0f} EGLD from the OTC desks to {dst} in the 2026-09-14..2026-09-19 (pre-halt) window."):
        added+=1
kn.setdefault("_metadata",{})["last_updated"]=RD
json.dump(kn,open(f"{REPO}/data/known-addresses.json","w"),indent=2)
print("known-addresses.json: added",added)

# ---- learnings.json ----
def roll(arr,val,n=8):
    a=list(arr)+[val]
    return a[-n:] if len(a)>n else a
rbp=[r for r in learn["runs"] if r.get("run_number")!=26][-1]["running_baselines"]
_pct=R["pre_committed_tests"]
_res=[t for t in _pct if t.get("resolved_in_run")==26]
_res_n=len(_res); _open_n=sum(1 for t in _pct if t["status"]=="open")
_hit=100*sum(1 for t in _res if t.get("outcome")=="as_predicted")/_res_n if _res_n else 0.0
sr=econ["staked"]/econ["circulatingSupply"]
xxr=R["token_activity"]["xexchange"]; ob=R["whale_intelligence"]["demand_instruments"]["exchange_orderbook"]
new_baselines={
 "egld_price_usd":roll(rbp["egld_price_usd"],econ["price"]),
 # run #26: 24h venue metrics NOT EVALUABLE (chain halted) - not appended, so a zero
 # does not enter the z-score baseline
 "dex_volume_24h_usd":rbp["dex_volume_24h_usd"],
 "dex_volume_24h_egld":rbp.get("dex_volume_24h_egld",[]),
 "staked_egld":roll(rbp["staked_egld"],econ["staked"]),
 "mex_price_usd":roll(rbp["mex_price_usd"],xxr["mex_price_usd"]),
 "total_delegators":roll(rbp["total_delegators"],R["staking_intelligence"]["churn"]["total_delegators_current"]),
 "staked_ratio":roll(rbp["staked_ratio"],sr),
 "exchange_net_flow_egld":roll(rbp["exchange_net_flow_egld"],R["whale_intelligence"]["exchange_flows"]["net_change_egld"]),
 "otc_pipeline_throughput_egld_7d":roll(rbp["otc_pipeline_throughput_egld_7d"],round(otc["gross_outbound_egld_7d"])),
 "otc_net_one_way_egld_7d":roll(rbp.get("otc_net_one_way_egld_7d",[]),round(otc["net_one_way_egld_7d"])),
 "otc_desk_inventory_egld":roll(rbp.get("otc_desk_inventory_egld",[]),round(desks)),
 "otc_net_one_way_measured_windows":{**(rbp.get("otc_net_one_way_measured_windows") or {}),
   "2026-09-14..2026-09-19 halt (run #26, 5.3-day frame, wave #4)":round(otc["net_one_way_egld_7d"]),
   "2026-09-07..2026-09-19 halt (WAVE #4 netted feed-to-drain, two frames)":round(wave["net_one_way_egld"])},
 "otc_circularity_pct":{k:round(v,1) for k,v in otc["circularity_series_pct"].items()},
 "dex_turnover_ratio_pct":rbp.get("dex_turnover_ratio_pct",[]),
 "identifiable_bid_absorbed_egld_7d":roll(rbp.get("identifiable_bid_absorbed_egld_7d",[]),0.0),
 "binance_staking_custody_egld":roll(rbp.get("binance_staking_custody_egld") or [],exchange_balances["Binance Staking"]),
 "reward_compound_pct":roll(rbp.get("reward_compound_pct",[]),round(R["staking_intelligence"]["reward_behavior"]["compound_pct_at_function_level"],2)),
 "delegation_total_locked_egld":roll(rbp.get("delegation_total_locked_egld",[]),round(R["staking_intelligence"]["summary"]["total_delegated_egld"])),
 "usdt_supply":roll(rbp.get("usdt_supply",[]),round(O["tokens"]["stable"]["USDT-f8c08c"]["supply"])),
 "usdc_supply":roll(rbp.get("usdc_supply",[]),round(O["tokens"]["stable"]["USDC-c76f1f"]["supply"])),
 "unbonding_queue_undelegated_egld_7d":roll(rbp.get("unbonding_queue_undelegated_egld_7d",[]),round(sk["undelegated_week"])),
 "withdraw_egld_returned_7d":[round(O["withdraw_decoded"]["egld_returned_total"])],
 "withdrawal_breadth_ex_pipeline_egld":roll(rbp.get("withdrawal_breadth_ex_pipeline_egld",[]),round(R["whale_intelligence"]["demand_instruments"]["withdrawal_breadth"]["total_egld_ex_pipeline"])),
 # post-halt market readings are a closed book (transfers suspended) - kept, flagged, not appended
 "cex_spot_volume_7d_egld":rbp.get("cex_spot_volume_7d_egld",[]),
 "otc_delivery_share_of_spot_pct":rbp.get("otc_delivery_share_of_spot_pct",[]),
 "binance_bybit_bid_depth_2pct_usd":rbp.get("binance_bybit_bid_depth_2pct_usd",[]),
 "closed_book_readings_run26":{"cex_spot_volume_7d_egld":round(ob["spot_volume_7d_egld"]),"binance_bybit_bid_depth_2pct_usd":round(ob["binance_bybit_bid_depth_2pct_usd"])},
 "hmex_supply":roll(rbp.get("hmex_supply",[]),O["mex_recovery"]["hmex_supply"]),
 "pre_committed_tests_resolved":roll(rbp.get("pre_committed_tests_resolved",[]),_res_n),
 "pre_committed_test_hit_rate_pct":roll(rbp.get("pre_committed_test_hit_rate_pct",[]),round(_hit,1)),
 "pre_committed_tests_open":roll(rbp.get("pre_committed_tests_open",[]),_open_n)}
ml=R["meta_learning"]
entry={
 "date":RD,"run_number":26,
 "data_quality":{"endpoints_that_worked":ml["endpoints_that_worked"],"endpoints_that_failed":ml["endpoints_that_failed"],
   "api_quirks_discovered":ml["api_quirks"],"data_gaps":ml["data_gaps"]},
 "analysis_insights":{
   "what_worked":[
     "THE IMPLAUSIBILITY CHECK CAUGHT THE WEEK'S STORY. The derived stage printed an exchange net flow of +4.9M EGLD; instead of narrating it, the top-account list was checked against total supply, which exposed a 41.3M EGLD account, and /stats blocks not advancing exposed the halt.",
     "TRACING THE FAN-OUT BEFORE WRITING: one pass over the attacker's outbound and each hop's forwards quantified exactly how much minted EGLD reached which venue, which let every balance metric be netted cleanly.",
     "READING THE PAUSED POOL'S /transfers found the Hatom recovery contract and its 89 whitelisted sales, which the pool's /transactions list does not show.",
     "SEQUENTIAL SCRIPTS: collector, follow-up, reward scan and LSD sweep ran one after another with zero paged errors and 8 of 8 providers.",
     "SEEDED LSD SWEEP returned all six known protocols."],
   "what_needs_improvement":[
     "THE COLLECTOR HAS NO LIVENESS CHECK. It ran a full 7-day collection against a chain that had stopped 55 hours earlier and nothing in its output said so.",
     "audit_report.py has no total-supply sanity check; a single account above supply passed both gates' data layer.",
     "The order-book instrument was read in a closed market; its second data point is unusable as a WoW comparison.",
     "Unknown Whale I was labelled an OTC operator for seven runs on circumstantial evidence."],
   "surprising_findings":[
     "A VM-level exploit minted roughly 2.5x the EGLD supply in about an hour through doubling deposit/compound rounds, and the chain was halted about ten minutes after the cash-out began.",
     "EGLD fully recovered its post-halt low within two days while the chain was still down.",
     "Hatom's MEX recovery sold seized collateral into pools that were paused to everyone else, via a pause whitelist.",
     "The attacker's cash-out route ran through Unknown Whale I, an address the model had placed inside the OTC pipeline.",
     "Two lookalike wallets are address-poisoning the OTC routers."]},
 "methodology_changes":ml["methodology_changes"],
 "new_addresses_discovered":[f"{x['address']} - {x['label']}" for x in ml["new_addresses_discovered_detail"]]+[
   "12 exploit fan-out wallets and 2 address-poisoning lookalikes added under the new `incident` section of known-addresses.json"],
 "action_items_completed":ml["action_items_completed_detail"],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":ml["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":ml["dashboard_suggestions_followup"],
 "self_assessment":{
   "most_valuable_insight":ml["most_valuable_insight"],
   "actions_completed_count":7,"actions_attempted_count":7,
   "what_would_2x_next_week":"A liveness check and a total-supply check at the top of the collector, so a halt or an invalid-state event is detected in the first minute rather than discovered through an implausible derived number; then a restart-anchored window so post-recovery flows are measured from the first new block.",
   "pre_committed_test_for_next_run":"HALT-RECOVERY-CLEAN: attacker+contract+fan-out < 1,000 EGLD and pre-halt desk/custody/Hatom balances within 1% = clean. UNKNOWN WHALE I: >500 distinct 7d senders = exchange. FOURTH-DEREGISTRATION week 4. STAKED-RATIO-FLOOR resolves run #27."},
 "recommendations_for_next_run":ml["recommendations_for_next_run"]}
learn["runs"]=[r for r in learn["runs"] if r.get("run_number")!=26]
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #26; total runs",len(learn["runs"]))
