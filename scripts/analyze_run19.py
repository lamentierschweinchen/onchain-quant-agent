#!/usr/bin/env python3
"""Exploratory analysis for run #19 (2026-08-03) - prints the numbers the assembler narrates."""
import json, math
from datetime import datetime, timezone

REPO = "/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D = json.load(open(f"{REPO}/data/collected/2026-08-03.json"))
prev = json.load(open(f"{REPO}/data/previous.json"))
prevcol = json.load(open(f"{REPO}/data/collected/2026-07-27.json"))
kn = json.load(open(f"{REPO}/data/known-addresses.json"))
learn = json.load(open(f"{REPO}/data/learnings.json"))

label_map, cat_map = {}, {}
for section, entries in kn.items():
    if not isinstance(entries, dict) or section == "_metadata": continue
    for addr, meta in entries.items():
        if isinstance(meta, dict) and addr.startswith("erd1"):
            label_map[addr] = meta.get("name","Unknown"); cat_map[addr]=meta.get("category","unknown")
def lab(a): return label_map.get(a,"Unknown")
def cat(a): return cat_map.get(a,"unknown")

econ=D["economics"]; pecon=prev["economics"]
price=econ["price"]; pp=pecon["egld_price_usd"]; price_chg=100*(price-pp)/pp
acc=D["accounts"]
def bal_of(a):
    x=acc.get(a)
    if x and isinstance(x.get("info"),dict) and "balance" in x["info"]:
        try: return int(x["info"]["balance"])/1e18
        except: return None
    return None

UPBIT_DESK="erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
DIST_DESK="erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
DESK_SET={UPBIT_DESK,DIST_DESK}
def desk_throughput(block):
    gross=inter=0.0; dest={}
    for a,v in block.items():
        for t in v.get("txs",[]):
            try: val=int(t.get("value","0"))/1e18
            except: val=0
            if val<=0: continue
            gross+=val
            r=t.get("receiver")
            if r in DESK_SET: inter+=val
            else: dest[r]=dest.get(r,0)+val
    return gross,inter,dest
g,i,dest = desk_throughput(D["desk_outbound_paged"])
print("=== OTC THROUGHPUT 7d ===")
print("gross",round(g),"interdesk",round(i),"NET",round(g-i))
for a,v in sorted(dest.items(),key=lambda x:-x[1])[:8]:
    inf=None
    print(f"   dest {a[:14]} {lab(a):35s} {v:,.0f}")
gin,iin,src = desk_throughput(D["desk_inbound_paged"])
print("inbound gross",round(gin),"interdesk",round(iin))
for a,v in sorted(src.items(),key=lambda x:-x[1])[:6]:
    print(f"   src? {a[:14]} {lab(a):35s} {v:,.0f}")
# inbound senders
insrc={}
for aa,vv in D["desk_inbound_paged"].items():
    for t in vv["txs"]:
        try: val=int(t.get("value","0"))/1e18
        except: val=0
        if val<=0: continue
        s=t.get("sender")
        if s in DESK_SET: continue
        insrc[s]=insrc.get(s,0)+val
print("  TRUE external inbound to desks:", round(sum(insrc.values())))
for a,v in sorted(insrc.items(),key=lambda x:-x[1])[:6]:
    print(f"   IN  {a[:14]} {lab(a):35s} {v:,.0f}")

bf = D.get("otc_backfill",{})
for wname,wd in bf.items():
    gg,ii,dd = desk_throughput(wd)
    print(f"BACKFILL {wname}: gross {gg:,.0f} interdesk {ii:,.0f} NET {gg-ii:,.0f}")

desk_cur=(bal_of(UPBIT_DESK) or 0)+(bal_of(DIST_DESK) or 0)
print("desk balances: UPbit",round(bal_of(UPBIT_DESK) or 0),"Dist",round(bal_of(DIST_DESK) or 0),"combined",round(desk_cur),"prev 61495")

print("\n=== CUSTODY FUNDER TRACE (erd1r3w62vq) ===")
for k in ["custody_funder_inbound_30d","custody_funder_outbound_30d"]:
    print(k)
    for t in D.get(k,[]):
        v=int(t.get("value","0"))/1e18
        print(f"   {datetime.fromtimestamp(t['timestamp'],tz=timezone.utc).date()} {v:,.0f} from {lab(t['sender'])}({t['sender'][:12]}) -> {lab(t['receiver'])}({t['receiver'][:12]})")
