"""Unit tests for ace_step.orchestrator."""

import json
from pathlib import Path

import pytest

from ace_step import orchestrator
from ace_step.kaggle_client import KaggleResourceError


def _base_kwargs(**overrides):
    kwargs = dict(
        prompt="epic metal",
        duration=60.0,
        seed=42,
        bpm=None,
        keyscale=None,
        vocal_language="en",
        lufs_target=-9.0,
    )
    kwargs.update(overrides)
    return kwargs


def _write_result_json(pulled_dir: Path, **fields):
    output_dir = pulled_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generation_status": "done",
        "generation_error": None,
        "stems_status": "done",
        "stems_error": None,
    }
    payload.update(fields)
    (output_dir / "result.json").write_text(json.dumps(payload), encoding="utf-8")
    return output_dir


def _write_raw_and_stems(output_dir: Path, *, raw_bytes=b"RIFF-fake-wav-bytes", with_stems=True):
    (output_dir / "raw.wav").write_bytes(raw_bytes)
    if with_stems:
        stems_dir = output_dir / "stems"
        stems_dir.mkdir(parents=True, exist_ok=True)
        for name in ("vocals", "drums", "bass", "guitar", "piano", "other"):
            (stems_dir / f"{name}.wav").write_bytes(b"stem-bytes")


def _stub_common(monkeypatch, updates, *, tmp_path):
    monkeypatch.setattr(
        orchestrator.song_db,
        "update_song",
        lambda db, song_id, **fields: updates.append(fields),
    )
    monkeypatch.setattr(
        orchestrator.song_lyrics, "generate_lyrics", lambda prompt, language: "[en]\n[Verse]\nx"
    )
    monkeypatch.setattr(
        orchestrator.kernel_render, "render_job_kernel", lambda job, dest_dir: Path(dest_dir)
    )
    monkeypatch.setattr(orchestrator.kernels, "push_kernel", lambda folder: "owner/kernel")
    monkeypatch.setattr(
        orchestrator.kernels, "get_kernel_status", lambda ref: {"status": "complete", "failure_message": ""}
    )

    def fake_normalize_loudness(input_path, output_path, target_lufs):
        Path(output_path).write_bytes(Path(input_path).read_bytes())

    monkeypatch.setattr(orchestrator.song_mastering, "normalize_loudness", fake_normalize_loudness)


