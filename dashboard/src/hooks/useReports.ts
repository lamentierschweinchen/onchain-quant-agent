import { useState, useEffect, useCallback } from 'react'
import type { ManifestEntry, WeeklyReport } from '../types/report'

interface UseReportsResult {
  manifest: ManifestEntry[]
  selectedDate: string
  setSelectedDate: (date: string) => void
  report: WeeklyReport | null
  loading: boolean
  error: string | null
  retry: () => void
}

export function useReports(): UseReportsResult {
  const [manifest, setManifest] = useState<ManifestEntry[]>([])
  const [selectedDate, setSelectedDate] = useState<string>('')
  const [report, setReport] = useState<WeeklyReport | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  // Bump this to trigger a retry without changing other deps.
  const [retryCount, setRetryCount] = useState(0)

  // Load manifest on mount (and on retry).
  useEffect(() => {
    let cancelled = false

    async function loadManifest() {
      setLoading(true)
      setError(null)

      try {
        const res = await fetch('/report-manifest.json')
        if (!res.ok) {
          throw new Error(`Failed to load manifest (HTTP ${res.status})`)
        }
        const data: ManifestEntry[] = await res.json()

        if (!cancelled) {
          setManifest(data)
          // Default to the most recent report (last entry).
          if (data.length > 0 && !selectedDate) {
            setSelectedDate(data[data.length - 1].date)
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load manifest')
          setLoading(false)
        }
      }
    }

    loadManifest()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [retryCount])

  // Load report whenever selectedDate changes.
  useEffect(() => {
    if (!selectedDate) return

    let cancelled = false

    async function loadReport() {
      setLoading(true)
      setError(null)
      setReport(null)

      try {
        const res = await fetch(`/reports/${selectedDate}.json`)
        if (!res.ok) {
          throw new Error(
            `Failed to load report for ${selectedDate} (HTTP ${res.status})`,
          )
        }
        const data: WeeklyReport = await res.json()

        if (!cancelled) {
          setReport(data)
          setLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : `Failed to load report for ${selectedDate}`,
          )
          setLoading(false)
        }
      }
    }

    loadReport()
    return () => {
      cancelled = true
    }
  }, [selectedDate])

  const retry = useCallback(() => {
    setError(null)
    setRetryCount((c) => c + 1)
  }, [])

  return {
    manifest,
    selectedDate,
    setSelectedDate,
    report,
    loading,
    error,
    retry,
  }
}
