#!/usr/bin/env python3
"""Re-fetch H-token + LSD market caps after 429."""
import json, time, urllib.request, urllib.parse

API = "https://api.multiversx.com"
OUT = "/tmp/run10/collected.json"

def get(path, retries=4):
    url = API + path
    for attempt in range(retries+1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent":"intel-agent/10"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            if "429" in str(e):
                time.sleep(3.0 + attempt*2)
                continue
            if attempt == retries:
                return {"__error__": str(e), "__url__": url}
            time.sleep(1.0)

D = json.load(open(OUT))
tvl_tokens = ["HUSDC-d80042","HEGLD-d61095","HUSDT-6f0914","HWBTC-49ca31","HWETH-b3d17e",
              "HBUSD-ac1fca","HHTM-e03ba5","HMEX-df6df7","HUTK-4fa4b2","HWTAO-2e9136",
              "SEGLD-3ad2d0","SWTAO-356a25","USH-111e09","XEGLD-e413ed"]
new = {}
for t in tvl_tokens:
    info = get(f"/tokens/{t}")
    print(f"{t}: mcap={info.get('marketCap') if isinstance(info,dict) else None} err={info.get('__error__') if isinstance(info,dict) else None}")
    new[t] = info
    time.sleep(0.6)

D["tvl_tokens"] = new
json.dump(D, open(OUT, "w"))
print("saved")
