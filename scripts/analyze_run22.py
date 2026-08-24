#!/usr/bin/env python3
"""Run #22 exploratory analysis."""
import json
from datetime import datetime, timezone
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D=json.load(open(f"{REPO}/data/collected/2026-08-24.json"))
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

print("\n=== OTC HUB, all measured windows ===")
for w,nm in [("otc_hub_trace","WEEK Aug17-24 (7d)"),
             ("otc_hub_trace_julywave","JULY EPISODE Jul6-27 ONE WINDOW"),
             ("otc_hub_trace_wave2ext","WAVE #2 EXTENDED Aug3-24"),
             ("otc_hub_trace_run16","BACKFILL run #16 Jul6-13"),
             ("otc_hub_trace_run18","BACKFILL run #18 Jul20-27"),
             ("otc_hub_trace_peak_run17","RUN #17 PEAK Jul13-20 (carried)")]:
    if w not in D or "venue_netting" not in D.get(w,{}):
        print(f"\n-- {nm}: MISSING"); continue
    vn=D[w]["venue_netting"]
    print(f"\n-- {nm}")
    print(f"   gross_out {vn['gross_out']:,.0f}  gross_in {vn['gross_in']:,.0f}  circular {vn['circular']:,.0f} "
          f"({100*vn['circular']/vn['gross_out'] if vn['gross_out'] else 0:.0f}%)  NET ONE-WAY {vn['net_one_way']:,.0f}")
    print(f"   unresolved out {vn['unresolved_out']:,.0f} in {vn['unresolved_in']:,.0f}")
    for v in sorted(vn["net_by_venue"], key=lambda k:-abs(vn["net_by_venue"][k])):
        o=vn["outbound_by_venue"].get(v,0); i=vn["inbound_by_venue"].get(v,0)
        print(f"     {v:34s} desk->venue {o:11,.0f}  venue->desk {i:11,.0f}  NET {o-i:+11,.0f}")

print("\n=== direct desk feeders this week ===")
for a,rec in D["otc_hub_trace"]["inbound"].items():
    if rec["amount"]>1000:
        print(f"  {rec['amount']:>10,.0f} <- {rec.get('kind'):7s} {lab(a)[:40]:40s} ({a[:16]}) bal={rec.get('balance')}")
print("=== desk destinations this week ===")
for a,rec in D["otc_hub_trace"]["outbound"].items():
    if rec["amount"]>1000:
        print(f"  {rec['amount']:>10,.0f} -> {rec.get('kind'):7s} {lab(a)[:40]:40s} ({a[:16]}) terms={list(rec.get('terminals',{}))[:2]}")

print("\n=== desk balances ===")
acc=D["accounts"]
def b(a):
    x=acc.get(a)
    return int(x["info"]["balance"])/1e18 if x and isinstance(x.get("info"),dict) and "balance" in x["info"] else None
UP="erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
DI="erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
print(f"  UPbit OTC Desk {b(UP):,.0f} (prev 38,392)")
print(f"  OTC Distribution {b(DI):,.0f} (prev 22,174)")
print(f"  COMBINED {b(UP)+b(DI):,.0f} vs 60,566 -> {b(UP)+b(DI)-60565.86:+,.0f}")

print("\n=== exchange balances vs previous ===")
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
print(f"  Mega Whale {b(MEGA):,.4f} (prev 1,099,059.3) delta {b(MEGA)-1099059.3223354353:+,.4f}")
print(f"  Coinbase Routing {b(CBR):,.2f} (prev ~16)")
print(f"  mega whale txs in/out: {len(D['mega_whale_inbound'])}/{len(D['mega_whale_outbound'])}")
for t in D['mega_whale_inbound'][:6]:
    print(f"     IN {int(t.get('value','0'))/1e18:,.1f} <- {lab(t['sender'])[:34]} {t['sender'][:14]}")
mp=D["mex_pairs"]
tv=sum((p.get("volume24h") or 0) for p in mp); tt=sum((p.get("totalValue") or 0) for p in mp)
print(f"  DEX vol24h ${tv:,.0f} (prev ${prev['xexchange']['volume_24h_usd']:,.0f}) pool TVL ${tt:,.0f} (prev ${prev['xexchange']['pool_tvl_usd']:,.0f})")
print(f"  turnover {100*tv/tt:.3f}% (prev {prev['xexchange']['turnover_ratio_pct']:.3f}%)")
pairs=sorted(mp,key=lambda p:-(p.get("volume24h") or 0))
for p in pairs[:5]:
    print(f"     {p.get('baseName')}/{p.get('quoteName')}: vol ${p.get('volume24h') or 0:,.0f} ({100*(p.get('volume24h') or 0)/tv:.1f}%) tvl ${p.get('totalValue') or 0:,.0f} trades {p.get('tradesCount24h') or p.get('trades24h')}")

