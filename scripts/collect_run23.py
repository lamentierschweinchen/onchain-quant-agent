#!/usr/bin/env python3
"""Run #23 data collection for MultiversX intel report (2026-08-31).

CADENCE: previous snapshot 2026-08-24 -> clean 7-DAY window (2026-08-24 -> 2026-08-31).

Implements run #22's recommendations:
  #3  RESOLVE THE UNBOND AND WAVE #3 TOGETHER - unbond wallet delegation + outbound,
      cross-checked against the desk inbound list
  #4  TRACE P2P.ORG's 1,244 STRANDED DELEGATORS - enumerate callers on its contract
  #5  BUILD THE UNBONDING QUEUE ACROSS ALL PROVIDERS (not just the movers)
  #6  SEPARATE TURNOVER FROM THE RALLY - DEX volume in EGLD terms, WEGLD/USDC split out
  #7  BOUND MEX - MEX/WEGLD pool TVL in EGLD terms + supply
  #8  REPAIR THE IDENTIFIABLE-BID - discover absorbers dynamically from desk outbound terminals
  #10 PAGE-CAP BUDGET - raised cap for exchange hot wallets specifically
  #11 DOES THE BINANCE 300,000 REACH THE DESKS? hot outbound >10K vs desk inbound

Run #22 method fixes folded into the main collector:
  - provider join key is `identity or provider` on BOTH sides, with a match-rate assertion
  - deregistration detection: locked == 0 with numNodes > 0
"""
import json, time, urllib.request, urllib.parse, os, sys, base64
from datetime import datetime, timezone

API = "https://api.multiversx.com"
REPORT_DATE = "2026-08-31"
OUT = "/tmp/run23w"
os.makedirs(OUT, exist_ok=True)

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
kn = json.load(open(f"{REPO}/data/known-addresses.json"))
prev = json.load(open(f"{REPO}/data/previous.json"))

def ts(y, m, d):
    return int(datetime(y, m, d, 0, 0, 0, tzinfo=timezone.utc).timestamp())

SEVEN_DAYS_AGO  = ts(2026, 8, 24)
WINDOW_END      = ts(2026, 8, 31)
ONE_DAY_AGO     = ts(2026, 8, 30)
THIRTY_DAYS_AGO = ts(2026, 8, 1)
# wave #3 / extended wave: feed restarted Aug 17-24; extend feed-to-drain through this window
WAVE_START, WAVE_END = ts(2026, 8, 17), ts(2026, 8, 31)

PAGECAP_LOG = []

