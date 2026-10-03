"""Separa os stems de uma musica ja gerada (Demucs htdemucs_6s, local).

A geracao do album e feita so com a musica (`caelum_gerar`); os stems so sao
separados depois que o usuario gostou dela, com `scripts/caelum_stems.py`.
"""

import shutil
import subprocess
from pathlib import Path

from ace_step import song_db
from reaper_bridge.stems import find_python_command

STEM_NAMES = ("vocals", "drums", "bass", "guitar", "piano", "other")
_MODEL = "htdemucs_6s"
_TIMEOUT = 3600.0  # na CPU a separacao leva varios minutos


class StemsError(RuntimeError):
    """Falha ao separar os stems de uma musica."""


def _stem_paths(saida: Path, song_id: int) -> dict[str, Path]:
    return {name: saida / f"{song_id}_stem_{name}.wav" for name in STEM_NAMES}


def separar_stems(
    faixa_dir: Path | str,
    song_id: int,
    *,
    runner=subprocess.run,
    find_python=find_python_command,
    timeout: float = _TIMEOUT,
) -> dict[str, Path]:
    """Roda o Demucs sobre `<faixa>/saida/<id>_master.wav` e grava
    `<id>_stem_<nome>.wav` ao lado dela. Se os stems ja existem, devolve-os sem
    rodar de novo. Levanta StemsError em qualquer falha (nao deixa lixo)."""
    saida = Path(faixa_dir) / "saida"
    master = saida / f"{song_id}_master.wav"
    if not master.is_file():
        raise StemsError(f"{master.name} nao encontrada em {saida}")

    destinos = _stem_paths(saida, song_id)
    if all(path.is_file() for path in destinos.values()):
        return destinos

    out_dir = saida / f".demucs_{song_id}"
    try:
        command = find_python().split() + [
            "-m", "demucs", "-n", _MODEL, "-o", str(out_dir), str(master)
        ]
        try:
            runner(command, check=True, capture_output=True, text=True, timeout=timeout)
        except subprocess.CalledProcessError as exc:
            detalhe = (exc.stderr or "").strip() or str(exc)
            raise StemsError(f"Demucs falhou: {detalhe}") from exc
        except subprocess.TimeoutExpired as exc:
            raise StemsError(f"Demucs nao terminou em {timeout:.0f}s") from exc

        origem = out_dir / _MODEL / master.stem
        faltando = [name for name in STEM_NAMES if not (origem / f"{name}.wav").is_file()]
        if faltando:
            raise StemsError(f"Demucs nao gerou os stems: {', '.join(faltando)}")
        for name, destino in destinos.items():
            shutil.copy(origem / f"{name}.wav", destino)
    except Exception:
        for destino in destinos.values():
            destino.unlink(missing_ok=True)
        raise
    finally:
        shutil.rmtree(out_dir, ignore_errors=True)

    db_path = saida / "songs.db"
    if db_path.is_file():
        song_db.update_song(
            db_path,
            song_id,
            stems_status="done",
            **{f"stem_{name}_path": str(path) for name, path in destinos.items()},
        )
    return destinos
