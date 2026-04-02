import type { Finding, Category, Severity } from '../types/report'
import { SEVERITY_COLORS } from '../lib/constants'

// Map finding categories to display colors (hex).
// Category tokens in the CSS cover exchange/defi/team/system/other.
// Finding categories use a different vocabulary, so we map manually.
const FINDING_CATEGORY_COLORS: Record<Category, string> = {
  whale: '#3B82F6',    // exchange blue — large holders / market actors
  staking: '#22C55E',  // team green — validator / staking ecosystem
  token: '#A855F7',    // defi purple — token activity
  defi: '#A855F7',     // defi purple
  network: '#6B7280',  // system grey — infrastructure / baseline
  anomaly: '#F97316',  // orange — flagged deviation
}

// Category display labels (capitalised)
const CATEGORY_LABELS: Record<Category, string> = {
  whale: 'Whale',
  staking: 'Staking',
  token: 'Token',
  defi: 'DeFi',
  network: 'Network',
  anomaly: 'Anomaly',
}

// Severities that get a glow effect
const GLOW_SEVERITIES = new Set<Severity>(['critical', 'high'])

interface ExecutiveSummaryProps {
  findings: Finding[]
}

export function ExecutiveSummary({ findings }: ExecutiveSummaryProps) {
  return (
    <div className="flex flex-row gap-4 overflow-x-auto pb-2">
      {findings.map((finding, idx) => {
        const borderColor = SEVERITY_COLORS[finding.severity]
        const categoryColor = FINDING_CATEGORY_COLORS[finding.category]
        const hasGlow = GLOW_SEVERITIES.has(finding.severity)

        return (
          <div
            key={idx}
            className="min-w-[280px] max-w-[400px] flex-shrink-0 bg-surface rounded-lg p-4 border border-border"
            style={{
              borderLeft: `3px solid ${borderColor}`,
              boxShadow: hasGlow
                ? `0 0 12px ${borderColor}33` // 33 = ~20% opacity in hex
                : undefined,
            }}
          >
            {/* Category pill — top right */}
            <div className="flex justify-end mb-2">
              <span
                className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium uppercase tracking-wide"
                style={{
                  color: categoryColor,
                  backgroundColor: `${categoryColor}22`,
                  border: `1px solid ${categoryColor}44`,
                }}
              >
                {CATEGORY_LABELS[finding.category]}
              </span>
            </div>

            {/* Finding text */}
            <p className="text-sm text-text-primary leading-relaxed">
              {finding.finding}
            </p>
          </div>
        )
      })}
    </div>
  )
}
