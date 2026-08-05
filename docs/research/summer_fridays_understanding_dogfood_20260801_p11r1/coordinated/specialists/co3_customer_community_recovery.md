# Summer Fridays Understanding p11r1 — CO3 Recovery Delta

```yaml
retrieval_header_version: 1
artifact_role: Customer/community acquisition recovery return
scope: Settles the p11 Reddit, native TikTok, and native Instagram pending jobs without changing the parent retailer or YouTube evidence.
use_when:
  - Combining the immutable p11 CO3 return with p11r1 recovery evidence.
authority_boundary: retrieval_only
```

## Terminal Accounting

```yaml
status: BLOCKED_TERMINAL
reddit_community_scout: {planned: 3, completed: 0, blocked: 1, unrun: 2}
native_tiktok: {planned: 5, completed: 1, blocked: 2, unrun: 2}
native_instagram: {planned: 4, completed: 4, blocked: 0, unrun: 0}
native_youtube: {planned: 1, completed: 1, blocked: 0, unrun: 0, source: reused_parent}
```

## Reddit

One exact Phase 1 trigger received the packet's single guarded
`old.reddit.com` CloakBrowser fallback. Packet `01KYWW44HKRRRDDFE6FGF0BSY5`
(manifest SHA256
`939906944e93cb8c45cce7b2b6164cadd3daa87a0fef5c5e4ec66d9202115370`)
preserved a 143-byte `reddit_network_security_block`, not a complaint body.
The parent direct route had already returned HTTP 403, so the fallback result
stops J-CO3-01 without replaying the other six triggers. J-CO3-02 and
J-CO3-03 remain unrun because their required complaint bodies and paired
rendered/native evidence do not exist.

## TikTok

The hardened runner bound the retained session label to the actual Chrome
process serving its CDP endpoint before use. It rejected an unrelated live
endpoint and then admitted one exact video through the correctly bound profile:

- `CO3-NATIVE-TT-7232313070897483051` completed as packet
  `01KYWVWQFQNT67GD5G5P5MMJ5E`, manifest SHA256
  `fb5557b9e960ae1049b4841ac1a756bfd6dcc0507dd1b60a419ae936b3fe95e3`;
- the source description was a Summer Fridays deep-dive reply;
- the page-owned response yielded 20 comments from 71 source-visible comments;
- no source-native transcript body was observed, so the packet supports one
  creator/comment slice and no prevalence or product-truth claim.

Two later exact targets stopped on an empty/stripped page shell with missing
hydration, no `itemStruct`, and no CAPTCHA/challenge marker:

| Job | Disposition | Staging evidence SHA256 |
|---|---|---|
| `CO3-NATIVE-TT-7527741844298435895` | blocked after initial attempt and one cooled fresh recovery reproduced `missing_video_detail_hydration` | initial `0d623de7de80934b41bbfe92578b34840fd8f29f90408fcf4bb0e00335f7a283`; recovery `1872480594e8742e28ac9dc854c93d683cbd84d19a3654da8d3541cbbb701284` |
| `CO3-NATIVE-TT-7379382940272217386` | blocked after the same shared empty-shell failure | `7e39517bbd44b78f265f1513846e0fb6039c6ec1c6540006e88db7c13a35cabd` |
| `CO3-NATIVE-TT-7354686188327832833` | unrun after the shared circuit opened | no child artifact |
| `CO3-NATIVE-TT-7496318205502246190` | unrun after the shared circuit opened | no child artifact |

No CAPTCHA was solved or bypassed, and no hot retry fan-out was run.

## Instagram

The official data lake was initialized before capture, which removes the p11
setup failure. Exact reel `DWE8EFkDHes` completed as packet
`01KYWVZWQAAB9R56X6H92699D4` with manifest SHA256
`fcdf6b636958cf6161b590bbc80fde42d77d736e261443dfa19e015ad0db05bb`.
It preserved seven comments and an 18-cue ASR transcript, plus the two required
Silver projections. The transcript is machine speech recognition and includes
probable errors; it records one creator's stated clean/non-toxic framing, not
medical, toxicology, or population evidence. Combined with the three parent
Instagram items, the four-item native Instagram route is complete under those
ceilings.

Raw artifacts live under
`C:\tmp\forseti-summer-fridays-understanding-p11r1-20260801\specialists\co3\`.
