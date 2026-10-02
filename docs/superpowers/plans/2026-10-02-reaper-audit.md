# Auditoria de sessão REAPER (reaper-copilot) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a new `reaper_bridge/audit.py` module with five read-only
session-structure checks plus a per-track summary, exposed as two new MCP
tools (`reaper_audit_session`, `reaper_track_summary`), so the user can ask
Claude Code for a REAPER session health-check instead of installing
ReaAssist.

**Architecture:** `reaper_bridge/audit.py` follows the exact convention of
`project.py`/`mixing.py`: every public function takes `project`, wraps its
`reapy` calls, and raises `ReaperBridgeError` on failure. Unlike the
existing modules, these functions return **structured data** (lists of
strings/tuples, or a dict) — never a formatted string. `mcp_server.py` owns
all Portuguese text formatting, same as it already does for every existing
tool.

**Tech Stack:** Python 3.11, reapy, pytest, `tests/fakes.py` (extended this
phase with FX bypass state, track sends, and numeric track-info values).

**Spec:** `docs/superpowers/specs/2026-10-02-reaper-audit-design.md` — read
this first for the full rationale (why no Lua-codegen pipeline is being
built) and the live-verified `reapy` attribute shapes this plan's code
depends on (`track.color`, `track.depth`, `track.get_info_value("I_RECARM")`,
`fx.is_enabled`, `track.n_sends`, `send.dest_track.name`).

## Global Constraints

- Every `audit.py` function takes `project` as its first parameter and
  raises `ReaperBridgeError` (never a raw exception) when the underlying
  `reapy` call fails — same convention as `reaper_bridge/mixing.py` and
  `reaper_bridge/project.py`.
- `audit.py` functions return structured data (`list[str]`,
  `list[tuple[str, str]]`, `list[tuple[str, list[str]]]`, or `dict`) —
  **never** a pre-formatted string. All user-facing Portuguese text lives in
  `mcp_server.py`.
- The five `find_*` functions iterate `project.tracks`, which (confirmed
  live) excludes the master track — no explicit skip logic is needed.
- `track.get_info_value("I_RECARM")` returns a `float` (`0.0`/`1.0`), not a
  `bool` — comparisons must use `== 1.0`, not truthiness, to match the real
  `reapy` API exactly.
- `fx.is_enabled` is `True` when the plugin is active; bypassed means
  `fx.is_enabled is False` (confirmed live via `fx.disable()`).
- New MCP tools follow the existing `_run()` pattern in `mcp_server.py`
  (acquire `_REAPER_LOCK`, catch `ReaperBridgeError` → `f"Erro: {exc}"`,
  catch any other `Exception` → `f"Erro inesperado: {exc}"`).

## Review Focus

- **`find_armed_tracks` using truthiness instead of `== 1.0`** on
  `get_info_value("I_RECARM")` — the real API returns a float, and
  `0.0 == False` in Python coincidentally works but `1.0 is True` does not;
  a implementer reaching for `bool(...)` or `is True` would silently break
  on real REAPER even though fakes might mask it. Task 1's tests pin the
  exact comparison.
- **`summarize_track` raising `ReaperBridgeError` for a track name that
  doesn't exist** — a reasonable person asking "resume a faixa Baxo" (typo)
  expects a clear error naming available tracks, not a crash or an empty
  dict. Task 3 pins this via `find_track`'s existing not-found behavior.
- **`find_multi_destination_sends` with exactly one send** — a track with
  a single send is normal routing, not "unusual"; the spec's threshold is
  `n_sends > 1`, and a boundary test at exactly 1 send (should NOT be
  flagged) catches an off-by-one (`>=` instead of `>`). Task 2 pins this.
- **`reaper_audit_session`'s "all clean" formatting** — a session with zero
  findings in every category must still produce a readable report (five
  "✓" lines), not an empty string or a crash from formatting an empty list.
  Task 4 pins this with an all-clean fixture.
- **`find_bypassed_fx` on a track with FX present but none bypassed** — must
  return an empty list, not skip the track or raise; a implementer might
  assume "has FX" implies "has a finding." Task 2 pins this alongside the
  bypassed case.

