---
retrieval_header_version: 1
artifact_role: Cross-vendor delegated adversarial code review-and-patch return for the Phase A evidence-first customer-pull frontier ordering
scope: Findings, bounded uncommitted patch, and recomputed evidence against implementation revision 7b148f14
authority_boundary: retrieval_only
use_when:
  - Adjudicating whether the evidence-first frontier ordering may be kept, modified, or rejected before landing.
  - Auditing which frontier ordering hazards were confirmed, which were defended, and which remain owner decisions.
open_next:
  - forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md
  - forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
  - docs/workflows/phase_a_customer_evidence_completion_path_v0.md
  - forseti-harness/judgment/phase_a_evidence_selection.py
---

# Phase A evidence-first customer-pull frontier ordering — delegated review and patch

reviewed_by: Anthropic Claude (controller)
authored_by: OpenAI Codex
controller_model_family: Anthropic
author_home_model_family: OpenAI
required_revision: `7b148f14a0ea6d97e0a14de971009fb536aebc02`
reviewed_revision: `7b148f14a0ea6d97e0a14de971009fb536aebc02`
reviewed_diff: `eaf0fea102649c8c4d517e610eb3785060577392..7b148f14a0ea6d97e0a14de971009fb536aebc02`
review_method: workflow-code-review
review_use_boundary: >
  These findings, citations, diff, and verdict are decision input only. They are
  not approval, not validation, not mandatory remediation, and not
  executor-ready patch authority.

## Receiver binding

The nominated `effective_target_worktree` `C:\Users\vmon7\.codex\worktrees\e4f8\orca`
was observed on branch `codex/phase-a-hydration-pack-cap-pilot` at `c5ad0896`,
one commit past the required revision, so it was not used for the patch. The
only commit between the two is `c5ad0896 Route evidence-first frontier
adversarial review`, and it touches none of the four named targets, so the
reviewed bytes are unaffected. A controller-owned detached worktree was created
from the exact required revision at
`C:\Users\vmon7\Desktop\projects\orca\.claude\worktrees\ctrl-frontier-review-7b148f14`
and observed clean at `7b148f14` before any read or edit. A second
controller-owned worktree at
`C:\Users\vmon7\Desktop\projects\orca\.claude\worktrees\ctrl-falsifier-base-7b148f14`
holds the unpatched reviewed revision and was used to prove the falsifier fails
before the patch and to run the baseline. Both are controller scaffolding and
are the owner's to remove.

Controller family is Anthropic; author home family is OpenAI. The lineages
differ, direct repository access was exercised, and no replacement controller
was launched.

## Verdict

**`patch_before_acceptance`.** The change does what it claims on the reviewed
corpus: the author's before/after numbers reproduce exactly, the motivating
near-miss holds through the real builder, creator-authored material cannot
supply customer support, and a reordered or truncated frontier is rejected by
verification. One confirmed runtime false green is patched here. Three further
confirmed hazards are ordering-design questions the current fitness sources do
not decide, and are returned as owner decisions rather than patched.

Per-target sub-verdicts:

- `[selection-runtime]` — patch_before_acceptance. One reachable materiality
  false green (CR-01) patched; CR-02, CR-03, CR-04, CR-08 returned unpatched.
- `[selection-tests]` — patch_before_acceptance. The shipped falsifier tests the
  private sort key, not the queue (CR-06); an end-to-end falsifier is added.
- `[semantic-contract]` — patch_before_acceptance. Paragraph merge (CR-05) and
  two undisclosed ordering properties (CR-01, CR-04) closed in prose.
- `[phase-a-workflow]` — accept as written. Every changed sentence matches
  observed runtime behavior; CR-07 is a reachability caveat, not a false claim.

## Findings

Severity and confidence are priority labels only. They create no approval,
validation, mandatory remediation, or patch authority.

### CR-01 — `[selection-runtime]` — major — confidence high — confirmed — patched

**Failure mechanism.** The frontier projection reads
`engagement.get("material_positive")` with no `engagement_unavailable` guard,
while all three sibling projections of the same field apply one:
`phase_a_evidence_selection.py:1089`, `:1166`, and
`phase_a_evidence_consumer.py:281` all null the value when
`status == "engagement_unavailable"`. A support row can reach the frontier with
an unavailable engagement posture and a truthy `material_positive`, because the
consumer merges `engagement_defaults` over the row's engagement columns
(`phase_a_evidence_consumer.py:175-186`) and only checks that `status` and
`engagement_kind` agree — it never checks that an unavailable posture carries no
materiality.

The leaked value is load-bearing twice over. It sets
`material_support_evidence_ids` (`:402-408`), which earns
`material_source_native_engagement` and therefore **admission**
(`:414-415`, `:426-433`), and it sets `material_count`, which this commit
promoted to the posture rank and to the second ordering key
(`:236`, `:244`, `:250`).

