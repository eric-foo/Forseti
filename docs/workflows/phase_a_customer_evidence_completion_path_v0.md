---
retrieval_header_version: 1
artifact_role: Phase A customer-evidence completion path
scope: Customer-language semantic integration from full acquisition corpus through cold-agent proof; campaign and Deliver boundaries remain separate
use_when:
  - Resuming the full Summer Fridays customer-corpus semantic run.
  - Applying the same Reddit/community plus retailer-review method to another company.
  - Deciding when customer evidence is ready to hand to Synthesize or Deliver.
  - Building or changing a Phase A commercial point frontier, point evidence pack, relation prompt, or quote-selection consumer.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
  - docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_customer_cross_source_proof_20260809_v0/README.md
---

# Phase A customer-evidence completion path v0

## Purpose

This is the durable path from a captured customer corpus to a complete,
retrievable evidence structure. It prevents a future operator from stopping
after two or three convenient examples or from treating Reddit and retailer
reviews as unrelated summaries. It does not produce a market conclusion.

The semantic leaf assessment, atomic evidence structuring, meaning-based
reconciliation, and evidence-packet projection together form the named
**Evidence Consolidation** stage. It begins only after acquisition has produced
an immutable, completely accounted corpus and ends only when the final corpus
hash has a complete, reproducible evidence packet or a visible unresolved
failure. This is a conceptual and completion boundary between acquisition and
Deliver, not a new globally numbered phase: historical Phase A, Phase B, Turn
B, Understanding, and Deliver vocabulary is not renumbered or migrated.

## Active commercial point-entry boundary

For the completed Summer Fridays Phase A packet, the business question is:
**Which customer-valued strengths and objections deserve commercial
investigation?** The no-provider
`build-customer-pull-point-frontier` command accounts every proposition matching
the requested product subject in one of three places:

- `retailer_first_queue` is read first because a retailer review is closest to
  a completed purchase;
- `community_discovery_queue` keeps customer points found only in community or
  qualified audience evidence visible and records retailer check-back as still
  open; and
- `nonpromoted_points` records why a proposition did not earn investigation.

The frontier also records every proposition excluded by the requested product
subject and reports the input, matched, and filtered counts. A stale or mistyped
subject therefore cannot make a smaller frontier look like complete packet
accounting.

Retailer is a first-look venue, never an admission gate. A community-only
purchase, repurchase, recommendation, recurring experience, or materially
engaged customer point may earn investigation without retailer support. It
does not become retailer corroboration. Conversely, creator-authored material
remains influence context and cannot enter either customer-truth queue.
Engagement is retained and ordered only within its own venue, role, and metric;
the frontier has no cross-platform customer-pull score.

Within each queue, more independent supporting origins lead. When origin counts
tie, cross-role independent recurrence leads same-role recurrence, followed by
more materially engaged supporting evidence items. Reported behavior remains a
commercially useful final tie-breaker, but generic trial or ownership does not
automatically outrank a better-corroborated strength or objection. This is a
queue-specific investigation order, not a universal source-quality ranking.
Materially engaged items may share one origin; they add resonance context but
do not add independent recurrence. An unavailable engagement posture adds no
materiality. Operator protection keeps a safety or costly-behavior point
admitted and accounted, but protection alone grants no ordering priority.

The frontier is a navigation artifact over a complete, non-truncated
`phase_a_evidence_packet_v3`; it is not packet v4 or a new evidence authority.
`materialize-customer-pull-point-selection-spec` turns one admitted proposition
into one hash-bound bounded-point selection with the normal thirteen-truth-origin
cap. For a non-value point with an explicit axis, candidate admission is the
union of every semantic row for the same product and axis plus the proposition's
literal refs. Every admitted row is newly judged against the exact bounded
point; sharing an axis grants no support or counter relation. Value points keep
literal-ref admission because their price/value behavior policy is not the
generic non-value route, and a hand-built value-first spec cannot claim the
non-value recent-year selection policy. The full packet and every frontier disposition remain
available; the displayed pack never implies prevalence.
Frontier specs use the exact bounded point as their direction: evidence that
the balm is expensive supports that objection, rather than being reversed by
the older positive-good-value box policy. Historical value-box selections keep
their stamped policy.

For a new point pack, relation confirmation occurs before the display cap:

```text
prepare-evidence-selection
  -> external first relation response over every admitted row
  -> prepare-preselection-relation-confirmation
  -> external hidden-label confirmation over every material, protected, or
     influence row that could reach display
  -> finalize-preselection-relation-confirmation
  -> external exact-quote response
  -> finalize-evidence-selection-quotes (no confirmation attachment for v7)
```

When that frontier-bound non-value point expands to a large axis pool, use the
named batch route at both model boundaries:

```text
prepare-evidence-selection-batches
  -> external named relation responses over every admitted row
  -> prepare-batched-preselection-relation-confirmation
  -> external named hidden-label confirmation responses over every material,
     protected, or influence row that could reach display
  -> finalize-batched-preselection-relation-confirmation
  -> external exact-quote response
  -> finalize-evidence-selection-quotes (no confirmation attachment for v7)
```

Both batch manifests bind contiguous complete row coverage and each response's
own batch identity. Batching is transport only: it changes neither candidate
admission nor the thirteen-origin cap. The second batching step is required at
full-axis scale; sending hundreds of confirmation rows as one open array would
recreate the truncation surface that named relation batches closed.

The confirmation frontier is independent of the first-pass relation. Therefore
a first-pass `exclude` cannot silently hide a materially engaged or protected
row. The confirming response may correct the relation and reason code; selection
then runs once over the corrected inventory. Every finally displayed row must
have crossed that confirmation boundary. Missing, duplicate, foreign, reordered,
or unconfirmed rows fail closed. Historical v6 quote manifests retain their
selected-row confirmation route for exact reproduction; they are not silently
restamped as v7.

Non-value axis-expanded point packs use `recent_year_coverage_v1` as a display
preference. The latest two calendar years present in the eligible pool receive
representation across available venue/role/native-metric buckets, up to half
the thirteen-origin cap after mandatory relation/protection reservations. When
eligible and space remains, one dated pre-window origin is retained so the
recent view does not erase earlier history. Undated rows remain in complete
candidate accounting. Age never changes a relation, independence, materiality,
or evidentiary weight. The final artifact groups selected IDs by literal
calendar year, with unavailable dates separate, and uses no strong/weak or
fresh/stale age judgment. Within a fixed venue/role/native-metric bucket,
source-native engagement still orders candidate display; it is never compared
across platforms, and an unavailable metric never sorts as observed zero. The
timeline is only a calendar ordering index: consumers dereference each selected
ID through `source_groups` and preserve its truth-support or influence layer.

## Operating path

```text
SERP map
  -> native customer-evidence acquisition
  -> complete Reddit/community and retailer-review source accounting
  -> run-local stable product identity
  -> Evidence Consolidation
       -> semantic leaf assessment
       -> atomic evidence structuring
       -> meaning-based cross-source reconciliation
       -> proposition/axis evidence packets
  -> acquisition seal when the current route contract is satisfied
  -> Synthesize / Deliver judgment
```

For each company, Phase A first verifies its products and the source-native IDs
used by each retailer or community coding artifact. The run then supplies a
small product-identity table. That table says, for example, that Sephora
`P455936`, Amazon `B0C42HJRBF`, and the verified relevant Revolve listing IDs
are presentations of Summer Fridays Lip Butter Balm for this run. Every map
entry cites preserved source evidence. Unclear equivalence stays unresolved.
For a method-v4 full run, that verified table is included once in every
reading assignment. It lets a worker name the same stable product across
Reddit and retailer evidence even when a Reddit leaf arrived without an
upstream product candidate. It does not assign by keyword: the leaf and its
conversation or product-page context still establish the subject.

The semantic workers read every admitted customer leaf. They interpret meaning
rather than exact wording and keep support, disagreement, conditions,
comparisons, uncertainty, and product versions separate. Reconciliation may
then join a Reddit observation and a retailer review when they concern the same
stable product and bounded meaning. It does not merge them merely because they
share a phrase.

A full-corpus run uses the run-v3 / bundle-v5 / method-v5 generation. Every
assessable leaf still receives exactly one context-aware judgment, made after
reading its parent and container context; there is no keyword or phrase gate,
and a short referential reply that adopts a specific parent complaint,
preference, product, or variant stays claim-bearing. What changes is only what a
leaf costs after that judgment: a leaf that is clearly outside scope, or clearly
inside the context but carrying no bounded proposition, terminates immediately
with no semantic unit, axis assignment, reconciliation candidacy, or packet
delivery. Ambiguous binding stays `unresolved` rather than being pushed into a
cheaper terminal disposition.

For a context-dependent short reply, operators and adjudicators inspect the
root question, immediate parent, and leaf together. They record the resolved
reading and keep separate what context supplied from what the leaf asserted.
For example, `which is your favorite?` -> `Vanilla Beige!` -> `My fav!` means
the final author also prefers Vanilla Beige. The leaf is claim-bearing
`personal_agreement`, not first-hand product experience. Because the two
visible handles are distinct, the pair may support same-thread recurrence for
that exact preference, with thread co-location disclosed; it is not
cross-venue corroboration and supplies no product axis. This is valid but
low-information recurrence: the child adds no reason, attribute, condition, or
explanatory detail. A reply such as `same` adopts only the clearly targeted
bounded meaning, not every clause of a multi-point parent.

Workers report those terminal decisions either individually or as explicit-ID
groups sharing one agent-authored reason. Grouping is transport compression, not
a sample or a default: every evidence ID is listed, raw occurrences are checked
for duplicates and unexpected or omitted IDs before anything is normalized, and
the durable raw response stays the record of evidence through hash-bound
compilation lineage. The new projection carries no static worker partition, so
any available worker takes globally missing work and atomic no-overwrite
publication remains the only durable truth boundary. Bundle and projection
verification happens once per controller invocation rather than once per
response.

The legacy v4 generation is unchanged and remains byte-reproducible; the paused
v4 run's artifacts are not migrated or restamped.

The final Evidence Consolidation packet is a retrieval surface. Asking for an
axis or bounded proposition returns the complete linked evidence union,
including counterevidence and unresolved adjacent material. Deliver owns any
later recommendation about price, premiumization, positioning, product work,
or campaign action.

The normal `project-evidence-packet` command emits
`phase_a_evidence_packet_v3`. It keeps v2's one-copy, source-grouped evidence
catalogue, but declares repeated evidence, engagement, and semantic-unit field
names once as named columns. Values shared by every row in a packet or source
group appear once as named defaults at that scope; all remaining row values map
positionally to explicit human-readable column names. Proposition rows still
link literal evidence and semantic-unit references under support, counter, or
adjacent relations. Raw engagement, observation time, source context, actor and
independence, conditions, behavior, uncertainty, and full-body bundle
resolution remain available. Operators do not select examples, supply a top-k
cap, perform a new lookup, or request v3 through an extra flag. Explicit v2 is
the matched comparison route; v1 is historical reproduction.

### Adopted token-cost baseline

On 2026-08-16, `phase_a_evidence_packet_v2` was adopted as the provisional
Phase A token-cost baseline. A matched model experiment compared v1 and v2 on three
frozen Summer Fridays propositions with 43, 20, and 9 evidence items. Each arm
used the same prompt and output schema for three repetitions, with arm order
alternated: 18 `gpt-5.6-sol` low-reasoning turns in total. V2 used 121,008
versus 183,786 input tokens, 85,179 versus 114,462, and 69,995 versus 88,508.
That is a reduction in every case (34.158%, 25.583%, and 20.917%) and 28.590%
across the matched set.

The saving is transport normalization, not evidence selection. V1 repeated
complete evidence content and proposition-local representations; v2 keeps one
evidence row and one selected semantic-unit representation, moves repeated
source semantics to a group header, and lets propositions reference those
units. The experiment returned 18 structurally valid responses with the
correct proposition IDs, no missing or invented cited references, and the
required condition, behavior, engagement, and uncertainty fields. Independent
semantic adjudication was not run, so the experiment establishes a structural
quality floor rather than semantic equivalence. Latency is explicitly
non-gating for this baseline; no storage-cost claim is needed.

This baseline must be reversed or revised if representative future cases lose
required evidence or resolvability, fail the structural citation floor, or no
longer save input tokens against v1. The legacy-v1 route is the comparison and
reproduction control, not a second normal operating mode.

#### Adopted v3 successor

