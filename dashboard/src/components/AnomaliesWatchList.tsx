import type {
  Anomaly,
  AnomalySeverity,
  WatchItem,
  TrendIndicators,
} from '../types/report'
import { SeverityBadge } from './ui/SeverityBadge'
import { NullState } from './ui/NullState'
import {
  formatPct,
  formatNumber,
  formatEgldBare,
  formatZScore,
} from '../lib/formatters'

const SEVERITY_ORDER: Record<AnomalySeverity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
}

const METHOD_LABELS: Record<string, string> = {
  z_score: 'Z-SCORE',
  percent_threshold: '% THRESHOLD',
  rule_based: 'RULE',
}

interface Props {
  anomalies: Anomaly[]
  watchList: WatchItem[]
  trends?: TrendIndicators | null
}

function CardSection({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle?: string
  children: React.ReactNode
}) {
  return (
    <section className="card overflow-hidden">
      <header className="px-4 py-2.5 border-b border-border bg-bg-elevated">
        <h3 className="text-[12px] font-semibold text-text-primary tracking-tight">
          {title}
        </h3>
        {subtitle && (
          <p className="text-[10px] text-text-muted mt-0.5">{subtitle}</p>
        )}
      </header>
      {children}
    </section>
  )
}

function MethodBadge({ method }: { method: string | null | undefined }) {
  if (!method) return null
  return (
    <span className="text-[9.5px] font-mono font-semibold tracking-widest text-text-muted bg-bg-elevated border border-border px-1.5 py-[1px] rounded">
      {METHOD_LABELS[method] ?? method.toUpperCase()}
    </span>
  )
}

