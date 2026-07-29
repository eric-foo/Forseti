"""Contract tests for the shared block-response policy (F2b/F3).

These pin the behavior that egress safety depends on, so a future edit to
the cadence module cannot quietly restore the pre-F2b "step down and
re-probe" policy that the sealed decay series showed is useless.

Stdlib + pytest only; no operator-drive fixtures, so this runs anywhere.
"""
import json
import sys
from pathlib import Path

import pytest

RUNNERS = Path(__file__).resolve().parents[2] / "runners"
sys.path.insert(0, str(RUNNERS))

import serp_egress_cadence as CAD  # noqa: E402


class TestRungAfterBlock:
    def test_block_outside_probation_freezes_the_rung(self):
        # The core F2b claim: a block that does not answer an escalation is
        # a flag, and rate reduction cannot clear a flag.
        assert CAD.rung_after_block(8, None) == (8, False)

    def test_block_long_after_a_rungup_freezes(self):
        assert CAD.rung_after_block(8, CAD.RUNGUP_PROBATION_JOBS + 1) == (8, False)

    def test_block_inside_probation_steps_back_one_rung(self):
        assert CAD.rung_after_block(8, 1) == (7, True)
        assert CAD.rung_after_block(8, CAD.RUNGUP_PROBATION_JOBS) == (7, True)

    def test_never_steps_below_zero(self):
        assert CAD.rung_after_block(0, 1) == (0, True)

    def test_probation_window_is_not_silently_widened(self):
        # A wide window would re-create the old step-down-on-every-block
        # behavior by accident.
        assert CAD.RUNGUP_PROBATION_JOBS <= 5


class TestShouldPingOwner:
    def test_first_isolated_block_does_not_ping(self):
        ping, consecutive = CAD.should_ping_owner(1, ["ok", "ok", "blocked"])
        assert ping is False and consecutive is False

    def test_two_consecutive_blocks_ping(self):
        ping, consecutive = CAD.should_ping_owner(2, ["ok", "blocked", "blocked"])
        assert ping is True and consecutive is True

    def test_third_block_pings_even_when_not_consecutive(self):
        ping, consecutive = CAD.should_ping_owner(3, ["blocked", "ok", "blocked"])
        assert ping is True and consecutive is False

    def test_short_history_is_safe(self):
        assert CAD.should_ping_owner(1, ["blocked"])[0] is False
        assert CAD.should_ping_owner(1, [])[0] is False

    def test_persistent_operator_route_never_inherits_automated_stop_ceiling(self):
        ping, consecutive = CAD.should_ping_owner(
            3,
            ["blocked", "blocked"],
            route="persistent_realchrome",
        )
        assert ping is False
        assert consecutive is True


class TestIdleCeiling:
    def test_idle_ceiling_is_the_owner_ratified_hour(self):
        # Owner rule 2026-07-29: idle at most one hour, then ping - never
        # the autonomous multi-hour cooldowns this replaced.
        assert CAD.IDLE_SECONDS_MAX == 60 * 60


class TestWriteOwnerPing:
    def test_ping_carries_the_state_an_owner_needs_to_route(self, tmp_path):
        p = tmp_path / "OWNER_PING.json"
        CAD.write_owner_ping(p, job_id="j0042", reason="second consecutive block",
                             counts={"ok": 10, "blocked": 2},
                             timestamp="2026-07-30 00:14:16",
                             extra={"query": "olaplex no 3 side effects"})
        d = json.loads(p.read_text(encoding="utf-8"))
        assert d["job_id"] == "j0042"
        assert d["reason"] == "second consecutive block"
        assert d["counts"] == {"ok": 10, "blocked": 2}
        assert d["at"] == "2026-07-30 00:14:16"
        assert d["query"] == "olaplex no 3 side effects"
        # the doctrine travels with the ping so the owner is not reading it
        # out of a doc at 3am
        doctrine = d["doctrine"].lower()
        assert "flag" in doctrine and "one recovery attempt" in doctrine
        assert "decay_note" in d

    def test_extra_cannot_silently_drop_required_fields(self, tmp_path):
        p = tmp_path / "ping.json"
        CAD.write_owner_ping(p, job_id="j1", reason="r", counts={},
                             timestamp="t", extra={"job_id": "override"})
        d = json.loads(p.read_text(encoding="utf-8"))
        # extra may override deliberately, but every required key survives
        assert set(("reason", "at", "job_id", "counts", "doctrine")) <= set(d)
