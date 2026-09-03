/**
 * Server-side proxy for the CoinGecko calls the pump tracker cannot make itself.
 *
 * CORRECTION, verified from a real browser: an earlier version of this comment
 * claimed /coins/markets and /derivatives send no CORS headers. Only
 * /derivatives actually fails from a browser — /coins/markets, /simple/price and
 * /coins/{id}/market_chart all send `access-control-allow-origin: *` and are now
 * fetched client-side.
 *
 * That matters because of the second constraint, which is the real one: the free
 * tier rate-limits per IP, and Vercel's edge addresses are shared across its
 * customers, so this function is 429ed far more often than any single visitor
 * would be. Proxying everything through here meant one rate limit killed the page
 * for everyone. So the browser calls what it can, and this endpoint exists for
 * /derivatives plus as a cached backup — with the hourly committed snapshot in
 * dashboard/public/derivatives-snapshot.json behind it.
 */

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

export const config = { runtime: 'edge' }

/**
 * /coins/markets is the richer endpoint but also the one CoinGecko rate-limits
 * first. /simple/price costs far less and still carries price, market cap,
 * volume and the 24h change — everything the verdict sentence and the peer bars
 * need. Reshaped into the same rows so the client cannot tell the difference
 * apart from the fields that are genuinely absent (24h high/low, 7d, 30d).
 */
async function fallbackMarkets(): Promise<Array<Record<string, unknown>> | null> {
  const res = await fetch(
    `${CG}/simple/price?ids=${PEER_IDS}&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true`,
    { headers: { accept: 'application/json' } },
  )
  if (!res.ok) return null
  const raw = (await res.json()) as Record<string, Record<string, number>>

  const NAMES: Record<string, [string, string]> = {
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

  const rows = Object.entries(raw).map(([id, v]) => ({
    id,
    symbol: NAMES[id]?.[0] ?? id,
    name: NAMES[id]?.[1] ?? id,
    current_price: v.usd,
    market_cap: v.usd_market_cap,
    total_volume: v.usd_24h_vol,
    price_change_percentage_24h: v.usd_24h_change,
    // Absent from this endpoint. Null rather than zero: the client renders a
    // dash for these, and a zero would read as a real measurement.
    high_24h: null,
    low_24h: null,
    price_change_percentage_7d_in_currency: null,
    price_change_percentage_30d_in_currency: null,
  }))
  return rows.length ? rows : null
}

export default async function handler(): Promise<Response> {
  try {
    const [marketsRes, derivsRes] = await Promise.all([
      fetch(
        `${CG}/coins/markets?vs_currency=usd&ids=${PEER_IDS}&price_change_percentage=24h,7d,30d`,
        { headers: { accept: 'application/json' } },
      ),
      fetch(`${CG}/derivatives?include_tickers=unexpired`, {
        headers: { accept: 'application/json' },
      }),
    ])

    // Degrade rather than die. Losing the derivatives leg costs the funding and
    // leverage readings; losing the rich markets leg costs 24h high/low and the
    // 7d/30d changes. Either is far better than the blank "could not load"
    // page the reader used to get whenever the free tier rate-limited.
    let markets: Array<Record<string, unknown>> | null = marketsRes.ok
      ? ((await marketsRes.json()) as Array<Record<string, unknown>>)
      : null
    let degraded: string | null = null

    if (!markets?.length) {
      markets = await fallbackMarkets()
      degraded = markets ? 'reduced' : null
    }

    if (!markets?.length) {
      return Response.json(
        {
          error: `upstream ${marketsRes.status}`,
          hint: marketsRes.status === 429 ? 'CoinGecko rate limit — try again in a minute' : undefined,
        },
        { status: 503, headers: { 'cache-control': 's-maxage=15' } },
      )
    }

    const derivatives = derivsRes.ok
      ? ((await derivsRes.json()) as Array<Record<string, unknown>>)
      : []

    // Only EGLD perps matter here, and the full derivatives payload is large.
    const venues = derivatives
      .filter((d) => String(d.symbol ?? '').toUpperCase().startsWith('EGLD'))
      .map((d) => ({
        market: String(d.market ?? '?'),
        open_interest: Number(d.open_interest ?? 0),
        volume_24h: Number(d.volume_24h ?? 0),
        funding_rate: d.funding_rate == null ? null : Number(d.funding_rate),
      }))
      .sort((a, b) => b.open_interest - a.open_interest)

    return Response.json(
      { markets, venues, degraded, fetchedAt: new Date().toISOString() },
      {
        headers: {
          // One upstream call a minute regardless of traffic; serve the stale
          // copy for up to five minutes while the refresh happens behind it. A
          // degraded response gets a shorter TTL so the full one returns sooner.
          'cache-control': degraded
            ? 's-maxage=30, stale-while-revalidate=300'
            : 's-maxage=60, stale-while-revalidate=300',
        },
      },
    )
  } catch (e) {
    return Response.json(
      { error: (e as Error).message || 'proxy failed' },
      { status: 502, headers: { 'cache-control': 's-maxage=15' } },
    )
  }
}
