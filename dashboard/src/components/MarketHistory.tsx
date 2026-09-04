import { useEffect, useState } from 'react'
import { formatUsd } from '../lib/formatters'
import { TimeChart } from './TimeChart'
import type { Series } from './TimeChart'

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

export function useHistory() {
  const [hist, setHist] = useState<History | null>(null)
  const [missing, setMissing] = useState(false)

  useEffect(() => {
    let cancelled = false

    // A scheduled GitHub Action commits new readings to the repo. It asks for
    // hourly and GitHub delivers roughly every 4-5 hours in practice. Reading them
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
  const last = pts[pts.length - 1]

  // The verdict reads a TRAILING window, not the whole series. Comparing the
  // first reading to the last means the window grows forever and the state gets
  // less responsive every day: on 4 Sep it still said "positions building" while
  // open interest had fallen 45% from its peak two days earlier, because the
  // comparison reached all the way back to the first reading. A day is long
  // enough to be a trend and short enough to still be news.
  const WINDOW_H = 24
  const cutoff = new Date(last.t).getTime() - WINDOW_H * 3_600_000
  const recent = pts.filter((p) => new Date(p.t).getTime() >= cutoff)
  const window = recent.length >= 2 ? recent : pts.slice(-2)
  const first = window[0]

  const withOi = window.filter((p): p is HistoryPoint & { oi: number } => p.oi != null)
  const oiFirst = withOi[0]
  const oiLast = withOi[withOi.length - 1]
  const priceUp = last.price >= first.price
  const oiUp = oiLast && oiFirst ? oiLast.oi >= oiFirst.oi : false
  const verdict = VERDICTS[`${priceUp ? 'up' : 'down'}-${oiUp ? 'up' : 'down'}`]
  const windowH = (new Date(last.t).getTime() - new Date(first.t).getTime()) / 3_600_000

  const fundings = pts.map((p) => p.funding).filter((f): f is number => f != null)
  // Full span of the chart. Must read pts[0], not `first` — `first` is now the
  // start of the 24h verdict window, and reusing it made the header claim the
  // whole series covered 23.8h when it covered 4.8 days.
  const hours = (new Date(last.t).getTime() - new Date(pts[0].t).getTime()) / 3_600_000
  const times = pts.map((p) => new Date(p.t).getTime())

  return (
    <section className="card overflow-hidden">
      <header className="px-4 py-2.5 border-b border-border bg-bg-elevated flex flex-wrap items-baseline justify-between gap-2">
        <div>
          <h2 className="text-[12px] font-semibold">
            {/* the answer is the headline; the question lives in the detail */}
            What the leverage is doing
          </h2>
          <p className="text-[10px] text-text-muted mt-0.5">
            Chart shows all {pts.length} readings over{' '}
            {hours < 24 ? `${hours.toFixed(1)}h` : `${(hours / 24).toFixed(1)} days`}; the reading
            on the right covers the last {windowH.toFixed(0)}h
          </p>
        </div>
        <span className={`text-[13px] font-semibold ${verdict.tone}`}>{verdict.title}</span>
      </header>

      <div className="p-4 space-y-4">
        <p className="text-[12.5px] text-text-secondary leading-relaxed max-w-[74ch]">
          <span className="text-text-muted">Over the last {windowH.toFixed(0)} hours: </span>
          {verdict.detail}
        </p>

        <div className="space-y-5">
          <TimeChart
            times={times}
            height={150}
            series={[
              {
                key: 'price',
                label: 'price',
                color: '#23f7dd',
                area: true,
                values: pts.map((p) => p.price),
                format: (v) => `$${v.toFixed(2)}`,
              },
              {
                key: 'oi',
                label: 'leverage outstanding',
                color: '#f0a020',
                axis: 'right',
                values: pts.map((p) => p.oi),
                format: (v) => formatUsd(v),
              },
            ] satisfies Series[]}
          />

          {fundings.length > 1 && (
            <div className="border-t border-border-subtle pt-4">
              <div className="flex items-baseline justify-between gap-3">
                <span className="eyebrow">Funding rate — which side pays</span>
                <span className="font-mono text-[10px] text-text-muted">
                  below the line, short sellers pay
                </span>
              </div>
              <div className="mt-1">
                <TimeChart
                  times={times}
                  height={92}
                  zeroLine
                  series={[
                    {
                      key: 'funding',
                      label: 'funding',
                      color: '#f4525a',
                      values: pts.map((p) => p.funding),
                      format: (v) => `${v.toFixed(4)}%`,
                    },
                  ] satisfies Series[]}
                />
              </div>
            </div>
          )}
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
