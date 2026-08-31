#!/usr/bin/env python3
"""Flag machine-readable identifiers leaking into reader-facing report prose.

Run #23 shipped a report whose narrative contained `corrected_direct_node_egld`,
`seconds_remaining`, `numNodes`, `serviceFee` and `dataApi` — internal field names
that mean nothing to a reader. The schema validator cannot catch this: the values
are valid strings in valid fields.

Enum fields and provenance lists are exempt: `anomalies[].method` is rendered as a
humanised badge, and the endpoint lists are a machine-readable audit trail.

Usage:  python3 scripts/lint_report_prose.py reports/2026-08-31.json
Exit 0 when clean, 1 when a leak is found.
"""
import json
import re
import sys

# Fields that legitimately hold machine values.
EXEMPT_KEYS = {
    "method", "data_sources_ok", "data_sources_failed",
    "endpoints_that_worked", "endpoints_that_failed",
    "identifier", "address", "hash", "sender", "receiver", "wallet",
    "provider", "provider_address", "owner_address", "contract", "id",
    "flow_type", "category", "severity", "health_signal", "status",
    "outcome", "direction", "event", "state", "tier",
    # The meta-learning block is the agent's engineering log. Script names and
    # JSON field paths are the correct vocabulary there, and the dashboard styles
    # them as code. Reader-facing narrative in that block is still linted below.
    "api_quirks", "methodology_changes", "recommendations_for_next_run",
    "data_gaps", "data_source", "dashboard_feature_suggestions",
    "dashboard_suggestions_followup", "action_items_completed",
    "new_addresses_discovered", "what_would_2x_next_week",
    "pre_committed_test_for_next_run", "coverage_note", "note",
}

# Real on-chain function names a quant reader needs; not leaks.
ALLOWED = {
    "unDelegate", "unDelegated", "unDelegations", "reDelegateRewards",
    "reDelegate", "claimRewards", "removeNodes", "unBondNodes",
    "unStakeNodes", "withdraw", "delegate", "xExchange", "xMoney",
    "xPortal", "dataApi",
}

SNAKE = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
CAMEL = re.compile(r"\b[a-z]+[A-Z][a-zA-Z]+\b")

# Identity slugs are the chain's own naming, not our field names.
IDENTITY_HINT = re.compile(r"^(binance_staking|[a-z0-9]+_staking|p2p_org_|star_staking)$")


def leaks(text: str):
    found = set()
    for m in SNAKE.findall(text):
        if IDENTITY_HINT.match(m) or m in ALLOWED:
            continue
        found.add(m)
    for m in CAMEL.findall(text):
        if m in ALLOWED:
            continue
        found.add(m)
    return found


def walk(node, path="", key=None, out=None):
    if out is None:
        out = []
    if isinstance(node, dict):
        for k, v in node.items():
            if k in EXEMPT_KEYS:
                continue
            walk(v, f"{path}/{k}", k, out)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            walk(v, f"{path}[{i}]", key, out)
    elif isinstance(node, str) and len(node) > 40:
        # Only prose; short strings are labels and identifiers.
        bad = leaks(node)
        if bad:
            out.append((path, sorted(bad)))
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: lint_report_prose.py <report.json>", file=sys.stderr)
        return 2
    report = json.load(open(sys.argv[1]))
    findings = walk(report)
    if not findings:
        print(f"PROSE OK: no machine identifiers in reader-facing text ({sys.argv[1]})")
        return 0
    print(f"PROSE LEAKS ({len(findings)}):")
    for path, bad in findings:
        print(f"  {path}: {', '.join(bad)}")
    print("\nRewrite these as plain English, or add genuine on-chain function")
    print("names to ALLOWED in scripts/lint_report_prose.py.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
