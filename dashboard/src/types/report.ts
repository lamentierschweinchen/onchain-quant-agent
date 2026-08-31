// TypeScript interfaces for the MultiversX Weekly Intelligence Report.
// Generated from data/report-schema.json (v2 — expanded).
// All v2 additions are optional, so older reports continue to render.

// ---------------------------------------------------------------------------
// Type aliases
// ---------------------------------------------------------------------------

export type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info'
export type AnomalySeverity = 'critical' | 'high' | 'medium' | 'low'
export type Category =
  | 'whale'
  | 'staking'
  | 'token'
  | 'defi'
  | 'network'
  | 'anomaly'
  | 'trend'
export type FlowType =
  | 'exchange_inflow'
  | 'exchange_outflow'
  | 'exchange_to_exchange'
  | 'defi_deposit'
  | 'defi_withdrawal'
  | 'whale_to_whale'
  | 'staking'
  | 'unstaking'
  | 'bridge'
  | 'unknown'
export type ProtocolCategory =
  | 'dex'
  | 'lending'
  | 'liquid_staking'
  | 'stablecoin'
  | 'nft_marketplace'
  | 'bridge'
  | 'perpetuals'
  | 'aggregator'
  | 'other'
export type WhaleTier = 'mega_whale' | 'large_whale' | 'mid_whale'
export type AnomalyMethod = 'z_score' | 'percent_threshold' | 'rule_based'
export type HealthSignal =
  | 'growing'
  | 'flat'
  | 'shrinking'
  | 'spiking'
  | 'draining'

// ---------------------------------------------------------------------------
// Metadata
// ---------------------------------------------------------------------------

export interface ReportMetadata {
  /** YYYY-MM-DD */
  report_date: string
  /** ISO 8601 date-time — start of 7-day analysis window */
  period_start: string
  /** ISO 8601 date-time — end of analysis window */
  period_end: string
  /** ISO 8601 date-time */
  generated_at: string
  egld_price_usd: number
  btc_price_usd?: number | null
  eth_price_usd?: number | null
  run_number?: number | null
  data_sources_ok: string[]
  data_sources_failed: string[]
}

// ---------------------------------------------------------------------------
// Executive summary
// ---------------------------------------------------------------------------

export interface Finding {
  finding: string
  severity: Severity
  category: Category
}

// ---------------------------------------------------------------------------
// Network health
// ---------------------------------------------------------------------------

export interface Economics {
  egld_price_usd: number
  market_cap_usd: number
  total_supply: number
  circulating_supply: number
  staked_egld: number
  staked_ratio: number
  staking_apr: number
  base_apr?: number | null
  topup_apr?: number | null
  token_market_cap_usd: number
}

export interface Activity {
  total_accounts: number
  total_transactions: number
  epoch: number
  blocks: number
  shards: number
  transactions_7d?: number | null
  avg_daily_transactions?: number | null
}

export interface NetworkDeltas {
  price_change_pct: number | null
  market_cap_change_pct: number | null
  staked_ratio_change_pp: number | null
  apr_change_pp: number | null
  accounts_added: number | null
  transactions_added: number | null
  supply_added?: number | null
  staked_egld_added?: number | null
  epoch_advanced?: number | null
}

export interface NetworkHealth {
  economics: Economics
  activity: Activity
  deltas: NetworkDeltas
  analysis: string
}

// ---------------------------------------------------------------------------
// Whale intelligence
// ---------------------------------------------------------------------------

export interface LargeTransaction {
  hash: string
  timestamp: string
  sender: string
  sender_label: string | null
  receiver: string
  receiver_label: string | null
  value_egld: number
  value_usd: number
  flow_type: FlowType
}

export interface WalletChange {
  address: string
  label: string | null
  category?: string | null
  tier?: WhaleTier | null
  balance_current_egld: number
  balance_previous_egld: number | null
  change_egld: number | null
  change_pct: number | null
}

export interface WhaleTierStats {
  threshold_egld: number
  count_current: number
  count_previous: number | null
  total_balance_egld: number
  previous_total_balance_egld: number | null
  net_change_egld: number | null
  net_change_pct: number | null
}

