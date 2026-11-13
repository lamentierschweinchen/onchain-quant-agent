"""Shared helpers for weekly report assemblers (import, do not copy per run).

The run #35/#36 assemblers built each report with `copy.deepcopy(last_week)` and
overwrote what they recomputed. Every field they forgot shipped last week's value
and passed every gate. `blank_template` keeps last week's *shape* (sections, list
rows, identity fields) but blanks every measured value to None, so a forgotten
field shows up as missing ("—" on the dashboard, a non-null invariant failure in
validate_report.py) instead of silently stale. Read previous values from the
original report object, never from the blanked copy.

`load_previous` returns the snapshot taken BEFORE a given report date. The
updater overwrites data/previous.json at the end of a run, so re-running an
assembler afterwards used to compute deltas against itself (run #36).
"""
from __future__ import annotations
import copy
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HISTORY = REPO / "data" / "previous_history"

# Fields that describe WHAT a row is, not a measurement; kept so list rows and
# tables keep their structure. Anything else is blanked.
IDENTITY = {"protocol", "category", "addresses_tracked", "name", "identity", "address", "provider_address",
            "label", "identifier", "ticker", "exchange", "venue", "entity", "metric", "id", "threshold_egld",
            "min_apr_pct", "max_apr_pct", "tier", "source", "wallets_count"}
# Whole sections that are ledgers carried forward by design.
KEEP_SECTIONS = {"pre_committed_tests", "meta_learning", "metadata"}


def _blank(obj, key=None):
    if isinstance(obj, dict):
        return {k: (copy.deepcopy(v) if k in IDENTITY else _blank(v, k)) for k, v in obj.items()}
    if isinstance(obj, list):
        if all(isinstance(x, dict) for x in obj):
            return [_blank(x) for x in obj]
        return []          # scalar lists (series, findings) must be rebuilt, not inherited
    return None


def blank_template(prev_report: dict) -> dict:
    """Last week's report with every measured value set to None (see module doc)."""
    return {k: (copy.deepcopy(v) if k in KEEP_SECTIONS else _blank(v)) for k, v in prev_report.items()}


def archive_previous(previous: dict) -> Path:
    """Write data/previous_history/<snapshot_date>.json. Call BEFORE overwriting data/previous.json."""
    HISTORY.mkdir(parents=True, exist_ok=True)
    out = HISTORY / f"{previous['snapshot_date']}.json"
    out.write_text(json.dumps(previous))
    return out


def load_previous(report_date: str) -> dict:
    """The latest snapshot strictly before report_date (archive first, then data/previous.json)."""
    cands = sorted(p for p in HISTORY.glob("20??-??-??.json") if p.stem < report_date) if HISTORY.exists() else []
    cur = REPO / "data" / "previous.json"
    if cur.exists():
        c = json.loads(cur.read_text())
        if c.get("snapshot_date", "") < report_date and (not cands or c["snapshot_date"] > cands[-1].stem):
            return c
    if not cands:
        raise FileNotFoundError(f"no previous snapshot before {report_date}")
    return json.loads(cands[-1].read_text())
