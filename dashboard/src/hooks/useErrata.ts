import { useEffect, useState } from 'react'
import type { Errata, WithdrawnClaim } from '../types/report'

/**
 * The report archive is immutable, so a reader opening run #19 today sees a
 * claim that run #21 withdrew, asserted with full confidence. errata.json is
 * aggregated across every report by generate-manifest.ts; this hook loads it
 * once and exposes the claims that a given run asserted.
 *
 * Deliberately non-blocking: a missing or malformed errata file must never stop
 * a report from rendering.
 */
export function useErrata(): Errata | null {
  const [errata, setErrata] = useState<Errata | null>(null)

  useEffect(() => {
    let cancelled = false
    fetch('/errata.json')
      .then((res) => (res.ok ? res.json() : null))
      .then((data: Errata | null) => {
        if (!cancelled && data && Array.isArray(data.claims)) setErrata(data)
      })
      .catch(() => {
        /* errata is an overlay, not a dependency */
      })
    return () => {
      cancelled = true
    }
  }, [])

  return errata
}

/** Claims this run asserted and a later run withdrew. */
export function supersededClaims(
  errata: Errata | null,
  runNumber: number | null | undefined,
): WithdrawnClaim[] {
  if (!errata || runNumber == null) return []
  return errata.claims.filter(
    (c) =>
      c.asserted_in_runs.includes(runNumber) && c.withdrawn_in_run > runNumber,
  )
}

/** Claims this run itself withdrew — shown as the run's own corrections. */
export function ownWithdrawals(
  errata: Errata | null,
  runNumber: number | null | undefined,
): WithdrawnClaim[] {
  if (!errata || runNumber == null) return []
  return errata.claims.filter((c) => c.withdrawn_in_run === runNumber)
}
