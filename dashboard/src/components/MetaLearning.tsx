import type { MetaLearning as MetaLearningType } from '../types/report'

interface MetaLearningProps {
  data?: MetaLearningType
}

export function MetaLearning({ data }: MetaLearningProps) {
  if (!data) return null

  return (
    <details className="group">
      <summary className="flex items-center justify-between cursor-pointer list-none select-none bg-surface border border-border rounded-lg px-4 py-3 hover:bg-surface-hover transition-colors">
        <span className="font-medium text-text-primary">Agent Meta-Learning</span>
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

      <div className="mt-3 space-y-5 bg-surface border border-border rounded-lg p-5">
        <div>
          <span className="text-xs font-semibold text-text-secondary uppercase tracking-widest">Run</span>
          <p className="font-mono text-xl font-bold text-text-primary mt-0.5">#{data.run_number}</p>
        </div>

        {data.key_findings.length > 0 && (
          <div>
            <span className="text-xs font-semibold text-text-secondary uppercase tracking-widest">
              Key Findings This Run
            </span>
            <ul className="mt-2 space-y-1">
              {data.key_findings.map((f, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-text-primary">
                  <span className="text-accent-cyan mt-0.5 flex-shrink-0">•</span>
                  <span>{f}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {data.api_quirks.length > 0 && (
          <div>
            <span className="text-xs font-semibold text-text-secondary uppercase tracking-widest">
              API Quirks Discovered
            </span>
            <ul className="mt-2 space-y-1">
              {data.api_quirks.map((q, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-text-secondary">
                  <span className="text-accent-cyan mt-0.5 flex-shrink-0">•</span>
                  <span>{q}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {data.recommendations_for_next_run.length > 0 && (
          <div>
            <span className="text-xs font-semibold text-text-secondary uppercase tracking-widest block mb-2">
              Recommendations for Next Run
            </span>
            <ul className="space-y-1">
              {data.recommendations_for_next_run.map((r, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm text-text-primary">
                  <span className="text-accent-cyan mt-0.5 flex-shrink-0">{idx + 1}.</span>
                  <span>{r}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </details>
  )
}
