# Phase A Hydration Final-Contract Quote Quality Adversarial Code Review v0

```yaml
retrieval_header_version: 1
artifact_role: Delegated cross-vendor reviewer findings report
scope: >
  Cross-vendor adversarial review of the context-complete exact-quote prompt
  correction at 2186312c and of the matched serial/parallel hydration proof
  receipt dc9420c0, including an independent deterministic replay of both arms.
use_when:
  - Adjudicating whether the v51 context-complete quote contract is proven.
  - Reusing the fifteen-origin hydration pack or its parallel relation transport.
  - Checking what the matched serial/parallel run does and does not establish.
authority_boundary: retrieval_only
review_provenance:
  authored_by: OpenAI Codex home lane (implementation at 2186312c)
  reviewed_by: Anthropic Claude Opus 5 via Claude Code, direct repository access
  de_correlation_bar: cross_vendor_discovery
  access_mode: >
    reviewer-owned branch claude/phase-a-final-contract-quote-review created at
    exact target revision 2186312c1c5bd70068995dc32b8e871a468dcbce
  dispatch: >
    Retired after adjudication; historical prompt path
    docs/prompts/reviews/phase_a_hydration_final_contract_quote_quality_delegated_adversarial_code_review_patch_prompt_v0.md
    is pinned in Git at 5f67b1c38b244e1f6000950b9a5a726fe4233b95.
  reviewed_diff: 390f7bdcf290e6929f541fe63fd50f5060c7236c..2186312c1c5bd70068995dc32b8e871a468dcbce
  findings: 6
review_use_boundary: >
  These findings are decision input for home-lane adjudication. They are not
  approval, not validation, not mandatory remediation, and not executor-ready
  patch authority. The reviewer patch is advisory and was neither pushed nor
  merged.
non_claims: >
  This report does not claim population prevalence, commercial pull, buyer
  willingness to pay, cross-provider latency generality, or independent
  semantic adjudication of all 836 relation decisions. No provider call was
  made by the reviewer; every re-derivation below is deterministic.
```

## Home-Lane Adjudication

The home lane verified the reviewer commit and accepted its disclosure patch as
`607c7620`. The findings were adjudicated as follows rather than inherited as a
block:

- **FF-01 — accepted, with a scale restriction.** The 56-of-836 cross-run
  disagreement and eight polarity flips are real. The adopted parallel row for
  `reddit:1apzs1v:post::batch-0463-unit-0002` is substantively correct under the
  bounded hydration claim; the serial `counter` label is not. The current
  parallel artifact remains usable as the measured hydration pack, but this one
  workload does not prove that a fresh run will label every displayed row the
  same way. Broad scaling remains restricted until a selected-row relation
  confirmation pilot can detect a displayed support/counter disagreement
  without relabeling all 836 candidates or materially erasing the measured
  latency gain.
- **FF-02 — accepted and closed at the deterministic consumer boundary.** A
  quote ending in an alphanumeric character now fails
  `quote_boundary_incomplete` when its exact source occurrence continues with
  whitespace and another alphanumeric character. There is no automatic retry.
  Replaying the adopted parallel response produced the byte-identical artifact
  SHA-256 `8afd0096a1c08a1885c751e93348324bf3488c2f58413871cc5240abe5a27380`;
  replaying the serial response failed at the new boundary, as intended.
- **FF-03 — accepted as a disclosed ceiling residual, not patched.** The
  220-character limit can force a choice between a grammatically complete start
  and all material conditions. The adopted exact quote keeps the material
  `bitter cold` condition but begins headless. Widening the cap would change the
  model-facing task and therefore requires a fresh matched provider run; the
  existing receipt is not reused to claim that untested change.
- **FF-04 — modified.** The 312-character reformulation/recommendation span is a
  genuine ceiling residual. The omitted Pink Sugar color clause is not a
  hydration qualification and does not reverse `feels hydrating and
  comfortable`; forcing it into a hydration quote would add off-axis detail.
  The judge rubric was broader than the contract on this point, so its flag is
  retained as review evidence but not accepted as a product defect.
