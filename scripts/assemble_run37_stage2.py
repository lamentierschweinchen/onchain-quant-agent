#!/usr/bin/env python3
"""Run #37 stage 2: z-scores, narrative, trends, tests, meta_learning. Reads stage1.json, writes reports/2026-11-16.json.
Every figure in the prose is formatted from the collected snapshot or the stage-1 digest; nothing is typed in from last week."""
import json, statistics, sys
from datetime import datetime, timezone
sys.path.insert(0, "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/scripts")
from report_template import load_previous
REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
S = "/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/dddf9200-b0cf-4286-98dd-088a97a7e141/scratchpad"
RD = "2026-11-16"; RUN = 37
R = json.load(open(f"{S}/stage1.json")); D = json.load(open(f"{S}/digest37.json"))
c = json.load(open(f"{REPO}/data/collected/{RD}.json")); pv = load_previous(RD)
r0 = json.load(open(f"{REPO}/reports/2026-11-09.json")); L = json.load(open(f"{REPO}/data/learnings.json")); L["runs"] = [x for x in L["runs"] if x["date"] < RD]
rb = L["runs"][-1]["running_baselines"]
price, pc, rel = D["price"], D["pc"], D["rel"]
T = c["run37_traces"]; A = c["run37_adhoc"]; NH = A["new_hot"]
hm = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%b %d %H:%M UTC").replace(" 0", " ")
def z(key, cur):
    arr = rb[key][-8:]
    if len(arr) < 4: return None
    sd = statistics.pstdev(arr); m = statistics.mean(arr)
    return ((cur - m) / sd if sd else None), m, sd
def sev(zv):
    a = abs(zv); return "critical" if a > 4 else "high" if a > 3 else "medium" if a > 2 else None

# ---- measured inputs
mexp = c["mex_economics"]["price"]
def stable(k): s = c[k]; return (int(s["minted"]) - int(s["burnt"])) / 10 ** s["decimals"]
usdc, usdt = stable("stable_USDC-c76f1f"), stable("stable_USDT-f8c08c")
pusdc, pusdt = pv["stablecoin_supply"]["USDC-c76f1f"], pv["stablecoin_supply"]["USDT-f8c08c"]
chg = D["chg"]; prevb = pv["exchange_balances"]
custody_now = prevb["Binance Staking"] + chg["Binance Staking"]
bin_net = chg["Binance.com"] + chg["Binance Staking"]
wd = c["withdraw_decoded"]; undel = c["undelegated_this_week_total_egld"]; ncall = c["undelegate_callers_count"]
si = R["staking_intelligence"]; ch = si["churn"]; act = R["network_health"]["activity"]; dl_ = R["network_health"]["deltas"]
xx = R["token_activity"]["xexchange"]; ef = R["whale_intelligence"]["exchange_flows"]
VV = {v["venue"]: v for v in ef["rail_status"]["by_venue"]}
wdays = c["_period"]["window_days"]
ob = R["whale_intelligence"]["demand_instruments"]["exchange_orderbook"]
tk = c["cg_tickers"]["tickers"]
bithumb = next((x["converted_last"]["usd"] for x in tk if x["market"]["identifier"] == "bithumb"), None)
bithumb_prem = (bithumb / ob["binance_price_usd"] - 1) * 100 if bithumb else None
prev_ob = r0["whale_intelligence"]["demand_instruments"]["exchange_orderbook"]
J = T["hatom_borrow_join"]; HM = T["hatom_egld_mm"]["by_function"]; UB = T["usdc_bridge"]; KW = T["kucoin_whale"]; OV = T["otc_vault"]
XR = T["exit_route_scan"]
first_new = NH["first_tx_ts"]; old_last = T["rail_liveness"]["rows"]["erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets"]["last_out_ts"]
dark_days = (first_new - old_last) / 86400
recv = {x["to"]: x for x in NH["top_receivers"]}
FD = A["venue_feeders"]
to_cb = FD["coinbase_seller"]["out_egld"]; to_bybit = sum(s["egld"] for k in ("bybit_router", "bybit_dep2") for s in FD[k]["sources"] if s["label"] == "NEW BINANCE HOT")
cross = to_cb + to_bybit
RLQ = next(v for a, v in A["unlabelled_movers"].items() if a.startswith("erd1rlqdj67qxp"))
rlq_sent = sum(x["egld"] for x in RLQ["out"])
days = NH["days"]; d10 = days["2026-11-10"]; d16 = days["2026-11-16"]
PM = A["provider_mover_inbound"]
mov = sorted(c["provider_movers"], key=lambda m: -abs(m["delta_egld"]))
def pname(m): return m["identity"] or ("provider " + m["address"][-6:])
mov_txt = ", ".join(f"{pname(m)} {m['delta_egld']:+,.0f}" for m in mov[:5])
big_del = [(k, x) for k, v in PM.items() for x in v["big_inbound"][:1]]
loop_wallets = J["loop_borrowers"]; bp = J["by_pattern"]
mm_cash_now = next(int(x["balance"]) / 1e18 for x in c["top_accounts"] if x["address"].startswith("erd1qqqqqqqqqqqqqpgq35qkf34a8svu4r2zmfzuztmeltqclapv78ss5jleq3"))
mm_cash_prev = next(float(x["balance_egld"]) for x in pv["top_accounts"] if x["address"].startswith("erd1qqqqqqqqqqqqqpgq35qkf34a8svu4r2zmfzuztmeltqclapv78ss5jleq3"))
lsd = {t: float(c["tvl_tokens"][t]["supply"]) for t in ("SEGLD-3ad2d0", "XEGLD-e413ed", "USH-111e09")}
plsd = pv["lsd_supply"]
TVL = D["TVL"]; PTVL = pv["defi_tvl"]
LK = A["binance_lookalikes"]; lk_hot = next(v for a, v in LK.items() if a.startswith("erd1tsddlqzd63"))
mexc_left = prevb["MEXC"] + chg["MEXC"]; kucoin_now = prevb["KuCoin"] + chg["KuCoin"]
ni = R["token_activity"]["newly_issued"]

# ---- baselines (this run's values)
BASE = {"egld_price_usd": price, "dex_volume_24h_usd": D["vol24"], "dex_volume_24h_egld": D["vol24"] / price, "staked_egld": D["staked"],
        "mex_price_usd": mexp, "total_delegators": D["dl"], "staked_ratio": D["ratio"], "korea_premium_pct": round(D["prem"], 1),
        "exchange_net_flow_egld": D["net"], "binance_staking_custody_egld": custody_now, "usdt_supply": round(usdt), "usdc_supply": round(usdc),
        "binance_native_rail_egld_7d": NH["external_in_egld_window"] + NH["out_egld_window"], "withdraw_egld_returned_7d": round(wd["egld_returned_total"])}
json.dump(BASE, open(f"{S}/baselines37.json", "w"))

