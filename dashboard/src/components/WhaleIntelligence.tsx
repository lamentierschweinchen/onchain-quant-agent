import { ResponsiveBar } from '@nivo/bar'
import type {
  WhaleIntelligence,
  WalletChange,
  LargeTransaction,
  WhaleTierStats,
  EntityNettingEntry,
  DormantActivation,
} from '../types/report'
import {
  formatEgld,
  formatEgldBare,
  formatUsd,
  formatPct,
  formatTimestamp,
  formatDate,
  formatNumber,
} from '../lib/formatters'
import { darkTheme, tooltipStyle } from '../lib/nivo-theme'
import {
  txUrl,
  CATEGORY_COLORS,
  TIER_COLORS,
  TIER_LABELS,
  TIER_DESCRIPTIONS,
} from '../lib/constants'
import { DataTable } from './ui/DataTable'
import { AddressLink } from './ui/AddressLink'
import { AnalysisBlock } from './ui/AnalysisBlock'
import { NullState } from './ui/NullState'
import type { Column } from './ui/DataTable'

interface WhaleIntelligenceProps {
  data: WhaleIntelligence
}

type WalletRow = Record<string, unknown> & WalletChange
type TxRow = Record<string, unknown> & LargeTransaction

function categoryColor(category: string | null): string {
  if (!category) return CATEGORY_COLORS.other
  const key = category as keyof typeof CATEGORY_COLORS
  return CATEGORY_COLORS[key] ?? CATEGORY_COLORS.other
}

