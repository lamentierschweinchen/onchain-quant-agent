import { useMemo, useRef, useState } from 'react'

/**
 * A time-scaled chart with a hover crosshair.
 *
 * Written because the sparklines it replaces spaced points evenly by index. The
 * readings are NOT evenly spaced — the series so far runs 18:07, 22:28, 22:41,
 * 23:04, 23:16 — so an index-spaced line made a four-hour gap look identical to
 * a twelve-minute one and distorted every slope on the page. X position here
 * comes from the timestamp.
 */

export interface Series {
  key: string
  label: string
  color: string
  /** Values aligned to `times`; null where that reading has no value. */
  values: Array<number | null>
  /** Right-hand axis instead of left. */
  axis?: 'left' | 'right'
  format: (v: number) => string
  /** Fill under the line. */
  area?: boolean
}

interface Props {
  times: number[]
  series: Series[]
  height?: number
  /** Draw a dashed baseline at zero — for series that cross it. */
  zeroLine?: boolean
}

const PAD = { top: 10, right: 4, bottom: 18, left: 4 }

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

/**
 * Bare HH:MM is only unambiguous inside a single day. Across a longer span the
 * labels wrap past midnight and read as running backwards — the first version of
 * this axis showed "00:00 17:49 11:38 05:27 23:16" for a 29-hour window. So the
 * day is included as soon as the span can cross one.
 */
function axisLabel(ms: number, spanMs: number): string {
  const d = new Date(ms)
  const hm = d.toISOString().slice(11, 16)
  if (spanMs < 20 * 3_600_000) return hm
  return `${MONTHS[d.getUTCMonth()]} ${d.getUTCDate()} ${hm}`
}

