import type { OtcPipeline as OtcPipelineData } from '../types/report'
import { formatEgldBare, formatPct2 } from '../lib/formatters'
import { NullState } from './ui/NullState'

interface Props {
  data?: OtcPipelineData
  /** Report date of the currently selected week — used to mark "this week" on the series. */
  reportDate: string
}

// ---------------------------------------------------------------------------
// The series arrives keyed by run label ({ run16: 309197, run17_peak: 409680 }).
// Order matters and the keys are not sortable as strings, so derive the run
// number and sort on it.
// ---------------------------------------------------------------------------

interface SeriesPoint {
  key: string
  run: number
  label: string
  gross: number | null
  net: number | null
}

function runNumber(key: string): number {
  const m = key.match(/(\d+)/)
  return m ? parseInt(m[1], 10) : 0
}

function buildSeries(data: OtcPipelineData): SeriesPoint[] {
  const gross = data.gross_series_egld_7d ?? {}
  const net = data.net_one_way_series_egld_7d ?? {}
  const runs = new Map<number, SeriesPoint>()

  for (const [key, value] of Object.entries(gross)) {
    const run = runNumber(key)
    if (!run) continue
    runs.set(run, {
      key,
      run,
      label: `#${run}`,
      gross: value,
      net: null,
    })
  }
  for (const [key, value] of Object.entries(net)) {
    const run = runNumber(key)
    if (!run) continue
    const existing = runs.get(run)
    if (existing) existing.net = value
    else runs.set(run, { key, run, label: `#${run}`, gross: null, net: value })
  }

  return Array.from(runs.values()).sort((a, b) => a.run - b.run)
}

/** Runs covered by the wave window, parsed from its date range against the series. */
function waveRuns(
  data: OtcPipelineData,
  series: SeriesPoint[],
): { first: number; last: number } | null {
  const wave = data.wave_window_netting
  if (!wave || series.length === 0) return null
  // The wave window ends on the current report, and its net is compared against
  // the SUM of the weekly nets inside it — so infer the span from that sum.
  const target = wave.sum_of_weekly_nets_egld
  const withNet = series.filter((p) => p.net != null)
  if (withNet.length === 0) return null

  // Walk backwards accumulating weekly nets until the sum matches (1% tolerance).
  let acc = 0
  for (let i = withNet.length - 1; i >= 0; i--) {
    acc += withNet[i].net as number
    if (Math.abs(acc - target) / target < 0.01) {
      return { first: withNet[i].run, last: withNet[withNet.length - 1].run }
    }
  }
  // Fall back to the last two weeks — a wave spans at least two windows.
  if (withNet.length >= 2) {
    return {
      first: withNet[withNet.length - 2].run,
      last: withNet[withNet.length - 1].run,
    }
  }
  return null
}

