# Summer Fridays Verification Supplement Return — 2026-08-06 v0

```yaml
retrieval_header_version: 1
artifact_role: Capture return artifact
scope: >
  Bounded verification supplement for Summer Fridays product-page history,
  cosmetic adverse-event records, and public INCI comparison against named
  Lip Butter Balm alternatives.
use_when:
  - Evaluating the Summer Fridays Deliver run's reformulation, reaction, and dupe-equivalence claims.
  - Reading the raw-capture receipts and source-access gaps for this one-shot pull.
authority_boundary: retrieval_only
open_next:
  - docs/research/summer_fridays_ci_inputs_20260806_verification/verification_supplement_extracts.json
stale_if:
  - The FDA cosmetic-event data advances beyond its observed 2025-08-31 currency date.
  - The named product pages publish new ingredient lists, sizes, prices, or claims.
  - Archive.org access recovers and the blocked product histories are recaptured.
```

Commissioning source: `docs/prompts/handoffs/summer_fridays_verification_supplement_capture_handoff_20260806_v0.md` on branch `origin/claude/verification-aems-rebind`, blob `1561bfd5fc936aa787ebe489c5b21642e6fb5477`.

## 1. Executive conclusion

1. **Product-page history — partial, with one real claims drift and no sampled
   Sheer Skin Tint formula or price drift.** The two complete late-2022 Sheer
   Skin Tint snapshots and the 2026-08-06 live page contain the same 820-character
   INCI string (normalized-string SHA-256
   `5d8001e92f747355854b278dc04bc4a135657c7d0846dce5b230e3c0e4fa0b29`)
   and show a $42 price. The product description was shortened and compressed
   between the 2022-12-11 snapshot and the current page: the efficacy-adjacent
   redness / pores / uneven-tone claim was dropped, while the lightweight,
   sheer-color, natural-finish, and hydration concepts were already present in
   2022. Lip Butter Balm and Jet
   Lag Mask archive indexes were not retrievable in this sitting, so no
   2022-present historical verdict is claimed for them. Separately, Summer
   Fridays' dated 2021-06-16 brand post announces an earlier Jet Lag Mask
   reformulation that removed fragrance/essential oils and added a soothing
   blend. A companion first-party statement responds to irritation reports and
   says some third-party production batches were compromised; it does not link
   those batches to the captured FDA reports or verify a second change during
   the 2024-2025 complaint era.
2. **Reaction signal — two Summer Fridays matches, both Jet Lag Mask and both
   direct reports.** The official openFDA cosmetic-event endpoint returned two
   records: a 2020 report with erythema and skin irritation and a 2021 report
   with chemical burn. The endpoint labels its data unvalidated and reports a
   `last_updated` date of 2025-08-31. These records are signal only: they do not
   establish causation, incidence, comparative safety, or current absence.
3. **Dupe equivalence — refuted at the public-list level for both named pairs.**
   Summer Fridays Lip Butter Balm and e.l.f. Glow Reviver Melting Lip Balm share
   2 of the first 5 listed ingredients and 10 exact normalized ingredients
   overall (Jaccard 0.2632); Summer Fridays and Glossier Original Balm Dotcom
   share 0 of the first 5 and 2 overall (Jaccard 0.0741). Both verdicts are
   `materially_different_lists`. This refutes “identical ingredient lists,” not
   consumer-perceived similarity, efficacy, or safety.

## 2. Instrument 1 — product-page history

### 2.1 Sheer Skin Tint

| Capture | INCI | Price | Size shown | Headline/claim wording | Verdict |
| --- | --- | --- | --- | --- | --- |
| Wayback `20220929002552` | Same normalized 820-character list as current | $42 | Not exposed in captured page text | Lightweight skin tint; sheer color; hydration; weightless fluid formula; redness / pores / uneven-tone claim; sheer-to-light coverage; natural finish; flexible shades; no-makeup look | Baseline; complete gzip response |
| Wayback `20221211205012` | Same | $42 | Not exposed | Byte-identical description to 2022-09-29 | `no_change_observed` vs 2022-09-29 |
| Live page, retrieved 2026-08-06 | Same | $42 | 30 ml / 1 fl oz | Lightweight fluid formula; sheer color and coverage; natural finish; hydration; badges: Hydrating / Dewy / Sheer Color | Description shortened after 2022-12-11; INCI and price unchanged at sampled endpoints |

