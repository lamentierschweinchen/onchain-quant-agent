#!/usr/bin/env python3
"""Run #25: refresh previous.json, known-addresses.json and append the learnings entry."""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-09-14"
D=json.load(open(f"{REPO}/data/collected/{RD}.json"))
R=json.load(open(f"{REPO}/reports/{RD}.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
learn=json.load(open(f"{REPO}/data/learnings.json"))
O=json.load(open("/tmp/run25w/derived.json"))

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
   "total_pairs":meco["marketPairs"],"mex_price_usd":R["token_activity"]["xexchange"]["mex_price_usd"],
   "mex_market_cap_usd":R["token_activity"]["xexchange"]["mex_market_cap_usd"],
   "mex_price_source":"coingecko - /mex/economics returns 0 while MEX/WEGLD is paused",
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
                        if (p_.get("staked_egld") or 0) >= 100} | {"SALSA: Liquid Staking":6419.960661549192,"VestaX Finance: Liquid Staking":1121.362402476542},
 "lsd_protocol_seeds":{"SALSA: Liquid Staking":"erd1qqqqqqqqqqqqqpgqaqxztq0y764dnet95jwtse5u5zkg92sfacts6h9su3",
                       "VestaX Finance: Liquid Staking":"erd1qqqqqqqqqqqqqpgqawus4zu5w2frmhh9rscjqnu9x6msfjya2d2sfw7tsn"},
 "exchange_orderbook":R["whale_intelligence"]["demand_instruments"]["exchange_orderbook"],
 "mex_pair_event":R["token_activity"]["xexchange"]["mex_pair_event"],
 "stablecoin_supply":{"USDC-c76f1f":O["tokens"]["stable"]["USDC-c76f1f"]["supply"],
                      "USDT-f8c08c":O["tokens"]["stable"]["USDT-f8c08c"]["supply"]},
 "otc_throughput_series":{k:round(v) for k,v in otc["gross_series_egld_7d"].items()},
 "otc_net_one_way_series":{k:round(v) for k,v in otc["net_one_way_series_egld_7d"].items()},
 "otc_circularity_measured_pct":{k:round(v,1) for k,v in otc["circularity_series_pct"].items()},
 "otc_desk_inventory_series":{**prev["otc_desk_inventory_series"],"run25":round(desks)},
 "otc_wave_window_netting":{"window":wave["window"],"gross_outbound_egld":round(wave["gross_outbound_egld"]),
   "circular_share_pct":round(wave["circular_share_pct"],1),
   "net_one_way_egld":round(wave["net_one_way_egld"]),
   "sum_of_weekly_nets_egld":round(wave["sum_of_weekly_nets_egld"]),
   "weekly_frame_overstatement_pct":round(wave["weekly_frame_overstatement_pct"],1)},
 "demand_instruments":{"dex_turnover_ratio_pct":R["token_activity"]["xexchange"]["turnover_ratio_pct"],
   "dex_volume_egld_24h":R["token_activity"]["xexchange"]["dex_volume_egld_24h"],
   "identifiable_bid_absorbed_egld_7d":0,"weeks_bid_at_zero":5,
   "weeks_bid_at_zero_in_last_four":4,
   "identifiable_bid_status":f"RETIRED (run #23; zero for a fifth week run #25). The 14 desk outbound terminals took {O['absorbers']['total_received']:,.0f} EGLD and ended the week holding {O['absorbers']['total_balance_held']:,.0f} between them. Run #23's received-minus-forwarded retention figure compared a multi-week inflow against a one-week outflow and is not usable; balance is the correct test.",
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
  {"address":UPBIT_DESK,"label":f"UPbit OTC Desk (wave #4: UPbit tranche {otc['upbit_reload_egld']:,.0f}; combined desks {desks:,.0f} after delivering {otc['net_one_way_egld_7d']:,.0f} one-way. Aug 17 - Sep 14 netted {wave['net_one_way_egld']:,.0f}. PRE-COMMITTED (delivery-price-relevance): delivery >300,000 with EGLD more than 5pp behind BTC = price-relevant supply)","balance_egld":b(UPBIT_DESK),"weeks_tracked":25,"first_seen":"2026-04-02"},
  {"address":DIST_DESK,"label":f"OTC Distribution Wallet (at {b(DIST_DESK):,.0f}; circularity {otc['circular_share_pct']:.0f}%, below the band - a straddle week)","balance_egld":b(DIST_DESK),"weeks_tracked":23,"first_seen":"2026-04-13"},
  {"address":"erd1qqqqqqqqqqqqqpgqa0fsfshnff4n76jhcye6k7uvd7qacsq42jpsp6shh2","label":"xExchange MEX/WEGLD pair - PAUSED 2026-09-13 16:43 UTC by the router owner. 191B MEX + 141,281 WEGLD inside, 172 failed txs. PRE-COMMITTED (mex-pair-resume): still paused/delisted at run #27 = MEX price discovery left the chain; resumed with MEX < 8.2e-07 = squeeze incident; resumed with MEX >= 8.2e-07 = repricing stuck. Query function=resume/setState and successful removeLiquidity","balance_egld":0.0,"weeks_tracked":1,"first_seen":RD},
  {"address":"erd1ss6u80ruas2phpmr82r42xnkd6rxy40g9jl69frppl4qez9w2jpsqj8x97","label":"xExchange router owner / admin wallet - sent the MEX/WEGLD pause. Scan its outbound for pause/resume calls on other pairs","balance_egld":None,"weeks_tracked":1,"first_seen":RD},
  {"address":CUSTODY,"label":f"Binance Staking custody (+{cust['delta']:,.0f} to {b(CUSTODY):,.0f}, second week of refill from the hot wallet; not a supply signal while the feed runs alongside)","balance_egld":b(CUSTODY),"weeks_tracked":19,"first_seen":"2026-05-25"},
  {"address":BINANCE_HOT,"label":f"Binance.com hot wallet ({b(BINANCE_HOT):,.0f}). Sent {HOT['total_egld']:,.0f} EGLD to OTC feeders/routers, day-sliced and uncapped - third week above 50,000: a permanent funding line. Keep querying by day","balance_egld":b(BINANCE_HOT),"weeks_tracked":3,"first_seen":"2026-08-31"},
  {"address":"erd1ytpenkzjucgq7mxu4l6u8v72vfxxlux2237925glajhs4dj3u8asue9arn","label":"Bybit/Gate.io -> OTC desk feeder (run #24's largest unattributed feeder, resolved by a two-hop back-trace)","balance_egld":None,"weeks_tracked":2,"first_seen":"2026-09-07"},
  {"address":LEDGERBYFIGMENT,"label":f"ledgerbyfigment - zero-stake, delegators {dser.get('ledgerbyfigment',{}).get('users',0):,} ({dser.get('ledgerbyfigment',{}).get('users_delta',0):+d}); participation-inertia decay series","balance_egld":0.0,"weeks_tracked":3,"first_seen":"2026-08-31"},
  {"address":P2P_PROVIDER,"label":f"p2p_org_ - exited; {dser.get('p2p_org_',{}).get('users',0):,} delegators attached. PRE-COMMITTED (fourth-deregistration, week 3 of 4, TRANSITION basis)","balance_egld":0.0,"weeks_tracked":4,"first_seen":"2026-08-24"},
  {"address":MEGA,"label":f"Mega Whale erd18mv2z6r2 - retired bid instrument, zero for a fifth week","balance_egld":b(MEGA),"weeks_tracked":25,"first_seen":"2026-04-02"},
  {"address":UNBOND,"label":f"229,865 EGLD unbond - retired, fourth week unmoved","balance_egld":ub["balance"],"weeks_tracked":5,"first_seen":"2026-08-17"},
  {"address":"erd1tx933j8r57smz7s7c6y4p4nzx9np968gpt66escfym3908k3zcqqcde3y8","label":f"Binance hot-funded unlabelled whale - largest ex-pipeline withdrawal recipient again ({br['top'][0]['egld']:,.0f} EGLD)","balance_egld":None,"weeks_tracked":2,"first_seen":"2026-09-07"}]}
