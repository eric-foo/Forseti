# Summer Fridays Intelligence Claim-Support Dogfood v0

```yaml
retrieval_header_version: 1
artifact_role: Research artifact (evidence-only claim-support dogfood)
scope: >
  Applies the owner-adopted intelligence claim-support contract to four
  previously discussed Summer Fridays propositions using preserved source-native
  records, provenance, actor state, timestamps, and engagement.
use_when:
  - Auditing how the shared claim-support contract changes the Summer Fridays competitive-choice examples.
  - Checking whether a Phase A axis finding should be isolated, directly observed, independently repeated, mixed, or causally unresolved.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/judgment/claim_support/forseti_intelligence_claim_support_contract_v0.md
  - docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/community_axis_coding.json
  - docs/research/summer_fridays_understanding_dogfood_20260802_p11r7/coordinated/evidence_depth_ledger.json
stale_if:
  - Any cited source-native record, actor, timestamp, engagement state, or formula/version binding is corrected.
  - The claim-support contract changes its support or conflict postures.
```

## Boundary and method

This is historical dogfood of four worked examples, not a corpus-wide
adjudication, current competitor verdict, market conclusion, sentiment estimate,
or premiumization recommendation. It freshly read the cited coded rows and their
preserved raw content records. The coded community rows retain thread/comment
provenance and excerpts but do not carry engagement; engagement below was read
from the source-native raw record named by the pinned manifest in the
evidence-depth ledger.

Only rows that actually assert the bounded proposition count. Broad axis totals
and regex-nominated rows do not corroborate a precise claim merely because they
share an axis label.

## Corpus context and selection receipt

The sealed Phase A corpus is much larger than the evidence refs in these four
examples: 577 source-native Reddit threads, 38,065 parsed comments, and 1,371
coded community rows across all 577 threads. The coded set contains 116 thread
bodies (`comment_id: post`) and 1,255 comments. The retailer lane separately
contains 3,200 eligible text reviews across Amazon, Revolve, and Sephora; the
native-social lane contains 36 posts from 23 creators. These counts describe the
available corpus, not support for any one proposition.

The examples below deliberately count only their cited, proposition-matched
units. They do not claim that the cited independent-origin count is the total
number of matching rows in the full corpus. A corpus-wide finding must screen
the whole coded candidate set, record admitted and excluded candidates with
reasons, include qualifying thread bodies, and reconcile retailer, creator,
editorial, owned, and ad lanes before assigning its final support posture.

## Claim 1 — Summer Fridays versus e.l.f. hydration is mixed

```yaml
claim_support:
  bounded_proposition: >
    Among captured Reddit authors directly comparing Summer Fridays Lip Butter
    Balm with e.l.f. lip balm, the reported hydration advantage is split.
  support_posture: independently_repeated
  independent_origin_count: 3
  source_roles: [reddit_community]
  evidence_refs:
    - 1t79b03/oq629l9
    - 1ktoo8j/mty6u0w
    - 1kq0492/mt2uibs
  engagement_evidence_refs:
    - 1t79b03/oq629l9: 0 points
    - 1ktoo8j/mty6u0w: 1 point
    - 1kq0492/mt2uibs: 2 points
  behavior_evidence_refs: []
  counterevidence_refs: [1kq0492/mt2uibs]
  conflict_posture: mixed
  scope_conditions:
    - Reddit only
    - exact formula/version not established
    - captured comments dated 2025-05-19 through 2026-06-06 UTC
    - independent_origin_count covers this cited worked-example set, not every corpus match
  causal_ceiling: descriptive_repeated_reports_only
```

Two distinct authors (`luxlisbon_`, 1 point; `friedstrawberryjam`, 0 points)
favored Summer Fridays on hydration. A third (`sashihmi`, 2 points) favored
e.l.f. and described Summer Fridays hydration as inconsistent. None of the three
items earns material resonance credit alone. Together they establish recurrence
and disagreement, so the only honest Phase A posture is
`split_or_conditional`. The zero-point comment is not discarded; it contributes
only because a separate author makes a similar comparison.

