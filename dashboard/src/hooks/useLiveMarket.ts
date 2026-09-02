import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Live market state for the pump tracker.
 *
 * Fetched client-side rather than through a serverless proxy on purpose: both
 * upstreams send `access-control-allow-origin: *`, and CoinGecko's free tier is
 * rate-limited per IP. Calling from each visitor's own browser spreads the limit
 * across readers instead of funnelling every visit through one server IP, which
 * is what would actually break if this page found an audience.
 *
 * Five requests per refresh: one market snapshot, one derivatives sweep, one
 * chain economics call, and one balance call per OTC desk.
 */

const CG = 'https://api.coingecko.com/api/v3'
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

const PEER_IDS = [
  'elrond-erd-2',
  'bitcoin',
  'ethereum',
  'solana',
  'polkadot',
  'avalanche-2',
  'cosmos',
  'near',
  'algorand',
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
  const [markets, derivatives, economics, ...deskAccounts] = await Promise.all([
    getJson(
      `${CG}/coins/markets?vs_currency=usd&ids=${PEER_IDS.join(',')}&price_change_percentage=24h,7d,30d`,
      signal,
    ),
    getJson(`${CG}/derivatives?include_tickers=unexpired`, signal),
    getJson(`${MX}/economics`, signal),
    ...DESKS.map((d) => getJson(`${MX}/accounts/${d.address}`, signal)),
  ])

  const rows = (markets as Array<Record<string, unknown>>) ?? []
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

  const venues: PerpVenue[] = ((derivatives as Array<Record<string, unknown>>) ?? [])
    .filter((d) => String(d.symbol ?? '').toUpperCase().startsWith('EGLD'))
    .map((d) => ({
      market: String(d.market ?? '?'),
      openInterest: Number(d.open_interest ?? 0),
      volume24h: Number(d.volume_24h ?? 0),
      funding: d.funding_rate == null ? null : Number(d.funding_rate),
    }))
    .sort((a, b) => b.openInterest - a.openInterest)

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