- **FF-05 and FF-06 — accepted.** The receipt hash derivation and the measured
  latency decomposition are now stated explicitly in the owning workflow.

No quote prompt, response schema, provider output, production artifact, cap, or
packet version changed in this adjudication. The courier prompt was retired
after use; Git history preserves it.

```yaml
home_adjudication:
  status: accepted_with_scale_restriction
  reviewer_patch: accepted_as_607c7620
  runtime_closure: quote_boundary_incomplete
  provider_calls: 0
  adopted_parallel_replay: pass_byte_identical
  serial_replay: rejected_at_quote_boundary_incomplete
  next_material_move: selected-row relation confirmation pilot
  broad_scale_ready: false
```

## Route And Preconditions

```yaml
author_family: OpenAI
reviewer_family: Anthropic
cross_vendor_condition: satisfied
repository_access: direct
route_status: proceeded
```

Target revision `2186312c1c5bd70068995dc32b8e871a468dcbce` exists and is a
descendant of `origin/main` at `31855948`; it is not merged. The branch
`codex/phase-a-hydration-pack-cap-pilot` has advanced by exactly one commit
(`5f67b1c3`, the courier prompt), which the dispatch `stale_if` clause permits.

All four exact targets verify. The declared `sha256` values are Windows
working-copy bytes, not repository blob bytes; every target file's
LF-normalized bytes hash to the blob at the target revision, and the working
copies in the authoring worktree reproduce the four declared digests exactly.

| target | declared sha256 | observed |
| --- | --- | --- |
| `forseti-harness/judgment/phase_a_evidence_selection.py` | `7239f033…3a7b21c0` | match |
| `forseti-harness/tests/unit/test_phase_a_evidence_selection.py` | `6b7434f0…34509e0a53` | match |
| `docs/workflows/phase_a_customer_evidence_completion_path_v0.md` | `42ebdbea…3e801ba1c0` | match |
| `forseti/…/forseti_semantic_evidence_integration_contract_v0.md` | `e50ee7ac…4a32a8156f` | match |

Receipt raw SHA-256 re-derives as
`dc9420c0a43e07fa6df66b1b45b8a193759f6908b2ba7ac8c4b7fbc117c6dde3` — match.

## Findings

### FF-01 — the two arms disagree on 6.7% of relations, including a displayed polarity flip

```yaml
severity: high
confidence: high
location: proof receipt `payload.accepted_residuals` and docs/workflows/phase_a_customer_evidence_completion_path_v0.md:426-441
```

**Failure mechanism.** The serial and parallel relation prompts and schemas are
byte-identical (verified: all three `prepared/batch_000N_prompt.txt` and
`_schema.json` pairs hash identically across arms, and both arms share one
`batch_manifest.json` at `61afad55…`). The receipt discloses the resulting
provider variation as one sentence: "provider relation variation changed one
selected origin and produced 13 versus 12 long-body quote rows." Re-deriving
the two `labeled_inventory` blocks from `serial/quote_manifest_v5.json` and
`parallel/quote_manifest_v5.json` shows the variation is far wider:

- **56 of 836 candidates (6.7%) received a different relation** between arms.
- Disagreement classes: `counter→adjacent` 21, `adjacent→exclude` 15,
  `adjacent→support` 10, `counter→support` 7, `support→adjacent` 2,
  `support→counter` 1.
- **8 of those are direct support↔counter polarity flips.**
- Arm relation mixes differ materially: serial `counter 488 / support 288 /
  adjacent 57 / exclude 3`; parallel `counter 461 / support 302 / adjacent 55 /
  exclude 18`.

One flip reaches the customer-facing pack. Semantic unit
`reddit:1apzs1v:post::batch-0463-unit-0002` carries the **identical** normalized
meaning in both arms — "Lip Butter Balm initially hydrates and leaves this
customer's lips softer than Laneige Glowy Balm." — and is displayed as:

- serial: `relation: counter`, `reason_code: differing_customer_experience`,
  `display_label: "Differing customer experience"`
- parallel: `relation: support`, `reason_code: matching_customer_experience`,
  `display_label: "Matching customer experience"`

The exact quote is byte-identical in both. A buyer reading the two packs sees
the same source sentence presented as corroboration in one and as
counterevidence in the other. Nothing in `_validate_relation_response` can
detect this: any of the four relations is structurally valid for any candidate,
and in positional mode the `reason_code` is derived *from* the returned relation
via `POSITIONAL_REASON_CODE_BY_RELATION`, so a flipped relation silently
manufactures a matching, plausible-looking display label.

**Why this matters to the bound outcome.** The receipt's stated reason for
adopting the parallel arm is latency plus blind-judge preference over the prior
accepted pack. Neither establishes relation stability. The pack's support/counter
balance — the thing `_select_groups` draws the fifteen origins from — is the
least stable part of the pipeline, and the receipt's residual wording
("changed one selected origin") reads as a selection-level nuisance rather than
a 6.7% labeling instability with polarity consequences.

**Minimum closure condition.** Record the measured cross-arm relation
disagreement (count, polarity-flip count, and the displayed flip) as an explicit
accepted residual and reversal trigger. This is a disclosure correction; it
changes no model-facing bytes and needs no provider recheck.

**Next authorized action.** Home lane accepts the disclosure patch below, or
states why 6.7% relation variance is tolerable for a customer-facing pack.

### FF-02 — the serial final arm violates contract v51's mid-phrase rule in 3 of 13 long-body quotes

```yaml
severity: high
confidence: high
location: forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md:950-960; proof artifact serial/artifact_v5.json
```

**Failure mechanism.** Contract v51 states the selected span "must retain a
nearby material qualification and cannot stop mid-phrase." Scanning both final
artifacts against their own source bodies (defect = quote's last character is
alphanumeric **and** the body continues with a word), the serial final artifact
stops mid-phrase three times:

| semantic unit | len | quote ends | body continues |
| --- | --- | --- | --- |
| `reddit:1rh75s2:o7wnksb::7wn-hydration` | 219 | `…and pricey lip balms in` | `" general. Except for…"` |
| `retailer:amazon_rendered_reviews:R3TOQKI1BIM0T3::u05` | 217 | `…feel so much better in this bitter` | `" cold, and I love the tint…"` |
| `retailer:sephora_product_group_reviews:205416444::hydrating` | 219 | `…heavier at night for the very cold winter` | `" months."` |

The parallel arm has **zero** such stops. The R3TOQKI1BIM0T3 case is the worst:
its own normalized meaning is "The balms restore moisture and make the
reviewer's lips feel better **in bitter cold**", and the serial span truncates
at `"in this bitter"` — it stops mid-phrase *and* fails to substantiate the
timing condition v51 requires it to substantiate, in the same 217 characters.

**Why this falsifies the proof framing.** The workflow doc records the run as
"Both arms produced fifteen truth origins, seventeen exact quotes, zero
unavailable quotes, and no influence origin" and the receipt's `wrong_cause`
block records `final_context_complete_prompt: "PASS: 17/17 exact quotes…"`.
Both statements are literally true and both are conformance-blind: `17/17` counts
exactness and availability, which deterministic code already enforces, not the
context-completeness the v51 change was written to obtain. Measured against the
rule the commit actually adds, the final one-call prompt achieved **13/13 in
parallel and 10/13 in serial** — a 23% mid-phrase-stop rate in one of the two
arms of its own proof run. The receipt cites that same run as the evidence for
`ADOPT_FINAL_CONTRACT_FOR_HYDRATION`.

**Minimum closure condition.** The proof narrative must record the measured
per-arm conformance rate rather than only the availability count. Optionally
(owner decision, see FF-03) add the deterministic clause-boundary guard.

**Next authorized action.** Accept the disclosure patch below; decide separately
whether a deterministic guard is wanted.

