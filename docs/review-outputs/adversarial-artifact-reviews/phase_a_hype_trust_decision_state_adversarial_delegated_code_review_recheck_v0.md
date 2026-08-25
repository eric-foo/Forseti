---
retrieval_header_version: 1
artifact_role: Cross-vendor delegated adversarial code review-and-patch return for the sealed Phase A hype/trust Decision State implementation
scope: Findings-only recheck of the prior blocker, the recheck patch scope, and the compact Decision State reader at implementation revision d669777a
authority_boundary: retrieval_only
use_when:
  - Adjudicating whether the sealed hype/trust Decision State implementation may land, be patched, or route to an architecture pass.
  - Auditing which prior-blocker closure conditions were met at d669777a and which were not.
open_next:
  - .agents/workflow-overlay/delegated-review-patch.md
  - .agents/workflow-overlay/review-lanes.md
  - docs/workflows/phase_a_customer_evidence_completion_path_v0.md
  - forseti-harness/judgment/phase_a_evidence_axis_consolidation.py
  - forseti-harness/judgment/phase_a_evidence_selection.py
---

# Phase A hype/trust Decision State — adversarial delegated code review recheck

reviewed_by: Anthropic Claude Opus (controller)
authored_by: OpenAI Codex
controller_model_family: Anthropic
author_home_model_family: OpenAI
de_correlation_bar: cross_vendor_discovery
required_revision: `d669777ac1e42a0ff330c649f76bdeb37f6f300c`
reviewed_revision: `d669777ac1e42a0ff330c649f76bdeb37f6f300c`
courier_revision: `699bdeff7ac8a2bb31537b0f6018a47e57782541`
recheck_patch_diff: `3edaa585aaa87c7ef2e1fc78a01d4422ca6ec6b8..d669777ac1e42a0ff330c649f76bdeb37f6f300c`
implementation_diff: `e455231eecb82f47c5c1ec9acd3de29512e061be..d669777ac1e42a0ff330c649f76bdeb37f6f300c`
review_method: workflow-code-review
review_lane: delegated_code_review_and_patch
output_mode: filesystem-output
edit_permission: patch-only (not exercised)
review_use_boundary: >
  These findings, citations, and verdict are decision input only. They are not
  approval, not validation, not mandatory remediation, and not executor-ready
  patch authority. Nothing here was committed, pushed, merged, or published,
  and no frozen input or output was altered.

## Receiver binding and exact-revision preflight

Controller family is Anthropic; author home family is OpenAI. The lineages
differ, so the cross-vendor discovery bar is satisfied. No same-vendor, self,
no-repo, or context-pack substitute was used, and no second controller was
dispatched.

Direct repository access was exercised in the commissioned worktree
`C:\Users\vmon7\.codex\worktrees\phase-a-hype-trust-axis`. Observed at start:

- branch `codex/hype-trust-axis`;
- `git status --porcelain` empty (clean, satisfying `dirty_state_allowed_at_start: false`);
- `HEAD` = `699bdeff` — the later courier prompt commit named in the
  commission, whose only delta against `d669777a` is a rename plus edit of
  `docs/prompts/reviews/...adversarial_delegated_code_review_patch_prompt_v0.md`
  (1 file, +97/-53). The five patch-scope files are byte-identical at
  `699bdeff` and `d669777a`, so the `stale_if` condition did not fire and the
  reviewed bytes are the pinned implementation.

The prior report named at
`docs/review-outputs/adversarial-artifact-reviews/phase_a_hype_trust_decision_state_delegated_code_review_v0.md`
is **not present in the repository** at this revision. The prior blocker and
adjudication were therefore taken only from the commission text, and no
independent reading of the prior findings was possible. This is a named source
gap, not a silent substitution.

`workflow-code-review` was invoked and is the review method for this lane.

## Verdict

**`NEEDS_ARCHITECTURE_PASS`.** No patch was authored and no partial edits
exist; `git diff --check` exits 0 and the worktree carries only this report.