`phase_a_evidence_packet_v3` supersedes v2 as the normal token-cost baseline.
The pre-bound adoption threshold was lower input tokens in every frozen case
and at least 10% aggregate reduction, because a smaller gain would not justify
a new schema generation and consumer surface. Across three alternating matched
repetitions of the same three Summer Fridays cases, using the same prompt,
output schema, `gpt-5.6-sol`, and low reasoning, v2 used 121,002, 85,173, and
72,341 input tokens; v3 used 99,225, 72,461, and 64,673. V3 reduced tokens in
every case by 17.997%, 14.925%, and 10.600%, and by 15.136% in aggregate
(278,516 to 236,359).

The saving is lossless transport normalization. The projector first builds v2,
then hoists only exactly repeated named values and serializes the remaining
values under explicit columns. A fail-closed preservation boundary rejects any
changed top-level payload, source-group evidence row, or proposition relation
before v3 can be returned or hashed. Focused tests deliberately removed one
relation and changed one engagement value; both failed at that boundary.
Identical input produced identical bytes and packet hashes.

All 18 model responses were structurally valid, used the correct proposition,
populated conditions, behavior, engagement, and uncertainty, and cited only
literal evidence or semantic-unit refs present in the supplied packet. The v2
and v3 packets preserved exact proposition IDs, admitted evidence IDs, and
semantic relation refs. Independent semantic adjudication was not run, so this
is a structural preservation and model-usability floor, not semantic
equivalence. Latency was non-gating; observed aggregate wall time was 3.013%
lower and cannot rescue or veto the token decision. Storage cost was not used.

The matched receipt is
`C:\tmp\forseti-phase-a-columnar-v3-success-test-20260816-v0\model_experiment_result_v1.json`
(raw SHA-256
`a1b0126f4eb950c30caf4bdb233723c0fcf1f0113b66679dcc03785916780697`).
Reverse to explicit v2 or revise v3 if a representative packet loses required
meaning or resolvability, produces an absent/invented cited ref, or fails to
save input tokens; a future independent semantic adjudication that finds
material output degradation also triggers reversal.

The column-interpretation residual was then tested on three withheld layouts:
an entirely unfamiliar seven-row fixture with unavailable engagement throughout,
a Birthday Cake proposition where one evidence item carried two relations, and
a three-source-group Pink Sugar conflict with heterogeneous engagement values.
Across three alternating repetitions per v2/v3 arm, both arms reconstructed all
30 requested rows and all 600 labeled fields exactly. V3 produced zero wrong-
column, wrong-row, formatting, missing/invented-reference, relation-integrity,
or synthesis-structure errors and used 180,671 input tokens versus v2's 187,885
(3.840% lower). This closes the observed model-readability concern and makes v3
the accepted token baseline for this lane. It remains same-vendor evidence, not
independent semantic adjudication. The receipt is
`C:\tmp\forseti-phase-a-columnar-v3-holdout-20260816-v0\holdout_experiment_result_v1.json`
(raw SHA-256
`d50aa9691d1ef51d5d92b977306e4648664339d3828b2d740bf5f176c26ba59b`).

#### Adopted decision-only related batching

Keep `phase_a_evidence_packet_v3` as the packet baseline. For downstream
consumption, run `prepare-evidence-consumer-batch` on the smallest group of
actually related cases: every multi-case batch must bind the same corpus and
bundle and share proposition-linked evidence. Do not combine unrelated cases
to manufacture savings. Non-related cases use singleton preparations. Send the
emitted prompt and response schema to the external fresh-agent call, then pass
the response and hash-bound manifest to `finalize-evidence-consumer-batch`.
The repository runner still makes zero model API calls.

The model response owns only the synthesis judgment and literal support and
counter refs. Finalization reattaches exact source facts from v3 and rejects
case/proposition cardinality or order changes, foreign refs, malformed or
missing engagement, failed lookups, and wrong row/column attachments. Packet
content, unresolved/unmerged material, adjacent relations, provenance,
identity, dates, conditions, uncertainty, causal ceiling, and bundle-backed
full-body resolution remain source-owned rather than model-repeated.

The pre-bound six-family experiment used three alternating repetitions per arm
with `gpt-5.6-sol` at low reasoning. The current v3 full-response baseline was
394,189 input plus 42,120 output = 436,309 logical tokens (28,160 cached input;
2,504 reasoning-output subset). Unbatched decision-only control was 382,056 +
16,464 = 398,520 (95,488 cached; 901 reasoning subset). The smallest finalist
batched only the overlapping broad-adverse and burning-conflict cases, leaving
four singleton cases: 332,493 + 14,735 = 347,228 (33,024 cached; 764 reasoning
subset). Calls fell from 18 to 15. The finalist saved 20.417% versus v3 and
12.871% versus unbatched decision-only, without subtracting cached tokens or
double-counting reasoning.

Finalist and unbatched control artifacts were 18/18 exact. The finalist had
zero missing/invented refs, attachment or semantic-relation failures,
cross-proposition contamination, or `public_identity_key` errors; deterministic
rehydration was idempotent. Shuffled order, duplicate proposition, missing
result, foreign in-batch ref, cross-batch ref, and another proposition's
judgment each failed at the intended deterministic boundary. Baseline remained
15/18 exact, so its copy errors were not credited as candidate savings.

Accepted residuals: provider prefix caching varied and is not a logical-token
claim; latency and storage were non-gating; the model check used one vendor and
structural artifact validation rather than independent semantic adjudication;
and only the measured smallest shared-context pair earns multi-case adoption.
Reverse to unbatched decision-only responses if a representative related batch
fails exact reconstruction, contamination/failure-boundary tests, the 1%
per-family regression tolerance, or the 10% matched aggregate logical-token
gate. Reverse the whole consumer successor to the v3 full-response baseline if
deterministic rehydration cannot preserve the complete consumer artifact.

The matched experiment result is
`C:\tmp\forseti-phase-a-related-batching-20260817-v0\experiment_result_v1.json`.

#### Optional evidence selection and exact quotes

When the complete proposition-linked view is too coarse for commercially
useful presentation, bind one narrow evidence point and use the existing
no-provider evidence-consumer's
`prepare-evidence-selection`, `finalize-evidence-selection-relations`, and
`finalize-evidence-selection-quotes` operations. This is a consumer view over
hash-bound `phase_a_evidence_packet_v3`; it is not packet v4, a semantic replay,
or a second evidence authority.

Admission uses explicit product plus axis membership, with literal nominated
semantic or unresolved refs for bounded non-axis cases. A nomination that
cannot resolve fails closed instead of disappearing. The external relation
response must account for every admitted candidate before deterministic
presentation selection. For non-value work, its provider-visible envelope is a
named columnar semantic view: bounded meaning, conditions, polarity,
product/version scope, source role/layer, uncertainty, existing relations, and
compact same-evidence meanings. Dates, engagement, URLs, evidence identity, and
provenance remain in the hash-bound candidate inventory and are reattached
deterministically; omitting them from the prompt must never omit them from the
artifact. Value-only relation work retains the full candidate view because the
bounded commercial pilot found that compacting those 12 rows could weaken
`repeated purchasing despite price` into a generic value label. Each candidate
carries the other normalized meanings
from that same evidence item as context only, so a price complaint cannot hide
same-source purchase or repurchase intent. For value work, bind `price feels
high` separately from `not worth it`, and nominate an evidence item that records
purchase, repurchase, switching, return, or abandonment under the existing
`costly_behavior` protection when that behavior changes the commercial reading.
Candidate admission remains direction-neutral: admit the relevant positive and
negative value evidence before assigning claim-relative support or counter.
For a selection whose only axis is `value_and_quantity`, the external relation
response uses the value-box reason-code vocabulary emitted in its response
schema. Support or counter requires the candidate's own meaning to state a
price, value, quantity-for-price, purchase commitment, repurchase, or
benefit-for-cost tradeoff. Same-evidence companions may qualify a direct value
premise — for example, repurchase despite price discomfort — but a gift card,
single-variant trial, formula, hydration, scent, or generic purchase statement
does not become value evidence merely because another meaning from the post is
negative. Such rows stay adjacent and remain in the disposition inventory. Do
not search for complaints first and then treat the surviving set as the answer.
A relation label describes how the row bears on the bounded claim; it is not a
permanent positive/negative label. Thus purchase or repurchase despite price
discomfort may be presented as a positive willingness-to-pay or value signal.
When the evidence shows purchase, repeated ownership, or repurchase without an
explicit price premise, use the corresponding plain behavior label rather than
inventing "despite price"; likewise, quantity efficiency without an explicit
price judgment is labeled "a little product goes a long way," not "worth the
price."

Keep atomic semantic meanings and their refs separately recorded. In the
presentation layer, meanings from the same evidence item may be grouped when
they have the same actor, action, direction, and conditions. For example,
separate shade meanings may display as “intends to repurchase Vanilla and
Vanilla Beige” while both semantic refs and named shades remain underneath one
origin and one exact quote. Never group across origins, hide a conflicting
clause, or broaden a shade-specific behavior into general repurchase.
The cap applies to displayed independent-origin groups. The default is thirteen
customer truth groups per bounded evidence point, and one selection may
explicitly raise that customer cap to at most twenty when protected evidence or
a material conflict cannot fit; creator influence remains capped separately at
three. Do not use one broad axis as the point merely to obtain one large pack.
Do not raise the cap merely to make an output look comprehensive. A full-axis
Summer Fridays hydration comparison found ten materially thinner, fifteen
materially better, and twenty no better than fifteen under mirrored review, so
that exact full-axis hydration selection uses fifteen. This is a measured
selection setting, not a universal default for every axis. Source
roles and retailer venues remain visible, with each publisher normalized to one
venue across host variants and short links; creator-authored popularity never
corroborates customer experience. Engagement may prioritize rows only inside
one venue/role/native-metric bucket, and a count the runtime cannot read whole
is ordered last rather than partially parsed. An unrecognized mapping-valued
engagement shape fails closed rather than becoming an unknown value or generic
score. Every nominated safety or costly-behavior origin is selected first; more
such customer origins than the selection's bound cap fails
`presentation_cap_insufficient`, as does a protected set that fits the cap only
until the support and counter lanes are reserved. For
non-value selections, the selector then reserves visible support and counter
only from materially positive or explicitly protected evidence. A value-only
selection instead fills materially positive support origins first, prioritizing
purchase and repurchase behavior before other direct value meanings, while
still round-robining source-native venue/role/metric buckets. Before that
round-robin fills the remaining places, it anchors one primary positive origin
by value-signal kind: purchase and repurchase behavior outrank explicit worth,
which outranks price-to-quantity meanings. Stable source bucket identity breaks
cross-venue ties; native engagement ranks only within the already fixed bucket.
It may add at most one ordinary counter from that anchor's same
venue/role/native-metric bucket, ranked by that native engagement value. If no
positive support exists, it still shows one materially positive complaint: the
strongest native-engagement complaint from the complaint bucket chosen by the
same semantic-first, stable-bucket rule. If the comparable bucket has no direct
counter, it displays none. An already visible operator-protected counter
suppresses the ordinary counter, and at the cap an ordinary counter may displace
the most recently added ordinary support origin but never the anchor.
Operator-protected safety or costly-behavior rows remain mandatory. This does
not compare raw engagement across platforms or create a commercial-pull score.
Unprotected zero, quiet, and
engagement-unavailable rows stay in the complete disposition inventory but are
not forced into the main presentation merely to fill a lane or venue. If no
materially positive or protected counter exists, the main presentation carries
no counter rather than manufacturing one from weak response. Each protected
group records its required display lanes, and the deterministic minimum member
rows needed to cover them are shown; one origin may therefore display multiple
rows. Every operator-protected row is visible or the run fails. The retained
disposition inventory remains the accounting record for all other displayed and
undisplayed candidates.

One displayed pack is one bounded evidence point, not one broad axis. It may
contain up to the selection's explicit customer-origin cap, and one origin may display several atomic
meanings. Call those origins corroboration only when their meanings support the
same bounded statement under compatible product, variant, timing, and
condition scope. Origins that merely discuss the same broad axis remain
separate evidence, not an inflated corroboration count. A source reporting
another person's experience remains adjacent unless the directly quoted
speaker's own account is the evidence unit. Internal independence metadata is
kept for deterministic origin accounting rather than used by the relation
model to discard otherwise valid evidence.

