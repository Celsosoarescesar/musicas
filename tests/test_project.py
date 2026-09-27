import pytest
from unittest.mock import patch

from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.project import (
    clear_track_items,
    create_track,
    find_track,
    get_or_create_track,
    list_tracks,
    rename_track,
    import_audio,
)
from tests.fakes import FakeProject, FakeTrack


def test_fake_item_delete_removes_itself_from_track():
    from tests.fakes import FakeTrack

    track = FakeTrack("piano")
    item = track.add_midi_item(start=0.0, end=1.0)
    assert track.items == [item]

    item.delete()

    assert track.items == []


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


def test_import_audio_creates_selects_and_inserts_on_current_track(tmp_path):
    file_path = tmp_path / "musica.wav"
    file_path.write_bytes(b"fake")
    # Faixas pre-existentes simulam um projeto "sujo" -- o bug real (InsertMedia
    # nao criar a faixa nova necessariamente no final da lista) so aparecia com
    # varias faixas ja no projeto.
    project = FakeProject([FakeTrack("bateria"), FakeTrack("baixo")])

    with patch(
        "reaper_bridge.project.reapy.reascript_api.InsertMedia"
    ) as mock_insert:
        track = import_audio(project, str(file_path), track_name="voz")

    assert track.name == "voz"
    assert track is project.tracks[-1]
    assert track.is_selected is True
    mock_insert.assert_called_once_with(str(file_path), 0)
    assert list_tracks(project) == ["bateria", "baixo", "voz"]


def test_import_audio_uses_filename_as_default_track_name(tmp_path):
    file_path = tmp_path / "minha_musica.wav"
    file_path.write_bytes(b"fake")
    project = FakeProject([])

    with patch("reaper_bridge.project.reapy.reascript_api.InsertMedia"):
        track = import_audio(project, str(file_path))

    assert track.name == "minha_musica"


def test_import_audio_wraps_raw_exception(tmp_path):
    file_path = tmp_path / "musica.wav"
    file_path.write_bytes(b"fake")
    project = FakeProject([FakeTrack("bateria")])

    with patch(
        "reaper_bridge.project.reapy.reascript_api.InsertMedia",
        side_effect=RuntimeError("REAPER disconnected"),
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


def test_import_audio_wraps_add_track_exception(tmp_path):
    file_path = tmp_path / "musica.wav"
    file_path.write_bytes(b"fake")
    project = FakeProject([FakeTrack("bateria")])

    def failing_add_track(index, name):
        raise RuntimeError("REAPER disconnected")

    project.add_track = failing_add_track
    with pytest.raises(ReaperBridgeError, match="não foi possível importar"):
        import_audio(project, str(file_path))


def test_get_or_create_track_returns_existing_track():
    drums = FakeTrack("bateria")
    project = FakeProject([drums])
    assert get_or_create_track(project, "bateria") is drums


def test_get_or_create_track_creates_when_missing():
    project = FakeProject([])
    track = get_or_create_track(project, "baixo")
    assert track.name == "baixo"
    assert list_tracks(project) == ["baixo"]


def test_get_or_create_track_raises_when_ambiguous():
    project = FakeProject([FakeTrack("voz"), FakeTrack("voz")])
    with pytest.raises(ReaperBridgeError, match="mais de uma"):
        get_or_create_track(project, "voz")


def test_get_or_create_track_wraps_raw_exception():
    project = FakeProject([FakeTrack("bateria")])
    # Make tracks raise an exception when iterated
    class FailingTracks:
        def __iter__(self):
            raise RuntimeError("REAPER disconnected")

    original_tracks = project.tracks
    try:
        project.tracks = FailingTracks()
        with pytest.raises(ReaperBridgeError, match="não foi possível buscar"):
            get_or_create_track(project, "voz")
    finally:
        project.tracks = original_tracks


def test_clear_track_items_removes_all_items():
    project = FakeProject([FakeTrack("piano")])
    track = project.tracks[0]
    track.add_midi_item(start=0.0, end=1.0)
    track.add_midi_item(start=1.0, end=2.0)
    assert len(track.items) == 2

    clear_track_items(track)

    assert track.items == []


def test_clear_track_items_wraps_raw_exception():
    project = FakeProject([FakeTrack("piano")])
    track = project.tracks[0]

    class FailingItem:
        def delete(self):
            raise RuntimeError("REAPER disconnected")

    track.items.append(FailingItem())
    with pytest.raises(ReaperBridgeError, match="não foi possível limpar"):
        clear_track_items(track)
