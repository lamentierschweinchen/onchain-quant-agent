#!/usr/bin/env python3
"""Run #9 analysis digest. Prints computed metrics for report assembly."""
import json, math
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D = json.load(open("/tmp/run9/collected.json"))
prev = json.load(open(f"{REPO}/data/previous.json"))
kn = json.load(open(f"{REPO}/data/known-addresses.json"))
learn = json.load(open(f"{REPO}/data/learnings.json"))

# entity resolution
label_map, cat_map = {}, {}
for section, entries in kn.items():
    if not isinstance(entries, dict) or section == "_metadata":
        continue
    for addr, meta in entries.items():
        if isinstance(meta, dict) and addr.startswith("erd1"):
            label_map[addr] = meta.get("name","Unknown")
            cat_map[addr] = meta.get("category","unknown")

def lab(a): return label_map.get(a, "Unknown")
def cat(a): return cat_map.get(a, "unknown")

econ = D["economics"]; st = D["stats"]
pecon = prev["economics"]; pact = prev["activity"]

price = econ["price"]
circ = econ["circulatingSupply"]
staked = econ["staked"]
staked_ratio = staked / circ

print("="*70)
print("NETWORK HEALTH")
print("="*70)
print(f"price {price} (prev {pecon['egld_price_usd']}) chg% {100*(price-pecon['egld_price_usd'])/pecon['egld_price_usd']:.3f}")
print(f"mcap {econ['marketCap']} (prev {pecon['market_cap_usd']}) chg% {100*(econ['marketCap']-pecon['market_cap_usd'])/pecon['market_cap_usd']:.3f}")
print(f"total_supply {econ['totalSupply']} (prev {pecon['total_supply']}) added {econ['totalSupply']-pecon['total_supply']}")
print(f"staked {staked} (prev {pecon['staked_egld']}) added {staked-pecon['staked_egld']}")
print(f"staked_ratio {staked_ratio:.6f} (prev {pecon['staked_ratio']:.6f}) chg_pp {100*(staked_ratio-pecon['staked_ratio']):.4f}")
print(f"apr {econ['apr']} base {econ['baseApr']} topup {econ['topUpApr']} (prev apr {pecon['staking_apr']})")
print(f"token_mcap {econ['tokenMarketCap']} (prev {pecon['token_market_cap_usd']})")
print(f"accounts {st['accounts']} (prev {pact['total_accounts']}) added {st['accounts']-pact['total_accounts']}")
print(f"txns {st['transactions']} (prev {pact['total_transactions']}) added {st['transactions']-pact['total_transactions']}")
print(f"epoch {st['epoch']} (prev {pact['epoch']}) +{st['epoch']-pact['epoch']}  blocks {st['blocks']}")
be = D["btc_eth"]
print(f"BTC {be['bitcoin']['usd']} ({be['bitcoin']['usd_24h_change']:.2f}%) ETH {be['ethereum']['usd']} ({be['ethereum']['usd_24h_change']:.2f}%)")

# ---- current balances from acc_data
acc = D["accounts"]
def bal_of(addr):
    a = acc.get(addr)
    if a and isinstance(a.get("info"), dict) and "balance" in a["info"]:
        try: return int(a["info"]["balance"])/1e18
        except: return None
    return None

# current top accounts
ta = D["top_accounts"]
cur_top = {x["address"]: int(x["balance"])/1e18 for x in ta}
# also override exchange balances with freshly-queried acc_data (same source basically)

# prev top accounts map
prev_top = {x["address"]: x["balance_egld"] for x in prev["top_accounts"]}
N_prev = len(prev["top_accounts"])
print(f"\nN_prev top_accounts = {N_prev}; current top = {len(ta)}")

print("="*70)
print("WHALE TIERS (top-%d apples-to-apples, exclude system)" % N_prev)
print("="*70)
def tiers_from(top_map):
    # top_map: addr->balance; exclude system category; take all
    items = [(a,b) for a,b in top_map.items() if cat(a)!="system"]
    mega=[x for x in items if x[1]>1_000_000]
    large=[x for x in items if 100_000<=x[1]<=1_000_000]
    mid=[x for x in items if 10_000<=x[1]<100_000]
    return mega,large,mid
