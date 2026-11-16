#!/usr/bin/env python3
"""Run #37: refresh previous.json, methodology (new rules + Evolution Log row) and append the learnings entry.
known-addresses.json was updated before assembly (hot wallet 2, depositor whale, two lookalikes). Idempotent: re-running
replaces this run's learnings entry and methodology block instead of appending twice."""
import json, copy, sys
sys.path.insert(0, "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/scripts")
from report_template import archive_previous, load_previous
REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"; RD = "2026-11-16"; RUN = 37
S = "/private/tmp/claude-501/-Users-ls-Documents-MultiversX-projects-onchain-quant-agent/dddf9200-b0cf-4286-98dd-088a97a7e141/scratchpad"
c = json.load(open(f"{REPO}/data/collected/{RD}.json")); R = json.load(open(f"{REPO}/reports/{RD}.json"))
cur_prev = json.load(open(f"{REPO}/data/previous.json"))
if cur_prev["snapshot_date"] < RD: archive_previous(cur_prev)   # keep the pre-run snapshot so assemblers can be re-run safely
pv = load_previous(RD)
kn = json.load(open(f"{REPO}/data/known-addresses.json")); L = json.load(open(f"{REPO}/data/learnings.json"))
D = json.load(open(f"{S}/digest37.json")); B = json.load(open(f"{S}/baselines37.json"))
A = c["run37_adhoc"]; NH = A["new_hot"]; T = c["run37_traces"]
LM = {}
for s, e in kn.items():
    if isinstance(e, dict):
        for a, m in e.items():
            if isinstance(m, dict) and a.startswith("erd1"): LM[a] = m.get("name")
eco = c["economics"]; st = c["stats"]; E = 1e18
P = copy.deepcopy(pv); P.pop("_run36_note", None)
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
P["_exchange_balances_note"] = "From run #37 'Binance.com' includes hot wallet 2 (erd1ts0g6r0h, 70,532 at run #37) next to erd1sdslvl, erd1ylwusw and the 300K cold wallet."
P["defi_tvl"] = D["TVL"]
P["lsd_supply"] = {t: float(c["tvl_tokens"][t].get("supply") or 0) for t in ["SEGLD-3ad2d0", "XEGLD-e413ed", "SWTAO-356a25", "USH-111e09"]}
P["lsd_staked_egld_emerging"] = D["EMERG"]
def stable(k): s = c[k]; return (int(s["minted"]) - int(s["burnt"])) / 10 ** s["decimals"]
P["stablecoin_supply"] = {"USDC-c76f1f": float(round(stable("stable_USDC-c76f1f"))), "USDT-f8c08c": float(round(stable("stable_USDT-f8c08c")))}
x = R["token_activity"]["xexchange"]
P["xexchange"] = {"volume_24h_usd": D["vol24"], "total_pairs": x["total_pairs"], "mex_price_usd": x["mex_price_usd"], "mex_market_cap_usd": x["mex_market_cap_usd"],
  "mex_price_source": "xExchange /mex/economics", "volume_status": x["volume_status"], "pool_tvl_usd": D["tvl"], "turnover_ratio_pct": x["turnover_ratio_pct"],
  "volume_24h_egld": D["vol24"] / D["price"], "pool_tvl_egld": D["tvl"] / D["price"]}
P["binance_rail"] = {"hot_wallet": NH["address"], "old_hot_wallet": "erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets", "first_tx_utc": "2026-11-09 18:29",
  "deposits_7d": NH["external_in_egld_window"], "withdrawals_7d": NH["out_egld_window"], "deposit_sweeps_7d": NH["external_in_txs"], "withdrawal_txs_7d": NH["out_n_window"], "state": "open",
  "rail_window_end_ts": NH["info"] and c["_period"].get("rail_window_end_ts")}
wa = [w for w in pv["watch_addresses"]]
have = {w["address"] for w in wa}
for w in wa:
    w["weeks_tracked"] = w.get("weeks_tracked", 0) + 1
    if w["address"] in c["accounts"]: w["balance_egld"] = int(c["accounts"][w["address"]]["info"]["balance"]) / E
RLQ = next(a for a in A["unlabelled_movers"] if a.startswith("erd1rlqdj67qxp"))
new_w = [
 {"address": NH["address"], "label": "Binance.com hot wallet 2 - new native rail since Nov 9 18:29 UTC; binance-backlog-fades", "balance_egld": NH["info"]["balance_egld"], "weeks_tracked": 1, "first_seen": RD},
 {"address": RLQ, "label": "Binance depositor whale - 43,586 to Binance in two clips (Nov 11, Nov 16); watch for a third", "balance_egld": A["unlabelled_movers"][RLQ]["balance_egld"], "weeks_tracked": 1, "first_seen": RD}]
P["watch_addresses"] = [w for w in new_w if w["address"] not in have] + wa
P["_run37_note"] = "Binance moved 2,264,611 EGLD custody -> erd1ylwusw on Nov 12 (internal). defi_tvl on a one-week basis from token market caps; otc series not refreshed."
json.dump(P, open(f"{REPO}/data/previous.json", "w"))