export interface WhaleTiers {
  mega_whales?: WhaleTierStats
  large_whales?: WhaleTierStats
  mid_whales?: WhaleTierStats
}

export interface ExchangeFlowEntry {
  exchange: string
  change_egld: number | null
  pct?: number | null
}

export interface EntityNettingEntry {
  entity: string
  net_flow_egld: number
  wallets_count: number
  interpretation?: string | null
}

export interface ExchangeFlows {
  total_exchange_egld_current: number | null
  total_exchange_egld_previous: number | null
  net_change_egld: number | null
  net_change_pct: number | null
  direction: string | null
  signal: string | null
  by_exchange: ExchangeFlowEntry[]
  entity_netting?: EntityNettingEntry[]
}

export interface DormantActivation {
  address: string
  label: string | null
  balance_egld: number
  last_active_before: string
  dormant_days?: number | null
  action: string
}

// ---------------------------------------------------------------------------
// OTC pipeline (first-class since run #19; wave-window netting since run #21)
// ---------------------------------------------------------------------------

export interface VenueNetting {
  venue: string
  desk_to_venue_egld: number
  venue_to_desk_egld: number
  net_egld: number
}

/** A historical window re-measured after the fact (gross -> net one-way). */
export interface NettedWindow {
  window: string
  gross_egld: number
  circular_egld: number
  net_one_way_egld: number
  circular_share_pct: number
  net_by_venue?: Record<string, number>
}

/**
 * Run #21: circularity crosses week boundaries, so a wave that spans two
 * reporting weeks must be netted feed-to-drain. Summing the weekly nets
 * overstates one-way distribution — the weekly figures are upper bounds.
 */
export interface WaveWindowNetting {
  window: string
  gross_outbound_egld: number
  gross_inbound_egld: number
  circular_egld: number
  circular_share_pct: number
  net_one_way_egld: number
  sum_of_weekly_nets_egld: number
  weekly_frame_overstatement_egld: number
  weekly_frame_overstatement_pct: number
  net_by_venue: Record<string, number>
  outbound_by_venue?: Record<string, number>
  inbound_by_venue?: Record<string, number>
  note?: string
}

export interface OtcPipeline {
  gross_outbound_egld_7d: number
  gross_inbound_egld_7d: number
  circular_egld_7d?: number
  net_one_way_egld_7d?: number
  circular_share_pct?: number | null
  desk_balance_egld?: number
  previous_desk_balance_egld?: number
  upbit_reload_egld?: number
  venue_netting?: VenueNetting[]
  /** Keyed by run label, e.g. { run19: 301498, run20: 604086 } */
  gross_series_egld_7d?: Record<string, number>
  net_one_way_series_egld_7d?: Record<string, number>
  circularity_series_pct?: Record<string, number>
  peak_window_renetted?: NettedWindow
  backfilled_windows?: NettedWindow[]
  wave_window_netting?: WaveWindowNetting
  series_note?: string
}

export interface WithdrawalBreadth {
  distinct_recipients_raw: number
  total_egld_raw: number
  distinct_recipients_ex_pipeline: number
  total_egld_ex_pipeline: number
  pipeline_share_pct: number | null
}

export interface DemandInstruments {
  identifiable_bid_absorbed_egld_7d: number
  mega_whale_balance_egld?: number
  mega_whale_change_egld?: number
  coinbase_routing_balance_egld?: number
  coinbase_routing_inflow_egld?: number
  weeks_at_zero?: number
  weeks_at_zero_in_last_four?: number
  bid_to_distribution_ratio_pct?: number | null
  dex_turnover_ratio_pct?: number | null
  previous_dex_turnover_ratio_pct?: number | null
  withdrawal_breadth?: WithdrawalBreadth
}

export interface WhaleIntelligence {
  large_transactions: LargeTransaction[]
  wallet_changes: WalletChange[]
  whale_tiers?: WhaleTiers
  exchange_flows: ExchangeFlows
  dormant_activations?: DormantActivation[]
  otc_pipeline?: OtcPipeline
  demand_instruments?: DemandInstruments
  analysis: string
}

// ---------------------------------------------------------------------------
// Staking intelligence
// ---------------------------------------------------------------------------

