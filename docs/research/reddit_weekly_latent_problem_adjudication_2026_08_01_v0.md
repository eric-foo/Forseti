# Reddit Weekly Latent-Problem Adjudication — 2026-08-01 v0

```yaml
retrieval_header_version: 1
artifact_role: Weekly deep-dive admission record
scope: >
  Model adjudication of the 2026-07-31 weekly Reddit listing read against the
  standing decision frame weekly_latent_problem_gtm_discovery_v0, producing the
  admitted deep-dive set and the venue-level suppressions behind it.
use_when:
  - Reading why a given thread entered (or did not enter) this week's dive queue.
  - Auditing how the standing weekly frame behaves against a real corpus.
  - Rebuilding or amending this week's capture list.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_listing_efficiency_policy_v0.md
  - docs/research/reddit_weekly_latent_problem_adjudication_2026_08_01_v0.json
  - docs/research/reddit_weekly_latent_problem_capture_list_2026_08_01_v0.json
stale_if:
  - A later weekly read supersedes the 2026-07-31 listing snapshot.
  - The standing frame, its dive budget, or the governing policy gates change.
  - The capture list is executed and the admitted set is amended on its results.
```

## What this is

The first application of `weekly_latent_problem_gtm_discovery_v0`. The weekly
reader produced the mechanical layer; this artifact is the model adjudication
the policy requires before any candidate becomes a capture slot, and the
record that lifts `capture_list_status` from
`blocked_pending_commission_model_adjudication` for this week only.

It is not validation, not readiness, not a claim that the admitted threads
contain decision-bearing evidence, and not authorization for anything beyond
the named capture list.

## Result

| | |
|---|---|
| threads read | 6,560 |
| cleared the 4+ comment floor | 4,430 |
| venues with candidates | 83 (roster 87; 4 venues contributed none) |
| working set adjudicated | top 14 per venue by comments |
| **admitted `yes`** | **129** |
| of which high priority | 51 |
| venues adjudicated to **zero** `yes` | 17 |
| capture slots | 127 (two already captured this session) |

Against a dive budget of 2 per venue and 3 in the densest failure-signal
venues, the ceiling was ~180. The adjudication came in under it at 129 — not
by hitting a cap, but because 17 venues produced nothing admissible and 10
more produced only one.

## The three-yes venues

The frame allows a third dive in the six venues carrying the densest
failure/unmet-need signal. Two corrections were applied in the reading:

1. **A volume floor is required.** The raw density ranking put `makeupdupes`
   (10/10), `wavyhair` (4/4) and `haircarescience` (3/3) on top. Those are
   small samples, not dense venues. Applying `n >= 30` gives the intended six:
   `malegrooming`, `haircare`, `koreanbeauty`, `beauty`, `skincare_addiction`,
   `drugstoremua`.
2. **The mechanical cue disagreed with the frame.** `malegrooming` ranked
   *first* on density (0.81) but yielded **one** `yes`: its rows are almost
   entirely appearance validation ("beard or no beard?", "which suits me?"),
   which gate 5 suppresses. Its score came from every such question counting as
   `concrete_question_or_request`. The allowance is a ceiling, not a quota, and
   it was not spent there.

Three `yes` rows were taken in `haircare`, `beauty`, `drugstoremua`,
`koreanbeauty`, and `skincare_addiction`.

## Venues adjudicated to zero

Recorded rather than silently absent, so a reader can see the suppression is a
decision with a gate behind it.

| venue | governing gate |
|---|---|
| `nailart`, `diygelnails`, `gelnails`, `makeupflatlays` | gate 5 — showcase venues (policy already names r/NailArt as heavily suppressed) |
| `fragranceswap`, `redditlaqueristaswap`, `makeupexchange` | gate 5 — WTS/swap administration |
| `makeuptips` | gate 5 — generic technique help and appearance validation |
| `dermatologyquestions` | gate 5 — crowd diagnosis outside a matching commission |
| `beautyboxes`, `muaonthecheap`, `muacjdiscussion` | gate 5 — retailer promotions and promotional chat |
| `whybrows` | gate 5 — appearance snark |
| `diybeauty` | gate 5 — specialist DIY formulation outside a matching commission |
| `perfumesthatfeellike` | gate 3 — vibe matching carries no commercial decision |
| `fragrancestories` | gate 6 — SOTD daily format, conditional and unmet |
| `newinbeauty` | gate 4 — launch feed; announcements are not problem evidence |

