# Competitor Ledger Spec v0

Companion to `serp_lane_v0.md` F20. Defines the competitor types, how each
is identified, the promotion ladder, and the wiring into the existing
claims-to-complaints path (choice-mechanism chain, D2/D4). Written
2026-07-27 against 149 extracted probes; every threshold here is a v0
default awaiting the full-bank ledger and owner vocabulary review.

Standing constraints apply: counts of observed cards only, never
volume/share/prevalence; US-parameterized is not physically US-local;
presence on a comparison surface is CITING, not switching (the L6 rule).
Subject binding (owner-ratified 2026-07-29): every subject commission
names its binding — exactly one formulation (the hero SKU; siblings
are `self_variant`); a deliberately brand-level commission is an
explicitly labeled BRAND READ (thin brand-line complaints only, no
per-SKU axes, no delight work).

## Why a ledger at all (the efficiency argument)

Competitor identification costs ~zero extra probes. The comparison
shapes are already on the default board, so the competitor surface is
captured either way — the only missing piece is a harvest-and-typing
pass over captures we already make. (Basis correction: the panel-era premise that
`vs {rival}` is the top shape on both axes is superseded — its social
half is withdrawn. **Numbers are not restated here**; the owning cells
in `serp_lane_v0.md` carry them. This paragraph previously cited
`alternatives` at 0.749 under an "F23" the ledger had independently
minted for the platform-door finding; the figure was REAL — it is
`alternatives` unique question share in the P9 design (sealed 0.747) —
but unique share is not comparable across designs, so a bare number
without its design is what drifted, not the measurement. Read F17, F23,
and F25 in the ledger; do not copy their figures back into this file.)
The expensive mistake is the current one: hand-picking rivals for the #1
shape, which turns the best probe into a confirmation loop (we only learn
about competitors we already guessed).

## The identification strategy: cheap-first, typed at harvest

Ordered by marginal cost. Each channel emits candidates with a
channel-default type and a source record; the ladder does the filtering,
so channels are allowed to be noisy.

**Channel 0 — existing-capture harvest (zero new probes).** Every
already-captured SERP carries competitor signal regardless of its shape: related searches
("{s} vs …"), PAA ("Is {s} better than …?"), organic/video titles with
comparison pairs, AIO comparison mentions, dupe-aggregator results. One
emitter pass over the extraction store harvests all of it retroactively.

**Channel 1 — rival-free seed probes (cycle 0 only, 2 probes).** `vs`
needs a name to exist — chicken-and-egg. `{s} dupe` and
`{s} alternatives` are rival-FREE shapes that produce names. When a
subject's ledger is empty, these two seed it; they are already on the
default board, so this costs nothing extra either.

**Channel 2 — harvested-rival vs probes (cycle N+1).** `{s} vs {rival}`
with rival drawn from the cycle-N ledger, highest-rung first. Operator
priors are allowed only as cycle-0 seeds, must be tagged `seed:operator`,
and retire as vs-inputs the moment the harvest produces one typed rival.

**Channel 3 — complaint-borne names (native capture, highest precision).**
The D2 classification's price-value class ("not worth $24", "drugstore
does the same", names a cheaper equivalent) already wires into the
substitute cell. Any complaint or community body naming an equivalent
emits a ledger entry with `surface_class: complaint_body`. This is
revealed switching language from actual users — the only channel whose
language is about leaving, not comparing. The rule fires on any
complaint-borne equivalent REGARDLESS of the driving axis
(owner-ratified 2026-07-28): price is one driver among several —
efficacy and tolerability switches ("more results with Purito", "skin
improved once I went back to DHC") fire it equally; the D2
price-value examples are illustrative, not a requirement. Cross-thread recurrence
counts only across DISTINCT authors (check the packet author fields);
same-author repeats collapse to one voice. (Installed 2026-07-28 after
the SF Ole Henriksen check: 3 threads, 3 different authors — that
independence, not any single vote count, justified the promotion.
Name the venue spread too: those 3 threads are ALL r/Sephora, so the
corroboration is author-diverse but venue-concentrated; distinct
subreddits is the stronger bar and stays worth naming when met.)

**Channel 4 — retail shelf co-location.** Corroborative only; never
originates an entry, only adds a surface class to an existing one.

**Speech-act posture gate (installed 2026-07-28, owner rule).**
Before any statement enters a complaint column (`complaint_body`
entries, unmet-value-map rows, concern ledgers), type its ACT:
only ASSERTION posture (first-hand experience claim) passes.
CLARIFICATION-SEEKING posture (doubt as question or secondhand
report — "I've seen people saying", "I heard", interrogatives, no
first-hand failure) never enters a complaint column. Posture cannot
be typed from a SERP title alone: a title is posture-unknown until
the thread body/comments are read — dive in before typing, or hold
the row untyped. Clarification-seeking rows route to a separate
**CLARIFICATION-DEMAND signal**: the row's engagement (post score,
comment count, under the post-as-comment rule) measures how many
observed voters share the concern — demand for an authoritative
answer, meaningful at high engagement even without further
corroboration (counts of observed engagement only, never
prevalence). Score its RESOLUTION (defused / confirmed /
unresolved), and read the resolution slot like an axis: an
unoccupied or weakly-occupied answer slot on a high-engagement
clarification demand is an ANGLE — the own/preempt play from the
repair-room playbook applies to answers, not just repair content.
Full posture taxonomy and specimens (Wimsylou SPF chain; T28
creasing counter-specimen): `complaints_axis_v0.md`.

