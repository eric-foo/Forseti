# Data Capture Source-Access Boundary Decision v0

```yaml
retrieval_header_version: 1
artifact_role: Product artifact
scope: Records the owner-decided loosening of the Data Capture source-access posture under Obligation 2 (Boundary Compliance) of the obligation contract, to a discoverable-or-entitled + disclosable standard that permits aggressive anti-blocking techniques and materiality-gated provenance cleanup.
use_when:
  - Evaluating whether a source-access / fetch method is in-bounds for Forseti Data Capture.
  - Planning source-access tooling or method selection.
  - Checking the current interpretation of Obligation 2 (Boundary Compliance).
  - Checking when authenticated, paywalled, cached, mirrored, or convenience access is in-bounds.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/contracts/obligation_contracts/core_spine_v0_data_capture_spine_obligation_contract_v0.md
  - forseti/product/spines/capture/core/operating_model/data_capture_spine_pressure_test_commissioning_plan_v0.md
  - docs/decisions/turn_08_product_thesis_v0.md
stale_if:
  - A later owner decision amends, rejects, or supersedes this source-access posture.
  - The obligation contract's Obligation 2 is materially revised or superseded.
  - Forseti's product thesis changes the trust/provenance posture this decision depends on.
```

## Status And Decision

Status: `ACCEPTED_SOURCE_ACCESS_BOUNDARY_DECISION_V0`, amended 2026-05-30,
2026-07-03, and 2026-09-04.

Primary decision: `LOOSEN_SOURCE_ACCESS_TO_DISCOVERABLE_OR_ENTITLED_DISCLOSABLE`.

Owner decision recorded 2026-05-28: loosen Data Capture source access to
permit disclosable aggressive anti-blocking techniques. The 2026-05-30 owner
amendment below supersedes the earlier narrower gated-access line.

This decision is the controlling interpretation of Obligation 2 (Boundary Compliance) for source-access methods. The obligation contract now cross-references this decision as the controlling boundary basis. Where this decision and the contract's Obligation 2 prose appear to differ, this decision controls for source-access method selection until amended or superseded.

Owner amendment recorded 2026-05-30:

```text
Owner decision: maximize source access and avoid over-restraining capture.

For Data Capture discovery, if a source can be found through non-exploit web,
search, archive, API, browser, or similar source paths, treat it as non-private
unless a hard-stop indicator is visible. Free or account-created access is
okay. Entitled paid, client, or consenting-coworker access is allowed. If access
visibly spills into cross-account, private, or admin material, do not use that
spillover once noticed. Fast convenience paths may be used for discovery; if
Judgment later relies on the material, it must be reacquired or verified through
a normal disclosable or entitlement-clean path before final client-facing or
durable evidence use.

The hard stops are explicitly illegal or too morally compromising methods:
stolen credentials or cookies, nonconsensual sessions, security exploits,
malware, credential stuffing, no-entitlement gate bypass, using obvious
cross-account/private/admin spillover once noticed, private or confidential
account areas without consent, or any method Forseti would refuse to disclose
internally.
```

## The Standard

A source-access method is **in-bounds** for Forseti Data Capture if it acquires **discoverable or legitimately entitled source material** and Forseti would **fully disclose how it was obtained**. Forseti's accepted posture is intentionally permissive: the risk of over-restraining capture is higher than the risk of using broad disclosable discovery paths.

Operationally, a method is in-bounds when **all** hold:

1. The material is **discoverable through non-exploit source paths**, visible through **free / account-created access**, or visible through **entitled paid, client, or consenting-coworker access**.
2. Obvious cross-account, private, or admin spillover is not used once noticed.
3. Forseti would **disclose exactly how the data was obtained** if asked — no method Forseti would need to conceal.
4. The method avoids the hard stops below.

**This permits:** scraping of public or discoverable pages; free or account-created login access; entitled paid, client, or consenting-coworker access; an owner's existing entitled/logged-in access to private or login-gated communities; JS-rendering headless browsers; rate-limited or aggressive fetching; official or sanctioned APIs; archive/cache/mirror access; logged-in capture or browser automation; convenience shortcuts for discovery; **and anti-blocking techniques — anti-detect / "cloaked" browsers, user-agent and fingerprint configuration, residential or rotating proxies, and CAPTCHA / JS-challenge handling — used to reach source material inside this boundary.**