Two of the four material findings are design-level rather than patch-level.
F1 cannot be closed by a bounded patch because the projector's only tie to
captured reality — `load_selection_sources` — is stubbed to `[]` in every
projector unit test, so the substrate a truthful fix would need does not exist
in the touched scope. F2 cannot be closed without re-introducing an
independent anchor into the compact reader, which is the design decision this
patch deliberately removed. F4 is closable in one line but the closure
invalidates the frozen final compact views the commission pins as evidence, so
it is an owner decision, not a delegate edit. Under the commission's escalation
clause the honest return is findings only.

The recheck patch is a real improvement on the prior revision. Closure items 2
and 5 are met, and item 3 is partially met. Items 1 and 4 are not met.

## Prior-blocker closure recheck

| # | Closure condition | Status |
| --- | --- | --- |
| 1 | Made-up / altered / sibling / wrong-source / spec-authored parent must fail before projection | **Not met** — only the spec-authored form fails (F1) |
| 2 | Legacy quote prompting must not receive parent text; quotes stay literal child text | **Met** |
| 3 | Every semantic row handle identity-bound to the exact selected evidence row | **Not met for semantic handles** (F2); met for evidence, quote, parent-context handles |
| 4 | Parent context must not silently lend source role, date, engagement, or customer/creator status | **Met in contract wording; partially met in mechanism** (m6) |
| 5 | Exact per-point hype meanings survive without a speculative cross-axis hype enum | **Met** |

## Findings

### F1 — `[projector]` Parent context is never re-derived from the verified bundle, so the artifact remains an authorable parent surface

- severity: major
- confidence: high
- location: `forseti-harness/judgment/phase_a_evidence_axis_consolidation.py:341` (`_validated_candidate_parent_contexts`), `:468-481`, `:558-564`, `:2851-2857`

Evidence. `_validated_candidate_parent_contexts` reads `candidate["parent_context"]`
and validates **shape only**: list-ness, the exact field set
`{context_id, source_ref, text}`, non-empty strings, and no duplicate
`context_id`. It performs no comparison against any upstream source.

`_validate_point_binding` loads and verifies the cold sources at lines 468-481
(`load_selection_sources`, `_verify_packet`, `_verify_bundle`, and the
packet↔bundle binding), then never reads `sources` again — a grep for
`sources|packet|bundle` across lines 380-700 of that file returns no further
occurrence. The verified bundle carries
`semantic_work_unit_projection.context_registry` plus each evidence unit's
`parent_context_refs`, and the selector already resolves exactly that in
`phase_a_evidence_selection.py:1248` (`_resolved_parent_context`), including
the `source_artifact_id` equality check that prevents a sibling-thread parent.
The projector reuses none of it.

The consequence is demonstrated by the repository's own new test.
`forseti-harness/tests/unit/test_phase_a_evidence_axis_consolidation.py:1737`
(`test_reader_evidence_row_handle_rejects_a_wrong_exact_join`) writes
fabricated `parent_context` entries into `artifact["candidate_dispositions"]`,
re-pins `point["artifact_sha256"]`, rehashes the manifest, rebuilds the axis
pack, and re-pins `spec["source_axis_pack_sha256"]` — and
`build_axis_consolidated_view` accepts them, producing two rows in
`parent_context_table` (asserted at line 1764). The projector fixture supplies
no `context_registry` and no `parent_context_refs` at all, so those parents are
provably absent from any bundle. A made-up parent projects.

The chain that would have caught it does not close. `artifact["candidate_inventory_sha256"]`
is compared only to the selection manifest's copy of the same scalar
(line 434); it is never recomputed from `candidate_dispositions`. The
tamper-evident `quote_manifest["labeled_inventory_sha256"]` is never compared
against `artifact["candidate_dispositions"]` — a grep for `labeled_inventory`
in the projector returns nothing. The only pin over the parent text is
`descriptor["artifact_sha256"]`, which the spec supplies.

