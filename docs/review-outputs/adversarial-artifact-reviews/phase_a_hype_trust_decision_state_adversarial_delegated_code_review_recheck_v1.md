---
retrieval_header_version: 1
artifact_role: Cross-vendor delegated adversarial code review-and-patch return for the Phase A hype/trust Decision State ownership repair
scope: Closure recheck of the four prior majors, bounded uncommitted workflow patch, and residuals at implementation revision 961e3e29
authority_boundary: retrieval_only
use_when:
  - Adjudicating whether the hype/trust Decision State ownership repair may land, be modified, or be rejected.
  - Auditing which of the six bound closure conditions were met at 961e3e29 and which residuals remain.
open_next:
  - docs/review-outputs/adversarial-artifact-reviews/phase_a_hype_trust_decision_state_adversarial_delegated_code_review_recheck_v0.md
  - .agents/workflow-overlay/delegated-review-patch.md
  - docs/workflows/phase_a_customer_evidence_completion_path_v0.md
  - forseti-harness/judgment/phase_a_evidence_axis_consolidation.py
---

# Phase A hype/trust Decision State ownership repair — adversarial delegated code review recheck v1

reviewed_by: Anthropic Claude Opus (controller)
authored_by: OpenAI Codex
controller_model_family: Anthropic
author_home_model_family: OpenAI
de_correlation_bar: cross_vendor_discovery
required_revision: `961e3e29ba6c6d5fee1c4055c810e3306ddf13a5`
reviewed_revision: `961e3e29ba6c6d5fee1c4055c810e3306ddf13a5`
courier_revision: `59548c356463d8a2c275d6ad89db992670738240`
prior_reviewed_revision: `d669777ac1e42a0ff330c649f76bdeb37f6f300c`
repair_diff: `699bdeff7ac8a2bb31537b0f6018a47e57782541..961e3e29ba6c6d5fee1c4055c810e3306ddf13a5`
implementation_diff: `d669777ac1e42a0ff330c649f76bdeb37f6f300c..961e3e29ba6c6d5fee1c4055c810e3306ddf13a5`
review_method: workflow-code-review
review_lane: delegated_code_review_and_patch
output_mode: filesystem-output
edit_permission: patch-only (exercised on `[workflow]` only)
review_use_boundary: >
  These findings, citations, diff, and verdict are decision input only. They are
  not approval, not validation, not mandatory remediation, and not
  executor-ready patch authority. Nothing was committed, pushed, merged, or
  published, and no frozen input or output was altered.

## Receiver binding and exact-revision preflight

Controller family is Anthropic; author home family is OpenAI. The lineages
differ, so the cross-vendor discovery bar holds. No same-vendor, self, no-repo,
or context-pack substitute was used, and no second controller was dispatched.

Observed directly in `C:\Users\vmon7\.codex\worktrees\phase-a-hype-trust-axis`
before any read or edit:

- branch `codex/hype-trust-axis`;
- `git status --porcelain` empty, satisfying `dirty_state_allowed_at_start: false`;
- `HEAD` = `59548c35`, whose only delta against `961e3e29` is the courier prompt
  itself (1 file, +61/-44), so `stale_if` did not fire and the reviewed bytes
  are the pinned implementation.

The prior return is present in-tree and was read completely. Its recomputed
raw SHA-256 is `921c78345bdd0f0590bd3c7bb8748d42c9c06d12ae8099474c5eeb14996adc02`,
matching the commission. The `[selector]` and `[selector-tests]` targets are
untouched since `d669777a`, so closure items 2 and 5 were rechecked against the
prior pass rather than re-derived.

`workflow-code-review` was invoked and is the review method for this lane.

## Verdict

**`patch_before_acceptance`.** All six bound closure conditions are met at
`961e3e29`, and three of the four prior majors are closed by mechanism rather
than by assertion. The repair is materially stronger than the revision it
replaces: the candidate-inventory recompute is real and I confirmed it holds
byte-exact across all 2,145 frozen dispositions; the accounting-contract guard
has genuine red-green coverage; the reader is honestly re-versioned to v3.

