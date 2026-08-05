# Summer Fridays Understanding p11r1 — Targeted Phase 2 Recovery Return

```yaml
retrieval_header_version: 1
artifact_role: Targeted Phase 2 acquisition recovery return
scope: Settles only the two p11 Phase 2 queries that failed the exact-query content floor.
use_when:
  - Combining the immutable six-job p11 Phase 2 result with the p11r1 recovery delta.
authority_boundary: retrieval_only
```

## Terminal Accounting

```yaml
status: COMPLETE_WITH_SERP_CEILINGS
parent_jobs: {planned: 8, completed: 6, blocked: 2, unrun: 0}
p11r1_recovery_jobs: {planned: 2, completed: 2, blocked: 0, unrun: 0}
combined_jobs: {planned: 8, completed: 8, blocked: 0, unrun: 0}
queue_run_id: summer_fridays_understanding_p11r1_phase2_recovery_20260801
queue_status: complete
cadence: {mode: fixed, delay_seconds: 113, slot_count: 2}
```

The exact p11 queries were too narrow to meet the typed row floor. Each p11r1
query broadened only the same commissioned seam; neither introduced a new
research question.

| Parent job | Recovery query | Packet evidence | Admitted content |
|---|---|---|---|
| `p2_q06_jet_lag_statement` | `"Summer Fridays" "Jet Lag Mask" redness irritation manufacturing` | packet `01KYWW5SB1GZR9C51X4XBHV1E8`; manifest SHA256 `f79a5f0fe1f0b3054eac31d5dcb06eb80c049415908170bf5e48db21d967ba2b` | 22 typed rows, 6,347 visible-text characters, 28 direct hrefs; includes the official statement result plus dated independent reporting. |
| `p2_q07_sustainability_bht` | `"Summer Fridays" sustainability vegan cruelty-free BHT` | packet `01KYWWCBY6DTZ94RB4WHZZHPB9`; manifest SHA256 `795ce63ee2549ca502024b3fb0f58566a8ae64d3db1d36e0942a2889cc75e883` | 23 typed rows, 4,953 visible-text characters, 24 direct hrefs; includes official product snippets and critical/community discovery surfaces. |

These are Google result-page observations. Google summaries are discovery
material, not source truth; snippets do not replace the linked body; the BHT
surface is not toxicology evidence; and the Jet Lag surface does not establish
medical causality. The parent decision receipt remains unchanged: these two
captures close acquisition gaps but do not manufacture a competitor response
or automatic-validation proof.

Raw packets and queue state live under
`C:\tmp\forseti-summer-fridays-understanding-p11r1-20260801\serp_phase2\`.