export function TimeChart({ times, series, height = 132, zeroLine = false }: Props) {
  const wrapRef = useRef<HTMLDivElement>(null)
  const [hover, setHover] = useState<number | null>(null)
  const W = 1000 // viewBox units; the SVG scales to its container

  const scales = useMemo(() => {
    const t0 = Math.min(...times)
    const t1 = Math.max(...times)
    const tSpan = t1 - t0 || 1
    const x = (t: number) => PAD.left + ((t - t0) / tSpan) * (W - PAD.left - PAD.right)

    const bounds: Record<string, { lo: number; hi: number }> = {}
    for (const axis of ['left', 'right'] as const) {
      const vals = series
        .filter((s) => (s.axis ?? 'left') === axis)
        .flatMap((s) => s.values.filter((v): v is number => v != null))
      if (!vals.length) continue
      let lo = Math.min(...vals)
      let hi = Math.max(...vals)
      if (zeroLine) {
        lo = Math.min(lo, 0)
        hi = Math.max(hi, 0)
      }
      const pad = (hi - lo) * 0.12 || Math.abs(hi) * 0.1 || 1
      bounds[axis] = { lo: lo - pad, hi: hi + pad }
    }
    const y = (v: number, axis: 'left' | 'right') => {
      const b = bounds[axis] ?? { lo: 0, hi: 1 }
      const span = b.hi - b.lo || 1
      return height - PAD.bottom - ((v - b.lo) / span) * (height - PAD.top - PAD.bottom)
    }
    return { x, y, t0, t1, bounds }
  }, [times, series, height, zeroLine])

  if (times.length < 2) {
    return (
      <div className="h-[132px] flex items-center justify-center text-[11px] text-text-faint font-mono">
        one reading so far — the shape appears from the second
      </div>
    )
  }

  // A gap counts as unsampled when it is well beyond the normal cadence. Derived
  // from the readings rather than hard-coded, so it holds whether they arrive
  // every minute or every hour.
  const gaps = times.slice(1).map((t, i) => t - times[i]).sort((a, b) => a - b)
  const medianGap = gaps.length ? gaps[Math.floor(gaps.length / 2)] : 0
  const gapLimit = Math.max(medianGap * 4, 90 * 60_000)

  const idx = hover ?? times.length - 1

  const onMove = (e: React.MouseEvent) => {
    const el = wrapRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const frac = (e.clientX - rect.left) / rect.width
    const target = scales.t0 + frac * (scales.t1 - scales.t0)
    let best = 0
    let bestD = Infinity
    times.forEach((t, i) => {
      const d = Math.abs(t - target)
      if (d < bestD) {
        bestD = d
        best = i
      }
    })
    setHover(best)
  }

  // Evenly spaced time ticks across the real span.
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => scales.t0 + f * (scales.t1 - scales.t0))

  return (
    <div ref={wrapRef} onMouseMove={onMove} onMouseLeave={() => setHover(null)} className="relative">
      <svg viewBox={`0 0 ${W} ${height}`} preserveAspectRatio="none"
           className="w-full block" style={{ height }} role="img"
           aria-label={series.map((s) => s.label).join(' and ') + ' over time'}>
        {zeroLine && scales.bounds.left && scales.bounds.left.lo < 0 && (
          <line x1={PAD.left} x2={W - PAD.right} y1={scales.y(0, 'left')} y2={scales.y(0, 'left')}
                stroke="currentColor" className="text-border-strong" strokeWidth="1" strokeDasharray="3 4" />
        )}

        {ticks.map((t, i) => (
          <line key={i} x1={scales.x(t)} x2={scales.x(t)} y1={PAD.top - 4} y2={height - PAD.bottom}
                stroke="currentColor" className="text-border-subtle" strokeWidth="1" />
        ))}

        {series.map((s) => {
          const axis = s.axis ?? 'left'
          // Two reasons to break the line: a null reading, and a gap in time
          // long enough that a straight segment would be an invention rather
          // than a measurement. Broken runs are rejoined by a faint dashed
          // connector, so the shape stays readable but the unsampled stretch is
          // visibly not data. (Without this the series drew a confident diagonal
          // across a two-day hole in the readings.)
          const runs: Array<Array<{ x: number; y: number }>> = []
          let run: Array<{ x: number; y: number }> = []
          let lastT: number | null = null
          s.values.forEach((v, i) => {
            if (v == null) {
              if (run.length) runs.push(run)
              run = []
              lastT = null
              return
            }
            if (lastT != null && times[i] - lastT > gapLimit) {
              if (run.length) runs.push(run)
              run = []
            }
            run.push({ x: scales.x(times[i]), y: scales.y(v, axis) })
            lastT = times[i]
          })
          if (run.length) runs.push(run)

          return (
            <g key={s.key}>
              {runs.slice(1).map((r, ri) => {
                const prev = runs[ri][runs[ri].length - 1]
                const next = r[0]
                return (
                  <line key={`gap${ri}`} x1={prev.x} y1={prev.y} x2={next.x} y2={next.y}
                        stroke={s.color} strokeWidth="1" strokeDasharray="2 5" opacity="0.35"
                        vectorEffect="non-scaling-stroke" />
                )
              })}
              {runs.map((r, ri) => {
                const d = r.map((p, i) => `${i ? 'L' : 'M'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')
                return (
                  <g key={ri}>
                    {s.area && r.length > 1 && (
                      <path d={`${d} L${r[r.length - 1].x},${height - PAD.bottom} L${r[0].x},${height - PAD.bottom} Z`}
                            fill={s.color} opacity="0.1" />
                    )}
                    <path d={d} fill="none" stroke={s.color} strokeWidth="2"
                          strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
                    {r.map((p, i) => (
                      <circle key={i} cx={p.x} cy={p.y} r={1.8} fill={s.color} opacity="0.55" />
                    ))}
                  </g>
                )
              })}
              {s.values[idx] != null && (
                <circle cx={scales.x(times[idx])} cy={scales.y(s.values[idx] as number, axis)}
                        r="3.6" fill={s.color} stroke="#0a0a0a" strokeWidth="1.5" />
              )}
            </g>
          )
        })}

        {hover != null && (
          <line x1={scales.x(times[idx])} x2={scales.x(times[idx])} y1={PAD.top - 4} y2={height - PAD.bottom}
                stroke="currentColor" className="text-text-muted" strokeWidth="1" />
        )}
      </svg>

      <div className="flex justify-between font-mono text-[9px] text-text-faint -mt-3 px-0.5">
        {ticks.map((t, i) => <span key={i}>{axisLabel(t, scales.t1 - scales.t0)}</span>)}
      </div>

      {/* Readout follows the crosshair; falls back to the latest reading. */}
      <div className="mt-2 flex flex-wrap items-baseline gap-x-4 gap-y-1 font-mono text-[11px]">
        <span className={hover != null ? 'text-text-primary' : 'text-text-faint'}>
          {axisLabel(times[idx], scales.t1 - scales.t0)} UTC
        </span>
        {series.map((s) =>
          s.values[idx] == null ? null : (
            <span key={s.key} className="whitespace-nowrap">
              <span className="inline-block w-1.5 h-1.5 rounded-full mr-1.5 align-middle"
                    style={{ background: s.color }} />
              <span className="text-text-muted">{s.label} </span>
              <span className="text-text-primary tabular">{s.format(s.values[idx] as number)}</span>
            </span>
          ),
        )}
      </div>
    </div>
  )
}
