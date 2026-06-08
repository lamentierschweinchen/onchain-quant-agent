# Delegator and Provider Reward-Behavior Analysis

**Report addendum**: 2026-06-08 (run #11 follow-up)
**Method**: `scripts/delegator_behavior.py`
**Sample**: top 8 providers by locked EGLD · 7-day window for delegator events · 30-day window for operator wallets · 12 claims per provider maximum traced
**Raw output**: [data/collected/delegator_behavior_2026-06-08.json](../data/collected/delegator_behavior_2026-06-08.json)

This addendum answers two questions the regular weekly report has not covered:
- **a)** What do individual DELEGATORS do with claimed rewards? (sell / hold / compound)
- **b)** What do staking PROVIDERS do with the service-fee earnings? (compound / sell / treasury)

---

## TL;DR

1. **At the function-call level, 62% of all reward decisions are to COMPOUND** (reDelegateRewards 348 vs claimRewards 214 across 8 top providers in 7 days). Delegators on MultiversX overwhelmingly auto-stack rewards rather than claim them out.
2. **Retail (<1 EGLD/claim) does not sell rewards** — across 68 sampled retail claims totaling 14.6 EGLD, ZERO went to a labeled exchange. 88% of retail-claimed value stays in the claimant's wallet.
3. **Institutional claims (50-1000 EGLD/claim) split ~50/50 sell vs hold by value** — small sample (3 events) but each individual decision is large enough to materially move flows.
4. **Provider operators do not sell to exchanges** in the 30d sample. Operator outbound flows go to treasury wallets, secondary internal addresses, or in one case (truststaking) to a DeFi protocol.
5. **NEW RELATIONSHIP DISCOVERED**: **truststaking is operated by XOXNO: Deployer Wallet** (`erd1x45vnu7shhecfz0v03qqfmy8srndch50cdx7m763p743tzlwah0sgzewlm`). truststaking is the 4th largest provider by locked EGLD (366K, 7,171 users); XOXNO routes 135K of operator outbound to `defi_deposit` (likely the XOXNO LSD via the deployer wallet's own contracts).

---

## Methodology

**Function-call semantics** (verified live):

| Function | Meaning |
|---|---|
| `reDelegateRewards` | Delegator compounds rewards back into their stake |
| `claimRewards` | Delegator pulls EGLD into their wallet |
| `delegate` | New stake added |
| `unDelegate` | Stake withdrawn (starts unbonding) |
| `withdraw` | Completion of an unbond |
| `reward` | Provider-initiated reward distribution |

**Delegator fate classification** — for each `claimRewards` event, the next outbound EGLD tx within 72h is classified:

| Fate | Logic |
|---|---|
| `sold` | Next receiver is in `known-addresses.json` with `category = exchange` |
| `rotated_provider` | Next receiver is another delegation contract (`erd1qqqqqqqqqqqqqqqp…`) |
| `defi_deposit` | Next receiver is a DeFi protocol contract |
| `held_or_other` | Next receiver is unknown / unlabeled |
| `held` | No outbound tx > 0.001 EGLD within 72h |

**Claim value** — derived from the `claimRewards` tx's smart-contract result (the EGLD that flowed from the delegation contract back to the claimant). Tier thresholds: retail < 1, mid-tier 1-50, institutional 50-1000, whale > 1000 EGLD per claim.

---

## Function-level distribution (8 providers, 7d, 719 events)

| Function | Count | Share |
|---|---|---|
| `reDelegateRewards` | 348 | **48.4%** |
| `claimRewards` | 214 | **29.8%** |
| `delegate` | 78 | 10.8% |
| `reward` | 34 | 4.7% |
| `withdraw` | 23 | 3.2% |
| `unDelegate` | 22 | 3.1% |

**Compound vs claim** (function-level, ignoring delegate/withdraw): **61.9% compound**.

This is the simplest signal: **delegators on the top 8 providers are roughly 2:1 in favor of auto-compounding rather than claiming**. This is a much higher compounding rate than I'd guessed — and a healthy signal for the staked ratio (the network's 48% staked ratio is sustained without delegators having to opt in to re-staking every reward).

---

## Delegator fates by tier (87 traced claims · 432 EGLD total)

| Tier | Events | Total EGLD | Held | Sold | Rotated | DeFi | Held/other |
|---|---|---|---|---|---|---|---|
| **Retail** (<1 EGLD) | 68 | 14.6 | 52 (88% of value) | 0 | 8 | 1 | 7 |
| **Mid-tier** (1-50 EGLD) | 16 | 152.1 | 11 (50% of value) | 1 (33%) | 1 (7%) | 0 | 3 (11%) |
| **Institutional** (50-1000 EGLD) | 3 | 258.3 | 1 (46% of value) | 2 (54%) | 0 | 0 | 0 |
| **Whale** (>1000 EGLD) | 0 | — | — | — | — | — | — |

### What this means

- **Retail does not sell**. Across 68 retail-tier claims (avg 0.21 EGLD), exactly zero go to a labeled exchange. Most retail-claimed value (88%) stays in the claimant's wallet. The small "rotated_provider" group (8 events, 0.72 EGLD) is delegators consolidating across providers.
- **Mid-tier is mostly hold**. One claimer sold 49.7 EGLD; the other 15 events stayed in-wallet. This is the noise tier — could swing either way with more sample.
- **Institutional shows real sell pressure**. 2 of 3 institutional claims (138.6 EGLD = 54% of institutional value) went to a CEX deposit. This is a small sample, but a single 50+ EGLD claim sold to exchange is materially more impactful than 50 retail claims held.

