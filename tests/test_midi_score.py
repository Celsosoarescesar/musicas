import pytest
from music21 import chord, note
from music21 import stream as m21stream

from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.midi import write_score_to_tracks
from reaper_bridge.project import list_tracks
from tests.fakes import FakeProject


def test_write_score_to_tracks_creates_one_track_per_part():
    score = m21stream.Score()
    soprano = m21stream.Part()
    soprano.partName = "Soprano"
    soprano.append(note.Note("C5", quarterLength=1.0))
    bass = m21stream.Part()
    bass.partName = "Baixo"
    bass.append(note.Note("C3", quarterLength=1.0))
    score.append(soprano)
    score.append(bass)
    project = FakeProject([])

    write_score_to_tracks(project, score, track_prefix="Coral - ")

    assert list_tracks(project) == ["Coral - Soprano", "Coral - Baixo"]
    soprano_notes = project.tracks[0].items[0].active_take.notes
    assert [n.pitch for n in soprano_notes] == [72]
    bass_notes = project.tracks[1].items[0].active_take.notes
    assert [n.pitch for n in bass_notes] == [48]


def test_write_score_to_tracks_expands_chords_into_simultaneous_notes():
    part = m21stream.Part()
    part.partName = "Harmonia"
    part.append(chord.Chord(["C4", "E4", "G4"], quarterLength=2.0))
    score = m21stream.Score()
    score.append(part)
    project = FakeProject([])

    write_score_to_tracks(project, score)

    notes = project.tracks[0].items[0].active_take.notes
    assert sorted(n.pitch for n in notes) == [60, 64, 67]
    assert all(n.start == 0.0 for n in notes)


def test_write_score_to_tracks_falls_back_to_single_track_for_plain_stream():
    plain = m21stream.Stream()
    plain.append(note.Note("C4", quarterLength=1.0))
    project = FakeProject([])

    write_score_to_tracks(project, plain, track_prefix="Melodia - ")

    assert list_tracks(project) == ["Melodia - parte 1"]


def test_write_score_to_tracks_raises_for_empty_score():
    empty_score = m21stream.Score()
    project = FakeProject([])
    with pytest.raises(ReaperBridgeError, match="nenhuma nota"):
        write_score_to_tracks(project, empty_score)


def test_write_score_to_tracks_is_idempotent_on_rerun():
    score = m21stream.Score()
    part = m21stream.Part()
    part.partName = "Melodia"
    part.append(note.Note("C4", quarterLength=1.0))
    part.append(note.Note("D4", quarterLength=1.0))
    score.append(part)
    project = FakeProject([])

    write_score_to_tracks(project, score)
    write_score_to_tracks(project, score)

    track = project.tracks[0]
    assert len(track.items) == 1
    assert [n.pitch for n in track.items[0].active_take.notes] == [60, 62]


def test_write_score_to_tracks_dedupes_repeated_part_names():
    score = m21stream.Score()
    part1 = m21stream.Part()
    part1.partName = "Voz"
    part1.append(note.Note("C4", quarterLength=1.0))
    part2 = m21stream.Part()
    part2.partName = "Voz"
    part2.append(note.Note("G4", quarterLength=1.0))
    score.append(part1)
    score.append(part2)
    project = FakeProject([])

    write_score_to_tracks(project, score)

    assert list_tracks(project) == ["Voz", "Voz (2)"]
    assert [n.pitch for n in project.tracks[0].items[0].active_take.notes] == [60]
    assert [n.pitch for n in project.tracks[1].items[0].active_take.notes] == [67]
