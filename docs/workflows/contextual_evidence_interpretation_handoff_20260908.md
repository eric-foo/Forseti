# Contextual evidence interpretation — continuation handoff

```yaml
retrieval_header_version: 1
artifact_role: Bounded continuation record
scope: Continue PR1569 without reconstructing the authoring conversation.
use_when:
  - Continuing contextual interpretation implementation and its review.
authority_boundary: retrieval_only
packet_version: 1
mode: max
source_loading_mode: repo-overlay-bound
created_at: 2026-09-08
```

## Goal, open decision and guard

Reduce false evidence claims while accepting ordinary contextual customer
testimony. Continue the bounded implementation's residual adjudication and
independent review; do not restart the whole study.

Open decision: whether remaining semantic failures need a bounded correction
or a separate architecture decision. Recommendation: review the actual failures
without expanding this patch into source-role/terminal-state redesign. This is
not acceptance or permission to bypass review.

The owner requests the smallest complete intervention, LLM-based meaning
judgment, preserved failures, and low token cost. No lexical classifier or
blanket public-author truth boost. Batch related dogfood cases with shared
instructions; keep baseline/treatment and independent repeats separate. Reuse
unchanged stages with exact prompt/schema/provenance checks. Do not tune frozen
expected labels or repeatedly launch broad studies.

## Binding and load contract

- Workspace: `C:/Users/vmon7/.codex/worktrees/cb76/orca`, already app-managed.
- Branch: `codex/contextual-evidence-interpretation`.
- Implementation: `4556246f78e83a88ee6e591d99649c34d5142682`.
- Baseline: `e2eb5837d1ca632da756abb948b3bf9e56e6e2e2`.
- PR: https://github.com/eric-foo/forseti/pull/1569 — draft, unmerged at writing.

Confirm, do not trust: inspect branch, HEAD, cleanliness, PR head/CI and evidence
files. This packet is a documentation-only descendant of the implementation;
resolve current HEAD. The worktree was clean before this file was added. Its
creation adds this one file, subsequently committed; no other writer remains
after handoff. Revalidate only claims affected by changed bytes.

Load outcomes: REUSE when pins match; PARTIAL_REUSE for unchanged seams;
STALE_REREAD_REQUIRED for drift; BLOCKED_DRIFT for conflicting target/writer;
BLOCKED_MISSING_PACKET for unavailable evidence. Local `C:/tmp` evidence remains
on this host, not GitHub; another host must obtain it rather than infer results.

## Inherited decisions and source ledger

The full real review 339335352 endorses barrier benefit in context: “will help”
does not automatically mean speculation. An actual untried hope stays
anticipation. Never-tried/non-use alone is not opposing use experience;
tried-and-abandoned use can be counter. Experienced “no recovery yet” can be
counter without an invented duration threshold. No expressed view is not an
opposing view.

Read AGENTS.md and `.agents/workflow-overlay/README.md` first. Owning semantics:
`forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md`.
Runtime/currentness: sibling `forseti_semantic_evidence_integration_contract_v0.md`
v123 and `docs/workflows/phase_a_customer_evidence_completion_path_v0.md`.
Compare these and changed code to implementation 4556246f. Overlay and lifecycle
facts are reread-required. This packet is continuation state, not authority.

## Implemented and verified

Run v12 selects method v14/verifier v13; authoring v5 and selection v4 use contextual
guidance. Existing single/batched/selected confirmations receive original
row-owned text; selected manifests bind IDs, body hashes and identity. Old
production selection v1/v2/v3 and historical methods/verifiers/authoring retain
prompt bytes. No new production model stage.

Implementation files: `forseti-harness/judgment/claim_meaning.py`,
`semantic_evidence_integration.py`, `phase_a_semantic_run.py`,
`phase_a_evidence_selection.py`, and
`forseti-harness/runners/run_semantic_evidence_integration.py`. Three owning
tests and four owning docs complete the change. The exact set is the Git diff
from e2eb5837 to 4556246f.

762 focused/coupling checks passed; the confirmation correction reran 255
affected tests. Required CI is green at 4556246f:
https://github.com/eric-foo/forseti/actions/runs/34202503582 . Previous full CI
reported 6578 passed/26 skipped. Five actual historical points replay
byte-for-byte: `C:/tmp/forseti-contextual-historical-replay-20260908-cb76/result.json`.