print("\n=== REC #8: MEX pair depth ===")
mw=D.get("mex_pairs_wide") or []
mexpairs=[p for p in mw if "MEX" in (p.get("baseSymbol","")+p.get("quoteSymbol","")) or "MEX" in (p.get("baseName","")+p.get("quoteName",""))]
for p in mexpairs[:8]:
    print(f"  {p.get('baseSymbol')}/{p.get('quoteSymbol')} price {p.get('basePrice')} vol24h ${p.get('volume24h') or 0:,.0f} tvl ${p.get('totalValue') or 0:,.0f} trades24h {p.get('tradesCount24h') or p.get('trades24h')}")
mt=D.get("mex_token") or {}
print(f"  MEX token: price {mt.get('price')} mcap {mt.get('marketCap')} supply {mt.get('supply')} accounts {mt.get('accounts')}")
print(f"  mex_economics: {json.dumps(D['mex_economics'])[:400]}")

wi=D["whale_i_info"]
print("\n=== Unknown Whale I (balance only this run) ===")
print(f"  balance {int(wi['balance'])/1e18:,.0f} nonce {wi.get('nonce')} shard {wi.get('shard')}")
hub=D["otc_hub_trace"]
UPd,DId=UP,DI
PIPE=set(hub["inbound"])|set(hub["outbound"])|{UPd,DId}
for w in ("julywave","wave2ext","run16","run18","peak_run17"):
    h=D.get(f"otc_hub_trace_{w}")
    if h: PIPE|=set(h["inbound"])|set(h["outbound"])
ROUTERS=set(kn.get("exchange_routers",{}).keys())
def cls(a):
    if a in (UPd,DId): return "DESK"
    if a in ROUTERS: return "ROUTER"
    if a in PIPE: return "PIPE"
    if cm.get(a)=="exchange": return "EXCHANGE"
    return "EXTERNAL"
def agg(txs,key):
    o={}
    for t in txs:
        try: v=int(t.get("value","0"))/1e18
        except: v=0
        if v<=0: continue
        o[t[key]]=o.get(t[key],0)+v
    return sorted(o.items(),key=lambda x:-x[1])

print("\n=== REC #1: UPbit replenishment (30d inbound) ===")
for a,v in (D.get("upbit_inbound_30d") or {}).items():
    txs=v["txs"]; print(f"  {v['label']}: {len(txs)} inbound txs 30d")
    for s,val in agg(txs,"sender")[:10]:
        print(f"     {val:12,.0f} <- {lab(s)[:40]:40s} {s[:16]}")

print("\n=== REC #2: THE 229,865 EGLD UNBOND ===")
uw=D.get("unbond_wallet_info") or {}
print(f"  wallet balance {int(uw.get('balance','0'))/1e18:,.2f} nonce {uw.get('nonce')} (prev 2,253.5)")
for row in (D.get("unbond_wallet_delegation") or []):
    ub=int(row.get("userUnBondable","0"))/1e18
    act=int(row.get("userActiveStake","0"))/1e18
    cl=int(row.get("claimableRewards","0"))/1e18
    print(f"  contract {row.get('contract')[:24]}  unBondable {ub:,.0f}  activeStake {act:,.0f}  claimable {cl:,.2f}")
    for u in row.get("userUndelegatedList",[]):
        print(f"      pending {int(u['amount'])/1e18:,.0f} EGLD, {u['seconds']}s remaining ({u['seconds']/86400:.2f}d)")
print(f"  outbound 7d txs {len(D.get('unbond_wallet_out_7d') or [])}, inbound {len(D.get('unbond_wallet_in_7d') or [])}")
for t in (D.get("unbond_wallet_out_7d") or [])[:10]:
    print(f"    OUT {int(t.get('value','0'))/1e18:,.2f} -> {lab(t['receiver'])[:34]:34s} {t['receiver'][:14]} fn={t.get('function')}")
for t in (D.get("unbond_wallet_in_7d") or [])[:10]:
    print(f"    IN  {int(t.get('value','0'))/1e18:,.2f} <- {lab(t['sender'])[:34]:34s} {t['sender'][:14]} fn={t.get('function')}")

