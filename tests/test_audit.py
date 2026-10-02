import pytest

from reaper_bridge.audit import find_armed_tracks, find_empty_tracks, find_muted_tracks
from reaper_bridge.errors import ReaperBridgeError
from tests.fakes import FakeProject, FakeTrack


def test_find_armed_tracks_returns_only_armed():
    voz = FakeTrack("voz")
    voz.set_info_value("I_RECARM", 1.0)
    baixo = FakeTrack("baixo")
    project = FakeProject([voz, baixo])
    assert find_armed_tracks(project) == ["voz"]


def test_find_armed_tracks_returns_empty_when_none_armed():
    project = FakeProject([FakeTrack("voz"), FakeTrack("baixo")])
    assert find_armed_tracks(project) == []


def test_find_armed_tracks_wraps_raw_exception():
    class ExplodingTracks:
        def __iter__(self):
            raise RuntimeError("REAPER disconnected")

    project = FakeProject([])
    project.tracks = ExplodingTracks()
    with pytest.raises(ReaperBridgeError, match="faixas armadas"):
        find_armed_tracks(project)


def test_find_muted_tracks_returns_only_muted():
    project = FakeProject([FakeTrack("voz", is_muted=True), FakeTrack("baixo")])
    assert find_muted_tracks(project) == ["voz"]


def test_find_muted_tracks_returns_empty_when_none_muted():
    project = FakeProject([FakeTrack("voz"), FakeTrack("baixo")])
    assert find_muted_tracks(project) == []


def test_find_empty_tracks_returns_only_tracks_without_items():
    with_item = FakeTrack("voz")
    with_item.add_midi_item()
    empty = FakeTrack("baixo")
    project = FakeProject([with_item, empty])
    assert find_empty_tracks(project) == ["baixo"]


def test_find_empty_tracks_returns_empty_when_all_have_items():
    track = FakeTrack("voz")
    track.add_midi_item()
    project = FakeProject([track])
    assert find_empty_tracks(project) == []
