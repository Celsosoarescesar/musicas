"""Unit tests for kagglelab.ace_step_client."""

import json
from unittest.mock import MagicMock

import pytest

from ace_step import client as ace_step_client


def _response(status_code=200, json_body=None, text=""):
    resp = MagicMock(status_code=status_code, text=text)
    resp.json.return_value = json_body or {}
    return resp


def test_check_health_returns_data_on_200(monkeypatch):
    fake_response = _response(json_body={"data": {"status": "ok"}, "error": None})
    monkeypatch.setattr(ace_step_client.requests, "get", lambda *a, **k: fake_response)

    result = ace_step_client.check_health("https://example.ngrok-free.dev")

    assert result == {"status": "ok"}


def test_check_health_raises_on_connection_error(monkeypatch):
    def fake_get(*a, **k):
        raise ace_step_client.requests.ConnectionError("refused")

    monkeypatch.setattr(ace_step_client.requests, "get", fake_get)

    with pytest.raises(ace_step_client.AceStepApiError, match="kernel_status"):
        ace_step_client.check_health("https://example.ngrok-free.dev")


def test_check_health_raises_on_non_200(monkeypatch):
    fake_response = _response(status_code=502, text="Bad Gateway")
    monkeypatch.setattr(ace_step_client.requests, "get", lambda *a, **k: fake_response)

    with pytest.raises(ace_step_client.AceStepApiError, match="502"):
        ace_step_client.check_health("https://example.ngrok-free.dev")


def test_check_health_raises_on_non_ok_status(monkeypatch):
    fake_response = _response(json_body={"data": {"status": "loading"}, "error": None})
    monkeypatch.setattr(ace_step_client.requests, "get", lambda *a, **k: fake_response)

    with pytest.raises(ace_step_client.AceStepApiError, match="loading"):
        ace_step_client.check_health("https://example.ngrok-free.dev")


def _generate_kwargs(**overrides):
    kwargs = dict(
        prompt="epic metal",
        lyrics="[en]\n[Verse]\nx",
        duration=10.0,
        seed=42,
        bpm=None,
        keyscale=None,
        vocal_language="en",
        poll_interval=0,
    )
    kwargs.update(overrides)
    return kwargs


def test_generate_music_releases_then_polls_until_success(monkeypatch):
    release_response = _response(
        json_body={"data": {"task_id": "abc123", "status": "queued"}, "error": None}
    )
    running_response = _response(
        json_body={"data": [{"task_id": "abc123", "status": 0}], "error": None}
    )
    result_payload = json.dumps([{"file": "/v1/audio?path=%2Ftmp%2Fabc.wav"}])
    done_response = _response(
        json_body={
            "data": [{"task_id": "abc123", "status": 1, "result": result_payload}],
            "error": None,
        }
    )
    posts = [release_response, running_response, done_response]
    monkeypatch.setattr(ace_step_client.requests, "post", lambda *a, **k: posts.pop(0))
    monkeypatch.setattr(ace_step_client.time, "sleep", lambda *_: None)

    result = ace_step_client.generate_music(
        "https://example.ngrok-free.dev", "secret", **_generate_kwargs()
    )

    assert result == {"file": "/v1/audio?path=%2Ftmp%2Fabc.wav"}
    assert posts == []


