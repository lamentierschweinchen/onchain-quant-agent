#!/usr/bin/env python3
"""Run #25 followup: recover every paged query the main pass lost to HTTP 429.

The main collector ran concurrently with delegator_behavior.py, and the extra
load tripped the rate limiter on the OTC Distribution Wallet's wave-window scan
(outbound cut at 400 txs, inbound returned 0). paged_txs recorded both as
errors rather than empty windows - the run #23 fix doing its job - so the wave
netting is known-corrupt rather than silently wrong.

This pass re-pages every (address, direction, tag) in _paged_errors with a
longer backoff, rebuilds the wave-window hub trace from the recovered legs, and
writes the result back into the canonical snapshot with a provenance note.
"""
import json, time, urllib.request, urllib.parse, sys, importlib.util, types
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD = "2026-09-14"
SNAP = f"{REPO}/data/collected/{RD}.json"
D = json.load(open(SNAP))

# Pull helper functions out of the collector source without running its main body.
src = open(f"{REPO}/scripts/collect_run25.py").read()
cut = src.index("D = {\"_period\"")
helpers = src[:cut]
g = {"__name__": "helpers"}
exec(helpers, g)
# longer backoff for the recovery pass
def get(path, params=None, retries=7):
    url = g["API"] + path + ("?" + urllib.parse.urlencode(params) if params else "")
    delay = 2.0
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "intel-agent/25-followup"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt == retries:
                g["API_ERRORS"].append({"url": url, "error": str(e)})
                return {"__error__": str(e), "__url__": url}
            time.sleep(delay); delay = min(delay * 2, 30.0)
g["get"] = get

# the rest of the collector's module-level helpers need these names
kn = g["kn"]
label_map, cat_map = {}, {}
for section, entries in kn.items():
    if not isinstance(entries, dict) or section == "_metadata":
        continue
    for addr, meta in entries.items():
        if isinstance(meta, dict) and addr.startswith("erd1"):
            label_map[addr] = meta.get("name", "Unknown"); cat_map[addr] = meta.get("category", "unknown")
g["label_map"] = label_map; g["cat_map"] = cat_map

# re-exec the hub helpers (venue_of / resolve_hop / attribute / hub_trace) against the new get
blk_start = src.index("def venue_of(addr):")
blk_end = src.index('print("\\n=== HUB TRACE: 7d window')
UPBIT_OTC = "erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
OTC_DIST = "erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
g["DESKS"] = {UPBIT_OTC: "UPbit OTC Desk", OTC_DIST: "OTC Distribution Wallet"}
exec(src[blk_start:blk_end], g)

errs = D.get("_paged_errors") or []
print(f"{len(errs)} paged errors to recover")
recovered = []
for e in errs:
    addr, direction, tag = e["address"], e["direction"], e["tag"]
    if tag == "wave3ext":
        txs = g["paged_txs"](addr, g["WAVE_START"], before=g["WAVE_END"], direction=direction, max_pages=200, tag="wave3ext_recovery")
        key = "desk_outbound_wave3ext" if direction == "sender" else "desk_inbound_wave3ext"
        D[key][addr]["txs"] = txs
        recovered.append({"address": addr, "direction": direction, "tag": tag, "txs": len(txs)})
        print(f"  recovered {tag} {addr[:14]} {direction}: {len(txs)} txs")
        time.sleep(1.0)
    else:
        recovered.append({"address": addr, "direction": direction, "tag": tag, "txs": None,
                          "note": "not a wave-window leg; left as recorded"})
        print(f"  NOT re-queried (tag {tag}) {addr[:14]} {direction}")

new_errs = [x for x in g["PAGED_ERRORS"]]
if any(r["tag"] == "wave3ext" for r in recovered) and not new_errs:
    D["otc_hub_trace_wave3ext"] = g["hub_trace"](D["desk_outbound_wave3ext"], D["desk_inbound_wave3ext"],
                                                 g["WAVE_START"], before=g["WAVE_END"])
    D["otc_hub_trace_wave3ext"]["_window"] = "WAVE EXTENDED Aug 17 - Sep 14 (feed-to-drain, 4 weeks)"
    D["otc_hub_trace_wave3ext"]["_provenance"] = "rebuilt by followup_run25.py after HTTP 429 on the main pass"
    vn = D["otc_hub_trace_wave3ext"]["venue_netting"]
    print(f"WAVE rebuilt: gross_out={vn['gross_out']:,.0f} gross_in={vn['gross_in']:,.0f} circ={vn['circular']:,.0f} net={vn['net_one_way']:,.0f}")
    print("  net_by_venue", {k: round(v) for k, v in vn["net_by_venue"].items()})
    D["_paged_errors_main_pass"] = errs
    D["_paged_errors"] = []
else:
    print("recovery incomplete:", new_errs)
D["_followup_recovery"] = {"recovered": recovered, "new_errors": new_errs,
                           "ran_at": datetime.now(timezone.utc).isoformat()}
json.dump(D, open(SNAP, "w"))
print("snapshot updated")
