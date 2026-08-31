import type { ContributorStats } from '../../types/stats'

interface StatsContributorsProps {
  contributors: ContributorStats[]
}

export function StatsContributors({ contributors }: StatsContributorsProps) {
  if (!contributors || contributors.length === 0) {
    return (
      <div className="card p-4 text-[12px] text-text-muted">No contributors in window.</div>
    )
  }

  const maxCommits = Math.max(...contributors.map((c) => c.commits_28d), 1)

  return (
    <div className="card overflow-hidden">
      <div className="px-4 py-2 border-b border-border eyebrow bg-bg-elevated flex items-baseline justify-between">
        <span>Top contributors</span>
        <span className="text-text-faint normal-case tracking-normal text-[9.5px]">
          last 28 days
        </span>
      </div>
      <ul>
        {contributors.map((c, i) => {
          const ratio = c.commits_28d / maxCommits
          return (
            <li
              key={c.login}
              className="relative px-4 py-2.5 border-b border-border-subtle last:border-0 hover:bg-surface-hover transition-colors"
            >
              {/* Bar background — proportional to commit count */}
              <div
                className="absolute inset-y-0 left-0 bg-accent-cyan/[0.04] pointer-events-none"
                style={{ width: `${ratio * 100}%` }}
              />
              <div className="relative flex items-center gap-3">
                <span className="text-[10px] text-text-faint font-mono w-4 text-right tabular">
                  {i + 1}
                </span>
                <img
                  src={c.avatar_url}
                  alt=""
                  loading="lazy"
                  className="w-6 h-6 rounded-full bg-surface border border-border"
                />
                <div className="flex-1 min-w-0">
                  <a
                    href={c.html_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`text-[13px] font-mono truncate block transition-colors ${
                      c.highlighted
                        ? 'text-accent-cyan'
                        : 'text-text-primary hover:text-accent-cyan'
                    }`}
                  >
                    {c.login}
                    {c.highlighted && (
                      <span className="ml-1.5 text-[9px] uppercase tracking-widest text-accent-cyan/60">
                        watch
                      </span>
                    )}
                  </a>
                  <span className="text-[10px] text-text-muted font-mono tabular">
                    {c.repos_touched} repo{c.repos_touched === 1 ? '' : 's'}
                    {c.prs_merged_28d > 0 && (
                      <>
                        {' · '}
                        <span className="text-text-secondary">{c.prs_merged_28d}</span> PRs
                      </>
                    )}
                  </span>
                </div>
                <div className="text-right">
                  <div className="text-[13px] font-mono text-text-primary tabular">
                    {c.commits_28d}
                  </div>
                  <div className="text-[9px] uppercase tracking-widest text-text-faint">
                    commits
                  </div>
                </div>
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
