import { ResponsivePie } from '@nivo/pie'
import type {
  TokenActivity,
  DefiActivity,
  TokenByHolders,
  TokenByVolume,
  NewlyIssuedToken,
  ProtocolBreakdown,
  HealthSignal,
  PairByVolume,
} from '../types/report'
import {
  formatNumber,
  formatUsd,
  formatPct,
  formatEgldBare,
  formatDate,
} from '../lib/formatters'
import { darkTheme, tooltipStyle } from '../lib/nivo-theme'
import { DataTable } from './ui/DataTable'
import { AnalysisBlock } from './ui/AnalysisBlock'
import { MetricCard } from './ui/MetricCard'
import { AddressLink } from './ui/AddressLink'
import { tokenUrl, HEALTH_COLORS } from '../lib/constants'
import type { Column } from './ui/DataTable'

interface TokenDefiProps {
  tokenData: TokenActivity
  defiData: DefiActivity
}

type HoldersRow = Record<string, unknown> & TokenByHolders
type VolumeRow = Record<string, unknown> & TokenByVolume
type NewRow = Record<string, unknown> & NewlyIssuedToken
type ProtocolRow = Record<string, unknown> & ProtocolBreakdown

const PROTOCOL_CATEGORY_COLORS: Record<string, string> = {
  dex: '#23F7DD',
  lending: '#B975F0',
  liquid_staking: '#34D196',
  nft_marketplace: '#FB8534',
  bridge: '#5896F2',
  perpetuals: '#E8B43A',
  aggregator: '#23F7DD',
  other: '#6B7587',
}

function ProtocolCategoryBadge({ category }: { category: string }) {
  const color =
    PROTOCOL_CATEGORY_COLORS[category] ?? PROTOCOL_CATEGORY_COLORS.other
  const label = category.replace(/_/g, ' ')
  return (
    <span
      className="inline-flex items-center px-1.5 py-[1px] rounded text-[10px] font-mono font-semibold tracking-wider uppercase"
      style={{
        backgroundColor: `${color}1A`,
        color,
        border: `1px solid ${color}33`,
      }}
    >
      {label}
    </span>
  )
}

function HealthBadge({ signal }: { signal: HealthSignal | null | undefined }) {
  if (!signal) return null
  const color = HEALTH_COLORS[signal] ?? '#6B7587'
  return (
    <span
      className="inline-flex items-center gap-1 px-1.5 py-[1px] rounded text-[10px] font-mono font-semibold tracking-wider uppercase"
      style={{
        backgroundColor: `${color}1A`,
        color,
        border: `1px solid ${color}33`,
      }}
    >
      <span
        className="w-1.5 h-1.5 rounded-full"
        style={{ backgroundColor: color }}
      />
      {signal}
    </span>
  )
}

function isLikelyAirdrop(row: TokenByHolders): boolean {
  return (
    row.holders > 1_000_000 &&
    (row.market_cap_usd === null || (row.market_cap_usd ?? 0) < 100_000)
  )
}

function CardSection({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle?: string
  children: React.ReactNode
}) {
  return (
    <section className="card overflow-hidden">
      <header className="px-4 py-2.5 border-b border-border bg-bg-elevated">
        <h3 className="text-[12px] font-semibold text-text-primary tracking-tight">
          {title}
        </h3>
        {subtitle && (
          <p className="text-[10px] text-text-muted mt-0.5">{subtitle}</p>
        )}
      </header>
      {children}
    </section>
  )
}

function TokenIdCell({ identifier }: { identifier: string }) {
  return (
    <a
      href={tokenUrl(identifier)}
      target="_blank"
      rel="noopener noreferrer"
      className="font-mono text-[11px] text-accent-cyan hover:underline"
    >
      {identifier}
    </a>
  )
}

