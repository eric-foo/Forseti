"""Canonical Google-SERP capture cadence for Forseti capture runners.

One source of truth for how fast a Google SERP stream may run, imported by
every Google capture runner rather than copied into each. Runners keep their
own block policy and job loop; only the cadence numbers live here.

## Shape

A stream runs one capture per `cycle` seconds and rests `REST_SECONDS` after
every `REST_EVERY` captures, so the effective hourly rate is lower than the
instantaneous one:

    effective/hr = REST_EVERY / (REST_EVERY * cycle + REST_SECONDS) * 3600

At the upper rungs this is deliberately a burst-and-rest shape: 30 captures
at 40s spacing is 90/hr instantaneous, then a 10-minute pause pulls the
sustained figure down to 60/hr.

## The ladder

A run starts at the rung recorded in its rate-state file and steps up one
rung after `RUNG_STEP_JOBS` consecutive clean captures. On ANY block it steps
one rung back and freezes escalation for the remainder of the run; escalation
never resumes after a block without a fresh owner decision. The ladder is a
graduated approach to a chosen operating rate -- it stops at the top rung and
never probes past it. Blocks are stop signals to respect, never a threshold
to measure or approach.

## Evidence (2026-07-28)

The whole ladder 27.1 -> 60.0/hr was walked clean on the real megadogfood
workload in one run (2026-07-28): zero blocks, zero failures, zero extract
errors at every rung. Evidence is NOT evenly distributed -- 40/hr carries
~443 captures, while 60/hr was reached last and carries the fewest, so
"we ended at 60" is not "60 is proven." Per-rung depth, not the top rung,
is the thing to read.

All of that evidence was gathered under the PREVIOUS shape (30 captures per
burst, 10-minute rest). The rest was shortened to 4 minutes on 2026-07-28 to
cut peak density; sustained rates are unchanged, but the burst shape under
which the rungs were measured is not the shape they now run. Treat the rungs
as rate-validated and shape-unvalidated until a clean run accumulates under
the current shape.

Historical note for context, not a bound: an earlier session profile saw
blocks somewhere in 28-40/hr; that did not reproduce here, which makes it
profile-dependent rather than wrong.

Upper rungs hold for fewer captures than lower ones (`RUNG_STEP_JOBS_ABOVE`
vs `RUNG_STEP_JOBS`): the lower rungs were novel and earned a long hold, while
above 40/hr the marginal step is smaller relative to what is already proven.
A tripped block costs 12-15 minutes isolated and 75-90 minutes as an episode,
so stepping is also cheaper in expectation than jumping.
"""

# Burst-and-rest shape. Rest is NOT free: at a fixed sustained rate, every
# minute of rest is paid for by a tighter burst, because the same captures must
# fit in less running time. Shortening the rest is therefore how you LOWER the
# instantaneous spike, not raise it. Owner concern 2026-07-28 was peak density,
# so the rest was cut from 10 min to 4 min and the burst held at ~20 minutes:
# at the top rung that moves the spike from 90/hr to 72/hr for the same 60/hr
# sustained, and cuts worst-case 10-minute density from 15 captures to 12.
# The floor at 60/hr sustained is a flat 60s cycle with NO rest (spike == 60,
# density 10); that is available by setting REST_SECONDS = 0 and is the
# minimum-spike option, at the cost of removing rests entirely -- a variable
# that was present throughout every clean run to date.
REST_EVERY = 24           # captures between rests (24 x 50s = 20-min burst at the top rung)
REST_SECONDS = 4 * 60     # rest length

# Rungs are declared as TARGET SUSTAINED rates; cycles are derived so the shape
# can change without silently re-rating every rung:
#     cycle = REST_EVERY * 3600 / rate / REST_EVERY - REST_SECONDS / REST_EVERY
TARGET_RATES = [27.1, 30.0, 32.7, 36.0, 40.0, 45.0, 50.0, 55.0, 60.0]

RATE_LADDER = [round(3600.0 / r - REST_SECONDS / REST_EVERY, 1)
               for r in TARGET_RATES]

RUNG_STEP_JOBS = 60       # consecutive clean captures to step up at <= 40/hr
RUNG_STEP_JOBS_ABOVE = 30 # ... and above it
RUNG_PROVEN_THROUGH = 4   # highest rung with measured clean evidence


def effective_rate(cycle, rest_every=REST_EVERY, rest_seconds=REST_SECONDS):
    """Sustained captures/hour for a cycle length, including rest breaks."""
    return rest_every / (rest_every * cycle + rest_seconds) * 3600.0


def rung_hold(rung):
    """Consecutive clean captures required before stepping up from `rung`."""
    return RUNG_STEP_JOBS if rung < RUNG_PROVEN_THROUGH else RUNG_STEP_JOBS_ABOVE


def cycle_for(rung):
    """Cycle seconds for a rung index, clamped into the ladder."""
    return RATE_LADDER[max(0, min(int(rung), len(RATE_LADDER) - 1))]


if __name__ == "__main__":
    for i, c in enumerate(RATE_LADDER):
        burst_min = REST_EVERY * c / 60.0
        print(f"rung {i}: {c:5.1f}s cycle -> {effective_rate(c):4.1f}/hr "
              f"sustained, {3600.0/c:5.1f}/hr instantaneous, "
              f"burst {burst_min:4.1f}min + {REST_SECONDS/60:.0f}min rest "
              f"(hold {rung_hold(i)})")
