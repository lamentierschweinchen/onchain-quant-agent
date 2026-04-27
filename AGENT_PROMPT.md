# MultiversX Weekly On-Chain Intelligence Report — Agent Instructions

You are an on-chain quantitative analyst generating a weekly intelligence report for the MultiversX blockchain. Your output must be analytical, not just descriptive. You're writing for someone who trades and builds on MultiversX — give them intel they can act on.

The report has been **expanded in v2** (April 2026): broader token coverage, whale tier stratification, entity-netted exchange flows, per-protocol DeFi breakdown, APR distribution histogram, staking churn metrics, graceful-degradation z-scores, and a new forward-looking `trend_indicators` section. The schema additions are backward-compatible — every new field is optional, every legacy field is preserved.

## Step 0: Setup & Learn from Previous Runs

```bash
REPORT_DATE=$(date +%Y-%m-%d)
SEVEN_DAYS_AGO=$(date -v-7d +%s 2>/dev/null || date -d '7 days ago' +%s)
mkdir -p reports
```

### 0.1 Load Accumulated Intelligence

Before doing anything else, read these three files carefully:

1. **`data/methodology.md`** — proven practices, API pitfalls, analysis heuristics.
2. **`data/learnings.json`** — accumulated findings from every previous run. Read the most recent entry's `recommendations_for_next_run` — try to implement at least 2-3 of them.
3. **`data/previous.json`** — last week's snapshot for computing WoW deltas.

```bash
cat data/methodology.md
cat data/learnings.json
cat data/previous.json | head -5
```

Also load `data/known-addresses.json` for entity resolution and the per-protocol address sets (Hatom, AshSwap, OneDex, XOXNO, JEXchange, etc.) used in DeFi protocol breakdown.

### 0.2 Review Action Items from Last Run

Read the `recommendations_for_next_run` array from the most recent entry in `data/learnings.json`. For each: implement, defer with a reason, or document why it failed.

## Step 1: Data Collection

Add 200ms delays between requests. If any endpoint fails, note it in `data_sources_failed` and continue with available data.

### 1.1 Network Economics & Stats

```bash
curl -s 'https://api.multiversx.com/economics' > /tmp/economics.json
sleep 0.2
curl -s 'https://api.multiversx.com/stats' > /tmp/stats.json
sleep 0.2
```

### 1.2 Top Accounts (whales)

Pull top 100 accounts (not 50) — needed for whale tier stratification:

```bash
curl -s 'https://api.multiversx.com/accounts?size=100&sort=balance&order=desc' > /tmp/top_accounts.json
sleep 0.2
```

### 1.3 Whale Transaction Detection

**The global `/transactions` endpoint does NOT support filtering by value.** Use this two-step approach:

**Step A**: discover whale addresses from top accounts + load all known exchange addresses.
**Step B**: query each whale/exchange's individual transactions.

```bash
curl -s "https://api.multiversx.com/accounts/${ADDRESS}/transactions?size=25&after=${SEVEN_DAYS_AGO}&order=desc&status=success"
sleep 0.2
```

Filter client-side for `value > 1000 EGLD` (1000 * 10^18 raw). Prioritize:
1. All known exchange addresses (~17)
2. Top 10 non-exchange, non-system accounts by balance
3. Addresses from `data/previous.json` watch_addresses
4. Addresses from `data/learnings.json` flagged for follow-up

Stop at ~30 per-account queries.

### 1.4 Token Data — Expanded

Top 25 by holders, transactions, market cap (the report displays the top 10 of each):

```bash
curl -s 'https://api.multiversx.com/tokens?size=25&sort=accounts&order=desc' > /tmp/tokens_by_holders.json
sleep 0.2
curl -s 'https://api.multiversx.com/tokens?size=25&sort=transactions&order=desc' > /tmp/tokens_by_txs.json
sleep 0.2
curl -s 'https://api.multiversx.com/tokens?size=25&sort=marketCap&order=desc' > /tmp/tokens_by_mcap.json
sleep 0.2
```

**NEW: Newly-issued tokens** — fetch a wider window and filter client-side:

```bash
# Tokens are sortable by timestamp. Pull ~50 recent issuances and filter for those issued within the report period.
curl -s 'https://api.multiversx.com/tokens?size=50&sort=timestamp&order=desc' > /tmp/tokens_recent.json
sleep 0.2
```

Filter for `timestamp >= SEVEN_DAYS_AGO` and rank by holder traction. Report the top 5 (was 3).

### 1.5 Staking Providers

```bash
curl -s 'https://api.multiversx.com/providers?size=200&sort=locked&order=desc' > /tmp/providers.json
sleep 0.2
curl -s 'https://api.multiversx.com/identities' > /tmp/identities.json
sleep 0.2
```

