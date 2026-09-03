import { useState } from 'react'
import type { LiveMarket } from '../hooks/useLiveMarket'
import { formatUsd } from '../lib/formatters'

/**
 * EGLD against every layer-1 peer, as diverging bars from a zero line.
 *
 * This replaces a tick-mark strip that plotted each peer as an unlabelled line
 * on an axis. The strip was prettier and told you less: you could see EGLD was
 * far right of a cluster but not which coin was where, nor by how much. Names
 * and numbers are the point of the panel, so they are back.
 */

function pct(n: number): string {
  return `${n >= 0 ? '+' : ''}${n.toFixed(1)}%`
}

export function PeerBars({ data }: { data: LiveMarket }) {
  const [active, setActive] = useState<string | null>(null)

  const rows = [
    { symbol: 'EGLD', name: 'MultiversX', change: data.change24h, price: data.price, me: true },
    ...data.peers.map((p) => ({
      symbol: p.symbol,
      name: p.name,
      change: p.change24h,
      price: p.price,
      me: false,
    })),
  ].sort((a, b) => b.change - a.change)

  // Symmetric scale, so a +30% and a −30% bar are the same length either side.
  const reach = Math.max(4, ...rows.map((r) => Math.abs(r.change)))
  const half = (v: number) => (Math.abs(v) / reach) * 50

  const rank = rows.findIndex((r) => r.me) + 1
  const shown = rows.find((r) => r.symbol === active) ?? null

  return (
    <div>
      <div className="flex items-baseline justify-between gap-3 flex-wrap">
        <span className="eyebrow">Today against every layer-1 peer</span>
        <span className="font-mono text-[10px] text-text-muted">
          {rank === 1 ? 'EGLD leads the group' : `EGLD ranks ${rank} of ${rows.length}`} ·{' '}
          {data.decouplingPp >= 0 ? '+' : ''}
          {data.decouplingPp.toFixed(1)}pp vs the median
        </span>
      </div>

      <div className="mt-3 space-y-[3px]" onMouseLeave={() => setActive(null)}>
        {rows.map((r) => {
          const up = r.change >= 0
          const dim = active != null && active !== r.symbol
          return (
            <div
              key={r.symbol}
              onMouseEnter={() => setActive(r.symbol)}
              onFocus={() => setActive(r.symbol)}
              onBlur={() => setActive(null)}
              tabIndex={0}
              aria-label={`${r.name}, ${pct(r.change)} in 24 hours, ${formatUsd(r.price)}`}
              className={`grid items-center gap-2.5 rounded-sm -mx-1 px-1 py-px cursor-default transition-opacity duration-150 focus:outline-none focus-visible:ring-1 focus-visible:ring-accent-cyan/60 ${
                dim ? 'opacity-45' : 'opacity-100'
              }`}
              style={{ gridTemplateColumns: '58px 1fr 62px' }}
            >
              <span
                className={`font-mono text-[11px] truncate ${
                  r.me ? 'text-accent-cyan font-bold' : 'text-text-muted'
                }`}
                title={r.name}
              >
                {r.symbol}
              </span>

              <div className={`relative bg-bg-elevated/60 ${r.me ? 'h-5' : 'h-3.5'} transition-[height]`}>
                {/* zero line */}
                <div className="absolute left-1/2 top-[-1px] bottom-[-1px] w-px bg-border-strong" />
                <div
                  className={`absolute top-0 bottom-0 transition-[width,left] duration-700 ease-out motion-reduce:transition-none ${
                    r.me ? (up ? 'bg-accent-cyan' : 'bg-down') : up ? 'bg-up/35' : 'bg-down/35'
                  }`}
                  style={
                    up
                      ? { left: '50%', width: `${half(r.change)}%` }
                      : { left: `${50 - half(r.change)}%`, width: `${half(r.change)}%` }
                  }
                />
              </div>

              <span
                className={`font-mono tabular text-[11px] text-right ${
                  r.me
                    ? 'text-accent-cyan font-bold'
                    : up
                      ? 'text-up/80'
                      : 'text-down/80'
                }`}
              >
                {pct(r.change)}
              </span>
            </div>
          )
        })}
      </div>

      <div className="mt-2.5 font-mono text-[9.5px] text-text-faint flex justify-between">
        <span>−{reach.toFixed(0)}%</span>
        <span>24-hour change</span>
        <span>+{reach.toFixed(0)}%</span>
      </div>

      {/* Fixed height so the page does not shift as the pointer crosses rows. */}
      <div className="mt-3 pt-3 border-t border-border-subtle min-h-[34px] font-mono text-[11px]">
        {shown ? (
          <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
            <span className={shown.me ? 'text-accent-cyan font-bold' : 'text-text-primary'}>
              {shown.name}
            </span>
            <span className="text-text-muted">
              price <span className="text-text-primary tabular">{formatUsd(shown.price)}</span>
            </span>
            <span className="text-text-muted">
              today{' '}
              <span className={`tabular ${shown.change >= 0 ? 'text-up' : 'text-down'}`}>
                {pct(shown.change)}
              </span>
            </span>
            {!shown.me && (
              <span className="text-text-muted">
                EGLD is{' '}
                <span className="text-accent-cyan tabular">
                  {(data.change24h - shown.change).toFixed(1)}pp
                </span>{' '}
                ahead of it
              </span>
            )}
          </div>
        ) : (
          <span className="text-text-faint">hover a row for its price and the gap to EGLD</span>
        )}
      </div>
    </div>
  )
}
