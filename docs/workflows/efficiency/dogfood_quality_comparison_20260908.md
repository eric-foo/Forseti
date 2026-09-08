# Dogfood quality comparison — 2026-09-08

```yaml
retrieval_header_version: 1
artifact_role: Bounded workflow experiment evidence
scope: Dogfood result assessment under existing, revised, and source-first guidance.
use_when:
  - Reviewing the dogfood quality overlay candidate and its evidence limits.
authority_boundary: retrieval_only
```

## Outcome and authority

The quality-focused candidate is implemented on `codex/dogfood-quality-20260908`
from baseline `bb4e0c812e87a794fe6df8a89c19610e0c076e25`. It is not established
as a reliable quality improvement. The different-vendor review was returned and
adjudicated on 2026-09-08; required CI remains a landing gate. Consult the lane's
current Git/PR state for publication and landing status.
The controlling source is `.agents/workflow-overlay/validation-gates.md`,
**Model-backed dogfood quality**; routing and prompt preflight point there.
This record is experiment evidence, not additional standing instructions.

Owner authorization: prioritize dogfood quality over efficiency, implement the
smallest complete process change, and compare it. The success contract was to
detect a material semantic error despite consumer acceptance, preserve valid
behavior, and distinguish replay, recovery and autonomous execution. Meaning
remains LLM-owned; no new runtime judge, label rules, hook or registry was added.

## Method and frozen evidence

Two separate native gpt-5.5/high contexts assessed the same actual saved outputs
for interest (repeat 2) and hydration (repeat 1), eight source rows each. The only
initial intervention was the dogfood guidance excerpt. Both received the same
claim-support contract and complete source-bearing envelopes, without evaluator
labels. Production consumer functions freshly rederived both saved points.
The evaluator criteria were frozen before calls. This is actual closeout
assessment, not hypothetical plan selection or fresh product generation.

Baseline guidance came from the pinned commit above. The first candidate added
meaning-versus-consumer checks, matched-comparison limits and recovery honesty.
Both assessments failed the target signal, so neither was discarded or retried.
A third, distinct experiment withheld generated classifications and consumer
status until source-based judgments were sealed. This tested answer exposure;
it was not a matched repeat of either prior run. The candidate was amended to
require reconciliation rather than adopting independent labels automatically.

All artifacts are at `C:/tmp/forseti-dogfood-quality-comparison-20260908`:
`compare.py`, `packet.json`, `consumer-proof.json`, `common-context.txt`,
`evaluator-only.json`, `freeze.json`, the `before` and `after` native attempts,
`source_first.py`, `source-first/freeze.json`, its native attempt, and
`comparison-result.json`. These local raw evidence pointers may be unavailable
on another host; absence is not verification. The result file SHA-256 is
`e4fd941652f073fd1a195fee9eab0c41aec534a2fc373da4516f334165d8be4c`. The unchanged original oracle is
`C:/tmp/forseti-contextual-meaning-20260908-cb76-confirmation2/oracle.json`,
SHA-256 `fb75b702efce374721f05084fb1c3f556ad4a8e199149239230c737711c4a405`.

## Observed comparison

| Signal | Existing guidance | First candidate | Source-first check |
| --- | --- | --- | --- |
| Detect false counter for interest/no view | Missed; accepted finding | Missed; explicitly defended counter | Detected; assigned adjacent |
| Preserve hydration distinctions | Preserved in assessment | Preserved in assessment | Introduced secondhand-report false support |
| Distinguish shared output from replication | Explicitly limited | Explicitly limited | Not tested by this call |
| Distinguish host recovery from A's autonomous success | Did not explicitly resolve A | Explicitly denied A autonomous success | Not tested by this call |

Material defect: “I use Instant Angel because it is what is provided at work;
I have no view on trying or buying it.” The bounded proposition is expressed
interest in trying or buying. No view establishes neither side; the original
confirmation's `counter` is unsupported. Both consumer replays passed despite
this error, proving the semantic signal is not merely schema acceptance.

The source-first check matched 13/16 frozen labels. It caught that defect but
assigned support to hydration row_02, the sister's experience reported by an
author who never used the product. The source-local actor scope and original
wording prevent donating that experience to the author. It also assigned
adjacent rather than exclude to two packaging-only rows; both labels are
nondirectional, but the strict mismatches remain recorded.

Author reconciliation retains the original hydration judgments and changes
the interest assessment to diagnosed semantic failure. This reconciliation is
an author judgment against source and frozen oracle, not an independently
validated gain. No product response was edited, restamped or promoted as fixed.

## Candidate scope, cost and residuals

The overlay now connects contrast selection, source-first semantic checking,
consumer outcomes and honest conclusion. Existing decision-routing and prompt
preflight pointers were updated. Top-level instructions, overlay entrypoint,
source-loading and repo map already route to these owners; no competing dogfood
section was found by the scoped stale-language search. No global skill changed.

No mandatory extra source-first run is installed. Delegated review narrowed the source-first
clause from a required step to an available move, guarded by source
reconciliation and a preservation check on its own output, because its single
trial paired one exposed defect with one invented support judgment. It stays
scoped to semantic correctness and adds no universal extra review cycle, fixed
repeat count or new artifact. Its demonstrated benefit is exposing one missed
defect; its observed risk is an independent checker inventing another. It must
not become a veto. When selected, it still costs an independent assessment and
source-based reconciliation; optional does not mean cost-free.

Reported native usage across three completed attempts: 65463
input tokens, including 4224 cached input, and
4773 output tokens. Root conversation usage is additional.
All three receipts report usage; hidden provider retry usage is not separately
observed. No efficiency improvement is claimed.

The initial matched comparison failed the semantic improvement signal. The
source-first experiment supports only a narrower diagnostic benefit, with a
material preservation failure before reconciliation. It does not establish
reliability, broad transfer, better case commissioning, autonomous execution,
or product correctness. No further model calls or policy landing are implied.
The success-implement checkpoint produced an operator-couriered Anthropic review
at `896098f552de812599786a439202125530d4f856`. The author kept its narrowing
of the mandatory source-first clause and corresponding evidence-record repairs
(F1-F3). The author clarified the conditional cost and reopening language;
cosmetic findings were left unchanged. This accepts a bounded assessment option
and honesty/preservation rules, not a demonstrated quality improvement.

The earlier `cold_operability_signal_pr_backtest_2026_08_07_v0.md` rejected a
standing extra consumer run when its admission bar and regression protection
were unmet. This candidate does not supersede that rejection. Delegated review
resolved the source-first clause's recurring scope by making the check optional
rather than required, given the preservation failure here; do not infer
permission to install a universal independent-checker requirement from this
experiment. Reconsider the scope when new evidence could change that decision,
such as a controlled comparison showing that skipping the optional move misses
material defects and that using it improves decisions without unacceptable
preservation regressions. A defect need not reach production to supply that
evidence; one skipped check alone does not establish a universal requirement.
