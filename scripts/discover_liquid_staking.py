#!/usr/bin/env python3
"""Discover liquid-staking protocols on MultiversX, including ones we do not track yet.

A liquid-staking contract has a precise, checkable signature:

  1. it is a smart contract  (erd1qqqq...)
  2. it DELEGATES            (/accounts/{addr}/delegation reports userActiveStake > 0)
  3. it ISSUES a receipt     (/accounts/{addr}/roles/tokens returns a token it owns)

Anything satisfying all three is staking EGLD on behalf of other people and handing
them a transferable claim — that is liquid staking, whatever it calls itself.

Candidates come from the delegation side, which is exhaustive by construction: an
LSD must call `delegate` on a delegation contract, so scanning provider inbound
transactions for smart-contract senders cannot miss one that is actually staking.

Usage:
    python3 scripts/discover_liquid_staking.py [--days 120] [--providers 40]
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


def classify(addr, label_map):
    """Apply the three-part signature. Returns a dict when it qualifies."""
    dg = get(f"/accounts/{addr}/delegation")
    time.sleep(0.25)
    staked = 0.0
    contracts = 0
    if isinstance(dg, list):
        for row in dg:
            act = int(row.get("userActiveStake", "0") or 0) / 1e18
            staked += act
            if act > 0:
                contracts += 1
    if staked <= 0:
        return None

    roles = get(f"/accounts/{addr}/roles/tokens", {"size": 25})
    time.sleep(0.25)
    tokens = []
    if isinstance(roles, list):
        for t in roles:
            ident = t.get("identifier")
            if not ident:
                continue
            meta = get(f"/tokens/{ident}")
            time.sleep(0.3)
            if isinstance(meta, dict) and "__error__" not in meta:
                tokens.append({
                    "identifier": ident,
                    "name": meta.get("name"),
                    "supply": meta.get("supply"),
                    "holders": meta.get("accounts"),
                    "price_usd": meta.get("price"),
                    "market_cap_usd": meta.get("marketCap"),
                })
    if not tokens:
        return None

    info = get(f"/accounts/{addr}")
    time.sleep(0.2)
    return {
        "address": addr,
        "known_label": label_map.get(addr),
        "owner": info.get("ownerAddress") if isinstance(info, dict) else None,
        "deployed_at": info.get("deployedAt") if isinstance(info, dict) else None,
        "staked_egld": staked,
        "delegation_contracts": contracts,
        "receipt_tokens": tokens,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=120,
                    help="How far back to scan provider inbound for delegate calls.")
    ap.add_argument("--providers", type=int, default=40,
                    help="How many providers to scan, largest first.")
    ap.add_argument("--max-pages", type=int, default=6)
    ap.add_argument("--output", default=f"{REPO}/data/collected/liquid_staking_discovery.json")
    args = ap.parse_args()

    after = int(datetime.now(timezone.utc).timestamp()) - args.days * 86400

    kn = json.load(open(f"{REPO}/data/known-addresses.json"))
    label_map = {}
    for section, entries in kn.items():
        if isinstance(entries, dict) and section != "_metadata":
            for a, m in entries.items():
                if isinstance(m, dict) and a.startswith("erd1"):
                    label_map[a] = m.get("name", "Unknown")

    providers = get("/providers", {"size": 200, "sort": "locked", "order": "desc"})
    if not isinstance(providers, list):
        print("could not load providers:", providers)
        return 1
    active = [p for p in providers if float(p.get("locked", 0) or 0) > 0][: args.providers]
    print(f"Scanning {len(active)} providers for smart-contract delegators "
          f"over the last {args.days} days…\n")

    candidates = {}
    for i, p in enumerate(active, 1):
        addr = p.get("provider")
        ident = p.get("identity") or addr
        frm = 0
        seen = 0
        for _ in range(args.max_pages):
            batch = get(f"/accounts/{addr}/transactions",
                        {"size": 50, "from": frm, "after": after, "order": "desc",
                         "status": "success", "receiver": addr})
            time.sleep(0.22)
            if not isinstance(batch, list) or not batch:
                break
            for t in batch:
                fn = t.get("function") or ""
                snd = t.get("sender")
                if fn in ("delegate", "claimRewards", "reDelegateRewards", "unDelegate") \
                        and is_contract(snd) and snd != addr:
                    candidates.setdefault(snd, set()).add(ident)
                    seen += 1
            if len(batch) < 50:
                break
            frm += 50
        if i % 10 == 0 or seen:
            print(f"  [{i}/{len(active)}] {str(ident)[:30]:32} contract-callers so far: {len(candidates)}")

    print(f"\n{len(candidates)} smart-contract delegators found. Verifying signature…\n")
    found = []
    for addr, provs in sorted(candidates.items()):
        res = classify(addr, label_map)
        if res:
            res["delegates_to"] = sorted(provs)[:6]
            found.append(res)
            tok = ", ".join(f"{t['identifier']} ({t['name']})" for t in res["receipt_tokens"])
            tag = res["known_label"] or "*** NOT TRACKED ***"
            print(f"  LSD  {addr[:24]}…  {res['staked_egld']:>12,.0f} EGLD  {tok}")
            print(f"       {tag}")

    found.sort(key=lambda x: -x["staked_egld"])
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "window_days": args.days,
        "providers_scanned": len(active),
        "contract_delegators_seen": len(candidates),
        "liquid_staking_protocols": found,
    }
    json.dump(out, open(args.output, "w"), indent=1)
    print(f"\nSaved {args.output}")
    untracked = [f for f in found if not f["known_label"]]
    print(f"\n=== {len(found)} liquid-staking protocols; {len(untracked)} NOT tracked ===")
    for f in untracked:
        print(f"  {f['address']}")
        for t in f["receipt_tokens"]:
            print(f"    {t['identifier']} {t['name']} supply={t['supply']} holders={t['holders']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
