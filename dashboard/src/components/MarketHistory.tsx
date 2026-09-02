import { useEffect, useState } from 'react'
import { formatUsd } from '../lib/formatters'

/**
 * Price against open interest over time — the pair that separates a squeeze
 * firing from a squeeze building, which a point-in-time reading cannot do.
 *
 * Open interest is the total notional in open leveraged contracts. It falls when
 * positions close and rises when new ones open, so reading it against the price
 * direction gives four distinct states (see VERDICTS below). Funding sign says
 * which side is crowded; this says whether that side is growing or leaving.
 */

export interface HistoryPoint {
  t: string
  price: number
  /** Null on points recorded before derivatives were tracked. */
  oi: number | null
  oiShare: number | null
  funding: number | null
  desks: number
  change24h: number
}

interface History {
  updated: string
  points: HistoryPoint[]
}

const VERDICTS: Record<string, { title: string; detail: string; tone: string }> = {
  'up-down': {
    title: 'Positions closing as price rises',
    detail:
      'Price is up over the window and the amount of leverage outstanding has fallen, which means traders are closing bets rather than opening them.',
    tone: 'text-accent-cyan',
  },
  'up-up': {
    title: 'Positions building as price rises',
    detail:
      'Price is up over the window and leverage outstanding has grown. Traders are adding bets rather than closing them, so nothing has been forced to unwind yet.',
    tone: 'text-severity-medium',
  },
  'down-down': {
    title: 'Positions closing as price falls',
    detail:
      'Price is down over the window and leverage outstanding has fallen. Leverage is leaving the market.',
    tone: 'text-text-secondary',
  },
  'down-up': {
    title: 'Positions building as price falls',
    detail:
      'Price is down over the window and leverage outstanding has grown. Traders are adding bets into the fall.',
    tone: 'text-severity-medium',
  },
}

function Spark({
  values,
  color,
  zero = false,
  height = 46,
}: {
  values: number[]
  color: string
  /** Draw a baseline at zero — for series that cross it, like funding. */
  zero?: boolean
  height?: number
}) {
  if (values.length < 2) return null
  const W = 260
  const lo = Math.min(...values, zero ? 0 : Math.min(...values))
  const hi = Math.max(...values, zero ? 0 : Math.max(...values))
  const span = hi - lo || 1
  const x = (i: number) => (i / (values.length - 1)) * W
  const y = (v: number) => height - ((v - lo) / span) * (height - 6) - 3
  const d = values.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(' ')
  const area = `${d} L${W},${height} L0,${height} Z`
  return (
    <svg
      viewBox={`0 0 ${W} ${height}`}
      preserveAspectRatio="none"
      className="w-full"
      style={{ height }}
      aria-hidden="true"
    >
      {zero && lo < 0 && hi > 0 && (
        <line x1="0" x2={W} y1={y(0)} y2={y(0)} stroke="currentColor" strokeWidth="1"
              className="text-border-strong" strokeDasharray="2 3" />
      )}
      <path d={area} fill={color} opacity="0.12" />
      <path d={d} fill="none" stroke={color} strokeWidth="1.6" strokeLinejoin="round" />
      <circle cx={x(values.length - 1)} cy={y(values[values.length - 1])} r="2.6" fill={color} />
    </svg>
  )
}

function Panel({
  label,
  latest,
  sub,
  children,
}: {
  label: string
  latest: string
  sub?: string
  children: React.ReactNode
}) {
  return (
    <div className="card p-3.5">
      <div className="flex items-baseline justify-between gap-3">
        <span className="eyebrow">{label}</span>
        <span className="font-mono tabular text-[13px] text-text-primary">{latest}</span>
      </div>
      <div className="mt-2">{children}</div>
      {sub && <div className="font-mono text-[10px] text-text-muted mt-1.5">{sub}</div>}
    </div>
  )
}

export function useHistory() {
  const [hist, setHist] = useState<History | null>(null)
  const [missing, setMissing] = useState(false)

  useEffect(() => {
    let cancelled = false

    // An hourly GitHub Action commits new readings to the repo. Reading them
    // from raw.githubusercontent means a new point appears without redeploying
    // the site; the copy bundled at build time is the fallback when that is
    // unreachable (rate limit, offline, or a fork without the workflow).
    const RAW =
      'https://raw.githubusercontent.com/lamentierschweinchen/onchain-quant-agent/main/dashboard/public/market-history.json'

    const pick = (d: unknown): History | null => {
      const h = d as History | null
      return h && Array.isArray(h.points) && h.points.length ? h : null
    }

    ;(async () => {
      for (const url of [RAW, '/market-history.json']) {
        try {
          const res = await fetch(url, { cache: 'no-cache' })
          if (!res.ok) continue
          const parsed = pick(await res.json())
          if (parsed && !cancelled) {
            setHist(parsed)
            return
          }
        } catch {
          /* try the next source */
        }
      }
      if (!cancelled) setMissing(true)
    })()

    return () => {
      cancelled = true
    }
  }, [])

  return { hist, missing }
}

