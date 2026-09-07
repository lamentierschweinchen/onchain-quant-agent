#!/usr/bin/env python3
"""Run #24 followup: recover the two genuinely truncated sources.

(1) BINANCE.COM HOT WALLET OUTBOUND. The main pass paged it at 1,000 txs and
    covered 4.4 of 7 days, so the 97,390 EGLD hot-to-pipeline figure that
    resolved the binance-desk-feed-standing test is a LOWER BOUND. Recovered by
    slicing the window into calendar days so each slice fits the page budget -
    the fix run #24 recommended for run #25, applied retrospectively.

(2) THE 16 PAGE-CAPPED PROVIDER SCANS. Re-checked rather than re-queried: every
    one was already re-paged at 30 pages in the main run and the largest deep
    result is 765 txs against a 1,500 cap, so nothing is truncated. The report's
    third failed-source entry is a false caveat and is corrected.
"""
import json, time, urllib.request, urllib.parse
from datetime import datetime, timezone

API="https://api.multiversx.com"
REPO="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent"
RD="2026-09-07"

def get(path, params=None, retries=3):
    url=API+path+("?"+urllib.parse.urlencode(params) if params else "")
    delay=1.0
    for a in range(retries+1):
        try:
            req=urllib.request.Request(url, headers={"User-Agent":"intel-agent/24-followup"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if "429" in str(e) and a<retries:
                time.sleep(delay); delay=min(delay*2,12.0); continue
            if a==retries: return {"__error__":str(e)}
            time.sleep(0.8)

def ts(y,m,d): return int(datetime(y,m,d,tzinfo=timezone.utc).timestamp())

kn=json.load(open(f"{REPO}/data/known-addresses.json"))
LABEL={}
for sec,ent in kn.items():
    if isinstance(ent,dict) and sec!="_metadata":
        for a,meta in ent.items():
            if isinstance(meta,dict) and a.startswith("erd1"): LABEL[a]=meta.get("name","Unknown")
DESK={"erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5",
      "erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r"}
FEEDERS={a for a,l in LABEL.items()
         if "OTC Desk Feeder" in l or "OTC Router" in l or "→OTC" in l or "->OTC" in l}
HOT=["erd1sdslvlxvfnnflzj42l8czrcngq3xjjzkjp3rgul4ttk6hntr4qdsv6sets",
     "erd1ylwuswz9zuk4acuq4aa6d0x9ys293yhlpwg6vpuwntndyej4u44q896zlz",
     "erd1v4ms58e22zjcp08suzqgm9ajmumwxcy4hfkdc23gvynnegjdflmsj6gmaq"]
DAYS=[(ts(2026,8,31)+86400*i, ts(2026,8,31)+86400*(i+1)) for i in range(7)]

def page_day(addr, after, before, max_pages=40):
    out, frm, capped = [], 0, False
    for _ in range(max_pages):
        b=get(f"/accounts/{addr}/transactions",
              {"size":50,"from":frm,"after":after,"before":before,"order":"desc",
               "status":"success","sender":addr})
        time.sleep(0.2)
        if isinstance(b,dict) and "__error__" in b:
            return out, "error:"+b["__error__"]
        if not isinstance(b,list) or not b: return out, False
        out+=b
        if len(b)<50: return out, False
        frm+=50
    return out, True

per_day, to_pipe, seen = [], {}, set()
tot_txs=0; caps=[]
for addr in HOT:
    for after,before in DAYS:
        txs, capped = page_day(addr, after, before)
        tot_txs += len(txs)
        if capped: caps.append({"address":addr,"after":after,"capped":capped})
        pipe=0.0
        for t in txs:
            v=int(t.get("value","0"))/1e18
            r=t.get("receiver")
            if v>0 and (r in DESK or r in FEEDERS):
                pipe+=v
                if t.get("txHash") not in seen:
                    seen.add(t["txHash"])
                    to_pipe[r]=to_pipe.get(r,0)+v
        per_day.append({"wallet":LABEL.get(addr,addr[:14]),"address":addr,
                        "day":datetime.fromtimestamp(after,tz=timezone.utc).strftime("%Y-%m-%d"),
                        "txs":len(txs),"to_pipeline_egld":pipe,"page_capped":capped})
        print(f"  {addr[:14]} {datetime.fromtimestamp(after,tz=timezone.utc):%m-%d}: {len(txs):5} txs, "
              f"{pipe:>10,.0f} EGLD to pipeline{' [CAPPED]' if capped else ''}")

total=sum(to_pipe.values())
OUT={"_window":"2026-08-31..2026-09-07 (daily slices)",
     "method":"per-calendar-day pagination of the three Binance.com hot wallets, 40 pages/day",
     "total_txs_scanned":tot_txs,
     "hot_to_pipeline_egld":total,
     "main_pass_figure_egld":97390.15,
     "by_recipient":{LABEL.get(k,k[:14]):v for k,v in sorted(to_pipe.items(),key=lambda x:-x[1])},
     "per_day":per_day,
     "page_caps_remaining":caps,
     "provider_scan_recheck":{
       "capped_first_pass":16,"deep_rescanned":16,"deep_caps":0,"largest_deep_result_txs":765,
       "deep_budget_txs":1500,
       "verdict":"NOT truncated. All 16 contracts that filled the 6-page first pass were re-paged at 30 pages and none came close to the deeper cap. The report's third failed-source entry is a false caveat."}}
json.dump(OUT,open(f"{REPO}/data/collected/followup_{RD}.json","w"),indent=1)
print(f"\nHOT -> PIPELINE (7 full days): {total:,.0f} EGLD  vs main pass {97390.15:,.0f} "
      f"({100*(total-97390.15)/97390.15:+.1f}%)")
print("scanned",tot_txs,"txs;",len(caps),"day-slices still capped")
print("by recipient:",json.dumps({k:round(v) for k,v in OUT['by_recipient'].items()},indent=1))