---

## Task 1: `find_armed_tracks`, `find_muted_tracks`, `find_empty_tracks`

**Files:**
- Modify: `tests/fakes.py`
- Create: `reaper_bridge/audit.py`
- Create: `tests/test_audit.py`

**Interfaces:**
- Consumes: nothing outside this task (no imports from other new code).
- Produces: `find_armed_tracks(project) -> list[str]`,
  `find_muted_tracks(project) -> list[str]`,
  `find_empty_tracks(project) -> list[str]` — consumed by Task 4's
  `reaper_audit_session` MCP tool. Also produces the `FakeTrack` extensions
  (`get_info_value`, `set_info_value`, `n_items` property) that Task 2 and
  Task 3 reuse.

- [ ] **Step 1: Extend `FakeTrack` in `tests/fakes.py`**

Modify the `FakeTrack.__init__` and add two methods plus a property. The
current constructor is:

```python
class FakeTrack:
    def __init__(self, name, volume=1.0, pan=0.0, is_muted=False, is_solo=False):
        self.name = name
        self.volume = volume
        self.pan = pan
        self.is_muted = is_muted
        self.is_solo = is_solo
        self.fxs = []
        self.items = []
        self.is_selected = False
```

Replace it with:

```python
class FakeTrack:
    def __init__(self, name, volume=1.0, pan=0.0, is_muted=False, is_solo=False):
        self.name = name
        self.volume = volume
        self.pan = pan
        self.is_muted = is_muted
        self.is_solo = is_solo
        self.fxs = []
        self.items = []
        self.is_selected = False
        self._info_values = {}

    @property
    def n_items(self):
        return len(self.items)

    def get_info_value(self, param_name):
        return self._info_values.get(param_name, 0.0)

    def set_info_value(self, param_name, value):
        self._info_values[param_name] = value
```

(Leave `make_only_selected_track`, `add_fx`, `add_midi_item` exactly as they
are — just add the three new members above them, after `__init__`.)

- [ ] **Step 2: Write the failing tests**

Create `tests/test_audit.py`:

```python
import pytest

from reaper_bridge.audit import find_armed_tracks, find_empty_tracks, find_muted_tracks
from reaper_bridge.errors import ReaperBridgeError
from tests.fakes import FakeProject, FakeTrack


def test_find_armed_tracks_returns_only_armed():
    voz = FakeTrack("voz")
    voz.set_info_value("I_RECARM", 1.0)
    baixo = FakeTrack("baixo")
    project = FakeProject([voz, baixo])
    assert find_armed_tracks(project) == ["voz"]


def test_find_armed_tracks_returns_empty_when_none_armed():
    project = FakeProject([FakeTrack("voz"), FakeTrack("baixo")])
    assert find_armed_tracks(project) == []


def test_find_armed_tracks_wraps_raw_exception():
    class ExplodingTracks:
        def __iter__(self):
            raise RuntimeError("REAPER disconnected")

    project = FakeProject([])
    project.tracks = ExplodingTracks()
    with pytest.raises(ReaperBridgeError, match="faixas armadas"):
        find_armed_tracks(project)


def test_find_muted_tracks_returns_only_muted():
    project = FakeProject([FakeTrack("voz", is_muted=True), FakeTrack("baixo")])
    assert find_muted_tracks(project) == ["voz"]


def test_find_muted_tracks_returns_empty_when_none_muted():
    project = FakeProject([FakeTrack("voz"), FakeTrack("baixo")])
    assert find_muted_tracks(project) == []


def test_find_empty_tracks_returns_only_tracks_without_items():
    with_item = FakeTrack("voz")
    with_item.add_midi_item()
    empty = FakeTrack("baixo")
    project = FakeProject([with_item, empty])
    assert find_empty_tracks(project) == ["baixo"]


def test_find_empty_tracks_returns_empty_when_all_have_items():
    track = FakeTrack("voz")
    track.add_midi_item()
    project = FakeProject([track])
    assert find_empty_tracks(project) == []
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `uv run pytest tests/test_audit.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'reaper_bridge.audit'`)

- [ ] **Step 4: Write `reaper_bridge/audit.py`**

```python
from __future__ import annotations