### FF-03 — the v51 boundary rule is asymmetric and has no tie-break at the 220 ceiling

```yaml
severity: medium
confidence: high
location: forseti-harness/judgment/phase_a_evidence_selection.py:181 (QUOTE_PROMPT); contract v51 lines 950-960
```

**Failure mechanism.** The new rule constrains the span's *end* absolutely
("cannot stop mid-phrase") and its *start* only for one narrow case ("must not
start with an unresolved pronoun … when the combined span fits"). It says
nothing about a start that is headless for any other reason, and it supplies no
precedence when start-completeness and component-completeness cannot both fit.

The adopted parallel artifact demonstrates both gaps on the same row.
`retailer:amazon_rendered_reviews:R3TOQKI1BIM0T3::u05` is exactly 220
characters and begins:

```text
have tried glossy products before that said they were moisturizing but…
```

The preceding body character is the subject `I`. The span is therefore a
grammatically headless fragment — but it is contract-compliant, because
"have" is not a pronoun and the pronoun rule's own escape ("when … the combined
span fits") applies: `"I have tried … in this bitter cold"` is **222**
characters, two over the ceiling. The only complete-start alternative,
`"I have tried … My lips feel so much better"`, is 202 characters but drops
"in this bitter cold" — the usage condition the same rule requires.

So at 220 characters this row has **no** span that satisfies v51 as written.
Serial resolved the conflict one way (kept `I`, truncated `bitter`) and produced
the FF-02 mid-phrase stop; parallel resolved it the other way (kept the
condition, dropped `I`) and produced a headless quote. Both mirrored judges
independently named this defect class a critical error — against the *losing*
artifact each time ("begins mid-thought", "begins mid-sentence … leaving the
subject … unclear") — and neither flagged the surviving instance in the winner.

**Minimum closure condition.** Either (a) state the precedence explicitly
(which requirement yields when the ceiling binds) and record headless starts as
a disclosed residual of the 220-character ceiling, or (b) widen the start-side
rule beyond pronouns. Option (b) materially changes the model-facing quote
instruction and therefore **requires a fresh matched provider recheck**; the
current receipt cannot be inherited as proof of a changed prompt.

**Next authorized action.** Owner decision between (a) and (b). This report
patches nothing in the contract's normative text; that is a doctrine change and
belongs to the home lane.

### FF-04 — the context-complete instruction did not close the brevity-clip class it was written to close

```yaml
severity: medium
confidence: high
location: forseti-harness/judgment/phase_a_evidence_selection.py:181 (QUOTE_PROMPT); both final artifacts
```

**Failure mechanism.** The new instruction says "Do not optimize for brevity:
when the necessary source wording fits, retain it instead of clipping to a
merely related phrase" and "Include any nearby same-evidence companion meaning
that materially qualifies or reverses it."

Semantic unit `reddit:19eo5it:kje19h9::batch-0409-unit-0003` (Pink Sugar, the
mixed praise/criticism family) returned a **161**-character span in *both* arms:

```text
I find it very hydrating and comfortable to wear and I’m obsessed with the flavor lol I personally can’t complain but I can agree that they’re probably overhyped
```

The immediately preceding clause in the same sentence is
`"It doesn’t give much color to the lips but "`. Including it yields a
**204**-character span — 16 characters of headroom under the ceiling. The model
left 59 characters of budget unused, began the span mid-clause after a
contrastive `but`, and dropped a nearby same-source qualification that fits.
The round-1 mirrored judge independently listed exactly this as a critical error
against the winning artifact: "Artifact B: the Pink Sugar quote omits the nearby
low-color outcome."

The judge's rubric ("nearby qualifications") is broader than the contract's
("a nearby *material* qualification", read against the normalized meaning). A
low-colour remark does not qualify a hydration meaning, so the artifact arguably
satisfies the contract while failing the rubric that the receipt uses as its
adoption evidence. That divergence is the finding: **the run's quality gate and
the run's contract are not measuring the same thing**, and the receipt reports
only the gate's verdict.

**Blind preference does not waive it.** Two objective omissions were flagged
against the winner in round 1 (Pink Sugar low-colour; reformulation
recommendation). Both survive into the adopted artifact and neither appears in
`accepted_residuals`. The generic residual that is recorded — "may omit adjacent
non-hydration commercial detail from the same review" — does not cover the
reformulation case, which is squarely about the formula/hydration claim.

**Defence that does hold.** The reformulation omission is structurally
unclosable: spanning from `"the old formula was the best"` through
`"…because of the new formula."` requires **312** characters. No contiguous
≤220 span carries both the old-formula overnight baseline and the explicit
recommendation. That one is a genuine ceiling residual, not a prompt defect.

**Minimum closure condition.** Record both judge-flagged objective omissions
against the adopted artifact as accepted residuals, and record that the
judge rubric is broader than the contract's materiality test. Strengthening the
instruction instead would require a fresh matched provider recheck.

### FF-05 — `payload_sha256` is not derivable with the repository's canonical hasher

```yaml
severity: low
confidence: high
location: C:\tmp\forseti-phase-a-hydration-final-contract-20260820-v0\experiment_result_v1.json:3
```

**Failure mechanism.** The receipt's `payload_sha256`
(`fc3d96cf…dcfc31fe`) does not reproduce under `_canonical_json_sha256`, the
repository's canonical JSON hash used by every manifest in this pipeline
(sorted keys, compact separators), which yields `9b099be8…cad2ab8a`. The digest
is in fact sha256 over `json.dumps(payload, sort_keys=False,
ensure_ascii=False, separators=(",", ":"))` — insertion-order compact JSON.

A reviewer re-deriving the payload hash by repository convention gets a
mismatch and can wrongly conclude the receipt was edited. The digest is also
insertion-order dependent, so a semantically identical payload with reordered
keys hashes differently.

**Minimum closure condition.** Record the derivation rule alongside the digest,
or emit the payload digest with `_canonical_json_sha256`.

### FF-06 — the 47.491% figure is the observed total delta, not the concurrency-attributable share

```yaml
severity: low
confidence: high
location: receipt `payload.decision.reason` and `payload.comparison.latency_saved_percent`
```

**Failure mechanism.** Every timing number in the receipt re-derives exactly
(see "Economics re-derivation" below), and the workflow doc correctly words the
figure as "The observed parallel latency reduction was 47.491%." The receipt's
`decision.reason`, however, states "actual concurrency reduced provider wall
time 47.491%", attributing the whole delta to concurrency.

Decomposing the 352,392.900 ms saving against serial active time
(742,019.840 ms):

- concurrency-attributable (parallel arm's own relation-call sum 564,522.048 ms
  minus its critical path 219,278.402 ms): **345,243.646 ms = 46.528%**
- net per-call provider variance (relation calls 50,863.461 ms in parallel's
  favour, quote call 43,714.207 ms against it): **7,149.254 ms = 0.963 pp**
- sum reconciles to 352,392.900 ms exactly.

Concurrency accounts for 98.0% of the measured saving, so the direction and
magnitude are sound; the attribution sentence is 0.963 pp optimistic.

**Minimum closure condition.** Word the decision reason as the observed total
delta, or carry the decomposition. No rerun needed.

## considered_and_defended

Attacked candidates that held under deterministic re-derivation.

**Committed provenance regenerates the run byte-for-byte (attack 7) — held.**
Working from the committed implementation at the target revision and the two
bound source files, the reviewer independently re-ran
`load_selection_sources` → `finalize_batched_relations_prepare_quotes` →
`finalize_quotes` over the stored relation responses for both arms. Results:

- serial and parallel `manifest_sha256` reproduce the stored
  `quote_manifest_v5.json` digests exactly;
- serial and parallel regenerated quote prompts hash to
  `5d76f9bf…bac100e8` and `661f86ce…70d581`, matching the receipt's
  `quote_prompt_file_sha256` for each arm;
- both `*_committed.*` files are byte-identical to their `*_v5.*` counterparts
  (prompt, manifest, and schema, both arms), confirming
  `committed_prompt_regeneration: all true`;
- both replays yield 836 candidates, 15 truth origins, 0 influence origins,
  17 exact quotes, 0 unavailable;
- the two bound source files hash to the receipt's `packet_file_sha256`
  `51e8f2ea…62980b2` and `bundle_file_sha256` `fdb0803e…f8ae7ff6`;
- both artifact files hash to the receipt's recorded digests.

No dirty-parent or stale-manifest claim survives: the implementation blob is
identical at `f6060eb5` and `2186312c`, and the reviewed commit adds only the
receipt paragraph, the six prompt-substring assertions, and the contract text.

**Transport and source integrity (attack 4) — held.** Re-running the named
falsifiers against the committed implementation reproduced every claimed
boundary, and each reached the *intended* boundary first:

| falsifier | observed boundary |
| --- | --- |
| swapped equal-size batch responses | `relation_batch_identity` |
| missing named row | `missing_candidate_result` |
| same-length one-character quote mutation | `quote_exactness` |
| over-length quote mutation | `quote_overlength` |
| quote-manifest field edited without rehash | `manifest_verification` |
| body hash rebound in a rehashed manifest | `body_identity_mismatch` |

**Creator laundering — not exercisable on this workload.** All 836 candidates
are `truth_support` (784 `community_post`, 52 `retailer_review`); the packet
contains no `creator_authored` evidence, so the
`creator_customer_laundering` boundary could not be driven from this data. The
guard itself is present and unconditional in `_validate_relation_response`, and
the artifact's `influence_group_count` of 0 is a true zero, not a suppressed
count. This is a coverage residual of the workload, not a defect.

**Bundle-level integrity below `load_selection_sources` — held.** Mutating
`bundle_sha256` in an already-loaded source object does not fail
`finalize_quotes`, but that path is unreachable: `load_selection_sources` pins
`bundle_file_sha256` and `packet_file_sha256` over whole-file bytes before any
finalizer runs, `_bundle_bodies` re-checks per-unit `source_artifact_id` and
`source_ref`, and each selected row's body is hash-bound in the quote manifest.
The `_verify_bundle` docstring states this inheritance explicitly.

**Value policy is not bypassed by the batched transport — held.**
`finalize_batched_relations_prepare_quotes` hardcodes `value_policy=False` for
the per-batch validation, which reads as a bypass. It is not:
`prepare_evidence_selection_batches` refuses a value-axis spec outright, and the
batched finalizer's second-stage call into
`finalize_relations_prepare_quotes` re-derives `_uses_value_policy` from the
embedded selection manifest and re-validates the merged result under it. A
forged value-axis batch manifest fails at `value_reason_code` because positional
reason codes are not in `VALUE_REASON_RELATIONS`.

**`display_label` cannot make an irrelevant quote acceptable (attack 3) — held
mechanically, with a residual.** `finalize_quotes` never consults
`display_label` when accepting or rejecting a quote; acceptance is exactness,
the 220-character ceiling, a two-alphanumeric floor, the short-body-in-full
rule, and null-on-unavailable. `_display_label` additionally refuses any label
over 80 characters or containing an internal relation word. The residual is
that `display_label` *is* still shipped to the model in
`QUOTE_PROMPT_COLUMNS`, and the prompt then spends a sentence telling the model
to discount it. Removing the column would delete the risk class outright and is
strictly smaller, but it changes model-facing prompt bytes and so would require
a fresh matched recheck; it is offered as an owner option, not patched here.

**One-call prompt robustness across behaviour families (attack 2) — largely
held.** The commission asks whether locate-expand-verify overfits the two
false-unavailable examples. It does not: this single workload exercises five
distinct families, and the one-call prompt returned an exact quote for every one
of them —

- comparator: `reddit:1apzs1v:post` (Laneige), `reddit:1rh75s2:post`
  (older Vanilla Beige), `R3TOQKI1BIM0T3` (other glossy products);
- third-person report: `R2TFKCU5P4OSLM` ("Staple for my teenage daughter.
  She loves…") — antecedent correctly retained;
- temporal/usage condition: `205416444` (day or night, cold winter months);
- formula change: `189249561` (old versus new formula);
- mixed praise/criticism: `19eo5it:kje19h9`, `1ln2gsa:n0c7l9q`.

Seventeen of seventeen returned available, zero unavailable, against a prior
strict prompt that falsely returned unavailable for two under-220 spans. The
receipt's claim that the broad "self-contained" prompt was correctly rejected
also checks out: the 181-character span
`"the old formula was the best … it's not moisturizing."` is a real under-ceiling
span that the rejected prompt discarded. Robustness therefore holds; FF-03 and
FF-04 are boundary-quality gaps within a working design, and neither justifies a
retry surface.

**Blind judging is genuinely mirrored (attack 5) — held.** Both round-3 judge
prompts are 95,862 characters; `ARTIFACT_A` of round 1 is byte-identical to
`ARTIFACT_B` of round 2 and vice versa. Round 1's `ARTIFACT_B` matches the
parallel final artifact's full quote set, confirming the receipt's declared
mappings and the `decoded_result`. The comparison is parallel-final versus the
*prior accepted pack* — the serial final artifact was never judged. The receipt
does not overstate this. It does mean the choice of parallel over serial rests
on latency alone, while on the one row where the two arms are objectively
comparable (`R3TOQKI1BIM0T3`) the unadopted serial arm has the cleaner sentence
start and the adopted parallel arm has the complete condition.

**Economics re-derivation (attack 6) — held.** Every figure re-derives from the
raw `turn.completed` usage records in the twenty event JSONL files. Logical
tokens are `input + output` per call throughout: reasoning is never added and
cache is never subtracted (all `cached_input_tokens` are 0 in this run, so the
policy is stated but untested here).

- serial totals `212,485 / 35,529 / 28,773 / 248,014` — all four reconcile;
- parallel totals `210,275 / 34,901 / 28,252 / 245,176` — all four reconcile;
- serial active provider time `281,401.042 + 164,536.323 + 169,448.144 +
  126,634.331 = 742,019.840 ms`;
- parallel relation critical path: earliest start `15:46:24.7256588Z`, latest
  completion `15:50:04.0040603Z` → `219,278.402 ms`, plus quote
  `170,348.538 ms` → `389,626.940 ms`;
- delta `352,392.900 ms`, `47.491035%`; token delta `-2,838`, `-1.14429%`;
- experiment overhead: 12 calls, `378,228 + 30,123 = 408,351` logical tokens,
  reasoning subset `25,261` — all reconcile, and the overhead set is exactly the
  20 observed event files minus the 8 production-arm calls, so **no provider
  call in the directory is unaccounted for**.

Filesystem mtimes corroborate the timestamps independently to within ~100 ms.
The three parallel relation calls started within 50 ms of one another and fully
overlapped; the three serial calls are strictly sequential with ~19.5 s
orchestration gaps between them. Those gaps are *excluded* from the serial
total, which biases the comparison against the parallel arm: an end-to-end
relation-stage measure would put the reduction near 50.1%, not 47.5%. The
"active provider wall time" framing is therefore conservative and honest, and
the token comparison is correctly labelled descriptive — the arms produced 13
versus 12 long-body quote rows, so the −1.144% delta cannot be a concurrency
saving.

**Validation obligation — run.** All commands were run on the reviewer branch at
the target revision before any patch:

```text
python -m pytest -q forseti-harness/tests/unit/test_phase_a_evidence_selection.py forseti-harness/tests/unit/test_phase_a_evidence_consumer.py forseti-harness/tests/unit/test_semantic_evidence_integration.py   -> 338 passed
python -m pytest -q forseti-harness                                                                                                                                                                              -> 5566 passed, 7 skipped
python -m py_compile forseti-harness/judgment/phase_a_evidence_selection.py                                                                                                                                       -> ok
git diff --check                                                                                                                                                                                                 -> clean
```

The 338-test focused count and the 7 existing skips match the receipt's
`validation` block. One caveat: the *first* full-harness run failed
`forseti-harness/tests/unit/test_creator_audience_queue.py::test_concurrent_claim_has_one_winner_and_expired_lease_is_recoverable`
with a `DataLakeRootError` from `forseti-harness/data_lake/root.py:621`. The
test passes in isolation and the immediately repeated full run passed clean.
This is a pre-existing concurrency/lease flake unrelated to the reviewed diff,
recorded here only so a future full-suite failure is not mistaken for a
regression from this commit.

**The new tests are wording pins, not behaviour tests — noted, not filed.** The
six added assertions in
`test_phase_a_evidence_selection.py:396-401` check that six literal phrases
appear in the generated quote prompt. They cannot fail for any prompt that
contains those phrases, however the surrounding instruction reads, and no
deterministic code enforces the v51 requirements they describe. This is not
filed as a separate finding because the properties are model-side and largely
undecidable — but it is why FF-02's 3-of-13 serial violation passed every gate
in the repository. One sub-property *is* decidable, and is offered below.

## Optional deterministic guard (owner decision, not patched)

A single clause-boundary rule in `finalize_quotes` would have caught all three
FF-02 defects: reject when the quote's last character is alphanumeric **and**
the source body continues with optional whitespace followed by a word
character. Evaluated against all 34 rows of both final artifacts, it rejects
exactly the 3 serial mid-phrase stops and produces **zero** false positives —
it correctly passes the parallel arm's `"…in this bitter cold"` (followed by a
comma) and every sentence-terminated span.

It is not applied here for one reason: it converts a silent quality defect into
a hard run failure, and the commission bars adding a standing quote-retry
stage. Under the serial arm's own responses this run would have failed closed.
That is the correct direction under "preserve real failure visibility", but the
operational consequence is an owner call, not a reviewer call.

## Patch

One commit on the reviewer branch, touching one file, changing no model-facing
bytes and no runtime behaviour. It records the measured facts behind FF-01,
FF-02, FF-04, FF-05, and FF-06 in the workflow document that already owns the
proof narrative. The contract's normative text is deliberately untouched: the
FF-03 and FF-04 rule questions are doctrine changes for the home lane, and any
change to the quote instruction invalidates the current receipt as proof.

## Residuals this review does not close

- No provider call was made; the semantic correctness of the 836 relation
  decisions and the 17 quote choices is not independently adjudicated here.
- The judge is same-vendor with the provider, and this is one hydration
  workload — the receipt already carries both residuals.
- Whether 6.7% cross-arm relation variance is acceptable for a customer-facing
  pack is a product judgment, not a code defect.
- Latency generality across providers, `p95` behaviour, and lower reasoning
  effort remain unmeasured.

```yaml
review_summary:
  route_status: proceeded_cross_vendor
  target_revision_verified: true
  receipt_hash_verified: true
  findings_count: 6
  patch_commit: reviewer branch claude/phase-a-final-contract-quote-review (not pushed)
  validation: focused 338 passed; full harness 5566 passed 7 skipped; py_compile ok; git diff --check clean
  residuals: no provider rerun; same-vendor judge; one workload; relation-variance tolerance is an owner judgment
  review_routing_status: routed
  recommendation: patch_before_acceptance
  report_path: docs/review-outputs/adversarial-artifact-reviews/phase_a_hydration_final_contract_quote_quality_adversarial_code_review_v0.md
  user_action_needed: >
    Adjudicate FF-01 and FF-02 disclosure, then decide FF-03 (ceiling tie-break
    wording versus a widened start-side rule) and the optional deterministic
    clause-boundary guard. Any change to the model-facing quote instruction
    requires a fresh matched provider recheck; the current receipt cannot be
    inherited as proof of a changed prompt.
```
