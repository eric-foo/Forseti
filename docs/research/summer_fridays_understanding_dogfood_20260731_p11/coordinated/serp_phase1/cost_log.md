# Summer Fridays p11 SERP Phase 1 Cost Log

```yaml
retrieval_header_version: 1
artifact_role: Run cost log
scope: Observed Phase 1 scout timing, capture, cooldown, recovery, and judgment accounting for p11.
use_when:
  - Auditing p11 Phase 1 acquisition cost and downstream waits.
authority_boundary: retrieval_only
```

```yaml
unit: serp_phase1_fresh_scout
actor: CO0
started_at: "2026-07-31T11:16:33.5254034Z"
ended_at: "2026-07-31T17:54:05.158413Z"
active_segments:
  - "2026-07-31T11:16:33.5254034Z/2026-07-31T11:16:43.9367954Z: interrupted-run first seed attempt and preserved block inspection"
  - "2026-07-31T15:24:18.316208Z/2026-07-31T15:24:56.312673Z: resumed exact first seed attempt and preserved block"
  - "2026-07-31T16:25:06.371450Z/2026-07-31T16:30:23.163077Z: permitted first recovery, second seed, and third-seed block"
  - "2026-07-31T17:30:34.721084Z/2026-07-31T17:41:07.607773Z: permitted third-seed recovery and remaining seed captures at owner cadence"
  - "2026-07-31T17:43:19.198870Z/2026-07-31T17:54:05.158413Z: subject price plus interleaved e.l.f. and Rhode versus/price queue"
waiting_segments:
  - "2026-07-31T15:24:56.312673Z/2026-07-31T16:25:06.371450Z: one-hour Google cooldown before the exact p1_01_review recovery"
  - "2026-07-31T16:30:23.163077Z/2026-07-31T17:30:34.721084Z: one-hour Google cooldown before the exact p1_03_bad_for_you recovery"
  - "113-second minimum inter-job cadence between successful captures in the resumed queue"
blocked_segments:
  - "2026-07-31T11:16:43.9345776Z: interrupted-run p1_01_review unusual-traffic packet preserved"
  - "2026-07-31T15:24:56.312673Z: resumed p1_01_review unusual-traffic packet preserved; queue entered cooldown"
  - "2026-07-31T16:30:23.163077Z: p1_03_bad_for_you unusual-traffic packet preserved; queue entered cooldown"
scripted_steps:
  - current runner/help, queue-policy, and state-schema preflight
  - CloakBrowser source-capture packet attempts under the current Google queue
  - capture-time Google content extraction and packet manifest emission
  - policy evaluation for the subject-price and four comparator jobs
  - local manifest, preserved-file hash, size, and queue-state validation
judgment_steps:
  - classified each unusual-traffic surface as a route block rather than zero yield
  - retained the exact held jobs and used only the permitted cooldown recoveries
  - rejected three parser-debris/unbound tokens from competitor promotion
  - promoted e.l.f. and Rhode only after two distinct seed-query sightings and exact-product resolution
  - separated native-item and owned-page discovery doors from captured native or owned evidence
capture_count: 15
source_content_capture_count: 12
block_or_failure_count: 3
recovered_block_count: 3
local_preflight_rejection_count: 2
planned_job_count: 12
completed_job_count: 12
blocked_job_count: 0
unrun_job_count: 0
downstream_waits_caused:
  - specialist terminals required one dependency refresh after the final Phase 1 return
```

The capture count includes the interrupted run's preserved first block, two
additional resume block packets, and the twelve successful terminal jobs. A
block attempt and a blocked job are different units: all twelve planned jobs
eventually completed, while every failed attempt remains visible in provenance.

The two local preflight rejections occurred before network capture and wrote no
packet. The TikTok Shop browser profile was explicitly excluded from Google
fallback and was not accessed. No hot retry, CAPTCHA interaction, proxy, or
borrowed account state was used.
