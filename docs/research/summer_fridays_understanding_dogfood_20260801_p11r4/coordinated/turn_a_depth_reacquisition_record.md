# Summer Fridays p11r4 Phase A Depth-Reacquisition Record

```yaml
retrieval_header_version: 1
artifact_role: Understanding acquisition execution and closure record
scope: Acquire-and-Seal-only dogfood of the broad-company-Understanding evidence-depth contract for Summer Fridays p11r4.
use_when:
  - Auditing the p11r4 evidence-depth ledger, source admission decisions, saturation walk, or raw closure.
  - Distinguishing this Phase A continuation from any separately commissioned Deliver.
authority_boundary: retrieval_only
open_next:
  - docs/workflows/summer_fridays_understanding_dogfood_20260801_p11r4/coordinated/acquisition_seal.md
  - docs/research/summer_fridays_understanding_dogfood_20260801_p11r4/coordinated/evidence_depth_ledger.json
```

```yaml
cycle_id: summer_fridays_understanding_p11r4_20260801
subject: Summer Fridays
phase: Acquire
completion_profile: broad_company_understanding_v1
commission_boundary: Acquire and Seal only
implementation_authority_revision: 8786371a9439bfaba223806859be2ea0106c43b1
parent_seal: docs/workflows/summer_fridays_understanding_dogfood_20260801_p11r3/coordinated/acquisition_seal.md
parent_seal_role: immutable historical provenance; not current completion credit
deliver_started: false
```

## Confirm-Don't-Trust Intake

The p11 handoff, the p11r3 seal, the current Understanding authorities, and the
new v3 validator were fresh-read before continuation. The p11r3 v2 seal still
passes only with the explicit `--allow-legacy-v2` historical-audit switch. It
was not treated as proof that the current two-axis completion contract had been
met.

The launch worktree was clean at implementation revision
`8786371a9439bfaba223806859be2ea0106c43b1` before this record was written. A
fresh filename scan found no Deliver-named artifact in the p11, p11r1, p11r2,
p11r3, or p11r4 raw roots or their corresponding repository artifact trees.
This turn acquired and sealed only.

## Reusable Raw Closure

Every source-capture manifest below was fresh-loaded with the current
`SourceCapturePacket` model. Every declared preserved file was then read from
disk and checked against its recorded byte count and raw-byte SHA256.

| Raw root | Packet manifests | Preserved files | Fresh result |
| --- | ---: | ---: | --- |
| `C:\tmp\forseti-sf-review-corpus-completion-20260725-p07-r3` | 2 | 4 | schema, size, and SHA256 pass |
| `C:\tmp\forseti-sf-understanding-dogfood-20260725-p10\data` | 158 | 556 | schema, size, and SHA256 pass |
| `C:\tmp\forseti-sf-serp-social-composition-20260726\data` | 33 | 98 | schema, size, and SHA256 pass |
| `C:\tmp\forseti-sf-phase2-native-return-20260728` | 11 | 24 | schema, size, and SHA256 pass |
| `C:\tmp\forseti-sf-reddit-anchor-20260727` | 1 | 2 | schema, size, and SHA256 pass |
| `C:\tmp\forseti-summer-fridays-understanding-p11-20260731` | 232 | 933 | schema, size, and SHA256 pass |
| `C:\tmp\forseti-summer-fridays-understanding-p11r1-20260801` | 11 | 40 | schema, size, and SHA256 pass |
| `C:\tmp\forseti-summer-fridays-understanding-p11r2-20260801` | 11 | 19 | schema, size, and SHA256 pass |
| `C:\tmp\forseti-summer-fridays-understanding-p11r3-20260801` | 5 | 9 | schema, size, and SHA256 pass |
| `C:\tmp\forseti-summer-fridays-understanding-p11r4-20260801` | 17 | 34 | schema, size, and SHA256 pass |

The p11r4 manifest hashes and packet IDs are fixed below. A packet is admitted
to evidence-depth accounting only when its metadata says
`content_capture_allowed: true`; command exit zero is not admission evidence.

## p11r4 Capture Accounting

### Newly admitted outside-in sources

