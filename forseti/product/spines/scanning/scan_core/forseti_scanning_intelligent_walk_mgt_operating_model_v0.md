# Forseti Scanning Intelligent Walk MGT Operating Model v0

```yaml
retrieval_header_version: 1
artifact_role: Product method operating model (owner-invoked Mini God Tier target lens; scanning-to-capture bridge)
scope: >
  Defines the high-signal scanning target shape the owner invoked as Mini God
  Tier: bounded intelligent walks, default CSB broad-scout phase, frontier
  selection, lake-first radar preflight, recency/current-state priority,
  branch decay/pivot discipline, dominance recording, value-based closure,
  CSB-first venue-value evaluation, exact-query discovery, hidden-venue
  discovery, precursor-signal handling, minimum evidence for promotion, shared scan
  vocabulary, and the capture-request handoff from scanning to the Capture
  spine. Bridges the
  Vertical Exploration Guide, the PROPOSED Demand Scan-Core Spec, and
  source-family lanes without ratifying scan-core, authorizing live scans, or
  moving packet-grade acquisition into scanning.
use_when:
  - Designing or reviewing a scanning lane that should behave like a high-signal bounded walker rather than a generic crawler.
  - Evaluating whether CSB-surfaced venues are worth downstream attention and whether hidden venues were missed.
  - Running the default bounded broad-scout phase for a CSB-first scan.
  - Prioritizing recent and current-state source reads without treating recency as proof.
  - Running bounded exact-query discovery to test CSB rows, find hidden venues, or record decisive negatives.
  - Deciding what scanning may emit before Capture, ECR, Cleaning, Judgment, or gate-run work begins.
  - Distinguishing precursor signals and precursor surfaces from gate proof, capture authority, or standing source maps.
  - Normalizing source-family lane outputs into shared scanning vocabulary and capture-request handoffs.
authority_boundary: retrieval_only
open_next:
  - docs/decisions/forseti_mini_god_tier_doctrine_v0.md
  - forseti/product/spines/foundation/vertical_exploration/forseti_vertical_exploration_guide_v0.md
  - docs/decisions/forseti_venue_registry_rejection_decision_v0.md
  - forseti/product/spines/scanning/scan_core/forseti_demand_scan_core_spec_v0.md
  - forseti/product/spines/scanning/admissibility_checkability/forseti_demand_scan_gate_adjudication_packet_v0.md
  - docs/decisions/screening_reddit_read_route_decision_v0.md
  - docs/workflows/screening_read_service_build_receipt_v0.md
  - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  - forseti/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md
  - forseti/product/spines/capture/core/source_families/social_media/creator_registry/creator_registry_match_preflight_usage_v0.md
stale_if:
  - The Mini God Tier doctrine is amended or re-pointed.
  - The Vertical Exploration Guide changes its walk contract, dry rule, or capture seam.
  - The Demand Scan-Core Spec is owner-adjudicated or amended on walk order, observation schema, or capture-needs handoff.
  - The default CSB broad-scout phase is amended, removed, or moved to another owner.
  - The recency/current-state priority is amended or superseded by a richer scan freshness contract.
  - A capture-owned request/route-binding contract supersedes the capture_request fields below.
  - The Creator Registry match preflight usage note or runner changes the receipt
    fields that clear new social creator/account capture.
  - A venue registry, atlas, crawler, monitor, or standing source-map decision is reopened by the owner.
```

## Status

`MGT_TARGET_OWNER_INVOKED` - owner-invoked in-thread 2026-06-21 for scanning.
This is a capability-target lens and operating model only. It is not
validation, readiness, scan-core ratification, scan authorization, capture
authorization, gate clearance, or buyer proof.

The product impulse may be described casually as a "smart crawler," but the
operating vocabulary here is **bounded intelligent walk**. "Crawler" is avoided
as source vocabulary because Forseti's standing crawler / monitor / registry /
atlas shapes are explicitly out of bounds unless a later owner decision reopens
them.

## Target Shape

Scanning should spend most of its read budget on value-bearing or
value-routing venues: the surfaces CSB nominated, exact public queries that can
find or disqualify venues, hidden venues CSB missed, independent-origin leads,
contradictions, high-quality pointers, decisive negatives, access notes, and
only those precursor surfaces that change the next route. It is not optimized
for exhaustive coverage.

