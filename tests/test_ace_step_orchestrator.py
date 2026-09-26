"""Unit tests for kagglelab.orchestrator."""

from pathlib import Path

from ace_step import orchestrator


def _base_kwargs(**overrides):
    kwargs = dict(
        base_url="https://example.ngrok-free.dev",
        api_key="secret",
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


def test_run_generation_happy_path_returns_done_and_updates_db(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    monkeypatch.setattr(
        orchestrator.song_db,
        "update_song",
        lambda db, song_id, **fields: updates.append(fields),
    )
    monkeypatch.setattr(
        orchestrator.ace_step_client, "check_health", lambda base_url: {"status": "ok"}
    )
    monkeypatch.setattr(
        orchestrator.song_lyrics,
        "generate_lyrics",
        lambda prompt, language: "[en]\n[Verse]\nx",
    )
    monkeypatch.setattr(
        orchestrator.ace_step_client,
        "generate_music",
        lambda *a, **k: {"file": "/v1/audio?path=%2Ftmp%2Fa.wav"},
    )

    def fake_download_audio(base_url, api_key, file_path, dest_path):
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(b"RIFF-fake-wav-bytes")
        return dest_path

    monkeypatch.setattr(orchestrator.ace_step_client, "download_audio", fake_download_audio)

    def fake_normalize_loudness(input_path, output_path, target_lufs):
        Path(output_path).write_bytes(Path(input_path).read_bytes())

    monkeypatch.setattr(orchestrator.song_mastering, "normalize_loudness", fake_normalize_loudness)
    monkeypatch.setattr(orchestrator, "run_separation", lambda *a, **k: ("done", None))

    status, detail = orchestrator.run_generation(
        db_path, tmp_path, 1, **_base_kwargs()
    )

    assert status == "done"
    assert detail == str(tmp_path / "1_master.wav")
    assert Path(detail).read_bytes() == b"RIFF-fake-wav-bytes"
    assert {"status": "generating", "lyrics": "[en]\n[Verse]\nx"} in updates
    assert {"status": "done", "output_path": str(tmp_path / "1_master.wav")} in updates


def test_run_generation_returns_error_when_health_check_fails(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    monkeypatch.setattr(
        orchestrator.song_db,
        "update_song",
        lambda db, song_id, **fields: updates.append(fields),
    )

    def fake_check_health(base_url):
        raise orchestrator.ace_step_client.AceStepApiError("kernel nao esta rodando")

    monkeypatch.setattr(orchestrator.ace_step_client, "check_health", fake_check_health)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "error"
    assert detail == "kernel nao esta rodando"
    assert updates == [{"status": "error", "error_message": "kernel nao esta rodando"}]


def test_run_generation_skips_lyrics_when_lyrics_given(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    monkeypatch.setattr(orchestrator.song_db, "update_song", lambda *a, **k: None)
    monkeypatch.setattr(
        orchestrator.ace_step_client, "check_health", lambda base_url: {"status": "ok"}
    )

    def fail_if_called(*a, **k):
        raise AssertionError("generate_lyrics should not be called when lyrics is given")

    monkeypatch.setattr(orchestrator.song_lyrics, "generate_lyrics", fail_if_called)
    monkeypatch.setattr(
        orchestrator.ace_step_client,
        "generate_music",
        lambda *a, **k: {"file": "/v1/audio?path=%2Ftmp%2Fa.wav"},
    )

    def fake_download_audio(base_url, api_key, file_path, dest_path):
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(b"x")
        return dest_path

    monkeypatch.setattr(orchestrator.ace_step_client, "download_audio", fake_download_audio)
    monkeypatch.setattr(
        orchestrator.song_mastering,
        "normalize_loudness",
        lambda input_path, output_path, target_lufs: Path(output_path).write_bytes(b"x"),
    )

    monkeypatch.setattr(orchestrator, "run_separation", lambda *a, **k: ("done", None))

    status, _detail = orchestrator.run_generation(
        db_path, tmp_path, 1, lyrics="[en]\n[Verse]\nready", **_base_kwargs()
    )

    assert status == "done"


def test_run_generation_records_error_on_generation_exception(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    monkeypatch.setattr(
        orchestrator.song_db,
        "update_song",
        lambda db, song_id, **fields: updates.append(fields),
    )
    monkeypatch.setattr(
        orchestrator.ace_step_client, "check_health", lambda base_url: {"status": "ok"}
    )
    monkeypatch.setattr(
        orchestrator.song_lyrics,
        "generate_lyrics",
        lambda prompt, language: "[en]\n[Verse]\nx",
    )

    def fake_generate_music(*a, **k):
        raise orchestrator.ace_step_client.AceStepApiError("geracao falhou")

    monkeypatch.setattr(orchestrator.ace_step_client, "generate_music", fake_generate_music)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "error"
    assert detail == "geracao falhou"
    assert {"status": "error", "error_message": "geracao falhou"} in updates


def test_run_generation_saves_remote_file_ref(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    monkeypatch.setattr(
        orchestrator.song_db,
        "update_song",
        lambda db, song_id, **fields: updates.append(fields),
    )
    monkeypatch.setattr(
        orchestrator.ace_step_client, "check_health", lambda base_url: {"status": "ok"}
    )
    monkeypatch.setattr(
        orchestrator.song_lyrics,
        "generate_lyrics",
        lambda prompt, language: "[en]\n[Verse]\nx",
    )
    monkeypatch.setattr(
        orchestrator.ace_step_client,
        "generate_music",
        lambda *a, **k: {"file": "/v1/audio?path=%2Fkaggle%2Fworking%2Fa.wav"},
    )

    def fake_download_audio(base_url, api_key, file_path, dest_path):
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(b"x")
        return dest_path

    monkeypatch.setattr(orchestrator.ace_step_client, "download_audio", fake_download_audio)
    monkeypatch.setattr(
        orchestrator.song_mastering,
        "normalize_loudness",
        lambda input_path, output_path, target_lufs: Path(output_path).write_bytes(b"x"),
    )
    monkeypatch.setattr(orchestrator, "run_separation", lambda *a, **k: ("done", None))

    orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())


_SIX_STEMS = {
    "vocals": "/v1/stems?path=%2Fk%2Fvocals.wav",
    "drums": "/v1/stems?path=%2Fk%2Fdrums.wav",
    "bass": "/v1/stems?path=%2Fk%2Fbass.wav",
    "guitar": "/v1/stems?path=%2Fk%2Fguitar.wav",
    "piano": "/v1/stems?path=%2Fk%2Fpiano.wav",
    "other": "/v1/stems?path=%2Fk%2Fother.wav",
}


def test_run_separation_happy_path_downloads_all_six_stems_and_updates_db(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    monkeypatch.setattr(
        orchestrator.song_db,
        "update_song",
        lambda db, song_id, **fields: updates.append(fields),
    )
    monkeypatch.setattr(
        orchestrator.ace_step_client,
        "separate_stems",
        lambda base_url, api_key, file_path, **k: dict(_SIX_STEMS),
    )

    downloaded = []

    def fake_download_audio(base_url, api_key, file_path, dest_path):
        downloaded.append((file_path, str(dest_path)))
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(b"stem-bytes")
        return dest_path

    monkeypatch.setattr(orchestrator.ace_step_client, "download_audio", fake_download_audio)

    status, detail = orchestrator.run_separation(
        db_path,
        tmp_path,
        1,
        "/v1/audio?path=%2Fkaggle%2Fworking%2Fa.wav",
        base_url="https://example.ngrok-free.dev",
        api_key="secret",
    )

    assert status == "done"
    assert detail is None
    assert len(downloaded) == 6
    assert {"stems_status": "separating"} in updates
    done_update = next(u for u in updates if u.get("stems_status") == "done")
    for name in _SIX_STEMS:
        assert done_update[f"stem_{name}_path"] == str(tmp_path / f"1_stem_{name}.wav")


def test_run_separation_records_error_on_failure_without_raising(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    monkeypatch.setattr(
        orchestrator.song_db,
        "update_song",
        lambda db, song_id, **fields: updates.append(fields),
    )

    def fake_separate_stems(base_url, api_key, file_path, **k):
        raise orchestrator.ace_step_client.AceStepApiError("cuda out of memory")

    monkeypatch.setattr(orchestrator.ace_step_client, "separate_stems", fake_separate_stems)

    status, detail = orchestrator.run_separation(
        db_path,
        tmp_path,
        1,
        "/v1/audio?path=%2Fkaggle%2Fworking%2Fa.wav",
        base_url="https://example.ngrok-free.dev",
        api_key="secret",
    )

    assert status == "error"
    assert detail == "cuda out of memory"
    assert {"stems_status": "error", "stems_error_message": "cuda out of memory"} in updates


def test_run_generation_automatically_runs_separation_with_fresh_remote_file_ref(
    monkeypatch, tmp_path
):
    db_path = tmp_path / "songs.db"
    monkeypatch.setattr(orchestrator.song_db, "update_song", lambda *a, **k: None)
    monkeypatch.setattr(
        orchestrator.ace_step_client, "check_health", lambda base_url: {"status": "ok"}
    )
    monkeypatch.setattr(
        orchestrator.song_lyrics, "generate_lyrics", lambda prompt, language: "[en]\n[Verse]\nx"
    )
    monkeypatch.setattr(
        orchestrator.ace_step_client,
        "generate_music",
        lambda *a, **k: {"file": "/v1/audio?path=%2Ftmp%2Fa.wav"},
    )

    def fake_download_audio(base_url, api_key, file_path, dest_path):
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(b"x")
        return dest_path

    monkeypatch.setattr(orchestrator.ace_step_client, "download_audio", fake_download_audio)
    monkeypatch.setattr(
        orchestrator.song_mastering,
        "normalize_loudness",
        lambda input_path, output_path, target_lufs: Path(output_path).write_bytes(b"x"),
    )

    separation_calls = []
    monkeypatch.setattr(
        orchestrator,
        "run_separation",
        lambda db, out_dir, song_id, remote_file_ref, **k: separation_calls.append(
            (db, out_dir, song_id, remote_file_ref, k)
        )
        or ("done", None),
    )

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "done"
    assert len(separation_calls) == 1
    db, out_dir, song_id, remote_file_ref, kwargs = separation_calls[0]
    assert db == db_path
    assert out_dir == tmp_path
    assert song_id == 1
    assert remote_file_ref == "/v1/audio?path=%2Ftmp%2Fa.wav"
    assert kwargs["base_url"] == "https://example.ngrok-free.dev"
    assert kwargs["api_key"] == "secret"


def test_run_generation_still_returns_done_when_separation_fails(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    monkeypatch.setattr(orchestrator.song_db, "update_song", lambda *a, **k: None)
    monkeypatch.setattr(
        orchestrator.ace_step_client, "check_health", lambda base_url: {"status": "ok"}
    )
    monkeypatch.setattr(
        orchestrator.song_lyrics, "generate_lyrics", lambda prompt, language: "[en]\n[Verse]\nx"
    )
    monkeypatch.setattr(
        orchestrator.ace_step_client,
        "generate_music",
        lambda *a, **k: {"file": "/v1/audio?path=%2Ftmp%2Fa.wav"},
    )

    def fake_download_audio(base_url, api_key, file_path, dest_path):
        dest_path = Path(dest_path)
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(b"x")
        return dest_path

    monkeypatch.setattr(orchestrator.ace_step_client, "download_audio", fake_download_audio)
    monkeypatch.setattr(
        orchestrator.song_mastering,
        "normalize_loudness",
        lambda input_path, output_path, target_lufs: Path(output_path).write_bytes(b"x"),
    )
    monkeypatch.setattr(
        orchestrator, "run_separation", lambda *a, **k: ("error", "cuda out of memory")
    )

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "done"
    assert detail == str(tmp_path / "1_master.wav")
