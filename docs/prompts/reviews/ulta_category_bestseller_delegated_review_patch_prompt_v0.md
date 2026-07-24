# Delegated Review-and-Patch Commission — Ulta Category Bestseller Runtime Diff

```yaml
retrieval_header_version: 1
artifact_role: Delegated review-and-patch commission prompt (operator-couriered)
scope: >
  Operator-couriered commission for a DIFFERENT-VENDOR reviewer to review and
  patch the Ulta category bestseller runtime diff on branch
  claude/ulta-category-bestseller-parity; home model (Claude) adjudicates.
use_when:
  - Running the de-correlated delegated review-and-patch on the Ulta category lane.
authority_boundary: retrieval_only
output_mode: paste-ready-chat
```

`lane_mode: advisory-commission (operator-couriered, external-controller)`
`terminal: operator delivers this to a DIFFERENT-VENDOR reviewer; home model (Claude) adjudicates`

## Review target now on the remote

The branch `claude/ulta-category-bestseller-parity` is pushed to `origin`
(`github.com/eric-foo/forseti`). A reviewer in **any** checkout can obtain the diff:

```
git fetch origin main claude/ulta-category-bestseller-parity
git diff origin/main...origin/claude/ulta-category-bestseller-parity -- forseti-harness/
```

Review that pushed diff. The local-worktree path in §1 is the author's machine only;
use the fetched remote refs above if that path is absent in your filesystem.

## 0. READ FIRST — de-correlation is a who-constraint

- The authoring / home / adjudicating model is **Anthropic Claude (Opus)**.
- You, the reviewer (controller), **must be a different vendor lineage** — e.g. OpenAI (GPT/Codex), Google (Gemini), Mistral, DeepSeek. A different *tier* of Claude/Anthropic does **not** satisfy de-correlation.
- **If you are an Anthropic-family model, STOP** and tell the operator this paste target defeats de-correlation; do not review.
- You are the **controller**: you review and may patch within the bounded scope, in the **working tree only**. Your diff, citations, and verdict are **claims**; the home model adjudicates before anything is kept. You are **not** final over the home model.
- No self-review shortcut, no spawning your own reviewer.

## 1. Repository + immutable revision

- Worktree (Windows; use PowerShell for git/python): `C:\tmp\forseti-ulta-category-bestseller-parity`
- Set for python: `$env:PYTHONPATH='C:\tmp\forseti-ulta-category-bestseller-parity\forseti-harness'` and run from `forseti-harness`.
- Branch: `claude/ulta-category-bestseller-parity`. Review the **runtime diff only**:
  ```
  git -C C:\tmp\forseti-ulta-category-bestseller-parity diff origin/main...HEAD -- forseti-harness/
  ```
- Read the changed files **in full** (not just hunks):
  `source_capture/ulta_brand_grid.py`, `source_capture/ulta_grid_projection.py`,
  `source_capture/adapters/ulta_us_market.py`, `source_capture/adapters/cloakbrowser_snapshot.py`,
  `source_capture/retail_capture_profiles.py`, `runners/run_source_capture_cloakbrowser_packet.py`,
  and tests `tests/unit/test_retail_grid_projection.py`, `tests/unit/test_source_capture_cloakbrowser_snapshot.py`.
