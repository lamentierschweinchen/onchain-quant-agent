import type { Finding, Category, Severity } from '../types/report'
import { SEVERITY_COLORS } from '../lib/constants'

const FINDING_CATEGORY_COLORS: Record<Category, string> = {
  whale: '#5896F2',
  staking: '#34D196',
  token: '#B975F0',
  defi: '#B975F0',
  network: '#8B97AC',
  anomaly: '#FB8534',
  trend: '#23F7DD',
}

const CATEGORY_LABELS: Record<Category, string> = {
  whale: 'WHALE',
  staking: 'STAKING',
  token: 'TOKEN',
  defi: 'DEFI',
  network: 'NETWORK',
  anomaly: 'ANOMALY',
  trend: 'TREND',
}

const GLOW_SEVERITIES = new Set<Severity>(['critical', 'high'])

interface ExecutiveSummaryProps {
  findings: Finding[]
}

export function ExecutiveSummary({ findings }: ExecutiveSummaryProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
      {findings.map((finding, idx) => {
        const borderColor = SEVERITY_COLORS[finding.severity]
        const categoryColor =
          FINDING_CATEGORY_COLORS[finding.category] ?? '#8B97AC'
        const hasGlow = GLOW_SEVERITIES.has(finding.severity)

        return (
          <article
            key={idx}
            className="relative bg-surface border border-border rounded-md p-4 card-hover overflow-hidden"
            style={{
              boxShadow: hasGlow ? `inset 3px 0 0 ${borderColor}` : `inset 2px 0 0 ${borderColor}`,
            }}
          >
            {/* Top row: index + category */}
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-mono text-text-muted">
                #{String(idx + 1).padStart(2, '0')}
              </span>
              <span
                className="inline-flex items-center px-1.5 py-[1px] rounded text-[10px] font-mono font-semibold tracking-wider"
                style={{
                  color: categoryColor,
                  backgroundColor: `${categoryColor}1A`,
                  border: `1px solid ${categoryColor}33`,
                }}
              >
                {CATEGORY_LABELS[finding.category] ?? finding.category}
              </span>
            </div>

            {/* Finding text */}
            <p className="text-[13px] text-text-primary leading-relaxed">
              {finding.finding}
            </p>
          </article>
        )
      })}
    </div>
  )
}
