# Reddit Listing-Efficiency Full-Corpus Application v0

```yaml
retrieval_header_version: 1
artifact_role: Research validation artifact
scope: >
  Mechanical application of the Reddit listing-efficiency policy to all 5,335
  retained deep-captured threads, plus a post-freeze 60-thread diagnostic audit
  of semantic disagreement clusters.
use_when:
  - Evaluating the Reddit source-family listing-efficiency policy.
  - Estimating the policy's mechanical effect on the captured corpus.
  - Inspecting known semantic and projection failure clusters.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_listing_efficiency_policy_v0.md
  - docs/research/reddit_listing_efficiency_holdout_100_v0.md
stale_if:
  - The 5,470-row canonical manifest, retained-source disposition, or policy floor changes.
  - A later audit supersedes the diagnostic conclusions.
```

## Result

The calibrated policy is directionally strong and materially more efficient
than the prior engagement-head/title-rescue selector, provided its qualitative
gates remain model judgment rather than keyword automation.

Across all 5,335 retained deep-captured threads:

| Mechanical outcome | Threads |
| --- | ---: |
| General suppression at `0–3` comments | 1,446 |
| Continue to commission-conditioned model adjudication at `4+` comments | 3,889 |
| Exactly four comments, retained for adjudication | 280 |
| Score zero but retained for adjudication | 86 |
| Selected by the old gate but removed by the new floor | 702 |
| Omitted by the old gate but restored to model review | 107 |

The discussion floor therefore removes 27.1% of retained threads before any
semantic review while preserving the tested four-comment boundary and
score-zero discussions.

The result is not “deep-read 3,889 threads.” Those rows receive cheap
listing-only model adjudication. Only `yes` rows receive exact-thread capture
or comment analysis.

## Why no universal corpus label exists

Commission applicability is load-bearing. A fragrance recommendation map,
retailer duty complaint, prescription-switching discussion, or resale
release-cycle explanation can be commercially rich and still be worth zero for
the current client. Persisting one global `yes` or `no` in the Data Lake would
turn a decision-relative judgment into false source truth.

The full-corpus pass therefore applies only stable mechanical facts globally:
comment floor, score non-veto, context availability, and source-visible cues.
Admission remains bound to a declared commission.

## Method and provenance

The universe was every `retained_source` row with its chosen content record in
the canonical 5,470-row manifest:

| Input/output | SHA-256 |
| --- | --- |
| Canonical manifest | `289ee06d3e4f8feb96540feafe375ae7333c2f3030d884fd28c801583d44027f` |
| Full 5,335-row mechanical projection | `3188bbe5fee3b4efc8b556dbbdcfb5e543e6d193d4c256a83828622c7903e5c4` |
| Frozen 60-row listing labels plus completed adjudication | `a0adab3aab89f558d8c91859b99a22233485de82f8c2081d0ce7af943cf65f13` |
| 60-row deep-audit capsules | `b4d5bd0ce4f185ca386394b54fa4dd6ecab902501f1afe1127c195635d01b244` |

The projection inspected all retained content records only to compute
diagnostic marker counts and independent-comment structure. Those hidden
fields did not alter the global mechanical policy outcome.

The 60-thread diagnostic sample excluded all prior owner-calibration,
100-thread holdout, source-audit, and exact-four probe threads. Its listing
labels were frozen before bodies/comments were opened:

- 20 old-selected listings with weak visible decision promise;
- 20 old-unselected listings restored by the four-comment review boundary;
- 20 opaque listings deliberately enriched using hidden commercial/performance
  markers.

The third cluster is adversarial diagnostics, not prevalence. None of the
60-row outcome rates is a corpus-wide accuracy estimate.

## Diagnostic outcomes

| Outcome | Count |
| --- | ---: |
| Correct admit | 4 |
| Correct suppress | 23 |
| Borderline promoted | 10 |
| Borderline held | 3 |
| Borderline suppressed | 1 |
| Accepted commission-conditional miss | 12 |
| False negative: semantic rule | 4 |
| False negative: listing projection | 1 |
| False positive | 1 |
| Duplicate/redundant judgment | 1 |

### Old selected, weak visible promise

The old engagement-head gate selected all 20. After audit, seven were correct
general suppressions, five were useful only to another commission, one
borderline suppressed, and one promising discontinued-product request yielded
no substitute. Six contained enough current value to retain or promote.

This cluster confirms that engagement-head capture is too expensive: high
discussion often validates appearance, retail operations, treatment, or
another commercially irrelevant objective.

### Old unselected, restored to review

Of 20 sampled rows, one was a correct admit, two borderlines promoted, two
borderlines held, and one product-compatibility question was a semantic miss.
Twelve correctly suppressed, one was commission-conditional, and one duplicated
another request.

Restoring every four-plus-comment row to **listing review**, not automatic
capture, is the right boundary. It recovers sharp low-engagement evidence
without deep-reading the entire tail.

### Opaque high-marker diagnostic

Of 20 deliberately enriched opaque listings, three were correct admits, five
borderlines promoted, one borderline held, and one title hid an exact Aveda
failure stack and named substitute. Six were commission-conditional and four
correctly suppressed.

The result supports a cheap context-preview seam. It does not support opening
every opaque thread's comments.

## Calibrations added

1. **Swatches are their own archetype.** A specific swatch listing can expose
   product maps, undertone behavior, discontinuation, price, size, and
   substitutes. It should not inherit generic-showcase suppression.
2. **Structured current-use formats can carry CI.** SOTD and similar formats
   become valuable when a product stack, performance ratings, restock intent,
   or suspected batch failure is likely.
3. **Product compatibility is not merely technique.** Exact material or
   product-type interactions can change formulation, education, and competitor
   decisions.
4. **Opaque means preview, not confident suppression.** Above the comment
   floor, missing product/media context maps to `borderline` and a cheap
   listing-context preview.
5. **High-engagement showcases remain conditional.** A full disclosed stack
   plus product-specific purchase response can justify the dive; appearance
   praise alone cannot.
6. **Promising replacement requests can still fail.** A discontinued Sephora
   brush request yielded no substitute. This is an accepted gamble, not grounds
   to remove the archetype.
7. **Transaction-source suppression still holds.** Rare release-cycle or
   scarcity evidence remains commission-specific and retrievable.
8. **Body-level redundancy matters.** Two rows with title/subreddit variants
   had the same normalized post-body hash. Title-plus-body exact matching did
   not prevent duplicate judgment. Upstream body-level near-duplicate handling
   is a separate smallest-complete work unit.

## Opinion

The policy is ready to govern the Reddit lane at research/product-contract
tier because its stable boundary is now repeatedly falsification-tested:

- score zero was rejected as a veto;
- `0–4` was rejected as a floor;
- `0–3` retained its efficiency role with an explicit poster-only residual;
- the 5,335-row pass proves the mechanical savings;
- targeted audits explain where model judgment—not more numeric scoring—is
  required.

The important constraint is architectural: **do not automate the semantic
gates with the existing title keyword score.** That score cannot determine
commission fit, distinguish appearance resonance from product value, or resolve
missing media. Its safe role is to expose listing cues to the model.

This is not corpus-wide accuracy, production validation, buyer proof, or a
claim that 3,889 rows deserve deep reads.