print("\n=== REC #4: 100%-FEE PROVIDERS ===")
for ident,plist in (D.get("fee100_identities") or {}).items():
    for p in (plist if isinstance(plist,list) else []):
        print(f"  {ident}: locked {float(p.get('locked',0) or 0)/1e18:,.0f} fee {p.get('serviceFee')} apr {p.get('apr')} users {p.get('numUsers')} nodes {p.get('numNodes')} owner {p.get('owner','')[:20]}")
print("  owners:",[(o['identity'],o['owner'][:20]) for o in (D.get('fee100_owners') or [])])
for ow,rec in (D.get("fee100_owner_flows") or {}).items():
    inf=rec.get("info") or {}
    print(f"  owner {ow[:20]} ({rec['identity']}) bal {int(inf.get('balance','0'))/1e18:,.2f} nonce {inf.get('nonce')} out30d {len(rec.get('out_30d') or [])} in30d {len(rec.get('in_30d') or [])}")
    cps={}
    for t in (rec.get("out_30d") or []):
        v=int(t.get("value","0"))/1e18
        if v>0: cps[t["receiver"]]=cps.get(t["receiver"],0)+v
    for a,v in sorted(cps.items(),key=lambda x:-x[1])[:5]:
        print(f"      OUT {v:11,.2f} -> {lab(a)[:34]:34s} {a[:16]}")
    cps={}
    for t in (rec.get("in_30d") or []):
        v=int(t.get("value","0"))/1e18
        if v>0: cps[t["sender"]]=cps.get(t["sender"],0)+v
    for a,v in sorted(cps.items(),key=lambda x:-x[1])[:5]:
        print(f"      IN  {v:11,.2f} <- {lab(a)[:34]:34s} {a[:16]}")

print("\n=== REC #6: USDT / USDC largest holders ===")
for nm,key in [("USDT-f8c08c","usdt_accounts"),("USDC-c76f1f","usdc_accounts")]:
    rows=D.get(key)
    if not isinstance(rows,list): print(f"  {nm}: {rows}"); continue
    tot=sum(float(r.get("balance",0))/1e6 for r in rows)
    print(f"  {nm}: top {len(rows)} holders sum {tot:,.0f}")
    for r in rows[:10]:
        a=r.get("address","")
        print(f"     {float(r.get('balance',0))/1e6:12,.0f}  {lab(a)[:34]:34s} {a[:16]}")

print("\n=== REC #8: Whale I largest external counterparty ===")
cpi=D.get("whale_i_cp_info") or {}
print(f"  erd1qkazru7aw5 balance {int(cpi.get('balance','0'))/1e18:,.0f} nonce {cpi.get('nonce')}")
print(f"  out30d {len(D.get('whale_i_cp_out_30d') or [])} in30d {len(D.get('whale_i_cp_in_30d') or [])}")
for nm,k,txs in [("OUT","receiver",D.get("whale_i_cp_out_30d") or []),("IN","sender",D.get("whale_i_cp_in_30d") or [])]:
    agv={}
    for t in txs:
        v=int(t.get("value","0"))/1e18
        if v>0: agv[t[k]]=agv.get(t[k],0)+v
    print(f"  {nm}: {len(agv)} counterparties, {sum(agv.values()):,.0f} EGLD")
    for a,v in sorted(agv.items(),key=lambda x:-x[1])[:6]:
        print(f"     {v:11,.0f} {cls(a):9s} {lab(a)[:34]:34s} {a[:16]}")

print("\n=== REC #9/#10: UNBONDING POOL (provider movers) ===")
print("  big movers recorded:",len(D.get("provider_big_movers") or []))
print("  unbonding_pool wallets:",len(D.get("unbonding_pool") or []))
for r in (D.get("unbonding_pool") or []):
    print("   ",r["wallet"][:16],r.get("balance_egld"),json.dumps(r.get("delegation"))[:200])

print("\n=== providers: fee cut follow-through (REC #4) ===")
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
        fee_changes.append((nm,round(pf*100,2),round(cf*100,2),round(p["_lk"]),
                            round(p["_lk"]-prevlk.get(nm,p["_lk"])),
                            p.get("numUsers",0)-prevu.get(nm,p.get("numUsers",0))))