**Failure scenario, reproduced.** A `community_post` source group with
`engagement_kind: engagement_unavailable`, `engagement_columns: ["status"]`,
`engagement_defaults: {"material_positive": true}`, and one evidence row whose
engagement column is `["engagement_unavailable"]` passes `_verify_packet` and
`_expand_packet`. At `7b148f14` the point supported only by that row is admitted
to `community_discovery_queue` with
`earning_reasons: ["material_source_native_engagement"]` and support rows
reporting `engagement_status: "engagement_unavailable"` alongside
`engagement_material_positive: True`. Without the leak the same point is
`nonpromoted` with `no_investigation_earning_signal`.

**Fitness citation.** The claim-support contract, *Engagement is resonance
corroboration*, rule 2: "Zero or negligible positive engagement earns no
resonance credit"; rule 3: "When context is too thin to judge materiality, keep
the raw value and do not award the posture"
(`forseti_intelligence_claim_support_contract_v0.md:112-118`). An unavailable
engagement posture is the maximal case of absent basis.

**Standing.** Pre-existing at the parent `eaf0fea1`; this commit amplifies it by
making the same unguarded value the primary posture rank. Not exercised by the
reviewed corpus: 0 of 3347 evidence rows in the dogfood packet carry an
unavailable-but-material engagement, and the frontier this patch produces from
that packet is byte-identical to the unpatched one.

**minimum_closure_condition.** The frontier projection yields `None` materiality
for an unavailable engagement posture, proven by a falsifier that runs through
`build_customer_pull_point_frontier` rather than the private sort key.

**next_authorized_action.** Chief Architect adjudicates hunk 1 and the new
`test_customer_pull_frontier_denies_material_credit_to_unavailable_engagement`.

### CR-02 — `[selection-runtime]` `[semantic-contract]` — major — confidence high — confirmed — not patched

**Failure mechanism.** `support_posture_rank` is a four-value total order placed
*ahead* of `-origin_count` (`phase_a_evidence_selection.py:238-251`). Two
cross-role origins therefore outrank any number of same-role origins, and the
posture label replaces the count as the dominant ordering fact.

**Fitness citation, against.** The claim-support contract states the postures
"identify the support route actually present. They are not a universal
source-quality score or a total ranking", gives a worked counter-example (a
directly observed price beats repeated comments for a price claim), and requires
that "Exact counts, source roles, proximity, and limitations always travel with
the posture; the label never replaces them"
(`forseti_intelligence_claim_support_contract_v0.md:82-87`).

**Failure scenario, reproduced.** In a synthetic retailer queue,
`A-cross-role-weak` (2 origins, 0 materially engaged rows, roles
`['community_post', 'retailer_review']`) leads `B-retailer-deep` (4 independent
retailer origins, 4 materially engaged rows) because posture rank 0 beats rank 1
before origin count is read.

**Live exposure, measured, and it is currently nil.** On the reviewed dogfood
packet the inversion does not occur. The retailer-first queue holds 5 rank-0
points and 3 rank-1 points, and for every rank-0 point the count of rank-1
points with strictly more origins and no less material engagement is zero. The
community-discovery queue holds no rank-0 point at all. So this is a latent
structural hazard in the ordering rule, not an observed defect in the reviewed
output.

**Why not patched.** The commission authorizes a patch here only if the current
fitness sources decide it. They decide that a posture ladder must not *become* a
total ranking, but they explicitly decline to supply the replacement ranking
("not a total ranking"). Choosing between "posture dominates count", "count
dominates posture", and "posture applied claim-kind-relative" is an owner
design decision, not a delegate correction.

**minimum_closure_condition.** The owner records which of those three orderings
the frontier asserts, and the contract sentence stops implying the postures are
a general strength rank.

**next_authorized_action.** Owner decision; no code change proposed.

### CR-03 — `[selection-runtime]` — major — confidence high — confirmed — not patched

**Failure mechanism.** `material_count` is `len(material_support_evidence_ids)`
(`phase_a_evidence_selection.py:236`), and that list is built from distinct
*evidence IDs* (`:402-408`), not distinct origins. Rows that share one
`independence_key` — the contract's reposts, quoted reviews, and downstream
summaries — each add one to the ordering key.

**Fitness citation.** "Reposts, syndicated articles, quoted reviews,
screenshots, and downstream summaries that share one origin count once"
(`forseti_intelligence_claim_support_contract_v0.md:128-129`).

**Failure scenario, reproduced, and live in the reviewed corpus.** Two support
rows re-keyed onto one shared `independence_key` produce
`independent_support_origin_count=1` with two material evidence IDs, and that
point leads an otherwise identical point backed by one genuine materially
engaged origin. On the reviewed dogfood packet, 17 of the 101 admitted points
have more material evidence IDs than distinct material origins —
`prop_b730a47403f19797dad1` at 20 ids over 18 origins, and sixteen
community-discovery points at 2 ids over 1 origin.

