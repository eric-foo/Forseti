# Delegated Code Review + Bounded Patch — Phase A Evidence Selection And Exact Quotes (v0)

```yaml
retrieval_header_version: 1
artifact_role: Reviewer findings report (docs/review-outputs/) — awaiting home-CA adjudication
scope: >
  Cross-vendor delegated_code_review_and_patch return for the Phase A v3
  evidence-selection and exact-quote consumer at commit fe2bee78. Eleven
  findings, seven of them closed by a bounded patch inside the commissioned
  file set, four reported without patch because closure needs an owner
  decision. Records the production replay used to show the patch is
  hash-neutral on all three sealed pilots.
use_when:
  - Adjudicating what this review found before any landing decision on fe2bee78.
  - Checking why quote_unavailable in the sealed pilots does not mean a missing source body.
  - Checking which lane, venue, engagement, and nomination failure modes remain open.
authority_boundary: retrieval_only
review_provenance:
  authored_by: OpenAI (author family per commission; exact model unrecorded)
  reviewed_by: Anthropic claude-opus-5
  de_correlation_bar: cross_vendor_discovery
  access_mode: repo (direct worktree access; reviewed and patched at fe2bee781eda4bc38c7767b8ac248eb3fe3c7e2c)
  dispatch: docs/prompts/reviews/phase_a_evidence_selection_quotes_delegated_adversarial_code_review_patch_prompt_v0.md
  review_method: workflow-code-review lane for the Python targets; adversarial artifact reading for the two owning documents
  reviewer_recommendation: seven findings patched, four open for owner decision, no NEEDS_ARCHITECTURE_PASS
  findings: 11
review_use_boundary: >
  These findings, the returned diff, and every test result here are decision
  input for the home Chief Architect only. They are not approval, not
  validation, not readiness, not mandatory remediation, and not executor-ready
  patch authority. Nothing here is accepted or merge-ready until the CA
  adjudicates the diff, verdict, and residuals as claims.
non_claims: >
  Advisory review plus a bounded delegate-authored patch. No provider call was
  made. The 60,901-item semantic extraction was not rerun, no historical
  production output was modified, and no packet v4 was created.
```

## Method And What Was Actually Confirmed

Reviewed the exact commissioned diff
(`7b0cf240..fe2bee78`, five files) by direct repository inspection, then ran
the ten required attacks as executable probes rather than by reading alone.
The evidence offered as "confirm, not trust" was confirmed, not inherited:

- Focused suites at the target revision: **249 passed** (72+72+72+33).
- Full `forseti-harness` suite at the target revision: **exit 0**, existing
  `datetime.utcnow()` deprecation warnings only.
- All four repository hooks and `git diff --check`: **exit 0**.
- Pilot receipt `C:\tmp\forseti-phase-a-selection-quotes-20260818-v0\pilot_receipt_v2.json`
  raw SHA-256 = `9e3e8d8af6c8772b7fbf23a5ad8fbf26960edd7c66878ada2632d734f6286503`,
  **matching** the commission.
- Blind-quality design matches the sealed mapping: six identical-arm
  calibration pairs plus primary/mirror comparisons on three targets, with
  hydration candidate winning both A and B positions.

One material gap in that evidence, found by reading the sealed specs: **all
three pilots ran with `protected_evidence_ids: {}` and no `admit_unresolved`.**
The pilot therefore exercises none of the protected-lane, nominated-unresolved,
or cap-reservation behavior the two owning documents make their strongest
claims about. The blind-quality result is about quote enrichment on selected
rows and carries no evidence for the lane machinery.

## Findings

Severity and confidence are priority labels only. `patched` means a fix is in
the returned diff; `open` means closure needs a decision the delegate does not
own.

### F-01 `quote_unavailable` conflated two different facts, and both owning documents named the wrong one — critical / high / patched (visibility only)

`finalize_quotes` accepted `quote_status: quote_unavailable` whether or not a
source body existed, and the artifact row recorded nothing that separated the
two. Both owning documents attributed the status to a missing body:
contract v39 said "Missing bodies produce a typed `quote_unavailable`", and the
completion path said "Missing bodies remain `quote_unavailable` beside the
normalized meaning."

Evidence, from the sealed production pilots (not a synthetic case): **all four
`quote_unavailable` rows across `hydration_artifact_v2.json` and
`reaction_artifact_v2.json` had their body hash recorded in the matching
`quote_body_sha256` map — every body was present.** Zero of four matched the
documented cause. The three reaction rows are the highest-value customer
evidence in the run: the Sephora row reporting severe dryness, peeling,
swelling and pain, and two TikTok audience rows reporting burning lips. A
reader of that artifact would conclude the source text was unavailable when it
was in hand and the extraction simply produced nothing.