json.dump(new_prev,open(f"{REPO}/data/previous.json","w"),indent=2)
print("WROTE previous.json; top_accounts",len(top_accounts),"providers",len(staking_providers),"(FULL list incl. zero-locked)")

# ---- known-addresses.json ----
def add_addr(section,addr,name,category,subcategory,notes):
    kn.setdefault(section,{})
    if addr in kn[section]: return False
    kn[section][addr]={"name":name,"category":category,"subcategory":subcategory,"notes":notes,
                       "first_seen":RD,"discovered_run":25}
    return True
added=0
for nm,ad in [("JEXchange: live aggregator router 2 (run #25)","erd1qqqqqqqqqqqqqpgqahn5kpu95tsd8sr9swtp7kj30c5nc0k36avst0muvv"),
              ("JEXchange: live aggregator router 3 (run #25)","erd1qqqqqqqqqqqqqpgqahfmv4apudlzgawgcvp2zr65dtufqfmy6avsazkewu"),
              ("JEXchange: live aggregator router 4 (run #25)","erd1qqqqqqqqqqqqqpgqypzse2xtacw5a2wnjv2v2n7sumyymdm96avsv022ct"),
              ("JEXchange: live aggregator router 5 (run #25)","erd1qqqqqqqqqqqqqpgqc75pqw9ye84c7v3cncnhwp7ys5kcet7m6avscyfyj3")]:
    if add_addr("defi_jexchange",ad,nm,"defi","dex_aggregator","Secondary router behind the re-derived JEXchange aggregator; promoted into the collector protocol set run #25."): added+=1