def test_generate_music_sends_expected_release_payload(monkeypatch):
    captured = {}

    def fake_post(url, json, headers, timeout):
        if "/release_task" in url:
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            return _response(json_body={"data": {"task_id": "abc123"}, "error": None})
        result_payload = json_module.dumps([{"file": "/v1/audio?path=x"}])
        return _response(
            json_body={
                "data": [{"task_id": "abc123", "status": 1, "result": result_payload}],
                "error": None,
            }
        )

    import json as json_module

    monkeypatch.setattr(ace_step_client.requests, "post", fake_post)
    monkeypatch.setattr(ace_step_client.time, "sleep", lambda *_: None)

    ace_step_client.generate_music(
        "https://example.ngrok-free.dev",
        "secret",
        **_generate_kwargs(bpm=120, keyscale="C Major"),
    )

    assert captured["url"] == "https://example.ngrok-free.dev/release_task"
    assert captured["json"]["prompt"] == "epic metal"
    assert captured["json"]["audio_duration"] == 10.0
    assert captured["json"]["bpm"] == 120
    assert captured["json"]["key_scale"] == "C Major"
    assert captured["json"]["task_type"] == "text2music"
    assert captured["json"]["use_random_seed"] is False
    assert captured["json"]["seed"] == 42
    assert captured["headers"] == {"Authorization": "Bearer secret"}


def test_generate_music_raises_on_task_failure(monkeypatch):
    release_response = _response(json_body={"data": {"task_id": "abc123"}, "error": None})
    failed_response = _response(
        json_body={
            "data": [{"task_id": "abc123", "status": 2, "result": "boom"}],
            "error": None,
        }
    )
    posts = [release_response, failed_response]
    monkeypatch.setattr(ace_step_client.requests, "post", lambda *a, **k: posts.pop(0))
    monkeypatch.setattr(ace_step_client.time, "sleep", lambda *_: None)

    with pytest.raises(ace_step_client.AceStepApiError, match="abc123"):
        ace_step_client.generate_music(
            "https://example.ngrok-free.dev", "secret", **_generate_kwargs()
        )


def test_generate_music_raises_clear_error_on_401(monkeypatch):
    fake_response = _response(status_code=401, text="unauthorized")
    monkeypatch.setattr(ace_step_client.requests, "post", lambda *a, **k: fake_response)

    with pytest.raises(ace_step_client.AceStepApiError, match="ACE_STEP_API_KEY"):
        ace_step_client.generate_music(
            "https://example.ngrok-free.dev", "wrong-key", **_generate_kwargs()
        )


def test_generate_music_raises_on_poll_timeout(monkeypatch):
    release_response = _response(json_body={"data": {"task_id": "abc123"}, "error": None})
    running_response = _response(
        json_body={"data": [{"task_id": "abc123", "status": 0}], "error": None}
    )

    def fake_post(url, **kwargs):
        return release_response if "/release_task" in url else running_response

    monkeypatch.setattr(ace_step_client.requests, "post", fake_post)

    # Fake clock: time.sleep(n) advances it by n, so the poll loop's own
    # `time.monotonic() >= deadline` check naturally fires after enough
    # simulated poll_interval-sized steps -- no real waiting either way.
    clock = {"t": 0.0}
    monkeypatch.setattr(ace_step_client.time, "monotonic", lambda: clock["t"])
    monkeypatch.setattr(ace_step_client.time, "sleep", lambda seconds: clock.__setitem__("t", clock["t"] + seconds))

    with pytest.raises(ace_step_client.AceStepApiError, match="Timeout"):
        ace_step_client.generate_music(
            "https://example.ngrok-free.dev",
            "secret",
            **_generate_kwargs(timeout=5.0, poll_interval=1.0),
        )


def test_generate_music_tolerates_transient_poll_failure_then_succeeds(monkeypatch):
    release_response = _response(json_body={"data": {"task_id": "abc123"}, "error": None})
    result_payload = json.dumps([{"file": "/v1/audio?path=x"}])
    done_response = _response(
        json_body={
            "data": [{"task_id": "abc123", "status": 1, "result": result_payload}],
            "error": None,
        }
    )
    poll_call_count = {"n": 0}

    def fake_post(url, json, headers, timeout):
        if "/release_task" in url:
            return release_response
        poll_call_count["n"] += 1
        if poll_call_count["n"] == 1:
            raise ace_step_client.requests.ConnectionError("transient network blip")
        return done_response

    monkeypatch.setattr(ace_step_client.requests, "post", fake_post)
    monkeypatch.setattr(ace_step_client.time, "sleep", lambda *_: None)

    result = ace_step_client.generate_music(
        "https://example.ngrok-free.dev", "secret", **_generate_kwargs()
    )

    assert result == {"file": "/v1/audio?path=x"}
    assert poll_call_count["n"] == 2


