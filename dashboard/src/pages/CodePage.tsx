import { useDigests } from '../hooks/useDigests'
import { useStats } from '../hooks/useStats'
import { CodeHeader } from '../components/code/CodeHeader'
import { DigestList } from '../components/code/DigestList'
import { DigestViewer } from '../components/code/DigestViewer'
import { StatsPanel, StatsPanelEmpty } from '../components/code/StatsPanel'

export function CodePage() {
  const {
    manifest,
    selectedDate,
    setSelectedDate,
    content,
    loading,
    error,
    retry,
    lastFetchedAt,
  } = useDigests()

  const { stats, loading: statsLoading } = useStats()

  if (error && manifest.length === 0) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center px-6">
        <div className="text-center max-w-md">
          <p className="text-down text-lg font-medium">Failed to load digests</p>
          <p className="mt-2 text-text-muted text-sm font-mono break-all">
            {error}
          </p>
          <button
            onClick={retry}
            className="mt-4 px-4 py-2 bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/30 rounded hover:bg-accent-cyan/20 transition-colors text-sm font-mono uppercase tracking-wider"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-bg text-text-primary">
      <CodeHeader
        manifest={manifest}
        selectedDate={selectedDate}
        onDateChange={setSelectedDate}
        lastFetchedAt={lastFetchedAt}
        onRefresh={retry}
        loading={loading}
      />

      <main className="max-w-[1380px] mx-auto px-6 pb-16 pt-6 space-y-8">
        {/* Quantitative stats — top of page */}
        {stats ? (
          <StatsPanel stats={stats} />
        ) : statsLoading ? null : (
          <StatsPanelEmpty />
        )}

        {/* Daily digest narrative — below stats */}
        <div className="grid grid-cols-1 md:grid-cols-[240px_1fr] gap-6">
          <DigestList
            manifest={manifest}
            selectedDate={selectedDate}
            onSelect={setSelectedDate}
          />
          <DigestViewer
            content={content}
            loading={loading}
            date={selectedDate}
          />
        </div>
      </main>

      <footer className="border-t border-border py-4 px-6 text-[10px] text-text-faint font-mono uppercase tracking-widest text-center">
        MultiversX Proof of Progress · Daily code-activity digest · Source:{' '}
        <a
          href="https://github.com/lamentierschweinchen/proof-of-progress"
          className="text-text-muted hover:text-accent-cyan transition-colors"
          target="_blank"
          rel="noopener noreferrer"
        >
          proof-of-progress
        </a>
      </footer>
    </div>
  )
}
