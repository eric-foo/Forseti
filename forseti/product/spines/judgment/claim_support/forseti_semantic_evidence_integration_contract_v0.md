---
artifact_role: authority
status: current
owner: Judgment / claim support
version: v1
effective_date: 2026-08-08
depends_on:
  - forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md
---

# Semantic Evidence Integration Contract v1

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
- actor/origin de-duplication and independent-origin counts;
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
with the root and captured immediate-parent chain needed to interpret it.
Missing or truncated context remains visible and may force `unresolved`.

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
and flattened leaf provenance. The agent still owns whether meanings are
equivalent and how conditions, negation, and uncertainty should be described.
Structural completeness is therefore proven; perfect open-world semantic
recall is not.

Emerging labels are consolidated semantically before seal. The agent groups
meaning-equivalent labels; the compiler preserves every original label and
never invents a merge. Each consolidated candidate terminates as `accepted`,
`nonmaterial`, or `blocker`.

## No-provider workflow

The runner makes no model API call. Historical v1/v2 routes retain their four
operations. Route 1.6 adds repeatable reconciliation-level operations:

1. `materialize-v3` verifies source artifacts and normalizes the declared
   containers/leaves into one hash-bound v3 source; unsupported families or
   denominator mismatches fail closed.
2. `prepare-batches` verifies sources, builds the bundle, and renders prompts.
3. `submit-batches` validates agent responses and exact alias coverage.
4. `prepare-reconciliation-level` renders one or more byte-bounded prompts
   from batch units or prior semantic nodes.
5. `submit-reconciliation-level` validates exact child accounting and writes
   the next node compilation; repeat until one terminal level remains.
6. `finalize-v3` flattens terminal nodes back to exact leaves and writes view
   v2.

The controller gives the rendered prompts to a capable agent in a fresh turn.
The returned JSON is untrusted until the corresponding submit/finalize command
accepts it.

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

- source v3, bundle v3, method v3, batch-response v2, reconciliation-response
  v2, and integration-view v2 lineage;
- the `phase_a_final_acquisition` corpus profile rather than a bounded
  regression slice;
- captured count equal to assessed plus mechanically excluded plus blocked,
  with every count exact and no blocked item;
- exact container accounting and disclosed capture envelopes;
- a prompt-bounded, acyclic reconciliation hierarchy whose terminal nodes
  flatten to exact leaf evidence;
- truthful evidence-stack counts that keep evidence items, containers,
  independent origins, roles, engagement, support, opposition, and mixed
  containers separate; and
- every emerging-axis candidate consolidated with original-label lineage and
  terminal disposition.

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

## Changelog

- `v1` / 2026-08-08 — added Route 1.6 full captured-corpus accounting,
  containers and capture envelopes, prompt-bounded hierarchical
  reconciliation, response/view version changes, emerging-axis consolidation,
  and separated evidence-stack counts. Preserved every historical Route 1.4
  and 1.5 contract.
- `v0` / 2026-08-07 — introduced Route 1.4 semantic integration and Route 1.5
  source-pinned product context.