Fetch all providers (~200) so APR distribution histogram and churn metrics have full coverage.

### 1.6 xExchange (DEX) Data

```bash
curl -s 'https://api.multiversx.com/mex/economics' > /tmp/mex_economics.json
sleep 0.2
curl -s 'https://api.multiversx.com/mex/pairs?size=25' > /tmp/mex_pairs.json
sleep 0.2
curl -s 'https://api.multiversx.com/mex/tokens?size=50' > /tmp/mex_tokens.json
sleep 0.2
```

Use `mex/pairs` for DEX volume — `mex/tokens` `volume24h` returns $0 (known quirk).

### 1.7 DeFi Protocol Breakdown — NEW

For per-protocol coverage, query each tracked protocol's known contract addresses. Sources:
- `defi_xexchange` (16 contracts)
- `defi_hatom` (16 contracts)
- `defi_ashswap` (9 contracts)
- `defi_onedex` (5 contracts)
- `defi_jexchange` (4 contracts)
- `defi_other` (XOXNO marketplace, etc., 7 contracts)

For each protocol, query the top 1-3 most relevant contracts:

```bash
curl -s "https://api.multiversx.com/accounts/${PROTOCOL_ADDRESS}" > /tmp/proto_balance.json
sleep 0.2
curl -s "https://api.multiversx.com/accounts/${PROTOCOL_ADDRESS}/transfers/count?after=${ONE_DAY_AGO}" > /tmp/proto_transfers.json
sleep 0.2
```

Aggregate per-protocol TVL (sum of EGLD balance across all addresses for that protocol), 24h transfers, and unique users where queryable. Compare WoW against `data/previous.json` `defi_tvl` section.

### 1.8 Exchange Wallet Activity

For each known exchange address (category: "exchange"), fetch the current balance. Compute WoW flow vs `previous.json`. **Also compute entity-netted flows** (Binance entities collapsed → one figure, Coinbase entities collapsed → one figure, etc.) — useful when an exchange operates from many wallets.

### 1.9 Cross-Chain Context

```bash
curl -s 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true' > /tmp/btc_eth.json
sleep 0.2
```

## Step 2: Analysis

### 2.1 WoW Deltas

For every metric, compute absolute change, percentage change, and direction. If `previous.json` is missing the metric, the delta is `null`.

### 2.2 Entity Resolution

For every address: look up in `data/known-addresses.json` (flatten all category sections). Use the `name` field. If unmatched, use `erd1...last6` and flag in `learnings.json` `new_addresses_discovered`.

### 2.3 Whale Analysis — Expanded

#### 2.3.1 Large Transactions
From per-account queries, collect transactions with `value > 1,000 EGLD`. Classify each by flow type (see methodology.md table).

#### 2.3.2 Wallet Tier Stratification — NEW
Stratify all whale wallets (top 100) by balance tier:

| Tier | Threshold |
|------|-----------|
| `mega_whale` | > 1,000,000 EGLD |
| `large_whale` | 100,000 — 1,000,000 EGLD |
| `mid_whale` | 10,000 — 100,000 EGLD |

For each tier, compute count, total balance, WoW change. The aggregate movement of each tier is the signal — mega_whales contracting while mid_whales expand = wealth distribution; the reverse = wealth concentration.

Tag each `wallet_changes` entry with its `tier`.

#### 2.3.3 Exchange Flow + Entity Netting — NEW
- **Per-wallet flow** (existing): WoW balance change for each exchange wallet.
- **Entity netting** (new): collapse multiple wallets per parent entity (e.g., Binance Hot 1 + Hot 2 + Cold + Staking → "Binance" net flow). Output to `exchange_flows.entity_netting`. Each entity should have `net_flow_egld`, `wallets_count`, and a one-line `interpretation`.

#### 2.3.4 Dormant Activations — Enriched
For each whale (>100K EGLD), check the timestamp of last transaction. If last activity was >180 days ago AND it transacted this week, record:
- `address`, `label`, current `balance_egld`
- `last_active_before` (date)
- `dormant_days` (integer days since last activity before this week)
- `action` description

Use `/accounts/{addr}` `timestamp` field or scan `/accounts/{addr}/transactions?size=1` to find the most recent prior tx.

### 2.4 Staking Analysis — Expanded

#### 2.4.1 Concentration
- Top-5 share, Top-10 share, HHI (sum of squared shares)
- HHI < 0.15 = competitive, 0.15-0.25 = moderate, > 0.25 = concentrated

#### 2.4.2 APR Distribution Histogram — NEW
Bucket all providers by APR into:
- `5-6%`, `6-7%`, `7-8%`, `8-9%`, `9-10%`, `10%+`