| Source job | Packet ID | Manifest SHA256 | Body bytes | Acquisition job performed |
| --- | --- | --- | ---: | --- |
| FemFounded company case | `01KYY371TQRV7QX2C9G9M3XPH2` | `a8ff747dcd8b92e52fbcc972d10ddddd61c3a45d7686cbcecfb2462e0d2330ff` | 95,737 | company/brand case context |
| Who What Wear perfume review | `01KYY385EJHZS76W1TQY4MRWQC` | `0789bf2b99ed6f2c293cf77d80ffa8a631f696fe557cb8c64b9e66177aebf0a8` | 1,210,510 | independent fragrance/product experience |
| Daily Beast Gap collaboration | `01KYY3938KNQTFHEXKQ0AAFWJH` | `e8116c6af4c73784b05303259e91af7e7def4e0e670ddc3d0e608179022e007f` | 633,591 | collaboration/channel extension |
| CEW CEO transition | `01KYY3BDHB7350M00EF04WBFY4` | `4ab89d9872af7df4fb5f10185cbc5ae87af1dfa2e27f1a8f5d2a242de5ceaddb` | 202,143 | leadership transition context |
| Moodie Davitt travel retail | `01KYY3BSHPSBPNWHQNWYHFVAQ8` | `9f813af2270e986ffd6a6389d6fafb3f31213e9b64e52cbb0e30cf1bf64a9ffd` | 200,675 | travel-retail channel expansion |
| BeautyScene fragrance launch | `01KYY3C5DZ55AJVGP28P9DQ28K` | `2a145f73188e77f2ac02b648a0df63184db5d2d82cee282c68f9caae9fd1024d` | 246,698 | fragrance/category launch |
| Grazia brand profile | `01KYY3D34PH871PF6M35A7G8KP` | `32f0707b558e4075f06a6f20f8607e987348ae5f4f766aab69573f1bac371f69` | 471,432 | international brand/retail profile |

These seven bodies each contain the subject name and were manually assigned a
distinct source origin. “Independent origin” here means a distinct publisher
or institution rather than a brand-owned copy or detected syndication; it does
not mean conflict-free editorial independence.

### Terminal refusals and excluded packets

| Attempt | Packet/diagnostic outcome | Disposition |
| --- | --- | --- |
| Parade | packet `01KYY36BQXZE03DKTAGSJ28EFT`; HTTP 403; `datadome_header`; manifest `44a6f6d168f95d8712f82c767e9c97bc1791ea2b66d30a800738c19a29624ef7` | refused; no depth credit |
| Editorialist | packet `01KYY36P7V0RP4WQYCFJDNSNX6`; HTTP 405; `aws_waf_header`; manifest `ec4f0caf679b3ceec1e6057536af7c82da93b5175c76f07e936cdd6833e8731b` | refused; no depth credit |
| Allure | packet `01KYY37J2V7EK7GC4VGZT50QYW`; HTTP 200 but `login_page`; manifest `119282c08a764266ecdf41a4f3bf1d2d32af4144cdafc631f6a7443d0dd34a10` | fail-closed false positive; no depth credit |
| Marie Claire | packet `01KYY38M52YVXAMPY3BJ1GH800`; HTTP 200 but `login_page`; manifest `375202386d114eb1c72bc6718ba7c4ef9edeb4e35ecac5f87df08a3fbbd19438` | fail-closed false positive; no depth credit |
| Yahoo Finance | packet `01KYY3CNYR31GV6VXJZHQA90V7`; HTTP 200 but `login_page`; manifest `47299594fbede474eb12d3de527f10fe814ae457a791a08b6795eda6dfd678e0` | fail-closed false positive; no depth credit |

The three 200 responses above demonstrate the precise reason HTTP status alone
cannot clear acquisition admission. Their bodies are preserved as diagnostic
provenance, not source evidence.

### Community and legal/regulatory continuation

| Source job | Outcome | Evidence use |
| --- | --- | --- |
| PissedConsumer service reviews | admitted packet `01KYY3Y51RQ39GWMZC8Z26WAG9`; manifest `9d6b8620f1ad5e392bb0a6a0dd39b996407e5967b8b0334d1136ee477c16286a`; 654,214 body bytes | bounded DTC service/fulfillment seam |
| Trustpilot | preserved HTTP 403 packet `01KYY3QYPTQ8M1Z1ZDP8Y56K6N`; manifest `e04828ad572802607760a54d9b09076e0659698360ac3d884ccd58ed902875d1`; browser recovery lost its execution context | no evidence credit; service seam is otherwise bounded, not claimed representative |
| EU General Court / EUIPO matter | admitted packet `01KYY3SB8J9QCQ2X3HXP5KVVEV`; manifest `93693df5f48005fa07c467f3e8b2bcad32d952441a21cd6e247e0e2b0020f07a`; 274,306 bytes | bounded trademark/legal-history seam |
| California Proposition 65 notice | admitted packet `01KYY3T2N153NXR0GWPP0DQVNF`; manifest `baf8ab05d6b61d6fed0f641b9f2477b6981c7de7aec0a473f581d88bd35821f7`; 132,852 bytes | notice existence only; no liability or medical conclusion |
| WIPO domain decision | admitted packet `01KYY3YGJN591X520GMECQBCVT`; manifest `e2769cc7676f07368c1ea202276c7feb04dda8e4d7c3bd8cb8ad1b3dd1c19072`; 173,606 bytes | bounded counterfeit/domain-enforcement seam |
| Korean Consumer Agency item | Direct HTTP failed certificate verification and the allowed browser route timed out | no evidence credit and no claim derived from the search result |

