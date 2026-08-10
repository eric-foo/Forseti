# Dieux p03 Phase A — Different-Vendor Semantic Review and Patch Return

```yaml
retrieval_header_version: 1
artifact_role: Commissioned cross-vendor semantic review-and-patch return (review candidate until Chief Architect adjudication)
scope: >
  Findings, bounded patches, spot-check ledger, validation evidence, and verdict
  for the Dieux p03 Phase A acquisition candidate under commission
  BEAUTY-DIEUX-PHASEA-COMPLETION-003.
authority_boundary: retrieval_only
current_as_of: 2026-08-06
```

## 1. Receiver binding receipt

- Reviewer vendor / model family: **Anthropic / Claude (Claude Fable 5)** — different upstream vendor from the OpenAI/Codex authoring lineage, satisfying the cross-vendor requirement.
- Worktree: `C:\tmp\forseti-dieux-phase-a-completion-handoff-20260805`
- Branch: `codex/dieux-phase-a-completion-handoff-20260805`
- HEAD: `3e0ade5f0dadb690b2209ee7b527cfdad42b3a2b` (matches commission binding)
- Initial dirty state (verified before any read): exactly three modified Commission Signal Board files plus untracked `docs/prompts/handoffs/dieux_phase_a_completion_and_seal_handoff_v0.md`, `docs/research/dieux_understanding_dogfood_20260805_p03/`, `docs/workflows/dieux_understanding_dogfood_20260805_p03/` — matches the commissioned expectation exactly.
- No-concurrent-writer result: no `.git/index.lock`; no p03 artifact changed bytes during the review except through this lane's authorized patches; footprint check after patching shows exactly three candidate files modified by this lane.
- Dirty-source note: every candidate and evidence artifact under the p03 roots is untracked commissioned work; all pinned hashes were independently recomputed (see §5) before reliance.

## 2. Findings (severity order)

### F-01 — MAJOR (patched): native-social support ref cited on seven axes its body does not state

- Artifact: `evidence_depth_ledger.json` support_refs (7 of 8 axes); upstream cause in read-only `specialists/co1_native_social_floor_composition.json`.
- Primary evidence: caption body `co1\native_social\youtube\8uZKNMnXImI_caption\raw\01_8uZKNMnXImI.captions.en.json3` (Sincerely Chany haul video). Its entire Dieux content is one Deliverance segment: "i have only tried this once or twice … i have seen the testimonials i love [Dieux's] desire and ethic … around being transparent". No hydration outcome, no irritation, no texture, no packaging, no segment fit, no repeat/switch behavior.
- Consequence: the unit was the only qualifying non-Reddit origin on those axes, so it silently carried each axis's `recurring` strength distribution (≥3 qualifying origins across ≥2 families). A support claim no native body states is invalid under the CSB rules.
- Patch: replaced the ref on six axes with transcript-verified `apparently_independent` units — `youtube:aKfppmQ5-qc` (Fortune; verified Instant Angel/Air Angel/Deliverance/Baptism content covering hydration, sensitivity, texture/finish, packaging, segment/portfolio) on A01/A02/A03/A04/A06, and `youtube:zxNrQP8V4K8` (RuthlessJEE; verified stopped-facial-use and body-diversion behavior on Instant Angel) on A07. Kept on A05 only, where the trust/hype content is genuinely body-supported.
- Owner action (read-only surface): the composition file's per-video `axis_ids` are looser than the transcripts support (the Chany video carries 7 axes; e.g. the Forever-Eye-Mask-anchored videos carry 3–7 axes with near-zero Dieux product-experience keywords). Class-level recheck recommended before any reuse of composition axis assignments outside this seal.

### F-02 — MAJOR (patched): miscoded decision-bearing row `18wuj9l` (price axis, wrong alternative brand)

