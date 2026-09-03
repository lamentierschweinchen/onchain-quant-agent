import { useEffect, useRef, useState } from 'react'
import type { LiveMarket } from '../hooks/useLiveMarket'
import { formatEgldBare, formatUsd } from '../lib/formatters'

/**
 * A running log of what actually moved while you were watching.
 *
 * The tiles show the current value and the history chart shows the shape, but
 * neither tells you that 42,127 EGLD left the trading desks in the ten minutes
 * you had the tab open — which is the sort of thing this page exists to catch.
 * Diffing consecutive refreshes turns the poll loop into a feed.
 *
 * Thresholds are deliberately well above the noise floor. A tape that logs every
 * cent of price drift is a tape nobody reads, and worse, it manufactures the
 * feeling that something is happening when nothing is.
 */

export interface TapeEvent {
  at: number
  text: string
  figure: string
  tone: 'up' | 'down' | 'notable'
}

const THRESHOLDS = {
  desks: 250, // EGLD
  pricePct: 0.4,
  oiPct: 1.5,
}

function diff(prev: LiveMarket, next: LiveMarket): TapeEvent[] {
  const out: TapeEvent[] = []
  const at = next.fetchedAt

  const dDesk = next.deskTotal - prev.deskTotal
  if (Math.abs(dDesk) >= THRESHOLDS.desks) {
    out.push({
      at,
      text: dDesk < 0 ? 'left the trading desks' : 'was staged on the desks',
      figure: `${formatEgldBare(Math.abs(dDesk))} EGLD`,
      // Down is not "bad" here — it is supply leaving. Colour tracks direction
      // only, per the rule that colour never carries sentiment on this page.
      tone: dDesk < 0 ? 'down' : 'up',
    })
  }

  const dPricePct = prev.price ? ((next.price - prev.price) / prev.price) * 100 : 0
  if (Math.abs(dPricePct) >= THRESHOLDS.pricePct) {
    out.push({
      at,
      text: dPricePct > 0 ? 'price moved up' : 'price moved down',
      figure: `${dPricePct > 0 ? '+' : ''}${dPricePct.toFixed(2)}% to $${next.price.toFixed(2)}`,
      tone: dPricePct > 0 ? 'up' : 'down',
    })
  }

  const dOi = next.openInterest - prev.openInterest
  const dOiPct = prev.openInterest ? (dOi / prev.openInterest) * 100 : 0
  if (Math.abs(dOiPct) >= THRESHOLDS.oiPct) {
    out.push({
      at,
      text: dOi > 0 ? 'new leveraged positions opened' : 'leveraged positions closed',
      figure: `${dOi > 0 ? '+' : '−'}${formatUsd(Math.abs(dOi))}`,
      tone: 'notable',
    })
  }

  // A funding flip changes who is paying whom — always worth a line.
  const was = prev.fundingMean
  const now = next.fundingMean
  if (was != null && now != null && Math.sign(was) !== Math.sign(now)) {
    out.push({
      at,
      text: now < 0 ? 'funding flipped — short sellers now pay' : 'funding flipped — buyers now pay',
      figure: `${now.toFixed(4)}%`,
      tone: 'notable',
    })
  }

  return out
}

const TONE: Record<TapeEvent['tone'], string> = {
  up: 'text-up',
  down: 'text-down',
  notable: 'text-accent-cyan',
}

export function EventTape({ data }: { data: LiveMarket | null }) {
  const [events, setEvents] = useState<TapeEvent[]>([])
  const prev = useRef<LiveMarket | null>(null)
  const openedAt = useRef(Date.now())

  useEffect(() => {
    if (!data) return
    if (prev.current) {
      const found = diff(prev.current, data)
      if (found.length) setEvents((e) => [...found, ...e].slice(0, 12))
    }
    prev.current = data
  }, [data])

  const waited = Math.round((Date.now() - openedAt.current) / 60_000)

  return (
    <div>
      <div className="flex items-baseline justify-between gap-3 flex-wrap">
        <span className="eyebrow">What moved while you watched</span>
        <span className="font-mono text-[10px] text-text-muted flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-accent-cyan pulse-dot" />
          recording
        </span>
      </div>

      {events.length === 0 ? (
        <p className="mt-2.5 font-mono text-[11px] text-text-faint">
          Nothing above the noise floor yet
          {waited >= 1 ? ` in ${waited} minute${waited === 1 ? '' : 's'}` : ''}. This logs desk
          movements over {THRESHOLDS.desks} EGLD, price moves over {THRESHOLDS.pricePct}%, leverage
          shifts over {THRESHOLDS.oiPct}%, and any flip in who pays funding.
        </p>
      ) : (
        <ul className="mt-2.5 divide-y divide-border-subtle">
          {events.map((e, i) => (
            <li
              key={`${e.at}-${e.text}-${i}`}
              className="py-1.5 flex items-baseline gap-3 font-mono text-[11.5px] tape-in"
            >
              <span className="text-text-faint tabular shrink-0">
                {new Date(e.at).toISOString().slice(11, 19)}
              </span>
              <span className={`${TONE[e.tone]} tabular font-semibold shrink-0`}>{e.figure}</span>
              <span className="text-text-secondary">{e.text}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
