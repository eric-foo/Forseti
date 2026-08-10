---
artifact_role: authority
status: current
owner: Judgment / claim support
version: v23
effective_date: 2026-08-10
depends_on:
  - forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md
---

# Semantic Evidence Integration Contract v23

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

Upstream `product_candidates` are hypotheses, not product truth. For the
current method, every admitted item also carries source-pinned product context
such as a thread title, parent text, post text, product page, creator post, or
source scope. The agent may bind an exact product only from the evidence text
together with that context. Context establishes what the item is about; it
does not donate unstated claims to the item's author. If the binding remains
unclear, the item stays `unresolved` or `out_of_scope`.

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
only one active result to reconciliation. Its whole-row read must keep direct
customer use, ownership, preference, and context-adopting answers first-hand;
must not assign an axis merely because a shade, product, or adjacent clause
names it; and must not invent a two-sided comparison from one side's stated
amount. It resolves leading yes/no replies against their parent question,
accounts for every materially distinct clause, and keeps unqualified preference
or better/worse language about a product overall axis-free even when it sits
beside an attribute claim. A stated liking or favorite evaluation of a named
shade may use `shade_and_color_fit`; ownership, purchase, or repurchase alone
may not.
Non-claim rows pass through unchanged.
Method v5 and v6 remain historical one-pass routes and acquire no retroactive
verification obligation.

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
material sides stay separate, opposite directions are not bundled, and generic
approval may still be discarded when it carries no bounded evidence.
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

Projection v2 binds semantic execution identity: source, corpus, and catalog
bindings; selected method v5-or-v6 identity and hash; response-schema version; prompt-encoding
version; exact work-unit membership; evidence and context references; prompt and
leaf caps; and complete assessable-denominator coverage. It must not encode a
worker count or static worker partition, because who executes a work unit is a
controller runtime decision, not part of semantic identity. The new generation
keeps the existing pretty, indented JSON prompt encoding, bound by name so a
later compact encoding cannot silently reuse a projection packed under this one.

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
set. A review-ID substring elsewhere in a file is never membership proof. Its captured-conversation
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
   The retailer builder also verifies the completion receipt, retains every
   captured source file, and de-duplicates a repeated native review identity to
   one customer evidence item while preserving every source-pinned product
   listing context carried by its occurrences. A repeated listing occurrence
   does not become another customer experience. No admitted retailer source
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
7. `prepare-batches` verifies sources, builds bundle v4, proves the work-unit
   bijection, writes byte-bounded prompts, and writes one deterministic
   three-worker assignment manifest.
8. `validate-batch-response` validates one returned batch immediately without
   compiling a partial corpus. `status` reports valid, missing, duplicate, and
   invalid responses so an interrupted run can resume honestly.
9. `submit-batches` validates all agent responses and exact alias coverage.
10. For method v7, `prepare-row-verification` renders byte-bounded independent
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
15. `prepare-calibration` reads a hash-pinned method-v5-or-v6 source and blind
    owner gold, projects exact bounded slices, and writes route-native sources,
    bundles, fingerprints, and prompts. The calibration spec deliberately
    selects the method being tested and may retarget the same pinned evidence
    from the source's method marker; the route fingerprint binds the selected
    method and exact method hash, so this is explicit method comparison rather
    than fallback. It makes no model call and cannot authorize a corpus run.
16. `evaluate-calibration` runs the existing response validator, then evaluates
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

- `v23` / 2026-08-10 — added run v5 / method v7 whole-row evidence
  verification between primary extraction and reconciliation. Every primary
  claim-bearing row now receives exactly one independent `accept`, complete-row
  `replace`, or `unresolved` decision; replacement rows reuse the ordinary
  semantic validator, original and verification lineage remain separately
  hash-bound, and reconciliation sees only the sole active result. Method v6
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
