# Summer Fridays Meta Ad Library Capture Handoff — 2026-07-26 v0

```yaml
retrieval_header_version: 1
artifact_role: Cold cross-lane capture handoff packet
scope: >
  Commission a bounded Summer Fridays Meta Ad Library acquisition that preserves
  observable active commercial creative and product-family coverage for later
  Deliver-side CI. This packet does not authorize the later cross-source join.
use_when:
  - Capturing Summer Fridays commercial ads visible in the Meta Ad Library.
  - Producing the paid-creative inventory input for a later Summer Fridays Deliver run.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  - forseti/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md
  - docs/prompts/templates/shared/forseti_preflight_defaults_v0.md
stale_if:
  - Meta materially changes Ad Library access, commercial-ad coverage, filters, or result fields.
  - A Forseti Meta Ad Library recipe card or dedicated runner supersedes this first probe.
  - The Summer Fridays company/entity authority or product-family inventory changes.
```

## Load Contract

- `packet_version`: `20260726_v0`
- `mode`: `max`
- `load_rule`: **confirm-don't-trust**. Confirm every named repo path, external lake,
  branch, and source surface before making strict or actionable claims.
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
  `docs/prompts/handoffs/summer_fridays_meta_ad_library_capture_handoff_20260726_v0.md`
- `output_artifact`:
  `docs/research/summer_fridays_ci_inputs_20260726/meta_ad_library_capture_return.md`
- `raw_lake_root`: `C:\tmp\forseti-sf-meta-ads-discovery-20260726\data`
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
  target_scope: Summer Fridays Meta Ad Library capture plus one bounded return artifact
  dirty_state_checked: yes
  blocked_if_missing: handoff, capture playbook, recon index, writable raw-lake root, or public Meta Ad Library surface
