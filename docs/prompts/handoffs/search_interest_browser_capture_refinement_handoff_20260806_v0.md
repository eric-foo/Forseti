# Search-Interest Browser-Capture Method Refinement Handoff — 2026-08-06 v0

```yaml
retrieval_header_version: 1
artifact_role: Cold cross-lane method-refinement handoff packet
scope: >
  Commission one bounded documentation pass that folds the empirically proven
  browser-route Google Trends capture method — validated end-to-end in the
  2026-08-05 Summer Fridays search-interest capture — into the owned capture
  sources, so future search-interest pulls start from the working method
  instead of re-learning a day of rate-limit lessons.
use_when:
  - Refining or documenting the Google Trends browser-route capture method.
  - Preparing any future search-interest pull (any brand) that will hit the
    Trends web endpoints.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/demand_durability_indicators/search_interest/demand_durability_indicator_search_interest_capture_profile_v0.md
  - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  - docs/research/summer_fridays_ci_inputs_20260805/search_interest_capture_return.md
stale_if:
  - Google materially changes the Trends explore/widgetdata endpoints, token
    scheme, or rate-limit behavior.
  - The capture profile or playbook already carries a newer browser-route
    method section superseding the 2026-08-05 lessons.
```

**Goal:** future Trends pulls should succeed in under an hour by following a
documented method, not by rediscovering quota behavior.
**Done looks like:** the owning capture sources carry the browser-route method
(endpoints, pacing, session/IP behavior, extraction paths, failure playbook),
each lesson traceable to the 2026-08-05 run evidence, with no standing-series
or sourcing authorization implied.

## Load Contract

- `packet_version`: `20260806_v0`
- `mode`: max (cold cross-lane packet)
- `load_rule`: **confirm-don't-trust** — every load-bearing fact below carries
  a compare target; re-verify before strict or actionable claims. This packet
  orients; it is not authority.
- `output_mode`: `file-write` — targets are the two owning capture sources in
  `open_next` above (update in place; do not create a parallel method doc).
- `edit_permission`: `docs-write` for those two sources only. No runtime code,
  no new pulls, no skill or overlay edits.
- `preflight_defaults`: `docs/prompts/templates/shared/forseti_preflight_defaults_v0.md`
  v0 — constants bound by pointer; deltas inline.
- `input_prompt_source`:
  `docs/prompts/handoffs/search_interest_browser_capture_refinement_handoff_20260806_v0.md`
- `workspace`: receiver-owned clean Forseti worktree.
- `expected_branch_note`: the evidence artifacts named below were authored on
  branch `claude/summer-fridays-search-handoff-54dc62` (head
  `93e525c323c4a4d27fcdd19304a00681d2b8891e`) and were **untracked, not yet
  landed** when this packet was written. Confirm landing state first; if not
  landed, read them from that worktree or request landing before strict use.
- `dirty_state_allowance`: clean initially; only the two named target sources
  may become modified.

## Open Decision / Fork

1. **Where the method lives**: fold into the capture profile's
   limits-visibility section vs. a new browser-route section in the playbook
   vs. both (profile = source semantics, playbook = capture mechanics).
   Recommendation: both, split by ownership — profile owns index/threshold
   semantics (already there), playbook owns the operational method. Owner of
   the call: receiver, within docs-write scope.
2. **Verification pull**: the refined method text can be written from the
   recorded evidence alone. A live verification pull is NOT authorized by this
   packet; if the receiver believes one is needed, stop and request owner
   authorization rather than pulling.
3. **Runner script**: a reusable in-page runner script would be implementation
   work — not authorized here; record as deferred with its trigger if judged
   valuable.

## Drift Guard

- This packet authorizes **method documentation only**. It does not authorize
  any Google Trends request, the standing demand-durability series, a cadence,
  vendor selection, or implementation/runtime work.
- Sourcing for search-interest remains **not generally authorized** per the
  capture profile; the 2026-08-05 pull was a bounded one-shot owner exception.
  Do not write anything that implies standing authorization.
- Do not defeat rate limits, and do not document any technique whose purpose
  is defeating them; the method's core is compliant pacing and session
  hygiene.
- Do not reopen the Summer Fridays evidence artifacts' conclusions; this lane
  consumes their §9 failure/omission ledger as method evidence only.

## Inherited Context

Source-loading: per `.agents/workflow-overlay/source-loading.md` (overlay
policy pointer); enter the ladder at the three `open_next` targets. Read
`AGENTS.md` and `.agents/workflow-overlay/README.md` first per repo routing.

Earlier-decided context (orientation only; verify at the pointer):

- The capture profile records search-interest sourcing as owner-gated and owns
  relative-index/threshold semantics — decided in the profile
  (`open_next[0]`); verify before writing near those sections.