**This still excludes (hard line, not risk-tolerance):** stolen credentials or cookies; nonconsensual sessions; security exploits; malware; credential stuffing; no-entitlement gate bypass; using obvious cross-account/private/admin spillover once noticed; accessing private messages, non-entitled private groups, confidential docs, or personal account areas without consent; and any method Forseti would refuse to disclose internally. These are out because they are explicitly illegal, internally non-disclosable, or too morally compromising for Forseti's trust story.

**Owner-accepted risk posture:** the permitted anti-blocking techniques carry real Terms-of-Service, reputational, and (for actively-enforcing sources such as Reddit) litigation risk. The owner accepts this risk as a deliberate, disclosable posture. This is not a claim of legal sufficiency; obtain real legal counsel before commercializing a scraping-based capability.

## 2026-07-03 Challenge-Close Clarification

For public or discoverable source surfaces, an owner-authorized click on the
site's own X/Close control for a visible challenge modal is in-bounds disclosable
challenge handling when it is used only to reach source material inside this
boundary. It is not no-entitlement bypass and it is not, by itself, a source
success claim. Any source-specific admission path that relies on this intervention
must preserve the intervention receipt and separately verify post-close
source-owned content or response yield.

This clarification does not authorize dragging or solving CAPTCHA/slider puzzles,
credential misuse, nonconsensual session use, private/admin spillover, or hiding
the method. If the challenge remains visible after the close attempt, preserve it
as a source-access limitation rather than treating it as captured evidence.

## 2026-09-04 Entitled Community Access Clarification

Private Facebook groups, Discord servers, and other login-gated communities are
in-bounds when the owner can already see the material through an existing,
legitimately entitled logged-in session. Existing membership is entitlement; it
must not be mislabeled as private spillover merely because the venue is not
public.

This clarification does not authorize obtaining new credentials, creating or
borrowing another identity, joining a community, evading a technical control,
or exceeding the permissions of the session actually supplied. Capture must
preserve the visibility class, entitlement/session provenance without secrets,
actual access scope, and any community privacy, quotation, attribution,
retention, or redistribution constraint material to downstream use. A private
community remains private evidence; access does not convert it into a public
source or waive its rules.

## Discovery, Materiality, And Provenance

Fast discovery and evidence-grade provenance are separate.

Discovery / harvest output may be broad, fast, and convenience-oriented. It may enumerate, route, inspect, and preserve candidate source material without immediately proving final evidence-grade provenance.

Discovery output becomes **material** only when Judgment relies on it: citing it, changing confidence, changing Action Ceiling or Decision Strength, using it in a decision claim, or including it in a client-facing or durable corpus output. Mere capture, storage, search-result presence, routing inspection, or queueing is not material use.

When discovery output becomes material, Forseti must reacquire or verify it through a normal disclosable path or an entitlement-clean path before final client-facing or durable evidence use. If clean reacquisition or verification is not possible, the limitation must travel visibly and downstream Judgment decides whether the material can be used, discounted, or excluded.

## Free, Account-Created, And Entitled Surfaces

Free login or account-created access is allowed. Paid, client, or consenting-coworker access is allowed. If we do not know access is spilling into cross-account, private, or admin material, we proceed. Once obvious spillover is noticed, that spillover is not used.

In-bounds examples:

- Anyone can create a free account and view the material.
- Forseti, the client, or a consenting coworker/collaborator can legitimately log in and view the material.
- The owner already belongs to a private Facebook group, Discord server, or
  other login-gated community and supplies that entitled session within its
  actual permissions and community constraints.
- A headless browser, automated Chrome session, API, export, cache, or faster endpoint reaches the material for discovery.
- A cached or mirrored copy helps discover the material, and material use is later verified through the normal or entitled path.

Out-of-bounds examples:

- Someone's cookie, session, credential, account, or device is used without consent.
- A new credential or identity is obtained, or a community is joined, for the
  collection without separate authority.
- A no-entitlement gate is deliberately bypassed.
- Obvious cross-account, private, or admin spillover appears; that spillover is not used once noticed.

## Why Discoverable-Or-Entitled + Disclosable Is The Line

The bar is now three things: the material is discoverable, free/account-created, or entitled; the method is disclosable; and hard stops are avoided. Disclosability keeps the trust story intact — Forseti can tell a buyer exactly how every source was obtained — the opposite of hiding. The discoverable-or-entitled rule avoids treating every weak gate, cache, bot block, or account surface as a stop condition.

The hard line is not "auth/paywall/private" as a blanket label. The hard line is stolen or nonconsensual access, exploit-style access, no-entitlement gate bypass, using obvious cross-account/private/admin spillover once noticed, internal non-disclosure, or clearly illegal / morally compromising conduct.

