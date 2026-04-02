# MultiversX Intelligence Dashboard — Design Spec

## Context

The `onchain-quant-agent` generates weekly MultiversX blockchain intelligence reports as structured JSON (`reports/YYYY-MM-DD.json`). There is currently no way to view these reports except reading raw JSON or markdown. This dashboard provides a visual interface for scanning weekly developments — data-backed, linked to sources, designed for a single analyst reviewing the weekly output.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Location | `dashboard/` subdirectory | Reports in `../reports/` accessible directly; single repo to push |
| Architecture | Single-page scrollable | Weekly briefing read top-to-bottom; no tab-switching friction |
| Stack | React 18 + TypeScript + Vite + Tailwind v4 + Nivo | Nivo has dark theme defaults and treemap for v2 |
| Deployment | Local-first (`pnpm dev`) | Personal tool; deploy-ready structure for later |
| Scope | All 8 report sections; defer sparklines, Sankey, treemap, search, export | v1 = complete data display; fancy viz needs multiple weeks of data |

## Data Loading

A prebuild script scans `../reports/*.json` and writes `public/report-manifest.json`:

```json
[{ "date": "2026-04-02", "file": "2026-04-02.json" }]
```

At runtime, `useReports()` fetches the manifest, defaults to the latest date, then fetches the selected report via `fetch(/reports/${date}.json)`. Report JSON files are copied to `public/reports/` by the prebuild script.

The Vite dev server proxies `../reports/` so files stay in sync during development without manual copying.

## Project Structure

```
dashboard/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
├── scripts/
│   └── generate-manifest.ts    # Scans ../reports/*.json → public/report-manifest.json + copies files
├── src/
│   ├── main.tsx
│   ├── App.tsx                 # Report loader → section layout
│   ├── types/
│   │   └── report.ts          # TypeScript interfaces matching report-schema.json
│   ├── hooks/
│   │   ├── useReports.ts      # Load manifest, fetch selected report
│   │   └── useFormatters.ts   # Formatting hooks
│   ├── components/
│   │   ├── Header.tsx
│   │   ├── SectionNav.tsx
│   │   ├── ExecutiveSummary.tsx
│   │   ├── NetworkHealth.tsx
│   │   ├── WhaleIntelligence.tsx
│   │   ├── StakingIntelligence.tsx
│   │   ├── TokenDefi.tsx
│   │   ├── AnomaliesWatchList.tsx
│   │   ├── MetaLearning.tsx
│   │   └── ui/
│   │       ├── MetricCard.tsx
│   │       ├── SeverityBadge.tsx
│   │       ├── DataTable.tsx
│   │       ├── AddressLink.tsx
│   │       ├── AnalysisBlock.tsx
│   │       └── NullState.tsx
│   ├── lib/
│   │   ├── formatters.ts
│   │   └── constants.ts
│   └── styles/
│       └── index.css
└── public/
    └── reports/                # Populated by prebuild script
```

## TypeScript Types

Generated from `data/report-schema.json`. Top-level interface:

```typescript
interface WeeklyReport {
  metadata: ReportMetadata;
  executive_summary: Finding[];
  network_health: NetworkHealth;
  whale_intelligence: WhaleIntelligence;
  staking_intelligence: StakingIntelligence;
  token_activity: TokenActivity;
  defi_activity: DefiActivity;
  anomalies: Anomaly[];
  watch_list: WatchItem[];
  meta_learning?: MetaLearning;
}
```

All WoW delta fields are typed as `number | null`. Formatters handle null with "Baseline" / "—" display.

## Application States

- **Loading**: Centered spinner while manifest or report JSON is being fetched
- **Error**: "Failed to load report" message with retry button if fetch fails or JSON is malformed
- **Missing report**: If a manifest entry points to a missing file, show error and fall back to next available report
- **Empty sections**: Each section handles its own empty/null state gracefully (see component specs)

## Component Specifications

### Header (sticky)

- **Left**: "MultiversX Intelligence" + report date dropdown (from manifest)
- **Center**: EGLD price from `metadata.egld_price_usd` with delta arrow from `network_health.deltas.price_change_pct`
- **Right**: Data source health dots (green for `data_sources_ok`, red for `data_sources_failed`) + generated timestamp
- **Sub-header**: Report period from `metadata.period_start` to `metadata.period_end`

