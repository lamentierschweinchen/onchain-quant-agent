// Dashboard-wide constants and URL helpers.

export const EXPLORER_BASE = 'https://explorer.multiversx.com'

export function accountUrl(address: string): string {
  return `${EXPLORER_BASE}/accounts/${address}`
}

export function txUrl(hash: string): string {
  return `${EXPLORER_BASE}/transactions/${hash}`
}

export function tokenUrl(identifier: string): string {
  return `${EXPLORER_BASE}/tokens/${identifier}`
}

// ---------------------------------------------------------------------------
// Severity palette — only severity uses these; everything else stays neutral
// ---------------------------------------------------------------------------

export const SEVERITY_COLORS = {
  critical: '#F4525A',
  high: '#FB8534',
  medium: '#E8B43A',
  low: '#5896F2',
  info: '#6B7587',
} as const

export const SEVERITY_LABELS = {
  critical: 'CRIT',
  high: 'HIGH',
  medium: 'MED',
  low: 'LOW',
  info: 'INFO',
} as const

// ---------------------------------------------------------------------------
// Category colours — restrained, used only for the executive summary
// ---------------------------------------------------------------------------

export const CATEGORY_COLORS = {
  exchange: '#5896F2',
  defi: '#B975F0',
  team: '#34D196',
  system: '#6B7587',
  other: '#8B97AC',
} as const

// ---------------------------------------------------------------------------
// Whale tier colours
// ---------------------------------------------------------------------------

export const TIER_COLORS = {
  mega_whale: '#F4525A',
  large_whale: '#FB8534',
  mid_whale: '#E8B43A',
} as const

export const TIER_LABELS = {
  mega_whale: 'MEGA',
  large_whale: 'LARGE',
  mid_whale: 'MID',
} as const

export const TIER_DESCRIPTIONS = {
  mega_whale: '> 1M EGLD',
  large_whale: '100K – 1M',
  mid_whale: '10K – 100K',
} as const

// ---------------------------------------------------------------------------
// Health signal colours
// ---------------------------------------------------------------------------

export const HEALTH_COLORS = {
  growing: '#34D196',
  flat: '#8B97AC',
  shrinking: '#FB8534',
  spiking: '#23F7DD',
  draining: '#F4525A',
} as const

// ---------------------------------------------------------------------------
// Navigation sections
// ---------------------------------------------------------------------------

export const SECTION_IDS = [
  'executive-summary',
  'network-health',
  'whale-intelligence',
  'staking-intelligence',
  'token-defi',
  'anomalies-watchlist',
  'meta-learning',
] as const

export const SECTION_LABELS: Record<string, string> = {
  'executive-summary': 'Summary',
  'network-health': 'Network',
  'whale-intelligence': 'Whales',
  'staking-intelligence': 'Staking',
  'token-defi': 'Tokens & DeFi',
  'anomalies-watchlist': 'Alerts & Trends',
  'meta-learning': 'Meta',
}