The observed change is primarily a deletion plus compression, not a shift
toward lightweight / sheer-color / natural-finish / hydration concepts: all
four were already present in 2022. The current description drops the
efficacy-adjacent redness / pores / uneven-tone claim and the historical
weightless, sheer-to-light-coverage, flexible-shades, and no-makeup-look
language. The site-level `<meta name="description">` and `og:description` are
byte-identical across all three captures, which bounds the observed change to
the product-description surface.

The change is bracketed by captures, not point-dated. The size axis is
`inconclusive`: the current page states 30 ml / 1 fl oz, while the two usable
2022 page bodies did not expose a size string. A change between sampled dates
cannot be excluded.

### 2.2 Lip Butter Balm

The current official page was captured at **$24** and **15 g / 0.5 oz**, with a
current Vanilla INCI list. The Wayback CDX request returned HTTP 503 and the one
bounded alternate request timed out with zero bytes. Therefore formula, size,
price, and claims history are all `capture_blocked`; no historical verdict is
made.

### 2.3 Jet Lag Mask

The current official page was captured with two sizes, **28 g / 1.0 oz** and
**64 g / 2.25 oz**, and a displayed $49 buy-once price for the selected size.
The Wayback CDX request timed out; the bounded alternate response was unusable.
The 2022-present page-history verdict is therefore `capture_blocked`.

An official Summer Fridays post dated **2021-06-16** announces an earlier
reformulation: the brand says it removed all fragrance, including essential
oils, and added allantoin, bisabolol, panthenol, and cucumber extract. The
source is the brand's own blog post, so this is a first-party announcement, not
independent verification of the formula change.

The companion statement supplies the first-party remediation context. The brand
says it received reports of temporary redness and irritation, found certain
third-party production batches compromised, tightened manufacturing protocols,
withdrew named lots from retailers, offered refunds, and made a minor
reformulation that removed essential oils. It also states the brand's view that
the product did not threaten customer health and safety. These are the brand's
own claims; the captured evidence does not independently establish the cause of
the reported reactions or connect the affected batches to either FDA report.

This is a verified brand-announced formula-change event, but it is outside the
requested 2022-present sample and is not an INCI-to-INCI snapshot comparison.

## 3. Instrument 2 — FDA cosmetic adverse-event records

### 3.1 Source route and currency

The live FDA AEMS cosmetics Qlik dashboard was opened and its disclaimer was
accepted. It states that cosmetics data are updated daily/near-real-time and
that searches are name-sensitive, incomplete, unverified, non-causal, and
unsuitable for rates or product comparisons. Its product-search extension did
not reliably apply the typed filter or expose an export in this sitting.

The record pull therefore used the FDA-linked official alternative,
`https://api.fda.gov/cosmetic/event.json`. Its response metadata reports
`last_updated: 2025-08-31`; this is the operative currency ceiling for the
records below, not the live dashboard's daily-refresh claim.

### 3.2 Summer Fridays matching record set

| FDA report | Initial receipt | Event date | Product(s) and role | Reaction terms | Stream |
| --- | --- | --- | --- | --- | --- |
| `24516207` / legacy `2020-CFS-012383` | 2020-11-27 | 2020-11-27 | Summer Fridays Jet Lag Mask — Suspect; Vitamin D — Concomitant | Erythema; Skin Irritation | Direct |
| `24519370` / legacy `2021-CFS-000593` | 2021-01-20 | 2021-01-16 | Summer Fridays Jet Lag Mask — Suspect | Chemical Burn | Direct |

Counts by initial-receipt year: **2020: 1; 2021: 1; total: 2**. A broad
`products.product_name:Summer` query returned 44 records, but client-side exact
brand screening found only these same two Summer Fridays matches.

### 3.3 Comparator context

| Brand query | Counts by initial-receipt year | Total | Product matches |
| --- | --- | --- | --- |
| Laneige | 2022: 1; 2025: 1 | 2 | Radian C Cream; Lip Glowy Balm Grapefruit |
| Glossier | 2019: 1; 2020: 1 | 2 | Perfecting Skin Tint; Bubblewrap Eye And Lip Plumping Cream |

