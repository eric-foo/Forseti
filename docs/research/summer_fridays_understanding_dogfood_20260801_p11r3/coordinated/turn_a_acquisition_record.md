# Summer Fridays p11r3 Turn A Acquisition Record

```yaml
retrieval_header_version: 1
artifact_role: Understanding acquisition execution record
scope: Phase A intake, pending-only execution, validation, and terminal accounting for the Summer Fridays p11r3 recovery.
use_when:
  - Auditing how the p11r3 acquisition seal was reached.
  - Distinguishing acquisition evidence from later capture-spine corrections.
authority_boundary: retrieval_only
```

```yaml
cycle_id: summer_fridays_understanding_p11r3_20260801
subject: Summer Fridays
phase: Acquire
commission_boundary: Acquire and Seal only
authority_revision: e39e7ab8c7035759df42f14534c49281106bcc15
parent_seal: docs/workflows/summer_fridays_understanding_dogfood_20260801_p11r2/coordinated/acquisition_seal.md
pending_on_entry: [CO1-J10, CO1-J11, CO3-NATIVE-TT-7527741844298435895]
completed_this_turn: [CO1-J10, CO1-J11, CO3-NATIVE-TT-7527741844298435895]
blocked_on_exit: []
unrun_on_exit: []
deliver_started: false
```

## Confirm-Don't-Trust Intake

The amended p11 handoff was fresh-read at repository revision
`e39e7ab8c7035759df42f14534c49281106bcc15`; its canonical SHA256 was
`547b71fc61767f3df276daeb755334ba2f0151bb4b4e3ab03c98eb55eff9bff4`.
The p11r2 blocked seal was treated as provenance, not completion evidence.

All eight artifacts in its resume contract were fresh-read and re-hashed using
the seal validator's canonical text basis. Every digest matched. Recursive raw
closure checks observed:

| Raw root | Manifests | Declared preserved files | Result |
|---|---:|---:|---|
| p11 parent | 232 | 933 | Every declared file exists and matches recorded size and SHA256. |
| p11r1 | 11 | 40 | Every declared file exists and matches recorded size and SHA256. |
| p11r2 | 11 | 19 | Every declared file exists and matches recorded size and SHA256. |
| p11r3 | 5 | 9 | Every declared file exists and matches recorded size and SHA256; all five manifests conform to the current packet schema. |

The p11 parent includes a command-output log named `P511756.stdout.json` whose
contents are not a standalone JSON document. It is not a packet manifest or a
declared packet JSON payload; its bytes and provenance were preserved unchanged.
No Deliver-named artifact was found in any p11/p11r1/p11r2/p11r3 raw root or
the corresponding repository artifact trees.

## Pending-Only Execution

Only the three pending job IDs were run. CO1-J10 and CO1-J11 completed through
the serial same-host Direct HTTP path; CO3-NATIVE-TT-7527741844298435895
completed through the retained packet-grade TikTok profile and local admission
gate. The owning specialist returns are:

- `specialists/co1_company_core_final_recovery.md`
- `specialists/co3_customer_community_final_recovery.md`

No previously completed acquisition job was rerun. The first p11r3 owned-page
pair is retained as diagnostic provenance for a classifier false positive and
is not counted as terminal evidence; the corrected pair is the owning evidence.

## Durable Capture-Spine Corrections

The recovery exposed two repeatable process defects. The first merged
implementation reduced recurrence but did not fully close them: a later
de-correlated review reproduced cases where a 200 login shell could receive
completion credit, `Retry-After` could be lost when a response body was empty
or over the size cap, response mitigation headers did not reach the classifier,
and an unexpected mid-batch exception could leave no summary. Those defects
were corrected in the follow-up capture-spine adjudication without rerunning or
changing the acquisition evidence recorded here.

The resulting current behavior is:

1. A new same-host Direct HTTP batch runner enforces serial execution, a
   60-second hard minimum and 90-second default gap, stop-on-first-refusal,
   no automatic retries, explicit unrun accounting, and `Retry-After`
   preservation across readable response failures. It consumes the packet
   runner's authoritative admission outcome, retains a recovery summary before
   re-raising unexpected runner failures, and receives the safe mitigation and
   encoding headers used by the classifier. The single-URL runner's cadence
   fields are documented as disclosure rather than scheduling.
2. Bare dormant hCaptcha script references no longer classify a full ordinary
   page as a challenge shell. Visible human-verification language and the other
   high-confidence block signals still fail closed. The batch wrapper also
   refuses completion credit whenever the owning packet runner does not admit
   the body as capturable source content, even if that inner runner returns zero.

The hCaptcha correction has an explicit residual: an hCaptcha-only interstitial
without recognized visible challenge language or a mitigation header can remain
`content_unverified`; that label is a ceiling, not positive content
certification. The TikTok runbook states that cadence inside one process does not protect
separate creator commands and requires at least 90 seconds plus result inspection
between such commands. Focused unit validation passed 42 tests across Direct
HTTP, batch pacing, and block-shell classification for the first implementation;
the follow-up adjudication added integrated batch-to-packet-to-adapter-to-classifier
regressions for the reproduced gaps.

## Terminal Acquisition State

All required-and-material jobs are accounted complete. Acquisition can be
sealed `SEALED_READY_FOR_DELIVER`, but this commission stops at that seal. No
comparison to p10, downstream synthesis, or Deliver artifact was started.
