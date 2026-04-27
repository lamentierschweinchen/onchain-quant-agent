import type { Severity, AnomalySeverity } from '../../types/report'
import { SEVERITY_LABELS } from '../../lib/constants'

interface SeverityBadgeProps {
  severity: Severity | AnomalySeverity | string
}

const SEVERITY_STYLES: Record<string, string> = {
  critical:
    'bg-severity-critical/15 text-severity-critical border border-severity-critical/40',
  high:
    'bg-severity-high/15 text-severity-high border border-severity-high/40',
  medium:
    'bg-severity-medium/15 text-severity-medium border border-severity-medium/40',
  low: 'bg-severity-low/15 text-severity-low border border-severity-low/40',
  info: 'bg-severity-info/15 text-severity-info border border-severity-info/40',
}

const FALLBACK = 'bg-severity-info/15 text-severity-info border border-severity-info/40'

export function SeverityBadge({ severity }: SeverityBadgeProps) {
  const styles = SEVERITY_STYLES[severity] ?? FALLBACK
  const label =
    SEVERITY_LABELS[severity as keyof typeof SEVERITY_LABELS] ?? severity.toUpperCase()

  return (
    <span
      className={`inline-flex items-center px-1.5 py-[1px] rounded text-[10px] font-mono font-semibold tracking-wider ${styles}`}
    >
      {label}
    </span>
  )
}
