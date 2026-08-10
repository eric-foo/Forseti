# Forseti Intelligence Claim-Support Contract v0

```yaml
retrieval_header_version: 1
artifact_role: Product artifact (owner-adopted intelligence claim-support contract)
scope: >
  Intelligence-cycle-wide contract for turning captured evidence into bounded
  observations, resonance-supported statements, independently repeated
  patterns, and cross-venue corroborated claims without hiding provenance,
  counterevidence, scope, or causal limits.
use_when:
  - Synthesizing, comparing, weighting, or promoting evidence into a finding, claim, explanation, memo input, or recommendation anywhere in the Forseti intelligence cycle.
  - Deciding what engagement, repeated statements, different venues, or reported behavior actually corroborate.
  - Auditing whether an evidence-backed statement outruns its exact sources.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/judgment/claim_ladder/judgment_spine_evidence_ladder_architecture_v0.md
  - forseti/product/spines/judgment/demand_read/c2_weighting/judgment_spine_c2_in_case_evidence_weighting_doctrine_v0.md
  - forseti/product/spines/commission_signal_board/authority/forseti_commission_signal_board_prompt_structure_rules_v0.md
stale_if:
  - The owner changes how engagement, independent recurrence, cross-venue corroboration, counterevidence, or explicit self-attribution may support an intelligence claim.
  - Judgment ownership of evidence synthesis moves to another spine.
```

## Status and purpose

`OWNER_ADOPTED_V0` on 2026-08-07.

This contract governs the support carried by an underlying intelligence claim.
It is not the Judgment Spine evidence ladder, which separately governs what a
completed Forseti run or proof artifact may claim about product learning, buyer
proof, or judgment quality. Both contracts may apply to the same artifact and
answer different questions:

- this contract asks, **"what do these sources support about the subject?"**;
- the evidence ladder asks, **"what may this run or artifact claim about its own
  proof tier?"**

## Unit of corroboration: one bounded proposition

Corroboration is claim-specific. Before combining evidence, bind the proposition
at the narrowest material scope:

```text
subject product or entity
  + comparator when present
  + attribute, choice, or behavior
  + direction
  + material condition
  + formula/version and time boundary when known
```

Two items mentioning the same broad axis are not automatically corroborating.
A review about an older formula does not establish the current formula. A claim
that a balm tastes good does not corroborate a claim that flavor causes
repurchase. An editorial wear test may corroborate wear performance but cannot
corroborate a customer's private purchase motivation.

When version, period, actor identity, or another load-bearing scope fact is
unknown, preserve `unknown`; never silently merge it into a known scope.

## Provenance floor

Every evidence unit used in a synthesized claim must resolve to:

- source URL or durable source identifier;
- source role and venue;
- source-visible actor/account identity, or `unavailable`;
- publication or observation time, or `unavailable`;
- exact excerpt, measurement, or bounded source-native observation;
- product/entity and formula/version scope when observable;
- source-native engagement metric, raw value, and observation state, or an
  explicit `engagement_unavailable`;
- any capture, parser, deletion, selection, or identity limitation that changes
  what the unit can carry.

A citation string that cannot resolve to this floor is a discovery lead, not
claim-bearing evidence. Missing engagement is not zero engagement.

## Claim-support postures

These postures identify the support route actually present. They are not a
universal source-quality score or a total ranking: a directly observed current
price is stronger for a price claim than repeated comments, while repeated
first-hand reports are better fitted to a repeated-experience claim. Exact
counts, source roles, proximity, and limitations always travel with the posture;
the label never replaces them.

| Posture | Meaning | Maximum honest wording |
| --- | --- | --- |
| `isolated` | One attributable observation with no material positive engagement and no qualifying recurrence. | "One source/person reported..." It cannot establish a directional competitive finding by itself. |
| `directly_observed` | A competent source or direct trace exposes the bounded fact itself, such as a dated price, published claim, ad, stock state, or measured result. | State the exact observed fact and scope. It does not establish prevalence, motive, durability beyond the observation window, or causation. |
| `resonance_supported` | One observation has material positive source-native endorsement or explicit agreeing replies. | "A materially endorsed statement reported..." This is audience resonance, not an independent-experience count or prevalence estimate. |
| `independently_repeated` | The same bounded proposition recurs across at least two independently credited actors/origins. | "Multiple independent sources/people reported..." State the exact count and venue concentration. |
| `cross_venue_corroborated` | The same proposition is independently repeated across at least two source roles competent to observe it. | "The pattern recurs across [named roles/venues]..." This is not representative market prevalence. |

Reported behavior is a separate strength dimension, not a source-prestige
level. Preserve evidence of purchase, repurchase, switching, abandonment,
return, recommendation, or other costly behavior in `behavior_evidence_refs`.
Behavior can strengthen a claim only for the behavior it actually records.

## Engagement is resonance corroboration

Likes, points, helpful votes, agreeing replies, and equivalent source-native
signals are evidence that a statement resonated with an audience. They are not
literal headcounts of people who independently lived the same experience.

Rules:

1. Preserve the raw metric kind, raw value, observation time, and available
   context. Do not translate points into independent-origin counts.
