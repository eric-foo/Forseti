# Summer Fridays Phase A Decision-Useful Coverage Adversarial Review Prompt v1

```yaml
retrieval_header_version: 1
artifact_role: Review prompt
scope: >
  Artifact-only opposing-family review of whether the completed Summer Fridays
  Understanding Phase A covers most major unique decision-useful CI evidence bases.
use_when:
  - Testing the completed Summer Fridays Phase A evidence set before any Turn B.
  - Identifying a materially missing evidence family without reopening web acquisition.
authority_boundary: retrieval_only
input_hashes:
  acquisition_record: a86001897d32541fbcb60015085236c9398f988be387e7434c474739f787d7e9
  company_core: 6ed7095c9aaae60f4a647eba2f9841e70a0503d5890178ada0098bb982d32d10
  retail_portfolio: b3418ea2a8cd904880f5b0216c4ffccfac95a6dbf2338267182828931ff105e8
  customer_community: 33f1456b0c830830328a640aa5f07f18bcdd87d904f43c6be1cc9ea4d92130b8
  evidence_completion: 13ca8f0087d25baee6fabb92db2e5743dab0a3fa7874687531c85867ef7a5452
  acquisition_seal: 1f3512de1ae2e011e9614d5af3c1c1b2609ea6402b1b6666f9363f222b2b5f17
stale_if: Any listed input hash changes.
```

You are performing a read-only opposing-family adversarial artifact review for
Forseti.

```yaml
output_mode: paste-ready-chat
template_kind: adversarial-artifact-review
edit_permission: read-only
targets: the six exact hash-pinned files listed below
input_prompt_source: docs/prompts/reviews/summer_fridays_phase_a_decision_useful_coverage_adversarial_review_20260725_v1.md
review_response_destination: current review task chat
doctrine_change: none
preflight_defaults: docs/prompts/templates/shared/forseti_preflight_defaults_v0.md v0 - constants bound; deltas stated inline.
```

## Goal and success signal

Decide whether this completed Phase A gives a fresh downstream competitive-
intelligence or Problem-Framing consumer most of the major **unique**
decision-useful evidence bases needed to understand Summer Fridays.

Success is a forced coverage verdict, with artifact-and-line evidence, that
distinguishes a missing evidence family capable of changing a material
downstream decision from ordinary depth, freshness, precision, or confidence
residuals.

This review does not ask whether all discoverable evidence was captured. That
bar is impossible and would reward source volume rather than decision value.

## Binding and source sequence

1. Read `AGENTS.md`, `.agents/workflow-overlay/README.md`,
   `.agents/workflow-overlay/review-lanes.md` (Current Lanes, Review Doctrine,
   and Rules), and `.agents/workflow-overlay/communication-style.md` (review
   summary and Chief Architect consumption sections).
2. REFERENCE-LOAD `workflow-adversarial-artifact-review`; do not apply it yet.
3. Hash all six targets with SHA-256. On any mismatch, return
   `BLOCKED_INPUT_HASH_MISMATCH` and stop.
4. SOURCE-LOAD all six targets in full. Declare `SOURCE_CONTEXT_READY`, or
   `SOURCE_CONTEXT_INCOMPLETE` with the exact missing or unreadable file.
5. Only after source readiness, APPLY
   `workflow-adversarial-artifact-review` to this coverage question.

If the review skill is unavailable or cannot be applied after source
readiness, return advisory-only critique and do not emit a bound verdict.

## Exact review set

| Artifact | Exact repo-relative path | SHA-256 |
| --- | --- | --- |
| Integrated acquisition record | `docs/research/summer_fridays_understanding_dogfood_20260724_p06/coordinated/turn_a_acquisition_record.md` | `a86001897d32541fbcb60015085236c9398f988be387e7434c474739f787d7e9` |
| Company/high-yield core | `docs/research/summer_fridays_understanding_dogfood_20260724_p06/coordinated/specialists/co1_company_core_identity.md` | `6ed7095c9aaae60f4a647eba2f9841e70a0503d5890178ada0098bb982d32d10` |
| Retail portfolio | `docs/research/summer_fridays_understanding_dogfood_20260724_p06/coordinated/specialists/co2_retail_portfolio.md` | `b3418ea2a8cd904880f5b0216c4ffccfac95a6dbf2338267182828931ff105e8` |
| Customer/community depth | `docs/research/summer_fridays_understanding_dogfood_20260724_p06/coordinated/specialists/co3_customer_community_depth.md` | `33f1456b0c830830328a640aa5f07f18bcdd87d904f43c6be1cc9ea4d92130b8` |
| Evidence completion and whole-gate reconciliation | `docs/research/summer_fridays_understanding_dogfood_20260725_p07/evidence_layer_completion.md` | `13ca8f0087d25baee6fabb92db2e5743dab0a3fa7874687531c85867ef7a5452` |
| Acquisition seal | `docs/workflows/summer_fridays_understanding_dogfood_20260725_p07/acquisition_seal.md` | `1f3512de1ae2e011e9614d5af3c1c1b2609ea6402b1b6666f9363f222b2b5f17` |