**Scope limit, stated honestly.** `independent_support_origin_count` is itself
correctly deduplicated by `independence_key` (`:398-401`) and is ordered *before*
material count, so echo inflation can only reorder points that already tie on
both posture and origin count. The named attack — "reward duplicate rows from
one origin as independent corroboration" — does not occur; the inflation is
confined to resonance ordering.

**Why not patched.** The contract separates resonance from independent-origin
credit and warns against translating engagement into origin counts (rule 1,
`:110-111`), so it does not clearly extend "count once" to resonance ordering.
Deduplicating would also change the emitted `material_support_evidence_ids`
semantics, the production queue order, and the frontier hash — high lock-in for
an owner-level judgement.

**minimum_closure_condition.** The owner decides whether within-posture
resonance ordering counts endorsements or distinct endorsed origins.

**next_authorized_action.** Owner decision; no code change proposed.

### CR-04 — `[selection-runtime]` `[semantic-contract]` — major — confidence high — confirmed — disclosure patched

**Failure mechanism.** `protected:{lane}` is an earning reason
(`phase_a_evidence_selection.py:416-417`) but has no standing in
`_frontier_point_sort_key`. Because the commit moved `reported_behavior` from
the first key to the fourth, a protected point that earned its former top slot
through behavior now sorts by posture like anything else.

**Failure scenario, reproduced.** A protected `costly_behavior` point with one
quiet origin and no material engagement sorts **first** in its queue under the
parent key `(0, -1, 0, id)` and **last** under the reviewed key `(3, -1, 0, 0, id)`.
A protected `safety` point with the same shape also sorts last.

**What is not wrong.** Admission is unchanged, the point stays in its queue, and
the exactly-once accounting still holds, so the point does not disappear. This
is a change of top-of-queue priority, not of visibility. Per the commission, no
new priority score was invented.

**Standing.** The behavior demotion is the intended change; the undisclosed
consequence for protected lanes is not stated anywhere in the reviewed prose.
The v55 changelog's "unchanged" list covers packet v3, admission, retailer-first
routing, and the origin cap, and is accurate as written — it simply does not
reach ordering priority.

**minimum_closure_condition.** The ordering authority states that a protected
lane grants no ordering priority, so an operator cannot assume protected points
lead. Patched in `[semantic-contract]`.

**next_authorized_action.** Chief Architect adjudicates hunk 3; separately
decides whether protected lanes should acquire ordering standing at all.

### CR-05 — `[semantic-contract]` — minor — confidence high — confirmed — patched

The v55 insertion ends at "…outrank a more strongly corroborated point." with no
blank line before "The materialized spec uses `relation_policy=bounded_point`:",
so the new ordering paragraph and the pre-existing materialized-spec paragraph
render as one paragraph. Patched by restoring the paragraph break.

**minimum_closure_condition.** The two paragraphs render separately.
**next_authorized_action.** Chief Architect adjudicates hunk 3.

### CR-06 — `[selection-tests]` — major — confidence high — confirmed — patched

**Failure mechanism.** `test_customer_pull_frontier_orders_evidence_strength_before_behavior_tiebreak`
imports the private `_frontier_point_sort_key` and sorts four hand-authored
dicts. It asserts a property of the key in isolation, so it cannot fail if
`build_customer_pull_point_frontier` stops populating `customer_support_roles`,
mis-derives `independent_support_origin_count`, routes a point to the wrong
queue, or stops sorting the queues at all. It also exercises only posture rank 1:
ranks 0, 2, and 3 are never reached, so the boundaries the commission names are
untested.

**Failure scenario.** Deleting either `retailer_queue.sort(...)` or
`community_queue.sort(...)` at `phase_a_evidence_selection.py:476-477` leaves the
shipped falsifier green while the queue an operator reads is unordered.

**minimum_closure_condition.** A falsifier that builds a real frontier and
asserts the queue order the reader sees. Patched by
`test_customer_pull_frontier_queue_orders_strength_before_behavior_end_to_end`.

**next_authorized_action.** Chief Architect adjudicates hunk 2.

### CR-07 — `[semantic-contract]` `[phase-a-workflow]` — minor — confidence medium — confirmed — not patched

Both prose sources present the four-rung ladder as operating "within each queue"
and "Within the retailer-first and community-discovery queues". Rank 0 requires
two truth roles, and any point with `retailer_review` support routes to the
retailer queue (`phase_a_evidence_selection.py:434`, `:474`). In a corpus whose
only truth roles are `community_post` and `retailer_review` — the reviewed
corpus's shape, `support_source_roles: ['community_post', 'retailer_review']` —
rank 0 is therefore unreachable in the community-discovery queue by
construction. The measured posture census over the reviewed packet is rank 0: 5
(all retailer-first), rank 1: 76, rank 2: 20, rank 3: 0. In the 93-point queue
the operator actually navigates, the new ladder collapses to two rungs and
discriminates no better than the pre-existing origin and material keys did.

