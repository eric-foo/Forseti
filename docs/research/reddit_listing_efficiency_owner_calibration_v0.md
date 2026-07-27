# Reddit Listing-Efficiency Owner Calibration v0

```yaml
retrieval_header_version: 1
artifact_role: Research artifact
scope: Owner-calibrated rules for choosing which captured Reddit listings deserve scarce deep-read capacity for commissioned company intelligence.
use_when:
  - Ranking captured Reddit threads before opening their post bodies or comments.
  - Distinguishing general deep-read admission from commission-specific retrieval.
  - Designing a holdout test for Reddit listing-selection efficiency.
authority_boundary: retrieval_only
```

## Status and boundary

- Calibration date: 2026-07-28.
- Owner-calibration state: 30 pairs completed; 60 threads across 39
  subreddits; every thread has an independent `yes`, `borderline`, or `no`
  dive-admission label.
- Admission distribution: 17 `yes`, 5 `borderline`, and 38 `no`; pairwise
  pre-dive outcomes were 9 Left, 7 Right, and 14 neither.
- Additional source checks: four captured-corpus source audits plus one
  transaction-thread-type audit.
- This is an evidence-backed research conclusion, not runtime implementation,
  production readiness, or product authority. Its listing-selection rules were
  subsequently stress-tested on the blind 100-thread sample recorded in
  `docs/research/reddit_listing_efficiency_holdout_100_v0.md`.
- The missing original handoff
  `docs/hygiene/reddit_listing_efficiency_validation_handoff.md` could not be
  recovered from the commissioned worktree at closeout. This record therefore
  stays inside the owner-calibration lane established in the active owner
  conversation. It does not authorize edits to the runtime ranker, subreddit
  registry, Capture, Cleaning, Judgment, or Deliver.

### Inputs freshly confirmed

| Input | Location | SHA-256 |
| --- | --- | --- |
| Completed owner labels and post-label audits | `C:\tmp\forseti_tower28_clinique_phase_a_20260728\owner_predive_clean_round_v1.json` | `338913dec6c63a407bdbb7797d1a611840f8bf084dd2d127fad841e44bcb0c88` |
| Canonical captured-thread manifest | `C:\tmp\forseti_reddit_listing_validation_full_corpus_20260727\canonical_packet_manifest_5470.json` | `289ee06d3e4f8feb96540feafe375ae7333c2f3030d884fd28c801583d44027f` |

The evidence is captured-corpus evidence only. No live Reddit completeness,
currentness, or monitoring claim is made.

## The decision being calibrated

The model is not choosing the most interesting, popular, or information-rich
Reddit post. It is choosing where to spend scarce deep-read capacity.

**Value means expected contribution to a commissioned company decision per
deep-read unit.**

A thread contributes when its evidence could materially sharpen at least one
of these:

1. a customer problem, tradeoff, unmet need, or use context;
2. a competitor strength, weakness, substitute, switching reason, or claim gap;
3. product, positioning, message, price, access, distribution, or channel
   choices;
4. adoption, abandonment, repeat purchase, willingness to pay, or purchase
   friction;
5. brand trust, creator association, reputation, or an objection that affects
   purchase.

The current default customer is a scaling challenger trying to gain share or
position itself against named competitors. Retail-operator, pharmaceutical,
clinical-treatment, formulation-R&D, resale, or professional-service evidence
has no standing bonus; it activates only when the commission includes that
decision.

Reddit is one source, not the product. Forseti's value comes from connecting a
Reddit signal to the commissioned company, competitors, products, creators,
claims, prices, channels, partnerships, and independent evidence, then
corroborating what survives. A lone thread is a lead or evidence fragment, not
a client conclusion.

## Smallest complete selection policy

Apply these gates in order. Do not collapse them into one additive score.

### Gate 0 — General-scan discussion floor

Return `no` for the general deep-read queue when captured listing comments are
`0`, `1`, `2`, or `3`.

This is a dive-budget cutoff, not deletion. Preserve the thread in retrieval so
a later direct brand, competitor, category, issue, or geography commission can
deliberately recover it.

Do not coerce missing or unknown engagement to zero. Route missing engagement
as missing data. Use the freshest available captured engagement snapshot before
ranking; captured counts can drift materially.

The 100-thread holdout falsified captured score `0` as a universal cutoff:
seven of 20 sampled zero-score threads justified a general dive, including one
whose top comment scored 56. Post score can raise or lower priority after the
other gates, but it cannot veto a commercially promising discussion.

