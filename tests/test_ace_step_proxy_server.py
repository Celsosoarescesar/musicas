"""Unit tests for the ace-step-api kernel's stem-separation proxy.

Loaded via importlib (not a normal package import) because
`projects/ace-step-api/kernel/` isn't a Python package -- same pattern as
tests/test_ace_step_server.py. The module has no heavy imports at the top
level (no torch/demucs), so this works without a GPU or the `demucs`
package installed locally.
"""

import importlib.util
from pathlib import Path

import pytest

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "ace_step"
    / "kernel"
    / "proxy_server.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("proxy_server", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


proxy_server = _load_module()


def test_parse_audio_path_extracts_path_from_query_string():
    result = proxy_server.parse_audio_path("/v1/audio?path=%2Fkaggle%2Fworking%2Fmusica.wav")
    assert result == "/kaggle/working/musica.wav"


def test_parse_audio_path_raises_when_path_param_missing():
    with pytest.raises(ValueError, match="path"):
        proxy_server.parse_audio_path("/v1/audio?other=1")


def test_build_demucs_command_has_expected_args(tmp_path):
    input_path = tmp_path / "musica.wav"
    out_dir = tmp_path / "out"

    command = proxy_server.build_demucs_command(input_path, out_dir)

    assert command[0] == proxy_server.sys.executable
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

    stems = proxy_server.stems_from_output_dir(tmp_path, "htdemucs_6s", "musica")

    assert set(stems) == {"vocals", "drums", "bass", "guitar", "piano", "other"}
    assert stems["vocals"] == track_dir / "vocals.wav"


def test_stems_from_output_dir_raises_when_a_stem_is_missing(tmp_path):
    track_dir = tmp_path / "htdemucs_6s" / "musica"
    track_dir.mkdir(parents=True)
    for name in ("vocals", "drums", "bass", "guitar", "piano"):  # "other" missing on purpose
        (track_dir / f"{name}.wav").write_bytes(b"fake")

    with pytest.raises(ValueError, match="other"):
        proxy_server.stems_from_output_dir(tmp_path, "htdemucs_6s", "musica")


import json
from urllib.parse import quote

from fastapi.testclient import TestClient

API_KEY = "secret"


class _ImmediateThread:
    """Runs its target synchronously in start() instead of spawning a real
    thread -- keeps the separation tests deterministic (same pattern used
    in the music-studio backend's tests)."""

    def __init__(self, target, args=(), kwargs=None, daemon=None):
        self._target = target
        self._args = args
        self._kwargs = kwargs or {}

    def start(self):
        self._target(*self._args, **self._kwargs)


def _client(monkeypatch):
    monkeypatch.setattr(proxy_server.threading, "Thread", _ImmediateThread)
    return TestClient(proxy_server.create_app("http://127.0.0.1:8189", API_KEY))


def _auth():
    return {"Authorization": f"Bearer {API_KEY}"}


def _file_ref(path: Path) -> str:
    return f"/v1/audio?path={quote(str(path), safe='')}"


def test_separate_task_requires_auth(monkeypatch, tmp_path):
    client = _client(monkeypatch)

    response = client.post("/separate_task", json={"file": _file_ref(tmp_path / "a.wav")})

    assert response.status_code == 401


def test_separate_task_happy_path_ends_done(monkeypatch, tmp_path):
    input_path = tmp_path / "musica.wav"
    input_path.write_bytes(b"fake-wav")

    def fake_run(command, **kwargs):
        out_dir = Path(command[command.index("--out") + 1])
        track_dir = out_dir / "htdemucs_6s" / input_path.stem
        track_dir.mkdir(parents=True)
        for name in ("vocals", "drums", "bass", "guitar", "piano", "other"):
            (track_dir / f"{name}.wav").write_bytes(b"fake-stem")
        return proxy_server.subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(proxy_server.subprocess, "run", fake_run)
    client = _client(monkeypatch)

    response = client.post(
        "/separate_task", json={"file": _file_ref(input_path)}, headers=_auth()
    )
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    result = client.post(
        "/query_separation_result", json={"task_id_list": [task_id]}, headers=_auth()
    )
    entries = result.json()
    assert entries[0]["status"] == 1
    stems = json.loads(entries[0]["result"])
    assert set(stems) == {"vocals", "drums", "bass", "guitar", "piano", "other"}


