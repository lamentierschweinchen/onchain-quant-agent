# MultiversX chain restart - what the chain, exchanges and price show (2026-09-24)

Read from the MultiversX API, GitHub (`multiversx/mx-chain-go`), CoinGecko and the Upbit public API at ~22:00 UTC Sep 24. Evidence: `data/collected/special/2026-09-24-chain-restart.json`.

## Timeline (UTC)

| When | What | Source |
|---|---|---|
| Sep 16 | Exploit wallet funded (~17 EGLD from MEXC, Bybit and `erd17m28zapc...`) | chain |
| Sep 19 06:34:46 | Exploit wallet deploys its contract | chain |
| **Sep 19 06:37:45** | **Last block kept on all four shards (round 33,384,826)** | chain |
| Sep 19 07:15-07:37 | Doubling deposits (3.2M, 6.4M, 12.8M EGLD...), fan-out, exchange deposits | old index (orphaned) |
| Sep 19 07:37-07:41 | Old chain stops | halted-state snapshot |
| Sep 19 ~08:00 | Upbit EGLD premium opens at +59% | Upbit API |
| Sep 19 10:28 | First fix commit ("atomicity and integration") | GitHub |
| Sep 20-22 | "hardfork-round-exclusion", "recovery checkpoint handling", v2.1.0-v2.1.2 | GitHub |
| Sep 23 16:00 | v2.1.4 pre-release ("skip accounts trie check") | GitHub |
| **Sep 23 16:35:00** | **Restart 1** - epoch 2242 starts; only 114 reward txs | chain |
| **Sep 23 16:52-16:53** | **Chain stops again on all shards** | chain |
| Sep 24 00:00 | Upbit premium reopens (+38%, peak +64% at 06:00) | Upbit API |
| Sep 24 10:40 | v2.1.5 full release ("do the check for trie nodes but write only the previous missing") | GitHub |
| **Sep 24 15:30:00** | **Restart 2** - live since | chain |
| Sep 24 15:40-15:58 | ~3,700 transactions from the rolled-back hour re-executed | chain |

## The recovery was a rollback plus a selective replay

- Every shard's history after Sep 19 06:37:45 was replaced; the same block heights now carry Sep 23-24 timestamps. That is 64 minutes of finalized history rewritten, not a targeted state edit.
- Exploit state is gone: attacker 13.2 EGLD (nonce 25, down from 130), contract 0.048 EGLD, all 12 fan-out wallets empty with nonce 0. Binance.com, KuCoin, MEXC, Unknown Whale I and erd1a6lte0 balances equal their pre-exploit values to the EGLD.
- Legitimate transactions from the rolled-back hour were re-executed at Sep 24 15:40-15:58 (12 of 12 sampled).
- **1,697 transactions from that hour were not re-executed.** 100 are the exploit's; the other **1,597** are mostly zero-value spam-bot transfers (two bots with nonces above 2.1M account for 278) and moved **467 EGLD** in total. The value-bearing ones are four transfers, three into `erd17m28zapcll4y0j6el0cn0x9dn85wtjxa3e7u2jtkppxzksq5r5cq7l4q2h` - the same wallet that funded the attacker on Sep 16. The senders still hold the funds.
- **The API index still serves the orphaned exploit transactions as `success`** (e.g. the 850,614 EGLD deposit into Binance.com, tx `8bc7da8d2a10...`), and account histories still list them.
- The pre-fork part of the exploit (contract deploy, first small rounds) is still canonical.

## Exchanges

- No tracked exchange hot wallet has sent a new transaction since restart 2: withdrawals are still closed everywhere on chain. The only exchange movements are three re-executed Sep 19 transfers.
- No public post-restart statement from MultiversX or the exchanges was found; the latest reporting is "fix on a shadow fork", Upbit trading caution (review to Oct 19-23), and "withdrawals before deposits" at Upbit.

## Price: a closed-book Korea premium

| | Upbit (USD via KRW-USDT) | Global | Premium | Upbit volume |
|---|---|---|---|---|
| Sep 19 08:00-23:00 | $5.4-6.9 | ~$4.0 | +34% to +65% | ₩66B day |
| Sep 21-23 | $4.2-4.7 | $4.1-4.5 | 0-4% | ₩1-4B/day |
| Sep 24 00:00-15:00 | $5.7-7.0 | ~$4.2-4.4 | +33% to +64% | ₩90B day |
| Sep 24 21:00 | $5.73 | $4.40 | +30% | |

BTC trades within 0.3% on Upbit and Binance, so FX is not the cause. Upbit is 77% of global EGLD volume ($61M/24h); Binance $1.3M. Upbit's bid within 2% is $21.6K against $65K of asks. Both premium episodes began while EGLD could not be deposited to Korean venues, so the arbitrage that would close the gap is blocked.

Global EGLD: $4.06 before the exploit, low $3.56 (Sep 20 15:00), high $4.60 (Sep 23 15:00), $4.37 now (+7.7%; BTC +4.1%).

## Since restart 2 (~6.5h)

- Network activity back to baseline (~6-7K tx/hour vs 5-8K pre-halt).
- xExchange ~$195K volume (89% WEGLD/USDC); MEX pool-priced at 6.7e-07. Hatom: normal flows, no liquidations; EGLD market 116,938 EGLD.
- OTC desks idle (3 txs; 46,637 EGLD, unchanged).
- **Staking exits up ~10x:** 84 new unDelegate calls, 41,515 EGLD, vs ~660 EGLD/hour pre-halt. 69% from two wallets (`erd155j9c36hp5...` 17,776 across vaporrepublic and star_staking; `erd16xmf87952g...` 10,994 from orangestaking).
- The address-poisoning operator (`erd1gyauk5zt...`) has sent 63 transactions since restart, re-funding lookalikes of KuCoin, Unknown Whale I and erd1a6lte0.
- Issuance: 4,030 EGLD across the two epoch transitions since the halt vs ~7,020 per normal epoch; the downtime was not paid as normal epochs (~27K EGLD of forgone staking rewards).

## Pre-committed test halt-recovery-clean (formal resolution at run #27)

Invalid balances < 1,000 EGLD: yes (13.3). OTC desks and Binance custody: identical. Hatom EGLD market +4.1%, explained by 6h of ordinary post-restart activity. Preliminary reading: clean on balances; the method was a rollback-and-replay that rewrote 64 minutes of finalized history and left 1,597 non-exploit transactions unexecuted, which is broader than the "preserve finalized history" framing.
