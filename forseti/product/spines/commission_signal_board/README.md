# Commission Signal Board Spine

```yaml
retrieval_header_version: 1
artifact_role: Spine README
scope: Entry point for the live Commission Signal Board spine and the Forseti Intelligence Cycle operating contract.
use_when:
  - Starting Commission Signal Board prompt, playbook, validator, or migration work.
  - Commissioning an Understanding or Deliver phase of a Forseti Intelligence Cycle.
  - Checking which CSB artifacts are canonical after the spine-first pilot authorization.
  - Distinguishing the live CSB pilot from the staged global docs migration.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/commission_signal_board/spine.yaml
  - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
  - forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md
  - forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md
  - forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
  - forseti/product/spines/commission_signal_board/migrations/moved_paths_index.md
stale_if:
  - The Commission Signal Board spine is renamed, retired, or merged into another spine.
  - The executable validator moves out of .agents/hooks.
  - Global Forseti docs move into a product-root docs subtree.
```

- Status: LIVE_PILOT_SPINE.
- Owner authorization: current-turn authorization, 2026-06-18.
- Current scope: Commission Signal Board plus the docs-only Forseti Intelligence Cycle operating contract.
- Global docs migration: accepted in direction, staged, not executed here.

## Canonical Artifacts

| Role | Path |
| --- | --- |
| Spine manifest | `forseti/product/spines/commission_signal_board/spine.yaml` |
| Prompt Structure Rules | `forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md` |
| Prompt Structure | `forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md` |
| Playbook / Forseti Intelligence Cycle contract | `forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md` |
| Deliver decision-memorandum method | `forseti/product/spines/commission_signal_board/workflows/deliver_decision_memorandum_method_v0.md` |
| Validator pointer | `forseti/product/spines/commission_signal_board/harness/validator.md` |
| Test pointer | `forseti/product/spines/commission_signal_board/tests/validator_tests.md` |
| Moved-path index | `forseti/product/spines/commission_signal_board/migrations/moved_paths_index.md` |
| Phase-vocabulary migration note | `forseti/product/spines/commission_signal_board/migrations/intelligence_cycle_phase_vocabulary_migration_v0.md` |

Naming note: **Prompt Structure** is the runnable CSB prompt/template. **Prompt Structure Rules** is the durable authority/rules doc for that prompt structure. File paths now use role-aligned names.

## Commission Profiles And Time Postures

CSB keeps the existing `mode: backtest | forward` axis unchanged and adds two
orthogonal fields:

- `commission_profile: standard_signal_board | company_competitive_intelligence`;
- `time_posture: recency_first | longitudinal`.

`recency_first` is the universal default and uses the canonical prompt's
deterministic 0-30, 31-90, 91-180, and over-180-day ladder. `longitudinal` is an
explicit override only for change, recurrence, or trajectory across a declared
period and requires both the period and rationale. A named event is a route or
query inside one of these two postures, not another posture.

A commission for one company subject defaults to
`company_competitive_intelligence` when the subject is a Brand or Org, including
an unresolved Brand/Org identity. That profile produces the conditional
ten-section company report and no demand-classifier handoff. Other commissions
continue to use the existing standard Sections 1-10 and classifier handoff.

## Forseti Intelligence Cycle

Future one-company intelligence work is commissioned as a **Forseti
Intelligence Cycle**, not by an unqualified `Phase 1` or `Phase 2` label. Its
canonical phases are **Understanding** and **Deliver**, in that order.
`Problem Framing` is the Deliver phase's historical name; historical artifacts
keep it, and problem framing survives as the Deliver phase's first synthesis
step (decision frame and target screen). Each phase has two possible
operator/model turns. An owner instruction that says **Understanding** or uses
historical **Phase A** language without also naming a synthesis deliverable
commissions **Acquire & Seal only** and stops after the seal. Passing the seal
makes the Synthesize turn eligible but never starts it; synthesis requires an
explicit current commission or a separately authorized follow-up.

The two possible turns are:

1. **Acquire & Seal** — bind the phase question and intended use, resolve
   canonical source routes before capture, run authorized Scanning/Capture, and
   preserve the resulting route receipts, provenance, failures, and seal state
   in a durable phase artifact. In the Deliver phase this turn is bounded to
   decision-specific supplements to the Understanding substrate, never a
   general re-scan.