Two things stand. One is a **new major** — the repair's integrity boundary
excludes `relation` and `reason_code` by name, and on the frozen corpus those
exact fields diverge from the only other pinned source for thirteen displayed
rows, with no artifact recording the authority for the change. One bounded,
truthful `[workflow]` patch is returned for it. The other is a **narrowed
survivor** of the prior semantic-ownership finding, whose mechanical closure
would change emitted reader bytes and so is the owner's call, not mine.

I did not escalate. Unlike the prior pass, a truthful bounded patch exists and
is returned below.

## Closure recheck

| # | Closure condition | Status |
| --- | --- | --- |
| 1 | Made-up / altered / sibling / wrong-source / spec-authored parent fails at the candidate inventory boundary after honest repinning | **Met** — verified on frozen data and in the new test |
| 2 | Legacy quote prompting receives no parent text; quotes stay literal child text | **Met** — unchanged since `d669777a` |
| 3 | Every semantic and state row handle identity-bound, including in-range swaps preserving range and membership | **Substantially met**; one narrowed swap class survives (F6) |
| 4 | Parent context lends no source role, date, engagement, or customer/creator status | **Met**, and improved beyond the prior wording |
| 5 | Exact per-point hype meanings survive without a cross-axis hype enum | **Met** — unchanged |
| 6 | Compact accounting contract fails on rule-identity divergence; reader identifies as v3 | **Met** |

### Item 1 — verified, not trusted

`_validate_point_binding` now recomputes the source-shaped inventory when the
selection manifest declares `linked_parent_context_v1`
(`forseti-harness/judgment/phase_a_evidence_axis_consolidation.py:458-478`).
I re-ran that recomputation independently against every frozen point artifact
under `C:\tmp\forseti-phase-a-hype-trust-exposure-bound-20260825-v2`:

```text
prop_02ea2754857b59843cd3 policy= linked_parent_context_v1 n= 429 MATCH
prop_1a4c51070134adc3916a policy= linked_parent_context_v1 n= 429 MATCH
prop_1ea796dcfca08320dd99 policy= linked_parent_context_v1 n= 429 MATCH
prop_639ccf284f2c9ac271af policy= linked_parent_context_v1 n= 429 MATCH
prop_fde4ba2177b8a331d2c4 policy= linked_parent_context_v1 n= 429 MATCH
total dispositions 2145
```

The exact attack my prior pass demonstrated — edit `parent_context` inside
`candidate_dispositions`, re-pin `artifact_sha256`, rebuild the axis pack — is
now rejected. The replacement test
(`test_candidate_inventory_rejects_rewritten_parent_context_before_projection`,
`forseti-harness/tests/unit/test_phase_a_evidence_axis_consolidation.py:1762`)
honestly re-pins the selection manifest, the quote manifest, the artifact, and
all four descriptor hashes before injecting the made-up parent, and asserts the
failure lands at `candidate_access` / `candidate disposition inventory changed`
rather than at an earlier outer hash. That is exactly what the closure
condition asked for.

The `elif` branch at `:470-478` also closes the prior minor m6 direction: a
candidate carrying `parent_context` without the linked policy now fails loud
instead of silently projecting.

### Item 6 — verified

`_reader_evidence_accounting_contract` raises
`decision_state_reader_accounting_contract` when its key set diverges from
`EVIDENCE_ACCOUNTING_CONTRACT` (`:284-289`), and
`test_reader_accounting_contract_rejects_an_authority_key_fork` (`:914`)
monkeypatches an extra authoritative key and asserts the raise — a real
red-green, not the tautology it replaced. The reader emits
`phase_a_evidence_decision_state_reader_surface_v3` (`:2288`).

## Findings

### F5 — `[projector]` `[workflow]` The integrity boundary excludes the two fields that decide a displayed row's relation, and they diverge on the frozen corpus

