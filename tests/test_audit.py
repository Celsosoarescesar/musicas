import pytest

from reaper_bridge.audit import (
    find_armed_tracks,
    find_bypassed_fx,
    find_empty_tracks,
    find_muted_tracks,
    find_multi_destination_sends,
    summarize_track,
)
from reaper_bridge.errors import ReaperBridgeError
from tests.fakes import FakeFX, FakeProject, FakeTrack


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


def test_find_bypassed_fx_returns_only_disabled_plugins():
    track = FakeTrack("piano")
    track.fxs.append(FakeFX("ReaEQ (Cockos)"))
    bypassed = FakeFX("ReaComp (Cockos)")
    bypassed.disable()
    track.fxs.append(bypassed)
    project = FakeProject([track])
    assert find_bypassed_fx(project) == [("piano", "ReaComp (Cockos)")]


def test_find_bypassed_fx_returns_empty_when_none_bypassed():
    track = FakeTrack("piano")
    track.fxs.append(FakeFX("ReaEQ (Cockos)"))
    project = FakeProject([track])
    assert find_bypassed_fx(project) == []


def test_find_multi_destination_sends_flags_more_than_one_send():
    source = FakeTrack("baixo")
    dest_a = FakeTrack("bus_a")
    dest_b = FakeTrack("bus_b")
    source.add_send(dest_a)
    source.add_send(dest_b)
    project = FakeProject([source, dest_a, dest_b])
    assert find_multi_destination_sends(project) == [("baixo", ["bus_a", "bus_b"])]


def test_find_multi_destination_sends_does_not_flag_exactly_one_send():
    source = FakeTrack("baixo")
    dest = FakeTrack("bus_a")
    source.add_send(dest)
    project = FakeProject([source, dest])
    assert find_multi_destination_sends(project) == []


def test_find_multi_destination_sends_returns_empty_when_no_sends():
    project = FakeProject([FakeTrack("baixo")])
    assert find_multi_destination_sends(project) == []


def test_summarize_track_returns_full_state():
    track = FakeTrack("piano", is_muted=True, color=(255, 0, 0), depth=1)
    track.set_info_value("I_RECARM", 1.0)
    enabled_fx = FakeFX("ReaEQ (Cockos)")
    bypassed_fx = FakeFX("ReaComp (Cockos)")
    bypassed_fx.disable()
    track.fxs.extend([enabled_fx, bypassed_fx])
    dest = FakeTrack("bus_a")
    track.add_send(dest, volume=0.8)
    project = FakeProject([track, dest])

    assert summarize_track(project, "piano") == {
        "name": "piano",
        "color": (255, 0, 0),
        "depth": 1,
        "is_muted": True,
        "is_armed": True,
        "fx": [
            {"name": "ReaEQ (Cockos)", "enabled": True},
            {"name": "ReaComp (Cockos)", "enabled": False},
        ],
        "sends": [{"dest": "bus_a", "volume": 0.8}],
    }


def test_summarize_track_raises_when_track_not_found():
    project = FakeProject([FakeTrack("piano")])
    with pytest.raises(ReaperBridgeError, match="não existe"):
        summarize_track(project, "baixo")
