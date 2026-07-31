# Forseti Company-Intelligence Information Architecture v0

```yaml
retrieval_header_version: 1
artifact_role: Decision record (company-intelligence information architecture)
scope: >
  Owner-adjudicated architecture for deciding which company information Forseti
  should seek, how evidence access and directness affect that choice, how
  decision-neutral company facts relate to decision-specific modules, and what
  may later enter Company Surface.
use_when:
  - Designing a one-company research or competitive-intelligence commission.
  - Deciding whether a public, paid, or customer-authorized fact is worth acquiring.
  - Separating reusable company facts from decision-specific analysis, GTM, and monitoring.
authority_boundary: retrieval_only
open_next:
  - docs/decisions/forseti_product_thesis_decision_adjudication_v0.md
  - forseti/product/satellites/beauty/beauty_decision_adjudication_product_profile_v0.md
  - forseti/product/information/company_surface/README.md
  - forseti/product/spines/commission_signal_board/README.md
stale_if:
  - The owner changes decision adjudication as the product center.
  - Company Surface takes ownership of decision-specific analysis or recommendations.
  - Forseti adopts a materially different evidence-access or rights posture.
```

## Status And Decision

`OWNER_ACCEPTED_INFORMATION_ARCHITECTURE_V0`

The owner accepted the architecture in conversation on 2026-07-16 with these
corrections:

- start from the decision and determine the information needed to make it;
- do not start from a generic report, a proprietary-data category, or a
  monitoring product;
- treat lawfully available open or paid web information as potentially
  acquirable, with purchase effort governed by how badly the decision needs the
  fact;
- make acquisition **decision-usefully complete**, not compact or constrained
  by a universal minimum report;
- apply **smallest complete** discipline to the later decision artifact, after
  the evidence world is honestly acquired and sealed;
- include a CSB or Scanning item only for a named decision-material job when no
  equal-or-better included item substitutes for it;
- continue acquisition only while the best remaining move has a credible chance
  of changing the action, action ceiling, rival assessment, or hold condition
  enough to justify its marginal cost, latency, access risk, and duplication;
- close acquisition only when every material requirement is answered,
  contradicted, held as a typed gap, or has no remaining non-dominated path
  whose expected decision value materially exceeds its marginal cost, latency,
  access risk, and duplication;
- inspect the Data Lake before external Scanning or Capture in recurring or
  actively radarred source families, using Silver/current view first, then
  packet/catalog inventory, then raw material when necessary;
- keep compound concepts split into the precise underlying facts that can
  actually be observed or inferred; and
- keep the architecture compatible with later Company Surface import without
  making Company Surface a dependency of the first proving work.

This record controls the information-requirements architecture. It does not
select the first buyer, company, beauty decision, commercial offer, or proving
case.

## Plain-Language Model

Forseti should not ask, "What information can we collect about this company?"
It should ask:

> What decision must be made, which facts could change that decision, and what
> is the strongest evidence we can lawfully obtain for each fact?

That produces this flow:

```text
named decision, owner, action, consequence, and deadline
-> claims and unknowns that could change the action
-> atomic facts needed to resolve them
-> strongest lawful evidence route for each fact
-> observed facts, explicit proxies, conflicts, and missingness
-> decision-specific analysis module
-> act, probe, sequence, hold, or avoid
```

A company report may be a useful factual view, but it is not the product center
and does not determine what matters. The decision determines what matters.

## The Core Distinctions

### 1. Information is not a source

`Customer repeat purchase`, `retailer sell-through`, `product complaints`, and
`claim substantiation` are information. Reddit, Sephora, an earnings
transcript, a paid database, and an internal sales table are sources that may
contain evidence about that information.

A source family must never be treated as though it were the fact itself.

### 2. Access is not evidence strength

A paid source may contain direct, decisive evidence or weak, duplicated
commentary. An open source may contain a direct company admission or only a
noisy proxy. Payment status therefore does not determine importance or truth.

Every required fact is assessed on four separate axes:

| Axis | Question | Working values |
| --- | --- | --- |
| Decision criticality | Could this fact change the action, action size, timing, or hold state? | controlling, material, supporting, descriptive |
| Evidence directness | How directly does the evidence establish the fact? | direct measurement, direct observation, proxy, inference |
| Access class | How can Forseti lawfully obtain it? | open web, paid/entitled web, customer-authorized internal, unavailable/prohibited |
| Rights state | What may Forseti do with what it obtains? | inspect, derive, preserve, quote, share, redistribute — each source-specific |

These axes must remain independent. In particular:

- `paid` does not mean `strong`;
- `publicly reachable` does not mean `complete`;
- `available on the web` does not automatically grant preservation,
  quotation, sharing, or redistribution rights; and
- `unavailable` does not authorize replacing a decisive fact with a proxy.

### 3. Three meanings of non-open information

The word `private` is too imprecise for this architecture. Use:

