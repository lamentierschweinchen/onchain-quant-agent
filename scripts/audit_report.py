#!/usr/bin/env python3
"""Pre-publish data-integrity audit for the weekly intelligence report.

Run AFTER assemble and BEFORE validate. Catches the class of bugs that
schema validation can't:

- Missing token data that silently zeroes out a TVL bucket (e.g., SWTAO
  returned None this run, making Hatom LSD appear -26% when reality was -1%)
- Large supply-change events that the assembler under-emphasized (e.g.,
  USH -7.08% surfaced only in trend_indicators.token_supply_events, not
  in executive_summary or watch_list)
- Excessive "Unknown" labels in large_transactions (entity-resolution gap)
- Implausible WoW deltas in protocol_breakdown that suggest missing data
- Null-but-derivable fields (top_by_market_cap.holders, top_by_volume.previous_transactions)

The audit emits WARNINGS (non-blocking) and ERRORS (blocking). ERRORS
should be addressed before publish; WARNINGS are advisories.

Usage:
    python3 scripts/audit_report.py reports/2026-06-08.json [collected_path]

Exits 0 if no errors (warnings allowed), 1 if errors found.

This script was added run #11 after a post-publish audit caught the
SWTAO/USH issues. Run it as the final gate in future runs:

    python3 scripts/audit_report.py reports/${DATE}.json data/collected/${DATE}.json
    python3 scripts/validate_report.py reports/${DATE}.json
"""
from __future__ import annotations
import json
import sys
from pathlib import Path


