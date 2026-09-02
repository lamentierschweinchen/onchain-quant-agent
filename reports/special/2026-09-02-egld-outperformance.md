# EGLD's 24-Hour Outperformance — Special Report

**Generated**: 2026-09-02 18:07 UTC · ad-hoc, outside the weekly cycle
**Baseline**: the run #23 weekly snapshot, 2026-08-31 (48h prior)
**Price**: $4.66 · +18.84% (24h) · +37.3% (7d) · +21.2% since the run #23 report

---

## The claim, corrected

EGLD is **#7 of 487** coins by 24-hour performance, not #1 — but the six above it
are memecoins and illiquid tokens, two of which barely trade:

| Rank | Asset | 24h | Market cap | 24h volume | Volume/mcap |
|---|---|---|---|---|---|
| 1 | AKE | +76.37% | $350M | $116.4M | 33.2% |
| 2 | MAGMA | +40.80% | $103M | $4.6M | 4.5% |
| 3 | T | +37.46% | $55M | $141.3M | 255.5% |
| 4 | CASHCAT | +31.01% | $252M | $97.6M | 38.7% |
| 5 | AIX | +24.78% | $81M | $0.3M | 0.4% |
| 6 | A7A5 | +19.67% | $451M | **$0.0M** | 0.0% |
| **7** | **EGLD** | **+18.84%** | **$143M** | **$25.1M** | **17.6%** |

Filtered to assets with at least $100M market cap **and** $20M of real volume,
EGLD is **#3 of 17**, behind two memecoins. Among established layer-1 protocol
tokens it is unambiguously first, and it is not close:

| Asset | 24h | 7d |
|---|---|---|
| **EGLD** | **+18.84%** | **+37.3%** |
| ALGO | +4.90% | +5.2% |
| BTC | +0.24% | -0.8% |
| SOL | -0.71% | +3.4% |
| ETH | -0.86% | -2.1% |
| AVAX | -0.93% | -0.7% |
| ATOM | -1.06% | -2.3% |
| DOT | -1.64% | +2.8% |
| NEAR | -3.69% | +1.7% |

EGLD is **+18.60pp against BTC** and **+19.70pp against ETH** over 24 hours, with
the entire L1 peer group flat to negative. This is the cleanest EGLD-specific
decoupling in the tracked series — stronger than run #16's +15.93% against a flat
tape, and the opposite of run #22's +30.43%, which was pure beta.

---

## Contributing factors

### 1. Supernova activates on 10 September — eight days out

The upgrade is scheduled for **10 September at epoch 2233**, with a node migration
window that **opened on 1 September** — the day this move began.

| Metric | Before | After |
|---|---|---|
| Block time | 6s | 600ms |
| Intra-shard finality | ~6s | below 250ms |
| Cross-shard settlement | ~18s | ~2.4s |

Activation requires mainnet to stop accepting new pool transactions for roughly
240 rounds — about **24 minutes** — after which queued transactions resume.

This is a dated, protocol-level catalyst whose timing lines up exactly with the
move. It is the only specific catalyst identifiable, and no token-economic change
accompanies it: no supply, staking or fee changes were announced.

### 2. The on-chain data does NOT corroborate a demand story

Every participation instrument moved the wrong way for a demand-led rally:

| Instrument | 48h change | Read |
|---|---|---|
| Staked EGLD | **-29,433** | unstaking into strength |
| Staked ratio | **-0.128pp** to 47.297% | falling |
| Delegated total | **-30,788** | falling |
| Delegator count | **-58** | flat, as for twelve weeks |
| SEGLD supply | -0.36% | no subscription |
| XEGLD supply | -0.11% | no subscription |
| SWTAO supply | -1.31% | redemption |
| USDC supply | -0.51% | dollars leaving |
| USDT supply | -0.20% | dollars leaving |

Trading activity did rise — DEX volume $234K → $316K (+35%), and **+11.5% measured
in EGLD rather than dollars**, so it is not purely the price. Pool TVL +17.3%,
turnover 10.51% → 12.11%. But that measures people trading, not people holding.

The one constructive holding-side signal is **USH +1.03%** — the first mint after
two consecutive burn weeks. Per the run #16 rule, a USH mint is CDP borrowers
opening leveraged positions. Leverage is returning.

### 3. A caveat on the catalyst itself

Scanning the node fleet for Supernova-capable software: across a full sweep of
**1,566 observers** and a **2,100-validator sample**, I found **no nodes on the
v2.x branch** that carries the Supernova code (v2.0.3, released 10 August, is the
first release whose notes reference it). 92.8–98% sit on v1.11.11.0, the newest
pre-Supernova tag.

**Stated as a question, not a conclusion**: the release notes do not say which tag
mainnet requires, so it is possible the mainnet Supernova build is a v1.11.x tag
and this scan cannot distinguish it. If it is not, the migration has barely begun
eight days before a hard fork. Worth resolving before treating 10 September as
certain.

---

## How large players are positioned

### The record supply overhang is being delivered into the strength

Run #23 closed with the largest staged supply position ever recorded and an open
question about whether it would drain. It is draining.

| | 2026-08-31 | 2026-09-02 | Change |
|---|---|---|---|
| Combined OTC desk inventory | 266,213 | **133,150** | **-133,063** |
| UPbit OTC Desk | 132,505 | 66,338 | -66,167 |
| OTC Distribution Wallet | 133,708 | 66,812 | -66,896 |

