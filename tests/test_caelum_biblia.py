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

# Faixas cuja letra_en.md ainda e o modelo. Quando terminar a letra_en.md de
# uma faixa, remova o slug desta lista: ela passa a ser checada por load_faixa
# completo (test_written_tracks_load_completely).
UNWRITTEN = [
    "02_executor",
    "03_silencio",
    "04_a_mao_que_me_fez",
    "05_culpa",
    "06_revolta",
    "07_do_outro_lado",
    "08_monstros",
    "09_fora_do_sistema",
    "10_caelum",
]


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


def test_unwritten_is_subset_of_biblia():
    assert set(UNWRITTEN) <= {slug for slug, _, _ in BIBLIA}
    assert "01_quebra_de_fe" not in UNWRITTEN


@pytest.mark.parametrize(
    "slug,bpm,keyscale", [row for row in BIBLIA if row[0] not in UNWRITTEN]
)
def test_written_tracks_load_completely(slug, bpm, keyscale):
    faixa = load_faixa(CAELUM_ROOT / slug)
    assert faixa.bpm == bpm and faixa.keyscale == keyscale
    assert faixa.lyrics.startswith("[en]")


@pytest.mark.parametrize("slug", UNWRITTEN)
def test_unwritten_tracks_are_valid_except_template_lyrics(slug):
    # Prova que prompt/bpm/tipos do faixa.toml estao certos: a unica coisa que
    # falta e a letra em ingles (a recusa e a de letra de modelo).
    try:
        load_faixa(CAELUM_ROOT / slug)
    except FaixaError as exc:
        assert "modelo" in str(exc)
    else:
        pytest.fail(
            f"{slug}: letra_en.md ja foi escrita -- tire '{slug}' de UNWRITTEN "
            "em tests/test_caelum_biblia.py"
        )


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
    lines = text.splitlines()
    for slug, bpm, keyscale in BIBLIA:
        num = slug[:2]
        arc = [l for l in lines if f"| {num} | `{slug}`" in l]
        assert arc, f"{slug} nao aparece na tabela do arco"
        sound = [l for l in lines if l.startswith(f"| {num} | ")
                 and keyscale.replace(" minor", " menor") in l]
        assert sound, f"{num}: tom {keyscale} nao esta na tabela do plano sonoro"
        assert any(f"| {bpm} |" in l for l in sound), f"{num}: BPM {bpm} errado"
    assert "executor" in text.lower()
    assert "quem e o monstro" in text.lower()
    assert "Obey. Don't ask." in text and "Ask. Don't obey." in text
    assert "ReaAssist" in text
