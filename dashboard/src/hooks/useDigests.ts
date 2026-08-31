import { useState, useEffect, useCallback } from 'react'

const REPO_OWNER = 'lamentierschweinchen'
const REPO_NAME = 'proof-of-progress'
const DIGESTS_PATH = 'digests'

export interface DigestEntry {
  date: string
  filename: string
  downloadUrl: string
  htmlUrl: string
  sha: string
}

interface UseDigestsResult {
  manifest: DigestEntry[]
  selectedDate: string
  setSelectedDate: (date: string) => void
  content: string | null
  loading: boolean
  error: string | null
  retry: () => void
  lastFetchedAt: number | null
}

interface GhContentEntry {
  name: string
  path: string
  sha: string
  download_url: string
  html_url: string
  type: string
}

/**
 * Fetches the digest manifest from GitHub's contents API, then the markdown
 * file body from raw.githubusercontent.com. Public repo, no auth needed.
 *
 * Rate limit: 60 requests/hour for unauthenticated GitHub API. Each page view
 * costs 1 contents request + 1 raw file fetch (raw doesn't count against API limit).
 */
export function useDigests(): UseDigestsResult {
  const [manifest, setManifest] = useState<DigestEntry[]>([])
  const [selectedDate, setSelectedDate] = useState<string>('')
  const [content, setContent] = useState<string | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)
  const [lastFetchedAt, setLastFetchedAt] = useState<number | null>(null)

  // Load manifest from GitHub contents API
  useEffect(() => {
    let cancelled = false

    async function loadManifest() {
      setLoading(true)
      setError(null)

      try {
        const res = await fetch(
          `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${DIGESTS_PATH}`,
          {
            headers: { Accept: 'application/vnd.github+json' },
          },
        )
        if (!res.ok) {
          throw new Error(`GitHub API ${res.status}`)
        }
        const files: GhContentEntry[] = await res.json()

        const digests: DigestEntry[] = files
          .filter(
            (f) => f.type === 'file' && /^\d{4}-\d{2}-\d{2}\.md$/.test(f.name),
          )
          .map((f) => ({
            date: f.name.replace('.md', ''),
            filename: f.name,
            downloadUrl: f.download_url,
            htmlUrl: f.html_url,
            sha: f.sha,
          }))
          .sort((a, b) => b.date.localeCompare(a.date)) // newest first

        if (!cancelled) {
          setManifest(digests)
          setLastFetchedAt(Date.now())
          // Default to most recent digest on first load
          if (digests.length > 0) {
            setSelectedDate((prev) => prev || digests[0].date)
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : 'Failed to load digests',
          )
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

  // Fetch the selected digest's markdown body
  useEffect(() => {
    if (!selectedDate) return
    const entry = manifest.find((d) => d.date === selectedDate)
    if (!entry) return

    let cancelled = false

    async function loadDigest() {
      setLoading(true)
      setError(null)
      setContent(null)

      try {
        const res = await fetch(entry!.downloadUrl)
        if (!res.ok) {
          throw new Error(
            `Failed to load digest for ${selectedDate} (HTTP ${res.status})`,
          )
        }
        const text = await res.text()

        if (!cancelled) {
          setContent(text)
          setLoading(false)
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : `Failed to load ${selectedDate}`,
          )
          setLoading(false)
        }
      }
    }

    loadDigest()
    return () => {
      cancelled = true
    }
  }, [manifest, selectedDate])

  const retry = useCallback(() => {
    setError(null)
    setRetryCount((c) => c + 1)
  }, [])

  return {
    manifest,
    selectedDate,
    setSelectedDate,
    content,
    loading,
    error,
    retry,
    lastFetchedAt,
  }
}
