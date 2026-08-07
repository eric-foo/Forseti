---
artifact_type: phase_a_semantic_integration_dogfood
authority: forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
status: completed_bounded_dogfood
current_as_of: 2026-08-07
scope: two admitted Summer Fridays Reddit evidence units; not a full-corpus conclusion
---

# Phase A Semantic Evidence Integration Dogfood

## Question

Can the Route 1.4 workflow read customer language by meaning, preserve every
distinct claim, and keep the exact compared product attached to the correct
axis without a model-provider API?

This is a bounded implementation dogfood, not a refreshed Summer Fridays
finding. It uses two already-captured Reddit comments to exercise the failure
mode that motivated the architecture. It does not claim to integrate the full
Summer Fridays corpus.

## Provenance

The admitted source artifact is
`docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/community_axis_coding.json`,
observed SHA-256
`fd2d9a57ce4a8474f2c3e785f7c3b8039bb39477722a4ee2eb03cc7e07093752`.

The two evidence aliases are:

- `reddit:1ft1w8d:lppwb5s`, source row `thread_id=1ft1w8d`,
  `comment_id=lppwb5s`, observed at source lines 9254-9269. Its single body
  says Summer Fridays smells good, is more comfortable than Ole Henriksen,
  lasts longer than Laneige Glowy, still disappears too quickly, and was
  formerly used habitually before the writer found better treatments.
- `reddit:1h0wfao:lz75gqx`, source row `thread_id=1h0wfao`,
  `comment_id=lz75gqx`, observed at source lines 10217-10229. Its body says
  Laneige is the writer's daily driver, has a liked texture, lasts longer than
  Summer Fridays, and contrasts that with frequent Summer Fridays
  reapplication.

The source does not expose public actor identity or engagement for these rows.
The dogfood therefore uses one shared unavailable-actor independence key and
gives neither row engagement credit. Two comments do not become two proven
independent customers.

## Observed run

The no-API file workflow completed all four stages:

1. `prepare-batches` admitted 2 evidence units into 1 batch, with bundle
   SHA-256
   `4e0472ecd789bfb2a5c6c059ec62aec1935ce2a3ba252db88b38dee52531bd95`
   and `model_api_calls: 0`.
2. The agent batch response split the 2 source bodies into 10 semantic units.
3. `submit-batches` produced compilation SHA-256
   `05c3a54daac059f88d6caf230fed532919fd572b0cd94171419a52a27af484ed`
   and `model_api_calls: 0`.
4. `finalize` accounted for 2 of 2 admitted units, emitted 8 propositions,
   and wrote view SHA-256
   `de847076a2374dd7ff1818dc1f65ba155cec9813fdce2ca51ecc2dd964b5154e`
   with `model_api_calls: 0`.

The durable inputs, agent judgments, and compiled result are `source.json`,
`batch_response.json`, `reconciliation_response.json`, and `view.json` in this
directory.

## Decisive result

The compiled view kept the comparisons separate:

- Summer Fridays comfort versus Ole Henriksen is one proposition on
  `texture_and_skin_finish`.
- Summer Fridays wear time versus Laneige is a different proposition on
  `wear_and_longevity`.
- The second captured comment opposes the first Laneige wear-time statement,
  so that proposition is `conflict_posture: mixed` rather than a directional
  advantage.
- No proposition says Summer Fridays lasts longer than Ole Henriksen.

It also retained meanings outside the initially targeted comparison: positive
Summer Fridays scent, insufficient Summer Fridays wear, liked Laneige texture,
habitual Laneige use, former habitual Summer Fridays use followed by an
unidentified replacement, and an unspecified lack of perceived benefit. The
last three are exposed as emerging axis candidates instead of being silently
discarded or forced into the provisional axes.

Every customer-experience and behavior proposition remains `isolated` with an
independent-origin count of 1. That is intentional: this dogfood proves
semantic coverage, product binding, and opposition handling; it does not prove
prevalence, independent recurrence, cross-venue corroboration, causation, or a
market conclusion.

## Reproduction boundary

The deterministic runner verifies source hashes, evidence accounting,
product/comparator bindings, source-role competence, counterevidence, and view
hashes. An agent still performs the meaning-based batch and reconciliation
judgments from the generated file prompts. The runner neither calls a model
provider nor pretends semantic judgment is deterministic software.

The full future-run obligation is larger than this dogfood: Route 1.4 must feed
the entire admitted claim-bearing Phase A corpus through the same accounting
contract before a new seal can pass.
