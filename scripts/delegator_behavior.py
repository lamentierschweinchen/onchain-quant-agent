#!/usr/bin/env python3
"""Delegator and Provider Reward-Behavior Analysis (run #11 follow-up).

ANSWERS TWO QUESTIONS:
  a) What do individual DELEGATORS do with claimed rewards? (sell / hold / compound)
  b) What do staking PROVIDERS do with the service-fee earnings? (compound / sell / treasury)

METHOD — Delegators:
  1. For each tracked provider, fetch recent inbound transactions (the function calls).
  2. Categorize by function: claimRewards / reDelegateRewards / delegate / unDelegate.
  3. compound:claim ratio at the function level is the first-order signal.
  4. For each claimRewards event in the sample, look up the claimant's NEXT outbound
     value-bearing tx within 72h. Classify the destination:
       - Known exchange address       -> "sold"
       - Another delegation contract  -> "rotated_provider"
       - Same delegator's wallet hop  -> "held_or_self_routed"
       - Unknown / no follow-up tx     -> "held"
  5. Stratify by claim value:
       - retail:        < 1 EGLD per claim
       - mid_tier:      1 - 50 EGLD
       - institutional: 50 - 1000 EGLD
       - whale:         > 1000 EGLD

METHOD — Providers:
  1. For each tracked provider, get ownerAddress (the operator's wallet).
  2. Query the operator wallet's outbound value-bearing txs over the past 30 days.
  3. Classify destinations as above. Operator fees are skimmed from the contract via
     internal smart contract calls; the operator wallet then deploys them.

CAVEATS:
  - MultiversX rewards are paid in EGLD at epoch boundaries; this analysis only sees
    the on-chain claim/redelegate calls, not the underlying accrual.
  - "Held" includes wallets that hold then sell next week — needs longitudinal
    follow-up for full picture.
  - Provider operator wallets may also receive non-fee EGLD (treasury inflows, etc.) —
    not all outbound flows are fee-deployment.
  - Sample is illustrative, not exhaustive. ~50 events per provider per week.

Usage:
    python3 scripts/delegator_behavior.py
        --providers 5             # how many top providers to sample
        --days 7                  # window for delegator claims
        --operator-days 30        # window for operator wallet activity
        --output /tmp/delegator_behavior.json
"""
from __future__ import annotations
import argparse
import json
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

API = "https://api.multiversx.com"
REPO = Path("/Users/ls/Documents/MultiversX/projects/onchain-quant-agent")


def get(path: str, params: dict | None = None, retries: int = 2):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "delegator-behavior/1"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt == retries:
                return {"__error__": str(e), "__url__": url}
            time.sleep(1.0)


def load_known_addresses() -> tuple[dict[str, str], dict[str, str]]:
    kn = json.loads((REPO / "data/known-addresses.json").read_text())
    label, cat = {}, {}
    for section, entries in kn.items():
        if not isinstance(entries, dict) or section == "_metadata":
            continue
        for addr, meta in entries.items():
            if isinstance(meta, dict) and addr.startswith("erd1"):
                label[addr] = meta.get("name", "Unknown")
                cat[addr] = meta.get("category", "unknown")
    return label, cat


def is_delegation_contract(addr: str) -> bool:
    # Heuristic: delegation contracts are at erd1qqqqqqqqqqqqqqqp... shard-meta SC addresses
    return addr.startswith("erd1qqqqqqqqqqqqqqqp")


def classify_destination(receiver: str, cat: dict[str, str], label: dict[str, str], sender: str) -> str:
    if receiver == sender:
        return "self_loop"
    c = cat.get(receiver, "unknown")
    if c == "exchange" or c == "exchange_router":
        return "sold"
    if is_delegation_contract(receiver):
        return "rotated_provider"
    if c == "defi":
        return "defi_deposit"
    if c in ("validator", "team", "system"):
        return f"{c}_contract"
    return "held_or_other"


def log(msg: str) -> None:
    import sys
    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {msg}", flush=True, file=sys.stderr)


