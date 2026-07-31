# Reddit Listing-Efficiency Policy v0

```yaml
retrieval_header_version: 1
artifact_role: Reddit source-family deep-dive selection contract
scope: >
  Commission-conditioned selection of captured Reddit listings for scarce
  exact-thread deep reads. Owns the general discussion floor, model gates,
  admission outputs, and post-admission evidence posture.
use_when:
  - Turning Reddit grid/listing rows into an exact-thread capture queue.
  - Applying or reviewing the weekly Reddit demand-read deep-dive gate.
  - Calibrating Reddit listing selection against captured thread content.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_weekly_demand_radar_spec_v0.md
  - docs/research/reddit_listing_efficiency_full_corpus_application_v0.md
  - docs/research/reddit_listing_efficiency_owner_calibration_v0.md
stale_if:
  - A later owner decision changes the default customer, value definition, or general discussion floor.
  - The listing projection gains or loses media, OCR, alt-text, entity-link, score, or comment fields.
  - A fresh held-out audit finds a repeated material error not covered by this contract.
```

## Status and ownership

Owner-directed lane policy, 2026-07-28.

The Reddit source-family lane owns this deep-dive selection contract. The Data
Lake remains neutral storage: it preserves and retrieves listing/capture
evidence but does not own source-selection judgment. A listing admission is
always tied to a decision frame and must not be persisted or reused as a
universal truth about the thread.

The default decision frame is a scaling beauty or personal-care challenger
trying to gain share or position itself against named competitors.

**Value is expected contribution to a commissioned company decision per
exact-thread deep read.** Popularity, general usefulness, and information
volume are not substitutes for that contribution.

### Standing weekly frame: `weekly_latent_problem_gtm_discovery_v0`

Owner-directed, 2026-08-01. The weekly demand radar serves the default
challenger commission above, seeking **latent problems usable for GTM**: a
problem the client is uncomfortable with but has not yet articulated, a problem
that is small now and structurally worsening, or an evident problem already in
view. All three are in scope.

This frame narrows which evidence counts; it does not replace the default
customer. Under it:

- **Gate 3 reads forward.** A decision need not already sit on the client's
  stated agenda; an unvoiced or emerging decision counts as current impact — a
  problem the client has not named cannot be on their list. Scope still binds:
  wrong category, customer, or geography remains `no`. This widening is
  frame-scoped and does not alter gate 3 for a named-client commission, where
  the narrow reading is what makes the dive budget work.
- **Gate 4 polarity shifts.** Praise, holy-grail, routine, and collection
  formats are weak rather than strong under this frame: they evidence what
  already works, not where the gap is. Failure, disappointment, workaround,
  substitution, compatibility conflict, and unmet-need questions carry the
  admission.
- **Opacity is weak evidence of low value.** A latent problem is by definition
  unnamed, so it is described in ordinary language rather than product
  vocabulary; and established community formats carry purchase, acquisition,
  and disappointment evidence under titles that state nothing. Apply gate 2 to
  the visible commercial object, including subreddit format convention, not to
  keyword presence. The weekly reader's `listing_context_insufficient` tag is a
  non-binding cue known to over-flag this frame's strongest rows; it may
  support `borderline`, never a `no`.
- **Corroboration raises priority.** A problem carried by independent voices,
  repeated across threads, or recurring across subreddits outranks an equally
  specific single-poster complaint, because a snowballing problem is one that
  more than one person already has. Corroboration orders `yes` rows; it is not
  an admission requirement and its absence is not a `no`.
- **Dive budget: 2 threads per subreddit** among gate-5 survivors, ranked by
  comments, extended to 3 in the six venues carrying the densest
  failure/unmet-need signal in that week's read. This frame's commission is a
  persona rather than a named brand, so gate 3 does not bound spend on its own;
  the cap substitutes until a named client narrows scope.

## Required sequence

Apply the following sequence. Do not collapse it into an additive score or
encode the qualitative gates as keyword weights.

### 1. Mechanical discussion floor

- Captured listing comments `0–3`: return `no` for the general deep-read queue.
  Preserve the listing for direct commission-specific retrieval.
- Captured listing comments `4+`: continue to model adjudication.
- Missing comments: route as missing data; never coerce to zero.
- Post score—including score `0`—never independently vetoes a thread.
- Use the freshest available captured counts.

The floor is a budget rule, not a claim that suppressed threads contain no
useful text. It intentionally accepts occasional poster-only misses.

### 2. Listing-context sufficiency

The model must be able to identify the commercial object from listing-visible
context.

- If a title depends on “this,” “which one,” an image, a crosspost payload, or
  an opaque community format, return `borderline` with reason
  `insufficient_listing_context`.
- Resolve that state only with cheap listing-level context already available:
  media presence/count, linked product identity, OCR, alt text, or equivalent
  projection fields.
- Do not open the hidden comment discussion merely to repair the listing
  projection.
- Treat `insufficient_listing_context` as a reason code attached to
  `borderline`, not as a fourth admission state.

