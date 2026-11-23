#!/usr/bin/env python3
"""Run #38: refresh previous.json, methodology (new rules + Evolution Log row) and append the learnings entry.
known-addresses.json was updated before assembly (hot wallet 2, depositor whale, two lookalikes). Idempotent: re-running
replaces this run's learnings entry and methodology block instead of appending twice."""
import json, copy, sys
sys.path.insert(0, "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/scripts")
from report_template import archive_previous, load_previous
REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"; RD = "2026-11-23"; RUN = 38
S = "/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/949f11b7-26bf-4a9a-b4a7-ae3219fe2344/scratchpad"
c = json.load(open(f"{REPO}/data/collected/{RD}.json")); R = json.load(open(f"{REPO}/reports/{RD}.json"))
cur_prev = json.load(open(f"{REPO}/data/previous.json"))
if cur_prev["snapshot_date"] < RD: archive_previous(cur_prev)   # keep the pre-run snapshot so assemblers can be re-run safely
pv = load_previous(RD)
kn = json.load(open(f"{REPO}/data/known-addresses.json")); L = json.load(open(f"{REPO}/data/learnings.json"))
D = json.load(open(f"{S}/digest38.json")); B = json.load(open(f"{S}/baselines38.json"))
A = c["run38_adhoc"]; H2 = A["hot2"]; T = c["run38_traces"]
LM = {}
for s, e in kn.items():
    if isinstance(e, dict):
        for a, m in e.items():
            if isinstance(m, dict) and a.startswith("erd1"): LM[a] = m.get("name")
eco = c["economics"]; st = c["stats"]; E = 1e18
P = copy.deepcopy(pv); P.pop("_run37_note", None)
P["snapshot_date"] = RD
P["economics"] = {"egld_price_usd": eco["price"], "market_cap_usd": eco["marketCap"], "total_supply": eco["totalSupply"], "circulating_supply": eco["circulatingSupply"],
  "staked_egld": eco["staked"], "staked_ratio": eco["staked"] / eco["circulatingSupply"], "staking_apr": eco["apr"], "base_apr": eco["baseApr"], "topup_apr": eco["topUpApr"],
  "token_market_cap_usd": eco["tokenMarketCap"], "btc_price_usd": c["btc_eth"]["bitcoin"]["usd"], "eth_price_usd": c["btc_eth"]["ethereum"]["usd"]}
P["activity"] = {"total_accounts": st["accounts"], "total_transactions": st["transactions"], "epoch": st["epoch"], "blocks": st["blocks"], "shards": 3}
P["top_accounts"] = [{"address": x["address"], "balance_egld": int(x["balance"]) / E, "label": LM.get(x["address"], "Unknown")} for x in c["top_accounts"][:100]]
P["top_tokens_by_holders"] = [{"identifier": t["identifier"], "name": t.get("name"), "holders": t["accounts"], "price_usd": t.get("price"), "supply_raw": t.get("supply"), "decimals": t.get("decimals")} for t in c["tokens_holders"][:25]]
P["top_tokens_by_volume"] = [{"identifier": t["identifier"], "name": t.get("name"), "transactions": t.get("transactions"), "holders": t.get("accounts")} for t in c["tokens_txs"][:25]]
P["newly_issued_tokens"] = R["token_activity"]["newly_issued"]
P["staking_providers"] = [{"provider": p.get("identity") or p["provider"], "name": p.get("identity") or p["provider"], "address": p["provider"], "locked_egld": float(p.get("locked", 0) or 0) / E,
  "num_delegators": p.get("numUsers"), "apr": p.get("apr"), "fee": p.get("serviceFee"), "num_nodes": p.get("numNodes")} for p in c["providers"]]
