---
retrieval_header_version: 1
artifact_role: Summer Fridays Route 1.7 bundle-v4 full-corpus projection and bounded semantic calibration receipt
scope: Full captured-corpus work-unit projection plus one real no-API, three-worker, two-level semantic calibration; no full-corpus semantic completion or Deliver conclusion
use_when:
  - Auditing the bundle-v4 scale correction and its real Summer Fridays calibration.
  - Planning or resuming full-corpus semantic judgment from the exact external lineage below.
authority_boundary: evidence_only
open_next:
  - forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
  - docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/semantic_integration_full_corpus_shadow_20260808_v1/README.md
---

# Summer Fridays Route 1.7 bundle-v4 shadow receipt v2

## Observed result

Bundle v4 represents the complete corrected Summer Fridays Phase A customer
corpus as 513 bounded semantic work units. It admits all 59,225 assessable
leaves from the 60,901-item captured denominator, preserves an exact
one-owner mapping for every admitted evidence ID, and assigns exactly 171 work
units to each of three no-API workers. The historical acquisition seal was not
restamped and no Deliver conclusion was produced.

| Measure | Bundle v3 shadow | Bundle v4 observed | Change |
|---|---:|---:|---:|
| Work units / prompts | 716 | 513 | -28.4% |
| Bundle bytes | 222,210,526 | 126,163,332 | -43.2% |
| Prompt bytes | 106,583,373 | 55,755,762 | -47.7% |
| Largest prompt bytes before file newline | 149,996 | 149,672 | within the unchanged 150,000-byte ceiling |

The reduction comes from storing repeated conversation/product context once
and referring to it, not from sampling or dropping evidence. Source v3 remains
unchanged. Bundle v4's corpus hash covers the shared context registry, and the
work-unit projection proves a bijection over all admitted evidence IDs.

The full projection is not a completed semantic run: `0 / 513` full-corpus
responses were authored. It proves that the complete corpus is represented and
repeatably partitioned at materially lower transfer cost.

## Real bounded semantic calibration

The calibration used one complete 186-leaf Reddit conversation
(`reddit_thread_1gti140`) plus 20 real assessable retailer-review containers.
All 206 leaves were assigned across three workers as 70 / 70 / 66 and every
worker response passed the repository validator. The compilation contained 440
semantic units.

The first reconciliation level used two independent prompt batches. It emitted
six merged nodes covering 12 semantic units and carried 428 non-equivalent
units without discarding them. The corrected level-wide emerging-axis owner
made one semantic decision over all 97 unique proposed labels, producing 78
consolidations: 76 `accepted` and two `nonmaterial`. A second, 6,764-byte
prompt level kept the six meanings separate and marked them terminal. The
final view reports:

- 206 / 206 evidence leaves accounted for;
- 206 semantically assessed, including one explicitly unresolved leaf;
- six bounded evidence propositions;
- 428 preserved unmerged semantic units;
- 78 emerging-axis candidates;
- zero model/provider API calls.

This proves a real three-worker resume path, two reconciliation levels,
terminal compilation, finalization, and evidence-packet projection. It does
not prove that all 59,225 assessable full-corpus leaves can converge to one
terminal batch.

## Proven evidence pull

The projected packet for `prop_44f789e1f19f137a4e85` returns both underlying
Reddit comments, their source URLs, public handles, engagement observations,
parent/thread context, product binding, semantic statements, and exact support
relations. The bounded proposition is that two authors called SK-II Pitera
Facial Treatment Essence a holy-grail product without stating the performance
basis. The two evidence items are separate credited origins inside one
conversation; the packet does not turn two comments into market prevalence or
a recommendation.

## Failures surfaced and closed

- One extraction worker initially omitted required subject bindings. The
  invalid response remains preserved and the corrected response passed.
- A refreshed corpus hash made prior responses stale. Status reported them as
  invalid; only the integrity hash was rebound after prompt equivalence was
  proven, and each response was revalidated.
- Status visibly reported two valid worker partitions and one missing partition
  before the third staged response was atomically published.
- Parallel level-one workers initially made overlapping emerging-axis label
  decisions, causing level two to reject its own stage. Bundle v4 now declares
  one batch as the level-wide semantic owner for the complete unique label set;
  other batches must return an empty consolidation list. The compiler still
  makes no lexical or arbitrary semantic choice.

## Exact external lineage

Large artifacts live under
`C:\tmp\forseti-phase-a-semantic-work-units-v4-dogfood-20260808`.

- `semantic_bundle_v4_identity_final.json`: 126,163,332 bytes; raw SHA-256
  `d214a44e03105aebd07359b1a13769076dfafa5e03ac09c1fefc8e04ac1343f6`;
  bundle SHA-256
  `b3d88c8e910be1b22496222ea9c5e8e8bc6579c4c6e4ae7aa3af87f10324002c`;
  corpus SHA-256
  `8b1b0c2159424e99c61ae7d68082f7e0b76a9b790cb1764cc7f5e695eb90e273`.
- `calibration_bundle_v4_identity_final.json`: bundle SHA-256
  `18c73e295b2eca96b800e117d756b4992e463d303e9b2a8ac504e9a3d82fd5e2`.
- `calibration_compilation_identity_final.json`: compilation SHA-256
  `f4c1a92b3663be4f8621640432c2f9d3f6b7206827db8bd182c5e4d8d649fcda`.
- `reconciliation_compilation_level1_v2.json`: node-compilation SHA-256
  `9cb4a06438ef9c0922b78a19e90ea35682dca6f9ff9f21d7006f2aca384d2c3d`.
- `reconciliation_compilation_level2_v3.json`: terminal
  node-compilation SHA-256
  `3f96c08b44403747a1f4c6984035b5d0fb4cf4074f6c1a7544f53e3a6d7e8895`.
- `calibration_view_v4.json`: view SHA-256
  `3d9af1b55649faabfdd3d0f63750eeb0afeb3046509cb95f7d7ecddc978eeb9f`.
- `calibration_evidence_packet_sk_ii_holy_grail.json`: packet SHA-256
  `14a092219a60556ebf2ece2ddebab1a49ba44b8feab82426c77cce2b06bd4a78`.

## Residual boundary

- Full-corpus semantic judgment remains `0 / 513`; the bounded calibration is
  proof of the method, not a substitute for the full run.
- Source reconstruction and combined source materialization still take minutes
  because they reread and rehash the large pinned source artifacts. Bundle-v4
  packing itself completed in seconds; source-layer latency is separate work.
- Terminal reconciliation at full scale remains unproven. The single-terminal-
  batch gate and 150,000-byte ceiling remain unchanged and fail closed.
- Exact normalized public-handle matches can conservatively collapse cross-
  venue credit, but this Summer Fridays corpus contained no observed public
  handle spanning multiple scoped independence keys. The mechanism is tested,
  not live-demonstrated here.
- This shadow run and receipt are evidence-only and not seal-eligible.
