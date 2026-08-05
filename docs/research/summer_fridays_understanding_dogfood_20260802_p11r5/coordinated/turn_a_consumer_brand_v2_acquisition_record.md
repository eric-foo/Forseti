# Summer Fridays p11r5 Consumer-Brand Phase A Acquisition Record

```yaml
retrieval_header_version: 1
artifact_role: Consumer-brand Understanding acquisition record
scope: Acquire-and-Seal-only reconstruction and dogfood of the Summer Fridays consumer-brand v2 evidence-depth contract.
use_when:
  - Auditing retailer product-axis incidence, independent corroboration, focused-search reuse, or saturation.
  - Deciding whether a separately commissioned bounded Deliver may consume p11r5.
authority_boundary: retrieval_only
open_next:
  - docs/research/summer_fridays_understanding_dogfood_20260802_p11r5/coordinated/evidence_depth_ledger.json
  - docs/workflows/summer_fridays_understanding_dogfood_20260802_p11r5/coordinated/acquisition_seal.md
```

## Boundary and drift check

This work stopped after Acquire & Seal. It did not start Deliver. A fresh
filename scan across the p11 through p11r5 raw and repository artifact roots
found no Deliver artifact before reconstruction began. Had one existed, this
run would have preserved it and returned `BLOCKED_DRIFT`.

The earlier p11 blocked seal and all p11 through p11r4 evidence were treated as
provenance, not completion credit. The confirm-don't-trust audit reopened every
available packet manifest, validated its schema, and recomputed every preserved
file's byte count and SHA256. It also revalidated all review-corpus receipts,
p11 pointer-board parents, and all 44 Sephora onboarding packet links. Observed:
**481 manifests** and
**1,719 preserved
files**, with **0 errors**.

## Corrected retailer evidence boundary

The historical 975-row figure was a shallow selected view, not the richest
retained review corpus. Fresh reconstruction admitted every eligible unique
text review and kept retailer boundaries separate:

- Sephora: **2,926** text reviews across **44** exact product contexts.
- Amazon: **196** deduplicated rendered text reviews across **26** admitted
  exact-product contexts; the four historical terminal PDP misses remain
  explicit and receive no invented evidence.
- Revolve: **78** usable text reviews. Another **498** unique rows were explicit
  rating-without-review placeholders and remain in the denominator as excluded
  no-usable-text rows.

That yields **3,200 coded text reviews** and **3,698 effective unique retailer
rows including the explicit Revolve exclusions**. Every coded row keeps its
native review ID, exact product context, incentive state, per-axis choice
outcomes, overall choice outcomes, and source-row reference. Counts below are
captured-sample incidence, not customer-population return rates or sentiment.

| Product axis | Polarity | Strength | Retailer mentions | Negative choice rows | Positive choice rows | Qualifying non-retailer origins |
| --- | --- | --- | ---: | ---: | ---: | --- |
| Reaction, irritation, and breakout risk | pain | strong | 546 | 140 | 41 | 10 Reddit / 3 social origins |
| Value for price and usable quantity | pain | strong | 523 | 78 | 32 | 12 Reddit / 2 social origins |
| Packaging and dispensing reliability | pain | strong | 307 | 69 | 28 | 8 Reddit / 6 social origins |
| Wear time and longevity | mixed | signal | 184 | 17 | 17 | 8 Reddit / 0 social origins |
| Hydration and moisture performance | mixed | strong | 1,179 | 65 | 193 | 13 Reddit / 5 social origins |
| Texture, feel, and skin finish | mixed | strong | 1,105 | 50 | 149 | 13 Reddit / 9 social origins |
| Coverage and pigment payoff | mixed | recurring | 231 | 4 | 22 | 1 Reddit / 3 social origins |
| Shade range and color fit | mixed | strong | 168 | 14 | 27 | 4 Reddit / 5 social origins |
| Scent and flavor appeal | mixed | strong | 700 | 97 | 130 | 12 Reddit / 10 social origins |
| Formula consistency and change | pain | signal | 56 | 5 | 1 | 1 Reddit / 0 social origins |
| Application and tool performance | mixed | signal | 215 | 12 | 30 | 0 Reddit / 3 social origins |
| Hype, originality, and product trust | pain | strong | 101 | 6 | 1 | 7 Reddit / 4 social origins |

Negative choice rows mean an explicit return/refund intention, stopped or
reduced use, switching, no future purchase, or rejection/not-recommendation was
causally attached to that axis. Positive choice rows mean an explicit
repurchase, retention, recommendation, or would-purchase signal was attached.
One review can mention multiple axes, but a choice consequence is never copied
to an unrelated axis.

## Independent corroboration and owned direction

All **20 Reddit threads** were reparsed from their preserved old-Reddit bodies;
the current parser recovered the content that an earlier consolidation step had
failed to expose. The source-native social audit resolved all **36 posts** from
their native packets and self-hash-verified transcript records. Creator-authored
captions, descriptions, titles, and transcripts supply creator credit; audience
comments do not masquerade as the creator's view.

Social relationship accounting is explicit: `{"apparently_independent": 22, "disclosed_paid_or_affiliate": 1, "owned": 12, "retailer_operated": 1}`. Only `apparently_independent` creators contribute axis
strength. The 12 official posts remain useful owned evidence but contribute one
owned creator and zero independent-corroboration credit. All 12 now carry a
normalized observed date and direction-event tags. The observed owned direction
is a 2026 sequence from hydration/lip-franchise and awards/community activation
into body and fragrance expansion plus multi-retailer August launch timing; it
is a factual publishing timeline, not proof that the owned product claims are
true.

## Focused continuation and saturation

Each of the 12 material axes is tied to exactly two already completed,
directly relevant acquisition jobs: one `corroborate_or_segment` job and one
`disconfirm_or_compare` job. The mapping reuses captured Phase 1/Phase 2 jobs
only where their actual query addressed the axis. No search result receives
evidence credit; only its already captured native destinations and admitted
packets do. Because all 24 goal slots resolved to completed existing jobs, no
new live request was pending and no site was hit again merely to increase a
count.

Two final dry batches then rechecked all 12 axes against the source-native join,
relationship exclusions, retailer incidence, and focused-job accounting. Both
produced zero new axes, zero strength changes, zero incidence changes, and no
new material seam. Additional same-family volume that would not change an axis
is dominated. A prevalence estimate would require a different sampling design
and remains outside this bounded qualitative acquisition.

## Limits preserved

This pack supports a bounded qualitative understanding of product pain and the
strongest delight axes. It does not support population prevalence, sentiment
percentages, a complete creator landscape, medical or ingredient-safety
causality, or exact conclusions about the four missing Amazon PDPs. Formula
consistency/change and wear/longevity remain visible `signal` axes rather than
being inflated to recurring or strong; the seal preserves that lower confidence.
