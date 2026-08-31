import type { Finding, Category, Severity } from '../types/report'
import { SEVERITY_COLORS } from '../lib/constants'
import { ExpandableText } from './ui/ExpandableText'

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


/**
 * The agent writes each finding as an ALL-CAPS lede followed by a normal-case
 * explanation. Rendered as one block that is a 600-character paragraph shouting
 * at the reader. Split it so the lede becomes a scannable headline and the
 * evidence sits underneath, collapsed.
 */
function splitFinding(text: string): { headline: string | null; body: string } {
  // The word after the lede may be lowercase (a provider identity like
  // "ledgerbyfigment"), so the uppercase test on the lede itself is the real gate.
  const m = text.match(/^(.{20,260}?[.:])\s+(?=[A-Za-z0-9(])/)
  if (!m) return { headline: null, body: text }
  const lede = m[1]
  const letters = lede.replace(/[^A-Za-z]/g, '')
  if (letters.length < 15) return { headline: null, body: text }
  const upper = lede.replace(/[^A-Z]/g, '').length
  // Only treat it as a headline when the agent actually shouted it.
  if (upper / letters.length < 0.7) return { headline: null, body: text }
  return { headline: lede.replace(/[.:]$/, ''), body: text.slice(m[0].length) }
}

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
        const { headline, body } = splitFinding(finding.finding)

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

            {/* Headline first, evidence on request */}
            {headline ? (
              <>
                <h3 className="text-[13px] font-semibold text-text-primary leading-snug">
                  {headline}
                </h3>
                {body && (
                  <ExpandableText
                    text={body}
                    lines={3}
                    className="mt-1.5 text-[12px] text-text-secondary leading-relaxed"
                    moreLabel="Evidence"
                    lessLabel="Collapse"
                  />
                )}
              </>
            ) : (
              <ExpandableText
                text={finding.finding}
                lines={4}
                className="text-[13px] text-text-primary leading-relaxed"
                moreLabel="More"
              />
            )}
          </article>
        )
      })}
    </div>
  )
}