For large non-value selections, use `prepare-evidence-selection-batches` and
`finalize-evidence-selection-batches` instead of asking one response to repeat
every candidate ID. The preparation emits at most 300 candidates per batch and
uses required named row slots (`row_0000`, `row_0001`, and so on) plus a
required single-valued `batch_id`. The provider returns that `batch_id` and the
relation for each slot. Row slots restart at `row_0000` in every batch, so
`batch_id` is what stops one batch's response from answering another: keep it,
or a response saved under the wrong name finalizes with complete-looking
coverage and systematically wrong relations. Finalization binds each slot back
to the hash-owned candidate identity, rejects a missing, foreign, or wrong-batch
response and a missing or foreign slot, requires exact contiguous coverage of
the complete candidate inventory, then continues through the ordinary quote
manifest. Only the batch responses named in the batch manifest are read; any
other file left in the response directory is ignored, so clear the directory
between runs rather than relying on the finalizer to notice a stale file.
Batching does not change admission, selection priority, relation meaning,
evidence facts, or the origin cap. It does change the row label: a batched row's
reason code and display label are derived from its relation alone, so a batched
pack shows "Matching customer experience" or "Differing customer experience"
where the literal-ID path names the source meaning. Do not read a batched row
label as evidence meaning, and prefer literal-ID mode when the pack's row labels
matter to the reader. Literal-ID response mode remains the default and the
required mode for value selections; named positional batching is an opt-in
transport for large non-value axes. Its quote preparation emits
`phase_a_evidence_quote_manifest_v6`, which retains the v5 binding of the actual batch-manifest hash
and every canonical batch-response hash. The embedded selection manifest keeps
the canonical full selection identity; it is not evidence that its single large
prompt was sent. The v5 relation-transport binding records the prompts' actual
route.

The relation finalizer emits two independent provider workloads from the same
selected rows: exact-quote extraction and selected-row relation confirmation.
Run them concurrently when the provider route permits. The confirmation prompt
does not contain the first-pass relation, reason code, display label,
engagement, or selection priority. Its rows carry opaque `confirmation_row_id`
handles in a content-derived order rather than `selected_id` in selection
order, because selection order itself encodes the first pass: the protected and
reserved support/counter origins lead and the adjacent creator-influence block
always trails. The response must return every confirmation row exactly
once and in order; any missing, duplicate, foreign, reordered, or disagreeing
row blocks the final artifact. Finalization re-derives the confirmation
manifest from the bound quote manifest, so route the response back against the
manifest the harness wrote rather than a hand-assembled one. Do not combine
confirmation with quote extraction:
the bounded combined pilot classified all selected rows correctly but clipped
one exact quote mid-phrase. New v6 artifacts record the confirmation-manifest
hash and `passed`; historical v1/v3/v4/v5 artifacts remain readable under their
original contracts. Replay one by running
`finalize-evidence-selection-quotes` with neither `--confirmation-manifest` nor
`--confirmation-response`; supplying either fails closed.

The confirmation response also decides whether the supplied scope is one
specific direction-bearing proposition about one product attribute or outcome
under one compatible condition set. A claim that merely names an experience
area, or bundles materially different outcomes, directions, or conditions,
returns `broad_axis_or_bundle` and fails at `bounded_point_not_confirmed`. This
is part of the existing confirmation call, not a third provider task. Record
the passing reason on the artifact; the words `point_id` and `bounded_point`
alone never establish boundedness.

For a fresh point selection, exact linked parent text travels only with the
point's explicitly admitted semantic refs. It is deduplicated into a compact
parent-context table rather than repeated across the axis-wide candidate pool.
Every point-scope confirmation batch receives that same compact table so a
batch cannot decide scope from a context-stripped point. The table may clarify
the point, but it does not attach parent meaning to every evidence row: a row
may use parent content for its relation only through its own exact context ID.
Use it to resolve `same`, `this happened to me`, or another omitted referent
only when the parent itself names the same subject, attribute or outcome,
direction, and material condition. If the parent is merely a wishlist,
shopping question, broad discussion, or otherwise does not supply the missing
meaning, keep the terse row unresolved for that point. A source-native joined
experience such as becoming dry and cracked may remain one point; do not use
that allowance to join unrelated outcomes from separate sources. Historical
selection manifests without `linked_parent_context_v1` replay with their
original no-parent-context view.

Every completed v6 point pack discloses the funnel rather than presenting the
chosen rows as the whole corpus: candidate semantic rows, distinct candidate
evidence items, candidate truth origins, display-eligible truth origins,
displayed rows, displayed truth origins, displayed origins by relation, and
displayed creator-influence origins. Render those counts with the bounded
point. They describe evidence
accounting, not customer prevalence, and the full candidate-disposition
inventory remains attached. Do not read the candidate-to-displayed drop as cap
pressure: candidate truth origins are the admitted pool. The v6 quote manifest
records the truth selection policy, and the finalizer uses that exact policy to
count distinct origins eligible before the cap; an origin with no operator-
protected lane and no material positive source-native engagement is never
eligible, and value-first also excludes an otherwise material adjacent origin.
The artifact's `presentation_basis` names that gate, and also records that the
bounded point passed the separate scope classification; a broad axis or bundled
claim never reaches a completed point-pack disclosure.

For a whole-axis pack, thirteen is the maximum number of displayed distinct
truth origins **per bounded point**, not the size of the evidence corpus and not
an instruction to take the thirteen largest engagement values. The queue order
above first preserves the point's relation lanes and independent recurrence;
source-native engagement only breaks later ties inside a comparable venue,
role, and metric. Keep the completed point artifact's full
`candidate_dispositions`, `candidate_inventory_sha256`, selection-manifest
binding, and packet/bundle source pointers. The artifact therefore accounts for
every admitted semantic candidate while copying source bodies only for the
selected quote workload; a later operator can resolve an undisplayed candidate
through the bound packet and bundle rather than rerunning extraction.

Complete an axis as a set of independently finalized bounded-point artifacts.
Do not pad the set when a frontier proposition fails the existing
`point_scope` decision: retire that proposition with its literal failure reason
and report the smaller valid point count. A completed historical point may be
reused only as an immutable artifact under the exact policy revision and hashes
that produced it. If a staged historical manifest still needs quote completion,
either finish it with that exact historical consumer revision and disclose the
mixed lineage in the axis manifest, or rerun the whole point under the current
policy. Never make a current finalizer accept an old manifest by rebinding or
editing its hashes. An axis manifest references each point artifact path and
SHA-256, policy revision, exact selection-manifest path and stored/file hashes,
and quote-manifest path and stored/file hashes; it does not duplicate the point
artifacts' full candidate inventories. A sibling-file convention is not a
cold-reader source pointer.

The live repository route for any named Phase A axis is
`phase_a_evidence_axis_pack_manifest_v1` ->
`phase_a_evidence_axis_pack_v1`. Use
`forseti-harness/runners/run_phase_a_evidence_axis_consolidation.py
build-axis-pack --manifest <explicit-manifest.json> --output <new-axis-pack.json>`.
The manifest is a self-hashed JSON object with `axis_id`, nonempty
`accepted_points`, and explicit `rejected_points` (an empty list is allowed).
Every accepted point names its `point_id`, `bounded_point`, `policy_revision`,
point-artifact path/file SHA-256, selection-manifest path/file SHA-256/stored
manifest SHA-256, and quote-manifest path/file SHA-256/stored manifest SHA-256.
Do not infer any sibling file. The builder independently reopens those literal
paths, verifies point and axis identity, candidate closure, the normal
thirteen-truth-origin cap, selection and quote lineage, packet
v3 identity, content-bound bundle identity, and packet-to-bundle binding, then
derives rather than trusts the pack's point, relation, origin, evidence, and
candidate counts. Accepted and rejected point IDs are unique and disjoint.
`policy_revision` is a declared operator pin rather than verified lineage: it
is cross-checked only against a point artifact that carries its own
`policy_revision`, and the completed Phase A point artifacts do not carry one,
so no completed point currently exercises that check.

Truth-origin counts admit only `truth_support` rows. Other displayed layers,
such as creator influence, remain displayed origins and displayed rows but
never enter `truth_origin_count` or `unique_truth_origins_across_axis`.

Validate a saved generic pack with
`validate-axis-pack --pack <axis-pack.json> --expected-axis-pack-sha256 <trusted-stored-hash>`.
Then build `phase_a_evidence_axis_consolidated_view_v2` with the same runner's
existing `build --spec <consolidation-spec.json> --output <new-view.json>` route.
The `phase_a_evidence_axis_consolidation_spec_v2` spec explicitly pins the
generic pack path and raw file SHA-256, supplies presentation-only navigation
groups, and supplies `projection_routes`; both structures must cover every
accepted point exactly once. Navigation may group points for reading but cannot
merge propositions or grant evidence or relation authority. The v1 spec and
view remain accepted only so frozen historical artifacts rebuild without byte
or hash drift. Validate the saved view with `validate --view
<view.json> --expected-view-sha256 <trusted-stored-hash>`. Both writers refuse
overwrite, make zero provider calls, and reproduce identical output from
identical inputs.

Projection routing is point-level, not an axis-name allowlist. A model may
recommend the route while authoring the spec, but the declared spec is the
durable choice; the builder does not silently infer or change it. Use
`direct_outcome` when the point reports an attribute or experienced result,
such as hydration, drying, wear, texture, finish, scent, flavor, shade fit,
reaction, application, or comparator performance. Use `decision_state` when
the point reports an actor's judgment or action state, such as value judgment,
ownership, purchase, purchase intent, completed use, return, repurchase,
switching, recommendation, or abandonment. These are routing examples rather
than axis assignments: one named axis may contain points of both kinds.

The v2 builder implements both `direct_outcome` and `decision_state` at the
explicit point-level routing seam. Direct Outcome preserves the v1
origin-normalized, surface-separated projection and carries forward each
point's existing boundaries that the presentation is not a causal judgment,
not a commercial-pull score, and that creator influence is not customer
corroboration. Decision State instead compacts explicit spec-authored actor,
object, judgment/action-stage, direction, quantity, semantic-reference, and
qualification facts without inferring states from quotes, engagement, point
text, or axis names. Value is the first full frozen Decision State test
subject; this does not make its findings prevalent, causal, or representative
of other products or axes.

For price-and-value evidence, Phase A preserves the source-explicit ingredients
that a later judgment may need: price or cheaper-comparator friction,
value-at-price judgments, price-conditioned purchase or repurchase intent, and
observed purchase, use, return, switching, or repurchase behavior. When one
source carries several of these states, their shared placement remains visible.
Phase A does not add a `premium`, `pricing_power`, or `tier_potential` state or
classify the current product as premium. The packed evidence may later support
evaluation of whether an offer could be elevated or a higher tier introduced;
that potential and any resulting action remain downstream judgments rather than
evidence-pack facts.

Bind every emitted response schema through the provider's structured-output
mechanism (for local Codex CLI execution, `--output-schema`); including schema
wording in the prompt alone is insufficient. The finalizer must reject field
name drift, missing rows, and quote-boundary failures. A source-exact quote
shortened by an operator after such a failure is a disclosed corrected response,
not an unmodified provider result; prefer a bounded provider correction turn
and preserve every discarded-call cost either way.

The completed hydration-axis dogfood is the immutable completed example and
legacy compatibility input for this generic route. Its pack at
`C:\tmp\forseti-phase-a-hydration-axis-pack-20260822-v0\hydration_axis_pack_v2.json`
(raw SHA-256
`42f7fa0ca3c7d2000c77e97d37a429aa32c04c320aa2fa000a68b114acf9c77d`)
exercised this resume boundary. Nine completed points retained their historical
policy revision; two unresolved points were rerun under the current linked-parent
policy. The precise same-drying-and-cracking point passed, while “does nothing
for their lips” failed generically because it named no single material outcome;
the axis therefore contains ten valid points rather than eleven. Each valid
point accounts all 836 hydration candidates and displays thirteen
evidence-origin groups.
Across the axis that is 130 point-origin placements and 146 display rows, but
only 32 distinct origins and 37 distinct evidence items because one origin can
inform several precise points. The selected origins span Reddit, Amazon, and
Sephora; the artifact retains every undisplayed candidate disposition and its
source-resolution bindings. Exact-quote and attachment finalization passed for
all ten artifacts. The completion run used 1,095,340 logical tokens; 405,771 of
those belonged to ten discarded malformed calls caused by the initially
unbound structured-output schema and are not hidden as production success. Two
long-body quote responses were source-exactly shortened to complete sentence
boundaries after provider boundary failures and are disclosed as corrected
responses, not unmodified provider output. A cold-reader replay then loaded only
the v2 axis pointers, reverified each selection-manifest identity and candidate
inventory hash, resolved all ten bound packet/bundle sources, and matched all
8,360 point-candidate dispositions to their source-derived candidate IDs. Its
first local v1 index had named only artifact paths; requiring an inferred sibling
selection manifest was rejected as incomplete rather than reported as cold
resolvability.

