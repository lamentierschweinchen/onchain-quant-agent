#!/usr/bin/env python3
"""Validate a weekly intelligence report against data/report-schema.json
PLUS a hand-curated list of dashboard-rendering invariants that the JSON
Schema alone can't catch (because the schema is permissive — every v2
field is optional — but the dashboard's React components have hard
expectations about which fields are present and what they're named).

Usage:
    python3 scripts/validate_report.py reports/2026-05-18.json

Exits 0 on success, 1 on validation failure. Used as the final gate in
the weekly run before committing.

This script exists because run #8 produced a JSON that passed
`json.load()` and HTTP 200'd, but used the wrong field names in
trend_indicators.validator_movements.notable_leavers
(`locked_egld_previous` instead of `previous_locked_egld`). The
resulting `undefined.toLocaleString()` crashed the entire React tree
because there's no error boundary at App level. Adding strict
validation here prevents the next iteration from re-introducing the
same class of bug.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(2)


REPO = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO / "data" / "report-schema.json"


# Hand-curated checks that the JSON Schema can't enforce on its own
# because it's permissive (every v2 field is optional). The dashboard
# code, by contrast, calls .toFixed / .toLocaleString on these fields
# unconditionally — so they must exist whenever the containing array
# is non-empty.
DASHBOARD_INVARIANTS = [
    # (path, required_fields_when_present)
    # path uses simple JSON-Pointer-like syntax; '[]' = each item of an array
    ("whale_intelligence.exchange_flows.by_exchange[]", ["exchange", "change_egld"]),
    ("whale_intelligence.exchange_flows.entity_netting[]", ["entity", "net_flow_egld", "wallets_count"]),
    ("whale_intelligence.wallet_changes[]", ["address", "balance_current_egld"]),
    ("whale_intelligence.whale_tiers.mega_whales", ["count_current", "total_balance_egld"]),
    ("whale_intelligence.whale_tiers.large_whales", ["count_current", "total_balance_egld"]),
    ("whale_intelligence.whale_tiers.mid_whales", ["count_current", "total_balance_egld"]),
    ("whale_intelligence.large_transactions[]", ["hash", "timestamp", "sender", "receiver", "value_egld", "flow_type"]),
    ("staking_intelligence.apr_distribution.buckets[]", ["label", "min_apr_pct", "max_apr_pct", "provider_count", "total_locked_egld"]),
    ("staking_intelligence.apr_outliers.top_apr[]", ["identity", "apr_pct", "fee_pct", "locked_egld"]),
    ("staking_intelligence.apr_outliers.lowest_fee[]", ["identity", "apr_pct", "fee_pct", "locked_egld"]),
    ("staking_intelligence.top_providers[]", ["rank", "identity", "locked_egld", "share_pct", "apr_pct", "fee_pct", "num_users"]),
    ("staking_intelligence.reward_behavior.compound_vs_claim", ["redelegate_count", "claim_count"]),
    ("staking_intelligence.reward_behavior.provider_operators[]", ["provider", "owner_address"]),
    ("token_activity.top_by_holders[]", ["identifier", "name", "holders"]),
    ("token_activity.xexchange", ["total_pairs", "mex_price_usd", "mex_market_cap_usd"]),
    ("defi_activity.protocol_breakdown[]", ["protocol", "category", "addresses_tracked"]),
    ("trend_indicators.validator_movements.notable_joiners[]", ["identity", "locked_egld"]),
    ("trend_indicators.validator_movements.notable_leavers[]", ["identity", "previous_locked_egld"]),
    ("trend_indicators.token_supply_events[]", ["identifier", "name", "event", "description"]),
    ("trend_indicators.regime_shifts[]", ["metric", "after_value", "description"]),
    ("anomalies[]", ["metric", "current_value", "severity", "description"]),
    ("watch_list[]", ["item", "reason", "weeks_on_list"]),
]

# Enum constraints the dashboard relies on (TS string-literal unions).
# These ARE in the JSON Schema, but jsonschema-validate may not flag
# them as critical — listing them explicitly produces clearer errors.
ENUM_INVARIANTS = [
    ("whale_intelligence.large_transactions[].flow_type",
     {"exchange_inflow", "exchange_outflow", "exchange_to_exchange",
      "defi_deposit", "defi_withdrawal",
      "whale_to_whale", "staking", "unstaking", "bridge", "unknown"}),
    ("defi_activity.protocol_breakdown[].category",
     {"dex", "lending", "liquid_staking", "stablecoin", "nft_marketplace",
      "bridge", "perpetuals", "aggregator", "other"}),
    ("defi_activity.protocol_breakdown[].health_signal",
     {"growing", "flat", "shrinking", "spiking", "draining", None}),
    ("trend_indicators.consecutive_streaks[].direction",
     {"up", "down", "flat"}),
    ("executive_summary[].category",
     {"whale", "staking", "token", "defi", "network", "anomaly", "trend"}),
    ("anomalies[].severity",
     {"critical", "high", "medium", "low"}),
    ("anomalies[].method",
     {"z_score", "percent_threshold", "rule_based", None}),
]


def walk_path(data, path):
    """Walk a dotted path with `[]` array iteration. Yields each match."""
    if not path:
        yield data
        return
    parts = []
    cur = ""
    for ch in path:
        if ch == ".":
            if cur:
                parts.append(cur)
                cur = ""
        else:
            cur += ch
    if cur:
        parts.append(cur)

    def visit(node, idx):
        if idx == len(parts):
            yield node
            return
        part = parts[idx]
        is_array = part.endswith("[]")
        key = part[:-2] if is_array else part
        if not isinstance(node, dict) or key not in node:
            return
        nxt = node[key]
        if is_array:
            if not isinstance(nxt, list):
                return
            for item in nxt:
                yield from visit(item, idx + 1)
        else:
            yield from visit(nxt, idx + 1)

    yield from visit(data, 0)


def check_dashboard_invariants(report):
    errors = []
    for path, required in DASHBOARD_INVARIANTS:
        # Special case: array invariants apply per item, scalar per object
        matches = list(walk_path(report, path))
        for i, item in enumerate(matches):
            if item is None:
                continue
            if not isinstance(item, dict):
                errors.append(f"  {path}[{i}]: expected object, got {type(item).__name__}")
                continue
            for field in required:
                if field not in item:
                    errors.append(f"  {path}[{i}]: missing required field '{field}' (keys present: {sorted(item.keys())})")
                elif item[field] is None and field in {"hash", "sender", "receiver", "identity", "address", "metric", "label", "exchange"}:
                    errors.append(f"  {path}[{i}].{field}: required field is null")
    return errors


def check_enum_invariants(report):
    errors = []
    for path, allowed in ENUM_INVARIANTS:
        for i, value in enumerate(walk_path(report, path)):
            if value is None and None in allowed:
                continue
            if value not in allowed:
                errors.append(f"  {path}[{i}]: value '{value}' not in allowed set {sorted(v for v in allowed if v is not None)}")
    return errors


def validate_against_schema(report, schema):
    errors = []
    try:
        validator = jsonschema.Draft7Validator(schema)
        for err in sorted(validator.iter_errors(report), key=lambda e: e.path):
            loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
            errors.append(f"  {loc}: {err.message}")
    except jsonschema.SchemaError as e:
        errors.append(f"  schema is itself invalid: {e}")
    return errors


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path/to/report.json>", file=sys.stderr)
        sys.exit(2)

    report_path = Path(sys.argv[1])
    if not report_path.exists():
        print(f"ERROR: report not found: {report_path}", file=sys.stderr)
        sys.exit(2)
    if not SCHEMA_PATH.exists():
        print(f"ERROR: schema not found: {SCHEMA_PATH}", file=sys.stderr)
        sys.exit(2)

    report = json.load(open(report_path))
    schema = json.load(open(SCHEMA_PATH))

    schema_errors = validate_against_schema(report, schema)
    invariant_errors = check_dashboard_invariants(report)
    enum_errors = check_enum_invariants(report)

    total = len(schema_errors) + len(invariant_errors) + len(enum_errors)
    if total == 0:
        print(f"OK: {report_path.name} passes schema + dashboard invariants ({len(report.get('executive_summary', []))} findings, "
              f"{len(report.get('whale_intelligence', {}).get('wallet_changes', []))} wallet changes, "
              f"{len(report.get('anomalies', []))} anomalies, "
              f"{len(report.get('watch_list', []))} watch items).")
        return 0

    print(f"VALIDATION FAILED for {report_path}", file=sys.stderr)
    print(f"  {len(schema_errors)} JSON Schema violation(s)", file=sys.stderr)
    print(f"  {len(invariant_errors)} dashboard-invariant violation(s)", file=sys.stderr)
    print(f"  {len(enum_errors)} enum violation(s)", file=sys.stderr)
    if schema_errors:
        print("\nJSON Schema violations:", file=sys.stderr)
        for e in schema_errors[:30]:
            print(e, file=sys.stderr)
    if invariant_errors:
        print("\nDashboard invariant violations:", file=sys.stderr)
        for e in invariant_errors:
            print(e, file=sys.stderr)
    if enum_errors:
        print("\nEnum violations:", file=sys.stderr)
        for e in enum_errors:
            print(e, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
