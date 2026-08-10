# Reddit Dive-Yield Calibration — 2026-08-01 v0

```yaml
retrieval_header_version: 1
artifact_role: Research calibration artifact
scope: >
  Measures which listing-visible features of a Reddit thread predict named-brand
  evidence in its comment bodies, using the 414 already-dived threads as the
  oracle. Supplies the evidence for raising the general discussion floor to 10+,
  and records the measured results that were NOT acted on.
use_when:
  - Reviewing or revisiting the general discussion floor.
  - Proposing a listing-level selection cue for the Reddit deep-dive queue.
  - Estimating how many threads a floor change adds or removes.
authority_boundary: retrieval_only
open_next:
  - forseti/product/spines/capture/core/source_families/social_media/reddit/reddit_listing_efficiency_policy_v0.md
  - docs/research/reddit_weekly_latent_problem_adjudication_2026_08_01_v0.md
stale_if:
  - The dived corpus grows enough to re-measure on a sample not selected by the superseded policy.
  - The brand vocabulary or the brand-rich threshold changes.
  - A later owner decision changes the floor again.
```

## Method

414 captured thread content records (`parser_version: 1` — the settled corpus
predating this week's www dives), 32,550 comments. For each thread: the
listing-visible features known at selection time (title, subreddit, comment
count, score) against an outcome only knowable after the dive — how many
distinct named brands appear in the post and comment bodies.

Titles were classified with the weekly reader's own `_classify_title_signal`,
so results are expressed in the vocabulary selection actually sees. "Brand-rich"
means three or more distinct brands. Corpus baseline: **39% brand-rich, mean 3.7
brands, median 2**; 67% of threads carry at least one brand.

## Result 1 — comment count dominates, and the bottom band is empty

| comments | threads | brand-rich | mean brands |
|---|---|---|---|
| 100+ | 170 | 71% | 7.3 |
| 30–99 | 31 | 45% | 3.2 |
| 10–29 | 62 | 19% | 1.1 |
| **4–9** | **151** | **9%** | **0.7** |

151 dives — 36% of the entire prior budget — went to the 4–9 band and returned
almost nothing. Part of this is arithmetic (six comments is less text than two
hundred), and that is not a subtle finding; the decision-relevant statement is
that a thread that small has not held a conversation yet, so there is nothing
for a deep read to read.

Applied to the live 2026-07-31 pool (4,430 candidates, 83 venues):

| floor | candidates | vs current | venues able to fill 2 dives | admitted threads surviving |
|---|---|---|---|---|
| 4 (superseded) | 4,430 | — | 83 / 83 | 129 / 129 |
| **10 (adopted)** | **2,776** | **−37%** | **79** | **125** |
| 30 | 1,263 | −71% | 69 | 109 |
| 50 | 644 | −85% | 55 | 84 |

Floor 10 cost four admitted threads, all `normal` priority (a discontinued-lipstick
dupe request, European drugstore polish, an anti-aging ingredient confusion, a
postpartum wavy-hair routine). The four venues that fell below 2-dive capacity —
`gelnails`, `makeupflatlays`, `muacjdiscussion`, `hairloss` — had already been
adjudicated to zero or one `yes` on their merits.

**The floor's value is adjudication cost and coverage, not dive quality.** The
frame already ranks by comments, so the admitted set was 84% at 30+ regardless.
Reviewing the top rows per venue covers ~24% of a 4,430 pool but ~38% of a 2,776
pool, which directly shrinks the unseen-tail residual named in the adjudication
record.

### Why not higher

At 30+ the same corpus loses 20 of 129 admitted threads including two high
priority: *"affordable powder bronzer that's actually dark!!!!"* (deep-tone
shade gap) and *"how do you tell if this Beauty of Joseon is US or
International?"* — the second being part of the week's strongest cluster.
Fourteen venues fall below their dive budget.

The mechanism is general and worth stating: **underserved-segment problems live
in small threads.** A problem affecting everyone draws 300 comments; a problem
affecting an overlooked group draws 25, not because it matters less but because
fewer people are in the room. A high floor systematically deletes the niche
findings while keeping the popular ones, which inverts what this lane is for.

## Result 2 — brand count measures width, not depth

| title signal | n | brand-rich | mean |
|---|---|---|---|
| `praise_or_success` | 33 | 67% | 6.8 |
| `concrete_outcome_or_experience` | 17 | 53% | 3.6 |
| `pain_or_failure` | 14 | 50% | 6.1 |
| `concrete_question_or_request` | 161 | 50% | 5.5 |
| `routine_or_collection` | 24 | 38% | 2.3 |
| `comparison_or_choice` | 19 | 26% | 2.3 |

Praise threads are the most brand-dense, which appears to contradict the
standing frame's gate-4 polarity. It does not, and the sample sizes matter:
praise is n=33 and pain n=14, so the gap between them is not resolvable —
what *is* clear is that both sit well above the 39% baseline.

The mechanism explains the apparent conflict. A holy-grail thread is a **list**:
two hundred people each name one product, maximal brand count, no depth on any
of them. A problem thread is a **diagnosis**: one or two brands, taken apart by
a hundred people. Praise is wide and shallow; problems are narrow and deep.

**Brand count is therefore the wrong optimization target.** Selecting on it
would steer the weekly back toward popularity lists — precisely what the
latent-problem frame exists to move away from. The target is a latent problem
attributable to a named brand, not a census of brands.

## Result 3 — the review cap, not the floor, was the binding rule in large venues

Measured after the floor decision, on the same 2026-07-31 pool at floor 10
(2,776 candidates, 82 venues with candidates): adjudication reviewed the top
14 candidates per venue by comments — 945 rows, 34% of the pool — leaving
1,831 candidates unseen. In any venue with more than 14 candidates, the
rank-14 comment count becomes the *effective* floor for that venue, set
accidentally by a review-batch size rather than by any decision:

| venue | candidates | effective floor (comments at rank 14) |
|---|---|---|
| makeupaddiction | 85 | 177 |
| colognes | 101 | 157 |
| malegrooming | 91 | 113 |
| femfraglab | 95 | 105 |
| tressless | 102 | 88 |
| sephora | 88 | 63 |

The cap bound 55 of 82 venues (median effective floor 32); the written 10+
floor was the binding rule in only the 27 venues with ≤14 candidates. This
partially undercut the floor decision's own rationale — small-thread niche
protection — in exactly the venues with the most candidates. Owner decision
2026-08-01: adjudication depth is now top 14 **plus** the 6 highest-commented
candidates in the 10–49 band not already included, per venue (see the policy's
standing-frame adjudication-depth rule). The slice restores guaranteed
small-thread coverage at a worst case of 20 rows per venue; the tail below
rank 14 and outside the slice remains unseen and stays a named residual.

Leaderboard-lane sizing measured on the same pool: 331 praise-shaped
candidates at floor 10; 97 at 50+; 41 at 100+ comments (the adopted lane
floor).

## Result 4 — measured and deliberately not adopted

- **A brand named in the title predicts nothing.** 36% brand-rich with a brand
  in the title versus 39% without — slightly negative, n=45. Mechanism: a brand
  in the title closes the answer space ("Is Medik8 the best retinol?" gets
  answers about Medik8), while an open problem draws everyone's own shelf into
  the thread. Recorded so this cue is not proposed again.
- **`comparison_or_choice` is below baseline** (26%). Same mechanism: "A or B?"
  fixes the answer set at two before anyone replies. This is also the honest
  answer to whether dupe requests are brand-rich conversations — they are not.
- **Venue prior, deferred.** Brand density by venue ranges from `femfraglab`
  81%, `colognes` 77%, `fragrance` 75% down to `nails`, `naturalhair` and
  `fragranceswap` at 0%. Mechanism: fragrance has no generic vocabulary — a
  scent cannot be discussed without naming the house and the bottle — whereas
  "moisturiser" or "gel polish" are discussable as categories. This is
  structural rather than weekly noise and would be a sound ranking input, but
  the owner adopted only the floor in this pass, and a venue prior strong enough
  to matter risks collapsing the dive mix into one category.

## Residuals and non-claims

- **The sample is not random.** All 414 threads were selected under the
  superseded engagement-head policy, so every rate here is conditioned on what
  that policy liked. The floor finding is robust to this (an empty band is empty
  regardless of how it was chosen); the per-signal rates are weaker.
- Brand vocabulary is a fixed ~170-name list, English and Western-skewed, and
  matches surface strings only. Unlisted and misspelled brands are invisible.
- Brand presence is a proxy for evidence value, not evidence value itself.
- Small cells (`pain_or_failure` n=14, `comparison_or_choice` n=19,
  `technique_or_repair_context` n=8) are directional only.
- This artifact is not validation, not readiness, and not a scoring model. It
  supplies one owner decision and records what else was measured.