Every CSB-first scan includes a bounded broad-scout phase by default. The phase
miss-checks the board before or alongside main deepening; it does not replace
main scanning judgment, mint candidates, clear gates, or bind Capture routes.

Target loop:

```text
authorized seed / objective
-> CSB board or owner-authorized seed
-> bounded broad-scout phase for CSB-first scans
-> bounded intelligent walk over venues
-> frontier-selected venue reads and exact-query probes
-> venue-value notes / exact-query negatives / hidden-venue pointers
-> lightweight observations
-> minimum-evidence promotion
-> capture request
-> capture spine acquisition
-> gate-run adjudication
```

The MGT bet is that this captures most of the value of a maximal crawler-like
system without accepting the infrastructure, maintenance, policy, and
source-drift cost of standing crawl machinery.

## Default CSB Broad-Scout Phase

A CSB-first scan runs a bounded broad-scout phase by default. The scout asks:
what high-value public venues did CSB miss; which CSB-nominated venues look low
value; which exact queries test the remaining gap; which recent/current-state
surfaces deserve main deepening; and which access walls or decisive negatives
should stop wasted effort.

Before external scanning in a recurring or actively radarred source family,
inspect the existing Data Lake through the highest-trustworthy current read
surface available: relevant Silver/current view first, then packet or catalog
inventory, then raw material when necessary. Use the result to reuse prior work
and identify stale, incomplete, conflicting, or source-fidelity gaps. Do not
treat lake inspection as proof of current external reality. Absence from Silver
is not absence from the lake or external world, and a missing read model does
not block acquisition.

The broad-scout phase is bounded by the scan commission's run cap. A scan may
use one route-ledger subagent for the scout when subagent support is available;
if not, the main operator runs the scout inline. The required default is the
bounded phase, not a hard dependency on subagent infrastructure.

A broad-scout return should be small and route-shaped: `frontier` entries
checked, `exact_query` strings used, `venue_eval`, `hidden_venue_pointer`,
`negative`, `access_note`, recency/current-state notes, and recommended main
deepening. It cannot emit final candidate decisions, clear demand gates, set
Capture routes, authorize source expansion, or continue after the commission cap
is reached.

## Hard Boundaries

Scanning does not own:

- standing crawlers, monitors, source maps, registries, or atlases;
- subagent infrastructure or any requirement that broad scout run only through subagents;
- packet-grade capture, manifests, ECR, screenshots, raw preservation, or route
  expansion;
- capture route binding or source-access policy decisions;
- replacing the demand gate with collection quotas;
- treating any numeric source, row, observation, venue, query, or capture-target
  count as acquisition completion;
- freezing final packet inclusion, which remains downstream;
- full-schema burden on every exploratory move;
- contact, outreach, lead-list, follower-graph, comment-scraping,
  channel-dossier, person-dossier, or standing creator-monitoring work.

Scanning owns, inside an authorized run:

- choosing the next public read by its expected contribution to the outcome the
  scan was commissioned to inform;
- recording when a plausible route is genuinely redundant with evidence already
  acquired for the same information job;
- deciding acquisition continuation and closure under the value test below;
- producing screen-light summaries, short quotes, precursor signals, precursor
  surfaces, venue evaluations, hidden-venue pointers, negatives, access notes,
  and candidate observations;
- preserving dated provenance for what was tried and why;
- emitting capture requests that tell Capture what to inspect and what the
  scan thinks that inspection could support.

## Frontier Selection

A frontier is a next-read candidate: a URL, venue, search phrase, hub, thread,
byline trail, source-family surface, or cross-reference the walk may inspect.

Choose the next frontier by its expected contribution to the outcome the scan
was commissioned to inform, not by crawl coverage. For an Intelligence Cycle,
that outcome is the bound phase question; for a gate-run scan, it is the action,
action ceiling, rival assessment, or hold condition.

Rank frontiers to decide sequence only. A lower-ranked frontier remains live
when it could add a distinct, material contribution; a higher-ranked move never
substitutes merely by outranking it. Same-direction evidence remains valuable
when it adds an independent origin, substantive detail, another angle or
attribute, mechanism, qualification, segmentation, corroboration, or
contradiction.

