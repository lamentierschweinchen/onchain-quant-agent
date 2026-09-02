#!/usr/bin/env python3
"""Ad-hoc: what is behind the EGLD move, and how are large holders positioned?

Window: since the run #23 snapshot (2026-08-31) — 48h — plus a tight 24h cut,
so the price move can be separated from the two-day drift.
"""
import json, time, urllib.request, urllib.parse, os
from datetime import datetime, timezone

API="https://api.multiversx.com"
OUT="/tmp/special_egld"; os.makedirs(OUT, exist_ok=True)
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
kn=json.load(open(f"{REPO}/data/known-addresses.json"))
prev=json.load(open(f"{REPO}/data/previous.json"))

NOW=int(datetime.now(timezone.utc).timestamp())
H24=NOW-86400
H48=int(datetime(2026,8,31,0,0,0,tzinfo=timezone.utc).timestamp())

ERR=[]
def get(path,params=None,retries=4):
    url=API+path+("?"+urllib.parse.urlencode(params) if params else "")
    delay=1.0
    for a in range(retries+1):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"intel/special"})
            with urllib.request.urlopen(req,timeout=30) as r: return json.loads(r.read().decode())
        except Exception as e:
            if "429" in str(e): time.sleep(delay); delay=min(delay*2,12); continue
            if a==retries: ERR.append({"url":url,"err":str(e)}); return {"__error__":str(e)}
            time.sleep(0.8)
    return {"__error__":"exhausted"}

def paged(addr,after,direction="sender",max_pages=30,tag=""):
    out,frm=[],0
    for _ in range(max_pages):
        p={"size":50,"from":frm,"after":after,"order":"desc","status":"success",direction:addr}
        b=get(f"/accounts/{addr}/transactions",p); time.sleep(0.25)
        if isinstance(b,dict): ERR.append({"addr":addr,"tag":tag,"err":"page failed"}); break
        if not b: break
        out.extend(b)
        if len(b)<50: break
        frm+=50
    return out

label={};cat={}
for s,e in kn.items():
    if isinstance(e,dict) and s!="_metadata":
        for a,m in e.items():
            if isinstance(m,dict) and a.startswith("erd1"):
                label[a]=m.get("name","Unknown"); cat[a]=m.get("category","unknown")

D={"_window":{"now":NOW,"h24":H24,"since_report":H48,
              "report_date":"2026-08-31","generated":datetime.now(timezone.utc).isoformat()}}

# --- macro -----------------------------------------------------------------
D["economics"]=get("/economics"); time.sleep(0.3)
D["stats"]=get("/stats"); time.sleep(0.3)
D["top_accounts"]=get("/accounts",{"size":100,"sort":"balance","order":"desc"}); time.sleep(0.3)
D["providers"]=get("/providers",{"size":200,"sort":"locked","order":"desc"}); time.sleep(0.3)
D["mex_economics"]=get("/mex/economics"); time.sleep(0.3)
D["mex_pairs"]=get("/mex/pairs",{"size":50}); time.sleep(0.3)
print("[macro] price",D["economics"].get("price"),"staked",D["economics"].get("staked"))

# --- exchange + desk + whale balances --------------------------------------
UPBIT_OTC="erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5"
OTC_DIST="erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"
DESKS={UPBIT_OTC:"UPbit OTC Desk",OTC_DIST:"OTC Distribution Wallet"}
MEGA="erd18mv2z6r2ksn4rfmm52tmhkc6x5tz6achmynvxftq4ay927029qqqmqpzfw"
CUSTODY="erd1rf4hv70arudgzus0ymnnsnc4pml0jkywg2xjvzslg0mz4nn2tg7q7k0t6p"
HOT="erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets"

watch={a:label[a] for a,c in cat.items() if c=="exchange"}
watch.update({UPBIT_OTC:"UPbit OTC Desk",OTC_DIST:"OTC Distribution Wallet",
              MEGA:"Mega Whale absorber",CUSTODY:"Binance Staking custody",HOT:"Binance.com hot"})
for w in prev.get("watch_addresses",[]): watch.setdefault(w["address"],(w.get("label") or "watch")[:50])

acc={}
for a,l in watch.items():
    acc[a]={"label":l,"info":get(f"/accounts/{a}")}
    time.sleep(0.18)
D["accounts"]=acc
print(f"[balances] {len(acc)} tracked wallets")

# --- desk flow, 48h and 24h -------------------------------------------------
for tag,after in (("48h",H48),("24h",H24)):
    ob,ib={},{}
    for d,l in DESKS.items():
        ob[d]={"label":l,"txs":paged(d,after,"sender",30,f"desk_{tag}")}
        ib[d]={"label":l,"txs":paged(d,after,"receiver",30,f"desk_{tag}")}
        print(f"[desk/{tag}] {l}: out={len(ob[d]['txs'])} in={len(ib[d]['txs'])}")
    D[f"desk_out_{tag}"]=ob; D[f"desk_in_{tag}"]=ib

# --- large transactions across tracked wallets, 48h -------------------------
big={}
for a,l in list(watch.items()):
    txs=paged(a,H48,"sender",8,"bigscan")
    rx=paged(a,H48,"receiver",8,"bigscan")
    big[a]={"label":l,"out":txs,"in":rx}
D["big_flows"]=big
print(f"[flows] scanned {len(big)} wallets for 48h transactions")

# --- token supplies ---------------------------------------------------------
toks=["SEGLD-3ad2d0","XEGLD-e413ed","SWTAO-356a25","USH-111e09","USDC-c76f1f",
      "USDT-f8c08c","WEGLD-bd4d79","MEX-455c57","LEGLD-d74da9","VOXEGLD-5872e5","VEGLD-2b9319"]
tv={}
for t in toks:
    tv[t]=get(f"/tokens/{t}"); time.sleep(0.6)
D["tokens"]=tv

D["_errors"]=ERR
json.dump(D,open(f"{OUT}/collected.json","w"))
print(f"\nsaved {OUT}/collected.json ; errors={len(ERR)}")
for e in ERR[:5]: print("  ERR",e)
