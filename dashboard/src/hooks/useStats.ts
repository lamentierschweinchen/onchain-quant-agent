import { useState, useEffect, useCallback } from 'react'
import type { ProgressStats } from '../types/stats'

const STATS_URL =
  'https://raw.githubusercontent.com/lamentierschweinchen/proof-of-progress/main/data/stats.json'

interface UseStatsResult {
  stats: ProgressStats | null
  loading: boolean
  error: string | null
  retry: () => void
}

export function useStats(): UseStatsResult {
  const [stats, setStats] = useState<ProgressStats | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function loadStats() {
      setLoading(true)
      setError(null)

      try {
        // Cache-bust so we get fresh stats when a new commit lands.
        const res = await fetch(`${STATS_URL}?t=${Date.now()}`)
        if (!res.ok) {
          if (res.status === 404) {
            // No stats yet — not really an error, just empty state.
            if (!cancelled) {
              setStats(null)
              setError(null)
              setLoading(false)
            }
            return
          }
          throw new Error(`HTTP ${res.status}`)
        }
        const data: ProgressStats = await res.json()
        if (!cancelled) {
          setStats(data)
          setLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load stats')
          setLoading(false)
        }
      }
    }

    loadStats()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [retryCount])

  const retry = useCallback(() => {
    setError(null)
    setRetryCount((c) => c + 1)
  }, [])

  return { stats, loading, error, retry }
}
