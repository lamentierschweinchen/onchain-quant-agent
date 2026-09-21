#!/usr/bin/env python3
"""Run #26: persist the 2026-09-19 VM-exploit / chain-halt evidence into the snapshot.

What the chain shows (read from the API, which still serves the halted state):
  - wallet erd1kwvkch79...rvvjd2 (funded Sep 16 with ~17 EGLD from MEXC, Bybit and
    one other wallet) deployed a contract at 06:34 UTC on Sep 19 and ran 31
    deposit -> compound rounds with deposits doubling each round;
  - it ended holding 41.3M EGLD, its contract 25.6M - together ~2.2x the 30.8M
    total supply that /economics still reports;
  - between 07:24 and 07:27 UTC it sent 9.81M EGLD to 12 fresh wallets, which
    forwarded into Binance.com, KuCoin, MEXC, an unlabelled high-nonce wallet and
    the wallet this model labels Unknown Whale I;
  - the last block on every shard is 07:37-07:41 UTC Sep 19. No block since.
MultiversX's public statement calls it an attempted exploit of a VM-level
atomicity issue that produced invalid state changes; progression is paused, a
fix is being validated on a shadow fork, and a targeted recovery that preserves
legitimate state is being evaluated.

Writes data/collected/2026-09-21.json key `chain_halt_incident`.
"""
import json, time, urllib.request, urllib.parse
from collections import Counter

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
SNAP = f"{REPO}/data/collected/2026-09-21.json"
API = "https://api.multiversx.com"
W = "erd1kwvkch79edm9qtg3tlaylgm9yff04lr9vaszazuavxtqrffz6scqrvvjd2"
C = "erd1qqqqqqqqqqqqqpgqsqffm2ezs77zsu6cvc6nxd4v8qegne4v6scqke2kq9"


def g(url, retries=5):
    if not url.startswith("http"):
        url = API + url
    d = 1.5
    for a in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "intel-agent/26-halt"}), timeout=40) as r:
                return json.loads(r.read())
        except Exception as e:
            if a == retries - 1:
                return {"__error__": str(e)}
            time.sleep(d); d *= 2


kn = json.load(open(f"{REPO}/data/known-addresses.json"))
lab, cat = {}, {}
for s, e in kn.items():
    if isinstance(e, dict):
        for a, m in e.items():
            if isinstance(m, dict):
                lab[a] = m.get("name"); cat[a] = m.get("category")

D = json.load(open(SNAP))
H = {}
H["last_blocks"] = {}
for s in (0, 1, 2, 4294967295):
    b = g(f"/blocks?size=1&shard={s}")
    if isinstance(b, list) and b:
        H["last_blocks"][str(s)] = {"nonce": b[0]["nonce"], "timestamp": b[0]["timestamp"]}
    time.sleep(0.3)

txs, frm = [], 0
while True:
    b = g(f"/accounts/{W}/transactions?size=50&from={frm}&order=asc")
    if not isinstance(b, list):
        break
    txs += b
    if len(b) < 50:
        break
    frm += 50; time.sleep(0.3)
H["attacker"] = {"address": W, "account": g(f"/accounts/{W}"), "tx_count": len(txs),
                 "functions": dict(Counter((t.get("function") or "(transfer)") for t in txs)),
                 "funding": [{"from": t["sender"], "label": lab.get(t["sender"]), "egld": int(t["value"]) / 1e18,
                              "ts": t["timestamp"]} for t in txs if t["receiver"] == W and int(t["value"]) > 0],
                 "rounds": [{"ts": t["timestamp"], "fn": t.get("function"), "egld": int(t["value"]) / 1e18}
                            for t in txs if t["sender"] == W and t.get("function") in ("deposit", "compound")],
                 "first_ts": min(t["timestamp"] for t in txs) if txs else None,
                 "last_ts": max(t["timestamp"] for t in txs) if txs else None}
time.sleep(0.3)
H["contract"] = {"address": C, "account": g(f"/accounts/{C}")}

fan = []
to_venue = Counter()
for t in txs:
    if t["sender"] != W or int(t["value"]) <= 0 or t.get("function") not in (None, "transfer"):
        continue
    r = t["receiver"]; v = int(t["value"]) / 1e18
    if v < 1000:
        continue
    o = g(f"/accounts/{r}/transactions?size=20&sender={r}&order=asc"); time.sleep(0.3)
    i = g(f"/accounts/{r}"); time.sleep(0.2)
    fwd = [{"to": x["receiver"], "label": lab.get(x["receiver"]), "category": cat.get(x["receiver"]),
            "egld": int(x["value"]) / 1e18, "ts": x["timestamp"]}
           for x in (o if isinstance(o, list) else []) if int(x["value"]) > 0]
    for x in fwd:
        to_venue[x["label"] or x["to"]] += x["egld"]
    if not fwd:
        to_venue["(unmoved in fresh wallet)"] += v
    fan.append({"hop1": r, "egld": v, "ts": t["timestamp"],
                "hop1_nonce": i.get("nonce") if isinstance(i, dict) else None,
                "hop1_balance": int(i.get("balance", "0")) / 1e18 if isinstance(i, dict) and "balance" in i else None,
                "forwarded": fwd})
H["fanout"] = fan
H["fanout_total_egld"] = sum(x["egld"] for x in fan)
H["fanout_by_destination"] = dict(to_venue)
H["exchange_deposits_egld"] = {k: v for k, v in to_venue.items()
                               if k in ("Binance.com", "KuCoin", "MEXC") or (k in lab.values() and "Binance" in k)}
H["public_statement"] = {
    "source": "MultiversX on X, relayed by crypto press (cryptowisser, crypto.news, coindoo, bloomingbit), 2026-09-19..21",
    "summary": ("An actor attempted to exploit a VM-level atomicity issue, causing invalid state changes. Network "
                "progression is paused to prevent further impact. A fix is prepared and is being validated on a shadow "
                "fork; deployment will be coordinated with validators, exchanges and infrastructure partners. A targeted "
                "recovery that preserves finalized history and legitimate user state while addressing only "
                "incident-related invalid changes is being evaluated. Attacker accounts identified and frozen in "
                "coordination with exchanges. Users asked not to transact or use deposits/withdrawals."),
    "exchange_actions": ["Upbit suspended EGLD deposits/withdrawals Sep 19 (17:47 KST) and designated EGLD a trading-caution market Sep 21",
                         "Bithumb suspended deposits/withdrawals", "Kraken set EGLD pairs to cancel-only",
                         "Coinbase reported delayed sends/receives"],
    "urls": ["https://www.cryptowisser.com/news/multiversx-halts-network-after-hacker-exploits-atomicity-flaw/",
             "https://crypto.news/multiversx-hit-by-upbit-warning-after-mainnet-exploit/",
             "https://coindoo.com/multiversx-halts-mainnet-to-repair-invalid-state/",
             "https://en.bloomingbit.io/feed/news/120675"]}
H["cg_egld_hourly_7d"] = g("https://api.coingecko.com/api/v3/coins/elrond-erd-2/market_chart?vs_currency=usd&days=7")
time.sleep(1.5)
H["cg_btc_hourly_7d"] = g("https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=7")
D["chain_halt_incident"] = H
json.dump(D, open(SNAP, "w"))
print("last blocks", H["last_blocks"])
print("attacker txs", len(txs), "fanout", round(H["fanout_total_egld"]), dict((k, round(v)) for k, v in to_venue.items()))
print("W balance", int(H["attacker"]["account"].get("balance", "0")) / 1e18, "C balance", int(H["contract"]["account"].get("balance", "0")) / 1e18)
