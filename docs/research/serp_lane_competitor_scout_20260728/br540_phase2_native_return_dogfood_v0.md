# Baccarat Rouge 540 phase-2 native-return dogfood v0

Durable record of the bounded BR540 native-return dogfood completed on
2026-07-30. This runs the six-step phase-2 shape end to end for one
Stage-6 subject: native capture, Channel 3, J3, J5 delta, targeted
return, and consolidation.

This is a **smallest-complete dogfood**, not the full 130-subject
phase-2 run. It binds one Stage-6 result (`mq0234`) and five exact
trigger threads. It proves that the existing Reddit and persistent
Google routes can close the loop without inventing a new lane or
running broad Reddit discovery.

Standing non-claims: counts are observed cards/comments, never
prevalence, volume, or share; US-parameterized Google is not
physically US-local; raw capture data stays outside Git; a mechanical
finding-grade rung does not erase weak author support.

## Authority, raw evidence, and currentness

This file is the canonical durable finding. The raw packets and
derived staging artifacts remain at:

`C:\tmp\forseti-br540-phase2-native-return-20260730-runtime\`

The staging root contains:

- `phase1_bridge\`: the `mq0234` extraction, bounded trigger queue,
  initial nine-name bridge ledger, subject baseline job, and query
  policy preflight;
- `reddit_capture\`: five finalized old-Reddit packets plus the batch
  summary;
- `reddit_consolidated\` and `agent_views\`: generic native
  projections for all five packets;
- `google_baseline\`, `google_phase2\`, and `google_phase2_tail\`:
  the persistent-tab Google packets and queue records;
- `google_extracted\`: 19 immutable-extractor outputs, 494 typed rows;
- `analysis\`: the native settlement, 39-entry consolidated ledger,
  J5 delta, and return-probe settlement.

The temporary `stale_preseal\` folder contains an unused copy of the
first derived Reddit projections. It was archived after a diagnostic
mistook raw Windows byte hashes for the consolidator's normalized-text
hash. The regenerated projections were verified 5/5 against the
consolidator's actual hash basis; neither copy changes the source
packets.

## Capture accounting

- Reddit: **5/5** exact trigger threads, **513** parsed comments,
  zero access diagnostics, zero extraction failures.
- Google: **19/19** packets — one subject J5 baseline, nine promoted
  competitor J5 reads, and nine evidence-derived head-to-head returns.
- Google route: one persistent, logged-out, operator-visible Chrome
  tab; exact product-scoped queries; 40-second starts (the canonical
  60/hr sustained shape); no new tab per search.
- Blocks: **0**. No challenge interaction or fallback click occurred.
- Total source packets in this dogfood: **24**.

The initial Reddit tool call timed out while its child process
continued correctly. A duplicate resume process was detected after
one duplicate `br540_r02` packet and stopped. The authoritative
five-packet batch is `reddit_capture\batch_summary.json`; the duplicate
packet remains outside Git and was excluded from every count and
finding.

## What the five trigger threads were

| slot | subreddit / thread | parsed comments |
|---|---|---:|
| `br540_r01` | r/Colognes `1nwmudi`, close-dupe request | 170 |
| `br540_r02` | r/fragrance `1c86515`, comparative review | 20 |
| `br540_r03` | r/fragranceclones `175ixsn`, best-clone request | 180 |
| `br540_r04` | r/Perfumes `1mxtekf`, all dupes ranked | 114 |
| `br540_r05` | r/fragranceclones `1izy34h`, best-dupe request | 29 |

No broad Reddit search ran. These are the five exact old-Reddit URLs
rendered by the single `mq0234` Google surface and accepted into the
bounded bridge.

## J3 — rendered snippet versus native verdict

J3 is per rendered surface. It compares Google's snippet stance with
the top-voted native stance from the subject's perspective.

| slot | rendered stance | native stance | tag |
|---|---|---|---|
| `r01` | Dossier is better than the original; Cloud is the top answer | 24-point top named answer is Cloud; Dossier is strongly supported with longevity dissent | ALIGNED |
| `r02` | Sweven is very similar but synthetic/chemical | exact five-point comment; its continuation prefers Fine'ry | ALIGNED |
| `r03` | OP confusion among Ruby, Rouge, and Untold | 41-point answer supplies a value/performance/quality split | RENDERED_BETTER |
| `r04` | one-point Airplane Mode comment is rendered as best and budget-friendly | 78-point post names Dossier the 98/100 winner; 41-point reply agrees | ALIGNED, competitor-identity drift |
| `r05` | Untold and Pendora are decent; Instant Crush is the high-end alternative | 16-point top comment says Untold worked; rendered three-point comment is present verbatim | ALIGNED |

**Headline: 4 ALIGNED / 1 RENDERED_BETTER / 0 NATIVE_BETTER
(n=5).**

The important correction is `r04`: Google did not hallucinate Airplane
Mode, but it elevated a one-point native comment over the post's
78-point Dossier winner. J3's polarity remains aligned (both are
anti-subject), while competitor identity drifts.

## Ledger delta and promotions

The bounded consolidated ledger holds **39 entries**:

- **9 finding-grade promotions**: Dossier Ambery Saffron, Ariana
  Grande Cloud, Oakcha Sweven, Memoire Archives Airplane Mode,
  Montagne Le Bonbon, Armaf Club de Nuit Untold, Paris Corner Pendora
  Rouge, Mancera Instant Crush, and Zara Red Temptation.
- **30 Channel-3 presence entries**: exact named alternatives from the
  post or decision-bearing comments that have complaint-body evidence
  but no second independent surface class in this bounded pass.

All nine promotions satisfy the mechanical rule:
`serp_rendered_snippet + complaint_body`. Author strength remains a
separate confidence line:

| promotion | native support in the five-thread slice | decisive qualification |
|---|---|---|
| Dossier Ambery Saffron | 26 known authors / 5 threads | `r04` post: 98/100 winner; 2–3 hours on skin |
| Ariana Grande Cloud | 19 / 4 | high recognition, but repeated “similar DNA, not the same” dissent |
| Oakcha Sweven | 11 / 3 | very similar; chemical/powdery and Extrait-variant complaints |
| Airplane Mode | 1 / 1 | spot-on and budget-friendly; lacks longevity — mechanically promoted but thin |
| Montagne Le Bonbon | 16 / 5 | strong support; Le Bonbon and Le Bonbon Intense must stay separate |
| Club de Nuit Untold | 56 / 5 | broadest support; harsh opening, batch, airiness, and variant dissent |
| Pendora Rouge | 1 / 1 | “decent” at three points — mechanically promoted but thin |
| Mancera Instant Crush | 18 / 4 | mistaken for BR540, but repeatedly not a 1:1 |
| Zara Red Temptation | 7 / 4 | accessible DNA; harsh saffron/amber and drydown complaints |

The 30 presence entries include Al Haramain Amber Oud Ruby/Rouge,
Maison Alhambra Baroque Rouge, Lattafa Ana Abiyedh Rouge, Fine'ry The
New Rouge, Orientica Amber Rouge, Fragrance World Barakkat Rouge,
Game of Spades Rouge, In the Stars, Seeing Rouge, The Woods
Collection Flame, Dubai Mirza, Pure Addiction, Manege Rouge, ALT
Crystal No. 23, Miim.Miic 99, Spirito Fiorentino, Alphaora, and other
exactly cited low-rung names. None was upgraded merely for recurring
inside Reddit: multiple threads are still one surface class.

The curation boundary is explicit. All nine phase-1 bridge names were
settled. The Channel-3 delta captures exact names in the post and
decision-bearing comments; it does not claim exhaustive perfume-name
NER over every zero-score reply in 513 comments.

## J5 price architecture

The subject's rendered baseline is **$360 / 70ml = $5.14/ml**.

| promoted name | list | standing floor | floor/ml | subject multiple |
|---|---:|---:|---:|---:|
| Dossier Ambery Saffron 50ml | $49.00 | $49.00 | $0.98 | 5.25x |
| Ariana Grande Cloud 100ml | $75.00 | $54.99 | $0.55 | 9.35x |
| Oakcha Sweven 50ml | $45.00 | $45.00 | $0.90 | 5.71x |
| Montagne Le Bonbon 50ml | $40.00 | $40.00 | $0.80 | 6.43x |
| Club de Nuit Untold 105ml | $50.00 | $37.25 | $0.35 | 14.69x |
| Pendora Rouge 100ml | $39.99 | $19.99 | $0.20 | 25.70x |
| Mancera Instant Crush 120ml | $200.00 | $72.00 typical | $0.60 | 8.57x |
| Zara Red Temptation 80ml | $39.90 | $39.90 | $0.50 | 10.28x |
| Airplane Mode 100ml | $60.00 | $35.93 | $0.36 | 14.28x |

Sponsored, unmatched-size, sold-out, promotional, and unidentified
long-tail prices were excluded from floors. No Shopping second page
was needed: every base SERP exposed a brand, typical-price, or
multi-offer layer.

This is value architecture, not a recommendation that the subject
compete on price. The response trap is structural: BR540 cannot match
these tickets without collapsing its prestige ladder. Its remaining
defense must be a better full-wear experience, not a cheaper bottle.

## Targeted return — what changed

All nine evidence-derived head-to-head queries ran. The queried name's
own echo never created a new rung.

1. **Dossier:** leading Reddit result says it has the DNA but is not
   close; Dossier says the scent is shared but the original has more
   depth, longevity, and projection. Third names: Al Haramain Amber
   Oud Rouge and Fine'ry The New Rouge.
2. **Cloud:** explicitly contrarian. Leading Reddit result says Cloud
   is heavier and not close; the forum block says “similar vibes,”
   not exact.
3. **Sweven:** Oakcha itself labels it Extrait. The surface introduces
   Dossier and ALT, both already in the bounded ledger.
4. **Le Bonbon:** exact EDP product is present, but Google mixes in Le
   Bonbon Intense/Extrait and an Aventus-heavy blend thread.
5. **Untold:** leading native result calls it a 98% EDP clone but less
   airy; a dedicated negative thread is also visible.
6. **Pendora Rouge:** thin direct evidence — cheap good clone, weak
   performance; mostly product/creator echo.
7. **Instant Crush:** adjacent rather than 1:1 — muskier, while BR540
   is cleaner and softer; creator verdicts conflict.
8. **Red Temptation:** opening similarity, weaker wear and a
   cherry-Vicks drydown; rendered video summary says roughly six-hour
   longevity.
9. **Airplane Mode:** partial. No direct head-to-head verdict rendered;
   the surface is product echo plus a performance complaint. Its
   one-author promotion remains thin.

No closure expansion ran. Every substitute third name was already in
the bounded native ledger. Aventus appeared only as a blend reference,
not as a BR540 substitute.

## The bounded competitor answer

The native return materially changes the flat “BR540 dupes” SERP:

- **Dossier is the clearest native similarity winner**, but longevity
  is its exposed weakness.
- **Untold owns the widest community consideration set**, but its
  value claim is fragile to batch performance, harshness, airiness,
  and EDP-versus-Extrait confusion.
- **Le Bonbon is the strongest variant-sensitive specialist**. EDP
  and Intense/Extrait evidence must never be merged.
- **Cloud is a DNA alternative, not a stable exact-dupe conclusion.**
- **Sweven, Red Temptation, and Pendora expose the same trade:** a low
  entry price versus chemical opening, drydown, or performance risk.
- **Instant Crush is a higher-end adjacent scent**, not a clean 1:1.
- **Airplane Mode passes the mechanical ladder but not a strong-author
  bar.**

The subject's best observed defense is **fidelity through the full
wear**: airiness, development, blend quality, and consistent
projection. That defense is real but not uncontested; several native
owners consider Dossier, Le Bonbon, Ruby/Rouge, or Untold close enough
that the $360 ticket no longer carries the comparison by itself.

## Unmet-value map

1. **Full-wear fidelity / airiness / complexity.** Strongest subject
   defense. `r02` says many dupes become linear sweet or mossy rather
   than reproducing BR540's development. Counterweight: Dossier is
   rated 98–99% by multiple native owners.
2. **Longevity and batch consistency.** Dossier, Airplane Mode, and
   some Untold bottles lose here. Counterweight: other Untold owners
   report nose blindness and unsolicited BR540 comparisons.
3. **Harsh synthetic opening.** Sweven, Red Temptation, and Maison
   Alhambra draw alcohol/saffron/chemical complaints. Counterweight:
   the nine-point Maison Alhambra owner says the drydown becomes
   nearly indistinguishable.
4. **Variant identity.** Ruby/Rouge, Le Bonbon/Intense, and
   EDP/Extrait are repeatedly conflated. Any later report that drops
   variant identity will overstate agreement.

## Residuals and next source

- This closes the six-step loop for one bounded subject only. It does
  not authorize extrapolation to the 130-subject bank.
- Airplane Mode and Pendora Rouge are mechanically finding-grade but
  remain one-author native cases.
- The Channel-3 delta is decision-bearing curation, not exhaustive
  entity extraction over every zero-score comment.
- The persistent Chrome identity still relies on the existing marked
  tab plus unique-Google-tab recovery; this dogfood observed no tab
  churn, but it is not a real-Chrome identity durability proof.
- Next source if this result is expanded: the full-bank phase-2
  commission, with product variants bound before queue generation.
  Do not recapture these five threads merely to enlarge counts.
