# Phase A Customer-Pull Frontier And Preselection Relation Delegated Code Review-And-Patch v0

```yaml
retrieval_header_version: 1
artifact_role: Forseti delegated review output
scope: Cross-vendor delegated adversarial code review-and-patch of the retailer-first Phase A point frontier and v7 preselection relation confirmation at 74865c03d44c55d2c1e3c125461c757c3f5c414e.
use_when:
  - Adjudicating the delegated return for the Phase A customer-pull frontier and v7 point-pack implementation.
  - Checking which commissioned attacks landed, which were defended, and what remains unpatched.
authority_boundary: retrieval_only
stale_if:
  - The five exact targets change after this review.
  - The owning claim-support, semantic-integration, or delegated-review authority changes.
```

## Provenance

```yaml
reviewed_by: claude-opus-5
authored_by: unrecorded
authored_by_note: >
  The commission records author_home_model_family OpenAI. The exact authoring
  model and version were not supplied, so the value stays unrecorded rather
  than fabricated. This records a measurement gap, not a captured measurement.
de_correlation_bar: cross_vendor_discovery
controller_model_family: Anthropic
author_home_model_family: OpenAI
current_receiving_actor_role: controller
dispatch_mode: external-controller-courier
mode: base-subagent
access: repo
review_lane: >
  mixed - workflow-code-review for the three Python targets,
  workflow-adversarial-artifact-review for the two owning documents.
  Both skills were invoked before findings were written.
target_revision: 74865c03d44c55d2c1e3c125461c757c3f5c414e
reviewed_diff: 53676d7a6902b876590ddbbd6b10434ae59dee91..74865c03d44c55d2c1e3c125461c757c3f5c414e
reviewer_worktree: C:/tmp/phase-a-rev-74865c03 (detached at the target revision, clean at checkout)
comparison_worktree: C:/tmp/phase-a-rev-parent (detached at the parent revision, used for the v6 reproduction differential)
edit_permission: patch-only, bounded to the five named targets, uncommitted
review_use_boundary: >
  These findings, citations, and the uncommitted diff are decision input for
  the commissioning Chief Architect. They are not approval, not validation,
  not readiness, not mandatory remediation, and not executor-ready patch
  authority. Nothing here is accepted, ready, or mergeable until the home/CA
  adjudicates each change and reverts what it rejects.
```

## Lane Preflight

- Trigger gate: satisfied. The commission explicitly names both lanes and binds a
  `delegated_code_review_and_patch` target kind.
- Lane collision: declared by the commission (mixed lane, Python to code review,
  the two documents to adversarial artifact review). No undeclared collision.
- Write boundary: the artifact-review lane is source-read-only by default. That
  default is overridden here by
  `.agents/workflow-overlay/delegated-review-patch.md`, which states this is a
  commissioned bounded-executor lane, not one of the source-read-only review
  lanes, and that patch authority comes from the commission as accepted scope.
  The two documents are named exact targets, so the doc edits below are inside
  that scope.
- Output mode: `filesystem-output`, `required_output_path` supplied by the
  commission.
- De-correlation: the author family is OpenAI, the controller is Anthropic, so
  the cross-vendor discovery bar is met. No same-vendor or self substitution was
  used, and no replacement controller was launched.

## Source-Read Ledger

| Source | Why read | Status |
| --- | --- | --- |
| `AGENTS.md` | Kernel behavior and Smallest Complete Intervention | clean @ target |
| `.agents/workflow-overlay/README.md` | Overlay entry and binding rule | clean @ target |
| `.agents/workflow-overlay/review-lanes.md` | Lane definitions, provenance fields, two-bar de-correlation | clean @ target |
| `.agents/workflow-overlay/delegated-review-patch.md` | Commission semantics, code-diff target kind, finalization gate | clean @ target |
| `forseti-harness/judgment/phase_a_evidence_selection.py` | Primary review target | clean at checkout, patched by this review |
| `forseti-harness/runners/run_semantic_evidence_integration.py` | Runner target | clean, unpatched |
| `forseti-harness/tests/unit/test_phase_a_evidence_selection.py` | Test target | clean at checkout, patched by this review |
| `forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md` | Contract target | clean at checkout, patched by this review |
| `docs/workflows/phase_a_customer_evidence_completion_path_v0.md` | Workflow target | clean at checkout, patched by this review |

