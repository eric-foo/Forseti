# Choice-Mechanism Chain — Design Proposal v0

```yaml
retrieval_header_version: 1
artifact_role: Design proposal (workflow record; non-authoritative until owner-adjudicated)
scope: >
  Bounded design for the choice-mechanism chain pillar of the CI report:
  acquisition lenses for below-title-level customer evidence (D1), the
  claims-to-complaints five-way review classification (D2), proportionality
  mechanics (D3), the client-facing chain-card format (D4), and one worked
  Tower 28 example. Proposal input to the CSB company-profile contract
  synthesis pass only — never standalone doctrine.
use_when:
  - Adjudicating the chain section of the CSB contract synthesis pass
    (adjudication ledger item 4).
  - Executing the contract-pass PR after owner adjudication.
authority_boundary: retrieval_only
open_next:
  - docs/decisions/forseti_ci_report_external_review_adjudication_ledger_v0.md
  - forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md
  - docs/research/forseti_beauty_tower28_company_intelligence_report_v1.md
superseded_by: forseti/product/spines/commission_signal_board/prompts/forseti_commission_signal_board_prompt_structure_v0.md
stale_if:
  - The design is adjudicated into the CSB contract pass (this proposal then
    becomes historical input, superseded by the contract itself).
  - The owner changes any chain-pillar ruling in the adjudication ledger.
```

## Provenance and load contract

