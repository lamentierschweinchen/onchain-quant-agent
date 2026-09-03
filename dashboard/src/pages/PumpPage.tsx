import { useEffect, useMemo, useRef, useState } from 'react'
import { useLiveMarket } from '../hooks/useLiveMarket'
import type { LiveMarket } from '../hooks/useLiveMarket'
import { PageTabs } from '../components/PageTabs'
import { MarketHistory, useHistory } from '../components/MarketHistory'
import { BigPicture } from '../components/BigPicture'
import { PeerBars } from '../components/PeerBars'
import { VenuePanel } from '../components/VenuePanel'
import { EventTape } from '../components/EventTape'
import { formatEgldBare, formatUsd, formatNumber } from '../lib/formatters'
import {
  decoupling,
  leverage,
  overhang,
  shortCostPerDay,
  TONE_TEXT,
  TONE_BG,
} from '../lib/pumpSignals'
import type { Signal } from '../lib/pumpSignals'

const REFRESH_MS = 60_000

/* ---------------------------------------------------------------- helpers */

function pct(n: number): string {
  return `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`
}

function utc(ts: number): string {
  return new Date(ts).toISOString().slice(11, 19) + ' UTC'
}

/** A figure that tints once, briefly, when its value actually changes. */
function Live({
  value,
  children,
  className = '',
}: {
  value: number | string
  children: React.ReactNode
  className?: string
}) {
  const prev = useRef(value)
  const [flash, setFlash] = useState<'up' | 'down' | null>(null)

  useEffect(() => {
    if (prev.current === value) return
    const rose =
      typeof value === 'number' && typeof prev.current === 'number'
        ? value > prev.current
        : true
    prev.current = value
    setFlash(rose ? 'up' : 'down')
    const id = setTimeout(() => setFlash(null), 700)
    return () => clearTimeout(id)
  }, [value])

  return (
    <span
      className={`${className} rounded px-1 -mx-1 transition-colors duration-700 motion-reduce:transition-none ${
        flash === 'up' ? 'bg-up/20' : flash === 'down' ? 'bg-down/20' : 'bg-transparent'
      }`}
    >
      {children}
    </span>
  )
}

/** Fills over the refresh interval, so "live" is something you can see. */
function RefreshBar({ fetchedAt, now }: { fetchedAt: number; now: number }) {
  const frac = Math.min(1, Math.max(0, (now - fetchedAt) / REFRESH_MS))
  return (
    <div className="h-px w-full bg-border-subtle" aria-hidden="true">
      <div
        className="h-px bg-accent-cyan/70 transition-[width] duration-1000 ease-linear motion-reduce:transition-none"
        style={{ width: `${frac * 100}%` }}
      />
    </div>
  )
}

/* ------------------------------------------------------------ desk gauge */

function DeskGauge({ data, peak }: { data: LiveMarket; peak: number }) {
  const [hovered, setHovered] = useState<number | null>(null)
  const total = data.deskTotal
  const scale = Math.max(peak, total)
  const drained = Math.max(0, peak - total)
  const shown = hovered != null ? data.deskBreakdown[hovered] : null
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <span className="eyebrow">Staged on the trading desks</span>
        <span className="font-mono text-[10px] text-text-muted">
          peak {formatEgldBare(peak)}
        </span>
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <Live value={Math.round(total)} className="font-mono tabular text-[34px] font-semibold leading-none text-text-primary">
          {formatEgldBare(total)}
        </Live>
        <span className="font-mono text-[12px] text-text-muted">EGLD</span>
      </div>
      <div className="mt-3 h-3.5 w-full bg-bg-elevated flex gap-px"
           onMouseLeave={() => setHovered(null)} role="img"
           aria-label={`${Math.round(total)} EGLD on the desks, from a peak of ${Math.round(peak)}`}>
        {data.deskBreakdown.map((d, i) => (
          <button
            key={d.label}
            type="button"
            aria-label={`${d.label}: ${formatEgldBare(d.egld)} EGLD`}
            onMouseEnter={() => setHovered(i)}
            onFocus={() => setHovered(i)}
            onBlur={() => setHovered(null)}
            style={{ width: `${(d.egld / scale) * 100}%` }}
            className={`h-full transition-opacity duration-150 focus:outline-none focus-visible:ring-1 focus-visible:ring-accent-cyan ${
              i === 0 ? 'bg-accent-cyan' : 'bg-accent-cyan/55'
            } ${hovered != null && hovered !== i ? 'opacity-35' : 'opacity-100'}`}
          />
        ))}
      </div>
      <div className="mt-2 font-mono text-[11px] min-h-[16px]">
        {shown ? (
          <span className="text-text-secondary">
            {shown.label} <span className="text-text-primary">{formatEgldBare(shown.egld)} EGLD</span>
            <span className="text-text-faint"> · {((shown.egld / total) * 100).toFixed(0)}% of the total</span>
          </span>
        ) : (
          <span className="text-down">−{formatEgldBare(drained)} left the desks since the peak</span>
        )}
      </div>
    </div>
  )
}

