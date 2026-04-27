# MultiversX Weekly Intelligence Report

**Period**: YYYY-MM-DD to YYYY-MM-DD
**Generated**: YYYY-MM-DD HH:MM UTC
**Run #**: N · **EGLD Price**: $X.XX (WoW: +X.X%) · **BTC**: $XXK · **ETH**: $X,XXX

---

## TL;DR

- Finding 1 (most significant)
- Finding 2
- Finding 3
- Finding 4
- Finding 5
- Finding 6
- Finding 7

---

## Risk Dashboard

```
METRIC                       VALUE          WoW CHANGE     SIGNAL
──────────────────────────────────────────────────────────────────
EGLD Price                   $X.XX          +X.X%          🟢
Staked Ratio                 XX.X%          +X.Xpp         🟢
Staking APR                  X.X%           -X.Xpp         🟡
Exchange Net Flow            +XX,XXX EGLD   ───            🔴 (sell pressure)
Active Accounts (7d)         XXX,XXX        +X.X%          🟢
TX Volume (7d)               X.XM           +X.X%          🟢
Top 5 Validator Share        XX.X%          +X.Xpp         🟢
Mega Whale Net Change        ±XXX,XXX EGLD  ───            🟡
Anomalies Detected           X (Z high)     ───            🟡
Trend Indicators Active      X              ───            🟢
──────────────────────────────────────────────────────────────────
🟢 = bullish/healthy   🟡 = neutral/watch   🔴 = bearish/concern
```

---

## 1. Network Health & Economics

| Metric | Value | WoW Change |
|--------|-------|------------|
| EGLD Price | $X.XX | +X.X% |
| Market Cap | $XXM | +X.X% |
| Total Supply | XX.XM EGLD | +X,XXX |
| Circulating Supply | XX.XM EGLD | +X,XXX |
| Staked EGLD | XX.XM | +X,XXX |
| Staked Ratio | XX.X% | +X.Xpp |
| Staking APR (avg) | X.X% | -X.Xpp |
| Base APR / TopUp APR | X.X% / X.X% | — |
| Total Accounts | X.XXM | +X,XXX |
| Total Transactions | XXXM | +X.XM |
| Avg Daily TX (7d) | XXX,XXX | +X.X% |
| Epoch | XXXX | +XX |

**Analysis**: [Narrative on staked ratio trajectory, APR compression dynamics, supply changes, account growth quality]

---

## 2. Whale Intelligence

### 2.1 Whale Tier Stratification

| Tier | Threshold | Wallets | Total Balance | WoW Change |
|------|-----------|---------|---------------|------------|
| Mega Whale | > 1M EGLD | N | XX.XM EGLD | ±XXX,XXX (±X.X%) |
| Large Whale | 100K — 1M | N | X.XM EGLD | ±XXX,XXX (±X.X%) |
| Mid Whale | 10K — 100K | N | X.XM EGLD | ±XXX,XXX (±X.X%) |

**Tier read**: [What does the directional movement of each tier mean? E.g., "mega whales contracting while mid whales expand → wealth distribution / OTC settlement"]

### 2.2 Large Transactions (>1,000 EGLD)

| Time | From | To | Amount | USD Value | Flow Type |
|------|------|----|--------|-----------|-----------|
| Mon 14:32 | Binance Hot 1 | erd1...abc | 25,000 EGLD | $100K | Exchange Outflow |
| Tue 09:15 | Unknown Whale | Hatom: EGLD MM | 10,000 EGLD | $40K | DeFi Deposit |

### 2.3 Top Wallet Balance Changes

| Tier | Wallet | Current | Previous | Δ EGLD | Δ % |
|------|--------|---------|----------|--------|-----|
| 🐳 Mega | Unknown Mega Whale | 991K | 192K | +799K | +414% |
| 🐳 Mega | UPbit | 1.30M | 1.43M | -139K | -9.7% |
| ⚓ Large | Bybit | 515K | 403K | +112K | +27.9% |

### 2.4 Exchange Flow Summary

#### Per-wallet Detail
| Exchange Wallet | Δ EGLD | Δ % |
|-----------------|--------|-----|
| Binance Hot 1 | -X,XXX | -X.X% |
| Binance Hot 2 | -X,XXX | -X.X% |
| ... | ... | ... |

