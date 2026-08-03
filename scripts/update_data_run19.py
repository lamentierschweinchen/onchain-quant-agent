#!/usr/bin/env python3
"""Run #19: refresh previous.json, known-addresses.json and append the learnings entry."""
import json
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D=json.load(open(f"{REPO}/data/collected/2026-08-03.json"))
R=json.load(open(f"{REPO}/reports/2026-08-03.json"))
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
 "snapshot_date":"2026-08-03",
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
 "otc_throughput_series":{"run12":round(otc["gross_series_egld_7d"]["run12"]),"run13":66128,"run14":186124,
                          "run15":506053,"run16":1100791,"run17":1284688,"run18":313173,
                          "run19":round(otc["gross_outbound_egld_7d"])},
 # NEW in run #19: only this run has been netted for round-trips. Do not backfill by assumption.
 "otc_net_one_way_series":{"run19":round(otc["net_one_way_egld_7d"])},
 "demand_instruments":{"dex_turnover_ratio_pct":R["token_activity"]["xexchange"]["turnover_ratio_pct"],
   "identifiable_bid_absorbed_egld_7d":0.0,"weeks_bid_at_zero":2,
   "withdrawal_breadth_ex_pipeline":R["whale_intelligence"]["demand_instruments"]["withdrawal_breadth"]},
 "watch_addresses":[
   {"address":UPBIT_DESK,"label":f"UPbit OTC Desk (RE-FED: UPbit sent a fresh 67,000 tranche after zero last week; desk at {b(UPBIT_DESK):,.0f})","balance_egld":b(UPBIT_DESK),"weeks_tracked":19,"first_seen":"2026-04-02"},
   {"address":DIST_DESK,"label":f"OTC Distribution Wallet (combined desk balance 65,053, +3,558; gross throughput 301,498 but only 61,435 NET one-way - 80% is round-trip churn with Bybit/Gate.io)","balance_egld":b(DIST_DESK),"weeks_tracked":17,"first_seen":"2026-04-13"},
   {"address":CUSTODY,"label":"Binance Staking custody (FLAT, zero txs. Last week's +150,000 is now traced to an unDelegate/withdraw on the binance_staking DELEGATION contract - the de-staking programme CONTINUED, it did not reverse. Watch what custody does with the re-parked 150K: drawdown to hot = distribution, re-delegation = first constructive Binance signal in 5 runs)","balance_egld":b(CUSTODY),"weeks_tracked":13,"first_seen":"2026-05-11"},
   {"address":MEGA,"label":"Mega Whale erd18mv2z6r2 (IDLE 2nd week: zero value txs, unchanged to the decimal. A 3rd zero week promotes 'large-bid infrastructure dormant' to a structural finding)","balance_egld":b(MEGA),"weeks_tracked":16,"first_seen":"2026-04-20"},
   {"address":CB_ROUTING,"label":"Coinbase Routing Wallet (still dry at 77 EGLD, zero txs 2nd week - the pipe that filled the absorber in runs #15 and #17. A refill is the earliest signal the bid is back)","balance_egld":b(CB_ROUTING),"weeks_tracked":2,"first_seen":"2026-07-27"},
   {"address":WHALE_I,"label":"Unknown Whale I (active) - UNIDENTIFIED, both FEEDS and RECEIVES from the OTC desks (net receiver this week); largest non-exchange participant in the hub. Trace its 30-60d inbound - may be the desk operator's own inventory wallet","balance_egld":b(WHALE_I),"weeks_tracked":1,"first_seen":"2026-08-03"},
   {"address":CUST_FUNDER,"label":"Binance custody reload funder erd1r3w62vq (RESOLVED: its 30d history is unDelegate + withdraw on the binance_staking delegation contract, then 150,000 to custody. A Binance de-staking withdrawal wallet, not an external funder)","balance_egld":b(CUST_FUNDER),"weeks_tracked":2,"first_seen":"2026-07-27"},
   {"address":KUCOIN,"label":"KuCoin canonical (GRADUATED: the run #17 whale deposit is stationary two weeks on, +2,549. No further tracking value unless it moves materially)","balance_egld":b(KUCOIN),"weeks_tracked":3,"first_seen":"2026-07-20"},
   {"address":SRC17,"label":"OTC source erd17l22 (still loaded at 324,758, +2,077 - inventory parked, not pushing)","balance_egld":b(SRC17),"weeks_tracked":13,"first_seen":"2026-05-11"},
   {"address":FUNDER,"label":"OTC source funder (Binance.com -> erd17l22 pass-through)","balance_egld":b(FUNDER) or 0,"weeks_tracked":11,"first_seen":"2026-05-25"},
   {"address":XOXNO_LSD,"label":"XOXNO LSD contract (XEGLD supply FLAT -0.15% - held through a drawdown for the first time in four; the redeem-on-weakness pattern broke)","balance_egld":b(XOXNO_LSD) or 0,"weeks_tracked":6,"first_seen":"2026-06-29"}]}
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
                       "notes":notes,"first_seen":"2026-08-03","discovered_run":19}
    return True
