import subprocess
from pathlib import Path

import pytest

from ace_step import song_db
from caelum.stems import STEM_NAMES, StemsError, separar_stems


def _faixa_com_master(tmp_path, song_id=3):
    saida = tmp_path / "01_teste" / "saida"
    saida.mkdir(parents=True)
    (saida / f"{song_id}_master.wav").write_bytes(b"master")
    song_db.create_song(saida / "songs.db", prompt="x")
    return tmp_path / "01_teste"


def _fake_demucs(names=STEM_NAMES, calls=None):
    def runner(cmd, **kwargs):
        if calls is not None:
            calls.append(cmd)
        out_dir = Path(cmd[cmd.index("-o") + 1])
        track = Path(cmd[-1]).stem
        dest = out_dir / "htdemucs_6s" / track
        dest.mkdir(parents=True)
        for name in names:
            (dest / f"{name}.wav").write_bytes(f"stem-{name}".encode())
        return subprocess.CompletedProcess(cmd, 0)

    return runner


def test_separar_stems_copies_stems_next_to_master_and_cleans_up(tmp_path):
    faixa = _faixa_com_master(tmp_path)
    calls = []

    result = separar_stems(
        faixa, 3, runner=_fake_demucs(calls=calls), find_python=lambda: "python"
    )

    saida = faixa / "saida"
    assert set(result) == set(STEM_NAMES)
    for name in STEM_NAMES:
        assert (saida / f"3_stem_{name}.wav").read_bytes() == f"stem-{name}".encode()
    assert calls[0][:5] == ["python", "-m", "demucs", "-n", "htdemucs_6s"]
    assert calls[0][-1] == str(saida / "3_master.wav")
    assert not (saida / ".demucs_3").exists()
    assert (saida / "3_master.wav").read_bytes() == b"master"


def test_separar_stems_records_done_status_in_song_db(tmp_path):
    faixa = _faixa_com_master(tmp_path, song_id=1)
    separar_stems(faixa, 1, runner=_fake_demucs(), find_python=lambda: "python")
    row = song_db.get_song(faixa / "saida" / "songs.db", 1)
    assert row["stems_status"] == "done"
    assert row["stem_vocals_path"] == str(faixa / "saida" / "1_stem_vocals.wav")


def test_separar_stems_fails_clearly_when_master_is_missing(tmp_path):
    faixa = _faixa_com_master(tmp_path)
    with pytest.raises(StemsError, match="9_master.wav"):
        separar_stems(faixa, 9, runner=_fake_demucs(), find_python=lambda: "python")


def test_separar_stems_fails_when_demucs_output_is_incomplete(tmp_path):
    faixa = _faixa_com_master(tmp_path)
    runner = _fake_demucs(names=("vocals", "drums"))
    with pytest.raises(StemsError, match="bass"):
        separar_stems(faixa, 3, runner=runner, find_python=lambda: "python")
    assert not (faixa / "saida" / "3_stem_vocals.wav").exists()
    assert not (faixa / "saida" / ".demucs_3").exists()


def test_separar_stems_wraps_demucs_failure(tmp_path):
    faixa = _faixa_com_master(tmp_path)

    def runner(cmd, **kwargs):
        raise subprocess.CalledProcessError(1, cmd, stderr="boom")

    with pytest.raises(StemsError, match="boom"):
        separar_stems(faixa, 3, runner=runner, find_python=lambda: "python")
    assert not (faixa / "saida" / ".demucs_3").exists()


def test_separar_stems_keeps_existing_stems_without_rerunning(tmp_path):
    faixa = _faixa_com_master(tmp_path)
    saida = faixa / "saida"
    for name in STEM_NAMES:
        (saida / f"3_stem_{name}.wav").write_bytes(b"ja existe")
    calls = []
    result = separar_stems(
        faixa, 3, runner=_fake_demucs(calls=calls), find_python=lambda: "python"
    )
    assert calls == []
    assert set(result) == set(STEM_NAMES)
