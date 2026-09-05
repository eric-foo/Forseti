# Forseti bloat cut and dogfood — 2026-09-05

```yaml
retrieval_header_version: 1
artifact_role: Dated implementation dogfood comparison
scope: Recoverable artifact retirement, duplicated helper and authority cuts, and a rejected CSB reading-route trial.
use_when:
  - Checking what the repository bloat cut removed and preserved.
  - Interpreting or reproducing the three-case token and latency experiment.
authority_boundary: retrieval_only
```

Retain the recoverable artifact retirement, shared acknowledgement/optional-fact
helpers, and three authority-mirror cuts. Reject the added CSB reading routes:
their preparation costs increased in both Understanding cases, and the frozen
quality checker did not establish equivalent quality. This is a storage and
maintenance reduction with no claimed overall token or runtime speed gain.

Baseline is `6d62b05aef99d541110b818157ec0ca10b85c305`. The tested reading-route
candidate is `6371e82fdb873cf41a8b172ac81cf2d3546f8292`. That intermediate commit
is experimental evidence, not the final accepted route. Before integrating main, the CSB README, Prompt Structure and playbook were
restored exactly to the experimental baseline. Main then advanced to
`70f295561e20e9dc478985041850cf2b5e6bcfc1` with separate collection-completion
changes. Those were merged unchanged; this lane makes no net change to those
three route documents against that integration base. The adjacent
`forseti_bloat_cut_dogfood_2026_09_05_evidence.json` preserves native usage,
source identities, original checker failures, frozen cases/checker/collector,
recovery observations and retained behavior hashes. Open it only to inspect
this experiment; it is not a normal task read pack. Current publication and CI
state belong to the PR containing this record, not this dated report.

## Retained cuts and their boundaries

| Surface | Change | Preserved boundary |
| --- | --- | --- |
| Historical migration review payload | Retire 451 normalized snapshots and `diff_u80.patch`: 452 files, 11,108,304 logical bytes. | Keep the packet recovery README, nine manifests, original review prompt and findings. Recover exact committed bytes from the pinned base. |
| Three duplicate screenshot aliases | Retire 1,366,546 bytes across three `visible_chrome_attempt` images. | Corresponding cited `visible_chrome_before_download` images have identical Git blobs and remain. |
| Runner acknowledgements | Ten runners use the existing consumption module's shared `ack_packet`. | Lane namespaces, collision/idempotence behavior, failure propagation and persisted acknowledgement bytes remain equivalent. |
| Optional-fact parsing | Reuse existing `source_capture.cli_support.build_optional_fact`. | Keep the runner import name/API and existing parser behavior. |
| Repeated workflow authority | Replace the review-template list, JSG status assertion and CSB acquisition sequence mirror with owner pointers. | Registry owns template IDs; dated JSG owner/conductor resolves state; playbook owns acquisition order. The manifest sequence key stays a list. |

Gross retirement is **455 files and 12,474,850 logical bytes**. The code and
necessary tests remove a further 4,207 LF-normalized bytes (8,071 bytes from
implementation code alone). Final tracked census, including this report and its evidence: **4,059 files /
180,850,472 bytes**, versus **4,512 / 193,047,491 bytes** at the integration base:
**12,197,019 bytes (6.32%) net less**. The original experimental baseline
contained 4,512 files / 193,018,389 bytes; the integration-base comparison
excludes the unrelated changes that landed during this task.
These are logical Git blob sizes summed by path, not filesystem allocation.
Git history is retained; identical blob objects were already shared. This
does not reclaim old Git objects or promise a smaller full-history clone.

The live 21.7 MB inbox stays because current capture records depend on it.
No blanket history move, dependency replacement, new cache, monitoring job,
maintenance registry or permanent measurement gate was added. The existing
efficiency collector and comparison API supplied the measurements.

## Recovery dogfood and historical discrepancy

The pinned review archive restored **all 462 members, including 451 snapshots**
with equal file sets, lengths and Git blob identities. A deliberately corrupted
blob was rejected. Exact retirement targets were checked as tracked and
unchanged before deletion; screenshot aliases were compared with retained
copies. The nine manifests and historical findings body remain unchanged.

Two preparation probes stopped before deletion. Default `git archive` obeyed
the host's `core.autocrlf=true` and changed line endings; per-command
`git -c core.autocrlf=false archive` recovered the exact blobs. Recovery then
exposed a pre-existing defect: all five original SHA256 pins disagree with
both the original packet commit `8df13cbd2ee3b655d94e315dc8cf1e258c3a9c70`
and the pinned recovery revision. Independent verification confirmed those two
commits contain the same relevant bytes. Common newline/encoding variants did
not reproduce the old pins.

The historical assertion that the pins matched is therefore **not reproduced**.
Original pin text/findings were preserved; dated notices in the packet README,
review prompt and report disclose the discrepancy. The original prompt's
`BLOCKED_SOURCE_CONTEXT` gate remains binding. Exact current blob recovery does
not rehabilitate that old review certification. Resolve the discrepancy or
commission a fresh review before relying on it. The recovery command and
owning next-source pointers are in
`docs/review-inputs/capture_spine_core_migration_adversarial_artifact_review_v0/README.md`.

## What the token and latency test actually exercised

Eighteen fresh Desktop agent turns exercised **read-only CSB commission
preparation**: three baseline/candidate pairs for each case below. The same
frozen task prompts began at the CSB README, using high effort and the observed
model `gpt-6-astra`. Dispatch alternated B1/C1, C2/B2, B3/C3, with up to four
concurrent leaves on one Windows host. Native elapsed time covers the entire
leaf task, including source reading and tools. All 158 response attempts were
counted, with complete reported usage coverage and no collection issues.