The closure is achievable and cheap. This reviewer re-resolved every frozen
candidate against its hash-verified bundle using the selector's own
`_parent_context_indexes` / `_resolved_parent_context` / `_expand_packet`
over all five frozen point directories under
`C:\tmp\forseti-phase-a-hype-trust-exposure-bound-20260825-v2`:

```text
total 2145  with_stored_context 12  mismatches 0
```

Under the rule "a candidate's stored `parent_context` must be empty or exactly
the bundle-derived resolution", all 2,145 frozen candidate dispositions pass,
and all 12 that carry parent context re-derive byte-exact. The rule is
therefore compatible with the frozen axis. (Strict equality without the
empty allowance fails for 1,683 candidates, because
`phase_a_evidence_selection.py:1520` attaches parent context only when the
candidate is `explicitly_admitted`.)

Why this is not patchable here. Adding the cross-check to
`_validate_point_binding` is a small edit, but it cannot be proven inside the
touched scope: `_fixture` at
`test_phase_a_evidence_axis_consolidation.py:179-182` monkeypatches
`judgment.phase_a_evidence_axis_consolidation.load_selection_sources` to return
`[]` for every projector unit test. A check gated on non-empty `sources` would
be a no-op in the entire projector suite — a fail-silent path — and proving it
would require authoring a real packet+bundle fixture that satisfies
`_verify_packet`, `_verify_bundle`, the `source_bindings.bundle_sha256`
linkage, and the context registry. That is fixture-substrate architecture, not
a bounded patch.

- authority basis: commission closure item 1; `docs/workflows/phase_a_customer_evidence_completion_path_v0.md` ("The projector derives it only from the hash-pinned candidate disposition"); the reader `quote_role` contract at `phase_a_evidence_axis_consolidation.py:137-141`.
- impact: the prior blocker's stated failure mode is relocated, not eliminated. A parent prompt with no counterpart in the captured corpus, or the right text against the wrong `source_ref`, still reaches the cold reader labelled as exact provenance-bound context.
- minimum_closure_condition: for every displayed decision-state row, the projector rejects any candidate `parent_context` that is neither empty nor byte-identical to the resolution derived from the packet/bundle it already verifies, and that rejection is exercised by a test whose fixture supplies real verified sources rather than a stubbed `load_selection_sources`.
- next_authorized_action: owner decision on whether the point artifact is trusted-by-pin or must be re-derived, and on funding a real source-binding fixture for the projector suite. No patch authorized by this pass.
- verification expectation: red-green is available once the fixture exists — a fabricated `parent_context` must raise at `decision_state_parent_context_binding` before the fix is claimed closed. Not run here; no fixture.
- patch_queue_entry: not authorized (escalated).

### F2 — `[projector]` `context_only_semantic_unit_row_ids` is self-asserting and is the sole authority for the relation-semantic membership check

- severity: major
- confidence: high
- location: `forseti-harness/judgment/phase_a_evidence_axis_consolidation.py:1587` (`valid_row_ids` shape check), `:1771-1791` (`context_only_semantic_row_ids` checked for shape only), `:1793` (`available_semantic_row_ids` seeded from that same field), `:1833-1840` (the membership assertion); and `:2123-2133`, `:2169` (`placement_table` removal)

Evidence. The new validator seeds the allowed semantic set from the row's own
`context_only_semantic_unit_row_ids`, then unions the semantic refs of the
state rows that row points at, then asserts
`set(relation_semantic_row_ids) <= available_semantic_row_ids`.
`context_only_semantic_unit_row_ids` itself is checked only for shape by
`valid_row_ids` (in-range, non-bool ints, no duplicates). Nothing binds it to
the evidence row it sits on. In the same patch, `placement_table` — which
carried `semantic_unit_ref` and `companion_semantic_unit_refs` per
`(point_id, selected_id)` and was the reader's only independent anchor for
semantic ownership — was removed.

