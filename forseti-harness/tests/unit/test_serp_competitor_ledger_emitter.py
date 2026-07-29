"""Pinned-fixture regression check for the SERP competitor-ledger emitter.

Runs the emitter on both stores and asserts the real names it must find
and the junk it must not. Presence-based (robust to store growth).
Run after ANY emitter edit; a silent regression (like the NYX drop
caught 2026-07-28) fails loudly here.

Fixture stores live on the operator drive, so this test SKIPS rather
than fails when they are absent (a fresh clone, CI, another machine).
A skip is not a pass: the emitter's behavior contract is only actually
checked where the stores exist. Promoted 2026-07-28 alongside the
emitter; the path defect that made this file uncollectable on
promotion (it invoked the pre-promotion filename in its own directory)
was fixed the same day.
"""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from runners.serp_competitor_ledger_emitter import harvest

RUNNER = Path(__file__).resolve().parents[2] / "runners" / "serp_competitor_ledger_emitter.py"
T28 = Path(r"C:\tmp\forseti-tower28-scout-20260727")
MEGA = Path(r"C:\tmp\forseti-serp-megadogfood-20260727")

requires_t28 = pytest.mark.skipif(
    not (T28 / "extracted_v2").is_dir(),
    reason=f"operator-drive fixture store absent: {T28 / 'extracted_v2'}")
requires_mega = pytest.mark.skipif(
    not (MEGA / "extracted").is_dir(),
    reason=f"operator-drive fixture store absent: {MEGA / 'extracted'}")


def run(args):
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "ledger.json"
        subprocess.run([sys.executable, "-B", str(RUNNER), *args,
                        "--output", str(out)], check=True, capture_output=True,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        return json.loads(out.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def t28():
    return run(["--extractions", str(T28 / "extracted_v2"),
                "--subject", "tower 28 swipe concealer",
                "--subject", "tower 28",
                "--subject", "tower 28 sos spray"])


@pytest.fixture(scope="module")
def mega():
    return run([])


def entry(d, subject, name_part, typ):
    return any(e["subject"] == subject and typ == e["type"]
               and name_part.lower() in e["name"].lower()
               for e in d["entries"])


# Tower 28 store: real names, correct types/directions
@requires_t28
def test_nyx_is_dupe_association_direction(t28):
    assert entry(t28, "tower 28 swipe concealer", "nyx", "dupe_association")


@requires_t28
def test_hourglass_is_anchor_up(t28):
    assert entry(t28, "tower 28 swipe concealer", "hourglass", "anchor_up")


@requires_t28
def test_saie_found_as_rival(t28):
    assert entry(t28, "tower 28 swipe concealer", "saie", "rival")


@requires_t28
def test_haus_labs_found_via_or_pattern(t28):
    assert entry(t28, "tower 28 swipe concealer", "haus labs", "rival")


@requires_t28
def test_outlets_routed_to_mediators_not_ledger(t28):
    assert not any("you beauty" in e["name"].lower() for e in t28["entries"])
    assert any("You Beauty" in m for m in t28["mediators"])


@requires_t28
def test_use_context_junk_rejected(t28):
    assert not any("prone skin" in e["name"].lower() for e in t28["entries"])


# Megadogfood store: real candidates survive, junk stays dead
@requires_mega
def test_summer_fridays_rival_of_rhode(mega):
    assert entry(mega, "rhode peptide lip treatment", "summer fridays", "rival")


@requires_mega
def test_amazon_basics_candidate_rung(mega):
    assert any(e["subject"] == "cerave moisturizing cream"
               and "amazon basics" in e["name"].lower()
               and e["rung"] == "candidate" for e in mega["entries"])


@requires_mega
def test_vanicream_found(mega):
    assert entry(mega, "cerave moisturizing cream", "vanicream", "rival")


@requires_mega
def test_imperative_junk_dead(mega):
    assert not any(e["name"].lower().startswith(("recommend", "find your"))
                   for e in mega["entries"])


@requires_mega
def test_bare_context_word_body_not_a_name(mega):
    assert not any(e["name"].lower() == "body" for e in mega["entries"])


@requires_mega
def test_no_question_word_fragment_names(mega):
    assert not any(e["name"].lower().startswith(("what ", "which ", "how "))
                   for e in mega["entries"])


@pytest.mark.parametrize(
    ("title", "junk"),
    [
        ("Cetaphil gentle cleanser vs bad", "bad"),
        (
            "Crest whitening strips vs 30 levels whiter. 7. 4. Why",
            "30 levels whiter",
        ),
        ("Crest whitening strips vs I brush my teeth before", "brush my teeth"),
        (
            "CeraVe moisturizing cream vs 86 Reddit-Picked",
            "reddit-picked",
        ),
    ],
)
def test_surfaced_title_fragments_never_emit(title, junk):
    emitted = list(
        harvest(
            [("serp_result_title", title)],
            title.split(" vs ", 1)[0],
            title,
        )
    )
    assert not any(junk in str(item[0]).lower() for item in emitted)