/* ------------------------------------------------- since you opened strip */

interface Snapshot {
  price: number
  deskTotal: number
  openInterest: number
  at: number
}

function useSessionAnchor(data: LiveMarket | null): Snapshot | null {
  const [anchor, setAnchor] = useState<Snapshot | null>(() => {
    try {
      const raw = sessionStorage.getItem('pump-anchor')
      return raw ? (JSON.parse(raw) as Snapshot) : null
    } catch {
      return null
    }
  })
  useEffect(() => {
    if (!data || anchor) return
    const snap: Snapshot = {
      price: data.price,
      deskTotal: data.deskTotal,
      openInterest: data.openInterest,
      at: Date.now(),
    }
    setAnchor(snap)
    try {
      sessionStorage.setItem('pump-anchor', JSON.stringify(snap))
    } catch {
      /* private mode — the strip just won't persist across reloads */
    }
  }, [data, anchor])
  return anchor
}

function SinceStrip({ data, anchor, now }: { data: LiveMarket; anchor: Snapshot; now: number }) {
  const mins = Math.max(0, Math.round((now - anchor.at) / 60000))
  if (mins < 1) return null
  const dp = data.price - anchor.price
  const dd = data.deskTotal - anchor.deskTotal
  const doi = data.openInterest - anchor.openInterest
  const item = (label: string, text: string, tone: string) => (
    <span className="whitespace-nowrap">
      <span className="text-text-faint">{label} </span>
      <span className={`${tone} font-medium`}>{text}</span>
    </span>
  )
  return (
    <div className="flex flex-wrap items-center gap-x-5 gap-y-1 font-mono text-[11px] text-text-muted">
      <span className="text-text-faint uppercase tracking-widest text-[9.5px]">
        Since you opened this page · {mins}m
      </span>
      {item('price', `${dp >= 0 ? '+' : '−'}$${Math.abs(dp).toFixed(3)}`, dp >= 0 ? 'text-up' : 'text-down')}
      {item(
        'desks',
        `${dd <= 0 ? '−' : '+'}${formatEgldBare(Math.abs(dd))} EGLD`,
        dd <= 0 ? 'text-down' : 'text-up',
      )}
      {item('leverage', `${doi >= 0 ? '+' : '−'}${formatUsd(Math.abs(doi))}`, 'text-text-secondary')}
    </div>
  )
}

/* -------------------------------------------------------------- fragments */

function Disclosure({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <details className="card group">
      <summary className="px-4 py-3 cursor-pointer list-none flex items-center justify-between gap-3 text-[12px] font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan/60 focus-visible:ring-inset">
        <span>{title}</span>
        <span className="font-mono text-[10px] text-text-muted">
          <span className="group-open:hidden">show +</span>
          <span className="hidden group-open:inline">hide −</span>
        </span>
      </summary>
      <div className="px-4 pb-4">{children}</div>
    </details>
  )
}

/* ------------------------------------------------------------------ page */

