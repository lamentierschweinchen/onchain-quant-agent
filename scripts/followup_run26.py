#!/usr/bin/env python3
"""Run #26 follow-up pass (run sequentially AFTER collect_run26.py, never alongside).

(1) Recover any paged query the main pass recorded as an error (run #23 rule).
(2) WITHDRAW AMOUNTS (run #25 rec #5): decode the EGLD returned by every
    `withdraw` call found in the all-provider scan, from the transaction's
    smart-contract results. Turns the run #25 "matured queue" timing argument
    into a measured figure.
(3) ADDRESS POISONING: two wallets whose first/last characters mimic the OTC
    desks spray 0.0001 EGLD at the pipeline's routers. Measure how many routers
    they touched, and whether any value above dust was ever sent TO them.
(4) Dashboard series: CoinGecko EGLD 90d (delivery-share backfill), MEX hourly
    14d (incident recovery), and the MEX/WEGLD pair's own call history since
    Sep 13 (pause -> resume timeline).
Writes back into data/collected/2026-09-21.json.
"""
import json, time, urllib.request, urllib.parse
from collections import Counter

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD = "2026-09-21"
SNAP = f"{REPO}/data/collected/{RD}.json"
API = "https://api.multiversx.com"
D = json.load(open(SNAP))
ERRORS = []


def get(url, retries=7):
    if not url.startswith("http"):
        url = API + url
    delay = 1.5
    for a in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "intel-agent/26-followup"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if a == retries:
                ERRORS.append({"url": url, "error": str(e)})
                return {"__error__": str(e)}
            time.sleep(delay)
            delay = min(delay * 2, 30.0)


def q(path, **params):
    return get(path + "?" + urllib.parse.urlencode(params))


def paged(addr, after, before=None, direction="sender", max_pages=40):
    out, frm = [], 0
    for _ in range(max_pages):
        p = {"size": 50, "from": frm, "after": after, "order": "desc", "status": "success", direction: addr}
        if before:
            p["before"] = before
        b = q(f"/accounts/{addr}/transactions", **p)
        time.sleep(0.25)
        if isinstance(b, dict):
            return out, b.get("__error__")
        out += b
        if len(b) < 50:
            return out, None
        frm += 50
    return out, "page-cap"


# (1) recover main-pass paged errors ------------------------------------------
recovered = []
for e in D.get("_paged_errors") or []:
    per = D["_period"]
    txs, err = paged(e["address"], per["window_start_ts"], direction=e["direction"])
    recovered.append({**e, "recovered_txs": len(txs), "recovery_error": err})
    print(f"[recover] {e['address'][:14]} {e['direction']} {e['tag']}: {len(txs)} txs err={err}")
D["followup_recovered_errors"] = recovered

# (2) withdraw amounts ----------------------------------------------------------
legs = D.get("withdraw_legs") or []
print(f"[withdraw] decoding {len(legs)} withdraw calls")
decoded = []
for i, leg in enumerate(legs):
    tx = get(f"/transactions/{leg['txHash']}?withScResults=true")
    time.sleep(0.2)
    amt = None
    if isinstance(tx, dict) and "__error__" not in tx:
        amt = 0.0
        for r in tx.get("results") or []:
            if r.get("receiver") == leg["sender"]:
                try:
                    amt += int(r.get("value", "0")) / 1e18
                except Exception:
                    pass
        if amt == 0.0:
            for o in tx.get("operations") or []:
                if o.get("action") == "transfer" and o.get("type") == "egld" and o.get("receiver") == leg["sender"]:
                    amt += int(o.get("value", "0")) / 1e18
    decoded.append({**leg, "egld_returned": amt})
    if i % 100 == 0:
        print(f"   {i}/{len(legs)}")
tot = sum(x["egld_returned"] or 0 for x in decoded)
by_prov = Counter()
for x in decoded:
    by_prov[x["identity"] or x["provider"]] += x["egld_returned"] or 0
