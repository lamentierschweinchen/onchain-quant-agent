import { ResponsiveBar } from '@nivo/bar'
import type { WhaleIntelligence, WalletChange, LargeTransaction } from '../types/report'
import { formatEgld, formatUsd, formatPct, formatTimestamp, formatDate } from '../lib/formatters'
import { darkTheme } from '../lib/nivo-theme'
import { txUrl } from '../lib/constants'
import { CATEGORY_COLORS } from '../lib/constants'
import { DataTable } from './ui/DataTable'
import { AddressLink } from './ui/AddressLink'
import { AnalysisBlock } from './ui/AnalysisBlock'
import { NullState } from './ui/NullState'
import type { Column } from './ui/DataTable'

interface WhaleIntelligenceProps {
  data: WhaleIntelligence
}

// DataTable row types
type WalletRow = Record<string, unknown> & WalletChange
type TxRow = Record<string, unknown> & LargeTransaction

// Map category string to a color hex for badge backgrounds
function categoryColor(category: string | null): string {
  if (!category) return CATEGORY_COLORS.other
  const key = category as keyof typeof CATEGORY_COLORS
  return CATEGORY_COLORS[key] ?? CATEGORY_COLORS.other
}

// Subtle row tint based on category
function walletRowClass(row: WalletRow): string {
  if (row.category === 'exchange') return 'bg-blue-500/5'
  if (row.category === 'defi') return 'bg-purple-500/5'
  if (row.category === 'team') return 'bg-green-500/5'
  return ''
}

// Category pill badge
function CategoryBadge({ category }: { category: string | null }) {
  const label = category ?? 'unknown'
  const color = categoryColor(category)
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

// Flow type badge
function FlowTypeBadge({ flowType }: { flowType: string }) {
  const isInflow = flowType.includes('inflow') || flowType === 'staking'
  const isOutflow = flowType.includes('outflow') || flowType === 'unstaking'
  let bg = '#6B7280'
  if (isInflow) bg = '#EF4444'
  if (isOutflow) bg = '#22C55E'
  const label = flowType.replace(/_/g, ' ')
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium capitalize"
      style={{
        backgroundColor: `${bg}20`,
        color: bg,
        border: `1px solid ${bg}40`,
      }}
    >
      {label}
    </span>
  )
}

