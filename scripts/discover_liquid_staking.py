#!/usr/bin/env python3
"""Discover liquid-staking protocols on MultiversX, including ones we do not track.

THE SIGNATURE
    A liquid-staking protocol is a smart contract that (a) owns an ESDT and
    (b) has userActiveStake > 0 on delegation contracts. It stakes EGLD on
    behalf of other people and hands them a transferable claim. Nothing else
    on this chain has that shape.

WHY IT IS DRIVEN FROM THE TOKEN SIDE
    The obvious approach - scan delegation contracts for smart-contract senders
    calling `delegate` - DOES NOT WORK. A contract-to-contract delegate call is
    settled as a smart-contract result and never appears in
    /accounts/{provider}/transactions. Verified against the VoxEGLD contract:
    zero hits as a sender in the provider's /transactions, 50 in its /transfers.
    This is the run #19/#21 lesson (trace through callers, SC results are
    invisible to value-transfer scans) in a new place.

    /tokens/{identifier} exposes `owner` directly, so going token -> owner ->
    delegation is one hop, exhaustive over anything with a listed token, and
    an order of magnitude cheaper.

Usage:
    python3 scripts/discover_liquid_staking.py
    python3 scripts/discover_liquid_staking.py --pages 4      # widen the sweep
"""
import argparse
import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = "https://api.multiversx.com"
REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"


def get(path, params=None, retries=3):
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    delay = 1.0
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "intel-agent/lsd-discovery"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if "429" in str(e):
                time.sleep(delay)
                delay = min(delay * 2, 12.0)
                continue
            if attempt == retries:
                return {"__error__": str(e)}
            time.sleep(0.8)
    return {"__error__": "retries exhausted"}


def is_contract(addr):
    return bool(addr) and addr.startswith("erd1qqqq")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages", type=int, default=3,
                    help="Pages of 50 to pull from each ranked token list.")
    ap.add_argument("--output", default=f"{REPO}/data/collected/liquid_staking_discovery.json")
    args = ap.parse_args()

    kn = json.load(open(f"{REPO}/data/known-addresses.json"))
    label_map = {}
    for section, entries in kn.items():
        if isinstance(entries, dict) and section != "_metadata":
            for a, m in entries.items():
                if isinstance(m, dict) and a.startswith("erd1"):
                    label_map[a] = m.get("name", "Unknown")

    # --- 1. Gather candidate tokens ----------------------------------------
    # Ranked lists catch anything with real adoption; the name search catches a
    # freshly launched LSD that has neither market cap nor holders yet, which is
    # exactly the case that would otherwise be missed for months.
    tokens = {}

    def absorb(batch):
        for t in batch if isinstance(batch, list) else []:
            if isinstance(t, dict) and t.get("identifier"):
                tokens.setdefault(t["identifier"], t)

    for term in ("EGLD", "staked", "stake"):
        absorb(get("/tokens", {"search": term, "size": 50}))
        print(f"  search '{term}' -> {len(tokens)} candidate tokens")
    for sort in ("marketCap", "accounts", "transactions"):
        for page in range(args.pages):
            absorb(get("/tokens", {"size": 50, "from": page * 50,
                                   "sort": sort, "order": "desc"}))
        print(f"  sort {sort} ({args.pages} pages) -> {len(tokens)} candidate tokens")

    # --- 2. Reduce to distinct smart-contract owners -----------------------
    owners = {}
    for ident, t in tokens.items():
        owner = t.get("owner")
        if is_contract(owner):
            owners.setdefault(owner, []).append(ident)
    print(f"\n{len(tokens)} tokens -> {len(owners)} distinct smart-contract owners to verify\n")

    # --- 3. Verify: does the owner actually stake? -------------------------
    found = []
    for i, (owner, idents) in enumerate(sorted(owners.items()), 1):
        dg = get(f"/accounts/{owner}/delegation")
        time.sleep(0.22)
        staked = 0.0
        n = 0
        if isinstance(dg, list):
            for row in dg:
                act = int(row.get("userActiveStake", "0") or 0) / 1e18
                staked += act
                if act > 0:
                    n += 1
        if staked <= 0:
            continue

        info = get(f"/accounts/{owner}")
        time.sleep(0.2)
        receipts = []
        for ident in idents:
            meta = tokens.get(ident, {})
            full = get(f"/tokens/{ident}")
            time.sleep(0.25)
            if isinstance(full, dict) and "__error__" not in full:
                meta = full
            receipts.append({
                "identifier": ident,
                "name": meta.get("name"),
                "supply": meta.get("supply"),
                "holders": meta.get("accounts"),
                "price_usd": meta.get("price"),
                "market_cap_usd": meta.get("marketCap"),
                "description": (meta.get("assets") or {}).get("description"),
                "website": (meta.get("assets") or {}).get("website"),
            })

        entry = {
            "address": owner,
            "known_label": label_map.get(owner),
            "tracked": owner in label_map,
            "owner_of_contract": info.get("ownerAddress") if isinstance(info, dict) else None,
            "deployed_at": info.get("deployedAt") if isinstance(info, dict) else None,
            "staked_egld": staked,
            "delegation_contracts": n,
            "receipt_tokens": receipts,
        }
        found.append(entry)
        tag = entry["known_label"] or "*** NOT TRACKED ***"
        toks = ", ".join(f"{r['identifier']} ({r['name']})" for r in receipts)
        print(f"  LSD  {staked:>12,.0f} EGLD staked  {toks}")
        print(f"       {owner}")
        print(f"       {tag}")

    found.sort(key=lambda x: -x["staked_egld"])
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "method": "token owner -> delegation stake (SC-to-SC delegate calls are "
                  "smart-contract results and invisible to /transactions)",
        "tokens_examined": len(tokens),
        "contract_owners_verified": len(owners),
        "liquid_staking_protocols": found,
    }
    json.dump(out, open(args.output, "w"), indent=1)

    untracked = [f for f in found if not f["tracked"]]
    print(f"\nSaved {args.output}")
    print(f"\n=== {len(found)} liquid-staking protocols found; {len(untracked)} NOT tracked ===")
    for f in untracked:
        print(f"  {f['address']}  {f['staked_egld']:,.0f} EGLD")
        for r in f["receipt_tokens"]:
            print(f"    {r['identifier']}  {r['name']}  supply={r['supply']}  holders={r['holders']}")
            if r.get("description"):
                print(f"      {r['description'][:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
