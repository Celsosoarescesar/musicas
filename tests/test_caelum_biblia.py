"""Trava as pastas do album contra a tabela da biblia e o conceito da vida real
(docs/superpowers/specs/2026-10-04-caelum-album-vida-real-design.md) e do livro
de Caelum (docs/superpowers/specs/2026-10-05-caelum-album-livro-e-vida-design.md)."""

import re
import subprocess
import tomllib

import pytest

from caelum.faixa import CAELUM_ROOT, FaixaError, load_faixa
from caelum.gerar import resolve_faixa_dir

# (slug, bpm, keyscale) -- fonte da verdade: tabela do plano/biblia.
# V = a vida real do autor (nu metal).
V_FAIXAS = [
    ("01_sozinho", 100, "D minor"),
    ("02_rotina", 96, "A minor"),
    ("03_o_que_nao_veio", 112, "E minor"),
    ("04_barulho", 108, "B minor"),
    ("05_vazio", 92, "F# minor"),
    ("06_tempo_perdido", 120, "C# minor"),
    ("07_silencio", 88, "E minor"),
    ("08_recomeco", 98, "B minor"),
    ("09_tarde_demais", 104, "E minor"),
    ("10_caelum", 100, "D minor"),
    ("11_obedecer", 96, "A minor"),
]

# M = o livro de Caelum (nu metal sinfonico), ver caelum/livro.md. Os pares 3 e
# 7 diferem de V no tom/bpm de proposito (M03 E/88, M07 F#/112).
M_FAIXAS = [
    ("m01_quebra_de_fe", 100, "D minor"),
    ("m02_executor", 96, "A minor"),
    ("m03_silencio", 88, "E minor"),
    ("m04_a_mao_que_me_fez", 108, "B minor"),
    ("m05_culpa", 92, "F# minor"),
    ("m06_revolta", 120, "C# minor"),
    ("m07_do_outro_lado", 112, "F# minor"),
    ("m08_monstros", 98, "B minor"),
    ("m09_fora_do_sistema", 104, "E minor"),
    ("m10_caelum", 100, "D minor"),
]

BIBLIA = V_FAIXAS + M_FAIXAS

# Ordem do disco: cada V seguida da M que a espelha; a 11 (Obedecer) entra antes
# do Executor.
ORDEM_DO_DISCO = [
    "01_sozinho", "m01_quebra_de_fe",
    "02_rotina", "11_obedecer", "m02_executor",
    "03_o_que_nao_veio", "m03_silencio",
    "04_barulho", "m04_a_mao_que_me_fez",
    "05_vazio", "m05_culpa",
    "06_tempo_perdido", "m06_revolta",
    "07_silencio", "m07_do_outro_lado",
    "08_recomeco", "m08_monstros",
    "09_tarde_demais", "m09_fora_do_sistema",
    "10_caelum", "m10_caelum",
]

# Palavra da orquestra do ato que tem de aparecer no prompt de cada M.
M_ATO_KEYWORD = {
    "m01_quebra_de_fe": "pipe organ",
    "m02_executor": "pipe organ",
    "m03_silencio": "pipe organ",
    "m04_a_mao_que_me_fez": "tremolo strings",
    "m05_culpa": "tremolo strings",
    "m06_revolta": "tremolo strings",
    "m07_do_outro_lado": "tremolo strings",
    "m08_monstros": "soaring strings",
    "m09_fora_do_sistema": "soaring strings",
    "m10_caelum": "soaring strings",
}

# Faixas cuja letra_en.md ainda e o modelo. Quando terminar a letra_en.md de
# uma faixa, remova o slug desta lista: ela passa a ser checada por load_faixa
# completo (test_written_tracks_load_completely).
UNWRITTEN = [
    "m08_monstros",
    "m09_fora_do_sistema",
    "m10_caelum",
]


def _toml(slug):
    return tomllib.loads((CAELUM_ROOT / slug / "faixa.toml").read_text(encoding="utf-8-sig"))


def test_album_has_exactly_the_track_folders():
    folders = sorted(
        p.name for p in CAELUM_ROOT.iterdir()
        if p.is_dir() and re.match(r"m?\d\d_", p.name)
    )
    assert folders == sorted(slug for slug, _, _ in BIBLIA)


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


@pytest.mark.parametrize("slug,keyword", sorted(M_ATO_KEYWORD.items()))
def test_m_prompt_is_symphonic_with_the_act_orchestra(slug, keyword):
    prompt = _toml(slug)["prompt"]
    assert "symphonic nu metal" in prompt
    assert keyword in prompt
    assert "DJ scratches" not in prompt


