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
}

export function DataTable<T extends Record<string, unknown>>({
  columns,
  data,
  defaultSort,
  rowClassName,
  emptyMessage = 'No data',
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(defaultSort?.key ?? null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(defaultSort?.dir ?? 'asc')

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

  return (
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
                  col.sortable ? 'cursor-pointer select-none hover:text-text-primary transition-colors' : '',
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
          {sorted.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-3 py-8 text-center text-text-secondary italic"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            sorted.map((row, i) => (
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
  )
}