These counts are **context only, never a safety ranking**. Every record captured
here — both Summer Fridays records, all 44 broad-screening records, and all four
comparator records — carries `report_type: Direct`; no mandatory MoCRA-era
serious-event report appears in this capture, so the mix of reporting streams in
the wider database is unobserved rather than confirmed. Presence is a signal;
absence is not exoneration. Counts are not incidence or rates. Because the
underlying database spans both voluntary and, since MoCRA, mandatory reporting,
year-over-year changes across the late-2023/2024 boundary must not be read as
product deterioration, and this API's 2025-08-31 currency ceiling means it
cannot establish present-day absence.

## 4. Instrument 3 — INCI comparison against named alternatives

The exact pair names came from the sealed coding: e.l.f. Glow Reviver Melting
Lip Balm appears in row 844/thread `1ktoo8j`, and Glossier Balm Dotcom appears
in Lip Butter Balm comparison rows including row 18/thread `10vrvls` and row
109/thread `15qtzd8`. The compared variants are Summer Fridays Vanilla, e.l.f.
Yummy Gummy, and Glossier Original because all three current official pages
published usable lists.

| Pair | First-five overlap | Full exact normalized overlap | Notable one-sided ingredients | Verdict |
| --- | --- | --- | --- | --- |
| Summer Fridays Lip Butter Balm Vanilla vs e.l.f. Glow Reviver Melting Lip Balm Yummy Gummy | 2 / 5 | 10 shared; SF share 55.56%; e.l.f. share 33.33%; Jaccard 26.32% | SF: polybutene, hydrogenated C6-14 olefin, murumuru butter, sodium hyaluronate. e.l.f.: tridecyl trimellitate, styrene copolymers, jojoba/mango/cocoa/meadowfoam oils or butters, fragrance, hydrolyzed sodium hyaluronate. | `materially_different_lists` |
| Summer Fridays Lip Butter Balm Vanilla vs Glossier Original Balm Dotcom | 0 / 5 | 2 shared; SF share 11.11%; Glossier share 18.18%; Jaccard 7.41% | SF uses a dimer-dilinoleate/emollient/wax base with shea and murumuru. Glossier leads with petrolatum, castor oil, beeswax, lanolin, and cupuaçu butter. | `materially_different_lists` |

The shared e.l.f. base ingredients can support a public-list claim of some
structural similarity, but the lists are not identical and the ordered
first-five differ materially. Ingredient lists do not disclose concentrations,
manufacturing process, grade, or sensory performance, so even an identical list
would not prove an identical formula. No safety or efficacy conclusion is made.

## 5. Capture receipts

Raw root: `C:\tmp\forseti-sf-verification-supplement-20260806\data`

| Raw path | Bytes | SHA-256 | Use |
| --- | ---: | --- | --- |
| `wayback/sheer_skin_tint_20220929002552.html` | 71,040 | `9fb8c5c44fb8da176fb40e36004a6566c2182901ad4889929dbe61caab1aed2b` | Complete gzip Wayback response |
| `wayback/sheer_skin_tint_20221211205012.html` | 75,292 | `1c989a8d1ffc092abaf89e1cea72ef97728a142dc750199c25f1a34e3ccfb8c1` | Complete gzip Wayback response |
| `wayback/sheer_skin_tint_current.html` | 824,661 | `c33f195407bb09ada630a05d832e349834cf262a07199b0f484da8b7b63d2e2f` | Current official PDP |
| `wayback/jet_lag_mask_current.html` | 783,562 | `e36de088759bef103ed17606775e4027b906aa692010f73592042d4f5b42edf7` | Current official PDP |
| `wayback/jet_lag_mask_statement_current.html` | 519,436 | `0d42e96d89ad7d7c8cfba2b944b19bfe57b29aad147dd140146a0a25cee1ec1f` | Official reformulation statement |
| `wayback/jet_lag_mask_upgrade_blog_current.html` | 540,280 | `95ff727f4d9ddc3795ab66bbcd8acd9a2abf6bf32e62e4181c261b9ab1657a32` | Dated 2021-06-16 brand post |
| `aems/summer_fridays_phrase.json` | 1,831 | `a7a9ac5b61792d078c7b58b964fcc57829b7c9fe351a00edcd4e805dbd8fca71` | Two Summer Fridays records |
| `aems/summer_token.json` | 40,636 | `d93d0e1d87ea956cbc60c8c228560b6bc0110eab9a35b509242c79bbbb5a0864` | Broad-name screening receipt |
| `aems/laneige.json` | 1,854 | `9cede1c6dcf0c1ab1899824c9dd2e388aaaf1abda13f3cf7a52b7728367d3efc` | Comparator records |
| `aems/glossier.json` | 2,563 | `5fbd726cc36884ad44b32f5c508c3fd25e159aa85108f7501584c4a521a347e8` | Comparator records |
| `inci/summer_fridays_lip_butter_balm_current.html` | 738,390 | `e40e931294cb740a588e663a78b7459b8d06741bba297d6097adaa14faa05c4b` | Subject INCI |
| `inci/elf_glow_reviver_melting_lip_balm_yummy_gummy_current.html` | 1,336,895 | `d5de6dcd0f7ed900ca26f8c3dd878790e7d7d5083f195fb0bd62eb46780ff13a` | e.l.f. comparator INCI |
| `inci/glossier_balm_dotcom_current.html` | 1,499,471 | `f563fba6af598968c2e92a6c6b9905114e5293e930dba1cbef9883f7b432bdb8` | Glossier comparator INCI |