Source-family membership is not a redundancy test. Two independently reported
articles, threads, review corpora, or creator posts may sharpen or corroborate
the same seam even though they belong to the same family. Treat a move as
repetitive only after checking origin, syndication/echo, substance, and likely
effect on the material-seam disposition. A copied wire story, syndicated review
feed, repost, or same-origin restatement counts once; an independent origin does
not become duplicative merely because it points in the same direction.

High-value reasons include:

- likely value of a CSB-nominated venue for this decision;
- likely hidden venue or surface that CSB missed;
- exact query likely to reveal a hidden venue, better origin, or decisive negative;
- likely precursor surface that may reveal better origins or candidates;
- likely independent demand-origin signal;
- likely gradeable costly-behavior evidence;
- likely contradiction, divergence, or defeater;
- likely pointer to a better venue or origin;
- recent or current source state inside the decision window;
- likely decision-owner or org-motion context;
- low access/policy risk relative to expected value;
- decisive negative value, where ruling it out changes the scan route.

The scan records why a frontier was selected when that reason is load-bearing.
This reason is a steering explanation, not a score or proof.

## Leads, Angles, And Material Seams

A **lead** is an individual observation or pointer. An **angle** is a coherent,
product-relevant inquiry created by one direct lead or by several leads that
converge on the same attribute, mechanism, condition, or consequence. A
**material seam** is an evidence-revealed relationship, alignment, tension, or
contradiction between observable surfaces that could materially change,
qualify, deepen, or explain the answer to the bound question.

One direct lead opens an angle immediately when it directly supports or attacks
a load-bearing promise, use case, mechanism, experience, channel translation,
or value condition. Several weaker leads open an angle when they coherently
converge; no lead count establishes or prevents an angle.

Every evidence-revealed, decision-relevant angle receives a discriminating
check unless it is already answered, plainly immaterial to the bound question,
or genuinely repetitive. The check is question-directed; it is not a one-query
ceiling or permission for a shallow pass. Promote an angle to a material seam
only when the checked evidence changes the supported answer at the bound
question's scope. Apply **Materiality decision effect (all source families)** in
`forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md`
for the before/after comparison, claim-support limits, and unresolved-check
disposition. Corroboration, a new mechanism or condition, or a detailed individual
report is not automatically material. Meaningful audience resonance may change
an optics answer without verifying the underlying product allegation.

Once visible, a material seam is a required information job. Before acquisition
can close, it must be supported, contradicted, meaningfully bounded, or honestly
blocked or gapped. This is adaptive evidence work, not an up-front seam
inventory, source quota, observation quota, or new ledger. Use the existing
observation, pointer, negative, gap, and capture-request vocabulary.

Example: a detailed report of pilling directly attacks a product's
"layers seamlessly under makeup" claim and opens a layering-compatibility
angle. Independent reports or a newly supported condition can promote the
claim-to-experience relationship when they change the bound answer. Several pump
complaints that converge on trapped product and lost value can open a
packaging-to-value angle.
Unrelated complaints about delivery, bottle color, coupons, and a damaged
shipping carton remain separate leads unless they form a coherent,
product-relevant inquiry.

Precursor is a venue-routing concept here. Do not relabel ordinary weak
owned/channel/editorial evidence as a precursor just because it falls below the
candidate bar. If the item mainly tells the operator whether a venue is useful,
record it as venue value, pointer, negative, access note, or unknown.

## Recency And Current-State Priority

Recency is a hard attention-priority rule, not proof. After source-family hard
stops and CSB routing, assign more scan attention to recent or current-state
URL-backed frontiers. For same-strength signals, the newer/current source
normally outranks the older source even when direction differs; a one-month-old
buyer comment generally deserves more scan attention than a one-year-old comment
of the same intensity.

High-priority recent/current-state frontiers include current official or
retailer state, dated buyer-language reviews, forum/community posts, stockout,
restock, sold-out, waitlist, availability changes, and recent editorial,
partner, or org-motion pointers. Older sources remain admissible when they
establish origin, chronology, partnership provenance, baseline contradiction, or
backtest cutoff. Label those as historical or contextual, and do not let them
override fresh current-state reads without a load-bearing reason.