1. **Paid or entitled web evidence** — available through a lawful subscription,
   membership, purchase, or licensed interface. This is eligible evidence.
2. **Customer-authorized internal evidence** — supplied or connected by the
   company under an explicit permission boundary.
3. **Unavailable or prohibited evidence** — not lawfully obtainable for the
   commission. If it controls the action, Forseti holds.

### 4. Consequence is not predictive proof

Evidence that an outcome was economically serious proves stakes. It does not
prove that an earlier public clue reliably predicted the outcome or would have
changed the decision.

This distinction prevents hindsight from being presented as intelligence.

## Decision-Useful Complete Evidence World

There is no universal minimum company report and no fixed ranking of company
data that applies to every decision.

For a named decision, the **decision-usefully complete evidence world** contains
every fact and evidence family with a material positive expected contribution
to understanding the decision, including what is necessary to:

- support the strongest defensible action;
- expose a counter-case that could reverse or materially resize that action;
- identify a decisive missing input;
- distinguish direct evidence from proxy and inference; and
- leave a truthful hold when the decision cannot be defended.

Acquisition continues until those material information jobs are supported,
contradicted, meaningfully bounded, or honestly blocked/gapped. It excludes
material that merely makes the report feel comprehensive, but compactness,
source count, actor count, and token minimization are not acquisition success
criteria.

`Complete` prevents an under-researched answer. `Decision-useful` excludes
irrelevant breadth without turning low cost or short output into a competing
objective. The later decision artifact applies Smallest Complete Intervention:
it communicates the narrowest package that fully preserves the decisive
evidence, counter-case, uncertainty, provenance, reversal conditions, and next
action.

No numeric source, row, observation, venue, or capture target establishes this
completeness. Collection targets are search hygiene only. Each included item
must perform a named decision-material job and must not be substitutable by an
equal-or-better included item.

Scanning owns acquisition closure. It continues only while the best remaining
move has a credible chance of changing the action, action ceiling, rival
assessment, or hold condition enough to justify its marginal cost, latency,
access risk, and duplication. It closes only when every material requirement
is answered, contradicted, held as a typed gap, or has no remaining
non-dominated acquisition path whose expected decision value materially
exceeds its marginal cost, latency, access risk, and duplication. A typed gap
closes a requirement only when no remaining non-dominated path whose expected
decision value materially exceeds its marginal cost, latency, access risk, and
duplication could still answer it within the commission's lawful, access, and
safety bounds. A run stopped by a run budget, cap, or policy boundary while such
a path remains is an incomplete run with typed gaps or a hold, not acquisition
closure.

## Architecture Layers

### Layer 1 — Decision frame

Bind:

- accountable decision owner or faithful proxy;
- action and available alternatives;
- consequence of error or delay;
- deadline and evidence cutoff;
- allowed recommendation verbs;
- known constraints;
- decisive-private-context boundary; and
- later reveal or outcome path.

No research commission should invent this frame from source availability.

### Layer 2 — Information-requirements register

Translate the decision into atomic facts. Each required fact records:

| Field | Purpose |
| --- | --- |
| `fact_id` | Stable identifier inside the commission |
| `underlying_fact` | The exact thing that must be known |
| `information_job` | The named decision-material job this fact or route performs |
| `decision_use` | Which action, threshold, or uncertainty it may change |
| `decision_effect` | Action, action ceiling, rival assessment, or hold condition it could change |
| `criticality` | Controlling, material, supporting, or descriptive |
| `preferred_measurement` | What direct evidence would look like |
| `acceptable_proxy` | Explicit fallback, if one can validly inform the decision |
| `proxy_ceiling` | What the proxy cannot establish |
| `comparison_or_baseline` | Required denominator, cohort, competitor, or prior state |
| `time_requirement` | Effective period, cutoff, and freshness need |
| `counterevidence_needed` | What would challenge the leading interpretation |
| `access_options` | Open, paid/entitled, authorized internal, or unavailable |
| `rights_requirement` | Inspect, preserve, quote, share, or redistribute need |
| `missing_behavior` | Proceed, narrow, probe, or hold when absent |
| `substitution_test` | Equal-or-better included fact or route that would make this item dominated |
| `refresh_eligibility` | Whether later change in this fact can affect a recurring decision |

Compound labels such as `demand durability`, `channel health`, or `execution
capacity` are module names, not acceptable facts. They must be decomposed.

For example, `demand durability` might require separate facts about:

- repeat purchase by a defined cohort;
- reorder interval;
- new-versus-returning customer mix;
- dependence on one launch, creator, discount, retailer, or geography;
- return or complaint reasons;
- search, review, community, or resale persistence; and
- the period and denominator behind every measure.

### Layer 3 — Evidence acquisition

Choose sources after the facts are named.

For a recurring or actively radarred source family, inspect the existing Data
Lake before external Scanning or Capture through the highest-trustworthy
current read surface available:

1. relevant Silver/current view;
2. packet or catalog inventory;
3. raw material when necessary.

This is a reuse, freshness, and coverage preflight, not proof of current
external reality. Route external acquisition only to net-new, stale,
incomplete, conflicting, or source-fidelity gaps. Absence from Silver is not
absence from the lake or the external world, and lack of a relevant read model
must not block acquisition.

Open and paid web sources are both eligible. The decision to buy access should
be based on:

1. how critical the fact is;
2. how much stronger or more direct the paid evidence is than available
   alternatives;
3. whether it can change the action or prevent a false hold;
4. cost and acquisition latency relative to the decision deadline; and
5. whether the source's terms permit the required inspection, derivation,
   preservation, quotation, and delivery.

The practical rule is:

> Pay for access when the expected decision value of the stronger fact exceeds
> the cost, delay, and rights limitation of obtaining it.

Membership willingness removes a commercial preference against paywalls. It
does not remove source-specific legal, contractual, technical, or evidentiary
limits.

CSB may specify the information requirements and source-family coverage.
CSB defines material information jobs and candidate routes; it does not freeze a
participant packet. Scanning discovers valuable venues, exact queries, hidden
sources, negatives, and access walls, records dominance, and owns marginal
acquisition choice and closure. Capture fulfills bounded requests or reports
typed failure/route exhaustion; it does not decide evidence-world completeness
or final packet inclusion. Capture reuses appropriate existing lake packets
before recapture unless reacquisition materially improves currentness, fidelity,
provenance, cutoff compliance, inspectability, or fills a named gap.
Downstream evidence owners preserve provenance, transformations, conflicts,
and limitations.

### Layer 4 — Observation and derivation

Every material result must separate:

- the raw or preserved evidence;
- the directly observed fact;
- any derived measure and its method;
- any proxy relationship;
- analyst inference;
- counterevidence;
- observed, published, and effective dates;
- coverage and access limitations; and
- the strongest claim the evidence may support.

A proxy must never be stored or presented as the underlying fact. For example,
review volume is not sell-through; community excitement is not repeat purchase;
job postings are not execution capacity; and an impairment is not proof that a
particular public early-warning signal worked.

### Layer 5 — Decision modules

Decision modules are reusable analytical assemblies. They are activated only
when the decision requires them, and each module must resolve into atomic facts.

Candidate modules include:

| Module | Example decisions it may inform | Illustrative atomic facts |
| --- | --- | --- |
| Customer choice and product failure | concept, positioning, claims, reformulation | stated alternatives, switching reason, use context, failure mode, complaint incidence, repeat behavior |
| Demand durability | launch, inventory, investment, competitive response | cohort repeat, reorder interval, concentration, promotion dependence, persistence |
| Retail and channel productivity | retailer entry, expansion, exit, allocation | productive doors/SKUs, sell-through, replenishment, returns, markdowns, margin and terms |
| Claims and substantiation | claim launch, packaging, regulatory response | exact claim version, evidence standard, test basis, complaint or challenge, jurisdiction |
| Launch and inventory | launch intervention, buy depth, replenishment | forecast, orders, stock, stockout duration, replenishment, cancellations, returns |
| Competitive response | price, positioning, launch timing, assortment | competitor action, affected segment, substitution, price umbrella, channel overlap |
| Execution and supply resilience | scale, delay, supplier change, contingency | capacity, lead time, defect rate, concentration, role ownership, contingency |
| Deal, financial, and concentration | acquisition, partnership, capital allocation | revenue/margin bridge, customer/channel concentration, cash need, liabilities, impairment |
| Regulatory and safety response | hold, recall, reformulate, communicate | adverse event, affected lot/version, severity, reporting duty, corrective action |

This is a candidate vocabulary, not a required checklist and not a ranking.

### Layer 6 — Decision artifact

The output follows the current Forseti product contract:

- decision and evidence-world frame;
- recommendation or explicit hold;
- strongest evidence and counter-case;
- uncertainty and action ceiling;
- decisive missing inputs;
- reversal conditions;
- inspectable evidence appendix; and
- later reveal or outcome plan.

A generic company dossier that stops at description is incomplete for a
Decision Sprint, even if its facts remain useful as substrate.

## Common Company Substrate

A decision-neutral one-company report can reduce repeated reconstruction. Its
common substrate should be limited to reusable observed company reality:

- Brand/Org identity and ownership state;
- owned category, collection/franchise, parent-product, material-variant,
  bundle/set, formula, package, and claim architecture;
- price, promotion, availability, and assortment states;
- channel and distribution footprint;
- launches, discontinuations, partnerships, and official commitments;
- leadership, hiring, role ownership, and organizational changes;
- material regulatory, litigation, safety, and corporate events; and
- provenance, timing, conflicts, missingness, and coverage limitations.

