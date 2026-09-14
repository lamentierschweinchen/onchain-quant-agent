import { useId, useMemo, useState } from 'react'
import type { MexPairEvent, PairCall } from '../types/report'
import { formatTokenPrice, formatPriceFull, formatEgldBare, formatUsd } from '../lib/formatters'
import { accountUrl, txUrl } from '../lib/constants'
import { useElementWidth } from '../hooks/useElementWidth'
import { StatTile } from './ui/StatTile'

interface Props {
  event: MexPairEvent
}

// ---------------------------------------------------------------------------
// A venue-level state change drawn against the series it moved.
//
// The first prose version of this finding read "pause, then spike", because it
// was built from daily closes. Plotted hourly, MEX had already left its range
// before the pool was paused. The panel exists to make that order of events
// visible at a glance: where the move starts, where the pool froze, how far the
// price went. The rug underneath is the pool's own transaction list, so the wall
// of failed withdrawals is data rather than description.
// ---------------------------------------------------------------------------

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const H_CHART = 240
const H_RUG = 64
const PAD = { top: 30, right: 64, bottom: 24, left: 12 }
const HOUR = 3_600_000

function fmtDay(ms: number) {
  const d = new Date(ms)
  return `${MONTHS[d.getUTCMonth()]} ${d.getUTCDate()}`
}
const hhmm = (ms: number) => new Date(ms).toISOString().slice(11, 16)
const fmtStamp = (ms: number) => `${fmtDay(ms)} · ${hhmm(ms)} UTC`
function fmtDuration(ms: number) {
  const m = Math.round(ms / 60_000)
  const h = Math.floor(m / 60)
  return h ? `${h}h${String(m % 60).padStart(2, '0')}m` : `${m}m`
}

type CallKind = 'withdraw' | 'swap' | 'other'
function kindOf(c: PairCall): CallKind {
  if (c.fn === 'removeLiquidity') return 'withdraw'
  if (c.fn && c.fn.startsWith('swap')) return 'swap'
  return 'other'
}

function median(xs: number[]) {
  const s = [...xs].sort((a, b) => a - b)
  return s[Math.floor(s.length / 2)]
}

interface Model {
  pts: Array<[number, number, number]>
  pauseMs: number
  moveMs: number
  baseline: number
  atPause: number
  peakMultiple: number
  calls: Array<PairCall & { ms: number; kind: CallKind }>
  failed: number
  failedBy: Record<CallKind, number>
  okAfter: number
}

function buildModel(event: MexPairEvent): Model | null {
  const pts = event.price_series_hourly
  if (!pts?.length) return null
  const pauseMs = Date.parse(event.paused_at_utc)
  const prices = pts.map((p) => p[1])
  const hi = Math.max(...prices)
  const peakIdx = prices.indexOf(hi)
  // Search only the day before the pause (or before the peak, if that came
  // first). Scanning from the start of the series trips on ordinary drift.
  const pauseIdx = Math.max(0, pts.findIndex((p) => p[0] > pauseMs) - 1)
  const anchor = Math.min(pauseIdx, peakIdx)
  const baseEnd = Math.max(1, anchor - 24)
  // Pre-move level: the median of the 48 hours before that search window.
  const baseline = median(prices.slice(Math.max(0, baseEnd - 48), baseEnd))
  let moveIdx = anchor
  for (let i = baseEnd; i <= anchor; i++) {
    if (prices[i] > baseline * 1.08 && prices.slice(i, anchor + 1).every((v) => v > baseline * 1.05)) {
      moveIdx = i
      break
    }
  }
  const calls = (event.pair_calls ?? []).map((c) => ({ ...c, ms: c.ts * 1000, kind: kindOf(c) }))
  const after = calls.filter((c) => c.ms > pauseMs && c.fn !== 'pause')
  const failedCalls = after.filter((c) => c.status === 'fail')
  return {
    pts,
    pauseMs,
    moveMs: pts[moveIdx][0],
    baseline,
    atPause: prices[pauseIdx] / baseline,
    peakMultiple: hi / baseline,
    calls,
    failed: failedCalls.length,
    failedBy: {
      withdraw: failedCalls.filter((c) => c.kind === 'withdraw').length,
      swap: failedCalls.filter((c) => c.kind === 'swap').length,
      other: failedCalls.filter((c) => c.kind === 'other').length,
    },
    okAfter: after.filter((c) => c.status === 'success').length,
  }
}

