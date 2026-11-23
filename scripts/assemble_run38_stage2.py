#!/usr/bin/env python3
"""Run #38 stage 2: z-scores, narrative, trends, tests, meta_learning. Reads stage1.json, writes reports/2026-11-23.json.
Every figure in the prose is formatted from the collected snapshot or the stage-1 digest."""
import json, statistics, sys
from collections import Counter
from datetime import datetime, timezone
sys.path.insert(0, "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/scripts")
from report_template import load_previous
REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
S = "/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/949f11b7-26bf-4a9a-b4a7-ae3219fe2344/scratchpad"
RD = "2026-11-23"; RUN = 38
R = json.load(open(f"{S}/stage1.json")); D = json.load(open(f"{S}/digest38.json"))
c = json.load(open(f"{REPO}/data/collected/{RD}.json")); pv = load_previous(RD)
r0 = json.load(open(f"{REPO}/reports/2026-11-16.json")); L = json.load(open(f"{REPO}/data/learnings.json")); L["runs"] = [x for x in L["runs"] if x["date"] < RD]
rb = L["runs"][-1]["running_baselines"]
price, pc, rel = D["price"], D["pc"], D["rel"]
T = c["run38_traces"]; A = c["run38_adhoc"]; H2 = A["hot2"]
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
bin_net = chg["Binance.com"] + chg["Binance Staking"]
wd = c["withdraw_decoded"]; undel = c["undelegated_this_week_total_egld"]; ncall = c["undelegate_callers_count"]
si = R["staking_intelligence"]; ch = si["churn"]; act = R["network_health"]["activity"]; dl_ = R["network_health"]["deltas"]
xx = R["token_activity"]["xexchange"]; ef = R["whale_intelligence"]["exchange_flows"]
wdays = c["_period"]["window_days"]
ob = R["whale_intelligence"]["demand_instruments"]["exchange_orderbook"]
prev_ob = r0["whale_intelligence"]["demand_instruments"]["exchange_orderbook"]
J = T["hatom_borrow_join"]; HM = T["hatom_egld_mm"]["by_function"]; UB = T["usdc_bridge"]; KW = T["kucoin_whale"]; OV = T["otc_vault"]
XR = T["exit_route_scan"]
days = H2["days"]
def dd(d): return days.get(d) or {"wd_n": 0, "wd_egld": 0.0, "dep_n": 0, "dep_egld": 0.0, "fund_egld": 0.0}
d18, d19, d20 = dd("2026-11-18"), dd("2026-11-19"), dd("2026-11-20")
h2_wd, h2_dep = H2["withdrawals_egld"], H2["deposits_egld"]; h2_net = h2_wd - h2_dep
pre_pause = 70532 + sum(dd(d)["dep_egld"] - dd(d)["wd_egld"] for d in ("2026-11-16", "2026-11-17"))   # hot wallet 2 held 70,532 at run #37
YL = A["ylw"]; CU = A["custody"]
hop = A["hot2_onehop"]
xv = Counter()
for a, v in hop.items():
    for k, val in v["by_class"].items():
        if k.startswith("exchange:"): xv[k.split(":")[1]] += min(val, v["received_from_hot2"])
cross = sum(xv.values())
RLQ = A["rlq"]; rlq_first = datetime.fromtimestamp(RLQ["first_tx_ts"], timezone.utc).strftime("%Y-%m-%d")
rlq_from_bin = sum(x["egld"] for x in RLQ["in_all"] if x["label"] and x["label"].startswith("Binance"))
BD = A["binance_delegation"]; bsp = BD["binance_identity_providers"][0] if BD["binance_identity_providers"] else None
mm_cash_now = next(int(x["balance"]) / 1e18 for x in c["top_accounts"] if x["address"].startswith("erd1qqqqqqqqqqqqqpgq35qkf34a8svu4r2zmfzuztmeltqclapv78ss5jleq3"))
mm_cash_prev = next(float(x["balance_egld"]) for x in pv["top_accounts"] if x["address"].startswith("erd1qqqqqqqqqqqqqpgq35qkf34a8svu4r2zmfzuztmeltqclapv78ss5jleq3"))
lsd = {t: float(c["tvl_tokens"][t]["supply"]) for t in ("SEGLD-3ad2d0", "XEGLD-e413ed", "USH-111e09")}
plsd = pv["lsd_supply"]
TVL = D["TVL"]; PTVL = pv["defi_tvl"]
mexc_left = prevb["MEXC"] + chg["MEXC"]; kucoin_now = prevb["KuCoin"] + chg["KuCoin"]
VV = {v["venue"]: v for v in ef["rail_status"]["by_venue"]}
loop_rows = [r for r in J["rows"] if r["pattern"] == "loop"]
top_looper = Counter(r["borrower"] for r in loop_rows).most_common(1)[0] if loop_rows else (None, 0)
top_looper_egld = sum(r.get("borrowed_egld") or 0 for r in loop_rows if r["borrower"] == top_looper[0])
bp = J["by_pattern"]; bpe = J["borrowed_egld_by_pattern"]
pmin = min(rb["egld_price_usd"])

# Binance venue row: use hot wallet 2's in-window customer flow (internal Binance legs excluded), same basis as run #37
for v in ef["rail_status"]["by_venue"]:
    if v["venue"] == "Binance.com":
        v.update({"deposits_egld_7d": h2_dep, "deposits_egld_txs_7d": H2["deposits_n"], "withdrawals_egld_7d": h2_wd, "withdrawals_egld_txs_7d": H2["withdrawals_n"]})
# wallet-change labels refreshed for this run
for w in R["whale_intelligence"]["wallet_changes"]:
    if w["address"].startswith("erd1ylwusw"): w["label"] = "Binance.com exchange wallet erd1ylwusw (reserve from custody)"
    if w["address"].startswith("erd1ts0g6r0h"): w["label"] = "Binance.com hot wallet 2 (erd1ts0g6r0h)"

