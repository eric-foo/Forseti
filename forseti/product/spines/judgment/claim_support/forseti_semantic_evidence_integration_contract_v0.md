---
artifact_role: authority
status: current
owner: Judgment / claim support
version: v104
effective_date: 2026-09-02
depends_on:
  - forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md
---

# Semantic Evidence Integration Contract v104

## Purpose

Semantic Evidence Integration turns one completed acquisition corpus into a
meaning-aware proposition view before downstream synthesis. It exists because
a large, well-captured corpus can still be underused, misbound to the wrong
product or competitor, or summarized from a convenient handful of citations.

This is a shared Judgment capability. An acquisition route may invoke it as a
pre-seal closure job, but does not own or redefine its claim-support semantics.
The existing intelligence claim-support contract remains the authority for
support posture, independence, conflict, source-role fitness, and causal
ceiling.

Semantic Evidence Integration is the runtime capability inside the named
**Evidence Consolidation** stage. That stage starts from an immutable,
completely accounted acquisition corpus and owns semantic leaf triage, atomic
evidence structuring, meaning-based cross-source reconciliation, and
evidence-packet projection. Its output is the complete evidence retrieval
surface consumed by the acquisition seal and later Deliver work. This stage
boundary does not create or rename a globally numbered phase; historical Phase
A, Phase B, Turn B, Understanding, and Deliver vocabulary remains unchanged.

It is not a market conclusion, recommendation, sentiment score, representative
estimate, causal model, custom-trained model, embeddings service, vector store,
or graph database.

## Operating location

For broad consumer-brand Understanding:

```text
SERP Phase 1 -> evidence fan-out -> SERP Phase 2 and adaptive returns
-> all selected acquisition jobs terminal
-> Semantic Evidence Integration
-> any affected-axis delta work terminal and integration regenerated
-> acquisition seal
-> Synthesize
```

The integration job may expose a material missing class or emerging axis. The
controller then reopens only the affected acquisition family. Any changed
corpus invalidates the prior integration view; the final seal points only to a
view compiled from the final corpus hash.

## Division of labor

The semantic agent owns only meaning:

- interpret paraphrases rather than match literal wording;
- split one source item when it makes different product, comparator, axis, or
  conditional statements;
- preserve negation, uncertainty, product/version identity, and conditions;
- relate a semantic unit as support, opposition, or adjacent context; and
- nominate an emerging axis when no existing axis fits honestly.

The intelligence claim-support contract's **Meaning-preserving interpretation
and useful abstraction** rule governs authoring and review here. Consolidation
may express a useful common claim without requiring lexically identical or
equally detailed sources. First-hand preferences and stated intentions may be
`customer_experience` claims when their meaning stays explicit; `reported_behavior`
credits `behavior_evidence_refs` and requires the behavior actually reported,
not a desired or future act. Source-role competence alone does not choose that
meaning. Do not create a new schema kind or silently relabel a frozen answer.

Deterministic code owns:

- the admitted evidence denominator and exact per-alias accounting;
- source-artifact resolution and hashes;
- stable batch, semantic-unit, proposition, corpus, and view identity;
- actor/origin de-duplication and conservative credited-public-origin counts;
- engagement availability;
- authority-owned source-role competence and impossible combinations;
- claim-support projection; and
- stale/incomplete-view rejection at the acquisition seal.

The agent never chooses its own evidence count, independence count, support
posture, cross-venue credit, or causal strength.

This ownership also applies to `bounded_meaning` prose. Current response-v3
normal and missing-definition authoring use count-neutral reported wording,
not a headcount inferred from attached statements or comments: the compact
candidate view does not expose complete author identities. Keep actual
source-attributed claims about other people attributed; do not delete them or
promote them into verified counts. Code still supplies origin/observation
accounting. Inverse comparisons may express the same fact, but the current node
shape requires one exact stored subject/comparator orientation; retain opposite
orientations separately without relabeling child identity. This is a transport
constraint, not a claim that the meanings differ or represent separate events.

Current authoring uses run v10 / integration method v12 / row-verification
method v11. `CURRENT_AXES` alone supplies valid output axis IDs. Category names
in the semantic examples below describe meaning, not fixed identifiers or
mandatory assignments across companies. The agent selects supplied IDs by the
unit's meaning and the supplied labels; it never imports Summer Fridays IDs
into a different inventory. Where no current axis fits, preserve supported
meaning with empty `axis_ids` and an emerging-axis label where appropriate.
Code still rejects foreign IDs; it does not translate categories or infer fit.
Earlier run/method identities and their prompt bytes remain historical replay,
not current cross-company authoring. No frozen output is rewritten or silently
promoted into the new generation.

Upstream `product_candidates` are hypotheses, not product truth. For the
current method, every admitted item also carries source-pinned product context
such as a thread title, parent text, post text, product page, creator post, or
source scope. The agent may bind an exact product only from the evidence text
together with that context. Context establishes what the item is about; it
does not donate unstated claims to the item's author. If the binding remains
unclear, the item stays `unresolved` or `out_of_scope`.

### Local reconciliation correction

Current response-v3 generation expresses optional retention as mutually exclusive
attached/nonempty-unmerged alternatives. Native validation retains the same
rejection boundary; frozen v1/v2 replay and already valid v3 responses are not
rewritten. Generation-schema compliance is not a semantic verdict.

When validation or source-aware review identifies a specific reconciliation
problem, `prepare_reconciliation_repair` binds an explicit nomination (node keys
and/or candidate refs plus reason) to the exact original response and stage.
It includes the connected component of all affected candidate/node attachments,
exact leaf text, parent/product context, and compiler-derived source inventory.
Inventory is not claim support: one shared identity remains one credited origin,
but only the established finalizer determines which sources support a claim.
An allegation is not a verdict; review may retain the original choices.

Before emitting a repair request, preparation reuses the compiler's exact
product/comparator/version compatibility check across the original response's
attached groups. If a known incompatible group remains outside the nominated
connected components, preparation fails and lists every omitted group. The
operator must nominate a complete scope explicitly; code does not expand it
silently or choose replacement meanings. This prevents paying for a correction
whose unchanged identity conflict already guarantees rejection. It does not
detect prose errors or promise that no other native defect remains. Previously
valid repair requests and successors retain exact replay; an incomplete request
that could never yield a valid successor is now rejected before the call.

If the existing repair prompt exceeds the stage's byte limit, preparation tries
`PACKED_REPAIR_CONTEXT_V1` before rejecting it. This is a lossless layout of the
same connected component, not a smaller evidence selection: uniform records
may share identical fields and ordered column headings, with every row retained.
JSON types, missing-versus-null distinctions, literal text, source identity,
conditions and ownership remain unchanged. Heterogeneous record shapes remain
lists. The full uncompressed context still binds the request; the consumer
rederives both context and prompt before applying any patch. Previously fitting
requests, response schemas, correction authority and normal authoring remain
unchanged. A still-oversized packet fails before any provider call. Packing
adds no semantic judgment, source retrieval or standing provider stage; model
understanding and correction quality require source-aware assessment.

Use the existing isolated provider route for at most one corrective attempt.
This is failure/review-only work, never a required extra normal-path stage.
The response replaces only that component or explicitly refuses. Code never
infers meaning, chooses a relation, edits upstream facts, or silently supplies
a definition. The full native consumer must accept the successor; other defects
may still block it. The repair model cannot emit `opposition_checked`: code
preserves it only for an exactly unchanged definition and its attachment
decisions, otherwise invalidates it to false. This withdraws prior clearance;
it never awards a new check or semantic approval. Changed or regrouped nodes
therefore remain unchecked for the established relation-closure boundary.
Unaffected definitions, decisions,
label assignments, source identities and original bytes remain preserved.

The public runner's `prepare-reconciliation-repair` and
`submit-reconciliation-repair` commands bind raw input bytes, rederive the
request, reject scope escape, and verify the durable successor on first write
and repeat reuse. A context component that exceeds the existing prompt limit
fails without truncation. Missing definitions alone retain the narrower existing
definition-recovery route. No standing census, retry loop, prose classifier,
additional count renderer, or independent review ceremony is installed.

After a current response-v3 validation failure, the read-only
`diagnose-reconciliation-response` command may inventory every independently
observable defect in its declared mechanical scope before a repair is nominated.
The unchanged validator still supplies `primary_validation_error` and remains
the sole acceptance boundary. The diagnostic reports exact affected candidate
and node handles for the recurring repair-relevant graph defects: duplicate
attachments, missing or orphaned definitions, identity incompatibility,
repeated leaves, and missing effective terminal support. When a malformed
prerequisite makes a downstream check ambiguous, it records that check as
skipped instead of guessing another failure. The report is write-once,
deterministic, current-v3-only, and makes no provider call. It neither selects a
repair scope nor proves semantic warrant; source-aware judgment and the existing
bounded repair routes remain unchanged.

If a scope-correct repair exposes another independent native failure, the
failure-only composer may persist that exact repair as
`LOCAL_REPAIR_COMPOSED_NOT_ACCEPTED`. The intermediate remains explicitly
unaccepted and cannot enter a selection. Its source response, repair request,
repair patch and intermediate bytes are hash-bound. An operator may pass it to
the already-existing definition or local-repair preparer for the newly visible
error; each new semantic edit still requires its own bounded judgment. Code does
not infer, clear or auto-chain a correction, and the normal path gains no call.
The same explicitly unaccepted composition is available when a scope-correct
missing-definition patch reveals a different native defect. Its failed
response, request, patch and intermediate bytes are likewise hash-bound before
the next existing bounded repair is prepared.

Current decision-only authoring also constrains terminal status and its claim
metadata as one schema choice. A nonterminal node requires both `claim_kind`
and `causal_ceiling` to be null; a terminal node requires both to use their
existing admitted values and requires `opposition_checked` to be a boolean.
This is structural compatibility, not proof that opposition was adequately
reviewed. The unchanged native consumer remains authoritative. Historical v2
response schemas and replay are unchanged.

Current decision-only prompts require a single relation for each exact
candidate-and-node pair. A candidate may attach to multiple distinct bounded
meanings, but it must not attach to the same node once as support and again as
counterevidence. The native consumer continues to reject duplicate attachment
keys regardless of relation. This prompt constraint does not mechanically prove
that the selected relation is semantically correct.

An invalid response that reused one node key for multiple definitions may enter
the same failure-only local-repair format only when that duplicate key is inside
the explicit connected nomination. The request carries every duplicate
definition and every attached candidate/source. The patch must return unique,
scope-valid replacements; code never chooses a rename or guesses which child
owned which meaning. Any duplicate outside the connected nomination blocks
preparation by name.

This is a reusable correction boundary, not prevention of every semantic error.
The v89 prompt-only dogfood (three fresh batches) still had five headcount
overstatements and zero initial native accepts. Neither structural acceptance
nor a locally corrected output establishes unobserved reader quality or
unattended reliability. Source-aware judgment must assess the new wording itself,
not assume that a prior source-row review validated a later summary.

## Admitted evidence and completeness

Completeness is bounded to the run's declared admitted evidence set. It never
claims that every raw internet item was captured. Each admitted item must have
exactly one top-level disposition:

- `claim_bearing` — one or more meaning units are emitted;
- `context_only` — useful context but no bounded proposition support;
- `out_of_scope` — outside the bound question/product/cutoff; or
- `unresolved` — meaning or binding cannot be established safely.

Every emitted semantic unit is either used by at least one proposition
relation or receives an explicit unmerged disposition. An absent alias, silent
bulk discard, or unaccounted semantic unit is incomplete. Objective upstream
metadata may define the admitted set; it may not declare that an item lacks a
competitor or material meaning merely because an exact token is absent.

Method v7 adds one independent whole-row evidence-integrity check after primary
extraction and before reconciliation. Every primary `claim_bearing` row is
checked against its exact leaf text and supplied product/parent context. The
checker returns exactly one of `accept`, complete-row `replace`, or
`unresolved`. It never emits a field patch. Deterministic code requires one
decision per primary claim-bearing evidence ID, validates any replacement
through the ordinary response validator, preserves the original raw-response
manifest, binds the verification responses in a separate manifest, and exposes
the hash of the active dispositions plus semantic units in that manifest so it
cannot be transferred onto different row content. Reconciliation sees only one
active result. Its whole-row read must keep direct
customer use, ownership, preference, and context-adopting answers first-hand;
must not assign an axis merely because a shade, product, or adjacent clause
names it; and must not invent a two-sided comparison from one side's stated
amount. It resolves leading yes/no replies against their parent question,
accounts for every materially distinct clause, and keeps unqualified preference
or better/worse language about a product overall axis-free even when it sits
beside an attribute claim. A stated liking or favorite evaluation of a named
shade uses `shade_and_color_fit`. Ownership, purchase, selection, or repurchase
of a named shade or an all/every-shade collection also carries
`shade_and_color_fit` because the observed behavior is shade-specific; this
records the behavioral subject and does not infer that the shade fit well. When
sale timing or price is expressly a condition of an intended or hypothetical
purchase, it also carries `value_and_quantity`; an incidental past sale mention
does not create that judgment.
Non-claim rows pass through unchanged.
Whole-row verification and selective repair bind decisions by explicit evidence
ID, not response-list position. Every assigned ID must occur exactly once;
missing, duplicate, foreign, and mismatched replacement identities fail.
Application follows source order, while the actual response order remains in
raw-response hash lineage. Order tolerance alone does not prove the chosen
meaning correct or change method or stage identity.
Current keyed-v3 methods v10, v11 and v12 emit row-review response v2 for both
verification and selective repair: one required object key per assigned evidence
ID, with replacements constrained to that same ID. The public preparation
runners persist each prompt's `.schema.json`; provider execution must use it.
Native application independently rejects missing/foreign keys and misbound
replacements. Row ownership is mechanical; correct interpretation is not.
The source-work stage and its historical partition remain unchanged. Explicit
library-level response-v1 preparation reproduces historical prompts, and v1
responses remain replayable alongside v2 responses without rewriting their raw lineage. This adds
no provider stage, automatic repair, or semantic classification rule.
Publication and public-runner loading reject duplicate JSON object keys before
stage validation, including nested keyed decisions. The publisher preserves
raw response bytes and exact usage on failure; a parsed last-key-wins object
cannot establish exact participation. This decoder check proves no semantic
meaning, and valid historical responses remain unchanged.
Method v5 and v6 remain historical one-pass routes and acquire no retroactive
verification obligation.

Contract v24 versions the whole-row verifier method to v2 without changing its
response or manifest schemas. The verifier first constructs a private inventory
of standalone meanings, resolving ellipsis only from supplied context; preserves
coexisting judgments unless the source explicitly withdraws one; maps every
material meaning to the proposed units; and only then checks fields. This is an
execution order for the existing completeness doctrine, not a phrase table,
clause parser, extra response field, conclusion pass, or mandatory second
verifier. A customer attribute qualifies a result only when it states or
unambiguously entails the same baseline or the source explicitly scopes that
result to it. A possible bias, caveat, or different product response remains a
separate meaning rather than becoming the result's condition. A conjoined
attribute phrase splits: only the part whose baseline the result reports
qualifies it. Sensitivity alone establishes no moisture baseline; product-linked
sensitivity remains reaction or tolerance context, while dry or dehydrated
context may qualify moisture. Later context may narrow an earlier judgment but
never silently replace it. Every returned field must be supported by the source
or supplied context.
Historical verifier-v1 stages remain hash-distinguishable and are not relabelled
as verifier v2.

Contract v25 versions the row-verification manifest to v2 and binds the exact
verifier method version and method-text SHA-256 into the active compilation.
Every reconciliation and finalization entry point that consumes that compilation
re-checks both fields against the current method. A missing, legacy-v1,
substituted, or rehashed mismatched manifest therefore fails closed instead of
letting a stored compilation inherit current verifier authority. Historical
manifest-v1 compilations remain historical artifacts and require a fresh
row-verification application before current reconciliation. The stage and
response schemas do not change.

Contract v26 versions the whole-row verifier method to v3. When an attribute is
not retained as a result's condition, the verifier must also omit that attribute
from the result statement; it may preserve the attribute separately only when
the source separately links it to a product response, in which case that
qualified meaning must not disappear merely because it does not condition the
neighboring result. This closes the path by
which a structurally correct condition list could coexist with an overbound
sentence. Current calibration may consume a provenance-bound row-verified
compilation for a slice. The evaluator first rebuilds the primary compilation
from the pinned responses, then requires the verified manifest to cite that
exact compilation and preserve its raw-response lineage before grading the
verified rows or their reconciliation. A compilation supplied as the verified
one but carrying no row-verification manifest is rejected, not graded. A
method-v7 slice fails closed when no verified compilation is supplied; only
historical-method slices without a supplied verified compilation retain the
historical evaluation path.

Contract v28 versions the whole-row verifier method to v4 and makes correction
preserving by default. A replacement remains a complete row, but it is not a
fresh regeneration: every proposed meaning and field that the source supports
must survive, and the verifier's reason must identify any source-based removal,
change, or addition. Drying, becoming drier, loss of moisture, and non-drying
belong to `hydration_and_moisture`; burning, irritation, peeling, breakout, or
damage belong to `reaction_and_breakout`, and drying severity alone does not
move a moisture claim into reaction. A unit solely about an adjacent or
comparator product cannot bind the target product unless it states a relationship
to the target. Named-shade behavior follows the shade rule above. Historical
verifier-v3 manifests remain identifiable by their pinned verifier-v3 text but
cannot authorize current reconciliation; they must replay row verification and
are not relabelled as verifier-v4 output.

Contract v29 versions the same whole-row verifier method to v5. Its final
completeness pass maps each independently usable source meaning to exactly one
unit and maps every unit back to supported source meaning. A paired comparison
may yield a separate relational meaning only when the source establishes the
same dimension and direction on both sides; proximity alone cannot create it.
Supported adjacent-product meanings remain under their own subject. A customer
attribute qualifies a result only when it is the directly relevant baseline or
the source explicitly scopes the result to it. It becomes a separate
bound-product response only when the source explicitly identifies that product
as causing, worsening, changing, or eliciting the response; ambiguous antecedents
and vague category wording remain context. This adds no response field, second
verifier, parser, phrase table, conclusion, or recommendation. Historical
verifier-v4 manifests remain hash-identifiable but require replay before current
reconciliation or calibration.

Contract v30 versions that verifier method to v6 and closes the overcorrection
found by its first blind replay. Ambiguity in one clause cannot discard supported
unambiguous meanings elsewhere in the row. When a variant referent is genuinely
ambiguous, the verifier may retain the uncertain meaning only at the verified
shared-product scope; it cannot select a variant. An ambiguous echo remains
axis-free and detail-free rather than importing one possible parent predicate.
Variant-specific behavior cannot broaden to the whole product family, and an
explicit overall evaluation remains separate from specific attribute facts and
from a disposition reason. Whole-row unresolved remains available only when no
safe complete row exists. This adds no response field, parser, second verifier,
or conclusion surface. Historical verifier-v5 manifests remain identifiable but
require replay before current reconciliation or calibration.

Contract v31 versions the verifier method to v7 and corrects referent scope.
Pronouns, omitted subjects, and evaluation scope resolve from the whole leaf and
its supplied parent context rather than the nearest named option alone. A named
option may establish ownership or experience without narrowing every later
product evaluation to that option. Explicit ownership remains separately
visible, while the option is not copied automatically into later conditions.
Earlier extraction examples identify separate meanings but do not decide their
referent scope. This adds no variant catalog, response field, parser, second
verifier, conclusion, or full-corpus resume authority.

Contract v32 versions the verifier method to v8 and closes the two residuals
found by the four-comment delta replay. A reaction-susceptibility trait does not
by itself become a hydration baseline; a neighboring hydration result remains
unconditioned unless the source links that trait to hydration. Explicit loss,
absorption, or waste of usable product remains `value_and_quantity` evidence
even when the mechanism is a tool or texture, and it stays separately usable
when its truth can vary independently. This adds no category registry, response
field, parser, second verifier, conclusion, or full-corpus resume authority.

For method v7, `personal_agreement` may remain support for a bounded meaning but
never adds a credited independent origin and must not be described as another
first-hand customer. This is enforced both in reconciliation instructions and
in deterministic final claim-support projection. Historical semantic methods
retain their frozen output behavior.

Two boundaries of that intake are stated because they are not obvious from the
rule above. Versioning the verifier method to v3 also retires every
method-v2-verified compilation: the manifest binds the exact method version and
method-text SHA-256, so a v2-verified compilation requires a fresh
row-verification application before current reconciliation or calibration, on
the same terms v25 set for manifest-v1 artifacts. The cold-repeat lane accepts
the same provenance-bound verified-compilation shape under the reserved
`cold-repeat` slice id. It rebuilds the raw cold compilation, requires the
supplied verified manifest to cite that exact input, and grades the verified
cold rows. Method v7 requires this like-for-like verified repeat whenever cold
repeat is configured; a missing or mismatched verified cold compilation fails
closed. Historical methods may compare raw primary and raw repeat, or verified
primary and verified repeat, but never mix those lineages in one consistency
judgment.

When a captured-but-excluded denominator exists, the completion profile draws
a deterministic bounded semantic audit sample per screening family. One
load-bearing missed class reopens that family rather than licensing a passing
seal from the original screen.

Route 1.6 uses a stronger, explicitly selected profile. Its declared corpus is
the union of unique source-native items captured inside the final Phase A scope
and cutoff, not only items nominated by an earlier lexical or axis screen.
Every captured item ends as:

- `assess` — usable captured text read semantically;
- `mechanically_excluded` — excluded by a deterministic reason such as an
  exact duplicate, wrong cutoff, corrupt body, or non-text object; or
- `blocked` — required text, artifact, or material conversational context is
  unavailable.

The compiler keeps captured, assessed, mechanically excluded, and blocked
counts separate. A blocked item prevents a complete Route 1.6 view. This
full-captured-corpus profile is not silently weakened into the historical
screen-plus-audit profile. A bounded regression slice may exercise Route 1.6
mechanics, but it is not seal-eligible as a final-acquisition corpus.

## Containers, context, and capture envelopes

Leaves remain the claim-bearing evidence items. Containers preserve context
and supply a separate count dimension:

- one Reddit root plus its captured replies is one conversation container;
- one creator post plus captured audience comments is one creator-conversation
  container;
- each retailer review is one retailer-review container; and
- each PDP, owned post, advertisement, editorial item, or measured object is
  one published-object container.

Each container records captured-leaf count, source-visible total or
`unavailable`, completeness posture, capture time, and the exact capture
boundary. A claim may therefore say that support appears in seven containers
without pretending those containers are seven independent people. When an
oversized conversation is split across semantic prompts, every reply travels
with references to a context table in that prompt containing the root and
captured immediate-parent chain needed to interpret it. Shared context text is
rendered once per work unit rather than copied into every reply row.
Missing or truncated context remains visible and may force `unresolved`.

Origin counts are conservative credited-public-origin counts, not unique-person
counts. A source-scoped visible handle may receive origin credit. Exact
normalized public-handle matches across venues are treated as a possible same
actor and receive one combined credit; they never prove that the accounts are
the same person. Different visible handles may count as apparently distinct
public origins. Missing or hidden identities remain unavailable and receive no
independence credit. This identity handling is deterministic; the semantic
agent does not decide it.

## Axes and propositions

Axes are organizing questions; propositions are the specific bounded meanings
supported or opposed by evidence.

- One proposition may bind multiple existing axes.
- One evidence item may emit multiple meaning units.
- Reusing one evidence item across axes does not create another independent
  origin.
- Existing axes guide interpretation but do not cap discovery.
- An `emerging_axis_candidate` is not automatically promoted into the axis
  inventory. Before a passing seal it is either reconciled into the inventory,
  dispositioned as bounded nonmaterial, or blocks as material.

Route consumers reference proposition IDs. The integration view owns the
claim-support block. Any inline display of that block is a derived projection,
not a second authority, and must not diverge from the referenced proposition.

## Versioned interfaces

`semantic_evidence_bundle_v1` binds the cycle/question, current axes,
hash-pinned source artifacts, admitted normalized evidence units, source-family
denominators, method hash, stable batches, corpus hash, and bundle hash.
It remains reproducible for historical artifacts.

`semantic_evidence_bundle_v2`, selected by
`semantic_evidence_source_v2`, additionally requires at least one normalized,
`product_context` row for every admitted evidence unit. Each row cites one of
the bundle's hash-pinned `source_artifacts`; free-standing analyst context is
not admissible. The bundle binds
`semantic_evidence_integration_method_v2`. The v2 method treats product
candidates as hypotheses and fails closed when text plus context cannot bind
the exact product. A v1 bundle cannot satisfy a new route-1.5.0 seal.