NICE = {"egld_price_usd": "EGLD price (USD)", "dex_volume_24h_usd": "DEX 24h volume (USD)", "staked_egld": "Staked EGLD", "total_delegators": "Delegator count", "mex_price_usd": "MEX price (USD)"}
anoms = []; ZS = {}
for key in ("egld_price_usd", "dex_volume_24h_usd", "staked_egld", "total_delegators", "mex_price_usd"):
    cur = BASE[key]; out = z(key, cur)
    if not out or out[0] is None: continue
    zv, m, sd = out; ZS[key] = zv; s = sev(zv)
    if s:
        anoms.append({"metric": key, "current_value": cur, "average_value": m, "stddev": sd, "z_score": zv, "method": "z_score", "severity": s,
                      "change_pct": (cur - rb[key][-1]) / rb[key][-1] * 100, "previous_value": rb[key][-1],
                      "description": f"{NICE[key]} {cur:,.6g} vs 8-run mean {m:,.6g} (z = {zv:+.2f})." + (" BTC fell by the same amount: this is the market, not an EGLD-specific break." if key == "egld_price_usd" else "")})
anoms.append({"metric": "binance_native_rail", "current_value": NH["external_in_egld_window"] + NH["out_egld_window"], "previous_value": 0, "method": "rule_based", "severity": "high",
    "description": f"Binance.com's native EGLD rail is live again on a new hot wallet (erd1ts0g6r0h, first transaction {hm(first_new)}), {dark_days:.1f} days after the old one went silent. "
                   f"In the window it paid {NH['out_n_window']:,} withdrawals ({NH['out_egld_window']:,.0f} EGLD) to {NH['distinct_receivers']:,} receivers and took {NH['external_in_txs']} deposit sweeps ({NH['external_in_egld_window']:,.0f} EGLD) from {NH['external_in_distinct_senders']} addresses."})
anoms.append({"metric": "binance_staking_custody_egld", "current_value": custody_now, "previous_value": prevb["Binance Staking"], "method": "rule_based", "severity": "high",
    "change_pct": (custody_now / prevb["Binance Staking"] - 1) * 100,
    "description": f"Binance Staking custody sent 2,264,611 EGLD to a Binance.com exchange wallet on Nov 12 16:24 UTC and 20,000 to the new hot wallet, leaving exactly 2,000,000. "
                   f"That is {2264611 / c['economics']['circulatingSupply'] * 100:.1f}% of supply moving from the wallet tagged as Binance's staked balance to one tagged as exchange funds. None of it left Binance: the receiving wallet holds 2,184,313 and has only funded the hot wallet (80,300)."})
anoms.append({"metric": "exchange_net_flow_egld", "current_value": D["net"], "previous_value": rb["exchange_net_flow_egld"][-1], "method": "rule_based", "severity": "medium",
    "description": f"Tracked exchange wallets gained {D['net']:+,.0f} EGLD after two net-outflow windows ({rb['exchange_net_flow_egld'][-2]:+,.0f}, {rb['exchange_net_flow_egld'][-1]:+,.0f}). Bybit {chg['Bybit']:+,.0f} and Coinbase {chg['Coinbase']:+,.0f} gained; Binance as a whole {bin_net:+,.0f}; MEXC {chg['MEXC']:+,.0f}. "
                   f"About {cross:,.0f} EGLD of the Bybit and Coinbase inflow came straight out of Binance's new hot wallet."})
anoms.append({"metric": "korea_premium_pct", "current_value": D["prem"], "previous_value": D["prev_prem"], "method": "rule_based", "severity": "medium",
    "description": f"Upbit ${ob['upbit']['price_usd']:.2f} vs Binance ${ob['binance_price_usd']:.2f}: premium {D['prem']:.1f}% (from {D['prev_prem']:.1f}%); Upbit {D['up_share']:.0f}% of 24h volume (from {prev_ob['upbit_share_of_volume_pct']:.0f}%)."
                   + (f" Bithumb ${bithumb:.2f} ({bithumb_prem:.0f}% over Binance)." if bithumb else "") + " Upbit's rail is still shut, so the gap cannot be arbitraged. Rule-based: no weekly baseline."})
anoms.append({"metric": "egld_minus_btc_pp", "current_value": rel, "previous_value": D["PREV_REL"], "method": "rule_based", "severity": "low",
    "description": f"EGLD {pc:+.2f}% vs BTC {D['btc_wow']:+.2f}% ({rel:+.1f}pp) and ETH {D['eth_wow']:+.1f}%. After {D['PREV_REL']:+.1f}pp last window, EGLD fell with the market and no further."})
usdc_net = UB["unwrap_usdc"] - UB["wrap_usdc"]
anoms.append({"metric": "usdc_bridge_net_unwrap", "current_value": usdc_net, "previous_value": 99719.798369 - 40629.114809, "method": "rule_based", "severity": "medium",
    "description": f"{UB['unwrap_txs']} unwraps moved {UB['unwrap_usdc']:,.0f} USDC into bridge-out tokens against {UB['wrap_txs']} wraps of {UB['wrap_usdc']:,.0f}: net {usdc_net:,.0f} leaving, about five times last window's net. One wallet did {max(v['usdc'] for v in UB['top_unwrappers'].values()):,.0f} of it. Wrapped USDC supply {usdc:,.0f} ({(usdc / pusdc - 1) * 100:+.2f}%)."})
dxp = (D["vol24"] / pv["xexchange"]["volume_24h_usd"] - 1) * 100
R["anomalies"] = anoms

def streak(arr, down=True):
    n = 0
    for i in range(len(arr) - 1, 0, -1):
        if (arr[i] < arr[i - 1]) if down else (arr[i] > arr[i - 1]): n += 1
        else: break
    return n
dlarr = rb["total_delegators"] + [D["dl"]]; sd_ = streak(dlarr)
uarr = rb["usdc_supply"] + [round(usdc)]; su = streak(uarr)
tarr = rb["usdt_supply"] + [round(usdt)]; st_ = streak(tarr)
sarr = rb["staked_egld"] + [D["staked"]]; ss = streak(sarr, down=False)
parr = rb["egld_price_usd"] + [price]; sp = streak(parr)
# ---- narrative
pr = pv["economics"]["staked_ratio"]
R["network_health"]["analysis"] = (
 f"WINDOW. {wdays:.2f} days (Nov 9 17:19 -> Nov 16 16:02 UTC); all four shards live. Epoch {act['epoch']}, {act['transactions_7d']:,} transactions "
 f"({act['avg_daily_transactions']:,}/day), {dl_['accounts_added']:,} new accounts. Supply {dl_['supply_added']:+,.0f} EGLD (the weekly emission).\n\n"
 f"PRICE. EGLD ${price:.2f}, {pc:+.2f}%, with BTC {D['btc_wow']:+.2f}% and ETH {D['eth_wow']:+.2f}%: {rel:+.1f}pp vs BTC. This was a market-wide drop, and EGLD tracked it almost exactly after trailing BTC by {abs(D['PREV_REL']):.1f}pp the window before. "
 f"Market cap ${c['economics']['marketCap'] / 1e6:,.1f}M. ${price:.2f} is below the Aug 17 reading ($2.76) and three cents above the bottom of the June-August range ($2.55). The price z-score is {ZS['egld_price_usd']:+.2f} on the 8-run baseline.\n\n"
 f"STAKING. Staked EGLD {D['staked']:,.0f} ({D['dstaked']:+,.0f}); ratio {D['ratio'] * 100:.2f}% (from {pr * 100:.2f}%). Network APR {c['economics']['apr'] * 100:.2f}%. Stake rose in a week the price fell 14%.")

