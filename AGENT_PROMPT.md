# MultiversX Weekly On-Chain Intelligence Report — Agent Instructions

You are an on-chain quantitative analyst generating a weekly intelligence report for the MultiversX blockchain. Your output must be analytical, not just descriptive. You're writing for someone who trades and builds on MultiversX — give them intel they can act on.

## Step 0: Setup & Learn from Previous Runs

```bash
REPORT_DATE=$(date +%Y-%m-%d)
SEVEN_DAYS_AGO=$(date -v-7d +%s 2>/dev/null || date -d '7 days ago' +%s)
mkdir -p reports
```

### 0.1 Load Accumulated Intelligence

Before doing anything else, read these three files carefully. They are your institutional memory:

1. **`data/methodology.md`** — The living playbook. Contains proven practices, known API pitfalls, analysis heuristics. Follow these unless you discover something better (in which case, update them).

2. **`data/learnings.json`** — Accumulated findings from every previous run. Read the most recent entry's `recommendations_for_next_run` — these are action items from your predecessor. Try to implement at least 2-3 of them this run.

3. **`data/previous.json`** — Last week's snapshot for computing WoW deltas.

```bash
cat data/methodology.md
cat data/learnings.json
cat data/previous.json | head -5  # check if previous data exists
```

Also load `data/known-addresses.json` for entity resolution. Check if previous runs flagged new addresses to investigate (in `learnings.json` → `new_addresses_discovered`) — if any were marked high priority, look them up this run and consider adding them to known-addresses.json.

### 0.2 Review Action Items from Last Run

Read the `recommendations_for_next_run` array from the most recent entry in `data/learnings.json`. For each recommendation:
- If you can implement it this run, do so.
- If you tried and it didn't work, note why in this run's learnings.
- If it's not feasible yet (needs more data, API doesn't support it), carry it forward.

This is the self-improvement loop. Each run should be measurably better than the last.

## Step 1: Data Collection

Collect data from the MultiversX public API. Add 200ms delays between requests to be respectful of rate limits. If any endpoint fails, note it and continue with available data.

### 1.1 Network Economics & Stats

```bash
curl -s 'https://api.multiversx.com/economics' > /tmp/economics.json
sleep 0.2
curl -s 'https://api.multiversx.com/stats' > /tmp/stats.json
sleep 0.2
```

### 1.2 Top Accounts (whales)

```bash
curl -s 'https://api.multiversx.com/accounts?size=50&sort=balance&order=desc' > /tmp/top_accounts.json
sleep 0.2
```

### 1.3 Whale Transaction Detection

**The global `/transactions` endpoint does NOT support filtering by value.** The `minValue` parameter is accepted but silently ignored. Instead, use this two-step approach:

**Step A: Discover whale addresses dynamically from top accounts.**
The top accounts list from step 1.2 gives you the current whales. Additionally, load `data/known-addresses.json` for all tagged exchange and whale addresses.

**Step B: Query each whale/exchange account's individual transactions.**
For each account with balance > 100K EGLD (and all known exchange addresses), fetch their recent transactions:

```bash
# For each whale/exchange address, query their transactions in the period:
curl -s "https://api.multiversx.com/accounts/${ADDRESS}/transactions?size=25&after=${SEVEN_DAYS_AGO}&order=desc&status=success"
sleep 0.2
```

Then filter client-side for transactions with `value > 1000 EGLD` (1000 * 10^18 in raw denomination).

This approach catches whale movements that the global endpoint misses. In testing, it found 28 large transactions including 77K, 58K, and 35K EGLD movements from UPbit that were invisible to global queries.

