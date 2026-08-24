#!/usr/bin/env python3
"""Run #22 follow-up collection.

(1) UNBONDING POOL (rec #9/#10): the main collector joined provider movers on the
    wrong key (previous.json stores `provider` = identity, not address), so it found
    79 phantom movers and zero wallets. Redo with the correct key and query
    /accounts/{addr}/delegation for the wallets behind every real move >= 5K EGLD.
(2) p2p_org_ WIND-DOWN: who unDelegated the remaining 69,583?
(3) MEX relative strength: prior-week MEX supply from the run #21 snapshot.
"""
import json, time, urllib.request, urllib.parse, os
from datetime import datetime, timezone

API="https://api.multiversx.com"
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
D=json.load(open(f"{REPO}/data/collected/2026-08-24.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
lm={}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"): lm[a]=m.get("name","Unknown")

def ts(y,m,d): return int(datetime(y,m,d,tzinfo=timezone.utc).timestamp())
AFTER=ts(2026,8,17); BEFORE=ts(2026,8,24)

def get(path,params=None,retries=2):
    url=API+path
    if params: url+="?"+urllib.parse.urlencode(params)
    for a in range(retries+1):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"intel-agent/22"})
            with urllib.request.urlopen(req,timeout=30) as r: return json.loads(r.read().decode())
        except Exception as e:
            if a==retries: return {"__error__":str(e),"__url__":url}
            time.sleep(1.0)

def paged(addr,after,direction="receiver",max_pages=12,before=None):
    out,frm=[],0
    for _ in range(max_pages):
        p={"size":50,"from":frm,"after":after,"order":"desc","status":"success",direction:addr}
        if before: p["before"]=before
        b=get(f"/accounts/{addr}/transactions",p); time.sleep(0.25)
        if not isinstance(b,list) or not b: break
        out.extend(b)
        if len(b)<50: break
        frm+=50
    return out

# ---- (1) correct-key provider movers --------------------------------------
pp={p["provider"]:p for p in prev["staking_providers"]}
cur=[p for p in D["providers"] if float(p.get("locked",0) or 0)>0]
key=lambda p: p.get("identity") or p["provider"]
movers=[]
for pr in cur:
    k=key(pr); lk=float(pr.get("locked",0) or 0)/1e18
    if k in pp:
        d=lk-pp[k]["locked_egld"]
        if abs(d)>=5000:
            movers.append({"key":k,"address":pr["provider"],"delta_egld":d,"locked_egld":lk,
                           "users":pr.get("numUsers"),"apr":pr.get("apr"),"fee":pr.get("serviceFee")})
curk={key(p) for p in cur}
for k,p in pp.items():
    if k not in curk:
        addr=next((x["provider"] for x in D["providers"] if (x.get("identity") or x["provider"])==k), None)
        movers.append({"key":k,"address":addr,"delta_egld":-p["locked_egld"],"locked_egld":0.0,
                       "users":None,"apr":0,"fee":None,"left_active_set":True})
movers.sort(key=lambda m:-abs(m["delta_egld"]))
print(f"[movers] {len(movers)} providers moved >=5K EGLD (correct key)")
for m in movers: print(f"   {m['delta_egld']:+11,.0f}  {m['key'][:32]}")

OUT={"provider_movers":movers,"_window":"2026-08-17..2026-08-24"}

undel_senders={}
prov_fn={}
for m in movers:
    if not m.get("address"): continue
    txs=paged(m["address"],AFTER,direction="receiver",before=BEFORE)
    fn={}
    legs=[]
    for t in txs:
        f=t.get("function") or "(transfer)"
        fn[f]=fn.get(f,0)+1
        if f=="unDelegate":
            snd=t.get("sender")
            amt=None
            try:
                import base64
                dec=base64.b64decode(t.get("data") or "").decode("utf-8",errors="ignore")
                parts=dec.split("@")
                if len(parts)>1: amt=int(parts[1],16)/1e18
            except Exception: pass
            legs.append({"sender":snd,"amount_egld":amt,"timestamp":t.get("timestamp"),"txHash":t.get("txHash")})
            if snd: undel_senders.setdefault(snd,[]).append({"provider":m["key"],"amount_egld":amt,"timestamp":t.get("timestamp")})
    prov_fn[m["key"]]={"function_counts":fn,"undelegate_legs":legs,"tx_count":len(txs)}
    print(f"[{m['key'][:26]:28}] {len(txs)} inbound txs; unDelegate={len(legs)}")
