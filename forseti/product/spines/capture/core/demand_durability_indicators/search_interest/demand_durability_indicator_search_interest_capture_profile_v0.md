# Demand-Durability Indicator — Search-Interest Capture Profile v0

```yaml
retrieval_header_version: 1
artifact_role: Product-method spec (demand-indicator capture profile)
scope: >
  Capture profile for the search-interest demand-durability indicator. Specifies
  what the capture lane must record and what limits must be made visible when
  search-interest signals are commissioned for a Decision Frame. Design+spec
  only. Does not authorize sourcing, implementation, contract hardening, or
  runtime. Conditional on sourcing (see below).
use_when:
  - Specifying or reviewing search-interest capture obligations for a commissioned Decision Frame.
  - Checking the temporal regime, cold-start doctrine, and comparability constraints for a search-interest series.
  - Deciding whether a search-interest series is capture-ready for handoff to ECR.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/demand_durability_indicators/capture_envelope_durability_delta_spec_v0.md  # Lane 1 envelope-delta (temporal regimes, cold-start doctrine, five new elements)
  - orca-harness/source_capture/models.py                                          # Capture Envelope of record (schema)
  - forseti/product/spines/capture/core/contracts/obligation_contracts/core_spine_v0_data_capture_spine_obligation_contract_v0.md  # Obligation contract
  - forseti/product/spines/product_lead/buyer_proof/forseti_buyer_proof_packet_v0.md                        # INV-1, Demand-Substrate Hard Gate, costly-behavior
  - forseti/product/spines/scanning/admissibility_checkability/forseti_demand_gate_definition_closures_proposal_v0.md  # AR-04 sourcing-gap status
  - forseti/product/spines/scanning/source_families/answer_engine/demand_search_interest_sourcing_and_gate_delta_spec_v0.md  # scanning-side source-class/gate-read delta for search-interest/AEO
stale_if:
  - The Lane 1 envelope-delta spec (capture_envelope_durability_delta_spec_v0.md) is amended or superseded.
  - The capture envelope of record (models.py or the obligation contract) is amended in a way that covers these facts.
  - An owner decision adopts, narrows, or rejects the search-interest unsourced-gap classification (AR-04).
  - A sourcing authorization for search-interest is accepted (at which point this profile becomes binding, not conditional).
```

- Status: `CAPTURE_PROFILE_DRAFT_V0`
- Artifact type: Product-method spec (demand-indicator capture profile)
- Implementation authorized: no
- Feature planning authorized: no
- Runtime / source-system design authorized: no
- Contract hardening authorized: no (owner-gated, out of scope)
- Sourcing authorized: **no** — see Conditional-On-Sourcing statement below

## Retrieval Header And Deconfliction Note

**What this is.** This capture profile is a delta-on-the-envelope spec that
names the search-interest-specific capture obligations, temporal regime, and
comparability constraints a commissioned search-interest series must satisfy.
It CITES and CONSUMES — it does not re-derive, replace, or fork — the following
authoritative sources:

- **Lane 1 envelope-delta spec:** `forseti/product/spines/capture/core/demand_durability_indicators/capture_envelope_durability_delta_spec_v0.md`
  (status `DELTA_SPEC_DRAFT_V0`). Consumed: the three temporal regimes + cold-start
  inherent-limit cap (Element 5), the five new elements (pinning facts, cold-start
  marker, series-diff, cadence model), and the INV-1 preservation rule.
- **Capture Envelope of record:** `orca-harness/source_capture/models.py` (schema)
  and `forseti/product/spines/capture/core/contracts/obligation_contracts/core_spine_v0_data_capture_spine_obligation_contract_v0.md`
  (obligations). These are the controlling envelope authorities. If this profile
  appears to conflict with either, the envelope of record wins; treat this profile
  as stale and open the controlling source.
- **INV-1 and the Demand-Substrate Hard Gate:** `forseti/product/spines/product_lead/buyer_proof/forseti_buyer_proof_packet_v0.md`.
  Consumed as-is; not redefined here.
- **Demand-Read Taxonomy:** `forseti/product/spines/foundation/demand_read_taxonomy/forseti_demand_read_taxonomy_v0.md`
  (PROPOSED, pending adjudication). Consumed as orientation for buy-side signal
  layer positioning; not operative until owner adjudication.
- **Search-interest / AEO source-class delta:** `forseti/product/spines/scanning/source_families/answer_engine/demand_search_interest_sourcing_and_gate_delta_spec_v0.md`
  owns the scanning-side source-class and gate-read placement; this profile owns
  only capture obligations after sourcing.

**Deconfliction.** Search-interest is classified in
`forseti/product/spines/scanning/admissibility_checkability/forseti_demand_gate_definition_closures_proposal_v0.md`
(AR-04) as a **G1 unsourced demand-family gap** — owner-owned, not yet sourced.
This profile specifies capture obligations CONDITIONAL ON A SOURCE BEING SOURCED
(see below). It does not constitute sourcing authorization and does not resolve
the AR-04 gap. No deconfliction conflict with the obligation contract exists
because the contract's scope is commissioned-capture obligations; this profile
extends that scope for the search-interest surface type when a commission exists.

