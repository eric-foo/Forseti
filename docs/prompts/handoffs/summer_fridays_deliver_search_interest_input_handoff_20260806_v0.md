# Summer Fridays Deliver — Search-Interest Input Handoff — 2026-08-06 v0

```yaml
retrieval_header_version: 1
artifact_role: Cold cross-lane evidence-input handoff packet
scope: >
  Route the completed 2026-08-05 Google Trends search-interest capture into
  the Summer Fridays Deliver run as a decision-scoped supplement alongside the
  sealed Phase A corpus: product prize ranking (attention level and
  direction), the independent destination-attention test, seasonality timing,
  and the dupe-demand read for the Deliver target screen.
use_when:
  - Executing or planning the Summer Fridays Deliver run target screen.
  - Consuming Summer Fridays search-interest evidence in any Deliver-phase
    artifact.
authority_boundary: retrieval_only
open_next:
  - docs/research/summer_fridays_ci_inputs_20260805/search_interest_capture_return.md
  - docs/research/summer_fridays_ci_inputs_20260805/search_interest_series.json
  - docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/turn_a_consumer_brand_v3_acquisition_record.md
stale_if:
  - A newer Summer Fridays search-interest pull supersedes the 2026-08-05
    capture.
  - The Summer Fridays Deliver run this feeds is completed or re-commissioned
    with a different target screen.
  - The Phase A corpus seal is lifted or re-cut by owner decision.
```

**Goal:** the Deliver target screen ranks Summer Fridays products by prize and
tests the Phase A switching destinations against evidence nobody
self-reported.
**Done looks like:** Deliver-phase artifacts cite the capture return and
series by path and hash, use only claims the return's §10 non-claims section
permits, and mark every below-threshold term with the exact required phrase.

## Load Contract

- `packet_version`: `20260806_v0`
- `mode`: max (cold cross-lane packet)
- `load_rule`: **confirm-don't-trust** — the digest below is orientation; the
  return artifact and series file are the evidence of record. Re-verify
  hashes, then fresh-read §1–§10 of the return artifact before any
  Deliver-phase claim.
- output_mode: `chat-only` — this packet routes evidence inputs and binds
  claim limits only; the consuming Deliver commission defines and owns its own
  output artifacts.
- `edit_permission`: `read-only` with respect to everything this packet names.
  The capture artifacts, the sealed Phase A corpus, and its seal are not to be
  edited, reopened, or reinterpreted from this lane.
- `preflight_defaults`: `docs/prompts/templates/shared/forseti_preflight_defaults_v0.md`
  v0 — constants bound by pointer; deltas inline.
- `input_prompt_source`:
  `docs/prompts/handoffs/summer_fridays_deliver_search_interest_input_handoff_20260806_v0.md`
- `landing_state_note`: at packet time the two capture artifacts were
  **untracked, not yet landed**, authored on branch
  `claude/summer-fridays-search-handoff-54dc62` (head
  `93e525c323c4a4d27fcdd19304a00681d2b8891e`). Compare targets:
  `search_interest_capture_return.md` sha256
  `41c09ce51bfa27e952acdc6db19de1a719a8a7d0ac7b1d1caacada4591663743`
  (26,463 bytes); `search_interest_series.json` sha256
  `2b3c777ae900fa672fff1f23a06f6c0b42bb67041344b4d8bf08a4e2d52bec8b`
  (890,866 bytes). If the artifacts are not at the receiver's HEAD, read them
  from that branch/worktree or request landing; a hash mismatch is
  `STALE_REREAD_REQUIRED`, not silent reuse.
- Raw exports (verbatim Google responses, receipts, run logs) are outside Git
  at `C:\tmp\forseti-sf-search-interest-discovery-20260805\data` —
  machine-local supplementary provenance, not required for Deliver use.

## What This Capture Is (position in Phase A)

A **decision-scoped supplement** to Phase A: one bounded, owner-authorized
Google Trends pull (2026-08-05) commissioned by
`docs/prompts/handoffs/summer_fridays_search_interest_capture_handoff_20260805_v0.md`.
It is COMPLETE (all 13 batches, all 5 related panels). It does not amend the
sealed Phase A corpus; it stands beside it, and it is not the standing
demand-durability series (that remains unauthorized).

