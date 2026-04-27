import { formatDelta } from '../../lib/formatters'

interface MetricCardProps {
  label: string
  value: string
  unit?: string
  delta?: number | null
  deltaFormat?: 'pct' | 'number' | 'pp'
  /** Optional secondary line (e.g. "10K – 100K EGLD") */
  sub?: string
  /** Optional tone for the value (used for net flows, etc.) */
  tone?: 'neutral' | 'up' | 'down'
  className?: string
  /** When true, draws a thin accent stripe on the left */
  accent?: boolean
}

export function MetricCard({
  label,
  value,
  unit,
  delta,
  deltaFormat = 'pct',
  sub,
  tone = 'neutral',
  className = '',
  accent = false,
}: MetricCardProps) {
  const showDelta = delta !== undefined
  const deltaResult = showDelta ? formatDelta(delta ?? null, deltaFormat) : null

  const toneClass =
    tone === 'up'
      ? 'text-up'
      : tone === 'down'
        ? 'text-down'
        : 'text-text-primary'

  return (
    <div
      className={`relative bg-surface border border-border rounded-md px-4 py-3 flex flex-col gap-1.5 card-hover ${className}`}
    >
      {accent && (
        <span className="absolute left-0 top-2 bottom-2 w-[2px] bg-accent-cyan/60 rounded" />
      )}

      <span className="eyebrow">{label}</span>

      <div className="flex items-baseline gap-1.5">
        <span className={`hero-number ${toneClass}`}>{value}</span>
        {unit && <span className="hero-unit">{unit}</span>}
      </div>

      {showDelta && deltaResult && (
        <span className={`text-[11px] font-mono ${deltaResult.color}`}>
          {deltaResult.arrow === 'up' && '▲ '}
          {deltaResult.arrow === 'down' && '▼ '}
          {deltaResult.text}
        </span>
      )}

      {sub && (
        <span className="text-[11px] text-text-muted font-mono">{sub}</span>
      )}
    </div>
  )
}
