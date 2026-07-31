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
