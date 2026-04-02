# Dashboard Frontend — Handoff for Next Agent

## What This Is

The `onchain-quant-agent` repo generates **weekly MultiversX blockchain intelligence reports** via a scheduled Claude Code agent. Reports are produced as both markdown (`reports/YYYY-MM-DD.md`) and structured JSON (`reports/YYYY-MM-DD.json`). The JSON follows a strict schema (`data/report-schema.json`).

**Your job**: Build a frontend dashboard that reads these JSON reports and presents them as a beautiful, interactive intelligence interface. Think Bloomberg Terminal meets crypto analytics — dark theme, data-dense, scannable.

---

## Architecture Decision

**Static site that reads JSON files directly.** No backend needed. The reports are committed to the repo by the scheduled agent every Monday. The dashboard reads them at build time or at runtime from the `/reports/` directory.

**Recommended stack:**
- **React + TypeScript** (the repo already has TypeScript configured)
- **Vite** as bundler
- **Tailwind CSS v4** for styling
- **Recharts** or **Nivo** for charts (both work well with this data shape)
- Deploy to **GitHub Pages** or **Vercel** (static export)

Put the dashboard in a `dashboard/` subdirectory of this repo (separate Vite project), or in a new repo — your call based on what feels cleaner.

---

## Data Source

### Report Files
- Location: `reports/YYYY-MM-DD.json`
- Schema: `data/report-schema.json` (JSON Schema draft-07)
- Currently one report exists: `reports/2026-04-02.json` (27KB, baseline — most WoW deltas are `null`)
- New reports appear weekly. The dashboard should list all available reports and default to the latest.

### Report Structure (top-level keys)

```
metadata              — date, period, EGLD price, data source status
executive_summary     — 3-7 findings with severity + category
network_health        — economics, activity stats, WoW deltas, analysis narrative
whale_intelligence    — large transactions, wallet changes, exchange flows, dormant activations, analysis
staking_intelligence  — top providers (name, locked, delegators, APR, nodes), concentration metrics (HHI), analysis
token_activity        — top by holders, top by volume, new tokens, xExchange summary, analysis
defi_activity         — SC deployments, protocol activity, analysis
anomalies             — z-score flagged metrics with severity
watch_list            — developing patterns worth monitoring
meta_learning         — run self-assessment (run number, action items completed, methodology changes)
```

### Key Data Types to Handle
- **Severity levels**: `critical` | `high` | `medium` | `low` | `info` — map to colors (red, orange, yellow, blue, gray)
- **Categories**: `whale` | `staking` | `token` | `defi` | `network` | `anomaly` — map to icons/colors
- **Flow types**: `exchange_inflow` | `exchange_outflow` | `defi_deposit` | `defi_withdrawal` | `whale_to_whale` | `staking` | `unstaking` | `bridge` | `unknown`
- **Nullable deltas**: First-run data has `null` for all WoW changes. Display "—" or "Baseline" gracefully.
- **EGLD amounts**: Already human-readable (not raw 10^18). Format with commas: `14,251,847 EGLD`
- **USD amounts**: Use `$109.1M`, `$3.68`, `$210K` formatting
- **Percentages**: `staked_ratio` is 0-1 fraction (multiply by 100 for display). `change_pct` values are already percentages.

---

## Dashboard Layout — 6 Sections

### 1. Header Bar
- Report date selector (dropdown of all available `YYYY-MM-DD.json` files)
- EGLD price from `metadata.egld_price_usd` with WoW change arrow
- Data source health indicators (green dots for `data_sources_ok`, red for `data_sources_failed`)
- Last generated timestamp

### 2. Executive Summary (top of page, always visible)
- Card row or alert-style banners for each finding in `executive_summary[]`
- Color-coded by `severity` (critical = red pulse, high = orange, medium = yellow, low = blue, info = gray)
- Category icon/badge on each card
- This is the "TL;DR" — should be scannable in 5 seconds

