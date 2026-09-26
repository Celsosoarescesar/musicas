"""SQLite database of generated songs — local orchestrator (Fase 2).

Uma tabela so (`songs`), sem tabela de log separada (YAGNI) -- o campo
`error_message` ja guarda a ultima falha. Uma conexao sqlite3 por
chamada; banco pequeno, uso pessoal, nao precisa de pool.
"""

import sqlite3
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS songs (
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
    remote_file_ref TEXT,
    stems_status TEXT,
    stems_error_message TEXT,
    stem_vocals_path TEXT,
    stem_drums_path TEXT,
    stem_bass_path TEXT,
    stem_guitar_path TEXT,
    stem_piano_path TEXT,
    stem_other_path TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

# Added after the table already existed in production (remote_file_ref
# onward) -- CREATE TABLE IF NOT EXISTS is a no-op against an existing
# table, so init_db also ALTERs in whichever of these a pre-existing
# database is still missing. Safe to re-run (checks PRAGMA table_info
# first) and safe on a brand-new database (already has them all from
# _SCHEMA, so the loop below finds nothing missing).
_MIGRATION_COLUMNS = {
    "remote_file_ref": "TEXT",
    "stems_status": "TEXT",
    "stems_error_message": "TEXT",
    "stem_vocals_path": "TEXT",
    "stem_drums_path": "TEXT",
    "stem_bass_path": "TEXT",
    "stem_guitar_path": "TEXT",
    "stem_piano_path": "TEXT",
    "stem_other_path": "TEXT",
}


def init_db(db_path: Path) -> None:
    """Create the songs table if it doesn't exist yet, and add any of
    _MIGRATION_COLUMNS a pre-existing database is still missing.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(_SCHEMA)
        existing_columns = {row[1] for row in conn.execute("PRAGMA table_info(songs)")}
        for name, sql_type in _MIGRATION_COLUMNS.items():
            if name not in existing_columns:
                conn.execute(f"ALTER TABLE songs ADD COLUMN {name} {sql_type}")
        conn.commit()
    finally:
        conn.close()


def create_song(
    db_path: Path,
    prompt: str,
    duration: float = 60.0,
    seed: int = 42,
    bpm: int | None = None,
    keyscale: str | None = None,
    vocal_language: str = "en",
) -> int:
    """Insert a new song with status 'draft'. Returns the new song's id."""
    init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute(
            """
            INSERT INTO songs (prompt, duration, seed, bpm, keyscale, vocal_language, status)
            VALUES (?, ?, ?, ?, ?, ?, 'draft')
            """,
            (prompt, duration, seed, bpm, keyscale, vocal_language),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


_UPDATABLE_COLUMNS = {
    "prompt", "lyrics", "duration", "seed", "bpm", "keyscale",
    "vocal_language", "status", "output_path", "error_message",
    "remote_file_ref", "stems_status", "stems_error_message",
    "stem_vocals_path", "stem_drums_path", "stem_bass_path",
    "stem_guitar_path", "stem_piano_path", "stem_other_path",
}


def update_song(db_path: Path, song_id: int, **fields) -> None:
    """Update known columns of a song by id. Always bumps updated_at.

    Raises ValueError if a field name isn't a real column -- this also
    closes the gap where **fields could otherwise be unpacked from a
    dict built outside a literal keyword call (Python does not enforce
    identifier syntax on **dict-unpacked kwargs).
    """
    if not fields:
        return
    unknown = set(fields) - _UPDATABLE_COLUMNS
    if unknown:
        raise ValueError(f"Campo(s) desconhecido(s) em update_song: {sorted(unknown)}")
    assignments = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values()) + [song_id]
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            f"UPDATE songs SET {assignments}, updated_at = datetime('now') WHERE id = ?",
            values,
        )
        conn.commit()
    finally:
        conn.close()


def get_song(db_path: Path, song_id: int) -> dict | None:
    """Return one song as a dict, or None if it doesn't exist."""
    init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM songs WHERE id = ?", (song_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def list_songs(db_path: Path, limit: int = 20) -> list[dict]:
    """Return the most recently created songs first."""
    init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT * FROM songs ORDER BY created_at DESC, id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()