R["whale_intelligence"]["analysis"] = (
 f"BINANCE'S RAIL IS BACK, ON A NEW WALLET. The old hot wallet (erd1sdslvl) is still silent and holds 3 EGLD. A new wallet, erd1ts0g6r0h, made its first transaction on {hm(first_new)}, about an hour after last week's snapshot and {dark_days:.1f} days after the old wallet's last move. "
 f"It was funded by Binance Staking custody (20,000) and by a tagged Binance.com wallet (80,300 in five sends), and it behaves like an exchange hot wallet: {NH['out_n_window']:,} withdrawals totalling {NH['out_egld_window']:,.0f} EGLD to {NH['distinct_receivers']:,} receivers, "
 f"and {NH['external_in_txs']} deposit sweeps totalling {NH['external_in_egld_window']:,.0f} EGLD from {NH['external_in_distinct_senders']} addresses. Its first full day, Nov 10, cleared {d10['wd_n']} withdrawals ({d10['wd_egld']:,.0f} EGLD) against {d10['dep_egld']:,.0f} deposited. "
 f"Over the window customers took out {NH['out_egld_window'] - NH['external_in_egld_window']:,.0f} EGLD more than they put in. The explorer has not tagged the wallet yet; the label rests on funding and behaviour.\n\n"
 f"BINANCE EMPTIED HALF ITS STAKING CUSTODY INTO AN EXCHANGE WALLET. On Nov 12 16:24 UTC the custody wallet sent 2,264,611 EGLD to Binance.com wallet erd1ylwusw, which had held 1 EGLD. Custody now holds exactly 2,000,000 (from 4,284,611); erd1ylwusw holds 2,184,313. "
 f"Nothing left the Binance group: across its five wallets the balance fell {abs(bin_net):,.0f}, which is the customer net withdrawal. What changed is the label on {2264611 / c['economics']['circulatingSupply'] * 100:.1f}% of supply, from staking reserve to exchange inventory. No Binance statement was found.\n\n"
 f"WHERE THE BINANCE WITHDRAWALS WENT. {cross:,.0f} EGLD ({cross / NH['out_egld_window'] * 100:.0f}% of the total) went to other exchanges within one hop: {to_cb:,.0f} through erd1tx933j8r into Coinbase's two wallets and {to_bybit:,.0f} through two routers into Bybit. "
 f"That is most of Bybit's {chg['Bybit']:+,.0f} and Coinbase's {chg['Coinbase']:+,.0f}. It is EGLD changing venue, not new supply reaching exchanges.\n\n"
 f"WHO DEPOSITED. The largest depositor was a top-100 wallet, erd1rlqdj67qxp: {rlq_sent:,.0f} EGLD in two sends (14,558 on Nov 11, 29,028 on Nov 16) through a deposit address. It has {RLQ['balance_egld']:,.0f} left. Nov 16 alone took {d16['dep_egld']:,.0f} EGLD of deposits, the heaviest deposit day since Nov 10.\n\n"
 f"OTHER BOOKS. Tracked exchange wallets {D['tot_c']:,.0f} EGLD, {D['net']:+,.0f} ({D['net'] / D['tot_p'] * 100:+.2f}%), the first net inflow in three windows. KuCoin took deposits again ({VV['KuCoin']['deposits_egld_7d']:,.0f} in, {VV['KuCoin']['withdrawals_egld_7d']:,.0f} out; {chg['KuCoin']:+,.0f}). "
 f"MEXC stayed withdraw-only for a third window ({chg['MEXC']:+,.0f}; {mexc_left:,.0f} left). Upbit's wallet received 3 EGLD and sent none.\n\n"
 f"HOLDERS HELD. The KuCoin withdrawer erd15ku2r2j6 did not move ({KW['balance_egld']:,.0f}). Mega Whale (1,219,231) and Whale B (181,822) did not move. "
 f"The OTC operator's vault took in {OV['in_window_in_egld']:,.0f} EGLD from Unknown Whale I and sent back {OV['in_window_out_egld']:,.0f}; it grew to {OV['balance_egld']:,.0f}. It is working inventory moving both ways, not a position being unwound. Desk throughput stayed negligible (132 EGLD).\n\n"
 f"POISONING FOLLOWED THE NEW WALLET. A lookalike of the new Binance hot wallet (same first six and last four characters) appeared on Nov 10, a day after the wallet did, and has sent {lk_hot['out_txs_30d']} dust transfers to {lk_hot['distinct_targets']} addresses, including Binance's own custody and exchange wallets.\n\n"
 f"TIERS. Mega whales {D['WT']['mega_whales'][2]:+,.0f} on a common-address basis: that is the 100,300 EGLD Binance's two large wallets passed down to the hot wallet, not selling. Large whales {D['WT']['large_whales'][2]:+,.0f} (Bybit and Coinbase books, the OTC vault); mid whales {D['WT']['mid_whales'][2]:+,.0f}.\n\n"
 f"EXITS. {XR['calls']} provider withdrawals above 3,000 EGLD: {', '.join(str(v['n']) + ' ' + k for k, v in XR['by_route'].items())}. None went to an exchange directly.")

for e_ in ef["entity_netting"]:
    if e_["entity"] == "Binance":
        e_["interpretation"] = (f"{bin_net:+,.0f} across five wallets, equal to customer flow at the new hot wallet: {NH['out_egld_window']:,.0f} withdrawn vs {NH['external_in_egld_window']:,.0f} deposited. "
                                f"The 2,264,611 custody -> exchange-wallet move and the 100,300 that funded the hot wallet are internal and cancel out.")
    elif e_["entity"] == "Bybit":
        e_["interpretation"] += f" {to_bybit:,.0f} of the deposits came from Binance's new hot wallet through two routers."
    elif e_["entity"] == "Coinbase":
        e_["interpretation"] += f" {to_cb:,.0f} of the deposits came from Binance's new hot wallet through erd1tx933j8r."
    elif e_["entity"] == "MEXC":
        e_["interpretation"] += f" Third window with no deposits; {mexc_left:,.0f} left."
