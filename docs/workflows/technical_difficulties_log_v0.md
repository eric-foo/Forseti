# Forseti Technical Difficulties Log v0

```yaml
retrieval_header_version: 1
artifact_role: Workflow record
scope: Chronological observations of material Forseti workflow or tooling difficulties, their verified impact, corrective owner, and code or doctrine pointers.
use_when:
  - A technical difficulty materially delays a lane, repeats, or causes a corrective repository change.
  - Checking whether an observed workflow failure already has a diagnosis, mitigation, or accepted residual.
authority_boundary: retrieval_only
open_next:
  - .agents/workflow-overlay/validation-gates.md
  - docs/decisions/dev_workflow_ci_branch_protection_doctrine_v0.md
```

## Use boundary

This is an append-only operational record, not workflow authority. Each entry
records observed evidence, impact, diagnosis, corrective pointers, validation,
and residuals. The linked doctrine or implementation owns the rule and behavior.
Add a later follow-up rather than rewriting a closed entry; factual corrections
may amend the affected entry and must say what changed.

## TD-2026-07-14-001 — Published lane rebase created an unpushable history

- **Observed:** 2026-07-14, Asia/Singapore.
- **Affected lane:** PR #896, `codex/topfrag-silver-analytics`.
- **State at recording:** corrective patch prepared and locally validated on
  `codex/technical-difficulties-published-rebase-guard`; delegated review and
  merge remain pending.
- **User-visible symptom:** conflict work and lifecycle recovery added several
  minutes after the implementation and review changes were already complete.

### Verified timeline

| Event | Observed time | Evidence |
| --- | --- | --- |
| Published branch updated by ordinary push | 01:29:40 +08:00 | remote-tracking reflog for `origin/codex/topfrag-silver-analytics` |
| Rebase onto `origin/main` started | 01:30:36 +08:00 | `HEAD` reflog |
| Rebase finished after conflict resolution | 01:34:28 +08:00 | branch and `HEAD` reflogs |
| Content-neutral ancestry merge restored a pushable graph | 01:37:59 +08:00 | branch and `HEAD` reflogs |
| Reconciled branch published | 01:38:16 +08:00 | remote-tracking reflog |
| Required CI ran green | 01:38:23–01:39:40 +08:00 | GitHub PR #896 check rollup (`forseti-harness-tests`) |
| PR merged | 01:41:44 +08:00 | GitHub PR #896 `mergedAt` readback |

The recovery interval from rebase start to publication of the reconciled branch
was **7 minutes 40 seconds**. Conflict resolution (01:30:36 to 01:34:28) was real
work that a fetch-plus-merge update would also incur; the **avoidable** portion
was the content-neutral ancestry reconciliation and its republish (01:34:28 to
01:38:16, **3 minutes 48 seconds**), which existed only because a published lane
had been rebased under the no-force-push policy. The 77-second CI run was normal
required validation, not the defect.

### Diagnosis

The controlling doctrine said lanes should follow a “rebase cadence” while the
same doctrine, local protected-action guard, pre-push guard, and server branch
protection prohibit force-push. Rebasing an already-published lane rewrote its
commit identities, so its next ordinary push could not fast-forward. Conflict
resolution was real work, but the additional ancestry-reconciliation step existed
only because the documented update route contradicted the no-force-push policy.

This is repeatable. Repository reflogs show the same published-branch rebase
pattern on multiple recent lane branches. Exact conflict count and duration vary
with overlap, but the non-fast-forward outcome follows whenever a published lane
is rebased and its rewritten commits differ from the remote branch.

### Corrective ownership

- **Rule owner:**
  `docs/decisions/dev_workflow_ci_branch_protection_doctrine_v0.md` distinguishes
  unpublished branches (rebase allowed) from published branches (fetch plus merge).
