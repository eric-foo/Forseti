# Summer Fridays Google Ads Transparency Capture Return — 2026-07-26 v0

```yaml
retrieval_header_version: 1
artifact_role: Capture return artifact
scope: >
  Bounded acquisition return for the verified Summer Fridays, LLC advertiser
  visible on the public Google Ads Transparency Center under the recorded
  United States, Any time, All platforms, All formats state. Preserves all 416
  distinct creative IDs materialized after ten continuation actions, with
  source format, date, and media-resolver metadata for the first 60, identity
  proof, typed omissions, and exact evidence bindings for later Deliver-side
  use.
use_when:
  - Reading the observed Summer Fridays Google Ads Transparency inventory captured on 2026-07-26.
  - Resolving all 416 materialized creative IDs through the companion JSON projection.
  - Checking source-visible Google creative formats, dates, media posture, and the few safely resolved product or offer signals.
  - Planning a later cross-source join without treating this return as spend, targeting, performance, or strategy evidence.
authority_boundary: retrieval_only
open_next:
  - docs/research/summer_fridays_ci_inputs_20260726/google_ads_transparency_observed_creative_ids_20260726.json
  - docs/prompts/handoffs/summer_fridays_google_ads_transparency_capture_handoff_20260726_v0.md
  - forseti/product/spines/capture/core/source_capture_toolbox/source_capture_playbook_v0.md
  - forseti/product/spines/capture/core/source_capture_toolbox/capture_recon_index_v0.md
stale_if:
  - Google materially changes advertiser identity, filter, result-card, detail-page, or continuation behavior.
  - Advertiser AR00430838150965755905, the portfolio authority, or the raw lake is recaptured or superseded.
  - A dedicated accepted Google Ads Transparency Center recipe or runner supersedes this first probe.
```

## 1. Executive acquisition conclusion

The public Google Ads Transparency Center resolved a **verified**
`Summer Fridays, LLC` advertiser based in the United States, advertiser ID
`AR00430838150965755905`. Under `Ads in United States` / `Any time` /
`All platforms` / `All formats`, the source header displayed `~500 ads`; its
card labels declared a 456-ad result set. Ten bounded scroll continuations
materialized **416 distinct source creative IDs** in the retained DOM.

The original handoff enumerated the **first 60 distinct IDs in source DOM
order**. A 2026-07-27 continuation now preserves all **416** materialized IDs
and their direct detail locators in
`google_ads_transparency_observed_creative_ids_20260726.json`. The result
remains **PARTIAL** because the source declared 456 cards and no exhaustion
signal was reached. Direct-detail metadata remains resolved only for the first
60: **39 Text, 16 Image, and 5 Video**. Ten were last shown `26 Jul 2026`; 50
were last shown `25 Jul 2026`.

Google rendered most creative content through either an archive-image asset or
a Google preview script. The public page did not expose stable machine-readable
headline/body/CTA/destination fields for most rows. This return therefore does
not promote rendered pixels, opaque script payloads, or image aspect ratios
into copy, landing-page, placement, product, or strategy claims. One offer is
retained because an admitted screenshot independently preserves it.

## 2. Route verdict and recipe card

**Verdict:** `REUSE_WITH_TYPED_LIMITS`. The anonymous public route is stable
enough for advertiser identity, result enumeration, source creative IDs,
region, last-shown date, source format, variation count, and source media
resolver handles. It is not sufficient by itself for complete copy or
destination extraction.

### First-probe recipe

1. Open `https://adstransparency.google.com/?region=US`.
2. Search the company domain, `summerfridays.com`, to discover candidate
   advertisers. Do not accept the domain result as identity proof: Google
   explicitly says a domain can include ads from multiple advertiser accounts.
3. Select the verified `Summer Fridays, LLC` result and bind advertiser ID
   `AR00430838150965755905`, verified status, and United States base.
4. Freeze `region=US`, `Any time`, `All platforms`, `All formats`, and source
   default order. The captured surface exposed no separate sort control or
   textual sort label.
5. Scroll at human rate up to ten times. Extract creative IDs from first DOM
   occurrence order and deduplicate responsive duplicate cards.
6. Stop at 60 IDs or ten continuations, whichever occurs first. If the source
   shows a larger result set, return `PARTIAL`.
7. Dereference each retained ID at
   `https://adstransparency.google.com/advertiser/AR00430838150965755905/creative/{CREATIVE_ID}?region=US`.