`semantic_evidence_batch_response_v1` is agent-authored. It accounts for every
alias and emits zero or more meaning units with precise subject, comparator,
axis, emerging-axis, and condition bindings.

`semantic_evidence_reconciliation_response_v1` is agent-authored. It groups
meaning-equivalent units into bounded propositions, records support/counter/
adjacent relations, states whether opposition was checked, and dispositions
every unused meaning unit.

`semantic_evidence_integration_view_v1` is compiler-authored. It carries final
coverage, propositions, claim-support blocks, emerging-axis candidates,
unmerged meanings, source/method/corpus bindings, and its own content hash.

Route 1.6 adds, without changing the historical interfaces above:

- `semantic_evidence_source_v3` — final-corpus scope/cutoff, container
  registry, capture envelopes, and one accounting row per captured item;
- `semantic_evidence_bundle_v3` — the normalized v3 corpus, actual rendered
  UTF-8 prompt-byte ceiling, and exact source/container/item denominators;
- `semantic_evidence_integration_method_v3` — leaf-with-container semantic
  assessment and bounded hierarchical reconciliation;
- `semantic_evidence_batch_response_v2` — semantic posture, uncertainty,
  polarity, exact product/version binding, and container-linked leaf output;
- `semantic_evidence_reconciliation_response_v2` — child-referenced semantic
  nodes, terminal claim metadata, unmerged children, and explicit emerging-axis
  consolidation; and
- `semantic_evidence_integration_view_v2` — compiler-flattened leaf lineage,
  capture-envelope accounting, evidence-item/container/origin/source-role/
  engagement counts, reverse indexes, and terminal consolidated axes.

Contract v7 adds `semantic_evidence_bundle_v4` and
`semantic_work_unit_projection_v1` without changing source v3, batch-response
v2, reconciliation-response v2, view v2, or evidence-packet v1 semantics.
Bundle v4 stores each assessable evidence row once, keeps captured accounting
as references to those rows, stores repeated context once in a hash-bound
context registry, and binds a bijective work-unit projection over the exact
assessable denominator. Every work unit carries one explicit agent-authored
disposition per assessable evidence row. Historical bundle v3 construction
remains explicitly reproducible; new full-corpus preparation defaults to v4.

Contract v8 adds `phase_a_semantic_integration_run_v2` and
`semantic_evidence_integration_method_v4` for run-local product identity and
cross-source customer-evidence proof. A v2 run binds each stable product ID to
a human-readable name, source-native product IDs and aliases, and one or more
hash-pinned authority artifacts. One source-native ID or alias cannot map to
two stable products in the same run. This is a run-local identity table, not a
global product registry or a claim that similarly named variants are the same.

Method v4 retains method v3 accounting and reconciliation semantics. It adds
one product-binding rule: source-pinned stable identity controls which product
owns an experience; a different product named inside the text is a comparator,
adjacent subject, or unresolved mention unless the evidence and context
establish otherwise. Meaning-equivalent customer experience may reconcile
across community and retailer-review roles when stable product, direction,
conditions, and uncertainty are compatible. Source roles and origins remain
separate. Method v4 adds no conclusion, recommendation, prevalence estimate,
provider API, embeddings service, or campaign-evidence bridge.

Contract v9 carries that verified run-local identity table into every method-v4
final-acquisition work unit as one hash-bound `product_identity_catalog_v1`.
The catalog is vocabulary, not evidence and not an automatic classifier. A
worker still binds each Reddit body or comment from its own text plus supplied
thread and parent context; a retailer review remains owned by its product page.
One thread may therefore contain different product subjects, and one comment
may yield separate subject/comparator meanings without creating extra customer
identity credit. A missing, altered, conflicting, or authority-unbound catalog
fails before final-acquisition prompts are accepted. Bounded historical proof
sources remain reproducible without acquiring the new final-run obligation.
Catalog v1 verifies product identities but carries no verified variant
vocabulary. Catalog-backed responses therefore keep `product_version_ids`
empty and preserve variant or formula wording in the bounded statement and
conditions. A later catalog revision is required before variants may become
durable cross-leaf identities.
The verified-catalog claim applies to the sanctioned source materializer that
derives this catalog from the bound run spec. A directly hand-authored
final-acquisition source is only internally self-consistent; until the runner
binds it back to a run spec, it must not be described as spec-verified.

Contract v10 adds a separate semantic generation for full-corpus execution:
`phase_a_semantic_integration_run_v3`, `semantic_evidence_bundle_v5`,
`semantic_work_unit_projection_v2`,
`semantic_evidence_integration_method_v5`,
`semantic_evidence_batch_response_v3`, and
`semantic_evidence_batch_compilation_v3`. Source v3, product identity catalog
v1, reconciliation response v2, node compilation v2, integration view v2,
evidence packet v1, and every route and seal version are unchanged. The
generations are mutually exclusive and fail closed in both directions: method
v5 requires bundle v5, bundle v5 requires method v5 or its versioned semantic
successor, and a response or
compilation from the wrong generation is rejected rather than coerced. The
legacy v4 generation remains readable, validatable, and byte-reproducible; its
paused artifacts are never mutated, restamped, migrated, or reinterpreted.

Method v5 requires exactly one context-aware relevance and accounting judgment
for every assessable leaf, made after reading the leaf with its parent,
container, and product context. A uniquely bounded direct or referential
in-scope proposition receives detailed processing, normally `claim_bearing`.
An ambiguous referent, product, variant, formula, or proposition receives
detailed `unresolved`; ambiguity is never routed to a cheaper `out_of_scope`.
A leaf clearly established as outside the governed semantic scope may
terminate as `out_of_scope`. A leaf clearly inside the relevant context that
carries no bounded proposition once that context is read may terminate as
`context_only`. No lexical phrase blacklist, keyword relevance gate, or length
rule is permitted. Context may resolve an omitted referent or predicate, but it
cannot donate an attribute or axis. Generic approval or dislike remains
`context_only` when context supplies only the product. A reply that uniquely
adopts a bounded parent complaint, comparison, behavior, preference, product
choice, condition, or variant remains detailed. For example, in the chain
`which is your favorite?` -> `Vanilla Beige!` -> `My fav!`, the final reply
adopts the Vanilla Beige preference; it is not an empty reaction.

Referential agreement uses the `personal_agreement` posture and does not
inherit the parent's first-hand experience. When a distinctly credited reply
actually asserts the same bounded proposition, it may contribute that actor's
same-thread recurrence under the intelligence claim-support contract. Bare
agreement is low-information recurrence: it adds no reason, attribute, axis,
condition, or explanatory detail. A reply such as `same` adopts only the
clearly targeted bounded meaning; it does not silently adopt every clause of a
multi-point parent. The shared thread remains disclosed and cannot earn
cross-venue credit. A reply that merely repeats or reports the parent remains
`attribution_or_echo` and adds no independent origin. Bounded variant or formula wording stays detailed
while catalog v1 keeps `product_version_ids` empty; ambiguous variant or
formula binding is detailed `unresolved`.

Contract v21 adds `phase_a_semantic_integration_run_v4` and
`semantic_evidence_integration_method_v6`. Method v6 deliberately reuses
bundle v5, projection v2, batch response v3, compilation v3, reconciliation
response v2, view v2, and evidence packet v1. It changes semantic instructions,
not transport or durable evidence shape. Method v5 text and historical outputs
remain hash-distinct and reproducible; a run must explicitly select method v6.

Method v6 preserves the complete meaning of each leaf before deciding how to
split it. It keeps explicit causal and explanatory links in the statement that
they qualify. It may keep connected ownership and habitual-use behavior in one
truth-complete statement when that is what the author expressed, but it never
turns quantity owned into a purchase count or a verified repurchase. Axis
assignment follows the whole outcome and direction, not an isolated symptom
word: healing pre-existing dryness or peeling is hydration/repair, while
product-caused or product-worsened irritation remains reaction. Named shade
selection, ownership, or preference may carry `shade_and_color_fit` without
inventing a reason such as undertone or complexion fit.

Contract v22 versions the semantic-calibration adjudication ruler separately
from the extraction method. New preparation receipts and reports carry the
ruler's stable ID and full SHA-256. Evaluation accepts only exact known ruler
hashes, binds a new receipt to its sidecar, and rejects an unknown or substituted
ruler. Historical preparation-v1 and report-v1 artifacts retain their original
shape and hashes; they are not rewritten to claim the new binding.

Contract v23 adds `phase_a_semantic_integration_run_v5` and
`semantic_evidence_integration_method_v7`. Method v7 keeps method v6 extraction
rules and the existing bundle/response/compilation/reconciliation/view
transports. Its new execution obligation is the hash-bound whole-row check
described above. An unverified compilation may still reproduce historical v5
or v6 behavior, but method v7 reconciliation and finalization fail closed until
the verification manifest is present and valid.

Contract v74 adds `phase_a_semantic_integration_run_v6` and
`semantic_evidence_integration_method_v8` for current authoring. Method v8
keeps method v7 meaning rules, row verification, bundle v5, projection v2,
compilation v3, reconciliation, views, and packets. It changes only the raw
batch-response transport: every expected evidence ID is an exact required key
under `decisions_by_evidence_id`, and the value contains that row's disposition,
reason, and semantic units without repeating the ID. The per-batch provider
schema is derived from immutable work-unit membership, written beside the
prompt or execution pack, hash-bound in the pack manifest, and rejects missing,
foreign, or repeated identities before semantic compilation. This adds no
provider call and no semantic rule. Historical run v5 / method v7 artifacts
retain response v3 grouped replay and are never silently reinterpreted as keyed
responses.

Contract v75 adds `phase_a_semantic_integration_run_v7`,
`semantic_evidence_integration_method_v9`, and keyed response transport v2.
They preserve method v8 meaning and keyed identity while moving one already
deterministic impossibility into the per-row provider schema:
`personal_agreement` is unavailable when the immutable evidence row carries no
parent-context reference. Rows with supplied parent context retain the posture.
The ordinary validator still rejects the same impossible combination after
generation; the schema now prevents it before token-consuming output is
accepted. Historical method v8 / keyed transport v1 schemas and responses
remain replayable under their original execution identity.

Contract v76 adds `phase_a_semantic_integration_run_v8`,
`semantic_evidence_integration_method_v10`, and keyed response transport v3.
They preserve v9 semantics and posture restrictions while requiring at least
one cataloged `subject_product_id` in every semantic unit at the provider
schema boundary. This mirrors the longstanding compilation validator and does
not infer, select, or repair a subject. Historical method v9 / keyed transport
v2 schemas and responses remain replayable under their original identity.

Contract v77 adds `semantic_evidence_row_verification_method_v9` and makes
response transport stage-local. The keyed `decisions_by_evidence_id` rule is
rendered only for the initial semantic batch surface that owns that schema; it
is omitted from row verification, targeted audit, and reconciliation prompts,
which retain their own response shapes. This removes contradictory response
instructions without changing semantic policy, adding a provider call, or
rewriting historical row-verifier v8 text.

Contract v78 adds `phase_a_semantic_integration_run_v9` and integration method
v11, retaining keyed transport v3, required subjects, and row-owned posture
restrictions. Method v11 pairs with row-verification method v10; historical
integration methods keep verifier v9. Current extraction, verification, targeted
audit, repair, and reconciliation prose names semantic concepts instead of
hard-coded example axis IDs. This corrects an observed Dieux prompt/inventory
mismatch; it is not evidence that the mismatch caused the provider timeout or
that latency or semantic quality improved.

Contract v80 adds run v10 / integration method v12 / verifier v11 without
changing keyed transport v3 or adding a provider stage. Explicit overall
evaluations survive as separate axis-free meanings; independently retrievable
attributes remain separate, qualifications stay attached, and an explicitly
stated reason remains attached to the behavior it explains. Verification checks
each unit before accepting the row rather than presuming the proposal correct.
These are semantic duties, not deterministic guarantees. Current-policy
readiness still requires the existing calibration and cold-repeat proof.
Historical integration v5-v11 and verifier v10 prompt bytes remain unchanged.

Calibration reopening retains producer-derived prompt metadata (including a
keyed response schema) while reading the actual saved prompt bytes. An altered
saved primary or cold prompt still fails at the prompt-identity boundary. This
loader repair changes neither the provider answer nor its semantic judgment.

When one leaf evaluates two alternatives on the same attribute, the relative
comparison remains evidence even if the observations occupy separate
sentences. A context-adopting reply keeps a parent's named-shade preference and
shade axis. Physical thickness, viscosity, or feel remains a texture outcome
when a formula is merely the comparator; formula consistency requires an
actual formula identity, change, or resemblance. Generic ingredient or
category nicknames do not establish an exact catalog product without a bound
alias or resolving context. Negative behavior stays logically negated unless
the statement is rewritten as an exact positive equivalent without retaining
the negative clause. An asserted desire remains affirmed even when it exposes
an unmet product attribute. A nearby preference supplies no reason, axis, or
comparison unless the source explicitly connects them.

Explicit contrast wording does not override atomicity. Independently testable
material sides stay separate and opposite directions are not bundled. Preserve
an explicit overall approval as its own axis-free meaning; do not infer a
specific product benefit from it. Historical prompts that discarded generic
approval are not the current authoring instruction.
Qualifications follow the same atomicity rule. This narrows the
meaning-preservation rule without weakening its causal, explanatory, or
connected-behavior cases.

A customer attribute may qualify a result when its meaning makes the attribute
relevant; an explicit causal phrase is not mandatory, but mere proximity is
insufficient. Non-worsening dryness is bounded hydration evidence rather than
proof of strong hydration. Product category, experienced category, price/value,
and attribute performance remain separate meanings unless the leaf explicitly
connects them. An unconsolidated semantic unit is not unimportant: it stays
retrievable with provenance unless deterministically dispositioned under the
existing rules. These clarifications add no score, high-value-comment
classifier, phrase table, second semantic pass, provider API, recommendation,
or conclusion.

Evidence posture describes how a leaf supports its unit, not whether its verb
sounds like an action or plan. A customer's own purchase, use, return, reach,
repurchase, or stated purchase intent is `first_hand`. `strategy_statement` is
reserved for company, creator, or other organizational strategy; it never
relabels customer shopping or use behavior.

Every atomic `statement` remains truthful when read without its structured
fields. Logical negation such as `not` and `never`, and comparative ordering
such as `less`, stay in the statement; `polarity` repeats the statement's
logical assertion form and never supplies or reverses words omitted from the
statement. A directly asserted comparison such as `A is less moisturising than
B` is `affirmed`: `less` carries comparative ordering, not logical negation.
`A is not as moisturising as B` is `negated`. Subject and comparator roles plus
the complete wording carry the comparison's direction. A support child and terminal
`bounded_meaning` have compatible direction. A negated child may validly be
`counter` to the inverse positive meaning, but it may never support that
positive meaning. `meaning_direction_preserved` adjudication checks the child,
relation, and terminal wording together.

Every detailed leaf is decomposed into the smallest complete set of atomic
meanings. Meanings that can be independently true, or differ in product, axis,
behavior, comparison, condition, polarity, or posture, remain separate; a
condition stays with the proposition it qualifies. Axis candidates provide
vocabulary only. Each assigned axis must be semantically supported by the
atomic unit and leaf; context may resolve a referent but cannot donate an axis.
Generic approval embedded beside a bounded judgment is absent from the atomic
statement: `good, but not worth $24` yields only `not worth $24`, never one
mixed-direction unit. A leading yes/no reply retains the exact predicate of
the parent question and its own qualification. Ownership is preserved as
behavior and remains separate from a conditional future purchase. Thus `I
have Poppy` and `would get it only on sale` are distinct atoms. Different
hydration truths also remain distinct: `not the most hydrating` does not absorb
`does not make lips drier`. Every explicit contrast in a two-product passage
remains present, including a hydration contrast stated through the comparator
and a separate target non-sinking claim when both are expressed. `More like a
gloss than a balm` is an axis-free category judgment unless the leaf separately
states a texture attribute.

