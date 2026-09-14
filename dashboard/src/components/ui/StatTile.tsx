/**
 * The stat tile used across the OTC, market-scale and contract-event panels.
 * One scale everywhere: 10px eyebrow, 19px mono hero, 11px secondary line.
 */
export function StatTile({
  label,
  value,
  unit,
  sub,
  accent,
  title,
  children,
}: {
  label: string
  value?: string
  unit?: string
  sub?: React.ReactNode
  accent?: 'cyan' | 'down' | 'critical'
  /** Full-precision value for hover and screen readers. */
  title?: string
  /** Extra inline content after the hero (e.g. a delta chip). */
  children?: React.ReactNode
}) {
  const color =
    accent === 'cyan'
      ? 'var(--color-accent-cyan)'
      : accent === 'down'
        ? 'var(--color-down)'
        : accent === 'critical'
          ? 'var(--color-severity-critical)'
          : 'var(--color-text-primary)'
  return (
    <div className="bg-bg-elevated border border-border rounded-md p-3 min-w-0">
      <div className="text-[10px] text-text-muted uppercase tracking-widest">{label}</div>
      <div className="mt-1.5 flex items-baseline gap-x-1.5 gap-y-1 flex-wrap">
        {value != null && (
          <span className="font-mono text-[19px] font-semibold leading-none" style={{ color }} title={title}>
            {value}
          </span>
        )}
        {unit && <span className="hero-unit !ml-0">{unit}</span>}
        {children}
      </div>
      {sub && <div className="mt-1 text-[11px] text-text-secondary leading-snug">{sub}</div>}
    </div>
  )
}
