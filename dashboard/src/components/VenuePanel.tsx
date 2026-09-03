import { useState } from 'react'
import type { LiveMarket, PerpVenue } from '../hooks/useLiveMarket'
import { formatUsd } from '../lib/formatters'

/**
 * Where the leverage actually sits, as a proportional band you can explore.
 *
 * This replaces a row of 32 identical dots. The dots answered exactly one
 * question — how many venues charge short sellers — and threw away the fact that
 * matters more: the leverage is not spread evenly. One venue holds a quarter of
 * it. Sizing each segment by open interest makes that visible before you read a
 * single number, and hovering names the venue and prices its funding.
 */

/** Funding is charged per position notional every eight hours, so ~3x a day. */
function costPerDay(v: PerpVenue): number | null {
  if (v.funding == null) return null
  return Math.abs(v.openInterest * (v.funding / 100) * 3)
}

function segmentTone(v: PerpVenue): { fill: string; label: string } {
  if (v.funding == null) return { fill: 'var(--color-border-strong)', label: 'no funding data' }
  return v.funding < 0
    ? { fill: 'var(--color-accent-cyan)', label: 'charges short sellers' }
    : { fill: 'var(--color-severity-medium)', label: 'charges buyers' }
}

export function VenuePanel({ data }: { data: LiveMarket }) {
  const [active, setActive] = useState<number | null>(null)
  const [pinned, setPinned] = useState<number | null>(null)

  const venues = data.venues
  const total = venues.reduce((s, v) => s + v.openInterest, 0)
  if (!venues.length || !total) {
    return <div className="text-[12.5px] text-text-muted">No venue data right now.</div>
  }

  // Two different things, which the first version conflated. `idx` is what the
  // readout describes and falls back to the largest venue so it is never empty.
  // `exploring` is whether the reader is actually pointing at something — only
  // then should the rest of the band dim. Without the distinction the band sat
  // permanently dimmed around a segment nobody had touched.
  const idx = active ?? pinned ?? 0
  const exploring = active != null || pinned != null
  const v = venues[idx]
  const share = (v.openInterest / total) * 100
  const cost = costPerDay(v)
  const tone = segmentTone(v)
  const noFunding = venues.filter((x) => x.funding == null).length

  return (
    <div
      onMouseLeave={() => setActive(null)}
      onKeyDown={(e) => e.key === 'Escape' && setPinned(null)}
    >
      <div className="flex items-baseline justify-between gap-3 flex-wrap">
        <span className="eyebrow">Where the leverage sits</span>
        <span className="font-mono text-[10px] text-text-muted">
          {venues.length} venues · {formatUsd(total)} outstanding
        </span>
      </div>

      {/* Widths are open interest. The band is one bar, not a chart, so the
          concentration reads instantly: the first segment is a quarter of it. */}
      <div className="mt-2.5 flex h-9 w-full gap-px rounded-sm overflow-hidden bg-bg-elevated">
        {venues.map((x, i) => {
          const w = (x.openInterest / total) * 100
          const on = i === idx
          return (
            <button
              key={x.market}
              type="button"
              aria-label={`${x.market}, ${formatUsd(x.openInterest)} open interest, ${segmentTone(x).label}`}
              aria-pressed={pinned === i}
              onMouseEnter={() => setActive(i)}
              onFocus={() => setActive(i)}
              onBlur={() => setActive(null)}
              onClick={() => setPinned(pinned === i ? null : i)}
              // A hair of minimum width so the long tail stays clickable rather
              // than collapsing into an unhittable sliver.
              style={{ width: `${w}%`, minWidth: 3, background: segmentTone(x).fill }}
              className={`h-full transition-[opacity,transform] duration-150 origin-bottom focus:outline-none ${
                !exploring
                  ? 'opacity-100'
                  : on
                    ? 'opacity-100 scale-y-100'
                    : 'opacity-30 scale-y-[0.78]'
              }`}
            />
          )
        })}
      </div>

      {/* The readout. Fixed height, so hovering across the band does not make
          the rest of the page jump. */}
      <div className="mt-3 min-h-[74px]">
        <div className="flex items-baseline justify-between gap-3 flex-wrap">
          <span className="text-[13px] font-semibold text-text-primary">{v.market}</span>
          <span className="font-mono text-[10px] text-text-muted">
            {/* The prompt is only useful before the reader works it out. */}
            {pinned === idx
              ? 'pinned — click again to release'
              : exploring
                ? 'click to pin'
                : 'hover the band to explore'}
          </span>
        </div>

        <div className="mt-1.5 grid grid-cols-2 sm:grid-cols-4 gap-x-4 gap-y-2">
          <Stat label="Leverage here" value={formatUsd(v.openInterest)} sub={`${share.toFixed(1)}% of all`} />
          <Stat label="Traded today" value={formatUsd(v.volume24h)} />
          <Stat
            label="Funding"
            value={v.funding == null ? '—' : `${v.funding.toFixed(4)}%`}
            sub={tone.label}
            tone={
              v.funding == null
                ? 'text-text-faint'
                : v.funding < 0
                  ? 'text-accent-cyan'
                  : 'text-severity-medium'
            }
          />
          <Stat
            label="Changing hands"
            value={cost == null ? '—' : `${formatUsd(cost)}/day`}
            sub={cost == null ? undefined : v.funding! < 0 ? 'shorts to buyers' : 'buyers to shorts'}
          />
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-border-subtle font-mono text-[10.5px] text-text-muted flex flex-wrap gap-x-4 gap-y-1">
        <Key color="var(--color-accent-cyan)" text={`${data.fundingNegative} charge short sellers`} />
        <Key
          color="var(--color-severity-medium)"
          text={`${data.fundingVenues - data.fundingNegative} charge buyers`}
        />
        {noFunding > 0 && <Key color="var(--color-border-strong)" text={`${noFunding} not reporting`} />}
      </div>
    </div>
  )
}

function Stat({
  label,
  value,
  sub,
  tone = 'text-text-primary',
}: {
  label: string
  value: string
  sub?: string
  tone?: string
}) {
  return (
    <div>
      <div className="font-mono text-[9px] uppercase tracking-widest text-text-faint">{label}</div>
      <div className={`font-mono tabular text-[14px] mt-0.5 ${tone}`}>{value}</div>
      {sub && <div className="font-mono text-[9.5px] text-text-muted mt-0.5">{sub}</div>}
    </div>
  )
}

function Key({ color, text }: { color: string; text: string }) {
  return (
    <span className="flex items-center gap-1.5">
      <span className="w-2 h-2 rounded-[1px]" style={{ background: color }} />
      {text}
    </span>
  )
}
