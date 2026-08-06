# Deliver Decision-Memorandum Method v0

```yaml
retrieval_header_version: 1
artifact_role: Product-method spec (Deliver decision-memorandum method)
scope: >
  Method rules for an explicitly commissioned decision-bearing Deliver output
  of a Forseti Intelligence Cycle: a competitive decision memorandum (challenger
  or defender framing) synthesized from a sealed Understanding substrate. Owns
  the memorandum's analysis steps, claim discipline, artifact shape, and
  pre-outreach gate. Does not change the acquisition gate, the seal contract,
  or the decision-neutral substrate artifact.
use_when:
  - A Deliver commission asks for a decision-bearing memorandum from a sealed corpus.
  - Reviewing whether a produced decision memorandum followed the bound method.
  - Commissioning the defender-framing derivative of an existing memorandum.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/commission_signal_board/workflows/commission_signal_board_playbook_v0.md
  - docs/decisions/forseti_product_thesis_decision_adjudication_v0.md
  - docs/decisions/forseti_company_intelligence_information_architecture_v0.md
  - .agents/workflow-overlay/product-proof.md
stale_if:
  - The Intelligence Cycle playbook's Turn B contract is amended in a way that covers or contradicts these rules.
  - An owner decision supersedes the memorandum product form (e.g., Decision Desk adoption).
  - Repeated runs show a rule is dead weight or a recurring defect class it should catch.
```

- Status: METHOD_V0 — calibrated on the Summer Fridays dogfood planning lane;
  no run has yet completed under it.
- Non-claims: asserts no validation, buyer proof, willingness-to-pay,
  readiness, or outreach authorization. A proxy-buyer run is product learning
  under `.agents/workflow-overlay/product-proof.md` until a qualified
  live-decision receipt clears a stronger tier.

## Entry Gate

This method is the Deliver phase's synthesis method for decision-bearing
artifacts. Enter only as a Synthesize turn under the playbook, with the
Deliver phase's governing acquisition gate passed: a passing Understanding
phase seal verified in fresh context, plus a durable bounded capture-return
artifact for every supplement the memorandum consumes.

Analysis of the preserved evidence — the joins, recomputations, and syntheses
Rules 2 and 13 require — is this method's job. What is prohibited is
modifying the sealed record or asserting any claim above its sealed ceilings.
New evidence is acquired only through the Deliver phase's bounded Acquire &
Seal turn — decision-specific, claim-scoped supplements (e.g., a one-shot
search-interest capture), never a general re-scan. A supplement that would
change a sealed claim ceiling requires a full Deliver-phase Acquire & Seal
with its own phase seal before synthesis; that Deliver seal augments the
Understanding seal — synthesis then requires both, the Deliver seal's
re-adjudicated ceilings govern the claims it names, and every other claim
stays under the Understanding ceilings.

## Supplement Chain

Every supplement the memorandum consumes travels this chain; a supplement
missing any link is not consumable:

1. **Owner authorization** — bounded, current-turn or accepted-handoff, scoped
   to the decision (recorded in the capture handoff's sourcing-authorization
   section).
2. **Capture handoff** — a durable packet under `docs/prompts/handoffs/`,
   authored under the prompt-orchestration contract, binding query scope,
   caps, output paths, and claim limits. Capture mechanics resolve through the
   capture spine's own authority.
3. **Typed capture return** — a durable return artifact plus machine-readable
   series in a dated `docs/research/` directory, carrying capture parameters,
   threshold/null ledger, failure ledger, and its own non-claims section.
4. **Evidence-input packet** (when the return crosses lanes) — a routing
   handoff carrying confirm-don't-trust hashes for the return artifacts and a
   short orientation digest; the return, not the digest, is the evidence of
   record.
5. **Synthesis citation** — the memorandum cites the return by
   repository path and sha256 and stays inside the return's own non-claims.

