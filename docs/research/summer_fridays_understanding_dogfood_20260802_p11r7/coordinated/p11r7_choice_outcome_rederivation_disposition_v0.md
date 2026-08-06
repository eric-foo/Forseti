# p11r7 Choice/Outcome Re-Derivation Disposition — 2026-08-06 v0

```yaml
retrieval_header_version: 1
artifact_role: Semantic-review and remediation disposition (durable gate record)
scope: >
  Durable disposition for the p11r7 semantic source review and its adjudicated
  remediation. This is the record the Deliver-phase Synthesize entry gate
  requires: it states what the review found, what the re-derivation changed,
  the adjudicated choice-field convention, and the corrected counterweight
  state a synthesis may rely on.
use_when:
  - Verifying the semantic-review disposition at Deliver Synthesize entry.
  - Interpreting choice/explicit_outcome values in community_axis_coding.json.
  - Auditing any claim built on p11r7 positive-counterweight evidence.
authority_boundary: retrieval_only
open_next:
  - docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/p11r7_disposition_log.csv
  - docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/turn_a_consumer_brand_v3_acquisition_record.md
  - docs/workflows/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/acquisition_seal.md
stale_if:
  - The community coding's choice/outcome fields are re-derived again.
  - The seal is re-cut for a reason other than this remediation.
```

## Chain of record

1. **Semantic source review** (2026-08-06, cross-vendor: Anthropic reviewer
   over OpenAI-authored artifacts): verdict `NEEDS_ARCHITECTURE_PASS` —
   systemic misattribution in `choice`/`explicit_outcome`: competitor events
   credited to the subject, negations coded positive, and outcome labels with
   no event in the raw body. 41 decision-bearing refs and 24 spot checks read
   against raw preserved bodies.
2. **Re-derivation** (2026-08-06, fresh Anthropic lane, distinct from the
   reviewer): all 355 outcome-bearing rows re-coded against raw bodies under
   the referent-binding rule; `comment_created_utc` backfilled on touched
   rows; 304/355 rows changed (dominated by demotion of event-free
   `alternative` codings). Per-row provenance: `p11r7_disposition_log.csv`.
3. **Adjudication** (commissioning Chief Architect): return accepted;
   spot-verified against raw; seal hash pins re-cut (see the seal's
   "Seal re-cut 2026-08-06" section); validator re-run to PASS.

## Adjudicated choice-field convention (binding for consumers)

- `subject` — the explicit choice stayed with a Summer Fridays product
  (retained / repurchased / recommended).
- `alternative` — the event's referent is a named non-SF product
  (`alternative_brand` set), whether adopting or rejecting it.
- `neither` — abandonment of a Summer Fridays product with no adopted named
  destination.
- `unstated` — no explicit purchase/retention/recommendation/abandonment act
  (paired with `explicit_outcome: none_explicit`).
Outcome verbs bind to their grammatical and semantic referent; negations code
as their negative counterpart; unresolvable referents carry
`parser_limitation` and never a guessed outcome.

## Corrected headline state (community corpus)

- Axis-expanded positive outcome rows 120 → 64; negative 134 → 141; net
  −14 → −77. `retained_or_repurchased` 85 → 38. Subject-choice threads
  54 → 24; alternative-choice threads 179 → 39 (event-free `alternative`
  codings demoted; all named competitor mentions retained as comparison
  evidence).
- Three axes (reaction, wear, formula consistency) have **zero** surviving
  subject-owned retention/repurchase/recommendation evidence; their ledger
  counterevidence entries say so and cite nothing.
- Comparison volume (`compares` 866), sharpening volume, axis assignments,
  and the 2,117 row×axis accounting are unchanged.

## Known boundaries

- Retailer-review coding (3,200 rows) and native-social coding were not
  re-derived; retailer positive-choice splits stand on their own corpus. A
  bounded retailer spot check is scoped into the confirming re-check.
- Event-free `alternative` rows were demoted, not re-hunted for previously
  uncoded competitor-owned events; a separate bounded pass may add those
  (understating competitor pull is the conservative direction).
- Two rows remain `parser_limitation` (unresolvable referents); one thread
  (`1sj7lf3`) has a thread-level subject error noted for corpus review.
- `evidence_text` excerpts were not re-derived; a few are stale relative to
  corrected codings (coding is authoritative; the disposition log carries the
  binding quotes).
