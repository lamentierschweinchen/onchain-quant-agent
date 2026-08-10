#!/usr/bin/env python3
"""Run #20 data collection for MultiversX intel report (2026-08-10).

CADENCE: previous snapshot is 2026-08-03 -> this is a clean 7-DAY window
(2026-08-03 -> 2026-08-10). All flow/throughput windows use it, so every
figure is directly comparable to the run #13-#19 weekly series.

The run #17 PEAK-window re-net (rec #1) was already executed against a FIXED
historical window (Jul 13-20) during the 2026-08-05 interim collection; it is
carried forward from data/collected/2026-08-05.json rather than re-queried.

Implements run #19's recommendations:
  #1 RE-NET THE RUN #17 PEAK WINDOW (Jul 13-20) for circularity - the top item
  #2 fold the two-hop both-legs OTC hub netting into the COLLECTOR
  #3 does the UPbit reload escalate (desk feed tranches + UPbit balance)
  #4 identifiable bid - 3rd consecutive zero week promotes to structural
  #5 DEX turnover ratio as a first-class series
  #6 identify 'Unknown Whale I (active)' erd1vd76pwhl4d - 60d inbound trace
  #7 fee response in the delegation market (per-provider serviceFee WoW)
  #8 does USH take a third burn week
"""
import json, time, urllib.request, urllib.parse, os, sys, base64
from datetime import datetime, timezone

API = "https://api.multiversx.com"
REPORT_DATE = "2026-08-10"
OUT = "/tmp/run20w"
os.makedirs(OUT, exist_ok=True)

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
kn = json.load(open(f"{REPO}/data/known-addresses.json"))
prev = json.load(open(f"{REPO}/data/previous.json"))

def ts(y, m, d):
    return int(datetime(y, m, d, 0, 0, 0, tzinfo=timezone.utc).timestamp())

SEVEN_DAYS_AGO    = ts(2026, 8, 3)    # clean weekly window, no overlap
INTERIM_START     = SEVEN_DAYS_AGO    # alias kept so the body reads unchanged
ONE_DAY_AGO       = ts(2026, 8, 9)
THIRTY_DAYS_AGO   = ts(2026, 7, 11)
SIXTY_DAYS_AGO    = ts(2026, 6, 11)

def get(path, params=None, retries=2):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(retries+1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"intel-agent/20"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt == retries:
                return {"__error__": str(e), "__url__": url}
            time.sleep(1.0)

def getraw(url, retries=2):
    for attempt in range(retries+1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"intel-agent/20"})
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

D = {"_period": {"report_date": REPORT_DATE,
                 "previous_snapshot": prev.get("snapshot_date"),
                 "window_start_ts": SEVEN_DAYS_AGO,
                 "window_days": 7,
                 "note": "clean 7d window 2026-08-03 -> 2026-08-10, comparable to runs #13-#19"}}
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
CB_ROUTING_A = "erd1eae23a530qymlpvfrudzsge5wgl003wl92saax74cew7j549eqqq3jklut"
CB_ROUTING_B = "erd1lgdltequh7627rtlacmcp6p5vec7zmu2rxhu7pjwvcja8f4a9gqq9vcc70"
CUSTODY_FUNDER = "erd1r3w62vqmsux5e38p6vnueatmfcs8nr5lmg3s97x6rafqpgxfae0sxv9z0v"
BINANCE_CUSTODY = "erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"
BINANCE_HOT = "erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp29trp6qsl2gdvvz2eqra76xc"
UNKNOWN_WHALE_I = "erd1vd76pwhl4dyeyd8gylv6mkkvy7g4dnfezjuyp4j4x3wwnauga57q53m3z0"

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
    UNKNOWN_WHALE_I:"Unknown Whale I (active)",
}
for a,l in otc_trace.items():
    accounts_to_query[a] = l

acc_data = {}
for addr, label in accounts_to_query.items():
    info = get(f"/accounts/{addr}")
    time.sleep(0.15)
    txs = get(f"/accounts/{addr}/transactions", {"size":40,"after":INTERIM_START,"order":"desc","status":"success"})
    time.sleep(0.15)
    acc_data[addr] = {"label":label, "info":info, "txs":txs}
D["accounts"] = acc_data
ok.append(f"/accounts/{{addr}} + /transactions x{len(acc_data)}")
print(f"[accounts] queried {len(acc_data)}")

# ---------------------------------------------------------------------------
# OTC THROUGHPUT - interim window (new period) + trailing 7d (context only)
# ---------------------------------------------------------------------------
DESKS = {UPBIT_OTC:"UPbit OTC Desk", OTC_DIST:"OTC Distribution Wallet"}

