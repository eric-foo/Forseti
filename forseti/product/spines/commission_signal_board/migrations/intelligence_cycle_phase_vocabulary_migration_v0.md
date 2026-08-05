# Intelligence Cycle Phase Vocabulary Migration v0 — 2026-08-05

```yaml
retrieval_header_version: 1
artifact_role: Spine migration note (vocabulary mapping)
scope: >
  Maps the Forseti Intelligence Cycle's historical phase and turn vocabulary to
  the current vocabulary adopted 2026-08-05, so historical seals, handoffs, and
  run records remain interpretable without rewriting them.
use_when:
  - Reading a historical seal, handoff, or run record that uses Problem Framing or Deliver-as-turn vocabulary.
  - Verifying which vocabulary a cycle artifact was authored under.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
  - forseti/product/spines/commission_signal_board/spine.yaml
stale_if:
  - The cycle's phase or turn vocabulary changes again.
```

Owner-directed change (Deliver planning lane, 2026-08-05). Docs-only: the CSB
output validator and the phase-acquisition-seal runner enforce neither the
phase enum nor the turn name, so no executable surface changed.

## Mapping

| Historical vocabulary | Current vocabulary |
| --- | --- |
| Phase `problem_framing` / "Problem Framing" | Phase `deliver` / "Deliver" |
| Informal phase shorthand "Problem" | Phase `deliver` |
| Turn `deliver` / "Turn B — Deliver" | Turn `synthesize` / "Turn B — Synthesize" |
| "Phase A" (historical) | Understanding phase, Acquire & Seal turn |
| Seal state `SEALED_READY_FOR_DELIVER`, field `deliver_allowed` | Unchanged stable spellings; read as "ready for the Deliver phase / synthesis" |

Problem framing did not disappear: it is the Deliver phase's first synthesis
step (decision frame and target screen) in the Deliver decision-memorandum
method.

## Boundaries

- Historical artifacts are never rewritten to the new vocabulary; changing
  them would falsify provenance. `phase: understanding` in existing seals
  remains valid; a historical `phase: problem_framing` value, if ever
  encountered, reads as `deliver`.
- New commissions use the current vocabulary only.
