import type { ProgressStats } from '../../types/stats'

interface StatCardProps {
  label: string
  value: number
  sub?: string
  accent?: boolean
}

function StatCard({ label, value, sub, accent = false }: StatCardProps) {
  return (
    <div className={`card ${accent ? 'card-accent' : ''} px-4 py-3`}>
      <div className="eyebrow">{label}</div>
      <div className="mt-1 flex items-baseline gap-1.5">
        <span className="hero-number">{value.toLocaleString('en-US')}</span>
        {sub && <span className="hero-unit">{sub}</span>}
      </div>
    </div>
  )
}

interface StatsTotalsProps {
  totals: ProgressStats['totals']
  windowDays: number
  totalRepos: number
}

export function StatsTotals({ totals, windowDays, totalRepos }: StatsTotalsProps) {
  return (
    <div>
      <div className="flex items-baseline gap-3 border-b border-border pb-2 mb-3">
        <h2 className="text-[14px] font-semibold text-text-primary tracking-tight">
          Activity
        </h2>
        <span className="text-[10.5px] text-text-muted uppercase tracking-widest">
          ecosystem · last {windowDays} days
        </span>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
        <StatCard label="Commits" value={totals.commits} accent />
        <StatCard label="PRs merged" value={totals.prs_merged} />
        <StatCard label="PRs opened" value={totals.prs_opened} />
        <StatCard label="Contributors" value={totals.contributors} />
        <StatCard label="Releases" value={totals.releases} />
        <StatCard
          label="Active repos"
          value={totals.repos_active}
          sub={`/ ${totalRepos}`}
        />
      </div>
    </div>
  )
}