def analyse(args: argparse.Namespace) -> dict:
    label, cat = load_known_addresses()
    now = int(datetime.now(timezone.utc).timestamp())
    seven_days_ago = now - args.days * 86400
    operator_window_start = now - args.operator_days * 86400

    # Step 1 - fetch providers; /providers size param is IGNORED (verified run #11) so we slice client-side
    log(f"fetching providers (will sample top {args.providers} by locked)")
    provs = get("/providers", {"sort": "locked", "order": "desc"})
    if not isinstance(provs, list):
        return {"error": "providers fetch failed", "detail": provs}
    # Sort by locked desc (defensive; API claims sorted but verify) and trim
    provs.sort(key=lambda p: -float(p.get("locked", 0)))
    provs = provs[: args.providers]
    log(f"sampled {len(provs)} providers")
    time.sleep(0.3)

    overall_func_counts: Counter[str] = Counter()
    delegator_fates: dict[str, Counter[str]] = defaultdict(Counter)  # tier -> {fate -> count}
    delegator_fates_value: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))  # tier -> {fate -> value_egld}
    per_provider: list[dict] = []
    operator_summaries: list[dict] = []
    sample_claims: list[dict] = []  # representative claim->fate examples for the report

    for pi, p in enumerate(provs, 1):
        identity = p.get("identity") or p["provider"]
        prov_addr = p["provider"]
        prov_locked = float(p.get("locked", 0)) / 1e18
        prov_users = p.get("numUsers", 0)
        prov_apr = p.get("apr", 0)
        prov_fee = p.get("serviceFee", 0)
        log(f"[{pi}/{len(provs)}] {identity}: fetching txs")

        # Step 2 - inbound function calls in the window
        txs = get(
            f"/accounts/{prov_addr}/transactions",
            {"size": 100, "after": seven_days_ago, "order": "desc", "status": "success", "receiver": prov_addr},
        )
        time.sleep(0.3)
        if not isinstance(txs, list):
            continue
        func_counts: Counter[str] = Counter()
        for t in txs:
            func_counts[t.get("function", "none")] += 1
            overall_func_counts[t.get("function", "none")] += 1

        # Step 3 - for each claimRewards, find the claimant's next outbound EGLD tx
        # Limit per provider to keep budget reasonable
        claims = [t for t in txs if t.get("function") == "claimRewards"]
        provider_fates: Counter[str] = Counter()
        provider_fates_value: dict[str, float] = defaultdict(float)
        # Get account info to find ownerAddress
        prov_info = get(f"/accounts/{prov_addr}")
        time.sleep(0.2)
        owner_addr = prov_info.get("ownerAddress") if isinstance(prov_info, dict) else None

        log(f"    {len(claims)} claims found; processing up to {args.claims_per_provider}")
        for ci, c in enumerate(claims[: args.claims_per_provider], 1):
            claimant = c.get("sender")
            ts = c.get("timestamp")
            if not claimant or not ts:
                continue
            log(f"    claim {ci}: claimant={claimant[:14]} ts={ts}")
            # Use claim tx's own SC-result value to get claim amount.
            # The /transactions/{hash}/?withScResults=true returns the SC results.
            tx_hash = c.get("txHash")
            claim_value = 0.0
            if tx_hash:
                tx_full = get(f"/transactions/{tx_hash}", {"withScResults": "true"})
                time.sleep(0.15)
                if isinstance(tx_full, dict):
                    for r in (tx_full.get("results") or []):
                        if r.get("receiver") == claimant:
                            try:
                                v = int(r.get("value", "0")) / 1e18
                                claim_value = max(claim_value, v)
                            except Exception:
                                pass
            # Find next outbound EGLD tx from the claimant within 72h
            next_tx = get(
                f"/accounts/{claimant}/transactions",
                {"size": 5, "after": ts + 60, "before": ts + 72 * 3600, "order": "asc", "sender": claimant, "status": "success"},
            )
            time.sleep(0.15)
            fate = "held"  # default
            destination_label = "(no follow-up)"
            if isinstance(next_tx, list):
                for nt in next_tx:
                    receiver = nt.get("receiver")
                    if not receiver or receiver == prov_addr:
                        continue
                    try:
                        v = int(nt.get("value", "0")) / 1e18
                    except Exception:
                        v = 0.0
                    if v < 0.001:
                        continue
                    fate = classify_destination(receiver, cat, label, claimant)
                    destination_label = label.get(receiver, receiver[:14] + "…")
                    break

            tier = (
                "retail" if claim_value < 1 else
                "mid_tier" if claim_value < 50 else
                "institutional" if claim_value < 1000 else
                "whale"
            )
            delegator_fates[tier][fate] += 1
            delegator_fates_value[tier][fate] += claim_value
            provider_fates[fate] += 1
            provider_fates_value[fate] += claim_value
            if len(sample_claims) < 20 and claim_value > 0.5:
                sample_claims.append({
                    "provider": identity,
                    "claimant": claimant[:20] + "…",
                    "claim_value_egld": round(claim_value, 4),
                    "fate": fate,
                    "destination": destination_label,
                    "tier": tier,
                })

        # Step 4 - operator wallet behavior
        operator_data = None
        if owner_addr:
            op_txs = get(
                f"/accounts/{owner_addr}/transactions",
                {"size": 50, "after": operator_window_start, "order": "desc", "status": "success", "sender": owner_addr},
            )
            time.sleep(0.2)
            op_bal_info = get(f"/accounts/{owner_addr}")
            time.sleep(0.2)
            op_balance = int(op_bal_info.get("balance", "0")) / 1e18 if isinstance(op_bal_info, dict) else None
            op_fates: Counter[str] = Counter()
            op_fates_value: dict[str, float] = defaultdict(float)
            outbound_count = 0
            if isinstance(op_txs, list):
                for t in op_txs:
                    try:
                        v = int(t.get("value", "0")) / 1e18
                    except Exception:
                        v = 0.0
                    if v < 0.01:
                        continue
                    receiver = t.get("receiver")
                    if not receiver:
                        continue
                    f = classify_destination(receiver, cat, label, owner_addr)
                    op_fates[f] += 1
                    op_fates_value[f] += v
                    outbound_count += 1
            operator_data = {
                "owner_address": owner_addr,
                "owner_label": label.get(owner_addr, "Unknown"),
                "owner_balance_egld": op_balance,
                "outbound_count_30d": outbound_count,
                "fates_by_count": dict(op_fates),
                "fates_by_value_egld": {k: round(v, 2) for k, v in op_fates_value.items()},
            }

        per_provider.append({
            "identity": identity,
            "provider_address": prov_addr,
            "locked_egld": prov_locked,
            "users": prov_users,
            "apr_pct": prov_apr,
            "fee_pct": prov_fee * 100 if prov_fee else 0,
            "owner_address": owner_addr,
            "func_counts_7d": dict(func_counts),
            "claim_redelegate_ratio": (func_counts.get("claimRewards", 0) /
                                       max(func_counts.get("reDelegateRewards", 1), 1)),
            "compound_pct": (100 * func_counts.get("reDelegateRewards", 0) /
                            max(sum(func_counts.values()), 1)),
            "sampled_claim_fates_by_count": dict(provider_fates),
            "sampled_claim_fates_by_value_egld": {k: round(v, 2) for k, v in provider_fates_value.items()},
            "operator": operator_data,
        })

    # Aggregate across all sampled claims
    total_function_calls = sum(overall_func_counts.values())
    aggregates = {
        "window_days": args.days,
        "providers_sampled": len(per_provider),
        "operator_window_days": args.operator_days,
        "total_function_calls_observed": total_function_calls,
        "overall_function_distribution": {
            f: {"count": c, "share_pct": round(100 * c / total_function_calls, 2)}
            for f, c in overall_func_counts.most_common()
        },
        "compound_vs_claim_at_function_level": {
            "redelegate_count": overall_func_counts.get("reDelegateRewards", 0),
            "claim_count": overall_func_counts.get("claimRewards", 0),
            "compound_pct_of_reward_decisions": round(
                100 * overall_func_counts.get("reDelegateRewards", 0) /
                max(overall_func_counts.get("reDelegateRewards", 0) + overall_func_counts.get("claimRewards", 0), 1), 2),
        },
        "delegator_fates_by_tier": {
            tier: {
                "by_count": dict(counts),
                "by_value_egld": {k: round(v, 2) for k, v in delegator_fates_value[tier].items()},
                "total_events": sum(counts.values()),
                "total_value_egld": round(sum(delegator_fates_value[tier].values()), 2),
            }
            for tier, counts in delegator_fates.items()
        },
    }

    return {
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "window_days": args.days,
            "operator_window_days": args.operator_days,
            "providers_sampled": args.providers,
            "claims_per_provider": args.claims_per_provider,
        },
        "aggregates": aggregates,
        "per_provider": per_provider,
        "sample_claims": sample_claims,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--providers", type=int, default=5)
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--operator-days", type=int, default=30)
    p.add_argument("--claims-per-provider", type=int, default=15)
    p.add_argument("--output", default="/tmp/delegator_behavior.json")
    args = p.parse_args()

    result = analyse(args)
    Path(args.output).write_text(json.dumps(result, indent=2))
    agg = result.get("aggregates", {})
    print(f"\n=== Delegator/Provider behavior — sampled {args.providers} providers, {args.days}d window ===")
    fd = agg.get("overall_function_distribution", {})
    for f, info in fd.items():
        print(f"  {f:22} {info['count']:5} ({info['share_pct']:.1f}%)")
    cvc = agg.get("compound_vs_claim_at_function_level", {})
    print(f"\n  COMPOUND vs CLAIM (function-level): {cvc.get('redelegate_count')} redelegate vs {cvc.get('claim_count')} claim "
          f"-> {cvc.get('compound_pct_of_reward_decisions')}% compound")
    print(f"\n  Delegator fates by tier:")
    for tier, info in agg.get("delegator_fates_by_tier", {}).items():
        print(f"    {tier:14} {info['total_events']:3} events / {info['total_value_egld']:9.2f} EGLD")
        for fate, c in info["by_count"].items():
            v = info["by_value_egld"].get(fate, 0)
            print(f"        {fate:24} count={c:3} value={v:8.2f} EGLD")
    print(f"\n  Provider operator behavior:")
    for pr in result["per_provider"]:
        op = pr.get("operator") or {}
        print(f"    {pr['identity']:22} owner={op.get('owner_label','-'):20} "
              f"bal={op.get('owner_balance_egld','-')} outbound30d={op.get('outbound_count_30d','-')}")
        if op.get("fates_by_value_egld"):
            for f, v in op["fates_by_value_egld"].items():
                print(f"        -> {f:22} {v:.2f} EGLD")
    print(f"\nOutput: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
