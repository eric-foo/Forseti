# SERP lane: competitor scout + journey levers

The SERP capture lane's competitor-scout work unit: typed competitor
ledger (spec + promotion ladder + channels), Understanding-cycle
installation (scout pass + ordering rule; two-phase shape with the
Reddit lane), journey levers J1-J5, the Tower 28 and Summer Fridays
live trials including their phase-2 native returns, the completed
megadogfood Stage 6 queue and pruned analysis slice, the bounded BR540
native-return dogfood, egress-shape evidence,
the Deliver retention/offense note, and the cross-company dogfood
(CeraVe / AeroPress).

**Authority: this folder is canonical.** Lane prose and instruments are
authored here, in the repository. The operator drive holds raw capture
data and in-flight scratch only -- never the sole copy of a decision,
rule, finding, or instrument. (Inverted 2026-07-28, replacing the
2026-07-27 staging-is-ahead rule: that rule licensed unbounded drift
and produced six separate cases of load-bearing work surviving only in
a temp folder. There is now one copy, so there is nothing to
reconcile.) Expected next supersession: the full-bank megadogfood
analysis pass (~2026-07-30, n~100 subjects) re-judges lane cells
F4-F21 and the emitter's candidate ladder. Stage 6 queue completion and its
future-run query/fallback corrections are recorded in
`megadogfood_stage6_queue_completion_v0.md`.

**Instruments** (in-repo, canonical):
`forseti-harness/runners/serp_competitor_ledger_emitter.py` (Channel-0
emitter), `extract_serp_v2.py` (SERP extractor),
`reddit_thread_composition.py` and `reddit_provenance_pull.py`
(native-lane analysis),
`forseti-harness/tests/unit/test_serp_competitor_ledger_emitter.py`
(pinned-fixture suite -- run after ANY emitter edit; it skips, rather
than passes, when the operator-drive fixture stores are absent).
`forseti-harness/source_capture/google_serp_queue_policy.py` owns the
pre-egress query gate and lower-route block transition.
`forseti-harness/runners/run_google_serp_persistent_fallback_packet.py`
executes the held-job persistent-tab route, preserves block packets, and
waits for manual operator clearance without challenge interaction.

**Raw capture data stays outside Git**, on the operator drive:
`C:\tmp\forseti-serp-megadogfood-20260727\` (query bank, run ledger,
extractions), `C:\tmp\forseti-tower28-scout-20260727\` (scout trial
packets, PDP captures), `C:\tmp\forseti-tower28-reddit-20260728\` and
`C:\tmp\forseti-sf-phase2-native-return-20260728\` (native thread
packets + composition reads), and
`C:\tmp\forseti-br540-phase2-native-return-20260730-runtime\`
(bounded BR540 native-return packets and staging analysis).

Reading order: `serp_lane_v0.md` (entry point / findings ledger) ->
`megadogfood_stage6_queue_completion_v0.md` (completed queue, pruning,
future-run corrections) ->
`br540_phase2_native_return_dogfood_v0.md` (smallest-complete
one-subject execution of the six-step native-return loop) ->
`competitor_ledger_spec_v0.md` (types, ladder, cycle installation,
J1-J5) -> `tower28_scout_trial_findings_v0.md` +
`tower28_phase2_native_return_v0.md` +
`summer_fridays_phase2_native_return_v0.md` (trial evidence, both
phases) -> `tower28_ci_onepager_demo_v0.md` (demo deliverable) ->
`deliver_note_repair_room_retention_v0.md` ->
`dogfood2_cross_company_note_v0.md` (generalization check) ->
`serp_lane_egress_shape_evidence_v0.md` (capture cadence evidence).

Re-judging the findings ledger against the full capture store (analysis
only, no captures) is commissioned via
`docs/prompts/handoffs/serp_lane_fullbank_analysis_execution_handoff_v0.md`.

Capture execution is commissioned via two handoffs, in order:
`docs/prompts/handoffs/serp_lane_phase1_scout_execution_handoff_v0.md`
(seeds -> rolling harvest -> merged vs+J5 queue -> priced ledger +
trigger-thread queue), then
`docs/prompts/handoffs/serp_lane_phase2_native_return_execution_handoff_v0.md`
(native return: Reddit-lane consumption, Channel 3, J3 settlement, J5
delta, evidence-targeted return probes). An agent starting the
Understanding cycle is routed to phase 1 by the CSB playbook's
Operating Sequence, not by being told to read a file.

**Summer Fridays reuse bar (temporary):** an agent running the
Understanding cycle for Summer Fridays must run phase 1 fresh — do not
invoke the playbook's reuse clause against this folder's SF ledger, and
do not read this folder's SF files; stop and report to the dispatcher.
Terms:
`docs/workflows/serp_scout_pass_calibration_predeclaration_v0.md`
(dispatcher/adjudicator-facing). Remove this bar when that note's
adjudication is appended.

Standing non-claims carried throughout: counts of observed cards only,
never prevalence/volume/share; US-parameterized is not physically
US-local; blocks are stop signals; raw data outside Git.
