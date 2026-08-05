# Summer Fridays Search-Interest Capture Handoff — 2026-08-05 v0

```yaml
retrieval_header_version: 1
artifact_role: Cold cross-lane capture handoff packet
scope: >
  Commission one bounded, one-shot Google Trends search-interest capture for
  the Summer Fridays Deliver target screen: relative attention trajectories for
  Summer Fridays products, head-to-heads against the Phase A named switching
  destinations, dupe-demand terms, related/rising queries, and seasonality.
  Decision-scoped supplement; not the standing demand-durability series.
use_when:
  - Capturing Summer Fridays search-interest evidence for the Deliver target screen.
  - Producing the search-trend input for a later Summer Fridays Deliver run.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/demand_durability_indicators/search_interest/demand_durability_indicator_search_interest_capture_profile_v0.md
  - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  - docs/prompts/templates/shared/forseti_preflight_defaults_v0.md
stale_if:
  - Google materially changes Trends access, comparison limits, or export fields.
  - A dedicated search-interest source family, recipe card, or runner supersedes this first probe.
  - The Summer Fridays Deliver run this capture feeds is completed or re-commissioned with a different target screen.
```

**What this is for:** the Deliver target screen must rank Summer Fridays
products by prize (attention level and direction), and test whether the named
switching destinations from Phase A are gaining attention independently of our
qualitative evidence.
**Done looks like:** a return artifact plus machine-readable series showing,
for each bound query set, the relative-interest curves with capture parameters,
anchor bridging, null/threshold rows, and no claim beyond relative search
attention.

## Load Contract

- `packet_version`: `20260805_v0`
- `load_rule`: **confirm-don't-trust**. Confirm every named repo path, branch,
  and source surface before strict or actionable claims.
- output_mode: `file-write`
- `edit_permission`: `docs-write` for the exact return artifacts below; bounded
  external capture writes at the named raw root. Repository implementation or
  runtime code is read-only.
- `preflight_defaults`: `docs/prompts/templates/shared/forseti_preflight_defaults_v0.md`
  v0 — constants bound; deltas stated inline.
- `input_prompt_source`:
  `docs/prompts/handoffs/summer_fridays_search_interest_capture_handoff_20260805_v0.md`
- `output_artifact`:
  `docs/research/summer_fridays_ci_inputs_20260805/search_interest_capture_return.md`
- `output_series`:
  `docs/research/summer_fridays_ci_inputs_20260805/search_interest_series.json`
- `raw_root`: `C:\tmp\forseti-sf-search-interest-discovery-20260805\data`
- `workspace`: clean receiver-owned Forseti worktree; do not work in another
  active Summer Fridays lane.
- `minimum_repository_checkpoint`: `93e525c323c4a4d27fcdd19304a00681d2b8891e`
  must be an ancestor of the receiver's clean `HEAD`, and this handoff must
  exist at that `HEAD`.
- `dirty_state_allowance`: clean initially; only the two named return artifacts
  may become modified/untracked. Raw exports stay outside Git.
- `repo_map_decision`: not needed; exact prompt, output, method, and term-source
  paths are bound.

## Sourcing Authorization Boundary

The search-interest capture profile
(`forseti/product/spines/capture/core/demand_durability_indicators/search_interest/demand_durability_indicator_search_interest_capture_profile_v0.md`)
records sourcing as not generally authorized. This commission carries a
**bounded owner authorization for exactly one one-shot pull** scoped to the
Summer Fridays Deliver target screen (owner instruction, 2026-08-05, this
lane). It does not authorize the standing demand-durability series, a cadence,
or any other subject. The profile's limits-visibility obligations (relative
index semantics, comparability constraints, cold-start and threshold caps)
apply to what this capture records; its series/cadence machinery does not.

## Drift Guard

- Summer Fridays and the Phase A named destinations only. No portfolio-wide
  category monitor, no additional brands, no standing series.
- Relative search attention only. Google Trends values are a source-declared
  0–100 relative index. Do not convert to sales, demand size, prevalence,
  market share, or population rates, and do not present index points as counts.
- A below-threshold or empty result is a threshold artifact. Use the exact
  phrase: **"below the Google Trends reporting threshold under the recorded
  geo/window"** — never "no interest" or "no demand."
- Branded search mixes curiosity, dupe-hunting, and purchase intent. Record
  curves; do not attribute motive.
- Do not reopen, edit, or reinterpret the sealed Phase A corpus or its seal.
- Public, human-rate capture only. If automated access (e.g., pytrends) is
  blocked or returns inconsistent values versus the UI, prefer the UI export
  and record the discrepancy; do not defeat rate limits.

## Term Sources

Derive the exact term lists from freshly read Phase A artifacts — do not treat
this handoff's prose as the term authority:

1. Product names and hero candidates:
   `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/turn_a_consumer_brand_v3_acquisition_record.md`
   (product-axis table and product contexts).
2. Named switching destinations per axis:
   `docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/evidence_depth_ledger.json`
   (`product_axes[].decision_usefulness` named alternatives).

## Bounded Query Families

Run these six families; freeze geo (`US` primary, worldwide secondary check),
windows (5-year and 12-month), property (web search), and category filter
before capture, and record them per batch. Every batch of more than one term
shares one recurring anchor term so cross-batch comparison stays honest. Cap:
**at most 14 comparison batches total**; if a family cannot fit, return
`PARTIAL` with the cut list rather than silently dropping terms.

1. **SF product vs. SF product** — the target-screen prize read (balm, skin
   tint, Jet Lag Mask at minimum, per the freshly read product authority).
2. **Lip Butter Balm vs. named lip destinations** (e.g., Laneige, Rhode,
   Aquaphor/Lanolips price-floor terms as recorded in the ledger).
3. **Skin tint vs. named tint destinations** (per ledger named alternatives).
4. **Dupe-demand terms** — "summer fridays dupe", "lip butter balm dupe", and
   ledger-derived variants.
5. **Brand seasonality** — "summer fridays" brand curve, 5-year window,
   seasonal swing and peak months.
6. **Related and rising queries** — capture the related/rising panels for the
   brand and hero-product terms; comparison-shaped queries ("x vs y") are
   priority rows.

## Minimum Capture And Extraction Contract

Per batch, retain: term set, anchor term, geo, window, property, category,
capture timestamp, raw export (CSV or equivalent) in the raw root, and the
extracted series. The `search_interest_series.json` must carry one record per
(term, geo, window) with: relative-index series, source batch id, anchor term,
threshold/null flag, and capture parameters — machine-readable so later runs
and other brands can stack onto it.

The return artifact must include:

1. executive capture conclusion (three findings max, labeled relative-attention only);
2. capture-parameter receipt per batch and the anchor-bridging map;
3. trajectory read per SF product (rising / flat / decaying, with window);
4. destination head-to-head table;
5. dupe-demand read;
6. related/rising query inventory with comparison queries flagged;
7. seasonality read;
8. threshold/null ledger (every below-threshold term listed);
9. failure/omission ledger;
10. non-claims: what the Deliver target screen may and may not conclude from
    this capture.

## Validation And Stop Conditions

Before closeout:

- fresh-read both written return artifacts;
- verify every series record resolves to a retained raw export;
- recompute batch and term counts from the series file;
- run `python -B .agents/hooks/header_index.py --strict`;
- run `python -B .agents/hooks/check_prompt_output_mode.py --strict`;
- run `git diff --check`.

Report each check as pass, fail, blocked, or not run. A rendered chart or
HTTP 200 without recorded capture parameters is not source-useful success.
Stop with the nearest explicit blocker if term sources, the Trends surface,
anchor bridging, or output writing cannot be verified.
