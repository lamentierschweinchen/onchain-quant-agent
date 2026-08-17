import type { UnbondingInFlight } from '../types/report'
import { formatEgldBare, formatDate } from '../lib/formatters'
import { AddressLink } from './ui/AddressLink'

interface Props {
  data: UnbondingInFlight
  /** The report's own date — the countdown is measured from the snapshot, not from now. */
  reportDate: string
}

/** Add fractional days to a YYYY-MM-DD date, returning YYYY-MM-DD. */
function addDays(dateStr: string, days: number): string {
  const d = new Date(`${dateStr}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() + Math.ceil(days))
  return d.toISOString().slice(0, 10)
}

function daysBetween(from: string, to: string): number {
  const a = new Date(`${from}T00:00:00Z`).getTime()
  const b = new Date(`${to}T00:00:00Z`).getTime()
  return Math.round((b - a) / 86_400_000)
}

/**
 * The only forward-looking quantity in the report: EGLD that becomes liquid on a
 * known date. Deliberately a single card, not a queue table — there is one
 * observation, and a table of one row would be a chart cosplaying as a system.
 */
export function UnbondingCard({ data, reportDate }: Props) {
  const legs = data.legs ?? []
  const landing = legs
    .map((l) => ({ ...l, lands: addDays(reportDate, l.days_to_unbond) }))
    .sort((a, b) => a.lands.localeCompare(b.lands))

  const lastLanding = landing.length ? landing[landing.length - 1].lands : null
  const today = new Date().toISOString().slice(0, 10)
  const daysLeft = lastLanding ? daysBetween(today, lastLanding) : null
  const due = daysLeft != null && daysLeft <= 0

  return (
    <section className="card card-accent overflow-hidden">
      <header className="px-4 py-2.5 border-b border-border bg-bg-elevated">
        <h3 className="text-[12px] font-semibold text-text-primary tracking-tight">
          Unbonding in flight
        </h3>
        <p className="text-[10px] text-text-muted mt-0.5">
          Stake that has left provider `locked` but is still inside the staking
          module — the residual this decomposes is not a direct-node measure
        </p>
      </header>

      <div className="p-4">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono text-[30px] font-semibold leading-none text-accent-cyan">
                {formatEgldBare(data.total_egld)}
              </span>
              <span className="hero-unit">EGLD</span>
            </div>
            <div className="mt-1.5 text-[11px] text-text-secondary">
              one wallet ·{' '}
              <AddressLink address={data.wallet} label={null} />
              {data.share_of_delegation_decline_pct != null && (
                <>
                  {' '}
                  ·{' '}
                  <span className="font-mono">
                    {data.share_of_delegation_decline_pct.toFixed(0)}%
                  </span>{' '}
                  of this week&apos;s delegation TVL decline
                </>
              )}
            </div>
          </div>

          <div className="text-right">
            <div className="text-[9.5px] text-text-muted uppercase tracking-widest">
              {due ? 'Unbonding complete' : 'Becomes liquid in'}
            </div>
            <div className="mt-1 flex items-baseline gap-1.5 justify-end">
              <span
                className="font-mono text-[26px] font-semibold leading-none"
                style={{
                  color: due
                    ? 'var(--color-down)'
                    : 'var(--color-text-primary)',
                }}
              >
                {due ? 'DUE' : daysLeft}
              </span>
              {!due && <span className="hero-unit">days</span>}
            </div>
            {lastLanding && (
              <div className="mt-1 text-[10.5px] text-text-muted font-mono">
                {formatDate(lastLanding)}
              </div>
            )}
          </div>
        </div>

        <div className="mt-4 grid gap-1.5">
          {landing.map((l) => (
            <div
              key={`${l.provider}-${l.date}`}
              className="flex items-baseline justify-between gap-3 text-[11.5px] border-t border-border-subtle pt-1.5"
            >
              <span className="text-text-secondary truncate">
                {l.provider}
              </span>
              <span className="flex items-baseline gap-3 whitespace-nowrap font-mono">
                <span className="text-text-primary">
                  {formatEgldBare(l.amount)}
                </span>
                <span className="text-text-faint">
                  unDelegated {l.date.slice(5)} → lands {l.lands.slice(5)}
                </span>
              </span>
            </div>
          ))}
        </div>

        <div className="mt-4 rounded border border-border-subtle bg-bg-elevated p-3">
          <div className="text-[9.5px] text-text-muted uppercase tracking-widest">
            Destination
          </div>
          <p className="mt-1 text-[12px] text-text-primary font-medium">
            Unresolved — next week&apos;s biggest unknown.
          </p>
          <p className="mt-1 text-[11px] text-text-secondary leading-relaxed">
            A delegation contract = provider rotation, neutral. An exchange or an
            OTC feeder = a distribution event larger than this week&apos;s entire
            one-way OTC figure. Staying in the wallet = idiosyncratic.
          </p>
        </div>

        <div className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-[10.5px] font-mono text-text-muted">
          <span>
            raw residual{' '}
            <span className="text-text-secondary">
              {data.raw_residual_egld > 0 ? '+' : ''}
              {formatEgldBare(data.raw_residual_egld)}
            </span>
          </span>
          <span>
            corrected direct-node{' '}
            <span
              className={
                data.corrected_direct_node_egld >= 0 ? 'text-up' : 'text-down'
              }
            >
              {data.corrected_direct_node_egld > 0 ? '+' : ''}
              {formatEgldBare(data.corrected_direct_node_egld)}
            </span>
          </span>
        </div>
      </div>
    </section>
  )
}