# trim current to top N_prev by balance
cur_trim = dict(sorted(cur_top.items(), key=lambda kv:-kv[1])[:N_prev])
cm,cl,cmid = tiers_from(cur_trim)
pm,pl,pmid = tiers_from(prev_top)
def tot(x): return sum(b for _,b in x)
for nm,c,p in [("mega",cm,pm),("large",cl,pl),("mid",cmid,pmid)]:
    print(f"{nm}: cur_count {len(c)} cur_tot {tot(c):.1f} | prev_count {len(p)} prev_tot {tot(p):.1f} | net {tot(c)-tot(p):.1f}")

print("="*70)
print("WALLET CHANGES (current top vs prev, >5% or >2000 EGLD abs)")
print("="*70)
changes=[]
for a,b in cur_top.items():
    if a in prev_top and cat(a)!="system":
        pb=prev_top[a]; d=b-pb
        pct=100*d/pb if pb else None
        if abs(d)>2000 or (pct is not None and abs(pct)>5):
            tier = "mega_whale" if b>1e6 else "large_whale" if b>=1e5 else "mid_whale" if b>=1e4 else "small"
            changes.append((a,lab(a),cat(a),tier,b,pb,d,pct))
changes.sort(key=lambda x:-abs(x[6]))
for a,l,c,t,b,pb,d,pct in changes[:25]:
    print(f"{d:+11.1f} ({pct:+6.1f}%) {t:11} {l[:38]:38} cur {b:.1f} {a[:12]}")

print("="*70)
print("EXCHANGE FLOWS (entity netting)")
print("="*70)
# entity grouping
def entity_of(addr):
    l = lab(addr)
    if "Binance" in l: return "Binance"
    if "Coinbase" in l: return "Coinbase"
    if "Crypto.com" in l: return "Crypto.com"
    for e in ["UPbit","Bybit","MEXC","Bitget","Gate.io","KuCoin","Bitfinex","Tokero"]:
        if e in l: return e
    return None
exch_addrs = [a for a,c in cat_map.items() if c=="exchange"]
# exclude OTC desk (those are 'other')
ent_cur, ent_prev, ent_wallets = {}, {}, {}
perwallet=[]
for a in exch_addrs:
    e = entity_of(a)
    if not e: continue
    cur = bal_of(a)
    if cur is None: cur = cur_top.get(a)
    pb = prev_top.get(a)
    ent_wallets[e]=ent_wallets.get(e,0)+1
    if cur is not None:
        ent_cur[e]=ent_cur.get(e,0)+cur
    if pb is not None:
        ent_prev[e]=ent_prev.get(e,0)+pb
    if cur is not None and pb is not None:
        perwallet.append((e,a,lab(a),cur,pb,cur-pb))
# Use prev.json exchange_balances entity totals as authoritative prev where available
prev_eb = prev["exchange_balances"]
# map prev_eb keys to entities
prev_ent={}
for k,v in prev_eb.items():
    if "Binance" in k: prev_ent["Binance"]=prev_ent.get("Binance",0)+v
    elif "Coinbase" in k: prev_ent["Coinbase"]=prev_ent.get("Coinbase",0)+v
    elif "Crypto.com" in k: prev_ent["Crypto.com"]=prev_ent.get("Crypto.com",0)+v
    else: prev_ent[k]=prev_ent.get(k,0)+v
print("per-wallet changes:")
for e,a,l,cur,pb,d in sorted(perwallet,key=lambda x:-abs(x[5])):
    print(f"  {d:+11.1f} {l[:30]:30} cur {cur:.1f} prev {pb:.1f} [{e}]")
print("\nentity netting (cur from queried wallets, prev from prev.json exchange_balances):")
total_cur=total_prev=0
ent_rows=[]
for e in sorted(set(list(ent_cur)+list(prev_ent))):
    c=ent_cur.get(e); p=prev_ent.get(e)
    if c is None or p is None:
        print(f"  {e}: cur {c} prev {p} (incomplete)");
    net = (c-p) if (c is not None and p is not None) else None
    if net is not None:
        ent_rows.append((e,ent_wallets.get(e,1),net))
        total_cur+=c; total_prev+=p
        print(f"  {e:12} wallets {ent_wallets.get(e,1)} net {net:+.1f} (cur {c:.1f} prev {p:.1f})")
