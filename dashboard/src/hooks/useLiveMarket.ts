import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Live market state for the pump tracker.
 *
 * DATA PATHS, and why they are shaped like this:
 *
 * Price and peers are fetched DIRECTLY from CoinGecko by the browser. An earlier
 * version proxied them through /api/market on the belief that /coins/markets
 * sends no CORS headers. That was wrong — it sends `access-control-allow-origin:
 * *`, verified from a real browser. What actually happens is worse and less
 * obvious: CoinGecko's free tier rate-limits per IP, Vercel's edge IPs are
 * shared across its customers, so the proxy gets 429ed more or less permanently
 * and every visitor sees the same dead page. Fetching from the browser gives
 * each visitor their own rate budget, which is the only version of this that
 * scales on a free tier.
 *
 * /derivatives is the exception: it genuinely fails from a browser, so it still
 * goes through the proxy, with a committed periodic snapshot behind it for when
 * the proxy is rate-limited.
 *
 * Chain data comes straight from the MultiversX API, which has permissive CORS
 * and no comparable limit.
 */

const MX = 'https://api.multiversx.com'
const CG = 'https://api.coingecko.com/api/v3'

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
].join(',')

/** Committed by the scheduled workflow, so funding survives a rate-limited proxy. */
const VENUE_SNAPSHOTS = [
  'https://raw.githubusercontent.com/lamentierschweinchen/onchain-quant-agent/main/dashboard/public/derivatives-snapshot.json',
  '/derivatives-snapshot.json',
]

/** The two wallets that fill large private orders on this chain. Their stock of
 *  EGLD is supply staged for sale, and it is not published anywhere else. */
/**
 * The wallet that refills the desks. Found on 3 Sep 2026 by asking where a
 * 150,000 EGLD inbound transfer came from, after the history series showed the
 * desk balance jumping 36K -> 169K in ten hours — a swing no inventory being
 * sold down could make. It has sent the desks 302,000 EGLD in three days and
 * still holds over a million, which is why this page no longer describes the
 * desk balance as supply running out.
 */
export const RESERVOIR = {
  address: 'erd1fcxu3f0hlxyvnp7zvuqmf34zf5w782tst6vuqhm4dwq4ayjspdaqce0q49',
  label: 'Desk reservoir',
}

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
  /** Null when the proxy is serving its reduced fallback. */
  high24h: number | null
  low24h: number | null
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
  /** EGLD held by the wallet that refills the desks. */
  reservoirEgld: number
  stakedEgld: number
  stakedRatio: number
  fetchedAt: number
  /** Set when the cheapest price endpoint was used and some fields are absent. */
  degraded?: string | null
  /** Set when funding/leverage came from the committed snapshot, not live. */
  venuesAsOf?: string | null
}

/** Last good snapshot, so a cold load during a rate limit is not a blank page. */
const CACHE_KEY = 'pump-last-good'

function readCache(): LiveMarket | null {
  try {
    const raw = localStorage.getItem(CACHE_KEY)
    if (!raw) return null
    const d = JSON.parse(raw) as LiveMarket
    // Anything older than a day is more misleading than useful.
    return Date.now() - d.fetchedAt < 86_400_000 ? d : null
  } catch {
    return null
  }
}

function writeCache(d: LiveMarket): void {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(d))
  } catch {
    /* private mode or quota — the cache is an optimisation, not a requirement */
  }
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

type Row = Record<string, unknown>

/** Reshape /simple/price into the row shape the rest of the file expects. */
const SIMPLE_NAMES: Record<string, [string, string]> = {
  'elrond-erd-2': ['egld', 'MultiversX'],
  bitcoin: ['btc', 'Bitcoin'],
  ethereum: ['eth', 'Ethereum'],
  solana: ['sol', 'Solana'],
  polkadot: ['dot', 'Polkadot'],
  'avalanche-2': ['avax', 'Avalanche'],
  cosmos: ['atom', 'Cosmos Hub'],
  near: ['near', 'NEAR Protocol'],
  algorand: ['algo', 'Algorand'],
}

function fromSimplePrice(raw: Record<string, Record<string, number>>): Row[] {
  return Object.entries(raw).map(([id, v]) => ({
    symbol: SIMPLE_NAMES[id]?.[0] ?? id,
    name: SIMPLE_NAMES[id]?.[1] ?? id,
    current_price: v.usd,
    market_cap: v.usd_market_cap,
    total_volume: v.usd_24h_vol,
    price_change_percentage_24h: v.usd_24h_change,
    // Genuinely absent from this endpoint — null, not zero, so the UI can say so.
    high_24h: null,
    low_24h: null,
    price_change_percentage_7d_in_currency: null,
    price_change_percentage_30d_in_currency: null,
  }))
}