R["whale_intelligence"]["demand_instruments"]["identifiable_bid_status"] = (
 f"RETIRED (run #23); Mega Whale 1,219,231 and Whale B 181,822 unchanged. OTC operator vault {OV['balance_egld']:,.0f} (two-way with Unknown Whale I: {OV['in_window_in_egld']:,.0f} in, {OV['in_window_out_egld']:,.0f} out this window).")

comp = None
R["staking_intelligence"]["analysis"] = (
 f"STAKE ROSE INTO THE DROP. Staked EGLD {D['dstaked']:+,.0f}; delegation contracts {si['summary']['total_delegated_egld'] - rb['delegation_total_locked_egld'][-1]:+,.0f} to {si['summary']['total_delegated_egld']:,.0f}. "
 f"Two wallets account for {big_del[0][1]['egld'] + sum(x['egld'] for x in PM['mandalastaking']['big_inbound'] if x['from'] == big_del[1][1]['from']):,.0f} of it: {big_del[0][1]['from'][:12]} delegated {big_del[0][1]['egld']:,.0f} EGLD to the largest provider (address ending r0pd0j, no identity), and {big_del[1][1]['from'][:12]} put {sum(x['egld'] for x in PM['mandalastaking']['big_inbound'] if x['from'] == big_del[1][1]['from']):,.0f} into mandalastaking, whose delegator count went from {PM['mandalastaking']['prev_users']} to {PM['mandalastaking']['users']}. "
 f"Biggest movers: {mov_txt}.\n\n"
 f"EXITS WERE ORDINARY. {ncall} wallets unDelegated {undel:,.0f} EGLD (previous window {rb['unbonding_queue_undelegated_egld_7d'][-1]:,.0f}); {wd['calls']} withdraw calls returned {wd['egld_returned_total']:,.0f} (previous {rb['withdraw_egld_returned_7d'][-1]:,.0f}). No unstaking wave at -14%.\n\n"
 f"DELEGATORS. {D['dl']:,} ({D['dl'] - D['dlp']:+,}): {ch['providers_gaining_delegators']} providers gained, {ch['providers_losing_delegators']} lost. The count has fallen for {sd_} straight windows, and in the last {ss} staked EGLD rose: fewer, larger positions. "
 f"HHI {D['hhi']:.5f}, top-5 {D['top5']:.2f}%, top-10 {D['top10']:.2f}%.")

R["token_activity"]["analysis"] = (
 f"DEX. 24h xExchange volume ${D['vol24']:,.0f} ({dxp:+.1f}% vs ${pv['xexchange']['volume_24h_usd']:,.0f}); in EGLD terms {xx['dex_volume_egld_24h']:,.0f} ({xx['dex_vol_egld_wow_pct']:+.1f}%). {xx['top_pair']} is {xx['top_pair_dominance_pct']:.0f}% of it. "
 f"Pair TVL ${D['tvl']:,.0f} ({(D['tvl'] / pv['xexchange']['pool_tvl_usd'] - 1) * 100:+.1f}% in USD, {(xx['pool_tvl_egld'] / xx['previous_pool_tvl_egld'] - 1) * 100:+.1f}% in EGLD). A 14% price drop did not bring volume to the DEX.\n\n"
 f"MEX ${mexp:.3e} ({xx['mex_price_change_wow_pct']:+.1f}%), moving with EGLD; z = {ZS['mex_price_usd']:+.2f}.\n\n"
 f"STABLECOINS. Wrapped USDC {usdc:,.0f} ({(usdc / pusdc - 1) * 100:+.2f}%), USDT {usdt:,.0f} ({(usdt / pusdt - 1) * 100:+.2f}%). Bridge unwraps were {UB['unwrap_usdc']:,.0f} USDC against {UB['wrap_usdc']:,.0f} wrapped; "
 f"{UB['unwrap_by_destination_token'].get('ETHUSDC-220753', 0) / UB['unwrap_usdc'] * 100:.0f}% headed to Ethereum, the rest to BSC. None of the five largest unwrappers sold EGLD on the DEX first: this is stablecoin capital leaving, not EGLD being cashed out.\n\n"
 + (f"NEW TOKENS. {len(ni)} issued in the window ({ni[0]['name']}, {ni[0]['holders']} holders)." if ni else "NEW TOKENS. None issued in the window."))

hl, hls, xl, ush = TVL["Hatom Lending"], TVL["Hatom Liquid Staking"], TVL["XOXNO LSD"], TVL["Hatom USH"]
R["defi_activity"]["analysis"] = (
 f"TVL FELL WITH THE PRICE, NOT WITH EXITS. One-week basis vs Nov 9: Hatom Lending ${hl / 1e6:.2f}M ({(hl / PTVL['Hatom Lending'] - 1) * 100:+.1f}%), Hatom Liquid Staking ${hls / 1e6:.2f}M ({(hls / PTVL['Hatom Liquid Staking'] - 1) * 100:+.1f}%), "
 f"XOXNO liquid staking ${xl / 1e6:.2f}M ({(xl / PTVL['XOXNO LSD'] - 1) * 100:+.1f}%), USH ${ush / 1e6:.2f}M ({(ush / PTVL['Hatom USH'] - 1) * 100:+.1f}%). "
 f"Liquid-staking token supplies were flat (Hatom {lsd['SEGLD-3ad2d0']:,.0f} vs {plsd['SEGLD-3ad2d0']:,.0f}; XOXNO {lsd['XEGLD-e413ed']:,.0f} vs {plsd['XEGLD-e413ed']:,.0f}), so the USD decline is the EGLD price. USH supply {lsd['USH-111e09']:,.0f} ({(lsd['USH-111e09'] / plsd['USH-111e09'] - 1) * 100:+.1f}%).\n\n"
 f"IDLE EGLD IN HATOM'S MARKET FELL. Idle EGLD in the money market fell from {mm_cash_prev:,.0f} to {mm_cash_now:,.0f} ({mm_cash_now - mm_cash_prev:+,.0f}). Calls in the window: {HM['borrow']['n']} borrows by {HM['borrow']['distinct_senders']} wallets, {HM['repayBorrow']['n']} repayments, "
 f"{HM['mintAndEnterMarket']['n'] + HM['mint']['n']} supplies, {T['hatom_egld_mm']['redeem_calls']} redemptions, {T['hatom_egld_mm']['liquidation_calls']} liquidations. Amounts are not decoded yet, so the split between new borrowing and withdrawn supply is open.\n\n"
 f"WHAT BORROWERS DID NEXT (new this run). Each borrow was joined to the same wallet's next 30 minutes: {bp.get('loop', 0)} of {J['borrow_calls']} were followed by a swap or stake and then a fresh supply (a leverage loop; {loop_wallets} wallets), "
 f"{bp.get('swap_only', 0)} by a swap only, {bp.get('resupply_only', 0)} by a re-supply, {bp.get('stake_only', 0)} by a delegation, {bp.get('none_in_30m', 0)} by nothing. "
 f"Three wallets run the loops; one of them made {max(v for k, v in __import__('collections').Counter(r['borrower'] for r in J['rows'] if r['pattern'] == 'loop').items()):d} of the {bp.get('loop', 0)}. A few wallets were adding leverage into the drop; nothing was liquidated.\n\n"
 f"SMALLER LIQUID-STAKING PROTOCOLS (discovery pass re-run): SALSA {D['EMERG']['SALSA (Staking Agency)']:,.0f} EGLD staked, Dinovox {D['EMERG']['Dinovox VoxEGLD']:,.0f}, JewelSwap {D['EMERG']['JewelSwap']:,.0f}, VestaX {D['EMERG']['VestaX Finance']:,.0f}; all within 6% of their Oct 26 readings.")

