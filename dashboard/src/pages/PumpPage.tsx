import { useEffect, useState } from 'react'
import { useLiveMarket } from '../hooks/useLiveMarket'
import type { LiveMarket } from '../hooks/useLiveMarket'
import { PageTabs } from '../components/PageTabs'
import { MarketHistory } from '../components/MarketHistory'
import { formatEgldBare, formatUsd, formatNumber } from '../lib/formatters'

/* -------------------------------------------------------------------------
   Three read-outs that are not price, because price is the one thing every
   other site already shows. Each is a named state with an explicit threshold,
   so a reader can see why it says what it says.
   ------------------------------------------------------------------------- */

type Tone = 'up' | 'down' | 'flat'

function decoupling(d: LiveMarket): { state: string; tone: Tone; detail: string } {
  const gap = d.decouplingPp
  if (gap > 8)
    return {
      state: 'Moving alone',
      tone: 'up',
      detail: `${gap >= 0 ? '+' : ''}${gap.toFixed(1)}pp vs the median layer-1 peer — this is specific to MultiversX, not a market move`,
    }
  if (gap < -8)
    return {
      state: 'Lagging badly',
      tone: 'down',
      detail: `${gap.toFixed(1)}pp vs the median peer`,
    }
  return {
    state: 'Moving with the market',
    tone: 'flat',
    detail: `${gap >= 0 ? '+' : ''}${gap.toFixed(1)}pp vs the median peer — inside the normal band`,
  }
}

function leverage(d: LiveMarket): { state: string; tone: Tone; detail: string } {
  const share = d.oiShareOfMcap
  const negShare = d.fundingVenues ? d.fundingNegative / d.fundingVenues : 0
  const heavy = share > 20
  if (negShare > 0.6)
    return {
      state: heavy ? 'Shorts crowded, heavily' : 'Shorts crowded',
      tone: 'up',
      detail: `${d.fundingNegative} of ${d.fundingVenues} venues have short sellers paying longs. Open interest is ${share.toFixed(1)}% of market cap${heavy ? ' — above 20% a squeeze moves price hard' : ''}`,
    }
  if (negShare < 0.4)
    return {
      state: heavy ? 'Longs crowded, heavily' : 'Longs crowded',
      tone: 'down',
      detail: `Only ${d.fundingNegative} of ${d.fundingVenues} venues show shorts paying. Longs are the crowded side, which cuts the other way. Open interest ${share.toFixed(1)}% of market cap`,
    }
  return {
    state: 'Balanced',
    tone: 'flat',
    detail: `${d.fundingNegative} of ${d.fundingVenues} venues negative. Open interest ${share.toFixed(1)}% of market cap`,
  }
}

function overhang(d: LiveMarket): { state: string; tone: Tone; detail: string } {
  const t = d.deskTotal
  if (t > 200_000)
    return {
      state: 'Supply staged',
      tone: 'down',
      detail: `${formatEgldBare(t)} EGLD sitting on the private trading desks, waiting to be sold`,
    }
  if (t < 60_000)
    return {
      state: 'Overhang cleared',
      tone: 'up',
      detail: `Only ${formatEgldBare(t)} EGLD left on the desks — the known selling pressure is largely spent`,
    }
  return {
    state: 'Working down',
    tone: 'flat',
    detail: `${formatEgldBare(t)} EGLD on the desks, between the 60K cleared mark and the 200K staged mark`,
  }
}

const TONE: Record<Tone, string> = {
  up: 'text-up',
  down: 'text-down',
  flat: 'text-text-secondary',
}
const DOT: Record<Tone, string> = {
  up: 'bg-up',
  down: 'bg-down',
  flat: 'bg-text-muted',
}

function Signal({
  label,
  state,
  tone,
  detail,
}: {
  label: string
  state: string
  tone: Tone
  detail: string
}) {
  return (
    <div className="card p-4">
      <div className="eyebrow">{label}</div>
      <div className="mt-2 flex items-center gap-2">
        <span className={`w-2 h-2 rounded-full shrink-0 ${DOT[tone]}`} aria-hidden="true" />
        <span className={`text-[17px] font-semibold ${TONE[tone]}`}>{state}</span>
      </div>
      <p className="mt-1.5 text-[12px] text-text-muted leading-relaxed">{detail}</p>
    </div>
  )
}

function Stat({
  label,
  value,
  sub,
  tone,
}: {
  label: string
  value: string
  sub?: string
  tone?: Tone
}) {
  return (
    <div className="card p-3.5">
      <div className="eyebrow">{label}</div>
      <div
        className={`font-mono tabular text-[22px] font-medium leading-none mt-1.5 ${tone ? TONE[tone] : 'text-text-primary'}`}
      >
        {value}
      </div>
      {sub && <div className="font-mono text-[10.5px] text-text-muted mt-1">{sub}</div>}
    </div>
  )
}