# ---------------------------------------------------------------- methodology
BEGIN, END = "<!-- run37:begin -->", "<!-- run37:end -->"
SECTION = f"""{BEGIN}
### A REOPENED RAIL CAN SIT ON A WALLET NOBODY TRACKS - FOLLOW CUSTODY'S OUTBOUND (run #37, 2026-11-16)

Run #36 read Binance's zero flow correctly as a dark rail. Run #37's tracked Binance wallets read zero customer flow again, yet the rail had been live for a week on a new hot wallet (erd1ts0g6r0h, first transaction Nov 9 18:29 UTC): 1,592 withdrawals (204,493 EGLD) and 396 deposit sweeps (174,725 EGLD). It was found only because the custody wallet and a tagged Binance.com wallet sent it 100,300 EGLD. Rule: when every tracked wallet of an exchange is silent, list the outbound of its custody and cold wallets and profile each unknown receiver (transaction count, distinct receivers, external senders) before reporting the rail as dark. A receiver funded by the exchange with hundreds of small fan-out transfers is the new hot wallet. The explorer tag lags (none after a week); do not wait for it.

### NET AN EXCHANGE'S OWN WALLET MOVES AT ENTITY LEVEL, IN BOTH DIRECTIONS (run #37, 2026-11-16)

On Nov 12 Binance Staking custody sent 2,264,611 EGLD to Binance.com wallet erd1ylwusw (custody now exactly 2,000,000). Per wallet that prints -2.28M and +2.25M; the entity figure is -29,768, which equals customer net flow at the hot wallet. Run #30's rule covered hot -> custody; this is custody -> exchange wallet, and the assembler now treats any transfer between two Binance-labelled wallets as internal. The move is still a finding (7.3% of supply relabelled from staking reserve to exchange inventory), but it is not a flow.

### A VENUE'S NET INFLOW CAN BE ANOTHER VENUE'S WITHDRAWALS (run #37, 2026-11-16)

Tracked exchanges gained 36,358 EGLD, the first net inflow in three windows. 76,720 EGLD of the Bybit and Coinbase gain came from Binance's new hot wallet within one hop (via erd1tx933j8r and two routers). Before reading aggregate net flow as supply arriving, trace the top depositors of each gaining venue one hop back; relocation between venues nets to zero for the market.

### LABEL-PREFIX ROLL-UPS NEED A CATEGORY CHECK (run #37, 2026-11-16)

The venue balance roll-up matches labels by prefix. Run #36 added the watch entry 'KuCoin round-trip whale ...', and in run #37 its 168,358 EGLD was summed into KuCoin's book (+173K phantom inflow, caught in the stage-1 digest). Roll-ups now skip that wallet; any new watch label that begins with a venue name must not be an exchange-category entry.

### THE >5% NEW-ACCOUNT AUDIT RULE HAS A CONSERVATION BRANCH (run #37, 2026-11-16)

audit_report.py check 9 (run #26) fails any new top account above 5% of supply. erd1ylwusw tripped it. The rule now accepts a new account when at least 95% of its balance arrived inside the window from wallets that were already top accounts last week (read from the snapshot's own transactions), and reports it as a warning. A minted balance, the case the rule exists for, still fails.

### JOIN HATOM BORROWS TO THE BORROWER'S NEXT 30 MINUTES (run #37, 2026-11-16) - closes a recommendation carried three runs

trace_run37.py section 22: every borrow call on the EGLD money market is joined to the same wallet's next transactions and classed loop (swap or stake, then supply), swap only, re-supply, stake only, or none. Run #37: 51 borrows by 12 wallets; 15 loops by 3 wallets, 15 swap only, 5 re-supply, 3 stake, 13 none. Amounts are not decoded yet (they sit in smart-contract results). Rail liveness (section 19) and the OTC vault's daily legs (section 21) are part of the same pass.
{END}
"""
row = ("| 37 | 2026-11-16 | **BINANCE REOPENED ON A NEW HOT WALLET AND MOVED 2.26M EGLD OUT OF STAKING CUSTODY.** 6.95-day window. EGLD -14.3% to $2.58 with BTC -13.9% (-0.4pp): a market drop. "
 "(1) Binance hot wallet 2 (erd1ts0g6r0h), first transaction Nov 9 18:29 UTC, 10.8 days after the old wallet went silent: 1,592 withdrawals (204,493 EGLD), 396 deposit sweeps (174,725); binance-rail-reopens AS PREDICTED. "
 "(2) Nov 12: custody -> Binance.com erd1ylwusw 2,264,611 (custody exactly 2,000,000); internal, Binance entity -29,768. "
 "(3) Tracked exchanges +36,358, first net inflow in three windows; 76,720 of Bybit/Coinbase inflow was Binance withdrawals relocating; top-100 wallet erd1rlqdj67qxp deposited 43,586 to Binance. KuCoin deposits resumed; MEXC withdraw-only a third window. "
 "(4) kucoin-whale-holds AS PREDICTED (168,358, no outbound). (5) Staked +86,327 in the drop; delegators -307 (10th straight decline). (6) USDC bridge: 301,421 unwrapped vs 16,986 wrapped; USDC supply -1.61%. "
 "(7) Hatom borrow join built: 15 of 51 borrows were loops by 3 wallets; idle EGLD -20,922; 0 liquidations. Korea premium 19.8%; Upbit decision window Nov 16-20 open, nothing announced. "
 "Rules: follow custody's outbound when an exchange reads dark; net internal moves both directions; trace gaining venues' depositors one hop; category-check prefix roll-ups; conservation branch in the >5% audit rule. "
 "Tests: 2 resolved (both as predicted), 2 registered (binance-backlog-fades, binance-reserve-stays). 7/7 prior action items completed. |")