Downstream consumers use generic completed axis packs through the live derived
`phase_a_evidence_axis_consolidated_view_v2`, built by
`forseti-harness/runners/run_phase_a_evidence_axis_consolidation.py`. This is a
presentation view, not a packet v4 and not another evidence authority. It
accepts `phase_a_evidence_axis_pack_v1` as the live input and retains
`phase_a_hydration_axis_pack_v2` only for immutable hydration compatibility. It
reverifies the exact axis, point, selection, quote, packet, and bundle bindings;
keeps all ten bounded points and every claim-relative placement; stores each of
the 32 origins, 37 evidence items, 56 quote records, and 181 companion meanings
once; and leaves all 8,360 candidate dispositions cold-resolvable through their
owning point artifacts. Three navigation groups make the axis readable without
merging its propositions: hydration efficacy, drying consequences, and
comparator performance. Balm Dotcom and Rhode remain separate bounded points,
and delayed drying/cracking remains separate from direct drying.

The view also separates Reddit posts from Reddit comments before presenting
source-native engagement. It does not normalize, percentile-rank, or compare a
post score with a comment score, retailer helpful count, another venue, or
another calendar-year bucket; undated engagement is explicitly non-comparable.
Repeated rows sharing one origin key remain one evidence-origin group, while
distinct actors in one thread remain distinct origins with that thread
concentration disclosed. The current axis has 32 evidence-origin groups: 30
carry `credited` independence posture and 2 carry `unavailable`; neither count
is a people or prevalence estimate. Each point carries its exact deterministic
support, counter, and adjacent origin lists directly as a consumer aid; those
lists are rederived from the preserved placements and cannot override them.
The point-level direct lists were added after the first compact dogfood made two
join errors while copying origin directions. That failed shape is negative
evidence and must not be restored merely to save more tokens.

The current trust-bound consolidation successor is at
`C:\tmp\forseti-phase-a-axis-consolidation-20260822-v0\consolidated_view_review_closed_v1.json`
(raw SHA-256
`e1845be89e8504fba4398de267639bdd431eef0d2eaeb5b94e7d8802eda87735`;
stored view SHA-256
`4a78b4ac7a5b00d0b1d454f1a32476946820d9000058ece08f1fa86a5142feb2`).
Its build spec is
`C:\tmp\forseti-phase-a-axis-consolidation-20260822-v0\consolidation_spec_v1.json`
(raw SHA-256
`f11f66a09f29113bfcfdc164afdc71b0d536e7ee0dcf1c9949461d18ea394490`).
Cold validation must receive the independently pinned stored view SHA through
`--expected-view-sha256`; copying the hash from the file under validation is not
a trust check. A wrong external pin rejects before reprojection. The zero-model
build completed in an observed 38.562 seconds, and a second build was
byte-identical. The predecessor v5 dogfood build completed in the receipt-bound
33.339 seconds. Its matched three-repetition receipt is
`C:\tmp\forseti-phase-a-axis-consolidation-20260822-v0\experiment_receipt_v1.json`
(raw SHA-256
`8f97a45de735dff2d62438e90f75cc6b1910878c91741b3d98f5b151ab4b75de`).
The completed ten-pack arm used 477,216 logical tokens; the consolidated arm
used 418,082, saving 59,134 logical tokens (12.391%) with lower provider input
in every repetition. The consolidated arm reproduced every point-relation
origin set in 3 of 3 repetitions; the ten-pack arm did so in 2 of 3. An opaque
same-vendor judge preferred the consolidated synthesis in all three primary and
all three mirrored comparisons, with zero material-quality failures and stable
ordering. Measured serial elapsed time was 547.708 seconds for the ten-pack and
494.333 seconds for the consolidated view, a descriptive 53.375-second
(9.745%) reduction rather than a latency guarantee or p95 claim. Cached input
is reported but never subtracted, and reasoning output is a subset of output,
never added twice. Those provider measurements belong to v5. The review-closed
successor
preserves every navigation group, point placement, relation, evidence fact,
quote, and companion meaning while adding the explicit 30/2 independence split
and denying comparison for undated engagement. No provider rerun was used to
pretend those metadata corrections were newly measured quality or latency. Its
same fixed prompt projects to 362,501 UTF-8 bytes versus the ten-pack's 501,073,
a static 27.655% reduction; logical-token and latency deltas remain the v5
measurements above.

That trust-bound file remains a frozen v1 artifact and is not rewritten by the
live v2 route. Its results establish the Direct Outcome predecessor evidence;
they do not themselves validate Decision State. The separate frozen value-axis
pilot exercises Decision State while preserving this Direct Outcome and v1
compatibility boundary.

The completed production evidence still proves one hydration axis only. The
generic builder's deterministic two-point fixtures prove schema and parity
behavior, not another product or axis. This route does not change the
thirteen-origin selector, point relations, packet v3, or turn displayed origins
into prevalence. Reverse to the
ten-point source artifacts if deterministic reprojection loses any point,
relation, condition, comparator, quote, source binding, or cold candidate
access; if a representative cold consumer inflates origins or changes a
direction; or if matched logical-token savings fall below ten percent without
a position-stable material quality gain.

The bounded v6 dogfood receipt is
`C:\tmp\forseti-phase-a-point-pack-v6-dogfood-20260821-v0\dogfood_receipt_v1.json`
(raw SHA-256
`6113212dfd6d3b755e3d382dd7d00536c92719e797a48d1263557a13a9bfe8ea`).
It reused the accepted historical fifteen-origin broad hydration selection only
to exercise the new confirmation and finalization boundary. A different model
family from the same vendor confirmed all 17 displayed rows, including the
known 922-point Reddit row as support, with zero disagreements. The call used
20,335 input plus 566 output logical tokens and completed in approximately 17
seconds. This is not cross-vendor adjudication and does not prove the new
thirteen-origin point default; deterministic runtime tests own that default.

The full-axis hydration receipt is
`C:\tmp\forseti-phase-a-hydration-cap-pilot-20260820-v0\experiment_result_v1.json`
(raw SHA-256
`74149af3d24c8ba742d38ec75bb9e5e2bd075570fd29d68f31189d143608b2e9`).
Its accepted route accounted for all 836 candidates and selected fifteen
customer origins into seventeen exact-quote rows across Reddit, Amazon, and
Sephora. Ten of those origins carry a support row and six carry a counter row;
two origins carry both, which is why the per-relation counts exceed fifteen.
Required named slots fixed the observed long-array truncation, but increased
relation-stage logical tokens by 35.092% versus the exact literal-ID arm. The
batched arm's measured serial provider wall time was higher than the literal-ID
arm's, and the production route itself ran serially; the 51.736% latency
reduction is the modelled parallel critical path, available only if the batches
are actually issued concurrently. This is a completeness trade with a
conditional parallel-latency upside, never a token saving.

Read that receipt's own residuals with its numbers, because they qualify the cap
decision and are recorded nowhere else: the provider and the mirrored judge were
the same vendor; the mirrored named-versus-prior pack comparison was
position-unstable and therefore inconclusive; the packet supplies no TikTok
audience evidence for this selection; the provider calls used high reasoning, so
lower-effort behavior is unmeasured; and the receipt records
`repository_head_at_run` as the parent commit with a dirty worktree, so it
attests to the run, not to a committed revision.

The post-review final-contract proof is
`C:\tmp\forseti-phase-a-hydration-final-contract-20260820-v0\experiment_result_v1.json`
(raw SHA-256
`dc9420c0a43e07fa6df66b1b45b8a193759f6908b2ba7ac8c4b7fbc117c6dde3`).
It ran fresh matched high-reasoning serial and genuinely concurrent arms over
the same 836 candidates, then regenerated the final prompts and manifests from
the committed implementation byte-for-byte. Both arms produced fifteen truth
origins, seventeen exact quotes, zero unavailable quotes, and no influence
origin. Serial used 248,014 logical tokens and 742,019.840 ms of active provider
time; parallel used 245,176 logical tokens and 389,626.940 ms. The observed
parallel latency reduction was 47.491%. The 1.144% lower parallel logical-token
total is descriptive provider-output variation, not a concurrency token-saving
claim. Both mirrored blind orderings preferred the corrected parallel artifact
to the prior accepted pack. The receipt separately discloses 408,351 logical
tokens across twelve rejected-attempt and judge calls; those are experiment
overhead, not production-arm economics. The receipt's `payload_sha256` is
sha256 over insertion-order compact JSON of the payload, not the repository's
sorted-key `_canonical_json_sha256`; re-derive it that way or a correct receipt
reads as tampered.

The cross-vendor review of that proof measured three facts the arm totals above
do not show, and they are carried here rather than left to the receipt's single
"changed one selected origin" sentence.

First, the two arms disagreed on the relation label for 56 of 836 candidates
(6.7%) despite byte-identical relation prompts and schemas, including eight
direct support/counter polarity flips. One flip reached the displayed pack:
`reddit:1apzs1v:post::batch-0463-unit-0002` carries an identical normalized
meaning and an identical exact quote in both arms, shown as "Matching customer
experience" in the parallel arm and "Differing customer experience" in the
serial arm. Nothing deterministic can detect this, because in positional mode
the reason code is derived from the returned relation and therefore always
agrees with it. Relation labeling, not origin selection, is the least stable
part of this pipeline; treat a repeated selection as evidence of transport
identity, never of relation stability. The measured parallel pack remains the
accepted historical artifact for this hydration workload. New v6 point packs
close the observed display boundary with the separate selected-row confirmation
described above without relabeling the complete candidate set.

Second, `seventeen exact quotes, zero unavailable` counts exactness and
availability, which deterministic code already enforces. It is not a measure of
the context-completeness the v51 contract requires. Measured against that rule,
the final one-call prompt returned 13 of 13 conforming long-body spans in the
parallel arm and 10 of 13 in the serial arm: three serial spans stop mid-phrase
(`…pricey lip balms in`, `…better in this bitter`, `…the very cold winter`), and
the second of those also drops the "bitter cold" condition its own normalized
meaning names. The 220-character ceiling can make start-completeness and
component-completeness jointly unsatisfiable — that same Amazon row needs 222
characters to keep both — and the contract states no precedence, so the adopted
parallel span resolves it by beginning headless (`have tried glossy products…`).

Third, both mirrored judges preferred the parallel artifact, but a blind
preference does not waive an objective omission. The reformulation span omits
the reviewer's explicit recommendation; that is a genuine ceiling residual,
because carrying both the old-formula baseline and the recommendation needs 312
characters. The judge also flagged a Pink Sugar color clause that would fit at
204 characters, but home adjudication did not accept that as a hydration defect:
the color remark neither qualifies nor reverses “feels hydrating and
comfortable,” and forcing it into this axis would add off-axis detail. This
shows that the judge rubric was broader than the contract's materiality rule.
Note also that the judges compared the parallel arm to the prior accepted pack,
never to the serial arm; the choice of parallel over serial rests on measured
latency, not on adjudicated quality.

Of the 47.491% observed latency reduction, 46.528 points are attributable to
concurrency and 0.963 points to net per-call provider variance; concurrency
accounts for 98% of the saving, and the residual variance is why the figure is
reported as observed rather than as a concurrency guarantee.

The quote stage reads bodies only for selected display rows. Bodies of at most
220 characters are copied in full by deterministic code, and absent bodies are
typed unavailable; neither is sent to the model. Only longer bodies enter the
provider prompt. That prompt uses named selected-row and deduplicated body
columns, so several meanings from one source body do not repeat the entire
body. It carries the deterministic display label, normalized meaning, and
same-evidence companion meanings. The label is presentation metadata only: a
returned long-source substring must directly express the normalized meaning or
a material companion qualification, or be `quote_unavailable`; a generic
batched relation label cannot make an irrelevant substring acceptable. An
exact span must not start with an unresolved pronoun when nearby preceding text
names its antecedent and the combined span fits. Product identity may still
come from the evidence row; the pronoun rule does not require every otherwise
relevant quote to repeat it. The quote is context-complete rather than merely
short: it must substantiate every material outcome, direction, comparator,
formula distinction, and usage or timing condition in the normalized meaning,
retain a nearby material qualification, and never stop mid-phrase. It may
return unavailable only after checking that no one span within 220 characters
supports the complete normalized meaning; optional non-reversing context need
not fit. An
available source body of at most 220 characters must be quoted in full, so a
short comment cannot
be clipped before a material qualification or same-source costly behavior. For
a longer body, it accepts one context-complete contiguous exact substring of at
most 220 characters after packet and bundle
content verification and evidence-ID, artifact-ID, and source-ref verification,
and rejects a body that changed after the quote manifest was written. When a
material qualification cannot fit, the quote response returns unavailable
rather than a misleading fragment. It never repairs text or adds ellipses. An
available quote must contain at least two
Unicode alphanumeric characters; no lexical-overlap relevance rule is applied.
A long-body quote in a current v4/v5/v6/v7 quote manifest that ends in an alphanumeric
character while the bound source continues with whitespace and another
alphanumeric character fails at
`quote_boundary_incomplete`. This catches a literal substring that stops before
its next source word; it adds no provider retry and makes the incomplete result
visible instead of publishing it.
A `quote_unavailable` row carries `source_body_present` and a deterministic
cause: `source_body_unavailable` when the body is absent, or
`no_relevant_exact_quote_returned` when a present body yielded no quote.
Available quotes carry a null cause, and the normalized meaning remains in every
case. The completed artifact retains every candidate disposition
and the full candidate-inventory hash, including Amazon or Revolve rows that did
not earn a display slot. Repository runners emit prompts and schemas but make
zero provider calls.

