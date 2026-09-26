# ACE-Step Batch Kernel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the ACE-Step Kaggle kernel's server+ngrok-tunnel architecture with a batch kernel that does generation+separation in one run and is retrieved via the Kaggle API's own `kernels_output`, eliminating the ngrok bandwidth cap that broke stem separation in a live test on 2026-09-26.

**Architecture:** One Kaggle kernel run per song does everything (load ACE-Step, generate, run Demucs) and writes results to `/kaggle/working/output/`; the local side renders the kernel with the job's parameters embedded (base64 JSON, since Kaggle only uploads one code file per kernel), pushes it, polls `kernels_status` until terminal, and pulls the finished output with `kernels_output` — no public HTTP endpoint anywhere.

**Tech Stack:** Python 3.11, `uv`, pytest, Kaggle SDK (`kaggle`/`kagglesdk`), stdlib `urllib` for the kernel's own localhost HTTP calls (no new dependencies).

**Spec:** `docs/superpowers/specs/2026-09-26-ace-step-batch-kernel-design.md`

## Global Constraints

- Kernel slug stays `celsosoarescesar/ace-step-api`; secrets dataset stays `celsosoarescesar/ace-step-api-secrets` — neither changes.
- Demucs model stays `htdemucs_6s` (6 stems: vocals/drums/bass/guitar/piano/other) — unchanged.
- `validate_secrets` now requires only `["ACE_STEP_API_KEY"]` (drop `NGROK_AUTHTOKEN`/`NGROK_DOMAIN`).
- Job dict shape is exactly `{"prompt", "lyrics", "duration", "seed", "bpm", "keyscale", "vocal_language"}` — no other fields.
- `result.json` shape is exactly `{"generation_status": "done"|"error", "generation_error": str|None, "stems_status": "done"|"error", "stems_error": str|None}`.
- Terminal kernel statuses are exactly `{"complete", "error", "cancel_acknowledged"}`.
- Default kernel-run timeout is `2700.0` seconds, poll interval `20.0` seconds (local side); kernel-internal health-wait timeout `600.0`s/5s poll, generation timeout `1200.0`s/5s poll (these are separate budgets, at different layers).
- No new pip dependencies: the kernel's own localhost HTTP calls use stdlib `urllib.request`, not `httpx`. `pyngrok` and `httpx` are dropped from the kernel's pip-install list.
- `songs.db` schema is unchanged — no migration.

## Review Focus