Selection receipt: the coded corpus contains six hydration-coded rows whose
text names both Summer Fridays and e.l.f.; three directly assert the exact
two-product hydration comparison and are cited here. The other three are a
generic category statement, a product-inventory fragment, and a broad lip-oil
roundup. None of the six is a thread body. The focal retailer corpus contains
hydration evidence but no exact Summer-Fridays-versus-e.l.f. hydration review.
The acquired creator comparisons cover package/formula similarity, texture,
shine, and price—not this hydration direction—so this example remains
Reddit-only rather than cross-venue corroborated.

Source URLs:

- `https://old.reddit.com/r/LipBalm/comments/1t79b03/the_gloss_report_summer_fridays_lip_butter_balm/`
- `https://old.reddit.com/r/drugstoreMUA/comments/1ktoo8j/review_elf_glow_reviver_melting_lip_balm/`
- `https://old.reddit.com/r/Sephora/comments/1kq0492/`

## Claim 2 — shorter wear versus Ole is repeated community evidence, not yet cross-venue

```yaml
claim_support:
  bounded_proposition: >
    Multiple captured Reddit authors report that Summer Fridays Lip Butter Balm
    requires more reapplication or wears for less time than Ole Henriksen Pout
    Preserve.
  support_posture: independently_repeated
  independent_origin_count: 3
  source_roles: [reddit_community]
  evidence_refs:
    - 13aw1sp/jjabq8d
    - 1nr7jxv/ngcm6wt
    - 1r09924/o4h7wba
  engagement_evidence_refs:
    - 13aw1sp/jjabq8d: 1 point
    - 1nr7jxv/ngcm6wt: 1 point
    - 1r09924/o4h7wba: 4 points
  behavior_evidence_refs:
    - 1r09924/o4h7wba: switched_or_replaced
  counterevidence_refs: []
  conflict_posture: none_observed
  scope_conditions:
    - Reddit only
    - comments span 2023-05-08 through 2026-02-09 UTC
    - exact formula/version continuity is not established
    - one 2023 row names Brown Sugar and Vanilla Beige; later rows are broader
    - independent_origin_count covers this cited worked-example set, not every corpus match
  causal_ceiling: descriptive_repeated_reports_only
```

This supports a repeated customer-language signal. It does not prove the
current formula objectively has weak longevity, that every variant behaves the
same way, or that shorter wear causes a purchase decision. The retailer coding
contains brand-wide wear/longevity incidence, but the aggregate does not bind
the same exact Summer Fridays-versus-Ole proposition, product version, or
direction. It therefore does not earn cross-venue credit here. A future
retailer-review or competent editorial comparison must be read at source and
matched to this proposition before promotion.

Selection receipt: a broader text screen finds ten wear-coded community rows
that name Summer Fridays and Ole Henriksen, including one thread body and nine
comments. This worked example adjudicates three of them; it is not an exhaustive
origin count. Several remaining rows are directionally relevant and require a
full proposition pass, while others mention only Ole wear, compare a different
Summer Fridays product, or make the wear comparison against another brand. The
focal retailer corpus contains 184 wear/longevity mentions (8 Amazon, 6 Revolve,
170 Sephora), but no captured review binds the exact Summer-Fridays-versus-Ole
product, direction, and formula/time proposition. No acquired creator or
editorial unit was found that closes that exact comparison.

Source URLs:

- `https://old.reddit.com/r/Sephora/comments/13aw1sp/summer_fridays_lip_balm/`
- `https://old.reddit.com/r/Sephora/comments/1nr7jxv/help_a_girl_out_which_lip_formula_reigns_supreme/`
- `https://old.reddit.com/r/LipBalm/comments/1r09924/ole_v_summer_fridays/`

## Claim 3 — flavor causing continued purchase remains isolated and unresolved

```yaml
claim_support:
  bounded_proposition: >
    Flavor causes customers to continue buying Summer Fridays despite shorter
    wear.
  support_posture: isolated
  independent_origin_count: 1
  source_roles: [reddit_community]
  evidence_refs: [1tjqlg0/oncgsqu]
  engagement_evidence_refs:
    - 1tjqlg0/oncgsqu: 1 point
  behavior_evidence_refs:
    - 1tjqlg0/oncgsqu: stated continued buying
  counterevidence_refs: []
  conflict_posture: not_checked
  scope_conditions:
    - one Reddit author
    - statement bundles flavors and older formulas
    - exact formula/version and object of the pronoun "they" remain unresolved
  causal_ceiling: bundled_single_actor_self_attribution_causal_not_established
```

