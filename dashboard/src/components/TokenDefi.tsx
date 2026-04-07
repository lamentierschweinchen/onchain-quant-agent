import { ResponsiveBar } from '@nivo/bar'
import type { TokenActivity, DefiActivity, TokenByHolders, TokenByTransactions } from '../types/report'
import { formatNumber, formatUsd, formatPct } from '../lib/formatters'
import { darkTheme } from '../lib/nivo-theme'
import { DataTable } from './ui/DataTable'
import { AnalysisBlock } from './ui/AnalysisBlock'
import { MetricCard } from './ui/MetricCard'
import type { Column } from './ui/DataTable'

interface TokenDefiProps {
  tokenData: TokenActivity
  defiData: DefiActivity
}

// DataTable row types
type HoldersRow = Record<string, unknown> & TokenByHolders
type VolumeRow = Record<string, unknown> & TokenByTransactions

// Protocol category color map
const PROTOCOL_CATEGORY_COLORS: Record<string, string> = {
  dex: '#23F7DD',
  lending: '#A855F7',
  liquid_staking: '#22C55E',
  nft_marketplace: '#F97316',
  bridge: '#3B82F6',
  perpetuals: '#EAB308',
  other: '#6B7280',
}

function ProtocolCategoryBadge({ category }: { category: string }) {
  const color = PROTOCOL_CATEGORY_COLORS[category] ?? PROTOCOL_CATEGORY_COLORS.other
  const label = category.replace(/_/g, ' ')
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize"
      style={{
        backgroundColor: `${color}20`,
        color: color,
        border: `1px solid ${color}40`,
      }}
    >
      {label}
    </span>
  )
}

// Likely airdrop / spam detection
function isLikelyAirdrop(row: TokenByHolders): boolean {
  return row.holders > 1_000_000 && (row.market_cap_usd === null || row.market_cap_usd < 100_000)
}