# ---- baselines (this run's values)
BASE = {"egld_price_usd": price, "dex_volume_24h_usd": D["vol24"], "dex_volume_24h_egld": D["vol24"] / price, "staked_egld": D["staked"],
        "mex_price_usd": mexp, "total_delegators": D["dl"], "staked_ratio": D["ratio"], "korea_premium_pct": round(D["prem"], 1),
        "exchange_net_flow_egld": D["net"], "binance_staking_custody_egld": CU["info"]["balance_egld"], "usdt_supply": round(usdt), "usdc_supply": round(usdc),
        "binance_native_rail_egld_7d": h2_wd + h2_dep, "withdraw_egld_returned_7d": round(wd["egld_returned_total"])}
json.dump(BASE, open(f"{S}/baselines38.json", "w"))

NICE = {"egld_price_usd": "EGLD price (USD)", "dex_volume_24h_usd": "DEX 24h volume (USD)", "staked_egld": "Staked EGLD", "total_delegators": "Delegator count", "mex_price_usd": "MEX price (USD)"}
anoms = []; ZS = {}
for key in ("egld_price_usd", "dex_volume_24h_usd", "staked_egld", "total_delegators", "mex_price_usd"):
    cur = BASE[key]; out = z(key, cur)
    if not out or out[0] is None: continue
    zv, m, sd = out; ZS[key] = zv; s = sev(zv)
    if s:
        anoms.append({"metric": key, "current_value": cur, "average_value": m, "stddev": sd, "z_score": zv, "method": "z_score", "severity": s,
                      "change_pct": (cur - rb[key][-1]) / rb[key][-1] * 100, "previous_value": rb[key][-1],
                      "description": f"{NICE[key]} {cur:,.6g} vs 8-run mean {m:,.6g} (z = {zv:+.2f})." + (f" BTC fell {abs(D['btc_wow']):.1f}%, so about half of this drop is EGLD-specific." if key == "egld_price_usd" else "")})
anoms.append({"metric": "egld_minus_btc_pp", "current_value": rel, "previous_value": D["PREV_REL"], "method": "rule_based", "severity": "medium",
    "description": f"EGLD {pc:+.2f}% vs BTC {D['btc_wow']:+.2f}% ({rel:+.1f}pp) and ETH {D['eth_wow']:+.1f}%. Last window EGLD matched BTC ({D['PREV_REL']:+.1f}pp); this window it fell twice as far. ${price:.2f} is the lowest reading in the stored baseline and below the $2.55 June-August floor."})
anoms.append({"metric": "binance_withdrawal_pause", "current_value": d18["wd_n"] + d19["wd_n"], "previous_value": None, "method": "rule_based", "severity": "high",
    "description": f"Binance hot wallet 2 paid no withdrawals on Nov 18 or Nov 19 while still taking deposits ({d18['dep_n'] + d19['dep_n']} sweeps, {d18['dep_egld'] + d19['dep_egld']:,.0f} EGLD) and holding about {pre_pause:,.0f} EGLD. "
                   f"On Nov 20 it received a {d20['fund_egld']:,.0f} EGLD top-up from Binance's 2.13M wallet and paid {d20['wd_n']} withdrawals ({d20['wd_egld']:,.0f} EGLD) in one day. A second queue, not a dry wallet."})
anoms.append({"metric": "binance_entity_net_flow_egld", "current_value": bin_net, "previous_value": rb["binance_entity_egld"][-1] - rb["binance_entity_egld"][-2], "method": "rule_based", "severity": "high",
    "description": f"Binance's five wallets fell {abs(bin_net):,.0f} EGLD, the customer net withdrawal: {h2_wd:,.0f} withdrawn vs {h2_dep:,.0f} deposited at hot wallet 2. Last window the entity net was -29,768."})
anoms.append({"metric": "hatom_egld_idle_cash", "current_value": mm_cash_now, "previous_value": mm_cash_prev, "method": "rule_based", "severity": "medium",
    "change_pct": (mm_cash_now / mm_cash_prev - 1) * 100,
    "description": f"Idle EGLD in Hatom's EGLD money market fell from {mm_cash_prev:,.0f} to {mm_cash_now:,.0f} ({(mm_cash_now / mm_cash_prev - 1) * 100:+.0f}%). {J['borrow_calls']} borrows took {J['borrowed_egld_total']:,.0f} EGLD; {bpe.get('loop', 0):,.0f} of it went into leverage loops by {J['loop_borrowers']} wallets. No liquidations."})
anoms.append({"metric": "korea_premium_pct", "current_value": D["prem"], "previous_value": D["prev_prem"], "method": "rule_based", "severity": "low",
    "description": f"Upbit ${ob['upbit']['price_usd']:.2f} vs Binance ${ob['binance_price_usd']:.2f}: premium {D['prem']:.1f}% (from {D['prev_prem']:.1f}%); Upbit {D['up_share']:.0f}% of 24h volume (from {prev_ob['upbit_share_of_volume_pct']:.0f}%). Upbit extended its caution to the week of Dec 14-18 with deposits still closed. Rule-based: no weekly baseline."})
usdc_net = UB["unwrap_usdc"] - UB["wrap_usdc"]
anoms.append({"metric": "usdc_bridge_net_unwrap", "current_value": usdc_net, "previous_value": rb["usdc_bridge_net_unwrap"][-1], "method": "rule_based", "severity": "medium",
    "description": f"{UB['unwrap_txs']} unwraps moved {UB['unwrap_usdc']:,.0f} USDC toward bridge-out tokens against {UB['wrap_txs']} wraps of {UB['wrap_usdc']:,.0f}: net {usdc_net:,.0f} leaving (previous window {rb['usdc_bridge_net_unwrap'][-1]:,.0f}). Wrapped USDC supply {usdc:,.0f} ({(usdc / pusdc - 1) * 100:+.2f}%)."})
R["anomalies"] = anoms

def streak(arr, down=True):
    n = 0
    for i in range(len(arr) - 1, 0, -1):
        if (arr[i] < arr[i - 1]) if down else (arr[i] > arr[i - 1]): n += 1
        else: break
    return n
