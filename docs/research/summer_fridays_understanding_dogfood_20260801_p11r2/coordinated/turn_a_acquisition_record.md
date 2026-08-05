# Summer Fridays Understanding p11r2 — Turn A Acquisition Record

```yaml
retrieval_header_version: 1
artifact_role: Acquire-and-seal recovery evidence and gate record
scope: Records final pending-job execution, raw validation, pacing diagnosis, remaining material gaps, and the acquisition-gate decision.
use_when:
  - Auditing p11r2 Phase A or determining whether a later Deliver turn is licensed.
authority_boundary: retrieval_only
```

## Adjudicated State

```yaml
status: BLOCKED_ACQUISITION_INCOMPLETE
acquisition_gate: blocked
deliver_allowed: false
deliver_started: false
bound_question_preserved: true
coldness_attestation: compliant
subject: Summer Fridays
as_of_date: 2026-07-31
commission_authority_revision: aa92073b51c3a4259fbc800e98a06770ec21fb8b
parent_p11r1_revision: cf37c213bfa3a7c05a3e6b8c7658fb5104de4c1a
capture_runner_revision: a273e1e4980cea1077ef6a536b8ecd8944f70072
phase1_jobs: {planned: 12, completed: 12, blocked: 0, unrun: 0}
co1_jobs: {planned: 11, completed: 9, blocked: 2, unrun: 0}
co2_jobs: {planned: 7, completed: 7, blocked: 0, unrun: 0}
reddit_community_jobs: {planned: 3, completed: 3, blocked: 0, unrun: 0}
native_tiktok_jobs: {planned: 5, completed: 4, blocked: 1, unrun: 0}
native_instagram_jobs: {planned: 4, completed: 4, blocked: 0, unrun: 0}
native_youtube_jobs: {planned: 1, completed: 1, blocked: 0, unrun: 0}
phase2_jobs: {planned: 8, completed: 8, blocked: 0, unrun: 0}
```

Only the nine jobs listed as pending by the p11r1 seal were eligible. This
recovery completed all three Reddit jobs and three of the four unfinished
TikTok jobs. It re-ran the already-complete Karly TikTok item once as a bounded
same-session health control; that control receives no additional completion
credit. The two blocked Summer Fridays-owned pages were not retried again after
their first request, 17-second second request, and nearly seven-minute cooled
retry had all returned HTTP 429. No completed job outside that diagnostic
control was replayed.

## What The Failures Mean

### Summer Fridays-owned pages

The two missing pages are:

- `https://summerfridays.com/pages/jet-lag-mask-statement` (`CO1-J10`)
- `https://summerfridays.com/pages/sustainability` (`CO1-J11`)

The original focused pair was requested seven seconds apart. The p11r1 pair was
17 seconds apart. That was unnecessarily fast, so future same-host work must
start with one health probe and must not fan out after a 429. But spacing is not
the root cause by itself: the first focused request came more than six hours
after the earlier site crawl, and a retry nearly seven minutes later still
returned the same `local_rate_limited` page with HTTP 429 and `Retry-After: 60`.
The evidence supports a Shopify automated-client/route refusal, not a claim
that the site merely counted too many requests in a short window. Those two
bodies remain genuinely absent.

### Reddit

The previously blocked pages were the seven exact threads listed in the CO3
recovery return. With the VPN disabled, normal old-Reddit Direct HTTP captured
all seven bodies and 492 comments without a retry. The prior 403 browser shell
was therefore a network/session-route block, not proof that Reddit had removed
the threads. The VPN/egress change is the leading explanation, but the preserved
artifacts cannot identify the exact network attribute Reddit rejected.

### TikTok

Slow dispatch recovered Makeup, WalkingTower, and Micah; the Karly control also
succeeded. Erin alone continued to return a full-page shell without video
hydration, while TikTok's official oEmbed endpoint confirmed that exact public
video and its caption. Erin is therefore a target-specific full-page capture
incompatibility in the current session/region/page variant, not a missing video,
global TikTok outage, CAPTCHA, or broad session failure.

## Process Repair And Dogfood

- Reddit was captured through the normal capture spine: one exact health probe,
  then a single six-URL bounded-jitter batch with 80–102-second gaps and no
  proxy, browser, retry, or crawl.
- TikTok launches were serialized with at least 90 seconds between commands so
  cadence applied across process boundaries. Three formerly incomplete targets
  admitted packet-grade transcript/comment evidence.
- The Reddit quality-summary defect was fixed and tested. The corrected live
  summary reads six content-retention packets as six parsed successes, with
  five usable, one needs review, and zero unusable; consolidation remains a
  separate truthful count.
- The retained future rule is deliberately small: probe once; batch requests so
  cadence applies; stop on a block or 429; honor `Retry-After`; preserve the
  failure. No auto-reload loop or durable global host-state system was added.

## Raw Closure

The new raw root is
`C:\tmp\forseti-summer-fridays-understanding-p11r2-20260801\`. Fresh recursive
validation observed 11 manifest locations, 11 unique packet IDs, 19 declared
preserved files, zero preserved-file size/hash errors, zero TikTok staging JSON
parse errors, and zero Deliver-named artifacts. The p11 and p11r1 raw roots and
their blocked seals remain preserved and unedited.

## Machine-Derived Resume Set

Three required-and-material jobs remain incomplete:

```yaml
pending_job_ids:
  - CO1-J10
  - CO1-J11
  - CO3-NATIVE-TT-7527741844298435895
```

## Acquisition Gate Decision

`BLOCKED_ACQUISITION_INCOMPLETE` remains mandatory. The recovery reduced the
material pending set from nine to three, but it did not acquire either required
company-owned page body or packet-grade transcript/comments for the Erin TikTok
item. A passing seal would hide those gaps.

No company report, synthesis, recommendation, strategy, Problem Framing
artifact, p10 comparison, Deliver handoff, or other Deliver output was created.
This acquisition record is not permission to start Deliver.
