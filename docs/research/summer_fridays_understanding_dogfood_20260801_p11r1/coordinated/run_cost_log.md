# Summer Fridays Understanding p11r1 — Recovery Cost Log

```yaml
retrieval_header_version: 1
artifact_role: Acquisition recovery cost ledger
scope: Records observed execution, waits, failures, and judgment for the p11r1 recovery only; parent cost remains in the immutable p11 ledger.
use_when:
  - Auditing why p11r1 stopped particular routes or what the recovery added.
authority_boundary: retrieval_only
```

No provider-dollar cost was exposed by the local runners, so none is invented.
Counts below are observed artifacts and attempts, not estimates.

```yaml
- unit: capture_spine_hardening
  actor: CO0
  active_segments:
    - fail-fast Instagram lake validation in exact and creator consumers
    - safe HTTP status and Retry-After preservation with exact rate-marker typing
    - TikTok retained-profile-to-CDP process binding
    - cross-platform acquisition-seal text hashing
  scripted_steps:
    - focused unit tests, compile checks, pull-request CI, and fresh-checkout dogfood
  judgment_steps:
    - keep each fix at the observed failure boundary and preserve real route failure
  validation:
    focused_seal_tests: 18_passed
    earlier_capture_hardening_ci: 4701_passed_25_skipped

- unit: parent_confirm_dont_trust
  actor: CO0
  active_segments:
    - fresh board and seal validation
    - canonical hash register and complete raw packet closure
  scripted_steps:
    - 232 manifest, 188 unique packet-ID, and 933 preserved-file checks
  blocked_segments: []
  downstream_waits_caused: []

- unit: co1_pending_recovery
  actor: CO0
  active_segments:
    - three bounded public ownership/leadership sources
    - two initial owned-page attempts and one backoff-respecting shared-route recovery
  waiting_segments:
    - source-declared 60-second owned-host backoff before the final recovery
  block_or_failure_count:
    owned_page_429_packets: 3
    orchestration_backoff_violation: 1
  new_packet_count: 6
  terminal_job_accounting: {planned: 3, completed: 1, blocked: 2, unrun: 0}

- unit: co3_pending_recovery
  actor: CO0
  active_segments:
    - one guarded Reddit fallback
    - retained-profile TikTok process binding and four exact live attempts
    - one exact Instagram deep capture into an initialized data lake
  waiting_segments:
    - cooled TikTok fresh recovery after the shared empty-shell failure
  block_or_failure_count:
    reddit_security_blocks: 1
    tiktok_empty_shell_staging_runs: 3
  admitted_packet_count: 2
  blocked_packet_count: 1
  terminal_delta:
    reddit: {planned: 3, completed: 0, blocked: 1, unrun: 2}
    tiktok: {planned: 5, completed: 1, blocked: 2, unrun: 2}
    instagram: {planned_parent_total: 4, completed_parent_total: 4, blocked: 0, unrun: 0}

- unit: targeted_phase2_recovery
  actor: CO0
  observed_window: 2026-07-31T19:59:23Z/2026-07-31T20:03:21Z
  active_segments:
    - two same-seam broader Google result captures and typed-content inspection
  waiting_segments:
    - declared 113-second fixed cadence
  scripted_steps:
    - durable queue claim/report, content admission, and manifest/hash validation
  new_packet_count: 2
  terminal_job_accounting: {planned: 2, completed: 2, blocked: 0, unrun: 0}

- unit: p11r1_raw_closure
  actor: CO0
  active_segments:
    - recursive packet-ID, preserved-file size, and SHA256 validation
  child_manifest_locations: 11
  child_unique_packet_ids: 11
  child_preserved_file_declarations: 40
  validation_errors: 0
```

The work stopped after acquisition sealing. No downstream Deliver wait or
execution time is part of this ledger.
