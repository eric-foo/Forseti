from pathlib import Path

from runners.run_google_serp_persistent_fallback_packet import (
    run_google_serp_persistent_fallback,
)
from source_capture.source_detail_sufficiency import (
    SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE,
)


def test_block_is_preserved_notified_once_and_exact_job_resumes(tmp_path: Path) -> None:
    output = tmp_path / "packet"
    archive = tmp_path / "blocked"
    capture_codes = iter((SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE, 0))
    inspections = iter(
        (
            {"access_blocked": True, "query": "held query"},
            {"access_blocked": False, "query": "held query"},
        )
    )
    notifications: list[dict] = []
    sleeps: list[float] = []

    def capture(**_kwargs):
        output.mkdir()
        (output / "manifest.json").write_text("{}\n", encoding="utf-8")
        code = next(capture_codes)
        return code, str(output)

    code, _ = run_google_serp_persistent_fallback(
        url="https://www.google.com/search?q=held+query",
        query="held query",
        job_id="job-1",
        output=output,
        block_archive=archive,
        cdp_endpoint="http://127.0.0.1:9223",
        marker="forseti.queue",
        decision_question="q",
        poll_seconds=0.25,
        capture_func=capture,
        inspect_func=lambda **_kwargs: next(inspections),
        notify_func=lambda **kwargs: notifications.append(kwargs),
        sleep_func=lambda seconds: sleeps.append(seconds),
    )

    assert code == 0
    assert len(notifications) == 1
    assert len(list(archive.glob("job-1_*"))) == 1
    assert not (archive / "block_alert.json").exists()
    assert sleeps == [0.25, 0.25]
    assert output.is_dir()


def test_clear_wrong_query_does_not_resume_navigation(tmp_path: Path) -> None:
    output = tmp_path / "packet"
    archive = tmp_path / "blocked"
    capture_codes = iter((SOURCE_DETAIL_SUFFICIENCY_EXIT_CODE, 0))
    inspections = iter(
        (
            {"access_blocked": False, "query": "another query"},
            {"access_blocked": False, "query": "held query"},
        )
    )

    def capture(**_kwargs):
        output.mkdir()
        return next(capture_codes), str(output)

    code, _ = run_google_serp_persistent_fallback(
        url="https://www.google.com/search?q=held+query",
        query="held query",
        job_id="job-2",
        output=output,
        block_archive=archive,
        cdp_endpoint="http://127.0.0.1:9223",
        marker="forseti.queue",
        decision_question="q",
        poll_seconds=0,
        capture_func=capture,
        inspect_func=lambda **_kwargs: next(inspections),
        notify_func=lambda **_kwargs: None,
        sleep_func=lambda _seconds: None,
    )

    assert code == 0
