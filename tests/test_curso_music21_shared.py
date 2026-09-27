from unittest.mock import patch

import pytest

from curso_music21._shared.reaper_track import lesson_track
from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.midi import write_notes_to_track
from tests.fakes import FakeProject, FakeTrack

TRACK_NAME = "Curso 01 - Notas e Alturas"


def test_lesson_track_creates_track_when_missing():
    project = FakeProject([])
    with patch(
        "curso_music21._shared.reaper_track.get_project", return_value=project
    ):
        returned_project, track = lesson_track(TRACK_NAME)

    assert returned_project is project
    assert track.name == TRACK_NAME
    assert track in project.tracks


def test_lesson_track_clears_items_on_second_run():
    track = FakeTrack(TRACK_NAME)
    project = FakeProject([track])
    write_notes_to_track(project, TRACK_NAME, [60, 62])
    assert len(track.items) == 1

    with patch(
        "curso_music21._shared.reaper_track.get_project", return_value=project
    ):
        lesson_track(TRACK_NAME)

    assert track.items == []


def test_lesson_track_propagates_reaper_bridge_error_when_reaper_unavailable():
    with patch(
        "curso_music21._shared.reaper_track.get_project",
        side_effect=ReaperBridgeError("REAPER não está aberto"),
    ):
        with pytest.raises(ReaperBridgeError, match="não está aberto"):
            lesson_track(TRACK_NAME)