- **Early enforcement:** `.agents/hooks/guard_protected_actions.py` blocks explicit
  `git rebase` and `git pull --rebase` when local Git state proves the current
  same-name branch is already published. Rebase recovery forms remain allowed.
- **Operator documentation:** `.agents/hooks/README.md` names the guard boundary,
  fail-open publication probe, and allowed route.
- **Focused validation observed:** the protected-action guard and Codex adapter
  self-tests returned `OK`; retrieval-header and DCP receipt-shape/hygiene checks
  returned no findings for the changed files; `check_map_links.py --strict`
  returned zero findings; and the full `forseti-harness` pytest suite reached
  100% with exit code 0 (seven skips, warnings only). These are local validation
  signals, not delegated review or merge state.

### Accepted residuals

- A plain `git pull` can still be affected by user Git configuration; doctrine
  therefore requires explicit fetch plus merge, while the guard only blocks
  commands it can identify without guessing.
- Opaque shell scripts, alternate harnesses without the tracked hook wiring, and
  deliberate hook bypass remain outside this local guard. Server-side no-force
  protection still prevents the unsafe publication result.
- Published-branch merges can still conflict. They preserve pushability and make
  the unavoidable conflict work visible; they do not eliminate overlap.
- Sandbox approval latency and required CI time remain separate operating costs.
  Neither was the root cause of this incident.

### Validation-environment note

Two local validation attempts failed before tests ran: `py_compile` was denied
while creating `.agents/hooks/__pycache__`, and pytest-xdist was denied while
creating `C:\tmp\pytest_rebase_guard`. ACL readback showed deny entries on the
hook cache directory, and the temp-root failure reproduced despite `C:\tmp`
being an intended writable root. The successful bounded route was
`PYTHONDONTWRITEBYTECODE=1` plus a fresh pytest `--basetemp` inside the active
worktree. No production or CI code change is justified: GitHub CI runs on Ubuntu,
the repository suite passed through the bounded local route, and changing host
ACLs is outside this repository's ownership.

### Non-claims

- Not a Silver-data, analytics, capture, or runtime defect.
- Not proof that PR #896 content was incorrect; its required CI completed green.
- Not proof that every historical rebase caused delay or conflict.
- Not validation, readiness, or merge approval for the corrective patch.

## TD-2026-07-15-001 — Cold scratch lanes hang on default shell and patch routes

- **Observed:** 2026-07-15, Asia/Singapore.
- **Affected lanes:** three isolated cold-agent runs of
  `docs/workflows/efficiency/tool_calling_dogfood_case_v0.md`.
- **State at recording:** open; repeatable mitigation observed, root cause and
  durable owner unresolved.
- **User-visible symptom:** all three runs made no filesystem change for several
  minutes until operator interruption; completed routes used 20–23 logical
  rounds versus the case's roughly five-round reference.

### Verified evidence

| Run | Default shell hung | `apply_patch` hung | Logical rounds / invocations | Final integrity |
| --- | --- | --- | ---: | --- |
| 1 | yes | yes | 23 / 41 | correct three-file patch; unrelated state preserved |
| 2 | yes | yes | 22 / 35 | correct three-file patch; unrelated state preserved |
| 3 | yes | yes | 20 / 31 | correct three-file patch; unrelated state preserved |

Trivial and task-specific default shell calls hung against the assigned
`C:\tmp` snapshots. Bounded elevated shell calls completed. The nested patch
helper also hung in every run; elevated launcher or executable attempts failed
with access denial, and all three runs ultimately used `git apply`. Fresh
operator verification confirmed the final diffs, tests, and untracked-note hash.

### Diagnosis

The failure is repeatable across three context-free agents and occurs before
task-specific reasoning can explain the delay. The effective default shell and
patch routes did not match the intended writable-scratch posture. Evidence does
not yet isolate whether the fault belongs to sandbox mediation, process startup,
the shell host, or patch-helper execution.