8. Preserve source-declared metadata and resolver handles. Treat copy,
   destinations, and product bindings as unresolved unless the source exposes
   them directly.

This is an Ads Transparency Center recipe only. It does not import the
ordinary Google SERP route.

## 3. Advertiser identity proof and rejected ambiguities

Identity was bound before inventory acceptance:

1. Company-owned packet `01KYF2KFD2JZM2DS1E7T67S3MK` retained
   `https://summerfridays.com/`.
2. A Google Ads Transparency Center search for `summerfridays.com` returned a
   verified `Summer Fridays, LLC` advertiser based in the United States.
3. The exact advertiser locator is
   `https://adstransparency.google.com/advertiser/AR00430838150965755905?region=US`.
4. The retained inventory and direct-detail pages render `Summer Fridays, LLC`
   under that same advertiser ID.

The domain search also surfaced verified advertiser
`BENTON MAPLERISE RETAIL LLC`. Google stated that the searched domain included
ads from multiple advertiser accounts. That candidate was rejected: a shared
destination domain is not company identity authority.

## 4. Filter, window, and enumeration receipt

- **Advertiser:** `Summer Fridays, LLC`.
- **Advertiser ID:** `AR00430838150965755905`.
- **Verification/base:** source-verified; based in United States.
- **Region:** `Ads in United States` / URL `region=US`.
- **Date window:** `Any time`.
- **Platform:** `All platforms`.
- **Format:** `All formats`.
- **Order:** source default; no sort label/control was exposed.
- **Session posture:** public anonymous; no stored Google login, cookie,
  paid-ad profile, or credential was used.
- **Proxy posture:** none requested or loaded; no physical-US-local claim.
- **Capture/extraction window:** `2026-07-26T11:22:43Z` through
  `2026-07-26T11:55:19Z`.
- **Source header:** `~500 ads`.
- **Source card denominator:** 456.
- **Distinct IDs materialized after ten continuations:** 416.
- **Enumerated here:** first 60 distinct IDs in source DOM order.
- **Status:** `PARTIAL`; neither the 60-ID cap nor the ten-continuation cap
  represents source exhaustion.

The rounded header count, card denominator, and materialized-ID count are
different source states, not interchangeable measurements.

## 5. Unique-ad inventory

Every row inherits:

- advertiser `Summer Fridays, LLC`, advertiser ID
  `AR00430838150965755905`;
- region `US`, date window `Any time`, platform `All platforms`, source-default
  order, and capture window from section 4;
- first-shown date: **not exposed on the captured direct-detail surface**;
- exact source pointer:
  `https://adstransparency.google.com/advertiser/AR00430838150965755905/creative/{CREATIVE_ID}?region=US`;
- headline/body/CTA/destination/product/collaboration: **not text-resolved**
  unless section 6 records an explicit exception;
- inventory evidence: packet `01KYF2MS14047RNMVTE3K5RZFA`, retained DOM
  `raw/01_cloakbrowser_rendered_dom.html`;
- detail evidence posture: every direct source pointer was checked; rows 1–4
  are additionally retained as packets `01KYF2VFQV9C5B4SFQA1D7NQAY`,
  `01KYF4E7E25CNZCW6RVC5W3X4B`, `01KYF33QXKMEWYWS8M22PTVSX7`,
  and `01KYF4F5GJEBP2SH0CQNCKPQHD`.

`R:<id>` means a source-resolved
`tpc.googlesyndication.com/archive/simgad/<id>` archive image. `P:<id>` means a
source-resolved Google preview script carrying internal `creativeId=<id>`.
These are media-resolver handles, not deduplicated-message or placement claims.

