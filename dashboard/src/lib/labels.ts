// Human labels for machine keys.
//
// The report is written by an agent, so anomaly/streak/regime identifiers arrive
// as snake_case slugs ("otc_netting_window_must_match_the_wave"). They are stable
// keys and worth keeping in the JSON, but a reader should not have to parse them.
// This module turns a slug into a sentence, keeps the raw key available for
// tooltips, and attaches a one-line gloss where the term itself needs explaining.

/** Tokens that should render in their canonical casing rather than Title Case. */
const ACRONYMS: Record<string, string> = {
  egld: 'EGLD',
  otc: 'OTC',
  usd: 'USD',
  usdc: 'USDC',
  usdt: 'USDT',
  ush: 'USH',
  dex: 'DEX',
  cex: 'CEX',
  tvl: 'TVL',
  apr: 'APR',
  hhi: 'HHI',
  lsd: 'LSD',
  mex: 'MEX',
  xegld: 'XEGLD',
  segld: 'SEGLD',
  swtao: 'SWTAO',
  wtao: 'WTAO',
  wegld: 'WEGLD',
  nft: 'NFT',
  defi: 'DeFi',
  wow: 'WoW',
  pct: '%',
  usdc_supply: 'USDC supply',
  xoxno: 'XOXNO',
  hatom: 'Hatom',
  binance: 'Binance',
  coinbase: 'Coinbase',
  bybit: 'Bybit',
  kucoin: 'KuCoin',
  upbit: 'UPbit',
  mexc: 'MEXC',
  bitget: 'Bitget',
  gate: 'Gate.io',
  zoidpay: 'ZoidPay',
  pi: 'pi-staking',
  '7d': '7d',
  '24h': '24h',
  '2nd': '2nd',
  '3rd': '3rd',
  '4th': '4th',
  '100pct': '100%',
  top10: 'top-10',
}

/**
 * Curated overrides — used where a mechanical de-slugging reads badly or where
 * the finding has a name the report itself uses in prose.
 */
const OVERRIDES: Record<string, string> = {
  NET_EXCHANGE: 'Net exchange flow',
  egld_price_usd: 'EGLD price',
  egld_price: 'EGLD price',
  mex_price_usd: 'MEX price',
  staked_egld: 'Total staked EGLD',
  staked_ratio: 'Staked ratio',
  total_delegators: 'Delegator count',
  dex_volume_24h_usd: 'DEX volume (24h)',
  dex_turnover_ratio_pct: 'DEX turnover ratio',
  dex_turnover_ratio: 'DEX turnover ratio',
  reward_compound_rate: 'Reward compound rate',
  token_holder_count_decline: 'Token holder counts declining',
  token_holder_counts_top10: 'Token holder counts (top 10)',
  delegator_base_flat: 'Delegator base flat',
  binance_staking_custody_egld: 'Binance staking custody balance',
  identifiable_bid_absorbed_egld_7d: 'Identifiable bid absorbed (7d)',
  otc_net_one_way_egld_7d: 'OTC net one-way distribution (7d)',
  otc_wave_window_net_one_way_egld: 'OTC wave, netted feed-to-drain',
  otc_net_one_way_distribution: 'OTC net one-way distribution',
  otc_net_one_way_series_backfilled: 'OTC net one-way series backfilled',
  otc_netting_window_must_match_the_wave:
    'Netting window must match the wave, not the week',
  otc_gross_series_restated_in_net_terms:
    'Gross OTC series restated in net terms',
  otc_peak_window_renetted: 'Peak OTC window re-netted',
  otc_throughput_reinterpreted_as_circular:
    'OTC throughput reinterpreted as circular',
  direct_node_unwind: 'Direct-node unwind',
  direct_node_unwind_withdrawn: 'Direct-node unwind withdrawn',
  direct_node_unwind_resolved_as_artifact:
    'Direct-node unwind was a measurement artifact',
  delegation_service_fee_to_100pct: 'Delegation service fees set to 100%',
  delegation_market_fee_repricing_withdrawn:
    'Fee-repricing reading withdrawn',
  delegation_market_repriced: 'Delegation market repriced',
  identifiable_bid_dormancy_ended: 'Identifiable bid woke up',
  identifiable_bid_dormant: 'Identifiable bid dormant',
  identifiable_bid_reactivated: 'Identifiable bid reactivated',
  identifiable_bid_absent: 'Identifiable bid absent',
  mex_pair_depth_checked: 'MEX pair depth measured',
  mex_outperforming_egld: 'MEX outperforming EGLD',
  xegld_supply_redemption_without_price_driver:
    'XEGLD redeemed with no price driver',
  xegld_redemption_destination_traced: 'XEGLD redemption destination traced',
  usdt_supply_burn: 'USDT supply burn',
  bridged_stablecoin_outflow: 'Bridged stablecoins leaving',
  stablecoin_supply: 'Stablecoin supply',
  participation_inertia_confirmed: 'Participation inertia confirmed',
  supply_channels_switched_off_together: 'Every supply channel switched off',
  recovery_reclassified_as_bear_rally: 'Recovery reclassified as a bear rally',
  egld_specific_outperformance: 'EGLD-specific outperformance',
  egld_leadership_thesis_failed: 'EGLD leadership thesis failed',
  capitulation_bounce_failed: 'Capitulation bounce failed',
  yield_chase_migration: 'Yield-chasing migration',
  yield_chase_validator_migration: 'Yield-chasing validator migration',
  hatom_lending_egld_tvl: 'Hatom Lending TVL (in EGLD)',
  hatom_lsd_tvl_in_egld: 'Hatom liquid-staking TVL (in EGLD)',
  withdrawal_breadth: 'Withdrawal breadth',
  cross_exchange_otc_pipeline: 'Cross-exchange OTC pipeline',
}