The same holdout found one exception among 20 sampled threads below the comment
floor: a zero-comment Project Pan post contained five completed-use reviews in
its body. Keep the floor because the general queue is buying independent
discussion, but name the poster-only case as an accepted residual. Recover it
when a direct commission retrieves the thread or cheap listing-visible context
already exposes a structured completed-use review. Do not silently claim that
the floor captures every useful post.

A follow-up test explicitly tried extending this rule to `0–4`. Thirty fresh
exactly-four-comment listings were mechanically frozen as `no` before deep
audit. The candidate floor caused nine material false negatives, correctly
suppressed 14, preserved six narrower-commission misses, and prevented one
clearly low-yield dive. The proposed extension is therefore rejected:
**four-comment threads remain eligible for the other gates.** The evidence and
examples are recorded in
`docs/research/reddit_listing_efficiency_holdout_100_v0.md`.

### Gate 0.5 — Listing-context sufficiency

Before applying the commercial gates, ask whether the listing projection shows
the object needed to interpret its claim.

- A deictic title such as “this” or “which one,” a visual punchline, an
  image-only comparison, or a crosspost payload mismatch is not enough for a
  confident product-level `yes` or `no`.
- Use an `insufficient_listing_context` or bounded `borderline` route when the
  missing context could change admission.
- Consume media presence/count and cheap linked-product, OCR, or alt context
  when already available. Do not open hidden discussion merely to repair the
  pre-dive projection.

This prevents both confident suppression of a hidden purchase decision and
confident admission of a visual joke mistaken for product failure.

### Gate 1 — Commission applicability

Ask whether the visible listing could change an in-scope decision for the
current commission.

- If **yes**, continue.
- If the connection exists only for a narrower future commission, suppress it
  from the general dive queue but preserve it for retrieval.
- If no plausible commercial decision is visible, return `no`.

Applicability gates engagement and specificity. A highly engaged retailer-app
complaint remains irrelevant when retailer operations and that channel are out
of scope. A technically specific medical-treatment thread remains irrelevant
to a general beauty-product commission.

### Gate 2 — Visible decision promise

Prefer listings that visibly promise one or more of:

- a named-product failure, disappointment, review, or performance claim;
- a recommendation, comparison, substitute, dupe, or ranked choice;
- a defined user, condition, constraint, product type, and requested outcome;
- a time-bounded outcome with a regimen or intervention likely to be disclosed;
- price, access, availability, purchase, repurchase, discontinuation, refund,
  or switching evidence;
- a product or category tradeoff that could affect positioning;
- a verified creator-to-brand or entity-to-company connection with observable
  trust or purchase consequences.

Strong verbs such as “disappointed,” “obsessed,” “worth it,” “stopped using,”
or “worked” increase priority only when a product/category and current
commercial decision are also visible.

A direct replacement request for a discontinued named product is a strong
decision promise even at modest engagement once it clears Gate 0. It can expose
substitutes, switching constraints, sampling behaviour, and unmet demand.

### Gate 3 — Objective suppression

Suppress by default when the visible objective is:

- appearance validation, colour voting, character comparison, or generic
  aesthetic praise;
- a generic showcase with no product, purchase, performance, usage, pricing,
  or market-learning hook;
- diagnosis, procedure cadence, or clinical-treatment advice outside a matching
  commission; do not apply this suppression to a purchasable product or
  consumer-device experience merely because the use condition is medically
  adjacent;
- personal, political, or creator gossip without a verified commercial link;
- technique-only help with no likely product-usability, failure, cost, or
  substitution evidence;
- a transaction listing whose comments record sale administration;
- retailer operations, promotions, or distribution outside the commissioned
  decision;
- specialist DIY formulation troubleshooting outside a formulation, sourcing,
  manufacturing, or product-development commission.

High score or comment count cannot rescue the wrong objective.

### Gate 4 — Engagement as expected-yield evidence

Engagement is required, but its two visible components mean different things.

- **Comment count** is the better pre-dive proxy for evidence depth,
  alternatives, disagreement, and corroboration.
- **Post score** is the better proxy for resonance with the visible post,
  outcome, concept, or image, but a captured zero does not establish absence of
  discussion value.
- High score with relatively little discussion often means visual appreciation,
  not product evidence.
- High discussion relative to score often predicts causal debate or problem
  complexity, but does not guarantee brand criticism or product value.
- Author replies, bot messages, transaction updates, and nested praise can
  inflate the apparent discussion. Inspect independent voices after admission.