print(f"\nTOTAL exchange: cur {total_cur:.1f} prev {total_prev:.1f} net {total_cur-total_prev:+.1f} pct {100*(total_cur-total_prev)/total_prev:+.3f}")

# ---- large transactions
print("="*70)
print("LARGE TRANSACTIONS (>1000 EGLD, 7d)")
print("="*70)
router_set = set(kn.get("exchange_routers",{}).keys())
otc_set = set([a for a,m in kn.get("unlabeled_whales",{}).items() if m.get("subcategory")=="otc"])
seen=set(); bigtx=[]
for a,info in acc.items():
    txs = info.get("txs")
    if not isinstance(txs,list): continue
    for t in txs:
        h=t.get("txHash") or t.get("hash")
        if not h or h in seen: continue
        try: v=int(t.get("value","0"))/1e18
        except: v=0
        if v<1000: continue
        seen.add(h)
        s=t.get("sender"); r=t.get("receiver")
        sl,rl=lab(s),lab(r)
        sc,rc=cat(s),cat(r)
        # flow classification
        s_exch = sc=="exchange"; r_exch=rc=="exchange"
        s_rout = s in router_set; r_rout = r in router_set
        s_otc = s in otc_set or "OTC" in sl; r_otc = r in otc_set or "OTC" in rl
        if (s_exch or s_rout or s_otc) and (r_exch or r_rout or r_otc):
            ft="exchange_to_exchange"
        elif r_exch and not s_exch: ft="exchange_inflow"
        elif s_exch and not r_exch: ft="exchange_outflow"
        elif rc=="defi": ft="defi_deposit"
        elif sc=="defi": ft="defi_withdrawal"
        elif rc=="validator": ft="staking"
        elif sc=="validator": ft="unstaking"
        elif rc=="bridge" or sc=="bridge": ft="bridge"
        elif "OTC" in sl or "OTC" in rl or s_rout or r_rout: ft="exchange_inflow"
        else: ft="unknown"
        ts=t.get("timestamp")
        iso=datetime.fromtimestamp(ts,tz=timezone.utc).isoformat() if ts else None
        bigtx.append((v,h,iso,s,sl,r,rl,ft))
bigtx.sort(key=lambda x:-x[0])
print(f"total big txs found: {len(bigtx)}")
for v,h,iso,s,sl,r,rl,ft in bigtx[:30]:
    print(f"  {v:10.1f} {ft:20} {sl[:22]:22} -> {rl[:22]:22} {iso}")

# ---- erd17l22 trace
print("="*70)
print("erd17l22 OTC trace")
print("="*70)
src="erd17l22xekj5lvfulatz20xr0llxky6c8zr923r95qg3pfx668m862skjdveh"
si=acc.get(src,{})
print(f"erd17l22 current balance: {bal_of(src)} (prev {prev_top.get(src)})")
# outbound this week
out_txs=[t for t in (si.get("txs") or []) if t.get("sender")==src]
print(f"outbound txs(7d): {len(out_txs)}")
from collections import Counter
dest_c=Counter()
for t in out_txs:
    try: v=int(t.get("value","0"))/1e18
    except: v=0
    dest_c[lab(t.get('receiver'))]+=v
for d,v in dest_c.most_common(8): print(f"   out-> {d[:40]:40} {v:.1f}")
# inbound funding
inb=D.get("erd17l22_inbound")
print(f"inbound txs(14d): {len(inb) if isinstance(inb,list) else inb}")
if isinstance(inb,list):
    inc=Counter()
    for t in inb:
        try: v=int(t.get("value","0"))/1e18
        except: v=0
        if v>100: inc[lab(t.get('sender'))+'|'+t.get('sender','')[:12]]+=v
    for d,v in inc.most_common(10): print(f"   in<- {d[:50]:50} {v:.1f}")

