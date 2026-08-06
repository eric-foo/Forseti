# Summer Fridays Verification Supplement Capture Handoff — 2026-08-06 v0

```yaml
retrieval_header_version: 1
artifact_role: Cold cross-lane capture handoff packet
scope: >
  Commission one bounded verification supplement of three public, independent
  instruments aimed at claims the sealed Summer Fridays corpus already holds:
  (1) Wayback Machine product-page history to verify or refute the
  reformulation, size/price-change, and claims-drift suspicions with dated
  events; (2) FDA CAERS adverse-event records as an independent signal on the
  reaction axis; (3) published INCI ingredient-list comparison against the
  named dupes to test the substitutability claim. One sitting; each
  instrument bounded below.
use_when:
  - Capturing verification evidence for the Summer Fridays Deliver run.
  - Testing the reformulation, reaction, or dupe-equivalence claims with non-self-reported sources.
authority_boundary: retrieval_only
open_next:
  - docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/p11r7_choice_outcome_rederivation_disposition_v0.md
  - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  - docs/prompts/handoffs/summer_fridays_search_interest_addendum_capture_handoff_20260806_v0.md
stale_if:
  - The Summer Fridays Deliver run this feeds is completed or re-commissioned.
  - Archive.org, the FDA CAERS distribution, or the cited product pages materially change access.
```

**What this is for:** three claims in the sealed corpus rest on customer
say-so alone — "they reformulated it," "the reaction risk is real," "the
cheap one is identical." Each has a public instrument that can confirm,
date, or refute it without asking a single customer.
**Done looks like:** one typed return plus machine-readable extracts giving
(1) a dated verdict on formula/size/price/claims changes per hero product,
(2) the CAERS record set for Summer Fridays with honest reporting-ceiling
labels, (3) a per-dupe INCI comparison verdict — each labeled with exactly
what it can and cannot conclude.

## Load Contract

- `packet_version`: `20260806_v0`
- `load_rule`: **confirm-don't-trust**. Confirm every named repo path and
  source surface before strict or actionable claims.
- output_mode: `file-write`
- `edit_permission`: `docs-write` for the exact return artifacts below;
  bounded external capture writes at the named raw root. Repository
  implementation or runtime code is read-only.
- `preflight_defaults`: `docs/prompts/templates/shared/forseti_preflight_defaults_v0.md`
  v0 — constants bound; deltas stated inline.
- `input_prompt_source`:
  `docs/prompts/handoffs/summer_fridays_verification_supplement_capture_handoff_20260806_v0.md`
- `output_artifact`:
  `docs/research/summer_fridays_ci_inputs_20260806_verification/verification_supplement_return.md`
- `output_extracts`:
  `docs/research/summer_fridays_ci_inputs_20260806_verification/verification_supplement_extracts.json`
- `raw_root`: `C:\tmp\forseti-sf-verification-supplement-20260806\data`
- `workspace`: clean receiver-owned Forseti worktree off current `main`; do
  not work in another active Summer Fridays lane.
- `dirty_state_allowance`: clean initially; only the two named return
  artifacts may become modified/untracked. Raw captures stay outside Git.
- `repo_map_decision`: not needed; exact prompt, output, and method paths are bound.

## Sourcing Authorization Boundary

This commission carries a **bounded owner authorization for exactly one
one-shot verification pull across the three named instruments** (owner
instruction, 2026-08-06, this lane). It does not authorize a standing
monitor, any other subject, or reopening the sealed Phase A corpus.

## Instrument 1 — Wayback product-page history (bounded)

Targets: `summerfridays.com` product pages and Sephora PDPs for at most the
three anchor-candidate products (Lip Butter Balm, Sheer Skin Tint, Jet Lag
Mask), plus the brand's PDP for any product a captured reformulation thread
names explicitly. Per product, sample at most **8 snapshots** spanning
2022 → present, denser around 2024–2025 (the complaint-cluster era).

Per snapshot, extract when visible: ingredient list (INCI), stated
size/fill, price, and headline claims wording. Produce per product a dated
change table: `no_change_observed` | changed, with the snapshot pair
bracketing each change.

Decision rules (state each verdict against them explicitly):
- A verified INCI change on a product with reformulation complaints →
  dated **verified formula-change event** (this is the named reopening
  trigger for the formula axis; record it, do not reopen anything yourself).
- No INCI change across the sampled span → the reformulation suspicion is
  **not supported by page evidence** (label: sampled snapshots only; a
  change between samples cannot be excluded).
- Size or price changes → dated events for the value axis.

## Instrument 2 — FDA CAERS adverse-event records (bounded)

Source: the FDA CAERS public data files (download the current distribution;
record the file date). Search for Summer Fridays across brand and product
name variants; also run the same query for two named comparator brands
(Laneige, Glossier) as scale context only.

Return: the full matching record set (dates, product named, symptom terms),
plus counts per year. Mandatory ceiling labels: CAERS is **voluntary,
unverified reporting — presence is signal, absence is not exoneration, and
counts are never incidence or rates**; comparator counts are context, never
a safety ranking.

## Instrument 3 — INCI comparison vs named dupes (bounded)

Pairs (at most five): Lip Butter Balm vs its named drugstore/dupe
alternatives from the sealed corpus (e.g., the e.l.f. and Glossier
equivalents named in the dupe threads; take exact pair names from the
coding's dupe-discourse rows, not from memory). Source: currently published
INCI lists on official brand or retailer pages (capture each page).

Per pair: ordered-list comparison — first-five-ingredient overlap, full-list
overlap, and notable actives present in one but not the other. Verdicts:
`substantially_similar_lists` | `materially_different_lists` |
`inconclusive`. Mandatory ceiling: identical ingredient *lists* do not
prove identical formulas (no concentrations); a material list difference
**does** refute "identical" at the public-evidence level. No safety or
efficacy claims.

## Drift Guard

- Three instruments, the caps above, one sitting. No standing monitors, no
  additional brands beyond the named comparators, no social/community
  acquisition, no sealed-corpus edits.
- Every quantitative statement carries its ceiling label inline.
- Wayback snapshot dates are capture dates of the archive, not event dates;
  a change is bracketed by snapshots, never point-dated beyond them.
- Preserve failures honestly: a page not archived, a CAERS distribution
  field gap, or an unpublished INCI list is a typed gap, not a reason to
  substitute a weaker source silently.

## Return Contract

The return artifact must include: (1) executive conclusion — one verdict per
instrument, three findings max; (2) per-product dated change tables
(instrument 1); (3) the CAERS record set and per-year counts with ceiling
labels (instrument 2); (4) per-pair INCI verdicts with the captured lists
(instrument 3); (5) capture receipts (URLs, snapshot ids, file dates,
sha256s of raw captures); (6) failure/gap ledger; (7) non-claims: what the
Deliver run may and may not conclude from each instrument. The extracts
file carries the machine-readable change tables, CAERS records, and INCI
comparisons with a `schema_version` field and per-record raw-capture
sha256s.

## Validation And Stop Conditions

Before closeout: fresh-read both written artifacts; verify every extract
record resolves to a retained raw capture;
run `python -B .agents/hooks/header_index.py --strict`;
run `python -B .agents/hooks/check_prompt_output_mode.py --strict`;
run `git diff --check`. Report each as pass, fail, blocked, or not run.
Stop with the nearest explicit blocker if a named source surface or output
writing cannot be verified.