A secondary agent-efficiency gap compounded the platform failure: runs polled or
varied a hanging route multiple times and each first Git-patch fallback failed
atomically. Ledger review found only two to four otherwise batchable rounds per
run, so read batching was not the dominant cost.

### Corrective ownership and mitigation

- **Observed bounded mitigation:** after one bounded hang, stop the unchanged
  route; a per-operation elevated shell call restored reads and tests. When the
  patch helper remained unavailable, a checked, atomic `git apply` fallback
  completed the edit.
- **Durable owner:** unresolved external tool/harness substrate; no Forseti
  runtime or repository code owner is established by this evidence.
- **Replay source:**
  `docs/workflows/efficiency/tool_calling_dogfood_run_2026_07_15_v0.md` records
  the fixture baseline, three-run results, and rerun trigger.
- **Upgrade trigger:** rerun the unchanged three-trial case after the default
  shell or edit route changes. Do not change the case and the tool path in the
  same comparison.

### Accepted residuals

- Elevation adds approval latency and is not normalized as the default route.
- Hand-authored Git patches are an error-prone fallback; atomic check/failure
  preserved the trees in these runs but does not make the route preferred.
- Root cause remains unknown; this entry records recurrence and impact, not a
  platform fix.

### Non-claims

- Not a Forseti product, capture, data, or runtime defect.
- Not proof that every `C:\tmp` operation or every agent will reproduce the
  failure.
- Not proof that the agents themselves caused the shared initial stalls.
- Not validation or readiness of the external tool substrate.

## TD-2026-07-16-002 — Sandboxed tool completion stalls reopened after interruptions

- **Observed:** 2026-07-16, Asia/Singapore.
- **User-visible symptom:** small patch and read operations remained running for
  roughly 80 to 265 seconds despite 20-second command budgets.
- **Verified contrast:** equivalent read-only commands through per-operation
  escalation completed in 0.3 to 0.6 seconds; same-worktree atomic edits
  completed in 0.4 seconds; the Codex guard adapter self-test completed in 1.7
  seconds.
- **Patch result:** the manually stopped built-in patch changed none of its four
  intended files.

### Diagnosis and correction

The dominant observed delay was the sandboxed tool route or its result-return
lifecycle, not Git, Python, the atomic helper, or the Forseti guard runtime. The
repository cannot repair that host component. A second process defect amplified
the cost: the circuit breaker expired at the end of a turn, so an interruption
or follow-up message reopened a route already observed to be stalled.

`AGENTS.md` now keeps that circuit open for the task/thread and requires later
context to inherit the observed stall. Safe shell work may use the one allowed
per-operation escalated retry and then that working route. After a patch stall,
the same-worktree atomic exact-edit helper remains the bounded fallback. No Luna
or separate worktree is required for ordinary sequential editing.

A related enforcement defect was also corrected: the Codex adapter now inspects
patch text in `tool_input.command`, `.patch`, and `.input`, with focused coverage
for all three forms. This closes a wrong-root guard gap; it does not repair the
host patch executor.

### Accepted residuals

- Built-in `apply_patch` may still stall at the host level and remains outside
  repository control.
- Escalation remains per-operation and is not a standing permission.
- A fresh task without inherited incident context may need one observed stall
  before its circuit opens.

### Validation observed

- Two focused hook-wiring tests passed.
- The Codex adapter self-test passed.
- `git diff --check` passed for the bounded repair files.

### Non-claims

- Not proof of the product-side root cause.
- Not a host-level patch-tool repair.
- Not authority to weaken protected-action or worktree guards.


### Delegated-review addendum — circuit-state continuity (2026-07-16)

A commissioned cross-vendor delegated review confirmed one containment gap:
the inheritance rule still depended on current context reporting the stall, but
no rule required an open circuit's `sandboxed_tool_stall` record to travel in a
precompact or handoff packet. Whenever such a packet is used, a receiving lane
could therefore silently reopen a route already observed to be stalled.
`AGENTS.md` now requires the record in either packet type.