def test_separate_task_records_error_status_on_demucs_failure(monkeypatch, tmp_path):
    input_path = tmp_path / "musica.wav"
    input_path.write_bytes(b"fake-wav")

    def fake_run(command, **kwargs):
        raise proxy_server.subprocess.CalledProcessError(1, command, stderr="cuda out of memory")

    monkeypatch.setattr(proxy_server.subprocess, "run", fake_run)
    client = _client(monkeypatch)

    response = client.post(
        "/separate_task", json={"file": _file_ref(input_path)}, headers=_auth()
    )
    task_id = response.json()["task_id"]

    result = client.post(
        "/query_separation_result", json={"task_id_list": [task_id]}, headers=_auth()
    )
    entry = result.json()[0]
    assert entry["status"] == 2
    assert "cuda out of memory" in entry["result"]


def test_query_separation_result_omits_unknown_task_ids(monkeypatch):
    client = _client(monkeypatch)

    result = client.post(
        "/query_separation_result", json={"task_id_list": ["does-not-exist"]}, headers=_auth()
    )

    assert result.json() == []


def test_get_stem_serves_file(monkeypatch, tmp_path):
    stem_path = tmp_path / "vocals.wav"
    stem_path.write_bytes(b"fake-stem-bytes")
    client = _client(monkeypatch)

    response = client.get(f"/v1/stems?path={quote(str(stem_path), safe='')}", headers=_auth())

    assert response.status_code == 200
    assert response.content == b"fake-stem-bytes"


def test_get_stem_404_when_missing(monkeypatch, tmp_path):
    client = _client(monkeypatch)

    response = client.get(
        f"/v1/stems?path={quote(str(tmp_path / 'missing.wav'), safe='')}", headers=_auth()
    )

    assert response.status_code == 404


def test_get_stem_requires_auth(monkeypatch, tmp_path):
    client = _client(monkeypatch)

    response = client.get(f"/v1/stems?path={quote(str(tmp_path / 'a.wav'), safe='')}")

    assert response.status_code == 401


class _FakeAsyncClient:
    def __init__(self, calls, response):
        self._calls = calls
        self._response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def request(self, method, url, **kwargs):
        self._calls["method"] = method
        self._calls["url"] = url
        self._calls["kwargs"] = kwargs
        return self._response


class _FakeUpstreamResponse:
    def __init__(self, status_code=200, content=b"{}", headers=None):
        self.status_code = status_code
        self.content = content
        self.headers = headers or {}


def test_catch_all_proxies_get_health_to_acestep(monkeypatch):
    calls = {}
    monkeypatch.setattr(
        proxy_server.httpx,
        "AsyncClient",
        lambda: _FakeAsyncClient(calls, _FakeUpstreamResponse(content=b'{"data": {"status": "ok"}}')),
    )
    client = TestClient(proxy_server.create_app("http://127.0.0.1:8189", API_KEY))

    response = client.get("/health")

    assert response.status_code == 200
    assert response.content == b'{"data": {"status": "ok"}}'
    assert calls["method"] == "GET"
    assert calls["url"] == "http://127.0.0.1:8189/health"


def test_catch_all_forwards_authorization_header_and_body(monkeypatch):
    calls = {}
    monkeypatch.setattr(
        proxy_server.httpx, "AsyncClient", lambda: _FakeAsyncClient(calls, _FakeUpstreamResponse())
    )
    client = TestClient(proxy_server.create_app("http://127.0.0.1:8189", API_KEY))

    client.post(
        "/release_task",
        json={"prompt": "epic metal"},
        headers={"Authorization": "Bearer real-acestep-key"},
    )

    assert calls["url"] == "http://127.0.0.1:8189/release_task"
    assert calls["kwargs"]["headers"].get("authorization") == "Bearer real-acestep-key"
    assert b"epic metal" in calls["kwargs"]["content"]


def test_catch_all_does_not_intercept_separate_task_route(monkeypatch):
    calls = {}
    monkeypatch.setattr(
        proxy_server.httpx, "AsyncClient", lambda: _FakeAsyncClient(calls, _FakeUpstreamResponse())
    )
    monkeypatch.setattr(proxy_server.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(
        proxy_server.subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("should not run demucs here")),
    )
    client = TestClient(proxy_server.create_app("http://127.0.0.1:8189", API_KEY))

    client.post("/separate_task", json={"file": "/v1/audio?path=%2Ftmp%2Fa.wav"}, headers=_auth())

    assert calls == {}  # never reached the catch-all/httpx forwarding