| # | Creative ID | Last shown | Format | Variations | Media resolver |
|---:|---|---|---|---|---|
| 1 | `CR13584248810057498625` | 26 Jul 2026 | Image | 1 | `P:812513489022` |
| 2 | `CR15947794189496877057` | 26 Jul 2026 | Image | 2 | `P:812615426045` |
| 3 | `CR14117226841009815553` | 26 Jul 2026 | Text | 3 | `R:18077530722337079300` |
| 4 | `CR14783016006762627073` | 26 Jul 2026 | Text | 1 | `R:11341754747887622795` |
| 5 | `CR06340229588483833857` | 26 Jul 2026 | Text | 2 | `R:4506633541760647655` |
| 6 | `CR04147944801611808769` | 26 Jul 2026 | Text | 3 | `P:815363438368` |
| 7 | `CR10667934104466489345` | 26 Jul 2026 | Text | 2 | `R:12306560403901926559` |
| 8 | `CR13847218456316870657` | 26 Jul 2026 | Text | 3 | `R:10302797198329127633` |
| 9 | `CR05348663768895193089` | 25 Jul 2026 | Text | 2 | `R:4731224334099220307` |
| 10 | `CR02377756644537794561` | 26 Jul 2026 | Image | 3 | `P:808934581874` |
| 11 | `CR00392223912483618817` | 26 Jul 2026 | Text | 2 | `R:9695587682102665510` |
| 12 | `CR03982226409073410049` | 25 Jul 2026 | Text | 1 | `P:815329106373` |
| 13 | `CR04018851141394628609` | 25 Jul 2026 | Image | 3 | `P:815331554106` |
| 14 | `CR01027087149041713153` | 25 Jul 2026 | Image | 3 | `P:812515891914` |
| 15 | `CR07739077871032860673` | 25 Jul 2026 | Image | 2 | `P:812618627645` |
| 16 | `CR17362749458399363073` | 25 Jul 2026 | Text | 2 | `R:16081297543673866284` |
| 17 | `CR16912771773521461249` | 25 Jul 2026 | Image | 1 | `P:807831001429` |
| 18 | `CR13479715490825764865` | 25 Jul 2026 | Text | 3 | `P:810497114065` |
| 19 | `CR13534640537629360129` | 25 Jul 2026 | Image | 2 | `P:774757680716` |
| 20 | `CR15921950237405478913` | 25 Jul 2026 | Image | 3 | `P:804051807573` |
| 21 | `CR08025398670365032449` | 25 Jul 2026 | Text | 3 | `R:633268771256604592` |
| 22 | `CR13562296922969997313` | 25 Jul 2026 | Image | 1 | `P:810497195671` |
| 23 | `CR12370433697214627841` | 25 Jul 2026 | Image | 3 | `P:690229024056` |
| 24 | `CR13392758938705854465` | 25 Jul 2026 | Image | 2 | `P:755454773690` |
| 25 | `CR03491707608765562881` | 25 Jul 2026 | Text | 2 | `R:2996321404568847099` |
| 26 | `CR09781207483090468865` | 25 Jul 2026 | Text | 2 | `R:17314556084315195718` |
| 27 | `CR06783880236778913793` | 25 Jul 2026 | Image | 1 | `P:795594785451` |
| 28 | `CR18340538740889354241` | 25 Jul 2026 | Text | 1 | `R:11004873130755898007` |
| 29 | `CR09014735633855283201` | 25 Jul 2026 | Image | 2 | `P:733798138302` |
| 30 | `CR08252643903937708033` | 25 Jul 2026 | Text | 1 | `R:10288708106090597766` |
| 31 | `CR06625242286806532097` | 25 Jul 2026 | Text | 3 | `R:6611754721095397716` |
| 32 | `CR04447724722779586561` | 25 Jul 2026 | Text | 3 | `R:17085871124843157953` |
| 33 | `CR05703053821274488833` | 25 Jul 2026 | Text | 1 | `R:9525105144540490526` |
| 34 | `CR15109712273226072065` | 25 Jul 2026 | Text | 3 | `R:18323468848107167702` |
| 35 | `CR13554569555249987585` | 25 Jul 2026 | Text | 2 | `R:7862063556615547583` |
| 36 | `CR14008619685168283649` | 25 Jul 2026 | Text | 1 | `R:7285510716853927893` |
| 37 | `CR04634178968314970113` | 25 Jul 2026 | Text | 3 | `R:49884094305887327` |
| 38 | `CR00968371235253649409` | 25 Jul 2026 | Text | 1 | `R:1511149107041309042` |
| 39 | `CR16151460894428102657` | 25 Jul 2026 | Image | 1 | `R:15182475860452102681` |
| 40 | `CR05121946068975616001` | 25 Jul 2026 | Text | 2 | `R:2084877971170940607` |
| 41 | `CR17148896293632868353` | 25 Jul 2026 | Video | 1 | `P:807024849291` |
| 42 | `CR14695237629830496257` | 25 Jul 2026 | Text | 1 | `R:13834508638785041281` |
| 43 | `CR02260128141819248641` | 25 Jul 2026 | Text | 3 | `R:6659395883194162207` |
| 44 | `CR17240840178956763137` | 25 Jul 2026 | Text | 1 | `R:1764372436037224043` |
| 45 | `CR13795018566262587393` | 25 Jul 2026 | Text | 1 | `R:4689002300402221648` |
| 46 | `CR03397751316515127297` | 25 Jul 2026 | Text | 3 | `P:811495363611` |
| 47 | `CR06072420484744478721` | 25 Jul 2026 | Text | 3 | `R:4761786421650844801` |
| 48 | `CR13775161480754233345` | 25 Jul 2026 | Text | 3 | `R:17213922319539997880` |
| 49 | `CR09138444710753337345` | 25 Jul 2026 | Video | 1 | `P:697388862916` |
| 50 | `CR02348939449796132865` | 25 Jul 2026 | Text | 1 | `R:12685231125301230488` |
| 51 | `CR01431416100431593473` | 25 Jul 2026 | Text | 3 | `R:11197854834498330699` |
| 52 | `CR04005445139714539521` | 25 Jul 2026 | Text | 2 | `R:10368057755521805962` |
| 53 | `CR10836698376142061569` | 25 Jul 2026 | Video | 1 | `P:774569802207` |
| 54 | `CR09884880640631898113` | 25 Jul 2026 | Video | 1 | `P:800200709659` |
| 55 | `CR11744334891179835393` | 25 Jul 2026 | Text | 3 | `R:6761178763391921920` |
| 56 | `CR15129690511171911681` | 25 Jul 2026 | Text | 3 | `R:1010763408485559024` |
| 57 | `CR05494546722560409601` | 25 Jul 2026 | Image | 2 | `P:800277539708` |
| 58 | `CR18212873904622403585` | 25 Jul 2026 | Text | 3 | `R:11784298466404669912` |
| 59 | `CR04133130050658631681` | 25 Jul 2026 | Text | 3 | `R:17325107355068690777` |
| 60 | `CR00670730319468429313` | 25 Jul 2026 | Video | 3 | `P:700507743971` |