Not patched: the prose is not false, and the reachability is corpus-contingent.
The owner should know that the headline rung does no work on the current corpus
shape before treating the ladder as the change's value.

**minimum_closure_condition.** Owner acknowledges the reachability condition.
**next_authorized_action.** Owner decision; no change proposed.

### CR-08 — `[selection-runtime]` — minor — confidence high — confirmed — not patched

`_frontier_point_sort_key` coerces drifted inputs silently: a string
`"3"` origin count sorts as 3, `2.9` truncates to 2, a missing key sorts as
posture rank 3 with origin 0, duplicate roles collapse correctly, and `None`
raises a bare `TypeError` instead of a bounded `EvidenceConsumerError`. This is
unreachable from `build_customer_pull_point_frontier`, where the field is always
`len(origins)`, but the reviewed commit made this private function an imported
test surface, so drifted callers are now possible. Not patched: adding
validation to a private sort key is recurring ceremony for an unreachable path.

**minimum_closure_condition.** Either the private key stays out of test imports,
or it validates its inputs.
**next_authorized_action.** Owner decision; no change proposed.

### CR-09 — out of patch scope, flag only — major — confidence high — confirmed

The reviewed commit rewrote two archived source lines inside a `diff` fence in
`docs/review-outputs/adversarial-artifact-reviews/phase_a_customer_pull_frontier_preselection_relation_delegated_review_v0.md`
(lines 553 and 569) from `pytest.raises(EvidenceConsumerError)` to
`pytest.raises&#40;EvidenceConsumerError&#41;`. Inside a fenced code block HTML
entities are not decoded, so the durable record now renders text that does not
reproduce the delegate's reviewed bytes — a review record that misquotes the
code it reviewed.

The escaping is not an encoding convention. Line 554, immediately below, keeps
its literal `finalize_preselection_relation_confirmation_prepare_quotes(`, and
these two lines are the only occurrences of `&#40;` or `&#41;` anywhere under
`docs/`. The pattern is consistent with appeasing a gate that matches the
`raises(` token.

**Material interaction with this commission.** A documentation gate is inducing
corruption of quoted evidence inside review records — the same class of defect
this review lane exists to catch, applied to the lane's own outputs. The
commission forbids editing these records, so nothing was changed.

**minimum_closure_condition.** The archived lines reproduce the reviewed bytes,
and whichever gate matched `raises(` stops matching inside fenced code.
**next_authorized_action.** Owner routes a separate bounded fix; not touched here.

### CR-10 — out of patch scope, flag only — minor — confidence medium — confirmed

The same commit split `authored_and_adjudicated_by` into `authored_by` and
`adjudicated_by` and added a new `review_use_boundary` block in
`..._preselection_relation_home_adjudication_v0.md`. The field split is
mechanical. Adding a `review_use_boundary` block is a substantive addition to a
durable adjudication record inside a commit whose subject is frontier ordering.
Flagged as scope bleed; not edited.

**minimum_closure_condition.** Owner confirms the added boundary block was
intended in this commit.
**next_authorized_action.** Owner decision; not touched here.

## considered_and_defended

These attacks were run and held.

1. **Posture tuple against the v55 prose, at every named boundary.** Two
   origins / two roles ranks 0; two origins / one role ranks 1; one origin with
   material engagement ranks 2; one quiet origin ranks 3. The ladder matches the
   prose exactly.
2. **The motivating near-miss, through the real builder.** Building a real
   frontier from a real packet yields `stronger`, `weaker-behavior`,
   `equal-behavior`, `equal` — the stronger point leads, and the behavior point
   wins only the fully equal tie. The author's claim reproduces.
3. **False cross-role strength.** `origin_count >= 2 and role_count >= 2` is
   provably equivalent to "there exist two distinct origins carrying distinct
   roles", so an echoed origin cannot manufacture rank 0 on its own; one origin
   presenting two roles ranks 3, not 0. The frontier's origin key
   `(corpus_sha256, independence_key)` is the same independence notion the
   thirteen-origin cap uses via `scoped_independence_key`, so the two paths do
   not disagree.
4. **Creator-authored material.** Creator rows are filtered out before roles,
   origins, and materiality are computed (`:396`). A point supported by two
   creator rows plus one community row reports `origins=1` and
   `roles=['community_post']`; a creator-only point is `nonpromoted` with
   `no_customer_truth_support_in_bound_packet`. Creator material supplies no
   second role and no customer support.
5. **Cross-platform magnitude comparison.** No engagement magnitude enters the
   key — only the per-venue `material_positive` boolean, decided inside its own
   venue and metric upstream. Reddit points are never compared with retailer
   helpful votes. The residual that several venue-local material signals can
   outrank one very high signal is real and is recorded as CR-03.
