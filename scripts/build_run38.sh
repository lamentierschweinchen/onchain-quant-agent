#!/usr/bin/env bash
# Run #38: rebuild the report end to end from data/collected (no API calls).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/assemble_run38_report.py >/dev/null
python3 scripts/assemble_run38_stage2.py
python3 scripts/inject_reward_behavior.py --report reports/2026-11-23.json --source data/collected/delegator_behavior_2026-11-23.json >/dev/null
python3 scripts/postfix_run38.py
python3 scripts/markdown_run38.py