### SectionNav (floating, right side)

Compact vertical dot-nav or pill-nav for jumping to sections. Highlights current section on scroll via IntersectionObserver.

### ExecutiveSummary

Horizontal card row from `executive_summary[]` (3-7 items). Each card:
- Colored left border by severity
- Category badge (top-right)
- Finding text
- Critical/high findings get subtle glow

### NetworkHealth

**Metrics grid (3x2):**

| Metric | Source | Format |
|--------|--------|--------|
| EGLD Price | `economics.egld_price_usd` | `$3.68` |
| Market Cap | `economics.market_cap_usd` | `$109.1M` |
| Staked Ratio | `economics.staked_ratio` | `48.1%` + Nivo pie |
| Staking APR | `economics.staking_apr` | `8.9%` |
| Total Accounts | `activity.total_accounts` | `9.18M` |
| Total Transactions | `activity.total_transactions` | `596.2M` |

**Secondary info** (smaller text below the grid): Total Supply (`economics.total_supply`), Circulating Supply (`economics.circulating_supply`), Staked EGLD (`economics.staked_egld`), Token Market Cap (`economics.token_market_cap_usd`), Epoch (`activity.epoch`), Shards (`activity.shards`).

Each MetricCard shows delta from `network_health.deltas.*` — green up-arrow, red down-arrow, gray "Baseline" for null.

**Staked ratio donut**: Nivo `ResponsivePie` — two slices: `staked_ratio` (cyan) and `1 - staked_ratio` (muted). Absolute values (`staked_egld` and `total_supply - staked_egld`) shown in tooltip.

**AnalysisBlock** with `network_health.analysis`.

### WhaleIntelligence

**Exchange Flows** (top of section):
- Net flow indicator — big directional arrow with EGLD amount
- Nivo `ResponsiveBar` chart of `exchange_flows.by_exchange[]` — green bars for outflow (accumulation), red for inflow (sell pressure)
- All null in baseline → show "Baseline — exchange flow tracking starts next week"

**Wallet Changes Table**:
- Columns: Address (AddressLink), Label, Category (badge), Balance (EGLD formatted), Change, Change%
- Sortable by any column. Default sort: balance descending.
- Row tint by category: exchange=blue, defi=purple, team=green, system=gray

**Large Transactions Table**:
- Columns: Time, From→To (AddressLinks), Value EGLD, Value USD, Flow Type (badge)
- Tx hash linked to explorer
- Empty state: "No large transactions detected this period"

**Dormant Activations**:
- Alert-style cards when present
- Empty state: "No dormant wallets activated"

**AnalysisBlock** with `whale_intelligence.analysis`.

### StakingIntelligence

**Provider Leaderboard**:
- DataTable: Rank, Name, Locked EGLD, Change, Delegators, APR%, Fee%, Nodes
- Default sort: locked descending
- Highlight rows where APR > 8.5% with fee < 5% (good deals)

**Concentration Metrics**:
- Two horizontal progress bars: top-5 share (19.3%), top-10 share (30.1%)
- HHI with interpretation badge: <0.15 green "Competitive", 0.15-0.25 yellow "Moderate", >0.25 red "Concentrated"
- Show `previous_herfindahl` trend arrow when non-null

**Provider Distribution Chart**:
- Nivo `ResponsiveBar` (horizontal) — top 15 providers by locked EGLD

**AnalysisBlock** with `staking_intelligence.analysis`.

### TokenDefi

**Top Tokens by Holders**: DataTable — Token, Name, Holders, Price, Market Cap. Flag spam (holders >> market cap).

**Top Tokens by Volume**: DataTable — Token, Name, Transactions, Change%, Price.

**New Tokens**: List from `token_activity.new_tokens[]`. Empty state: "No new tokens this period."

**xExchange Summary**:
- 4 MetricCards: total pairs (`xexchange_summary.total_pairs`), 24h volume (`xexchange_summary.total_volume_24h_usd`), MEX price (`xexchange_summary.mex_price_usd`), MEX market cap (`xexchange_summary.mex_market_cap_usd`)
- Nivo `ResponsiveBar` — top 5 pairs by volume from `xexchange_summary.top_pairs_by_volume[]`

