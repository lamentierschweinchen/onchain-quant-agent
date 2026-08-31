import type { ProgressStats } from '../../types/stats'
import { StatsTotals } from './StatsTotals'
import { StatsHeatmap } from './StatsHeatmap'
import { StatsRepoTable } from './StatsRepoTable'
import { StatsContributors } from './StatsContributors'
import { StatsReleases } from './StatsReleases'

interface StatsPanelProps {
  stats: ProgressStats
}

export function StatsPanel({ stats }: StatsPanelProps) {
  return (
    <section className="space-y-6">
      <StatsTotals
        totals={stats.totals}
        windowDays={stats.window.days}
        totalRepos={stats.repos.length}
      />
      <StatsHeatmap
        dailyCommits={stats.daily_commits}
        window={stats.window}
      />
      <StatsRepoTable repos={stats.repos} />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <StatsContributors contributors={stats.top_contributors} />
        <StatsReleases releases={stats.recent_releases} />
      </div>
    </section>
  )
}

export function StatsPanelEmpty({ generatedAt }: { generatedAt?: string }) {
  return (
    <section className="card p-6 text-center">
      <div className="eyebrow mb-2">Stats not yet computed</div>
      <p className="text-text-muted text-[12.5px] max-w-md mx-auto">
        Quantitative stats will appear here once the daily agent has committed{' '}
        <code className="bg-surface-strong text-accent-cyan px-1 py-0.5 rounded text-[11px] font-mono">
          data/stats.json
        </code>{' '}
        to the repo.{' '}
        {generatedAt && (
          <span className="block mt-2 text-[10.5px] font-mono text-text-faint">
            Last attempt: {generatedAt}
          </span>
        )}
      </p>
    </section>
  )
}
