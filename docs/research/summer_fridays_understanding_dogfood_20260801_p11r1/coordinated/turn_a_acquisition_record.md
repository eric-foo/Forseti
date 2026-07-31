# Summer Fridays Understanding p11r1 — Turn A Acquisition Record

```yaml
retrieval_header_version: 1
artifact_role: Acquire-and-seal recovery evidence and gate record
scope: Records parent reuse validation, p11r1 acquisition deltas, process corrections, remaining material gaps, and the final acquisition-gate decision.
use_when:
  - Auditing p11r1 Phase A or determining whether a later Deliver turn is licensed.
authority_boundary: retrieval_only
```

## Adjudicated State

```yaml
status: BLOCKED_ACQUISITION_INCOMPLETE
acquisition_gate: blocked
deliver_allowed: false
deliver_started: false
bound_question_preserved: true
coldness_attestation: compliant
subject: Summer Fridays
as_of_date: 2026-07-31
parent_authority_revision: aa92073b51c3a4259fbc800e98a06770ec21fb8b
parent_launch_root_revision: 91fce81459a58528c3ead10d8a5ac5e45c96824a
p11r1_code_authority_revision: 6f4858ba64c30168beb2cd2dd66ef12defb3aa90
phase1_jobs: {planned: 12, completed: 12, blocked: 0, unrun: 0}
co1_jobs: {planned: 11, completed: 9, blocked: 2, unrun: 0}
co2_jobs: {planned: 7, completed: 7, blocked: 0, unrun: 0}
reddit_community_jobs: {planned: 3, completed: 0, blocked: 1, unrun: 2}
native_tiktok_jobs: {planned: 5, completed: 1, blocked: 2, unrun: 2}
native_instagram_jobs: {planned: 4, completed: 4, blocked: 0, unrun: 0}
native_youtube_jobs: {planned: 1, completed: 1, blocked: 0, unrun: 0}
phase2_jobs: {planned: 8, completed: 8, blocked: 0, unrun: 0}
```

The p11r1 commission executed only the 14 jobs that the immutable p11 seal
listed as pending. Five changed disposition: CO1-J2, one TikTok item, one
Instagram item, and both Phase 2 queries completed. Two more TikTok items
gained a more precise blocked result. The remaining two TikTok items were
intentionally left unrun after the shared platform circuit opened. No
completed parent job was replayed.

The parent blocked seal is preserved at canonical-text SHA256
`462df7b3ffe1e5dea5661e9fc4dc839bcd96c437fb433dec166f46f0d66eea2f`.
It supplied provenance and a pending-job set, not Phase A completion credit.

## Fresh-Read Recovery Artifact Register

| Artifact | Canonical-text SHA256 | Observed state |
|---|---|---|
| `docs/research/summer_fridays_understanding_dogfood_20260801_p11r1/coordinated/parent_reuse_validation.md` | `cc7d64d3862421816ca431648c4d7c617eae6025de3d87963a24c6efc6dd18b4` | Parent board/seal pass; 232 manifests and 933 preserved files revalidated; no Deliver artifact. |
| `docs/research/summer_fridays_understanding_dogfood_20260801_p11r1/coordinated/specialists/co1_company_core_recovery.md` | `705171d5122200a269c7c85fba337fd10c1e4b5a637d5db445c272af4380d4c6` | CO1-J2 completed to a bounded public-evidence result; J10/J11 remain blocked on repeated 429. |
| `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co2_retail_portfolio.md` | `b76c772fd7227621938516f6ff1b5fa3c94e2f082392d257e7072d6eda23b880` | Immutable parent CO2 return reused after full hash validation; all seven jobs complete under typed ceilings. |
| `docs/research/summer_fridays_understanding_dogfood_20260801_p11r1/coordinated/specialists/co3_customer_community_recovery.md` | `d3be3ceccbb5fe389ff384abde8352b663a0044960b3957454493dd677024de0` | Instagram closes, one TikTok closes, Reddit and the remaining TikTok route stay incomplete. |
| `docs/research/summer_fridays_understanding_dogfood_20260801_p11r1/coordinated/serp_phase2/targeted_recovery_return.md` | `f19e295cf58b2457f6fb2b8d93fdffe72dc4056cedb3515e1aee77c45e3a9c74` | Both same-seam broader queries admitted typed result rows; combined Phase 2 is 8/8 complete. |
| `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/serp_phase2/decision_receipt.json` | `3e814232972ecedec7c563f79c78bfca70f9618fae5b5a6c17446345f1dc95bf` | Parent lifecycle decision remains contract-valid and unchanged by acquisition-only recovery. |
| `docs/research/summer_fridays_understanding_dogfood_20260801_p11r1/coordinated/run_cost_log.md` | `67b511ee5e3c7eb51f33b979599930f466343b91ea5bd411989a105924999a28` | Child execution, wait, failure, and validation accounting. |

## Raw Closure