## Evidence-Depth Result

The accompanying ledger enumerates the units and lets the v3 validator derive
the metrics rather than trusting these reported totals.

| Family | Derived depth | Source ceiling |
| --- | --- | --- |
| Outside-in | 12 units from 12 distinct origins | origin diversity, not a complete press census or proof of publisher neutrality |
| Retailer reviews | 975 provider-visible unique rows across Revolve, Amazon, and Sephora; more than five product contexts; six categories; low/mid/high ratings present | exact-ID/text dedupe within each corpus; zero exact cross-provider identity collisions observed, but semantic cross-provider duplicates and shared-review-feed linkage remain unresolved |
| Reddit/forum | 20 distinct thread IDs across six communities and six topic categories | qualitative tension discovery, not sentiment prevalence or a representative Reddit sample |
| Native social | 36 distinct source-native posts from 23 creators on TikTok, Instagram, and YouTube with positive, mixed, critical, and neutral evidence | discovery was query-selected and tension-seeking; creator-landscape and narrative-prevalence claims remain excluded |

The social count treats separate source-native posts as separate evidence units
even when one creator authored more than one. Creator depth is deduplicated by
creator ID. The 12 official Instagram posts count as 12 distinct content units
but one creator, so volume cannot manufacture creator diversity.

The official-post rows were fresh-read from packet
`01KYF1RQRX0M3KM2K2BKGDNV6G` at
`C:\tmp\forseti-sf-serp-social-composition-20260726\data\raw\c42\01KYF1RQRX0M3KM2K2BKGDNV6G`.
Its manifest raw-byte SHA256 is
`ebd2f9c55c1768ce080da27931159c36d9bcfce3be016e0bcc6ae1bc1140ee9d`;
its 12 hash-verified call files name, one each, `DbONTyYSmTS`,
`DbMHFSlkl3x`, `DbJDdz6FL_P`, `DYkQGiSFJVQ`, `DbGgXb7ynHH`,
`DbLnqyuFD67`, `DXwwFV1FI7h`, `DYr-dtXy3XE`, `DZsWUUJS9vn`,
`Dav6X6ckua9`, `DZ8QMCwEpGw`, and `Da8LUpMFN5X`.

## Adaptive Saturation Walk

Five bounded search batches followed the profile floors. The first three were
material and triggered focused capture; the last two were dry.

| Batch | Focus | Result |
| --- | --- | --- |
| 1 | product/category and DTC experience | added a DTC service/fulfillment seam; material |
| 2 | structural/legal/regulatory records | added trademark and regulatory-notice seams; material |
| 3 | service corroboration and counterfeit/domain evidence | sharpened service and added domain-enforcement evidence; material |
| 4 | positive service, long-term Jet Lag use, body category, authorized/counterfeit channels | corroborated existing seams only; no new material seam or changed disposition |
| 5 | value/dupes, international Sephora, creator marketing, formula/packaging | corroborated existing seams only; no new material seam or changed disposition |

The practical next moves are either dominated by already admitted evidence,
blocked without an allowed route, or non-material to the bounded qualitative
Understanding. Trustpilot and the Korean Consumer Agency item remain explicit
source-level misses. The four missing Amazon exact-product PDP baselines and
comprehensive Space NK US evidence remain excluded from exact-product/channel
claims; neither gap blocks the bounded company-level qualitative acquisition.

## Dogfood Process Finding

The first deliberately invalid Direct HTTP timing invocation exposed that the
runner validated timing metadata after making the request. That probe left no
packet, but it performed network work before failing. The implementation now
constructs and validates `PacketTiming` before capture and updates only the
capture timestamp after a successful response. A regression test proves invalid
timing fails before both network access and output-directory creation.

The single-URL Direct HTTP CLI still may exit zero for a preserved refusal; the
packet metadata's `content_capture_allowed` value remains the authoritative
admission decision. The existing same-host batch wrapper consumes that
decision. This p11r4 ledger also excludes all packets whose owning metadata did
not admit content. Changing the standalone CLI's exit contract is left for the
commissioned de-correlated review because it may affect existing callers.

## Terminal Phase A State

The two-axis anti-token floors are met, echo/syndication handling is explicit,
all material seams have a terminal disposition, and the final two practical
batches added no material value. The p11r4 acquisition can therefore receive a
v3 seal with no pending Phase A work. This statement does not make the evidence
market-representative and does not start Deliver.
