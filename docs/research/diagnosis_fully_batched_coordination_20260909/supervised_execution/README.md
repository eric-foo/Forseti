# Supervised execution for this sample

This is the sample's reusable execution entrypoint for the frozen real-evidence
verifier positive control. It is not a production method or a global Codex setting.
The original experiments and their first-pass failures remain unchanged.

Run from a terminal with a new absolute output directory:

```powershell
node docs/research/diagnosis_fully_batched_coordination_20260909/supervised_execution/run.mjs C:/path/to/new-run-output
```

The script owns launch, stdout/stderr preservation, process completion, the
expected-duration review, exact correction application, cold-input validation and
native accounting. It returns one completion receipt, or an exception/review
receipt. A review timer does not kill, restart or label a quiet process healthy or
stalled. There is one review notification per process; later terminal outcome is
always preserved. No automatic retries. Logs include empty files.

For execution through a conversational shell tool, keep the returned session
handle and use the longest wait compatible with the active host requirements.
For this session use `write_stdin` with empty input and `yield_time_ms: 55000`,
with no separate status command between waits. Give required updates when a wait
returns. If a review exception arrives, inspect that same process and its exact
receipt before deciding whether to continue. No new daemon, AI watchdog or global
timeout setting is needed.

Use a fresh compact execution conversation for future runs: the commission,
this entrypoint, output location and unresolved exceptions are sufficient.
Do not carry the authoring chat, evidence packs or all reader answers into an
execution coordinator. This entrypoint needs no coordinator model internally;
the real verifier remains a separately metered evidence judgment.

The 60-second session update requirement is not removed. Calls made by the outer
conversation still cost tokens; a model-free supervisor does not make that cost
disappear. `dogfood.json` and `report.md` distinguish those costs from this runner.

`freeze.json` binds the implementation and the actual verifier inputs used for
dogfood. `dogfood.mjs` checks real nonzero/spawn failure, an overdue review without
kill/restart, a 70-second quiet operation, and the exact frozen evidence verifier.
Do not rerun into existing output directories; first-pass logs are not disposable.