The child raw root is
`C:\tmp\forseti-summer-fridays-understanding-p11r1-20260801\`. A recursive
fresh validation observed 11 manifest locations, 11 unique packet IDs, and 40
preserved-file declarations with zero parse, missing-file, size, SHA256, or
packet-ID collision errors. Failed TikTok runs have staging JSON rather than
admitted manifests; their three terminal cadence files were parsed and hashed
separately in the CO3 return. The Phase 2 queue finished `complete` with two
success reports and no block or failure report.

## Why p11 Acquisition Was Incomplete, And What Changed

| p11 problem | Root cause found in p11r1 | Smallest complete response | Dogfood result |
|---|---|---|---|
| Instagram exact item never captured | The consumer opened a browser before checking whether the required data lake was valid. | Run the same local lake check at both exact and creator entry points before any browser/network action. | A valid initialized lake admitted the exact reel, transcript, comments, and Silver rows. |
| TikTok retained profile was unusable | The exact runner could not consume the retained profile, and a live CDP port alone did not prove which profile owned it. | Resolve the retained profile and bind it to the actual Chrome process command line before attaching. | An unrelated endpoint was rejected; the correct profile admitted one exact item. Later empty-shell failures remained visible. |
| Owned-page `local_rate_limited` gave too little evidence | The packet typed a small marker but did not preserve the navigation status or safe backoff header. | Preserve HTTP status and a validated `Retry-After`, and type the rate marker only on an exact match. | All three blocked packets show HTTP 429 and `Retry-After: 60`; the final cooled retry proves the host still refused content. |
| Phase 2 exact queries returned too few rows | The site-restricted phrasing was narrower than the content-admission floor, not a Google access failure. | Broaden only within the same Jet Lag and sustainability/BHT seams. | Both jobs completed with 22 and 23 typed rows at the declared cadence. |
| Reddit bodies were missing | Direct access returned 403 and the one licensed guarded fallback hit Reddit's network-security block. | Preserve one fallback packet and stop the shared route; do not fan out six more doomed calls. | No body was captured, so Reddit and its derivative jobs remain honestly incomplete. |
| An unchanged parent seal looked drifted in a fresh checkout | Windows converted LF to CRLF even though the Git blobs were identical. | Canonicalize line endings for seal-referenced Markdown/JSON/YAML only; keep other types exact-byte. | The parent seal passes in both worktrees, while the existing real-edit test still fails on content drift. |

The capture-spine portion landed through PR #1409 at merge commit
`6f4858ba64c30168beb2cd2dd66ef12defb3aa90`. Its complete CI run observed
4,701 passed and 25 skipped tests after fixing one creator-runner preflight
call site that CI caught. The checkout-stable seal verifier was then added in
this p11r1 acquisition work unit and covered by the focused 18-test validator
suite.

## Evidence-Family Adjudication

| Evidence family | p11r1 result | Gate effect |
|---|---|---|
| Company ownership/leadership | Public evidence now establishes the dated 2024 transaction and current partnership language, but not current legal control, percentages, or title currency. | CO1-J2 complete as a bounded public-evidence result; no ownership overclaim. |
| Company-owned event/claim pages | Repeated HTTP 429 after the advertised backoff; no body acquired. | CO1-J10 and CO1-J11 remain material blocks. |
| Reddit community | Direct and guarded fallback routes both failed before body content. | J-CO3-01 blocked; J-CO3-02/03 remain unrun derivatives. |
| Native TikTok | Correct profile route admitted one exact item; two later items repeatedly rendered empty shells without a challenge marker. | One complete, two blocked, two unrun after circuit opening. |
| Native Instagram | The formerly setup-blocked exact item admitted successfully. | Four of four native Instagram jobs complete under ASR/comment ceilings. |
| Targeted Phase 2 | Both same-seam broader recoveries admitted typed rows. | Eight of eight Phase 2 jobs complete; SERP-only limits retained. |

## Machine-Derived Resume Set

Nine required-and-material jobs remain incomplete:

```yaml
pending_job_ids:
  - CO1-J10
  - CO1-J11
  - J-CO3-01
  - J-CO3-02
  - J-CO3-03
  - CO3-NATIVE-TT-7527741844298435895
  - CO3-NATIVE-TT-7379382940272217386
  - CO3-NATIVE-TT-7354686188327832833
  - CO3-NATIVE-TT-7496318205502246190
```

## Acquisition Gate Decision

`BLOCKED_ACQUISITION_INCOMPLETE` remains mandatory. The p11r1 work reduced the
material pending set from 14 to 9 and fixed the process defects that obscured
Instagram, profile binding, rate evidence, Phase 2 admission, and cross-platform
seal verification. It did not acquire the two owned bodies, any Reddit body,
or four of five exact TikTok items. A passing seal would hide those gaps.

No company report, synthesis, recommendation, strategic response, Problem
Framing artifact, p10 comparison, Deliver handoff, or other Deliver output was
created. The final bounded Deliver-artifact scan was clear.
