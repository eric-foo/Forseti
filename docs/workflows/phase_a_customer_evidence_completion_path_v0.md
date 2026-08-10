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