## Verdict

`MATERIAL_FALSE_GREEN_FOUND_AND_PATCHED_IN_SCOPE` with three unpatched findings
routed to the home/CA. No design-level problem was found, so
`NEEDS_ARCHITECTURE_PASS` was not returned and no partial patch is quarantined.

Per-target sub-verdicts, where materially different:

- `[selection-runtime]`: one critical false green found and patched; three
  further findings reported and deliberately not patched.
- `[selection-runner]`: no finding. Every commissioned runner attack was
  defended.
- `[selection-tests]`: one coverage gap; the minimum missing falsifier was added
  inside this file only.
- `[semantic-contract]` and `[phase-a-workflow]`: one shared behavioral-claim
  defect found and patched in both.

## Findings

### CR-01 — critical — confidence high — `[selection-runtime]` — PATCHED

**Location.** `forseti-harness/judgment/phase_a_evidence_selection.py`, the
confirmation loop inside
`finalize_preselection_relation_confirmation_prepare_quotes`
(`for candidate_id, check in zip(expected_manifest["confirmation_candidate_ids"], checks, strict=True)`).

**Defect.** The v7 confirmation response overwrites each row's first-pass
`relation` and `reason_code`, but the loop re-implements only a subset of the
per-row guards that `_validate_relation_response` applies to the first pass.
Three first-pass guards were absent from the confirmation path: the
creator-to-customer laundering guard, the internal-relation-word reason-code
guard, and the 80-character reason-code bound. Because the confirmed label
*replaces* the first-pass label, a guard applied only on the first pass is not
applied at all.

**Why this is the highest-loss variant.** Every influence row is placed in the
confirmation frontier unconditionally by `_preselection_confirmation_candidates`
(`row.get("layer") == "influence_context"`). So the laundering escape is not a
corner case: on every v7 pack, every creator-authored row is presented to the
confirming workload with an opaque handle, and a returned `support` was
accepted.

**Evidence — observed, not inferred.** Against the unpatched target revision,
with the repository's own `_write_source(tmp_path, 20)` fixture, 20 admitted
candidates, 16 confirmation rows, 4 of them influence rows:

```text
influence rows in confirmation frontier: 4
[ACCEPTED] P1 creator_authored confirmed as 'support': creator row relation in labeled_inventory=['support'], artifact disposition=[('influence_context', 'support')]
[BLOCKED ] P1b creator_authored 'support' on FIRST pass: boundary=creator_customer_laundering
```

The identical label is rejected on the first pass and accepted at confirmation,
and it reaches the durable artifact's `candidate_dispositions`.

For the reason-code guards, a confirmed row that is not among the displayed
rows escapes both checks, because `_display_label` — the only downstream guard
that catches them — is called on selected rows only (three call sites, all on
selected or displayed rows):

```text
confirmed rows: 16, displayed: 15, confirmed-but-not-displayed: 1
[ACCEPTED] relation-word leak 'adjacent_to_the_claim' on non-displayed row -> artifact reason_code=['adjacent_to_the_claim']
[ACCEPTED] over-long 151-char reason code on non-displayed row -> artifact reason_code=['a_bcde_bcde_bcde_... (151 chars)']
```

**Authority basis.** `forseti_semantic_evidence_integration_contract_v0.md`
states for v7 that "Missing, duplicate, foreign, reordered, malformed, or
broad-scope responses fail closed", and
`docs/workflows/phase_a_customer_evidence_completion_path_v0.md` states "A
malformed, overlong, or support/counter/adjacent/exclude-leaking reason code
fails closed before display." Both claims were false for the v7 confirmation
path. The contract also states "Creator-authored material cannot supply
customer support", and the v7 confirmation prompt itself instructs
"Creator-authored material remains adjacent influence context and cannot become
customer corroboration" — an instruction with no runtime enforcement behind it.
This is commissioned Required Attack 4 landing.