### Caveats

- `held_or_other` is over-broad. Some of those destinations are bridges (sold in spirit), some are treasury wallets (held in spirit), some are DEX routers (sold via on-chain). To split these correctly, we'd need to expand known-addresses coverage of bridges, treasuries, and DEX routers.
- 72h window may miss "delayed sells" — claimer holds for 4 days then deposits to CEX.
- The institutional/whale sample is too small for confident percentages (3 events). Need 4-8 weeks of data for stable estimates.

---

## Provider operator behavior (8 owners, 30d outbound)

| Provider | Operator wallet | 30d outbound EGLD count | Destinations |
|---|---|---|---|
| figment-networks | unlabeled | 0 | — |
| binance_staking | unlabeled | 0 | — |
| stakingagency | unlabeled | 5 (463 EGLD) | held_or_other |
| **truststaking** | **XOXNO: Deployer Wallet** | 4 (341 EGLD) | 205 EGLD held_or_other + **135 EGLD defi_deposit** |
| meria | unlabeled | 1 (346 EGLD) | held_or_other |
| istariv | unlabeled | 1 (786 EGLD) | held_or_other |
| thepalmtreenw | unlabeled | 1 (550 EGLD) | held_or_other |
| validblocks | unlabeled | 0 | — |

### Key findings

- **Zero operators sold fees to a labeled exchange** in the 30d window. The dominant pattern is operator → unlabeled wallet (likely treasury or secondary internal address).
- **truststaking is operated by XOXNO** (`erd1x45vnu7shhecfz0v03qqfmy8srndch50cdx7m763p743tzlwah0sgzewlm`). truststaking is the 4th-largest provider by locked EGLD (366K, 7,171 users). The 135 EGLD that XOXNO deployed to `defi_deposit` is likely the XOXNO LSD or related XOXNO contract — i.e., **the operator is re-deploying fees into the same protocol's DeFi stack**. This is a strategic finding: the XOXNO/truststaking pair gives XOXNO leverage over a meaningful slice of MultiversX delegation.
- **figment-networks, binance_staking, validblocks**: zero outbound from the operator in 30d. Either fees are accumulating in the contract (developerReward field), or they're skimmed via internal SC calls we'd need to trace separately.

### Caveats

- Operator wallets may receive non-fee EGLD (treasury inflows, founder personal funds), so not all outbound is "fee deployment."
- The provider's accumulated fee revenue often stays *inside* the delegation contract as `developerReward` (visible on `/accounts/{prov_addr}` `developerReward` field) and only flows to the operator wallet when extracted. To get the complete picture, we'd need to also track `developerReward` over time.

---

## Recommendations

### 1. Make this a recurring weekly section

Add `staking_intelligence.reward_behavior` to the schema:

```json
{
  "reward_behavior": {
    "providers_sampled": 8,
    "window_days": 7,
    "compound_pct_at_function_level": 61.9,
    "delegator_fates_by_tier": {
      "retail": { "events": 68, "value_egld": 14.6, "by_count": {...}, "by_value": {...} },
      "mid_tier": { ... },
      "institutional": { ... }
    },
    "provider_operator_fee_destinations": [
      { "provider": "truststaking", "owner": "XOXNO: Deployer Wallet",
        "outbound_30d_egld": 341, "fates_by_value_egld": { "held_or_other": 205, "defi_deposit": 135 } }
    ]
  }
}
```

This adds ~200 API calls to a typical weekly run (8 providers × ~25 calls each). Manageable within the existing budget.

### 2. Expand entity resolution

The "held_or_other" bucket is too broad. Adding the following address sets to `known-addresses.json` would let us classify more precisely:

- **MultiversX bridges** to ETH, BSC, etc. (any → bridge = "exit_to_other_chain")
- **DEX routers** (WEGLD wrappers, OneDex/AshSwap entry points) (any → dex_router = "sold_on_dex")
- **Operator treasury wallets** (now we know truststaking → XOXNO; same enrichment for the other top operators)

### 3. Add `developerReward` tracking

Each delegation contract has a `developerReward` field that represents accumulated fees not yet extracted. Tracking this across weeks gives the COMPLETE picture of fee economics:

- Fees accrued (developerReward delta + extractions)
- Fees extracted to operator wallet (when operator outbound spikes)
- Fees deployed (operator outbound destinations)

The cycle period (accrual → extraction → deployment) varies by operator; some skim continuously, some let fees accumulate for months.

### 4. Watch list for next run

- **truststaking operator flows**: a XOXNO-operated provider routing 135 EGLD to DeFi this month is a clean lever for XOXNO to influence on-chain liquidity. Track whether the defi_deposit flow grows or stays flat.
- **Institutional claim spike**: if next week shows >10 institutional-tier claims, the 50/50 sell/hold ratio becomes statistically meaningful and a directional signal for whale rotation.
- **Compound rate trajectory**: 61.9% compound this week. If this falls during continued price decline, retail is panicking out of compounding (bearish DeFi sentiment).

---

## Action items

- [x] Prototype script committed: `scripts/delegator_behavior.py`
- [x] Raw output preserved: `data/collected/delegator_behavior_2026-06-08.json`
- [x] truststaking → XOXNO relationship documented (this report)
- [ ] Add operator addresses to `known-addresses.json` under new `staking_provider_operators` section
- [ ] Integrate into weekly report schema next run
- [ ] Build a "compound rate" dashboard widget — single most actionable number from this analysis
