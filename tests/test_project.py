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