**Blast radius, stated precisely.** The laundered row does not enter the
customer-truth block: `_select_groups` filters on `row["layer"] == layer`, so an
`influence_context` row cannot occupy a truth origin group or a reserved
support/counter lane. The damage is that the durable artifact records a
creator-authored row as `relation: support` in `labeled_inventory` and
`candidate_dispositions`, and the row appears in the influence block carrying a
support-shaped display label. Any consumer that counts relations across the
inventory, rather than re-filtering by layer, reads creator support as support.

**Patch.** Add the three missing guards to the confirmation loop, reusing the
first pass's own boundary names for the two new checks
(`reason_code_relation_leak`, `creator_customer_laundering`) and folding the
length bound into the existing `relation_confirmation_shape` raise. Existing
boundary names were deliberately not renamed.

**Red-green proof (same-check).** The new test
`test_preselection_confirmation_reapplies_first_pass_row_guards` asserts all
three boundaries. Against the unpatched runtime the equivalent probes returned
`ACCEPTED` for all three (output above); after the patch:

```text
[BLOCKED ] P1 creator_authored confirmed as 'support': boundary=creator_customer_laundering
[BLOCKED ] P2 confirmation reason_code containing 'adjacent': boundary=reason_code_relation_leak
[BLOCKED ] P3 confirmation reason_code of 151 chars: boundary=relation_confirmation_shape
[BLOCKED ] relation-word leak 'adjacent_to_the_claim': boundary=reason_code_relation_leak
[BLOCKED ] over-long 151-char reason code: boundary=relation_confirmation_shape
```

**minimum_closure_condition.** A confirmed relation and reason code clear every
per-row guard the first-pass label had to clear, and a falsifier in
`[selection-tests]` fails against the unguarded behavior.

**next_authorized_action.** Home/CA adjudicates the patch hunk and keeps,
modifies, or reverts it.

### CR-02 — major — confidence high — `[selection-runtime]` — NOT PATCHED

**Location.** `build_customer_pull_point_frontier`, the subject filter
`if not (subjects & wanted_subjects): continue`, which precedes
`considered_ids.append(proposition_id)`.

**Defect.** A proposition whose `subject_product_ids` do not intersect the
requested subjects is dropped before it is counted. It appears in no queue, in
no `nonpromoted_points` disposition, and not in `considered_proposition_ids`.
The `accounting` block reports `considered_proposition_count` but no
subject-filtered count, so the number of propositions the frontier never looked
at is invisible.

**Why the defense fails.** The steelman is that a proposition about another
product is legitimately out of scope, and the three-way accounting is defined
over *considered* propositions, which `verify_customer_pull_point_frontier`
enforces exactly. That defense holds for the internal invariant but not for the
operator-facing claim. The fitness reference requires accounting "every selected
product proposition exactly once", and the workflow document says the command
"accounts every product proposition in one of three places". A mistyped or
stale `subject_product_ids` value silently produces a smaller frontier that
still passes `verify_customer_pull_point_frontier` and still reports a clean
three-way accounting — a frontier that looks complete and is not.

**Evidence.** The dogfood cited in the commission accounted 105 propositions as
8 + 93 + 4, which sums exactly because every proposition matched the subject. A
subject-id typo produces the same clean-looking shape over a subset, with no
number anywhere that reveals the shortfall.

**Why it was deliberately not patched.** The natural fix — a
`subject_filtered_count` in `accounting` — changes the frontier schema, which
changes `frontier_sha256`, which invalidates the already-produced frontier
`3055c49a0a075d4f628a752ffede987cebeb9f8eb048b7dda443189d26283300` cited in the
commission's evidence. The commission forbids altering historical production
outputs. Choosing between a schema change plus a frontier rebuild and leaving
the gap is an owner decision, not a delegate decision.

**minimum_closure_condition.** Either the frontier records how many
propositions the subject filter excluded, or the owning documents stop claiming
the frontier accounts every proposition and state the subject-scoped bound
instead.

**next_authorized_action.** Owner decision on schema change versus documentation
correction.

### CR-03 — minor — confidence high — `[selection-runtime]` — NOT PATCHED

**Location.** `RELATION_PROMPT`, the added sentence "Support directly supports
the bounded claim. Counter directly opposes or materially qualifies it.
Adjacent is relevant context that directly establishes neither direction.
Exclude is wrong-scope or non-evidence."

