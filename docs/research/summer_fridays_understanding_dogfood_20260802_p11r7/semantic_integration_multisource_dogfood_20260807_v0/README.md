---
artifact_type: phase_a_semantic_integration_multisource_dogfood
authority: forseti/product/spines/judgment/claim_support/forseti_semantic_evidence_integration_contract_v0.md
status: completed_bounded_dogfood
current_as_of: 2026-08-07
scope: all 80 already-captured Lip Butter Balm reaction-axis candidates across Reddit, Sephora reviews, one TikTok creator post, and its captured 20-of-77 audience-comment envelope
---

# Phase A Multi-Source Semantic Integration Dogfood

## Question

Can the semantic integration layer screen every already-captured candidate for
one real Summer Fridays question, stack meaning-equivalent evidence across
source roles, retain counterevidence and variant differences, and refuse false
independence or source-role credit without a model-provider API?

The bounded subject is public customer language about burning, irritation,
dryness, peeling, rash, itching, or related adverse reactions after using
Summer Fridays Lip Butter Balm. This is evidence structuring, not a safety
finding, prevalence estimate, diagnosis, causal conclusion, recommendation, or
new acquisition run.

## Declared denominator

The dogfood admitted the complete candidate slice already identified by the
upstream evidence work:

| Source family | Admitted units | Selection boundary |
| --- | ---: | --- |
| Reddit/community | 50 | Every Lip Butter Balm row coded to `reaction_and_breakout` in the p11r7 community coding artifact |
| Sephora retailer reviews | 9 | Every P455936 row coded to `reaction_and_breakout` in the p11r5 retailer coding artifact |
| TikTok creator post | 1 | The captured creator post that framed the Vanilla Beige burning question |
| TikTok audience comments | 20 | Every captured comment in the observed 20-of-77 comment envelope |
| **Total** | **80** | No candidate inside this declared slice was omitted |

`source.json` pins 55 source artifacts: the two upstream coding artifacts, the
50 source-native Reddit records, two Sephora review captures, and the TikTok
post/comment capture. Each admitted unit retains its exact text, stable source
identifier, actor identity when visible, publication time, raw engagement,
product binding, source role, and independent-origin key.

This denominator proves integration of the existing coded slice. It does not
prove that upstream acquisition or axis coding found every relevant statement
among all 577 captured Reddit threads or 3,200 eligible retailer reviews.

## Observed run

The no-provider file workflow completed against the patched semantic-
integration implementation:

- 80 evidence units were admitted and 80 were accounted for.
- 45 were `claim_bearing`.
- 14 were `context_only` questions, hearsay, hypotheses, or related material
  that could not support the bounded customer-experience claim.
- 21 were `out_of_scope`, including competitor reactions, wrong-product
  statements, inventories without an experience, and false-positive wording
  such as a perfume named “Burning Cherry” or a figurative “burning pit.”
- The 45 claim-bearing items produced 62 distinct semantic units.
- Reconciliation produced 17 bounded propositions and retained five
  unmerged causal or echo units.
- Bundle SHA-256:
  `013851d703f6f721223dc1621837d1030b172c8beea6677c4a9491253842f9a5`.
- Compilation SHA-256:
  `b7c9571b1cbb807ba0971225cf971974b2edb3e080cdf77b007f9b180c046990`.
- View SHA-256:
  `74305933581f2c032250877ace32cbe8652c1e511f79f4088da3528248b3fcd5`.
- Model-provider API calls: `0`.

## What evidence stacking produced

The broad, nonrepresentative proposition retained both directions:

> Across the captured Reddit, Sephora-review, and TikTok-audience evidence,
> customers report several kinds of adverse Lip Butter Balm experience, while
> other captured customers explicitly report tolerance or no comparable
> reaction.

Its compiled support block contains:

- `cross_venue_corroborated` posture;
- 37 independently credited supporting origins;
- customer-experience support from `community_post`, `retailer_review`, and
  `audience_comment` roles;
- seven counterevidence records;
- `mixed` conflict posture; and
- nine engagement-bearing support records.

This is the evidence-stacking behavior the earlier two-comment dogfood could
not demonstrate. It does not mean “37 people prove the product is unsafe.” It
means the same bounded adverse-experience class recurred across 37 visible
origins inside this selected public corpus, with contrary experiences retained
beside it.

