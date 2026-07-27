# Summer Fridays Google Ads Transparency Capture Handoff — 2026-07-26 v0

```yaml
retrieval_header_version: 1
artifact_role: Cold cross-lane capture handoff packet
scope: >
  Commission a bounded Summer Fridays Google Ads Transparency Center acquisition
  across the advertiser and ad formats the public surface exposes, preserving
  typed creative inventory for later Deliver-side CI.
use_when:
  - Capturing Summer Fridays ads visible in Google's Ads Transparency Center.
  - Producing the Google paid-creative input for a later Summer Fridays Deliver run.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  - forseti/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md
  - docs/prompts/templates/shared/forseti_preflight_defaults_v0.md
stale_if:
  - Google materially changes Ads Transparency Center identity, region, date, or format surfaces.
  - A Forseti Google Ads Transparency recipe card or dedicated runner supersedes this first probe.
  - The Summer Fridays company/entity authority or product-family inventory changes.
```

> **Completed:** this one-shot commission produced
> `docs/research/summer_fridays_ci_inputs_20260726/google_ads_transparency_capture_return.md`.
> Do not rerun this dated commission as live instructions. It remains only
> because the durable return cites it as provenance; no durable successor route
> is claimed here.

## Load Contract

- `packet_version`: `20260726_v0`
- `mode`: `max`
- `load_rule`: **confirm-don't-trust**. Confirm every named path, source identity,
  filter, and retained packet before making strict or actionable claims.
- output_mode: `file-write`
- `template_kind`: `none`
- `edit_permission`: `docs-write` for the exact return artifact below; bounded
  external capture writes are authorized at the named raw-lake root. Repository
  implementation/runtime code is read-only.
- `reviews`: findings-first; no formal review verdict, severity contract, or patch queue.
- `doctrine_change`: none.
- `preflight_defaults`: `docs/prompts/templates/shared/forseti_preflight_defaults_v0.md`
  v0 — constants bound; deltas stated inline.
- `input_prompt_source`:
  `docs/prompts/handoffs/summer_fridays_google_ads_transparency_capture_handoff_20260726_v0.md`
- `output_artifact`:
  `docs/research/summer_fridays_ci_inputs_20260726/google_ads_transparency_capture_return.md`
- `raw_lake_root`: `C:\tmp\forseti-sf-google-ads-discovery-20260726\data`
- `workspace`: use a clean receiver-owned Forseti worktree off current
  `origin/main`; do not work in another active Summer Fridays lane.
- `minimum_repository_checkpoint`: `6c5da01ef024f71c33013c10bec05ac65e232c9d`
  must be an ancestor of the receiver's clean `HEAD`, and this handoff must exist
  at that `HEAD`.
- `dirty_state_allowance`: clean initially; only the named return artifact may
  become modified/untracked in the repo. Raw capture data stays outside Git.
- `untracked_files_in_scope`: only the named return artifact if its destination
  directory does not yet exist.
- `repo_map_decision`: not needed; exact prompt, output, method, and lake paths are bound.
- `controlling_source_state`: re-read and record current state; modified or
  missing controlling sources block strict route claims.

```yaml
forseti_start_preflight:
  agents_read: yes
  overlay_read: yes
  source_pack: custom
  edit_permission: docs-write
  target_scope: Summer Fridays Google Ads Transparency capture plus one bounded return artifact
  dirty_state_checked: yes
  blocked_if_missing: handoff, capture playbook, recon index, writable raw-lake root, or public Ads Transparency Center surface
```

If the receiver cannot access the repository and named Windows-local lake, stop
and request a source capsule or a correctly placed receiver. Do not substitute
ordinary Google Search results for the Ads Transparency Center.

## Goal Handoff

- **Long-term goal:** help Forseti produce unusually strong company intelligence
  by connecting observable paid creative with products, channels, customer
  evidence, and company claims.
- **Active objective:** preserve the Summer Fridays advertiser identity and
  decision-usable ad inventory visible in Google's Ads Transparency Center under
  a recorded region/date/format state.
- **Fitness reference:** the later Deliver lane can compare product-family paid
  air cover across Google's publicly observable ad surfaces without inventing a
  spend ledger or treating absence as strategy.
- **Done signal:** admitted source packets and a return artifact preserve
  verified advertiser identity, bounded enumeration, creative/product typing,
  result ceilings, and exact provenance.

## Open Decision / Fork

This is a first probe of the Ads Transparency Center route. The ordinary Google
Search route decision does **not** govern this source.

- First locate the advertiser/search result substrate and route-specific fields.
- If stable advertiser and ad identifiers are visible, capture the bounded
  inventory and bank a recipe-card section.
- If the surface shows only partial ads, snippets, thumbnails, or a capped date
  range, return `PARTIAL` and preserve the limitation.
- An empty or erroring result requires a known-positive advertiser control or a
  second independent method before any target-absence conclusion.
- If access becomes authenticated/access-controlled and there is no entitled
  session, stop. Do not defeat authentication.

## Drift Guard

- Summer Fridays only. No competitor census, campaign plan, SEO plan, media-mix
  recommendation, or generalized multi-company infrastructure.
- Google Ads Transparency Center only. Do not call this “AdSense”; AdSense is not
  the commissioned source.
- Acquisition only. Do not join with Meta, retailer, Reddit, TikTok/IG/YouTube,
  SERP, ingredient, or Phase A evidence.
