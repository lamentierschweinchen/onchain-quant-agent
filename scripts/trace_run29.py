#!/usr/bin/env python3
"""Run #29 targeted traces (after collector/followup/rails). Writes D["run29_traces"].
(1) Largest EGLD deposits into the Binance.com hot wallet in the window: who sent, and where did the sender's EGLD come from (provider withdraw? DEX?)
(2) The 11,000 EGLD Binance withdrawal: recipient and onward hop.
(3) The OTC desk's first post-halt outbound: timestamps, routers, terminals.
(4) Exit-route scan (run #28 rec #3): every provider withdraw call > 1,000 EGLD in the follow-up decode -> where did the sender's EGLD go next.
"""
import json,time,urllib.request,urllib.parse
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent";SNAP=f"{REPO}/data/collected/2026-10-09.json"
D=json.load(open(SNAP));API="https://api.multiversx.com";WIN=D["_period"]["window_start_ts"]
kn=json.load(open(f"{REPO}/data/known-addresses.json"));LM={}
for s,e in kn.items():
    if isinstance(e,dict):
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"): LM[a]=(m.get("name"),m.get("category"))
def get(p,**q):
    url=API+p+("?"+urllib.parse.urlencode(q) if q else "");d=1.5
    for a in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"intel-agent/29-trace"}),timeout=40) as r: return json.loads(r.read().decode())
        except Exception as e:
            if a==6: return {"__error__":str(e)}
            time.sleep(d);d=min(d*2,30)
def txs(a,after=0,n=100,**kw):
    r=get(f"/accounts/{a}/transactions",size=n,after=after,order="desc",status="success",**kw);time.sleep(0.45);return r if isinstance(r,list) else []
def eg(t): return int(t.get("value","0"))/1e18
BIN="erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets"
T={}
# (1) deposits
dep=[t for t in txs(BIN,WIN,100,receiver=BIN) if eg(t)>=500]
dep+= [t for t in txs(BIN,WIN+0,100,receiver=BIN,**{"from":100}) if eg(t)>=500] if len(dep)>=1 else []
by={}
for t in dep:
    by.setdefault(t["sender"],[]).append({"egld":eg(t),"ts":t["timestamp"],"hash":t["txHash"]})
rows=[]
for s,l in sorted(by.items(),key=lambda kv:-sum(x["egld"] for x in kv[1]))[:8]:
    info=get(f"/accounts/{s}");time.sleep(0.4)
    inb=txs(s,WIN-86400*14,40,receiver=s)
    src={}
    for t in inb:
        if eg(t)>=100: src.setdefault(t["sender"],[]).append({"egld":eg(t),"fn":t.get("function"),"ts":t["timestamp"]})
    rows.append({"sender":s,"label":LM.get(s),"total_egld":sum(x["egld"] for x in l),"n":len(l),"deposits":l[:6],
                 "balance_egld":int(info.get("balance","0"))/1e18 if isinstance(info,dict) else None,
                 "inbound_sources_14d":[{"from":k,"label":LM.get(k),"egld":sum(x["egld"] for x in v),"fns":sorted({x["fn"] or "transfer" for x in v})} for k,v in sorted(src.items(),key=lambda kv:-sum(x["egld"] for x in kv[1]))[:5]]})
T["binance_depositors"]=rows
# (2) the 11,000 withdrawal
big=[t for t in txs(BIN,WIN,100,sender=BIN) if eg(t)>=5000]
w=[]
for t in big:
    r=t["receiver"];o=txs(r,t["timestamp"]-60,20,sender=r)
    w.append({"receiver":r,"egld":eg(t),"ts":t["timestamp"],"label":LM.get(r),"onward":[{"to":x["receiver"],"label":LM.get(x["receiver"]),"egld":eg(x),"fn":x.get("function"),"ts":x["timestamp"]} for x in o if eg(x)>0][:5]})
T["binance_big_withdrawals"]=w
# (3) desk outbound
desk=["erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5","erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"]
dd={}
for a in desk:
    dd[a]={"out":[{"to":t["receiver"],"label":LM.get(t["receiver"]),"egld":eg(t),"ts":t["timestamp"]} for t in txs(a,WIN,100,sender=a) if eg(t)>0],
           "in":[{"from":t["sender"],"label":LM.get(t["sender"]),"egld":eg(t),"ts":t["timestamp"]} for t in txs(a,WIN,100,receiver=a) if eg(t)>0.01]}
T["desks"]=dd
# (4) exit-route scan over big withdraws
WDL=(D.get("withdraw_decoded") or {}).get("largest") or []
ex=[]
for w_ in WDL[:6]:
    s=w_["sender"];o=txs(s,w_["timestamp"]-30,30,sender=s)
    ex.append({"sender":s,"label":LM.get(s),"provider":w_.get("identity"),"withdrawn_egld":w_["egld_returned"],"ts":w_["timestamp"],
               "next":[{"to":x["receiver"],"label":LM.get(x["receiver"]),"egld":eg(x),"fn":x.get("function"),"ts":x["timestamp"]} for x in reversed(o) if eg(x)>0 or x.get("function")][:6]})
T["exit_routes"]=ex
D2=json.load(open(SNAP));D2["run29_traces"]=T
json.dump(D2,open(SNAP,"w"))
print(json.dumps(T,indent=1,default=str)[:9000])
