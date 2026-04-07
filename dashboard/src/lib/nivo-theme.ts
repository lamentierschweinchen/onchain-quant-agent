// Theme type not exported from this version of @nivo/core
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Theme = any

export const darkTheme: Theme = {
  background: 'transparent',
  text: { fontSize: 12, fill: '#94A3B8' },
  axis: {
    ticks: { text: { fill: '#94A3B8', fontSize: 11 } },
    legend: { text: { fill: '#E2E8F0', fontSize: 12 } },
  },
  grid: { line: { stroke: '#2A3144', strokeWidth: 1 } },
  tooltip: {
    container: {
      background: '#1A1F2E',
      color: '#E2E8F0',
      fontSize: 12,
      borderRadius: '6px',
      border: '1px solid #2A3144',
      boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
    },
  },
}