print("funder balance now:", bal_of("erd1r3w62vqmsux5e38p6vnueatmfcs8nr5lmg3s97x6rafqpgxfae0sxv9z0v"))
print("custody bal now:", bal_of("erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"), "prev 3357100.6")
print("custody 7d out:")
for t in D.get("binance_custody_out_7d",[]):
    v=int(t.get("value","0"))/1e18
    if v>0: print(f"   OUT {v:,.0f} -> {lab(t['receiver'])} {t['receiver'][:14]}")
print("custody 7d in:")
for t in D.get("binance_custody_in_7d",[]):
    v=int(t.get("value","0"))/1e18
    if v>0: print(f"   IN  {v:,.0f} <- {lab(t['sender'])} {t['sender'][:14]}")

print("\n=== DEMAND: absorber + routing pipes ===")
MW="erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"
print("mega whale balance", bal_of(MW), "prev 1093311.6")
print(" inbound txs:", len(D.get("mega_whale_inbound",[])), "outbound:", len(D.get("mega_whale_outbound",[])))
for t in D.get("mega_whale_inbound",[])[:8]:
    v=int(t.get("value","0"))/1e18
    print(f"   IN {v:,.0f} <- {lab(t['sender'])} {t['sender'][:14]}")
for t in D.get("mega_whale_outbound",[])[:8]:
    v=int(t.get("value","0"))/1e18
    print(f"   OUT {v:,.0f} -> {lab(t['receiver'])} {t['receiver'][:14]}")
for nm,ad in [("cb_routing_a","erd1eae23a530qymlpvfrudzsge5wgl003wl92saax74cew7j549eqqq3jklut"),
              ("cb_routing_b","erd1lgdltequh7627rtlacmcp6p5vec7zmu2rxhu7pjwvcja8f4a9gqq9vcc70")]:
    print(nm, ad[:16], "bal", bal_of(ad), "in", len(D.get(nm+"_in_7d",[])), "out", len(D.get(nm+"_out_7d",[])))
    for t in D.get(nm+"_in_7d",[])[:4]:
        v=int(t.get("value","0"))/1e18
        if v>0: print(f"    IN {v:,.0f} <- {lab(t['sender'])}")
    for t in D.get(nm+"_out_7d",[])[:4]:
        v=int(t.get("value","0"))/1e18
        if v>0: print(f"    OUT {v:,.0f} -> {lab(t['receiver'])} {t['receiver'][:14]}")

print("\n=== WITHDRAWAL BREADTH (>1000 EGLD out of exchanges) ===")
recips={}; tot_w=0; per_ex={}
for a,v in D.get("exchange_outbound_paged",{}).items():
    for t in v["txs"]:
        try: val=int(t.get("value","0"))/1e18
        except: val=0
        if val<1000: continue
        r=t.get("receiver")
        if cat(r)=="exchange": continue
        recips.setdefault(r,0); recips[r]+=val; tot_w+=val
        per_ex[v["label"]]=per_ex.get(v["label"],0)+val
print("distinct recipients >1000 EGLD:", len(recips), "total", round(tot_w))
for e,v in sorted(per_ex.items(),key=lambda x:-x[1]): print(f"   from {e:20s} {v:,.0f}")
for a,v in sorted(recips.items(),key=lambda x:-x[1])[:12]:
    print(f"   -> {a[:16]} {lab(a):30s} {v:,.0f}")
# also count all outbound >1000 including exchange-to-exchange for context
allbig=sum(1 for a,v in D.get("exchange_outbound_paged",{}).items() for t in v["txs"] if int(t.get("value","0"))/1e18>=1000)
print("total >1000 EGLD outbound txs:", allbig)

print("\n=== DEPTH RATIO (mex pairs) ===")
pairs=D["mex_pairs"]
prevpairs={}
for p in prevcol.get("mex_pairs",[]):
    prevpairs[p.get("baseSymbol","")+"/"+p.get("quoteSymbol","")]=p
tot=sum(p.get("volume24h") or 0 for p in pairs)
tottvl=sum(p.get("totalValue") or 0 for p in pairs)
print("total vol", round(tot), "total tvl", round(tottvl), "turnover %", round(100*tot/tottvl,3))
prevtot=sum(p.get("volume24h") or 0 for p in prevcol.get("mex_pairs",[]))
prevtvl=sum(p.get("totalValue") or 0 for p in prevcol.get("mex_pairs",[]))
print("prev vol", round(prevtot), "prev tvl", round(prevtvl), "prev turnover %", round(100*prevtot/prevtvl,3))
for p in sorted(pairs,key=lambda x:-(x.get("volume24h") or 0))[:6]:
    nm=p.get("baseSymbol","")+"/"+p.get("quoteSymbol","")
    pv=prevpairs.get(nm,{})
    print(f"   {nm:14s} vol {p.get('volume24h') or 0:12,.0f} tvl {p.get('totalValue') or 0:12,.0f} turn {100*(p.get('volume24h') or 0)/max(p.get('totalValue') or 1,1):6.3f}%  prev turn {100*(pv.get('volume24h') or 0)/max(pv.get('totalValue') or 1,1):6.3f}%")