## Choice-state and qualified-association boundary (installed 2026-07-28)

Type a statement's choice state after the speech-act posture gate; choice state
does not replace posture.

- **EXECUTED_CHOICE** — the evidence reports a completed action: returned,
  switched, went back, replaced, or selected after comparison/use. When the
  exact subject and cause are stated, emit the completed choice/exit row.
- **INTENDED_CHOICE** — the evidence makes an unqualified commitment to a
  future action: "I will return X," "I'm returning X," or "I will replace X
  with Y." When the exact subject, action, and cause are stated, emit an
  exit-pressure row marked `INTENDED_CHOICE`; never report it as an executed
  outcome.
- **POSSIBLE_CHOICE** — desire, consideration, or conditional action:
  "might," "may," "tempted," "thinking of," or "if the problem repeats, I
  will return." Hold it as consideration/demand context. It is not choice
  evidence and emits no executed or intended choice row.

The cause is load-bearing: a named action without its reason records choice
state but cannot set or corroborate an attribute axis.

A qualified copy claim ("pretty sure X and Y are identical") may emit a
`dupe_association` at **presence** only when the exact pair and the claimed
evidence basis are named. Preserve the qualifier in the source evidence and
mark the confidence/evidence line **TENTATIVE**. This creates no new rung and
cannot promote from that statement alone. Hold a qualified claim that lacks
the exact pair or its basis.

Choice-state ceilings on delight are owned by `delight_axis_v0.md`: only an
executed choice can satisfy its choice-revealing bar; intended and possible
choices cannot SET an axis.

## Read contract (installed 2026-07-28, from cold-agent dogfood round 2)