def test_generate_music_raises_after_repeated_poll_failures(monkeypatch):
    release_response = _response(json_body={"data": {"task_id": "abc123"}, "error": None})

    def fake_post(url, json, headers, timeout):
        if "/release_task" in url:
            return release_response
        raise ace_step_client.requests.ConnectionError("connection refused")

    monkeypatch.setattr(ace_step_client.requests, "post", fake_post)
    monkeypatch.setattr(ace_step_client.time, "sleep", lambda *_: None)

    with pytest.raises(ace_step_client.AceStepApiError, match="abc123"):
        ace_step_client.generate_music(
            "https://example.ngrok-free.dev", "secret", **_generate_kwargs()
        )


def test_generate_music_raises_on_empty_query_result(monkeypatch):
    release_response = _response(json_body={"data": {"task_id": "abc123"}, "error": None})
    empty_response = _response(json_body={"data": [], "error": None})
    posts = [release_response, empty_response]
    monkeypatch.setattr(ace_step_client.requests, "post", lambda *a, **k: posts.pop(0))
    monkeypatch.setattr(ace_step_client.time, "sleep", lambda *_: None)

    with pytest.raises(ace_step_client.AceStepApiError, match="abc123"):
        ace_step_client.generate_music(
            "https://example.ngrok-free.dev", "secret", **_generate_kwargs()
        )


def test_generate_music_raises_clear_error_on_release_task_missing_task_id(monkeypatch):
    release_response = _response(json_body={"data": {"status": "queued"}, "error": None})
    monkeypatch.setattr(ace_step_client.requests, "post", lambda *a, **k: release_response)

    with pytest.raises(ace_step_client.AceStepApiError, match="task_id"):
        ace_step_client.generate_music(
            "https://example.ngrok-free.dev", "secret", **_generate_kwargs()
        )


def test_download_audio_writes_file(tmp_path, monkeypatch):
    fake_response = _response(status_code=200)
    fake_response.content = b"RIFF....fake wav bytes"
    monkeypatch.setattr(ace_step_client.requests, "get", lambda *a, **k: fake_response)
    dest = tmp_path / "sub" / "out.wav"

    result = ace_step_client.download_audio(
        "https://example.ngrok-free.dev", "secret", "/v1/audio?path=x", dest
    )

    assert result == dest
    assert dest.read_bytes() == b"RIFF....fake wav bytes"


def test_download_audio_raises_on_non_200(monkeypatch, tmp_path):
    fake_response = _response(status_code=404, text="not found")
    monkeypatch.setattr(ace_step_client.requests, "get", lambda *a, **k: fake_response)

    with pytest.raises(ace_step_client.AceStepApiError, match="404"):
        ace_step_client.download_audio(
            "https://example.ngrok-free.dev", "secret", "/v1/audio?path=missing", tmp_path / "out.wav"
        )


