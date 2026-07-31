# Summer Fridays Understanding p11 — Targeted SERP Phase 2 Return

```yaml
retrieval_header_version: 1
artifact_role: Targeted SERP Phase 2 terminal return
scope: Records specialist-derived Phase 2 acquisition jobs, raw packet provenance, decision-lifecycle settlement, and terminal evidence ceilings for the p11 run.
use_when:
  - Auditing p11 Phase 2 consumption, failures, or acquisition sealing.
authority_boundary: retrieval_only
```

## Terminal State

```yaml
status: BLOCKED_TERMINAL
subject: Summer Fridays
subject_entity_key: summer fridays|company|brand
bound_question_preserved: true
terminal_returns_consumed: 3
targeted_queries_planned: 8
targeted_queries_completed_with_admitted_content: 6
targeted_queries_failed_content_admission: 2
targeted_queries_access_blocked: 0
targeted_queries_unrun: 0
capture_attempts: 9
raw_failure_packets_preserved: 3
j5_delta_rows: 0
automatic_validations_licensed: 0
lifecycle_claims_required: 0
deliver_started: false
```

The bound question remains: “What does current public evidence show about Summer Fridays as a company and brand system—its identity, ownership, leadership, proposition, offering architecture, markets and channels, chronology and material events, customer and community response, and bounded outside-in context—and which observable tensions warrant later Problem Framing?” No topic or evidence-family requirement was narrowed to obtain a seal.

## Consumed Terminal Returns

| Actor | Terminal artifact | SHA256 | Consumed state |
|---|---|---|---|
| CO1 | `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co1_company_core_identity.md` | `11f501bfefd51d80b996b31eabd18fcf17057ee550326ef032e0d50e5e2479bb` | `BLOCKED_TERMINAL`; 8 of 11 jobs completed, with legal ownership and the two owned-source doors terminally blocked. |
| CO2 | `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co2_retail_portfolio.md` | `078e4d96079b0ffe215f91d09a579527de9a9e63b5896832c4ded654b9991aec` | `BLOCKED_TERMINAL`; all seven planned jobs were already complete and revalidated, with typed retailer-route ceilings preserved. |
| CO3 | `docs/research/summer_fridays_understanding_dogfood_20260731_p11/coordinated/specialists/co3_customer_community_depth.md` | `0523946892ee35b516a59d462e48cf37f9bf604ed3cfa2258a94cce42bc63131` | `BLOCKED_TERMINAL`; 7 exhausted Reddit inputs plus 10 native jobs were settled, with 4 native jobs complete and 6 blocked. |

CO0 fresh-read the locators and typed blockers in each return. These specialist artifacts are provenance maps, not substitutes for the preserved source packets.

## Target Query Ledger

| Query ID | Targeted query | Terminal disposition | Bounded observation |
|---|---|---|---|
| `p2_q01_ownership` | `"Summer Fridays" ownership investor acquisition Marianna Hewitt Lauren Ireland` | Completed; packet `01KYWPJF9JT79CAG8TYH0W82WE`; manifest SHA256 `e95452a8068acf68ec9aa23227eedfe0e0492b348930868c81dd0ec0977d22fe`. | TSG Consumer’s July 25, 2024 result supports an investment/growth-partnership event and continuing founder involvement. It does not independently prove current legal control or executive titles. |
| `p2_q02_spacenk_us` | `site:spacenk.com/us "Summer Fridays" USD` | Completed; packet `01KYWPPXB91H5J7MXWW79B33R3`; manifest SHA256 `840907547c198fc0816482b842ad22224a3350e388c3943f5ac85d380ef4afa2`. | `/us/` result locators still rendered GBP snippets, so the US-market contradiction remains unresolved. |
| `p2_q03_shadedrops_succession` | `"Summer Fridays" "ShadeDrops" SPF 30 discontinued SPF 50 reformulated` | Completed; packet `01KYWPVQXYYK4MWJRQBKD54XCZ`; manifest SHA256 `149c458a351df265226a8eb698c9e7829e628e746cd0003e4a37b69ac480f618`. | An official-brand result title supports an upgraded ShadeDrops SPF 50 succession. Detailed ingredient statements in SERP synthesis are not promoted as primary proof. |
| `p2_q04_cloud_dew_reformulation` | `"Summer Fridays" "Cloud Dew" reformulated sticky discontinued` | Completed; packet `01KYWQ0D4C17F4Y08S48RRAK34`; manifest SHA256 `9c916465c5bd7fb2b2bf566ad45285932150c7299204e3d55662a73481bb1365`. | A retailer result snippet supports that Cloud Dew was reformulated; one-author replacement-performance language remains non-prevalence evidence. |
| `p2_q05_lip_balm_stability` | `"Summer Fridays" "Lip Butter Balm" watery separated` | Completed; packet `01KYWQ50P6E2RZ555KR1MJC002`; manifest SHA256 `edda74b1fbc70bcde4c78c22148947e3c336279764e6a3bb7c0af2e3d349308d`. | Reddit and Sephora result snippets corroborate a thin/watery or leaking question surface, not cause or prevalence. SERP-synthesized causes and fixes are excluded. |
| `p2_q06_jet_lag_statement` | `site:summerfridays.com/pages/jet-lag-mask-statement irritation redness manufacturing` | Failed content admission twice; packets `01KYWQ9V7W796K9QZ3739FCX8W` and `01KYWQES2HA6W3J073SHDPW0RN`; manifest SHA256s `63341bf70bd0a302cb4ccd49195430430a6f74de6fa4088a1e97f801981a8b7c` and `bbb24ff2ba087f0bec19f93aec2e2fb3188d8a1ecc483e75ee98dfc1213bd08b`. | Both raw surfaces showed the official statement result, including community feedback about temporary redness and irritation, but each extracted only 1 typed row / 500 visible characters and failed the 3-row contract floor. Browser metadata recorded `access_blocked=false`. |
| `p2_q07_sustainability_bht` | `site:summerfridays.com/pages/sustainability "Summer Fridays" vegan cruelty-free BHT` | Failed content admission; packet `01KYWQKTYX9PBV1DSCACMT03QX`; manifest SHA256 `89508eefe896242d00f876edc4becf21a30e3477cc13f5c5a44e46d1ea018208`. | The raw surface explicitly showed no results for this exact query, but 0 typed rows / 735 visible characters failed the contract floor. This is not evidence that the underlying sustainability claims are absent. |
| `p2_q08_lip_balm_packaging` | `"Summer Fridays" "Lip Butter Balm" "metal tube" fragrance applicator` | Completed; packet `01KYWQSCR4F06XP90HMVQFGYAQ`; manifest SHA256 `1768e1ef36e3494032b9744d305c77b4d5eb1503aa2d29acd7d99647ecbaf9d7`. | TikTok and retailer snippets support a metal-tube/applicator issue surface, not consensus or prevalence. |

