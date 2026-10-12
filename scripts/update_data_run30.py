#!/usr/bin/env python3
"""Run #30: refresh previous.json, known-addresses.json and append the learnings entry."""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-10-12"
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
R=json.load(open(f"{REPO}/reports/{RD}.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
learn=json.load(open(f"{REPO}/data/learnings.json"))
O=json.load(open("/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/b8b82f4e-fcb2-488c-b627-23fb854f5366/scratchpad/run30w/derived.json"))
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
   "volume_status":"run #30 24h volume evaluable (~2.7-day window)",
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
 "exchange_orderbook_latest":{"run":30,"rails":"partial",**{k:R["whale_intelligence"]["demand_instruments"]["exchange_orderbook"][k] for k in ("binance","bybit","upbit","coinbase","gate","all_venues","korea_premium_pct","upbit_share_of_volume_pct","spot_volume_7d_egld")}},
 "mex_pair_event":R["token_activity"]["xexchange"]["mex_pair_event"],
 "mex_incident_recovery":prev.get("mex_incident_recovery"),
 "chain_halt_incident":prev.get("chain_halt_incident"),
 "incident_addresses":sorted(INC_ADDRS),
 "incident_balances_at_halt":prev.get("incident_balances_at_halt"),
 "pre_halt_reference_balances":prev.get("pre_halt_reference_balances"),
 "halt_recovery_run27":prev["halt_recovery_run27"],
 "halt_recovery_run28":prev.get("halt_recovery_run28"),
  "halt_recovery_run29":prev.get("halt_recovery_run29"),
 "halt_recovery_run30":{k:R["whale_intelligence"]["halt_recovery"][k] for k in ("invalid_balances_egld_now","invalid_balances_egld_at_halt")},
 "exchange_rail_status_run27":prev.get("exchange_rail_status_run27"),
 "exchange_rail_status_run28":prev.get("exchange_rail_status_run28"),
 "exchange_rail_status_run29":prev.get("exchange_rail_status_latest"),
 "exchange_rail_status_latest":{"run":30,**{k:R["whale_intelligence"]["exchange_flows"]["rail_status"][k] for k in ("venues_open","venues_deposit_only","venues_closed","by_venue")},"restart_2_ts":1790263800},
 "exit_routes_run28":prev.get("exit_routes_run28"),
 "exit_routes_run29":prev.get("exit_routes_run29"),
 "exit_routes_run30":R["whale_intelligence"]["exit_routes"],
 "stablecoin_supply":{"USDC-c76f1f":O["tokens"]["stable"]["USDC-c76f1f"]["supply"],
                      "USDT-f8c08c":O["tokens"]["stable"]["USDT-f8c08c"]["supply"]},
 "otc_throughput_series":{k:round(v) for k,v in otc["gross_series_egld_7d"].items()},
 "otc_net_one_way_series":{k:round(v) for k,v in otc["net_one_way_series_egld_7d"].items()},
 "otc_circularity_measured_pct":{k:round(v,1) for k,v in otc["circularity_series_pct"].items()},
 "otc_desk_inventory_series":{**prev["otc_desk_inventory_series"],"run30":round(desks)},
 "otc_wave_window_netting":{"window":wave["window"],"gross_outbound_egld":round(wave["gross_outbound_egld"]),
   "circular_share_pct":round(wave["circular_share_pct"],1),
   "net_one_way_egld":round(wave["net_one_way_egld"]),
   "sum_of_weekly_nets_egld":round(wave["sum_of_weekly_nets_egld"]),
   "weekly_frame_overstatement_pct":round(wave["weekly_frame_overstatement_pct"],1)},
 "demand_instruments":{"dex_turnover_ratio_pct":R["token_activity"]["xexchange"]["turnover_ratio_pct"],
   "dex_volume_egld_24h":R["token_activity"]["xexchange"]["dex_volume_egld_24h"],
   "identifiable_bid_absorbed_egld_7d":0,"weeks_bid_at_zero":10,
   "weeks_bid_at_zero_in_last_four":4,
   "identifiable_bid_status":f"RETIRED (run #23). Run #30: the Mega Whale's +120,172 was a Coinbase-intermediated Whale B leg, not a bid. The 14 desk outbound terminals took {O['absorbers']['total_received']:,.0f} EGLD and ended the week holding {O['absorbers']['total_balance_held']:,.0f} between them. Run #23's received-minus-forwarded retention figure compared a multi-week inflow against a one-week outflow and is not usable; balance is the correct test.",
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
  {"address":"erd1r3w62vqmsux5e38p6vnueatmfcs8nr5lmg3s97x6rafqpgxfae0sxv9z0v","label":"Binance de-staking wallet - unDelegated 320,002 EGLD from binance_staking Oct 12 06:16 UTC, unbonds ~Oct 21. PRE-COMMITTED (binance-undelegation-destination)","balance_egld":b("erd1r3w62vqmsux5e38p6vnueatmfcs8nr5lmg3s97x6rafqpgxfae0sxv9z0v"),"weeks_tracked":1,"first_seen":RD},
  {"address":CUSTODY,"label":f"Binance Staking custody ({b(CUSTODY):,.0f}, +161,137 from the hot wallet Oct 12)","balance_egld":b(CUSTODY),"weeks_tracked":24,"first_seen":"2026-05-25"},
  {"address":BINANCE_HOT,"label":"Binance.com hot wallet - customer deposits lead withdrawals (+19.8K/day net of the custody move)","balance_egld":b(BINANCE_HOT),"weeks_tracked":8,"first_seen":"2026-08-31"},
  {"address":MEGA,"label":"Mega Whale erd18mv2z6r2 - +120,172 via Coinbase routing Oct 10 (Whale B leg). PRE-COMMITTED (mega-whale-coinbase-leg)","balance_egld":b(MEGA),"weeks_tracked":30,"first_seen":"2026-04-02"},
  {"address":"erd1at3jm3xvzxhdgt4f695l7l2f6r0tpkqjnemfpc0raam5e9xtjuqqs6fkul","label":"Unknown Whale B - sent 122,054 to Coinbase Oct 10 22:32, feeding the Mega Whale leg","balance_egld":b("erd1at3jm3xvzxhdgt4f695l7l2f6r0tpkqjnemfpc0raam5e9xtjuqqs6fkul"),"weeks_tracked":1,"first_seen":RD},
  {"address":CB_ROUTING,"label":"Coinbase Routing Wallet - passed 120,172 to the Mega Whale Oct 10","balance_egld":b(CB_ROUTING),"weeks_tracked":2,"first_seen":RD},
  {"address":"erd1fcxu3f0hlxyvnp7zvuqmf34zf5w782tst6vuqhm4dwq4ayjspdaqce0q49","label":"UPbit hot wallet - 3 small deposits, no withdrawals. Upbit caution review Oct 19-23. PRE-COMMITTED (korea-premium-arbitrage)","balance_egld":b("erd1fcxu3f0hlxyvnp7zvuqmf34zf5w782tst6vuqhm4dwq4ayjspdaqce0q49"),"weeks_tracked":4,"first_seen":"2026-09-28"},
  {"address":UPBIT_DESK,"label":"UPbit OTC Desk - quiet, no reload. PRE-COMMITTED (otc-pipeline-resumption)","balance_egld":b(UPBIT_DESK),"weeks_tracked":30,"first_seen":"2026-04-02"},
  {"address":DIST_DESK,"label":"OTC Distribution Wallet - 1,604 EGLD out in small clips that ended at Gate.io","balance_egld":b(DIST_DESK),"weeks_tracked":28,"first_seen":"2026-04-13"},
  {"address":"erd1d2anjjhad4xlcrcu8jkk99yhrflsg5skavxqpkxwamxq80lmmglqzw605j","label":"Cross-venue wallet: Binance.com + Bybit withdrawals, Gate.io deposits","balance_egld":None,"weeks_tracked":1,"first_seen":RD},
  {"address":"erd1hl5y4ahk2a52rf4znn69a62w8skjputp7h3wxfsyyq3kykj0j2uqt7vqmy","label":"Unknown Whale (erd1hl5y4a) - many small receives; probable exchange/payment hot wallet, linked to erd1vxa2vk","balance_egld":b("erd1hl5y4ahk2a52rf4znn69a62w8skjputp7h3wxfsyyq3kykj0j2uqt7vqmy"),"weeks_tracked":3,"first_seen":"2026-10-05"},
  {"address":"erd1a6lte0wqwwdjtt0nvv62c6pacltznzgq93gjxu6el44cx6lqx3fsu48u4l","label":"Probable exchange hot wallet (erd1a6lte0) - woke up: 17 inbound from 14 senders","balance_egld":b("erd1a6lte0wqwwdjtt0nvv62c6pacltznzgq93gjxu6el44cx6lqx3fsu48u4l"),"weeks_tracked":5,"first_seen":"2026-09-21"},
  {"address":"erd1y27r22e4svp6g985ednf0nnd383pq2tmhkkzf3g58wems07kgc5stex2ne","label":"OTC desk Oct 6 terminal - holder, nonce 1, 5,836 EGLD","balance_egld":None,"weeks_tracked":1,"first_seen":RD},
  {"address":"erd1kwvkch79edm9qtg3tlaylgm9yff04lr9vaszazuavxtqrffz6scqrvvjd2","label":"MultiversX VM exploit wallet (Sep 19) - dust","balance_egld":b("erd1kwvkch79edm9qtg3tlaylgm9yff04lr9vaszazuavxtqrffz6scqrvvjd2"),"weeks_tracked":5,"first_seen":"2026-09-21"},
  {"address":"erd1z7wyqlr64qhr5k3wu9qa4d6c6wszxx8s5n9qc7067ds9f9pv3stqppm63r","label":"ADDRESS-POISONING lookalike of the OTC Distribution Wallet - 0 inbound above dust","balance_egld":None,"weeks_tracked":5,"first_seen":"2026-09-21"},
  {"address":"erd1v6k4dxe72tg0d43pvxrhq0zhlg0z5p0r4jeww2wtazv8kjn0cugsryxnk5","label":"ADDRESS-POISONING lookalike of the UPbit OTC Desk - 0 inbound above dust","balance_egld":None,"weeks_tracked":5,"first_seen":"2026-09-21"},
  {"address":UNBOND,"label":"229,865 EGLD unbond - retired, ninth week unmoved","balance_egld":ub["balance"],"weeks_tracked":10,"first_seen":"2026-08-17"}]}
json.dump(new_prev,open(f"{REPO}/data/previous.json","w"),indent=2)
print("WROTE previous.json; top_accounts",len(top_accounts),"providers",len(staking_providers),"(FULL list incl. zero-locked)")

# ---- known-addresses.json ----
def add_addr(section,addr,name,category,subcategory,notes):
    kn.setdefault(section,{})
    if addr in kn[section]: return False
    kn[section][addr]={"name":name,"category":category,"subcategory":subcategory,"notes":notes,
                       "first_seen":RD,"discovered_run":30}
    return True
added=0
for sec,addr,name,cat_,sub,note in [
    ("exchange_routers","erd124tc2z7gzk0sg6uu4lequvwnevhd8jx0casskhwzf447zcl3at9sd6m3jz","Binance: staking-rewards pass-through","exchange_router","binance_destaking","Received 6,760 EGLD of binance_staking rewards claimed by the Binance de-staking wallet (Oct 12 06:17) and deposited it to the Binance.com hot wallet at 06:35."),
    ("unlabeled_whales","erd1d2anjjhad4xlcrcu8jkk99yhrflsg5skavxqpkxwamxq80lmmglqzw605j","Cross-venue arbitrage wallet (Binance/Bybit -> Gate.io)","other","arbitrage","Oct 10-12: withdrew 14,315 from Binance.com and 12,792 from Bybit, deposited 8,992 at Gate.io. Nonce 90."),
    ("unlabeled_whales","erd1y27r22e4svp6g985ednf0nnd383pq2tmhkkzf3g58wems07kgc5stex2ne","OTC desk terminal (Oct 6, holder)","other","otc_terminal","Received the UPbit OTC desk's 5,745 EGLD through routers on Oct 6; nonce 1, holds 5,836 EGLD, has sent nothing of value.")]:
    added+=add_addr(sec,addr,name,cat_,sub,note)
kn.setdefault("_metadata",{})["last_updated"]=RD
json.dump(kn,open(f"{REPO}/data/known-addresses.json","w"),indent=2)
print("known-addresses.json: added",added)

# ---- learnings.json ----
def roll(arr,val,n=8):
    a=list(arr)+[val]
    return a[-n:] if len(a)>n else a
rbp=[r for r in learn["runs"] if r.get("run_number")!=30][-1]["running_baselines"]
_pct=R["pre_committed_tests"]
_res=[t for t in _pct if t.get("resolved_in_run")==30]
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
 # PARTIAL RAILS (UPbit withdrawals closed) + ~2.7-day window: exchange flow and OTC series NOT appended
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
 # 4-day off-cadence window: NOT appended to the weekly series
 "unbonding_queue_undelegated_egld_7d":rbp.get("unbonding_queue_undelegated_egld_7d",[]),
 "unbonding_short_window_readings":{**(rbp.get("unbonding_short_window_readings") or {}),"run30_short":{"undelegated_egld":round(q["undelegated_egld"]),"withdraw_egld_returned":round(q["withdraw_egld_returned"]),"days":round(D["_period"]["window_days"],2)}},
 "withdraw_egld_returned_7d":rbp.get("withdraw_egld_returned_7d",[]),
 "withdrawal_breadth_ex_pipeline_egld":rbp.get("withdrawal_breadth_ex_pipeline_egld",[]),
 "cex_spot_volume_7d_egld":rbp.get("cex_spot_volume_7d_egld",[]),
 "otc_delivery_share_of_spot_pct":rbp.get("otc_delivery_share_of_spot_pct",[]),
 "binance_bybit_bid_depth_2pct_usd":rbp.get("binance_bybit_bid_depth_2pct_usd",[]),
 "closed_book_readings_run26":rbp.get("closed_book_readings_run26"),
 "closed_book_readings_run27":rbp.get("closed_book_readings_run27"),
 "partial_rail_readings_run28":rbp.get("partial_rail_readings_run28"),
 "partial_rail_readings_run29":rbp.get("partial_rail_readings_run29"),
 "partial_rail_readings_run30":{"window_days":round(D["_period"]["window_days"],2),"cex_spot_volume_7d_egld":round(ob["spot_volume_7d_egld"]),"binance_bybit_bid_depth_2pct_usd":round(ob["binance_bybit_bid_depth_2pct_usd"]),
   "korea_premium_pct":round(ob["korea_premium_pct"],1),"upbit_share_of_volume_pct":round(ob["upbit_share_of_volume_pct"],1),
   "exchange_net_flow_egld":round(R["whale_intelligence"]["exchange_flows"]["net_change_egld"]),
   "otc_gross_egld":round(otc["gross_outbound_egld_7d"]),"binance_com_deposits_egld":round(next(v["deposits_egld_7d"] for v in R["whale_intelligence"]["exchange_flows"]["rail_status"]["by_venue"] if v["venue"]=="Binance.com")),
   "venues_open":R["whale_intelligence"]["exchange_flows"]["rail_status"]["venues_open"]},
 "dex_exit_discount_pct":rbp.get("dex_exit_discount_pct",[]),
 "korea_premium_pct":roll(rbp.get("korea_premium_pct",[]),round(ob["korea_premium_pct"],1)),
 "hmex_supply":rbp.get("hmex_supply",[]),
 "pre_committed_tests_resolved":roll(rbp.get("pre_committed_tests_resolved",[]),_res_n),
 "pre_committed_test_hit_rate_pct":roll(rbp.get("pre_committed_test_hit_rate_pct",[]),round(_hit,1)),
 "pre_committed_tests_open":roll(rbp.get("pre_committed_tests_open",[]),_open_n)}
