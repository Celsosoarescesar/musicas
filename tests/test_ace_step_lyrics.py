"""Unit tests for kagglelab.song_lyrics."""

from unittest.mock import MagicMock

import pytest

from ace_step import lyrics as song_lyrics


def test_generate_lyrics_returns_cli_stdout(monkeypatch):
    fake_result = MagicMock()
    fake_result.stdout = "[en]\n[Verse]\nDarkness falls upon the land\n[Chorus]\nRise up high\n"
    monkeypatch.setattr(song_lyrics.subprocess, "run", lambda *a, **k: fake_result)

    lyrics = song_lyrics.generate_lyrics("epic symphonic metal", language="en")

    assert lyrics.startswith("[en]")
    assert "[Verse]" in lyrics


def test_generate_lyrics_passes_style_prompt_and_language_via_stdin(monkeypatch):
    calls = {}

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        calls["kwargs"] = kwargs
        result = MagicMock()
        result.stdout = "[pt]\n[Verse]\nSombras caem\n"
        return result

    monkeypatch.setattr(song_lyrics.subprocess, "run", fake_run)

    song_lyrics.generate_lyrics("metal sinfonico sombrio", language="pt")

    assert calls["cmd"][0].lower().endswith(("claude", "claude.cmd"))
    assert calls["cmd"][1] == "-p"
    assert len(calls["cmd"]) == 2  # the prompt itself goes via stdin, not argv
    assert "metal sinfonico sombrio" in calls["kwargs"]["input"]
    assert "pt" in calls["kwargs"]["input"]


def test_generate_lyrics_strips_claude_session_env_vars(monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_SESSION_ID", "parent-session")
    monkeypatch.setenv("CLAUDECODE", "1")
    calls = {}

    def fake_run(cmd, **kwargs):
        calls["env"] = kwargs["env"]
        result = MagicMock()
        result.stdout = "[en]\n[Verse]\nx\n"
        return result

    monkeypatch.setattr(song_lyrics.subprocess, "run", fake_run)

    song_lyrics.generate_lyrics("epic metal")

    assert "CLAUDE_CODE_SESSION_ID" not in calls["env"]
    assert "CLAUDECODE" not in calls["env"]


def test_generate_lyrics_wraps_called_process_error(monkeypatch):
    def fake_run(cmd, **kwargs):
        exc = song_lyrics.subprocess.CalledProcessError(returncode=1, cmd=cmd)
        exc.stderr = "not authenticated"
        raise exc

    monkeypatch.setattr(song_lyrics.subprocess, "run", fake_run)

    with pytest.raises(song_lyrics.LyricsGenerationError, match="not authenticated"):
        song_lyrics.generate_lyrics("epic metal")


def test_generate_lyrics_rejects_output_without_section_tags(monkeypatch):
    fake_result = MagicMock()
    fake_result.stdout = "just some plain text with no tags"
    monkeypatch.setattr(song_lyrics.subprocess, "run", lambda *a, **k: fake_result)

    with pytest.raises(song_lyrics.LyricsGenerationError, match="marcadores"):
        song_lyrics.generate_lyrics("epic metal")


def test_generate_lyrics_rejects_confused_cli_response_mentioning_a_bracket(monkeypatch):
    # A real failure mode seen in practice: the CLI answers with a
    # clarifying question instead of lyrics, and that question happens to
    # mention "[Verse]" as an example -- a naive "has brackets somewhere"
    # check would wrongly accept this as valid lyrics.
    fake_result = MagicMock()
    fake_result.stdout = (
        "I don't see a full brief yet. Could you clarify the mood, and "
        "should I structure it with [Verse] and [Chorus] sections?"
    )
    monkeypatch.setattr(song_lyrics.subprocess, "run", lambda *a, **k: fake_result)

    with pytest.raises(song_lyrics.LyricsGenerationError, match="marcadores"):
        song_lyrics.generate_lyrics("epic metal")
