#!/usr/bin/env python3
"""Snapshot EGLD's long-range price history to a file the dashboard can read.

The pump tracker's "bigger picture" panel normally reads /api/chart, an edge
function proxying CoinGecko. CoinGecko's free tier rate-limits by IP, and when it
returns 429 the edge has nothing to serve, so the panel used to disappear.

A year of daily closes changes once a day, so a committed snapshot is a perfectly
good fallback: the hourly workflow refreshes it, and the panel renders from it
whenever the live proxy is unavailable. Same pattern as market-history.json.
"""

import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

CG = "https://api.coingecko.com/api/v3/coins/elrond-erd-2/market_chart"
OUT = pathlib.Path(__file__).resolve().parents[1] / "dashboard" / "public" / "price-history.json"


def fetch(days: str, extra: str = "") -> list:
    """GET one range, retrying through the free tier's rate limit."""
    url = f"{CG}?vs_currency=usd&days={days}{extra}"
    delay = 5.0
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={"accept": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r).get("prices", [])
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 5:
                raise
            print(f"  429 on days={days}, waiting {delay:.0f}s", file=sys.stderr)
            time.sleep(delay)
            delay *= 2
    return []


def thin(pairs: list, target: int) -> list:
    """Match the edge function's thinning so both sources look identical."""
    if len(pairs) <= target:
        out = list(pairs)
    else:
        step = len(pairs) / target
        out = [pairs[int(i * step)] for i in range(target)]
        if out[-1][0] != pairs[-1][0]:
            out.append(pairs[-1])
    return [[int(t), round(float(p), 4)] for t, p in out]


def main() -> int:
    year = thin(fetch("365", "&interval=daily"), 400)
    time.sleep(3)  # be polite between the two calls
    month = thin(fetch("30"), 360)

    if len(year) < 2 or len(month) < 2:
        print("refusing to write a snapshot with no usable series", file=sys.stderr)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "year": year,
                "month": month,
                "fetchedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
            separators=(",", ":"),
        )
        + "\n"
    )
    lo = min(p for _, p in year)
    hi = max(p for _, p in year)
    print(f"wrote {OUT.name}: {len(year)} daily + {len(month)} hourly, 1y range ${lo}–${hi}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
