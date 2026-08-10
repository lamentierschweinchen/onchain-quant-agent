#!/usr/bin/env python3
"""Run #20 exploratory analysis."""
import json
from datetime import datetime, timezone
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D=json.load(open(f"{REPO}/data/collected/2026-08-10.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
lm,cm={},{}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"):
                lm[a]=m.get("name","Unknown"); cm[a]=m.get("category","unknown")
def lab(a): return lm.get(a,"Unknown")
econ=D["economics"]; pecon=prev["economics"]
price=econ["price"]; pp=pecon["egld_price_usd"]
print("=== MACRO (7d) ===")
print(f"EGLD ${price} vs ${pp} = {100*(price-pp)/pp:+.2f}%")
be=D["btc_eth"]
print(f"BTC {be['bitcoin']['usd']} vs {pecon['btc_price_usd']} = {100*(be['bitcoin']['usd']-pecon['btc_price_usd'])/pecon['btc_price_usd']:+.2f}%")
print(f"ETH {be['ethereum']['usd']} vs {pecon['eth_price_usd']} = {100*(be['ethereum']['usd']-pecon['eth_price_usd'])/pecon['eth_price_usd']:+.2f}%")
print(f"staked {econ['staked']:,} vs {pecon['staked_egld']:,} = {econ['staked']-pecon['staked_egld']:+,}")
sr=econ['staked']/econ['circulatingSupply']
print(f"staked ratio {sr*100:.3f}% vs {pecon['staked_ratio']*100:.3f}%")
st=D["stats"]; pact=prev["activity"]
print(f"txs +{st['transactions']-pact['total_transactions']:,} accounts +{st['accounts']-pact['total_accounts']:,} epochs +{st['epoch']-pact['epoch']}")

print("\n=== OTC HUB, three windows ===")
for w,nm in [("otc_hub_trace","WEEK Aug3-10 (7d)"),
             ("otc_hub_trace_peak_run17","RUN #17 PEAK Jul13-20 (RE-NET)")]:
    vn=D[w]["venue_netting"]
    print(f"\n-- {nm}")
    print(f"   gross_out {vn['gross_out']:,.0f}  gross_in {vn['gross_in']:,.0f}  circular {vn['circular']:,.0f} "
          f"({100*vn['circular']/vn['gross_out']:.0f}%)  NET ONE-WAY {vn['net_one_way']:,.0f}")
    print(f"   unresolved out {vn['unresolved_out']:,.0f} in {vn['unresolved_in']:,.0f}")
    for v in sorted(vn["net_by_venue"], key=lambda k:-abs(vn["net_by_venue"][k])):
        o=vn["outbound_by_venue"].get(v,0); i=vn["inbound_by_venue"].get(v,0)
        print(f"     {v:34s} desk->venue {o:11,.0f}  venue->desk {i:11,.0f}  NET {o-i:+11,.0f}")

print("\n=== direct desk feeders this week ===")
for a,rec in D["otc_hub_trace"]["inbound"].items():
    if rec.get("kind")=="direct" and rec["amount"]>1000:
        print(f"  {rec['amount']:,.0f} <- {lab(a)} ({a[:16]})")

print("\n=== desk balances ===")
acc=D["accounts"]
def b(a):
    x=acc.get(a)
    return int(x["info"]["balance"])/1e18 if x and isinstance(x.get("info"),dict) and "balance" in x["info"] else None
UP="erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
DI="erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
print(f"  UPbit OTC Desk {b(UP):,.0f} (prev 32,202)")
print(f"  OTC Distribution {b(DI):,.0f} (prev 32,852)")
print(f"  COMBINED {b(UP)+b(DI):,.0f} vs 65,053 -> {b(UP)+b(DI)-65053.478:+,.0f}")

print("\n=== exchange balances vs previous ===")
pb=prev["exchange_balances"]
def ent(a):
    l=lab(a)
    if "Binance" in l: return "Binance"
    if "Coinbase" in l: return "Coinbase"
    if "Crypto.com" in l: return "Crypto.com"
    for e2 in ["UPbit","Bybit","MEXC","Bitget","Gate.io","KuCoin","Bitfinex","Tokero"]:
        if e2 in l: return e2
    return None
prev_top={x["address"]:x["balance_egld"] for x in prev["top_accounts"]}
cur_top={x["address"]:int(x["balance"])/1e18 for x in D["top_accounts"]}
exch=[a for a,c in cm.items() if c=="exchange"]
BAD={"erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp29trp6qsl2gdvvz2eqra76xc",
     "erd1ty4pvmjtl3mnsjvnsxqkm3xqm4dm7ppgz9sh4nk4tqvlmw0jyggqzn4mdc"}
ec,ep,ew,noprior={},{},{},[]
for a in exch:
    if a in BAD: continue
    e2=ent(a)
    if not e2: continue
    cur=b(a) or cur_top.get(a)
    p=prev_top.get(a)
    if cur is None: continue
    if p is None:
        noprior.append((e2,lab(a),cur)); continue
    ec[e2]=ec.get(e2,0)+cur; ep[e2]=ep.get(e2,0)+p; ew[e2]=ew.get(e2,0)+1
tot=0
for e2 in sorted(ec,key=lambda k:-abs(ec[k]-ep[k])):
    d=ec[e2]-ep[e2]; tot+=d
    print(f"  {e2:14s} {ec[e2]:12,.0f}  ({d:+11,.0f}, {100*d/ep[e2] if ep[e2] else 0:+6.2f}%)  wallets={ew[e2]}")
print(f"  NET {tot:+,.0f}")
print("  no prior (excluded):",noprior)

print("\n=== demand instruments ===")
MEGA="erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"
CBR="erd1lgdltequh7627rtlacmcp6p5vec7zmu2rxhu7pjwvcja8f4a9gqq9vcc70"
print(f"  Mega Whale {b(MEGA):,.4f} (prev 1,093,311.6012) delta {b(MEGA)-1093311.6011787355:+,.4f}")
print(f"  Coinbase Routing {b(CBR):,.2f} (prev 77.13)")
print(f"  mega whale txs in/out: {len(D['mega_whale_inbound'])}/{len(D['mega_whale_outbound'])}")
mp=D["mex_pairs"]
tv=sum((p.get("volume24h") or 0) for p in mp); tt=sum((p.get("totalValue") or 0) for p in mp)
print(f"  DEX vol24h ${tv:,.0f} (prev ${prev['xexchange']['volume_24h_usd']:,.0f}) pool TVL ${tt:,.0f} (prev ${prev['xexchange']['pool_tvl_usd']:,.0f})")
print(f"  turnover {100*tv/tt:.3f}% (prev {prev['xexchange']['turnover_ratio_pct']:.3f}%)")
pairs=sorted(mp,key=lambda p:-(p.get("volume24h") or 0))
for p in pairs[:4]:
    print(f"     {p.get('baseName')}/{p.get('quoteName')}: ${p.get('volume24h') or 0:,.0f} ({100*(p.get('volume24h') or 0)/tv:.1f}%)")

print("\n=== Unknown Whale I ===")
wi=D["whale_i_info"]
print(f"  balance {int(wi['balance'])/1e18:,.0f} nonce {wi.get('nonce')} shard {wi.get('shard')}")
print(f"  60d inbound txs {len(D['whale_i_inbound_60d'])} outbound {len(D['whale_i_outbound_60d'])}")
def agg(txs,key):
    o={}
    for t in txs:
        try: v=int(t.get("value","0"))/1e18
        except: v=0
        if v<=0: continue
        o[t[key]]=o.get(t[key],0)+v
    return sorted(o.items(),key=lambda x:-x[1])
print("  TOP INBOUND SOURCES 60d:")
for a,v in agg(D["whale_i_inbound_60d"],"sender")[:8]:
    print(f"    {v:12,.0f} <- {lab(a)[:45]:45s} {a[:14]}")
print("  TOP OUTBOUND DESTS 60d:")
for a,v in agg(D["whale_i_outbound_60d"],"sender" if False else "receiver")[:8]:
    print(f"    {v:12,.0f} -> {lab(a)[:45]:45s} {a[:14]}")
ts_in=[t.get("timestamp") for t in D["whale_i_inbound_60d"] if t.get("timestamp")]
if ts_in:
    print(f"  inbound window {datetime.fromtimestamp(min(ts_in),tz=timezone.utc).date()} .. {datetime.fromtimestamp(max(ts_in),tz=timezone.utc).date()}")
fn={}
for t in D["whale_i_outbound_60d"]:
    fn[t.get("function") or "(transfer)"]=fn.get(t.get("function") or "(transfer)",0)+1
print("  outbound functions:",dict(sorted(fn.items(),key=lambda x:-x[1])[:8]))

print("\n=== providers: fee response test (REC #7) ===")
provs=[p for p in D["providers"] if p.get("locked") and float(p["locked"])>0]
for p in provs: p["_lk"]=float(p["locked"])/1e18
provs.sort(key=lambda p:-p["_lk"])
tl=sum(p["_lk"] for p in provs)
prevfee={p["name"]:p.get("fee") for p in prev["staking_providers"]}
prevlk={p["name"]:p["locked_egld"] for p in prev["staking_providers"]}
prevu={p["name"]:p["num_delegators"] for p in prev["staking_providers"]}
prevapr={p["name"]:p.get("apr") for p in prev["staking_providers"]}
fee_changes=[]
for p in provs:
    nm=p.get("identity") or p["provider"]
    pf=prevfee.get(nm); cf=p.get("serviceFee")
    if pf is not None and cf is not None and abs(cf-pf)>1e-9:
        fee_changes.append((nm,pf*100,cf*100,p["_lk"]))
print("  FEE CHANGES:",fee_changes if fee_changes else "NONE - no competitive repricing")
apr_changes=[]
for p in provs:
    nm=p.get("identity") or p["provider"]
    pa=prevapr.get(nm); ca=p.get("apr")
    if pa and ca and abs(ca-pa)>0.15:
        apr_changes.append((nm,round(pa,2),round(ca,2),round(p["_lk"])))
print("  APR moves >0.15pp:",sorted(apr_changes,key=lambda x:-abs(x[2]-x[1]))[:10])
print(f"  total delegated {tl:,.0f} vs {prev['staking_concentration']['total_locked_egld']:,.0f} = {tl-prev['staking_concentration']['total_locked_egld']:+,.0f}")
cd=sum(p.get("numUsers",0) for p in provs); pd_=sum(prevu.values())
print(f"  delegators {cd:,} vs {pd_:,} = {cd-pd_:+,}")
shares=[p["_lk"]/tl for p in provs]
print(f"  HHI {sum(s*s for s in shares):.5f} top5 {sum(shares[:5])*100:.2f}% top10 {sum(shares[:10])*100:.2f}%")
moves=[]
for p in provs:
    nm=p.get("identity") or p["provider"]
    if nm in prevlk:
        moves.append((nm,p["_lk"]-prevlk[nm],(p.get("numUsers",0)-prevu.get(nm,0)),p.get("apr"),(p.get("serviceFee") or 0)*100))
moves.sort(key=lambda x:-abs(x[1]))
print("  TOP PROVIDER MOVES:")
for nm,d,du,a,f in moves[:12]:
    print(f"    {nm[:28]:28s} {d:+10,.0f}  users {du:+5d}  apr {a:.2f} fee {f:.0f}%")
hi=[p for p in provs if (p.get("apr") or 0)>=8.8 and (p.get("identity") or p["provider"]) in prevlk]
print(f"  APR>=8.8 cohort net: {sum(p['_lk']-prevlk[p.get('identity') or p['provider']] for p in hi):+,.0f} ({len(hi)} providers)")

print("\n=== tokens / supply ===")
tt_=D["tvl_tokens"]
prevls=prev["lsd_supply"]
for tid in ["SEGLD-3ad2d0","XEGLD-e413ed","SWTAO-356a25","USH-111e09"]:
    c=tt_.get(tid,{}); cs=float(c.get("supply") or 0); ps=float(prevls.get(tid) or 0)
    print(f"  {tid}: supply {cs:,.0f} vs {ps:,.0f} = {100*(cs-ps)/ps if ps else 0:+.3f}%  price {c.get('price')} mcap {c.get('marketCap')}")
for sid in ["USDC-c76f1f","USDT-f8c08c"]:
    c=D.get("stable_"+sid,{})
    print(f"  {sid}: supply {float(c.get('supply') or 0):,.0f} price {c.get('price')}")
print("  WEGLD supply",D["wegld_token"].get("supply"))

print("\n=== defi tvl ===")
def mc(t):
    x=tt_.get(t); return (x.get("marketCap") or 0) if isinstance(x,dict) else 0
hl=sum(mc(x) for x in ["HUSDC-d80042","HEGLD-d61095","HUSDT-6f0914","HWBTC-49ca31","HWETH-b3d17e","HBUSD-ac1fca","HHTM-e03ba5","HMEX-df6df7","HUTK-4fa4b2","HWTAO-2e9136"])
print(f"  Hatom Lending ${hl:,.0f} (prev ${prev['defi_tvl']['Hatom Lending']:,.0f}) EGLD {hl/price:,.0f} vs {prev['defi_tvl']['Hatom Lending']/pp:,.0f} = {100*((hl/price)-(prev['defi_tvl']['Hatom Lending']/pp))/(prev['defi_tvl']['Hatom Lending']/pp):+.2f}%")
print(f"  price move {100*(price-pp)/pp:+.2f}% -> inverse ratio {abs(100*((hl/price)-(prev['defi_tvl']['Hatom Lending']/pp))/(prev['defi_tvl']['Hatom Lending']/pp))/abs(100*(price-pp)/pp):.2f}")
print(f"  Hatom LSD ${mc('SEGLD-3ad2d0')+mc('SWTAO-356a25'):,.0f}  USH ${mc('USH-111e09'):,.0f}  XOXNO ${mc('XEGLD-e413ed'):,.0f}")
we=sum(int(x["balance"])/1e18 for x in D["wegld"].values() if isinstance(x,dict) and "balance" in x)
print(f"  xExchange WEGLD contracts {we:,.0f} EGLD = ${we*price:,.0f}")
for n,v in D["proto"].items():
    c=v["transfers_24h"]; print(f"  {n}: {c.get('count') if isinstance(c,dict) else c} transfers 24h")

print("\n=== wallet changes (top-60 trim) ===")
N=len(prev["top_accounts"])
ct=dict(sorted(cur_top.items(),key=lambda kv:-kv[1])[:N])
ch=[]
for a,v in ct.items():
    if a in prev_top and cm.get(a)!="system":
        d=v-prev_top[a]
        if abs(d)>2000: ch.append((a,lab(a),prev_top[a],v,d))
ch.sort(key=lambda x:-abs(x[4]))
for a,l,p,c,d in ch[:15]:
    print(f"  {d:+11,.0f}  {l[:42]:42s} {a[:14]} ({p:,.0f} -> {c:,.0f})")