export interface StakingProvider {
  rank: number
  identity: string
  name?: string | null
  provider_address?: string | null
  locked_egld: number
  previous_locked_egld?: number | null
  share_pct: number
  apr_pct: number
  fee_pct: number
  num_users: number
  num_nodes?: number | null
  wow_change_egld?: number | null
}

export interface Concentration {
  top_5_share_pct: number
  top_10_share_pct: number
  hhi: number | null
  hhi_previous: number | null
  hhi_interpretation?: string | null
}

export interface StakingSummary {
  total_staked_egld: number
  total_delegated_egld?: number | null
  staked_ratio: number
  num_providers: number
  apr_min?: number | null
  apr_max?: number | null
  apr_weighted_avg?: number | null
}

export interface AprBucket {
  label: string
  min_apr_pct: number
  max_apr_pct: number
  provider_count: number
  total_locked_egld: number
}

export interface AprDistribution {
  buckets: AprBucket[]
}

export interface AprOutlier {
  identity: string
  name?: string | null
  apr_pct: number
  fee_pct: number
  locked_egld: number
}

export interface AprOutliers {
  top_apr: AprOutlier[]
  lowest_fee: AprOutlier[]
}

export interface StakingChurn {
  total_delegators_current: number
  total_delegators_previous: number | null
  delegators_added: number | null
  delegators_change_pct: number | null
  providers_gaining_delegators: number | null
  providers_losing_delegators: number | null
}

/**
 * The collector emits `total_events` / `by_count` / `by_value_egld`; the original
 * type declared `events` / `fates_by_*`, which never matched any report. Because
 * the fetched JSON is cast rather than parsed, TypeScript could not catch it and
 * the fates table rendered a blank event count and all-zero fates from run #11
 * until run #23. Both spellings are accepted so the whole archive renders.
 */
export interface RewardFateTier {
  events?: number
  total_events?: number
  total_value_egld: number
  fates_by_count?: Record<string, number>
  by_count?: Record<string, number>
  fates_by_value_egld?: Record<string, number>
  by_value_egld?: Record<string, number>
}

export interface RewardOperatorEntry {
  provider: string
  owner_address: string | null
  owner_label: string | null
  owner_balance_egld: number | null
  outbound_count: number | null
  fates_by_count: Record<string, number>
  fates_by_value_egld: Record<string, number>
}

export interface RewardBehavior {
  providers_sampled: number
  delegator_window_days: number
  operator_window_days: number
  function_distribution: Record<string, { count: number; share_pct: number }>
  compound_pct_at_function_level: number
  compound_vs_claim: { redelegate_count: number; claim_count: number }
  delegator_fates_by_tier: Record<string, RewardFateTier>
  provider_operators: RewardOperatorEntry[]
  key_findings?: string[]
}

export interface FeeEvent {
  provider: string
  fee_from_pct: number
  fee_to_pct: number
  apr_from_pct?: number | null
  apr_to_pct?: number | null
  locked_egld: number
  locked_wow_egld?: number | null
  users?: number | null
  users_wow?: number | null
  num_nodes?: number | null
}

export interface UnbondingLeg {
  provider: string
  amount: number
  days_to_unbond: number
  date: string
}

/**
 * Run #21: the staked-minus-delegated residual also contains delegation
 * unbonding in flight. This block is what makes it decomposable — and it is the
 * only forward-looking quantity in the report: the EGLD becomes liquid on a
 * known date.
 */
export interface UnbondingInFlight {
  wallet: string
  total_egld: number
  legs: UnbondingLeg[]
  share_of_delegation_decline_pct?: number | null
  raw_residual_egld: number
  corrected_direct_node_egld: number | null
  status?: string
}

export interface StakingIntelligence {
  summary?: StakingSummary
  top_providers: StakingProvider[]
  concentration: Concentration
  apr_distribution?: AprDistribution
  apr_outliers?: AprOutliers
  churn?: StakingChurn
  reward_behavior?: RewardBehavior
  fee_events?: FeeEvent[]
  unbonding_in_flight?: UnbondingInFlight
  analysis: string
}

// ---------------------------------------------------------------------------
// Token activity
// ---------------------------------------------------------------------------

