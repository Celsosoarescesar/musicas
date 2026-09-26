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
    # Make tracks raise an exception
    project.tracks = property(lambda self: (_ for _ in ()).throw(RuntimeError("REAPER disconnected")))
    with pytest.raises(ReaperBridgeError, match="não foi possível listar"):
        list_tracks(project)


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
    # Make track.name assignment raise an exception
    def failing_name_setter(value):
        raise RuntimeError("REAPER disconnected")
    type(track).name = property(lambda self: self._name, failing_name_setter)
    track._name = "bateria"
    with pytest.raises(ReaperBridgeError, match="não foi possível renomear"):
        rename_track(project, "bateria", "drums")