for tag, after in [("interim", SEVEN_DAYS_AGO)]:
    D[f"desk_outbound_{tag}"] = {}
    D[f"desk_inbound_{tag}"] = {}
    for d_addr, d_label in DESKS.items():
        o = paged_txs(d_addr, after, direction="sender")
        i = paged_txs(d_addr, after, direction="receiver")
        D[f"desk_outbound_{tag}"][d_addr] = {"label":d_label, "txs":o}
        D[f"desk_inbound_{tag}"][d_addr] = {"label":d_label, "txs":i}
        print(f"[paged/{tag}] {d_label}: out={len(o)} in={len(i)}")
ok.append("paginated desk in/outbound (7d)")

# alias for backward-compat with the run #19 assembler shape
D["desk_outbound_paged"] = D["desk_outbound_interim"]
D["desk_inbound_paged"]  = D["desk_inbound_interim"]

# ---------------------------------------------------------------------------
# REC #1 - run #17 PEAK WINDOW re-net: CARRIED FORWARD (fixed historical window,
# already executed in the 2026-08-05 interim collection). No re-query needed.
# ---------------------------------------------------------------------------
try:
    _interim = json.load(open(f"{REPO}/data/collected/2026-08-05.json"))
    D["otc_hub_trace_peak_run17"] = _interim["otc_hub_trace_peak_run17"]
    D["_peak_run17_provenance"] = "carried from data/collected/2026-08-05.json (fixed window Jul 13-20)"
    ok.append("run #17 peak-window re-net (carried forward)")
except Exception as e:
    failed.append(f"peak_run17 carry-forward -> {e}")

# ---------------------------------------------------------------------------
# REC #2 - TWO-HOP BOTH-LEGS HUB NETTING, NOW IN THE COLLECTOR
# ---------------------------------------------------------------------------
def venue_of(addr):
    l = label_map.get(addr)
    if l and cat_map.get(addr) == "exchange":
        for v in ["Binance.com","Binance","UPbit","Bybit","Gate.io","KuCoin",
                  "Coinbase","Crypto.com","MEXC","Bitget","Bitfinex","Tokero"]:
            if v.split(".")[0] in l:
                return v
        return l
    if l and "Whale" in l:
        return l
    return None

_resolve_cache = {}

def resolve_hop(addr, direction, after, before=None):
    """One hop past `addr` (out) or before it (in). Cached across windows."""
    key = (addr, direction, after, before)
    if key in _resolve_cache:
        return _resolve_cache[key]
    v = venue_of(addr)
    if v:
        res = ({v: None}, "direct", None)
        _resolve_cache[key] = res
        return res
    side = "sender" if direction == "out" else "receiver"
    params = {"size":30, "after":after, "order":"desc", "status":"success", side:addr}
    if before:
        params["before"] = before
    txs = get(f"/accounts/{addr}/transactions", params)
    time.sleep(0.25)
    info = get(f"/accounts/{addr}")
    time.sleep(0.2)
    bal = int(info.get("balance","0"))/1e18 if isinstance(info, dict) and "balance" in info else None
    agg = {}
    for t in (txs if isinstance(txs, list) else []):
        val = int(t.get("value","0"))/1e18
        if val <= 0:
            continue
        other = t["receiver"] if direction == "out" else t["sender"]
        if other in DESKS:
            continue
        vv = venue_of(other) or ("UNRESOLVED:" + other)
        agg[vv] = agg.get(vv, 0) + val
    res = (agg, "router", bal)
    _resolve_cache[key] = res
    return res

def attribute(block):
    per_venue, unresolved = {}, 0.0
    for addr, rec in block.items():
        amt, terms = rec["amount"], rec["terminals"]
        if rec["kind"] == "direct":
            v = venue_of(addr)
            per_venue[v] = per_venue.get(v, 0) + amt
            continue
        named = {k:v for k,v in terms.items() if v and not k.startswith("UNRESOLVED")}
        tot = sum(named.values())
        if tot <= 0:
            unresolved += amt
            continue
        for v, val in named.items():
            per_venue[v] = per_venue.get(v, 0) + amt * (val/tot)
    return per_venue, unresolved