**Defect.** `RELATION_PROMPT` is shared by both first-pass call sites
(`prepare_evidence_selection` and the batched path), so the edit applies to
every selection mode, including legacy replays. It changes the relation prompt
text, therefore `prompt_sha256`, therefore `selection_manifest_sha256`,
therefore any downstream quote manifest hash.

**Evidence.** Running the identical non-value fixture through
`prepare_evidence_selection` plus `finalize_relations_prepare_quotes` at the
parent revision and at the target revision, the only content differences in the
resulting v6 quote manifest are the two hash fields:

```text
- "selection_manifest_sha256": "f2bcc8e38f992c7cee50c8a8cbc0ae27347e828c6fd0eee3c443145818cf5dc0"
+ "selection_manifest_sha256": "230f95273dc56cfae02b9d51f1659ad3ee54d7aaf82c7d2060fae3936202b684"
```

`labeled_inventory_sha256`, `selected_rows_sha256`, the quote `prompt_sha256`,
the selected row set, and `truth_selection_policy` are byte-identical, so the
selection behavior itself did not regress.

**Impact, bounded honestly.** An already-stamped v6 quote manifest still
finalizes, because `_verified_quote_manifest_version` checks the manifest's own
stored hash and does not re-derive the relation prompt. What is lost is
from-spec byte reproducibility: re-running a historical spec today no longer
yields the historical selection manifest. A repository search found no
production artifact pinning these hashes; the only match is a prior review
output. The documents' "exact reproduction" language is therefore stronger than
what the code now provides for a from-spec replay.

**Why deliberately not patched.** Reverting the sentence would remove an
intentional semantic improvement that aligns the first-pass prompt with the new
v7 confirmation prompt. Whether replay-hash stability or prompt alignment wins
is an owner call.

**minimum_closure_condition.** Either the shared prompt edit is scoped so
legacy modes keep their historical text, or "exact reproduction" is restated as
"already-stamped manifests remain finalizable".

**next_authorized_action.** Owner decision.

### CR-04 — minor — confidence medium — `[selection-runtime]` — NOT PATCHED

**Location.** `_frontier_point_sort_key`, first sort component
`0 if "reported_behavior" in reasons else 1`.

**Observation.** Any proposition whose `claim_kind` is `reported_behavior`
sorts ahead of every non-`reported_behavior` proposition, regardless of
`independent_support_origin_count` or material engagement. A broad reported
behaviour such as merely trying the product therefore outranks a
twice-independently-supported, materially engaged value objection.

**Disposition.** The commission asks to distinguish an implementation defect
from an intended discovery disposition and not to silently redesign the earning
rule. The contract's earning list is unordered, so the code is not contradicted
by it, and behaviour-closest-to-purchase leading is a coherent intent. This is
reported as a priority question for the owner, not patched.

**minimum_closure_condition.** The owner confirms that unconditional
`reported_behavior` precedence is the intended discovery order, or the sort key
is changed.

**next_authorized_action.** Owner decision.

### CR-05 — minor — confidence high — `[selection-runtime]` — NOT PATCHED

**Location.** `build_customer_pull_point_frontier`, the `origins` set
comprehension keyed on
`(packet.get("source_bindings", {}).get("corpus_sha256"), row["independence_key"])`.

**Observation.** The first tuple component is constant for all rows within one
packet, so the pair is effectively a one-element key and
`independent_support_origin_count` is a count of distinct `independence_key`
values. The component is dead rather than wrong. `independence_key` itself is
derived identically here and in `_candidate_rows`
(`evidence.get("independence_key") or evidence_id`), so the frontier and the
selection path agree on the underlying identity; the frontier counts unscoped
evidence-level origins while selection groups on `scoped_independence_key`.

**Why not patched.** Removing the dead component changes `frontier_sha256` and
invalidates the pinned dogfood frontier, for no behavioral gain.

**minimum_closure_condition.** None required for correctness; noted so a future
reader does not mistake the tuple for a cross-corpus independence guarantee.

**next_authorized_action.** No action.

### AR-01 — major — confidence high — `[semantic-contract]` `[phase-a-workflow]` — PATCHED

**Phase.** correctness.

**Location.** Contract line "Every historical v6 point pack also requires a
separate selected-row relation confirmation before quote finalization"; workflow
line "New point packs use `phase_a_evidence_quote_manifest_v7`".

