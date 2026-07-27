# Competitor Ledger Spec v0 — staging (owner routes into repo when called)

Companion to `serp_lane_v0.md` F20. Defines the competitor types, how each
is identified, the promotion ladder, and the wiring into the existing
claims-to-complaints path (choice-mechanism chain, D2/D4). Written
2026-07-27 against 149 extracted probes; every threshold here is a v0
default awaiting the full-bank ledger and owner vocabulary review.

Standing constraints apply: counts of observed cards only, never
volume/share/prevalence; US-parameterized is not physically US-local;
presence on a comparison surface is CITING, not switching (the L6 rule).

## Why a ledger at all (the efficiency argument)

Competitor identification costs ~zero extra probes. `vs {rival}` and
`dupe` are already the top shapes on both lane axes (F4/F17/F18), so the
default 6-probe board already captures the competitor surface — the only
missing piece is a harvest-and-typing pass over captures we already make.
The expensive mistake is the current one: hand-picking rivals for the #1
shape, which turns the best probe into a confirmation loop (we only learn
about competitors we already guessed).

## The identification strategy: cheap-first, typed at harvest

Ordered by marginal cost. Each channel emits candidates with a
channel-default type and a source record; the ladder does the filtering,
so channels are allowed to be noisy.

**Channel 0 — free riders (zero probes).** Every already-captured SERP
carries competitor signal regardless of its shape: related searches
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
language is about leaving, not comparing.

**Channel 4 — retail shelf co-location.** Corroborative only; never
originates an entry, only adds a surface class to an existing one.

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

Not types: retailers, marketplaces, and ingredient INCI names are
excluded at harvest. Creators/outlets go to the F12/F19/F21 mediator
lists, never this ledger.

## The promotion ladder

- **presence** — named once, one surface class. Bears NO claim; exists
  only as a probe-queue entry. Noise is expected here.
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

- `megadogfood-20260727/bin/competitor_ledger.py` — Channel-0 emitter,
  v0.1 (2026-07-28). Two modes: megadogfood store (default) and
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
  residual prose-fragment noise at presence rung (ladder-tolerated);
  from cross-company dogfood #2 (2026-07-28,
  `megadogfood analysis/dogfood2_cross_company_note_v0.md`):
  name+context compounds should collapse to parent ("Vaseline for
  baby" -> "Vaseline"), and CONTEXT_GENERIC is beauty-centric
  ("Irritated Skin" leaked at q=11). J2 now has THREE exit patterns
  (armed / retention / technique-moat) and J5 TWO price architectures
  (hidden-floor / ladder) — see the dogfood note.
- `megadogfood-20260727/bin/test_competitor_ledger.py` — pinned-fixture
  regression check (12 assertions over both frozen stores). RUN THIS
  AFTER ANY EMITTER EDIT; a FAIL names the broken fact. Each assertion
  pins a mistake class the emitter actually made once; when a new
  subject exposes a new mistake, add its assertion here.
- Channel-3 emitter does not exist yet (needs the Reddit/native lane);
  the schema above is written to receive it.

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
   exit), **J2** exit-door read (CeraVe: complaint SERP renders "Amazon
   Basics vs CeraVe"; Tower 28: renders repair content — a retention
   surface), **J3** rendered-vs-actual fragility (SF 19eo5it vote-mass
   pattern), **J4** rival offense — J4 IS deep treatment: owner-named
   only, never auto-invoked. **J5** price-architecture read (added
   2026-07-28; OWNER-ACCEPTED 2026-07-28 with the entry-blueprint
   framing — standing floor sets the entry price, ranked unmet-value
   map quantifies the "x more" delivered at that price): from 1-2 captured PDP/collection pages per subject,
   emit list price, bundle/refill floor (per-unit math), and the
   response-trap note — the price point where the incumbent cannot
   match without cannibalizing its own bundle program. Tower 28
   specimen: $28 standard, refill floor ≈$17/bottle; a value entrant
   at $17-19 flat sells the incumbent's hidden price openly and traps
   the response. Floor rules (owner, 2026-07-28): per-unit normalized;
   STANDING offers only (durable SKUs like refill programs and jumbo
   sizes — never promos; the Sephora "Lip Day 50%" banner in the same
   capture is the excluded counterexample); cross-retailer verified
   when possible (Swipe $24 matched brand-site vs Sephora). The floor
   is the entry price anchor; the ranked unmet-value map supplies the
   "how much more we must deliver at that price". J3 divergence output is a per-surface tag —
   ALIGNED / RENDERED_BETTER / NATIVE_BETTER (snippet stance vs
   top-voted native stance, counts-only): NATIVE_BETTER surfaces are
   where the subject should drive clicks; RENDERED_BETTER surfaces are
   where it should avoid attention (and where a rival would drive it).
   Owner routing 2026-07-28: the comparator runs in the REDDIT LANE's
   analysis step (phase-1 SERP supplies the snippet; the lane supplies
   the captured thread) — same home as the trigger-thread queue.

**Two-phase shape (owner framing, 2026-07-28):** Phase 1 = the SERP
scout pass (doors: typed ledger, thread list, mediator list). Phase 2
is NOT new machinery: the scout pass ENDS at emitting the trigger-
thread queue (contrarian-titled, claim-attack, vs threads), and the
EXISTING Reddit lane's fan-out consumes that queue alongside its other
discovery inputs — its runner, access gate, cadence, and review
routing already own native capture. The scout only adds a discovery
source and a priority tag. Outputs per captured thread: composition
read against the rendered surface (J3) and complaint-borne names
harvested (Channel 3). Validated on Tower 28: phase 2 CHANGED the
competitor answer (community consideration set Kosas/NARS/Haus Labs vs
SERP's Hourglass/NYX; Haus Labs and Kosas reached finding-grade only
through phase-2/Channel-4 surface independence). Rendered snippets and
native verdicts can disagree (vs-hourglass specimen) — the glancer
absorbs Google's verdict, the clicker meets the community's; the gap is
the J3 fragility measure.

**Repo landing (owner routing):** (a) one line in the CSB
prompt-structure spine making Section 8 consume a scout ledger when one
exists; (b) handoff prompts add the seed-harvest-vs ordering between
subject binding and commission authoring. Until routed, handoffs cite
this spec directly.

## First-run lessons (95 probes, 74 entries, 9 candidates — 2026-07-27)

1. **`vs` names are headline-extractable; dupe names are not.** The vs
   surface yields clean rival names in the title string itself (Delter
   Press, Nanopress, Amazon Basics, DeLonghi Magnifica, Round Lab). The
   dupe surface reliably signals the DOOR ("86 Reddit-Picked Dupes for
   CeraVe...") but the names sit in the page body — so Channel 0 fills
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

1. The type vocabulary itself (four types; are rival/anchor_up split
   right for non-beauty verticals?).
2. Candidate threshold (2+ queries) and stale window (2 passes).
3. Whether `substitute_down` should ever be SERP-emittable (currently
   complaint-only by definition).