Preserve the source publication time beside every evidence row when the source
exposes it. Current semantic-source builders carry Reddit post/comment
timestamps, Sephora submission times, Amazon review dates, and Revolve review
creation times into packet v3. A completed packet with a missing time may be
rehydrated only from the exact source artifact and SHA-256 already bound by its
bundle; unavailable or unsupported legacy bytes leave the time unavailable and
changed bytes fail.
The date enables later descriptive alignment with search trends but does not
establish that either signal caused the other.

New frontier-bound point packs use `phase_a_evidence_quote_manifest_v7`; the
non-frontier relation and batched routes still produce `v6`. Both record the
ordered `provider_selected_ids` subset. The finalizer recomputes that subset
from the bound bodies, rejects drift, deterministically fills short or missing
bodies, and merges provider-returned long-body quotes back into original
selection order. Every selected row requires one customer-facing
`display_label` of at most 80 characters plus
the exact quote; do not add a second paraphrased sentence. The finalizer derives
the label from the already-validated relation `reason_code`; the quote response
returns only quote identity, status, and exact text. The label names the evidence
signal, not its internal relation to the bounded claim. Value examples
include `Repurchase intent despite price`, `Product appeal outweighs price
concern`, `Explicitly worth the price`, `Strong price-to-quantity value`, `Too
little product for the price`, `Performance does not justify the price`, and
`Price prevents repurchase`. A malformed, overlong, or
support/counter/adjacent/exclude-leaking reason code fails closed before display.
V7 also binds the completed pre-selection relation confirmation and requires no
late confirmation attachment during quote finalization. Historical v6 keeps
its selected-row confirmation attachment; legacy v1 and v3 quote manifests keep
their original all-selected response shape and remain finalizable. The
superseded v2 presentation-statement experiment was scratch-only and is not a
supported historical runtime contract.

Regression note: the exact short comment “Do I cringe a little every time I
remember the price tag? Yes. Will I be repurchasing vanilla AND vanilla beige?
Also yes.” must remain one context-complete quote. The exact comment “They are
kind of expensive for what they are, but the packaging is just so cute I can't
not.” likewise carries price resistance and purchase behavior together. In
both cases, extracting only the price clause reverses or materially weakens the
commercial reading. Weak zero-engagement complaints remain accounted but do
not displace a materially engaged or protected counter merely to fill a lane.
Likewise, a stated time to finish or pan a product is completed-use context, not
quantity efficiency or good value by itself. When the same source explicitly
says it will buy again, package the exact repurchase statement as repurchase
intent and retain the completed-use meaning as same-source context.
The 599-score Strawberry-duo post is the opposite regression shape: its source
body reports a thinner, less-moisturizing formula, disliked scent, and a final
warning not to buy, but its admitted value-axis meanings are gift-card purchase
and trying one variant. Those meanings do not directly judge value, so the post
must remain adjacent to the value box even though it remains useful evidence for
formula, hydration, scent, and general purchase-warning work.

## Evidence-family boundary

- Reddit/community and retailer reviews are customer evidence and may be
  reconciled here.
- Creator-audience comments may join only when their capture envelope and
  customer role are independently established.
- Owned pages, Meta ads, Google Ads Transparency, and creator-authored campaign
  material remain company-side evidence. They may later be compared with
  customer evidence in a claim-to-response bridge, but they do not corroborate
  a customer experience merely by repeating the same language.
- Campaign conclusions and recommendations belong downstream, not in this
  Phase A structure.

## Proof sequence and current boundary

1. Complete a real bounded cross-source product/axis proof with all selected
   leaves accounted and deterministic wrong-product controls.
2. Freeze and independently review the product binding, semantic method,
   validators, and proof receipt.
3. Prove catalog reach on a real empty-candidate or mixed-product Reddit leaf
   plus retailer evidence, then independently review the runtime change.
4. Bind the final execution route, then run its hash-pinned bounded semantic
   calibration before assigning any remaining full-corpus work. Calibration
   must include a production-shaped work unit, blind atomic gold, selective
   cold repeats, and final-view cross-source obligations; a failure or blocker
   keeps the corpus paused.
5. Only after calibration passes, give cold agents the full assessable Reddit
   and retailer corpus and require exact per-leaf accounting through terminal
   reconciliation and evidence-packet projection.
6. Adopt the current method into a seal-bearing route only through an explicit later
   route revision. A bounded or full shadow run does not rewrite Route 1.6 or
   1.7 obligations.
7. Only after the customer corpus is complete, integrated, reproducible, and
   cold-agent proven should the separate campaign/customer bridge be handed
   off.

As of 2026-08-09, the bounded 300-leaf Summer Fridays proof and the later
four-leaf catalog-reach shadow proof are complete. The latter observed two
empty-candidate Reddit leaves receiving the verified Lip Butter Balm identity
and one real Reddit-plus-Sephora wear stack, while preserving 18
non-equivalent units as unmerged. The first different-vendor pass has been
adjudicated and its material findings closed; a clean closure pass remains due
because the commissioned code-review method was unavailable to that receiver.
The 59,225-leaf full-corpus semantic completion and terminal convergence remain
later observed work, not a current claim.

The run-v3 / bundle-v5 / method-v5 generation is implemented and covered by
repository fixtures and unit tests only. Its structural accounting, version
compatibility, raw-occurrence validation, expansion, lineage, and status
behavior are proven at repository scale; its latency, token, and full-corpus
compatibility effects are not. No measurement against the paused full run's
frozen artifacts has been performed, so the generation carries no latency
claim, no token claim, no full-corpus execution readiness, and no
run-resumption authority. Method v5 has not been semantically calibrated: its
four-way boundary is proven as instructions and routing structure, never as
model recall.

As of 2026-08-10, contract v20 and the no-provider runner implement the bounded
calibration gate. The latest completed Summer Fridays dogfood was v18: 13 of 17
gold cases passed, six of seven selective cold repeats were consistent, all
seven relation obligations passed, and no anomaly warning fired. Four critical
cases still failed through over-splitting, localized unsupported axes, an
inflated contextual favorite, and loss of the bounded ownership-plus-go-to
meaning. The 121-row production-shaped response expanded from 179 v17 units to
260 v18 units, while 235 non-gold units remained outside adjudication-v3's
per-unit checks. This triggers the calibration design's route-change condition:
do not keep accreting prompt examples; test a smaller complexity-balanced
production work-unit shape under unchanged v18 semantics. V18 does not
authorize corpus resumption, estimate defect prevalence, or change the
still-incomplete full-corpus boundary above.

The follow-up v19 architecture probe kept v18 semantic wording and blind gold
unchanged, packed the same 121-row production carrier into near-balanced 61-row
and 60-row prompts, and applied spec v3's compilation-bound audit to the ten
highest-unit-density non-gold rows. Its hash-bound report is
`SEMANTIC_CALIBRATION_FAIL`: 11 of 17 gold cases passed, all seven cold repeats
were materially consistent, and three of ten audited non-gold rows contained
confirmed unsupported or over-split meanings. The split emitted 289 production
units, up from v18's 260. Core and production reconciliation also independently
failed finalization after community evidence was promoted to
`observable_fact`, so no final views existed and all seven relation obligations
remained blocked rather than adjudicated satisfied.

This fires the architecture-probe stop condition. Do not add another prompt
example, delegate a post-pass patch review, resume the 561-prompt corpus, or
claim route readiness from v19. The next decision belongs to selective
verification or a changed execution route that addresses semantic instability
and final-view claim-kind competence; v19 is evidence for that decision, not
authority to implement it.

The bounded v20 direction-adjudication replay isolates one v19 measurement
error without reopening that stop. Contract wording and the generated
adjudication sidecar now distinguish a directly asserted lower comparison
(`A is less moisturising than B`, `affirmed`) from logical negation (`A is not
as moisturising as B`, `negated`). Three fresh read-only adjudications produced
the same 13-of-13 results across five v19 lower comparisons, matched clean
controls, a reversed comparator, a contradicted negation, and a polarity
conflict; those three adjudications were not frozen as durable artifacts, so
that 13-of-13 result is reported, not independently checkable. Re-evaluating
the frozen v19 responses with only the five affected per-unit judgments
corrected removed all five direction failures and raised gold passage from 11
of 17 to 14 of 17. That corrected re-evaluation edited five recorded judgments
rather than re-adjudicating under the generated sidecar, so it measures the
direction rule, not the sidecar's effect on an adjudicator. The result remains
`SEMANTIC_CALIBRATION_FAIL`: three unrelated gold cases still fail, three of
the ten density-audit rows remain confirmed defects, no final views exist, and
all seven relationship obligations remain blocked. This replay is bounded
same-provider evidence, not independent cross-vendor review, prevalence,
readiness, or authority to resume the 561-prompt corpus.

The subsequent architecture adjudication withdrew the proposed polarity
removal and selective whole-row verifier. The five v19 lower-comparison gold
units at issue already used `affirmed` polarity, while the calibration
adjudications disagreed about their direction. The architecture review also
measured the proposed structural selector as nominating at least 73 of 92
claim-bearing
production rows (at least 79.3%) before all candidate triggers were applied,
so it was a near-full reread rather than a selective route. The 92-row
claim-bearing denominator is checkable in the frozen v19 compilation; the
73-row nomination count was not frozen as a durable artifact, so it is
reported, not independently checkable. The retained provisional architecture is
one-pass extraction, deterministic validation, reconciliation-time
source-role/claim-kind competence enforcement, and finalization.

A fresh bounded v20 adjudication-and-reconciliation replay at
`C:\tmp\forseti-summer-fridays-semantic-calibration-v20-replay-20260810-v0`
then exercised that retained route rather than editing v19 judgments. It used
the frozen v19 preparation rather than new v20 extraction prompts, reusing the
preparation identity
`4067e7c51e31ffaf35e51874705a471044833ec506813aa08b0d0699e108531f`,
carried the integrity-checked v20 adjudication sidecar, and used four blind
extraction work units plus crossed and fresh reconciliation readers. The run
made zero model API calls and did not touch the 561-prompt corpus. All judgment
readers were OpenAI-family agents, so this is fresh role separation rather than
cross-vendor semantic proof. Reader blindness, reader crossing, vendor family,
and the zero-API-call condition are operator-reported: replay artifacts do not
record reader identity, reader role, or API-use provenance, so those
operational facts are not independently checkable.

The fresh report remains `SEMANTIC_CALIBRATION_FAIL`. It produced 234 primary
semantic units, of which 205 came from the production slice, down from v19's
289 on that same slice; it completed both terminal views, passed 11 of 17 gold
cases, held four of seven cold repeats consistent, satisfied four of seven
relationship obligations, and confirmed two of ten density-audit rows as
defective. All fifty adjudicated statement-direction checks passed, so the five
v19 lower-comparison failures did not recur. The remaining failures are real
and different: unsupported reaction or shade axes, missed narrow preference,
ownership, and go-to atoms, three cold-repeat inconsistencies, and three broken
cross-evidence relationships. The report is bound by
`report_sha256: 36ca06321f537fc12d1b464eb6bc42dfc0711f99f7f107c6219422f6cb8e2a25`;
the observed preparation-to-report wall time was 36.7 minutes.

This fresh replay supersedes the edited 14-of-17 result as the current behavior
observation; it does not erase that earlier direction-rule measurement. Keep
the full corpus paused. The next semantic change, if any, must target a
reproduced remaining defect class and preserve matched clean controls; this
run supplies no authority for a universal second read, polarity redesign,
prompt-example accretion, readiness, prevalence, or corpus resumption.