export interface TokenByHolders {
  identifier: string
  name: string
  holders: number
  previous_holders: number | null
  holders_change?: number | null
  price_usd: number | null
  market_cap_usd: number | null
  volume_24h_usd: number | null
}

export interface TokenByVolume {
  identifier: string
  name: string
  transactions: number | null
  previous_transactions?: number | null
  change_pct?: number | null
  price_usd?: number | null
  volume_24h_usd?: number | null
}

export interface TokenByTransactions {
  identifier: string
  name: string
  total_transactions: number
}

export interface NewlyIssuedToken {
  identifier: string
  name: string
  deployer?: string | null
  deployer_label?: string | null
  issued_at?: string | null
  holders?: number | null
  transactions?: number | null
  supply?: number | null
  decimals?: number | null
}

export interface PairByVolume {
  name: string
  volume_24h_usd: number
  share_pct: number
  tvl_usd?: number | null
  trades_count_24h?: number | null
  is_other?: boolean
}

export interface XExchangeSummary {
  total_pairs: number
  total_volume_24h_usd: number | null
  mex_price_usd: number
  mex_market_cap_usd: number
  mex_price_change_24h_pct?: number | null
  mex_price_change_wow_pct?: number | null
  top_pair: string | null
  top_pair_volume_24h_usd: number | null
  top_pair_dominance_pct: number | null
  top_pairs_by_volume?: PairByVolume[]
}

export interface TokenActivity {
  top_by_holders: TokenByHolders[]
  top_by_volume?: TokenByVolume[]
  top_by_transactions?: TokenByTransactions[]
  top_by_market_cap?: TokenByHolders[]
  newly_issued?: NewlyIssuedToken[]
  xexchange: XExchangeSummary
  analysis: string
}

// ---------------------------------------------------------------------------
// DeFi activity
// ---------------------------------------------------------------------------

export interface ProtocolActivity {
  name: string
  category: string
  volume_24h_usd: number | null
  active_pairs: number | null
  transfers_24h: number | null
  tvl_egld?: number | null
  tvl_usd?: number | null
  tvl_wow_change_pct?: number | null
}

export interface ProtocolBreakdown {
  protocol: string
  category: ProtocolCategory
  addresses_tracked: number
  tvl_egld?: number | null
  tvl_usd?: number | null
  tvl_wow_change_pct?: number | null
  tvl_wow_change_egld?: number | null
  transfers_24h?: number | null
  unique_users_7d?: number | null
  notable_events?: string | null
  health_signal?: HealthSignal | null
}

export interface ScDeployment {
  address: string
  deployer: string
  deployer_label?: string | null
  timestamp: string
  interaction_count: number
}

export interface DefiActivity {
  protocols: ProtocolActivity[]
  protocol_breakdown?: ProtocolBreakdown[]
  sc_deployments?: ScDeployment[]
  analysis: string
}

// ---------------------------------------------------------------------------
// Anomalies
// ---------------------------------------------------------------------------

export interface Anomaly {
  metric: string
  current_value: number
  previous_value?: number | null
  average_value?: number | null
  stddev?: number | null
  z_score?: number | null
  change_pct?: number | null
  method?: AnomalyMethod | null
  description: string
  severity: AnomalySeverity
}

// ---------------------------------------------------------------------------
// Trend indicators (NEW)
// ---------------------------------------------------------------------------

export interface AcceleratingExchangeOutflow {
  exchange: string
  trend: string
  cumulative_change_pct?: number | null
  weeks_in_trend: number
  interpretation?: string | null
}

export interface NotableValidator {
  identity: string
  name?: string | null
  locked_egld: number
}

export interface NotableLeaver {
  identity: string
  name?: string | null
  previous_locked_egld: number
}

export interface ValidatorMovements {
  providers_joining: number | null
  providers_leaving: number | null
  net_provider_change: number | null
  notable_joiners?: NotableValidator[]
  notable_leavers?: NotableLeaver[]
}

export type SupplyEvent =
  | 'mint'
  | 'burn'
  | 'unlock'
  | 'lock'
  | 'issuance'
  | 'supply_change'

export interface TokenSupplyEvent {
  identifier: string
  name: string
  event: SupplyEvent
  magnitude_pct?: number | null
  current_supply?: number | null
  previous_supply?: number | null
  description: string
}

