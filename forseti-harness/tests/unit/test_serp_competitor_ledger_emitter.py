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

import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

RUNNER = Path(__file__).resolve().parents[2] / "runners" / "serp_competitor_ledger_emitter.py"
T28 = Path(r"C:\tmp\forseti-tower28-scout-20260727")
MEGA = Path(r"C:\tmp\forseti-serp-megadogfood-20260727")

SPEC = importlib.util.spec_from_file_location("serp_competitor_ledger_emitter",
                                              RUNNER)
EMITTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EMITTER)

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
                        "--output", str(out)], check=True, capture_output=True)
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


def write_synthetic_extractions(path, titles):
    path.mkdir()
    for i, title in enumerate(titles):
        packet = {
            "requested_query": f"query-{i}",
            "rows": [{"module_type": "organic", "title": title}],
        }
        (path / f"{i}.json").write_text(json.dumps(packet), encoding="utf-8")


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


# ---- v0.2/v0.3: adjudicated recall, cleanup, and promotion gate ----------

VERDICTS = MEGA / "analysis" / "candidate_verdicts_v0.json"
requires_verdicts = pytest.mark.skipif(
    not VERDICTS.exists(),
    reason=f"verdicts cache absent: {VERDICTS}")


@pytest.fixture(scope="module")
def mega_gated():
    return run(["--verdicts", str(VERDICTS)])


@requires_mega
def test_enum_comma_list_recall(mega):
    # "Korean Sunscreen Reviews: Beauty of Joseon, Isntree, ..." was one of
    # 70 zero-yield titles in v0.1; the enumeration branch must recover it.
    assert entry(mega, "beauty of joseon sunscreen", "isntree", "rival")


def test_possessive_apostrophe_subject_matching():
    brand = EMITTER.brand_tokens("Paula's Choice BHA Exfoliant")
    assert EMITTER.matches_subject("Paula’s Choice vs The Ordinary", brand)
    assert EMITTER.matches_subject("Paula Choice or La Roche-Posay", brand)


@requires_mega
def test_context_compounds_collapse_and_conditions_fail_closed(mega):
    aquaphor = [e for e in mega["entries"]
                if e["subject"] == "aquaphor healing ointment"]
    assert any(e["name"].lower() == "vaseline" for e in aquaphor)
    assert not any(e["name"].lower().startswith("vaseline for ")
                   for e in aquaphor)
    assert not any("irritated skin" in e["name"].lower()
                   for e in mega["entries"])


@requires_mega
@requires_verdicts
def test_gate_candidate_rung_is_all_usable(mega_gated):
    # With a verdicts cache, nothing reaches candidate without USABLE.
    vd = json.loads(VERDICTS.read_text(encoding="utf-8"))
    usable = {(v["subject"], v["name"].lower()) for v in vd["verdicts"]
              if v["verdict"] == "USABLE"}
    for e in mega_gated["entries"]:
        if e["rung"] == "candidate":
            assert (e["subject"], e["name"].lower()) in usable, e["name"]


@requires_mega
@requires_verdicts
def test_gate_junk_never_candidate(mega_gated):
    # The 2026-07-28 hand adjudication's worst offenders stay off the rung.
    for subj, name in (("medicube collagen mask", "real"),
                       ("hoka clifton 9", "nah"),
                       ("aquaphor healing ointment", "benefits")):
        assert not any(e["subject"] == subj and e["name"].lower() == name
                       and e["rung"] == "candidate"
                       for e in mega_gated["entries"])


@requires_mega
@requires_verdicts
def test_self_variants_use_ratified_type(mega_gated):
    flagged = [e for e in mega_gated["entries"]
               if e.get("verdict") == "SELF_VARIANT"]
    assert flagged
    assert all(e["type"] == "self_variant" for e in flagged)


@requires_mega
@requires_verdicts
def test_gate_fails_closed_on_unadjudicated(mega_gated):
    # Any recurring entry missing a verdict must be pending, never candidate.
    vd = json.loads(VERDICTS.read_text(encoding="utf-8"))
    known = {(v["subject"], v["name"].lower()) for v in vd["verdicts"]}
    for e in mega_gated["entries"]:
        if e["distinct_queries"] >= 2 and \
                (e["subject"], e["name"].lower()) not in known:
            assert e["rung"] == "pending_adjudication", e["name"]


def test_missing_verdict_cache_still_enables_fail_closed_gate(tmp_path):
    extractions = tmp_path / "extractions"
    write_synthetic_extractions(
        extractions, ["Acme vs RivalCo", "Acme vs RivalCo"])
    base = ["--extractions", str(extractions), "--subject", "Acme"]

    ungated = run(base)
    gated = run([*base, "--verdicts", str(tmp_path / "missing.json")])

    assert any(e["name"] == "RivalCo" and e["rung"] == "candidate"
               for e in ungated["entries"])
    assert any(e["name"] == "RivalCo"
               and e["rung"] == "pending_adjudication"
               for e in gated["entries"])


def test_empty_mediator_cache_emits_parallel_pending_map(tmp_path):
    extractions = tmp_path / "extractions"
    write_synthetic_extractions(extractions, ["Acme on Instagram"])
    cache = tmp_path / "mediators.json"
    cache.write_text(json.dumps({"mediators": []}), encoding="utf-8")

    result = run(["--extractions", str(extractions), "--subject", "Acme",
                  "--mediator-classes", str(cache)])

    assert result["mediators"] == {"Acme (instagram)": ["Acme"]}
    assert result["mediator_classes"] == {
        "Acme (instagram)": "pending_classification"}
