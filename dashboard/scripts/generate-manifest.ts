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
