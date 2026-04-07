import { ResponsivePie } from '@nivo/pie'
import type { NetworkHealth } from '../types/report'
import { formatEgld, formatUsd, formatPct, formatNumber } from '../lib/formatters'
import { darkTheme } from '../lib/nivo-theme'
import { MetricCard } from './ui/MetricCard'
import { AnalysisBlock } from './ui/AnalysisBlock'

interface NetworkHealthProps {
  data: NetworkHealth
}

export function NetworkHealth({ data }: NetworkHealthProps) {
  const { economics, activity, deltas, analysis } = data

  const pieData = [
    {
      id: 'Staked',
      value: economics.staked_ratio,
      label: 'Staked',
    },
    {
      id: 'Circulating',
      value: 1 - economics.staked_ratio,
      label: 'Circulating',
    },
  ]

  const stakedEgld = economics.staked_egld
  const unstakedEgld = economics.total_supply - economics.staked_egld

  return (
    <div className="space-y-6">
      {/* Metrics grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <MetricCard
          label="EGLD Price"
          value={formatUsd(economics.egld_price_usd)}
          delta={deltas.price_change_pct}
          deltaFormat="pct"
        />
        <MetricCard
          label="Market Cap"
          value={formatUsd(economics.market_cap_usd)}
          delta={deltas.market_cap_change_pct}
          deltaFormat="pct"
        />
        <MetricCard
          label="Staked Ratio"
          value={formatPct(economics.staked_ratio, true)}
          delta={deltas.staked_ratio_change_pp}
          deltaFormat="pct"
        />
        <MetricCard
          label="Staking APR"
          value={formatPct(economics.staking_apr, true)}
          delta={deltas.apr_change_pp}
          deltaFormat="pct"
        />
        <MetricCard
          label="Total Accounts"
          value={formatNumber(activity.total_accounts)}
          delta={deltas.accounts_added}
          deltaFormat="number"
        />
        <MetricCard
          label="Total Transactions"
          value={formatNumber(activity.total_transactions)}
          delta={deltas.transactions_added}
          deltaFormat="number"
        />
      </div>

      {/* Secondary info row */}
      <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm text-text-secondary">
        <span>Supply: {formatNumber(economics.total_supply)} EGLD</span>
        <span>Circulating: {formatNumber(economics.circulating_supply)} EGLD</span>
        <span>Staked: {formatEgld(economics.staked_egld)}</span>
        <span>Token MCap: {formatUsd(economics.token_market_cap_usd)}</span>
        <span>Epoch: {activity.epoch}</span>
        <span>Shards: {activity.shards}</span>
      </div>

      {/* Staked ratio donut chart */}
      <div className="bg-surface rounded-lg border border-border p-4">
        <p className="text-sm font-medium text-text-secondary mb-3">Staked vs Unstaked Supply</p>
        <div style={{ height: 200 }}>
          <ResponsivePie
            data={pieData}
            theme={darkTheme}
            colors={['#23F7DD', '#2A3144']}
            innerRadius={0.6}
            cornerRadius={3}
            padAngle={2}
            arcLinkLabelsSkipAngle={360}
            arcLabel={(d) => `${(d.value * 100).toFixed(1)}%`}
            arcLabelsTextColor="#0D1117"
            arcLabelsSkipAngle={10}
            tooltip={({ datum }) => {
              const egldAmount = datum.id === 'Staked' ? stakedEgld : unstakedEgld
              return (
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
                  <strong>{datum.label}</strong>
                  <br />
                  {formatEgld(egldAmount)}
                  <br />
                  {(datum.value * 100).toFixed(2)}%
                </div>
              )
            }}
            legends={[
              {
                anchor: 'right',
                direction: 'column',
                justify: false,
                translateX: 80,
                translateY: 0,
                itemsSpacing: 8,
                itemWidth: 80,
                itemHeight: 18,
                itemTextColor: '#94A3B8',
                symbolSize: 10,
                symbolShape: 'circle',
              },
            ]}
            margin={{ top: 10, right: 100, bottom: 10, left: 10 }}
          />
        </div>
      </div>

      {/* Analysis */}
      <AnalysisBlock text={analysis} />
    </div>
  )
}