---

## Conditional-On-Sourcing Statement

**Search-interest sourcing is an UNSOURCED GAP (AR-04).** Per
`forseti/product/spines/scanning/admissibility_checkability/forseti_demand_gate_definition_closures_proposal_v0.md`,
search-interest is a G1 demand-family card that is currently unsourced — the
sourcing route, vendor, API, or access method has not been authorized by the
owner for Orca capture use.

**This capture profile describes obligations that apply ONLY AFTER a
search-interest source is sourced and the sourcing is authorized by the owner.**
Reading this document does not authorize sourcing, implementation, contract
hardening, vendor selection, API access, or any runtime. Those decisions are
owner-gated and out of scope for this profile.

**Bounded per-run exception (owner decision, 2026-08-06):** one one-shot
category-benchmark search-interest pull per commissioned broad consumer-brand
Phase A run is authorized as a run input; the requirement, decision rule, and
claim limits are owned by
`forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md`
("Category-Benchmark Search-Interest Read"). This exception does not source
the standing series, any cadence, or a vendor, and AR-04 otherwise remains
open. This profile's limits-visibility obligations (relative-index semantics,
entity/topic and pull-date pins, threshold discipline) apply to what such a
pull records.

---

## What This Profile Adds (Cited Extension, Not New Authority)

This profile names the search-interest-specific facts that sit on top of the
Lane 1 envelope-delta's five new elements. It does not invent new capture
facts; it applies the envelope-delta doctrine to the search-interest surface.

### Temporal Regime: Retroactive-Native

Search-interest is a **retroactive-native** source, as defined in Lane 1
envelope-delta §Element 5 ("The three temporal regimes"). The source natively
exposes its own history; a single capture can recover a back-run of prior
normalized values, bounded by the source's own retention window and the
platform's API or export capabilities.

Capture obligation (consumed from Lane 1, §Element 5 Regime 1):
- Record how far back native history reaches for the specific source surface
  and topic/entity, as a `VisibleFact`.
- Record the fidelity of that retroactive history: whether early values are
  estimates, revised, aggregated differently, or subject to the source's
  normalization retroactively changing with later data.
- The cold-start marker (Lane 1 §Element 2) still applies to *Orca's own
  coverage window*, but `pre_coverage_history_posture` may be partly satisfied
  by retroactive-native history — recorded with the source as the explicit basis,
  never asserted.
- Cold-start is an inherent-limit cap only for the window before the source's
  own history begins; retroactive-native recovery is bounded by the source's
  retention, not by Orca's prior observation window.

### Entity/Topic Pinning (Not Query String)

Search-interest sources normalize values relative to a query or topic
identifier, not to an absolute search volume. A single normalized value is
meaningless without knowing the exact entity or topic ID the source used.
A pull on Monday re-normalizes the entire series against Monday's peak.

Capture must record:
- `entity_topic_id_pin` — the source-internal entity or topic identifier (not
  the raw query string) used to anchor the pull. Carried as a `VisibleFact`.
  When the source does not expose a stable entity ID (only a query string),
  record the query string and mark the entity-ID as `unavailable_by_source`.
- `pull_date_pin` — the date of each pull, as a distinct capture fact per
  observation. Because the source re-normalizes per pull, two observations with
  different pull dates are not directly comparable on absolute values. Record
  this as a visible comparability limitation on the series.

These pins are extensions of Lane 1 §Element 1 (first-class pinning facts) for
the search-interest surface. They narrow what today lives generically inside
`capture_context`. They do not replace `capture_context`; they name the two
pins that recur for search-interest so a downstream reader can see a
re-normalization break without parsing prose.

### Shape / Durability, Not Magnitude Comparison

Search-interest series are **relative / normalized** by construction. Across
different pull dates, absolute values shift because the normalization peak
shifts. Capture must record this as a standing series-level limitation:

- The series is suitable for **shape and trend direction reads** (persistent /
  rising / declining / spiked-and-retreated) within a single pull's normalized
  window.
- It is **not suitable for magnitude comparison across different pull dates**
  without controlling for the normalization baseline.
- When downstream use will compare observations across pull dates, capture must
  flag that as an unresolved comparability question, not silently produce a
  composite series.

This is a capture-side observability obligation. Whether the shape is durable,
transient, or manufactured demand is a downstream Judgment call; capture records the series and
its normalization limits — it does not judge them.

### Locale and Geography Pin

Search-interest values typically depend on geography and language settings.
Capture must record:

- `locale_pin` — the geography and language scope the source returned results
  for (e.g., `US`, `en-GB`, worldwide), as a `VisibleFact` (Lane 1 §Element 1).
