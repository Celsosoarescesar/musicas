import subprocess
from unittest.mock import patch

import pytest

from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.stems import find_python_command, get_source_path, split_stems
from tests.fakes import FakeItem, FakeProject, FakeSource, FakeTake, FakeTrack


def test_get_source_path_returns_take_source_filename():
    track = FakeTrack("bateria")
    item = FakeItem()
    item.active_take = FakeTake(is_midi=False, source=FakeSource(r"C:\musica.wav"))
    track.items.append(item)
    assert get_source_path(track) == r"C:\musica.wav"


def test_get_source_path_raises_when_track_has_no_items():
    track = FakeTrack("bateria")
    with pytest.raises(ReaperBridgeError, match="não tem nenhum item"):
        get_source_path(track)


def test_get_source_path_wraps_raw_exception_from_active_take():
    track = FakeTrack("bateria")
    item = FakeItem()

    class FailingTake:
        @property
        def source(self):
            raise RuntimeError("REAPER desconectado")

    item.active_take = FailingTake()
    track.items.append(item)
    with pytest.raises(ReaperBridgeError, match="não foi possível ler"):
        get_source_path(track)


def test_find_python_command_returns_first_working_candidate():
    def fake_run(args, **kwargs):
        if args[:1] == ["python"]:
            raise FileNotFoundError()
        return subprocess.CompletedProcess(args, returncode=0)

    with patch("reaper_bridge.stems.subprocess.run", side_effect=fake_run) as mock_run:
        result = find_python_command()

    assert result == "py -3"
    assert mock_run.call_count == 2


def test_find_python_command_skips_candidate_without_demucs():
    # Reproduz um bug real: dentro do venv do uv, "python" existe e RESPONDE
    # normalmente (returncode 0), mas e o Python do proprio projeto, sem
    # demucs instalado -- so um probe que verifica "import demucs" de verdade
    # pega essa diferenca; um probe que so confirma que o comando existe (tipo
    # --version) aceitaria "python" errado.
    def fake_run(args, **kwargs):
        if args[:1] == ["python"] and "demucs" in " ".join(args):
            return subprocess.CompletedProcess(args, returncode=1)
        return subprocess.CompletedProcess(args, returncode=0)

    with patch("reaper_bridge.stems.subprocess.run", side_effect=fake_run) as mock_run:
        result = find_python_command()

    assert result == "py -3"
    assert mock_run.call_count == 2


def test_find_python_command_raises_when_none_found():
    with patch(
        "reaper_bridge.stems.subprocess.run", side_effect=FileNotFoundError()
    ):
        with pytest.raises(ReaperBridgeError, match="nenhum comando Python"):
            find_python_command()


def _make_track_with_source(name, source_path):
    track = FakeTrack(name)
    item = FakeItem()
    item.active_take = FakeTake(is_midi=False, source=FakeSource(source_path))
    track.items.append(item)
    return track


def test_split_stems_imports_each_generated_stem_file(tmp_path):
    source_path = tmp_path / "musica.wav"
    source_path.write_bytes(b"fake-audio")
    project = FakeProject([_make_track_with_source("bateria", str(source_path))])

    stems_dir = tmp_path / "musica_stems" / "htdemucs_6s" / "musica"
    stems_dir.mkdir(parents=True)
    (stems_dir / "vocals.wav").write_bytes(b"v")
    (stems_dir / "drums.wav").write_bytes(b"d")

    with patch("reaper_bridge.stems.find_python_command", return_value="python"):
        with patch(
            "reaper_bridge.stems.subprocess.run",
            return_value=subprocess.CompletedProcess([], returncode=0, stdout="", stderr=""),
        ) as mock_run:
            with patch("reaper_bridge.stems.import_audio") as mock_import:
                result = split_stems(project, "bateria")

    assert mock_run.call_count == 1
    assert result == ["bateria_drums", "bateria_vocals"]
    assert mock_import.call_count == 2
    called_paths = {call.args[1] for call in mock_import.call_args_list}
    assert called_paths == {str(stems_dir / "drums.wav"), str(stems_dir / "vocals.wav")}


def test_split_stems_raises_when_demucs_exits_nonzero(tmp_path):
    source_path = tmp_path / "musica.wav"
    source_path.write_bytes(b"fake-audio")
    project = FakeProject([_make_track_with_source("bateria", str(source_path))])

    with patch("reaper_bridge.stems.find_python_command", return_value="python"):
        with patch(
            "reaper_bridge.stems.subprocess.run",
            return_value=subprocess.CompletedProcess(
                [], returncode=1, stdout="", stderr="ModuleNotFoundError: demucs"
            ),
        ):
            with pytest.raises(ReaperBridgeError, match="Demucs falhou"):
                split_stems(project, "bateria")


def test_split_stems_raises_when_demucs_exits_nonzero_with_stdout_only(tmp_path):
    # Reproduz um caso real: o Demucs as vezes escreve o traceback de erro no
    # stdout (nao no stderr) -- por exemplo quando o processo falha dentro de
    # um worker de multiprocessing. A mensagem de erro precisa incluir isso,
    # nao so o stderr.
    source_path = tmp_path / "musica.wav"
    source_path.write_bytes(b"fake-audio")
    project = FakeProject([_make_track_with_source("bateria", str(source_path))])

    with patch("reaper_bridge.stems.find_python_command", return_value="python"):
        with patch(
            "reaper_bridge.stems.subprocess.run",
            return_value=subprocess.CompletedProcess(
                [], returncode=1, stdout="OSError: Could not load this library", stderr=""
            ),
        ):
            with pytest.raises(ReaperBridgeError, match="Could not load this library"):
                split_stems(project, "bateria")


def test_split_stems_raises_on_timeout(tmp_path):
    source_path = tmp_path / "musica.wav"
    source_path.write_bytes(b"fake-audio")
    project = FakeProject([_make_track_with_source("bateria", str(source_path))])

    with patch("reaper_bridge.stems.find_python_command", return_value="python"):
        with patch(
            "reaper_bridge.stems.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="demucs", timeout=5),
        ):
            with pytest.raises(ReaperBridgeError, match="não terminou"):
                split_stems(project, "bateria", timeout_seconds=5)


def test_split_stems_raises_when_no_stem_files_found(tmp_path):
    source_path = tmp_path / "musica.wav"
    source_path.write_bytes(b"fake-audio")
    project = FakeProject([_make_track_with_source("bateria", str(source_path))])

    with patch("reaper_bridge.stems.find_python_command", return_value="python"):
        with patch(
            "reaper_bridge.stems.subprocess.run",
            return_value=subprocess.CompletedProcess([], returncode=0, stdout="", stderr=""),
        ):
            with pytest.raises(ReaperBridgeError, match="não foi encontrada"):
                split_stems(project, "bateria")


def test_split_stems_raises_when_source_file_missing(tmp_path):
    missing_path = str(tmp_path / "nao_existe.wav")
    project = FakeProject([_make_track_with_source("bateria", missing_path)])

    with pytest.raises(ReaperBridgeError, match="não encontrado"):
        split_stems(project, "bateria")
