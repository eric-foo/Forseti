---
artifact_type: phase_a_route_1_6_bounded_regression
authority: forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
status: completed_bounded_regression
current_as_of: 2026-08-08
scope: frozen 80-item Summer Fridays multi-source reaction-axis slice migrated through Route 1.6 interfaces and a two-level reconciliation hierarchy
---

# Phase A Route 1.6 Multi-Source Regression

## Purpose and boundary

This regression proves that Route 1.6 can migrate and recompile the existing
80-item Summer Fridays multi-source evidence slice while preserving its frozen
semantic judgments and adding truthful container, identity, prompt-bound, and
hierarchical accounting.

It is not the full Phase A corpus. In particular, its 50 Reddit leaves are one
previously selected candidate per captured conversation rather than all leaves
in those conversations. The source and view therefore carry
`bounded_regression_slice`; they are not seal-eligible as
`phase_a_final_acquisition`. The separately commissioned full Summer Fridays
shadow remains necessary before claiming full-corpus operation.

Authority and next source:

- Route behavior and non-claims:
  `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md`.
- Historical semantic ground truth:
  `../semantic_integration_multisource_dogfood_20260807_v0/`.
- Recheck by rebuilding the bundle, batch compilation, two reconciliation
  levels, and view through
  `forseti-harness/runners/run_semantic_evidence_integration.py`.

## Declared regression corpus

The v3 source contains 80 assessed leaves and 60 containers:

| Family | Leaves | Containers | Container meaning |
| --- | ---: | ---: | --- |
| Reddit/community | 50 | 50 | One selected leaf in each captured conversation |
| Sephora reviews | 9 | 9 | Each retailer review is its own container |
| TikTok creator post | 1 | 1 shared | Creator root in one creator/audience conversation |
| TikTok audience comments | 20 | same shared container | Twenty captured comments |

The TikTok envelope is 21 captured leaves—the creator root plus 20 comments—
out of 78 source-visible leaves—the root plus 77 comments. Its container is
therefore `partial`. Other selected-slice conversation limits remain explicit
instead of being restated as complete thread coverage.

All 80 selected leaves have one accounting row and one container. The compiled
coverage is:

- captured: 80;
- semantically assessed: 80;
- mechanically excluded: 0;
- blocked: 0;
- accounted: 80;
- complete within this bounded regression: true.

## Observed Route 1.6 run

The no-provider workflow used:

- `semantic_evidence_source_v3` and `semantic_evidence_bundle_v3`;
- two extraction prompts, 149,955 and 18,560 rendered UTF-8 bytes under a
  150,000-byte ceiling;
- `semantic_evidence_batch_response_v2`, preserving 44 claim-bearing, 14
  context-only, and 22 out-of-scope dispositions;
- 61 semantic units with first-hand/agreement/echo/question/speculation/
  strategy posture plus independent uncertainty posture;
- reconciliation response v2 across two levels;
- 17 terminal propositions, five unmerged units, and no emerging-axis
  candidates; and
- `semantic_evidence_integration_view_v2` with compiler-owned leaf and
  container indexes.

Hashes:

- corpus: `eb8d8c9920376fad0c8cd3fc263563b8537cc0d6290bf0e1a41a5703e3170f21`;
- bundle: `ddbfc2132f5b58ea796e42d06a47250f7f2edeb865f1dea4622b95f69aedd6cf`;
- batch compilation: `8e4a0c1371add9f9aede430152aa00d92a99610c729561291c11569d6a078e96`;
- level-one nodes: `d3652b1ed54829bb1e71f314991798e8fa6e145538e42226ba94f5b57190867e`;
- terminal nodes: `20f38f54e73e96815f49277623bfc78a77066b8afaa1fcd6615219c7c0d01554`;
- view: `07daa100b635175634dcfe7cafd0891b79056760597d39f262762376ffe21a27`.

Model-provider API calls: zero.

## Observed evidence-packet projection

