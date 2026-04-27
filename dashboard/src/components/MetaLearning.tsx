import type { MetaLearning as MetaLearningType } from '../types/report'

interface MetaLearningProps {
  data?: MetaLearningType
}

export function MetaLearning({ data }: MetaLearningProps) {
  if (!data) return null

  const completionRate =
    data.action_items_from_previous && data.action_items_from_previous > 0
      ? Math.round(
          ((data.action_items_completed ?? 0) / data.action_items_from_previous) *
            100,
        )
      : null

  return (
    <details className="group">
      <summary className="flex items-center justify-between cursor-pointer list-none select-none bg-surface border border-border rounded-md px-4 py-2.5 hover:bg-surface-hover transition-colors">
        <div className="flex items-center gap-3">
          <span className="text-[12px] font-semibold text-text-primary tracking-tight">
            Agent Meta-Learning
          </span>
          <span className="text-[10px] font-mono text-text-muted">
            Run #{data.run_number}
          </span>
          {completionRate != null && (
            <span className="text-[10px] font-mono text-text-muted">
              <span className="text-up">{completionRate}%</span> action items completed
            </span>
          )}
        </div>
        <svg
          className="w-3.5 h-3.5 text-text-muted transition-transform group-open:rotate-180"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M5.22 8.22a.75.75 0 0 1 1.06 0L10 11.94l3.72-3.72a.75.75 0 1 1 1.06 1.06l-4.25 4.25a.75.75 0 0 1-1.06 0L5.22 9.28a.75.75 0 0 1 0-1.06Z"
            clipRule="evenodd"
          />
        </svg>
      </summary>

      <div className="mt-2 space-y-4 bg-surface border border-border rounded-md p-4">
        {/* Top stat strip */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Stat label="Run" value={`#${data.run_number}`} />
          {data.action_items_from_previous != null && (
            <Stat
              label="Action Items"
              value={`${data.action_items_completed ?? 0} / ${data.action_items_from_previous}`}
              tone="up"
            />
          )}
          {data.new_addresses_discovered != null && (
            <Stat
              label="New Addresses"
              value={String(data.new_addresses_discovered)}
            />
          )}
          {data.endpoints_that_failed && (
            <Stat
              label="Endpoints Failed"
              value={String(data.endpoints_that_failed.length)}
              tone={data.endpoints_that_failed.length > 0 ? 'down' : 'flat'}
            />
          )}
        </div>

        {data.most_valuable_insight && (
          <div className="border-l-2 border-accent-cyan/60 pl-3 py-1">
            <span className="eyebrow text-accent-cyan/80">Most valuable insight</span>
            <p className="text-[13px] text-text-primary mt-0.5">
              {data.most_valuable_insight}
            </p>
          </div>
        )}

        {data.top_recommendation && (
          <div className="border-l-2 border-severity-medium/60 pl-3 py-1">
            <span className="eyebrow text-severity-medium/80">Top recommendation for next run</span>
            <p className="text-[13px] text-text-primary mt-0.5">
              {data.top_recommendation}
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {data.key_findings && data.key_findings.length > 0 && (
            <Block title="Key Findings This Run">
              <ul className="space-y-1.5">
                {data.key_findings.map((f, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2 text-[12px] text-text-primary leading-relaxed"
                  >
                    <span className="text-accent-cyan mt-1 flex-shrink-0">•</span>
                    <span>{f}</span>
                  </li>
                ))}
              </ul>
            </Block>
          )}

          {data.api_quirks && data.api_quirks.length > 0 && (
            <Block title="API Quirks Discovered">
              <ul className="space-y-1.5">
                {data.api_quirks.map((q, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2 text-[12px] text-text-secondary leading-relaxed"
                  >
                    <span className="text-accent-cyan mt-1 flex-shrink-0">•</span>
                    <span>{q}</span>
                  </li>
                ))}
              </ul>
            </Block>
          )}
        </div>

        {data.methodology_changes && data.methodology_changes.length > 0 && (
          <Block title="Methodology Changes This Week">
            <ul className="space-y-1.5">
              {data.methodology_changes.map((m, idx) => (
                <li
                  key={idx}
                  className="flex items-start gap-2 text-[12px] text-text-primary leading-relaxed"
                >
                  <span className="text-accent-cyan mt-1 flex-shrink-0">•</span>
                  <span className="font-mono text-[11.5px]">{m}</span>
                </li>
              ))}
            </ul>
          </Block>
        )}

        {data.recommendations_for_next_run &&
          data.recommendations_for_next_run.length > 0 && (
            <Block title="Recommendations for Next Run">
              <ol className="space-y-1.5">
                {data.recommendations_for_next_run.map((r, idx) => (
                  <li
                    key={idx}
                    className="flex items-start gap-2 text-[12px] text-text-primary leading-relaxed"
                  >
                    <span className="text-accent-cyan font-mono mt-0 flex-shrink-0">
                      {String(idx + 1).padStart(2, '0')}.
                    </span>
                    <span>{r}</span>
                  </li>
                ))}
              </ol>
            </Block>
          )}
      </div>
    </details>
  )
}

function Stat({
  label,
  value,
  tone = 'neutral',
}: {
  label: string
  value: string
  tone?: 'neutral' | 'up' | 'down' | 'flat'
}) {
  const cls =
    tone === 'up'
      ? 'text-up'
      : tone === 'down'
        ? 'text-down'
        : tone === 'flat'
          ? 'text-flat'
          : 'text-text-primary'
  return (
    <div className="bg-bg-elevated border border-border rounded p-2.5">
      <span className="eyebrow">{label}</span>
      <p className={`hero-number-sm tabular ${cls}`}>{value}</p>
    </div>
  )
}

function Block({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <div>
      <span className="eyebrow block mb-2">{title}</span>
      {children}
    </div>
  )
}
