import type { LiveMarket } from '../hooks/useLiveMarket'

/**
 * The page's derived read-outs, kept out of the component so the thresholds are
 * in one auditable place.
 *
 * Two rules learned the hard way:
 *
 * 1. COLOUR IS NOT SENTIMENT. Green and red mean price and desk direction only.
 *    A crowded short book is a condition, not good news; toning it green makes a
 *    non-trader read the whole page as a buy signal. Conditions are teal
 *    ("notable") or amber ("watch this").
 *
 * 2. STATES DESCRIBE, THEY DO NOT PREDICT. "Squeeze firing" is a forecast in an
 *    observation's clothes. "Shorts closing as price rises" is the same fact
 *    without the implied next candle.
 */

export type Tone = 'up' | 'down' | 'notable' | 'watch' | 'flat'

export interface Signal {
  state: string
  tone: Tone
  detail: string
  /** Short clause for the verdict sentence at the top of the page. */
  clause: string
}

/**
 * Thresholds flip a state the instant a value crosses them. At a 60-second
 * refresh a reading sitting near a boundary would flip every minute, and with
 * change-flashes on it would manufacture drama out of noise. So a state has to
 * travel `margin` past the boundary before it releases.
 */
function withHysteresis(
  value: number,
  bounds: { enter: number; exit: number },
  previouslyInside: boolean,
): boolean {
  return previouslyInside ? value > bounds.exit : value > bounds.enter
}

export function decoupling(d: LiveMarket, prev?: string): Signal {
  const gap = d.decouplingPp
  const wasAlone = prev === 'alone'
  const alone = withHysteresis(gap, { enter: 8, exit: 6 }, wasAlone)
  const laggingNow = withHysteresis(-gap, { enter: 8, exit: 6 }, prev === 'lagging')

  if (alone)
    return {
      state: 'Moving alone',
      tone: 'notable',
      clause: `up ${d.change24h.toFixed(0)}% while its peers are flat`,
      detail: `${gap >= 0 ? '+' : ''}${gap.toFixed(1)} percentage points clear of the median layer-1 peer. A move this far from the group is specific to MultiversX rather than the market.`,
    }
  if (laggingNow)
    return {
      state: 'Lagging its peers',
      tone: 'watch',
      clause: `lagging its peers by ${Math.abs(gap).toFixed(0)} points`,
      detail: `${gap.toFixed(1)} percentage points behind the median layer-1 peer.`,
    }
  return {
    state: 'Moving with the market',
    tone: 'flat',
    clause: 'moving with the rest of the market',
    detail: `${gap >= 0 ? '+' : ''}${gap.toFixed(1)} points against the median peer — inside the normal band.`,
  }
}

export function leverage(d: LiveMarket, prev?: string): Signal {
  const negShare = d.fundingVenues ? d.fundingNegative / d.fundingVenues : 0
  const heavy = d.oiShareOfMcap > 20
  const shortsCrowded = withHysteresis(negShare, { enter: 0.6, exit: 0.5 }, prev === 'shorts')
  const longsCrowded = withHysteresis(1 - negShare, { enter: 0.6, exit: 0.5 }, prev === 'longs')

  if (shortsCrowded)
    return {
      state: 'Shorts are paying to stay short',
      tone: heavy ? 'watch' : 'notable',
      clause: 'traders betting against it are paying to hold that bet',
      detail: `${d.fundingNegative} of ${d.fundingVenues} venues charge short sellers a fee paid to the other side. Leverage outstanding is ${d.oiShareOfMcap.toFixed(0)}% of market cap${heavy ? ', which is high enough that a forced unwind moves price hard in whichever direction it goes' : ''}.`,
    }
  if (longsCrowded)
    return {
      state: 'Longs are paying to stay long',
      tone: heavy ? 'watch' : 'notable',
      clause: 'traders betting on it are paying to hold that bet',
      detail: `Only ${d.fundingNegative} of ${d.fundingVenues} venues charge shorts, so the fee is running the other way. Leverage outstanding is ${d.oiShareOfMcap.toFixed(0)}% of market cap.`,
    }
  return {
    state: 'Neither side is crowded',
    tone: 'flat',
    clause: 'leverage is balanced between both sides',
    detail: `${d.fundingNegative} of ${d.fundingVenues} venues charge shorts. Leverage outstanding is ${d.oiShareOfMcap.toFixed(0)}% of market cap.`,
  }
}

/**
 * Deliberately says "left the desk", not "was sold". The balance falling means
 * EGLD moved out of two labelled addresses — it may have gone to an exchange, to
 * a buyer, or to another wallet of the same operator. Tracing the destination is
 * a separate job and this page has not done it.
 */
export function overhang(d: LiveMarket, peak: number, prev?: string): Signal {
  const t = d.deskTotal
  const staged = withHysteresis(t, { enter: 200_000, exit: 180_000 }, prev === 'staged')
  const cleared = withHysteresis(-t, { enter: -60_000, exit: -68_000 }, prev === 'cleared')
  const drained = peak > 0 ? peak - t : 0

  if (staged)
    return {
      state: 'Supply staged on the desks',
      tone: 'watch',
      clause: `${Math.round(t).toLocaleString()} EGLD is sitting on the trading desks`,
      detail: `${Math.round(t).toLocaleString()} EGLD held by the two wallets that fill large private orders. A rising balance means more is being positioned there.`,
    }
  if (cleared)
    return {
      state: 'Desks nearly empty',
      tone: 'notable',
      clause: `the desks are nearly empty at ${Math.round(t).toLocaleString()} EGLD`,
      detail: `Only ${Math.round(t).toLocaleString()} EGLD left on the desks, down ${Math.round(drained).toLocaleString()} from the ${Math.round(peak).toLocaleString()} peak.`,
    }
  return {
    state: 'Desk balance falling',
    tone: 'flat',
    clause: `${Math.round(t).toLocaleString()} EGLD is still staged on the desks, down from ${Math.round(peak).toLocaleString()}`,
    detail: `${Math.round(t).toLocaleString()} EGLD on the desks, ${Math.round(drained).toLocaleString()} lower than the ${Math.round(peak).toLocaleString()} peak. Where it went is not traced here.`,
  }
}

/**
 * Funding is charged on position notional every eight hours. Open interest is
 * the matched notional, so the daily transfer from one side to the other is
 * roughly OI x rate x 3. An estimate — venues differ on interval and on the
 * notional they report — but it turns "-0.087% mean funding" into a number a
 * non-trader can hold, and the arithmetic is shown so it can be checked.
 */
export function shortCostPerDay(d: LiveMarket): number | null {
  if (d.fundingMean == null) return null
  return Math.abs(d.openInterest * (d.fundingMean / 100) * 3)
}

export const TONE_TEXT: Record<Tone, string> = {
  up: 'text-up',
  down: 'text-down',
  notable: 'text-accent-cyan',
  watch: 'text-severity-medium',
  flat: 'text-text-secondary',
}

export const TONE_BG: Record<Tone, string> = {
  up: 'bg-up',
  down: 'bg-down',
  notable: 'bg-accent-cyan',
  watch: 'bg-severity-medium',
  flat: 'bg-text-muted',
}
