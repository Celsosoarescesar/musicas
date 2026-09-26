"""Unit tests for the pure logic in the ACE-Step Kaggle kernel script.

Loaded via importlib (not a normal package import) because
`projects/ace-step-api/kernel/` isn't a Python package — it's a folder
pushed as-is to a Kaggle kernel. The module itself has no third-party
imports at the top level (see ace_step_server.py's docstring), so this
works without torch/fastapi/diffusers installed locally.
"""

import importlib.util
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


def test_first_dead_process_returns_none_when_all_alive():
    class FakeAlive:
        def poll(self):
            return None

    result = ace_step_server.first_dead_process({"acestep": FakeAlive(), "proxy": FakeAlive()})

    assert result is None


def test_first_dead_process_returns_name_of_dead_one():
    class FakeAlive:
        def poll(self):
            return None

    class FakeDead:
        def poll(self):
            return 1

    result = ace_step_server.first_dead_process({"acestep": FakeAlive(), "proxy": FakeDead()})

    assert result == "proxy"


def test_write_proxy_server_script_matches_repo_file(tmp_path):
    """Guards against embedded/real-file drift.

    Kaggle's `script`-type kernel push only stores the single `code_file`
    (confirmed live -- `proxy_server.py` never reached the kernel, so the
    proxy subprocess failed with FileNotFoundError and took the whole
    kernel down). `ace_step_server.py` now carries proxy_server.py's exact
    bytes base64-embedded and writes them out at runtime instead of relying
    on a sibling file. This test decodes that same embedded constant and
    diffs it against the real file, so an edit to proxy_server.py without
    regenerating the embedded copy fails here instead of on a live kernel.
    """
    real_proxy_path = (
        Path(__file__).resolve().parents[1]
        / "ace_step"
        / "kernel"
        / "proxy_server.py"
    )
    dest = tmp_path / "proxy_server.py"

    result = ace_step_server.write_proxy_server_script(dest)

    assert result == dest
    assert dest.read_bytes() == real_proxy_path.read_bytes()
