# Summer Fridays Understanding p11r2 — CO3 Recovery Delta

```yaml
retrieval_header_version: 1
artifact_role: Customer/community acquisition recovery return
scope: Closes the pending p11 Reddit complaint-body work and four unfinished native TikTok attempts without changing completed parent evidence.
use_when:
  - Combining the immutable p11/p11r1 CO3 returns with the final p11r2 acquisition evidence.
authority_boundary: retrieval_only
```

## Terminal Accounting

```yaml
status: BLOCKED_TERMINAL
reddit_community_scout: {planned: 3, completed: 3, blocked: 0, unrun: 0}
native_tiktok: {planned: 5, completed: 4, blocked: 1, unrun: 0}
native_instagram: {planned: 4, completed: 4, blocked: 0, unrun: 0, source: reused_p11r1}
native_youtube: {planned: 1, completed: 1, blocked: 0, unrun: 0, source: reused_parent}
```

## Reddit — Exact Pages And Route Result

With the operator's VPN disabled, the normal capture-spine route was healthy:
exact `old.reddit.com` Direct HTTP, no proxy, no browser, no retry, and no
crawl. A one-thread health probe returned HTTP 200 and a 604,340-byte body.
Only then did one bounded batch capture the remaining six URLs with planned
gaps of 101.433, 80.036, 101.852, 80.897, and 80.328 seconds. All seven
captures succeeded on their first request.

| Thread id | Exact requested page | Captured comments | Quality |
|---|---|---:|---|
| `19eo5it` | `https://old.reddit.com/r/Sephora/comments/19eo5it/can_we_all_just_admit_that_summer_fridays_isnt/` | 180 | usable; local consolidation from preserved raw |
| `1oh26y0` | `https://old.reddit.com/r/Sephora/comments/1oh26y0/review_finally_got_around_to_trying_summer/` | 37 | usable |
| `1fvevie` | `https://old.reddit.com/r/beauty/comments/1fvevie/summer_fridays_is_lying_to_you/` | 85 | needs review; 28 collapsed/deleted-node parser warnings retained |
| `1al8aby` | `https://old.reddit.com/r/Sephora/comments/1al8aby/summer_fridays_applicator_clogged/` | 2 | usable |
| `1slrvyj` | `https://old.reddit.com/r/LipBalm/comments/1slrvyj/summer_fridays/` | 24 | usable |
| `1ahn26w` | `https://old.reddit.com/r/Sephora/comments/1ahn26w/how_do_yall_feel_about_the_summer_fridays_lip_balm/` | 74 | usable |
| `1qdk0gq` | `https://old.reddit.com/r/LipBalm/comments/1qdk0gq/cheaper_dupes_for_summer_fridays_type_balms/` | 90 | usable |

This closes `J-CO3-01`. It also makes the two formerly unrunnable local
derivations runnable:

- `J-CO3-02` completed with a complaint-borne substitute emission. Across the
  bounded threads, commenters named alternatives or comparison points including
  Laneige, Marin, Ole Henriksen, Too Faced, Aquaphor, Rhode, Eadem, Glossier,
  e.l.f., Topicals, Trader Joe's, Naturium, Jack Black, Vaseline, Fresh, Tower
  28, and Kosas. This is a qualitative list from seven selected threads, not a
  ranking, prevalence estimate, recommendation, or product-performance fact.
- `J-CO3-03` completed with a rendered/native comparison. The Reddit bodies
  contain mixed discussion of hydration, texture, scent, price, formula
  change, reactions, applicator clogging, and tube/package failure. Native
  TikTok supplies a separate creator transcript about clear applicator plastic
  breaking on two Summer Fridays balms and a Topicals balm, plus comments that
  include both similar failures and no-problem/user-handling counterexamples.
  Another native item discusses discontinued/reformulated portfolio items and
  carries comments about dry or falling-out blush sticks. These are bounded
  anecdotes and creator/comment claims, not prevalence or verified causation.

The prior 143-byte Reddit block page was therefore not evidence that these
threads were deleted. It was a route/session network-security response from the
stateless browser fallback. The healthy direct route after the VPN change makes
the VPN/egress path the leading explanation; the artifacts do not isolate
which network attribute Reddit rejected.