if add_addr("defi_xexchange","erd1qqqqqqqqqqqqqpgqa0fsfshnff4n76jhcye6k7uvd7qacsq42jpsp6shh2","xExchange: MEX/WEGLD pair (PAUSED 2026-09-13)","defi","dex_pair",
   "Paused 2026-09-13 16:43 UTC (tx b0decfa361def3e21753a1a1f59df1f3a09f7e256a6332e366ba9d4e5f2a8253) by the router owner; dropped from /mex/pairs; 191B MEX + 141,281 WEGLD reserves; 172 failed txs in the week."): added+=1
if add_addr("defi_xexchange","erd1ss6u80ruas2phpmr82r42xnkd6rxy40g9jl69frppl4qez9w2jpsqj8x97","xExchange: router owner / admin","defi","admin",
   "Owner of the xExchange router contract that owns the pairs; sent the MEX/WEGLD pause on 2026-09-13."): added+=1
# relabel the resolved feeder
for sec in kn.values():
    if isinstance(sec,dict) and "erd1ytpenkzjucgq7mxu4l6u8v72vfxxlux2237925glajhs4dj3u8asue9arn" in sec:
        sec["erd1ytpenkzjucgq7mxu4l6u8v72vfxxlux2237925glajhs4dj3u8asue9arn"]["name"]="Bybit/Gate.io->OTC Desk Feeder (resolved run #25)"
        sec["erd1ytpenkzjucgq7mxu4l6u8v72vfxxlux2237925glajhs4dj3u8asue9arn"]["notes"]=(sec["erd1ytpenkzjucgq7mxu4l6u8v72vfxxlux2237925glajhs4dj3u8asue9arn"].get("notes","")+" Run #25 two-hop back-trace: fed by Bybit and Gate.io over Aug 17 - Sep 14.").strip()
hub=D["otc_hub_trace"]
for addr,rec in hub["inbound"].items():
    if rec.get("kind")!="router" or rec["amount"]<15000: continue
    terms={k:v for k,v in rec["terminals"].items() if not k.startswith("UNRESOLVED")}
    src=max(terms,key=terms.get) if terms else "unknown"
    if label_map.get(addr): continue
    if add_addr("exchange_routers",addr,f"{src}->OTC Desk Feeder (run #25)","router","otc_feeder",
       f"Zero-balance pass-through carrying {rec['amount']:,.0f} EGLD from {src} into the OTC desk complex in the 2026-09-07..2026-09-14 window."):
        added+=1
for addr,rec in hub["outbound"].items():
    if rec.get("kind")!="router" or rec["amount"]<15000: continue
    terms={k:v for k,v in rec["terminals"].items() if not k.startswith("UNRESOLVED")}
    dst=max(terms,key=terms.get) if terms else "unknown"
    if label_map.get(addr): continue
    if add_addr("exchange_routers",addr,f"OTC Desk->{dst} Router (run #25)","router","otc_router",
       f"Zero-balance pass-through forwarding {rec['amount']:,.0f} EGLD from the OTC desks to {dst} in the 2026-09-07..2026-09-14 window."):
        added+=1
kn.setdefault("_metadata",{})["last_updated"]=RD
json.dump(kn,open(f"{REPO}/data/known-addresses.json","w"),indent=2)
print("known-addresses.json: added",added)

# ---- learnings.json ----
def roll(arr,val,n=8):
    a=list(arr)+[val]
    return a[-n:] if len(a)>n else a
