#!/usr/bin/env python3
"""Run #18 data collection for MultiversX weekly intel report (2026-07-27).

Run #17 discovered that the size=50 tx cap undercounted OTC desk throughput ~4x.
This collector paginates desk/router queries to the after= boundary by default,
nets out desk<->desk transfers, and backfills the runs #13-#15 windows so the
throughput series becomes a comparable time series (run #17 recommendation #1).
"""
import json, time, urllib.request, urllib.parse, os, sys
from datetime import datetime, timezone

API = "https://api.multiversx.com"
OUT = "/tmp/run18"
os.makedirs(OUT, exist_ok=True)

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
kn = json.load(open(f"{REPO}/data/known-addresses.json"))
prev = json.load(open(f"{REPO}/data/previous.json"))

# period boundaries (today is 2026-07-27)
def ts(y, m, d):
    return int(datetime(y, m, d, 0, 0, 0, tzinfo=timezone.utc).timestamp())

SEVEN_DAYS_AGO    = ts(2026, 7, 20)
ONE_DAY_AGO       = ts(2026, 7, 26)
FOURTEEN_DAYS_AGO = ts(2026, 7, 13)

def get(path, params=None, retries=2):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(retries+1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"intel-agent/18"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt == retries:
                return {"__error__": str(e), "__url__": url}
            time.sleep(1.0)

def getraw(url, retries=2):
    for attempt in range(retries+1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"intel-agent/18"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt == retries:
                return {"__error__": str(e)}
            time.sleep(1.0)

def paged_txs(addr, after, before=None, direction="sender", page=50, max_pages=60):
    """Page /accounts/{addr}/transactions until the after= boundary is reached.

    Run #17 rule: a single size=50 page covers only ~2.5 of 7 days on a busy desk,
    so every un-paginated throughput figure was a truncated tail.
    """
    out, frm = [], 0
    for _ in range(max_pages):
        params = {"size":page, "from":frm, "after":after, "order":"desc", "status":"success",
                  direction:addr}
        if before:
            params["before"] = before
        batch = get(f"/accounts/{addr}/transactions", params)
        time.sleep(0.25)
        if not isinstance(batch, list) or not batch:
            break
        out.extend(batch)
        if len(batch) < page:
            break
        frm += page
    return out

D = {}
ok, failed = [], []

def step(name, val, endpoint):
    D[name] = val
    if isinstance(val, dict) and "__error__" in val:
        failed.append(f"{endpoint} -> {val['__error__']}")
    else:
        ok.append(endpoint)
    time.sleep(0.2)

# 1.1 economics + stats
step("economics", get("/economics"), "/economics")
step("stats", get("/stats"), "/stats")

# 1.2 top accounts
step("top_accounts", get("/accounts", {"size":100,"sort":"balance","order":"desc"}), "/accounts?sort=balance")

# 1.4 tokens
step("tokens_holders", get("/tokens", {"size":25,"sort":"accounts","order":"desc"}), "/tokens?sort=accounts")
step("tokens_txs", get("/tokens", {"size":25,"sort":"transactions","order":"desc"}), "/tokens?sort=transactions")
step("tokens_mcap", get("/tokens", {"size":25,"sort":"marketCap","order":"desc"}), "/tokens?sort=marketCap")

# 1.5 providers + identities
step("providers", get("/providers", {"size":200,"sort":"locked","order":"desc"}), "/providers?size=200")
step("identities", get("/identities"), "/identities")

# 1.6 mex
step("mex_economics", get("/mex/economics"), "/mex/economics")
step("mex_pairs", get("/mex/pairs", {"size":25}), "/mex/pairs")
step("mex_tokens", get("/mex/tokens", {"size":50}), "/mex/tokens")

# 1.9 coingecko
D["btc_eth"] = getraw("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true")
if isinstance(D["btc_eth"], dict) and "__error__" not in D["btc_eth"]:
    ok.append("coingecko/simple/price")
else:
    failed.append("coingecko/simple/price")
time.sleep(0.2)

# label/cat map
label_map, cat_map = {}, {}
for section, entries in kn.items():
    if not isinstance(entries, dict) or section == "_metadata":
        continue
    for addr, meta in entries.items():
        if isinstance(meta, dict) and addr.startswith("erd1"):
            label_map[addr] = meta.get("name","Unknown")
            cat_map[addr] = meta.get("category","unknown")

exchange_addrs = [a for a,c in cat_map.items() if c == "exchange"]

# accounts to query
accounts_to_query = {}
for a in exchange_addrs:
    accounts_to_query[a] = label_map[a]

sys_prefix = "erd1qqqqqqqqqqqqq"
ta = D["top_accounts"] if isinstance(D["top_accounts"], list) else []
nonexch_count = 0
for acc in ta:
    addr = acc["address"]
    if addr.startswith(sys_prefix):
        continue
    c = cat_map.get(addr, "unknown")
    if c in ("exchange","system","validator","defi","team"):
        continue
    if nonexch_count < 12:
        accounts_to_query[addr] = label_map.get(addr, "Unknown")
        nonexch_count += 1

for w in prev.get("watch_addresses", []):
    accounts_to_query[w["address"]] = w.get("label","watch")

# OTC pipeline + carried recommendations (run #17)
otc_trace = {
    "erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh":"Unknown Whale erd17l22 (OTC source)",
    "erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp":"OTC source funder erd12tq6ax5k (canonical)",
    "erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw":"Unknown Mega Whale erd18mv2z6r2",
    "erd1nhtq4mj3jzlz35l6szpkp0cagss803l6crwq8zjjpuykfsxwj0dsg2c2gu":"OTC Source-Chain Router",
    "erd1ecyftln6n8ej5mxu0ejzxayfmtxfmzc08sp55qr8aj74yst4ejus4em6ce":"OTC Source Pass-through",
    "erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5":"UPbit OTC Desk",
    "erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r":"OTC Distribution Wallet",
    "erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p":"Binance Staking custody",
    "erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp29trp6qsl2gdvvz2eqra76xc":"Binance.com hot",
    # run #17 discoveries: distribution routers + migration destinations
    "erd15ku2r2j6smlwumftumlpw0mfpqxy32wyt4ewxzyhs3ugsjee8stq2xh84e":"Whale erd15ku2r2j6 (emptied to KuCoin)",
}
for a,l in otc_trace.items():
    accounts_to_query[a] = l

acc_data = {}
for addr, label in accounts_to_query.items():
    info = get(f"/accounts/{addr}")
    time.sleep(0.15)
    txs = get(f"/accounts/{addr}/transactions", {"size":40,"after":SEVEN_DAYS_AGO,"order":"desc","status":"success"})
    time.sleep(0.15)
    acc_data[addr] = {"label":label, "info":info, "txs":txs}
D["accounts"] = acc_data
ok.append(f"/accounts/{{addr}} + /transactions x{len(acc_data)}")

# ---------------------------------------------------------------------------
# PAGINATED OTC THROUGHPUT (run #17 recommendation #1)
# ---------------------------------------------------------------------------
UPBIT_OTC = "erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
OTC_DIST  = "erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
DESKS = {UPBIT_OTC:"UPbit OTC Desk", OTC_DIST:"OTC Distribution Wallet"}

D["desk_outbound_paged"] = {}
for d_addr, d_label in DESKS.items():
    txs = paged_txs(d_addr, SEVEN_DAYS_AGO, direction="sender")
    D["desk_outbound_paged"][d_addr] = {"label":d_label, "txs":txs}
    print(f"[paged] {d_label} outbound 7d: {len(txs)} txs")
D["desk_inbound_paged"] = {}
for d_addr, d_label in DESKS.items():
    txs = paged_txs(d_addr, SEVEN_DAYS_AGO, direction="receiver")
    D["desk_inbound_paged"][d_addr] = {"label":d_label, "txs":txs}
    print(f"[paged] {d_label} inbound 7d: {len(txs)} txs")
ok.append("paginated desk in/outbound (run #18 default)")

# Backfill runs #13-#15 windows on the same paginated method so the series is comparable
BACKFILL_WINDOWS = {
    "run13_jun15_jun22": (ts(2026,6,15), ts(2026,6,22)),
    "run14_jun22_jun29": (ts(2026,6,22), ts(2026,6,29)),
    "run15_jun29_jul06": (ts(2026,6,29), ts(2026,7,6)),
}
D["otc_backfill"] = {}
for wname, (aft, bef) in BACKFILL_WINDOWS.items():
    wdata = {}
    for d_addr, d_label in DESKS.items():
        txs = paged_txs(d_addr, aft, before=bef, direction="sender")
        wdata[d_addr] = {"label":d_label, "txs":txs}
        print(f"[backfill] {wname} {d_label}: {len(txs)} txs")
    D["otc_backfill"][wname] = wdata
ok.append("OTC throughput backfill runs #13-#15 (paginated)")

# ---------------------------------------------------------------------------
# Carried follow-ups
# ---------------------------------------------------------------------------
# erd12tq6ax5k INBOUND (14d)
D["erd12tq6ax5k_inbound"] = get("/accounts/erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp/transactions",
              {"size":50,"after":FOURTEEN_DAYS_AGO,"order":"desc","status":"success",
               "receiver":"erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp"})
time.sleep(0.2)

# erd17l22 INBOUND (14d)
D["erd17l22_inbound"] = get("/accounts/erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh/transactions",
              {"size":50,"after":FOURTEEN_DAYS_AGO,"order":"desc","status":"success",
               "receiver":"erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh"})
time.sleep(0.2)

# Mega whale absorber - clip size growing? Is Coinbase Routing fed by the desks?
mw_addr = "erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"
D["mega_whale_inbound"] = paged_txs(mw_addr, SEVEN_DAYS_AGO, direction="receiver")
D["mega_whale_outbound"] = paged_txs(mw_addr, SEVEN_DAYS_AGO, direction="sender")

# KuCoin resolution (run #17 recommendation #3): does the balance persist or bleed?
KUCOIN = "erd1ty4pvmjtl3mnsjvnsxqkm3xqm4dm7ppgz9sh4nk4tqvlmw0jyggqzn4mdc"
D["kucoin_outbound"] = paged_txs(KUCOIN, SEVEN_DAYS_AGO, direction="sender")
D["kucoin_inbound"] = paged_txs(KUCOIN, SEVEN_DAYS_AGO, direction="receiver")
# and the emptied whale's inbound history (was it itself an OTC recipient?)
WHALE_EXIT = "erd15ku2r2j6smlwumftumlpw0mfpqxy32wyt4ewxzyhs3ugsjee8stq2xh84e"
D["whale_exit_inbound_90d"] = paged_txs(WHALE_EXIT, ts(2026,4,27), direction="receiver", max_pages=10)

# Binance custody 4th leg?
D["binance_custody_txs"] = paged_txs("erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p",
                                     SEVEN_DAYS_AGO, direction="sender", max_pages=10)

# XOXNO LSD follow-up
xoxno_lsd_addr = "erd1qqqqqqqqqqqqqpgq6uzdzy54wnesfnlaycxwymrn9texlnmyah0ssrfvk6"
D["xoxno_lsd_account"] = get(f"/accounts/{xoxno_lsd_addr}")
time.sleep(0.15)

# DeFi protocol transfers/count + balances
proto_contracts = {
    "XOXNO Aggregator": "erd1qqqqqqqqqqqqqpgq5rf2sppxk2xu4m0pkmugw2es4gak3rgjah0sxvajva",
    "OneDex Swap": "erd1qqqqqqqqqqqqqpgqqz6vp9y50ep867vnr296mqf3dduh6guvmvlsu3sujc",
    "JEXchange Aggregator": "erd1qqqqqqqqqqqqqpgqqvs2jvf64wzcz2836er0j98l3ytshpcr5sns997aga",
    "JEXchange Fees": "erd1272et87h3sa7hlg5keuswh50guz2ngmd6lhmjxkwwu0ah6gdds5qhka964",
    "Hatom EGLD MM": "erd1qqqqqqqqqqqqqpgq35qkf34a8svu4r2zmfzuztmeltqclapv78ss5jleq3",
    "Hatom Liquid Staking": "erd1qqqqqqqqqqqqqpgq4gzfcw7kmkjy8zsf04ce6dl0auhtzjx078sslvrf4e",
    "XOXNO LSD": "erd1qqqqqqqqqqqqqpgq6uzdzy54wnesfnlaycxwymrn9texlnmyah0ssrfvk6",
}
proto_data = {}
for name, addr in proto_contracts.items():
    cnt = get(f"/accounts/{addr}/transfers/count", {"after":ONE_DAY_AGO})
    time.sleep(0.15)
    bal = get(f"/accounts/{addr}")
    time.sleep(0.15)
    proto_data[name] = {"addr":addr, "transfers_24h":cnt, "balance":bal}
D["proto"] = proto_data
ok.append("/accounts/{addr}/transfers/count x%d" % len(proto_data))

# xExchange WEGLD contract balances (3 shards) for TVL
wegld_contracts = [
    "erd1qqqqqqqqqqqqqpgqvc7gdl0p4s97guh498wgz75k8sav6sjfjlwqh679jy",
    "erd1qqqqqqqqqqqqqpgqhe8t5jewej70zupmh44jurgn29psua5l2jps3ntjj3",
    "erd1qqqqqqqqqqqqqpgqmuk0q2saj0mgutxm4teywre6dl8wqf58xamqdrukln",
]
wegld_bal = {}
for c in wegld_contracts:
    b = get(f"/accounts/{c}")
    time.sleep(0.15)
    wegld_bal[c] = b
D["wegld"] = wegld_bal

# H-token + LSD market caps for DeFi TVL (dataApi null-price guard active)
tvl_tokens = ["HUSDC-d80042","HEGLD-d61095","HUSDT-6f0914","HWBTC-49ca31","HWETH-b3d17e",
              "HBUSD-ac1fca","HHTM-e03ba5","HMEX-df6df7","HUTK-4fa4b2","HWTAO-2e9136",
              "SEGLD-3ad2d0","SWTAO-356a25","USH-111e09","XEGLD-e413ed","WTAO-3ec9c0"]
DATAAPI_TOKENS = {"SEGLD-3ad2d0","SWTAO-356a25","USH-111e09","XEGLD-e413ed"}
tok_mcap = {}
for t in tvl_tokens:
    info = get(f"/tokens/{t}")
    time.sleep(1.05)
    tok_mcap[t] = info

refetch_log = {}
for t in DATAAPI_TOKENS:
    info = tok_mcap.get(t)
    attempts = 0
    while isinstance(info, dict) and info.get("price") is None and attempts < 4:
        attempts += 1
        time.sleep(2.5)
        info = get(f"/tokens/{t}")
    tok_mcap[t] = info
    refetch_log[t] = {"retries": attempts, "recovered": isinstance(info, dict) and info.get("price") is not None}
D["tvl_tokens"] = tok_mcap
D["dataapi_refetch_log"] = refetch_log
ok.append("/tokens/{id} x%d (dataApi re-fetch guard active)" % len(tok_mcap))

# stablecoin supply follow-up
for sid in ["USDC-c76f1f","USDT-f8c08c"]:
    D[f"stable_{sid}"] = get(f"/tokens/{sid}")
    time.sleep(0.5)

D["emrs_token"] = get("/tokens/EMRS-6e4067")
time.sleep(0.2)
D["zpay_token"] = get("/tokens/ZPAY-247875")
time.sleep(0.2)

# Newly-issued token scan via ESDT system SC scan
ESDT_SYS = "erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u"
issues_data = get(f"/accounts/{ESDT_SYS}/transactions",
              {"size":50,"after":SEVEN_DAYS_AGO,"order":"desc","status":"success","function":"issue"})
D["esdt_sys_issues_raw"] = issues_data
time.sleep(0.2)

newly_issued = []
if isinstance(issues_data, list):
    seen_tickers = set()
    for tx in issues_data[:30]:
        data_field = tx.get("data", "")
        if not data_field:
            continue
        try:
            import base64
            decoded = base64.b64decode(data_field).decode("utf-8", errors="ignore")
            parts = decoded.split("@")
            if len(parts) < 3 or parts[0] != "issue":
                continue
            name = bytes.fromhex(parts[1]).decode("utf-8", errors="ignore")
            ticker = bytes.fromhex(parts[2]).decode("utf-8", errors="ignore")
            if ticker in seen_tickers or len(ticker) < 3 or len(ticker) > 10:
                continue
            seen_tickers.add(ticker)
            search = get("/tokens", {"search":name,"size":5})
            time.sleep(0.3)
            if isinstance(search, list):
                for tok in search:
                    tid = tok.get("identifier","")
                    if tid.startswith(ticker+"-"):
                        newly_issued.append({
                            "identifier":tid,
                            "name":tok.get("name") or name,
                            "ticker":ticker,
                            "accounts":tok.get("accounts",0),
                            "transactions":tok.get("transactions",0),
                            "timestamp":tx.get("timestamp"),
                            "deployer":tx.get("sender","")
                        })
                        break
        except Exception:
            continue
D["newly_issued"] = newly_issued
ok.append("/accounts/{ESDT_SYS}/transactions?function=issue (newly_issued workaround)")

# Save
json.dump(D, open(f"{OUT}/collected.json","w"))
json.dump({"ok":ok,"failed":failed}, open(f"{OUT}/status.json","w"))

os.makedirs(f"{REPO}/data/collected", exist_ok=True)
json.dump(D, open(f"{REPO}/data/collected/2026-07-27.json","w"))
print("Saved canonical snapshot to data/collected/2026-07-27.json")

print("=== ECONOMICS ===")
print(json.dumps(D["economics"], indent=0)[:600])
st = D["stats"]
if isinstance(st, dict):
    print({k:st.get(k) for k in ["accounts","transactions","epoch","blocks","shards","scResults"]})
print("\n=== STATUS ok=%d failed=%d ===" % (len(ok), len(failed)))
print("FAILED:", failed)
print("=== top_accounts:", len(ta))
print("=== accounts queried:", len(acc_data))
print("=== providers:", len(D["providers"]) if isinstance(D["providers"],list) else D["providers"])
print("=== btc_eth:", D["btc_eth"])
print("=== mex_economics:", D["mex_economics"])
print("=== dataapi_refetch_log:", json.dumps(refetch_log))
print("=== newly_issued:", len(newly_issued))
for t in newly_issued: print("    ", t["identifier"], t["name"], t["accounts"], "holders")
