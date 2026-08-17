import fs from 'fs'
import path from 'path'

const reportsDir = path.resolve(import.meta.dirname, '../../reports')
const publicDir = path.resolve(import.meta.dirname, '../public')
const publicReportsDir = path.resolve(publicDir, 'reports')

// Ensure public/reports/ exists
fs.mkdirSync(publicReportsDir, { recursive: true })

// In CI/Vercel the parent reports/ directory doesn't exist — fall back to
// whatever is already committed in public/reports/.
const sourceExists = fs.existsSync(reportsDir)

const files = sourceExists
  ? fs.readdirSync(reportsDir).filter(f => /^\d{4}-\d{2}-\d{2}\.json$/.test(f)).sort()
  : fs.readdirSync(publicReportsDir).filter(f => /^\d{4}-\d{2}-\d{2}\.json$/.test(f)).sort()

// Generate manifest
const manifest = files.map(f => ({
  date: f.replace('.json', ''),
  file: f,
}))

// Write manifest
fs.writeFileSync(
  path.resolve(publicDir, 'report-manifest.json'),
  JSON.stringify(manifest, null, 2),
)

// ---------------------------------------------------------------------------
// Errata overlay (added run #21)
//
// Each report may declare `meta_learning.withdrawn_claims` — claims published in
// EARLIER runs that this run withdraws. The archive is immutable, so without this
// aggregation a reader opening run #19 sees a withdrawn narrative asserted with
// full confidence. Collect every withdrawal into one small file, resolve run
// numbers to dates, and let the dashboard warn on superseded reports.
// ---------------------------------------------------------------------------
const searchDir = sourceExists ? reportsDir : publicReportsDir
const runToDate = new Map<number, string>()
type Withdrawal = {
  claim: string
  asserted_in_runs: number[]
  withdrawn_in_run: number
  reason: string
  replacement?: string | null
}
const withdrawals: Withdrawal[] = []

for (const file of files) {
  let report: Record<string, any>
  try {
    report = JSON.parse(fs.readFileSync(path.resolve(searchDir, file), 'utf8'))
  } catch {
    continue
  }
  const run = report?.metadata?.run_number
  const date = file.replace('.json', '')
  if (typeof run === 'number') runToDate.set(run, date)
  const claims = report?.meta_learning?.withdrawn_claims
  if (Array.isArray(claims)) {
    for (const c of claims) {
      if (c && typeof c.claim === 'string' && Array.isArray(c.asserted_in_runs)) {
        withdrawals.push(c as Withdrawal)
      }
    }
  }
}

// ---------------------------------------------------------------------------
// Scoreboard ledger (added run #21)
//
// Prediction accuracy only means something as a SERIES, so the per-run records
// are aggregated here rather than being re-derived from whichever week happens
// to be selected. Every test carries the run that registered it and the run that
// resolved it, so open tests stay visible across weeks until they resolve.
// ---------------------------------------------------------------------------
type TestRecord = Record<string, any> & {
  id: string
  registered_in_run: number
  status: string
  outcome?: string | null
  resolved_in_run?: number | null
}
const allTests: TestRecord[] = []
const runRecords: Record<string, any>[] = []

for (const file of files) {
  let report: Record<string, any>
  try {
    report = JSON.parse(fs.readFileSync(path.resolve(searchDir, file), 'utf8'))
  } catch {
    continue
  }
  const tests = report?.pre_committed_tests
  if (!Array.isArray(tests) || tests.length === 0) continue

  const run = report?.metadata?.run_number ?? null
  const date = file.replace('.json', '')
  const resolvedHere = tests.filter(
    (t: TestRecord) => t.status === 'resolved' && t.resolved_in_run === run,
  )
  const count = (outcome: string) =>
    resolvedHere.filter((t: TestRecord) => t.outcome === outcome).length

  const asPredicted = count('as_predicted')
  runRecords.push({
    run,
    date,
    registered: tests.filter((t: TestRecord) => t.registered_in_run === run).length,
    resolved: resolvedHere.length,
    as_predicted: asPredicted,
    against: count('against'),
    inconclusive: count('inconclusive'),
    withdrawn: count('withdrawn'),
    hit_rate_pct: resolvedHere.length
      ? (100 * asPredicted) / resolvedHere.length
      : null,
    open_after: tests.filter((t: TestRecord) => t.status === 'open').length,
  })

  for (const t of tests) {
    allTests.push({ ...t, seen_in_run: run, seen_in_date: date })
  }
}

// Latest state per test id — a test registered open in one run and resolved in
// the next appears in both reports; the resolved copy wins.
const byId = new Map<string, TestRecord>()
for (const t of allTests) {
  const prev = byId.get(t.id)
  if (!prev || (prev.status === 'open' && t.status === 'resolved')) byId.set(t.id, t)
}
const ledger = Array.from(byId.values())
const totalResolved = ledger.filter(t => t.status === 'resolved').length
const totalAsPredicted = ledger.filter(t => t.outcome === 'as_predicted').length

const scoreboard = {
  generated_from: files.length,
  totals: {
    tests: ledger.length,
    resolved: totalResolved,
    open: ledger.filter(t => t.status === 'open').length,
    as_predicted: totalAsPredicted,
    against: ledger.filter(t => t.outcome === 'against').length,
    inconclusive: ledger.filter(t => t.outcome === 'inconclusive').length,
    withdrawn: ledger.filter(t => t.outcome === 'withdrawn').length,
    hit_rate_pct: totalResolved ? (100 * totalAsPredicted) / totalResolved : null,
  },
  runs: runRecords.sort((a, b) => (a.run ?? 0) - (b.run ?? 0)),
  tests: ledger.sort(
    (a, b) => (b.registered_in_run ?? 0) - (a.registered_in_run ?? 0),
  ),
}

fs.writeFileSync(
  path.resolve(publicDir, 'scoreboard.json'),
  JSON.stringify(scoreboard, null, 2),
)

const errata = {
  generated_from: files.length,
  claims: withdrawals.map(c => ({
    ...c,
    asserted_in_dates: c.asserted_in_runs
      .map(r => runToDate.get(r))
      .filter((d): d is string => Boolean(d)),
    withdrawn_in_date: runToDate.get(c.withdrawn_in_run) ?? null,
  })),
}

fs.writeFileSync(
  path.resolve(publicDir, 'errata.json'),
  JSON.stringify(errata, null, 2),
)

// Copy report files to public/reports/ (only when source dir exists)
if (sourceExists) {
  for (const file of files) {
    fs.copyFileSync(
      path.resolve(reportsDir, file),
      path.resolve(publicReportsDir, file),
    )
  }
}

console.log(`Generated manifest with ${files.length} report(s): ${files.join(', ')} (source: ${sourceExists ? reportsDir : publicReportsDir})`)
console.log(`Generated errata.json with ${errata.claims.length} withdrawn claim(s)`)
console.log(
  `Generated scoreboard.json: ${scoreboard.totals.tests} test(s) across ${scoreboard.runs.length} run(s) — ` +
    `${scoreboard.totals.resolved} resolved, ${scoreboard.totals.as_predicted} as predicted, ` +
    `${scoreboard.totals.open} open`,
)
