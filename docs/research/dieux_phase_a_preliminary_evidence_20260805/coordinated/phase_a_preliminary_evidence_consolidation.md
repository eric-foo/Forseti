# Dieux Phase A preliminary evidence consolidation

Status: **preliminary, unsealed, and not Deliver input**

Subject: Dieux Skin

Current through: 2026-08-05

Owning evidence: the three coordinated JSON artifacts beside this report

Next source of truth: a validated Phase A acquisition seal after final semantic adjudication and material-exhaustion review

## Decision

The completed dogfood supports a real preliminary competitive-intelligence map,
but it did **not** complete Dieux Phase A. The retained evidence is already useful
for deciding which hypotheses deserve corroboration: reaction and clogging risk,
skin-type-specific moisturizer fit, makeup and occlusion limitations, price-led
switching, and the brand's strong hydration and texture defense. It cannot yet
support a sealed conclusion because only 95 Reddit packets contain source-native
thread bodies, Soko Glam is the only complete retailer-review corpus, the Sephora
capture contains no review bodies, and no final semantic or material-exhaustion
adjudication has occurred.

The controller's terminal claim also required correction. It banked 122 Reddit
captures as successful; fresh source-native parsing found 95 body-bearing threads
and 27 Reddit login-wall redirects. Two additional packets are explicit blocks.
No packet receives `captured_used` credit from this consolidation.

## Evidence inventory and integrity

| Evidence unit | Observed coverage | Research posture |
|---|---:|---|
| Admitted unique Reddit threads | 124 | 95 body-bearing; 27 login-wall false successes; 2 explicit blocks |
| Parsed Reddit content | 95 threads; 5,436 comments; 274 conservative coded rows | Candidate nomination only; engagement, source date, capture time, and packet locator retained per thread/row |
| Soko Glam retailer corpus | 6 products; 77/77 review bodies; 58 verified buyers | Complete captured corpus for this retailer snapshot; one retailer is not cross-retailer independence |
| Soko ratings | 60 five-star, 9 four-star, 2 three-star, 2 two-star, 4 one-star | Descriptive only; not market prevalence |
| Bounded cross-source captures | 5 editorial pages and 1 Sephora product page | Use-test and condition-specific corroboration; Sephora is positioning/discovery only because no review bodies were captured |
| Official/retailer discovery in the first dogfood | 7 official pages and 3 retailer pages | Search-vocabulary input, not a complete official or retailer corpus |

Pinned inputs:

- authenticated completion receipt: `0c229d3e0392c87b49ae0799529e239aa10e5ac01c1f66571b248007ed1bb22a`
- Soko Glam raw corpus: `40618a42445188bf9c87aef02dfd9351be49a22e22f6231a8b64e76f294d2922`
- community coding: `8d4cdf212fa59933a6f8b1c74e93785b4e59434371ea1a5a9a1793055d625471`
- retailer coding: `03e3a4370b459ea54c2eb55445a98c5310960cb234a9a90fa277ddce0839564f`
- cross-source ledger: `9698c472b2a25591f452273972ac1ad4827f6af876360a0c8736942674c8f10d`

The raw Reddit and cross-source packets remain under their frozen temporary
run roots. The coordinated JSON files retain their exact packet/file locators,
source URLs, dates, capture times, engagement observations, and input hashes so
a later analyst can re-open the primary evidence instead of trusting this prose.

## Acquisition timing and wait accounting

The completed controller run did **not** take a fixed 20-minute rest after every
21 Google searches. Twenty-one was an adjudication checkpoint, not a pacing
boundary.

| Route | Work observed | Worker-active time | Deliberate pacing configuration |
|---|---:|---:|---|
| Google | 40/40 jobs; 41 attempts | 608.910 seconds (10m08.9s) | rung 8, nominal 40-second cycle, jitter ±0.5; one 10-minute rest after 30 in the pinned route |
| Reddit | 124 admitted attempts | 2,752.517 seconds (45m52.5s) | 44–61 seconds after each attempt; one 20-minute challenge cooldown |
| Whole CO3 window | start to terminal | 11,040.210 seconds (3h04m00.2s) | hosts were intended to pipeline, but measured cross-host active overlap was only 176.339 seconds (2m56.3s) |

