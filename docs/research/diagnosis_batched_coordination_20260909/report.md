# Same Diagnosis, Batched Coordination — 2026-09-09

```yaml
retrieval_header_version: 1
artifact_role: Bounded empirical before/after experiment
scope: Three fixed evidence cases, six cold reader runs, initial and update stages.
use_when:
  - Evaluating diagnostic preservation and total token cost in this sample.
authority_boundary: retrieval_only
```

**Adoption is not supported.** Batching completed the sample with materially fewer measured tokens, but preserved the shared Softwear omission and introduced a transient completed-action error. Quality takes priority over cost. The two fixture corrections landed before calls; the replacement definition still exposes a scope ambiguity. No production method or stopped whole-corpus work was changed.

**Quality.** Both packaging arms retain one-to-seven arrival-leak accounts, two explicit loose tops, four bare agreements, unknown TikTok SKU, same-thread limits, offer versus dispatch versus delivery, and Softwear–Void pocket leakage alongside loyalty and intended repurchase. Both still omit the reviewer's reluctance to complain because they believe packaging comes from an outside manufacturer. Full mentions attributed manufacturing responsibility only: partial retention, not a pass. R01 and both actual baseline answers confirm this was a shared baseline omission; its check was not weakened.

Both hydration arms preserve direct versus mask/serum joint hydration, lightweight-versus-sticky descriptions, skin/amount/day-night conditions, 12-hour self-report, unavailable A07, A17 non-trial/shipping, repeated A18 context and other-product boundaries. Buffer Jelly gift/two-use/joint-use limits and Plasma Wash texture praise alongside cleansing failure, burning, dryness and contemplated return remain visible. No material hydration regression was observed.

Both buying updates preserve three acquisition accounts/six product-action categories, cart versus checkout, gifts, stock units versus events, adverse outcomes alongside loyalty and intended versus completed remedies. All new answers correctly retain A04 makeup-remover functional redundancy outside completed replacement. **Full initial counts A02 habitual skipping as completed routine discontinuation/replacement**, without a narrated transition from prior use. Full update retracts it; the first-pass failure remains. Its additional A05 count is a defensible wider reading: that source explicitly stopped disposable masks before discovering Avant Guard. The unchanged empty oracle assumes Experiment-linked replacement, whereas corrected discontinuation/substitution wording does not expressly exclude earlier other-product cessation. This residual definition ambiguity is not an invented event. No post-freeze correction or tuning occurred.

Incremental buying update also calls contextual Softwear stocking corroboration across community and retailer roles without a local independence/identity caveat. Content recurrence and the reported reason are supported; independent cross-role corroboration is not established. Similar over-credit existed in baseline full. This remains an unresolved support-credit concern, independently of the failures already blocking adoption.

There is **one mechanical mismatch among 80 checks** (full initial replacement set A02/A05); all final sets match. Mechanical agreement does not clear semantic omissions. [quality.json](quality.json) contains source-backed adjudication and [quality-initial.json](quality-initial.json) preserves first-pass findings. This is coordinator assessment, not independent review.

**Tokens and latency.** This table is the available checkpoint at **2026-09-09T13:35:03.848Z**, including preparation and grading to that point. [comparison.json](comparison.json) carries later available cutoffs and supersedes this table when refreshed. Late publication/closeout costs are not silently treated as zero.

| Native tokens | Cold baseline | Batched checkpoint | Reduction |
| --- | ---: | ---: | ---: |
| Coordinator | 11,194,579 | 2,706,088 | 75.83% |
| Readers | 518,066 | 444,917 | 14.12% |
| Combined | 11,712,645 | 3,151,005 | 73.10% |

Incremental readers: **236,480** versus 274,653 previously. Full readers: **208,437** versus 243,413 previously. Incremental remains **28,043 tokens / 13.45% more expensive than full**. Case totals incremental/full: packaging 65,995/66,226; hydration 101,839/71,967; buying 68,646/70,244. One incremental hydration retrieval of A07 contributes materially. Thirteen calls replaced baseline fifteen; stochastic retrieval differences are not an established batching effect.

Reader batch elapsed **189.452 seconds (3.16 minutes)**. End-to-end elapsed to the table's measurement snapshot was **8.28 minutes**, versus **26.52 minutes** for baseline. Native extraction verifies baseline coordinator 11,194,579 plus readers 518,066 = 11,712,645 combined, with baseline final counter 2026-09-09T13:14:17.484Z and duration 1,591.408 seconds. [baseline-native-counters.json](baseline-native-counters.json) contains counters/timestamps only, not conversation or reasoning.

All thirteen calls used observed **gpt-6-astra / medium / CLI 0.153.4**, matching baseline. The current commission's comparable-settings requirement governs the explicit medium override despite the usual project high default. Realized service tier is not exposed. Native event usage and session counters agree; there were no unmetered calls, failed launches, semantic retries or reader tool calls. All input plus output is counted; cached input and reasoning are subsets, never added twice. No dollar comparison is made.

Chronological checkpoint intervals include preparation, overlapping execution/assessment, grading and later publication/closeout. Precise activity attribution remains unallocated within mixed intervals. Native tool items and unique cumulative-usage observations are reported separately from reader calls, not claimed to reveal every internal inference step. [validation.json](validation.json) separately records bytes: source fixture 71,612; reader stdin 493,727; event stdout 142,503; reader stderr zero; final answers 131,835. Output bytes are not token savings.

**Design and verification.** The initial commission is authoritative. Work began clean at 46fbf6ffdc576b20014fab8ceea3fcedbf837a0c in the allocated 72b7 worktree, branch codex/diagnosis-batched-coordination-20260909. Selected account bodies, 31 contexts, packaging records and retailer source match pinned originals. Baseline and reference worktrees stayed read-only. [freeze.json](freeze.json) binds the two corrections, unchanged questions/splits/expected sets and reused runner. Review updated_at is separately preserved as review_updated_at; engagement observed_at is unavailable. [fixture-errata.json](fixture-errata.json) records every change.

Six case/arm jobs execute initial then update in one script. Initial findings are reader-authored. Incremental gets only its own findings, additions and retrieval catalog; full rereads all sources. Native checks verify exact stdin, no prior assistant/tool history, unique sessions, no resume/fork, no unexpected tools and no answer-key input. The unchanged authority wrapper embeds the current claim-support contract. Complete stdin/stdout/stderr/receipts remain in runs/; complete adjudication packs are case-pack-*.json. Run measure.mjs --check and validate.mjs to reproduce frozen identity/accounting; compare.mjs refreshes the available coordinator counter. Adaptations remain sample-local.

This is a **practical before/after comparison**, not causal proof of batching alone: corrected inputs, stochastic retrieval/output, coordination and incidental overhead changed. Three purposive overlapping cases cannot establish general non-inferiority, market coverage or production scalability. Supported semantic operation and owner-only reopen boundaries remain intact.

**Publication boundary.** publication.json records observed draft-PR state when available. Different-vendor operator-courier review and author adjudication remain mandatory before merge; neither has occurred. No merge or whole-corpus continuation. Parent finalizes residual late-call/final-response cost after task completion from the final native counter/timestamps at **C:/Users/vmon7/.codex/sessions/2026/09/09/rollout-2026-09-09T21-27-29-01a0865a-240b-73c2-8028-45fea9d93369.jsonl**. comparison.json names its own cutoff; do not recursively rewrite the report to chase the last token.
