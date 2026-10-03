"""Leitura da configuracao de uma faixa do album (faixa.toml + letra_en.md).

Ver docs/superpowers/specs/2026-10-02-caelum-album-design.md.
"""

import math
import tomllib
from dataclasses import dataclass
from pathlib import Path

CAELUM_ROOT = Path(__file__).resolve().parent

_ALLOWED_KEYS = {"prompt", "duration", "seed", "bpm", "keyscale", "vocal_language", "lufs_target"}


class FaixaError(ValueError):
    """Configuracao de faixa invalida ou incompleta."""


@dataclass(frozen=True)
class Faixa:
    dir: Path
    prompt: str
    lyrics: str
    duration: float
    seed: int
    bpm: int | None
    keyscale: str | None
    vocal_language: str
    lufs_target: float


def _validate_numeric_type(value, allow_float=False):
    """Validate that value is a number (not bool, not string), optionally float."""
    if isinstance(value, bool):
        raise TypeError(f"tipo invalido: esperado numero, obtido bool")
    if isinstance(value, str):
        raise TypeError(f"tipo invalido: esperado numero, obtido string")
    if not isinstance(value, (int, float)):
        raise TypeError(f"tipo invalido: esperado numero, obtido {type(value).__name__}")
    if not allow_float and isinstance(value, float) and not value.is_integer():
        raise TypeError(f"tipo invalido: esperado inteiro, obtido float")
    return value


def load_faixa(faixa_dir: Path | str) -> Faixa:
    """Le `faixa.toml` e `letra_en.md` de uma pasta de faixa.

    Falha cedo (FaixaError) em qualquer problema, para nao gastar uma geracao
    do Kaggle com configuracao quebrada: arquivos ausentes, TOML invalido,
    chave desconhecida, prompt vazio, letra vazia, valor de tipo errado.
    """
    faixa_dir = Path(faixa_dir)
    toml_path = faixa_dir / "faixa.toml"
    lyrics_path = faixa_dir / "letra_en.md"
    if not toml_path.is_file():
        raise FaixaError(f"faixa.toml nao encontrado em {faixa_dir}")
    if not lyrics_path.is_file():
        raise FaixaError(f"letra_en.md nao encontrado em {faixa_dir}")

    try:
        toml_text = toml_path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise FaixaError(f"faixa.toml encoding invalido: {exc}") from exc

    try:
        data = tomllib.loads(toml_text)
    except tomllib.TOMLDecodeError as exc:
        raise FaixaError(f"faixa.toml invalido: {exc}") from exc

    unknown = set(data) - _ALLOWED_KEYS
    if unknown:
        raise FaixaError(f"chave(s) desconhecida(s) em faixa.toml: {sorted(unknown)}")

    prompt = data.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise FaixaError("faixa.toml precisa de 'prompt' (texto nao vazio)")

    try:
        lyrics = lyrics_path.read_text(encoding="utf-8-sig").strip()
    except UnicodeDecodeError as exc:
        raise FaixaError(f"letra_en.md encoding invalido: {exc}") from exc

    if not lyrics:
        raise FaixaError(f"{lyrics_path.name} esta vazio")

    try:
        # Validate and convert duration
        if "duration" in data:
            duration = _validate_numeric_type(data["duration"], allow_float=True)
            duration = float(duration)
            if not math.isfinite(duration):
                raise ValueError("duration nao pode ser infinito ou NaN")
            if duration <= 0:
                raise ValueError("duration deve ser positivo")
        else:
            duration = 180.0

        # Validate and convert seed
        if "seed" in data:
            seed = _validate_numeric_type(data["seed"], allow_float=False)
            seed = int(seed)
        else:
            seed = 42

        # Validate and convert bpm
        if "bpm" in data:
            bpm = _validate_numeric_type(data["bpm"], allow_float=False)
            bpm = int(bpm)
            if bpm <= 0:
                raise ValueError("bpm deve ser positivo")
        else:
            bpm = None

        # Validate keyscale (optional, but if present must be non-empty string)
        if "keyscale" in data:
            keyscale = data["keyscale"]
            if not isinstance(keyscale, str):
                raise TypeError(f"keyscale: tipo invalido, esperado string")
            if not keyscale.strip():
                raise ValueError("keyscale esta vazio")
        else:
            keyscale = None

        # Validate vocal_language (optional, but if present must be non-empty string)
        if "vocal_language" in data:
            vocal_language = data["vocal_language"]
            if not isinstance(vocal_language, str):
                raise TypeError(f"vocal_language: tipo invalido, esperado string")
            if not vocal_language.strip():
                raise ValueError("vocal_language esta vazio")
        else:
            vocal_language = "en"

        # Validate and convert lufs_target
        if "lufs_target" in data:
            lufs_target = _validate_numeric_type(data["lufs_target"], allow_float=True)
            lufs_target = float(lufs_target)
            if not math.isfinite(lufs_target):
                raise ValueError("lufs_target nao pode ser infinito ou NaN")
        else:
            lufs_target = -9.0

        return Faixa(
            dir=faixa_dir,
            prompt=prompt.strip(),
            lyrics=lyrics,
            duration=duration,
            seed=seed,
            bpm=bpm,
            keyscale=keyscale.strip() if keyscale else None,
            vocal_language=vocal_language.strip(),
            lufs_target=lufs_target,
        )
    except (TypeError, ValueError, OverflowError) as exc:
        raise FaixaError(f"valor invalido em faixa.toml: {exc}") from exc
