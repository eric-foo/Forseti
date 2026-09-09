# Supervised execution dogfood, 2026-09-10

The sample-local [entrypoint](README.md) completed its real verifier call and
quiet/failure checks. It uses code for process supervision and one compact
completion result. This is a bounded execution result, not proof that the full
experiment now costs less or that this is globally optimal.

## Decision and scope

The owner requested the smallest complete fix for expensive routine coordinator
wakeups, followed by implementation and dogfood. This session still requires
updates within 60 seconds. A native multi-agent timeout setting does not govern
the shell session used here, and cannot remove that session instruction.

The existing experiment already batched model work in code. Adding another AI
supervisor would add a model/context boundary. The chosen change makes the frozen
positive-control verifier executable through one entrypoint, including process
logs, an expected-duration review, correction application and native accounting.
The outer conversation retains one session handle and waits up to 55 seconds
without separate status commands. It still pays for model calls when waits return.

Scope is this research sample's positive-control execution. This does not wire a
new runner into the complete nine-generation experiment or change global settings,
production behavior, diagnostic doctrine or the original frozen evidence. Future
executions should use the compact invocation in the README in a fresh conversation;
that reduction in coordinator context was not tested in this authoring conversation.

## Observed dogfood

Implementation, prompts and source inputs were [frozen](freeze.json) before the
first model launch. [Dogfood](dogfood.json) preserves all first-pass outcomes:

| Case | Result |
| --- | --- |
| Quiet process crossing its review interval | One review event; process subsequently succeeded; no kill or restart |
| Intentional process failure | Exit 7 and stderr preserved as failure |
| Missing executable | ENOENT preserved as failure |
| Controlled 70-second quiet process | Completed in 70,098 ms; one outer follow-up wait requested 55,000 ms |
| Fresh real verifier, unchanged known-error input | One Astra/high call, 23,529 ms, no tools or retries |

The 70-second process is synthetic; the real verifier took about 24 seconds.
The overdue test is a duration-review test, not a proven deadlock detector.
Cancellation and host-crash recovery were not tested. The supervisor never
automatically kills, restarts or labels a quiet process healthy or stalled.

The verifier made [one correction](real-verifier/response.json), changing the
claim of reduced congestion to the source-supported absence of caused forehead
congestion. The frozen A13 source says “It has not caused the congestion on my
forehead”; that does not establish improvement of existing congestion. The
[delivered answer](real-verifier/corrected.json) contains the exact replacement;
all other fields match the original. This exercises the known error, not a new
estimate of general diagnostic accuracy.

## Cost and verification

[Native measurement](measurement.json) separates the model worker from this outer
conversation. Cached input is included within input, not added to it again.

| Component | Tokens |
| --- | ---: |
| Real verifier input | 38,448 |
| Real verifier output | 480 |
| Real verifier total | 38,928 |
| Internal code supervision | 0 |
| Outer implementation conversation through recorded cutoff | 976,925 |
| Of that outer total: cached input | 917,120 |
| Combined through cutoff | 1,015,853 |

The coordinator cutoff is **2026-09-09T18:38:15.370Z**, from the current turn's
start at 18:28:42.927Z. Subsequent reporting, publication and the final response
are additional unallocated cost. This is not a finalized whole-turn total.
The large outer cost is evidence that code supervision alone does not solve
repeated long-context processing. No whole-experiment savings percentage is claimed.

Run `node docs/research/diagnosis_fully_batched_coordination_20260909/supervised_execution/measure.mjs --check`
to recheck frozen identity, native completion/accounting, exact correction replay,
quiet and overdue behavior, preserved failure exits and log sizes, and the observed
single host wait. The native accounting check requires the recorded local Codex
session files; process receipts and first-pass outputs remain in this directory.

The existing draft PR remains held for different-vendor operator-courier review
and author adjudication before merge. These execution checks do not satisfy that
independent review gate.