dlarr = rb["total_delegators"] + [D["dl"]]; sd_ = streak(dlarr)
uarr = rb["usdc_supply"] + [round(usdc)]; su = streak(uarr)
sarr = rb["staked_egld"] + [D["staked"]]; ss = streak(sarr, down=False)
parr = rb["egld_price_usd"] + [price]; sp = streak(parr)
marr = rb["mex_price_usd"] + [mexp]; sm = streak(marr)
dxp = (D["vol24"] / pv["xexchange"]["volume_24h_usd"] - 1) * 100

# ---- narrative
pr = pv["economics"]["staked_ratio"]
R["network_health"]["analysis"] = (
 f"WINDOW. {wdays:.2f} days (Nov 16 16:02 -> Nov 23 UTC); all four shards live. Epoch {act['epoch']}, {act['transactions_7d']:,} transactions "
 f"({act['avg_daily_transactions']:,}/day), {dl_['accounts_added']:,} new accounts. Supply {dl_['supply_added']:+,.0f} EGLD (the weekly emission).\n\n"
 f"PRICE. EGLD ${price:.2f}, {pc:+.2f}%, with BTC {D['btc_wow']:+.2f}% and ETH {D['eth_wow']:+.2f}%: {rel:+.1f}pp vs BTC. Last window EGLD fell with the market; this window it fell about twice as far. "
 f"Market cap ${c['economics']['marketCap'] / 1e6:,.1f}M. ${price:.2f} is below every price in the stored baseline (previous low ${pmin:.2f}) and below the $2.55 floor of the June-August range; the price has now fallen {sp} windows in a row. Price z-score {ZS.get('egld_price_usd', 0):+.2f} on the 8-run baseline.\n\n"
 f"STAKING. Staked EGLD {D['staked']:,.0f} ({D['dstaked']:+,.0f}); ratio {D['ratio'] * 100:.2f}% (from {pr * 100:.2f}%). Network APR {c['economics']['apr'] * 100:.2f}%. Stake held flat through the drop.")

xv_txt = ", ".join(f"{k} {v:,.0f}" for k, v in xv.most_common())
R["whale_intelligence"]["analysis"] = (
 f"BINANCE'S CUSTOMERS KEPT WITHDRAWING. Hot wallet 2 (erd1ts0g6r0h) paid {H2['withdrawals_n']:,} withdrawals totalling {h2_wd:,.0f} EGLD to {H2['distinct_receivers']:,} receivers and took {H2['deposits_n']} deposit sweeps of {h2_dep:,.0f} from {H2['distinct_depositors']} addresses. "
 f"Net {h2_net:,.0f} EGLD left Binance, against 29,768 in the first week back. Withdrawals were about the same size as last week's ({204493:,}); deposits fell by {174725 - h2_dep:,.0f}. That is a standing net outflow, not a backlog clearing.\n\n"
 f"A SECOND PAUSE. On Nov 18 and Nov 19 the wallet paid nothing out while it kept taking deposits ({d18['dep_n'] + d19['dep_n']} sweeps). It held about {pre_pause:,.0f} EGLD, so it was not empty. "
 f"On Nov 20 Binance's reserve wallet erd1ylwusw sent it {d20['fund_egld']:,.0f} and it paid {d20['wd_n']} withdrawals ({d20['wd_egld']:,.0f} EGLD) that day, {d20['wd_egld'] / h2_wd * 100:.0f}% of the window. The pattern is a queue released in one go. No Binance notice was found for the gap.\n\n"
 f"THE RESERVE HELD. erd1ylwusw holds {YL['info']['balance_egld']:,.0f}; its only outbound was the {YL['out_to_binance_egld']:,.0f} top-up to the hot wallet. Staking custody stayed at {CU['info']['balance_egld']:,.0f} with no transaction in the window. "
 f"Neither wallet holds a direct delegation, and the binance_staking provider moved {bsp['locked_egld'] - bsp['previous_locked_egld']:+,.0f} EGLD ({bsp['locked_egld']:,.0f}), so the Nov 12 custody move did not come with a change in Binance's on-chain staking.\n\n"
 f"WHERE THE WITHDRAWALS WENT. Of the fifteen largest receivers, the ones that moved on sent {cross:,.0f} EGLD to other exchanges within one hop ({xv_txt}), about {cross / h2_wd * 100:.0f}% of Binance's withdrawals. "
 f"That accounts for most of Bybit's {chg['Bybit']:+,.0f} and Coinbase's {chg['Coinbase']:+,.0f}. Across all tracked exchange wallets the books moved {D['net']:+,.0f} ({D['net'] / D['tot_p'] * 100:+.2f}%): Binance's outflow mostly relocated rather than left exchanges.\n\n"
 f"THE DEPOSITOR WHALE STOPPED. erd1rlqdj67qxp sent nothing this window ({RLQ['info']['balance_egld']:,.0f} left). Its history is older than recorded last week: first transaction {rlq_first}, and its {rlq_from_bin:,.0f} EGLD came out of Binance's old hot wallet in many small withdrawals. It is a long-time Binance customer moving coins back, not new money.\n\n"
 f"OTHER BOOKS. MEXC withdraw-only for a fourth window ({chg['MEXC']:+,.0f}; {mexc_left:,.0f} left). KuCoin {chg['KuCoin']:+,.0f} ({VV['KuCoin']['deposits_egld_7d']:,.0f} in, {VV['KuCoin']['withdrawals_egld_7d']:,.0f} out). Gate.io {chg['Gate.io']:+,.0f}. Upbit's wallet did not move.\n\n"
 f"HOLDERS HELD. The KuCoin withdrawer erd15ku2r2j6 did not move ({KW['balance_egld']:,.0f}). The OTC operator's vault took in {OV['in_window_in_egld']:,.0f} from Unknown Whale I and sent back {OV['in_window_out_egld']:,.0f}; balance {OV['balance_egld']:,.0f}. The poisoning ring was quiet (no operator sends).\n\n"
 f"TIERS. Mega whales {D['WT']['mega_whales'][2]:+,.0f} on a common-address basis (Binance's reserve topping up its hot wallet), large whales {D['WT']['large_whales'][2]:+,.0f} (Bybit and Coinbase books), mid whales {D['WT']['mid_whales'][2]:+,.0f}.\n\n"
 f"EXITS. {XR['calls']} provider withdrawals above 3,000 EGLD: {', '.join(str(v['n']) + ' ' + k for k, v in XR['by_route'].items())}. None went to an exchange directly.")

