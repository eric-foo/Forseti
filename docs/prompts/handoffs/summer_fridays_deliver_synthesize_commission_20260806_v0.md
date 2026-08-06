# Summer Fridays Deliver Synthesize Commission — 2026-08-06 v0

```yaml
retrieval_header_version: 1
artifact_role: Cold cross-lane Deliver-phase Synthesize commission
scope: >
  Commission the first Deliver-phase Synthesize turn of the Summer Fridays
  Forseti Intelligence Cycle: a challenger competitive decision memorandum
  authored in fresh context under the Deliver decision-memorandum method
  (all thirteen rules), from the twice-corrected sealed Understanding
  substrate plus the landed typed supplements. Produces the memorandum,
  its inspectable evidence appendix, and the first machine-readable output
  set with the bootstrap schema. Does not include the cold adversarial
  read, the defender derivative, or any outreach — those are separate
  commissions.
use_when:
  - Executing the Summer Fridays challenger decision memorandum.
  - Checking what the first Deliver run was commissioned to produce.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/commission_signal_board/workflows/deliver_decision_memorandum_method_v0.md
  - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
  - docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/p11r7_choice_outcome_rederivation_disposition_v0.md
stale_if:
  - The Deliver decision-memorandum method is materially amended before this run starts.
  - The p11r7 seal is re-cut again before this run starts.
```

**Goal:** the first real product artifact of the cycle — a decision
memorandum a premium beauty challenger's product lead could use to choose a
wedge against Summer Fridays, or to walk away, with every claim resolving to
corrected sealed evidence.
**Done looks like:** a concise memorandum plus inspectable appendix in the
named output directory; every load-bearing claim carries its resolution
labels and resolves to a cited locator; the defended tier obeys the cap; the
four machine-readable structures exist with `deliver_output_schema_v1.json`
filed beside them; the run ends at draft-complete — explicitly NOT
ready-to-show (the cold read is a separate later commission).

## Load Contract

- `packet_version`: `20260806_v0`
- `mode`: max (cold cross-lane commission)
- `load_rule`: **confirm-don't-trust**. Verify the gate artifacts below by
  fresh read and hash before any synthesis claim.
- output_mode: `file-write`
- `edit_permission`: `docs-write` for the named output directory plus the
  one-line `open_next` schema pointer the method's Rule 11 requires adding
  to the method doc at closeout. Everything else read-only.
- `preflight_defaults`: `docs/prompts/templates/shared/forseti_preflight_defaults_v0.md`
  v0 — constants bound; deltas stated inline.
- `input_prompt_source`:
  `docs/prompts/handoffs/summer_fridays_deliver_synthesize_commission_20260806_v0.md`
- `output_directory`:
  `docs/research/summer_fridays_deliver_20260806_d01/`
  containing at minimum: `challenger_decision_memorandum_v0.md`,
  `evidence_appendix_v0.md`, `target_screen.json`, `axis_map.json`,
  `destination_map.json`, `claims_join.json`,
  `deliver_output_schema_v1.json`.
- `workspace`: clean receiver-owned Forseti worktree off current `main`;
  fresh context — do not run inside another active Summer Fridays lane.