6. **Queue separation and accounting.** Retailer-first is not retailer-only, a
   community-only point still earns the discovery queue and records retailer
   check-back as open, community support is never labelled retailer
   corroboration, every considered proposition occurs exactly once, and
   subject-filtered and nonpromoted points stay enumerated. Dropping one point
   and re-sealing is rejected at `customer_pull_frontier_accounting`.
7. **Determinism and local rehash.** Queue order is independent of packet row
   order and of proposition declaration order; ties terminate on
   `proposition_id`; a frontier whose queue was reordered and locally re-hashed
   is rejected at `customer_pull_frontier_verification` with "frontier does not
   rebuild". The new ordering is genuinely hash-bound, not advisory.
8. **Smallest complete ordering change.** The change is one private key
   function inside the existing v3 consumer. No commercial-pull score, behavior
   subtype classifier, packet v4, second evidence authority, new provider
   workload, or recurring review step is introduced.
9. **Admission unchanged.** The `earning_reasons` block is byte-identical to the
   parent revision. The patch returned here changes admission only in the CR-01
   leak case, which the reviewed corpus does not exercise — the frontier built
   from the dogfood packet is byte-identical before and after the patch.

## Recomputed evidence

Every author claim below was recomputed from the repository and the local
packet rather than accepted. The packet used is
`C:\tmp\forseti-summer-fridays-polarity-repair-replay-20260817-v0\incremental-terminal-migration-v10\phase_a_evidence_packet_v3.json`,
observed at 6548990 bytes with `packet_sha256`
`c9d8b5e5d1b199689f9fc0a35c6dc4f19de0a48e4e9815f5ec03ff8ddc62fe34`.

| Author claim | Recomputed result |
| --- | --- |
| Exact clean commit `7b148f14` with parent `eaf0fea1` | Confirmed; both objects present, `7b148f14` is the tip-1 commit of `codex/phase-a-hydration-pack-cap-pilot` |
| 105 considered propositions | Confirmed: `considered_proposition_count: 105`, `subject_filtered_count: 0` |
| 8 retailer-first, 93 community-discovery, 4 nonpromoted | Confirmed exactly; all 4 nonpromoted carry `no_investigation_earning_signal` |
| Top-13 community slice before: 13 behavior / 41 origins / 28 material | Confirmed exactly, recomputed under the parent sort key |
| Top-13 community slice after: 4 behavior / 92 origins / 51 material | Confirmed exactly, recomputed under the reviewed sort key |
| Frontier SHA-256 `fafbfe79…52b13f` | `not_reproduced` — the `frontier_id` and `business_question` used are recorded neither in the commission nor on disk, and both enter the hash. No frontier artifact exists under the dogfood root. The counts above are independent of those two inputs and do reproduce. |
| Targeted falsifier failed before, passed after | Confirmed by construction at the reviewed revision: the pre-change key orders `weaker-behavior` ahead of `stronger`, the reviewed key does not |
| `git diff --check` and Python compilation pass | Confirmed on the patched worktree |

The reviewed corpus carries only `positive_helpful_count` and `score_state`
engagement kinds, and 0 of its 3347 evidence rows combine an unavailable
engagement posture with a truthy `material_positive`. CR-01 is therefore latent
in this corpus, and the patch leaves this corpus's frontier byte-identical.

## Returned diff

Uncommitted, in the controller worktree at
`C:\Users\vmon7\Desktop\projects\orca\.claude\worktrees\ctrl-frontier-review-7b148f14`.
Nothing was committed, pushed, staged, stashed, reset, merged, or opened as a
pull request.

Blank context lines inside the fenced diff below were stripped of their
leading diff-context space to satisfy the review-record whitespace
convention this repository already applies to embedded diffs. The block is
therefore a faithful record of the change but is not byte-exact for
`git apply`; the adjudicable artifact is the uncommitted working tree named
above. This is the same gate pressure recorded as CR-09, handled by
disclosure rather than silently.

Neutral decision-sufficient citations, by hunk:

- **Hunk 1**, `[selection-runtime]`, closes CR-01. Cites
  `phase_a_evidence_selection.py:1089` and `:1166` and
  `phase_a_evidence_consumer.py:281` for the guard shape already used three
  times in this codebase, and
  `forseti_intelligence_claim_support_contract_v0.md:112-118` for the rule that
  absent engagement basis earns no resonance posture.
- **Hunk 2**, `[selection-tests]`, closes CR-06 and gives CR-01 a ground-truth
  falsifier. Cites `phase_a_evidence_selection.py:476-477` for the queue sorts
  the shipped test does not reach.
