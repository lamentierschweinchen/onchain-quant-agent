import type { Anomaly, AnomalySeverity, WatchItem } from '../types/report'
import { SeverityBadge } from './ui/SeverityBadge'
import { NullState } from './ui/NullState'

// Sort order for anomaly severity
const SEVERITY_ORDER: Record<AnomalySeverity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
}

interface AnomaliesWatchListProps {
  anomalies: Anomaly[]
  watchList: WatchItem[]
}

export function AnomaliesWatchList({ anomalies, watchList }: AnomaliesWatchListProps) {
  const sorted = [...anomalies].sort(
    (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity],
  )

  return (
    <div className="space-y-8">
      {/* ------------------------------------------------------------------ */}
      {/* Anomalies                                                            */}
      {/* ------------------------------------------------------------------ */}
      <section>
        <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-widest mb-4">
          Anomalies
        </h3>

        {sorted.length === 0 ? (
          <NullState message="No anomalies detected this week." />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {sorted.map((anomaly, idx) => (
              <div
                key={idx}
                className="bg-surface rounded-lg p-4 border border-border"
              >
                {/* Top row: metric name + severity badge */}
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-text-primary text-sm">
                    {anomaly.metric}
                  </span>
                  <SeverityBadge severity={anomaly.severity} />
                </div>

                {/* Current value */}
                <p className="font-mono text-sm text-text-primary">
                  Current: {anomaly.current_value}
                </p>

                {/* Z-score and average (or null-state) */}
                {anomaly.z_score !== null ? (
                  <div className="mt-1 space-y-0.5">
                    <p className="font-mono text-sm text-text-secondary">
                      Z-score: {anomaly.z_score.toFixed(2)}
                    </p>
                    {anomaly.average_value !== null && (
                      <p className="font-mono text-sm text-text-secondary">
                        Average: {anomaly.average_value}
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="mt-1">
                    <NullState message="Baseline — anomaly tracking starts next week" />
                  </div>
                )}

                {/* Description */}
                <p className="text-sm text-text-secondary mt-2 leading-relaxed">
                  {anomaly.description}
                </p>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Watch List                                                           */}
      {/* ------------------------------------------------------------------ */}
      <section>
        <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-widest mb-4">
          Watch List
        </h3>

        {watchList.length === 0 ? (
          <NullState message="Nothing on the watch list." />
        ) : (
          <ol className="space-y-3">
            {watchList.map((item, idx) => (
              <li
                key={idx}
                className="bg-surface rounded-lg p-3 border border-border flex items-start gap-3"
              >
                {/* Weeks-on-list counter badge */}
                <div className="flex-shrink-0 bg-accent-cyan/20 text-accent-cyan rounded-full w-8 h-8 flex items-center justify-center text-sm font-bold">
                  {item.weeks_on_list}
                </div>

                {/* Item text + reason */}
                <div className="min-w-0">
                  <p className="font-medium text-text-primary text-sm">
                    {item.item}
                  </p>
                  <p className="text-sm text-text-secondary mt-0.5">
                    {item.reason}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  )
}