## Artifact-only boundary

Use only these six files. Do not browse the public web, open raw capture lakes,
read run commissions or task transcripts, inspect VPN/ZIP/proxy state, compare
models or topology, or reconstruct retry chronology. Treat an external pointer
as `provenance_not_checked` unless its decisive semantics are reproduced in the
six-file set.

Do not score capture mechanics, route admissibility, parser behavior, seal
correctness, task count, compactness, token cost, or elapsed time as
independent dimensions. Mention one only when the artifact itself shows that it
materially limits what a downstream consumer can learn or do.

## Coverage test

Build a compact ledger for these decision-useful bases:

1. company identity, ownership, leadership, chronology, and material events;
2. bounded outside-in scale, traction, and channel or market position;
3. correct parent/family identity and portfolio/category/price/claims shape;
4. current official retailer authorization, channel expression, assortment,
   overlap, and material distribution gaps;
5. customer/community language, pain points, purchase drivers, objections,
   usage, workarounds, complaints, and response patterns;
6. category-balanced review/Q&A depth, provider/overlap ceilings, and what
   remains unknown;
7. product and category trajectory, including launches, expansion, historical
   incidents, reformulation, or trust-relevant change;
8. actionability, navigability, provenance transparency, and uncertainty for a
   fresh CI or Problem-Framing consumer.

For each base, distinguish:

- covered with decision-useful evidence;
- covered but materially thin or claim-bounded;
- missing as a unique material evidence family; or
- not determinable from the review set.

A gap is **material** only when the missing evidence family could plausibly
change a high-level company understanding, priority, risk, opportunity, or
Problem-Framing direction. More rows from an already represented family,
another retailer with duplicative information, ordinary freshness, or greater
precision alone is not a new unique base.

## Bound verdicts

Return exactly one:

- `MOST_MAJOR_UNIQUE_BASES_COVERED`: no omitted unique evidence family visible
  from the artifacts is likely to change the high-level downstream
  understanding; residuals are depth, freshness, precision, or confidence
  limits.
- `MATERIAL_DECISION_USEFUL_BASES_MISSING`: at least one omitted unique
  evidence family could plausibly change a high-level downstream decision or
  Problem-Framing direction.
- `INDETERMINATE`: the six artifacts do not permit either judgment.

The verdict is a coverage judgment only. It is not seal approval, readiness,
validation, proof of exhaustive research, or authorization to begin Turn B.

## Required output

Start with the compact Forseti `review_summary` YAML from
`.agents/workflow-overlay/communication-style.md`, using
`review_location: chat_only_current_thread`. Record the actual `reviewed_by`;
use `authored_by: unrecorded` unless exact author identity was supplied.
Record `de_correlation_bar: cross_vendor_discovery` only when the reviewer is
genuinely from a different upstream vendor family.

Then return:

1. `coverage_result`
   - `verdict`;
   - `confidence: high | medium | low`;
   - one-sentence decisive reason.
2. The eight-base coverage ledger with decisive `file:line` citations.
3. Findings-first material omissions, if any, with severity, confidence,
   evidence, impact, `minimum_closure_condition`, and
   `next_authorized_action`. Do not emit `patch_queue_entry`.
4. Thin-but-covered residuals that do not change the verdict.
5. `considered_and_defended`, including plausible missing-base candidates that
   the artifact set already covers or that fail the materiality test.
6. Provenance limitations and unperformed checks.
7. A one-line read-budget audit.
8. Review-use boundary: decision input only, not approval, validation,
   readiness, mandatory remediation, executor-ready authority, or Turn B
   authorization.

The answer must be self-contained and courier-ready. Do not edit files, write a
report, perform acquisition, or take Git lifecycle actions.