# baselines must roll off the PREVIOUS run, not off a partial re-run of this one
rbp=[r for r in learn["runs"] if r.get("run_number")!=25][-1]["running_baselines"]
_pct=R["pre_committed_tests"]
_res=[t for t in _pct if t.get("resolved_in_run")==25]
_res_n=len(_res); _open_n=sum(1 for t in _pct if t["status"]=="open")
_hit=100*sum(1 for t in _res if t.get("outcome")=="as_predicted")/_res_n if _res_n else 0.0
sr=econ["staked"]/econ["circulatingSupply"]
xxr=R["token_activity"]["xexchange"]
new_baselines={
 "egld_price_usd":roll(rbp["egld_price_usd"],econ["price"]),
 "dex_volume_24h_usd":roll(rbp["dex_volume_24h_usd"],xxr["total_volume_24h_usd"]),
 "dex_volume_24h_egld":roll(rbp.get("dex_volume_24h_egld",[]),round(xxr["dex_volume_egld_24h"])),
 "staked_egld":roll(rbp["staked_egld"],econ["staked"]),
 "mex_price_usd":roll(rbp["mex_price_usd"],R["token_activity"]["xexchange"]["mex_price_usd"]),
 "total_delegators":roll(rbp["total_delegators"],R["staking_intelligence"]["churn"]["total_delegators_current"]),
 "staked_ratio":roll(rbp["staked_ratio"],sr),
 "exchange_net_flow_egld":roll(rbp["exchange_net_flow_egld"],R["whale_intelligence"]["exchange_flows"]["net_change_egld"]),
 "otc_pipeline_throughput_egld_7d":roll(rbp["otc_pipeline_throughput_egld_7d"],round(otc["gross_outbound_egld_7d"])),
 "otc_net_one_way_egld_7d":roll(rbp.get("otc_net_one_way_egld_7d",[]),round(otc["net_one_way_egld_7d"])),
 "otc_desk_inventory_egld":roll(rbp.get("otc_desk_inventory_egld",[]),round(desks)),
 "otc_net_one_way_measured_windows":{
   **(rbp.get("otc_net_one_way_measured_windows") or {}),
   "2026-09-07..2026-09-14 (run #25, weekly frame, wave #4)":round(otc["net_one_way_egld_7d"]),
   "2026-08-17..2026-09-14 (waves #3+#4 netted as one window, four frames)":round(wave["net_one_way_egld"])},
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
 "cex_spot_volume_7d_egld":roll(rbp.get("cex_spot_volume_7d_egld",[]),round(R["whale_intelligence"]["demand_instruments"]["exchange_orderbook"]["spot_volume_7d_egld"])),
 "otc_delivery_share_of_spot_pct":roll(rbp.get("otc_delivery_share_of_spot_pct",[]),round(R["whale_intelligence"]["demand_instruments"]["exchange_orderbook"]["net_one_way_share_of_spot_volume_pct"],2)),
 "binance_bybit_bid_depth_2pct_usd":roll(rbp.get("binance_bybit_bid_depth_2pct_usd",[]),round(R["whale_intelligence"]["demand_instruments"]["exchange_orderbook"]["binance_bybit_bid_depth_2pct_usd"])),
 "hmex_supply":roll(rbp.get("hmex_supply",[]),O["mex_event"]["hmex_supply"]),
 "pre_committed_tests_resolved":roll(rbp.get("pre_committed_tests_resolved",[]),_res_n),
 "pre_committed_test_hit_rate_pct":roll(rbp.get("pre_committed_test_hit_rate_pct",[]),round(_hit,1)),
 "pre_committed_tests_open":roll(rbp.get("pre_committed_tests_open",[]),_open_n)}

