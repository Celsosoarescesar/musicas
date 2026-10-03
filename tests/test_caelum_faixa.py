import pytest

from caelum.faixa import CAELUM_ROOT, Faixa, FaixaError, load_faixa


def _make_faixa(tmp_path, toml="prompt = \"nu metal\"\n", lyrics="[en]\n[Verse]\nhello\n"):
    (tmp_path / "faixa.toml").write_text(toml, encoding="utf-8")
    if lyrics is not None:
        (tmp_path / "letra_en.md").write_text(lyrics, encoding="utf-8")
    return tmp_path


def test_load_faixa_applies_defaults(tmp_path):
    faixa = load_faixa(_make_faixa(tmp_path))
    assert isinstance(faixa, Faixa)
    assert faixa.dir == tmp_path
    assert faixa.prompt == "nu metal"
    assert faixa.lyrics == "[en]\n[Verse]\nhello"
    assert faixa.duration == 180.0
    assert faixa.seed == 42
    assert faixa.bpm is None
    assert faixa.keyscale is None
    assert faixa.vocal_language == "en"
    assert faixa.lufs_target == -9.0


def test_load_faixa_reads_all_fields(tmp_path):
    toml = (
        'prompt = "nu metal"\nduration = 200\nseed = 7\nbpm = 140\n'
        'keyscale = "D minor"\nvocal_language = "en"\nlufs_target = -8.5\n'
    )
    faixa = load_faixa(_make_faixa(tmp_path, toml=toml))
    assert (faixa.duration, faixa.seed, faixa.bpm) == (200.0, 7, 140)
    assert faixa.keyscale == "D minor"
    assert faixa.lufs_target == -8.5


def test_load_faixa_rejects_unknown_key(tmp_path):
    with pytest.raises(FaixaError, match="bpn"):
        load_faixa(_make_faixa(tmp_path, toml='prompt = "x"\nbpn = 140\n'))


@pytest.mark.parametrize("toml", ["", 'prompt = ""\n', 'prompt = "   "\n', "prompt = 3\n"])
def test_load_faixa_rejects_missing_or_blank_prompt(tmp_path, toml):
    with pytest.raises(FaixaError, match="prompt"):
        load_faixa(_make_faixa(tmp_path, toml=toml))


@pytest.mark.parametrize("lyrics", ["", "  \n\n"])
def test_load_faixa_rejects_blank_lyrics(tmp_path, lyrics):
    with pytest.raises(FaixaError, match="letra_en.md"):
        load_faixa(_make_faixa(tmp_path, lyrics=lyrics))


def test_load_faixa_rejects_missing_files(tmp_path):
    with pytest.raises(FaixaError, match="faixa.toml"):
        load_faixa(tmp_path)
    (tmp_path / "faixa.toml").write_text('prompt = "x"\n', encoding="utf-8")
    with pytest.raises(FaixaError, match="letra_en.md"):
        load_faixa(tmp_path)


def test_load_faixa_rejects_invalid_toml_and_bad_values(tmp_path):
    with pytest.raises(FaixaError, match="invalido"):
        load_faixa(_make_faixa(tmp_path, toml="prompt = = x"))
    with pytest.raises(FaixaError, match="invalido"):
        load_faixa(_make_faixa(tmp_path, toml='prompt = "x"\nbpm = "rapido"\n'))


def test_modelo_is_a_loadable_faixa():
    faixa = load_faixa(CAELUM_ROOT / "_modelo")
    assert faixa.vocal_language == "en"
    assert faixa.lyrics.startswith("[en]")
