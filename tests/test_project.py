import pytest

from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.project import create_track, find_track, list_tracks, rename_track
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
