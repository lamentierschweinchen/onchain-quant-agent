#!/usr/bin/env python3
"""Two-hop resolution of the OTC desk hub for run #19.

Run #17 established "read a distribution wave by DESTINATION two hops out".
Run #19 needs the mirror as well: the desks were FED by exchanges this week, so
the same resolution has to run on the inbound leg. The output is persisted into
the collected snapshot as `otc_hub_trace` so the assembler does not re-query and
so the netting is reproducible from the stored raw data.
"""
import json, time, urllib.request, urllib.parse
from datetime import datetime, timezone

API = "https://api.multiversx.com"
REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
SNAP = f"{REPO}/data/collected/2026-08-03.json"
D = json.load(open(SNAP))
kn = json.load(open(f"{REPO}/data/known-addresses.json"))

label, cat = {}, {}
for s, e in kn.items():
    if not isinstance(e, dict) or s == "_metadata": continue
    for a, m in e.items():
        if isinstance(m, dict) and a.startswith("erd1"):
            label[a] = m.get("name", "Unknown"); cat[a] = m.get("category", "unknown")

AFTER = int(datetime(2026, 7, 27, tzinfo=timezone.utc).timestamp())
DESKS = {"erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5",
         "erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"}

def get(path, params=None):
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "intel-agent/19"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as ex:
        return {"__error__": str(ex)}

def venue_of(addr):
    """Map an address to a venue name if it is a known exchange or the recurring whale."""
    l = label.get(addr)
    if l and cat.get(addr) == "exchange":
        for v in ["Binance.com", "Binance", "UPbit", "Bybit", "Gate.io", "KuCoin",
                  "Coinbase", "Crypto.com", "MEXC", "Bitget", "Bitfinex", "Tokero"]:
            if v.split(".")[0] in l:
                return v
        return l
    if l and "Whale" in l:
        return l
    return None

# --- outbound: desk -> router -> terminal ---------------------------------
out_dest = {}
for a, v in D["desk_outbound_paged"].items():
    for t in v["txs"]:
        val = int(t.get("value", "0")) / 1e18
        if val <= 0 or t["receiver"] in DESKS: continue
        out_dest[t["receiver"]] = out_dest.get(t["receiver"], 0) + val

# --- inbound: source -> feeder -> desk ------------------------------------
in_src = {}
for a, v in D["desk_inbound_paged"].items():
    for t in v["txs"]:
        val = int(t.get("value", "0")) / 1e18
        if val <= 0 or t["sender"] in DESKS: continue
        in_src[t["sender"]] = in_src.get(t["sender"], 0) + val

def resolve(addr, direction):
    """Return {venue: amount} one hop past `addr` (outbound) or before it (inbound)."""
    v = venue_of(addr)
    if v:
        return {v: None}, "direct", None
    key = "sender" if direction == "out" else "receiver"
    txs = get(f"/accounts/{addr}/transactions",
              {"size": 30, "after": AFTER, "order": "desc", "status": "success", key: addr})
    time.sleep(0.25)
    info = get(f"/accounts/{addr}")
    time.sleep(0.2)
    bal = int(info.get("balance", "0")) / 1e18 if isinstance(info, dict) and "balance" in info else None
    agg = {}
    for t in (txs if isinstance(txs, list) else []):
        val = int(t.get("value", "0")) / 1e18
        if val <= 0: continue
        other = t["receiver"] if direction == "out" else t["sender"]
        if other in DESKS: continue
        vv = venue_of(other) or ("UNRESOLVED:" + other)
        agg[vv] = agg.get(vv, 0) + val
    return agg, "router", bal

trace = {"outbound": {}, "inbound": {}}
for addr, amt in sorted(out_dest.items(), key=lambda x: -x[1]):
    if amt < 1000:
        trace["outbound"][addr] = {"amount": amt, "kind": "small", "terminals": {}, "balance": None}
        continue
    agg, kind, bal = resolve(addr, "out")
    trace["outbound"][addr] = {"amount": amt, "kind": kind, "terminals": agg, "balance": bal,
                               "label": label.get(addr, "Unknown")}
    print(f"OUT {amt:10,.0f} -> {addr[:16]} {label.get(addr,'Unknown')[:30]:30s} {kind} {list(agg)[:2]}")

for addr, amt in sorted(in_src.items(), key=lambda x: -x[1]):
    if amt < 1000:
        trace["inbound"][addr] = {"amount": amt, "kind": "small", "terminals": {}, "balance": None}
        continue
    agg, kind, bal = resolve(addr, "in")
    trace["inbound"][addr] = {"amount": amt, "kind": kind, "terminals": agg, "balance": bal,
                              "label": label.get(addr, "Unknown")}
    print(f"IN  {amt:10,.0f} <- {addr[:16]} {label.get(addr,'Unknown')[:30]:30s} {kind} {list(agg)[:2]}")

# --- venue-level netting ---------------------------------------------------
def attribute(block, amount_key="amount"):
    """Attribute each router's desk-side amount to venues, pro-rata by the router's own flows."""
    per_venue = {}
    unresolved = 0.0
    for addr, rec in block.items():
        amt = rec["amount"]
        terms = rec["terminals"]
        if rec["kind"] == "direct":
            v = venue_of(addr)
            per_venue[v] = per_venue.get(v, 0) + amt
            continue
        named = {k: v for k, v in terms.items() if v and not k.startswith("UNRESOLVED")}
        tot = sum(named.values())
        if tot <= 0:
            unresolved += amt
            continue
        for v, val in named.items():
            per_venue[v] = per_venue.get(v, 0) + amt * (val / tot)
    return per_venue, unresolved

out_venues, out_unres = attribute(trace["outbound"])
in_venues, in_unres = attribute(trace["inbound"])
print("\n=== DESK HUB VENUE NETTING ===")
venues = sorted(set(list(out_venues) + list(in_venues)))
net = {}
for v in venues:
    o = out_venues.get(v, 0); i = in_venues.get(v, 0)
    net[v] = o - i
    print(f"  {v:34s} desk->venue {o:11,.0f}  venue->desk {i:11,.0f}  NET {o-i:+11,.0f}")
print(f"  unresolved out {out_unres:,.0f}  unresolved in {in_unres:,.0f}")
gross_out = sum(out_dest.values()); gross_in = sum(in_src.values())
circular = sum(min(out_venues.get(v, 0), in_venues.get(v, 0)) for v in venues)
print(f"  gross out {gross_out:,.0f} gross in {gross_in:,.0f} CIRCULAR (round-tripped) {circular:,.0f}")
print(f"  NET one-way distribution {gross_out-circular:,.0f}")

trace["venue_netting"] = {"outbound_by_venue": out_venues, "inbound_by_venue": in_venues,
                          "net_by_venue": net, "unresolved_out": out_unres, "unresolved_in": in_unres,
                          "gross_out": gross_out, "gross_in": gross_in, "circular": circular}
D["otc_hub_trace"] = trace
json.dump(D, open(SNAP, "w"))
print("\npersisted otc_hub_trace into", SNAP)