/**
 * Short explanations for terms the report leans on. Rendered as a subtitle so a
 * first-time reader is not expected to already know the model's vocabulary.
 */
export const GLOSSARY: Record<string, string> = {
  net_one_way:
    'Desk flow that does NOT return to the venue that supplied it — the part that is genuine distribution',
  gross_throughput: 'Every leg the OTC desks moved, round trips included',
  identifiable_bid:
    'The one large buyer this model can name and track (a mega-whale fed through a Coinbase routing wallet)',
  turnover_ratio: 'Share of the DEX pool depth that actually trades each day',
  circularity:
    'Share of desk flow that round-trips back to the venue that supplied it',
  unbonding: 'Stake that has left a provider but is not yet withdrawable',
  direct_node: 'Stake run on self-operated validators rather than via delegation',
}

function titleCaseWord(word: string): string {
  const lower = word.toLowerCase()
  if (ACRONYMS[lower]) return ACRONYMS[lower]
  if (/^\d/.test(lower)) return lower
  return lower.charAt(0).toUpperCase() + lower.slice(1)
}

/**
 * Turn a machine key into a human label.
 *  otc_netting_window_must_match_the_wave → "Netting window must match the wave, not the week" (override)
 *  xoxno_lsd_supply_collapse              → "XOXNO LSD supply collapse"
 *  "Gate.io balance -21.6% WoW"           → unchanged (already prose)
 */
export function humanizeKey(raw: string | null | undefined): string {
  if (!raw) return ''
  if (OVERRIDES[raw]) return OVERRIDES[raw]

  // Already a human sentence (older reports wrote these by hand).
  if (/\s/.test(raw) && !/^[A-Z_]+$/.test(raw)) {
    return raw.charAt(0).toUpperCase() + raw.slice(1)
  }

  const parts = raw.split(/[_\-.]/).filter(Boolean)
  if (parts.length === 0) return raw

  const words = parts.map((p, i) => {
    const lower = p.toLowerCase()
    if (ACRONYMS[lower]) return ACRONYMS[lower]
    // Keep small joining words lowercase unless they lead.
    if (i > 0 && ['the', 'a', 'of', 'to', 'and', 'as', 'in', 'at', 'by', 'must', 'was'].includes(lower)) {
      return lower
    }
    return i === 0 ? titleCaseWord(p) : lower
  })

  const label = words.join(' ')
  return label.charAt(0).toUpperCase() + label.slice(1)
}

/** True when the humanized form differs enough that showing the raw key adds information. */
export function keyDiffers(raw: string | null | undefined): boolean {
  if (!raw) return false
  return humanizeKey(raw) !== raw
}

/** Gloss for a key, matched on substrings of the raw slug. */
export function glossFor(raw: string | null | undefined): string | null {
  if (!raw) return null
  const k = raw.toLowerCase()
  if (k.includes('net_one_way')) return GLOSSARY.net_one_way
  if (k.includes('turnover')) return GLOSSARY.turnover_ratio
  if (k.includes('identifiable_bid')) return GLOSSARY.identifiable_bid
  if (k.includes('circular')) return GLOSSARY.circularity
  if (k.includes('unbond')) return GLOSSARY.unbonding
  if (k.includes('direct_node')) return GLOSSARY.direct_node
  if (k.includes('gross')) return GLOSSARY.gross_throughput
  return null
}
