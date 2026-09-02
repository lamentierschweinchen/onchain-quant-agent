#!/usr/bin/env python3
"""Append one market reading to the pump tracker's history file.

The tracker shows what the market looks like RIGHT NOW, which tells you which
side is crowded but not whether that is changing. A short book that is crowded
and thinning is the opposite trade to one that is crowded and growing, and a
point-in-time reading cannot tell them apart.

Run this on a schedule (hourly is plenty) to turn the gauge into a series:
    python3 scripts/poll_market.py

Writes dashboard/public/market-history.json — an append-only ring buffer capped
at MAX_POINTS so the file a visitor downloads stays small.
"""
import json
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "dashboard", "public", "market-history.json")
MAX_POINTS = 720  # 30 days at hourly

CG = "https://api.coingecko.com/api/v3"
MX = "https://api.multiversx.com"
DESKS = [
    "erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5",
    "erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r",
]


def get(url, tries=4):
    delay = 1.5
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "egld-pump-tracker/1"})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt == tries - 1:
                raise
            if "429" in str(e):
                delay = min(delay * 2, 20)
            time.sleep(delay)
    raise RuntimeError("unreachable")


def reading():
    mk = get(f"{CG}/coins/markets?" + urllib.parse.urlencode({
        "vs_currency": "usd", "ids": "elrond-erd-2",
        "price_change_percentage": "24h"}))
    time.sleep(2.0)
    egld = mk[0]

    dv = get(f"{CG}/derivatives?include_tickers=unexpired")
    time.sleep(2.0)
    venues = [d for d in dv if str(d.get("symbol") or "").upper().startswith("EGLD")]
    oi = sum(d.get("open_interest") or 0 for d in venues)
    pvol = sum(d.get("volume_24h") or 0 for d in venues)
    fr = [d.get("funding_rate") for d in venues if d.get("funding_rate") is not None]

    econ = get(f"{MX}/economics")
    time.sleep(0.4)
    desks = 0.0
    for a in DESKS:
        acc = get(f"{MX}/accounts/{a}")
        desks += int(acc.get("balance", "0")) / 1e18
        time.sleep(0.4)

    mcap = float(egld.get("market_cap") or 0)
    return {
        "t": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "price": round(float(egld.get("current_price") or 0), 4),
        "change24h": round(float(egld.get("price_change_percentage_24h") or 0), 2),
        "mcap": round(mcap),
        "spotVol": round(float(egld.get("total_volume") or 0)),
        "oi": round(oi),
        "oiShare": round(100 * oi / mcap, 2) if mcap else None,
        "perpVol": round(pvol),
        "funding": round(sum(fr) / len(fr), 5) if fr else None,
        "fundingNeg": sum(1 for f in fr if f < 0),
        "fundingVenues": len(fr),
        "desks": round(desks),
        "staked": round(float(econ.get("staked") or 0)),
    }


def main():
    try:
        hist = json.load(open(OUT))
        points = hist.get("points", [])
    except Exception:
        points = []

    try:
        p = reading()
    except Exception as e:
        print(f"poll failed, history left unchanged: {e}")
        return 1

    # Skip a duplicate if the source has not refreshed since the last point.
    if points and points[-1].get("t") == p["t"]:
        print("duplicate timestamp, skipped")
        return 0

    points.append(p)
    points = points[-MAX_POINTS:]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump({
        "updated": p["t"],
        "note": "Hourly readings for the EGLD pump tracker. funding is the mean "
                "across perp venues; negative means short sellers pay longs. "
                "oiShare is open interest as a percent of market cap.",
        "points": points,
    }, open(OUT, "w"), indent=1)
    print(f"appended {p['t']}  price ${p['price']}  oi ${p['oi']:,}  "
          f"funding {p['funding']}  desks {p['desks']:,}  ({len(points)} points)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
