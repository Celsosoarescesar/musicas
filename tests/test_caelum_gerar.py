from unittest.mock import patch

import pytest

from ace_step import song_db
from caelum.faixa import FaixaError
from caelum.gerar import gerar, resolve_faixa_dir


def _make_faixa(root, name="01_teste", seed=42):
    faixa_dir = root / name
    faixa_dir.mkdir()
    (faixa_dir / "faixa.toml").write_text(
        f'prompt = "nu metal"\nduration = 90\nseed = {seed}\nbpm = 130\n', encoding="utf-8"
    )
    (faixa_dir / "letra_en.md").write_text("[en]\n[Verse]\nhello\n", encoding="utf-8")
    return faixa_dir


def test_resolve_faixa_dir_finds_slug_under_root(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    assert resolve_faixa_dir("01_teste", root=tmp_path) == faixa_dir


def test_resolve_faixa_dir_accepts_literal_path(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    assert resolve_faixa_dir(str(faixa_dir), root=tmp_path / "outro") == faixa_dir


def test_resolve_faixa_dir_raises_when_missing(tmp_path):
    with pytest.raises(FaixaError, match="99_nada"):
        resolve_faixa_dir("99_nada", root=tmp_path)


def test_gerar_runs_pipeline_with_faixa_config_and_saves_in_saida(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    with patch(
        "caelum.gerar.orchestrator.run_generation", return_value=("done", "x.wav")
    ) as mock_run:
        song_id, status, detail = gerar(faixa_dir, timeout=99.0)

    assert (song_id, status, detail) == (1, "done", "x.wav")
    args, kwargs = mock_run.call_args
    assert args == (faixa_dir / "saida" / "songs.db", faixa_dir / "saida", 1)
    assert kwargs["prompt"] == "nu metal"
    assert kwargs["lyrics"] == "[en]\n[Verse]\nhello"
    assert kwargs["duration"] == 90.0
    assert kwargs["seed"] == 42
    assert kwargs["bpm"] == 130
    assert kwargs["vocal_language"] == "en"
    assert kwargs["lufs_target"] == -9.0
    assert kwargs["timeout"] == 99.0
    row = song_db.get_song(faixa_dir / "saida" / "songs.db", 1)
    assert row["seed"] == 42 and row["bpm"] == 130


def test_gerar_seed_override_is_used_and_recorded(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    with patch(
        "caelum.gerar.orchestrator.run_generation", return_value=("done", "x.wav")
    ) as mock_run:
        gerar(faixa_dir, seed=7)
    assert mock_run.call_args.kwargs["seed"] == 7
    assert song_db.get_song(faixa_dir / "saida" / "songs.db", 1)["seed"] == 7


def test_gerar_second_run_creates_new_song_id_in_same_db(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    with patch("caelum.gerar.orchestrator.run_generation", return_value=("done", "x.wav")):
        first_id, _, _ = gerar(faixa_dir)
        second_id, _, _ = gerar(faixa_dir, seed=8)
    assert (first_id, second_id) == (1, 2)


def test_gerar_returns_error_status_without_raising(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    with patch(
        "caelum.gerar.orchestrator.run_generation", return_value=("error", "kernel falhou")
    ):
        assert gerar(faixa_dir) == (1, "error", "kernel falhou")


def test_gerar_invalid_faixa_fails_before_touching_db_or_kaggle(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    (faixa_dir / "letra_en.md").write_text("   \n", encoding="utf-8")
    with patch("caelum.gerar.orchestrator.run_generation") as mock_run:
        with pytest.raises(FaixaError):
            gerar(faixa_dir)
    mock_run.assert_not_called()
    assert not (faixa_dir / "saida").exists()


def test_gerar_instrumental_sends_instrumental_tag_instead_of_lyrics(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    with patch(
        "caelum.gerar.orchestrator.run_generation", return_value=("done", "x.wav")
    ) as mock_run:
        gerar(faixa_dir, instrumental=True)

    assert mock_run.call_args.kwargs["lyrics"] == "[Instrumental]"


def test_gerar_template_lyrics_fail_before_touching_db_or_kaggle(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    (faixa_dir / "letra_en.md").write_text(
        "[en]\n[Verse]\n(write the English lyrics here)\n", encoding="utf-8"
    )
    with patch("caelum.gerar.orchestrator.run_generation") as mock_run:
        with pytest.raises(FaixaError, match="modelo"):
            gerar(faixa_dir)
    mock_run.assert_not_called()
    assert not (faixa_dir / "saida").exists()


def test_gerar_automatic_duration_passes_none_and_stores_zero(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    (faixa_dir / "faixa.toml").write_text(
        'prompt = "nu metal"\nduration = "auto"\nseed = 42\n', encoding="utf-8"
    )
    with patch(
        "caelum.gerar.orchestrator.run_generation", return_value=("done", "x.wav")
    ) as mock_run:
        gerar(faixa_dir)
    assert mock_run.call_args.kwargs["duration"] is None
    assert song_db.get_song(faixa_dir / "saida" / "songs.db", 1)["duration"] == 0.0


def test_gerar_defaults_to_music_only_and_com_stems_flag_enables_stems(tmp_path):
    faixa_dir = _make_faixa(tmp_path)
    with patch(
        "caelum.gerar.orchestrator.run_generation", return_value=("done", "x.wav")
    ) as mock_run:
        gerar(faixa_dir)
        assert mock_run.call_args.kwargs["stems"] is False
        gerar(faixa_dir, stems=True)
        assert mock_run.call_args.kwargs["stems"] is True