Phase 1 already captured exact standing prices for the selected products—Summer Fridays Lip Butter Balm 15 g at USD 24, e.l.f. Glow Reviver Melting Lip Balm 0.52 oz at USD 9, and Rhode Peptide Lip Treatment 10 ml at USD 20—and CO3 did not promote another competitor. Therefore Phase 2 correctly emitted no J5 delta.

## Route And Recovery Adjudication

- The first resume queue claimed `p2_q01_ownership`, but capture was rejected locally before network because the cadence call omitted the required series ID. That preflight defect wrote no source packet and is not counted as a query or network failure.
- All source attempts then used the complete queue with the required cadence metadata. Six queries admitted content.
- The first `p2_q06_jet_lag_statement` caller mislabeled exit `4` as `blocked` and wrote a cooldown state. Fresh inspection overruled that derived label: the packet metadata says `access_blocked=false`, while content admission failed below the row floor. The queue-state label is preserved as interrupted-run provenance, not trusted as the terminal cause.
- One ordinary recovery was allowed for `p2_q06_jet_lag_statement`; it reproduced the same non-access content anomaly and was correctly reported `failed`. No third attempt ran.
- `p2_q07_sustainability_bht` preserved an explicit zero-result raw surface and failed content admission. An identical retry would not add discriminating evidence, so none ran.
- `p2_q08_lip_balm_packaging` was then run as the sole unfinished tail job and completed. No Phase 2 job remains pending or unrun.

## Decision Lifecycle

The settlement records two exact-product candidates. e.l.f. has independent SERP and creator-transcript surfaces; Rhode has two SERP surface classes. Neither has a contract-eligible first-hand complaint author, so both correctly remain `watch_for_new_source`, `weak`, and not decision-ready. No `validate_once` licence, claim, price response, or value recommendation was created.

```yaml
settlement_path: C:\tmp\forseti-summer-fridays-understanding-p11-20260731\serp_phase2\settlement_resume.json
store_root: C:\tmp\forseti-summer-fridays-understanding-p11-20260731\serp_phase2_store
claim_ids: []
prior_receipt_sha256s: []
settlement_sha256: bf51a2b4af26605c0f34a9f992d3a12cc156bd9bf8b2f47d71e24d5de8bed754
decision_receipt_sha256: 3e814232972ecedec7c563f79c78bfca70f9618fae5b5a6c17446345f1dc95bf
contract_validation: pass
lifecycle_seal_validation: pass
```

The interrupted run’s empty lifecycle remains attributable, but not authoritative for this completion check: settlement SHA256 `17469973d13d141742d2cc8acc41e481893c11f3acc00774848dc30dec63eb61`, receipt SHA256 `f58e6a360ee2339549cd8f02726b982aba8ffe18d8f6d48299f6af33954ad7b2`, and provenance SHA256 `35677421a4dd2d0385006deb1bebedb29951215cfb4a468ad26f3d85a4865536`.

## Material Blocks And Ceilings

- Legal ownership/current control and executive-title currency remain unresolved.
- The two owned-source doors—the Jet Lag statement and sustainability page—remain uncaptured as admitted first-party bodies.
- Space NK US-market pinning, four exact Amazon PDP identities, Reddit-native community evidence, five TikTok exact-video items, and one Instagram item remain terminally incomplete on their recorded routes.
- The two competitor entries are watch-only candidates. Their presence does not authorize a downstream finding, competitive response, or Deliver work.

## Cost Unit

```yaml
unit: targeted_serp_phase2_resume
actor: CO0
capture_window_started_at: 2026-07-31T18:21:30Z
capture_window_ended_at: 2026-07-31T18:43:10Z
active_segments:
  - fresh-read three final specialist terminals and derive eight decision-material queries
  - execute six admitted captures and preserve three raw failure packets
  - adjudicate one incorrect queue-state cause and one bounded recovery
  - seal two watch-only candidates through the decision lifecycle
waiting_segments:
  - enforced Google cadence intervals between source attempts
blocked_segments:
  - two Jet Lag content-admission failures
  - one sustainability exact-query content-admission failure
scripted_steps:
  - queue validation, capture, packet validation, decision contract, and lifecycle seal
judgment_steps:
  - query licensing, retry adjudication, cause correction, claim ceilings, and no-J5-delta decision
capture_attempts: 9
content_admitted_captures: 6
raw_failure_packets: 3
local_preflight_failures_before_network: 1
material_job_failures: 2
downstream_waits_caused:
  - acquisition seal must preserve terminal gaps rather than claim Phase A success
```
