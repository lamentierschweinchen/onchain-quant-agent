import { ResponsiveBar } from '@nivo/bar'
import type {
  TokenActivity,
  DefiActivity,
  TokenByHolders,
  TokenByVolume,
  NewlyIssuedToken,
  ProtocolBreakdown,
  HealthSignal,
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
  // xExchange top pair bar (small)
  // -------------------------------------------------------------------------
  const xexBarData = xexchange.top_pair
    ? [{ name: xexchange.top_pair, volume: xexchange.top_pair_volume_24h_usd ?? 0 }]
    : []

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

      {/* xExchange top pair bar */}
      {xexBarData.length > 0 && xexchange.top_pair_dominance_pct != null && (
        <CardSection
          title="Top Pair by 24h Volume"
          subtitle={`${xexchange.top_pair} dominates ${xexchange.top_pair_dominance_pct.toFixed(1)}% of DEX volume`}
        >
          <div className="p-4" style={{ height: 220 }}>
            <ResponsiveBar
              data={xexBarData}
              keys={['volume']}
              indexBy="name"
              layout="vertical"
              theme={darkTheme}
              colors={['#23F7DD']}
              margin={{ top: 12, right: 20, bottom: 50, left: 60 }}
              padding={0.5}
              valueFormat={(v) => formatUsd(v)}
              axisBottom={{ tickSize: 0, tickPadding: 8 }}
              axisLeft={{
                tickSize: 0,
                tickPadding: 6,
                format: (v) => formatUsd(v as number),
              }}
              enableGridY={true}
              enableGridX={false}
              labelTextColor="#0A0D14"
              labelSkipHeight={20}
              tooltip={({ indexValue, value }) => (
                <div style={tooltipStyle}>
                  <strong>{indexValue}</strong>
                  <br />
                  24h Volume: {formatUsd(value)}
                </div>
              )}
            />
          </div>
        </CardSection>
      )}

      {/* ---------------- Top 10 by Holders ---------------- */}
      <CardSection
        title="Top 10 Tokens by Holders"
        subtitle="Spam / airdrop tokens flagged inline"
      >
        <DataTable
          columns={holderColumns}
          data={holderRows}
          defaultSort={{ key: 'holders', dir: 'desc' }}
        />
      </CardSection>

      {/* ---------------- Top 10 by Volume ---------------- */}
      <CardSection title="Top 10 Tokens by Transaction Volume">
        <DataTable
          columns={volumeColumns}
          data={volumeSource}
          defaultSort={{ key: 'transactions', dir: 'desc' }}
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