Record `retrieval_date` for each load-bearing read and the event, review,
publication, or source-state date when available. If an older source is carried
forward, record why it is still load-bearing and whether a re-verify or
`stale_after` note is needed before downstream use.

## Public-Reaction Engagement Priority

Public-reaction engagement is resonance and routing context, not proof. When a
frontier exposes upvotes, helpful votes, likes, views, shares, comment counts,
reply counts, source-native score state, visible sort/rank/order, or
pinned/hearted/official-response markers, scanning should treat that public
reaction as qualitative resonance weight by default and may use it to prioritize
the next read, explain venue value, or request Capture preservation.

For same-source and same-strength public-reaction evidence, a detailed signal
with materially higher visible engagement usually deserves more scan attention
than a drive-by signal with little or no engagement. Direction, visible audience
fit, source baseline, manipulation risk, and ambiguity decide how much priority
the context deserves. This is a route-priority and resonance-hypothesis claim
only. Scanning must not use engagement context to decide demand, credibility,
independence, artificial amplification, gate clearance, graph weight, final
resonance weight, or Action Ceiling. Source-family adapters with explicit
engagement, visibility, rank, or influence fields inherit the same boundary.

## Exact Query Discovery

An `exact_query` is a bounded public query string crafted to test a CSB row,
find a hidden venue, reach a better origin surface, or produce a decisive
negative. Exact-query discovery belongs to scanning because it is part of
frontier selection and venue-value evaluation.

Rules:

- count each exact query plus first-pass result inspection against the run cap;
- record the query string, intent, retrieval date, result class, and next-route
  decision when it changes the walk;
- when the row is creator/social or influence-related, public YouTube video and
  Shorts result pages are allowed screening routes if reachable without login
  and selected inside the run cap;
- emit discovered venues as `hidden_venue_pointer`, weak/no-yield results as
  `negative`, and access/policy walls as `access_note`;
- do not treat query count, search rank, AEO visibility, or repeated SERP
  presence as demand proof;
- do not turn exact queries into a standing query monitor, search-volume model,
  SEO keyword surface, crawler, or registry.

## Branch Decay, Pivot, And Stop

Continue acquisition while any practical remaining move is reasonably likely
to add material incremental value to the outcome the scan was commissioned to
inform. Incremental value includes changing, strengthening, independently
corroborating, qualifying, segmenting, or meaningfully deepening a finding;
adding mechanism, substance, another angle or attribute; pursuing a material
seam exposed by initial or later evidence; and testing a credible alternative or
contradiction. Rank moves to decide sequence only, never to eliminate distinct
work.

Before claiming closure, let the language, explanations, complaints,
comparisons, contradictions, and unexplained observations actually found
generate the remaining frontier. Close acquisition only when every material
seam has an earned disposition and the remaining practical moves are reasonably
expected to add only immaterial or genuinely repetitive evidence. Evidence is
repetitive only when it adds no meaningful independent origin, substance, angle,
mechanism, qualification, segmentation, corroboration, or contradiction.

A typed gap closes a material requirement only when the commission's existing
limits or source boundaries prevent the remaining answer-bearing work. A
touched lens, zero-yield route, exhausted route list, or absence of a promotable
candidate is a route result, never evidence of acquisition closure.

The following conditions stop the current run but do not by themselves prove
acquisition closure:

- the run budget, cap, or source-policy boundary is reached;
- the remaining path would require standing monitoring, bulk access,
  auth-gated data, packet-grade capture, or a capture-owned route decision;
- the current guide or run-specific walk contract fires a hard stop that this
  operating model did not explicitly supersede.

When a safety or policy stop fires before the closure test is satisfied, record
the unanswered material requirement as a typed gap or hold. No numeric target
or exhausted collection allowance earns completion.

For ordinary vertical walks, the Vertical Exploration Guide's dry rule remains
the default. For explicitly declared MGT / intelligent-walk scans with multiple
frontiers, dry handling is branch-aware: repeated dry moves close the active
branch; they do not automatically end the whole run while another declared or
freshly surfaced frontier has non-trivial expected value and the run remains
inside caps.