async function load(signal: AbortSignal): Promise<LiveMarket> {
  // The browser's own IP has its own rate budget, so the direct call is tried
  // first and the proxy is the backup, not the other way round.
  const directMarkets = getJson(
    `${CG}/coins/markets?vs_currency=usd&ids=${PEER_IDS}&price_change_percentage=24h,7d,30d`,
    signal,
  ).catch(() => null)
  const proxy = getJson('/api/market', signal).catch(() => null)

  const [direct, proxied, economics, ...accounts] = await Promise.all([
    directMarkets,
    proxy,
    getJson(`${MX}/economics`, signal),
    ...DESKS.map((d) => getJson(`${MX}/accounts/${d.address}`, signal)),
    getJson(`${MX}/accounts/${RESERVOIR.address}`, signal),
  ])

  const payload = (proxied ?? {}) as {
    markets?: Row[]
    venues?: Row[]
    fetchedAt?: string
  }

  let rows = (direct as Row[] | null) ?? null
  let degraded: string | null = null

  if (!rows?.length && payload.markets?.length) rows = payload.markets

  if (!rows?.length) {
    // Last resort: the cheapest endpoint there is. Loses 24h high/low and the
    // 7d/30d changes, keeps everything the verdict sentence needs.
    const simple = await getJson(
      `${CG}/simple/price?ids=${PEER_IDS}&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true`,
      signal,
    ).catch(() => null)
    if (simple) {
      rows = fromSimplePrice(simple as Record<string, Record<string, number>>)
      degraded = 'reduced'
    }
  }

  if (!rows?.length) throw new Error('No price source responded')

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

  // Derivatives: proxy first, then the committed snapshot. Losing this costs the
  // funding and leverage readings but must not cost the whole page.
  let venueRows = payload.venues ?? []
  let venuesAsOf: string | null = null
  if (!venueRows.length) {
    for (const url of VENUE_SNAPSHOTS) {
      const snap = (await getJson(url, signal).catch(() => null)) as
        | { venues?: Row[]; fetchedAt?: string }
        | null
      if (snap?.venues?.length) {
        venueRows = snap.venues
        venuesAsOf = snap.fetchedAt ?? null
        break
      }
    }
  }

  const venues: PerpVenue[] = venueRows.map((d) => ({
    market: String(d.market ?? '?'),
    openInterest: Number(d.open_interest ?? 0),
    volume24h: Number(d.volume_24h ?? 0),
    funding: d.funding_rate == null ? null : Number(d.funding_rate),
  }))

  const fundings = venues.map((v) => v.funding).filter((f): f is number => f != null)
  const openInterest = venues.reduce((s, v) => s + v.openInterest, 0)

  const balanceOf = (acc: unknown): number => {
    const raw = (acc as { balance?: string } | null)?.balance
    // Defaulting a missing balance to 0 would silently understate the desks and
    // read as a drain that never happened, so an absent field is NaN, not zero.
    return raw == null ? NaN : Number(raw) / 1e18
  }
  const deskAccounts = accounts.slice(0, DESKS.length)
  const deskBreakdown = deskAccounts.map((acc, i) => ({
    label: DESKS[i].label,
    egld: balanceOf(acc),
  }))
  const reservoirEgld = balanceOf(accounts[DESKS.length])

  const econ = economics as Record<string, number>

  return {
    price: Number(egld.current_price ?? 0),
    change24h,
    change7d:
      egld.price_change_percentage_7d_in_currency == null
        ? null
        : Number(egld.price_change_percentage_7d_in_currency),
    change30d:
      egld.price_change_percentage_30d_in_currency == null
        ? null
        : Number(egld.price_change_percentage_30d_in_currency),
    high24h: egld.high_24h == null ? null : Number(egld.high_24h),
    low24h: egld.low_24h == null ? null : Number(egld.low_24h),
    marketCap,
    volume24h: Number(egld.total_volume ?? 0),
    peers,
    decouplingPp: change24h - median(peers.map((p) => p.change24h)),
    openInterest,
    oiShareOfMcap: marketCap ? (100 * openInterest) / marketCap : 0,
    perpVolume: venues.reduce((s, v) => s + v.volume24h, 0),
    fundingMean: fundings.length ? fundings.reduce((s, f) => s + f, 0) / fundings.length : null,
    fundingNegative: fundings.filter((f) => f < 0).length,
    fundingVenues: fundings.length,
    venues,
    deskTotal: deskBreakdown.reduce((s, d) => s + d.egld, 0),
    deskBreakdown,
    reservoirEgld,
    stakedEgld: Number(econ.staked ?? 0),
    stakedRatio: econ.circulatingSupply ? Number(econ.staked) / Number(econ.circulatingSupply) : 0,
    fetchedAt: Date.now(),
    degraded,
    venuesAsOf,
  }
}

export function useLiveMarket(refreshMs = 60_000) {
  // Hydrate from the last good reading so the page has real numbers on screen
  // immediately, including when the upstream is rate-limiting a cold visitor.
  const [data, setData] = useState<LiveMarket | null>(readCache)
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
      writeCache(next)
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