P["staking_concentration"] = {"hhi": D["hhi"], "top_5_share_pct": D["top5"], "top_10_share_pct": D["top10"], "total_locked_egld": R["staking_intelligence"]["summary"]["total_delegated_egld"]}
P["exchange_balances"] = {k: pv["exchange_balances"][k] + D["chg"][k] for k in pv["exchange_balances"]}
P["_exchange_balances_note"] = "'Binance.com' includes hot wallet 2 (erd1ts0g6r0h), erd1sdslvl, erd1ylwusw (2.13M reserve) and the 300K cold wallet."
P["defi_tvl"] = D["TVL"]
P["lsd_supply"] = {t: float(c["tvl_tokens"][t].get("supply") or 0) for t in ["SEGLD-3ad2d0", "XEGLD-e413ed", "SWTAO-356a25", "USH-111e09"]}
P["lsd_staked_egld_emerging"] = D["EMERG"]
def stable(k): s = c[k]; return (int(s["minted"]) - int(s["burnt"])) / 10 ** s["decimals"]
P["stablecoin_supply"] = {"USDC-c76f1f": float(round(stable("stable_USDC-c76f1f"))), "USDT-f8c08c": float(round(stable("stable_USDT-f8c08c")))}
x = R["token_activity"]["xexchange"]
P["xexchange"] = {"volume_24h_usd": D["vol24"], "total_pairs": x["total_pairs"], "mex_price_usd": x["mex_price_usd"], "mex_market_cap_usd": x["mex_market_cap_usd"],
  "mex_price_source": "xExchange /mex/economics", "volume_status": x["volume_status"], "pool_tvl_usd": D["tvl"], "turnover_ratio_pct": x["turnover_ratio_pct"],
  "volume_24h_egld": D["vol24"] / D["price"], "pool_tvl_egld": D["tvl"] / D["price"]}
P["binance_rail"] = {"hot_wallet": H2["address"], "old_hot_wallet": "erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets", "first_tx_utc": "2026-11-09 18:29",
  "deposits_7d": H2["deposits_egld"], "withdrawals_7d": H2["withdrawals_egld"], "deposit_sweeps_7d": H2["deposits_n"], "withdrawal_txs_7d": H2["withdrawals_n"], "state": "open",
  "reserve_wallet": A["ylw"]["address"], "reserve_balance_egld": A["ylw"]["info"]["balance_egld"], "withdrawal_pause_days": ["2026-11-18", "2026-11-19"],
  "rail_window_end_ts": c["_period"].get("rail_window_end_ts")}
wa = [w for w in pv["watch_addresses"]]
for w in wa:
    w["weeks_tracked"] = w.get("weeks_tracked", 0) + 1
    if w["address"] in c["accounts"]: w["balance_egld"] = int(c["accounts"][w["address"]]["info"]["balance"]) / E
    if w["address"] == A["rlq"]["address"]: w["balance_egld"] = A["rlq"]["info"]["balance_egld"]; w["label"] = "Binance depositor whale - long-time Binance customer (first tx 2024-10-29); no send in run #38"
    if w["address"] == H2["address"]: w["balance_egld"] = H2["info"]["balance_egld"]; w["label"] = "Binance.com hot wallet 2 - net outflow 104,559 in run #38; binance-outflow-persists"
have = {w["address"] for w in wa}
YLW = A["ylw"]["address"]
new_w = [{"address": YLW, "label": "Binance 2.13M reserve wallet - refills hot wallet 2 (50,000 on Nov 20)", "balance_egld": A["ylw"]["info"]["balance_egld"], "weeks_tracked": 1, "first_seen": RD}]
P["watch_addresses"] = [w for w in new_w if w["address"] not in have] + wa
P["_run38_note"] = "SWTAO/HUSDC/HWTAO prices derived (API null; TAO from CoinGecko, API WTAO $462 rejected). defi_tvl on a one-week basis from token market caps."
json.dump(P, open(f"{REPO}/data/previous.json", "w"))

