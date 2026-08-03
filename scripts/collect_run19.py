#!/usr/bin/env python3
"""Run #19 data collection for MultiversX weekly intel report (2026-08-03).

Implements run #18's recommendations:
  #1 trace the Binance custody reload origin (erd1r3w62vq 30d inbound)
  #3 do the OTC desks stay dead (paginated throughput, UPbit balance)
  #4 INSTRUMENT DEMAND: identifiable-bid wallets, per-pair depth ratio inputs,
     withdrawal breadth (distinct addresses receiving >1,000 EGLD from exchanges)
  #7 backfill the OTC series one window further (run #12, Jun 8-15)
  #8 pi-staking - the only persistent growth story
"""
import json, time, urllib.request, urllib.parse, os, sys, base64
from datetime import datetime, timezone

API = "https://api.multiversx.com"
OUT = "/tmp/run19"
os.makedirs(OUT, exist_ok=True)

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
kn = json.load(open(f"{REPO}/data/known-addresses.json"))
prev = json.load(open(f"{REPO}/data/previous.json"))

def ts(y, m, d):
    return int(datetime(y, m, d, 0, 0, 0, tzinfo=timezone.utc).timestamp())

SEVEN_DAYS_AGO    = ts(2026, 7, 27)
ONE_DAY_AGO       = ts(2026, 8, 2)
FOURTEEN_DAYS_AGO = ts(2026, 7, 20)
THIRTY_DAYS_AGO   = ts(2026, 7, 4)

