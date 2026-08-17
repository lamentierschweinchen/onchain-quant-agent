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