- The 2026-08-05 capture return is the evidence corpus for every method claim
  below — `docs/research/summer_fridays_ci_inputs_20260805/search_interest_capture_return.md`,
  sha256 `41c09ce51bfa27e952acdc6db19de1a719a8a7d0ac7b1d1caacada4591663743`
  (26,463 bytes). Its §2 (receipts), §9 (failure/omission ledger) are the
  load-bearing sections.
- Raw request-level logs live outside Git at
  `C:\tmp\forseti-sf-search-interest-discovery-20260805\data` (machine-local;
  manifest.jsonl sha256
  `35894ba8702aed5f5a8e7701925a3f9990a3ebd39689aa87b4af820e88cececc`,
  12,435 bytes at packet time). Load-bearing: no (the return artifact carries
  the needed summaries); use only if per-request detail is wanted.

## The Method Evidence To Fold In (from the 2026-08-05 run)

Each item is traceable to the return artifact §9 ledger and run logs; verify
there before strict claims.

1. **Endpoint anatomy.** The Trends UI is backed by two endpoint families:
   `POST /trends/api/explore` (mints widget tokens; cheap — never rate-limited
   across ~25 same-day calls) and `GET /trends/api/widgetdata/multiline|relatedsearches?req=...&token=...`
   (returns the actual data; aggressively quota'd). Tokens embed the resolved
   request; comparison explores emit indexed widget ids
   (`RELATED_QUERIES_0..N` with `keywordName` per term); single-term explores
   emit unsuffixed ids. Responses are JSON with a `)]}',`-style prefix to
   strip.
2. **Session/IP behavior.** Google stamps `userType: USER_TYPE_SCRAPER` into
   widget tokens by IP reputation, not browser environment: an automation
   pane, the owner's real signed-in Chrome, and a VPN egress all received the
   same flag on the same day. Datacenter/VPN ranges (observed: AS60068
   Datacamp) are pre-flagged. The flag correlates with a tight `widgetdata`
   quota.
3. **Quota shape (empirical, one day, one machine).** A fresh-to-Trends IP
   yields 1–2 quick `widgetdata` successes, then hard 429s; recovery arrives
   in drips (observed successes at gaps of ~20 min to ~2.5 h). ~55–75s pacing
   was too hot; sustained success came from 7–45 min retry rounds. Quiet
   periods (30–60 min) sometimes, not always, reset the drip. The
   `relatedsearches` endpoint is quota'd separately but similarly.
4. **Working capture pattern.** In-page `fetch()` from a real browser session
   on trends.google.com (page context, session cookies), driven by an injected
   sequential runner with jittered pacing, per-item retry with 120–150s
   cooloffs, then escalating patient rounds for stragglers. Verbatim response
   bodies retained with sha256 + UTC receipts per file (append-only manifest).
5. **Extraction paths by surface.** App-embedded browser pane: POST to a
   localhost receiver works. Real Chrome via extension: localhost is gated by
   local-network permission (hangs) and base64 tool returns are blocked by an
   exfiltration guard — the working path is bundling captures into one JSON
   blob and downloading it via a normal browser download, then reading it from
   disk. Undisplayed automation panes never fire the page's own widget
   requests (lazy rendering) — the in-page API fetch pattern is required.
6. **Failure playbook.** `pytrends` 429'd from the first probe (dead route);
   direct `/trends/explore` navigation without a session 429s (homepage-first
   establishes the session); on persistent 429 the productive moves are, in
   order: slower rounds on the same IP, a genuinely different residential IP,
   or waiting for quota drip — never tighter loops.
7. **Comparability discipline** (already owned by the profile — point, don't
   restate): per-batch 0–100 normalization, shared-anchor bridging across
   batches, exact below-threshold phrasing, single-pull date pinning.

## Exact Next Authorized Action

1. Fresh-read both target sources and the return artifact §2/§9 (confirm
   compare targets above).
2. Write the browser-route method into the two owning sources per Open
   Decision 1, each claim consistent with the recorded evidence; keep
   authorization boundaries per Drift Guard.
3. Validate: `python -B .agents/hooks/header_index.py --strict`,
   `python -B .agents/hooks/check_prompt_output_mode.py --strict`,
   `git diff --check`; report pass/fail/blocked/not-run.
4. Stop conditions: target sources missing or materially diverged from the
   pointers above; evidence artifacts unreachable and unlanded; any step
   requiring a live Trends request.

## Superseded / Dangerous-To-Reuse Context

- The 2026-08-05 quota numbers are one-day, one-machine observations — reuse
  as engineering priors, not as stable Google behavior. Label them with their
  observation date in the method text.
- `run_log_fix.json` retry cadences (150–210s) were themselves too hot that
  day; the later 7–45 min rounds are the pattern that worked.