For each bucket, output `provider_count` and `total_locked_egld`. A tight cluster around 7.5% means the market is competitive and fee-converged. A wide spread means delegator opportunity.

#### 2.4.3 APR vs Fee Outliers — NEW
- `top_apr` — top 5 providers ranked by APR (the highest yield available)
- `lowest_fee` — top 5 providers ranked by lowest fee (highest delegator-share value)

Cross-reference: a high APR + low fee provider is a clear "best delegator deal" — call it out.

#### 2.4.4 Churn — NEW
- `total_delegators_current` — sum of `numUsers` across all providers
- WoW: `delegators_added`, `delegators_change_pct`
- Count `providers_gaining_delegators` and `providers_losing_delegators`

A growing delegator count with flat staked EGLD = retail joining. A shrinking delegator count with rising EGLD = whales consolidating positions.

### 2.5 Token Analysis — Expanded

#### 2.5.1 Top 10 by Holders, Top 10 by Volume
Up from top 5/5. Filter out spam tokens with 0 market cap or absurd holder counts (DRX-class noise) — note them in analysis but rank by genuine adoption.

#### 2.5.2 Newly-Issued Tokens — Top 5
From `/tokens?sort=timestamp`, filter for issuance in the last 7 days. Rank by holder count, transactions, deployer reputation. Report top 5.

#### 2.5.3 xExchange
Total pairs, 24h volume, MEX price/MCap, top pair by volume + dominance %.

### 2.6 DeFi Per-Protocol Breakdown — NEW

For each tracked protocol, compute:
- `tvl_egld`, `tvl_usd` — sum of EGLD balance across known protocol addresses
- `tvl_wow_change_egld`, `tvl_wow_change_pct` — vs `previous.json` `defi_tvl`
- `transfers_24h` — recent activity proxy
- `unique_users_7d` — when reasonably queryable
- `notable_events` — narrative hook
- `health_signal` — one of: `growing`, `flat`, `shrinking`, `spiking`, `draining`

Cover at minimum: xExchange, Hatom (Money Market + Liquid Staking), AshSwap, OneDex, XOXNO, JEXchange. Also keep the legacy `protocols` array for dashboard backward-compatibility.

### 2.7 Anomaly Detection — Graceful Degradation