## Decision Digest (orientation only — verify in the return artifact)

1. **Prize ranking (attention level and direction):** Lip Butter Balm ≫ Jet
   Lag Mask ≈ Dream Lip Oil > Sheer Skin Tint (rising fastest from the
   smallest base) ≫ Cloud Dew / ShadeDrops / Rich Cushion / Dream Oasis (at or
   below the reporting threshold). Return artifact §3.
2. **Destination test (the Phase A cross-check):** every captured named
   switching destination — lip: Laneige, Rhode, Aquaphor, Lanolips; tint:
   Ilia, Saie, Hourglass, Kosas, Armani — holds a level-or-rising curve; none
   is decaying. Most out-level their SF counterpart (Laneige ~4× Lip Butter
   Balm; Ilia ~5×, Saie ~3×, Hourglass ~2.5× the SF tint). §4.
3. **Timing:** brand attention peaks November–December and troughs
   July–August; the 2024 annual peak has not been re-attained, and the decline
   is US-led (worldwide gentler). §7. (The capture itself ran in the seasonal
   trough — read absolute recent levels with that in mind.)
4. **Dupe demand:** real at brand level, emerged 2024, peaked April 2025, past
   peak and cooling in the 12-m window; product-level dupe phrasing is below
   threshold except inside the Jet Lag Mask related panel. §5.
5. **Related-query texture:** brand panel is lip-dominated with flavor-drop
   breakouts; `rhode` (+4,100% rising) and `laneige` appear inside the brand's
   own panel; no literal "x vs y" queries anywhere. §6.

## Drift Guard (binding claim limits — from the return artifact §10)

- Every value is a Google Trends **0–100 relative index normalized within its
  batch**. Never convert to sales, demand size, prevalence, market share, or
  population rates; never present index points as counts.
- Below-threshold terms use the exact phrase **"below the Google Trends
  reporting threshold under the recorded geo/window"** — never "no interest"
  or "no demand". The threshold ledger is return artifact §8.
- Branded search mixes curiosity, dupe-hunting, and purchase intent — record
  curves, do not attribute motive.
- Single-pull comparability: 2026-08-05 values are not directly comparable to
  any future pull without re-anchoring (freeform terms, no entity IDs).
  Cross-batch comparison inside this capture goes through the anchor map
  (§2), anchor term "summer fridays lip butter balm".
- Do not reopen, edit, or reinterpret the sealed Phase A corpus or its seal.
- The two related-panel families with source-side empty "rising" lists are
  nulls from Google, not capture gaps.

## Exact Next Authorized Action

1. Verify both compare targets, then fresh-read the return artifact in full
   (it is ~26 KB; §1–§10).
2. Consume the evidence in the Deliver target screen per the Deliver
   commission's own contract, citing
   `docs/research/summer_fridays_ci_inputs_20260805/` paths and hashes.
3. For machine reads (charts, stacking, recomputation), consume
   `search_interest_series.json` — one record per (term, geo, window, batch)
   with per-record capture params, threshold flags, and raw-export sha256s.
4. Stop conditions: hash mismatch or missing artifacts (see
   `landing_state_note`); any Deliver claim that §10 does not permit; any need
   for a fresh pull (requires new owner authorization).

## Superseded / Dangerous-To-Reuse Context

- Interim PARTIAL states of the capture (8/13, 9/13, 11/13) circulated in the
  authoring chat during 2026-08-05 — superseded by the COMPLETE return; use
  only the final artifacts at the hashes above.
- An early reduced reconstruction of one explore receipt
  (`b09_explore.json`) was superseded by a verbatim re-capture the same
  morning; the raw-root manifest records both. Irrelevant to Deliver-level
  use.
- The one-day rate-limit observations in §9 are method lore for the capture
  lane (see the sibling refinement handoff
  `docs/prompts/handoffs/search_interest_browser_capture_refinement_handoff_20260806_v0.md`),
  not Deliver-relevant evidence.