from .errors import ReaperBridgeError


def find_armed_tracks(project) -> list[str]:
    try:
        return [
            track.name
            for track in project.tracks
            if track.get_info_value("I_RECARM") == 1.0
        ]
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível verificar faixas armadas: verifique se o REAPER está aberto"
        ) from exc


def find_muted_tracks(project) -> list[str]:
    try:
        return [track.name for track in project.tracks if track.is_muted]
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível verificar faixas mutadas: verifique se o REAPER está aberto"
        ) from exc


def find_empty_tracks(project) -> list[str]:
    try:
        return [track.name for track in project.tracks if track.n_items == 0]
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível verificar faixas vazias: verifique se o REAPER está aberto"
        ) from exc
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_audit.py -v`
Expected: all 7 PASS

- [ ] **Step 6: Commit**

```bash
git add reaper_bridge/audit.py tests/fakes.py tests/test_audit.py
git commit -m "feat: add armed/muted/empty track audit checks"
```

---

## Task 2: `find_bypassed_fx`, `find_multi_destination_sends`

**Files:**
- Modify: `tests/fakes.py`
- Modify: `reaper_bridge/audit.py`
- Modify: `tests/test_audit.py`

**Interfaces:**
- Consumes: Task 1's `FakeTrack` (now also needs `sends`/`n_sends`) and the
  existing `FakeFX`.
- Produces: `find_bypassed_fx(project) -> list[tuple[str, str]]`,
  `find_multi_destination_sends(project) -> list[tuple[str, list[str]]]` —
  consumed by Task 4. Also produces the `FakeSend` class and
  `FakeTrack.add_send`/`n_sends`, and `FakeFX.is_enabled`/`disable()`/
  `enable()`, reused by Task 3.

- [ ] **Step 1: Extend `tests/fakes.py`**

Add `is_enabled`, `disable()`, `enable()` to `FakeFX` — current class:

```python
class FakeFX:
    def __init__(self, name, param_names=()):
        self.name = name
        self.params = [FakeFXParam(param_name) for param_name in param_names]
```

Replace with:

```python
class FakeFX:
    def __init__(self, name, param_names=(), is_enabled=True):
        self.name = name
        self.params = [FakeFXParam(param_name) for param_name in param_names]
        self.is_enabled = is_enabled

    def disable(self):
        self.is_enabled = False

    def enable(self):
        self.is_enabled = True
```

Add a `FakeSend` class right after `FakeFX`:

```python
class FakeSend:
    def __init__(self, dest_track, volume=0.0):
        self.dest_track = dest_track
        self.volume = volume
```

Add `self.sends = []` to `FakeTrack.__init__` (alongside `self._info_values = {}`
from Task 1) and these two members to `FakeTrack`:

```python
    @property
    def n_sends(self):
        return len(self.sends)

    def add_send(self, dest_track, volume=0.0):
        send = FakeSend(dest_track, volume=volume)
        self.sends.append(send)
        return send
```

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_audit.py`:

```python
from reaper_bridge.audit import find_bypassed_fx, find_multi_destination_sends
from tests.fakes import FakeFX


def test_find_bypassed_fx_returns_only_disabled_plugins():
    track = FakeTrack("piano")
    track.fxs.append(FakeFX("ReaEQ (Cockos)"))
    bypassed = FakeFX("ReaComp (Cockos)")
    bypassed.disable()
    track.fxs.append(bypassed)
    project = FakeProject([track])
    assert find_bypassed_fx(project) == [("piano", "ReaComp (Cockos)")]


def test_find_bypassed_fx_returns_empty_when_none_bypassed():
    track = FakeTrack("piano")
    track.fxs.append(FakeFX("ReaEQ (Cockos)"))
    project = FakeProject([track])
    assert find_bypassed_fx(project) == []


def test_find_multi_destination_sends_flags_more_than_one_send():
    source = FakeTrack("baixo")
    dest_a = FakeTrack("bus_a")
    dest_b = FakeTrack("bus_b")
    source.add_send(dest_a)
    source.add_send(dest_b)
    project = FakeProject([source, dest_a, dest_b])
    assert find_multi_destination_sends(project) == [("baixo", ["bus_a", "bus_b"])]


def test_find_multi_destination_sends_does_not_flag_exactly_one_send():
    source = FakeTrack("baixo")
    dest = FakeTrack("bus_a")
    source.add_send(dest)
    project = FakeProject([source, dest])
    assert find_multi_destination_sends(project) == []


def test_find_multi_destination_sends_returns_empty_when_no_sends():
    project = FakeProject([FakeTrack("baixo")])
    assert find_multi_destination_sends(project) == []
```