- Live dogfood evidence (5 projections, verified complete): `C:\tmp\ulta_5cat_dogfood\<cat>_projection.json` and `C:\tmp\ulta_5cat_dogfood\<cat>\` (cats: makeup, skincare, hair, fragrance, bath_body).
- Baseline: **255 focused tests pass** at this revision.

## 2. What the change does

Adds Ulta **category** bestseller capture on the `/shop/<category>/all?sort=best_sellers` route, reusing the existing Ulta brand-grid card parser (proven byte-compatible on the real DOM). New category semantics only:
- `ulta_brand_grid.py`: capture the selected sort id (`best_sellers`) from the Sort-By control (`data-testid="dropdown__header__value"` → its `id`) into the state + content record; `None` on brand grids.
- `ulta_grid_projection.py`: `_requested_category_slug` (parses `/shop/<cat>/all`) + a category branch `_build_ulta_category_grid_result` with subject binding (category slug ↔ rendered `<h1>` via `_slugify`), native-order confirmation (`selected_sort_id == "best_sellers"`), `page_kind=category_grid`, and a **bounded top-window** completeness (declared cohort is context; a still-present load-more control / "more available" is NOT an error). The `/brand/<slug>` path is an early-return-avoided branch and must stay byte-identical.
- `adapters/ulta_us_market.py` + runner `_validate_ulta_us_market_url`: accept `/shop/<cat>/all` for the grid US-route conjunction (the conjunction itself is URL-agnostic and reused unchanged).
- `retail_capture_profiles.py`: `ulta_category_grid_aggregate` profile (`button.LoadContent__button` continuation).
- runner: `_ULTA_GRID_PROFILES` set wired into grid dispatch, market page-kind, and projection-request validation; `detect_retail_grid_retailer` admits ulta `/shop/<cat>/all`.
- `adapters/cloakbrowser_snapshot.py`: after the load-more loop, scroll to the bottom + settle so a view-triggered terminal footer ("You have viewed N of M") serializes reliably. **Shared** across all load-more captures.

## 3. Success contract the change must meet (S1–S8)

- **S1** native bestseller identity from source-native evidence (serialized `best_sellers`), never inferred from DOM order / ratings / price.
- **S2** five exact category subjects; category identity must NOT reuse `/brand/<slug>` semantics.
- **S3** bounded top-window completeness; reconcile declared count, captured placements, unique parents, duplicates, continuation/terminal. NOTE: "complete" means the *bounded requested window* is reconciled — matching the Sephora precedent (720 of a 2513 cohort, `has_more=true`, is `complete`/`requested_page_window_reconciled`) — NOT that the whole category was captured.
- **S4** ordered identity + duplicates kept visible (never silently erased); contiguous ranks for the retained window.
- **S5** truthful US route (reuse the en-US site conjunction); currency/delivery stay unpinned.
- **S7** must NOT weaken current Ulta brand-grid, PDP, Sephora, Target, or shared retail behavior.

## 4. Bounded patch scope + hard stops

- **Editable:** `forseti-harness/**` working tree only (the changed files above and their focused tests).
- **Off-scope — flag, do NOT edit:** anything outside `forseti-harness/`; changes to brand-grid / PDP / Sephora / Target / other-retailer behavior beyond what a fix strictly requires; architectural redesigns; the source upstream of any generated artifact. If the correct fix is off-scope, flag it and stop there.
- **Lifecycle HARD STOP — working-tree edits only:** NO commit, push, PR, merge, stash, reset, branch surgery, or any repo hygiene.

## 5. Review method + focus

Run an adversarial **code review**, then apply minimal working-tree patches for real in-scope defects. Focus:

1. **Category-branch correctness** (`_build_ulta_category_grid_result`, `_requested_category_slug`, sort capture): None-handling, off-by-one, reconciliation errors, subject-binding false pos/neg (e.g. a `/shop/<x>/all` slug colliding with a brand; `_slugify` of a category `<h1>` that doesn't fold to the slug).
2. **Brand-grid / shared regression risk (S7):** is the `/brand/<slug>` path byte-identical? Does the shared `detect_retail_grid_retailer` / adapter scroll change affect PDP, Sephora, Target, or other load-more captures?
3. **Shared adapter scroll change:** any lifecycle/timing/failure-visibility harm to other retailers' load-more captures.
4. **Native-order robustness (S1):** is `selected_sort_id` extraction anchored correctly and round-tripped through the content record? Can a non-bestseller or absent sort slip through as confirmed?
5. **Bounded-window semantics (S3):** is "complete" truthful, or could a genuinely short/failed capture be mislabeled complete? Are declared/viewed/more_available reconciled correctly?
6. **Wiring completeness:** every `ulta_grid_aggregate` decision site updated for the new profile via `_ULTA_GRID_PROFILES` — any missed site that misroutes the category profile?
7. **Continuation redesign to deterministic `?page=N` pagination (OWNER-DIRECTED — highest value, the main ask):** the current Load-More click loop is flaky — dogfood windows varied 128–384 for a fixed 5-click budget because the loop breaks on a transient `load_more_selector` `count()==0` between clicks and/or a scroll-height-stable stop, silently under-capturing (e.g. 128 of 7092). Ulta fixes `pageSize:64` (no page-size URL param exists — confirmed) and paginates via `loadMoreTemplateUrl = /shop/<cat>/all?page=%1`. **The owner has decided to replace the flaky Load-More clicking with a deterministic `?page=N&sort=best_sellers` multi-page traversal** that navigates pages `1..N` in one browser session, collects each page's rendered cards, assigns global ranks `((page-1)*64 + local_position)`, merges, and reconciles the terminal (a page returning `<64` or empty, or `page > ceil(resultCount/64)`). The in-repo template to mirror is **`forseti-harness/source_capture/adapters/sephora_catalog_traversal.py`** (a pre-capture plugin exposing `grid_page_doms` / `grid_page_urls`, consumed by the runner's multi-page grid path) plus its aggregate reconciliation in `retail_grid_projection.py` (`_sephora_catalog_grid_reconciliation`). **Implement this in the working tree if it fits the bounded patch scope**; if it is genuinely too large for a bounded patch, return a concrete, file-by-file `NEEDS_ARCHITECTURE_PASS` design for it (touch points, new plugin shape, content-record shape, reconciliation, tests) rather than leaving the flaky loop. Preserve the existing behavior for `/brand/<slug>` and every other retailer. This is the highest-value item; prioritize it.
8. **Test adequacy:** do the 5 new category tests exercise the wrong-cause paths, or are any assertions vacuous/misaligned?

## 6. Escalation valve

If a finding is design-level (architecture), **stop patching, revert any partial diff** (leave no kept patch), and return findings only labeled `NEEDS_ARCHITECTURE_PASS`.

## 7. Deliverable (operator carries this home for adjudication)

- **Findings:** each with severity (blocker/major/minor/nit), `file:line`, the concrete defect, a failing scenario, and a **source citation** (neutral in tone, decision-sufficient in substance — cite the exact code that makes it wrong).
- **Unified working-tree diff** of any patches you applied.
- **Verdict:** `SHIP_AS_IS` / `PATCH_THEN_SHIP` / `BLOCK` / `NEEDS_ARCHITECTURE_PASS`, plus a **residual-risk note**.
- **Validation:** run the focused suite and report the result:
  ```powershell
  $env:PYTHONPATH='C:\tmp\forseti-ulta-category-bestseller-parity\forseti-harness'
  cd C:\tmp\forseti-ulta-category-bestseller-parity\forseti-harness
  python -m pytest -p no:cacheprovider -q --basetemp C:\tmp\ulta_delegated_review_pt `
    tests/unit/test_ulta_us_market_wiring.py `
    tests/unit/test_retail_capture_profiles.py `
    tests/unit/test_retail_grid_projection.py `
    tests/unit/test_source_capture_cloakbrowser_snapshot.py `
    tests/unit/test_ulta_onboarding_capture.py
  git -C C:\tmp\forseti-ulta-category-bestseller-parity diff --check
  ```
  Report actual pass/fail counts and any not-run reasons. An exit code alone is not proof.

## 8. Adjudication (home model — for the operator's awareness, not your task)

The home model (Claude) will treat your diff, citations, and verdict as claims: accept / modify / reject each change against the citations and the artifact's intent, revert rejected hunks, re-run validation, and reserve final veto. Make your citations strong enough to survive that.