export interface ConsecutiveStreak {
  metric: string
  direction: 'up' | 'down' | 'flat'
  weeks: number
  cumulative_change_pct?: number | null
  interpretation?: string | null
}

export interface RegimeShift {
  metric: string
  before_value?: number | null
  after_value: number
  description: string
}

export interface TrendIndicators {
  accelerating_exchange_outflows?: AcceleratingExchangeOutflow[]
  validator_movements?: ValidatorMovements
  token_supply_events?: TokenSupplyEvent[]
  consecutive_streaks?: ConsecutiveStreak[]
  regime_shifts?: RegimeShift[]
}

// ---------------------------------------------------------------------------
// Watch list
// ---------------------------------------------------------------------------

export interface WatchItem {
  item: string
  reason: string
  weeks_on_list: number
}

// ---------------------------------------------------------------------------
// Meta-learning
// ---------------------------------------------------------------------------

export interface MetaLearning {
  run_number: number
  endpoints_that_worked?: string[]
  endpoints_that_failed?: string[]
  api_quirks?: string[]
  key_findings?: string[]
  action_items_from_previous?: number | null
  action_items_completed?: number | null
  methodology_changes?: string[]
  new_addresses_discovered?: number | null
  most_valuable_insight?: string | null
  top_recommendation?: string | null
  recommendations_for_next_run?: string[]
}

// ---------------------------------------------------------------------------
// Pre-committed tests (run #21+) — the model's epistemic ledger.
// Forward-only: never backfilled from prose.
// ---------------------------------------------------------------------------

export type TestStatus = 'open' | 'resolved'
export type TestOutcome =
  | 'as_predicted'
  | 'against'
  | 'inconclusive'
  | 'withdrawn'

export interface TestBranch {
  condition: string
  reading: string
}

export interface PreCommittedTest {
  id: string
  registered_in_run: number
  claim: string
  threshold: string
  branches?: TestBranch[]
  status: TestStatus
  outcome?: TestOutcome | null
  resolved_in_run?: number | null
  resolution?: string | null
  measured_value?: string | null
}

/** One run's prediction record — the traced factor. */
export interface ScoreboardRunRecord {
  run: number | null
  date: string
  registered: number
  resolved: number
  as_predicted: number
  against: number
  inconclusive: number
  withdrawn: number
  hit_rate_pct: number | null
  open_after: number
}

export interface ScoreboardTotals {
  tests: number
  resolved: number
  open: number
  as_predicted: number
  against: number
  inconclusive: number
  withdrawn: number
  hit_rate_pct: number | null
}

/** Cross-run ledger, aggregated at build time from every report. */
export interface ScoreboardLedger {
  generated_from: number
  totals: ScoreboardTotals
  runs: ScoreboardRunRecord[]
  tests: (PreCommittedTest & { seen_in_run?: number; seen_in_date?: string })[]
}

// ---------------------------------------------------------------------------
// Errata overlay — aggregated across all reports by generate-manifest.ts
// ---------------------------------------------------------------------------

export interface WithdrawnClaim {
  claim: string
  asserted_in_runs: number[]
  withdrawn_in_run: number
  reason: string
  replacement?: string | null
  /** Added by the manifest generator */
  asserted_in_dates?: string[]
  withdrawn_in_date?: string | null
}

export interface Errata {
  generated_from: number
  claims: WithdrawnClaim[]
}

// ---------------------------------------------------------------------------
// Manifest
// ---------------------------------------------------------------------------

export interface ManifestEntry {
  date: string
  file: string
}

// ---------------------------------------------------------------------------
// Top-level
// ---------------------------------------------------------------------------

export interface WeeklyReport {
  metadata: ReportMetadata
  executive_summary: Finding[]
  network_health: NetworkHealth
  whale_intelligence: WhaleIntelligence
  staking_intelligence: StakingIntelligence
  token_activity: TokenActivity
  defi_activity: DefiActivity
  anomalies: Anomaly[]
  trend_indicators?: TrendIndicators
  watch_list: WatchItem[]
  pre_committed_tests?: PreCommittedTest[]
  meta_learning?: MetaLearning
}