export function PumpPage() {
  const { data, error, loading, refresh } = useLiveMarket(REFRESH_MS)
  const { hist } = useHistory()
  const [now, setNow] = useState(() => Date.now())
  const anchor = useSessionAnchor(data)

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])

  // Remember the previous state name per signal so thresholds get hysteresis
  // instead of flipping every refresh when a value sits on a boundary.
  const prevStates = useRef<{ dec?: string; lev?: string; ovh?: string }>({})
  const peak = useMemo(
    () => Math.max(266213, ...(hist?.points.map((p) => p.desks) ?? [0])),
    [hist],
  )

  const signals = useMemo(() => {
    if (!data) return null
    const dec = decoupling(data, prevStates.current.dec)
    const lev = leverage(data, prevStates.current.lev)
    const ovh = overhang(data, peak, prevStates.current.ovh)
    prevStates.current = {
      dec: dec.state.startsWith('Moving alone') ? 'alone' : dec.state.startsWith('Lagging') ? 'lagging' : 'with',
      lev: lev.state.startsWith('Shorts') ? 'shorts' : lev.state.startsWith('Longs') ? 'longs' : 'balanced',
      ovh: ovh.state.startsWith('Supply') ? 'staged' : ovh.state.startsWith('Desks nearly') ? 'cleared' : 'falling',
    }
    return { dec, lev, ovh }
  }, [data, peak])

  const cost = data ? shortCostPerDay(data) : null

  return (
    <div className="min-h-screen bg-bg text-text-primary">
      <header className="sticky top-0 z-50 border-b border-border bg-bg/95 backdrop-blur-sm">
        <div className="flex items-center gap-4 px-6 py-3 flex-wrap">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-6 bg-accent-cyan rounded-sm" />
            <div className="flex flex-col leading-tight">
              <span className="text-[14px] font-semibold tracking-tight">EGLD Pump Tracker</span>
              <span className="text-[9.5px] font-mono uppercase tracking-[0.14em] text-text-muted">
                Live · every 60s
              </span>
            </div>
          </div>
          <div className="flex-1" />
          <PageTabs active="pump" />
        </div>
        {data && <RefreshBar fetchedAt={data.fetchedAt} now={now} />}
      </header>

      <main className="max-w-[1080px] mx-auto px-6 py-6">
        {loading && !data && (
          <div className="grid gap-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="card p-6 animate-pulse">
                <div className="h-3 w-32 bg-bg-elevated rounded" />
                <div className="h-8 w-52 bg-bg-elevated rounded mt-3" />
              </div>
            ))}
          </div>
        )}

        {error && !data && (
          <div className="card p-6">
            <p className="text-down font-medium">Could not load live data</p>
            <p className="text-text-muted text-[13px] font-mono mt-1">{error}</p>
            <button type="button" onClick={refresh}
              className="mt-4 px-3 py-1.5 rounded border border-accent-cyan/30 bg-accent-cyan/10 text-accent-cyan text-[11px] font-mono uppercase tracking-wider hover:bg-accent-cyan/20 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan/60">
              Try again
            </button>
          </div>
        )}

        {data && signals && (
          <div className="space-y-4">
            {(error || data.degraded || data.venuesAsOf) && (
              <div className="text-[11px] font-mono text-severity-medium space-y-1">
                {error && (
                  <p>
                    Refresh failed ({error}). Showing the last good reading, from{' '}
                    {utc(data.fetchedAt)}.
                  </p>
                )}
                {!error && data.degraded && (
                  <p>
                    The price source is rate-limiting, so 24h high/low and the 7d/30d changes
                    are unavailable. Price, peers and chain data are live.
                  </p>
                )}
                {data.venuesAsOf && (
                  <p>
                    Funding and leverage are from the hourly snapshot taken{' '}
                    {data.venuesAsOf.slice(11, 16)} UTC — the live derivatives feed is
                    rate-limiting. Price, peers and desk balances are live.
                  </p>
                )}
              </div>
            )}

            {/* ---- TIER 0: the sentence, then the two numbers that matter ---- */}
            <section className="card p-5">
              <p className="text-[19px] leading-snug font-medium text-text-primary max-w-[62ch]">
                EGLD is{' '}
                <span className={signals.dec.tone === 'notable' ? 'text-accent-cyan' : ''}>
                  {signals.dec.clause}
                </span>
                ,{' '}
                <span className={TONE_TEXT[signals.lev.tone]}>{signals.lev.clause}</span>, and{' '}
                <span className={TONE_TEXT[signals.ovh.tone]}>{signals.ovh.clause}</span>.
              </p>

              <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div>
                  <div className="eyebrow">Price</div>
                  <div className="mt-2 flex items-baseline gap-3 flex-wrap">
                    <Live value={data.price} className="font-mono tabular text-[38px] font-semibold leading-none">
                      ${data.price.toFixed(2)}
                    </Live>
                    <Live
                      value={data.change24h}
                      className={`font-mono tabular text-[18px] font-semibold ${data.change24h >= 0 ? 'text-up' : 'text-down'}`}
                    >
                      {pct(data.change24h)}
                    </Live>
                  </div>
                  <div className="mt-2 font-mono text-[11px] text-text-muted">
                    {data.low24h != null && data.high24h != null && (
                      <>${data.low24h.toFixed(2)}–${data.high24h.toFixed(2)} today · </>
                    )}
                    data as of {utc(data.fetchedAt)}
                  </div>
                </div>
                <DeskGauge data={data} peak={peak} />
              </div>

              {anchor && (
                <div className="mt-5 pt-4 border-t border-border-subtle">
                  <SinceStrip data={data} anchor={anchor} now={now} />
                </div>
              )}
            </section>

            {/* ---- what the leverage costs, in money ---- */}
            <section className="card p-5 space-y-5">
              <div>
                <div className="eyebrow">What betting against it costs, per day</div>
                {cost != null ? (
                  <>
                    <Live value={Math.round(cost)} className="block mt-2 font-mono tabular text-[32px] font-semibold text-accent-cyan leading-none">
                      {formatUsd(cost)}
                    </Live>
                    <p className="mt-2 text-[12px] text-text-muted leading-relaxed max-w-[46ch]">
                      {formatUsd(data.openInterest)} of leverage outstanding ×{' '}
                      {data.fundingMean?.toFixed(4)}% × 3 charges a day. Paid by the side betting
                      on a fall, to the side betting on a rise. An estimate: venues differ on
                      interval.
                    </p>
                  </>
                ) : (
                  <p className="mt-2 text-[13px] text-text-muted">No funding data right now.</p>
                )}
              </div>
              <div className="pt-1 border-t border-border-subtle">
                <div className="pt-4">
                  <VenuePanel data={data} />
                </div>
              </div>
            </section>

            {/* ---- TIER 1: context, then the live series ---- */}
            <BigPicture livePrice={data.price} />

            <MarketHistory />

            <section className="card p-5">
              <PeerBars data={data} />
            </section>

            <section className="card p-5">
              <EventTape data={data} />
            </section>

            {/* ---- TIER 2: evidence, folded away ---- */}
            <Disclosure title="Why each reading says what it says">
              <div className="grid gap-3 sm:grid-cols-3 pt-1">
                {([signals.dec, signals.lev, signals.ovh] as Signal[]).map((s) => (
                  <div key={s.state}>
                    <div className="flex items-center gap-1.5">
                      <span className={`w-1.5 h-1.5 rounded-full ${TONE_BG[s.tone]}`} />
                      <span className={`text-[12.5px] font-semibold ${TONE_TEXT[s.tone]}`}>
                        {s.state}
                      </span>
                    </div>
                    <p className="mt-1 text-[12px] text-text-muted leading-relaxed">{s.detail}</p>
                  </div>
                ))}
              </div>
            </Disclosure>

            <Disclosure title={`Leverage by venue — all ${data.venues.length}`}>
              <div className="overflow-x-auto">
                <table className="w-full text-[12px] tabular">
                  <thead>
                    <tr className="text-left">
                      {['Venue', 'Open interest', 'Funding'].map((h, i) => (
                        <th key={h} className={`py-2 font-mono text-[9.5px] uppercase tracking-wider text-text-muted ${i ? 'text-right' : ''}`}>
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.venues.map((v) => (
                      <tr key={v.market} className="border-t border-border-subtle">
                        <td className="py-1.5 text-text-secondary">{v.market}</td>
                        <td className="py-1.5 text-right text-text-primary">{formatUsd(v.openInterest)}</td>
                        <td className={`py-1.5 text-right ${v.funding == null ? 'text-text-faint' : v.funding < 0 ? 'text-accent-cyan' : 'text-severity-medium'}`}>
                          {v.funding == null ? '—' : `${v.funding.toFixed(4)}%`}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Disclosure>

            <Disclosure title="The two desk wallets">
              <div className="grid gap-3 sm:grid-cols-2 pt-1">
                {data.deskBreakdown.map((d) => (
                  <div key={d.label}>
                    <div className="eyebrow">{d.label}</div>
                    <div className="font-mono tabular text-[18px] mt-1">{formatEgldBare(d.egld)} EGLD</div>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-[11.5px] text-text-muted leading-relaxed max-w-[74ch]">
                Both are <em>labelled</em> rather than confirmed: they were identified by tracing
                repeated large transfers between exchange wallets and these addresses over
                twenty-three weeks. A falling balance means EGLD left the wallet — it may have
                been sold, moved to an exchange, or moved to another wallet of the same operator.
                This page does not trace the destination.
              </p>
            </Disclosure>

            <div className="font-mono text-[10.5px] text-text-faint leading-relaxed border-t border-border pt-4">
              Mcap {formatUsd(data.marketCap)} · spot vol {formatUsd(data.volume24h)} · leveraged vol{' '}
              {formatUsd(data.perpVolume)} · 7d {data.change7d != null ? pct(data.change7d) : '—'} · 30d{' '}
              {data.change30d != null ? pct(data.change30d) : '—'} · staked{' '}
              {formatNumber(data.stakedEgld)} EGLD ({(100 * data.stakedRatio).toFixed(1)}%)
              <br />
              Price and leverage from CoinGecko, chain data from the MultiversX API.
              Observational, not investment advice.
              <button type="button" onClick={refresh}
                className="ml-3 rounded px-2 py-0.5 uppercase tracking-wider text-accent-cyan/80 hover:text-accent-cyan hover:bg-accent-cyan/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan/60">
                refresh now
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