This substrate is not a complete account of the company. It is the reusable
factual layer from which decision-specific requirements may start.

The current CSB one-company competitive-intelligence profile may produce this
decision-neutral substrate. It must not be mistaken for the later
decision-specific adjudication run.

### Small high-yield Understanding core

Before optional deepening, resolve five jobs through the existing ledgers:
current offering and portfolio architecture; exact current commercial and retail
expression where material; channel, distribution, and geography posture;
strategic and operating chronology; and applicable material events. This is an
acquisition floor and ordering rule, not a new section, schema, source quota, or
substitute for customer/community evidence or another material required lens. A
material unresolved core job blocks the acquisition seal. Unavailable or
immaterial remainders stay typed gaps and non-claims. Commission archives,
supply investigation, ads or creators, competitors, search trends, and similar
deepening only for a named unresolved inference job.

### Portfolio and retail architecture

Completed company Understanding makes the owned portfolio denominator, its
retailer expression, complete bounded review-corpus board, evidence-selected
interpretive depth set, and resulting outside-in interpretation visible as one
first-class report section. Retailer grids, exact parent PDPs, dated public
moves, and reproducibly bounded review corpora may support that interpretation
without pretending to expose internal revenue, margin, or management reporting.
The corpus board accounts for every selected-retailer listing and distinct
review corpus before category-balanced interpretation is selected; it is not a
full historical crawl or a requirement to interpret every row. This section
consumes the company substrate already captured for Understanding; it does not
create a parallel acquisition checklist or data store.

When retail expression is material, acquire this substrate breadth-first. Begin
with enough owned evidence to bind the subject, categories, franchises, known
parents, and canonical product identity. Use company-owned evidence to establish
the officially named US retailer board before probing retailer surfaces. When
at least four company-authorized, target-market, route-admissible third-party
retailers exist, select and attempt at least four, favoring venues that add
distinct assortment, commercial, or customer evidence. The company-owned DTC
site does not count toward the four. When fewer than four qualify, select all
that qualify and record `AUTHORIZED_RETAILER_SHORTFALL` with the observed count
and reasons; never fill the floor with an unauthorized, duplicate, or
market-unpinned venue. Resolve Sephora explicitly: when it is officially named
and its US grid is route-complete, it must be included, counts as one selected
retailer, and is the retail primary. If it is officially named but blocked,
unpinned, or incomplete, preserve that typed outcome and use the strongest
complete selected retailer as the working primary rather than fabricating
Sephora coverage. When another qualified retailer is available, replace a
blocked selected route to restore four usable venues while preserving the
blocked outcome. For every selected retailer, capture its available grid
surface, deterministically union and reconcile exact listings with the owned
candidates, then return to owned surfaces to close the complete publicly exposed
denominator and typed gaps. Owned evidence remains canonical identity authority;
retailer grids are discovery and channel-expression evidence.

Attempt one common-floor baseline PDP for every reconciled exact retailer
listing and preserve each admitted baseline or typed miss. A miss is
acquisition-blocking only when it is strategic or decision-bearing for the
bound question, carries a distinct material seam or required corpus identity,
or reveals a route-wide failure. A non-strategic middle-of-curve miss may remain
an accepted residual when the retained baselines still support the intended
answer; no coverage percentage alone decides materiality. Then bind every
admitted listing to provider tenant/store plus product/grouping
collection context and acquire one bounded onboarding window for every distinct
accessible review corpus, or preserve its typed no-review, not-exposed,
blocked, or unresolved outcome. Only after that complete bounded corpus board
may expensive interpretation or Q&A depth be selected for a named,
non-duplicative and category-balanced job. This is not an all-retailer or
source-count quota and does not require a full historical review crawl or
complete global SKU graph.

Sephora, Ulta, and Target expose brand or assortment grids. Amazon requires an
authorization result separate from marketplace presence:
`COMPANY_AUTHORIZED` means a company-owned source explicitly names or links the
target-market Amazon store or retailer; `MARKETPLACE_IDENTITY_VERIFIED_NOT_COMPANY_AUTHORIZED`
means the exact branded storefront or seller/listing identity is verified but
company-owned evidence does not authorize it; and
`MARKETPLACE_PRESENCE_UNVERIFIED` means exact seller/storefront identity is not
proven. Only `COMPANY_AUTHORIZED` counts toward the four-retailer floor. A
verified-but-not-company-authorized Amazon route may supplement marketplace,
price, or customer evidence with that limitation attached; an unverified route
remains a discovery pointer. Amazon exposes a query-bound ranked-search window
that may be complete for its declared query and reachable result window, never a
guaranteed complete or authorized-only brand catalog. Projection capability does
not prove route admission; every run records market pin, reachability, surface
boundary, and typed failure. Point-in-time retailer metrics are traction
proxies, not sales, share, or trend.