def test_run_generation_happy_path_returns_done_and_updates_db(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fake_pull_kernel_output(ref, dest_dir):
        output_dir = _write_result_json(Path(dest_dir))
        _write_raw_and_stems(output_dir)
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "done"
    assert detail == str(tmp_path / "1_master.wav")
    assert Path(detail).read_bytes() == b"RIFF-fake-wav-bytes"
    assert {"status": "generating", "lyrics": "[en]\n[Verse]\nx"} in updates
    assert {"status": "done", "output_path": str(tmp_path / "1_master.wav")} in updates
    done_update = next(u for u in updates if u.get("stems_status") == "done")
    for name in ("vocals", "drums", "bass", "guitar", "piano", "other"):
        expected_path = str(tmp_path / f"1_stem_{name}.wav")
        assert done_update[f"stem_{name}_path"] == expected_path
        assert Path(expected_path).read_bytes() == b"stem-bytes"
    assert not (tmp_path / ".kernel_1").exists()
    assert not (tmp_path / ".pulled_1").exists()


def test_run_generation_skips_lyrics_when_lyrics_given(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fail_if_called(*a, **k):
        raise AssertionError("generate_lyrics should not be called when lyrics is given")

    monkeypatch.setattr(orchestrator.song_lyrics, "generate_lyrics", fail_if_called)

    def fake_pull_kernel_output(ref, dest_dir):
        output_dir = _write_result_json(Path(dest_dir))
        _write_raw_and_stems(output_dir)
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, _detail = orchestrator.run_generation(
        db_path, tmp_path, 1, lyrics="[en]\n[Verse]\nready", **_base_kwargs()
    )

    assert status == "done"


def test_run_generation_records_error_when_push_kernel_fails(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fake_push_kernel(folder):
        raise KaggleResourceError("kernel invalido")

    monkeypatch.setattr(orchestrator.kernels, "push_kernel", fake_push_kernel)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "error"
    assert detail == "kernel invalido"
    assert {"status": "error", "error_message": "kernel invalido"} in updates


def test_run_generation_records_error_on_polling_timeout(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)
    monkeypatch.setattr(
        orchestrator.kernels, "get_kernel_status", lambda ref: {"status": "running", "failure_message": ""}
    )

    status, detail = orchestrator.run_generation(
        db_path, tmp_path, 1, timeout=0.05, poll_interval=0.01, **_base_kwargs()
    )

    assert status == "error"
    assert "Timeout" in detail
    assert "celsosoarescesar/ace-step-api" in detail


def test_run_generation_tolerates_transient_status_poll_failures(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    calls = {"count": 0}

    def flaky_get_kernel_status(ref):
        calls["count"] += 1
        if calls["count"] <= 2:
            raise KaggleResourceError("instabilidade transitoria")
        return {"status": "complete", "failure_message": ""}

    monkeypatch.setattr(orchestrator.kernels, "get_kernel_status", flaky_get_kernel_status)

    def fake_pull_kernel_output(ref, dest_dir):
        output_dir = _write_result_json(Path(dest_dir))
        _write_raw_and_stems(output_dir)
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, _detail = orchestrator.run_generation(
        db_path, tmp_path, 1, timeout=5.0, poll_interval=0.01, **_base_kwargs()
    )

    assert status == "done"
    assert calls["count"] >= 3


def test_run_generation_gives_up_after_too_many_consecutive_status_poll_failures(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def always_fails(ref):
        raise KaggleResourceError("instabilidade persistente")

    monkeypatch.setattr(orchestrator.kernels, "get_kernel_status", always_fails)

    def fail_if_called(ref, dest_dir):
        raise AssertionError("pull_kernel_output should not be called when polling never succeeds")

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fail_if_called)

    status, detail = orchestrator.run_generation(
        db_path, tmp_path, 1, timeout=5.0, poll_interval=0.01, **_base_kwargs()
    )

    assert status == "error"
    assert "instabilidade persistente" in detail


def test_run_generation_pulls_and_reports_generation_error_when_kernel_status_is_error(
    monkeypatch, tmp_path
):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)
    monkeypatch.setattr(
        orchestrator.kernels,
        "get_kernel_status",
        lambda ref: {"status": "error", "failure_message": "kernel crashou"},
    )

    def fake_pull_kernel_output(ref, dest_dir):
        _write_result_json(
            Path(dest_dir), generation_status="error", generation_error="cuda out of memory"
        )
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "error"
    assert "kernel crashou" in detail
    assert "cuda out of memory" in detail


def test_run_generation_falls_back_to_failure_message_when_pull_after_error_fails(
    monkeypatch, tmp_path
):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)
    monkeypatch.setattr(
        orchestrator.kernels,
        "get_kernel_status",
        lambda ref: {"status": "error", "failure_message": "kernel crashou"},
    )

    def fake_pull_kernel_output(ref, dest_dir):
        raise KaggleResourceError("kernel foi encerrado antes de escrever qualquer output")

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "error"
    assert "kernel crashou" in detail


def test_run_generation_records_error_when_result_json_missing(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fake_pull_kernel_output(ref, dest_dir):
        Path(dest_dir).mkdir(parents=True, exist_ok=True)
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "error"
    assert "result.json" in detail


def test_run_generation_records_error_when_result_json_is_malformed(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fake_pull_kernel_output(ref, dest_dir):
        output_dir = Path(dest_dir) / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "result.json").write_text("{not valid json", encoding="utf-8")
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "error"
    assert "result.json" in detail


def test_run_generation_records_error_when_generation_status_not_done(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fake_pull_kernel_output(ref, dest_dir):
        _write_result_json(
            Path(dest_dir), generation_status="error", generation_error="cuda out of memory"
        )
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "error"
    assert detail == "cuda out of memory"


def test_run_generation_records_error_when_raw_wav_missing_despite_done_status(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fake_pull_kernel_output(ref, dest_dir):
        _write_result_json(Path(dest_dir))  # says done, but never writes raw.wav
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "error"
    assert "raw.wav" in detail


def test_run_generation_records_stems_error_without_failing_generation(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fake_pull_kernel_output(ref, dest_dir):
        output_dir = _write_result_json(
            Path(dest_dir), stems_status="error", stems_error="cuda out of memory"
        )
        _write_raw_and_stems(output_dir, with_stems=False)
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "done"
    assert {
        "stems_status": "error", "stems_error_message": "cuda out of memory"
    } in updates


def test_run_generation_records_stems_error_when_stem_file_copy_fails(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fake_pull_kernel_output(ref, dest_dir):
        output_dir = _write_result_json(Path(dest_dir))  # says stems done
        _write_raw_and_stems(output_dir, with_stems=False)  # but no stem files exist
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "done"  # missing stems must never flip generation back to error
    error_update = next(u for u in updates if u.get("stems_status") == "error")
    assert "stems_error_message" in error_update
