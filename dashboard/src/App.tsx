import { useReports } from './hooks/useReports'
import { Header } from './components/Header'
import { SectionNav } from './components/SectionNav'
import { ExecutiveSummary } from './components/ExecutiveSummary'
import { NetworkHealth } from './components/NetworkHealth'
import { WhaleIntelligence } from './components/WhaleIntelligence'
import { StakingIntelligence } from './components/StakingIntelligence'
import { TokenDefi } from './components/TokenDefi'
import { AnomaliesWatchList } from './components/AnomaliesWatchList'
import { MetaLearning } from './components/MetaLearning'

function App() {
  const { manifest, selectedDate, setSelectedDate, report, loading, error, retry } = useReports()

  if (loading) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="mt-4 text-text-secondary">Loading report...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <div className="text-center max-w-md">
          <p className="text-severity-high text-lg font-medium">Failed to load report</p>
          <p className="mt-2 text-text-secondary text-sm">{error}</p>
          <button
            onClick={retry}
            className="mt-4 px-4 py-2 bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/30 rounded-lg hover:bg-accent-cyan/20 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <p className="text-text-secondary">No reports available</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-bg text-text-primary">
      <Header
        metadata={report.metadata}
        priceDelta={report.network_health.deltas.price_change_pct}
        manifest={manifest}
        selectedDate={selectedDate}
        onDateChange={setSelectedDate}
      />

      <SectionNav />

      <main className="max-w-7xl mx-auto px-6 pb-16 space-y-12 pt-4">
        <section id="executive-summary">
          <h2 className="text-xl font-bold text-text-primary mb-4">Executive Summary</h2>
          <ExecutiveSummary findings={report.executive_summary} />
        </section>

        <section id="network-health">
          <h2 className="text-xl font-bold text-text-primary mb-4">Network Health</h2>
          <NetworkHealth data={report.network_health} />
        </section>

        <section id="whale-intelligence">
          <h2 className="text-xl font-bold text-text-primary mb-4">Whale Intelligence</h2>
          <WhaleIntelligence data={report.whale_intelligence} />
        </section>

        <section id="staking-intelligence">
          <h2 className="text-xl font-bold text-text-primary mb-4">Staking Intelligence</h2>
          <StakingIntelligence data={report.staking_intelligence} />
        </section>

        <section id="token-defi">
          <h2 className="text-xl font-bold text-text-primary mb-4">Tokens & DeFi</h2>
          <TokenDefi tokenData={report.token_activity} defiData={report.defi_activity} />
        </section>

        <section id="anomalies-watchlist">
          <h2 className="text-xl font-bold text-text-primary mb-4">Anomalies & Watch List</h2>
          <AnomaliesWatchList anomalies={report.anomalies} watchList={report.watch_list} />
        </section>

        <section id="meta-learning">
          <MetaLearning data={report.meta_learning} />
        </section>
      </main>
    </div>
  )
}

export default App
