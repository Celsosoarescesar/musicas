"""Unit tests for ace_step.kernel_render."""

import importlib.util
from pathlib import Path

import pytest

from ace_step import kernel_render


def _load_rendered_module(path: Path):
    spec = importlib.util.spec_from_file_location("rendered_ace_step_server", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_JOB = {
    "prompt": "epic metal",
    "lyrics": "[en]\n[Verse]\nx",
    "duration": 60.0,
    "seed": 42,
    "bpm": None,
    "keyscale": None,
    "vocal_language": "en",
}


def test_render_job_kernel_copies_metadata_and_embeds_job(tmp_path):
    dest = kernel_render.render_job_kernel(_JOB, tmp_path / "out")

    assert dest == tmp_path / "out"
    assert (dest / "kernel-metadata.json").read_text(encoding="utf-8") == (
        kernel_render._METADATA_PATH.read_text(encoding="utf-8")
    )

    rendered_source = (dest / "ace_step_server.py").read_text(encoding="utf-8")
    assert "_JOB_B64: str | None = None" not in rendered_source

    module = _load_rendered_module(dest / "ace_step_server.py")
    assert module.decode_job(module._JOB_B64) == _JOB


def test_render_job_kernel_round_trips_unicode_quotes_and_newlines(tmp_path):
    job = dict(_JOB, lyrics='[en]\n[Verse]\nquote " and \'apos\' and emoji \U0001F3B5\nline two')

    dest = kernel_render.render_job_kernel(job, tmp_path / "out")

    module = _load_rendered_module(dest / "ace_step_server.py")
    assert module.decode_job(module._JOB_B64) == job


def test_render_job_kernel_raises_if_placeholder_missing(tmp_path, monkeypatch):
    bad_template = tmp_path / "template.py"
    bad_template.write_text("# no placeholder here\n", encoding="utf-8")
    monkeypatch.setattr(kernel_render, "_TEMPLATE_PATH", bad_template)

    with pytest.raises(ValueError, match="_JOB_B64"):
        kernel_render.render_job_kernel(_JOB, tmp_path / "out")
