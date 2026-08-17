#!/usr/bin/env python3
"""Run #21 targeted follow-ups:
 (a) verify the serviceFee=1.0 / apr=0 readings on egldstakingprovider + procryptostaking
 (b) trace the p2p_org_ -149,582 delegation move (largest single provider move in tracking)
 (c) test whether the protocol Staking SC is queryable at all (direct-node unwind trace)
 (d) trace XEGLD redemption: unDelegate/withdraw callers on the XOXNO LSD contract -> destinations
"""
import json, time, urllib.request, urllib.parse
from datetime import datetime, timezone

API="https://api.multiversx.com"
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D=json.load(open(f"{REPO}/data/collected/2026-08-17.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
lm,cmap={},{}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"):
                lm[a]=m.get("name","Unknown"); cmap[a]=m.get("category","unknown")
def lab(a): return lm.get(a,"Unknown")

def get(path, params=None, retries=2):
    url=API+path
    if params: url+="?"+urllib.parse.urlencode(params)
    for i in range(retries+1):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"intel-agent/21f"})
            with urllib.request.urlopen(req,timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as ex:
            if i==retries: return {"__error__":str(ex),"__url__":url}
            time.sleep(1.0)

def ts(y,m,d): return int(datetime(y,m,d,tzinfo=timezone.utc).timestamp())
W_START=ts(2026,8,10); W_END=ts(2026,8,17); D21=ts(2026,7,27); D30=ts(2026,7,18)

OUT={}

print("=== (a) VERIFY serviceFee=1 / apr=0 ===")
targets={"egldstakingprovider":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqpt0llllsy0c2kv",
         "procryptostaking":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqxlllllsmehg53",
         "p2p_org_":"erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqm8llllsyhrgzd"}
fresh=get("/providers",{"identity":"egldstakingprovider"})
time.sleep(0.3)
print("  /providers?identity=egldstakingprovider ->",json.dumps(fresh)[:500])
OUT["providers_identity_query"]=fresh
for nm,addr in targets.items():
    p=get(f"/providers/{addr}")
    time.sleep(0.3)
    if isinstance(p,dict):
        print(f"  /providers/{{addr}} {nm}: apr={p.get('apr')} serviceFee={p.get('serviceFee')} "
              f"locked={int(p.get('locked','0'))/1e18:,.0f} numNodes={p.get('numNodes')} numUsers={p.get('numUsers')} "
              f"featured={p.get('featured')} identity={p.get('identity')}")
    OUT[f"provider_{nm}"]=p

print("\n=== (b) p2p_org_ delegation contract flows (21d) ===")
p2p=targets["p2p_org_"]
for direction in ("receiver","sender"):
    txs=get(f"/accounts/{p2p}/transactions",{"size":50,"after":D21,"order":"desc","status":"success",direction:p2p})
    time.sleep(0.3)
    OUT[f"p2p_{direction}_21d"]=txs
    if isinstance(txs,list):
        fn={}
        for t in txs: fn[t.get("function") or "(transfer)"]=fn.get(t.get("function") or "(transfer)",0)+1
        print(f"  {direction}: {len(txs)} txs, functions {fn}")
        agg={}
        key="sender" if direction=="receiver" else "receiver"
        for t in txs:
            v=int(t.get("value","0"))/1e18
            agg[t[key]]=agg.get(t[key],0)+v
        for a,v in sorted(agg.items(),key=lambda x:-x[1])[:8]:
            print(f"     {v:12,.1f} {'<-' if direction=='receiver' else '->'} {lab(a)[:34]:34s} {a[:18]} ")
# who called unDelegate on p2p_org_
und=get(f"/accounts/{p2p}/transactions",{"size":50,"after":D30,"order":"desc","function":"unDelegate"})
time.sleep(0.3)
OUT["p2p_undelegate_30d"]=und
if isinstance(und,list):
    print(f"  unDelegate calls 30d: {len(und)}")
    for t in und[:10]:
        print(f"     {t.get('sender')[:20]} {lab(t.get('sender'))[:28]:28s} {datetime.fromtimestamp(t['timestamp'],tz=timezone.utc).date()} status={t.get('status')}")

print("\n=== (c) Staking SC queryability ===")
SSC="erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqplllst77y4l"
variants=[("txs no-status-no-dir",f"/accounts/{SSC}/transactions",{"size":10,"after":W_START,"order":"desc"}),
          ("txs receiver only",f"/accounts/{SSC}/transactions",{"size":10,"receiver":SSC,"order":"desc"}),
          ("txs any",f"/accounts/{SSC}/transactions",{"size":10,"order":"desc"}),
          ("transfers any",f"/accounts/{SSC}/transfers",{"size":10,"order":"desc"}),
          ("global txs receiver",f"/transactions",{"size":10,"receiver":SSC,"order":"desc"})]
for nm,path,params in variants:
    r=get(path,params)
    time.sleep(0.35)
    n=len(r) if isinstance(r,list) else r
    print(f"  {nm}: {n if not isinstance(n,dict) else str(n)[:120]}")
    if isinstance(r,list) and r:
        for t in r[:4]:
            print(f"      {t.get('function')} val={int(t.get('value','0'))/1e18:,.1f} from {lab(t.get('sender'))[:22]} {t.get('sender','')[:14]} ts={t.get('timestamp')}")
    OUT[f"ssc_{nm.replace(' ','_')}"]=r if isinstance(r,list) else r

print("\n=== (d) XEGLD redemption trace ===")
XL="erd1qqqqqqqqqqqqqpgq6uzdzy54wnesfnlaycxwymrn9texlnmyah0ssrfvk6"
callers={}
for fn in ("unDelegate","unDelegatePending","withdraw","withdrawPending"):
    r=get(f"/accounts/{XL}/transactions",{"size":50,"after":W_START,"order":"desc","status":"success","function":fn})
    time.sleep(0.3)
    OUT[f"xegld_{fn}"]=r
    if isinstance(r,list):
        print(f"  {fn}: {len(r)} calls")
        for t in r:
            callers.setdefault(t["sender"],[]).append(fn)
print(f"  distinct callers: {len(callers)}")
# for the callers, look at their next outbound EGLD movements
dest_class={}
detail=[]
for i,(addr,fns) in enumerate(list(callers.items())[:22]):
    info=get(f"/accounts/{addr}")
    time.sleep(0.2)
    outb=get(f"/accounts/{addr}/transactions",{"size":15,"after":W_START,"order":"desc","status":"success","sender":addr})
    time.sleep(0.25)
    bal=int(info.get("balance","0"))/1e18 if isinstance(info,dict) and "balance" in info else None
    rows=[]
    for t in (outb if isinstance(outb,list) else []):
        v=int(t.get("value","0"))/1e18
        r_=t.get("receiver")
        c=cmap.get(r_,"unknown")
        fnm=t.get("function")
        if v>0.5:
            rows.append((v,lab(r_),c,r_,fnm))
            k= "exchange" if c=="exchange" else ("delegation" if (r_ or "").startswith("erd1qqqqqqqqqqqqqqqp") else ("defi" if c=="defi" else "other"))
            dest_class[k]=dest_class.get(k,0)+v
    detail.append({"address":addr,"functions":fns,"balance_egld":bal,"outbound":rows})
    if rows:
        print(f"  {addr[:16]} bal {bal:,.1f} fns={set(fns)}")
        for v,l,c,r_,fnm in rows[:4]:
            print(f"      -> {v:10,.1f} {l[:26]:26s} cat={c} fn={fnm} {r_[:16]}")
print("  destination classes (EGLD):",{k:round(v,1) for k,v in sorted(dest_class.items(),key=lambda x:-x[1])})
OUT["xegld_caller_detail"]=detail
OUT["xegld_dest_class"]=dest_class

json.dump(OUT,open(f"{REPO}/data/collected/followup_2026-08-17.json","w"))
print("\nSaved data/collected/followup_2026-08-17.json")