D["withdraw_decoded"] = {
    "calls": len(decoded),
    "decoded_ok": sum(1 for x in decoded if x["egld_returned"] is not None),
    "egld_returned_total": tot,
    "by_provider_top": by_prov.most_common(12),
    "largest": sorted(decoded, key=lambda x: -(x["egld_returned"] or 0))[:15],
}
print(f"[withdraw] {tot:,.0f} EGLD returned across {len(decoded)} calls")

# (3) address poisoning ----------------------------------------------------------
POISON = {
    "erd1z7wyqlr64qhr5k3wu9qa4d6c6wszxx8s5n9qc7067ds9f9pv3stqppm63r":
        "mimics OTC Distribution Wallet erd1z7fnqf...nm63r",
    "erd1v6k4dxe72tg0d43pvxrhq0zhlg0z5p0r4jeww2wtazv8kjn0cugsryxnk5":
        "mimics UPbit OTC Desk erd1v6x9egd...hcxnk5",
}
start30 = D["_period"]["window_start_ts"] - 23 * 86400
pz = {}
for a, note in POISON.items():
    info = get(f"/accounts/{a}")
    time.sleep(0.25)
    out, oerr = paged(a, start30, direction="sender", max_pages=40)
    inn, ierr = paged(a, start30, direction="receiver", max_pages=20)
    targets = Counter(t["receiver"] for t in out)
    real_in = [{"from": t["sender"], "egld": int(t.get("value", "0")) / 1e18, "ts": t["timestamp"],
                "hash": t["txHash"]} for t in inn if int(t.get("value", "0")) > 10**16]
    pz[a] = {"note": note,
             "nonce": info.get("nonce") if isinstance(info, dict) else None,
             "balance_egld": int(info.get("balance", "0")) / 1e18 if isinstance(info, dict) and "balance" in info else None,
             "created_ts": info.get("timestamp") if isinstance(info, dict) else None,
             "dust_txs_30d": len(out), "distinct_targets_30d": len(targets),
             "outbound_error": oerr, "inbound_error": ierr,
             "inbound_above_0_01_egld": real_in,
             "inbound_total_egld": sum(int(t.get("value", "0")) for t in inn) / 1e18,
             "funders": Counter(t["sender"] for t in inn).most_common(5)}
    print(f"[poison] {a[:14]}..{a[-6:]}: nonce {pz[a]['nonce']}, {len(out)} dust txs to {len(targets)} targets, "
          f"{len(real_in)} inbound > 0.01 EGLD")
D["address_poisoning"] = pz

# (4) dashboard series -----------------------------------------------------------
D["dash_cg_egld_90d"] = get("https://api.coingecko.com/api/v3/coins/elrond-erd-2/market_chart?vs_currency=usd&days=90&interval=daily")
time.sleep(2)
D["dash_cg_mex_hourly"] = get("https://api.coingecko.com/api/v3/coins/maiar-dex/market_chart?vs_currency=usd&days=14")
time.sleep(1)
PAIR = "erd1qqqqqqqqqqqqqpgqa0fsfshnff4n76jhcye6k7uvd7qacsq42jpsp6shh2"
ptx = []
frm = 0
while True:
    b = q(f"/accounts/{PAIR}/transactions", size=50, **{"from": frm}, after=1789257600, order="desc")
    if not isinstance(b, list):
        print("pair page error", b)
        break
    ptx += [{"ts": t["timestamp"], "fn": t.get("function"), "status": t.get("status"), "sender": t.get("sender")} for t in b]
    if len(b) < 50 or frm > 3000:
        break
    frm += 50
    time.sleep(0.3)
D["dash_mex_pair_txs"] = ptx
print("pair txs since Sep 13:", len(ptx), Counter((t["fn"], t["status"]) for t in ptx).most_common(8))

D["_followup_errors"] = ERRORS
json.dump(D, open(SNAP, "w"))
print("followup written; errors:", len(ERRORS))