- When locale changes what is returned (a trend visible in the US may not
  surface globally), the capture records the actual locale observed; it does not
  infer global demand from a single locale pull.
- When locale is not controllable by the operator (the source determines it
  from account settings or IP), record that as `unavailable_by_source` with
  the best-available locale description.

### Cadence Disclosure (Consumed from Lane 1 §Element 4)

A search-interest series should declare its intended cadence using the existing
`CadencePlan` shape (Lane 1 §Element 4), record realized cadence per
observation via `capture_time`, and record cadence deviations and gaps as
visible limitations. Because the source re-normalizes per pull, cadence gaps
affect not just coverage but re-normalization baseline consistency.

### Series-Diff for Re-normalization Detection (Consumed from Lane 1 §Element 3)

The series-diff (Lane 1 §Element 3) applies to the search-interest series.
Observed differences across the series that may reflect source re-normalization
(the same historical date having a different normalized value across two pulls)
must be recorded as observed differences. Capture records the hash-based
difference as an observable; it does not decide whether the difference is due
to natural re-normalization or source-side data change. That determination is
downstream Judgment's.

---

## INV-1 Preservation

This profile is bound by INV-1 (no scoring, weighting, ranking, or judgment),
per `forseti/product/spines/product_lead/buyer_proof/forseti_buyer_proof_packet_v0.md` and the
demand-read taxonomy. Concretely:

- every capture fact described here is an **observable**, not a durability score;
- the series shape (rising, falling, spiked) is recorded as an observed pattern;
  whether that pattern reflects durable, transient, or manufactured demand is a Judgment call;
- no formula, threshold, weight, or numeric scoring rule appears in this profile;
- normalization limits are captured as visible constraints on downstream use,
  not as quality scores.

---

## Boundaries And Non-Goals

- **No sourcing authorization.** This profile is conditional on sourcing (see
  above). Reading it does not authorize any search-interest data access,
  vendor selection, API subscription, or search platform integration.
- **No second envelope.** The envelope of record (`models.py` + obligation
  contract) is the sole Capture Envelope authority. This profile cites it and
  extends it for the search-interest surface; it does not fork it.
- **No contract hardening.** Whether any fact named here becomes a schema field
  or obligation contract obligation is owner-gated and out of scope.
- **No ECR / Cleaning / Judgment design.** No ECR fields, Cleaning
  transformations, normalization rules, or Judgment/scoring logic.
- **No magnitude-comparison claims.** Capture records the series and its limits;
  downstream layers decide comparability and sufficiency.
- **No runtime, scraper, API, or scheduler design.** `CadencePlan` is referenced
  as an existing planning primitive only.
- **No implementation of any kind.** Design+spec only.

---

## Non-Claims

This profile is not validation, readiness, acceptance, contract hardening,
source-of-truth promotion, buyer proof, judgment-quality evidence, sourcing
authorization, implementation authorization, runtime authorization, tooling
authorization, scheduler/monitor authorization, source-access boundary
amendment, obligation-contract amendment, schema change, ECR design, Cleaning
implementation, Judgment design, or commercial-readiness evidence. It is a
design+spec profile that cites the existing Capture Envelope of record and the
Lane 1 envelope-delta spec and names the search-interest-specific capture
obligations and comparability constraints a commissioned series must satisfy
when a source is authorized.

---

## Lifecycle Verification

```yaml
lifecycle_verification:
  authored_by: Claude Sonnet 4.6 (claude-sonnet-4-6)
  authored_date: 2026-06-14
  worktree: .claude/worktrees/capture-indicator-search-review
  branch: capture-indicator-search-review
  base: origin/main
  pr_target: main
  sources_cited:
    - forseti/product/spines/capture/core/demand_durability_indicators/capture_envelope_durability_delta_spec_v0.md  # Lane 1 envelope-delta (consumed, not re-derived)
    - orca-harness/source_capture/models.py                                          # Capture Envelope of record (schema, cited)
    - forseti/product/spines/capture/core/contracts/obligation_contracts/core_spine_v0_data_capture_spine_obligation_contract_v0.md  # Obligation contract (cited)
    - forseti/product/spines/product_lead/buyer_proof/forseti_buyer_proof_packet_v0.md                        # INV-1, Hard Gate (consumed)
    - forseti/product/spines/scanning/admissibility_checkability/forseti_demand_gate_definition_closures_proposal_v0.md  # AR-04 (cited)
    - forseti/product/spines/foundation/demand_read_taxonomy/forseti_demand_read_taxonomy_v0.md                      # Signal layer orientation (consumed)
  inv1_preserved: yes — observables only, no scoring, weighting, ranking, or judgment
  conditional_on_sourcing: yes — AR-04 unsourced gap; sourcing not authorized by this profile
  contract_hardening_authorized: no
  implementation_authorized: no
  non_claims_stated: yes
```
