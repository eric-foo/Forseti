# Reddit Listing-Efficiency 100-Thread Holdout v0

```yaml
retrieval_header_version: 1
artifact_role: Research validation artifact
scope: Blind listing-only application and post-freeze deep audit of the owner-calibrated Reddit deep-read selection policy.
use_when:
  - Evaluating or revising docs/research/reddit_listing_efficiency_owner_calibration_v0.md.
  - Distinguishing tested listing-selection failures from accepted commission-specific misses.
  - Designing a later runtime or model evaluation without treating this stress test as corpus prevalence.
authority_boundary: retrieval_only
```

## Result

The 100-thread stress test found one material rule error and four smaller
selection kinks.

1. **Captured post score `0` is not a safe universal cutoff.** Seven of 20
   deliberately sampled zero-score threads contained enough commercially
   relevant discussion to justify a general deep read. One had a 56-point top
   comment despite a zero post score.
2. **The `0–3` comment floor is efficient but not exception-free.** One of 20
   deliberately sampled low-comment threads was a zero-comment post whose body
   contained five completed-use product reviews. The floor remains useful for
   the general queue because it suppresses threads without independent
   discussion; this content-dense poster-only case is now an explicit accepted
   residual unless its value is visible in the listing projection or recovered
   for a direct commission.
3. **Opaque or image-dependent titles need a context-sufficiency state.** One
   false negative hid a Dior purchase decision behind “get this,” while one
   false positive turned out to be a visual joke rather than a Clio product
   failure.
4. **Two archetype boundaries were too coarse.** Direct discontinued-product
   replacement requests can be valuable at modest engagement, and consumer
   device experience should not be suppressed merely because a condition is
   medically adjacent.
5. **Captured engagement can drift enough to change ranking.** At least one
   audited thread showed 7 listing comments but 66 comments in its captured
   content record. Ranking should use the freshest available captured metadata.

The core policy survived the stress test. Among the 20 listings assigned a
confident pre-dive `yes`, 18 yielded decision-bearing evidence and two did not.
This is an observed result inside a deliberately stratified test, **not** a
corpus-wide precision estimate.

## Method

The holdout was selected deterministically from the captured Reddit corpus
using seed `listing_efficiency_holdout_v1_20260728`.

The 100 threads were deliberately stratified to stress the policy:

| Stratum | Threads | Purpose |
| --- | ---: | --- |
| Captured post score `0`, comments at least `4` | 20 | Test the score-zero hard floor |
| Positive score, comments `0–3` | 20 | Test the low-comment hard floor |
| Positive score, comments at least `4` | 60 | Test the remaining gates and archetypes |

Selection used retained, currently selected, exact-deduplicated threads with an
available content record. It excluded 142 threads used in the prior 30-pair
owner calibration, source audits, and pairwise pilot work. The available pools
before deterministic sampling contained 80 score-zero, 670 low-comment, and
3,554 above-floor threads.

For every holdout thread:

1. admission (`yes`, `borderline`, or `no`) and priority were frozen using only
   title, subreddit, flair, captured score, captured comment count, the general
   commissioned-decision frame, and the existing calibration;
2. hidden post bodies and comments were not used before label freeze;
3. the captured post and comments were then deep-audited;
4. hidden usefulness counted as a selection error only when its expected
   general commissioned-decision value justified the dive from an improved
   listing rule. Narrow future-commission evidence remained an accepted miss.

## Inputs and reproducibility

| Input | SHA-256 |
| --- | --- |
| Canonical 5,470-thread manifest | `289ee06d3e4f8feb96540feafe375ae7333c2f3030d884fd28c801583d44027f` |
| Completed owner calibration labels and audits | `338913dec6c63a407bdbb7797d1a611840f8bf084dd2d127fad841e44bcb0c88` |
| Frozen labels plus completed adjudication | `b05495a60a9d30f1a3b8df37fe7290d3be0114429e3f59d0fdd17eb04c5891bc` |
| Deep-audit capsules | `92c77824c84db51e8de6ee9afa46d72f8483ee645d874057b13c7123865d27f0` |