- Listing counts are captured-state evidence, not immutable totals. Prefer the
  freshest available capture before ranking.

After Gate 0, there is no second universal numeric cutoff yet. In this
calibration, admitted threads included a 6-score/10-comment request, while
rejected threads included 960-score/310-comment, 663-score/27-comment, and
189-score/141-comment posts. Commercial objective and commission fit explain
those decisions.

Low engagement is nevertheless a strong default suppressor. A specific but
weakly discussed thread stays searchable for a direct brand/category
commission; it does not consume general deep-read capacity. An exception
requires unusually strong decision content in the listing itself, such as a
clear displacement claim or tightly defined buyer/problem/product request.

### Gate 5 — Source and format prior

Apply a source or format prior only where captured evidence supports one. Do
not infer a subreddit-wide policy from one pair.

- A poor-base-rate source raises the evidence needed for admission.
- A useful-tail source keeps strict topic and engagement gates rather than being
  removed.
- A structured recurring format can be useful even when the post score is low
  if it reliably elicits named current-use reports.
- Opaque community terms must be normalized before suppression; unfamiliarity
  is not evidence of low value.

### Gate 6 — Admission and priority

Assign admission independently to each thread:

- `yes`: expected current-decision contribution justifies a scarce deep read;
- `borderline`: plausible current contribution, but important uncertainty
  remains about applicability, product content, or evidence depth;
- `no`: insufficient expected current contribution.

Then rank only admitted threads. Pairwise preference never substitutes for
admission. If neither thread is admitted, the operational pair result is `N`
even when one is relatively better.

Within the admitted set, prioritize:

1. direct current-commission applicability;
2. explicit product/category decision promise;
3. likely evidence depth and independent corroboration;
4. specificity of problem, user, constraint, and outcome;
5. likely competitor, switching, price, access, or positioning contribution;
6. lower interpretation and safety burden.

## Thread-archetype rules

| Archetype | Default | Admit or raise priority when | Suppress or lower priority when |
| --- | --- | --- | --- |
| Named-product failure or disappointment | High | Meaningful discussion can expose mechanisms, disagreement, substitutes, non-repurchase, or expectation gaps | Very low engagement, clinical-only scope, or no current commission fit |
| Category recommendation or “what worked?” | High | User/problem/product type and constraints are specific; comments can form a weighted product map | Request is broad, weakly engaged, or outside a purchasable decision |
| Comparison, substitute, dupe, or worth-it question | High to conditional | Competitors, price tiers, performance, abandonment, or cheaper workarounds are likely | Low discussion or category is outside the commission |
| Discontinued-product replacement | High once Gate 0 is cleared | A named discontinued product and replacement need expose substitutes, constraints, sampling, unmet demand, or a brand roadmap signal | The named product/category is outside the commission |
| Routine, regimen, or progress | Conditional | Named interventions, a time window, disclosed stack, failure, adherence, or likely tradeoffs are visible | Appearance-only result, empty post, praise-only comments, or no attribution route |
| Empties, Project Pan, hit-pan, or finish challenges | Conditional | Full use, repurchase/non-repurchase, consumption rate, substitution, or regret can be recovered | Progress is merely aesthetic or no product decision can be inferred |
| Collection, favourites, current-use, or scent-of-the-day | Conditional | Engagement is sufficient to expose ownership, favourites, gaps, occasions, usage, scarcity, duplicates, or purchase behaviour | Low-comment collection praise or a list with no decision context |
| Showcase, FOTD, manicure, or before-and-after | Suppress by default | High engagement plus a likely disclosed product stack, performance question, purchase context, or commissioned visual-trend need makes a bounded gamble rational | Praise dominates; the result cannot be attributed; no product or market-learning hook is visible |
| Technique or application problem | Conditional | It can expose product incompatibility, usability, expectation, education, or brand-specific technique | It asks only for steps and lacks product, failure, cost, or commissioned category relevance |
| Creator or reputation topic | Cross-stitch first | A verified creator-brand relationship and trust, boycott, lost-purchase, sponsorship, or campaign consequence are material | Gossip, personal controversy, or politics has no verified commercial consequence |
| Availability, price, promotion, retailer, or service | Commission-conditional | The client decision includes distribution, channel, threshold, access, refund, salon/service, or promotion strategy | Current commission is general product CI and the operational issue cannot change it |
| Medical or diagnosis thread | Suppress by default | A matching pharmaceutical/treatment commission explicitly accepts the safety and corroboration burden | General beauty CI, crowd diagnosis, procedure cadence, or sparse anecdotes |
| Consumer health-adjacent product or device experience | Conditional | Purchasable products/devices, duration, comparative outcomes, abandonment, failure, or user-fit tradeoffs can change a commissioned product decision | The thread is primarily diagnosis/treatment advice, lacks a purchasable object, or cannot meet the higher safety/corroboration burden |
| WTS, resale, or swap listing | Suppress | Commission concerns resale price, scarcity, grey market, discontinuation, secondary demand, or channel leakage | Comments are chat requests, sale status, verification, splits, or shipping |