# ---------------------------------------------------------------- methodology
BEGIN, END = "<!-- run38:begin -->", "<!-- run38:end -->"
SECTION = f"""{BEGIN}
### A FEED PRICE CAN BE A POOL PRICE - CHECK IT AGAINST AN EXTERNAL REFERENCE (run #38, 2026-11-23)

On Nov 23 /tokens returned null price for SWTAO-356a25, HUSDC-d80042 and HWTAO-2e9136, and /tokens/WTAO-4f5363 reported TAO at $462 while CoinGecko had $192. Applying the run #11 ratio fallback with the API's WTAO price would have printed Hatom Liquid Staking +25.8% in a -10% week. Rule: the ratio fallback's base price comes from CoinGecko for any asset with a CoinGecko listing; a chain price more than 2x the external reference is rejected and logged in dataapi_refetch_log. HUSDC uses USDC (about $1) as its base.

### SIZE BORROWS FROM THE CALL'S RESULTS (run #38, 2026-11-23) - closes run #37 rec #4

trace_run38.py section 22 now fetches /transactions/{{hash}} for every borrow and sums the smart-contract results paid to the borrower. Run #38: 94 borrows by 15 wallets took 52,499 EGLD; 70 loops (45,645 EGLD) by 4 wallets. Repayments are not sized yet; until they are, net leverage change is read from the money market's idle EGLD (55,973 -> 15,477).

### A BACKLOG TEST NEEDS A DAILY VIEW (run #38, 2026-11-23)

binance-backlog-fades resolved against: withdrawals held at ~205K and net outflow rose to 104,559. Inside the window the hot wallet paid nothing on Nov 18-19 (with ~52K on hand) and 114,410 on Nov 20 after a 50,000 reserve top-up. A weekly total cannot separate a queue from a standing exit; read per-day withdrawals next to reserve top-ups before interpreting any exchange's weekly net.
{END}
"""
row = ("| 38 | 2026-11-23 | **BINANCE'S REOPENED RAIL IS AN EXIT: NET 104,559 EGLD OUT, WITH A TWO-DAY WITHDRAWAL PAUSE.** ~7-day window. EGLD -10.1% to $2.32 vs BTC -4.7% (-5.4pp); new low for the series, below the $2.55 June-August floor. "
 "(1) Hot wallet 2: 205,572 withdrawn, 101,013 deposited; no withdrawals Nov 18-19, 114,410 on Nov 20 after a 50,000 top-up from the 2.13M reserve. binance-backlog-fades AGAINST; binance-reserve-stays AS PREDICTED. "
 "(2) 108,004 of the withdrawals reached Bybit, Gate.io and Coinbase within one hop; tracked books -37,011. (3) Hatom: 70 of 94 borrows were loops (45,645 EGLD, first decoded sizes) by 4 wallets; idle EGLD 55,973 -> 15,477; 0 liquidations; USH -8.2%. "
 "(4) Upbit extended its caution to Dec 14-18 (premium 18.1%); test re-dated once. (5) Staked +2,307; delegators -49 (11th straight); USDC -2.9% (net bridge unwrap 242,835); MEX z -4.27. "
 "(6) API nulls on three Hatom tokens and a $462 WTAO pool price; derived with CoinGecko TAO. erd1rlqdj67qxp first tx is 2024-10-29 (corrected). "
 "Rules: external price check on fallback bases; borrow sizes from results; daily view before reading an exchange's weekly net. "
 "Tests: 2 resolved (1 as predicted, 1 against), 2 registered (binance-outflow-persists, hatom-loops-unwind-without-liquidation). 6/6 prior action items completed. |")
m = open(f"{REPO}/data/methodology.md").read()
if BEGIN in m:
    m = m[:m.index(BEGIN)] + m[m.index(END) + len(END):].lstrip("\n")
m = "\n".join(l for l in m.split("\n") if not l.startswith("| 38 | 2026-11-23 |"))
head, tail = m.split("## Evolution Log", 1)
m = head.rstrip("\n") + "\n\n" + SECTION + "\n## Evolution Log" + tail.rstrip("\n") + "\n" + row + "\n"
open(f"{REPO}/data/methodology.md", "w").write(m)

# ---------------------------------------------------------------- learnings
L["runs"] = [x for x in L["runs"] if x["date"] < RD]
prev = L["runs"][-1]; rb = copy.deepcopy(prev["running_baselines"])
def app(k, v):
    if isinstance(rb.get(k), list): rb[k].append(v)
for k in ("egld_price_usd", "dex_volume_24h_usd", "staked_egld", "mex_price_usd", "total_delegators", "staked_ratio", "exchange_net_flow_egld", "usdt_supply", "usdc_supply",
          "korea_premium_pct", "binance_staking_custody_egld", "binance_native_rail_egld_7d", "withdraw_egld_returned_7d"):
    app(k, B[k])