OUT["provider_inbound"]=prov_fn

print(f"\n[unbonding-pool] {len(undel_senders)} distinct unDelegate callers")
pool=[]
for w,legs in list(undel_senders.items())[:30]:
    dg=get(f"/accounts/{w}/delegation"); time.sleep(0.3)
    inf=get(f"/accounts/{w}"); time.sleep(0.2)
    pend=[]
    if isinstance(dg,list):
        for row in dg:
            for u in (row.get("userUndelegatedList") or []):
                pend.append({"contract":row.get("contract"),
                             "amount_egld":int(u["amount"])/1e18,
                             "seconds_remaining":u.get("seconds"),
                             "days_remaining":round((u.get("seconds") or 0)/86400,2)})
    tot=sum(p["amount_egld"] for p in pend)
    pool.append({"wallet":w,"label":lm.get(w,"Unknown"),
                 "balance_egld":int(inf.get("balance","0"))/1e18 if isinstance(inf,dict) and "balance" in inf else None,
                 "nonce":inf.get("nonce") if isinstance(inf,dict) else None,
                 "this_week_undelegated":sum((l["amount_egld"] or 0) for l in legs),
                 "legs":legs,"pending_unbonding":pend,"total_pending_egld":tot})
    print(f"   {w[:16]} wk_undel={sum((l['amount_egld'] or 0) for l in legs):,.0f} pending={tot:,.0f} bal={pool[-1]['balance_egld']}")
pool.sort(key=lambda x:-x["total_pending_egld"])
OUT["unbonding_pool"]=pool
OUT["unbonding_pool_total_egld"]=sum(p["total_pending_egld"] for p in pool)

# also carry the run #21 wallet (still pending, already queried in main pass)
OUT["run21_unbond_wallet"]={"wallet":"erd1daqlaezxx22rzyxnqx5ddkykm5ajelt0hetjnstm7rxqg78xqusqazv9ms",
                            "delegation":D.get("unbond_wallet_delegation"),
                            "balance_egld":int((D.get("unbond_wallet_info") or {}).get("balance","0"))/1e18,
                            "outbound_7d":len(D.get("unbond_wallet_out_7d") or []),
                            "inbound_7d":len(D.get("unbond_wallet_in_7d") or [])}

# ---- (3) MEX supply prior week --------------------------------------------
try:
    p21=json.load(open(f"{REPO}/data/collected/2026-08-17.json"))
    OUT["mex_prev"]={"supply":(p21.get("mex_token") or {}).get("supply"),
                     "circulatingSupply":(p21.get("mex_economics") or {}).get("circulatingSupply"),
                     "totalSupply":(p21.get("mex_economics") or {}).get("totalSupply"),
                     "marketCap":(p21.get("mex_economics") or {}).get("marketCap")}
    OUT["mex_cur"]={"supply":(D.get("mex_token") or {}).get("supply"),
                    "circulatingSupply":(D.get("mex_economics") or {}).get("circulatingSupply"),
                    "totalSupply":(D.get("mex_economics") or {}).get("totalSupply"),
                    "marketCap":(D.get("mex_economics") or {}).get("marketCap")}
    # MEX/WEGLD pool depth in EGLD terms
    def mexpair(snap):
        for p in (snap.get("mex_pairs_wide") or snap.get("mex_pairs") or []):
            if p.get("baseSymbol")=="MEX" and p.get("quoteSymbol")=="WEGLD":
                return p
        return None
    OUT["mex_pair_prev"]=mexpair(p21); OUT["mex_pair_cur"]=mexpair(D)
    print("\n[MEX] prev supply",OUT["mex_prev"],"cur",OUT["mex_cur"])
except Exception as e:
    OUT["mex_prev_error"]=str(e)

json.dump(OUT,open(f"{REPO}/data/collected/followup_2026-08-24.json","w"),indent=1)
print("\nsaved data/collected/followup_2026-08-24.json")
print("unbonding pool total:",f"{OUT['unbonding_pool_total_egld']:,.0f}")
