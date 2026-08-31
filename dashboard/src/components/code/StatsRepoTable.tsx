import type { RepoStats } from '../../types/stats'
import { Sparkline } from './Sparkline'

interface StatsRepoTableProps {
  repos: RepoStats[]
}

function relativeTime(iso: string | null): string {
  if (!iso) return '—'
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}d ago`
  return iso.slice(0, 10)
}

function freshnessColor(iso: string | null): string {
  if (!iso) return 'text-text-faint'
  const hours = (Date.now() - new Date(iso).getTime()) / (1000 * 60 * 60)
  if (hours < 24) return 'text-up'
  if (hours < 24 * 7) return 'text-text-secondary'
  return 'text-text-muted'
}

export function StatsRepoTable({ repos }: StatsRepoTableProps) {
  if (!repos || repos.length === 0) {
    return null
  }

  return (
    <div>
      <div className="flex items-baseline gap-3 border-b border-border pb-2 mb-3">
        <h2 className="text-[14px] font-semibold text-text-primary tracking-tight">
          Per-repo activity
        </h2>
        <span className="text-[10.5px] text-text-muted uppercase tracking-widest">
          sorted by 28d commits · sparkline = 12 weeks
        </span>
      </div>

      <div className="card overflow-hidden">
        <table className="terminal-table">
          <thead>
            <tr>
              <th className="w-[30%]">Repo</th>
              <th className="text-right w-[8%]">28d</th>
              <th className="text-right w-[8%]">7d</th>
              <th className="text-right w-[8%]">PRs</th>
              <th className="text-right w-[8%]">Open</th>
              <th className="w-[12%]">Activity</th>
              <th className="w-[14%]">Last commit</th>
              <th className="text-right w-[8%]">★</th>
            </tr>
          </thead>
          <tbody>
            {repos.map((r) => (
              <tr key={r.full_name}>
                <td>
                  <div className="flex flex-col">
                    <a
                      href={r.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-[13px] font-mono text-text-primary hover:text-accent-cyan transition-colors"
                    >
                      {r.name}
                    </a>
                    {r.description && (
                      <span className="text-[10.5px] text-text-muted truncate max-w-[360px]">
                        {r.description}
                      </span>
                    )}
                  </div>
                </td>
                <td className="text-right font-mono tabular">{r.commits_28d}</td>
                <td className="text-right font-mono tabular text-text-secondary">
                  {r.commits_7d}
                </td>
                <td className="text-right font-mono tabular">
                  {r.prs_merged_28d}
                </td>
                <td className="text-right font-mono tabular text-text-muted">
                  {r.open_prs}
                </td>
                <td>
                  <Sparkline values={r.weekly_commits} />
                </td>
                <td>
                  <span
                    className={`text-[11px] font-mono tabular ${freshnessColor(r.last_commit_at)}`}
                  >
                    {relativeTime(r.last_commit_at)}
                  </span>
                </td>
                <td className="text-right font-mono tabular text-text-muted">
                  {r.stars >= 1000
                    ? `${(r.stars / 1000).toFixed(1)}k`
                    : r.stars}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
