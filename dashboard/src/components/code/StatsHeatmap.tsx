import type { ProgressStats } from '../../types/stats'

interface StatsHeatmapProps {
  dailyCommits: number[]
  window: ProgressStats['window']
}

/**
 * Maps a commit count to an opacity. Quintile-style bins so the scale
 * stays readable even with a few outlier days.
 */
function intensity(count: number, max: number): number {
  if (count === 0) return 0
  if (max <= 1) return 0.4
  const ratio = count / max
  if (ratio < 0.15) return 0.18
  if (ratio < 0.35) return 0.34
  if (ratio < 0.6) return 0.55
  if (ratio < 0.85) return 0.78
  return 1
}

function dayLabel(start: string, daysFromStart: number): string {
  const d = new Date(start + 'T00:00:00Z')
  d.setUTCDate(d.getUTCDate() + daysFromStart)
  return d.toISOString().slice(0, 10)
}

export function StatsHeatmap({ dailyCommits, window }: StatsHeatmapProps) {
  if (!dailyCommits || dailyCommits.length === 0) {
    return null
  }

  const max = Math.max(...dailyCommits, 1)
  const total = dailyCommits.reduce((a, b) => a + b, 0)
  const today = dailyCommits[dailyCommits.length - 1] ?? 0

  return (
    <div>
      <div className="flex items-baseline gap-3 border-b border-border pb-2 mb-3">
        <h2 className="text-[14px] font-semibold text-text-primary tracking-tight">
          Daily commits
        </h2>
        <span className="text-[10.5px] text-text-muted uppercase tracking-widest">
          {dailyCommits.length}-day heatmap
        </span>
        <span className="flex-1" />
        <span className="text-[10.5px] text-text-muted uppercase tracking-widest">
          today{' '}
          <span className="font-mono text-text-secondary tabular">{today}</span>
        </span>
      </div>

      <div className="card p-4">
        <div
          className="grid gap-[3px]"
          style={{
            gridTemplateColumns: `repeat(${dailyCommits.length}, minmax(0, 1fr))`,
          }}
        >
          {dailyCommits.map((count, i) => {
            const date = dayLabel(window.start, i)
            const op = intensity(count, max)
            return (
              <div
                key={i}
                title={`${date} · ${count} commit${count === 1 ? '' : 's'}`}
                className="aspect-square rounded-[2px] border border-border-subtle"
                style={{
                  backgroundColor:
                    op === 0
                      ? 'var(--color-surface)'
                      : `rgba(35, 247, 221, ${op})`,
                }}
              />
            )
          })}
        </div>
        <div className="mt-3 flex items-center justify-between text-[10px] font-mono text-text-faint tabular">
          <span>{window.start}</span>
          <span className="text-text-muted">
            {total} commits over {window.days} days · avg{' '}
            {(total / window.days).toFixed(1)}/day
          </span>
          <span>{window.end}</span>
        </div>
      </div>
    </div>
  )
}
