import { useReports } from '../hooks/useReports'
import { Header } from '../components/Header'
import { SectionNav } from '../components/SectionNav'
import { ExecutiveSummary } from '../components/ExecutiveSummary'
import { NetworkHealth } from '../components/NetworkHealth'
import { WhaleIntelligence } from '../components/WhaleIntelligence'
import { StakingIntelligence } from '../components/StakingIntelligence'
import { TokenDefi } from '../components/TokenDefi'
import { AnomaliesWatchList } from '../components/AnomaliesWatchList'
import { MetaLearning } from '../components/MetaLearning'
import { OtcPipeline } from '../components/OtcPipeline'
import { UnbondingCard } from '../components/UnbondingCard'
import { Scoreboard } from '../components/Scoreboard'
import { ErrataBanner } from '../components/ErrataBanner'
import { useErrata, supersededClaims, ownWithdrawals } from '../hooks/useErrata'
import { useScoreboard } from '../hooks/useScoreboard'

export function HomePage() {
  const { manifest, selectedDate, setSelectedDate, report, loading, error, retry } = useReports()
  // Errata is an overlay across ALL reports, so it loads independently of the
  // selected week and must never block rendering.
  const errata = useErrata()
  // The prediction ledger spans runs, so it loads independently of the cursor.
  const scoreboard = useScoreboard()

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
        <ErrataBanner
          superseded={supersededClaims(errata, report.metadata.run_number)}
          own={ownWithdrawals(errata, report.metadata.run_number)}
          onJumpToRun={setSelectedDate}
        />

        <SectionHeader title="Executive Summary" subtitle="Top findings, ordered by significance">
          <section id="executive-summary">
            <ExecutiveSummary findings={report.executive_summary} />
          </section>
        </SectionHeader>

        <SectionHeader title="Network Health" subtitle="Macro economics + onchain activity">
          <section id="network-health">
            <NetworkHealth data={report.network_health} />
          </section>
        </SectionHeader>

        <SectionHeader
          title="OTC Pipeline"
          subtitle="Gross vs net one-way · wave-window netting · venue terminals"
        >
          <section id="otc-pipeline">
            <OtcPipeline
              data={report.whale_intelligence.otc_pipeline}
              reportDate={report.metadata.report_date}
            />
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
          <section id="staking-intelligence" className="space-y-4">
            {report.staking_intelligence.unbonding_in_flight && (
              <UnbondingCard
                data={report.staking_intelligence.unbonding_in_flight}
                reportDate={report.metadata.report_date}
              />
            )}
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

        <SectionHeader
          title="Model Scoreboard"
          subtitle="Calls made in advance · what landed, what missed, what is still open"
        >
          <section id="scoreboard">
            <Scoreboard
              tests={report.pre_committed_tests}
              runNumber={report.metadata.run_number}
              ledger={scoreboard}
            />
          </section>
        </SectionHeader>

        <section id="meta-learning">
          <MetaLearning data={report.meta_learning} />
        </section>
      </main>

      <footer className="border-t border-border py-4 px-6 text-[10px] text-text-faint font-mono uppercase tracking-widest text-center">
        MultiversX Onchain Intelligence · v2 schema · Generated weekly by{' '}
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