ml=R["meta_learning"]
entry={
 "date":RD,"run_number":30,
 "data_quality":{"endpoints_that_worked":ml["endpoints_that_worked"],"endpoints_that_failed":ml["endpoints_that_failed"],
   "api_quirks_discovered":ml["api_quirks"],"data_gaps":ml["data_gaps"]},
 "analysis_insights":{
   "what_worked":[
     "INTRA-ENTITY NETTING ON RAIL READINGS: Binance.com's raw Oct 12 withdrawals (187,532) were 86% one send to Binance's own custody; netting it turned an apparent drain into net customer deposits and resolved binance-deposit-persistence correctly.",
     "THE COLLECTOR-SIDE EXIT SCAN answered the exit-route question on the whole population of large withdraws, and showed the population was nearly empty.",
     "REUSING STORED LABEL HISTORY: the Whale B -> Coinbase -> Mega Whale leg was recognisable in minutes because the April notes on both wallets described the same pattern.",
     "Call-history classification (redeem vs liquidate) settled the Hatom EGLD market question without any balance inference."],
   "what_needs_improvement":[
     "The first collector launch hung for ~5 hours with buffered output; long passes must run unbuffered and be watched through the log.",
     "The new exit-route scan shipped with a classification bug (withdraw calls as re-delegation), caught on review; new classifiers need a hand-checked sample before use.",
     "No web check this run for Coinbase/Bybit/Upbit network notices.",
     "The report assembler is still copied and hand-patched each run."],
   "surprising_findings":[
     "Binance unDelegated 320,002 EGLD from its own provider and moved 161,137 into custody within four hours of each other.",
     "Coinbase's reopening minutes were used for a 120K whale-to-whale leg, repeating the April Whale B / Mega Whale pattern almost exactly.",
     "DEX volume roughly doubled in EGLD terms as CEX rails reopened, almost all of it WEGLD/USDC.",
     "Unknown Whale I received nothing with four major venues open, which ended its exchange hypothesis."]},
 "methodology_changes":ml["methodology_changes"],
 "new_addresses_discovered":ml["new_addresses_discovered_detail"],
 "action_items_completed":ml["action_items_completed_detail"],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":ml["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":ml["dashboard_suggestions_followup"],
 "self_assessment":{
   "most_valuable_insight":ml["most_valuable_insight"],
   "actions_completed_count":6,"actions_attempted_count":6,
   "what_would_2x_next_week":"A full 7-day window with arbitrage wallets netted out of venue flows, plus the Binance unbond traced on maturity: that would separate holder selling from venue churn and from exchange treasury moves.",
   "pre_committed_test_for_next_run":"BINANCE-UNDELEGATION-DESTINATION (run #31 or #32, after ~Oct 21). MEGA-WHALE-COINBASE-LEG by run #32. KOREA-PREMIUM-ARBITRAGE when UPbit has >= 20 depositors. OTC-PIPELINE-RESUMPTION through run #31."},
 "recommendations_for_next_run":ml["recommendations_for_next_run"]}
learn["runs"]=[r for r in learn["runs"] if r.get("run_number")!=30]
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #30; total runs",len(learn["runs"]))
