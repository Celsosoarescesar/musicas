"""Leitura da configuracao de uma faixa do album (faixa.toml + letra_en.md).

Ver docs/superpowers/specs/2026-10-02-caelum-album-design.md.
"""

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
        data = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise FaixaError(f"faixa.toml invalido: {exc}") from exc

    unknown = set(data) - _ALLOWED_KEYS
    if unknown:
        raise FaixaError(f"chave(s) desconhecida(s) em faixa.toml: {sorted(unknown)}")

    prompt = data.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise FaixaError("faixa.toml precisa de 'prompt' (texto nao vazio)")

    lyrics = lyrics_path.read_text(encoding="utf-8").strip()
    if not lyrics:
        raise FaixaError(f"{lyrics_path.name} esta vazio")

    try:
        return Faixa(
            dir=faixa_dir,
            prompt=prompt.strip(),
            lyrics=lyrics,
            duration=float(data.get("duration", 180.0)),
            seed=int(data.get("seed", 42)),
            bpm=int(data["bpm"]) if "bpm" in data else None,
            keyscale=data.get("keyscale"),
            vocal_language=data.get("vocal_language", "en"),
            lufs_target=float(data.get("lufs_target", -9.0)),
        )
    except (TypeError, ValueError) as exc:
        raise FaixaError(f"valor invalido em faixa.toml: {exc}") from exc