The author mentioned loving both flavors and older formulas, then mentioned
shorter wear and continued buying. The source does not isolate which factor
explains the behavior. One low-engagement bundled statement cannot support an
emotional-value, repurchase-driver, or premium-permission finding. Promotion
would require multiple independent explicit attributions that separate flavor
from formula nostalgia and other plausible reasons; cross-venue recurrence
would strengthen the reported-motivation claim but still would not prove
population-level causation.

The wider corpus is not empty on adjacent propositions. Eight Lip Butter Balm
community rows combine scent/flavor with an explicit positive purchase or
retention outcome. One (`197e9bf/ki1lc96`) explicitly says the author would skip
an unscented lip oil and repurchase the scented balm, but it does not include the
shorter-wear condition in this bounded proposition. A coded thread body
(`1i2oqpt/post`) praises the smell but says the product did not nourish and was
being panned before moving to Ole Henriksen. Revolve review `812944380` says the
Birthday Duo smells sweet, has good texture, and would be repurchased; it bundles
scent with texture and likewise says nothing about shorter wear. These sources
are adjacent evidence, not corroboration of the exact causal trade-off claimed
here.

Source URL:

- `https://old.reddit.com/r/LipBalm/comments/1tjqlg0/lets_chat_3_whats_your_biggest_problem_with_lip/`

## Claim 4 — observed sticker price is a bounded direct fact

```yaml
claim_support:
  bounded_proposition: >
    At the p11 US observation cutoff, e.l.f. Glow Reviver Melting Lip Balm had a
    lower sticker price than Summer Fridays Lip Butter Balm.
  support_posture: directly_observed
  independent_origin_count: 2
  source_roles: [owned_source, retailer_product]
  evidence_refs:
    - 01KYWMC8ZSWS6K6ZRZR3VVERWA#organic:4
    - 01KYWMN6SF5QAM2QJ1HT9120T9#organic:5
    - 01KYWMN6SF5QAM2QJ1HT9120T9#organic:6
  engagement_evidence_refs: []
  behavior_evidence_refs: []
  counterevidence_refs: []
  conflict_posture: none_observed
  scope_conditions:
    - Summer Fridays USD 24 for 15 g
    - e.l.f. USD 9 for 0.52 oz
    - US observation cutoff only
    - size units remain not directly normalized in the cited run
  causal_ceiling: descriptive_only
```

This claim does not need customer likes or repeated testimony because the dated
prices are the directly observed facts. It supports a lower observed sticker
price, not superior value, willingness to switch, market positioning, margin,
or premium permission.

The first packet was captured on 2026-07-31 at 17:43:29 UTC and preserves the
Summer Fridays official Lip Butter Balm result showing 15 g / 0.5 oz and USD 24.
The second was captured at 17:48:22 UTC and preserves an e.l.f. official result
showing USD 9 plus a Target result binding USD 9 to the 0.52 oz product. These
packet-row refs replace the earlier unresolved `sf-pdp` / `elf-pdp` aliases.

## Dogfood verdict

The contract changes the prior interpretation in four material ways:

1. The zero-point e.l.f. comment no longer carries a premium or general
   hydration conclusion; only independent recurrence keeps it relevant, and the
   recurrence is visibly mixed.
2. Ole longevity remains a real repeated community signal, but loses any claim
   to current-formula certainty or cross-venue corroboration until exact
   retailer/editorial evidence is adjudicated.
3. Flavor-driven continued purchase is rejected as a finding and retained as
   one unresolved hypothesis-bearing observation.
4. Direct price observation remains usable without forcing testimonial
   corroboration onto a fact the source directly exposes.

The dogfood also exposes a concrete workflow requirement: synthesized claims
must resolve coded rows back to source-native engagement and provenance. Broad
axis counts remain useful for discovery and maturity, but they cannot substitute
for proposition-specific adjudication.

## Non-claims

- not representative sentiment or prevalence;
- not a current-formula verdict;
- not a competitor ranking;
- not a causal finding;
- not a premiumization, pricing, product, campaign, or Deliver recommendation;
- not proof that the captured actor identities are globally unique;
- not validation of every coded row in the historical corpus.
