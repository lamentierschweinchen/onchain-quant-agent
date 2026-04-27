# Analysis Methodology — Living Document

**Last updated**: 2026-04-27 (run #5, schema v2)
**Status**: This document is read and updated by the agent on every run. It contains proven practices, known pitfalls, and evolving heuristics.

---

## Core Principles

1. **Every metric needs a "so what?"** — Data without interpretation is a spreadsheet, not intelligence. Always explain what a number means for someone making decisions on MultiversX.
2. **Deltas matter more than absolutes** — "Staked ratio is 48.1%" is a fact. "Staked ratio rose 0.3pp this week, continuing a 4-week trend of increasing lockup" is intelligence.
3. **Name everything** — Addresses are meaningless to readers. Always resolve via known-addresses.json. If you can't label it, note it for investigation.
4. **Flag what you can't see** — Missing data is itself a signal. If an endpoint fails or returns unexpected results, say so explicitly.
5. **Forward-looking beats backward-looking** — Anomalies tell you what already happened. Trend indicators tell you what is about to happen. Both matter, but the second is the higher-value insight.
6. **Stratify before aggregating** — A single "exchange flow" number hides whether retail or whales drove it. Tier the data: by whale size, by exchange entity, by protocol category.

---

## API Best Practices

### What Works
- `/economics` — reliable, fast, cached. Use for all macro metrics.
- `/accounts?size=50&sort=balance&order=desc` — dynamic whale discovery. Run every time.
- `/accounts/{addr}/transactions?size=25&after=TIMESTAMP` — the ONLY reliable way to find whale transactions. Query ~30 accounts per run.
- `/providers?sort=locked&order=desc` — complete staking provider data.
- `/identities` — returns all ~263 validator identities in one call. No pagination needed.
- `/mex/pairs` — full xExchange pair data with 24h volume and TVL.
- `/mex/tokens` — includes `previous24hPrice` for calculating 24h changes.
- `/tokens?sort=accounts|transactions|marketCap` — three different views of the token ecosystem.

### What Doesn't Work
- **`minValue` on `/transactions`** — silently ignored. DO NOT USE. Wastes API calls and returns wrong data.
- **Global `/transactions`** for whale detection — only returns most recent ~100 txs network-wide. You'll get xPortal claim spam, not whale movements.
- **Relying on account nonce for activity** — some whales have nonce 0 (received via internal transfers/genesis). Zero nonce ≠ inactive.
- **Assuming exchange txs are visible as standard transactions** — large exchanges (e.g., MEXC) use internal transfers or smart contract mechanisms that don't appear in `/accounts/{addr}/transactions`. Always verify balance changes against the exchange balance snapshot in previous.json, not just recent tx queries.
- **`/mex/tokens` volume24h field** — returns $0 for all tokens despite real trading occurring. Use `/mex/pairs` for DEX volume data. The pairs endpoint correctly shows per-pair 24h volume and trade counts.

### Intermediary Wallet Investigation Pattern
When a large transfer goes to an unknown account:
1. Check the recipient's **nonce** — low nonce (< 10) = high probability routing wallet; medium nonce (10–100) = still possible routing wallet
2. Fetch their **recent transactions** to see if they immediately forwarded the funds
3. Check **current balance** — near-zero balance after a large receipt = confirmed routing wallet (regardless of nonce)
4. **IMPORTANT: Low nonce ≠ cold storage guarantee**. Nonce 4 accounts can reactivate after weeks of dormancy. Always re-check activity if an account was previously classified cold.
5. This pattern identified: Binance 470K restaking (nonce 3 router), Coinbase 798K OTC (nonce 80 router)

### Coinbase OTC Pattern
When Coinbase shows large inflows AND outflows in the same week:
1. Check if the gross flows are from/to different counterparties — this confirms OTC intermediation
2. Net balance change is the signal (net -7K EGLD despite 1M+ gross flows = OTC neutral)
3. The buyers and sellers are identifiable as the counterparties
4. This pattern identified the Apr 18 2026 bilateral deal: Whale A+B sold 1.026M, mega-whale erd18mv2z6r2 received 798K

### Key Metric Distinction
- **`/economics` `staked`** = total EGLD locked in the Staking Module contract (14.25M EGLD) — includes both direct node staking and delegation
- **`/providers` `locked`** = total EGLD locked via delegation smart contracts only (11.17M EGLD) — excludes direct node operator staking
- These will always differ. Use `/economics` staked for macro staked ratio, `/providers` for delegation market concentration metrics.

### Rate Limiting
- No explicit rate limit headers, but add 200ms delays between requests.
- Budget ~50-60 API calls per run. Prioritize whale accounts over completeness.
- If you need to paginate, the per-request max is 50 items.

---

## Whale Detection Methodology

### Priority Order for Account Queries
1. **Known exchange addresses** (~17) — always query, these are the flow indicators
2. **Top 10 non-exchange, non-system accounts** — dynamic whale discovery
3. **Accounts from previous.json that dropped out of top 50** — potential large outflows
4. **Addresses flagged in learnings.json** — follow up on previously discovered unknowns

### Whale Tier Stratification (v2)
Stratify the top-100 wallets into balance tiers and report the aggregate movement of each tier separately.

| Tier | Threshold | Typical Holders |
|------|-----------|-----------------|
| `mega_whale` | > 1,000,000 EGLD | Exchange staking pools, mega-OTC counterparties, foundation wallets |
| `large_whale` | 100,000 — 1,000,000 EGLD | Exchange hot wallets, individual mega-holders, large delegation contracts |
| `mid_whale` | 10,000 — 100,000 EGLD | Smaller exchanges, active traders, mid-tier holders |

**Why it matters**: a single "exchange flow" number is too coarse. If mega_whales are net-shrinking while mid_whales are net-growing, that's wealth distribution. If mega_whales grow while mid_whales shrink, that's accumulation by the very largest holders. Each pattern has different implications for liquidity and price stability.

### Entity Netting (v2)
Many entities (Binance, Coinbase) operate from multiple wallets. The per-wallet view is noisy. Collapse them to a single net-flow figure per parent entity.

Example: Binance Hot 1 (-77K) + Binance Hot 2 (-23K) + Binance Cold (0) + Binance Staking (+50K) = -50K Binance net.

Use entity netting alongside, not instead of, per-wallet flows. The per-wallet detail explains the *mechanism*; the entity-level netting tells you the *direction*.

### Transaction Classification
| Flow Type | Logic |
|-----------|-------|
| `exchange_inflow` | Receiver is known exchange, sender is not |
| `exchange_outflow` | Sender is known exchange, receiver is not |
| `defi_deposit` | Receiver is known DeFi contract |
| `defi_withdrawal` | Sender is known DeFi contract |
| `staking` | Receiver is known staking provider |
| `unstaking` | Sender is known staking provider |
| `bridge` | Either party is a bridge contract |
| `whale_to_whale` | Both are large holders, neither exchange/DeFi |
| `unknown` | Can't classify — flag for investigation |

### Balance Change Detection
- Compare top 50 accounts against `data/previous.json`
- Flag any account with >5% balance change
- Flag any account that dropped out of / entered the top 50
- Track exchange total balance WoW for the net flow signal

---

## Staking Analysis

### Concentration Metrics
- **Herfindahl-Hirschman Index (HHI)**: sum of squared market shares for all providers
  - < 0.15 = competitive market
  - 0.15-0.25 = moderate concentration
  - > 0.25 = highly concentrated
- **Top-5 and Top-10 share**: simple percentage of total stake
- Track these WoW — trend matters more than absolute level

### APR Analysis
- Base APR (10.8%) vs TopUp APR (6.5%) spread indicates how top-heavy the network is
- Provider APR varies from ~6.5% to ~9.3% — the spread is meaningful for delegators
- Low-fee providers (Incal 1%, Maple Leaf 0%) vs standard 12% fee is worth highlighting

### APR Distribution Histogram (v2)
Bucket all providers by APR into: `5-6%`, `6-7%`, `7-8%`, `8-9%`, `9-10%`, `10%+`. For each bucket, output `provider_count` and `total_locked_egld`.

**Interpretation**:
- Tight cluster around one bucket (e.g. all providers in 7-8%) → competitive equilibrium, fees converged
- Wide spread → market opportunity, delegators can earn meaningfully more by switching
- Most stake concentrated in a low-APR bucket while a high-APR bucket exists with little stake → delegator inertia (they're not chasing yield)

### APR vs Fee Outliers (v2)
- `top_apr` — top 5 providers ranked by APR (the highest yield available)
- `lowest_fee` — top 5 providers ranked by lowest fee (highest delegator-share value)

The intersection of these two lists is the asymmetric value zone. A high-APR + low-fee provider that has *not* attracted proportional stake is a clear delegator opportunity worth flagging.

### Churn Metric (v2)
Sum `numUsers` across all providers → `total_delegators_current`. Compare to previous week's sum:
- `delegators_added` — net new delegators this week
- `providers_gaining_delegators` / `providers_losing_delegators` — breadth of churn

**Interpretation matrix**:
| Delegators | Staked EGLD | Read |
|------------|-------------|------|
| ↑ | ↑ | Healthy retail growth |
| ↑ | flat | Retail joining, no whale conviction |
| flat | ↑ | Whale consolidation, no new participation |
| ↓ | ↑ | Concentrated re-staking by fewer larger holders (e.g. exchange restaking events) |
| ↓ | ↓ | Outflow / unstaking pressure |

---

## Token Analysis

### Noise vs Signal
- **Ignore high-holder-count tokens with zero market cap** — these are airdrop spam (DRX with 2.47M holders is not real adoption)
- **Real token ecosystem starts at WEGLD** (134K holders) and USDC (83K holders)
- Focus on tokens with both meaningful holder count AND market cap
- Volume spikes relative to a token's own baseline are more interesting than absolute volume

### xExchange Health Indicators
- Daily volume / EGLD market cap ratio: measures DEX utilization
- Number of pairs with >$1K daily volume: measures how many pairs are "alive"
- WEGLD/USDC dominance %: if one pair is >50% of all volume, the DEX is thin

### Newly-Issued Tokens (v2)
Pull `/tokens?sort=timestamp&order=desc&size=50` and filter client-side for `timestamp >= SEVEN_DAYS_AGO`. Rank by holder traction.

**Quality filter** (in this order):
1. Has > 10 holders (filters spam mints)
2. Has > 5 transactions (filters dormant deploys)
3. Has identifiable deployer (cross-reference deployer against known-addresses.json)

Report top 5. A new token deployed by a known team or DeFi protocol is a higher-signal launch than an unknown deployer.

## DeFi Per-Protocol Breakdown (v2)

Each tracked protocol gets its own row in `protocol_breakdown`. Address sets come from `data/known-addresses.json`:

| Protocol | Category | Address Set | What to Track |
|----------|----------|-------------|---------------|
| xExchange | dex | `defi_xexchange` (16 addresses) | TVL across pair contracts, 24h volume from `/mex/pairs`, transfers |
| Hatom | lending + liquid_staking | `defi_hatom` (16 addresses) | EGLD Money Market TVL, sEGLD supply, borrow utilization |
| AshSwap | dex (stableswap) | `defi_ashswap` (9 addresses) | Pool TVL, swap volume |
| OneDex | dex (aggregator) | `defi_onedex` (5 addresses) | Aggregator routing volume |
| XOXNO | nft_marketplace | `defi_other` subset | Marketplace contract activity |
| JEXchange | dex (orderbook) | `defi_jexchange` (4 addresses) | Order book depth proxies |

**Health signal mapping**:
- `growing` — TVL up >5% WoW, transfers up
- `flat` — TVL within ±2%, transfers stable
- `shrinking` — TVL down 2-15% WoW, sustained
- `spiking` — TVL or transfers up >50% WoW (likely event-driven)
- `draining` — TVL down >15% WoW (concerning, investigate)

Always sum addresses per protocol — a single address can be misleading. xExchange has separate WEGLD contracts per shard; both must be summed for accurate TVL.

---

## Anomaly Detection — Graceful Degradation (v2)

The agent now ships z-score logic on every run, with a documented fallback when sample size is insufficient.

### Three Methods, Selected by Data Availability

**Method 1 — Z-score** (used when N >= 4 data points exist for the metric in `learnings.json` `running_baselines`)
- mean = average of baseline array (excluding current)
- stddev = population stddev of baseline array
- z = (current - mean) / stddev
- Severity:
  - |z| > 4 → critical
  - |z| > 3 → high
  - |z| > 2 → medium
  - |z| > 1.5 → low (note as "approaching anomaly threshold")
- Set `method: "z_score"` and populate `average_value`, `stddev`, `z_score`

**Method 2 — Percent threshold** (fallback when N < 4 data points)
- |% change vs previous| > 50% → low
- > 100% → medium
- > 200% → high
- > 500% → critical
- Set `method: "percent_threshold"` and populate `change_pct`. Note in `description` that this is degraded mode and full z-score will activate at week N+1.

**Method 3 — Rule-based** (always available, complements above)
- Dormant wallet activations
- Exchange exits >25% in a single week
- Validator joining/leaving events with >50K EGLD
- Token holder declines on a streak ≥3 consecutive weeks
- Set `method: "rule_based"`

### Common False Positives to Filter
- Epoch transitions can cause temporary metric spikes
- Token listing/delisting on xExchange creates volume anomalies
- Weekend/holiday activity dips are not anomalies
- Single-week routing wallet activity (Binance restaking, OTC desk injection) is *expected* once flagged — don't re-flag the same pattern week after week

## Trend Indicators (v2)

Distinct from anomalies (point-in-time deviations), trend indicators capture multi-week trajectories — the leading edge of where the network is going.

### accelerating_exchange_outflows
For each exchange in `previous.json` `exchange_balances`, check whether the current WoW change is in the same direction as previous 2+ weeks.
- 3 consecutive weeks of decline → emit a trend entry with `cumulative_change_pct` and `interpretation`
- Example: Gate.io declined 3 weeks running (-25%, -22%, -22%) cumulating -54% — likely customer exit or treasury rebalance

### validator_movements
Compare provider list this week vs previous week:
- `providers_joining` — providers in current `/providers` but not in `previous.staking_providers`
- `providers_leaving` — providers in previous but not in current (or current locked = 0)
- `notable_joiners`/`notable_leavers` — providers with >50K EGLD locked

Sustained net validator joining = network growth signal. Net leaving = consolidation pressure.

### token_supply_events
Compare `supply` field for tracked tokens vs previous week:
- > 1% supply change for normal tokens → mint or burn event
- > 0.1% for stablecoins (USDC, USDT) → meaningful issuance/redemption
- 100% supply change (zero → nonzero or vice versa) → lock/unlock event

### consecutive_streaks
Across the running_baselines arrays, identify metrics that have moved in the same direction for 3+ consecutive weeks. The interpretation field should explain *what* the streak means (e.g. "EGLD price up 5 weeks → momentum regime").

### regime_shifts
Step-changes that look like regime breaks rather than mean-reverting noise. Distinct from anomalies — an anomaly is a point spike that could revert; a regime shift is a level change that persists.

Heuristic: if a metric jumps >2 sigma AND the new level is sustained for 2+ weeks, promote it from anomaly to regime_shift.

---

## Report JSON Schema — CRITICAL

The dashboard (`dashboard/src/types/report.ts`) enforces a strict schema. A blank page means the JSON doesn't match. The report JSON **must** have these exact top-level keys:

```
metadata, executive_summary, network_health, whale_intelligence,
staking_intelligence, token_activity, defi_activity, anomalies,
watch_list, meta_learning
```

Use `dashboard/public/reports/2026-04-07.json` as the canonical reference. Do NOT invent a flat schema — it will break the dashboard silently.

After generating the JSON, also run the deployment steps:
1. `cd dashboard && npx tsx scripts/generate-manifest.ts` — copies JSON to public/
2. `git add ... && git push`
3. `cd dashboard && vercel --prod` — deploy to Vercel
4. Return the stable URL: **https://dashboard-omega-lyart-99.vercel.app**

---

## Report Quality Checklist

Before committing the report, verify:
- [ ] All EGLD amounts are human-readable (divided by 10^18)
- [ ] All addresses are labeled where possible
- [ ] Every section has an analysis paragraph, not just tables
- [ ] Executive summary has 5 actionable bullets
- [ ] Watch list items from previous week are addressed (kept, updated, or graduated)
- [ ] JSON report matches the schema in data/report-schema.json
- [ ] previous.json is updated with current snapshot
- [ ] learnings.json is updated with this run's findings
- [ ] methodology.md is updated if new practices were established

---

## Evolution Log

| Run | Date | Changes |
|-----|------|---------|
| 1 | 2026-04-02 | Initial methodology established. Per-account whale detection, entity resolution, staking HHI, baseline snapshot format. |
| 2 | 2026-04-07 | Added BTC/ETH price context. Confirmed OTC desk pattern for recurring large exchange outflows. Added `exchange_balances` and `watch_addresses` to previous.json for cleaner WoW tracking. Discovered that `/providers` total locked ≠ `/economics` staked (different metrics). |
| 3 | 2026-04-13 | Established intermediary wallet investigation pattern for routing wallets (check nonce + immediate txs). Confirmed mex/tokens volume24h is unreliable (returns $0) — use mex/pairs exclusively. OTC desk lifecycle confirmed at ~3 weeks. Begin 3-point running baselines for z-score prep. |
| 4 | 2026-04-20 | Confirmed routing wallet nonce is NOT always near-zero (nonce 80 wallet was pure pass-through). Confirmed low nonce ≠ cold storage guarantee (nonce 4 wallet reactivated). Established Coinbase OTC pattern: simultaneous large inflows+outflows from different counterparties = OTC intermediation — watch net balance, not gross flows. mex/pairs field names confirmed: baseName, quoteName, volume24h, totalValue. 4-run z-score baselines now active. |
| 5 | 2026-04-27 | **Schema v2 expansion**: top 10/10/5 token coverage, whale tier stratification (mega/large/mid >1M / 100K-1M / 10K-100K), exchange entity netting, per-protocol DeFi breakdown (xExchange, Hatom, AshSwap, OneDex, XOXNO, JEXchange), APR distribution histogram, staking churn metric, top APR + lowest fee outliers, dormant_days field on dormant_activations, graceful-degradation z-scores (z when N>=4, % threshold when N<4, rule_based always), new trend_indicators section (accelerating_exchange_outflows, validator_movements, token_supply_events, consecutive_streaks, regime_shifts). All schema additions backward-compatible. |
