import type { DigestEntry } from '../../hooks/useDigests'

interface DigestListProps {
  manifest: DigestEntry[]
  selectedDate: string
  onSelect: (date: string) => void
}

function formatDayLabel(date: string): string {
  const d = new Date(date + 'T00:00:00Z')
  return d.toLocaleDateString('en-US', {
    weekday: 'short',
    timeZone: 'UTC',
  })
}

export function DigestList({ manifest, selectedDate, onSelect }: DigestListProps) {
  if (manifest.length === 0) {
    return (
      <aside className="card p-4 text-[12px] text-text-muted">
        No digests yet — the daily agent hasn't run.
      </aside>
    )
  }

  return (
    <aside className="card overflow-hidden h-fit sticky top-32">
      <div className="px-3 py-2 border-b border-border eyebrow bg-bg-elevated">
        Digests · {manifest.length}
      </div>
      <ul className="max-h-[calc(100vh-220px)] overflow-y-auto">
        {manifest.map((entry) => {
          const isSelected = entry.date === selectedDate
          return (
            <li key={entry.date}>
              <button
                onClick={() => onSelect(entry.date)}
                className={[
                  'w-full text-left px-3 py-2 flex items-baseline justify-between gap-2 border-l-2 transition-colors',
                  isSelected
                    ? 'border-accent-cyan bg-accent-cyan/10 text-accent-cyan'
                    : 'border-transparent text-text-secondary hover:bg-surface-hover hover:text-text-primary',
                ].join(' ')}
              >
                <span className="font-mono text-[12px] tabular">
                  {entry.date}
                </span>
                <span
                  className={[
                    'text-[9.5px] uppercase tracking-widest',
                    isSelected ? 'text-accent-cyan/70' : 'text-text-faint',
                  ].join(' ')}
                >
                  {formatDayLabel(entry.date)}
                </span>
              </button>
            </li>
          )
        })}
      </ul>
    </aside>
  )
}