def audit_report(report_path: Path, collected_path: Path | None, previous_path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    R = json.loads(report_path.read_text())
    prev = json.loads(previous_path.read_text())
    collected = json.loads(collected_path.read_text()) if collected_path and collected_path.exists() else None

    # ---------- Check 1: Raw token data integrity (if collected.json available) ----------
    if collected:
        tvl_tokens = collected.get("tvl_tokens", {})
        for tid in ["HUSDC-d80042", "HEGLD-d61095", "HUSDT-6f0914", "HWBTC-49ca31",
                    "HWETH-b3d17e", "HBUSD-ac1fca", "HHTM-e03ba5", "HMEX-df6df7",
                    "HUTK-4fa4b2", "HWTAO-2e9136", "SEGLD-3ad2d0", "SWTAO-356a25",
                    "USH-111e09", "XEGLD-e413ed"]:
            t = tvl_tokens.get(tid)
            if not isinstance(t, dict):
                warnings.append(f"raw_data: {tid} entry missing from collected.tvl_tokens")
                continue
            if t.get("marketCap") is None or t.get("price") is None:
                # Determine which protocol this affects
                affected = {
                    "SEGLD-3ad2d0": "Hatom Liquid Staking", "SWTAO-356a25": "Hatom Liquid Staking",
                    "XEGLD-e413ed": "XOXNO LSD", "USH-111e09": "Hatom USH",
                }.get(tid, "Hatom Lending")
                errors.append(
                    f"raw_data: {tid} API returned null price/mcap — affects {affected} TVL. "
                    f"Use fallback derivation: token_supply × (prev_token_price/prev_underlying_price) × current_underlying_price"
                )

    # ---------- Check 2: Implausible WoW deltas in protocol_breakdown ----------
    pb = R.get("defi_activity", {}).get("protocol_breakdown", [])
    # Cross-reference to prev defi_tvl. If EGLD-denominated WoW >25%, flag.
    prev_defi = prev.get("defi_tvl", {})
    prev_egld_price = prev.get("economics", {}).get("egld_price_usd", 0)
    for p in pb:
        wow = p.get("tvl_wow_change_pct")
        if wow is None:
            continue
        if abs(wow) > 25:
            warnings.append(
                f"defi_wow: protocol_breakdown[{p['protocol']}] reports {wow:+.1f}% EGLD WoW — "
                f"verify underlying token data (tvl_usd={p.get('tvl_usd')}, tvl_egld={p.get('tvl_egld')}). "
                f">25% WoW changes in stable DeFi protocols usually indicate missing/null data."
            )

    # ---------- Check 3: Token supply events vs executive_summary surface ----------
    tses = R.get("trend_indicators", {}).get("token_supply_events", [])
    exec_summary_text = " ".join(f.get("finding", "") for f in R.get("executive_summary", []))
    for tse in tses:
        chg = abs(tse.get("change_pct", 0))
        if chg > 5:  # significant supply event
            tid = tse["identifier"]
            tname = tse.get("name", "?")
            # Check whether this is mentioned in any high-visibility section
            mentioned = (
                tid in exec_summary_text or
                tname.lower() in exec_summary_text.lower() or
                any(tid in w.get("item", "") or tname.lower() in w.get("item", "").lower()
                    for w in R.get("watch_list", []))
            )
            if not mentioned:
                warnings.append(
                    f"surface_signal: {tid} ({tname}) supply event {chg:.2f}% NOT surfaced in "
                    f"executive_summary or watch_list — only in trend_indicators. Significant events "
                    f"(>5% supply change) should be in the TL;DR."
                )

    # ---------- Check 4: Unknown-label rate in large_transactions ----------
    lts = R.get("whale_intelligence", {}).get("large_transactions", [])
    if lts:
        unknown = sum(1 for t in lts if t.get("sender_label") == "Unknown" or t.get("receiver_label") == "Unknown")
        pct = 100 * unknown / len(lts)
        if pct > 60:
            warnings.append(
                f"entity_resolution: {pct:.0f}% of large_transactions ({unknown}/{len(lts)}) have at "
                f"least one Unknown party. Consider tracing top recurring unknown addresses to add to "
                f"known-addresses.json."
            )

    # ---------- Check 5: Null-but-derivable fields ----------
    ta = R.get("token_activity", {})
    nulls = sum(1 for t in ta.get("top_by_market_cap", []) if t.get("holders") is None)
    if nulls == len(ta.get("top_by_market_cap", [])) and nulls > 0:
        warnings.append(
            f"derivable_null: top_by_market_cap[].holders all null. Available in raw "
            f"/tokens response as the 'accounts' field — populate in assembler."
        )
    nulls = sum(1 for t in ta.get("top_by_volume", []) if t.get("previous_transactions") is None)
    if nulls == len(ta.get("top_by_volume", [])) and nulls > 0:
        warnings.append(
            f"derivable_null: top_by_volume[].previous_transactions all null. Available in "
            f"prev.top_tokens_by_volume — diff in assembler."
        )

    # ---------- Check 6: Forward-indicator failure tracking ----------
    # If the previous run had recommendations and this run resolved >2 of them in the same
    # direction, that pattern is itself a top finding. Flag if not surfaced.
    # (Heuristic check based on key phrases.)
    last_run_recs = []
    try:
        learn = json.loads((report_path.parent.parent / "data/learnings.json").read_text())
        if len(learn.get("runs", [])) >= 2:
            last_run_recs = learn["runs"][-2].get("recommendations_for_next_run", [])
    except Exception:
        pass
    if last_run_recs:
        # action_items_completed is sometimes a count (int), sometimes a list — handle both
        completed = R.get("meta_learning", {}).get("action_items_completed", 0)
        completed_count = completed if isinstance(completed, int) else len(completed) if isinstance(completed, list) else 0
        if completed_count == 0:
            warnings.append(
                "meta_learning: action_items_completed=0 but previous run had "
                f"{len(last_run_recs)} recommendations. Track each per the failed-forward-indicator rule."
            )

    # ---------- Check 7: APR distribution invariant ----------
    apr_buckets = R.get("staking_intelligence", {}).get("apr_distribution", {}).get("buckets", [])
    total = R.get("staking_intelligence", {}).get("summary", {}).get("total_delegated_egld", 0)
    if apr_buckets and total > 0:
        bucket_total = sum(b.get("total_locked_egld", 0) for b in apr_buckets)
        coverage = 100 * bucket_total / total
        if coverage < 95:
            warnings.append(
                f"apr_coverage: APR buckets cover {coverage:.1f}% of total_delegated_egld "
                f"({bucket_total:,.0f}/{total:,.0f}). The remainder are providers with APR outside "
                f"the 5-10%+ range — investigate or extend buckets."
            )

    # ---------- Check 8: Hatom LSD = SEGLD + SWTAO sanity ----------
    if collected:
        tt = collected.get("tvl_tokens", {})
        segld = tt.get("SEGLD-3ad2d0", {}) if isinstance(tt.get("SEGLD-3ad2d0"), dict) else {}
        swtao = tt.get("SWTAO-356a25", {}) if isinstance(tt.get("SWTAO-356a25"), dict) else {}
        segld_mcap = segld.get("marketCap") or 0
        swtao_mcap = swtao.get("marketCap") or 0
        expected_hatom_lsd = segld_mcap + swtao_mcap
        for p in pb:
            if p["protocol"] == "Hatom Liquid Staking":
                reported = p.get("tvl_usd", 0)
                if abs(reported - expected_hatom_lsd) > 100_000 and expected_hatom_lsd > 0:
                    warnings.append(
                        f"hatom_lsd_sum: protocol_breakdown reports ${reported/1e6:.2f}M but "
                        f"SEGLD+SWTAO sum is ${expected_hatom_lsd/1e6:.2f}M. Discrepancy "
                        f"${(reported-expected_hatom_lsd)/1e6:+.2f}M — verify."
                    )

    return errors, warnings


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    report_path = Path(sys.argv[1])
    collected_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else None
    if not collected_path:
        # Try to infer from report date
        try:
            R = json.loads(report_path.read_text())
            date = R.get("metadata", {}).get("report_date")
            if date:
                inferred = report_path.parent.parent / f"data/collected/{date}.json"
                if inferred.exists():
                    collected_path = inferred
        except Exception:
            pass
    previous_path = report_path.parent.parent / "data/previous.json"

    errors, warnings = audit_report(report_path, collected_path, previous_path)

    if warnings:
        print(f"AUDIT WARNINGS ({len(warnings)}):", file=sys.stderr)
        for w in warnings:
            print(f"  - {w}", file=sys.stderr)
    if errors:
        print(f"\nAUDIT ERRORS ({len(errors)}):", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        print(f"\nFAIL: fix errors before publishing.", file=sys.stderr)
        return 1
    print(f"AUDIT OK ({len(warnings)} warnings, 0 errors) for {report_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
