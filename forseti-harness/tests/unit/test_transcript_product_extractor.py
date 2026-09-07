"""Pass 1 transcript product extractor: offline tests with a fake transport.

No network, no credentials. Verifies the D1-D8 doctrine prompt, identity-from-transcript
(CE1), the CE5+CE9 quote-locator (timestamp from the cue; fabricated/unlocatable quote
rejected), closed-enum + range guards (CE3), creator-stated-rating-as-evidence (CE10), and
that a ProductMention carries no verdict field (CE4).
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from cleaning.raw_model_transport import RawApiProvider
from cleaning.transcript_product_extractor import (
    TranscriptInput,
    build_extraction_prompt,
    extract_transcript_products,
    locate_quote,
    parse_mentions,
)
from schemas.product_mention_models import ProductMention


class FakeTransport:
    def __init__(self, canned_response: str) -> None:
        self.canned_response = canned_response
        self.last_body: dict[str, Any] | None = None

    def post_json(self, url, headers, body, timeout_seconds):  # noqa: ANN001
        self.last_body = body
        return self.canned_response


def _cues() -> list[dict]:
    return [
        {"start_ms": 1000, "end_ms": 3000, "text": "Today I'm testing Dior Sauvage Elixir"},
        {"start_ms": 3000, "end_ms": 6000, "text": "and it is an absolute beast in the heat"},
        {"start_ms": 6000, "end_ms": 9000, "text": "I'd give it a solid 8 out of 10 honestly"},
    ]


def _transcript(**over: Any) -> TranscriptInput:
    base = dict(
        video_id="vid12345678",
        transcript_anchor="ANCHOR01",
        transcript_source="asr",
        cues=_cues(),
    )
    base.update(over)
    return TranscriptInput(**base)


def _item(**over: Any) -> dict[str, Any]:
    base = dict(
        brand="Dior",
        line="Sauvage Elixir",
        concentration="elixir",
        stance_vote=0.8,
        creator_authored=True,
        possible_negation_or_irony=False,
        extractor_confidence=0.9,
        source_pointer="absolute beast in the heat",
    )
    base.update(over)
    return base


def _anthropic(items: list[dict[str, Any]] | str) -> str:
    text = items if isinstance(items, str) else json.dumps(items)
    return json.dumps({"content": [{"type": "text", "text": text}]})


def _extract(canned: str, transcript: TranscriptInput | None = None):
    transport = FakeTransport(canned)
    result = extract_transcript_products(
        transcript or _transcript(),
        transport=transport,
        provider=RawApiProvider.ANTHROPIC_MESSAGES,
        model="test-model",
        api_key="test-key",
    )
    return result, transport


# --- happy path + CE5 (timestamp from the cue, not the model) ----------------


def test_parses_valid_mention_and_timestamps_from_cue() -> None:
    result, _ = _extract(_anthropic([_item()]))
    assert len(result.mentions) == 1
    assert result.rejected == []
    m = result.mentions[0]
    assert m.brand == "Dior"
    assert m.line == "Sauvage Elixir"
    assert m.concentration.value == "elixir"
    # CE5: the quote lives in cue 2 -> its [3000, 6000] span, code-assigned.
    assert (m.start_ms, m.end_ms) == (3000, 6000)
    assert m.mention_id == "ANCHOR01:0"


def test_quote_spanning_two_cues_takes_first_start_last_end() -> None:
    result, _ = _extract(_anthropic([_item(source_pointer="Dior Sauvage Elixir and it is")]))
    assert len(result.mentions) == 1
    assert (result.mentions[0].start_ms, result.mentions[0].end_ms) == (1000, 6000)


# --- CE9: fabricated / unlocatable quote is rejected --------------------------


def test_rejects_quote_not_in_transcript() -> None:
    result, _ = _extract(_anthropic([_item(source_pointer="this phrase is nowhere in the audio")]))
    assert result.mentions == []
    assert len(result.rejected) == 1
    assert "CE9" in result.rejected[0]["reason"]


def test_rejects_empty_quote() -> None:
    result, _ = _extract(_anthropic([_item(source_pointer="")]))
    assert result.mentions == []
    assert len(result.rejected) == 1


# --- CE1: identity comes from the transcript, never the model -----------------


def test_identity_from_transcript_not_model() -> None:
    sneaky = _item(video_id="evil", transcript_anchor="evil", mention_id="evil", malicious="x")
    result, _ = _extract(_anthropic([sneaky]))
    assert len(result.mentions) == 1
    m = result.mentions[0]
    assert m.video_id == "vid12345678"
    assert m.transcript_anchor == "ANCHOR01"
    assert m.mention_id == "ANCHOR01:0"


# --- CE3: closed enum + range guards reject, never store ----------------------


def test_rejects_bad_concentration() -> None:
    result, _ = _extract(_anthropic([_item(concentration="spray")]))
    assert result.mentions == []
    assert len(result.rejected) == 1


def test_rejects_out_of_range_stance() -> None:
    result, _ = _extract(_anthropic([_item(stance_vote=5.0)]))
    assert result.mentions == []
    assert len(result.rejected) == 1


def test_uppercase_concentration_is_normalized() -> None:
    result, _ = _extract(_anthropic([_item(concentration="ELIXIR")]))
    assert len(result.mentions) == 1
    assert result.mentions[0].concentration.value == "elixir"


# --- CE10: creator-stated rating is evidence, verified by its own quote --------


def test_stated_rating_with_real_quote_is_kept() -> None:
    item = _item(stated_rating={"value": 8, "scale_max": 10, "source_pointer": "8 out of 10"})
    result, _ = _extract(_anthropic([item]))
    assert len(result.mentions) == 1
    rating = result.mentions[0].stated_rating
    assert rating is not None and rating.value == 8


def test_stated_rating_with_fake_quote_is_dropped_mention_kept() -> None:
    item = _item(stated_rating={"value": 9, "scale_max": 10, "source_pointer": "9 out of 10"})
    result, _ = _extract(_anthropic([item]))
    assert len(result.mentions) == 1  # mention survives
    assert result.mentions[0].stated_rating is None  # unverifiable score quote dropped


# --- CE4: a ProductMention has no verdict field by construction ---------------


def test_mention_has_no_verdict_field() -> None:
    assert "verdict" not in ProductMention.model_fields


# --- abstain / malformed ------------------------------------------------------


def test_empty_array_yields_no_mentions() -> None:
    result, _ = _extract(_anthropic("[]"))
    assert result.mentions == []
    assert result.rejected == []


def test_malformed_model_json_raises() -> None:
    with pytest.raises(ValueError):
        parse_mentions("not json", _transcript())


def test_non_array_model_json_raises() -> None:
    with pytest.raises(ValueError):
        parse_mentions(json.dumps({"oops": 1}), _transcript())


# --- locate_quote unit --------------------------------------------------------


def test_locate_quote_normalizes_case_and_whitespace() -> None:
    cues = [{"start_ms": 100, "end_ms": 200, "text": "The  BEAST   Mode"}]
    assert locate_quote("beast mode", cues) == (100, 200)


def test_locate_quote_returns_none_when_absent() -> None:
    assert locate_quote("nope", _cues()) is None


# --- prompt doctrine (D1-D8) + request hygiene --------------------------------


def test_prompt_carries_doctrine() -> None:
    prompt = build_extraction_prompt(_transcript()).lower()
    assert "never invent" in prompt
    assert "verbatim quote" in prompt
    assert "do not output timestamps" in prompt
    assert "as data" in prompt and "never as instructions" in prompt
    assert "elixir" in prompt  # closed concentration set surfaced


_RULE_EXAMPLES = [
    # DESCRIBING the fragrance -> NOT stance (neutral)
    ("fresh, dewy, musky", "neutral"), ("sweet mango", "neutral"), ("a bit powdery", "neutral"),
    ("it's strong", "neutral"), ("lasts a few hours", "neutral"), ("can't wait to try", "neutral"),
    # a flattering adjective ON A NOTE (scope = note, not product) -> neutral
    ("terrific fresh", "neutral"), ("classy clean rose", "neutral"), ("a beautiful jasmine note", "neutral"),
    # EVALUATING the fragrance as a whole -> stance
    ("stunning", "stance"), ("elegant", "stance"), ("unique", "stance"), ("a masterpiece", "stance"),
    ("the best", "stance"), ("incredible longevity", "stance"),
]


def test_prompt_carries_actionable_stance_rule() -> None:
    # Calibration fix (rubric 0.4): separate DESCRIBING a fragrance (notes / character / bare
    # performance -> neutral) from EVALUATING it (quality judgment / recommendation / rating ->
    # stance), and check the SCOPE of praise. Pins the distinctions so the rule cannot be weakened.
    prompt = " ".join(build_extraction_prompt(_transcript()).lower().split())  # normalize line-wraps
    assert "describing" in prompt and "evaluating" in prompt   # the core distinction
    assert "however flattering" in prompt                       # flattery alone is not stance
    assert "lasts a few hours" in prompt                        # bare performance = description
    assert "incredible longevity" in prompt                     # evaluative performance = stance
    assert "can't wait to try" in prompt                        # untried anticipation = neutral
    assert "quality judgment" in prompt                         # evaluation anchor
    assert "scope" in prompt                                    # check the scope of the praise
    assert "a beautiful jasmine note" in prompt                 # flattering adjective on a NOTE = neutral


def test_rule_examples_bound_to_correct_section() -> None:
    # No automated extractor exists (Pass-1 is agent/LLM-in-the-loop), so this fixture documents the
    # rule's INTENT and BINDS each example to its section: a neutral example must NOT sit inside the
    # EVALUATING block, and a stance example MUST. Moving a neutral example under EVALUATING fails here.
    prompt = " ".join(build_extraction_prompt(_transcript()).lower().split())  # normalize line-wraps
    assert "evaluating (is stance" in prompt and "scope test" in prompt
    eval_block = prompt.split("evaluating (is stance", 1)[1].split("scope test", 1)[0]
    for phrase, cls in _RULE_EXAMPLES:
        p = phrase.lower()
        assert p in prompt, f"rule example missing from rubric: {phrase!r}"
        if cls == "stance":
            assert p in eval_block, f"stance example not in EVALUATING block: {phrase!r}"
        else:
            assert p not in eval_block, f"neutral example wrongly inside EVALUATING block: {phrase!r}"


def test_request_body_has_no_forbidden_keys() -> None:
    _, transport = _extract(_anthropic([_item()]))
    assert set(transport.last_body) <= {"model", "max_tokens", "messages"}


# --- additional CE coverage (review-driven) ----------------------------------


def test_stated_rating_with_bad_scale_max_is_dropped() -> None:
    # quote is real (passes CE9) but scale_max=0 -> StatedRating rejects -> rating dropped, mention kept.
    item = _item(stated_rating={"value": 8, "scale_max": 0, "source_pointer": "8 out of 10"})
    transcript = _transcript(
        cues=_cues() + [{"start_ms": 6000, "end_ms": 9000, "text": "honestly a solid 8 out of 10"}]
    )
    result, _ = _extract(_anthropic([item]), transcript)
    assert len(result.mentions) == 1
    assert result.mentions[0].stated_rating is None


def test_provenance_stamps_model_version() -> None:
    result, _ = _extract(_anthropic([_item()]))
    prov = result.mentions[0].provenance
    assert prov["model_version"] == "test-model"  # R1: per-mention model stamp
    assert prov["rubric_version"]


def test_locate_quote_tolerates_unicode_whitespace_and_tabs() -> None:
    cues = [{"start_ms": 10, "end_ms": 20, "text": "beast mode\tcompliment getter"}]
    assert locate_quote("beast mode compliment getter", cues) == (10, 20)


def test_locate_quote_tolerates_nonbreaking_space() -> None:
    nbsp = chr(0x00A0)  # the \s normalization CE9 relies on must cover unicode whitespace
    cues = [{"start_ms": 10, "end_ms": 20, "text": f"beast{nbsp}mode{nbsp}getter"}]
    assert locate_quote("beast mode getter", cues) == (10, 20)


def test_brand_null_falls_back_to_unknown() -> None:
    # model returns JSON null for brand -> must coerce to "unknown", never the literal "None".
    result, _ = _extract(_anthropic([_item(brand=None)]))
    assert len(result.mentions) == 1
    assert result.mentions[0].brand == "unknown"


def test_brand_missing_falls_back_to_unknown() -> None:
    item = _item()
    del item["brand"]
    result, _ = _extract(_anthropic([item]))
    assert result.mentions[0].brand == "unknown"


def test_stated_rating_value_above_scale_max_is_dropped() -> None:
    transcript = _transcript(
        cues=_cues() + [{"start_ms": 6000, "end_ms": 9000, "text": "honestly a solid 8 out of 10"}]
    )
    item = _item(stated_rating={"value": 11, "scale_max": 10, "source_pointer": "8 out of 10"})
    result, _ = _extract(_anthropic([item]), transcript)
    assert len(result.mentions) == 1
    assert result.mentions[0].stated_rating is None  # value > scale_max -> dropped


def test_stated_rating_nan_value_is_dropped() -> None:
    # a hostile model emitting a bare NaN must not persist a non-finite, non-RFC-JSON rating.
    transcript = _transcript(
        cues=_cues() + [{"start_ms": 6000, "end_ms": 9000, "text": "a solid 8 out of 10"}]
    )
    item = _item(stated_rating={"value": float("nan"), "scale_max": 10, "source_pointer": "8 out of 10"})
    result, _ = _extract(_anthropic([item]), transcript)
    assert len(result.mentions) == 1
    assert result.mentions[0].stated_rating is None


def test_stated_rating_non_dict_or_missing_value_dropped() -> None:
    r1, _ = _extract(_anthropic([_item(stated_rating="8/10")]))  # non-dict
    assert r1.mentions[0].stated_rating is None
    r2, _ = _extract(_anthropic([_item(stated_rating={"scale_max": 10, "source_pointer": "absolute beast in the heat"})]))
    assert r2.mentions[0].stated_rating is None  # missing "value"


def test_null_line_is_rejected() -> None:
    result, _ = _extract(_anthropic([_item(line=None)]))
    assert result.mentions == []
    assert len(result.rejected) == 1


def test_blank_brand_falls_back_to_unknown() -> None:
    result, _ = _extract(_anthropic([_item(brand="   ")]))
    assert len(result.mentions) == 1
    assert result.mentions[0].brand == "unknown"


def test_mention_rejects_nonfinite_stance_or_confidence() -> None:
    # pydantic ge/le rejects NaN/inf; lock it so a future switch to comparison validators regresses loudly.
    for bad in [_item(stance_vote=float("nan")), _item(stance_vote=float("inf")),
                _item(extractor_confidence=float("nan"))]:
        result, _ = _extract(_anthropic([bad]))
        assert result.mentions == []
        assert len(result.rejected) == 1


def test_stated_rating_inf_scale_max_is_dropped() -> None:
    transcript = _transcript(
        cues=_cues() + [{"start_ms": 6000, "end_ms": 9000, "text": "a solid 8 out of 10"}]
    )
    item = _item(stated_rating={"value": 8, "scale_max": float("inf"), "source_pointer": "8 out of 10"})
    result, _ = _extract(_anthropic([item]), transcript)
    assert len(result.mentions) == 1
    assert result.mentions[0].stated_rating is None  # math.isfinite(scale_max) guard


def test_product_mention_requires_source_pointer_directly() -> None:
    # CE2 defense-in-depth: locked at the schema even though the extractor never passes an empty quote.
    with pytest.raises(Exception):
        ProductMention(
            mention_id="a:0", video_id="v", transcript_anchor="A", transcript_source="asr",
            brand="Dior", line="Sauvage", concentration="edt", stance_vote=0.0,
            source_pointer="", start_ms=0, end_ms=1, extractor_confidence=0.5,
        )


def test_locate_quote_empty_cues_is_none() -> None:
    assert locate_quote("anything", []) is None


def test_parse_over_empty_cues_rejects_all() -> None:
    result = parse_mentions(json.dumps([_item()]), _transcript(cues=[]))
    assert result.mentions == []
    assert len(result.rejected) == 1


def test_locate_quote_multiple_matches_takes_first_span() -> None:
    cues = [
        {"start_ms": 100, "end_ms": 200, "text": "great scent here"},
        {"start_ms": 5000, "end_ms": 6000, "text": "great scent here"},
    ]
    assert locate_quote("great scent here", cues) == (100, 200)


def test_parse_reuses_one_cue_scan_for_mentions_and_ratings() -> None:
    class CountedCues(list):
        scans = 0

        def __iter__(self):
            self.scans += 1
            return super().__iter__()

    cues = CountedCues(_cues())
    transcript = _transcript(cues=cues)
    items = [
        _item(stated_rating={"value": 8, "source_pointer": "8 out of 10" if i % 2 else "9 out of 10"})
        for i in range(12)
    ]
    result = parse_mentions(json.dumps(items), transcript)
    assert result.rejected == []
    assert len(result.mentions) == 12
    for i, mention in enumerate(result.mentions):
        assert mention.mention_id == f"ANCHOR01:{i}"
        assert (mention.start_ms, mention.end_ms) == (3000, 6000)
        assert (mention.stated_rating.value if mention.stated_rating else None) == (8 if i % 2 else None)
    assert cues.scans == 1

    # Reusing a TranscriptInput across calls must not retain a stale/global index.
    cues[1]["text"] = "a different observation"
    later = parse_mentions(json.dumps(items), transcript)
    assert later.mentions == []
    assert later.rejected == [
        {"index": str(i), "reason": "CE9: quote not found in transcript"} for i in range(12)
    ]
    assert cues.scans == 2


@pytest.mark.parametrize("model_text", ["not json", "{}"])
def test_parse_invalid_json_precedes_cue_access(model_text: str) -> None:
    with pytest.raises(ValueError):
        parse_mentions(model_text, _transcript(cues=[None]))


@pytest.mark.parametrize("items", [[], [None, 3, []]])
def test_parse_without_objects_does_not_access_transcript(items: list) -> None:
    result = parse_mentions(json.dumps(items), None)
    assert result.mentions == []
    assert result.rejected == [
        {"index": str(i), "reason": "item is not an object"} for i in range(len(items))
    ]


@pytest.mark.parametrize("items", [[], [None, 3, []], [{}, _item(source_pointer=" \t\n")]])
def test_parse_without_searchable_quotes_does_not_read_cues(items: list) -> None:
    result = parse_mentions(json.dumps(items), _transcript(cues=[None]))
    assert result.mentions == []
    assert result.rejected == [
        {"index": str(i), "reason": "CE9: quote not found in transcript" if isinstance(item, dict)
         else "item is not an object"}
        for i, item in enumerate(items)
    ]


def test_nonempty_quote_still_exposes_malformed_cue() -> None:
    with pytest.raises(AttributeError):
        parse_mentions(json.dumps([_item()]), _transcript(cues=[None]))
    with pytest.raises(AttributeError):
        locate_quote("a quote", [None])
    assert locate_quote(" \t", [None]) is None


@pytest.mark.parametrize(
    ("cues", "quote", "expected"),
    [
        ([{"start_ms": 10, "end_ms": 20, "text": "BEAST\u00a0mode"},
          {"text": "\t "},
          {"start_ms": 30, "end_ms": 40, "text": "compliment getter"},
          {"start_ms": 50, "end_ms": 60, "text": "beast mode compliment getter"}],
         " mode\ncompliment ", (10, 40)),
        ([{"start_ms": "10", "end_ms": "20", "text": 123}], "23", (10, 20)),
        ([{"start_ms": 10, "end_ms": 20, "text": None}], "None", (10, 20)),
        ([{"start_ms": "bad", "end_ms": 20, "text": "beast"},
          {"start_ms": 30, "end_ms": 40, "text": "beast"}], "beast", None),
        ([{"start_ms": 10, "text": "beast"}], "beast", None),
        ([{"start_ms": 10, "end_ms": None, "text": "beast"}], "beast", None),
        ([{"text": " \t"}], "beast", None),
        ([], "beast", None),
    ],
)
def test_quote_edge_cases_preserve_parse_and_wrapper_results(cues, quote, expected) -> None:
    assert locate_quote(quote, cues) == expected
    result = parse_mentions(json.dumps([_item(source_pointer=quote)]), _transcript(cues=cues))
    if expected is None:
        assert result.mentions == []
        assert result.rejected == [{"index": "0", "reason": "CE9: quote not found in transcript"}]
    else:
        assert result.rejected == []
        assert len(result.mentions) == 1
        assert (result.mentions[0].start_ms, result.mentions[0].end_ms) == expected
        assert result.mentions[0].source_pointer == quote