**Defect.** Both documents reclassify v6 as historical and reproduction-only,
but `finalize_relations_prepare_quotes` and
`finalize_batched_relations_prepare_quotes` still stamp `QUOTE_MANIFEST_VERSION`
(v6) for any new non-frontier selection, and both CLI routes remain live and
ungated. Under contract v52 every completed selection artifact is a bounded
evidence-point pack, so a new non-frontier selection made today is a new point
pack stamped v6 — which the documents say does not exist.

**Why the defense fails.** The steelman is that the intended workflow is
frontier-first, so in practice new packs are v7. That defense describes
intent, not the runtime. Nothing in the code prevents or warns about the v6
route, so a reader who trusts "historical" would mis-read a fresh v6 manifest
as a legacy artifact and could skip its still-required selected-row
confirmation.

**Impact.** Version-terminology drift on the v6/v7 legacy boundary, which is a
named commissioned attack surface (Required Attack 13). It risks an operator
treating a live obligation as a reproduction-only one.

**Patch.** Both documents now state that v7 is the route for a frontier-bound
point pack and that the non-frontier routes still stamp v6, so the v6
selected-row confirmation obligation is live rather than reproduction-only.

**Red-green proof.** `not_applicable` — this is a source-support claim, not an
executable check. `pwsh .github/scripts/run-doc-gates.ps1` passed 24/24 after
the edit; that is shape and gate evidence, which is weaker than a behavioral
falsifier and is labeled as such.

**minimum_closure_condition.** Every behavioral claim about which manifest
version a live route produces matches what that route stamps.

**next_authorized_action.** Home/CA adjudicates the two doc hunks.

## Considered And Defended

- Retailer-first silently becoming retailer-only — defended.
  `community_discovery_queue` is populated independently of
  `retailer_support`, `customer_pull_policy.retailer_is_admission_gate` is
  `False`, and `checkback.retailer` records
  `none_observed_in_bound_packet` rather than demoting the point. Deleting the
  community queue and rehashing fails at
  `customer_pull_frontier_accounting`.
- A negative value point inheriting the positive-value direction — defended.
  `selection_spec_from_customer_pull_frontier` stamps
  `relation_policy="bounded_point"` and `axis_ids: []`; `_uses_value_policy`
  returns `False` for that policy before any axis inference, so
  `_policy_guidance` emits no value-box text and `VALUE_REASON_RELATIONS` is
  not enforced. Historical `auto` value selections were verified unchanged in
  the cross-revision differential under CR-03.
- A first-pass reversed relation deleting a high-engagement or protected row —
  defended. `_preselection_confirmation_candidates` selects on `layer`,
  `protected_lanes`, and `engagement_material_positive` only, never on
  `relation`, and its membership rule matches `_truth_row_display_eligible`
  exactly. A first-pass `exclude` on a material row is recoverable, and the
  `selected_relation_unconfirmed` check is a real backstop rather than the
  primary guard.
- A forged v7 replay accepted after a local rehash — defended. `finalize_quotes`
  re-derives the entire expected quote manifest by re-running
  `finalize_preselection_relation_confirmation_prepare_quotes` over the embedded
  replay and compares whole dictionaries, and that re-run itself re-verifies the
  embedded selection manifest's own hash and re-derives
  `candidate_inventory_sha256` from the real sources. Forging requires forging
  the packet.
- v6 versus v7 confirmation attachment — defended. A v7 manifest falls to the
  `elif` branch and rejects a late attachment at
  `unexpected_relation_confirmation`; v6 still raises
  `selected_relation_confirmation_required` when the attachment is absent.
- Protected row confirmed as `exclude` — defended.
  `_validate_protected_rows` runs on the corrected inventory and raises
  `protected_candidate_excluded`.
- Confirmation ordering or handles leaking first-pass signal — defended.
  `_confirmation_row_presentation` orders by
  `sha256(frontier_sha256 + "::" + candidate_id)` and emits opaque `row_NN`
  handles; the envelope carries no candidate id, relation, reason code,
  engagement, or priority.
