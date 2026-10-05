#!/usr/bin/env python3
"""Run #28 targeted traces (run after collector/followup/rails):
(1) the largest post-restart unDelegator erd155j9c36h: where did its unbonded EGLD go?
(2) the five OTC Desk->Gate.io routers that deposited at Gate.io's reopen: where was the EGLD from, and since when?
(3) the week's largest unlabelled balance movers.
Writes D["run28_traces"]."""
import json,time,urllib.request,urllib.parse
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent";SNAP=f"{REPO}/data/collected/2026-10-05.json"
D=json.load(open(SNAP));API="https://api.multiversx.com";WIN=D["_period"]["window_start_ts"]
def get(p,**q):
    url=API+p+("?"+urllib.parse.urlencode(q) if q else "");d=1.5
    for a in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"intel-agent/28-trace"}),timeout=40) as r: return json.loads(r.read().decode())
        except Exception as e:
            if a==6: return {"__error__":str(e)}
            time.sleep(d);d=min(d*2,30)
    
def txs(a,side,after,n=100):
    r=get(f"/accounts/{a}/transactions",size=n,after=after,order="desc",**{side:a});time.sleep(0.4);return r if isinstance(r,list) else []
def slim(t): return {"ts":t["timestamp"],"from":t["sender"],"to":t["receiver"],"egld":int(t.get("value","0"))/1e18,"fn":t.get("function"),"status":t.get("status"),"action":(t.get("action") or {}).get("description")}
T={}
U="erd155j9c36hp5dkqp7u5gwjek00g2axermvqdzk3j7mpk9k8yunpy4s9fpq8c"
T["undelegator"]={"info":get(f"/accounts/{U}"),"out":[slim(t) for t in txs(U,"sender",WIN-86400*10)],"in":[slim(t) for t in txs(U,"receiver",WIN-86400*10)],
  "tokens":get(f"/accounts/{U}/tokens",size=20),"delegation":get(f"/accounts/{U}/delegation")}
routers=[t["cp"] for t in D["exchange_rails"]["erd1p4vy5n9mlkdys7xczegj398xtyvw2nawz00nnfh4yr7fpjh297cqtsu7lw"]["in"]["top"]]
gate_in=[]
T["gate_routers"]={}
for r in routers:
    ins=txs(r,"receiver",1786000000,50); time.sleep(0.2)
    T["gate_routers"][r]={"info":get(f"/accounts/{r}"),"in":[slim(t) for t in ins if int(t.get("value","0"))>0][:10],
                          "out":[slim(t) for t in txs(r,"sender",1786000000,20) if int(t.get("value","0"))>0][:10]}
for a in ["erd1ygqnssmnq2p37l9wyv00jwq6echwa9dhssr50399gjj6c7qwa8vqap0prn","erd1hhvfrwvqj5jhxqwlac9vftwgnlkv0s9y7xy7xp98vehlq74qee6srkqgdh",
          "erd1hl5y4ahk2a52rf4znn69a62w8skjputp7h3wxfsyyq3kykj0j2uqt7vqmy","erd1v3undjd5mrvqq3tg3re8u9z55tc3ysxaw7ladqrvq9m69r4tv0yqrkfryq"]:
    T.setdefault("movers",{})[a]={"out":[slim(t) for t in txs(a,"sender",WIN,50) if int(t.get("value","0"))>0][:12],
                                  "in":[slim(t) for t in txs(a,"receiver",WIN,50) if int(t.get("value","0"))>0][:12]}
# full-window Gate.io inbound EGLD census (all pages)
D["run28_traces"]=T;json.dump(D,open(SNAP,"w"));print("ok")
