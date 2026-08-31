import type { DigestEntry } from '../../hooks/useDigests'
import { PageTabs } from '../PageTabs'

interface CodeHeaderProps {
  manifest: DigestEntry[]
  selectedDate: string
  onDateChange: (date: string) => void
  lastFetchedAt: number | null
  onRefresh: () => void
  loading: boolean
}

function relativeTime(epoch: number): string {
  const seconds = Math.floor((Date.now() - epoch) / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return new Date(epoch).toISOString().slice(0, 10)
}

function formatDigestDate(date: string): string {
  // 2026-05-18 → May 18
  const d = new Date(date + 'T00:00:00Z')
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC',
  })
}

export function CodeHeader({
  manifest,
  selectedDate,
  onDateChange,
  lastFetchedAt,
  onRefresh,
  loading,
}: CodeHeaderProps) {
  return (
    <header className="sticky top-0 z-50 border-b border-border bg-bg/95 backdrop-blur-sm">
      {/* Top row — brand, tabs, GitHub link */}
      <div className="flex items-center px-6 py-3 gap-6 border-b border-border-subtle">
        {/* Brand */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <div className="w-1.5 h-6 bg-accent-cyan rounded-sm shadow-[0_0_8px_rgba(35,247,221,0.5)]" />
          <div className="flex flex-col leading-tight">
            <span className="text-[14px] font-semibold tracking-tight text-text-primary">
              MultiversX Intelligence
            </span>
            <span className="text-[10px] uppercase tracking-[0.15em] text-text-muted">
              Proof of Progress · Code Activity
            </span>
          </div>
        </div>

        <div className="ml-4">
          <PageTabs active="code" />
        </div>

        <div className="flex-1" />

        <a
          href="https://github.com/lamentierschweinchen/proof-of-progress"
          target="_blank"
          rel="noopener noreferrer"
          className="hidden md:flex items-center gap-1.5 text-[11px] font-mono text-text-muted hover:text-accent-cyan transition-colors"
        >
          <span className="text-text-faint">repo:</span>
          <span>lamentierschweinchen/proof-of-progress</span>
          <span className="text-text-faint">↗</span>
        </a>
      </div>

      {/* Bottom row — date selector + meta */}
      <div className="flex items-center px-6 py-2 gap-4 text-[11px]">
        <div className="flex items-center gap-2">
          <span className="text-text-muted uppercase tracking-wider text-[10px]">
            Digest
          </span>
          <select
            value={selectedDate}
            onChange={(e) => onDateChange(e.target.value)}
            disabled={manifest.length === 0}
            className="bg-surface border border-border text-text-primary text-[11px] font-mono rounded px-2 py-0.5 focus:outline-none focus:border-accent-cyan/60 cursor-pointer hover:border-border-strong transition-colors disabled:opacity-40"
          >
            {manifest.map((entry) => (
              <option key={entry.date} value={entry.date}>
                {formatDigestDate(entry.date)}
              </option>
            ))}
          </select>
          <span className="text-text-muted">
            <span className="text-text-faint">·</span>{' '}
            <span className="text-text-secondary font-mono">{manifest.length}</span>{' '}
            total
          </span>
        </div>

        <div className="flex-1" />

        {lastFetchedAt && (
          <span className="text-text-muted">
            Fetched{' '}
            <span className="text-text-secondary font-mono">
              {relativeTime(lastFetchedAt)}
            </span>
          </span>
        )}

        <button
          onClick={onRefresh}
          disabled={loading}
          className="text-[11px] font-mono uppercase tracking-wider text-text-muted hover:text-accent-cyan transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          aria-label="Refresh digest list"
        >
          {loading ? '…' : '↻ Refresh'}
        </button>
      </div>
    </header>
  )
}