A scan is **explicitly declared** MGT when the scan authorization or commission
document invokes this operating model and the branch-aware rule by name. The
declaration must appear in the authorizing commission, not be asserted at
runtime by the walk itself. An authorized scan that does not carry an explicit
MGT declaration uses the ordinary dry rule.

A **run cap** (move budget, read limit, or equivalent) must be stated in any
MGT scan commission. Caps are the primary enforcement mechanism that makes
branch-aware pivot behavior bounded rather than open-ended. A scan commission
without a stated cap does not qualify as a bounded intelligent walk under this
model and must not invoke the branch-aware dry rule. A cap is a safety boundary,
not an acquisition-completion target.

## Shared Vocabulary

Source-family lanes should emit into this vocabulary instead of inventing
separate downstream shapes:

- `frontier` - a candidate next read and its reason;
- `move` - one bounded read or attempted read;
- `exact_query` - a bounded public query string used to test a CSB row, find a
  hidden venue, reach a better origin, or produce a decisive negative;
- `broad_scout_return` - a bounded route ledger for a CSB-first scan: checked
  frontiers, exact queries, venue evaluations, hidden-venue pointers, negatives,
  access notes, recency/current-state notes, and recommended main deepening;
  not a candidate decision, gate decision, capture route, or source-expansion
  authorization;
- `precursor_signal` - an early, URL-backed clue that may guide a walk but is
  tied to a venue or surface worth probing; not proof, gate clearance, or
  capture authorization;
- `precursor_surface` - a venue, hub, thread, search, AEO surface, source-family
  surface, or cross-reference that produced or likely produces precursor
  signals inside an authorized run; not a registry, atlas, monitor, or standing
  source map;
- `venue_eval` - a screen-light assessment of whether a CSB-nominated or
  discovered venue is worth more retrieval, capture, or exclusion for this
  commission;
- `hidden_venue_pointer` - a URL, venue, hub, or source-family surface not
  surfaced by the starting CSB board but worth returning to CSB, scanning, or
  Capture as a route candidate;
- `dominance_record` - a rejected route proven likely to repeat evidence already
  acquired for the same information job, naming the acquired substitute and the
  shared underlying origin, substance, or angle; it is a route-redundancy record,
  never a ranking comparison between distinct information jobs;
- `candidate` - possible target/company/topic worth carrying forward;
- `observation` - screen-light evidence or contradiction tied to a URL;
- `pointer` - a URL, venue, byline, hub, or cross-reference likely to improve
  the next read;
- `negative` - checked path with decisive low/no yield;
- `access_note` - public access constraint and shapes tried;
- `influence_obs` - hub, pointing structure, public creator-video pointer,
  wind-caller, or detector signal;
- `gate_role` - what demand-gate role the observation might support, if any;
- `capture_request` - scanning's request for Capture to inspect specified
  URLs for specified observations.

These terms are screen-light. They do not mint ECR, Cleaning, Judgment,
claim-ladder, packet, buyer-proof vocabulary, source-access authority, or gate
proof.

## Promotion Schema, Not Collection Quotas

Collection targets are search hygiene only. They do not decide inclusion,
acquisition closure, or whether demand is real, durable, manufactured, or
action-worthy. The schemas below are structural promotion requirements, not
numeric collection minimums.

Promote a move note to an observation when the signal is worth carrying for
downstream gate or capture evaluation: it ties to a specific URL and a possible
gate role, decision window, or candidate. Do not promote every observed item;
do not suppress signal that may support a candidate entry.

`signal_stage` names what the scan currently thinks the item is doing.
`gate_role` remains separate: a precursor may have no gate role yet, and a
possible gate role does not turn the precursor into proof.

Minimum promotion from move note to observation:

```yaml
observation_id:
source_move_id:
url:
retrieval_date:
short_quote_or_summary:
signal_stage: venue_value | precursor | candidate_support | contradiction | negative | access_note | unknown
claim_it_might_support:
gate_role: none | demand_origin | costly_behavior | divergence | org_motion | decision_event | influence
independence_hypothesis:
uncertainty_or_limits:
```

Minimum promotion from observation to candidate observation:

