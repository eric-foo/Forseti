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
- **Adjudication depth: the full floor-cleared pool.** Every candidate that
  clears gate 1 — including sub-floor exception rows — is adjudicated.
  Owner decision 2026-08-01, superseding the same-day top-14 + band-slice
  rule by subtraction: partial depth left 482 admissible threads (32% of its
  unseen rows) unread in the 2026-07-31 pool while silently setting the
  effective floor at 63–177 comments in large venues, and full-pool
  adjudication of that same pool (2,820 rows) proved affordable in one
  session. Full depth deletes the unseen-tail residual and both depth
  sub-rules. The dive budget below, not review depth, is the scarcity
  control.
- **Dive budget: 2 threads per subreddit** among gate-5 survivors, ranked by
  comments, extended to 3 in the six venues carrying the densest
  failure/unmet-need signal in that week's read. This frame's commission is a
  persona rather than a named brand, so gate 3 does not bound spend on its own;
  the cap substitutes until a named client narrows scope.

### Leaderboard lane: `weekly_category_leaderboard_v0`

Owner-directed, 2026-08-01. A praise or holy-grail thread is weak for the
problem queue (gate 4's polarity is unchanged), but its top-scored comments
are crowd-validated who-owns-the-category evidence. That evidence is read
through a separate shallow lane rather than by bending the problem gates:

- **Selection is mechanical.** Praise/holy-grail-format titles with `50+`
  captured listing comments; no model adjudication and no gate sequence. The
  comment floor is what bounds the lane's size. Lowered from `100+` by owner
  decision 2026-08-01: the 50–99 praise band (32 recorded rows that week)
  otherwise falls between this lane and the problem queue by design, and the
  lane's cost is capture minutes, not judgment. The weekly reader emits the
  lane (`leaderboard_lane` in its output, `--leaderboard-capture-list-output`
  for a ready URL list, appearance-poll titles excluded); already-captured
  threads are deduplicated at capture-list build time, not in the reader.
- **Capture cost is identical to a dive.** A leaderboard thread is captured
  whole-tree at the standard cadence; the lane is cheap in judgment, not in
  requests, so it queues after the week's problem dives.
- **The read is shallow.** Top comments by score only, as a competitive map of
  crowd-validated favourites. Comment score orders the read; it does not
  establish truth, and a leaderboard read never substitutes for problem-dive
  evidence or admits a thread to the problem queue.

### Census lane: `weekly_wear_census_v0`

Owner-directed, 2026-08-03. Daily SOTD-type and indie-daily threads are a
behavioral worn-share census — commenters report what they actually put on
that day — the honest counterpart to the leaderboard's stated favorites, and
the only listing shape that surfaces indie houses stated-favorite formats
never rank. Adopted on a measured test (17 rejected daily/mega threads
recaptured; 9 usable): SOTD and indie-daily shapes carried 91 of 107 wear
reports with 9 embedded signals (6 discontinuation mentions), while daily
discussion/advice/help threads yielded 8 qualifying reports across 68
comments and stay rejected.

- **Selection is mechanical.** SOTD/scent-of-the-day/indies-of-the-day titles
  with `20+` captured listing comments, capped at 3 per venue per week
  (most-commented days first); no model adjudication. The weekly reader emits
  the lane (`census_lane` in its output, `--census-capture-list-output` for a
  ready URL list).
- **The read is a tally.** Wear/use/bought reports per brand, plus embedded
  signals (discontinuation, counterfeit, selling-off, reformulation
  complaints), which route to the read layer. The census orders attention; it
  never establishes truth, feeds admission gates, or substitutes for
  problem-dive evidence. It is a community panel, not a market sample, and
  the weekly read must label it as such.

## Required sequence

Apply the following sequence. Do not collapse it into an additive score or
encode the qualitative gates as keyword weights.

### 1. Mechanical discussion floor

- Captured listing comments `0–9`: return `no` for the general deep-read queue.
  Preserve the listing for direct commission-specific retrieval.
- Captured listing comments `10+`: continue to model adjudication.
- **Sub-floor exception (owner decision 2026-08-01):** a thread at `4–9`
  comments whose title carries an explicit failure, adverse-reaction,
  authenticity, discontinuation, or dupe/substitution signal continues to
  model adjudication with `selection_reason: sub_floor_exception_signal`.
  The pattern lives in the weekly reader; swap/WTS administration is excluded
  by title prefix. Measured on the 2026-07-31 pool: 47 of 1,654 sub-floor
  threads matched and read as direct extensions of that week's clusters, so
  the exception recovers the floor's highest-value losses for ~35 extra
  adjudication rows a week and zero capture cost. It gates nothing above the
  floor and admits nothing by itself.
- **Engagement branch of the sub-floor exception (owner decision
  2026-08-01):** a sub-floor thread (`0–9` comments) in a discussion venue
  with score `40+` continues to model adjudication with `selection_reason:
  sub_floor_engagement_signal`. High score at low comment count is the
  silent-resonance shape — many felt it, nobody answered — which the title
  branch cannot see under an ordinary title. Raw score fails as an
  instrument (the measured band's top scorers were ~90% visual showcases),
  so the branch excludes showcase venues; the excluded-venue set lives in
  the weekly reader and is a named maintenance point that must track roster
  changes. Measured on the 2026-07-31 pool: 72 rows, ~19% adjudicated `yes`,
  several invisible to every other selection instrument. The owner accepts
  the false-positive cost: the price is a title read, and gate 5 does the
  rest.
- Missing comments: route as missing data; never coerce to zero.
- Post score—including score `0`—never independently vetoes a thread.
- Use the freshest available captured counts.

The floor is a budget rule, not a claim that suppressed threads contain no
useful text. It intentionally accepts occasional poster-only misses.

Raised from `4+` to `10+` by owner decision 2026-08-01, measured against the
414 already-dived threads rather than argued: dives landing in the 4–9 band
carried three or more named brands 9% of the time against a 39% corpus
baseline, and averaged 0.7 brands per thread. A thread that small has not held
a conversation yet, so a deep read has nothing to read. Applied to a real
weekly pool the change removes 37% of the review queue and four of 129
admitted threads, all low priority.

The floor's value is adjudication cost, not dive quality — the ranking
already puts most admitted threads well above it. At full-pool adjudication
depth the review queue is exactly the floor-cleared pool, so the floor (with
its exception) is the single knob that sizes the weekly adjudication.

**Do not raise it further without re-measuring.** At `30+` the same corpus loses
20 of 129 admitted threads including two high-priority ones, and 14 venues fall
below their dive budget. Underserved-segment problems live in small threads —
a problem affecting everyone gets 300 comments, a problem affecting an
overlooked group gets 25 — so a higher floor deletes exactly the niche findings
this policy exists to surface. That protection is only as real as adjudication
depth makes it: any per-venue review cap silently re-raises the effective
floor in large venues regardless of the floor written here, which is why the
standing frame binds adjudication depth to the full floor-cleared pool.
Evidence: `docs/research/reddit_dive_yield_calibration_2026_08_01_v0.md`.

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

`priority_band: suppressed` accompanies `no`. A decision record without a
decision frame is invalid for reuse.

**Borderline routes to capture (owner decision 2026-08-03).** A `borderline`
row joins the week's capture list alongside `yes` rows; its bounded
uncertainty is resolved by the captured thread itself, at extraction time,
not by leaving the row uncaptured. Measured before adopted: the 2026-08-01
week's 119 borderline rows had died silently; capturing them (55 correctly
captured in the test batch) yielded roughly 85% real signal — including a
second independent thread for an existing wound card and two multi-voice
findings invisible at listing level. This is the standing
false-positive-over-missed-latent preference applied at the admission seam:
only a model `no` suppresses capture. Extraction workers label borderline
lanes explicitly, and a captured borderline thread that proves empty is
recorded as `NO_SIGNAL` in its extract line, keeping the yield measurable
week over week.

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

### Weekly read deliverable contract (owner decision 2026-08-01)

The weekly read's primary output is **GTM target cards**, in two lanes, with
cluster synthesis compressed to context and the leaderboard annex retained:

- **Wound card** (a named brand bleeding now): brand and product; the problem
  in one plain sentence a founder outside this project can read cold — no
  internal vocabulary; `independent_reporters` (count plus commenter handles,
  re-readable in the cited packet); thread size(s) and ids; two verbatim
  quotes; where the customers say they are going instead; one sentence on why
  the brand would pay to see this; caveats (single-thread, suppression
  signals, counterfeit-vs-product confusion).
- **Opportunity card** (an unserved gap with no wounded incumbent): the gap in
  one plain sentence; who has the demand; which challenger brands the
  evidence names as positioned to claim it; same corroboration and citation
  fields.

Binding rules: **no minimum card count** — a thin week reports two cards or
zero rather than manufacturing wounds; corroboration is a counted list of
named independent reporters, never an adjective, and every card separates
**within-thread reporters** from **cross-thread appearances** (distinct
captured threads naming the same brand-problem), because the two are
different strengths of evidence and conflating them overstates a card; this contract changes the
read layer only and never feeds back into admission gates (brand-attribution
is not a selection criterion — the calibration artifact records why); any
card going client-facing is re-read against its cited packets first and
gains at least one non-Reddit corroboration. Extraction workers emit, per
thread, the fields the cards consume: core problem, named brands in stated
context, `independent_reporters` (count + handles), `where_customers_go`,
verbatim quotes, corroboration basis, and commercial signal. Reversal
condition: if two consecutive weeks yield fewer than two honest cards, the
card-first shape is overhead and cluster synthesis leads again.

## Accepted residuals and non-claims

- Captured threads are depth-bounded, not exhaustive. On the www surface the
  in-place comment tree is expanded until no control remains, and the deep tail
  below that bound sits behind `Continue this thread` anchors that are
  `rel="nofollow"` links to separate pages, which this lane does not follow.
  Two measured captures reached 152 of 198 and 174 of 209 declared comments.
  Every thread record therefore carries `comment_completeness` stating the
  declared total, the captured count, and the gap. "Deep-read all captured
  comments" above means exactly that: all comments the record contains, with
  the shortfall visible rather than assumed away.
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