Empirically reproduced against the repository fixture:

```text
semantic rows: ['reddit:thread1:comment1::dry', 'reddit:thread1:post::hydrating',
                'reddit:thread1:post::texture', 'retailer:sephora:review1::dry']
fact selected_02 reddit:thread1:comment1 rel [0] ctx []
fact selected_01 reddit:thread1:post     rel [1] ctx []
attaching semantic row 1 ( reddit:thread1:post::hydrating ) owned by selected_01
  onto selected_02 / reddit:thread1:comment1
VALIDATION PASSED -- foreign meaning accepted on the wrong evidence row
```

Setting `selected_02`'s `relation_semantic_unit_row_ids` and
`context_only_semantic_unit_row_ids` both to the semantic row owned by
`selected_01` — a different evidence row, different origin, opposite relation —
passes `_validate_decision_state_reader_evidence_rows` without error. The
validator's allowed set is derived from the field the attacker moved.

The existing test at
`test_phase_a_evidence_axis_consolidation.py:1827-1848` mutates only
`relation_semantic_unit_row_ids` while holding `context_only_...` fixed, and
computes its "wrong" row id from the same allowed set the validator uses. It
therefore exercises the guard exactly where it holds and never where it fails.
No test mutates `context_only_semantic_unit_row_ids`, `relation_state_row_ids`,
or `source_context_state_row_ids`.

- authority basis: commission closure item 3 and required attack 5 ("Mutate every direct reader row ID to a plausible in-range row owned by another selected item. Confirm evidence, quote, semantic, state, and parent-context mismatches fail at `decision_state_reader_evidence_binding`."); commission fitness reference ("row handles with exact identity rechecks").
- impact: the evidence and quote handles are genuinely identity-bound (`evidence_id` and `quote_span_id` recheck), and the parent-context handles are too. The semantic handles are not. A compact reader shipped standalone — which the dogfood comparison treats as the delivered product — cannot detect a meaning moved from one selected evidence row to another. That is the "traceable, compact output that looks exact" false green named in the commission's fitness reference, applied to meaning rather than to hype polarity.
- minimum_closure_condition: a semantic row handle on a relation fact is rejected when it does not belong to that selected row's own primary-plus-companion meaning set, judged against something the relation fact does not itself assert, and a mutation of `context_only_semantic_unit_row_ids` alone is proven to fail.
- next_authorized_action: architecture decision on where the compact reader's semantic-ownership anchor lives now that `placement_table` is gone — a restored minimal per-row anchor, a per-row checksum, or an explicit accepted residual recorded on the reader contract. No patch authorized by this pass.
- verification expectation: red-green available — the probe above must raise at `decision_state_reader_evidence_binding` after the fix. Not run against a fix; none authored.
- patch_queue_entry: not authorized (escalated).

### F3 — `[projector]` `[projector-tests]` The compact reader's accounting contract is an unbound hand-maintained fork, and its only test is tautological

- severity: major
- confidence: high
- location: `forseti-harness/judgment/phase_a_evidence_axis_consolidation.py:244-271`, `:2179`; `forseti-harness/tests/unit/test_phase_a_evidence_axis_consolidation.py:833-836`, `:888-892`

Evidence. The reader's `evidence_accounting_contract` was
`copy.deepcopy(view["evidence_accounting_contract"])` — derived from the
authoritative `EVIDENCE_ACCOUNTING_CONTRACT`. It is now
`_reader_evidence_accounting_contract()`, a standalone literal. A grep across
`forseti-harness/` shows the two are never related to each other in production
code or in any test: `EVIDENCE_ACCOUNTING_CONTRACT` appears at `:64`, `:3104`,
and test `:829`; `_reader_evidence_accounting_contract` at `:244`, `:2179`,
and tests `:836`, `:888`. No key-set parity check exists anywhere.

