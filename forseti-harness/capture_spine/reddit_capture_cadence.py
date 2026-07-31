"""Shared request pacing for the Reddit capture lane.

One home for both Reddit request streams -- the weekly listing grid and the
exact-thread dive -- because the value of the policy is that a source sees ONE
consistent pacing shape from us. Two runners each carrying their own copy would
drift, and the drift would be invisible until the streams looked different from
the outside.

Owner direction 2026-07-31, provisional ("for now"): a 31-46 second jittered
target measured START to START.

Two things that setting encodes, both learned the hard way:

- **Cycle, not gap.** The cadence numbers used to be the wait BETWEEN captures,
  slept after each one, so the real interval was the number plus however long
  the capture took. Measured on the www listing surface, captures run 18.9-33.9s,
  so the 2026-07-30 pass configured at "30s" actually hit Reddit about every 60s
  and a 44-61s setting spaced requests 74-91s apart. Under ``cycle`` the measured
  duration is subtracted and the configured number is the interval. Verified on
  the 2026-07-31 roster pass: observed 31.1-46.0s, mean 39.2s.

- **Jitter, not fixed.** The pass that ended in a total block ran 91 requests at
  exactly 30.0s intervals. A metronome is a machine signature regardless of how
  polite the interval is.

This module carries no capture authorization and no ToS claim; it only states
how fast the lane's own runners pace themselves.
"""

from __future__ import annotations

from source_capture.cadence import CadenceMode

REDDIT_CADENCE_MODE: CadenceMode = "bounded_jitter"
REDDIT_CADENCE_BASIS = "cycle"
REDDIT_CADENCE_MIN_GAP_SECONDS = 31.0
REDDIT_CADENCE_MAX_GAP_SECONDS = 46.0

__all__ = [
    "REDDIT_CADENCE_BASIS",
    "REDDIT_CADENCE_MAX_GAP_SECONDS",
    "REDDIT_CADENCE_MIN_GAP_SECONDS",
    "REDDIT_CADENCE_MODE",
]
