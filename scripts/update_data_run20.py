#!/usr/bin/env python3
"""Run #20: refresh previous.json, known-addresses.json and append the learnings entry."""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D=json.load(open(f"{REPO}/data/collected/2026-08-10.json"))
R=json.load(open(f"{REPO}/reports/2026-08-10.json"))
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
otc=R["whale_intelligence"]["otc_pipeline"]

# ---- previous.json ----
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
CB_ROUTING="erd1lgdltequh7627rtlacmcp6p5vec7zmu2rxhu7pjwvcja8f4a9gqq9vcc70"
SRC17="erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh"
FUNDER="erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp"
XOXNO_LSD="erd1qqqqqqqqqqqqqpgq6uzdzy54wnesfnlaycxwymrn9texlnmyah0ssrfvk6"
CUST_FUNDER="erd1r3w62vqmsux5e38p6vnueatmfcs8nr5lmg3s97x6rafqpgxfae0sxv9z0v"
WHALE_I="erd1vd76pwhl4dyev8tvqf6y0ny78dv3xzcalpfhqcqhkr9tpne9tk4qkcgt6r"
# resolve Whale I's exact address from the snapshot rather than trusting a literal
for a in acc:
    if "Whale I" in lab(a): WHALE_I=a

new_prev={
 "snapshot_date":"2026-08-10",
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
   "mex_price_usd":meco["price"],"mex_market_cap_usd":meco["marketCap"],
   "pool_tvl_usd":R["token_activity"]["xexchange"]["pool_tvl_usd"],
   "turnover_ratio_pct":R["token_activity"]["xexchange"]["turnover_ratio_pct"]},
 "lsd_supply":{tid:D["tvl_tokens"].get(tid,{}).get("supply") for tid in ["SEGLD-3ad2d0","XEGLD-e413ed","SWTAO-356a25","USH-111e09"]},
 # GROSS paginated throughput, net of desk-to-desk only. Run #19 extended it one window left
 # (run #12) and showed that gross is NOT net of round-trip circularity - see otc_net_one_way.
 "otc_throughput_series":{k:round(v) for k,v in otc["gross_series_egld_7d"].items()},
 # NET one-way: three MEASURED anchors now (run #17 peak re-netted this run, run #19, run #20).
 # Runs #13-#16 and #18 remain gross-only. Do NOT interpolate them from the constant-circularity
 # observation without measuring at least one more window.
 "otc_net_one_way_series":{k:round(v) for k,v in otc["net_one_way_series_egld_7d"].items()},
 "otc_circularity_measured_pct":{"run17_peak":round(otc["peak_window_renetted"]["circular_share_pct"],1),
                                 "run19":80.0,"run20":round(otc["circular_share_pct"],1)},
 "demand_instruments":{"dex_turnover_ratio_pct":R["token_activity"]["xexchange"]["turnover_ratio_pct"],
   "identifiable_bid_absorbed_egld_7d":R["whale_intelligence"]["demand_instruments"]["identifiable_bid_absorbed_egld_7d"],"weeks_bid_at_zero":0,
   "withdrawal_breadth_ex_pipeline":R["whale_intelligence"]["demand_instruments"]["withdrawal_breadth"]},
 "watch_addresses":[
   {"address":UPBIT_DESK,"label":f"UPbit OTC Desk (WAVE #2: UPbit fed a 319,000 tranche, 4.8x last week and past the 200K pre-committed threshold; desk at {b(UPBIT_DESK):,.0f})","balance_egld":b(UPBIT_DESK),"weeks_tracked":20,"first_seen":"2026-04-02"},
   {"address":DIST_DESK,"label":f"OTC Distribution Wallet (combined desk balance 63,795, -1,259 - passing flow through rather than accumulating. Gross 604,086, NET one-way 188,658, 69% circular)","balance_egld":b(DIST_DESK),"weeks_tracked":18,"first_seen":"2026-04-13"},
   {"address":CUSTODY,"label":"Binance Staking custody (PARKED 2nd week, zero txs, unchanged at 3,357,101. The 150,000 traced in run #19 to the completed delegation unwind is still sitting there. Registered branches: drawdown to hot = distribution continues; re-delegation = first constructive Binance signal in 6 runs)","balance_egld":b(CUSTODY),"weeks_tracked":14,"first_seen":"2026-05-11"},
   {"address":MEGA,"label":"Mega Whale erd18mv2z6r2 (REACTIVATED: took 5,748 EGLD from the Coinbase Routing pipe after two zero weeks, so the 3-week dormancy promotion is CANCELLED. But that is only 3% of the week's net OTC distribution. Watch tranche SIZE - 30-50K would mean the bid is genuinely back, another sub-10K week means maintenance)","balance_egld":b(MEGA),"weeks_tracked":17,"first_seen":"2026-04-20"},
   {"address":CB_ROUTING,"label":"Coinbase Routing Wallet (REFILLED: received 5,764 EGLD from a Coinbase hot wallet after two weeks dry at 77.13, and forwarded it to the absorber. This was run #19's pre-registered 'earliest observable reversal' and it fired)","balance_egld":b(CB_ROUTING),"weeks_tracked":3,"first_seen":"2026-07-27"},
   {"address":WHALE_I,"label":"Unknown Whale I - PROFILED, not identified. Nonce 10,169, 20,794 lifetime txs, 15-75 txs/day, ~80-110 distinct counterparties, 2 tokens / 8 NFTs. Appears on BOTH sides of the OTC hub in every window measured. Behavioural profile = OTC operator inventory / market-making wallet, not an end buyer. TEST: if >60% of counterparties by value are hub feeders/routers, net it out of the one-way distribution figure (would cut 188,658 to ~175,818)","balance_egld":b(WHALE_I),"weeks_tracked":2,"first_seen":"2026-08-03"},
   {"address":XOXNO_LSD,"label":"XOXNO LSD contract (XEGLD supply -2.23% on a FLAT price week - the first XOXNO redemption in tracking without a drawdown driver, ~5,250 redeemed, while SEGLD was flat to 3 decimals. TRACE the contract's outbound flows: native delegation = migration/constructive, exchange = exit/bearish)","balance_egld":b(XOXNO_LSD) or 0,"weeks_tracked":7,"first_seen":"2026-06-29"},
   {"address":SRC17,"label":"OTC source erd17l22 (inventory parked, not pushing)","balance_egld":b(SRC17),"weeks_tracked":14,"first_seen":"2026-05-11"},
   {"address":FUNDER,"label":"OTC source funder (Binance.com -> erd17l22 pass-through)","balance_egld":b(FUNDER) or 0,"weeks_tracked":12,"first_seen":"2026-05-25"},
   {"address":CUST_FUNDER,"label":"Binance de-staking withdrawal wallet erd1r3w62vq (RESOLVED in run #19: unDelegate + withdraw on the binance_staking delegation contract, then 150,000 to custody. Quiet this week)","balance_egld":b(CUST_FUNDER),"weeks_tracked":3,"first_seen":"2026-07-27"}]}
