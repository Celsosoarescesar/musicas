"""Shared song-generation pipeline, used by both the CLI
(scripts/criar_musica.py) and the FastAPI backend
(projects/music-studio/backend/).

Ver docs/superpowers/specs/2026-09-19-music-studio-web-design.md.
"""

from pathlib import Path

from ace_step import client as ace_step_client, mastering as song_mastering, song_db
from ace_step import lyrics as song_lyrics


def run_generation(
    db_path: Path,
    output_dir: Path,
    song_id: int,
    *,
    base_url: str,
    api_key: str,
    prompt: str,
    duration: float,
    seed: int,
    bpm: int | None,
    keyscale: str | None,
    vocal_language: str,
    lufs_target: float,
    lyrics: str | None = None,
    timeout: float = 300.0,
) -> tuple[str, str | None]:
    """Run the full generation pipeline for an already-created song row.

    Never raises -- every failure is recorded on the row via
    `song_db.update_song(..., status="error", error_message=...)` instead
    of propagating, so callers (CLI, background threads) don't need their
    own try/except. Returns `("done", output_path)` on success or
    `("error", error_message)` on failure.
    """
    try:
        ace_step_client.check_health(base_url)
    except ace_step_client.AceStepApiError as exc:
        error_message = str(exc)
        song_db.update_song(db_path, song_id, status="error", error_message=error_message)
        return "error", error_message

    try:
        resolved_lyrics = lyrics or song_lyrics.generate_lyrics(prompt, language=vocal_language)
        song_db.update_song(db_path, song_id, status="generating", lyrics=resolved_lyrics)

        result = ace_step_client.generate_music(
            base_url,
            api_key,
            prompt=prompt,
            lyrics=resolved_lyrics,
            duration=duration,
            seed=seed,
            bpm=bpm,
            keyscale=keyscale,
            vocal_language=vocal_language,
            timeout=timeout,
        )
        song_db.update_song(db_path, song_id, remote_file_ref=result["file"])

        raw_path = Path(output_dir) / f"{song_id}_raw.wav"
        ace_step_client.download_audio(base_url, api_key, result["file"], raw_path)

        final_path = Path(output_dir) / f"{song_id}_master.wav"
        song_mastering.normalize_loudness(raw_path, final_path, target_lufs=lufs_target)

        song_db.update_song(db_path, song_id, status="done", output_path=str(final_path))

        # Sempre separa os stems junto com a geracao, na mesma sessao do
        # Kaggle, enquanto remote_file_ref ainda existe de verdade (ver
        # docs/superpowers/specs/2026-09-19-demucs-kernel-proxy-design.md --
        # "Limitacao conhecida: o arquivo remoto e efemero"). Falha na
        # separacao nao derruba a geracao, que ja terminou com sucesso --
        # fica registrada a parte via stems_status/stems_error_message.
        run_separation(
            db_path, output_dir, song_id, result["file"], base_url=base_url, api_key=api_key
        )

        return "done", str(final_path)
    except Exception as exc:
        error_message = str(exc)
        song_db.update_song(db_path, song_id, status="error", error_message=error_message)
        return "error", error_message


def run_separation(
    db_path: Path,
    output_dir: Path,
    song_id: int,
    remote_file_ref: str,
    *,
    base_url: str,
    api_key: str,
    timeout: float = 300.0,
) -> tuple[str, str | None]:
    """Run stem separation for an already-generated song.

    `remote_file_ref` is the same opaque `/v1/audio?path=...` string
    `generate_music`'s result returns in `result["file"]` -- it's ephemeral
    (tied to the Kaggle session that generated it), so this must be called
    while that session is still the one running.

    Never raises -- every failure is recorded on the row via
    `song_db.update_song(..., stems_status="error", stems_error_message=...)`
    instead of propagating. Returns `("done", None)` on success or
    `("error", error_message)` on failure.
    """
    try:
        song_db.update_song(db_path, song_id, stems_status="separating")
        stems = ace_step_client.separate_stems(
            base_url, api_key, remote_file_ref, timeout=timeout
        )
        fields = {}
        for name, stem_path in stems.items():
            dest = Path(output_dir) / f"{song_id}_stem_{name}.wav"
            ace_step_client.download_audio(base_url, api_key, stem_path, dest)
            fields[f"stem_{name}_path"] = str(dest)
        song_db.update_song(db_path, song_id, stems_status="done", **fields)
        return "done", None
    except Exception as exc:
        error_message = str(exc)
        song_db.update_song(
            db_path, song_id, stems_status="error", stems_error_message=error_message
        )
        return "error", error_message
