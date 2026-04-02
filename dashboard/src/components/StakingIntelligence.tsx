import { ResponsiveBar } from '@nivo/bar'
import type { StakingIntelligence, StakingProvider } from '../types/report'
import { formatEgld, formatNumber, cleanServiceFee } from '../lib/formatters'
import { darkTheme } from '../lib/nivo-theme'
import { DataTable } from './ui/DataTable'
import { AnalysisBlock } from './ui/AnalysisBlock'
import type { Column } from './ui/DataTable'

interface StakingIntelligenceProps {
  data: StakingIntelligence
}

// Row type passed to DataTable (needs Record<string, unknown>)
type ProviderRow = Record<string, unknown> & {
  _rank: number
  name: string
  locked_egld: number
  change_egld: number | null
  num_delegators: number
  apr: number
  service_fee_pct: number
  num_nodes: number
}

function hhiLabel(hhi: number): { text: string; className: string } {
  if (hhi < 0.15) return { text: 'Competitive', className: 'bg-green-500/20 text-green-400 border border-green-500/30' }
  if (hhi <= 0.25) return { text: 'Moderate', className: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' }
  return { text: 'Concentrated', className: 'bg-red-500/20 text-red-400 border border-red-500/30' }
}

export function StakingIntelligence({ data }: StakingIntelligenceProps) {
  const { top_providers, concentration, analysis } = data

  // Sort providers by locked_egld descending for rank assignment and chart
  const sortedProviders = [...top_providers].sort((a, b) => b.locked_egld - a.locked_egld)

  // Build table rows with rank
  const tableRows: ProviderRow[] = sortedProviders.map((p, i) => ({
    _rank: i + 1,
    name: p.name,
    locked_egld: p.locked_egld,
    change_egld: p.change_egld,
    num_delegators: p.num_delegators,
    apr: p.apr,
    service_fee_pct: p.service_fee_pct,
    num_nodes: p.num_nodes,
  }))

  const columns: Column<ProviderRow>[] = [
    {
      key: '_rank',
      label: '#',
      align: 'left',
      render: (v) => (
        <span className="text-text-secondary font-mono text-xs">{v as number}</span>
      ),
    },
    {
      key: 'name',
      label: 'Provider',
      align: 'left',
    },
    {
      key: 'locked_egld',
      label: 'Locked EGLD',
      align: 'right',
      sortable: true,
      render: (v) => formatEgld(v as number),
    },
    {
      key: 'change_egld',
      label: 'Change',
      align: 'right',
      sortable: true,
      render: (v) => {
        if (v == null) return <span className="text-text-secondary">—</span>
        const n = v as number
        const sign = n >= 0 ? '+' : ''
        const cls = n > 0 ? 'text-green-400' : n < 0 ? 'text-red-400' : 'text-text-secondary'
        return <span className={cls}>{sign}{formatEgld(Math.abs(n))}</span>
      },
    },
    {
      key: 'num_delegators',
      label: 'Delegators',
      align: 'right',
      sortable: true,
      render: (v) => formatNumber(v as number),
    },
    {
      key: 'apr',
      label: 'APR %',
      align: 'right',
      sortable: true,
      render: (v) => cleanServiceFee(v as number),
    },
    {
      key: 'service_fee_pct',
      label: 'Fee %',
      align: 'right',
      sortable: true,
      render: (v) => cleanServiceFee(v as number),
    },
    {
      key: 'num_nodes',
      label: 'Nodes',
      align: 'right',
      sortable: true,
    },
  ]

  // Bar chart: top 15 providers by locked_egld
  const top15 = sortedProviders.slice(0, 15)
  const barData = [...top15]
    .reverse() // horizontal bar: bottom = first item, so reverse for descending top-to-bottom
    .map((p) => ({
      name: p.name,
      locked_egld: p.locked_egld,
    }))

  // Abbreviate EGLD values for bar axis labels
  function abbreviateEgld(value: number): string {
    if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`
    if (value >= 1_000) return `${Math.round(value / 1_000)}K`
    return String(Math.round(value))
  }

  const hhi = concentration.herfindahl_index
  const prevHhi = concentration.previous_herfindahl
  const hhiBadge = hhi !== null ? hhiLabel(hhi) : null

  return (
    <div className="space-y-6">
      {/* Provider leaderboard table */}
      <div className="bg-surface rounded-lg border border-border overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <h3 className="text-sm font-semibold text-text-primary">Provider Leaderboard</h3>
        </div>
        <DataTable
          columns={columns}
          data={tableRows}
          defaultSort={{ key: 'locked_egld', dir: 'desc' }}
          rowClassName={(row: ProviderRow) => {
            const r = row as StakingProvider
            return r.apr > 8.5 && r.service_fee_pct < 5 ? 'bg-green-500/5' : ''
          }}
        />
      </div>

      {/* Concentration metrics */}
      <div className="bg-surface rounded-lg border border-border p-4 space-y-4">
        <h3 className="text-sm font-semibold text-text-primary">Stake Concentration</h3>

        {/* Top 5 share */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-text-secondary mb-1">
            <span>Top 5 Share</span>
            <span className="font-mono text-text-primary">
              {concentration.top_5_share_pct.toFixed(1)}%
            </span>
          </div>
          <div className="h-2 rounded-full overflow-hidden" style={{ background: '#2A3144' }}>
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${Math.min(concentration.top_5_share_pct, 100)}%`,
                background: '#23F7DD',
              }}
            />
          </div>
        </div>

        {/* Top 10 share */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-text-secondary mb-1">
            <span>Top 10 Share</span>
            <span className="font-mono text-text-primary">
              {concentration.top_10_share_pct.toFixed(1)}%
            </span>
          </div>
          <div className="h-2 rounded-full overflow-hidden" style={{ background: '#2A3144' }}>
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${Math.min(concentration.top_10_share_pct, 100)}%`,
                background: '#23F7DD',
              }}
            />
          </div>
        </div>

        {/* HHI */}
        <div className="flex items-center gap-3 flex-wrap">
          <span className="text-xs text-text-secondary">HHI (Herfindahl Index):</span>
          {hhi !== null ? (
            <>
              <span className="font-mono text-sm text-text-primary">{hhi.toFixed(4)}</span>
              {hhiBadge && (
                <span
                  className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${hhiBadge.className}`}
                >
                  {hhiBadge.text}
                </span>
              )}
              {prevHhi !== null && prevHhi !== undefined && (
                <span className="text-xs text-text-secondary">
                  {hhi < prevHhi ? (
                    <span className="text-green-400">▼ improving</span>
                  ) : hhi > prevHhi ? (
                    <span className="text-red-400">▲ concentrating</span>
                  ) : (
                    <span>— unchanged</span>
                  )}
                </span>
              )}
            </>
          ) : (
            <span className="text-text-secondary text-sm">—</span>
          )}
        </div>
      </div>

      {/* Provider distribution bar chart */}
      <div className="bg-surface rounded-lg border border-border p-4">
        <h3 className="text-sm font-semibold text-text-primary mb-3">
          Top 15 Providers by Locked EGLD
        </h3>
        <div style={{ height: 400 }}>
          <ResponsiveBar
            data={barData}
            keys={['locked_egld']}
            indexBy="name"
            layout="horizontal"
            theme={darkTheme}
            colors={['#23F7DD']}
            margin={{ top: 8, right: 80, bottom: 40, left: 160 }}
            padding={0.3}
            valueFormat={(v) => abbreviateEgld(v)}
            axisBottom={{
              legend: 'EGLD Locked',
              legendPosition: 'middle',
              legendOffset: 32,
              format: (v) => abbreviateEgld(v as number),
              tickSize: 4,
            }}
            axisLeft={{
              tickSize: 0,
              tickPadding: 8,
            }}
            enableGridX={true}
            enableGridY={false}
            labelTextColor="#0D1117"
            labelSkipWidth={40}
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
                {formatEgld(value)}
              </div>
            )}
          />
        </div>
      </div>

      {/* Analysis */}
      <AnalysisBlock text={analysis} />
    </div>
  )
}