There are 60 distinct source IDs and 60 distinct source resolver handles in
this window. Linked creative bytes were not all independently downloaded and
hashed, so visual or byte-identical creative equivalence is **not asserted**.

## 6. Source-resolved offer exception

Only this exception overrides the shared unresolved fields in section 5:

| Creative ID | Independently retained detail | Family/object binding | Destination / offer |
|---|---|---|---|
| `CR14117226841009815553` | packet `01KYF33QXKMEWYWS8M22PTVSX7` screenshot visibly renders `Take 10% Off Your First Order - Save 10% Off Your First Order` | brand-level; no product family named | 10% off first order; destination not exposed |

## 7. Creative/message clusters and product-family coverage

### Source-declared format clusters

| Cluster | Rows | What is safely observed |
|---|---:|---|
| Text | 39 | Google source format `Text`; most copy rendered as an archive image or opaque preview rather than page text |
| Image | 16 | Google source format `Image`; no placement or visual-message inference |
| Video | 5 | Google source format `Video`; no full playback, duration, transcript, or frame-level analysis retained |

The comparison authority was freshly read from
`C:\tmp\forseti-sf-understanding-dogfood-20260725-p10\data\co1\13_portfolio_parent_disposition_v1\portfolio_parent_disposition_v1.json`,
SHA-256
`8B4BE38929B167A1EB1AEBFFE5EA2813A0172DFEDD3525188F534E634E2BD212`.
It resolves 27 current/exposed families and seven historical-only families.

No product-family title is independently preserved in the admitted packet
bundle. Product-family rows safely resolved: **0**.

### No-observed-family statements

**None asserted.** Although the portfolio authority is fresh, most Google
creative copy is rendered inside source image/script media and was not
source-resolved as text. Declaring the other portfolio families “not observed”
would convert an extraction limitation into an absence claim. A later
pixel/media review may add bounded no-observed rows only after all 60 retained
media records are actually resolved.

## 8. Failures, omissions, and typed limits

1. The initial domain search was useful for discovery but explicitly mixed
   advertisers. It was rejected as identity authority.
2. The exact advertiser inventory packet was written successfully, but its
   visible-text sufficiency regex expected creative IDs in page text. Google
   stored the IDs in rendered DOM attributes, so the runner recorded
   `source_detail_sufficiency_failed`. A direct DOM check found 416 distinct
   IDs. The typed failure is retained; the packet was not rerun or rewritten.
3. Responsive markup duplicated visible cards. IDs were deduplicated by first
   DOM occurrence before the first-60 ceiling was applied.
4. Eleven rapid direct-detail reads initially returned an application shell
   without metadata. Fresh, slower reads resolved all eleven. These were
   retrieval gaps, not ad absence.
