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
language is about leaving, not comparing. Cross-thread recurrence
counts only across DISTINCT authors (check the packet author fields);
same-author repeats collapse to one voice. (Installed 2026-07-28 after
the SF Ole Henriksen check: 3 threads, 3 different authors — that
independence, not any single vote count, justified the promotion.
Name the venue spread too: those 3 threads are ALL r/Sephora, so the
corroboration is author-diverse but venue-concentrated; distinct
subreddits is the stronger bar and stays worth naming when met.)

**Channel 4 — retail shelf co-location.** Corroborative only; never
originates an entry, only adds a surface class to an existing one.

## Position statement and drift check (installed 2026-07-28)

Every consolidation opens with a one-line DUPE-ECONOMY POSITION
statement — which side of the dupe economy the subject sits on, read
from the entry directions already in the ledger (anchor_up received vs
dupe_association received). Each subsequent pass compares against the
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
   exit). **J2** exit-door read (three observed patterns: ARMED —
   CeraVe's complaint SERP renders "Amazon Basics vs CeraVe";
   RETENTION — Tower 28's renders repair content; TECHNIQUE-MOAT —
   AeroPress complaints resolve into hobbyist technique content).
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
3 of SF's 13 rotted unlocatable (installed 2026-07-28). Outputs per
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