def get(path, params=None, retries=2):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    for attempt in range(retries+1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"intel-agent/23"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt == retries:
                return {"__error__": str(e), "__url__": url}
            time.sleep(1.0)

def getraw(url, retries=2):
    for attempt in range(retries+1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"intel-agent/23"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if attempt == retries:
                return {"__error__": str(e)}
            time.sleep(1.0)

def paged_txs(addr, after, before=None, direction="sender", page=50, max_pages=60, tag=""):
    out, frm = [], 0
    hit_cap = True
    for _ in range(max_pages):
        params = {"size":page, "from":frm, "after":after, "order":"desc", "status":"success",
                  direction:addr}
        if before:
            params["before"] = before
        batch = get(f"/accounts/{addr}/transactions", params)
        time.sleep(0.22)
        if not isinstance(batch, list) or not batch:
            hit_cap = False
            break
        out.extend(batch)
        if len(batch) < page:
            hit_cap = False
            break
        frm += page
    if hit_cap:
        oldest = min((t.get("timestamp") or 0) for t in out) if out else None
        PAGECAP_LOG.append({"address":addr, "direction":direction, "tag":tag,
                            "txs":len(out), "max_pages":max_pages,
                            "requested_after":after, "oldest_seen_ts":oldest,
                            "coverage_days": round((WINDOW_END-oldest)/86400,1) if oldest else None})
        print(f"  [PAGE-CAP] {addr[:14]} {direction} {tag}: {len(out)} txs, oldest {oldest}")
    return out

D = {"_period": {"report_date": REPORT_DATE,
                 "previous_snapshot": prev.get("snapshot_date"),
                 "window_start_ts": SEVEN_DAYS_AGO,
                 "window_days": 7,
                 "note": "clean 7d window 2026-08-24 -> 2026-08-31, comparable to runs #13-#22"}}
ok, failed = [], []

def step(name, val, endpoint):
    D[name] = val
    if isinstance(val, dict) and "__error__" in val:
        failed.append(f"{endpoint} -> {val['__error__']}")
    else:
        ok.append(endpoint)
    time.sleep(0.2)

# --- macro -----------------------------------------------------------------
step("economics", get("/economics"), "/economics")
step("stats", get("/stats"), "/stats")
step("top_accounts", get("/accounts", {"size":100,"sort":"balance","order":"desc"}), "/accounts?sort=balance")

# --- tokens ----------------------------------------------------------------
step("tokens_holders", get("/tokens", {"size":25,"sort":"accounts","order":"desc"}), "/tokens?sort=accounts")
step("tokens_txs", get("/tokens", {"size":25,"sort":"transactions","order":"desc"}), "/tokens?sort=transactions")
step("tokens_mcap", get("/tokens", {"size":25,"sort":"marketCap","order":"desc"}), "/tokens?sort=marketCap")

# --- staking ---------------------------------------------------------------
step("providers", get("/providers", {"size":200,"sort":"locked","order":"desc"}), "/providers?size=200")
step("identities", get("/identities"), "/identities")

# --- mex -------------------------------------------------------------------
step("mex_economics", get("/mex/economics"), "/mex/economics")
step("mex_pairs", get("/mex/pairs", {"size":25}), "/mex/pairs")
step("mex_pairs_wide", get("/mex/pairs", {"size":50}), "/mex/pairs?size=50")
step("mex_tokens", get("/mex/tokens", {"size":50}), "/mex/tokens")
step("mex_farms", get("/mex/farms", {"size":25}), "/mex/farms")

# --- cross-chain -----------------------------------------------------------
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
accounts_to_query = {a: label_map[a] for a in exchange_addrs}

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
    accounts_to_query[w["address"]] = (w.get("label") or "watch")[:60]

UPBIT_OTC = "erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
OTC_DIST  = "erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
MEGA_WHALE = "erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"
CB_ROUTING_A = "erd1eae23a530qymlpvfrudzsge5wgl003wl92saax74cew7j549eqqq3jklut"
CB_ROUTING_B = "erd1lgdltequh7627rtlacmcp6p5vec7zmu2rxhu7pjwvcja8f4a9gqq9vcc70"
CUSTODY_FUNDER = "erd1r3w62vqmsux5e38p6vnueatmfcs8nr5lmg3s97x6rafqpgxfae0sxv9z0v"
BINANCE_CUSTODY = "erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"
BINANCE_HOT = "erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp29trp6qsl2gdvvz2eqra76xc"
UNKNOWN_WHALE_I = "erd1vd76pwhl4dyeyd8gylv6mkkvy7g4dnfezjuyp4j4x3wwnauga57q53m3z0"
XOXNO_LSD = "erd1qqqqqqqqqqqqqpgq6uzdzy54wnesfnlaycxwymrn9texlnmyah0ssrfvk6"
UNBOND_WALLET = "erd1daqlaezxx22rzyxnqx5ddkykm5ajelt0hetjnstm7rxqg78xqusqazv9ms"

otc_trace = {
    "erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh":"Unknown Whale erd17l22 (OTC source)",
    "erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp":"OTC source funder erd12tq6ax5k",
    MEGA_WHALE:"Unknown Mega Whale erd18mv2z6r2",
    "erd1nhtq4mj3jzlz35l6szpkp0cagss803l6crwq8zjjpuykfsxwj0dsg2c2gu":"OTC Source-Chain Router",
    UPBIT_OTC:"UPbit OTC Desk",
    OTC_DIST:"OTC Distribution Wallet",
    BINANCE_CUSTODY:"Binance Staking custody",
    BINANCE_HOT:"Binance.com hot",
    CUSTODY_FUNDER:"Binance de-staking withdrawal wallet erd1r3w62vq",
    CB_ROUTING_A:"Coinbase Routing/Custody erd1eae23a5",
    CB_ROUTING_B:"Coinbase Routing Wallet erd1lgdltequ",
    UNKNOWN_WHALE_I:"Unknown Whale I (OTC operator inventory)",
    UNBOND_WALLET:"The 229,865 EGLD unbond wallet",
}
for a,l in otc_trace.items():
    accounts_to_query[a] = l

acc_data = {}
for addr, label in accounts_to_query.items():
    info = get(f"/accounts/{addr}")
    time.sleep(0.14)
    txs = get(f"/accounts/{addr}/transactions", {"size":40,"after":SEVEN_DAYS_AGO,"order":"desc","status":"success"})
    time.sleep(0.14)
    acc_data[addr] = {"label":label, "info":info, "txs":txs}
D["accounts"] = acc_data
ok.append(f"/accounts/{{addr}} + /transactions x{len(acc_data)}")
print(f"[accounts] queried {len(acc_data)}")

# ---------------------------------------------------------------------------
# OTC desks - paginated both legs
# ---------------------------------------------------------------------------
DESKS = {UPBIT_OTC:"UPbit OTC Desk", OTC_DIST:"OTC Distribution Wallet"}
D["desk_outbound_paged"] = {}
D["desk_inbound_paged"] = {}
for d_addr, d_label in DESKS.items():
    o = paged_txs(d_addr, SEVEN_DAYS_AGO, direction="sender", tag="desk7d")
    i = paged_txs(d_addr, SEVEN_DAYS_AGO, direction="receiver", tag="desk7d")
    D["desk_outbound_paged"][d_addr] = {"label":d_label, "txs":o}
    D["desk_inbound_paged"][d_addr] = {"label":d_label, "txs":i}
    print(f"[paged/7d] {d_label}: out={len(o)} in={len(i)}")
ok.append("paginated desk in/outbound (7d)")

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
    time.sleep(0.22)
    info = get(f"/accounts/{addr}")
    time.sleep(0.18)
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

print("\n=== HUB TRACE: 7d window (Aug 24 -> Aug 31) ===")
D["otc_hub_trace"] = hub_trace(D["desk_outbound_paged"], D["desk_inbound_paged"], SEVEN_DAYS_AGO)
ok.append("two-hop both-legs hub netting, 7d window")

# wave #3 extended window (feed restarted Aug 17) -- run #22 rule: test the wave, do not assume
print("\n=== HUB TRACE: WAVE #3 EXTENDED (Aug 17 -> Aug 31) ===")
_wob, _wib = {}, {}
for d_addr, d_label in DESKS.items():
    o = paged_txs(d_addr, WAVE_START, before=WAVE_END, direction="sender", max_pages=120, tag="wave3ext")
    i = paged_txs(d_addr, WAVE_START, before=WAVE_END, direction="receiver", max_pages=120, tag="wave3ext")
    _wob[d_addr] = {"label":d_label, "txs":o}
    _wib[d_addr] = {"label":d_label, "txs":i}
    print(f"[paged/wave3ext] {d_label}: out={len(o)} in={len(i)}")
D["desk_outbound_wave3ext"] = _wob
D["desk_inbound_wave3ext"] = _wib
D["otc_hub_trace_wave3ext"] = hub_trace(_wob, _wib, WAVE_START, before=WAVE_END)
D["otc_hub_trace_wave3ext"]["_window"] = "WAVE #3 EXTENDED Aug 17-31 (feed-to-drain)"
ok.append("wave #3 extended window netting (Aug 17-31)")

try:
    _prevcol = json.load(open(f"{REPO}/data/collected/2026-08-24.json"))
    for _k in ("otc_hub_trace_peak_run17","otc_hub_trace_run16","otc_hub_trace_run18",
               "otc_hub_trace_julywave","otc_hub_trace_wave2ext"):
        if _k in _prevcol:
            D[_k] = _prevcol[_k]
    D["_historical_trace_provenance"] = "carried from data/collected/2026-08-24.json (fixed historical windows)"
    ok.append("historical hub-trace windows (carried forward)")
except Exception as e:
    failed.append(f"historical trace carry-forward -> {e}")

# ---------------------------------------------------------------------------
# REC #3 - RESOLVE THE UNBOND: did the 229,865 move, and where?
# ---------------------------------------------------------------------------
D["unbond_wallet_info"] = get(f"/accounts/{UNBOND_WALLET}")
time.sleep(0.2)
D["unbond_wallet_delegation"] = get(f"/accounts/{UNBOND_WALLET}/delegation")
time.sleep(0.2)
D["unbond_wallet_out_7d"] = paged_txs(UNBOND_WALLET, SEVEN_DAYS_AGO, direction="sender", max_pages=20, tag="unbond_out")
D["unbond_wallet_in_7d"]  = paged_txs(UNBOND_WALLET, SEVEN_DAYS_AGO, direction="receiver", max_pages=20, tag="unbond_in")
_ubw_targets = {}
for t in (D["unbond_wallet_out_7d"] or []):
    r = t.get("receiver"); v = int(t.get("value","0"))/1e18
    if r and v > 100:
        _ubw_targets[r] = _ubw_targets.get(r, 0) + v
D["unbond_wallet_targets"] = _ubw_targets
D["unbond_target_traces"] = {}
for r, amt in sorted(_ubw_targets.items(), key=lambda x:-x[1])[:5]:
    D["unbond_target_traces"][r] = {"address":r,"amount":amt,"label":label_map.get(r,"Unknown"),
                                    "info":get(f"/accounts/{r}")}
    time.sleep(0.2)
    D["unbond_target_traces"][r]["out"] = paged_txs(r, SEVEN_DAYS_AGO, direction="sender", max_pages=6, tag="unbond_hop2")
# also read zero-value function calls (run #19 rule) on this wallet
D["unbond_wallet_all_out"] = get(f"/accounts/{UNBOND_WALLET}/transactions",
                                 {"size":50,"after":SEVEN_DAYS_AGO,"order":"desc","sender":UNBOND_WALLET})
time.sleep(0.2)
ok.append("229,865 EGLD unbond resolution (rec #3)")
print(f"[unbond] out7d={len(D['unbond_wallet_out_7d'])} targets={len(_ubw_targets)}")

# ---------------------------------------------------------------------------
# REC #5 - UNBONDING QUEUE ACROSS ALL PROVIDERS (correct join key, run #22 rule)
# ---------------------------------------------------------------------------
prev_prov = {p["provider"]: p for p in prev.get("staking_providers", [])}
cur_all = D["providers"] if isinstance(D["providers"], list) else []
def pkey(p): return p.get("identity") or p.get("provider")
cur_keys = {pkey(p) for p in cur_all}
match_rate = len(cur_keys & set(prev_prov)) / max(1, min(len(cur_keys), len(prev_prov)))
D["_provider_join_match_rate"] = match_rate
print(f"[join] provider key match rate {match_rate:.1%} ({len(cur_keys & set(prev_prov))} of {min(len(cur_keys),len(prev_prov))})")
if match_rate < 0.80:
    failed.append(f"provider join match rate {match_rate:.1%} < 80% (run #22 assertion)")

movers = []
for p in cur_all:
    k = pkey(p); lk = float(p.get("locked",0) or 0)/1e18
    pv = prev_prov.get(k)
    if pv is None:
        continue
    d = lk - pv.get("locked_egld",0.0)
    if abs(d) >= 5000:
        movers.append({"key":k,"address":p.get("provider"),"delta_egld":d,"locked_egld":lk,
                       "users":p.get("numUsers"),"prev_users":pv.get("num_delegators"),
                       "apr":p.get("apr"),"fee":p.get("serviceFee"),"nodes":p.get("numNodes")})
for k, pv in prev_prov.items():
    if k not in cur_keys and pv.get("locked_egld",0) >= 5000:
        movers.append({"key":k,"address":None,"delta_egld":-pv["locked_egld"],"locked_egld":0.0,
                       "users":None,"prev_users":pv.get("num_delegators"),"apr":0,"fee":None,
                       "left_active_set":True})
movers.sort(key=lambda m:-abs(m["delta_egld"]))
D["provider_movers"] = movers
print(f"[movers] {len(movers)} providers moved >=5K EGLD")
for m in movers[:15]:
    print(f"   {m['delta_egld']:+11,.0f}  {str(m['key'])[:36]}")

# deregistration detection: locked == 0 with numNodes > 0
D["deregistered_providers"] = [
    {"key":pkey(p),"address":p.get("provider"),"nodes":p.get("numNodes"),
     "users":p.get("numUsers"),"apr":p.get("apr"),"fee":p.get("serviceFee"),
     "locked":float(p.get("locked",0) or 0)/1e18,
     "prev_locked":prev_prov.get(pkey(p),{}).get("locked_egld"),
     "prev_users":prev_prov.get(pkey(p),{}).get("num_delegators")}
    for p in cur_all
    if float(p.get("locked",0) or 0) == 0 and int(p.get("numNodes",0) or 0) > 0]
print(f"[dereg] {len(D['deregistered_providers'])} providers locked==0 with nodes>0")

# scan EVERY provider's inbound for unDelegate (rec #5)
print("\n=== UNBONDING QUEUE: scanning ALL providers ===")
undel_senders = {}
prov_fn = {}
scan_set = [p for p in cur_all if float(p.get("locked",0) or 0) > 0 or int(p.get("numNodes",0) or 0) > 0]
for i, p in enumerate(scan_set):
    addr = p.get("provider"); k = pkey(p)
    if not addr:
        continue
    txs = paged_txs(addr, SEVEN_DAYS_AGO, before=WINDOW_END, direction="receiver",
                    max_pages=6, tag="provscan")
    fn = {}; legs = []
    for t in txs:
        f = t.get("function") or "(transfer)"
        fn[f] = fn.get(f,0)+1
        if f in ("unDelegate","withdraw","unStakeNodes"):
            snd = t.get("sender"); amt = None
            try:
                dec = base64.b64decode(t.get("data") or "").decode("utf-8", errors="ignore")
                parts = dec.split("@")
                if len(parts) > 1:
                    amt = int(parts[1],16)/1e18
            except Exception:
                pass
            if f == "unDelegate":
                legs.append({"sender":snd,"amount_egld":amt,"timestamp":t.get("timestamp"),
                             "txHash":t.get("txHash")})
                if snd:
                    undel_senders.setdefault(snd,[]).append(
                        {"provider":k,"amount_egld":amt,"timestamp":t.get("timestamp")})
    prov_fn[k] = {"address":addr,"function_counts":fn,"undelegate_legs":legs,"tx_count":len(txs)}
    if legs or (i % 25 == 0):
        print(f"  [{i+1}/{len(scan_set)}] {str(k)[:30]:32} txs={len(txs):4} unDel={len(legs)}")
D["provider_inbound_all"] = prov_fn
D["provider_scan_count"] = len(scan_set)
ok.append(f"all-provider unDelegate scan x{len(scan_set)} (rec #5)")
print(f"[unbonding] {len(undel_senders)} distinct unDelegate callers across {len(scan_set)} providers")

# query /delegation for the largest callers
caller_tot = {w: sum((l["amount_egld"] or 0) for l in legs) for w, legs in undel_senders.items()}
pool = []
for w in sorted(caller_tot, key=lambda x:-caller_tot[x])[:45]:
    dg = get(f"/accounts/{w}/delegation"); time.sleep(0.25)
    inf = get(f"/accounts/{w}"); time.sleep(0.18)
    pend = []
    if isinstance(dg, list):
        for row in dg:
            for u in (row.get("userUndelegatedList") or []):
                pend.append({"contract":row.get("contract"),
                             "amount_egld":int(u["amount"])/1e18,
                             "seconds_remaining":u.get("seconds"),
                             "days_remaining":round((u.get("seconds") or 0)/86400,2)})
    pool.append({"wallet":w,"label":label_map.get(w,"Unknown"),
                 "balance_egld":int(inf.get("balance","0"))/1e18 if isinstance(inf,dict) and "balance" in inf else None,
                 "nonce":inf.get("nonce") if isinstance(inf,dict) else None,
                 "this_week_undelegated":caller_tot[w],
                 "legs":undel_senders[w],
                 "pending_unbonding":pend,
                 "total_pending_egld":sum(x["amount_egld"] for x in pend)})
pool.sort(key=lambda x:-x["total_pending_egld"])
D["unbonding_pool"] = pool
D["undelegated_this_week_total_egld"] = sum(caller_tot.values())
D["undelegate_callers_count"] = len(undel_senders)
D["unbonding_pool_total_egld"] = sum(p["total_pending_egld"] for p in pool)
ok.append("unbonding pool /accounts/{addr}/delegation x%d" % len(pool))
print(f"[unbonding] undelegated this week {sum(caller_tot.values()):,.0f} EGLD; "
      f"measured pending {D['unbonding_pool_total_egld']:,.0f}")

# ---------------------------------------------------------------------------
# REC #4 - P2P.ORG's 1,244 STRANDED DELEGATORS
# ---------------------------------------------------------------------------
P2P = None
for p in cur_all:
    if p.get("identity") == "p2p_org_":
        P2P = p; break
D["p2p_provider"] = P2P
if P2P:
    addr = P2P["provider"]
    txs = paged_txs(addr, SEVEN_DAYS_AGO, before=WINDOW_END, direction="receiver",
                    max_pages=12, tag="p2p_callers")
    fn = {}; callers = {}
    for t in txs:
        f = t.get("function") or "(transfer)"
        fn[f] = fn.get(f,0)+1
        s = t.get("sender")
        if s:
            callers.setdefault(s, []).append(f)
    D["p2p_callers"] = {"function_counts":fn, "distinct_callers":len(callers),
                        "callers":{k:v for k,v in list(callers.items())[:80]},
                        "tx_count":len(txs)}
    D["p2p_owner"] = P2P.get("owner")
    print(f"[p2p] {len(txs)} inbound txs, {len(callers)} distinct callers, fns={fn}")
ok.append("p2p_org_ stranded-delegator caller enumeration (rec #4)")

# ---------------------------------------------------------------------------
# 100%-fee providers follow-through
# ---------------------------------------------------------------------------
D["fee100_identities"] = {}
for ident in ("egldstakingprovider","procryptostaking"):
    D["fee100_identities"][ident] = get("/providers", {"identity":ident})
    time.sleep(0.3)
ok.append("100%-fee provider follow-through")

# ---------------------------------------------------------------------------
# REC #11 - DOES THE BINANCE 300,000 REACH THE DESKS?
# ---------------------------------------------------------------------------
D["binance_custody_out"] = paged_txs(BINANCE_CUSTODY, SEVEN_DAYS_AGO, direction="sender", max_pages=6, tag="custody")
D["binance_custody_in"]  = paged_txs(BINANCE_CUSTODY, SEVEN_DAYS_AGO, direction="receiver", max_pages=6, tag="custody")
D["binance_hot_out"] = paged_txs(BINANCE_HOT, SEVEN_DAYS_AGO, direction="sender", max_pages=20, tag="binance_hot_out")
D["binance_hot_in"]  = paged_txs(BINANCE_HOT, SEVEN_DAYS_AGO, direction="receiver", max_pages=20, tag="binance_hot_in")
_big_hot = {}
for t in (D["binance_hot_out"] or []):
    v = int(t.get("value","0"))/1e18
    if v >= 10000:
        _big_hot[t["receiver"]] = _big_hot.get(t["receiver"],0)+v
D["binance_hot_big_outbound"] = _big_hot
D["binance_hot_big_traces"] = {}
for r, amt in sorted(_big_hot.items(), key=lambda x:-x[1])[:6]:
    D["binance_hot_big_traces"][r] = {"amount":amt,"label":label_map.get(r,"Unknown"),
                                      "info":get(f"/accounts/{r}")}
    time.sleep(0.2)
    D["binance_hot_big_traces"][r]["out"] = paged_txs(r, SEVEN_DAYS_AGO, direction="sender",
                                                      max_pages=6, tag="binance_hop2")
ok.append("Binance hot outbound >10K vs desk inbound (rec #11)")
print(f"[binance] {len(_big_hot)} outbound recipients >=10K")

# ---------------------------------------------------------------------------
# demand instruments (rec #8 dynamic absorbers, rec #10 raised page cap)
# ---------------------------------------------------------------------------
D["mega_whale_inbound"]  = paged_txs(MEGA_WHALE, SEVEN_DAYS_AGO, direction="receiver", max_pages=6, tag="absorber")
D["mega_whale_outbound"] = paged_txs(MEGA_WHALE, SEVEN_DAYS_AGO, direction="sender", max_pages=6, tag="absorber")
for nm, ad in [("cb_routing_a", CB_ROUTING_A), ("cb_routing_b", CB_ROUTING_B)]:
    D[f"{nm}_in"]  = paged_txs(ad, SEVEN_DAYS_AGO, direction="receiver", max_pages=4, tag=nm)
    D[f"{nm}_out"] = paged_txs(ad, SEVEN_DAYS_AGO, direction="sender",  max_pages=4, tag=nm)

# rec #8: DISCOVER absorbers dynamically - desk outbound terminals that HOLD what they receive
absorber_candidates = {}
for a, rec in D["otc_hub_trace"]["outbound"].items():
    if rec["amount"] >= 2000 and not venue_of(a):
        absorber_candidates[a] = rec["amount"]
for a, rec in D["otc_hub_trace_wave3ext"]["outbound"].items():
    if rec["amount"] >= 2000 and not venue_of(a):
        absorber_candidates[a] = max(absorber_candidates.get(a,0), rec["amount"])
absorbers = []
for a, amt in sorted(absorber_candidates.items(), key=lambda x:-x[1])[:14]:
    inf = get(f"/accounts/{a}"); time.sleep(0.18)
    bal = int(inf.get("balance","0"))/1e18 if isinstance(inf,dict) and "balance" in inf else None
    outb = paged_txs(a, SEVEN_DAYS_AGO, direction="sender", max_pages=4, tag="absorber_scan")
    fwd = sum(int(t.get("value","0"))/1e18 for t in outb)
    absorbers.append({"address":a,"label":label_map.get(a,"Unknown"),"received_from_desks":amt,
                      "balance_egld":bal,"forwarded_out_egld":fwd,"nonce":inf.get("nonce") if isinstance(inf,dict) else None,
                      "retained_egld":max(0.0,amt-fwd),
                      "is_absorber": bal is not None and bal > 0.5*amt})
D["dynamic_absorbers"] = absorbers
ok.append("dynamic absorber discovery from desk terminals (rec #8)")
print(f"[absorbers] scanned {len(absorbers)} desk terminals; "
      f"{sum(1 for x in absorbers if x['is_absorber'])} retain >50%")

# withdrawal breadth - raised page cap for exchange hot wallets (rec #10)
HOT_CAP = 30
D["exchange_outbound_paged"] = {}
for a in exchange_addrs:
    lab = label_map[a]
    cap = HOT_CAP if ("hot" in lab.lower() or "Binance.com" in lab or "UPbit" in lab) else 10
    txs = paged_txs(a, SEVEN_DAYS_AGO, direction="sender", max_pages=cap, tag="breadth")
    D["exchange_outbound_paged"][a] = {"label":lab, "txs":txs, "page_cap":cap}
    if txs:
        print(f"[breadth] {lab}: {len(txs)} outbound txs (cap {cap})")
ok.append("withdrawal-breadth scan (paginated exchange outbound, raised hot-wallet cap)")

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
    "XOXNO LSD": XOXNO_LSD,
}
proto_data = {}
for name, addr in proto_contracts.items():
    cnt = get(f"/accounts/{addr}/transfers/count", {"after":ONE_DAY_AGO}); time.sleep(0.14)
    bal = get(f"/accounts/{addr}"); time.sleep(0.14)
    proto_data[name] = {"addr":addr, "transfers_24h":cnt, "balance":bal}
D["proto"] = proto_data
ok.append("/accounts/{addr}/transfers/count x%d" % len(proto_data))

wegld_contracts = [
    "erd1qqqqqqqqqqqqqpgqvc7gdl0p4s97guh498wgz75k8sav6sjfjlwqh679jy",
    "erd1qqqqqqqqqqqqqpgqhe8t5jewej70zupmh44jurgn29psua5l2jps3ntjj3",
    "erd1qqqqqqqqqqqqqpgqmuk0q2saj0mgutxm4teywre6dl8wqf58xamqdrukln",
]
D["wegld"] = {}
for c in wegld_contracts:
    D["wegld"][c] = get(f"/accounts/{c}"); time.sleep(0.14)

tvl_tokens = ["HUSDC-d80042","HEGLD-d61095","HUSDT-6f0914","HWBTC-49ca31","HWETH-b3d17e",
              "HBUSD-ac1fca","HHTM-e03ba5","HMEX-df6df7","HUTK-4fa4b2","HWTAO-2e9136",
              # WTAO-3ec9c0 was WRONG and 404'd on every run from #13 to #23 without
              # anyone noticing, which is why the run #11 accumulator fallback for
              # SWTAO was believed dead. The live WrappedTAO is WTAO-4f5363.
              "SEGLD-3ad2d0","SWTAO-356a25","USH-111e09","XEGLD-e413ed","WTAO-4f5363"]
DATAAPI_TOKENS = {"SEGLD-3ad2d0","SWTAO-356a25","USH-111e09","XEGLD-e413ed"}
tok_mcap = {}
for t in tvl_tokens:
    tok_mcap[t] = get(f"/tokens/{t}")
    time.sleep(1.05)
refetch_log = {}
for t in DATAAPI_TOKENS:
    info = tok_mcap.get(t); attempts = 0
    while isinstance(info, dict) and info.get("price") is None and attempts < 4:
        attempts += 1; time.sleep(2.5); info = get(f"/tokens/{t}")
    tok_mcap[t] = info
    refetch_log[t] = {"retries":attempts,
                      "recovered": isinstance(info, dict) and info.get("price") is not None}
# run #22 rule: recover from the LIST endpoints before deriving
list_prices = {}
for src in ("tokens_mcap","tokens_holders","tokens_txs"):
    for tok in (D.get(src) or []):
        if isinstance(tok, dict) and tok.get("identifier"):
            list_prices.setdefault(tok["identifier"], tok)
for t in DATAAPI_TOKENS:
    info = tok_mcap.get(t)
    if isinstance(info, dict) and info.get("price") is None and t in list_prices:
        lp = list_prices[t]
        if lp.get("price") is not None:
            info["price"] = lp["price"]; info["marketCap"] = lp.get("marketCap")
            info["_price_source"] = "list_endpoint_recovery"
            refetch_log[t]["list_recovery"] = True
D["tvl_tokens"] = tok_mcap
D["dataapi_refetch_log"] = refetch_log
ok.append("/tokens/{id} x%d (dataApi re-fetch + list recovery)" % len(tok_mcap))

for sid in ["USDC-c76f1f","USDT-f8c08c"]:
    D[f"stable_{sid}"] = get(f"/tokens/{sid}"); time.sleep(0.5)
for nm, tid in [("wegld_token","WEGLD-bd4d79"),("mex_token","MEX-455c57"),
                ("emrs_token","EMRS-6e4067"),("zpay_token","ZPAY-247875"),
                ("htm_token","HTM-f51d55")]:
    D[nm] = get(f"/tokens/{tid}"); time.sleep(0.25)

# --- newly issued tokens ---------------------------------------------------
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
        data_field = tx.get("data","")
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
            search = get("/tokens", {"search":name,"size":5}); time.sleep(0.3)
            if isinstance(search, list):
                for tok in search:
                    tid = tok.get("identifier","")
                    if not tid.startswith(ticker+"-"):
                        continue
                    if tok.get("accounts",0) > 1000 or tid in prev_ids:
                        continue
                    newly_issued.append({"identifier":tid,"name":tok.get("name") or name,
                        "ticker":ticker,"accounts":tok.get("accounts",0),
                        "transactions":tok.get("transactions",0),
                        "timestamp":tx.get("timestamp"),"deployer":tx.get("sender","")})
                    break
        except Exception:
            continue
D["newly_issued"] = newly_issued
ok.append("/accounts/{ESDT_SYS}/transactions?function=issue (newly_issued workaround)")

# --- save ------------------------------------------------------------------
D["_pagecap_terminations"] = PAGECAP_LOG
json.dump(D, open(f"{OUT}/collected.json","w"))
json.dump({"ok":ok,"failed":failed}, open(f"{OUT}/status.json","w"))
os.makedirs(f"{REPO}/data/collected", exist_ok=True)
json.dump(D, open(f"{REPO}/data/collected/{REPORT_DATE}.json","w"))
print(f"\nSaved canonical snapshot to data/collected/{REPORT_DATE}.json")
print("=== ECONOMICS ==="); print(json.dumps(D["economics"])[:600])
st = D["stats"]
if isinstance(st, dict):
    print({k:st.get(k) for k in ["accounts","transactions","epoch","blocks","shards"]})
print("\n=== STATUS ok=%d failed=%d ===" % (len(ok), len(failed)))
print("FAILED:", failed)
print("=== providers:", len(D["providers"]) if isinstance(D["providers"],list) else D["providers"])
print("=== btc_eth:", D["btc_eth"])
print("=== dataapi_refetch_log:", json.dumps(refetch_log))
print("=== newly_issued:", len(newly_issued))
for w in ["otc_hub_trace","otc_hub_trace_wave3ext"]:
    if w in D and "venue_netting" in D[w]:
        vn = D[w]["venue_netting"]
        print(f"=== {w}: gross_out={vn['gross_out']:,.0f} gross_in={vn['gross_in']:,.0f} "
              f"circular={vn['circular']:,.0f} net_one_way={vn['net_one_way']:,.0f}")
        print("    net_by_venue:", {k:round(v) for k,v in vn["net_by_venue"].items()})
print("=== PAGE-CAP TERMINATIONS:", json.dumps(PAGECAP_LOG, indent=1))
