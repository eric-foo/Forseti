---
retrieval_header_version: 1
artifact_role: Summer Fridays customer-evidence cross-source semantic proof receipt
scope: Complete bounded Lip Butter Balm hydration/wear slice across Reddit and retailer reviews; evidence structuring only
use_when:
  - Auditing run-local product identity and Reddit-to-retailer evidence stacking.
  - Preparing the later full customer-corpus cold-agent run.
authority_boundary: evidence_only
open_next:
  - forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
  - docs/workflows/phase_a_customer_evidence_completion_path_v0.md
---

# Summer Fridays customer cross-source proof v0

## Observed result

The bounded no-provider run processed all 300 already-captured Summer Fridays
Lip Butter Balm leaves coded to hydration/moisture or wear/longevity. One
run-local stable identity joined the source-native product IDs used by Reddit
coding, Sephora, Amazon, and Revolve without changing their source roles or
provenance.

| Source family | Assessable leaves |
| --- | ---: |
| Reddit/community | 216 |
| Retailer reviews | 84 |
| **Total** | **300** |

The retailer union contains 75 Sephora `P455936` reviews, seven Amazon
`B0C42HJRBF` reviews, and two Revolve `SUMR-WU76` reviews. A `P455936`-only
filter would therefore have silently lost nine same-product reviews. The
stable binding corrected that loss without searching for new evidence.

Fifteen hydration/wear retailer rows on other product pages mentioned a lip
balm in their text but stayed outside the proof. Six were Dream Lip Oil
`P509439` reviews that explicitly compared with or mentioned Lip Butter Balm.
The page identity, not the mention, controlled selection. This is the live
wrong-product control.

## Semantic execution

Three cold workers processed five prompts with no provider API. Every one of
the 300 evidence aliases received exactly one disposition:

| Disposition | Count |
| --- | ---: |
| Claim-bearing | 254 |
| Context-only | 4 |
| Out-of-scope after semantic reading | 42 |
| **Accounted** | **300** |

The 254 claim-bearing leaves produced 576 distinct semantic units. Two
reconciliation levels produced a terminal 53-proposition view and preserved
477 non-equivalent semantic units as explicitly unmerged rather than forcing
them into broad summaries.

Eight terminal propositions contain both `community_post` and
`retailer_review` support and compile to `cross_venue_corroborated`. They
include bounded meanings about:

- hydration plus long wear across Reddit, Amazon, and Sephora;
- failure to hydrate or increased dryness;
- repeated application or short wear;
- hydration combined with a thick, plush, smooth, or comfortable texture;
- dryness together with irritation, peeling, chapping, soreness, or itching;
- value relative to performance or hype; and
- appealing scent.

These are retrieval labels, not conclusions. The run does not say how common
an experience is, which experience matters most, why sales moved, or what the
company should do.

The two-axis evidence packet selects 26 propositions and returns 55 linked
evidence items from 54 containers and 52 credited public origins. It also
reports 229 axis-relevant unmerged candidates and 248 unscoped unmerged
candidates. `truncated` is `false`; the smaller accepted evidence count is not
a top-k cutoff.

## Failure visibility

The first terminal compilation passed response validation but failed final
view compilation. Two customer-evidence nodes used claim kinds that their
source roles could not support:

- a community-plus-retailer layering routine was labeled `actor_strategy`;
- a retailer-review node was labeled `observable_fact`.

The failed response and terminal compilation remain in the external run. A
new corrected response moved both candidates to explicit unmerged status
because their upstream posture could not be honestly repaired at terminal
reconciliation. The corrected view then finalized. This is observed evidence
that source-role competence remains fail-closed after agent judgment.

## Exact lineage

Large artifacts are external under
`C:\tmp\forseti-phase-a-customer-cross-source-proof-20260809`.

- Source v3: internal SHA-256
  `540b5f9211a44da915ad32ea22f6f6e3c28f663dc783904c76683c15d2b3ee2f`;
  raw file SHA-256
  `3a950046e7902101d0973e83494f485f9ccdf984ee18f755c408d55055b942c2`.
- Bundle v4: bundle SHA-256
  `9cae1f69c2e9caaf5f1fc39e066a8f47e36bc6df04e982fdb2857530c7a43a9a`;
  corpus SHA-256
  `c8401724f37e30acbc845c2f997e59a1f21a6bdf615e6ed2924c9e10f0ff5082`;
  method SHA-256
  `bde2883c9f7c1ee25aee017711e72bdf0053fd98514da7c1566e56102406adb9`.
- Batch compilation: 576 semantic units; compilation SHA-256
  `5697f41230e9982649815332510df0956305796ad80b9cc76baa1aa7466ef222`.
- Level-one node compilation SHA-256:
  `49dc8facd13ffd2effbdc1dc47eafc526c541b8599611dd578d38369ab6c7a11`.
- Failed level-two node compilation SHA-256:
  `4b5cc35d1f03427afea993ca2cdaddead5342791ebe0de03ae4ff640f0e306ed`.
- Corrected level-two node compilation SHA-256:
  `2d2a9a61058a027d07e91439df0a8021b2778d7a564dec3ba36a138a2f597ef2`.
- Final view SHA-256:
  `e15daddf916bb77e2aee10b917307922c53eebc8e59cb343b0011c64c06e9435`.
- Two-axis evidence-packet SHA-256:
  `12272eeaa508d2706bee23ac9953850cb8c3886bd7e1c3d166ab0d7f1a1d9f44`.

A fresh source and bundle rebuild reproduced the same internal source, bundle,
and corpus hashes. All five prompts stayed under 150,000 rendered UTF-8 bytes;
the largest was 126,308 bytes. Model/provider API calls were zero.

## Boundary and next step

This is a complete bounded proof, not the full customer corpus and not a
seal-bearing method-v4 run. It does not replace the still-unfinished semantic
execution of all 59,225 assessable Summer Fridays customer leaves. The next
step is independent delegated code review and patch of this implementation.
Only after accepted home adjudication should a cold agent execute the full
corpus. Campaign evidence and any claim-to-customer-response comparison remain
the separate later path recorded in the completion-path document.
