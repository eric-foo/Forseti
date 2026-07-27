# Summer Fridays Deliver Corroboration Progression Note — 2026-07-27

```yaml
retrieval_header_version: 1
artifact_role: Deliver intake note
scope: >
  Case-specific Summer Fridays guidance for turning source-specific candidate
  signals into bounded cross-source conclusions without treating SERP output
  as corroboration or installing an exhaustive query grid.
use_when:
  - Starting or preparing the Summer Fridays p10 Deliver turn.
  - Adjudicating whether a Summer Fridays lead is isolated, search-expanded, natively corroborated, contradicted, or ready for bounded inclusion.
  - Deciding whether a proposed Summer Fridays SERP refinement is worth a separately routed acquisition action.
authority_boundary: retrieval_only
open_next:
  - docs/workflows/summer_fridays_understanding_dogfood_20260725_p10/coordinated/acquisition_seal.md
  - docs/research/summer_fridays_ci_inputs_20260726/serp_social_composition_capture_return.md
  - docs/research/summer_fridays_ci_inputs_20260726/google_ads_transparency_capture_return.md
  - docs/research/summer_fridays_ci_inputs_20260726/google_ads_transparency_observed_creative_ids_20260726.json
  - forseti/product/spines/cleaning/contracts/core_spine_v0_corroboration_vs_amplification_discipline_v0.md
stale_if:
  - The Summer Fridays p10 acquisition seal or recovery adjudication is superseded.
  - The referenced SERP, TikTok, Reddit, or Google Ads evidence is recaptured or superseded.
  - Accepted Deliver or Judgment authority supersedes this case-specific note.
```

```yaml
deliver_intake_status: READY_FOR_CASE_SPECIFIC_USE
standing_doctrine_changed: false
acquisition_seal_amended: false
supplemental_evidence_admission: required_before_use
```

## Decision

Use a **corroboration progression**, not a visibility or card-count matrix.
Deliver may join independently preserved source observations and decide what
they support. SERP is a source-route scout: it expands a grounded lead into
candidate sources, variants, vocabulary, and counterevidence routes. A Google
result, snippet, AI Overview, repeated card, or rank is not itself independent
corroboration.

The progression is:

`source-specific seed → targeted source-route expansion → native-source
verification → independence/echo adjudication → bounded Deliver statement`

## Phase Boundary

- **Understanding / acquisition** preserves source-specific observations,
  provenance, limitations, disagreement, and candidate signals.
- **Scanning / Capture** performs any new SERP or native-source follow-through.
  A Deliver actor does not silently reopen acquisition or add live search
  results to a sealed corpus.
- **Deliver** joins admitted evidence, assesses corroboration versus echo,
  preserves counterevidence and uncertainty, and decides whether the candidate
  becomes a conclusion, a material unresolved lead, or an omitted anecdote.

The Summer Fridays SERP, TikTok, and Google Ads supplements were captured after
the original p10 seal. This note does not rewrite that seal. Deliver must verify
and explicitly admit the supplemental pointers before using them.

## Efficient Query Structure

Do not run a mandatory `brand × every franchise × every product` grid. That
would be combinatorial, repeatedly rediscover official and retailer pages, and
create query volume without additional decision value.

Start from a retained lead in retailer reviews, Reddit or another community,
support evidence, legal or regulatory records, owned claims, paid creative, or
another admitted source. Skip generic brand and franchise baselines. Use the
source's exact product and issue language to form a bounded query, then seek:

1. an independent native source;
2. product, variant, timing, or context specificity;
3. contrary or disconfirming evidence; and
4. evidence that the repeated language is not merely syndicated, copied, or
   Google-amplified.

SERP is not corroboration. It expands a retained lead into candidate independent
sources, counterevidence, variants, and more precise search language. Only
admitted native evidence can later help Deliver judge whether the lead is
independently corroborated, contradicted, narrowed, or still isolated.

Continue only while a non-dominated next query has a credible chance to change
the supported statement, its confidence, its product boundary, or the next
decision. Stop when another query would only repeat the same source family,
echo the same unverified claim, or add detail that cannot affect Deliver.

## Corroboration Progress Record

For each decision-material candidate, Deliver records:

| Field | Meaning |
| --- | --- |
| Candidate lead | Product- and issue-bounded proposition being tested |
| Seed evidence | Exact retained source and what it supports |
| Search expansion | Query and candidate routes found; never counted as corroboration |
| Native evidence | Directly preserved source text, comments, media metadata, or other admitted evidence |
| Independence / echo | Whether sources are genuinely independent, syndicated, copied, or uncertain |
| Counterevidence | Contrary accounts, alternative explanations, and scope limits |
| Supported statement | Strongest wording the joined evidence permits |
| Remaining unknown | Prevalence, causality, timing, representativeness, or other unresolved boundary |
| Deliver disposition | bounded conclusion / material unresolved lead / omit as isolated |

No numeric corroboration score or minimum-source count is installed. Source
independence, decision materiality, contradiction, and claim ceiling require
judgment.

## Worked Summer Fridays Progression

### Lip Butter Balm burning/reaction

- **Seed:** retained `/r/beauty` and `/r/Sephora` threads describe burning,
  dryness, flaking, or contact-dermatitis-like experience, with contrary
  accounts also present.
- **Search expansion:** packet `01KYDAFEGK8Y8PBEWF0A111QCX` asked what
  adverse-experience content was Google-visible beyond the captured Reddit
  corpus; later job 6 used the quoted product-plus-issue form.
- **Native follow-through:** TikTok packet
  `01KYF1X0V8TTNZ9KH718V1CTJ8` preserved the selected post description and 20
  comments from a response declaring 77 total.
- **Supported statement:** a recurring multi-source reaction narrative exists
  around Lip Butter Balm; Vanilla Beige is repeatedly named in the admitted
  TikTok source.
- **Boundary:** no prevalence, diagnosis, causality, full-comment census, or
  product-wide safety conclusion.
- **Deliver use:** eligible as a bounded conclusion or material tension only
  with its counterevidence and uncertainty adjacent.

This is the useful pattern:

`lightly corroborated source lead → adversarial SERP sharpening → independent
native evidence → bounded cross-source conclusion`.

“Adversarial” is load-bearing: the search must look for contradiction and
alternative explanation as well as confirmation. Otherwise SERP becomes a
confirmation-bias amplifier.

## Non-Claims

- Not global Deliver, Scanning, Capture, Cleaning, or Judgment doctrine.
- Not permission for Deliver to browse or capture outside the sealed/admitted
  evidence route.
- Not a query quota, every-family obligation, source-count threshold, or
  standing monitor.
- Not evidence that Google result composition represents demand, prevalence,
  consumer behavior, or market share.
- Not a claim that repeated language is independent corroboration before
  syndication, copying, and source identity are assessed.
- Not a Summer Fridays safety, causality, spend, performance, or strategy
  conclusion.