Both desks halved, almost symmetrically. Over the 48 hours the desks moved
**640,200 EGLD out** against 423,917 in — 47% circular, leaving **338,919 of
genuine one-way movement**, resolved two hops to venue:

| Venue | Desk → venue | Venue → desk | Net |
|---|---|---|---|
| UPbit | 232,827 | 92,000 | **+140,827** |
| Binance.com | 124,552 | 83,187 | +41,365 |
| Gate.io | 28,568 | 0 | +28,568 |
| Bybit | 146,498 | 126,093 | +20,404 |

**The last 24 hours look different from the 48**, and worse. UPbit flipped from net
receiver to **net source (-74,857)**, feeding 92,000 back into the desks, while the
desks delivered to Bybit (+24,936), Binance.com (+21,842) and Gate.io (+16,395).
The first day cleared inventory back to UPbit; the second day resumed pushing it
onto order books.

Circularity of 47% sits well below the historical 63–80% band — the diagnostic
established in run #21 for a wave whose feed and drain legs straddle the window.

### Binance reversed its distribution programme

This is the largest single positioning change, and it cuts the other way:

| Wallet | 2026-08-31 | 2026-09-02 | Change |
|---|---|---|---|
| Binance.com hot | 951,271 | 434,997 | **-516,274 (-54.3%)** |
| Binance Staking custody | 2,978,782 | 3,398,618 | **+419,836 (+14.1%)** |

Run #23 documented the opposite for two consecutive weeks: custody draining into
the hot wallet, which then fed the OTC desks — the funding leg of distribution.
That has **reversed**. Roughly 420K has moved off exchange float and back into
custody, and the hot wallet has more than halved.

The run #9 watch on this wallet carries a pre-registered reading: a move back into
custody is the constructive branch. It just fired constructive for the first time
since run #14.

### Whale tiers: everyone except Binance sold

On a prior-tier basis across the 76 addresses present in both snapshots (the run
#14 boundary guard):

| Tier | Wallets | 2026-08-31 | 2026-09-02 | Change |
|---|---|---|---|---|
| Mega (>1M) | 2 | 4,077,842 | 4,497,678 | **+419,836 (+10.30%)** |
| Large (100K–1M) | 17 | 4,959,207 | 4,589,396 | **-369,811 (-7.46%)** |
| Mid (10K–100K) | 50 | 1,474,936 | 1,369,864 | **-105,072 (-7.12%)** |

The entire mega-tier gain **is** the Binance custody transfer. Net that out and
large and mid whales sold **474,883 EGLD combined** into the move. Gate.io was
nearly emptied (-82.9%, 9,537 left) and Bybit fell 19.2%.

Two wallets accumulated: Unknown Whale B (+55,037) and a nonce-0 migration
destination (+66,525).

### The identifiable bid is still exactly zero

The Mega Whale absorber — the one large buyer this model can name — is unchanged
to four decimal places for a fourth consecutive week. There is no traceable large
buyer behind this move. The demand is arriving on exchange order books, where this
model cannot see it.

### Emerging liquid staking is the one growth story

| Protocol | Supply 08-31 | Supply 09-02 | Holders |
|---|---|---|---|
| Dinovox VoxEGLD | 1,748 | **1,841 (+5.3%)** | 78 → **102 (+31%)** |
| SALSA | 5,080 | 5,071 | 382 → 383 |
| VestaX | 802 | 802 | 439 |

VoxEGLD — the protocol flagged two days ago — grew supply 5.3% and holders 31% in
48 hours, while the established LSDs shrank. It is tiny, but it is the only
liquid-staking instrument on the chain currently taking subscriptions.

---

## What this adds up to

A protocol upgrade eight days out is being priced, and the entities holding EGLD
are using the bid to reduce exposure.

The evidence for the second half is unusually consistent: the record OTC overhang
halved into the move, with the most recent 24 hours delivering to Bybit, Binance
and Gate.io rather than clearing back to UPbit; large and mid whales net-sold
474,883 EGLD; staked EGLD, delegation, both major LSDs and both wrapped dollars
all contracted; and there is no identifiable large buyer anywhere in the data.

Two things genuinely cut the other way, and they are not small. Binance moved
420K off exchange float back into staking custody — reversing the two-week
distribution programme, and firing the constructive branch of a watch standing
since run #9. And USH minted for the first time in three weeks, meaning borrowers
are opening leveraged positions rather than closing them.

The tension to hold: the supply being distributed is **identified, named and
finite** — 133,150 EGLD still sits on the desks, and it is now half what it was.
The demand absorbing it is **anonymous and unmeasurable** from on-chain data,
because it is arriving at exchange order books. That asymmetry is why this model
can describe the selling precisely and can say almost nothing about the buying.

### What would settle it

| Question | What to watch | Threshold |
|---|---|---|
| Is the overhang cleared or reloading? | Desk inventory | Below ~60K = delivered; back above ~200K = restaged |
| Was Binance's reversal real? | Custody vs hot | Custody holding above 3.3M through 10 Sep |
| Is the upgrade on schedule? | Validator versions | v2.x share before 10 Sep |
| Is demand real or positioning? | Price after activation | Holding $4.50+ through the 24-minute pause |

---

*Ad-hoc report, outside the weekly cycle. Figures are 48-hour deltas against the
run #23 snapshot (2026-08-31) unless stated. All EGLD amounts human-readable. All
times UTC.*