@pytest.mark.parametrize("slug", [slug for slug, _, _ in V_FAIXAS])
def test_v_prompts_stay_without_orchestra(slug):
    assert "symphonic" not in _toml(slug)["prompt"]


@pytest.mark.parametrize("slug", [slug for slug, _, _ in M_FAIXAS])
def test_m_scene_context_names_the_monster_and_the_mirror(slug):
    text = (CAELUM_ROOT / slug / "letra_pt.md").read_text(encoding="utf-8-sig")
    assert "- Monstro quer dizer: " in text
    assert "- Espelho (V): " in text


def test_m_pairs_3_and_7_differ_from_v_on_purpose():
    by_slug = {slug: (bpm, key) for slug, bpm, key in BIBLIA}
    assert by_slug["03_o_que_nao_veio"] == (112, "E minor")
    assert by_slug["m03_silencio"] == (88, "E minor")
    assert by_slug["07_silencio"] == (88, "E minor")
    assert by_slug["m07_do_outro_lado"] == (112, "F# minor")


def test_disc_order_is_the_21_tracks_with_obedecer_before_the_executor():
    assert len(ORDEM_DO_DISCO) == 21
    assert sorted(ORDEM_DO_DISCO) == sorted(slug for slug, _, _ in BIBLIA)
    assert ORDEM_DO_DISCO[0] == "01_sozinho" and ORDEM_DO_DISCO[-1] == "m10_caelum"
    i = ORDEM_DO_DISCO.index("11_obedecer")
    assert ORDEM_DO_DISCO[i - 1] == "02_rotina"
    assert ORDEM_DO_DISCO[i + 1] == "m02_executor"


def test_m_folders_resolve_by_slug():
    assert resolve_faixa_dir("m01_quebra_de_fe") == CAELUM_ROOT / "m01_quebra_de_fe"


def test_m_saida_is_gitignored():
    result = subprocess.run(
        ["git", "check-ignore", "-q", "caelum/m01_quebra_de_fe/saida/1_master.wav"],
        cwd=CAELUM_ROOT.parent,
    )
    assert result.returncode == 0


def test_livro_lists_the_disc_order_and_the_story():
    text = (CAELUM_ROOT / "livro.md").read_text(encoding="utf-8-sig")
    positions = [text.find(f"`{slug}`") for slug in ORDEM_DO_DISCO]
    missing = [s for s, p in zip(ORDEM_DO_DISCO, positions) if p < 0]
    assert not missing, f"livro.md nao cita: {missing}"
    assert positions == sorted(positions), "livro.md: a tabela nao esta na ordem do disco"
    lowered = text.lower()
    for needle in (
        "assassin",
        "obey. don't ask.",
        "ask. don't obey.",
        "ordem grave",
        "2026-10-05-caelum-album-livro-e-vida-design.md",
    ):
        assert needle in lowered, f"livro.md nao menciona '{needle}'"


@pytest.mark.parametrize("name", ["conceito.md", "README.md"])
def test_conceito_and_readme_point_to_the_livro(name):
    assert "livro.md" in (CAELUM_ROOT / name).read_text(encoding="utf-8-sig")


def test_biblia_document_covers_every_track_and_the_real_life_concept():
    text = (CAELUM_ROOT / "conceito.md").read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    for slug, bpm, keyscale in V_FAIXAS:
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
PENDING_REWRITE = ("10_caelum", "11_obedecer")


def _find_forbidden(text):
    """Termos proibidos em `text`, ignorando caixa e quebras de linha."""
    normalized = " ".join(text.lower().split())
    return [term for term in FORBIDDEN_TERMS if term in normalized]


def _is_allegory_allowed(rel):
    """A alegoria medieval so e permitida no livro de Caelum (pastas mNN_* e livro.md)."""
    return rel.parts[0] == "livro.md" or re.match(r"m\d\d_", rel.parts[0]) is not None


def _album_text_files(include_pending=False):
    for path in sorted(CAELUM_ROOT.rglob("*")):
        if path.suffix not in (".md", ".toml") or not path.is_file():
            continue
        rel = path.relative_to(CAELUM_ROOT)
        if "saida" in rel.parts or "__pycache__" in rel.parts:
            continue
        if _is_allegory_allowed(rel):
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
    assert "livro.md" not in scanned
    assert not any(re.match(r"m\d\d_", p) for p in scanned)