json.dump(new_prev,open(f"{REPO}/data/previous.json","w"),indent=2)
print("WROTE previous.json; top_accounts",len(top_accounts),"providers",len(staking_providers))

# ---- known-addresses.json: label the OTC hub wallets discovered this run ----
newly={
 "erd1ytpenkzjucgq7mxucm5t5sgkvhqfa25vp0hf6nqz5vg6ry5gsxlqhc9x0z":None,  # placeholder, resolved below
}
hub=D["otc_hub_trace"]
def add_addr(section,addr,name,category,subcategory,notes):
    kn.setdefault(section,{})
    if addr in kn[section]: return False
    kn[section][addr]={"name":name,"category":category,"subcategory":subcategory,
                       "notes":notes,"first_seen":"2026-08-10","discovered_run":20}
    return True
added=0
# inbound feeders (venue -> desk), labelled by their dominant source venue
for addr,rec in hub["inbound"].items():
    if rec.get("kind")!="router" or rec["amount"]<20000: continue
    terms={k:v for k,v in rec["terminals"].items() if not k.startswith("UNRESOLVED")}
    src=max(terms,key=terms.get) if terms else "unknown"
    if label_map.get(addr): continue
    if add_addr("exchange_routers",addr,f"{src}->OTC Desk Feeder (run #20)","router","otc_feeder",
                f"Zero-balance pass-through that carried {rec['amount']:,.0f} EGLD from {src} into the UPbit OTC desk complex in the 2026-08-03..2026-08-10 window. Inbound leg of the circular desk hub."):
        added+=1