- **Hunk 3**, `[semantic-contract]`, closes CR-05 and discloses CR-01 and CR-04.
  Cites `phase_a_evidence_selection.py:236` and `:402-408` for the endorsement
  count, `:416-417` and `:238-253` for protected lanes carrying no ordering
  standing, and
  `forseti_intelligence_claim_support_contract_v0.md:115-118` for the ban on a
  universal cross-platform engagement number.

`[phase-a-workflow]` was left unmodified: every sentence it added matches
observed runtime behavior.

```diff
diff --git a/forseti-harness/judgment/phase_a_evidence_selection.py b/forseti-harness/judgment/phase_a_evidence_selection.py
index 5c187d0a..a6ffd6ea 100644
--- a/forseti-harness/judgment/phase_a_evidence_selection.py
+++ b/forseti-harness/judgment/phase_a_evidence_selection.py
@@ -375,6 +375,7 @@ def build_customer_pull_point_frontier(
                 )
             group, evidence = evidence_index[evidence_id]
             engagement = evidence.get("engagement") or {}
+            engagement_status = engagement.get("status") or "engagement_available"
             venue, venue_basis = _source_venue(
                 str(group["source_role"]), evidence.get("source_ref"), evidence_id
             )
@@ -386,9 +387,12 @@ def build_customer_pull_point_frontier(
                     "source_venue": venue,
                     "source_venue_basis": venue_basis,
                     "engagement_kind": group["engagement_kind"],
-                    "engagement_status": engagement.get("status")
-                    or "engagement_available",
-                    "engagement_material_positive": engagement.get("material_positive"),
+                    "engagement_status": engagement_status,
+                    "engagement_material_positive": (
+                        engagement.get("material_positive")
+                        if engagement_status != "engagement_unavailable"
+                        else None
+                    ),
                     "independence_key": evidence.get("independence_key") or evidence_id,
                 }
             )
diff --git a/forseti-harness/tests/unit/test_phase_a_evidence_selection.py b/forseti-harness/tests/unit/test_phase_a_evidence_selection.py
index 94474008..ee18f7b4 100644
--- a/forseti-harness/tests/unit/test_phase_a_evidence_selection.py
+++ b/forseti-harness/tests/unit/test_phase_a_evidence_selection.py
@@ -409,6 +409,151 @@ def test_customer_pull_frontier_orders_evidence_strength_before_behavior_tiebrea
     ]


+def _frontier_point(proposition_id: str, claim_kind: str, support: list[str]) -> dict:
+    return {
+        "proposition_id": proposition_id,
+        "bounded_proposition": f"Customers report the balm behaves as {proposition_id}.",
+        "claim_kind": claim_kind,
+        "axis_ids": ["value_and_quantity"],
+        "subject_product_ids": ["summer-fridays-lip-butter-balm"],
+        "product_version_ids": [],
+        "conditions": [],
+        "evidence_item_counts": {"support": len(support), "counter": 0, "adjacent": 0},
+        "evidence_relations": {
+            "support": [
+                [evidence_id, [f"{evidence_id}::hydration"]] for evidence_id in support
+            ],
+            "counter": [],
+            "adjacent": [],
+        },
+    }
+
+
+def _frontier_packet_for(propositions: list[dict], count: int = 25) -> dict:
+    packet, _ = _packet_and_bundle(count)
+    packet["selection"] = {
+        "mode": "proposition",
+        "axis_ids": ["value_and_quantity"],
+        "proposition_ids": [row["proposition_id"] for row in propositions],
+    }
+    packet["selection_coverage"] = {
+        "truncated": False,
+        "selected_proposition_count": len(propositions),
+    }
+    packet["propositions"] = propositions
+    packet.pop("packet_sha256")
+    packet["packet_sha256"] = _canonical_hash(packet)
+    return packet
+
+
+def test_customer_pull_frontier_queue_orders_strength_before_behavior_end_to_end() -> None:
+    # The sort key alone cannot show that the queue a reader actually sees is
+    # ordered this way: the rows must come from the builder's own counting.
+    # community_post evidence ids in a 25-row fixture are 0, 5, 10, 15, 20.
+    packet = _frontier_packet_for(
+        [
+            _frontier_point(
+                "stronger",
+                "customer_experience",
+                ["community_post:0", "community_post:5", "community_post:10", "community_post:15"],
+            ),
+            _frontier_point(
+                "weaker-behavior",
+                "reported_behavior",
+                ["community_post:5", "community_post:10"],
+            ),
+            _frontier_point(
+                "equal", "customer_experience", ["community_post:5", "community_post:15"]
+            ),
+            _frontier_point(
+                "equal-behavior", "reported_behavior", ["community_post:5", "community_post:15"]
+            ),
+        ]
+    )
+
+    frontier = build_customer_pull_point_frontier(
+        packet,
+        frontier_id="strength-before-behavior",
+        business_question="Which customer points deserve commercial investigation?",
+        subject_product_ids=["summer-fridays-lip-butter-balm"],
+    )
+
+    verify_customer_pull_point_frontier(frontier, packet)
+    assert [row["proposition_id"] for row in frontier["community_discovery_queue"]] == [
+        "stronger",
+        "weaker-behavior",
+        "equal-behavior",
+        "equal",
+    ]
+    assert frontier["retailer_first_queue"] == []
+
+
+def test_customer_pull_frontier_denies_material_credit_to_unavailable_engagement() -> None:
+    # An unavailable engagement posture carries no observable materiality basis,
+    # so it can neither earn investigation nor lift a point's support posture.
+    packet = _frontier_packet_for(
+        [_frontier_point("quiet-point", "customer_experience", ["community_post:quiet"])]
+    )
+    packet["source_groups"].append(
+        {
+            "source_family": "reddit_community",
+            "source_role": "community_post",
+            "engagement_kind": "engagement_unavailable",
+            "engagement_context": "unavailable",
+            "evidence_defaults": {},
+            "evidence_columns": packet["source_groups"][0]["evidence_columns"],
+            "engagement_defaults": {"material_positive": True},
+            "engagement_columns": ["status"],
+            "evidence_rows": [
+                [
+                    "community_post:quiet",
+                    "artifact:quiet",
+                    "https://reddit.com/evidence/quiet",
+                    "container:quiet",
+                    "2026-08-17T00:00:00Z",
+                    "actor:quiet",
+                    "credited",
+                    "origin:quiet",
+                    "public:quiet",
+                    ["engagement_unavailable"],
+                    [
+                        [
+                            "community_post:quiet::hydration",
+                            "Customer report quiet says the balm feels moisturizing.",
+                            "first_hand",
+                            "asserted",
+                            "affirmed",
+                            ["summer-fridays-lip-butter-balm"],
+                            [],
+                            ["hydration_and_moisture"],
+                            ["after use"],
+                            [],
+                        ]
+                    ],
+                ]
+            ],
+        }
+    )
+    packet.pop("packet_sha256")
+    packet["packet_sha256"] = _canonical_hash(packet)
+
+    frontier = build_customer_pull_point_frontier(
+        packet,
+        frontier_id="unavailable-engagement",
+        business_question="Which customer points deserve commercial investigation?",
+        subject_product_ids=["summer-fridays-lip-butter-balm"],
+    )
+
+    verify_customer_pull_point_frontier(frontier, packet)
+    assert frontier["community_discovery_queue"] == []
+    assert frontier["nonpromoted_points"] == [
+        {
+            "proposition_id": "quiet-point",
+            "disposition": "no_investigation_earning_signal",
+        }
+    ]
+
+
 def test_customer_pull_frontier_exposes_subject_filtered_propositions() -> None:
     packet = _proposition_packet_for_frontier()
     other = copy.deepcopy(packet["propositions"][0])
diff --git a/forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md b/forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
index 2dec694e..2cef7c63 100644
--- a/forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
+++ b/forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
@@ -1068,7 +1068,14 @@ earning signal. More independent origins and material engagement order points
 inside one posture. Reported behavior is retained as a separate commercial
 strength dimension and breaks otherwise equal ties; it is not a universal
 source-support rank and cannot make generic trial or ownership outrank a more
-strongly corroborated point.
+strongly corroborated point. Material engagement enters this order only as a
+count of endorsements already judged material inside their own venue and
+metric; an unavailable engagement posture earns no materiality, and no
+engagement magnitude is compared across venues. An operator-protected
+safety or costly-behavior lane keeps a point admitted and fully accounted but
+grants no ordering priority: a protected point supported by one quiet origin
+sorts last inside its queue.
+
 The materialized spec uses `relation_policy=bounded_point`: relation direction
 is evaluated against that proposition's exact wording. Thus an expensive-price
 complaint supports an expensive-price point instead of being inverted by the
```

