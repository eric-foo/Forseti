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
verified outputs left hydration unconditioned by sensitivity, retained explicit
sponge/product loss under `value_and_quantity`, and completed with zero
unresolved rows. The runner accepted both full verified compilations. This
closes the two-comment verifier boundary; no historical result is relabelled and
the replay alone does not claim full-corpus completion.