`newinbeauty` is worth noting: it was added to the roster this cycle, and under
this frame it produced nothing. Every row is a launch announcement. That is a
fact about the frame's fit with the venue, not a reason to retire it — a
launch feed is exactly the wrong shape for latent-problem discovery and may
still serve a competitor-tracking commission.

## What the frame actually selected for

The admitted set clusters, and the clusters are the point:

- **Reformulation and discontinuation harm** — talc removal hurting wear
  (r/Sephora), Cantu reformulation (r/NaturalHair), a holy-grail foundation
  gone cakey (r/PaleMUA), discontinued-fragrance longing (r/fragrance).
- **Treatment failure and adoption fear** — finasteride making loss worse,
  oral minox + spiro "way worse", "now I'm scared of minoxidil", masseter botox
  aging a user, corroborated by a second botox brow-drop thread in the same
  venue.
- **Channel and authenticity** — a counterfeit COSRX from Amazon causing months
  of acne, "SEPHORA is lying to you", got2b using AI models on dye boxes,
  influencer trust in two fragrance venues.
- **Format and compliance gaps** — sunscreen you can actually apply at the
  recommended amount, reapplying over makeup, mini bottle sizes, large-format
  Asian sunscreen. The sunscreen-compliance problem appears independently in
  r/makeup and r/SunscreenReddit; that cross-venue repeat is the frame's
  corroboration signal firing.
- **Overconsumption backlash** — "overconsumption rules everything around me",
  quitting all skincare and improving, haircare shopping "my version of
  gambling". A snowballing problem, and precisely the kind a client would not
  have on their agenda.
- **Underserved segments** — deep-tone bronzers, olive undertones pulling
  orange, pale users wanting a white cast, female pattern loss at 18, adult
  acne, postpartum hair, men's basic skincare illiteracy.

## Method and residuals

Working set was the top 14 rows per venue by comments, the reader's own review
order. Gates were applied in sequence per the policy, with the frame's readings
(gate 3 forward-reading, gate 4 polarity shifted, opacity as a weak cue,
corroboration ordering `yes` rows).

Named residuals:

- **The working set is not the full candidate set.** 4,430 rows cleared the
  floor; roughly 1,050 were adjudicated. A problem-shaped thread ranked below
  14th in its venue was not seen. This is the budget working as designed, but
  it is a real blind spot, not exhaustive coverage.
- **`borderline` rows were not separately enumerated.** Rows that were neither
  admitted nor venue-level suppressed are absent from the record rather than
  carried as `borderline`. A future amendment should carry them, since the
  policy treats `borderline` as resolvable.
- **Two admitted threads were already captured** this session (r/Sephora talc,
  r/tressless finasteride) and carry `capture_state: already_captured`. They
  are recorded as `yes` so the admitted set is not silently short.
- Admission is per this frame only and must not be reused as a universal claim
  about any thread.

## Band-slice supplement, 2026-08-01 (same day, after the depth-rule decision)

The owner-directed adjudication-depth rule (top 14 plus the 6 highest-commented
candidates in the 10–49 band per venue) was applied retroactively to this
week's pool: 318 additional rows across the 55 venues the flat top-14 cap had
bound. Full records:
`reddit_weekly_latent_problem_adjudication_2026_08_01_band_slice_v0.json`.

Result: **122 `yes` (20 high), 31 `borderline` (now enumerated, unlike the main
pass), 165 `no`.** The 38% yes rate against the main pass's ~14% has a
mechanism — validation, showcase, and poll formats concentrate in
high-comment threads, while small threads skew toward concrete product
questions — but single-adjudicator drift between passes is a live confounder,
so the rate gap is directional, not calibrated.

