import type {
  PreCommittedTest,
  TestOutcome,
  ScoreboardLedger,
} from '../types/report'
import { NullState } from './ui/NullState'
import { formatDateShort } from '../lib/formatters'
import { ExpandableText } from './ui/ExpandableText'

interface Props {
  /** Tests carried by the currently selected report. */
  tests?: PreCommittedTest[]
  runNumber?: number | null
  /** Cross-run ledger — constant as the reader moves the week cursor. */
  ledger?: ScoreboardLedger | null
}

const OUTCOME_STYLE: Record<
  TestOutcome,
  { label: string; short: string; color: string; blurb: string }
> = {
  as_predicted: {
    label: 'CALLED IT',
    short: 'Called it',
    color: '#34D196',
    blurb: 'A registered branch fired in the direction written down in advance',
  },
  against: {
    label: 'GOT IT WRONG',
    short: 'Wrong',
    color: '#FB8534',
    blurb: 'The measurement contradicted the claim',
  },
  inconclusive: {
    label: 'NO CLEAR ANSWER',
    short: 'Unclear',
    color: '#E8B43A',
    blurb: 'Neither branch fired cleanly — usually a sign the threshold was mis-specified',
  },
  withdrawn: {
    label: 'PREMISE COLLAPSED',
    short: 'Premise gone',
    color: '#F4525A',
    blurb:
      'The claim the test rested on was withdrawn, so the test never got to resolve',
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

/** The traced factor: how often the model's advance calls actually land. */
function CalibrationStrip({ ledger }: { ledger: ScoreboardLedger }) {
  const t = ledger.totals
  const scored = t.as_predicted + t.against + t.inconclusive
  const hit = scored > 0 ? (100 * t.as_predicted) / scored : null
  const segments = (
    [
      { key: 'as_predicted', count: t.as_predicted },
      { key: 'inconclusive', count: t.inconclusive },
      { key: 'against', count: t.against },
      { key: 'withdrawn', count: t.withdrawn },
    ] as { key: TestOutcome; count: number }[]
  ).filter((s) => s.count > 0)
  const total = segments.reduce((s, x) => s + x.count, 0) || 1

  return (
    <div className="rounded border border-border bg-bg-elevated p-3">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <div className="text-[9.5px] text-text-muted uppercase tracking-widest">
            Track record — calls that landed
          </div>
          <div className="mt-1 flex items-baseline gap-2">
            <span className="font-mono text-[26px] font-semibold leading-none text-text-primary">
              {t.as_predicted}
              <span className="text-text-faint">/{scored}</span>
            </span>
            {hit != null && (
              <span className="font-mono text-[13px] text-accent-cyan">
                {hit.toFixed(0)}%
              </span>
            )}
          </div>
          <div className="mt-1 text-[10.5px] text-text-muted">
            Excludes {t.withdrawn} test
            {t.withdrawn === 1 ? '' : 's'} whose premise was withdrawn — those
            score the model&apos;s claims, not its predictions
          </div>
        </div>
        <div className="text-right">
          <div className="text-[9.5px] text-text-muted uppercase tracking-widest">
            Ledger
          </div>
          <div className="mt-1 font-mono text-[11px] text-text-secondary">
            {t.open} open · {t.resolved} resolved · {ledger.runs.length} run
            {ledger.runs.length === 1 ? '' : 's'}
          </div>
        </div>
      </div>

      {/* outcome mix */}
      <div className="mt-3 flex h-2 rounded overflow-hidden">
        {segments.map((s) => (
          <div
            key={s.key}
            style={{
              width: `${(100 * s.count) / total}%`,
              backgroundColor: OUTCOME_STYLE[s.key].color,
              opacity: 0.85,
            }}
            title={`${s.count} × ${OUTCOME_STYLE[s.key].short}`}
          />
        ))}
      </div>
      <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-1">
        {segments.map((s) => (
          <span
            key={s.key}
            className="flex items-center gap-1.5 text-[10px] font-mono text-text-muted"
          >
            <span
              className="inline-block w-2 h-2 rounded-sm"
              style={{ backgroundColor: OUTCOME_STYLE[s.key].color }}
            />
            {s.count} {OUTCOME_STYLE[s.key].short.toLowerCase()}
          </span>
        ))}
      </div>

      {/* per-run record — a real series once more than one run has scored */}
      {ledger.runs.length > 1 && (
        <div className="mt-3 border-t border-border-subtle pt-2">
          <div className="text-[9.5px] text-text-muted uppercase tracking-widest mb-1">
            Per run
          </div>
          <div className="flex flex-wrap gap-3">
            {ledger.runs.map((r) => (
              <span
                key={r.date}
                className="font-mono text-[10.5px] text-text-secondary"
                title={`${r.date}: ${r.resolved} resolved, ${r.as_predicted} as predicted`}
              >
                #{r.run}{' '}
                <span className="text-text-primary">
                  {r.as_predicted}/{r.resolved}
                </span>
              </span>
            ))}
          </div>
        </div>
      )}

      {ledger.totals.resolved < 12 && (
        <p className="mt-2 text-[10px] text-text-faint leading-snug">
          Small sample — the ledger starts at run #21 and is never backfilled
          from older prose, so this is a record being built rather than a rate to
          trust yet.
        </p>
      )}
    </div>
  )
}

function TestCard({
  test,
  showRegisteredElsewhere,
}: {
  test: PreCommittedTest
  showRegisteredElsewhere?: boolean
}) {
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
            Waiting
          </span>
        ) : (
          test.outcome && <OutcomeChip outcome={test.outcome} />
        )}
      </div>

      {/* The verdict is the headline; the evidence behind it is opt-in. Showing
          claim + threshold + measurement + resolution for every test turned this
          panel into a quarter of the page. */}
      {test.resolution && (
        <ExpandableText
          text={test.resolution}
          lines={2}
          className="mt-1.5 text-[11.5px] text-text-primary leading-relaxed"
          moreLabel="Full reasoning"
          lessLabel="Collapse"
        />
      )}

      {test.measured_value && (
        <ExpandableText
          text={test.measured_value}
          lines={1}
          className="mt-1.5 text-[11px] text-text-secondary leading-relaxed font-mono"
          moreLabel={isOpen ? 'Where it stands' : 'What was measured'}
          lessLabel="Collapse"
        />
      )}

      <details className="mt-1.5 group">
        <summary className="cursor-pointer list-none inline-flex items-center gap-1 rounded px-2 py-1.5 -ml-2 text-[9.5px] font-mono uppercase tracking-widest text-text-muted transition-colors duration-100 hover:text-accent-cyan hover:bg-accent-cyan/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan/60">
          What would settle it
          <span aria-hidden="true" className="group-open:hidden">+</span>
          <span aria-hidden="true" className="hidden group-open:inline">−</span>
        </summary>
        <p className="mt-1 text-[11px] text-text-secondary leading-relaxed">
          {test.threshold}
        </p>
      </details>

      <div className="mt-1.5 flex flex-wrap gap-x-4 gap-y-0.5 text-[9.5px] font-mono uppercase tracking-widest text-text-faint">
        <span>
          called in run #{test.registered_in_run}
          {showRegisteredElsewhere ? ' (earlier week)' : ''}
        </span>
        {test.resolved_in_run != null && (
          <span>settled in run #{test.resolved_in_run}</span>
        )}
        {test.branches && test.branches.length > 0 && (
          <span>{test.branches.length} outcomes written down in advance</span>
        )}
      </div>
    </li>
  )
}