- [ ] **Step 3: Run tests to verify the new ones fail**

Run: `uv run pytest tests/test_audit.py -v -k "bypassed or multi_destination"`
Expected: FAIL (`AttributeError: module 'reaper_bridge.audit' has no
attribute 'find_bypassed_fx'`, etc.)

- [ ] **Step 4: Append to `reaper_bridge/audit.py`**

```python


def find_bypassed_fx(project) -> list[tuple[str, str]]:
    try:
        pairs: list[tuple[str, str]] = []
        for track in project.tracks:
            for fx in track.fxs:
                if not fx.is_enabled:
                    pairs.append((track.name, fx.name))
        return pairs
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível verificar plugins bypassed: verifique se o REAPER está aberto"
        ) from exc


def find_multi_destination_sends(project) -> list[tuple[str, list[str]]]:
    try:
        result: list[tuple[str, list[str]]] = []
        for track in project.tracks:
            if track.n_sends > 1:
                destinations = [send.dest_track.name for send in track.sends]
                result.append((track.name, destinations))
        return result
    except Exception as exc:
        raise ReaperBridgeError(
            "não foi possível verificar o roteamento das faixas: verifique se o REAPER está aberto"
        ) from exc
```

- [ ] **Step 5: Run all audit tests to verify they pass**

Run: `uv run pytest tests/test_audit.py -v`
Expected: all 12 PASS

- [ ] **Step 6: Commit**

```bash
git add reaper_bridge/audit.py tests/fakes.py tests/test_audit.py
git commit -m "feat: add bypassed-FX and multi-destination-send audit checks"
```

---

## Task 3: `summarize_track`

**Files:**
- Modify: `tests/fakes.py`
- Modify: `reaper_bridge/audit.py`
- Modify: `tests/test_audit.py`

**Interfaces:**
- Consumes: `reaper_bridge.project.find_track` (existing), Task 2's
  `FakeFX.is_enabled`/`FakeTrack.sends`/`FakeSend`, Task 1's
  `FakeTrack.get_info_value`.
- Produces: `summarize_track(project, track_name: str) -> dict` with keys
  `name: str`, `color: tuple[int, int, int]`, `depth: int`,
  `is_muted: bool`, `is_armed: bool`, `fx: list[dict]` (each
  `{"name": str, "enabled": bool}`), `sends: list[dict]` (each
  `{"dest": str, "volume": float}`) — consumed by Task 4's
  `reaper_track_summary` MCP tool.

- [ ] **Step 1: Extend `FakeTrack.__init__` in `tests/fakes.py`**

Add `color` and `depth` constructor parameters (defaults match what was
confirmed live against a freshly created REAPER track):

```python
    def __init__(
        self,
        name,
        volume=1.0,
        pan=0.0,
        is_muted=False,
        is_solo=False,
        color=(0, 0, 0),
        depth=0,
    ):
        self.name = name
        self.volume = volume
        self.pan = pan
        self.is_muted = is_muted
        self.is_solo = is_solo
        self.color = color
        self.depth = depth
        self.fxs = []
        self.items = []
        self.sends = []
        self.is_selected = False
        self._info_values = {}
```

