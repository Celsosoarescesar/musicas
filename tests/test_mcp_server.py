from unittest.mock import patch

from mcp_server import (
    reaper_add_fx,
    reaper_apply_master,
    reaper_generate_scale,
    reaper_import_audio,
    reaper_list_tracks,
    reaper_set_volume,
)
from reaper_bridge.errors import ReaperBridgeError


def test_reaper_list_tracks_returns_track_names():
    with patch("mcp_server.get_project", return_value=object()):
        with patch("mcp_server.project_ops.list_tracks", return_value=["bateria", "baixo"]):
            assert reaper_list_tracks() == "Faixas: bateria, baixo"


def test_reaper_list_tracks_returns_error_message_on_bridge_error():
    with patch("mcp_server.get_project", side_effect=ReaperBridgeError("REAPER fechado")):
        assert reaper_list_tracks() == "Erro: REAPER fechado"


def test_reaper_set_volume_calls_mixing_with_correct_arguments():
    fake_project = object()
    with patch("mcp_server.get_project", return_value=fake_project):
        with patch("mcp_server.mixing.set_volume") as mock_set_volume:
            result = reaper_set_volume("voz", 3.0)
    mock_set_volume.assert_called_once_with(fake_project, "voz", 3.0)
    assert "3.0" in result


def test_reaper_apply_master_lists_added_plugins():
    fake_fx = type("FakeFX", (), {"name": "ReaEQ (Cockos)"})()
    with patch("mcp_server.get_project", return_value=object()):
        with patch("mcp_server.mastering.apply_master_chain", return_value=[fake_fx]):
            assert "ReaEQ" in reaper_apply_master()


def test_reaper_generate_scale_returns_pitches_as_text():
    with patch("mcp_server.midi.generate_scale", return_value=[60, 62, 64]):
        assert "[60, 62, 64]" in reaper_generate_scale("C", "major")


def test_reaper_add_fx_reports_success():
    with patch("mcp_server.get_project", return_value=object()):
        with patch("mcp_server.mixing.add_fx"):
            assert "ReaEQ" in reaper_add_fx("voz", "ReaEQ (Cockos)")


def test_run_returns_unexpected_error_message_for_non_bridge_exception():
    with patch("mcp_server.get_project", side_effect=RuntimeError("boom")):
        assert reaper_list_tracks() == "Erro inesperado: boom"


def test_reaper_import_audio_wraps_track_name_read_failure():
    class BrokenTrack:
        @property
        def name(self):
            raise RuntimeError("REAPER disconnected")

    with patch("mcp_server.get_project", return_value=object()):
        with patch("mcp_server.project_ops.import_audio", return_value=BrokenTrack()):
            result = reaper_import_audio("C:/audio.wav")
    assert result.startswith("Erro: áudio importado")


def test_reaper_apply_master_wraps_fx_name_read_failure():
    class BrokenFX:
        @property
        def name(self):
            raise RuntimeError("REAPER disconnected")

    with patch("mcp_server.get_project", return_value=object()):
        with patch("mcp_server.mastering.apply_master_chain", return_value=[BrokenFX()]):
            result = reaper_apply_master()
    assert result.startswith("Erro: master aplicado")
