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
          <p className="mt-4 text-text-muted text-sm font-mono uppercase tracking-wider">
            Loading…
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <div className="text-center max-w-md">
          <p className="text-down text-lg font-medium">Failed to load report</p>
          <p className="mt-2 text-text-muted text-sm font-mono">{error}</p>
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

  if (!report) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <p className="text-text-muted">No reports available</p>
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

      <main className="max-w-[1380px] mx-auto px-6 pb-16 space-y-8 pt-6">
        <SectionHeader title="Executive Summary" subtitle="Top findings, ordered by significance">
          <section id="executive-summary">
            <ExecutiveSummary findings={report.executive_summary} />
          </section>
        </SectionHeader>

        <SectionHeader title="Network Health" subtitle="Macro economics + on-chain activity">
          <section id="network-health">
            <NetworkHealth data={report.network_health} />
          </section>
        </SectionHeader>

        <SectionHeader title="Whale Intelligence" subtitle="Tier stratification, flows, dormant activations">
          <section id="whale-intelligence">
            <WhaleIntelligence data={report.whale_intelligence} />
          </section>
        </SectionHeader>

        <SectionHeader
          title="Staking Intelligence"
          subtitle="Concentration, APR distribution, churn"
        >
          <section id="staking-intelligence">
            <StakingIntelligence data={report.staking_intelligence} />
          </section>
        </SectionHeader>

        <SectionHeader
          title="Tokens & DeFi"
          subtitle="Top 10 tokens, newly issued, per-protocol breakdown"
        >
          <section id="token-defi">
            <TokenDefi
              tokenData={report.token_activity}
              defiData={report.defi_activity}
            />
          </section>
        </SectionHeader>

        <SectionHeader
          title="Anomalies & Trend Indicators"
          subtitle="Z-score (when N≥4) · % threshold fallback · multi-week trajectories"
        >
          <section id="anomalies-watchlist">
            <AnomaliesWatchList
              anomalies={report.anomalies}
              watchList={report.watch_list}
              trends={report.trend_indicators ?? null}
            />
          </section>
        </SectionHeader>

        <section id="meta-learning">
          <MetaLearning data={report.meta_learning} />
        </section>
      </main>

      <footer className="border-t border-border py-4 px-6 text-[10px] text-text-faint font-mono uppercase tracking-widest text-center">
        MultiversX On-Chain Intelligence · v2 schema · Generated weekly by{' '}
        <a
          href="https://github.com/lamentierschweinchen/onchain-quant-agent"
          className="text-text-muted hover:text-accent-cyan transition-colors"
          target="_blank"
          rel="noopener noreferrer"
        >
          onchain-quant-agent
        </a>
      </footer>
    </div>
  )
}

function SectionHeader({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle?: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-3">
      <div className="flex items-baseline gap-3 border-b border-border pb-2">
        <h2 className="text-[14px] font-semibold text-text-primary tracking-tight">
          {title}
        </h2>
        {subtitle && (
          <span className="text-[10.5px] text-text-muted uppercase tracking-widest">
            {subtitle}
          </span>
        )}
      </div>
      {children}
    </div>
  )
}

export default App