export function WhaleIntelligence({ data }: WhaleIntelligenceProps) {
  const { exchange_flows, wallet_changes, large_transactions, dormant_activations, analysis } = data

  // -------------------------------------------------------------------------
  // Exchange flows: check if ALL net_flow_egld are null
  // -------------------------------------------------------------------------
  const allFlowsNull = exchange_flows.by_exchange.every((e) => e.net_flow_egld === null)

  // Aggregate duplicate exchange names by summing their net_flow
  const exchangeMap = new Map<string, number>()
  if (!allFlowsNull) {
    for (const entry of exchange_flows.by_exchange) {
      if (entry.net_flow_egld !== null) {
        exchangeMap.set(
          entry.exchange,
          (exchangeMap.get(entry.exchange) ?? 0) + entry.net_flow_egld,
        )
      }
    }
  }

  const barData = Array.from(exchangeMap.entries())
    .map(([exchange, net_flow]) => ({ exchange, net_flow }))
    .sort((a, b) => Math.abs(b.net_flow) - Math.abs(a.net_flow))
    // put reversed so the largest bar appears at top in horizontal layout
    .reverse()

  // Net flow direction for summary indicator
  const netFlow = exchange_flows.net_exchange_flow_egld
  const netFlowPositive = netFlow !== null && netFlow > 0

  // -------------------------------------------------------------------------
  // Wallet changes table columns
  // -------------------------------------------------------------------------
  const walletColumns: Column<WalletRow>[] = [
    {
      key: 'address',
      label: 'Address',
      render: (_v, row) => (
        <AddressLink address={row.address as string} label={row.label as string | null} />
      ),
    },
    {
      key: 'category',
      label: 'Category',
      render: (_v, row) => <CategoryBadge category={row.category as string | null} />,
    },
    {
      key: 'current_balance_egld',
      label: 'Balance',
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
        return (
          <span className={cls}>
            {sign}
            {formatEgld(Math.abs(n))}
          </span>
        )
      },
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
  ]

  const walletRows: WalletRow[] = wallet_changes.map((w) => ({ ...w } as WalletRow))

  // -------------------------------------------------------------------------
  // Large transactions table columns
  // -------------------------------------------------------------------------
  const txColumns: Column<TxRow>[] = [
    {
      key: 'timestamp',
      label: 'Time',
      render: (v) => (
        <span className="text-text-secondary text-xs font-mono">{formatTimestamp(v as string)}</span>
      ),
    },
    {
      key: 'sender',
      label: 'From',
      render: (_v, row) => (
        <AddressLink address={row.sender as string} label={row.sender_label as string | null} />
      ),
    },
    {
      key: 'receiver',
      label: 'To',
      render: (_v, row) => (
        <AddressLink address={row.receiver as string} label={row.receiver_label as string | null} />
      ),
    },
    {
      key: 'value_egld',
      label: 'Value EGLD',
      align: 'right',
      render: (v) => formatEgld(v as number),
    },
    {
      key: 'value_usd',
      label: 'Value USD',
      align: 'right',
      render: (v) => formatUsd(v as number),
    },
    {
      key: 'flow_type',
      label: 'Flow Type',
      render: (v) => <FlowTypeBadge flowType={v as string} />,
    },
    {
      key: 'hash',
      label: 'TX',
      render: (v) => (
        <a
          href={txUrl(v as string)}
          target="_blank"
          rel="noopener noreferrer"
          className="font-mono text-xs text-accent-cyan hover:underline"
        >
          {(v as string).slice(0, 8)}…
        </a>
      ),
    },
  ]

  const txRows: TxRow[] = large_transactions.map((t) => ({ ...t } as TxRow))

  return (
    <div className="space-y-6">
      {/* ------------------------------------------------------------------ */}
      {/* Exchange Flows                                                       */}
      {/* ------------------------------------------------------------------ */}
      <div className="bg-surface rounded-lg border border-border overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <h3 className="text-sm font-semibold text-text-primary">Exchange Flows</h3>
        </div>
        <div className="p-4">
          {allFlowsNull ? (
            <NullState message="Baseline — exchange flow tracking starts next week" />
          ) : (
            <div className="space-y-4">
              {/* Net flow indicator */}
              {netFlow !== null && (
                <div className="flex items-baseline gap-3">
                  <span
                    className={`text-3xl font-mono font-bold ${netFlowPositive ? 'text-red-400' : 'text-green-400'}`}
                  >
                    {netFlowPositive ? '▲' : '▼'} {formatEgld(Math.abs(netFlow))}
                  </span>
                  <span className="text-sm text-text-secondary">
                    net {netFlowPositive ? 'inflow (sell pressure)' : 'outflow (accumulation)'}
                  </span>
                </div>
              )}

              {/* Bar chart */}
              <div style={{ height: 300 }}>
                <ResponsiveBar
                  data={barData}
                  keys={['net_flow']}
                  indexBy="exchange"
                  layout="horizontal"
                  theme={darkTheme}
                  colors={({ value }) =>
                    (value as number) < 0 ? '#22C55E' : '#EF4444'
                  }
                  margin={{ top: 8, right: 80, bottom: 40, left: 140 }}
                  padding={0.3}
                  valueFormat={(v) => formatEgld(Math.abs(v))}
                  axisBottom={{
                    legend: 'Net Flow EGLD',
                    legendPosition: 'middle',
                    legendOffset: 32,
                    format: (v) => {
                      const n = v as number
                      if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`
                      if (Math.abs(n) >= 1_000) return `${Math.round(n / 1_000)}K`
                      return String(Math.round(n))
                    },
                    tickSize: 4,
                  }}
                  axisLeft={{ tickSize: 0, tickPadding: 8 }}
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
                      Net flow: {formatEgld(value)}
                    </div>
                  )}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Wallet Changes                                                       */}
      {/* ------------------------------------------------------------------ */}
      <div className="bg-surface rounded-lg border border-border overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <h3 className="text-sm font-semibold text-text-primary">Top Wallet Balances</h3>
          <p className="text-xs text-text-secondary mt-0.5">
            Ranked wallets — week-over-week changes available from next run
          </p>
        </div>
        <DataTable
          columns={walletColumns}
          data={walletRows}
          defaultSort={{ key: 'current_balance_egld', dir: 'desc' }}
          rowClassName={walletRowClass}
          emptyMessage="No wallet data available"
        />
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Large Transactions                                                   */}
      {/* ------------------------------------------------------------------ */}
      <div className="bg-surface rounded-lg border border-border overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <h3 className="text-sm font-semibold text-text-primary">Large Transactions</h3>
          <p className="text-xs text-text-secondary mt-0.5">Transactions &gt; 5,000 EGLD this period</p>
        </div>
        <DataTable
          columns={txColumns}
          data={txRows}
          emptyMessage="No large transactions detected this period"
        />
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Dormant Activations                                                  */}
      {/* ------------------------------------------------------------------ */}
      <div className="bg-surface rounded-lg border border-border overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <h3 className="text-sm font-semibold text-text-primary">Dormant Wallet Activations</h3>
          <p className="text-xs text-text-secondary mt-0.5">Wallets inactive 6+ months that moved funds this week</p>
        </div>
        <div className="p-4">
          {dormant_activations.length === 0 ? (
            <NullState message="No dormant wallets activated this period" />
          ) : (
            <div className="space-y-3">
              {dormant_activations.map((d) => (
                <div
                  key={d.address}
                  className="flex items-start justify-between gap-4 p-3 rounded-lg border border-yellow-500/20 bg-yellow-500/5"
                >
                  <div className="space-y-1 min-w-0">
                    <AddressLink address={d.address} label={d.label} />
                    <div className="flex flex-wrap gap-3 text-xs text-text-secondary">
                      <span>Balance: <span className="font-mono text-text-primary">{formatEgld(d.balance_egld)}</span></span>
                      <span>Last active: <span className="text-text-primary">{formatDate(d.last_active_before)}</span></span>
                    </div>
                    <p className="text-xs text-yellow-400">{d.action}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Analysis                                                             */}
      {/* ------------------------------------------------------------------ */}
      <AnalysisBlock text={analysis} />
    </div>
  )
}
