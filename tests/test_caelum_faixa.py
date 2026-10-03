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


def test_modelo_letra_is_rejected_as_template():
    # O modelo existe para ser copiado; carregar sua letra como se fosse real
    # gastaria uma geracao do Kaggle com "(write the English lyrics here)".
    with pytest.raises(FaixaError, match="modelo"):
        load_faixa(CAELUM_ROOT / "_modelo")


@pytest.mark.parametrize(
    "lyrics",
    [
        "[en]\n[Verse]\nreal line\n(write the chorus here)\n[Bridge]\nmore real\n",
        "[en]\n[Verse]\n(Write The English lyrics here)\n",
        "[en]\r\n[Verse]\r\n(write the English lyrics here)\r\n",
    ],
)
def test_load_faixa_rejects_partially_template_lyrics(tmp_path, lyrics):
    with pytest.raises(FaixaError, match="modelo"):
        load_faixa(_make_faixa(tmp_path, lyrics=lyrics))


def test_load_faixa_rejects_template_lyrics_with_bom(tmp_path):
    faixa_dir = _make_faixa(tmp_path, lyrics=None)
    (faixa_dir / "letra_en.md").write_bytes(
        b"\xef\xbb\xbf[en]\n[Verse]\n(write the English lyrics here)\n"
    )
    with pytest.raises(FaixaError, match="modelo"):
        load_faixa(faixa_dir)


def test_load_faixa_accepts_real_adlib_starting_with_write(tmp_path):
    faixa = load_faixa(_make_faixa(tmp_path, lyrics="[en]\n[Verse]\n(Write my name in blood)\n"))
    assert "(Write my name in blood)" in faixa.lyrics


def test_load_faixa_accepts_lyrics_that_merely_mention_writing(tmp_path):
    faixa = load_faixa(_make_faixa(tmp_path, lyrics="[en]\n[Verse]\nI write my name in ash\n"))
    assert "write my name" in faixa.lyrics


# Fix Round 1: Type validation tests

@pytest.mark.parametrize("key,value", [
    ("seed", "true"),
    ("duration", "true"),
    ("bpm", "true"),
])
def test_load_faixa_rejects_boolean_as_numeric(tmp_path, key, value):
    """Booleans must not be coerced to numbers."""
    toml = f'prompt = "x"\n{key} = {value}\n'
    with pytest.raises(FaixaError, match="tipo"):
        load_faixa(_make_faixa(tmp_path, toml=toml))


@pytest.mark.parametrize("key,value,expected_match", [
    ("keyscale", "5", "tipo"),
    ("vocal_language", "5", "tipo"),
    ("vocal_language", '""', "vazio"),
    ("keyscale", '""', "vazio"),
])
def test_load_faixa_validates_string_fields(tmp_path, key, value, expected_match):
    """keyscale and vocal_language must be non-empty strings."""
    toml = f'prompt = "x"\n{key} = {value}\n'
    with pytest.raises(FaixaError, match=expected_match):
        load_faixa(_make_faixa(tmp_path, toml=toml))


@pytest.mark.parametrize("key,value", [
    ("bpm", '"140"'),
    ("seed", '"7"'),
    ("duration", '"200"'),
    ("lufs_target", '"8.5"'),
])
def test_load_faixa_rejects_quoted_numeric_strings(tmp_path, key, value):
    """Numeric fields must be TOML numbers, not strings."""
    toml = f'prompt = "x"\n{key} = {value}\n'
    with pytest.raises(FaixaError, match="tipo"):
        load_faixa(_make_faixa(tmp_path, toml=toml))


@pytest.mark.parametrize("key", ["bpm", "seed"])
def test_load_faixa_rejects_float_for_integer_fields(tmp_path, key):
    """bpm and seed must be integers, not floats."""
    toml = f'prompt = "x"\n{key} = 140.5\n'
    with pytest.raises(FaixaError, match="tipo"):
        load_faixa(_make_faixa(tmp_path, toml=toml))


@pytest.mark.parametrize("key,value", [
    ("bpm", "inf"),
    ("duration", "inf"),
    ("lufs_target", "inf"),
    ("duration", "nan"),
])
def test_load_faixa_rejects_infinite_and_nan(tmp_path, key, value):
    """Reject infinite and NaN values."""
    toml = f'prompt = "x"\n{key} = {value}\n'
    with pytest.raises(FaixaError, match="invalido"):
        load_faixa(_make_faixa(tmp_path, toml=toml))


@pytest.mark.parametrize("value", [0, -100, -1])
def test_load_faixa_rejects_non_positive_bpm(tmp_path, value):
    """bpm must be positive."""
    toml = f'prompt = "x"\nbpm = {value}\n'
    with pytest.raises(FaixaError, match="positivo"):
        load_faixa(_make_faixa(tmp_path, toml=toml))


@pytest.mark.parametrize("value", [0, -100, -1])
def test_load_faixa_rejects_non_positive_duration(tmp_path, value):
    """duration must be positive."""
    toml = f'prompt = "x"\nduration = {value}\n'
    with pytest.raises(FaixaError, match="positivo"):
        load_faixa(_make_faixa(tmp_path, toml=toml))


def test_load_faixa_handles_non_utf8_toml(tmp_path):
    """Non-UTF-8 faixa.toml should raise FaixaError, not UnicodeDecodeError."""
    (tmp_path / "faixa.toml").write_bytes(b'prompt = "x"\n' + b'\xff\xfe')
    (tmp_path / "letra_en.md").write_text("[en]\nhello", encoding="utf-8")
    with pytest.raises(FaixaError, match="encoding"):
        load_faixa(tmp_path)


def test_load_faixa_handles_non_utf8_lyrics(tmp_path):
    """Non-UTF-8 letra_en.md should raise FaixaError, not UnicodeDecodeError."""
    (tmp_path / "faixa.toml").write_text('prompt = "x"\n', encoding="utf-8")
    (tmp_path / "letra_en.md").write_bytes(b"[en]\n" + b'\xff\xfe')
    with pytest.raises(FaixaError, match="encoding"):
        load_faixa(tmp_path)


def test_load_faixa_handles_bom_in_lyrics(tmp_path):
    """UTF-8 BOM should be stripped from letra_en.md."""
    (tmp_path / "faixa.toml").write_text('prompt = "x"\n', encoding="utf-8")
    # Write with UTF-8 BOM
    (tmp_path / "letra_en.md").write_bytes(b'\xef\xbb\xbf[en]\n[Verse]\nhello')
    faixa = load_faixa(tmp_path)
    assert faixa.lyrics.startswith("[en]")
    assert not faixa.lyrics.startswith("﻿")


def test_load_faixa_handles_bom_in_toml(tmp_path):
    """UTF-8 BOM should be stripped from faixa.toml."""
    # Write with UTF-8 BOM
    (tmp_path / "faixa.toml").write_bytes(b'\xef\xbb\xbf' + b'prompt = "x"\n')
    (tmp_path / "letra_en.md").write_text("[en]\nhello", encoding="utf-8")
    faixa = load_faixa(tmp_path)
    assert faixa.prompt == "x"


def test_load_faixa_accepts_automatic_duration(tmp_path):
    faixa = load_faixa(_make_faixa(tmp_path, toml='prompt = "x"\nduration = "auto"\n'))
    assert faixa.duration is None


def test_load_faixa_rejects_other_duration_strings(tmp_path):
    with pytest.raises(FaixaError, match="duration"):
        load_faixa(_make_faixa(tmp_path, toml='prompt = "x"\nduration = "longa"\n'))
