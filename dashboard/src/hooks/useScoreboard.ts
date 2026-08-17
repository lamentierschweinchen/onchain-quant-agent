import { useEffect, useState } from 'react'
import type { ScoreboardLedger } from '../types/report'

/**
 * The scoreboard is a SERIES, not a property of one week: accuracy only means
 * something across runs, and a test registered in run N is resolved in run N+1.
 * generate-manifest.ts aggregates every report's `pre_committed_tests` into
 * scoreboard.json, so this loads once and stays constant as the reader moves the
 * week cursor.
 *
 * Non-blocking by design — a missing ledger degrades the panel, never the page.
 */
export function useScoreboard(): ScoreboardLedger | null {
  const [ledger, setLedger] = useState<ScoreboardLedger | null>(null)

  useEffect(() => {
    let cancelled = false
    fetch('/scoreboard.json')
      .then((res) => (res.ok ? res.json() : null))
      .then((data: ScoreboardLedger | null) => {
        if (!cancelled && data && Array.isArray(data.tests)) setLedger(data)
      })
      .catch(() => {
        /* the ledger is an overlay, not a dependency */
      })
    return () => {
      cancelled = true
    }
  }, [])

  return ledger
}
