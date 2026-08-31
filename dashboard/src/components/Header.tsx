import {
  formatDelta,
  formatDate,
  formatTimestamp,
  formatUsd,
} from '../lib/formatters'
import type { ReportMetadata, ManifestEntry } from '../types/report'
import { PageTabs } from './PageTabs'

interface HeaderProps {
  metadata: ReportMetadata
  priceDelta: number | null
  manifest: ManifestEntry[]
  selectedDate: string
  onDateChange: (date: string) => void
}

function MarketTicker({
  symbol,
  price,
  className = '',
}: {
  symbol: string
  price: number | null | undefined
  className?: string
}) {
  if (price == null) return null
  return (
    <div className={`flex items-baseline gap-1.5 ${className}`}>
      <span className="text-[10px] font-medium text-text-muted tracking-wider uppercase">
        {symbol}
      </span>
      <span className="ticker text-text-primary font-medium">
        {formatUsd(price)}
      </span>
    </div>
  )
}

export function Header({
  metadata,
  priceDelta,
  manifest,
  selectedDate,
  onDateChange,
}: HeaderProps) {
  const delta = formatDelta(priceDelta, 'pct')

  const totalOk = metadata.data_sources_ok.length
  const recovered = metadata.data_sources_recovered ?? []
  const totalFailed = metadata.data_sources_failed.length

  return (
    <header className="sticky top-0 z-50 border-b border-border bg-bg/95 backdrop-blur-sm">
      {/* Top row — title, EGLD price, ticker, status */}
      <div className="flex items-center px-6 py-3 gap-6 border-b border-border-subtle">
        {/* Brand */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="w-1.5 h-6 bg-accent-cyan rounded-sm shadow-[0_0_8px_rgba(35,247,221,0.5)]" />
          <div className="flex flex-col leading-tight">
            <span className="text-[14px] font-semibold tracking-tight text-text-primary">
              MultiversX Intelligence
            </span>
            <span className="text-[10px] uppercase tracking-[0.15em] text-text-muted">
              Weekly Onchain Brief · v2
            </span>
          </div>
        </div>

        <div className="ml-4">
          <PageTabs active="home" />
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Market tickers */}
        <div className="hidden md:flex items-center gap-5">
          <MarketTicker symbol="BTC" price={metadata.btc_price_usd} />
          <MarketTicker symbol="ETH" price={metadata.eth_price_usd} />
          <div className="h-5 w-px bg-border" />
          <div className="flex items-baseline gap-2">
            <span className="text-[10px] font-medium text-text-muted tracking-wider uppercase">
              EGLD
            </span>
            <span className="hero-number-sm">
              {formatUsd(metadata.egld_price_usd)}
            </span>
            <span className={`text-[11px] font-mono ${delta.color}`}>
              {delta.arrow === 'up' && '▲ '}
              {delta.arrow === 'down' && '▼ '}
              {delta.text}
            </span>
          </div>
        </div>
      </div>

      {/* Bottom row — date selector, period, data source health */}
      <div className="flex items-center px-6 py-2 gap-4 text-[11px]">
        {/* Date picker */}
        <div className="flex items-center gap-2">
          <span className="text-text-muted uppercase tracking-wider text-[10px]">
            Report
          </span>
          <select
            value={selectedDate}
            onChange={(e) => onDateChange(e.target.value)}
            className="bg-surface border border-border text-text-primary text-[11px] font-mono rounded px-2 py-0.5 focus:outline-none focus:border-accent-cyan/60 cursor-pointer hover:border-border-strong transition-colors"
          >
            {manifest.map((entry) => (
              <option key={entry.date} value={entry.date}>
                {formatDate(entry.date)}
              </option>
            ))}
          </select>
          {metadata.run_number && (
            <span className="text-text-muted">
              <span className="text-text-faint">·</span> Run #
              <span className="text-text-secondary">{metadata.run_number}</span>
            </span>
          )}
        </div>

        <div className="hidden sm:block h-3 w-px bg-border" />

        {/* Period — secondary on a phone, where the selector already names the week */}
        <span className="hidden sm:inline text-text-muted">
          Period{' '}
          <span className="text-text-secondary font-mono">
            {formatDate(metadata.period_start.slice(0, 10))}
          </span>
          {' → '}
          <span className="text-text-secondary font-mono">
            {formatDate(metadata.period_end.slice(0, 10))}
          </span>
        </span>

        <div className="flex-1" />

        {/* Data source dots */}
        {/* The data-source dot strip is ~240px of fixed-width content and was
            forcing the whole page to scroll horizontally at 375px. It is
            provenance detail, not a headline, so it waits for a wider viewport. */}
        <div className="hidden md:flex items-center gap-3">
          {totalOk > 0 && (
            <div className="flex items-center gap-1.5">
              <div className="flex gap-[3px]">
                {metadata.data_sources_ok.slice(0, 13).map((src) => (
                  <span
                    key={src}
                    title={src}
                    className="w-1.5 h-1.5 rounded-full bg-up shadow-[0_0_3px_rgba(52,209,150,0.6)]"
                  />
                ))}
              </div>
              <span className="text-text-muted">{totalOk} ok</span>
            </div>
          )}
          {/* A source that failed once and was re-queried successfully is not
              missing data. Counting it as "failed" told the reader the report
              had holes it does not have. */}
          {recovered.length > 0 && (
            <div className="flex items-center gap-1.5">
              <div className="flex gap-[3px]">
                {recovered.slice(0, 5).map((src) => (
                  <span
                    key={src}
                    title={src}
                    className="w-1.5 h-1.5 rounded-full bg-severity-medium"
                  />
                ))}
              </div>
              <span
                className="text-severity-medium cursor-help"
                title={recovered.join('\n\n')}
              >
                {recovered.length} retried
              </span>
            </div>
          )}
          {totalFailed > 0 && (
            <div className="flex items-center gap-1.5">
              <div className="flex gap-[3px]">
                {metadata.data_sources_failed.slice(0, 5).map((src) => (
                  <span
                    key={src}
                    title={src}
                    className="w-1.5 h-1.5 rounded-full bg-down"
                  />
                ))}
              </div>
              <span
                className="text-down cursor-help"
                title={metadata.data_sources_failed.join('\n\n')}
              >
                {totalFailed} missing
              </span>
            </div>
          )}
        </div>

        <div className="hidden sm:block h-3 w-px bg-border" />

        <span className="hidden sm:inline text-text-muted">
          Generated{' '}
          <span className="text-text-secondary font-mono">
            {formatTimestamp(metadata.generated_at)}
          </span>
        </span>
      </div>
    </header>
  )
}