- Artifact: `community_axis_coding_v4.json` row `18wuj9l`; `evidence_depth_ledger.json` A05 support and decision-bearing refs.
- Primary evidence: native body `capture_9996157cbc1837392553\raw\02_02_realchrome_visible_text.txt`. The only Dieux-displacing alternative is "I would recommend the **Avene xeracalm balm** for this step if you are acne prone"; Vanicream appears only as a cleanser and shampoo. The post contains **no Dieux price/value content** ("expensive" refers to Kiehl's; "pricey" to SEEN haircare).
- Consequence: A05 (price/value/hype/trust) rested its decision-bearing counterevidence on a row that is false for that axis, and "Vanicream" gained executed-destination credit it does not have anywhere in the corpus.
- Patch: v4 row — removed `price_value_hype_product_trust`, corrected `alternative_brand` to `Avène`; ledger A05 — support ref and decision-bearing ref re-anchored to `1f9ys6t` (verified price counterevidence: executed substitution from SkinCeuticals Triple Lipid, "$150+" avoidance, "well worth it", price-transparency trust).

### F-03 — MAJOR (patched): packaging axis coded onto a comment with no packaging content (`1gti140`)

- Artifact: `community_axis_coding_v4.json` row `1gti140`; ledger A04 refs.
- Primary evidence: native body `capture_bc9b97adacffb2515f9d\...\02_02_realchrome_visible_text.txt`. The coded Air Angel comment ("HG… third or fourth bottle… hydrating, not too heavy, plays well with spf and makeup") and every other Dieux comment in the thread contain zero packaging/dispensing content.
- Consequence: A04's decision-bearing counterevidence pointed at absent content; the recorded counterevidence ("positive accounts do not mention packaging failure") converted absence into a support claim, which the CSB rules do not permit.
- Patch: v4 row — removed `packaging_dispensing_usability`; ledger A04 — support and decision-bearing refs re-anchored to `1f9ys6t`, whose body carries genuine positive packaging counterevidence ("actually very easy to dispense and I was able to get pretty much every last drop out with one of those tube turner things"). `1j6c4zo` retains its packaging coding legitimately (verified Air Angel pump-trapping content).

### F-04 — MODERATE (patched): competitor-destination decision effects were stale inventory candidates, not observed behavior

- Artifact: `evidence_depth_ledger.json` `decision_usefulness.decision_effects.competitor_destination` (7 axes).
- Primary evidence: the strings were copied verbatim from the pre-Phase-2 `consumer_brand_axis_inventory.json` routing candidates. Row-level adjudication and native bodies show Prequel, Stratia, Embryolisse, Vanicream, CeraVe are comparison/recommendation mentions only, while verified executed destinations were omitted — Dr. Jart Ceramidin (`1l8evw5`: "I just tried Dieux and all it was, was oily … I just returned it"; "die hard dr jart girl … going back to dr. jart"), Kiehl's, Lions Pose, Alpyn (`1l8evw5`), Zerafite and Experiment (`1qs3yv1`), Aestura and Skinfix (`1hpp7we`), COSRX (Strategist editorial), plus candidate-recorded Avène, La Roche-Posay, Le Mieux, BYOMA, Dr Sam's, Farmacy.
- Consequence: destination sets read as observed switching effects while mixing routing candidates with evidence — the exact mention-vs-destination confusion the commission's question 3 targets.
- Patch: all seven fields rewritten to executed-behavior-only sets with mention-only names explicitly demoted; A04 now truthfully states no packaging-driven destination is established; A08 unchanged (already truthful).

### F-05 — MODERATE (patched): service-axis decision-bearing role inverted

- Artifact: ledger A08 `decision_bearing_support_refs`.
- Primary evidence: `1omfgsp` native body is pure service pain (delays, broken make-good promise, Sephora channel-switch intent); the axis's recorded strongest counterevidence is the official policy, not that thread.
- Patch: roles corrected — `1omfgsp` → `customer_tension`; `official_service_policy` added as `counterevidence`.

### F-06 — MODERATE (patched): official service policy locator pointed at a body without the policy

- Artifact: ledger artifact `external_official_service_policy`.
- Primary evidence: pinned `02_cloakbrowser_visible_text.txt` (4,530 bytes) contains only collapsed FAQ questions; the admitted policy answers (DHL 5–8 days, $5/free ≥ $60, returns, refund pathways) exist only in `01_cloakbrowser_rendered_dom.html` — exactly the DOM packet CO1's return credits.
- Patch: locator and sha256 repointed to the DOM file (`318433db…`).

### F-07 — MODERATE (patched): same-outlet editorial pages coded as independent origins

- Artifact: ledger `external_context` units `whowhatwear_air_angel` / `whowhatwear_best_moisturizers`.
- Primary evidence: both are whowhatwear.com pages; the candidate's own convention is outlet-level origins (`byrdie`, `the_cut`, …), but these carried split origin_ids and both claimed `independent_origin`.
- Consequence: external independent-unit/origin counts were inflated 13/13 vs the truthful 12/12.
- Patch: shared `origin_id: who_what_wear`; second unit set to `same_origin`. Floors still pass (12 ≥ 12 both metrics) — the correction changes truthfulness, not the gate.

### F-08 — MODERATE (patched): seal understates the Phase 2 decision receipt

- Artifact: `acquisition_seal.md` `serp_phase2_decision_receipt.entries: 0`.
- Primary evidence: the receipt contains 4 results (`entry_count: 4`, all `watch`, none decision-ready); Summer Fridays precedent seals record total entries.
- Patch: `entries: 4`.

### F-09 — ADVISORY (not patched; explicit CA adjudication requested): materiality reading behind the stopping rule

- The closure batches record `material_incremental_value: false` and zero `new_comparison_choices` / `new_competitor_alternatives` for every Phase 2 job, yet the P2-A05-V capture (`1l8evw5`) contains the corpus's first executed events for Dr. Jart Ceramidin, Lions Pose, Alpyn, and Kiehl's, and CO3's own Phase 2 return says the five focused threads "materially extend" the evidence. This closure survives only under a decision-effect (typed-materiality) reading: the new events instantiate already-established displacement patterns and change no competitive decision at the `bounded_observation_only` ceiling. With the destination fields now truthful (F-04), I judge that reading defensible — but it is a judgment, not a mechanical fact. If the Chief Architect instead reads a first executed switch to a previously mention-only brand as a `competitor destination` material addition, A05/A07 have no post-addition dry continuation families and closure for those axes would require a bounded continuation before sealing.

### F-10 — ADVISORY: retailer coding provenance and packaging-mention noise

- 898 of 913 Sephora `source_row_ref` locators cite the failed first-walk packet `01KZ9DQ7XC…` that CO2's return says receives no row credit; the bytes are real preserved provider responses and all 990 refs resolve with zero review-ID mismatches, so this is provenance hygiene, not evidence falsity. A minority of packaging-coded rows are idiom-only (e.g. `338912642`: "gone through an entire tube" with no packaging experience), slightly inflating the A04 axis-mention tally (105). Counts remain bounded-qualitative; class-level recode is disproportionate inside this commission and is left to the owner.

### F-11 — ADVISORY: thread-level flattening in v4

- One row per thread flattens per-comment nuance: e.g. `o28gng` carries `choice: alternative / Chuda` although the focused row-level coding correctly types Chuda as "routine_comparison_not_deliverance_switch". The focused and specialist codings remain the more precise record; v4's flattening is acceptable for its validator role but should not be read as per-comment attribution. A03's retained support ref `17yyp96` is thin (a one-line routine placement) but truthful as routine-compatibility content.

## 3. Review-question adjudication (commission §Review questions)

1. Subject anchoring — PASS. Every read body is genuinely about Dieux, a named product, or a bounded comparison.
2. Axis and role fit — FAILED as authored (F-01/02/03), corrected by patch.
3. Competitor-event attribution — FAILED as authored at the decision-effects layer (F-04), corrected; row-level coding itself separates executed from mention correctly (verified in `1qs3yv1`, `1hpp7we`, `1l8evw5`, `o28gng`).
4. Behavioral consequence — PASS. Repeat/churn/switch claims trace to source-native first-person statements and stay qualitative.
5. Counterevidence — PASS. Negatives, mixed outcomes, incentive/relationship postures, and source limits survive aggregation (Zoe's relationship-bearing account is explicitly bounded; Fortune's "doing too much for my skin" and RuthlessJEE's stopped-use are preserved).
6. Service/product separation — PASS. `1omfgsp` and Trustpilot support only `service_fulfillment_support_trust`; no efficacy/texture/product-quality credit found anywhere.
7. Meta treatment — PASS. Same-session Nike control (≈110 results, 29 IDs) validates the instrument; Dieux exact-route zero stays a bounded point-in-time observation; non-claims intact.
8. Retailer and social floors — PASS after F-07. Dedup claims (zero cross-corpus overlap; 29 pinned Instant Angel rows mapped to fresh native IDs) are recorded truthfully; TikTok Shop rows carry zero additive credit.
9. Phase ordering — PASS. Family order F1→F4 and Phase 2 `executed_at` sequence verified; specialists verified the Phase 1 terminal gate before capture.
10. TikTok Shop treatment — PASS. Routed probe supersedes the route block as route completion only; six default-Recommended five-star ID-less rows receive zero corpus credit; no exhaustion or representativeness claim.
11. Seal truthfulness — PASS after F-08. `acquisition_gate: pass` with zero pending material route jobs is mechanically true; `SEALED_READY_FOR_DELIVER`/`deliver_allowed: true` is the schema-required passing pair, and the pending cross-vendor review and CA adjudication are correctly recorded (`acceptance_status`, `independent_semantic_review`, header prose); Deliver has not started.
12. Claim ceiling — PASS. No prevalence, superiority, causation, medical-safety, market-share, or pipeline-adoption leak found; pipeline verdict stays `reject_unchanged_from_prior_dogfood`.
13. Internal coherence — FAILED as authored (F-04..F-08), corrected; all pinned hashes now reconcile (note: the decision receipt and lifecycle sealed receipt are byte-identical after newline normalization — same content, different line endings; not a defect).

## 4. Spot-check ledger (two independent source-native reads per material axis)

Every locator below was hash-verified against its ledger pin before reading. "Independent" = different unit, author set, and (where possible) family/venue from the axis's decision-bearing reference and from each other.

| # | Axis | Spot check | Locator | Independence rationale | Adjudication |
|---|---|---|---|---|---|
| 1 | A01 hydration | Oprah Daily editorial | `C:\tmp\forseti-dieux-phase-a-completion-20260805-p03\co1\phase2\oprah_instant_angel_http\raw\01_http_response_body.bin` | Editorial family, distinct origin/author vs decision-bearing Reddit `11naqw4` | Matches coding: 4-month conditional use test, affiliate-disclosed, no efficacy claim |
| 2 | A01 hydration | Reddit `129uppa` | `…dogfood-20260804\...\capture_bd476254f067e393f0bd\raw\02_02_realchrome_visible_text.txt` | Different subreddit (r/30PlusSkinCare), different author than `11naqw4` | Deliverance redness/rosacea content supports sharpens/conditional coding |
| 3 | A02 irritation | Reddit `o28gng` | `…completion-20260805-p03\co3\phase2_focused_reddit\03_o28gng\raw\02_02_realchrome_visible_text.txt` | Phase 2 capture, r/SkincareAddiction 2021 thread, disjoint authors | Breakout/refund/rechallenge and delight coexist; Chuda correctly typed as routine comparison |
| 4 | A02 irritation | Zoe Report editorial | `…co1\phase2\zoe_deliverance_http\raw\01_http_response_body.bin` | Editorial family, relationship-bearing (disclosed prelaunch supply) | Bounded exactly as coded; founder-relationship caveats preserved |
| 5 | A03 texture | Reddit `1f9ys6t` | `…co3\phase2_focused_reddit\04_1f9ys6t\raw\02_02_realchrome_visible_text.txt` | Different thread/venue (r/SkincareAddictionLux) vs decision-bearing `17yyp96` (r/AsianBeauty) | Rich texture/weight/finish content confirms multi-axis coding |
| 6 | A03 texture | Reddit `1823590` | `…dogfood-20260804\...\capture_1d37c95c523951dfe4db\raw\02_02_realchrome_visible_text.txt` | r/NYCinfluencersnark — non-skincare community, distinct population | "No clogged pores or pilling under sunscreen and makeup"; supports corroborates/subject and the re-anchored counterevidence |
| 7 | A04 packaging | Reddit `1j6c4zo` | `…dogfood-20260804\...\capture_70a3f69f9272ca1d108e\raw\02_02_realchrome_visible_text.txt` | Different thread from (former) decision-bearing `1gti140`; contradicts-polarity row | Genuine Air Angel pump-trapping content; packaging coding valid here |
| 8 | A04 packaging | Sephora review `338912642` | `…co2\lake\raw\3c7\01KZ9DQ7XC…\raw\02_reviews_non_incentivized_most_helpful_offset_000.json#Results[38]` | Retailer corpus family, provider-verified native ID | Exposed idiom-only packaging coding (F-10); hydration/breakout/no-future-purchase codes are body-true |
| 9 | A05 price | Reddit `1l8evw5` | `…co3\phase2_focused_reddit\01_1l8evw5\raw\02_02_realchrome_visible_text.txt` | Phase 2 thread, r/Sephora, disjoint from Strategist author | Confirms executed Dr. Jart return-preference, Lions Pose/Alpyn/Kiehl's displacement, value framing |
| 10 | A05 price | Strategist editorial | `C:\tmp\forseti-dieux-cross-source-baseline-dogfood-20260805\sources\nymag_cosrx_replacement\raw\02_02_realchrome_visible_text.txt` | Editorial family, distinct origin | Executed price-driven COSRX switch with intact luxury counterevidence — exactly as coded |
| 11 | A06 segment | Who What Wear Air Angel editorial | `…cross-source-baseline…\sources\who_what_wear_air_angel\raw\02_02_realchrome_visible_text.txt` | Editorial family vs decision-bearing Reddit `11naqw4` | Internal IA→Air Angel switch by skin state; supports the portfolio-ladder counterevidence |
| 12 | A06 segment | Reddit `1gti140` | `…dogfood-20260804\...\capture_bc9b97adacffb2515f9d\raw\02_02_realchrome_visible_text.txt` | Different thread/venue (r/Sephora HG thread) | Air Angel daytime combo/oily segment fit genuine; exposed the false packaging code (F-03) |
| 13 | A07 switching | Reddit `1qs3yv1` | `…co3\reddit_realchrome_capture\F3_1qs3yv1\raw\02_02_realchrome_visible_text.txt` | F3 brandless-family capture, distinct authors | Confirms executed Zerafite/Skinfix replacements and Experiment preference; both-sides comparison preserved |
| 14 | A07 switching | Reddit `1hpp7we` | `…co3\reddit_realchrome_capture\trigger_1hpp7we\raw\02_02_realchrome_visible_text.txt` | Trigger-family capture, different venue-thread population | Confirms executed Aestura replacement and Skinfix switch; Embryolisse correctly mention-only |
| 15 | A08 service | Trustpilot window | `…co3\trustpilot\realchrome\raw\02_02_realchrome_visible_text.txt` | External platform family vs decision-bearing Reddit `1omfgsp` | All nine reviews match CO3's typed table verbatim, incl. Baptism-attribution caution; service-only boundary held |
| 16 | A08 service | Official FAQ policy (DOM) | `…co1\official_us_faq_service_and_retailer_dom_admitted\raw\01_cloakbrowser_rendered_dom.html` | Owned corporate source, different family and origin | Policy answers present in DOM only — exposed and fixed the locator defect (F-06) |

Decision-bearing references read in full (all hash-verified): `11naqw4` (4 axes), `17yyp96`, `1gti140`, `18wuj9l`, `1omfgsp`; plus post-patch anchors `1823590` and `1f9ys6t`, and native-social transcripts `8uZKNMnXImI`, `aKfppmQ5-qc`, `zxNrQP8V4K8`.

## 5. Files changed and diff account

Patched (all inside the commissioned six-file authority; every other read path untouched):

1. `docs/research/dieux_understanding_dogfood_20260805_p03/coordinated/community_axis_coding_v4.json`
   - Row `18wuj9l`: removed `price_value_hype_product_trust` from `axis_ids`; `alternative_brand` `Vanicream` → `Avène`.
   - Row `1gti140`: removed `packaging_dispensing_usability` from `axis_ids`.
   - New normalized SHA-256: `e812ba4a46f790c2ac147fc5660ac36f633bccadfe43383f4042ce5f5539e805`.
2. `docs/research/dieux_understanding_dogfood_20260805_p03/coordinated/evidence_depth_ledger.json`
   - `community_axis_coding` artifact pin updated to the new v4 hash; `external_official_service_policy` locator/sha repointed to the DOM body.
   - Who What Wear units: shared `origin_id`, second unit `same_origin`.
   - Support refs: haul-video unit replaced by `aKfppmQ5-qc` on A01/A02/A03/A04/A06 and `zxNrQP8V4K8` on A07 (kept on A05); `1gti140` (A04) and `18wuj9l` (A05) replaced by the verified `1f9ys6t` ref.
   - Decision-bearing refs re-anchored: A03→`1823590`, A04→`1f9ys6t`, A05→`1f9ys6t`; A08 roles corrected with `official_service_policy` counterevidence ref added.
   - Seven `competitor_destination` decision-effect strings rewritten to observed-behavior-only sets.
   - New normalized SHA-256: `c615276abeaf68542615810ad201b7e1d61bc059bd587f6cbfd4fd73a3d80a8a`.
3. `docs/workflows/dieux_understanding_dogfood_20260805_p03/coordinated/acquisition_seal.md`
   - `serp_phase2_decision_receipt.entries: 0` → `4`; both `evidence_depth_ledger` sha pins (top-level and `resume_contract`) updated to the new ledger hash.

Plus this review report (the commissioned additional allowed output). JSON edits were byte-exact round-trips (`json.dumps(indent=2, ensure_ascii=False)` + CRLF), so diffs are limited to the listed keys. Post-patch footprint check confirmed exactly these three candidate files changed during the lane.

## 6. Validation evidence

Run after all patches, from the worktree root:

- `python forseti-harness\runners\run_phase_acquisition_seal_validation.py --seal docs\workflows\dieux_understanding_dogfood_20260805_p03\coordinated\acquisition_seal.md --repo-root .`
  - Exit code: **0**. Output: `{"findings": [], "seal_schema_version": "phase_acquisition_seal_v3", "status": "PASS", "validator": "phase_acquisition_seal_v3"}`
  - (Baseline pre-patch run also passed with zero findings; the defects found here are semantic, below the mechanical gate's floor.)
- `git diff --check`
  - Exit code: **0**; no whitespace errors. (Pre-existing LF→CRLF conversion warnings on the three already-modified Commission Signal Board files; those files were not touched by this lane.)
- `git status --porcelain` shape unchanged: same three pre-existing modified CSB files; p03 trees remain untracked commissioned work.

## 7. Verdict

**PASS_WITH_PATCHES**

The candidate's route accounting, phase ordering, service/product separation, Meta and TikTok bounded treatments, claim ceilings, and floor accounting are truthful. The patched defects were concentrated in the semantic bindings layer — support/decision references and destination decision-effects — where authored content overstated what the native bodies state. With the patches applied the six-artifact set is internally coherent, source-native-backed at every decision-bearing anchor, and passes required validation.

## 8. Residual risks and claim ceilings

- **Materiality reading (F-09)**: closure of A05/A07 rests on the decision-effect reading of the stopping rule; the CA should explicitly ratify or reject it. If rejected, a bounded continuation for those two axes is the corrective, not a doctrine change.
- **Composition axis assignments (F-11/F-01)**: the read-only native-social composition over-assigns axes per video; reuse outside this seal should re-derive axes from transcripts.
- **Retailer coding noise (F-10)**: axis-mention tallies carry minor idiom-driven inflation and cite the no-credit walk packet for provenance; acceptable at `bounded_observation_only`, not for any incidence-bearing claim.
- Claim ceilings unchanged and reaffirmed: qualitative existence, conditions, consequences, destinations, and counterevidence only; **no** prevalence, superiority, causation, medical-safety, market-share, representativeness, VPN-causality, route-performance, or pipeline-adoption claim. The pipeline-adoption verdict remains `reject_unchanged_from_prior_dogfood`. This return is a review candidate, not acceptance; formal acceptance authority remains with the Chief Architect under the overlay review doctrine.

## 9. Escalation and confirmations

- `NEEDS_ARCHITECTURE_PASS: no` — every defect was patch-level within the named candidate set; no design-level flaw in the seal schema, evidence model, or workflow was exposed.
- `deliver_started: false` — Dieux Deliver was not started, drafted, or prepared.
- Lifecycle confirmations: **no** commit, push, pull request, merge, rebase, stash, reset, clean, branch change, worktree deletion, or repository hygiene was performed. No read-only path was modified. No new research or network capture was performed.

## 10. Delegated review return courier

```text
DELEGATED_ARTIFACT_REVIEW_RETURN_FOR_HOME_MODEL

Here is the delegated cross-vendor semantic review result for
BEAUTY-DIEUX-PHASEA-COMPLETION-003 / DIEUX-UNDERSTANDING-20260805-003.
Adjudicate it under the delegated-review-patch return contract.

- Commission target: six Dieux p03 Phase A decision artifacts (patch scope)
  plus this report path.
- Findings: F-01..F-08 patched (three major, five moderate); F-09..F-11
  advisory, unpatched. Full evidence citations in §2 and §4 above.
- Patches: exactly three candidate files changed; diff account in §5;
  hash chain re-pinned (v4 -> ledger -> seal).
- Validation: seal validator PASS exit 0 post-patch; git diff --check exit 0.
- Reviewer verdict: PASS_WITH_PATCHES (candidate; not acceptance).
- Residual risk: F-09 materiality reading needs explicit CA ratification;
  composition axis assignments (read-only) flagged class-level.
- Boundaries: no prevalence/causation/readiness claims; deliver_started: false;
  no lifecycle actions taken.

These findings and patches are decision input for the Chief Architect, not
accepted truth; the CA may keep, modify, or reject any patch.
```

Review-use boundary: everything in this report is decision input for the commissioning Chief Architect. Nothing here is validation of readiness, acceptance of the seal, or authorization to start Dieux Deliver.
