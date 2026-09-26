"""Unit tests for the pure logic in the ACE-Step Kaggle kernel script.

Loaded via importlib (not a normal package import) because
`projects/ace-step-api/kernel/` isn't a Python package — it's a folder
pushed as-is to a Kaggle kernel. The module itself has no third-party
imports at the top level (see ace_step_server.py's docstring), so this
works without torch/fastapi/diffusers installed locally.
"""

import base64
import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "ace_step"
    / "kernel"
    / "ace_step_server.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("ace_step_server", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ace_step_server = _load_module()


def test_load_secrets_reads_json_file(tmp_path):
    (tmp_path / "secrets.json").write_text(
        '{"NGROK_AUTHTOKEN": "tok", "NGROK_DOMAIN": "example.ngrok-free.dev", '
        '"ACE_STEP_API_KEY": "key"}',
        encoding="utf-8",
    )
    result = ace_step_server.load_secrets(tmp_path)
    assert result == {
        "NGROK_AUTHTOKEN": "tok",
        "NGROK_DOMAIN": "example.ngrok-free.dev",
        "ACE_STEP_API_KEY": "key",
    }


def test_load_secrets_missing_file_raises_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="dataset_sources"):
        ace_step_server.load_secrets(tmp_path)


def test_validate_secrets_passes_when_all_present():
    ace_step_server.validate_secrets(
        {"A": "x", "B": "y"}, ["A", "B"]
    )  # must not raise


def test_validate_secrets_raises_on_missing_key():
    with pytest.raises(ValueError, match="A"):
        ace_step_server.validate_secrets({"B": "y"}, ["A", "B"])


def test_validate_secrets_raises_on_empty_value():
    with pytest.raises(ValueError, match="A"):
        ace_step_server.validate_secrets({"A": "", "B": "y"}, ["A", "B"])


def test_resolve_secrets_dataset_dir_prefers_flat_layout(tmp_path):
    flat = tmp_path / "ace-step-api-secrets"
    flat.mkdir()
    (flat / "secrets.json").write_text("{}", encoding="utf-8")
    nested = tmp_path / "datasets" / "celsosoarescesar" / "ace-step-api-secrets"
    nested.mkdir(parents=True)
    (nested / "secrets.json").write_text("{}", encoding="utf-8")

    result = ace_step_server.resolve_secrets_dataset_dir(
        tmp_path, "celsosoarescesar/ace-step-api-secrets"
    )
    assert result == flat


def test_resolve_secrets_dataset_dir_falls_back_to_nested_layout(tmp_path):
    nested = tmp_path / "datasets" / "celsosoarescesar" / "ace-step-api-secrets"
    nested.mkdir(parents=True)
    (nested / "secrets.json").write_text("{}", encoding="utf-8")

    result = ace_step_server.resolve_secrets_dataset_dir(
        tmp_path, "celsosoarescesar/ace-step-api-secrets"
    )
    assert result == nested


def test_resolve_secrets_dataset_dir_defaults_to_flat_when_neither_exists(tmp_path):
    result = ace_step_server.resolve_secrets_dataset_dir(
        tmp_path, "celsosoarescesar/ace-step-api-secrets"
    )
    assert result == tmp_path / "ace-step-api-secrets"


def test_decode_job_round_trips_dict():
    job = {
        "prompt": "epic metal", "lyrics": "[en]\n[Verse]\nx", "duration": 60.0,
        "seed": 42, "bpm": None, "keyscale": None, "vocal_language": "en",
    }
    encoded = base64.b64encode(json.dumps(job).encode("utf-8")).decode("ascii")
    assert ace_step_server.decode_job(encoded) == job


def test_write_result_json_writes_expected_shape(tmp_path):
    dest = tmp_path / "output" / "result.json"
    result = ace_step_server.write_result_json(
        dest,
        generation_status="done",
        generation_error=None,
        stems_status="error",
        stems_error="cuda out of memory",
    )
    assert result == dest
    assert json.loads(dest.read_text(encoding="utf-8")) == {
        "generation_status": "done",
        "generation_error": None,
        "stems_status": "error",
        "stems_error": "cuda out of memory",
    }


def test_parse_audio_path_extracts_path_from_query_string():
    result = ace_step_server.parse_audio_path("/v1/audio?path=%2Fkaggle%2Fworking%2Fmusica.wav")
    assert result == "/kaggle/working/musica.wav"


def test_parse_audio_path_raises_when_path_param_missing():
    with pytest.raises(ValueError, match="path"):
        ace_step_server.parse_audio_path("/v1/audio?other=1")


def test_build_demucs_command_has_expected_args(tmp_path):
    input_path = tmp_path / "musica.wav"
    out_dir = tmp_path / "out"

    command = ace_step_server.build_demucs_command(input_path, out_dir)

    assert command[0] == ace_step_server.sys.executable
    assert command[1:3] == ["-m", "demucs"]
    assert command[command.index("-n") + 1] == "htdemucs_6s"
    assert command[command.index("-d") + 1] == "cuda"
    assert command[command.index("--out") + 1] == str(out_dir)
    assert command[-1] == str(input_path)


def test_stems_from_output_dir_returns_all_six_paths(tmp_path):
    track_dir = tmp_path / "htdemucs_6s" / "musica"
    track_dir.mkdir(parents=True)
    for name in ("vocals", "drums", "bass", "guitar", "piano", "other"):
        (track_dir / f"{name}.wav").write_bytes(b"fake")

    stems = ace_step_server.stems_from_output_dir(tmp_path, "htdemucs_6s", "musica")

    assert set(stems) == {"vocals", "drums", "bass", "guitar", "piano", "other"}
    assert stems["vocals"] == track_dir / "vocals.wav"


def test_stems_from_output_dir_raises_when_a_stem_is_missing(tmp_path):
    track_dir = tmp_path / "htdemucs_6s" / "musica"
    track_dir.mkdir(parents=True)
    for name in ("vocals", "drums", "bass", "guitar", "piano"):  # "other" missing on purpose
        (track_dir / f"{name}.wav").write_bytes(b"fake")

    with pytest.raises(ValueError, match="other"):
        ace_step_server.stems_from_output_dir(tmp_path, "htdemucs_6s", "musica")


