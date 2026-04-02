import { formatDelta, formatDate, formatTimestamp, formatUsd } from '../lib/formatters'
import type { ReportMetadata, ManifestEntry } from '../types/report'

interface HeaderProps {
  metadata: ReportMetadata
  priceDelta: number | null
  manifest: ManifestEntry[]
  selectedDate: string
  onDateChange: (date: string) => void
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
  const totalFailed = metadata.data_sources_failed.length

  return (
    <header className="sticky top-0 z-50 bg-bg/95 backdrop-blur border-b border-border">
      {/* Main row */}
      <div className="flex justify-between items-center px-6 py-3 gap-4">
        {/* Left: title + date picker */}
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-lg font-bold text-accent-cyan whitespace-nowrap">
            MultiversX Intelligence
          </span>
          <select
            value={selectedDate}
            onChange={(e) => onDateChange(e.target.value)}
            className="bg-surface border border-border text-text-primary text-sm rounded px-2 py-1 focus:outline-none focus:border-accent-cyan/50 cursor-pointer"
          >
            {manifest.map((entry) => (
              <option key={entry.date} value={entry.date}>
                {formatDate(entry.date)}
              </option>
            ))}
          </select>
        </div>

        {/* Center: EGLD price + delta */}
        <div className="flex items-center gap-2">
          <span className="font-mono text-xl font-bold text-text-primary">
            {formatUsd(metadata.egld_price_usd)}
          </span>
          <span className={`text-sm font-medium font-mono ${delta.color}`}>
            {delta.arrow === 'up' && '▲ '}
            {delta.arrow === 'down' && '▼ '}
            {delta.text}
          </span>
        </div>

        {/* Right: data source health + generated timestamp */}
        <div className="flex flex-col items-end gap-1">
          <div className="flex items-center gap-2 flex-wrap justify-end">
            {totalOk > 0 && (
              <span className="flex items-center gap-1 text-xs text-text-secondary">
                <span className="flex gap-0.5">
                  {metadata.data_sources_ok.map((src) => (
                    <span
                      key={src}
                      title={src}
                      className="w-2 h-2 bg-green-500 rounded-full inline-block"
                    />
                  ))}
                </span>
                <span>{totalOk} ok</span>
              </span>
            )}
            {totalFailed > 0 && (
              <span className="flex items-center gap-1 text-xs text-red-400">
                <span className="flex gap-0.5">
                  {metadata.data_sources_failed.map((src) => (
                    <span
                      key={src}
                      title={src}
                      className="w-2 h-2 bg-red-500 rounded-full inline-block"
                    />
                  ))}
                </span>
                <span>{totalFailed} failed</span>
              </span>
            )}
          </div>
          <span className="text-xs text-text-secondary whitespace-nowrap">
            Generated {formatTimestamp(metadata.generated_at)}
          </span>
        </div>
      </div>

      {/* Sub-header: period */}
      <div className="px-6 pb-2 text-sm text-text-secondary">
        Period:{' '}
        <span className="text-text-primary">
          {formatDate(metadata.period_start.slice(0, 10))}
        </span>
        {' — '}
        <span className="text-text-primary">
          {formatDate(metadata.period_end.slice(0, 10))}
        </span>
      </div>
    </header>
  )
}
