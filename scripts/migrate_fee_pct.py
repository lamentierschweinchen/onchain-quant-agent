#!/usr/bin/env python3
"""One-shot migration: convert `fee_pct` from fraction (0.12) to percent (12.0)
in historical reports where it was stored incorrectly.

Audit (run 2026-06-01):
- Runs #2-#7 (2026-04-07 through 2026-05-11): fee_pct already in percent units.
- Runs #8 + #9 (2026-05-18, 2026-05-25): fee_pct stored as fraction. BROKEN.
- Run #10 (2026-06-01): fixed at write time.
- Run #1 (2026-04-02): top_providers empty; nothing to migrate.

Touches:
  staking_intelligence.top_providers[].fee_pct
  staking_intelligence.apr_outliers.top_apr[].fee_pct
  staking_intelligence.apr_outliers.lowest_fee[].fee_pct

Heuristic: only multiply if max(fee_pct) across the file is <= 1.0 (i.e. all
values look like fractions). Skips files where any fee_pct > 1.0 (already
correct). Idempotent.
"""
import json, sys, glob, shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REPORTS = REPO / "reports"
DASH = REPO / "dashboard" / "public" / "reports"

def all_fees(report):
    fees = []
    si = report.get("staking_intelligence") or {}
    for p in si.get("top_providers") or []:
        if isinstance(p.get("fee_pct"), (int, float)):
            fees.append(p["fee_pct"])
    outl = si.get("apr_outliers") or {}
    for key in ("top_apr", "lowest_fee"):
        for p in outl.get(key) or []:
            if isinstance(p.get("fee_pct"), (int, float)):
                fees.append(p["fee_pct"])
    return fees

def needs_migration(report):
    """Return True iff every fee_pct is <= 1.0 (looks like a fraction)
    AND at least one is > 0 (not just an empty file)."""
    fees = all_fees(report)
    if not fees: return False
    if max(fees) > 1.0: return False
    if all(f == 0 for f in fees): return False
    return True

def migrate(report):
    si = report["staking_intelligence"]
    for p in si.get("top_providers") or []:
        if isinstance(p.get("fee_pct"), (int, float)):
            p["fee_pct"] = p["fee_pct"] * 100
    outl = si.get("apr_outliers") or {}
    for key in ("top_apr", "lowest_fee"):
        for p in outl.get(key) or []:
            if isinstance(p.get("fee_pct"), (int, float)):
                p["fee_pct"] = p["fee_pct"] * 100

def main():
    paths = sorted(glob.glob(str(REPORTS / "*.json")))
    touched = []
    for path in paths:
        report = json.load(open(path))
        if not needs_migration(report):
            print(f"  SKIP {Path(path).name} (fees already in percent units or empty)")
            continue
        before = all_fees(report)
        migrate(report)
        after = all_fees(report)
        print(f"  FIX  {Path(path).name}  max {max(before):.4f} -> {max(after):.2f}")
        json.dump(report, open(path, "w"), indent=2)
        # mirror into dashboard/public/reports
        dash_path = DASH / Path(path).name
        if dash_path.exists():
            shutil.copy(path, dash_path)
            print(f"       copied to {dash_path.relative_to(REPO)}")
        touched.append(Path(path).name)
    print(f"\nMigrated {len(touched)} report(s): {touched}")

if __name__ == "__main__":
    main()
