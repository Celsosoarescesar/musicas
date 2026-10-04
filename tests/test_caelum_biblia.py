"""Trava as pastas do album contra a tabela da biblia e o conceito da vida real
(docs/superpowers/specs/2026-10-04-caelum-album-vida-real-design.md)."""

import tomllib

import pytest

from caelum.faixa import CAELUM_ROOT, FaixaError, load_faixa

# (slug, bpm, keyscale) -- fonte da verdade: tabela do plano/biblia.
BIBLIA = [
    ("01_sozinho", 100, "D minor"),
    ("02_rotina", 96, "A minor"),
    ("03_o_que_nao_veio", 112, "E minor"),
    ("04_barulho", 108, "B minor"),
    ("05_vazio", 92, "F# minor"),
    ("06_tempo_perdido", 120, "C# minor"),
    ("07_alguem_ai", 112, "F# minor"),
    ("08_recomeco", 98, "B minor"),
    ("09_tarde_demais", 104, "E minor"),
    ("10_caelum", 100, "D minor"),
]

# Faixas cuja letra_en.md ainda e o modelo. Quando terminar a letra_en.md de
# uma faixa, remova o slug desta lista: ela passa a ser checada por load_faixa
# completo (test_written_tracks_load_completely).
UNWRITTEN = [
    "05_vazio",
    "06_tempo_perdido",
    "07_alguem_ai",
    "08_recomeco",
    "09_tarde_demais",
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
    assert "01_sozinho" not in UNWRITTEN


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


def test_biblia_document_covers_every_track_and_the_real_life_concept():
    text = (CAELUM_ROOT / "conceito.md").read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    for slug, bpm, keyscale in BIBLIA:
        num = slug[:2]
        arc = [l for l in lines if f"| {num} | `{slug}`" in l]
        assert arc, f"{slug} nao aparece na tabela do arco"
        sound = [l for l in lines if l.startswith(f"| {num} | ")
                 and keyscale.replace(" minor", " menor") in l]
        assert sound, f"{num}: tom {keyscale} nao esta na tabela do plano sonoro"
        assert any(f"| {bpm} |" in l for l in sound), f"{num}: BPM {bpm} errado"
    lowered = text.lower()
    assert "vida real" in lowered
    assert "um sentimento" in lowered
    assert "guarda de abordagem" in lowered
    assert "2026-10-04-caelum-album-vida-real-design.md" in text
    assert "ReaAssist" in text


# Vocabulario da alegoria medieval, trocado por cenas reais na revisao de
# conceito (docs/superpowers/specs/2026-10-03-caelum-album-realismo-design.md).
# Cobre PT e EN (letra_en.md e o que o ACE-Step canta). "ordem"/"order" soltos
# sao palavras comuns e nao entram.
FORBIDDEN_TERMS = (
    "ordem grave", "execut", "alquimia", "lamina", "lâmina", "cacador", "caçador",
    "the order", "blade", "alchemy",
)

# Pastas cujas letras ainda sao do conceito antigo e serao refeitas com o
# usuario (uma sessao por faixa). Tire a pasta daqui quando a letra nova for
# aprovada e commitada (o teste de expiracao abaixo avisa).
PENDING_REWRITE = ("10_caelum",)


def _find_forbidden(text):
    """Termos proibidos em `text`, ignorando caixa e quebras de linha."""
    normalized = " ".join(text.lower().split())
    return [term for term in FORBIDDEN_TERMS if term in normalized]


def _album_text_files(include_pending=False):
    for path in sorted(CAELUM_ROOT.rglob("*")):
        if path.suffix not in (".md", ".toml") or not path.is_file():
            continue
        rel = path.relative_to(CAELUM_ROOT)
        if "saida" in rel.parts or "__pycache__" in rel.parts:
            continue
        if not include_pending and rel.parts[0] in PENDING_REWRITE:
            continue
        yield rel, path.read_text(encoding="utf-8-sig")


def test_no_allegorical_vocabulary_outside_pending_rewrites():
    offenders = [
        f"{rel}: '{term}'"
        for rel, text in _album_text_files()
        for term in _find_forbidden(text)
    ]
    assert not offenders, "vocabulario alegorico encontrado: " + "; ".join(offenders)


def test_find_forbidden_catches_terms_wrapped_across_lines():
    assert _find_forbidden("a Ordem\nGrave caiu") == ["ordem grave"]
    assert _find_forbidden("the\norder falls") == ["the order"]
    assert _find_forbidden("uma ordem e a order comum") == []


@pytest.mark.parametrize("slug", PENDING_REWRITE)
def test_pending_rewrite_exemption_is_still_needed(slug):
    found = [
        term
        for rel, text in _album_text_files(include_pending=True)
        if rel.parts[0] == slug
        for term in _find_forbidden(text)
    ]
    assert found, (
        f"{slug}: letra ja refeita -- tire '{slug}' de PENDING_REWRITE "
        "em tests/test_caelum_biblia.py"
    )


def test_scan_actually_covers_biblia_readme_and_tracks():
    scanned = {str(rel).replace("\\", "/") for rel, _ in _album_text_files()}
    assert "conceito.md" in scanned and "README.md" in scanned
    assert "03_o_que_nao_veio/letra_pt.md" in scanned and "09_tarde_demais/faixa.toml" in scanned
    assert not any(p.split("/")[0] in PENDING_REWRITE for p in scanned)
