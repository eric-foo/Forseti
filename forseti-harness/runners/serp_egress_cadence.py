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

Rungs 0-4 (27.1 -> 40.0/hr) were walked on the real megadogfood workload:
240 consecutive captures, zero blocks, zero failures, ~2h per rung. Rungs 5-8
(45 -> 60/hr) are owner-directed toward a 60/hr operating target and carry NO
measured evidence yet -- they are why the per-rung hold and the fall-back-and-
freeze rule exist. Historical note for context, not a bound: an earlier
session profile saw blocks somewhere in 28-40/hr; that did not reproduce here,
which makes it profile-dependent rather than wrong.

Upper rungs hold for fewer captures than lower ones (`RUNG_STEP_JOBS_ABOVE`
vs `RUNG_STEP_JOBS`): the lower rungs were novel and earned a long hold, while
above 40/hr the marginal step is smaller relative to what is already proven.
A tripped block costs 12-15 minutes isolated and 75-90 minutes as an episode,
so stepping is also cheaper in expectation than jumping.
"""

# cycle seconds per rung, slowest first
RATE_LADDER = [113.0, 100.0, 90.0, 80.0, 70.0, 60.0, 52.0, 45.5, 40.0]

REST_EVERY = 30           # captures between rests
REST_SECONDS = 10 * 60    # rest length

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
        proven = "measured clean" if i <= RUNG_PROVEN_THROUGH else "NO evidence yet"
        print(f"rung {i}: {c:5.1f}s cycle -> {effective_rate(c):4.1f}/hr "
              f"sustained, {3600.0/c:5.1f}/hr instantaneous "
              f"(hold {rung_hold(i)}, {proven})")
