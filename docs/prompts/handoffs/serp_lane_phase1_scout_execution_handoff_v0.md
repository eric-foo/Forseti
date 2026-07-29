# SERP Lane Phase 1 — Scout Execution Handoff v0

```yaml
retrieval_header_version: 1
artifact_role: Execution handoff prompt
scope: >
  Bounded runtime commission to execute phase 1 of the SERP-lane
  competitor cycle for a newly bound subject: front-loaded rival-free
  seeds, rolling harvest into a typed competitor ledger, then one merged
  vs+J5 capture queue, ending at a priced ledger plus the trigger-thread
  queue that phase 2 consumes.
use_when:
  - A subject has been bound for the Understanding cycle and the scout
    pass runs before specialist fan-out.
stale_if:
  - The default boards in serp_lane_v0.md move past v2.1 (2026-07-29,
    tournament + platform-door + noise-floor re-judgment) without this
    handoff being re-rendered.
  - The owner egress cadence or the CloakBrowser packet runner changes.
authority_boundary: retrieval_only
```

## Preflight (routine core)

```yaml
prompt_preflight:
  output_mode: file-write
  write_destination: >
    operator staging: a new subject work folder under C:\tmp for packets,
    extractions, ledgers, and the findings note. Repo docs-write only to
    refresh docs/research/serp_lane_competitor_scout_20260728/ in its lane
    PR when the owner routes.
  input_prompt_source: docs/prompts/handoffs/serp_lane_phase1_scout_execution_handoff_v0.md
  edit_permission: docs-write
  runtime_authorization: >
    This accepted handoff is the bounded runtime authorization (AGENTS.md):
    Google SERP captures for this subject's seed, vs, and J5 queues only.
    No clicks, no proxy, no CAPTCHA interaction, no account state, no
    other capture surface.
  targets: operator staging for this subject; the routed snapshot folder
    above (refresh-only). No code, spine, or overlay edits.
  reviews: findings-first; no formal verdict bound.
```

**Goal:** hand the Understanding cycle a typed, priced competitor ledger
— who this subject actually competes with, in which direction, at what
price — instead of letting each specialist guess.
**Done looks like:** a ledger whose names came from captured surfaces
rather than from anyone's prior, each carrying its ladder rung and
provenance; a price line for the subject and the selected names; and a
trigger-thread queue handed to the Reddit lane. This is the executor
target and a review axis-to-attack, not a review pass bar.

## Required reads (pointer-first; the spec owns the method)

1. `docs/research/serp_lane_competitor_scout_20260728/README.md` —
   reading order and the authority note. That folder is CANONICAL: lane
   prose and instruments are authored there, in the repo. The operator
   drive holds raw capture data and in-flight scratch only. Write your
   findings into the repo folder, never only into a `C:\tmp` note.
2. `docs/research/serp_lane_competitor_scout_20260728/competitor_ledger_spec_v0.md`
   — the four harvest channels (especially Channel 0, existing-capture
   harvest); the competitor types and promotion ladder; the cycle
   installation and its ordering rule; the cycle-loop schedule; the
   **merged vs+J5 queue generation rule** (normative — the algorithm is
   stated there, so it need not be re-derived); and the `### J5` section
   for price procedure, floor rules, and egress settlement.
3. `.agents/workflow-overlay/safety-rules.md` — authorization boundaries.
4. The CloakBrowser packet runner's source or `--help` before the first
   run (`forseti-harness/runners/run_source_capture_cloakbrowser_packet.py`)
   — resolve args from source, not memory.

## Method (deltas only; the spec owns the mechanics)

1. **Seeds — Board v2.1** (owner-ratified 2026-07-29; live authority:
   `serp_lane_v0.md` § Current default boards). Ten rival-free queries,
   run in this order or concurrently — all of them are wanted, so probe
   selection is not a decision point:

   | probe | the question it asks |
   | --- | --- |
   | `{s} review` | what is the consensus verdict? |
   | `{s} side effects` | what harm do people attribute to it? |
   | `is {s} bad for you` | what safety worry circulates? |
   | `{s} made it worse` | how does it backfire, in users' words? |
   | `{s} not working` | how does it fail to deliver? |
   | `{s} reddit` | what does the community say unprompted? |
   | `{s} dupe` (or `alternatives`) | who is it substituted with? |
   | `{s} youtube` | who explains and reviews it? (YT = the evaluative/explainer layer, F22) |
   | `{s} tiktok` | who compares and substitutes it? (TT = the substitution layer, F22) |
   | `{s} instagram` | who showcases it; which brands and credentialed professionals broadcast? (IG = showcase + derm-explainer layer, F22) |

   The three platform doors are CORE, not optional — the creator/social
   layer always matters (owner call). They are also the volume doors
   (F23): discount their 15–31% brand-own-account share before reading
   sentiment. **Never seed** `{s} complaints` or `regret buying {s}`
   (tournament-cut, F6) and never plant a competitor name you have not
   harvested. Operator-supplied names are allowed but tagged
   `seed:operator` and retired as vs-inputs on the first harvested rival.
   Front-load at ~1/min, ≤10 captures (wave-2 evidence: 60/hr sustained
   is clean; the constraint is the ~30-min window, not the burst).

   The `vs {rival}` probe is NOT a seed: its rival arrives from this
   phase's own rolling harvest (Channel 0–2), and again after phase 2 —
   the Reddit lane's complaint-borne names (Channel 3) refresh the vs
   queue for the return leg. Two fill moments, both from harvest.
