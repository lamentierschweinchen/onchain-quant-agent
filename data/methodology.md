# Analysis Methodology — Living Document

**Last updated**: 2026-04-02 (run #1)
**Status**: This document is read and updated by the agent on every run. It contains proven practices, known pitfalls, and evolving heuristics.

---

## Core Principles

1. **Every metric needs a "so what?"** — Data without interpretation is a spreadsheet, not intelligence. Always explain what a number means for someone making decisions on MultiversX.
2. **Deltas matter more than absolutes** — "Staked ratio is 48.1%" is a fact. "Staked ratio rose 0.3pp this week, continuing a 4-week trend of increasing lockup" is intelligence.
3. **Name everything** — Addresses are meaningless to readers. Always resolve via known-addresses.json. If you can't label it, note it for investigation.
4. **Flag what you can't see** — Missing data is itself a signal. If an endpoint fails or returns unexpected results, say so explicitly.

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
1. Check the recipient's **nonce** — low nonce (< 10) = purpose-built routing wallet
2. Fetch their **recent transactions** to see if they immediately forwarded the funds
3. Check **current balance** — near-zero balance after a large receipt = confirmed routing wallet
4. This pattern correctly identified Binance's 470K EGLD restaking as internal vs. a withdrawal

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

---

## Anomaly Detection

### Z-Score Method
- Requires 4+ weeks of historical data to be meaningful
- Threshold: flag anything > 2 standard deviations
- For first 4 weeks, use simple % change thresholds instead:
  - >50% change = noteworthy
  - >100% change = significant
  - >200% change = investigate immediately

### Common False Positives to Filter
- Epoch transitions can cause temporary metric spikes
- Token listing/delisting on xExchange creates volume anomalies
- Weekend/holiday activity dips are not anomalies

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