def hub_trace(out_block, in_block, after, before=None, min_amt=1000):
    out_dest, in_src = {}, {}
    for a, v in out_block.items():
        for t in v["txs"]:
            val = int(t.get("value","0"))/1e18
            if val <= 0 or t["receiver"] in DESKS:
                continue
            out_dest[t["receiver"]] = out_dest.get(t["receiver"], 0) + val
    for a, v in in_block.items():
        for t in v["txs"]:
            val = int(t.get("value","0"))/1e18
            if val <= 0 or t["sender"] in DESKS:
                continue
            in_src[t["sender"]] = in_src.get(t["sender"], 0) + val

    trace = {"outbound":{}, "inbound":{}}
    for addr, amt in sorted(out_dest.items(), key=lambda x:-x[1]):
        if amt < min_amt:
            trace["outbound"][addr] = {"amount":amt,"kind":"small","terminals":{},"balance":None,
                                       "label":label_map.get(addr,"Unknown")}
            continue
        agg, kind, bal = resolve_hop(addr, "out", after, before)
        trace["outbound"][addr] = {"amount":amt,"kind":kind,"terminals":agg,"balance":bal,
                                   "label":label_map.get(addr,"Unknown")}
        print(f"  OUT {amt:10,.0f} -> {addr[:14]} {kind} {list(agg)[:2]}")
    for addr, amt in sorted(in_src.items(), key=lambda x:-x[1]):
        if amt < min_amt:
            trace["inbound"][addr] = {"amount":amt,"kind":"small","terminals":{},"balance":None,
                                      "label":label_map.get(addr,"Unknown")}
            continue
        agg, kind, bal = resolve_hop(addr, "in", after, before)
        trace["inbound"][addr] = {"amount":amt,"kind":kind,"terminals":agg,"balance":bal,
                                  "label":label_map.get(addr,"Unknown")}
        print(f"  IN  {amt:10,.0f} <- {addr[:14]} {kind} {list(agg)[:2]}")

    out_venues, out_unres = attribute(trace["outbound"])
    in_venues, in_unres = attribute(trace["inbound"])
    venues = sorted(set(list(out_venues)+list(in_venues)))
    net = {v: out_venues.get(v,0)-in_venues.get(v,0) for v in venues}
    gross_out, gross_in = sum(out_dest.values()), sum(in_src.values())
    circular = sum(min(out_venues.get(v,0), in_venues.get(v,0)) for v in venues)
    trace["venue_netting"] = {"outbound_by_venue":out_venues, "inbound_by_venue":in_venues,
                              "net_by_venue":net, "unresolved_out":out_unres,
                              "unresolved_in":in_unres, "gross_out":gross_out,
                              "gross_in":gross_in, "circular":circular,
                              "net_one_way":gross_out-circular}
    return trace

print("\n=== HUB TRACE: 7d window (Aug 3 -> Aug 10) ===")
D["otc_hub_trace"] = hub_trace(D["desk_outbound_interim"], D["desk_inbound_interim"], INTERIM_START)
ok.append("two-hop both-legs hub netting, 7d window (folded into collector)")

# ---------------------------------------------------------------------------
# REC #6 - IDENTIFY 'Unknown Whale I (active)'
# ---------------------------------------------------------------------------
D["whale_i_info"] = get(f"/accounts/{UNKNOWN_WHALE_I}")
time.sleep(0.2)
D["whale_i_inbound_60d"]  = paged_txs(UNKNOWN_WHALE_I, SIXTY_DAYS_AGO, direction="receiver", max_pages=12)
D["whale_i_outbound_60d"] = paged_txs(UNKNOWN_WHALE_I, SIXTY_DAYS_AGO, direction="sender",  max_pages=12)
ok.append("Unknown Whale I 60d bidirectional trace")
print(f"[whale I] inbound60d={len(D['whale_i_inbound_60d'])} outbound60d={len(D['whale_i_outbound_60d'])}")

# ---------------------------------------------------------------------------
# custody + demand instruments
# ---------------------------------------------------------------------------
D["binance_custody_out"] = paged_txs(BINANCE_CUSTODY, INTERIM_START, direction="sender", max_pages=6)
D["binance_custody_in"]  = paged_txs(BINANCE_CUSTODY, INTERIM_START, direction="receiver", max_pages=6)
D["mega_whale_inbound"]  = paged_txs(MEGA_WHALE, INTERIM_START, direction="receiver", max_pages=6)
D["mega_whale_outbound"] = paged_txs(MEGA_WHALE, INTERIM_START, direction="sender", max_pages=6)
for nm, ad in [("cb_routing_a", CB_ROUTING_A), ("cb_routing_b", CB_ROUTING_B)]:
    D[f"{nm}_in"]  = paged_txs(ad, INTERIM_START, direction="receiver", max_pages=4)
    D[f"{nm}_out"] = paged_txs(ad, INTERIM_START, direction="sender",  max_pages=4)
ok.append("identifiable-bid instrument (absorber + Coinbase routing pipes)")

BREADTH_EXCHANGES = {a: label_map[a] for a in exchange_addrs}
D["exchange_outbound_paged"] = {}
for a, lab in BREADTH_EXCHANGES.items():
    txs = paged_txs(a, INTERIM_START, direction="sender", max_pages=8)
    D["exchange_outbound_paged"][a] = {"label":lab, "txs":txs}
    if txs:
        print(f"[breadth] {lab}: {len(txs)} outbound txs")
ok.append("withdrawal-breadth scan (paginated exchange outbound, interim window)")

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
json.dump(D, open(f"{REPO}/data/collected/{REPORT_DATE}.json","w"))
print(f"Saved canonical snapshot to data/collected/{REPORT_DATE}.json")

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
for w in ["otc_hub_trace","otc_hub_trace_peak_run17"]:
    vn = D[w]["venue_netting"]
    print(f"=== {w}: gross_out={vn['gross_out']:,.0f} gross_in={vn['gross_in']:,.0f} "
          f"circular={vn['circular']:,.0f} net_one_way={vn['net_one_way']:,.0f}")