(This merges with Task 1's and Task 2's additions to the same method —
the final `__init__` has all of: `color`, `depth`, `self.sends = []`, and
`self._info_values = {}`.)

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_audit.py`:

```python
from reaper_bridge.audit import summarize_track


def test_summarize_track_returns_full_state():
    track = FakeTrack("piano", is_muted=True, color=(255, 0, 0), depth=1)
    track.set_info_value("I_RECARM", 1.0)
    enabled_fx = FakeFX("ReaEQ (Cockos)")
    bypassed_fx = FakeFX("ReaComp (Cockos)")
    bypassed_fx.disable()
    track.fxs.extend([enabled_fx, bypassed_fx])
    dest = FakeTrack("bus_a")
    track.add_send(dest, volume=0.8)
    project = FakeProject([track, dest])

    assert summarize_track(project, "piano") == {
        "name": "piano",
        "color": (255, 0, 0),
        "depth": 1,
        "is_muted": True,
        "is_armed": True,
        "fx": [
            {"name": "ReaEQ (Cockos)", "enabled": True},
            {"name": "ReaComp (Cockos)", "enabled": False},
        ],
        "sends": [{"dest": "bus_a", "volume": 0.8}],
    }


def test_summarize_track_raises_when_track_not_found():
    project = FakeProject([FakeTrack("piano")])
    with pytest.raises(ReaperBridgeError, match="não existe"):
        summarize_track(project, "baixo")
```

- [ ] **Step 3: Run tests to verify the new ones fail**

Run: `uv run pytest tests/test_audit.py -v -k summarize_track`
Expected: FAIL (`AttributeError: module 'reaper_bridge.audit' has no
attribute 'summarize_track'`)

- [ ] **Step 4: Append to `reaper_bridge/audit.py`**

First, add the import at the top of the file (alongside the existing
`from .errors import ReaperBridgeError`):

```python
from .project import find_track
```

Then append the function:

```python


def summarize_track(project, track_name: str) -> dict:
    track = find_track(project, track_name)
    try:
        return {
            "name": track.name,
            "color": track.color,
            "depth": track.depth,
            "is_muted": track.is_muted,
            "is_armed": track.get_info_value("I_RECARM") == 1.0,
            "fx": [{"name": fx.name, "enabled": fx.is_enabled} for fx in track.fxs],
            "sends": [
                {"dest": send.dest_track.name, "volume": send.volume}
                for send in track.sends
            ],
        }
    except Exception as exc:
        raise ReaperBridgeError(
            f"não foi possível resumir a faixa '{track_name}': verifique se o REAPER está aberto"
        ) from exc
```

(`find_track` already raises `ReaperBridgeError` with a "faixa '...' não
existe, faixas disponíveis: ..." message when `track_name` isn't found, so
no separate not-found handling is needed here.)

- [ ] **Step 5: Run all audit tests to verify they pass**

Run: `uv run pytest tests/test_audit.py -v`
Expected: all 14 PASS

- [ ] **Step 6: Commit**

```bash
git add reaper_bridge/audit.py tests/fakes.py tests/test_audit.py
git commit -m "feat: add summarize_track for single-track audit detail"
```

---

## Task 4: MCP tools `reaper_audit_session` and `reaper_track_summary`

**Files:**
- Modify: `mcp_server.py`
- Modify: `tests/test_mcp_server.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: Task 1/2's five `find_*` functions and Task 3's
  `summarize_track` from `reaper_bridge.audit`.
- Produces: two new MCP tools, `reaper_audit_session() -> str` and
  `reaper_track_summary(track_name: str) -> str`. Nothing downstream in
  this phase consumes these (this is the last task).

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_mcp_server.py`. First, extend the existing import block
at the top of the file:

```python
from mcp_server import (
    reaper_add_fx,
    reaper_apply_master,
    reaper_audit_session,
    reaper_generate_scale,
    reaper_import_audio,
    reaper_list_tracks,
    reaper_set_volume,
    reaper_split_stems,
    reaper_track_summary,
)
```

Then append these test functions:

```python
def test_reaper_audit_session_reports_all_clean_when_nothing_found():
    with patch("mcp_server.get_project", return_value=object()):
        with patch("mcp_server.audit.find_armed_tracks", return_value=[]):
            with patch("mcp_server.audit.find_muted_tracks", return_value=[]):
                with patch("mcp_server.audit.find_empty_tracks", return_value=[]):
                    with patch("mcp_server.audit.find_bypassed_fx", return_value=[]):
                        with patch(
                            "mcp_server.audit.find_multi_destination_sends", return_value=[]
                        ):
                            result = reaper_audit_session()
    assert result.count("✓") == 5
    assert "⚠" not in result