```yaml
candidate_observation_id:
candidate:
supporting_observations: []
why_promoted:
decision_window:
competing_or_defeating_observations: []
capture_needed: yes | no | unknown
```

The richer Demand Scan-Core schema remains the right home when an authorized
scan has enough signal to emit a candidate entry. It should not be forced onto
every low-level move.

## Capture Request Contract

Scanning hands Capture a request, not a route.

Emit a `capture_request` only when the observation needs Capture-owned action,
not merely because a venue produced a non-empty clue. At least one must be true:

- the source state is volatile or time-sensitive enough that packet-grade
  preservation could matter;
- the next useful read is blocked by a source-access, entitlement, or
  route-binding boundary that scanning must not cross;
- a promoted or near-promoted candidate-support observation needs Capture to
  preserve provenance before gate use;
- a hidden venue is high-yield enough that Capture-owned acquisition is the
  right next action, not another screen-light scan move.

The request must name the decision-material information job, the specific
acquisition or preservation value sought, and why an acquired observation or
existing lake packet does not already provide that value. A similar conclusion
does not substitute when the requested capture adds an independent origin,
substance, angle, mechanism, qualification, segmentation, corroboration, or
contradiction.

Do not emit a capture request for ordinary owned-only chronology, retailer
presence, editorial visibility, AEO visibility, or weak precursor material
unless one of the triggers above is explicitly satisfied.

```yaml
capture_request_id:
source_scan:
candidate_or_observation_ids: []
urls:
  - url:
    venue:
    observation_supported:
    gate_role:
what_capture_should_verify:
decision_window:
route_binding_state: cited_current | unknown | blocked_outside_current_binding | not_applicable
creator_registry_match_preflight:
  required_when: new_social_creator_account_capture | not_applicable
  receipt_path: null_or_path
  intended_action: new_capture | classify | update_existing | not_applicable
  decision: existing_match | new_candidate | ambiguous_match | invalid_candidate | not_applicable
  action_status: allowed | blocked | not_applicable
  can_start_new_capture: true | false | not_applicable
screening_evidence_summary:
uncertainty_or_access_limits:
not_requested:
  - route expansion
  - packet commitment by scanning
  - ECR, Cleaning, or Judgment work
```

Capture decides route binding, entitlement/source policy, acquisition method,
packet-grade preservation, manifests, and packet lifecycle. The scan may cite a
known current binding or say `unknown`; it must not set, stretch, or recommend
the route.

For social creator/account capture requests, the
`creator_registry_match_preflight` block is the scan-to-capture bridge into the
Creator Registry exact-match runner. Starting a new social creator/account
capture requires a preserved receipt row with `intended_action: new_capture` and
`can_start_new_capture: true`; a visual registry/projection scan is orientation
only and does not clear capture. Existing matches route to work against the
matched registry identity, while ambiguous or invalid rows stop until resolved.

## Gate Packaging

Scanning and the demand gate are different operations, but they should be
packaged as one efficient commission where authorized:

```text
scan with origination provenance -> in-session gate-run -> verdict / cap / hold
```

The gate remains the inference layer. It answers whether the collected evidence
clears de-correlation, costly behavior, integrity/divergence, and action
ceiling. Scanning supplies dated provenance and observations; it does not
replace the gate with raw source counts.

## Source-Family Adapter Rule

Reddit, LinkedIn, answer-engine/search, trade press, forums, trackers, review
surfaces, and future source families may keep local guardrails. Their
downstream scanning output should still map into the same shared terms:
`frontier`, `move`, `exact_query`, `precursor_signal`, `precursor_surface`,
`observation`, `pointer`, `venue_eval`, `hidden_venue_pointer`, `negative`,
`access_note`, `capture_request`, and `gate_role`.

Local restrictions always carry. Examples:

- Reddit screening reads remain orchestrator-mediated and screen-light.
- LinkedIn remains planning-only under its hard privacy and no-contact rails
  unless a separate owner-authorized mode applies.
- Search-interest / AEO remains proposed and gap-bound until owner-approved
  sourcing and schema placement land.
