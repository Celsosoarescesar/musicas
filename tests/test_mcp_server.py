from unittest.mock import patch

from mcp_server import (
    reaper_add_fx,
    reaper_apply_master,
    reaper_audit_session,
    reaper_generate_scale,
    reaper_import_audio,
    reaper_list_tracks,
    reaper_set_volume,
    reaper_split_stems,
    reaper_track_summary,
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


def test_reaper_split_stems_lists_created_tracks():
    with patch("mcp_server.get_project", return_value=object()):
        with patch(
            "mcp_server.stems.split_stems",
            return_value=["bateria_vocals", "bateria_drums"],
        ) as mock_split:
            result = reaper_split_stems("bateria")
    mock_split.assert_called_once()
    assert "bateria_vocals" in result
    assert "bateria_drums" in result


def test_reaper_split_stems_returns_error_message_on_bridge_error():
    with patch("mcp_server.get_project", return_value=object()):
        with patch(
            "mcp_server.stems.split_stems",
            side_effect=ReaperBridgeError("Demucs falhou"),
        ):
            assert reaper_split_stems("bateria") == "Erro: Demucs falhou"


def test_reaper_apply_master_wraps_fx_name_read_failure():
    class BrokenFX:
        @property
        def name(self):
            raise RuntimeError("REAPER disconnected")

    with patch("mcp_server.get_project", return_value=object()):
        with patch("mcp_server.mastering.apply_master_chain", return_value=[BrokenFX()]):
            result = reaper_apply_master()
    assert result.startswith("Erro: master aplicado")


def test_reaper_audit_session_reports_all_clean_when_nothing_found():
    with patch("mcp_server.get_project", return_value=object()):
        with patch("mcp_server.audit.find_armed_tracks", return_value=[]):
            with patch("mcp_server.audit.find_muted_tracks", return_value=[]):
                with patch("mcp_server.audit.find_empty_tracks", return_value=[]):
                    with patch("mcp_server.audit.find_bypassed_fx", return_value=[]):
                        with patch(
                            "mcp_server.audit.find_multi_destination_sends", return_value=[]
                        ):
                            result = reaper_audit_session()
    assert result.count("✓") == 5
    assert "⚠" not in result


def test_reaper_audit_session_reports_findings():
    with patch("mcp_server.get_project", return_value=object()):
        with patch("mcp_server.audit.find_armed_tracks", return_value=["voz"]):
            with patch("mcp_server.audit.find_muted_tracks", return_value=["baixo"]):
                with patch("mcp_server.audit.find_empty_tracks", return_value=[]):
                    with patch(
                        "mcp_server.audit.find_bypassed_fx",
                        return_value=[("piano", "ReaComp (Cockos)")],
                    ):
                        with patch(
                            "mcp_server.audit.find_multi_destination_sends", return_value=[]
                        ):
                            result = reaper_audit_session()
    assert "voz" in result
    assert "baixo" in result
    assert "ReaComp (Cockos)" in result
    # armed, muted, and bypassed-fx each contribute one ⚠; empty and
    # multi-dest-sends are clean, contributing one ✓ each.
    assert result.count("⚠") == 3
    assert result.count("✓") == 2


def test_reaper_audit_session_returns_error_message_on_bridge_error():
    with patch("mcp_server.get_project", side_effect=ReaperBridgeError("REAPER fechado")):
        assert reaper_audit_session() == "Erro: REAPER fechado"


def test_reaper_track_summary_formats_fields():
    summary = {
        "name": "piano",
        "color": (255, 0, 0),
        "depth": 0,
        "is_muted": True,
        "is_armed": False,
        "fx": [{"name": "ReaEQ (Cockos)", "enabled": True}],
        "sends": [{"dest": "bus_a", "volume": 0.8}],
    }
    with patch("mcp_server.get_project", return_value=object()):
        with patch("mcp_server.audit.summarize_track", return_value=summary):
            result = reaper_track_summary("piano")
    assert "piano" in result
    assert "ReaEQ (Cockos)" in result
    assert "bus_a" in result


def test_reaper_track_summary_shows_default_color_label_for_black():
    summary = {
        "name": "piano",
        "color": (0, 0, 0),
        "depth": 0,
        "is_muted": False,
        "is_armed": False,
        "fx": [],
        "sends": [],
    }
    with patch("mcp_server.get_project", return_value=object()):
        with patch("mcp_server.audit.summarize_track", return_value=summary):
            result = reaper_track_summary("piano")
    assert "padrão do tema" in result
    assert "(0, 0, 0)" not in result


def test_reaper_track_summary_shows_custom_color_as_tuple():
    summary = {
        "name": "piano",
        "color": (255, 0, 0),
        "depth": 0,
        "is_muted": False,
        "is_armed": False,
        "fx": [],
        "sends": [],
    }
    with patch("mcp_server.get_project", return_value=object()):
        with patch("mcp_server.audit.summarize_track", return_value=summary):
            result = reaper_track_summary("piano")
    assert "(255, 0, 0)" in result


def test_reaper_track_summary_returns_error_message_on_bridge_error():
    with patch("mcp_server.get_project", return_value=object()):
        with patch(
            "mcp_server.audit.summarize_track",
            side_effect=ReaperBridgeError("faixa 'xyz' não existe, faixas disponíveis: piano"),
        ):
            result = reaper_track_summary("xyz")
    assert result == "Erro: faixa 'xyz' não existe, faixas disponíveis: piano"