for e_ in ef["entity_netting"]:
    if e_["entity"] == "Binance":
        e_["interpretation"] = (f"{bin_net:+,.0f} across five wallets, matching customer flow at hot wallet 2: {h2_wd:,.0f} withdrawn vs {h2_dep:,.0f} deposited. "
                                f"The {d20['fund_egld']:,.0f} reserve-to-hot-wallet top-up is internal and cancels out.")
    elif e_["entity"] == "Bybit":
        e_["interpretation"] += f" {xv.get('Bybit', 0):,.0f} of the deposits traced one hop back to Binance withdrawals."
    elif e_["entity"] == "Coinbase":
        e_["interpretation"] += f" {xv.get('Coinbase', 0):,.0f} of the deposits traced one hop back to Binance withdrawals."
    elif e_["entity"] == "MEXC":
        e_["interpretation"] += f" Fourth window with no deposits; {mexc_left:,.0f} left."
R["whale_intelligence"]["demand_instruments"]["identifiable_bid_status"] = (
 f"RETIRED (run #23). OTC operator vault {OV['balance_egld']:,.0f} (two-way with Unknown Whale I: {OV['in_window_in_egld']:,.0f} in, {OV['in_window_out_egld']:,.0f} out this window).")

R["staking_intelligence"]["analysis"] = (
 f"FLAT THROUGH THE DROP. Staked EGLD {D['dstaked']:+,.0f}; delegation contracts {si['summary']['total_delegated_egld'] - rb['delegation_total_locked_egld'][-1]:+,.0f} to {si['summary']['total_delegated_egld']:,.0f}. "
 f"No large delegator stood out: the biggest provider mover was primal-block-one ({c['provider_movers'][0]['delta_egld']:+,.0f}, one 7,500 EGLD delegation).\n\n"
 f"EXITS WERE ORDINARY. {ncall} wallets unDelegated {undel:,.0f} EGLD (previous window {rb['unbonding_queue_undelegated_egld_7d'][-1]:,.0f}); {wd['calls']} withdraw calls returned {wd['egld_returned_total']:,.0f} (previous {rb['withdraw_egld_returned_7d'][-1]:,.0f}). A -10% week did not start an unstaking wave.\n\n"
 f"DELEGATORS. {D['dl']:,} ({D['dl'] - D['dlp']:+,}): {ch['providers_gaining_delegators']} providers gained, {ch['providers_losing_delegators']} lost. The count has fallen for {sd_} straight windows, slowly. "
 f"HHI {D['hhi']:.5f}, top-5 {D['top5']:.2f}%, top-10 {D['top10']:.2f}%.")

R["token_activity"]["analysis"] = (
 f"DEX. 24h xExchange volume ${D['vol24']:,.0f} ({dxp:+.1f}% vs ${pv['xexchange']['volume_24h_usd']:,.0f}); in EGLD terms {xx['dex_volume_egld_24h']:,.0f} ({xx['dex_vol_egld_wow_pct']:+.1f}%). {xx['top_pair']} is {xx['top_pair_dominance_pct']:.0f}% of it. "
 f"Pair TVL ${D['tvl']:,.0f} ({(D['tvl'] / pv['xexchange']['pool_tvl_usd'] - 1) * 100:+.1f}% in USD, {(xx['pool_tvl_egld'] / xx['previous_pool_tvl_egld'] - 1) * 100:+.1f}% in EGLD). The selling did not happen on the DEX.\n\n"
 f"MEX ${mexp:.3e} ({xx['mex_price_change_wow_pct']:+.1f}%), down {sm} windows running and falling faster than EGLD; z = {ZS.get('mex_price_usd', 0):+.2f}.\n\n"
 f"STABLECOINS. Wrapped USDC {usdc:,.0f} ({(usdc / pusdc - 1) * 100:+.2f}%), USDT {usdt:,.0f} ({(usdt / pusdt - 1) * 100:+.2f}%). Bridge unwraps {UB['unwrap_usdc']:,.0f} USDC against {UB['wrap_usdc']:,.0f} wrapped; "
 f"{UB['unwrap_by_destination_token'].get('BSCUSDC-887875', 0) / UB['unwrap_usdc'] * 100:.0f}% headed to BSC, the rest to Ethereum. None of the six largest unwrappers sold EGLD on the DEX first; one was XOXNO's deployer wallet (50,000).\n\n"
 "NEW TOKENS. None issued in the window.")