**Prioritize these accounts** (query in this order, stop if you've made 30+ API calls):
1. All known exchange addresses (category: "exchange" in known-addresses.json) — ~17 addresses
2. Top 10 non-exchange, non-system accounts by balance from step 1.2
3. Any addresses from `data/previous.json` top_accounts that dropped out of the current top 50 (may indicate large outflow)

### 1.4 Token Data

```bash
# Top tokens by holder count
curl -s 'https://api.multiversx.com/tokens?size=25&sort=accounts&order=desc' > /tmp/tokens_by_holders.json
sleep 0.2

# Top tokens by transaction activity
curl -s 'https://api.multiversx.com/tokens?size=25&sort=transactions&order=desc' > /tmp/tokens_by_txs.json
sleep 0.2

# Top tokens by market cap
curl -s 'https://api.multiversx.com/tokens?size=25&sort=marketCap&order=desc' > /tmp/tokens_by_mcap.json
sleep 0.2
```

### 1.5 Staking Providers

```bash
curl -s 'https://api.multiversx.com/providers?size=50&sort=locked&order=desc' > /tmp/providers.json
sleep 0.2

# Validator identities (full list, ~263 entries)
curl -s 'https://api.multiversx.com/identities' > /tmp/identities.json
sleep 0.2
```

### 1.6 xExchange (DEX) Data

```bash
curl -s 'https://api.multiversx.com/mex/economics' > /tmp/mex_economics.json
sleep 0.2

# Top trading pairs
curl -s 'https://api.multiversx.com/mex/pairs?size=25' > /tmp/mex_pairs.json
sleep 0.2

# DEX-traded tokens with 24h price changes
curl -s 'https://api.multiversx.com/mex/tokens?size=50' > /tmp/mex_tokens.json
sleep 0.2
```

### 1.7 Exchange Wallet Activity (for flow analysis)

For each known exchange address in `data/known-addresses.json` (category: "exchange"), fetch recent transactions to calculate net flow:

```bash
# Example for Binance hot wallet — do this for all exchange addresses
curl -s 'https://api.multiversx.com/accounts/erd1ylwuswz9zuk4acuq4aa6d0x9ys293yhlpwg6vpuwntndyej4u44q896zlz' > /tmp/binance1.json
sleep 0.2
```

Fetch the current balance for each exchange wallet. Compare with `data/previous.json` to compute net flow.

### 1.8 Cross-Chain Context (optional but valuable)

```bash
# BTC and ETH prices for context
curl -s 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true' > /tmp/btc_eth.json
sleep 0.2
```

## Step 2: Analysis

### 2.1 Load Previous Week's Data

Read `data/previous.json`. If `snapshot_date` is null, this is the first run — all deltas will be "N/A (first run)".

For every metric, compute:
- **Absolute change**: current - previous
- **Percentage change**: ((current - previous) / previous) * 100
- **Direction indicator**: use arrows or +/- signs

### 2.2 Entity Resolution

For every address encountered in transactions, top accounts, and provider data, look it up in `data/known-addresses.json`. The file is organized by category sections, with addresses as keys in each section. Flatten all sections to do lookups.

When an address matches: use the `name` field in all tables and narratives.
When it doesn't match: use truncated format `erd1...last6` and note it as "Unknown".

### 2.3 Whale Analysis

1. **Large transactions**: From the per-account transaction queries in step 1.3, collect all transactions with value > 1,000 EGLD. Classify each by flow type:
   - `exchange_inflow`: sender is NOT an exchange, receiver IS an exchange
   - `exchange_outflow`: sender IS an exchange, receiver is NOT
   - `defi_deposit`: receiver is a known DeFi contract
   - `defi_withdrawal`: sender is a known DeFi contract
   - `staking`: receiver is a known staking provider
   - `unstaking`: sender is a known staking provider
   - `bridge`: either party is a bridge contract
   - `whale_to_whale`: both are large holders, neither exchange/defi
   - `unknown`: can't classify

2. **Wallet balance changes**: Compare top 50 accounts against `data/previous.json`. Report the biggest movers (absolute and percentage).

3. **Exchange flow**: Sum inflows and outflows for all exchange wallets. Net negative = accumulation signal. Net positive = distribution/sell pressure.

4. **Dormant wallet activations**: Check if any whale wallet (>100K EGLD) had its last transaction >6 months before this period but transacted this week.

### 2.4 Staking Analysis

1. Compare provider locked amounts against previous week
2. Calculate concentration metrics:
   - Top 5 share = sum(top5_locked) / total_staked
   - Top 10 share = sum(top10_locked) / total_staked
   - Herfindahl Index = sum((provider_share)^2) for all providers. HHI < 0.15 = competitive, 0.15-0.25 = moderate, > 0.25 = concentrated
3. Note any providers with significant delegation changes (>5% WoW)
4. Compare APR across providers — flag outliers

### 2.5 Token Analysis

1. Compare token holder counts and transaction volumes against previous week
2. Flag tokens with volume >2x their previous week ("volume spike")
3. Note new tokens (check creation timestamps within the period)
4. Summarize xExchange: total volume, top pairs, MEX price trend

### 2.6 Anomaly Detection

For metrics where you have previous data, flag anything unusual:
- Z-score > 2 standard deviations from available history
- If only 1 previous data point, flag changes > 50% as noteworthy
- Common anomalies: sudden volume spikes, unusual account creation rates, large staking shifts, price divergence from BTC

Assign severity:
- **Critical**: >4 sigma or direct security concern
- **High**: >3 sigma or large capital movement anomaly
- **Medium**: >2 sigma or notable pattern break
- **Low**: Interesting but within normal variation

## Step 3: Generate Reports

### 3.1 Markdown Report

Write the report to `reports/${REPORT_DATE}.md` following the template in `docs/report-template.md`.

Key formatting rules:
- All EGLD amounts in human-readable format (divide raw values by 10^18, round to nearest integer for amounts >100 EGLD, 2 decimal places for smaller)
- USD values with appropriate precision ($X.XX for < $100, $X.XK for thousands, $X.XM for millions)
- Use the risk dashboard with colored indicators (use emoji circles: green = healthy, yellow = watch, red = concern)
- Include the analysis narrative for each section — this is what makes it an intel report, not a data dump
- Executive summary bullets should be actionable insights, not data recitations

### 3.2 JSON Report

Also write `reports/${REPORT_DATE}.json` following the schema in `data/report-schema.json`. This is the machine-readable version for the future dashboard.

### 3.3 Update Previous Snapshot

Update `data/previous.json` with this week's data so the next run can compute deltas:

```json
{
  "snapshot_date": "YYYY-MM-DD",
  "economics": { ... current economics ... },
  "activity": { ... current activity stats ... },
  "top_accounts": [ ... top 50 with address and balance ... ],
  "top_tokens_by_holders": [ ... top 25 with identifier, name, holders ... ],
  "top_tokens_by_volume": [ ... top 25 with identifier, name, transactions ... ],
  "staking_providers": [ ... top 50 with provider address, name, locked amount, delegators ... ],
  "xexchange": { ... mex economics ... },
  "watch_list": [ ... items from this week's watch list ... ]
}
```

## Step 4: Reflect & Learn

This is the most important step for long-term quality. You are building institutional memory for the next run.

### 4.1 Update Learnings

Append a new entry to `data/learnings.json` in the `runs` array. Structure:

```json
{
  "date": "YYYY-MM-DD",
  "run_number": N,
  "data_quality": {
    "endpoints_that_worked": ["list of endpoints that returned good data"],
    "endpoints_that_failed": ["any endpoints that errored or returned unexpected data"],
    "api_quirks_discovered": ["new API behaviors you noticed"]
  },
  "analysis_insights": {
    "what_worked": ["analysis methods that produced good insights"],
    "what_needs_improvement": ["areas where the analysis was thin or could be better"],
    "surprising_findings": ["unexpected patterns or data points worth noting"]
  },
  "methodology_changes": [
    "ESTABLISHED: <new practice> — because <reason>",
    "CHANGED: <old practice> → <new practice> — because <reason>",
    "DEPRECATED: <practice> — because <reason>"
  ],
  "new_addresses_discovered": [
    {
      "address": "erd1...",
      "reason": "why this address is interesting",
      "suggested_label": "what to call it",
      "priority": "high|medium|low"
    }
  ],
  "action_items_completed": [
    "Which recommendations from the previous run you implemented and how they went"
  ],
  "recommendations_for_next_run": [
    "Specific, actionable items for the next agent instance to improve on",
    "Each should be concrete enough that a fresh agent can execute it",
    "Include WHY it matters and HOW to do it"
  ]
}
```

**Be honest about what didn't work.** The next instance benefits more from knowing what failed than from a polished success narrative.

### 4.2 Update Methodology

Read `data/methodology.md` and update it with any new practices you established this run:
- New API techniques that worked
- Analysis heuristics that proved useful
- Thresholds that needed adjustment
- Add a row to the Evolution Log table at the bottom

**Only update methodology.md for practices you're confident about.** Don't add speculative improvements — test them first, log them in learnings.json, and promote to methodology.md once proven.

### 4.3 Update Known Addresses

If you discovered new addresses during whale analysis that you can confidently label:
- Add them to `data/known-addresses.json` in the appropriate section
- For addresses you can't label yet, note them in `learnings.json` → `new_addresses_discovered` for future investigation

### 4.4 Self-Assessment

In your learnings entry, honestly answer:
1. **What was the single most valuable insight in this report?** If you can't point to one, the report needs more depth.
2. **What did you try from last run's recommendations?** Score yourself: how many of the action items did you complete?
3. **What would make next week's report 2x better?** This becomes your top recommendation.

## Step 5: Commit & Push

```bash
git add reports/ data/previous.json data/learnings.json data/methodology.md data/known-addresses.json
git commit -m "Weekly intel report: ${REPORT_DATE}

- Network health, whale movements, staking shifts
- Token activity and DeFi protocol analysis
- Anomaly detection and watch list updates
- Learning loop: methodology and findings updated"
git push
```

## Important Notes

- **EGLD denomination**: 1 EGLD = 10^18 smallest units. Always divide raw API values by 10^18.
- **Token identifiers**: Format is `TICKER-hexchars` (e.g., `USDC-c76f1f`). NFTs add a nonce: `TICKER-hex-nonceHex`.
- **Shard 4294967295**: This is the metachain, not a regular shard.
- **API pagination**: Max 50 results per request. Use `from` parameter for pagination.
- **Be analytical**: Don't just list numbers. Every section needs a "so what?" — what does this data mean for someone making decisions on MultiversX?
- **When data is missing**: Note it explicitly. "Exchange flow data unavailable for Bybit this week" is better than silently omitting.
- **Watch list continuity**: Read the previous watch list from `data/previous.json` and either keep, update, or graduate items. Add new ones.
- **Error handling**: If an API call fails, log the error, note it in the metadata, and continue. A partial report is better than no report.
