import type { WithdrawnClaim } from '../types/report'
import { formatDate } from '../lib/formatters'
import { ExpandableText } from './ui/ExpandableText'

interface Props {
  /** Claims this report asserted that a LATER run withdrew. */
  superseded: WithdrawnClaim[]
  /** Claims this report itself withdrew. */
  own: WithdrawnClaim[]
  onJumpToRun?: (date: string) => void
}

function ClaimRow({
  claim,
  tone,
  onJumpToRun,
}: {
  claim: WithdrawnClaim
  tone: 'superseded' | 'own'
  onJumpToRun?: (date: string) => void
}) {
  const jumpDate =
    tone === 'superseded'
      ? (claim.withdrawn_in_date ?? null)
      : (claim.asserted_in_dates?.[0] ?? null)

  return (
    <li className="border-t border-border-subtle pt-2 first:border-t-0 first:pt-0">
      <p
        className={[
          'text-[12px] leading-snug',
          tone === 'superseded'
            ? 'text-text-primary line-through decoration-down/60'
            : 'text-text-secondary line-through decoration-text-faint',
        ].join(' ')}
      >
        {claim.claim}
      </p>
      <div className="mt-1 text-[11px] text-text-secondary leading-relaxed">
        <span className="font-mono text-[10px] uppercase tracking-widest text-text-muted">
          {tone === 'superseded'
            ? `withdrawn by run #${claim.withdrawn_in_run}`
            : `asserted in run${claim.asserted_in_runs.length > 1 ? 's' : ''} #${claim.asserted_in_runs.join(', #')}`}
        </span>
        <ExpandableText text={claim.reason} lines={2} moreLabel="Why" />
      </div>
      {claim.replacement && (
        <div className="mt-1 text-[11px] text-text-primary leading-relaxed">
          <span className="font-mono text-[10px] uppercase tracking-widest text-accent-cyan">
            replaced by
          </span>
          <ExpandableText
            text={claim.replacement}
            lines={2}
            moreLabel="Read the replacement"
          />
        </div>
      )}
      {jumpDate && onJumpToRun && (
        <button
          onClick={() => onJumpToRun(jumpDate)}
          className="mt-1.5 text-[10px] font-mono uppercase tracking-widest text-text-muted hover:text-accent-cyan transition-colors"
        >
          {tone === 'superseded'
            ? `Open the correction (${formatDate(jumpDate)}) →`
            : `Open the report that asserted it (${formatDate(jumpDate)}) →`}
        </button>
      )}
    </li>
  )
}

/**
 * Two directions, one component:
 *  - viewing an OLD report whose claims were later withdrawn → a warning
 *  - viewing the report that DID the withdrawing → its corrections, stated plainly
 *
 * Without this, the archive re-asserts every corrected claim with full
 * confidence, which for a report whose distinguishing virtue is self-correction
 * is the one bug that undermines the whole project.
 */
export function ErrataBanner({ superseded, own, onJumpToRun }: Props) {
  if (superseded.length === 0 && own.length === 0) return null

  return (
    <div className="space-y-3">
      {superseded.length > 0 && (
        <section
          className="card overflow-hidden"
          style={{
            borderColor: 'rgba(244, 82, 90, 0.4)',
            background:
              'linear-gradient(180deg, rgba(244,82,90,0.07) 0%, transparent 60%)',
          }}
        >
          <header className="px-4 py-2.5 border-b border-border flex items-baseline gap-2">
            <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-down">
              Superseded
            </span>
            <h3 className="text-[12px] font-semibold text-text-primary tracking-tight">
              {superseded.length === 1
                ? 'One claim in this report was later withdrawn'
                : `${superseded.length} claims in this report were later withdrawn`}
            </h3>
          </header>
          <ul className="p-4 space-y-3">
            {superseded.map((c, i) => (
              <ClaimRow
                key={i}
                claim={c}
                tone="superseded"
                onJumpToRun={onJumpToRun}
              />
            ))}
          </ul>
        </section>
      )}

      {own.length > 0 && (
        <section className="card overflow-hidden">
          <header className="px-4 py-2.5 border-b border-border bg-bg-elevated flex items-baseline gap-2">
            <span className="font-mono text-[10px] font-bold uppercase tracking-widest text-accent-cyan">
              Corrections
            </span>
            <h3 className="text-[12px] font-semibold text-text-primary tracking-tight">
              {own.length === 1
                ? 'This run withdrew one earlier claim'
                : `This run withdrew ${own.length} earlier claims`}
            </h3>
          </header>
          <details className="group">
            <summary className="cursor-pointer list-none px-4 py-2 text-[10.5px] font-mono uppercase tracking-widest text-text-muted transition-colors duration-100 hover:text-accent-cyan focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan/60 focus-visible:ring-inset">
              <span className="group-open:hidden">Show what changed +</span>
              <span className="hidden group-open:inline">Hide −</span>
            </summary>
            <ul className="px-4 pb-4 space-y-3">
              {own.map((c, i) => (
                <ClaimRow key={i} claim={c} tone="own" onJumpToRun={onJumpToRun} />
              ))}
            </ul>
          </details>
        </section>
      )}
    </div>
  )
}