What a single evidence read EMITS, so output completeness does not
vary by agent. A **native-thread read** emits: (1) the dupe-economy
position line; (2) complaint-axis rows (posture-gated, per-SKU,
per-attribute, contested marks where defended; a complaint body
naming only the BRAND files to a thin brand-level line — owner-
ratified 2026-07-29 — which is reported alongside but never folded
into any SKU's axes); (3) competitor-ledger
rows (channels/types above); (4) posture-gated signal rows
(clarification-demand with resolution, axis-forfeiture alerts);
(5) held/excluded rows with stated reasons. A **SERP-only read**
emits: (1) rendered-surface rows with verdict-source typing;
(2) clarification-demand CANDIDATES (titles are posture-unknown);
(3) the trigger-thread queue with URLs; (4) composition-level reads
(J2 room type) where licensed. Every read closes by NAMING what is
not runnable on its evidence (J3 without the paired render/native
side; occupancy lines without a rendered layer; delight rows without
rival-owned surfaces) — honest absence is part of the deliverable.

For native-thread coverage, sweep every evidence row that contains action or
intent language, or a copy/equivalence/comparison claim. Give each candidate an
explicit emitted-or-held disposition with its evidence row ID and reason. A
candidate absent from the final output is not a valid hold; qualified or
insufficient evidence belongs in held/excluded rows. For an action/intent
candidate, list its row ID individually and type it `EXECUTED_CHOICE`,
`INTENDED_CHOICE`, or `POSSIBLE_CHOICE` before the emit/hold decision; a bundled
row-ID range or association-only explanation is not a choice-state disposition.

## Cold-agent reading-doctrine calibration protocol (installed 2026-07-28)

Run this protocol whenever the reading doctrine changes materially or a new
evidence class enters scope. It tests whether a cold agent can recover the
doctrine's intended rows from the text alone; it is separate from outcome-based
weight calibration.

1. **Pick uncontaminated evidence.** Any thread or SERP named as a specimen in
   the doctrine is disqualified. Prefer a fresh category, an inverse-direction
   case (for example, a CONFIRMED resolution when the specimen is DEFUSED), and
   one case per rule cluster under test.
2. **Freeze the register before launch.** Use row-level expectations when the
   register author has read the evidence and rule-level expectations otherwise.
   Name 2–4 load-bearing discriminators per case. A case passes only when all
   load-bearing discriminators hit.
3. **Use a neutral prompt.** Give the cold agent only these three doctrine
   paths, the subject, the evidence paths, and this generic task: "produce the
   evidence rows this evidence contributes, applying the doctrine exactly; do
   not invent rows the doctrine does not license." Never name an expected rule,
   construct, or finding.
4. **Match the bank-scale tier.** The worker tier used for bank-scale harvest
   is the default doctrine-text test tier (Sonnet in the proven 2026-07-28
   runs). A/B a synthesis tier only when tiering itself is the question; render
   the doctrine from one pinned commit into a temporary directory for both runs
   so later doc changes cannot confound the comparison.
5. **Score against the frozen register.** Mark every discriminator hit,
   partial, or miss. Record beyond-register findings separately; a cold agent
   out-scouting the register is signal, not noise.
6. **Install only repeatable gaps.** A miss warrants one doctrine install only
   when it recurs across agents or traces to a missing or misplaced rule.
   Single-agent variance is not a doctrine gap until a second run reproduces
   it. Install operative rules here; install complaint orientation in
   `complaints_axis_v0.md` and delight-only deltas in `delight_axis_v0.md`.
   Completeness is measured at the source cold agents actually load.
7. **Route open vocabulary edges to the owner.** If an agent correctly holds a
   row because vocabulary is unresolved, record the question for owner ruling.
   Never install an answer the owner has not supplied.

Calibration baseline at installation: five cold runs all passed (round 1:
9 hits/1 partial; round 2: 3/3 cases; synthesis-tier A/B: strict superset with
no overthink symptoms). Repeatable gaps installed from those runs were the
axis-forfeiture alert, this read contract, and complaint-side
ENGAGEMENT-THIN symmetry. Evidence:
`C:\tmp\forseti-axis-delight-calibration-20260728\second_leg_native\`
(`dogfood_*_v0.md`, doctrine commits `aaa97d28` through `61793775`).

## Position statement and drift check (installed 2026-07-28)

Every consolidation opens with a one-line DUPE-ECONOMY POSITION
statement — which side of the dupe economy the subject sits on, read
from the entry directions already in the ledger (anchor_up received vs
dupe_association received). Referent framing — the subject used as
the category's reference point in alternatives shapes ("X that isn't
the {s}") — is recorded on the position line as a named observation,
counts-only (owner-ratified 2026-07-29): it types no entry, sets no
position alone, and never triggers drift; it keeps category-defining
subjects from reading as blank. Each subsequent pass compares against the
prior pass's statement: a flip or drift is a HEADLINE finding, not a
footnote, because drift is the attackable moment (specimen: SF read
natively as premium original AND newly as duper-of-mass-originals,
q07 123-pt — two positions at once is itself the finding). Evidence
base n=2 (T28 dupe-side / SF anchor-side); escalate to a findings-
ledger cell when the full-bank pass tests it across subjects.

## The types (the writing)

Direction matters: one observed pairing writes entries on BOTH subjects'
ledgers with different types.

**rival** — same-tier head-to-head peer. Signature: symmetric comparison
language ("X vs Y" where either could be searched first), comparable
price tier, PAA "is X better than Y". What it feeds: the cycle-N+1 vs
probe list; the positioning axis of the CI report. Symmetric: Y gets a
`rival` entry for X too.

**dupe_association** — the cheaper product publicly claimed to replicate
the subject. Signature: "dupe for {s}" / "{s} dupe" surfaces pairing a
named cheaper product AGAINST the subject; dupe-aggregator rows. What it
feeds: pricing/margin pressure reads; the substitute cell when the same
name also appears in price-value complaints. Directional: the named
product's own ledger gets `anchor_up` pointing at the subject.

**substitute_down** — a cheaper functional exit that does NOT claim to be
a copy. Signature: complaint-borne only ("drugstore does the same",
partial-substitution statements in L4/L5 bodies); price-value D2 class.
What it feeds: the chain-card substitute cell directly — this is "where
the pressure resolves". Never emitted from SERP surfaces alone.

**anchor_up** — the premium product the subject rides or is compared UP
to. Signature: the subject appears on the DUPE side of a pairing ("{s}
is a dupe for [luxury Y]"). What it feeds: whose demand the subject
borrows; aspiration positioning; early-warning surface (the anchor's
complaints foreshadow the subject's).

**self_variant (owner-ratified 2026-07-28)** — the subject's own
sibling surfacing in comparison position: same brand, different SKU,
formulation, generation, or discontinued predecessor (Vaseline Blue
Seal vs Original; MFK house fragrances vs BR 540; the Brooks
discontinued-variant rivalry; regional reformulations under the
exact-SKU rule). Signature: shared brand/house with the subject in a
vs/dupe/alternatives shape. What it feeds: J5 ladder/cannibalization
reads, hero-product shaping, and succession-to-incumbent analysis —
NEVER the external-rival reads, vs-probe queue, or axis-occupancy
counts. Not symmetric with external types; observed in 3+ categories
before ratification. Size binding (owner-ratified 2026-07-29, kept
deliberately simple): one formulation = one SKU; size/fill never
splits it, because complaints attach to what the product DOES, not
how much of it was bought. Size spread is J5 ladder input;
per-unit normalization handles mismatched-size comparisons. No
further machinery.

Not types: retailers, marketplaces, and ingredient INCI names are
excluded at harvest. Creators/outlets go to the F12/F19/F21 mediator
lists, never this ledger. **Generic commodities (owner-ratified
2026-07-28)** — household commodities and home remedies surfacing as
alternatives ("Vaseline vs olive oil") are excluded from the ledger:
they cannot be vs-probed, cannot own axes, and carry no CI
commercial value. The substitute pressure is still recorded — typed
as a COMMODITY-EXIT signal in the exit-door read, alongside
behavioral and category exits.

## The promotion ladder

- **presence** — named once, one surface class. Bears NO claim; cite-only.
  Noise is expected here, so presence never drives Google egress or analysis
  eligibility without an explicit owner adjudication that supplies a real
  product identity. The raw ledger row remains preserved.
- **candidate** — recurrence: named on 2+ independent queries (different
  query strings, any shapes) within a subject. Bears exactly: "a
  comparison association was observed on k captured surfaces" —
  counts-only.
- **finding-grade** — surface-independence: 2+ surface CLASSES (SERP
  question layer / organic-video titles / AIO / complaint bodies / retail
  shelf). Only finding-grade entries may enter the chain-card substitute
  cell or a CI report. Complaint bodies count as an independent class, so
  Channel 3 promotes fast — by design, since it is the high-precision
  channel.

Demotion: an entry that gains no new source in 2 consecutive analysis
passes is flagged stale (kept, marked; never silently dropped).

Corroboration strength (owner weighting, installed 2026-07-28): within
complaint-body evidence, 2 distinct authors is the floor and is easy to
hit coincidentally; **3+ distinct authors is STRONG** and is the tier
that earns priority attention; **3+ authors across distinct
venues/subreddits is STRONGEST** and is named explicitly whenever met.
Rungs do not change — this grades the confidence line a CI report
attaches to a finding-grade entry. Specimen: Ole Henriksen promoted at
3-author/1-venue (r/Sephora), upgraded to author- and venue-diverse by
the return-leg capture (r/MakeupAddiction + Substack editorial).

Social-platform engagement (owner-ratified 2026-07-29): weighted only
against the creator's own recent-grid median (median not mean; #ad
rows flagged inside the grid). Without a defensible grid, the row
keeps rendered prominence plus an UNBASELINED flag — raw platform
counts are recorded, never weighted, never compared across platforms.
Doubt test: if the weight could not be reproduced and defended from
the packet (grid unavailable, unusable, inapplicable to this row, or
creator identity unconfirmed), it is UNBASELINED. Doubt withholds the
multiplier, never the evidence — the row's statement still flows
through the normal gates.

## Wiring into the claims-to-complaints path (owner Q2)

The chain-card IS the complaint journey: claim → buy-reason → experience
→ complaint class → substitute, with the mechanism sentence ending at
"where the pressure resolves". The competitor ledger does not need its
own lifecycle — it plugs into that existing one at two points:

**Inbound (complaints → ledger).** D2 class 3 (price-value) already
"wires into the substitute cell"; operationally that now means: any
complaint naming an equivalent emits a `substitute_down` (or
`dupe_association` if copy-claiming) entry with
`surface_class: complaint_body` and the observation id. No change to D2
itself — the five classes stand; this consumes an output D2 already
produces.

**Outbound (ledger → chain-card).** The substitute cell stops being
filled ad hoc per report: its content comes from the subject's
finding-grade `substitute_down` + `dupe_association` entries, each
carrying its observation ids and confidence mark, exactly like the other
four cells. The F21 cross-scope professional creators mediate the FRONT
of the same journey (problem → product entry); the ledger owns the EXIT.

Repo note: this wiring touches the choice-mechanism chain proposal (repo
doctrine). This spec stays in staging; the D2/D4 amendment is an owner
routing decision, not something the lane edits.

## Entry schema (v0)

```json
{"name": "...", "type": "rival|dupe_association|substitute_down|anchor_up",
 "subject": "...", "rung": "presence|candidate|finding_grade",
 "seed": null, "sources": [{"surface_class": "serp_question_layer",
 "query": "...", "evidence": "raw title/text", "date": "..."}]}
```

## Instruments

- `forseti-harness/runners/serp_competitor_ledger_emitter.py` —
  Channel-0 emitter, v0.1 (2026-07-28). Two modes: megadogfood store
  (default; its store path is operator-drive) and
  Understanding-cycle scout mode (`--extractions DIR --subject NAME`).
  v0.1 fixes, dogfooded on both stores: brand-token subject matching
  (direction bug fixed — NYX now dupe_association with correct
  direction), outlet/creator names routed to a `mediators` output
  instead of the ledger, community "X or Y" pattern (Haus Labs),
  question-prefix strip-then-extract, use-context junk rejection.
  Post-fix candidates are real names (NYX, Saie, Summer Fridays Lip
  Butter Balm q=4, Amazon Basics q=3). Known v0.2 items: scout-mode
  subject cross-product bleeds product evidence onto sibling subjects;
  self-variant entries ("Premium") pending the owner vocabulary call;
  obvious title fragments (`bad`, sentence debris, numeric/editorial labels)
  now fail closed at emission; any remaining presence noise is quarantined
  from egress and analysis rather than treated as ladder-tolerated input;
  from cross-company dogfood #2 (2026-07-28,
  `megadogfood analysis/dogfood2_cross_company_note_v0.md`):
  name+context compounds should collapse to parent ("Vaseline for
  baby" -> "Vaseline"), and CONTEXT_GENERIC is beauty-centric
  ("Irritated Skin" leaked at q=11). J2 now has THREE exit patterns
  (armed / retention / technique-moat) and J5 TWO price architectures
  (hidden-floor / ladder) — see the dogfood note.
- `forseti-harness/tests/unit/test_serp_competitor_ledger_emitter.py` —
  pinned-fixture regression check (12 assertions over both frozen
  stores). RUN THIS AFTER ANY EMITTER EDIT; a FAIL names the broken
  fact. Each assertion pins a mistake class the emitter actually made
  once; when a new subject exposes a new mistake, add its assertion
  here. It SKIPS rather than passes when the operator-drive fixture
  stores are absent — a skip is not a pass.
- Channel-3 emitter does not exist yet (needs the Reddit/native lane);
  the schema above is written to receive it.
- `dogfood10_runner.py` (phase-1 loop reference: `select_names`,
  `build_merged_queue`, `interleave`, J5 reserve-tier trigger) has no
  in-repo copy. The generation rule below is normative, so the merged
  queue is reconstructible from this spec alone; promote the script if
  it is ever needed beyond that.

**Merged vs+J5 queue — generation rule (normative).** After harvest,
select up to 2 names typed `rival`/`dupe_association`/`anchor_up` at
candidate or finding-grade rung, ranked by ladder rung first, then by
distinct_queries descending. Presence is cite-only and is never selected
automatically. Run every selected job through
`source_capture.google_serp_queue_policy.evaluate_queue_job` before egress;
a rejected job is recorded with its reason and not captured. Emit two job
lists: vs jobs `{subject} vs {name}` per selected name; J5 jobs
`{name} {product_scope} price` per selected name PLUS one `{subject} price`.
`product_scope` is mandatory for competitor J5 even when the selected entity
is a real brand: `Amazon Basics` or `CeraVe` alone spans many products and
cannot identify the intended price. A harvested name that is already an exact
product may repeat its product class explicitly; clarity beats terseness.
Interleave the lists strictly
(vs, J5, vs, J5, …), appending the remainder when one list runs out —
so a block or stop truncates both lanes evenly rather than losing one
entirely. At capture time, a J5 SERP returning fewer than 3 rows with
a `$` price in title or snippet appends one reserve job: the same
query with `&udm=28` (Shopping tab). Selecting zero names is a valid
outcome and emits the subject-price job only. At FULL PARITY — all
eligible names tied on both ranking keys — zero-select is mandatory
(owner-ratified 2026-07-29): complete the Channel-1 seeds first and
let real recurrence break the tie; no third ranking key exists, and
the tie is a diagnostic that the queue is running ahead of the seeds.
Raw rejected names and generated-job rejections remain in the ledger/queue
receipt; “prune” means analysis/egress quarantine, never evidence deletion.

## Cycle installation: a scout PASS + one ordering rule (not a step)

Owner-ratified shape after the Tower 28 trial: this is not a ceremonial
cycle stage. It is one analysis pass plus one sequencing rule, installed
at the front of the Understanding cycle before specialist fan-out.

**The ordering rule (the only step-like thing, and it is load-bearing):**
`vs {rival}` — the #1-value shape on both lane axes — is unrunnable
without a name. Seed probes (`{s} dupe`, `{s} alternatives`, both
already on the default board) must land and be harvested BEFORE the vs
probes run and before specialists are commissioned; otherwise the cycle
falls back to operator-picked rivals (the confirmation loop this spec
exists to kill). Validated live: Tower 28 phase 1 yielded zero rivals
from titles; phase 2 vs probes on harvested names opened the dense
social door (10+ comparison videos per SERP) and surfaced a new rival
(Saie) nobody hand-picked.

**The pass:** after extraction, run the emitter (scout mode below);
zero extra probes for a subject already on the default board; a cold
subject costs 2 seed captures inside the 15-20/hr band, queued behind
any running campaign — never a parallel stream on the same egress.

**Consumers of the ledger:**
1. The same cycle's `vs {rival}` probes — highest rung first; operator
   seeds tagged `seed:operator` retire on first harvested rival.
2. Commission board Section 8 (Competitor Context) — currently ships
   `status: gap` awaiting "a named interpretive job from fresh subject
   evidence"; the pass is that job. Presence/candidate entries with
   sources, counts-only. Deep competitor treatment stays a separately
   named follow-up per Section 2 doctrine — the ledger just lets the
   follow-up be named precisely.
3. Community-depth specialist — candidates become the "cited
   substitutes" watch-list its mandate already names; complaint-borne
   names flow back as `substitute_down` (Channel 3).
4. Named interpretive jobs (journey levers): **J1** claim-x-dupe cross
   (Tower 28 pattern: live acne-safe claim attack x pre-built NYX
   exit). **J2** exit-door read (three observed patterns: ARMED —
   CeraVe's complaint SERP renders "Amazon Basics vs CeraVe";
   RETENTION — Tower 28's renders repair content; TECHNIQUE-MOAT —
   AeroPress complaints resolve into hobbyist technique content).
   An unmatched room shape is recorded as UNNAMED with a one-line
   description of its resolving content; a shape recurring on 2+
   subjects earns a naming review (owner-ratified 2026-07-29 —
   never force-fit into the three named rooms).
   **J3** rendered-vs-actual fragility: per-surface tag ALIGNED /
   RENDERED_BETTER / NATIVE_BETTER (snippet stance vs top-voted native
   stance, counts-only); NATIVE_BETTER surfaces are where the subject
   should drive clicks, RENDERED_BETTER where it should avoid
   attention (and where a rival would drive it). Comparator runs in
   the REDDIT LANE's analysis step (phase-1 supplies the snippet, the
   lane supplies the thread). **J4** rival offense — IS deep
   treatment: owner-named only, never auto-invoked. **J5** — own
   section below.

### J5 — price-architecture read (OWNER-ACCEPTED 2026-07-28)

**Phase: PHASE-1 TAIL.** Subject pricing runs the moment the subject
is bound; competitor pricing runs right after the harvest step (needs
names, not threads) — never waits on the Reddit lane. Re-run when
phase 2 promotes a new name (Kulfi-type entrants that only surface in
complaint bodies).

**Emits per name:** list price · standing floor (per-unit) · the
response-trap note (the price where the incumbent cannot match without
cannibalizing its own bundle/ladder). Entry blueprint: the floor sets
the entry price; the ranked unmet-value map quantifies the "x more"
delivered at that price. Two architecture types observed: hidden-floor
(Tower 28: $28 list, refill floor ≈$17/bottle) and ladder (AeroPress:
$40 -> $200 self-variant spread; attack the middle, not the floor).

**Value doctrine (owner decision 2026-07-28).** This lane reads VALUE
competition, not price competition, and Forseti does not help subjects
compete on price. "Value" is deliberately left undefined in doctrine
for now (owner call: earlier operational formulations were too anchored
to one pilot's evidence; candidate formulations live in the calibration
artifacts, not here). J5's response-trap and floor reads serve value
analysis, never price advice.

**Verdict-source typing (installed 2026-07-28).** Every rendered
comparison verdict is typed by its source class at ANALYSIS time —
editorial (listicle/affiliate outlets), community (reddit/forum),
brand, marketplace, or CREATOR (owner-ratified 2026-07-29:
author-over-domain — any row carrying `account_or_creator` types as
creator regardless of displayed_domain, the Amazon Live case;
credential subtyping deferred until a read needs the split) —
using the displayed_domain already in the
extraction; no new capture and no lake storage of editorial pages.
Editorial-vs-community DIVERGENCE is a standing per-subject line in
the competitor read: editorial is effectively the glancer's verdict on
`alternatives`-shape surfaces (it dominated every pilot alternatives
SERP), community is the clicker's, and the two can point at different
exits (Breville specimen: editorial → value clone; community →
fix-the-complaint). Editorial-body capture (non-Google host, http
packet) is a NAMED optional follow-through only when a dupe-door
editorial's body holds names the ledger needs — never a standing
corpus.

**Axis-occupancy read (installed 2026-07-28, the Opalescence rule).**
Every unmet-value-map axis carries an OCCUPANTS line: the named
products whose rendered positioning sits on that axis ("Best for
Sensitive Teeth" on the sensitivity axis). Vacant vs occupied is the
entry read (entrants: enter on a vacant top axis — the Kulfi/
Opalescence pattern, observed in 3 categories) and the incumbent
early-warning (a NEW name appearing on the subject's #1 complaint axis
is a headline alert, not a footnote). A rival occupying the same axis
across 2+ subjects is an AXIS-OWNER (SKIN1004 specimen) — flag for
category-level treatment; the full-bank pass computes the axis-owner
table.

**Default procedure — 1-2 URL captures per name, zero clicks:**
1. Price-intent SERP ("{product} price"): shopping carousel with USD
   prices, per-unit math ($1.12/oz), Google's typical-price signal
   ("Usually $18"), seller names. When present, the AIO's per-retailer
   price list is itself a floor read.
2. `&udm=28` Shopping page (URL-addressable, same route) when the
   carousel is thin: ~50 offers incl. sellers absent from the base
   SERP. Reserve tier (not default): per-product seller census via
   product-page URLs harvested from the captured DOM.
3. Brand-site collection page + one retailer PDP for the SUBJECT
   (bundle/refill economics + the retailer comparison carousel, which
   prices the whole prestige set in one capture).

**Floor rules:** per-unit normalized; STANDING offers only (refill
programs, jumbo SKUs — never promos; "Usually $X" preferred as the
standing estimate); cross-retailer verified when possible; floor-
bearing prices only from the subject's harvested retailer set or
known majors; unknown long-tail sellers and ALL sponsored results are
recorded but never floor-bearing (gray-market guard — specimens: the
counterfeit "ceraveese.it.com" sponsored ad; GoSupps at $59-165 for a
$17 product). Off-price channel presence (T.J.Maxx) is recorded as a
channel-erosion signal when observed.

**Egress: no proxy, settled 3-way 2026-07-28** (SG-headless vs
SG-Chrome vs US-proxied-Chrome, same query: floor layer identical
offer-for-offer; only the ads layer localizes and only physically-
local modules — "Nearby, X mi", in-store stock — need US egress).
Owner: online focus, proxy dropped from J5; local
availability/distribution reads remain a separate owner-gated job on
the TikTok-Shop-US egress route. Carry the standing non-claim on
every artifact. Evidence packets: `dogfood2_packets/
price-surface-test`, `price-surface-shopping-tab`, `pdp_packets/`.

**Two-phase shape (owner framing, 2026-07-28):** Phase 1 = the SERP
scout pass (doors: typed ledger, thread list, mediator list). Phase 2
is NOT new machinery: the scout pass ENDS at emitting the trigger-
thread queue (contrarian-titled, claim-attack, vs threads), and the
EXISTING Reddit lane's fan-out consumes that queue alongside its other
discovery inputs — its runner, access gate, cadence, and review
routing already own native capture. The scout only adds a discovery
source and a priority tag. Queue entries carry canonical URLs at
emission (packet provenance); owner-observed items are located
in-session while the surface is fresh or explicitly marked deferred —
3 of SF's 13 rotted unlocatable (installed 2026-07-28). A
mediator-list entry meeting a deep-dive trigger — creator recurs on
2+ subjects, or their row carries a statement a read would weight,
or their row is an axis/answer-slot's only occupant, or
#ad-convergence needs checking — carries a `grid_capture` tag with
profile URL at emission (same URL-rot rule); the existing social
capture runners' input queue consumes tagged entries
(owner-ratified 2026-07-29). Phase 1 itself never visits a platform
and never weights a raw social count. Outputs per
captured thread: composition read against the rendered surface (J3),
complaint-borne names harvested (Channel 3), and — in
comparison-titled threads — THIRD NAMES flagged (names in comments
absent from the title; twice the highest-value find: Caliray 35-pt,
Ole Henriksen x3; installed 2026-07-28). Validated on Tower 28: phase 2 CHANGED the
competitor answer (community consideration set Kosas/NARS/Haus Labs vs
SERP's Hourglass/NYX; Haus Labs and Kosas reached finding-grade only
through phase-2/Channel-4 surface independence). Rendered snippets and
native verdicts can disagree (vs-hourglass specimen) — the glancer
absorbs Google's verdict, the clicker meets the community's; the gap is
the J3 fragility measure. Consolidation states the subject's
dupe-economy POSITION (dupe-side / anchor-side / both) with cites, and
flags observed DRIFT — position read as moving in community narrative
(specimen: SF read as newly duping mass originals, 123-pt). Drift is
an attack surface: self-image lags it, competitors exploit it
(installed 2026-07-28).

**Cycle loop schedule (owner framing, 2026-07-28):** Within phase 1:
seeds are front-loaded (mild ~1/min burst — CLEARED 2026-07-28: 4
captures at 60s spacing, zero blocks, `burst_test\` packets; front-load
stays <=8 captures pending longer-burst evidence); HARVEST IS LOCAL
COMPUTE and runs rolling as each packet lands, never queued behind
captures; once harvest emits names, vs probes and J5 price reads are
ONE merged capture queue at band cadence (the gate is harvest, not
vs — J5 picks up small deltas as vs probes harvest new rivals). The
two lanes are complementary, not merely compatible: vs-probe AIOs
render spec denominators (ml sizes) that price SERPs omit, so the
per-unit floor needs both lanes (Haus Labs 7ml/$32 = $4.57/ml read
assembled across b01+b02, burst-test specimen 2026-07-28). The
Reddit lane starts the moment the trigger-thread queue emits — it
hits a different host, so it may run concurrently with the Google
stream (owner-accepted 2026-07-28; block attribution is host-
specific). Return leg — SERP round 2 after fan-out consolidation:
(a) J5 delta on every phase-2 promotion (the Kulfi pattern, 1-2 URLs
per name); (b) evidence-targeted probes authored FROM fan-out
findings — narrow queries the seed grammar could not have guessed
(entrant checks like `kulfi vs tower 28`, unmet-value-axis shapes,
claim-attack follow-ups); every finding-grade rival with NO captured
head-to-head automatically earns a vs probe here (installed
2026-07-28; motivating case SF/Ole Henriksen — promoted natively,
never probed). Targeted probes obey the same typed-ledger
rules, with one guard: a probed name's own echo in its targeted SERP
bears no new ladder rung (the query was conditioned on the evidence);
only third names and the surface's composition are new evidence.

**Repo landing (owner routing) — LANDED 2026-07-28 (commit 2cc5e038).**
(a) CSB prompt-structure Section 8 now consumes a scout ledger when one
exists (type, rung, provenance; sub-finding-grade ships as
`status: gap`; comparator names must trace to a harvested surface or a
typed gap). (b) The CSB playbook's Operating Sequence step 6 routes the
phase-1 handoff before specialist commission authoring, states why the
seed-harvest-vs ordering is load-bearing, and makes a skipped pass a
typed gap. Handoffs no longer need to cite this spec to be discovered —
the cycle's own source names the pass.

**Still open — the D2/D4 chain amendment** (divergence now flagged
in the proposal itself at its D2 price-value class, 2026-07-28, so an
adjudicator meets it there; the decision itself is untaken). The
"Outbound (ledger →
chain-card)" section above says the substitute cell is filled from
finding-grade `substitute_down` + `dupe_association` entries. The
choice-mechanism chain proposal
(`docs/workflows/forseti_choice_mechanism_chain_design_proposal_v0.md`,
last touched 2026-07-17/18) still describes the substitute cell being
filled generically and knows nothing about this ledger. Until that
amendment lands, the two documents disagree about how the cell gets its
content and a report author following chain doctrine alone will keep
filling it ad hoc. This is an owner routing decision on repo doctrine,
not a lane edit.

## First-run lessons (95 probes, 74 entries, 9 candidates — 2026-07-27)

1. **`vs` names are headline-extractable; dupe names are not.** The vs
   surface yields clean rival names in the title string itself (Delter
   Press, Nanopress, Amazon Basics, DeLonghi Magnifica, Round Lab). The
   dupe surface reliably signals the DOOR ("86 Reddit-Picked Dupes for
   CeraVe...") but the names sit in the page body — so existing-capture
   harvest (Channel 0) fills
   `rival` well, while `dupe_association`/`anchor_up` mostly wait for
   organic-body or native harvest. This matches the type definitions:
   the substitute-side types are body/complaint-borne by nature.
2. **Self-variants surface as top vs candidates.** AeroPress Premium
   (q=5) and Rhode's own Peptide Lip Tint (q=2) out-recur true rivals.
   The vs surface does own-line disambiguation as much as competition.
   Open vocabulary question: a fifth type `self_variant` (useful — it
   maps the brand's internal cannibalization surface) vs. exclusion.
3. **"dupe for {use-context}" is a false-anchor pattern** ("CeraVe dupe
   for dry skin") — the right-hand side must be entity-like, not a
   skin-type/use phrase, before an `anchor_up` is emitted.
4. **Issue subjects emit concept comparisons, not competitors**
   ("purging vs irritation") — excluded at harvest; those pairs belong
   to the issue→question graph, not this ledger.

## Open for owner review

1. The type vocabulary itself (are rival/anchor_up split right for
   non-beauty verticals?). PARTIALLY RESOLVED 2026-07-28: the
   self-variant question is ratified as a fifth type and the
   generic-commodity question as a harvest exclusion with
   commodity-exit routing (see the types section); the non-beauty
   vertical fit of rival/anchor_up remains open.
2. Candidate threshold (2+ queries) and stale window (2 passes) —
   FOLDED (owner, 2026-07-29) into the full-bank executor lane's
   follow-up: tune empirically against the 649-probe / 111-candidate
   adjudicated harvest, not by rule.
3. ~~Whether `substitute_down` should ever be SERP-emittable~~ —
   CLOSED (owner-ratified 2026-07-29): complaint-only stands. The
   full bank confirmed it empirically: zero SERP emissions at 649
   probes.