def get(path, params=None, retries=2):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(retries+1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"intel-agent/19"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt == retries:
                return {"__error__": str(e), "__url__": url}
            time.sleep(1.0)

def getraw(url, retries=2):
    for attempt in range(retries+1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"intel-agent/19"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt == retries:
                return {"__error__": str(e)}
            time.sleep(1.0)

def paged_txs(addr, after, before=None, direction="sender", page=50, max_pages=60):
    """Page /accounts/{addr}/transactions to the after= boundary (run #17/#18 rule)."""
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

# --- 1.1 macro -------------------------------------------------------------
step("economics", get("/economics"), "/economics")
step("stats", get("/stats"), "/stats")
step("top_accounts", get("/accounts", {"size":100,"sort":"balance","order":"desc"}), "/accounts?sort=balance")

# --- 1.4 tokens ------------------------------------------------------------
step("tokens_holders", get("/tokens", {"size":25,"sort":"accounts","order":"desc"}), "/tokens?sort=accounts")
step("tokens_txs", get("/tokens", {"size":25,"sort":"transactions","order":"desc"}), "/tokens?sort=transactions")
step("tokens_mcap", get("/tokens", {"size":25,"sort":"marketCap","order":"desc"}), "/tokens?sort=marketCap")

# --- 1.5 staking -----------------------------------------------------------
step("providers", get("/providers", {"size":200,"sort":"locked","order":"desc"}), "/providers?size=200")
step("identities", get("/identities"), "/identities")

# --- 1.6 mex ---------------------------------------------------------------
step("mex_economics", get("/mex/economics"), "/mex/economics")
step("mex_pairs", get("/mex/pairs", {"size":25}), "/mex/pairs")
step("mex_tokens", get("/mex/tokens", {"size":50}), "/mex/tokens")

# --- 1.9 cross-chain -------------------------------------------------------
D["btc_eth"] = getraw("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true")
if isinstance(D["btc_eth"], dict) and "__error__" not in D["btc_eth"]:
    ok.append("coingecko/simple/price")
else:
    failed.append("coingecko/simple/price")
time.sleep(0.2)

# --- entity maps -----------------------------------------------------------
label_map, cat_map = {}, {}
for section, entries in kn.items():
    if not isinstance(entries, dict) or section == "_metadata":
        continue
    for addr, meta in entries.items():
        if isinstance(meta, dict) and addr.startswith("erd1"):
            label_map[addr] = meta.get("name","Unknown")
            cat_map[addr] = meta.get("category","unknown")

exchange_addrs = [a for a,c in cat_map.items() if c == "exchange"]

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

UPBIT_OTC = "erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
OTC_DIST  = "erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
MEGA_WHALE = "erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"
CB_ROUTING_A = "erd1eae23a530qymlpvfrudzsge5wgl003wl92saax74cew7j549eqqq3jklut"  # run #18 watch entry
CB_ROUTING_B = "erd1lgdltequh7627rtlacmcp6p5vec7zmu2rxhu7pjwvcja8f4a9gqq9vcc70"  # known-addresses label
CUSTODY_FUNDER = "erd1r3w62vqmsux5e38p6vnueatmfcs8nr5lmg3s97x6rafqpgxfae0sxv9z0v"
BINANCE_CUSTODY = "erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"
BINANCE_HOT = "erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp29trp6qsl2gdvvz2eqra76xc"

otc_trace = {
    "erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh":"Unknown Whale erd17l22 (OTC source)",
    "erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp":"OTC source funder erd12tq6ax5k",
    MEGA_WHALE:"Unknown Mega Whale erd18mv2z6r2",
    "erd1nhtq4mj3jzlz35l6szpkp0cagss803l6crwq8zjjpuykfsxwj0dsg2c2gu":"OTC Source-Chain Router",
    UPBIT_OTC:"UPbit OTC Desk",
    OTC_DIST:"OTC Distribution Wallet",
    BINANCE_CUSTODY:"Binance Staking custody",
    BINANCE_HOT:"Binance.com hot",
    CUSTODY_FUNDER:"Binance custody reload funder erd1r3w62vq",
    CB_ROUTING_A:"Coinbase Routing/Custody erd1eae23a5",
    CB_ROUTING_B:"Coinbase Routing Wallet erd1lgdltequ",
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
print(f"[accounts] queried {len(acc_data)}")

# ---------------------------------------------------------------------------
# PAGINATED OTC THROUGHPUT (default since run #18)
# ---------------------------------------------------------------------------
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
ok.append("paginated desk in/outbound")

# Run #18 recommendation #7: extend the comparable series one window back (run #12).
BACKFILL_WINDOWS = {"run12_jun08_jun15": (ts(2026,6,8), ts(2026,6,15))}
D["otc_backfill"] = {}
for wname, (aft, bef) in BACKFILL_WINDOWS.items():
    wdata = {}
    for d_addr, d_label in DESKS.items():
        txs = paged_txs(d_addr, aft, before=bef, direction="sender")
        wdata[d_addr] = {"label":d_label, "txs":txs}
        print(f"[backfill] {wname} {d_label}: {len(txs)} txs")
    D["otc_backfill"][wname] = wdata
ok.append("OTC throughput backfill run #12 window (paginated)")

# ---------------------------------------------------------------------------
# RECOMMENDATION #1 - trace the Binance custody reload origin
# ---------------------------------------------------------------------------
D["custody_funder_inbound_30d"]  = paged_txs(CUSTODY_FUNDER, THIRTY_DAYS_AGO, direction="receiver", max_pages=10)
D["custody_funder_outbound_30d"] = paged_txs(CUSTODY_FUNDER, THIRTY_DAYS_AGO, direction="sender",  max_pages=10)
D["binance_custody_out_7d"] = paged_txs(BINANCE_CUSTODY, SEVEN_DAYS_AGO, direction="sender", max_pages=10)
D["binance_custody_in_7d"]  = paged_txs(BINANCE_CUSTODY, SEVEN_DAYS_AGO, direction="receiver", max_pages=10)
ok.append("Binance custody reload funder trace (30d, paginated)")
print(f"[custody] funder inbound30d={len(D['custody_funder_inbound_30d'])} outbound30d={len(D['custody_funder_outbound_30d'])}")

# ---------------------------------------------------------------------------
# RECOMMENDATION #4 - INSTRUMENT THE DEMAND SIDE
# ---------------------------------------------------------------------------
# (a) identifiable bid: the absorber + the pipes that feed it
D["mega_whale_inbound"]  = paged_txs(MEGA_WHALE, SEVEN_DAYS_AGO, direction="receiver")
D["mega_whale_outbound"] = paged_txs(MEGA_WHALE, SEVEN_DAYS_AGO, direction="sender")
for nm, ad in [("cb_routing_a", CB_ROUTING_A), ("cb_routing_b", CB_ROUTING_B)]:
    D[f"{nm}_in_7d"]  = paged_txs(ad, SEVEN_DAYS_AGO, direction="receiver", max_pages=6)
    D[f"{nm}_out_7d"] = paged_txs(ad, SEVEN_DAYS_AGO, direction="sender",  max_pages=6)
ok.append("identifiable-bid instrument (absorber + Coinbase routing pipes)")

# (c) withdrawal breadth: distinct addresses receiving >1,000 EGLD from exchange hot wallets
BREADTH_EXCHANGES = {
    BINANCE_HOT: "Binance.com hot",
    "erd1s7wsfsuwrhrcy8dnpp5s9gcqsvxkmz3f7ma9sy0v4pu3rqedkc0shcnyaz": "Bybit",
    "erd1ty4pvmjtl3mnsjvnsxgcpedd08fsn83f05tu0v5j23wnfce9p86snlkdyy": "KuCoin",
    "erd16jruked88jgtsar78ej85hjp3qsd9jkjcw4swsn7k0teqh3wgcqqgyrupq": "Coinbase",
    "erd1qk0hepsl9jlgvsqmmhs4y2h6ll75dqyp0fzvpj3lqmmnkwavdxpqcrnjs2": "UPbit",
    "erd1rhp4q3qlydyrrjt7dgpfzxk8n4f7yenv7ss7v2location": None,  # placeholder removed below
}
BREADTH_EXCHANGES = {k:v for k,v in BREADTH_EXCHANGES.items() if v}
# add any exchange address present in known-addresses that we did not hard-code
for a in exchange_addrs:
    if a not in BREADTH_EXCHANGES:
        BREADTH_EXCHANGES[a] = label_map[a]
D["exchange_outbound_paged"] = {}
for a, lab in BREADTH_EXCHANGES.items():
    txs = paged_txs(a, SEVEN_DAYS_AGO, direction="sender", max_pages=8)
    D["exchange_outbound_paged"][a] = {"label":lab, "txs":txs}
    if txs:
        print(f"[breadth] {lab}: {len(txs)} outbound txs")
ok.append("withdrawal-breadth scan (paginated exchange outbound)")

# ---------------------------------------------------------------------------
# RECOMMENDATION #8 - pi-staking, the only persistent growth story
# ---------------------------------------------------------------------------
pi_addr = None
if isinstance(D["providers"], list):
    for p in D["providers"]:
        if str(p.get("identity","")).lower() == "pi-staking" or "pi-staking" in str(p.get("identity","")).lower():
            pi_addr = p.get("provider")
            break
D["pi_staking_provider_addr"] = pi_addr
if pi_addr:
    D["pi_staking_inbound_7d"] = paged_txs(pi_addr, SEVEN_DAYS_AGO, direction="receiver", max_pages=8)
    D["pi_staking_identity"] = get("/identities/pi-staking")
    time.sleep(0.2)
    ok.append("pi-staking provider inbound scan")
    print(f"[pi-staking] {pi_addr} inbound txs 7d: {len(D['pi_staking_inbound_7d'])}")

# ---------------------------------------------------------------------------
# DeFi protocol activity + balances
# ---------------------------------------------------------------------------
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

for sid in ["USDC-c76f1f","USDT-f8c08c"]:
    D[f"stable_{sid}"] = get(f"/tokens/{sid}")
    time.sleep(0.5)

D["emrs_token"] = get("/tokens/EMRS-6e4067")
time.sleep(0.2)
D["zpay_token"] = get("/tokens/ZPAY-247875")
time.sleep(0.2)
D["wegld_token"] = get("/tokens/WEGLD-bd4d79")
time.sleep(0.2)

# --- newly issued tokens (ESDT system SC scan) -----------------------------
ESDT_SYS = "erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u"
issues_data = get(f"/accounts/{ESDT_SYS}/transactions",
              {"size":50,"after":SEVEN_DAYS_AGO,"order":"desc","status":"success","function":"issue"})
D["esdt_sys_issues_raw"] = issues_data
time.sleep(0.2)

prev_ids = set()
for k in ("top_tokens_by_holders","top_tokens_by_volume"):
    for t in prev.get(k, []):
        if isinstance(t, dict) and t.get("identifier"):
            prev_ids.add(t["identifier"])

newly_issued = []
if isinstance(issues_data, list):
    seen_tickers = set()
    for tx in issues_data[:30]:
        data_field = tx.get("data", "")
        if not data_field:
            continue
        try:
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
                    if not tid.startswith(ticker+"-"):
                        continue
                    # run #15 guard: an established token resolved by name-search is a false positive
                    if tok.get("accounts",0) > 1000 or tid in prev_ids:
                        continue
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

# --- save ------------------------------------------------------------------
json.dump(D, open(f"{OUT}/collected.json","w"))
json.dump({"ok":ok,"failed":failed}, open(f"{OUT}/status.json","w"))
os.makedirs(f"{REPO}/data/collected", exist_ok=True)
json.dump(D, open(f"{REPO}/data/collected/2026-08-03.json","w"))
print("Saved canonical snapshot to data/collected/2026-08-03.json")

print("=== ECONOMICS ===")
print(json.dumps(D["economics"], indent=0)[:600])
st = D["stats"]
if isinstance(st, dict):
    print({k:st.get(k) for k in ["accounts","transactions","epoch","blocks","shards"]})
print("\n=== STATUS ok=%d failed=%d ===" % (len(ok), len(failed)))
print("FAILED:", failed)
print("=== providers:", len(D["providers"]) if isinstance(D["providers"],list) else D["providers"])
print("=== btc_eth:", D["btc_eth"])
print("=== dataapi_refetch_log:", json.dumps(refetch_log))
print("=== newly_issued:", len(newly_issued))
for t in newly_issued: print("    ", t["identifier"], t["name"], t["accounts"], "holders")