- severity: major
- confidence: high on the mechanism and the observation; the cause of the divergence is not established
- location: `forseti-harness/judgment/phase_a_evidence_axis_consolidation.py:459-467` (the `relation`/`reason_code` exclusion), `:554-557` and `:2716-2719` (relation checked only artifact-against-artifact)

Evidence. The new recompute strips exactly `{"relation", "reason_code"}` from
each disposition before hashing. Those two fields therefore sit outside the
only content-derived integrity check the projector performs on
`candidate_dispositions`. The projector's two relation checks compare the
artifact's disposition to the artifact's own display row; no second pinned
source is consulted. `quote_manifest["labeled_inventory"]` — which is
hash-pinned three ways (its own `labeled_inventory_sha256`, the quote
manifest's self-consistent `manifest_sha256`, and
`artifact["quote_manifest_sha256"]`, all of which I verified as consistent) —
is never compared.

The exclusion is not academic. Across all five frozen points, thirteen
**displayed** candidates carry an artifact `relation` that differs from the
hash-pinned `labeled_inventory`:

```text
prop_02ea2754857b59843cd3 displayed=14 divergent=1
    candidate_78fc774b798b47b7af0b19ef labeled= counter -> disposition= adjacent
prop_1a4c51070134adc3916a displayed=13 divergent=4
    candidate_7d37b78aad448ca1f47e14e2 labeled= support  -> disposition= adjacent
    candidate_7f122c243457bcc5fa60835a labeled= counter  -> disposition= adjacent
    candidate_9f5971aa1189f50eb69b780e labeled= counter  -> disposition= adjacent
    candidate_f93278b90c53483e2d153660 labeled= support  -> disposition= adjacent
prop_1ea796dcfca08320dd99 displayed=15 divergent=1
    candidate_21bdea654d4703836b72265e labeled= support  -> disposition= adjacent
prop_639ccf284f2c9ac271af displayed=13 divergent=3
    candidate_440c6dbc356d4500f61a247f labeled= support  -> disposition= adjacent
    candidate_9d1eedaa14660f7a846771f0 labeled= support  -> disposition= adjacent
    candidate_e0a23ec88d39ff07e11d5665 labeled= support  -> disposition= adjacent
prop_fde4ba2177b8a331d2c4 displayed=13 divergent=4
    candidate_7d37b78aad448ca1f47e14e2 labeled= support  -> disposition= adjacent
    candidate_7f122c243457bcc5fa60835a labeled= counter  -> disposition= adjacent
    candidate_9d1eedaa14660f7a846771f0 labeled= support  -> disposition= adjacent
    candidate_9f5971aa1189f50eb69b780e labeled= counter  -> disposition= adjacent
```

Every divergence moves in one direction — toward `adjacent` — and the
`reason_code` is unchanged in every case. Worked through in full for the first:

```text
labeled_inventory   relation: counter  | reason: rhode_preferred_for_formula_safety
candidate_disposit  relation: adjacent | reason: rhode_preferred_for_formula_safety
quote_manifest selected_rows: selected_03 counter  rhode_preferred_for_formula_safety
artifact display row:          selected_03 adjacent rhode_preferred_for_formula_safety
```

That is a formula-scope appraisal downgraded away from an overall-product
judgment — precisely what `DECISION_OBJECT_SCOPE_RELATION_GUIDANCE` requires.
The direction is conservative in every one of the thirteen cases, so this reads
as a correct semantic narrowing, not as laundering, and I am **not** claiming
the axis's meaning is wrong.

What I am claiming is narrower and mechanical. I could not identify the code
path that produces it. The only in-harness post-confirmation relation rewrite
sets `relation = "exclude"`
(`forseti-harness/judgment/phase_a_evidence_selection.py:2591`), not
`"adjacent"`; the preselection confirmation at `:3899` runs before the quote
manifest is written; and the run's own
`relation_binding_adjudication_receipt.json` records `"adjudications": []`.
So thirteen displayed relations were narrowed after the quote manifest was
frozen, and no artifact in the verified chain records the authority for it.
Including those fields in the recompute is not an available fix — it would
reject the frozen axis outright.