The residual wall time was therefore dominated by Reddit pacing, the one
challenge cooldown, and operational gaps: route setup, block reconciliation,
decision import, retry settlement, and the owner-authorized continuation. Removing
Summer Fridays' earlier fixed 20-minute batch rests is a genuine saving. It is
not evidence that 31–46 seconds is already safe: the clean observed run supports
44–61 seconds. A 31–46-second band is a bounded next dogfood hypothesis and must
retain the same challenge circuit and truthful-content check.

## Coding method and ceiling

The two coding files are deterministic nominations, not an LLM's final reading.
Reddit titles/posts and subject-anchored comments were mapped to the 12 axes with
explicit patterns; choice and behavior labels require explicit language. Soko
titles and review bodies were mapped with the same axis vocabulary, while rating,
recommendation, verification, relative review date, observation time, and helpful
counts remain separate fields. A row can map to multiple axes, so the counts below
are coverage indicators rather than independent observations.

This evidence can establish existence, conditions, behavior, named destinations,
and contradiction. It cannot establish prevalence, market share, causal product
effects, medical safety, or final axis strength.

## Axis-by-axis preliminary decision usefulness

| Axis | Reddit candidate coverage | Soko review coverage | Decision-relevant signal and current limitation |
|---|---:|---:|---|
| Hydration and barrier performance | 79 threads / 23 communities | 40 reviews | Strongly defended benefit, but rich-moisturizer needs split by climate and skin type. Marie Claire's 2026-01-06 use test leaves an occlusive gap on severe spots. Final independence not adjudicated. |
| Reaction, irritation, and breakout | 56 / 15 | 17 | Material hypothesis: Instant Angel clogging/reaction and Deliverance burning can cause stop-use. Soko includes verified 1–2-star reactions (`instant_angel:3`, `:5`, `:21`, `:30`; `deliverance:2`), while Reddit contains both congestion reports and safe-use counterevidence. No prevalence claim. |
| Texture, weight, and finish | 64 / 18 | 29 | Portfolio strength and segmentation: Instant Angel is richer; Air Angel is lighter for oily/acne-prone users; Skin Mercy sits between. Richness can become heaviness or insufficient winter occlusion depending on segment. |
| Routine and makeup compatibility | 73 / 22 | 18 | Air Angel and Instant Angel receive positive layering evidence, but Marie Claire reports Skin Mercy can make concealer slip without primer. Product-specific, not a brand-wide defect. |
| Packaging and dispensing | 28 / 12 | 9 | A real but secondary friction: one verified Soko review calls Instant Angel's moisturizer excellent and packaging worst-in-rotation (`instant_angel:17`); another negative review still values aluminum packaging (`:30`). Needs more independent behavior-linked evidence before escalation. |
| Price, value, hype, and trust | 58 / 19 | 9 | New York Magazine's 2025-11-05 use account gives a concrete displacement: COSRX Ceramide prevented an intended Instant Angel repurchase on adequate performance and much lower price, while conceding Dieux's more luxurious feel. This is a material value opening, not switching prevalence. |
| Segment and condition fit | 69 / 18 | 21 | The most decision-useful structure is conditional fit: Air Angel for oilier/acne-prone dehydration, Instant Angel for richer lipid needs, Skin Mercy for sensitive/eczema-prone comfort, Deliverance for some redness/rosacea users who tolerate niacinamide. Contradictory reactions remain visible. |
| Post-procedure and active compatibility | 42 / 13 | 4 | Reddit contains tretinoin/retinoid co-use and concern about stacked niacinamide or actives. The Cut's 2026-02-16 guide narrows Deliverance's rosacea fit to niacinamide-tolerant users. Medical or causal claims are out of scope. |
| Efficacy and visible results | 70 / 18 | 37 | Hydration, softness, glow, and redness relief are recurrent defenses. Deliverance is polarized between meaningful redness benefit and no perceived effect or irritation. Duration and conditions require semantic review. |
| Product selection and portfolio fit | 94 / 25 | 77 | The portfolio is not interchangeable: the evidence supports use-case routing, not one universal hero. This axis has broad candidate coverage partly because every retailer review is necessarily product-specific. |
| Repeat purchase, switching, and destinations | 61 / 23 | 16 | Behavior is present: stop-use, give-away, non-repurchase, repeated purchase, and alternatives such as COSRX, Vanicream, Farmacy, Embryolisse, Skinfix, and CeraVe. Automated alternative extraction is a candidate list; final review must distinguish a true destination from a product merely mentioned in context. |
| Strongest delight counterevidence | 80 / 23 | 57 | The brand has substantial defense: repeated praise for hydration, cosmetic elegance, redness support, and product-specific repurchase. This prevents a pain-only attack narrative. Positive retailer skew and editorial-selection bias remain material limitations. |

