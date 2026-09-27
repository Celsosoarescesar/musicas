"""Shared song-generation pipeline, used by scripts/criar_musica.py.

One Kaggle kernel run does generation + Demucs stem separation for a
single song end-to-end (no live server, no tunnel) -- see
docs/superpowers/specs/2026-09-26-ace-step-batch-kernel-design.md.
"""

import json
import shutil
import time
from pathlib import Path

from ace_step import kernel_render, kernels, mastering as song_mastering, song_db
from ace_step import lyrics as song_lyrics
from ace_step.kaggle_client import KaggleResourceError

_KERNEL_REF = "celsosoarescesar/ace-step-api"
_STEM_NAMES = ("vocals", "drums", "bass", "guitar", "piano", "other")
_MAX_CONSECUTIVE_STATUS_POLL_FAILURES = 3


def _wait_for_kernel_terminal(ref: str, *, timeout: float, poll_interval: float) -> dict:
    """Poll get_kernel_status(ref) until it reaches a terminal status.

    Tolerates up to _MAX_CONSECUTIVE_STATUS_POLL_FAILURES consecutive
    KaggleResourceErrors (transient API hiccups) before giving up -- a
    single failed poll shouldn't abort a kernel that's still running fine.

    A "complete" status is not trusted until a non-terminal status has
    confirmed this run actually started: the kernel slug is reused for
    every run and Kaggle's kernel-status API takes no version/run
    identifier, so a "complete" seen on the very first poll right after
    push could be a stale leftover from the *previous* run rather than
    this one -- trusting it would silently pull and master the wrong
    song's audio. "error"/"cancel_acknowledged" don't carry that same
    silent-wrong-data risk (worst case is a false failure), so they're
    still trusted immediately.

    Raises TimeoutError if no terminal status is reached within `timeout`
    seconds, or re-raises KaggleResourceError if polling keeps failing.
    """
    deadline = time.monotonic() + timeout
    consecutive_failures = 0
    seen_non_terminal = False
    while True:
        try:
            result = kernels.get_kernel_status(ref)
        except KaggleResourceError:
            consecutive_failures += 1
            if consecutive_failures > _MAX_CONSECUTIVE_STATUS_POLL_FAILURES:
                raise
            time.sleep(poll_interval)
            continue
        consecutive_failures = 0
        status = result["status"]
        if kernels.is_terminal_kernel_status(status):
            if status != "complete" or seen_non_terminal:
                return result
        else:
            seen_non_terminal = True
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Timeout de {timeout}s esperando o kernel {ref} terminar -- ele "
                "pode continuar rodando no Kaggle; consulte "
                f"'uv run python scripts/kernel_status.py {ref}' mais tarde"
            )
        time.sleep(poll_interval)


def run_generation(
    db_path: Path,
    output_dir: Path,
    song_id: int,
    *,
    prompt: str,
    duration: float,
    seed: int,
    bpm: int | None,
    keyscale: str | None,
    vocal_language: str,
    lufs_target: float,
    lyrics: str | None = None,
    timeout: float = 2700.0,
    poll_interval: float = 20.0,
) -> tuple[str, str | None]:
    """Run the full generation+separation pipeline for an already-created song row.

    Renders and pushes a batch Kaggle kernel that does generation and
    Demucs separation in one run, waits for it to finish, and pulls its
    output. Never raises -- every failure is recorded on the row via
    `song_db.update_song(..., status="error", error_message=...)` instead
    of propagating. Returns `("done", output_path)` on success or
    `("error", error_message)` on failure.
    """
    output_dir = Path(output_dir)
    tmp_kernel_dir = output_dir / f".kernel_{song_id}"
    tmp_pulled_dir = output_dir / f".pulled_{song_id}"
    try:
        resolved_lyrics = lyrics or song_lyrics.generate_lyrics(prompt, language=vocal_language)
        song_db.update_song(db_path, song_id, status="generating", lyrics=resolved_lyrics)

        job = {
            "prompt": prompt,
            "lyrics": resolved_lyrics,
            "duration": duration,
            "seed": seed,
            "bpm": bpm,
            "keyscale": keyscale,
            "vocal_language": vocal_language,
        }
        kernel_render.render_job_kernel(job, tmp_kernel_dir)
        kernels.push_kernel(tmp_kernel_dir)

        kernel_result = _wait_for_kernel_terminal(
            _KERNEL_REF, timeout=timeout, poll_interval=poll_interval
        )
        if kernel_result["status"] != "complete":
            detail = kernel_result.get("failure_message") or ""
            kernel_detail = None
            try:
                kernels.pull_kernel_output(_KERNEL_REF, tmp_pulled_dir)
                pulled_result = json.loads(
                    (tmp_pulled_dir / "output" / "result.json").read_text(encoding="utf-8")
                )
                kernel_detail = pulled_result.get("generation_error") or pulled_result.get(
                    "stems_error"
                )
            except Exception:
                pass
            if kernel_detail:
                detail = f"{detail} -- {kernel_detail}" if detail else kernel_detail
            raise RuntimeError(
                f"Kernel {_KERNEL_REF} terminou com status "
                f"{kernel_result['status']!r}: {detail or 'sem detalhes'}"
            )
        kernels.pull_kernel_output(_KERNEL_REF, tmp_pulled_dir)

        result_path = tmp_pulled_dir / "output" / "result.json"
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"O kernel nao produziu um result.json valido em {result_path} -- "
                f"ele pode ter falhado antes de terminar a geracao: {exc}"
            ) from exc

        if result.get("generation_status") != "done":
            raise RuntimeError(
                result.get("generation_error") or "geracao falhou no kernel, sem detalhes"
            )

        raw_path = tmp_pulled_dir / "output" / "raw.wav"
        if not raw_path.is_file() or raw_path.stat().st_size == 0:
            raise RuntimeError(
                f"result.json reportou geracao concluida mas {raw_path} nao existe ou esta vazio"
            )

        final_path = output_dir / f"{song_id}_master.wav"
        song_mastering.normalize_loudness(raw_path, final_path, target_lufs=lufs_target)
        song_db.update_song(db_path, song_id, status="done", output_path=str(final_path))

        try:
            if result.get("stems_status") == "done":
                fields = {}
                for name in _STEM_NAMES:
                    stem_src = tmp_pulled_dir / "output" / "stems" / f"{name}.wav"
                    stem_dest = output_dir / f"{song_id}_stem_{name}.wav"
                    shutil.copy(stem_src, stem_dest)
                    fields[f"stem_{name}_path"] = str(stem_dest)
                song_db.update_song(db_path, song_id, stems_status="done", **fields)
            else:
                song_db.update_song(
                    db_path,
                    song_id,
                    stems_status="error",
                    stems_error_message=(
                        result.get("stems_error") or "separacao falhou no kernel, sem detalhes"
                    ),
                )
        except Exception as exc:
            song_db.update_song(
                db_path, song_id, stems_status="error", stems_error_message=str(exc)
            )

        return "done", str(final_path)
    except Exception as exc:
        error_message = str(exc)
        song_db.update_song(db_path, song_id, status="error", error_message=error_message)
        return "error", error_message
    finally:
        shutil.rmtree(tmp_kernel_dir, ignore_errors=True)
        shutil.rmtree(tmp_pulled_dir, ignore_errors=True)