print("\n=== EXCHANGE BALANCES ===")
cur_top={x["address"]:int(x["balance"])/1e18 for x in D["top_accounts"]}
prev_top={x["address"]:x["balance_egld"] for x in prev["top_accounts"]}
def entity_of(a):
    l=lab(a)
    if "Binance" in l: return "Binance"
    if "Coinbase" in l: return "Coinbase"
    if "Crypto.com" in l: return "Crypto.com"
    for e in ["UPbit","Bybit","MEXC","Bitget","Gate.io","KuCoin","Bitfinex","Tokero"]:
        if e in l: return e
    return None
exch=[a for a,c in cat_map.items() if c=="exchange"]
BAD={"erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp29trp6qsl2gdvvz2eqra76xc",
     "erd1ty4pvmjtl3mnsjvnsxqkm3xqm4dm7ppgz9sh4nk4tqvlmw0jyggqzn4mdc"}
missing_prior=[]
for a in exch:
    if a in BAD: continue
    e=entity_of(a)
    if not e: continue
    cur=bal_of(a); cur = cur if cur is not None else cur_top.get(a)
    pb=prev_top.get(a)
    if cur is None: continue
    if pb is None:
        missing_prior.append((e,lab(a),a,cur)); continue
    if abs(cur-pb)>100:
        print(f"  {e:12s} {lab(a):28s} {pb:14,.0f} -> {cur:14,.0f}  {cur-pb:+12,.0f} ({100*(cur-pb)/pb if pb else 0:+.1f}%)")
print("NO PRIOR BALANCE (phantom risk):")
for e,l,a,c in missing_prior: print(f"   {e} {l} {a[:16]} cur={c:,.0f}")

print("\n=== STAKING ===")
provs=[p for p in D["providers"] if p.get("locked") and float(p["locked"])>0]
for p in provs: p["_lk"]=float(p["locked"])/1e18
provs.sort(key=lambda p:-p["_lk"])
total_locked=sum(p["_lk"] for p in provs)
prevp={p["name"]:p["locked_egld"] for p in prev["staking_providers"]}
prevu={p["name"]:p["num_delegators"] for p in prev["staking_providers"]}
cur_deleg=sum(p.get("numUsers",0) for p in provs); prev_deleg=sum(prevu.values())
print("providers active",len(provs),"total_locked",round(total_locked),"prev",round(prev["staking_concentration"]["total_locked_egld"]),"delta",round(total_locked-prev["staking_concentration"]["total_locked_egld"]))
print("delegators",cur_deleg,"prev",prev_deleg,"delta",cur_deleg-prev_deleg)
moves=[]
for p in provs:
    nm=p.get("identity") or p["provider"]
    if nm in prevp:
        moves.append((nm,p["_lk"]-prevp[nm],p.get("numUsers",0)-prevu.get(nm,0)))
moves.sort(key=lambda x:-abs(x[1]))
for nm,d,du in moves[:14]: print(f"   {nm:28s} {d:+12,.0f} users {du:+5d}")
print("pi-staking:", [m for m in moves if m[0]=='pi-staking'])
pi=[p for p in provs if (p.get('identity') or '')=='pi-staking']
if pi: print("   pi detail: locked",round(pi[0]['_lk']),"users",pi[0].get('numUsers'),"apr",pi[0].get('apr'),"fee",pi[0].get('serviceFee'),"nodes",pi[0].get('numNodes'))
print("pi inbound txs 7d:", len(D.get("pi_staking_inbound_7d",[])))
funcs={}
vals=0
senders={}
for t in D.get("pi_staking_inbound_7d",[]):
    f=t.get("function","?"); funcs[f]=funcs.get(f,0)+1
    v=int(t.get("value","0"))/1e18; vals+=v
    if v>0: senders[t["sender"]]=senders.get(t["sender"],0)+v
print("   functions:",funcs,"value in:",round(vals))
for s,v in sorted(senders.items(),key=lambda x:-x[1])[:6]: print(f"     {s[:16]} {lab(s):24s} {v:,.0f}")