- Public YouTube videos and Shorts are allowed as screen-light creator/social
  routes when reachable without login and chosen by frontier/exact-query logic;
  record the video or Short URL, retrieval date, visible dated call/context, and
  campaign/affiliate caveat. Do not scrape comments, enumerate channels, build
  subscriber/follower graphs, create channel/person dossiers, or monitor
  creators. TikTok/Instagram live reads remain separately authorized.

## Accepted Residuals

These residuals are accepted for the MGT target. They are the price paid to
avoid the rejected maximal infrastructure.

| Residual | Why acceptable now | Remaining risk | Upgrade trigger |
| --- | --- | --- | --- |
| Long-tail miss risk | No standing crawl or exhaustive atlas keeps cost and policy risk low. | Some useful sources will be missed. | Repeated missed-source postmortems or sustained scan throughput bottleneck. |
| Rediscovery cost | Append-only provenance and card-set promotion cover reuse without maintaining a general registry. | Operators may revisit known venues before a trigger fires. | Same vertical third screen, multi-operator cadence, or sustained weekly cadence per the guide. |
| Capture re-fetch | Capture reuses appropriate existing lake packets before recapture and re-acquires only when currentness, fidelity, provenance, cutoff compliance, inspectability, or a named gap materially improves. | A justified recapture can still duplicate effort, and reuse can carry stale-state risk. | Repeated stale or insufficient packet reuse despite typed recapture reasons. |
| Judgment-dependent frontier choice | Human/agent judgment gives high signal without building crawler ranking infrastructure. | Frontier selection may be inconsistent across operators. | Repeated low-yield scans from poor frontier ordering. |
| Full schema deferred until promotion | Lightweight moves keep exploration fast. | Some weak signals may be under-structured until promoted. | Review finds promoted observations lack fields needed for gate or capture. |
| Source-family gaps cap ceilings | Review surfaces, search-interest, and AEO are not all sourced or gate-recordable today. | Some candidates stay hold/low-commitment or gap-tagged. | Owner adjudicates source-class cards and capture bindings. |
| No readiness claim | This is an operating model, not proof. | The shape may still need review, live rehearsal, and source-family tuning. | Owner asks for ratification, first scan commission, or validation evidence. |

## Non-Claims

Not validation, readiness, buyer proof, gate clearance, scan authorization,
capture authorization, scan-core ratification, source-family adoption, crawler
approval, monitor approval, registry approval, subagent-infrastructure mandate,
or live web access permission. No implementation, scheduler, crawler,
dashboard, storage layer, packet runner, ECR, Cleaning, Judgment, outreach, or
buyer-contact work is authorized here.

## Direction Change Propagation