export function MexPauseTimeline({ event }: Props) {
  const { ref, width } = useElementWidth<HTMLDivElement>()
  const [hover, setHover] = useState<number | null>(null)
  const [range, setRange] = useState<'zoom' | 'all'>('zoom')
  const model = useMemo(() => buildModel(event), [event])

  const pauseMs = Date.parse(event.paused_at_utc)
  const quoteCg = event.mex_price_coingecko_now
  const quoteApi = event.mex_price_tokens_api
  const apiGap = quoteCg && quoteApi ? (100 * (quoteApi - quoteCg)) / quoteCg : null
  const dexHasPrice = event.mex_price_mex_economics != null && event.mex_price_mex_economics > 0
  const hmexPct =
    event.hmex_supply != null && event.hmex_prev_supply
      ? (100 * (event.hmex_supply - event.hmex_prev_supply)) / event.hmex_prev_supply
      : null
  const wow =
    quoteCg != null && event.mex_price_prev
      ? (100 * (quoteCg - event.mex_price_prev)) / event.mex_price_prev
      : null

  return (
    <section className="card" aria-labelledby="mex-pause-title">
      {/* ---------- header: the finding, in words ---------- */}
      <header className="px-4 py-3 border-b border-border bg-bg-elevated flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2 sm:gap-3">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span
              className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded font-mono text-[10px] font-semibold uppercase tracking-wider"
              style={{
                color: 'var(--color-severity-critical)',
                background: 'color-mix(in srgb, var(--color-severity-critical) 12%, transparent)',
                border: '1px solid color-mix(in srgb, var(--color-severity-critical) 35%, transparent)',
              }}
            >
              <span aria-hidden className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--color-severity-critical)' }} />
              Paused
            </span>
            <h3 id="mex-pause-title" className="text-[13px] font-semibold text-text-primary tracking-tight">
              MEX/WEGLD pool, frozen since {fmtStamp(pauseMs)}
            </h3>
          </div>
          {model && (
            <p className="text-[12px] text-text-secondary mt-1.5 max-w-[78ch] leading-relaxed">
              The xExchange router owner paused the pool{' '}
              <span className="text-text-primary">
                {fmtDuration(pauseMs - model.moveMs)} after MEX had started moving
              </span>
              , with the price already{' '}
              <span className="font-mono text-text-primary">{model.atPause.toFixed(1)}×</span> its
              pre-move level. It went on to{' '}
              <span className="font-mono text-text-primary">{model.peakMultiple.toFixed(1)}×</span>.
              The liquidity is still inside, withdrawals fail, and{' '}
              <span className="font-mono text-text-primary">{model.failed}</span> calls have bounced
              since.
            </p>
          )}
        </div>
        <div className="flex items-center gap-1 text-[11px] font-mono -ml-2.5 sm:ml-0 shrink-0">
          <a
            href={txUrl(event.pause_tx)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center min-h-8 px-2.5 rounded text-text-secondary hover:text-accent-cyan hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan transition-colors"
          >
            Pause tx ↗
          </a>
          <a
            href={accountUrl(event.pair_address)}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center min-h-8 px-2.5 rounded text-text-secondary hover:text-accent-cyan hover:bg-surface-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan transition-colors"
          >
            Pool contract ↗
          </a>
        </div>
      </header>

      <div className="p-4 space-y-4">
        {/* ---------- tiles ---------- */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <StatTile
            label="Still locked in the pool"
            value={formatEgldBare(event.pair_holds_wegld)}
            unit="WEGLD"
            sub={
              <>
                + {(event.pair_holds_mex / 1e9).toFixed(1)}B MEX · {formatUsd(event.prev_pair_tvl_usd)} of
                liquidity last week, the #2 pool on xExchange
              </>
            }
          />
          <StatTile
            label="Failed calls since the pause"
            value={String(model ? model.failed : event.failed_txs_7d)}
            unit="txs"
            accent="critical"
            sub={
              model ? (
                <>
                  <span className="font-mono text-text-primary">{model.failedBy.withdraw}</span> withdrawals ·{' '}
                  <span className="font-mono text-text-primary">{model.failedBy.swap}</span> swaps
                  {model.failedBy.other > 0 && <> · {model.failedBy.other} other</>}
                </>
              ) : null
            }
          />
          <StatTile
            label="MEX price · CoinGecko"
            value={formatTokenPrice(quoteCg)}
            title={formatPriceFull(quoteCg)}
            sub={
              <>
                Tokens API <span className="font-mono text-text-primary">{formatTokenPrice(quoteApi)}</span>
                {apiGap != null && <span className="font-mono"> ({apiGap > 0 ? '+' : ''}{apiGap.toFixed(0)}%)</span>}
                {' · '}xExchange:{' '}
                {dexHasPrice ? (
                  <span className="font-mono text-text-primary">{formatTokenPrice(event.mex_price_mex_economics)}</span>
                ) : (
                  'no price while the pool is frozen'
                )}
              </>
            }
          >
            {wow != null && (
              <span className="font-mono text-[12px] text-up">
                {wow > 0 ? '+' : ''}
                {wow.toFixed(0)}% WoW
              </span>
            )}
          </StatTile>
          <StatTile
            label="Hatom HMEX supply"
            value={hmexPct != null ? `+${hmexPct.toFixed(0)}%` : '—'}
            sub={
              <>
                {event.hmex_supply != null && event.hmex_prev_supply != null && (
                  <span className="font-mono">
                    {(event.hmex_prev_supply / 1e12).toFixed(1)}T → {(event.hmex_supply / 1e12).toFixed(1)}T ·{' '}
                  </span>
                )}
                MEX went into Hatom lending, not out through the pool
              </>
            }
          />
        </div>

        {/* ---------- chart ---------- */}
        {model && (
          <div className="bg-bg-elevated border border-border rounded-md p-3">
            <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 mb-2">
              <span className="text-[10px] text-text-muted uppercase tracking-widest">
                MEX price · hourly · log scale
              </span>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                <Legend />
                <RangeToggle
                  value={range}
                  onChange={(r) => {
                    setRange(r)
                    setHover(null)
                  }}
                />
              </div>
            </div>
            <div ref={ref} style={{ minHeight: H_CHART + H_RUG }}>
              {width != null && (
                <TimelineChart width={width} model={model} range={range} hover={hover} setHover={setHover} />
              )}
            </div>
            <p className="mt-2 pt-2 border-t border-border-subtle text-[11px] text-text-secondary leading-relaxed">
              Price is CoinGecko's hourly series, because no onchain pool prices MEX any more. The two
              rows below the chart are every transaction sent to the pool contract.
              {model.okAfter > 0 && ` ${model.okAfter} calls after the pause still succeeded.`} The
              reason for the pause is not recorded onchain.
            </p>
          </div>
        )}
      </div>
    </section>
  )
}

function RangeToggle({ value, onChange }: { value: 'zoom' | 'all'; onChange: (v: 'zoom' | 'all') => void }) {
  const opts: Array<['zoom' | 'all', string]> = [
    ['zoom', '72 hours'],
    ['all', '14 days'],
  ]
  return (
    <div role="group" aria-label="Chart range" className="inline-flex rounded-md border border-border bg-bg p-0.5">
      {opts.map(([v, label]) => (
        <button
          key={v}
          type="button"
          aria-pressed={value === v}
          onClick={() => onChange(v)}
          className={[
            'min-h-7 px-2.5 rounded text-[11px] font-mono transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan',
            value === v ? 'bg-surface-strong text-text-primary' : 'text-text-muted hover:text-text-secondary',
          ].join(' ')}
        >
          {label}
        </button>
      ))}
    </div>
  )
}

function Legend() {
  return (
    <span className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] font-mono text-text-secondary">
      <span className="flex items-center gap-1.5">
        <span aria-hidden className="inline-block w-4 h-[2px] rounded" style={{ background: 'var(--color-accent-cyan)' }} />
        price
      </span>
      <span className="flex items-center gap-1.5">
        <span aria-hidden className="inline-block w-2.5 h-2.5 rounded-sm hatch-frozen border border-border" />
        frozen
      </span>
      <span className="flex items-center gap-1.5">
        <span aria-hidden className="inline-block w-[3px] h-2.5 rounded-sm" style={{ background: 'var(--color-severity-critical)' }} />
        failed
      </span>
      <span className="flex items-center gap-1.5">
        <span aria-hidden className="inline-block w-[3px] h-2.5 rounded-sm" style={{ background: 'var(--color-text-secondary)' }} />
        succeeded
      </span>
    </span>
  )
}