export function TokenDefi({ tokenData, defiData }: TokenDefiProps) {
  const { top_by_holders, top_by_transactions, xexchange, analysis: tokenAnalysis } = tokenData
  const { protocols, analysis: defiAnalysis } = defiData

  // -------------------------------------------------------------------------
  // Top Tokens by Holders — table columns
  // -------------------------------------------------------------------------
  const holderColumns: Column<HoldersRow>[] = [
    {
      key: 'identifier',
      label: 'Token',
      render: (v, row) => (
        <span className="inline-flex flex-col gap-0.5">
          <span className="font-mono text-xs text-text-primary">{v as string}</span>
          {isLikelyAirdrop(row as unknown as TokenByHolders) && (
            <span className="text-xs text-text-secondary italic">Likely airdrop</span>
          )}
        </span>
      ),
    },
    {
      key: 'name',
      label: 'Name',
    },
    {
      key: 'holders',
      label: 'Holders',
      align: 'right',
      sortable: true,
      render: (v) => formatNumber(v as number),
    },
    {
      key: 'price_usd',
      label: 'Price',
      align: 'right',
      sortable: true,
      render: (v) => (v != null ? formatUsd(v as number) : <span className="text-text-secondary">—</span>),
    },
    {
      key: 'market_cap_usd',
      label: 'Market Cap',
      align: 'right',
      sortable: true,
      render: (v) => (v != null ? formatUsd(v as number) : <span className="text-text-secondary">—</span>),
    },
  ]

  const holderRows: HoldersRow[] = top_by_holders.map((t) => ({ ...t } as HoldersRow))

  // -------------------------------------------------------------------------
  // Top Tokens by Volume — table columns
  // -------------------------------------------------------------------------
  const volumeColumns: Column<VolumeRow>[] = [
    {
      key: 'identifier',
      label: 'Token',
      render: (v) => <span className="font-mono text-xs text-text-primary">{v as string}</span>,
    },
    {
      key: 'name',
      label: 'Name',
    },
    {
      key: 'total_transactions',
      label: 'Transactions',
      align: 'right',
      sortable: true,
      render: (v) => formatNumber(v as number),
    },
    {
      key: 'change_pct',
      label: 'Change %',
      align: 'right',
      sortable: true,
      render: (v) => {
        if (v == null) return <span className="text-text-secondary">—</span>
        const n = v as number
        const sign = n >= 0 ? '+' : ''
        const cls = n > 0 ? 'text-green-400' : n < 0 ? 'text-red-400' : 'text-text-secondary'
        return (
          <span className={cls}>
            {sign}
            {formatPct(n)}
          </span>
        )
      },
    },
    {
      key: 'price_usd',
      label: 'Price',
      align: 'right',
      render: (v) => (v != null ? formatUsd(v as number) : <span className="text-text-secondary">—</span>),
    },
  ]

  const volumeRows: VolumeRow[] = top_by_transactions.map((t) => ({ ...t } as VolumeRow))

  // -------------------------------------------------------------------------
  // xExchange — no top_pairs array in this schema; show summary metrics only
  // -------------------------------------------------------------------------
  const xexBarData: { name: string; volume: number }[] = xexchange.top_pair
    ? [{ name: xexchange.top_pair, volume: xexchange.top_pair_volume_24h_usd ?? 0 }]
    : []

  return (
    <div className="space-y-6">
      {/* ------------------------------------------------------------------ */}
      {/* xExchange Summary Metrics                                            */}
      {/* ------------------------------------------------------------------ */}
      <div>
        <h3 className="text-sm font-semibold text-text-primary mb-3">xExchange Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            label="Total Pairs"
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
          />
          <MetricCard
            label="MEX Market Cap"
            value={formatUsd(xexchange.mex_market_cap_usd)}
          />
        </div>
      </div>

      {/* xExchange top pairs bar chart */}
      {xexBarData.length > 0 && (
        <div className="bg-surface rounded-lg border border-border p-4">
          <h3 className="text-sm font-semibold text-text-primary mb-3">
            Top Pairs by 24h Volume
          </h3>
          <div style={{ height: 250 }}>
            <ResponsiveBar
              data={xexBarData}
              keys={['volume']}
              indexBy="name"
              layout="vertical"
              theme={darkTheme}
              colors={['#23F7DD']}
              margin={{ top: 8, right: 20, bottom: 60, left: 80 }}
              padding={0.3}
              valueFormat={(v) => formatUsd(v)}
              axisBottom={{
                tickSize: 4,
                tickPadding: 6,
                tickRotation: -30,
              }}
              axisLeft={{
                tickSize: 4,
                tickPadding: 6,
                format: (v) => formatUsd(v as number),
              }}
              enableGridY={true}
              enableGridX={false}
              labelTextColor="#0D1117"
              labelSkipHeight={20}
              tooltip={({ indexValue, value }) => (
                <div
                  style={{
                    background: '#1A1F2E',
                    color: '#E2E8F0',
                    fontSize: 12,
                    borderRadius: '6px',
                    border: '1px solid #2A3144',
                    padding: '8px 12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
                  }}
                >
                  <strong>{indexValue}</strong>
                  <br />
                  24h Volume: {formatUsd(value)}
                </div>
              )}
            />
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Top Tokens by Holders                                                */}
      {/* ------------------------------------------------------------------ */}
      <div className="bg-surface rounded-lg border border-border overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <h3 className="text-sm font-semibold text-text-primary">Top Tokens by Holders</h3>
          <p className="text-xs text-text-secondary mt-0.5">
            Week-over-week holder changes available from next run
          </p>
        </div>
        <DataTable
          columns={holderColumns}
          data={holderRows}
          defaultSort={{ key: 'holders', dir: 'desc' }}
          emptyMessage="No token holder data available"
        />
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Top Tokens by Volume                                                 */}
      {/* ------------------------------------------------------------------ */}
      <div className="bg-surface rounded-lg border border-border overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <h3 className="text-sm font-semibold text-text-primary">Top Tokens by Transaction Volume</h3>
        </div>
        <DataTable
          columns={volumeColumns}
          data={volumeRows}
          defaultSort={{ key: 'total_transactions', dir: 'desc' }}
          emptyMessage="No transaction volume data available"
        />
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* DeFi Protocol Cards                                                  */}
      {/* ------------------------------------------------------------------ */}
      <div>
        <h3 className="text-sm font-semibold text-text-primary mb-3">DeFi Protocol Activity</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {protocols.map((protocol) => (
            <div
              key={protocol.name}
              className="bg-surface rounded-lg p-4 border border-border space-y-2"
            >
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-medium text-text-primary">{protocol.name}</span>
                <ProtocolCategoryBadge category={protocol.category} />
              </div>
              <div className="flex flex-wrap gap-4 text-xs text-text-secondary">
                {protocol.volume_24h_usd != null && (
                  <span>
                    Volume 24h:{' '}
                    <span className="font-mono text-text-primary">
                      {formatUsd(protocol.volume_24h_usd)}
                    </span>
                  </span>
                )}
                {protocol.active_pairs != null && (
                  <span>
                    Pairs:{' '}
                    <span className="font-mono text-text-primary">
                      {formatNumber(protocol.active_pairs)}
                    </span>
                  </span>
                )}
                {protocol.transfers_24h != null && (
                  <span>
                    Transfers 24h:{' '}
                    <span className="font-mono text-text-primary">
                      {formatNumber(protocol.transfers_24h)}
                    </span>
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Analysis blocks                                                      */}
      {/* ------------------------------------------------------------------ */}
      <div className="space-y-3">
        <div>
          <p className="text-xs font-medium text-text-secondary uppercase tracking-wide mb-2">
            Token Analysis
          </p>
          <AnalysisBlock text={tokenAnalysis} />
        </div>
        <div>
          <p className="text-xs font-medium text-text-secondary uppercase tracking-wide mb-2">
            DeFi Analysis
          </p>
          <AnalysisBlock text={defiAnalysis} />
        </div>
      </div>
    </div>
  )
}