# outbound routers terminating at a venue
for addr,rec in hub["outbound"].items():
    if rec.get("kind")!="router" or rec["amount"]<20000: continue
    terms={k:v for k,v in rec["terminals"].items() if not k.startswith("UNRESOLVED")}
    dst=max(terms,key=terms.get) if terms else "unknown"
    if label_map.get(addr): continue
    if add_addr("exchange_routers",addr,f"OTC Desk->{dst} Router (run #20)","router","otc_router",
                f"Zero-balance pass-through that forwarded {rec['amount']:,.0f} EGLD from the OTC desks to {dst} in the 2026-08-03..2026-08-10 window."):
        added+=1
# the custody funder is now identified
if CUST_FUNDER not in label_map:
    if add_addr("exchange_routers",CUST_FUNDER,"Binance: de-staking withdrawal wallet","exchange","binance_destaking",
                "Calls unDelegate/withdraw on the binance_staking delegation contract and forwards the proceeds to the Binance Staking custody wallet. Sent the +150,000 custody 'reload' on 2026-07-22, which run #18 had read as external accumulation."):
        added+=1
kn.setdefault("_metadata",{})["last_updated"]="2026-08-10"
json.dump(kn,open(f"{REPO}/data/known-addresses.json","w"),indent=2)
print("known-addresses.json: added",added,"addresses")

# ---- learnings.json append ----
def roll(arr,val,n=8):
    a=list(arr)+[val]
    return a[-n:] if len(a)>n else a
rbprev=learn["runs"][-1]["running_baselines"]
sr_cur=econ["staked"]/econ["circulatingSupply"]
new_baselines={
 "egld_price_usd":roll(rbprev["egld_price_usd"],econ["price"]),
 "dex_volume_24h_usd":roll(rbprev["dex_volume_24h_usd"],R["token_activity"]["xexchange"]["total_volume_24h_usd"]),
 "staked_egld":roll(rbprev["staked_egld"],econ["staked"]),
 "mex_price_usd":roll(rbprev["mex_price_usd"],meco["price"]),
 "total_delegators":roll(rbprev["total_delegators"],R["staking_intelligence"]["churn"]["total_delegators_current"]),
 "staked_ratio":roll(rbprev["staked_ratio"],sr_cur),
 "exchange_net_flow_egld":roll(rbprev.get("exchange_net_flow_egld",[]),R["whale_intelligence"]["exchange_flows"]["net_change_egld"]),
 # GROSS series - appended (same units as run #18's replacement array), run #12 window prepended
 "otc_pipeline_throughput_egld_7d":roll(rbprev["otc_pipeline_throughput_egld_7d"],round(otc["gross_outbound_egld_7d"])),
 # NET one-way array: run #19's single point, plus this run's. The re-netted run #17 PEAK is a
 # non-contiguous historical window and is stored in otc_net_one_way_measured_windows, NOT appended
 # here - appending it would put a Jul 13-20 value after an Aug 3-10 one (run #18's units lesson,
 # applied to the time axis rather than the unit).
 "otc_net_one_way_egld_7d":roll(rbprev.get("otc_net_one_way_egld_7d",[]),round(otc["net_one_way_egld_7d"])),
 "otc_net_one_way_measured_windows":{"2026-07-13..2026-07-20 (run #17 peak, re-netted run #20)":round(otc["peak_window_renetted"]["net_one_way_egld"]),
                                     "2026-07-27..2026-08-03 (run #19)":61435,
                                     "2026-08-03..2026-08-10 (run #20)":round(otc["net_one_way_egld_7d"])},
 "dex_turnover_ratio_pct":roll(rbprev.get("dex_turnover_ratio_pct",[]),round(R["token_activity"]["xexchange"]["turnover_ratio_pct"],3)),
 "identifiable_bid_absorbed_egld_7d":roll(rbprev.get("identifiable_bid_absorbed_egld_7d",[]),round(R["whale_intelligence"]["demand_instruments"]["identifiable_bid_absorbed_egld_7d"],1)),
 "binance_staking_custody_egld":roll(rbprev.get("binance_staking_custody_egld") or [],exchange_balances["Binance Staking"]),
 "reward_compound_pct":roll(rbprev.get("reward_compound_pct",[]),round(R["staking_intelligence"].get("reward_behavior",{}).get("compound_pct_at_function_level",0),2))}

