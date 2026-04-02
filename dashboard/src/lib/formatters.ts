// Pure formatting utilities for the MultiversX Intelligence Dashboard.

/**
 * Format an EGLD amount.
 * - >= 1,000,000 → "14.25M EGLD"
 * - < 1,000,000  → "495,145.27 EGLD"
 */
export function formatEgld(value: number): string {
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(2)}M EGLD`
  }
  return `${value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} EGLD`
}

/**
 * Format a USD value.
 * - >= 1,000,000 → "$109.1M"
 * - >= 1,000    → "$213.0K"
 * - < 1,000     → "$3.68"
 */
export function formatUsd(value: number): string {
  if (value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`
  }
  if (value >= 1_000) {
    return `$${(value / 1_000).toFixed(1)}K`
  }
  return `$${value.toFixed(2)}`
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

export interface DeltaResult {
  text: string
  color: string
  arrow: 'up' | 'down' | null
}

/**
 * Format a week-over-week delta with direction colour and arrow.
 * - null → baseline indicator
 * - positive → green / up
 * - negative → red / down
 */
export function formatDelta(
  value: number | null,
  format: 'pct' | 'number',
): DeltaResult {
  if (value === null) {
    return { text: 'Baseline', color: 'text-text-secondary', arrow: null }
  }

  const sign = value >= 0 ? '+' : ''
  const text =
    format === 'pct'
      ? `${sign}${value.toFixed(1)}%`
      : `${sign}${value.toFixed(1)}`

  if (value > 0) {
    return { text, color: 'text-green-400', arrow: 'up' }
  }
  if (value < 0) {
    return { text, color: 'text-red-400', arrow: 'down' }
  }
  // Exactly zero — neutral
  return { text, color: 'text-text-secondary', arrow: null }
}

/**
 * Shorten a bech32 address for display.
 * "erd1qyu5wthldzr8wx5c9ucg8kjagg0jfs53s8nr3zpz3hypefsdd8ssycr6th"
 * → "erd1qyu5wt...cr6th"
 */
export function truncateAddress(address: string): string {
  if (address.length <= 16) return address
  return `${address.slice(0, 10)}...${address.slice(-5)}`
}

/**
 * Format a raw number with K/M suffixes.
 * - >= 1,000,000 → "596.2M"
 * - >= 1,000     → "9.18K" / "9.18M"  (see examples)
 * - < 1,000      → "306"
 *
 * Examples from spec:
 *   596192455 → "596.2M"
 *   9182828   → "9.18M"
 *   306       → "306"
 */
export function formatNumber(value: number): string {
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1)}M`
  }
  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(2)}K`
  }
  return String(Math.round(value))
}

/**
 * Format a YYYY-MM-DD date string to a human-readable form.
 * "2026-04-02" → "Apr 2, 2026"
 */
export function formatDate(dateStr: string): string {
  // Parse as UTC noon to avoid timezone boundary issues.
  const date = new Date(`${dateStr}T12:00:00Z`)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  })
}

/**
 * Format an ISO 8601 timestamp.
 * "2026-04-02T17:08:50.860Z" → "Apr 2, 2026 17:08"
 */
export function formatTimestamp(iso: string): string {
  const date = new Date(iso)
  const datePart = date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  })
  const hours = String(date.getUTCHours()).padStart(2, '0')
  const minutes = String(date.getUTCMinutes()).padStart(2, '0')
  return `${datePart} ${hours}:${minutes}`
}

/**
 * Round a service fee to one decimal place and append "%".
 * Handles floating-point imprecision: 7.920000000000001 → "7.9%"
 */
export function cleanServiceFee(fee: number): string {
  return `${parseFloat(fee.toFixed(1))}%`
}