app("dex_volume_24h_egld", round(B["dex_volume_24h_egld"]))
app("dex_turnover_ratio_pct", round(R["token_activity"]["xexchange"]["turnover_ratio_pct"], 3))
app("reward_compound_pct", round(R["staking_intelligence"]["reward_behavior"]["compound_pct_at_function_level"], 2))
app("delegation_total_locked_egld", round(R["staking_intelligence"]["summary"]["total_delegated_egld"]))
app("unbonding_queue_undelegated_egld_7d", round(c["undelegated_this_week_total_egld"]))
app("pre_committed_tests_resolved", 2); app("pre_committed_test_hit_rate_pct", 50.0)
app("pre_committed_tests_open", sum(1 for t in R["pre_committed_tests"] if t["status"] == "open"))
app("binance_entity_egld", round(sum(P["exchange_balances"][k] for k in ("Binance.com", "Binance Staking"))))
rb["hatom_borrow_loops"]["run38"] = T["hatom_borrow_join"]["by_pattern"]
rb["hatom_borrowed_egld_by_pattern"] = {"run38": {k: round(v) for k, v in T["hatom_borrow_join"]["borrowed_egld_by_pattern"].items()}}
mmc = next(int(x["balance"]) / E for x in c["top_accounts"] if x["address"].startswith("erd1qqqqqqqqqqqqqpgq35qkf34a8svu4r2zmfzuztmeltqclapv78ss5jleq3"))
rb["hatom_egld_mm_idle_egld"] = [55973, round(mmc)]
app("usdc_bridge_net_unwrap", round(T["usdc_bridge"]["unwrap_usdc"] - T["usdc_bridge"]["wrap_usdc"]))
rb["binance_reserve_egld"] = [2184313, round(A["ylw"]["info"]["balance_egld"])]
ml = R["meta_learning"]
entry = {"date": RD, "run_number": RUN,
 "data_quality": {"endpoints_that_worked": ml.get("endpoints_that_worked", []), "endpoints_that_failed": ml["endpoints_that_failed"], "api_quirks_discovered": ml["api_quirks"]},
 "analysis_insights": {
   "what_worked": ["Per-day hot-wallet flow next to reserve top-ups exposed the Nov 18-19 withdrawal pause and the Nov 20 release that a weekly total hides",
                   "Hot wallet 2 in the collector and Binance wallets in the rails internal set: venue figures match entity netting without ad-hoc overrides",
                   "Decoding borrow results sized the Hatom loops (45,645 EGLD) for the first time",
                   "Checking the WTAO feed against CoinGecko stopped a +25.8% phantom Hatom Liquid Staking reading"],
   "what_needs_improvement": ml["data_gaps"] + ["Repayments are still unsized, so net leverage change rests on the money market's idle balance."],
   "surprising_findings": ["Binance's net outflow more than tripled (104,559) with withdrawals flat: deposits fell, not withdrawals rose.",
                           "Binance paid no EGLD withdrawals on Nov 18-19 while holding ~52K and taking deposits, then paid 114,410 on Nov 20.",
                           "Hatom leverage loops went from 15 to 70 in a -10% week; idle EGLD in the market fell 72%.",
                           "The chain's TAO price ($462) is 2.4x the market; three Hatom tokens returned null prices the same day.",
                           "erd1rlqdj67qxp is a 2024 Binance customer, not a new whale."]},
 "methodology_changes": ml["methodology_changes"],
 "new_addresses_discovered": ml["new_addresses_discovered_detail"],
 "action_items_completed": ml["action_items_completed_detail"],
 "running_baselines": rb,
 "dashboard_feature_suggestions": ml["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup": ml["dashboard_suggestions_followup"],
 "self_assessment": {"most_valuable_insight": ml["most_valuable_insight"], "recommendations_completed": "6 of 6", "next_week_2x_better": ml["self_assessment"]["what_would_make_it_2x_better"]},
 "recommendations_for_next_run": ml["recommendations_for_next_run"]}
L["runs"].append(entry)
json.dump(L, open(f"{REPO}/data/learnings.json", "w"), indent=1)
print("updated previous/methodology/learnings; runs:", len(L["runs"]), "| archived:", cur_prev["snapshot_date"], "| exch", {k: round(v) for k, v in P["exchange_balances"].items()})