The test that previously bound them,
`assert reader["evidence_accounting_contract"] == EVIDENCE_ACCOUNTING_CONTRACT`,
was replaced by
`assert reader["evidence_accounting_contract"] == _reader_evidence_accounting_contract()`.
Since line 2179 builds the reader field *from* that function, the assertion
compares the function to itself and cannot fail for any edit to either
contract. The sibling assertion at `:888-892` has the same shape.

Contrast `_decision_state_reader_contract` at `:234-241`, which deep-copies the
authoritative contract and applies a named override dict — a form that
propagates by construction. The accounting contract did not receive that
treatment.

The two dicts happen to agree on all six keys today, so no rule is currently
missing. The defect is the absent binding: adding, renaming, or strengthening a
rule in `EVIDENCE_ACCOUNTING_CONTRACT` would silently leave the compact reader
short, and no test would fail.

- authority basis: `docs/workflows/phase_a_customer_evidence_completion_path_v0.md` ("The compact Decision State reader carries the same six accounting rules in shorter reader-native wording; this is wording compaction, not a weaker rule") — an unenforced claim; commission fitness reference ("one displayed evidence row, one origin, and two observations from that same origin remain three different counts").
- impact: the counting rules the cold reader is handed can silently diverge from the authoritative rules, and the test suite is structurally incapable of detecting it.
- minimum_closure_condition: the compact accounting contract's key set is mechanically tied to `EVIDENCE_ACCOUNTING_CONTRACT`, and adding a key to the authoritative contract fails a named check.
- next_authorized_action: owner may authorize a bounded patch adding a key-parity assertion in `[projector-tests]`; this pass is escalated and did not author it.
- verification expectation: red-green is straightforward — add a seventh key to `EVIDENCE_ACCOUNTING_CONTRACT`, confirm the parity check fails, revert. Not run; no patch authorized after escalation.
- patch_queue_entry: not authorized (escalated).

### F4 — `[projector]` The reader surface shape changed incompatibly while keeping `schema_version: ..._v2`

- severity: major
- confidence: high
- location: `forseti-harness/judgment/phase_a_evidence_axis_consolidation.py:2163`

Evidence. Across revisions the constant reads:

```text
e455231e -> phase_a_evidence_decision_state_reader_surface_v1
3edaa585 -> phase_a_evidence_decision_state_reader_surface_v2
d669777a -> phase_a_evidence_decision_state_reader_surface_v2
```

Between `3edaa585` and `d669777a` the surface lost the top-level
`placement_table`, gained two `relation_facts` columns (`layer`,
`context_only_semantic_unit_row_ids`), and replaced
`evidence_accounting_contract` — all while the version string held at `v2`.

This is not hypothetical. Inside the single frozen evidence directory
`C:\tmp\forseti-phase-a-hype-trust-exposure-bound-20260825-v2`, both shapes are
on disk and both self-declare `..._v2`:

```text
post_review_validation\consolidated_view_1..6.json   v2  placement_table=True   context_only_col=False
post_review_validation\consolidated_view_7.json      v2  placement_table=False  context_only_col=True
post_review_validation\consolidated_view_8.json      v2  placement_table=False  context_only_col=True
consolidated_view_postfix2_1.json                    v2  placement_table=True   context_only_col=False
consolidated_view_postfix2_2.json                    v2  placement_table=True   context_only_col=False
```

Views 7 and 8 are the commission's cited final compact views
(raw SHA-256 `2b11bc38…`, confirmed by this reviewer). Views 1-6 and the
`postfix2` pair sit in the same evidence set under the same version label with
an incompatible shape. A consumer keying off `schema_version` cannot
distinguish them.