The frozen-label artifact records the applied calibration commit
`02bd195c3181b8f372d656fc5b07d02992467cf7` and blob
`a98e9fadfd177b4b4937c6c16a089fbf4a38891b`.

The evidence is captured-corpus evidence only. No live Reddit completeness,
currentness, or monitoring claim is made.

## Observed outcomes

| Audit outcome | Count | Interpretation |
| --- | ---: | --- |
| Correct admit | 18 | Confident `yes` produced useful evidence |
| False positive | 2 | Confident `yes` did not justify the dive |
| Borderline promote | 4 | Uncertainty resolved to `yes` |
| Borderline hold | 4 | Conditionality remained material |
| Borderline suppress | 1 | Uncertainty resolved to `no` |
| Correct suppress | 32 | General suppression was correct |
| Accepted conditional miss | 27 | Useful only for a narrower commission; retrieval should preserve it |
| False negative: score floor | 7 | Score-zero veto caused the miss |
| False negative: comment floor | 1 | Poster body was rich despite no discussion |
| False negative: rule | 3 | Archetype or objective rule caused the miss |
| False negative: listing projection | 1 | The commercial object was hidden from the projected listing |

The outcome mix is intentionally enriched for cutoff failures. It cannot be
used to estimate how often these outcomes occur in the full corpus.

### Results by stratum

| Stratum | Decisive result |
| --- | --- |
| Score zero | 7 rule-breaking false negatives, 5 accepted conditional misses, 8 correct suppressions |
| Comments zero to three | 1 poster-only false negative, 9 accepted conditional misses, 10 correct suppressions |
| Above floor | 18 correct admits, 2 false positives, 4 rule/projection false negatives, 9 borderline resolutions, 27 other correct or intentionally conditional outcomes |

## Decisive failures

### Score-zero floor

| ID | Listing | Captured engagement | Deep-read evidence |
| --- | --- | ---: | --- |
| `H002` | Korean Skincare vs Tretinoin and Dapsone? | 0 / 25 | 23 independent comments separated K-beauty support from tretinoin efficacy; top comment scored 56 |
| `H003` | Beauty Writer/Expert | 0 / 23 | Paid beauty-box placement, excess-inventory dumping, white-label inflation, and distrust |
| `H005` | How to grow insane eyelashes | 0 / 22 | Named serums, prescription alternative, time to result, side effects, and independent experiences |
| `H006` | Will Ptiox mess up my facial expressions? | 0 / 12 | Product-claim skepticism, repeat purchase, alternatives, and mechanism correction |
| `H014` | Colleague looks 10 years younger | 0 / 16 | Likely stealth-marketing pattern and comparison with tretinoin, sunscreen, Botox, and genetics |
| `H015` | Matte top coats without dulling glitter | 0 / 10 | Two named products and a concrete finish/application tradeoff |
| `H016` | Can glycolic acid help reduce dark underarms? | 0 / 8 | Repeated outcomes, cadence, alternatives, named products, and dissent |

The owner hypothesis that a zero-score post would almost never contain a
high-scoring comment was directly falsified by `H002`. Post score remains a
resonance signal, but it cannot veto a commercially promising discussion.

### Low-comment floor

`H024`, “Skincare pans” (score 56, zero comments), contained five completed-use
reviews, repeat use, a favourite, and an explicit non-repurchase in the post
body. It proves that comment count is not a truth boundary. It does **not** by
itself justify sending every zero-comment thread to deep read: there was no
independent corroboration, and the useful material was hidden from the tested
listing projection.

The smallest correction is therefore to keep `0–3` comments as the general
dive-budget floor while naming this as an accepted residual. A later selector
may recover such cases only when cheap listing-visible context already exposes
a structured completed-use review, or when a direct product/category
commission retrieves the thread.

### Rule misses above the floor

