"""Lyrics generation via the Claude Code CLI (headless), no Anthropic API key.

Chama `claude -p "<prompt>"` autenticado com CLAUDE_CODE_OAUTH_TOKEN
(ja presente no .env, lido via python-dotenv) -- nao usa o pacote
`anthropic` nem uma API key tradicional. Ver
docs/superpowers/specs/2026-09-13-ace-step-orchestrator-design.md.
"""

import os
import re
import shutil
import subprocess

from dotenv import load_dotenv

_SECTION_MARKERS = ("[Verse]", "[Chorus]", "[Bridge]", "[Outro]", "[Intro]")
# A bare "[" and "]" anywhere in the text isn't enough evidence of real
# structured lyrics -- a confused CLI response (e.g. asking a clarifying
# question that happens to mention "[Verse]" as an example) can satisfy
# that. Require the language tag on line 1 AND at least one real section
# marker.
_LANGUAGE_TAG = re.compile(r"^\[[a-z]{2}(-[A-Za-z]{2})?\]")


class LyricsGenerationError(Exception):
    """Raised when lyrics generation fails or returns unusable output."""


def _clean_subprocess_env() -> dict:
    """Environment for the child `claude` CLI, stripped of this process's
    own Claude Code session variables.

    When `generate_lyrics` runs from inside a Claude Code session (e.g.
    this script invoked via `uv run` from a Claude Code Bash tool call),
    CLAUDE_CODE_SESSION_ID / CLAUDECODE / CLAUDE_CODE_MESSAGING_SOCKET
    etc. are already in os.environ and get inherited by the child
    `claude -p` process. That makes the child attach to the *parent*
    session's context instead of starting a clean one-shot headless
    call, so it answers as if continuing that conversation instead of
    writing lyrics. Filtering them out gives a truly independent call.
    """
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("CLAUDE_") and key != "CLAUDECODE"
    }


_INSTRUCTIONS = """You are a professional music lyricist and songwriter.
Output ONLY the lyrics with section markers, no explanations or meta-text.
Use these section markers: [Verse], [Chorus], [Bridge], [Outro], [Intro].
Each section should have 2-4 lines typically.
Keep lines short and singable (8-15 words per line).
The language tag [language_code] must be the very first line (e.g. [en], [pt])."""


def generate_lyrics(style_prompt: str, language: str = "en") -> str:
    """Generate structured song lyrics matching a style/mood description.

    Raises LyricsGenerationError if the `claude` CLI fails or returns
    output with no section tags.
    """
    load_dotenv()
    prompt = (
        f"{_INSTRUCTIONS}\n\n"
        f'Generate lyrics for this style/mood: "{style_prompt}"\n'
        f"Target language: {language}\n"
        "Start with the language tag."
    )
    # subprocess.run on Windows doesn't resolve PATHEXT shims (claude.cmd)
    # for a bare "claude" the way cmd.exe/bash do -- resolve the real path
    # via shutil.which, falling back to the literal name elsewhere.
    claude_cli = shutil.which("claude") or "claude"
    try:
        # Pass the prompt via stdin, not argv: on Windows, `claude` resolves
        # to a .cmd shim, and multi-line argv strings get mangled by
        # cmd.exe's own command-line parsing (the model then sees only the
        # first line). `-p` reading from a pipe is the CLI's documented
        # usage ("useful for pipes") and sidesteps that entirely.
        result = subprocess.run(
            [claude_cli, "-p"],
            input=prompt,
            check=True,
            capture_output=True,
            text=True,
            env=_clean_subprocess_env(),
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or "").strip() or str(exc)
        raise LyricsGenerationError(f"Falha ao gerar letra via Claude CLI: {detail}") from exc
    except Exception as exc:
        raise LyricsGenerationError(f"Falha ao gerar letra via Claude CLI: {exc}") from exc

    lyrics = result.stdout.strip()
    has_language_tag = bool(_LANGUAGE_TAG.match(lyrics))
    has_section_marker = any(marker in lyrics for marker in _SECTION_MARKERS)
    if not has_language_tag or not has_section_marker:
        raise LyricsGenerationError(
            f"Letra gerada nao tem marcadores de secao esperados: {lyrics[:200]!r}"
        )
    return lyrics
