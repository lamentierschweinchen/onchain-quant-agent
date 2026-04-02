import { formatDelta } from '../../lib/formatters'

interface MetricCardProps {
  label: string
  value: string
  delta?: number | null
  deltaFormat?: 'pct' | 'number'
  className?: string
}

export function MetricCard({
  label,
  value,
  delta,
  deltaFormat = 'pct',
  className = '',
}: MetricCardProps) {
  // delta undefined means "don't show delta", null means "baseline"
  const showDelta = delta !== undefined
  const deltaResult = showDelta ? formatDelta(delta ?? null, deltaFormat) : null

  return (
    <div
      className={`bg-surface rounded-lg border border-border p-4 flex flex-col gap-1 ${className}`}
    >
      <span className="text-2xl font-mono font-bold text-text-primary leading-none">
        {value}
      </span>
      <span className="text-sm text-text-secondary">{label}</span>
      {showDelta && deltaResult && (
        <span className={`text-xs font-medium mt-1 ${deltaResult.color}`}>
          {deltaResult.arrow === 'up' && '▲ '}
          {deltaResult.arrow === 'down' && '▼ '}
          {deltaResult.text}
        </span>
      )}
    </div>
  )
}
