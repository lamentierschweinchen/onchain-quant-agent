// TypeScript interfaces for the MultiversX Weekly Intelligence Report.
// Generated from data/report-schema.json and validated against reports/2026-04-02.json.

// ---------------------------------------------------------------------------
// Type aliases
// ---------------------------------------------------------------------------

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info';
export type AnomalySeverity = 'critical' | 'high' | 'medium' | 'low';
export type Category = 'whale' | 'staking' | 'token' | 'defi' | 'network' | 'anomaly';
export type FlowType =
  | 'exchange_inflow'
  | 'exchange_outflow'
  | 'defi_deposit'
  | 'defi_withdrawal'
  | 'whale_to_whale'
  | 'staking'
  | 'unstaking'
  | 'bridge'
  | 'unknown';
export type ProtocolCategory =
  | 'dex'
  | 'lending'
  | 'liquid_staking'
  | 'nft_marketplace'
  | 'bridge'
  | 'perpetuals'
  | 'other';

// ---------------------------------------------------------------------------
// Metadata
// ---------------------------------------------------------------------------

export interface ReportMetadata {
  /** YYYY-MM-DD */
  report_date: string;
  /** ISO 8601 date-time — start of 7-day analysis window */
  period_start: string;
  /** ISO 8601 date-time — end of analysis window */
  period_end: string;
  /** ISO 8601 date-time */
  generated_at: string;
  egld_price_usd: number;
  data_sources_ok: string[];
  data_sources_failed: string[];
}

// ---------------------------------------------------------------------------
// Executive summary
// ---------------------------------------------------------------------------

export interface Finding {
  /** One-sentence insight */
  finding: string;
  severity: Severity;
  category: Category;
}

// ---------------------------------------------------------------------------
// Network health
// ---------------------------------------------------------------------------

export interface Economics {
  egld_price_usd: number;
  market_cap_usd: number;
  total_supply: number;
  circulating_supply: number;
  staked_egld: number;
  /** Fraction 0–1 */
  staked_ratio: number;
  /** Fraction, e.g. 0.089 for 8.9% */
  staking_apr: number;
  token_market_cap_usd: number;
}

export interface Activity {
  total_accounts: number;
  total_transactions: number;
  epoch: number;
  blocks: number;
  shards: number;
}

/** Week-over-week changes. All fields are null when no previous data exists. */
export interface NetworkDeltas {
  price_change_pct: number | null;
  market_cap_change_pct: number | null;
  /** percentage points (pp) */
  staked_ratio_change_pp: number | null;
  /** percentage points (pp) */
  apr_change_pp: number | null;
  accounts_added: number | null;
  transactions_added: number | null;
}

export interface NetworkHealth {
  economics: Economics;
  activity: Activity;
  deltas: NetworkDeltas;
  /** Narrative analysis of network health trends */
  analysis: string;
}

// ---------------------------------------------------------------------------
// Whale intelligence
// ---------------------------------------------------------------------------

export interface LargeTransaction {
  hash: string;
  /** ISO 8601 date-time */
  timestamp: string;
  /** Bech32 sender address */
  sender: string;
  sender_label: string | null;
  /** Bech32 receiver address */
  receiver: string;
  receiver_label: string | null;
  value_egld: number;
  value_usd: number;
  flow_type: FlowType;
}

export interface WalletChange {
  address: string;
  label: string | null;
  category?: string | null;
  balance_current_egld: number;
  balance_previous_egld: number | null;
  change_egld: number | null;
  change_pct: number | null;
}

export interface ExchangeFlowEntry {
  exchange: string;
  change_egld: number | null;
  pct?: number | null;
}

/** Net flow to/from known exchange addresses.
 *  Negative net_change_egld = net outflow (accumulation signal).
 *  Positive = net inflow (sell pressure).
 */
export interface ExchangeFlows {
  total_exchange_egld_current: number | null;
  total_exchange_egld_previous: number | null;
  net_change_egld: number | null;
  net_change_pct: number | null;
  direction: string | null;
  signal: string | null;
  by_exchange: ExchangeFlowEntry[];
}

export interface DormantActivation {
  address: string;
  label: string | null;
  balance_egld: number;
  /** YYYY-MM-DD */
  last_active_before: string;
  action: string;
}

export interface WhaleIntelligence {
  /** Transactions > 5,000 EGLD in the period */
  large_transactions: LargeTransaction[];
  /** Top wallet balance changes vs previous week */
  wallet_changes: WalletChange[];
  exchange_flows: ExchangeFlows;
  /** Wallets inactive 6+ months that moved funds this week */
  dormant_activations: DormantActivation[];
  /** Narrative: accumulation vs distribution signals, smart money patterns */
  analysis: string;
}