### 3. Network Health Panel
- **Key metrics grid** (2x3 or 3x2):
  - EGLD Price + delta
  - Market Cap + delta
  - Staked Ratio (show as gauge/donut: 48.1% staked vs 51.9% circulating)
  - Staking APR + delta
  - Total Accounts + delta
  - Total Transactions + delta
- **Deltas**: Show as `+2.3%` green or `-1.5%` red badges. If `null`, show "Baseline" in gray.
- **Analysis text**: Render `network_health.analysis` as a narrative block below metrics
- **Over time**: When multiple reports exist, chart these metrics week-over-week

### 4. Whale Intelligence Panel (the most complex section)

**4a. Exchange Flow Summary**
- Net flow indicator: big arrow up (sell pressure) or down (accumulation) based on `exchange_flows.net_exchange_flow_egld`
- Bar chart of `by_exchange[]` flows (positive = inflow = red, negative = outflow = green)
- Total inflow vs outflow comparison

**4b. Top Wallet Changes**
- Table from `wallet_changes[]`:
  | Label | Balance | Change | Change % |
  | Color code by category (exchange = blue, defi = purple, team = green, other = gray)
- Sortable columns
- Address truncated with copy button, linked to `https://explorer.multiversx.com/accounts/{address}`

**4c. Large Transactions**
- Table from `large_transactions[]`:
  | Time | From | To | Value EGLD | Value USD | Flow Type |
  | Flow type badges (color-coded)
- Link hashes to `https://explorer.multiversx.com/transactions/{hash}`

**4d. Dormant Activations**
- List from `dormant_activations[]` — wallets inactive 6+ months that woke up
- Show last active date and action taken
- This is a high-signal alert section — make it visually prominent when non-empty

**4e. Analysis narrative** from `whale_intelligence.analysis`

### 5. Staking Intelligence Panel

**5a. Provider Leaderboard**
- Table from `staking_intelligence.top_providers[]`:
  | Rank | Name | Locked EGLD | Change | Delegators | APR | Fee | Nodes |
  | Sortable, default sort by locked descending
- Highlight APR outliers (Incal at 8.82% with 1% fee, Maple Leaf at 9.28% with 0% fee — these are interesting)

**5b. Concentration Metrics**
- `top_5_share_pct` and `top_10_share_pct` as horizontal bar or progress bar
- HHI value with interpretation badge: < 0.15 green "Competitive", 0.15-0.25 yellow "Moderate", > 0.25 red "Concentrated"
- Show `previous_herfindahl` for trend if available

**5c. Staking Distribution Chart**
- Treemap or horizontal stacked bar of top 15 providers by locked amount
- Shows relative market share visually

**5d. Analysis narrative** from `staking_intelligence.analysis`

### 6. Token & DeFi Panel

**6a. Top Tokens by Holders**
- Table from `token_activity.top_by_holders[]`:
  | Token | Name | Holders | Prev Holders | Price | Market Cap |
- Filter out spam tokens (DRX with 2.47M holders but no market cap is noise)

**6b. Top Tokens by Volume**
- Table from `token_activity.top_by_volume[]`:
  | Token | Name | Transactions | Change % | Price |
  | Highlight volume spikes (change_pct > 100%)

**6c. xExchange Summary**
- From `token_activity.xexchange_summary`:
  - Total pairs count, 24h volume
  - MEX price and market cap
  - Top pairs by volume as a mini bar chart

**6d. DeFi Protocol Activity**
- Cards from `defi_activity.protocol_activity[]`:
  | Protocol | Category Badge | TX Count | Users | Notable Events |

**6e. Analysis narratives** from both sections

### 7. Anomalies & Watch List (bottom section)

**7a. Anomaly Alerts**
- From `anomalies[]`:
  - Card per anomaly with severity badge
  - Show metric name, current value, average, z-score
  - Description text
  - Sort by severity