- Capture source-visible ads and fields only. Do not infer spend, budget, bid,
  impressions, audience, targeting, performance, conversion, share of voice,
  or strategy.
- Use the exact absence phrase: **“No Summer Fridays ad creative was observed
  on the captured Google Ads Transparency Center surface under the recorded
  advertiser/region/date/format state.”** Never shorten this to “not spending.”
- Search, YouTube, Display, or other format labels are used only when Google
  exposes them. Do not infer serving placement from creative aspect ratio or URL.
- A destination domain or advertiser name alone does not prove the correct
  advertiser entity. Resolve company identity before inventory claims.
- Public, targeted, human-rate capture only. No credential, private-person,
  exit-IP, or auth-bypass collection.

## Inherited Context

Summer Fridays is the dogfood company. Multi-company generalization is future
work. The current Phase A corpus remains sealed separately; this is a supplemental
acquisition input for a later Deliver join.

No accepted Ads Transparency Center-specific recipe card or runner was found at
the authoring checkpoint. The capture playbook therefore owns the probe method.
The existing Google Search decision
`docs/decisions/search_surface_google_parameterized_us_capture_route_v0.md`
must **not** be silently imported: it governs ordinary Google Search/SERP
captures, not the Ads Transparency Center.

## Source And Authority Ledger

Re-read these before strict claims:

1. `forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md`
   - authoring compare target SHA-256:
     `aac268200599b047c1a1a8096ed2f683197f484475761c20649a86740494d3f5`
   - role: access gate, substrate diagnosis, route selection, receipts, verdicts.
2. `forseti/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md`
   - authoring compare target SHA-256:
     `22ba2475317a731fc1aeb55ce7ab8004ad39bdc82d44dfb5e0f14c4c68244d58`
   - role: empirical route and false-block context.
3. `forseti/product/spines/capture/core/source_families/README.md`
   - role: discover any newer Google Ads source family or route card.
4. `docs/decisions/search_surface_google_parameterized_us_capture_route_v0.md`
   - authoring compare target SHA-256:
     `5a079e37f9311709c10d0d329386cc4588b2fab4a4b43f8daafa1dd28e2a0b94`
   - role: explicit boundary showing the ordinary SERP route is separate.
5. Current accepted Summer Fridays company and portfolio sources under
   `docs/research/summer_fridays_understanding_dogfood_20260725_p10/`
   - role: first-party entity and product-family normalization;
   - re-read rather than trusting this handoff's inherited summary.

External source:

- Google Ads Transparency Center, with advertiser identity, region, date window,
  format state, and capture time recorded.

## Exact Next Authorized Action

1. Bind a clean receiver worktree and confirm all named paths.
2. Run the lake-first preflight. If the raw-lake root already contains data,
   inventory it; do not overwrite or silently mix runs.
3. Confirm Summer Fridays' official company domain and legal/advertiser identity
   from retained first-party evidence.
4. Run capture-playbook Steps 0–3 against the Ads Transparency Center:
   access class → substrate/problem → cheapest matching route → packet/receipt.
5. Resolve the verified advertiser entity using both name and company domain or
   another source-native identity binding. Record ambiguous entities separately.
6. Freeze the source-visible filters before enumeration:
   advertiser, region, date window, ad format/type, sort/default state, and
   capture start/end timestamps.
7. Enumerate up to **60 unique source ad identifiers or 10 continuation actions,
   whichever comes first**. Capture a visible exhaustion signal when present.
   Above the cap, return `PARTIAL`.
8. Preserve raw source evidence and write only the named return artifact.

## Minimum Capture And Extraction Contract

For each source-visible ad, retain when exposed:

- verified advertiser identity and source profile/advertiser locator;
- source-native ad/creative identifier;
- first/last shown or other source-declared date fields;
- region and ad-format/type state;
- headline, body, CTA, visible creative/media type, media-availability state;
- destination URL/domain and visible landing-page label;
- identifiable Summer Fridays product/family/variant or brand-only classification;
- visible retailer, creator/partner, collaboration, offer, or promotion language;
- packet ID, manifest path/hash, capture time, and exact source-record pointer.

Deduplicate source ad identifiers, repeated cards, canonical destination URLs
after stripping tracking parameters, and byte-identical/reused creative while
retaining ad-instance-to-creative relationships.

The return artifact must include:

1. executive acquisition conclusion;
2. route verdict and recipe-card section;
3. advertiser-identity proof and rejected ambiguities;
4. filter/window receipt and enumeration ceiling;
5. unique-ad inventory;
6. creative/message clusters;
7. product-family coverage matrix;
8. explicit “no observed creative” rows only for freshly verified portfolio families;
9. failure/omission ledger;
10. complete source packet bundle with hashes;
11. safe later-Deliver uses and non-claims.

## Validation And Stop Conditions

Before closeout:

- fresh-read the return artifact;
- dereference every ad row to retained source evidence;
- recompute unique-ad, creative, and family counts;
- verify raw-lake manifests against preserved files using current lake tools;
- run `python -B .agents/hooks/header_index.py --strict`;
- run `python -B .agents/hooks/check_prompt_output_mode.py --strict`;
- run `git diff --check`.

Report each as pass, fail, blocked, or not run. A non-error page or screenshot
without verified advertiser identity and decision-material creative detail is
not success. Stop with the nearest explicit blocker if identity, access,
provenance, packet admission, or output writing cannot be verified.