function TimelineChart({
  width,
  model,
  range,
  hover,
  setHover,
}: {
  width: number
  model: Model
  range: 'zoom' | 'all'
  hover: number | null
  setHover: (i: number | null) => void
}) {
  const hintId = useId()
  // Announce the tooltip to screen readers only when the keyboard moved it;
  // a live region that fires on every mouse move is noise.
  const [viaKeyboard, setViaKeyboard] = useState(false)
  const { pauseMs, moveMs, baseline } = model
  const zoom = range === 'zoom'
  // 72-hour view: a day and a bit of calm before the move, then everything after.
  const from = zoom ? moveMs - 30 * HOUR : model.pts[0][0]
  const pts = model.pts.filter((p) => p[0] >= from)
  const calls = model.calls.filter((c) => c.ms >= from)
  const t0 = pts[0][0]
  const t1 = pts[pts.length - 1][0]
  const lo = Math.min(...pts.map((p) => p[1]))
  const hi = Math.max(...pts.map((p) => p[1]))
  const peak = pts[pts.findIndex((p) => p[1] === hi)]

  const innerW = width - PAD.left - PAD.right
  const x = (ms: number) => PAD.left + ((ms - t0) / (t1 - t0 || 1)) * innerW
  const lLo = Math.log10(lo * 0.85)
  const lHi = Math.log10(hi * 1.15)
  const y = (v: number) => PAD.top + (1 - (Math.log10(v) - lLo) / (lHi - lLo)) * (H_CHART - PAD.top - PAD.bottom)

  const ticks = [2e-7, 3e-7, 5e-7, 1e-6, 2e-6, 3e-6, 5e-6].filter((v) => v >= lo * 0.85 && v <= hi * 1.15)
  const tickStep = zoom ? (width < 560 ? 24 : 6) * HOUR : (width < 560 ? 4 : 2) * 24 * HOUR
  const timeTicks: number[] = []
  for (let d = Math.ceil(t0 / tickStep) * tickStep; d <= t1; d += tickStep) timeTicks.push(d)

  const line = pts.map((p, i) => `${i ? 'L' : 'M'}${x(p[0]).toFixed(1)},${y(p[1]).toFixed(1)}`).join('')
  const area = `${line}L${x(t1).toFixed(1)},${H_CHART - PAD.bottom}L${x(t0).toFixed(1)},${H_CHART - PAD.bottom}Z`
  const px = x(pauseMs)
  const peakX = x(peak[0])
  const peakNearPause = Math.abs(peakX - px) < 48

  const hp = hover != null ? pts[hover] : null
  const nearest = (clientX: number, rect: DOMRect) => {
    const ms = t0 + ((clientX - rect.left - PAD.left) / innerW) * (t1 - t0)
    let best = 0
    let bd = Infinity
    pts.forEach((p, i) => {
      const d = Math.abs(p[0] - ms)
      if (d < bd) {
        bd = d
        best = i
      }
    })
    return best
  }
  const onKey = (e: React.KeyboardEvent) => {
    const cur = hover ?? pts.length - 1
    const step = e.shiftKey ? 24 : 1
    const next =
      e.key === 'ArrowLeft'
        ? Math.max(0, cur - step)
        : e.key === 'ArrowRight'
          ? Math.min(pts.length - 1, cur + step)
          : e.key === 'Home'
            ? 0
            : e.key === 'End'
              ? pts.length - 1
              : null
    if (next != null) {
      setViaKeyboard(true)
      setHover(next)
      e.preventDefault()
    } else if (e.key === 'Escape') setHover(null)
  }

  const callsNear = hp ? calls.filter((c) => Math.abs(c.ms - hp[0]) <= 30 * 60_000) : []
  const failedNear = callsNear.filter((c) => c.status === 'fail').length
  const tipW = 196
  const tipLeft = hp ? (x(hp[0]) > width - tipW - 24 ? x(hp[0]) - tipW - 12 : x(hp[0]) + 12) : 0

  const rows: Array<['withdraw' | 'swap', string, number]> = [
    ['withdraw', 'Withdrawals', 26],
    ['swap', 'Swaps', 52],
  ]

  return (
    <div className="relative">
      <span id={hintId} className="sr-only">
        Arrow keys step through hourly values, Shift plus arrow moves a day, Escape clears.
      </span>
      {/* Persistent live region: it must exist before its text changes to be announced. */}
      <div role="status" aria-live="polite" className="sr-only">
        {viaKeyboard && hp
          ? `${fmtStamp(hp[0])}, ${formatTokenPrice(hp[1])}, ${(hp[1] / baseline).toFixed(2)} times pre-move, ${hp[0] > pauseMs ? 'pool frozen' : 'pool trading'}`
          : ''}
      </div>
      <svg
        width={width}
        height={H_CHART + H_RUG}
        role="group"
        tabIndex={0}
        aria-label={`MEX hourly price, ${fmtDay(t0)} to ${fmtDay(t1)}, log scale. The move started ${fmtStamp(moveMs)}; the pool was paused ${fmtStamp(pauseMs)} with the price at ${model.atPause.toFixed(1)} times its pre-move level; it peaked at ${formatPriceFull(peak[1])}.`}
        aria-describedby={hintId}
        className="block rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan cursor-crosshair"
        onMouseMove={(e) => {
          if (viaKeyboard) setViaKeyboard(false)
          setHover(nearest(e.clientX, e.currentTarget.getBoundingClientRect()))
        }}
        onMouseLeave={() => setHover(null)}
        onBlur={() => setHover(null)}
        onKeyDown={onKey}
      >
        <defs>
          <pattern id="mex-hatch" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
            <line x1="0" y1="0" x2="0" y2="6" stroke="var(--color-severity-critical)" strokeWidth="1" opacity="0.2" />
          </pattern>
          <linearGradient id="mex-area" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0%" stopColor="var(--color-accent-cyan)" stopOpacity="0.16" />
            <stop offset="100%" stopColor="var(--color-accent-cyan)" stopOpacity="0" />
          </linearGradient>
        </defs>

        <rect
          x={px}
          y={PAD.top - 14}
          width={Math.max(0, x(t1) - px)}
          height={H_CHART - PAD.top - PAD.bottom + 14 + H_RUG}
          fill="url(#mex-hatch)"
        />

        {ticks.map((t) => (
          <g key={t}>
            <line x1={PAD.left} x2={width - PAD.right} y1={y(t)} y2={y(t)} stroke="var(--color-border-subtle)" />
            <text x={width - PAD.right + 8} y={y(t) + 3.5} fontSize={10.5} className="font-mono" fill="var(--color-text-secondary)">
              {formatTokenPrice(t)}
            </text>
          </g>
        ))}

        <line x1={PAD.left} x2={width - PAD.right} y1={y(baseline)} y2={y(baseline)} stroke="var(--color-text-muted)" strokeDasharray="2 4" />
        <text x={PAD.left + 4} y={y(baseline) - 6} fontSize={10.5} fill="var(--color-text-secondary)">
          pre-move level
        </text>

        <path d={area} fill="url(#mex-area)" />
        <path d={line} fill="none" stroke="var(--color-accent-cyan)" strokeWidth={1.75} strokeLinejoin="round" />

        {/* move start: labelled only in the zoomed view, where there is room */}
        {moveMs >= t0 && (
          <g>
            <line
              x1={x(moveMs)}
              x2={x(moveMs)}
              y1={PAD.top - 14}
              y2={H_CHART - PAD.bottom}
              stroke="var(--color-accent-cyan)"
              strokeDasharray="2 3"
              opacity={0.7}
            />
            {zoom && width >= 560 && (
              <text
                x={x(moveMs) - 6}
                y={Math.min(y(baseline) + 18, H_CHART - PAD.bottom - 6)}
                textAnchor="end"
                fontSize={11}
                fill="var(--color-accent-cyan)"
              >
                move starts {hhmm(moveMs)}
              </text>
            )}
          </g>
        )}

        <line x1={px} x2={px} y1={PAD.top - 14} y2={H_CHART + H_RUG - 2} stroke="var(--color-severity-critical)" strokeWidth={1.25} />
        <text x={px + 6} y={PAD.top - 18} fontSize={11} fontWeight={600} fill="var(--color-severity-critical)">
          Paused {hhmm(pauseMs)}
        </text>

        <circle cx={peakX} cy={y(peak[1])} r={3.5} fill="var(--color-bg-elevated)" stroke="var(--color-accent-cyan)" strokeWidth={1.5} />
        <text
          x={peakNearPause ? peakX + 4 : peakX}
          y={y(peak[1]) - 9}
          textAnchor={peakNearPause ? 'start' : 'middle'}
          fontSize={11.5}
          fontWeight={600}
          className="font-mono"
          fill="var(--color-text-primary)"
        >
          {model.peakMultiple.toFixed(1)}×
        </text>

        {timeTicks.map((d) => (
          <text key={d} x={x(d)} y={H_CHART - 6} textAnchor="middle" fontSize={10.5} className="font-mono" fill="var(--color-text-secondary)">
            {zoom && new Date(d).getUTCHours() !== 0 ? hhmm(d) : fmtDay(d)}
          </text>
        ))}

        {/* rug: the pool's own transactions */}
        <g transform={`translate(0, ${H_CHART})`}>
          {rows.map(([k, label, ry]) => {
            const failedHere = calls.filter((c) => c.kind === k && c.status === 'fail' && c.ms > pauseMs).length
            return (
              <g key={k}>
                <line x1={PAD.left} x2={width - PAD.right} y1={ry} y2={ry} stroke="var(--color-border-subtle)" />
                <text x={PAD.left + 4} y={ry - 8} fontSize={10} fill="var(--color-text-secondary)">
                  {label}
                  {failedHere > 0 && ` · ${failedHere} failed since pause`}
                </text>
                {calls
                  .filter((c) => c.kind === k)
                  .map((c, i) => (
                    <line
                      key={`${c.ts}-${i}`}
                      x1={x(c.ms)}
                      x2={x(c.ms)}
                      y1={ry - 5}
                      y2={ry + 5}
                      stroke={c.status === 'fail' ? 'var(--color-severity-critical)' : 'var(--color-text-secondary)'}
                      strokeWidth={1.25}
                      opacity={c.status === 'fail' ? 0.85 : 0.7}
                    />
                  ))}
              </g>
            )
          })}
        </g>

        {hp && (
          <g pointerEvents="none">
            <line x1={x(hp[0])} x2={x(hp[0])} y1={PAD.top - 14} y2={H_CHART + H_RUG - 2} stroke="var(--color-text-secondary)" strokeDasharray="3 3" />
            <circle cx={x(hp[0])} cy={y(hp[1])} r={4} fill="var(--color-accent-cyan)" stroke="var(--color-bg-elevated)" strokeWidth={2} />
          </g>
        )}
      </svg>

      {hp && (
        <div
            className="absolute top-2 pointer-events-none z-10 rounded-md border border-border-strong bg-surface-strong/95 px-3 py-2 shadow-lg"
          style={{ left: Math.max(4, tipLeft), width: tipW }}
        >
          <div className="text-[10.5px] font-mono text-text-secondary">{fmtStamp(hp[0])}</div>
          <div className="mt-1 flex items-baseline justify-between gap-2">
            <span className="font-mono text-[14px] font-semibold text-text-primary" title={formatPriceFull(hp[1])}>
              {formatTokenPrice(hp[1])}
            </span>
            <span className="font-mono text-[11px] text-text-secondary">{(hp[1] / baseline).toFixed(2)}× pre-move</span>
          </div>
          <div className="mt-1 text-[11px] text-text-secondary">
            24h volume <span className="font-mono text-text-primary">{formatUsd(hp[2])}</span>
          </div>
          <div className="mt-0.5 text-[11px] text-text-secondary">
            {hp[0] > pauseMs ? 'Pool frozen' : 'Pool trading'}
            {failedNear > 0 && (
              <>
                {' '}
                · <span className="font-mono text-text-primary">{failedNear}</span> failed this hour
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
