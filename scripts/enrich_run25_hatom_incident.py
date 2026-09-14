#!/usr/bin/env python3
"""Run #25: reconstruct the Hatom MEX money market incident (2026-09-13) from chain data.

Context: Hatom's 2026-09-14 21:03 UTC statement (x.com/HatomProtocol/status/2099605029715906573)
calls it a "MEX money market incident", says user funds are safe, the incident is contained,
a recovery plan will unwind the incident-driven activity without user losses or bad debt, and
the MEX money market plus the MEX/EGLD, MEX/USH and MEX/USDC pairs stay paused until about
Wednesday. It does not state a cause; a detailed report is promised.

This script records only what the chain shows: the three pause calls, the Hatom MEX market's
call timeline, and the two wallets that deposited MEX as collateral during the spike and
borrowed EGLD against it (with the MEX bought through xExchange's composeTasks contract).
Output: data/collected/2026-09-14.json key dash_hatom_incident.
"""
import json, time, urllib.request, urllib.parse
REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
SNAP = f"{REPO}/data/collected/2026-09-14.json"
API = "https://api.multiversx.com"
A = 1789257600  # 2026-09-13 00:00 UTC
OWNER = "erd1ss6u80ruas2phpmr82r42xnkd6rxy40g9jl69frppl4qez9w2jpsqj8x97"
MEX_MM = "erd1qqqqqqqqqqqqqpgq2rnjnp543m5d8fac8v2ltkr5w2quh0v978ssswj939"
EGLD_MM = "erd1qqqqqqqqqqqqqpgq35qkf34a8svu4r2zmfzuztmeltqclapv78ss5jleq3"
COMPOSE = "erd1qqqqqqqqqqqqqpgqsytkvnexypp7argk02l0rasnj57sxa542jpshkl7df"
WALLETS = {"A": "erd10fe5lv5vwslmua46zgx9vfy79575al3cy2z6t26j94flqymccdpqz0fuqq",
           "B": "erd1fjcgt8g02ejvhqc5hye8k0zqws2j5g4mw3vxvyy38tv9llpkwt3q428cuk"}

def g(path, params=None):
    u = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    for a in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "intel-agent/25-incident"}), timeout=40) as r:
                return json.loads(r.read())
        except Exception as e:
            if a == 5: raise
            time.sleep(1.5 * (a + 1))

def paged(addr, **p):
    out, frm = [], 0
    while True:
        b = g(f"/accounts/{addr}/transactions", {"size": 50, "from": frm, "order": "asc", **p})
        out += b; frm += 50; time.sleep(0.3)
        if len(b) < 50: return out

pauses = []
for t in g(f"/accounts/{OWNER}/transactions", {"size": 20, "after": A, "order": "asc", "function": "pause"}):
    toks = [x["identifier"] for x in g(f"/accounts/{t['receiver']}/tokens", {"size": 5}) if x.get("type") == "FungibleESDT"]
    lp = next((x for x in toks if x.startswith(("EGLDMEX", "MEXUSH", "MEXUSDC"))), None)
    name = {"EGLDMEX-0be9e5": "MEX/WEGLD", "MEXUSH-179240": "MEX/USH", "MEXUSDC-a57860": "MEX/USDC"}.get(lp, lp)
    pauses.append({"ts": t["timestamp"], "pair": name, "address": t["receiver"], "tx": t["txHash"], "status": t["status"]})
    time.sleep(0.3)

mm = paged(MEX_MM, after=A, before=A + 2 * 86400)
mm_calls = [{"ts": t["timestamp"], "fn": t.get("function"), "sender": t["sender"], "status": t["status"]} for t in mm]

wallets = {}
for k, w in WALLETS.items():
    txs = paged(w, after=A, sender=w)
    deposits, borrows, buys = [], [], []
    for t in txs:
        if t.get("status") != "success": continue
        f = t.get("function")
        if f == "mintAndEnterMarket" and t["receiver"] == MEX_MM:
            d = g(f"/transactions/{t['txHash']}"); time.sleep(0.25)
            mex = sum(int(o["value"]) for o in d.get("operations") or [] if o.get("identifier") == "MEX-455c57" and o.get("receiver") == MEX_MM) / 1e18
            deposits.append({"ts": t["timestamp"], "mex": mex})
        elif f == "borrow" and t["receiver"] == EGLD_MM:
            d = g(f"/transactions/{t['txHash']}"); time.sleep(0.25)
            egld = sum(int(r.get("value", "0")) for r in d.get("results") or [] if r.get("receiver") == w) / 1e18
            borrows.append({"ts": t["timestamp"], "egld": egld})
        elif f == "composeTasks" and t["receiver"] == COMPOSE:
            d = g(f"/transactions/{t['txHash']}"); time.sleep(0.25)
            mex = sum(int(o["value"]) for o in d.get("operations") or [] if o.get("identifier") == "MEX-455c57" and o.get("receiver") == w) / 1e18
            buys.append({"ts": t["timestamp"], "egld_in": int(t.get("value", "0")) / 1e18, "mex_out": mex})
    wallets[k] = {"address": w, "deposits": deposits, "borrows": borrows, "xexchange_buys": buys,
                  "mex_deposited": sum(x["mex"] for x in deposits), "egld_borrowed": sum(x["egld"] for x in borrows),
                  "egld_spent_buying_mex": sum(x["egld_in"] for x in buys), "mex_bought": sum(x["mex_out"] for x in buys)}
    print(k, f"deposited {wallets[k]['mex_deposited']/1e9:.1f}B MEX, borrowed {wallets[k]['egld_borrowed']:,.0f} EGLD, "
             f"bought {wallets[k]['mex_bought']/1e9:.1f}B MEX for {wallets[k]['egld_spent_buying_mex']:,.0f} EGLD")

D = json.load(open(SNAP))
D["dash_hatom_incident"] = {
    "statement": {"source": "https://x.com/HatomProtocol/status/2099605029715906573", "author": "Hatom Labs (@HatomProtocol)",
                  "published_utc": "2026-09-14T21:03:42Z",
                  "summary": ("Calls it a MEX money market incident. User funds remain safe and the incident is contained after a "
                              "coordinated response with the xExchange team. A recovery plan, built with independent MultiversX DeFi "
                              "experts, is designed to unwind the incident-driven activity without losses to users or bad debt for the "
                              "protocol. The MEX money market and the MEX/EGLD, MEX/USH and MEX/USDC pairs remain paused and are expected "
                              "to resume by Wednesday after recovery and safety checks. No user action required. A detailed incident "
                              "report is promised; the statement gives no cause."),
                  "resume_expected": "by Wednesday 2026-09-16 (stated)"},
    "pauses": pauses, "mex_money_market_calls": mm_calls, "wallets": wallets,
    "liquidations_on_mex_market": sum(1 for c in mm_calls if c["fn"] == "liquidateBorrow"),
    "mex_market_last_call_ts": max(c["ts"] for c in mm_calls) if mm_calls else None,
}
json.dump(D, open(SNAP, "w"))
print("pauses", [(p["pair"], p["ts"]) for p in pauses], "mm calls", len(mm_calls))