This is a deliberate loosening from a stricter reading, recorded as a decision because it amends an accepted-baseline obligation foundational to the trust story. The owner has accepted the associated ToS / reputational / litigation risk of the permitted methods.

## What This Decision Does NOT Do

- It does **not** authorize building source-access tooling, scrapers, crawlers, runtime systems, or any software by itself. Building requires a separate, explicit owner authorization naming the bounded implementation scope.
- Later owner authorization now exists for the bounded first-tranche Source Capture Armory build in `docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md`; this boundary decision still controls the source-access standard and hard stops.
- It does **not** authorize accessing any specific source; each method/source pair must still pass the standard.
- It does **not** claim legal sufficiency; Forseti should obtain real legal counsel before commercializing a scraping-based capability.
- It does **not** waive the other 15 obligations or any non-claim.

## Direction Change Propagation

```yaml
direction_change_propagation:
  doctrine_changed: "The Data Capture source-access boundary now permits discoverable, free/account-created, and entitled paid/client/coworker access, with obvious cross-account/private/admin spillover excluded once noticed and Judgment-materiality-triggered clean reacquisition or verification before final evidence use."
  trigger: product_doctrine
  controlling_sources_updated:
    - docs/product/data_capture_source_access_boundary_decision_v0.md
    - docs/product/data_capture_source_access_method_plan_v0.md
    - docs/product/core_spine_v0_data_capture_spine_obligation_contract_v0.md
    - docs/product/data_capture_spine_pressure_test_commissioning_plan_v0.md
    - docs/product/data_capture_spine_pressure_test_execution_authorization_v0.md
    - .agents/workflow-overlay/source-loading.md
    - docs/workflows/orca_repo_map_v0.md
  downstream_surfaces_checked:
    - AGENTS.md
    - CLAUDE.md
    - .agents/workflow-overlay/source-of-truth.md
    - .agents/workflow-overlay/source-loading.md
    - docs/workflows/orca_repo_map_v0.md
    - docs/product/data_capture_spine_intake_surface_consolidation_v0.md
    - docs/product/data_capture_spine_pressure_test_slot3_wso_capture_session_v0.md
  intentionally_not_updated:
    - path: AGENTS.md
      reason: "Top-level instruction does not encode source-access doctrine."
    - path: CLAUDE.md
      reason: "Claude shim does not encode source-access doctrine."
    - path: .agents/workflow-overlay/source-of-truth.md
      reason: "Source hierarchy and propagation contract did not change; this turn applies the existing contract."
    - path: docs/product/data_capture_spine_intake_surface_consolidation_v0.md
      reason: "The intake-surface layer boundary is unchanged; it already references the source-access boundary as support when source-access mechanics are contested."
    - path: docs/product/data_capture_spine_pressure_test_slot3_wso_capture_session_v0.md
      reason: "The artifact records what a past WSO session did and did not use; historical session facts should not be rewritten to match the later boundary."
  stale_language_search: "rg -n \"methods Orca would refuse to disclose\\.|non-disclosable methods|entitled view|no scope expansion|entitlement-scope expansion|account-scope expansion|auth bypass|authentication bypass|paywall bypass|paywall circumvention|private / non-public|private, authenticated, paywalled|public, market-level, non-deceptive, and non-intrusive|public / market-level / non-deceptive / non-intrusive|public-data \\+ disclosable|public / market-level data only|hard line exclusions: auth bypass / paywall / private|LOOSEN_SOURCE_ACCESS_TO_PUBLIC_DATA_DISCLOSABLE|all 10|10 candidate\" docs/product/data_capture_source_access_boundary_decision_v0.md docs/product/data_capture_source_access_method_plan_v0.md docs/product/core_spine_v0_data_capture_spine_obligation_contract_v0.md docs/product/data_capture_spine_pressure_test_commissioning_plan_v0.md docs/product/data_capture_spine_pressure_test_execution_authorization_v0.md .agents/workflow-overlay/source-loading.md docs/workflows/orca_repo_map_v0.md | Select-String -NotMatch \"stale_language_search\""
  non_claims:
    - "not validation"
    - "not readiness"
    - "not legal sufficiency"
    - "not runtime authorization"
```

## Direction Change Propagation - 2026-07-03 Challenge-Close Clarification

