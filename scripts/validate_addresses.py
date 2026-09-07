#!/usr/bin/env python3
"""Pre-flight bech32 validation for every tracked MultiversX address.

Closes a recommendation that has been open since run #12, when an invalid-checksum
Binance address in watch_addresses silently returned nothing (HTTP 400) and caused
the Binance entity to be undercounted by ~222K EGLD. Run #18 hit the same bug a
second time: run #17's KuCoin watch entry
(erd1ty4pvmjtl3mnsjvnsxqkm3xqm4dm7ppgz9sh4nk4tqvlmw0jyggqzn4mdc) is not a valid
bech32 string, so the KuCoin resolution test came back empty rather than erroring.

Run this BEFORE the collector. Exit code 1 if any tracked address is invalid.

    python3 scripts/validate_addresses.py
"""
import json, sys, os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
HRP = "erd"
CURRENT_RUN = 24

def _polymod(values):
    gen = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for v in values:
        b = chk >> 25
        chk = ((chk & 0x1ffffff) << 5) ^ v
        for i in range(5):
            chk ^= gen[i] if ((b >> i) & 1) else 0
    return chk

def _hrp_expand(hrp):
    return [ord(c) >> 5 for c in hrp] + [0] + [ord(c) & 31 for c in hrp]

def bech32_valid(addr):
    """True if addr is a well-formed erd1 bech32 string with a valid checksum."""
    if not isinstance(addr, str) or not addr.startswith(HRP + "1"):
        return False
    if addr.lower() != addr and addr.upper() != addr:
        return False
    addr = addr.lower()
    data_part = addr[len(HRP) + 1:]
    if len(data_part) < 6:
        return False
    data = []
    for c in data_part:
        if c not in CHARSET:
            return False
        data.append(CHARSET.index(c))
    return _polymod(_hrp_expand(HRP) + data) == 1

def collect_addresses():
    """Yield (source, address, label) for every address the pipeline relies on."""
    kn_path = os.path.join(REPO, "data", "known-addresses.json")
    kn = json.load(open(kn_path))
    for section, entries in kn.items():
        if not isinstance(entries, dict) or section == "_metadata":
            continue
        for addr, meta in entries.items():
            if isinstance(addr, str) and addr.startswith("erd1"):
                name = meta.get("name", "?") if isinstance(meta, dict) else "?"
                yield f"known-addresses.json:{section}", addr, name

    prev_path = os.path.join(REPO, "data", "previous.json")
    if os.path.exists(prev_path):
        prev = json.load(open(prev_path))
        for w in prev.get("watch_addresses", []):
            yield "previous.json:watch_addresses", w.get("address", ""), w.get("label", "?")[:60]
        for a in prev.get("top_accounts", []):
            yield "previous.json:top_accounts", a.get("address", ""), a.get("label", "?")

    # run #23 rec #6: the collector hardcodes addresses too. Run #23 shipped an
    # invalid Binance hot wallet directly in collect_run23.py, got HTTP 400, and
    # printed "0 outbound recipients >=10K" - which would have resolved a
    # pre-committed test on fabricated evidence. Grep every erd1 literal out of
    # scripts/*.py and check it the same way.
    import glob, re
    # A full MultiversX bech32 address is exactly 62 characters. Anything
    # shorter in source is a deliberate prefix or a truncated label in a print
    # statement, not an address the collector will query, so only full-length
    # literals are checked. Scripts from earlier runs are frozen artifacts:
    # only the current run's collector and the unversioned shared scripts are
    # live enough for a failure here to matter.
    lit = re.compile(r"\berd1[0-9a-z]{58}\b")
    runnum = re.compile(r"run(\d+)")
    for path in sorted(glob.glob(os.path.join(REPO, "scripts", "*.py"))):
        base = os.path.basename(path)
        if base == "validate_addresses.py":
            continue  # its docstring quotes known-bad addresses on purpose
        m = runnum.search(base)
        if m and int(m.group(1)) < CURRENT_RUN:
            continue
        try:
            src = open(path, encoding="utf-8").read()
        except Exception:
            continue
        for a in dict.fromkeys(lit.findall(src)):
            yield f"scripts/{base}", a, "hardcoded literal"

def main():
    bad, total, seen = [], 0, set()
    for source, addr, label in collect_addresses():
        key = (source, addr)
        if key in seen:
            continue
        seen.add(key)
        total += 1
        if not bech32_valid(addr):
            bad.append((source, addr, label))
    print(f"checked {total} tracked addresses")
    if bad:
        print(f"\nINVALID ({len(bad)}):")
        for source, addr, label in bad:
            print(f"  [{source}] {addr}  <- {label}")
        print("\nThese return HTTP 400 and SILENTLY produce no balance and no transactions.")
        print("Fix them in the source file before running the collector.")
        return 1
    print("all addresses pass bech32 checksum validation")
    return 0

if __name__ == "__main__":
    sys.exit(main())
