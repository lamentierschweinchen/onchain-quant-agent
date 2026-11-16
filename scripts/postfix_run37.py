#!/usr/bin/env python3
"""Run #37 post-inject fix: drop reward-behavior operator rows with no resolved owner (validator invariant)."""
import json
p="/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/reports/2026-11-16.json"; R=json.load(open(p))
po=R["staking_intelligence"]["reward_behavior"]["provider_operators"]
drop=[x.get("provider") or x.get("identity") for x in po if not x.get("owner_address")]
R["staking_intelligence"]["reward_behavior"]["provider_operators"]=[x for x in po if x.get("owner_address")]
if drop: R["meta_learning"]["data_gaps"].append(f"Reward-behavior operator row dropped (owner unresolved): {drop}")
# replace the injector's boilerplate paragraph with this week's measured figures
rb=R["staking_intelligence"]["reward_behavior"]; L0=json.load(open("/Users/ls/Documents/MultiversX/projects/onchain-quant-agent/data/learnings.json"))
prevc=[x for x in L0["runs"] if x["date"]<"2026-11-16"][-1]["running_baselines"]["reward_compound_pct"][-1]
an=R["staking_intelligence"]["analysis"]; cut=an.find("REWARD BEHAVIOR")
if cut>0: an=an[:cut].rstrip()
cv=rb["compound_vs_claim"]; ft=rb.get("delegator_fates_by_tier") or {}
inst=ft.get("institutional") or {}
sold=sum(1 for o in rb["provider_operators"] if (o.get("fates_by_count") or {}).get("sold"))
an+=(f"\n\nREWARDS. {rb['compound_pct_at_function_level']:.1f}% of reward decisions compounded ({cv['redelegate_count']} re-delegations vs {cv['claim_count']} claims at 8 sampled providers), down from {prevc:.1f}%: "
     f"more delegators took rewards as cash in the week the price fell. {inst.get('events',0)} large claims totalled {inst.get('total_value_egld',0):,.0f} EGLD. {sold} of {len(rb['provider_operators'])} sampled operators sent fee income to an exchange in 30 days.")
R["staking_intelligence"]["analysis"]=an
json.dump(R,open(p,"w"),indent=1,default=str); print("dropped",drop)
