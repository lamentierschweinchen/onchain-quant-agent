import { useState } from 'react'
import type { ExchangeOrderbook, VenueDepth } from '../types/report'
import { formatEgldBare, formatUsd } from '../lib/formatters'
import { useElementWidth } from '../hooks/useElementWidth'
import { NullState } from './ui/NullState'
import { StatTile } from './ui/StatTile'

interface Props {
  data?: ExchangeOrderbook
  reportDate: string
}

// ---------------------------------------------------------------------------
// The OTC chart above this panel shows delivery in absolute EGLD, which invites
// reading each bar against the week's price as if nothing else traded. This
// panel supplies the denominator: the same delivery as a share of what traded
// on centralised exchanges that week, and the bids resting at the two venues
// the desks deliver into.
// ---------------------------------------------------------------------------

function median(xs: number[]) {
  const s = [...xs].sort((a, b) => a - b)
  const m = Math.floor(s.length / 2)
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2
}

export function MarketScale({ data, reportDate }: Props) {
  if (!data) {
    return <NullState message="Exchange-side scale starts at run #25." />
  }

  const series = data.delivery_share_series ?? []
  const shares = series.map((r) => r.share_pct)
  const minShare = shares.length ? Math.min(...shares) : null
  const maxShare = shares.length ? Math.max(...shares) : null
  const netRange =
    series.length > 1
      ? Math.max(...series.map((r) => r.net_one_way_egld)) / Math.min(...series.map((r) => r.net_one_way_egld))
      : null
  const spotWow = data.spot_volume_prior_7d_egld
    ? (100 * (data.spot_volume_7d_egld - data.spot_volume_prior_7d_egld)) / data.spot_volume_prior_7d_egld
    : null
  const multiple =
    data.binance_bybit_net_delivery_usd_7d && data.binance_bybit_bid_depth_2pct_usd
      ? data.binance_bybit_net_delivery_usd_7d / data.binance_bybit_bid_depth_2pct_usd
      : null

  return (
    <section className="card" aria-labelledby="market-scale-title">
      <header className="px-4 py-3 border-b border-border bg-bg-elevated flex flex-wrap items-baseline justify-between gap-3">
        <div className="min-w-0">
          <h3 id="market-scale-title" className="text-[13px] font-semibold text-text-primary tracking-tight">
            Pipeline at market scale
          </h3>
          <p className="text-[12px] text-text-secondary mt-0.5 max-w-[78ch]">
            The desks deliver about{' '}
            <span className="font-mono text-text-primary">
              {data.net_one_way_share_of_spot_volume_pct != null ? `${data.net_one_way_share_of_spot_volume_pct.toFixed(1)}%` : '—'}
            </span>{' '}
            of what trades on exchanges each week, a share that has barely moved in ten weeks. Against the
            bids resting where it lands, a week's delivery is far larger, so it is worked in over days.
          </p>
        </div>
        <span className="text-[10px] font-mono uppercase tracking-widest text-text-muted whitespace-nowrap">
          {reportDate}
        </span>
      </header>

      <div className="p-4 space-y-4">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <StatTile
            label="Delivery as share of spot volume"
            value={data.net_one_way_share_of_spot_volume_pct != null ? `${data.net_one_way_share_of_spot_volume_pct.toFixed(2)}%` : '—'}
            accent="cyan"
            sub={
              minShare != null && maxShare != null ? (
                <>
                  Ten-week range{' '}
                  <span className="font-mono text-text-primary">
                    {minShare.toFixed(1)}–{maxShare.toFixed(1)}%
                  </span>
                </>
              ) : null
            }
          />
          <StatTile
            label="Exchange spot volume · 7d"
            value={formatEgldBare(data.spot_volume_7d_egld)}
            unit="EGLD"
            sub={spotWow != null ? `${spotWow > 0 ? '+' : '−'}${Math.abs(spotWow).toFixed(0)}% vs the prior week` : null}
          />
          <StatTile
            label="Bids within 2% · Binance + Bybit"
            value={data.binance_bybit_bid_depth_2pct_usd != null ? formatUsd(data.binance_bybit_bid_depth_2pct_usd) : '—'}
            sub="The two venues the desks deliver into"
          />
          <StatTile
            label="Weekly delivery vs those bids"
            value={multiple != null ? `${multiple.toFixed(1)}×` : '—'}
            sub={
              data.binance_bybit_net_delivery_usd_7d != null ? (
                <>
                  <span className="font-mono text-text-primary">{formatUsd(data.binance_bybit_net_delivery_usd_7d)}</span>{' '}
                  net into those venues this week
                </>
              ) : null
            }
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-3">
          <div className="lg:col-span-3 bg-bg-elevated border border-border rounded-md p-3 min-w-0">
            <div className="mb-1 text-[10px] text-text-muted uppercase tracking-widest">
              Delivery as % of exchange spot volume · per run
            </div>
            {series.length > 1 ? (
              <ShareChart series={series} />
            ) : (
              <p className="py-10 text-center text-[12px] text-text-secondary">
                One run measured; the comparison starts next week.
              </p>
            )}
            <p className="mt-2 pt-2 border-t border-border-subtle text-[11px] text-text-secondary leading-relaxed">
              The share stayed between {minShare?.toFixed(1)}% and {maxShare?.toFixed(1)}% while delivery in
              EGLD varied {netRange != null ? `${netRange.toFixed(0)}-fold` : 'widely'}. Weeks that look big
              in absolute terms were big weeks for the whole market.
            </p>
          </div>

          <div className="lg:col-span-2 bg-bg-elevated border border-border rounded-md p-3 min-w-0">
            <div className="mb-3 text-[10px] text-text-muted uppercase tracking-widest">
              Order-book depth within 2% of mid
            </div>
            <DepthLadder data={data} />
            <p className="mt-3 pt-2 border-t border-border-subtle text-[11px] text-text-secondary leading-relaxed">
              One snapshot at report time from CoinGecko's exchange tickers, all EGLD pairs per venue
              summed. Next week's reading is the first comparison.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------------------

function ShareChart({ series }: { series: NonNullable<ExchangeOrderbook['delivery_share_series']> }) {
  const { ref, width } = useElementWidth<HTMLDivElement>()
  const H = 196
  return (
    <div ref={ref} style={{ minHeight: H }}>
      {width != null && <ShareBars series={series} width={width} height={H} />}
    </div>
  )
}

function ShareBars({
  series,
  width,
  height: H,
}: {
  series: NonNullable<ExchangeOrderbook['delivery_share_series']>
  width: number
  height: number
}) {
  const [active, setActive] = useState<number | null>(null)
  const P = { top: 24, right: 8, bottom: 26, left: 34 }
  const innerW = width - P.left - P.right
  const innerH = H - P.top - P.bottom
  const top = Math.max(3, Math.ceil(Math.max(...series.map((r) => r.share_pct)) + 0.5))
  const y = (v: number) => P.top + innerH - (v / top) * innerH
  const slot = innerW / series.length
  const barW = Math.min(slot * 0.58, 34)
  const med = median(series.map((r) => r.share_pct))
  const current = series[series.length - 1].run
  const ticks = Array.from({ length: top + 1 }, (_, i) => i)
  const a = active != null ? series[active] : null
  const showValues = slot > 30

  return (
    <div className="relative">
      <svg width={width} height={H} role="group" aria-label="Delivery as a share of exchange spot volume, one bar per run" className="block">
        {ticks.map((t) => (
          <g key={t}>
            <line x1={P.left} x2={width - P.right} y1={y(t)} y2={y(t)} stroke="var(--color-border-subtle)" />
            <text x={P.left - 8} y={y(t) + 3.5} textAnchor="end" fontSize={10.5} className="font-mono" fill="var(--color-text-secondary)">
              {t}%
            </text>
          </g>
        ))}

        {series.map((r, i) => {
          const cx = P.left + slot * i + slot / 2
          const isCur = r.run === current
          const isActive = active === i
          return (
            <g
              key={r.run}
              tabIndex={0}
              role="img"
              aria-label={`Run ${r.run}, week to ${r.date}: ${formatEgldBare(r.net_one_way_egld)} EGLD delivered, ${r.share_pct.toFixed(2)}% of ${formatEgldBare(r.spot_volume_7d_egld)} EGLD spot volume`}
              onMouseEnter={() => setActive(i)}
              onMouseLeave={() => setActive(null)}
              onFocus={() => setActive(i)}
              onBlur={() => setActive(null)}
              className="outline-none"
            >
              <rect x={cx - slot / 2} y={P.top} width={slot} height={innerH} fill="transparent" />
              {isActive && <rect x={cx - slot / 2 + 1} y={P.top} width={slot - 2} height={innerH} rx={3} fill="var(--color-surface-hover)" />}
              <rect
                x={cx - barW / 2}
                y={y(r.share_pct)}
                width={barW}
                height={Math.max(1, y(0) - y(r.share_pct))}
                rx={2}
                fill="var(--color-accent-cyan)"
                opacity={isCur || isActive ? 0.95 : 0.45}
              />
              {(isCur || showValues) && (
                <text
                  x={cx}
                  y={y(r.share_pct) - 6}
                  textAnchor="middle"
                  fontSize={10.5}
                  className="font-mono"
                  fontWeight={isCur ? 600 : 400}
                  fill={isCur ? 'var(--color-text-primary)' : 'var(--color-text-secondary)'}
                >
                  {r.share_pct.toFixed(1)}
                </text>
              )}
              <text
                x={cx}
                y={H - P.bottom + 16}
                textAnchor="middle"
                fontSize={10.5}
                className="font-mono"
                fontWeight={isCur ? 700 : 400}
                fill={isCur ? 'var(--color-accent-cyan)' : 'var(--color-text-secondary)'}
              >
                #{r.run}
              </text>
              <rect
                x={cx - slot / 2 + 1}
                y={P.top - 2}
                width={slot - 2}
                height={innerH + 4}
                rx={3}
                fill="none"
                stroke="var(--color-accent-cyan)"
                strokeWidth={1.5}
                className="focus-ring-svg"
              />
            </g>
          )
        })}

        {/* median, labelled in place */}
        <g pointerEvents="none">
          <line x1={P.left} x2={width - P.right} y1={y(med)} y2={y(med)} stroke="var(--color-text-secondary)" strokeDasharray="4 4" />
          <text x={P.left + 4} y={y(med) - 5} fontSize={10.5} className="font-mono" fill="var(--color-text-secondary)">
            median {med.toFixed(1)}%
          </text>
        </g>
      </svg>

      {a && (
        <div
          className="absolute pointer-events-none z-10 w-[196px] rounded-md border border-border-strong bg-surface-strong/95 px-3 py-2 shadow-lg"
          style={{
            top: 4,
            left: Math.min(Math.max(8, P.left + slot * (active as number) + slot / 2 - 98), width - 204),
          }}
        >
          <div className="text-[10.5px] font-mono text-text-secondary">
            Run #{a.run} · week to {a.date}
          </div>
          <div className="mt-1 font-mono text-[14px] font-semibold text-text-primary">{a.share_pct.toFixed(2)}%</div>
          <div className="mt-0.5 text-[11px] text-text-secondary">
            <span className="font-mono text-text-primary">{formatEgldBare(a.net_one_way_egld)}</span> delivered of{' '}
            <span className="font-mono text-text-primary">{formatEgldBare(a.spot_volume_7d_egld)}</span> EGLD traded
          </div>
        </div>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// An order-book ladder: bids grow left from the centre, asks grow right, values
// sit in fixed columns at the spine so nothing overflows at phone width.

const VENUES: Array<[keyof ExchangeOrderbook, string, boolean]> = [
  ['binance', 'Binance', true],
  ['bybit', 'Bybit', true],
  ['coinbase', 'Coinbase', false],
  ['gate', 'Gate', false],
  ['upbit', 'Upbit', false],
]

const LADDER = 'grid grid-cols-[68px_1fr_52px_52px_1fr] items-center gap-x-1.5'

function DepthLadder({ data }: { data: ExchangeOrderbook }) {
  const rows = VENUES.map(([k, label, pipeline]) => ({ label, pipeline, d: data[k] as VenueDepth | undefined })).filter(
    (r): r is { label: string; pipeline: boolean; d: VenueDepth } => !!r.d,
  )
  const max = Math.max(...rows.flatMap((r) => [r.d.depth_minus2_usd, r.d.depth_plus2_usd]), 1)

  return (
    <div role="table" aria-label="Order-book depth within 2 percent of mid, by venue">
      <div role="row" className={`${LADDER} pb-1.5 text-[10px] uppercase tracking-widest text-text-muted`}>
        <span role="columnheader">Venue</span>
        <span role="columnheader" className="text-right">
          Bids
        </span>
        <span role="columnheader" aria-label="Bid depth, USD" />
        <span role="columnheader" aria-label="Ask depth, USD" />
        <span role="columnheader">Asks</span>
      </div>
      <div className="space-y-1.5">
        {rows.map((r) => (
          <div key={r.label} role="row" className={LADDER}>
            <span role="rowheader" className="text-[12px] text-text-primary flex items-center gap-1.5 min-w-0">
              <span className="truncate">{r.label}</span>
              {r.pipeline && (
                <span
                  role="img"
                  aria-label="OTC pipeline destination"
                  title="The OTC desks deliver into this venue"
                  className="shrink-0 w-1.5 h-1.5 rounded-full"
                  style={{ background: 'var(--color-accent-cyan)' }}
                />
              )}
            </span>
            <span className="flex justify-end h-4" aria-hidden>
              <span
                className="h-full rounded-l-sm"
                style={{ width: `${(100 * r.d.depth_minus2_usd) / max}%`, background: 'var(--color-up)', opacity: 0.75 }}
              />
            </span>
            <span role="cell" className="font-mono text-[11px] text-text-primary text-right">
              {formatUsd(r.d.depth_minus2_usd)}
            </span>
            <span role="cell" className="font-mono text-[11px] text-text-secondary border-l border-border-strong pl-1.5">
              {formatUsd(r.d.depth_plus2_usd)}
            </span>
            <span className="flex h-4" aria-hidden>
              <span
                className="h-full rounded-r-sm"
                style={{ width: `${(100 * r.d.depth_plus2_usd) / max}%`, background: 'var(--color-text-secondary)', opacity: 0.55 }}
              />
            </span>
          </div>
        ))}
      </div>
      <div className="mt-3 pt-2 border-t border-border-subtle flex flex-wrap items-center justify-between gap-2 text-[11px]">
        <span className="text-text-secondary">
          All venues · <span className="font-mono">{data.all_venues.pairs}</span> pairs
        </span>
        <span className="font-mono">
          <span className="text-up">{formatUsd(data.all_venues.depth_minus2_usd)}</span>
          <span className="text-text-muted"> bid / </span>
          <span className="text-text-secondary">{formatUsd(data.all_venues.depth_plus2_usd)}</span>
          <span className="text-text-muted"> ask</span>
        </span>
      </div>
      <p className="mt-1.5 flex items-center gap-1.5 text-[11px] text-text-secondary">
        <span aria-hidden className="w-1.5 h-1.5 rounded-full" style={{ background: 'var(--color-accent-cyan)' }} />
        OTC pipeline destination
      </p>
    </div>
  )
}