The method-v6 controlled replay at
`C:\tmp\forseti-summer-fridays-semantic-calibration-v21-replay-20260810-v1`
then exercised the smallest meaning-preservation correction on the same real
calibration carrier: seven semantic-core leaves, 121 production-shaped leaves,
seven selective cold repeats, and both terminal reconciliation views. It kept
the bundle-v5 transport and all downstream schemas unchanged. It corrected the
observed healed-peeling axis, named-shade axis, causal preference reason,
connected ownership-plus-go-to meaning, omitted ownership, sensitive-lip
condition leakage, advertised-balm value, and two surrounding density-audit
defects. It also preserved non-drying as bounded hydration evidence and kept
experienced category separate from value.

The resulting report is `SEMANTIC_CALIBRATION_PASS`: 17 of 17 gold cases, all
seven selective repeats, all seven relationship obligations, and all ten
production density-audit rows passed with zero blockers and zero hard failures.
The report is bound by
`report_sha256: 414c961fc13fc41de971ee2dca925ff2534cdc19cb06ef6222b17030ef3c02c9`.
All 128 primary leaves remained exactly accounted, terminal views completed,
and no model API was called.

This is a controlled replay, not fresh-reader semantic proof. The v20 response
corpus was the baseline and the affected meanings were corrected under method
v6 before recompilation; cold-repeat uncertainty was also reconciled by the
same operator. The result proves that the new general rules, existing schemas,
compiler, reconciliation, evidence retrieval, and calibration gates can carry
the intended meanings without contradiction. It does not prove that an
independent cold reader will apply the v6 wording unaided, estimate corpus
prevalence, authorize the full-corpus run, or make the route seal-ready. Keep
the full corpus paused until the code change receives de-correlated review and
a fresh blind v6 reader reproduces the bounded result or exposes the next real
defect class.

The delegated v6 code review then found a real ambiguity in those instructions:
the retained v5 rule forbade bundled mixed directions while the v6 appendix
said to keep every explicit contrast together. Home adjudication accepted that
finding and the delegate's method-hash pin. It clarified that contrast and
qualification still obey atomicity, corrected the stale bundle-v5 error text,
and documented that calibration may deliberately retarget the same hash-pinned
source evidence to the spec-selected method; the exact method hash in the route
fingerprint makes that a visible comparison, not a fallback.

Fresh blind dogfood did not reproduce the controlled pass. The first corrected
read at
`C:\tmp\forseti-summer-fridays-semantic-calibration-v21-review-fix-20260810-v3`
accounted all 128 primary leaves, completed both terminal views, and satisfied
all seven cross-source relations, but passed only 14 of 17 gold cases and five
of seven cold repeats. It exposed missing same-attribute comparison, shade-axis,
texture-versus-formula, exact-product nickname, and logical-negation behavior.
A compact general correction addressed those classes without adding a field,
second read, product phrase table, or extra production-shaped prompt.

The resulting fresh blind run at
`C:\tmp\forseti-summer-fridays-semantic-calibration-v21-review-fix-20260810-v4`
again accounted 7/7 semantic-core and 121/121 production-shaped leaves, used
the original two production prompts (largest 89,904 bytes), completed terminal
reconciliation, and satisfied all seven relation obligations. It passed 16 of
17 gold cases, four of seven cold repeats, and seven of ten density audits. The
one remaining gold failure split weeks-long peeling from repeated-use worsening
instead of preserving their causal relationship. The cold repeat also
over-decomposed two dense rows and miscredited one reported deterrent; three
other dense production rows retained polarity or comparison defects. The
evaluator therefore returned `SEMANTIC_CALIBRATION_FAIL`, with report hash
`74009baaedadc3e5e170012586b383179f2d1b60664bc211015187321f0e1ae3`.

This is useful negative proof: the compact general rules corrected all five
defect classes they targeted, but one-pass prompt wording alone has not produced
stable calibration behavior. Do not resume the full corpus, claim method-v6
readiness, or keep accreting case-like prompt clauses. The next decision must
address selective semantic verification or another bounded consistency
mechanism against these preserved fresh failures; it remains separate from any
campaign bridge, Deliver conclusion, prevalence estimate, or seal adoption.

A final bounded fidelity correction then separated calibration-ruler defects
from reader defects. It made asserted desires affirmative, prohibited a nearby
preference from inventing an axis, reason, or comparison, allowed different
supported atomic decompositions in the cold repeat, allowed one reply to carry
both attributed parent claims and its own shopping reaction, and split the
retailer peeling gold into its two independently supported facts. These are
general meaning rules; they add no field, second read, example table, or new
production work unit.

The fresh blind run at
`C:\tmp\forseti-summer-fridays-semantic-calibration-v21-review-fix-20260810-v5`
used method hash
`9ff5c8a8be460ef2b599d08ec08485ebbd698ef12ad2db9eb9cf8bad38090805`,
kept the two production-shaped prompts (largest 89,958 bytes), accounted all
7/7 semantic-core and 121/121 production-shaped leaves, and completed both
terminal views. The pigment defect was absent: the desire for more pigment kept
affirmed direction. The original-Glossier row changed shape but did not close
its defect class. It no longer bundled an unsupported `less hydrating than`
degree claim with the supported `not the most hydrating` statement, so its
density adjudication moved from confirmed defect to benign. It still emits
`reddit:13aw1sp:jj95w9s::u081`, which turns the nearby Glossier preference into
a hydration comparison. The blind adjudicator accepted the parenthetical as a
link; owner adjudication treats it as insufficient to establish the comparison.
All seven relation obligations also held.

The run still returned `SEMANTIC_CALIBRATION_FAIL`. The deterministic report
passed 15 of 17 gold cases, five of seven cold repeats, and eight of ten density
audits; its canonical report hash is
`b3e1477c4596fc0da38fbc9e048ba64f8e2519b357e06072262f16877a724a26`.
The remaining failures are different classes: one direct scent answer was
miscast as agreement, a non-repurchase unit inherited a neighboring shade axis,
one cold read preserved a material balm-value observation the primary omitted,
and a production row invented a two-product per-use comparison from a one-sided
quantity statement. Preserve this run as proof that the requested correction
worked and that method-v6 is still not ready for the full corpus. Do not turn
these residuals into more case-specific prompt clauses; route them through the
planned selective semantic verification decision.

The delegated review also found that v5 changed the adjudication instructions
without changing their self-declared `v1` version. The v5 sidecar hash is
`9b6459531ffe20280a087b1ef254f7302a5ee7d63e1a0efa0533a53fac7562af`,
while the earlier preserved runs use
`5fd4aeeafa278291943dc6316fe91a8f6b51a79c69f734dc0d29bb63d4286a49`;
neither `preparation_receipt.json` nor `report.json` stores that ruler hash.
Therefore
the score deltas between those runs cannot be attributed solely to the semantic
method. Freeze the preserved reports under their exact sidecars. Before another
calibration, version the revised ruler and persist its full hash in both the
preparation receipt and final report; do not rewrite the existing report hashes.

The production-shaped prompt also finished only 42 bytes below its 90,000-byte
ceiling. No further method-text growth should use that preserved slice without
an explicit repacking or ceiling decision, because the next small change may
turn two prompts into three and end direct prompt-shape comparability.

Contract v22 closes the ruler-lineage defect for future calibration without
rewriting history. Preparation v2 and report v2 now carry
`semantic_calibration_adjudication_contract_v2` plus full SHA-256
`186a0022397d35ca5ee6a464742155a6e55e606d1ad0da636611d404c838ab78`.
Evaluation accepts only that ruler and the two exact preserved v1 sidecar
hashes; an unknown or receipt-mismatched sidecar fails closed. Re-evaluating the
preserved v5 run through the new code reproduced its report-v1 object and
canonical hash
`b3e1477c4596fc0da38fbc9e048ba64f8e2519b357e06072262f16877a724a26`
exactly. A fresh preparation-v2 proof at
`C:\tmp\forseti-calibration-ruler-v2-proof-20260810` wrote the same ruler ID and
hash into both its receipt and report; with no new adjudication, it correctly
stopped at `SEMANTIC_CALIBRATION_BLOCKED`. This proof changes no extraction
method or prompt and grants no full-corpus resume authority.

Contract v23 adds the smallest complete independent whole-row check between
primary extraction and reconciliation. Run v5 selects method v7. Every primary
claim-bearing evidence row receives exactly one `accept`, complete-row
`replace`, or `unresolved` decision against its leaf and supplied context.
Replacements pass through the ordinary semantic validator; non-claim rows pass
through unchanged. The compiler preserves the original raw-response manifest,
binds the verifier responses separately, and gives reconciliation exactly one
active result. Method v7 fails closed at reconciliation and finalization when
that verification manifest is absent or invalid. The extraction wording and
transport schemas remain unchanged from method v6.

The final fresh blind Summer Fridays dogfood at
`C:\tmp\forseti-summer-fridays-row-verification-v1-20260810-v3` checked all 91
claim-bearing rows from the preserved 121-leaf production-shaped compilation.
It packed six verifier prompts, the largest 89,720 bytes under the 90,000-byte
ceiling, and made no model API call. The independent readers returned 43
accepts, 47 complete-row replacements, and one unresolved row. The runner
rejected no hidden partial result and wrote a 264-unit active compilation with
`compilation_sha256:
7d04a4bcd827f7d9d1f01fcbadca806e1c7a923badc7e8ec78281ff285386a95`.
The same persisted compilation then prepared reconciliation successfully as two
prompts with 264 candidates; its stage hash is
`55ed039e170fbeef7cbd5db61bf441816194f2102214e46d3185a0580892df62`.

The blind pass corrected five of the six preserved residual rows: it removed
hydration borrowed by unqualified Glossier/Laneige preferences, made the short
Cherry-scent answer first-hand, removed shade-fit from ownership and repurchase,
kept the pigment desire affirmed, restored omitted sale purchases, and removed
the invented two-product per-use quantity comparison. It also preserved the
important boundary that an actual named-shade favorite may use
`shade_and_color_fit` while ownership or repurchase alone may not. The one
unresolved row stayed out of the active semantic units rather than being forced
into a claim.

One material semantic residual remains visible. On
`reddit:13aw1sp:jj8kde7`, this final reader accepted the proposed row even though
it omitted the parent-linked negative judgment that the product was not really
worth $24 when judged as a balm and retained sensitivity as a hydration
condition. Earlier independent reads and a final targeted cold check did catch
the omitted value meaning, so the representation and replacement path can carry
the correction; the repeated disagreement proves that one verifier read is not
a perfect completeness oracle. Do not hide this with more case-shaped prompt
clauses or treat the row-verification pass as semantic readiness. It is a
material quality improvement and a fail-closed integration boundary, not a
replacement for bounded semantic calibration. The real dogfood reused the
preserved method-v6 bundle to test the new optional pass; focused tests prove
that method v7 makes the pass mandatory. No full-corpus run, prevalence claim,
Deliver conclusion, seal, or resume authority follows.

The different-vendor patch review then found two mechanical gaps in the v7
claim. First, the legacy flat finalizer did not call the v7 verification gate;
it now carries the same fail-closed check as the staged and v3 finalizers.
Second, the manifest bound the active evidence-ID list but not the active row
content. It could therefore be copied from an honest verified compilation onto
different dispositions and semantic units over the same bundle. Contract v23
now binds `active_rows_sha256` over both active dispositions and semantic units,
and every consumer recomputes it before accepting the compilation. Malformed
manifest-bearing compilations now raise a controlled semantic error rather than
a raw missing-key exception.

The fresh blind readings remain preserved unchanged under the `v3` dogfood
root. A deterministic post-review re-derivation at
`C:\tmp\forseti-summer-fridays-row-verification-v1-20260810-v4` reused that exact
stage and the same six verifier responses; no semantic row was reread or edited.
The 43/47/1 decisions, 264 semantic units, evidence dispositions, and original
raw-response manifest are object-identical to `v3`. Only the strengthened
manifest and its downstream identities changed. The current verified
compilation hash is
`694015e53ea96188a56dcef9c4cca95272ed42a13230956d802543a3c26603eb`,
its active-row-content hash is
`ab178a2f8a16be8716e51131bc85b787707089af8d8b8a5cdd1b91e7b9e1a0b7`,
and the resulting two-prompt reconciliation stage hash is
`6e962e4d9640353df0e144eaa451e02603fa06115722c27eedcc2152ea48d223`.
The earlier `7d04a4bc...` compilation and `55ed039e...` stage remain historical
pre-content-binding receipts; current code correctly refuses to treat their old
manifest shape as sufficient v7 verification.