5. The public detail surface exposed `Last shown` but not `First shown`.
6. Google labels some rows `Text` while rendering their copy as an archive
   image. The label and media resolver are both retained without pretending
   that the page exposed machine-readable headline/body/CTA fields.
7. Linked preview-script, image, and video bytes were not all independently
   preserved. Visual deduplication and byte-identical creative reuse are
   unresolved.
8. Video playback, duration, audio, transcript, and frame content were not
   captured.
9. Sign-in was not required for the visible advertiser inventory. Google's
   notice that some age-restricted ads require sign-in remains a public-surface
   coverage limitation, not evidence that any specific Summer Fridays ad was
   hidden.
10. An attempted all-row detail packetization batch reached its 60-second
    command bound after successfully admitting rows 2 and 4. It was not
    continued: the inventory packet already retains every row's source ID and
    resolver handle, while every row carries its exact public detail pointer.
    The two completed packets remain admitted and are listed below.
11. No source exhaustion signal was reached. IDs 61–416 materialized in the
    retained DOM but are intentionally not enumerated here; the source card
    denominator was 456.

## 9. Source evidence bundle

Raw lake:
`C:\tmp\forseti-sf-google-ads-discovery-20260726\data`

Lake identity: epoch `v4.1`, root UUID
`01KYF2KDSBXWF38D8DWE12GCQG`.

| Packet | Role | Manifest SHA-256 | Preserved-file SHA-256 |
|---|---|---|---|
| `01KYF2KFD2JZM2DS1E7T67S3MK` | company homepage identity | `7b389992f30ec7576b61b0eefa47da1e5f317d88b6fac29df70caa9bfc1c608a` | body `eb6a0cdebb78086f64f0130541657af2c1424ca7053294629452dca926fa26d7`; metadata `f6780a163f29aa6ba35bb1656b0160746c26729a9295de875692677815e8fa48` |
| `01KYF2MS14047RNMVTE3K5RZFA` | exact advertiser inventory; ten continuations | `16ba067458894b70e6f1210422c933ffe866e3f9f398f667e990bca436d52d65` | DOM `3c6d8548be0e43ca43b9b07f799dd2f8f1cc62f3f52471d23c9fd31a3c689963`; text `3d1b2a3d43de68e9dd79b47d55d852645aaa6499c7347a4e2b80f765c2ba2367`; screenshot `0e3295df3ff2a87db4b11b3504bc07435b7b3f2f9452d28527a622321cc2f870`; metadata `916fe9ca0dd9088ec5f23ee09c4abd89b07618fefa4d9e66f32f8a9716cd9aa4` |
| `01KYF2VFQV9C5B4SFQA1D7NQAY` | representative Image-format direct detail, row 1 | `ceb90466e2f8e203ac9d8fd5dc080e54a964e2c08eeedae207ba1d9d2ccab960` | DOM `ff97a7d5e9583f67426c547a45e879c2c1a4b9bc3db307e6147639e9e74d5da3`; text `d33817f230954a6ae3f0a5cd8ae3d571201d33fd12e86a65f6f5f9338be69cdc`; screenshot `15c837a11a8f56f739444f488719ec78b8f1840ddf537e2ad56b6de48bdf3599`; metadata `f82d74d14af0f0d8f9269beed6f1475e3bdd63a4f7269704920624245308dd90` |
| `01KYF4E7E25CNZCW6RVC5W3X4B` | Image-format direct detail, row 2 | `fbff86afb0ee45f946aa031bd2a043fda70a792008144f00e894991f53bf29f5` | DOM `3e104757bbaf6d0d3d5b16c699755e5a9fa2fe602a81b8030bbef48060afac09`; text `07c4386c249225c674f75815162b20d5b7160a7973d2e4fc7a17e53e92d87627`; screenshot `8ea249fc4aaec99a84f27af18ee164afdea8c748d6c5363854c10469e1ec6956`; metadata `614984a8392aae4d827ea009ceb43f3aa8ceccc7652f7d9fd75556064a1009f2` |
| `01KYF33QXKMEWYWS8M22PTVSX7` | representative Text-format direct detail, row 3 | `1c27b895f1561c4b33c5f06c2e627c494a856f7862db32ea31fefb3f4d75fd33` | DOM `d8d281199750f017b1a796ad9a861f1ab519e90c2a051464bbaea50aa09f9319`; text `56c931d8772714dfc359aaf1b0ed32b5a332cebc36891f36e8c79524ba209887`; screenshot `cf602e64a4d28efefab5032cccecd8d4c637b134c93468b1f9e4d70ba74c1e80`; metadata `3b6621a9db99aff0fa9355103d9a49ebb7e3a60d9cd512a428d05a0893046dd9` |
| `01KYF4F5GJEBP2SH0CQNCKPQHD` | Text-format direct detail, row 4 | `8db4e5e8bf05100384b7ee7b345f024516496c4062b22410a818308339f3fcbc` | DOM `4bf7a1be816770002e082546487bb118355c550a23838d60822553a1addb0bc6`; text `3b41192f74cb8c033ab8a5d43e3155a0753c92f125311f22fcb190c3c275dfc5`; screenshot `ede1bde870000b34f557e2f8770333dcbbb0567d25a0608465493ecd52871d3f`; metadata `ca1229e043346789ffc230cc6052f5dc412855488748a2012465f5fcd7490a3e` |

