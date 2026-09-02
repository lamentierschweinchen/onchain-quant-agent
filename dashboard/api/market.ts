/**
 * Server-side proxy for the CoinGecko calls the pump tracker needs.
 *
 * Two reasons this cannot be done from the browser:
 *
 *  1. CORS. CoinGecko sends `access-control-allow-origin: *` on some endpoints
 *     (/simple/price) but NOT on /coins/markets or /derivatives, which are the
 *     two this page actually needs. A client-side fetch fails outright.
 *  2. Rate limits. The free tier is limited per IP. Fetching here and caching at
 *     the edge means CoinGecko sees one request a minute no matter how many
 *     people load the page — which is the behaviour that matters if it finds an
 *     audience.
 *
 * MultiversX's own API does send permissive CORS, so chain data is still fetched
 * directly by the browser and is not proxied here.
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

    if (!marketsRes.ok || !derivsRes.ok) {
      return Response.json(
        {
          error: `upstream ${marketsRes.status}/${derivsRes.status}`,
          hint:
            marketsRes.status === 429 || derivsRes.status === 429
              ? 'CoinGecko rate limit — the cached copy will serve until it clears'
              : undefined,
        },
        // Let the edge keep serving the previous good copy rather than blanking.
        { status: 503, headers: { 'cache-control': 's-maxage=15' } },
      )
    }

    const [markets, derivatives] = await Promise.all([
      marketsRes.json(),
      derivsRes.json(),
    ])

    // Only EGLD perps matter here, and the full derivatives payload is large.
    const venues = (derivatives as Array<Record<string, unknown>>)
      .filter((d) => String(d.symbol ?? '').toUpperCase().startsWith('EGLD'))
      .map((d) => ({
        market: String(d.market ?? '?'),
        open_interest: Number(d.open_interest ?? 0),
        volume_24h: Number(d.volume_24h ?? 0),
        funding_rate: d.funding_rate == null ? null : Number(d.funding_rate),
      }))
      .sort((a, b) => b.open_interest - a.open_interest)

    return Response.json(
      { markets, venues, fetchedAt: new Date().toISOString() },
      {
        headers: {
          // One upstream call a minute regardless of traffic; serve the stale
          // copy for up to five minutes while the refresh happens behind it.
          'cache-control': 's-maxage=60, stale-while-revalidate=300',
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
