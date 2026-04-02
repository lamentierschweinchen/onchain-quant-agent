import type { MetaLearning as MetaLearningType } from '../types/report'
import { AnalysisBlock } from './ui/AnalysisBlock'

interface MetaLearningProps {
  data?: MetaLearningType
}

export function MetaLearning({ data }: MetaLearningProps) {
  if (!data) return null

  const { completed, total } = {
    completed: data.action_items_completed,
    total: data.action_items_from_previous,
  }
  const progressPct = total > 0 ? Math.round((completed / total) * 100) : 0

  return (
    <details className="group">
      {/* Clickable summary header */}
      <summary className="flex items-center justify-between cursor-pointer list-none select-none bg-surface border border-border rounded-lg px-4 py-3 hover:bg-surface-hover transition-colors">
        <span className="font-medium text-text-primary">Agent Meta-Learning</span>
        {/* Chevron rotates when open via group-open utility */}
        <svg
          className="w-4 h-4 text-text-secondary transition-transform group-open:rotate-180"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M5.22 8.22a.75.75 0 0 1 1.06 0L10 11.94l3.72-3.72a.75.75 0 1 1 1.06 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L5.22 9.28a.75.75 0 0 1 0-1.06Z"
            clipRule="evenodd"
          />
        </svg>
      </summary>

      {/* Expanded content */}
      <div className="mt-3 space-y-5 bg-surface border border-border rounded-lg p-5">
        {/* Run number */}
        <div>
          <span className="text-xs font-semibold text-text-secondary uppercase tracking-widest">
            Run
          </span>
          <p className="font-mono text-xl font-bold text-text-primary mt-0.5">
            #{data.run_number}
          </p>
        </div>

        {/* Most valuable insight */}
        <div>
          <span className="text-xs font-semibold text-text-secondary uppercase tracking-widest">
            Most Valuable Insight
          </span>
          <p className="italic text-text-secondary text-sm mt-1 leading-relaxed">
            "{data.most_valuable_insight}"
          </p>
        </div>

        {/* Methodology changes */}
        {data.methodology_changes.length > 0 && (
          <div>
            <span className="text-xs font-semibold text-text-secondary uppercase tracking-widest">
              Methodology Changes
            </span>
            <ul className="mt-2 space-y-1">
              {data.methodology_changes.map((change, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-text-primary">
                  <span className="text-accent-cyan mt-0.5 flex-shrink-0">•</span>
                  <span>{change}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Action items progress */}
        <div>
          <span className="text-xs font-semibold text-text-secondary uppercase tracking-widest">
            Action Items
          </span>
          <p className="text-sm text-text-primary mt-1">
            Completed{' '}
            <span className="font-mono font-bold text-accent-cyan">{completed}</span>
            {' '}of{' '}
            <span className="font-mono font-bold">{total}</span>
          </p>
          {/* Progress bar */}
          <div className="mt-2 h-1.5 rounded-full bg-border overflow-hidden">
            <div
              className="h-full rounded-full bg-accent-cyan transition-all"
              style={{ width: `${progressPct}%` }}
            />
          </div>
          <p className="text-xs text-text-secondary mt-1">{progressPct}% complete</p>
        </div>

        {/* New addresses discovered */}
        <div>
          <span className="text-xs font-semibold text-text-secondary uppercase tracking-widest">
            New Addresses Discovered
          </span>
          <p className="font-mono text-xl font-bold text-text-primary mt-0.5">
            {data.new_addresses_discovered}
          </p>
        </div>

        {/* Top recommendation */}
        <div>
          <span className="text-xs font-semibold text-text-secondary uppercase tracking-widest block mb-2">
            Top Recommendation for Next Run
          </span>
          <AnalysisBlock text={data.top_recommendation} />
        </div>
      </div>
    </details>
  )
}
