import type { ReleaseEntry } from '../../types/stats'

interface StatsReleasesProps {
  releases: ReleaseEntry[]
}

function formatDate(iso: string): string {
  if (!iso) return '—'
  return iso.slice(0, 10)
}

export function StatsReleases({ releases }: StatsReleasesProps) {
  if (!releases || releases.length === 0) {
    return (
      <div className="card p-4 text-[12px] text-text-muted">No releases in window.</div>
    )
  }

  return (
    <div className="card overflow-hidden">
      <div className="px-4 py-2 border-b border-border eyebrow bg-bg-elevated flex items-baseline justify-between">
        <span>Recent releases</span>
        <span className="text-text-faint normal-case tracking-normal text-[9.5px]">
          across watchlist
        </span>
      </div>
      <ul>
        {releases.map((r) => (
          <li
            key={`${r.repo}-${r.tag}`}
            className="flex items-center gap-3 px-4 py-2 border-b border-border-subtle last:border-0 hover:bg-surface-hover transition-colors"
          >
            <span className="text-[10px] font-mono text-text-faint w-[80px] flex-shrink-0 tabular">
              {formatDate(r.published_at)}
            </span>
            <span className="text-[10.5px] uppercase tracking-wider text-text-muted w-[140px] flex-shrink-0 truncate">
              {r.repo}
            </span>
            <a
              href={r.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 text-[13px] font-mono text-text-primary hover:text-accent-cyan transition-colors truncate"
            >
              {r.tag}
            </a>
            {r.is_prerelease && (
              <span className="text-[9px] font-mono uppercase tracking-widest text-severity-medium border border-severity-medium/40 px-1.5 py-0.5 rounded">
                pre
              </span>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