- Runner path resolution, wrong packet or bundle pairing, overwrite refusal,
  provider calls — defended. Every new runner output is guarded by an
  `output.exists()` refusal before write, all new runs report
  `model_api_calls: 0` and call no provider, and passing a packet other than
  the one the frontier was built from fails inside
  `verify_customer_pull_point_frontier` because the rebuild diverges.
- Engagement aggregation or cross-platform ordering — defended. The frontier
  stores `engagement_status` and `engagement_material_positive` only, exposes
  `cross_platform_score: None`, and every ordering path buckets by
  `(source_role, source_venue, engagement_kind)` before any native value.
- Duplicate or missing proposition identities — defended.
  `len(by_id) != len(propositions)` and `set(by_id) != set(selected_ids)` both
  fail closed, truncated or non-proposition packets are rejected, and
  `verify_customer_pull_point_frontier` re-checks queue-membership uniqueness
  before the full rebuild.
- Smallest complete extension versus a parallel evidence authority — defended.
  The frontier is a derived navigation view over the existing v3 packet, adds
  no packet v4, mutates no packet or proposition, and reuses the existing
  selection spec and cap. The v7 route reuses `_prepare_quotes_from_labeled`
  rather than forking the quote pipeline. No packet v4 or full semantic replay
  is requested by this review.

## Bounded Uncommitted Diff

Five files were commissioned as patchable. Three were patched; the runner
needed no change. The diff is generated from the reviewer worktree against the
target revision and is uncommitted.

