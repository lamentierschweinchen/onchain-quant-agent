import { useEffect, useId, useMemo, useRef, useState } from 'react'

/**
 * Where the current move sits in the last year.
 *
 * The live tiles answer "what is happening right now", which on its own reads as
 * a straight line up. This panel is the corrective: at the time of writing EGLD
 * is 113% above its June low and still 64% below the September high, and both
 * facts change how the same 34% day should be read. Without it the page implies
 * a breakout when what it is actually showing is a recovery.
 */

type Pair = [number, number]

interface Chart {
  year: Pair[]
  month: Pair[]
  fetchedAt: string
}

const RANGES = [
  { key: '30d', label: '30D', days: 30 },
  { key: '3m', label: '3M', days: 90 },
  { key: '1y', label: '1Y', days: 365 },
] as const

type RangeKey = (typeof RANGES)[number]['key']

function useChart() {
  const [chart, setChart] = useState<Chart | null>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    let cancelled = false

    // CoinGecko is called from the browser first, for the same reason the live
    // tiles are: its free tier rate-limits per IP, and the edge proxy runs on
    // Vercel's shared addresses, so the proxy is 429ed far more often than any
    // individual visitor would be. The proxy is the second try, and a committed
    // snapshot the third — a year of daily closes barely moves, so a snapshot is
    // a perfectly good last resort. Before this the panel vanished on a 429.
    const CG = 'https://api.coingecko.com/api/v3/coins/elrond-erd-2/market_chart'
    const SOURCES: Array<string | [string, string]> = [
      [`${CG}?vs_currency=usd&days=365&interval=daily`, `${CG}?vs_currency=usd&days=30`],
      '/api/chart',
      'https://raw.githubusercontent.com/lamentierschweinchen/onchain-quant-agent/main/dashboard/public/price-history.json',
      '/price-history.json',
    ]

    const thin = (pairs: Pair[], target: number): Pair[] => {
      if (pairs.length <= target) return pairs
      const step = pairs.length / target
      const out = Array.from({ length: target }, (_, i) => pairs[Math.floor(i * step)])
      if (out[out.length - 1][0] !== pairs[pairs.length - 1][0]) out.push(pairs[pairs.length - 1])
      return out
    }

    ;(async () => {
      let best = null as Chart | null
      for (const src of SOURCES) {
        try {
          let d: Chart
          if (Array.isArray(src)) {
            // Direct: two calls, same shape the proxy would have returned.
            const [yr, mo] = await Promise.all(
              src.map((u) =>
                fetch(u).then((r) => (r.ok ? r.json() : null)).catch(() => null),
              ),
            )
            d = {
              year: yr?.prices ? thin(yr.prices as Pair[], 400) : [],
              month: mo?.prices ? thin(mo.prices as Pair[], 360) : [],
              fetchedAt: new Date().toISOString(),
            }
          } else {
            const res = await fetch(src, { cache: 'no-cache' })
            if (!res.ok) continue
            d = (await res.json()) as Chart
          }
          const year = Array.isArray(d.year) ? d.year : []
          const month = Array.isArray(d.month) ? d.month : []
          if (!year.length && !month.length) continue
          // Merge across sources so a partial live response still wins for the
          // half it did return.
          best = {
            year: year.length ? year : (best?.year ?? []),
            month: month.length ? month : (best?.month ?? []),
            fetchedAt: d.fetchedAt ?? best?.fetchedAt ?? '',
          }
          if (best.year.length && best.month.length) break
        } catch {
          /* try the next source */
        }
      }
      if (cancelled) return
      if (best) setChart(best)
      else setFailed(true)
    })()

    return () => {
      cancelled = true
    }
  }, [])

  return { chart, failed }
}

function fmtDate(ms: number, withTime: boolean): string {
  const d = new Date(ms)
  const day = d.toISOString().slice(0, 10)
  return withTime ? `${day} ${d.toISOString().slice(11, 16)}` : day
}

