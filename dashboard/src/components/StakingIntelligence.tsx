import { ResponsiveBar } from '@nivo/bar'
import type {
  StakingIntelligence,
  StakingProvider,
  AprBucket,
  AprOutlier,
} from '../types/report'
import {
  formatEgld,
  formatEgldBare,
  formatNumber,
  formatPct,
  cleanServiceFee,
} from '../lib/formatters'
import { darkTheme, tooltipStyle } from '../lib/nivo-theme'
import { DataTable } from './ui/DataTable'
import { AnalysisBlock } from './ui/AnalysisBlock'
import { MetricCard } from './ui/MetricCard'
import type { Column } from './ui/DataTable'

interface StakingIntelligenceProps {
  data: StakingIntelligence
}

type ProviderRow = Record<string, unknown> & {
  _rank: number
  identity: string
  name?: string | null
  locked_egld: number
  share_pct: number
  num_users: number
  apr_pct: number
  fee_pct: number
  num_nodes?: number | null
  wow_change_egld?: number | null
}

function hhiLabel(hhi: number): { text: string; className: string } {
  if (hhi < 0.15)
    return {
      text: 'Competitive',
      className:
        'bg-up/15 text-up border border-up/30',
    }
  if (hhi <= 0.25)
    return {
      text: 'Moderate',
      className:
        'bg-severity-medium/15 text-severity-medium border border-severity-medium/30',
    }
  return {
    text: 'Concentrated',
    className:
      'bg-severity-critical/15 text-severity-critical border border-severity-critical/30',
  }
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

export function StakingIntelligence({ data }: StakingIntelligenceProps) {
  const {
    summary,
    top_providers,
    concentration,
    apr_distribution,
    apr_outliers,
    churn,
    analysis,
  } = data

  const sortedProviders = [...top_providers].sort(
    (a, b) => b.locked_egld - a.locked_egld,
  )

  const tableRows: ProviderRow[] = sortedProviders.map((p, i) => ({
    _rank: i + 1,
    identity: p.identity,
    name: p.name ?? p.identity,
    locked_egld: p.locked_egld,
    share_pct: p.share_pct,
    num_users: p.num_users,
    apr_pct: p.apr_pct,
    fee_pct: p.fee_pct,
    num_nodes: p.num_nodes,
    wow_change_egld: p.wow_change_egld,
  }))

  const columns: Column<ProviderRow>[] = [
    {
      key: '_rank',
      label: '#',
      render: (v) => (
        <span className="text-text-muted font-mono text-[11px]">{v as number}</span>
      ),
    },
    {
      key: 'name',
      label: 'Provider',
    },
    {
      key: 'locked_egld',
      label: 'Locked',
      align: 'right',
      sortable: true,
      render: (v) => (
        <span className="tabular text-text-primary">
          {formatEgldBare(v as number)}
        </span>
      ),
    },
    {
      key: 'wow_change_egld',
      label: 'Δ WoW',
      align: 'right',
      sortable: true,
      render: (v) => {
        if (v == null) return <span className="text-text-muted">—</span>
        const n = v as number
        const cls = n > 0 ? 'text-up' : n < 0 ? 'text-down' : 'text-flat'
        return (
          <span className={`${cls} tabular`}>
            {n >= 0 ? '+' : ''}
            {formatEgldBare(Math.abs(n))}
          </span>
        )
      },
    },
    {
      key: 'share_pct',
      label: 'Share',
      align: 'right',
      sortable: true,
      render: (v) => (
        <span className="tabular text-text-secondary">
          {(v as number).toFixed(2)}%
        </span>
      ),
    },
    {
      key: 'num_users',
      label: 'Delegators',
      align: 'right',
      sortable: true,
      render: (v) => (
        <span className="tabular text-text-secondary">
          {formatNumber(v as number)}
        </span>
      ),
    },
    {
      key: 'apr_pct',
      label: 'APR',
      align: 'right',
      sortable: true,
      render: (v) => (
        <span className="tabular text-up">{cleanServiceFee(v as number)}</span>
      ),
    },
    {
      key: 'fee_pct',
      label: 'Fee',
      align: 'right',
      sortable: true,
      render: (v) => (
        <span className="tabular text-text-secondary">
          {cleanServiceFee(v as number)}
        </span>
      ),
    },
    {
      key: 'num_nodes',
      label: 'Nodes',
      align: 'right',
      sortable: true,
      render: (v) =>
        v != null ? (
          <span className="tabular text-text-muted">{v as number}</span>
        ) : (
          <span className="text-text-muted">—</span>
        ),
    },
  ]

  // Bar chart: top 15 providers
  const top15 = sortedProviders.slice(0, 15)
  const barData = [...top15].reverse().map((p) => ({
    name: p.name ?? p.identity,
    locked_egld: p.locked_egld,
  }))

  const hhi = concentration.hhi
  const prevHhi = concentration.hhi_previous
  const hhiBadge = hhi !== null ? hhiLabel(hhi) : null

  // APR histogram data
  const aprHistData = apr_distribution
    ? apr_distribution.buckets.map((b: AprBucket) => ({
        bucket: b.label,
        provider_count: b.provider_count,
        total_locked_egld: b.total_locked_egld,
      }))
    : []

  return (
    <div className="space-y-4">
      {/* ---------------- Summary metric strip ---------------- */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          <MetricCard
            accent
            label="Total Staked"
            value={formatEgldBare(summary.total_staked_egld)}
            unit="EGLD"
          />
          {summary.total_delegated_egld != null && (
            <MetricCard
              label="Via Delegation"
              value={formatEgldBare(summary.total_delegated_egld)}
              unit="EGLD"
            />
          )}
          <MetricCard
            label="Staked Ratio"
            value={formatPct(summary.staked_ratio, true)}
          />
          <MetricCard
            label="Providers"
            value={String(summary.num_providers)}
          />
          {summary.apr_weighted_avg != null && (
            <MetricCard
              label="Avg APR"
              value={`${summary.apr_weighted_avg.toFixed(2)}%`}
            />
          )}
          {summary.apr_min != null && summary.apr_max != null && (
            <MetricCard
              label="APR Range"
              value={`${summary.apr_min.toFixed(1)} – ${summary.apr_max.toFixed(1)}%`}
            />
          )}
        </div>
      )}

      {/* ---------------- Concentration + Churn side-by-side ---------------- */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <CardSection title="Stake Concentration">
          <div className="p-4 space-y-3">
            <ProgressRow
              label="Top 5 Share"
              value={concentration.top_5_share_pct}
            />
            <ProgressRow
              label="Top 10 Share"
              value={concentration.top_10_share_pct}
            />

            <div className="flex items-center gap-3 flex-wrap pt-2 border-t border-border-subtle">
              <span className="eyebrow">HHI Index</span>
              {hhi !== null ? (
                <>
                  <span className="font-mono text-[14px] text-text-primary tabular">
                    {hhi.toFixed(4)}
                  </span>
                  {hhiBadge && (
                    <span
                      className={`inline-flex items-center px-1.5 py-[1px] rounded text-[10px] font-mono font-semibold tracking-wider ${hhiBadge.className}`}
                    >
                      {hhiBadge.text.toUpperCase()}
                    </span>
                  )}
                  {prevHhi != null && (
                    <span className="text-[11px] font-mono text-text-muted">
                      {hhi < prevHhi ? (
                        <span className="text-up">▼ improving</span>
                      ) : hhi > prevHhi ? (
                        <span className="text-down">▲ concentrating</span>
                      ) : (
                        <span>— unchanged</span>
                      )}
                    </span>
                  )}
                </>
              ) : (
                <span className="text-text-muted text-sm">—</span>
              )}
            </div>
          </div>
        </CardSection>

        {/* Churn */}
        <CardSection
          title="Delegator Churn"
          subtitle="WoW change in total delegators across all providers"
        >
          <div className="p-4 space-y-3">
            {churn ? (
              <>
                <div className="flex items-baseline gap-2">
                  <span className="hero-number-sm">
                    {formatNumber(churn.total_delegators_current)}
                  </span>
                  <span className="hero-unit">delegators</span>
                </div>
                {churn.delegators_added != null && (
                  <div className="flex items-baseline gap-3 text-[12px] font-mono">
                    <span
                      className={
                        churn.delegators_added > 0
                          ? 'text-up'
                          : churn.delegators_added < 0
                            ? 'text-down'
                            : 'text-flat'
                      }
                    >
                      {churn.delegators_added > 0 ? '▲ +' : churn.delegators_added < 0 ? '▼ ' : ''}
                      {formatNumber(churn.delegators_added)}
                    </span>
                    {churn.delegators_change_pct != null && (
                      <span className="text-text-muted">
                        ({churn.delegators_change_pct > 0 ? '+' : ''}
                        {churn.delegators_change_pct.toFixed(2)}% WoW)
                      </span>
                    )}
                  </div>
                )}
                <div className="grid grid-cols-2 gap-3 pt-2 border-t border-border-subtle">
                  <div>
                    <span className="eyebrow">Gaining</span>
                    <p className="font-mono text-[14px] text-up tabular">
                      {churn.providers_gaining_delegators ?? '—'}
                    </p>
                  </div>
                  <div>
                    <span className="eyebrow">Losing</span>
                    <p className="font-mono text-[14px] text-down tabular">
                      {churn.providers_losing_delegators ?? '—'}
                    </p>
                  </div>
                </div>
              </>
            ) : (
              <p className="text-[12px] text-text-muted italic">
                Churn metric introduced in v2 — appears in next run
              </p>
            )}
          </div>
        </CardSection>
      </div>

      {/* ---------------- APR Distribution Histogram (NEW) ---------------- */}
      {apr_distribution && aprHistData.length > 0 && (
        <CardSection
          title="APR Distribution Histogram"
          subtitle="How providers are spread across APR buckets — tight cluster = competitive equilibrium"
        >
          <div className="p-4">
            <div style={{ height: 280 }}>
              <ResponsiveBar
                data={aprHistData}
                keys={['provider_count']}
                indexBy="bucket"
                layout="vertical"
                theme={darkTheme}
                colors={['#23F7DD']}
                margin={{ top: 12, right: 20, bottom: 50, left: 50 }}
                padding={0.35}
                axisBottom={{
                  legend: 'APR Bucket',
                  legendPosition: 'middle',
                  legendOffset: 38,
                  tickSize: 0,
                  tickPadding: 8,
                }}
                axisLeft={{
                  legend: 'Provider Count',
                  legendPosition: 'middle',
                  legendOffset: -38,
                  tickSize: 0,
                  tickPadding: 6,
                }}
                enableGridY={true}
                enableGridX={false}
                labelTextColor="#0A0D14"
                labelSkipHeight={16}
                tooltip={({ indexValue, value, data: dat }) => (
                  <div style={tooltipStyle}>
                    <strong>{indexValue} APR</strong>
                    <br />
                    Providers: {value}
                    <br />
                    Locked:{' '}
                    {formatEgld(dat.total_locked_egld as number)}
                  </div>
                )}
              />
            </div>
          </div>
        </CardSection>
      )}

      {/* ---------------- APR Outliers (NEW) ---------------- */}
      {apr_outliers && (apr_outliers.top_apr.length > 0 || apr_outliers.lowest_fee.length > 0) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <CardSection title="Top 5 by APR" subtitle="Highest yield providers">
            <OutlierTable items={apr_outliers.top_apr} highlight="apr_pct" />
          </CardSection>
          <CardSection title="Top 5 by Lowest Fee" subtitle="Best delegator-share providers">
            <OutlierTable items={apr_outliers.lowest_fee} highlight="fee_pct" />
          </CardSection>
        </div>
      )}

      {/* ---------------- Provider leaderboard ---------------- */}
      <CardSection title="Provider Leaderboard" subtitle="Top providers by stake">
        <DataTable
          columns={columns}
          data={tableRows}
          defaultSort={{ key: 'locked_egld', dir: 'desc' }}
          collapsed={5}
          noun="provider"
          rowClassName={(row: ProviderRow) => {
            const r = row as unknown as StakingProvider
            return r.apr_pct > 8.5 && r.fee_pct < 5 ? 'bg-up/5' : ''
          }}
        />
      </CardSection>

      {/* ---------------- Provider distribution chart ---------------- */}
      <CardSection title="Top 15 Providers by Locked EGLD">
        <div className="p-4" style={{ height: 420 }}>
          <ResponsiveBar
            data={barData}
            keys={['locked_egld']}
            indexBy="name"
            layout="horizontal"
            theme={darkTheme}
            colors={['#23F7DD']}
            margin={{ top: 8, right: 80, bottom: 36, left: 160 }}
            padding={0.35}
            valueFormat={(v) => formatEgldBare(v)}
            axisBottom={{
              legend: 'EGLD Locked',
              legendPosition: 'middle',
              legendOffset: 28,
              format: (v) => formatEgldBare(v as number),
              tickSize: 0,
              tickPadding: 6,
            }}
            axisLeft={{ tickSize: 0, tickPadding: 8 }}
            enableGridX={true}
            enableGridY={false}
            labelTextColor="#0A0D14"
            labelSkipWidth={50}
            tooltip={({ indexValue, value }) => (
              <div style={tooltipStyle}>
                <strong>{indexValue}</strong>
                <br />
                {formatEgld(value)}
              </div>
            )}
          />
        </div>
      </CardSection>

      <AnalysisBlock label="Staking Intelligence" text={analysis} />
    </div>
  )
}