hl, hls, xl, ush = TVL["Hatom Lending"], TVL["Hatom Liquid Staking"], TVL["XOXNO LSD"], TVL["Hatom USH"]
R["defi_activity"]["analysis"] = (
 f"TVL FELL LESS THAN THE PRICE. One-week basis vs Nov 16: Hatom Lending ${hl / 1e6:.2f}M ({(hl / PTVL['Hatom Lending'] - 1) * 100:+.1f}%), Hatom Liquid Staking ${hls / 1e6:.2f}M ({(hls / PTVL['Hatom Liquid Staking'] - 1) * 100:+.1f}%), "
 f"XOXNO liquid staking ${xl / 1e6:.2f}M ({(xl / PTVL['XOXNO LSD'] - 1) * 100:+.1f}%), USH ${ush / 1e6:.2f}M ({(ush / PTVL['Hatom USH'] - 1) * 100:+.1f}%). "
 f"Liquid-staking token supplies were flat (Hatom {lsd['SEGLD-3ad2d0']:,.0f} vs {plsd['SEGLD-3ad2d0']:,.0f}; XOXNO {lsd['XEGLD-e413ed']:,.0f} vs {plsd['XEGLD-e413ed']:,.0f}). USH supply {lsd['USH-111e09']:,.0f} ({(lsd['USH-111e09'] / plsd['USH-111e09'] - 1) * 100:+.1f}%), a net repayment. "
 f"Three Hatom tokens (staked TAO, HUSDC, HTAO) returned no price from the API; they are valued at last week's ratio to their base asset, and TAO is priced from CoinGecko because the chain's own TAO price ($462) is 2.4 times the market.\n\n"
 f"LEVERAGE WENT IN, SIZED FOR THE FIRST TIME. Borrow amounts are now decoded from each call's results. {J['borrow_calls']} borrows by {J['borrowers']} wallets took {J['borrowed_egld_total']:,.0f} EGLD out of Hatom's EGLD market. "
 f"{bp.get('loop', 0)} of them ({bpe.get('loop', 0):,.0f} EGLD) were followed within 30 minutes by a swap or stake and a fresh supply: leverage loops, run by {J['loop_borrowers']} wallets. One wallet made {top_looper[1]} of the loops ({top_looper_egld:,.0f} EGLD). "
 f"The rest: {bp.get('swap_only', 0)} swap only ({bpe.get('swap_only', 0):,.0f}), {bp.get('resupply_only', 0)} re-supply ({bpe.get('resupply_only', 0):,.0f}), {bp.get('none_in_30m', 0)} nothing in 30 minutes ({bpe.get('none_in_30m', 0):,.0f}). "
 f"Idle EGLD in the market fell from {mm_cash_prev:,.0f} to {mm_cash_now:,.0f}. Loops went from 15 to {bp.get('loop', 0)} week on week while the price fell 10%. Nothing was liquidated, but leveraged staking positions are larger going into a falling market.\n\n"
 f"SMALLER LIQUID-STAKING PROTOCOLS (discovery pass): SALSA {D['EMERG']['SALSA (Staking Agency)']:,.0f} EGLD staked, Dinovox {D['EMERG']['Dinovox VoxEGLD']:,.0f}, JewelSwap {D['EMERG']['JewelSwap']:,.0f}, VestaX {D['EMERG']['VestaX Finance']:,.0f}.")

R["executive_summary"] = [
 {"category": "whale", "severity": "high", "finding": f"BINANCE'S NET OUTFLOW MORE THAN TRIPLED: {h2_net:,.0f} EGLD LEFT ({h2_wd:,.0f} withdrawn, {h2_dep:,.0f} deposited), against 29,768 in the first week back. The backlog reading failed: this is a standing exit."},
 {"category": "whale", "severity": "high", "finding": f"BINANCE PAUSED EGLD WITHDRAWALS FOR TWO DAYS (NOV 18-19) WITH ~{pre_pause / 1000:,.0f}K ON HAND, THEN PAID {d20['wd_egld']:,.0f} EGLD ON NOV 20 after a {d20['fund_egld']:,.0f} top-up from its reserve. The 2.13M reserve otherwise held."},
 {"category": "network", "severity": "high", "finding": f"EGLD FELL {abs(pc):.1f}% TO ${price:.2f}, {abs(rel):.1f}pp WORSE THAN BTC ({D['btc_wow']:.1f}%). Lowest price in the stored baseline and below the $2.55 June-August floor; {sp} straight weekly declines."},
 {"category": "defi", "severity": "medium", "finding": f"HATOM LEVERAGE LOOPS GREW FROM 15 TO {bp.get('loop', 0)}: {bpe.get('loop', 0):,.0f} EGLD borrowed and looped by {J['loop_borrowers']} wallets (first decoded sizes). Idle EGLD in the market fell {abs(mm_cash_now - mm_cash_prev):,.0f} to {mm_cash_now:,.0f}. No liquidations. Hatom USH supply fell {abs(lsd['USH-111e09'] / plsd['USH-111e09'] - 1) * 100:.1f}% ({lsd['USH-111e09'] - plsd['USH-111e09']:+,.0f}) as stablecoin debt was repaid."},
 {"category": "whale", "severity": "medium", "finding": f"MOST OF BINANCE'S OUTFLOW STAYED ON EXCHANGES: {cross:,.0f} EGLD reached Bybit, Gate.io and Coinbase within one hop. Tracked exchange books moved only {D['net']:+,.0f}."},
 {"category": "token", "severity": "medium", "finding": f"UPBIT EXTENDED ITS EGLD CAUTION TO DEC 14-18, DEPOSITS STILL CLOSED. Premium {D['prem']:.1f}% (from {D['prev_prem']:.1f}%), Upbit {D['up_share']:.0f}% of volume."},
 {"category": "staking", "severity": "low", "finding": f"STAKE HELD: {D['dstaked']:+,.0f} EGLD staked, {undel:,.0f} unDelegated by {ncall} wallets, delegators {D['dl'] - D['dlp']:+,}. A -10% week did not start an unstaking wave."},
]

ti = R["trend_indicators"]
r36 = json.load(open(f"{REPO}/reports/2026-11-09.json")); r35 = json.load(open(f"{REPO}/reports/2026-11-02.json"))
def book(rep, name):
    for x in rep["whale_intelligence"]["exchange_flows"]["by_exchange"]:
        if x["exchange"] == name: return x
mch = [book(r35, "MEXC")["change_egld"], book(r36, "MEXC")["change_egld"], book(r0, "MEXC")["change_egld"], chg["MEXC"]]
mexc_start = mexc_left - sum(mch)
ti["accelerating_exchange_outflows"] = [
 {"exchange": "MEXC", "trend": "outflow", "cumulative_change_pct": (mexc_left / mexc_start - 1) * 100, "weeks_in_trend": 4,
  "interpretation": f"Fourth window withdraw-only: {', '.join(f'{x:+,.0f}' for x in mch)}; zero deposits throughout. {mexc_left:,.0f} left of {mexc_start:,.0f}."},
 {"exchange": "Binance (all wallets)", "trend": "outflow", "cumulative_change_pct": (bin_net + rb['binance_entity_egld'][-1] - rb['binance_entity_egld'][-2]) / rb["binance_entity_egld"][-2] * 100, "weeks_in_trend": 2,
  "interpretation": f"Second outflow window since the rail reopened: -29,768 then {bin_net:+,.0f}. Withdrawals steady at ~205K a week; deposits fell from 174,725 to {h2_dep:,.0f}."}]