Additional accepted residuals from that review:

- Automatic compaction that drops the stall record can silently close the
  circuit; the bounded cost is one re-observed stall before it reopens.
- The adapter inspects the three known Codex payload fields (`command`, `patch`,
  `input`); an unrecognized or non-string payload shape is skipped rather than
  denied, so a future host payload-schema change would reopen the inspection gap
  until observed and patched.

```yaml
direction_change_propagation:
  doctrine_changed: >
    An open sandboxed-tool-stall circuit is now named lane state: precompact
    and handoff packets must carry the `sandboxed_tool_stall` record so a
    receiving lane inherits the open circuit.
  trigger: workflow_authority
  related_triggers: [lifecycle_boundary]
  controlling_sources_updated:
    - AGENTS.md
  downstream_surfaces_checked:
    - CLAUDE.md
    - .agents/workflow-overlay/source-of-truth.md
    - .agents/workflow-overlay/source-loading.md
    - docs/workflows/technical_difficulties_log_v0.md
  intentionally_not_updated:
    - {path: CLAUDE.md, reason: "It imports AGENTS.md and must not duplicate the circuit rule."}
    - {path: .agents/workflow-overlay/source-of-truth.md, reason: "Checkpoint packet mechanics remain compatible; circuit state stays owned by AGENTS.md."}
    - {path: .agents/workflow-overlay/source-loading.md, reason: "Packet routing is unchanged; the packet-content obligation belongs with the circuit rule."}
  stale_language_search: >
    rg -n -i "precompact|handoff packet|sandboxed_tool_stall"
    AGENTS.md CLAUDE.md .agents/workflow-overlay docs/workflows/technical_difficulties_log_v0.md
  stale_language_search_result: >
    Executed 2026-07-16 after home replay. Hits were the live AGENTS.md circuit
    rule, this incident record, and compatible packet-mechanics references; no
    live instruction said a packet continuation resets or discards an open circuit.
  non_claims: [not validation, not readiness, not a host-level tool repair]
```

### Owner-reset correction — severe circuit overfix (2026-07-16)

The persistent circuit correctly prevented repeated use of observed stalled
routes, but its absolute prohibition on rerooting also refused required skill
loading and an explicit owner instruction to continue in a new worktree. A
subsequent `apply_patch` call stalled for 121.9 seconds; a bounded read proved it
wrote no matching bytes. Two further `apply_patch` attempts with a clean
worktree and a relative, file-scoped payload also stalled without writing. The
rule was therefore a severe overfix: its containment cost exceeded the defect
class and made it temporarily self-sealing against correction.

`AGENTS.md` now preserves the automatic circuit while allowing the owner, after
failed routes and mutation uncertainty are reported, to authorize one named
fresh task or worktree route. The fresh route must re-establish target,
revision, dirty-state, writer, and mutation-outcome facts before mutation. The
reset is route-scoped and does not erase the incident, broaden authority, allow
concurrent writers, weaken protected-action checks, or permit repeated recovery
attempts.

