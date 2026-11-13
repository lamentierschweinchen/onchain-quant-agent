#!/usr/bin/env python3
"""Staleness gate: fail a report that silently re-publishes last week's numbers.

Why this exists (run #36): the lean assembler builds each week's report by
deep-copying the previous one and overwriting what it recomputes. Anything it
forgets to recompute ships with last week's value and passes every other gate,
because the value is well-formed. Run #36 shipped a two-run-old DEX volume, a
stale turnover ratio, four liquid-staking TVL rows from run #34, a retired
incident block and placeholder text, all caught only by a manual diff.

Method: walk every leaf of the new report and compare it with the same field in
the previous report(s). List items are aligned by an identity key (address,
protocol, identifier, ...) rather than by index, so a re-ordered table still
lines up. A leaf is flagged when it is equal to the prior value and is not on
the list of fields that are legitimately stable week to week.

  ERROR (fails the gate)
    - a float with a real fractional part equal to the previous report's value
      (two independent measurements never agree to 10+ digits)
    - a narrative string (>= 60 chars) copied verbatim
    - placeholder text ("see analysis", "TODO", "restated at this run's prices")
  WARN (printed, does not fail)
    - integers and round numbers equal to last week's (could be real)
    - balances/prices on watch-listed paths where idle wallets are common

A genuine carry-forward is declared, with a reason, in
data/carry_declarations.json:  {"2026-11-16": {"path.regex": "reason"}}.
Declared paths are reported as CARRIED instead of failing.

Usage:
    python3 scripts/check_staleness.py reports/2026-11-09.json [--against reports/2026-11-02.json]
Exit 0 = pass, 1 = stale fields found, 2 = usage error.
"""
from __future__ import annotations
import argparse
import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DECL = REPO / "data" / "carry_declarations.json"

# Sections that are carried forward by design (ledgers / bookkeeping).
SKIP_TOP = {"metadata", "meta_learning", "pre_committed_tests"}

# Keys used to align list items across weeks, in priority order.
ID_KEYS = ("address", "provider_address", "protocol", "identifier", "exchange", "venue",
           "entity", "metric", "id", "item", "label", "name", "hash", "title")

# Fields that are legitimately the same week to week. Matched against the
# normalised path (list items shown as [key=value] or [i]).
STABLE = [r"\.threshold_egld$", r"\.(min|max)_apr_pct$", r"\.rank$", r"\.apr_pct$", r"\.fee_pct$",
          r"\.num_nodes$", r"\.addresses_tracked$", r"\.providers_sampled$", r"_window_days$",
          r"\.(address|provider_address|owner_address|identity|name|label|source|category|deployer|"
          r"sender|receiver|sender_label|receiver_label|ticker|identifier|provider|pair_address)$",
          r"\.decimals$", r"liveness\.(restart_|rollback)", r"\.tracked_wallets$", r"\.pairs$",
          r"\.zero_apr_providers$", r"\.provider_count$", r"\.count_(current|previous)$",
          r"\.weeks_on_list$", r"\.weeks_in_trend$", r"\.weeks$", r"\.shards$", r"\.total_pairs$",
          r"exchange_orderbook\.source$", r"identifiable_bid_status$", r"\.interpretation$|\.reason$",
          r"reward_behavior\.key_findings\["]   # regenerated each run by inject_reward_behavior.py; may legitimately repeat
# Paths where an exact repeat is plausible (idle wallets, illiquid tokens): warn only.
SOFT = [r"\.price_usd$", r"owner_balance_egld$", r"\.balance_(current|previous)_egld$",
        r"\.total_balance_egld$", r"\.fates_by_(value_egld|count)\.", r"\.market_cap_usd$",
        r"\.holders$", r"\.num_users$"]
PLACEHOLDER = re.compile(r"see analysis|\bTODO\b|\bTBD\b|placeholder|restated at this run's prices|lorem", re.I)

STABLE_RE = [re.compile(p) for p in STABLE]
SOFT_RE = [re.compile(p) for p in SOFT]