## Evidence and material limits

Start with `C:/tmp/forseti-contextual-meaning-20260908-cb76/root-adjudication.md`
for the home semantic reading, not an independent verdict.

- Initial selection: same root `report.json`; frozen oracle SHA
  `fb75b702efce374721f05084fb1c3f556ad4a8e199149239230c737711c4a405`.
  48 rows ×3 repeats/arm. Baseline confirmation 137/144; initial treatment 134/144.
  Four false-counter regressions drove the confirmation-only correction. Six
  treatment adjacent/exclude disagreements award neither side evidence but
  remain strict mismatches. One baseline whole-point rejection left 8 final
  judgments unavailable; never invent a successful artifact for them.
- Corrective packed confirmation:
  `C:/tmp/forseti-contextual-meaning-20260908-cb76-confirmation2/report.json`.
  Three calls, six findings/call, 144 judgments: 137 exact matches and 18/18
  final artifacts validated. One material false-counter remains: interest-7
  repeat2 (no view on trying/buying); six other mismatches are adjacent/exclude.
  Report SHA c4f50db8e4a1226311554aae700bdd6e7feb589558ca1aa115fd49020cdaf382.
  First responses are reused after
  exact prompt/schema equality. This changes wording AND inference packing;
  it is not isolated causal proof or a production batching implementation.
- Producer: `C:/tmp/forseti-contextual-producer-20260908-cb76/completion-receipt.json`
  and `final-row-output-index.json`. 12 calls, six valid pipelines. Real barrier
  endorsement first_hand: baseline 2/3, treatment 3/3. Experience-informed advice:
  0/3 versus 3/3. Hopes, ad attribution, non-recovery and return objects remain
  distinct. Residuals: two treatment negated non-use statements have affirmed
  polarity; one logo observation becomes context_only. No universal semantic pass.
- Formation: `C:/tmp/forseti-contextual-formation-20260908-cb76/durable-verification.json`
  and its baseline/treatment-native-results-setup2.json files. 12 compilations
  pass. Barrier final views 6/6 pass; interest 0/6 because an unrelated packaging
  report stays nonterminal in both versions. Counter attachment varies. A
  deliberately defective normalized ad claim remains contaminated input here;
  formation did not see its original text and did not repair it.

All runtimes, inputs, prompts, responses and failures remain frozen. One
selection capacity failure was recovered once. 12 formation launches failed
locally before any model response and were recovered after initializing the
isolated runtime. These are separate from semantic failures.

## Token cost and stop point

99 completed dogfood model calls consumed 2,013,769 reported input tokens,
including 597,120 cached, and 132,952 output tokens. Main/helper conversation
usage is additional and unmeasured here. The final packed check used 3 calls
and 80,004 input tokens. No more experiments were launched after that fixed
check. The owner requested a fresh-task handoff to reduce accumulated context.

## Next authorized action and lifecycle

Complete the independent different-vendor review-and-patch of the bounded diff
and failures. Home reasoning/helper mechanics are not independent review.
AGENTS.md makes this operator-courier only: author the prompt, never discover,
dispatch or spawn a reviewer. Delegate patches stay uncommitted pending home
adjudication. Use targeted checks; required CI owns broad testing. Escalate
source-role/terminal-state redesign as NEEDS_ARCHITECTURE_PASS. Keep the PR draft
until review and material outcome claims are resolved.

Review targets are the exact implementation/test/doc set above. Read the diff
by the second latency-bearing call after binding, under the overlay's delegated
review-and-patch contract and workflow-code-review. Any further probe must name
the unresolved decision it can change and use the smallest adequate batch.

## Superseded / dangerous to reuse

Initial treatment bd69ab64 and its frozen v4 prompts are development evidence,
not corrected 4556246f execution. Earlier PR1567/1565/1568 and old 36-row oracles
are historical; do not revive them or amend their scores. The broader all-axis
blind proof remains incomplete. Valid intermediate nodes, cached-token counts
and this handoff are not completed proof or review approval.
