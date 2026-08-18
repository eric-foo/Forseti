---
retrieval_header_version: 1
artifact_role: Phase A customer-evidence completion path
scope: Customer-language semantic integration from full acquisition corpus through cold-agent proof; campaign and Deliver boundaries remain separate
use_when:
  - Resuming the full Summer Fridays customer-corpus semantic run.
  - Applying the same Reddit/community plus retailer-review method to another company.
  - Deciding when customer evidence is ready to hand to Synthesize or Deliver.
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
useful presentation, use the existing no-provider evidence-consumer's
`prepare-evidence-selection`, `finalize-evidence-selection-relations`, and
`finalize-evidence-selection-quotes` operations. This is a consumer view over
hash-bound `phase_a_evidence_packet_v3`; it is not packet v4, a semantic replay,
or a second evidence authority.

Admission uses explicit product plus axis membership, with literal nominated
semantic or unresolved refs for bounded non-axis cases. A nomination that
cannot resolve fails closed instead of disappearing. The external relation
response must account for every admitted candidate before deterministic
presentation selection. Each candidate carries the other normalized meanings
from that same evidence item as context only, so a price complaint cannot hide
same-source purchase or repurchase intent. For value work, bind `price feels
high` separately from `not worth it`, and nominate an evidence item that records
purchase, repurchase, switching, return, or abandonment under the existing
`costly_behavior` protection when that behavior changes the commercial reading.
Candidate admission remains direction-neutral: admit the relevant positive and
negative value evidence before assigning claim-relative support or counter.
Do not search for complaints first and then treat the surviving set as the
answer. A relation label describes how the row bears on the bounded claim; it
is not a permanent positive/negative label. Thus purchase or repurchase despite
price discomfort counters a poor-value claim and may be presented as a positive
willingness-to-pay or value signal.

Keep atomic semantic meanings and their refs separately recorded. In the
presentation layer, meanings from the same evidence item may be grouped when
they have the same actor, action, direction, and conditions. For example,
separate shade meanings may display as “intends to repurchase Vanilla and
Vanilla Beige” while both semantic refs and named shades remain underneath one
origin and one exact quote. Never group across origins, hide a conflicting
clause, or broaden a shade-specific behavior into general repurchase.
The cap applies to displayed independent-origin
groups: ten customer truth groups and three creator-influence groups. Source
roles and retailer venues remain visible, with each publisher normalized to one
venue across host variants and short links; creator-authored popularity never
corroborates customer experience. Engagement may prioritize rows only inside
one venue/role/native-metric bucket, and a count the runtime cannot read whole
is ordered last rather than partially parsed. An unrecognized mapping-valued
engagement shape fails closed rather than becoming an unknown value or generic
score. Every nominated safety or costly-behavior origin is selected first; more
than ten such customer origins fails `presentation_cap_insufficient`. The
selector then reserves visible support and counter only from materially positive
or explicitly protected evidence. Unprotected zero, quiet, and
engagement-unavailable rows stay in the complete disposition inventory but are
not forced into the main presentation merely to fill a lane or venue. If no
materially positive or protected counter exists, the main presentation carries
no counter rather than manufacturing one from weak response. Each protected
group records its required display lanes, and the deterministic minimum member
rows needed to cover them are shown; one origin may therefore display multiple
rows. Every operator-protected row is visible or the run fails. The retained
disposition inventory remains the accounting record for all other displayed and
undisplayed candidates.

The quote stage reads bodies only for selected display rows. An available source
body of at most 220 characters must be quoted in full, so a short comment cannot
be clipped before a material qualification or same-source costly behavior. For
a longer body, it accepts one context-complete contiguous exact substring of at
most 220 characters after packet and bundle
content verification and evidence-ID, artifact-ID, and source-ref verification,
and rejects a body that changed after the quote manifest was written. When a
material qualification cannot fit, the quote response returns unavailable
rather than a misleading fragment. It never repairs text or adds ellipses. An
available quote must contain at least two
Unicode alphanumeric characters; no lexical-overlap relevance rule is applied.
A `quote_unavailable` row carries `source_body_present` and a deterministic
cause: `source_body_unavailable` when the body is absent, or
`no_relevant_exact_quote_returned` when a present body yielded no quote.
Available quotes carry a null cause, and the normalized meaning remains in every
case. The completed artifact retains every candidate disposition
and the full candidate-inventory hash, including Amazon or Revolve rows that did
not earn a display slot. Repository runners emit prompts and schemas but make
zero provider calls.

New quote manifests use `phase_a_evidence_quote_manifest_v2`. Every selected
row requires one `presentation_statement` of at most 220 characters that states
the evidence-bound commercial reading in plain language. It groups eligible
same-evidence meanings, retains named variants and material reversals, and does
not append generic caveats whose limits are already implicit in the evidence
fields and controlling claim-support contract. Legacy v1 quote manifests keep
their original response shape and remain finalizable.

Regression note: the exact short comment “Do I cringe a little every time I
remember the price tag? Yes. Will I be repurchasing vanilla AND vanilla beige?
Also yes.” must remain one context-complete quote. The exact comment “They are
kind of expensive for what they are, but the packaging is just so cute I can't
not.” likewise carries price resistance and purchase behavior together. In
both cases, extracting only the price clause reverses or materially weakens the
commercial reading. Weak zero-engagement complaints remain accounted but do
not displace a materially engaged or protected counter merely to fill a lane.

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
