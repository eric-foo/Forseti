---
artifact_role: authority
status: current
owner: Judgment / claim support
version: v2
effective_date: 2026-08-08
depends_on:
  - forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md
---

# Semantic Evidence Integration Contract v2

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
and flattened leaf provenance. Every stage and node compilation retains the
root batch-compilation hash; finalization rejects a terminal hierarchy whose
root hash differs from the supplied batch compilation even when the visible
leaf denominator happens to match. The agent still owns whether meanings are
equivalent and how conditions, negation, and uncertainty should be described.
Structural completeness is therefore proven; perfect open-world semantic
recall is not.

Emerging labels are consolidated semantically before seal. The agent groups
meaning-equivalent labels; the compiler preserves every original label and
never invents a merge. Each consolidated candidate terminates as `accepted`,
`nonmaterial`, or `blocker`. Every parent node preserves the exact union of its
children's emerging labels. Once validated, a consolidation is carried
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
3. `build-serp-source-surface-spec` hash-pins the bounded job-to-packet map;
   `prepare-serp-source-frontier` enumerates every source-bearing row; and
   `materialize-serp-source-frontier-review` applies an agent-authored semantic
   review, mechanically deduplicates repeated locators, and emits the recovery
   targets that target reconciliation must settle.
4. `census-phase-a-corpus` independently proves the captured Reddit and
   retailer customer-corpus denominators where those Phase A source shapes are
   present.
5. `materialize-phase-a-v3` merges audited, source-family-produced v3
   fragments into one final-acquisition source and writes a separate lineage
   receipt. It never guesses a new source-family adapter.
6. `materialize-v3` verifies source artifacts and normalizes declared
   containers/leaves into one hash-bound v3 source; unsupported families or
   denominator mismatches fail closed.
7. `prepare-batches` verifies sources, builds the bundle, and renders prompts.
8. `validate-batch-response` validates one returned batch immediately without
   compiling a partial corpus. `status` reports valid, missing, duplicate, and
   invalid responses so an interrupted run can resume honestly.
9. `submit-batches` validates all agent responses and exact alias coverage.
10. `prepare-reconciliation-level` renders one or more byte-bounded prompts
   from batch units or prior semantic nodes.
11. `validate-reconciliation-response` validates one returned hierarchy batch
   before the level is complete.
12. `submit-reconciliation-level` validates exact child accounting and writes
    the next node compilation; repeat until one terminal level remains.
13. `finalize-v3` flattens terminal nodes back to exact leaves and writes view
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
  flatten to exact leaf evidence and retain the exact root batch-compilation
  lineage;
- truthful evidence-stack counts that keep evidence items, containers,
  independent origins, roles, engagement, support, opposition, and mixed
  containers separate; and
- every emerging-axis candidate consolidated with immutable original-label
  lineage and terminal disposition, including lower-level blockers.

A passing route-1.7.0 seal additionally requires one embedded
`phase_a_serp_source_frontier_v1` in the evidence-depth ledger. Its Phase 1 and
Phase 2 job sets must exactly match the sealed jobs, every focused-search SERP
packet must be admitted, and every source-bearing result row from those bounded
surfaces must receive exactly one agent-semantic disposition: `routed`,
`duplicate`, or `excluded`. A routed row points to an existing native-capture
or locator-recovery target; a duplicate points directly to a routed owner; an
excluded row carries a reason. People-also-ask and related-search prompts are
Google navigation aids, not external sources. This closes the SERP-to-native
linking gap without crawling result pagination or treating SERP text as native
evidence.

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