- Commissioned by the handoff packet `docs/workflows/forseti_choice_mechanism_chain_design_handoff_v0.md` (authored on branch `claude/tower28-c1-corrections-c5-validator`; packet is consumed by this proposal's delivery).
- Binding constraints reread directly from
  `docs/decisions/forseti_ci_report_external_review_adjudication_ledger_v0.md`
  (items 4, 9, 10, 12), not from the packet paraphrase.
- Method: three independent design passes (evidence-first,
  decision-consumer-first, adversarial/failure-mode-first) were produced and
  adjudicated into this single proposal; convergent cores were kept, and the
  divergences are ruled in "Adjudication notes" below. Every observation id
  cited in the worked example was verified by direct read against the Tower 28
  v1 observation ledger.

**What this is.** A guidance-only design for how the chain gets fed (D1, D2)
and shown (D3, D4), plus one fully worked Tower 28 card, ready for owner
adjudication in one pass.

**What it is not.** Not a scan, capture, or contract edit. Not a new schema,
ledger, or validator field — the only new durable record is the commissioned
D2 per-review row; confidence marks and card cells are presentation guidance
the conclusion-writer applies. It states no complaint rate without a
denominator, demands no capture/sell-through/rate claim, tracks no comparator
base rate, and is point-in-time (co-movement is the future longitudinal seed,
out of scope).

**Design spine.** Every place a number, claim, or id could be laundered into
something it does not support, the format carries a slot that makes the gap
visible — a denominator, a cannot-see boundary, a specificity marker, a
cell-level "what this id shows" clause. Aggressiveness rides on top of those
slots; it never replaces them.

## The chain

For each hero product: **claim → why customers buy → what they experience →
which complaints attack the claim → where defectors go**, every link
resolving to observation-ledger rows.

## D1 — Acquisition lenses (below title level)

The three sanctioned route-classes already in doctrine — retailer review
surfaces, sanctioned listing reads, public web — are the boundary. Each is
decomposed into the lenses that feed the chain's links, with what each CAN
and CANNOT see. The cannot-see clauses are capability boundaries, not
restraint caveats, and they are load-bearing through two structural rules:

1. **A cell may only be sourced from a lens that can actually see it.**
2. **No lens sees a population rate** — sell-through, repeat purchase, or
   complaint rate — so a rate claim is structurally unsourceable, not merely
   discouraged.

### Route-class: retailer review surfaces

| Lens | Feeds | CAN see | CANNOT see |
| --- | --- | --- | --- |
| **L1 — per-review bodies** (PDP review text) | experience, complaint | dated body text; star; verified-purchase marker where the surface exposes it; problem specificity (vague vs mechanism/ingredient-named); which SKU | complaint rate (only sampled composition); incentivized/gifted status beyond a visible badge; representativeness |
| **L2 — aggregate rating state** (per-SKU rating + count) | experience (dispersion) | reception dispersion across the line; which products read higher or lower at the read date | complaint composition, the why, any text, any rate — reception proxy only |

### Route-class: sanctioned listing reads

| Lens | Feeds | CAN see | CANNOT see |
| --- | --- | --- | --- |
| **L3 — community listing reads** (title+date sanctioned screening) | buy-reason, experience, complaint (theme), substitute | dated thread titles; failure-mode and switching-intent phrasing; need-state venue relevance; title-level recurrence | login-walled bodies; sentiment; outcomes; switching volume; seeding (undetectable at title level) |
| **L4 — read-only public archives** (browser-readable community bodies) | experience, complaint, substitute | verified dated first-person bodies, including claim-contradiction language and price-substitution advice | current conversation (archival only); representativeness; view-count-as-rate |

### Route-class: public web

| Lens | Feeds | CAN see | CANNOT see |
| --- | --- | --- | --- |
| **L5 — independent need-state reviewers/blogs** | buy-reason, experience, substitute | dated first-person experience; explicit repurchase or partial-substitution statements | gifting/PR-sample status (often undisclosed); representativeness |
| **L6 — substitution/comparison surfaces** (dupe aggregators; creator/social search-index titles) | substitute, complaint (theme) | named substitute sets with price gaps; comparison-pair language; theme existence at title level | switching volume (page existence is citing, not switching); content, dates, and authenticity behind an indexed title; SEO/affiliate motive is present |
| **L7 — brand + retailer claim/catalog surfaces** | claim, buy-reason | exact current claim copy and brand-vs-retailer copy divergence; price, shades, assortment; self-designated labels; seals cited | claim version history; substantiation files; whether a self-designated rank is real |

**Coverage note.** Buy-reason for a hero often rests on L7 self-designations
(bestseller / top-3) until L1/L3/L5 corroborate; the card marks that cell
`proxy` rather than treating a brand label as fact. Motivation is never
measured, only read from language: the buy-reason cell carries reported
motivation, never demand.

## D2 — Review classification method

### Admission rule (substantiveness filter)

Classify only **substantive** reviews: verified-purchase where the surface
exposes that marker, plus non-trivial body text (a stated problem, mechanism,
comparison, or use-context). Where the surface exposes a verified-purchase
marker, only marker-bearing reviews are admitted; where the surface has no
such marker, non-trivial body text alone admits. That admission choice is part
of the stated sample definition (D3). **Contentless drive-by star ratings are
never classified** — the separately collected aggregate star distribution (L2)
already carries them, and classifying them would double-count reception as
complaint.

### Per-review record (the one commissioned durable record)

`product | star | class | claim_attacked (claim token, or none) | specificity (vague | mechanism/ingredient-specific) | date`

Six fields, nothing more. This is the entire new recurring toll; it exists so
the complaint cell can state an honest sampled composition instead of arguing
prevalence in prose.

Binding semantics, so two scanners produce the same rows without extra fields:

- **Container.** Each row is a child of exactly one existing observation-ledger
  row — the OBS row for the review-surface read that admitted it. Venue,
  source identity, access route, observation date, and independence lineage
  are the parent's fields and are never repeated in the row.
- **`class` values.** One of the five classes, or `held_background` — the
  recorded holding state for an ungraduated reaction complaint. It is a state
  value, not a sixth analytic class: held rows are counted in the stated
  sample and named as background, never as claim-attacks.
- **Primary only.** The row carries the tie-break primary. A secondary reading
  that changes the read (e.g. a cheaper named substitute inside a
  substantiation-risk review) is carried by the report narrative that cites
  the row, not by the row.
- **`date`.** The review's own publication date as the surface shows it
  (`null` when the surface shows none). The parent OBS row carries the
  observation date; the two are never conflated.
- **Contract insertion seam** (named for the contract pass, which owns the
  actual edit): the rows live as one typed child block under the company
  contract's Section 7 (customer and community response), keyed by parent OBS
  id and serialized like the contract's existing typed YAML documents. No
  validator or ledger fields are added.

### The five classes (claim-relative, text-triggered)

Classification is **relative to the brand's load-bearing claim set** — state
those claims first, classify against them. The same text classifies
differently across brands ("broke me out" attacks a sensitive-skin promise;
for a long-wear brand it is an ordinary defect).

1. **Substantiation risk** — names a specific stated claim (a label word,
   seal, or test claim) AND a specific checkable counter (named ingredient,
   named certification/test discrepancy). Consequence lane: claims-file /
   retailer-compliance.
2. **Core-positioning threat** — reports the exact harm the load-bearing
   positioning promises to prevent, tied to the product, and clears the
   graduation bar below. Consequence lane: positioning/demand.
3. **Price-value** — worth/price is the actual grievance ("not worth $24",
   "drugstore does the same", names a cheaper equivalent). Also wires into
   the substitute cell. **Reconciled (owner-ratified 2026-07-29):** the
   substitute cell is filled ONLY from finding-grade `substitute_down` +
   `dupe_association` entries with their observation ids, per the SERP
   lane's typed competitor ledger; ad hoc per-report filling is retired.
   A complaint naming an equivalent emits such an entry (any driving
   axis, not price-value only — see the ledger spec's Channel 3). See
   `docs/research/serp_lane_competitor_scout_20260728/competitor_ledger_spec_v0.md`
   ("Wiring into the claims-to-complaints path"). This pointer records the
   divergence only — it decides nothing.
4. **Education gap** — expectation/use mismatch where the product performed
   as designed and never claimed otherwise.
5. **Ordinary defect** — residual class: performance/quality failure
   unrelated to the load-bearing claim (creasing, oxidizing, pump, wear,
   packaging, shade accuracy).

### Tie-break ladder (deterministic; first match wins)

**Substantiation risk → core-positioning threat → price-value → education
gap → ordinary defect (residual).**

The top two are the rarest, most specific, highest-consequence signals — the
ones the complaint cell exists to surface — so a review qualifying for them
is never buried under a lower class. One primary class per review;
`claim_attacked` preserves the linkage, and a secondary class is recorded
only when it changes the read (e.g. a substantiation-risk review that also
names a cheaper substitute feeds the substitute cell).

### Expected-background: a holding state, not a sixth class

The expected-background class from ledger item 4 (idiosyncratic /
allergy-type reactions every sensitive-skin brand accrues) sits **underneath**
the two claim-attack classes as their default holding state, not beside them
as a peer. A reaction complaint ("broke me out", "stung", "irritated") lands
in expected-background by default: recorded, denominated, visible — and
explicitly not counted as a claim-attack. This makes "assume category
background exists" operational without measuring a base rate: background is
the definitional floor, not a computed number.

### Graduation rule (ledger item 4, honored exactly)

A held reaction complaint (or theme) graduates to a claim-attack class when
**any one** holds:

1. it is **ingredient-specific** (names the mechanism/ingredient), or
2. it is **repeated across independent venues**, or
3. it **directly attacks the load-bearing claim** (names or quotes it).

Routing on graduation: named label + named counter → **substantiation risk**;
graduation on repetition or direct attack without a checkable counter →
**core-positioning threat**.

Claim relativity is preserved through the candidate gate: graduation applies
only to complaints whose harm falls inside the brand's stated load-bearing
claim set. An ingredient-specific complaint that attacks no stated claim never
graduates — it is an ordinary defect with `claim_attacked: none`, and
reaction-type instances of it stay `held_background`. Claim specificity (a
property of the brand's own copy, the D3 amplification input) and complaint
specificity (a property of the review, the D2 marker) are distinct and never
substitute for each other.

A `specificity: vague` complaint matches no
trigger on its own and stays background until independent repetition — a
single verified ingredient-specific instance graduates itself. Aggressive and
bounded at once, by construction.

## D3 — Proportionality mechanics

**1. Proportions are of stated samples only.** Any count on the card renders
in a fixed micro-frame that cannot be written without its denominator and
sample definition:

> `<n> of <N> sampled substantive <negative | all> reviews — <venue>, <date-range>`

The `<negative | all>` token is mandatory: a proportion drawn from a
negative-only base must say so, so it can never masquerade as a share of all
reviews. A bare count is not a renderable value. A stated sample also states
how it was drawn — the selection route and order (e.g. all substantive reviews
in the date range under the platform's default sort, or most-recent-first to a
stated depth) plus the D2 admission handling — enough that a second scanner
could reproduce `N`. A denominator over an undefined convenience sample is not
a stated sample. Where no per-review sample
exists yet, the card states **no proportion at all** — raw verified instances
plus the next observable that would produce a denominator. Refusing the rate
is the honest move, not a gap to paper over.

**2. No base-rate tracking — say so, once.** The card carries one standing
sentence and tracks nothing:

> *Sensitive-skin cosmetics accrue idiosyncratic-reaction complaints as
> category background. This card tracks no comparator base rate and makes no
> cross-brand rate claim.*

(Adapt the category wording per subject.) This satisfies "assume category
background exists and say so" without the base-rate ledger the owner rejected
as unmaintainable.

**3. Claim-amplification does the base-rate's job — and scales decision
weight, never the number.** An explicit brand claim amplifies any complaint
that attacks it; the stronger and more specific the claim, the more a
claim-attacking complaint counts **toward the decision**. The amplification
marker is a function of the claim — fully observable in the brand's own copy
— never of unobserved prevalence:

| Claim being attacked | Amplification |
| --- | --- |
| Explicit AND specific (named label word, ingredient-level, or seal — e.g. "non-comedogenic", "acne-safe") | **High** |
| Explicit but general ("safe for sensitive skin") | **Medium** |
| Implicit / none | **None** — no claim-attack amplification; the complaint keeps its D2 class (ordinary defect when it attacks no stated claim) |

Amplification binds to the D2 specificity marker: an ingredient-specific
complaint attacking an ingredient-level claim is the most decision-bearing
complaint on the board even at n=1 — and the card says **why** (claim
property) rather than inflating **how many**. The amplification note and the
denominator (or its absence) always appear in the same breath, so decision
weight never leaks into implied prevalence.

## D4 — Chain-card presentation format

One card per hero product:

- **Mechanism sentence** on top — one aggressive, decision-bearing line:
  where the value sits, what drives the buy, the most specific thing
  attacking it, where the pressure resolves.
- **Five cells** beneath — claim / buy-reason / experience / complaint class
  / substitute — each carrying its observation ids, a one-clause statement of
  what each id shows in this cell, and a confidence mark. The complaint cell
  additionally carries the D3 composite (sampled composition or instances +
  amplification) and the standing background sentence.

### Confidence marks (fixed vocabulary; presentation only)

`verified` (first-party page read or browser-verified body) · `corroborated`
(same signal across independent venues) · `proxy` (aggregate rating state or
brand self-designation; ceiling-bound) · `thin` (single instance or
title-level listing) · `unverified` (search-index metadata; platform not
read). A cell inherits the weakest mark among its load-bearing inputs. The
complaint cell may carry a **split mark** — e.g. `verified (exists) /
unsampled (prevalence)` — the visual form of the D3 honesty rule. Marks
compress fields the report already carries (`source_class`, `recency_tier`,
`current_state_use`); no new schema.

### Four structural rules

1. **Mechanism-sentence containment.** Every load-bearing noun in the top
   sentence traces to a cited cell below it. The sentence may compress and
   sharpen; it may not assert what the cells do not carry.
2. **Every id states what it shows.** A dead id cannot produce its clause, and
   the clause must stay inside its row's excerpt, time anchor, fact domain,
   and ambiguity limitation. This makes mispointing visible to review; it does
   not make it impossible — a fluent-but-broader clause is author error the
   format cannot self-catch. The actual check is discipline with a stated
   ceiling: the author verifies each clause against its row before the card
   ships, and review re-verifies.
3. **The complaint cell obeys the D3 denominator frame.** No count without
   the micro-frame or an explicit no-proportion statement.
4. **Empty-cell honesty.** A link with no substantive observation reads
   `no substantive evidence — <GAP/REQ id>`, never plausible filler.

Shipping note (guidance only, existing seam): when a card ships, cells whose
evidence could change a conclusion, be disputed, or disappear point to the
already-accepted capture-request trigger (adjudication ledger item 12) through
the report's existing typed requests. No new seam, schema, or capture is
created here.

Because each cell shows its own evidence floor, the mechanism sentence is
free to be maximally aggressive — the reader sees exactly what holds it up.

### Compression to the front-page 5-field row (ledger item 9)

| Field | Source in the card | Discipline |
| --- | --- | --- |
| **claim** | mechanism sentence, tightened to the decision assertion | verbatim label words where the claim is a label word |
| **evidence** | load-bearing cell ids + the D3 composite carried intact | the admission field: exactly what is and is not in hand, with denominators and gap ids |
| **consequence** | the mechanism sentence's decision-bearing edge | maximally aggressive |
| **confidence** | the weakest load-bearing cell | aggressive but split: high on existence of the claim-attack, explicitly low on prevalence when no denominator is sampled — committing to what is and is not known, not hedging both |
| **next observable** | the cheapest read that upgrades the weakest cell | usually the graduation trigger; this field is what makes the aggressive consequence safe. If no graduating observation is nameable, the consequence must soften — there is nothing to make it safe |

## Worked example — Swipe concealer (Tower 28 hero, selected example)

Filled entirely from existing Tower 28 v1 observation rows; every citation
verified against the row it sits in. No new scanning. Rebuilt after the
adversarial review (see Review disposition record below) to obey this
proposal's own rules: time anchors carried, allegation kept an allegation, no
conversion or switching claim, marks at the weakest load-bearing input.

### Chain card

> **Mechanism sentence:** Tower 28's hero Swipe concealer ($24, brand-labeled
> Bestseller) is sold on the brand's current sensitive-skin-safe promise, and
> the sharpest recorded attack on that promise is a browser-verified 2024
> customer complaint naming Polyglyceryl-3 Diisostearate against Sephora PDP
> copy that then read "non-comedogenic" — a label word the brand's own current
> ingredients page avoids — while dupe surfaces currently pair a $12 NYX
> substitute against it.

| Cell | Content | Ids + mark |
| --- | --- | --- |
| **Claim** | "Safe for even the most sensitive skin" — brand mission line, current (OBS-001: homepage copy, read 2026-07-16). "Non-comedogenic" — Sephora PDP copy **as quoted in a 2024 thread** (OBS-023); not a current PDP read. The brand's own current ingredients page avoids that word (OBS-003, read 2026-07-16) — a claim-surface divergence observed across time anchors. | OBS-001, OBS-003, OBS-023 · `verified` (current brand copy) / `verified-2024-quotation` (retailer copy) |
| **Buy-reason** | Positioned draws only — reported and self-designated, not measured motivation: brand-labeled Bestseller, 21 shades, $24 (OBS-004, current, self-designation); brand-supplied top-3 Sephora NA concealer claim (OBS-012, one origin, unaudited); carried among Sephora makeup heroes (OBS-008, current). The eczema need-state community actively discusses the brand and its ingredient class — venue relevance only, not Swipe-buyer motivation (OBS-020, title-level). | OBS-004, OBS-008, OBS-012, OBS-020 · `proxy / thin` (weakest load-bearing input is title-level) |
| **Experience** | Mid-pack at the read date: 4.34 across 3,652 Sephora reviews (OBS-009, current — reception proxy, not a complaint rate). Dated rejection title "anyone elses tower 28 concealer suck?" (2026-06-06) coexists with haul/pairing threads in the same venue (OBS-017, title-level). One dated first-person account praises the brand's skincare yet prefers a Typology concealer (OBS-024, single reviewer, independence unproven). | OBS-009, OBS-017, OBS-024 · `proxy / thin` |
| **Complaint class** | **Substantiation risk** (graduated: ingredient-specific AND directly attacks the quoted claim; tie-break routes named-label + named-counter here), secondary core-positioning threat. The evidence is a **named customer allegation, not a verified contradiction**: a browser-verified 2024-04-25 complaint says Swipe "broke me out", names Polyglyceryl-3 Diisostearate, and sets it against PDP copy quoted in-thread as "non-comedogenic" (OBS-023; the row itself notes the comedogenicity assertion is the customer's, not a test result). Sidebar recurrence pointers into 2025 exist, bodies unread (OBS-023). Undated, unverified indexed TikTok theme alongside: "Tower 28 Concealer Made Me Breakout" (OBS-025). **Amplification: High** — the attacked claim is an explicit named label word. **Composition: 1 verified allegation + 1 unread title theme; no sampled proportion (GAP-008).** *Sensitive-skin cosmetics accrue idiosyncratic-reaction complaints as category background; no comparator base rate is tracked or claimed.* | OBS-023, OBS-025 · `verified (allegation exists, 2024) / unsampled (prevalence)` |
| **Substitute** | Heterogeneous citing signals — no switching observation exists: dupe aggregators currently pair NYX Bare With Me $12 against Swipe $24 (OBS-027, current, SEO/affiliate-motivated, partly snippet-level); undated comparison-genre titles "Tower 28 vs NARS", "Tower 28 VS Saie" (OBS-026, unverified). One verified partial substitution: a brand advocate prefers Typology's concealer (OBS-024). Historical shade-range edge exclusion: a 2026-01 pale-olive request excludes "Tower 28 BU" (OBS-021, title-level, >180d chronology). | OBS-021, OBS-024, OBS-026, OBS-027 · `proxy / unverified` (distinct signals; citing ≠ switching; not corroboration of one claim) |

### Compressed front-page row

| Field | Content |
| --- | --- |
| **Claim** | Tower 28's hero Swipe concealer is sold on the brand's current sensitive-skin-safe promise; the strongest recorded attack is a 2024 ingredient-named customer allegation against retailer claim copy that then read "non-comedogenic" (OBS-001, OBS-003, OBS-023). |
| **Evidence** | One browser-verified 2024 complaint naming Polyglyceryl-3 Diisostearate against quoted "non-comedogenic" PDP copy, with 2025 recurrence pointers unread (OBS-023); an undated, unverified indexed TikTok breakout theme (OBS-025); 4.34/3,652 current aggregate reception (OBS-009); dupe surfaces currently pairing NYX $12 against $24 (OBS-027). Named instances, not a sampled rate (GAP-008). Current Sephora PDP claim copy was not read this pass; the brand's own current page avoids the word (OBS-003). |
| **Consequence** | The claim surface is the hero's most exposed axis: an ingredient-named allegation against a quoted label claim is exactly the complaint class that does the most damage if it repeats. Pressure-test Swipe's claim surface — a current PDP claim-copy read plus a claims-file check — before any Phase 2 lean on acne-safe positioning. |
| **Confidence** | High that the 2024 allegation exists, names the ingredient, and attacks the claim as then quoted (verified direct read). Low on prevalence — one verified allegation plus an unread title theme, no sampled denominator (GAP-008) — and low on current retailer copy state (2024 quotation; current PDP unread). |
| **Next observable** | Bounded per-review text sampling of Swipe's Sephora reviews (REQ-004) plus the report's capture requests REQ-001 / REQ-002 (which carry the scan-side CR-001 / CR-002 lineage) plus a current Swipe PDP claim-copy read: repeated independent ingredient-specific complaints yield the first stated-sample composition ("k of n sampled substantive negatives attack the claim"); near-silence keeps it idiosyncratic background. |

The consequence and confidence are maximally aggressive — a decisive
"pressure-test this first" and a committed high/low split — and every
aggressive word is bounded by the evidence line, the stated absence of a
denominator, the carried time anchors, and the next observable that would
move it.

## Limits and accepted residuals

**D1.** No lens sees population rates, switching volume, sell-through, or
reviewer independence; for Tower 28, community bodies and creator content
stay title/theme-level until the report's capture requests (REQ-001 /
REQ-002) execute. *Accepted residual:* a complaint cell can prove existence
and specificity of an attack but never prevalence without a captured,
denominated sample — designed in, not a defect. Buy-reason often rests on
`proxy`-marked self-designations until independently corroborated; the design
surfaces this rather than resolving it.

**D2.** The six-field row is the only added record; classification quality
depends on judgment at tie-break boundaries and on the surface exposing a
verified-purchase marker. *Accepted residual:* a `vague` complaint stays in
expected-background and cannot graduate alone — a genuine but inarticulate
positioning failure sits undercounted until it repeats across independent
venues. Accepted: promoting vague complaints is the worse failure.

**D3.** No comparator base rate exists; the standing sentence asserts
category background without measuring it. Amplification is a claim-property
decision weight, deliberately not a measured customer-prevalence effect.
*Accepted residual:* a graduated claim-attack can still be genuinely
low-prevalence; the card asserts decision weight and says so, never
incidence.

**D4.** The containment and id-clause rules make an outrunning sentence and a
mispointed id visible to review — they are author/review discipline with a
stated ceiling, not self-enforcing structure — and they do not catch a
correctly-cited cell that is itself thin; the confidence mark surfaces that
thinness rather than removing it.
Confidence marks are evidence-class grades, not probabilities. *Accepted
residual:* the front-page row's aggressive consequence is only as safe as its
next observable is honest; with no graduating observation nameable, the
consequence must soften. The five-cell compression can under-represent a
product with several distinct claim-attacks; one primary class per complaint
keeps legibility and accepts that loss.

**Worked example.** Swipe's strongest complaint (OBS-023) is a single
verified 2024 customer allegation; graduation is carried by
ingredient-specificity, not prevalence, and the card states this in-cell and
in the confidence field. Until REQ-004 / REQ-001 / REQ-002 land, the honest
ceiling is "a named 2024 allegation attacking the claim as then quoted",
never "verified contradiction" or "measured positioning failure" — and the
card's discipline rules exist to keep that ceiling visible.

## Adjudication notes (divergences ruled during synthesis)

Three independent design passes converged on: Swipe/OBS-023 as the worked
hero; expected-background as a holding state under the claim-attack classes
with the three ledger graduation triggers; the substantiveness filter with
the double-counting rationale; the six-field record as the whole recurring
toll; amplification as decision weight never rate; split existence/prevalence
confidence; and refusing any proportion for Tower 28 until REQ-004 samples a
denominator. Divergences were ruled as follows:

| Divergence | Ruling | Why |
| --- | --- | --- |
| Tie-break order (one pass put core-positioning above substantiation) | Substantiation risk first | Named label + named counter is the rarer, more precise, independently checkable signal, and routes to a distinct consequence lane (claims-file/compliance); two of three passes agreed |
| Last two ladder rungs | Education gap above ordinary defect | Ordinary defect is the residual class and belongs last |
| Confidence vocabulary (bracket tags vs 3 glyphs vs 5 words) | Five-word set + split mark on the complaint cell | Self-explanatory without a legend; the split mark carries the D3 honesty rule visually |
| Amplification expression (prose rule vs claim-specificity table) | The High/Medium/None table bound to the D2 specificity marker | Amplification becomes a function of fully observable brand copy, not analyst mood |

## Review disposition record (adversarial review, 2026-07-17)

Reviewed by an adversarial artifact review at revision `ae2890e6`:
`docs/review-outputs/adversarial-artifact-reviews/forseti_choice_mechanism_chain_design_proposal_adversarial_review_v0.md`
(16 findings; recommendation `patch_before_acceptance`). Chief Architect
adjudication and this patch's dispositions:

| Finding | Adjudication | Disposition in this artifact |
| --- | --- | --- |
| AR-01 record/state machine | Confirmed | Closed — binding semantics added to the D2 record (parent OBS container, `held_background` state value, primary-only, `date` meaning, Section 7 insertion seam) |
| AR-02 claim relativity | Partially confirmed | Closed — claim-relative routing rule added to graduation; D3 amplification `none` row no longer reassigns class |
| AR-03 restraint-caveat ceremony | Rejected as major | CAN/CANNOT columns are the commissioned deliverable ("name what each lens can and cannot see"); accepted as a minor redundancy trim in Limits |
| AR-04 strengthening question | Rejected as proposal defect; routed | Ledger item 10 is a sibling contract-pass item (and partly temporal, excluded by the drift guard); the contract pass composes the front-page voice and may render "strengthening: not observable point-in-time" |
| AR-05 preservation trigger | Downgraded to minor pointer | Closed — guidance-only shipping note added in D4 pointing to the existing item 12 capture-request trigger |
| AR-06 date-anchor laundering | Confirmed | Closed — worked example rebuilt with explicit time anchors; "non-comedogenic" carried as 2024-quoted retailer copy, never current PDP state |
| AR-07 motive/defection/conversion | Confirmed for worked-example language | Closed — conversion/motivation claims removed; buy-reason recast as positioned draws + venue relevance; chain link names stay (commission-owned) with D1's reported-motivation boundary carrying the discipline |
| AR-08 allegation promoted | Confirmed | Closed — evidence described as a named customer allegation; contradiction language removed; aggressive action recommendation kept |
| AR-09 confidence marks | Confirmed | Closed — worked cells re-marked at weakest load-bearing input; heterogeneous substitute signals no longer called corroborated |
| AR-10 sample definition | Confirmed | Closed — selection route/order/admission added to the D3 stated-sample definition; "rate-bearing positioning failure" replaced with stated-sample composition |
| AR-11 insertion seam | Confirmed | Closed — Section 7 / parent-OBS placement named in the D2 record semantics; contract pass owns the edit |
| AR-12 CR citations | Confirmed | Closed — report request rows REQ-001/REQ-002 cited; scan-side CR-001/CR-002 named as nested lineage only |
| AR-13 mispointing guard | Partially confirmed | Closed — D4 rule 2 and Limits restated as discipline with a stated ceiling, not self-enforcing structure |
| AR-14 temporal wording | Confirmed minor | Closed — D1 L2 wording anchored to the read date |
| AR-15 admission ambiguity | Confirmed minor | Closed — one reading bound in the D2 admission rule and tied to the sample definition |
| AR-16 "flagship" | Confirmed minor | Closed — observed labels only |

This record is adjudication routing for the contract pass, not validation,
acceptance, or readiness; owner adjudication of the proposal still governs.

## Non-claims

- Not doctrine, validation, readiness, acceptance, or a contract edit; the
  CSB contract pass adjudicates what, if anything, lands.
- No demand, capture, sell-through, or rate claim; substitution is described
  by citing named substitutes and price gaps; complaint composition by class
  and stated-sample denominator only.
- No monitoring cadence; point-in-time only.
- A future card or row inherits none of this worked example's conclusions;
  the example demonstrates format under the Tower 28 v1 evidence state.