Worked instances of links 2–5 (the first resolves in-tree; the latter two land
via PR #1433, pin: `origin/claude/sf-deliver-search-interest-input`):
`docs/prompts/handoffs/summer_fridays_search_interest_capture_handoff_20260805_v0.md`,
`docs/research/summer_fridays_ci_inputs_20260805/search_interest_capture_return.md` (PR #1433),
`docs/prompts/handoffs/summer_fridays_deliver_search_interest_input_handoff_20260806_v0.md` (PR #1433).

## Run Sequence

Steps 2–4 are the Deliver phase's problem-framing step: they bind the decision
frame before any drafting.

1. Verify the seal gate (playbook Synthesize-turn contract).
2. Target screen (Rule 1) — select the anchor product.
3. Claims register and claims-to-complaints join (Rule 2).
4. Product-slice recomputation (Rule 13) — re-derive axis support at the
   anchor-product grain before any slice-level claim.
5. Draft the memorandum (Rules 3–10, 12).
6. Cold adversarial read (Rule 9).
7. Defender-framing derivative when commissioned, produced under the Framing
   Variants contract below — exposure map, moat identification, defector
   destinations — never a mechanical flip of the challenger recommendation.
8. Outreach only under a separate authorization; this method ends at
   ready-to-show.

## Rules

1. **Target screen first.** The anchor product is selected by evidence, not by
   chatter volume or author intuition. Score each candidate product on two
   axes with a penalty:
   - *Prize* — attention and traction proxies only: accumulated review mass,
     review velocity, distribution breadth, search-interest direction, and the
     incumbent's own paid emphasis from ad-transparency captures (the
     incumbent's revealed bet). Label all of these as attention proxies; none
     is sales.
   - *Exploitable weakness* — complaint severity, whether complaints carry
     behavior consequences (returns, switching, refusal to rebuy), and
     claims-gap findings from Rule 2.
   - *Defended-strength penalty* — strong positive-choice counterevidence on
     the same product lowers its attack score.
2. **Claims register and typed join.** Build the promise-side register from
   captured product pages, owned posts, and ad-library creative (paid copy is
   the sharpest promise set). Join each promise to the complaint evidence and
   type every gap: *price-to-quantity*, *promise-vs-delivered*, or
   *substitutability*. A link counts only when it cites the exact promise text
   and the specific complaint evidence; weak links are marked weak, never
   rounded up. Attack recommendations aim at the typed root, not the surface
   complaint (e.g., "overhyped" is a symptom to decompose, never a wedge).
3. **Resolution labels.** Every load-bearing claim states its grain on three
   dimensions: which product (one product vs. portfolio), signal kind
   (attention/traction vs. sales), and sample kind (captured sample vs.
   population). A claim at one grain never supports a conclusion at another
   without an explicit stated bridge.
4. **Interpretation-table check.** Any product-role assertion (flagship,
   leading, declining) is checked against the interpretation rules in
   `docs/decisions/forseti_company_intelligence_information_architecture_v0.md`
   rather than asserted from memory.
5. **Declared challenger profile.** A proxy run declares the challenger's
   decision-swinging attributes (price tier, category incumbency,
   substantiation capability, retail access, claim permissions, price-fight
   appetite) and tags each recommendation with the attributes it depends on.
   A real buyer's facts replace the profile and the recommendations re-resolve;
   the memorandum is built to survive that swap.
6. **Voice-evidence claim ladder.**
   - *Allowed, strong:* direction plus cross-channel robustness plus
     consequence ("the visible voice on this axis tilts negative across
     independent channels, with documented returns and switching").
   - *Allowed, labeled:* within-sample ratios with the sample named.
   - *Allowed:* perception-surface claims — what a prospective shopper visibly
     sees at the shelf or search results — as commercial facts in their own
     right.
   - *Banned:* population rates, prevalence, sentiment percentages of
     customers. Every claim whose decision value depends on a rate names the
     representative instrument (survey, transaction data) that would upgrade
     it.
7. **Per-channel behavior weighting.** Weight each channel by the behavior it
   can actually carry: retailer reviews for stated purchase outcomes
   (returned, won't rebuy, repurchasing); community threads for concrete
   switching and destination narratives. Adjective-only evidence ranks below
   behavior-bearing evidence in both.
8. **Conditionality discipline.** One line of stated assumptions, one
   "what would change this answer" paragraph. No recurring hedge sections.
9. **Cold adversarial read.** Before any outreach, a fresh-context reader with
   no authoring involvement attacks the memorandum, explicitly hunting grain
   conflations (Rule 3 violations), claim-ladder violations (Rule 6),
   ungrounded product-role assertions (Rule 4), and — by dereferencing a
   sample of load-bearing claims to their cited evidence — synthesis-layer
   misparaphrase (prose that drifts from what the cited evidence says). The
   read returns a written disposition: findings plus a ready / not-ready
   verdict, kept with the run outputs. Material findings must be closed and
   the closure re-checked (by the same or a fresh cold reader) before
   ready-to-show; an asserted-but-unrecorded cold read does not satisfy this
   rule. The cold read gates ready-to-show; it never proves value, demand, or
   willingness to pay.
10. **Artifact shape.** A concise decision memorandum plus an inspectable
    evidence appendix in which every claim resolves to preserved-source
    locators. No deck (a deck is at most a later derivative for a live buyer's
    internal circulation), no brand-history tour, no source-family or
    acquisition-volume organization, no twelve-axis narrative — only
    decision-bearing axes appear in the body; the rest stay in the appendix.
11. **Machine-consistent outputs.** The target screen, axis map, destination
    map, and claims join are also emitted in machine-readable form so
    successive runs in one category stack into a cross-brand defection map
    without rework. Each emitted structure carries a `schema_version` field.
    The first run under this method files the schema definition (field names
    and meanings) as `deliver_output_schema_v1.json` beside its own outputs,
    and its closeout adds a pointer to that file in this method doc's
    `open_next` in the same work unit — after which this doc names the schema
    authority and every later run consumes it. A format change bumps the
    version; version-migration ceremony is deferred until a v2 actually
    exists. Until the first run lands, this rule binds only the
    `schema_version` field and the first-run filing obligation — there is
    deliberately no speculative schema to conform to.
12. **Defense tiers and cap.** The memorandum classifies every assessed axis
    into exactly one of three tiers. Start every axis in the middle tier and
    move it only when it satisfies one of the other definitions:
    - *Attack candidates* — behavior-backed weaknesses whose negative reading
      remains decision-bearing after Rule 1's same-product defended-strength
      penalty. Adjective-only or merely below-average performance does not
      qualify.
    - *Contested ground* — the final tier for everything not moved to attack
      or defended, including mixed evidence and above-average performance.
      Compete on merits; no warning label. Most axes belong here.
    - *Defended — zero, one, or two strongest only.* Eligibility requires a
      positive-side Rule 6 strong claim: documented positive-choice behavior
      such as repeat purchase or a concrete recommendation act (never ratings
      or adjectives alone), consistent across independent channel types under
      Rule 7. That reading must remain the stronger behavior-backed reading
      after same-axis negative behavior evidence and any corrected or
      re-derived outcome codings are applied. Rank every eligible axis by the
      strength of that evidence, label at most two as defended even when more
      are tied, and leave every unselected qualifier in contested ground.
    In a challenger memorandum, the do-not-attack list is exactly the defended
    tier; it is empty when no axis qualifies. Above-average performance is
    never, by itself, "do not attack."
    The cap forces ranking instead of thresholding; it exists because
    positive-counterweight evidence has empirically inflated (p11r7 semantic
    review) and because threshold-thinking over-shrinks the attack surface.
    Revisit posture: first-run evidence may revise the cap's size, never
    silently per-run.
13. **Slice honesty and closed research.** Axis support computed at portfolio
    grain is re-derived at the anchor-product grain before any slice-level
    claim; a slice that falls below the sealed evidence floor degrades to a
    bounded-signal claim rather than being rounded up. The sealed corpus stays
    closed; paid upgrades (lab benchmarking, representative surveys, purchased
    market data) are priced per the specific claim each would strengthen.

## Framing Variants

The same sealed evidence and analysis serve two commissioned framings:

- **Challenger memorandum** — wedge selection, do-not-attack list, and probe
  list for a named or declared-proxy attacker.
- **Defender memorandum** — exposure map, moat identification, and defector
  destinations for the subject company itself. The defender variant does not
  prioritize internal remediation (the subject's internal data dominates
  there); it shows what an outside attacker sees and where silent defectors
  go, which internal data cannot contain.

Both variants carry the same claim ladder, resolution labels, and non-claims.
