"""Trava as pastas do album contra a tabela da biblia
(docs/superpowers/specs/2026-10-03-caelum-album-biblia-design.md)."""

import tomllib

import pytest

from caelum.faixa import CAELUM_ROOT, FaixaError, load_faixa

# (slug, bpm, keyscale) -- fonte da verdade: tabela do plano/biblia.
BIBLIA = [
    ("01_quebra_de_fe", 100, "D minor"),
    ("02_executor", 96, "A minor"),
    ("03_silencio", 88, "E minor"),
    ("04_a_mao_que_me_fez", 108, "B minor"),
    ("05_culpa", 92, "F# minor"),
    ("06_revolta", 120, "C# minor"),
    ("07_do_outro_lado", 112, "F# minor"),
    ("08_monstros", 98, "B minor"),
    ("09_fora_do_sistema", 104, "E minor"),
    ("10_caelum", 100, "D minor"),
]

# Faixas cuja letra_en.md ainda e o modelo. Ao terminar uma faixa, tire o slug
# daqui: ela passa a ser checada por load_faixa completo (ver o teste da 01).
UNWRITTEN = [slug for slug, _, _ in BIBLIA[1:]]


def _toml(slug):
    return tomllib.loads((CAELUM_ROOT / slug / "faixa.toml").read_text(encoding="utf-8-sig"))


def test_album_has_exactly_the_ten_track_folders():
    folders = sorted(p.name for p in CAELUM_ROOT.glob("[0-9][0-9]_*") if p.is_dir())
    assert folders == [slug for slug, _, _ in BIBLIA]


@pytest.mark.parametrize("slug,bpm,keyscale", BIBLIA)
def test_faixa_toml_matches_biblia(slug, bpm, keyscale):
    data = _toml(slug)
    assert data["bpm"] == bpm
    assert data["keyscale"] == keyscale
    assert f"{bpm} bpm" in data["prompt"]
    assert keyscale in data["prompt"]
    assert "no rap" in data["prompt"]
    assert data["seed"] == 42
    assert data["vocal_language"] == "en"
    assert data["lufs_target"] == -9.0


def test_pilot_track_loads_completely():
    faixa = load_faixa(CAELUM_ROOT / "01_quebra_de_fe")
    assert faixa.bpm == 100 and faixa.keyscale == "D minor"
    assert faixa.lyrics.startswith("[en]")


@pytest.mark.parametrize("slug", UNWRITTEN)
def test_unwritten_tracks_are_valid_except_template_lyrics(slug):
    # Prova que prompt/bpm/tipos do faixa.toml estao certos: a unica coisa que
    # falta e a letra em ingles (a recusa e a de letra de modelo).
    with pytest.raises(FaixaError, match="modelo"):
        load_faixa(CAELUM_ROOT / slug)


@pytest.mark.parametrize("slug", UNWRITTEN)
def test_unwritten_tracks_have_scene_context_in_letra_pt(slug):
    text = (CAELUM_ROOT / slug / "letra_pt.md").read_text(encoding="utf-8-sig")
    assert "Contexto da cena" in text
    assert "- ...\n" not in text.replace("\r\n", "\n").split("## Letra")[0]
    assert "[Verso 1]" in text and "[Ponte" in text


def test_unwritten_tracks_keep_the_template_files():
    for slug in UNWRITTEN:
        for name in ("letra_en.md", "pronuncia.md"):
            assert (CAELUM_ROOT / slug / name).is_file(), f"{slug}/{name} ausente"


def test_biblia_document_covers_every_track_and_the_two_axes():
    text = (CAELUM_ROOT / "BIBLIA.md").read_text(encoding="utf-8-sig")
    for slug, bpm, keyscale in BIBLIA:
        assert slug in text, f"{slug} nao aparece na biblia"
        assert f"{bpm}" in text and keyscale.replace(" minor", " menor") in text
    assert "executor" in text.lower()
    assert "quem e o monstro" in text.lower()
    assert "Obey. Don't ask." in text and "Ask. Don't obey." in text
    assert "ReaAssist" in text