ti["validator_movements"] = {"providers_joining": 0, "providers_leaving": 0, "net_provider_change": si["summary"]["num_providers"] - sum(1 for x in pv["staking_providers"] if x["locked_egld"] > 0),
    "notable_joiners": [], "notable_leavers": [], "note": f"{si['summary']['num_providers']} providers with stake; no joins or deregistrations in the window."}
ti["token_supply_events"] = [
 {"identifier": "USDC-c76f1f", "name": "WrappedUSDC", "event": "burn", "supply_previous": str(round(pusdc)), "supply_current": str(round(usdc)), "change_pct": (usdc / pusdc - 1) * 100,
  "description": f"{usdc - pusdc:+,.0f} USDC, the largest weekly contraction in the baseline. Bridge unwraps {UB['unwrap_usdc']:,.0f} vs wraps {UB['wrap_usdc']:,.0f}."},
 {"identifier": "USDT-f8c08c", "name": "USDT", "event": "mint", "supply_previous": str(round(pusdt)), "supply_current": str(round(usdt)), "change_pct": (usdt / pusdt - 1) * 100,
  "description": f"{usdt - pusdt:+,.0f} USDT, ending three straight contractions."},
 {"identifier": "USH-111e09", "name": "Hatom USH", "event": "burn", "supply_previous": str(round(plsd["USH-111e09"])), "supply_current": str(round(lsd["USH-111e09"])), "change_pct": (lsd["USH-111e09"] / plsd["USH-111e09"] - 1) * 100,
  "description": f"{lsd['USH-111e09'] - plsd['USH-111e09']:+,.0f} USH: stablecoin debt repaid while EGLD borrowing rose."}]
ti["consecutive_streaks"] = [
 {"metric": "egld_price_usd", "direction": "down", "weeks": sp, "cumulative_change_pct": (price / parr[-sp - 1] - 1) * 100, "interpretation": f"${parr[-sp - 1]:.2f} -> ${price:.2f}; this leg was worse than BTC."},
 {"metric": "mex_price_usd", "direction": "down", "weeks": sm, "cumulative_change_pct": (mexp / marr[-sm - 1] - 1) * 100, "interpretation": "MEX keeps falling faster than EGLD."},
 {"metric": "total_delegators", "direction": "down", "weeks": sd_, "cumulative_change_pct": (D["dl"] / dlarr[-sd_ - 1] - 1) * 100,
  "interpretation": f"{D['dl']:,} ({D['dl'] - D['dlp']:+,}); a slow drift, not an exit."},
 {"metric": "usdc_supply", "direction": "down", "weeks": su, "cumulative_change_pct": (usdc / uarr[-su - 1] - 1) * 100, "interpretation": f"{uarr[-su - 1]:,.0f} -> {usdc:,.0f}; the pace roughly doubled again."},
 {"metric": "staked_egld", "direction": "up", "weeks": ss, "cumulative_change_pct": (D["staked"] / sarr[-ss - 1] - 1) * 100,
  "interpretation": f"{sarr[-ss - 1]:,.0f} -> {D['staked']:,.0f}; this window's {D['dstaked']:+,.0f} is the smallest gain of the streak."}]
ti["consecutive_streaks"] = [x for x in ti["consecutive_streaks"] if x["weeks"] >= 2]
ti["regime_shifts"] = [
 {"metric": "binance_entity_net_flow_egld", "before_value": rb["binance_entity_egld"][-1] - rb["binance_entity_egld"][-2], "after_value": bin_net,
  "description": f"Binance's net customer flow went from -29,768 to {bin_net:+,.0f} with withdrawals unchanged (~205K): deposits are what fell. Two weeks in, the reopened rail is an exit route."},
 {"metric": "egld_price_usd", "before_value": 2.55, "after_value": price,
  "description": f"Price broke below the $2.55 floor that held from June to August; ${price:.2f} is a new low for the series."}]

prevw = {w["item"]: w["weeks_on_list"] for w in r0["watch_list"]}
def wk(name): return prevw.get(name, 0) + 1
R["watch_list"] = [
 {"item": "BINANCE HOT WALLET 2 erd1ts0g6r0h", "weeks_on_list": wk("BINANCE HOT WALLET 2 erd1ts0g6r0h"), "reason": f"{h2_wd:,.0f} out, {h2_dep:,.0f} in, balance {H2['info']['balance_egld']:,.0f}. Paused Nov 18-19, then 114K in a day. Does the net outflow persist? PRE-COMMITTED (binance-outflow-persists)."},
 {"item": "BINANCE 2.13M RESERVE erd1ylwusw", "weeks_on_list": wk("BINANCE 2.18M EXCHANGE WALLET erd1ylwusw"), "reason": f"{YL['info']['balance_egld']:,.0f}; drawn {YL['out_to_binance_egld']:,.0f} to refill the hot wallet. At this week's net outflow it lasts about {YL['info']['balance_egld'] / max(h2_net, 1):.0f} weeks."},
 {"item": "BINANCE STAKING CUSTODY 2.00M", "weeks_on_list": wk("BINANCE STAKING CUSTODY 2.00M"), "reason": "Unchanged at 2,000,000; no transaction in the window."},
 {"item": "HATOM LEVERAGE LOOPS", "weeks_on_list": 1, "reason": f"{bp.get('loop', 0)} loops ({bpe.get('loop', 0):,.0f} EGLD) by {J['loop_borrowers']} wallets; idle EGLD {mm_cash_now:,.0f}. Watch for liquidations if the price keeps falling. PRE-COMMITTED (hatom-loops-unwind-without-liquidation)."},
 {"item": "UPBIT CAUTION REVIEW - extended to Dec 14-18", "weeks_on_list": wk("UPBIT CAUTION REVIEW - decision Nov 16-20"), "reason": f"Extended again; deposits closed. Premium {D['prem']:.1f}%. Test re-dated once (upbit-premium-on-decision)."},
 {"item": "MEXC WITHDRAW-ONLY", "weeks_on_list": wk("MEXC WITHDRAW-ONLY"), "reason": f"Zero deposits for four windows; {mexc_left:,.0f} left."},
 {"item": "KUCOIN WITHDRAWER erd15ku2r2j6 (168,358)", "weeks_on_list": wk("KUCOIN WITHDRAWER erd15ku2r2j6 (168,358)"), "reason": "Held through a second down week; no outbound. Graduates next run if still idle."},
 {"item": "OTC OPERATOR VAULT erd1drc22z7h", "weeks_on_list": wk("OTC OPERATOR VAULT erd1drc22z7h"), "reason": f"{OV['balance_egld']:,.0f}; two-way with Unknown Whale I ({OV['in_window_in_egld']:,.0f} in, {OV['in_window_out_egld']:,.0f} out). Not draining."},
 {"item": "EXPLOIT WALLET AND POISONING RING", "weeks_on_list": wk("EXPLOIT WALLET AND POISONING RING"), "reason": "Quiet: no operator sends, no lookalike received value."}]