**7b. Watch List**
- From `watch_list[]`:
  - Persistent items tracker — show `weeks_on_list` as a badge
  - Item + reason pairs
  - Items graduating from watch to anomaly should be highlighted

### 8. Meta / About (collapsible footer or separate page)
- From `meta_learning`:
  - Run number, methodology changes this week
  - Action items completed ratio (progress bar)
  - Most valuable insight
  - Top recommendation for next run
- This shows the agent's self-improvement loop — interesting for transparency

---

## Design Guidelines

### Theme
- **Dark mode primary** (dark navy/charcoal background, not pure black)
- Light mode optional toggle
- MultiversX brand colors for accents: `#23F7DD` (cyan/teal), `#1B46C2` (blue)
- Severity colors: critical `#EF4444`, high `#F97316`, medium `#EAB308`, low `#3B82F6`, info `#6B7280`

### Typography
- Monospace for addresses and numbers (transaction hashes, EGLD amounts)
- Sans-serif for narratives and labels
- Analysis text sections should feel like reading a Bloomberg note — clean, professional

### Responsive
- Desktop-first (this is an analytics dashboard, primarily consumed on desktop)
- Tablet should work (stack panels vertically)
- Mobile: simplified view with executive summary + key metrics only

### Interactions
- Tables should be sortable by clicking column headers
- Addresses should be truncatable with copy-to-clipboard
- All addresses link to MultiversX Explorer: `https://explorer.multiversx.com/accounts/{address}`
- All tx hashes link to: `https://explorer.multiversx.com/transactions/{hash}`
- Report date picker to browse historical reports
- Charts should have tooltips on hover

---

## Loading Reports

The simplest approach for a static site:

```typescript
// Option A: At build time, generate a manifest of all report files
// Create a script that reads reports/ directory and outputs reports-manifest.json
// [{ date: "2026-04-02", file: "2026-04-02.json" }, ...]

// Option B: At runtime, fetch from a known path
const response = await fetch(`/reports/${selectedDate}.json`);
const report: WeeklyReport = await response.json();
```

For Option A with Vite, you can use `import.meta.glob`:
```typescript
const reports = import.meta.glob('/reports/*.json');
```

---

## TypeScript Types

Generate types from `data/report-schema.json`. Here's the top-level interface to get started:

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
  meta_learning: MetaLearning;
}

interface Finding {
  finding: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  category: 'whale' | 'staking' | 'token' | 'defi' | 'network' | 'anomaly';
}
```

Full types should be generated from the schema. Use a tool like `json-schema-to-typescript` or write them manually from `data/report-schema.json`.

---

## Key Files to Read

| File | Why |
|------|-----|
| `data/report-schema.json` | The contract — defines every field the dashboard must handle |
| `reports/2026-04-02.json` | Real data to build against (27KB, comprehensive) |
| `reports/2026-04-02.md` | The markdown report — shows the narrative tone and structure |
| `data/known-addresses.json` | 135 tagged entities — could be used for address resolution on the frontend too |
| `README.md` | Project context |

---

## Nice-to-Haves (if time allows)

1. **Week-over-week trend sparklines**: When 4+ reports exist, show mini line charts next to key metrics
2. **Whale flow Sankey diagram**: Visualize exchange inflows/outflows as a Sankey or flow diagram
3. **Staking treemap**: Interactive treemap of provider market share
4. **Search**: Filter whale transactions, token tables, providers by text
5. **Export**: Download current view as PDF or PNG
6. **RSS/notification**: Show when a new report is available
7. **Diff view**: Compare two reports side by side highlighting what changed

---

## What NOT to Build

- No backend API server — this reads static JSON files
- No authentication — these are public reports
- No real-time data fetching from MultiversX API — the agent does that weekly
- No data editing/admin interface — the agent manages all data
- Don't try to re-implement the analysis — just display what the agent produced