#### Entity-Netted Flows (NEW)
| Entity | Net Flow | Wallets | Interpretation |
|--------|----------|---------|----------------|
| Binance | -50K EGLD | 4 | Mild distribution |
| Coinbase | -7K EGLD | 2 | Net-neutral OTC week |
| UPbit | -139K EGLD | 1 | OTC desk distribution phase |

**Net change across all exchanges**: ±XXX,XXX EGLD ([accumulation | distribution | neutral])

### 2.5 Dormant Wallet Activations

| Address | Label | Balance | Dormant Days | Action |
|---------|-------|---------|--------------|--------|
| erd1kn38... | Unknown Whale A | 143K EGLD | 287 | Liquidated 352K to Coinbase Apr 17-18 |

**Analysis**: [Smart money narrative — accumulation vs distribution signals, OTC desk patterns, tier-specific behavior, dormant reactivations]

---

## 3. Staking Power Map

### 3.1 Top 10 Providers

| Rank | Provider | Locked EGLD | Δ WoW | Delegators | APR | Fee | Nodes |
|------|----------|-------------|-------|------------|-----|-----|-------|
| 1 | Figment | 587,983 | +501 | 306 | 6.29% | 12% | 32 |
| 2 | Binance Staking | 524,344 | -1,477 | 8,479 | 6.14% | 7.9% | 28 |
| ... | ... | ... | ... | ... | ... | ... | ... |

### 3.2 Concentration

| Metric | Current | Previous | Trend |
|--------|---------|----------|-------|
| Top 5 Share | XX.X% | XX.X% | [improving/worsening] |
| Top 10 Share | XX.X% | XX.X% | — |
| HHI | 0.0XXX | 0.0XXX | [more/less decentralized] |
| HHI Interpretation | competitive_unconcentrated | — | — |

### 3.3 APR Distribution Histogram (NEW)

```
APR BUCKET     PROVIDERS      TOTAL LOCKED    SHARE
───────────────────────────────────────────────────
5-6%           N              X,XXX EGLD      X.X%
6-7%           N              X,XXX EGLD      X.X%
7-8%           N              X,XXX EGLD      X.X%
8-9%           N              X,XXX EGLD      X.X%
9-10%          N              X,XXX EGLD      X.X%
10%+           N              X,XXX EGLD      X.X%
───────────────────────────────────────────────────
```

**Read**: [Tight cluster vs wide spread interpretation]

### 3.4 APR Outliers (NEW)

#### Top 5 Highest APR
| Provider | APR | Fee | Locked |
|----------|-----|-----|--------|
| Maple Leaf | 9.28% | 0.0% | 12K EGLD |
| Incal | 8.58% | 1.0% | 224K EGLD |

#### Top 5 Lowest Fee
| Provider | Fee | APR | Locked |
|----------|-----|-----|--------|
| Maple Leaf | 0.0% | 9.28% | 12K EGLD |
| Incal | 1.0% | 8.58% | 224K EGLD |

**Best delegator value**: [provider with highest APR-after-fee, called out explicitly]

### 3.5 Churn Metric (NEW)

| Metric | Current | Previous | Change |
|--------|---------|----------|--------|
| Total Delegators | XXX,XXX | XXX,XXX | +X,XXX (+X.X%) |
| Providers Gaining | N | — | — |
| Providers Losing | N | — | — |

**Interpretation**: [Delegator growth + EGLD growth = healthy retail | Delegator drop + EGLD growth = whale consolidation | etc.]

**Analysis**: [Decentralization trajectory, delegation migration patterns, APR equilibrium dynamics]

---

## 4. Token & DeFi Activity

### 4.1 Top 10 Tokens by Holder Count

| Token | Holders | WoW Δ | Price | Market Cap |
|-------|---------|-------|-------|------------|
| WEGLD-bd4d79 | 134,289 | -26 | $4.03 | $2.2M |
| ... (10 rows) | ... | ... | ... | ... |

### 4.2 Top 10 Tokens by Volume

| Token | Transactions (24h) | WoW Δ% | Price |
|-------|--------------------|--------|-------|
| WEGLD-bd4d79 | XXX,XXX | +X.X% | $4.03 |
| ... (10 rows) | ... | ... | ... |

### 4.3 Top 5 Newly-Issued Tokens This Week

| Token | Name | Deployer | Holders | Transactions | Issued |
|-------|------|----------|---------|--------------|--------|
| NEWT-abc123 | NewToken | erd1...abc (label) | 234 | 89 | Apr 26 |
| ... | ... | ... | ... | ... | ... |