export function TokenDefi({ tokenData, defiData }: TokenDefiProps) {
  const {
    top_by_holders,
    top_by_volume,
    top_by_transactions,
    newly_issued = [],
    xexchange,
    analysis: tokenAnalysis,
  } = tokenData
  const {
    protocols,
    protocol_breakdown = [],
    analysis: defiAnalysis,
  } = defiData

  // -------------------------------------------------------------------------
  // Top by holders
  // -------------------------------------------------------------------------
  const holderColumns: Column<HoldersRow>[] = [
    {
      key: 'identifier',
      label: 'Token',
      render: (v, row) => (
        <span className="inline-flex flex-col gap-0.5">
          <TokenIdCell identifier={v as string} />
          {isLikelyAirdrop(row as unknown as TokenByHolders) && (
            <span className="text-[10px] text-text-muted italic">
              spam / airdrop
            </span>
          )}
        </span>
      ),
    },
    { key: 'name', label: 'Name' },
    {
      key: 'holders',
      label: 'Holders',
      align: 'right',
      sortable: true,
      render: (v) => (
        <span className="tabular text-text-primary">
          {formatNumber(v as number)}
        </span>
      ),
    },
    {
      key: 'holders_change',
      label: 'Δ WoW',
      align: 'right',
      sortable: true,
      render: (_v, row) => {
        const change = row.holders_change as number | null | undefined
        const fallback =
          row.previous_holders != null
            ? (row.holders as number) - (row.previous_holders as number)
            : null
        const n = change != null ? change : fallback
        if (n == null) return <span className="text-text-muted">—</span>
        const cls = n > 0 ? 'text-up' : n < 0 ? 'text-down' : 'text-flat'
        return (
          <span className={`${cls} tabular`}>
            {n >= 0 ? '+' : ''}
            {formatNumber(Math.abs(n))}
          </span>
        )
      },
    },
    {
      key: 'price_usd',
      label: 'Price',
      align: 'right',
      sortable: true,
      render: (v) =>
        v != null ? (
          <span className="tabular text-text-secondary">
            {formatUsd(v as number)}
          </span>
        ) : (
          <span className="text-text-muted">—</span>
        ),
    },
    {
      key: 'market_cap_usd',
      label: 'MCap',
      align: 'right',
      sortable: true,
      render: (v) =>
        v != null ? (
          <span className="tabular text-text-primary">
            {formatUsd(v as number)}
          </span>
        ) : (
          <span className="text-text-muted">—</span>
        ),
    },
  ]

  const holderRows: HoldersRow[] = top_by_holders
    .slice(0, 10)
    .map((t) => ({ ...t }) as HoldersRow)

  // -------------------------------------------------------------------------
  // Top by volume — prefer top_by_volume, fall back to top_by_transactions
  // -------------------------------------------------------------------------
  const volumeColumns: Column<VolumeRow>[] = [
    {
      key: 'identifier',
      label: 'Token',
      render: (v) => <TokenIdCell identifier={v as string} />,
    },
    { key: 'name', label: 'Name' },
    {
      key: 'transactions',
      label: 'TX (period)',
      align: 'right',
      sortable: true,
      render: (v) => (
        <span className="tabular text-text-primary">
          {v != null ? formatNumber(v as number) : '—'}
        </span>
      ),
    },
    {
      key: 'change_pct',
      label: 'Δ % WoW',
      align: 'right',
      sortable: true,
      render: (v) => {
        if (v == null) return <span className="text-text-muted">—</span>
        const n = v as number
        const cls = n > 0 ? 'text-up' : n < 0 ? 'text-down' : 'text-flat'
        return (
          <span className={`${cls} tabular`}>
            {n >= 0 ? '+' : ''}
            {formatPct(n)}
          </span>
        )
      },
    },
    {
      key: 'price_usd',
      label: 'Price',
      align: 'right',
      sortable: true,
      render: (v) =>
        v != null ? (
          <span className="tabular text-text-secondary">
            {formatUsd(v as number)}
          </span>
        ) : (
          <span className="text-text-muted">—</span>
        ),
    },
  ]

  const volumeSource: VolumeRow[] = top_by_volume
    ? top_by_volume.slice(0, 10).map((t) => ({ ...t }) as VolumeRow)
    : top_by_transactions
      ? top_by_transactions.slice(0, 10).map((t) => ({
          identifier: t.identifier,
          name: t.name,
          transactions: t.total_transactions,
        } as VolumeRow))
      : []

  // -------------------------------------------------------------------------
  // Newly issued (top 5)
  // -------------------------------------------------------------------------
  const newColumns: Column<NewRow>[] = [
    {
      key: 'identifier',
      label: 'Token',
      render: (v) => <TokenIdCell identifier={v as string} />,
    },
    { key: 'name', label: 'Name' },
    {
      key: 'deployer',
      label: 'Deployer',
      render: (_v, row) =>
        row.deployer ? (
          <AddressLink
            address={row.deployer as string}
            label={row.deployer_label as string | null}
          />
        ) : (
          <span className="text-text-muted">—</span>
        ),
    },
    {
      key: 'holders',
      label: 'Holders',
      align: 'right',
      sortable: true,
      render: (v) =>
        v != null ? (
          <span className="tabular text-text-primary">
            {formatNumber(v as number)}
          </span>
        ) : (
          <span className="text-text-muted">—</span>
        ),
    },
    {
      key: 'transactions',
      label: 'TX',
      align: 'right',
      sortable: true,
      render: (v) =>
        v != null ? (
          <span className="tabular text-text-secondary">
            {formatNumber(v as number)}
          </span>
        ) : (
          <span className="text-text-muted">—</span>
        ),
    },
    {
      key: 'issued_at',
      label: 'Issued',
      align: 'right',
      render: (v) =>
        v ? (
          <span className="text-[11px] text-text-muted font-mono">
            {formatDate(String(v).slice(0, 10))}
          </span>
        ) : (
          <span className="text-text-muted">—</span>
        ),
    },
  ]

  const newRows: NewRow[] = newly_issued
    .slice(0, 5)
    .map((t) => ({ ...t }) as NewRow)

  // -------------------------------------------------------------------------
  // xExchange top pairs donut (NEW): pairs with >=1% share + "Other" bucket
  // -------------------------------------------------------------------------
  const pairsForDonut: PairByVolume[] = xexchange.top_pairs_by_volume ?? []

  // Synthesize from legacy fields if the array is missing on older reports
  const fallbackDonut: PairByVolume[] =
    pairsForDonut.length === 0 && xexchange.top_pair
      ? [
          {
            name: xexchange.top_pair,
            volume_24h_usd: xexchange.top_pair_volume_24h_usd ?? 0,
            share_pct: xexchange.top_pair_dominance_pct ?? 100,
            is_other: false,
          },
          ...(xexchange.top_pair_dominance_pct != null &&
          xexchange.top_pair_dominance_pct < 100 &&
          xexchange.total_volume_24h_usd
            ? [
                {
                  name: 'Other pairs',
                  volume_24h_usd:
                    xexchange.total_volume_24h_usd -
                    (xexchange.top_pair_volume_24h_usd ?? 0),
                  share_pct: 100 - (xexchange.top_pair_dominance_pct ?? 0),
                  is_other: true as const,
                },
              ]
            : []),
        ]
      : []

  const donutData = (pairsForDonut.length > 0 ? pairsForDonut : fallbackDonut).map(
    (p) => ({
      id: p.name,
      label: p.name,
      value: p.volume_24h_usd,
      share_pct: p.share_pct,
      tvl_usd: p.tvl_usd,
      trades_count_24h: p.trades_count_24h,
      is_other: p.is_other,
    }),
  )

  // Restrained palette: cyan accent for the dominant pair, fading desaturation
  const PAIR_COLORS = [
    '#23F7DD', // dominant — accent cyan
    '#5896F2', // 2nd — exchange blue
    '#B975F0', // 3rd — defi purple
    '#34D196', // 4th — up green
    '#E8B43A', // 5th — medium yellow
    '#FB8534', // 6th — high orange
    '#5C6679', // 7+
    '#3F4759',
  ]
  const otherColor = '#2D364D' // muted gray for "Other pairs"

  const donutWithColor = donutData.map((d, i) => ({
    ...d,
    color: d.is_other ? otherColor : PAIR_COLORS[i] ?? '#5C6679',
  }))

  // -------------------------------------------------------------------------
  // Per-protocol breakdown table
  // -------------------------------------------------------------------------
  const protocolColumns: Column<ProtocolRow>[] = [
    {
      key: 'protocol',
      label: 'Protocol',
    },
    {
      key: 'category',
      label: 'Category',
      render: (v) => <ProtocolCategoryBadge category={v as string} />,
    },
    {
      key: 'tvl_egld',
      label: 'TVL EGLD',
      align: 'right',
      sortable: true,
      render: (v) =>
        v != null ? (
          <span className="tabular text-text-primary">
            {formatEgldBare(v as number)}
          </span>
        ) : (
          <span className="text-text-muted">—</span>
        ),
    },
    {
      key: 'tvl_usd',
      label: 'TVL USD',
      align: 'right',
      sortable: true,
      render: (v) =>
        v != null ? (
          <span className="tabular text-text-secondary">
            {formatUsd(v as number)}
          </span>
        ) : (
          <span className="text-text-muted">—</span>
        ),
    },
    {
      key: 'tvl_wow_change_pct',
      label: 'Δ % WoW',
      align: 'right',
      sortable: true,
      render: (v) => {
        if (v == null) return <span className="text-text-muted">—</span>
        const n = v as number
        const cls = n > 0 ? 'text-up' : n < 0 ? 'text-down' : 'text-flat'
        return (
          <span className={`${cls} tabular`}>
            {n >= 0 ? '+' : ''}
            {formatPct(n)}
          </span>
        )
      },
    },
    {
      key: 'transfers_24h',
      label: '24h TXs',
      align: 'right',
      sortable: true,
      render: (v) =>
        v != null ? (
          <span className="tabular text-text-secondary">
            {formatNumber(v as number)}
          </span>
        ) : (
          <span className="text-text-muted">—</span>
        ),
    },
    {
      key: 'health_signal',
      label: 'Health',
      render: (v) => <HealthBadge signal={v as HealthSignal | null | undefined} />,
    },
    {
      key: 'notable_events',
      label: 'Notable',
      render: (v) =>
        v ? (
          <span className="text-[11.5px] text-text-secondary">
            {v as string}
          </span>
        ) : (
          <span className="text-text-muted">—</span>
        ),
    },
  ]

  const protocolRows: ProtocolRow[] = protocol_breakdown.map(
    (p) => ({ ...p }) as ProtocolRow,
  )

  return (
    <div className="space-y-4">
      {/* ---------------- xExchange Hero Strip ---------------- */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <MetricCard
          accent
          label="xExchange Pairs"
          value={formatNumber(xexchange.total_pairs)}
        />
        <MetricCard
          label="24h Volume"
          value={
            xexchange.total_volume_24h_usd != null
              ? formatUsd(xexchange.total_volume_24h_usd)
              : '—'
          }
        />
        <MetricCard
          label="MEX Price"
          value={formatUsd(xexchange.mex_price_usd)}
          delta={
            xexchange.mex_price_change_wow_pct ??
            xexchange.mex_price_change_24h_pct ??
            null
          }
          deltaFormat="pct"
        />
        <MetricCard
          label="MEX Market Cap"
          value={formatUsd(xexchange.mex_market_cap_usd)}
        />
      </div>

      {/* xExchange volume share donut */}
      {donutWithColor.length > 0 && (
        <CardSection
          title="Volume Share by Pair (24h)"
          subtitle={
            xexchange.top_pair_dominance_pct != null
              ? `${donutWithColor[0].label} commands ${xexchange.top_pair_dominance_pct.toFixed(1)}% — pairs <1% rolled into "Other"`
              : 'Pairs ≥1% of DEX volume — long tail rolled into "Other"'
          }
        >
          <div className="p-4 grid grid-cols-1 md:grid-cols-[1fr_320px] gap-6 items-center">
            {/* Donut */}
            <div style={{ height: 280 }}>
              <ResponsivePie
                data={donutWithColor}
                theme={darkTheme}
                colors={({ data }) => data.color as string}
                innerRadius={0.62}
                cornerRadius={2}
                padAngle={1}
                activeOuterRadiusOffset={6}
                borderWidth={0}
                arcLinkLabelsSkipAngle={360}
                arcLabelsSkipAngle={360}
                tooltip={({ datum }) => {
                  const d = datum.data as (typeof donutWithColor)[number]
                  return (
                    <div style={tooltipStyle}>
                      <strong>{d.label}</strong>
                      <br />
                      Volume: {formatUsd(d.value)}
                      <br />
                      Share: {d.share_pct.toFixed(2)}%
                      {d.tvl_usd != null && (
                        <>
                          <br />
                          TVL: {formatUsd(d.tvl_usd)}
                        </>
                      )}
                    </div>
                  )
                }}
                margin={{ top: 8, right: 8, bottom: 8, left: 8 }}
              />
            </div>

            {/* Legend table */}
            <div className="text-[12px] font-mono">
              <div className="flex justify-between text-text-muted text-[10px] uppercase tracking-wider pb-2 border-b border-border-subtle mb-1">
                <span>Pair</span>
                <span>Volume / Share</span>
              </div>
              <ul className="space-y-1.5">
                {donutWithColor.map((d) => (
                  <li
                    key={d.id}
                    className="flex items-center justify-between gap-3 py-0.5"
                  >
                    <span className="flex items-center gap-2 min-w-0">
                      <span
                        className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
                        style={{ backgroundColor: d.color }}
                      />
                      <span
                        className={`truncate ${d.is_other ? 'text-text-muted italic' : 'text-text-primary'}`}
                      >
                        {d.label}
                      </span>
                    </span>
                    <span className="flex-shrink-0 text-right">
                      <span className="text-text-secondary tabular">
                        {formatUsd(d.value)}
                      </span>
                      <span className="text-text-muted tabular ml-2 inline-block w-12 text-right">
                        {d.share_pct.toFixed(1)}%
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
              {xexchange.total_volume_24h_usd != null && (
                <div className="flex justify-between mt-2 pt-2 border-t border-border-subtle text-text-muted">
                  <span className="uppercase tracking-wider text-[10px]">
                    Total
                  </span>
                  <span className="tabular text-text-primary">
                    {formatUsd(xexchange.total_volume_24h_usd)}
                  </span>
                </div>
              )}
            </div>
          </div>
        </CardSection>
      )}

      {/* ---------------- Top Tokens by Holders ---------------- */}
      <CardSection
        title="Top Tokens by Holders"
        subtitle="Spam / airdrop tokens flagged inline"
      >
        <DataTable
          columns={holderColumns}
          data={holderRows}
          defaultSort={{ key: 'holders', dir: 'desc' }}
          collapsed={5}
          noun="token"
        />
      </CardSection>

      {/* ---------------- Top Tokens by Volume ---------------- */}
      <CardSection title="Top Tokens by Transaction Volume">
        <DataTable
          columns={volumeColumns}
          data={volumeSource}
          defaultSort={{ key: 'transactions', dir: 'desc' }}
          collapsed={5}
          noun="token"
        />
      </CardSection>

      {/* ---------------- Newly Issued (top 5) ---------------- */}
      {newRows.length > 0 && (
        <CardSection
          title="Newly-Issued Tokens This Week"
          subtitle="Top 5 by holder traction in the last 7 days"
        >
          <DataTable columns={newColumns} data={newRows} />
        </CardSection>
      )}

      {/* ---------------- Per-Protocol DeFi Breakdown (NEW) ---------------- */}
      {protocolRows.length > 0 && (
        <CardSection
          title="DeFi — Per-Protocol Breakdown"
          subtitle="TVL, transfers, health signal across tracked DeFi protocols"
        >
          <DataTable
            columns={protocolColumns}
            data={protocolRows}
            defaultSort={{ key: 'tvl_egld', dir: 'desc' }}
            collapsed={5}
            noun="protocol"
          />
        </CardSection>
      )}

      {/* ---------------- Legacy protocol cards (always visible if present) ---------------- */}
      {protocols.length > 0 && (
        <CardSection
          title="DeFi Protocol Activity (legacy view)"
          subtitle="Aggregated activity per known protocol contract"
        >
          <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-3">
            {protocols.map((protocol) => (
              <div
                key={protocol.name}
                className="bg-bg-elevated border border-border rounded p-3 space-y-2"
              >
                <div className="flex items-center gap-2 flex-wrap justify-between">
                  <span className="font-medium text-text-primary text-[13px]">
                    {protocol.name}
                  </span>
                  <ProtocolCategoryBadge category={protocol.category} />
                </div>
                <div className="grid grid-cols-2 gap-x-3 gap-y-1 text-[11px] font-mono">
                  {protocol.tvl_usd != null && (
                    <div>
                      <span className="text-text-muted">TVL </span>
                      <span className="text-text-primary tabular">
                        {formatUsd(protocol.tvl_usd)}
                      </span>
                    </div>
                  )}
                  {protocol.tvl_wow_change_pct != null && (
                    <div>
                      <span className="text-text-muted">Δ WoW </span>
                      <span
                        className={
                          protocol.tvl_wow_change_pct > 0
                            ? 'text-up'
                            : protocol.tvl_wow_change_pct < 0
                              ? 'text-down'
                              : 'text-flat'
                        }
                      >
                        {protocol.tvl_wow_change_pct > 0 ? '+' : ''}
                        {protocol.tvl_wow_change_pct.toFixed(2)}%
                      </span>
                    </div>
                  )}
                  {protocol.volume_24h_usd != null && (
                    <div>
                      <span className="text-text-muted">Vol 24h </span>
                      <span className="text-text-primary tabular">
                        {formatUsd(protocol.volume_24h_usd)}
                      </span>
                    </div>
                  )}
                  {protocol.transfers_24h != null && (
                    <div>
                      <span className="text-text-muted">TXs 24h </span>
                      <span className="text-text-primary tabular">
                        {formatNumber(protocol.transfers_24h)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </CardSection>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <AnalysisBlock label="Token Analysis" text={tokenAnalysis} />
        <AnalysisBlock label="DeFi Analysis" text={defiAnalysis} />
      </div>
    </div>
  )
}