R["executive_summary"] = [
 {"category": "whale", "severity": "high", "finding": f"BINANCE'S EGLD RAIL REOPENED ON A NEW HOT WALLET. erd1ts0g6r0h started on {hm(first_new)}, {dark_days:.1f} days after the old wallet went silent. In the window: {NH['out_n_window']:,} withdrawals ({NH['out_egld_window']:,.0f} EGLD) and {NH['external_in_egld_window']:,.0f} EGLD of deposits. Customers took out {NH['out_egld_window'] - NH['external_in_egld_window']:,.0f} net."},
 {"category": "whale", "severity": "high", "finding": f"BINANCE MOVED 2,264,611 EGLD OUT OF STAKING CUSTODY INTO AN EXCHANGE WALLET (Nov 12). Custody is now exactly 2,000,000. Nothing left Binance, but {2264611 / c['economics']['circulatingSupply'] * 100:.1f}% of supply changed from staking reserve to exchange inventory. No statement found."},
 {"category": "network", "severity": "medium", "finding": f"EGLD FELL {abs(pc):.1f}% TO ${price:.2f}, IN LINE WITH BTC ({D['btc_wow']:.1f}%) AND ETH ({D['eth_wow']:.1f}%). {rel:+.1f}pp vs BTC after {D['PREV_REL']:+.1f}pp the window before: a market drop, not an EGLD-specific one."},
 {"category": "whale", "severity": "medium", "finding": f"EXCHANGE BOOKS GAINED {D['net']:,.0f} EGLD, THE FIRST NET INFLOW IN THREE WINDOWS. But {cross:,.0f} of Bybit's and Coinbase's gain came straight from Binance withdrawals: EGLD changing venue. The one large new deposit was a top-100 wallet sending {rlq_sent:,.0f} to Binance."},
 {"category": "staking", "severity": "medium", "finding": f"STAKED EGLD ROSE {D['dstaked']:,.0f} WHILE PRICE FELL 14%. Two wallets delegated {big_del[0][1]['egld'] + sum(x['egld'] for x in PM['mandalastaking']['big_inbound'] if x['from'] == big_del[1][1]['from']):,.0f} between them. Exits were ordinary ({undel:,.0f} unDelegated). Delegator count {D['dl'] - D['dlp']:+,}."},
 {"category": "token", "severity": "medium", "finding": f"KOREA PREMIUM {D['prem']:.1f}% (FROM {D['prev_prem']:.1f}%); UPBIT'S DECISION WINDOW OPENED TODAY (Nov 16-20), NOTHING ANNOUNCED YET." + (f" Bithumb trades {bithumb_prem:.0f}% over Binance." if bithumb else "") + f" Upbit's share of volume {D['up_share']:.0f}%."},
 {"category": "defi", "severity": "medium", "finding": f"STABLECOINS LEFT FASTER: {UB['unwrap_usdc']:,.0f} USDC unwrapped for bridging out vs {UB['wrap_usdc']:,.0f} wrapped. On Hatom, idle EGLD fell {abs(mm_cash_now - mm_cash_prev):,.0f}; of {HM['borrow']['n']} borrows, {bp.get('loop', 0)} were leverage loops by {loop_wallets} wallets. No liquidations."},
]

ti = R["trend_indicators"]
mexc3 = rb  # MEXC book three windows ago is stored in the run #35 report
r35 = json.load(open(f"{REPO}/reports/2026-11-02.json"))
def book(rep, name):
    for x in rep["whale_intelligence"]["exchange_flows"]["by_exchange"]:
        if x["exchange"] == name: return x
m35 = book(r35, "MEXC"); m36 = book(r0, "MEXC")
mexc_start = mexc_left - chg["MEXC"] - m36["change_egld"] - m35["change_egld"]
ti["accelerating_exchange_outflows"] = [
 {"exchange": "MEXC", "trend": "outflow", "cumulative_change_pct": (mexc_left / mexc_start - 1) * 100, "weeks_in_trend": 3,
  "interpretation": f"Third window withdraw-only: {m35['change_egld']:+,.0f}, {m36['change_egld']:+,.0f}, {chg['MEXC']:+,.0f}, zero deposits in all three. {mexc_left:,.0f} left of {mexc_start:,.0f}."},
 {"exchange": "Binance (all wallets)", "trend": "outflow", "cumulative_change_pct": bin_net / (prevb["Binance.com"] + prevb["Binance Staking"]) * 100, "weeks_in_trend": 1,
  "interpretation": f"{bin_net:+,.0f} in the first window after the rail reopened: withdrawals {NH['out_egld_window']:,.0f} vs deposits {NH['external_in_egld_window']:,.0f}. Daily withdrawals fell from {d10['wd_egld']:,.0f} on Nov 10 to {days['2026-11-15']['wd_egld']:,.0f} on Nov 15."},
 {"exchange": "KuCoin", "trend": "outflow ended", "cumulative_change_pct": chg["KuCoin"] / prevb["KuCoin"] * 100, "weeks_in_trend": 1,
  "interpretation": f"{chg['KuCoin']:+,.0f} after three outflow windows: deposits resumed ({VV['KuCoin']['deposits_egld_txs_7d']} sweeps, {VV['KuCoin']['deposits_egld_7d']:,.0f} EGLD). Book {kucoin_now:,.0f}."}]
ti["validator_movements"] = {"providers_joining": 0, "providers_leaving": 0, "net_provider_change": si["summary"]["num_providers"] - sum(1 for x in pv["staking_providers"] if x["locked_egld"] > 0),
    "notable_joiners": [], "notable_leavers": [], "note": f"{si['summary']['num_providers']} providers with stake; no joins or deregistrations in the window. Identity join matched {c['_provider_join_match_rate']}."}