- authority basis: commission attack 8 (relation and hash lineage); the repair's own new boundary; `docs/workflows/phase_a_customer_evidence_completion_path_v0.md`.
- impact: the field that decides support versus counter versus adjacent for every displayed row is authoritative by the spec-supplied `artifact_sha256` alone, and the workflow doc described the new recompute in terms that read as complete coverage of the disposition inventory.
- minimum_closure_condition: either the post-manifest relation narrowing has a hash-bound authority the projector verifies, or the owning prose states plainly that `relation` and `reason_code` sit outside the recomputed boundary and are pinned by the artifact hash alone.
- next_authorized_action: the second half is closed by the returned `[workflow]` patch. The first half — whether the thirteen narrowings should carry a recorded, verifiable authority — is an owner decision and is not patched here.
- verification expectation: the returned patch is prose; its proof is the six gates below plus the frozen-corpus observation. No red-green applies to a documentation correction.
- patch_queue_entry: not applicable; the bounded patch is applied and returned, not queued.

### F6 — `[projector]` A coordinated ownership-block swap on a state-free relation fact still passes

- severity: major
- confidence: high
- location: `forseti-harness/judgment/phase_a_evidence_axis_consolidation.py:1825-1840` (ownership set built from two self-asserted fields), `:1930-1937` (membership judged against that set)

Evidence. The repair adds `primary_semantic_unit_row_id` and
`companion_semantic_unit_row_ids` to each relation fact and requires relation,
context-only, and state semantics to belong to that ownership set, with
`state_binding_sha256` rechecking both state partitions. This closes the swap I
demonstrated in the prior pass and every single-field variant: moving only the
relation and context-only handles now fails with `semantic rows do not belong`,
and re-pointing a state row at forged content fails with
`state row identity does not match`. Both are covered by the updated test.

The ownership set is still asserted by the same row it authorizes. Moving the
whole block together is accepted:

```text
fact selected_02 reddit:thread1:comment1 primary 0 comp [] rel [0] ctx [] relstates [1] ctxstates []
fact selected_01 reddit:thread1:post     primary 1 comp [2] rel [1] ctx [] relstates [0] ctxstates [2]
moving whole ownership block: attach reddit:thread1:post::hydrating
  (owned by selected_01 / reddit:thread1:post) onto selected_02 / reddit:thread1:comment1
VALIDATION PASSED -- coordinated ownership-block swap accepted
```

Setting the victim fact's `primary_semantic_unit_row_id`,
`companion_semantic_unit_row_ids`, `relation_semantic_unit_row_ids`,
`context_only_semantic_unit_row_ids`, both state-row lists, and a recomputed
`state_binding_sha256` together attaches a meaning owned by a different
evidence row, from a different origin, with an opposite relation.

The class is much narrower than the prior finding. It requires forging a
digest rather than swapping an index, and it only works when the victim fact
asserts no states — a fact that binds states cannot have its ownership moved,
because the state rows' semantics must remain inside the owned set. Context-only
rows with empty `state_ids` are a legitimate and documented form, so the class
is real rather than degenerate.

The structural reason is that the compact reader contains no data relating a
semantic unit to the evidence row that produced it: `semantic_unit_table` has
no evidence column, and `state_binding_sha256` covers state content only.

- authority basis: commission closure item 3, which asks specifically for "plausible in-range swaps that preserve valid ranges and semantic membership"; commission attack 5.
- impact: within a mutation-testing frame, a mis-wire that carried a fact's whole semantic block from the wrong placement while its `evidence_id` came from the right one is not detected. A cold reader holding only the compact surface cannot recheck ownership against anything.
- minimum_closure_condition: the per-fact digest covers the fact's identity as well as its states — at minimum `evidence_id`, `selected_id`, `primary_semantic_unit_row_id`, and `companion_semantic_unit_row_ids` — so a semantic block cannot be moved without also contradicting the evidence identity the same fact already rechecks.
- next_authorized_action: owner decision. Extending `_reader_state_binding_sha256` into an ownership digest changes emitted reader bytes, so it invalidates the frozen reader-v3 views (`0151893391…` raw, `7873ee4641…` logical) and the dogfood receipt (`c0cc199deb…`) this commission cites as its evidence. That trade is the owner's; I did not take it unilaterally.
- verification expectation: red-green is available — the probe above must raise at `decision_state_reader_evidence_binding` after any such change, and the existing suite must still pass.
- patch_queue_entry: not authorized (byte-impacting; owner decision).