Logical polarity repeats the statement's assertion form: `not the most
hydrating` and `does not make lips drier` are negated even though the author
affirms that those statements are true. Direct `less` or `more` comparisons are
affirmed when asserted without logical negation; their lower or higher ordering
remains explicit in the statement and product roles. Calibration field
`statement_direction_supported` judges source entailment of that complete
direction and polarity consistency, not sentiment or whether the comparison is
favorable. `Worsens peeling` carries
`reaction_and_breakout`; not-drying alone carries hydration, not reaction.
Bare ownership, quantity owned, and go-to behavior are axis-free unless a
separate attribute is stated; named shade ownership remains the accepted
shade-axis exception.

An `attribution_or_echo` unit's standalone statement names the attribution; the
posture field cannot carry words omitted from an otherwise first-hand-sounding
sentence. A shade-ownership unit carries `shade_and_color_fit`. `I have the
Poppy flavor` is an ownership atom, while `reaches for other formulas` is an
affirmed switching behavior rather than a negated target-use statement.

For bundle v5 reconciliation, each candidate carries its exact set of leaf
evidence postures through every level. The prompt exposes that set, and level
validation rejects `customer_experience` or `reported_behavior` terminal proof
when any supporting posture is not `first_hand` or `personal_agreement`.
`strategy_statement` is routed as `actor_strategy`. This check occurs before
finalization so a known impossible claim-kind/posture combination cannot spend
another level or masquerade as a valid node compilation.

Reconciliation must expose conflict and exact agreement, not merely keep their
leaves somewhere in the view. When opposite experiences address the same
bounded proposition, the opposing child is linked as `counter` rather than
emitted only as a second support-only proposition with `none_observed`
conflict. An exact `first_hand` preference and a distinct actor's
`personal_agreement` may support one bounded proposition while preserving both
actors, postures, and shared-thread provenance.

After a leaf is validly classified as terminal `context_only` or clearly
established `out_of_scope`, it incurs no bespoke extraction, semantic-unit
construction, axis assignment, reconciliation candidacy, proposition
rewriting, or downstream evidence-packet delivery. The unavoidable cost per
leaf remains loading it with its necessary context, making the one
meaning-aware judgment, and publishing its exact evidence ID under an explicit
terminal disposition.

Batch response v3 carries two explicit populations: detailed evidence records
and terminal disposition groups. `claim_bearing` and `unresolved` are always
detailed. `context_only` and `out_of_scope` may be grouped only when every
listed leaf has already been contextually judged eligible and they genuinely
share one disposition and one semantic reason; a nuanced or singleton terminal
judgment may remain detailed. Each group carries an ordered, explicit evidence-ID
list and one agent-authored reason. Grouping is response transport compression:
there is no implicit remainder, default disposition, wildcard, exclusion
filter, omitted-ID behavior, sample, or semantic census. Raw response v3 is the
durable agent-authored artifact of record.

Raw evidence-ID occurrences are validated before any dictionary or set is
constructed, so a duplicate cannot be masked by collapsing: no duplicate inside
one group, none across groups, no overlap between grouped and detailed records,
no unexpected ID, and an exact union with the work unit's expected IDs. Only
then is the response deterministically expanded into the normalized
one-row-per-evidence-ID representation existing validation consumes. Expansion
preserves every original evidence ID, its disposition and reason, and the
bundle's immutable source text, context references, product bindings, and
provenance; it emits rows in expected work-unit order, fails closed on
malformed, duplicated, missing, or unexpected identifiers, and never
deduplicates silently.

Deterministic expansion must not erase the identity of the raw response-v3
artifacts. Batch compilation v3 binds the exact accepted response set through
canonical raw-response hashes in a deterministic sorted manifest. The compiled
semantic representation may remain expanded, but its lineage proves which
durable raw grouped responses produced it, and downstream reconciliation
rejects a compilation v3 that lacks that lineage.

The keyed response transport is the current-authoring replacement for response
v3 grouping, not a new evidence model. Transport v2 also removes
`personal_agreement` from a row's allowed posture enum when that row has no
supplied parent context; it does not choose a replacement posture or infer the
row's meaning. The keyed transport removes the model-authored task of
copying identifiers into rows or terminal groups: the provider must fill one
already named object slot per expected evidence ID. Deterministic normalization
then produces the same one-row-per-evidence representation consumed by
compilation v3. Exact membership, source text, context, product binding,
provenance, and raw-response hashes remain unchanged obligations. Grouped
response v3 remains supported only when the bound historical method identity
requires it.

Projection v2 binds semantic execution identity: source, corpus, and catalog
bindings; the selected method v5, v6, v7, or v8 identity and hash; response-schema
version; prompt-encoding
version; exact work-unit membership; evidence and context references; prompt and
leaf caps; and complete assessable-denominator coverage. It must not encode a
worker count or static worker partition, because who executes a work unit is a
controller runtime decision, not part of semantic identity. The new generation
keeps the existing pretty, indented JSON prompt encoding, bound by name so a
later compact encoding cannot silently reuse a projection packed under this one.

Contract v33 adds an optional `semantic_prompt_execution_pack_v1` transport for
long-lived workers. It stores the method, response shape, axes, and product
catalog in one hash-bound shared frame and stores each work unit's exact context
table and evidence rows in a separately hashed payload. Every payload must
reconstruct the existing standalone prompt byte-for-byte before it is usable;
the bundle, method, response, compilation, work-unit, prompt ceiling, and
evidence-accounting identities do not change. Context remains batch-local in
v1 because exposing neighboring context or relying on model memory would change
the judgment surface and requires separate calibration. The pack is execution
transport only: it adds no static worker topology, provider API, semantic cache,
evidence filter, or resume/readiness claim.

The reconstruction target is the rendered standalone prompt string that batch
prompt building already produces, not the `prompts/<batch_id>.md` file the
standalone preparation route writes. The rendered string is the canonical
model-facing prompt and the prompt-ceiling input. The file writer appends one
trailing newline as a storage delimiter, so a reconstructed prompt is exactly
one byte shorter than the corresponding stored `.md` artifact. Byte-for-byte
reconstruction is asserted against the canonical rendered string; consumers
that deliberately submit raw `.md` file bytes also submit that storage newline.

Pack verification is bundle-relative and exclusive, not self-proving. It
regenerates the frame, manifest, and payloads from the originating bundle,
compares them to freshly read stored bytes, requires the stored file set to be
exactly the frame, the manifest, and one payload per named work unit, and
re-runs reconstruction on each freshly parsed payload because a hash over
canonical JSON cannot see the key order that prompt bytes depend on. Without
the originating bundle the pack proves nothing; the reported stored-byte total
and reduction cover exactly that verified file set. A batch id must be one safe
path component, since it names the stored payload file. The pack carries no
model call, and no observed latency change is attributed to it.

For the new generation the controller verifies the immutable bundle and
projection once per invocation and reuses that verified context across all
response validation in that invocation. Status reports global expected,
accepted, staged, invalid, and missing work-unit state; it reports no static
worker partitions, and the legacy partition report remains only on the
projection-v1 path. The global missing-work list is the repository interface
consumed by the invoking controller. Any active assignment bookkeeping belongs
only to that controller's in-memory execution state; this contract installs no
repository scheduler or otherwise-unused assignment API. Deterministic atomic
no-overwrite publication remains the only durable truth boundary, and
publication collisions plus invalid or staged artifacts stay visible rather
than silently successful. No daemon, queue database, lease protocol, heartbeat,
persistent claim-marker system, persistent verification cache, new registry,
automated loser deletion, or response winner selection is introduced.

High-watermark repacking, larger prompt or leaf caps, persistent
method/catalog/context transport, compact prompt JSON, a two-stage semantic
census, additional worker infrastructure, and reconciliation redesign remain
out of this generation. Contract v10 adds no provider API, no semantic
calibration, no latency or token claim, and no route or seal obligation.

`build-product-axis-proof-source` creates a bounded regression source from an
already materialized full source by selecting the complete captured union for
one stable product and one or more exact axes. It replaces mapped source IDs
with the stable run ID, retains source-native context, and rejects lexical
mentions on pages bound to a different product. Its output is never a
final-acquisition corpus. Route 1.6 and 1.7 passing-seal requirements remain on
method v3 until an explicit later route revision adopts method v4; a v4 shadow
or proof cannot silently satisfy those historical obligations.

`phase_a_evidence_packet_v1` is a read-only projection from one finalized
`semantic_evidence_integration_view_v2`, its bound v3 bundle, and its bound
batch and terminal-node compilations. The projector first rebuilds the supplied
view from those inputs, preventing an altered semantic statement from being
paired with a valid view. It is the tail-end retrieval surface for Phase A evidence,
not another evidence authority or another closure job. A caller selects either
one or more exact proposition IDs or one or more exact axis IDs. When a caller
starts from a natural-language question, an agent interprets that meaning and
chooses the relevant IDs from the finalized view; deterministic code then
expands those IDs without a keyword or top-k cutoff.

The packet returns every distinct linked evidence item once, while preserving
all proposition/relation/semantic-unit links. Each linked semantic unit retains
its evidence posture, uncertainty posture, and polarity; accepted relations do
not lose qualifications that remain visible on unmerged material. It reports
the complete selected union of support, counter, and adjacent evidence,
container and independent-origin counts, the selected containers with their
capture boundaries, and any
axis-relevant unmerged or unresolved candidates. It also reports the complete
corpus unmerged denominator and returns unscoped unmerged meanings separately,
so an emerging-label meaning with no accepted axis cannot disappear from every
packet. Per-relation evidence counts are non-disjoint unions: one item may
support one selected proposition and oppose another. One
item supporting multiple propositions or axes remains one evidence item. The
packet binds the source view, bundle, both compilation hashes, and corpus hash.
It fails closed on unknown IDs, stale lineage, or inconsistent reverse indexes.

The packet contains bounded propositions only as retrieval labels. It does not
carry a conclusion, recommendation, importance ranking, prevalence estimate,
or causal judgment. Deliver may use the packet as evidence input but owns any
downstream conclusion. A changed corpus invalidates the source view and every
packet derived from it. The projection uses no provider API, embeddings,
vector store, or new persistent index.

Contract v35 adds `phase_a_evidence_packet_v2` as the default output of the
existing `project-evidence-packet` route. It preserves v1 selection, lineage,
coverage, and fail-closed rebuilding, but changes the model-facing layout. Each
admitted linked, unmerged, unscoped-unmerged, or unresolved evidence item
appears once in a source-grouped catalogue. A source group owns the repeated
source family, source role, engagement metric kind, and source-specific
engagement context; each evidence row retains its raw engagement value,
observation time, materiality observation, actor and independence data,
publication time, source reference, container reference, and the selected
semantic units. Each proposition carries only relation-to-evidence and
relation-to-semantic-unit references. Full evidence text and parent/product
context remain resolvable by `evidence_id` from the hash-bound bundle and are
not duplicated inline.

The catalogue has no evidence-count cap and no top-k admission rule. Source
grouping is presentation and transport normalization only; it does not merge
actors, platforms, source roles, meanings, engagement units, or proposition
relations. `phase_a_evidence_packet_v1` remains available only through the
explicit legacy packet-version route for historical reproduction. Contract
v35 made v2 the no-flag runner default; contract v36 below supersedes that
default while retaining explicit v2 reproduction.

Contract v36 makes `phase_a_evidence_packet_v3` the normal output. V3 is a
lossless transport projection over v2: repeated evidence, engagement, and
semantic-unit field names are declared once as explicit named columns, while
values common to every row in a packet or source group are declared once as
named defaults at that exact scope. Remaining positional values map to those
human-readable column names. Evidence IDs and semantic-unit references remain
literal, proposition relations remain explicit, and source-group headers still
own source-native engagement meaning. This is normalization, not abbreviation
or evidence selection.

Before v3 is returned or hashed, the projector reconstructs the expected
column/default layout from v2 and rejects any changed top-level payload,
source-group evidence row, or proposition relation. V2 remains available
through the explicit packet-version route as the matched comparison baseline;
v1 remains historical reproduction. The normal runner needs no new operator
step, lookup, or retrieval round.

Contract v37 changes only the downstream evidence-consumer protocol. The
packet remains `phase_a_evidence_packet_v3`. A no-provider prepare operation
may place proposition cases in one ordered decision batch only when their
packets bind the same corpus and bundle and their proposition relations share
evidence. Unrelated cases remain separate calls. The model returns only its
synthesis judgment and literal support/counter refs; it does not recopy
engagement, provenance, actor identity, dates, excerpts, relation inventories,
or resolution facts. A hash-bound manifest preserves exact case and
proposition order and the original packet/selector identities.

The no-provider finalize operation rejects missing, duplicate, shuffled, or
foreign case/proposition results and refs before deterministically reattaching
the source-owned rows and inventories. It reconstructs v3 named defaults and
positional columns, including source-native engagement and
`public_identity_key`, and fails on a missing lookup, wrong row attachment, or
malformed engagement posture. Preparation and finalization make zero model API
calls; an external fresh agent still consumes the emitted prompt and response
schema. This is call-overhead amortization plus deterministic rehydration, not
packet compression, evidence selection, a caching claim, or a new judgment
authority.

Contract v39 adds an optional no-provider selection-and-quote consumer over
one or more hash-bound v3 packets. It does not change packet v3 or the
authoritative semantic view. Admission is deterministic from explicit product
and axis membership or literal operator-nominated semantic/unresolved refs.
Current authoring uses selection spec v2 with explicit `point_actor_scope`:
source-local reports or an identified actor bound to a credited literal point
anchor by source ID and independence key. The completion path's paragraph
beginning `Fresh selections use` owns the operational shape and CLI route.
Both existing judgment exchanges receive the scope and row origin identity;
both reader surfaces preserve it unchanged. Deterministic code verifies the
identity and transfer, not whether the authored scope fits the source meaning.
Under source-local reports the input source ID is not a person identifier.
Read source-bound independence keys with their independence posture and
source-visible attribution; different keys alone do not prove different
people. Check origin overlap before describing opposed rows as separate
authors. One credited origin can appear on both sides; preserve its separate
observations without inferring conflict or refinement from identity alone.
Different people's opposed preferences do not disprove a particular person's
private state. Frozen selection spec v1 replay keeps its original scope
semantics; it is not fresh authoring and gains no default.
Current scoped specs may carry the completion path's inline
`phase_a_relation_adjudication_v1` exception input. It preserves an explicit
bounded judgment on an unchanged point/source/inventory/policy basis across
confirmation reruns, retaining the raw answers and all changed labels. The
semantic finalizer applies only the authored relation/reason to exactly matching
row-owned ref sets; it does not infer semantic correctness or select refs.
Missing, duplicate, foreign, or stale corrections fail visibly. The builder
and readers still only preserve and verify attachments, never settle meaning.
The record travels with the current spec; no machine-local locator or historical
adapter is part of the current authoring contract. Projection-field changes are
judging-policy changes and invalidate reuse; row order and batching do not.
An external response must label every admitted candidate exactly once as
support, counter, adjacent, or exclude before presentation selection begins;
missing, duplicate, foreign, reordered, and wrong-role rows fail closed at
response validation, and wrong-product nomination fails closed earlier at
admission. An operator nomination that cannot resolve — an `admit_semantic_ref`,
an `admit_unresolved` ref, a protected evidence ID, or an unrecognised protected
lane key — fails closed rather than being dropped. All dispositions and their
inventory hash remain in the completed artifact, including rows not displayed.
Every candidate also carries the other normalized meanings from its evidence
item as non-candidate context. Those companions cannot create another admitted
row or independent origin, but they prevent an isolated clause from hiding a
same-source qualification. In particular, a price-discomfort clause does not
become poor-value support when the same customer records purchase or repurchase
despite that price. A value selection binds `price feels high` separately from
`not worth it`; operator-observed purchase, repurchase, switching, return, or
abandonment that changes the reading uses the existing `costly_behavior`
protected-evidence lane rather than a new score.

Presentation caps independent origins, not underlying evidence. One selection
is one bounded evidence point, not one broad axis. The default is at most
thirteen customer truth-support origin groups per point; a selection may
explicitly bind a customer cap from one through twenty when protected evidence
or a material conflict cannot fit. Creator influence remains capped separately
at three and cannot consume or enlarge the customer cap. A raised cap is
selection-specific rather than a new global default. The earlier measured
full-axis Summer Fridays hydration selection bound fifteen and remains a
historical comparison artifact; new presentation runs split the broad axis into
bounded points instead of treating fifteen origins as one axis-wide pack.
Every explicitly nominated safety or costly-behavior origin is selected first;
if those origins alone exceed the bound customer cap, selection fails
`presentation_cap_insufficient`. The selector then reserves support and counter
only from materially positive or explicitly protected evidence; that reservation
is subject to the same cap check, so a protected set that fits the cap only until
the support and counter lanes are reserved also fails
`presentation_cap_insufficient` rather than dropping a required origin. Unprotected
zero, quiet, and engagement-unavailable rows remain accounted but are not forced
into the main display to fill a lane or venue. When no materially positive or
protected counter exists, no counter is displayed. The cap check follows every
addition. Each protected origin records its required display lanes, and the
display contains the deterministic minimum member rows that cover them. Every
operator-protected row is visible or selection fails closed. Unreserved origins
retain the compact representative-plus-distinct-row behavior over the
display-eligible set. The complete disposition inventory remains the accounting
record for displayed and undisplayed candidates.
Engagement orders rows only inside one source-native venue/role/metric bucket;
its literal stored value remains unchanged and there is no cross-platform
score. Venue is normalized per publisher across host variants and short links,
so one publisher cannot split into several display sections or ordering
buckets. A source-native value the runtime cannot read as a whole number — an
abbreviated or group-separated count — is treated as uncomparable and ordered
last rather than partially parsed. Mapping-valued engagement is accepted only
for an exactly recognized source-native engagement kind and shape; any other
mapping fails `unsupported_engagement_shape` rather than becoming an unknown or
generic score. A distinct relation or condition from the same origin may
receive another displayed quote without consuming another origin slot.
Creator-authored material is influence context and is
deterministically barred from customer support or counter relations; qualified
creator-audience comments retain their customer role.

Only selected display rows expose their source bodies to the existing external
quote response. Current v9 authoring presents stable token addresses inside
each deduplicated body. Every returned row is schema-bound to its selected row
and body and chooses an inclusive start/end token pair; deterministic code
copies the original contiguous source characters. Foreign bodies, foreign
tokens, reversed spans, transcription-shaped responses, and changed bodies fail
locally. This proves exact row/body transfer, not that a structurally valid span
is semantically adequate; context completeness remains a bounded quality
judgment. The bundle is content-verified against its own stored
`bundle_sha256` where it enters the trust boundary, and the finalizer follows
the packet's bundle hash to its literal evidence ID, requires exact
source-artifact and source-ref equality, and rejects a body whose hash differs
from the one the quote manifest recorded. An available source body of no more
than 220 characters must be quoted in full; this deterministic boundary prevents
a short comment from being clipped before a material qualification or
countervailing behavior. Under current v9 token addressing, quoted in full means
that body's first token through its last, because a token address cannot name
leading or trailing whitespace. Current v9 and historical v8 use that threshold only for short-body copying and
external-review workload selection, never as a semantic ceiling. A longer
available quote must be the shortest context-complete contiguous source
substring that carries the material meaning, with no inserted ellipsis or
rewriting, and must contain at least two Unicode alphanumeric characters. It may
exceed 220 characters when the necessary antecedent or qualification requires
it. The substring must express the display label through either the
selected normalized meaning or the same-evidence companion meaning that
justified that label. If no contiguous exact span carries the material meaning,
the external response returns unavailable instead of a misleading fragment;
length alone is not an unavailable cause in current v9 or historical v8. No lexical-overlap relevance
rule is applied. For historical v4/v5/v6/v7/v8 quote manifests, a long-body quote
that ends in an alphanumeric
character while the bound source continues with whitespace and another
alphanumeric character fails at `quote_boundary_incomplete`; this deterministic
check prevents an exact but mid-phrase span from silently satisfying the
context-complete contract. Current v9 does not apply that prose heuristic after
token-span selection: deterministic enforcement owns exact row/body/token
attachment, while semantic completeness remains explicitly not mechanically
proven. A typed
`quote_unavailable` covers two distinct cases: no source body yields
`source_body_unavailable`, while a present body with no returned exact relevant
quote yields `no_relevant_exact_quote_returned`. Available quotes carry a null
cause. Each displayed row also records `source_body_present`, and the
source-owned normalized meaning and same-evidence companion meanings remain in
all cases. Full-body enforcement closes context clipping for short sources;
semantic relevance and context completeness for longer sources remain a
quality-adjudication obligation outside the deterministic runtime. Both
prepare/finalize stages make zero provider calls and are deterministic and
idempotent.

For a large non-value selection, positional relation transport may be split
into hash-bound batches of at most 300 candidates. Each response is an object
carrying the required single-valued `batch_id` of the batch it answers, plus
required named `row_NNNN` properties that map to the zero-based candidate
positions in that batch and whose values are only support, counter, adjacent,
or exclude. It repeats neither candidate IDs nor free-text reason codes.
Because row keys restart at `row_0000` in every batch, `batch_id` is what makes
a response answerable by exactly one batch: without it two same-size batches
would share one schema and one interchangeable response, and a transposed or
stale response would finalize with complete-looking coverage and systematically
wrong relations. Finalization validates the batch-manifest hash, source and
candidate hashes, the exact batch set, contiguous complete coverage, each
response's own batch identity, and the exact required row key set before
deterministically reattaching literal candidate identities. Any missing,
foreign, or wrong-batch response, and any missing or foreign row, fails closed
before presentation selection.

Positional transport buys that failure visibility by giving up the
model-authored reason code. A batched row therefore carries a reason label
derived deterministically from its relation alone — one fixed label per
relation — not a code naming the evidence meaning. That label is the relation
restated, so a batched pack's row labels distinguish relations but not
meanings, and any consumer that reads a reason code or display label as source
meaning is reading a weaker signal than the literal-ID path supplies. Relation
authority, semantic admission, candidate identity, and the exact-quote
requirement are unchanged. The transport is unavailable for value selections,
whose relation-aligned vocabulary remains literal-ID based.

Policy guidance is a property of the whole selection, not of a transport slice:
every batch prompt carries the guidance derived from the complete admitted
candidate inventory, so a batch cannot acquire a policy lane the selection as a
whole rejected.

Batched quote preparation versions its durable output as
`phase_a_evidence_quote_manifest_v6`. It retains the v5 binding of the exact relation
batch-manifest hash, batch count, and one canonical response hash per batch.
The embedded selection manifest remains the canonical full-selection identity;
its single-prompt hash is not an execution receipt. The v5 transport binding is
the authority for which relation prompts and responses actually produced the
selected quote workload. Removing or changing that binding changes the manifest
hash and fails quote finalization.

Every v6 point pack also requires a separate selected-row relation confirmation
before quote finalization. V7 is the route for a frontier-bound point pack; the
non-frontier `finalize-evidence-selection-relations` and
`finalize-evidence-selection-batches` routes still stamp v6, so this obligation
is live for those packs and is not reproduction-only. The confirmation prompt contains only
the bounded point plus each selected row's source-owned meaning, conditions,
product/version scope, source role, and same-evidence companion meanings. It
does not expose the first-pass relation, reason code, display label, engagement,
or selection priority. Withholding selection priority is structural, not a
prompt request: selection order leads with protected and reserved
support/counter origins and always trails with the adjacent creator-influence
block, so the confirmation rows carry opaque `confirmation_row_id` handles and
are presented in a content-derived order keyed to the bound selected-row
identities. That order is deterministic and reproduces on re-preparation, so
the pass stays replayable without carrying the first pass into it. The
confirmation response must account for every confirmation row exactly once and
in order. Any missing, duplicate, foreign, reordered, or differently labeled
row fails closed; neither pass silently wins. The confirmation manifest is
re-derived from the bound quote manifest at finalization, so a hand-written
manifest cannot vouch for a workload that was shown the first-pass labels.
The same response must classify `bounded_point` as either `single_point` or
`broad_axis_or_bundle` and give a short reason. `single_point` means one
specific direction-bearing proposition about one material product attribute or
outcome under one compatible condition set. Merely naming an experience area,
or combining materially different attributes, outcomes, directions, or
conditions, fails at `bounded_point_not_confirmed`. This reuses the existing
confirmation call; it adds no third provider workload.
Quote extraction remains a separate response so relation checking cannot make
the quote task clip or omit source context. Historical v1/v3/v4/v5 manifests
remain finalizable under their stamped contracts and never acquire this new
obligation; one is finalized with no confirmation attachment at all, and
supplying one fails closed at `unexpected_relation_confirmation`.

Current Decision State consolidation is delta-based when a new point layout
regroups already judged evidence. `prepare-decision-state-reconciliation` pins
the current axis packs and templates plus the chosen historical specs. It may
reuse a Decision State judgment only for an unchanged source-owned semantic
identity consisting of evidence ID, semantic-unit ref, literal normalized
statement, axes, conditions, and polarity, and only when every matching prior
observation carries the same complete judgment bundle. Point ID, selected-row
ID, row order, axis placement, and relation are not semantic reuse keys. Because
current v4 rows address meanings by semantic ref, one evidence and semantic-ref
slot must resolve to a single current identity across every axis in the run; two
current axes carrying different content for the same slot fail closed rather
than silently resolving to one of them. New or changed identities, conflicting
history, and partial multi-ref state groups are the only units sent to the
existing bounded judgment boundary. That boundary describes the actor rather
than turning every product outcome into a state. Its current prompt uses
`expectation_judgment` only for explicit expectation, hype, skepticism,
surprise, disappointment, or underwhelming language; uses
`preference_judgment` only for an explicit evaluative or suitability judgment;
keeps other product attributes and observed outcomes as context; does not infer
acquisition from price or quantity; and does not infer use from ownership or
carrying. Carrying or keeping a product nearby is context unless ownership or
use is explicit. Commercial direction is relative to the preserved decision
object: a preference for A over B keeps the full comparison as a favorable
object, while an exact midpoint numeric rating is mixed absent another stated
direction. One atomic statement with separable explicit states emits each state
rather than hiding a state in conditions or collapsing the bundle into mixed.
`finalize-decision-state-reconciliation` requires exact coverage of those
unresolved identities, compiles complete current v4 Decision State bindings,
and validates the ordinary consolidation consumer. Current row-owned relation
refs remain point-relative and are copied only from the current v3 selection
artifact. This adds no third provider stage: a run with no unresolved identities
needs no model call, while a run with deltas judges only those deltas. The
manifest is a hash-bound run receipt, not a global semantic registry, ontology,
or independently writable evidence authority. Exact historical agreement proves
mechanical reuse eligibility, not semantic truth; bounded review retains the
right to challenge an old judgment.

The current point reader projects the exact meanings named by a displayed row's
`relation_semantic_unit_refs`. A selected row's primary meaning and quote remain
available as lineage, but they are not presented as the relation-owned meaning
when the relation binds only a same-evidence companion. In that companion-only
case the relation-facing quote is explicitly `quote_unavailable` unless a quote
span owned by that exact meaning was captured. This prevents a neighboring
selected-row quote from visually impersonating the meaning that supports,
counters, or sits adjacent to the point; it does not decide whether the chosen
semantic-reference subset is itself warranted.

Companion-owned semantic fields that the frozen projection does not carry remain
null and are listed in `unbound_meaning_fields`; they never inherit the selected
row's product/version, conditions, axes, polarity, statement, or uncertainty.
When primary and companion meanings are co-bound, the headline meaning is the
owner of the headline quote regardless of reference order. Both the point-reader
compiler and structured-reader validator use the same quote-ownership projection.
The latter accepts honest companion-only quote unavailability and rejects the
neighboring primary quote; this closes an existing consumer gap, not a new
semantic judgment stage.

The confirmation pass still shares the first pass's source role for each row,
because source-role competence is required input for the judgment rather than
leaked first-pass state. Creator-authored rows are constrained to `adjacent` by
deterministic code, so their confirmation carries no independent information;
the confirmation's discriminating power is over the customer truth rows.

Fresh selection manifests use `linked_parent_context_v1`. Exact parent text is
carried only for the point's explicitly admitted semantic refs, not for every
candidate admitted by an axis expansion. The provider-visible projection names
that text once in a compact context table and gives each applicable row its
context IDs; every point-scope confirmation batch receives the same table so
scope is never judged from a context-stripped point. Point-level visibility
does not attach the parent to unrelated evidence: a candidate may use parent
content for its own relation only through its own exact context ID. The full
exact context remains hash-bound in the candidate inventory. A terse agreement
or omitted referent may inherit meaning from that
linked parent only when the parent clearly supplies the same subject,
attribute or outcome, direction, and material condition. Thread proximity by
itself supplies nothing, and a vague phrase stays unresolved when its parent
does not name the missing meaning. Two effects may remain one bounded point
when the source itself presents them as one joined experience under the same
subject, direction, and conditions; this does not permit an actor to assemble
unrelated outcomes across sources. Manifests without the policy retain their
historical no-parent-context reconstruction.

The completed v6 artifact identifies its `point_id` and `bounded_point`, then
discloses candidate semantic-row count, distinct candidate evidence-item count,
candidate truth-origin count, displayed row count, displayed truth-origin
count, display-eligible truth-origin count, relation-specific displayed origin
counts, and displayed creator-influence count. These are evidence-accounting
counts, not customer prevalence. The v6 quote manifest records the truth
selection policy, and the finalizer applies that same policy predicate when it
counts the distinct origins eligible before the cap; the selector and the
reported denominator therefore cannot silently drift apart.
The complete candidate-disposition inventory remains attached, so the display
cannot imply that its selected rows were the whole source pool. The disclosed
candidate truth-origin count is the admitted pool, not the pool the cap chose
from: a truth origin with no operator-protected lane and no material positive
source-native engagement is never display-eligible, and the value-first policy
also excludes an otherwise material adjacent origin. The artifact reports the
exact `display_eligible_truth_origin_count` and its `presentation_basis` names
that pre-cap gate, so the candidate-to-displayed drop is not read as cap
pressure alone. Naming a runtime field `point_id` or `bounded_point` establishes
nothing about boundedness; the separately returned scope classification gates
the completed pack, and the artifact records the passing reason.

Contract v58 makes `phase_a_evidence_quote_manifest_v8` the normal route for a
new bounded point pack. It retains v7's de-correlated relation check before the
display cap. After the first response accounts for every admitted candidate,
the confirmation workload includes every customer-truth row with material
source-native engagement, every operator-protected row, and every influence
row. This frontier is derived without consulting the first-pass relation. A
first-pass `exclude` therefore cannot make a materially engaged or protected
candidate disappear before its relation is checked.

The confirmation prompt keeps the v6 hidden-label boundary: it exposes the
bounded point and source-owned meaning, conditions, product/version scope,
source role, and companion meanings, but not candidate identity, first-pass
relation or reason, engagement, or selection priority. It returns a relation
and relation-aligned reason code for every opaque row exactly once and also
confirms that the scope is one bounded point. Missing, duplicate, foreign,
reordered, malformed, or broad-scope responses fail closed. A confirmed value
reason must belong to the returned value relation. Unlike v6, a disagreement
does not merely reject a pack after selection: the confirmed relation and
reason replace that row's first-pass values, and the thirteen-origin selection
runs once over the corrected inventory. Every finally displayed row must be in
the confirmation frontier or finalization fails
`selected_relation_unconfirmed`.

V8 quote finalization verifies the hash-bound pre-selection confirmation
lineage embedded in the quote manifest and accepts no separate late
confirmation attachment. Quote extraction remains a separate external
response, so relation adjudication cannot encourage context clipping. V6
remains supported only for exact historical reproduction under its stamped
selected-row confirmation contract. V7 also remains readable and
reconstructible under its stamped 220-character ceiling; neither historical
version is silently upgraded or restamped.

Contract v53 also adds
`phase_a_customer_pull_point_frontier_v1`, a no-provider navigation view over a
complete non-truncated proposition-mode v3 packet. It accounts every selected
proposition matching the requested product subject exactly once and records the
identities and count of propositions excluded by that subject filter. The input,
matched, and filtered counts must reconcile, so subject mismatch cannot masquerade
as complete packet accounting. Retailer-supported customer points enter a
first-look queue because retailer reviews are closest to completed purchase;
community- or qualified-audience-only customer points remain in a separate
discovery queue and record retailer check-back as open. Retailer is not an
admission gate. Creator-authored material cannot supply customer support.
Points earn investigation through explicit reported customer behavior,
independent customer recurrence, material source-native engagement, or an
operator-protected safety/costly lane. Engagement remains comparable only
inside one role, venue, and metric bucket, and no cross-platform commercial-pull
score is created. Materializing one admitted proposition produces a v1
selection spec bound to the frontier, source packet, bounded point, candidate-
admission mode, axis set, transport mode, and literal semantic refs with the
normal thirteen-origin cap. A non-value point carrying an explicit axis admits
the same-product axis union plus its literal refs; every row is still judged
against the exact bounded point, so axis membership grants no relation. Value
points keep literal-ref admission under their separate value policy. The
frontier changes no packet, source fact, proposition relation, or Deliver
authority.

At full-axis scale, both relation passes use named batches. The first layer
accounts every admitted candidate. The second independently accounts every
material, protected, or influence row that could reach display, preserving the
v7 pre-cap correction boundary without one hundreds-row response array. Each
layer binds its own manifest, contiguous coverage, response hashes, and required
batch identity; the complete set is deterministically reassembled before the
ordinary v7 selector runs. Missing, foreign, transposed, malformed, or partial
responses fail before quote selection. Historical v6 batching and narrow v7
single-response replay retain their stamped behavior.

Axis-expanded non-value specs also bind
`temporal_presentation_policy=recent_year_coverage_v1`. The latest two literal
calendar years in the display-eligible pool receive representation across
available role/venue/native-metric buckets up to half the cap after mandatory
protection and direction reservations; one eligible dated pre-window origin is
retained when space remains. Undated rows remain fully accounted. This is a
presentation preference only: publication time never changes relation,
independence, materiality, or truth weight. Artifacts expose a neutral calendar-
year timeline and never label age strong, weak, fresh, or stale. Native
engagement still orders only within one comparable source bucket.
The timeline is an ordering index, not a freestanding evidence layer: consumers
must dereference each `selected_id` through `source_groups` and preserve its
`layer`; an `influence_context` row never becomes customer chronology merely
because it shares a calendar year with truth-support rows.

Within the retailer-first and community-discovery queues, more independent
supporting origins lead. When origin counts tie, cross-role independent
recurrence leads same-role recurrence, followed by the number of materially
engaged supporting evidence items. Reported behavior is retained as a separate
commercial strength dimension and breaks otherwise equal ties; it is not a
universal source-support rank and cannot make generic trial or ownership
outrank a more strongly corroborated point. This queue-specific order does not
turn the claim-support postures into a universal ranking. Materially engaged
items may share one origin; they add resonance context but do not add
independent recurrence. An unavailable engagement posture earns no
materiality, and engagement magnitude is never compared across venues. An
operator-protected safety or costly-behavior lane keeps a point admitted and
fully accounted, but protection alone grants no ordering priority.

The materialized spec uses `relation_policy=bounded_point`: relation direction
is evaluated against that proposition's exact wording. Thus an expensive-price
complaint supports an expensive-price point instead of being inverted by the
historical positive-good-value box. Existing non-frontier value selections keep
their `auto` value policy for exact reproduction.

A generic batched display label is never semantic authority for quote choice.
For a long source body, the returned exact substring must directly express the
source-owned normalized meaning or a material same-evidence companion
qualification. A relation-derived label alone cannot make an irrelevant
substring acceptable. The exact span must not start with an unresolved pronoun
when nearby preceding text names its antecedent.
Product identity may still rely on the evidence row; this pronoun rule does not
require an otherwise exact, relevant span to repeat it. Quote selection must
prefer a context-complete span over the shortest matching phrase and directly
substantiate every material outcome, direction, comparator, formula
distinction, and usage or timing condition in the normalized meaning. It must
retain a nearby material qualification and cannot stop mid-phrase. It may
return unavailable only after checking that no contiguous exact span supports
the complete normalized meaning; quote length alone is not a reason to reject
available evidence.

Contract v40 clarifies value evidence without changing packet v3 or the
selection schema. Candidate admission for a value axis is direction-neutral:
the consumer admits the relevant positive and negative evidence before an
external response relates each row to the bounded claim. `support` and
`counter` are claim-relative labels, not permanent sentiment or commercial
value labels. A customer may say the price feels high while also showing
willingness to pay through purchase or repurchase. For a bounded poor-value
claim, that behavior is counterevidence and may be described in plain-language
presentation as a positive willingness-to-pay or value signal.

Atomic source meanings remain separately traceable. Presentation may group
same-evidence, same-actor, same-action, same-direction meanings into one
lossless statement — for example, an intention to repurchase Vanilla and
Vanilla Beige — while retaining every underlying semantic-unit reference,
named object, condition, exact quote, and provenance. It must not group across
independent origins, erase a conflicting clause, or turn shade-specific
repurchase into an unqualified general repurchase claim.

Contract v41 versions new quote manifests to
`phase_a_evidence_quote_manifest_v2`. Each selected row now requires one
concise `presentation_statement` alongside its exact quote. The statement owns
the useful evidence-bound commercial reading, may perform the lossless grouping
allowed above, and keeps material reversals in one sentence. It does not append
generic method caveats whose boundaries are already carried by the source-owned
fields and this contract. Legacy v1 quote manifests retain their prior response
shape and remain finalizable; packet v3 and completed evidence stay unchanged.

Contract v42 replaces that unlanded v2 presentation experiment with
`phase_a_evidence_quote_manifest_v3`. A selected row carries one short
customer-facing `display_label` plus the exact quote; it does not carry a second
paraphrased sentence. The finalizer derives the label from the already-validated
relation `reason_code`; the quote response returns no label text. The label
names the evidence signal itself — for example,
`Repurchase intent despite price`, `Product appeal outweighs price concern`,
`Explicitly worth the price`, or `Too little product for the price` — and never
exposes the internal support/counter/adjacent/exclude relation. Relation
finalization rejects a missing, malformed, overlong, or relation-leaking reason
code before it can become display text. The
unlanded v2 manifest produced only scratch dogfood and is not a supported
historical runtime contract; legacy v1 remains finalizable byte-for-byte.

Contract v43 makes value-only presentation direct and positive-first without
changing `phase_a_evidence_packet_v3` or adding a score. When the sole selected
axis is `value_and_quantity`, or an explicit-reference-only bounded selection
admits candidates that all carry that axis, the emitted relation-response schema limits
reason codes to a small relation-aligned value vocabulary. Support or counter
requires the candidate's own normalized meaning to state a price, value,
quantity-for-price, purchase commitment, repurchase, or benefit-for-cost
tradeoff. Same-evidence companions may qualify a direct premise — including
purchase or repurchase despite price discomfort — but companion-only formula,
hydration, scent, gift-card, trial, or generic purchase meanings remain
adjacent. A value code may describe the combined visible meaning of a candidate
and its same-evidence companions when one supplies the price/value premise and
another supplies the purchase behavior. When an explicit price premise and
purchase behavior are jointly visible, the customer-facing code carries the
`despite_price` qualifier. Explicit same-evidence regret, waste, or poor value
makes every candidate from that origin counter or adjacent unless the source
explicitly commits to buy or repurchase again despite the cost, or explicitly
concludes that the product is worth the price. Displaying empties, using the
product up, or otherwise trying to make a regretted purchase feel more
worthwhile is sunk-cost rationalization, not countervailing value evidence.
Those two exceptions settle the lane before either regret reason is reached:
neither applies to an origin the source keeps positive by explicitly committing
to buy or repurchase again despite the cost, or by concluding the product is
worth the price. Where the regret does keep the candidate counter, the
counter reason `high_spend_followed_by_buyer_remorse` is available only when
one evidence item explicitly records a substantial completed spend amount, or
explicitly characterizes the completed spend as substantial, together with
cost-linked regret. Multiple units alone do not establish high spend. It adds no generic
customer-journey fields and implies neither repurchase, transaction count, nor
future intent; regret without that explicit substantial completed spending remains
`purchase_regret_due_cost`. The
deterministic finalizer rejects a value reason code placed in the
wrong relation lane. A behavior observed without an explicit price premise uses
a plain purchase, repeated-purchase, or repurchase label; the corresponding
`despite_price` label is valid only when price or cost is explicit. Quantity
efficiency without an explicit price judgment uses `product_goes_a_long_way`
rather than claiming the benefits justify the price. Time to finish, pan, or
empty a product is completed-use evidence, not quantity efficiency, repurchase,
or good value by itself. It remains adjacent unless the same evidence explicitly
states a purchase or repurchase; that explicit behavior receives the matching
behavior code. `product_goes_a_long_way` requires an explicit statement that a
small amount suffices or another direct quantity-efficiency judgment.

After every protected safety or costly-behavior row is admitted, value-only
presentation fills materially positive support origins first. Purchase and
repurchase behavior precede other direct value meanings inside each
source-native venue/role/metric bucket, and buckets continue to round-robin for
source visibility. The primary positive anchor is chosen first by semantic
value-signal priority, then stable source bucket identity; native engagement is
used only within that fixed source-native bucket. At most one ordinary counter
may be shown: the highest native-engagement direct counter from that anchor's
same venue/role/metric bucket. If no support exists, one materially positive
complaint is still shown from the complaint bucket chosen by the same
semantic-first, stable-bucket rule. If the comparable bucket has none, no
ordinary counter is manufactured. An already visible protected counter
suppresses the ordinary counter; at the cap, an ordinary counter may displace
the most recently added ordinary support origin but never the anchor. Protected
rows remain mandatory. This rule never compares raw engagement across platforms
and does not convert engagement into corroborating headcount or a
commercial-pull score. Mandatory protected groups are also ordered without a
cross-venue engagement term. The quote prompt now carries the deterministic display
label and requires a longer-body exact substring to express that label through
the normalized meaning or the same-evidence companion meaning that justified
it, or return unavailable. Semantic fit remains externally
adjudicated; deterministic exactness and body identity checks are unchanged.

Every evidence row carries its source publication time when the preserved
source exposes one. Reddit post/comment timestamps, Sephora submission times,
Amazon source dates, and Revolve creation times enter the semantic source and
flow through packet v3 to the final selection artifact. For completed packets
whose publication time is absent, the selection consumer may rehydrate it only
from the exact hash-bound source artifact named by the bundle; missing source
bytes and unsupported legacy source formats remain unavailable, while changed
bytes fail rather than supplying a date. This is source chronology for later time alignment, not proof that search
interest caused the evidence or vice versa.

Semantic posture distinguishes first-hand experience, personal agreement,
attribution or echo, questions, speculation, observable statements, and actor
strategy. Uncertainty remains a separate dimension. The compiler never turns
an echo, question, creator framing, or unknown actor into an independent
customer experience.

## Prompt-bounded hierarchy

Route 1.6 bounds the actual rendered UTF-8 bytes of every extraction and
reconciliation prompt, including method, schema, axes, context, and formatting
overhead. A single evidence item or semantic candidate that cannot fit fails
before agent output is accepted.

Reconciliation may repeat in levels. A level reads immutable candidates from
the prior level and emits child-referenced semantic nodes. Deterministic code
validates exact child accounting, source/product/comparator/version bindings,
condition lineage, polarity lineage, stale hashes, cycles, duplicate credit,
and flattened leaf provenance. Every stage and node compilation retains the
root batch-compilation hash; finalization rejects a terminal hierarchy whose
root hash differs from the supplied batch compilation even when the visible
leaf denominator happens to match. The agent still owns whether meanings are
equivalent and how conditions, negation, and uncertainty should be described.
Structural completeness is therefore proven; perfect open-world semantic
recall is not.

Current method-v12 reconciliation uses decision-only response v3. The model
authors bounded nodes, relations, axes, uncertainty and terminal metadata. One
required keyed decision per candidate names one or more node attachments or an
allowed unmerged reason, never both. One required keyed assignment per original
emerging label names a declared label group. Missing, foreign, duplicate,
orphan and prohibited decisions fail visibly; the compiler never chooses a
group, inserts a singleton, invents a missing definition or infers prose meaning.
Normal-mode admitted customer findings must remain nodes; they may remain
nonterminal when terminal warrant is uncertain. Convergence retention remains
under the existing source-row rule.

Code carries compatible subject/comparator/version identities (every selected
child must match; unlike identities are never unioned), exact emerging-label
unions and polarity composition. Code also carries every literal child
condition, deduplicating only identical strings. These source-owned fields and
child_relations are absent from the model-authored node shape, not optional
copies whose conflicts can be ignored. The compiler retains each condition's child
lineage; their union does not assert that every condition holds for every
author. At later levels, retain prior-node qualifications as node conditions
without inventing original-leaf ownership for them. Each supporting child must
establish the chosen common claim, not every other child's more specific detail.
Use ordinary context-supported interpretation and informative abstraction under
the owning claim-support rule. A shared brand ID does not make an unnamed item
a range-wide claim; generic approval is not a particular benefit. Intent,
acquisition, use, and repurchase are not interchangeable. Differences in scope,
conditions, intensity or uncertainty require separate nodes when they change
the proposed assertion, not by default. Current response-v3 prompts teach both
valid compression and overstatement limits; historical response-v2 prompt replay
keeps its original wording. No lexical rule or deterministic semantic classifier
is added, and neither the fewest nodes nor the most singletons is a success target.
The prompt also exposes source roles by existing leaf relation, the
compiler-owned terminal claim-kind competence table, and the compiler's
existing rule for composing a leaf relation with the chosen child relation, so
effective support is stated rather than guessed. An observable-statement
posture alone does not make a community report a directly verified fact.
Material with no semantically appropriate, source-competent terminal kind
remains nonterminal or, where retention permits, retrievable as unmerged
evidence rather than being relabeled to pass.
These are derived prompt facts, not new stored authority or relaxed validation.
Method v11 and earlier prompt replay is unchanged. Existing saved prompts and
responses remain historical evidence; a changed current prompt is recorded
as a fresh attempt, never silently substituted into an old receipt.
Explicit response-v2 preparation remains available for replay. A partially
completed immutable stage may receive new v3 requests without repartitioning;
only JSON whitespace may be compacted to retain byte fit. Stored v2 and new v3
responses share the existing validator and downstream node-compilation-v2
shape, without replacing raw provider artifacts. No normal-path semantic provider
stage is added. Mechanical assembly does not prove that chosen meanings belong together.

Normal method-v12 response-v3 preparation now selects
`exact_identity_namespaces_v2` at the public `prepare-reconciliation-level`
entrypoint. The separately selected `authoring_revision` is not a response or
stage schema revision. Each exact tuple of subject, comparator and version
**sets, with their roles preserved**, gets a code-derived opaque prefix. Every
candidate's attachment keys must use that prefix; node definitions may use the
batch's prefixes. Any number of model-authored keys, shared claims and multiple
attachments remain possible within a class. No identity vocabulary is copied
into these handles. Matching prefixes establish compatibility, not semantic
warrant, actual product identity truth, or useful consolidation.

This normal-request-only constraint applies at every reconciliation level and
mode. V2 also states the existing native repeated-leaf rule before generation:
one original semantic leaf may enter a node through only one attached child.
Fresh V2 stages cap a batch at 96 candidates as well as the existing prompt-byte
limit. The cap bounds output and connected-repair scope; it does not choose a
meaning, truncate context, weaken the native consumer, or promise provider
success. New stage packing includes the instruction bytes; immutable resumed
stages retain their membership and fail visibly if whitespace compaction cannot
fit the complete prompt. Native identity checks remain unchanged for all
relations. The restriction removes an incidental signal previously carried by
attempted incompatible merges; equal upstream-discrepancy discovery sensitivity
is not claimed. It adds request bytes, not a provider call or a new review stage.

Use `--authoring-revision exact_identity_namespaces_v1` to reproduce the prior
namespaced normal requests, or `--authoring-revision legacy` to reproduce the
older unrestricted normal requests.
The low-level Python preparation APIs retain their historical default for replay;
current callers explicitly select `RECONCILIATION_AUTHORING_IDENTITY_V2`.
Explicit response-v2 and older methods retain historical public defaults.
Missing-definition and local-repair requests use the unchanged historical
renderer/schema and can preserve existing opaque keys. Accepted work keeps its
actual original prompt, schema, attempt and correction receipts; newly rendered
unused requests are never substituted as its provenance. Neither namespace
compliance nor native acceptance proves source-supported meaning preservation.

Current response-v3 generation requires a nonempty node list when any assigned
candidate must remain a finding under the existing retention rule. This prevents
an empty answer, not partial definition omissions. The native consumer reports
undefined node keys separately as `MissingReconciliationDefinitions`, with their
exact child/relation assignments. Other malformed assignments still fail; the
diagnostic does not certify that an undefined key denotes a legitimate claim.

After this failure only, `prepare-reconciliation-definitions` binds the original
failed response and prepares one corrective judgment request containing only the
affected candidate groups. One required keyed slot supplies either a complete
model-authored definition or an explicit cannot-define reason. Keys are opaque
handles, never evidence of meaning. An unsupported fixed grouping or insufficient
context remains a visible semantic-judgment blocker; code never selects a meaning,
redirects an attachment or changes existing definitions. Large missing sets may
still require substantial provider work; an oversized recovery fails visibly
without truncation. No automatic repartitioning or unbounded retry is introduced.

`submit-reconciliation-definitions` appends only the missing model-authored nodes
to a fresh successor, then applies the unchanged native reconciliation consumer.
An unresolved answer publishes no successor. Original, corrective and successor
bytes and hashes remain separate; the original failed attempt is not relabeled
successful. Matching durable successors can be revalidated without another call;
changed inputs or outputs fail rather than overwrite. The provider execution and
usage-accounting route is unchanged. Use at most one corrective attempt for a
failed batch before returning unresolved work to judgment. Successful batches owe
no corrective call. Historical v2 replay and immutable stage membership stay intact.
Completeness and unchanged assignments are mechanical claims; semantic warrant
and improved provider reliability are not proven by successful composition.

Contract v34 adds an opt-in global relation-closure generation after one
terminal normal-retention frontier. Deterministic block pairs cover every
unordered frontier-candidate pair exactly once; each pair terminates as
`equivalent`, `opposed`, `distinct`, `adjacent`, or `unresolved`. Prompt batch
and local node handles are transport only. Equivalent pairs form transitive
classes, while opposed pairs form symmetric inter-class links. Directional
class identity uses a deterministic truth-complete assertion already present
on a validated frontier node plus product/comparator/version, conditions,
uncertainty, claim kind, and causal ceiling; axes and raw polarity are not hash
salt. `mixed` input polarity fails closed for whole-row repair. A hash-bound
coverage manifest must decide every required pair, with zero unresolved pairs,
before finalization may report `none_observed`; incomplete coverage is not a
negative conflict finding. This generation emits integration view v3 and does
not change policy-v2 artifacts or their finalization behavior.

The v34 generation is experimental, not an operational full-corpus route. A
dated operator observation on 2026-08-13 read the machine-local policy-v2 normal
frontier at
`C:\tmp\forseti-summer-fridays-full-corpus-v8-20260812-v0\reconciliation-policy-v2\level-0002\node_compilation.json`
(raw-file SHA-256
`23b417fde1de678379fabf54ea50fdcaaac7b8e0811b5d21c4227d53c40b7d75`;
stored `node_compilation_sha256`
`344e38ac29c0dbe27af397271ed0657b96b983e87e4b679f318cd8ba5311c473`)
and observed 7,076 semantic nodes plus 780 carried unmerged units. A read-only
name scan of that run root observed no relation-closure output. These are dated
operator observations over that exact path, not a repository-backed universal
absence claim. Exhaustive preparation would require millions of pair decisions;
v34 must not be run on, or used to claim `none_observed` for, that observed
frontier. Only a complete validated closure compilation may carry that posture.
Structural membership, pair-identity, and cardinality checks contain malformed
or internally inconsistent artifacts; without the source stage and raw
responses they do not prove semantic truth or detect a coherently forged whole
artifact.

### Supported operating route and owner-only reopen boundary

The supported completed semantic route for normal Forseti intelligence cycles
is full-corpus extraction, mandatory row verification, policy-v2 normal
reconciliation, convergence/retention under that existing policy, and the
supported view/output. One-off and unresolved evidence remains explicit; lack
of v34 closure never becomes `none_observed`. Agents must not run v34, treat it
as completion, or use it to claim global meaning identity, global opposition
coverage, or global negative conflict coverage.

Registry-first global identity, embeddings or top-k retrieval, deterministic
semantic blocking, and exhaustive all-pairs closure are deferred research
directions, not active implementation routes. An owner may explicitly reopen
architecture work only after a measured customer or intelligence outcome is
materially harmed by duplicate meaning identity or missing global opposition.
When that trigger is recorded, reorient first to this section as the semantic
contract authority and then to
`docs/workflows/phase_a_customer_evidence_completion_path_v0.md` for the latest
run history and operating sequence. Until then, preserving the supported route
and its honest residual evidence is the complete action.

The same generation adds selective whole-row repair. It projects only named
evidence rows through the existing complete-row verifier, preserves every
untouched active row exactly, and writes a repair manifest binding the parent
verified compilation, selected IDs, responses, and new active-row hash. The
new compilation hash invalidates every older reconciliation and view. Repair
never edits semantic nodes or a finalized view directly.

When a completed policy-v2 terminal compilation exists and a selective repair
changes only a narrow set of verified rows, `migrate-repaired-terminal` is the
supported incremental successor route. It admits an old terminal node only
after comparing every complete leaf semantic row it uses against the repaired
compilation; any statement, polarity, uncertainty, product/comparator/version,
axis, condition, or evidence-posture change invalidates that node. The current
route can deterministically rederive a node only when the complete-row repair
changed polarity while leaving the truth-complete statement and every other
semantic field unchanged. Changed unmerged rows retain exact membership and
reason but resolve their semantic content from the repaired compilation. That
is preservation, not fresh semantic adjudication: the migration does not claim
that the prior unmerged decision or reason was reconsidered against the repaired
meaning. A consumer that needs current membership or a freshly supported reason
for such a row must use fresh reconciliation.

The migration compiler hash-binds the raw bundle, old verified compilation,
repaired compilation, old terminal compilation, every terminal leaf, every
unmerged unit, the reuse/invalidation census, and any exact-identity coalescing.
Coalescing requires truth/scope/claim metadata to agree, unions emerging labels,
postures, and lineage, rejects relation or condition-lineage conflicts, and
uses logical AND for opposition checking. It is not relation closure and cannot
carry closure-only fields or make a global `none_observed` claim. `finalize-v3`
recomputes claim support, evidence stacks, and reverse indices from the migrated
nodes plus repaired compilation, and retains its independent duplicate-identity
guard. A broader proposition-linked semantic change, any requested membership
change, incomplete leaf proof, or missing source artifact falls back to a fresh
supported reconciliation replay.

For bundle v4, agent-facing reconciliation prompts carry child references and
the meaning dimensions needed to judge a merge, but omit expanded
`leaf_relations` and `condition_lineage`. The stage and compiler retain that
full lineage and deterministically reconstruct it from accepted child
references. The terminal hierarchy must still fit one declared prompt-bounded
batch; v7 neither raises that ceiling nor claims that an unexecuted full corpus
will converge to it.

Emerging labels are consolidated semantically before seal. The agent groups
meaning-equivalent labels; the compiler preserves every original label and
never invents a merge. Each consolidated candidate terminates as `accepted`,
`nonmaterial`, or `blocker`. Every parent node preserves the exact union of its
children's emerging labels. Under bundle v4, exactly one prompt batch owns the
level-wide emerging-label decision and receives the complete unique label set;
every other batch must return no consolidations. This prevents parallel prompt
batches from making overlapping or conflicting decisions about the same label
without replacing that semantic decision with a deterministic compiler choice.
Once validated, a consolidation is carried
unchanged through every later level; no later response may duplicate,
overwrite, drop, or invent its original-label disposition. A lower-level
`blocker` therefore remains visible in the terminal view and blocks seal.

## No-provider workflow

The runner makes no model API call. Historical v1/v2 routes retain their four
operations. Before current-route batching, a reusable full-corpus run uses an
immutable `phase_a_semantic_integration_run_v1` specification. The spec binds
the final acquisition seal, cycle/question/cutoff, current axes, rendered
prompt ceiling, external run root, and hash-pinned v3 source fragments. Every
sealed route must terminate as exactly one of `semantic_source`,
`structured_reference`, `discovery_only`, `control_only`, `duplicate_of`, or
`blocked`. Only `semantic_source` routes carry v3 source bindings and owe
exhaustive leaf-level semantic processing. In Phase A those routes are the
Reddit/community conversation corpus and retailer review text. Ads, owned
pages, PDP facts, creator posts, editorial, and other captured materials stay
hash-verified `structured_reference` routes: they remain usable evidence but
do not owe customer-language corpus conversion. A duplicate route must name a
`semantic_source`, `structured_reference`, or blocked owner and may not form a
duplicate chain. `blocked` is reserved for a required semantic source that is
still missing and prevents materialization.

The customer-corpus census rereads packet-backed Reddit records and verifies
retailer source-row references before semantic work. A
`retailer_review_source_manifest_v1` pins every retailer source file by raw-byte
SHA-256, names its admitted parser family, and binds the source-native review-ID
set. Current packet replay accepts both old-Reddit and preserved www-Reddit
HTML through their existing source-owned parsers. A conversation container
reports the source-visible total and completeness posture its own projection
states: old-Reddit markup declares no thread comment total and stays
`unavailable`, while a www projection supplies the source-declared total, and a
measured shortfall or a deliberately unfollowed continuation link makes that
container `partial` with the shortfall named in its capture boundary. An exact
match between the declared and captured counts is never promoted to `complete`,
because the source-declared total is not an independent completeness oracle.
Current retailer replay also
accepts the Soko Glam/Okendo corpus shape, deriving each stable review identity
from its source-native product slug and positive ordinal. A review-ID substring
elsewhere in a file is never membership proof. Its captured-conversation
union is reconciled against both owning sources: every coded thread family
member must appear in the union, and every reconciled target that already
yielded captured material must keep its native packet binding. It counts roots,
replies, readable leaves, mechanical exclusions, former captured-excluded
leaves, and retailer text/rating-only rows separately. The census is a
denominator proof, not semantic judgment and not a substitute for v3 source
materialization. Large source, prompt, response, and compilation artifacts
remain under the spec's external run root; a compact repository receipt may
bind their hashes.

Current-route operations are:

1. `audit-phase-a-source` verifies the final seal, every terminal route
   artifact, every route classification, and every hash-pinned source binding.
2. `build-retailer-source-manifest` pins the current retailer source files and
   structurally proves their review identities. For a retrospective run this
   proves the bytes available now; it does not rewrite or restamp the historical
   acquisition seal.
   `build-phase-a-reddit-source-v3` then materializes every packet-backed root
   and comment, and `build-phase-a-retailer-source-v3` materializes every
   source-native retailer review. Both commands preserve the captured
   denominator, mechanically exclude only exact non-text placeholders, and
   keep repository-owned locators relative to the declared repository root.
   The retailer builder verifies a Revolve completion receipt whenever the
   source manifest contains Revolve, and requires no unrelated Revolve receipt
   for a non-Revolve corpus. It retains every
   captured source file, and de-duplicates a repeated native review identity to
   one customer evidence item while preserving every source-pinned product
   listing context carried by its occurrences. A repeated listing occurrence
   does not become another customer experience. A source-native review with no
   usable text remains a mechanical exclusion and must still appear in the
   captured denominator; readable uncoded rows still fail closed. No admitted retailer source
   format preserves a capture timestamp, so retailer capture envelopes record
   capture time as unavailable rather than stamping a run-derived date.
3. `build-serp-source-surface-spec` reads hash-pinned Phase 1 and Phase 2
   queue-state receipts selected by their terminal returns, derives every
   successful job-to-packet edge, and requires the
   bounded surface map to match that producer-owned inventory exactly;
   `prepare-serp-source-frontier` enumerates every source-bearing row; and
   `materialize-serp-source-frontier-review` accepts one explicit agent-authored
   decision for every inventory row (no bulk/default decision), mechanically
   deduplicates repeated locators, and emits recovery targets that target
   reconciliation must settle. `reconcile-serp-frontier-targets` then binds
   exact Reddit and native-social object identities already present in the
   evidence ledger and leaves unmatched historical links explicitly
   unavailable; it performs no fresh acquisition.
4. `census-phase-a-corpus` independently proves the captured Reddit and
   retailer customer-corpus denominators where those Phase A source shapes are
   present.
5. `materialize-phase-a-v3` merges audited, source-family-produced v3
   fragments into one final-acquisition source and writes a separate lineage
   receipt. It never guesses a new source-family adapter.
6. `materialize-v3` verifies source artifacts and normalizes declared
   containers/leaves into one hash-bound v3 source; unsupported families or
   denominator mismatches fail closed. Materialization never renders
   provisional prompts; prompt packing belongs only to `prepare-batches`.
7. `prepare-batches` verifies sources, builds the method-bound bundle, proves
   the work-unit bijection, and writes byte-bounded prompts. Current run v9 also
   writes one exact keyed provider-response schema per work unit. Historical v4
   bundles retain their deterministic three-worker assignment manifest; current
   v5 bundles encode no static worker topology.
8. `validate-batch-response` validates one returned batch immediately without
   compiling a partial corpus. `status` reports valid, missing, duplicate, and
   invalid responses so an interrupted run can resume honestly.
9. `submit-batches` validates all agent responses and exact alias coverage.
10. For method v7 or v8, `prepare-row-verification` renders byte-bounded independent
    checks for every primary claim-bearing row, and
    `submit-row-verification` requires exactly one `accept`, complete-row
    `replace`, or `unresolved` decision per row before writing the sole active
    compilation. Non-claim rows are not reread.
11. `prepare-reconciliation-level` renders one or more byte-bounded prompts
    from batch units or prior semantic nodes.
12. `validate-reconciliation-response` validates one returned hierarchy batch
    before the level is complete.
13. `submit-reconciliation-level` validates exact child accounting and writes
     the next node compilation; repeat until one terminal level remains.
14. `finalize-v3` flattens terminal nodes back to exact leaves and writes view
     v2.
15. After selective row repair, `migrate-repaired-terminal` may replace a full
    reconciliation replay only when a completed old terminal compilation and
    complete old/new verified compilations establish the leaf-complete equality
    and narrow deterministic-rederivation proof above. It writes a new terminal
    compilation and migration manifest and makes zero provider calls.
16. The opt-in v34 route instead runs `prepare-relation-closure` over the
    terminal normal-retention frontier, validates each large-run response with
    `validate-relation-closure-response`, runs `submit-relation-closure` only
    after exact global pair-relation coverage, and uses
    `finalize-relation-closed` to write view v3. `prepare-row-repair` /
    `submit-row-repair` may correct named source rows first; any repair restarts
    reconciliation from its new verified compilation hash.
17. `prepare-calibration` reads a hash-pinned source and blind
    owner gold, projects exact bounded slices, and writes route-native sources,
    bundles, fingerprints, and prompts. The calibration spec deliberately
    selects the method being tested and may retarget the same pinned evidence
    from the source's method marker; the route fingerprint binds the selected
    method and exact method hash, so this is explicit method comparison rather
    than fallback. It makes no model call and cannot authorize a corpus run.
    Supported targets are historical methods v5/v6 and the production-owned
    `SEMANTIC_METHODS_V7_PLUS` set (currently v7-v11). Every target in that set
    requires a provenance-bound row-verified compilation for both primary and
    configured cold-repeat evaluation. A new keyed response transport does not
    waive verification; historical v5/v6 replay behavior remains unchanged.
18. `evaluate-calibration` runs the existing response validator, then evaluates
    disposition, unit-count, product/axis/posture, atomic-meaning, cross-source,
    anomaly, and selective cold-repeat obligations. Semantic atom, relation,
    anomaly, and repeat judgments must be explicit and hash-bound to the exact
    compiled responses they judge. Cross-source relation judgments additionally
    bind a final reconciliation view that the evaluator rebuilds from the
    supplied terminal node compilation; extraction output alone cannot satisfy
    a merge or counterevidence obligation. Missing or stale adjudication blocks;
    a critical mismatch fails. The report is a bounded calibration result only,
    never a prevalence estimate, readiness claim, or corpus-resume authority.

Adjudication v3 closes both the unsupported-axis gap and the unmerged-unit
direction gap without a phrase or field-value blacklist. For every semantic
unit in every gold case, the adjudicator must partition the unit's exact
assigned axes into supported and unsupported lists and judge whether its
statement plus polarity preserve what the source actually asserted. Missing
units, axes, direction judgments, extra keys, overlap, or malformed judgments
block; an explicitly unsupported axis or false direction judgment fails the
case. Calibration specs v2 and v3 bind adjudication v3 and cannot pass with v1
or v2 adjudication. Spec v3 adds the closed density audit below; historical
spec v2 remains readable without acquiring that later obligation.
The older versions remain readable with historical specs only; v2 proves its
per-axis obligation but not the v16 per-unit direction obligation.

The calibration spec is authored from source text, required context, and the
run-local catalog before the evaluated responses are read. Fields representing
observed or predicted machine output are forbidden in that gold artifact. Every
gold container — spec, slice, case, atom, relation obligation, repeat bound, and
anomaly threshold — is a closed key set, and the gold must declare at least one
case: an unrecognized or misspelled obligation field is rejected rather than
ignored, so an obligation cannot silently disappear from the gate while the
report still reads as a pass. A `route_contract` pins the method hash,
bundle/response/prompt generations, rendered axes hash, and run-local catalog
hash; preparation fails if the actual route differs on any of those. The same
`route_contract` also records the semantic runner revision and contract version,
but those two are operator-declared provenance only: no observable in-process
value is supplied by the current execution interface to check them against, so
they are carried into the route fingerprint unverified and must not be read as
machine-enforced pins. A
calibration slice may be compact or production-shaped, but every selected
evidence ID must project exactly once, and a claim-bearing gold case must name
at least one required atomic meaning. Evaluation requires the hash-pinned full
source and deterministically rebuilds the expected bounded sources, bundles,
prompts, route fingerprints, and preparation receipt. The supplied preparation
must match those rebuilt artifacts exactly; its self-hash proves internal
consistency only and is not accepted as provenance. Clearly empty reactions
remain accounted as `context_only` with zero semantic units; no phrase blacklist
or deterministic meaning matcher substitutes for the one context-aware
relevance judgment.
Repeated large axis signatures are a deterministic warning, not an automatic
semantic verdict, and must receive a compilation-bound adjudication before a
pass is possible. Selective second reads repack only the predeclared cases into
one separately hash-bound route-native slice; their consistency judgment binds
both the primary compilation for each case and the compact repeat compilation.
Consistency is semantic rather than count-identical: different supported
atomic decompositions may be consistent, but a dropped, added, reattributed, or
directionally changed supported meaning is inconsistent. Judge every unit's
attribution separately, because one reply may contain attributed parent claims
alongside its own first-hand shopping reaction. Axis and attribution judgments
apply to primary cases as well as cold repeats.

Spec v3 may additionally require a `semantic_unit_density_audit` on a slice.
The evaluator deterministically ranks non-gold evidence rows that emitted at
least one semantic unit by descending unit count, breaks ties by evidence ID,
and selects the declared number of rows. Every selected row receives its own
compilation-bound adjudication. The adjudicator checks whether the row's units
are source-supported, independently meaningful, non-duplicative, and no more
finely split than the source warrants. All four checks are explicit and closed:
all true derives `reviewed_benign`, any false derives `reviewed_defect`, and any
unknown derives `unresolved`; a stated outcome that disagrees with those checks
is invalid. A confirmed defect fails; missing, stale, invalid, or unresolved
judgment blocks. This is an anomaly audit, not a new gold case, a prevalence
sample, a deterministic semantic verdict, or a license to relax the
pre-authored cases after seeing output.

The controller is the active agent task. It assigns immutable batch IDs to at
most three no-API semantic subagents and treats the response directory as the
durable resume surface. Repository code prepares, validates, and reports work;
it does not invoke a model through an API or headless CLI. A worker writes a
temporary response and publishes it only after completing the file.
`publish-batch-response` enforces this boundary: it accepts only a validated
sibling `.json.tmp`, atomically creates a no-replace final hard link, and then
removes the temporary name. An existing final response and a filesystem that
cannot provide the no-replace link both fail closed. Missing batches may be
reassigned when no accepted output exists. No
lease, daemon, mutable queue service, or claim-marker subsystem is required.
The returned JSON is untrusted until the corresponding validator accepts it.
Status is derived from validated response files and reports remaining work per
static worker partition; a dead worker never becomes a completed batch.

If exact prompt packing exposes more work than the available no-API judgment
lane can execute as one bounded run, the status remains
`SEMANTIC_BATCH_JUDGMENT_REQUIRED`. The controller records that observed
capacity boundary; it may not substitute a sample, silently raise the prompt
ceiling, or describe prompt generation as completed semantic integration.

## Failure and seal posture

A passing route-1.5.0 acquisition seal requires:

- a material, terminal `semantic_evidence_integration` route job;
- a completed integration block and resolvable hash-pinned view;
- exact bundle/corpus/method/view hashes;
- `semantic_evidence_integration_method_v2` for a newly sealed route;
- equal admitted and accounted counts with `complete: true`;
- no unresolved material evidence;
- every proposition reference resolved on the axis that cites it;
- every material comparator carries distinct stable subject and competitor
  product IDs, and every cited competitive-choice proposition binds exactly
  those two IDs in that orientation;
- every emerging axis terminally dispositioned; and
- no impossible source-role, independence, repetition, cross-venue, conflict,
  or causal combination.

A passing route-1.6.0 seal additionally requires:

- source v3, bundle v4, method v3, batch-response v2, reconciliation-response
  v2, and integration-view v2 lineage;
- the `phase_a_final_acquisition` corpus profile rather than a bounded
  regression slice;
- captured count equal to assessed plus mechanically excluded plus blocked,
  with every count exact and no blocked item;
- exact container accounting and disclosed capture envelopes;
- a prompt-bounded, acyclic reconciliation hierarchy whose terminal nodes
  flatten to exact leaf evidence and retain the exact root batch-compilation
  lineage;
- truthful evidence-stack counts that keep evidence items, containers,
  independent origins, roles, engagement, support, opposition, and mixed
  containers separate; and
- every emerging-axis candidate consolidated with immutable original-label
  lineage and terminal disposition, including lower-level blockers.

A passing route-1.7.0 seal additionally requires one embedded
`phase_a_serp_source_frontier_v1` in the evidence-depth ledger. Its Phase 1 and
Phase 2 job sets and packet sets must exactly match the successful attempts in
the terminal-return-selected, hash-pinned queue-state receipts. A recovery job
may name its sealed parent through one explicit one-to-one alias. Every
focused-search job must match its own recorded packet set exactly, and every
source-bearing result row from those bounded surfaces must receive exactly one
agent-semantic disposition: `routed`, `duplicate`, or `excluded`; a bulk/default
routing decision is invalid. One resolved packet file has one artifact identity
across all Phase 1, Phase 2, and focused-search surfaces. The same identity may
visibly serve more than one job, but a second identity over the same file would
enumerate its rows twice and is invalid. A
routed row points to an existing native-capture or locator-recovery target with
the exact source URL (or its deterministic recovery locator) and a discovery
job recorded by that row's packet; a duplicate points directly to a routed owner; an
excluded row carries a reason. People-also-ask and related-search prompts are
Google navigation aids, not external sources. This closes the SERP-to-native
linking gap without crawling result pagination or treating SERP text as native
evidence. Blocked and failed attempts remain visible in the producer receipt
but do not become source-bearing packet surfaces. The frontier classifies the
producer-owned set; it never defines that set.

Uncertainty is preserved rather than repaired. Nonmaterial unresolved evidence
may remain visible; material unresolved evidence blocks the affected claim or
the seal. A changed corpus always requires a new view.

## Historical boundary

This contract enters the Understanding Acquire & Seal route at `1.4.0`.
Historical `1.3.0` and earlier seals retain exactly their stamped obligations
and are never rewritten or restamped to claim semantic-integration coverage.
The context-aware method and stable comparator product-ID requirements enter at
`1.5.0`; a historical `1.4.0` seal retains its original v1 method obligation
and never owes the 1.5.0 additions.

Full captured-corpus accounting, prompt-bounded hierarchy, semantic posture,
container/capture-envelope accounting, explicit emerging-axis consolidation,
and truthful evidence-stack counts enter at `1.6.0`. Historical `1.5.0` and
earlier seals retain their stamped view and method obligations and never owe
Route 1.6 fields.

The semantic-source boundary and complete bounded SERP-row linking enter at
`1.7.0`. Historical `1.6.0` and earlier seals are immutable and never owe the
new frontier.

## Changelog

- `v104` / 2026-09-02 — versioned current normal reconciliation authoring to
  `exact_identity_namespaces_v2`. It states the unchanged native rule that one
  original semantic leaf may enter a node through only one attached child, and
  caps fresh current batches at 96 candidates in addition to the existing
  prompt-byte ceiling. Frozen Dieux level 4 packed 25 of 26 batches at 140–145
  candidates: 10 were initially accepted, 11 returned structurally invalid
  responses, and 5 timed out. Repeated-leaf defects appeared in seven initial
  batches and again after layered recovery; four exact connected repairs then
  exceeded the unchanged 120,000-byte ceiling, while two full batches timed out
  twice. The sole 95-candidate tail batch was accepted; this observation binds
  the containment-oriented cap but does not prove semantic quality or provider
  reliability. Fresh v2 Dieux level-4 dogfood then accounted all 3,665 candidates
  exactly once in 39 deterministic batches, each at most 96 candidates; two
  rebuilds were byte-identical and the largest prompt was 86,060 bytes. The
  unchanged consumer initially accepted 30, rejected 4 structurally, and saw 5
  provider failures. All four initial recovery requests fit at 15,927–67,572
  prompt bytes; none required truncation. Bounded recovery and one explicit
  retry per failed call raised acceptance to 36 of 39. The three unresolved
  batches remain visible: one normal batch timed out twice, one repeated-leaf
  component persisted through three changed repair responses, and one layered
  orphan/definition response ended in an explicit cannot-define judgment for a
  fixed key. The explicit repeated-leaf instruction therefore does not prove
  prevention; the native consumer remains unchanged and fail-closed. Explicit
  v1 and legacy selection preserve old packing and prompt bytes; accepted
  artifacts keep their original prompt and receipt provenance. No automatic
  deduplication, truncation, provider call, retry loop, semantic classifier, or
  Deliver conclusion is added.
- `v103` / 2026-09-02 — added a read-only current-response-v3 reconciliation
  diagnostic so one failed answer can expose all independently observable
  mechanical defects before the operator commissions a bounded repair. The
  unchanged validator remains fail-first and authoritative; the diagnostic
  reports its exact primary error, affected opaque handles, and any dependent
  checks skipped because their prerequisites are malformed. It never repairs,
  infers meaning, selects scope, accepts a response, or calls a provider.
  Frozen Dieux level-3 dogfood over all 28 original completed responses reported
  3 valid and 25 invalid responses, covered every authoritative primary error,
  and exposed 79 issue records: 38 duplicate attachments, 40 missing node keys
  across 17 response-level records, 9 orphan nodes, 7 repeated-leaf nodes, and
  8 terminal nodes without effective support. All 13 currently selected accepted
  responses remained clean, and a second 28-response run was byte-identical.
  These are structural findings, not semantic verdicts or repair authorization;
  no response, stage, provider attempt, or historical artifact was changed.
- `v102` / 2026-09-01 — required one relation per exact candidate-and-node
  pair in current decision-only prompts. Dieux level-2 authoring repeatedly
  emitted the same node key as both support and counter for one candidate,
  including inside bounded repairs; the unchanged consumer correctly rejected
  every occurrence. The prompt now states the already-enforced invariant so the
  provider is warned before generation. Dieux level-3 dogfood still emitted the
  invalid shape, so prevention is not proven and the consumer remains the
  reliable enforcement. No schema or consumer is weakened, no call is added,
  and historical rendering remains unchanged.
- `v101` / 2026-09-01 — made the current decision-only terminal schema require
  a boolean `opposition_checked`, matching the unchanged native invariant.
  Dieux level-2 definition recovery had produced a terminal node with valid
  claim kind and causal ceiling but null opposition status; the provider schema
  admitted it and the consumer rejected it. Nonterminal and historical v2
  behavior remain unchanged, no call is added, and the boolean does not prove
  that opposition was adequately reviewed.
- `v100` / 2026-09-01 — added the symmetric explicitly unaccepted intermediate
  for a scope-correct missing-definition patch that reveals another native
  defect. The next existing bounded repair consumes the hash-bound intermediate;
  no partial response is selected and no automatic repair is introduced.
- `v99` / 2026-09-01 — allowed the existing failure-only local repair to carry
  an explicitly nominated duplicate node key, including every duplicate
  definition and connected owner. Unnominated duplicates still block by name;
  code does not rename, reattach or infer meaning automatically.
- `v98` / 2026-09-01 — made current decision-only response schemas reject
  nonterminal nodes carrying terminal claim metadata, and terminal nodes with
  either claim field absent. This moves an existing native invariant into the
  provider-visible schema without changing historical v2 replay or adding a
  call.
- `v97` / 2026-09-01 — added an explicitly unaccepted, hash-bound local-repair
  intermediate so one bounded correction can be preserved when native
  validation reveals a second independent defect. Existing definition and
  local-repair preparers consume that intermediate; no response is selected
  until the unchanged full validator passes. This adds no normal-path call,
  automatic semantic edit, retry loop or accepted partial-success path.
- `v96` / 2026-09-01 — versioned the existing targeted benchmark audit method
  from v1 to v2 so current audits judge source-to-result fidelity at the
  decision-relevant bounded-finding level rather than by literal vocabulary.
  The prompt names the consequential boundaries that may change downstream use
  and treats descriptive-channel detail as non-load-bearing unless the current
  commission makes it a decision dimension. It contains no word-pair exception,
  adjacency dictionary, mandatory mirror, repeat-review gate, or change to
  production consolidation. Historical v1 text remains available and frozen
  artifacts remain unchanged. The wording was tested uncued on the same 48-row
  Dieux diagnostic sample: after the response was frozen, the controller-hidden
  harmless-adjacency and intended-action/completed-action controls both passed.
  That one-call same-model calibration is behavioral evidence, not semantic
  truth or a population estimate. Durable report:
  `C:\tmp\forseti-phase-a-dieux-uncued-bounded-meaning-calibration-20260901-v1\final-report.md`,
  SHA-256 `4ea934883d5eeb794a907e3feee79025fd1f313c9689de243890a69d8eee5f50`.
- `v95` / 2026-09-01 — kept the v94 bounded-edit rejection unchanged after a
  controlled audit-calibration experiment on 48 purposively selected frozen
  Dieux rows. The candidate rubric applied the existing bounded-proposition
  rule without a word-pair dictionary: both mirrored positions treated the
  `looks supple` / `feels supple` difference as harmless for this broad Phase A
  use and retained the `decided to try` / `bought` action-boundary error.
  Those exact examples and their intended boundary were stated in the
  experiment prompt, so the result proves consistent application under an
  explicit rule, not uncued model generalization. Critical classifications
  still changed with presentation order for seven unique rows under the prior
  rubric and eleven under the candidate rubric. The owner accepts that ordering
  sensitivity as a visible model residual rather than a standing engineering
  target: no word-pair exception, adjacency dictionary, mandatory mirror,
  repeat-review gate, or new production/audit machinery is added. A later
  task may account for finer visual-versus-tactile meaning when that distinction
  is actually decision-relevant; it does not burden the present broad Phase A
  consolidation. Durable report:
  `C:\tmp\forseti-phase-a-dieux-bounded-finding-calibration-20260901-v2\final-report.md`,
  SHA-256 `f900ea9c78ae532e34e893d2b0744e58d362f60dd04800f46ff5dc830bc2fb79`.
- `v94` / 2026-09-01 — rejected, and did not promote, the bounded-edit
  row-verifier experiment nominated by the checker value audit. The prototype
  made the consumer preserve every unnamed field/unit and allowed only explicit
  disposition, field, removal and addition operations. A fresh outcome-independent
  held-out set covered 212 rows in 11 complete batches (110 community, 102
  retailer) with zero overlap against the prior 96-row audit. All 212 candidate
  decisions reached a test-only native-valid consumer successor, but the opaque-
  label same-vendor quality assessment found 80 material-error rows for bounded
  edits versus 71 for the existing whole-row checker (original extraction: 94).
  Candidate-only clean rows were 33; whole-row-only clean rows were 42. Both
  checker variants had one different serious assessed error. Containing output
  shape therefore did not prevent an intentionally wrong targeted edit and did
  not beat current machinery. Experimental runtime, runner, tests and normative
  wording were removed rather than installing a dormant adapter or recurring
  ceremony. Historical/current behavior remains verifier v11 response v1/v2.
  Candidate generation observed 807,878 input and 42,233 output tokens across 11
  successful `gpt-5.5`/high attempts; historical deltas are `NOT_COMPARABLE`
  because batch/prompt definitions differ. Thirty-three preceding attempts
  failed with zero reported usage while exposing local-config and structured-
  output schema incompatibilities. Same-vendor assessment is descriptive, not
  independent truth or population inference. Durable report:
  `C:\tmp\forseti-phase-a-dieux-bounded-edit-dogfood-20260901-v3\final-report.md`,
  SHA-256 `3cb0c4cb20a42204fd2d0e370f961f32bd49a3c63920c3ac8258e2901d772492`;
  output manifest SHA-256
  `1da23435b9abf0669d37e3504aaddb13e143f1b9a9817a96fc67cf9dc7da496c`.
- `v93` / 2026-09-01 — added an oversize-only lossless table layout to the
  existing local reconciliation repair request. The old renderer still runs
  first; previously fitting requests and the response schema stay unchanged.
  Common fields are carried once and remaining values retain named columns,
  exact JSON types, source text and row order. Heterogeneous key sets remain
  lists; no absent field becomes null. The canonical full context remains the
  identity input, and a packet that still exceeds its bound fails visibly.
  Two formerly blocked Dieux components fit the unchanged 120,000-byte limit:
  156,535 -> 112,453 bytes and 122,613 -> 87,988 bytes. Both contexts reconstruct
  exactly; five saved repair requests replay unchanged and a 23,658-byte small
  control is identical. Focused validation: 355 tests passed; coupling: 18.
  Two `high` provider attempts (one per case) reached the existing repair
  consumer and repeated without new calls. Source assessment is deliberately
  mixed: batch 32 correctly separated stated need from achieved benefit and
  another reviewer's experience; batch 30 repaired opaque product wording but
  expanded a continued-use definition to unsupported repeat purchase. That
  successor remains held; native acceptance is not semantic clearance, and
  this single attempt does not establish packing as the cause. Outside the
  nominated components, 166 decisions and 92 definitions remain unchanged.
  Evidence/accounting: `C:\tmp\forseti-phase-a-repair-packing-20260901-v1\assessment.json`;
  SHA-256 `02e9f38ea3206c0a119c91fb6733c06138f00c2d9c68bf2d5599eb02b278138d`.
  Reported trial usage: 96,012 input (2,816 cached included), 12,074 output
  (1,032 reasoning included), 108,086 logical tokens; zero observed retries or
  process failures. Historical provider-token/latency deltas are
  `NOT_COMPARABLE` because the old oversized requests never reached a provider.
  No corpus selection changed, no provider stage was added, and no whole-batch
  semantic clearance, long-run reliability or Phase A completion is claimed.
- `v92` / 2026-09-01 — selected separately versioned, normal-request-only exact
  identity namespaces after the bounded AO-2 feasibility and recovery work.
  Public current preparation selects the restriction; explicit legacy selection
  and shared correction defaults preserve replay. No new decoder, identity
  authority, semantic provider stage or forced singleton is added. Finite
  feasibility observations are under
  `C:\tmp\forseti-phase-a-namespace-feasibility-20260901-v1`: one constrained
  raw batch had zero incompatible groups but omitted one definition; both it
  and the baseline had source-meaning errors. Candidate raw logical tokens were
  64,422 versus 59,125 baseline (n=1 each), not a savings or quality-win claim.
  Existing definition recovery and four-candidate local correction produced a
  valid 152-decision successor under
  `C:\tmp\forseti-phase-a-namespace-recovery-20260901-v1`, adding 40,737 logical
  tokens in two calls. Four corrected nodes retain `opposition_checked=false`.
  Current implementation/replay and continuation evidence is under
  `C:\tmp\forseti-phase-a-namespace-current-20260901-v1`; progress there is not
  Phase A completion. Three normal calls covering 474 decisions produced zero
  incompatible-identity groups; one failed on an orphan definition. Source
  inspection found behavior/intent and single-source plural-wording errors.
  Three existing local corrections (12/4/12 candidates) recovered the batches,
  preserving 446 outside decisions and 242 outside definitions. Dieux reached
  26/54 structurally accepted first-level batches; 28 and downstream work remain.
  Six calls used 275,365 logical tokens, with no process failure or observed
  transport retry; 353 focused tests and exact-head CI at `3c5b8aa1` passed
  (6,037 tests, 25 skipped). This is bounded correction, not autonomous accuracy
  or a current-versus-historical quality win. Semantic preservation, global reliability, unknown
  formula compatibility and equal identity-discrepancy discovery remain unproven.

- `v91` / 2026-08-31 — moved the existing exact-identity check into failure-only
  repair preparation as well as compilation. Separate saved Dieux batches 16,
  17 and 21 reproduced incompatible product/comparator/version groups. In batch
  21, correcting the initially nominated groups still left another incompatible
  refund group untouched, so the full successor failed. Preparation now lists
  all such omitted groups before a corrective provider call; nomination remains
  explicit and semantic rewriting remains judgment-owned. No normal-path call,
  schema, historical adapter, automatic scope expansion or prose classifier is
  added. The regression tests reach the intended public boundary with honestly
  repinned product, comparator and version fixtures. All 339 integration tests
  passed; 21 accepted batches, ten valid repairs and 35 pending requests replayed
  unchanged. One fresh eight-candidate correction passed the public consumer
  and bounded source inspection, preserving 149 decisions and 97 definitions;
  Dieux reached 22/54 structurally accepted batches, not Phase A completion or
  proven future semantic reliability. Exact accounting and bounded dogfood are under
  `C:\tmp\forseti-phase-a-dieux-repair-scope-20260831-v1`.

- `v90` / 2026-08-31 — made optional current-generation retention choices
  exclusive and added source-bound connected-component correction at the public
  reconciliation consumer. Reuses immutable attempts and existing final
  accounting; it does not create a second evidence-count authority. Preserves
  unrelated work and requires explicit judgment/refusal plus full native
  validation. Changed meaning or attachments invalidate prior opposition
  clearance in code; the repair model cannot assert that clearance. The v89
  adherence failure remains evidence, not a closed issue. Ten saved corrections
  replayed; one fresh final-version repair passed the public consumer and bounded
  source inspection. Two earlier candidate attempts failed (provider root-schema
  rejection; model-carried stale clearance), and are preserved. This is n=1 for
  the final version, not repeat reliability or autonomous semantic detection.
  Validation, exact attempt accounting and saved Dieux repair dogfood are under
  `C:\tmp\forseti-phase-a-dieux-local-repair-20260831-v1`.

- `v89` / 2026-08-31 — corrected recurring Dieux comparison and attribution
  outputs through source-bound adjudication, preserving frozen predecessors.
  The first 13 returned batches contained three incompatible comparison groups
  and ten plural-author overstatements; continuation exposed another inverse
  orientation group and further plural wording. Current response-v3 guidance
  now carries the existing compiler-owned-count boundary into bounded prose
  and makes the exact-orientation constraint explicit, in both normal authoring
  and missing-definition recovery. No new identity payload, provider stage,
  prose classifier, changed counting logic or relaxed validator. Historical v2
  prompt replay remains isolated. Prompt delivery is testable; future model
  adherence and full Dieux completion remain separate observations. Run-local
  repair, failure and continuation evidence stays under
  `C:\tmp\forseti-phase-a-dieux-full-corpus-20260831-v1` in
  `reconciliation-comparison-recovery-20260831-v1`,
  `reconciliation-attribution-current-20260831-v1` and their recorded successor.
- `v88` / 2026-08-31 — added failure-only missing-definition recovery at the
  current reconciliation consumer, plus a conditional nonempty generation guard.
  Dieux's three saved completed responses omitted 1, 88 and 96 referenced
  definitions while passing their supplied schemas. An earlier full-answer retry
  reduced 102 omissions to one, still failing native validation. This motivated
  exact missing-piece recovery rather than more prompt emphasis or a standing
  second review. Existing grouping and definitions are immutable; unsupported
  groups remain unresolved, not mechanically repaired. No new ontology, normal-
  path provider stage, semantic classifier or historical response mutation.
  Focused public-consumer tests cover partial omissions, wrong keys, changed
  assignments/definitions, unresolved groups, byte-bound lineage, durable repeat
  and consumer rejection. The first bounded dogfood recovered all three saved
  failures in one corrective attempt each: 185 definitions appended, no prior
  decisions/definitions changed, and 11 of 54 batches structurally accepted
  (1,149 nodes, 215 unmerged units). Exact repeat submission used no new provider
  call. This n=3 observation is not a general reliability rate or semantic review.
  Run-specific provider outcomes and subsequent continuation live at
  `C:\tmp\forseti-phase-a-dieux-full-corpus-20260831-v1\reconciliation-definitions-20260831-v1`;
  their existence or structural success does not establish Phase A completion.
- `v87` / 2026-08-31 — generalized the owner's skin-change clarification into
  claim-relative interpretation and useful abstraction in the cycle-wide
  claim-support authority and current response-v3 reconciliation prompt.
  Narrow scope is not literal-word equivalence. Sources with different detail
  may support a genuine common assertion while preserving their leaf-owned
  distinctions. This supersedes v86's forced-split adjudication for buy/try:
  expressed product interest is a legitimate shared claim, without credit for
  a completed action. No phrase whitelist, new provider stage, consensus loop,
  ontology or relaxed identity/coverage validator was introduced. Historical
  response-v2 preparation remains unchanged. The prompt-delivery test failed
  before this correction; the final-view fixture already admitted shared
  interest without behavior credit, locating the defect in guidance and review,
  not a missing compiler capability. These tests do not prove provider accuracy.
  The bounded Dieux adjudication inspected 139 behavior-labeled nodes and checked
  49 selected nodes against their underlying candidate meanings. It changed
  only those claim kinds and four broken assignments to already-declared label
  groups. All wording, relations and original files remain unchanged; the
  buy/try group stays intact. Four batches (457 nodes, 108 unmerged units) now
  pass structural validation with explicit controller assistance; 50 of 54
  remain unattempted at that checkpoint, and the full-stage completeness guard
  still rejects the partial set. All 54 historical prompts replay exactly;
  current prompts rebuild identically within the existing ceiling. Evidence:
  `C:\tmp\forseti-phase-a-dieux-full-corpus-20260831-v1\reconciliation-meaning-adjudicated\proof.json`
  (SHA-256 `c19552174f6855997df5883ab932fd2f1f27a2efcd259fa7afb03a5b10bf12af`).
  Subsequent productive provider attempts are recorded separately under that
  run, not folded into this assisted or deterministic proof. No full-corpus
  semantic clearance, repeated provider reliability or Phase A completion is
  claimed.
- `v86` / 2026-08-31 — adjudicated the different-vendor PR #1530 review of
  `17b4bb218eae8a9bc788c44898a170ffbf7653a4`. F1 export-list cleanup and F2's
  unreachable owner branch need no patch. F3's duplicate-key gap is live, not
  hypothetical: the Dieux controller already publishes keyed row reviews
  through the shared helper. Five hash-correct malformed fixtures were accepted
  before the closure and now fail before callback/publication. One shared
  decoder hook closes the gap; raw answers and usage survive rejection.
  A bounded scan of all 225 top-level phase response files (8,959,150 bytes)
  under `C:\tmp\forseti-phase-a-dieux-full-corpus-20260831-v1` found no duplicate
  keys. This is preventive closure, not a finding of corrupted saved answers;
  attempt-only and external artifacts were outside that scan. F4 corrects the
  row-review default's actual v10/v11/v12 gate; reconciliation's v12 gate and
  explicit historical replay stay unchanged.
  The F5 forced-split disposition below is superseded by v87's general
  claim-relative abstraction rule; the historical adjudication had required
  preserving the separate buy and try intentions rather than
  counting their disjunctive union as repeated support for one narrow action.
  Both remain valid first-hand statements of intent, not completed purchase
  or use. The current terminal `reported_behavior` kind would populate
  `behavior_evidence_refs`; these statements do not establish that behavior.
  Correct the affected semantic answer through the existing judgment route,
  preserving both intentions without inventing observed action; no keyword
  rule, general ban on intent, or frozen-answer rewrite was added. The owner's
  accepted `changed my skin` / `visible results` reading remains closed.
  Progress is three structurally accepted batches, one rejected label-owner
  batch and 50 unattempted out of 54, not 51 unattempted. Semantic correction
  remains open; neither this review nor its mechanical closure completes Dieux.
  Review return SHA-256:
  `5e4af7ba79c64e2dadd87b528b334ff2bf5610807a716686579fe327b5d8d6dc`;
  local test receipts: `reconciliation-decisions/review-publication-red.xml`
  and `reconciliation-decisions/review-publication-final.xml` under that run root.
- `v85` / 2026-08-31 — replaced current reconciliation's redundant source-fact
  copying with explicit decision-only response v3 and deterministic assembly.
  Required candidate and original-label slots address the observed omissions,
  duplicate group membership and prohibited unmerging; child facts retain their
  original ownership. Historical v2 transport and downstream compilation remain
  supported. No provider stage, auto-repair or semantic classifier was added.
  The owner accepted the earlier `changed my skin` / `visible results` wording
  in context; that allegation is no longer a blocker, and this is owner
  adjudication rather than mechanical semantic proof. Real-data dogfood and
  completion status are recorded under
  `C:\tmp\forseti-phase-a-dieux-full-corpus-20260831-v1\reconciliation-decisions`;
  structural acceptance alone does not complete Dieux Phase A.
  The first wave made four provider attempts for three batches: two responses
  passed structural validation; the label owner timed out once, then returned
  four assignments to undeclared groups and failed the intended boundary.
  No later batch launched. Inspection of the two accepted batches' multi-child
  groups left a buy-versus-try merge finding for adjudication; this is not an
  allegation of observed purchase. A next-level fixture exposed and then
  verified preservation of historical node qualifications alongside leaf
  conditions. A run-local display error after durable acceptance was corrected
  without another provider call. Shared schema definitions then reduced the
  54 sidecars from 9,977,865 to 1,933,635 bytes with exact expanded-constraint
  equality; those final sidecars were not re-sent to the provider, so no token
  savings or latency improvement is claimed. The timed-out attempt has no
  complete usage measurement; aggregate historical token delta is
  `NOT_COMPARABLE`. Evidence: `assessment.json`, `shared-schema-proof.json`,
  `condition-carry-replay.json`, and `accounting-decision-consolidation.json`
  (the accounting file is at the parent run root).
- `v84` / 2026-08-31 — Dieux full-corpus reconciliation exposed three
  cause-visible first-level failures: one answer invented a child identifier;
  the emerging-axis owner omitted five exact labels and invented one; and one
  node reinterpreted mixed child polarity from agreeable wording. Current
  method-v12 reconciliation preparation now carries its existing response-v2
  transport as a schema sidecar whose child references and level-owned original
  labels are constrained to the assigned inventories. The public preparer
  persists that sidecar. Native validation still enforces exact cross-group
  label coverage, polarity composition and source competence; semantic adequacy
  remains judgment-owned. This adds no provider stage. Historical prompt bytes
  and method-v11-and-earlier preparation remain unchanged. This machinery
  result does not by itself complete Dieux consolidation or prove unattended
  semantic accuracy.
  The constrained corrective run completed three calls and accepted none:
  one assigned `price transparency` to two emerging-label groups, one unmerged
  an admitted first-hand formula-interest finding in normal-retention mode,
  and one omitted the adjacent child's `when it warms up` condition. All were
  rejected by their intended native boundary with current hashes; no later
  batch was launched. Across the first-level run, seven calls covered four of
  54 batches, with one structurally accepted batch and 50 unattempted batches.
  Bounded inspection of that accepted batch also left a `visible results`
  wording allegation open. Current enumeration constraints therefore remove
  invented handles, not the wider preservation/repeatability problem. Evidence:
  `C:\tmp\forseti-phase-a-dieux-full-corpus-20260831-v1\reconciliation-constrained\proof.json`,
  `reconciliation-constrained/corrective-result.json`, and
  `accounting-consolidation-paused.json`. Full Phase A remains incomplete.
- `v83` / 2026-08-31 — Dieux verify-0036 returned 25 decisions but duplicated
  one ID and omitted another; a corrective retry repeated that ID five times
  and omitted four others. Array length was not exact row participation.
  Current verification/repair producers now emit evidence-ID-keyed response v2
  with exact required slots and same-ID replacements; both public runners
  persist the constrained schema. Native application accepts explicit v1/v2
  transports while retaining the original source-work stage and raw response
  hashes. Completed answers need no regeneration. This prevents structural
  omission/substitution, not incorrect meanings inside valid slots; semantic
  repair and Dieux completion remain separate obligations.
  The full-corpus run subsequently completed all 111 verification batches:
  38 accepted v1 responses were retained and 73 keyed v2 responses were accepted,
  including the formerly failing batch. Four selective-repair batches and four
  corrective attempts also passed row participation. Source inspection still
  required six explicit controller-authored row corrections, including a false
  Air Angel agreement inferred from a Prequel comment and an Aestura-only
  statement attached to Skin Mercy. These are reviewer-assisted semantic
  judgments, not evidence of unattended accuracy or a new runtime classifier.
  The repaired 6,908-row ledger retains 141 unresolved rows and 8,416 meanings;
  its native replay is byte-identical. The bounded evidence is under
  `C:\tmp\forseti-phase-a-dieux-full-corpus-20260831-v1` in
  `repair-adjudicated/adjudication.json` and `repair-dogfood.json`.
  Consolidation and final axis-reader completion remain unclaimed at this
  checkpoint; structural acceptance does not clear semantic truth.
- `v82` / 2026-08-31 — full-corpus Dieux verification returned all 27 assigned
  decisions exactly once, but in a different order. Verification and selective
  repair now bind decisions by evidence ID rather than list position. Missing,
  duplicate, foreign, and mismatched replacement identities still fail; source
  order controls application and raw response order remains hash-bound lineage.
  Prompt, schema, method, and stage identities are unchanged. Publication can
  recover a completed response after callback rejection only when the existing
  usage receipt equals the exact rederived bytes; it neither restamps usage nor
  replaces a canonical response. This removes unnecessary provider repetition,
  not semantic review: row-meaning issues and full-corpus completion remain open.
- `v81` / 2026-08-31 — the corrected 87-row Dieux trial reached reconciliation
  with 156 meanings. One provider answer produced 98 nodes; 18 changed or
  omitted literal child conditions, and bounded inspection also found
  unnamed-item/range-wide and acquisition/use merges. The existing validator
  rejected the answer before finalization. Current method-v12 reconciliation
  now states the literal condition requirement and the bounded merge rule at
  the actual consumer prompt. Validators, extraction, verification, schemas,
  and provider-stage count are unchanged. The first correction's answer
  preserved all literal conditions across 141 nodes but failed source-role
  competence on one community report labeled as an observable fact. The
  prompt now exposes the existing source-role facts and competence table;
  it does not invent a new policy or infer claim kind from prose.
  Cross-vendor review found the prompt also needed the existing relation
  composition rule, including counter-under-counter becoming effective
  support; the accepted patch states that rule and tests all nine relation
  combinations. The third provider attempt retained all 156 meanings in a
  valid packet. Home adjudication accepted its qualified redness common core
  but conservatively split one moisturizing/hydrating disjunction into three
  source-exact groups. The new controller-authored successor has 130 nodes,
  17 unchanged unmerged meanings, and 127 unchanged prior nodes; it is not a
  fresh provider answer or a repeat-stability result. Replacement nodes do
  not inherit opposition clearance. Original attempts and frozen inputs remain
  unchanged. PR #1529 records the adjudication and proof pointers; no new
  provider stage or standing review ceremony was added. Full Dieux completion,
  full-corpus cost, and final-prompt repeat stability remain unproven.
- `v80` / 2026-08-30 — fixed public calibration reopening: keyed prompt schema
  metadata was lost by the disk loader, so valid saved v8-v11 prompts disagreed
  with their producer. The regression reached that public boundary before the
  repair; separate altered-primary and altered-cold controls still fail there.
  Actual Dieux method-v11 calibration (84 rows, separate six-row repeat) then
  exposed bundled meanings and a lost explicit repurchase-reason link after
  row verification. Its reconciliation response also failed the existing
  customer-proof posture guard. These failures remain failures, not latency
  diagnoses or a reason to relax validation. Run v10 / method v12 / verifier
  v11 reconciles the conflicting generic-approval instructions and clarifies
  existing per-unit checks. It adds no provider stage or prose classifier and
  does not restamp prior answers. The successor proof separately discloses
  exposed regression gold, two corrected test-expectation errors, and three
  fresh source-authored holdouts. No accuracy or completion claim follows from
  adding the route; real calibration and final consumers remain required.
- `v79` / 2026-08-30 — repaired calibration's stale v5/v6/v7-only admission
  and v7-only mandatory-verification checks by consuming the existing
  production-owned `SEMANTIC_METHODS_V7_PLUS` set at admission, primary
  evaluation, and cold-repeat evaluation. Reached during Dieux completion:
  the current method-v11 run could not enter the required readiness check.
  The fix adds no semantic method, provider call, schema, or new gate; keyed
  response identity remains bound by the existing route fingerprint. Existing
  historical replay stays isolated. Passing checker tests or preparing Dieux
  inputs does not establish semantic accuracy or full-corpus readiness.
- `v78` / 2026-08-30 — removed foreign example axis IDs from current shared
  policy prose under run v9 / integration v11 / verifier v10. The supplied
  inventory owns IDs; semantic judgment owns fit; existing validators reject
  foreign IDs. Preserved historical method bytes and verifier replay. Added no
  model stage, axis translator, or claim that this fixes provider latency.

- `v77` / 2026-08-30 — isolated the keyed initial-batch response transport from
  downstream provider prompts after Dieux row-verification preparation rendered
  both a keyed-object instruction and the row verifier's required decisions
  list. Row verification method v9 binds the stage-local transport rule;
  targeted audit and reconciliation also omit the incompatible batch-only
  instruction. Initial batch prompt bytes and historical row-verifier v8 text
  remain intact.
- `v76` / 2026-08-30 — added run v8 / method v10 / keyed transport v3 after
  Dieux batch-0017 produced a semantic unit with an empty subject-product list.
  The ordinary validator rejected it; the provider schema had omitted that
  already-required minimum. Current schemas now require one subject ID per
  semantic unit. The boundary does not choose or repair product identity, and
  historical v9/v2 replay remains intact.
- `v75` / 2026-08-30 — added run v7 / method v9 / keyed transport v2 after two
  identical Dieux batch-0018 attempts labeled one top-level community post
  `personal_agreement` solely from the word `second`; both failed the existing
  no-parent validator. The per-evidence provider schema now excludes that
  posture only when the immutable row has no parent-context reference, while
  preserving it for actual replies. This is deterministic prevention of an
  already invalid combination, not a prose classifier or semantic relabeler.
  Historical v8/v1 replay remains intact.
- `v74` / 2026-08-30 — added run v6 / method v8 keyed batch-response
  transport for current authoring. Each provider response now fills exact
  schema-required evidence-ID object keys, which removes the recurring model
  task of copying long identifiers while keeping all method-v7 semantic rules
  and downstream compilation unchanged. Prompt and execution-pack preparation
  persist the exact per-batch provider schema, and execution-pack verification
  rejects missing, altered, or extra schema files. Historical run v5 / method
  v7 grouped responses replay under their original identity. Added zero
  provider stages and changed no evidence meaning.
- `v73` / 2026-08-30 — made retrospective current-source replay accept the
  already preserved www-Reddit and Soko Glam/Okendo shapes without rewriting
  historical collection artifacts. A www conversation container now carries the
  source-declared comment total, a `partial` completeness posture when the
  capture fell short or left continuation links unfollowed, and the named
  shortfall in its capture boundary, instead of asserting that no
  source-visible total exists. Soko review IDs are rederived from the
  pinned product slug and ordinal; retailer census and materialization now
  reparse the complete pinned source set, require exact readable-row coding,
  and preserve source-native non-text rows as mechanical exclusions. A Revolve
  completion receipt remains mandatory when Revolve is present but is no
  longer an unrelated gate on non-Revolve corpora. Post-level community coding
  now carries its run-local product and axis bindings just as comment-level
  coding already did. Added no provider stage, semantic inference, collection,
  frozen-output mutation, Deliver claim, or semantic response-transport change.
- `v72` / 2026-08-29 — added a pinned, current-spec-only bounded relation
  adjudication input at the existing preselection finalization seam. The
  current-policy ownership refresh at `7888c532` reached seven successful
  provider calls (580,100 input and 47,470 output tokens) but stopped when two
  rows selected the same Marshmallow meaning as both support and adjacent.
  This ambiguity had already been explicitly judged adjacent; wholesale
  regeneration reopened it. Corrections now bind the exact point, complete
  source/inventory and judging policy, survive row/batch presentation changes,
  preserve original responses, and fail on stale or unmatched bindings. No
  provider stage or semantic classifier was added. This does not prove the
  chosen judgment true, eliminate fresh-authoring cost, or complete Phase A.
- `v71` / 2026-08-29 — adjudicated cross-vendor correction to the v70
  scope-reading rule: input source identity is not person identity; read
  origin keys with independence posture and attribution, and check overlap
  before describing opposed rows as separate authors. The shade dogfood has
  one `full-corpus` source ID across 1,021 candidate rows and 538 distinct
  origin keys: 497 credited keys across 955 rows, plus 41 unavailable-identity
  keys across 66 rows, not 538 proven people. One credited account supplies
  both Vanilla-favorite observations. Joint favorites do not oppose a
  non-exclusive favorite claim merely by naming another option. The review's
  unconditional key-to-person and key-to-refinement wording was not retained.
  Text correction to existing judgment and reader guidance; no new provider
  stage, consumer boundary, schema, or frozen artifact mutation. Changed
  guidance invalidates scoped reader cache inputs as designed. Semantic
  adequacy and improved reader quality remain unproven until observed.
- `v70` / 2026-08-29 — made actor scope explicit in current selection spec v2
  and carried it through existing judgment calls and both reader consumers.
  Missing scope, unresolved focal identity, foreign-origin focal relations,
  changed consumer scope, and conflicting relations on identical point-local
  evidence/ref-set bindings fail visibly; no deterministic prose classifier
  or additional provider stage was added. The two shade failures originated
  in unbound actor scope, not the latest relation-facing display projection.
  Historical v1 selection replay and frozen artifacts retain their bytes.
  Scope adequacy, semantic truth, full-axis quality, and Phase A completion
  remain separate claims; previous blind wins do not establish this change.
- `v69` / 2026-08-29 — adjudicated the returned all-axis review: accepted the
  companion-field and headline quote-owner fixes, and closed the remaining
  structured-reader quote-ownership gap in the same work unit. Companion fields
  no longer inherit primary semantic values; both reader consumers share one
  quote projection. Freshly hash-bound current and v2 fixtures prove that an
  honest companion-only unavailable quote passes and the neighboring quote
  fails at the reader-output boundary. The earlier blind comparison remains
  evidence for its pinned output bytes, not a new quality judgment of the patched
  displays. No frozen source mutation or additional provider stage is required.
- `v68` / 2026-08-28 — completed the bounded Summer Fridays Phase A all-axis
  consumer proof and corrected only defects observed at the current consumer.
  The point reader had exposed a selected row's primary quote while its relation
  was bound only to a same-evidence companion meaning; current projection now
  shows the exact relation-bound meanings and keeps the selected row and quote as
  lineage, using explicit relation-facing quote unavailability for a
  companion-only binding. The no-frontier response schema now types its two
  provider `const` strings instead of relying on a provider-invalid untyped
  constant. Bounded relation review corrected three hydration rows without
  mutating frozen evidence: two support/counter errors and one causal wording
  exposure rebound to an existing non-causal same-evidence meaning. A value
  reader sentence was narrowed from `independent` to `separate credited`; source
  identity never proves independence. The final 12-axis primary/mirror set
  preserved exactly 50 accepted points, 14 rejected points, and 184 no-frontier
  candidate rows with zero current critical errors and 22 current wins versus 2
  historical wins. A required fresh repeat resolved coverage in both positions;
  packaging remained position-sensitive and is `INCONCLUSIVE`, not forced to a
  winner. The 154-unit Decision State review changed 43 judgments, but was
  same-family rather than vendor-independent. Separate prompt canaries disagreed
  with that reviewed authority on 7 of 83 and then 6 of 83 rows, so repeated
  provider judgment is not treated as a deterministic semantic oracle. These
  results prove current transport, attachment, accounting, and consumer quality
  under that owner-accepted review tradeoff; semantic truth, vendor independence,
  market prevalence, causal force, and Deliver conclusions remain unproven.
- `v67` / 2026-08-28 — replaced positional reuse of historical Decision State
  rows with run-scoped semantic-identity delta reconciliation. The temporary
  all-axis proof driver had copied bindings by `point_id` plus `selected_id` and
  changed only relation refs, which could transfer a plausible state bundle to
  the wrong meaning after regrouping. Current preparation now reuses only one
  unambiguous complete historical bundle for an unchanged evidence/ref/content
  identity; new content, conflicting history, and incomplete grouped states
  remain explicitly unresolved. Finalization requires exact delta coverage and
  proves the compiled v4 specs at the ordinary reader consumer. Relation remains
  point-relative and comes only from the current v3 artifact. This is a
  per-run compiler rather than a global registry and adds no provider call when
  all meanings are stable. Deterministic reuse does not prove semantic warrant.
  Summer Fridays dogfood rebuilt all nine point-bearing packs twice from the 50
  finalized point artifacts, then reconciled 253 Decision State rows across 25
  points. Of 739 unique semantic units, 585 reused one unambiguous judgment and
  154 units affecting 62 rows remained for bounded adjudication (37 conflicting
  history; 117 new units). Two preparations were byte-identical and took 2.568
  and 2.559 seconds; one 154-unit provider call finalized all nine current specs
  through the ordinary consumer. The Hype/trust canary caught and removed three
  request-contract defects before that run: a provider-invalid untyped `const`,
  a response hash absent from the prompt, and independently enumerated state
  kinds/directions that allowed contract-invalid pairs. Those are transport and
  compilation observations, not proof that the 154 judgments are semantically
  correct or that reader quality improved. Full-view validation remained the
  dominant deterministic cost at 489.704 seconds.
- `v66` / 2026-08-27 — replaced current v9 quote transcription with
  `row_owned_token_span_v1` inside the existing quote call. All-axis completion
  dogfood first observed 13 of 39 long-body point responses fail the exact or
  complete-boundary consumer; one bounded correction still left 9 point
  failures and exposed quotes copied under another selected row. Current schemas
  now bind each selected row to one source body and its allowed token addresses;
  the provider returns only inclusive start/end addresses, and deterministic
  finalization copies the exact source characters. Foreign bodies, foreign
  tokens, reversed spans, transcription-shaped responses, and changed bodies
  fail locally. The change adds no provider call, retry loop, prose classifier,
  quote-length ceiling, frozen rewrite, or Deliver judgment. Structurally valid
  span adequacy remains not mechanically proven. A first 9-failure-plus-canary
  dogfood finalized 10 of 10 token-span responses but exposed an avoidable
  899,188-input-token enum schema. Replacing per-row token enumeration with a
  body-bound token pattern reduced the hydration schema from 409,055 to 25,063
  bytes and the unaffected reaction canary from 203,885 to 30,379 bytes; both
  lean-schema calls finalized on their first attempt using 97,694 input tokens
  in aggregate. This is transport and failure-boundary evidence, not semantic
  quote-quality proof. Historical v7/v8 text responses retain their stamped
  replay and boundary behavior.
- `v65` / 2026-08-27 — retired the selected-row v3 provider review and made
  explicit row-owned relation bindings mandatory in current authoring. The
  existing hidden-label preselection confirmation now returns the smallest
  nonempty primary-or-same-evidence companion semantic-ref subset with each
  relation (`phase_a_evidence_quote_manifest_v9`); the v3 selection artifact
  carries it unchanged, and the v4 consolidation spec must repeat it for every
  displayed Direct Outcome and Decision State row. Builder and readers reject
  missing, duplicate, foreign, cross-point, cross-evidence, omitted, or changed
  attachments. They prove row ownership and transfer integrity, not whether the
  judgment-authored subset semantically warrants support, counter, or adjacent.
  This removes one unbatched selected-row whole-axis provider call without
  removing the pre-existing batched semantic confirmation. It adds no provider
  stage, deterministic prose classifier, consensus loop, adapter, frozen
  rewrite, permanent canary, or Deliver judgment. Historical v1/v2
  consolidation specs and v7/v8 quote manifests remain replayable.
- `v64` / 2026-08-27 — recorded the now-rejected selected-row v3 experiment.
  Its exact canonical-policy candidate was not the shipped v3 prompt and was
  position-unstable: two shade runs flagged 14 and 59 rows, while four formula
  runs flagged 6, 4, 5, and 4. Four earlier attempts failed before reaching the
  provider because of orchestration configuration. Repeated stability of the
  shipped v3 prompt is unmeasured because each axis had only one historical run;
  that prompt also condensed canonical policy into a third policy. The 24 shade
  and 3 formula flags remain unadjudicated allegations. This evidence supported
  retiring recurring ceremony in favor of a lower deterministic attachment
  boundary; it did not prove those rows wrong, semantic truth, reader-quality
  improvement, or that all semantic provider cost disappeared.
- `v63` / 2026-08-27 — tightened every Phase A point-relation prompt after the
  final all-axis dogfood proved that broad sentiment direction still overrode
  the bounded predicate and actor scope. The recurring failures included a
  conditional future repurchase promoted into an aim to finish, liking or
  purchase intent treated as ownership evidence, non-exhaustive shade lists
  treated as non-ownership, and a different actor's preference treated as
  changing a named actor's private state. Support and counter now require the
  same asserted judgment or behavior state, material object and condition,
  load-bearing actor scope, and—where applicable—the same superlative,
  assortment, and attribute scope. Materially overlapping but non-equivalent
  states remain adjacent; product-family or axis overlap alone is excluded.
  Focused unit validation passes 156 tests. A fresh seven-case cold dogfood
  returned the exact expected relations for completion intent, ownership,
  actor identity, and a different-flavour formula comparator, but it applied a
  condensed restatement of the boundary rather than the shipped prompt string.
  This proof's production relation and confirmation waves exercised the
  asserted-state, superlative, and adjacency-floor sentences on real candidate
  pools; the cross-actor, ownership, and completion-intent sentences appear in
  no production prompt in that proof root and stay unexercised outside the
  condensed dogfood until the affected shade points are regenerated. The first
  canary receipt is intentionally retained as a proof-expectation failure:
  exact object scope correctly excluded an e.l.f. dupe from a Trader Joe's
  ingredient point. The corrected receipt passes. The pre-fix shade consumer remains a
  stable current critical failure, so the run stopped without rewriting frozen
  outputs or claiming Phase A completion. Historical token deltas remain
  `NOT_COMPARABLE`; no Deliver or price-savings claim follows.
- `v62` / 2026-08-27 — made bounded-point relation judgment preserve every
  material qualifier after hydration dogfood exposed two recurring promotions:
  generic drying had been admitted as severe drying, and similar drying or
  cracking had been admitted as the same experience without an explicit
  comparison target. The initial relation prompt and every pre-selection
  confirmation route now keep broader, weaker, or merely similar outcomes
  adjacent. Severe reactions or consequences do not establish severe drying
  unless the source explicitly links them to drying; terse agreement may still
  adopt an exact linked parent's experience. A fresh current-format hydration
  pack rebuilt byte-identically twice, retained all 10 accepted and one rejected
  frontier members plus all 8,360 candidate dispositions, and changed only the
  two source-proven point artifacts. Point-local compilation reused nine of ten
  inputs after the final correction. A fresh mirrored comparison preferred the
  corrected current reader in both positions with no current critical error.
  The model judge's error labels remain allegations until checked against the
  authoritative view and literal source; reader preference cannot create or
  erase factual failure. Frozen production artifacts remain unchanged, and no
  Deliver claim or all-axis completion claim follows.
- `v61` / 2026-08-26 — closed the two recurring reader defects exposed by the
  frozen 12-axis comparison without reviving its temporary hydration bridge.
  Point brief v4 now carries each selected placement's exact
  `point_relative_meaning`; two meanings attached to one literal quote can no
  longer collapse into an unexplained repeated quote or contradictory relation
  label. A dedicated no-frontier reader now validates the complete v2 pack,
  presents every candidate once in a compact columnar request with deduplicated
  parent contexts, exact evidence IDs, and scoped origin keys; accepts only one
  to five in-pool candidate handles; and deterministically expands those
  handles to complete frozen source rows. Request-native parent-context wording
  preserves an empty context list as unresolved rather than proof of a
  self-contained source. Its
  output fixes relations to `not_applicable_no_admitted_frontier_point` and
  keeps displayed-example count separate from the full candidate count.
  Frozen coverage and packaging dogfood rebuilt byte-identically at 121 and 63
  rows. Their requests were 127,013 and 68,999 bytes versus the retired
  temporary prompts' 357,594 and 163,294 bytes. The two valid live calls used
  98,183 input tokens, zero cached input, 794 output tokens, and 43 reasoning
  tokens versus 185,262 historical input tokens under the same two
  no-frontier whole-axis call definitions; the current outputs retained exact
  source, date, engagement, semantic, origin, and parent-context recovery for
  all ten selected examples. Both final calls succeeded on their first attempt;
  the receipt at
  `C:\tmp\forseti-phase-a-smallest-complete-20260826-v1\DOGFOOD_RECEIPT.md`
  records the exact request/output hashes, usage, timing, and the limit that raw
  provider JSONL was not separately persisted. A different-vendor review found
  the first compact table exposed origin counts only in aggregate; home
  adjudication rejected its contradictory overall PASS, added evidence/origin
  identity to every model-visible row, corrected stale parent-context wording,
  and reran both axes. Current
  point-format hype and shade snapshots also rebuilt byte-identically and
  recompiled 15 historical handle selections with all 50 representative
  meaning blocks present. Hydration remains intentionally unobserved at the
  final current-reader boundary because its only frozen pack is legacy-format;
  no adapter or estimated token usage was retained to manufacture coverage.
  This change does not relabel the frozen shade or hype relations and does not
  claim all-axis Phase A completion.
- `v60` / 2026-08-26 — completed the frozen 12-axis reader comparison without
  making legacy hydration a permanent current-reader input. The old hydration
  pack predates the embedded axis-pack identity, complete lineage, and typed
  rejection disposition required by the current point reader. A temporary
  different-vendor-reviewed bridge (patch SHA-256
  `b8d864b72fd3c489a55c4a93ffbabad6e5628c4496ca6d79b646e19784420a3e`)
  supplied only that measurement route; review first corrected an unpinned
  quote-file hash entering point identity and a weaker legacy accounting gate.
  The bridge was never committed, pushed, opened as a PR, merged, or retained
  as product behavior. The final reader accepts current-format packs only;
  legacy hydration remains available to its existing historical
  consolidated-view replay and fails loudly at current reader accounting.
  Across the measured current readers, all 53 consumer calls succeeded over
  exactly 50 accepted points, 14 rejected points, and 184 no-frontier rows:
  2,128,742 input tokens, zero cached input, 21,155 output tokens, 4,124
  reasoning tokens, 4,329,673 request bytes, 67,552 response bytes, and
  675,803 ms summed provider-active time. Thirty-four mapped blind judgments
  produced 29 current wins and five historical wins, but this is not an
  all-axis quality-improvement claim: shade had stable current critical
  relation errors; hydration and hype retained position-linked critical
  classification; coverage resolved to a historical win; and packaging
  remained position-inconclusive. Scent, value, texture, formula, reaction,
  and wear were stable current wins without current critical classification;
  the rejected-only application explanation resolved the same way after its
  required fresh pair. The run showed why the historical consumer shapes are
  retired for current work: several omit rejected or full-pool accounting,
  lose literal recoverability, or turn no-frontier candidates into patterns;
  three axes had no receipt-bound historical reader output at all. It also
  showed that point-local structure does not cure a bad frozen relation, so no
  reader patch hides those failures. Historical latency and token deltas remain
  `NOT_COMPARABLE` wherever call definitions differ. The immutable measurement
  receipt is
  `C:\tmp\forseti-phase-a-all-axis-proof-20260826-v0\MEASUREMENT_BRIDGE_CLOSEOUT.md`;
  absence of a current-format hydration pack means the final adapter-free
  reader is not yet proven across all 12 axes.
- `v59` / 2026-08-26 — added the scalable point-local reader after a complete
  routed v2 axis is built. Each accepted point now has a path-independent,
  meaning-bound input fingerprint and content-addressed request, response, and
  compiled brief; unchanged point work can be reused across a changed whole-axis
  snapshot, while changed method, schema, subject, axis, facts, lineage, or
  Decision State creates a new identity. Deterministic code restores literal
  evidence and the complete Decision State ledger, and final assembly emits no
  axis output until accepted plus rejected membership is exact. Snapshot
  validation and point-file reading remain linear rather than repeating the
  whole axis for every point. Cross-vendor adversarial recheck closed stale
  response reuse, repeated validation, snapshot-scoped brief reuse,
  store-optional validation, label-addressed requests, and state-identity
  shadowing; texture dogfood plus a frozen-value sample reproduced exact reuse,
  failure visibility, and state separation. Added no evidence authority, global
  index, prevalence or Deliver judgment, interpretation-method change, or
  frozen v1/v2 output mutation.
- `v58` / 2026-08-25 — versioned new bounded-point quote manifests to v8 and
  removed the 220-character semantic ceiling. The threshold remains only for
  deterministic full-copying of short bodies and external-review workload
  selection. Longer evidence now carries the shortest context-complete
  contiguous exact span needed for its meaning; length alone cannot reject a
  truthful frontier relation. V7 remains exactly replayable under its stamped
  ceiling, and new runner authoring no longer exposes the legacy unquotable
  rejection path.
- `v57` / 2026-08-22 — closed the delegated-review recency edges: every
  admitted ISO publication-time shape now resolves to a calendar year;
  unavailable engagement cannot sort ahead of an observed native metric;
  value-first specs reject the non-value recency-selection policy; and the
  timeline is explicitly an ordering index whose selected IDs retain their
  truth-versus-influence layer through `source_groups`. No packet, stored source
  fact, relation authority, or historical artifact was rewritten.
- `v56` / 2026-08-21 — expanded non-value frontier points from literal-only
  proposition refs to the complete same-product axis candidate union while
  retaining exact bounded-point judgment and the thirteen-origin display cap.
  Added named batching for the v7 preselection confirmation frontier, so full-
  axis breadth does not reopen long-array omission or allow first-pass labels to
  choose the cap unchecked. Added a bound two-calendar-year representation
  preference plus one eligible dated historical anchor and a neutral selected-
  row timeline. Age changes presentation only; packet v3, source facts,
  relation semantics, value-point admission, prevalence boundaries, and
  cross-platform engagement prohibitions are unchanged.
- `v55` / 2026-08-21 — changed customer-pull frontier ordering so independent
  supporting-origin count leads, followed on ties by cross-role recurrence and
  materially engaged supporting items before reported behavior. Behavior
  remains a final tie-breaker, preventing generic trial or ownership from
  monopolizing the top queue while preserving purchase, repurchase, return,
  and recommendation evidence. Unavailable engagement earns no materiality;
  protected lanes preserve admission but grant no ordering priority. Packet
  v3, ordinary point admission, retailer-first routing, and the thirteen-origin
  cap are unchanged.
- `v54` / 2026-08-21 — closed the delegated review false green by requiring
  preselection confirmation labels to pass the same creator-layer and reason-code
  guards as the first pass. Made subject-filter exclusions and counts explicit in
  the customer-pull frontier, scoped the new bounded-point relation definitions so
  legacy v6 from-spec prompt hashes remain reproducible, and corrected the live
  v6 versus frontier-v7 route wording. Packet v3 and the thirteen-origin cap are
  unchanged.
- `v53` / 2026-08-21 — added the hash-bound retailer-first customer-pull point
  frontier over a complete proposition-mode v3 packet. Retailer is the
  first-look venue, not an admission gate; community-only customer points stay
  visible for retailer check-back, creator-authored material stays outside
  customer truth, and every proposition receives one queue or nonpromotion
  disposition. Added v7 point-pack preparation, which confirms every material,
  protected, or influence row before the thirteen-origin display cap and
  reselects from the corrected relations. This prevents a first-pass reversed
  relation from silently discarding high-engagement or protected evidence.
  Packet v3, venue-relative engagement, legacy v6 reproduction, and downstream
  Deliver authority remain unchanged.
- `v52` / 2026-08-21 — made one completed selection artifact one bounded
  evidence-point pack, raised the default customer truth-origin cap from ten to
  thirteen, and added explicit pool-to-display accounting. New quote manifests
  are v6 and require a separate hidden-label confirmation of every selected
  relation before finalization. A disagreement fails closed; quote extraction
  stays separate after the combined relation-plus-quote pilot clipped a source
  phrase. Historical v1/v3/v4/v5 manifests retain their stamped behavior. Added
  no packet v4, prevalence estimate, cross-platform engagement score, or
  relabeling of the complete candidate pool. Delegated code review corrected
  three defects inside this change before landing: the confirmation rows were
  presented in selection order under first-pass `selected_id` handles, which
  handed the confirming workload the selection priority the manifest recorded as
  hidden; the confirmation manifest was accepted on its binding hashes alone
  rather than re-derived, so a hand-written manifest could vouch for a workload
  that saw the labels; and `presentation_basis` asserted boundedness and a
  cap-driven funnel that the runtime never establishes. Home adjudication
  completed the funnel repair by recording the truth selection policy in v6
  and deriving the exact display-eligible truth-origin count from the same
  predicate the selector uses. It also closed the broad-axis false green by
  adding a `single_point` versus `broad_axis_or_bundle` decision to the existing
  confirmation call; broad scopes now fail before artifact completion without
  adding another provider workload.
- `v51` / 2026-08-21 — prohibited a long exact-quote span from starting with an
  unresolved pronoun when the nearby antecedent fits under the existing
  220-character ceiling. Product identity may still rely on the evidence row,
  avoiding the broader rejected rule that made seven usable hydration quotes
  unavailable. Also required the selected span to substantiate every material
  component of the normalized meaning, retain nearby qualifications, and avoid
  mid-phrase clipping after both mirrored fresh-pack judges rejected shorter
  but materially incomplete spans. This closes the observed quote-quality
  near-misses without changing packet v3, source facts, relation transport, or
  selection.
- `v50` / 2026-08-20 — closed the returned cross-vendor batching review. Each
  batched response now carries its required single-valued batch identity, and a
  v5 quote manifest binds the actual relation batch manifest plus every
  canonical response hash. Generic relation-derived labels remain presentation
  metadata and cannot justify quote relevance without the source-owned meaning.
  Added no packet version, value-policy change, capture, or semantic replay.
- `v49` / 2026-08-20 — kept ten customer origins as the presentation default
  while allowing an explicit one-through-twenty cap; the measured full-axis
  hydration pack binds fifteen because fifteen beat ten and twenty did not beat
  fifteen, on a same-vendor mirrored judge. Added hash-bound non-value relation
  batching with at most 300 candidates, required named row slots, and a required
  single-valued `batch_id` per response, so a truncated long response fails
  before selection, a transposed or stale batch response fails before selection,
  and candidate IDs and facts remain deterministic. Recorded that a batched row's
  reason label is derived from its relation and is therefore not a source-meaning
  code. Value selection, packet v3, creator separation, and cross-platform
  engagement boundaries are unchanged.
- `v48` / 2026-08-18 — corrected completed-use handling and chronology. Time to
  finish or pan is no longer quantity-efficiency/value evidence by itself; an
  explicit same-source repurchase remains direct repurchase intent. Longer-body
  quotes may express the selected label through the exact companion meaning
  that justified it. Semantic-source builders now preserve Reddit, Sephora,
  Amazon, and Revolve publication times, while the selection consumer can
  rehydrate dates for completed packets only from hash-bound source artifacts.
  Added no packet version, value score, search-trend inference, or provider call.
- `v47` / 2026-08-18 — made an explicit-reference-only bounded selection inherit
  the value policy when every admitted candidate carries `value_and_quantity`.
  Mixed explicit-reference sets remain generic, and the named references still
  bound candidate admission rather than expanding to the whole axis. Added no
  selection-spec field, packet version, provider call, or production-output rewrite.
- `v46` / 2026-08-18 — added one sparse, claim-specific counter meaning for
  explicit substantial completed spending followed by cost-linked buyer’s
  remorse. Multiple units alone do not qualify. The meaning does not add
  lifecycle fields to origins or infer repurchase,
  transaction count, or future intent; ordinary cost-linked regret keeps its
  existing reason.
- `v45` / 2026-08-18 — tightened value classification after a real-corpus
  challenge exposed sunk-cost rationalization being mislabeled as good value.
  Explicit regret, waste, or poor value now keeps every candidate from that
  evidence origin counter or adjacent unless the same source explicitly buys
  or repurchases again despite the cost, or concludes the product is worth the
  price. Price-plus-purchase behavior must use its `despite_price` label rather
  than a plain behavior or generic good-value label.
- `v44` / 2026-08-18 — closed the delegated value-selection review. Added
  real-entry-point tests that fail if any production value-policy wiring is
  disabled, curated every displayable value label, and replaced the accidental
  alphabetic complaint anchor with a semantic-signal-first anchor that never
  compares raw engagement across platforms. An all-complaint value set now
  shows one materially positive complaint instead of an empty box. Clarified
  that one same-evidence origin may jointly supply the price premise and
  purchase behavior, while explicit regret, waste, or poor value reverses a
  positive purchase inference unless the same source explicitly countervails
  it. Protected cross-venue ordering no longer uses raw engagement.
- `v43` / 2026-08-18 — made value-only selection direct and positive-first.
  Formula, hydration, scent, gift-card, trial-only, and generic purchase
  meanings cannot enter the value box through a companion-only warning. The
  599-score Strawberry-duo post remains available to its fitted axes but stays
  adjacent to value. Purchase and repurchase despite price are prioritized;
  one ordinary direct complaint may be shown only from the primary positive
  signal's comparable native-engagement bucket. The quote prompt binds the
  deterministic display label as well as the normalized meaning. Added
  relation-aligned value reason codes and fail-closed validation, but no packet
  v4, cross-platform score, provider call, evidence deletion, or production
  output rewrite.
- `v42` / 2026-08-18 — removed the redundant selected-row paraphrase and
  replaced the unlanded v2 quote-manifest experiment with v3. Customer display
  now uses a short evidence-signal label plus the exact quote and engagement /
  source metadata. The label is derived deterministically from the validated
  relation reason code, so the quote stage spends no output tokens inventing
  it. Internal claim-relative relations remain stored but cannot leak into the
  label. Real value labels distinguish repurchase despite price,
  appeal outweighing price concern, explicit worth, price-to-quantity value,
  insufficient product, unjustified performance, and price-blocked repurchase.
  Legacy v1 still replays exactly; the superseded v2 scratch artifact was never
  production output, pushed, merged, or published.
- `v41` / 2026-08-18 — added a required selected-row
  `presentation_statement` to new v2 quote manifests so the consumer, rather
  than a later chat author, records the concise commercial reading. It groups
  same-source same-action meanings such as Vanilla and Vanilla Beige repurchase
  while preserving both atomic semantic refs, the exact quote, and provenance.
  Removed repetitive presentation boilerplate about implied population and
  value limits; the underlying claim-support boundaries remain unchanged.
  Legacy v1 quote manifests remain readable. Added no score, packet version,
  evidence replay, or provider call inside the repository runner.
- `v40` / 2026-08-18 — made the value-context correction explicit. Value-axis
  admission is direction-neutral; relation labels remain relative to the
  bounded claim; price discomfort is distinct from poor value; and
  purchase/repurchase despite price may be presented as a positive
  willingness-to-pay signal while countering a poor-value claim. Allowed
  lossless display grouping of same-evidence same-action meanings while keeping
  their atomic semantic refs and provenance. This records the regression lesson
  exposed by the 204-point repurchase comment and the multi-purchase “cute, I
  can't not” comment: do not clip or isolate the price clause from the behavior
  that changes its commercial meaning. Added no value score, prevalence claim,
  commercial-pull score, packet version, or provider call.
- `v39` / 2026-08-18 — added the optional hash-bound Phase A
  selection-and-exact-quote consumer. It accounts for every axis- or
  literal-ref-admitted candidate before capping source-grouped presentation,
  fails closed on an operator nomination that cannot resolve, separates
  customer truth support from creator influence, ranks engagement only inside
  comparable native-metric buckets over publisher-normalized venues, preserves
  distinct same-origin relations/conditions, and verifies exact quotes against
  a content-verified bundle body. Lane reservation is origin-level, so lane
  visibility in the displayed set is not guaranteed; `source_body_present`
  separates a missing body from a body that yielded no quote.
  Kept packet v3 and completed semantic outputs immutable; added no provider
  call, prevalence estimate, causal claim, commercial-pull score, or new
  evidence authority.
- `v38` / 2026-08-17 — added the owner-authorized, no-provider
  `migrate-repaired-terminal` successor for a completed policy-v2 terminal
  compilation after selective whole-row repair. Reuse now requires complete
  old/new leaf equality; polarity-only defects may be deterministically
  rederived; compatible exact identities coalesce under must-agree, union, and
  conflict-visible rules; and every input, leaf, invalidation, reuse, unmerged
  unit, and coalescing decision is hash-bound. The route preserves the finalizer
  duplicate guard, never claims relation closure, and falls back to fresh
  reconciliation for broader proposition-linked semantic changes. A rederived
  node retains its source `child_relations`; flattened leaf relations never
  replace its prior-level child lineage. Changed unmerged rows preserve their
  old membership and reason without claiming fresh semantic adjudication.
  Enforced the existing v35/v36
  lossless-engagement rule for legacy bundle observations carrying one explicit
  `raw_*` source-native metric: the raw field name supplies the metric kind, the
  stored value and materiality basis remain literal, and ambiguous or unknown
  shapes fail instead of becoming `engagement_unavailable`. Also brought
  `finalize-v3` into conformance with the existing rule that only complete
  validated closure may report `none_observed`: a node's local
  `opposition_checked` no longer promotes a proposition's `conflict_posture`,
  which now stays `not_checked` on every policy-v2 route, not only the
  migration route. This changes no contract rule, but it does change emitted
  view values, so a previously pinned v3 view containing an affected
  `none_observed` value no longer reproduces and must be regenerated before
  reuse.
- `v37` / 2026-08-17 — adopted ordered batching for actually related Phase A
  proposition cases plus the decision-only response and deterministic v3
  rehydration seam. The measured six-family workload fell from 18 to 15 calls
  across three repetitions and from 436,309 to 347,228 logical tokens
  (20.417%) while the finalist reproduced 18/18 complete artifacts. Kept v3
  frozen and added fail-closed case/proposition/ref/row/engagement boundaries.
- `v36` / 2026-08-16 — made lossless named-default/column
  `phase_a_evidence_packet_v3` the normal Phase A evidence transport. Kept
  literal evidence and semantic-unit refs, source grouping, every relation and
  candidate class, native engagement, actor/independence data, conditions,
  uncertainty, and bundle resolution while removing repeated field labels and
  values. Added a fail-closed v3-against-v2 preservation boundary and retained
  explicit v2/v1 comparison routes.
- `v35` / 2026-08-16 — made `phase_a_evidence_packet_v2` the normal
  source-grouped consolidation output. Evidence and selected semantic units are
  stored once, propositions link to them by relation, native engagement metadata
  travels with each evidence row under its source group, and complete bodies
  remain resolvable from the bound bundle rather than duplicated inline. Kept
  the complete v1 selection and lineage proof, no evidence-count cap, no
  conclusion or score, and an explicit legacy-v1 reproduction option.
- `v34` containment correction / 2026-08-13 — made any artifact carrying
  closure-only evidence run closure-specific structural checks before generic
  finalization, and rederive exact candidate membership, all-pairs identity,
  and pair cardinality from class children. Recorded the 7,076-node Summer
  Fridays state as a dated, hash-bound operator observation; made the supported
  policy-v2 route and owner-only research reopen trigger explicit. This is
  malformed-artifact containment, not semantic proof against coherent wholesale
  forgery; historical v2 and valid v34 artifacts retain their interfaces.
  Landed in PR #1496 after its bounded external recheck returned `READY`.
- `v34` / 2026-08-13 — added opt-in corpus-global relation closure over the
  terminal normal-retention frontier. Exhaustive compiler-counted pair coverage
  now drives partition-independent equivalence classes and symmetric opposition;
  incomplete or unresolved coverage blocks finalization, and duplicate
  directional proposition identities fail closed. Added selective whole-row
  repair with parent verified-compilation lineage and untouched-row preservation.
  Historical policy-v2 artifacts and view v2 remain frozen.
- `v33` / 2026-08-12 — added the optional load-once prompt execution pack for
  long-lived workers. The pack hash-binds one shared method/schema/axes/catalog
  frame and one exact context-plus-evidence payload per existing work unit, and
  requires byte-identical reconstruction of every rendered standalone prompt
  string, which is one byte shorter than the stored `.md` artifact because the
  file writer appends a trailing newline. Verification is bundle-relative and
  admits no stored file the bundle does not name. Context stays batch-local; no
  semantic method, response, compilation, evidence denominator, prompt ceiling,
  worker topology, provider call, or readiness claim changed.
- `v32` / 2026-08-12 — versioned the whole-row verifier method to v8, prevented
  reaction-susceptibility traits from becoming unsupported hydration conditions,
  and preserved explicit usable-product loss or waste as separately retrievable
  `value_and_quantity` evidence. Added no category registry, schema, field,
  parser, second verifier, provider call, or full-corpus resume authority.
- `v31` / 2026-08-11 — versioned the whole-row verifier method to v7, resolved
  pronouns and evaluation scope from the whole conversation, separated explicit
  named-option ownership from later product-level judgments, and prevented
  extraction examples from fixing referent scope. Added no schema, variant
  catalog, parser, second verifier, provider call, or full-corpus resume authority.
- `v30` / 2026-08-11 — versioned the whole-row verifier method to v6, prevented
  local ambiguity from erasing safe row content, bounded ambiguous variant and
  echo meanings without guessing, preserved exact variant-versus-family scope,
  and kept explicit overall evaluations separate. Added no schema, field,
  parser, second verifier, provider call, or full-corpus resume authority.
- `v29` / 2026-08-11 — versioned the whole-row verifier method to v5, added a
  final source-to-unit completeness bijection, preserved same-dimension paired
  comparisons as separate relational meanings when textually established, and
  prevented baseline traits, vague category wording, or ambiguous antecedents
  from becoming product-caused outcomes. Added no schema, field, second read,
  parser, provider call, conclusion, or full-corpus resume authority.
- `v28` / 2026-08-11 — versioned the whole-row verifier method to v4, made
  complete-row replacement preserve all source-supported proposed content by
  default, aligned drying/non-drying with hydration, made named-shade behavior
  shade-specific, and blocked comparator-only statements from binding the
  target. Method-v7 claim-support projection now prevents
  `personal_agreement` from adding independent-origin credit. Historical
  verifier-v3 receipts remain identifiable but require replay, while historical
  semantic-method output remains frozen. Added no response, stage, manifest,
  bundle, or report schema; no
  second verifier, provider API, conclusion, or full-corpus execution.
- `v27` / 2026-08-11 — extended the existing verified-compilation intake to
  the reserved `cold-repeat` slice id. The evaluator now rebuilds and binds the
  raw cold compilation before grading its verified rows; method v7 requires a
  verified cold compilation whenever cold repeat is configured, and all
  methods block mixed verified/unverified consistency comparisons. Added no
  response, stage, manifest, bundle, adjudication, or report schema and no
  second verifier type.
- `v26` / 2026-08-11 — versioned the whole-row verifier method to v3 and made
  statement text obey the same customer-attribute boundary as structured
  conditions. Added optional calibration intake for an exact provenance-bound
  verified compilation; evaluation rebuilds and validates its primary input
  before using the active rows, rejects a supplied compilation that carries no
  row-verification manifest, and blocks a cold repeat when the primary and
  repeat do not share row-verification lineage. Retires method-v2-verified compilations,
  which must replay row verification. Added no response, stage, manifest,
  bundle, or adjudication schema; no provider API, mandatory second verifier,
  conclusion, full-corpus execution, readiness claim, or resume authority.
- `v25` / 2026-08-11 — versioned the row-verification manifest to v2, added the
  verifier method version and exact method-text SHA-256 to its hash-bound
  content, and required current reconciliation/finalization consumers to match
  both. Legacy-v1 or tampered method bindings now fail closed and must replay
  row verification. Added no response/stage field, semantic rule, provider API,
  extra verifier pass, conclusion, full-corpus execution, readiness claim, or
  resume authority.
- `v24` / 2026-08-10 — versioned the whole-row verifier method to v2 and made
  meaning inventory precede field checking. The verifier now restates each leaf
  as standalone meanings, preserves simultaneous or qualified judgments unless
  explicitly withdrawn, and maps every material meaning to a proposed unit
  before checking axes or other fields. Customer attributes condition only the
  same stated or unambiguously entailed baseline or one explicitly scoped by the
  source. A possible bias, caveat, or different response stays separate rather
  than becoming a condition. A conjoined attribute phrase splits so that only
  the part whose baseline the result reports qualifies it. Sensitivity alone is
  not a moisture baseline; product-linked sensitivity is reaction/tolerance
  context, while dry or dehydrated context may qualify moisture. Later context
  may narrow an earlier judgment but never silently replace it. Every returned
  field must be supported by the source or supplied context.
  Added no response/schema field, parser, phrase table, provider API, conclusion,
  mandatory second verifier, full-corpus execution, readiness claim, or resume
  authority.
- `v23` / 2026-08-10 — added run v5 / method v7 whole-row evidence
  verification between primary extraction and reconciliation. Every primary
  claim-bearing row now receives exactly one independent `accept`, complete-row
  `replace`, or `unresolved` decision; replacement rows reuse the ordinary
  semantic validator, original and verification lineage remain separately
  hash-bound, the manifest binds the exact active dispositions and semantic
  units, and reconciliation sees only the sole active result. Method v6
  extraction wording and historical artifacts remain reproducible. Added no
  provider API, lexical selector, conclusion, full-corpus execution, readiness
  claim, or resume authority.
- `v22` / 2026-08-10 — versioned the calibration adjudication ruler and bound
  its stable ID and full SHA-256 into preparation-v2 and report-v2 artifacts.
  Preserved preparation-v1 and report-v1 shapes for historical evaluation,
  accepted only the two exact known historical ruler hashes, and made the
  mixed-attribution and cold-repeat failure conditions explicit. Changed no
  extraction method, prompt, evidence schema, provider call, full-corpus state,
  readiness claim, or resume authority.
- `v21` / 2026-08-10 — added run v4 / method v6 as a meaning-preservation
  correction on the existing bundle-v5 transport. The semantic reader now
  assigns axes from the complete outcome and direction, preserves explicit
  causal and connected ownership/use meanings, distinguishes relevant customer
  attributes from nearby but unrelated ones, keeps category and value facts
  separate, and treats unmerged material as unconsolidated rather than
  unimportant. Preserved method-v5 text and every transport schema. Added no
  phrase table, high-value-comment subsystem, second read, provider call,
  recommendation, full-corpus execution, readiness claim, or resume authority.
- `v20` / 2026-08-10 — disambiguated logical polarity from comparative
  ordering in this contract's extraction and calibration wording. A directly
  asserted `less` or `more` comparison remains `affirmed`; logical
  constructions such as `not as`, `never`, and `does not` remain `negated`.
  The generated bounded calibration preparation now carries the same
  adjudication contract as a hash-reported sidecar, and calibration
  evaluation refuses a prepared sidecar whose bytes no longer match that
  bound contract. Extraction-side effect is doctrine only: the method-v5
  prompt text the extraction model actually reads is unchanged, which is why
  the frozen preparation identity is unchanged and why no extraction run
  behavior changed under this version. Added no sentiment classifier, phrase
  blacklist, provider call, full-corpus execution, readiness claim, or resume
  authority.
- `v19` / 2026-08-10 — kept method-v5/v18 semantic wording and blind gold
  unchanged while adding calibration spec v3's closed audit of the highest
  semantic-unit-density non-gold rows. Each selected row now requires an exact
  compilation-bound semantic bloat judgment; a confirmed defect fails and a
  missing, stale, or unresolved judgment blocks. Bound the Summer Fridays
  production carrier to two count- and byte-balanced prompts as a route probe,
  not a prompt-tuning pass. Preserved historical spec-v2 readability and added
  no provider call, prevalence estimate, full-corpus execution, readiness, or
  resume authority.
- `v18` / 2026-08-10 — tightened six general boundaries exposed by v17: a
  leading yes/no answer retains the parent question's predicate; generic praise
  is removed from a bounded value statement; logical negative constructions
  remain negated; peeling, not-drying, bare go-to behavior, and shade ownership
  receive only their directly supported axes; opposite experiences receive an
  explicit counter relation; and exact first-hand plus personal-agreement
  preferences may reconcile while preserving both actors and their shared
  thread. Added no phrase classifier, confidence score, schema, provider call,
  or corpus-run authority.
- `v17` / 2026-08-10 — made the existing independently-true atomicity rule
  operational in method v5: two clauses remain separate whenever either could
  change truth without the other, even with the same product, axis, or posture.
  Named the three v16 failure boundaries directly: target non-sinking versus
  target/comparator hydration contrast, not-most-hydrating versus not-drying,
  and present ownership versus sale-only future purchase. Added no new schema,
  universal evidence score, provider call, or corpus-run authority.
- `v16` / 2026-08-10 — added adjudication v3's closed per-unit meaning-direction
  judgment so an explicit unmerged unit cannot evade calibration merely because
  it creates no final proposition relation. Preserved v1/v2 read compatibility
  for historical reports while requiring v3 for current spec-v2 runs. Clarified
  that bare distinct-actor agreement is valid but low-information same-thread
  recurrence, and that `same` adopts only a clearly targeted bounded meaning,
  never every clause or reason in a multi-point parent. Tightened degree,
  non-sinking-versus-comparator decomposition, logical polarity, and smoothing
  axis instructions from observed v15 failures. Added no universal evidence
  score, provider call, route generation, or corpus-run authority.
- `v15` / 2026-08-10 — narrowed direction preservation to the semantically
  correct relation rule: support must match terminal direction, while a
  negated child may remain counterevidence to the inverse positive proposition.
  Required attribution to remain visible in echo statements, shade ownership
  to carry its supported axis, explicit ownership to remain atomic, and
  switching-to-other-formulas wording to remain affirmed. Reinforced retention
  of target/comparator hydration contrasts. Added no schema or corpus-run
  authority.
- `v14` / 2026-08-10 — required every atomic statement and terminal bounded
  meaning to remain truth-complete without relying on `polarity`, preventing
  negated children from becoming positive reconciliation claims. Clarified the
  already-required boundaries for embedded generic praise, ownership behavior,
  secondary two-product contrasts, and axis-free gloss-versus-balm category
  judgments. Added `meaning_direction_preserved` as a calibration relation
  obligation so independent adjudication can hard-fail final-view polarity
  loss. Added no lexical classifier, runtime schema, provider call, or corpus
  execution authority.
- `v13` / 2026-08-10 — corrected the context boundary for a short reply that
  uniquely adopts a bounded preference or product choice. The real chain
  `which is your favorite?` -> `Vanilla Beige!` -> `My fav!` is claim-bearing
  `personal_agreement`, with no axis donated by context. A distinctly credited
  agreeing actor may add same-thread recurrence for that exact preference,
  while the shared thread stays disclosed and neither first-hand experience nor
  cross-venue credit is inherited. Generic approval with only a known product
  remains `context_only`; no lexical blacklist or runtime schema was added.
- `v12` / 2026-08-10 — corrected method-v5's context boundary so a resolved
  product referent cannot upgrade generic approval or dislike into a detailed
  claim; added an explicit atomic-splitting self-check and made axis candidates
  vocabulary rather than assignments. Added hash-bound adjudication v2, which
  accounts for every assigned axis on every gold-case unit and fails explicit
  semantic non-support while retaining v1 read compatibility for historical
  reports. Calibration spec v2 explicitly requires adjudication v2 so a newly
  authored run cannot select the historical schema and skip the new gate. Added
  no phrase blacklist, provider API, full-corpus replay, route revision, seal
  obligation, or product-version vocabulary. A real calibration dogfood also
  exposed reconciliation dropping extraction posture before claim-kind choice;
  bundle v5 now carries posture through reconciliation and rejects an invalid
  customer-proof binding at level validation rather than only at finalization.
- `v11` / 2026-08-10 — added fail-closed bounded semantic calibration for the
  method-v5 route: blind hash-pinned gold, exact source projection, route
  fingerprints, production-shaped sentinel slices, deterministic validator
  reuse, explicit atom/relation/anomaly adjudication, and selectively repeated
  cold reads bound to both response compilations. Missing or stale semantic
  judgment blocks, critical mismatch fails, and every report disclaims
  prevalence, readiness, full-corpus completion, and resume authority. Gold
  containers are closed key sets, at least one case is required, and every
  claim-bearing case names an atomic meaning; evaluation rebuilds the expected
  preparation from the hash-pinned full source instead of trusting a self-hashed
  preparation receipt; a cold repeat cannot be judged consistent without its
  primary compilation. Runner revision and contract version are recorded as
  declared provenance, not enforced pins. Added no provider API, phrase
  blacklist, full-corpus replay, queue service, or product version vocabulary.
- `v10` / 2026-08-09 — added the run-v3 / bundle-v5 / projection-v2 / method-v5
  / response-v3 / compilation-v3 semantic generation for full-corpus execution.
  Required one mandatory context-aware relevance and accounting judgment per
  assessable leaf across a four-way boundary, made clearly empty generic
  reactions terminal at near-zero marginal cost, and added explicit-ID terminal
  grouping as transport compression with raw-occurrence validation before any
  dictionary or set construction. Bound the accepted raw response-v3 set through
  canonical hashes in compilation v3, removed static worker topology from the
  new projection, and made bundle/projection verification invocation-scoped with
  a global missing-work interface and controller-owned ephemeral coordination.
  Preserved the legacy v4 generation byte-exactly, added no queue service or
  persistent coordination subsystem, and made no latency, token, calibration,
  readiness, or seal claim.
- `v9` / 2026-08-09 — added the hash-bound product-identity catalog to each
  method-v4 final-acquisition work unit, required response subject/comparator
  product IDs to come from that catalog, barred unverified identity-bearing
  version IDs under catalog v1, and preserved per-leaf subject/comparator roles
  in mixed-product conversations. The catalog supplies vocabulary only: it
  adds no lexical product assignment, global registry, customer duplication,
  conclusion, campaign bridge, or historical bounded-proof rewrite. The v9
  method-text hash supersedes earlier method-v4 prompt bytes; older v4 bundles
  remain hash-distinguishable but are not reproducible under the current code.
- `v8` / 2026-08-09 — added a hash-pinned, run-local product identity table,
  method v4 cross-source customer-evidence semantics, and a deterministic
  bounded product/axis proof-source projection. Preserved wrong-product
  mentions as comparator, adjacent, unresolved, or out-of-scope material;
  retained historical run v1/method v3 reproduction; and made no current-route
  seal claim, conclusion, campaign bridge, provider call, or global registry.
- `v7` / 2026-08-08 — added bundle v4 accounting-by-reference, a hash-bound
  context registry and bijective work-unit projection, deterministic three-way
  no-API worker assignment and resumable per-partition status, and slim
  reconciliation prompts whose full lineage remains compiler-owned. One
  declared prompt batch owns each level's global emerging-label consolidation,
  so parallel batches cannot emit overlapping label decisions. Exact
  public-handle matches across venues now collapse to one conservative credited
  origin without claiming a unique person. Source v3, response/view/packet
  semantics, the prompt ceiling, the single-terminal-batch gate, and historical
  bundle v3 reproduction remain unchanged.
- `v6` / 2026-08-08 — added reusable full-corpus Reddit and retailer v3 source
  builders, exact SERP-target reconciliation against existing native captures,
  repository-relative locator enforcement, and separation of source
  materialization from prompt packing. A real Summer Fridays shadow compiler
  may now expose an honest no-API execution-capacity block without sampling or
  claiming that generated prompts were semantically judged. No route version,
  provider API, conclusion layer, or historical-seal obligation changed.
- `v5` / 2026-08-08 — added `phase_a_evidence_packet_v1`, a complete
  proposition/axis evidence-stack projection from the finalized v2 view. It
  de-duplicates shared records; preserves opposition, semantic posture,
  uncertainty, polarity, unresolved material, and unscoped unmerged meanings;
  exposes no top-k truncation or conclusion; and adds no provider API or new
  seal obligation.
- `v4` / 2026-08-08 — replaced the operator-declared Phase 1/2 packet
  denominator with a generated inventory from terminal-return-selected,
  hash-pinned Google SERP
  queue states. The seal now rejects missing or extra successful packets per
  job and exactly reconciles focused-search job packet sets. This is a
  correction to the unsealed Route 1.7 implementation; historical Route 1.6
  seals remain unchanged.
- `v3` / 2026-08-08 — narrowed exhaustive semantic processing to customer
  language in Reddit/community conversations and retailer reviews; introduced
  verified structured-reference routes for other evidence; pinned retailer
  source files and structural review identity; and added Route 1.7 bounded
  SERP-row-to-native linking with exact semantic disposition accounting. No
  provider API or historical seal rewrite was added.
- `v2` / 2026-08-08 — added the reusable full-corpus run specification,
  acquisition-route/source audit, customer-corpus census, v3-fragment
  materialization receipt, single-response validation, and resumable status.
  The audit rejects a duplicate route that names a non-owning route, and the
  census reconciles its captured-conversation union against both owning
  sources. These operations add no provider API and do not restamp historical
  seals.
- `v1` / 2026-08-08 — added Route 1.6 full captured-corpus accounting,
  containers and capture envelopes, prompt-bounded hierarchical
  reconciliation, response/view version changes, emerging-axis consolidation,
  and separated evidence-stack counts. Preserved every historical Route 1.4
  and 1.5 contract.
- `v1` correction / 2026-08-08 — carried immutable emerging-axis dispositions
  and the root batch-compilation hash through every reconciliation level so
  labels, lower-level blockers, and coincident-denominator lineage cannot
  disappear.
- `v0` / 2026-08-07 — introduced Route 1.4 semantic integration and Route 1.5
  source-pinned product context.