# Mega whale erd18mv2
mw="erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"
print(f"\nMega Whale erd18mv2 balance: {bal_of(mw)} (prev {prev_top.get(mw)}) txs7d: {len(acc.get(mw,{}).get('txs') or [])}")
bs="erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"
print(f"Binance Staking balance: {bal_of(bs)} (prev {prev_top.get(bs)})")

# ---- STAKING
print("="*70)
print("STAKING")
print("="*70)
provs=[p for p in D["providers"] if p.get("locked") and float(p.get("locked",0))>0]
for p in provs:
    p["_locked"]=float(p["locked"])/1e18
total_locked=sum(p["_locked"] for p in provs)
provs.sort(key=lambda p:-p["_locked"])
shares=[p["_locked"]/total_locked for p in provs]
hhi=sum(s*s for s in shares)
top5=sum(shares[:5])*100; top10=sum(shares[:10])*100
print(f"providers(locked>0): {len(provs)} total_locked {total_locked:.1f}")
print(f"top5 {top5:.2f}% top10 {top10:.2f}% HHI {hhi:.6f} (prev HHI {prev['staking_concentration']['hhi']:.6f})")
# prev provider map
prevp={p["name"]:p["locked_egld"] for p in prev["staking_providers"]}
prevp_users={p["name"]:p["num_delegators"] for p in prev["staking_providers"]}
print("\nTop 20 providers (wow):")
for i,p in enumerate(provs[:20],1):
    nm=p.get("identity") or p.get("provider") or p.get("name")
    apr=round(p.get("apr",0)*100,2) if p.get("apr",0)<1 else p.get("apr")
    fee=p.get("serviceFee", p.get("fee"))
    pl=prevp.get(nm)
    wow=p["_locked"]-pl if pl else None
    print(f"  {i:2} {str(nm)[:24]:24} lk {p['_locked']:9.1f} apr {apr} fee {fee} users {p.get('numUsers')} wow {wow if wow is None else round(wow,1)}")

# APR helper
def apr_pct(p):
    a=p.get("apr",0)
    return a*100 if a<1 else a
def fee_pct(p):
    f=p.get("serviceFee", p.get("fee",0))
    return f if f is not None else 0
# apr distribution
print("\nAPR distribution buckets:")
buckets=[("5-6%",5,6),("6-7%",6,7),("7-8%",7,8),("8-9%",8,9),("9-10%",9,10),("10%+",10,100)]
for lbl,mn,mx in buckets:
    sub=[p for p in provs if mn<=apr_pct(p)<mx]
    print(f"  {lbl}: count {len(sub)} locked {sum(p['_locked'] for p in sub):.1f}")
# outliers
print("\nTop APR (fee=0 or low):")
byapr=sorted(provs,key=lambda p:-apr_pct(p))[:5]
for p in byapr: print(f"  {str(p.get('identity'))[:20]:20} apr {apr_pct(p):.2f} fee {fee_pct(p)} locked {p['_locked']:.1f}")
print("Lowest fee:")
byfee=sorted(provs,key=lambda p:(fee_pct(p),-apr_pct(p)))[:6]
for p in byfee: print(f"  {str(p.get('identity'))[:20]:20} apr {apr_pct(p):.2f} fee {fee_pct(p)} locked {p['_locked']:.1f}")
# churn
cur_deleg=sum(p.get("numUsers",0) for p in provs)
prev_deleg=sum(prevp_users.values())
gaining=losing=0
for p in provs:
    nm=p.get("identity") or p.get("name")
    pu=prevp_users.get(nm)
    if pu is not None:
        if p.get("numUsers",0)>pu: gaining+=1
        elif p.get("numUsers",0)<pu: losing+=1
print(f"\nchurn: cur_deleg {cur_deleg} prev_deleg {prev_deleg} added {cur_deleg-prev_deleg} gaining {gaining} losing {losing}")
print(f"total_delegated current {total_locked:.1f}")

