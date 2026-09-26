import pytest

from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.midi import read_notes_from_track, write_notes_to_track
from tests.fakes import FakeItem, FakeProject, FakeTake, FakeTrack


def test_write_notes_to_track_creates_midi_item_with_notes():
    project = FakeProject([FakeTrack("piano")])
    item = write_notes_to_track(project, "piano", [60, 64, 67], note_length=0.25)
    assert [note.pitch for note in item.active_take.notes] == [60, 64, 67]
    assert item.active_take.notes[1].start == 0.25


def test_write_notes_to_track_raises_for_empty_pitches():
    project = FakeProject([FakeTrack("piano")])
    with pytest.raises(ReaperBridgeError, match="nenhuma nota"):
        write_notes_to_track(project, "piano", [])


def test_read_notes_from_track_returns_pitches_written():
    project = FakeProject([FakeTrack("piano")])
    write_notes_to_track(project, "piano", [60, 62, 64])
    assert read_notes_from_track(project, "piano") == [60, 62, 64]


def test_read_notes_from_track_ignores_non_midi_items():
    project = FakeProject([FakeTrack("audio")])
    track = project.tracks[0]
    non_midi_item = FakeItem()
    non_midi_item.active_take = FakeTake(is_midi=False)
    track.items.append(non_midi_item)
    assert read_notes_from_track(project, "audio") == []