High-priority findings that corroborate existing clusters: counterfeit/
authenticity (fake Cetaphil in r/tressless, a retinol "that doesn't actually
exist" in r/30PlusSkinCare), dupe-tier demand (Catrice/Pillow Talk, elf vs
Clinique balm, influencer-dupe regret, a clone that degraded to alcohol),
foundation defection (a holy-grail foundation "turned cakey" plus a Double
Wear replacement rant), shade gaps (Dior's missing 2WO olive shade), toddler/
kids textured-hair care (three independent threads), and product-exhaustion
fatigue ("tried everything" in three venues). New singletons: the IFRA 52nd
amendment bergamot restriction (regulatory reformulation risk), minoxidil pet
toxicity, and a vendor ghosting buyers.

Capture outcome under the standing budget: 8 band `yes` rows fell in venues
with unused dive budget and were queued; the other 19 high-priority rows sit
in venues whose budget the main pass already filled, so they are recorded but
not captured — capturing them would exceed the standing 2–3 per venue cap and
is an owner option, not an agent default. The unseen-tail residual above
shrinks accordingly: after this supplement roughly 1,510 of 2,776 candidates
remain unreviewed, all below rank 14 and outside the band slice.

## Full-pool supplement, 2026-08-01 (same day)

Owner direction: adjudicate everything. The remaining 1,513 candidates — every
row below rank 14 and outside the band slice — now carry decision records:
`reddit_weekly_latent_problem_adjudication_2026_08_01_full_pool_v0.json`.
**The 2026-07-31 pool is 100% adjudicated: 2,776 rows in three passes (945
top-14, 318 band slice, 1,513 full pool), 733 total `yes`. The unseen-tail
residual for this week is closed.** Decision records only; per owner direction
no capture slots were issued from this pass, and the dive budgets remain as
already captured.

Full-pool result: **482 `yes` (19 high), 84 `borderline`, 947 `no`** — a 32%
yes rate, consistent with the band slice's 38% and the same mechanism
(validation and showcase formats crowd the top of big venues; concrete product
questions live small). Four venues were adjudicated wholesale under their
categorical format suppression (`fragranceswap`, `redditlaqueristaswap` as
WTS/swap administration, `dermatologyquestions` as crowd diagnosis,
`diyfragrance` as specialist formulation — 132 rows) rather than title by
title; a stray admissible thread inside them is an accepted residual. In
`perfumesthatfeellike`, concrete olfactory-profile requests were admitted and
cultural-reference whimsy suppressed as `low_expected_decision_contribution`
— a judgment split, named here because the band slice had admitted that
venue's top rows wholesale.

New high-priority signal concentrated in three places:

- **Quality control as a cross-category cluster** — JPG Le Male "something is
  off", Skin1004 fill variance, an indie "acceptable variation or QC issue?",
  a serum "normal color or oxidized?", "do all LynB polishes feel like this?",
  a blocked spray nozzle, a Sephora pickup order "sitting in someone's
  shower". Batch/condition doubt is now corroborated across fragrance,
  K-beauty, indie, polish, and retail fulfillment.
- **Reformulation anxiety, now five-legged** — IFRA bergamot, Bleu de Chanel
  "has been reformulated", original Glossier You "undoubtedly better",
  Givenchy Pi "weaker lately?", plus the JPG batch thread above.
- **Channel trust** — "Operation Eau de Fraud", a "Luwest Viltton" score,
  fragrance packaging "supposed to come in a box?", honest reviews "getting
  removed on Jomashop?", K-beauty reseller ranking (Yami vs YesStyle vs
  Stylevana), Amazon prescribing finasteride from two photos, a near-scam
  Dutasteride order, and the mass-channel value wave (Walmart/Costco/Sam's/
  TJ Maxx/Marshalls threads across three fragrance venues).

Singleton highs worth a future look: disability-friendly polish technique and
tremor-safe shaving (accessibility in beauty, two independent venues), and
olfactory changes persisting after a JHAG product (safety signal).