def test_reaper_audit_session_reports_findings():
    with patch("mcp_server.get_project", return_value=object()):
        with patch("mcp_server.audit.find_armed_tracks", return_value=["voz"]):
            with patch("mcp_server.audit.find_muted_tracks", return_value=["baixo"]):
                with patch("mcp_server.audit.find_empty_tracks", return_value=[]):
                    with patch(
                        "mcp_server.audit.find_bypassed_fx",
                        return_value=[("piano", "ReaComp (Cockos)")],
                    ):
                        with patch(
                            "mcp_server.audit.find_multi_destination_sends", return_value=[]
                        ):
                            result = reaper_audit_session()
    assert "voz" in result
    assert "baixo" in result
    assert "ReaComp (Cockos)" in result
    # armed, muted, and bypassed-fx each contribute one ⚠; empty and
    # multi-dest-sends are clean, contributing one ✓ each.
    assert result.count("⚠") == 3
    assert result.count("✓") == 2


def test_reaper_audit_session_returns_error_message_on_bridge_error():
    with patch("mcp_server.get_project", side_effect=ReaperBridgeError("REAPER fechado")):
        assert reaper_audit_session() == "Erro: REAPER fechado"


def test_reaper_track_summary_formats_fields():
    summary = {
        "name": "piano",
        "color": (255, 0, 0),
        "depth": 0,
        "is_muted": True,
        "is_armed": False,
        "fx": [{"name": "ReaEQ (Cockos)", "enabled": True}],
        "sends": [{"dest": "bus_a", "volume": 0.8}],
    }
    with patch("mcp_server.get_project", return_value=object()):
        with patch("mcp_server.audit.summarize_track", return_value=summary):
            result = reaper_track_summary("piano")
    assert "piano" in result
    assert "ReaEQ (Cockos)" in result
    assert "bus_a" in result


def test_reaper_track_summary_returns_error_message_on_bridge_error():
    with patch("mcp_server.get_project", return_value=object()):
        with patch(
            "mcp_server.audit.summarize_track",
            side_effect=ReaperBridgeError("faixa 'xyz' não existe, faixas disponíveis: piano"),
        ):
            result = reaper_track_summary("xyz")
    assert result == "Erro: faixa 'xyz' não existe, faixas disponíveis: piano"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_mcp_server.py -v -k "audit_session or track_summary"`
Expected: FAIL (`ImportError: cannot import name 'reaper_audit_session'`)

- [ ] **Step 3: Modify `mcp_server.py`**

Change the import line:

```python
from reaper_bridge import mastering, midi, mixing, stems
```

to:

```python
from reaper_bridge import audit, mastering, midi, mixing, stems
```

Then add these two tools at the end of the file, right before the
`if __name__ == "__main__":` block:

```python
@mcp.tool()
def reaper_audit_session() -> str:
    """Audita a sessão REAPER atual: faixas armadas, mutadas, vazias, FX
    bypassed e faixas com sends para múltiplos destinos."""
    def operation():
        project = get_project()
        lines = ["Auditoria da sessão:"]

        armed = audit.find_armed_tracks(project)
        if armed:
            lines.append(f"  ⚠ {len(armed)} faixa(s) armada(s) para gravação: {', '.join(armed)}")
        else:
            lines.append("  ✓ nenhuma faixa armada para gravação")

        muted = audit.find_muted_tracks(project)
        if muted:
            lines.append(f"  ⚠ {len(muted)} faixa(s) mutada(s): {', '.join(muted)}")
        else:
            lines.append("  ✓ nenhuma faixa mutada")

        empty = audit.find_empty_tracks(project)
        if empty:
            lines.append(f"  ⚠ {len(empty)} faixa(s) vazia(s): {', '.join(empty)}")
        else:
            lines.append("  ✓ nenhuma faixa vazia")

        bypassed = audit.find_bypassed_fx(project)
        if bypassed:
            pairs_text = ", ".join(f"{track} → {fx}" for track, fx in bypassed)
            lines.append(f"  ⚠ {len(bypassed)} FX bypassed: {pairs_text}")
        else:
            lines.append("  ✓ nenhum FX bypassed")

        multi_dest = audit.find_multi_destination_sends(project)
        if multi_dest:
            pairs_text = ", ".join(
                f"{track} → {', '.join(dests)}" for track, dests in multi_dest
            )
            lines.append(f"  ⚠ {len(multi_dest)} faixa(s) com sends para múltiplos destinos: {pairs_text}")
        else:
            lines.append("  ✓ nenhuma faixa com sends para múltiplos destinos")

        return "\n".join(lines)
    return _run(operation)


