/**
 * Long-range price history for the pump tracker's "bigger picture" panel.
 *
 * Separate from /api/market because the cadence is completely different: the
 * live tiles want a fresh reading every minute, whereas a year of daily closes
 * changes once a day. Caching them together would mean either re-fetching a year
 * of history every minute or serving stale prices, so they get their own edge
 * cache with an hour-long TTL.
 *
 * The client calls CoinGecko directly first — /coins/{id}/market_chart does send
 * `access-control-allow-origin: *`, contrary to what an earlier comment here
 * claimed. This endpoint is the second try, useful because its edge cache serves
 * visitors whose own IP is being rate-limited.
 */

const CG = 'https://api.coingecko.com/api/v3'
const ID = 'elrond-erd-2'

export const config = { runtime: 'edge' }

/** [timestampMs, price] pairs, rounded and thinned to keep the payload small. */
type Pair = [number, number]

function thin(pairs: Pair[], target: number): Pair[] {
  if (pairs.length <= target) return pairs
  const step = pairs.length / target
  const out: Pair[] = []
  for (let i = 0; i < target; i++) out.push(pairs[Math.floor(i * step)])
  // Always keep the true final point — it is the one the reader checks.
  const last = pairs[pairs.length - 1]
  if (out[out.length - 1][0] !== last[0]) out.push(last)
  return out
}

function clean(raw: unknown, target: number): Pair[] {
  const pairs = (raw as Pair[] | undefined) ?? []
  return thin(pairs, target).map(([t, p]) => [t, Number(p.toFixed(4))] as Pair)
}

export default async function handler(): Promise<Response> {
  try {
    // days=365 comes back daily; days=30 comes back hourly. Both are what the
    // two zoom levels want, so no interval parameter is passed (it is a paid
    // feature on some plans and the defaults are already correct).
    const [yearRes, monthRes] = await Promise.all([
      fetch(`${CG}/coins/${ID}/market_chart?vs_currency=usd&days=365&interval=daily`, {
        headers: { accept: 'application/json' },
      }),
      fetch(`${CG}/coins/${ID}/market_chart?vs_currency=usd&days=30`, {
        headers: { accept: 'application/json' },
      }),
    ])

    // Return whichever leg succeeded rather than failing both. The free tier
    // rate-limits per IP, and losing only the 30-day zoom is much better than
    // losing the whole panel — the client falls back to its committed snapshot
    // for the missing half.
    const year = yearRes.ok ? clean(((await yearRes.json()) as Record<string, unknown>).prices, 400) : []
    const month = monthRes.ok ? clean(((await monthRes.json()) as Record<string, unknown>).prices, 360) : []

    if (!year.length && !month.length) {
      return Response.json(
        {
          error: `upstream ${yearRes.status}/${monthRes.status}`,
          hint:
            yearRes.status === 429 || monthRes.status === 429
              ? 'CoinGecko rate limit — the client falls back to its committed snapshot'
              : undefined,
        },
        { status: 503, headers: { 'cache-control': 's-maxage=60' } },
      )
    }

    return Response.json(
      { year, month, fetchedAt: new Date().toISOString() },
      {
        headers: {
          'cache-control': 's-maxage=3600, stale-while-revalidate=86400',
        },
      },
    )
  } catch (e) {
    return Response.json(
      { error: (e as Error).message || 'proxy failed' },
      { status: 502, headers: { 'cache-control': 's-maxage=60' } },
    )
  }
}