```yaml
direction_change_propagation:
  doctrine_changed: >
    A sandboxed-tool-stall circuit remains persistent across ordinary
    follow-ups, but explicit owner instruction may authorize one named fresh
    recovery route after the failed routes and mutation uncertainty are
    reported. The route must re-bind and re-confirm state before mutation, and
    one failure closes it.
  trigger: workflow_authority
  related_triggers: [lifecycle_boundary]
  controlling_sources_updated:
    - AGENTS.md
  downstream_surfaces_checked:
    - CLAUDE.md
    - .agents/workflow-overlay/decision-routing.md
    - .agents/workflow-overlay/source-of-truth.md
    - .agents/workflow-overlay/source-loading.md
    - .agents/workflow-overlay/validation-gates.md
    - docs/workflows/technical_difficulties_log_v0.md
  intentionally_not_updated:
    - {path: CLAUDE.md, reason: "It imports AGENTS.md and must not duplicate the circuit rule."}
    - {path: .agents/workflow-overlay/decision-routing.md, reason: "Its receiver binding and explicit task-creation authorization already govern the named fresh route."}
    - {path: .agents/workflow-overlay/source-of-truth.md and .agents/workflow-overlay/source-loading.md, reason: "Source and checkpoint mechanics remain unchanged; the stall circuit stays owned by AGENTS.md."}
    - {path: .agents/workflow-overlay/validation-gates.md, reason: "Revision, dirty-state, writer, and protected-action gates remain unchanged and are expressly preserved by the reset."}
  stale_language_search: >
    rg -n -i "does not (by itself )?reset|do not (autonomously )?reroot|fresh recovery route|sandboxed_tool_stall|severe overfix"
    AGENTS.md CLAUDE.md .agents/workflow-overlay
    docs/workflows/technical_difficulties_log_v0.md
  stale_language_search_result: >
    Executed 2026-07-16 in the owner-reset recovery worktree. Live hits are the
    amended persistent circuit, its explicit named-route reset, and the dated
    incident records. No checked live surface retains an absolute ban on an
    owner-authorized fresh recovery task or worktree.
  non_claims:
    - not validation or readiness
    - not a host-level sandbox, hook, timeout, or executor repair
    - not permission for destructive Git, concurrent writers, or broader edits
```

### Superseding diagnosis — Codex Desktop Windows sandbox setup (2026-07-16)

Later dogfood isolated the dominant failure more precisely. The same trivial
read took 18.6 milliseconds in direct PowerShell and 51.6 milliseconds inside
the command process launched by Codex Desktop, while the Desktop tool call took
112.7 seconds end to end. A fresh standalone Codex CLI session completed the
same class of read in 15.7 seconds with hooks and 12.3 seconds with hooks
disabled. Forseti hook execution therefore did not account for the Desktop
stall.

The local Desktop sandbox log showed synchronous Windows write-ACL refresh
before command launch. One reproduced refresh took about 29.6 seconds; during
concurrent Desktop activity, setup calls joined a shared singleflight wait and
released together after roughly 98 to 161 seconds. The configured command
timeout did not bound that pre-execution setup wait. The legacy `orca` launch
root amplified the work: it contained about 202,000 files and 36,000
directories, versus about 3,900 files in the canonical `forseti` checkout.

This supersedes the process model in the circuit-state continuity and
owner-reset addenda above. Those entries remain append-only evidence, but their
cross-handoff circuit inheritance and special owner-reset protocol are no longer
live obligations. A stall circuit is task-local; a fresh task launched directly
in a separate small worktree is a new sandbox route. Concurrent Desktop lanes
remain supported when each task owns a small worktree. Standalone CLI or WSL2 is
the explicit fallback for a correctly rooted lane that still stalls or for
sustained shell-heavy parallelism.

Independent fixes remain valid: protected-action and nested-worktree guards,
the direct Windows Python hook launcher, explicit hook timeouts, and inspection
of all known Codex `apply_patch` payload fields. This repository mitigation does
not repair Codex Desktop, weaken fail-closed protection, or make CLI/WSL2 the
default interface.

