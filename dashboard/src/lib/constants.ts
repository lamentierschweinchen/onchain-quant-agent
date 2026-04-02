// Dashboard-wide constants and URL helpers.

export const EXPLORER_BASE = 'https://explorer.multiversx.com'

export function accountUrl(address: string): string {
  return `${EXPLORER_BASE}/accounts/${address}`
}

export function txUrl(hash: string): string {
  return `${EXPLORER_BASE}/transactions/${hash}`
}

// ---------------------------------------------------------------------------
// Severity palette
// ---------------------------------------------------------------------------

export const SEVERITY_COLORS = {
  critical: '#EF4444',
  high: '#F97316',
  medium: '#EAB308',
  low: '#3B82F6',
  info: '#6B7280',
} as const

export const SEVERITY_BG_CLASSES = {
  critical: 'bg-severity-critical/10 border-severity-critical/30',
  high: 'bg-severity-high/10 border-severity-high/30',
  medium: 'bg-severity-medium/10 border-severity-medium/30',
  low: 'bg-severity-low/10 border-severity-low/30',
  info: 'bg-severity-info/10 border-severity-info/30',
} as const

// ---------------------------------------------------------------------------
// Category colours (for charts / labels)
// ---------------------------------------------------------------------------

export const CATEGORY_COLORS = {
  exchange: '#3B82F6',
  defi: '#A855F7',
  team: '#22C55E',
  system: '#6B7280',
  other: '#94A3B8',
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
  'token-defi': 'Tokens',
  'anomalies-watchlist': 'Alerts',
  'meta-learning': 'Meta',
}