- authority basis: commission fitness reference (compact reader as the delivered cold-reader surface); evidence set named in "Evidence To Confirm, Not Trust".
- impact: `schema_version` stops being a usable discriminator for the compact reader within the very evidence set the landing decision rests on.
- minimum_closure_condition: the current compact reader shape carries a version string that no earlier-shaped artifact claims, or the earlier-shaped artifacts in the frozen evidence set are explicitly marked superseded on the durable record.
- next_authorized_action: owner decision. A bump to `..._v3` is a one-line edit but changes the emitted bytes, so it invalidates the frozen `consolidated_view_7/8` hashes (`2b11bc38…` raw, `a73fdc08…` logical) and the dogfood receipt `e6d511ac…`. That trade is the owner's, not the delegate's; no patch was authored.
- verification expectation: after any bump, the frozen compact-view and receipt hashes must be recomputed and the commission's evidence block re-stated. Not run.
- patch_queue_entry: not authorized (escalated; frozen-output impact).

### Minor findings

- **m1** `[projector]` The displayed row's *own* primary meaning is no longer distinguishable from a same-evidence companion meaning in the compact reader. `placement_table` carried `semantic_unit_ref` and `companion_semantic_unit_refs`; the replacement exposes only the union across `relation_semantic_unit_row_ids`, `context_only_semantic_unit_row_ids`, and the state rows. Meanings are recoverable as a set, not as "this row's meaning versus what else that source said". Severity minor, confidence medium. Closure: the compact reader marks or derives the placement's primary meaning, or the reader contract states plainly that it does not. (`:1935-1971`, `:2066-2073`)
- **m2** `[projector]` `DECISION_STATE_CONSUMER_CONTRACT["qualification_rule"]` at `:151-156` still instructs the consumer to "resolve every qualification_ref through placement_table semantic_unit_ref". No artifact named `placement_table` now exists anywhere — the full view exposes `point_placements`, and the reader table was removed by this patch. The reader override at `:172-177` replaces it for the reader only; the full-view contract is left stale. Severity minor, confidence high. Pre-existing string, now fully stale.
- **m3** `[projector-tests]` `test_context_only_qualification_refs_resolve_through_primary_or_companion` asserts `"placement_table" in rule` at `:1997`, pinning the stale vocabulary in m2 in place. A test that locks a wrong contract string will resist its own correction. Severity minor, confidence high.
- **m4** `[projector]` `placement_processing_rule` (`:125-128`, "process every placement exactly once") and `context_only_row_rule` (`:146-150`, "for that placement") reach the compact reader unmodified by `DECISION_STATE_READER_CONTRACT_OVERRIDES`, while the reader's own `consumer_join_order` was rewritten to "process each selected_id exactly once". The compact reader is handed two vocabularies, one of which names nothing it exposes. Severity minor, confidence high.
- **m5** `[projector-tests]` `_fixture` monkeypatches `load_selection_sources` to return `[]` (`:175-182`), so `_verify_packet`, `_verify_bundle`, and the packet↔bundle binding at `:468-481` have zero unit coverage in the projector suite. This is pre-existing, but the recheck patch made it load-bearing: it moved parent-context authority onto the candidate path whose only reality anchor runs through that unexercised code. Severity minor as a standalone, but it is the blocking substrate for F1's closure. Confidence high.
- **m6** `[projector]` `_validated_candidate_parent_contexts` returns `[]` when the candidate carries no `parent_context` key at all — the shape produced when `parent_context_policy != linked_parent_context_v1`. The reader contract states that empty `parent_context_ids` arrays "mean the literal quote is self-contained" (`:183`). Nothing verifies that affirmative claim; absence of a key becomes a positive assertion of self-containment. Severity minor, confidence medium. Closure item 4 is met in the contract wording (source role and date declared unavailable, venue and surface recoverable from `source_ref`) but the self-containment claim is unbacked.

## considered_and_defended