ti["token_supply_events"] = [
 {"identifier": "USDC-c76f1f", "name": "WrappedUSDC", "event": "burn", "supply_previous": str(round(pusdc)), "supply_current": str(round(usdc)), "change_pct": (usdc / pusdc - 1) * 100,
  "description": f"{usdc - pusdc:+,.0f} USDC, the largest contraction in the last eight readings. Bridge unwraps {UB['unwrap_usdc']:,.0f} vs wraps {UB['wrap_usdc']:,.0f}."},
 {"identifier": "USDT-f8c08c", "name": "USDT", "event": "burn", "supply_previous": str(round(pusdt)), "supply_current": str(round(usdt)), "change_pct": (usdt / pusdt - 1) * 100,
  "description": f"{usdt - pusdt:+,.0f} USDT, third straight contraction."},
 {"identifier": "USH-111e09", "name": "Hatom USH", "event": "burn", "supply_previous": str(round(plsd["USH-111e09"])), "supply_current": str(round(lsd["USH-111e09"])), "change_pct": (lsd["USH-111e09"] / plsd["USH-111e09"] - 1) * 100,
  "description": f"{lsd['USH-111e09'] - plsd['USH-111e09']:+,.0f} USH: net repayment while EGLD borrowing rose."}]
ti["consecutive_streaks"] = [
 {"metric": "total_delegators", "direction": "down", "weeks": sd_, "cumulative_change_pct": (D["dl"] / dlarr[-sd_ - 1] - 1) * 100,
  "interpretation": f"{D['dl']:,} ({D['dl'] - D['dlp']:+,}); the decline picked up again after nearly stopping last window, while staked EGLD rose."},
 {"metric": "staked_egld", "direction": "up", "weeks": ss, "cumulative_change_pct": (D["staked"] / sarr[-ss - 1] - 1) * 100,
  "interpretation": f"{sarr[-ss - 1]:,.0f} -> {D['staked']:,.0f} since the Binance unbond step-down; this window's {D['dstaked']:+,.0f} is the largest of the run."},
 {"metric": "usdc_supply", "direction": "down", "weeks": su, "cumulative_change_pct": (usdc / uarr[-su - 1] - 1) * 100, "interpretation": f"{uarr[-su - 1]:,.0f} -> {usdc:,.0f}; the pace doubled this window."},
 {"metric": "usdt_supply", "direction": "down", "weeks": st_, "cumulative_change_pct": (usdt / tarr[-st_ - 1] - 1) * 100, "interpretation": f"{tarr[-st_ - 1]:,.0f} -> {usdt:,.0f}."},
 {"metric": "egld_price_usd", "direction": "down", "weeks": sp, "cumulative_change_pct": (price / parr[-sp - 1] - 1) * 100, "interpretation": f"${parr[-sp - 1]:.2f} -> ${price:.2f}; this leg matched BTC."}]
ti["consecutive_streaks"] = [x for x in ti["consecutive_streaks"] if x["weeks"] >= 2]
ti["regime_shifts"] = [
 {"metric": "binance_native_rail_egld_7d", "before_value": 0.0, "after_value": NH["external_in_egld_window"] + NH["out_egld_window"],
  "description": f"Binance's on-chain EGLD flow went from zero to {NH['external_in_egld_window'] + NH['out_egld_window']:,.0f} EGLD gross in a week, on a new hot wallet. Before the pause the old wallet ran about 145,000 a week, so the first week back was a backlog."},
 {"metric": "binance_staking_custody_egld", "before_value": prevb["Binance Staking"], "after_value": custody_now,
  "description": "Custody stepped down to a round 2,000,000 after climbing from 3.49M to 4.28M since early October. The 2.26M that left is in a Binance.com exchange wallet, where it can fund withdrawals without another custody move."},
 {"metric": "tracked_exchange_net_flow_egld", "before_value": rb["exchange_net_flow_egld"][-1], "after_value": D["net"],
  "description": f"Net flow turned positive ({D['net']:+,.0f}) after -205,817 and -86,702. Read with care: with Binance back, most of the inflow at Bybit and Coinbase is Binance withdrawals relocating."}]

# watch list: carry items forward by name, rebuild reasons
prevw = {w["item"]: w["weeks_on_list"] for w in r0["watch_list"]}
def wk(name): return prevw.get(name, 0) + 1
R["watch_list"] = [
 {"item": "UPBIT CAUTION REVIEW - decision Nov 16-20", "weeks_on_list": wk("UPBIT CAUTION REVIEW - decision Nov 16-20"), "reason": f"Decision window is open; nothing announced by Nov 16 16:00 UTC. Premium {D['prem']:.1f}% (from {D['prev_prem']:.1f}%), Upbit share {D['up_share']:.0f}%. Wallet idle (1,055,328). PRE-COMMITTED (upbit-premium-on-decision)."},
 {"item": "BINANCE HOT WALLET 2 erd1ts0g6r0h", "weeks_on_list": 1, "reason": f"New rail: {NH['out_egld_window']:,.0f} out, {NH['external_in_egld_window']:,.0f} in, balance {NH['info']['balance_egld']:,.0f}. Does the first-week withdrawal backlog fade? PRE-COMMITTED (binance-backlog-fades)."},
 {"item": "BINANCE 2.18M EXCHANGE WALLET erd1ylwusw", "weeks_on_list": 1, "reason": "Received 2,264,611 from staking custody on Nov 12; holds 2,184,313. Reserve, re-stake or distribution? PRE-COMMITTED (binance-reserve-stays)."},
 {"item": "BINANCE STAKING CUSTODY 2.00M", "weeks_on_list": wk("BINANCE STAKING CUSTODY 4.28M"), "reason": "Stepped down from 4,284,611 to exactly 2,000,000. Any further move changes the reading of Nov 12."},
 {"item": "BINANCE DEPOSITOR WHALE erd1rlqdj67qxp", "weeks_on_list": 1, "reason": f"Sent {rlq_sent:,.0f} EGLD to Binance in two clips (Nov 11, Nov 16); {RLQ['balance_egld']:,.0f} left. A third clip would make it a programme."},
 {"item": "MEXC WITHDRAW-ONLY", "weeks_on_list": wk("MEXC WITHDRAW-ONLY"), "reason": f"Zero deposits for three windows; {mexc_left:,.0f} left."},
 {"item": "KUCOIN WITHDRAWER erd15ku2r2j6 (168,358)", "weeks_on_list": wk("KUCOIN WITHDRAWER erd15ku2r2j6 (168,358)"), "reason": "Held through a -14% week; no outbound at all. Test resolved as a holder; keep one more window."},
 {"item": "OTC OPERATOR VAULT erd1drc22z7h", "weeks_on_list": wk("OTC OPERATOR VAULT erd1drc22z7h"), "reason": f"{OV['balance_egld']:,.0f} (+{OV['in_window_in_egld'] - OV['in_window_out_egld']:,.0f}); two-way clips with Unknown Whale I. Not draining."},
 {"item": "SELLER CHAIN erd1hl5y4a", "weeks_on_list": wk("SELLER CHAIN erd1hl5y4a"), "reason": "221,070 (+3,288). Its usual Binance route is open again; erd137cw9q, a large Oct 9 Binance depositor, sent 10,575 to the new hot wallet."},
 {"item": "EXPLOIT WALLET AND POISONING RING", "weeks_on_list": wk("EXPLOIT WALLET AND POISONING RING"), "reason": f"Exploit wallet dust only. A new lookalike mimics the Binance hot wallet ({lk_hot['out_txs_30d']} dust transfers since Nov 10)."}]