Current controlling-source hashes matched the handoff compare targets:

- source capture playbook:
  `AAC268200599B047C1A1A8096ED2F683197F484475761C20649A86740494D3F5`;
- capture recon index:
  `22BA2475317A731FC1AEB55CE7AB8004AD39BDC82D44DFB5E0F14C4C68244D58`;
- ordinary Google SERP boundary decision:
  `5A079E37F9311709C10D0D329386CC4588B2FAB4A4B43F8DAAFA1DD28E2A0B94`.

No accepted Google Ads Transparency Center source-family recipe was present at
the receiver checkpoint.

## 10. Safe later-Deliver uses and non-claims

Safe later uses:

1. Use
   `google_ads_transparency_observed_creative_ids_20260726.json` as the durable
   ordered inventory of all 416 IDs materialized in the retained DOM.
2. Join the first 60 source creative IDs' last-shown dates, formats, variation
   counts, and resolver handles to other independently captured evidence.
3. Preserve product-family fields as unresolved unless a later retained-media
   review produces independently dereferenceable evidence.
4. Use the ten-continuation ceiling and source-default order as a capture
   receipt; use the first-60 boundary only for the enriched detail subset.
5. Commission a later retained-media review before adding copy-level message
   clusters or no-observed-family rows.

Non-claims:

- not an exhaustive Google advertiser inventory;
- not a spend, budget, bid, impression, reach, frequency, audience, targeting,
  delivery, conversion, performance, ROAS, or strategy record;
- not proof of Search, YouTube, Display, Shopping, or any other placement unless
  Google later exposes that label per row;
- not proof that source-default order represents advertiser priority or
  performance;
- not a visual-deduplication or full-creative-transcription result;
- not evidence that unresolved product families, offers, destinations, or
  collaborations are absent;
- not a cross-source CI synthesis or Deliver conclusion.

## 11. Full observed-ID projection — 2026-07-27 continuation

The companion
`google_ads_transparency_observed_creative_ids_20260726.json` was generated
from the admitted inventory packet's stored DOM, not from a new Google
request. It:

- binds advertiser `Summer Fridays, LLC` and
  `AR00430838150965755905`;
- binds the recorded United States / Any time / All platforms / All formats
  filter state;
- pins source packet `01KYF2MS14047RNMVTE3K5RZFA` and DOM SHA-256
  `3c6d8548be0e43ca43b9b07f799dd2f8f1cc62f3f52471d23c9fd31a3c689963`;
- extracts `creative/(CR\d+)`, retains first DOM occurrence, and projects 416
  ordered creative IDs with exact public detail URLs; and
- preserves the 456-card denominator and unresolved source-exhaustion gap.

The projected JSON SHA-256 is
`c7a23f789ef89b321aff4972633cff7a2e720d4c21dfe5f5274e3c14804b5607`.

This closes the durable-ID projection gap. It does **not** close creative-media
interpretation: copy, product family, offer, destination, placement, visual
deduplication, or performance remain unresolved outside the bounded first-60
metadata and the one screenshot-preserved offer.

Google describes the Ads Transparency Center as a searchable hub of ads served
from verified advertisers across Search, YouTube, and Display:
<https://safety.google/safety/ads-data/>. That makes it the appropriate public
Google-ad evidence surface for the verified Summer Fridays advertiser. It does
not make this local projection exhaustive: 416 IDs materialized against a
456-card denominator, no source-exhaustion signal was reached, and brand-related
ads paid for by a retailer, partner, agency, affiliate, or another verified
advertiser would not necessarily appear under this advertiser identity.
