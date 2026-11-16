#!/usr/bin/env bash
# Run #37: rebuild the report end to end from data/collected (no API calls).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/assemble_run37_report.py >/dev/null
python3 scripts/assemble_run37_stage2.py
python3 scripts/inject_reward_behavior.py --report reports/2026-11-16.json --source data/collected/delegator_behavior_2026-11-16.json >/dev/null
python3 scripts/postfix_run37.py
python3 scripts/markdown_run37.py