2. **Synthesize** — start in fresh context from that artifact, verify its
   acquisition gate, then synthesize and hand off without claiming evidence,
   coverage, provenance, or route exhaustion the seal does not support.
   Understanding synthesis produces the decision-neutral company-intelligence
   substrate; Deliver synthesis produces the explicitly commissioned
   decision-bearing artifact under the Deliver decision-memorandum method.

Both turns consume the shared intelligence claim-support contract before they
turn evidence into a finding. Acquire & Seal preserves the support and conflict
postures needed downstream; Synthesize and Deliver may not silently promote an
isolated or resonance-only observation into independent recurrence,
cross-venue corroboration, representative prevalence, or causation.

Use the phase-specific owners below; the playbook remains the operating
contract. Open the source for the current job rather than loading every owner.

| Current job | Owning source |
| --- | --- |
| Company acquisition order, actor roles, and source routing | [Default Understanding route](workflows/commission_signal_board_playbook_v0.md#default-us-consumer-beauty-understanding-route); [acquisition sequence](workflows/commission_signal_board_playbook_v0.md#acquisition-and-seal-sequence), including retailer breadth in step 3 |
| Consumer-brand completion, depth, maturity, and final source review | [Intelligence Cycle operating rules](authority/forseti_commission_signal_board_prompt_structure_rules_v0.md#forseti-intelligence-cycle-operating-contract) |
| Company information jobs, retailer admission, and metric claim limits | [Conditional company prompt contract](prompts/forseti_commission_signal_board_prompt_structure_v0.md#conditional-company-competitive-intelligence-output-contract) |
| Synthesis gate and Deliver boundaries | [Turn B](workflows/commission_signal_board_playbook_v0.md#turn-b--synthesize) |
| Commissioned Deliver memorandum | [Deliver decision-memorandum method](workflows/deliver_decision_memorandum_method_v0.md) |

When both turns are explicitly commissioned, two turns are the normal budget,
not permission to convert a blocked acquisition into apparent completion. The
playbook owns the full contract and the six non-numeric outcome signals.
Historical artifact names containing `phase1` or `Phase 1` remain historically
accurate provenance and are not executable names for a future cycle.

## Legacy Non-Controlling Artifacts

| Artifact | Status | Current authority |
| --- | --- | --- |
| `forseti/product/spines/commission_signal_board/dispatch_rules/forseti_demand_gate_run_commission_criteria_v0.md` | Historical only; not a live CSB dispatch rule | Use the CSB prompt and playbook. CSB is an evidence/signals-only board and must not emit admit/hold/fail gate verdicts. |

## Boundaries

CSB owns commission profiles, source-family requirements, time posture, and
typed gaps/requests. Scanning owns the intelligent walk, exact-query and
category-aware hidden-venue discovery, negatives, access notes, and frontier
closeout. Capture owns lawful source access and preservation adapters. CSB does
not contain venue or research modules and does not fake either downstream act.
CSB defines material information jobs and candidate routes; it does not freeze a
participant packet, decide final inclusion, or declare acquisition complete.
Every included item needs a named decision-material job and no equal-or-better
included substitute.

For recurring or actively radarred source families, CSB routes a lake-first
preflight before external Scanning or Capture: relevant Silver/current view,
then packet or catalog inventory, then raw material when needed. Lake inspection
tests reuse, freshness, and coverage only. It is not proof of current external
reality; absence from Silver is not absence from the lake or the world, and a
missing read model does not block acquisition.

This spine does not authorize retrieval, scraping, capture, graph construction,
demand classification, forecasting, judgment, buyer proof, validation,
readiness, CI, hook wiring, or runtime work. Public-reaction engagement belongs
in CSB as resonance/routing context only; the authority and prompt artifacts keep
it separate from proof, Commit/Scale support, graph weight, classifier mapping,
final resonance weight, and Action Ceiling.

The executable validator remains at
`.agents/hooks/check_commission_signal_board_output.py`. The executable tests
and fixtures remain under `forseti-harness/tests/`.

Company reports remain one-company-at-a-time and decision-neutral. They may use
bounded comparator pointers to interpret the subject, but deep competitor
treatment requires a separately named follow-up commission. Their Company
Surface ledger is candidate-only: no import, identity resolution, stored
corpus, or Company Surface mutation occurs in CSB.

## Old Paths

The old CSB doc paths under `docs/` are absent on current `main`. Use the
moved-path index before following historical links or older handoff packets:

```text
forseti/product/spines/commission_signal_board/migrations/moved_paths_index.md
```