Contract v24 keeps the same whole-row verification architecture and versions
its verifier method to v2. The change is deliberately procedural: before
checking axes or other fields, the reader privately reconstructs every
standalone meaning, preserves simultaneous positive and negative judgments,
and maps each material meaning to a proposed unit. Later context may qualify an
earlier answer but cannot erase it without an explicit withdrawal. Every field
must remain supported by the source or supplied context. A customer attribute
conditions a result only when it states or unambiguously entails the same
baseline or the source explicitly scopes that result to it. A possible bias,
caveat, or different product response stays a separate meaning, and a conjoined
attribute phrase splits so that only the part whose baseline the result reports
qualifies it. Sensitivity alone establishes no moisture baseline; product-linked
sensitivity remains reaction/tolerance context, while dry or dehydrated context
may qualify moisture. The private inventory adds no response field, parser,
extra worker, or Deliver judgment. Verifier-v1 stages remain historical
artifacts rather than being silently replayed under the new method text.

The verifier-v2 calibration used the preserved 121-leaf Summer Fridays
production-shaped compilation. An initial full blind pass at
`C:\tmp\forseti-summer-fridays-row-verification-v2-20260810-v0` checked all 91
claim-bearing rows in six prompts and compiled 35 accepts, 54 complete-row
replacements, two unresolved rows, and 285 active semantic units with no model
API calls. It restored the omitted `reddit:13aw1sp:jj8kde7` judgment that the
product was not worth $24 as a balm, but still attached sensitivity to hydration.
That near-miss kept the calibration open rather than allowing prompt structure
or a valid compilation to stand in for semantic success.

The final bounded repeat at
`C:\tmp\forseti-summer-fridays-row-verification-v2-20260810-v5` used method hash
`037ac8e7256cda9ffce258cab0738ff76b2395bf1ec666217419f068a6901faa`.
Its full 91-row preparation still packed into six prompts under the existing
90,000-byte ceiling; the largest was 89,787 bytes. Three fresh blind readers
then independently checked the same real three-row boundary. All three restored
the balm-value judgment, kept the hydration result condition-free, and preserved
sensitivity as a separate reaction/tolerance meaning. All three retained very
dry lips as the hydration baseline on `reddit:13aw1sp:jj93sc5`; all retained
natural wrinkles as the smoothing baseline on `reddit:13aw1sp:jj9vrbp`, while
one of the three also carried lip dryness into that smoothing condition.
The final targeted responses were fresh-read for exact row order, complete
replacement shape, statements, and conditions. This proves the bounded semantic
boundary and production prompt packing, not a completed final-method 91-row
submission, semantic readiness, full-corpus resume, prevalence, Deliver, or seal.

The delegated code review then treated that one-of-three dryness carryover as a
live attribute-overbinding residual rather than a settled reader difference:
the leaf conjoins dryness and wrinkles in one attribute phrase, and only
wrinkles report the smoothing result's baseline. Home adjudication accepted the
attribute split, generalized non-cancellation to any later context, and required
every returned field to remain supported rather than restoring a long field
checklist.

The adjudicated replay at
`C:\tmp\forseti-summer-fridays-row-verification-v2-20260810-v6` used method hash
`0172f560dd83a6f866842c06473d35f9f79633a5e71bf17a84ca95546f08affb` and stage
hash `b6d35dd65da16e19b9ded1590d3eec06d3da44f30e61c70638c959e5147f0797`.
A fresh production preparation again covered all 91 claim-bearing rows in six
prompts; the largest rendered prompt was 89,909 bytes under the unchanged
90,000-byte ceiling. Three new blind readers then received the same real
three-row boundary through the actual renderer. All three restored the
balm-value judgment, left hydration free of sensitivity, retained sensitivity
as separate reaction/tolerance context, retained very dry lips only for the
hydration comparison, and retained natural wrinkles—but not dryness—for the
smoothing result. Their persisted JSON passed fresh checks for exact row order,
complete replacement shape, statements, axes, and conditions.

This remains a bounded semantic proof, not a completed final-method 91-row
response submission, semantic readiness, full-corpus resume, prevalence,
Deliver, or seal. One separate architecture residual also remains: applying row
verification refuses a mismatched stage, but a later reconciliation consuming a
stored verified compilation does not itself embed or re-derive the verifier
method identity. That provenance hardening is not part of this semantic-method
fix.

Contract v25 closes that stored-compilation residual with
`semantic_evidence_row_verification_manifest_v2`. The active compilation now
carries the verifier method version and exact method-text SHA-256 inside the
manifest hash; every current reconciliation/finalization entry point re-checks
both. A legacy-v1, missing, substituted, or rehashed mismatched binding fails
closed and must replay row verification. This changes only the manifest schema;
the verifier stage, response, prompt, and semantic method stay unchanged.

The same 91-row production-shaped input was also repacked without executing new
semantic responses to measure the prompt-size tradeoff. A 90,000-byte ceiling
uses 6 prompts and 488,963 total rendered bytes; 60,000 uses 11 and 635,473;
50,000 uses 17 and 811,285; 45,000 uses 23 and 987,097; 40,000 uses 37 and
1,397,325; and 37,500 uses 50 and 1,778,251. One-row prompts range from 31,375
to 37,216 bytes, so 37,500 is the current corpus's mechanical floor and 35,000
cannot carry every row. The successful final three-row blind replay rendered at
43,757 bytes, making 45,000 the smallest semantically evidenced operating
candidate. It is not yet the full-corpus default: it roughly doubles prompt
bytes versus 90,000 and still needs the complete 91-row semantic replay to
measure quality and latency under that packing.

Contract v27 keeps the one-reader whole-row architecture and versions its
verifier method to v3. A customer attribute excluded from a result's structured
conditions must also disappear from that result's sentence. When the source
separately links the excluded attribute to another product response, that
separate meaning remains evidence instead of disappearing with the neighboring
condition. Calibration can now grade an explicitly supplied verified
compilation, but only after rebuilding its primary compilation and proving that
the verifier manifest cites that exact input and preserves its raw-response
lineage. Method-v7 calibration fails closed when no verified compilation is
supplied. When cold repeat is configured, its raw responses pass through the
same row-verification application and exact-input lineage check under the
reserved `cold-repeat` slice id; method v7 therefore compares verified primary
rows only with verified repeat rows.

The final boundary replay at
`C:\tmp\forseti-summer-fridays-row-verification-v3-boundary-20260811-v1`
rendered the same three real Summer Fridays rows in one 44,047-byte prompt. All
three fresh blind readers preserved lip sensitivity as its own product-linked
reaction, excluded sensitivity from hydration, retained very dry lips as the
hydration baseline, and retained natural wrinkles—but not dryness—as the
smoothing baseline. This closed the repeated statement-versus-condition leak
without adding a second standing verifier, case-specific field, parser, or
provider call.

The complete 91-row replay at
`C:\tmp\forseti-summer-fridays-semantic-final-v3-50k-20260811-v1` then used a
50,000-byte verifier ceiling. The final method text packed 91 claim-bearing rows
into 18 prompts, with a 49,674-byte largest prompt and 846,131 rendered bytes in
total. Three blind workers returned 37 accepts, 54 complete-row replacements,
and zero unresolved verification decisions. The active compilation contains
278 semantic units and has `compilation_sha256:
c90fd3a7fdc4addffa2aac905ad9a7964301ace0985985543b5852f2ce627230`.
The five previously load-bearing rows now preserve the settled boundaries: the
balm-value judgment and separate sensitivity reaction survive; sensitivity does
not enter hydration; dryness does not enter smoothing; ownership and repurchase
do not borrow shade fit; and the Ole Henriksen comparison does not invent a
Summer Fridays quantity claim.

Reconciliation completed in four levels over 25 observed minutes from verifier
preparation to final view. A level-one competence correction demoted six
community-authored observable statements from established facts to non-terminal
attributed evidence; their meaning and provenance remained available. The
terminal `semantic_evidence_integration_view_v2` accounts for all 121 captured
items, contains 10 consolidated propositions—nine independently repeated and
one resonance-supported—plus 242 distinct unmerged semantic units, and keeps
three source leaves explicitly unresolved. Its
`view_sha256` is
`701602c002fdc056b4faf7cdae7f2efc7024462feaf8b05a4f6208be6e105a51`.
The 161-plus-1 split at reconciliation level three is an observed latency
inefficiency, not a semantic omission or a reason to mutate the route inside
this proof.

What that run does not establish is the new calibration gate itself. Its bundle
is `semantic_evidence_integration_method_v6`, recorded as `method_version` on
the terminal view, so the method-v7 fail-closed path above has unit coverage
only and no real-run evidence. The same lineage carries a second gap the run
cannot close: because row verification is permitted but not required below v7,
this exact v6 lineage can still be graded on its unverified primary compilation
by omitting the verified-compilation root, and the calibration report records
only a compilation hash, never which of the two it graded.

This completes the production-shaped 121-leaf batch's accounted semantic path;
it does not yet authorize the 59,225-leaf corpus. The existing calibration gold
predates the settled attribute, ownership-axis, and comparison boundaries, so a
fresh adjudication must grade this exact verified compilation and its terminal
view before the full corpus resumes. The run makes no prevalence, Deliver,
campaign, seal, or readiness claim.

Contract v28 keeps the same single whole-row verifier and versions only its
method text to v4. The verifier now treats replacement as a correction of the
proposed row rather than an invitation to rewrite it from scratch: supported
meanings, axes, product bindings, conditions, posture, and direction stay unless
the source justifies a named correction. It also aligns drying and non-drying
with hydration, records named-shade or all/every-shade ownership as
shade-specific behavior, records an expressly sale-conditioned future purchase
as value evidence, and prevents a statement solely about a comparator from becoming a
Summer Fridays statement. At finalization, method-v7 personal agreement may
support the meaning but cannot count as another independent first-hand customer.
Historical verifier-v3 receipts remain identifiable but require replay before
current reconciliation, and historical semantic views rebuild exactly.

The bounded v28 dogfood reuses the frozen v27 extraction responses so the test
isolates the verifier and claim-support changes. Its fresh prompts use a
50,000-byte ceiling and cover semantic-core, cold-repeat, and the complete
production-shaped verification slice. This replay is calibration evidence only;
it does not authorize the full corpus until its blind responses validate and a
fresh adjudication passes the existing gate.

The final-hash replay is recorded at
`C:\tmp\forseti-summer-fridays-semantic-verifier-v4-dogfood-20260811-v1`.
It checked all 103 claim-bearing rows: 86 were accepted, 17 received bounded
complete-row corrections, none were unresolved, and all three verified
compilations validated with zero model API calls. The verifier corrected drying
without moving peeling out of reaction, kept customer sensitivity separate from
hydration conditions, retained all/every-shade behavior, added value only when
future purchase was expressly sale- or price-conditioned, and removed
comparator-only target bindings. The current compilation hashes are
`a4a56aaf2400ffe670cf1f1d45f1569a22ad3bcbacfbd25eed6a8a68e8e09a47`
for semantic core,
`dd5d70e7a88273c737b194c02709bfe2a80bbc2b5c9e014cef073cab05592a41`
for cold repeat, and
`d85142112dc2850cf98fd39278046a9efc7a59f3ac5ea7515a6cdf78ba9f046e`
for the production-shaped slice.

Reconciliation accounts for all 7 core and 121 production-shaped items. The
core view contains 25 propositions and retains two echo-only meanings as
unmerged attribution (`view_sha256:
b37be3fdaeccf2f17f7332ac850d152bf31c0689ebff5313ef340b738fe45fed`).
The production view contains 17 genuinely stacked propositions and preserves
202 distinct meanings explicitly as unmerged retrieval evidence rather than
manufacturing consensus (`view_sha256:
82e530edc20be48cc78cdfc76fb197612cdc537ca32eaf20cf47d89bde1c3121`).

Fresh blind adjudication remains `SEMANTIC_CALIBRATION_FAIL`: 15 of 17 gold
cases pass, all 7 relation obligations are satisfied, 4 of 7 cold repeats are
consistent, and all 10 density rows are benign. The remaining semantic defects
are one omitted target-versus-Lanolips moisture comparison and one primary row
that invents a product-linked sensitivity reaction; the latter also creates an
eighth unit beyond the ruler's 4..7 range. Three cold cases remain inconsistent.
The evaluator separately reports `PREPARATION_RECEIPT_MISMATCH` even though the
rebound receipt and stored spec bind the same `spec_sha256`; that mechanical
residual is not hidden or counted as semantic success. Full-corpus execution
therefore remains paused.

Contract v29 installs the smallest general correction for those remaining
semantic defects without adding another verifier. The active verifier-v5 method
now performs one final source-to-unit completeness check, preserves an explicit
same-dimension relational comparison separately from its side observations,
and requires an explicit bound-product link before turning a nearby customer
attribute into a product response. It also keeps supported adjacent-product
meanings under their own subject. Historical verifier-v4 results remain evidence
about the prior method and must not be relabelled. A fresh blind verifier-v5
replay and adjudication still owe proof; until that run passes, the full corpus
remains paused and the independent preparation-receipt mismatch remains open.