added=0
# inbound feeders (venue -> desk), labelled by their dominant source venue
for addr,rec in hub["inbound"].items():
    if rec.get("kind")!="router" or rec["amount"]<20000: continue
    terms={k:v for k,v in rec["terminals"].items() if not k.startswith("UNRESOLVED")}
    src=max(terms,key=terms.get) if terms else "unknown"
    if label_map.get(addr): continue
    if add_addr("exchange_routers",addr,f"{src}->OTC Desk Feeder (run #19)","router","otc_feeder",
                f"Zero-balance pass-through that carried {rec['amount']:,.0f} EGLD from {src} into the UPbit OTC desk complex in the 2026-07-27..2026-08-03 window. Inbound leg of the circular desk hub."):
        added+=1
# outbound routers terminating at a venue
for addr,rec in hub["outbound"].items():
    if rec.get("kind")!="router" or rec["amount"]<20000: continue
    terms={k:v for k,v in rec["terminals"].items() if not k.startswith("UNRESOLVED")}
    dst=max(terms,key=terms.get) if terms else "unknown"
    if label_map.get(addr): continue
    if add_addr("exchange_routers",addr,f"OTC Desk->{dst} Router (run #19)","router","otc_router",
                f"Zero-balance pass-through that forwarded {rec['amount']:,.0f} EGLD from the OTC desks to {dst} in the 2026-07-27..2026-08-03 window."):
        added+=1
# the custody funder is now identified
if CUST_FUNDER not in label_map:
    if add_addr("exchange_routers",CUST_FUNDER,"Binance: de-staking withdrawal wallet","exchange","binance_destaking",
                "Calls unDelegate/withdraw on the binance_staking delegation contract and forwards the proceeds to the Binance Staking custody wallet. Sent the +150,000 custody 'reload' on 2026-07-22, which run #18 had read as external accumulation."):
        added+=1
kn.setdefault("_metadata",{})["last_updated"]="2026-08-03"
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
 "otc_pipeline_throughput_egld_7d":[round(otc["gross_series_egld_7d"]["run12"]),66128,186124,506053,1100791,1284688,313173,round(otc["gross_outbound_egld_7d"])],
 # NEW ARRAY, different quantity - per run #18's units rule this must NOT be appended to the gross one
 "otc_net_one_way_egld_7d":[round(otc["net_one_way_egld_7d"])],
 "dex_turnover_ratio_pct":[round(R["token_activity"]["xexchange"]["previous_turnover_ratio_pct"],3),
                           round(R["token_activity"]["xexchange"]["turnover_ratio_pct"],3)],
 "identifiable_bid_absorbed_egld_7d":[0,0],
 "binance_staking_custody_egld":roll(rbprev.get("binance_staking_custody_egld") or [],exchange_balances["Binance Staking"]),
 "reward_compound_pct":roll(rbprev.get("reward_compound_pct",[]),round(R["staking_intelligence"].get("reward_behavior",{}).get("compound_pct_at_function_level",0),2))}

