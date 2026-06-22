# Analysis Methodology — Living Document

**Last updated**: 2026-06-22 (run #13, schema v2)
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


### Cross-Exchange OTC Funnel Pattern (run #6, 2026-05-04)

The OTC desks on MultiversX are NOT exchange-internal infrastructure — they are shared infrastructure that aggregates flow from multiple exchanges.

**Detection signature**:
1. Routing wallet receives identical-amount chunks (e.g. 5,999 / 7,999 / 8,000 EGLD) from a known exchange wallet
2. Routing wallet has near-zero balance immediately before AND immediately after the receipt
3. Within minutes, the same amount is forwarded to a known OTC desk
4. Wallet has medium-high nonce (>100) but low active balance — pure pass-through pattern

**First documented case**: Binance.com 2 (erd1sdsl) → 3 routing wallets (erd16nws nonce 169, erd1k4r6 nonce 180, erd1de38 nonce 147) → UPbit OTC Desk + OTC Distribution Wallet. ~80K EGLD routed in week 1.

**Implication**: A single OTC desk's gross inflows do NOT represent a single exchange's customer flow — they aggregate flows from multiple exchange counterparties. Net OTC flow analysis must consider the entire upstream chain.

**To validate next run**: query the OTC desks' downstream recipients (erd1f4kcxxn4, erd1tuvllxaf, erd1krmy7xld, erd142cjv2r5) — if they forward to other exchanges' deposit addresses, the multi-hop pipeline is confirmed.

**VALIDATED in run #7 (2026-05-11)**: Confirmed at scale. 8 routing wallets traced forwarding UPbit OTC + OTC Distribution chunks to Bybit/Binance/KuCoin. Plus reverse flows: Bybit→KuCoin (erd1rffkz8zwp3), KuCoin↔Binance↔Bybit (erd14n5vtgezss). The OTC pipeline is operational bidirectional cross-exchange settlement infrastructure. Detection method now industrialized: query each OTC desk's outflows, look for identical-amount chunks (1-8K EGLD typical) forwarded within minutes to wallets with near-zero balance and high nonce (>100). Then query those routing wallets to identify the destination exchange.

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

### Delegator and Provider Reward Behavior (v3, run #11)

**Tool**: `scripts/delegator_behavior.py`

A focused analysis of what individual delegators do with claimed rewards (sell/hold/compound) and what staking providers do with service-fee earnings (compound/sell/treasury). This complements the per-provider WoW change view by tracking the *decisions* underlying those changes.

#### Function-call semantics on delegation contracts

| Function | Meaning |
|---|---|
| `reDelegateRewards` | Delegator compounds rewards back into their stake |
| `claimRewards` | Delegator pulls EGLD into their wallet |
| `delegate` | New stake added |
| `unDelegate` | Stake withdrawn (starts unbonding) |
| `withdraw` | Completion of an unbond |
| `reward` | Provider-initiated reward distribution |

#### Compound vs Claim ratio at function-level

For top-N providers, query inbound transactions over the past 7d, count function calls. The simplest metric is `reDelegateRewards / (reDelegateRewards + claimRewards)`. Run #11 baseline: **61.9% compound** across top 8 providers (348 redelegate vs 214 claim).

If this ratio falls during continued price decline, retail is panic-claiming (bearish DeFi sentiment). If it rises, delegators are doubling down on yield (bullish).

#### Delegator fate classification (per claim)

For each `claimRewards` event, look up the claimant's next outbound EGLD tx within 72h:

| Fate | Logic |
|---|---|
| `sold` | Next receiver is `category=exchange` in known-addresses.json |
| `rotated_provider` | Next receiver is another delegation contract |
| `defi_deposit` | Next receiver is `category=defi` |
| `held_or_other` | Next receiver unlabeled |
| `held` | No outbound tx > 0.001 EGLD within 72h |

Tier thresholds (per-claim value): retail <1 EGLD, mid-tier 1-50, institutional 50-1000, whale >1000.

#### Provider operator behavior

Each delegation contract has an `ownerAddress` (the operator wallet). Query its outbound EGLD over 30d, classify destinations the same way. Helps answer: does the provider sell, treasury, or re-deploy fees?

#### Discoveries from run #11 baseline

- **Retail (<1 EGLD/claim) does not sell rewards** — 0 of 68 retail claims went to a labeled exchange.
- **Institutional (50-1000 EGLD/claim) is ~50/50 sell vs hold** by value (small sample of 3).
- **No provider operator sold fees to exchanges** in 30d. Top destination = treasury wallets (held_or_other).
- **truststaking is operated by XOXNO: Deployer Wallet** — discovered via this analysis. XOXNO has both a flagship LSD and control of the 4th-largest provider.

Full results: [reports/2026-06-08-delegator-behavior.md](../reports/2026-06-08-delegator-behavior.md) and `data/collected/delegator_behavior_2026-06-08.json`.

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

### Newly-Issued Tokens (v2 — workaround active as of run #11)

**Note**: `/tokens?sort=timestamp` returns HTTP 400 — silently unsupported. Use the ESDT system SC scan workaround below.

#### Working method (run #11+):
1. Query `/accounts/erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u/transactions?after=SEVEN_DAYS_AGO&status=success&function=issue&size=50`
2. For each tx, decode `data` field: base64 → hex pairs separated by `@`
3. Format: `issue@<name_hex>@<ticker_hex>@<supply_hex>@<decimals_hex>@<flag_key_hex>@<flag_val_hex>@...`
4. Decode `<name_hex>` and `<ticker_hex>` from hex back to ASCII
5. Resolve the resulting `IDENTIFIER-randomhex` via `/tokens?search=<TICKER>&size=10` filtered by exact name match
6. Report top 5 ranked by holders traction (filter: >10 holders, >5 txs, identifiable deployer)

#### Quality filter (run #11+):
1. Has > 10 holders (filters spam mints)
2. Has > 5 transactions (filters dormant deploys)
3. Has identifiable deployer (cross-reference deployer against known-addresses.json)

Report top 5. A new token deployed by a known team or DeFi protocol is a higher-signal launch than an unknown deployer.

Run #11 detected 3 issuances this method: FRANZELA (FRA, 2 holders), GreenSmokeNetwork (GSN, 1 holder), GrandTheftAurum (GTA, 1 holder). All sub-quality filter, but the method itself worked reliably.

### (Deprecated, kept for context) Original method
Pull `/tokens?sort=timestamp&order=desc&size=50` and filter client-side for `timestamp >= SEVEN_DAYS_AGO`. Rank by holder traction.

**Quality filter** (in this order):
1. Has > 10 holders (filters spam mints)
2. Has > 5 transactions (filters dormant deploys)
3. Has identifiable deployer (cross-reference deployer against known-addresses.json)

Report top 5. A new token deployed by a known team or DeFi protocol is a higher-signal launch than an unknown deployer.

## DeFi Per-Protocol Breakdown (v2)

Each tracked protocol gets its own row in `protocol_breakdown`. Address sets come from `data/known-addresses.json`:

| Protocol | Category | Address Set | TVL Method |
|----------|----------|-------------|------------|
| xExchange | dex | `defi_xexchange` (16 addresses) | Sum contract balances + 24h volume from `/mex/pairs` |
| Hatom Lending | lending | `defi_hatom` (39 addresses) | Sum H-token market caps (HUSDC, HWBTC, HEGLD, HWETH, HUSDT, HWTAO, HHTM, HMEX, HUTK, HBUSD). Exclude HSEGLD/HSWTAO to avoid double-count |
| Hatom Liquid Staking | liquid_staking | `defi_hatom` subset | SEGLD-3ad2d0 market cap + SWTAO-356a25 market cap |
| Hatom USH | stablecoin | `defi_hatom` subset | USH-111e09 market cap |
| XOXNO LSD | liquid_staking | `defi_xoxno` subset | XEGLD-e413ed market cap |
| XOXNO Aggregator | aggregator | `defi_xoxno` subset | `transfers_24h` only (non-custodial) |
| XOXNO Marketplace | nft_marketplace | `defi_xoxno` subset | Operational EGLD only; NFT volume is the real metric |
| AshSwap | dex (stableswap) | `defi_ashswap` (9 addresses) | Pool TVL, swap volume |
| OneDex | aggregator | `defi_onedex` (5 addresses) | `transfers_24h` (aggregator) |
| JEXchange | dex (orderbook) | `defi_jexchange` (4 addresses) | `transfers_24h` (orderbook) |

### SWTAO null-mcap fallback (run #11, 2026-06-08)

The MultiversX /tokens/SWTAO-356a25 endpoint occasionally returns `price: null` and `marketCap: null` (verified live this run). When this happens, the assembler will silently zero out the SWTAO portion of Hatom LSD TVL, making it appear ~$1M smaller than reality and producing implausible WoW deltas (e.g., -26% EGLD).

**Fallback derivation**:
```
accumulator_ratio = prev_swtao_price / prev_wtao_price       # ~1.22 typical
swtao_price_est = wtao_price_current * accumulator_ratio
swtao_mcap_est = swtao_price_est * swtao_supply_current
```

The accumulator ratio is stable WoW (rewards accrue smoothly). Validated this run: derived $264.02/SWTAO produced ~$875K mcap, making Hatom LSD ~$3.38M (-0.8% EGLD WoW, essentially flat) — matching the expected magnitude given SEGLD supply only fell -0.9%.

Add this fallback to future assembler scripts. The audit script (`scripts/audit_report.py`) flags the null condition as an ERROR; treating it as one will catch the issue before publish.

### LSDs: report in SUPPLY terms, not market cap (run #13, 2026-06-22)

**Mcap-based LSD TVL is price-contaminated and produces phantom contraction signals.** SEGLD/XEGLD mcap = price × supply. During an EGLD decline, mcap falls even when the underlying staked position is unchanged; SWTAO mcap tracks TAO price entirely (not MultiversX flows). The run #11/#12 "synchronized LSD contraction" narrative was largely a price artifact built on mcap.

**Rule**: the primary LSD/stablecoin signal is **circulating supply** (the `/tokens/{id}` `supply` field, which is decimals-adjusted and never returns null), compared WoW. Mcap is secondary (USD context only).

Run #13 demonstration — in supply terms the LSDs were flat-to-up while USD mcaps fell:
| Token | Supply WoW | USD mcap WoW | Read |
|---|---|---|---|
| SEGLD-3ad2d0 | -0.51% | -5.3% | flat (mild redemption); USD drop is price |
| XEGLD-e413ed | **+0.63%** | -3.5% | GREW; the run #12 "3rd-week contraction" watch was NOT confirmed |
| SWTAO-356a25 | -0.06% | -17.7% | flat; mcap drop is TAO price |
| USH-111e09 | -0.08% | -0.2% | flat; 2-week burn trend ended |

`previous.json` now stores an `lsd_supply` block (SEGLD/XEGLD/SWTAO/USH raw supply) so the next run can compute supply WoW directly without needing the prior collected snapshot.

### dataApi token null-price recovery (run #13, 2026-06-22) — SUPERSEDES the run #12 1.0s rule

The run #12 rule ("≥1.0s spacing fixes /tokens/{id} nulls") is **incomplete**. This run, the four `priceSource.type == "dataApi"` tokens (SEGLD, SWTAO, USH, XEGLD) returned `price=null marketCap=null` on the sequential pass **even at 1.05s spacing**, while the H-tokens (a different price source) populated fine. Isolated re-fetch of just those four at **2.5s spacing** recovered all of them.

**Rule**: after the main `/tokens/{id}` pass, detect any dataApi-class token with `price is None` and re-fetch it individually at ≥2.5s spacing (up to ~4 retries). Do NOT treat a single null pass as an outage — it is a transient dataApi feed hiccup under sequential load that recovers on isolated retry. Combined with supply-based TVL (above), this makes the LSD/stablecoin TVL robust to the feed. The audit script's null-mcap ERROR remains the backstop.

### Exit-liquidity-bounce pattern VALIDATED (run #13, 2026-06-22)

Run #12 flagged the "exit liquidity bounce": EGLD +1.36% on collapsing engagement (delegators, DEX volume, on-exchange capital). Run #13 resolved it — the bounce **failed within one week**, breaking to a new low ($2.85 < the $2.95 floor) while exchange inflows continued (3rd week) and the OTC pipeline reloaded. **Promote to a reusable bearish forward indicator**: a relief rally on contracting engagement is distribution, not reversal; expect it to fail to new lows within 1-2 weeks.

### Stablecoin contraction as de-risking indicator (run #11, 2026-06-08)

When USH (Hatom stablecoin) supply BURNS >1% in a single week during a price decline, this signals borrowers actively closing CDP positions to release collateral and avoid liquidation. USH is the borrowing token in Hatom CDPs, so supply burn = position closures.

This week: USH -47,072 (-7.08%), the largest single-week burn observed. Synchronized with SEGLD -6,510 (-0.9%) and XEGLD -3,790 (-1.2%) supply contractions = cross-Hatom de-risking visible. Bearish signal for DeFi engagement: users actively reducing leverage.

Surface this in:
- `executive_summary` (when USH change >5%)
- `anomalies` (severity high when USH change >5%, medium when 1-5%)
- `defi_activity.analysis` (always, when any of USH/SEGLD/XEGLD move >1%)

### Critical TVL Lesson (run #5, 2026-04-27)

Lending protocols on MultiversX denominate contract balance in deposit-receipt tokens (HUSDC, HWBTC, HSEGLD, etc.), NOT in EGLD. Summing contract EGLD balance produces a near-zero TVL for the entire lending stack. The correct method is to sum the H-token market caps, which represent the total deposited collateral.

Applied to Hatom: previous TVL estimate was $528K (sum of EGLD-only contract balances). Corrected: $10.23M ($5.15M LSD + $4.37M Lending + $708K USH). A **19x underestimate** before correction.

### LSD Double-Count Avoidance

When a user stakes EGLD into Hatom LSD they receive SEGLD. If they then deposit SEGLD into Hatom Money Market they receive HSEGLD. Both SEGLD and HSEGLD have non-zero market caps, but counting both double-counts the same underlying EGLD. Same applies to SWTAO/HSWTAO and XEGLD (XOXNO's LSD has its own deposit market via the LSD Composability contract).

Rule: when computing protocol TVL, **exclude H-tokens that wrap LSDs**. Count the LSD itself once.

### TVL Method by Protocol Category

| Category | Method | Reason |
|----------|--------|--------|
| Liquid staking | LSD-token market cap | Underlying is delegated to validators, not held in contract |
| Lending | Sum of deposit-receipt token market caps | Balance is denominated in lent tokens, not EGLD |
| DEX (AMM) | Sum contract balance × 2 (pool ratio) | Both sides of pair counted |
| DEX (aggregator) | `transfers_24h` only — TVL is irrelevant | Non-custodial routing |
| NFT marketplace | NFT trading volume — contract balance is operational only | NFTs are escrowed but value is in NFTs not EGLD |
| Stablecoin | Stablecoin market cap | Direct measure of collateralized value |

**Health signal mapping**:
- `growing` — TVL up >5% WoW, transfers up
- `flat` — TVL within ±2%, transfers stable
- `shrinking` — TVL down 2-15% WoW, sustained
- `spiking` — TVL or transfers up >50% WoW (likely event-driven)
- `draining` — TVL down >15% WoW (concerning, investigate)

Always sum addresses per protocol — a single address can be misleading. xExchange has separate WEGLD contracts per shard; both must be summed for accurate TVL.

---


### Protocol-level transfers_24h (run #6, 2026-05-04)

The correct endpoint for protocol activity throughput is:
```
/accounts/{addr}/transfers/count?after={unix_ts}
```

Previous attempts using account-object fields (`scrCount`, `transfersLast24h`) returned 0 or null because those fields are not present in `/accounts/{addr}` response. The dedicated `/transfers/count` endpoint is the correct path. Verified with XOXNO Aggregator (12,181 transfers in 24h), OneDex (8,110), JEXchange Lite Pool (2,229).

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
- **Failed forward indicator convergence** (new run #11): when 3+ of a prior run's `recommendations_for_next_run` bullish forwards resolve in the BEARISH direction within the same reporting period, this is a decisive bearish convergence signal. Emit as high-severity rule-based anomaly. Distinguishes random noise (one prediction misses) from regime shift (multiple bullish forwards all failing simultaneously).
- **Bilateral inverse rule magnitude deterioration** (new run #11): track ratio `|Hatom Lending EGLD %| / |EGLD price %|` across confirmed events. Series so far: 0.88, 0.80, 0.70, 0.21 (this week). Sustained decline = depositor capacity exhaustion. Emit when ratio drops below 0.30.
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

The dashboard (`dashboard/src/types/report.ts`) enforces a strict schema. **A blank page means the JSON doesn't match** and the React tree unmounted due to an unhandled error (no App-level error boundary). The report JSON **must** have these exact top-level keys:

```
metadata, executive_summary, network_health, whale_intelligence,
staking_intelligence, token_activity, defi_activity, anomalies,
watch_list, meta_learning
```

### Two-layer pre-publish gate (run AFTER assemble, BEFORE manifest/commit/deploy)

**Layer 1 — Data-integrity audit** (added run #11 after the SWTAO/USH miss):

```bash
python3 scripts/audit_report.py reports/${REPORT_DATE}.json data/collected/${REPORT_DATE}.json
```

Catches the class of bug that schema validation cannot:
- Token API returning null price/marketCap (e.g., SWTAO-356a25 ran null this week, silently making Hatom LSD appear -26% EGLD WoW when the real value was -1%)
- Large supply events under-emphasized (e.g., USH -7.08% surfaced only in trend_indicators, not exec_summary — the audit flags any >5% supply change not appearing in TL;DR)
- Implausible protocol_breakdown WoW deltas (>25% suggests missing input data)
- Null-but-derivable fields (top_by_market_cap.holders, top_by_volume.previous_transactions)
- Excessive Unknown labels in large_transactions (>60% triggers a warning to trace recurring routers)
- APR distribution coverage below 95% of total delegated
- Hatom LSD sum = SEGLD + SWTAO (cross-check against the raw API totals)

Exit 0 if no errors (warnings allowed), 1 if errors.

**Layer 2 — Schema + dashboard invariant validator** (existing, added run #8):

```bash
python3 scripts/validate_report.py reports/${REPORT_DATE}.json
```

Checks three layers:
1. JSON Schema (`data/report-schema.json`) — types and enums
2. Dashboard-rendering invariants — required fields the React components call methods on
3. Enum string-literal unions

Exit 0 means safe to manifest+deploy. Non-zero exit means **do not push**; fix the JSON and re-run.

### Field-name canon (the parts the validator can't infer)

The dashboard's `dashboard/src/types/report.ts` is the source of truth. Common gotchas worth memorizing:

| Section | Required field name | Common wrong name |
|---|---|---|
| `trend_indicators.validator_movements.notable_leavers[]` | `previous_locked_egld` | `locked_egld_previous` ← run #8 broke this |
| `whale_intelligence.whale_tiers.{tier}_whales` | `count_current`, `total_balance_egld`, `previous_total_balance_egld` | `count`, `total_egld`, `total_egld_previous` |
| `whale_intelligence.exchange_flows.by_exchange[]` | `exchange`, `change_egld`, `pct` | `name`, `flow_egld` |
| `staking_intelligence.apr_distribution.buckets[]` | `label`, `min_apr_pct`, `max_apr_pct`, `provider_count`, `total_locked_egld` | `bucket`, `min`, `max`, `count`, `locked` |
| `token_activity.top_by_holders[]` | `previous_holders`, `holders_change` | `holders_previous`, `holders_wow_change` |
| `whale_intelligence.large_transactions[].timestamp` | ISO 8601 string | Unix int |

### Extending enums

If you genuinely need a new enum value (new flow type, new protocol category), extend ALL THREE in the same commit:
1. `data/report-schema.json` (the schema)
2. `dashboard/src/types/report.ts` (the TS union — additive only)
3. `scripts/validate_report.py` `ENUM_INVARIANTS` table
4. Then rebuild + redeploy the dashboard

### Why this matters

Run #8 had `locked_egld_previous` instead of `previous_locked_egld` in notable_leavers. JSON loaded fine, HTTP 200, but `formatEgldBare(undefined).toLocaleString()` threw at first render. Because there's no App-level error boundary, the WHOLE React tree unmounted — page completely blank, no spinner, no error message. The validator catches this class of bug before deploy.

### Deployment steps (run AFTER validator passes)
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
| 5.1 | 2026-04-27 | **XOXNO ecosystem expansion**: added 14 XOXNO contracts to known-addresses.json under new `defi_xoxno` section. Split XOXNO tracking into 4 sub-protocols (LSD, Aggregator, Marketplace, Other) since they have different metrics. **TVL method discovery**: for liquid staking protocols, contract balance is misleading — use the staked-derivative token's market cap as TVL proxy (XEGLD-e413ed market cap = $1.54M = ~359K EGLD staked). For non-custodial routers (XOXNO Aggregator, OneDex), TVL is irrelevant — the metric is `transfers_24h`. **Activity ranking**: XOXNO Aggregator handles 21,926 transfers/24h (highest single-contract throughput on the network); OneDex 13,308; JEXchange 3,772; xExchange 5 contracts combined 3,120. **Dashboard ergonomics**: added expand/collapse to long DataTables (top 5 default → "Show all (N)" footer button) for providers, wallets, transactions, tokens, protocol breakdown — full-set sort still active when collapsed. |
| 5.2 | 2026-04-27 | **Hatom ecosystem expansion + lending TVL methodology fix**. Hatom has 59 contracts total (deployer wallet erd1cc2yw...99pvt); previously tracked 16 → now 39. Added: 13 money markets (EGLD, sEGLD, USDC, USDT, WBTC, WETH, BUSD, HTM, MEX, UTK, wTAO, swTAO), TAO Liquid Staking + Wrapped TAO Minter, isolated lending (EGLD + wTAO), USH stablecoin suite (4 strategy contracts), 7 asset facilitators (cross-protocol), Booster v2, Price Aggregator v2, deployer wallet. **CRITICAL TVL FIX**: lending protocols denominate balance in H-tokens (deposit receipts), not EGLD — summing contract EGLD balances missed the entire lending stack. Corrected method: sum H-token market caps. **Hatom TVL recalibrated $528K → $10.23M** (~19x underestimate before correction). Split Hatom into 3 sub-protocols in `protocol_breakdown`: Lending ($4.37M), Liquid Staking ($5.15M = SEGLD + SWTAO), USH ($708K). **New ranking**: Hatom dominates MultiversX DeFi with 70% of total tracked TVL ($10.23M of $14.7M total). xExchange $2.32M, XOXNO LSD $1.54M. **Double-count avoidance rule**: exclude H-tokens that wrap LSDs (HSEGLD, HSWTAO) since the underlying value is already in the LSD-token market cap. |
| 6 | 2026-05-04 | **Cross-exchange OTC funnel discovery**: First observed shared OTC infrastructure on MultiversX. Binance.com 2 (erd1sdsl) → 3 routing wallets (erd16nws nonce 169, erd1k4r6 nonce 180, erd1de38 nonce 147) → UPbit OTC Desk + OTC Distribution Wallet. Pattern: identical-amount chunks (5,999/7,999/8,000 EGLD), forwarded within minutes, near-zero-balance routers. **Yield-chasing migration confirmed** as a recurring trend indicator: Ninja Staking +15.5K and Egld Staking Provider +14.2K (both 0%-fee, 9%+ APR) gained the equivalent of what 5 lower-APR providers lost — first activation after 4 weeks of inertia. **API endpoint discovery**: /accounts/{addr}/transfers/count?after={ts} is the correct endpoint for protocol-level transfers_24h (NOT account object fields). **Hatom H-token discovery**: /tokens?search={ticker} filtered for 'Hatom' name prefix is reliable token-discovery path; full Hatom Lending stack: HUSDC + HUSDT + HEGLD + HWBTC + HWETH + HHTM + HMEX + HUTK + HWTAO + HBUSD = $4.41M. **Z-score reversion validated**: EGLD price went +3.29σ → +0.77σ in one week, confirming the run #5 'one-week event' classification. Stored FULL provider list (108) in previous.json — enables churn analysis from run #7. New section in known-addresses.json: 'exchange_routers' with 3 entries. |
| 7 | 2026-05-11 | **Cross-exchange OTC pipeline VALIDATED**: 8 new routing wallets traced confirming multi-hop CEX-to-CEX settlement layer. Routes: UPbit OTC + OTC Distribution → routers (erd1g8ll, erd1n5wcu, erd1cwkw3, erd1dmmh5, erd1fs0c4, erd17cfk3, erd1fdkq6, erd1ljlcx) → Bybit/Binance/KuCoin. PLUS reverse flows: Bybit → erd1rffkz8zwp3 → KuCoin; KuCoin → erd14n5vtgezss → Bybit (bidirectional). The OTC fabric is general-purpose CEX-CEX settlement, not unidirectional distribution. **First major unstaking event**: -325K from /economics staked module, +377K to Binance Staking wallet. Single-source single-destination flow (Binance unstaked ~377K from direct nodes). 50% staked-ratio approach REVERSED 49.50% → 48.33%. **NEW RULE**: When EGLD price ripping, lending TVL underperforms (depositors withdraw to capture gains). Hatom Lending flat in USD = -13% in EGLD terms during the +14.7% rally. **NEW RULE**: Major staking-wallet balance increases (Binance Staking +377K) predict directional pressure within 1-2 weeks — the capital is parked, watch for movement. **NEW RULE**: DEX volume during EGLD rallies concentrates in WEGLD/USDC (91% this week). Single-pair dominance = CEX-derived buyers parking in stablecoin pairs. **Z-score history**: egld_price +3.29σ (run #5) → +0.77σ (run #6) → +3.40σ (run #7). Second elevation in 4 weeks suggests structural pattern, not noise. **DEX volume +5.86σ — largest z-score in tracked history**. Watch for regime shift confirmation next week. **Yield-chase sustained for 2 weeks**: Egld Staking Provider +17K (after +14.2K last week), Ninja Staking +3K. Top losers all 7-12% fee 7-9% APR. **All 10 protocol_breakdown TVLs computed**: Hatom Lending $5.31M, Hatom LSD $4.49M, Hatom USH $686K, XOXNO LSD $1.71M, xExchange TVL aggregated. |
| 9 | 2026-05-25 | **Binance staking-custody accumulation discovered**: hot wallet erd1sdsl -316K -> Binance Staking custody wallet +267K (now 3.38M), but the protocol staked module rose only +2K -> capital PARKED, not delegated. Combined with run #7's 377K, Binance holds a large undeployed EGLD position in its staking wallet. New top forward indicator: track this wallet vs economics.staked weekly (jump in staked = delegation/bullish; drawdown to hot wallets = distribution/bearish). **NEW RULE - degenerate z-scores**: when a baseline's stddev is tiny relative to the metric (total_delegators sd~18 on ~179K base), small moves produce spurious huge z-scores (z=-4.5 for a -0.03% move). Always cross-check absolute % change; downgrade severity when economic move <0.1%. **CONFIRMED - decompose entity netting**: intra-entity wallet shuffles (Binance hot->staking custody) dominate the headline exchange-flow number; always break entity net into per-wallet moves before calling a flow bullish/bearish. **Exchange-flow reversal VALIDATED**: run #8's +169K bearish inflow was a single-week reaction (reverted to -56K outflow) - the two-week confirmation rule worked. **ZoidPay DEX event**: ZPAY +59% price, ZPAY/WEGLD pair captured 40.8% of xExchange volume - first non-WEGLD/USDC pair >40% in tracking history; WEGLD/USDC dominance 91.6%->56.2%. **Yield-chase week 4** with rotating leadership (procryptostaking +17K, valuestaking +16K took over from ninjastaking/egldstakingprovider). **MEX z-score activated** (N=4, z=-0.83 normal). **Bilateral inverse rule scales with price**: +2.3% price -> Hatom Lending -1% EGLD (mild). **Token supply-event fix**: previous.json now stores supply_raw (raw integer) so run #10 can diff like-for-like (prior runs stored decimals-adjusted, breaking comparison). **OTC source funder found**: erd12tq6ax5k -> erd17l22 (~2K). erd17l22 dormant after run #8 distribution wave; OTC desks in distribution phase (~145K throughput). |
| 8 | 2026-05-18 | **OTC source wallet template ESTABLISHED**: Tracing run #7's flagged Unknown Whale erd17l22 (last week +58K) revealed it distributes 2K EGLD chunks through erd1nhtq4 (nonce 2543, ~7.5K balance) → erd1ecyftln (nonce 50, 0 balance) → OTC Distribution Wallet + UPbit OTC Desk. erd17l22 is therefore an OTC SOURCE wallet — completing the missing upstream link in the pipeline taxonomy (source → router → desk → desk-router → exchange). Detection method: when a top-100 non-exchange whale shows large WoW balance change, query top 1-2 outbound recipients, then trace through 2-3 hops — typically terminates at a known OTC desk. **BILATERAL INVERSE RULE CONFIRMED**: Run #7 saw Hatom Lending -13% EGLD during +14.7% rally; this week's mirror image: Hatom Lending +13.6% EGLD during -16.9% decline, Hatom LSD +21.9% EGLD. Depositors capture gains during rallies, DCA during dips. Useful as leading indicator of expected behavior. **DEX volume regime-shift watch CLOSED**: Run #7 +5.86σ peak ($328K) fully reverted to -0.67σ ($75K), -77% retrace. Confirmed event-driven anomaly, not regime. **Yield-chase PROMOTED to regime shift** after 3 consecutive weeks: ninjastaking +37.9K cumulative (run #6/7/8: +15.5K/+3K/+19.4K), egldstakingprovider +38.1K cumulative. Both providers near-tripled their stake in 3 weeks. **Exchange flows reverted to NET INFLOW** during the decline (-17%): +169K EGLD onto exchanges (Binance +76K, Coinbase +39K, Gate.io +21K, UPbit +14.5K). Classic bearish setup, opposite of run #7. **NEW QUIRK**: Always trim top-50-vs-top-50 when computing whale tier deltas. Run #7 stored only top 50 in previous.json — fetching top 100 silently inflated mid_whale tier (reported +30 wallets where actual is +1). **NEW QUIRK**: Hatom H-token identifiers — use `/tokens?search=Hatom` not guessed suffixes. Correct: HUSDC-d80042, HEGLD-d61095, HUSDT-6f0914, HWBTC-49ca31, HWETH-b3d17e, HBUSD-ac1fca, HHTM-e03ba5, HMEX-df6df7, HUTK-4fa4b2, HWTAO-2e9136, HSEGLD-c13a4e, HSWTAO-6df80c. |
| 10b | 2026-06-01 | **APR/Fee units schema bug fixed + retroactive migration**. The MultiversX /providers API returns `apr` already in percent units (6.37 = 6.37%) but `serviceFee` as a fraction (0.12 = 12%). Inconsistent. The pipeline was storing both raw, so `apr_pct` was correct but `fee_pct` was 100× too small in the JSON. Dashboard's `cleanServiceFee()` formatter (just `.toFixed(2) + "%"`) renders apr_pct correctly but rendered fee_pct=0.12 as "0.12%" instead of "12%". Bug present in runs #8 and #9 only — earlier runs happened to store `fee_pct` in percent units, #8 changed the convention silently. **Fix**: assembler now stores `fee_pct = serviceFee * 100`, matching apr_pct's percent convention. Markdown drops the `*100` everywhere. **Retroactive migration**: `scripts/migrate_fee_pct.py` patched runs #8 and #9 in-place (idempotent guard: only multiplies if max(fee_pct) <= 1.0). **NEW METHODOLOGY**: unit conventions for stored numeric fields must be documented in the schema. New rule — every `*_pct` field in the JSON is in percent units (12.0 means 12%), never a fraction. Validator could/should enforce this. **DONE same day**: raw collected.json now persisted under `data/collected/{REPORT_DATE}.json` and committed (1.6 MB this run; ~80 MB/year steady state). Backfilled run #10. AGENT_PROMPT.md updated so future runs save automatically. Earlier runs (#1-#9) only have whatever data was carried forward into the report JSONs — not backfillable retroactively. |
| 11a | 2026-06-08 | **DELEGATOR/PROVIDER REWARD-BEHAVIOR ANALYSIS** (new layer added late in run #11). New script `scripts/delegator_behavior.py` traces what individual delegators and provider operators do with EGLD rewards. Method: for each `claimRewards` event on top providers in a 7d window, look up the claimant's next outbound EGLD tx within 72h and classify (sold to CEX / rotated to another provider / DeFi deposit / held). For provider operators: query `ownerAddress` outbound flows over 30d. **Run #11 baseline findings**: function-level compound rate = **61.9%** across top 8 providers (348 redelegate vs 214 claim); retail (<1 EGLD/claim) does NOT sell rewards (0 of 68 went to a CEX, 88% held in-wallet); institutional (50-1000 EGLD/claim) splits ~50/50 sell vs hold by value (small sample of 3); zero provider operators sold to exchanges in 30d (all routed to treasury wallets). **NEW RELATIONSHIP DISCOVERED**: truststaking operator wallet = `erd1x45vnu7…` = **XOXNO: Deployer Wallet**. truststaking is the 4th-largest provider (366K locked, 7,171 users); XOXNO has both a flagship LSD AND control of a top delegation provider — significant strategic position. 30d operator outbound: 205 EGLD to held_or_other + 135 EGLD to defi_deposit (likely XOXNO LSD or XOXNO contracts). **New `staking_provider_operators` section added to known-addresses.json** with 7 operator wallets for the top providers. **API quirks**: (1) `/providers?size=N` parameter is IGNORED — always returns all ~185 providers; must slice client-side. (2) `urllib.parse.urlencode` requires explicit `import urllib.parse` at module level (Python scoping bug if imported inside function — silently fails as `__error__` dict). |
| 11 | 2026-06-08 | **EGLD FLOOR BROKE, BULLISH FORWARDS COLLAPSED**: EGLD -15.7% to $2.95, broke run #10's $3.50 floor, z=-3.32σ HIGH severity. 5-week cumulative -37% from May 4 peak. EGLD UNDERPERFORMED BTC (+1.3%) and ETH (+3.6%) - decoupled to the downside, MultiversX-specific weakness. **NEW PATTERN: 'failed forward indicator' as bearish signal**: 3 of 4 run #10 bullish forwards resolved BEARISH simultaneously - (1) Binance Staking custody STALLED at 3.51M (3-week accumulation ended, no delegation, no distribution); (2) $3.50 floor BROKE; (3) Coinbase 3-week outflow streak REVERSED (+43K inflow this week from a 3-week -62K outflow streak). When 3+ bullish forwards fail together during a decline, it is a decisive bearish convergence. The only directionally validated prediction was the BEARISH-for-retail OTC distribution wave. **OTC distribution wave HIT ON SCHEDULE (week 1 of 1-3 predicted window)**: UPbit OTC -14K (-30%), OTC Distribution -12.4K (-28%), combined -26.4K. Retail throughput 163K in 7d. The load-distribute cycle is now empirically validated at 1-week minimum period. **Newly-issued token detection WORKAROUND SUCCEEDED** (6-run blocker resolved): /accounts/erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u/transactions?function=issue returns ESDT issuance txs. Decode tx.data hex segments split on @ to extract [name, ticker, supply, decimals, ...flags]. Look up identifier via /tokens?search=<NAME>. 3 issuances detected (FRA, GSN, GTA - all low-quality spam, 0-2 holders). **Bilateral inverse rule 5th confirmation but MAGNITUDE DETERIORATING**: response ratios across events 0.88, 0.80, 0.70, 0.21 (this week). Hypothesis: depositor capacity diminishing OR conviction reducing as decline persists. **Yield-chase regime ENDED at week 5**: cohort net flow -2.6K, 3 of 5 prior leaders reversed; only ninjastaking sustained (+38K cumulative over 5 weeks). **Synchronized LSD contraction** during decline (Hatom LSD -1.6% EGLD, XOXNO LSD -1.4% EGLD) - new unusual pattern; watch for confirmation. **API quirk - funder address typo**: erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp is the ACTUAL funder (not the typo-variant carried from run #10). Now canonicalized in known-addresses.json. **Largest absolute delegator drop in tracking history**: -447 WoW (vs typical -24 to -53). Capitulation pattern emerging. |
| 10 | 2026-06-01 | **OTC PIPELINE FULLY TRACED TO BINANCE ORIGIN**: Verified erd12tq6ax5k as the missing link funder. 14d inbound = 100% from Binance.com hot wallet (erd1sdsl, 8,972 EGLD); 7d outbound = 100% to erd17l22 (OTC source). Balance 0, pure pass-through, nonce 1505 (heavy historical use). Full pipeline: Binance.com → erd12tq6ax5k (funder) → erd17l22 (source) → chain routers → UPbit OTC Desk + OTC Distribution → retail. Implication: Binance is the ultimate originator of MultiversX on-chain OTC distribution. New tracing methodology: query candidate funder's 14d inbound, check sender concentration + balance + outbound mirroring. **BINANCE STAKING CUSTODY 3RD WEEK OF ACCUMULATION** (3.11M → 3.38M → 3.51M, +402K cumulative). Protocol staked module barely moved — capital remains PARKED. Promoted from anomaly to structural-position regime shift. **EGLD -11.84% to $3.50, broke prior $3.74 floor**. z=-2.09σ (medium). 4-week trajectory -25% from May 4 peak. EGLD underperformed BTC (-1.4%) and ETH (-2.4%). **BILATERAL INVERSE RULE NOW WELL-CALIBRATED** across 3 events: +14.7%/-13%, -16.9%/+13.6%, -11.8%/+8.3% (linear magnitude relationship). **OTC DESKS REVERSED TO LOADING PHASE** (UPbit OTC Desk +56%, OTC Distribution +54%, combined +32.6K) — predicts new distribution wave in 1-3 weeks. **YIELD-CHASE REGIME STALLING WEEK 5**: cohort net flow dropped from ~+50K cumulative weeks 1-4 to +3.5K this week (only procryptostaking sustained; valuestaking/egldstakingprovider/orius all reversed). **ZoidPay/WEGLD dominance FULLY REVERTED** 40.8% → 8.9% — confirms run #9 event-driven. **TOKEN SUPPLY EVENT DETECTION ACTIVE** (supply_raw diff): WEGLD +4.7% (+26K wrapped) flagged as first real event. **NEW METHODOLOGY RULE**: filter erd1qqqq* system staking contracts from validator joiner/leaver lists — protocol direct-node aggregators that move above/below threshold are not real validator events. **API quirk**: /tokens/{id} batch hits HTTP 429 with sub-0.5s delays; use ≥0.5s between H-token mcap queries. |
| 13 | 2026-06-22 | **CAPITULATION BOUNCE FAILED - exit-liquidity thesis VALIDATED**: EGLD -4.68% to $2.85, breaking back below the $2.95 floor to a new local low one week after run #12's +1.36% relief rally. EGLD again decoupled to the downside (WoW BTC -2.49%, ETH +1.43%). The run #12 'exit liquidity bounce' (price up on collapsing engagement) correctly predicted the failure - now promoted to a reusable bearish forward indicator. **DELEGATOR CAPITULATION WAS A ONE-SHOT**: -78 WoW (vs -4,003 last week); base stabilized at 174,406, staked-EGLD unstaking decelerated -38K->-9K. Run #9 degenerate-z-score guard applied (z=-2.68σ downgraded to LOW for a -0.04% move). **EXCHANGE NET INFLOW 3rd consecutive week** (+12K): Coinbase 3-week streak (+43K/+8.3K/+6.0K) exceeds the 2-week confirmation rule -> off-exchange-accumulation reversal STRUCTURAL. **BINANCE STAKING CUSTODY 3rd-week stall** at 3.51M (6 weeks parked, 779K). **OTC PIPELINE RELOADED** on schedule (+7K desk balance, 85K throughput; Binance->OTC Router 2 feeding 4,800 chunks) - distribution wave expected 1-3 weeks. **NEW METHODOLOGY - report LSDs in SUPPLY terms not mcap**: supply-based WoW (SEGLD -0.5%, XEGLD +0.6%) shows LSDs flat-to-up while USD mcaps fell; the multi-run 'synchronized LSD contraction' narrative was a price artifact. previous.json now stores lsd_supply. **NEW API QUIRK - dataApi tokens null even at 1.0s** (supersedes run #12 rule): SEGLD/SWTAO/USH/XEGLD returned null at 1.05s; isolated 2.5s re-fetch recovered all. Need a populated-or-retry guard. **Reward compound rate slid 3rd week** 61.9%->59.14%->55.31% (mild bearish drift). **Stablecoin supply contracted** USDC -0.5% USDT -1.8% (burn). USH 2-week de-leveraging ENDED (supply flat). 9 of 10 prior action items completed. |
| 12 | 2026-06-15 | **EXIT LIQUIDITY BOUNCE SIGNATURE** (new bearish pattern): EGLD +1.36% to $2.99 (FIRST up-week after 5 down-weeks, matching run #11's capitulation bounce prediction off the $2.95 floor) but ALL engagement metrics collapsed simultaneously - (1) delegator base -4,003 = largest single-week drop in tracking by 9x; (2) DEX volume -55% = largest WoW drop in tracking; (3) yield-chase cohort fully unwound, net -17K, ninjastaking (sole 5-wk sustained gainer) reversed -10.5K; (4) on-exchange capital build 2nd consecutive week (Coinbase +8.3K confirms 2-week net-inflow per run #11's confirmation rule); (5) reward compound rate 61.9% -> 59.14% (mild). Diagnosis: technical bounce on sell-side execution, not demand-driven recovery. Sellers used the bounce as exit liquidity. **NEW METHODOLOGY**: 'engagement composite' as forward indicator - if next week shows price flat-or-down WHILE engagement metrics keep contracting, regime is decisively bearish; if engagement recovers, the bounce is real. **NEW API QUIRK**: /tokens/{id} HTTP 429 rate-limit triggers at <1.0s spacing AND returns successful HTTP 200 responses with price=null marketCap=null silently. The run #10b 0.5s rule is INCORRECT. New rule: ≥1.0s between /tokens/{id} queries. This silently undercounted Hatom LSD by ~$1.18M in run #11 (SWTAO returned null due to rate-limit) and would have undercounted all 4 LSDs in run #12 if not caught by sanity check. **BILATERAL INVERSE RULE GUARDRAIL**: rule only applies for |Δprice|≥5%. Small moves (<3%) cannot test the rule - EGLD-denominated TVL noise dominates. This run's +1.4% / +0.9% does NOT count as observation #6. **DATA-QUALITY FIX**: run #11 watch_addresses contained an invalid-checksum bech32 address (erd1sdslv...29trp...76xc, HTTP 400). Canonical is erd1sdslv...3rgul...sets. Run #11 Binance.com entity undercounted by ~222K. Recommend pre-store bech32 validation. **REVISED PATTERN**: Run #11's 'synchronized LSD contraction' downgraded - Hatom LSD apples-to-apples (with SWTAO added back to prev) is FLAT, only XOXNO LSD contracting confirmed. **Capitulation prediction VALIDATED on price-up side, INVALIDATED on demand-up side**: the $2.95 bounce came as predicted but on collapsing engagement. The OTC pipeline entered an inter-cycle gap (-0.9K combined) - reload expected next 1-2 weeks per cycle pattern. |