The URLs, ingredient lists, records, metrics, and capture hashes behind the
decisive verdicts are duplicated in `verification_supplement_extracts.json` for
machine use, including the broad-screening receipt
`aems/summer_token.json`. The JSON does not duplicate every byte count shown in
the table above.

## 6. Failure and gap ledger

- **Wayback CDX:** Sheer Skin Tint returned an observed 49-row index on the
  first query, but that response could not be retained after a later HTTP 503,
  so the row count is an unretained observation with no capture behind it. Lip
  Butter Balm returned HTTP 503; Jet Lag Mask timed out. One bounded alternate
  request also failed for each. No other archive was silently substituted.
- **Wayback playback:** snapshot `20220927024031` timed out after 469,627 bytes
  of an expected 510,021 and is retained as a partial raw file; it is excluded
  from the decisive table. The `20220929002552` and `20221211205012` gzip
  responses completed and are the historical evidence used.
- **FDA dashboard:** the live dashboard was accessible and its disclaimer/data
  limitations were observed, but its search extension did not reliably bind the
  typed product selection and no export could be verified. The official
  openFDA cosmetic-event endpoint was used and explicitly carries the older
  2025-08-31 currency ceiling.
- **HTTP captures:** two attempted FDA overview HTML downloads produced 10-byte
  404 bodies, and one obsolete e.l.f. URL produced a 404 page. These failure
  artifacts remain in the raw root and are not cited as evidence.
- **INCI pair scope:** only the two explicitly named, publicly listable e.l.f.
  and Glossier comparisons were run. Ruby & Millie and Trader Joe's products
  were not added because exact current official INCI surfaces were not bound by
  the handoff and expanding would not improve the named “identical” test.

## 7. Non-claims

- The Deliver run may say the sampled Sheer Skin Tint INCI and $42 price were
  unchanged between two late-2022 snapshots and the 2026-08-06 page, and that
  the product description was shortened and dropped its redness / pores /
  uneven-tone claim within that bracket. It may not portray the retained
  lightweight / sheer-color / natural-finish / hydration concepts as newly
  introduced, or date the change more precisely than the bracket.
- It may say Summer Fridays publicly acknowledged a Jet Lag Mask reformulation
  in 2021 alongside a statement responding to irritation reports and describing
  compromised third-party production batches. It may not infer a later
  2024-2025 reformulation from that event, treat the brand's own post as
  independent confirmation, or treat the statement as proof of causation.
- It may say two Summer Fridays Jet Lag Mask reports exist in the captured FDA
  endpoint data. It may not say the product caused the reactions, calculate a
  rate, rank brands, or treat no newer captured report as exoneration.
- Both captured FDA reports were initially received before the 2021-06-16
  statement. It may state that ordering. It may not join the two sources into a
  causal chain: nothing in this capture links either report to the batches the
  brand described as compromised, or to any specific lot code.
- It may say the e.l.f. and Glossier public lists are materially different from
  Summer Fridays and therefore are not ingredient-list-identical. It may not
  infer comparative safety, efficacy, concentrations, sensory equivalence, or
  formula identity from public INCI alone.
