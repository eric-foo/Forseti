# Understanding SERP Cycle — Deferred Notes v0

```yaml
retrieval_header_version: 1
artifact_role: Workflow note
scope: >
  Owner-directed deferred insights from the 2026-07-26 Summer Fridays SERP
  composition handoff review, held for the future Understanding SERP cycle.
  Notes only; no capture, route, or handoff authority.
use_when:
  - Designing the Understanding SERP cycle's question set and analysis semantics.
  - Deciding what a SERP composition capture can and cannot answer, and how to
    budget native social follow-through.
authority_boundary: retrieval_only
open_next:
  - docs/prompts/handoffs/summer_fridays_serp_social_composition_capture_handoff_20260726_v0.md
  - docs/decisions/search_surface_google_parameterized_us_capture_route_v0.md
stale_if:
  - An accepted Understanding SERP cycle design absorbs or supersedes these notes.
  - The SERP composition handoff return artifact lands and contradicts them.
```

Source: owner review of the fitness reference in
`docs/prompts/handoffs/summer_fridays_serp_social_composition_capture_handoff_20260726_v0.md`
(2026-07-26). These are analysis-semantics notes for the future cycle, not
changes to that handoff.

## Note 1 — Capped vs. uncapped question classes

The fitness reference decomposes into questions of two different evidence
classes, and only one is budget-limited:

- **Composition questions** (journey ownership per query; degree of
  social/community mediation per product/problem): the SERP capture is itself
  the primary evidence. Every observed result card answers them; they are
  uncapped and unaffected by any native follow-through budget.
- **Content-fidelity questions** (does the underlying social claim hold at the
  source): the SERP is only a pointer. Each answer costs one bounded native
  capture, so any cap here is a **verification-depth budget**, not a coverage
  cap on the deliverable.

Cycle implication: budget native follow-through by *claim*, not by platform
quota; and never compute a claim-survival rate from a purposive,
decision-leverage-selected native sample — verified rows are exemplars, and
`platform_native_unverified` dominance is a budget artifact, not a finding.

## Note 2 — Product×problem mediation variance is the signal

The decision-useful output of a composition map is not the aggregate
social-vs-official share; it is the **variance across product×problem cells**.
One problem ("lip balm burning") may be mediated almost entirely by creators
and community while an adjacent product query is retailer/editorial-owned.
That variance locates where the company has lost narrative control of a
specific problem — per product, per problem, never generalized to the brand.
Design the cycle's tables around cells, not totals, and keep the counts as
observed-result-card counts only, never prevalence or market share.

## Note 3 — Native follow-through rationale (owner-corrected 2026-07-26)

Deletion or stale indexing is a minor tail risk; currency of an unverified row
is adequately handled by the SERP card's visible date plus a canonical-URL
check. The load-bearing rationale for native capture is that the snippet is
Google's lossy compression of the source:

1. qualifier stripping (resolution/negation dropped, alarming word kept);
2. claim-scope drift (variant, shade, use condition unbound in the snippet);
3. missing commercial context (sponsorship, affiliate/commission, shop links
   live in captions/overlays, never in snippets);
4. missing resonance (engagement and comment corroboration/pushback invisible
   on the SERP).

Native follow-through is fidelity, scope, and resonance recovery — not a
liveness check. Timestamp/date matching is the default treatment for rows left
`platform_native_unverified`.

## Owner descope record — 2026-07-26

The official/retailer absence-presence question is descoped as a Deliver-side
question for the Summer Fridays cycle (owner call: the brand's
authorized-retailers list already covers the retailer set). Recorded
distinction, in case a future cycle revisits: the authorized list says who may
sell; SERP absence/presence says who actually appears mediating the journey,
including affiliates or unlisted sellers. The descope changes no capture
contract — the mediation map still falls out of composition at no extra cost.
