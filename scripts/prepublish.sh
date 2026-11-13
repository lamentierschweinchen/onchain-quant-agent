#!/usr/bin/env bash
# Single pre-publish gate. Run before generate-manifest / commit / deploy.
#   scripts/prepublish.sh 2026-11-16
# Fails (non-zero) on the first gate that fails. Each layer catches a different class:
#   1 prose     - machine identifiers leaking into reader-facing text
#   2 audit     - data integrity vs the raw collected snapshot (silent API nulls etc.)
#   3 schema    - schema + dashboard invariants (a bad field blanks the whole page)
#   4 staleness - values silently carried over from last week's report (run #36)
set -euo pipefail
D="${1:?usage: scripts/prepublish.sh YYYY-MM-DD}"
cd "$(dirname "$0")/.."
R="reports/$D.json"
echo "== 1/4 prose";     python3 scripts/lint_report_prose.py "$R"
echo "== 2/4 audit";     python3 scripts/audit_report.py "$R" "data/collected/$D.json"
echo "== 3/4 schema";    python3 scripts/validate_report.py "$R"
echo "== 4/4 staleness"; python3 scripts/check_staleness.py "$R"
echo "PREPUBLISH OK: $R"