export function BigPicture({ livePrice }: { livePrice?: number }) {
  const { chart, failed } = useChart()
  const [range, setRange] = useState<RangeKey>('30d')
  const [hover, setHover] = useState<number | null>(null)
  const wrapRef = useRef<HTMLDivElement>(null)
  const gradId = useId()

  const series = useMemo<Pair[]>(() => {
    if (!chart) return []
    // The 30-day window is hourly; the longer ones come from the daily year.
    const base =
      range === '30d'
        ? (chart.month.length ? chart.month : chart.year.filter(([t]) => t >= Date.now() - 31 * 86_400_000))
        : (chart.year.length ? chart.year : chart.month).filter(
            ([t]) => t >= Date.now() - (range === '3m' ? 90 : 366) * 86_400_000,
          )

    // The series is up to an hour stale but the live price is a minute old, so
    // the line is extended to the live reading. Same quantity, fresher source —
    // it also means the tip of the line visibly moves while the page is open.
    if (livePrice == null || !base.length) return base
    return [...base, [Date.now(), livePrice] as Pair]
  }, [chart, range, livePrice])

  const stats = useMemo(() => {
    if (series.length < 2) return null
    let lo = series[0]
    let hi = series[0]
    for (const p of series) {
      if (p[1] < lo[1]) lo = p
      if (p[1] > hi[1]) hi = p
    }
    // The live price is a minute old; the series is up to an hour old. Prefer
    // the live one for "where we are now" so the panel agrees with the hero.
    const nowPrice = livePrice ?? series[series.length - 1][1]
    return {
      lo,
      hi,
      nowPrice,
      fromLow: (nowPrice / lo[1] - 1) * 100,
      fromHigh: (nowPrice / hi[1] - 1) * 100,
      change: (nowPrice / series[0][1] - 1) * 100,
    }
  }, [series, livePrice])

  if (failed)
    return (
      <section className="card p-4">
        <div className="eyebrow">The bigger picture</div>
        <p className="text-[12.5px] text-text-muted mt-1.5">
          Long-range price history is unavailable right now.
        </p>
      </section>
    )

  if (!chart || !stats) return <div className="card h-[300px] animate-pulse" />

  const atHigh = stats.fromHigh > -0.5

  const W = 1000
  const H = 200
  const PAD = { t: 16, b: 22, l: 0, r: 0 }
  const t0 = series[0][0]
  const t1 = series[series.length - 1][0]
  const span = t1 - t0 || 1
  const lo = stats.lo[1]
  const hi = stats.hi[1]
  const vSpan = hi - lo || 1
  const x = (t: number) => ((t - t0) / span) * W
  const y = (v: number) => H - PAD.b - ((v - lo) / vSpan) * (H - PAD.t - PAD.b)

  const line = series.map(([t, v], i) => `${i ? 'L' : 'M'}${x(t).toFixed(1)},${y(v).toFixed(1)}`).join(' ')
  const area = `${line} L${W},${H} L0,${H} Z`

  const idx = hover ?? series.length - 1
  const pt = series[idx]
  const hourly = range === '30d'

  const onMove = (e: React.MouseEvent) => {
    const el = wrapRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const target = t0 + ((e.clientX - rect.left) / rect.width) * span
    let best = 0
    let bestD = Infinity
    series.forEach(([t], i) => {
      const d = Math.abs(t - target)
      if (d < bestD) {
        bestD = d
        best = i
      }
    })
    setHover(best)
  }

  const marker = (p: Pair, label: string, tone: string, above: boolean) => (
    <g>
      <line x1="0" x2={W} y1={y(p[1])} y2={y(p[1])} stroke="currentColor" className={tone}
            strokeWidth="1" strokeDasharray="3 5" opacity="0.5" />
      <circle cx={x(p[0])} cy={y(p[1])} r="3" fill="currentColor" className={tone} />
      <text x={Math.min(Math.max(x(p[0]), 46), W - 46)} y={y(p[1]) + (above ? -8 : 14)}
            textAnchor="middle" className={`${tone} fill-current`}
            style={{ fontSize: 11, fontFamily: 'ui-monospace, monospace' }}>
        {label} ${p[1].toFixed(2)}
      </text>
    </g>
  )

  return (
    <section className="card overflow-hidden">
      <header className="px-4 py-2.5 border-b border-border bg-bg-elevated flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-[12px] font-semibold">The bigger picture</h2>
          <p className="text-[10px] text-text-muted mt-0.5">
            Where today sits in the last {range === '30d' ? '30 days' : range === '3m' ? '3 months' : 'year'}
          </p>
        </div>
        <div className="flex gap-1" role="tablist" aria-label="Time range">
          {RANGES.map((r) => (
            <button
              key={r.key}
              type="button"
              role="tab"
              aria-selected={range === r.key}
              onClick={() => {
                setRange(r.key)
                setHover(null)
              }}
              className={`px-2.5 py-1 rounded font-mono text-[10px] uppercase tracking-wider transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan/60 ${
                range === r.key
                  ? 'bg-accent-cyan/15 text-accent-cyan'
                  : 'text-text-muted hover:text-text-secondary hover:bg-bg-elevated'
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </header>

      {/* The two numbers that reframe the move, before the chart itself. */}
      <div className="grid grid-cols-2 sm:grid-cols-3 divide-x divide-border border-b border-border">
        <div className="px-4 py-3">
          <div className="eyebrow">Above the low</div>
          <div className="font-mono tabular text-[22px] font-semibold text-up mt-1 leading-none">
            +{stats.fromLow.toFixed(0)}%
          </div>
          <div className="font-mono text-[10px] text-text-muted mt-1">
            ${stats.lo[1].toFixed(2)} on {fmtDate(stats.lo[0], false)}
          </div>
        </div>
        <div className="px-4 py-3">
          <div className="eyebrow">{atHigh ? 'At the high' : 'Below the high'}</div>
          {/* When the current price IS the window high, "-0%" reads as a bug
              rather than as the (more interesting) fact that it is the top. */}
          <div className={`font-mono tabular font-semibold mt-1 leading-none ${
            atHigh ? 'text-accent-cyan text-[17px] pt-1' : 'text-down text-[22px]'
          }`}>
            {atHigh ? 'top of the range' : `${stats.fromHigh.toFixed(0)}%`}
          </div>
          <div className="font-mono text-[10px] text-text-muted mt-1">
            ${stats.hi[1].toFixed(2)} on {fmtDate(stats.hi[0], false)}
          </div>
        </div>
        <div className="px-4 py-3 col-span-2 sm:col-span-1">
          <div className="eyebrow">Over the window</div>
          <div className={`font-mono tabular text-[22px] font-semibold mt-1 leading-none ${stats.change >= 0 ? 'text-up' : 'text-down'}`}>
            {stats.change >= 0 ? '+' : ''}{stats.change.toFixed(0)}%
          </div>
          <div className="font-mono text-[10px] text-text-muted mt-1">
            from ${series[0][1].toFixed(2)}
          </div>
        </div>
      </div>

      <div ref={wrapRef} onMouseMove={onMove} onMouseLeave={() => setHover(null)}
           className="relative px-1 pt-2">
        <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="w-full block"
             style={{ height: 200 }} role="img"
             aria-label={`EGLD price over the last ${range}, ${stats.fromLow.toFixed(0)} percent above the low of ${stats.lo[1].toFixed(2)}`}>
          <defs>
            <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#23f7dd" stopOpacity="0.30" />
              <stop offset="100%" stopColor="#23f7dd" stopOpacity="0" />
            </linearGradient>
          </defs>

          <path d={area} fill={`url(#${gradId})`} />
          <path key={range} d={line} pathLength={1} fill="none" stroke="#23f7dd" strokeWidth="2"
                strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke"
                className="draw-in" />

          {marker(stats.lo, 'low', 'text-up', false)}
          {marker(stats.hi, 'high', 'text-down', true)}

          {hover != null && (
            <line x1={x(pt[0])} x2={x(pt[0])} y1={PAD.t - 10} y2={H - PAD.b}
                  stroke="currentColor" className="text-text-muted" strokeWidth="1" />
          )}
          {hover == null && (
            <circle cx={x(pt[0])} cy={y(pt[1])} r="4" fill="#23f7dd" className="pulse-dot" />
          )}
          <circle cx={x(pt[0])} cy={y(pt[1])} r="4" fill="#23f7dd" stroke="#0a0a0a" strokeWidth="2" />
        </svg>

        <div className="flex justify-between font-mono text-[9px] text-text-faint px-1 -mt-1">
          <span>{fmtDate(t0, false)}</span>
          <span>{fmtDate(t0 + span / 2, false)}</span>
          <span>{fmtDate(t1, false)}</span>
        </div>
      </div>

      <div className="px-4 py-3 border-t border-border flex flex-wrap items-baseline gap-x-5 gap-y-1 font-mono text-[11px]">
        <span className={hover != null ? 'text-text-primary' : 'text-text-faint'}>
          {fmtDate(pt[0], hourly)}
        </span>
        <span>
          <span className="text-text-muted">price </span>
          <span className="text-text-primary tabular">${pt[1].toFixed(2)}</span>
        </span>
        <span>
          <span className="text-text-muted">above the low </span>
          <span className="text-up tabular">+{((pt[1] / lo - 1) * 100).toFixed(0)}%</span>
        </span>
        <span className="text-text-faint">
          {hover != null ? 'hover to scrub' : 'hover the chart to read any day'}
        </span>
      </div>
    </section>
  )
}