```

If the receiver cannot access the repository and the named Windows-local
workspace/lake, stop and request a source capsule or a receiver on the machine
that can. Do not substitute an alternate checkout, search-engine snippets, a
summary, or screenshots supplied without provenance.

## Goal Handoff

- **Long-term goal:** help Forseti produce unusually strong company intelligence
  by connecting what a company says, promotes, sells, and receives from customers.
- **Active objective:** preserve a decision-usable inventory of Summer Fridays
  commercial ads observable in the Meta Ad Library for the bound market/window,
  typed by product family and creative/message.
- **Fitness reference:** the later Deliver lane can answer which Summer Fridays
  product families have observable Meta/Instagram/Facebook creative air cover and
  which have no observed active creative in this capture window, without claiming
  spend, performance, targeting, or strategy.
- **Done signal:** admitted raw packets plus a return artifact enumerate or
  explicitly bound the visible result surface, deduplicate ads/creative variants,
  map identifiable products, and carry coverage ceilings and provenance locators.

## Open Decision / Fork

This is the first Forseti Meta Ad Library probe. The receiver must locate the
actual signal substrate before choosing the capture route.

- If the public surface exposes stable ad/result identifiers and enough visible
  creative detail, capture the bounded inventory and bank a recipe-card section.
- If only a partial visible result set is obtainable, return `PARTIAL` with the
  exact pagination/filter ceiling.
- If the surface is empty or errors, prove the instrument with a known-positive
  commercial advertiser or a second independent method before any empty-source
  conclusion.
- If access is authenticated/access-controlled and the receiver has no entitled
  access, stop at the gate. Do not defeat authentication.

## Drift Guard

- Summer Fridays only. Do not expand into competitor parity, portfolio strategy,
  campaign recommendations, or a reusable multi-company monitor.
- Acquisition only. Do not cross-stitch with retailer reviews, Reddit, ingredients,
  TikTok Shop, SERPs, or the Phase A acquisition seal.
- Capture what Meta visibly exposes. Do not infer spend, budget, ROAS, impressions,
  targeting, conversion, campaign objective, market priority, or executive intent.
- Use the exact absence phrase: **“No active Summer Fridays commercial creative
  was observed on the captured Meta Ad Library surface under the recorded
  market/filter/window.”** Never shorten this to “not spending.”
- A creative mentioning a product family is family-level evidence only. Do not
  infer SKU, shade, variant, or launch status unless the creative or destination
  page makes it identifiable.
- Treat Instagram/Facebook placement labels only as source-declared fields. The
  absence of a placement label is unknown, not proof the placement was unused.
- Public, targeted, human-rate capture only. No private-person dossiers, credential
  capture, exit-IP retention, auth bypass, or mass scraping.
- Preserve failures and omissions. A login wall, omitted media, broken preview,
  or capped result list is typed evidence, not a reason to fake completion.

## Inherited Context

Summer Fridays is the current dogfood company, not the permanent product scope.
Generalizing this route to other companies is future work. The existing Phase A
corpus is a separate lifecycle and is not reopened by this supplement.

No accepted Meta-specific recipe card or dedicated runner was found at the
authoring checkpoint. Therefore:

- the capture playbook owns access classification, substrate diagnosis, route
  selection, honest verdicts, and receipts;
- the recon index supplies known false-diagnosis lessons;
- the generic browser/CloakBrowser packet runners are candidate transports, not
  proof that the Ad Library is capturable;
- Meta's surface is primary evidence; the return artifact is a typed inventory,
  not a substitute for retained source packets.

## Source And Authority Ledger

Re-read these before strict claims:

1. `forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md`
   - authoring compare target SHA-256:
     `aac268200599b047c1a1a8096ed2f683197f484475761c20649a86740494d3f5`
   - role: capture method, access gate, route selection, receipt, verdict vocabulary.
2. `forseti/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md`
   - authoring compare target SHA-256:
     `22ba2475317a731fc1aeb55ce7ab8004ad39bdc82d44dfb5e0f14c4c68244d58`
   - role: empirical route and false-block context.
3. `forseti/product/spines/capture/core/source_families/README.md`
   - role: confirm whether a Meta Ads source family or newer recipe card now exists.
4. Summer Fridays company identity and product-family authority:
   - locate the current accepted company/portfolio source from
     `docs/research/summer_fridays_understanding_dogfood_20260725_p10/`;
   - re-read the source itself before normalizing ads;
   - do not rely on this handoff's prose as the product inventory.

External source:

- Meta Ad Library commercial-ad surface, with advertiser identity, country,
  category/filter, and capture time recorded in every run.

## Exact Next Authorized Action

1. Bind a clean receiver worktree and confirm all named paths.
2. Run the lake-first preflight. The new raw-lake root should be empty; if it is
   not, inventory it and do not overwrite packets.
3. Confirm the official Summer Fridays entity/page identity from a company-owned
   link or other retained first-party identity evidence. Name collisions do not pass.
4. Run capture-playbook Steps 0–3 against the Meta Ad Library surface:
   access class → substrate/problem statement → cheapest matching route → packet
   and receipt.
5. Freeze the capture parameters before enumeration:
   advertiser/page identity, country/market, commercial-ad category, active/status
   filter, capture start/end timestamps, sort/default state, and pagination cap.
6. Enumerate up to **60 unique ad/library identifiers or 10 result-continuation
   actions, whichever comes first**. If the surface declares fewer, capture the
   visible exhaustion signal. If it declares more, return `PARTIAL` rather than
   implying completeness.
7. Preserve raw source evidence and extract the typed inventory below.
8. Write only the named return artifact. Do not edit the Phase A record or seal.

## Minimum Capture And Extraction Contract

For each observable ad, retain when source-visible:

- canonical advertiser/page identity and source locator;
- Meta/library ad identifier;
- active/inactive source status and source-declared first-shown/start date;
- creative body/headline, CTA, visible format/media type, and media-availability state;
- destination URL/domain and any visible landing-page label;
- source-declared placement/platform fields;
- identifiable Summer Fridays product, family, variant, or brand-only classification;
- visible offer, promotion, retailer/channel, creator/partner, affiliate, or
  collaboration language;
- capture timestamp, market/filter/window, packet ID, manifest path/hash, and
  source-record pointer.

Deduplicate:

- exact library/ad identifiers;
- repeated creative attached to multiple visible ad instances, while retaining
  the instance-to-creative relationship;
- canonical destination URLs after stripping tracking parameters;
- repeated cards caused by pagination or UI reflow.

The return artifact must include:

1. executive acquisition conclusion;
2. route verdict and recipe-card section;
3. capture-parameter receipt and enumeration ceiling;
4. advertiser-identity proof;
5. unique-ad inventory;
6. creative/message clusters;
7. product-family coverage matrix;
8. explicit “no observed active creative” rows only for families in the freshly
   read portfolio authority;
9. failure/omission ledger;
10. source packet bundle with exact locators and hashes;
11. non-claims and what Deliver may safely join later.

## Validation And Stop Conditions

Before closeout:

- fresh-read the written return artifact;
- verify every inventory row resolves to a retained packet/source record;
- recompute unique-ad, creative, and family counts from the rows;
- verify raw-lake manifests against preserved files using the current lake tools;
- run `python -B .agents/hooks/header_index.py --strict`;
- run `python -B .agents/hooks/check_prompt_output_mode.py --strict`;
- run `git diff --check`.

Report each check as pass, fail, blocked, or not run. A transport success,
screenshot, HTTP 200, or visible page without the required ad details is not
source-useful success. Stop with the nearest explicit blocker if identity,
access, packet admission, provenance, or output writing cannot be verified.
