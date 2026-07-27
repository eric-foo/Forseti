# SERP-Lane Egress Shape Evidence — v0 (2026-07-28)

Source: `C:\tmp\forseti-tower28-scout-20260727\burst_test\burst_test_findings_v0.md`
(cross-checked against the sibling `burst_ledger.jsonl` on the same
path). This note records observed capture behavior for capacity
planning only; it is not a target, a schedule, or a recommendation —
a block, wherever it occurs, is a stop signal to be respected, not an
obstacle to route around.

## Burst-shape result

Owner-directed bounded egress-shape experiment: a mild-form burst
(~1 capture/minute front-load) on a REAL interleaved queue — Tower 28
phase-2 vs probes + J5 price reads in ONE merged queue. Target cycle
was 60s start-to-start. Actual, from `burst_ledger.jsonl`
(`started_at`, UTC):

| job | lane      | started_at (UTC)      | gap from prev | outcome | rows | capture wall-time |
|-----|-----------|------------------------|----------------|---------|------|--------------------|
| b01 | vs probe  | 2026-07-27T18:14:23Z   | —              | ok      | 28   | 4.9s               |
| b02 | J5 price  | 2026-07-27T18:15:23Z   | 60s            | ok      | 23   | 4.0s               |
| b03 | vs probe  | 2026-07-27T18:16:23Z   | 60s            | ok      | 35   | 5.2s               |
| b04 | J5 price  | 2026-07-27T18:17:23Z   | 60s            | ok      | 23   | 4.5s               |

- Spacing held exactly: 60s / 60s / 60s, no schedule slip (captures
  returned in 4-5s, far inside the 60s cycle).
- Span first->last start: **180s for 4 captures** = an instantaneous
  burst rate of **60 captures/hour equivalent**, sustained 3 minutes.
- For comparison: the never-blocked sustained band is 15-20/hr, the
  2026-07-28 sustained experiment ran ~27/hr, and blocks were
  historically observed at sustained 28-40/hr. This burst ran at
  ~2-4x the never-blocked sustained rate, for 4 captures.

**Block verdict: 0 blocks in 4 captures at 60s spacing.** All four
extractions returned `route_verdict: null` (no
`blocked_google_unusual_traffic`), each with a fully-rendered result
surface. No unusual-traffic interstitial, no retry, no cooldown. The
stop-on-block path in `burst_runner.py` was armed throughout and never
fired.

## SCOPE LIMIT — read before reusing this result

This tests the mild end of burst tolerance only: 4 captures at 1/min,
from a cold-ish egress, with the main run paused. It establishes that a
4-capture 60s-spaced front-load did not trip the block on this
occasion. **It does NOT establish a safe sustained rate, a safe burst
length, or that 60/hr is survivable beyond 3 minutes.** Burst tolerance
past 4 captures remains untested. "0 blocks in 4 captures at 60s
spacing" is the whole finding — it is not a safe-rate claim and not a
licence to sustain that rate.

## Interleave finding

The vs probes and the J5 price probes ran from ONE merged queue,
alternating vs / price / vs / price. The two lanes are complementary —
neither lane alone would have completed the read the merged queue
produced:

- **vs probe b01** (Tower 28 vs Haus Labs) carried price AND size data:
  a TikTok row rendering `$32` / `$22`, and an AIO section headed
  "Price and Packaging" stating **"Haus Labs is 7 ML and Tower 28 is
  6"** — the size denominator that makes the b02 per-unit floor
  interpretable.
- **J5 price probe b02** (Haus Labs Triclone) supplied the price side:
  standing list **$32.00** (Sephora regular, brand-site pre-discount,
  Klarna 3-store comparison naming $32.00 the cheapest of 3 stores),
  and a source-rendered **$4.57/ml** (Instacart card), implying 7 ml —
  consistent with the AIO's stated volume.
- Combined: **Haus Labs Triclone = $32.00 / 7 ml = $4.57/ml**, a
  per-unit floor the price lane alone lacked a denominator for and the
  vs lane alone lacked a price for.
- Same pattern on the other pair: **Kulfi Main Match = $26.00 / 5 ml
  (0.17 oz) = $5.20/ml** (b04 price + brand-site/Sephora/editorial size
  agreement).

This cross-feed argues for merging the vs and price lanes into one
queue rather than splitting them.

## Emitter defect exposed by the burst (open emitter-queue item)

The competitor-ledger emitter (`vs`/`or` pattern matcher) missed a
rival named inside a comma-list enumeration. b03's video title read
"Kosas, Giorgio Armani, and Tower 28 are the concealers I ..." — Giorgio
Armani is a real co-occurring rival, confirmed by manual read, but is
**invisible to the emitter** because the title carries no `vs`/`or`
pattern for the matcher to split on. This is a new gap, not a
recurrence of the known clipped-title/qualifier-suffix noise classes:
**rivals named inside a comma-list enumeration are currently invisible
to the emitter's vs/or pattern matcher.** Left open on the emitter
queue, not fixed here.

## Standing non-claims

- **Counts of observed result cards only.** Nothing here is a
  prevalence, volume, traffic, demand, or market-share claim, and
  nothing here supports one.
- **US-parameterized is not physically US-local.** The route is
  `hl=en, gl=us, pws=0` from the observed default egress (SG). All four
  captures carried the Google footer note "Unknown - Can't determine
  location." These are US-parameterized results, not results as served
  to a physically-US user.
