#!/usr/bin/env python3
"""Run #36 post-inject fix: drop reward-behavior operator rows with no resolved owner (validator invariant)."""
import json
p="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/reports/2026-11-09.json"; R=json.load(open(p))
po=R["staking_intelligence"]["reward_behavior"]["provider_operators"]
drop=[x.get("provider") or x.get("identity") for x in po if not x.get("owner_address")]
R["staking_intelligence"]["reward_behavior"]["provider_operators"]=[x for x in po if x.get("owner_address")]
if drop: R["meta_learning"]["data_gaps"].append(f"Reward-behavior operator row dropped (owner unresolved): {drop}")
json.dump(R,open(p,"w"),indent=1,default=str); print("dropped",drop)