- `minimum_repository_checkpoint`: `6ef742f7` (PR #1437 merge) must be an
  ancestor of the receiver's clean `HEAD`.
- `repo_map_decision`: not needed; exact method, gate, and evidence paths
  are bound.

## Method Binding (source-gated)

REFERENCE-LOAD the following method instructions. Do not APPLY them yet;
use them only to prepare a neutral source-reading lens:

1. `forseti/product/spines/commission_signal_board/workflows/deliver_decision_memorandum_method_v0.md`
   — the full method: entry gate, supplement chain, run sequence, and all
   thirteen rules. This commission binds every rule; none is optional.
2. The playbook's Turn B — Synthesize section
   (`forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md`).

Then SOURCE-LOAD the gate and evidence pack below, declare
`SOURCE_CONTEXT_READY` (or `SOURCE_CONTEXT_INCOMPLETE` with the exact gap),
and only then APPLY the method.

## Gate Verification (blocking, in order)

1. Run `python -B forseti-harness/runners/run_phase_acquisition_seal_validation.py
   --seal docs/workflows/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/acquisition_seal.md
   --repo-root .` — must be `PASS` with zero findings.
2. Fresh-read the semantic-review disposition
   (`.../coordinated/p11r7_choice_outcome_rederivation_disposition_v0.md`)
   including its confirming-re-check adjudication section; cite it in the
   memorandum's evidence-world note. A missing or stale disposition is a
   blocked gate.
3. Verify each consumed supplement per the method's Supplement Chain:
   - `docs/research/summer_fridays_ci_inputs_20260805/` (Trends capture) via
     the hashes in
     `docs/prompts/handoffs/summer_fridays_deliver_search_interest_input_handoff_20260806_v0.md`;
   - `docs/research/summer_fridays_ci_inputs_20260806/` (addendum: category
     verdict, Shopping check) — fresh-read its §1 and non-claims;
   - `docs/research/summer_fridays_ci_inputs_20260806_verification/` (three
     verification instruments) — consume if landed; if not landed at start,
     proceed without it, mark every claim it would have strengthened as
     `pending_verification_supplement`, and say so in the limitations.

## Declared Challenger Profile (Rule 5)

Declare after the target screen selects the anchor product; the profile
category follows the anchor. Fixed attributes for this proxy run:
premium tier; no incumbent product in the anchor's category; substantiation
capability at probe level (can commission tests, has not run them);
prestige-retail access aspirational, not current; US market frame
(owner-confirmed default); price-fight averse. Tag every recommendation
with the attributes it depends on, per the method.

## Run Sequence Deltas (the method owns the sequence; these are this run's specifics)

- **Target screen (Rule 1):** candidates are Lip Butter Balm, Sheer Skin
  Tint, Jet Lag Mask. Prize axis consumes review mass (corrected retailer
  splits), search-interest level and direction (20260805 capture), the
  category-vs-brand verdict (20260806 addendum: categories rising, brand
  declining — a growing prize with a weakening incumbent), and the Meta
  ad-library posture (`docs/research/summer_fridays_ci_inputs_20260726/meta_ad_library_capture_return.md`:
  heavy lip rotation, DTC-only destinations). Emit `target_screen.json`
  with the scoring and the decision.
- **Claims register (Rule 2):** promise side from captured PDPs, the 12
  owned posts, and the Meta ad creative; complaint side from the corrected
  coding. Type every gap; "overhyped" is decomposed, never used as a wedge.
- **Era-slicing analysis:** using `comment_created_utc` on the corrected
  outcome rows and native retailer review dates, slice the anchor product's
  complaint and delight classes by era. If the verification supplement
  landed dated change events, anchor the slices to them; otherwise slice
  by year and label the anchors as calendar-only.
- **Slice recomputation (Rule 13):** re-derive axis support at the
  anchor-product grain; degrade any slice below the sealed floor to a
  bounded-signal claim.
- **Drafting (Rules 3–10, 12):** memorandum sections per the method's
  artifact shape; the defended tier obeys Rule 12 exactly (contested-first,
  cap at two, do-not-attack list ≡ defended tier, empty allowed — with the
  corrected counterweight at net −78 an empty or one-item defended tier is
  a legitimate outcome, not a failure); the voice-evidence claim ladder and
  resolution labels apply to every load-bearing claim; population-rate
  language is banned and each rate-worthy claim names its upgrade
  instrument.
- **Rule 11 bootstrap:** the four JSON structures carry
  `schema_version: 1`; file `deliver_output_schema_v1.json` beside them
  (field names and meanings); add the one-line pointer to the method doc's
  `open_next` in the same work unit.

## Known Evidence Boundaries (carry into the memorandum's limitations)

- Community counterweight after two correction rounds: positive 64 vs
  negative 142 (net −78); reaction and wear carry
  `counterevidence_absent_verified`; formula's counterweight is one row.
- Retailer positive splits stand on their own corpus (referent spot check
  0/25 defects); axis-binding noise ~2/25 in sample — any retailer split
  carrying decision weight gets its rows spot-checked at drafting time (the
  disposition note's trigger).
- All voice evidence is captured-sample qualitative; the Trends evidence is
  relative attention only; the addendum's Shopping check is inconclusive
  below threshold and is cited only as a bound.
- This is a proxy-buyer product-learning run under
  `.agents/workflow-overlay/product-proof.md`: no willingness-to-pay,
  buyer-validation, or readiness claim anywhere in the artifact.

## Stop Conditions

Stop with the nearest explicit blocker if: the seal validator does not PASS;
the disposition is missing; a consumed supplement fails its hash; the
target screen cannot separate the candidates without inventing evidence; or
any method rule would have to be violated to complete a section. Do not
lower a claim standard to finish a draft. The run ends at draft-complete
plus the return summary (outputs written, gate receipts, limitations,
unresolved items); it does not commission the cold read, produce a defender
variant, claim readiness, or start outreach.