function pct(n: number): string {
  return `${n >= 0 ? '+' : ''}${n.toFixed(2)}%`
}

function ago(ts: number, now: number): string {
  const s = Math.max(0, Math.round((now - ts) / 1000))
  if (s < 60) return `${s}s ago`
  return `${Math.round(s / 60)}m ago`
}

export function PumpPage() {
  const { data, error, loading, refresh } = useLiveMarket(60_000)
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="min-h-screen bg-bg text-text-primary">
      <header className="sticky top-0 z-50 border-b border-border bg-bg/95 backdrop-blur-sm">
        <div className="flex items-center gap-4 px-6 py-3 flex-wrap">
          <div className="flex items-center gap-2">
            <div className="w-1.5 h-6 bg-accent-cyan rounded-sm" />
            <div className="flex flex-col leading-tight">
              <span className="text-[14px] font-semibold tracking-tight">
                EGLD Pump Tracker
              </span>
              <span className="text-[9.5px] font-mono uppercase tracking-[0.14em] text-text-muted">
                Live · refreshes every 60s
              </span>
            </div>
          </div>
          <div className="flex-1" />
          <PageTabs active="pump" />
        </div>
      </header>

      <main className="max-w-[1100px] mx-auto px-6 py-6">
        {loading && !data && (
          <div className="grid gap-3">
            {[0, 1, 2].map((i) => (
              <div key={i} className="card p-6 animate-pulse">
                <div className="h-3 w-28 bg-bg-elevated rounded" />
                <div className="h-7 w-44 bg-bg-elevated rounded mt-3" />
              </div>
            ))}
          </div>
        )}

        {error && !data && (
          <div className="card p-6">
            <p className="text-down font-medium">Could not load live data</p>
            <p className="text-text-muted text-[13px] font-mono mt-1">{error}</p>
            <button
              type="button"
              onClick={refresh}
              className="mt-4 px-3 py-1.5 rounded border border-accent-cyan/30 bg-accent-cyan/10 text-accent-cyan text-[11px] font-mono uppercase tracking-wider hover:bg-accent-cyan/20 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan/60"
            >
              Try again
            </button>
          </div>
        )}

        {data && (
          <div className="space-y-5">
            {error && (
              <p className="text-[11px] font-mono text-severity-medium">
                Live refresh failed ({error}). Showing the last good reading from{' '}
                {ago(data.fetchedAt, now)}.
              </p>
            )}

            {/* headline numbers */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              <Stat
                label="Price"
                value={`$${data.price.toFixed(2)}`}
                sub={`$${data.low24h.toFixed(2)}–$${data.high24h.toFixed(2)} 24h`}
              />
              <Stat
                label="24 hour"
                value={pct(data.change24h)}
                tone={data.change24h >= 0 ? 'up' : 'down'}
              />
              {data.change7d != null && (
                <Stat
                  label="7 day"
                  value={pct(data.change7d)}
                  tone={data.change7d >= 0 ? 'up' : 'down'}
                />
              )}
              {data.change30d != null && (
                <Stat
                  label="30 day"
                  value={pct(data.change30d)}
                  tone={data.change30d >= 0 ? 'up' : 'down'}
                />
              )}
              <Stat
                label="Market cap"
                value={formatUsd(data.marketCap)}
                sub={`vol ${formatUsd(data.volume24h)}`}
              />
              <Stat
                label="Volume / cap"
                value={`${((100 * data.volume24h) / data.marketCap).toFixed(1)}%`}
                sub="turnover"
              />
            </div>

            {/* the three signals */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Signal label="Is it moving alone?" {...decoupling(data)} />
              <Signal label="Which side is leveraged?" {...leverage(data)} />
              <Signal label="Supply waiting to sell" {...overhang(data)} />
            </div>

            <MarketHistory />

            {/* detail */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              <section className="card overflow-hidden">
                <header className="px-4 py-2.5 border-b border-border bg-bg-elevated">
                  <h2 className="text-[12px] font-semibold">24 hour change vs peers</h2>
                </header>
                <div className="p-4 space-y-1.5">
                  {[
                    { symbol: 'EGLD', change24h: data.change24h, me: true },
                    ...data.peers.map((p) => ({ ...p, me: false })),
                  ].map((p) => {
                    const span = Math.max(
                      12,
                      ...[data.change24h, ...data.peers.map((x) => x.change24h)].map(Math.abs),
                    )
                    const w = (Math.abs(p.change24h) / span) * 50
                    const positive = p.change24h >= 0
                    return (
                      <div key={p.symbol} className="grid grid-cols-[56px_1fr_62px] items-center gap-2">
                        <span
                          className={`font-mono text-[11.5px] ${p.me ? 'text-accent-cyan font-bold' : 'text-text-secondary'}`}
                        >
                          {p.symbol}
                        </span>
                        <span className="relative h-4 bg-bg-elevated">
                          <span className="absolute inset-y-0 w-px bg-border-strong" style={{ left: '50%' }} />
                          <span
                            className={`absolute inset-y-0 ${p.me ? 'bg-accent-cyan' : positive ? 'bg-up/40' : 'bg-down/40'}`}
                            style={
                              positive
                                ? { left: '50%', width: `${w}%` }
                                : { right: '50%', width: `${w}%` }
                            }
                          />
                        </span>
                        <span
                          className={`font-mono tabular text-[11.5px] text-right ${p.me ? 'text-accent-cyan font-bold' : 'text-text-secondary'}`}
                        >
                          {pct(p.change24h)}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </section>

              <section className="card overflow-hidden">
                <header className="px-4 py-2.5 border-b border-border bg-bg-elevated">
                  <h2 className="text-[12px] font-semibold">Leverage by venue</h2>
                  <p className="text-[10px] text-text-muted mt-0.5">
                    Negative funding means short sellers are paying to keep their bet open
                  </p>
                </header>
                <div className="overflow-x-auto">
                  <table className="w-full text-[12px] tabular">
                    <thead className="bg-bg-soft">
                      <tr className="text-left">
                        <th className="px-3 py-2 font-mono text-[9.5px] uppercase tracking-wider text-text-muted">Venue</th>
                        <th className="px-3 py-2 font-mono text-[9.5px] uppercase tracking-wider text-text-muted text-right">Open interest</th>
                        <th className="px-3 py-2 font-mono text-[9.5px] uppercase tracking-wider text-text-muted text-right">Funding</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.venues.slice(0, 8).map((v) => (
                        <tr key={v.market} className="border-t border-border-subtle">
                          <td className="px-3 py-1.5 text-text-secondary">{v.market}</td>
                          <td className="px-3 py-1.5 text-right text-text-primary">
                            {formatUsd(v.openInterest)}
                          </td>
                          <td
                            className={`px-3 py-1.5 text-right ${v.funding == null ? 'text-text-faint' : v.funding < 0 ? 'text-up' : 'text-down'}`}
                          >
                            {v.funding == null ? '—' : `${v.funding.toFixed(4)}%`}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Stat
                label="Open interest"
                value={formatUsd(data.openInterest)}
                sub={`${data.oiShareOfMcap.toFixed(1)}% of market cap`}
                tone={data.oiShareOfMcap > 20 ? 'down' : undefined}
              />
              <Stat
                label="Leveraged volume"
                value={formatUsd(data.perpVolume)}
                sub={`${(data.perpVolume / data.volume24h).toFixed(1)}× spot volume`}
              />
              <Stat
                label="Staked"
                value={`${formatNumber(data.stakedEgld)} EGLD`}
                sub={`${(100 * data.stakedRatio).toFixed(2)}% of supply locked`}
              />
            </div>

            <section className="card overflow-hidden">
              <header className="px-4 py-2.5 border-b border-border bg-bg-elevated">
                <h2 className="text-[12px] font-semibold">
                  Private trading desks — supply staged for sale
                </h2>
                <p className="text-[10px] text-text-muted mt-0.5">
                  These two wallets fill large orders off the order book. Published nowhere
                  else.
                </p>
              </header>
              <div className="p-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
                {data.deskBreakdown.map((d) => (
                  <div key={d.label}>
                    <div className="eyebrow">{d.label}</div>
                    <div className="font-mono tabular text-[19px] mt-1">
                      {formatEgldBare(d.egld)}
                    </div>
                  </div>
                ))}
                <div>
                  <div className="eyebrow text-accent-cyan/80">Combined</div>
                  <div className="font-mono tabular text-[19px] mt-1 text-accent-cyan">
                    {formatEgldBare(data.deskTotal)}
                  </div>
                </div>
              </div>
            </section>

            <div className="flex flex-wrap items-center gap-x-5 gap-y-2 pt-1 text-[10.5px] font-mono text-text-faint">
              <span>updated {ago(data.fetchedAt, now)}</span>
              <button
                type="button"
                onClick={refresh}
                className="rounded px-2 py-1 -ml-2 uppercase tracking-wider text-accent-cyan/80 hover:text-accent-cyan hover:bg-accent-cyan/10 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-cyan/60"
              >
                Refresh now
              </button>
              <span>price and leverage: CoinGecko · chain data: MultiversX API</span>
              <span>Observations, not advice.</span>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
