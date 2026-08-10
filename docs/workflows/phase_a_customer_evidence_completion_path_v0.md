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