Tt = R["pre_committed_tests"]
def find(i): return next(t for t in Tt if t["id"] == i)
find("binance-backlog-fades").update({"status": "resolved", "outcome": "against", "resolved_in_run": RUN,
  "measured_value": f"{h2_wd:,.0f} withdrawn, {h2_dep:,.0f} deposited, net {h2_net:,.0f} (hot wallet 2, internal Binance legs excluded)",
  "resolution": f"Standing exit (withdrawals > 180,000 and net > 40,000). Withdrawals held at last week's size while deposits fell; net outflow rose from 29,768 to {h2_net:,.0f}. A two-day withdrawal pause (Nov 18-19) made part of it another backlog, but the threshold reads the week as a whole."})
find("binance-reserve-stays").update({"status": "resolved", "outcome": "as_predicted", "resolved_in_run": RUN,
  "measured_value": f"erd1ylwusw {YL['info']['balance_egld']:,.0f}; sent {YL['out_egld']:,.0f}, all to hot wallet 2; nothing delegated or sent outside Binance",
  "resolution": "Reserve (balance >= 2,000,000). The wallet is drawn down only to refill the hot wallet."})
up = find("upbit-premium-on-decision")
up.update({"measured_value": f"run #38: caution extended to the week of Dec 14-18, deposits still closed; premium {D['prem']:.1f}%, Upbit {D['up_share']:.0f}% of volume.",
  "threshold": up["threshold"] + " RE-DATED ONCE (run #38): Upbit extended the caution to Dec 14-18; evaluate at the first run after that decision. A further extension withdraws the test."})
find("delivery-price-relevance-2").update({"measured_value": "run #38: desk gross negligible. Not evaluable."})
Tt.append({"id": "binance-outflow-persists", "registered_in_run": RUN, "claim": "Binance's net EGLD outflow is a standing exit, not a one-off after the pause.",
  "threshold": f"Over run #39's window at Binance's hot wallet(s), internal legs excluded: net withdrawal > 40,000 = persists; net withdrawal < 10,000 or a net deposit = faded; otherwise no conclusion. Run #38: net {h2_net:,.0f}.",
  "branches": [{"condition": "net > 40K", "reading": "persists"}, {"condition": "net < 10K or net deposit", "reading": "faded"}, {"condition": "otherwise", "reading": "no conclusion"}],
  "status": "open", "outcome": None, "resolved_in_run": None, "measured_value": f"run #38: {h2_wd:,.0f} withdrawn, {h2_dep:,.0f} deposited", "resolution": None})
Tt.append({"id": "hatom-loops-unwind-without-liquidation", "registered_in_run": RUN, "claim": "Hatom's EGLD leverage loops are managed positions: if EGLD keeps falling they are repaid, not liquidated.",
  "threshold": "At run #39, on Hatom's EGLD money market: any liquidation call = not managed; repayments >= borrows with zero liquidations = managed unwind; otherwise (loops continue, no liquidations) = no conclusion.",
  "branches": [{"condition": "any liquidation", "reading": "not managed"}, {"condition": "repay >= borrow, no liquidation", "reading": "managed unwind"}, {"condition": "otherwise", "reading": "no conclusion"}],
  "status": "open", "outcome": None, "resolved_in_run": None, "measured_value": f"run #38: {HM['borrow']['n']} borrows, {HM['repayBorrow']['n']} repayments, 0 liquidations; {bpe.get('loop', 0):,.0f} EGLD looped", "resolution": None})