2. **Harvest — rolling, never queued behind captures.** Harvest is local
   compute over extractions and costs no egress; run the emitter as
   packets land so the ledger has names as early as possible.
3. **Merged vs+J5 queue.** Generate it by the spec's normative rule and
   capture it at the owner cadence. Reference implementation, if the
   operator drive is reachable:
   `C:\tmp\forseti-scout-dogfood10-20260728\bin\dogfood10_runner.py`.
4. **Levers, read off the same captures — no extra probes.** J1 claim×
   dupe cross; J2 exit-door classification (armed / retention /
   technique-moat); J3 tag where rendered snippets may diverge from
   native verdicts. J4 is owner-named only.
5. **Emit the handoff to phase 2:** the trigger-thread queue (contrarian-
   titled, claim-attack, and vs threads, with canonical URLs captured at
   emission), the mediator list, and the priced ledger. Phase 2 runs via
   `docs/prompts/handoffs/serp_lane_phase2_native_return_execution_handoff_v0.md`;
   the Reddit lane hits a different host and may start as soon as the
   queue exists.

## If unsure, proceed like this

- **Harvested name might not be a real competitor?** It cannot reach the
  candidate rung unadjudicated — the v0.2 gate holds it at
  `pending_adjudication`, fail closed. Adjudicate from its captured
  evidence first; when the evidence is too thin to call, spend **one
  verification probe** on the name itself (`{name} review`): a real
  brand resolves to a coherent product surface (own site, retail
  listings, reviews), junk resolves to nothing coherent. Echo guard
  applies — the verification probe's own echo of the name bears no
  ladder rung.
- **Unsure whether an outlet/creator is a standing anchor for the
  subject?** "Anchor" = the claim that a specific site or creator is
  durably attached to this subject (the mediator list, native
  follow-through targets). Domains churn ~27% overnight (F24), so ONE
  appearance may be Google's shuffle, not a relationship: it takes
  **two sightings on two different days** to write "anchor" — one
  sighting is logged as presence only.
- **Blocked mid-run?** A block is a flag, not a rate signal (F2b) —
  slowing down cannot clear it. Stop the stream, record it, idle **up
  to 1 hour maximum, then PING the owner** with the run state and let
  them route the resume. (Decay evidence, F3: 26 min proven
  insufficient, ~3h25m proven sufficient — the ping should say the
  flag likely needs more idle than the hour already spent.) Never retry
  hot, never approach the threshold to measure it.
- **Anything else ambiguous?** Prefer the reading that leaves a typed
  gap over the reading that invents data — a visible hole routes work;
  a guessed fill poisons every downstream consumer.

## Egress boundaries (hard)

- Read the CURRENT owner cadence before the first capture — do not assume
  a historical band. One Google-stream capture at a time. A block is a
  stop signal per the rule above: stop, record, ≤1h idle, ping owner;
  never retry hot, never interact with a CAPTCHA. Blocks are respected,
  never approached or measured.
- Standing non-claims on every artifact: counts of observed cards only,
  never prevalence/volume/share; US-parameterized is not physically
  US-local; raw capture data stays on the operator drive, outside Git.

## Return contract (schema-bound; one line per field; `unknown` if absent)

- `ledger`: each name with type, ladder rung, distinct_queries, and one
  provenance cite (job id).
- `selected_for_vs`: names the merged queue used, and why they ranked.
- `j5_prices`: subject and per name — list price, standing floor,
  response-trap note, source URL class; `architecture`: hidden-floor or
  ladder.
- `levers`: J1 cross (live / not observed), J2 exit-door class, J3 tags.
- `trigger_thread_queue`: URLs handed to the Reddit lane.
- `mediators`: outlets and creators (never ledger entries).
- `blocks`: count and detail, or `0 blocks in N captures`.
- `artifacts`: staging paths written.