## Validation evidence

Every command below was run by the controller against the durable target it
reports on. Baseline commands ran in the pristine worktree at the reviewed
revision; candidate commands ran in the patched controller worktree.

| Command | Target | Result |
| --- | --- | --- |
| `python -m pytest -q test_phase_a_evidence_selection.py test_phase_a_evidence_consumer.py test_semantic_evidence_integration.py` | candidate | **passed** — 355 passed, 0 failed |
| `python -m pytest -q forseti-harness --tb=no -p no:warnings` | baseline `7b148f14`, unpatched | **passed** — exit 0 over 5588 collected tests, one skip observed |
| `python -m pytest -q forseti-harness --tb=no -p no:warnings` | candidate | **passed** — exit 0 over 5590 collected tests, one skip observed |
| `pwsh .github/scripts/run-doc-gates.ps1` | candidate | **passed** — 24/24 doc gates |
| `git diff --check` | candidate | **passed** — exit 0 |
| Targeted falsifier at the unpatched reviewed revision | baseline `7b148f14` plus the new test file only | **failed as designed** — `test_customer_pull_frontier_denies_material_credit_to_unavailable_engagement` fails; the quiet point is admitted to `community_discovery_queue` instead of being nonpromoted |
| Dogfood frontier recompute | baseline and candidate | **passed and identical** — same accounting, same queue order, same `frontier_sha256` from both, confirming the patch does not perturb this corpus |