- `result.json` says `generation_status: "done"` but the pulled `raw.wav` is missing or zero-length (truncated/failed copy inside the kernel or during `kernels_output`) — must record `status="error"`, never crash or master a garbage/missing file. Test in Task 6.
- A `kernels_status` poll call raises `KaggleResourceError` transiently (network blip) mid-poll — must tolerate a few consecutive failures before giving up, not abort a kernel that's still running fine (this exact problem was already solved once for the old HTTP poll loop; the new kernel-status poll loop needs the same tolerance). Test in Task 6.
- `result.json` exists but is malformed/truncated JSON — must be treated the same as "missing", not raise `json.JSONDecodeError` uncaught. Test in Task 6.
- Unicode/quotes/newlines in generated `lyrics` breaking the base64 embedding into the rendered kernel source. Test in Task 2.
- An unrecognized `get_kernel_status` status string (a future Kaggle SDK enum value this code doesn't know about) being mis-treated as terminal instead of safely kept polling. Test in Task 3.

---

## Task 1: `ace_step_server.py` — pure data/file-shape helpers

**Files:**
- Modify: `ace_step/kernel/ace_step_server.py`
- Modify: `tests/test_ace_step_kernel_server.py`

**Interfaces:**
- Consumes: nothing new (stdlib only).
- Produces (used by Task 2's round-trip test, Task 4, and Task 5):
  - `decode_job(job_b64: str) -> dict`
  - `write_result_json(dest_path: Path, *, generation_status: str, generation_error: str | None, stems_status: str, stems_error: str | None) -> Path`
  - `parse_audio_path(file_ref: str) -> str`
  - `build_demucs_command(input_path: Path, out_dir: Path, *, model: str = "htdemucs_6s", device: str = "cuda") -> list[str]`
  - `stems_from_output_dir(out_dir: Path, model: str, track_name: str) -> dict[str, Path]`
  - `_STEM_NAMES: tuple[str, ...]` = `("vocals", "drums", "bass", "guitar", "piano", "other")`
  - Module constant `_JOB_B64: str | None = None` (the placeholder `kernel_render.render_job_kernel` replaces in Task 2).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_ace_step_kernel_server.py` (keep the existing imports/`_load_module`/`ace_step_server` at top; add `import base64` and `import json` to this test file's own imports):

```python
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
```

Also delete these two now-obsolete tests from the same file (the functions they cover are removed in this task — the kernel no longer runs forever or embeds a proxy script):
- `test_first_dead_process_returns_none_when_all_alive`
- `test_first_dead_process_returns_name_of_dead_one`
- `test_write_proxy_server_script_matches_repo_file`

- [ ] **Step 2: Run tests to verify the new ones fail**

Run: `cd /c/estudos/daw_music_studio && PYTHONPATH=. uv run pytest tests/test_ace_step_kernel_server.py -v`
Expected: the 7 new tests FAIL with `AttributeError` (functions don't exist yet); the 3 deleted tests are gone so they don't run at all.

- [ ] **Step 3: Implement**

In `ace_step/kernel/ace_step_server.py`:

1. Change the top import block from:
```python
import base64
import json
from pathlib import Path
```
to:
```python
import base64
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
```

2. Delete the entire `_PROXY_SERVER_SOURCE_B64 = (...)` constant and the `write_proxy_server_script` function that follows it (everything between the `_PROXY_PORT`/`_ACESTEP_PORT` comment block and `def main():`, except keep `_PROXY_PORT = 8188` and `_ACESTEP_PORT = 8189` for now — `_PROXY_PORT` is removed in Task 5).

3. Delete the `first_dead_process` function entirely.

4. Add these new module-level constants and functions (place them where `first_dead_process` used to be, before `def main():`):

```python
# Set by ace_step.kernel_render.render_job_kernel before this file is pushed
# to Kaggle -- see docs/superpowers/specs/2026-09-26-ace-step-batch-kernel-design.md.
# Left as None here so this file stays importable/testable on its own.
_JOB_B64: str | None = None

_STEM_NAMES = ("vocals", "drums", "bass", "guitar", "piano", "other")


def decode_job(job_b64: str) -> dict:
    """Decode the base64-JSON job embedded by render_job_kernel."""
    return json.loads(base64.b64decode(job_b64.encode("ascii")).decode("utf-8"))


def write_result_json(
    dest_path: Path,
    *,
    generation_status: str,
    generation_error: str | None,
    stems_status: str,
    stems_error: str | None,
) -> Path:
    """Write the kernel's result summary as JSON to dest_path. Returns dest_path."""
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text(
        json.dumps(
            {
                "generation_status": generation_status,
                "generation_error": generation_error,
                "stems_status": stems_status,
                "stems_error": stems_error,
            }
        ),
        encoding="utf-8",
    )
    return dest_path


def parse_audio_path(file_ref: str) -> str:
    """Extract the raw filesystem path from a `/v1/audio?path=...`-style string.

    `file_ref` is the same opaque string the embedded acestep API's
    `/release_task` + `/query_result` result returns in its `file` field --
    a relative URL with the real path URL-encoded in its `path` query
    parameter.
    """
    parsed = urlparse(file_ref)
    query = parse_qs(parsed.query)
    try:
        path_values = query["path"]
    except KeyError as exc:
        raise ValueError(
            f"Nao foi possivel extrair o caminho de {file_ref!r} -- esperava um "
            "parametro de query 'path'"
        ) from exc
    return unquote(path_values[0])


def build_demucs_command(
    input_path: Path, out_dir: Path, *, model: str = "htdemucs_6s", device: str = "cuda"
) -> list[str]:
    """Build the `python -m demucs` command to separate `input_path` into `out_dir`."""
    return [
        sys.executable,
        "-m",
        "demucs",
        "-n",
        model,
        "-d",
        device,
        "--out",
        str(out_dir),
        str(input_path),
    ]


def stems_from_output_dir(out_dir: Path, model: str, track_name: str) -> dict[str, Path]:
    """Map Demucs' output directory layout to the 6 expected stem file paths.

    Demucs writes to
    `<out_dir>/<model>/<track_name>/{vocals,drums,bass,guitar,piano,other}.wav`.
    Raises ValueError (never a partial dict) if any expected stem is missing.
    """
    track_dir = Path(out_dir) / model / track_name
    stems = {name: track_dir / f"{name}.wav" for name in _STEM_NAMES}
    missing = [name for name, path in stems.items() if not path.exists()]
    if missing:
        found = sorted(p.name for p in track_dir.glob("*")) if track_dir.exists() else []
        raise ValueError(
            f"Demucs nao gerou os stems esperados em {track_dir} -- faltando: "
            f"{', '.join(missing)} (arquivos encontrados: {found})"
        )
    return stems
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/estudos/daw_music_studio && PYTHONPATH=. uv run pytest tests/test_ace_step_kernel_server.py -v`
Expected: all tests PASS (the 7 new ones plus the untouched pre-existing ones: `load_secrets`, `validate_secrets`, `resolve_secrets_dataset_dir` tests).

- [ ] **Step 5: Commit**

```bash
git add ace_step/kernel/ace_step_server.py tests/test_ace_step_kernel_server.py
git commit -m "refactor: mover helpers puros do proxy pro kernel, preparar embed de job"
```

---

## Task 2: `ace_step/kernel_render.py` — render a job into a pushable kernel folder

**Files:**
- Create: `ace_step/kernel_render.py`
- Create: `tests/test_ace_step_kernel_render.py`

**Interfaces:**
- Consumes: `ace_step/kernel/ace_step_server.py`'s `_JOB_B64: str | None = None` placeholder line (Task 1) and `decode_job` (used only by this task's own test, to round-trip-verify the embedding).
- Produces (used by Task 6): `render_job_kernel(job: dict, dest_dir: Path) -> Path`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_ace_step_kernel_render.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/estudos/daw_music_studio && PYTHONPATH=. uv run pytest tests/test_ace_step_kernel_render.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'ace_step.kernel_render'`.

- [ ] **Step 3: Implement**

Create `ace_step/kernel_render.py`:

```python
"""Render a self-contained Kaggle kernel folder for one song-generation job.

Kaggle's `script`-type kernel push only uploads a single code file, so
per-run parameters can't be passed as arguments. Instead, the job dict is
JSON-serialized, base64-encoded, and embedded as the `_JOB_B64` module
constant in a copy of `ace_step/kernel/ace_step_server.py`, replacing its
`None` placeholder. See
docs/superpowers/specs/2026-09-26-ace-step-batch-kernel-design.md.
"""

import base64
import json
import shutil
from pathlib import Path

_KERNEL_DIR = Path(__file__).parent / "kernel"
_TEMPLATE_PATH = _KERNEL_DIR / "ace_step_server.py"
_METADATA_PATH = _KERNEL_DIR / "kernel-metadata.json"
_PLACEHOLDER = "_JOB_B64: str | None = None"


def render_job_kernel(job: dict, dest_dir: Path) -> Path:
    """Render a pushable kernel folder for `job` into `dest_dir`. Returns dest_dir.

    Raises ValueError if the template's `_JOB_B64` placeholder isn't found
    exactly once (the template changed and this function needs updating).
    """
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    source = _TEMPLATE_PATH.read_text(encoding="utf-8")
    occurrences = source.count(_PLACEHOLDER)
    if occurrences != 1:
        raise ValueError(
            f"Esperava exatamente 1 ocorrencia de {_PLACEHOLDER!r} em "
            f"{_TEMPLATE_PATH}, encontrei {occurrences} -- o template mudou, "
            "atualize render_job_kernel."
        )

    job_b64 = base64.b64encode(json.dumps(job, ensure_ascii=False).encode("utf-8")).decode(
        "ascii"
    )
    rendered = source.replace(_PLACEHOLDER, f'_JOB_B64: str | None = "{job_b64}"')
    (dest_dir / "ace_step_server.py").write_text(rendered, encoding="utf-8")

    shutil.copy(_METADATA_PATH, dest_dir / "kernel-metadata.json")
    return dest_dir
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/estudos/daw_music_studio && PYTHONPATH=. uv run pytest tests/test_ace_step_kernel_render.py -v`
Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add ace_step/kernel_render.py tests/test_ace_step_kernel_render.py
git commit -m "feat: render_job_kernel embute parametros da musica no kernel batch"
```

---

## Task 3: `kernels.py` — terminal kernel status classification

**Files:**
- Modify: `ace_step/kernels.py`
- Modify: `tests/test_ace_step_kernels.py`

**Interfaces:**
- Consumes: nothing new.
- Produces (used by Task 6): `is_terminal_kernel_status(status: str) -> bool`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_ace_step_kernels.py` (add `import pytest` if not already imported — it already is):

```python
@pytest.mark.parametrize(
    "status,expected",
    [
        ("queued", False),
        ("running", False),
        ("complete", True),
        ("error", True),
        ("cancel_acknowledged", True),
        ("some_future_status_not_seen_yet", False),
    ],
)
def test_is_terminal_kernel_status(status, expected):
    assert kernels.is_terminal_kernel_status(status) is expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /c/estudos/daw_music_studio && PYTHONPATH=. uv run pytest tests/test_ace_step_kernels.py -v -k is_terminal`
Expected: FAIL with `AttributeError: module 'ace_step.kernels' has no attribute 'is_terminal_kernel_status'`.

- [ ] **Step 3: Implement**

Add to `ace_step/kernels.py` (after the imports, before `search_kernels`):

```python
_TERMINAL_KERNEL_STATUSES = frozenset({"complete", "error", "cancel_acknowledged"})


def is_terminal_kernel_status(status: str) -> bool:
    """Return True if `status` (as normalized by get_kernel_status) means the
    kernel run has finished, one way or another (success, failure, or
    cancellation) -- False for anything still in progress, including a
    status value this code doesn't recognize (keep polling rather than
    silently misclassifying an unknown status as done).
    """
    return status in _TERMINAL_KERNEL_STATUSES
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/estudos/daw_music_studio && PYTHONPATH=. uv run pytest tests/test_ace_step_kernels.py -v`
Expected: all tests PASS, including the 6 new parametrized cases.

- [ ] **Step 5: Commit**

```bash
git add ace_step/kernels.py tests/test_ace_step_kernels.py
git commit -m "feat: is_terminal_kernel_status classifica status de kernel do Kaggle"
```

---

## Task 4: `ace_step_server.py` — localhost HTTP client + health/generation polling

**Files:**
- Modify: `ace_step/kernel/ace_step_server.py`
- Modify: `tests/test_ace_step_kernel_server.py`

**Interfaces:**
- Consumes: Task 1's `parse_audio_path` is NOT used here (it's used in Task 5's `main()`); this task only needs stdlib.
- Produces (used by Task 5's `main()`): `_post_json`, `_get_json`, `wait_for_health(base_url, api_key, *, timeout, poll_interval) -> None`, `wait_for_generation(base_url, api_key, job, *, timeout, poll_interval) -> str`

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_ace_step_kernel_server.py` (add `import json` already present from Task 1; no other new top-level imports needed in the test file):

```python
class _FakeHTTPResponse:
    def __init__(self, body):
        self._body = json.dumps(body).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_post_json_sends_body_and_parses_response(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["method"] = request.get_method()
        captured["data"] = request.data
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout
        return _FakeHTTPResponse({"task_id": "abc"})

    monkeypatch.setattr(ace_step_server.urllib.request, "urlopen", fake_urlopen)

    result = ace_step_server._post_json(
        "http://127.0.0.1:8189/release_task",
        {"prompt": "epic metal"},
        headers={"Authorization": "Bearer key"},
        timeout=30.0,
    )

    assert result == {"task_id": "abc"}
    assert captured["method"] == "POST"
    assert captured["url"] == "http://127.0.0.1:8189/release_task"
    assert json.loads(captured["data"]) == {"prompt": "epic metal"}
    assert captured["headers"].get("Authorization") == "Bearer key"
    assert captured["timeout"] == 30.0


def test_get_json_sends_headers_and_parses_response(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        return _FakeHTTPResponse({"data": {"status": "ok"}})

    monkeypatch.setattr(ace_step_server.urllib.request, "urlopen", fake_urlopen)

    result = ace_step_server._get_json(
        "http://127.0.0.1:8189/health", headers={"Authorization": "Bearer key"}, timeout=10.0
    )

    assert result == {"data": {"status": "ok"}}
    assert captured["url"] == "http://127.0.0.1:8189/health"
    assert captured["headers"].get("Authorization") == "Bearer key"


def test_wait_for_health_returns_when_status_ok(monkeypatch):
    monkeypatch.setattr(
        ace_step_server, "_get_json", lambda url, headers, timeout: {"data": {"status": "ok"}}
    )
    ace_step_server.wait_for_health("http://127.0.0.1:8189", "key", timeout=5.0, poll_interval=0.01)


def test_wait_for_health_times_out_when_never_ok(monkeypatch):
    monkeypatch.setattr(
        ace_step_server, "_get_json", lambda url, headers, timeout: {"data": {"status": "loading"}}
    )
    with pytest.raises(TimeoutError):
        ace_step_server.wait_for_health(
            "http://127.0.0.1:8189", "key", timeout=0.05, poll_interval=0.01
        )


_TEST_JOB = {
    "prompt": "epic metal", "lyrics": "[en]\nx", "duration": 60.0, "seed": 42,
    "bpm": None, "keyscale": None, "vocal_language": "en",
}


def test_wait_for_generation_returns_file_ref_on_status_1(monkeypatch):
    def fake_post_json(url, payload, headers, timeout):
        if url.endswith("/release_task"):
            return {"task_id": "abc"}
        return [{"status": 1, "result": json.dumps([{"file": "/v1/audio?path=%2Ftmp%2Fa.wav"}])}]

    monkeypatch.setattr(ace_step_server, "_post_json", fake_post_json)

    result = ace_step_server.wait_for_generation(
        "http://127.0.0.1:8189", "key", _TEST_JOB, timeout=5.0, poll_interval=0.01
    )

    assert result == "/v1/audio?path=%2Ftmp%2Fa.wav"


def test_wait_for_generation_raises_runtime_error_on_status_2(monkeypatch):
    def fake_post_json(url, payload, headers, timeout):
        if url.endswith("/release_task"):
            return {"task_id": "abc"}
        return [{"status": 2, "result": "cuda out of memory"}]

    monkeypatch.setattr(ace_step_server, "_post_json", fake_post_json)

    with pytest.raises(RuntimeError, match="cuda out of memory"):
        ace_step_server.wait_for_generation(
            "http://127.0.0.1:8189", "key", _TEST_JOB, timeout=5.0, poll_interval=0.01
        )


def test_wait_for_generation_times_out_when_never_done(monkeypatch):
    def fake_post_json(url, payload, headers, timeout):
        if url.endswith("/release_task"):
            return {"task_id": "abc"}
        return [{"status": 0, "result": None}]

    monkeypatch.setattr(ace_step_server, "_post_json", fake_post_json)

    with pytest.raises(TimeoutError):
        ace_step_server.wait_for_generation(
            "http://127.0.0.1:8189", "key", _TEST_JOB, timeout=0.05, poll_interval=0.01
        )
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/estudos/daw_music_studio && PYTHONPATH=. uv run pytest tests/test_ace_step_kernel_server.py -v -k "post_json or get_json or wait_for"`
Expected: FAIL with `AttributeError` (none of these names exist yet).

- [ ] **Step 3: Implement**

1. Change the top import block (from Task 1) to add `time` and `urllib.request`/`urllib.error`:
```python
import base64
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse
```

2. Add these functions, right after `stems_from_output_dir` (still before `def main():`):

```python
def _post_json(url: str, payload: dict, *, headers: dict, timeout: float) -> dict:
    """POST JSON to url, return the parsed JSON response body."""
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, method="POST", headers={**headers, "Content-Type": "application/json"}
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _get_json(url: str, *, headers: dict, timeout: float) -> dict:
    """GET url, return the parsed JSON response body."""
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_health(base_url: str, api_key: str, *, timeout: float, poll_interval: float) -> None:
    """Poll base_url/health until it reports status 'ok'. Raises TimeoutError otherwise."""
    deadline = time.monotonic() + timeout
    headers = {"Authorization": f"Bearer {api_key}"}
    last_error = None
    while time.monotonic() < deadline:
        try:
            body = _get_json(f"{base_url}/health", headers=headers, timeout=10.0)
            status = body.get("data", {}).get("status")
            if status == "ok":
                return
            last_error = f"status atual: {status!r}"
        except (urllib.error.URLError, OSError, ValueError) as exc:
            last_error = str(exc)
        time.sleep(poll_interval)
    raise TimeoutError(
        f"Timeout de {timeout}s esperando {base_url}/health responder 'ok' -- "
        f"ultimo erro: {last_error}"
    )


def wait_for_generation(
    base_url: str, api_key: str, job: dict, *, timeout: float, poll_interval: float
) -> str:
    """Submit `job` to /release_task and poll /query_result until done.

    Returns the raw `/v1/audio?path=...`-style file reference string on
    success. Raises RuntimeError if the task fails, TimeoutError if it
    doesn't finish within `timeout` seconds.
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "prompt": job["prompt"],
        "lyrics": job["lyrics"],
        "audio_duration": job["duration"],
        "audio_format": "wav",
        "use_random_seed": False,
        "seed": job["seed"],
        "bpm": job["bpm"],
        "key_scale": job["keyscale"],
        "vocal_language": job["vocal_language"],
        "task_type": "text2music",
    }
    task = _post_json(f"{base_url}/release_task", payload, headers=headers, timeout=30.0)
    task_id = task["task_id"]

    deadline = time.monotonic() + timeout
    while True:
        query = _post_json(
            f"{base_url}/query_result", {"task_id_list": [task_id]}, headers=headers, timeout=30.0
        )
        if query:
            entry = query[0]
            status = entry["status"]
            if status == 1:
                return json.loads(entry["result"])[0]["file"]
            if status == 2:
                raise RuntimeError(f"Geracao falhou (task {task_id}): {entry.get('result')}")
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Timeout de {timeout}s esperando a task {task_id} terminar")
        time.sleep(poll_interval)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/estudos/daw_music_studio && PYTHONPATH=. uv run pytest tests/test_ace_step_kernel_server.py -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add ace_step/kernel/ace_step_server.py tests/test_ace_step_kernel_server.py
git commit -m "feat: cliente HTTP localhost + polling de health/geracao no kernel"
```

---

## Task 5: `ace_step_server.py` — `main()` batch rewrite

**Files:**
- Modify: `ace_step/kernel/ace_step_server.py`

**Interfaces:**
- Consumes: Task 1's `decode_job`, `write_result_json`, `parse_audio_path`, `build_demucs_command`, `stems_from_output_dir`, `_STEM_NAMES`, `_JOB_B64`; Task 4's `wait_for_health`, `wait_for_generation`.
- Produces: the kernel's actual runtime behavior (writes `/kaggle/working/output/{raw.wav,result.json,stems/*.wav}`, exits 0/1) — exercised by Task 9's live run, not by unit tests (matches this file's existing convention: only the pure helpers above `main()` are unit-tested; `main()` itself needs a real GPU/Kaggle kernel and is verified live).

- [ ] **Step 1: Replace `main()`**

In `ace_step/kernel/ace_step_server.py`, make these changes to `main()`:

1. Change:
```python
    validate_secrets(secrets, ["NGROK_AUTHTOKEN", "NGROK_DOMAIN", "ACE_STEP_API_KEY"])
    ngrok_authtoken = secrets["NGROK_AUTHTOKEN"]
    ngrok_domain = secrets["NGROK_DOMAIN"]
    api_key = secrets["ACE_STEP_API_KEY"]
```
to:
```python
    validate_secrets(secrets, ["ACE_STEP_API_KEY"])
    api_key = secrets["ACE_STEP_API_KEY"]
```

2. Leave the clone/patch/flash-attn-filter/disk-logging sections (from `log_disk_usage("antes do clone")` through `filtered_requirements_path.write_text(...)`) exactly as they are — unchanged.

3. Change the pip-install-extras call from:
```python
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "-q", "--no-cache-dir", "-U",
            "pyngrok", "fastapi", "uvicorn", "httpx", "demucs",
        ],
        check=True,
    )
    log_disk_usage("depois do pip install")

    from pyngrok import ngrok

    env = os.environ.copy()
```
to:
```python
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "-q", "--no-cache-dir", "-U",
            "fastapi", "uvicorn", "demucs",
        ],
        check=True,
    )
    log_disk_usage("depois do pip install")

    env = os.environ.copy()
```

4. In the `env.update({...})` dict, change `"ACESTEP_API_HOST": "0.0.0.0",` to `"ACESTEP_API_HOST": "127.0.0.1",` (everything else in that dict is unchanged).

5. Replace everything from `logger.info(f"Subindo acestep.api_server ...")` through the end of the function (the old proxy launch, ngrok tunnel, and forever-loop) with:

```python
    logger.info(f"Subindo acestep.api_server (config={_ACESTEP_MODEL_CONFIG})...")
    server_process = subprocess.Popen(
        [sys.executable, "-m", "acestep.api_server"],
        cwd=str(repo_dir),
        env=env,
    )

    api_base_url = f"http://127.0.0.1:{_ACESTEP_PORT}"
    output_dir = Path("/kaggle/working/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    if _JOB_B64 is None:
        raise RuntimeError(
            "_JOB_B64 nao foi definido -- este kernel precisa ser renderizado por "
            "ace_step.kernel_render.render_job_kernel antes de ser enviado ao Kaggle"
        )
    job = decode_job(_JOB_B64)

    generation_status = "error"
    generation_error = None
    stems_status = "error"
    stems_error = None

    try:
        logger.info("Esperando acestep.api_server ficar saudavel...")
        wait_for_health(api_base_url, api_key, timeout=600.0, poll_interval=5.0)

        logger.info("Gerando musica...")
        raw_file_ref = wait_for_generation(
            api_base_url, api_key, job, timeout=1200.0, poll_interval=5.0
        )
        source_path = parse_audio_path(raw_file_ref)
        raw_dest = output_dir / "raw.wav"
        shutil.copy(source_path, raw_dest)
        generation_status = "done"
        logger.info(f"Musica gerada e copiada para {raw_dest}.")

        try:
            demucs_out_dir = Path("/kaggle/working/demucs_out")
            command = build_demucs_command(raw_dest, demucs_out_dir)
            subprocess.run(command, check=True, capture_output=True, text=True)
            stems = stems_from_output_dir(demucs_out_dir, "htdemucs_6s", raw_dest.stem)
            stems_out_dir = output_dir / "stems"
            stems_out_dir.mkdir(parents=True, exist_ok=True)
            for name, stem_path in stems.items():
                shutil.copy(stem_path, stems_out_dir / f"{name}.wav")
            stems_status = "done"
            logger.info("Separacao de stems concluida.")
        except subprocess.CalledProcessError as exc:
            stems_error = (exc.stderr or "").strip() or str(exc)
            logger.error(f"Separacao de stems falhou: {stems_error}")
        except Exception as exc:
            stems_error = str(exc)
            logger.error(f"Separacao de stems falhou: {stems_error}")
    except Exception as exc:
        generation_error = str(exc)
        logger.error(f"Geracao falhou: {generation_error}")
    finally:
        write_result_json(
            output_dir / "result.json",
            generation_status=generation_status,
            generation_error=generation_error,
            stems_status=stems_status,
            stems_error=stems_error,
        )
        shutil.rmtree(repo_dir, ignore_errors=True)
        server_process.terminate()

    sys.exit(0 if generation_status == "done" else 1)
```

6. Delete the now-unused `_PROXY_PORT = 8188` constant (search for it near the top of the file, alongside `_ACESTEP_PORT = 8189` — remove only the `_PROXY_PORT` line, keep `_ACESTEP_PORT`).

- [ ] **Step 2: Run the full local test suite as a regression check**

Run: `cd /c/estudos/daw_music_studio && PYTHONPATH=. uv run pytest tests/test_ace_step_kernel_server.py -v`
Expected: all tests PASS (this step doesn't test `main()` itself, just confirms the pure-helper tests from Tasks 1 and 4 still pass after editing the same file). `main()`'s actual behavior is verified live in Task 9.

- [ ] **Step 3: Commit**

```bash
git add ace_step/kernel/ace_step_server.py
git commit -m "feat: main() do kernel vira batch (gera + separa + sai, sem ngrok)"
```

---

## Task 6: `orchestrator.py` — batch-driven `run_generation`

**Files:**
- Modify: `ace_step/orchestrator.py`
- Modify: `tests/test_ace_step_orchestrator.py` (full rewrite — the old HTTP-mocked tests no longer apply)

**Interfaces:**
- Consumes: Task 2's `kernel_render.render_job_kernel`; Task 3's `kernels.is_terminal_kernel_status`; existing `kernels.push_kernel`/`get_kernel_status`/`pull_kernel_output`; existing `mastering.normalize_loudness`; existing `song_db`; existing `kaggle_client.KaggleResourceError`.
- Produces (used by Task 7): `run_generation(db_path, output_dir, song_id, *, prompt, duration, seed, bpm, keyscale, vocal_language, lufs_target, lyrics=None, timeout=2700.0, poll_interval=20.0) -> tuple[str, str | None]` — note `run_separation` and the `base_url`/`api_key` parameters are gone.

- [ ] **Step 1: Write the failing tests**

Replace the entire contents of `tests/test_ace_step_orchestrator.py` with:

```python
"""Unit tests for ace_step.orchestrator."""

import json
from pathlib import Path

import pytest

from ace_step import orchestrator
from ace_step.kaggle_client import KaggleResourceError


def _base_kwargs(**overrides):
    kwargs = dict(
        prompt="epic metal",
        duration=60.0,
        seed=42,
        bpm=None,
        keyscale=None,
        vocal_language="en",
        lufs_target=-9.0,
    )
    kwargs.update(overrides)
    return kwargs


def _write_result_json(pulled_dir: Path, **fields):
    output_dir = pulled_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "generation_status": "done",
        "generation_error": None,
        "stems_status": "done",
        "stems_error": None,
    }
    payload.update(fields)
    (output_dir / "result.json").write_text(json.dumps(payload), encoding="utf-8")
    return output_dir


def _write_raw_and_stems(output_dir: Path, *, raw_bytes=b"RIFF-fake-wav-bytes", with_stems=True):
    (output_dir / "raw.wav").write_bytes(raw_bytes)
    if with_stems:
        stems_dir = output_dir / "stems"
        stems_dir.mkdir(parents=True, exist_ok=True)
        for name in ("vocals", "drums", "bass", "guitar", "piano", "other"):
            (stems_dir / f"{name}.wav").write_bytes(b"stem-bytes")


def _stub_common(monkeypatch, updates, *, tmp_path):
    monkeypatch.setattr(
        orchestrator.song_db,
        "update_song",
        lambda db, song_id, **fields: updates.append(fields),
    )
    monkeypatch.setattr(
        orchestrator.song_lyrics, "generate_lyrics", lambda prompt, language: "[en]\n[Verse]\nx"
    )
    monkeypatch.setattr(
        orchestrator.kernel_render, "render_job_kernel", lambda job, dest_dir: Path(dest_dir)
    )
    monkeypatch.setattr(orchestrator.kernels, "push_kernel", lambda folder: "owner/kernel")
    monkeypatch.setattr(
        orchestrator.kernels, "get_kernel_status", lambda ref: {"status": "complete", "failure_message": ""}
    )

    def fake_normalize_loudness(input_path, output_path, target_lufs):
        Path(output_path).write_bytes(Path(input_path).read_bytes())

    monkeypatch.setattr(orchestrator.song_mastering, "normalize_loudness", fake_normalize_loudness)


def test_run_generation_happy_path_returns_done_and_updates_db(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fake_pull_kernel_output(ref, dest_dir):
        output_dir = _write_result_json(Path(dest_dir))
        _write_raw_and_stems(output_dir)
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "done"
    assert detail == str(tmp_path / "1_master.wav")
    assert Path(detail).read_bytes() == b"RIFF-fake-wav-bytes"
    assert {"status": "generating", "lyrics": "[en]\n[Verse]\nx"} in updates
    assert {"status": "done", "output_path": str(tmp_path / "1_master.wav")} in updates
    done_update = next(u for u in updates if u.get("stems_status") == "done")
    for name in ("vocals", "drums", "bass", "guitar", "piano", "other"):
        expected_path = str(tmp_path / f"1_stem_{name}.wav")
        assert done_update[f"stem_{name}_path"] == expected_path
        assert Path(expected_path).read_bytes() == b"stem-bytes"
    assert not (tmp_path / ".kernel_1").exists()
    assert not (tmp_path / ".pulled_1").exists()


def test_run_generation_skips_lyrics_when_lyrics_given(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fail_if_called(*a, **k):
        raise AssertionError("generate_lyrics should not be called when lyrics is given")

    monkeypatch.setattr(orchestrator.song_lyrics, "generate_lyrics", fail_if_called)

    def fake_pull_kernel_output(ref, dest_dir):
        output_dir = _write_result_json(Path(dest_dir))
        _write_raw_and_stems(output_dir)
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, _detail = orchestrator.run_generation(
        db_path, tmp_path, 1, lyrics="[en]\n[Verse]\nready", **_base_kwargs()
    )

    assert status == "done"


def test_run_generation_records_error_when_push_kernel_fails(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fake_push_kernel(folder):
        raise KaggleResourceError("kernel invalido")

    monkeypatch.setattr(orchestrator.kernels, "push_kernel", fake_push_kernel)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "error"
    assert detail == "kernel invalido"
    assert {"status": "error", "error_message": "kernel invalido"} in updates


def test_run_generation_records_error_on_polling_timeout(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)
    monkeypatch.setattr(
        orchestrator.kernels, "get_kernel_status", lambda ref: {"status": "running", "failure_message": ""}
    )

    status, detail = orchestrator.run_generation(
        db_path, tmp_path, 1, timeout=0.05, poll_interval=0.01, **_base_kwargs()
    )

    assert status == "error"
    assert "Timeout" in detail
    assert "celsosoarescesar/ace-step-api" in detail


def test_run_generation_tolerates_transient_status_poll_failures(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    calls = {"count": 0}

    def flaky_get_kernel_status(ref):
        calls["count"] += 1
        if calls["count"] <= 2:
            raise KaggleResourceError("instabilidade transitoria")
        return {"status": "complete", "failure_message": ""}

    monkeypatch.setattr(orchestrator.kernels, "get_kernel_status", flaky_get_kernel_status)

    def fake_pull_kernel_output(ref, dest_dir):
        output_dir = _write_result_json(Path(dest_dir))
        _write_raw_and_stems(output_dir)
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, _detail = orchestrator.run_generation(
        db_path, tmp_path, 1, timeout=5.0, poll_interval=0.01, **_base_kwargs()
    )

    assert status == "done"
    assert calls["count"] >= 3


def test_run_generation_records_error_when_kernel_status_is_error(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)
    monkeypatch.setattr(
        orchestrator.kernels,
        "get_kernel_status",
        lambda ref: {"status": "error", "failure_message": "kernel crashou"},
    )

    def fail_if_called(ref, dest_dir):
        raise AssertionError("pull_kernel_output should not be called when the kernel errored")

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fail_if_called)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "error"
    assert "kernel crashou" in detail


def test_run_generation_records_error_when_result_json_missing(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fake_pull_kernel_output(ref, dest_dir):
        Path(dest_dir).mkdir(parents=True, exist_ok=True)
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "error"
    assert "result.json" in detail


def test_run_generation_records_error_when_result_json_is_malformed(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fake_pull_kernel_output(ref, dest_dir):
        output_dir = Path(dest_dir) / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "result.json").write_text("{not valid json", encoding="utf-8")
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "error"
    assert "result.json" in detail


def test_run_generation_records_error_when_generation_status_not_done(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fake_pull_kernel_output(ref, dest_dir):
        _write_result_json(
            Path(dest_dir), generation_status="error", generation_error="cuda out of memory"
        )
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "error"
    assert detail == "cuda out of memory"


def test_run_generation_records_error_when_raw_wav_missing_despite_done_status(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fake_pull_kernel_output(ref, dest_dir):
        _write_result_json(Path(dest_dir))  # says done, but never writes raw.wav
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "error"
    assert "raw.wav" in detail


def test_run_generation_records_stems_error_without_failing_generation(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fake_pull_kernel_output(ref, dest_dir):
        output_dir = _write_result_json(
            Path(dest_dir), stems_status="error", stems_error="cuda out of memory"
        )
        _write_raw_and_stems(output_dir, with_stems=False)
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "done"
    assert {
        "stems_status": "error", "stems_error_message": "cuda out of memory"
    } in updates


def test_run_generation_records_stems_error_when_stem_file_copy_fails(monkeypatch, tmp_path):
    db_path = tmp_path / "songs.db"
    updates = []
    _stub_common(monkeypatch, updates, tmp_path=tmp_path)

    def fake_pull_kernel_output(ref, dest_dir):
        output_dir = _write_result_json(Path(dest_dir))  # says stems done
        _write_raw_and_stems(output_dir, with_stems=False)  # but no stem files exist
        return Path(dest_dir)

    monkeypatch.setattr(orchestrator.kernels, "pull_kernel_output", fake_pull_kernel_output)

    status, detail = orchestrator.run_generation(db_path, tmp_path, 1, **_base_kwargs())

    assert status == "done"  # missing stems must never flip generation back to error
    error_update = next(u for u in updates if u.get("stems_status") == "error")
    assert "stems_error_message" in error_update
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /c/estudos/daw_music_studio && PYTHONPATH=. uv run pytest tests/test_ace_step_orchestrator.py -v`
Expected: FAIL with `AttributeError: module 'ace_step.orchestrator' has no attribute 'kernel_render'` (or similar) since `orchestrator.py` hasn't been rewritten yet.

- [ ] **Step 3: Implement**

Replace the entire contents of `ace_step/orchestrator.py` with:

```python
"""Shared song-generation pipeline, used by scripts/criar_musica.py.

One Kaggle kernel run does generation + Demucs stem separation for a
single song end-to-end (no live server, no tunnel) -- see
docs/superpowers/specs/2026-09-26-ace-step-batch-kernel-design.md.
"""

import json
import shutil
import time
from pathlib import Path

from ace_step import kernel_render, kernels, mastering as song_mastering, song_db
from ace_step import lyrics as song_lyrics
from ace_step.kaggle_client import KaggleResourceError

_KERNEL_REF = "celsosoarescesar/ace-step-api"
_STEM_NAMES = ("vocals", "drums", "bass", "guitar", "piano", "other")
_MAX_CONSECUTIVE_STATUS_POLL_FAILURES = 3


def _wait_for_kernel_terminal(ref: str, *, timeout: float, poll_interval: float) -> dict:
    """Poll get_kernel_status(ref) until it reaches a terminal status.

    Tolerates up to _MAX_CONSECUTIVE_STATUS_POLL_FAILURES consecutive
    KaggleResourceErrors (transient API hiccups) before giving up -- a
    single failed poll shouldn't abort a kernel that's still running fine.
    Raises TimeoutError if no terminal status is reached within `timeout`
    seconds, or re-raises KaggleResourceError if polling keeps failing.
    """
    deadline = time.monotonic() + timeout
    consecutive_failures = 0
    while True:
        try:
            result = kernels.get_kernel_status(ref)
        except KaggleResourceError:
            consecutive_failures += 1
            if consecutive_failures > _MAX_CONSECUTIVE_STATUS_POLL_FAILURES:
                raise
            time.sleep(poll_interval)
            continue
        consecutive_failures = 0
        if kernels.is_terminal_kernel_status(result["status"]):
            return result
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"Timeout de {timeout}s esperando o kernel {ref} terminar -- ele "
                "pode continuar rodando no Kaggle; consulte "
                f"'uv run python scripts/kernel_status.py {ref}' mais tarde"
            )
        time.sleep(poll_interval)


def run_generation(
    db_path: Path,
    output_dir: Path,
    song_id: int,
    *,
    prompt: str,
    duration: float,
    seed: int,
    bpm: int | None,
    keyscale: str | None,
    vocal_language: str,
    lufs_target: float,
    lyrics: str | None = None,
    timeout: float = 2700.0,
    poll_interval: float = 20.0,
) -> tuple[str, str | None]:
    """Run the full generation+separation pipeline for an already-created song row.

    Renders and pushes a batch Kaggle kernel that does generation and
    Demucs separation in one run, waits for it to finish, and pulls its
    output. Never raises -- every failure is recorded on the row via
    `song_db.update_song(..., status="error", error_message=...)` instead
    of propagating. Returns `("done", output_path)` on success or
    `("error", error_message)` on failure.
    """
    output_dir = Path(output_dir)
    tmp_kernel_dir = output_dir / f".kernel_{song_id}"
    tmp_pulled_dir = output_dir / f".pulled_{song_id}"
    try:
        resolved_lyrics = lyrics or song_lyrics.generate_lyrics(prompt, language=vocal_language)
        song_db.update_song(db_path, song_id, status="generating", lyrics=resolved_lyrics)

        job = {
            "prompt": prompt,
            "lyrics": resolved_lyrics,
            "duration": duration,
            "seed": seed,
            "bpm": bpm,
            "keyscale": keyscale,
            "vocal_language": vocal_language,
        }
        kernel_render.render_job_kernel(job, tmp_kernel_dir)
        kernels.push_kernel(tmp_kernel_dir)

        kernel_result = _wait_for_kernel_terminal(
            _KERNEL_REF, timeout=timeout, poll_interval=poll_interval
        )
        if kernel_result["status"] != "complete":
            detail = kernel_result.get("failure_message") or "sem detalhes"
            raise RuntimeError(
                f"Kernel {_KERNEL_REF} terminou com status "
                f"{kernel_result['status']!r}: {detail}"
            )
        kernels.pull_kernel_output(_KERNEL_REF, tmp_pulled_dir)

        result_path = tmp_pulled_dir / "output" / "result.json"
        try:
            result = json.loads(result_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            raise RuntimeError(
                f"O kernel nao produziu um result.json valido em {result_path} -- "
                f"ele pode ter falhado antes de terminar a geracao: {exc}"
            ) from exc

        if result.get("generation_status") != "done":
            raise RuntimeError(
                result.get("generation_error") or "geracao falhou no kernel, sem detalhes"
            )

        raw_path = tmp_pulled_dir / "output" / "raw.wav"
        if not raw_path.is_file() or raw_path.stat().st_size == 0:
            raise RuntimeError(
                f"result.json reportou geracao concluida mas {raw_path} nao existe ou esta vazio"
            )

        final_path = output_dir / f"{song_id}_master.wav"
        song_mastering.normalize_loudness(raw_path, final_path, target_lufs=lufs_target)
        song_db.update_song(db_path, song_id, status="done", output_path=str(final_path))

        try:
            if result.get("stems_status") == "done":
                fields = {}
                for name in _STEM_NAMES:
                    stem_src = tmp_pulled_dir / "output" / "stems" / f"{name}.wav"
                    stem_dest = output_dir / f"{song_id}_stem_{name}.wav"
                    shutil.copy(stem_src, stem_dest)
                    fields[f"stem_{name}_path"] = str(stem_dest)
                song_db.update_song(db_path, song_id, stems_status="done", **fields)
            else:
                song_db.update_song(
                    db_path,
                    song_id,
                    stems_status="error",
                    stems_error_message=(
                        result.get("stems_error") or "separacao falhou no kernel, sem detalhes"
                    ),
                )
        except Exception as exc:
            song_db.update_song(
                db_path, song_id, stems_status="error", stems_error_message=str(exc)
            )

        return "done", str(final_path)
    except Exception as exc:
        error_message = str(exc)
        song_db.update_song(db_path, song_id, status="error", error_message=error_message)
        return "error", error_message
    finally:
        shutil.rmtree(tmp_kernel_dir, ignore_errors=True)
        shutil.rmtree(tmp_pulled_dir, ignore_errors=True)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /c/estudos/daw_music_studio && PYTHONPATH=. uv run pytest tests/test_ace_step_orchestrator.py -v`
Expected: all 12 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add ace_step/orchestrator.py tests/test_ace_step_orchestrator.py
git commit -m "refactor: run_generation vira push/poll/pull de kernel batch, sem HTTP"
```

---

## Task 7: `scripts/criar_musica.py` — CLI update

**Files:**
- Modify: `scripts/criar_musica.py`

**Interfaces:**
- Consumes: Task 6's `orchestrator.run_generation(db_path, output_dir, song_id, *, prompt, duration, seed, bpm, keyscale, vocal_language, lufs_target, lyrics=None, timeout=2700.0, poll_interval=20.0)`.
- Produces: nothing else depends on this file.

- [ ] **Step 1: Replace the file**

Replace the entire contents of `scripts/criar_musica.py` with:

```python
import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from ace_step import orchestrator, song_db

DEFAULT_DB_PATH = Path("ace_step/output/songs.db")
DEFAULT_OUTPUT_DIR = Path("ace_step/output")


def main():
    parser = argparse.ArgumentParser(
        description="Cria uma musica: letra via Claude + geracao+separacao via kernel batch no Kaggle."
    )
    parser.add_argument("--prompt", required=True, help="Descricao de estilo/mood da musica")
    parser.add_argument("--duration", type=float, default=60.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--bpm", type=int, default=None)
    parser.add_argument("--keyscale", default=None)
    parser.add_argument("--vocal-language", default="en")
    parser.add_argument("--lufs-target", type=float, default=-9.0)
    parser.add_argument("--lyrics", default=None, help="Letra pronta -- pula a geracao via Claude")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument(
        "--timeout",
        type=float,
        default=2700.0,
        help=(
            "Orcamento total (segundos) para o kernel batch terminar (setup + "
            "geracao + separacao) -- cada musica paga o custo de setup do zero, "
            "aumente para musicas mais longas ou kernels lentos pra iniciar"
        ),
    )
    args = parser.parse_args()

    load_dotenv()

    song_id = song_db.create_song(
        args.db,
        prompt=args.prompt,
        duration=args.duration,
        seed=args.seed,
        bpm=args.bpm,
        keyscale=args.keyscale,
        vocal_language=args.vocal_language,
    )
    print(f"Musica #{song_id} criada (draft).")

    status, detail = orchestrator.run_generation(
        args.db,
        DEFAULT_OUTPUT_DIR,
        song_id,
        prompt=args.prompt,
        duration=args.duration,
        seed=args.seed,
        bpm=args.bpm,
        keyscale=args.keyscale,
        vocal_language=args.vocal_language,
        lufs_target=args.lufs_target,
        lyrics=args.lyrics,
        timeout=args.timeout,
    )

    if status == "error":
        print(f"Erro: {detail}", file=sys.stderr)
        sys.exit(1)
    print(f"Musica #{song_id} pronta: {detail}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke-check it imports and parses args**

Run: `cd /c/estudos/daw_music_studio && PYTHONPATH=. uv run python scripts/criar_musica.py --help`
Expected: prints the usage/help text with no traceback, and the `--timeout` help text mentions "kernel batch".

- [ ] **Step 3: Commit**

```bash
git add scripts/criar_musica.py
git commit -m "chore: criar_musica.py nao depende mais de ACE_STEP_API_URL/API_KEY local"
```

---

## Task 8: Delete the server+tunnel code and its tests

**Files:**
- Delete: `ace_step/kernel/proxy_server.py`
- Delete: `ace_step/client.py`
- Delete: `tests/test_ace_step_client.py`
- Delete: `tests/test_ace_step_proxy_server.py`
- Modify: `.env` (remove two lines)

- [ ] **Step 1: Delete the files**

```bash
cd /c/estudos/daw_music_studio
git rm ace_step/kernel/proxy_server.py ace_step/client.py tests/test_ace_step_client.py tests/test_ace_step_proxy_server.py
```

- [ ] **Step 2: Remove the unused env vars**

Read `.env`, then remove the `ACE_STEP_API_URL=...` and `ACE_STEP_API_KEY=...` lines (leave every other line untouched — `.env` is gitignored, this edit is local-only and doesn't get committed).

- [ ] **Step 3: Run the full test suite**

Run: `cd /c/estudos/daw_music_studio && PYTHONPATH=. uv run pytest -v`
Expected: all tests PASS, with no `ModuleNotFoundError`/`ImportError` referencing `ace_step.client` or `proxy_server` anywhere (confirms nothing else still imports the deleted modules).

- [ ] **Step 4: Commit**

```bash
git add -A ace_step tests
git commit -m "chore: remove servidor proxy + cliente HTTP do ace_step (substituidos pelo kernel batch)"
```

---

## Task 9: Live verification

This task spends real Kaggle GPU time/quota — matches this project's standing practice of verifying third-party integrations live before calling them done (see the spec's Motivation section: this whole rewrite exists because the previous architecture was verified live and found broken).

- [ ] **Step 1: Run a short real generation end-to-end**

Run: `cd /c/estudos/daw_music_studio && PYTHONPATH=. uv run python scripts/criar_musica.py --prompt "upbeat energetic electronic pop" --duration 30 --timeout 2700`

This pushes a freshly-rendered kernel to `celsosoarescesar/ace-step-api`, waits for it to run to completion, and pulls the result. A short `--duration` keeps the generation/separation portion quick while still exercising the full cold-start (git clone + pip install + model load) that every batch run now pays.

- [ ] **Step 2: Confirm the result**

Check the printed output ends with `Musica #<id> pronta: ace_step/output/<id>_master.wav`, not an `Erro:` line. If it errors, read the message: since `_wait_for_kernel_terminal`/`pull_kernel_output` assumptions (especially the `output/` prefix inside the pulled directory — see the spec's "Open risks" section) are unverified until this run, a mismatch here (e.g. `kernels_output` not preserving the `/kaggle/working/output/` subpath) is the most likely first bug; adjust `orchestrator.py`'s `tmp_pulled_dir / "output" / ...` paths to match whatever `kernels_output` actually produces, matching the debugging pattern in `[[feedback_verify_third_party_apis_live]]`.

- [ ] **Step 3: Confirm the DB row and files**

Run: `cd /c/estudos/daw_music_studio && PYTHONPATH=. uv run python -c "import sqlite3; c=sqlite3.connect('ace_step/output/songs.db'); c.row_factory=sqlite3.Row; print(dict(c.execute('SELECT * FROM songs ORDER BY id DESC LIMIT 1').fetchone()))"`

Expected: `status: done`, `stems_status: done`, all 6 `stem_*_path` fields populated with paths that exist on disk and are non-empty (`ace_step/output/<id>_stem_vocals.wav` etc., plus `<id>_master.wav`) — and critically, no `ERR_NGROK_725` or any ngrok-related error anywhere, since this path never talks to ngrok at all.

- [ ] **Step 4: Update project memory**

This isn't a code step — after this run succeeds, note in project memory that the ace_step pipeline moved to the batch-kernel architecture (supersedes `[[project_ace_step_pipeline]]`'s description of the server+ngrok design) and that it was verified live on this date.