### 3. Commission applicability

Ask whether the visible listing could change an in-scope decision for the
declared commission.

- Current decision impact: continue.
- Useful only to another brand, category, retailer, service, geography, or
  treatment commission: return `no` for the current queue and preserve for
  retrieval.
- No plausible commercial decision: return `no`.

This gate prevents rich but irrelevant evidence from consuming the current
dive budget.

### 4. Visible decision promise

Raise admission when the listing visibly promises:

- named-product performance, failure, praise, disappointment, or review;
- recommendation, comparison, substitute, dupe, or discontinued-product
  replacement;
- a specific user, condition, constraint, product type, and desired outcome;
- completed use, repurchase, abandonment, regret, or consumption cadence;
- price, access, purchase, refund, availability, or switching evidence;
- a disclosed product stack or product-compatibility problem;
- a verified creator/brand relationship with purchase or trust consequences.

Strong language without a visible commercial object does not qualify.

### 5. Objective suppression

Return `no` by default for:

- appearance validation, colour voting, or praise-only showcases;
- generic technique help with no product compatibility, usability, cost, or
  failure implication;
- crowd diagnosis, clinical-treatment advice, or procedure cadence outside a
  matching commission;
- gossip without a verified commercial relationship and consequence;
- WTS, resale, or swap administration;
- retailer operations/promotions, professional services, or specialist DIY
  formulation outside a matching commission.

High score or comment count cannot rescue the wrong objective.

### 6. Format and source priors

Normalize the format before deciding:

- Swatches are product-map evidence, not generic showcases, when products,
  undertones, discontinuation, price, wear, or substitutes are likely.
- Project Pan, empties, finish, and hit-pan formats are conditional on completed
  use, repurchase/non-repurchase, consumption, substitution, or regret.
- SOTD/FOTD/current-use formats are conditional on a disclosed stack,
  performance, purchase, or availability consequence.
- Product-compatibility technique questions are conditional; exact material or
  product-type interactions can be CI even when the wording asks “how.”
- Visual showcases remain suppressed unless listing-visible context makes a
  product stack, performance question, or purchase response likely.
- Consumer product/device experience is distinct from crowd diagnosis; medical
  adjacency raises the safety and corroboration burden but is not an automatic
  veto.
- `r/NailArt` and `r/DIYBeauty` remain heavily suppressed, not removed.
- WTS/swap sources remain suppressed for the general queue. Rare scarcity,
  release-cycle, or grey-market evidence stays retrievable for a matching
  commission.

### 7. Admission and ranking

The only admission values are:

- `yes`: expected current-decision contribution justifies the deep read;
- `borderline`: a bounded listing-context, applicability, or safety uncertainty
  must be resolved first;
- `no`: insufficient expected current contribution.

Rank only `yes` rows, in this order:

1. current commission fit;
2. explicit product/category decision promise;
3. likely independent evidence depth;
4. problem/user/constraint/outcome specificity;
5. competitor, switching, price, access, or positioning contribution;
6. lower interpretation and safety burden.

Pairwise preference never substitutes for independent admission.

## Required decision record

Every applied decision must carry:

```yaml
policy_version: reddit_listing_efficiency_v0
decision_frame: <commission/client/category being served>
thread_url: <captured listing URL>
listing_snapshot:
  captured_at: <known timestamp or missing>
  score: <integer or missing>
  comments: <integer or missing>
admission: yes | borderline | no
reason_codes: [<one or more concise reasons>]
priority_band: high | normal | suppressed
```

`priority_band: suppressed` accompanies `no`. A `borderline` row cannot produce
an exact-thread capture slot until its bounded uncertainty is resolved. A
decision record without a decision frame is invalid for reuse.

## After admission

Deep-read all captured comments for an admitted thread; do not stop at the top
comment. Separate independent voices from the original poster, bots, author
replies, and nested repetition. Comment points order presentation; they do not
establish truth.

Extract product mentions only in their stated context: performance, failure,
preference, purchase, switching, price, access, substitution, or neutral
mention. A whole-post score can corroborate resonance with a disclosed result
or stack but cannot attribute that result to one product.

Reddit remains one source. Before Deliver, connect surviving evidence to the
commissioned company, competitors, products, creators, claims, prices,
channels, partnerships, and every material outside source that could change
the decision. A thread is a lead or evidence fragment, not a client conclusion.

## Accepted residuals and non-claims

- Some useful poster-only threads below four comments will be missed.
- Some promising listings will produce no decision-bearing evidence.
- Opaque titles remain unresolved when no cheap listing context exists.
- Commission-specific evidence is intentionally absent from unrelated queues.
- Duplicate bodies under title/subreddit variants require upstream
  body-level near-duplicate handling; this policy does not define that
  mechanism.

This contract is not a learned scorer, relevance weight, subreddit allowlist,
corpus-wide accuracy claim, Judgment verdict, buyer proof, live Reddit
completeness claim, or authorization for broad crawling.