entry={
 "date":RD,"run_number":25,
 "data_quality":{
   "endpoints_that_worked":R["meta_learning"]["endpoints_that_worked"],
   "endpoints_that_failed":R["meta_learning"]["endpoints_that_failed"],
   "api_quirks_discovered":R["meta_learning"]["api_quirks"],
   "data_gaps":R["meta_learning"]["data_gaps"]},
 "analysis_insights":{
   "what_worked":[
     "READING VENUE STATE FROM THE CONTRACT. /mex/economics returning MEX at $0 looked like an API outage; the pair contract's own transaction list showed a `pause` call with a timestamp, a sender and 172 failed calls after it. The headline of the week came from refusing to treat an absent row as missing data.",
     "THE FIRST EXCHANGE-SIDE INSTRUMENT paid off in its first run: CoinGecko per-venue depth and 7d spot volume put the record delivery at ~2% of turnover and withdrew run #24's 'invisible bid' framing.",
     "DAY-SLICED BINANCE HOT-WALLET SCAN in the main pass: 772 txs, zero capped slices, no follow-up needed.",
     "TWO-HOP BACK-TRACE OF FEEDERS resolved run #24's largest unattributed feeder in one pass (Bybit + Gate.io).",
     "PAGED ERROR RECORDING made the 429 damage recoverable: the collector logged two failed wave legs as errors, and followup_run25.py re-paged them and rebuilt the four-week trace.",
     "CROSS-CHECKING IMPLAUSIBLE NUMBERS BEFORE WRITING: a 177,587 EGLD provider exit (identity rename), a +44% Hatom Lending move (HMEX priced off a frozen pool) and a 46.8% compound rate from 4 providers (rate-limited sample) were all caught before publication."],
   "what_needs_improvement":[
     "RUNNING delegator_behavior.py CONCURRENTLY WITH THE COLLECTOR tripped the shared rate limit. It damaged the wave trace and silently halved the reward sample. Scripts must run sequentially, and delegator_behavior.py needs the paged_txs error guard.",
     "THE LIQUID-STAKING SWEEP DROPPED TWO KNOWN PROTOCOLS. Discovery must seed from last week's finds.",
     "IDENTITY-KEYED PROVIDER JOINS break on renames. The collector still joins on identity; only the assembler falls back to address.",
     "WITHDRAW AMOUNTS ARE NOT DECODED, so the staked-ratio attribution rests on timing.",
     "THE BILATERAL INVERSE RULE has been partly mechanical all along: dollar collateral rises in EGLD terms when EGLD falls. The behavioural test is the HEGLD leg, and it failed this week."],
   "surprising_findings":[
     "xExchange paused its #2 deepest pool, and MEX went UP ~7.5x the next day rather than down.",
     "HMEX supply rose 672% in the pause week: MEX went into Hatom rather than out through the pool.",
     "The compound rate fell from the series high to the series low in one week (62.05% -> 49.44%), and none of the retail claims were sold.",
     "Staked EGLD fell 156,538 while delegation TVL rose 35,617.",
     "USDT supply -12.8% and USDC +2.7% in the same week."]},
 "methodology_changes":R["meta_learning"]["methodology_changes"],
 "new_addresses_discovered":[
   "erd1qqqqqqqqqqqqqpgqa0fsfshnff4n76jhcye6k7uvd7qacsq42jpsp6shh2 - xExchange MEX/WEGLD pair, PAUSED 2026-09-13 16:43 UTC (added under defi_xexchange)",
   "erd1ss6u80ruas2phpmr82r42xnkd6rxy40g9jl69frppl4qez9w2jpsqj8x97 - xExchange router owner/admin, sent the pause (added under defi_xexchange)",
   "erd1ytpenkzjucgq7mxu4l6u8v72vfxxlux2237925glajhs4dj3u8asue9arn - relabelled Bybit/Gate.io->OTC Desk Feeder after a two-hop back-trace",
   "Four secondary JEXchange routers added under defi_jexchange; new desk feeder/router wallets >15K EGLD labelled from this week's hub trace",
   "Provider identity renames (not new addresses): cslabsio -> chainstatelabs (erd1...phllllsndz99p), kevinlallement -> dinovox (erd1...dlllllszljs2d)"],
 "action_items_completed":R["meta_learning"]["action_items_completed_detail"],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":R["meta_learning"]["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":R["meta_learning"]["dashboard_suggestions_followup"],
 "self_assessment":{
   "most_valuable_insight":R["meta_learning"]["most_valuable_insight"],
   "actions_completed_count":9,"actions_attempted_count":9,
   "what_would_2x_next_week":("Decode the xExchange admin wallet's recent calls across ALL pairs and the MEX pair's state, so the pause is read as part of a pattern or as a one-off; and turn the one-snapshot order-book reading into a WoW series for Binance and Bybit, the pipeline's two delivery venues. Those two change what the report can say about the two biggest open questions: why MEX has no on-chain price, and whether the desks' supply moves EGLD."),
   "pre_committed_test_for_next_run":("MEX PAIR: still paused at run #27 = structural; resumed with MEX < 8.2e-07 = squeeze incident. "
     "DELIVERY-PRICE-RELEVANCE: delivery >300,000 and EGLD more than 5pp behind BTC = price-relevant supply. "
     "COMPOUND: <52% = regime switch; >=55% = one-week reaction. STAKED RATIO: <46.30% by run #27 = exits continuing.")},
 "recommendations_for_next_run":R["meta_learning"]["recommendations_for_next_run"]}
learn["runs"]=[r for r in learn["runs"] if r.get("run_number")!=25]
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #25; total runs",len(learn["runs"]))
for k in ["egld_price_usd","otc_net_one_way_egld_7d","otc_desk_inventory_egld","dex_turnover_ratio_pct","dex_volume_24h_egld","reward_compound_pct","pre_committed_test_hit_rate_pct"]:
    print("  baseline",k,new_baselines[k])