export function AnomaliesWatchList({ anomalies, watchList, trends }: Props) {
  const sorted = [...anomalies].sort(
    (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity],
  )

  return (
    <div className="space-y-4">
      {/* ---------------- Anomalies ---------------- */}
      <CardSection
        title="Anomaly Alerts"
        subtitle="Z-score (≥4 data points) · % threshold (graceful degradation) · rule-based"
      >
        <div className="p-4">
          {sorted.length === 0 ? (
            <NullState message="No anomalies detected this week." />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {sorted.map((anomaly, idx) => (
                <article
                  key={idx}
                  className="bg-bg-elevated rounded border border-border p-3 space-y-2"
                >
                  {/* header */}
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-medium text-text-primary text-[12.5px]">
                      {anomaly.metric}
                    </span>
                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <MethodBadge method={anomaly.method} />
                      <SeverityBadge severity={anomaly.severity} />
                    </div>
                  </div>

                  {/* numeric panel */}
                  <div className="grid grid-cols-3 gap-2 text-[11px] font-mono pt-1 border-t border-border-subtle">
                    <div>
                      <span className="eyebrow">Current</span>
                      <p className="text-text-primary tabular">
                        {fmtVal(anomaly.current_value)}
                      </p>
                    </div>
                    <div>
                      <span className="eyebrow">
                        {anomaly.average_value != null ? 'Mean' : 'Previous'}
                      </span>
                      <p className="text-text-secondary tabular">
                        {fmtVal(
                          anomaly.average_value ?? anomaly.previous_value ?? null,
                        )}
                      </p>
                    </div>
                    <div>
                      <span className="eyebrow">
                        {anomaly.z_score != null ? 'Z-Score' : 'Δ %'}
                      </span>
                      <p
                        className={`tabular font-semibold ${anomaly.z_score != null && Math.abs(anomaly.z_score) >= 2 ? 'text-severity-medium' : 'text-text-secondary'}`}
                      >
                        {anomaly.z_score != null
                          ? formatZScore(anomaly.z_score)
                          : anomaly.change_pct != null
                            ? `${anomaly.change_pct >= 0 ? '+' : ''}${formatPct(anomaly.change_pct)}`
                            : '—'}
                      </p>
                    </div>
                  </div>

                  {/* description */}
                  <p className="text-[12px] text-text-secondary leading-relaxed">
                    {anomaly.description}
                  </p>
                </article>
              ))}
            </div>
          )}
        </div>
      </CardSection>

      {/* ---------------- Trend Indicators ---------------- */}
      {trends && hasAnyTrend(trends) && (
        <CardSection
          title="Trend Indicators"
          subtitle="Forward-looking multi-week trajectories — distinct from point-in-time anomalies"
        >
          <div className="p-4 space-y-4">
            {/* Accelerating exchange outflows */}
            {trends.accelerating_exchange_outflows &&
              trends.accelerating_exchange_outflows.length > 0 && (
                <div>
                  <p className="eyebrow mb-2">Accelerating Exchange Outflows</p>
                  <div className="space-y-2">
                    {trends.accelerating_exchange_outflows.map((t) => (
                      <div
                        key={t.exchange}
                        className="flex items-start gap-3 p-2 rounded bg-bg-elevated border border-border"
                      >
                        <div className="flex-shrink-0 w-12 text-center">
                          <span className="text-[10px] eyebrow">Wks</span>
                          <p className="text-[18px] font-mono font-bold text-severity-medium tabular">
                            {t.weeks_in_trend}
                          </p>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2 flex-wrap">
                            <span className="font-medium text-text-primary text-[12.5px]">
                              {t.exchange}
                            </span>
                            {t.cumulative_change_pct != null && (
                              <span
                                className={`text-[11px] font-mono tabular ${
                                  t.cumulative_change_pct < 0
                                    ? 'text-down'
                                    : 'text-up'
                                }`}
                              >
                                {t.cumulative_change_pct >= 0 ? '+' : ''}
                                {t.cumulative_change_pct.toFixed(1)}% cum
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-text-muted">{t.trend}</p>
                          {t.interpretation && (
                            <p className="text-[11.5px] text-text-secondary mt-1 italic">
                              {t.interpretation}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            {/* Validator movements */}
            {trends.validator_movements && (
              <div>
                <p className="eyebrow mb-2">Validator Movements</p>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
                  <div className="bg-bg-elevated border border-border rounded p-2.5">
                    <span className="eyebrow">Joining</span>
                    <p className="font-mono text-[18px] text-up tabular font-bold">
                      {trends.validator_movements.providers_joining ?? '—'}
                    </p>
                  </div>
                  <div className="bg-bg-elevated border border-border rounded p-2.5">
                    <span className="eyebrow">Leaving</span>
                    <p className="font-mono text-[18px] text-down tabular font-bold">
                      {trends.validator_movements.providers_leaving ?? '—'}
                    </p>
                  </div>
                  <div className="bg-bg-elevated border border-border rounded p-2.5 col-span-2">
                    <span className="eyebrow">Net Change</span>
                    <p
                      className={`font-mono text-[18px] tabular font-bold ${
                        (trends.validator_movements.net_provider_change ?? 0) >
                        0
                          ? 'text-up'
                          : (trends.validator_movements.net_provider_change ??
                                0) < 0
                            ? 'text-down'
                            : 'text-flat'
                      }`}
                    >
                      {trends.validator_movements.net_provider_change != null
                        ? trends.validator_movements.net_provider_change >= 0
                          ? `+${trends.validator_movements.net_provider_change}`
                          : trends.validator_movements.net_provider_change
                        : '—'}
                    </p>
                  </div>
                </div>

                {trends.validator_movements.notable_joiners &&
                  trends.validator_movements.notable_joiners.length > 0 && (
                    <div className="mt-2">
                      <span className="text-[10px] text-text-muted uppercase tracking-wider">
                        Notable joiners
                      </span>
                      <ul className="text-[12px] mt-1 space-y-0.5">
                        {trends.validator_movements.notable_joiners.map((p) => (
                          <li key={p.identity} className="flex justify-between font-mono">
                            <span className="text-text-secondary">
                              {p.name ?? p.identity}
                            </span>
                            <span className="text-up tabular">
                              {formatEgldBare(p.locked_egld)} EGLD
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                {trends.validator_movements.notable_leavers &&
                  trends.validator_movements.notable_leavers.length > 0 && (
                    <div className="mt-2">
                      <span className="text-[10px] text-text-muted uppercase tracking-wider">
                        Notable leavers
                      </span>
                      <ul className="text-[12px] mt-1 space-y-0.5">
                        {trends.validator_movements.notable_leavers.map((p) => (
                          <li key={p.identity} className="flex justify-between font-mono">
                            <span className="text-text-secondary">
                              {p.name ?? p.identity}
                            </span>
                            <span className="text-down tabular">
                              -{formatEgldBare(p.previous_locked_egld)} EGLD
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
              </div>
            )}

            {/* Token supply events */}
            {trends.token_supply_events &&
              trends.token_supply_events.length > 0 && (
                <div>
                  <p className="eyebrow mb-2">Token Supply Events</p>
                  <div className="space-y-1.5">
                    {trends.token_supply_events.map((e, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-3 px-2.5 py-2 bg-bg-elevated border border-border rounded text-[12px]"
                      >
                        <span className="font-mono text-text-primary text-[11px] uppercase tracking-wider w-16 flex-shrink-0">
                          {e.event}
                        </span>
                        <span className="font-medium text-text-primary flex-shrink-0">
                          {e.name}{' '}
                          <span className="text-text-muted font-mono text-[10px]">
                            ({e.identifier})
                          </span>
                        </span>
                        {e.magnitude_pct != null && (
                          <span
                            className={`font-mono tabular text-[11px] flex-shrink-0 ${
                              e.event === 'mint' || e.event === 'unlock'
                                ? 'text-up'
                                : 'text-down'
                            }`}
                          >
                            {e.magnitude_pct >= 0 ? '+' : ''}
                            {e.magnitude_pct.toFixed(2)}%
                          </span>
                        )}
                        <span className="text-text-secondary text-[11.5px] truncate">
                          {e.description}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            {/* Consecutive streaks */}
            {trends.consecutive_streaks &&
              trends.consecutive_streaks.length > 0 && (
                <div>
                  <p className="eyebrow mb-2">Consecutive Streaks</p>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {trends.consecutive_streaks.map((s, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-3 p-2.5 bg-bg-elevated border border-border rounded"
                      >
                        <div className="flex-shrink-0 w-10 text-center">
                          <span
                            className={`text-[18px] font-bold ${
                              s.direction === 'up'
                                ? 'text-up'
                                : s.direction === 'down'
                                  ? 'text-down'
                                  : 'text-flat'
                            }`}
                          >
                            {s.direction === 'up'
                              ? '▲'
                              : s.direction === 'down'
                                ? '▼'
                                : '—'}
                          </span>
                          <p className="text-[10px] text-text-muted font-mono">
                            {s.weeks}w
                          </p>
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2 flex-wrap">
                            <span className="font-medium text-text-primary text-[12.5px]">
                              {s.metric}
                            </span>
                            {s.cumulative_change_pct != null && (
                              <span
                                className={`text-[11px] font-mono tabular ${
                                  s.cumulative_change_pct >= 0
                                    ? 'text-up'
                                    : 'text-down'
                                }`}
                              >
                                {s.cumulative_change_pct >= 0 ? '+' : ''}
                                {s.cumulative_change_pct.toFixed(1)}%
                              </span>
                            )}
                          </div>
                          {s.interpretation && (
                            <p className="text-[11.5px] text-text-secondary mt-0.5">
                              {s.interpretation}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            {/* Regime shifts */}
            {trends.regime_shifts && trends.regime_shifts.length > 0 && (
              <div>
                <p className="eyebrow mb-2">Regime Shifts</p>
                <div className="space-y-1.5">
                  {trends.regime_shifts.map((r, i) => (
                    <div
                      key={i}
                      className="p-2.5 bg-accent-cyan/5 border border-accent-cyan/30 rounded"
                    >
                      <div className="flex items-center justify-between gap-2 flex-wrap">
                        <span className="font-medium text-text-primary text-[12.5px]">
                          {r.metric}
                        </span>
                        <span className="font-mono text-[11px] text-accent-cyan tabular">
                          {r.before_value != null ? fmtVal(r.before_value) : '—'}{' '}
                          → {fmtVal(r.after_value)}
                        </span>
                      </div>
                      <p className="text-[11.5px] text-text-secondary mt-0.5">
                        {r.description}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CardSection>
      )}

      {/* ---------------- Watch List ---------------- */}
      <CardSection
        title="Watch List"
        subtitle="Persistent items tracked across weeks"
      >
        <div className="p-4">
          {watchList.length === 0 ? (
            <NullState message="Nothing on the watch list." />
          ) : (
            <ol className="space-y-2">
              {watchList.map((item, idx) => (
                <li
                  key={idx}
                  className="bg-bg-elevated rounded border border-border p-3 flex items-start gap-3"
                >
                  <div className="flex-shrink-0 bg-accent-cyan/15 text-accent-cyan rounded w-9 h-9 flex flex-col items-center justify-center font-mono">
                    <span className="text-[14px] font-bold leading-none">
                      {item.weeks_on_list}
                    </span>
                    <span className="text-[8px] tracking-widest leading-none mt-0.5">
                      WK
                    </span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-medium text-text-primary text-[12.5px]">
                      {item.item}
                    </p>
                    <p className="text-[11.5px] text-text-secondary mt-1 leading-relaxed">
                      {item.reason}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          )}
        </div>
      </CardSection>
    </div>
  )
}

function fmtVal(v: number | null | undefined): string {
  if (v == null) return '—'
  const abs = Math.abs(v)
  if (abs >= 1_000_000) return formatNumber(v)
  if (abs >= 1_000) return formatNumber(v)
  if (Number.isInteger(v)) return v.toLocaleString('en-US')
  if (abs < 1) return v.toFixed(4)
  return v.toFixed(2)
}

function hasAnyTrend(t: TrendIndicators): boolean {
  return Boolean(
    (t.accelerating_exchange_outflows?.length ?? 0) > 0 ||
      t.validator_movements ||
      (t.token_supply_events?.length ?? 0) > 0 ||
      (t.consecutive_streaks?.length ?? 0) > 0 ||
      (t.regime_shifts?.length ?? 0) > 0,
  )
}
