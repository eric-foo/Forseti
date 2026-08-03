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

### Tail audit (post-pass, same day)

A false-rejection audit over the recorded `no` rows found: the categorical
wholesale venues spot-check clean (all 8 dermatologyquestions rows are genuine
crowd diagnosis, all 14 diyfragrance rows genuine formulation; zero flips);
the praise rejections at 100+ comments are leaderboard-lane inputs, routed not
lost. Three named softness zones remain, in size order:

1. **The floor, not the adjudication, is the dominant false-rejection
   reservoir**: 1,654 threads at 4–9 comments were never read, ≈150 of them
   brand-rich at the measured 9% rate. Deliberate, measured, and recorded in
   the calibration artifact — but it is where most true positives went.
2. **~55 image-dependent `no` calls** (39 `crowd_diagnosis_or_clinical`, 16
   `no_visible_commercial_object`) carry the reader's own
   insufficient-context flag: the gate-5 objective was inferred from
   venue+flair with the image unseen. This is the least-grounded decision
   class in the record; some are statistically wrong. The other ~316
   context-flagged rejections are format-legible (WTS, FOTD, SOTD, haul)
   regardless of image.
3. **32 praise-shaped threads at 50–99 comments** fall between lanes by
   design: too praise-shaped for this queue, below the leaderboard lane's
   100+ floor.

Two follow-ups from the audit, owner-directed:

- **One record flipped on captured evidence.** The r/DIYfragrance JPG Le Male
  Le Parfum formula request (`1v5ewzf`) was captured (one bounded request,
  13/13 comments) to test whether the community supplies formulas. It does —
  a full quantitative formula inline, paid and free formula marketplaces, and
  GCMS reverse-engineering services. The row is amended `no → yes` on
  verified dupe-demand evidence; the venue's gate-5 suppression otherwise
  stands. Finding: **dupe demand extends below the finished-clone tier to a
  self-make tier with its own supply chain.**
- **Sub-floor exception rule: adopted, tuned, applied.** Owner go 2026-08-01.
  The rule is live in gate 1 and the weekly reader (WTS-prefix exclusion,
  plus reformulation/availability terms that immediately caught a "VS
  Midnight Bloom formula changed??" and a "Fenty Midnight no longer
  available?"). Applied retroactively to this week's 4–9 band it selected 44
  rows: **37 `yes` (3 high — the Cetaphil "crazy reaction", the Beauty of
  Joseon "weird reaction", the VS reformulation), 7 `no`.** Records:
  `reddit_weekly_latent_problem_adjudication_2026_08_01_exception_slice_v0.json`.
  The three highs corroborate the counterfeit/QC and reformulation clusters
  from the smallest threads of the week — the floor's blind spot, now with
  a working exception.

The image-dependent rejection class (audit item 2) was reviewed by the owner
and closed as not worth pursuing; those rows stand as `no`. The leaderboard
lane floor was lowered to 50+ (policy updated); mechanical selection with an
appearance-poll exclusion yields 41 threads this week, queued for capture as
`reddit_leaderboard_capture_list_2026_08_01_v0.json`.

**Integrated weekly funnel, final:** 6,560 eligible threads → 2,776 cleared
the 10+ floor, 44 entered via the sub-floor title exception, and 72 via the
engagement branch (score 40+ at 0–9 comments, discussion venues; owner
decision the same day, accepting the false-positive cost for silent-resonance
coverage — records in
`reddit_weekly_latent_problem_adjudication_2026_08_01_engagement_slice_v0.json`)
→ **2,892 adjudicated end to end** → **785 `yes`** (27%; 129 top-14 + 122
band + 483 full pool incl. one capture-verified flip + 37 title-exception +
14 engagement, the last including finds invisible to every other instrument:
an eczema-in-summer comic resonating at score 122 with 3 comments, a
working-in-beauty overconsumption-struggle thread, a 1-comment "90 days of
adapalene changed my life"), 119 `borderline`, 1,988 `no` — plus 41
leaderboard-lane threads read shallow, for **826 threads flowing to
downstream reads**. 135 problem dives and 1 verification capture in the
lake, leaderboard capture in flight.

## Rejection composition audit (added 2026-08-03)

Owner question: what did we reject, and why. Basis: the 1,172 per-row `no`
records and 119 `borderline` records across the band, full-pool, exception,
and engagement passes. Honesty note first: the original flat-14 pass recorded
only its 129 admissions per-row; its ~816 rejections exist as aggregate
venue-level suppressions in this document, not as per-row reason codes. The
by-subtraction full-pool practice adopted mid-week records every row, so this
gap does not recur.

Primary reason distribution over the 1,172 recorded rejections:
appearance_validation 354 (30%) — rate-my-look photo threads, concentrated in
r/MakeupAddiction, r/malegrooming, r/Nails; crowd_diagnosis_or_clinical 238
(20%) — what-is-wrong-with-my-skin/scalp diagnosis asks, concentrated in
r/tressless and the skin venues; praise_or_sentimental_discussion 230 (20%);
wts_swap_administration 122 (10%, of which 111 are r/fragranceswap
marketplace listings); low_expected_decision_contribution 64 (5.5%, all
r/PerfumesThatFeelLike vibe-matching); retailer promotion, news-release,
DIY-formulation, megathread, and technique codes make up the tail. Rejected
comment mass is 29,785 versus 33,110 admitted — the gates declined roughly
half the conversation volume on the grid.

Venue economics the distribution exposes: r/fragranceswap went 0-for-111 (a
pure marketplace; delisting it from the weekly problem grid is the obvious
subtraction candidate — its ISO demand signal already routes via the
title-exception rule, which excludes [WTS]/[WTT]). r/Nails and r/malegrooming
reject at 95%, r/MakeupAddiction at 87% — showcase-dominant venues carried
for their occasional admits. The best-yield venues (r/FemFragLab 47% reject,
r/fragrance 52%, r/30PlusSkincare 52%) are the discussion venues the
engagement exception already privileges.

False-reject probe: the 25 highest-engagement rejects were re-read from their
listing rows; all are genuine (astrology-themed look votes, pub-look
showcases, collection flexes). Of 230 praise rejections only 5 were
independently caught by the leaderboard lane — but scanning the 31 praise
rejects at 50+ comments the lane missed, they are sentiment threads without
ranking shape (collection tours, milestone manicures, "I love Creed"), which
the leaderboard title pattern correctly ignores. No new exception rule earns
its keep from this audit.

The genuine residual is the borderline set: 119 rows recorded and then never
captured — a silent disposition. 55 are insufficient_listing_context
(low-information titles like "is it worth", "anything good here" at 65-93
comments that could hide anything), 17 possible_product_demand, 9
behavior_shift_signal (no-buy and stopping-collecting threads that are
exactly Cluster 7's overconsumption counter-current, including "freezing my
credit card today" at 54 comments). At capture cadence the whole set costs
about 1.3 hours. Disposition decision deferred to the owner: capture the
borderline set as a bounded batch under the standing
false-positive-over-missed-latent preference, or record borderline=drop as
the standing rule.