## TikTok — Retry And Diagnosis

The same retained profile and profile-bound Chrome endpoint were used. Launches
were separated by at least 90 seconds instead of issuing independent one-video
commands 19–24 seconds apart.

| Job | Final disposition | Evidence |
|---|---|---|
| `CO3-NATIVE-TT-7232313070897483051` | complete, reused p11r1; same-session p11r2 control also completed | control cadence SHA256 `0c9ff3f3a7a1680e2c445f54599830f1cacdb88957f27a1a55a594a431ba8c8a` |
| `CO3-NATIVE-TT-7527741844298435895` | blocked for packet-grade capture | cooled retry again lacked `itemStruct`/video-detail hydration; no CAPTCHA marker; staging SHA256 `1c8f2375a4e60e3889a5c6b7aab2ce230f3a98ebf94a567ce17a029c4f7289fe` |
| `CO3-NATIVE-TT-7379382940272217386` | complete | packet `01KYWYWE9RZGG8C4VKZDBHF5DZ`; manifest SHA256 `7ac10a9606d984ad6311e90eb8b9511b59061ff3f43efd997e47de63f2ababe8` |
| `CO3-NATIVE-TT-7354686188327832833` | complete | packet `01KYWYMQRJG9FV7ZZ90HF41NF5`; manifest SHA256 `e65cd268ce4bb1dfe523664e0a38c3758ccdd59e54730d69f3938b8513845df9` |
| `CO3-NATIVE-TT-7496318205502246190` | complete | packet `01KYWYRA6PA8K7PBXPH9XRCN2R`; manifest SHA256 `1a6ec04ded040e36b137d026d6006315779bcaba96c4a83e9e523a75354452f1` |

The Makeup target succeeded after the slower relaunch, so its earlier empty
shell was transient and rapid cross-command launches were a plausible
contributor. Erin failed again after a long cooldown while a Karly control and
the three other targets succeeded in the same session. TikTok's official
oEmbed endpoint also returned HTTP 200 for Erin's exact video, creator, and
caption. That combination rules out a deleted/private video and a globally
broken session; it isolates a target-specific failure of the full video page to
provide the hydration required by the capture contract.

The oEmbed response is preserved as packet `01KYWYJV5CHJSB5GDGT6QDETHP`,
manifest SHA256
`687d97917513c9efc71bd3287f0d45fd718091da90d0fe69219548fa4c199491`.
It supports only the creator-authored caption and public-video identity. It does
not supply transcript, comments, packet-grade native admission, medical or
toxicology validation, or product truth, so it cannot complete Erin's job.

## Raw Closure And Process Findings

The p11r2 raw root is
`C:\tmp\forseti-summer-fridays-understanding-p11r2-20260801\`. A recursive
fresh check observed 11 manifests, 11 unique packet IDs, and 19 preserved-file
declarations. Every declared file existed with the recorded size and SHA256;
all TikTok staging JSON parsed; no Deliver-named artifact existed.

Two process failures were confirmed:

1. Internal cadence does not protect separate one-video/process launches. The
   prior TikTok commands were only 19–24 seconds apart even though each command
   declared a cadence. This run fixed the dispatch behavior by serializing
   launches and leaving at least 90 seconds between them.
2. The Reddit quality summary treated valid content-retention packets as though
   a missing derived consolidation meant unusable capture. The runner now
   recognizes the preserved `reddit_thread_content_v0` record as a parsed
   artifact while keeping consolidation accounting separate. Focused tests and
   this six-packet dogfood report 6 parsed successes, 5 usable, 1 needs review,
   and 0 unusable.

No automatic reload loop or cross-process host ledger was added. An automatic
reload would increase requests exactly when a page is unhealthy, and a durable
global ledger would add a new shared state surface without evidence that it is
needed. The bounded operating rule is: health-probe one URL, batch same-source
work so cadence actually applies, stop fan-out on 429 or an access shell, honor
`Retry-After`, and preserve the block.