### Community-language normalization

Resolve common formats before applying the table:

- `FOTD`: face-of-the-day showcase; often carries a product stack.
- `PBE mani`: Polish & Beauty Expo manicure; may imply expo purchase,
  scarcity, and an exact stack.
- `Project Pan`: intentional use-down project.
- `hit pan`: enough use to expose the pan; partial-consumption evidence.
- `finish`: complete use; stronger consumption evidence than hit pan, though
  repurchase still must be observed.
- `10 by fall`: a time-bounded challenge to finish or substantially use ten
  products.
- `SOTD`: scent of the day; a structured current-use format.

These meanings remove avoidable false negatives. They do not create automatic
admission.

## Source-specific policies supported by this corpus

### r/NailArt — heavily suppress, do not remove

In the captured corpus, 92 of 99 retained threads were showcase-like. Admit
only explicit product/performance failure, named material/tool/brand comparison,
business or pricing questions, durability/removal/allergy/application problems,
or commissioned visual-trend evidence. Generic artwork, beginner progress, and
praise-only seasonal posts stay suppressed.

### r/DIYBeauty — heavily suppress, do not remove

The 11 retained threads had median score 1 and median comments 5 and were
dominated by hobbyist formulation troubleshooting. Admit commercial-product
replication failures, material sourcing/price/minimum-quantity constraints,
strong recurring formulation failures relevant to a claim, or an explicit
R&D/manufacturing commission.

### r/HairDye — retain with strict topic and engagement gates

The 95 retained threads had median score 7 and median comments 5, but the useful
tail repeatedly produced brand recommendations, fade/durability evidence,
named-product failure, box-dye versus semi-permanent tradeoffs, salon
miscommunication/refunds, price barriers, and colour-correction constraints.
Suppress appearance voting, undisclosed before-and-after showcases, and
low-comment technique questions.

### r/BeautyGuruChatter — retain; cross-stitch entities before gating

Nine of 15 captured threads were commercially substantive and two were
commission-conditional. Admit product, launch, collaboration, sponsorship,
dupe, pricing, distribution, formulation, advertising, regulatory, or purchase
topics. A creator controversy becomes commercially material only after a
reliable creator-to-brand link and observable trust or purchase consequence are
established.

### Other subreddits

No standing subreddit-wide policy was established. Apply the general gates.
The RedditLaqueristas examples show that showcases are usually weak but
high-engagement collection or product-stack posts can expose purchase,
scarcity, duplicate-avoidance, storage, and willingness-to-pay evidence. That
is a format finding, not a completed source audit.

## Cross-stitching and corroboration contract

### Before the deep-read decision

Listing selection may use:

- title, subreddit, flair, captured score, and captured comment count;
- the commissioned decision frame and competitor/category map;
- known entity relationships such as creator-to-brand, brand ownership,
  partnership, product category, or recurring community-format meaning.

This enrichment must happen before suppression. Otherwise an opaque creator,
acronym, or community format can be incorrectly discarded. It must not use the
hidden post body or comments before the pre-dive label is frozen.

### After admission

Deep reading should separate:

- the original poster from independent commenters;
- top-level agreement from author acknowledgements and nested repetition;
- whole-post resonance from product-level causality;
- named-product mention from actual preference, performance, purchase, or
  switching evidence;
- one-thread evidence from recurrence across independent threads and sources.

A post score can corroborate resonance with a disclosed multi-product regimen
or result, but it cannot attribute the outcome to one product in the stack.
Likewise, a highly upvoted comment that ratios the poster can outweigh the
poster's interpretation, but only as community evidence—not ground truth.

Before Deliver, connect surviving claims to material external evidence that
could change the decision: official product claims, prices, launches,
availability, partnerships, creator relationships, retailer/channel facts,
independent reviews, and recurrence in other communities. “Every material
source” means every source whose evidence could change the decision, not every
available source.