def item_key(item) -> str | None:
    if isinstance(item, dict):
        for k in ID_KEYS:
            v = item.get(k)
            if isinstance(v, (str, int)) and v != "":
                return f"{k}={v}"
    return None


def flatten(obj, path="", out=None):
    """Map normalised path -> leaf value."""
    if out is None:
        out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            flatten(v, f"{path}.{k}" if path else k, out)
    elif isinstance(obj, list):
        keys = [item_key(x) for x in obj]
        unique = len(set(k for k in keys if k)) == len(obj) and all(keys)
        for i, x in enumerate(obj):
            flatten(x, f"{path}[{keys[i] if unique else i}]", out)
    else:
        out[path] = obj
    return out


def is_real_float(v) -> bool:
    return isinstance(v, float) and math.isfinite(v) and v != round(v) and abs(v) > 1e-9


def any_match(res, path):
    return any(r.search(path) for r in res)


def declared(date: str) -> dict[str, str]:
    if not DECL.exists():
        return {}
    return json.loads(DECL.read_text()).get(date, {})


def previous_report(path: Path) -> Path | None:
    d = path.stem
    olds = sorted(p for p in path.parent.glob("20??-??-??.json") if p.stem < d)
    return olds[-1] if olds else None


def check(cur: dict, prev: dict, date: str):
    errors, warns, carried = [], [], []
    decl = {re.compile(k): v for k, v in declared(date).items()}
    C = {k: v for k, v in flatten(cur).items() if k.split(".")[0].split("[")[0] not in SKIP_TOP}
    P = flatten(prev)
    # siblings that state "no change" make an equal balance legitimate
    def sibling_zero(path):
        base = path.rsplit(".", 1)[0]
        for s in ("change_egld", "net_change_egld"):
            v = C.get(f"{base}.{s}")
            if isinstance(v, (int, float)) and abs(v) < 1e-6:
                return True
        return False
    for path, v in C.items():
        if isinstance(v, str) and PLACEHOLDER.search(v):
            errors.append((path, "placeholder text", v[:90]))
            continue
        if path not in P or v is None or isinstance(v, bool) or P[path] != v:
            continue
        if any_match(STABLE_RE, path):
            continue
        dec = next((r for r in decl if r.search(path)), None)
        if dec:
            carried.append((path, decl[dec]))
            continue
        if isinstance(v, str):
            if len(v) >= 60:
                errors.append((path, "narrative copied verbatim", v[:90]))
            continue
        if not isinstance(v, (int, float)) or v == 0:
            continue
        if any_match(SOFT_RE, path) or sibling_zero(path):
            warns.append((path, "equal to last report", v))
        elif is_real_float(v):
            errors.append((path, "float identical to last report", v))
        elif abs(v) >= 10:
            warns.append((path, "integer equal to last report", v))
    return errors, warns, carried


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("--against", help="previous report (default: latest earlier report in the same folder)")
    a = ap.parse_args()
    rp = Path(a.report)
    if not rp.exists():
        print(f"no such report: {rp}", file=sys.stderr)
        return 2
    pp = Path(a.against) if a.against else previous_report(rp)
    if not pp:
        print("STALENESS: no earlier report to compare against; skipped")
        return 0
    cur, prev = json.loads(rp.read_text()), json.loads(pp.read_text())
    date = cur.get("metadata", {}).get("report_date", rp.stem)
    errors, warns, carried = check(cur, prev, date)
    for p, why in carried:
        print(f"  CARRIED {p}: {why}")
    for p, why, v in warns:
        print(f"  WARN    {p}: {why} ({v})")
    for p, why, v in errors:
        print(f"  ERROR   {p}: {why} ({v})")
    if errors:
        print(f"STALENESS FAILED for {rp.name} vs {pp.name}: {len(errors)} error(s), {len(warns)} warning(s). "
              "Recompute these fields, drop them, or declare the carry in data/carry_declarations.json.")
        return 1
    print(f"STALENESS OK for {rp.name} vs {pp.name} ({len(warns)} warning(s), {len(carried)} declared carries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