function ProgressRow({ label, value }: { label: string; value: number }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[11px]">
        <span className="text-text-muted uppercase tracking-wider">{label}</span>
        <span className="font-mono text-text-primary tabular">{value.toFixed(2)}%</span>
      </div>
      <div
        className="h-1.5 rounded-full overflow-hidden"
        style={{ background: '#1F273A' }}
      >
        <div
          className="h-full rounded-full"
          style={{
            width: `${Math.min(value, 100)}%`,
            background: 'linear-gradient(90deg, #23F7DD, #18B5A2)',
          }}
        />
      </div>
    </div>
  )
}

function OutlierTable({
  items,
  highlight,
}: {
  items: AprOutlier[]
  highlight: 'apr_pct' | 'fee_pct'
}) {
  return (
    <table className="terminal-table">
      <thead>
        <tr>
          <th className="text-left">Provider</th>
          <th className="text-right">APR</th>
          <th className="text-right">Fee</th>
          <th className="text-right">Locked</th>
        </tr>
      </thead>
      <tbody>
        {items.map((o) => (
          <tr key={o.identity}>
            <td className="font-medium">{o.name ?? o.identity}</td>
            <td
              className={`text-right tabular ${highlight === 'apr_pct' ? 'text-up font-semibold' : 'text-text-secondary'}`}
            >
              {o.apr_pct.toFixed(2)}%
            </td>
            <td
              className={`text-right tabular ${highlight === 'fee_pct' ? 'text-accent-cyan font-semibold' : 'text-text-secondary'}`}
            >
              {o.fee_pct.toFixed(1)}%
            </td>
            <td className="text-right tabular text-text-muted">
              {formatEgldBare(o.locked_egld)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