```diff
diff --git a/forseti-harness/judgment/phase_a_evidence_selection.py b/forseti-harness/judgment/phase_a_evidence_selection.py
index d44bfa75..074e297f 100644
--- a/forseti-harness/judgment/phase_a_evidence_selection.py
+++ b/forseti-harness/judgment/phase_a_evidence_selection.py
@@ -2687 +2687,6 @@ def finalize_preselection_relation_confirmation_prepare_quotes(
-        if relation not in RELATIONS or not isinstance(reason_code, str) or not REASON_CODE_RE.fullmatch(reason_code):
+        if (
+            relation not in RELATIONS
+            or not isinstance(reason_code, str)
+            or len(reason_code) > 80
+            or not REASON_CODE_RE.fullmatch(reason_code)
+        ):
@@ -2690,0 +2696,5 @@ def finalize_preselection_relation_confirmation_prepare_quotes(
+        if INTERNAL_RELATION_LABEL_RE.search(reason_code.replace("_", " ")):
+            raise EvidenceConsumerError(
+                "reason_code_relation_leak",
+                "reason code must name the evidence meaning, not its internal relation",
+            )
@@ -2695,0 +2706,10 @@ def finalize_preselection_relation_confirmation_prepare_quotes(
+        # The confirmed label replaces the first-pass label, so it must clear the
+        # same per-row guards the first pass applied.  Every influence row is in
+        # the confirmation frontier by construction, so without this check a
+        # confirmed "support" would launder creator-authored material into
+        # customer corroboration after the first pass rejected exactly that.
+        if row["layer"] == "influence_context" and relation in {"support", "counter"}:
+            raise EvidenceConsumerError(
+                "creator_customer_laundering",
+                "creator-authored evidence cannot corroborate customer truth",
+            )
diff --git a/forseti-harness/tests/unit/test_phase_a_evidence_selection.py b/forseti-harness/tests/unit/test_phase_a_evidence_selection.py
index f279e06d..31ffe202 100644
--- a/forseti-harness/tests/unit/test_phase_a_evidence_selection.py
+++ b/forseti-harness/tests/unit/test_phase_a_evidence_selection.py
@@ -575,0 +576,95 @@ def test_preselection_confirmation_recovers_material_candidate_before_cap_select
+def test_preselection_confirmation_reapplies_first_pass_row_guards(
+    tmp_path: Path,
+) -> None:
+    """A confirmed label must clear the guards the first-pass label had to clear.
+
+    The confirmation response overwrites the first-pass relation and reason
+    code, so a guard applied only on the first pass is not applied at all.
+    """
+    spec, sources = _write_source(tmp_path, 20)
+    _, _, selection_manifest = prepare_evidence_selection(spec, sources)
+    candidates = _candidate_rows(sources, spec)
+    first_pass = _relation_response(candidates)
+    _, _, confirmation_manifest = prepare_preselection_relation_confirmation(
+        selection_manifest, sources, first_pass
+    )
+    original_by_id = {
+        row["candidate_id"]: row
+        for row in _validate_relation_response(candidates, first_pass)
+    }
+    reason_by_relation = {
+        "support": "matching_customer_experience",
+        "counter": "differing_customer_experience",
+        "adjacent": "related_customer_context",
+        "exclude": "wrong_scope_or_non_evidence",
+    }
+
+    def _confirmation(overrides: dict[str, tuple[str, str]]) -> dict:
+        checks = []
+        for row_id, candidate_id in zip(
+            confirmation_manifest["confirmation_row_ids"],
+            confirmation_manifest["confirmation_candidate_ids"],
+            strict=True,
+        ):
+            relation = original_by_id[candidate_id]["relation"]
+            relation, reason_code = overrides.get(
+                candidate_id, (relation, reason_by_relation[relation])
+            )
+            checks.append(
+                {
+                    "confirmation_row_id": row_id,
+                    "relation": relation,
+                    "reason_code": reason_code,
+                }
+            )
+        return {
+            "point_scope": "single_point",
+            "point_scope_reason": "One direction-bearing hydration point.",
+            "relation_checks": checks,
+        }
+
+    creator_id = next(
+        row["candidate_id"]
+        for row in candidates
+        if row["layer"] == "influence_context"
+        and row["candidate_id"] in confirmation_manifest["confirmation_candidate_ids"]
+    )
+    truth_id = next(
+        row["candidate_id"]
+        for row in candidates
+        if row["layer"] == "truth_support"
+        and row["candidate_id"] in confirmation_manifest["confirmation_candidate_ids"]
+    )
+
+    for overrides, boundary in (
+        (
+            {creator_id: ("support", "matching_customer_experience")},
+            "creator_customer_laundering",
+        ),
+        ({truth_id: ("adjacent", "adjacent_to_the_claim")}, "reason_code_relation_leak"),
+        (
+            {truth_id: ("adjacent", "a" + "_bcde" * 30)},
+            "relation_confirmation_shape",
+        ),
+    ):
+        with pytest.raises&#40;EvidenceConsumerError&#41; as caught:
+            finalize_preselection_relation_confirmation_prepare_quotes(
+                selection_manifest,
+                sources,
+                first_pass,
+                confirmation_manifest,
+                _confirmation(overrides),
+            )
+        assert caught.value.boundary == boundary
+
+    # The identical labels are rejected on the first pass, so confirmation is
+    # not merely stricter here -- it now matches.
+    laundered_first_pass = copy.deepcopy(first_pass)
+    for row in laundered_first_pass["results"]:
+        if row["candidate_id"] == creator_id:
+            row["relation"] = "support"
+    with pytest.raises&#40;EvidenceConsumerError&#41; as caught:
+        _validate_relation_response(candidates, laundered_first_pass)
+    assert caught.value.boundary == "creator_customer_laundering"
+
+
diff --git a/forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md b/forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
index 27e5d786..9d914d9d 100644
--- a/forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
+++ b/forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
@@ -954,2 +954,5 @@ hash and fails quote finalization.
-Every historical v6 point pack also requires a separate selected-row relation
-confirmation before quote finalization. The confirmation prompt contains only
+Every v6 point pack also requires a separate selected-row relation
+confirmation before quote finalization. V7 is the route for a frontier-bound
+point pack; the non-frontier `finalize-evidence-selection-relations` and
+`finalize-evidence-selection-batches` routes still stamp v6, so this obligation
+is live for those packs and is not reproduction-only. The confirmation prompt contains only
diff --git a/docs/workflows/phase_a_customer_evidence_completion_path_v0.md b/docs/workflows/phase_a_customer_evidence_completion_path_v0.md
index 4eb63844..bc25bb77 100644
--- a/docs/workflows/phase_a_customer_evidence_completion_path_v0.md
+++ b/docs/workflows/phase_a_customer_evidence_completion_path_v0.md
@@ -671 +671,2 @@ establish that either signal caused the other.
-New point packs use `phase_a_evidence_quote_manifest_v7` and record the
+New frontier-bound point packs use `phase_a_evidence_quote_manifest_v7`; the
+non-frontier relation and batched routes still produce `v6`. Both record the

```