The candidate suite collects two more tests than the baseline: exactly the two
added in hunk 2. Pytest exits non-zero on any failure, so exit 0 on both trees
establishes zero failures on both; the count of pre-existing skips was equal in
posture across the two runs. No baseline failure was used to excuse anything,
because there was none.

Commands as run, on a PowerShell-first Windows host:

```powershell
$env:PYTHONPATH='forseti-harness'
python -m pytest -q forseti-harness/tests/unit/test_phase_a_evidence_selection.py forseti-harness/tests/unit/test_phase_a_evidence_consumer.py forseti-harness/tests/unit/test_semantic_evidence_integration.py
python -m pytest -q forseti-harness --tb=no -p no:warnings
pwsh .github/scripts/run-doc-gates.ps1
git diff --check
```

Not run, and why: no extraction, no semantic reconciliation, no provider call,
no capture. The frontier is deterministic and no-provider, and the commission
forbids rerunning those stages. `model_api_calls` is 0 in every frontier built
during this review.

## Residual risks

1. **CR-02, CR-03, and CR-04 are returned open.** All three are confirmed
   properties of the ordering rule, and all three are owner design decisions
   rather than delegate corrections. The queue shipped at `7b148f14` carries
   them.
2. **CR-01 is latent, not live.** The patch is justified by a reachable
   construction and by three sibling call sites, not by an observed defect in
   the reviewed corpus. An owner who judges the construction unreachable in
   practice may reasonably reject hunk 1; the falsifier would then also need to
   go.
3. **The reported frontier hash was not reproduced.** The counts and both
   top-13 slices reproduce exactly, but `frontier_id` and `business_question`
   are unrecorded and both enter the hash, so `fafbfe79…52b13f` stands
   unverified. Recording the frontier build inputs alongside the hash would
   close this for future reviews.
4. **The delegate-authored sliver.** Hunks 1 through 3 and the two new tests are
   controller-authored lines inside this same pass, so they carry no
   cross-vendor discovery credit. They are mechanically verifiable — the guard
   is a three-site class sweep, and the falsifier fails at the reviewed revision
   and passes after — and remain subject to Chief Architect adjudication.
5. **Two controller worktrees remain on disk.**
   `ctrl-frontier-review-7b148f14` holds the returned diff and this report;
   `ctrl-falsifier-base-7b148f14` is clean at the reviewed revision. Both are
   the owner's to remove. Nothing was committed, pushed, staged, stashed,
   reset, merged, or opened as a pull request in any worktree.
6. **CR-09 is unfixed by design.** The corrupted quotations in the earlier
   review record stay as they are, because the commission places those records
   outside patch scope.

```yaml
review_summary:
  lane: workflow-code-review
  target_kind: delegated_code_review_and_patch
  reviewed_revision: 7b148f14a0ea6d97e0a14de971009fb536aebc02
  controller_model_family: Anthropic
  author_home_model_family: OpenAI
  recommendation: patch_before_acceptance
  summary: Ordering does what it claims on the reviewed corpus and the author counts reproduce exactly; one reachable materiality false green is patched, and three ordering-design hazards plus a corrupted earlier review record are returned as owner decisions.
  next_action: Chief Architect adjudicates the three hunks and the two added tests, then decides CR-02, CR-03, CR-04, and CR-09 as owner-level questions.
  report_path: docs/review-outputs/adversarial-artifact-reviews/phase_a_customer_pull_frontier_evidence_first_ordering_delegated_review_v0.md
  review_location: controller_worktree_uncommitted
  findings_total: 10
  findings_confirmed: 10
  findings_patched: 4
  findings_returned_open: 6
  targets_patched: selection-runtime, selection-tests, semantic-contract
  targets_unchanged: phase-a-workflow
  architecture_pass_required: false
  validation: focused 355 passed; full suite exit 0 on baseline and candidate; doc gates 24/24; git diff --check clean
  dogfood_reproduction: counts and both top-13 slices reproduced exactly; frontier sha256 not reproduced for want of the recorded frontier_id and business_question
```

## Review-use boundary

These findings, citations, diff, verdict, and residuals are decision input only.
They are not approval, not validation, not mandatory remediation, and not
executor-ready patch authority. The Chief Architect adjudicates every hunk as a
claim, may accept, modify, or reject any of them, and reverts what it rejects.
Nothing here asserts that the change is accepted, ready, or mergeable.