```yaml
direction_change_propagation:
  doctrine_changed: >
    Owner-authorized X/Close follow-through on a public challenge modal is
    in-bounds disclosable challenge handling, not a hard blocker by itself, while
    source-specific admission still requires post-close source-owned yield and a
    preserved intervention receipt.
  trigger: product_doctrine
  controlling_sources_updated:
    - orca/product/spines/capture/core/contracts/source_access_boundary/data_capture_source_access_boundary_decision_v0.md
    - docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md
    - docs/workflows/tiktok_live_microbatch_owner_gated_handoff_v0.md
    - docs/workflows/tiktok_live_microbatch_gate_repair_fresh_thread_handoff_v0.md
    - orca/product/spines/capture/core/source_families/social_media/tiktok/tiktok_capture_lane_spec_v0.md
    - orca/product/spines/capture/core/source_families/social_media/tiktok/tiktok_sessioned_capture_warm_probe_plan_v0.md
  downstream_surfaces_checked:
    - .agents/workflow-overlay/safety-rules.md
    - orca/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  stale_language_search: >
    rg -n "challenge-close diagnostics are never capture success|do not click challenge-close controls to claim success|clicked challenge-close diagnostic receipt|diagnostic-only" docs/workflows/tiktok_ui_movement_blocker_substrate_playbook_v0.md docs/workflows/tiktok_live_microbatch_owner_gated_handoff_v0.md docs/workflows/tiktok_live_microbatch_gate_repair_fresh_thread_handoff_v0.md orca/product/spines/capture/core/source_families/social_media/tiktok orca-harness/source_capture/tiktok
  non_claims:
    - not validation
    - not readiness
    - not legal sufficiency
    - not unchallenged clean capture
```

## Non-Claims

This artifact does not claim: implementation authorization, runtime authorization, tooling authorization, legal sufficiency, data-rights sufficiency, validation, hardening, readiness, buyer proof, or source-of-truth promotion beyond this decision. It does not authorize commits, pushes, PRs, installs, or builds.

## Next Authorized Step

Use this decision as the controlling boundary basis for Obligation 2 and source-access method planning. Building any source-access tooling still requires separate explicit owner authorization naming the bounded implementation scope; the current first-tranche authorization is `docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md`.

## Direction Change Propagation - 2026-06-02 Phase Language Patch

```yaml
direction_change_propagation:
  doctrine_changed: "The source-access boundary decision no longer describes Orca as globally non-implementation; it now says this boundary does not itself authorize builds, while the later first-tranche Source Capture Armory authorization supplies bounded implementation authority."
  trigger: lifecycle_boundary
  controlling_sources_updated:
    - "docs/product/data_capture_source_access_boundary_decision_v0.md"
    - ".agents/workflow-overlay/project-authority.md"
    - ".agents/workflow-overlay/safety-rules.md"
    - ".agents/workflow-overlay/template-registry.md"
    - ".agents/workflow-overlay/validation-gates.md"
    - ".agents/workflow-overlay/source-loading.md"
    - "docs/product/data_capture_source_access_method_plan_v0.md"
  downstream_surfaces_checked:
    - "AGENTS.md"
    - ".agents/workflow-overlay/README.md"
    - ".agents/workflow-overlay/source-of-truth.md"
    - "docs/workflows/orca_repo_map_v0.md"
    - "docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md"
    - "forseti/product/spines/capture/core/source_capture_toolbox/README.md"
    - "docs/product/core_spine_v0_data_capture_spine_obligation_contract_v0.md"
  intentionally_not_updated:
    - path: "docs/product/core_spine_v0_data_capture_spine_obligation_contract_v0.md"
      reason: "Capture obligations and forbidden outputs did not change."
    - path: "docs/workflows/orca_repo_map_v0.md"
      reason: "Repo map already routes to the later first-tranche tooling authorization and armory README."
    - path: "docs/decisions/data_capture_spine_source_access_tooling_build_authorization_v0.md"
      reason: "Already supplies the later bounded first-tranche implementation authority."
    - path: "forseti/product/spines/capture/core/source_capture_toolbox/README.md"
      reason: "Already points armory work to the later bounded first-tranche authorization."
  stale_language_search: "rg -n \"Orca remains in its non-implementation phase|non-implementation / proof-setup phase|exit the non-implementation phase\" docs/product/data_capture_source_access_boundary_decision_v0.md .agents/workflow-overlay/safety-rules.md .agents/workflow-overlay/project-authority.md .agents/workflow-overlay/template-registry.md .agents/workflow-overlay/validation-gates.md docs/product/data_capture_source_access_method_plan_v0.md"
  non_claims:
    - "not validation"
    - "not readiness"
    - "not source-access boundary amendment"
    - "not blanket implementation authorization"
```