The read-only `phase_a_evidence_packet_v1` projector was run against the
frozen bundle, batch compilation, and view. Selecting the real broad adverse-
reaction proposition `prop_00a4d685489ce45b4c1c` returned all 43 distinct
linked evidence items: 37 support and six counter, across 30 containers — the
support-plus-counter container union, not the 26 support containers counted
below — and three supporting source roles (`community_post`, `retailer_review`,
and `audience_comment`). Every linked semantic unit retains its posture,
uncertainty, and polarity. It also retained all five corpus unmerged meanings
as axis-relevant candidates; this slice has no no-axis unmerged meaning.
The packet reports `truncated: false`, makes zero model-provider API calls, and
has packet hash
`66240baff9af5b4ffb2cccf921e29e2e47a34a3ea50333667285519d8edbf24f`.

An axis-wide check for `reaction_and_breakout` selected all 17 propositions
and returned a 44-item de-duplicated union rather than adding the same source
again for every proposition. All 44 items participate in more than one
relation across those propositions, so the packet explicitly reports 44 mixed-
relation evidence items. This axis-wide output was a temporary verification
artifact; the proposition packet below is the durable dogfood.

The packet is evidence retrieval, not the answer: it contains the bounded
proposition as a label and preserves support, counter, adjacent, unmerged, and
unresolved lanes, but it emits no conclusion, recommendation, importance
ranking, prevalence estimate, or causal judgment.

## What truthful stacking added

The broad adverse-experience proposition retains the historical 38 supporting
semantic units from 37 evidence items and 37 independently credited origins.
Route 1.6 additionally shows that those observations occur in 26 containers:
17 Reddit conversations, eight retailer-review containers, and one TikTok
creator/audience conversation.

Other representative distinctions remain visible:

| Bounded point | Support evidence | Support containers | Credited origins |
| --- | ---: | ---: | ---: |
| Burning experience is mixed | 15 | 6 | 15 |
| Vanilla Beige adverse reports | 7 | 3 | 7 |
| Brown Sugar adverse reports | 3 | 1 | 3 |
| Explicit tolerance/no comparable reaction | 6 | 5 | 5 |

This is why “seven threads” and “seven people” are separate claims. The Brown
Sugar example has three visible audience accounts but one creator/audience
conversation container. The two historical `nessa_14` observations remain
separate evidence records but receive one origin credit.

## Partition sensitivity

`partition_sensitivity.json` compares two legal extraction partitions:

- 150,000-byte ceiling: batches of 71 and 9 leaves;
- 100,000-byte ceiling: batches of 45 and 35 leaves.

Their batch-membership hashes differ, while flattened proposition membership,
compiler-owned evidence stacks, claim-support blocks, and proposition IDs are
equal. This is a bounded live-subcorpus rollout measurement, not a standing
full-corpus double-run obligation and not proof of byte-identical open-world
agent judgment.

## Files

- `source.json` — v3 bounded-regression source with container registry.
- `bundle.json` — compiler-authored v3 bundle.
- `batch_responses.json` and `batch_compilation.json` — frozen agent meanings
  migrated to response v2 and compiler output.
- `reconciliation_stage_1.json`, `reconciliation_responses_1.json`, and
  `node_compilation_1.json` — nonterminal identity-preserving hierarchy level.
- `reconciliation_stage_2.json`, `reconciliation_response_2.json`, and
  `node_compilation_2.json` — terminal proposition level.
- `reconciliation_prompts_1.json` and `reconciliation_prompts_2.json` — exact
  rendered prompts with byte counts.
- `view.json` — compiler-authored view v2.
- `evidence_packet_prop_00a4d685489ce45b4c1c.json` — complete read-only
  support/counter stack for one real multi-source proposition.
- `partition_sensitivity.json` — bounded alternate-partition comparison.

## Non-claims

This regression is not complete Summer Fridays corpus coverage, evidence of
representative prevalence, a safety conclusion, causal proof, a market
conclusion, a recommendation, Deliver output, perfect semantic recall, or
proof that every public item was captured.
