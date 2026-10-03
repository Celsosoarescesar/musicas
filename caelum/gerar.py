"""Gera uma faixa do album: le a config da pasta, chama o pipeline do ace_step
(kernel batch: ACE-Step + Demucs) e grava tudo em <faixa>/saida/.

Nao reescreve a geracao; so a configura. Ver
docs/superpowers/specs/2026-10-02-caelum-album-design.md.
"""

from pathlib import Path

from ace_step import orchestrator, song_db

from .faixa import CAELUM_ROOT, FaixaError, load_faixa


def resolve_faixa_dir(arg: str, root: Path = CAELUM_ROOT) -> Path:
    """Aceita o slug de uma faixa (ex.: '01_semente', procurado em `root`)
    ou um caminho literal para a pasta da faixa."""
    named = Path(root) / arg
    if named.is_dir():
        return named
    literal = Path(arg)
    if literal.is_dir():
        return literal
    raise FaixaError(f"pasta da faixa '{arg}' nao encontrada (procurei em {root} e como caminho)")


INSTRUMENTAL_LYRICS = "[Instrumental]"


def gerar(
    faixa_dir: Path | str,
    *,
    seed: int | None = None,
    instrumental: bool = False,
    stems: bool = False,
    timeout: float = 2700.0,
) -> tuple[int, str, str | None]:
    """Roda a geracao+separacao de uma faixa. Devolve (song_id, status, detalhe).

    Valida a faixa ANTES de criar a musica no banco ou falar com o Kaggle
    (FaixaError sobe). Depois, o pipeline nunca levanta: erros voltam como
    status "error" e ficam gravados na linha da musica.

    `stems=False` (padrao) gera so a musica: os stems sao separados depois, com
    `scripts/caelum_stems.py`, se o usuario gostar dela. `stems=True` separa no kernel.

    `instrumental=True` (plano B da spec) gera a base sem vocal: manda a tag
    "[Instrumental]" no lugar da letra_en.md. Note que a letra faz parte da
    geracao -- a mesma seed com outra letra dá outra musica.
    """
    faixa = load_faixa(faixa_dir)
    used_seed = faixa.seed if seed is None else seed
    saida = faixa.dir / "saida"
    db_path = saida / "songs.db"

    song_id = song_db.create_song(
        db_path,
        prompt=faixa.prompt,
        duration=0.0 if faixa.duration is None else faixa.duration,  # 0.0 = automatica
        seed=used_seed,
        bpm=faixa.bpm,
        keyscale=faixa.keyscale,
        vocal_language=faixa.vocal_language,
    )
    status, detail = orchestrator.run_generation(
        db_path,
        saida,
        song_id,
        prompt=faixa.prompt,
        duration=faixa.duration,
        seed=used_seed,
        bpm=faixa.bpm,
        keyscale=faixa.keyscale,
        vocal_language=faixa.vocal_language,
        lufs_target=faixa.lufs_target,
        lyrics=INSTRUMENTAL_LYRICS if instrumental else faixa.lyrics,
        stems=stems,
        timeout=timeout,
    )
    return song_id, status, detail
