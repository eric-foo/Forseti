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

Enter only from the playbook's Turn B with its acquisition gate passed: sealed
phase artifact verified in fresh context. This method never reopens, edits, or
reinterprets the sealed corpus; new evidence is acquired only through a
separately authorized, bounded, claim-scoped supplement (e.g., a one-shot
search-interest capture), never a general re-scan.

## Run Sequence

1. Verify the seal gate (Turn B contract).
2. Target screen (Rule 1) — select the anchor product.
3. Claims register and claims-to-complaints join (Rule 2).
4. Product-slice recomputation (Rule 12) — re-derive axis support at the
   anchor-product grain before any slice-level claim.
5. Draft the memorandum (Rules 3–10).
6. Cold adversarial read (Rule 9).
7. Defender-framing derivative when commissioned (same evidence, flipped
   recommendation section).
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
   conflations (Rule 3 violations), claim-ladder violations (Rule 6), and
   ungrounded product-role assertions (Rule 4). The cold read gates
   ready-to-show; it never proves value, demand, or willingness to pay.
10. **Artifact shape.** A concise decision memorandum plus an inspectable
    evidence appendix in which every claim resolves to preserved-source
    locators. No deck (a deck is at most a later derivative for a live buyer's
    internal circulation), no brand-history tour, no source-family or
    acquisition-volume organization, no twelve-axis narrative — only
    decision-bearing axes appear in the body; the rest stay in the appendix.
11. **Machine-consistent outputs.** The target screen, axis map, destination
    map, and claims join are also emitted in a schema-consistent
    machine-readable form so successive runs in one category stack into a
    cross-brand defection map without rework. Silent format drift between runs
    is a defect.
12. **Slice honesty and closed research.** Axis support computed at portfolio
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
