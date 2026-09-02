import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Live market state for the pump tracker.
 *
 * Price and derivatives come through /api/market, an edge function, because
 * CoinGecko does NOT send CORS headers on /coins/markets or /derivatives — a
 * browser fetch fails outright. Proxying also lets the edge cache the response
 * for 60s, so CoinGecko sees one call a minute however many people are reading.
 *
 * Chain data is fetched straight from the MultiversX API, which does send
 * permissive CORS and has no comparable rate limit.
 */

const MX = 'https://api.multiversx.com'

/** The two wallets that fill large private orders on this chain. Their stock of
 *  EGLD is supply staged for sale, and it is not published anywhere else. */
export const DESKS: Array<{ address: string; label: string }> = [
  {
    address: 'erd1v6x9egd2j5cmr57cugxukfnn647q2zuy57nu68t0y6qpu6ztaypshcxnk5',
    label: 'UPbit OTC Desk',
  },
  {
    address: 'erd1z7fnqf4mjknsx289t9qf9kv5yr2fts7uv8ssmuknq7546f8e6ceq2nm63r',
    label: 'OTC Distribution Wallet',
  },
]

export interface Peer {
  symbol: string
  name: string
  change24h: number
  price: number
}

export interface PerpVenue {
  market: string
  openInterest: number
  volume24h: number
  funding: number | null
}

export interface LiveMarket {
  price: number
  change24h: number
  change7d: number | null
  change30d: number | null
  high24h: number
  low24h: number
  marketCap: number
  volume24h: number
  peers: Peer[]
  /** EGLD 24h change minus the median peer change — how alone the move is. */
  decouplingPp: number
  openInterest: number
  oiShareOfMcap: number
  perpVolume: number
  fundingMean: number | null
  fundingNegative: number
  fundingVenues: number
  venues: PerpVenue[]
  deskTotal: number
  deskBreakdown: Array<{ label: string; egld: number }>
  stakedEgld: number
  stakedRatio: number
  fetchedAt: number
}

async function getJson(url: string, signal: AbortSignal): Promise<unknown> {
  const res = await fetch(url, { signal })
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

function median(xs: number[]): number {
  if (xs.length === 0) return 0
  const s = [...xs].sort((a, b) => a - b)
  const m = Math.floor(s.length / 2)
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2
}

async function load(signal: AbortSignal): Promise<LiveMarket> {
  const [proxied, economics, ...deskAccounts] = await Promise.all([
    getJson('/api/market', signal),
    getJson(`${MX}/economics`, signal),
    ...DESKS.map((d) => getJson(`${MX}/accounts/${d.address}`, signal)),
  ])

  const payload = proxied as {
    markets?: Array<Record<string, unknown>>
    venues?: Array<Record<string, unknown>>
    error?: string
  }
  if (payload.error) throw new Error(payload.error)

  const rows = payload.markets ?? []
  const egld = rows.find((r) => String(r.symbol).toLowerCase() === 'egld')
  if (!egld) throw new Error('EGLD not present in the market response')

  const peers: Peer[] = rows
    .filter((r) => String(r.symbol).toLowerCase() !== 'egld')
    .map((r) => ({
      symbol: String(r.symbol).toUpperCase(),
      name: String(r.name),
      change24h: Number(r.price_change_percentage_24h ?? 0),
      price: Number(r.current_price ?? 0),
    }))
    .sort((a, b) => b.change24h - a.change24h)

  const change24h = Number(egld.price_change_percentage_24h ?? 0)
  const marketCap = Number(egld.market_cap ?? 0)

  const venues: PerpVenue[] = (payload.venues ?? []).map((d) => ({
    market: String(d.market ?? '?'),
    openInterest: Number(d.open_interest ?? 0),
    volume24h: Number(d.volume_24h ?? 0),
    funding: d.funding_rate == null ? null : Number(d.funding_rate),
  }))

  const fundings = venues
    .map((v) => v.funding)
    .filter((f): f is number => f != null)
  const openInterest = venues.reduce((s, v) => s + v.openInterest, 0)

  const deskBreakdown = deskAccounts.map((acc, i) => ({
    label: DESKS[i].label,
    egld: Number((acc as { balance?: string }).balance ?? '0') / 1e18,
  }))

  const econ = economics as Record<string, number>

  return {
    price: Number(egld.current_price ?? 0),
    change24h,
    change7d: egld.price_change_percentage_7d_in_currency == null
      ? null
      : Number(egld.price_change_percentage_7d_in_currency),
    change30d: egld.price_change_percentage_30d_in_currency == null
      ? null
      : Number(egld.price_change_percentage_30d_in_currency),
    high24h: Number(egld.high_24h ?? 0),
    low24h: Number(egld.low_24h ?? 0),
    marketCap,
    volume24h: Number(egld.total_volume ?? 0),
    peers,
    decouplingPp: change24h - median(peers.map((p) => p.change24h)),
    openInterest,
    oiShareOfMcap: marketCap ? (100 * openInterest) / marketCap : 0,
    perpVolume: venues.reduce((s, v) => s + v.volume24h, 0),
    fundingMean: fundings.length
      ? fundings.reduce((s, f) => s + f, 0) / fundings.length
      : null,
    fundingNegative: fundings.filter((f) => f < 0).length,
    fundingVenues: fundings.length,
    venues,
    deskTotal: deskBreakdown.reduce((s, d) => s + d.egld, 0),
    deskBreakdown,
    stakedEgld: Number(econ.staked ?? 0),
    stakedRatio: econ.circulatingSupply
      ? Number(econ.staked) / Number(econ.circulatingSupply)
      : 0,
    fetchedAt: Date.now(),
  }
}

export function useLiveMarket(refreshMs = 60_000) {
  const [data, setData] = useState<LiveMarket | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const abortRef = useRef<AbortController | null>(null)

  const refresh = useCallback(async () => {
    abortRef.current?.abort()
    const ctrl = new AbortController()
    abortRef.current = ctrl
    try {
      const next = await load(ctrl.signal)
      setData(next)
      setError(null)
    } catch (e) {
      if ((e as Error).name === 'AbortError') return
      // Keep the last good snapshot on screen; a stale number beats an empty page.
      setError((e as Error).message || 'Could not reach the data sources')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, refreshMs)
    return () => {
      clearInterval(id)
      abortRef.current?.abort()
    }
  }, [refresh, refreshMs])

  return { data, error, loading, refresh }
}
