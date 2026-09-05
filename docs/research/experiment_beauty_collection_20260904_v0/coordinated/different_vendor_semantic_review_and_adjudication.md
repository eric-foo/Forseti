# Experiment Beauty — Different-Vendor Review and Adjudication

```yaml
retrieval_header_version: 1
artifact_role: Experiment Beauty case evidence — commissioned different-vendor review and Chief Architect adjudication
scope: Durable case-local record of the review findings, accepted patches, owner clarification, residuals, and acceptance boundary for the Experiment Beauty acquisition seal.
use_when:
  - Auditing why the Experiment Beauty acquisition evidence was accepted.
  - Checking which review findings were kept, closed, or retained as residuals.
authority_boundary: retrieval_only
open_next:
  - docs/workflows/experiment_beauty_understanding_20260905_v0/coordinated/acquisition_seal.md
  - forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
branch_or_commit: commissioned revision 8f9b2b76; settled pre-adjudication branch tip f0f8033e
```

## Review identity and boundary

- Subject: Experiment Beauty acquisition and material-saturation evidence.
- Authoring lineage: OpenAI / Codex.
- Reviewer lineage: Anthropic / Claude; exact model was not recorded.
- Access: direct repository and data-lake read access was reported and supported by the review's mechanical packet read-back.
- Reviewer verdict: `PASS_WITH_PATCHES`.
- Review transport: the complete return was couriered in chat. This record preserves the decision-relevant return and adjudication beside the case evidence so a future reader does not need the authoring conversation.

The reviewer verdict and patches were decision input, not acceptance. The Chief
Architect independently adjudicated the return against the settled branch.

## Adjudicated findings

### S1 — Accepted and kept

Two ingredient-hash evidence references did not name the preserved packet that
contained the underlying observation. The reviewer demonstrated that the bare
hashes did not occur in the 232 preserved source files and could not be
reproduced under the tested normalizations.

The accepted patch replaced them with three packet-anchored references because
one hash represented two distinct saved observations:

- `owned:01M1PDKQSY1C5DETG1G1WHGT96:ingredient_hash:485c6ae3cf1008cc78bf0afe0e8cf8ffcfe266ce1bc34654bacd6bcedbc16d94`
- `owned:01M1PDM2V1GYAAF9RZ03N1QB92:ingredient_hash:485c6ae3cf1008cc78bf0afe0e8cf8ffcfe266ce1bc34654bacd6bcedbc16d94`
- `owned:01M1PDKXF2X27X12M3WDKT1SG5:ingredient_hash:a1e4b8dac9a7d109c67b7a815d8ab999f195043daadef667924cb4c35ffa8dd4`

The provisional maturity scan was repinned to the changed axis inventory. This
closed source location without treating the two observations as two independent
origins.

### S2 — Accepted and closed by owner clarification

The Phase A workflow allowed acquisition-stage evidence work after a bounded
Capture handoff, while the Judgment contract said Evidence Consolidation starts
only from a completely accounted corpus after all selected acquisition jobs are
terminal. A cold reader could reasonably disagree about whether integration
could run before every possible later acquisition job was known.

The owner chose iterative snapshot semantics:

1. Preparatory consolidation may start after a bounded Capture handoff.
2. A complete integration pass may start only when every job selected for that
   pass is terminal and the current evidence snapshot is immutable and fully
   accounted.
3. If that pass exposes a material gap, only the affected acquisition work is
   selected.
4. Any changed evidence invalidates the prior integration, which is regenerated
   before sealing.
5. Only the final-corpus integration may support the acquisition seal; Deliver
   still requires that passing seal and a separate commission.

The owning Judgment contract is advanced to v115 and the Phase A completion
workflow now states the same boundary.

### S3 — Accepted and kept

Two workflow instructions wrongly attributed the machine-readable packet
inventory to the Capture obligation contract. The contract requires the
handoff to supply that inventory; it does not contain the inventory itself. The
accepted wording now points to the Capture handoff's inventory required by the
contract.

## Residuals retained without more patching

- The ingredient hashes locate the correct packets but their original text-normalization method remains undocumented. The packet anchors, not hash reproduction, carry source resolution.
- Google Ads and Meta inventories remain bounded captures; neither claims complete platform exhaustion.
- Reddit discovery-query provenance was not preserved, so the captured URL set does not prove search exhaustion. The case already discloses this ceiling.
- No new standing checker was added for the three case JSON artifacts. A future demonstrated stale-edit defect, rather than this one case, is the trigger to reconsider that recurring cost.
- The repo-map observation remains advisory because the existing case roots are directly discoverable and no live router claims a complete case index.

These residuals do not authorize prevalence, causation, medical-safety,
market-consensus, demand-volume, or Deliver claims.

## Review evidence retained

The returned review reported:

- exact receipt-to-inventory accounting over 100 packets: 98 current and 2 superseded;
- successful read-back of 232 preserved files totaling 18,241,029 bytes with no reported size or SHA-256 mismatch;
- exact match between all 13 consumer-brand evidence floors in the scan and the live validator;
- primary-byte verification of the retailer totals and the 717 readable Reddit post/comment rows;
- successful Capture checker self-test and receipt validation; and
- a clean 334-test run before a concurrent writer entered the tree.

The concurrent-writer condition is closed rather than inherited: after the
other work settled, the branch was clean and the current seal validator,
maturity-scan validator, focused tests, harness-coupling check, and branch-level
review-routing check all passed. Those checks establish their named mechanical
conditions only; semantic acceptance is the adjudication recorded above.

## Final disposition

`ACCEPTED_AFTER_PATCHES_AND_OWNER_CLARIFICATION`.

Experiment Beauty now joins Summer Fridays and Dieux as a preserved
consumer-brand evidence case using the existing repository pattern:

- source and research evidence under `docs/research/experiment_beauty_collection_20260904_v0/`;
- final Acquire & Seal state under `docs/workflows/experiment_beauty_understanding_20260905_v0/`.

This disposition closes Acquire & Seal only. Experiment Beauty Deliver has not
started.