def test_separate_stems_polls_until_done_and_returns_stem_paths(monkeypatch):
    call_count = {"n": 0}

    def fake_post(base_url, path, api_key, payload, timeout):
        if path == "/separate_task":
            return {"task_id": "abc123"}
        assert path == "/query_separation_result"
        call_count["n"] += 1
        if call_count["n"] < 2:
            return [{"task_id": "abc123", "status": 0, "result": None}]
        return [
            {
                "task_id": "abc123",
                "status": 1,
                "result": json.dumps(
                    {
                        "vocals": "/v1/stems?path=%2Ftmp%2Fvocals.wav",
                        "drums": "/v1/stems?path=%2Ftmp%2Fdrums.wav",
                        "bass": "/v1/stems?path=%2Ftmp%2Fbass.wav",
                        "other": "/v1/stems?path=%2Ftmp%2Fother.wav",
                    }
                ),
            }
        ]

    monkeypatch.setattr(ace_step_client, "_post_raw", fake_post)
    monkeypatch.setattr(ace_step_client.time, "sleep", lambda seconds: None)

    stems = ace_step_client.separate_stems(
        "https://example.ngrok-free.dev",
        "secret",
        "/v1/audio?path=%2Ftmp%2Fa.wav",
        poll_interval=0.01,
    )

    assert stems == {
        "vocals": "/v1/stems?path=%2Ftmp%2Fvocals.wav",
        "drums": "/v1/stems?path=%2Ftmp%2Fdrums.wav",
        "bass": "/v1/stems?path=%2Ftmp%2Fbass.wav",
        "other": "/v1/stems?path=%2Ftmp%2Fother.wav",
    }


def test_separate_stems_raises_on_error_status(monkeypatch):
    def fake_post(base_url, path, api_key, payload, timeout):
        if path == "/separate_task":
            return {"task_id": "abc123"}
        return [{"task_id": "abc123", "status": 2, "result": "cuda out of memory"}]

    monkeypatch.setattr(ace_step_client, "_post_raw", fake_post)

    with pytest.raises(ace_step_client.AceStepApiError, match="cuda out of memory"):
        ace_step_client.separate_stems(
            "https://example.ngrok-free.dev", "secret", "/v1/audio?path=%2Ftmp%2Fa.wav"
        )


def test_separate_stems_handles_the_proxy_s_unwrapped_json_response(monkeypatch):
    """Regression test: confirmed live on Kaggle that /separate_task and
    /query_separation_result (proxy_server.py's own endpoints, not proxied
    through to acestep) return their JSON body directly -- no
    {"data": ..., "error": ...} envelope like acestep's own endpoints. A
    version of separate_stems that reused the generic, envelope-unwrapping
    `_post` crashed with KeyError('data') against the real server; this
    test mocks at the `requests.post` level (the real response shape)
    instead of mocking `_post`/`_post_raw` directly, so it would have
    caught that mismatch.
    """
    def fake_post(url, json, headers, timeout):
        if url.endswith("/separate_task"):
            return _response(json_body={"task_id": "abc123"})
        assert url.endswith("/query_separation_result")
        return _response(
            json_body=[
                {
                    "task_id": "abc123",
                    "status": 1,
                    "result": '{"vocals": "/v1/stems?path=%2Ftmp%2Fvocals.wav"}',
                }
            ]
        )

    monkeypatch.setattr(ace_step_client.requests, "post", fake_post)

    stems = ace_step_client.separate_stems(
        "https://example.ngrok-free.dev", "secret", "/v1/audio?path=%2Ftmp%2Fa.wav"
    )

    assert stems == {"vocals": "/v1/stems?path=%2Ftmp%2Fvocals.wav"}


def test_separate_stems_raises_on_timeout(monkeypatch):
    def fake_post(base_url, path, api_key, payload, timeout):
        if path == "/separate_task":
            return {"task_id": "abc123"}
        return [{"task_id": "abc123", "status": 0, "result": None}]

    monkeypatch.setattr(ace_step_client, "_post_raw", fake_post)
    monkeypatch.setattr(ace_step_client.time, "sleep", lambda seconds: None)

    monotonic_values = iter([0.0, 0.0, 100.0])
    monkeypatch.setattr(
        ace_step_client.time, "monotonic", lambda: next(monotonic_values, 100.0)
    )

    with pytest.raises(ace_step_client.AceStepApiError, match="Timeout"):
        ace_step_client.separate_stems(
            "https://example.ngrok-free.dev",
            "secret",
            "/v1/audio?path=%2Ftmp%2Fa.wav",
            timeout=1.0,
            poll_interval=0.01,
        )