The more exact propositions remained separate:

| Bounded point | Observed support |
| --- | --- |
| Burning experience is mixed | 15 supporting origins across three customer roles, five counterevidence records, `mixed` |
| Vanilla Beige adverse reports | 7 supporting origins across Sephora reviews and TikTok audience comments; creator post retained only as adjacent framing |
| Pink Sugar experience is mixed | 3 supporting origins across retailer and audience roles, 2 counterevidence records |
| Iced Coffee experience is mixed | 2 supporting origins across Reddit and retailer reviews, 1 TikTok audience counterexample |
| Brown Sugar adverse reports | 3 independent TikTok audience origins; one venue only |
| Adverse effects emerging with time/use | 6 supporting origins across Reddit, retailer, and TikTok audience roles |
| Customer behavior after an adverse experience | 9 supporting origins across Reddit and retailer reviews reporting stopping, returning, discarding, declining repurchase/recommendation, switching preference, or clearing a collection |
| Explicit tolerance/no comparable reaction | 7 supporting records but 6 independent origins because two Reddit records came from the same visible author |

## Concrete provenance examples

- Reddit `1mzokbt:post`, author `purplepeas18`, 2 observed points: reports
  Mint-variant burning, dryness, and flaking after several weeks, followed by
  stopping use. The continuing-sensitivity statement remains separately
  bounded with causation not established.
- Reddit `1qxm1tz:o3xko68`, author `kelhar417`, 3 observed points: reports
  severe drying under daily use and more than a week for recovery.
- Sephora review `187419902`, visible AuthorId `1792047916`, Vanilla Beige,
  non-incentivized, 22 positive of 25 feedback votes: reports warmth/burning
  and no future purchase. Its formula-change attribution is preserved but not
  promoted into a verified formula fact.
- Sephora review `272258322`, visible AuthorId `43532478387`, Vanilla Beige,
  non-incentivized, 30 positive of 36 feedback votes: reports peeling,
  swelling, pain, and stopping use, while explicitly allowing that the
  reaction may be individual.
- TikTok audience comment `7381650580382679851`, visible account
  `bernstein_stella`, 288 observed diggs: directly reports the same Vanilla
  Beige-specific experience.
- TikTok audience comment `7381753285764956946`, visible account `vi.3252`, 1
  observed digg: reports using one Pink Sugar tube over a year and most of a
  second without the discussed reaction. It remains counterevidence despite
  lower resonance.
- Reddit `1kq0492:mt21uxw` and `1m07jmq:n37cif6` are both authored by
  `nessa_14`. Both records remain visible, but together receive one
  independent-origin credit rather than two.
- TikTok video `7381649202134207786`, creator `marinabarnoo`, 4,090 observed
  diggs: establishes materially resonant creator framing. It is never counted
  as customer-experience support; its captured audience comments are assessed
  separately by visible account.

## Evidence deliberately not promoted

Five meaning units remain visible but unmerged:

- stevia as a proposed cause;
- shea butter as a proposed cause;
- a claimed new-formula explanation that was not independently verified;
- a question about whether the formula changed; and
- a Sephora reviewer’s reference to similar TikTok reports, treated as an
  echo rather than another independent source.

Engagement materiality is a dogfood-specific, conservative judgment with the
raw metric and context preserved. No universal Reddit, Sephora, or TikTok
threshold is installed. Likes, points, helpful votes, and diggs can support
resonance; they never become additional independent experiences.

## Validation

Observed checks against the patched implementation:

- exact deterministic rebuild of bundle, compilation, and view;
- all 80 aliases accounted for exactly once;
- focused semantic-integration and acquisition-seal tests pass;
- removing one admitted alias fails with
  `does not account for every alias exactly once`;
- changing the creator post from adjacent framing to customer-experience
  support fails with `creator_authored` incompetent for
  `customer_experience`;
- altering bundle content without recomputing its stored hash fails with
  `content does not match its stored bundle_sha256`; and
- the repeated `nessa_14` records produce six independent origins from seven
  tolerance-support records.

The durable agent judgments are `batch_response_0001.json`,
`batch_response_0002.json`, and `reconciliation_response.json`. The admitted
evidence and final compiler-owned result are `source.json` and `view.json`.