```yaml
direction_change_propagation:
  doctrine_changed: >
    Scanning core now treats public YouTube videos/Shorts as bounded non-login
    creator-video routes for creator/social exact-query and frontier reads,
    while preserving no TikTok/Instagram live read without separate authorization,
    no comment scraping, no channel/person dossier, no graph, and no standing
    creator monitoring.
  trigger: product_doctrine
  related_triggers:
    - workflow_authority
  controlling_sources_updated:
    - forseti/product/spines/scanning/scan_core/orca_scanning_intelligent_walk_mgt_operating_model_v0.md
    - forseti/product/spines/scanning/scan_core/orca_demand_scan_core_spec_v0.md
  downstream_surfaces_checked:
    - AGENTS.md
    - .agents/workflow-overlay/README.md
    - .agents/workflow-overlay/source-of-truth.md
    - .agents/workflow-overlay/prompt-orchestration.md
    - forseti/product/spines/scanning/README.md
    - docs/workflows/orca_repo_map_v0.md
    - forseti/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md
    - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  intentionally_not_updated:
    - path: AGENTS.md
      reason: >
        Agent kernel rules are unchanged; this is scanning-method routing, not a
        global behavior rule.
    - path: .agents/workflow-overlay/prompt-orchestration.md
      reason: >
        Prompt authoring contract is unchanged; future scanning prompts inherit
        this through the scanning core source pack.
    - path: forseti/product/spines/scanning/README.md
      reason: >
        The front-door already routes cold scanning starts through this MGT model
        and the proposed Demand Scan-Core Spec; duplicating the YouTube/Shorts
        rule there would create a second wording surface.
    - path: docs/workflows/orca_repo_map_v0.md
      reason: >
        Repo-map routing is unchanged: scanning tasks still open the scanning
        README, which opens this MGT operating model.
    - path: docs/prompts/product-planning/imaginary_authors_core_satellite_csb_recommission_prompt_v0.md
      reason: >
        The owner clarified the target as the reusable core for future asks, so
        the one-off executed IA commission was restored instead of silently
        rewriting that historical prompt.
  stale_language_search: >
    rg -n "YouTube|Shorts|creator-video|creator/social|comment scraping|comment-scraping|channel/person|channel-dossier|creator graph|standing creator|TikTok/Instagram live"
    forseti/product/spines/scanning docs/prompts/product-planning docs/workflows/orca_repo_map_v0.md
    forseti/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md
    forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
    (run 2026-06-22)
  stale_language_search_result: >
    Executed 2026-06-22 after edit. In the scanning core, hits are this accepted
    bounded-route rule, the proposed schema alignment, or the receipt itself. In
    product-planning prompts, older subject-specific prompts still carry their
    prior TikTok/Instagram live-read boundaries; the IA recommission prompt is
    restored to its pre-correction state. Repo-map hits only route to the scanning
    spine. The capture recon index/playbook in this worktree do not contain a
    YouTube source-family route; this change creates no capture route, comments
    route, channel/person dossier, graph, monitoring, or TikTok/Instagram live
    access authorization.
  non_claims:
    - not validation
    - not readiness
    - not scan authorization
    - not capture authorization
    - not source-access authorization
    - not implementation authorization
```
```yaml
direction_change_propagation:
  doctrine_changed: >
    Scanning now treats evidence-revealed angles and material seams as adaptive
    acquisition work, values substantive same-direction evidence, uses ranking
    only for sequence, narrows dominance to genuine route redundancy, and
    blocks rather than seals when unresolved material seams outlive the
    commission's existing limits.
  trigger: workflow_authority
  related_triggers:
    - lifecycle_boundary
  controlling_sources_updated:
    - forseti/product/spines/scanning/scan_core/forseti_scanning_intelligent_walk_mgt_operating_model_v0.md
    - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
  downstream_surfaces_checked:
    - AGENTS.md
    - .agents/workflow-overlay/README.md
    - .agents/workflow-overlay/source-of-truth.md
    - .agents/workflow-overlay/decision-routing.md
    - docs/decisions/forseti_mini_god_tier_doctrine_v0.md
    - forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md
    - forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md
    - .agents/hooks/check_commission_signal_board_output.py
    - forseti-harness/tests/unit/test_commission_signal_board_output_validator.py
    - docs/workflows/forseti_repo_map_v0.md
  intentionally_not_updated:
    - path: forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md
      reason: >
        CSB owns planning-time route inclusion and already delegates acquisition
        continuation and closure to Scanning; the observed failure occurred
        after commissioning.
    - path: forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md
      reason: >
        Its equal-or-better language governs planning-time route substitution,
        not evidence-derived frontier closure, and it already states that zero
        yield and coverage do not establish acquisition completion.
    - path: .agents/hooks/check_commission_signal_board_output.py
      reason: >
        Lead, angle, seam, and evidence sufficiency are judgment semantics; no
        new field or mechanically truth-verifiable predicate was added.
    - path: docs/decisions/forseti_mini_god_tier_doctrine_v0.md
      reason: >
        The capability-target lens and accepted-residual discipline are
        unchanged; this edit applies them to acquisition behavior.
    - path: docs/workflows/forseti_repo_map_v0.md
      reason: >
        No path, owner, or start route changed.
  stale_language_search: >
    rg -n -i "best remaining move|higher expected decision value|equal-or-better included|lawful, access, and safety bounds|zero yield.*completion|lens.*acquisition closure"
    forseti/product/spines/scanning/scan_core/forseti_scanning_intelligent_walk_mgt_operating_model_v0.md
    forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
  non_claims:
    - not validation
    - not readiness
    - not behavioral proof
    - not a source, observation, lead, angle, or seam quota
    - not a new acquisition schema or validator gate
```

Older receipts archived verbatim in `docs/decisions/dcp_receipts_archive_v0.md`.