```yaml
direction_change_propagation:
  doctrine_changed: >
    Sandboxed-tool stall containment is task-local rather than cross-handoff
    lane state, while concurrent Codex Desktop writers launch directly in
    separate small worktrees and use CLI or WSL2 only as an explicit fallback.
  trigger: workflow_authority
  related_triggers: [lifecycle_boundary]
  controlling_sources_updated:
    - AGENTS.md
    - .agents/workflow-overlay/decision-routing.md
  downstream_surfaces_checked:
    - CLAUDE.md
    - .agents/workflow-overlay/source-loading.md
    - .agents/workflow-overlay/validation-gates.md
    - .agents/hooks/README.md
    - .codex/hooks.json
    - forseti-harness/tests/unit/test_ci_hook_wiring.py
  intentionally_not_updated:
    - {path: CLAUDE.md, reason: "It imports AGENTS.md and must not duplicate the circuit rule."}
    - {path: .agents/workflow-overlay/source-loading.md, reason: "Checkpoint and handoff mechanics no longer carry stall state; no compatible live obligation required an edit."}
    - {path: .agents/workflow-overlay/validation-gates.md, reason: "Existing target, dirty-state, writer, and protected-action gates remain unchanged."}
    - {path: .agents/hooks/README.md and .codex/hooks.json, reason: "Hook topology, launchers, timeouts, and guard behavior remain intentionally unchanged."}
    - {path: forseti-harness/tests/unit/test_ci_hook_wiring.py, reason: "No live test enforced cross-handoff stall inheritance; independent guard coverage remains valid."}
  stale_language_search: >
    rg -n -i "sandboxed_tool_stall|fresh recovery route|owner-reset|owner reset|precompact.{0,80}stall|handoff.{0,80}stall|atomic_exact_edit"
    AGENTS.md CLAUDE.md .agents/workflow-overlay .agents/hooks/README.md .codex/hooks.json
    forseti-harness/tests/unit/test_ci_hook_wiring.py docs/workflows/technical_difficulties_log_v0.md
  non_claims:
    - not validation, readiness, review, or approval
    - not a Codex Desktop sandbox repair
    - not authority to weaken protected-action or worktree guards
```

## TD-2026-07-17-003 — Repeated sandbox refresh latency and recoverable exact edits

- **Observed:** 2026-07-17, Asia/Singapore.
- **Affected surface:** Codex Desktop Windows sandboxed tool calls and the
  Forseti exact-edit fallback used after a native patch stall.
- **Native ownership boundary:** the installed runtime is packaged under
  `C:\Program Files\WindowsApps\OpenAI.Codex_26.707.12708.0_x64__2p2nqsd0c76g0`.
  This repository contains the hook adapter and fallback editor, but not the
  editable source for sandbox setup, runner acquisition, end-to-end tool
  deadlines, or the native `apply_patch` executor.

### Current dogfood evidence

Controlled repository-independent fixtures produced these wall times:

| Operation | Payload | Wall time | Result |
| --- | ---: | ---: | --- |
| native patch add | 5 lines | 449.2 s | correct LF-only file |
| native patch replace | 1 line | 267.3 s | correct replacement |
| native patch add | 43 lines | 282.2 s | correct LF-only file |
| native patch replace | 1 line | 289.6 s | correct replacement |
| sandboxed verification reads | trivial | 75.8–103.0 s | correct read |

A separate timestamped probe measured about 1.1 seconds of work inside a
100.7-second tool call. Git status, worktree enumeration, a 72 KB read, and the
helper's `--help` each completed in 108–325 ms. The sandbox log showed repeated,
overlapping `setup refresh: spawning` events before helper resolution. This
confirms that payload size, newline style, Git enumeration, and the actual file
mutation are not the dominant cost.

The prior superseding diagnosis remains relevant: setup processes may still
join an internal wait. The evidence proves repeated refresh initiation and a
long pre-execution wait; it does not prove the exact internal locking or cache
implementation. The native correction must therefore be judged by behavior,
not by prescribing one unverified internal mechanism.

### Repository-controlled correction

