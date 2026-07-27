# Cross-company dogfood #2 — CeraVe + AeroPress (2026-07-28)

Owner ask: dogfood the full method (harvest + J-levers + J5) against
companies other than Tower 28. Zero new Google probes: local
re-extraction of the running bank (206 eligible probes, 285 ok
captures) + one brand-store page (aeropress.com, separate host).
Counts of observed cards only; US-parameterized is not physically
US-local.

## What generalized

**The emitter + ladder.** 38 candidates on the refreshed store, led by
real names across four verticals: Vaseline (q=13, Aquaphor), French
Press (q=12, AeroPress), Bambino Plus / DeLonghi Magnifica / Ninja
Luxe (Breville), Amazon Basics (q=5, CeraVe), Live it Up (AG1).
Fixture test: 12/12 PASS after re-run.

**J2 exit-door typing — now three patterns, one per company type:**
- CeraVe: ARMED. Amazon Basics renders on `not_working` AND
  `overrated`; the churn moment carries an equivalence claim.
- Tower 28: RETENTION. Complaint SERPs render repair content;
  exposure lives on claim/dupe surfaces instead.
- AeroPress: TECHNIQUE MOAT (new). Complaint shapes resolve into
  hobbyist technique content (11 repair cards on `mistakes` alone,
  ~0 competitor cards); the only rendered "exit" is the brand's own
  Premium upsell. Strongest retention shape observed: the community
  answers complaints with technique, and churn pressure routes
  INTERNAL (upgrade), not external.

**J3 trigger queues.** 7 CeraVe + 16 AeroPress threads incl. textbook
contrarian anchors ("Cerave moisturizing cream big mistake!",
"I fell for the hype and regret", "What's so bad about CeraVe?").
Queues route to the Reddit lane per owner routing 2026-07-28.

**J5 price architecture.** Generalizes, and yields a second
architecture TYPE: Tower 28 = hidden-floor (bundle conceals $17
fair price); AeroPress = LADDER (Original ~$40 -> Clear $50 ->
Premium ~$200 -> bundles $360; parts sold separately at $40-100).
No hidden floor to expose — instead a 5x self-variant spread that
explains why "Premium" out-recurs true rivals on the vs surface:
the brand's own upsell IS its comparison traffic. Attack surface is
the ladder's middle (where ORB/Delter/Nanopress already sit), not
the floor.

## What broke (v0.2 queue additions)

1. Name+context compounds: "Vaseline for baby" / "Vaseline for wound
   healing" should collapse into parent "Vaseline" (they currently
   split the recurrence count).
2. Context vocabulary is beauty-centric: "Irritated Skin" (q=11!)
   and "wound" leak through — the CONTEXT_GENERIC set needs
   per-vertical extension or a smarter entity test.
3. Self-variant pressure again ("Premium" q=8, "original" q=4 on
   anua) — the owner vocabulary call (self_variant type vs exclusion)
   is now the largest single noise source at candidate rung.

## Verdict

The method survives contact with three more verticals; the J2/J5
typologies got RICHER, not looser (three exit patterns, two price
architectures). The noise that remains is one vocabulary decision
(self_variant) and two mechanical fixes — all queued, none blocking
the full-bank analysis pass (~07-30).