function Tile({
  label,
  value,
  unit,
  sub,
  accent,
}: {
  label: string
  value: string
  unit?: string
  sub?: React.ReactNode
  accent?: 'cyan' | 'muted' | 'down'
}) {
  const valueColor =
    accent === 'cyan'
      ? 'var(--color-accent-cyan)'
      : accent === 'down'
        ? 'var(--color-down)'
        : 'var(--color-text-primary)'
  return (
    <div className="bg-bg-elevated border border-border rounded p-3">
      <div className="text-[9.5px] text-text-muted uppercase tracking-widest">
        {label}
      </div>
      <div className="mt-1.5 flex items-baseline gap-1">
        <span
          className="font-mono text-[18px] font-semibold leading-none"
          style={{ color: valueColor }}
        >
          {value}
        </span>
        {unit && <span className="hero-unit">{unit}</span>}
      </div>
      {sub && (
        <div className="mt-1 text-[10.5px] text-text-secondary leading-snug">
          {sub}
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Series chart: gross (faint) behind net one-way (solid), with a bracket over
// the runs belonging to one wave. The point of the chart is the tension between
// the bars inside the bracket and the bracket's own number.
// ---------------------------------------------------------------------------

const W = 760
const H = 250
const PAD = { top: 54, right: 16, bottom: 30, left: 52 }

function SeriesChart({
  series,
  wave,
  currentRun,
}: {
  series: SeriesPoint[]
  wave: { first: number; last: number; net: number } | null
  currentRun: number | null
}) {
  const innerW = W - PAD.left - PAD.right
  const innerH = H - PAD.top - PAD.bottom
  const max = Math.max(
    ...series.map((p) => Math.max(p.gross ?? 0, p.net ?? 0)),
    1,
  )
  // Round the scale up to a clean tick.
  const step = max > 1_000_000 ? 500_000 : max > 400_000 ? 200_000 : 50_000
  const top = Math.ceil(max / step) * step
  const ticks: number[] = []
  for (let v = 0; v <= top; v += step) ticks.push(v)

  const slot = innerW / series.length
  const grossW = Math.min(slot * 0.56, 46)
  const netW = grossW * 0.5

  const y = (v: number) => PAD.top + innerH - (v / top) * innerH
  const xCenter = (i: number) => PAD.left + slot * i + slot / 2

  const waveFirstIdx = wave ? series.findIndex((p) => p.run === wave.first) : -1
  const waveLastIdx = wave ? series.findIndex((p) => p.run === wave.last) : -1

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      width="100%"
      role="img"
      aria-label="OTC net one-way distribution per week, with wave-window netting"
      style={{ display: 'block' }}
    >
      {/* gridlines */}
      {ticks.map((t) => (
        <g key={t}>
          <line
            x1={PAD.left}
            x2={W - PAD.right}
            y1={y(t)}
            y2={y(t)}
            stroke="var(--color-border-subtle)"
            strokeWidth={1}
          />
          <text
            x={PAD.left - 8}
            y={y(t) + 3}
            textAnchor="end"
            className="font-mono"
            fontSize={9}
            fill="var(--color-text-faint)"
          >
            {t === 0 ? '0' : formatEgldBare(t)}
          </text>
        </g>
      ))}

      {/* bars */}
      {series.map((p, i) => {
        const cx = xCenter(i)
        const isCurrent = currentRun != null && p.run === currentRun
        const inWave =
          waveFirstIdx >= 0 && i >= waveFirstIdx && i <= waveLastIdx
        return (
          <g key={p.key}>
            {p.gross != null && (
              <rect
                x={cx - grossW / 2}
                y={y(p.gross)}
                width={grossW}
                height={Math.max(y(0) - y(p.gross), 1)}
                fill="var(--color-text-muted)"
                opacity={0.18}
              >
                <title>{`Run #${p.run} gross throughput: ${formatEgldBare(p.gross)} EGLD`}</title>
              </rect>
            )}
            {p.net != null && (
              <rect
                x={cx - netW / 2}
                y={y(p.net)}
                width={netW}
                height={Math.max(y(0) - y(p.net), 1)}
                fill="var(--color-accent-cyan)"
                opacity={inWave ? 0.95 : 0.55}
              >
                <title>{`Run #${p.run} net one-way (weekly frame, upper bound): ${formatEgldBare(p.net)} EGLD`}</title>
              </rect>
            )}
            <text
              x={cx}
              y={H - 10}
              textAnchor="middle"
              className="font-mono"
              fontSize={9.5}
              fill={
                isCurrent
                  ? 'var(--color-accent-cyan)'
                  : 'var(--color-text-muted)'
              }
              fontWeight={isCurrent ? 700 : 400}
            >
              {p.label}
            </text>
            {p.net == null && p.gross != null && (
              <text
                x={cx}
                y={y(p.gross) - 5}
                textAnchor="middle"
                fontSize={8}
                fill="var(--color-text-faint)"
              >
                gross only
              </text>
            )}
          </g>
        )
      })}

      {/* wave bracket */}
      {wave && waveFirstIdx >= 0 && waveLastIdx >= 0 && (
        <g>
          {(() => {
            const x1 = xCenter(waveFirstIdx)
            const x2 = xCenter(waveLastIdx)
            const by = 30
            return (
              <>
                <line
                  x1={x1}
                  x2={x2}
                  y1={by}
                  y2={by}
                  stroke="var(--color-accent-cyan)"
                  strokeWidth={1.25}
                />
                <line
                  x1={x1}
                  x2={x1}
                  y1={by}
                  y2={by + 8}
                  stroke="var(--color-accent-cyan)"
                  strokeWidth={1.25}
                />
                <line
                  x1={x2}
                  x2={x2}
                  y1={by}
                  y2={by + 8}
                  stroke="var(--color-accent-cyan)"
                  strokeWidth={1.25}
                />
                <text
                  x={(x1 + x2) / 2}
                  y={by - 8}
                  textAnchor="middle"
                  className="font-mono"
                  fontSize={10.5}
                  fill="var(--color-accent-cyan)"
                  fontWeight={600}
                >
                  {`${formatEgldBare(wave.net)} netted feed-to-drain`}
                </text>
              </>
            )
          })()}
        </g>
      )}
    </svg>
  )
}

export function OtcPipeline({ data, reportDate }: Props) {
  if (!data) {
    return (
      <NullState message="OTC pipeline netting starts at run #19 — not tracked in this report." />
    )
  }

  const series = buildSeries(data)
  const wave = data.wave_window_netting
  const span = waveRuns(data, series)
  const currentRun = series.length ? series[series.length - 1].run : null

  const grossOut = data.gross_outbound_egld_7d
  const net = data.net_one_way_egld_7d
  const circPct = data.circular_share_pct
  const feed = data.upbit_reload_egld
  const deskDelta =
    data.desk_balance_egld != null && data.previous_desk_balance_egld != null
      ? data.desk_balance_egld - data.previous_desk_balance_egld
      : null

  const venues = (data.venue_netting ?? [])
    .slice()
    .sort((a, b) => Math.abs(b.net_egld) - Math.abs(a.net_egld))

  return (
    <section className="card overflow-hidden">
      <header className="px-4 py-2.5 border-b border-border bg-bg-elevated flex items-baseline justify-between gap-3">
        <div>
          <h3 className="text-[12px] font-semibold text-text-primary tracking-tight">
            OTC Pipeline — distribution, net of round trips
          </h3>
          <p className="text-[10px] text-text-muted mt-0.5">
            Desks fed by exchanges through router wallets · gross counts every
            leg, net one-way strips flow that returns to the venue that supplied
            it
          </p>
        </div>
        <span className="text-[9.5px] font-mono uppercase tracking-widest text-text-faint whitespace-nowrap">
          {reportDate}
        </span>
      </header>

      <div className="p-4 space-y-4">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <Tile
            label="Gross throughput 7d"
            value={formatEgldBare(grossOut)}
            unit="EGLD"
            sub={
              circPct != null ? (
                <>
                  {formatPct2(circPct)} of it round-trips to the venue that
                  supplied it
                </>
              ) : null
            }
          />
          <Tile
            label="Net one-way (weekly frame)"
            value={net != null ? formatEgldBare(net) : '—'}
            unit="EGLD"
            accent="cyan"
            sub={
              wave ? (
                <span className="text-text-muted">
                  Upper bound — see the wave figure below
                </span>
              ) : null
            }
          />
          <Tile
            label="Feed into the desks"
            value={feed != null ? formatEgldBare(feed) : '—'}
            unit="EGLD"
            sub={
              <span className="text-text-muted">
                The leading edge: no feed, no wave
              </span>
            }
          />
          <Tile
            label="Desk balance"
            value={
              data.desk_balance_egld != null
                ? formatEgldBare(data.desk_balance_egld)
                : '—'
            }
            unit="EGLD"
            sub={
              deskDelta != null ? (
                <span
                  className={
                    deskDelta > 0
                      ? 'text-up'
                      : deskDelta < 0
                        ? 'text-down'
                        : 'text-flat'
                  }
                >
                  {deskDelta > 0 ? '+' : ''}
                  {formatEgldBare(deskDelta)} WoW ·{' '}
                  {deskDelta < 0 ? 'passing through' : 'accumulating'}
                </span>
              ) : null
            }
          />
        </div>

        {series.length > 1 && (
          <div className="bg-bg-elevated border border-border rounded p-3">
            <div className="flex items-baseline justify-between gap-3 mb-1">
              <span className="text-[10px] text-text-muted uppercase tracking-widest">
                Net one-way per week vs gross
              </span>
              <span className="flex items-center gap-3 text-[9.5px] font-mono text-text-muted">
                <span className="flex items-center gap-1.5">
                  <span
                    className="inline-block w-2.5 h-2.5 rounded-sm"
                    style={{
                      background: 'var(--color-text-muted)',
                      opacity: 0.25,
                    }}
                  />
                  gross
                </span>
                <span className="flex items-center gap-1.5">
                  <span
                    className="inline-block w-2.5 h-2.5 rounded-sm"
                    style={{ background: 'var(--color-accent-cyan)' }}
                  />
                  net one-way
                </span>
              </span>
            </div>
            <SeriesChart
              series={series}
              wave={
                wave && span
                  ? { ...span, net: wave.net_one_way_egld }
                  : null
              }
              currentRun={currentRun}
            />
            {wave && (
              <p className="mt-2 text-[11px] text-text-secondary leading-relaxed border-t border-border-subtle pt-2">
                Inside the bracket the weekly bars sum to{' '}
                <span className="font-mono text-text-primary">
                  {formatEgldBare(wave.sum_of_weekly_nets_egld)}
                </span>{' '}
                EGLD, but netted feed-to-drain across {wave.window} the wave
                moved{' '}
                <span className="font-mono text-accent-cyan">
                  {formatEgldBare(wave.net_one_way_egld)}
                </span>{' '}
                EGLD one-way — circularity crosses week boundaries, so every
                weekly figure is an upper bound.
              </p>
            )}
          </div>
        )}

        {venues.length > 0 && (
          <div>
            <div className="text-[10px] text-text-muted uppercase tracking-widest mb-1.5">
              Where the flow terminates, this week
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-[11.5px] border-collapse">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left px-2 py-1.5 text-[9.5px] font-medium text-text-muted uppercase tracking-widest">
                      Venue
                    </th>
                    <th className="text-right px-2 py-1.5 text-[9.5px] font-medium text-text-muted uppercase tracking-widest">
                      Desk → venue
                    </th>
                    <th className="text-right px-2 py-1.5 text-[9.5px] font-medium text-text-muted uppercase tracking-widest">
                      Venue → desk
                    </th>
                    <th className="text-right px-2 py-1.5 text-[9.5px] font-medium text-text-muted uppercase tracking-widest">
                      Net
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {venues.map((v) => (
                    <tr
                      key={v.venue}
                      className="border-b border-border/50 hover:bg-surface-hover transition-colors"
                    >
                      <td className="px-2 py-1.5 text-text-primary">
                        {v.venue}
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono text-text-secondary">
                        {formatEgldBare(v.desk_to_venue_egld)}
                      </td>
                      <td className="px-2 py-1.5 text-right font-mono text-text-secondary">
                        {formatEgldBare(v.venue_to_desk_egld)}
                      </td>
                      <td
                        className={[
                          'px-2 py-1.5 text-right font-mono',
                          v.net_egld > 0
                            ? 'text-down'
                            : v.net_egld < 0
                              ? 'text-up'
                              : 'text-flat',
                        ].join(' ')}
                      >
                        {v.net_egld > 0 ? '+' : ''}
                        {formatEgldBare(v.net_egld)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-1.5 text-[10px] text-text-faint">
              Positive net = the venue RECEIVED from the desks (supply arriving
              at an order book). Negative = the venue SOURCED the flow.
            </p>
          </div>
        )}
      </div>
    </section>
  )
}