## Validation

All commands were run in the reviewer worktree at
`C:/tmp/phase-a-rev-74865c03` with the patch applied, and the results below are
the observed results.

| Command | Result |
| --- | --- |
| `python -m pytest -q` on the three focused test files | exit 0, 351 passed |
| `python -m pytest -q forseti-harness` | exit 0, one pre-existing skip, existing deprecation and unknown-mark warnings only |
| `pwsh .github/scripts/run-doc-gates.ps1` | 24/24 gates passed |
| `git diff --check` | exit 0, no whitespace errors |

The focused suite counted 350 tests before the patch and 351 after, the added
test being the CR-01 falsifier. The pre-patch baseline for the same three files
was also exit 0, so the patch neither fixed nor broke an existing test; it
closed a gap no existing test covered.

Not run, and not claimed: no provider call, no extraction or reconciliation
rerun, no packet v4, no Deliver calibration, no token or latency measurement,
no real-corpus dogfood. The evidence in the commission's "Evidence To Confirm,
Not Trust" section was not independently reproduced against the machine-local
dogfood packet, because that path was outside this worktree; the frontier
SHA-256 and the 8/93/4 accounting are therefore carried forward as commission
claims, not as facts this review observed.

## Residual Risk

- CR-02 remains open: a subject-scoped frontier can look completely accounted
  while silently excluding propositions, and no number anywhere reveals it.
- CR-03 remains open: from-spec replay of a historical selection no longer
  reproduces its historical selection-manifest hash.
- CR-04 remains open as a design question about discovery ordering.
- The CR-01 patch closes the three guards that the first pass already applied.
  It does not prove that the first-pass guard set is itself complete; any guard
  missing from both passes is out of this review's reach.
- The confirmation frontier's membership rule and
  `_truth_row_display_eligible` are two separate expressions of the same
  admission rule, kept in agreement by hand. They were verified to agree at
  this revision. A future change to one and not the other would be caught only
  by the `selected_relation_unconfirmed` backstop, which fails the run rather
  than silently mis-selecting — loud, but late.
- The lines this review authored are the non-independent sliver of this pass.
  They received mechanical verification through the named falsifier and the
  full suite, and they still require home/CA adjudication.

## Review-Use Boundary

These findings are decision input for the commissioning Chief Architect. They
are not approval, not validation, not readiness, not mandatory remediation, and
not executor-ready patch authority. The diff, the citations, and the verdict are
claims to adjudicate, not premises to inherit. The home/CA may accept, modify,
or reject every change and must revert rejected hunks. Nothing is kept until
that adjudication, and no lifecycle action was taken: nothing was committed,
pushed, merged, or published.

## Delegated Review Return Courier

```text
DELEGATED_CODE_REVIEW_RETURN_FOR_HOME_MODEL

Commission: Phase A customer-pull frontier and v7 preselection relation
delegated adversarial code review-and-patch at 74865c03.
Target kind: delegated_code_review_and_patch, five named files.
Controller: Anthropic (claude-opus-5). Author family: OpenAI. Cross-vendor
discovery bar met; no same-vendor or self substitution; no replacement
controller launched.

Findings: CR-01 critical (patched), CR-02 major (not patched), CR-03 minor
(not patched), CR-04 minor (not patched), CR-05 minor (not patched),
AR-01 major (patched).
Patched files: phase_a_evidence_selection.py,
test_phase_a_evidence_selection.py,
forseti_semantic_evidence_integration_contract_v0.md,
phase_a_customer_evidence_completion_path_v0.md.
Unpatched by design: run_semantic_evidence_integration.py (no finding).
Diff: uncommitted in C:/tmp/phase-a-rev-74865c03.
Validation: focused suite exit 0 (351 passed), full harness exit 0,
doc gates 24/24, git diff --check exit 0.
Verdict: MATERIAL_FALSE_GREEN_FOUND_AND_PATCHED_IN_SCOPE, three unpatched
findings routed for owner decision. Not accepted, not ready, not mergeable.
Residual: CR-02, CR-03, CR-04 open; delegate-authored lines are the
non-independent sliver.
```
