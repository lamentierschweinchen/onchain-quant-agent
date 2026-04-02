import type { Severity, AnomalySeverity } from '../../types/report'

interface SeverityBadgeProps {
  severity: Severity | AnomalySeverity | string
}

const SEVERITY_STYLES: Record<string, string> = {
  critical: 'bg-severity-critical/15 text-severity-critical border border-severity-critical/30',
  high: 'bg-severity-high/15 text-severity-high border border-severity-high/30',
  medium: 'bg-severity-medium/15 text-severity-medium border border-severity-medium/30',
  low: 'bg-severity-low/15 text-severity-low border border-severity-low/30',
  info: 'bg-severity-info/15 text-severity-info border border-severity-info/30',
}

const FALLBACK_STYLE = 'bg-severity-info/15 text-severity-info border border-severity-info/30'

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  const styles = SEVERITY_STYLES[severity] ?? FALLBACK_STYLE

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium uppercase tracking-wide ${styles}`}>
      {severity}
    </span>
  )
}