m = open(f"{REPO}/data/methodology.md").read()
if BEGIN in m:
    m = m[:m.index(BEGIN)] + m[m.index(END) + len(END):].lstrip("\n")
m = "\n".join(l for l in m.split("\n") if not l.startswith("| 37 | 2026-11-16 |"))
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
app("pre_committed_tests_resolved", 2); app("pre_committed_test_hit_rate_pct", 100.0)
app("pre_committed_tests_open", sum(1 for t in R["pre_committed_tests"] if t["status"] == "open"))
rb["binance_entity_egld"] = [round(sum(pv["exchange_balances"][k] for k in ("Binance.com", "Binance Staking"))), round(sum(P["exchange_balances"][k] for k in ("Binance.com", "Binance Staking")))]
rb["hatom_borrow_loops"] = {"run37": T["hatom_borrow_join"]["by_pattern"]}
rb["usdc_bridge_net_unwrap"] = [round(99719.798369 - 40629.114809), round(T["usdc_bridge"]["unwrap_usdc"] - T["usdc_bridge"]["wrap_usdc"])]
ml = R["meta_learning"]
entry = {"date": RD, "run_number": RUN,
 "data_quality": {"endpoints_that_worked": ml.get("endpoints_that_worked", []), "endpoints_that_failed": ml["endpoints_that_failed"], "api_quirks_discovered": ml["api_quirks"]},
 "analysis_insights": {
   "what_worked": ["Following Binance custody's outbound to an unknown receiver and profiling it (1,611 transfers, 1,258 receivers) identified the new hot wallet",
                   "Entity netting turned -2.28M / +2.25M wallet rows into a -29,768 customer flow that matched the hot wallet's deposits minus withdrawals to the EGLD",
                   "One-hop back-trace of each gaining venue's top depositors (Bybit, Coinbase) showed 76,720 EGLD of 'inflow' was Binance withdrawals",
                   "blank_template + staleness gate: no carried values; two exact repeats were verified fresh and declared"],
   "what_needs_improvement": ml["data_gaps"] + ["The new hot wallet was profiled by an ad-hoc script; it must move into the collector and rails pass.",
                   "The invalid-state audit rule needed a conservation branch mid-run (added); the prefix roll-up bug reached the stage-1 digest before it was caught."],
   "surprising_findings": ["Binance's rail was not dark for a second week: it had reopened on an untracked wallet one hour after run #36's snapshot.",
                           "Binance cut its staking custody wallet to exactly 2,000,000 EGLD, moving 2,264,611 (7.3% of supply) to an exchange wallet.",
                           "38% of Binance's first-week withdrawals went to Coinbase and Bybit within one hop.",
                           "Staked EGLD rose 86,327 in a week the price fell 14%, while the delegator count fell for a tenth straight window.",
                           "A poisoning lookalike of the new Binance hot wallet appeared within a day of the wallet itself."]},
 "methodology_changes": ml["methodology_changes"] + ["audit_report.py check 9: a new top account above 5% of supply is accepted (warning) when >= 95% of it arrived in-window from last week's top accounts."],
 "new_addresses_discovered": ml["new_addresses_discovered_detail"],
 "action_items_completed": ml["action_items_completed_detail"],
 "running_baselines": rb,
 "dashboard_feature_suggestions": ml["dashboard_feature_suggestions"],
 "dashboard_suggestions_followup": ml["dashboard_suggestions_followup"],
 "self_assessment": {"most_valuable_insight": ml["most_valuable_insight"], "recommendations_completed": "7 of 7", "next_week_2x_better": ml["self_assessment"]["what_would_make_it_2x_better"]},
 "recommendations_for_next_run": ml["recommendations_for_next_run"]}
L["runs"].append(entry)
json.dump(L, open(f"{REPO}/data/learnings.json", "w"), indent=1)
print("updated previous/methodology/learnings; runs:", len(L["runs"]), "| archived:", cur_prev["snapshot_date"], "| exch", {k: round(v) for k, v in P["exchange_balances"].items()})