entry={
 "date":"2026-08-10","run_number":20,
 "data_quality":{
   "endpoints_that_worked":R["meta_learning"]["endpoints_that_worked"],
   "endpoints_that_failed":R["meta_learning"]["endpoints_that_failed"],
   "api_quirks_discovered":R["meta_learning"]["api_quirks"],
   "data_gaps":R["meta_learning"]["data_gaps"]},
 "analysis_insights":{
   "what_worked":[
     "PRE-COMMITTED TESTS CARRIED THE ENTIRE RUN. Run #19 registered four tests with explicit numeric thresholds and three fired in the pre-specified direction: the UPbit tranche cleared 200,000 (came in at 319,000), net one-way cleared 150,000 (came in at 188,658), and the identifiable bid reactivated through precisely the Coinbase Routing pipe that run #19 named as 'the earliest observable reversal'. This is the first run in four with ZERO corrections of a prior headline - not because the model got luckier, but because the questions were specified before the data arrived.",
     "RE-NETTING A HISTORICAL WINDOW WORKED AND WAS CHEAPER THAN FEARED. The run #17 peak window re-queried three weeks later returned identical gross figures with every router and feeder still resolvable. 1,284,688 gross was 68% circular, leaving 409,680 one-way. Retrospective re-netting is now a standing capability, not a one-off.",
     "THE SECOND-ORDER RESULT BEAT THE FIRST. Measuring circularity in a third window showed it is roughly CONSTANT (68% / 80% / 69%), which rescues the runs #13-#18 gross series as a valid SHAPE with wrong units rather than discarding it. Run #19 had assumed the worst case; measuring one more window produced a materially less destructive - and more useful - answer.",
     "SUPPRESSING A RULE RATHER THAN COMPUTING IT. The bilateral inverse rule requires |price change| >= 5% and price moved -0.37%, which would have produced a nonsense ratio of 3.50. The report states explicitly that the rule is not evaluable and does not advance the confirmation count. Prior runs computed the ratio whenever both legs existed.",
     "A BEHAVIOURAL PROFILE ANSWERED AN IDENTITY QUESTION WELL ENOUGH TO ACT ON. 'Unknown Whale I' could not be named, but nonce 10,169, 20,794 lifetime txs, 15-75 txs/day and ~80-110 counterparties on both sides of the hub is sufficient to classify it as operator inventory rather than an end buyer - and to state the exact test that would confirm it and the exact figure that would change (188,658 -> ~175,818)."],
   "what_needs_improvement":[
     "The whale_i 60-day trace terminated on the collector's 12-page cap at 600 txs, covering ~25 days of a requested 60, and the script did not flag that it had hit the page limit rather than the time boundary. That silent truncation is the same class of bug as the run #17 pagination miss, one layer down. The collector should log page-cap terminations.",
     "TWO FLOWS OF FIRST-ORDER SIZE ARE NARRATED AS 'UNEXPLAINED'. The direct-node unwind (~25.6K this week, ~215K over three weeks) is measured only as a residual between total staked and delegation TVL, and the XEGLD redemption (~5,250 tokens on a flat price week) has no destination trace. Both are cheap to resolve and neither was attempted this run because query budget went to the OTC re-netting.",
     "The net one-way series has three anchors but they are not contiguous - the run #17 peak sits three weeks before run #19 with nothing measured between. Storing it as a flat array would have created a false time axis, so it is stored as a keyed window map instead, but the series is still not chartable as a weekly line.",
     "MEX has outperformed EGLD for three consecutive weeks and the model has now given the same stale-pricing explanation twice without checking it. That is the shape of an assumption hardening into a fact."],
   "surprising_findings":[
     "A FLAT PRICE WEEK CONTAINED A TRIPLING OF NET DISTRIBUTION. EGLD moved -0.37% while the OTC hub pushed 188,658 EGLD of genuine one-way movement, up from 61,435. The market cleared a real supply wave without breaking, and paid for it in relative underperformance (~2pp behind BTC and ETH) rather than absolute decline.",
     "THE RUN #17 'RECORD 1.28M DISTRIBUTION WAVE' WAS A 410K WAVE. Real in direction, roughly a third the size in magnitude. This week's 188,658 is 46% of that corrected peak, not 15% of the headline one - which makes the current wave much more significant relative to history than the uncorrected figures implied.",
     "THE FIRST COMPETITIVE FEE CUT IN TWENTY RUNS - and it has not worked. egldstakingprovider cut 24% -> 15% on a 127,531 EGLD book, lifting APR to 7.82%, and still shed -8,168 EGLD and -7 delegators in the same week. The model predicted the cut would come; whether delegators respond to it is now the open question, and a null result would materially weaken the yield-arbitrage mechanism this model has leaned on for four runs.",
     "XOXNO'S LSD REDEEMED WITHOUT A PRICE DRIVER FOR THE FIRST TIME. Every prior XEGLD redemption in tracking coincided with a drawdown (-29.2% at -10.5% price, -2.70% at -12%). This week price was flat and ~5,250 XEGLD redeemed anyway, while Hatom's SEGLD was flat to three decimal places - so it is XOXNO-specific, not liquid-staking-wide.",
     "ZERO new tokens were issued for a fourth consecutive week - the raw ESDT system-SC scan came back empty, not merely below the quality bar. For a chain whose thesis rests on application-layer growth, this is a more durable problem than any of the flow dynamics the report spends its length on.",
     "Retail delegators remain the most steadfast cohort measured: of 72 claims traced, NONE went to a labelled exchange, for the tenth consecutive run. The only selling cohort was institutional, at 2 events and 162 EGLD."]},
 "methodology_changes":R["meta_learning"]["methodology_changes"],
 "new_addresses_discovered":[
   "The Coinbase Routing wallet's FUNDER is resolved: a Coinbase customer-facing hot wallet already labelled in known-addresses (60,702 lifetime txs, 17,097 EGLD balance). The full bid pipe is therefore Coinbase hot -> Coinbase Routing -> Mega Whale absorber, all three legs now named. This closes a chain that had been half-anonymous since run #15.",
   "'Unknown Whale I' PROFILED but not named: nonce 10,169, 20,794 lifetime transactions, 15-75 txs/day, 79 distinct outbound and 108 distinct inbound counterparties, 2 tokens and 8 NFTs, balance 166,603 (+11,217). Present on both sides of the OTC hub in all three measured windows. Classified provisionally as OTC operator inventory / market-making, NOT an end buyer. Explicit confirmation test recorded in watch_addresses.",
   "Additional OTC desk feeder and router wallets labelled from this week's hub trace, terminating at UPbit, Binance.com, Bybit and Gate.io. The venue shape is now identical across three measured windows: UPbit sole net source, Binance/Bybit the largest receivers.",
   "STILL FLAGGED, not fixed: two invalid-checksum entries in known-addresses.json (Hatom UTK Money Market, OneDex Launchpad). Neither is queried by the collector, so no figure is affected."],
 "action_items_completed":[
   "DONE (run #19 rec #1, the top item): RE-NET THE RUN #17 PEAK WINDOW. 1,284,688 gross was 68% circular, leaving 409,680 genuinely one-way, with the same venue shape as this week (UPbit sole net source -214,000; Bybit +219,602, Binance.com +128,283 receiving). Consequence is narrower than run #19 feared: restate the magnitude, keep the direction. And the second-order finding - circularity roughly constant across three windows - rescues the whole gross series as a shape.",
   "DONE (rec #2): PROMOTE THE TWO-HOP BOTH-LEGS NETTING INTO THE COLLECTOR. scripts/collect_run20.py now performs the hub trace inline and writes otc_hub_trace into the snapshot; gross and net one-way are produced together every week. net_one_way is stored as its OWN baseline array plus a keyed window map for the non-contiguous re-netted peak, never appended to the gross array.",
   "DONE (rec #3): DOES THE UPbit RELOAD ESCALATE? YES, decisively. 319,000 against the 200,000 pre-committed threshold and 4.8x last week's 67,000, with net one-way at 188,658 against the 150,000 threshold. Both branches of the pre-committed test pointed the same way: wave #2 is genuinely staging and run #18's exhaustion call is dead. UPbit's own balance stayed flat at 1,202,942 while feeding, so it is being replenished from an unobserved source - flagged for next run.",
   "DONE (rec #4): DOES THE IDENTIFIABLE BID COME BACK? YES, and through exactly the pre-registered pipe. A Coinbase hot wallet sent 5,764 EGLD to the Coinbase Routing wallet (dry at 77.13 for two weeks), which forwarded 5,748 to the Mega Whale absorber - its first movement in three weeks. The three-week structural promotion is CANCELLED, not triggered. Size caveat recorded: 3% of the week's net distribution, ~18% of the run #15 tranche.",
   "DONE (rec #5): TRACK THE DEX TURNOVER RATIO AS A FIRST-CLASS SERIES. Added to running_baselines as its own array (4.061 / 2.141 / 2.235). Neither run #19 branch fired - no recovery above ~4%, no third halving. Stabilisation at a low level: removes a tail risk, provides no demand evidence.",
   "PARTIAL (rec #6): IDENTIFY 'Unknown Whale I'. Profiled thoroughly but not named - the 60d trace hit the collector's page cap at 600 txs (~25 days). Behavioural evidence supports OTC operator inventory rather than end buyer, and the confirmation test plus the exact figure it would change (188,658 -> ~175,818) are recorded. Carried forward with a specific method fix (raise max_pages).",
   "DONE (rec #7): WATCH FOR A FEE RESPONSE IN THE DELEGATION MARKET. It happened - egldstakingprovider cut 24% -> 15%, the first competitive repricing in twenty runs, exactly the event run #19 predicted the fee-arbitrage mechanism would force. Recorded as a regime shift. It has not worked yet (-8,168 EGLD, -7 delegators the same week); the 2-3 week follow-through is now a pre-committed test.",
   "DONE (rec #8): DOES USH STABILISE OR TAKE A THIRD WEEK? Stabilised, at -0.32% after -2.93% and -2.60% - run #19's stabilisation branch, inside the noise band. Borrowers retired the run #16 leverage chase and stopped without touching base positions. No capitulation tell. Hatom Lending's EGLD TVL grew a third week alongside it, and notably without a dip to buy."],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":R["meta_learning"]["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":R["meta_learning"]["dashboard_suggestions_followup"],
 "self_assessment":{
   "most_valuable_insight":R["meta_learning"]["most_valuable_insight"],
   "actions_completed_count":7,"actions_attempted_count":8,
   "what_would_2x_next_week":"Close the two unexplained structural flows. The model is now well-instrumented on the OTC pipeline and adequately instrumented on demand, and both behaved predictably this week - which is why the weakest sentences in this report are the two that say 'the model cannot explain this'. The direct-node unwind is ~215K over three weeks and is measured only as a residual between total staked and delegation TVL; nobody has looked at which node operators are unstaking or where the EGLD lands. The XEGLD redemption is ~5,250 tokens on a FLAT price week, the first time XOXNO redemption has decoupled from a drawdown, and its destination is untraced - the difference between migration to native delegation (constructive, and delegation grew by the right order of magnitude in the same week) and exit to an exchange (bearish). Both are cheap. Second: raise the collector's page cap and log page-cap terminations, so a truncated trace announces itself rather than silently under-reporting - this is the same failure class as the run #17 pagination miss. Third: backfill net one-way for runs #16 and #18, the two windows whose interpretation has driven the most narrative, now that retrospective re-netting is proven to work three weeks out.",
   "pre_committed_test_for_next_run":"OTC: net one-way above ~300K with a UPbit tranche above ~350K = wave #2 matches or exceeds the re-netted run #17 peak of 409,680 and the supply overhang becomes the dominant fact on the chain; net back below ~100K = this was a two-week burst rather than a wave. BID: a tranche in the 30-50K range = the bid is genuinely back and the demand deficit is closing; another sub-10K week or a return to zero = this was a maintenance transfer and the dormancy finding should be revived. FEE CUT: stake returning to egldstakingprovider within 2-3 weeks = MultiversX delegators respond to price signals and other high-fee incumbents should follow; stake continuing to leave despite the better deal = delegator inertia dominates fee economics, which would materially weaken the yield-arbitrage mechanism. XEGLD: destinations in native delegation contracts = migration and constructive; destinations at exchanges = exit and bearish; a single large recipient = idiosyncratic and dismissable."},
 "recommendations_for_next_run":R["meta_learning"]["recommendations_for_next_run"]}
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #20; total runs",len(learn["runs"]))
for k in ["egld_price_usd","otc_pipeline_throughput_egld_7d","otc_net_one_way_egld_7d","dex_turnover_ratio_pct","reward_compound_pct"]:
    print("  baseline",k,new_baselines[k])