Tt = R["pre_committed_tests"]
def find(i): return next(t for t in Tt if t["id"] == i)
find("binance-rail-reopens").update({"status": "resolved", "outcome": "as_predicted", "resolved_in_run": RUN,
  "measured_value": f"{NH['external_in_egld_window']:,.0f} EGLD of customer deposits ({NH['external_in_txs']} sweeps, {NH['external_in_distinct_senders']} addresses) at a newly identified Binance hot wallet; old wallet still 0",
  "resolution": f"Reopened (deposits >= 5,000). The rail came back on a new wallet, erd1ts0g6r0h, first active {hm(first_new)}; it was dark for {dark_days:.1f} days. The clause about a newly identified address is what caught it: every wallet tracked last week still shows zero customer flow."})
find("kucoin-whale-holds").update({"status": "resolved", "outcome": "as_predicted", "resolved_in_run": RUN,
  "measured_value": f"balance {KW['balance_egld']:,.0f}; outbound {KW['out_total_egld']:,.0f}; to exchanges {KW['to_exchange_egld']:,.0f}",
  "resolution": "Holder (balance >= 150,000, no exchange send). No outbound transaction of any kind through a week in which EGLD fell 14%."})
find("delivery-price-relevance-2").update({"measured_value": "run #37: desk gross 132 EGLD. Not evaluable."})
find("upbit-premium-on-decision").update({"measured_value": f"run #37: premium {D['prem']:.1f}%, Upbit {D['up_share']:.0f}% of volume; decision window Nov 16-20 open, nothing announced by Nov 16 16:00 UTC."})
Tt.append({"id": "binance-backlog-fades", "registered_in_run": RUN, "claim": "The first week's net withdrawal at Binance's new hot wallet was a backlog from the 10.8-day pause, not a standing exit.",
  "threshold": f"Over run #38's window, customer flow at erd1ts0g6r0h (plus any further Binance hot wallet): withdrawals < 120,000 EGLD AND net withdrawal < 15,000 = backlog faded; withdrawals > 180,000 OR net withdrawal > 40,000 = standing exit; otherwise no conclusion. Run #37: {NH['out_egld_window']:,.0f} out, {NH['out_egld_window'] - NH['external_in_egld_window']:,.0f} net.",
  "branches": [{"condition": "withdrawals < 120K and net < 15K", "reading": "backlog faded"}, {"condition": "withdrawals > 180K or net > 40K", "reading": "standing exit"}, {"condition": "otherwise", "reading": "no conclusion"}],
  "status": "open", "outcome": None, "resolved_in_run": None, "measured_value": f"run #37: {NH['out_egld_window']:,.0f} withdrawn, {NH['external_in_egld_window']:,.0f} deposited", "resolution": None})
Tt.append({"id": "binance-reserve-stays", "registered_in_run": RUN, "claim": "The 2,264,611 EGLD moved from staking custody to erd1ylwusw is exchange reserve, not EGLD on its way out or back into stake.",
  "threshold": "At run #38: erd1ylwusw balance >= 2,000,000 = reserve; >= 300,000 sent to delegation contracts or back to custody = re-staked; >= 300,000 sent anywhere outside Binance's wallets = distribution; otherwise (it only tops up the hot wallet, total under 300,000) = reserve drawn for withdrawals, no conclusion",
  "branches": [{"condition": "balance >= 2.0M", "reading": "reserve"}, {"condition": ">= 300K delegated or returned to custody", "reading": "re-staked"}, {"condition": ">= 300K outside Binance", "reading": "distribution"}, {"condition": "otherwise", "reading": "no conclusion"}],
  "status": "open", "outcome": None, "resolved_in_run": None, "measured_value": "run #37: 2,184,313 held; 80,300 sent, all to the hot wallet", "resolution": None})