print("  FEE CHANGES:",fee_changes if fee_changes else "NONE")
for nm in ("egldstakingprovider","procryptostaking","syndicatex"):
    p=next((x for x in provs if (x.get("identity") or x["provider"])==nm),None)
    if p:
        print(f"  {nm}: locked {p['_lk']:,.0f} ({p['_lk']-prevlk.get(nm,0):+,.0f}) users {p.get('numUsers')} ({p.get('numUsers',0)-prevu.get(nm,0):+d}) apr {p.get('apr'):.2f} fee {(p.get('serviceFee') or 0)*100:.0f}%")
print(f"  total delegated {tl:,.0f} vs {prev['staking_concentration']['total_locked_egld']:,.0f} = {tl-prev['staking_concentration']['total_locked_egld']:+,.0f}")
cd=sum(p.get("numUsers",0) for p in provs); pd_=sum(prevu.values())
print(f"  delegators {cd:,} vs {pd_:,} = {cd-pd_:+,}")
shares=[p["_lk"]/tl for p in provs]
print(f"  HHI {sum(s*s for s in shares):.5f} top5 {sum(shares[:5])*100:.2f}% top10 {sum(shares[:10])*100:.2f}%")
dn=(econ['staked']-pecon['staked_egld'])-(tl-prev['staking_concentration']['total_locked_egld'])
print(f"  DIRECT-NODE residual: {dn:+,.0f}")
moves=[]
for p in provs:
    nm=p.get("identity") or p["provider"]
    if nm in prevlk:
        moves.append((nm,p["_lk"]-prevlk[nm],(p.get("numUsers",0)-prevu.get(nm,0)),p.get("apr"),(p.get("serviceFee") or 0)*100))
moves.sort(key=lambda x:-abs(x[1]))
print("  TOP PROVIDER MOVES:")
for nm,d,du,a,f in moves[:14]:
    print(f"    {nm[:28]:28s} {d:+10,.0f}  users {du:+5d}  apr {a:.2f} fee {f:.0f}%")
hi=[p for p in provs if (p.get("apr") or 0)>=8.8 and (p.get("identity") or p["provider"]) in prevlk]
print(f"  APR>=8.8 cohort net: {sum(p['_lk']-prevlk[p.get('identity') or p['provider']] for p in hi):+,.0f} ({len(hi)} providers)")
zf=[p for p in provs if (p.get("serviceFee") or 0)==0 and (p.get("identity") or p["provider"]) in prevlk]
print(f"  zero-fee cohort net: {sum(p['_lk']-prevlk[p.get('identity') or p['provider']] for p in zf):+,.0f} ({len(zf)} providers)")

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
print("  dataapi refetch:",json.dumps(D["dataapi_refetch_log"]))

print("\n=== defi tvl ===")
def mc(t):
    x=tt_.get(t); return (x.get("marketCap") or 0) if isinstance(x,dict) else 0
hl=sum(mc(x) for x in ["HUSDC-d80042","HEGLD-d61095","HUSDT-6f0914","HWBTC-49ca31","HWETH-b3d17e","HBUSD-ac1fca","HHTM-e03ba5","HMEX-df6df7","HUTK-4fa4b2","HWTAO-2e9136"])
print(f"  Hatom Lending ${hl:,.0f} (prev ${prev['defi_tvl']['Hatom Lending']:,.0f}) EGLD {hl/price:,.0f} vs {prev['defi_tvl']['Hatom Lending']/pp:,.0f} = {100*((hl/price)-(prev['defi_tvl']['Hatom Lending']/pp))/(prev['defi_tvl']['Hatom Lending']/pp):+.2f}%")
print(f"  price move {100*(price-pp)/pp:+.2f}% -> mechanical inverse ratio {abs(100*((hl/price)-(prev['defi_tvl']['Hatom Lending']/pp))/(prev['defi_tvl']['Hatom Lending']/pp))/abs(100*(price-pp)/pp) if price!=pp else 0:.2f} (EVALUABLE only if |dPrice|>=5%)")
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
for a,l,p,c,d in ch[:16]:
    print(f"  {d:+11,.0f}  {l[:42]:42s} {a[:14]} ({p:,.0f} -> {c:,.0f})")

print("\n=== page-cap terminations ===")
print(json.dumps(D.get("_pagecap_terminations",[]),indent=1))
print("\n=== newly issued ===", D.get("newly_issued"))
print("=== status ===")
print(json.dumps(json.load(open("/tmp/run22w/status.json"))["failed"]))