Officially named, route-complete Sephora must be the retail primary. Otherwise,
preserve the typed Sephora blocked, unpinned, or incomplete outcome and use
another complete selected retailer as the working primary.
Keep retailer counts as separate, traceable series unless exact corpus identity
and deterministic deduplication justify comparison. Counts show accumulated
retailer-local attention, never sales.

| Observed public pattern | Strongest ordinary interpretation | Required boundary |
| --- | --- | --- |
| Large accumulated review base, continuing review velocity, and broad authorized distribution | Established leading product | Large totals alone establish accumulated attention, not current sales |
| Rising age-adjusted review velocity plus new variants or retailer expansion | Product receiving growth investment | Do not call it a revenue growth engine without economics |
| Lower price, mini or trial format, wide availability, and frequent inclusion in starter bundles | Entry or trial product | Format and merchandising show intended access, not conversion |
| Founding status, central brand language, prominent placement, and sustained support | Flagship or credibility anchor | Strategic prominence can differ from current volume |
| Recent launch, narrow distribution, and limited variants | Experiment or early adjacency | Low totals are expected for a young product and do not prove weakness |
| Weak age-adjusted velocity plus repeated discounting or shrinking availability | Plausible weak link | Require a stable observation window; one low total or one stockout is insufficient |
| Frequent bundling with a higher-traction product | Attachment or cross-sell product | Bundling shows merchandising intent, not attach rate |
| New shades, sizes, bundles, or channel placements despite ordinary totals | Actively supported franchise | Visible investment does not prove successful investment |
| Large historical base, slowing velocity, stable price, and stable distribution | Mature franchise | Do not call it declining, harvested, or a cash generator without stronger trend or economic evidence |

Apply the table with four rules:

1. Reconcile exact parent identities and normalize product age before comparing
   review totals or velocity. Keep every retailer as a separate series.
2. Preserve all captured review rows. Deduplicate analysis deterministically
   first using provider/origin review IDs and, when absent, a normalized
   rating-date-author-title-body fingerprint. An LLM may flag ambiguous
   near-matches for adjudication; it must not delete, merge, or become canonical
   review identity.
   The implemented post-Capture selective-depth and linkage producer is
   `cleaning.retail_review_overlap`. It emits
   `retail_review_depth_selection_v0` and
   `retail_review_overlap_linkage_v1`, re-verifies raw packet references,
   preserves native review occurrences and retailer totals, and leaves ambiguous
   conflicts unmerged. It is not raw Capture or portfolio-role/sales Judgment.
3. A point-in-time directional role such as visible growth investment or a
   plausible weak link requires age-aware review accumulation or review recency
   inside a reproducibly bounded corpus plus at least one independent public
   behavior such as dated launch activity, assortment, variants, placement,
   pricing, promotion, availability, or channel breadth. Acceleration, slowing,
   or decline still requires a declared longitudinal observation window.
4. Use the named target market as the default evidence frame. For a US decision,
   do not build an international map unless geography, expansion, price,
   channel dependence, supply exposure, or the later decision gives it a named
   information job.

## Company Surface Boundary

Company Surface is not required for the first proving run. This architecture is
storage-neutral and authorizes no Company Surface implementation or mutation.

When a later import is authorized, suitable Company Surface candidates include:

- canonical company, Brand, product, SKU, claim, channel, and event identities;
- dated factual observations and measured values;
- source and provenance links;
- explicit limitations, missingness, conflicts, corrections, and identity
  uncertainty;
- history and effective-time relationships; and
- an explicit relation stating that one observation is a proxy for another
  fact, without promoting the proxy into that fact.

These remain outside Company Surface:

- the current buyer or Decision Frame;
- research-run priority and access-purchase choice;
- pain, urgency, ICP, wedge, outreach, or GTM hypotheses;
- analyst interpretations and confidence;
- recommendation, action ceiling, and reversal conditions; and
- proof or willingness-to-pay conclusions.

Physical records continue to belong to Data Lake-owned storage. Company Surface
owns shared company meaning and history, not the raw packets or downstream
decision.

## Monitoring Eligibility

Forseti should not monitor a source merely because it is capturable or might be
interesting.

A variable becomes eligible for longitudinal refresh only when all of these are
named:

1. the atomic fact;
2. the decision it can change;
3. the baseline or prior state;
4. the material-change threshold or qualitative trigger;
5. the required cadence relative to the decision window;
6. the acquisition and rights route; and
7. what action follows from a meaningful change.

Longitudinal evidence may be needed in a point-in-time Decision Sprint.
Production monitoring is a later delivery mechanism, not the reason a fact is
important.

## Evidence Examples

### e.l.f. Bronzing Drops — direct evidence of input use

The e.l.f. example is useful because company leadership reportedly identified
Bronzing Drops as its most requested community product and the launch explicitly
positioned a $12 item against a $38 prestige inspiration.

That supports a bounded claim:

> Customer requests and an observed prestige price umbrella entered an actual
> product and positioning decision.

It does not by itself prove the product succeeded because of those inputs, that
the request represented the whole market, or that the same method transfers to
another company.

Sources to re-verify before strict use:

- [e.l.f. earnings transcript mirror](https://fintool.com/app/research/companies/ELF/documents/transcripts/q1-2025)
- [e.l.f. product announcement](https://investor.elfbeauty.com/stock-and-financial/press-releases/landing-news/2024/06-10-2024-050119999)

### Drunk Elephant impairment — direct evidence of consequence, not prediction

Shiseido's reported ¥46.8 billion impairment establishes that Drunk Elephant's
deterioration had serious economic consequences.

It does not establish that an earlier public `cohort drift` proxy:

- was observable before the deterioration became obvious;
- measured actual customer retention or repeat purchase;
- would have crossed a predeclared action threshold;
- would have caused a decision owner to act; or
- would have prevented or reduced the impairment.

To test that stronger proposition, Forseti would need a sealed backtest:
predeclare the decision and cutoff, use only evidence available by the cutoff,
state the action before reveal, and compare it with the later outcome.

Source to re-verify before strict use:

- [Shiseido 2025 results](https://corp.shiseido.com/en/ir/pdf/ir20260210_244.pdf)

In short: e.l.f. says, "we used this input to make a product decision."
Shiseido says, "the eventual outcome was costly." The latter does not prove
which earlier signal would have warned correctly.

## First Proving-Run Requirement

The next lane should not commission another broad company report immediately.
It should first choose one beauty decision family and bind:

- the company and faithful decision-owner proxy;
- action, alternatives, consequence, deadline, and cutoff;
- atomic facts most likely to control or materially change the action;
- which facts are expected on open web, paid web, authorized internal data, or
  unavailable;
- which proxies are admissible and their ceilings;
- the decision-usefully complete evidence world;
- the sealed backtest or later reveal path; and
- the hold condition.

Only then should it commission the Research Engine.

## Success Signals

This architecture is functioning when:

1. A cold agent can derive a decision-usefully complete evidence plan from a
   named decision without using a generic company-report checklist or treating
   compactness as an acquisition target.
2. The agent can explain exactly why each requested fact may change the action.
3. Paid access is purchased because a critical fact justifies it, not because
   paid data is presumed superior.
4. Sources, facts, proxies, and inferences remain visibly separate.
5. Missing decisive evidence produces a hold rather than a generic hypothesis.
6. Reusable factual outputs can later be imported into Company Surface without
   importing GTM or decision judgment.
7. Longitudinal refresh is attached only to variables with a named decision
   trigger and action.
8. Acquisition closes by material requirements and non-dominated expected
   decision value, never by a source, row, observation, venue, or capture count.
9. Recurring/radarred families reuse the lake first without confusing lake state
   with current external truth.

## Explicit Non-Claims

This record is:

- not selection of a buyer, company, first decision family, offer, price, or GTM
  route;
- not a universal company-data ranking or mandatory report schema;
- not proof that any named source is currently accessible, complete, licensed,
  or decision-sufficient;
- not proof that the e.l.f. inputs caused success or that public cohort proxies
  predicted the Drunk Elephant impairment;
- not Company Surface, Data Lake, CSB, Scanning, Capture, Cleaning, or Judgment
  implementation authority;
- not authorization to buy access, acquire private data, contact companies, or
  redistribute source content;
- not production monitoring readiness; and
- not buyer proof, willingness-to-pay proof, or same-decision validation.

## Direction Change Propagation

```yaml
direction_change_propagation:
  doctrine_changed: >
    Company-intelligence acquisition now uses job-based inclusion,
    non-dominated expected-decision-value continuation and closure, and a
    lake-first reuse/freshness/coverage preflight for recurring or actively
    radarred source families; CSB defines jobs/routes without freezing a packet,
    Scanning owns marginal acquisition and closure, and Capture fulfills bounded
    requests or returns typed exhaustion while reusing suitable lake packets
    before justified recapture.
  trigger: architecture_doctrine
  related_triggers:
    - product_doctrine
    - workflow_authority
    - lifecycle_boundary
  controlling_sources_updated:
    - docs/decisions/forseti_company_intelligence_information_architecture_v0.md
    - forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md
    - forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md
    - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
    - forseti/product/spines/commission_signal_board/README.md
    - forseti/product/spines/scanning/README.md
    - forseti/product/spines/scanning/scan_core/forseti_scanning_intelligent_walk_mgt_operating_model_v0.md
    - forseti/product/spines/capture/README.md
    - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  downstream_surfaces_checked:
    - AGENTS.md
    - .agents/workflow-overlay/README.md
    - .agents/workflow-overlay/source-of-truth.md
    - .agents/workflow-overlay/decision-routing.md
    - .agents/workflow-overlay/retrieval-metadata.md
    - .agents/workflow-overlay/validation-gates.md
    - .agents/workflow-overlay/safety-rules.md
    - .agents/workflow-overlay/source-loading.md
    - docs/workflows/forseti_repo_map_v0.md
    - .agents/hooks/check_commission_signal_board_output.py
    - .agents/hooks/check_csb_scanning_artifact.py
    - forseti-harness/tests/unit/test_commission_signal_board_output_validator.py
    - forseti-harness/tests/unit/test_csb_scanning_artifact_validator.py
  intentionally_not_updated:
    - path: AGENTS.md
      reason: >
        The change is bounded to company-intelligence acquisition doctrine; no
        repeated cross-domain defect justifies changing the global Smallest
        Complete Intervention kernel.
    - path: CSB and Scanning validator code
      reason: >
        Existing checkers remain structural/overclaim guards. This work adds
        judgment-based inclusion, dominance, lake-reuse, and closure rules that
        are not mechanically truth-verifiable, so no semantic ceremony was added.
    - path: Packing Spine
      reason: >
        Packet assembly and final inclusion design are outside this work unit.
    - path: e.l.f. backtest artifacts
      reason: >
        The architecture example remains historical context; the backtest was
        not continued or modified.
    - path: Reddit Silver lane claims
      reason: >
        No mature Reddit Silver lane is asserted without primary-source
        verification.
    - path: .agents/workflow-overlay/source-loading.md
      reason: >
        Its current routes already open the company-intelligence decision,
        Scanning front door, Capture method, source-family catalog, and Silver
        authority. The phrase "complete venue coverage" is confined to a
        historical bounded Reddit pressure-test state and points to its owning
        control note; it is not general evidence-world or acquisition-closure
        doctrine.
    - path: docs/workflows/forseti_repo_map_v0.md
      reason: >
        Its T1 routes already distinguish company intelligence, Scanning,
        Capture/source families, and Silver authority. No owner or path moved.
  stale_language_search: >
    rg -n -i "source count|source-count|observation count|venue count|capture
    target|minimum sources|at least [0-9]+|quota|coverage target|mandatory
    Reddit|requires a bounded Reddit|completion.*(source|row|observation|venue|
    capture)|authorized target is met"
    forseti/product/spines/commission_signal_board
    forseti/product/spines/scanning
    forseti/product/spines/capture/README.md
    forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
    docs/decisions/forseti_company_intelligence_information_architecture_v0.md
  stale_language_search_result: >
    Executed 2026-07-17 across the nine affected authority files. Remaining
    quota/count hits are explicit prohibitions, structural promotion/schema
    language, the validator-compatible `mandatory_bounded_scout` row token, or
    this receipt's search literal. No live affected authority treats a numeric
    source, row, observation, venue, query, or capture-target count as inclusion
    or acquisition closure. Structural section counts, recency windows, run
    caps, temporal gates, source-independence checks, and schema fields remain
    because they govern output shape, safety, validity, or claim strength rather
    than collection completion.
  non_claims:
    - not validation or readiness
    - not proof of current external source reality
    - not Packing Spine design or implementation
    - not final packet inclusion or freeze
    - not source-access, capture, or implementation authorization
```

## Direction Change Propagation — Exact PDP Materiality

```yaml
direction_change_propagation:
  doctrine_changed: >
    Exact retailer-listing breadth remains an attempt-and-disposition
    obligation, but a typed PDP miss no longer blocks mechanically. Strategic,
    decision-bearing, distinct-seam, required-corpus, and route-systemic misses
    block; a freshly supported non-strategic middle-of-curve miss may be an
    accepted residual. Percent coverage alone is not the decision rule.
  trigger: architecture_doctrine
  related_triggers: [workflow_authority]
  controlling_sources_updated:
    - docs/decisions/forseti_company_intelligence_information_architecture_v0.md
    - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
  downstream_surfaces_checked:
    - forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md
    - forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md
    - forseti/product/spines/capture/core/source_families/retail_pdp/retailer_information_extraction_standard_v0.md
    - docs/workflows/summer_fridays_understanding_dogfood_20260725_p10/coordinated/acquisition_seal.md
  intentionally_not_updated:
    - path: commission signal board prompt structure and validator
      reason: >
        They require acquisition accountability and typed gaps but do not encode
        the former all-or-nothing exact-PDP denominator rule.
    - path: historical acquisition records and raw packets
      reason: >
        Historical observations remain immutable; a recovery adjudication may
        supersede only their gate effect.
  stale_language_search: >
    rg -n "one verified raw PDP baseline|full-raw common-floor|every reconciled
    exact retailer listing|complete selected-retailer exact PDP" forseti docs
    .agents
  non_claims:
    - not permission to skip an exact listing attempt
    - not a numerical coverage threshold
    - not validation or readiness
```

```yaml
direction_change_propagation:
  doctrine_changed: >
    Company-intelligence acquisition retains the owner-accepted asymmetric
    continuation and closure thresholds, and a typed gap cannot close a material
    requirement while an answerable non-dominated path still materially clears
    its marginal cost, latency, access risk, and duplication within lawful,
    access, and safety bounds.
  trigger: architecture_doctrine
  related_triggers:
    - workflow_authority
    - lifecycle_boundary
  controlling_sources_updated:
    - docs/decisions/forseti_company_intelligence_information_architecture_v0.md
    - forseti/product/spines/scanning/README.md
    - forseti/product/spines/scanning/scan_core/forseti_scanning_intelligent_walk_mgt_operating_model_v0.md
  downstream_surfaces_checked:
    - AGENTS.md
    - .agents/workflow-overlay/source-of-truth.md
    - .agents/workflow-overlay/source-loading.md
    - .agents/workflow-overlay/validation-gates.md
    - docs/workflows/forseti_repo_map_v0.md
    - forseti/product/spines/commission_signal_board/README.md
    - forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md
    - forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md
    - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
    - forseti/product/spines/capture/README.md
    - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
    - .agents/hooks/check_commission_signal_board_output.py
    - .agents/hooks/check_csb_scanning_artifact.py
  intentionally_not_updated:
    - path: AGENTS.md
      reason: >
        The correction is bounded to company-intelligence acquisition doctrine;
        it does not establish a repeated cross-domain defect in the global
        Smallest Complete Intervention kernel.
    - path: CSB and Capture authority files
      reason: >
        They already assign marginal acquisition and closure to Scanning without
        restating the typed-gap closure test, so no additional copy is needed.
    - path: CSB and Scanning validator code
      reason: >
        The corrected thresholds and typed-gap guard require decision judgment
        and are not mechanically truth-verifiable; existing structural and
        overclaim checks remain unchanged.
    - path: information-requirements register field consolidation
      reason: >
        Potential overlap among information_job, decision_use, and
        decision_effect does not alter the corrected acquisition rule and would
        require a separate schema decision.
    - path: actively radarred terminology
      reason: >
        The phrase is owner-supplied scope language for an actively maintained
        radar source family; this patch does not broaden or redefine that scope.
  stale_language_search: >
    rg -n -i "and an expected decision value|worth its marginal burden|credible
    chance|typed gap closes|held as a typed gap|expected decision value
    materially exceeds" across the nine PR-1026 authority files.
  stale_language_search_result: >
    Executed 2026-07-17. No live continuation rule uses the rejected conjunctive
    threshold or the looser "worth its marginal burden" closure wording. The
    architecture record and both Scanning closure authorities use the
    owner-accepted continuation and closure tests, and each Scanning-owned
    closure statement carries the typed-gap guard. CSB and Capture retain their
    existing authority boundaries without duplicating Scanning's closure rule.
  non_claims:
    - not validation or readiness
    - not proof that a particular acquisition should continue or close
    - not a schema consolidation
    - not validator enforcement of semantic judgment
```

## Direction Change Propagation — Portfolio And Retail Architecture

```yaml
direction_change_propagation:
  doctrine_changed: >
    Completed company Understanding now carries a first-class Portfolio And
    Retail Architecture section that makes the owned denominator, qualified
    retailer corpus, evidence-selected depth, and outside-in interpretation
    visible and mechanically present.
  trigger: output_authority
  related_triggers: [architecture_doctrine, validation_philosophy]
  controlling_sources_updated:
    - docs/decisions/forseti_company_intelligence_information_architecture_v0.md
    - forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md
    - forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md
    - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
  downstream_surfaces_checked:
    - .agents/hooks/check_commission_signal_board_output.py
    - forseti-harness/tests/unit/test_commission_signal_board_output_validator.py
    - forseti-harness/tests/fixtures/commission_signal_board_outputs/valid_company_competitive_intelligence_output.txt
    - forseti-harness/tests/fixtures/commission_signal_board_outputs/valid_company_commission_stage_output.txt
    - forseti-harness/tests/fixtures/commission_signal_board_outputs/bad_company_commission_scout_status_output.txt
    - docs/workflows/forseti_understanding_tiered_retail_capture_batch_plan_handoff_v0.md
  intentionally_not_updated:
    - path: Capture and durability-series contracts
      reason: >
        STEP-5 changes the Understanding output contract only; longitudinal
        monitoring remains explicitly deferred.
    - path: historical company reports and receipts
      reason: >
        Sealed historical runs remain immutable; the new contract governs future
        runs.
  stale_language_search: >
    rg -n "Positioning, Offerings, Markets, And Channels|eight company-report
    lenses|complete every-SKU architecture" across the changed live authority,
    validator, fixture, and handoff surfaces.
  non_claims:
    - not validation
    - not readiness
    - not Summer Fridays acquisition or Deliver
    - not longitudinal monitoring
```