## Deep-audit lessons

Twenty-seven of 30 pairwise pre-dive outcomes matched the post-dive pair result.
This is diagnostic only, not an accuracy claim or holdout result.

The three differences identify the main residuals:

1. `C03`: neither thread deserved admission, although the relatively preferred
   thread contained some post-dive value. Useful hidden content does not
   retroactively justify an inefficient dive.
2. `C09`: a creator-to-brand relationship changed the commercial meaning.
   Entity cross-stitching is required before the listing gate.
3. `C30`: the lower-engagement thread contained more product detail after
   reading, but remained too weak and medically adjacent for general admission.
   Occasional low-engagement yield is an accepted miss when optimizing total
   value per dive.

Other recurring lessons:

- high engagement validates the visible objective; it does not replace it;
- top comments and independent-voice count matter more than raw comment count
  after diving;
- a hidden product list in a showcase can be useful without making showcases a
  high-base-rate source;
- commission mismatch can make rich evidence worth zero now while preserving
  it for later retrieval;
- title specificity without engagement is usually insufficient;
- engagement without a commercially relevant objective is also insufficient.

### 100-thread holdout corrections

The subsequent blind holdout is recorded in
`docs/research/reddit_listing_efficiency_holdout_100_v0.md`. Its decisive
corrections are incorporated above:

- captured score `0` is not a universal veto;
- the `0–3` comment floor remains a general budget rule with an explicit
  poster-only completed-use residual;
- a tested `0–4` extension is rejected because it lost nine valuable threads
  while preventing one low-yield dive in a fresh 30-thread boundary probe;
- opaque and media-dependent listings require a context-sufficiency state;
- discontinued-product replacement and consumer-device experience need
  narrower, commercially truthful treatment;
- fresh captured engagement should replace stale listing counts before
  ranking.

In the stratified stress set, 18 of 20 confident `yes` labels yielded
decision-bearing evidence. That observed result is not a corpus-wide precision
estimate.

## Downstream Deliver note

When a problem recurs across independent sources and is relevant to the
commission, Deliver may identify it as both customer-language evidence and a
transparent community-participation opportunity. A client may answer helpfully
where community rules allow.

Guards:

- do not manufacture questions, seed disguised advocacy, impersonate
  customers, or describe the practice as engagement farming;
- disclose material affiliation and follow community rules;
- answer the problem first and stay within substantiated claims;
- do not provide unsafe medical advice;
- label any evidence gathered after client participation as
  intervention-affected;
- do not recommend participation from one isolated thread.

This calibration does not authorize external participation.

## What not to build from this evidence

Do not yet create:

- any universal score cutoff or comment cutoff beyond Gate 0;
- learned numeric weights;
- a subreddit allow/deny list beyond the audited policies;
- a rule that equates post score with product value;
- a rule that opens every named-product or highly engaged thread;
- a requirement to owner-label the remaining 1,752 clean pairs;
- a production-readiness or corpus-wide selection-quality claim.

The blind 100-thread proof is complete. The smallest next proof, if runtime
implementation is later commissioned, is to encode these corrected gates and
test the implementation against frozen listing projections. Do not request
more owner labels unless a repeated new archetype or disagreement cluster
appears.

## Evidence trace

| Finding | Calibration evidence |
| --- | --- |
| Applicability gates richness and engagement | `C02`, `C16`, `C18`, `C26` |
| Appearance/showcase objective can nullify high engagement | `C04`, `C07`, `C19`, `C21` |
| Direct product failure/recommendation is high-yield | `C05`, `C10`, `C11`, `C13`, `C24`, `C25`, `C27` |
| Progress/regimen value depends on disclosed decision content | `C10`, `C11`, `C15`, `C22`, `C30` |
| Score measures resonance, not evidence depth | `C07`, `C19`, `C28`, `C29`, `C30` |
| Useful post-dive content does not retroactively justify a dive | `C03`, `C08`, `C23`, `C30` |
| Entity-to-brand cross-stitching prevents a material miss | `C09` |
| Product-specific low engagement is usually commission-only | `C12`, `C18`, `C23`, `C26`, `C29`, `C30` |
| Transaction comments are not product-evidence depth | `C23` |
| Whole-post engagement cannot attribute one product in a stack | `C15`, `C28` |
| High-engagement collections can expose purchase economics | `C29` |
| Captured engagement metadata can drift | `C17` |