## Material preliminary competitive-intelligence findings

1. **The strongest opening is segment mismatch, not generic efficacy.** Richness,
   oil load, active tolerance, climate, and makeup routine determine whether the
   same product is loved, insufficient, or reaction-producing. A challenger can
   compete on clearer routing and a more forgiving fit rather than claiming that
   Dieux does not hydrate.

2. **Reaction evidence has behavior attached.** Verified Soko reviews record
   burning, redness, bumps, rash, stop-use, give-away, and wash-off. Reddit adds
   candid congestion and stacked-active contexts. The simultaneous high praise
   means the defensible claim is conditional risk, not universal harm.

3. **Price has a named, decision-relevant destination.** The COSRX replacement
   account shows that "adequate, compatible, much cheaper" can beat a more
   luxurious Dieux experience. Reddit supplies additional candidate destinations,
   but each still needs source-level adjudication before being called a switch.

4. **Skin Mercy may leave two narrow jobs unresolved.** A 2026-01-06 editorial
   use test reports the need for a separate occlusive on severe dry/eczema spots
   and a primer under concealer. Those are sharper opportunities than a broad
   claim that the cream is not hydrating.

5. **Strong delight is strategically binding.** Air Angel's light, non-oily
   hydration and Instant Angel's richer cosmetic elegance are repeated defenses.
   Competitive work should preserve those jobs while improving fit, value, or
   tolerance; otherwise it attacks where Dieux is strongest.

## Why Phase A cannot seal from this work

- The 27 login-wall packets have no thread evidence and are excluded.
- Only one complete retailer corpus is coded; Sephora review bodies and Dieux
  direct-review bodies were not captured here.
- Five editorial use tests are useful triangulation but not an independent
  customer sample.
- Regex nominations have not received final semantic adjudication, including
  true-switch versus contextual-mention review.
- No evidence-floor plus material-exhaustion decision has been made for Dieux.
- The live controller adoption verdict remains rejected because its earlier
  ignored-block and shared-controller incidents cannot be repaired after the fact.

Therefore the truthful status is **preliminary evidence consolidated; Phase A
open; no acquisition seal**.

## Implemented controller correction

The controller now treats either of these as a challenge even if the capture
subprocess exits zero:

1. packet metadata reports an access block; or
2. a Reddit request resolves on the same host to a final `/login/` URL, including
   the observed `reason=lor2` redirect with `access_blocked: false`.

The run-root process lock, held-item retry behavior, block ceiling, and distinct
Google/Reddit endpoint checks remain fail-closed. Deterministic regression tests
cover the login-redirect false-success case. The correction prevents capture
volume from impersonating evidence; it does not retroactively validate the live
dogfood or grant research-use credit.
