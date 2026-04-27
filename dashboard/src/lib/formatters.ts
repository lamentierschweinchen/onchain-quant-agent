// Pure formatting utilities for the MultiversX Intelligence Dashboard.

/**
 * Format an EGLD amount with precision tiers.
 *  >= 1B  → "1.45B EGLD"
 *  >= 1M  → "14.25M EGLD"
 *  >= 1K  → "234.5K EGLD"
 *  < 1K   → "495.27 EGLD"
 */
export function formatEgld(value: number): string {
  if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)}B EGLD`
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M EGLD`
  if (value >= 10_000) return `${(value / 1_000).toFixed(1)}K EGLD`
  return `${value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })} EGLD`
}

/** EGLD without the "EGLD" suffix — for tables where the unit is a column header */
export function formatEgldBare(value: number): string {
  if (value >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)}B`
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M`
  if (value >= 10_000) return `${(value / 1_000).toFixed(1)}K`
  return value.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 2 })
}

/**
 * Format a USD value.
 *  >= 1B → "$2.4B"
 *  >= 1M → "$109.1M"
 *  >= 1K → "$213.0K"
 *  < 1K  → "$3.68"
 */
export function formatUsd(value: number): string {
  if (value >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(2)}B`
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`
  if (value >= 1) return `$${value.toFixed(2)}`
  if (value >= 0.001) return `$${value.toFixed(4)}`
  // Very small prices — scientific
  return `$${value.toExponential(2)}`
}

/** Compact USD without sign — for chart axes */
export function formatUsdCompact(value: number): string {
  const abs = Math.abs(value)
  if (abs >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(1)}B`
  if (abs >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`
  if (abs >= 1_000) return `${Math.round(value / 1_000)}K`
  return String(Math.round(value))
}

/**
 * Format a percentage.
 * @param value   The raw value.
 * @param isRatio When true, multiply by 100 before formatting (e.g. 0.48 → "48.0%").
 */
export function formatPct(value: number, isRatio = false): string {
  const display = isRatio ? value * 100 : value
  return `${display.toFixed(1)}%`
}

/** Percent with 2 decimals — useful for HHI shares */
export function formatPct2(value: number, isRatio = false): string {
  const display = isRatio ? value * 100 : value
  return `${display.toFixed(2)}%`
}

export interface DeltaResult {
  text: string
  color: string
  arrow: 'up' | 'down' | null
}

export function formatDelta(
  value: number | null,
  format: 'pct' | 'number' | 'pp',
): DeltaResult {
  if (value === null || value === undefined) {
    return { text: 'Baseline', color: 'text-text-muted', arrow: null }
  }

  const sign = value >= 0 ? '+' : ''
  let text: string
  if (format === 'pct') text = `${sign}${value.toFixed(2)}%`
  else if (format === 'pp') text = `${sign}${value.toFixed(2)}pp`
  else if (Math.abs(value) >= 1000) text = `${sign}${formatNumber(value)}`
  else text = `${sign}${value.toFixed(0)}`

  if (value > 0) return { text, color: 'text-up', arrow: 'up' }
  if (value < 0) return { text, color: 'text-down', arrow: 'down' }
  return { text, color: 'text-flat', arrow: null }
}

/** Truncate bech32 address: erd1abcd...XXXXX */
export function truncateAddress(address: string, head = 8, tail = 5): string {
  if (address.length <= head + tail + 3) return address
  return `${address.slice(0, head)}…${address.slice(-tail)}`
}

/**
 * Format a raw number with K/M/B suffixes.
 * 596192455 → "596.2M"
 * 9182828   → "9.18M"
 * 306       → "306"
 */
export function formatNumber(value: number): string {
  const abs = Math.abs(value)
  if (abs >= 1_000_000_000) return `${(value / 1_000_000_000).toFixed(2)}B`
  if (abs >= 1_000_000) return `${(value / 1_000_000).toFixed(2)}M`
  if (abs >= 10_000) return `${(value / 1_000).toFixed(1)}K`
  if (abs >= 1_000) return `${(value / 1_000).toFixed(2)}K`
  return Math.round(value).toLocaleString('en-US')
}

/** Long form with full digits and commas — for "exact" displays */
export function formatNumberFull(value: number): string {
  return Math.round(value).toLocaleString('en-US')
}

/**
 * Format a YYYY-MM-DD date string to "Apr 27, 2026".
 */
export function formatDate(dateStr: string): string {
  const date = new Date(`${dateStr}T12:00:00Z`)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  })
}

/** Short date "Apr 27" without year — for compact ticker labels */
export function formatDateShort(dateStr: string): string {
  const date = new Date(`${dateStr}T12:00:00Z`)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  })
}

/**
 * Format an ISO 8601 timestamp to "Apr 2 17:08 UTC".
 */
export function formatTimestamp(iso: string): string {
  const date = new Date(iso)
  const datePart = date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  })
  const hours = String(date.getUTCHours()).padStart(2, '0')
  const minutes = String(date.getUTCMinutes()).padStart(2, '0')
  return `${datePart} ${hours}:${minutes}`
}

/**
 * Round a service fee — handles floating-point imprecision.
 * 7.920000000000001 → "7.9%"
 */
export function cleanServiceFee(fee: number): string {
  return `${parseFloat(fee.toFixed(2))}%`
}

/** Format a z-score with sign and sigma symbol */
export function formatZScore(z: number): string {
  const sign = z >= 0 ? '+' : ''
  return `${sign}${z.toFixed(2)}σ`
}

/** Format a tier label for display */
export function formatTier(tier: string | null | undefined): string {
  if (!tier) return ''
  return tier
    .replace('_whales', '')
    .replace('_whale', '')
    .replace(/^./, (s) => s.toUpperCase())
}