2. Zero or negligible positive engagement earns no resonance credit. The unit
   remains available as raw evidence, a contradiction, a discovery lead, or a
   safety/rare-defect trigger.
3. Material positive engagement may earn `resonance_supported` when the basis
   is visible. Do not install a universal cross-platform number: venue size,
   exposure, age, ranking, and metric semantics differ. When context is too thin
   to judge materiality, keep the raw value and do not award the posture.
4. An explicit agreeing reply may be credited as another actor observation only
   when its actor is distinct and the reply actually asserts the proposition.
   Thread co-location remains visible and does not become cross-venue credit.
5. High engagement can support a directional description of the endorsed
   statement. It cannot alone establish prevalence, market share, objective
   performance, or causation.

## Independence, de-duplication, and source-role fit

- Reposts, syndicated articles, quoted reviews, screenshots, and downstream
  summaries that share one origin count once.
- Exact, possible, confirmed, or unavailable same-actor overlap cannot be used
  to manufacture independent-origin credit.
- Separate comments in one thread may provide distinct-actor recurrence when
  identity is visible, but the shared conversational context remains disclosed.
- Cross-venue credit requires different source roles, not merely different URLs.
- A source role must be competent for the proposition: retailer reviews and
  community posts may corroborate reported experience; editorial or measured
  tests may corroborate observable performance; owned claims and advertisements
  establish actor strategy, not customer experience; creator-authored promotion
  is not independent customer corroboration.

## Counterevidence and conflict

Every synthesized claim carries one `conflict_posture`:

- `not_checked`: the evidence set was not checked for material opposition;
- `none_observed`: a bounded check found no material opposition;
- `mixed`: credible support exists in opposing directions;
- `contradicted`: stronger or more directly fitted evidence defeats the proposed
  direction.

Material opposing evidence is referenced separately. More evidence in both
directions strengthens the finding that the experience is split; it does not
justify averaging the conflict away or selecting the preferred side.
`not_checked` caps a claim at an unresolved or provisional posture.

## Causal and motivational boundary

Public evidence may support descriptions and reported reasons. It does not gain
causal force merely through repetition.

- One person saying "I bought because X" is an explicit individual
  self-attribution.
- Multiple independent people saying the same thing supports a **repeated
  reported reason**.
- Neither licenses an unqualified statement that X causes the behavior across
  customers or the market.
- When one statement bundles several possible reasons, attribution remains
  unresolved unless the source separates them.
- Correlation, co-occurrence, timing, or brand-to-creator propagation may
  nominate a causal hypothesis; they do not establish it.

## Cycle ownership

- **Scanning/discovery** nominates candidate sources and propositions. It does
  not award a support level from snippets or co-mentions.
- **Capture** preserves source-native body, provenance, engagement, time, and
  limitations. It does not decide what the source proves.
- **Cleaning/ECR** reconciles identity, duplicates, shared origination, product
  scope, and evidence-unit references without strengthening meaning.
- **Judgment** binds the proposition, assigns claim-support and conflict
  postures, checks source-role fit, and states the causal ceiling.
- **Deliver** consumes these bounded claims. It may combine them for a decision
  but may not silently promote an isolated or resonance-only observation into
  an independently repeated, cross-venue, representative, or causal claim.

## Minimum synthesis shape

Any durable claim-bearing output uses this shape directly or an owning schema
that maps every field without loss:

```yaml
claim_support:
  bounded_proposition:
  support_posture: isolated | directly_observed | resonance_supported | independently_repeated | cross_venue_corroborated
  independent_origin_count:
  source_roles: []
  evidence_refs: []
  engagement_evidence_refs: []
  behavior_evidence_refs: []
  counterevidence_refs: []
  conflict_posture: not_checked | none_observed | mixed | contradicted
  scope_conditions: []
  causal_ceiling:
```

`causal_ceiling` is plain, bounded language such as `descriptive_only`,
`single_actor_self_attribution`, `repeated_reported_reason`, or
`causal_not_established`; it is not a numeric confidence score.

## Promotion rules

- `isolated` testimonial or interpretive evidence with zero, negligible, or
  unavailable resonance cannot by itself set a subject/competitor advantage,
  broad finding, or recommendation. Directly observable facts use
  `directly_observed`, not this exception.
- `directly_observed` may carry the bounded descriptive fact its source is
  competent to expose, but nothing broader.
- `resonance_supported` may carry the endorsed descriptive statement only with
  its engagement basis and resonance ceiling visible.
- `independently_repeated` requires at least two independent credited origins;
  exact count, identity limitations, and venue concentration remain visible.
- `cross_venue_corroborated` requires at least two competent source roles and
  at least one independent credited origin in each.
- `mixed` evidence yields a split/conditional finding unless an evidenced
  condition actually separates the directions.
- `contradicted` evidence cannot support the defeated direction.
- A downstream decision may demand more evidence because of stakes, but higher
  stakes never increase what an existing item proves.

## Non-claims and residuals

This contract is qualitative and claim-specific. It creates no universal
numeric score, source-prestige ladder, sentiment percentage, representative
market estimate, causal estimator, bot/fake classifier, or automatic truth
verdict. Mechanical validators may enforce schema and impossible combinations;
semantic review still owns whether two items truly support the same proposition
and whether engagement is material in its native context.