export function MarketHistory() {
  const { hist, missing } = useHistory()

  if (missing) {
    return (
      <section className="card p-4">
        <div className="eyebrow">History</div>
        <p className="text-[12.5px] text-text-muted mt-1.5 max-w-[70ch]">
          No readings recorded yet. Run{' '}
          <code className="font-mono text-accent-cyan/90">scripts/poll_market.py</code> on a
          schedule to build the series — a single reading tells you which side is crowded, but
          only a series tells you whether that side is growing or leaving.
        </p>
      </section>
    )
  }
  if (!hist) return null

  const pts = hist.points
  const first = pts[0]
  const last = pts[pts.length - 1]
  const withOi = pts.filter((p): p is HistoryPoint & { oi: number } => p.oi != null)
  const oiFirst = withOi[0]
  const oiLast = withOi[withOi.length - 1]
  const priceUp = last.price >= first.price
  const oiUp = oiLast && oiFirst ? oiLast.oi >= oiFirst.oi : false
  const verdict = VERDICTS[`${priceUp ? 'up' : 'down'}-${oiUp ? 'up' : 'down'}`]

  const fundings = pts.map((p) => p.funding).filter((f): f is number => f != null)
  const hours = (new Date(last.t).getTime() - new Date(first.t).getTime()) / 3_600_000

  return (
    <section className="card overflow-hidden">
      <header className="px-4 py-2.5 border-b border-border bg-bg-elevated flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h2 className="text-[12px] font-semibold">
            {/* the answer is the headline; the question lives in the detail */}
            What the leverage is doing
          </h2>
          <p className="text-[10px] text-text-muted mt-0.5">
            Price against open interest. {pts.length} readings over{' '}
            {hours < 24 ? `${hours.toFixed(1)}h` : `${(hours / 24).toFixed(1)} days`}
          </p>
        </div>
        <span className={`text-[13px] font-semibold ${verdict.tone}`}>{verdict.title}</span>
      </header>

      <div className="p-4 space-y-4">
        <p className="text-[12.5px] text-text-secondary leading-relaxed max-w-[74ch]">
          {verdict.detail}
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <Panel
            label="Price"
            latest={`$${last.price.toFixed(2)}`}
            sub={`from $${first.price.toFixed(2)}`}
          >
            <Spark values={pts.map((p) => p.price)} color="#23f7dd" />
          </Panel>
          <Panel
            label="Open interest"
            latest={oiLast ? formatUsd(oiLast.oi) : '—'}
            sub={oiFirst && oiLast ? `${oiLast.oiShare != null ? `${oiLast.oiShare.toFixed(1)}% of market cap · ` : ''}from ${formatUsd(oiFirst.oi)}` : undefined}
          >
            <Spark values={withOi.map((p) => p.oi)} color={oiUp ? '#f0a020' : '#23f7dd'} />
          </Panel>
          <Panel
            label="Funding rate"
            latest={last.funding != null ? `${last.funding.toFixed(4)}%` : '—'}
            sub={
              fundings.length > 1
                ? last.funding != null && fundings[0] != null && last.funding < fundings[0]
                  ? 'getting more negative — shorts paying more'
                  : 'less negative — short pressure easing'
                : undefined
            }
          >
            <Spark values={fundings} color="#f4525a" zero />
          </Panel>
        </div>

        <div className="text-[11px] text-text-muted leading-relaxed max-w-[74ch] border-t border-border-subtle pt-3">
          <span className="font-mono text-[9.5px] uppercase tracking-widest text-text-faint">
            How to read it
          </span>
          <p className="mt-1.5">
            Open interest counts <em>both</em> sides of every contract, so it measures how much
            leverage is in the market — not how much is short. Funding tells you which side is
            crowded: negative means short sellers are paying holders of long positions, which
            they only do when short demand exceeds long demand. Rising price with falling open
            interest means those positions are being closed. Rising price with rising open
            interest means new ones are replacing them.
          </p>
        </div>
      </div>
    </section>
  )
}
