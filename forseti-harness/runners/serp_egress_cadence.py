"""Canonical Google-SERP capture cadence for Forseti capture runners.

One source of truth for how fast a Google SERP stream may run and how an
automated route must respond to a block, imported rather than copied into each
runner. Query eligibility and route selection live in
`source_capture.google_serp_queue_policy`; runners must use both authorities.

The automated cooldown/stop ceiling deliberately excludes the operator-visible
`persistent_realchrome` route. That route pauses without navigation, pings the
operator once per distinct block, waits for manual clearance, and resumes the
exact held job at the same cadence.

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
rung after `RUNG_STEP_JOBS` consecutive clean captures. On a block WITHIN the
five-job escalation probation it steps one rung back; any other block freezes
the current rung (F2b, 2026-07-29: rate reduction cannot clear a live flag).
Either way escalation freezes for the remainder of the run; escalation
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

ONCE FLAGGED, RATE STOPS BEING THE VARIABLE. On 2026-07-28 a first block
(load-driven -- see the shape comment below) was followed 14 minutes later by
a second block on the FIRST capture after a ~26-minute total gap, at a rate
two rungs lower. Zero successful captures separated them. That second block
says nothing about 55/hr; it says the IP was still flagged and a ~26-minute
cooldown did not clear it. This matches the lane's standing finding that
recovery from a flag is slow (>75 min) and that prevention beats reaction.
Operational consequence: after a block, further LOWER-ROUTE probing every
12-15 minutes mostly re-confirms the flag. Preserve that block packet and stop
the lower route. When the run has its explicitly enabled dedicated, logged-out,
operator-visible Chrome fallback ready, transition the exact held job and the
remainder of that run to one persistent real-Chrome tab. This is a transport
fallback, not a CAPTCHA solver or evidence that the lower route recovered.
The executable held-job seam is
`runners/run_google_serp_persistent_fallback_packet.py`; after transition,
queue runners use it for each remaining job.
Keep the owner-set cadence (including a 45/hr or 60/hr band); a route change
does not authorize a rate increase. If the persistent tab is itself blocked,
pause navigation, ping the operator once per distinct block, and resume only
after the operator manually clears the visible challenge. A held job that is
blocked again after a clearance pings again; a single latched ping per job
would leave the second block waiting silently. This operator-visible route does
not inherit the automated repeat-block stop ceiling. Never click or solve the
challenge in automation. If the fallback is unavailable, fail loud and let the
lower-route flag decay for hours before a new run at a low rung. Do not
interpret post-flag blocks as data about the rate they happened to occur at.

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
# fit in less running time. Shortening the rest LOWERS the instantaneous spike.
#
# A block followed a 4-minute-rest experiment on 2026-07-28, but the timing
# reconstruction shows the shape was NOT the cause and was never actually
# tested. What happened: a 30-capture burst ended 19:33:45 with a 10-minute
# rest due; the operator restarted the orchestrator ~2 minutes later, and the
# fresh process began capturing immediately, truncating that rest to 2.1
# minutes. The result was 41 captures in 30 minutes -- effectively one
# continuous half-hour burst -- and a block at the 11th capture after the
# restart. The 4-minute rest never fired, because the block arrived before the
# burst reached it.
#
# So the honest reading is: rest REMOVAL correlates with the block. "4-minute
# rest is worse than 10-minute rest" is unsupported -- that comparison has no
# data. This strengthens the hypothesis that the REST WINDOW is load-bearing
# (a recovery interval, not dead time) and says nothing about how short a real
# rest may safely be. n=1 either way; blocks are stochastic.
#
# Kept at 10 minutes because that is the shape with ~150 consecutive clean
# captures at 60/hr behind it. Do not shorten it without a deliberate test that
# actually runs the shorter rest.
REST_EVERY = 30           # captures between rests (30 x 40s = 20-min burst at the top rung)
REST_SECONDS = 10 * 60    # rest length -- load-bearing; see the block above

# Rungs are declared as TARGET SUSTAINED rates; cycles are derived so the shape
# can change without silently re-rating every rung:
#     cycle = REST_EVERY * 3600 / rate / REST_EVERY - REST_SECONDS / REST_EVERY
# Rungs 9-11 (2026-07-28, owner-directed) target a ~77/hr peak-30-minute
# window. Read the SUSTAINED column and the PEAK-30MIN column as different
# things: a rest does not fall evenly inside every 30-minute slice, so a
# 30-minute window runs ~1.067x the sustained figure (60/hr sustained measured
# 64/hr peak-30min over 151 clean captures). That ratio is why the top rung
# here is 72/hr sustained, not 77: 77 SUSTAINED would put the 30-minute window
# at ~82/hr, which is precisely where the run's only block landed. 72 sustained
# lands the window at ~77/hr -- above everything measured clean, below the one
# observed block.
#
# Why the 30-minute window is the metric: at 10- and 20-minute windows the
# clean stretch and the blocked stretch were IDENTICAL (16 captures / 96/hr and
# 30 captures / 90/hr respectively). They diverged only at 30 minutes -- 32
# captures (64/hr) clean versus 41 (82/hr) blocked. So the instantaneous spike
# is not the discriminating variable; the half-hour total is. One observation,
# consistent-with rather than measured, and blocks are stochastic.
TARGET_RATES = [27.1, 30.0, 32.7, 36.0, 40.0, 45.0, 50.0, 55.0, 60.0,
                65.0, 70.0, 72.0]

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



# ---------------------------------------------------------------------------
# Block response (F2b/F3 doctrine, owner-ratified 2026-07-29)
#
# Landed here rather than per-runner because the first attempt landed it in
# ONE runner and the very next launch (dogfood10, 2026-07-30) re-probed a
# live flag with the old 12-15 min policy. Automated Google capture runners
# should call this instead of writing their own. The operator-visible
# persistent route owns a separate pause/ping/manual-clear loop.
#
# The policy, and why each part:
#   * step a rung back ONLY inside the escalation probation. A block that
#     does not follow a rung increase is a flag, not a rate signal, and the
#     sealed diagnosis shows trailing-1h load does not separate blocks from
#     clean captures at all (median 42 vs 39).
#   * idle at most IDLE_SECONDS_MAX, then make exactly ONE recovery attempt.
#     12-17 min re-probes failed six times in the sealed decay series.
#   * on automated routes, a second consecutive block or the third of a run
#     writes a ping file and stops for owner routing. Never probe on.
#   * persistent_realchrome is excluded: it pauses and pings the operator once
#     per distinct block, then waits for manual clearance without navigation.
# ---------------------------------------------------------------------------

IDLE_SECONDS_MAX = 60 * 60      # owner ceiling: idle at most one hour
RUNGUP_PROBATION_JOBS = 5       # a block this soon after a rung-up may be rate


def rung_after_block(rung, jobs_since_rungup):
    """Rung to hold after a block.

    `jobs_since_rungup` is None outside escalation probation. Inside it, the
    block plausibly answers the escalation, so step back; otherwise freeze.
    """
    if jobs_since_rungup is not None and jobs_since_rungup <= RUNGUP_PROBATION_JOBS:
        return max(0, int(rung) - 1), True
    return int(rung), False


def should_ping_owner(blocks_this_run, recent_outcomes, *, route="primary_route"):
    """True when an automated-route block must stop for owner routing.

    The persistent operator-visible route sends its own immediate notification
    for every distinct block and waits for manual clearance; it never inherits
    this automated stop ceiling.
    """
    recent = list(recent_outcomes)
    consecutive = len(recent) >= 2 and recent[-2] == "blocked"
    if route == "persistent_realchrome":
        return False, consecutive
    return (consecutive or blocks_this_run >= 3), consecutive


def write_owner_ping(ping_path, *, job_id, reason, counts, timestamp,
                     extra=None):
    """Write the owner-routing ping. Returns the path written."""
    import json
    import os
    from pathlib import Path as _Path
    payload = {"reason": reason, "at": timestamp, "job_id": job_id,
               "counts": dict(counts),
               "doctrine": "F2b/F3: a block is a flag, not a rate signal; "
                           "idle <=60min then ONE recovery attempt; owner "
                           "routes the resume",
               "decay_note": "sealed series: 10-17min gaps failed 6x; "
                             "12.5 and 14.7min cleared once each; elapsed "
                             "idle alone does not predict clearance"}
    if extra:
        payload.update(extra)
    target = _Path(ping_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.tmp.{os.getpid()}")
    encoded = (json.dumps(payload, indent=1) + "\n").encode("utf-8")
    with temporary.open("xb") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, target)
    return str(target)

if __name__ == "__main__":
    for i, c in enumerate(RATE_LADDER):
        burst_min = REST_EVERY * c / 60.0
        sust = effective_rate(c)
        note = "measured clean" if i <= RUNG_PROVEN_THROUGH else (
            "above all clean evidence" if sust > 60.0 else "reached, thin evidence")
        print(f"rung {i:2d}: {c:5.1f}s cycle -> {sust:4.1f}/hr sustained, "
              f"~{sust*1.067:4.1f}/hr peak-30min, {3600.0/c:5.1f}/hr inst, "
              f"burst {burst_min:4.1f}min + {REST_SECONDS/60:.0f}min rest "
              f"({note})")
    print(f"\nreference: one block observed at 82/hr peak-30min; "
          f"64/hr peak-30min ran 151 captures clean")