// ---------------------------------------------------------------------------
// Staking intelligence
// ---------------------------------------------------------------------------

export interface StakingProvider {
  rank: number;
  identity: string;
  locked_egld: number;
  share_pct: number;
  apr_pct: number;
  fee_pct: number;
  num_users: number;
}

/**
 * HHI interpretation:
 *   < 0.15  — competitive (decentralized)
 *   0.15–0.25 — moderate concentration
 *   > 0.25  — concentrated
 */
export interface Concentration {
  top_5_share_pct: number;
  top_10_share_pct: number;
  hhi: number | null;
  hhi_previous: number | null;
  hhi_interpretation?: string | null;
}

export interface StakingSummary {
  total_staked_egld: number;
  total_delegated_egld: number;
  staked_ratio: number;
  num_providers: number;
  apr_min: number;
  apr_max: number;
  apr_weighted_avg: number;
}

export interface StakingIntelligence {
  summary: StakingSummary;
  top_providers: StakingProvider[];
  concentration: Concentration;
  analysis: string;
}

// ---------------------------------------------------------------------------
// Token activity
// ---------------------------------------------------------------------------

export interface TokenByHolders {
  identifier: string;
  name: string;
  holders: number;
  previous_holders: number | null;
  price_usd: number | null;
  market_cap_usd: number | null;
  volume_24h_usd: number | null;
}

export interface TokenByTransactions {
  identifier: string;
  name: string;
  total_transactions: number;
}

export interface XExchangeSummary {
  total_pairs: number;
  total_volume_24h_usd: number | null;
  mex_price_usd: number;
  mex_market_cap_usd: number;
  mex_price_change_24h_pct: number | null;
  top_pair: string | null;
  top_pair_volume_24h_usd: number | null;
  top_pair_dominance_pct: number | null;
}

export interface TokenActivity {
  top_by_holders: TokenByHolders[];
  top_by_transactions: TokenByTransactions[];
  top_by_market_cap?: TokenByHolders[];
  xexchange: XExchangeSummary;
  analysis: string;
}

// ---------------------------------------------------------------------------
// DeFi activity
// ---------------------------------------------------------------------------

export interface ProtocolActivity {
  name: string;
  category: string;
  volume_24h_usd: number | null;
  active_pairs: number | null;
  transfers_24h: number | null;
}

export interface DefiActivity {
  protocols: ProtocolActivity[];
  analysis: string;
}

// ---------------------------------------------------------------------------
// Anomalies
// ---------------------------------------------------------------------------

export interface Anomaly {
  metric: string;
  current_value: number;
  previous_value?: number | null;
  average_value?: number | null;
  z_score?: number | null;
  change_pct?: number | null;
  description: string;
  severity: AnomalySeverity;
}

// ---------------------------------------------------------------------------
// Watch list
// ---------------------------------------------------------------------------

export interface WatchItem {
  item: string;
  reason: string;
  weeks_on_list: number;
}

// ---------------------------------------------------------------------------
// Meta-learning (self-improvement loop)
// ---------------------------------------------------------------------------

/**
 * Present from run 2 onward; absent (optional) in the baseline run.
 *
 * NOTE: In the JSON schema, `action_items_from_previous` and
 * `action_items_completed` are *integer counts*, not string arrays.
 */
export interface MetaLearning {
  run_number: number;
  endpoints_that_worked: string[];
  endpoints_that_failed: string[];
  api_quirks: string[];
  key_findings: string[];
  recommendations_for_next_run: string[];
}

// ---------------------------------------------------------------------------
// Report manifest entry (used by the dashboard to list available reports)
// ---------------------------------------------------------------------------

export interface ManifestEntry {
  /** YYYY-MM-DD */
  date: string;
  /** Relative path to the JSON file */
  file: string;
}

// ---------------------------------------------------------------------------
// Top-level report
// ---------------------------------------------------------------------------

export interface WeeklyReport {
  metadata: ReportMetadata;
  /** Top 3–7 findings ordered by significance */
  executive_summary: Finding[];
  network_health: NetworkHealth;
  whale_intelligence: WhaleIntelligence;
  staking_intelligence: StakingIntelligence;
  token_activity: TokenActivity;
  defi_activity: DefiActivity;
  anomalies: Anomaly[];
  watch_list: WatchItem[];
  /** Present from run 2 onward; absent in the baseline run */
  meta_learning?: MetaLearning;
}