The fresh verifier-v5 row replay at
`C:\tmp\forseti-summer-fridays-semantic-verifier-v5-dogfood-20260811-v0`
proved both targeted corrections at the row boundary: all 40 required gold
meanings were present, including the missing hydration comparison, and the
sensitive-lips row returned seven supported meanings without inventing a
product-caused sensitivity reaction. A blind precheck found 16 of 17 strict
gold rows, 6 of 7 cold repeats, and 9 of 10 density rows clean. The strict gold
miss is a stale ruler boundary: its scent-causal named-shade preference allowed
only `scent_and_flavor`, while the settled named-shade rule also requires
`shade_and_color_fit`. Verifier v5 nevertheless remains insufficient because
one reader made two partially ambiguous rows wholly unresolved, one cold repeat
broadened shade-specific sale intent to the product family, and one density row
lost an explicit overall positive evaluation.

Contract v30 versions the same verifier to v6 for those general residuals.
Local ambiguity may no longer erase independently safe meanings; ambiguous
variant and echo meanings stay bounded without guessing; variant-specific
behavior cannot broaden to the family; and explicit overall evaluations remain
separate. Verifier-v5 artifacts remain preserved as negative proof. A fresh
blind v6 replay, corrected gold-ruler binding, terminal reconciliation, and
formal adjudication remain required before full-corpus execution resumes.

That blind row replay is recorded at
`C:\tmp\forseti-summer-fridays-semantic-verifier-v6-dogfood-20260811-v0`.
All 103 rows compiled under verifier-v6 with zero unresolved decisions and zero
model API calls. Both original defects remain corrected, both formerly dropped
ambiguous rows retain their safe meanings, and all 40 required gold meanings are
present. The strict stored ruler reports 15 of 17 cases, but both disagreements
conflict with settled doctrine: the named-shade favorite correctly carries
`shade_and_color_fit` beside its scent reason, and an explicit overall favorite
reaction remains evidence rather than disappearing. On the settled rules the
gold meanings are 17 of 17. Cold repeat is 4 of 7 field-exact; two additional
pairs preserve the same propositions with only asserted-versus-qualified drift.
The apparent Poppy-specific broadening was later found to be a ruler error, not
a semantic regression: the parent asks whether the product range is worth USD 24,
while Poppy identifies the option the customer owns.
The density audit is 9 of 10 clean and finds one omitted material conversion
context. These residuals show that more verifier prompt wording is no longer the
smallest correct move: the governing rules are already present but one-pass
readers apply them unevenly. Keep full-corpus execution paused pending an
architecture decision on semantic disagreement/coverage handling, a corrected
hash-bound ruler, and the still-open preparation-receipt mismatch.

Verifier v7 corrects that referent-scope error without adding a variant catalog.
It resolves pronouns and evaluation scope from the whole exchange, retains the
named option as a separate ownership or experience meaning, and does not
automatically narrow later product-level judgments to that option. In two fresh
blind rounds, all three readers selected a product-level sale judgment; after a
completeness clarification, all three also retained Poppy ownership, sale value,
switching, smoothing failure, and no-repurchase evidence. This bounded check
does not resume the full corpus or close the other recorded residuals.

The four-comment verifier-v7 delta at
`C:\tmp\forseti-summer-fridays-semantic-delta-v1-20260811-v0` confirmed the
referent-scope correction: independent reads retained Poppy as ownership context
while keeping the sale-only judgment at product scope, and both retained the
skin-tint conversion context. It also exposed two narrower verifier residuals:
one verifier reused reaction susceptibility as a hydration condition, and one
lost the value meaning of explicit product waste through an application tool.
Contract v32 versions the verifier to v8 with those two general clarifications.
The bounded blind replay at
`C:\tmp\forseti-summer-fridays-semantic-verifier-v8-delta-20260812-v0`
applied verifier v8 independently to the primary and cold compilations. Both
stages bind method hash
`96237f5b5a407727f2ee338e9c6838a577e91de6ceb609d165d6906b437dabd8`.
Both verified outputs left hydration unconditioned by sensitivity, retained
explicit sponge/product loss under `value_and_quantity`, and completed with zero
unresolved rows. The runner accepted both full verified compilations:
`bd14adcf131ddfbd630b75fd64778e7869d6984da5c6588e77b85d47147ca567`
for primary (36 active units, 0 accept / 4 replace / 0 unresolved) and
`f387ac008c345a252dcafd705a3a9cad849402a0e5a9a05f875884706d2148cf`
for cold (32 active units, 1 accept / 3 replace / 0 unresolved), with zero model
API calls. The two legs differ on the separability half of the new value rule:
the primary leg carried the sponge product-loss meaning as its own unit, while
the cold leg kept it fused with the thin-texture and tool meanings in a single
three-axis unit. That axis retention is proven on both legs; independent
separation is proven on the primary leg only. This closes the two-comment
verifier boundary at axis retention; no historical result is relabelled and the
replay alone does not claim full-corpus completion.

Contract v33 adds an opt-in reconciliation-policy v2 without changing semantic
method v7, its extraction prompts, or its mandatory row-verification artifacts.
The policy is selected once when preparing the first reconciliation level and
is then carried in each validator-produced node compilation. Reconciliation
node keys are local to their prompt batch; compiler identity continues to
combine the stage, batch, and local key, so identical local handles in different
responses cannot collide. Normal mode must retain every valid first-hand or
personal-agreement customer finding as a semantic node, including a one-row
finding. After a completed normal level removes less than one percent of its
input candidates, the next level enters convergence mode. Convergence prompts
receive only the compiler-counted number of distinct supporting evidence rows:
a one-row finding stays retained as unmerged retrieval evidence, while a
candidate or exact-equivalence merge spanning more than one source row must
remain a node. The validator enforces all three boundaries independently of the
prompt and preserves exact child accounting. Historical preparation without
the policy remains byte-stable; the completed verified method-v7 compilation
can therefore be replayed under the new reconciliation policy without
re-extraction or row re-verification.

A convergence pass is terminal when every surviving candidate remains a
terminal node and the pass produces exactly as many nodes as it received
candidates. This fixed-point rule may span multiple prompt-bounded batches:
prompt byte size is a transport constraint, not a semantic requirement to
invent another merge. Historical reconciliation without policy v2 retains its
single-batch terminal rule.

The full-corpus policy-v2 replay reused the existing verified method-v7
compilation and reached a fixed point at level 8. The terminal compilation has
107 repeated findings supported by 320 semantic units; 7,700 one-off or
otherwise non-converged units remain explicitly retrievable, so all 8,020
captured semantic units are accounted exactly once. The finalized view accounts
all 60,901 captured corpus items (59,225 semantically assessed and 1,676
mechanically excluded), reports zero blocked items, and preserves the 96
explicitly unresolved evidence rows. Its stored view SHA-256 is
`b50dda4370b2c98ce4ac2553aa9c2cb84b5cb23f1c91fa55567c7f9607b31c42`.

Contract v34 does not relabel that policy-v2 replay. It adds a separate opt-in
route that closes relations before one-row findings are retired. Deterministic
block pairs cover every unordered pair on one terminal normal-retention
frontier exactly once. Prompt batches remain transport only: equivalent pair
decisions form transitive classes across partitions, and opposed pair decisions
form symmetric links between classes. Directional identity comes from a
deterministically selected truth-complete frontier assertion and excludes axes,
stage, batch, and local handles. Finalization requires a hash-bound decision for
every required pair, with zero unresolved pairs, and writes view v3; missing
coverage cannot appear as `none_observed`.

That v34 route is experimental rather than operational. On 2026-08-13, a dated
operator read of
`C:\tmp\forseti-summer-fridays-full-corpus-v8-20260812-v0\reconciliation-policy-v2\level-0002\node_compilation.json`
(raw-file SHA-256
`23b417fde1de678379fabf54ea50fdcaaac7b8e0811b5d21c4227d53c40b7d75`;
stored `node_compilation_sha256`
`344e38ac29c0dbe27af397271ed0657b96b983e87e4b679f318cd8ba5311c473`)
observed 7,076 semantic nodes and 780 carried unmerged units. A read-only name
scan of that run root observed no relation-closure output. Those statements are
operator observations scoped to that exact path and date, not repository-backed
universal absence proof. Exhaustive preparation at that scale would require
millions of decisions, so v34 must not be run, treated as completion, or used to
claim global identity, global opposition coverage, or `none_observed` for that
frontier. Structural finalization guards reject internally inconsistent closure
schema, candidate membership, all-pairs identity, and coverage cardinality, but
remain containment rather than semantic proof against a coherently forged whole
artifact.

The supported completed path for normal Forseti intelligence cycles remains:
full-corpus extraction -> mandatory row verification -> policy-v2 normal
reconciliation -> convergence/retention under the existing supported policy ->
the supported view/output. Preserve one-off and unresolved evidence honestly;
absence of v34 closure never converts into `none_observed`. Registry-first
global identity, embeddings/top-k retrieval, deterministic blocking, and
exhaustive all-pairs closure are deferred research directions. Agents must not
explore or implement them unless an owner explicitly reopens architecture work
because a measured customer or intelligence outcome is materially harmed by
duplicate meaning identity or missing global opposition. On that trigger,
reorient first to the semantic integration contract's "Supported operating
route and owner-only reopen boundary" and then this workflow for current run
history; otherwise continue the supported policy-v2 path.

When closure exposes a bad source-row decomposition or mixed logical polarity,
`prepare-row-repair` projects only the named evidence rows through the existing
complete-row verifier. `submit-row-repair` preserves every other active row,
writes explicit repair lineage, and changes the verified compilation hash.
Every prior reconciliation and view then fails stale-lineage validation and
must be regenerated. When a completed old policy-v2 terminal compilation is
available, run `migrate-repaired-terminal` before commissioning a full replay.
That no-provider operation is admissible only when it can prove complete
old/new leaf equality for every reused node, preserve exact unmerged membership,
and deterministically rederive every changed dependency under the semantic
contract's narrow polarity-only rule. It writes a new terminal compilation and
separate hash-bound manifest; it never edits or rebinds an old response. A
statement, scope, condition, posture, membership, relation, or lineage change
outside that proof rejects locally and returns the operator to fresh policy-v2
reconciliation. Run `finalize-v3` and evidence-packet projection only against
the repaired verified compilation plus the new migrated terminal compilation.
The route does not permit direct edits to node compilations or finalized views.

The owner-authorized Summer Fridays repair successor at
`C:\tmp\forseti-summer-fridays-polarity-repair-replay-20260817-v0\incremental-terminal-migration-v9`
exercised that exact route with zero provider calls. Complete-row repair changed
five semantic units: three proposition-linked overhyped rows changed polarity,
while two additional meanings from the same repaired evidence rows changed but
retained their exact unmerged membership. Those two memberships and their prior
reasons were preserved rather than freshly adjudicated against the repaired
meanings; a consumer needing that stronger claim must use fresh reconciliation.
The migration reused 106 of 107 old terminal nodes, invalidated and rederived
one, and coalesced two compatible
exact-identity groups into 105 unique terminal nodes. It preserved 320 terminal
leaf relations, 7,700 unmerged units, 8,020 total semantic units, 96 unresolved
evidence rows, and all 60,901 captured/accounted items. The full packet also
preserved the selected legacy source-native engagement observations instead of
converting them to unavailable: 3,215 Reddit rows retained their literal score
state and 132 retailer rows retained their literal positive-helpful count,
with no inferred values. Stored hashes are
`3682244e87a8b305f882794575b0fa77f55ef77220c0545b8058eb899388be15`
for the successor node compilation,
`61dcbfc4b2426e131b56392c83d10a9096f96ef209c791bcf5552554f2d2f37a`
for its migration manifest,
`865dd68cd3c56e13e1369a4c8ef798ac4d3ae6ff36ed4fc52440ec0409f87cdb`
for the finalized 105-proposition view, and
`c9d8b5e5d1b199689f9fc0a35c6dc4f19de0a48e4e9815f5ec03ff8ddc62fe34`
for the full-view `phase_a_evidence_packet_v3`. A second clean output directory
at `incremental-terminal-migration-v10` reproduced all four artifacts
byte-for-byte. The earlier v7/v8 runs remain historical evidence but are
superseded: independent review found that their single rederived node replaced
its prior-level `child_relations` with flattened leaf refs. The finalized view
was unaffected, but the node-lineage record and packet source binding were not
lossless and must not be reused.
