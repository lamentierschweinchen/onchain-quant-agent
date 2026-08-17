import type { PreCommittedTest, TestOutcome } from '../types/report'
import { NullState } from './ui/NullState'

interface Props {
  tests?: PreCommittedTest[]
  runNumber?: number | null
}

const OUTCOME_STYLE: Record<
  TestOutcome,
  { label: string; color: string; blurb: string }
> = {
  as_predicted: {
    label: 'FIRED AS PREDICTED',
    color: '#34D196',
    blurb: 'A registered branch fired in the direction written down in advance',
  },
  against: {
    label: 'RESOLVED AGAINST',
    color: '#FB8534',
    blurb: 'The measurement contradicted the claim',
  },
  inconclusive: {
    label: 'INCONCLUSIVE',
    color: '#E8B43A',
    blurb: 'Neither branch fired cleanly',
  },
  withdrawn: {
    label: 'PREMISE WITHDRAWN',
    color: '#F4525A',
    blurb: 'The claim the test rested on was withdrawn, not resolved',
  },
}

function OutcomeChip({ outcome }: { outcome: TestOutcome }) {
  const style = OUTCOME_STYLE[outcome]
  if (!style) return null
  return (
    <span
      className="inline-flex items-center px-1.5 py-[1px] rounded text-[9.5px] font-mono font-bold tracking-widest uppercase whitespace-nowrap"
      style={{
        color: style.color,
        backgroundColor: `${style.color}1A`,
        border: `1px solid ${style.color}33`,
      }}
      title={style.blurb}
    >
      {style.label}
    </span>
  )
}

function TestCard({ test }: { test: PreCommittedTest }) {
  const isOpen = test.status === 'open'
  return (
    <li
      className={[
        'rounded border p-3',
        isOpen
          ? 'border-accent-cyan/30 bg-accent-cyan/[0.04]'
          : 'border-border bg-bg-elevated',
      ].join(' ')}
    >
      <div className="flex items-start justify-between gap-3">
        <p className="text-[12.5px] font-medium text-text-primary leading-snug">
          {test.claim}
        </p>
        {isOpen ? (
          <span className="inline-flex items-center px-1.5 py-[1px] rounded text-[9.5px] font-mono font-bold tracking-widest uppercase whitespace-nowrap text-accent-cyan bg-accent-cyan/10 border border-accent-cyan/30">
            Open
          </span>
        ) : (
          test.outcome && <OutcomeChip outcome={test.outcome} />
        )}
      </div>

      <p className="mt-1.5 text-[11px] text-text-secondary leading-relaxed">
        <span className="font-mono text-[9.5px] uppercase tracking-widest text-text-muted">
          threshold
        </span>{' '}
        {test.threshold}
      </p>

      {test.measured_value && (
        <p className="mt-1 text-[11px] text-text-secondary leading-relaxed">
          <span className="font-mono text-[9.5px] uppercase tracking-widest text-text-muted">
            measured
          </span>{' '}
          <span className="font-mono text-text-primary">
            {test.measured_value}
          </span>
        </p>
      )}

      {test.resolution && (
        <p className="mt-1.5 text-[11.5px] text-text-primary leading-relaxed border-t border-border-subtle pt-1.5">
          {test.resolution}
        </p>
      )}

      <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-0.5 text-[9.5px] font-mono uppercase tracking-widest text-text-faint">
        <span>registered run #{test.registered_in_run}</span>
        {test.resolved_in_run != null && (
          <span>resolved run #{test.resolved_in_run}</span>
        )}
        {test.branches && test.branches.length > 0 && (
          <span>{test.branches.length} registered branches</span>
        )}
      </div>
    </li>
  )
}

/**
 * The epistemic ledger. A reader of one report sees a dozen assertive findings
 * with no way to tell a prediction that fired from a correction of last week's
 * claim — this panel is that distinction, and nothing else.
 *
 * Forward-only: tests are structured from run #21 onward and never reconstructed
 * from older prose.
 */
export function Scoreboard({ tests, runNumber }: Props) {
  if (!tests || tests.length === 0) {
    return (
      <NullState message="Pre-committed tests are structured from run #21 onward — this report predates the ledger." />
    )
  }

  const open = tests.filter((t) => t.status === 'open')
  const resolved = tests.filter((t) => t.status === 'resolved')
  const asPredicted = resolved.filter((t) => t.outcome === 'as_predicted').length

  return (
    <section className="card overflow-hidden">
      <header className="px-4 py-2.5 border-b border-border bg-bg-elevated flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h3 className="text-[12px] font-semibold text-text-primary tracking-tight">
            Pre-committed tests
          </h3>
          <p className="text-[10px] text-text-muted mt-0.5">
            Falsifiable claims registered with numeric thresholds one week and
            resolved the next — open questions first
          </p>
        </div>
        <div className="flex items-center gap-4 text-[10px] font-mono uppercase tracking-widest">
          <span className="text-accent-cyan">{open.length} open</span>
          <span className="text-text-muted">
            {resolved.length} resolved
            {resolved.length > 0 && (
              <span className="text-up">
                {' '}
                · {asPredicted} as predicted
              </span>
            )}
          </span>
        </div>
      </header>

      <div className="p-4 space-y-4">
        {open.length > 0 && (
          <div>
            <div className="text-[10px] text-text-muted uppercase tracking-widest mb-1.5">
              Open — registered for run #{(runNumber ?? 0) + 1}
            </div>
            <ul className="space-y-2">
              {open.map((t) => (
                <TestCard key={t.id} test={t} />
              ))}
            </ul>
          </div>
        )}

        {resolved.length > 0 && (
          <div>
            <div className="text-[10px] text-text-muted uppercase tracking-widest mb-1.5">
              Resolved this run
            </div>
            <ul className="space-y-2">
              {resolved.map((t) => (
                <TestCard key={t.id} test={t} />
              ))}
            </ul>
          </div>
        )}
      </div>
    </section>
  )
}