entry={
 "date":"2026-08-03","run_number":19,
 "data_quality":{
   "endpoints_that_worked":R["meta_learning"]["endpoints_that_worked"],
   "endpoints_that_failed":R["meta_learning"]["endpoints_that_failed"],
   "api_quirks_discovered":R["meta_learning"]["api_quirks"],
   "data_gaps":R["meta_learning"]["data_gaps"]},
 "analysis_insights":{
   "what_worked":[
     "Applying the run #17 two-hop destination rule to the INBOUND leg as well was the highest-yield change of the run. It cost about 25 extra queries and revealed that 80% of gross desk throughput round-trips to the venue that fed it - which redefines the pipeline's headline metric and retroactively qualifies the runs #13-#18 series.",
     "Reading the function/action field on ZERO-VALUE transactions resolved a question run #18 had recorded as unresolvable. The Binance custody funder appeared to have no funding history because its EGLD arrived as a smart-contract result; its zero-value outbound txs carried function=unDelegate and function=withdraw, which identified the source exactly and falsified last week's bullish conclusion.",
     "The three demand instruments requested by run #18 were all built and all paid off immediately: the DEX turnover ratio turned 'depth held, trading left' into a measurement (4.06% -> 2.14%), the identifiable-bid composite recorded a clean second week of zero, and withdrawal breadth exposed that 84% of >1,000 EGLD exchange withdrawals go straight into the OTC pipeline rather than to self-custody.",
     "The pre-commitment discipline again did its job. Four registered tests resolved (UPbit reload, custody origin, USH acceleration, depositor capacity), and two of them resolved AGAINST the prior run's conclusion - which is only visible because the branches were written down in advance.",
     "Answering an open 'why' question with provider parameters rather than a narrative: pi-staking's seven-week growth streak is fully explained by 9.10% APR at a 0% fee on a small base, and the cohort check (APR>=8.8% +37,090 vs 20%-fee procryptostaking -5,998) generalises it to fee arbitrage rather than adoption."],
   "what_needs_improvement":[
     "Three consecutive runs have had a headline conclusion overturned by measuring one level deeper (run #17 pagination, run #18 baseline units, run #19 circularity and the custody origin). The pattern is that a flow AGGREGATE gets reported as a fact before its constituent legs are resolved. Single-week structural conclusions drawn from aggregates should be marked provisional in the report itself.",
     "The corrected net-one-way figure exists for exactly one week, so there is no series. Until the run #17 peak window is re-netted, the model cannot say whether the five-week escalation was distribution or churn - which is a live gap in the most-cited chart the pipeline produces.",
     "The withdrawal-breadth instrument has no prior-week comparison and will not become useful for two more runs. Instruments should be backfilled at introduction where the raw snapshots allow it (data/collected has every week since run #10).",
     "'Unknown Whale I (active)' is the largest non-exchange participant in the OTC hub, both feeding and receiving, and remains unidentified after appearing in multiple runs. It should have been traced this run rather than deferred."],
   "surprising_findings":[
     "The OTC pipeline is a CIRCULAR cross-exchange settlement hub, not a one-way distribution channel. Bybit fed 132,074 EGLD into the desks through three feeders and took 160,410 back out through five routers in the same week; Gate.io did the same at smaller scale. Netting round-trips reduces a 301,498 headline to 61,435 of genuine one-way movement.",
     "Run #18's single most bullish finding was wrong. The +150,000 Binance custody 'reload' was the delegation unwind completing - an unDelegate on July 9 and a withdraw on July 22, with the transfer to custody minutes later. Binance never stopped de-staking.",
     "Every traced desk destination above 2,000 EGLD terminated at an exchange or at one recurring whale intermediary. There was ZERO retail dispersion in a week with 301,498 EGLD of gross pipeline activity.",
     "The reward compound rate jumped to 62.25%, the highest in tracking, reversing two weeks of slippage during a down week - and of 73 retail claims traced, NONE went to a labelled exchange. The smallest delegators are the most steadfast cohort on the chain.",
     "XOXNO's LSD held flat through a -5% price week. XEGLD has redeemed on every prior drawdown in tracking (-29.2% in run #14, -2.70% last week); the redeem-on-weakness pattern broke.",
     "84% of the EGLD leaving exchanges in >1,000 EGLD transfers went into the OTC pipeline rather than to self-custody addresses. The naive withdrawal-breadth metric would have read as retail accumulation."]},
 "methodology_changes":R["meta_learning"]["methodology_changes"],
 "new_addresses_discovered":[
   "erd1r3w62vq... IDENTIFIED (was unknown in run #18): a Binance DE-STAKING WITHDRAWAL wallet. Its 30-day history is unDelegate + withdraw on the binance_staking delegation contract followed by a 150,000 transfer to the Binance Staking custody wallet. Added to known-addresses as exchange/binance_destaking.",
   "Three OTC desk FEEDER wallets (inbound leg, new pattern): zero-balance pass-throughs carrying Bybit and Gate.io funds INTO the desks. Previously the desks were only ever fed by UPbit directly, so the inbound routing layer had never been observed.",
   "Multiple OTC desk->venue routers re-confirmed and newly labelled where unnamed, terminating at Bybit, Binance.com and Gate.io.",
   "'Unknown Whale I (active)' is now confirmed as a two-way participant in the OTC hub (both feeds and receives) and is the largest non-exchange counterparty in it. Still unidentified; added to watch_addresses for a 30-60d inbound trace.",
   "STILL FLAGGED, not fixed: two invalid-checksum entries in known-addresses.json (Hatom UTK Money Market, OneDex Launchpad). Neither is queried by the collector."],
 "action_items_completed":[
   "DONE: TRACE THE BINANCE CUSTODY RELOAD ORIGIN. Resolved, and it falsifies run #18's reading. The funder's complete 30-day history is unDelegate (Jul 9) + withdraw (Jul 22) on the binance_staking DELEGATION contract, then the 150,000 to custody. The reload was the run #16 provider unwind (-148,941) completing after unbonding, not external accumulation. The de-staking programme is intact; custody was flat all week.",
   "DONE: DID THE DEMAND SIDE COME BACK? No. Price fell a further 5.28%, the identifiable bid recorded a second consecutive zero week (Mega Whale unchanged to the decimal, Coinbase Routing still at 77 EGLD), and the DEX turnover ratio halved again. The pre-committed test resolves toward the bid-problem branch, with one correction: its premise that there was 'no traceable distribution' was wrong - netting the pipeline shows ~61K of genuine one-way distribution with UPbit as the source.",
   "DONE: DO THE OTC DESKS STAY DEAD? No - UPbit resumed with a fresh 67,000 tranche after one week of nothing, and the desk balance rose to 65,053. Gross throughput was flat at 301,498. The exhaustion call from run #18 lasted exactly one week, though at ~1/20th of the run #17 peak in net terms.",
   "DONE: INSTRUMENT DEMAND PROPERLY - all three sub-items built. (a) identifiable-bid composite (Coinbase Routing balance + Mega Whale delta) now a standing metric, reading zero for a second week; (b) per-pair TVL/volume depth ratio from mex/pairs added to token_activity.xexchange, showing turnover 4.06% -> 2.14% on flat depth; (c) withdrawal breadth measured, and immediately showed that 84% of >1,000 EGLD exchange outflows go into the OTC pipeline, so only the ex-pipeline figure (20 addresses, 56,896 EGLD) is a retail proxy.",
   "DONE: DOES THE USH DE-LEVERAGING ACCELERATE? Neither branch - it continued at almost exactly the prior pace (-2.93% after -2.60%, cumulative -5.45%). An orderly unwind that retires the run #16 leverage chase without a forced-closure signature, so no capitulation tell.",
   "DONE: CONFIRM OR FALSIFY THE DEPOSITOR-CAPACITY RECOVERY. The bilateral inverse ratio came in at 0.58 on a -5.28% price week - neither the >0.8 'structurally restored' branch nor the 0.2-0.4 'reverted' branch. Read: capacity is healthy and mid-range, run #11's decay hypothesis stays falsified, and run #18's 0.98 was a spike rather than a new level.",
   "DONE: BACKFILL THE OTC SERIES ONE WINDOW FURTHER. The run #12 window (Jun 8-15) is still queryable and returns 44,335 EGLD net of desk-to-desk, extending the gross series one window left and confirming the escalation began at run #13 rather than earlier.",
   "DONE: WATCH pi-staking. Explained: 9.10% APR at 0% service fee on a 63,922 EGLD base - second-highest APR, joint-lowest fee, small enough to absorb inflows without diluting. Not an integration or adoption story. The cohort check generalises it: APR>=8.8% providers took +37,090 while 20%-fee procryptostaking and 12%-fee syndicatex shed."],
 "running_baselines":new_baselines,
 "dashboard_feature_suggestions":R["meta_learning"]["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup":R["meta_learning"]["dashboard_suggestions_followup"],
 "self_assessment":{
   "most_valuable_insight":R["meta_learning"]["most_valuable_insight"],
   "actions_completed_count":8,"actions_attempted_count":8,
   "what_would_2x_next_week":"Rebuild the OTC throughput history in NET one-way terms. The single most-cited artefact this pipeline produces is the throughput series, and this run proved that its unit measures pipeline activity rather than distribution - 80% of this week's gross was round-trip churn between Bybit, Gate.io and the desks. Re-netting the run #17 peak window (about 60 queries) would answer whether the 1.28M record was real distribution or the same churn at scale, and that single answer changes the interpretation of the last six weeks. Second: fold the two-hop both-legs resolution into the collector so gross and net are produced together every week rather than by a side script. Third: backfill the three new demand instruments from the stored snapshots (data/collected has every week since run #10) so they have history instead of a single point.",
   "pre_committed_test_for_next_run":"OTC: net one-way distribution rising back above ~150K with a further UPbit tranche above ~200K = wave #2 genuinely staging and run #18's exhaustion call is dead; net staying near 60K on high gross = the desks are cross-exchange settlement infrastructure and gross throughput should be dropped from the supply indicators entirely. BID: a third consecutive week of zero absorption by the Mega Whale absorber with the Coinbase Routing wallet still dry promotes 'the chain's large-bid infrastructure is dormant' from observation to structural finding; a Coinbase Routing refill is the earliest observable reversal."},
 "recommendations_for_next_run":R["meta_learning"]["recommendations_for_next_run"]}
learn["runs"].append(entry)
json.dump(learn,open(f"{REPO}/data/learnings.json","w"),indent=2)
print("APPENDED learnings.json run #19; total runs",len(learn["runs"]))
for k in ["egld_price_usd","otc_pipeline_throughput_egld_7d","otc_net_one_way_egld_7d","dex_turnover_ratio_pct","reward_compound_pct"]:
    print("  baseline",k,new_baselines[k])