@mcp.tool()
def reaper_track_summary(track_name: str) -> str:
    """Resume o estado de uma faixa: FX chain, sends, cor, pasta, mute/arm."""
    def operation():
        summary = audit.summarize_track(get_project(), track_name)
        lines = [f"Faixa '{summary['name']}':"]
        lines.append(f"  Mutada: {'sim' if summary['is_muted'] else 'não'}")
        lines.append(f"  Armada: {'sim' if summary['is_armed'] else 'não'}")
        lines.append(f"  Cor: {summary['color']}")
        lines.append(f"  Profundidade de pasta: {summary['depth']}")
        if summary["fx"]:
            fx_text = ", ".join(
                f"{fx['name']} ({'ativo' if fx['enabled'] else 'bypassed'})"
                for fx in summary["fx"]
            )
            lines.append(f"  FX: {fx_text}")
        else:
            lines.append("  FX: (nenhum)")
        if summary["sends"]:
            sends_text = ", ".join(
                f"{send['dest']} ({send['volume']})" for send in summary["sends"]
            )
            lines.append(f"  Sends: {sends_text}")
        else:
            lines.append("  Sends: (nenhum)")
        return "\n".join(lines)
    return _run(operation)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_mcp_server.py -v`
Expected: all PASS (existing tests + 5 new ones)

- [ ] **Step 5: Add manual smoke-test checklist items to `README.md`**

In the "Checklist de smoke test manual" section, after the last existing
`- [ ]` line (the "Analisa o que eu toquei" one), add:

```markdown
- [ ] "Audita a sessão" → lista faixas armadas/mutadas/vazias, FX bypassed
      e sends para múltiplos destinos (ou confirma que não há nenhum,
      faixa por faixa).
- [ ] "Resume a faixa drums" → mostra mute/arm, FX chain, sends, cor e
      profundidade de pasta dessa faixa.
```

- [ ] **Step 6: Run the full test suite**

Run: `uv run pytest tests/ -v`
Expected: all PASS except the 8 pre-existing, unrelated failures in
`tests/test_mastering.py` and `tests/test_project.py` (environment/`reapy`
version mismatch — `reapy.reascript_api` missing `InsertMedia` — confirmed
present even on `master` before this phase, see
`docs/superpowers/plans/2026-09-27-curso-music21-fase6.md`'s finishing
notes for the prior confirmation of this same pre-existing issue).

- [ ] **Step 7: Commit**

```bash
git add mcp_server.py tests/test_mcp_server.py README.md
git commit -m "feat: add reaper_audit_session and reaper_track_summary MCP tools"
```

---

## After this plan

The next blocks from the ReaAssist-parity brainstorm (peak/LUFS audio
analysis, routing/buses, MIDI editing, audio item editing, markers/regions,
FX/plugin management, persistent preferences) each get their own spec and
plan when the user wants to tackle them — see "Próximos blocos" in
`docs/superpowers/specs/2026-10-02-reaper-audit-design.md`.
