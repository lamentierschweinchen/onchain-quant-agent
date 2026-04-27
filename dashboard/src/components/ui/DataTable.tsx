import { useState } from 'react'

export interface Column<T> {
  key: string
  label: string
  render?: (value: unknown, row: T) => React.ReactNode
  sortable?: boolean
  align?: 'left' | 'right'
  className?: string
}

interface DataTableProps<T extends Record<string, unknown>> {
  columns: Column<T>[]
  data: T[]
  defaultSort?: { key: string; dir: 'asc' | 'desc' }
  rowClassName?: (row: T) => string
  emptyMessage?: string
  /**
   * If set and `data.length` exceeds it, only the first `collapsed` rows
   * are shown by default. A "Show all (N)" footer button reveals the rest.
   * Sorting always applies to the full set; the collapse only limits
   * which rows render after sort.
   */
  collapsed?: number
  /** Noun used in the expand button label (default: 'row') */
  noun?: string
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  defaultSort,
  rowClassName,
  emptyMessage = 'No data',
  collapsed,
  noun = 'row',
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(defaultSort?.key ?? null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(defaultSort?.dir ?? 'asc')
  const [expanded, setExpanded] = useState(false)

  function handleSort(key: string) {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortKey(key)
      setSortDir('asc')
    }
  }

  const sorted = sortKey
    ? [...data].sort((a, b) => {
        const av = a[sortKey]
        const bv = b[sortKey]
        if (av == null && bv == null) return 0
        if (av == null) return 1
        if (bv == null) return -1
        let cmp = 0
        if (typeof av === 'number' && typeof bv === 'number') {
          cmp = av - bv
        } else {
          cmp = String(av).localeCompare(String(bv))
        }
        return sortDir === 'asc' ? cmp : -cmp
      })
    : data

  const total = sorted.length
  const collapseLimit = collapsed ?? total
  const showCollapseUI = collapsed != null && total > collapseLimit
  const visible =
    showCollapseUI && !expanded ? sorted.slice(0, collapseLimit) : sorted

  return (
    <div className="w-full">
      <div className="w-full overflow-x-auto">
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="border-b border-border">
              {columns.map((col) => (
                <th
                  key={col.key}
                  onClick={col.sortable ? () => handleSort(col.key) : undefined}
                  className={[
                    'px-3 py-2 text-xs font-medium text-text-secondary uppercase tracking-wide',
                    col.align === 'right' ? 'text-right' : 'text-left',
                    col.sortable
                      ? 'cursor-pointer select-none hover:text-text-primary transition-colors'
                      : '',
                    col.className ?? '',
                  ].join(' ')}
                >
                  <span className="inline-flex items-center gap-1">
                    {col.label}
                    {col.sortable && sortKey === col.key && (
                      <span className="text-accent-cyan">
                        {sortDir === 'asc' ? '▲' : '▼'}
                      </span>
                    )}
                    {col.sortable && sortKey !== col.key && (
                      <span className="text-border opacity-60">⇅</span>
                    )}
                  </span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-3 py-8 text-center text-text-secondary italic"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              visible.map((row, i) => (
                <tr
                  key={i}
                  className={[
                    'border-b border-border/50 hover:bg-surface-hover transition-colors',
                    rowClassName ? rowClassName(row) : '',
                  ].join(' ')}
                >
                  {columns.map((col) => {
                    const rawValue = row[col.key]
                    const cell = col.render ? col.render(rawValue, row) : rawValue

                    return (
                      <td
                        key={col.key}
                        className={[
                          'px-3 py-2.5 text-text-primary',
                          col.align === 'right' ? 'text-right font-mono' : '',
                          col.className ?? '',
                        ].join(' ')}
                      >
                        {cell as React.ReactNode}
                      </td>
                    )
                  })}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showCollapseUI && (
        <button
          onClick={() => setExpanded((e) => !e)}
          aria-expanded={expanded}
          className="w-full px-4 py-2 border-t border-border bg-bg-elevated hover:bg-surface-hover transition-colors text-[10.5px] font-mono uppercase tracking-widest text-text-muted hover:text-accent-cyan flex items-center justify-center gap-2"
        >
          {expanded ? (
            <>
              <span>Show top {collapseLimit}</span>
              <Chevron direction="up" />
            </>
          ) : (
            <>
              <span>
                Show all {total} {noun}
                {total === 1 ? '' : 's'}
              </span>
              <Chevron direction="down" />
            </>
          )}
        </button>
      )}
    </div>
  )
}

function Chevron({ direction }: { direction: 'up' | 'down' }) {
  return (
    <svg
      width="10"
      height="10"
      viewBox="0 0 10 10"
      fill="none"
      style={{ transform: direction === 'up' ? 'rotate(180deg)' : 'none' }}
    >
      <path
        d="M2 4l3 3 3-3"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  )
}