# validator movements
cur_names={(p.get("identity") or p.get("name")) for p in provs}
prev_names=set(prevp.keys())
joining=cur_names-prev_names
leaving=prev_names-cur_names
print(f"\nvalidator joiners: {joining}")
print(f"validator leavers: {leaving}")
cur_locked_by={(p.get('identity') or p.get('name')):p['_locked'] for p in provs}
print("notable joiners (>50K):")
for n in joining:
    if cur_locked_by.get(n,0)>50000: print(f"   {n}: {cur_locked_by[n]:.1f}")
print("notable leavers (>50K):")
for n in leaving:
    if prevp.get(n,0)>50000: print(f"   {n}: prev {prevp[n]:.1f}")

# yield-chase tracking
print("\nyield-chase providers wow:")
for nm in ["ninjastaking","egldstakingprovider","orius","valuestaking","procryptostaking","mapleleafnetwork"]:
    cur=cur_locked_by.get(nm); pl=prevp.get(nm)
    if cur and pl: print(f"   {nm:22} cur {cur:.1f} prev {pl:.1f} wow {cur-pl:+.1f}")

# ---- TOKENS
print("="*70)
print("TOKENS")
print("="*70)
th=D["tokens_holders"]
prev_th={t["identifier"]:t for t in prev["top_tokens_by_holders"]}
print("top by holders (wow):")
for t in th[:10]:
    pid=prev_th.get(t["identifier"])
    ph=pid["holders"] if pid else None
    hc=t["accounts"]-ph if ph else None
    print(f"  {t['identifier']:16} {t.get('name','')[:14]:14} holders {t['accounts']:8} prev {ph} chg {hc}")
print("\ntop by transactions:")
for t in D["tokens_txs"][:10]:
    print(f"  {t['identifier']:16} {t.get('name','')[:14]:14} txns {t.get('transactions')}")
print("\ntop by mcap:")
for t in D["tokens_mcap"][:10]:
    print(f"  {t['identifier']:16} {t.get('name','')[:14]:14} mcap {t.get('marketCap')}  price {t.get('price')}")

# supply events (stablecoins + WEGLD)
print("\nsupply events (vs prev top_tokens_by_holders supply):")
prev_supply={t["identifier"]:t.get("supply") for t in prev["top_tokens_by_holders"]}
cur_by_id={t["identifier"]:t for t in th}
for tid,ps in prev_supply.items():
    ct=cur_by_id.get(tid)
    if ct and ps:
        cs=ct.get("supply")
        if cs and ps:
            chg=100*(float(cs)-float(ps))/float(ps)
            if abs(chg)>0.1:
                print(f"  {tid}: supply {ps} -> {cs} ({chg:+.3f}%)")

# ---- xExchange / mex
print("="*70)
print("xEXCHANGE")
print("="*70)
mp=D["mex_pairs"]; meco=D["mex_economics"]
pairs=[]
for p in mp:
    v=p.get("volume24h") or 0
    pairs.append((p.get("baseName","?")+"/"+p.get("quoteName","?"), v, p.get("totalValue"), p.get("tradesCount24h",p.get("trades24h"))))
pairs.sort(key=lambda x:-(x[1] or 0))
totvol=sum((p[1] or 0) for p in pairs)
print(f"mex price {meco['price']:.4e} mcap {meco['marketCap']} pairs {meco['marketPairs']} vol24h(eco) {meco.get('volume24h')}")
print(f"sum pairs vol24h {totvol:.1f}")
prev_mexp=prev["xexchange"]["mex_price_usd"]
print(f"mex price wow: {100*(meco['price']-prev_mexp)/prev_mexp:+.3f}%")
print("top pairs:")
for nm,v,tv,tc in pairs[:5]:
    print(f"  {nm:30} vol {v:.1f} share {100*(v or 0)/totvol:.2f}% tvl {tv} trades {tc}")

# ---- DeFi TVL
print("="*70)
print("DEFI TVL")
print("="*70)
tt=D["tvl_tokens"]
def mcap(tid):
    t=tt.get(tid)
    if isinstance(t,dict) and "marketCap" in t: return t.get("marketCap") or 0
    return 0