/**
 * The epistemic ledger. A reader of one report sees a dozen assertive findings
 * with no way to tell a call that landed from a correction of last week's claim
 * — this panel is that distinction, plus the running record of how often the
 * model is right when it commits in advance.
 *
 * Forward-only: tests are structured from run #21 onward, never reconstructed
 * from older prose.
 */
export function Scoreboard({ tests, runNumber, ledger }: Props) {
  const localTests = tests ?? []
  const ledgerTests = ledger?.tests ?? []

  // Open questions come from the whole ledger, so a test registered two weeks
  // ago stays visible until it settles.
  const openAll = (ledgerTests.length ? ledgerTests : localTests).filter(
    (t) => t.status === 'open',
  )
  const resolvedHere = localTests.filter((t) => t.status === 'resolved')

  if (!ledger && localTests.length === 0) {
    return (
      <NullState message="Predictions are tracked from run #21 onward — this report predates the ledger." />
    )
  }

  return (
    <section className="card overflow-hidden">
      <header className="px-4 py-2.5 border-b border-border bg-bg-elevated">
        <h3 className="text-[12px] font-semibold text-text-primary tracking-tight">
          Model scoreboard
        </h3>
        <p className="text-[10px] text-text-muted mt-0.5">
          Every week the model writes down what it expects and the number that
          would prove it wrong. The next week grades it — so you can see how well
          it actually reads this chain, not just how confidently it writes.
        </p>
      </header>

      <div className="p-4 space-y-4">
        {ledger && <CalibrationStrip ledger={ledger} />}

        {openAll.length > 0 && (
          <div>
            <div className="text-[10px] text-text-muted uppercase tracking-widest mb-1.5">
              Waiting to be settled
              {runNumber != null && ` — graded in run #${runNumber + 1}`}
            </div>
            <ul className="space-y-2">
              {openAll.map((t) => (
                <TestCard
                  key={t.id}
                  test={t}
                  showRegisteredElsewhere={
                    runNumber != null && t.registered_in_run !== runNumber
                  }
                />
              ))}
            </ul>
          </div>
        )}

        {resolvedHere.length > 0 && (
          <div>
            <div className="text-[10px] text-text-muted uppercase tracking-widest mb-1.5">
              Settled this week
            </div>
            <ul className="space-y-2">
              {resolvedHere.map((t) => (
                <TestCard key={t.id} test={t} showRegisteredElsewhere />
              ))}
            </ul>
          </div>
        )}

        {resolvedHere.length === 0 && localTests.length === 0 && ledger && (
          <p className="text-[11px] text-text-muted">
            This week predates the ledger — the open questions above were
            recorded in{' '}
            {ledger.runs.length > 0
              ? `run #${ledger.runs[ledger.runs.length - 1].run} (${formatDateShort(
                  ledger.runs[ledger.runs.length - 1].date,
                )})`
              : 'a later run'}
            .
          </p>
        )}
      </div>
    </section>
  )
}