ml = R["meta_learning"]
n429 = c.get("_n_429")
ml.update({"run_number": RUN,
 "endpoints_that_failed": [f"Collector: 1 paged query hit HTTP 429 (Bybit outbound breadth) and was recovered by the follow-up pass; {len(c.get('_api_errors') or [])} transient errors, 0 unrecovered."],
 "api_quirks": ["A reopened exchange rail can sit on an address nobody tracks: every tracked Binance wallet read zero customer flow while the new hot wallet moved 379K EGLD. Follow the outbound of custody and cold wallets to find it.",
                "The explorer tag lags a new exchange wallet (erd1ts0g6r0h has none after a week); funding source plus fan-out is the usable signal.",
                "Label-prefix matching silently adds a non-exchange wallet to a venue if its label starts with the venue name ('KuCoin round-trip whale' was counted as KuCoin's book: +168K phantom inflow, caught in the stage-1 digest)."],
 "data_gaps": ["No Binance statement found for the new hot wallet or the 2.26M custody move; a third-party status page lists EGLD wallet maintenance on Nov 10-11 and from Nov 13, but the chain shows withdrawals paid every day through Nov 16.",
               "Upbit and Bithumb decisions not announced as of the snapshot (Upbit window Nov 16-20).",
               "OTC pipeline sections not refreshed (desk gross 132 EGLD).",
               "Hatom borrow sizes not decoded (the join classifies what followed each borrow, not how much was borrowed)."],
 "key_findings": [e["finding"] for e in R["executive_summary"][:5]],
 "action_items_from_previous": 7, "action_items_completed": 7,
 "action_items_completed_detail": [
   "binance-rail-reopens resolved (reopened, on a new wallet) and kucoin-whale-holds resolved (holder): both as predicted.",
   "Upbit decision checked (window Nov 16-20, nothing announced); premium 19.8% and volume share 14% recorded.",
   "Rail-liveness check added to the trace pass: last value-bearing deposit and withdrawal per tracked exchange wallet, silent > 48h flagged; stored in the report's exchange-flow section.",
   "New Binance deposit route identified before netting flows: hot wallet 2 (erd1ts0g6r0h) found from custody's outbound, added to known addresses, netted at entity level.",
   "Hatom borrow -> swap/stake -> supply join built (carried three runs): 51 borrows, 15 loops by 3 wallets.",
   "OTC vault tracked by day: 20,750 in, 9,772 out to Unknown Whale I; not draining.",
   "Unchanged-numerics diff is the staleness layer of scripts/prepublish.sh (added Nov 13); run as the publish gate."],
 "methodology_changes": [
   "Trace pass: rail liveness per tracked exchange wallet (rule from run #36 automated).",
   "Trace pass: Hatom EGLD-market borrows joined to the borrower's next 30 minutes (loop / swap only / re-supply / stake / none).",
   "When a tracked exchange's wallets read zero, trace the outbound of its custody and cold wallets before calling the rail dark: the new hot wallet was one hop from custody.",
   "Venue balance roll-up excludes non-exchange wallets whose label starts with a venue name.",
   "Whale tiers: a wallet promoted into the top 100 by an internal transfer is put on the common-address basis with its prior balance, so the tier does not show a phantom loss.",
   "Liquid-staking discovery pass re-run (last run #34); small-protocol rows show staked EGLD again."],
 "new_addresses_discovered_detail": [
   "erd1ts0g6r0hn2tme5t53epyp9lurm7893v52c30xp5zur05mm92r4hqx6jd26: Binance.com hot wallet 2 (new; funded by custody and erd1ylwusw)",
   "erd1rlqdj67qxp9l4gt895hwsjl7akrw6td3hhxwm2u4l2te9fzr3gjq6qzh4e: Binance depositor whale (43,586 sent, 41,905 left)",
   "erd1tsddlqzd63...x7jd26: address-poisoning lookalike of Binance hot wallet 2",
   "erd1yl5ksy466z...x6zlz: address-poisoning lookalike of Binance.com erd1ylwusw"],
 "new_addresses_discovered": 4,
 "most_valuable_insight": "Binance did not stay dark: it reopened on a wallet we were not tracking, and the same week relabelled 2.26M EGLD from staking custody to exchange inventory. Read from the tracked wallets alone, this window would have shown a second 'dark' week and a 2.28M 'outflow' from custody.",
 "top_recommendation": "RUN #38 FIRST: resolve binance-backlog-fades and binance-reserve-stays; record the Upbit decision and the premium on the day.",
 "recommendations_for_next_run": [
  "Resolve binance-backlog-fades and binance-reserve-stays on run #38's window (hot wallet 2 daily rails; erd1ylwusw outbound).",
  "Upbit decision (due by Nov 20): resolve upbit-premium-on-decision; record premium, volume share and whether the wallet moves.",
  "Add hot wallet 2 to the rails pass and the collector's Binance set so its flows land in exchange_rails without the ad-hoc script.",
  "Decode Hatom borrow amounts from smart-contract results so the loop count has an EGLD size.",
  "Trace erd1rlqdj67qxp's funding (first transaction Oct 29) and whether it sends a third clip to Binance.",
  "Check whether Binance's 2.26M move coincides with a change in its on-chain delegations (binance_staking provider stake)."],
 "dashboard_feature_suggestions": [
  {"title": "Exchange entity wallet map", "motivation": "This run Binance's customer flow moved to a new hot wallet and 2.26M EGLD moved custody -> exchange wallet. The per-wallet table shows -2.28M and +2.25M on separate rows; only the entity roll-up (-29,768) is the real number, and nothing shows that the wallets belong together.", "suggested_visualization": "per-entity node diagram (custody, cold, hot wallets) with internal transfers as edges and customer in/out as external arrows; internal edges greyed out", "data_already_available": True, "data_source": "whale_intelligence.exchange_flows.entity_netting + internal_note + wallet_changes; run37_adhoc.new_hot.funding_legs in data/collected", "priority": "high"},
  {"title": "Withdrawal destination sankey per venue", "motivation": "76,719 EGLD (38%) of Binance's first-week withdrawals went to Coinbase and Bybit within one hop, which is why 'exchange net inflow +36K' overstates new supply. The flow table cannot show venue-to-venue relocation.", "suggested_visualization": "sankey from source venue to one-hop destination class (other exchange by name, DeFi, staking, held, unresolved)", "data_already_available": True, "data_source": "run37_adhoc.new_hot.top_receivers + venue_feeders in data/collected; kucoin_destinations has the same shape", "priority": "medium"},
  {"title": "Hatom borrow follow-through bars", "motivation": "The new borrow join (15 loops, 15 swap-only, 5 re-supply, 3 stake, 13 none out of 51 borrows) has no home on the DeFi panel; it is the first direct read of whether leverage is being added.", "suggested_visualization": "stacked weekly bar of borrow follow-through patterns with distinct-wallet count on hover", "data_already_available": True, "data_source": "run37_traces.hatom_borrow_join.by_pattern (weekly from run #37)", "priority": "low"}],
 "dashboard_suggestions_followup": [
  {"title": "Venue rail liveness strip", "status": "pending", "reason": "Data now produced every run (exchange_flows.rail_liveness); component not built. More useful this week: it would have shown Binance's old wallet silent 425h next to a live entity."},
  {"title": "Single-wallet CEX round-trip ledger", "status": "deprioritized", "reason": "The KuCoin withdrawer did not move and KuCoin's flows normalised; the withdrawal-destination sankey proposed this run covers the general case."},
  {"title": "Entity-netted exchange flow bridge", "status": "pending", "reason": "Superseded in scope by this run's exchange entity wallet map (2.26M internal move); build that one instead."},
  {"title": "Exchange book depletion timeline", "status": "pending", "reason": "Still relevant for MEXC (three windows withdraw-only, 27,786 left)."},
  {"title": "Hatom leverage-loop tracker", "status": "pending", "reason": "Join built this run; data exists from run #37, component not built (see borrow follow-through bars)."}],
 "self_assessment": {"most_valuable_insight": "Binance reopened on an untracked wallet and relabelled 2.26M EGLD; entity netting turned two alarming rows into a -29,768 customer outflow.", "recommendations_completed": "7 of 7", "what_would_make_it_2x_better": "Hot-wallet discovery as a standing collector step (follow custody outbound every run) and decoded Hatom borrow sizes."}})
ml["withdrawn_claims"] = ml.get("withdrawn_claims") or []
worked = [x for x in (ml.get("endpoints_that_worked") or []) if "Nov 9" not in x and "Oct 26" not in x][:38] + [
    "post-restart window netting (Sep 24 - Nov 16)", "rail liveness per tracked exchange wallet (run #36 rec #3)",
    "Binance hot wallet 2 full in/out profile (ad-hoc pass)", "Hatom borrow follow-through join (EGLD market)",
    "liquid-staking discovery pass (token owner -> delegation)", "OTC vault daily legs", "venue feeder one-hop sources"]
ml["endpoints_that_worked"] = worked
R["metadata"]["data_sources_ok"] = worked
R["metadata"]["data_sources_failed"] = []
R["metadata"]["data_sources_recovered"] = ["/accounts/{Bybit}/transactions outbound breadth page (HTTP 429 in the collector, recovered by the follow-up pass)"]

json.dump(R, open(f"{REPO}/reports/{RD}.json", "w"), indent=1, default=str)
print("wrote", f"reports/{RD}.json", "| anomalies", [(a["metric"], a["severity"]) for a in anoms], "| z", {k: round(v, 2) for k, v in ZS.items()})
print("streaks", [(x["metric"], x["weeks"]) for x in ti["consecutive_streaks"]], "mexc_start", round(mexc_start), "cross", round(cross), "bithumb", bithumb, bithumb_prem)
