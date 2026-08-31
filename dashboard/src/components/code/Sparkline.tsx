interface SparklineProps {
  values: number[]
  width?: number
  height?: number
  color?: string
  /** Optional area fill below the line */
  fill?: boolean
}

/**
 * Inline SVG sparkline. ~80×16 by default. Renders a smooth polyline with
 * optional area fill. Uses tabular numerics-friendly minimal styling so it
 * sits cleanly inside table cells.
 */
export function Sparkline({
  values,
  width = 80,
  height = 18,
  color = 'var(--color-accent-cyan)',
  fill = true,
}: SparklineProps) {
  if (!values || values.length === 0) {
    return (
      <span className="inline-block text-text-faint text-[10px] font-mono">—</span>
    )
  }

  const max = Math.max(...values, 1)
  const padding = 1
  const innerWidth = width - padding * 2
  const innerHeight = height - padding * 2

  const points = values.map((v, i) => {
    const x = padding + (i / Math.max(values.length - 1, 1)) * innerWidth
    const y = padding + (1 - v / max) * innerHeight
    return [x, y]
  })

  const linePath = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p[0].toFixed(2)} ${p[1].toFixed(2)}`)
    .join(' ')

  const areaPath = fill
    ? `${linePath} L ${points[points.length - 1][0].toFixed(2)} ${height - padding} L ${padding} ${height - padding} Z`
    : null

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      style={{ display: 'block' }}
      aria-hidden
    >
      {areaPath && (
        <path d={areaPath} fill={color} opacity={0.12} />
      )}
      <path
        d={linePath}
        fill="none"
        stroke={color}
        strokeWidth={1.25}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Last-value dot */}
      <circle
        cx={points[points.length - 1][0]}
        cy={points[points.length - 1][1]}
        r={1.5}
        fill={color}
      />
    </svg>
  )
}