| ID | Listing | Failure and correction |
| --- | --- | --- |
| `H062` | Extremely dry and frizzy hair | A broad title still produced direct Nizoral failure and K18/Dove/Elizavecca/Olaplex/Redken choice evidence. Specific current products in the visible problem should outweigh generic “advice” phrasing. |
| `H070` | Replacement for CocoaPink’s Climbing Star Jasmine | Direct discontinued-product replacement, alternatives, samples, and a brand roadmap signal were suppressed at 8 / 6. Replacement and discontinuation are high-value decision promises even at modest engagement above the comment floor. |
| `H078` | Red light therapy—who has tried it? | Named consumer devices, duration, positive and negative outcomes, and condition-specific tradeoffs were mistaken for generic clinical advice. Medical adjacency raises safety and corroboration burden; it does not erase purchasable-device evidence. |

### Listing-projection failures

- `H082` hid a named Dior purchase decision, non-repurchase, luxury
  alternatives, routine, and willingness-to-pay logic behind the title
  “Debating on whether or not to get this.”
- `H084` asked “Which one is better after the age of 30?” but the compared
  products were absent from the projected listing.
- `H095` looked like a highly engaged Clio failure but was a visual punchline
  about mistaking lash-curler packaging for mascara; comments were jokes.
- Other audited threads hid exact product stacks in their body or image, or
  contained a crosspost payload mismatch.

The selector needs an explicit `insufficient_listing_context` path for deictic
or media-dependent listings. It should consume media presence/count and cheap
linked product context when available. It should not invent a product failure
or confidently suppress a purchase decision when the visible subject is
missing.

### False positives

| ID | Why the dive failed |
| --- | --- |
| `H046` | A fragrance-gift regret question mostly elicited rejection of the premise, with little transferable alternative or purchase evidence. |
| `H095` | Strong failure language and engagement described a visual joke, not a product-performance failure. |

A first-person regret hook needs a visible consequence, substitution request,
or decision object. Strong language plus engagement cannot compensate for
missing media context.

## Borderline calibration

Four borderline listings should have been promoted:

- `H043`: structured oud portfolio and real-versus-synthetic positioning;
- `H057`: completed-use marks, repurchase, overhype, substitution, consumption
  cadence, and spend limits;
- `H061`: full lip stack, undertone gap, use context, and purchase response;
- `H080`: direct Innisfree/Tatcha price substitution, sampling, finish, eye
  sting, layering, and category comparison.

Four remained correctly conditional because of teen-treatment safety, a
crosspost mismatch and narrow vibe commission, missing compared products, or a
grooming-specific commission. One high-engagement progress thread (`H045`)
resolved to suppression because it contained appearance praise and lifestyle
advice rather than product evidence.

This supports a narrow promotion rule: structured completed-use sets, explicit
product combinations, and named comparisons with real discussion should not
remain borderline merely because they use recurring community formats.

## What held

- WTS, resale, and transaction administration remained suppressible.
- Appearance validation and generic showcase engagement remained poor evidence
  of product value.
- DIY formulation remained commission-conditional.
- Fragrance-vibe, retailer/service, and rare visual-product threads sometimes
  contained rich evidence, but remained accepted misses under the current
  scaling-challenger general commission. They should be retrievable, not added
  to the general queue.
- Comment quality still requires independent-voice inspection after diving;
  author replies, bots, and nested repetition are not corroboration.
- Reddit remains a lead source. None of these threads alone becomes a client
  conclusion without entity cross-stitching and corroboration from every
  material source that could change the decision.

## Calibration changes authorized by this evidence

1. Remove captured score `0` from the universal engagement floor.
2. Keep captured comments `0–3` as the general floor, with the poster-only
   completed-use case named as an accepted residual rather than hidden.
3. Use the freshest available captured engagement before ranking.
4. Add `insufficient_listing_context` for opaque or media-dependent listings;
   expose media presence/count and cheap linked-product context when available.
5. Raise direct discontinued-product replacement requests above generic
   low-engagement advice.
6. Separate consumer product/device experience from crowd diagnosis and
   clinical-treatment advice.
7. Promote structured completed-use sets, explicit product stacks, and named
   comparisons when discussion clears the floor and commission fit is present.

These are retrieval-rule corrections only. This holdout does not authorize a
runtime implementation, a learned numeric scorer, live Reddit collection, or a
production-quality claim.