- **Removed `body is None` raise in `_quote_prompt_envelope`** (`phase_a_evidence_selection.py:3413-3417`, deleted). Candidate: a fail-loud guard was traded for a silent `null` body in the quote prompt. Defense held: `provider_rows` already excludes every row whose body is `None` (`:3396`), and `_project_parent_context` copies each row and pops one key without touching `source_id` or `evidence_id`, so the guard was unreachable. Dead-guard removal, not a fail-silent path.
- **`RELATION_CONFIRMATION_PROMPT` still receives parent context and gets no `policy_guidance`** (`:4359-4364`). Candidate: parent text leaking into a non-context-aware prompt, and the hype/scope policies missing from a relation decision. Defense held: that prompt's own instruction text (`:231`) is explicitly context-aware, and the route is gated to `QUOTE_MANIFEST_VERSION` (v6) while every frozen point manifest is the v8 preselection-confirmed route. The function is untouched by this patch. Off-scope flag rather than a finding.
- **No deterministic hype `reason_code` → relation lane.** Candidate: the value axis enforces `VALUE_REASON_RELATIONS` in code (`:3290-3301`), so a model returning `support` with reason code `overhyped_but_loved` would be rejected there but accepted on the hype axis, where the only enforcement is `HYPE_EXPECTATION_RELATION_GUIDANCE` prose. Defense held: commission closure item 5 explicitly forbids "forcing a speculative cross-axis hype enum". Owner-adjudicated. Named residual below.
- **`placements.append(placement)` moved above the decision-state block** (`:2842-2843`). Candidate: a placement now enters the list before its state binding is validated. Defense held: `placements` holds a reference and the later `placement["parent_contexts"] = …` mutation is visible; every intervening failure raises rather than continuing. No semantic change.
- **Reader state partition could under-approximate the allowed semantic set.** Candidate: `relation_state_row_ids` and `source_context_state_row_ids` might omit some of the row's states, causing a false failure on a legitimate view. Defense held: `:2080-2091` partitions the complete `row["state_ids"]` on whether the state's refs intersect the relation refs, so the union is exhaustive, and `_decision_state_group:1350` forces `asserted_refs | context_ref_set == available_refs`. No false failure.
- **Legacy quote route parent-text gate** (closure item 2). Attacked and held: `include_parent_context=context_complete_quotes` (`:3569`) makes `context_aware` false on the legacy route, so `CONTEXT_QUOTE_PROMPT_COLUMNS` and `_attach_parent_context_envelope` are both skipped; `LEGACY_QUOTE_PROMPT` (`:213-219`) carries no parent-context instruction, and `QUOTE_PROMPT` (`:223`) forbids copying parent text into `exact_quote`. The new selector test asserts the parent text, `parent_context_rows`, and `parent_context_ids` are all absent from the legacy prompt.
- **Round-trip and idempotency after the schema change** (attack 7). Attacked and held: `_decision_state_bindings` now rejects any row key set other than the exact required fields (`:1113-1118`), `_bindings_from_decision_state_groups` no longer emits `parent_contexts` (`:1464-1469` deleted), and `_expand_compact_decision_state_groups` pins the exact compact group key set. The rebuild path and the binding validator agree; the suite passes.
- **Decision-object scope guidance breadth** (attack 3). Attacked and held: `DECISION_OBJECT_SCOPE_RELATION_GUIDANCE` is unconditional in `_policy_guidance` (`:985`), matching the workflow doc's new axis-wide statement. The two renamed selector tests
  (`test_hype_policy_guidance_forbids_…`, `test_relation_guidance_says_…`) are an honest correction: they assert prompt-string content and their new names no longer claim behavioural enforcement.
- **`layer` added to `relation_facts`** (attack 8). Checked as a genuine improvement: the compact reader can now distinguish `influence_context` from `truth_support` per displayed row without the placement table, so creator material stays visibly creator material. Combined with `evidence_table` carrying `source_role`, `source_venue`, `content_surface`, `publication_time`, and the five engagement columns, and per-point `candidate_inventory_sha256` for hash lineage, attack 6's recovery list holds except for m1.

## Validation evidence and not-run checks

Run against the pinned revision as an unpatched baseline, in the commissioned
worktree:

```text
python -m pytest -p no:cacheprovider -q \
  forseti-harness/tests/unit/test_phase_a_evidence_axis_consolidation.py \
  forseti-harness/tests/unit/test_phase_a_evidence_selection.py
  -> 252 passed

python .agents/hooks/check_harness_coupling.py --strict
  -> 18 passed; GATE PASS harness coupling contracts

git diff --check
  -> exit 0
```

Independently recomputed from the commission's "Evidence To Confirm, Not
Trust" block:

```text
2b11bc38c866d86adf1336217078604002262498cb46a48cc907b747b2ffa714  consolidated_view_7.json
2b11bc38c866d86adf1336217078604002262498cb46a48cc907b747b2ffa714  consolidated_view_8.json
e6d511ac467d278b79b50e37d7c00c888f20bd16df540a0ad932952a8abe2b11  final_receipt.json
```

All three match the commission. The frozen packet, bundle, and axis-pack raw
hashes were not independently recomputed; their paths are not named in the
commission and were not resolved. That is a not-proven boundary, not a
confirmation.

Not run, with cause:

- `check_retrieval_header.py --changed --strict`, `check_placement.py --changed --strict --base origin/main`, and `check_prompt_output_mode.py --strict --base origin/main` are post-patch gates over changed paths. No patch was authored, so they had no patch to check; the only changed path is this report, and its provenance gate is reported in the final chat closeout.
- No red-green proof accompanies F1, F2, F3, or F4, because escalation forbade authoring the fixes. Each finding states the red-green shape its closure would need.
- The dogfood token and tie/win figures, the 46-tie comparison result, and the two disclosed mirror drifts were read as commission claims and not re-derived.

## Residual risk

- The escalation leaves four major findings open. The recheck patch is a net
  improvement over `3edaa585` on closure items 2, 3 (partially), and 5, and
  landing it is defensible if the owner accepts F1, F2, and F4 as named
  residuals rather than blockers.
- F1's severity depends entirely on whether the point artifact is treated as a
  trusted pipeline output pinned by a spec-supplied hash. If it is, the finding
  reduces to "parent context is exactly as trusted as evidence text, quotes,
  meanings, and engagement, all of which come from the same artifact without
  bundle re-derivation" — a consistent trust model, and the accepted
  pre-review residual already says parent context is context, not evidence.
  If the prior blocker's phrase "must fail before projection" was meant
  literally, it is not met. That reading is the owner's to settle.
- The hype/trust semantic boundaries between "overhyped", "did not live up to
  hype", "worth the hype", and "love despite going viral" are enforced only by
  prompt prose, with no deterministic code guard. This is owner-adjudicated
  (closure item 5) and was not treated as a finding, but the highest-loss false
  green named in the commission's fitness reference remains structurally
  unguarded in code.
- Two of the compact reader's contract entries (m2, m4) and one test (m3) still
  speak a placement vocabulary the reader no longer exposes. None of these
  change emitted data.
- This reviewer read the prior report only through the commission's summary of
  it. If the prior report's blocker text differs from that summary, the closure
  table above should be re-checked against the original.

## Blockers, off-scope flags, and not-proven boundaries

- Blocker to a bounded patch: the projector unit fixture stubs
  `load_selection_sources` to `[]`, so no source-binding behaviour can be
  proven inside the touched scope (m5, F1).
- Off-scope and flag-only: `prepare_selected_relation_confirmation` and
  `RELATION_CONFIRMATION_PROMPT` receive no policy guidance; the full-view
  `qualification_rule` string; the absence of a hype reason-code lane. None
  were patched.
- Not proven: the frozen packet, bundle, and axis-pack hashes; the dogfood
  comparison figures; that the frozen axis would still build unchanged under
  any of the closures proposed above, except F1's, for which the 0/2145
  re-derivation result is stated.
- No file in the repository was modified by this review other than this report.
  Nothing was committed, pushed, merged, or published, and no frozen artifact
  was altered.