### Minor findings and named residuals

- **m7** `[projector]` The item-1 recompute is a cross-artifact **consistency** check, not a re-derivation from the captured bundle. A coordinated re-pin of the artifact, the selection manifest, the quote manifest, and the spec still passes, because `candidate_inventory_sha256` is a scalar the projector never recomputes from the bundle it verifies at `:479-492`. This raises forgery cost from one file to four with four hash recomputations, which is a real improvement, and the home explicitly rejected a source-schema re-freeze. Named residual, not a defect against the bound condition. Confidence high.
- **m8** `[projector-tests]` `_fixture` still monkeypatches `load_selection_sources` to `[]` (`:179-182`), so `_verify_packet`, `_verify_bundle`, and the packet/bundle binding at `:479-492` have zero unit coverage. The item-1 fix does not depend on those sources, so this no longer blocks the closure it blocked last pass, but the projector's only tie to captured reality remains unexercised. Severity minor, confidence high.
- **m9** `[projector]` Reader v3 removes the version ambiguity for everything emitted from `961e3e29` forward, and I confirmed the historical v2 views 7 and 8 are byte-unchanged at `2b11bc38c866d86adf1336217078604002262498cb46a48cc907b747b2ffa714`. The prior collision *between* frozen v2 payloads persists on disk: `post_review_validation/consolidated_view_1..6.json` carry `placement_table`, while views 7 and 8 do not, and all eight declare v2. Frozen outputs must not be altered, so the closure is a line on the durable disposition, not an edit. Severity minor, confidence high.
- **m10** `[projector]` The accounting guard compares rule **identities** only. A rule could still be weakened in the compact wording without failing, and the workflow doc's "wording compaction, not a weaker rule" claim remains partly unenforced. Closure item 6 asked only for rule identities, so this is a named residual rather than a miss. Severity minor, confidence high.

## Returned patch

One file, `[workflow]`, uncommitted. It closes the second half of F5's minimum
closure condition — making the boundary visible in the owning prose — without
touching emitted bytes, frozen inputs, or frozen outputs. It adds no recurring
step, gate, or receipt, and it pins no corpus-specific count that would need
maintaining.

`[workflow]` `docs/workflows/phase_a_customer_evidence_completion_path_v0.md`

```diff
diff --git a/docs/workflows/phase_a_customer_evidence_completion_path_v0.md b/docs/workflows/phase_a_customer_evidence_completion_path_v0.md
index db8b836b..801178d9 100644
--- a/docs/workflows/phase_a_customer_evidence_completion_path_v0.md
+++ b/docs/workflows/phase_a_customer_evidence_completion_path_v0.md
@@ -905 +905,9 @@ candidate hash; a spec-supplied replacement or rewritten candidate context is
-rejected.
+rejected. That recomputation is an integrity boundary, not a completeness
+claim. `relation` and `reason_code` stay outside it because a point artifact
+may legitimately carry a later, narrower relation than the quote manifest that
+produced it — an object-scope downgrade to `adjacent` under the rule above is
+the expected case. Those two fields are therefore authoritative by the
+spec-supplied `artifact_sha256` alone: no second pinned source can contradict
+them, and a relation changed after the quote manifest was written is not
+detectable at projection. Any such change records its authority with the
+artifact; the inventory hash does not carry it.

```

I deliberately did not patch F6, m7, m8, m9, or m10. F6 and m9 carry
frozen-artifact consequences that belong to the owner; m7 was explicitly
adjudicated out of scope by the home; m8 is a fixture-substrate investment; m10
exceeds the bound closure condition.