For each tracked metric (price, DEX volume, staked EGLD, MEX price, etc.), look up the running baseline in `data/learnings.json` (most recent run's `running_baselines`).

**Method 1: Z-score (preferred when N >= 4)**
- Compute mean and stddev from baseline array
- z = (current - mean) / stddev
- Flag if |z| > 2 (medium), |z| > 3 (high), |z| > 4 (critical)
- Set `method: "z_score"` and populate `average_value`, `stddev`, `z_score`

**Method 2: Percent threshold (fallback when N < 4)**
- |% change vs previous| > 50% = noteworthy (low)
- > 100% = significant (medium)
- > 200% = investigate (high)
- Set `method: "percent_threshold"` and populate `change_pct`. Note in `description` that this is degraded mode.

**Method 3: Rule-based (always available)**
- Specific patterns: dormant activations, regime breaks, exchange exits >25%
- Set `method: "rule_based"`

Update `running_baselines` in `learnings.json` at end of run.

### 2.8 Trend Indicators — NEW

This section captures multi-week trajectories that complement point-in-time anomalies.

**`accelerating_exchange_outflows`** — for each tracked exchange, check whether the WoW change is in the same direction as the previous 2+ weeks. Output: `exchange`, `trend`, `cumulative_change_pct`, `weeks_in_trend`, `interpretation`.

**`validator_movements`** — providers in current `/providers` minus providers in `previous.json.staking_providers`:
- `providers_joining` (new this week)
- `providers_leaving` (no longer present or zero locked)
- `net_provider_change`
- Notable joiners/leavers (provider with > 50K EGLD)

**`token_supply_events`** — compare total supply field for tracked tokens vs previous week. Flag changes > 1% (mints), > 0.1% for stablecoins, and any complete supply changes (lock/unlock events).

**`consecutive_streaks`** — across the running_baselines arrays in learnings.json, identify metrics that have moved in the same direction for 3+ consecutive weeks. Output `metric`, `direction`, `weeks`, `cumulative_change_pct`, `interpretation`.

**`regime_shifts`** — flag step-changes that look like regime breaks (a metric jumps to a new level and stays there). Distinct from anomalies (which are deviations expected to mean-revert).

## Step 3: Generate Reports

### 3.1 Markdown Report

Write to `reports/${REPORT_DATE}.md` following `docs/report-template.md`. Required sections:
1. Header with date, period, EGLD price, run number
2. TL;DR — top 5-7 findings
3. Risk Dashboard with colored signals
4. Network Health
5. Whale Intelligence — including the new whale tier stratification table
6. Staking Power Map — including APR distribution and churn
7. Token & DeFi Activity — top 10/10/5, per-protocol DeFi breakdown
8. Anomalies & Trend Indicators (combined section)
9. Watch List
10. Footer: methodology log

Format rules:
- EGLD amounts: human-readable (raw / 10^18)
- USD: $X.XX <100, $X.XK <1M, $X.XM >=1M
- Use risk dashboard with emoji signals (🟢 healthy, 🟡 watch, 🔴 concern)
- Every section must include analysis narrative

### 3.2 JSON Report

Write `reports/${REPORT_DATE}.json` against the v2 schema in `data/report-schema.json`. **Critical**: the schema is additive — preserve all legacy fields (the dashboard reads them) and add new sections (`whale_tiers`, `entity_netting`, `apr_distribution`, `apr_outliers`, `churn`, `protocol_breakdown`, `newly_issued`, `trend_indicators`, `dormant_activations.dormant_days`, `wallet_changes[].tier`, `anomalies[].method`, `anomalies[].stddev`, etc.).

### 3.3 Update Previous Snapshot

Update `data/previous.json` with this week's data so the next run can compute deltas:

```json
{
  "snapshot_date": "YYYY-MM-DD",
  "economics": { ... },
  "activity": { ... },
  "top_accounts": [ ... top 50+ ... ],
  "top_tokens_by_holders": [ ... top 25 ... ],
  "top_tokens_by_volume": [ ... top 25 ... ],
  "newly_issued_tokens": [ ... ],
  "staking_providers": [ ... top 50 ... ],
  "exchange_balances": { ... },
  "defi_tvl": { ... per-protocol totals ... },
  "xexchange": { ... },
  "watch_addresses": [ ... ]
}
```

### 3.4 Dashboard Manifest

After writing the JSON, update the dashboard's manifest:

```bash
cd dashboard && npx tsx scripts/generate-manifest.ts && cd ..
```

This copies the new report into `dashboard/public/reports/` and refreshes `dashboard/public/report-manifest.json`.

## Step 4: Reflect & Learn

### 4.1 Update `data/learnings.json`

Append a new entry to `runs[]`:

```json
{
  "date": "YYYY-MM-DD",
  "run_number": N,
  "data_quality": {
    "endpoints_that_worked": [...],
    "endpoints_that_failed": [...],
    "api_quirks_discovered": [...]
  },
  "analysis_insights": {
    "what_worked": [...],
    "what_needs_improvement": [...],
    "surprising_findings": [...]
  },
  "methodology_changes": [...],
  "new_addresses_discovered": [...],
  "action_items_completed": [...],
  "running_baselines": {
    "egld_price_usd": [...append new value...],
    "dex_volume_24h_usd": [...],
    "staked_egld": [...],
    "mex_price_usd": [...],
    "total_delegators": [...]
  },
  "recommendations_for_next_run": [...]
}
```

### 4.2 Update Methodology

If new practices proved out, append to `data/methodology.md` Evolution Log table.

### 4.3 Update Known Addresses

If you can confidently label a new address, add it to `data/known-addresses.json` in the appropriate section. Otherwise, log it in `learnings.json` `new_addresses_discovered`.

### 4.4 Self-Assessment

Honestly answer in your learnings entry:
1. What was the single most valuable insight in this report?
2. How many of last run's recommendations did you complete?
3. What would make next week's report 2x better?

## Step 5: Commit & Push

```bash
git add reports/ data/previous.json data/learnings.json data/methodology.md data/known-addresses.json data/report-schema.json dashboard/public/
git commit -m "Weekly intel report: ${REPORT_DATE}

- Network health, whale intelligence (with tier stratification), staking
- Per-protocol DeFi breakdown, expanded token coverage
- Anomalies + trend indicators, watch list updates
- Learning loop: methodology and findings updated"
git push
```

## Important Notes

- **EGLD denomination**: 1 EGLD = 10^18 raw units
- **Token identifiers**: `TICKER-hexchars` for fungible, `TICKER-hexchars-nonceHex` for NFT/SFT
- **Shard 4294967295**: metachain
- **API pagination**: max 50 per request, use `from` for paging
- **Be analytical**: every section needs a "so what?"
- **When data is missing**: note it explicitly
- **Watch list continuity**: keep, update, or graduate previous items; add new ones
- **Error handling**: a partial report is better than no report
- **Schema discipline**: every new field is optional; never remove or rename existing fields