def supply_units(tid):
    t=tt.get(tid)
    if isinstance(t,dict):
        try: return float(t.get("supply",0))
        except: return 0
    return 0
hatom_lending = sum(mcap(x) for x in ["HUSDC-d80042","HEGLD-d61095","HUSDT-6f0914","HWBTC-49ca31","HWETH-b3d17e","HBUSD-ac1fca","HHTM-e03ba5","HMEX-df6df7","HUTK-4fa4b2","HWTAO-2e9136"])
hatom_lsd = mcap("SEGLD-3ad2d0")+mcap("SWTAO-356a25")
hatom_ush = mcap("USH-111e09")
xoxno_lsd = mcap("XEGLD-e413ed")
print(f"Hatom Lending TVL(usd) {hatom_lending:.1f}  (prev {prev['defi_tvl']['Hatom Lending']:.1f})")
print(f"  in EGLD: {hatom_lending/price:.1f} (prev {prev['defi_tvl']['Hatom Lending']/pecon['egld_price_usd']:.1f})")
print(f"Hatom LSD TVL(usd) {hatom_lsd:.1f}  SEGLD mcap {mcap('SEGLD-3ad2d0'):.1f} SWTAO {mcap('SWTAO-356a25'):.1f}")
print(f"  in EGLD: {hatom_lsd/price:.1f}")
print(f"Hatom USH TVL(usd) {hatom_ush:.1f} (prev {prev['defi_tvl']['Hatom USH']:.1f})")
print(f"XOXNO LSD TVL(usd) {xoxno_lsd:.1f} (prev {prev['defi_tvl']['XOXNO LSD']:.1f})  in EGLD {xoxno_lsd/price:.1f}")
# xExchange TVL = sum WEGLD balances *2? run8 used tvl_usd 2272067 / tvl_egld 585584. Let me sum WEGLD balances
wegld_total=0
for c,b in D["wegld"].items():
    if isinstance(b,dict) and "balance" in b:
        wegld_total+=int(b["balance"])/1e18
print(f"WEGLD contract balances total: {wegld_total:.1f} EGLD")
# token mcap detail for SEGLD/XEGLD supply
print(f"SEGLD supply {supply_units('SEGLD-3ad2d0'):.1f} price {tt.get('SEGLD-3ad2d0',{}).get('price')}")
print(f"XEGLD supply {supply_units('XEGLD-e413ed'):.1f} price {tt.get('XEGLD-e413ed',{}).get('price')}")
print(f"USDC supply {supply_units('HUSDC-d80042')}")

print("\nProtocol transfers_24h:")
for nm,pd in D["proto"].items():
    c=pd["transfers_24h"]
    cv=c.get("count") if isinstance(c,dict) else c
    print(f"  {nm:22} transfers24h {cv}  bal {int(pd['balance'].get('balance','0'))/1e18 if isinstance(pd['balance'],dict) and 'balance' in pd['balance'] else '?':}")

# ---- ANOMALIES (z-scores)
print("="*70)
print("ANOMALIES / Z-SCORES")
print("="*70)
rb=learn["runs"][-1]["running_baselines"]
def zscore(arr, cur):
    if len(arr)<4: return None
    mean=sum(arr)/len(arr)
    var=sum((x-mean)**2 for x in arr)/len(arr)
    sd=math.sqrt(var)
    z=(cur-mean)/sd if sd>0 else 0
    return mean,sd,z
for metric,cur in [("egld_price_usd",price),("dex_volume_24h_usd",totvol),
                   ("staked_egld",staked),("staked_ratio",staked_ratio),
                   ("mex_price_usd",meco["price"]),("total_delegators",cur_deleg)]:
    arr=rb.get(metric,[])
    res=zscore(arr,cur)
    if res:
        m,sd,z=res
        print(f"  {metric:22} cur {cur} mean {m:.6g} sd {sd:.6g} z {z:+.3f}  (N={len(arr)})")
    else:
        print(f"  {metric:22} cur {cur} N={len(arr)} (insufficient for z)")
print("\nbaselines (for append):")
for k,v in rb.items():
    print(f"  {k}: {v}")
