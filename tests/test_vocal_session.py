from unittest.mock import patch

import pytest

from reaper_bridge.errors import ReaperBridgeError
from reaper_bridge.vocal_session import build_vocal_session
from tests.fakes import FakeProject, FakeTrack


def _write_stems(tmp_path, song_id=3, names=("vocals", "drums", "bass", "guitar", "piano", "other")):
    for name in names:
        (tmp_path / f"{song_id}_stem_{name}.wav").write_bytes(b"RIFF")
    return str(tmp_path)


def _fake_import(project, file_path, track_name=None):
    return project.add_track(index=project.n_tracks, name=track_name)


def _build(project, stems_dir, song_id=3):
    with patch("reaper_bridge.vocal_session.import_audio", side_effect=_fake_import) as mock_import:
        created = build_vocal_session(project, stems_dir, song_id)
    return created, mock_import


def test_build_creates_stem_tracks_guide_and_armed_voice_track(tmp_path):
    project = FakeProject()
    created, mock_import = _build(project, _write_stems(tmp_path))

    assert created == ["drums", "bass", "guitar", "piano", "other", "guia_ia", "voz_caelum"]
    assert [t.name for t in project.tracks] == created
    guide = next(t for t in project.tracks if t.name == "guia_ia")
    assert guide.is_muted is True
    voice = next(t for t in project.tracks if t.name == "voz_caelum")
    assert voice.get_info_value("I_RECARM") == 1
    assert voice.is_muted is False
    imported_paths = [c.args[1] for c in mock_import.call_args_list]
    assert imported_paths[-1].endswith("3_stem_vocals.wav")


def test_stem_tracks_are_not_muted(tmp_path):
    project = FakeProject()
    _build(project, _write_stems(tmp_path))
    for name in ("drums", "bass", "guitar", "piano", "other"):
        assert next(t for t in project.tracks if t.name == name).is_muted is False


def test_build_without_vocals_stem_skips_guide_track(tmp_path):
    project = FakeProject()
    stems_dir = _write_stems(tmp_path, names=("drums", "bass", "guitar", "piano", "other"))
    created, _ = _build(project, stems_dir)
    assert "guia_ia" not in created
    assert created[-1] == "voz_caelum"


def test_build_raises_when_no_stem_files_found(tmp_path):
    project = FakeProject()
    with pytest.raises(ReaperBridgeError, match="nenhum stem"):
        _build(project, str(tmp_path))
    assert project.tracks == []


def test_build_ignores_stems_of_other_song_ids(tmp_path):
    project = FakeProject()
    stems_dir = _write_stems(tmp_path, song_id=1)
    with pytest.raises(ReaperBridgeError, match="nenhum stem"):
        _build(project, stems_dir, song_id=2)


@pytest.mark.parametrize("existing", ["voz_caelum", "guia_ia", "drums"])
def test_build_refuses_when_target_track_name_already_exists(tmp_path, existing):
    project = FakeProject([FakeTrack(existing)])
    with patch("reaper_bridge.vocal_session.import_audio", side_effect=_fake_import) as mock_import:
        with pytest.raises(ReaperBridgeError, match=existing):
            build_vocal_session(project, _write_stems(tmp_path), 3)
    mock_import.assert_not_called()
    assert [t.name for t in project.tracks] == [existing]


def test_build_twice_does_not_duplicate_tracks(tmp_path):
    project = FakeProject()
    stems_dir = _write_stems(tmp_path)
    _build(project, stems_dir)
    count_after_first = project.n_tracks
    with pytest.raises(ReaperBridgeError):
        _build(project, stems_dir)
    assert project.n_tracks == count_after_first


def test_build_raises_when_stems_dir_missing(tmp_path):
    with pytest.raises(ReaperBridgeError, match="pasta de stems"):
        _build(FakeProject(), str(tmp_path / "nao_existe"))


def test_build_wraps_arm_failure(tmp_path):
    class UnarmableProject(FakeProject):
        def add_track(self, index, name):
            track = super().add_track(index, name)
            if name == "voz_caelum":
                def boom(param, value):
                    raise RuntimeError("REAPER desconectado")
                track.set_info_value = boom
            return track

    project = UnarmableProject()
    with pytest.raises(ReaperBridgeError, match="armar"):
        _build(project, _write_stems(tmp_path))
