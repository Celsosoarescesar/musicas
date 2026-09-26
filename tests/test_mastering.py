from unittest.mock import patch

import pytest

from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.mastering import (
    MASTER_CHAIN_PLUGINS,
    apply_master_chain,
    render_project,
)
from tests.fakes import FakeProject


def test_apply_master_chain_adds_all_plugins_to_master_track():
    project = FakeProject([])
    fxs = apply_master_chain(project)
    assert [fx.name for fx in fxs] == MASTER_CHAIN_PLUGINS
    assert [fx.name for fx in project.master_track.fxs] == MASTER_CHAIN_PLUGINS


def test_render_project_raises_when_directory_missing(tmp_path):
    project = FakeProject([])
    missing_dir = str(tmp_path / "nao_existe" / "musica.wav")
    with pytest.raises(ReaperBridgeError, match="pasta de destino"):
        render_project(project, missing_dir)


def test_render_project_raises_for_non_wav_output(tmp_path):
    project = FakeProject([])
    output_path = str(tmp_path / "musica.mp3")
    with pytest.raises(ReaperBridgeError, match=r"\.wav"):
        render_project(project, output_path)


def test_render_project_waits_for_file_then_returns_path(tmp_path):
    project = FakeProject([])
    output_path = tmp_path / "musica.wav"

    def fake_command(command_id, flag):
        output_path.write_bytes(b"fake-audio")

    with patch(
        "reaper_bridge.mastering.reapy.reascript_api.Main_OnCommand",
        side_effect=fake_command,
    ):
        result = render_project(project, str(output_path), timeout_seconds=5)

    assert result == str(output_path)
    assert project.get_info_string("RENDER_FILE") == str(tmp_path)


def test_render_project_raises_on_timeout(tmp_path):
    project = FakeProject([])
    output_path = str(tmp_path / "musica.wav")
    with patch("reaper_bridge.mastering.reapy.reascript_api.Main_OnCommand"):
        with patch("reaper_bridge.mastering.time.sleep"):
            with pytest.raises(ReaperBridgeError, match="não terminou"):
                render_project(project, output_path, timeout_seconds=0.01)


def test_render_project_wraps_unexpected_errors_from_reapy(tmp_path):
    project = FakeProject([])
    output_path = str(tmp_path / "musica.wav")
    with patch(
        "reaper_bridge.mastering.reapy.reascript_api.Main_OnCommand",
        side_effect=RuntimeError("boom"),
    ):
        with pytest.raises(ReaperBridgeError, match="boom"):
            render_project(project, output_path)
