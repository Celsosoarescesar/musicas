import pytest
from unittest.mock import patch

from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.project import create_track, find_track, list_tracks, rename_track, import_audio
from tests.fakes import FakeProject, FakeTrack


def test_list_tracks_returns_track_names():
    project = FakeProject([FakeTrack("bateria"), FakeTrack("baixo")])
    assert list_tracks(project) == ["bateria", "baixo"]


def test_find_track_returns_matching_track():
    drums = FakeTrack("bateria")
    project = FakeProject([drums, FakeTrack("baixo")])
    assert find_track(project, "bateria") is drums


def test_find_track_raises_with_available_names_when_missing():
    project = FakeProject([FakeTrack("bateria")])
    with pytest.raises(ReaperBridgeError, match="bateria"):
        find_track(project, "voz")


def test_find_track_raises_when_name_is_ambiguous():
    project = FakeProject([FakeTrack("voz"), FakeTrack("voz")])
    with pytest.raises(ReaperBridgeError, match="mais de uma"):
        find_track(project, "voz")


def test_create_track_appends_new_track():
    project = FakeProject([FakeTrack("bateria")])
    track = create_track(project, "baixo")
    assert track.name == "baixo"
    assert list_tracks(project) == ["bateria", "baixo"]


def test_rename_track_changes_name():
    project = FakeProject([FakeTrack("bateria")])
    rename_track(project, "bateria", "drums")
    assert list_tracks(project) == ["drums"]


def test_list_tracks_wraps_raw_exception():
    project = FakeProject([FakeTrack("bateria")])
    # Make tracks raise an exception when iterated
    class FailingTracks:
        def __iter__(self):
            raise RuntimeError("REAPER disconnected")

    original_tracks = project.tracks
    try:
        project.tracks = FailingTracks()
        with pytest.raises(ReaperBridgeError, match="não foi possível listar"):
            list_tracks(project)
    finally:
        project.tracks = original_tracks


def test_create_track_wraps_raw_exception():
    project = FakeProject([FakeTrack("bateria")])
    # Make add_track raise an exception
    def failing_add_track(*args, **kwargs):
        raise RuntimeError("REAPER disconnected")
    project.add_track = failing_add_track
    with pytest.raises(ReaperBridgeError, match="não foi possível criar"):
        create_track(project, "baixo")


def test_rename_track_wraps_raw_exception():
    project = FakeProject([FakeTrack("bateria")])
    track = project.tracks[0]
    original_name = track.name

    # Make track.name assignment raise an exception
    def failing_name_setter(self, value):
        raise RuntimeError("REAPER disconnected")

    # Store original class state and replace name with a property that raises on set
    original_name_attr = FakeTrack.__dict__.get("name")
    try:
        FakeTrack.name = property(lambda self: original_name, failing_name_setter)
        with pytest.raises(ReaperBridgeError, match="não foi possível renomear"):
            rename_track(project, "bateria", "drums")
    finally:
        # Restore the original class state
        if original_name_attr is None:
            if hasattr(FakeTrack, "name"):
                delattr(FakeTrack, "name")
        else:
            FakeTrack.name = original_name_attr


def test_import_audio_raises_when_file_missing():
    project = FakeProject([])
    with pytest.raises(ReaperBridgeError, match="não encontrado"):
        import_audio(project, "C:/nao/existe.wav")


def test_import_audio_raises_for_unsupported_extension(tmp_path):
    file_path = tmp_path / "musica.xyz"
    file_path.write_bytes(b"fake")
    project = FakeProject([])
    with pytest.raises(ReaperBridgeError, match="não suportada"):
        import_audio(project, str(file_path))


def test_import_audio_inserts_media_and_renames_new_track(tmp_path):
    file_path = tmp_path / "musica.wav"
    file_path.write_bytes(b"fake")
    project = FakeProject([FakeTrack("bateria")])

    def fake_insert_media(path, mode):
        project.tracks.append(FakeTrack("stem"))

    with patch(
        "reaper_bridge.project.reapy.reascript_api.InsertMedia",
        side_effect=fake_insert_media,
    ) as mock_insert:
        track = import_audio(project, str(file_path), track_name="voz")

    mock_insert.assert_called_once_with(str(file_path), 1)
    assert track.name == "voz"
    assert list_tracks(project) == ["bateria", "voz"]


def test_import_audio_wraps_raw_exception(tmp_path):
    file_path = tmp_path / "musica.wav"
    file_path.write_bytes(b"fake")
    project = FakeProject([FakeTrack("bateria")])

    def failing_insert_media(path, mode):
        raise RuntimeError("REAPER disconnected")

    with patch(
        "reaper_bridge.project.reapy.reascript_api.InsertMedia",
        side_effect=failing_insert_media,
    ):
        with pytest.raises(ReaperBridgeError, match="não foi possível importar"):
            import_audio(project, str(file_path))


def test_import_audio_wraps_cursor_position_exception(tmp_path):
    file_path = tmp_path / "musica.wav"
    file_path.write_bytes(b"fake")
    project = FakeProject([FakeTrack("bateria")])

    # Make cursor_position assignment raise an exception
    def failing_cursor_setter(self, value):
        raise RuntimeError("REAPER disconnected")

    # Replace the cursor_position property to fail on set
    original_cursor = type(project).__dict__.get("cursor_position")
    try:
        type(project).cursor_position = property(
            lambda self: 0.0, failing_cursor_setter
        )
        with pytest.raises(ReaperBridgeError, match="não foi possível importar"):
            import_audio(project, str(file_path))
    finally:
        # Restore original
        if original_cursor is None:
            if hasattr(type(project), "cursor_position"):
                delattr(type(project), "cursor_position")
        else:
            type(project).cursor_position = original_cursor


def test_import_audio_wraps_final_rename_exception(tmp_path):
    file_path = tmp_path / "musica.wav"
    file_path.write_bytes(b"fake")
    project = FakeProject([FakeTrack("bateria")])

    def fake_insert_media(path, mode):
        project.tracks.append(FakeTrack("stem"))

    # Make track.name assignment raise an exception
    def failing_name_setter(self, value):
        raise RuntimeError("REAPER disconnected")

    original_name_attr = FakeTrack.__dict__.get("name")
    try:
        FakeTrack.name = property(lambda self: "stem", failing_name_setter)
        with patch(
            "reaper_bridge.project.reapy.reascript_api.InsertMedia",
            side_effect=fake_insert_media,
        ):
            with pytest.raises(ReaperBridgeError, match="não foi possível importar"):
                import_audio(project, str(file_path), track_name="voz")
    finally:
        # Restore original
        if original_name_attr is None:
            if hasattr(FakeTrack, "name"):
                delattr(FakeTrack, "name")
        else:
            FakeTrack.name = original_name_attr