## considered_and_defended

- **Could the recompute false-fail on a legitimate rerun?** Candidate: `selected_id` or other fields mutated onto labeled rows during quote preparation would break the hash. Defense held: `_select_groups` returns copies, so `row["selected_id"] = selected_id` never reaches the labeled inventory, and no frozen disposition carries `selected_id`. Confirmed across all 2,145 frozen rows; the recompute matched every point.
- **Key-order sensitivity of the recompute.** Candidate: dict ordering could make the hash unstable across producers. Defense held: `_compact` uses `sort_keys=True`, so `_canonical_json_sha256` is order-independent.
- **`state_binding_sha256` position independence.** Candidate: two distinct states with identical content would be interchangeable. Defense held: `decision_state_id` is itself a content hash, so identical content is the same state row; the digest also separates the two partitions, so moving a row between them is caught.
- **Could the new `owned_semantic_row_ids` constraint false-fail a legitimate view?** Candidate: a state whose semantics fall outside primary-plus-companion would break a valid build. Defense held: `_decision_state_group` already forces `asserted_refs | context_ref_set == available_refs` where `available_refs` is exactly primary plus companions, so state semantics are always inside the owned set. The frozen axis and the 254-test suite both build clean.
- **Does the new item-1 test repeat the implementation as its oracle?** Candidate: it recomputes `_canonical_json_sha256` over the same shaped list production uses. Defense held: the hash is fixture construction, not the assertion; the made-up parent is injected *after* the hash is computed, so the failing condition is independent of the production formula. Mild oracle coupling, no wrong-cause green.
- **Legacy-v1 and Direct Outcome isolation (attack 7).** Attacked and held: the reader-v3 surface is built only when at least one point routes `decision_state`; `LEGACY_CONSOLIDATED_VIEW_VERSION` and the direct-outcome relation binding path are untouched by this diff, and the round-trip through `_expand_compact_decision_state_groups` still pins its exact compact group key set.
- **Hype semantics (attacks 1-3) and legacy quote routing (attack 2).** Attacked and held, unchanged from the prior pass: `[selector]` and `[selector-tests]` are byte-identical to `d669777a`. The decision-object scope guidance remains unconditional in `_policy_guidance`, no cross-axis hype enum was forced, and `LEGACY_QUOTE_PROMPT` still receives no parent context or parent-context columns.
- **Attack 6 after the placement-table removal.** Attacked and held, and improved: the fact row now carries `primary_semantic_unit_row_id` and `companion_semantic_unit_row_ids`, so the prior pass's m1 — primary versus companion no longer distinguishable — is closed. With `layer`, `evidence_table`'s role/venue/surface/date/engagement columns, `origin_group_id`, and per-point `candidate_inventory_sha256`, the recovery list holds.
- **Contract vocabulary drift (prior m2, m3, m4).** Rechecked and closed: the full-view `qualification_rule` now names `point_placements`, the reader overrides supply reader-native `placement_processing_rule` and `context_only_row_rule`, and the test that pinned the stale `placement_table` string now pins `point_placements`.
- **Self-containment claim (prior m6, closure item 4).** Rechecked and closed: the reader join order now states that empty parent arrays "mean no parent context is supplied and do not prove self-containment", and the workflow doc carries the same correction.
- **Whether the thirteen relation narrowings indicate laundering.** Candidate: displayed relations changed outside the hash chain could hide creator-to-customer promotion. Defense held: every one of the thirteen moves toward `adjacent`, never toward `support` or `counter`, and each keeps its original `reason_code`. The direction is uniformly conservative and matches the object-scope rule. F5 is reported as an integrity-boundary and recorded-authority finding only.

## Validation evidence

All six commissioned gates run against the patched worktree:

```text
python -m pytest -p no:cacheprovider -q \
  forseti-harness/tests/unit/test_phase_a_evidence_axis_consolidation.py \
  forseti-harness/tests/unit/test_phase_a_evidence_selection.py
  -> 254 passed

python .agents/hooks/check_harness_coupling.py --strict
  -> 18 passed; GATE PASS harness coupling contracts

python .agents/hooks/check_retrieval_header.py --changed --strict
  -> exit 0

python .agents/hooks/check_placement.py --changed --strict --base origin/main
  -> 10 changed paths, 0 violations, 0 freshness, 5 legacy-tolerated (warn-only); exit 0

python .agents/hooks/check_prompt_output_mode.py --strict --base origin/main
  -> OK (0 findings in 1 changed in-scope file); exit 0

git diff --check
  -> exit 0
```

The 254-test result matches the commission and was also observed unpatched
before the `[workflow]` edit, so the patch changed no test outcome.

Independently recomputed from "Evidence To Confirm, Not Trust":

```text
921c78345bdd0f0590bd3c7bb8748d42c9c06d12ae8099474c5eeb14996adc02  prior review return v0
2b11bc38c866d86adf1336217078604002262498cb46a48cc907b747b2ffa714  consolidated_view_7.json
2b11bc38c866d86adf1336217078604002262498cb46a48cc907b747b2ffa714  consolidated_view_8.json
```

All match, confirming both the prior return's identity and that the historical
v2 views remain byte-unchanged.

Not run, with cause:

- The reader-v3 view hashes (`0151893391…`, `7873ee4641…`) and the v3 dogfood receipt (`c0cc199deb…`) were not recomputed. The named paths under `post_review_validation/consolidated_view_9_v3.json`, `consolidated_view_10_v3.json`, and `dogfood_post_review_v3/final_receipt.json` were not resolved during this pass, so those are not-proven boundaries rather than confirmations.
- The frozen packet, bundle, and axis-pack raw hashes were not recomputed; their paths are not named in the commission.
- The dogfood comparison figures — 42 ties, six compact wins, the one full-arm critical parent-context omission, and the token totals — were read as commission claims and not re-derived.
- No red-green proof accompanies F5 or F6, because F5's returned patch is prose and F6's closure is byte-impacting and unauthorized.

## Residual risk

- F5's mechanical half is open: thirteen displayed relations were narrowed after the quote manifest was frozen, and nothing in the verified chain records why. The returned patch makes the boundary honest; it does not create the missing authority record. If the narrowing was applied by a rerun whose quote manifest was not re-saved, the cheapest closure is to re-save that manifest so the two sources agree.
- F6 leaves a narrow ownership-forgery class open on state-free facts. Its closure changes emitted reader bytes and would need the same versioning treatment the v2-to-v3 move just received.
- The reader-v3 surface is 15,565 bytes larger than the final v2 surface, an accepted pre-review residual. I did not independently confirm that figure.
- The hype/trust semantic boundaries between "overhyped", "did not live up to hype", "worth the hype", and "love despite going viral" remain enforced by prompt prose with no deterministic code guard. This is owner-adjudicated under closure item 5 and is not a finding, but the highest-loss false green named in the fitness reference stays structurally unguarded in code.
- Frozen v2 views 1 through 6 and 7 through 8 remain mutually incompatible under one version label. No edit is possible or appropriate; the disposition should say so.

## Blockers, off-scope flags, and not-proven boundaries

- No blocker to landing was found. Both open majors are owner decisions with named trade-offs, not defects that prevent a truthful patch.
- Off-scope and flag-only, not patched: `prepare_selected_relation_confirmation` still receives no policy guidance; the absence of a deterministic hype reason-code lane; the operator-side pipeline scripts under `C:\tmp` that appear to have produced the F5 divergence.
- Not proven: the reader-v3 view and receipt hashes; the frozen packet, bundle, and axis-pack hashes; the dogfood comparison figures; the reader-v3 size delta; and the cause of the thirteen relation narrowings.
- Exactly one repository file was modified by this review — the `[workflow]` doc — plus this report. Nothing was committed, pushed, merged, or published, and no frozen artifact was altered.