`.agents/tools/atomic_exact_edit.py` now writes a root-local versioned journal
before the first replacement, stores original and updated bytes plus hashes,
and exposes `--recover`. A normal apply marks the journal committed before
cleanup. An interrupted apply rolls back on the next apply or explicit recovery.
Recovery refuses to overwrite a file whose bytes match neither journaled state.
A per-root OS lock in a temporary-directory namespace serializes apply and
recovery, so a concurrent invocation fails loudly instead of silently joining,
rolling back, or re-journaling a live transaction. The lock key is derived from
the normalized resolved root and is user-scoped where the OS exposes a UID; the
lock is released by the operating system when the holder dies, so a crash never
wedges later recovery. The journal loader fails closed on malformed, tampered,
root-mismatched, escaping, or symlinked journal data and retains the journal for
inspection. Each file replacement is atomic; the multi-file sequence is
recoverable, not transactional, and the journal duplicates the touched files'
bytes inside the same root until cleanup. The coordination lock file persists
outside the edited root because deleting it would reintroduce an acquisition
race. A hard exit can still strand `.<name>.atomic-exact-edit-*` temporaries
beside their targets; those target temporaries and a retained journal are not
gitignored, so an interrupted operation remains visible to downstream clean-tree
checks while normal successful use leaves no root-local lock residue. The
journal is written with `chmod 0600`, which restricts other local users' read
access on POSIX only; Windows enforces file access through ACLs rather than
the mode bits, so 0600 is not a Windows confidentiality guarantee there.
Because the journal is deliberately not gitignored, a broad `git add` run
during an interrupted state — before `--recover` runs — could commit its
duplicated original/updated file bytes into history.

Dogfood terminated the helper with exit 86 after the first file in a two-file
edit. The first file contained updated bytes, the second retained original
bytes, and the journal survived. `--recover` restored both originals and removed
the journal. Repeating the crash and then writing a third-party state caused
recovery to exit 1, preserve the third-party bytes, and retain the journal.
The permanent harness tests repeat both cases with a real subprocess hard
exit, prove that a hard exit after the committed journal write finalizes
instead of rolling back, and prove that a held transaction lock makes a
concurrent recover or apply fail loudly while the interrupted state survives.

### Native runtime success signals

A native repair is complete only when all of these are demonstrated on a
reference Windows runner:

1. Eight simultaneous trivial calls with one unchanged permission profile do
   not pay eight independent setup windows; all complete within approximately
   one cold preparation period.
2. A warm trivial call adds less than one second p95 infrastructure overhead,
   while a cold preparation stays below five seconds p95.
3. A declared timeout bounds submission, queueing, sandbox preparation, runner
   acquisition, command execution, and result delivery, returning within two
   seconds of its deadline with the failed phase named.
4. Permission-profile or writable-root changes invalidate reuse, while identical
   normalized profiles never inherit broader access.
5. Native multi-file patches either commit fully, roll back fully, or leave a
   durable recovery receipt that identifies every file; interruption never
   leaves an unclassified mutation outcome.
6. Per-call timing exposes queue, setup, runner, command, and result-delivery
   durations without leaking command contents, credentials, or environment
   secrets.

Each threshold above is decidable only against a stated minimum sample matrix
on the named reference runner; a single anecdote cannot pass or fail a p95.
At minimum: 20 warm calls, 5 cold preparations, 3 independent eight-call
concurrent bursts, 5 timeout injections spread across the named phases, and 2
distinct normalized profiles plus 1 identical-profile pair. Reported results
must state the observed sample counts next to each threshold.

### Native implementation sequence

1. Instrument the packaged runtime's owning source so the measured delay is
   attributed to queue, setup, runner acquisition, command, or delivery.
2. Reuse or coalesce preparation for identical normalized permission profiles;
   invalidate it only when a security-relevant input changes.
3. Propagate one monotonic deadline through every phase.
4. Make native patch commit recoverable with staged payloads, hashes, a durable
   journal, and crash recovery.
5. Run cold, warm, 1/2/4/8-call concurrency, profile-separation, timeout, and
   per-replacement crash-injection tests before controlled rollout.

### Non-claims

- The Forseti journal does not repair Codex Desktop sandbox latency or native
  `apply_patch`.
- The dogfood does not establish the runtime's precise internal lock design.
- Worktree cleanup and newline normalization remain hygiene, not the primary
  native correction.