This is the fitness bar "no admitted evidence silently disappears" failing at
the display layer for exactly the rows that matter most.

Patched: every output row now carries `source_body_present`; both documents now
state both causes; the artifact `output_boundary` names the distinction.
**Not patched:** whether a body-present `quote_unavailable` should retry, fail,
or surface a reason code is an owner decision.

- `minimum_closure_condition`: a reader of the artifact can tell an absent body
  from an unproductive extraction, and no owning document claims otherwise.
- `next_authorized_action`: CA adjudication; then an owner decision on whether
  a body-present `quote_unavailable` is an acceptable terminal state.

### F-02 A lane reservation can reserve a group that then displays no row of that lane — critical / high / open

`_select_groups` reserves one *origin group* per lane (support, counter, quiet,
unknown engagement, safety, costly behavior) when origins exceed the cap.
`_display_members` then chooses that group's one or two displayed rows on
entirely separate criteria and never learns why the group was reserved.

Executable evidence: an origin holding a strong support row, a quiet support
row, and the **only counter row in the entire selection**. The group is
correctly reserved by the counter predicate — and then displays
`candidate_a1/support` and `candidate_a2/support`. Relations visible anywhere in
the final display: `['support']`. The counter is gone from the presentation
while the reservation reports success.

The same hole exists under the cap: when all groups are displayed, a group with
a counter can still display two support rows, because `_display_members` only
consults its `distinct` list when its `quiet` list is empty.

This directly refutes contract v39's "The selector preserves support, counter,
one distinct quiet item when present, unavailable engagement, and explicitly
nominated safety or costly-behavior lanes" and the completion path's "Counter,
quiet, unknown-engagement, safety, and costly-behavior lanes cannot be silently
crowded out."

Reported without a code patch: the fix requires choosing what the single second
display slot does when a group is reserved for counter but also holds a quiet
row — displace the quiet row, or open a third slot. That is a presentation
policy the owner sets, not a defect with one correct answer. Both documents
were corrected to describe origin-level reservation truthfully in the interim.

- `minimum_closure_condition`: either a reserved lane is guaranteed a displayed
  row of that lane, or every document stops claiming lane preservation in the
  display.
- `next_authorized_action`: owner decision on the second-slot policy, then a
  re-commissioned bounded patch.

### F-03 Operator nominations that could not resolve were silently dropped — major / high / patched

Three nomination paths disappeared without any signal, while the fourth
(`admit_semantic_refs`) correctly raised `failed_rehydration_lookup`:

- `admit_unresolved` naming a `source_id` absent from `sources` — probe returned
  no error and a candidate count unchanged from the un-nominated baseline.
- `protected_evidence_ids` naming an evidence ID that is not admitted — no
  error, and **no** candidate carried a protected lane.
- A misspelled lane key (`safety_critical` rather than `safety`) — filtered out
  by `if key in {"safety", "costly_behavior"}` with no error.

A safety lane nominated by an operator could therefore be entirely absent from
the run while every stage reported success. Note the repository's own test
fixture nominated `retailer_review:6` in cases with only four evidence rows —
the silent drop was live in the test suite itself and invisible because it
raised nothing.

Patched: all four nomination paths now fail closed, and malformed nomination
rows raise `selection_spec` instead of being skipped by an `isinstance` filter.

- `minimum_closure_condition`: no operator nomination can be absent from a run
  that reports success.
- `next_authorized_action`: CA adjudication of the returned guards.

### F-04 Unresolved candidates were stamped as a protected lane and outranked all real customer evidence — major / high / patched

`_candidate_rows` gave every `admit_unresolved` candidate
`"protected_lanes": ["unknown"]`. `"unknown"` is not a lane — the spec reader
filters `protected_evidence_ids` to exactly `{safety, costly_behavior}` — but
`_global_priority`'s first sort key is `0 if row.get("protected_lanes") else 1`.