print("\n=== DEFI ===")
tt=D["tvl_tokens"]
def mc(t):
    x=tt.get(t); return (x.get("marketCap") or 0) if isinstance(x,dict) else 0
def sup(t,col=tt):
    x=col.get(t)
    try: return float(x.get("supply")) if x and x.get("supply") else None
    except: return None
for t in ["SEGLD-3ad2d0","XEGLD-e413ed","SWTAO-356a25","USH-111e09"]:
    c=sup(t); p=sup(t,prevcol.get("tvl_tokens",{}))
    print(f"  {t}: supply {c:,.0f} prev {p:,.0f} WoW {100*(c-p)/p:+.2f}%  mcap {mc(t):,.0f}")
hl=sum(mc(x) for x in ["HUSDC-d80042","HEGLD-d61095","HUSDT-6f0914","HWBTC-49ca31","HWETH-b3d17e","HBUSD-ac1fca","HHTM-e03ba5","HMEX-df6df7","HUTK-4fa4b2","HWTAO-2e9136"])
print("Hatom Lending USD", round(hl), "prev", round(prev["defi_tvl"]["Hatom Lending"]))
hl_egld=hl/price; prev_hl_egld=prev["defi_tvl"]["Hatom Lending"]/pp
print("Hatom Lending EGLD", round(hl_egld), "prev", round(prev_hl_egld), "chg%", round(100*(hl_egld-prev_hl_egld)/prev_hl_egld,2))
print("price chg%", round(price_chg,2), "inverse ratio", round(abs(100*(hl_egld-prev_hl_egld)/prev_hl_egld)/abs(price_chg),3))
for sid in ["USDC-c76f1f","USDT-f8c08c"]:
    c=D.get("stable_"+sid,{}); p=prevcol.get("stable_"+sid,{})
    try:
        cs=float(c.get("supply")); ps=float(p.get("supply"))
        print(f"  {sid}: {cs:,.0f} prev {ps:,.0f} {100*(cs-ps)/ps:+.2f}%")
    except Exception as e: print(" stable err",sid,e)
wt=D.get("wegld_token",{})
pwt=prevcol.get("wegld_token") or {}
print("WEGLD supply", wt.get("supply"), "prev(from tokens_holders)", [t.get('supply') for t in prevcol['tokens_holders'] if t['identifier']=='WEGLD-bd4d79'])
wegld_egld=sum(int(b["balance"])/1e18 for b in D["wegld"].values() if isinstance(b,dict) and "balance" in b)
print("xExchange WEGLD contract EGLD", round(wegld_egld), "prev EGLD", round(prev["defi_tvl"]["xExchange (USD)"]/pp))
def tcount(name):
    c=D["proto"][name]["transfers_24h"]; return c.get("count") if isinstance(c,dict) else c
for n in D["proto"]: print("  transfers24h",n,tcount(n))

print("\n=== WHALE TIERS / wallet changes ===")
N_prev=len(prev["top_accounts"])
cur_trim=dict(sorted(cur_top.items(),key=lambda kv:-kv[1])[:N_prev])
def tiers(top):
    items=[(a,b) for a,b in top.items() if cat(a)!="system"]
    return ([x for x in items if x[1]>1e6],[x for x in items if 1e5<=x[1]<=1e6],[x for x in items if 1e4<=x[1]<1e5])
cm,cl,cmid=tiers(cur_trim); pm,pl,pmid=tiers(prev_top)
for nm,c,p in [("mega",cm,pm),("large",cl,pl),("mid",cmid,pmid)]:
    print(f"  {nm}: {len(c)} wallets {sum(b for _,b in c):,.0f} vs prev {len(p)} {sum(b for _,b in p):,.0f} delta {sum(b for _,b in c)-sum(b for _,b in p):+,.0f}")
chg=[]
for a,b in cur_top.items():
    if a in prev_top and cat(a)!="system":
        d=b-prev_top[a]
        if abs(d)>2000: chg.append((a,lab(a),prev_top[a],b,d))
chg.sort(key=lambda x:-abs(x[4]))
for a,l,pb,b,d in chg[:18]: print(f"   {l:34s} {a[:14]} {pb:12,.0f} -> {b:12,.0f} {d:+11,.0f}")

print("\n=== NEW top-100 entrants not in prev ===")
for a,b in sorted(cur_top.items(),key=lambda kv:-kv[1])[:60]:
    if a not in prev_top and cat(a)!="system":
        print(f"   NEW {lab(a):30s} {a[:16]} {b:,.0f}")
