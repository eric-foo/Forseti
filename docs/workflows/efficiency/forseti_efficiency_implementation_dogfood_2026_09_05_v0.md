# Forseti efficiency implementation and dogfood — 2026-09-05

```yaml
retrieval_header_version: 1
artifact_role: Dated implementation dogfood comparison
scope: Five accepted efficiency changes, local before/after observations, and limits against baseline 22a5868d.
use_when:
  - Checking what the September efficiency implementation changed and demonstrated.
  - Reproducing its local comparisons or deciding whether an unmeasured benefit needs further work.
authority_boundary: retrieval_only
open_next:
  - docs/workflows/efficiency/forseti_efficiency_implementation_dogfood_2026_09_05_evidence.json
  - docs/workflows/efficiency/forseti_repo_efficiency_audit_2026_09_05_v0.md
```

## Outcome and currentness

The accepted five-change plan is implemented: transcript-local quote indexing,
three-file workflow-rule reconciliation, shared/pruned checker discovery,
four current generated-output ignore rules, and lazy ASR model reuse in all
three batch entrypoints. No lake lookup, global cache, model/prompt change,
historical deletion, or new standing validation step was added.

Baseline: `22a5868d46e89b51ccc0d293d95b5bf226d95cae`. The companion evidence records
the exact before/after LF-normalized hashes of all eleven changed behavior
sources, raw observations, failure probes, and one-off reproduction scripts.
It is an on-demand evidence archive, not a default source-loading pack.
Publication and CI state belong to this change's PR and must be read there;
this dated record does not certify a later checkout or model version.

## Before and after

All timings below are local wall-clock medians, not production estimates.

| Boundary and sample | Before | After | What the comparison establishes |
| --- | --- | --- | --- |
| Full transcript parse: 5,000 cues, 100 mentions with ratings, two rejected items; five alternating pairs | 4.773s | 0.0338s | Identical serialized mentions and rejections; shared cue indexing eliminates repeated normalization/allocation. |
| Map checker, identical live repository tree; five alternating pairs | 2.680s | 2.189s | Identical stdout, stderr and exits; seeded C2/C4 workloads read each admitted file once instead of twice. |
| Silver checker, identical live repository tree; five alternating pairs | 9.302s | 9.542s | No demonstrated full-check latency improvement; identical outputs and exits. |
| Silver discovery alone; five alternating pairs | 64.34ms; 694 directory-scan calls | 44.66ms; 311 calls | Same 497 sorted producer paths; scans inside excluded subtrees fall from 72 to zero. Discovery saves about 20ms, a small portion of the full checker. |
| Real ASR: cached small/int8, speech/silence/speech, fresh-process AB/BA pairs | 18.335s wall; 40.203s process CPU; three model loads | 14.776s wall; 33.703s CPU; one load | All cues, postures and metadata match. Constructor CPU falls from 9.539s to 3.219s; synchronous and generator CPU remain similar. |
| Four generated-output path families | All four probes unignored | All four ignored | Two adjacent source/fixture controls remain trackable; legacy ignore behavior remains. |

The first ASR measurement used shared-process alternating batches and observed
a regression: median **16.486s to 19.500s**, with a broad after range of
12.974–21.280s. That result is retained. The follow-up isolated every arm,
removed progress output from timed sections, and measured constructor, eager
transcription and lazy segment-consumption CPU separately. Both balanced pairs
improved, supporting reuse for the observed workload. The precise cause of the
first timing reversal remains unproven; the later result is not a universal
latency guarantee.

ASR used locally generated speech and silence, cached models, and offline mode.
No external capture, paid model call, or production lake write was used.
The evidence preserves audio hashes, outputs, software version and generation
recipe. Different default speech voices need newly identified input hashes.

## Behavior and failure checks

- Transcript regression: twelve mention/rating pairs scanned cues 24 times
  before the patch; the new one-scan assertion failed on that baseline and
  passes after it. A second parse rebuilds after transcript mutation. Empty
  work, malformed input, repeated/cross-cue quotes, invalid first-match
  timestamps, and fabricated rating quotes retain their intended outcomes.
- ASR tests cover zero loads for empty/skipped work, one load for multiple
  successes, session/configuration isolation, release of model references,
  missing optional dependencies, initialization/decode recovery, actual runner
  injection, and failure without a record or acknowledgement. Content pins
  were refreshed without changing derivation-policy versions.
- Seeded invalid header and inline links inside an admitted file still produce
  the same two findings. Strict modes exit 1; advisory modes remain advisory.
  Header-line limits, exemptions, debt counts, producer membership and internal
  error handling retain their existing contracts. Real map runs retain 37
  annotated nonresolving entries; Silver retains its existing unresolved-member
  note at `forseti-harness/ecr/lake.py:136`.
- Workflow scenario checks establish source agreement: bounded durable prompts
  and eligible compact commissions do not inherit blanket receipts or named
  phases; five small decisive sources do not force handoff. Full orchestration,
  genuinely lost context, missing authority, and required portable strict-claim
  evidence retain their existing boundaries. These are source-based scenario
  checks, not a live LLM token experiment.

Focused pytest groups observed: **54 passed** for transcript extraction;
**89 passed** for ASR/session/caller and policy-pin checks; **20 passed** for
inventory, cadence coverage and no-LLM imports; **16 passed** for actual checker
files; **48 passed** for existing hook internal-error handling. Groups are not
an asserted disjoint total. Existing ASR/cadence warnings concern
`datetime.utcnow`. Required CI remains the broad integration gate.

## Scope, propagation, and limits

The workflow unit updates `source-loading.md`, its `validation-gates.md` mirror,
and the shared prompt behavior contract. Their existing prompt-orchestration
owner is unchanged. A targeted search found none of the four retired trigger
formulations in the overlay/template consumer set. JSG status, template
inventories and historical provenance pins were not folded into this change.

Each change reaches its active consumer: mention and rating checks share the
index; strict/check/report routes share discovery; catch-up, cadence and both
creator entry paths own ASR sessions. One-shot ASR remains compatible. The
ignore patch changes matching only and untracks or deletes no artifact.

Token savings, billed cost, production throughput, long-running batch memory,
other model configurations, and general task latency remain unmeasured. Model
references are released at session exit; immediate native memory reclamation
is not claimed. Samples are small and filesystem cache, scheduling and machine
background load were not fully controlled. Silver's discovery improvement is
retained as lower traversal work, with no full-check speedup claim.

Under the project-owned conditional Success Implement review rule, the
completion disposition is `not_needed`: baseline differential outputs,
seeded failures, real-model output comparison and the unchanged workflow owner
supply independent oracles for the changed boundaries. No specific remaining
shared-assumption failure class was identified that commissions the separate
review-and-patch lane. This is a routing judgment, not a review claim.

The root sandboxed speech-generation route stalled and was terminated after
leaving a zero-byte output. A bounded approved SAPI child generated the fixture;
the checker ACL failure used a hash-bound approved replacement. Both failures
and their mitigations are recorded; neither ordinary route is claimed repaired.