function CategoryBadge({ category }: { category: string | null }) {
  const label = category ?? 'unknown'
  const color = categoryColor(category)
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

function TierBadge({ tier }: { tier: string | null | undefined }) {
  if (!tier || !(tier in TIER_COLORS)) return null
  const color = TIER_COLORS[tier as keyof typeof TIER_COLORS]
  const label = TIER_LABELS[tier as keyof typeof TIER_LABELS]
  return (
    <span
      className="tier-badge"
      style={{
        color,
        backgroundColor: `${color}1A`,
        border: `1px solid ${color}33`,
      }}
    >
      {label}
    </span>
  )
}

function FlowTypeBadge({ flowType }: { flowType: string }) {
  const isInflow = flowType.includes('inflow') || flowType === 'staking'
  const isOutflow = flowType.includes('outflow') || flowType === 'unstaking'
  let color = '#6B7587'
  if (isInflow) color = '#F4525A'
  if (isOutflow) color = '#34D196'
  const label = flowType.replace(/_/g, ' ')
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

function CardSection({
  title,
  subtitle,
  children,
  toolbar,
}: {
  title: string
  subtitle?: string
  children: React.ReactNode
  toolbar?: React.ReactNode
}) {
  return (
    <section className="card overflow-hidden">
      <header className="flex items-center justify-between px-4 py-2.5 border-b border-border bg-bg-elevated">
        <div>
          <h3 className="text-[12px] font-semibold text-text-primary tracking-tight">
            {title}
          </h3>
          {subtitle && (
            <p className="text-[10px] text-text-muted mt-0.5">{subtitle}</p>
          )}
        </div>
        {toolbar && <div className="flex items-center gap-2">{toolbar}</div>}
      </header>
      {children}
    </section>
  )
}

function TierCard({
  tierKey,
  data,
}: {
  tierKey: 'mega_whale' | 'large_whale' | 'mid_whale'
  data: WhaleTierStats
}) {
  const color = TIER_COLORS[tierKey]
  const label = TIER_LABELS[tierKey]
  const desc = TIER_DESCRIPTIONS[tierKey]
  const change = data.net_change_egld
  const changePct = data.net_change_pct

  return (
    <div className="card p-4 relative">
      <span
        className="absolute left-0 top-3 bottom-3 w-[3px] rounded"
        style={{ backgroundColor: color }}
      />
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-baseline gap-2">
          <span
            className="text-[11px] font-mono font-bold tracking-wider"
            style={{ color }}
          >
            {label}
          </span>
          <span className="text-[10px] text-text-muted font-mono">
            {desc}
          </span>
        </div>
        <span className="text-[10px] text-text-muted font-mono uppercase tracking-wider">
          {data.count_current} wallets
          {data.count_previous != null &&
            data.count_previous !== data.count_current && (
              <span className="ml-1 text-text-faint">
                ({data.count_current - data.count_previous >= 0 ? '+' : ''}
                {data.count_current - data.count_previous})
              </span>
            )}
        </span>
      </div>
      <div className="flex items-baseline gap-1.5 mb-1">
        <span className="hero-number-sm">
          {formatEgldBare(data.total_balance_egld)}
        </span>
        <span className="hero-unit">EGLD</span>
      </div>
      {change != null ? (
        <div className="flex items-baseline gap-2 text-[11px] font-mono">
          <span className={change > 0 ? 'text-up' : change < 0 ? 'text-down' : 'text-flat'}>
            {change > 0 ? '▲' : change < 0 ? '▼' : '—'}{' '}
            {change > 0 ? '+' : ''}{formatEgldBare(change)}
          </span>
          {changePct != null && (
            <span className="text-text-muted">
              {changePct > 0 ? '+' : ''}{changePct.toFixed(2)}% WoW
            </span>
          )}
        </div>
      ) : (
        <span className="text-[10px] text-text-muted">Baseline tier — WoW available next run</span>
      )}
    </div>
  )
}

export function WhaleIntelligence({ data }: WhaleIntelligenceProps) {
  const {
    exchange_flows,
    wallet_changes,
    whale_tiers,
    large_transactions,
    dormant_activations = [],
    analysis,
  } = data

  // -------------------------------------------------------------------------
  // Exchange flows
  // -------------------------------------------------------------------------
  const allFlowsNull = exchange_flows.by_exchange.every(
    (e) => e.change_egld === null,
  )

  const exchangeMap = new Map<string, number>()
  if (!allFlowsNull) {
    for (const entry of exchange_flows.by_exchange) {
      if (entry.change_egld !== null) {
        exchangeMap.set(
          entry.exchange,
          (exchangeMap.get(entry.exchange) ?? 0) + entry.change_egld,
        )
      }
    }
  }

  // Negate raw values so:
  //   outflow (originally negative, EGLD leaving exchange = accumulation)  → positive  → renders RIGHT
  //   inflow  (originally positive, EGLD entering exchange = sell pressure) → negative → renders LEFT
  // Filter out wallets with no change (or near-zero) — they're noise on this chart.
  const NOISE_THRESHOLD = 100 // EGLD
  const flowEntries = Array.from(exchangeMap.entries())
    .filter(([, v]) => Math.abs(v) >= NOISE_THRESHOLD)
    .map(([exchange, raw]) => ({
      exchange,
      flow: -raw, // sign flip
      raw,
    }))
    // Most positive (= biggest outflow / accumulation) at top
    .sort((a, b) => b.flow - a.flow)
    // Nivo horizontal bar renders index 0 at the BOTTOM, so reverse for top-down listing
    .reverse()

  // Symmetric x-axis around zero
  const maxAbs =
    flowEntries.length > 0
      ? Math.max(...flowEntries.map((d) => Math.abs(d.flow))) * 1.1
      : 0

  // Aggregate totals (in original sign convention)
  const totalInflow = exchange_flows.by_exchange
    .filter((e) => e.change_egld !== null && e.change_egld > 0)
    .reduce((s, e) => s + (e.change_egld ?? 0), 0)
  const totalOutflow = exchange_flows.by_exchange
    .filter((e) => e.change_egld !== null && e.change_egld < 0)
    .reduce((s, e) => s + Math.abs(e.change_egld ?? 0), 0)
  const totalAbs = totalInflow + totalOutflow

  const netFlow = exchange_flows.net_change_egld
  const netFlowPositive = netFlow !== null && netFlow > 0

  // -------------------------------------------------------------------------
  // Wallet changes table
  // -------------------------------------------------------------------------
  const walletColumns: Column<WalletRow>[] = [
    {
      key: 'tier',
      label: 'Tier',
      render: (_v, row) => <TierBadge tier={row.tier as string | null | undefined} />,
    },
    {
      key: 'address',
      label: 'Address',
      render: (_v, row) => (
        <AddressLink
          address={row.address as string}
          label={row.label as string | null}
        />
      ),
    },
    {
      key: 'category',
      label: 'Category',
      render: (_v, row) => (
        <CategoryBadge category={row.category as string | null} />
      ),
    },
    {
      key: 'balance_current_egld',
      label: 'Balance',
      align: 'right',
      sortable: true,
      render: (v) => (
        <span className="tabular">{formatEgldBare(v as number)}</span>
      ),
    },
    {
      key: 'change_egld',
      label: 'Δ EGLD',
      align: 'right',
      sortable: true,
      render: (v) => {
        if (v == null) return <span className="text-text-muted">—</span>
        const n = v as number
        const cls = n > 0 ? 'text-up' : n < 0 ? 'text-down' : 'text-flat'
        return (
          <span className={`${cls} tabular`}>
            {n >= 0 ? '+' : ''}
            {formatEgldBare(Math.abs(n)) === '0' && n !== 0 ? formatEgldBare(n) : (n >= 0 ? formatEgldBare(n) : `-${formatEgldBare(-n)}`)}
          </span>
        )
      },
    },
    {
      key: 'change_pct',
      label: 'Δ %',
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
  ]

  const walletRows: WalletRow[] = wallet_changes.map(
    (w) => ({ ...w }) as WalletRow,
  )

  // -------------------------------------------------------------------------
  // Large transactions table
  // -------------------------------------------------------------------------
  const txColumns: Column<TxRow>[] = [
    {
      key: 'timestamp',
      label: 'Time',
      render: (v) => (
        <span className="text-text-muted text-[11px] font-mono">
          {formatTimestamp(v as string)}
        </span>
      ),
    },
    {
      key: 'sender',
      label: 'From',
      render: (_v, row) => (
        <AddressLink
          address={row.sender as string}
          label={row.sender_label as string | null}
        />
      ),
    },
    {
      key: 'receiver',
      label: 'To',
      render: (_v, row) => (
        <AddressLink
          address={row.receiver as string}
          label={row.receiver_label as string | null}
        />
      ),
    },
    {
      key: 'value_egld',
      label: 'Value',
      align: 'right',
      sortable: true,
      render: (v) => (
        <span className="tabular text-text-primary">
          {formatEgldBare(v as number)}
        </span>
      ),
    },
    {
      key: 'value_usd',
      label: 'USD',
      align: 'right',
      sortable: true,
      render: (v) => (
        <span className="tabular text-text-secondary">
          {formatUsd(v as number)}
        </span>
      ),
    },
    {
      key: 'flow_type',
      label: 'Flow',
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
          className="font-mono text-[11px] text-accent-cyan hover:underline"
        >
          {(v as string).slice(0, 8)}…
        </a>
      ),
    },
  ]

  const txRows: TxRow[] = large_transactions.map((t) => ({ ...t }) as TxRow)

  return (
    <div className="space-y-4">
      {/* ---------------- Whale Tier Stratification (NEW) ---------------- */}
      {whale_tiers && (whale_tiers.mega_whales || whale_tiers.large_whales || whale_tiers.mid_whales) && (
        <CardSection
          title="Whale Tier Stratification"
          subtitle="Aggregate movement of each tier reveals wealth distribution dynamics"
        >
          <div className="p-4 grid grid-cols-1 md:grid-cols-3 gap-3">
            {whale_tiers.mega_whales && (
              <TierCard tierKey="mega_whale" data={whale_tiers.mega_whales} />
            )}
            {whale_tiers.large_whales && (
              <TierCard tierKey="large_whale" data={whale_tiers.large_whales} />
            )}
            {whale_tiers.mid_whales && (
              <TierCard tierKey="mid_whale" data={whale_tiers.mid_whales} />
            )}
          </div>
        </CardSection>
      )}

      {/* ---------------- Exchange Flows ---------------- */}
      <CardSection
        title="Exchange Flows"
        subtitle="Net EGLD movement across known exchange wallets"
      >
        <div className="p-4">
          {allFlowsNull ? (
            <NullState message="Baseline — exchange flow tracking starts next week" />
          ) : (
            <div className="space-y-4">
              {netFlow !== null && (
                <div className="flex items-baseline gap-3 pb-3 border-b border-border-subtle">
                  <div className="flex flex-col gap-0.5">
                    <span className="eyebrow">Net Flow</span>
                    <span
                      className={`hero-number ${netFlowPositive ? 'text-down' : 'text-up'}`}
                    >
                      {netFlowPositive ? '▲' : '▼'} {formatEgldBare(Math.abs(netFlow))}
                    </span>
                    <span className="text-[11px] text-text-muted">
                      {netFlowPositive
                        ? 'net inflow → sell pressure'
                        : 'net outflow → accumulation'}
                    </span>
                  </div>
                  {exchange_flows.signal && (
                    <div className="ml-auto text-right">
                      <span className="eyebrow">Signal</span>
                      <p className="text-[12px] text-text-primary font-mono mt-0.5">
                        {exchange_flows.signal.replace(/_/g, ' ')}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Direction legend */}
              <div className="flex items-center justify-between text-[10px] font-mono uppercase tracking-wider px-2">
                <span className="flex items-center gap-1.5 text-down">
                  <span>← inflow</span>
                  <span className="text-text-muted normal-case tracking-normal">
                    sell pressure
                  </span>
                </span>
                <span className="text-text-muted">net flow per wallet</span>
                <span className="flex items-center gap-1.5 text-up">
                  <span className="text-text-muted normal-case tracking-normal">
                    accumulation
                  </span>
                  <span>outflow →</span>
                </span>
              </div>

              <div style={{ height: 32 + 28 * flowEntries.length }}>
                <ResponsiveBar
                  data={flowEntries}
                  keys={['flow']}
                  indexBy="exchange"
                  layout="horizontal"
                  theme={darkTheme}
                  colors={({ value }) =>
                    (value as number) >= 0 ? '#34D196' : '#F4525A'
                  }
                  valueScale={{ type: 'linear', min: -maxAbs, max: maxAbs }}
                  margin={{ top: 4, right: 24, bottom: 32, left: 24 }}
                  padding={0.32}
                  valueFormat={(v) => formatEgldBare(Math.abs(v))}
                  axisBottom={{
                    format: (v) => formatEgldBare(Math.abs(v as number)),
                    tickSize: 0,
                    tickPadding: 6,
                    tickValues: 5,
                  }}
                  axisLeft={null}
                  enableGridX={true}
                  enableGridY={false}
                  gridXValues={[0]}
                  enableLabel={false}
                  markers={[
                    {
                      axis: 'x',
                      value: 0,
                      lineStyle: {
                        stroke: '#5C6679',
                        strokeWidth: 1,
                      },
                    },
                  ]}
                  layers={[
                    'grid',
                    'axes',
                    'bars',
                    // Custom layer: render labels INSIDE the chart so the
                    // exchange name sits at the zero line, on the side
                    // opposite the bar (so it never overlaps the bar)
                    ({ bars }) => (
                      <g>
                        {bars.map((bar) => {
                          const v = bar.data.value as number
                          const goesRight = v >= 0
                          const exchange = bar.data.indexValue as string
                          return (
                            <g key={bar.key}>
                              {/* Exchange name + value, anchored at the zero line */}
                              <text
                                x={
                                  goesRight
                                    ? bar.x - 6
                                    : bar.x + bar.width + 6
                                }
                                y={bar.y + bar.height / 2}
                                textAnchor={goesRight ? 'end' : 'start'}
                                dominantBaseline="central"
                                style={{
                                  fontSize: 11,
                                  fill: '#8B97AC',
                                  fontFamily:
                                    '"Inter", system-ui, sans-serif',
                                }}
                              >
                                {exchange}
                              </text>
                              {/* Value label at the far end of the bar */}
                              <text
                                x={
                                  goesRight
                                    ? bar.x + bar.width + 6
                                    : bar.x - 6
                                }
                                y={bar.y + bar.height / 2}
                                textAnchor={goesRight ? 'start' : 'end'}
                                dominantBaseline="central"
                                style={{
                                  fontSize: 11,
                                  fill: goesRight ? '#34D196' : '#F4525A',
                                  fontFamily:
                                    '"JetBrains Mono", ui-monospace, monospace',
                                  fontVariantNumeric: 'tabular-nums',
                                }}
                              >
                                {goesRight ? '+' : '−'}
                                {formatEgldBare(Math.abs(v))}
                              </text>
                            </g>
                          )
                        })}
                      </g>
                    ),
                    'markers',
                  ]}
                  tooltip={({ indexValue, value }) => {
                    const v = value as number
                    return (
                      <div style={tooltipStyle}>
                        <strong>{indexValue}</strong>
                        <br />
                        {v >= 0 ? 'Outflow' : 'Inflow'}:{' '}
                        {formatEgld(Math.abs(v))}
                      </div>
                    )
                  }}
                />
              </div>

              {/* Aggregate inflow vs outflow proportion bar */}
              {totalAbs > 0 && (
                <div className="space-y-1.5 pt-3 border-t border-border-subtle">
                  <div className="flex justify-between text-[10px] font-mono uppercase tracking-wider text-text-muted">
                    <span>
                      Total inflow{' '}
                      <span className="text-down tabular">
                        {formatEgldBare(totalInflow)}
                      </span>
                    </span>
                    <span>
                      <span className="text-up tabular">
                        {formatEgldBare(totalOutflow)}
                      </span>{' '}
                      Total outflow
                    </span>
                  </div>
                  <div className="flex h-2 rounded-sm overflow-hidden bg-bg-elevated">
                    {totalInflow > 0 && (
                      <div
                        className="bg-down/80"
                        style={{
                          flex: totalInflow,
                        }}
                        title={`Inflow ${formatEgldBare(totalInflow)} EGLD`}
                      />
                    )}
                    {totalOutflow > 0 && (
                      <div
                        className="bg-up/80"
                        style={{
                          flex: totalOutflow,
                        }}
                        title={`Outflow ${formatEgldBare(totalOutflow)} EGLD`}
                      />
                    )}
                  </div>
                  <div className="flex justify-between text-[10px] text-text-faint font-mono">
                    <span>
                      {((totalInflow / totalAbs) * 100).toFixed(1)}%
                    </span>
                    <span>
                      {((totalOutflow / totalAbs) * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </CardSection>

      {/* ---------------- Entity-Netted Flows (NEW) ---------------- */}
      {exchange_flows.entity_netting && exchange_flows.entity_netting.length > 0 && (
        <CardSection
          title="Entity-Netted Flows"
          subtitle="Multiple wallets per parent entity collapsed into one figure"
        >
          <div className="p-0">
            <table className="terminal-table">
              <thead>
                <tr>
                  <th className="text-left">Entity</th>
                  <th className="text-right">Net Flow</th>
                  <th className="text-right">Wallets</th>
                  <th className="text-left">Interpretation</th>
                </tr>
              </thead>
              <tbody>
                {exchange_flows.entity_netting
                  .sort((a, b) => Math.abs(b.net_flow_egld) - Math.abs(a.net_flow_egld))
                  .map((e: EntityNettingEntry) => {
                    const cls =
                      e.net_flow_egld > 0
                        ? 'text-down'
                        : e.net_flow_egld < 0
                          ? 'text-up'
                          : 'text-flat'
                    return (
                      <tr key={e.entity}>
                        <td className="font-medium">{e.entity}</td>
                        <td className={`text-right tabular ${cls}`}>
                          {e.net_flow_egld >= 0 ? '+' : ''}
                          {formatEgldBare(e.net_flow_egld)}
                        </td>
                        <td className="text-right tabular text-text-muted">
                          {e.wallets_count}
                        </td>
                        <td className="text-text-secondary text-[11.5px]">
                          {e.interpretation ?? '—'}
                        </td>
                      </tr>
                    )
                  })}
              </tbody>
            </table>
          </div>
        </CardSection>
      )}

      {/* ---------------- Wallet Changes ---------------- */}
      <CardSection
        title="Top Wallet Balances"
        subtitle="WoW changes by tier — sortable"
      >
        <DataTable
          columns={walletColumns}
          data={walletRows}
          defaultSort={{ key: 'balance_current_egld', dir: 'desc' }}
          emptyMessage="No wallet data available"
        />
      </CardSection>

      {/* ---------------- Large Transactions ---------------- */}
      <CardSection
        title="Large Transactions"
        subtitle="Transactions > 1,000 EGLD this period"
      >
        <DataTable
          columns={txColumns}
          data={txRows}
          emptyMessage="No large transactions detected this period"
        />
      </CardSection>

      {/* ---------------- Dormant Activations ---------------- */}
      <CardSection
        title="Dormant Wallet Activations"
        subtitle="Wallets inactive 6+ months that moved this week"
      >
        <div className="p-4">
          {dormant_activations.length === 0 ? (
            <NullState message="No dormant wallets activated this period" />
          ) : (
            <div className="space-y-2">
              {dormant_activations.map((d: DormantActivation) => (
                <div
                  key={d.address}
                  className="flex items-start justify-between gap-4 p-3 rounded border border-severity-medium/30 bg-severity-medium/5"
                >
                  <div className="space-y-1.5 min-w-0 flex-1">
                    <AddressLink address={d.address} label={d.label} />
                    <div className="flex flex-wrap gap-4 text-[11px] text-text-muted font-mono">
                      <span>
                        Balance{' '}
                        <span className="text-text-primary">
                          {formatEgldBare(d.balance_egld)} EGLD
                        </span>
                      </span>
                      <span>
                        Last active{' '}
                        <span className="text-text-primary">
                          {formatDate(d.last_active_before)}
                        </span>
                      </span>
                      {d.dormant_days != null && (
                        <span>
                          Dormant{' '}
                          <span className="text-severity-medium">
                            {formatNumber(d.dormant_days)} days
                          </span>
                        </span>
                      )}
                    </div>
                    <p className="text-[12px] text-text-secondary leading-relaxed">
                      {d.action}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </CardSection>

      {/* ---------------- Analysis ---------------- */}
      <AnalysisBlock label="Whale Intelligence" text={analysis} />
    </div>
  )
}