- These success signals are a product acceptance contract, not evidence that
  the native runtime currently passes them.

## TD-2026-07-30-001 — Byte-pinned repo text file breaks only on Windows, invisible to CI

- **Observed:** 2026-07-30, Asia/Singapore.
- **Affected lane:** PR #1387, `codex/serp-lane-yt-onboarding-20260730`;
  artifact `forseti-harness/capture_spine/tiktok_creator_discovery_frontier/
  tiktok_fragrance_creator_promotion_policy_v3_calibration.json`.
- **State at recording:** corrective `.gitattributes` pin and a self-diagnosing
  assertion landed; no other byte-pinned artifact audited.
- **User-visible symptom:** a full local unit run showed
  `test_promotion_policy_v3_calibration_is_bound_to_admitted_cohort` failing
  with a bare sha256 mismatch, while the same test passed in CI. The failure
  reads as "the calibration artifact was tampered with" and was very nearly
  dismissed as someone else's pre-existing breakage.

### Verified evidence

| Fact | Value |
| --- | --- |
| Pinned hash in `_PROMOTION_POLICY` | `14a5a49359a7…f36b388fe` |
| Working-copy bytes on Windows | `b36a393e8d3e…386638484ee` |
| Same bytes, CRLF→LF normalised | `14a5a49359a7…f36b388fe` (matches) |
| CRLF pairs in the working copy | 142 |
| Bare LF in the working copy | 0 |
| CI result for the same commit | pass |

### Diagnosis

The test hashes `path.read_bytes()` — deliberately byte-exact, because the
point is that the artifact has not changed. Git on Windows checks repo text
out with CRLF (`core.autocrlf`), so the bytes on disk differ from the bytes
the hash was computed over. The invariant was never violated; the checkout
representation was.

The dangerous property is the asymmetry: **the failure is Windows-only and CI
is LF, so CI stays green.** A real integrity failure and a line-ending artifact
present identically — a hash mismatch with no further signal — so the true
positive and the false positive are indistinguishable at the point of failure.

### Corrective ownership

1. `.gitattributes` pins the directory's JSON to LF, following the convention
   already established there for creator-profile source inputs and
   `docs/review-inputs/*.json`:
   `forseti-harness/capture_spine/tiktok_creator_discovery_frontier/*.json text eol=lf`.
   A working copy checked out BEFORE the rule keeps its CRLF; it must be
   re-checked-out (delete + `git checkout --`, or `git add --renormalize`).
2. The assertion is now self-diagnosing: on mismatch it re-hashes the
   LF-normalised bytes, and if THAT matches the pinned value it fails with an
   explicit line-ending message naming the `.gitattributes` fix and warning
   not to update the pinned hash (which would break LF platforms).

Correction 2 is the load-bearing one. Detection was never missing — the test
did fail. What was missing was **interpretation**: the ~20 minutes went to
deciding whether the artifact or the checkout was wrong.

### Prevention for future byte-pinned artifacts

Any new artifact whose bytes are hash-pinned needs its path pinned to LF in
`.gitattributes` in the same commit. The generalisable guard is the
diagnosis-on-mismatch pattern above; copy it rather than emitting a bare hash
comparison, so the next occurrence explains itself.

### Accepted residuals

- Only the one artifact was pinned and corrected. Other byte-pinned files in
  the repository were NOT audited for the same exposure; a sweep would need to
  enumerate every `sha256(...read_bytes())` assertion and check
  `.gitattributes` coverage for each hashed path.
- CI cannot see this class at all (Linux checkout is LF), so the guard is
  local-run only. A Windows CI leg would close that, and is not proposed here.

### Non-claims

- No claim that the calibration artifact's contents were ever wrong; the
  cohort binding it asserts held throughout.
- No claim that other line-ending-sensitive checks in the repository are
  currently correct — only that this one is.
