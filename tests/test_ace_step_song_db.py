"""Unit tests for kagglelab.song_db."""

import sqlite3

import pytest

from ace_step import song_db


def test_create_song_returns_id_with_draft_status(tmp_path):
    db_path = tmp_path / "songs.db"

    song_id = song_db.create_song(db_path, prompt="epic metal", duration=30.0, seed=7)

    song = song_db.get_song(db_path, song_id)
    assert song["status"] == "draft"
    assert song["prompt"] == "epic metal"
    assert song["duration"] == 30.0
    assert song["seed"] == 7


def test_update_song_changes_fields(tmp_path):
    db_path = tmp_path / "songs.db"
    song_id = song_db.create_song(db_path, prompt="epic metal")

    song_db.update_song(db_path, song_id, status="done", output_path="/tmp/out.wav")

    song = song_db.get_song(db_path, song_id)
    assert song["status"] == "done"
    assert song["output_path"] == "/tmp/out.wav"


def test_update_song_with_no_fields_is_a_noop(tmp_path):
    db_path = tmp_path / "songs.db"
    song_id = song_db.create_song(db_path, prompt="epic metal")

    song_db.update_song(db_path, song_id)  # must not raise

    song = song_db.get_song(db_path, song_id)
    assert song["status"] == "draft"


def test_update_song_rejects_unknown_field(tmp_path):
    db_path = tmp_path / "songs.db"
    song_id = song_db.create_song(db_path, prompt="epic metal")

    with pytest.raises(ValueError, match="malicious_field"):
        song_db.update_song(db_path, song_id, malicious_field="x")


def test_get_song_returns_none_for_missing_id(tmp_path):
    db_path = tmp_path / "songs.db"
    song_db.init_db(db_path)

    assert song_db.get_song(db_path, 999) is None


def test_list_songs_returns_most_recent_first(tmp_path):
    db_path = tmp_path / "songs.db"
    first_id = song_db.create_song(db_path, prompt="first")
    second_id = song_db.create_song(db_path, prompt="second")

    songs = song_db.list_songs(db_path)

    assert [s["id"] for s in songs] == [second_id, first_id]


def test_list_songs_respects_limit(tmp_path):
    db_path = tmp_path / "songs.db"
    for i in range(5):
        song_db.create_song(db_path, prompt=f"song {i}")

    songs = song_db.list_songs(db_path, limit=2)

    assert len(songs) == 2


def test_init_db_migrates_pre_existing_database_adding_new_columns(tmp_path):
    db_path = tmp_path / "songs.db"
    # Simulate a database created before the stem-separation columns
    # existed -- CREATE TABLE IF NOT EXISTS alone is a no-op against an
    # existing table, so init_db must add the missing columns explicitly.
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prompt TEXT NOT NULL,
            lyrics TEXT NOT NULL DEFAULT '',
            duration REAL NOT NULL DEFAULT 60.0,
            seed INTEGER NOT NULL DEFAULT 42,
            bpm INTEGER,
            keyscale TEXT,
            vocal_language TEXT NOT NULL DEFAULT 'en',
            status TEXT NOT NULL DEFAULT 'draft',
            output_path TEXT,
            error_message TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    conn.execute("INSERT INTO songs (prompt) VALUES ('old song')")
    conn.commit()
    conn.close()

    song_db.init_db(db_path)

    song = song_db.get_song(db_path, 1)
    assert song["prompt"] == "old song"
    assert song["remote_file_ref"] is None
    assert song["stems_status"] is None
    assert song["stem_vocals_path"] is None


def test_init_db_migration_is_idempotent(tmp_path):
    db_path = tmp_path / "songs.db"
    song_db.init_db(db_path)

    song_db.init_db(db_path)  # must not raise (e.g. "duplicate column")

    song_id = song_db.create_song(db_path, prompt="epic metal")
    assert song_db.get_song(db_path, song_id)["stems_status"] is None


def test_update_song_accepts_stem_separation_fields(tmp_path):
    db_path = tmp_path / "songs.db"
    song_id = song_db.create_song(db_path, prompt="epic metal")

    song_db.update_song(
        db_path,
        song_id,
        remote_file_ref="/v1/audio?path=%2Fkaggle%2Fworking%2Fa.wav",
        stems_status="done",
        stem_vocals_path="/tmp/1_stem_vocals.wav",
        stem_drums_path="/tmp/1_stem_drums.wav",
        stem_bass_path="/tmp/1_stem_bass.wav",
        stem_other_path="/tmp/1_stem_other.wav",
    )

    song = song_db.get_song(db_path, song_id)
    assert song["remote_file_ref"] == "/v1/audio?path=%2Fkaggle%2Fworking%2Fa.wav"
    assert song["stems_status"] == "done"
    assert song["stem_vocals_path"] == "/tmp/1_stem_vocals.wav"
    assert song["stem_drums_path"] == "/tmp/1_stem_drums.wav"
    assert song["stem_bass_path"] == "/tmp/1_stem_bass.wav"
    assert song["stem_other_path"] == "/tmp/1_stem_other.wav"


def test_update_song_accepts_guitar_and_piano_stem_fields(tmp_path):
    # htdemucs_6s (6 stems) instead of htdemucs (4 stems) -- daw_music_studio's
    # own kernel/proxy separates guitar and piano too.
    db_path = tmp_path / "songs.db"
    song_id = song_db.create_song(db_path, prompt="epic metal")

    song_db.update_song(
        db_path,
        song_id,
        stem_guitar_path="/tmp/1_stem_guitar.wav",
        stem_piano_path="/tmp/1_stem_piano.wav",
    )

    song = song_db.get_song(db_path, song_id)
    assert song["stem_guitar_path"] == "/tmp/1_stem_guitar.wav"
    assert song["stem_piano_path"] == "/tmp/1_stem_piano.wav"


def test_update_song_accepts_stems_error_message(tmp_path):
    db_path = tmp_path / "songs.db"
    song_id = song_db.create_song(db_path, prompt="epic metal")

    song_db.update_song(
        db_path, song_id, stems_status="error", stems_error_message="cuda out of memory"
    )

    song = song_db.get_song(db_path, song_id)
    assert song["stems_status"] == "error"
    assert song["stems_error_message"] == "cuda out of memory"