Consequence, confirmed by probe: an unresolved placeholder row whose
`normalized_meaning` is a *disposition reason string* ("axis could not be
resolved for this evidence row"), not a customer statement, sorts into the top
priority tier alongside genuine safety rows, ahead of every ordinary support and
counter row, and becomes its origin group's representative and first displayed
row — displacing a real customer quote. The quote stage then asks the model to
find a source substring expressing that disposition reason.

Patched: unresolved candidates now carry only the protected lanes actually
nominated for them. Latent rather than live — no pilot used `admit_unresolved`,
so no production output changes.

- `minimum_closure_condition`: `protected_lanes` carries only nominated lanes,
  and a placeholder row cannot outrank real customer evidence.
- `next_authorized_action`: CA adjudication; separately, an owner decision on
  whether nominated-unresolved rows deserve a reserved lane of their own (they
  now have none).

### F-05 "Bundle verification" never verified bundle content — major / high / patched

`prepare_evidence_selection`'s `bundle_verification` boundary compared two
*declared* strings: `bundle["bundle_sha256"]` against
`packet["source_bindings"]["bundle_sha256"]`. Neither was ever checked against
the bundle's actual content. An evidence body edited in place, with the declared
hash left untouched, passed verification and its text became the accepted
"exact quote" — the exact stale-file/wrong-bundle-hash attack the commission
named.

The repository already owns this primitive: `_verify_stored_hash(bundle,
field="bundle_sha256", label="bundle")` in `semantic_evidence_integration.py`,
used at seven call sites. The one module whose entire purpose is binding quotes
to bundle bodies was the one that did not use it.

Proof the check was absent: the test fixture set `"bundle_sha256": "b" * 64`
against real content and the whole suite passed.

Patched: `_verify_bundle` content-verifies the bundle where it first enters the
trust boundary. Verified safe against production — all three sealed pilot
bundles, including the 121 MB `bundle_v5_method_v7.json`, pass the new check
(their declared hash already equals the canonical recomputation), at ~1 s cost
once per prepare. Deliberately *not* added to `load_selection_sources`, whose
`bundle_file_sha256` pin already carries the proof forward; repeating it there
would add cost with no new detection.

- `minimum_closure_condition`: a quote cannot be sourced from a body the bundle
  hash does not cover.
- `next_authorized_action`: CA adjudication.

### F-06 A body swapped after the quote manifest was accepted; the recorded body hash was never enforced — minor / high / patched

`finalize_relations_prepare_quotes` records `quote_body_sha256` per selected
row, and `finalize_quotes` never read it — it re-derived bodies from `sources`
and validated the quote against whatever was there. Probe: substituting every
body between the two stages and returning a substring of the substituted text
was accepted with no error.

Scope, stated honestly: the runner path is not exposed, because
`load_selection_sources` pins `bundle_file_sha256` and the runner binds
`quote_manifest.selection_manifest_sha256` to the selection manifest. This was a
dead receipt and a library-level hole, not a live runner defect.

Patched: `finalize_quotes` now rejects a body whose hash differs from the
recorded one, and rejects a selected row the manifest recorded no hash for.

- `minimum_closure_condition`: the recorded body hash gates the quote it was
  recorded for.
- `next_authorized_action`: CA adjudication.

### F-07 Venue normalization was an exact-host allowlist, so host variants split one publisher across sections and ordering buckets — major / medium / patched

`_source_venue` matched `{"reddit.com", "old.reddit.com"}`,
`{"tiktok.com", "m.tiktok.com"}` and similar exact sets, falling through to the
raw hostname otherwise. Confirmed fall-throughs: `np.reddit.com`,
`new.reddit.com`, `sh.reddit.com`, `redd.it`, `vm.tiktok.com`, `vt.tiktok.com`,
`smile.amazon.com` each became **its own venue**.

This is not cosmetic. `source_venue` is part of the round-robin bucket key, so a
split publisher takes a double share of the cap. Measured on the repository's
own 20-row fixture: baseline displayed venues
`{amazon: 2, reddit: 3, sephora: 3, tiktok: 2}`; moving three Reddit rows to
`np.reddit.com` produced `{amazon: 2, np.reddit.com: 3, reddit: 1, sephora: 2,
tiktok: 2}` — **Sephora silently lost a display slot to a cosmetic URL
difference**, against a fitness goal that specifically wants retailer evidence
visible.

Latent, not live: production refs in all three pilots are `old.reddit.com`,
`www.reddit.com` and `www.tiktok.com`, all covered by the old table.

Patched: `VENUE_HOST_SUFFIXES` matches a registered domain and any subdomain of
it, plus `redd.it`. A lookalike host (`notreddit.com`) is still not absorbed,
and the `source_venue_basis` distinction is preserved.

**Deliberately not patched:** regional Amazon marketplaces. `amazon.co.uk` is
already treated as `amazon` while `amazon.ca` and `amazon.de` are not — an
inconsistency, but whether marketplaces are one commercial venue is an owner
call, not a lookup-table bug.

- `minimum_closure_condition`: one publisher cannot occupy more than one venue
  bucket because of a host variant.
- `next_authorized_action`: CA adjudication; owner decision on regional
  marketplaces.

### F-08 Engagement ordering silently misread and mis-ranked source-native values — major / medium / patched in part

Three separate defects in `_numeric_engagement` / `_bucket_priority`, all
matching the commission's named "most plausible false green":

1. **Partial parse.** The regex `^\s*([0-9]+(?:\.[0-9]+)?)\b` returned `1.0`
   for `"1.2k points"` and `1.0` for `"1,234 points"` — ranking a 1,200-point
   post below a 5-point one, silently, with no error.
2. **Negative scores ranked below unknowns.** The sort term
   `-(numeric if numeric is not None else -1)` maps an unavailable value to
   `+1` and a `-30` score to `+30`, so a downvoted Reddit row sorted *below*
   rows with no engagement data at all. Confirmed ordering:
   `900, 2, 0, unavailable, -30`.
3. **Unhandled mapping shapes return `None` silently.** A `Mapping` raw value
   with any `engagement_kind` other than `sephora_helpful_votes` returns `None`
   with no signal, collapsing an entire bucket to lexical `candidate_id` order
   — indistinguishable from genuinely unavailable engagement.

(1) and (2) are patched: a numeric token must now parse whole or be treated as
uncomparable, and uncomparable values rank last on their own sort term
regardless of sign. Verified against every real production value —
`'922'`, `'599'`, `'1 point'`, `'368 points'`, `'295 points'`, `'45'`,
`'2 points'` all parse identically to before.

(3) is **reported, not patched**: whether an unrecognised native shape should
raise or degrade to unordered is a fail-loud-versus-fail-soft policy the owner
sets. The Sephora `{negative, positive, total}` handling itself is correct —
confirmed that only `positive` orders the bucket, that an inconsistent total
raises `missing_engagement`, and that the raw object reaches the artifact
byte-unchanged.

- `minimum_closure_condition`: no engagement value is ordered by a number the
  source did not state, and an unreadable shape is distinguishable from an
  absent one.
- `next_authorized_action`: CA adjudication; owner decision on (3).

### F-09 An exact quote has no substance floor — minor / high / open

`finalize_quotes` accepts any substring of the body. Confirmed accepted as
`quote_available`: `" "` (a single space), `"."`, and `"e"`. Combined with the
acknowledged residual that relevance is not machine-checked, a structurally
perfect artifact can present a single punctuation mark as a customer's verified
quote.

Reported, not patched: any minimum (length, word count, overlap with the
normalized meaning) is a threshold the owner must set, and the commission is
explicit that runtime must not use lexical overlap as truth. The artifact
`output_boundary` now states that exactness is verified and relevance is not,
so the gap is at least visible to a downstream reader.

- `minimum_closure_condition`: a quote that cannot carry meaning cannot be
  presented as verified customer evidence.
- `next_authorized_action`: owner decision on the substance bar.

### F-10 `presentation_cap_insufficient` is unreachable — minor / high / open

`_select_groups` runs six `reserve()` calls for `truth_support`, each appending
at most one group, then raises `presentation_cap_insufficient` if
`len(selected) > cap`. With `MAX_TRUTH_GROUPS = 10` the guard can never fire.
It is a dead failure path that reads as protection against
"more protected groups than available slots" — the commission's attack 4 —
while providing none. Left in place; removing it or lowering the cap is an owner
call.

### F-11 Duplication and coverage debt — minor / medium / partly patched

- `_compact` is copied verbatim from `phase_a_evidence_consumer`, which this
  module already imports four private helpers from. `__import__("re")` was
  called inline inside a sort-key helper rather than importing `re` at module
  scope (patched as part of F-08).
- Otherwise the module *is* a reasonable smallest-complete extension: it
  consumes the existing packet, adds no second evidence authority, and creates
  no parallel runner ceremony. Attack 10 does not otherwise land.
- Test coverage did not reach most of the commissioned attack surface. At
  fe2bee78 there was no test for `admit_unresolved`, protected-lane reservation
  actually reserving, the unknown-engagement lane, multiple sources or packet
  lineages, manifest tampering, stale files, `body_identity_mismatch`,
  `duplicate_quote_result` / `foreign_quote_result` / `quote_order_mismatch`, or
  the runner overwrite guards. The "249 passed" figure is real and does not
  cover these. The patch adds 18 tests across F-03 through F-08; the rest remain
  uncovered.

## Considered And Defended

- **Candidate accounting under mutation.** Missing, duplicate, foreign, and
  reordered relation rows each fail closed at their own named boundary.
  Confirmed on the real reaction pilot: all 61 candidates retained as
  dispositions with 14 displayed.
- **Creator laundering.** `creator_authored` cannot receive `support` or
  `counter`; the check is deterministic and precedes selection. TikTok audience
  comments keep a separate `source_role`, so they never merge with creator rows
  in the grouping key.
- **Two sources sharing one packet.** Raises `duplicate_candidate_id` rather
  than double-counting — fails loud, correctly.
- **Windows source refs.** Fall through cleanly to evidence-ID token matching.
  Confirmed on real Amazon, Revolve and Sephora rows carrying `C:\...` refs and
  on non-URL refs like `sephora:review:272258322`.
- **Raw engagement preservation.** Literal strings and the Sephora vote map
  reach the artifact unchanged; no cross-platform score is computed anywhere.
- **Source-native ellipsis.** Preserved when exact; an inserted ellipsis is
  rejected as non-contiguous.
- **Two rows sharing one quote.** Accepted, and legitimately so — distinct
  origins can carry identical boilerplate.
- **Determinism and idempotence.** Candidate ordering, group iteration, reserve
  ordering and the round robin are all deterministic; repeated finalization
  reproduces the artifact byte-for-byte. Runner overwrite guards are present on
  every output (though untested — see F-11).
- **`model_api_calls: 0`.** A hardcoded literal rather than a measurement, but
  true: the module makes no calls and imports no client.

## Patch And Validation Evidence

Patched four of the five commissioned targets. `run_semantic_evidence_integration.py`
needed no change and was not touched.

```text
 docs/workflows/phase_a_customer_evidence_completion_path_v0.md |  30 ++--
 forseti-harness/judgment/phase_a_evidence_selection.py         | 145 +++++++++++----
 forseti-harness/tests/unit/test_phase_a_evidence_selection.py  | 171 ++++++++++++++++--
 forseti/.../forseti_semantic_evidence_integration_contract_v0.md |  66 +++++---
 4 files changed, 336 insertions(+), 76 deletions(-)
```

Contract v39 prose was corrected in place rather than bumped to v40: v39 is
introduced by the commit under review and has never been an accepted published
version, so correcting it before it lands is the smaller and more truthful move.

Validation after the patch:

- Focused selection/consumer/semantic suites: **267 passed** (249 baseline plus
  18 new tests). Zero failures.
- Full `forseti-harness` suite: rerun after the patch, **exit 0**, no failures
  or errors; the same pre-existing `datetime.utcnow()` deprecation warnings as
  the unpatched baseline.
- `check_retrieval_header.py --changed --strict`, `check_repo_map_freshness.py
  --changed --strict`, `check_placement.py`, `check_map_links.py --strict`,
  `git diff --check`: all **exit 0**.

**Production replay — the strongest available check that the patch changes
nothing it should not.** All three sealed pilots were replayed end-to-end
through the patched code using their recorded model responses (zero provider
calls, no historical output modified):

| pilot | bundle content check | `candidate_inventory_sha256` | `labeled_inventory_sha256` | `selected_rows_sha256` | row-field drift |
| --- | --- | --- | --- | --- | --- |
| hydration (13 candidates) | pass | match | match | match | 0 |
| reaction (61 candidates) | pass | match | match | match | 0 |
| finish (2 candidates) | pass | match | match | match | 0 |

Group counts are unchanged (`10/0`, `10/1`, `1/0`). The only artifact
difference is the added `source_body_present` field and two added
`output_boundary` lines. `source_body_present` sits on the final artifact only —
it is outside every manifest hash, which is why the selection and quote
manifests reproduce exactly.

That replay is also the evidence for F-01: it is where all four
`quote_unavailable` rows reported `source_body_present: True`.

## Residual Risk

- F-02, F-09, F-10 and the third limb of F-08 remain open by design; each needs
  an owner threshold or policy, and inventing one would have been the delegate
  substituting its judgment for the owner's.
- The patch is delegate-authored capability work. Per
  `.agents/workflow-overlay/delegated-review-patch.md`, cross-vendor discovery
  covers the review of the pre-existing diff, **not** the lines this reviewer
  wrote. Those lines carry mechanical verification (267 tests, four hooks, the
  three-pilot hash-identical replay) plus CA adjudication, and that limitation
  belongs on the durable disposition.
- Lane behavior remains unproven on real data: no pilot exercised
  `protected_evidence_ids` or `admit_unresolved`, so F-03 and F-04 are closed
  against synthetic cases only.
- The commission's own accepted residuals stand unchanged: 823 of 836 hydration
  candidates were not provider-relabeled, provider and blind judge were
  same-vendor, and quote relevance remains a quality-adjudication obligation.

No `NEEDS_ARCHITECTURE_PASS`. The design is sound; the defects are guard-level
and presentation-policy-level, not structural.
