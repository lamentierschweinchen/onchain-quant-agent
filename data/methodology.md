# Analysis Methodology — Living Document

**Last updated**: 2026-08-17 (run #21, schema v2)
**Status**: This document is read and updated by the agent on every run. It contains proven practices, known pitfalls, and evolving heuristics.

---

## Core Principles

1. **Every metric needs a "so what?"** — Data without interpretation is a spreadsheet, not intelligence. Always explain what a number means for someone making decisions on MultiversX.
2. **Deltas matter more than absolutes** — "Staked ratio is 48.1%" is a fact. "Staked ratio rose 0.3pp this week, continuing a 4-week trend of increasing lockup" is intelligence.
3. **Name everything** — Addresses are meaningless to readers. Always resolve via known-addresses.json. If you can't label it, note it for investigation.
4. **Flag what you can't see** — Missing data is itself a signal. If an endpoint fails or returns unexpected results, say so explicitly.
5. **Forward-looking beats backward-looking** — Anomalies tell you what already happened. Trend indicators tell you what is about to happen. Both matter, but the second is the higher-value insight.
6. **Stratify before aggregating** — A single "exchange flow" number hides whether retail or whales drove it. Tier the data: by whale size, by exchange entity, by protocol category.

---

## API Best Practices

### What Works
- `/economics` — reliable, fast, cached. Use for all macro metrics.
- `/accounts?size=50&sort=balance&order=desc` — dynamic whale discovery. Run every time.
- `/accounts/{addr}/transactions?size=25&after=TIMESTAMP` — the ONLY reliable way to find whale transactions. Query ~30 accounts per run.
- `/providers?sort=locked&order=desc` — complete staking provider data.
- `/identities` — returns all ~263 validator identities in one call. No pagination needed.
- `/mex/pairs` — full xExchange pair data with 24h volume and TVL.
- `/mex/tokens` — includes `previous24hPrice` for calculating 24h changes.
- `/tokens?sort=accounts|transactions|marketCap` — three different views of the token ecosystem.

### What Doesn't Work
- **`minValue` on `/transactions`** — silently ignored. DO NOT USE. Wastes API calls and returns wrong data.
- **Global `/transactions`** for whale detection — only returns most recent ~100 txs network-wide. You'll get xPortal claim spam, not whale movements.
- **Relying on account nonce for activity** — some whales have nonce 0 (received via internal transfers/genesis). Zero nonce ≠ inactive.
- **Assuming exchange txs are visible as standard transactions** — large exchanges (e.g., MEXC) use internal transfers or smart contract mechanisms that don't appear in `/accounts/{addr}/transactions`. Always verify balance changes against the exchange balance snapshot in previous.json, not just recent tx queries.
- **`/mex/tokens` volume24h field** — returns $0 for all tokens despite real trading occurring. Use `/mex/pairs` for DEX volume data. The pairs endpoint correctly shows per-pair 24h volume and trade counts.

### Intermediary Wallet Investigation Pattern
When a large transfer goes to an unknown account:
1. Check the recipient's **nonce** — low nonce (< 10) = high probability routing wallet; medium nonce (10–100) = still possible routing wallet
2. Fetch their **recent transactions** to see if they immediately forwarded the funds
3. Check **current balance** — near-zero balance after a large receipt = confirmed routing wallet (regardless of nonce)
4. **IMPORTANT: Low nonce ≠ cold storage guarantee**. Nonce 4 accounts can reactivate after weeks of dormancy. Always re-check activity if an account was previously classified cold.
5. This pattern identified: Binance 470K restaking (nonce 3 router), Coinbase 798K OTC (nonce 80 router)

### Coinbase OTC Pattern
When Coinbase shows large inflows AND outflows in the same week:
1. Check if the gross flows are from/to different counterparties — this confirms OTC intermediation
2. Net balance change is the signal (net -7K EGLD despite 1M+ gross flows = OTC neutral)
3. The buyers and sellers are identifiable as the counterparties
4. This pattern identified the Apr 18 2026 bilateral deal: Whale A+B sold 1.026M, mega-whale erd18mv2z6r2 received 798K

### Key Metric Distinction
- **`/economics` `staked`** = total EGLD locked in the Staking Module contract (14.25M EGLD) — includes both direct node staking and delegation
- **`/providers` `locked`** = total EGLD locked via delegation smart contracts only (11.17M EGLD) — excludes direct node operator staking
- These will always differ. Use `/economics` staked for macro staked ratio, `/providers` for delegation market concentration metrics.

### Rate Limiting
- No explicit rate limit headers, but add 200ms delays between requests.
- Budget ~50-60 API calls per run. Prioritize whale accounts over completeness.
- If you need to paginate, the per-request max is 50 items.

---

## Whale Detection Methodology

### Priority Order for Account Queries
1. **Known exchange addresses** (~17) — always query, these are the flow indicators
2. **Top 10 non-exchange, non-system accounts** — dynamic whale discovery
3. **Accounts from previous.json that dropped out of top 50** — potential large outflows
4. **Addresses flagged in learnings.json** — follow up on previously discovered unknowns

### Whale Tier Stratification (v2)
Stratify the top-100 wallets into balance tiers and report the aggregate movement of each tier separately.

| Tier | Threshold | Typical Holders |
|------|-----------|-----------------|
| `mega_whale` | > 1,000,000 EGLD | Exchange staking pools, mega-OTC counterparties, foundation wallets |
| `large_whale` | 100,000 — 1,000,000 EGLD | Exchange hot wallets, individual mega-holders, large delegation contracts |
| `mid_whale` | 10,000 — 100,000 EGLD | Smaller exchanges, active traders, mid-tier holders |

**Why it matters**: a single "exchange flow" number is too coarse. If mega_whales are net-shrinking while mid_whales are net-growing, that's wealth distribution. If mega_whales grow while mid_whales shrink, that's accumulation by the very largest holders. Each pattern has different implications for liquidity and price stability.

### Entity Netting (v2)
Many entities (Binance, Coinbase) operate from multiple wallets. The per-wallet view is noisy. Collapse them to a single net-flow figure per parent entity.

Example: Binance Hot 1 (-77K) + Binance Hot 2 (-23K) + Binance Cold (0) + Binance Staking (+50K) = -50K Binance net.

Use entity netting alongside, not instead of, per-wallet flows. The per-wallet detail explains the *mechanism*; the entity-level netting tells you the *direction*.

### Transaction Classification
| Flow Type | Logic |
|-----------|-------|
| `exchange_inflow` | Receiver is known exchange, sender is not |
| `exchange_outflow` | Sender is known exchange, receiver is not |
| `defi_deposit` | Receiver is known DeFi contract |
| `defi_withdrawal` | Sender is known DeFi contract |
| `staking` | Receiver is known staking provider |
| `unstaking` | Sender is known staking provider |
| `bridge` | Either party is a bridge contract |
| `whale_to_whale` | Both are large holders, neither exchange/DeFi |
| `unknown` | Can't classify — flag for investigation |

### Balance Change Detection
- Compare top 50 accounts against `data/previous.json`
- Flag any account with >5% balance change
- Flag any account that dropped out of / entered the top 50
- Track exchange total balance WoW for the net flow signal

---


### Cross-Exchange OTC Funnel Pattern (run #6, 2026-05-04)

The OTC desks on MultiversX are NOT exchange-internal infrastructure — they are shared infrastructure that aggregates flow from multiple exchanges.

**Detection signature**:
1. Routing wallet receives identical-amount chunks (e.g. 5,999 / 7,999 / 8,000 EGLD) from a known exchange wallet
2. Routing wallet has near-zero balance immediately before AND immediately after the receipt
3. Within minutes, the same amount is forwarded to a known OTC desk
4. Wallet has medium-high nonce (>100) but low active balance — pure pass-through pattern

**First documented case**: Binance.com 2 (erd1sdsl) → 3 routing wallets (erd16nws nonce 169, erd1k4r6 nonce 180, erd1de38 nonce 147) → UPbit OTC Desk + OTC Distribution Wallet. ~80K EGLD routed in week 1.

**Implication**: A single OTC desk's gross inflows do NOT represent a single exchange's customer flow — they aggregate flows from multiple exchange counterparties. Net OTC flow analysis must consider the entire upstream chain.

**To validate next run**: query the OTC desks' downstream recipients (erd1f4kcxxn4, erd1tuvllxaf, erd1krmy7xld, erd142cjv2r5) — if they forward to other exchanges' deposit addresses, the multi-hop pipeline is confirmed.

**VALIDATED in run #7 (2026-05-11)**: Confirmed at scale. 8 routing wallets traced forwarding UPbit OTC + OTC Distribution chunks to Bybit/Binance/KuCoin. Plus reverse flows: Bybit→KuCoin (erd1rffkz8zwp3), KuCoin↔Binance↔Bybit (erd14n5vtgezss). The OTC pipeline is operational bidirectional cross-exchange settlement infrastructure. Detection method now industrialized: query each OTC desk's outflows, look for identical-amount chunks (1-8K EGLD typical) forwarded within minutes to wallets with near-zero balance and high nonce (>100). Then query those routing wallets to identify the destination exchange.

## Staking Analysis

### Concentration Metrics
- **Herfindahl-Hirschman Index (HHI)**: sum of squared market shares for all providers
  - < 0.15 = competitive market
  - 0.15-0.25 = moderate concentration
  - > 0.25 = highly concentrated
- **Top-5 and Top-10 share**: simple percentage of total stake
- Track these WoW — trend matters more than absolute level

### APR Analysis
- Base APR (10.8%) vs TopUp APR (6.5%) spread indicates how top-heavy the network is
- Provider APR varies from ~6.5% to ~9.3% — the spread is meaningful for delegators
- Low-fee providers (Incal 1%, Maple Leaf 0%) vs standard 12% fee is worth highlighting

### APR Distribution Histogram (v2)
Bucket all providers by APR into: `5-6%`, `6-7%`, `7-8%`, `8-9%`, `9-10%`, `10%+`. For each bucket, output `provider_count` and `total_locked_egld`.

**Interpretation**:
- Tight cluster around one bucket (e.g. all providers in 7-8%) → competitive equilibrium, fees converged
- Wide spread → market opportunity, delegators can earn meaningfully more by switching
- Most stake concentrated in a low-APR bucket while a high-APR bucket exists with little stake → delegator inertia (they're not chasing yield)

### APR vs Fee Outliers (v2)
- `top_apr` — top 5 providers ranked by APR (the highest yield available)
- `lowest_fee` — top 5 providers ranked by lowest fee (highest delegator-share value)

The intersection of these two lists is the asymmetric value zone. A high-APR + low-fee provider that has *not* attracted proportional stake is a clear delegator opportunity worth flagging.

### Delegator and Provider Reward Behavior (v3, run #11)

**Tool**: `scripts/delegator_behavior.py`

A focused analysis of what individual delegators do with claimed rewards (sell/hold/compound) and what staking providers do with service-fee earnings (compound/sell/treasury). This complements the per-provider WoW change view by tracking the *decisions* underlying those changes.

#### Function-call semantics on delegation contracts

| Function | Meaning |
|---|---|
| `reDelegateRewards` | Delegator compounds rewards back into their stake |
| `claimRewards` | Delegator pulls EGLD into their wallet |
| `delegate` | New stake added |
| `unDelegate` | Stake withdrawn (starts unbonding) |
| `withdraw` | Completion of an unbond |
| `reward` | Provider-initiated reward distribution |

#### Compound vs Claim ratio at function-level

For top-N providers, query inbound transactions over the past 7d, count function calls. The simplest metric is `reDelegateRewards / (reDelegateRewards + claimRewards)`. Run #11 baseline: **61.9% compound** across top 8 providers (348 redelegate vs 214 claim).

If this ratio falls during continued price decline, retail is panic-claiming (bearish DeFi sentiment). If it rises, delegators are doubling down on yield (bullish).

#### Delegator fate classification (per claim)

For each `claimRewards` event, look up the claimant's next outbound EGLD tx within 72h:

| Fate | Logic |
|---|---|
| `sold` | Next receiver is `category=exchange` in known-addresses.json |
| `rotated_provider` | Next receiver is another delegation contract |
| `defi_deposit` | Next receiver is `category=defi` |
| `held_or_other` | Next receiver unlabeled |
| `held` | No outbound tx > 0.001 EGLD within 72h |

Tier thresholds (per-claim value): retail <1 EGLD, mid-tier 1-50, institutional 50-1000, whale >1000.

#### Provider operator behavior

Each delegation contract has an `ownerAddress` (the operator wallet). Query its outbound EGLD over 30d, classify destinations the same way. Helps answer: does the provider sell, treasury, or re-deploy fees?

#### Discoveries from run #11 baseline

- **Retail (<1 EGLD/claim) does not sell rewards** — 0 of 68 retail claims went to a labeled exchange.
- **Institutional (50-1000 EGLD/claim) is ~50/50 sell vs hold** by value (small sample of 3).
- **No provider operator sold fees to exchanges** in 30d. Top destination = treasury wallets (held_or_other).
- **truststaking is operated by XOXNO: Deployer Wallet** — discovered via this analysis. XOXNO has both a flagship LSD and control of the 4th-largest provider.

Full results: [reports/2026-06-08-delegator-behavior.md](../reports/2026-06-08-delegator-behavior.md) and `data/collected/delegator_behavior_2026-06-08.json`.

### Churn Metric (v2)
Sum `numUsers` across all providers → `total_delegators_current`. Compare to previous week's sum:
- `delegators_added` — net new delegators this week
- `providers_gaining_delegators` / `providers_losing_delegators` — breadth of churn

**Interpretation matrix**:
| Delegators | Staked EGLD | Read |
|------------|-------------|------|
| ↑ | ↑ | Healthy retail growth |
| ↑ | flat | Retail joining, no whale conviction |
| flat | ↑ | Whale consolidation, no new participation |
| ↓ | ↑ | Concentrated re-staking by fewer larger holders (e.g. exchange restaking events) |
| ↓ | ↓ | Outflow / unstaking pressure |

---

## Token Analysis

### Noise vs Signal
- **Ignore high-holder-count tokens with zero market cap** — these are airdrop spam (DRX with 2.47M holders is not real adoption)
- **Real token ecosystem starts at WEGLD** (134K holders) and USDC (83K holders)
- Focus on tokens with both meaningful holder count AND market cap
- Volume spikes relative to a token's own baseline are more interesting than absolute volume

### xExchange Health Indicators
- Daily volume / EGLD market cap ratio: measures DEX utilization
- Number of pairs with >$1K daily volume: measures how many pairs are "alive"
- WEGLD/USDC dominance %: if one pair is >50% of all volume, the DEX is thin

### Newly-Issued Tokens (v2 — workaround active as of run #11)

**Note**: `/tokens?sort=timestamp` returns HTTP 400 — silently unsupported. Use the ESDT system SC scan workaround below.

#### Working method (run #11+):
1. Query `/accounts/erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u/transactions?after=SEVEN_DAYS_AGO&status=success&function=issue&size=50`
2. For each tx, decode `data` field: base64 → hex pairs separated by `@`
3. Format: `issue@<name_hex>@<ticker_hex>@<supply_hex>@<decimals_hex>@<flag_key_hex>@<flag_val_hex>@...`
4. Decode `<name_hex>` and `<ticker_hex>` from hex back to ASCII
5. Resolve the resulting `IDENTIFIER-randomhex` via `/tokens?search=<TICKER>&size=10` filtered by exact name match
6. Report top 5 ranked by holders traction (filter: >10 holders, >5 txs, identifiable deployer)

#### Quality filter (run #11+):
1. Has > 10 holders (filters spam mints)
2. Has > 5 transactions (filters dormant deploys)
3. Has identifiable deployer (cross-reference deployer against known-addresses.json)

Report top 5. A new token deployed by a known team or DeFi protocol is a higher-signal launch than an unknown deployer.

Run #11 detected 3 issuances this method: FRANZELA (FRA, 2 holders), GreenSmokeNetwork (GSN, 1 holder), GrandTheftAurum (GTA, 1 holder). All sub-quality filter, but the method itself worked reliably.

### (Deprecated, kept for context) Original method
Pull `/tokens?sort=timestamp&order=desc&size=50` and filter client-side for `timestamp >= SEVEN_DAYS_AGO`. Rank by holder traction.

**Quality filter** (in this order):
1. Has > 10 holders (filters spam mints)
2. Has > 5 transactions (filters dormant deploys)
3. Has identifiable deployer (cross-reference deployer against known-addresses.json)

Report top 5. A new token deployed by a known team or DeFi protocol is a higher-signal launch than an unknown deployer.

## DeFi Per-Protocol Breakdown (v2)

Each tracked protocol gets its own row in `protocol_breakdown`. Address sets come from `data/known-addresses.json`:

| Protocol | Category | Address Set | TVL Method |
|----------|----------|-------------|------------|
| xExchange | dex | `defi_xexchange` (16 addresses) | Sum contract balances + 24h volume from `/mex/pairs` |
| Hatom Lending | lending | `defi_hatom` (39 addresses) | Sum H-token market caps (HUSDC, HWBTC, HEGLD, HWETH, HUSDT, HWTAO, HHTM, HMEX, HUTK, HBUSD). Exclude HSEGLD/HSWTAO to avoid double-count |
| Hatom Liquid Staking | liquid_staking | `defi_hatom` subset | SEGLD-3ad2d0 market cap + SWTAO-356a25 market cap |
| Hatom USH | stablecoin | `defi_hatom` subset | USH-111e09 market cap |
| XOXNO LSD | liquid_staking | `defi_xoxno` subset | XEGLD-e413ed market cap |
| XOXNO Aggregator | aggregator | `defi_xoxno` subset | `transfers_24h` only (non-custodial) |
| XOXNO Marketplace | nft_marketplace | `defi_xoxno` subset | Operational EGLD only; NFT volume is the real metric |
| AshSwap | dex (stableswap) | `defi_ashswap` (9 addresses) | Pool TVL, swap volume |
| OneDex | aggregator | `defi_onedex` (5 addresses) | `transfers_24h` (aggregator) |
| JEXchange | dex (orderbook) | `defi_jexchange` (4 addresses) | `transfers_24h` (orderbook) |

### SWTAO null-mcap fallback (run #11, 2026-06-08)

The MultiversX /tokens/SWTAO-356a25 endpoint occasionally returns `price: null` and `marketCap: null` (verified live this run). When this happens, the assembler will silently zero out the SWTAO portion of Hatom LSD TVL, making it appear ~$1M smaller than reality and producing implausible WoW deltas (e.g., -26% EGLD).

**Fallback derivation**:
```
accumulator_ratio = prev_swtao_price / prev_wtao_price       # ~1.22 typical
swtao_price_est = wtao_price_current * accumulator_ratio
swtao_mcap_est = swtao_price_est * swtao_supply_current
```

The accumulator ratio is stable WoW (rewards accrue smoothly). Validated this run: derived $264.02/SWTAO produced ~$875K mcap, making Hatom LSD ~$3.38M (-0.8% EGLD WoW, essentially flat) — matching the expected magnitude given SEGLD supply only fell -0.9%.

Add this fallback to future assembler scripts. The audit script (`scripts/audit_report.py`) flags the null condition as an ERROR; treating it as one will catch the issue before publish.

### LSDs: report in SUPPLY terms, not market cap (run #13, 2026-06-22)

**Mcap-based LSD TVL is price-contaminated and produces phantom contraction signals.** SEGLD/XEGLD mcap = price × supply. During an EGLD decline, mcap falls even when the underlying staked position is unchanged; SWTAO mcap tracks TAO price entirely (not MultiversX flows). The run #11/#12 "synchronized LSD contraction" narrative was largely a price artifact built on mcap.

**Rule**: the primary LSD/stablecoin signal is **circulating supply** (the `/tokens/{id}` `supply` field, which is decimals-adjusted and never returns null), compared WoW. Mcap is secondary (USD context only).

Run #13 demonstration — in supply terms the LSDs were flat-to-up while USD mcaps fell:
| Token | Supply WoW | USD mcap WoW | Read |
|---|---|---|---|
| SEGLD-3ad2d0 | -0.51% | -5.3% | flat (mild redemption); USD drop is price |
| XEGLD-e413ed | **+0.63%** | -3.5% | GREW; the run #12 "3rd-week contraction" watch was NOT confirmed |
| SWTAO-356a25 | -0.06% | -17.7% | flat; mcap drop is TAO price |
| USH-111e09 | -0.08% | -0.2% | flat; 2-week burn trend ended |

`previous.json` now stores an `lsd_supply` block (SEGLD/XEGLD/SWTAO/USH raw supply) so the next run can compute supply WoW directly without needing the prior collected snapshot.

### Net exchange flow must be read JOINTLY with OTC throughput (run #14, 2026-06-29)

**A large net exchange OUTFLOW during a broad sell-off is NOT automatically bullish.** Run #14: net exchange flow reversed to -222K (Binance hot -158K, Bybit -56K) after a 3-week inflow streak — in isolation this reads as off-exchange accumulation. But the OTC pipeline simultaneously ran a record 195K of distribution throughput and reloaded the desks +35K. So distribution did not stop; it shifted channel (exchange deposits -> OTC pipeline). **Rule**: always pair the exchange-flow number with OTC desk throughput + balance delta before calling a flow bullish/bearish. The two channels substitute for each other. Large exchange hot-wallet moves are invisible in `/accounts/{addr}/transactions` (internal transfers/SC mechanisms) — Binance's -158K produced zero value-bearing standard txs, so the destination is inferred, not proven. Compute exchange flow from balance deltas, never tx scans.

### Custody<->hot transfers ARE traceable; tx-scan the custody address (run #15, 2026-07-06)

**When a tracked exchange CUSTODY wallet changes balance, tx-scan the custody address directly before assuming the move is untraceable.** Run #15 resolved the 7-week Binance Staking custody standoff: the custody drew down -158,853 and, UNLIKE the internal-transfer-invisible hot-wallet moves of prior weeks, the counterparty leg showed up as standard value txs on the custody address (received 241,147 from Binance.com hot, sent back 300,000 + 100,000). Lesson: staking-custody <-> exchange-hot transfers are standard value txs (visible in `/accounts/{addr}/transactions`); it's the hot <-> external/customer leg that is internal-transfer-invisible. So a custody move can usually be ATTRIBUTED (to which hot wallet), even if the onward external destination cannot. Always query the custody address's txs, not just its balance delta.

### Pre-commit the directional reading on a multi-week structural watch (run #15, 2026-07-06)

The Binance-custody watch (runs #9-14) carried a PRE-REGISTERED interpretation: a move to the protocol staked module = bullish delegation; a drawdown back to hot wallets = bearish distribution. When the move finally came (run #15, drawdown-to-hot), the pre-commit removed all ambiguity - no post-hoc rationalizing which way to read it. **Rule**: for any long-running "parked position, eventual move" watch, register the bull/bear reading of each possible outcome BEFORE the move happens. It disciplines the eventual call and makes the resolution instantly legible.

### Read exchange net-flow by ENTITY, not just aggregate (run #15, 2026-07-06)

A headline net exchange-flow number can invert the true breadth when ONE entity's move exceeds the net. Run #15: net -218K OUTFLOW, but ~all of it was a single Binance idiosyncratic move (-236K, the custody unwind); ex-Binance the exchange complex was net-INFLOW (Crypto.com +27K, Bybit +21K, KuCoin +9.6K) into the price bounce. Calling the aggregate "distribution" would have been wrong - it was one entity's plumbing on top of a mildly accumulative-onto-exchange tape. **Rule**: always decompose net flow to per-entity before labeling the aggregate bullish/bearish; if one entity exceeds the net, report it as that entity's move, not a market-wide signal. (Complements the run #14 "read flow jointly with OTC throughput" rule.)

### Bilateral inverse rule - first UP-week confirmation (run #15, 2026-07-06)

The bilateral inverse rule (Hatom Lending EGLD-denominated TVL moves counter to price) had only ever been tested on DOWN weeks (depositors DCA/hold, TVL up in EGLD terms). Run #15 gave the first UP-week test at |dPrice|>=5%: price +5.88%, Hatom Lending EGLD-TVL -2.86% (correct inverse sign) - depositors WITHDREW to capture gains, the mirror of dip-DCA. Response ratio 0.49. The rule now has two-sided confirmation.

### Newly-issued scan: holder-count guard against false positives (run #15, 2026-07-06)

The ESDT system-SC issue-function scan can resolve an `issue` tx onto a LONG-ESTABLISHED token via the name-search step. Run #15 it matched WrappedUSDC (USDC-c76f1f, 81,516 holders) - not a new mint. **Fix**: after resolving, drop any match with >1,000 holders OR an identifier already present in previous.json's token lists (a genuinely new token this window has a tiny holder base). Keep the existing >10-holder / >5-tx quality bar for the rest. A cleaner future guard would also check the token's own issuance timestamp against the window rather than trusting the scanned tx's timestamp.

### Net out the binance_staking DELEGATION provider before narrating delegation-TVL WoW (run #16, 2026-07-13)

Binance operates a delegation PROVIDER on MultiversX (identity `binance_staking`, ~8,500 delegators) that is DISTINCT from its Staking CUSTODY wallet (erd1rf4hv70...). Both are Binance staking legs and both can move independently. Run #16: the binance_staking provider shed -148,941 of locked stake, which by itself made the delegation total_locked look like it shrank -28K NET - when ex-Binance, delegation actually GREW +120K broadly (smartchainconnection +38K, pokerstaking +16.6K, Synexis +9.3K). **Rule**: treat a single-entity provider swing (binance_staking, or the erd1qqqq system aggregators) the same way as the run #15 exchange-entity rule - decompose/net it out before labeling the delegation-TVL aggregate. A -149K move on ONE provider inverted the breadth of a +120K broad-growth week.

### Read a CEX outflow by DESTINATION, not just its sign (run #16, 2026-07-13)

An exchange cold-wallet OUTFLOW during a price rally reads as bullish self-custody in isolation - but it can be OTC-routing. Run #16: UPbit's cold wallet fell -131K, which looks like accumulation, but UPbit fed its OWN UPbit OTC Desk 320,000 + 140,000 = 460K in standard transfers - the outflow was the LOADING leg of a record OTC distribution reload, not customer withdrawal. **Rule**: before calling an exchange outflow bullish, check whether the receiver is a known OTC desk/router (the transfer is a standard value tx and traceable). This is the per-transfer refinement of the run #14 read-flow-jointly-with-OTC rule. Contrast Bybit's -221K same week, which had NO value-bearing standard txs (internal-transfer-invisible) and therefore stayed genuinely ambiguous.

### z-score UNDER-flags a regime change after a 2+ week trend (run #16, 2026-07-13)

The run #9 degenerate-z guard covered z OVER-flagging tiny moves (spurious huge z on a low-variance baseline). Run #16 is the opposite failure: EGLD ripped +15.93% (an EGLD-SPECIFIC decoupling - BTC/ETH flat) but produced z=-0.09, because two consecutive up-weeks pulled the baseline mean up to the current level. **Rule**: when a metric has trended one direction for 2+ weeks, the absolute z-score understates a genuine break - cross-check with the rule-based read (here: EGLD up while majors flat = EGLD-specific, not macro). A de-trended or relative-strength anomaly measure (EGLD WoW vs BTC/ETH WoW) would catch what the absolute z misses; flagged as a future improvement.

### USH MINT as a leverage-returning indicator (run #16, 2026-07-13) - mirror of the run #11 burn rule

Run #11 established: USH (Hatom CDP stablecoin) supply BURNING >1% in a week during a decline = borrowers force-closing CDP positions (de-leveraging). Run #16 is the clean mirror: USH supply MINTED +6.49% (626,942, the largest move since the run #11 -7% burn) during the +16% rally = borrowers OPENING new CDP positions (leverage RETURNING). Paired with XEGLD (XOXNO LSD) supply +4.54% (re-accumulating after its -29% collapse) and reward compound rate up a 3rd week to 61.59%, it is a genuine-demand cluster. **Rule**: surface USH supply moves >5% in EITHER direction in exec_summary; mint = leverage returning (constructive), burn = de-leveraging (de-risking). Supply is price-independent, so this is robust to the price move contaminating mcap.

### Bilateral inverse rule - 2nd UP-week confirmation, larger magnitude (run #16, 2026-07-13)

The bilateral inverse rule (Hatom Lending EGLD-denominated TVL moves counter to price) got its 2nd up-week test at a LARGE magnitude: price +15.93%, Hatom Lending EGLD-TVL -11.48% (correct inverse sign - depositors withdrew to bank gains), response ratio 0.72. Up-week response-ratio series so far: 0.49 (run #15), 0.72 (run #16). The rule now has two up-side confirmations and holds cleanly at a big up-move. Note the coexistence with the USH mint: Lending-deposit withdrawal (profit-taking) and USH minting (new leverage) are DIFFERENT cohorts, not a contradiction.

### Whale-tier boundary-crossing guard (run #14, 2026-06-29)

Before narrating tier-aggregate net changes, check whether a single wallet crossed a tier threshold. Run #14: Mega Whale erd18mv2z6r2 crossing 1M (998,971 -> 1,010,011) produced a phantom +997K mega / -1.2M large swing that is a reclassification artifact, not real accumulation. Net out boundary crossings first, or the tier story is dominated by one wallet stepping over a line.

### Supply-based LSD reporting VALIDATED under stress (run #14, 2026-06-29)

The run #13 supply-first LSD rule paid off in its first real stress test. XOXNO LSD (XEGLD) supply COLLAPSED -29.2% in one week (321,592 -> 227,765, ~94K redeemed) — the largest single-protocol LSD supply move in tracking. On a supply basis this is unambiguous and large; an mcap-only view would have blended it into the parallel -10.5% EGLD price drop and missed it entirely. The move was XOXNO-specific (SEGLD supply only -0.7%, SWTAO flat), so it was NOT a synchronized LSD event. **Lesson reaffirmed**: supply is the primary, price-independent LSD signal; mcap is USD context only. Large single-week supply moves point to one/few large redeemers — trace the LSD contract's outbound flows next run to distinguish migration (to native delegation / another LSD — bullish) from exit (to exchange — bearish).

### SWTAO can stay null for an ENTIRE run; carry prior price when WTAO also null (run #14, 2026-06-29)

The run #13 dataApi re-fetch guard (re-fetch dataApi-priced tokens individually at >=2.5s, up to 4 retries) was implemented this run and recovered 3 of 4 tokens (SEGLD/XEGLD/USH populated first pass). But SWTAO-356a25 stayed null through the main pass AND all 4 isolated 2.5s retries — the dataApi feed can keep a SPECIFIC token null for a whole run, not just under sequential load. The run #11 accumulator-ratio fallback (`swtao_price = wtao_price * prev_swtao_price/prev_wtao_price`) was ALSO unavailable because WTAO price was null too. **Last-resort fallback**: carry the prior-week SWTAO price applied to current supply for the USD mcap, mark it estimated (`_price_estimated`), and write it into the persisted snapshot so the audit's null-mcap ERROR and the report stay self-consistent. Supply (never null, flat +0.27%) remains the reliable signal. A more robust TAO price source would remove the dependency.

### dataApi token null-price recovery (run #13, 2026-06-22) — SUPERSEDES the run #12 1.0s rule

The run #12 rule ("≥1.0s spacing fixes /tokens/{id} nulls") is **incomplete**. This run, the four `priceSource.type == "dataApi"` tokens (SEGLD, SWTAO, USH, XEGLD) returned `price=null marketCap=null` on the sequential pass **even at 1.05s spacing**, while the H-tokens (a different price source) populated fine. Isolated re-fetch of just those four at **2.5s spacing** recovered all of them.

**Rule**: after the main `/tokens/{id}` pass, detect any dataApi-class token with `price is None` and re-fetch it individually at ≥2.5s spacing (up to ~4 retries). Do NOT treat a single null pass as an outage — it is a transient dataApi feed hiccup under sequential load that recovers on isolated retry. Combined with supply-based TVL (above), this makes the LSD/stablecoin TVL robust to the feed. The audit script's null-mcap ERROR remains the backstop.

### Exit-liquidity-bounce pattern VALIDATED (run #13, 2026-06-22)

Run #12 flagged the "exit liquidity bounce": EGLD +1.36% on collapsing engagement (delegators, DEX volume, on-exchange capital). Run #13 resolved it — the bounce **failed within one week**, breaking to a new low ($2.85 < the $2.95 floor) while exchange inflows continued (3rd week) and the OTC pipeline reloaded. **Promote to a reusable bearish forward indicator**: a relief rally on contracting engagement is distribution, not reversal; expect it to fail to new lows within 1-2 weeks.

### Stablecoin contraction as de-risking indicator (run #11, 2026-06-08)

When USH (Hatom stablecoin) supply BURNS >1% in a single week during a price decline, this signals borrowers actively closing CDP positions to release collateral and avoid liquidation. USH is the borrowing token in Hatom CDPs, so supply burn = position closures.

This week: USH -47,072 (-7.08%), the largest single-week burn observed. Synchronized with SEGLD -6,510 (-0.9%) and XEGLD -3,790 (-1.2%) supply contractions = cross-Hatom de-risking visible. Bearish signal for DeFi engagement: users actively reducing leverage.

Surface this in:
- `executive_summary` (when USH change >5%)
- `anomalies` (severity high when USH change >5%, medium when 1-5%)
- `defi_activity.analysis` (always, when any of USH/SEGLD/XEGLD move >1%)

### Critical TVL Lesson (run #5, 2026-04-27)

Lending protocols on MultiversX denominate contract balance in deposit-receipt tokens (HUSDC, HWBTC, HSEGLD, etc.), NOT in EGLD. Summing contract EGLD balance produces a near-zero TVL for the entire lending stack. The correct method is to sum the H-token market caps, which represent the total deposited collateral.

Applied to Hatom: previous TVL estimate was $528K (sum of EGLD-only contract balances). Corrected: $10.23M ($5.15M LSD + $4.37M Lending + $708K USH). A **19x underestimate** before correction.

### LSD Double-Count Avoidance

When a user stakes EGLD into Hatom LSD they receive SEGLD. If they then deposit SEGLD into Hatom Money Market they receive HSEGLD. Both SEGLD and HSEGLD have non-zero market caps, but counting both double-counts the same underlying EGLD. Same applies to SWTAO/HSWTAO and XEGLD (XOXNO's LSD has its own deposit market via the LSD Composability contract).

Rule: when computing protocol TVL, **exclude H-tokens that wrap LSDs**. Count the LSD itself once.

### TVL Method by Protocol Category

| Category | Method | Reason |
|----------|--------|--------|
| Liquid staking | LSD-token market cap | Underlying is delegated to validators, not held in contract |
| Lending | Sum of deposit-receipt token market caps | Balance is denominated in lent tokens, not EGLD |
| DEX (AMM) | Sum contract balance × 2 (pool ratio) | Both sides of pair counted |
| DEX (aggregator) | `transfers_24h` only — TVL is irrelevant | Non-custodial routing |
| NFT marketplace | NFT trading volume — contract balance is operational only | NFTs are escrowed but value is in NFTs not EGLD |
| Stablecoin | Stablecoin market cap | Direct measure of collateralized value |

**Health signal mapping**:
- `growing` — TVL up >5% WoW, transfers up
- `flat` — TVL within ±2%, transfers stable
- `shrinking` — TVL down 2-15% WoW, sustained
- `spiking` — TVL or transfers up >50% WoW (likely event-driven)
- `draining` — TVL down >15% WoW (concerning, investigate)

Always sum addresses per protocol — a single address can be misleading. xExchange has separate WEGLD contracts per shard; both must be summed for accurate TVL.

---


### Protocol-level transfers_24h (run #6, 2026-05-04)

The correct endpoint for protocol activity throughput is:
```
/accounts/{addr}/transfers/count?after={unix_ts}
```

Previous attempts using account-object fields (`scrCount`, `transfersLast24h`) returned 0 or null because those fields are not present in `/accounts/{addr}` response. The dedicated `/transfers/count` endpoint is the correct path. Verified with XOXNO Aggregator (12,181 transfers in 24h), OneDex (8,110), JEXchange Lite Pool (2,229).

## Anomaly Detection — Graceful Degradation (v2)

The agent now ships z-score logic on every run, with a documented fallback when sample size is insufficient.

### Three Methods, Selected by Data Availability

**Method 1 — Z-score** (used when N >= 4 data points exist for the metric in `learnings.json` `running_baselines`)
- mean = average of baseline array (excluding current)
- stddev = population stddev of baseline array
- z = (current - mean) / stddev
- Severity:
  - |z| > 4 → critical
  - |z| > 3 → high
  - |z| > 2 → medium
  - |z| > 1.5 → low (note as "approaching anomaly threshold")
- Set `method: "z_score"` and populate `average_value`, `stddev`, `z_score`

**Method 2 — Percent threshold** (fallback when N < 4 data points)
- |% change vs previous| > 50% → low
- > 100% → medium
- > 200% → high
- > 500% → critical
- Set `method: "percent_threshold"` and populate `change_pct`. Note in `description` that this is degraded mode and full z-score will activate at week N+1.

**Method 3 — Rule-based** (always available, complements above)
- Dormant wallet activations
- Exchange exits >25% in a single week
- Validator joining/leaving events with >50K EGLD
- Token holder declines on a streak ≥3 consecutive weeks
- **Failed forward indicator convergence** (new run #11): when 3+ of a prior run's `recommendations_for_next_run` bullish forwards resolve in the BEARISH direction within the same reporting period, this is a decisive bearish convergence signal. Emit as high-severity rule-based anomaly. Distinguishes random noise (one prediction misses) from regime shift (multiple bullish forwards all failing simultaneously).
- **Bilateral inverse rule magnitude deterioration** (new run #11): track ratio `|Hatom Lending EGLD %| / |EGLD price %|` across confirmed events. Series so far: 0.88, 0.80, 0.70, 0.21 (this week). Sustained decline = depositor capacity exhaustion. Emit when ratio drops below 0.30.
- Set `method: "rule_based"`

### Common False Positives to Filter
- Epoch transitions can cause temporary metric spikes
- Token listing/delisting on xExchange creates volume anomalies
- Weekend/holiday activity dips are not anomalies
- Single-week routing wallet activity (Binance restaking, OTC desk injection) is *expected* once flagged — don't re-flag the same pattern week after week

## Trend Indicators (v2)

Distinct from anomalies (point-in-time deviations), trend indicators capture multi-week trajectories — the leading edge of where the network is going.

### accelerating_exchange_outflows
For each exchange in `previous.json` `exchange_balances`, check whether the current WoW change is in the same direction as previous 2+ weeks.
- 3 consecutive weeks of decline → emit a trend entry with `cumulative_change_pct` and `interpretation`
- Example: Gate.io declined 3 weeks running (-25%, -22%, -22%) cumulating -54% — likely customer exit or treasury rebalance

### validator_movements
Compare provider list this week vs previous week:
- `providers_joining` — providers in current `/providers` but not in `previous.staking_providers`
- `providers_leaving` — providers in previous but not in current (or current locked = 0)
- `notable_joiners`/`notable_leavers` — providers with >50K EGLD locked

Sustained net validator joining = network growth signal. Net leaving = consolidation pressure.

### token_supply_events
Compare `supply` field for tracked tokens vs previous week:
- > 1% supply change for normal tokens → mint or burn event
- > 0.1% for stablecoins (USDC, USDT) → meaningful issuance/redemption
- 100% supply change (zero → nonzero or vice versa) → lock/unlock event

### consecutive_streaks
Across the running_baselines arrays, identify metrics that have moved in the same direction for 3+ consecutive weeks. The interpretation field should explain *what* the streak means (e.g. "EGLD price up 5 weeks → momentum regime").

### regime_shifts
Step-changes that look like regime breaks rather than mean-reverting noise. Distinct from anomalies — an anomaly is a point spike that could revert; a regime shift is a level change that persists.

Heuristic: if a metric jumps >2 sigma AND the new level is sustained for 2+ weeks, promote it from anomaly to regime_shift.

---

## Report JSON Schema — CRITICAL

The dashboard (`dashboard/src/types/report.ts`) enforces a strict schema. **A blank page means the JSON doesn't match** and the React tree unmounted due to an unhandled error (no App-level error boundary). The report JSON **must** have these exact top-level keys:

```
metadata, executive_summary, network_health, whale_intelligence,
staking_intelligence, token_activity, defi_activity, anomalies,
watch_list, meta_learning
```

### Two-layer pre-publish gate (run AFTER assemble, BEFORE manifest/commit/deploy)

**Layer 1 — Data-integrity audit** (added run #11 after the SWTAO/USH miss):

```bash
python3 scripts/audit_report.py reports/${REPORT_DATE}.json data/collected/${REPORT_DATE}.json
```

Catches the class of bug that schema validation cannot:
- Token API returning null price/marketCap (e.g., SWTAO-356a25 ran null this week, silently making Hatom LSD appear -26% EGLD WoW when the real value was -1%)
- Large supply events under-emphasized (e.g., USH -7.08% surfaced only in trend_indicators, not exec_summary — the audit flags any >5% supply change not appearing in TL;DR)
- Implausible protocol_breakdown WoW deltas (>25% suggests missing input data)
- Null-but-derivable fields (top_by_market_cap.holders, top_by_volume.previous_transactions)
- Excessive Unknown labels in large_transactions (>60% triggers a warning to trace recurring routers)
- APR distribution coverage below 95% of total delegated
- Hatom LSD sum = SEGLD + SWTAO (cross-check against the raw API totals)

Exit 0 if no errors (warnings allowed), 1 if errors.

**Layer 2 — Schema + dashboard invariant validator** (existing, added run #8):

```bash
python3 scripts/validate_report.py reports/${REPORT_DATE}.json
```

Checks three layers:
1. JSON Schema (`data/report-schema.json`) — types and enums
2. Dashboard-rendering invariants — required fields the React components call methods on
3. Enum string-literal unions

Exit 0 means safe to manifest+deploy. Non-zero exit means **do not push**; fix the JSON and re-run.

### Field-name canon (the parts the validator can't infer)

The dashboard's `dashboard/src/types/report.ts` is the source of truth. Common gotchas worth memorizing:

| Section | Required field name | Common wrong name |
|---|---|---|
| `trend_indicators.validator_movements.notable_leavers[]` | `previous_locked_egld` | `locked_egld_previous` ← run #8 broke this |
| `whale_intelligence.whale_tiers.{tier}_whales` | `count_current`, `total_balance_egld`, `previous_total_balance_egld` | `count`, `total_egld`, `total_egld_previous` |
| `whale_intelligence.exchange_flows.by_exchange[]` | `exchange`, `change_egld`, `pct` | `name`, `flow_egld` |
| `staking_intelligence.apr_distribution.buckets[]` | `label`, `min_apr_pct`, `max_apr_pct`, `provider_count`, `total_locked_egld` | `bucket`, `min`, `max`, `count`, `locked` |
| `token_activity.top_by_holders[]` | `previous_holders`, `holders_change` | `holders_previous`, `holders_wow_change` |
| `whale_intelligence.large_transactions[].timestamp` | ISO 8601 string | Unix int |

### Extending enums

If you genuinely need a new enum value (new flow type, new protocol category), extend ALL THREE in the same commit:
1. `data/report-schema.json` (the schema)
2. `dashboard/src/types/report.ts` (the TS union — additive only)
3. `scripts/validate_report.py` `ENUM_INVARIANTS` table
4. Then rebuild + redeploy the dashboard

### Why this matters

Run #8 had `locked_egld_previous` instead of `previous_locked_egld` in notable_leavers. JSON loaded fine, HTTP 200, but `formatEgldBare(undefined).toLocaleString()` threw at first render. Because there's no App-level error boundary, the WHOLE React tree unmounted — page completely blank, no spinner, no error message. The validator catches this class of bug before deploy.

### Deployment steps (run AFTER validator passes)
1. `cd dashboard && npx tsx scripts/generate-manifest.ts` — copies JSON to public/
2. `git add ... && git push`
3. `cd dashboard && vercel --prod` — deploy to Vercel
4. Return the stable URL: **https://dashboard-omega-lyart-99.vercel.app**

---

## Report Quality Checklist

Before committing the report, verify:
- [ ] All EGLD amounts are human-readable (divided by 10^18)
- [ ] All addresses are labeled where possible
- [ ] Every section has an analysis paragraph, not just tables
- [ ] Executive summary has 5 actionable bullets
- [ ] Watch list items from previous week are addressed (kept, updated, or graduated)
- [ ] JSON report matches the schema in data/report-schema.json
- [ ] previous.json is updated with current snapshot
- [ ] learnings.json is updated with this run's findings
- [ ] methodology.md is updated if new practices were established

---

### PAGINATE desk/router tx queries - prior throughput figures were ~4x undercounts (run #17, 2026-07-20)

**The collector's `/accounts/{addr}/transactions?size=50` call is NOT a 7-day window on a busy address.** On the OTC desks (400-900 txs/week) a 50-tx page covers only the most recent ~2.5 days, so every "7d throughput" figure reported in runs <= #16 was a truncated tail, not a weekly total.

Verified by re-querying with full pagination:

| Window | Reported at the time (size=50) | True paginated 7d, net of inter-desk |
|---|---|---|
| run #16 (Jul 6-13) | ~323K | **1,100,791** |
| run #17 (Jul 13-20) | 213K | **1,328,037** |

**Consequences**: (1) the historical throughput series (85K / 145K / 163K / 172K / 195K / 323K) is a set of lower bounds on inconsistently-sized windows and is NOT a comparable time series - no trend claim about OTC throughput built on it is defensible; (2) the pipeline was systematically understating the scale of the distribution it exists to detect, by roughly 4x.

**Rule**: page with `from=` until the `after=` boundary is reached (or the result set is empty), for desks, routers, and any high-activity tracked address. Then **subtract desk<->desk transfers** - UPbit OTC sent 315,000 to the OTC Distribution Wallet this week and 255,500 in the run #16 window; counting gross double-counts the pair. Backfill runs #13-#15 the same way before using the series.

### A wallet going to zero may be a MIGRATION, not a sale - resolve the receiver (run #17, 2026-07-20)

An emptied wallet reads as distribution from balance deltas alone, but two of this run's largest apparent "exits" were internal moves:

| Source | Amount | Destination | Reality |
|---|---|---|---|
| Coinbase Custody | 65,090 | erd1z4xerdjq6aa2 (nonce 0) | Custody migration - destination still holds it |
| Whale erd102hmf79en4 | 165,006 | erd18pwhucm0rd89 (nonce 0) | Wallet migration - destination still holds it |
| Whale erd15ku2r2j6 | 145,443 | KuCoin | **Genuine full exit onto an exchange** |

**Rule**: when a tracked wallet empties, resolve its single large outbound receiver and check that receiver's **nonce and balance**. Nonce 0 + holding the exact amount = migration, exclude from flow analysis. Only a receiver that is a known exchange/desk counts as distribution. Without this check, Coinbase would have been logged at -75,338 outflow when the real figure is ~-10K. This is the wallet-level analogue of the run #15 entity-decomposition rule.

### Read a distribution wave by DESTINATION, two hops out (run #17, 2026-07-20)

The run #16 rule said to check whether a CEX outflow's receiver is an OTC desk. Run #17 extends it one hop further: when the DESKS drain, trace where the desk outflows terminate. This week the five largest unlabeled desk recipients were all zero-balance, high-nonce pass-through routers forwarding to **Bybit and Binance.com**, with a further 150,000 sent straight back to UPbit.

That changes the interpretation completely: a 1.33M drawdown dispersing to many small unlabeled wallets would be retail distribution (supply absorbed by holders), whereas one terminating at exchange deposit addresses is **distribution onto venues** (supply arriving at the order book). Same headline number, opposite meaning. Two-hop tracing should be standard on any large desk drawdown. Corroborating evidence this week: net exchange flow simultaneously reversed to +193,747 inflow.

### Honor the |dPrice| >= 5% guardrail - record non-tests explicitly (run #17, 2026-07-20)

EGLD moved only +0.96% this week, below the run #12 guardrail, so the bilateral inverse rule was **not evaluable** and Hatom Lending's -0.63% EGLD-TVL move carries no information about it. The run recorded this as an explicit NON-observation rather than logging a spurious confirmation. The confirmed up-week series stands unchanged at 0.49 (run #15) and 0.72 (run #16).

The failure mode this guards against is subtle: on a small-move week the inverse sign will appear correct roughly half the time by chance, and logging those inflates the apparent evidence base for the rule. Any run where |dPrice| < 5% must state that the rule was not tested.

### PAGINATION IMPLEMENTED AND THE SERIES BACKFILLED - throughput is now a real time series (run #18, 2026-07-27)

Run #17 discovered the size=50 undercount; run #18 fixed it in the collector and backfilled the history.

`collect_run18.py` now pages `/accounts/{addr}/transactions` with `from=` until the `after=` boundary for both OTC desks, in BOTH directions, and nets out desk<->desk transfers. The runs #13-#15 windows were re-queried with the identical method.

| Run | Window | Net paginated 7d throughput (EGLD) |
|---|---|---|
| 13 | Jun 15-22 | 66,128 |
| 14 | Jun 22-29 | 186,124 |
| 15 | Jun 29 - Jul 6 | 506,053 |
| 16 | Jul 6-13 | 1,100,791 |
| 17 | Jul 13-20 | 1,284,688 |
| 18 | Jul 20-27 | 313,173 |

**Validation**: re-measuring the run #16 window reproduces 1,100,791 exactly, matching run #17's independently derived figure. Re-measuring the run #17 window gives 1,284,688 against the 1,328,037 reported at the time (-3.3%, boundary timing); the series uses the internally consistent numbers.

**What it revealed**: five consecutive weeks of escalating distribution peaking in run #17, then a 76% break. That structure did not exist in the truncated figures - the old series (85K/145K/163K/172K/195K/323K) was noise.

**Limits**: runs <= #12 are NOT backfillable (raw snapshots start at run #10 and the tx windows are no longer economically queryable). The comparable series starts at run #13 and must not be extended backwards. The `otc_pipeline_throughput_egld_7d` baseline in learnings.json was REPLACED outright in run #18 because it had been mixing desk-balance deltas with throughput values - any z-score computed against the old array was meaningless.

### A BASELINE ARRAY WHOSE UNITS CHANGE MID-SERIES IS WORSE THAN NO BASELINE (run #18, 2026-07-27)

`otc_pipeline_throughput_egld_7d` contained `[-881, 7028, 35401, 35401, 237717, 1328037]` - the first five are desk-balance DELTAS and the last is a true throughput figure. Nothing errored; the z-score just silently described a quantity that does not exist. Rule: when a metric's definition or units change, replace the whole baseline array rather than appending, and state in the same run that prior entries are not comparable.

### PRE-FLIGHT BECH32 VALIDATION (run #18, 2026-07-27) - closes a run #12 recommendation

Run #12 lost ~222K EGLD of Binance balance to an invalid-checksum address that returned HTTP 400 and silently produced nothing. The recommendation to pre-validate addresses stayed open for six runs. Run #18 hit the same bug again: run #17's KuCoin watch entry was invalid, so the KuCoin resolution test would have returned empty rather than erroring.

`scripts/validate_addresses.py` now checks every address in `known-addresses.json` and `previous.json` against the bech32 checksum. Run it BEFORE the collector; it exits 1 on any offender.

First run found **four** invalid entries: the KuCoin watch address, the System Delegation Manager (fixed to the canonical `erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqylllslmq6y6`), Hatom UTK Money Market and OneDex Launchpad (both flagged, not guessed - a wrong replacement is worse than a known gap).

**Why the failure mode is nasty**: an invalid address does not crash anything. It returns `{"__error__": "HTTP Error 400"}`, the balance helper returns `None`, and the entity silently contributes zero. Every downstream figure looks plausible.

### EXCLUDE NEWLY TRACKED ADDRESSES FROM THEIR FIRST WoW DELTA (run #18, 2026-07-27)

An address added to the tracked set mid-series has no prior-week balance, so entity netting books its ENTIRE balance as an inflow. This has now caused an error two runs running:

| Run | Address | Phantom |
|---|---|---|
| 17 | Coinbase Custody 2 (added as a migration destination) | +65,090 |
| 18 | a third Binance.com hot wallet absent from the stored top-60 | +6,995 |

This week the headline exchange flow was +166,978, of which +156,995 (94%) was non-flow once the Binance custody reload (+150,000, intra-entity parking) and the phantom were removed. True external flow was +9,983 - flat. Reporting the raw number would have manufactured a bearish signal.

**Rule**: every address contributing to a current-week entity total must also have a prior-week balance. If it does not, either seed the prior balance or exclude it from that week's delta and say so.

### PROMOTE A REPEATED NON-OBSERVATION AT A PRE-REGISTERED THRESHOLD (run #18, 2026-07-27)

The delegator base was reported as "flat again" for six consecutive runs. That is narrative cost with no information. Run #17 pre-registered the promotion criterion (a 6th flat week); it was met, and participation inertia is now a base rate rather than a weekly finding.

**Rule**: when the same non-event is reported three or more times, pre-register the threshold at which it becomes a background assumption, then stop re-reporting it. Only a genuine BREAK is newsworthy afterwards. The corollary matters too: having established that the base does not move with price, "flat delegators" can no longer be cited as bearish confirmation of a rally.

### WHEN EVERY TRACKED SUPPLY CHANNEL IS OFF AND PRICE STILL FALLS, SWITCH THE DIAGNOSIS TO DEMAND (run #18, 2026-07-27)

This pipeline is instrumented almost entirely on the supply side: OTC desks, throughput, custody wallets, exchange balances, routers. For runs #14-#17 that was sufficient - EGLD weakness had a traceable distribution behind it every week.

Run #18 broke the pattern. OTC throughput fell 76% with no desk reload, Binance's custody de-staking programme reversed into a +150,000 reload, and true external exchange flow was flat. Every supply channel switched off, and EGLD still fell 10.13% - while BTC rose 1.71% and ETH rose 5.35%.

The instruments that DID move were all demand-side: the Mega Whale absorber recorded zero transactions (Coinbase Routing pipe drained to 77 EGLD), DEX volume collapsed 61% while pool TVL and WEGLD supply ROSE (depth stayed, trading left), and bridged stablecoins resumed burning.

**Rule**: read the demand instruments as a group with equal standing, not as colour. And note the asymmetry that makes this the worse condition: supply exhausts, absent demand does not.

**Diagnostic tell**: a distribution week produces HIGH volume. Price falling on COLLAPSING volume with intact depth is an absent bid, not an aggressive offer.


### GROSS THROUGHPUT IS NOT DISTRIBUTION - NET THE DESK HUB PER VENUE, BOTH LEGS (run #19, 2026-08-03)

Run #17 established: read a distribution wave by DESTINATION, two hops out. Run #19 shows the rule must be applied SYMMETRICALLY, because the desks can be fed by the same venues they deliver to.

This week the desks moved 301,498 EGLD out and 307,283 in. Resolving both legs two hops:

| Venue | desk -> venue | venue -> desk | net |
|---|---|---|---|
| Bybit | 160,410 | 132,074 | +28,336 |
| Binance.com | 67,293 | 54,062 | +13,231 |
| Gate.io | 38,190 | 31,560 | +6,631 |
| UPbit | 0 | 67,000 | -67,000 |
| Unknown Whale I | 32,538 | 22,367 | +10,171 |

**240,063 EGLD (80%) round-trips to the venue that supplied it.** Genuine one-way movement is 61,435, with UPbit the only net source.

**Rules**:
1. Report TWO numbers every week: gross throughput (pipeline activity) and net one-way (distribution). They differed 5x this week.
2. The runs #12-#18 series is GROSS only - circularity was never measured. It is valid as an activity series and must NOT be described as distribution volume.
3. Do not append net one-way to the gross baseline array (run #18's units rule). `otc_net_one_way_egld_7d` is a separate array starting at run #19.

`scripts/trace_otc_hub_run19.py` performs the resolution and persists it into the collected snapshot as `otc_hub_trace`, so the netting is reproducible from stored raw data.

### A ZERO-VALUE TRANSACTION IS NOT AN EMPTY TRANSACTION - READ THE function FIELD (run #19, 2026-08-03)

Run #18 recorded the origin of the +150,000 Binance custody "reload" as unresolvable: the sending wallet erd1r3w62vq showed one inbound transfer of 0.0001 EGLD in 30 days. Its EGLD had arrived as a **smart-contract result**, which does not appear as a value transfer.

The answer was in its OUTBOUND list, on transactions with `value: 0`:

| Date | function | target |
|---|---|---|
| 2026-07-09 | `unDelegate` | binance_staking delegation contract |
| 2026-07-22 | `withdraw` | binance_staking delegation contract |
| 2026-07-22 | transfer 150,000 | Binance Staking custody |

The unbonding period lines up with the -148,941 the binance_staking PROVIDER shed in the run #16 window. So the "reload" was the delegation unwind completing, not accumulation - and run #18's "strongest bullish structural counter-signal" was withdrawn.

**Rule**: before concluding a wallet's funding is untraceable, read `function`/`action` on its zero-value transactions. Delegation-layer movements (unDelegate/withdraw/reDelegateRewards) move EGLD via SC results and are invisible to a value-transfer scan. This is the delegation-layer analogue of the run #15 custody tx-scan rule.

### THREE CONSECUTIVE RUNS HAVE HAD A HEADLINE CONCLUSION OVERTURNED BY MEASURING ONE LEVEL DEEPER (run #19, 2026-08-03)

| Run | Conclusion as first reported | What overturned it |
|---|---|---|
| 17 | OTC throughput ~323K (run #16 window) | pagination: true figure 1,100,791 (~4x) |
| 18 | otc throughput baseline z-scores | the array mixed desk-balance deltas with throughput |
| 19 | "supply channels switched off"; "custody de-staking reversed" | circularity netting; the funder's unDelegate/withdraw |

The common mechanism is that a flow AGGREGATE was reported as a fact before its constituent legs were resolved. **Rule**: treat any single-week structural conclusion drawn from an aggregate as provisional, and say so in the report, until the legs have been resolved.

### DEMAND-SIDE INSTRUMENTS (run #19, 2026-08-03) - closes run #18's top recommendation

Three standing metrics, all built this run:

1. **DEX turnover ratio** = sum(volume24h) / sum(totalValue) over `/mex/pairs`. Turns "depth held while trading left" into a measurement. Run #19: 2.14% vs 4.06% the prior week on -2.8% pool TVL. Independent of both price and the flow plumbing, which makes it the cleanest demand series the model has.
2. **Identifiable-bid composite** = Coinbase Routing wallet balance + Mega Whale erd18mv2z6r2 delta. Run #19: zero absorption for a second consecutive week.
3. **Withdrawal breadth** = distinct non-exchange addresses receiving >1,000 EGLD out of tracked exchange wallets. **Must be reported ex-pipeline**: 84% of this week's volume went to OTC desks, feeders and routers. Raw 34 addresses / 361,830 EGLD; ex-pipeline 20 addresses / 56,896 EGLD.


### NET THE OTC HUB OVER THE WAVE, NOT THE REPORTING WEEK (run #21, 2026-08-17)

Circularity does not respect week boundaries, so weekly netting counts legs whose mirrors sit in the adjacent window. Run #21 measured it directly:

| Frame | Gross out | Circular | Net one-way |
|---|---|---|---|
| Week Aug 3-10 (run #20) | 604,086 | 69% | 188,658 |
| Week Aug 10-17 (run #21) | 222,532 | **38%** | 138,265 |
| **Wave Aug 3-17, netted feed-to-drain** | **826,619** | **74%** | **210,922** |

Summing the two weekly nets gives 326,924 - a **55% overstatement** of the 210,922 the wave actually delivered. The mechanism is visible in one venue: UPbit fed 319,000 into the desks in the first week and took 130,000 back out in the second, so week 1 books UPbit as a -319,000 source and week 2 as a +116,000 receiver, while over the wave it is a -73,000 net source.

**Rules**:
1. Report the WAVE-window net (feed-to-drain) alongside the weekly figure. Treat every weekly net one-way number as an **upper bound**.
2. The 38%-circularity reading is the diagnostic tell: when a week's circularity drops far below the 63-80% band, a return leg has landed whose feed sat in a prior window.
3. Do not append a wave-window figure to the weekly baseline array (run #18's units rule) - it lives in `otc_net_one_way_measured_windows` keyed by window.

### THE STAKED-MINUS-DELEGATED RESIDUAL IS NOT A DIRECT-NODE MEASURE (run #21, 2026-08-17)

`economics.staked` minus the sum of `/providers` `locked` also contains **delegation unbonding in flight**. An `unDelegate` removes EGLD from a provider's `locked` immediately, but the EGLD stays inside the staking module for the 7-10 epoch unbonding period, so:

```
d(residual) = d(direct-node stake) + d(new unDelegations) - d(completed withdrawals)
```

Run #21: the residual flipped +282,713 and ONE wallet explained 229,865 of it - `unDelegate` of 149,585 from p2p_org_ (2026-08-15) and 80,279 from a second provider (2026-08-14), both confirmed still unbonding via `/accounts/{addr}/delegation`. Corrected, direct-node stake GREW +52,848.

This **withdraws the runs #18-#20 "direct-node unwind"** (~215K, described in run #20 as the largest unexplained structural flow tracked). A falling residual alongside rising delegation is equally consistent with earlier unbondings *completing*.

**Method**: `/accounts/{addr}/delegation` returns, per delegation contract, `userActiveStake`, `userUnBondable` and a `userUndelegatedList` of `{amount, seconds}`. Query it for the wallets behind any provider move above ~20K EGLD before attributing a residual to node operators. The protocol Staking SC cannot be used as a cross-check: `erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqplllst77y4l` returns a valid `/accounts` response but **HTTP 400 on every transaction query** (with/without status, with/without direction filter, and on the global `/transactions?receiver=` form).

### A FEE CHANGE IS NOT EVIDENCE OF COMPETITION (run #21, 2026-08-17)

Run #20 read `egldstakingprovider` cutting 24% -> 15% as "the first competitive fee repricing in twenty runs". One week later the same provider set **serviceFee = 1.0 (100%)**, and `procryptostaking` - the incumbent named as the one that had *not* cut - did the same, both taking delegator APR to 0 while still running 50 nodes each. Owner wallets differ, so it is two unrelated operators.

**Rules**:
- A single parameter move by an incumbent under pressure is ambiguous between competing, winding down and squeezing. Wait for the direction to persist two weeks, or for stake to actually return, before assigning intent.
- `serviceFee: 1.0` with `apr: 0` is a REAL API state (verified on `/providers`, `/providers?identity=`, `/providers/{address}`), not an indexer artifact. Such providers fall outside every APR bucket, so report bucket coverage against total delegated (run #21: 5 providers, 251,266 EGLD, 2.3% of delegated stake, at 0% APR).
- A zero-yield signal moved **capital but not people**: egldstakingprovider lost 26% of its book and 13 of ~1,124 users. This is the strongest available confirmation of participation inertia.

### DECOMPOSE DELEGATION TVL AS SURVIVORS PLUS LEAVERS (run #21, 2026-08-17)

A provider whose `locked` goes to 0 drops out of the `locked>0` working set, so its whole balance silently becomes a validator-departure statistic instead of part of the TVL delta. Run #21 reconciles only with all three terms:

```
-212,841 (negative moves) + 99,353 (positive moves) - 122,947 (the leaver's full locked) = -236,435
```

### CHECK THE CHEAP THING BEFORE REPEATING AN EXPLANATION (run #21, 2026-08-17)

Runs #19 and #20 both attributed MEX outperforming EGLD to "stale pricing in illiquid pairs" without querying the pair. One field already present in the collected snapshot (`totalValue` on `/mex/pairs`) shows MEX/WEGLD is the **#2 deepest pool on xExchange** at $291,459 - 15.9% of all pool TVL - with 125 trades in 24h. The explanation is withdrawn.

**Rule**: an explanation repeated in a second run must be verified in that run, not restated. Three claims were withdrawn in run #21 and all three had the same shape: a quantity reported before the cheapest available check was run.

### TRACE THROUGH THE CALLERS WHEN A CONTRACT HAS NO OUTBOUND VALUE TXS (run #21, 2026-08-17)

The XOXNO LSD contract settles redemptions via smart-contract results, so `/accounts/{addr}/transactions?sender=` returns **zero** value transactions no matter the window. The working method is to enumerate the *callers* by function (`unDelegate`, `unDelegatePending`, `withdraw`, `withdrawPending`) and follow each caller's own outbound flows. Run #21: 8 wallets, onward flows of 80-600 EGLD each, 531 EGLD into native delegation contracts and ZERO to any labelled exchange - retail rotation, not an exit. The same technique resolved the delegation unwind.


### THE SCOREBOARD AND ERRATA ARE NOW REPORT FIELDS - MAINTAIN THEM EVERY RUN (run #21, 2026-08-17)

Two schema additions turn the model's self-correction from prose into structure. Both are **forward-only** and must be populated by every future run, or the dashboard panels silently degrade to their null states.

**1. `pre_committed_tests` (top-level array).** Every falsifiable claim registered with a numeric threshold. Each run must:
- RESOLVE the prior run's open tests: set `status: "resolved"`, `resolved_in_run`, `measured_value`, `resolution`, and an `outcome` of `as_predicted` / `against` / `inconclusive` / `withdrawn`.
- REGISTER this run's tests as `status: "open"` with `threshold` and `branches` (condition -> reading) filled in BEFORE the next run's data exists.

`inconclusive` is a real and useful outcome - run #21's wave-escalation test resolved that way, and the attempt to force it into a branch is what exposed the weekly-netting error. `withdrawn` means the test's premise died rather than the test resolving (both the fee-cut and direct-node tests ended there).

**Never reconstruct tests from older prose.** Runs <= #19 have no structured tests and must stay that way; a falsifiability ledger built on retrofitted data entry is worthless.

**2. `meta_learning.withdrawn_claims` (array).** Claims published in EARLIER runs that this run withdraws: `claim`, `asserted_in_runs`, `withdrawn_in_run`, `reason`, optional `replacement`. `dashboard/scripts/generate-manifest.ts` aggregates these across all reports into `public/errata.json`, which the dashboard uses to (a) warn on a superseded archived report and (b) show the correcting run its own withdrawals.

**Why this matters**: the archive is immutable. Before run #21 a reader opening run #19 saw the direct-node-unwind narrative asserted with full confidence, with nothing indicating it had been withdrawn. For a report whose distinguishing virtue is self-correction, an archive that silently re-asserts corrected claims is the one bug that undermines the project.

**Dashboard panels added run #21** (all read from report fields, no hardcoded data): `OtcPipeline` (gross vs net one-way per week with a bracket over the runs belonging to one wave - the bars inside the bracket sum to more than the bracket's own number, which IS the finding), `UnbondingCard` (one number, one countdown, one open question - the only forward-looking quantity tracked), `ErrataBanner`, `Scoreboard`. Validator invariants were extended in the same commit for `pre_committed_tests[]`, `meta_learning.withdrawn_claims[]`, `otc_pipeline.wave_window_netting` and `staking_intelligence.unbonding_in_flight`.


## Evolution Log

| Run | Date | Changes |
|-----|------|---------|
| 1 | 2026-04-02 | Initial methodology established. Per-account whale detection, entity resolution, staking HHI, baseline snapshot format. |
| 2 | 2026-04-07 | Added BTC/ETH price context. Confirmed OTC desk pattern for recurring large exchange outflows. Added `exchange_balances` and `watch_addresses` to previous.json for cleaner WoW tracking. Discovered that `/providers` total locked ≠ `/economics` staked (different metrics). |
| 3 | 2026-04-13 | Established intermediary wallet investigation pattern for routing wallets (check nonce + immediate txs). Confirmed mex/tokens volume24h is unreliable (returns $0) — use mex/pairs exclusively. OTC desk lifecycle confirmed at ~3 weeks. Begin 3-point running baselines for z-score prep. |
| 4 | 2026-04-20 | Confirmed routing wallet nonce is NOT always near-zero (nonce 80 wallet was pure pass-through). Confirmed low nonce ≠ cold storage guarantee (nonce 4 wallet reactivated). Established Coinbase OTC pattern: simultaneous large inflows+outflows from different counterparties = OTC intermediation — watch net balance, not gross flows. mex/pairs field names confirmed: baseName, quoteName, volume24h, totalValue. 4-run z-score baselines now active. |
| 5 | 2026-04-27 | **Schema v2 expansion**: top 10/10/5 token coverage, whale tier stratification (mega/large/mid >1M / 100K-1M / 10K-100K), exchange entity netting, per-protocol DeFi breakdown (xExchange, Hatom, AshSwap, OneDex, XOXNO, JEXchange), APR distribution histogram, staking churn metric, top APR + lowest fee outliers, dormant_days field on dormant_activations, graceful-degradation z-scores (z when N>=4, % threshold when N<4, rule_based always), new trend_indicators section (accelerating_exchange_outflows, validator_movements, token_supply_events, consecutive_streaks, regime_shifts). All schema additions backward-compatible. |
| 5.1 | 2026-04-27 | **XOXNO ecosystem expansion**: added 14 XOXNO contracts to known-addresses.json under new `defi_xoxno` section. Split XOXNO tracking into 4 sub-protocols (LSD, Aggregator, Marketplace, Other) since they have different metrics. **TVL method discovery**: for liquid staking protocols, contract balance is misleading — use the staked-derivative token's market cap as TVL proxy (XEGLD-e413ed market cap = $1.54M = ~359K EGLD staked). For non-custodial routers (XOXNO Aggregator, OneDex), TVL is irrelevant — the metric is `transfers_24h`. **Activity ranking**: XOXNO Aggregator handles 21,926 transfers/24h (highest single-contract throughput on the network); OneDex 13,308; JEXchange 3,772; xExchange 5 contracts combined 3,120. **Dashboard ergonomics**: added expand/collapse to long DataTables (top 5 default → "Show all (N)" footer button) for providers, wallets, transactions, tokens, protocol breakdown — full-set sort still active when collapsed. |
| 5.2 | 2026-04-27 | **Hatom ecosystem expansion + lending TVL methodology fix**. Hatom has 59 contracts total (deployer wallet erd1cc2yw...99pvt); previously tracked 16 → now 39. Added: 13 money markets (EGLD, sEGLD, USDC, USDT, WBTC, WETH, BUSD, HTM, MEX, UTK, wTAO, swTAO), TAO Liquid Staking + Wrapped TAO Minter, isolated lending (EGLD + wTAO), USH stablecoin suite (4 strategy contracts), 7 asset facilitators (cross-protocol), Booster v2, Price Aggregator v2, deployer wallet. **CRITICAL TVL FIX**: lending protocols denominate balance in H-tokens (deposit receipts), not EGLD — summing contract EGLD balances missed the entire lending stack. Corrected method: sum H-token market caps. **Hatom TVL recalibrated $528K → $10.23M** (~19x underestimate before correction). Split Hatom into 3 sub-protocols in `protocol_breakdown`: Lending ($4.37M), Liquid Staking ($5.15M = SEGLD + SWTAO), USH ($708K). **New ranking**: Hatom dominates MultiversX DeFi with 70% of total tracked TVL ($10.23M of $14.7M total). xExchange $2.32M, XOXNO LSD $1.54M. **Double-count avoidance rule**: exclude H-tokens that wrap LSDs (HSEGLD, HSWTAO) since the underlying value is already in the LSD-token market cap. |
| 6 | 2026-05-04 | **Cross-exchange OTC funnel discovery**: First observed shared OTC infrastructure on MultiversX. Binance.com 2 (erd1sdsl) → 3 routing wallets (erd16nws nonce 169, erd1k4r6 nonce 180, erd1de38 nonce 147) → UPbit OTC Desk + OTC Distribution Wallet. Pattern: identical-amount chunks (5,999/7,999/8,000 EGLD), forwarded within minutes, near-zero-balance routers. **Yield-chasing migration confirmed** as a recurring trend indicator: Ninja Staking +15.5K and Egld Staking Provider +14.2K (both 0%-fee, 9%+ APR) gained the equivalent of what 5 lower-APR providers lost — first activation after 4 weeks of inertia. **API endpoint discovery**: /accounts/{addr}/transfers/count?after={ts} is the correct endpoint for protocol-level transfers_24h (NOT account object fields). **Hatom H-token discovery**: /tokens?search={ticker} filtered for 'Hatom' name prefix is reliable token-discovery path; full Hatom Lending stack: HUSDC + HUSDT + HEGLD + HWBTC + HWETH + HHTM + HMEX + HUTK + HWTAO + HBUSD = $4.41M. **Z-score reversion validated**: EGLD price went +3.29σ → +0.77σ in one week, confirming the run #5 'one-week event' classification. Stored FULL provider list (108) in previous.json — enables churn analysis from run #7. New section in known-addresses.json: 'exchange_routers' with 3 entries. |
| 7 | 2026-05-11 | **Cross-exchange OTC pipeline VALIDATED**: 8 new routing wallets traced confirming multi-hop CEX-to-CEX settlement layer. Routes: UPbit OTC + OTC Distribution → routers (erd1g8ll, erd1n5wcu, erd1cwkw3, erd1dmmh5, erd1fs0c4, erd17cfk3, erd1fdkq6, erd1ljlcx) → Bybit/Binance/KuCoin. PLUS reverse flows: Bybit → erd1rffkz8zwp3 → KuCoin; KuCoin → erd14n5vtgezss → Bybit (bidirectional). The OTC fabric is general-purpose CEX-CEX settlement, not unidirectional distribution. **First major unstaking event**: -325K from /economics staked module, +377K to Binance Staking wallet. Single-source single-destination flow (Binance unstaked ~377K from direct nodes). 50% staked-ratio approach REVERSED 49.50% → 48.33%. **NEW RULE**: When EGLD price ripping, lending TVL underperforms (depositors withdraw to capture gains). Hatom Lending flat in USD = -13% in EGLD terms during the +14.7% rally. **NEW RULE**: Major staking-wallet balance increases (Binance Staking +377K) predict directional pressure within 1-2 weeks — the capital is parked, watch for movement. **NEW RULE**: DEX volume during EGLD rallies concentrates in WEGLD/USDC (91% this week). Single-pair dominance = CEX-derived buyers parking in stablecoin pairs. **Z-score history**: egld_price +3.29σ (run #5) → +0.77σ (run #6) → +3.40σ (run #7). Second elevation in 4 weeks suggests structural pattern, not noise. **DEX volume +5.86σ — largest z-score in tracked history**. Watch for regime shift confirmation next week. **Yield-chase sustained for 2 weeks**: Egld Staking Provider +17K (after +14.2K last week), Ninja Staking +3K. Top losers all 7-12% fee 7-9% APR. **All 10 protocol_breakdown TVLs computed**: Hatom Lending $5.31M, Hatom LSD $4.49M, Hatom USH $686K, XOXNO LSD $1.71M, xExchange TVL aggregated. |
| 9 | 2026-05-25 | **Binance staking-custody accumulation discovered**: hot wallet erd1sdsl -316K -> Binance Staking custody wallet +267K (now 3.38M), but the protocol staked module rose only +2K -> capital PARKED, not delegated. Combined with run #7's 377K, Binance holds a large undeployed EGLD position in its staking wallet. New top forward indicator: track this wallet vs economics.staked weekly (jump in staked = delegation/bullish; drawdown to hot wallets = distribution/bearish). **NEW RULE - degenerate z-scores**: when a baseline's stddev is tiny relative to the metric (total_delegators sd~18 on ~179K base), small moves produce spurious huge z-scores (z=-4.5 for a -0.03% move). Always cross-check absolute % change; downgrade severity when economic move <0.1%. **CONFIRMED - decompose entity netting**: intra-entity wallet shuffles (Binance hot->staking custody) dominate the headline exchange-flow number; always break entity net into per-wallet moves before calling a flow bullish/bearish. **Exchange-flow reversal VALIDATED**: run #8's +169K bearish inflow was a single-week reaction (reverted to -56K outflow) - the two-week confirmation rule worked. **ZoidPay DEX event**: ZPAY +59% price, ZPAY/WEGLD pair captured 40.8% of xExchange volume - first non-WEGLD/USDC pair >40% in tracking history; WEGLD/USDC dominance 91.6%->56.2%. **Yield-chase week 4** with rotating leadership (procryptostaking +17K, valuestaking +16K took over from ninjastaking/egldstakingprovider). **MEX z-score activated** (N=4, z=-0.83 normal). **Bilateral inverse rule scales with price**: +2.3% price -> Hatom Lending -1% EGLD (mild). **Token supply-event fix**: previous.json now stores supply_raw (raw integer) so run #10 can diff like-for-like (prior runs stored decimals-adjusted, breaking comparison). **OTC source funder found**: erd12tq6ax5k -> erd17l22 (~2K). erd17l22 dormant after run #8 distribution wave; OTC desks in distribution phase (~145K throughput). |
| 8 | 2026-05-18 | **OTC source wallet template ESTABLISHED**: Tracing run #7's flagged Unknown Whale erd17l22 (last week +58K) revealed it distributes 2K EGLD chunks through erd1nhtq4 (nonce 2543, ~7.5K balance) → erd1ecyftln (nonce 50, 0 balance) → OTC Distribution Wallet + UPbit OTC Desk. erd17l22 is therefore an OTC SOURCE wallet — completing the missing upstream link in the pipeline taxonomy (source → router → desk → desk-router → exchange). Detection method: when a top-100 non-exchange whale shows large WoW balance change, query top 1-2 outbound recipients, then trace through 2-3 hops — typically terminates at a known OTC desk. **BILATERAL INVERSE RULE CONFIRMED**: Run #7 saw Hatom Lending -13% EGLD during +14.7% rally; this week's mirror image: Hatom Lending +13.6% EGLD during -16.9% decline, Hatom LSD +21.9% EGLD. Depositors capture gains during rallies, DCA during dips. Useful as leading indicator of expected behavior. **DEX volume regime-shift watch CLOSED**: Run #7 +5.86σ peak ($328K) fully reverted to -0.67σ ($75K), -77% retrace. Confirmed event-driven anomaly, not regime. **Yield-chase PROMOTED to regime shift** after 3 consecutive weeks: ninjastaking +37.9K cumulative (run #6/7/8: +15.5K/+3K/+19.4K), egldstakingprovider +38.1K cumulative. Both providers near-tripled their stake in 3 weeks. **Exchange flows reverted to NET INFLOW** during the decline (-17%): +169K EGLD onto exchanges (Binance +76K, Coinbase +39K, Gate.io +21K, UPbit +14.5K). Classic bearish setup, opposite of run #7. **NEW QUIRK**: Always trim top-50-vs-top-50 when computing whale tier deltas. Run #7 stored only top 50 in previous.json — fetching top 100 silently inflated mid_whale tier (reported +30 wallets where actual is +1). **NEW QUIRK**: Hatom H-token identifiers — use `/tokens?search=Hatom` not guessed suffixes. Correct: HUSDC-d80042, HEGLD-d61095, HUSDT-6f0914, HWBTC-49ca31, HWETH-b3d17e, HBUSD-ac1fca, HHTM-e03ba5, HMEX-df6df7, HUTK-4fa4b2, HWTAO-2e9136, HSEGLD-c13a4e, HSWTAO-6df80c. |
| 10b | 2026-06-01 | **APR/Fee units schema bug fixed + retroactive migration**. The MultiversX /providers API returns `apr` already in percent units (6.37 = 6.37%) but `serviceFee` as a fraction (0.12 = 12%). Inconsistent. The pipeline was storing both raw, so `apr_pct` was correct but `fee_pct` was 100× too small in the JSON. Dashboard's `cleanServiceFee()` formatter (just `.toFixed(2) + "%"`) renders apr_pct correctly but rendered fee_pct=0.12 as "0.12%" instead of "12%". Bug present in runs #8 and #9 only — earlier runs happened to store `fee_pct` in percent units, #8 changed the convention silently. **Fix**: assembler now stores `fee_pct = serviceFee * 100`, matching apr_pct's percent convention. Markdown drops the `*100` everywhere. **Retroactive migration**: `scripts/migrate_fee_pct.py` patched runs #8 and #9 in-place (idempotent guard: only multiplies if max(fee_pct) <= 1.0). **NEW METHODOLOGY**: unit conventions for stored numeric fields must be documented in the schema. New rule — every `*_pct` field in the JSON is in percent units (12.0 means 12%), never a fraction. Validator could/should enforce this. **DONE same day**: raw collected.json now persisted under `data/collected/{REPORT_DATE}.json` and committed (1.6 MB this run; ~80 MB/year steady state). Backfilled run #10. AGENT_PROMPT.md updated so future runs save automatically. Earlier runs (#1-#9) only have whatever data was carried forward into the report JSONs — not backfillable retroactively. |
| 11a | 2026-06-08 | **DELEGATOR/PROVIDER REWARD-BEHAVIOR ANALYSIS** (new layer added late in run #11). New script `scripts/delegator_behavior.py` traces what individual delegators and provider operators do with EGLD rewards. Method: for each `claimRewards` event on top providers in a 7d window, look up the claimant's next outbound EGLD tx within 72h and classify (sold to CEX / rotated to another provider / DeFi deposit / held). For provider operators: query `ownerAddress` outbound flows over 30d. **Run #11 baseline findings**: function-level compound rate = **61.9%** across top 8 providers (348 redelegate vs 214 claim); retail (<1 EGLD/claim) does NOT sell rewards (0 of 68 went to a CEX, 88% held in-wallet); institutional (50-1000 EGLD/claim) splits ~50/50 sell vs hold by value (small sample of 3); zero provider operators sold to exchanges in 30d (all routed to treasury wallets). **NEW RELATIONSHIP DISCOVERED**: truststaking operator wallet = `erd1x45vnu7…` = **XOXNO: Deployer Wallet**. truststaking is the 4th-largest provider (366K locked, 7,171 users); XOXNO has both a flagship LSD AND control of a top delegation provider — significant strategic position. 30d operator outbound: 205 EGLD to held_or_other + 135 EGLD to defi_deposit (likely XOXNO LSD or XOXNO contracts). **New `staking_provider_operators` section added to known-addresses.json** with 7 operator wallets for the top providers. **API quirks**: (1) `/providers?size=N` parameter is IGNORED — always returns all ~185 providers; must slice client-side. (2) `urllib.parse.urlencode` requires explicit `import urllib.parse` at module level (Python scoping bug if imported inside function — silently fails as `__error__` dict). |
| 11 | 2026-06-08 | **EGLD FLOOR BROKE, BULLISH FORWARDS COLLAPSED**: EGLD -15.7% to $2.95, broke run #10's $3.50 floor, z=-3.32σ HIGH severity. 5-week cumulative -37% from May 4 peak. EGLD UNDERPERFORMED BTC (+1.3%) and ETH (+3.6%) - decoupled to the downside, MultiversX-specific weakness. **NEW PATTERN: 'failed forward indicator' as bearish signal**: 3 of 4 run #10 bullish forwards resolved BEARISH simultaneously - (1) Binance Staking custody STALLED at 3.51M (3-week accumulation ended, no delegation, no distribution); (2) $3.50 floor BROKE; (3) Coinbase 3-week outflow streak REVERSED (+43K inflow this week from a 3-week -62K outflow streak). When 3+ bullish forwards fail together during a decline, it is a decisive bearish convergence. The only directionally validated prediction was the BEARISH-for-retail OTC distribution wave. **OTC distribution wave HIT ON SCHEDULE (week 1 of 1-3 predicted window)**: UPbit OTC -14K (-30%), OTC Distribution -12.4K (-28%), combined -26.4K. Retail throughput 163K in 7d. The load-distribute cycle is now empirically validated at 1-week minimum period. **Newly-issued token detection WORKAROUND SUCCEEDED** (6-run blocker resolved): /accounts/erd1qqqqqqqqqqqqqqqpqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqzllls8a5w6u/transactions?function=issue returns ESDT issuance txs. Decode tx.data hex segments split on @ to extract [name, ticker, supply, decimals, ...flags]. Look up identifier via /tokens?search=<NAME>. 3 issuances detected (FRA, GSN, GTA - all low-quality spam, 0-2 holders). **Bilateral inverse rule 5th confirmation but MAGNITUDE DETERIORATING**: response ratios across events 0.88, 0.80, 0.70, 0.21 (this week). Hypothesis: depositor capacity diminishing OR conviction reducing as decline persists. **Yield-chase regime ENDED at week 5**: cohort net flow -2.6K, 3 of 5 prior leaders reversed; only ninjastaking sustained (+38K cumulative over 5 weeks). **Synchronized LSD contraction** during decline (Hatom LSD -1.6% EGLD, XOXNO LSD -1.4% EGLD) - new unusual pattern; watch for confirmation. **API quirk - funder address typo**: erd12tq6ax5k49dkp4lwmuvdv8sa9df5mqjnrv2mmjnxkv4m5ns562vsmtaujp is the ACTUAL funder (not the typo-variant carried from run #10). Now canonicalized in known-addresses.json. **Largest absolute delegator drop in tracking history**: -447 WoW (vs typical -24 to -53). Capitulation pattern emerging. |
| 10 | 2026-06-01 | **OTC PIPELINE FULLY TRACED TO BINANCE ORIGIN**: Verified erd12tq6ax5k as the missing link funder. 14d inbound = 100% from Binance.com hot wallet (erd1sdsl, 8,972 EGLD); 7d outbound = 100% to erd17l22 (OTC source). Balance 0, pure pass-through, nonce 1505 (heavy historical use). Full pipeline: Binance.com → erd12tq6ax5k (funder) → erd17l22 (source) → chain routers → UPbit OTC Desk + OTC Distribution → retail. Implication: Binance is the ultimate originator of MultiversX on-chain OTC distribution. New tracing methodology: query candidate funder's 14d inbound, check sender concentration + balance + outbound mirroring. **BINANCE STAKING CUSTODY 3RD WEEK OF ACCUMULATION** (3.11M → 3.38M → 3.51M, +402K cumulative). Protocol staked module barely moved — capital remains PARKED. Promoted from anomaly to structural-position regime shift. **EGLD -11.84% to $3.50, broke prior $3.74 floor**. z=-2.09σ (medium). 4-week trajectory -25% from May 4 peak. EGLD underperformed BTC (-1.4%) and ETH (-2.4%). **BILATERAL INVERSE RULE NOW WELL-CALIBRATED** across 3 events: +14.7%/-13%, -16.9%/+13.6%, -11.8%/+8.3% (linear magnitude relationship). **OTC DESKS REVERSED TO LOADING PHASE** (UPbit OTC Desk +56%, OTC Distribution +54%, combined +32.6K) — predicts new distribution wave in 1-3 weeks. **YIELD-CHASE REGIME STALLING WEEK 5**: cohort net flow dropped from ~+50K cumulative weeks 1-4 to +3.5K this week (only procryptostaking sustained; valuestaking/egldstakingprovider/orius all reversed). **ZoidPay/WEGLD dominance FULLY REVERTED** 40.8% → 8.9% — confirms run #9 event-driven. **TOKEN SUPPLY EVENT DETECTION ACTIVE** (supply_raw diff): WEGLD +4.7% (+26K wrapped) flagged as first real event. **NEW METHODOLOGY RULE**: filter erd1qqqq* system staking contracts from validator joiner/leaver lists — protocol direct-node aggregators that move above/below threshold are not real validator events. **API quirk**: /tokens/{id} batch hits HTTP 429 with sub-0.5s delays; use ≥0.5s between H-token mcap queries. |
| 14 | 2026-06-29 | **XEGLD SUPPLY COLLAPSED -29% + on-chain conviction DIVERGED from price**: XOXNO LSD supply fell 321,592->227,765 (~94K redeemed) in one week - largest single-protocol LSD supply move in tracking, XOXNO-specific (SEGLD flat). Supply-first LSD methodology (run #13) validated under stress - mcap framing would have buried it in the -10.5% price drop. **EGLD -10.5% to $2.55 (2nd-largest weekly drop), but a BROAD-MARKET dump** (BTC -6.4%, ETH -9.5% WoW), not EGLD-specific decoupling; z only -1.75σ (baseline widened by the multi-week decline). **DIVERGENCE**: despite the dump, protocol staked ROSE +81K (buy-the-dip), delegator base FLAT 2nd week at 174,407 (capitulation confirmed a one-shot), yield-chase REIGNITED (ninjastaking +11.6K, star_staking +7.7K, pi-staking +7.1K/+24 users - last run's isolated entry kept drawing), reward compound rate RECOVERED 55.31%->58.54%. **NET EXCHANGE FLOW REVERSED to -222K outflow** (Binance hot -158K, Bybit -56K) after a 3-week inflow streak - BUT distribution shifted channel: OTC pipeline ran a RECORD 195K throughput while reloading desks +35K. NEW RULE: read exchange flow JOINTLY with OTC throughput - a dump-week outflow is ambiguous (self-custody vs OTC routing). NEW RULE: whale-tier boundary-crossing guard (erd18mv2z6r2 crossing 1M created a phantom +997K mega swing). **OTC distribution wave HIT on schedule** (run #13 predicted week 1-3; arrived week 1). **Binance Staking custody STALLED 4th week** at 3.51M (7 weeks parked; the +81K staked came from yield-chase, not custody). **Stablecoin burn ACCELERATED 2nd week** (USDC -1.3%, USDT -3.7%; USH -3.2% CDP de-leveraging resumed). **Mega Whale erd18mv2z6r2 ACTIVATED** (+11K, crossed 1M; Apr-18 OTC-deal counterparty). **EMRS-6e4067 is a GENUINE large-cap** (10,331 holders, 151,107 txs - correcting run #13's thin-float assumption). **dataApi guard implemented** - recovered 3/4 tokens; SWTAO stayed null all run (WTAO also null) -> carried-prior-price fallback. 8/9 prior action items completed. |
| 16 | 2026-07-13 | **EGLD DECOUPLED TO THE UPSIDE vs a RECORD OTC DISTRIBUTION RELOAD - demand vs staged supply**: EGLD RIPPED +15.93% to $3.13 (2nd up-week) while BTC -0.2% / ETH +0.7% were FLAT - the FIRST EGLD-specific up-move of the cycle, flipping the high-beta-laggard pattern to potential leader. z=-0.09 (baseline caught up after 2 up-weeks) -> new rule: z-score UNDER-flags a regime change after a 2+ week trend; cross-check with the rule-based read (EGLD up while majors flat = EGLD-specific). **RECORD OTC RELOAD into the strength**: UPbit OTC + OTC Distribution desks loaded +237,717 combined (biggest single-week load in tracking, ~98K -> ~335K), fed by UPbit -> OTC Desk 460K, with a record ~323K 7d throughput - a large distribution wave being SET UP into the rally (the key bearish tell) -> new rule: read a CEX outflow by DESTINATION (UPbit's -131K 'outflow' WAS the OTC loading leg, not self-custody). **BINANCE DE-STAKING on two fronts**: custody 2nd-leg -43K (now -202K over 2 weeks from the 3.51M peak) + the binance_staking DELEGATION provider -149K = ~-192K out of staked positions, hot wallets net +115K inflow -> new rule: net out the binance_staking provider before narrating delegation-TVL WoW (its -149K masked +120K broad ex-Binance delegation growth). **DEFI LEVERAGE RETURNING**: USH supply MINTED +6.49% (largest since the run #11 -7% burn; borrowers re-opening CDPs) + XEGLD supply +4.54% (LSD re-accumulating after the -29% collapse) + reward compound rate up a 3rd week to 61.59% -> new rule: USH mint >5% = leverage returning (mirror of the run #11 burn rule). **Net exchange flow -196K (3rd outflow week) but NOT clean accumulation**: just Bybit -221K (untraced) + UPbit -131K (OTC-routed); the rest INFLOW (Binance +115K, Gate.io +26K, Crypto.com +15K). **Mega Whale erd18mv2z6r2 STEPPED BACK** (flat at 1.04M) after 2 accumulation weeks - the identifiable absorber went quiet just as OTC reloaded. **Total staked +80K** (holders staking through the rally); **delegator base FLAT 4th week (174,349)** - no new retail on the rip. **Bilateral inverse rule 2nd UP-week confirmation** (price +15.93%, Hatom Lending EGLD-TVL -11.48%, ratio 0.72; up-week series 0.49, 0.72). **Stablecoins choppy** (USDC -0.66% decelerating 4th wk, USDT -1.87% re-accelerated). **dataApi feed CLEAN 2nd run** (0 retries). 8/8 prior action items completed. |
| 15 | 2026-07-06 | **7-WEEK BINANCE CUSTODY STANDOFF RESOLVED - to the DISTRIBUTION side**: Binance Staking custody drew down -158,853 (3,512,650 -> 3,353,797) back to Binance.com hot wallets after 3 accumulation + 4 stall weeks. TRACEABLE this time via standard txs (custody +241K in, -400K out) -> new rule: tx-scan the custody address; custody<->hot legs are visible standard value txs (unlike hot<->external). The multi-week watch's PRE-COMMITTED reading (delegate=bullish / drawdown-to-hot=bearish) fired bearish - lesson: pre-register the directional interpretation of a structural watch before the move. **EGLD +5.88% to $2.70, FIRST up-week**, $2.55 held, but a broad relief bounce (BTC +5.2%, ETH +12.3%) in which EGLD badly UNDERPERFORMED (ETH 2x+ its gain) - high-beta laggard both directions; z=-1.08 LOW. **Net exchange flow -218K (2nd outflow week) but ~ENTIRELY Binance** (-236K); ex-Binance the complex was net-INFLOW (Crypto.com +27K, Bybit +21K) -> new rule: decompose net flow by entity before labeling it, one entity can invert the aggregate. **XEGLD -29% collapse was a ONE-SHOT**: supply stabilized at ~226,400 (-0.6%), no continuation - resolves last run's top watch (redeemer destination untraceable: LSD moves via SC results, not value txs). **Mega Whale erd18mv2z6r2 is the ABSORBER**: +32.7K routed FROM Coinbase Routing (2nd accumulation week, now 1.04M) - distribution meeting a real identifiable bid, not dumped into a vacuum. **OTC pipeline late-distribution phase**: ~172K throughput (vs 195K) but desks FLIPPED to DRAINING (-8.9K) after last week's +35K load; fresh UPbit->OTC Desk 160K reload landed. **Delegator base FLAT 3rd week (174,373)** - capitulation fully behind us; delegation TVL +70K broad (Synexis +18K) while total staked -46K = direct-node->delegation ROTATION; yield-chase spike UNWOUND (-8.6K, egldstakingprovider -13.7K) as price recovered, pi-staking the exception (+13 users, 3rd growth week). **Stablecoin flight DECELERATED and narrowed**: USDC -2.0% (3rd burn wk) but USDT burn nearly stopped (-0.3% vs -3.7%), USH de-leveraging ended (flat). **Reward compound rate recovered 58.54%->60.35%** (2nd week up). **Bilateral inverse rule got its first UP-week confirmation** (price +5.88%, Hatom Lending EGLD-TVL -2.86%, ratio 0.49). **dataApi feed CLEAN** (0 re-fetch retries, all 4 tokens first pass - last run's SWTAO null was transient). **Newly-issued scan false-positived onto WrappedUSDC** (81K holders) -> added holder-count guard. 9/9 prior action items completed. |
| 13 | 2026-06-22 | **CAPITULATION BOUNCE FAILED - exit-liquidity thesis VALIDATED**: EGLD -4.68% to $2.85, breaking back below the $2.95 floor to a new local low one week after run #12's +1.36% relief rally. EGLD again decoupled to the downside (WoW BTC -2.49%, ETH +1.43%). The run #12 'exit liquidity bounce' (price up on collapsing engagement) correctly predicted the failure - now promoted to a reusable bearish forward indicator. **DELEGATOR CAPITULATION WAS A ONE-SHOT**: -78 WoW (vs -4,003 last week); base stabilized at 174,406, staked-EGLD unstaking decelerated -38K->-9K. Run #9 degenerate-z-score guard applied (z=-2.68σ downgraded to LOW for a -0.04% move). **EXCHANGE NET INFLOW 3rd consecutive week** (+12K): Coinbase 3-week streak (+43K/+8.3K/+6.0K) exceeds the 2-week confirmation rule -> off-exchange-accumulation reversal STRUCTURAL. **BINANCE STAKING CUSTODY 3rd-week stall** at 3.51M (6 weeks parked, 779K). **OTC PIPELINE RELOADED** on schedule (+7K desk balance, 85K throughput; Binance->OTC Router 2 feeding 4,800 chunks) - distribution wave expected 1-3 weeks. **NEW METHODOLOGY - report LSDs in SUPPLY terms not mcap**: supply-based WoW (SEGLD -0.5%, XEGLD +0.6%) shows LSDs flat-to-up while USD mcaps fell; the multi-run 'synchronized LSD contraction' narrative was a price artifact. previous.json now stores lsd_supply. **NEW API QUIRK - dataApi tokens null even at 1.0s** (supersedes run #12 rule): SEGLD/SWTAO/USH/XEGLD returned null at 1.05s; isolated 2.5s re-fetch recovered all. Need a populated-or-retry guard. **Reward compound rate slid 3rd week** 61.9%->59.14%->55.31% (mild bearish drift). **Stablecoin supply contracted** USDC -0.5% USDT -1.8% (burn). USH 2-week de-leveraging ENDED (supply flat). 9 of 10 prior action items completed. |
| 12 | 2026-06-15 | **EXIT LIQUIDITY BOUNCE SIGNATURE** (new bearish pattern): EGLD +1.36% to $2.99 (FIRST up-week after 5 down-weeks, matching run #11's capitulation bounce prediction off the $2.95 floor) but ALL engagement metrics collapsed simultaneously - (1) delegator base -4,003 = largest single-week drop in tracking by 9x; (2) DEX volume -55% = largest WoW drop in tracking; (3) yield-chase cohort fully unwound, net -17K, ninjastaking (sole 5-wk sustained gainer) reversed -10.5K; (4) on-exchange capital build 2nd consecutive week (Coinbase +8.3K confirms 2-week net-inflow per run #11's confirmation rule); (5) reward compound rate 61.9% -> 59.14% (mild). Diagnosis: technical bounce on sell-side execution, not demand-driven recovery. Sellers used the bounce as exit liquidity. **NEW METHODOLOGY**: 'engagement composite' as forward indicator - if next week shows price flat-or-down WHILE engagement metrics keep contracting, regime is decisively bearish; if engagement recovers, the bounce is real. **NEW API QUIRK**: /tokens/{id} HTTP 429 rate-limit triggers at <1.0s spacing AND returns successful HTTP 200 responses with price=null marketCap=null silently. The run #10b 0.5s rule is INCORRECT. New rule: ≥1.0s between /tokens/{id} queries. This silently undercounted Hatom LSD by ~$1.18M in run #11 (SWTAO returned null due to rate-limit) and would have undercounted all 4 LSDs in run #12 if not caught by sanity check. **BILATERAL INVERSE RULE GUARDRAIL**: rule only applies for |Δprice|≥5%. Small moves (<3%) cannot test the rule - EGLD-denominated TVL noise dominates. This run's +1.4% / +0.9% does NOT count as observation #6. **DATA-QUALITY FIX**: run #11 watch_addresses contained an invalid-checksum bech32 address (erd1sdslv...29trp...76xc, HTTP 400). Canonical is erd1sdslv...3rgul...sets. Run #11 Binance.com entity undercounted by ~222K. Recommend pre-store bech32 validation. **REVISED PATTERN**: Run #11's 'synchronized LSD contraction' downgraded - Hatom LSD apples-to-apples (with SWTAO added back to prev) is FLAT, only XOXNO LSD contracting confirmed. **Capitulation prediction VALIDATED on price-up side, INVALIDATED on demand-up side**: the $2.95 bounce came as predicted but on collapsing engagement. The OTC pipeline entered an inter-cycle gap (-0.9K combined) - reload expected next 1-2 weeks per cycle pattern. |
| 17 | 2026-07-20 | **THE RECORD OTC RELOAD WAS DISTRIBUTED - TO EXCHANGES - AND THE RALLY STALLED**: run #16's staged supply was delivered in full. Desks DRAINED -255,736 (335,430 -> 79,694, -76.2%, largest drawdown in tracking) on **1,328,037 EGLD of true 7d throughput**, and for the first time destinations were traced two hops: five zero-balance high-nonce routers forwarding to Bybit and Binance.com, plus 150,000 straight back to UPbit -> new rule: read a distribution wave by DESTINATION two hops out (terminating at venues = distribution onto the order book, not retail absorption). **METHODOLOGY BUG FOUND - throughput undercounted ~4x in EVERY prior run**: the size=50 tx cap covers only ~2.5 of 7 days on a busy desk; re-measuring the run #16 window with pagination gives 1,100,791 vs the ~323K reported at the time. The whole historical throughput series is lower bounds on inconsistent windows and must be backfilled before any trend claim -> new rule: paginate to the after= boundary and net out desk<->desk transfers (315,000 this week). **EGLD LEADERSHIP THESIS FAILED IN ONE WEEK**: +0.96% to $3.16 while BTC +1.95% and ETH +4.36% BOTH outpaced it - run #16's registered 3rd-up-week test resolved to FADE, reclassifying the +15.93% decoupling as a one-week event, not a laggard->leader regime break (run #13 exit-liquidity signature: a rally that stalls the moment distribution lands). **NET EXCHANGE FLOW REVERSED to +193,747 INFLOW** after 3 outflow weeks - the confirming leg; first time since run #13 that the exchange-balance and OTC channels agree instead of substituting. **LARGEST PROPORTIONAL EXCHANGE MOVE IN TRACKING**: KuCoin +430.6% (33,156 -> 175,929) from ONE counterparty - whale erd15ku2r2j6 sent its entire 145,443 EGLD and went to zero (~0.5% of circulating supply). **New rule - an emptied wallet may be a MIGRATION**: Coinbase Custody's 65,090 and whale erd102hmf79en4's 165,006 both went to fresh nonce-0 wallets that still hold them; resolve the receiver's nonce+balance before calling an emptied wallet a sale (Coinbase's real move is ~-10K, not -75,338). **Absorber RESUMED but outgunned**: Mega Whale erd18mv2z6r2 +50,621 via Coinbase Routing - a live bid at ~1/25th the distributed volume. **Binance custody 3rd de-staking leg** -103,579 (-305,549 cumulative from the 3.51M peak; promoted event -> programme), while the binance_staking PROVIDER stabilized (+298) so delegation and total staked agree this week (+47,701 / +81,022, broad: valuestaking +12.7K, Synexis +11.7K, pi-staking +5.7K). **Delegator base FLAT a 5TH week (174,335)** across the entire +24% recovery - zero participation broadening. **DeFi leverage PAUSED**: USH flat +0.14% after +6.49% (borrowers stopped adding the week price stopped rising, no forced-closure burn), XEGLD +2.69% (2nd week), compound rate slipped 61.59% -> 60.19%. **Bilateral inverse rule NOT EVALUABLE** (|dPrice| 0.96% < 5% guardrail) - recorded as an explicit non-test rather than a spurious confirmation. Stablecoin bleed STOPPED (USDC -0.13%, USDT +0.05%) but no inflow. dataApi feed clean 3rd run. 8 new addresses (6 OTC routers + 2 migration destinations). 8/8 prior action items completed. |
| 18 | 2026-07-27 | **EVERY TRACKED SUPPLY CHANNEL SWITCHED OFF AND PRICE FELL ANYWAY - the diagnosis moves to the demand side**: EGLD -10.13% to $2.84 while BTC +1.71% and ETH +5.35% BOTH ROSE - the first time in tracking that EGLD fell double digits against a RISING tape (prior decouplings in runs #11/#13 came against flat-or-falling majors), which confirms and exceeds run #17's registered laggard test and formally reclassifies the +24% recovery as a BEAR-MARKET RALLY. **Three run #17 pre-committed tests resolved, two constructive**: (1) OTC WAVE EXHAUSTED - desks drained to 61,495 through the 80K trigger on 313,173 EGLD of 7d throughput (-76%), and critically UPbit sent NO reload after last week's 364,000; (2) BINANCE CUSTODY REVERSED - the three-leg de-staking programme (-305,549 from the 3.51M peak) broke with a single +150,000 reload to 3,357,101, from a nonce-8 pass-through whose own funder is unresolved; (3) KUCOIN resolved BEARISH - the whale's 145,443 deposit STAYED (-2.6%), so per the pre-commitment it was sold into the book, and a 90-day inbound trace shows the source was a long-dormant holder, not an OTC recipient. **PAGINATION IMPLEMENTED + SERIES BACKFILLED** (run #17's top recommendation): the collector now pages to the after= boundary by default and nets desk<->desk; runs #13-#15 were re-queried with the identical method giving a first-ever comparable series 66,128 / 186,124 / 506,053 / 1,100,791 / 1,284,688 / 313,173, validated by reproducing run #16's independent 1,100,791 exactly - revealing five weeks of escalating distribution that peaked in run #17 and broke. The polluted otc throughput BASELINE (mixed desk deltas with throughput) was replaced outright -> new rule: a baseline whose units change mid-series is worse than none. **HEADLINE EXCHANGE INFLOW +166,978 IS 94% ARTIFACT**: custody reload +150,000 (intra-entity) plus a +6,995 phantom from a Binance wallet with no prior-week balance; TRUE external flow +9,983, flat -> new rule: exclude newly tracked addresses from their first WoW delta (2nd occurrence after run #17's Coinbase Custody 2). **THE ABSORBER WENT TO ZERO**: Mega Whale erd18mv2z6r2 recorded NO value txs (flat 1,093,312) and the Coinbase Routing pipe feeding it drained to 77 EGLD - the one identifiable large bid disappeared in the worst possible week. **DEX VOLUME COLLAPSED -61.1% to $75K** (2nd-largest drop in tracking) on 95.6% WEGLD/USDC while pool TVL and WEGLD supply ROSE -> depth stayed, trading left; a distribution week produces HIGH volume, so this is an absent bid. **DEFI SPLIT**: USH burned -2.60% past the 1% threshold (run #11 de-leveraging rule re-activated; run #17's chase test resolved bearish - the run #16 +6.49% mint was a rally chase) and XEGLD reversed -2.70%, while Hatom Lending posted the STRONGEST bilateral-inverse response ever measured (price -10.13% vs EGLD-TVL +9.89%, ratio 0.98 against a prior down-week series of 0.88/0.80/0.70/0.21) - falsifying run #11's depositor-capacity-decay hypothesis, which was cyclical not terminal. **PARTICIPATION INERTIA PROMOTED TO A STRUCTURAL FINDING** at run #17's pre-registered 6-week threshold: delegators 174,341 (+6), flat across a +24% rally AND its -10% reversal -> new rule: promote a repeated non-observation to a background assumption at a pre-registered threshold and stop re-reporting it. Total staked -126,662 (first real unstaking since run #11) but ~110K left DIRECT-NODE stake, delegation only -16,634 and rotational (pi-staking +11,330/+35 users, a 6th growth week and the most persistent gainer in tracking; Synexis +10,429; against procryptostaking -11,051, ieleman -10,091). **BECH32 PRE-FLIGHT VALIDATION BUILT** (closes a run #12 recommendation open for six runs): scripts/validate_addresses.py found FOUR invalid addresses on its first run, including run #17's KuCoin watch entry which would have silently returned nothing for this week's resolution test; Delegation Manager fixed, two Hatom/OneDex entries flagged not guessed. Stablecoin bleed RESUMED (USDC -1.01%, USDT -2.79%) after exactly one flat week; compound rate slipped a 2nd week 60.19% -> 58.81%; dataApi feed clean 4th run. 8/8 prior action items completed plus the run #12 carry-over. |
| 19 | 2026-08-03 | **THE OTC PIPELINE IS 80% CIRCULAR AND RUN #18's BULLISH CUSTODY SIGNAL IS FALSIFIED - two headline conclusions overturned by measuring one level deeper**: (1) applying the run #17 two-hop destination rule to the INBOUND leg for the first time (never needed before, because UPbit had always been the sole feeder) shows Bybit pushing 132,074 EGLD into the desks through three zero-balance feeders and taking 160,410 back out through five routers, with Gate.io doing the same at smaller scale - so of 301,498 gross throughput, 240,063 (80%) round-trips to the venue that supplied it and genuine one-way movement is just 61,435, with UPbit the only net source (-67,000) -> new rule: report gross (pipeline activity) and net one-way (distribution) as two numbers, and relabel the runs #12-#18 series as gross-only. (2) The +150,000 custody "reload" that run #18 called the strongest bullish structural counter-signal came from a wallet whose complete 30-day history is an unDelegate (Jul 9) and a withdraw (Jul 22) on the binance_staking DELEGATION contract - the run #16 provider unwind (-148,941) completing after unbonding, not accumulation -> new rule: read the function/action field on ZERO-VALUE transactions before declaring an origin untraceable, because delegation-layer EGLD moves via SC results. **UPbit RESUMED FEEDING after exactly one week off** (fresh 67,000 tranche vs 364,000 at the run #17 peak and zero last week; desks +3,558 to 65,053), so run #18's exhaustion call lasted one week - though at ~1/20th of peak in net terms. **ALL THREE DEMAND INSTRUMENTS BUILT** (run #18's top recommendation): DEX turnover ratio 4.06% -> 2.14% of pool TVL traded daily on -2.8% depth (volume $38.6K, a NEW tracked low), identifiable-bid composite at ZERO for a 2nd week (Mega Whale unchanged to the decimal, Coinbase Routing still 77 EGLD), and withdrawal breadth which immediately showed 84% of >1,000 EGLD exchange outflows go into the OTC pipeline rather than self-custody (ex-pipeline: 20 addresses, 56,896 EGLD). **EGLD -5.28% to $2.69 but WITH the tape this time** (BTC -3.22%, ETH -5.56%) - no repeat of run #18's decoupling, so the week is broad risk-off and the chain-specific case now rests on the demand instruments rather than relative price. **pi-staking EXPLAINED** (run #18 question): 9.10% APR at 0% fee on a 63,922 EGLD base - the APR>=8.8% cohort took +37,090 while 20%-fee procryptostaking (-5,998) and 12%-fee syndicatex (-11,935) shed; with participation inert (174,325, -16, 7th flat week) fee arbitrage is the only force moving stake. **DIRECT-NODE UNWIND WEEK 2**: delegation +56,300 while total staked -23,213, implying ~79.5K left direct-node stake. **DEFI HELD**: USH -2.93% (2nd burn week, cumulative -5.45%, orderly rather than forced-closure), both LSDs FLAT for the first time in four drawdown weeks (XOXNO's redeem-on-weakness pattern broke), bilateral inverse 7th confirmation at 0.58 (mid-range - run #18's 0.98 was a spike, not a level), stablecoin outflow essentially stopped (USDC -0.17%, USDT -0.02%), and the reward compound rate made a NEW TRACKED HIGH at 62.25% with zero of 73 retail claims going to an exchange. Run #12 OTC window backfilled (44,335). dataApi feed clean 5th run. 8/8 prior action items completed. |
| 20 | 2026-08-10 | **Retrospective re-netting proven, and circularity found to be roughly CONSTANT.** The run #17 peak window (Jul 13-20), re-queried three weeks later, returned identical gross figures with every router and feeder still resolvable: 1,284,688 gross was 68% circular, leaving **409,680 genuinely one-way**. Combined with run #19's 80% and this run's 69%, circularity is approximately constant across windows -- which means the runs #13-#18 gross series has the **right SHAPE and the wrong UNITS** (a ~3-5x overstatement of distribution volume), rather than being unusable as run #19 feared. Rule: restate magnitudes, keep directions; retrospective re-netting is a standing capability for any window inside API retention (~60 queries). Two-hop both-legs netting is now folded into the collector (`collect_run20.py`), so gross and net one-way are produced together every week. NET one-way is stored as its own baseline array PLUS a keyed `otc_net_one_way_measured_windows` map -- a non-contiguous historical window must never be appended to a weekly array (run #18's units lesson, applied to the time axis). **Bilateral inverse rule must be SUPPRESSED, not computed, when \|price change\| < 5%**: a +1.30% TVL move against a -0.37% price move yields a mechanical 3.50 that is pure small-denominator artifact; the report now states the rule is not evaluable and the confirmation count does not advance. **Pre-committed tests are now the primary output discipline** -- four resolved this run, three fired as predicted, and it is the first run in four with zero corrections of a prior headline. **Raise max_pages for high-frequency addresses and LOG page-cap terminations**: the whale_i 60-day trace silently stopped at the 12-page cap (600 txs, ~25 days of a requested 60), the same failure class as the run #17 pagination miss one layer down. |
| 21 | 2026-08-17 | **THE WEEKLY NETTING FRAME OVERSTATES DISTRIBUTION BY 55%, AND THE THREE-WEEK 'DIRECT-NODE UNWIND' NEVER HAPPENED - a run of four self-corrections.** (1) Wave #2 stopped: UPbit's feed collapsed -96% to 14,000 and the desks returned 130,000 to UPbit, so run #20's pre-committed escalation thresholds (net >300K, tranche >350K) both missed. That return leg exposed the frame bug - netting the wave feed-to-drain (Aug 3-17) gives 210,922 one-way against the 326,924 its two weekly nets sum to, because circularity crosses week boundaries; this week's 38% circularity against a 63-80% band is the diagnostic tell -> new rule: net over the wave, weekly nets are UPPER BOUNDS. UPbit's replenishment source, flagged in run #20 as unobserved, turns out to be the desks and their own feeders - the hub recycles through it. (2) The 'direct-node unwind' (~215K over runs #18-#20) is a measurement artifact: the staked-minus-delegated residual also holds delegation unbonding in flight, and ONE wallet's 229,865 unDelegate pair (149,585 from p2p_org_, 80,279 from a provider that went to zero locked, both zero-value txs with the amount in the data field, both confirmed unbonding via /accounts/{addr}/delegation) explains this week's entire +282,713 flip. Corrected, direct-node stake GREW +52,848 -> new rule + new instrument. The protocol Staking SC returns HTTP 400 on all transaction queries. (3) Run #20's 'first competitive fee cut in twenty runs' is withdrawn: egldstakingprovider went 15% -> 100% and procryptostaking 20% -> 100%, zeroing delegator APR, different owners, 50 nodes each, both still bleeding -> new rule: a fee change is not evidence of competition. A zero-yield signal moved 26% of one book but only 13 of ~1,124 users - the strongest confirmation of participation inertia yet. (4) 'MEX is stale-priced' is falsified: MEX/WEGLD is the #2 deepest pool at $291,459 (15.9% of DEX depth) on 125 trades/24h, and MEX has matched or beaten EGLD four weeks running with no mechanism identified. **Constructive**: EGLD +2.99% vs BTC -0.25% / ETH +1.82%, the first EGLD-specific up-week since run #16, achieved with the identifiable bid at literally ZERO (absorber and Coinbase Routing both recorded no transactions - run #20's reactivation was the maintenance transfer its sub-10K branch predicted) - direct evidence the marginal SELLER sets this price. DEX turnover rose a 2nd week (2.24% -> 2.93%) and ex-pipeline withdrawal breadth hit its highest reading (24 addresses / 111,683 EGLD, pipeline share 47% vs 84% in run #19). **Bearish counterweight**: bridged USDT -15.42% (100,287 tokens), 4x the prior worst weekly contraction, 9th run with no stablecoin inflow. Binance re-parked 118,440 hot -> staking custody in one traceable transfer (3,475,540, not delegated). Net one-way series BACKFILLED to five anchors (run #16 309,197 at 72% circular; run #18 114,877 at 63%). 'Unknown Whale I' cleared the 60% test (62.5% two-way with hub infrastructure) and is reclassified as OTC operator inventory, so its hub take is no longer counted as demand. XEGLD redemption traced through its callers - zero exchange destinations. Delegators 174,353 (+23, 9th flat week); zero qualifying new tokens for a 5th week (the one issuance was a 'Bitcoin' ticker impersonation). dataApi feed clean 7th run; page-cap logging shipped and reported nothing. 8/8 prior action items completed. |