### 4.4 xExchange Summary

| Metric | Value | Δ |
|--------|-------|---|
| Active Pairs | XXX | — |
| 24h Volume | $XXX,XXX | +XX% WoW |
| MEX Price | $0.0000XXX | +X.X% WoW |
| MEX Market Cap | $X.XM | — |
| Top Pair | WEGLD/USDC: $XXK | XX.X% dominance |

**Analysis**: [Token holder trajectory, DEX health, newly-issued quality, sector rotation if any]

---

## 5. DeFi Per-Protocol Breakdown (NEW)

| Protocol | Category | TVL EGLD | TVL USD | WoW Δ% | 24h Transfers | Health |
|----------|----------|----------|---------|--------|---------------|--------|
| xExchange | DEX | XXX,XXX | $X.XM | +X.X% | XXX | 🟢 growing |
| Hatom Money Market | Lending | XX,XXX | $XXX,XXX | +X.X% | XX | 🟢 growing |
| Hatom Liquid Staking | Liquid Staking | XX,XXX | $XXX,XXX | -X.X% | XXX | 🟡 flat |
| AshSwap | DEX (stableswap) | XX,XXX | $XXX,XXX | ±X.X% | XX | 🟡 flat |
| OneDex | Aggregator | XX,XXX | $XXX,XXX | ±X.X% | XX | 🟡 flat |
| XOXNO | NFT Marketplace | — | — | — | XXX | 🟢 active |
| JEXchange | DEX (orderbook) | X,XXX | $XX,XXX | ±X.X% | X | 🟡 flat |

**Analysis**: [Per-protocol commentary — which sectors are gaining vs losing, capital rotation, notable events]

### 5.1 New Smart Contract Deployments

_X new contracts deployed this week. Y received >100 interactions._

---

## 6. Anomalies & Trend Indicators

### 6.1 Anomaly Alerts

| Severity | Method | Metric | Current | Baseline | Z-Score / Δ% | Description |
|----------|--------|--------|---------|----------|--------------|-------------|
| HIGH | z_score | DEX Volume | $186K | $109K | +1.6σ | 4-week baseline mean exceeded |
| MEDIUM | rule_based | Whale A | 143K EGLD | 495K | -71% | Reactivated after 4 weeks dormant |
| LOW | percent_threshold | New Token X holders | 50 | 5 | +900% | Degraded mode (N=2 only) |

### 6.2 Trend Indicators (NEW)

#### Accelerating Exchange Outflows
| Exchange | Trend | Cumulative Δ% | Weeks | Interpretation |
|----------|-------|----------------|-------|----------------|
| Gate.io | 4 consecutive weeks of decline | -54% | 4 | Customer exit or treasury rebalance |

#### Validator Movements
| Type | Count | Notable |
|------|-------|---------|
| Joining | N | [list with locked amounts] |
| Leaving | N | [list with previous locked] |
| Net change | ±N | — |

#### Token Supply Events
| Token | Event | Magnitude | Description |
|-------|-------|-----------|-------------|
| TOKEN-abc | Mint | +5% | Treasury issuance |
| WTAO | Burn | -2% | Reverse-bridge to Bittensor |

#### Consecutive Streaks
| Metric | Direction | Weeks | Cumulative | Interpretation |
|--------|-----------|-------|------------|----------------|
| EGLD price | up | 3 | +12% | Momentum regime |
| WTAO holders | down | 5 | -2.4% | Bridge interest fading |

#### Regime Shifts
| Metric | Before | After | Description |
|--------|--------|-------|-------------|
| DEX 7d avg volume | $80K | $180K | Step change persisting 2+ weeks |

---

## 7. Watch List

| Item | Reason | Weeks Tracked |
|------|--------|---------------|
| Unknown Mega Whale erd18mv2... | 991K EGLD parked since Apr 18, no movement | 2 |
| UPbit OTC Desk Cycle 2 | Distribution ongoing, ~30% complete | 5 |
| Gate.io declining streak | -54% over 4 weeks, breakdown threshold approaching | 4 |

---

## 8. Methodology Footer

- Z-score baselines: N=X data points across [list of metrics]
- Action items completed from previous run: X / Y
- New addresses flagged for investigation: N
- Methodology changes this run: [bullet list, brief]

---

*Report generated by [onchain-quant-agent](https://github.com/lamentierschweinchen/onchain-quant-agent) — schema v2*