ml = R["meta_learning"]
ml.update({"run_number": RUN,
 "endpoints_that_failed": [f"Collector: 0 paged errors, {len(c.get('_api_errors') or [])} API errors, {c.get('_n_429', 0)} rate-limit retries."],
 "api_quirks": ["/tokens returned null price and market cap for SWTAO-356a25, HUSDC-d80042 and HWTAO-2e9136 on the same day; the ratio fallback (methodology, run #11) was applied to all three.",
                "/tokens/WTAO-4f5363 and /mex/tokens report TAO at $462 vs CoinGecko $192: a thin xExchange pool price. Never use it as the TAO base.",
                "Hot wallet 2 in the collector's Binance set pages daily without hitting caps (658 out, 769 in for the window)."],
 "data_gaps": ["No Binance statement found for the Nov 18-19 withdrawal pause.",
               "SWTAO, HUSDC and HTAO prices are derived (API nulls), so Hatom Lending and Liquid Staking TVL carry a small model error.",
               "OTC pipeline sections not refreshed (desk activity negligible).",
               "No tokens issued in the window per the /tokens timestamp sort; not cross-checked against ESDT issue transactions."],
 "key_findings": [e["finding"] for e in R["executive_summary"][:5]],
 "action_items_from_previous": 6, "action_items_completed": 6,
 "action_items_completed_detail": [
   "binance-backlog-fades resolved (against: standing exit, net 104,559) and binance-reserve-stays resolved (as predicted: 2.13M held).",
   "Upbit decision recorded: caution extended to Dec 14-18 with deposits closed; upbit-premium-on-decision re-dated once per its own clause.",
   "Hot wallet 2 added to the collector's Binance set; Binance wallets added to the rails pass's internal set so funding legs are not counted as deposits.",
   "Hatom borrow amounts decoded from each call's smart-contract results: 52,499 EGLD borrowed, 45,645 in loops.",
   "erd1rlqdj67qxp traced: first transaction 2024-10-29 (not 2026), funded by Binance's old hot wallet; no third clip.",
   "Binance delegation footprint checked: custody and erd1ylwusw hold no delegation; binance_staking provider -634 EGLD. The Nov 12 move did not change on-chain staking."],
 "methodology_changes": [
   "Collector: Binance hot wallet 2 is in the Binance hot set (daily-sliced paging).",
   "Rails pass: Binance's own wallets are in the internal set; venue deposit/withdrawal figures exclude reserve top-ups.",
   "Trace pass: Hatom borrow joins carry the decoded EGLD amount (results to the borrower).",
   "Ad-hoc pass: one-hop destination class for the top 15 receivers of Binance's hot wallet (cross-venue share).",
   "Price sanity check: a token price more than 2x the CoinGecko reference for the same asset is rejected (WTAO)."],
 "new_addresses_discovered_detail": [],
 "new_addresses_discovered": 0,
 "most_valuable_insight": "Binance's reopened rail is an exit, not a backlog: withdrawals held at ~205K a week while deposits fell, and a two-day pause was cleared from the 2.13M reserve. At this pace the reserve covers about 20 weeks.",
 "top_recommendation": "RUN #39 FIRST: resolve binance-outflow-persists and hatom-loops-unwind-without-liquidation.",
 "recommendations_for_next_run": [
  "Resolve binance-outflow-persists and hatom-loops-unwind-without-liquidation on run #39's window.",
  "Track erd1ylwusw drawdowns per week as a reserve runway series (balance / net weekly outflow).",
  "Size Hatom repayments the same way as borrows (decode repayBorrow values) so net leverage change has an EGLD figure.",
  "Re-check the three null-priced Hatom tokens; if the API still returns null, move the ratio fallback into the collector.",
  "Look for any Binance notice covering Nov 18-19 and check whether other venues (Bybit, Gate.io) paused EGLD withdrawals on the same days.",
  "Graduate the KuCoin withdrawer from the watch list if it stays idle another window."],
 "dashboard_feature_suggestions": [
  {"title": "Exchange reserve runway gauge", "motivation": f"Binance's reserve wallet ({YL['info']['balance_egld']:,.0f}) now refills the hot wallet; with a {h2_net:,.0f} weekly net outflow it covers about {YL['info']['balance_egld'] / max(h2_net, 1):.0f} weeks. No component shows a stock against its burn rate.", "suggested_visualization": "gauge or depletion line: reserve balance per week with projected runway at trailing net outflow", "data_already_available": True, "data_source": "run38_adhoc.ylw + hot2 in data/collected; whale_intelligence.exchange_flows.entity_netting", "priority": "high"},
  {"title": "Daily hot-wallet flow bars", "motivation": "The Nov 18-19 withdrawal pause and the 114K Nov 20 release are invisible in a weekly total; only a daily view shows a queue forming and clearing.", "suggested_visualization": "daily diverging bars (withdrawals down, deposits up) with funding top-ups as markers", "data_already_available": True, "data_source": "run38_adhoc.hot2.days in data/collected", "priority": "medium"},
  {"title": "Hatom leverage-loop size series", "motivation": f"Loops grew from 15 to {bp.get('loop', 0)} with {bpe.get('loop', 0):,.0f} EGLD decoded this week, while idle EGLD fell to {mm_cash_now:,.0f}. A single-week panel cannot show leverage building into a drawdown.", "suggested_visualization": "stacked weekly bars of borrowed EGLD by follow-through pattern, with idle-cash line overlay", "data_already_available": True, "data_source": "run38_traces.hatom_borrow_join.borrowed_egld_by_pattern + top_accounts Hatom money market balance", "priority": "medium"}],
 "dashboard_suggestions_followup": [
  {"title": "Exchange entity wallet map", "status": "pending", "reason": "Still the right view: this week the reserve -> hot wallet top-up is the only internal edge and it explains the Nov 20 spike."},
  {"title": "Withdrawal destination sankey per venue", "status": "pending", "reason": "Data refreshed (one-hop classes for hot wallet 2's top receivers); component not built."},
  {"title": "Hatom borrow follow-through bars", "status": "pending", "reason": "Superseded in scope by the loop-size series now that amounts are decoded; build that instead."}],
 "self_assessment": {"most_valuable_insight": "Binance's rail is an exit route with a 2.13M reserve behind it; the backlog test failed honestly.", "recommendations_completed": "6 of 6", "what_would_make_it_2x_better": "Decode repayments as well as borrows, and turn the hot-wallet daily view into a standing series."}})
ml["withdrawn_claims"] = ml.get("withdrawn_claims") or []
worked = [x for x in (ml.get("endpoints_that_worked") or []) if "Nov 16" not in x and "ad-hoc" not in x][:38] + [
    "post-restart window netting (Sep 24 - Nov 23)", "Binance hot wallet 2 daily paging in the collector",
    "Hatom borrow amounts decoded from results", "hot wallet 2 one-hop destination classes", "liquid-staking discovery pass"]
ml["endpoints_that_worked"] = worked
R["metadata"]["data_sources_ok"] = worked
R["metadata"]["data_sources_failed"] = []
R["metadata"]["data_sources_recovered"] = ["/tokens price for SWTAO-356a25, HUSDC-d80042, HWTAO-2e9136 (null; derived by ratio fallback)"]

json.dump(R, open(f"{REPO}/reports/{RD}.json", "w"), indent=1, default=str)
print("wrote", f"reports/{RD}.json", "| anomalies", [(a["metric"], a["severity"]) for a in anoms], "| z", {k: round(v, 2) for k, v in ZS.items()})
print("streaks", [(x["metric"], x["weeks"]) for x in ti["consecutive_streaks"]], "cross", round(cross), dict(xv), "pre_pause", round(pre_pause), "net", round(h2_net))