- Standalone: backtest tea-note perfume board preparation, dated source and
  answer-surface cutoff handling, lake-first coverage planning and classifier
  boundary. It did not generate and validate a full standalone board.
- Acquisition: fresh Summer Fridays Understanding Acquire & Seal commission
  planning, CO0–CO3 duties, capability/dispatch prerequisites, semantic
  integration before sealing and no automatic synthesis. No evidence capture,
  actor fan-out or acquisition seal was executed.
- Synthesis: fresh-context commission entry with a hypothetical mechanical seal
  pass but missing adjudicated semantic review, plus duplicate-origin and
  engagement claim limits. No source-backed company report was synthesized.

Descriptive **per-arm medians** follow. Percentages are ratios of those medians,
not median paired effects. Every pair has the same direction for total tokens
and elapsed time within its case.

| Case | Total tokens, baseline → trial | Native elapsed, baseline → trial |
| --- | --- | --- |
| Standalone board preparation | 364,443 → 291,447 (-20.0%) | 151.398s → 137.502s (-9.2%) |
| Understanding acquisition preparation | 517,516 → 784,309 (+51.6%) | 220.385s → 281.132s (+27.6%) |
| Understanding synthesis preparation | 351,369 → 639,959 (+82.1%) | 147.443s → 216.474s (+46.8%) |

Tokens are summed native response usage, including reused input context.
Cached input is part of input tokens, not an extra additive category. Median
noncached input changes were 40,212 → 38,150; 51,203 → 86,601; and 40,508 →
63,906, respectively. The evidence also retains input, cached input, output,
response counts, individual pairs and paired changes. Independently calculated
metric medians need not add together. No billing or dollar cost was measured.
Concurrency and three pairs per case limit latency precision and generality.

## Why the trial was rejected

The frozen quality-gated comparison is **inconclusive**, with 18/18 checker
failures retained. Its source whitelist admitted only five files while the
task required broader project pointers; it also demanded exact literal strings
not specified by the task. For example, all six synthesis outputs said
`synthesis_allowed_now=false`, yet explanatory blocked-status strings failed
literal equality with `blocked`. Acquisition controller/ledger explanations
and stage descriptions similarly failed literal/keyword checks.

These are measurement defects, not grounds to relabel the runs as passes.
The checker was not changed after observing outputs. Its earlier synthetic
selftest (three representative passes and nine seeded rejects) did not detect
these false negatives. Some differences may be substantive: one baseline
acquisition plan omitted the subject-specific calibration quarantine carried
by candidates. There is no comprehensive semantic-equivalence claim, and no
quality-adjusted win can be inferred from the token table.

The original static reading estimate assumed baseline agents read whole
documents. Actual baseline agents selected relevant sections. The trial
required broader prompt/owner reads for Understanding preparation; smaller
prescribed section-byte totals did not predict smaller actual task usage.
This is an observed explanation supported by source-read traces, not an
isolated causal estimate. Both arms also differ in the three authority mirrors,
so their individual token effects are unmeasured. The trial's two substantial
resource increases and missing quality evidence give no reason to retain its
extra instructions. All three reading-route files were restored exactly.

## Verification and propagation

Code verification observed 33 focused tests and 309 broader lane/contract tests
passing (overlapping groups, not an asserted disjoint total). The shared helper
was checked against all ten original executable AST bodies with only namespace
substitution. Persisted acknowledgement output was compared with direct
`append_ack` for two namespaces; collision, bounded error, unexpected error
and recheck propagation cases were exercised. Existing inventory generation
reported unchanged; the TikTok content pin was refreshed without changing its
output-neutral policy version. The 47 broader-test warnings were existing
`datetime.utcnow` deprecations.

CSB validation observed 109 passing unit tests and a passing validator selftest.
The complete standalone Prompt Body and append-only changelog content remained
unchanged during the trial. After rejection, all three route documents matched the experimental
baseline; after main integration they match the integration base. The retained
manifest owner anchor resolves. Strict harness
coupling preflight passed; this is not a full-suite claim. The PR's required
CI is the broad integration gate and must be read at its actual final head.

The first pre-push attempt was blocked by two legacy document-shape findings:
the historical prompt put its unchanged `review-report` mode on a separate
line, and the historical output lacked the explicit review-use boundary.
The declaration was made inline and the dated notice now states that findings
are decision input, not approval, validation, mandatory remediation or patch
authority. The historical findings body and unresolved hash gate stay intact.

Direction-change propagation is bounded to three existing owner pointers:
review registry rather than a duplicate ID list; dated JSG owner/conductor
rather than a frozen mirror; CSB playbook rather than a repeated acquisition
sequence. The README, dispatcher, playbook, registry, conductor and relevant
maps were checked as consumers; rejected trial routes do not become authority.
Retirement notices reconcile the packet router and two historical consumers.
No new standing synchronization step or actor-carried receipt is required.

The project conditional review trigger was evaluated against the final diff.
No specific uncovered failure class was identified that defeats the bound
preservation/equivalence checks and required CI; review routing is `not_needed`.
The proposed route whose quality had no adequate oracle was rejected. This is
not a claim that a delegated review ran or that the historical review became
valid. A future retry of reading-route optimization first needs a quality
oracle accepting semantically valid plans, frozen before new observations;
this task does not install or commission that follow-up.