**SC Deployments**: List from `defi_activity.sc_deployments[]`. Empty state: "No new smart contracts deployed."

**DeFi Protocols**: Card per `defi_activity.protocol_activity[]` — name, category badge, notable events text.

**AnalysisBlocks** for both `token_activity.analysis` and `defi_activity.analysis`.

### AnomaliesWatchList

**Anomalies**: Cards sorted by severity. Each: metric name bold, current value, severity badge, description. Z-score and average shown when non-null.

**Watch List**: Ordered list with `weeks_on_list` counter badge. Item text + reason. Clean tracker aesthetic.

### MetaLearning (collapsible)

Collapsed by default. Entire section hidden if `meta_learning` is absent from the report (it's optional — the baseline report omits it).

When present, shows: run number, most valuable insight, methodology changes, action items completed (fraction), new addresses discovered, top recommendation.

## Shared UI Primitives

| Component | Props | Behavior |
|-----------|-------|----------|
| `MetricCard` | `label`, `value`, `delta`, `format` | Big number, label below, delta badge. Null delta → "Baseline" |
| `SeverityBadge` | `severity` | Colored pill: critical=red, high=orange, medium=yellow, low=blue, info=gray. Note: anomalies use 4 levels (no `info`); executive summary uses all 5. |
| `DataTable` | `columns`, `data`, `defaultSort` | Click header to sort. Custom cell renderers for badges/links |
| `AddressLink` | `address`, `label?` | Truncated display, copy button, links to explorer |
| `AnalysisBlock` | `text` | Styled block with left accent border. Bloomberg-note feel |
| `NullState` | `message?` | Renders "—" or custom message in muted text |

## Color System

```
Background:      #0F1219
Surface:         #1A1F2E
Surface hover:   #242B3D
Border:          #2A3144
Text primary:    #E2E8F0
Text secondary:  #94A3B8
Accent cyan:     #23F7DD (MultiversX primary)
Accent blue:     #1B46C2 (MultiversX secondary)

Severity:
  critical:      #EF4444
  high:          #F97316
  medium:        #EAB308
  low:           #3B82F6
  info:          #6B7280
```

## Source Links

Every address and transaction hash links to MultiversX Explorer:
- Accounts: `https://explorer.multiversx.com/accounts/{address}`
- Transactions: `https://explorer.multiversx.com/transactions/{hash}`

## Key Files to Reference During Implementation

| File | Purpose |
|------|---------|
| `reports/2026-04-02.json` | Real data to build against (27KB) |
| `data/report-schema.json` | Schema for generating TypeScript types |
| `data/known-addresses.json` | 130 tagged entities for address resolution |
| `DASHBOARD_HANDOFF.md` | Original detailed spec with formatting rules |

## Formatting Notes

- **EGLD amounts**: Comma-separated with 2 decimal places. Abbreviate millions: `14.25M EGLD`.
- **USD amounts**: `$3.68` for small, `$109.1M` for millions, `$210K` for thousands.
- **Percentages**: `staked_ratio` is a 0-1 fraction — multiply by 100. `change_pct` values are already percentages. `service_fee_pct` may have floating point artifacts (e.g., `7.920000000000001`) — round to 1 decimal.
- **Addresses**: Truncate to `erd1qyu5...cr6th` (first 10 + last 5 chars).
- **Null deltas**: Display "Baseline" in muted gray text, or "—" in table cells.
- **Duplicate exchange names**: The `by_exchange[]` array may contain duplicate names (e.g., "Binance.com" appears 3x for different wallet types). Aggregate by name before charting — sum `net_flow_egld` values per exchange name.
- **Exchange flow null handling**: When all `net_flow_egld` values are null (baseline), skip the bar chart entirely and show a NullState message.

## Verification

1. Run `pnpm dev` — dashboard loads at localhost
2. Report selector shows `2026-04-02` and loads it
3. All 8 sections render with real data from the JSON
4. Null deltas show "Baseline" or "—" gracefully (no broken UI)
5. Addresses link to MultiversX Explorer correctly
6. Tables sort when clicking column headers
7. Nivo charts render (staked ratio donut, exchange flow bars, provider bars, xExchange pairs)
8. Page scrolls smoothly between sections; SectionNav highlights current section
