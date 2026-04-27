import { ResponsivePie } from '@nivo/pie'
import type { NetworkHealth } from '../types/report'
import {
  formatEgld,
  formatEgldBare,
  formatUsd,
  formatPct,
  formatPct2,
  formatNumber,
  formatNumberFull,
} from '../lib/formatters'
import { darkTheme, tooltipStyle } from '../lib/nivo-theme'
import { MetricCard } from './ui/MetricCard'
import { AnalysisBlock } from './ui/AnalysisBlock'

interface NetworkHealthProps {
  data: NetworkHealth
}

export function NetworkHealth({ data }: NetworkHealthProps) {
  const { economics, activity, deltas, analysis } = data

  const pieData = [
    { id: 'Staked', value: economics.staked_ratio, label: 'Staked' },
    { id: 'Circulating', value: 1 - economics.staked_ratio, label: 'Circulating' },
  ]

  const stakedEgld = economics.staked_egld
  const unstakedEgld = economics.total_supply - economics.staked_egld

  return (
    <div className="space-y-4">
      {/* Hero metrics row */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <MetricCard
          accent
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
          deltaFormat="pp"
        />
        <MetricCard
          label="Staking APR"
          value={formatPct(economics.staking_apr, true)}
          delta={deltas.apr_change_pp}
          deltaFormat="pp"
        />
        <MetricCard
          label="Total Accounts"
          value={formatNumber(activity.total_accounts)}
          delta={deltas.accounts_added}
          deltaFormat="number"
        />
        <MetricCard
          label="TX 7d"
          value={
            activity.transactions_7d != null
              ? formatNumber(activity.transactions_7d)
              : formatNumber(activity.total_transactions)
          }
          delta={deltas.transactions_added}
          deltaFormat="number"
        />
      </div>

      {/* Detail panel — economics breakdown + supply pie + activity stats */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Economics detail */}
        <div className="card p-4 lg:col-span-1">
          <p className="eyebrow mb-3">Economics</p>
          <dl className="text-[12px] space-y-2 font-mono">
            <DetailRow label="Total Supply" value={`${formatNumber(economics.total_supply)} EGLD`} />
            <DetailRow
              label="Circulating"
              value={`${formatNumber(economics.circulating_supply)} EGLD`}
            />
            <DetailRow label="Staked" value={formatEgld(economics.staked_egld)} />
            <DetailRow label="Token MCap" value={formatUsd(economics.token_market_cap_usd)} />
            {economics.base_apr != null && (
              <DetailRow
                label="Base APR"
                value={formatPct2(economics.base_apr, true)}
              />
            )}
            {economics.topup_apr != null && (
              <DetailRow
                label="TopUp APR"
                value={formatPct2(economics.topup_apr, true)}
              />
            )}
          </dl>
        </div>

        {/* Staked vs unstaked donut */}
        <div className="card p-4 lg:col-span-1">
          <div className="flex items-center justify-between mb-2">
            <p className="eyebrow">Supply Distribution</p>
            <span className="text-[10px] font-mono text-text-muted tabular">
              {formatPct(economics.staked_ratio, true)} staked
            </span>
          </div>
          <div style={{ height: 180 }}>
            <ResponsivePie
              data={pieData}
              theme={darkTheme}
              colors={['#23F7DD', '#1F273A']}
              innerRadius={0.72}
              cornerRadius={2}
              padAngle={1.5}
              activeOuterRadiusOffset={4}
              borderWidth={0}
              arcLinkLabelsSkipAngle={360}
              arcLabelsSkipAngle={360}
              tooltip={({ datum }) => {
                const egldAmount =
                  datum.id === 'Staked' ? stakedEgld : unstakedEgld
                return (
                  <div style={tooltipStyle}>
                    <strong>{datum.label}</strong>
                    <br />
                    {formatEgld(egldAmount)}
                    <br />
                    {(datum.value * 100).toFixed(2)}%
                  </div>
                )
              }}
              margin={{ top: 8, right: 8, bottom: 8, left: 8 }}
            />
          </div>
          <div className="flex justify-around text-[11px] mt-1">
            <div className="text-center">
              <div className="flex items-center gap-1.5 justify-center">
                <span className="w-2 h-2 rounded-sm bg-accent-cyan" />
                <span className="text-text-muted">Staked</span>
              </div>
              <span className="font-mono text-text-primary">
                {formatEgldBare(stakedEgld)}
              </span>
            </div>
            <div className="text-center">
              <div className="flex items-center gap-1.5 justify-center">
                <span className="w-2 h-2 rounded-sm bg-surface-strong" />
                <span className="text-text-muted">Circulating</span>
              </div>
              <span className="font-mono text-text-primary">
                {formatEgldBare(unstakedEgld)}
              </span>
            </div>
          </div>
        </div>

        {/* Activity stats */}
        <div className="card p-4 lg:col-span-1">
          <p className="eyebrow mb-3">Activity</p>
          <dl className="text-[12px] space-y-2 font-mono">
            <DetailRow
              label="Total TX"
              value={formatNumberFull(activity.total_transactions)}
            />
            {activity.avg_daily_transactions != null && (
              <DetailRow
                label="Avg Daily TX"
                value={formatNumber(activity.avg_daily_transactions)}
              />
            )}
            <DetailRow label="Epoch" value={String(activity.epoch)} />
            <DetailRow label="Blocks" value={formatNumber(activity.blocks)} />
            <DetailRow label="Shards" value={String(activity.shards)} />
            {deltas.epoch_advanced != null && (
              <DetailRow
                label="Epochs This Period"
                value={`+${deltas.epoch_advanced}`}
              />
            )}
          </dl>
        </div>
      </div>

      {/* Analysis */}
      <AnalysisBlock text={analysis} />
    </div>
  )
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-text-muted text-[11px] uppercase tracking-wider">
        {label}
      </dt>
      <dd className="text-text-primary tabular">{value}</dd>
    </div>
  )
}
